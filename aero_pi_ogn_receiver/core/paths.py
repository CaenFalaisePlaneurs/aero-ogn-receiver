from __future__ import annotations

from importlib import resources
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent

CONFIG_DIR = Path("/etc/aero-pi-ogn-receiver")
CONFIG_PATH = CONFIG_DIR / "config.yaml"
NATIVE_CONFIG_PATH = CONFIG_DIR / "rtlsdr-ogn.conf"
INSTALL_MANIFEST_PATH = CONFIG_DIR / "install-manifest.json"

OPT_DIR = Path("/opt/aero-pi-ogn-receiver")
OGN_INSTALL_DIR = OPT_DIR / "ogn"
OGN_CURRENT_DIR = OGN_INSTALL_DIR / "current"

STATE_DIR = Path("/var/lib/aero-pi-ogn-receiver")
LOG_DIR = Path("/var/log/aero-pi-ogn-receiver")


def manifest_path() -> Path:
    return data_path("ogn-binaries.yaml")


def data_path(name: str) -> Path:
    return Path(str(resources.files("aero_pi_ogn_receiver.data").joinpath(name)))


def template_path(name: str) -> Path:
    return Path(str(resources.files("aero_pi_ogn_receiver.templates").joinpath(name)))


def example_config_path() -> Path:
    cwd_candidate = Path.cwd() / "config.example.yaml"
    if cwd_candidate.exists():
        return cwd_candidate
    source_candidate = PROJECT_ROOT / "config.example.yaml"
    if source_candidate.exists():
        return source_candidate
    share_candidate = Path("/usr/share/aero-pi-ogn-receiver/config.example.yaml")
    if share_candidate.exists():
        return share_candidate
    return data_path("config.example.yaml")


def default_read_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return example_config_path()
