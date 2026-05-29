"""clawmetry/waste_flags.py: OSS delegating shim after the impl moved to clawmetry-pro.

The real per-run waste heuristics (runaway loops, cold cache, bloated
context, repeated-error chains) ship in the closed-source ``clawmetry-pro``
package as ``clawmetry_pro/lib/waste_flags.py``. Per-run waste flags
are a Pro feature (entitlement key ``per_run_waste_flags``).

When clawmetry-pro is installed, this shim delegates to the real
implementation so OSS callers (``routes/sessions.py``, ``routes/overview.py``,
``clawmetry/sync.py``) keep computing flags unchanged.

When clawmetry-pro is NOT installed, every flag computation returns an
empty list / safe default. OSS-only users do not see waste flags in their
dashboard; the Free tier degrades gracefully.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

logger = logging.getLogger("clawmetry.waste_flags")


def _pro():
    """Return ``clawmetry_pro.lib.waste_flags`` when importable, else ``None``."""
    try:
        from clawmetry_pro.lib import waste_flags as _w
        return _w
    except Exception:
        return None


# ── public surface ─────────────────────────────────────────────────────────────


def compute_flags(signals: Any) -> list[dict]:
    """Compute per-run waste flags. Returns ``[]`` when clawmetry-pro is
    not installed (Free tier sees no waste-flag overlay)."""
    pro = _pro()
    if pro is None:
        return []
    try:
        return pro.compute_flags(signals)
    except Exception as exc:
        logger.warning("waste_flags.compute_flags delegation failed: %s", exc)
        return []


def compute_signals_from_events(events: Iterable[dict]) -> dict:
    """Reduce events into the signal dict ``compute_flags`` consumes.
    Returns ``{}`` when clawmetry-pro is not installed."""
    pro = _pro()
    if pro is None:
        return {}
    try:
        return pro.compute_signals_from_events(events)
    except Exception as exc:
        logger.warning("waste_flags.compute_signals delegation failed: %s", exc)
        return {}


def runtime_from_session_id(session_id: Any) -> str:
    """Map a session id prefix to a runtime label. OSS Free always
    returns ``"openclaw"`` (the only Free runtime); when clawmetry-pro
    is installed the real lookup runs."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.runtime_from_session_id(session_id)
        except Exception:
            pass
    # Free-default: assume OpenClaw (the only Free runtime).
    return "openclaw"


def severity_from_counts(error_count: Any, flag_count: Any) -> str:
    """Map error + flag counts to a severity label. Free-default is
    ``"info"`` (no flagging happens on OSS-only)."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.severity_from_counts(error_count, flag_count)
        except Exception:
            pass
    return "info"


def event_is_real_error(event: Any) -> bool:
    """True when an event is a real error (not benign / not corrected).
    Free-default: returns ``False`` (assume not a real error when the
    pro filter isn't available; conservative for the dashboard's error
    counters)."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.event_is_real_error(event)
        except Exception:
            pass
    return False
