#!/usr/bin/env bash
# Thin convenience installer for aero-pi-ogn-receiver.
# It creates a user-owned virtual environment and installs this project into it.

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git}"
VENV_DIR="${AERO_PI_OGN_VENV:-$HOME/aero-pi-ogn-receiver-venv}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. On Raspberry Pi OS, run: sudo apt install -y python3-venv"
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
  "$VENV_DIR/bin/pip" install "$PROJECT_ROOT"
else
  "$VENV_DIR/bin/pip" install "git+$REPO_URL"
fi

"$VENV_DIR/bin/python" -m aero_pi_ogn_receiver.setup.venv_readme "$VENV_DIR" >/dev/null

cat <<EOF

aero-pi-ogn-receiver is installed in:
  $VENV_DIR

Command sheet:
  $VENV_DIR/README-aero-pi-ogn-receiver.md

Next steps:
  sudo $VENV_DIR/bin/python -m aero_pi_ogn_receiver.setup.setup
  sudo nano /etc/aero-pi-ogn-receiver/config.yaml
  sudo $VENV_DIR/bin/aero-pi-ogn config validate
  sudo $VENV_DIR/bin/aero-pi-ogn config render --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf

For interactive use:
  $VENV_DIR/bin/aero-pi-ogn status --live
  export PATH="$VENV_DIR/bin:\$PATH"

To uninstall the system integration while preserving /etc/aero-pi-ogn-receiver/config.yaml:
  sudo $VENV_DIR/bin/aero-pi-ogn-uninstall --complete
  rm -rf "$VENV_DIR"

The setup command is explicit because it writes system files and downloads and
verifies the pinned OGN runtime binaries.
EOF
