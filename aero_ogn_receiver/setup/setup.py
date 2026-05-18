from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aero_ogn_receiver.core import paths as default_paths
from aero_ogn_receiver.core.architecture import (
    SUPPORTED_BINARY_ARCHES,
    host_os_architecture,
    resolve_binary_arch,
)
from aero_ogn_receiver.core.checksums import ChecksumMismatch, verify_file_hash
from aero_ogn_receiver.core.config_model import load_config
from aero_ogn_receiver.core.manifest import BinaryEntry, load_manifest
from aero_ogn_receiver.core.render import render_ogn_config


BASE_SYSTEM_PACKAGES = ("rtl-sdr", "ca-certificates", "procserv")
ARM64_OGN_RUNTIME_PACKAGES = (
    "libc6:armhf",
    "libstdc++6:armhf",
    "libgcc-s1:armhf",
    "librtlsdr0:armhf",
)
SYSTEMD_UNITS = (
    "aero-ogn-rf.service",
    "aero-ogn-decode.service",
    "aero-ogn-receiver.target",
)
INSTALL_STATE_FILENAME = "install-state.json"


@dataclass(frozen=True)
class SetupPaths:
    config_dir: Path
    config_path: Path
    native_config_path: Path
    opt_dir: Path
    ogn_install_dir: Path
    ogn_current_dir: Path
    state_dir: Path
    cache_dir: Path
    log_dir: Path
    systemd_dir: Path

    @classmethod
    def system(cls) -> "SetupPaths":
        return cls(
            config_dir=default_paths.CONFIG_DIR,
            config_path=default_paths.CONFIG_PATH,
            native_config_path=default_paths.NATIVE_CONFIG_PATH,
            opt_dir=default_paths.OPT_DIR,
            ogn_install_dir=default_paths.OGN_INSTALL_DIR,
            ogn_current_dir=default_paths.OGN_CURRENT_DIR,
            state_dir=default_paths.STATE_DIR,
            cache_dir=default_paths.STATE_DIR / "cache",
            log_dir=default_paths.LOG_DIR,
            systemd_dir=Path("/etc/systemd/system"),
        )

    @classmethod
    def under_root(cls, root: Path) -> "SetupPaths":
        return cls(
            config_dir=root / "etc/aero-ogn-receiver",
            config_path=root / "etc/aero-ogn-receiver/config.yaml",
            native_config_path=root / "etc/aero-ogn-receiver/rtlsdr-ogn.conf",
            opt_dir=root / "opt/aero-ogn-receiver",
            ogn_install_dir=root / "opt/aero-ogn-receiver/ogn",
            ogn_current_dir=root / "opt/aero-ogn-receiver/ogn/current",
            state_dir=root / "var/lib/aero-ogn-receiver",
            cache_dir=root / "var/lib/aero-ogn-receiver/cache",
            log_dir=root / "var/log/aero-ogn-receiver",
            systemd_dir=root / "etc/systemd/system",
        )


