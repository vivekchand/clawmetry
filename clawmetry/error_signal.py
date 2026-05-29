"""clawmetry/error_signal.py: OSS delegating shim after the impl moved to clawmetry-pro.

The real benign-error filter + corrected_is_error heuristics ship in
the closed-source ``clawmetry-pro`` package as
``clawmetry_pro/lib/error_signal.py``. Error triage / benign filtering
is a Pro feature (entitlement key ``error_triage``).

When clawmetry-pro is installed, this shim delegates to the real impl
so OSS callers (``clawmetry/sync.py``, ``clawmetry/local_store.py``,
``routes/selfevolve.py`` stub) keep filtering unchanged.

When clawmetry-pro is NOT installed:
* ``is_benign_tool_error`` returns ``False`` (no benign classification)
* ``corrected_is_error`` returns ``raw_is_error`` (no correction)
* ``extract_tool_result_text`` returns ``""``

This means OSS-only dashboards may surface a few transient errors that
the Pro filter would have suppressed, but never under-reports real
failures.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("clawmetry.error_signal")


def _pro():
    """Return ``clawmetry_pro.lib.error_signal`` when importable, else ``None``."""
    try:
        from clawmetry_pro.lib import error_signal as _e
        return _e
    except Exception:
        return None


# ── public surface ─────────────────────────────────────────────────────────────


def is_benign_tool_error(text: Any) -> bool:
    """True when the tool-result text matches a known benign pattern
    (transient retries, read-guard re-reads, etc). Returns ``False``
    when clawmetry-pro is not installed."""
    pro = _pro()
    if pro is None:
        return False
    try:
        return pro.is_benign_tool_error(text)
    except Exception:
        return False


def extract_tool_result_text(data: Any) -> str:
    """Pull the human-readable text out of a tool-result event for
    benign-pattern matching. Returns ``""`` when clawmetry-pro is not
    installed."""
    pro = _pro()
    if pro is None:
        return ""
    try:
        return pro.extract_tool_result_text(data)
    except Exception:
        return ""


def corrected_is_error(raw_is_error: Any, result_text: Any) -> bool:
    """Corrected ``is_error`` flag: same as the raw value when the
    pattern doesn't match a known benign signature. Returns ``raw_is_error``
    coerced to bool when clawmetry-pro is not installed (no correction)."""
    pro = _pro()
    if pro is None:
        return bool(raw_is_error)
    try:
        return pro.corrected_is_error(raw_is_error, result_text)
    except Exception:
        return bool(raw_is_error)
