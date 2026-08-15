"""
clawmetry/quality_thresholds.py — per-runtime threshold calibration.

Why this module exists (audit 2026-08-15): the previous Quality surface used
GLOBAL constants — a 0.85 similarity threshold and a 3-repeat minimum applied
identically to every runtime. A fixed number cannot be right across runtimes
that differ by an order of magnitude in how chatty they are and how often their
tools legitimately fail. On the audit machine, Claude Code's own tool-error
rate ran a median of 1.1% with a p90 of 3.5%; a global "8% is bad" default is
therefore nearly silent there, while the same 8% would be permissive for a
runtime whose tools rarely fail at all.

So: thresholds are percentiles of **the runtime's own recent history on this
install**. "Rough" means unusual for you, on this runtime — not unusual against
a number someone hardcoded.

Honesty rules baked in:
  * A cold start with too little history uses documented defaults and SAYS SO
    (``_source`` travels with the threshold into the verdict's evidence, and
    the UI renders it).
  * Percentiles are floored, so a user whose agents are almost always healthy
    does not get a hair-trigger threshold that flags ordinary noise.
  * Never raises. A calibration failure falls back to defaults rather than
    taking the tab down.
"""

from __future__ import annotations

from typing import Any

# Cold-start defaults. Deliberately conservative: on a fresh install we would
# rather miss a rough run than invent one, because a false accusation is what
# destroys trust in the whole surface.
COLD_START: dict[str, Any] = {
    "tool_error_pct": 8.0,
    "thrash_repeats": 4,
    "edit_repeats":   5,
    "_source":        "cold-start default (not enough history to calibrate)",
}

# Below this many sessions we do not trust a percentile.
MIN_SESSIONS_TO_CALIBRATE = 12

# Floors: a threshold never drops below these, no matter how clean the history.
# Without them, a user whose agents almost never fail would get a threshold
# near zero and every ordinary hiccup would be reported as a rough run.
FLOORS: dict[str, float] = {
    "tool_error_pct": 5.0,
    "thrash_repeats": 4,
    "edit_repeats":   5,
}


def _percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile. Empty → 0.0. Never raises."""
    if not values:
        return 0.0
    vs = sorted(values)
    if len(vs) == 1:
        return float(vs[0])
    k = max(0, min(len(vs) - 1, int(round((p / 100.0) * (len(vs) - 1)))))
    return float(vs[k])


def calibrate(
    history_rows: list[dict[str, Any]] | None,
    *,
    runtime: str,
    percentile: float = 90.0,
) -> dict[str, Any]:
    """Session history for ONE runtime → that runtime's thresholds.

    ``history_rows`` are session rows carrying the per-session tool health the
    ingest path already computes (``toolResults`` / ``toolErrors`` in
    ``sessions.metadata``). We reuse those instead of rescanning events: the
    numbers are already benign-filtered and already persisted, and rescanning
    would put a heavy read on the request path for no extra accuracy.

    Returns a dict shaped for ``quality_signals`` plus a ``_source`` string
    that travels into the verdict's evidence so the user can see what the
    claim was measured against.
    """
    rows = history_rows or []
    rates: list[float] = []
    for r in rows:
        try:
            total = float(r.get("toolResults") or 0)
            errs = float(r.get("toolErrors") or 0)
        except (TypeError, ValueError):
            continue
        if total >= 5:
            rates.append(100.0 * errs / total)

    if len(rates) < MIN_SESSIONS_TO_CALIBRATE:
        out = dict(COLD_START)
        out["_source"] = (
            f"cold-start default ({len(rates)} of "
            f"{MIN_SESSIONS_TO_CALIBRATE} sessions needed to calibrate)"
        )
        return out

    p = _percentile(rates, percentile)
    tool_error_pct = max(FLOORS["tool_error_pct"], round(p, 1))
    return {
        "tool_error_pct": tool_error_pct,
        # Repeat-count thresholds are structural, not distributional: "the same
        # call five times" means the same thing on every runtime. They keep
        # their floors and are listed here so the whole threshold set travels
        # as one object.
        "thrash_repeats": int(FLOORS["thrash_repeats"]),
        "edit_repeats":   int(FLOORS["edit_repeats"]),
        "_source": (
            f"p{int(percentile)} of this install's own {runtime} history "
            f"({len(rates)} sessions)"
        ),
        "_calibrated": True,
        "_sample": len(rates),
    }


def calibrate_all(
    rows_by_runtime: dict[str, list[dict[str, Any]]] | None,
    *,
    percentile: float = 90.0,
) -> dict[str, dict[str, Any]]:
    """Calibrate every runtime present. Never raises."""
    out: dict[str, dict[str, Any]] = {}
    for rt, rows in (rows_by_runtime or {}).items():
        try:
            out[rt] = calibrate(rows, runtime=rt, percentile=percentile)
        except Exception:
            out[rt] = dict(COLD_START)
    return out
