#!/usr/bin/env bash
# ClawMetry — One-command installer
# Usage: curl -fsSL https://clawmetry.com/install.sh | bash
set -e

CLAWMETRY_APP="https://app.clawmetry.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}  🦞 ClawMetry${NC}"
echo -e "  Real-time observability for OpenClaw AI agents"
echo ""

# ── Check Python ────────────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
  echo -e "${RED}  ✗ Python 3 not found.${NC}"
  if command -v brew &>/dev/null; then
    echo -e "  → Installing Python via Homebrew..."
    brew install python3
  elif command -v apt-get &>/dev/null; then
    echo -e "  → Installing Python (apt)..."
    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip >/dev/null 2>&1
  elif command -v yum &>/dev/null; then
    sudo yum install -y python3 python3-pip >/dev/null 2>&1
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip >/dev/null 2>&1
  elif command -v apk &>/dev/null; then
    sudo apk add python3 py3-pip >/dev/null 2>&1
  elif command -v pacman &>/dev/null; then
    sudo pacman -Sy --noconfirm python python-pip >/dev/null 2>&1
  else
    echo -e "${RED}  ✗ Please install Python 3 from https://python.org${NC}"
    exit 1
  fi
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION found"

# ── Install / upgrade clawmetry ─────────────────────────────────────────────

echo -e "  ${CYAN}→${NC} Installing ClawMetry..."

# Try pip install (fast path)
if python3 -m pip install --upgrade --quiet clawmetry 2>/dev/null; then
  :
else
  # Fallback: user install
  python3 -m pip install --upgrade --quiet --user clawmetry 2>/dev/null || true
fi

# Ensure clawmetry is on PATH
CLAWMETRY_BIN=""
for candidate in \
  "$(python3 -m site --user-base 2>/dev/null)/bin/clawmetry" \
  "$HOME/.local/bin/clawmetry" \
  "/usr/local/bin/clawmetry" \
  "$(python3 -c 'import sys; print(sys.prefix)' 2>/dev/null)/bin/clawmetry"; do
  if [ -x "$candidate" ]; then
    CLAWMETRY_BIN="$candidate"
    break
  fi
done

if [ -z "$CLAWMETRY_BIN" ]; then
  CLAWMETRY_BIN="$(command -v clawmetry 2>/dev/null || true)"
fi

if [ -z "$CLAWMETRY_BIN" ]; then
  echo -e "${RED}  ✗ clawmetry not found on PATH after install.${NC}"
  echo -e "  Try: pip install --user clawmetry"
  exit 1
fi

CLAWMETRY_VERSION=$("$CLAWMETRY_BIN" --version 2>/dev/null | head -1 || echo "installed")
echo -e "  ${GREEN}✓${NC} ClawMetry $CLAWMETRY_VERSION installed"
echo ""

# ── Connect ─────────────────────────────────────────────────────────────────

"$CLAWMETRY_BIN" onboard < /dev/tty

echo ""
echo -e "  ${GREEN}${BOLD}Done!${NC} Open ${CYAN}${CLAWMETRY_APP}${NC} to see your agents."
echo ""
