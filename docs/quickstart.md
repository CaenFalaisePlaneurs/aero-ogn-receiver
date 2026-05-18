---
layout: page
title: Quick Start
---

# aero-pi-ogn-receiver Quick Start

Minimal commands for checking whether the receiver sees aircraft.

## 1. Open A Terminal On The Pi

Use Raspberry Pi Connect, SSH, or a local keyboard/monitor.

## 2. Activate The Virtual Environment

```bash
source ~/aero-pi-ogn-receiver-venv/bin/activate
```

After activation, the `aero-pi-ogn` command should be available directly.

Example output:

```text
(aero-pi-ogn-receiver-venv) pi@raspberrypi:~ $
```

There is normally no command output; the shell prompt changes to show the venv.

If there is an issue:

```text
bash: /home/pi/aero-pi-ogn-receiver-venv/bin/activate: No such file or directory
```

That means the virtual environment is not present at the expected path. The
software may not be installed, or it may have been installed in a different
venv.

## 3. Check Receiver Health

```bash
aero-pi-ogn status --live
```

Look for `Overall: OK`.

Example output:

```text
OGN receiver live status
Receiver: LFAS
Config:   /etc/aero-pi-ogn-receiver/config.yaml
OGN:      0.3.2 auto -> arm, aprs.glidernet.org:14580

Component           State    Evidence
------------------  -------  --------
config              OK       loaded /etc/aero-pi-ogn-receiver/config.yaml
binary manifest     OK       0.3.2 arm, sha256 0fa9865295a3...
installed binary    OK       /opt/aero-pi-ogn-receiver/ogn/current
rf service          OK       aero-pi-ogn-rf.service active/running, pid 18041
decode service      OK       aero-pi-ogn-decode.service active/running, pid 18042
system time         OK       synchronized
usb receiver        OK       Bus 001 Device 005: ID 0bda:2838 Realtek Semiconductor Corp. RTL2838 DVB-T
rf status page      OK       http://localhost:8080/status.html
decode status page  OK       http://localhost:8081/status.html
cpu temperature     OK       73.1 C
disk space          OK       49.0% free on /

Overall: OK
```

If there is an issue, expect `Overall: WARN` or `Overall: FAIL`, with the
problem shown on the matching component line.

Example service issue:

```text
rf service          WARN     aero-pi-ogn-rf.service inactive/dead
decode service      WARN     aero-pi-ogn-decode.service inactive/dead

Overall: WARN
```

Example missing USB receiver:

```text
usb receiver        FAIL     no RTL-SDR USB device found

Overall: FAIL
```

## 4. Watch Locally Decoded Aircraft

```bash
aero-pi-ogn aircraft --watch 5
```

This is the main field-debugging view. It shows aircraft identity when known,
GPS position, altitude, speed, heading, and signal/frequency quality when the
upstream decoder provides those fields.

Press `Ctrl-C` to stop watching.

Example output when no aircraft are currently decoded:

```text
Local decoded aircraft
Source: http://localhost:8081/aircraft-list-short.txt
Updated: 2026-05-18 12:19:09

No aircraft currently tracked by the local decoder.
```

Example output when aircraft are decoded:

```text
Local decoded aircraft
Source: http://localhost:8081/aircraft-list-short.txt
Updated: 2026-05-18 14:03:25

ID/REG     AGE   LAT        LON        ALT_M  KT  HDG  QUALITY
---------  ----  ---------  ---------  -----  --  ---  -----------------
F-CABC     1.2s  48.92746   -0.14842   457    55  090  12.3/4.5dB +1.2kHz
01:ABCDEF  4.8s  48.91234   -0.10231   612    72  135  10.1/3.8dB -0.4kHz
```

If there is an issue reaching the decoder endpoint:

```text
Aircraft list unavailable: <urlopen error [Errno 111] Connection refused>
```

That usually means `ogn-decode` is not running yet, has crashed, or the decoder
HTTP status page is not reachable. Check `aero-pi-ogn status --live`.

## 5. Inspect The Raw Aircraft Feed

```bash
aero-pi-ogn aircraft --raw
```

