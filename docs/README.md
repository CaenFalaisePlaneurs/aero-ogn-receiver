---
layout: page
title: aero-pi-ogn-receiver
---

# aero-pi-ogn-receiver

<img src="https://raw.githubusercontent.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver/main/docs/aero-pi-ogn-receiver_logo.png" alt="aero-pi-ogn-receiver logo" width="300px">

Installable OGN/FLARM receiver manager for Raspberry Pi.

Recommended receiver hardware: Raspberry Pi 3B or newer. Very old single-core
models such as Raspberry Pi 1 and Raspberry Pi Model B+ can install the project,
but they may not keep up with real-time OGN decoding and are not recommended
for production reception.

Project documentation is published at
[caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/).

Install on a target Raspberry Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver/main/scripts/install.sh | sh
```

Start here:

- [Quick start](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/quickstart.html)
- [Installation](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/installation.html)
- [CLI reference](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/cli.html)
- [Advanced usage](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/advanced-usage.html)
- [Maintenance](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/maintenance.html)
- [OGN binaries and third-party runtime components](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/binaries.html)
- [Troubleshooting](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/troubleshooting.html)
- [Security policy](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/security.html)
- [Development](https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/development.html)

`aero-pi-ogn-receiver` installs and manages an Open Glider Network receiver on an
existing Raspberry Pi OS system. It does not build a custom Raspberry Pi image.
