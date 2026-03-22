#!/bin/bash
# ClawMetry — One-line installer (macOS + Linux)
# Usage: curl -fsSL https://clawmetry.com/install.sh | bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'

BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

echo ""
echo -e "  ${BOLD}🦞 ClawMetry${NC}  ${DIM}AI Observability for OpenClaw${NC}"
echo -e "  $(printf '%.0s─' {1..50})"
echo ""

# ── Detect OS ───────────────────────────────────────────────────────────────

OS="$(uname -s)"

case "$OS" in
  Darwin)
    echo -e "  → Detected macOS"
    INSTALL_DIR="$HOME/.clawmetry"
    BIN_DIR="$HOME/.local/bin"
    USE_SUDO=""
    if ! command -v python3 &>/dev/null; then
      if command -v brew &>/dev/null; then
        echo -e "  → Installing Python via Homebrew..."
        brew install python3
      else
        echo -e "${RED}  ✗ Python3 not found. Install: brew install python3${NC}"
        exit 1
      fi
    fi
    ;;
  Linux)
    echo -e "  → Detected Linux"
    INSTALL_DIR="/opt/clawmetry"
    BIN_DIR="/usr/local/bin"
    USE_SUDO="sudo"
    if command -v apt-get &>/dev/null; then
      sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv python3-pip >/dev/null 2>&1
    elif command -v yum &>/dev/null; then
      sudo yum install -y python3 python3-pip >/dev/null 2>&1
    elif command -v dnf &>/dev/null; then
      sudo dnf install -y python3 python3-pip >/dev/null 2>&1
    elif command -v apk &>/dev/null; then
      sudo apk add python3 py3-pip >/dev/null 2>&1
    elif command -v pacman &>/dev/null; then
      sudo pacman -Sy --noconfirm python python-pip >/dev/null 2>&1
    fi
    ;;
  *)
    echo -e "${RED}  ✗ Unsupported OS: $OS (macOS and Linux only)${NC}"
    exit 1
    ;;
esac

# ── Install into venv ────────────────────────────────────────────────────────

echo -e "  → Creating virtual environment..."
# Preserve config before wiping venv (contains node_id, encryption_key)
_CM_CFG_BAK=""
if [ -f "$INSTALL_DIR/config.json" ]; then
  _CM_CFG_BAK=$(mktemp)
  cp "$INSTALL_DIR/config.json" "$_CM_CFG_BAK"
elif [ -f "$HOME/.clawmetry/config.json" ] && [ "$INSTALL_DIR" = "$HOME/.clawmetry" ]; then
  _CM_CFG_BAK=$(mktemp)
  cp "$HOME/.clawmetry/config.json" "$_CM_CFG_BAK"
fi
$USE_SUDO rm -rf "$INSTALL_DIR"
$USE_SUDO python3 -m venv "$INSTALL_DIR"
$USE_SUDO "$INSTALL_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1

# Restore config if it was backed up
if [ -n "$_CM_CFG_BAK" ] && [ -f "$_CM_CFG_BAK" ]; then
  $USE_SUDO cp "$_CM_CFG_BAK" "$INSTALL_DIR/config.json"
  rm -f "$_CM_CFG_BAK"
fi

echo -e "  → Installing clawmetry from PyPI..."
$USE_SUDO "$INSTALL_DIR/bin/pip" install --no-cache-dir clawmetry >/dev/null 2>&1

# Create symlink
mkdir -p "$BIN_DIR" 2>/dev/null || $USE_SUDO mkdir -p "$BIN_DIR"
$USE_SUDO ln -sf "$INSTALL_DIR/bin/clawmetry" "$BIN_DIR/clawmetry"

CLAWMETRY_BIN="$BIN_DIR/clawmetry"
CLAWMETRY_VERSION=$("$INSTALL_DIR/bin/python3" -c "import importlib.metadata; print(importlib.metadata.version('clawmetry'))" 2>/dev/null || echo "installed")

echo ""
echo -e "  ${GREEN}${BOLD}✓ ClawMetry $CLAWMETRY_VERSION installed${NC}"
echo ""
echo -e "  $(printf '%.0s─' {1..50})"
echo ""

# ── Onboarding ───────────────────────────────────────────────────────────────
# Runs: clawmetry onboard

if [ "${CLAWMETRY_SKIP_ONBOARD:-}" = "1" ]; then
  echo -e "  ${DIM}Skipping onboard (CLAWMETRY_SKIP_ONBOARD=1)${NC}"
# shellcheck disable=SC2217
elif [ -r /dev/tty ] 2>/dev/null; then
  "$CLAWMETRY_BIN" onboard < /dev/tty || true
else
  "$CLAWMETRY_BIN" onboard || true
fi

# ── PATH reminder if needed ──────────────────────────────────────────────────

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo ""
  echo -e "  ${BOLD}⚠️  Add $BIN_DIR to your PATH:${NC}"
  SHELL_NAME="$(basename "$SHELL")"
  case "$SHELL_NAME" in
    zsh)  echo -e "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc && source ~/.zshrc" ;;
    bash) echo -e "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc" ;;
    *)    echo -e "    export PATH=\"$BIN_DIR:\$PATH\"" ;;
  esac
  echo ""
fi
