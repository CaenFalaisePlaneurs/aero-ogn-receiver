from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aero_ogn_receiver.core.architecture import SUPPORTED_BINARY_ARCHES
from aero_ogn_receiver.core import simple_yaml


class ConfigError(ValueError):
    """Raised when user YAML config is invalid."""


@dataclass(frozen=True)
class ReceiverConfig:
    name: str
    latitude: float
    longitude: float
    altitude_m: int


@dataclass(frozen=True)
class RadioConfig:
    ppm_correction: int
    gsm_calibration: bool
    gsm_center_freq_mhz: float
    gsm_gain_db: float
    ogn_gain_db: float
    bias_tee: bool


@dataclass(frozen=True)
class OgnConfig:
    aprs_server: str
    version: str
    binary_arch: str


@dataclass(frozen=True)
class ServiceConfig:
    start_on_boot: bool


@dataclass(frozen=True)
class AppConfig:
    receiver: ReceiverConfig
    radio: RadioConfig
    ogn: OgnConfig
    service: ServiceConfig


def load_config(path: Path) -> AppConfig:
    try:
        data = simple_yaml.load(path)
    except simple_yaml.YamlError as exc:
        raise ConfigError(f"{path}: {exc}") from exc
    return parse_config(data)


def parse_config(data: object) -> AppConfig:
    if not isinstance(data, dict):
        raise ConfigError("config root must be a mapping")

    receiver = _mapping(data, "receiver")
    radio = _mapping(data, "radio")
    ogn = _mapping(data, "ogn")
    service = _mapping(data, "service")

    return AppConfig(
        receiver=ReceiverConfig(
            name=_non_empty_string(receiver, "name"),
            latitude=_number(receiver, "latitude", minimum=-90.0, maximum=90.0),
            longitude=_number(receiver, "longitude", minimum=-180.0, maximum=180.0),
            altitude_m=_integer(receiver, "altitude_m", minimum=-500, maximum=10000),
        ),
        radio=RadioConfig(
            ppm_correction=_integer(radio, "ppm_correction", minimum=-200, maximum=200),
            gsm_calibration=_optional_boolean(radio, "gsm_calibration", default=False),
            gsm_center_freq_mhz=_number(
                radio, "gsm_center_freq_mhz", minimum=800.0, maximum=1100.0
            ),
            gsm_gain_db=_number(radio, "gsm_gain_db", minimum=0.0, maximum=100.0),
            ogn_gain_db=_number(radio, "ogn_gain_db", minimum=0.0, maximum=100.0),
            bias_tee=_boolean(radio, "bias_tee"),
        ),
        ogn=OgnConfig(
            aprs_server=_aprs_server(ogn, "aprs_server"),
            version=_non_empty_string(ogn, "version"),
            binary_arch=_binary_arch(ogn, "binary_arch"),
        ),
        service=ServiceConfig(
            start_on_boot=_boolean(service, "start_on_boot"),
        ),
    )


def _mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a mapping")
    return value


def _non_empty_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value.strip()


def _boolean(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be true or false")
    return value


def _optional_boolean(data: dict[str, Any], key: str, *, default: bool) -> bool:
    if key not in data:
        return default
    return _boolean(data, key)


def _integer(
    data: dict[str, Any], key: str, *, minimum: int | None = None, maximum: int | None = None
) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{key} must be an integer")
    if minimum is not None and value < minimum:
        raise ConfigError(f"{key} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{key} must be <= {maximum}")
    return value


def _number(
    data: dict[str, Any],
    key: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{key} must be a number")
    number = float(value)
    if minimum is not None and number < minimum:
        raise ConfigError(f"{key} must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise ConfigError(f"{key} must be <= {maximum}")
    return number


def _aprs_server(data: dict[str, Any], key: str) -> str:
    value = _non_empty_string(data, key)
    host, separator, port = value.rpartition(":")
    if not host or separator != ":" or not port.isdigit():
        raise ConfigError(f"{key} must look like host:port")
    port_number = int(port)
    if port_number < 1 or port_number > 65535:
        raise ConfigError(f"{key} port must be between 1 and 65535")
    return value


def _binary_arch(data: dict[str, Any], key: str) -> str:
    value = _non_empty_string(data, key)
    if value not in SUPPORTED_BINARY_ARCHES:
        raise ConfigError(f"{key} must be one of: {', '.join(SUPPORTED_BINARY_ARCHES)}")
    return value
