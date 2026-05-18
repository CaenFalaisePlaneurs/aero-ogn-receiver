from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


RF_UNIT = "aero-ogn-rf.service"
DECODE_UNIT = "aero-ogn-decode.service"
TARGET_UNIT = "aero-ogn-receiver.target"
ALL_UNITS = (RF_UNIT, DECODE_UNIT)


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def journalctl_command(
    component: str = "all",
    *,
    follow: bool = False,
    lines: int = 200,
    since: str | None = None,
    errors: bool = False,
) -> list[str]:
    command = ["journalctl"]
    for unit in units_for_component(component):
        command.extend(["-u", unit])
    command.append("--no-pager")
    command.extend(["-n", str(lines)])
    if follow:
        command.append("-f")
    if since:
        command.extend(["--since", since])
    if errors:
        command.extend(["-p", "warning"])
    return command


def systemctl_command(action: str, component: str = "all") -> list[str]:
    command = ["systemctl", action]
    command.extend(units_for_component(component, include_target=(component == "all")))
    return command


def units_for_component(component: str, *, include_target: bool = False) -> tuple[str, ...]:
    if component == "rf":
        return (RF_UNIT,)
    if component == "decode":
        return (DECODE_UNIT,)
    if component == "target":
        return (TARGET_UNIT,)
    if component == "all":
        if include_target:
            return (TARGET_UNIT, RF_UNIT, DECODE_UNIT)
        return ALL_UNITS
    raise ValueError(f"unknown component: {component}")


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(command: list[str]) -> CommandResult:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
