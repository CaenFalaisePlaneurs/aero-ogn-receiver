---
layout: page
title: Operations
---

# Operations

Day-to-day receiver operation is now split into focused pages:

- [Maintenance](maintenance.html): Service start/stop/restart, config changes, upgrades, logs, and uninstall
- [Advanced Usage](advanced-usage.html): Aircraft views, raw decoder data, APRS logs, RF checks, and binary notes
- [Troubleshooting](troubleshooting.html): Service, USB, power, antenna, and RF-path diagnosis

The main field operations path remains:

```text
Raspberry Pi Connect -> shell/terminal -> aero-pi-ogn CLI
```

Setup also writes a local command sheet into the virtual environment:

```bash
less ~/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md
```
