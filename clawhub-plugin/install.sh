#!/usr/bin/env bash
# ClawMetry — ClawHub Plugin Installer
# Installs ClawMetry Python package and configures it as an OpenClaw plugin.
#
# Usage:
#   Via ClawHub:  openclaw plugins install clawmetry
#   Manual:       bash install.sh [--port 8900] [--host 127.0.0.1] [--no-service]
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
DIM='\033[2m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

CM_PORT="${CM_PORT:-8900}"
CM_HOST="${CM_HOST:-127.0.0.1}"
CM_NO_SERVICE="${CM_NO_SERVICE:-}"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) CM_PORT="$2"; shift 2 ;;
    --host) CM_HOST="$2"; shift 2 ;;
    --no-service) CM_NO_SERVICE=1; shift ;;
    *) shift ;;
  esac
done

echo ""
echo -e "  ${BOLD}ClawMetry — OpenClaw Observability Plugin${NC}"
echo -e "  ${DIM}$(printf '%.0s-' {1..46})${NC}"
echo ""

# -- Detect OS ----------------------------------------------------------------
OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="macos" ;;
  Linux)  PLATFORM="linux" ;;
  *)
    echo -e "${RED}  Unsupported OS: $OS${NC}"
    exit 1
    ;;
esac

# -- Check Python --------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}  Python 3 is required but not found.${NC}"
  echo -e "    Install: https://python.org/downloads"
  exit 1
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  -> Python $PYTHON_VER detected"

# -- Install via pip -----------------------------------------------------------
echo -e "  -> Installing ClawMetry..."
if python3 -m pip install --quiet --upgrade clawmetry 2>/dev/null; then
  CM_VERSION=$(python3 -m pip show clawmetry 2>/dev/null | grep "^Version:" | awk '{print $2}')
  echo -e "  ${GREEN}OK${NC} ClawMetry ${CM_VERSION} installed"
else
  echo -e "${RED}  pip install failed.${NC}"
  echo -e "    Try manually: pip install clawmetry"
  exit 1
fi

# -- Verify clawmetry binary ---------------------------------------------------
if ! command -v clawmetry &>/dev/null; then
  USER_BIN="$(python3 -m site --user-base)/bin"
  export PATH="$USER_BIN:$PATH"
fi

if ! command -v clawmetry &>/dev/null; then
  CLAWMETRY_CMD="python3 -m clawmetry.cli"
else
  CLAWMETRY_CMD="clawmetry"
fi

echo -e "  -> Command: ${CYAN}${CLAWMETRY_CMD}${NC}"

# -- Configure OpenClaw plugin -------------------------------------------------
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
if command -v openclaw &>/dev/null && [[ -d "$HOME/.openclaw" ]]; then
  echo -e "  -> Configuring OpenClaw plugin entry..."
  if [[ -f "$OPENCLAW_CONFIG" ]]; then
    python3 -c "
import json, sys
try:
    with open('$OPENCLAW_CONFIG', 'r') as f:
        config = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    config = {}

plugins = config.setdefault('plugins', {})
allow = plugins.setdefault('allow', [])
if 'clawmetry' not in allow:
    allow.append('clawmetry')

entries = plugins.setdefault('entries', {})
if 'clawmetry' not in entries:
    entries['clawmetry'] = {
        'enabled': True,
        'port': int('$CM_PORT'),
        'host': '$CM_HOST',
        'autoStart': True
    }

with open('$OPENCLAW_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
print('  ${GREEN}OK${NC} Plugin registered in openclaw.json')
" 2>/dev/null || echo -e "  ${YELLOW}WARN${NC} Could not update openclaw.json — configure manually"
  else
    mkdir -p "$(dirname "$OPENCLAW_CONFIG")"
    cat > "$OPENCLAW_CONFIG" <<CONF
{
  "plugins": {
    "allow": ["clawmetry"],
    "entries": {
      "clawmetry": {
        "enabled": true,
        "port": ${CM_PORT},
        "host": "${CM_HOST}",
        "autoStart": true
      }
    }
  }
}
CONF
    echo -e "  ${GREEN}OK${NC} Created openclaw.json with plugin config"
  fi
else
  echo -e "  ${DIM}  OpenClaw not detected — skipping plugin config (standalone mode)${NC}"
fi

# -- Skip service install if requested -----------------------------------------
if [[ -n "$CM_NO_SERVICE" ]]; then
  echo ""
  echo -e "  ${GREEN}OK${NC} ClawMetry installed (no service, --no-service flag set)"
  echo -e "  Start manually: ${CYAN}${CLAWMETRY_CMD} --host ${CM_HOST} --port ${CM_PORT}${NC}"
  echo ""
  exit 0
fi

# -- Install as service --------------------------------------------------------
if [[ "$PLATFORM" == "macos" ]]; then
  PLIST_LABEL="com.clawmetry.dashboard"
  PLIST_DIR="$HOME/Library/LaunchAgents"
  PLIST_PATH="$PLIST_DIR/${PLIST_LABEL}.plist"
  LOG_PATH="$HOME/.clawmetry/dashboard.log"
  PYTHON_BIN=$(which python3)

  mkdir -p "$PLIST_DIR" "$HOME/.clawmetry"

  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>-m</string>
        <string>clawmetry.cli</string>
        <string>--host</string>
        <string>${CM_HOST}</string>
        <string>--port</string>
        <string>${CM_PORT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>StandardOutPath</key>
    <string>${LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_PATH}</string>
</dict>
</plist>
PLIST

  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  UID_VAL=$(id -u)
  launchctl bootstrap "gui/${UID_VAL}" "$PLIST_PATH" 2>/dev/null \
    || launchctl load -w "$PLIST_PATH" 2>/dev/null \
    || true

  echo -e "  ${GREEN}OK${NC} LaunchAgent registered: ${PLIST_LABEL}"

elif [[ "$PLATFORM" == "linux" ]]; then
  SERVICE_NAME="clawmetry-dashboard"
  SERVICE_DIR="$HOME/.config/systemd/user"
  SERVICE_PATH="${SERVICE_DIR}/${SERVICE_NAME}.service"
  LOG_PATH="$HOME/.clawmetry/dashboard.log"
  PYTHON_BIN=$(which python3)

  mkdir -p "$SERVICE_DIR" "$HOME/.clawmetry"

  cat > "$SERVICE_PATH" <<UNIT
[Unit]
Description=ClawMetry Dashboard — OpenClaw Observability
After=network.target

[Service]
ExecStart=${PYTHON_BIN} -m clawmetry.cli --host ${CM_HOST} --port ${CM_PORT}
Restart=always
RestartSec=30
StandardOutput=append:${LOG_PATH}
StandardError=append:${LOG_PATH}

[Install]
WantedBy=default.target
UNIT

  if command -v systemctl &>/dev/null && systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable --now "$SERVICE_NAME" 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} systemd user service registered: ${SERVICE_NAME}"
  else
    mkdir -p "$(dirname "$LOG_PATH")"
    nohup "${PYTHON_BIN}" -m clawmetry.cli --host "${CM_HOST}" --port "${CM_PORT}" \
      >> "$LOG_PATH" 2>&1 &
    echo -e "  ${GREEN}OK${NC} Dashboard started in background (pid $!)"
    echo -e "    ${DIM}Log: ${LOG_PATH}${NC}"
  fi
fi

echo ""
echo -e "  ${GREEN}${BOLD}ClawMetry installed and running!${NC}"
echo ""
echo -e "  Dashboard:  ${CYAN}http://${CM_HOST}:${CM_PORT}${NC}"
echo -e "  Plugin:     openclaw plugins inspect clawmetry"
echo ""
