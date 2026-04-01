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
    bash "$PRESET_SCRIPT" >/dev/null 2>&1 \
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
          # Use the venv python directly (most reliable on macOS)
          _PY="$INSTALL_DIR/bin/python3"
          [ -x "$_PY" ] || _PY="python3"
          HOST_API_KEY=$("$_PY" -c "import json; print(json.load(open('$HOST_CONFIG')).get('api_key',''))" 2>/dev/null || true)
          HOST_ENC_KEY=$("$_PY" -c "import json; print(json.load(open('$HOST_CONFIG')).get('encryption_key',''))" 2>/dev/null || true)
        fi
      }

      _read_host_config

      if [ -n "$HOST_API_KEY" ]; then
        echo -e "  ${GREEN}${BOLD}✓ ClawMetry Cloud already authenticated${NC}"
      elif [ -z "$HOST_API_KEY" ]; then
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
            # Clear stale config + sync state if key doesn't match (new account)
            if [ -n "$SB_KEY" ] && [ "$SB_KEY" != "$HOST_API_KEY" ]; then
              docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
                bash -s >/dev/null 2>&1 << 'CLEAR_SCRIPT'
rm -f /root/.clawmetry/config.json /sandbox/.clawmetry/config.json
# Reset sync state so events re-upload under new account
for state_file in /root/.clawmetry/sync-state.json /sandbox/.clawmetry/sync-state.json; do
  if [ -f "$state_file" ]; then
    python3 -c "import json; p='$state_file'; s=json.load(open(p)); s['last_event_ids']={} ; json.dump(s,open(p,'w'))"
  fi
done
CLEAR_SCRIPT
              echo -e "  ${DIM}↺ Cleared stale config (different account)${NC}"
            fi
            # Pre-write config so --key matches _saved_api_key (skips OTP verification)
            CONNECT_TS=$(date -u +%Y-%m-%dT%H:%M:%S 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)
            # Write config to both root and sandbox user homes
            docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
              bash -c "
python3 - << PYEOF
import json, os, shutil
cfg = {'api_key':'$HOST_API_KEY','node_id':'$sb','platform':'Linux','connected_at':'$CONNECT_TS','encryption_key':'$HOST_ENC_KEY'}
for d in ['/root/.clawmetry', '/sandbox/.clawmetry']:
    os.makedirs(d, exist_ok=True)
    json.dump(cfg, open(d + '/config.json', 'w'))
