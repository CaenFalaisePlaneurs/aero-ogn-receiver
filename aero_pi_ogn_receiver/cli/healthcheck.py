from __future__ import annotations

import argparse

from aero_pi_ogn_receiver.cli.status import collect_status, overall_state, print_checks


def add_healthcheck_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser("healthcheck", help="Run receiver health checks")
    parser.add_argument("--live", action="store_true", help="Include live receiver-chain checks")
    parser.set_defaults(handler=healthcheck_command)


def healthcheck_command(args: argparse.Namespace) -> int:
    report = collect_status(live=args.live)
    print_checks(report.checks)
    state = overall_state(report.checks)
    print(f"\nOverall: {state}")
    return 1 if any(check.state == "FAIL" for check in report.checks) else 0

