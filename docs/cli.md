---
layout: page
title: CLI Reference
---

# CLI Reference

The `aero-pi-ogn` command is created by package installation. If the package is
installed in the recommended virtual environment, either call it with the full
venv path or add the venv `bin` directory to `PATH`:

```bash
/home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
export PATH="$HOME/aero-pi-ogn-receiver-venv/bin:$PATH"
aero-pi-ogn status --live
```

From an unpacked source checkout that has not been installed, use the module
form instead:

```bash
python3 -m aero_pi_ogn_receiver status --live
python3 -m aero_pi_ogn_receiver config validate
```

Implemented first-pass commands, shown here using the installed entry point:

```bash
aero-pi-ogn config validate
aero-pi-ogn config render
aero-pi-ogn binaries list
aero-pi-ogn status
aero-pi-ogn status --live
aero-pi-ogn status --watch 5
aero-pi-ogn aircraft
aero-pi-ogn aircraft --watch 5
aero-pi-ogn logs
aero-pi-ogn logs --follow
aero-pi-ogn logs traffic --follow
aero-pi-ogn service status
aero-pi-ogn healthcheck
```

## Aircraft

`aero-pi-ogn aircraft` is the local aircraft tracking view. It reads the upstream
decoder's `http://localhost:8081/aircraft-list-short.txt` endpoint and displays
the identity available from the decoder, GPS position, altitude, speed, heading,
and signal/frequency quality fields when those fields are present. Registration
or immatriculation is only shown when the upstream decoder/device database
provides it; otherwise the FLARM/OGN device ID is shown.

Aircraft command reference:

```bash
aero-pi-ogn aircraft              # one-shot local aircraft table
aero-pi-ogn aircraft --watch 5    # refresh the table every 5 seconds
aero-pi-ogn aircraft --raw        # print raw decoder aircraft-list rows
aero-pi-ogn aircraft --long       # use aircraft-list.txt instead of short
```

## Logs

`aero-pi-ogn logs traffic --follow` is the focused live view for APRS and decoded
aircraft activity. It filters the decoder journal down to useful APRS send/login
lines and polls the upstream decoder aircraft list endpoint when aircraft are
currently decoded.

Traffic log command reference:

```bash
aero-pi-ogn logs traffic --follow
aero-pi-ogn logs aprs --follow
aero-pi-ogn logs traffic --follow --include-aprs-heartbeat
aero-pi-ogn logs traffic --follow --no-aircraft
```

On non-Raspberry Pi development machines, hardware and systemd checks report
`UNKNOWN` instead of crashing.
