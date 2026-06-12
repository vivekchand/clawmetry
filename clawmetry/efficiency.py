"""
clawmetry/efficiency.py — Efficiency grade + measured savings (pure math).

Turns per-(runtime, model) window aggregates (LocalStore.query_efficiency_rollup
over ``rollup_model_daily``) into an honest efficiency report card:

  * three metrics  — cache hit rate, cache-write ROI, average context size;
  * a 0-100 score + letter grade (null with ``insufficient_data`` when the
    window has fewer than 10 calls — never a fake grade);
  * ranked savings ``actions`` (model_downgrade / context_trim / cache_warm),
    each carrying the raw inputs in ``data`` — NO user-facing copy here, the
    frontend owns the wording;
  * ``cache_saved_monthly_usd`` — what prompt caching already saved (positive
    reinforcement, not an action).

All dollar math goes through :mod:`clawmetry.providers_pricing`
(``_get_rates`` / ``provider_for_model`` / the cache multipliers /
``default_auto_downgrade_map``) — never a hardcoded price.

Pure + unit-testable: no I/O, no store access. NEVER raises — garbage rows
are coerced to zeros (with a logged warning) and any unexpected failure
yields the honest empty shape.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from clawmetry.providers_pricing import (
    _CACHE_READ_MULT,
    _CACHE_WRITE_MULT,
    _get_rates,
    default_auto_downgrade_map,
    downgrade_model_name,
    provider_for_model,
)

log = logging.getLogger("clawmetry.efficiency")

# Grading thresholds / weights (3 metrics — truncation data isn't in the store).
_MIN_CALLS_FOR_GRADE = 10
_MONTH_DAYS = 30.0
# Sum of action savings can never claim more than 90% of the projected
# monthly spend — estimates that "save more than you spend" read as snake oil.
_SAVINGS_CAP_FRACTION = 0.9

# model_downgrade emission gates: short outputs, real volume, real spend.
_DOWNGRADE_MAX_AVG_OUT = 300.0
_DOWNGRADE_MIN_CALLS = 20
_DOWNGRADE_MIN_WINDOW_COST_USD = 1.0

# context_trim: only flag genuinely heavy contexts; assume ~40% is trimmable.
_CONTEXT_TRIM_THRESHOLD_TOKENS = 40_000.0
_CONTEXT_TRIM_FRACTION = 0.4

_NUM_FIELDS = (
    "tokens_in", "tokens_out", "cache_read", "cache_write",
    "cost_usd", "calls", "days_with_data",
)


def _num(value: Any) -> float:
    """Coerce any value to a non-negative finite float (bad input -> 0.0)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(f) or f < 0:
        return 0.0
    return f


def _coerce_row(row: Any) -> dict[str, Any] | None:
    """Normalise one aggregate row; ``None`` (skip) when it isn't a mapping."""
    if not isinstance(row, dict):
        log.warning("efficiency: skipping non-dict row %r", type(row).__name__)
        return None
    out: dict[str, Any] = {
        "runtime": str(row.get("runtime") or "openclaw"),
        "model": str(row.get("model") or ""),
    }
    for k in _NUM_FIELDS:
        out[k] = _num(row.get(k))
    return out


def _rates_for(model: str) -> tuple[float, float]:
    """(input_per_1m, output_per_1m) for a model via the shared pricing table."""
    return _get_rates(provider_for_model(model), model)


def _grade_for_score(score: float | None) -> str | None:
    """Letter grade for a 0-100 score (None passes through)."""
    if score is None:
        return None
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"


def _score_points(
    cache_hit_rate_pct: float | None,
    cache_roi: float | None,
    cache_write: float,
    avg_context_tokens: float | None,
) -> int:
    """0-100 score from the three weighted metrics."""
    pts = 0
    hr = cache_hit_rate_pct if cache_hit_rate_pct is not None else 0.0
    if hr >= 60:
        pts += 40
    elif hr >= 40:
        pts += 28
    elif hr >= 20:
        pts += 16
    elif hr >= 5:
        pts += 6
    # Cache-write ROI (30): no cache writes at all is neutral, not punished.
    if cache_write <= 0:
        pts += 18
    elif cache_roi is not None:
        if cache_roi >= 3:
            pts += 30
        elif cache_roi >= 2:
            pts += 24
        elif cache_roi >= 1:
            pts += 14
        elif cache_roi >= 0.5:
            pts += 6
    # Average context size (30).
    ctx = avg_context_tokens if avg_context_tokens is not None else 0.0
    if ctx <= 20_000:
        pts += 30
    elif ctx <= 50_000:
        pts += 24
    elif ctx <= 100_000:
        pts += 12
    elif ctx <= 200_000:
        pts += 6
    return pts


