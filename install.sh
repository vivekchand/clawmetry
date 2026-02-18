#!/bin/bash
# Clawmetry — One-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
set -e

echo "🔭 Installing Clawmetry — OpenClaw Observability Dashboard"
echo ""

# Detect OS and install python3-venv if needed
if command -v apt-get &>/dev/null; then
    echo "→ Installing Python venv (apt)..."
    sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv python3-pip >/dev/null 2>&1
elif command -v yum &>/dev/null; then
    echo "→ Installing Python venv (yum)..."
    sudo yum install -y python3 python3-pip >/dev/null 2>&1
elif command -v apk &>/dev/null; then
    echo "→ Installing Python venv (apk)..."
    sudo apk add python3 py3-pip >/dev/null 2>&1
fi

# Create isolated venv (remove old one to ensure clean state)
echo "→ Creating virtual environment at /opt/clawmetry..."
sudo rm -rf /opt/clawmetry
sudo python3 -m venv /opt/clawmetry
sudo /opt/clawmetry/bin/pip install --upgrade pip >/dev/null 2>&1

# Install clawmetry
echo "→ Installing clawmetry from PyPI..."
sudo /opt/clawmetry/bin/pip install --no-cache-dir clawmetry >/dev/null 2>&1

# Create symlink for easy access
sudo ln -sf /opt/clawmetry/bin/clawmetry /usr/local/bin/clawmetry

# Detect OpenClaw workspace
WORKSPACE=""
if [ -d "$HOME/.openclaw" ]; then
    WORKSPACE="$HOME/.openclaw"
elif [ -d "/root/.openclaw" ]; then
    WORKSPACE="/root/.openclaw"
fi

echo ""
echo "✅ Clawmetry installed successfully!"
echo ""
echo "  Version: $(clawmetry --version 2>/dev/null || echo 'installed')"
echo ""
echo "  Start with:"
echo "    clawmetry --host 0.0.0.0 --port 8900"
echo ""
if [ -n "$WORKSPACE" ]; then
    echo "  OpenClaw workspace detected: $WORKSPACE"
    echo ""
fi
echo "  Then open http://YOUR_IP:8900 in your browser"
echo ""
echo "  To run in background:"
echo "    nohup clawmetry --host 0.0.0.0 --port 8900 &"
echo ""
echo "🔭 Happy observing!"
