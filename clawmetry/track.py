"""
clawmetry.track — Zero-config HTTP interceptor for LLM cost tracking.

Activates ClawMetry's HTTP monkey-patching on import so any Python script
automatically gets per-call cost logging and a session summary at exit.

Usage:
    import clawmetry.track          # explicit — activate immediately

    CLAWMETRY_TRACK=1 python ...    # env-var — activate via clawmetry.__init__

The underlying implementation lives in clawmetry.interceptor.
This module is the user-facing shorthand that GH #374 introduced.
"""
from __future__ import annotations

import os as _os

# Allow opting out even when this module is explicitly imported
_disabled = _os.environ.get("CLAWMETRY_NO_INTERCEPT", "").strip() in ("1", "true", "yes")

if not _disabled:
    try:
        from clawmetry.interceptor import activate as _activate
        _activate()
    except Exception:
        pass  # never crash on import


def get_stats() -> dict:
    """Return current session cost/token stats dict."""
    try:
        from clawmetry.interceptor import get_session_stats
        return get_session_stats()
    except Exception:
        return {}


def set_source(name: str) -> None:
    """Tag every intercepted LLM call with a named source — your production
    agent's name (e.g. "support-agent"). Makes an out-loop agent built on any
    SDK (OpenAI Agents, LangChain, Vercel AI SDK, E2B, …) a first-class source
    in ClawMetry, so you can attribute cost per product. Equivalent to setting
    the ``CLAWMETRY_SOURCE`` env var.

    Usage::

        import clawmetry.track
        clawmetry.track.set_source("support-agent")
    """
    try:
        from clawmetry.interceptor import set_source as _set
        _set(name)
    except Exception:
        pass


__all__ = ["get_stats", "set_source"]
