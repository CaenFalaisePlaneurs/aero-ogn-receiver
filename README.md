# aero-ogn-receiver

Installable OGN/FLARM receiver manager for Raspberry Pi.

`aero-ogn-receiver` installs and manages an Open Glider Network receiver on an
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
[QUICKSTART.md](QUICKSTART.md).

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
sudo /home/$(whoami)/aero-ogn-receiver-venv/bin/python -m aero_ogn_receiver.setup.setup --dry-run
sudo /home/$(whoami)/aero-ogn-receiver-venv/bin/python -m aero_ogn_receiver.setup.setup
grep " install \| upgrade " /var/log/apt/history.log
```

Setup writes `/var/lib/aero-ogn-receiver/install-state.json` to record the
Debian packages and foreign architectures that were added by setup. The
uninstaller can use that file to remove project-added packages later. It cannot
safely roll back unrelated package upgrades that apt performed while resolving
dependencies.

To remove the receiver integration and binaries while preserving the user YAML
configuration at `/etc/aero-ogn-receiver/config.yaml`:

```bash
sudo /home/$(whoami)/aero-ogn-receiver-venv/bin/aero-ogn-uninstall --complete
```

That removes systemd units, generated native config, `/opt/aero-ogn-receiver`,
state/log directories, setup-installed Debian packages, and any foreign
architecture setup added when no packages still use it. Add `--purge` only when
you also want to remove the preserved `/etc/aero-ogn-receiver` configuration.

The uninstaller prints the follow-up command for removing the user-owned Python
virtual environment after it exits. With the recommended install path, that is:

```bash
rm -rf ~/aero-ogn-receiver-venv
```

If `git` was installed only to fetch this project and is no longer needed on the
Pi, remove that prerequisite separately:

```bash
sudo apt purge -y git git-man liberror-perl
sudo apt autoremove -y
```

## Installation Shape

These are the intended Pi commands:

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

Setup writes a short command sheet into the virtual environment:
`~/aero-ogn-receiver-venv/README-aero-ogn-receiver.md`. It contains the common
status, service, config, upgrade, and uninstall commands, and points back to
this README for troubleshooting and less common tasks.

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

The `aero-ogn` command is created by package installation. If the package is
installed in the recommended virtual environment, either call it with the full
venv path or add the venv `bin` directory to `PATH`:

```bash
/home/$(whoami)/aero-ogn-receiver-venv/bin/aero-ogn status --live
export PATH="$HOME/aero-ogn-receiver-venv/bin:$PATH"
aero-ogn status --live
```

From an unpacked source checkout that has not been installed, use the module
form instead:

```bash
python3 -m aero_ogn_receiver status --live
python3 -m aero_ogn_receiver config validate
```

Implemented first-pass commands, shown here using the installed entry point:

```bash
aero-ogn config validate
aero-ogn config render
aero-ogn binaries list
aero-ogn status
aero-ogn status --live
aero-ogn status --watch 5
aero-ogn aircraft
aero-ogn aircraft --watch 5
aero-ogn logs
aero-ogn logs --follow
aero-ogn logs traffic --follow
aero-ogn service status
aero-ogn healthcheck
```

`aero-ogn aircraft` is the local aircraft tracking view. It reads the upstream
decoder's `http://localhost:8081/aircraft-list-short.txt` endpoint and displays
the identity available from the decoder, GPS position, altitude, speed, heading,
and signal/frequency quality fields when those fields are present. Registration
or immatriculation is only shown when the upstream decoder/device database
provides it; otherwise the FLARM/OGN device ID is shown.

Aircraft command reference:

```bash
aero-ogn aircraft              # one-shot local aircraft table
aero-ogn aircraft --watch 5    # refresh the table every 5 seconds
aero-ogn aircraft --raw        # print raw decoder aircraft-list rows
aero-ogn aircraft --long       # use aircraft-list.txt instead of short
```

`aero-ogn logs traffic --follow` is the focused live view for APRS and decoded
aircraft activity. It filters the decoder journal down to useful APRS send/login
lines and polls the upstream decoder aircraft list endpoint when aircraft are
currently decoded.

Traffic log command reference:

```bash
aero-ogn logs traffic --follow
aero-ogn logs aprs --follow
aero-ogn logs traffic --follow --include-aprs-heartbeat
aero-ogn logs traffic --follow --no-aircraft
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

### Antenna Or RF Path

A bad antenna, feedline, adapter, active antenna/LNA, or bias tee configuration
often does not look like a software failure. The services can be active, the
USB SDR can be detected, and the receiver status can still show `Overall: OK`.
The symptom is that the receiver does not see useful aircraft traffic.

Typical commands:

```bash
aero-ogn status --live
aero-ogn aircraft --watch 5
aero-ogn logs traffic --follow
aero-ogn logs rf --follow
```

Common antenna/RF-path symptom pattern:

```text
status --live      Overall: OK
aircraft --watch   No aircraft currently tracked by the local decoder.
logs traffic       APRS status repeatedly reports 0/0Acfts[1h]
logs rf            BkgNoise stays unusually low/flat or high/unstable
```

Example APRS status line with no aircraft received:

```text
APRS <- LFAS>OGNSDR:>095907h v0.3.2.ARM CPU:1.1 RAM:197.7/950.0MB NTP:0.0ms/-2.1ppm +70.9C EGM96:+47m 0/0Acfts[1h] RF:+0+0.0ppm/+3.31dB
```

Example RF noise line:

```text
BkgNoise = 4.1dB, Gain = 49.6dB [28]
```

Interpretation:

```text
Very low or flat BkgNoise + no aircraft
  Possible disconnected antenna, broken coax, bad SMA/adapter, wrong antenna.

Very high or unstable BkgNoise + no/few aircraft
  Possible overload, bad LNA, active antenna power issue, local interference,
  or wrong bias tee setting.

Only very close aircraft appear
  Possible poor antenna placement, damaged antenna, lossy cable, water ingress,
  bad ground plane, or antenna not tuned for 868 MHz.
```

The practical field test is to run `aero-ogn aircraft --watch 5` while a known
nearby aircraft with a working FLARM is transmitting. If the receiver remains
healthy but the aircraft never appears, inspect the RF path before assuming a
software issue.

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
under GPL-3.0-or-later.

Official OGN binaries are separate third-party runtime components and are not
relicensed by this project. See `THIRD_PARTY.md` and `SECURITY.md`.
