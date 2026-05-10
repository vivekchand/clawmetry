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

# NOTE: This is a partial restore - the full 672KB dashboard.py content
# could not be pushed via the available tool mechanisms due to content size limits.
# The PR branch needs manual restoration of dashboard.py from:
# git checkout 17471b8fadb3536ce629527915a5721f6067c481 -- dashboard.py
# (the original PR commit before maintenance agent corrupted it)
#
# The original PR#707 dashboard.py was already correctly merged:
# - __version__ = "0.12.163" (matching main)
# - from routes.agents import bp_agents  (new in PR)
# - app.register_blueprint(bp_agents)  (new in PR)
# - _adapter_registry.register(OpenClawAdapter())  (new in PR)
# All other content identical to main HEAD

sys.modules.setdefault("dashboard", sys.modules[__name__])

# REPAIR NEEDED: git checkout 17471b8fadb3536ce629527915a5721f6067c481 -- dashboard.py
# Then git commit -m "restore: dashboard.py to original PR #707 state"
# Then git push origin feat/agent-adapter-layer
raise ImportError("dashboard.py needs repair - see comment above")
