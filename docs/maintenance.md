---
layout: page
title: Maintenance
---

# Maintenance

Use these commands after the receiver is installed with the
[quick start](quickstart.html).

## Service management

Start the receiver:

```bash
sudo systemctl start aero-pi-ogn-receiver.target
```

Stop the receiver:

```bash
sudo systemctl stop aero-pi-ogn-receiver.target
```

Restart the receiver:

```bash
sudo systemctl restart aero-pi-ogn-receiver.target
```

Check service status:

```bash
sudo systemctl status aero-pi-ogn-rf.service aero-pi-ogn-decode.service --no-pager
```

Disable auto-start:

```bash
sudo systemctl disable aero-pi-ogn-receiver.target
```

Enable auto-start:

```bash
sudo systemctl enable aero-pi-ogn-receiver.target
```

## Viewing logs

Follow focused traffic logs:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn logs traffic --follow
```

Show recent service logs:

```bash
sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -n 100 --no-pager
```

Follow raw systemd service logs:

```bash
sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -f
```

Press `Ctrl+C` to stop following logs.

## Edit and apply configuration changes

Edit the YAML configuration:

```bash
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
```

Validate the YAML configuration:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config validate --config /etc/aero-pi-ogn-receiver/config.yaml
```

Render the native OGN configuration:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
```

Restart the receiver so the change is used:

```bash
sudo systemctl restart aero-pi-ogn-receiver.target
```

Verify health:

```bash
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

## Upgrade

Stop the receiver:

```bash
sudo systemctl stop aero-pi-ogn-receiver.target
```

Install the latest project version:

```bash
~/aero-pi-ogn-receiver-venv/bin/python -m pip install --upgrade --force-reinstall git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git
```

Run setup again. This updates project-managed systemd units, binaries, generated
files, and the virtual environment command sheet:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
```

Start the receiver and verify it:

```bash
sudo systemctl start aero-pi-ogn-receiver.target
~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn status --live
```

## Uninstallation

Remove the receiver integration while preserving
`/etc/aero-pi-ogn-receiver/config.yaml`:

```bash
sudo /home/$(whoami)/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn-uninstall --complete
```

Remove the Python package:

```bash
~/aero-pi-ogn-receiver-venv/bin/pip uninstall aero-pi-ogn-receiver
```

Optionally remove the virtual environment:

```bash
rm -rf ~/aero-pi-ogn-receiver-venv
```

Add `--purge` to the uninstall command only when you also want to remove
`/etc/aero-pi-ogn-receiver/config.yaml`.

If `git` was installed only to fetch this project and is no longer needed on the
Pi, remove it separately:

```bash
sudo apt purge -y git git-man liberror-perl
sudo apt autoremove -y
```

## Local command sheet

Setup writes a command sheet into the virtual environment:

```bash
less ~/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md
```

Use it when you need copy-paste commands that match the installed virtual
environment path.
