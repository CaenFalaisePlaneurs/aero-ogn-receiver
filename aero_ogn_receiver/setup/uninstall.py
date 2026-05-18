from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aero_ogn_receiver.setup.setup import INSTALL_STATE_FILENAME, SYSTEMD_UNITS, SetupPaths


@dataclass(frozen=True)
class UninstallOptions:
    dry_run: bool
    purge: bool
    complete: bool
    remove_binaries: bool
    remove_packages: bool
    no_daemon_reload: bool
    paths: SetupPaths
    root: Path | None


class UninstallError(RuntimeError):
    """Raised when uninstall cannot continue safely."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aero_ogn_receiver.setup.uninstall",
        description="Remove aero-ogn-receiver system integration.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changes")
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Remove preserved config/state as well as service integration",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help=(
            "Remove receiver integration, OGN binaries, recorded Debian packages, "
            "state, and logs while preserving /etc/aero-ogn-receiver/config.yaml"
        ),
    )
    parser.add_argument(
        "--remove-binaries",
        action="store_true",
        help="Remove /opt/aero-ogn-receiver",
    )
    parser.add_argument(
        "--remove-packages",
        action="store_true",
        help="Remove Debian packages and foreign architectures recorded as installed by setup",
    )
    parser.add_argument(
        "--no-daemon-reload",
        action="store_true",
        help="Do not run systemctl daemon-reload/reset-failed",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Apply under an alternate root for tests; skips systemctl by default",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = UninstallOptions(
        dry_run=args.dry_run,
        purge=args.purge,
        complete=args.complete,
        remove_binaries=args.remove_binaries or args.complete,
        remove_packages=args.remove_packages or args.complete,
        no_daemon_reload=args.no_daemon_reload or args.root is not None,
        paths=SetupPaths.under_root(args.root) if args.root else SetupPaths.system(),
        root=args.root,
    )

    try:
        run_uninstall(options)
    except (UninstallError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def run_uninstall(options: UninstallOptions) -> None:
    if options.dry_run:
        print("Uninstall dry run:")
    else:
        _require_root_unless_test_root(options)
        print("Uninstalling aero-ogn-receiver system integration:")

    _stop_and_disable(options)
    _remove_systemd_units(options)
    _reload_systemd(options)
    _remove_binaries(options)
    _remove_packages(options)
    _remove_config_and_state(options)
    _print_summary(options)


def _require_root_unless_test_root(options: UninstallOptions) -> None:
    if options.root is not None:
        return
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        raise UninstallError(
            "uninstall changes system files and must be run with sudo. "
            "Use --dry-run to preview without changes."
        )


def _stop_and_disable(options: UninstallOptions) -> None:
    if options.root is not None or options.no_daemon_reload:
        _say(options, "Skip systemctl stop/disable")
        return
    if not shutil.which("systemctl"):
        _say(options, "Skip systemctl stop/disable because systemctl is unavailable")
        return
    for command in (
        ["systemctl", "stop", "aero-ogn-receiver.target"],
        ["systemctl", "disable", "aero-ogn-receiver.target"],
    ):
        _say(options, "Run " + " ".join(command))
        if not options.dry_run:
            subprocess.run(command, check=False)


def _remove_systemd_units(options: UninstallOptions) -> None:
    for unit in SYSTEMD_UNITS:
        destination = options.paths.systemd_dir / unit
        _say(options, f"Remove systemd unit: {destination}")
        if not options.dry_run and destination.exists():
            destination.unlink()


def _reload_systemd(options: UninstallOptions) -> None:
    if options.no_daemon_reload:
        _say(options, "Skip systemctl daemon-reload/reset-failed")
        return
    if not shutil.which("systemctl"):
        _say(options, "Skip systemctl daemon-reload/reset-failed because systemctl is unavailable")
        return
    for command in (
        ["systemctl", "daemon-reload"],
        ["systemctl", "reset-failed"],
    ):
        _say(options, "Run " + " ".join(command))
        if not options.dry_run:
            subprocess.run(command, check=False)


def _remove_binaries(options: UninstallOptions) -> None:
    if not options.remove_binaries:
        _say(options, f"Preserve OGN binaries: {options.paths.opt_dir}")
        return
    _say(options, f"Remove OGN binaries: {options.paths.opt_dir}")
    if not options.dry_run and options.paths.opt_dir.exists():
        shutil.rmtree(options.paths.opt_dir)


def _remove_config_and_state(options: UninstallOptions) -> None:
    if options.purge:
        config_targets = (options.paths.config_dir,)
    else:
        _say(options, f"Preserve config: {options.paths.config_path}")
        config_targets = (options.paths.native_config_path,)

    for target in (*config_targets, options.paths.state_dir, options.paths.log_dir):
        _say(options, f"Remove: {target}")
        if options.dry_run or not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def _remove_packages(options: UninstallOptions) -> None:
    if not options.remove_packages:
        _say(options, "Preserve Debian packages")
        return
    if options.root is not None:
        _say(options, "Skip Debian package removal under alternate root")
        return
    state = _read_install_state(options)
    if not state:
        _say(options, "Skip Debian package removal because install state is unavailable")
        return

    packages = _string_list(state.get("packages_installed_by_setup"))
    if packages:
        command = [
            "apt-get",
            "purge",
            "-y",
            "--allow-remove-essential",
            *packages,
        ]
        _run_package_command(options, command)
        _run_package_command(options, ["apt-get", "autoremove", "-y"])
    else:
        _say(options, "No setup-installed Debian packages recorded")

    for architecture in _string_list(state.get("foreign_architectures_added")):
        _remove_foreign_architecture(options, architecture)


def _read_install_state(options: UninstallOptions) -> dict[str, object] | None:
    state_path = options.paths.state_dir / INSTALL_STATE_FILENAME
    if not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UninstallError(f"cannot read install state {state_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise UninstallError(f"install state {state_path} is invalid")
    return data


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _run_package_command(options: UninstallOptions, command: list[str]) -> None:
    _say(options, "Run " + " ".join(command))
    if options.dry_run:
        return
    env = {
        **os.environ,
        "DEBIAN_FRONTEND": "noninteractive",
        "APT_LISTCHANGES_FRONTEND": "none",
    }
    subprocess.run(command, check=True, env=env)


def _remove_foreign_architecture(options: UninstallOptions, architecture: str) -> None:
    if _foreign_architecture_has_packages(architecture):
        _say(options, f"Keep foreign architecture {architecture}; packages still installed")
        return
    command = ["dpkg", "--remove-architecture", architecture]
    _say(options, "Run " + " ".join(command))
    if not options.dry_run:
        subprocess.run(command, check=False)


def _foreign_architecture_has_packages(architecture: str) -> bool:
    if not shutil.which("dpkg-query"):
        return True
    completed = subprocess.run(
        ["dpkg-query", "-W", "-f=${binary:Package}\n"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return True
    suffix = f":{architecture}"
    return any(line.strip().endswith(suffix) for line in completed.stdout.splitlines())


def _print_summary(options: UninstallOptions) -> None:
    if options.dry_run:
        return
    print()
    print("Uninstall complete.")
    if not options.purge:
        print(f"Configuration was preserved at: {options.paths.config_path}")
    if not options.remove_binaries:
        print(f"OGN binary directory was preserved at: {options.paths.opt_dir}")
    if _running_inside_virtualenv():
        print()
        print("To remove the user-owned Python virtual environment after this command exits:")
        print(f"  rm -rf {sys.prefix}")


def _running_inside_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _say(options: UninstallOptions, message: str) -> None:
    prefix = "Would " if options.dry_run else ""
    print(f"- {prefix}{message}")


if __name__ == "__main__":
    raise SystemExit(main())
