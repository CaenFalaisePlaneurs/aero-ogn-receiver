from __future__ import annotations

import json

from aero_ogn_receiver.core import paths
from aero_ogn_receiver.core.config_model import AppConfig


def render_ogn_config(config: AppConfig) -> str:
    template = paths.template_path("rtlsdr-ogn.conf.j2").read_text(encoding="utf-8")
    replacements = {
        "{{ receiver.name }}": _quote(config.receiver.name),
        "{{ receiver.latitude }}": _format_coordinate(config.receiver.latitude),
        "{{ receiver.longitude }}": _format_coordinate(config.receiver.longitude),
        "{{ receiver.altitude_m }}": str(config.receiver.altitude_m),
        "{{ radio.ppm_correction }}": str(config.radio.ppm_correction),
        "{{ radio.gsm_section }}": _render_gsm_section(config),
        "{{ radio.ogn_gain_db }}": _format_number(config.radio.ogn_gain_db),
        "{{ radio.bias_tee }}": "1" if config.radio.bias_tee else "0",
        "{{ ogn.aprs_server }}": _quote(config.ogn.aprs_server),
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def _quote(value: str) -> str:
    return json.dumps(value)


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _render_gsm_section(config: AppConfig) -> str:
    if not config.radio.gsm_calibration:
        return ""
    center_freq = _format_number(config.radio.gsm_center_freq_mhz)
    gain = _format_number(config.radio.gsm_gain_db)
    return (
        "  GSM:\n"
        "  {\n"
        f"    CenterFreq = {center_freq};\n"
        f"    Gain = {gain};\n"
        "  };\n"
    )


def _format_coordinate(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")
