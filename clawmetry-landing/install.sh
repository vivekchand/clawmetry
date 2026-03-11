#!/bin/bash
# ClawMetry — One-line installer (macOS + Linux)
# Usage: curl -fsSL https://clawmetry.com/install.sh | bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

CLAWMETRY_APP="https://app.clawmetry.com"

echo ""
echo -e "  ${BOLD}🦞 ClawMetry${NC}  ${DIM}AI Observability for OpenClaw${NC}"
echo -e "  $(printf '%.0s─' {1..50})"
echo ""

OS="$(uname -s)"
INSTALL_DIR=""
USE_SUDO=""
BIN_DIR=""

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

echo -e "  → Creating virtual environment..."
$USE_SUDO rm -rf "$INSTALL_DIR"
$USE_SUDO python3 -m venv "$INSTALL_DIR"
$USE_SUDO "$INSTALL_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1

echo -e "  → Installing clawmetry from PyPI..."
$USE_SUDO "$INSTALL_DIR/bin/pip" install --no-cache-dir clawmetry >/dev/null 2>&1

# Create symlink
mkdir -p "$BIN_DIR" 2>/dev/null || $USE_SUDO mkdir -p "$BIN_DIR"
$USE_SUDO ln -sf "$INSTALL_DIR/bin/clawmetry" "$BIN_DIR/clawmetry"

# Get version from venv (avoids system binary version mismatch)
CLAWMETRY_VERSION=$("$INSTALL_DIR/bin/python3" -c "import importlib.metadata; print(importlib.metadata.version('clawmetry'))" 2>/dev/null || echo "installed")

echo ""
echo -e "  ${GREEN}${BOLD}✓ ClawMetry clawmetry $CLAWMETRY_VERSION installed${NC}"
echo ""
echo -e "  $(printf '%.0s─' {1..50})"
echo ""
echo -e "  Run with:"
echo ""
echo -e "    clawmetry --host 0.0.0.0 --port 8900        ${DIM}# foreground (LAN accessible)${NC}"
echo -e "    clawmetry start --host 0.0.0.0 --port 8900  ${DIM}# background service (LAN accessible)${NC}"
echo ""
echo -e "  $(printf '%.0s─' {1..50})"
echo ""
echo -e "  ${BOLD}🦞 ClawMetry Cloud${NC}  ${DIM}— monitor from anywhere${NC}"
echo ""
echo -e "  Sign in and connect this node to your cloud dashboard:"
echo ""
echo -e "    ${BOLD}clawmetry connect${NC}  ${DIM}# sync to clawmetry cloud${NC}"
echo ""
echo -e "  Your data stays encrypted end-to-end."
echo -e "  Free 7-day trial · no credit card required."
echo ""
echo -e "  Docs:  ${CYAN}https://clawmetry.com/how-it-works${NC}"
echo ""
echo -e "  🦞  Happy observing!"
echo ""

# PATH reminder if needed
if [ "$OS" = "Darwin" ] && [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo -e "  ${BOLD}⚠️  Add $BIN_DIR to your PATH:${NC}"
  SHELL_NAME="$(basename "$SHELL")"
  case "$SHELL_NAME" in
    zsh)  echo -e "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc && source ~/.zshrc" ;;
    bash) echo -e "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc" ;;
    *)    echo -e "    export PATH=\"$BIN_DIR:\$PATH\"" ;;
  esac
  echo ""
fi
