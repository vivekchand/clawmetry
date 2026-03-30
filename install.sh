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
$USE_SUDO "$INSTALL_DIR/bin/pip" install --no-cache-dir --upgrade clawmetry >/dev/null 2>&1

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

# ── NemoClaw detection ───────────────────────────────────────────────────────

NEMOCLAW_DETECTED=0
# Ensure common install paths are checked (non-interactive shells may have minimal PATH)
for _p in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do
  [[ ":$PATH:" != *":$_p:"* ]] && [ -d "$_p" ] && export PATH="$_p:$PATH"
done
if command -v nemoclaw &>/dev/null; then
  NEMOCLAW_DETECTED=1
  echo -e "  ${BOLD}🟢 NemoClaw detected${NC}"
  echo ""

  # Step 1: Find and auto-apply the bundled preset script
  PRESET_SCRIPT=$("$INSTALL_DIR/bin/python3" -c "
import importlib.resources
try:
    pkg = importlib.resources.files('clawmetry') / 'resources' / 'add-nemoclaw-clawmetry-preset.sh'
    print(str(pkg))
except Exception:
    pass
" 2>/dev/null || true)

  if [ -n "$PRESET_SCRIPT" ] && [ -f "$PRESET_SCRIPT" ]; then
    echo -e "  → Applying ClawMetry preset to NemoClaw sandboxes..."
    bash "$PRESET_SCRIPT" \
      && echo -e "  ${GREEN}${BOLD}✓ NemoClaw preset applied${NC}" \
      || echo -e "  ${DIM}⚠  Preset incomplete. Run manually: bash $PRESET_SCRIPT${NC}"
    echo ""
  fi

  # Step 2: Auto-install ClawMetry inside sandbox + interactive connect
  SANDBOX_NAMES=$(nemoclaw list 2>/dev/null | awk '
    /^  Sandboxes:/ { in_list=1; next }
    /^  \* = default sandbox/ { in_list=0; next }
    in_list && /^    [^ ]/ { name=$1; gsub(/\*/, "", name); if (name != "") print name }
  ' | head -5)

  if [ -n "$SANDBOX_NAMES" ]; then
    # Find the OpenShell cluster container for kubectl access
    CLUSTER_CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep 'openshell-cluster' | head -1)

    if [ -n "$CLUSTER_CONTAINER" ]; then
      # Step 2a: Install ClawMetry inside all sandboxes via kubectl exec
      echo "$SANDBOX_NAMES" | while IFS= read -r sb; do
        [ -z "$sb" ] && continue
        echo -e "  → Installing ClawMetry inside sandbox ${BOLD}${sb}${NC}..."

        # Always upgrade to latest
        echo -e "  ${DIM}→ Upgrading to latest...${NC}"
        if docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
          pip install --break-system-packages --quiet --upgrade clawmetry 2>/dev/null; then
          NEW_VER=$(docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
            clawmetry --version 2>/dev/null | grep -o '[0-9]*\.[0-9]*\.[0-9]*' || true)
          echo -e "  ${GREEN}${BOLD}✓ ClawMetry ${NEW_VER} installed${NC}"
        else
          echo -e "  ${DIM}⚠  Auto-install failed. Install manually:${NC}"
          echo -e "    ${GREEN}nemoclaw $sb connect${NC}"
          echo -e "    ${GREEN}pip install --break-system-packages --upgrade clawmetry${NC}"
        fi
      done

      echo ""

      # Step 2b: OTP on HOST (--key-only: saves key+enc_key, no daemon — host has no OpenClaw)
      HOST_CONFIG="$HOME/.clawmetry/config.json"
      HOST_API_KEY=""
      HOST_ENC_KEY=""

      _read_host_config() {
        if [ -f "$HOST_CONFIG" ]; then
          HOST_API_KEY=$(/usr/bin/python3 -c "import json; print(json.load(open('$HOST_CONFIG')).get('api_key',''))" 2>/dev/null \
            || python3 -c "import json; print(json.load(open('$HOST_CONFIG')).get('api_key',''))" 2>/dev/null || true)
          HOST_ENC_KEY=$(/usr/bin/python3 -c "import json; print(json.load(open('$HOST_CONFIG')).get('encryption_key',''))" 2>/dev/null \
            || python3 -c "import json; print(json.load(open('$HOST_CONFIG')).get('encryption_key',''))" 2>/dev/null || true)
        fi
      }

      _read_host_config

      if [ -z "$HOST_API_KEY" ]; then
        echo -e "  ${BOLD}Authenticate with ClawMetry Cloud${NC}"
        echo -e "  ${DIM}Enter your email to get a one-time code.${NC}"
        echo ""

        if (exec </dev/tty) 2>/dev/null; then
          # --key-only: OTP flow without starting daemon on host (no OpenClaw on host)
          "$CLAWMETRY_BIN" connect --key-only </dev/tty || true
          _read_host_config
        else
          echo -e "  ${DIM}Run to authenticate:${NC}"
          echo -e "    ${GREEN}clawmetry connect --key-only${NC}"
        fi
      fi

      # Step 2c: Connect each sandbox using the key (non-interactive, starts daemon inside sandbox)
      if [ -n "$HOST_API_KEY" ] && [ -n "$HOST_ENC_KEY" ]; then
        echo ""
        echo "$SANDBOX_NAMES" | while IFS= read -r sb; do
          [ -z "$sb" ] && continue
          echo -e "  → Connecting sandbox ${BOLD}${sb}${NC} to ClawMetry Cloud..."

          # Check if already connected with the CURRENT API key
          SB_KEY=$(docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
            bash -c 'test -f /root/.clawmetry/config.json && python3 -c "import json; print(json.load(open(\"/root/.clawmetry/config.json\")).get(\"api_key\",\"\"))" 2>/dev/null || echo ""' 2>/dev/null || true)

          if [ -n "$SB_KEY" ] && [ "$SB_KEY" = "$HOST_API_KEY" ]; then
            echo -e "  ${GREEN}${BOLD}✓ Sandbox $sb already connected${NC}"
          else
            # Clear stale config if key doesn't match
            if [ -n "$SB_KEY" ] && [ "$SB_KEY" != "$HOST_API_KEY" ]; then
              docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
                rm -f /root/.clawmetry/config.json 2>/dev/null || true
              echo -e "  ${DIM}↺ Cleared stale config (different account)${NC}"
            fi
            # Pre-write config so --key matches _saved_api_key (skips OTP verification)
            CONNECT_TS=$(date -u +%Y-%m-%dT%H:%M:%S 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)
            docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
              bash -c "mkdir -p /root/.clawmetry && python3 -c \"
import json; json.dump({'api_key':'$HOST_API_KEY','node_id':'$sb','platform':'Linux','connected_at':'$CONNECT_TS','encryption_key':'$HOST_ENC_KEY'},open('/root/.clawmetry/config.json','w'))
\"" 2>/dev/null || true

            # Connect non-interactively (OTP skipped — key matches saved config)
            if docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
              clawmetry connect --key "$HOST_API_KEY" --enc-key "$HOST_ENC_KEY" --node-id "$sb" 2>/dev/null; then
              echo -e "  ${GREEN}${BOLD}✓ Sandbox $sb connected (node: $sb)${NC}"
              # Ensure daemon survives kubectl exec session end via supervisord if available
              docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
                bash -c 'command -v supervisorctl >/dev/null 2>&1 && supervisorctl start clawmetry-sync 2>/dev/null || true' 2>/dev/null || true
            else
              echo -e "  ${DIM}⚠  Could not connect sandbox $sb automatically.${NC}"
              echo -e "  ${DIM}Connect manually: nemoclaw $sb connect → clawmetry connect${NC}"
            fi
          fi
        done
      fi

      echo ""
      echo -e "  ${GREEN}${BOLD}✓ All done! Open app.clawmetry.com to see your sandboxes${NC}"
    else
      # No cluster container found, fall back to manual instructions
      FIRST_SANDBOX=$(echo "$SANDBOX_NAMES" | head -1)
      echo -e "  ${BOLD}Next: install ClawMetry inside sandbox ${FIRST_SANDBOX}${NC}"
      echo ""
      echo -e "  ${DIM}Connect to the sandbox and run:${NC}"
      echo ""
      echo -e "    ${GREEN}nemoclaw $FIRST_SANDBOX connect${NC}"
      echo -e "    ${GREEN}pip install --break-system-packages clawmetry${NC}"
      echo -e "    ${GREEN}clawmetry connect${NC}"
      echo -e "    ${GREEN}clawmetry --host 0.0.0.0 --port 8900 &${NC}"
      echo ""
    fi
    echo ""
  else
    echo -e "  ${DIM}No NemoClaw sandboxes found yet.${NC}"
    echo -e "  ${DIM}Once you create a sandbox, install ClawMetry inside:${NC}"
    echo -e "    ${GREEN}nemoclaw <sandbox-name> connect${NC}"
    echo -e "    ${GREEN}pip install --break-system-packages clawmetry${NC}"
    echo ""
  fi
fi

# ── Onboarding ───────────────────────────────────────────────────────────────
# Runs: clawmetry onboard (skipped when NemoClaw is detected — setup happens inside sandbox)

if [ "${CLAWMETRY_SKIP_ONBOARD:-}" = "1" ] || [ "$NEMOCLAW_DETECTED" = "1" ]; then
  [ "$NEMOCLAW_DETECTED" = "1" ] || echo -e "  ${DIM}Skipping onboard (CLAWMETRY_SKIP_ONBOARD=1)${NC}"
elif (exec </dev/tty) 2>/dev/null; then
  "$CLAWMETRY_BIN" onboard </dev/tty || true
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
