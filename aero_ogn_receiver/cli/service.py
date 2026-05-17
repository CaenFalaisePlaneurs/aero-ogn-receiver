from __future__ import annotations

import argparse
import shlex

from aero_ogn_receiver.core import systemd


def add_service_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("service", help="Inspect project-owned systemd units")
    service_subparsers = parser.add_subparsers(dest="service_command", required=True)

    status = service_subparsers.add_parser("status", help="Show systemd status")
    status.add_argument("component", nargs="?", default="all", choices=["all", "rf", "decode"])
    status.add_argument("--verbose", action="store_true", help="Print the systemctl command")
    status.set_defaults(handler=status_command)


def status_command(args: argparse.Namespace) -> int:
    command = systemd.systemctl_command("status", args.component)
    if args.verbose:
        print("+ " + shlex.join(command))
    if not systemd.command_available("systemctl"):
        print("systemctl is not available on this machine")
        return 0
    result = systemd.run_command(command)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode

