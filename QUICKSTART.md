# aero-ogn-receiver Quick Start

Minimal commands for checking whether the receiver sees aircraft.

## 1. Open A Terminal On The Pi

Use Raspberry Pi Connect, SSH, or a local keyboard/monitor.

## 2. Activate The Virtual Environment

```bash
source ~/aero-ogn-receiver-venv/bin/activate
```

After activation, the `aero-ogn` command should be available directly.

## 3. Check Receiver Health

```bash
aero-ogn status --live
```

Look for `Overall: OK`.

## 4. Watch Locally Decoded Aircraft

```bash
aero-ogn aircraft --watch 5
```

This is the main field-debugging view. It shows aircraft identity when known,
GPS position, altitude, speed, heading, and signal/frequency quality when the
upstream decoder provides those fields.

Press `Ctrl-C` to stop watching.

## 5. Inspect The Raw Aircraft Feed

```bash
aero-ogn aircraft --raw
```

Use this if a plane is visible but the table looks incomplete or unexpected.

## 6. Follow APRS And Traffic Logs

```bash
aero-ogn logs traffic --follow
```

Use this to confirm the receiver is sending APRS packets and to see traffic log
activity. Press `Ctrl-C` to stop.

## 7. Leave The Virtual Environment

```bash
deactivate
```

For install, upgrade, uninstall, troubleshooting, and hardware notes, read
`README.md`.
