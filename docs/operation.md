---
layout: page
title: Operations
---

# Operations

The main field operations path is:

```text
Raspberry Pi Connect -> shell/terminal -> aero-pi-ogn CLI
```

Setup writes a short command sheet into the virtual environment:
`~/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md`. It contains the common
status, service, config, upgrade, and uninstall commands, and points back to the
project documentation for troubleshooting and less common tasks.

## Check Status

```bash
source ~/aero-pi-ogn-receiver-venv/bin/activate
aero-pi-ogn status --live
aero-pi-ogn aircraft --watch 5
aero-pi-ogn aircraft --raw
aero-pi-ogn service status
aero-pi-ogn logs --lines 100
aero-pi-ogn logs traffic --follow
```

## Start, Stop, Restart

```bash
sudo systemctl start aero-pi-ogn-receiver.target
sudo systemctl stop aero-pi-ogn-receiver.target
sudo systemctl restart aero-pi-ogn-receiver.target
sudo systemctl status aero-pi-ogn-rf.service aero-pi-ogn-decode.service --no-pager
```

The installed systemd units run the OGN binaries through localhost-bound
`procServ` instances for compatibility with the upstream runtime. The normal
operator interface remains `aero-pi-ogn status`, `aero-pi-ogn logs`, and `systemctl`;
the procServ control ports are local-only implementation details.

## Edit And Validate Config

```bash
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
aero-pi-ogn config validate --config /etc/aero-pi-ogn-receiver/config.yaml
sudo aero-pi-ogn config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
sudo systemctl restart aero-pi-ogn-receiver.target
```

## Upgrade

```bash
~/aero-pi-ogn-receiver-venv/bin/python -m pip install --upgrade --force-reinstall git+https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git
sudo ~/aero-pi-ogn-receiver-venv/bin/python -m aero_pi_ogn_receiver.setup.setup
sudo systemctl restart aero-pi-ogn-receiver.target
aero-pi-ogn status --live
```

## Uninstall

Preserve `/etc/aero-pi-ogn-receiver/config.yaml` and remove the receiver
integration, binaries, recorded system packages, state, and logs:

```bash
sudo ~/aero-pi-ogn-receiver-venv/bin/aero-pi-ogn-uninstall --complete
rm -rf ~/aero-pi-ogn-receiver-venv
```

To also remove `/etc/aero-pi-ogn-receiver/config.yaml`, add `--purge` to the
uninstall command.
