#!/bin/sh
# Full Raspberry Pi installer for aero-pi-ogn-receiver.
# Intended for:
#   curl -fsSL https://raw.githubusercontent.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver/main/scripts/install.sh | sh

set -eu

REPO_URL="${AERO_PI_OGN_REPO_URL:-https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git}"
PIP_SPEC="${AERO_PI_OGN_PIP_SPEC:-git+$REPO_URL}"
VENV_DIR="${AERO_PI_OGN_VENV:-$HOME/aero-pi-ogn-receiver-venv}"
CONFIG_PATH="${AERO_PI_OGN_CONFIG:-/etc/aero-pi-ogn-receiver/config.yaml}"
NATIVE_CONFIG_PATH="${AERO_PI_OGN_NATIVE_CONFIG:-/etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf}"
START_SERVICES="${AERO_PI_OGN_START_SERVICES:-1}"
RECONFIGURE="${AERO_PI_OGN_RECONFIGURE:-}"
TTY_PATH="${AERO_PI_OGN_TTY:-/dev/tty}"

TMP_CONFIG=""
PROMPT_RESULT=""
CONFIG_EXISTED_BEFORE=0

cleanup() {
  if [ -n "$TMP_CONFIG" ] && [ -f "$TMP_CONFIG" ]; then
    rm -f "$TMP_CONFIG"
  fi
}

trap cleanup EXIT HUP INT TERM

say() {
  printf '%s\n' "$*"
}

step() {
  printf '\n==> %s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<EOF
aero-pi-ogn-receiver installer

Usage:
  curl -fsSL https://raw.githubusercontent.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver/main/scripts/install.sh | sh

Environment overrides:
  AERO_PI_OGN_VENV=/path/to/venv
  AERO_PI_OGN_PIP_SPEC=git+https://github.com/.../aero-pi-ogn-receiver.git
  AERO_PI_OGN_RECONFIGURE=1
  AERO_PI_OGN_START_SERVICES=0

Optional configuration overrides:
  AERO_PI_OGN_RECEIVER_NAME=LFAS
  AERO_PI_OGN_LATITUDE=48.92746
  AERO_PI_OGN_LONGITUDE=-0.14842
  AERO_PI_OGN_ALTITUDE_M=157
  AERO_PI_OGN_PPM_CORRECTION=0
  AERO_PI_OGN_BIAS_TEE=false
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    fail "unexpected argument: $1"
    ;;
esac

case "$VENV_DIR" in
  /*)
    ;;
  *)
    fail "AERO_PI_OGN_VENV must be an absolute path"
    ;;
esac

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
  say "Warning: running as root; the virtual environment will be owned by root at $VENV_DIR."
else
  command -v sudo >/dev/null 2>&1 || fail "sudo is required for system package, /etc, /opt, and systemd changes"
  SUDO="sudo"
fi

run_root() {
  if [ -n "$SUDO" ]; then
    sudo "$@"
  else
    "$@"
  fi
}

have_tty() {
  [ -r "$TTY_PATH" ] && [ -w "$TTY_PATH" ]
}

read_tty() {
  if ! have_tty; then
    fail "interactive configuration needs a terminal; provide configuration environment variables or unset AERO_PI_OGN_RECONFIGURE"
  fi
  IFS= read -r PROMPT_RESULT < "$TTY_PATH" || fail "could not read from $TTY_PATH"
}

prompt_value() {
  prompt_text="$1"
  default_value="$2"
  required="$3"

  while :; do
    if ! have_tty; then
      if [ -n "$default_value" ] || [ "$required" = "0" ]; then
        PROMPT_RESULT="$default_value"
        return 0
      fi
      fail "interactive configuration needs a terminal; provide configuration environment variables or unset AERO_PI_OGN_RECONFIGURE"
    fi
    if [ -n "$default_value" ]; then
      printf '%s [%s]: ' "$prompt_text" "$default_value" > "$TTY_PATH"
    else
      printf '%s: ' "$prompt_text" > "$TTY_PATH"
    fi
    read_tty
    if [ -z "$PROMPT_RESULT" ]; then
      PROMPT_RESULT="$default_value"
    fi
    if [ -n "$PROMPT_RESULT" ] || [ "$required" = "0" ]; then
      return 0
    fi
    say "A value is required."
  done
}

normalize_bool() {
  case "$1" in
    1|y|Y|yes|YES|Yes|true|TRUE|True|on|ON|On)
      PROMPT_RESULT="true"
      return 0
      ;;
    0|n|N|no|NO|No|false|FALSE|False|off|OFF|Off)
      PROMPT_RESULT="false"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

prompt_bool() {
  prompt_text="$1"
  default_value="$2"
  default_hint="y/N"
  if [ "$default_value" = "true" ]; then
    default_hint="Y/n"
  fi

  while :; do
    if ! have_tty; then
      PROMPT_RESULT="$default_value"
      return 0
    fi
    printf '%s [%s]: ' "$prompt_text" "$default_hint" > "$TTY_PATH"
    read_tty
    if [ -z "$PROMPT_RESULT" ]; then
      PROMPT_RESULT="$default_value"
    fi
    if normalize_bool "$PROMPT_RESULT"; then
      return 0
    fi
    say "Answer yes or no."
  done
}

env_or_prompt() {
  value="$1"
  prompt_text="$2"
  default_value="$3"
  required="$4"

  if [ -n "$value" ]; then
    PROMPT_RESULT="$value"
    return 0
  fi
  prompt_value "$prompt_text" "$default_value" "$required"
}

env_or_prompt_bool() {
  value="$1"
  prompt_text="$2"
  default_value="$3"

  if [ -n "$value" ]; then
    if ! normalize_bool "$value"; then
      fail "$prompt_text must be yes/no, true/false, or 1/0"
    fi
    return 0
  fi
  prompt_bool "$prompt_text" "$default_value"
}

config_env_is_set() {
  [ -n "${AERO_PI_OGN_RECEIVER_NAME:-}" ] ||
    [ -n "${AERO_PI_OGN_LATITUDE:-}" ] ||
    [ -n "${AERO_PI_OGN_LONGITUDE:-}" ] ||
    [ -n "${AERO_PI_OGN_ALTITUDE_M:-}" ] ||
    [ -n "${AERO_PI_OGN_PPM_CORRECTION:-}" ] ||
    [ -n "${AERO_PI_OGN_BIAS_TEE:-}" ] ||
    [ -n "${AERO_PI_OGN_APRS_SERVER:-}" ] ||
    [ -n "${AERO_PI_OGN_BINARY_ARCH:-}" ] ||
    [ -n "${AERO_PI_OGN_VERSION:-}" ] ||
    [ -n "${AERO_PI_OGN_GSM_CALIBRATION:-}" ] ||
    [ -n "${AERO_PI_OGN_GSM_CENTER_FREQ_MHZ:-}" ] ||
    [ -n "${AERO_PI_OGN_GSM_GAIN_DB:-}" ] ||
    [ -n "${AERO_PI_OGN_OGN_GAIN_DB:-}" ]
}

collect_config() {
  env_or_prompt "${AERO_PI_OGN_RECEIVER_NAME:-}" "Receiver name or station code" "LFAS" "1"
  receiver_name="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_LATITUDE:-}" "Receiver latitude" "48.92746" "1"
  latitude="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_LONGITUDE:-}" "Receiver longitude" "-0.14842" "1"
  longitude="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_ALTITUDE_M:-}" "Receiver altitude in meters" "157" "1"
  altitude_m="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_PPM_CORRECTION:-}" "SDR PPM correction" "0" "1"
  ppm_correction="$PROMPT_RESULT"

  env_or_prompt_bool "${AERO_PI_OGN_BIAS_TEE:-}" "Enable bias tee for compatible active antenna/LNA only" "false"
  bias_tee="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_APRS_SERVER:-}" "OGN APRS server" "aprs.glidernet.org:14580" "1"
  aprs_server="$PROMPT_RESULT"

  env_or_prompt "${AERO_PI_OGN_BINARY_ARCH:-}" "OGN binary architecture" "auto" "1"
  binary_arch="$PROMPT_RESULT"

  if [ -n "${AERO_PI_OGN_GSM_CALIBRATION:-}" ]; then
    if ! normalize_bool "$AERO_PI_OGN_GSM_CALIBRATION"; then
      fail "AERO_PI_OGN_GSM_CALIBRATION must be yes/no, true/false, or 1/0"
    fi
    gsm_calibration="$PROMPT_RESULT"
  else
    gsm_calibration="false"
  fi

  gsm_center_freq_mhz="${AERO_PI_OGN_GSM_CENTER_FREQ_MHZ:-950}"
  gsm_gain_db="${AERO_PI_OGN_GSM_GAIN_DB:-25}"
  ogn_gain_db="${AERO_PI_OGN_OGN_GAIN_DB:-50}"
}

write_temp_config() {
  TMP_CONFIG="$(mktemp)"
  export AERO_PI_OGN_RECEIVER_NAME="$receiver_name"
  export AERO_PI_OGN_LATITUDE="$latitude"
  export AERO_PI_OGN_LONGITUDE="$longitude"
  export AERO_PI_OGN_ALTITUDE_M="$altitude_m"
  export AERO_PI_OGN_PPM_CORRECTION="$ppm_correction"
  export AERO_PI_OGN_BIAS_TEE="$bias_tee"
  export AERO_PI_OGN_GSM_CALIBRATION="$gsm_calibration"
  export AERO_PI_OGN_GSM_CENTER_FREQ_MHZ="$gsm_center_freq_mhz"
  export AERO_PI_OGN_GSM_GAIN_DB="$gsm_gain_db"
  export AERO_PI_OGN_OGN_GAIN_DB="$ogn_gain_db"
  export AERO_PI_OGN_APRS_SERVER="$aprs_server"
  export AERO_PI_OGN_BINARY_ARCH="$binary_arch"

  "$VENV_DIR/bin/python" - "$TMP_CONFIG" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from aero_pi_ogn_receiver.core import paths, simple_yaml


def default_ogn_version() -> str:
    try:
        data = simple_yaml.load(paths.example_config_path())
        return str(data["ogn"]["version"])
    except Exception:
        return "0.3.2"


def env(name: str) -> str:
    return os.environ[name]


def quoted(value: str) -> str:
    return json.dumps(value)


config = f"""receiver:
  name: {quoted(env("AERO_PI_OGN_RECEIVER_NAME"))}
  latitude: {env("AERO_PI_OGN_LATITUDE")}
  longitude: {env("AERO_PI_OGN_LONGITUDE")}
  altitude_m: {env("AERO_PI_OGN_ALTITUDE_M")}

radio:
  ppm_correction: {env("AERO_PI_OGN_PPM_CORRECTION")}
  gsm_calibration: {env("AERO_PI_OGN_GSM_CALIBRATION")}
  gsm_center_freq_mhz: {env("AERO_PI_OGN_GSM_CENTER_FREQ_MHZ")}
  gsm_gain_db: {env("AERO_PI_OGN_GSM_GAIN_DB")}
  ogn_gain_db: {env("AERO_PI_OGN_OGN_GAIN_DB")}
  bias_tee: {env("AERO_PI_OGN_BIAS_TEE")}

ogn:
  aprs_server: {quoted(env("AERO_PI_OGN_APRS_SERVER"))}
  version: {quoted(os.environ.get("AERO_PI_OGN_VERSION", default_ogn_version()))}
  binary_arch: {quoted(env("AERO_PI_OGN_BINARY_ARCH"))}

service:
  start_on_boot: true
"""

Path(sys.argv[1]).write_text(config, encoding="utf-8")
PY
}

install_prompted_config() {
  while :; do
    collect_config
    write_temp_config
    if "$VENV_DIR/bin/aero-pi-ogn" config validate --config "$TMP_CONFIG"; then
      break
    fi
    rm -f "$TMP_CONFIG"
    TMP_CONFIG=""
    if config_env_is_set || ! have_tty; then
      fail "configuration values are invalid"
    fi
    say "Please enter the receiver configuration again."
  done

  run_root install -m 0644 "$TMP_CONFIG" "$CONFIG_PATH"
  rm -f "$TMP_CONFIG"
  TMP_CONFIG=""
}

should_write_config() {
  if config_env_is_set; then
    return 0
  fi
  [ "$RECONFIGURE" = "1" ] || [ "$RECONFIGURE" = "true" ] || [ "$RECONFIGURE" = "yes" ]
}

if [ -n "$SUDO" ]; then
  step "Checking sudo access"
  sudo -v
fi

if run_root test -f "$CONFIG_PATH"; then
  CONFIG_EXISTED_BEFORE=1
fi

step "Installing base Debian packages"
command -v apt-get >/dev/null 2>&1 || fail "apt-get not found; this installer targets Raspberry Pi OS/Debian"
run_root apt-get update
run_root apt-get install -y python3-venv git

step "Creating Python virtual environment"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
else
  say "Using existing virtual environment: $VENV_DIR"
fi

step "Installing aero-pi-ogn-receiver"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/python" -m pip install --upgrade --force-reinstall "$PIP_SPEC"

step "Running privileged receiver setup"
run_root "$VENV_DIR/bin/python" -m aero_pi_ogn_receiver.setup.setup --venv-dir "$VENV_DIR"

if should_write_config; then
  step "Configuring receiver"
  install_prompted_config
elif [ "$CONFIG_EXISTED_BEFORE" -eq 0 ]; then
  say "Using default example configuration installed by setup: $CONFIG_PATH"
else
  say "Keeping existing configuration: $CONFIG_PATH"
fi

step "Validating and rendering receiver configuration"
run_root "$VENV_DIR/bin/aero-pi-ogn" config validate --config "$CONFIG_PATH"
run_root "$VENV_DIR/bin/aero-pi-ogn" config render --config "$CONFIG_PATH" --output "$NATIVE_CONFIG_PATH"

case "$START_SERVICES" in
  0|false|FALSE|False|no|NO|No)
    say "Skipping service start because AERO_PI_OGN_START_SERVICES=$START_SERVICES."
    ;;
  *)
    step "Enabling and starting receiver services"
    if ! run_root systemctl enable --now aero-pi-ogn-receiver.target; then
      fail "services did not start; inspect logs with: sudo journalctl -u aero-pi-ogn-rf.service -u aero-pi-ogn-decode.service -n 50"
    fi
    ;;
esac

step "Checking receiver status"
if ! "$VENV_DIR/bin/aero-pi-ogn" status --live; then
  say "[CHECK] Receiver status reported a problem. See:"
  say "        https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/troubleshooting.html"
fi

cat <<EOF

aero-pi-ogn-receiver installation finished.

Virtual environment:
  $VENV_DIR

Configuration:
  $CONFIG_PATH

Command sheet:
  $VENV_DIR/README-aero-pi-ogn-receiver.md

Useful commands:
  $VENV_DIR/bin/aero-pi-ogn status --live
  $VENV_DIR/bin/aero-pi-ogn aircraft --watch 5
  $VENV_DIR/bin/aero-pi-ogn logs traffic --follow
EOF
