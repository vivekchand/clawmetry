#!/usr/bin/env python3
"""
ClawMetry - See your agent think 🦞

Real-time observability dashboard for OpenClaw AI agents.
Single-file Flask app with zero config - auto-detects your setup.

Usage:
    clawmetry                             # Auto-detect everything
    clawmetry --port 9000                 # Custom port
    clawmetry --workspace ~/bot           # Custom workspace
    OPENCLAW_HOME=~/bot clawmetry

https://github.com/vivekchand/clawmetry
MIT License
"""

import os
import sys

# When run as `python dashboard.py`, this module is registered as `__main__`,
# not `dashboard`. Route blueprints in routes/ do `import dashboard as _d` at
# call time — without this alias, that import re-executes all 33k lines as a
# second `dashboard` module on first request, causing 10s+ timeouts on Windows
# CI (issue surfaced by the bp_sessions refactor).
sys.modules.setdefault("dashboard", sys.modules[__name__])

test_placeholder = True  # PLACEHOLDER - actual content will be in next push
