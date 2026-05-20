---
layout: page
title: Troubleshooting
---

# Troubleshooting

Start with the health check:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

If it reports `Overall: OK`, the services and basic system checks are healthy.
If it reports `WARN` or `FAIL`, use the matching section below.

---

## Service will not start

Check the service state:

```bash
sudo systemctl status aero-pi-ogn-rf.service aero-pi-ogn-decode.service --no-pager
```

Check recent logs:

```bash
sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -n 100 --no-pager
```

Restart the receiver:

```bash
sudo systemctl restart aero-pi-ogn-receiver.target
```

Verify again:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

If the services still fail, validate and render the configuration again:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config validate --config /etc/aero-pi-ogn-receiver/config.yaml
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
sudo systemctl restart aero-pi-ogn-receiver.target
```

---

## RTL-SDR USB receiver is missing

Check USB detection:

```bash
lsusb
```

Check receiver health:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

A missing USB receiver normally appears as:

```text
usb receiver        FAIL     no RTL-SDR USB device found
```

Try these checks:

- Re-seat the RTL-SDR dongle.
- Try another USB port.
- Remove unneeded USB devices.
- Reboot the Pi.
- Test with a powered USB hub if the Pi power supply is marginal.

---

## Power or throttling issues

The RTL-SDR dongle is powered by the Raspberry Pi USB port. A weak power supply
can cause USB resets, RF service restarts, high temperature, or unstable
decoder behavior.

Check the current and historical Pi power state:

```bash
vcgencmd get_throttled
vcgencmd measure_temp
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

Historical bits stay set until reboot. For a clean comparison, record the
value, reboot, run the receiver for a representative period, then check again.

---

## Status is OK but no aircraft appear

Run these checks:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn aircraft --watch 5
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn logs traffic --follow
```

This pattern usually means the software is alive but the receiver is not
decoding useful traffic:

```text
status --live      Overall: OK
aircraft --watch   No aircraft currently tracked by the local decoder.
logs traffic       APRS status repeatedly reports 0/0Acfts[1h]
```

Possible causes:

- No FLARM-equipped aircraft are nearby.
- The antenna is disconnected or not suitable for 868 MHz.
- The coax, adapter, or connector is damaged.
- The antenna location is shielded or too low.
- An active antenna or LNA is not powered correctly.
- `radio.bias_tee` is wrong for the connected hardware.

Confirm with a known nearby aircraft when possible.

---

## Repeated APRS reconnects or decoder restarts

If `aero-pi-ogn logs traffic --follow` repeatedly shows APRS startup and login
messages, the APRS server may not be the real problem:

```text
APRS_Sender.Exec() ... Start
APRS_Sender.Exec() ... Connected to aprs.glidernet.org:14580, login sent
APRS -> # logresp LFAS verified, server GLIDERN2
```

Check the full service logs:

```bash
sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -n 200 --no-pager
```

If the logs also show messages like these, the local OGN runtime is not keeping
up with real-time decoding:

```text
Demodulator is 17sec behind !
RF_Acq.Exec() ... Dropped a slot
Received a sigChild for process ... The process was killed by signal 11
Restarting child "./ogn-decode"
```

On a very old Raspberry Pi, such as a Raspberry Pi 1 or Model B+ with one
700 MHz ARMv6 CPU core, `ogn-rf` and `ogn-decode` can saturate the CPU. The
systemd services may still look active because procServ restarts the crashed
child process, but reception will not be reliable.

Check the Pi model and load:

```bash
cat /proc/device-tree/model
nproc
uptime
vcgencmd get_throttled
```

Expected signs of a CPU-underpowered Pi:

```text
Raspberry Pi Model B Plus Rev 1.2
nproc -> 1
load average much higher than 1.0
Demodulator is ... behind
ogn-decode killed by signal 11
```

Use a newer Raspberry Pi with multiple CPU cores for reliable reception. A
powered USB hub can help with SDR power stability, but it will not fix a CPU
that cannot keep up with OGN decoding. In this case, "underpowered" means the
Pi CPU is too small for the real-time RF/decoder workload, not that the RTL-SDR
dongle necessarily needs more USB power.

---

## Antenna or RF-path problem

Follow the RF logs:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn logs rf --follow
```

Example RF noise line:

```text
BkgNoise = 4.1dB, Gain = 49.6dB [28]
```

Interpretation:

```text
Very low or flat BkgNoise + no aircraft
  Possible disconnected antenna, broken coax, bad adapter, or wrong antenna.

Very high or unstable BkgNoise + no/few aircraft
  Possible overload, bad LNA, active antenna power issue, local interference, or wrong bias tee setting.

Only very close aircraft appear
  Possible poor antenna placement, damaged antenna, lossy cable, water ingress, bad ground plane, or antenna not tuned for 868 MHz.
```

The practical field test is to run `aero-pi-ogn aircraft --watch 5` while a
known nearby aircraft with working FLARM is transmitting.

---

## Configuration errors

Validate the YAML file:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config validate --config /etc/aero-pi-ogn-receiver/config.yaml
```

Edit the file:

```bash
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
```

Render the native OGN config again:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
```

Restart the receiver:

```bash
sudo systemctl restart aero-pi-ogn-receiver.target
```

---

## Package or dependency issues

### Step 4 fails with `Failed to fetch` or `Unable to fetch some archives`

During setup, Step 4 runs APT to install Raspberry Pi OS packages such as
`rtl-sdr`, `ca-certificates`, and `procserv`. Errors like this usually mean the
selected Debian/Raspbian mirror is temporarily unavailable, stale, or
unreachable:

```text
Failed to fetch http://mirror.ircam.fr/...
Unable to fetch some archives
```

Retry the package index update, then rerun Step 4:

```bash
sudo apt clean
sudo apt update
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
```

If the same mirror keeps failing, wait a few minutes and retry. If it still
fails, check which APT sources the Pi is using:

```bash
cat /etc/apt/sources.list
cat /etc/apt/sources.list.d/*.sources
cat /etc/apt/sources.list.d/*.list 2>/dev/null
```

On Raspberry Pi OS, the normal sources should point to Raspberry Pi/Raspbian
package servers such as:

```text
http://raspbian.raspberrypi.com/raspbian/
http://archive.raspberrypi.com/debian/
```

If a third-party mirror is configured directly and keeps failing, switch back to
the normal Raspberry Pi OS package sources or another working local mirror, then
run `sudo apt update` and rerun Step 4.

### Python package reinstall

Reinstall the Python package:

```bash
sudo systemctl stop aero-pi-ogn-receiver.target
~/aero-pi-ogn-receiver-venv/bin/python -m pip install --upgrade --force-reinstall git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
sudo systemctl start aero-pi-ogn-receiver.target
```

Verify health:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

For normal service commands, see [Maintenance](maintenance.html). For deeper
traffic and RF checks, see [Advanced Usage](advanced-usage.html).
