---
layout: page
title: Troubleshooting
---

# Troubleshooting

## RTL-SDR USB Power

The RTL-SDR dongle is normally powered by the Raspberry Pi USB port. If the Pi
power supply is marginal, or the dongle draws current in bursts, the receiver
can become unstable even when the software is otherwise healthy. Symptoms can
include USB disconnects, `rtl_test` failures, OGN RF restarts, high temperature,
or Raspberry Pi undervoltage/throttle flags.

Check the current and historical Pi power state:

```bash
vcgencmd get_throttled
vcgencmd measure_temp
python3 -m aero_pi_ogn_receiver status --live
journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service --since "1 hour ago" --no-pager
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

## Antenna Or RF Path

A bad antenna, feedline, adapter, active antenna/LNA, or bias tee configuration
often does not look like a software failure. The services can be active, the
USB SDR can be detected, and the receiver status can still show `Overall: OK`.
The symptom is that the receiver does not see useful aircraft traffic.

Typical commands:

```bash
aero-pi-ogn status --live
aero-pi-ogn aircraft --watch 5
aero-pi-ogn logs traffic --follow
aero-pi-ogn logs rf --follow
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

The practical field test is to run `aero-pi-ogn aircraft --watch 5` while a known
nearby aircraft with a working FLARM is transmitting. If the receiver remains
healthy but the aircraft never appears, inspect the RF path before assuming a
software issue.