@dataclass(frozen=True)
class SetupOptions:
    dry_run: bool
    skip_apt: bool
    skip_download: bool
    no_daemon_reload: bool
    version: str
    arch: str
    paths: SetupPaths
    root: Path | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aero_ogn_receiver.setup.setup",
        description="Prepare a Raspberry Pi for aero-ogn-receiver.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changes")
    parser.add_argument(
        "--skip-apt",
        action="store_true",
        help="Do not install Debian packages",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Create config/systemd files but do not download or extract OGN binaries",
    )
    parser.add_argument(
        "--no-daemon-reload",
        action="store_true",
        help="Do not run systemctl daemon-reload",
    )
    parser.add_argument("--version", default="0.3.2", help="OGN binary version to install")
    parser.add_argument(
        "--arch",
        default="auto",
        choices=SUPPORTED_BINARY_ARCHES,
        help="OGN binary arch",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Apply under an alternate root for tests; skips apt and systemctl by default",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = SetupOptions(
        dry_run=args.dry_run,
        skip_apt=args.skip_apt or args.root is not None,
        skip_download=args.skip_download,
        no_daemon_reload=args.no_daemon_reload or args.root is not None,
        version=args.version,
        arch=resolve_binary_arch(args.arch),
        paths=SetupPaths.under_root(args.root) if args.root else SetupPaths.system(),
        root=args.root,
    )

    try:
        run_setup(options)
    except (SetupError, OSError, subprocess.CalledProcessError, tarfile.TarError, urllib.error.URLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


class SetupError(RuntimeError):
    """Raised when setup cannot continue safely."""


def run_setup(options: SetupOptions) -> None:
    if options.dry_run:
        print("Setup dry run:")
    else:
        _require_root_unless_test_root(options)
        print("Setting up aero-ogn-receiver:")

    entry = load_manifest().get(options.version, options.arch)

    _create_directories(options)
    install_state = _install_system_packages(options)
    _write_install_state(options, install_state)
    _install_config(options)
    _render_config(options)
    if options.skip_download:
        _say(options, f"Skip OGN binary download/extract for {entry.version} {entry.arch}")
    else:
        _install_ogn_binary(options, entry)
    _apply_ogn_runtime_permissions(options)
    _install_systemd_units(options)
    _reload_systemd(options)
    _print_next_steps(options)


def _require_root_unless_test_root(options: SetupOptions) -> None:
    if options.root is not None:
        return
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        raise SetupError(
            "setup writes system files and must be run with sudo. "
            "Use --dry-run to preview without changes."
        )


def _install_system_packages(options: SetupOptions) -> dict[str, object]:
    state = {
        "version": 1,
        "binary_arch": options.arch,
        "requested_packages": [],
        "packages_preexisting": [],
        "packages_installed_by_setup": [],
        "foreign_architectures_preexisting": [],
        "foreign_architectures_added": [],
    }
    if options.skip_apt:
        _say(options, "Skip Debian package installation")
        return state
    packages = _system_packages_for_binary_arch(options.arch)
    foreign_architectures_before = _foreign_architectures()
    preexisting_packages = _installed_packages(packages)
    state["requested_packages"] = list(packages)
    state["packages_preexisting"] = sorted(preexisting_packages)
    state["foreign_architectures_preexisting"] = sorted(foreign_architectures_before)
    if options.arch == "arm" and host_os_architecture() == "arm64":
        _ensure_armhf_architecture(options)
    foreign_architectures_after = _foreign_architectures()
    state["foreign_architectures_added"] = sorted(
        foreign_architectures_after - foreign_architectures_before
    )
    _say(options, f"Install Debian packages: {', '.join(packages)}")
    if options.dry_run:
        state["packages_installed_by_setup"] = [
            package for package in packages if package not in preexisting_packages
        ]
        return state
    if not shutil.which("apt-get"):
        raise SetupError("apt-get not found; this setup command targets Raspberry Pi OS/Debian")
    env = {
        **os.environ,
        "DEBIAN_FRONTEND": "noninteractive",
        "APT_LISTCHANGES_FRONTEND": "none",
    }
    subprocess.run(["apt-get", "update", "-qq"], check=True, env=env)
    subprocess.run(
        [
            "apt-get",
            "install",
            "-y",
            "-qq",
            "-o",
            "Dpkg::Options::=--force-confdef",
            "-o",
            "Dpkg::Options::=--force-confold",
            *packages,
        ],
        check=True,
        env=env,
    )
    installed_after = _installed_packages(packages)
    state["packages_installed_by_setup"] = sorted(installed_after - preexisting_packages)
    return state


def _installed_packages(packages: Sequence[str]) -> set[str]:
    if not packages or not shutil.which("dpkg-query"):
        return set()
    installed: set[str] = set()
    for package in packages:
        completed = subprocess.run(
            ["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.startswith("ii "):
            installed.add(package)
    return installed


def _write_install_state(options: SetupOptions, state: dict[str, object]) -> None:
    state_path = options.paths.state_dir / INSTALL_STATE_FILENAME
    _say(options, f"Write install state: {state_path}")
    if options.dry_run:
        return
    options.paths.state_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state_path.chmod(0o644)


def _system_packages_for_binary_arch(binary_arch: str) -> tuple[str, ...]:
    if binary_arch == "arm" and host_os_architecture() == "arm64":
        return (*BASE_SYSTEM_PACKAGES, *ARM64_OGN_RUNTIME_PACKAGES)
    return BASE_SYSTEM_PACKAGES


def _foreign_architectures() -> set[str]:
    if not shutil.which("dpkg"):
        return set()
    completed = subprocess.run(
        ["dpkg", "--print-foreign-architectures"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return set()
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def _ensure_armhf_architecture(options: SetupOptions) -> None:
    if "armhf" in _foreign_architectures():
        _say(options, "armhf architecture already enabled for 32-bit OGN binaries")
        return
    _say(options, "Enable armhf architecture for 32-bit OGN binaries")
    if options.dry_run:
        return
    subprocess.run(["dpkg", "--add-architecture", "armhf"], check=True)


def _create_directories(options: SetupOptions) -> None:
    for directory in (
        options.paths.config_dir,
        options.paths.ogn_install_dir,
        options.paths.state_dir,
        options.paths.cache_dir,
        options.paths.log_dir,
        options.paths.systemd_dir,
    ):
        _say(options, f"Create directory: {directory}")
        if not options.dry_run:
            directory.mkdir(parents=True, exist_ok=True)


def _install_config(options: SetupOptions) -> None:
    if options.paths.config_path.exists():
        _say(options, f"Keep existing config: {options.paths.config_path}")
        return
    source = default_paths.example_config_path()
    _say(options, f"Install example config: {options.paths.config_path}")
    if options.dry_run:
        return
    shutil.copyfile(source, options.paths.config_path)
    options.paths.config_path.chmod(0o644)


def _render_config(options: SetupOptions) -> None:
    _say(options, f"Render native OGN config: {options.paths.native_config_path}")
    if options.dry_run:
        return
    config = load_config(options.paths.config_path)
    rendered = render_ogn_config(config)
    options.paths.native_config_path.write_text(rendered, encoding="utf-8")
    options.paths.native_config_path.chmod(0o644)


def _install_ogn_binary(options: SetupOptions, entry: BinaryEntry) -> None:
    archive_name = Path(urllib.parse.urlparse(entry.url).path).name
    if not archive_name:
        raise SetupError(f"cannot determine archive filename from URL: {entry.url}")
    archive_path = options.paths.cache_dir / archive_name
    install_path = options.paths.ogn_install_dir / f"{entry.archive_root}-{entry.arch}"

    _download_archive(options, entry, archive_path)
    _verify_archive(options, entry, archive_path)

    if install_path.exists():
        _say(options, f"Keep existing extracted OGN binary dir: {install_path}")
    else:
        _say(options, f"Extract OGN archive to: {options.paths.ogn_install_dir}")
        if not options.dry_run:
            _extract_archive_root(archive_path, entry, install_path, options.paths.cache_dir)

    _say(options, f"Point current OGN binary symlink at: {install_path}")
    if options.dry_run:
        return
    if not install_path.exists():
        raise SetupError(f"expected extracted archive root does not exist: {install_path}")
    _replace_symlink(options.paths.ogn_current_dir, install_path)


def _apply_ogn_runtime_permissions(options: SetupOptions) -> None:
    for name in ("ogn-rf", "gsm_scan"):
        binary_path = options.paths.ogn_current_dir / name
        if not binary_path.exists():
            _say(options, f"Skip setuid permissions for missing OGN binary: {binary_path}")
            continue
        _say(options, f"Set setuid root compatibility permission: {binary_path}")
        if options.dry_run:
            continue
        if options.root is None:
            shutil.chown(binary_path, user="root", group="root")
        binary_path.chmod(binary_path.stat().st_mode | stat.S_ISUID)


def _extract_archive_root(
    archive_path: Path,
    entry: BinaryEntry,
    install_path: Path,
    cache_dir: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="extract-", dir=cache_dir) as temp_dir:
        temp_path = Path(temp_dir)
        _safe_extract_tar(archive_path, temp_path)
        extracted_root = temp_path / entry.archive_root
        if not extracted_root.exists():
            raise SetupError(f"archive did not contain expected root: {entry.archive_root}")
        shutil.move(str(extracted_root), str(install_path))


def _download_archive(options: SetupOptions, entry: BinaryEntry, archive_path: Path) -> None:
    if archive_path.exists():
        _say(options, f"Use cached OGN archive: {archive_path}")
        return
    _say(options, f"Download OGN archive: {entry.url}")
    if options.dry_run:
        return
    urllib.request.urlretrieve(entry.url, archive_path)


def _verify_archive(options: SetupOptions, entry: BinaryEntry, archive_path: Path) -> None:
    _say(options, f"Verify SHA-256 for: {archive_path}")
    if options.dry_run:
        return
    try:
        verify_file_hash(archive_path, entry.sha256, "sha256")
        verify_file_hash(archive_path, entry.md5, "md5")
    except ChecksumMismatch as exc:
        raise SetupError(str(exc)) from exc


def _install_systemd_units(options: SetupOptions) -> None:
    for unit in SYSTEMD_UNITS:
        source = default_paths.template_path(unit)
        destination = options.paths.systemd_dir / unit
        _say(options, f"Install systemd unit: {destination}")
        if not options.dry_run:
            shutil.copyfile(source, destination)
            destination.chmod(0o644)


def _reload_systemd(options: SetupOptions) -> None:
    if options.no_daemon_reload:
        _say(options, "Skip systemctl daemon-reload")
        return
    _say(options, "Run systemctl daemon-reload")
    if options.dry_run:
        return
    if not shutil.which("systemctl"):
        raise SetupError("systemctl not found; cannot reload systemd")
    subprocess.run(["systemctl", "daemon-reload"], check=True)


def _print_next_steps(options: SetupOptions) -> None:
    if options.dry_run:
        return
    print()
    print("Setup complete. Next steps:")
    print(f"1. Edit configuration: sudo nano {options.paths.config_path}")
    print(f"2. Validate config: aero-ogn config validate --config {options.paths.config_path}")
    print(
        "3. Review rendered native config: "
        f"aero-ogn config render --config {options.paths.config_path}"
    )
    print("4. Start services when ready: sudo systemctl enable --now aero-ogn-receiver.target")
    print("5. Check status: aero-ogn status --live")


def _safe_extract_tar(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()
    with tarfile.open(archive_path, "r:*") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if not _is_relative_to(target, destination_resolved):
                raise SetupError(f"archive member escapes extraction directory: {member.name}")
        archive.extractall(destination, filter="data")


def _replace_symlink(link: Path, target: Path) -> None:
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            raise SetupError(f"cannot replace non-symlink directory: {link}")
        link.unlink()
    link.symlink_to(target)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _say(options: SetupOptions, message: str) -> None:
    prefix = "Would " if options.dry_run else ""
    print(f"- {prefix}{message}")


if __name__ == "__main__":
    raise SystemExit(main())