def _empty_scope(days: int) -> dict[str, Any]:
    """Honest no-data shape (shared by empty input and the error fallback)."""
    return {
        "schema": 1,
        "window_days": days,
        "grade": None,
        "score": None,
        "insufficient_data": True,
        "metrics": {
            "cache_hit_rate_pct": None,
            "cache_roi": None,
            "avg_context_tokens": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "cache_read": 0,
            "cache_write": 0,
            "calls": 0,
            "window_cost_usd": 0.0,
            "days_with_data": 0,
        },
        "cache_saved_monthly_usd": 0.0,
        "projected_monthly_cost_usd": 0.0,
        "actions": [],
    }


def _build_scope(rows: list[dict[str, Any]], days: int) -> dict[str, Any]:
    """Grade + actions for one scope (the whole node, or one runtime)."""
    if not rows:
        return _empty_scope(days)

    # Per-model aggregation (the action math is per model) + scope totals.
    per_model: dict[str, dict[str, float]] = {}
    for r in rows:
        m = r["model"]
        agg = per_model.setdefault(m, {
            "tokens_in": 0.0, "tokens_out": 0.0, "cache_read": 0.0,
            "cache_write": 0.0, "cost_usd": 0.0, "calls": 0.0,
        })
        for k in agg:
            agg[k] += r[k]
    tokens_in = sum(a["tokens_in"] for a in per_model.values())
    tokens_out = sum(a["tokens_out"] for a in per_model.values())
    cache_read = sum(a["cache_read"] for a in per_model.values())
    cache_write = sum(a["cache_write"] for a in per_model.values())
    cost_usd = sum(a["cost_usd"] for a in per_model.values())
    calls = sum(a["calls"] for a in per_model.values())
    days_with_data = int(max((r["days_with_data"] for r in rows), default=0))
    factor = _MONTH_DAYS / max(1, days_with_data)

    # ── metrics ──────────────────────────────────────────────────────────
    hit_denom = cache_read + tokens_in
    cache_hit_rate_pct = (cache_read / hit_denom * 100.0) if hit_denom > 0 else None
    cache_roi = (cache_read / cache_write) if cache_write > 0 else None
    avg_context_tokens = (
        (tokens_in + cache_read + cache_write) / calls if calls > 0 else None
    )

    # ── score / grade (never a fake grade on a thin window) ─────────────
    insufficient = calls < _MIN_CALLS_FOR_GRADE
    if insufficient:
        score: int | None = None
    else:
        score = _score_points(
            cache_hit_rate_pct, cache_roi, cache_write, avg_context_tokens
        )
    grade = _grade_for_score(score)

    # ── actions (window math first, scaled to monthly below) ────────────
    actions: list[dict[str, Any]] = []
    input_side_window_usd = 0.0
    warm_wasted_window_usd = 0.0
    warm_models: list[dict[str, Any]] = []
    cache_saved_window_usd = 0.0
    for model, agg in per_model.items():
        in_rate, _out_rate = _rates_for(model)
        # Measured savings caching already delivered: every cached-read token
        # was billed at _CACHE_READ_MULT instead of the full input rate.
        cache_saved_window_usd += (
            agg["cache_read"] * in_rate * (1.0 - _CACHE_READ_MULT) / 1e6
        )
        # Input-side window cost (for context_trim).
        input_side_window_usd += (
            agg["tokens_in"] * in_rate
            + agg["cache_read"] * in_rate * _CACHE_READ_MULT
            + agg["cache_write"] * in_rate * _CACHE_WRITE_MULT
        ) / 1e6
        # cache_warm: writes that never paid back (re-read tax).
        if agg["cache_write"] > 0:
            roi_m = agg["cache_read"] / agg["cache_write"]
            if roi_m < 1.0:
                wasted = (
                    agg["cache_write"] * in_rate * _CACHE_WRITE_MULT / 1e6
                ) * (1.0 - roi_m)
                if wasted > 0:
                    warm_wasted_window_usd += wasted
                    warm_models.append({
                        "model": model,
                        "cache_roi": round(roi_m, 4),
                        "wasted_window_usd": round(wasted, 6),
                    })
        # model_downgrade: short-output high-volume traffic on a model with a
        # cheaper same-provider sibling in the shared downgrade map.
        target = downgrade_model_name(model, default_auto_downgrade_map())
        if (
            target
            and agg["calls"] >= _DOWNGRADE_MIN_CALLS
            and agg["cost_usd"] >= _DOWNGRADE_MIN_WINDOW_COST_USD
            and (agg["tokens_out"] / agg["calls"]) < _DOWNGRADE_MAX_AVG_OUT
        ):
            t_in, t_out = _rates_for(target)
            target_cost = (
                agg["tokens_in"] * t_in
                + agg["tokens_out"] * t_out
                + agg["cache_read"] * t_in * _CACHE_READ_MULT
                + agg["cache_write"] * t_in * _CACHE_WRITE_MULT
            ) / 1e6
            saving = agg["cost_usd"] - target_cost
            if saving > 0:
                actions.append({
                    "id": "model_downgrade",
                    "model": model,
                    "savings_monthly_usd": saving * factor,
                    # Token math is exact; substituting the model is the
                    # hypothesis — still not flagged as an estimate per spec.
                    "estimate": False,
                    "data": {
                        "target_model": target,
                        "calls": int(agg["calls"]),
                        "avg_tokens_out": round(agg["tokens_out"] / agg["calls"], 2),
                        "window_cost_usd": round(agg["cost_usd"], 6),
                        "target_window_cost_usd": round(target_cost, 6),
                    },
                })
    if (
        avg_context_tokens is not None
        and avg_context_tokens > _CONTEXT_TRIM_THRESHOLD_TOKENS
        and input_side_window_usd > 0
    ):
        actions.append({
            "id": "context_trim",
            "savings_monthly_usd": input_side_window_usd * _CONTEXT_TRIM_FRACTION * factor,
            "estimate": True,
            "data": {
                "avg_context_tokens": round(avg_context_tokens, 1),
                "input_side_window_cost_usd": round(input_side_window_usd, 6),
                "trim_fraction": _CONTEXT_TRIM_FRACTION,
            },
        })
    if warm_wasted_window_usd > 0:
        actions.append({
            "id": "cache_warm",
            "savings_monthly_usd": warm_wasted_window_usd * factor,
            "estimate": True,
            "data": {
                "wasted_window_usd": round(warm_wasted_window_usd, 6),
                "models": warm_models,
            },
        })

    # ── monthly scaling + the 0.9 sanity cap ─────────────────────────────
    projected_monthly_cost_usd = cost_usd * factor
    total_savings = sum(a["savings_monthly_usd"] for a in actions)
    cap = _SAVINGS_CAP_FRACTION * projected_monthly_cost_usd
    if total_savings > cap and total_savings > 0:
        scale = cap / total_savings
        for a in actions:
            a["savings_monthly_usd"] *= scale
        # Anything scaled down to nothing isn't worth showing.
        actions = [a for a in actions if a["savings_monthly_usd"] > 0]
    actions.sort(key=lambda a: -a["savings_monthly_usd"])
    for a in actions:
        a["savings_monthly_usd"] = round(a["savings_monthly_usd"], 6)

    return {
        "schema": 1,
        "window_days": days,
        "grade": grade,
        "score": score,
        "insufficient_data": insufficient,
        "metrics": {
            "cache_hit_rate_pct": (
                round(cache_hit_rate_pct, 2) if cache_hit_rate_pct is not None else None
            ),
            "cache_roi": round(cache_roi, 4) if cache_roi is not None else None,
            "avg_context_tokens": (
                round(avg_context_tokens, 1) if avg_context_tokens is not None else None
            ),
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "cache_read": int(cache_read),
            "cache_write": int(cache_write),
            "calls": int(calls),
            "window_cost_usd": round(cost_usd, 6),
            "days_with_data": days_with_data,
        },
        "cache_saved_monthly_usd": round(cache_saved_window_usd * factor, 6),
        "projected_monthly_cost_usd": round(projected_monthly_cost_usd, 6),
        "actions": actions,
    }


