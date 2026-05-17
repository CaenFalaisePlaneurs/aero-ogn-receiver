from __future__ import annotations

import argparse
import shlex

from aero_ogn_receiver.core import systemd


def add_logs_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("logs", help="Show receiver journald logs")
    parser.add_argument("component", nargs="?", default="all", choices=["all", "rf", "decode"])
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    parser.add_argument("--lines", "-n", type=int, default=200, help="Number of recent lines")
    parser.add_argument("--since", help='Pass a journalctl --since value, e.g. "1 hour ago"')
    parser.add_argument("--errors", action="store_true", help="Show warnings and errors")
    parser.add_argument("--verbose", action="store_true", help="Print the journalctl command")
    parser.set_defaults(handler=logs_command)


def logs_command(args: argparse.Namespace) -> int:
    command = systemd.journalctl_command(
        args.component,
        follow=args.follow,
        lines=args.lines,
        since=args.since,
        errors=args.errors,
    )
    if args.verbose:
        print("+ " + shlex.join(command))
    if not systemd.command_available("journalctl"):
        print("journalctl is not available on this machine")
        return 1
    result = systemd.run_command(command)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode

