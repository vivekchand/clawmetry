#!/usr/bin/env bash
# ClawMetry — ClawHub Plugin Uninstaller
# Stops the dashboard service and removes ClawMetry.
#
# Usage (called by ClawHub):
#   bash uninstall.sh [--keep-config] [--keep-package]
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
DIM='\033[2m'
RED='\033[0;31m'
NC='\033[0m'

KEEP_CONFIG=""
KEEP_PACKAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-config)  KEEP_CONFIG=1; shift ;;
    --keep-package) KEEP_PACKAGE=1; shift ;;
    *) shift ;;
  esac
done

echo ""
echo -e "  ${BOLD}🦞 ClawMetry — Uninstalling${NC}"
echo -e "  ${DIM}$(printf '%.0s─' {1..46})${NC}"
echo ""

OS="$(uname -s)"

# ── Stop and remove service ────────────────────────────────────────────────────
if [[ "$OS" == "Darwin" ]]; then
  PLIST_LABEL="com.clawmetry.dashboard"
  PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

  if [[ -f "$PLIST_PATH" ]]; then
    UID_VAL=$(id -u)
    launchctl bootout "gui/${UID_VAL}" "$PLIST_PATH" 2>/dev/null \
      || launchctl unload "$PLIST_PATH" 2>/dev/null \
      || true
    rm -f "$PLIST_PATH"
    echo -e "  ${GREEN}✓${NC} Stopped and removed LaunchAgent"
  else
    echo -e "  ${DIM}→ LaunchAgent not found (already removed?)${NC}"
  fi

elif [[ "$OS" == "Linux" ]]; then
  SERVICE_NAME="clawmetry-dashboard"
  SERVICE_PATH="$HOME/.config/systemd/user/${SERVICE_NAME}.service"

  if command -v systemctl &>/dev/null; then
    systemctl --user disable --now "$SERVICE_NAME" 2>/dev/null || true
  fi

  if [[ -f "$SERVICE_PATH" ]]; then
    rm -f "$SERVICE_PATH"
    systemctl --user daemon-reload 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Stopped and removed systemd user service"
  fi

  # Also kill any background process
  pkill -f "clawmetry.cli" 2>/dev/null || true
  pkill -f "clawmetry --host" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Stopped any background ClawMetry processes"
fi

# ── Remove config (unless --keep-config) ──────────────────────────────────────
if [[ -z "$KEEP_CONFIG" ]]; then
  if [[ -d "$HOME/.clawmetry" ]]; then
    rm -rf "$HOME/.clawmetry"
    echo -e "  ${GREEN}✓${NC} Removed ~/.clawmetry config directory"
  fi
else
  echo -e "  ${DIM}→ Config preserved (--keep-config)${NC}"
fi

# ── Uninstall pip package (unless --keep-package) ─────────────────────────────
if [[ -z "$KEEP_PACKAGE" ]]; then
  if command -v python3 &>/dev/null; then
    if python3 -m pip uninstall -y clawmetry 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} Uninstalled clawmetry pip package"
    else
      echo -e "  ${DIM}→ clawmetry pip package not found${NC}"
    fi
  fi
else
  echo -e "  ${DIM}→ Package preserved (--keep-package)${NC}"
fi

echo ""
echo -e "  ${GREEN}${BOLD}✓ ClawMetry uninstalled.${NC}"
echo ""
echo -e "  ${DIM}To reinstall: openclaw plugins install clawmetry${NC}"
echo -e "  ${DIM}Or: curl -fsSL https://clawmetry.com/install.sh | bash${NC}"
echo ""
