from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from aero_pi_ogn_receiver.core import paths, systemd
from aero_pi_ogn_receiver.core.architecture import resolve_binary_arch
from aero_pi_ogn_receiver.core.config_model import AppConfig, ConfigError, load_config
from aero_pi_ogn_receiver.core.manifest import ManifestError, load_manifest


STATES = ("OK", "WARN", "FAIL", "UNKNOWN")


@dataclass(frozen=True)
class StatusCheck:
    component: str
    state: str
    evidence: str


@dataclass(frozen=True)
class StatusReport:
    config_path: Path
    config: AppConfig | None
    checks: list[StatusCheck]


def add_status_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("status", help="Show receiver status")
    parser.add_argument("--live", action="store_true", help="Run live receiver-chain checks")
    parser.add_argument(
        "--watch",
        type=float,
        metavar="SECONDS",
        help="Repeat live status at the given interval",
    )
    parser.set_defaults(handler=status_command)


def status_command(args: argparse.Namespace) -> int:
    if args.watch is not None:
        interval = max(args.watch, 1.0)
        try:
            while True:
                print("\033[H\033[J", end="")
                report = collect_status(live=True)
                print_status(report, live=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            print()
            return 0

    report = collect_status(live=args.live)
    print_status(report, live=args.live)
    return 1 if any(check.state == "FAIL" for check in report.checks) else 0


def collect_status(*, live: bool = False) -> StatusReport:
    config_path = paths.default_read_config_path()
    config: AppConfig | None = None
    checks: list[StatusCheck] = []

    try:
        config = load_config(config_path)
    except (ConfigError, FileNotFoundError) as exc:
        checks.append(StatusCheck("config", "FAIL", str(exc)))
    else:
        checks.append(StatusCheck("config", "OK", f"loaded {config_path}"))
        checks.append(_manifest_check(config))

    checks.append(_installed_binary_check())
    checks.extend(_service_checks())

    if live:
        checks.extend(
            [
                _time_check(),
                _rtl_sdr_check(),
                _status_page_check("rf status page", "http://localhost:8080/status.html"),
                _status_page_check(
                    "decode status page", "http://localhost:8081/status.html"
                ),
                _runtime_stability_check(),
                _host_capacity_check(),
                _cpu_temperature_check(),
                _disk_space_check(),
            ]
        )

    return StatusReport(config_path=config_path, config=config, checks=checks)


def print_status(report: StatusReport, *, live: bool = False) -> None:
    title = "OGN receiver live status" if live else "OGN receiver status"
    print(title)
    if report.config:
        resolved_arch = resolve_binary_arch(report.config.ogn.binary_arch)
        arch_text = resolved_arch
        if report.config.ogn.binary_arch == "auto":
            arch_text = f"auto -> {resolved_arch}"
        print(f"Receiver: {report.config.receiver.name}")
        print(f"Config:   {report.config_path}")
        print(
            "OGN:      "
            f"{report.config.ogn.version} {arch_text}, "
            f"{report.config.ogn.aprs_server}"
        )
    else:
        print(f"Config:   {report.config_path}")
    print()
    print_checks(report.checks)
    print()
    print(f"Overall: {overall_state(report.checks)}")


def print_checks(checks: list[StatusCheck]) -> None:
    component_width = max([len("Component"), *(len(check.component) for check in checks)])
    print(f"{'Component':<{component_width}}  State    Evidence")
    print(f"{'-' * component_width}  -------  --------")
    for check in checks:
        print(f"{check.component:<{component_width}}  {check.state:<7}  {check.evidence}")


def overall_state(checks: list[StatusCheck]) -> str:
    states = {check.state for check in checks}
    if "FAIL" in states:
        return "FAIL"
    if "WARN" in states:
        return "WARN"
    if "UNKNOWN" in states:
        return "UNKNOWN"
    return "OK"


def _manifest_check(config: AppConfig) -> StatusCheck:
    try:
        arch = resolve_binary_arch(config.ogn.binary_arch)
        entry = load_manifest().get(config.ogn.version, arch)
    except ManifestError as exc:
        return StatusCheck("binary manifest", "FAIL", str(exc))
    return StatusCheck(
        "binary manifest",
        "OK",
        f"{entry.version} {entry.arch}, sha256 {entry.sha256[:12]}...",
    )


def _installed_binary_check() -> StatusCheck:
    rf_path = paths.OGN_CURRENT_DIR / "ogn-rf"
    decode_path = paths.OGN_CURRENT_DIR / "ogn-decode"
    if rf_path.exists() and decode_path.exists():
        missing_interpreter = _missing_elf_interpreter(rf_path) or _missing_elf_interpreter(
            decode_path
        )
        if missing_interpreter:
            return StatusCheck(
                "installed binary",
                "FAIL",
                f"missing runtime loader {missing_interpreter}",
            )
        return StatusCheck("installed binary", "OK", str(paths.OGN_CURRENT_DIR))
    if paths.OGN_CURRENT_DIR.exists():
        return StatusCheck("installed binary", "FAIL", "ogn-rf or ogn-decode is missing")
    return StatusCheck("installed binary", "UNKNOWN", "not installed in /opt")


def _missing_elf_interpreter(binary_path: Path) -> str | None:
    try:
        data = binary_path.read_bytes()
    except OSError:
        return None
    marker = b"/lib/ld-linux-armhf.so.3"
    if marker in data and not Path(marker.decode("ascii")).exists():
        return marker.decode("ascii")
    return None


def _service_checks() -> list[StatusCheck]:
    return [
        _systemd_unit_check("rf service", systemd.RF_UNIT),
        _systemd_unit_check("decode service", systemd.DECODE_UNIT),
    ]


def _systemd_unit_check(component: str, unit: str) -> StatusCheck:
    if not systemd.command_available("systemctl"):
        return StatusCheck(component, "UNKNOWN", "systemctl is not available")
    command = [
        "systemctl",
        "show",
        unit,
        "--property=LoadState",
        "--property=ActiveState",
        "--property=SubState",
        "--property=MainPID",
        "--property=NRestarts",
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip() or "systemctl failed"
        return StatusCheck(component, "UNKNOWN", message)

    properties = {}
    for line in completed.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            properties[key] = value

    if properties.get("LoadState") == "not-found":
        return StatusCheck(component, "UNKNOWN", f"{unit} is not installed")
    active = properties.get("ActiveState", "unknown")
    sub = properties.get("SubState", "unknown")
    pid = properties.get("MainPID", "0")
    restarts = int(properties.get("NRestarts", "0") or "0")
    if active == "active":
        if restarts > 0:
            return StatusCheck(component, "WARN", f"{unit} active/{sub}, pid {pid}, restarts {restarts}")
        return StatusCheck(component, "OK", f"{unit} active/{sub}, pid {pid}")
    if active == "failed":
        return StatusCheck(component, "FAIL", f"{unit} failed/{sub}")
    return StatusCheck(component, "WARN", f"{unit} {active}/{sub}")


def _time_check() -> StatusCheck:
    if not systemd.command_available("timedatectl"):
        return StatusCheck("system time", "UNKNOWN", "timedatectl is not available")
    command = ["timedatectl", "show", "--property=NTPSynchronized", "--value"]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return StatusCheck("system time", "UNKNOWN", "time sync state unavailable")
    synchronized = completed.stdout.strip().lower()
    if synchronized == "yes":
        return StatusCheck("system time", "OK", "synchronized")
    if synchronized == "no":
        return StatusCheck("system time", "WARN", "not synchronized")
    return StatusCheck("system time", "UNKNOWN", f"unexpected state {synchronized!r}")


def _rtl_sdr_check() -> StatusCheck:
    if shutil.which("lsusb"):
        completed = subprocess.run(["lsusb"], check=False, capture_output=True, text=True)
        if completed.returncode == 0:
            device = _find_rtl_sdr_usb_device(completed.stdout)
            if device:
                return StatusCheck("usb receiver", "OK", device)
            return StatusCheck("usb receiver", "FAIL", "no RTL-SDR USB device found")
    if shutil.which("rtl_test"):
        return StatusCheck("usb receiver", "UNKNOWN", "rtl_test present; active probe not run")
    return StatusCheck("usb receiver", "UNKNOWN", "rtl-sdr tools are not available")


def _find_rtl_sdr_usb_device(lsusb_output: str) -> str | None:
    for line in lsusb_output.splitlines():
        lower = line.lower()
        if "0bda:2838" in lower or "rtl2838" in lower or "nesdr" in lower:
            return line.strip()
    return None


def _status_page_check(component: str, url: str) -> StatusCheck:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            if response.status == 200:
                return StatusCheck(component, "OK", url)
            return StatusCheck(component, "WARN", f"{url} returned HTTP {response.status}")
    except urllib.error.URLError as exc:
        return StatusCheck(component, "UNKNOWN", f"{url} unavailable: {exc.reason}")
    except TimeoutError:
        return StatusCheck(component, "WARN", f"{url} timed out")


def _runtime_stability_check() -> StatusCheck:
    if not systemd.command_available("journalctl"):
        return StatusCheck("runtime stability", "UNKNOWN", "journalctl is not available")
    command = systemd.journalctl_command("all", lines=300, since="10 minutes ago")
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip() or "journalctl failed"
        return StatusCheck("runtime stability", "UNKNOWN", message)
    return _runtime_stability_from_journal(completed.stdout)


def _runtime_stability_from_journal(journal_output: str) -> StatusCheck:
    child_crashes = _count_lines(journal_output, "killed by signal")
    child_restarts = _count_lines(journal_output, "Restarting child")
    demod_lag = _count_lines(journal_output, "Demodulator is")
    dropped_slots = _count_lines(journal_output, "Dropped a slot")
    if child_crashes:
        return StatusCheck(
            "runtime stability",
            "FAIL",
            (
                f"{child_crashes} child crash(es), {child_restarts} child restart(s), "
                f"{demod_lag} demod lag warning(s), {dropped_slots} RF dropped slot(s)"
            ),
        )
    if child_restarts or demod_lag or dropped_slots:
        return StatusCheck(
            "runtime stability",
            "WARN",
            (
                f"{child_restarts} child restart(s), {demod_lag} demod lag warning(s), "
                f"{dropped_slots} RF dropped slot(s)"
            ),
        )
    return StatusCheck("runtime stability", "OK", "no recent child crashes or RF lag warnings")


def _count_lines(text: str, marker: str) -> int:
    return sum(1 for line in text.splitlines() if marker in line)


def _host_capacity_check() -> StatusCheck:
    machine = platform.machine()
    cpu_count = _cpu_count()
    model = _raspberry_pi_model()
    description_parts = []
    if model:
        description_parts.append(model)
    description_parts.extend([machine, f"{cpu_count} CPU(s)"])
    description = ", ".join(description_parts)
    if machine == "armv6l" or cpu_count <= 1:
        return StatusCheck(
            "host capacity",
            "WARN",
            f"{description}; may not keep up with real-time OGN decoding",
        )
    return StatusCheck("host capacity", "OK", description)


def _cpu_count() -> int:
    return max(1, int((os.cpu_count() or 1)))


def _raspberry_pi_model() -> str | None:
    model_path = Path("/proc/device-tree/model")
    try:
        return model_path.read_text(encoding="utf-8").rstrip("\x00\n")
    except OSError:
        return None


def _cpu_temperature_check() -> StatusCheck:
    temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if not temp_path.exists():
        return StatusCheck("cpu temperature", "UNKNOWN", "thermal sensor unavailable")
    try:
        celsius = int(temp_path.read_text(encoding="utf-8").strip()) / 1000.0
    except (OSError, ValueError) as exc:
        return StatusCheck("cpu temperature", "UNKNOWN", str(exc))
    if celsius >= 80.0:
        return StatusCheck("cpu temperature", "WARN", f"{celsius:.1f} C")
    return StatusCheck("cpu temperature", "OK", f"{celsius:.1f} C")


def _disk_space_check() -> StatusCheck:
    usage = shutil.disk_usage("/")
    free_percent = usage.free / usage.total * 100
    if free_percent <= 5:
        return StatusCheck("disk space", "FAIL", f"{free_percent:.1f}% free on /")
    if free_percent <= 10:
        return StatusCheck("disk space", "WARN", f"{free_percent:.1f}% free on /")
    return StatusCheck("disk space", "OK", f"{free_percent:.1f}% free on /")
