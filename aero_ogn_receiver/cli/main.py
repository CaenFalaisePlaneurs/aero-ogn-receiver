from __future__ import annotations

import argparse
from collections.abc import Sequence

from aero_ogn_receiver import __version__
from aero_ogn_receiver.cli import aircraft, binaries, config, healthcheck, logs, service, status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aero-ogn",
        description="Manage an installable OGN/FLARM receiver on Raspberry Pi.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    config.add_config_parser(subparsers)
    binaries.add_binaries_parser(subparsers)
    status.add_status_parser(subparsers)
    aircraft.add_aircraft_parser(subparsers)
    logs.add_logs_parser(subparsers)
    service.add_service_parser(subparsers)
    healthcheck.add_healthcheck_parser(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    return int(args.handler(args))
