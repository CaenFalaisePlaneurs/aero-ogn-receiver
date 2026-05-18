from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_SHORT_URL = "http://localhost:8081/aircraft-list-short.txt"
DEFAULT_LONG_URL = "http://localhost:8081/aircraft-list.txt"

LOCAL_TRACK_RE = re.compile(
    r"(?P<age>\d+(?:\.\d+)?)s\s+"
    r"(?P<identifier>[0-9A-Fa-f]{2}:[0-9A-Fa-f]{6})\s+"
    r"\[(?P<latitude>[+-]?\d+(?:\.\d+)?),\s*(?P<longitude>[+-]?\d+(?:\.\d+)?)\]deg\s+"
    r"(?P<altitude_m>-?\d+)m,\s+"
    r"(?P<heading_deg>\d{1,3})deg\s+"
    r"(?P<speed_kt>\d+)kt\s+"
    r"#(?P<kind>[0-9A-Fa-f]{2})\s+"
    r"(?P<signal_db>[+-]?\d+(?:\.\d+)?/[+-]?\d+(?:\.\d+)?dB)\s+"
    r"(?P<freq_offset_khz>[+-]?\d+(?:\.\d+)?)kHz"
)

APRS_RE = re.compile(
    r"(?P<identifier>[A-Za-z0-9?_-]+)>[^:]+:"
    r"(?P<body>.*)"
)
APRS_POS_RE = re.compile(
    r"(?P<time>\d{6})h"
    r"(?P<lat_deg>\d{2})(?P<lat_min>\d{2}\.\d+)(?P<lat_ns>[NS])"
    r"."
    r"(?P<lon_deg>\d{3})(?P<lon_min>\d{2}\.\d+)(?P<lon_ew>[EW])"
    r"."
    r"(?:(?P<heading_deg>\d{3})/(?P<speed_kt>\d{3}))?"
    r".*?/A=(?P<altitude_ft>\d{6})"
)
DB_NAME_RE = re.compile(r'Name="(?P<name>[^"]+)"')
SIGNAL_RE = re.compile(r"(?P<signal_db>[+-]?\d+(?:\.\d+)?)dB")
FREQ_RE = re.compile(r"(?P<freq_offset_khz>[+-]?\d+(?:\.\d+)?)kHz")


@dataclass(frozen=True)
class AircraftTrack:
    identifier: str
    latitude: str = ""
    longitude: str = ""
    altitude_m: str = ""
    speed_kt: str = ""
    heading_deg: str = ""
    quality: str = ""
    age: str = ""
    raw: str = ""


def add_aircraft_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "aircraft",
        help="Show locally decoded aircraft from the OGN decoder HTTP endpoint",
    )
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="Refresh at this interval")
    parser.add_argument("--long", action="store_true", help="Use aircraft-list.txt instead of short")
    parser.add_argument("--raw", action="store_true", help="Print raw endpoint lines")
    parser.add_argument("--url", help="Override aircraft list URL")
    parser.add_argument("--timeout", type=float, default=3.0, help="HTTP timeout in seconds")
    parser.set_defaults(handler=aircraft_command)


def aircraft_command(args: argparse.Namespace) -> int:
    url = args.url or (DEFAULT_LONG_URL if args.long else DEFAULT_SHORT_URL)
    if args.watch is not None:
        interval = max(args.watch, 1.0)
        try:
            while True:
                print("\033[H\033[J", end="")
                exit_code = print_aircraft(url, timeout=args.timeout, raw=args.raw)
                time.sleep(interval)
        except KeyboardInterrupt:
            print()
            return 0
        return exit_code
    return print_aircraft(url, timeout=args.timeout, raw=args.raw)


def print_aircraft(url: str, *, timeout: float, raw: bool) -> int:
    try:
        text = fetch_aircraft_text(url, timeout=timeout)
    except AircraftFetchError as exc:
        print(f"Aircraft list unavailable: {exc}", file=sys.stderr)
        return 1

    lines = cleaned_lines(text)
    print("Local decoded aircraft")
    print(f"Source: {url}")
    print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not lines:
        print("No aircraft currently tracked by the local decoder.")
        return 0

    if raw:
        for line in lines:
            print(line)
        return 0

    tracks = [parse_aircraft_line(line) for line in lines]
    print_aircraft_table(tracks)
    return 0


class AircraftFetchError(RuntimeError):
    pass


def fetch_aircraft_text(url: str, *, timeout: float = 3.0) -> str:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.URLError) as exc:
        raise AircraftFetchError(str(exc)) from exc


def cleaned_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_aircraft_line(line: str) -> AircraftTrack:
    local_match = LOCAL_TRACK_RE.search(line)
    if local_match:
        groups = local_match.groupdict()
        return AircraftTrack(
            identifier=groups["identifier"].upper(),
            latitude=groups["latitude"],
            longitude=groups["longitude"],
            altitude_m=groups["altitude_m"],
            speed_kt=groups["speed_kt"],
            heading_deg=groups["heading_deg"],
            quality=f"{groups['signal_db']} {groups['freq_offset_khz']}kHz",
            age=f"{groups['age']}s",
            raw=line,
        )

    aprs_match = APRS_RE.search(line)
    if aprs_match:
        identifier = aprs_match.group("identifier")
        body = aprs_match.group("body")
        name_match = DB_NAME_RE.search(line)
        if name_match:
            identifier = name_match.group("name")
        pos_match = APRS_POS_RE.search(body)
        if pos_match:
            groups = pos_match.groupdict()
            quality_parts = _aprs_quality_parts(line)
            return AircraftTrack(
                identifier=identifier,
                latitude=f"{_aprs_coordinate(groups['lat_deg'], groups['lat_min'], groups['lat_ns']):.5f}",
                longitude=f"{_aprs_coordinate(groups['lon_deg'], groups['lon_min'], groups['lon_ew']):.5f}",
                altitude_m=str(round(int(groups["altitude_ft"]) * 0.3048)),
                speed_kt=(groups.get("speed_kt") or "").lstrip("0") or groups.get("speed_kt") or "",
                heading_deg=(groups.get("heading_deg") or "").lstrip("0")
                or groups.get("heading_deg")
                or "",
                quality=" ".join(quality_parts),
                raw=line,
            )
        return AircraftTrack(identifier=identifier, raw=line)

    return AircraftTrack(identifier="?", raw=line)


def print_aircraft_table(tracks: list[AircraftTrack]) -> None:
    rows = [
        [
            track.identifier,
            track.age,
            track.latitude,
            track.longitude,
            track.altitude_m,
            track.speed_kt,
            track.heading_deg,
            track.quality,
        ]
        for track in tracks
    ]
    headers = ["ID/REG", "AGE", "LAT", "LON", "ALT_M", "KT", "HDG", "QUALITY"]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    if any(track.identifier == "?" for track in tracks):
        print()
        print("Some rows used an unknown upstream format; rerun with --raw to inspect them.")


def _aprs_coordinate(degrees: str, minutes: str, hemisphere: str) -> float:
    value = int(degrees) + float(minutes) / 60.0
    if hemisphere in {"S", "W"}:
        return -value
    return value


def _aprs_quality_parts(line: str) -> list[str]:
    parts: list[str] = []
    signal_matches = list(SIGNAL_RE.finditer(line))
    if signal_matches:
        parts.append(f"{signal_matches[-1].group('signal_db')}dB")
    freq_match = FREQ_RE.search(line)
    if freq_match:
        parts.append(f"{freq_match.group('freq_offset_khz')}kHz")
    return parts
