from __future__ import annotations

import platform
import shutil
import subprocess


SUPPORTED_BINARY_ARCHES = ("auto", "arm", "arm64", "rpi_gpu")


def host_os_architecture() -> str | None:
    """Return the OS package architecture when available.

    On Raspberry Pi OS this distinguishes 32-bit and 64-bit userlands. The
    resolver currently prefers the 32-bit OGN archive for auto mode because
    OGN 0.3.2 arm64 crashes when the decoder connects on the test Pi.
    """

    if shutil.which("dpkg"):
        completed = subprocess.run(
            ["dpkg", "--print-architecture"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            architecture = completed.stdout.strip()
            if architecture:
                return architecture

    machine = platform.machine().lower()
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    if machine.startswith(("armv", "arm")):
        return "arm"
    return machine or None


def resolve_binary_arch(configured_arch: str, host_arch: str | None = None) -> str:
    if configured_arch not in SUPPORTED_BINARY_ARCHES:
        raise ValueError(
            f"unsupported OGN binary architecture {configured_arch!r}; "
            f"expected one of: {', '.join(SUPPORTED_BINARY_ARCHES)}"
        )
    if configured_arch != "auto":
        return configured_arch

    architecture = host_arch or host_os_architecture()
    if architecture in {"arm64", "aarch64"}:
        return "arm"
    if architecture in {"armhf", "armel", "arm"}:
        return "arm"
    return "arm"
