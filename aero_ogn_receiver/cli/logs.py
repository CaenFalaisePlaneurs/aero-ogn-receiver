from __future__ import annotations

import argparse
import shlex
import selectors
import subprocess
import sys
import time
import urllib.error
import urllib.request

from aero_ogn_receiver.core import systemd


TRAFFIC_LOG_COMPONENTS = {"traffic", "aprs"}
DEFAULT_AIRCRAFT_URL = "http://localhost:8081/aircraft-list-short.txt"


def add_logs_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("logs", help="Show receiver journald logs")
    parser.add_argument(
        "component",
        nargs="?",
        default="all",
        choices=["all", "rf", "decode", "traffic", "aprs"],
        help="'traffic' filters APRS plus decoded aircraft info",
    )
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    parser.add_argument("--lines", "-n", type=int, default=200, help="Number of recent lines")
    parser.add_argument("--since", help='Pass a journalctl --since value, e.g. "1 hour ago"')
    parser.add_argument("--errors", action="store_true", help="Show warnings and errors")
    parser.add_argument(
        "--include-aprs-heartbeat",
        action="store_true",
        help="For traffic logs, include APRS server heartbeat/time-sync lines",
    )
    parser.add_argument(
        "--no-aircraft",
        action="store_true",
        help="For traffic logs, do not poll the decoder aircraft-list endpoint",
    )
    parser.add_argument(
        "--aircraft-url",
        default=DEFAULT_AIRCRAFT_URL,
        help="For traffic logs, decoded aircraft list URL",
    )
    parser.add_argument(
        "--aircraft-interval",
        type=float,
        default=10.0,
        help="For followed traffic logs, aircraft polling interval in seconds",
    )
    parser.add_argument("--verbose", action="store_true", help="Print the journalctl command")
    parser.set_defaults(handler=logs_command)


def logs_command(args: argparse.Namespace) -> int:
    if args.component in TRAFFIC_LOG_COMPONENTS:
        return traffic_logs_command(args)

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
    if args.follow:
        return stream_journal(command)
    result = systemd.run_command(command)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


def traffic_logs_command(args: argparse.Namespace) -> int:
    command = systemd.journalctl_command(
        "decode",
        follow=args.follow,
        lines=args.lines,
        since=args.since,
        errors=False,
    )
    if args.verbose:
        print("+ " + shlex.join(command))
    if not systemd.command_available("journalctl"):
        print("journalctl is not available on this machine")
        return 1

    include_aircraft = not args.no_aircraft
    if args.follow:
        return stream_traffic(
            command,
            include_heartbeat=args.include_aprs_heartbeat,
            include_aircraft=include_aircraft,
            aircraft_url=args.aircraft_url,
            aircraft_interval=max(args.aircraft_interval, 1.0),
            verbose=args.verbose,
        )

    result = systemd.run_command(command)
    print_traffic_lines(result.stdout.splitlines(), include_heartbeat=args.include_aprs_heartbeat)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if include_aircraft:
        print_aircraft_snapshot(args.aircraft_url, previous=None, verbose=args.verbose)
    return result.returncode


def stream_journal(command: list[str]) -> int:
    try:
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as process:
            if process.stdout is None:
                return process.wait()
            for line in process.stdout:
                print(line, end="", flush=True)
            return process.wait()
    except KeyboardInterrupt:
        return 130


def stream_traffic(
    command: list[str],
    *,
    include_heartbeat: bool,
    include_aircraft: bool,
    aircraft_url: str,
    aircraft_interval: float,
    verbose: bool,
) -> int:
    last_aircraft: str | None = None
    next_aircraft_poll = time.monotonic()
    try:
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as process:
            if process.stdout is None:
                return process.wait()

            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                timeout = None
                if include_aircraft:
                    timeout = max(0.0, next_aircraft_poll - time.monotonic())

                events = selector.select(timeout)
                for key, _ in events:
                    line = key.fileobj.readline()
                    if line == "":
                        selector.unregister(key.fileobj)
                        return process.wait()
                    if is_traffic_log_line(line, include_heartbeat=include_heartbeat):
                        print(line, end="", flush=True)

                if include_aircraft and time.monotonic() >= next_aircraft_poll:
                    last_aircraft = print_aircraft_snapshot(
                        aircraft_url,
                        previous=last_aircraft,
                        verbose=verbose,
                    )
                    next_aircraft_poll = time.monotonic() + aircraft_interval

                if process.poll() is not None:
                    return process.returncode
    except KeyboardInterrupt:
        return 130


def print_traffic_lines(lines: list[str], *, include_heartbeat: bool) -> None:
    for line in lines:
        if is_traffic_log_line(line, include_heartbeat=include_heartbeat):
            print(line)


def is_traffic_log_line(line: str, *, include_heartbeat: bool = False) -> bool:
    if "APRS <-" in line:
        return True
    if "APRS_Sender" in line or "logresp" in line:
        return True
    if include_heartbeat and ("APRS ->" in line or "APRS time" in line):
        return True
    return any(token in line for token in ("Aircraft", "aircraft", "Acft:", "Decoded:"))


def print_aircraft_snapshot(
    url: str,
    *,
    previous: str | None,
    verbose: bool = False,
) -> str | None:
    snapshot = fetch_aircraft_snapshot(url, verbose=verbose)
    if not snapshot or snapshot == previous:
        return previous
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    for line in snapshot.splitlines():
        print(f"{timestamp} AIRCRAFT {line}", flush=True)
    return snapshot


def fetch_aircraft_snapshot(url: str, *, verbose: bool = False) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.URLError) as exc:
        if verbose:
            print(f"aircraft list unavailable: {exc}", file=sys.stderr)
        return None
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    return "\n".join(lines)
