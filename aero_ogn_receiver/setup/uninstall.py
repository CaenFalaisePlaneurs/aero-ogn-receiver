from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aero_ogn_receiver.setup.setup import SYSTEMD_UNITS, SetupPaths


@dataclass(frozen=True)
class UninstallOptions:
    dry_run: bool
    purge: bool
    remove_binaries: bool
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
        "--remove-binaries",
        action="store_true",
        help="Remove /opt/aero-ogn-receiver",
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
        remove_binaries=args.remove_binaries,
        no_daemon_reload=args.no_daemon_reload or args.root is not None,
        paths=SetupPaths.under_root(args.root) if args.root else SetupPaths.system(),
        root=args.root,
    )

    try:
        run_uninstall(options)
    except (UninstallError, OSError) as exc:
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
    if not options.purge:
        _say(options, f"Preserve config: {options.paths.config_path}")
        _say(options, f"Preserve state: {options.paths.state_dir}")
        return

    for target in (options.paths.config_dir, options.paths.state_dir, options.paths.log_dir):
        _say(options, f"Remove: {target}")
        if not options.dry_run and target.exists():
            shutil.rmtree(target)


def _print_summary(options: UninstallOptions) -> None:
    if options.dry_run:
        return
    print()
    print("Uninstall complete.")
    if not options.purge:
        print(f"Configuration was preserved at: {options.paths.config_path}")
    if not options.remove_binaries:
        print(f"OGN binary directory was preserved at: {options.paths.opt_dir}")


def _say(options: UninstallOptions, message: str) -> None:
    prefix = "Would " if options.dry_run else ""
    print(f"- {prefix}{message}")


if __name__ == "__main__":
    raise SystemExit(main())
