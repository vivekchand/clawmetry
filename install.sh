#!/usr/bin/env bash
set -e

CLAWMETRY_INGEST="https://ingest.clawmetry.com"
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
echo -e "  Real-time observability for OpenClaw agents"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}  ✗ Python 3 not found. Install it from https://python.org${NC}"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check pip
if ! python3 -m pip --version &>/dev/null; then
  echo -e "${RED}  ✗ pip not found. Run: python3 -m ensurepip${NC}"
  exit 1
fi

# Install / upgrade clawmetry
echo -e "  ${CYAN}→${NC} Installing ClawMetry..."
python3 -m pip install --upgrade clawmetry --quiet

CLAWMETRY_VERSION=$(python3 -c "import clawmetry; print(getattr(clawmetry, '__version__', '?'))" 2>/dev/null || clawmetry --version 2>/dev/null | head -1 || echo "?")
echo -e "  ${GREEN}✓${NC} ClawMetry installed"
echo ""

# Run onboarding wizard
clawmetry onboard

echo ""
echo -e "  ${GREEN}${BOLD}Done!${NC} Open ${CYAN}${CLAWMETRY_APP}${NC} to see your agents."
echo ""
