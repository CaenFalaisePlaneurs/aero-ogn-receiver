---
layout: page
title: Advanced Usage
---

# Advanced Usage

Use this page after the receiver is installed and the
[quick start](quickstart.html) has completed.

## Activate the command environment

You can either run the full path:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

Or activate the virtual environment for shorter commands:

```bash
source ~/aero-pi-ogn-receiver-venv/bin/activate
```

After activation, `aero-pi-ogn` should be available directly:

```bash
aero-pi-ogn status --live
```

Leave the virtual environment with:

```bash
deactivate
```

## Aircraft views

The table view is the normal field check:

```bash
aero-pi-ogn aircraft
aero-pi-ogn aircraft --watch 5
```

Use the raw view when the table looks incomplete or when you want to compare
directly with the upstream decoder output:

```bash
aero-pi-ogn aircraft --raw
aero-pi-ogn aircraft --long --raw
```

The local decoder provides the aircraft identity. Registration is shown when the
decoder/device database knows it. Otherwise the FLARM/OGN device ID is shown.

## Health checks

Run a one-shot status check:

```bash
aero-pi-ogn status --live
```

Watch the status every five seconds:

```bash
aero-pi-ogn status --watch 5
```

Use the healthcheck command in scripts or monitoring probes:

```bash
aero-pi-ogn healthcheck
```

On non-Raspberry Pi development machines, hardware and systemd checks report
`UNKNOWN` instead of crashing.

## Log views

Follow the focused traffic view:

```bash
aero-pi-ogn logs traffic --follow
```

Show APRS lines only:

```bash
aero-pi-ogn logs aprs --follow
```

Include APRS heartbeat lines when you need to confirm that the receiver is still
announcing itself upstream:

```bash
aero-pi-ogn logs traffic --follow --include-aprs-heartbeat
```

Follow the RF service logs when checking noise, gain, SDR, or antenna behavior:

```bash
aero-pi-ogn logs rf --follow
```

Show recent logs without following:

```bash
aero-pi-ogn logs --lines 100
```

## RF path checks

A healthy service does not guarantee a healthy antenna path. When the receiver
is running but no aircraft appear, compare three signals:

```bash
aero-pi-ogn status --live
aero-pi-ogn aircraft --watch 5
aero-pi-ogn logs rf --follow
```

Typical RF noise line:

```text
BkgNoise = 4.1dB, Gain = 49.6dB [28]
```

Common patterns:

```text
Very low or flat BkgNoise + no aircraft
  Possible disconnected antenna, broken coax, bad adapter, or wrong antenna.

Very high or unstable BkgNoise + few aircraft
  Possible overload, bad LNA, active antenna power issue, interference, or wrong bias tee setting.

Only very close aircraft appear
  Possible poor placement, lossy coax, damaged antenna, water ingress, or antenna not tuned for 868 MHz.
```

The best field test is to watch `aero-pi-ogn aircraft --watch 5` while a known
nearby aircraft with working FLARM is transmitting.

## OGN binaries

The installer downloads official OGN receiver binaries only during explicit
install or update operations, verifies them against the committed manifest, and
installs them under `/opt/aero-pi-ogn-receiver/ogn`.

List the configured binary manifest:

```bash
aero-pi-ogn binaries list
```

For normal Raspberry Pi installs, keep:

```yaml
ogn:
  binary_arch: "auto"
```

Read [OGN Binaries](binaries.html) before manually changing the binary
architecture.

## Generated command sheet

Setup writes a local command sheet into the virtual environment:

```bash
less ~/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md
```

It contains the common status, service, config, upgrade, and uninstall commands
for the current virtual environment path.
