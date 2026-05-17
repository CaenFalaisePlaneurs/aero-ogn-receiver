"""Setuptools hook for install-time data files.

Project metadata lives in pyproject.toml. This file mirrors the aero-pi-cam
pattern for installing the example config into a share directory where the
privileged setup module can find it after pip installation.
"""

from pathlib import Path

from setuptools import setup


config_example = Path(__file__).parent / "config.example.yaml"
data_files = []
if config_example.exists():
    data_files.append(("usr/share/aero-ogn-receiver", [str(config_example.name)]))

setup(
    name="aero-ogn-receiver",
    data_files=data_files,
)

