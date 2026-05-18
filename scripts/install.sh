#!/usr/bin/env bash
# Thin convenience installer for aero-ogn-receiver.
# It creates a user-owned virtual environment and installs this project into it.

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/CaenFalaisePlaneurs/aero-ogn-receiver.git}"
VENV_DIR="${AERO_OGN_VENV:-$HOME/aero-ogn-receiver-venv}"
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

cat <<EOF

aero-ogn-receiver is installed in:
  $VENV_DIR

Next steps:
  sudo $VENV_DIR/bin/python -m aero_ogn_receiver.setup.setup
  sudo nano /etc/aero-ogn-receiver/config.yaml
  sudo $VENV_DIR/bin/aero-ogn config validate
  sudo $VENV_DIR/bin/aero-ogn config render --output /etc/aero-ogn-receiver/rtlsdr-ogn.conf

For interactive use:
  $VENV_DIR/bin/aero-ogn status --live
  export PATH="$VENV_DIR/bin:\$PATH"

The setup command is explicit because it writes system files and downloads and
verifies the pinned OGN runtime binaries.
EOF