def build_efficiency_slice(rows: list[dict], days: int = 30) -> dict:
    """Efficiency grade + measured-savings slice for a node.

    ``rows`` are per-(runtime, model) aggregates over the trailing ``days``
    window (``LocalStore.query_efficiency_rollup`` shape):
    ``{runtime, model, tokens_in, tokens_out, cache_read, cache_write,
    cost_usd, calls, days_with_data}``. Returns the node-wide grade plus a
    ``byRuntime`` map of the same shape (minus ``byRuntime``) — per-runtime
    honesty is built in, never a node-wide number relabelled.

    Pure; never raises. Garbage rows / fields coerce to zeros; empty input
    returns the honest ``insufficient_data`` shape.
    """
    try:
        days_i = int(days)
    except (TypeError, ValueError):
        days_i = 30
    if days_i <= 0:
        days_i = 30
    try:
        clean: list[dict[str, Any]] = []
        for row in (rows or []):
            c = _coerce_row(row)
            if c is not None:
                clean.append(c)
        out = _build_scope(clean, days_i)
        by_runtime: dict[str, dict[str, Any]] = {}
        if clean:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for r in clean:
                grouped.setdefault(r["runtime"], []).append(r)
            for rt, rt_rows in grouped.items():
                by_runtime[rt] = _build_scope(rt_rows, days_i)
        out["byRuntime"] = by_runtime
        return out
    except Exception as exc:  # pragma: no cover - defensive, never-crash rule
        log.warning("efficiency: slice build failed (%s); returning empty", exc)
        empty = _empty_scope(days_i)
        empty["byRuntime"] = {}
        return empty
