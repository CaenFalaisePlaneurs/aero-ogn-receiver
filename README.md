# aero-ogn-receiver

Installable OGN/FLARM receiver manager for Raspberry Pi.

`aero-ogn-receiver` installs and manages an Open Glider Network receiver on an
existing Raspberry Pi OS system. It does not build a custom Raspberry Pi image.
The user workflow follows the same product shape as `aero-pi-cam`: create a
user-owned virtual environment, install the package, run an explicit privileged
setup command, edit one YAML config file, and operate the service through
systemd plus a Pi Connect-friendly CLI.

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

## Installation Shape

These are the intended Pi commands once the real setup implementation is filled
in:

```bash
sudo apt update
sudo apt install -y python3-venv git
python3 -m venv ~/aero-ogn-receiver-venv
~/aero-ogn-receiver-venv/bin/pip install git+https://github.com/CaenFalaisePlaneurs/aero-ogn-receiver.git
sudo /home/$(whoami)/aero-ogn-receiver-venv/bin/python -m aero_ogn_receiver.setup.setup
sudo nano /etc/aero-ogn-receiver/config.yaml
sudo /home/$(whoami)/aero-ogn-receiver-venv/bin/aero-ogn config render --output /etc/aero-ogn-receiver/rtlsdr-ogn.conf
sudo systemctl enable --now aero-ogn-receiver.target
```

The package also exposes console entry points:

```bash
aero-ogn
aero-ogn-setup
aero-ogn-uninstall
```

There is also a thin convenience script for source checkouts:

```bash
bash scripts/install.sh
```

The script creates `~/aero-ogn-receiver-venv`, installs the package into that
venv, and prints the explicit `sudo` setup/config commands. It does not replace
the privileged setup step.

## CLI

Implemented first-pass commands:

```bash
aero-ogn config validate
aero-ogn config render
aero-ogn binaries list
aero-ogn status
aero-ogn status --live
aero-ogn status --watch 5
aero-ogn logs
aero-ogn logs --follow
aero-ogn service status
aero-ogn healthcheck
```

The main field operations path is:

```text
Raspberry Pi Connect -> shell/terminal -> aero-ogn CLI
```

On non-Raspberry Pi development machines, hardware and systemd checks report
`UNKNOWN` instead of crashing.

## OGN Binaries

This project is a manager/wrapper around official OGN receiver binaries. It does
not reimplement `ogn-rf` or `ogn-decode`, and it does not relicense those
binaries.

The repository must contain only source code, templates, documentation, tests,
and a binary manifest. The installer will download official OGN archives from
`download.glidernet.org` only during explicit install/update operations, verify
them against the committed SHA-256 manifest, and install them under
`/opt/aero-ogn-receiver/ogn`.

`binary_arch: "auto"` currently selects the 32-bit ARM OGN archive on Raspberry
Pi OS, including 64-bit Raspberry Pi OS, because OGN 0.3.2 arm64 crashed during
decoder connection testing on the Pi target. Explicit `arm`, `arm64`, and
`rpi_gpu` values are also accepted for manual testing.

The installed systemd units run the OGN binaries through localhost-bound
`procServ` instances for compatibility with the upstream runtime. The normal
operator interface remains `aero-ogn status`, `aero-ogn logs`, and `systemctl`;
the procServ control ports are local-only implementation details.

Do not commit `ogn-rf`, `ogn-decode`, or any `rtlsdr-ogn` archive.

## Troubleshooting

### RTL-SDR USB Power

The RTL-SDR dongle is normally powered by the Raspberry Pi USB port. If the Pi
power supply is marginal, or the dongle draws current in bursts, the receiver
can become unstable even when the software is otherwise healthy. Symptoms can
include USB disconnects, `rtl_test` failures, OGN RF restarts, high temperature,
or Raspberry Pi undervoltage/throttle flags.

Check the current and historical Pi power state:

```bash
vcgencmd get_throttled
vcgencmd measure_temp
python3 -m aero_ogn_receiver status --live
journalctl -u aero-ogn-rf.service -u aero-ogn-decode.service --since "1 hour ago" --no-pager
```

Useful `get_throttled` bits:

```text
0x1      under-voltage is currently detected
0x2      ARM frequency is currently capped
0x4      system is currently throttled
0x10000  under-voltage has occurred since boot
0x20000  ARM frequency capping has occurred since boot
0x40000  throttling has occurred since boot
```

Historical bits stay set until reboot. For a clean hardware comparison, record
the value, reboot, then run the receiver for a representative period and check
again.

A powered USB hub is a valid reliability test. It can remove the dongle current
draw from the Pi USB rail and may reduce undervoltage, USB resets, and RF noise
coupled through Pi power. Use a good powered hub that does not backfeed 5V into
the Raspberry Pi over USB.

## Development

Run the test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Useful local smoke checks:

```bash
python3 -m aero_ogn_receiver config validate
python3 -m aero_ogn_receiver binaries list
python3 -m aero_ogn_receiver status --live
python3 -m aero_ogn_receiver.setup.setup --dry-run
```

## License

Project source code, installer code, templates, and documentation are licensed
under GPL-3.0-or-later, matching the intended licensing model from
`aero-pi-cam`.

Official OGN binaries are separate third-party runtime components and are not
relicensed by this project. See `THIRD_PARTY.md` and `SECURITY.md`.
