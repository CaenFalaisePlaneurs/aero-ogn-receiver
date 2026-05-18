---
layout: default
title: aero-pi-ogn-receiver
permalink: /
---

# aero-pi-ogn-receiver

<img src="{{ '/aero-pi-ogn-receiver_logo.png' | relative_url }}" alt="aero-pi-ogn-receiver logo" style="max-width: 20vw;">

Installable OGN/FLARM receiver manager for Raspberry Pi.

`aero-pi-ogn-receiver` installs and manages an Open Glider Network receiver on an
existing Raspberry Pi OS system. It does not build a custom Raspberry Pi image.
The user workflow is to create a user-owned virtual environment, install the
package, run an explicit privileged setup command, edit one YAML config file,
and operate the service through systemd plus a Pi Connect-friendly CLI.

## Current Status

This repository is in its first implementation milestone. The Python package,
CLI, config validation, OGN config rendering, pinned binary manifest, checksum
helpers, systemd templates, setup/uninstall commands, and development-machine
tests exist.

The setup command is implemented as a guarded system installer: when run with
`sudo` on Raspberry Pi OS, it can install Debian dependencies, create `/etc` and
`/opt` project paths, render the native OGN config, download the pinned OGN
archive, verify SHA-256/MD5, extract it, install systemd units, and reload
systemd. It does not start the receiver automatically.

Use `--dry-run` to preview setup or uninstall actions without changing the
machine.

For the minimal field workflow to check whether planes are being received, see
[Quick start](quickstart.md).

## Documentation

- [Quick start](quickstart.md): minimal commands for checking whether the receiver sees aircraft.
- [Installation](installation.md): Pi install commands, package changes, setup, and uninstall.
- [CLI reference](cli.md): installed entry points, status, aircraft, logs, service, and health commands.
- [Operations](operation.md): day-to-day service operation and the generated venv command sheet.
- [OGN binaries](binaries.md): binary manifest, architecture selection, and third-party runtime policy.
- [Troubleshooting](troubleshooting.md): USB power, antenna, RF path, and field diagnosis.
- [Security policy](security.md): binary trust boundary and download/update policy.
- [Development](development.md): local test and smoke-check commands.
