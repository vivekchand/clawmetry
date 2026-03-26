"""
clawmetry/sitecustomize_hook.py — Zero-config auto-activation.

This module is triggered on every Python startup via a ``clawmetry-auto.pth``
file installed into site-packages.  It installs the HTTP interceptor so that
LLM API costs are tracked without any code changes from the user.

Opt-out:
    CLAWMETRY_DISABLE=1  — disables all auto-tracking for this process.
"""
from __future__ import annotations

import os


def activate() -> None:
    """Install the HTTP interceptor.  Never raises — user's process is sacred."""
    if os.environ.get("CLAWMETRY_DISABLE"):
        return
    try:
        from clawmetry.interceptor import patch_http
        from clawmetry.ledger import get_ledger
        import atexit

        _ledger = get_ledger()
        patch_http(_ledger)

        def _on_exit() -> None:
            try:
                stats = _ledger.session_total()
                if stats["calls"] > 0:
                    by_provider = " · ".join(
                        f"{p}: ${c:.2f}" for p, c in stats["by_provider"].items()
                    )
                    duration = stats["duration_seconds"]
                    mins, secs = divmod(int(duration), 60)
                    today = _ledger.today_total()
                    monthly = _ledger.monthly_estimate()
                    print(
                        f"\nclawmetry \u25b8 session: ${stats['total_usd']:.2f} "
                        f"({stats['calls']} calls, {mins}m {secs}s) "
                        f"\u2500\u2500 today: ${today['total_usd']:.2f} "
                        f"\u2500\u2500 ~${monthly:.0f}/mo"
                    )
                    if by_provider:
                        print(f"           {by_provider}")
            except Exception:
                pass

        atexit.register(_on_exit)
    except Exception:
        pass  # Never crash the user's process


activate()
