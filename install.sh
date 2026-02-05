#!/bin/bash
# OpenClaw Dashboard — One-line installer
# Usage: curl -sSL https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/install.sh | bash

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}   ___                    ____ _                ${NC}"
echo -e "${CYAN}  / _ \ _ __   ___ _ __  / ___| | __ ___      __${NC}"
echo -e "${CYAN} | | | | '_ \ / _ \ '_ \| |   | |/ _\` \ \ /\ / /${NC}"
echo -e "${CYAN} | |_| | |_) |  __/ | | | |___| | (_| |\ V  V / ${NC}"
echo -e "${CYAN}  \___/| .__/ \___|_| |_|\____|_|\__,_| \_/\_/  ${NC}"
echo -e "${CYAN}       |_|          ${YELLOW}Dashboard v0.2.4${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python 3 is required but not found.${NC}"
    echo "   Install it: sudo apt install python3 python3-pip"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Install via pip
echo -e "\n${BOLD}Installing openclaw-dashboard...${NC}"
pip3 install --user openclaw-dashboard 2>/dev/null || pip3 install openclaw-dashboard

# Verify
if command -v openclaw-dashboard &> /dev/null; then
    echo -e "\n${GREEN}✅ Installed successfully!${NC}"
    echo ""
    echo -e "  Run it:  ${BOLD}openclaw-dashboard${NC}"
    echo -e "  Options: ${BOLD}openclaw-dashboard --help${NC}"
    echo ""
else
    echo -e "\n${YELLOW}⚠️  Installed, but 'openclaw-dashboard' not in PATH.${NC}"
    echo -e "  Try:  ${BOLD}python3 -m dashboard${NC}"
    echo -e "  Or add ~/.local/bin to your PATH"
fi

echo -e "${CYAN}🦞 See your agent think → http://localhost:8900${NC}"
echo ""
