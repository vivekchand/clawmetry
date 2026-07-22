#!/usr/bin/env bash
# close-c6.sh: Apply required E2E status checks across all 3 repos in one shot.
#
# Prerequisites: gh CLI installed and authenticated as repo admin. ~30 seconds.
# No PAT creation, no repo secret setup, no Actions UI needed.
#
# Usage:
#   bash scripts/close-c6.sh
#
# What this does:
#   Adds 6 required status checks to main branch protection across 3 repos:
#     clawmetry         : OSS golden path (wheel + OpenClaw + 9 tabs)
#     clawmetry         : Cross-repo handoff (C4)
#     clawmetry         : MOAT Keystone (13-endpoint bar)
#     clawmetry         : E2E Browser Tests (critical subset)
#     clawmetry-cloud   : Cloud golden-path browser E2E
#     clawmetry-landing : Landing golden path (C3)
#
# After running: every PR in those 3 repos must pass the E2E suite to merge.
# This closes criterion C6 of the E2E Robustness epic.
#
# Tracking: vivekchand/clawmetry#3906

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=== C6: applying required E2E status checks ==="
echo ""
echo "Target repos and checks:"
echo "  clawmetry         : OSS golden path (wheel + OpenClaw + 9 tabs)"
echo "  clawmetry         : Cross-repo handoff (C4)"
echo "  clawmetry         : MOAT Keystone (13-endpoint bar)"
echo "  clawmetry         : E2E Browser Tests (critical subset)"
echo "  clawmetry-cloud   : Cloud golden-path browser E2E"
echo "  clawmetry-landing : Landing golden path (C3)"
echo ""

if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not found."
  echo "Install from https://cli.github.com then run: gh auth login"
  exit 1
fi

if ! gh auth status --active 2>/dev/null; then
  echo ""
  echo "ERROR: gh CLI is not authenticated. Run: gh auth login"
  exit 1
fi

TOKEN=$(gh auth token)
if [ -z "${TOKEN}" ]; then
  echo "ERROR: could not read token from gh CLI."
  exit 1
fi

echo "Got token from gh CLI."
echo ""

# Unset GITHUB_REPOSITORY so apply_required_status_checks.py applies
# all 6 checks across all 3 repos (not just the current repo).
unset GITHUB_REPOSITORY 2>/dev/null || true

GITHUB_TOKEN="${TOKEN}" python3 "${SCRIPT_DIR}/apply_required_status_checks.py"
