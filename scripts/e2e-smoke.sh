#!/usr/bin/env bash
# ClawMetry E2E smoke tests (curl-based, no browser required).
# Run this on a node that has clawmetry installed and the git repo present.
#
# Usage:
#   bash scripts/e2e-smoke.sh
#   REPO=/path/to/openclaw-dashboard bash scripts/e2e-smoke.sh
#
# Exit code: 0 = all pass, 1 = one or more failures.

set -euo pipefail

REPO="${REPO:-$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel 2>/dev/null || echo /home/vivek/projects/openclaw-dashboard)}"
PORT=9901
BASE="http://localhost:$PORT"
FAILURES=()

pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1"; FAILURES+=("$1"); }

# ---------------------------------------------------------------------------
# 1. Install & CLI
# ---------------------------------------------------------------------------
echo "=== 1. Install & CLI ==="
clawmetry --version >/dev/null 2>&1 && pass "clawmetry --version" || fail "clawmetry --version"
clawmetry status >/dev/null 2>&1 && pass "clawmetry status" || fail "clawmetry status"

# ---------------------------------------------------------------------------
# 2. Dashboard starts
# ---------------------------------------------------------------------------
echo "=== 2. Dashboard starts ==="
pkill -f "clawmetry.*${PORT}" 2>/dev/null || true
sleep 1
clawmetry --port "$PORT" &
CM_PID=$!
sleep 3

status=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")
[ "$status" = "200" ] && pass "dashboard / → 200" || fail "dashboard / → $status (expected 200)"

# ---------------------------------------------------------------------------
# 3. API endpoints
# ---------------------------------------------------------------------------
echo "=== 3. API endpoints ==="
for path in /api/overview /api/sessions /api/crons /api/memory /api/flow; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE$path")
    [ "$code" = "200" ] && pass "GET $path → 200" || fail "GET $path → $code (expected 200)"
done

overview=$(curl -s "$BASE/api/overview")
echo "$overview" | python3 -c "import sys,json; d=json.load(sys.stdin); ok='sessions' in d or 'activeSessions' in d; sys.exit(0 if ok else 1)" \
    && pass "/api/overview has sessions key" || fail "/api/overview missing sessions/activeSessions key"

# ---------------------------------------------------------------------------
# 4. install.sh correctness
# ---------------------------------------------------------------------------
echo "=== 4. install.sh ==="
first_line=$(curl -fsSL https://clawmetry.com/install.sh 2>/dev/null | head -1)
[[ "$first_line" == "#!/"* ]] && pass "install.sh starts with shebang" || fail "install.sh does not start with shebang: $first_line"

onboard_count=$(curl -fsSL https://clawmetry.com/install.sh 2>/dev/null | grep -c 'clawmetry onboard' || true)
[ "$onboard_count" -ge 1 ] && pass "install.sh contains 'clawmetry onboard'" || fail "install.sh missing 'clawmetry onboard'"

# ---------------------------------------------------------------------------
# 5. PyPI version matches GitHub public/main
#    Fetch before comparing so the local ref is never stale.
# ---------------------------------------------------------------------------
echo "=== 5. Version check ==="
git -C "$REPO" fetch public 2>/dev/null || true
PYPI=$(pip index versions clawmetry 2>/dev/null | head -1 | grep -oP '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
GH=$(git -C "$REPO" show public/main:dashboard.py 2>/dev/null | grep '__version__' | head -1 | grep -oP '[0-9]+\.[0-9]+\.[0-9]+' || true)
echo "  PyPI: $PYPI | GitHub public/main: $GH"
[ "$PYPI" = "$GH" ] && pass "VERSION_MATCH ($PYPI)" || fail "VERSION_MISMATCH (PyPI=$PYPI, GitHub=$GH)"

# ---------------------------------------------------------------------------
# 6. Cloud endpoints
#    Accept 200 or 302 — app.clawmetry.com redirects authenticated users to /fleet/.
# ---------------------------------------------------------------------------
echo "=== 6. Cloud endpoints ==="
code=$(curl -s -o /dev/null -w '%{http_code}' https://clawmetry.com/)
[ "$code" = "200" ] && pass "clawmetry.com → 200" || fail "clawmetry.com → $code (expected 200)"

code=$(curl -s -o /dev/null -w '%{http_code}' https://app.clawmetry.com/)
[[ "$code" == "200" || "$code" == "302" ]] \
    && pass "app.clawmetry.com → $code (200 or 302 ok)" \
    || fail "app.clawmetry.com → $code (expected 200 or 302)"

# ---------------------------------------------------------------------------
# 7. Cleanup
# ---------------------------------------------------------------------------
kill "$CM_PID" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
if [ ${#FAILURES[@]} -eq 0 ]; then
    echo "All tests passed."
    exit 0
else
    echo "FAILED tests (${#FAILURES[@]}):"
    for f in "${FAILURES[@]}"; do echo "  - $f"; done
    exit 1
fi