# chown sandbox home to sandbox user
os.system('chown -R sandbox:sandbox /sandbox/.clawmetry 2>/dev/null')
PYEOF
" 2>/dev/null || true

            # Connect non-interactively (OTP skipped — key matches saved config)
            if docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
              clawmetry connect --key "$HOST_API_KEY" --enc-key "$HOST_ENC_KEY" --node-id "$sb" --no-daemon >/dev/null 2>&1; then
              echo -e "  ${GREEN}${BOLD}✓ Sandbox $sb connected (node: $sb)${NC}"
              # Ensure daemon survives kubectl exec session end via supervisord if available
              docker exec "$CLUSTER_CONTAINER" kubectl exec -n openshell "$sb" -- \
                bash -c 'command -v supervisorctl >/dev/null 2>&1 && supervisorctl start clawmetry-sync >/dev/null 2>&1 || true' 2>/dev/null || true
            else
              echo -e "  ${DIM}⚠  Could not connect sandbox $sb automatically.${NC}"
              echo -e "  ${DIM}Connect manually: nemoclaw $sb connect → clawmetry connect${NC}"
            fi
          fi
        done
      fi

      # Step 2d: Start supervisord inside each sandbox to keep daemon alive
      echo "$SANDBOX_NAMES" | while IFS= read -r sb; do
        [ -z "$sb" ] && continue
        echo -e "  → Starting supervisor in sandbox ${BOLD}${sb}${NC}..."

        # Ensure PyPI + ClawMetry policies applied before pip install
        for _pol in clawmetry pypi; do
          printf '%s\ny\n' "$_pol" | nemoclaw "$sb" policy-add >/dev/null 2>&1 || true
        done
        # Wait for network policy to propagate inside sandbox
        sleep 5

        _sb_out=$(docker exec -i "$CLUSTER_CONTAINER" kubectl exec -i -n openshell "$sb" -- \
          bash -s 2>&1 << 'SANDBOX_SCRIPT'
            set -e

            # Install supervisord if missing
            command -v supervisord >/dev/null 2>&1 || pip install --break-system-packages --quiet supervisor 2>/dev/null

            # Detect the real OpenClaw data directory (NemoClaw stores it at /sandbox/.openclaw-data)
            # Walk /sandbox, /root and /home to find agents/main/sessions — do NOT hardcode the path.
            _oc_dir=""
            for _search_root in /sandbox /root /home; do
              _hit=$(find "$_search_root" -maxdepth 6 -name "sessions.json" \
                       -path "*/agents/main/sessions/*" 2>/dev/null | head -1)
              if [ -n "$_hit" ]; then
                # Walk up 4 levels from sessions.json to reach the openclaw root
                # sessions.json lives at <root>/agents/main/sessions/sessions.json
                _oc_dir=$(dirname "$_hit")   # .../agents/main/sessions
                _oc_dir=$(dirname "$_oc_dir") # .../agents/main
                _oc_dir=$(dirname "$_oc_dir") # .../agents
                _oc_dir=$(dirname "$_oc_dir") # <openclaw-root>
                break
              fi
            done
            # Fallback: use the clawmetry config path (guaranteed to exist after connect)
            if [ -z "$_oc_dir" ]; then
              _clawmetry_config=$(cat /sandbox/.clawmetry/config.json 2>/dev/null || cat /root/.clawmetry/config.json 2>/dev/null || echo "")
              _oc_dir="/sandbox/.openclaw-data"
              echo "WARN: openclaw sessions not found; defaulting to $_oc_dir"
            fi
            echo "INFO: CLAWMETRY_OPENCLAW_DIR=$_oc_dir"

            # Resolve the clawmetry config path
            if [ -f /sandbox/.clawmetry/config.json ]; then
              _cm_config="/sandbox/.clawmetry/config.json"
              _cm_log="/sandbox/.clawmetry/sync.log"
            else
              _cm_config="/root/.clawmetry/config.json"
              _cm_log="/root/.clawmetry/sync.log"
            fi

            # Resolve sync.py path
            SYNC_PATH=$(python3 -c "import clawmetry.sync, os; print(os.path.abspath(clawmetry.sync.__file__))")

            # Write supervisord configs
            mkdir -p /etc/supervisor/conf.d /var/log/supervisor /var/run

            cat > /etc/supervisor/supervisord.conf << 'SUPEOF'
[unix_http_server]
file=/var/run/supervisor.sock
[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
nodaemon=false
[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
[supervisorctl]
serverurl=unix:///var/run/supervisor.sock
[include]
files = /etc/supervisor/conf.d/*.conf
SUPEOF

            cat > /etc/supervisor/conf.d/clawmetry-sync.conf << PROGEOF
[program:clawmetry-sync]
command=python3 ${SYNC_PATH}
autostart=true
autorestart=true
startretries=10
startsecs=3
stdout_logfile=${_cm_log}
stderr_logfile=${_cm_log}
stdout_logfile_maxbytes=10MB
environment=HOME="/sandbox",CLAWMETRY_CONFIG="${_cm_config}",CLAWMETRY_OPENCLAW_DIR="${_oc_dir}"
PROGEOF

            # Verify conf files were actually written before proceeding
            if [ ! -f /etc/supervisor/supervisord.conf ]; then
              echo "ERROR: failed to write /etc/supervisor/supervisord.conf" >&2
              exit 1
            fi
            if [ ! -f /etc/supervisor/conf.d/clawmetry-sync.conf ]; then
              echo "ERROR: failed to write /etc/supervisor/conf.d/clawmetry-sync.conf" >&2
              exit 1
            fi

            # Kill ALL stray sync.py daemons before supervisord takes over
            kill "$(cat /root/.clawmetry/sync.pid 2>/dev/null)" 2>/dev/null || true
            kill "$(cat /sandbox/.clawmetry/sync.pid 2>/dev/null)" 2>/dev/null || true
            rm -f /root/.clawmetry/sync.pid /sandbox/.clawmetry/sync.pid
            for _f in /proc/[0-9]*/cmdline; do
              _p="${_f%/cmdline}"; _p="${_p#/proc/}"
              if grep -qa "sync.py" "$_f" 2>/dev/null && grep -qa "clawmetry" "$_f" 2>/dev/null; then
                kill "$_p" 2>/dev/null || true
              fi
            done
            sleep 1

            # Shut down existing supervisord cleanly, then start fresh
            if supervisorctl -c /etc/supervisor/supervisord.conf pid >/dev/null 2>&1; then
              supervisorctl -c /etc/supervisor/supervisord.conf shutdown >/dev/null 2>&1 || true
              sleep 2
            fi
            kill "$(cat /var/run/supervisord.pid 2>/dev/null)" 2>/dev/null || true
            rm -f /var/run/supervisord.pid /var/run/supervisor.sock
            sleep 1
            supervisord -c /etc/supervisor/supervisord.conf
            sleep 3
            supervisorctl -c /etc/supervisor/supervisord.conf status
SANDBOX_SCRIPT
        )
        _rc=$?
        # Surface any WARN/ERROR/INFO lines from the sandbox script
        _info=$(echo "$_sb_out" | grep -E "^(INFO|WARN|ERROR):" || true)
        if [ "$_rc" -eq 0 ]; then
          echo -e "  ${GREEN}${BOLD}✓ Supervisor running in $sb${NC}"
          [ -n "$_info" ] && echo -e "  ${DIM}$_info${NC}"
        else
          echo -e "  ${DIM}⚠  Could not start supervisor in $sb${NC}"
          [ -n "$_sb_out" ] && echo -e "  ${DIM}$_sb_out${NC}"
        fi
      done

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
