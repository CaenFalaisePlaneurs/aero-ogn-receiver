---
layout: page
title: Quick Start
---

# aero-pi-ogn-receiver Quick Start

Follow these steps one by one on the Raspberry Pi. Copy and paste each command
into your terminal.

## Requirements

- Raspberry Pi OS on a Raspberry Pi
- RTL-SDR USB receiver connected to the Pi
- OGN/FLARM antenna connected to the receiver
- Internet access during installation
- Your receiver location name, latitude, longitude, and altitude

---

## Step 1: Install the basic tools

Install the Raspberry Pi packages needed to create the Python virtual
environment and fetch the project:

```bash
sudo apt update
sudo apt install -y python3-venv git
```

**Verify Step 1 completed successfully:**

```bash
python3 -m venv --help >/dev/null && git --version && echo "[OK] Basic tools are installed!" || echo "[FAIL] Install python3-venv and git again with: sudo apt install -y python3-venv git"
```

**Checkpoint: Step 1 complete. The Pi has the basic install tools.**

---

## Step 2: Create a virtual environment

This creates an isolated space for the receiver manager:

```bash
python3 -m venv ~/aero-pi-ogn-receiver-venv
```

**Verify Step 2 completed successfully:**

```bash
ls -d ~/aero-pi-ogn-receiver-venv && echo "[OK] Virtual environment created successfully!" || echo "[FAIL] Virtual environment creation failed. Try running: python3 -m venv ~/aero-pi-ogn-receiver-venv"
```

**Checkpoint: Step 2 complete. The virtual environment exists.**

---

## Step 3: Install the software

Install the latest project version from GitHub:

```bash
~/aero-pi-ogn-receiver-venv/bin/pip install git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git
```

**Note**: This can take a few minutes. Wait for the command to finish.

**Verify Step 3 completed successfully:**

```bash
~/aero-pi-ogn-receiver-venv/bin/pip show aero-pi-ogn-receiver && echo "[OK] Package installed successfully!" || echo "[FAIL] Package installation failed. Try running: ~/aero-pi-ogn-receiver-venv/bin/pip install git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git"
```

**Checkpoint: Step 3 complete. The receiver manager is installed.**

---

## Step 4: Run the setup

This command will:

- Install required system packages (`rtl-sdr`, `procserv`, certificates, and OGN runtime dependencies)
- Create `/etc/aero-pi-ogn-receiver/config.yaml`
- Download and verify the pinned OGN receiver binaries
- Install the systemd service units
- Write a command sheet into the virtual environment

**Important**: This command needs root privileges to write system files. Use
`sudo` without `-u`:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
```

You will be asked for your password. Type it and press Enter.

**Verify Step 4 completed successfully:**

```bash
test -f /etc/aero-pi-ogn-receiver/config.yaml && test -f /etc/systemd/system/aero-pi-ogn-rf.service && test -f /etc/systemd/system/aero-pi-ogn-decode.service && echo "[OK] Setup completed successfully!" || echo "[FAIL] Setup failed. Try running: sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup"
```

**Checkpoint: Step 4 complete. The system files and services are installed.**

---

## Step 5: Configure the receiver

Edit the configuration file with your station and radio settings:

```bash
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
```

**What to change:**

- `receiver.name`: Your receiver or airfield name, for example `LFAS`
- `receiver.latitude`: Your receiver latitude
- `receiver.longitude`: Your receiver longitude
- `receiver.altitude_m`: Your receiver altitude in meters
- `radio.ppm_correction`: Your SDR frequency correction, or `0` if unknown
- `radio.bias_tee`: Use `true` only for compatible active antennas or LNAs
- `ogn.aprs_server`: Keep `aprs.glidernet.org:14580` unless you know you need another server
- `ogn.binary_arch`: Keep `"auto"` for normal Raspberry Pi installs

Press `Ctrl+X`, then `Y`, then `Enter` to save and exit.

**Verify Step 5 completed successfully:**

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config validate --config /etc/aero-pi-ogn-receiver/config.yaml && echo "[OK] Configuration file is valid!" || echo "[FAIL] Configuration is invalid. Edit it again with: sudo nano /etc/aero-pi-ogn-receiver/config.yaml"
```

**Checkpoint: Step 5 complete. Your receiver configuration is valid.**

---

## Step 6: Render the OGN configuration

The native OGN receiver programs read a generated config file. Render it after
editing the YAML configuration:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
```

**Verify Step 6 completed successfully:**

```bash
sudo test -f /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf && echo "[OK] OGN configuration rendered successfully!" || echo "[FAIL] OGN configuration was not rendered. Try the render command again."
```

**Checkpoint: Step 6 complete. The OGN runtime configuration is ready.**

---

## Step 7: Start the receiver

Enable the receiver services and start them now:

```bash
sudo systemctl enable --now aero-pi-ogn-receiver.target
```

**Verify Step 7 completed successfully:**

```bash
sudo systemctl is-active --quiet aero-pi-ogn-rf.service && sudo systemctl is-active --quiet aero-pi-ogn-decode.service && echo "[OK] Receiver services started successfully!" || echo "[FAIL] Receiver services did not start. Check logs with: sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -n 50"
```

**Checkpoint: Step 7 complete. The receiver services are running.**

---

## Step 8: Check receiver health

Run the live health check:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

You should see `Overall: OK`.

**Verify Step 8 completed successfully:**

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live | grep -q "Overall: OK" && echo "[OK] Receiver health is good!" || echo "[CHECK] Receiver reported WARN or FAIL. Read: https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/troubleshooting.html"
```

**Checkpoint: Step 8 complete. The receiver manager can inspect the system.**

---

## Step 9: Check for aircraft

Watch the locally decoded aircraft table:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn aircraft --watch 5
```

Press `Ctrl+C` to stop watching.

If aircraft are nearby and transmitting, you should see rows with an aircraft
ID, position, altitude, speed, heading, and signal quality.

If the output says `No aircraft currently tracked by the local decoder`, the
software may still be working. Leave it running when a known FLARM-equipped
aircraft is nearby. If the receiver stays healthy but never sees aircraft, read
the [troubleshooting guide](troubleshooting.html).

**Checkpoint: Step 9 complete. You know how to confirm local reception.**

---

## Viewing logs

To see receiver traffic and APRS activity:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn logs traffic --follow
```

Press `Ctrl+C` to stop viewing logs.

---

## Next steps

- [Advanced Usage](advanced-usage.html): Aircraft views, logs, raw decoder data, and RF checks
- [Maintenance](maintenance.html): Service management, upgrades, config changes, and uninstall
- [Troubleshooting](troubleshooting.html): Service, USB, power, antenna, and RF-path problems
- [CLI Reference](cli.html): Full command reference