Use this if a plane is visible but the table looks incomplete or unexpected.

Example output:

```text
Local decoded aircraft
Source: http://localhost:8081/aircraft-list-short.txt
Updated: 2026-05-18 14:03:25

1.234s 01:ABCDEF [+48.92746, -000.14842]deg 457m, 090deg 055kt #02 12.3/4.5dB +1.2kHz
FLRDDE1A3>OGFLR,qAS,LFAS:/074716h4726.50N/00922.64E'086/015/A=003848 id0ADDE1A3 14.5dB +0.5kHz
```

If no aircraft are currently decoded, the raw view prints the same empty-state
message as the table view:

```text
No aircraft currently tracked by the local decoder.
```

If the endpoint is unreachable, expect an `Aircraft list unavailable: ...`
error. Check receiver health with `aero-pi-ogn status --live`.

## 6. Follow APRS And Traffic Logs

```bash
aero-pi-ogn logs traffic --follow
```

Use this to confirm the receiver is sending APRS packets and to see traffic log
activity. Press `Ctrl-C` to stop.

Example output:

```text
May 18 11:59:07 pi-nico-test procServ[18042]: APRS <- LFAS>OGNSDR:/095907h4855.64NI00008.90W&/A=000515
May 18 11:59:07 pi-nico-test procServ[18042]: APRS <- LFAS>OGNSDR:>095907h v0.3.2.ARM CPU:1.1 RAM:197.7/950.0MB NTP:0.0ms/-2.1ppm +70.9C EGM96:+47m 0/0Acfts[1h] RF:+0+0.0ppm/+3.31dB
2026-05-18 14:03:25 AIRCRAFT 1.234s 01:ABCDEF [+48.92746, -000.14842]deg 457m, 090deg 055kt #02 12.3/4.5dB +1.2kHz
```

If there is no immediate output, that can be normal. This command waits for new
traffic, APRS, or aircraft-list changes. Leave it running for a few minutes, or
open another terminal and run `aero-pi-ogn status --live`.

If journald is unavailable or the service is missing, expect an error from
`journalctl` or no matching unit logs. In that case, check:

```bash
aero-pi-ogn service status
```

## 7. Recognize Antenna Or RF-Path Issues

A faulty antenna, coax, connector, adapter, LNA, or wrong bias tee setting often
does not crash the receiver. The software can look healthy while no useful RF is
received.

Typical pattern:

```text
aero-pi-ogn status --live      -> Overall: OK
aero-pi-ogn aircraft --watch 5 -> No aircraft currently tracked by the local decoder.
aero-pi-ogn logs traffic       -> APRS status keeps showing 0/0Acfts[1h]
```

Example traffic line:

```text
APRS <- LFAS>OGNSDR:>095907h v0.3.2.ARM CPU:1.1 RAM:197.7/950.0MB NTP:0.0ms/-2.1ppm +70.9C EGM96:+47m 0/0Acfts[1h] RF:+0+0.0ppm/+3.31dB
```

Check RF noise:

```bash
aero-pi-ogn logs rf --follow
```

Example RF output:

```text
BkgNoise = 4.1dB, Gain = 49.6dB [28]
```

Suspicious signs:

```text
BkgNoise very low or flat + 0 aircraft       disconnected antenna, bad coax, bad adapter
BkgNoise very high or unstable + few aircraft overload, bad LNA, interference, wrong bias tee
Only close aircraft appear                   poor placement, lossy coax, damaged antenna
```

The best practical check is to watch `aero-pi-ogn aircraft --watch 5` while a known
aircraft with a working FLARM is nearby and transmitting.

## 8. Leave The Virtual Environment

```bash
deactivate
```

Example output:

```text
pi@raspberrypi:~ $
```

There is normally no command output; the shell prompt stops showing the venv.

If there is an issue:

```text
bash: deactivate: command not found
```

That means the shell is probably not inside the venv anymore. It is harmless.

For install, upgrade, uninstall, troubleshooting, and hardware notes, read the
[installation](installation.html), [operation](operation.html), and
[troubleshooting](troubleshooting.html) docs.
