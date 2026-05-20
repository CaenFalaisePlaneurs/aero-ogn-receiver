---
layout: page
title: Installation
---

# Installation

For a copy-paste first install with verification after each step, start with
the [Quick Start](quickstart.html). This page documents the installer shape,
system package changes, and uninstall behavior in more detail.

## Hardware Requirements

Use Raspberry Pi OS on a Raspberry Pi 3B or newer for reliable real-time OGN
reception. Very old single-core models such as Raspberry Pi 1 and Raspberry Pi
Model B+ can install the software, but they may not keep up with the RF and
decoder workload.

An RTL-SDR dongle should have stable USB power. A powered USB hub can help with
USB power stability, but it does not replace CPU capacity: a single-core
700 MHz Pi can still fall behind even when the SDR is powered correctly.

## Installation Shape

These are the intended Pi commands:

```bash
sudo apt update
sudo apt install -y python3-venv git
python3 -m venv ~/aero-pi-ogn-receiver-venv
~/aero-pi-ogn-receiver-venv/bin/pip install git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config render --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
sudo systemctl enable --now aero-pi-ogn-receiver.target
```

The setup command is a guarded system installer. When run with `sudo` on
Raspberry Pi OS, it can install Debian dependencies, create `/etc` and `/opt`
project paths, render the native OGN config, download the pinned OGN archive,
verify SHA-256/MD5, extract it, install systemd units, and reload systemd. It
does not start the receiver automatically.

Use `--dry-run` to preview setup or uninstall actions without changing the
machine.

Setup writes a short command sheet into the virtual environment:
`~/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md`. It contains the common
status, service, config, upgrade, and uninstall commands, and points back to
the full project documentation for [maintenance](maintenance.html),
[troubleshooting](troubleshooting.html), and less common tasks.

The package also exposes console entry points:

```bash
aero-pi-ogn
aero-pi-ogn-setup
aero-pi-ogn-uninstall
```

There is also a thin convenience script for source checkouts:

```bash
bash scripts/install.sh
```

The script creates `~/aero-pi-ogn-receiver-venv`, installs the package into that
venv, and prints the explicit `sudo` setup/config commands. It does not replace
the privileged setup step.

## OS Package Changes

The privileged setup command is not a pure file copy. On Raspberry Pi OS it runs
`apt-get update` and installs the Debian packages required by the receiver
runtime. It does not intentionally run a full system upgrade, but apt may still
upgrade already-installed packages when Debian dependency resolution requires a
newer matching version.

Current setup dependencies include:

```text
rtl-sdr
ca-certificates
procserv
```

On 64-bit Raspberry Pi OS, `binary_arch: "auto"` currently selects the official
32-bit ARM OGN binary for runtime compatibility. In that case setup enables the
`armhf` foreign architecture if needed and installs the 32-bit runtime packages
required by the OGN binary:

```text
libc6:armhf
libstdc++6:armhf
libgcc-s1:armhf
librtlsdr0:armhf
```

This can also pull closely related dependency updates such as `systemd`, `udev`,
or shared libraries if the local image package set is behind the current
repository metadata. For the most reproducible production install, start from an
up-to-date Raspberry Pi OS image and record the package changes from setup:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup --dry-run
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
grep " install \| upgrade " /var/log/apt/history.log
```

Setup writes `/var/lib/aero-pi-ogn-receiver/install-state.json` to record the
Debian packages and foreign architectures that were added by setup. The
uninstaller can use that file to remove project-added packages later. It cannot
safely roll back unrelated package upgrades that apt performed while resolving
dependencies.

## Uninstall

To remove the receiver integration and binaries while preserving the user YAML
configuration at `/etc/aero-pi-ogn-receiver/config.yaml`:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn-uninstall --complete
```

That removes systemd units, generated native config, `/opt/aero-pi-ogn-receiver`,
state/log directories, setup-installed Debian packages, and any foreign
architecture setup added when no packages still use it. Add `--purge` only when
you also want to remove the preserved `/etc/aero-pi-ogn-receiver` configuration.

The uninstaller prints the follow-up command for removing the user-owned Python
virtual environment after it exits. With the recommended install path, that is:

```bash
rm -rf ~/aero-pi-ogn-receiver-venv
```

If `git` was installed only to fetch this project and is no longer needed on the
Pi, remove that prerequisite separately:

```bash
sudo apt purge -y git git-man liberror-perl
sudo apt autoremove -y
```
