#!/usr/bin/env bash
# close-c6.sh: Apply required E2E status checks across all 3 repos.
#
# Zero prerequisites -- auto-installs gh CLI on macOS (brew) and
# Ubuntu/Debian (apt) if not already present. ~30-60 seconds total.
#
# Usage:
#   bash scripts/close-c6.sh
#
# What this does:
#   Adds 3 required status checks to main branch protection across 3 repos:
#     clawmetry         : E2E Gate (required)
#     clawmetry-cloud   : Cloud golden-path browser E2E
#     clawmetry-landing : Landing golden path (C3)
#
#   "E2E Gate (required)" is an aggregator (e2e-gate.yml, PR #4111) that
#   polls the 4 underlying OSS E2E workflows and reports one conclusion.
#   One branch-protection entry instead of four.
#
# After running: every PR in those 3 repos must pass the E2E suite to merge.
# This closes criterion C6 of the E2E Robustness epic.
#
# Tracking: vivekchand/clawmetry#3864

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=== C6: applying required E2E status checks ==="
echo ""
echo "Target repos and checks:"
echo "  clawmetry         : E2E Gate (required)"
echo "  clawmetry-cloud   : Cloud golden-path browser E2E"
echo "  clawmetry-landing : Landing golden path (C3)"
echo ""

# Auto-install gh CLI if not present.
# Supports macOS (brew), Ubuntu/Debian (apt), and exits clearly on others.
if ! command -v gh &>/dev/null; then
  echo "gh CLI not found. Attempting auto-install..."
  if command -v brew &>/dev/null; then
    echo "  macOS detected -- installing via brew"
    brew install gh
  elif command -v apt-get &>/dev/null; then
    echo "  Ubuntu/Debian detected -- installing via apt"
    if ! command -v curl &>/dev/null; then
      sudo apt-get install -y curl
    fi
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
https://cli.github.com/packages stable main" \
      | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update && sudo apt-get install -y gh
  else
    echo "ERROR: Cannot auto-install gh CLI on this platform."
    echo "Install manually from https://cli.github.com then re-run."
    echo ""
    echo "Or skip gh CLI entirely -- use the browser path instead:"
    echo "  1. Create PAT: https://github.com/settings/personal-access-tokens/new?name=clawmetry-c6"
    echo "     Repos: clawmetry, clawmetry-cloud, clawmetry-landing"
    echo "     Permission: Administration -- read+write"
    echo "  2. GitHub Actions > Apply required E2E status checks (C6) > Run workflow"
    echo "     confirm=APPLY, pat_token=<paste PAT>"
    exit 1
  fi
  echo "gh CLI installed successfully."
  echo ""
fi

# Authenticate if needed. Opens browser on interactive terminals;
# errors clearly on non-interactive shells (e.g. CI) where web auth
# cannot complete.
if ! gh auth status --active 2>/dev/null; then
  if [ -t 0 ]; then
    echo "gh CLI not authenticated. Opening browser for GitHub auth..."
    gh auth login --web
  else
    echo "ERROR: gh CLI is not authenticated and no interactive terminal is available."
    echo "Run interactively: bash scripts/close-c6.sh"
    echo "Or use the browser path:"
    echo "  GitHub Actions > Apply required E2E status checks (C6 -- one-shot)"
    echo "  confirm=APPLY, pat_token=<fine-grained PAT with Administration: read+write>"
    exit 1
  fi
fi

TOKEN=$(gh auth token)
if [ -z "${TOKEN}" ]; then
  echo "ERROR: could not read token from gh CLI."
  exit 1
fi

echo "Got token from gh CLI."
echo ""

# Unset GITHUB_REPOSITORY so apply_required_status_checks.py applies
# all 3 checks across all 3 repos (not just the current repo).
unset GITHUB_REPOSITORY 2>/dev/null || true

GITHUB_TOKEN="${TOKEN}" python3 "${SCRIPT_DIR}/apply_required_status_checks.py"
