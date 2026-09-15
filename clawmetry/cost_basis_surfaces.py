"""Financial-basis entries for the cost surfaces #5975 did not reach.

vivekchand/clawmetry#5937, REQ-OBS-CEA-025 (AC-OBS-CEA-025.8 and .9).

``clawmetry/cost_basis.py`` defines the vocabulary. This module applies it to
the remaining dollar figures on the Usage tab (Where the money goes, the
efficiency and cache cards, Cost Forecast, Cost Comparison, Spend
Optimization, Cache Re-read Tax, compression potential, Cost By Plugin /
Skill, Skill Cost Leaderboard, Cost by Team) and to the per-message cost a
Sessions transcript carries.

Every figure here is **usage value at published rates**: recorded token
counts priced at a provider's list price, or the runtime's own per-call cost,
which runtimes compute from published rates too. None is a bill, so none may
claim ``contract`` or ``allocated_actual``.

What varies is the arithmetic basis beside it:

* a sum of recorded per-call cost over a window is ``derived``;
* anything that assumes something unobserved is ``estimated``: a monthly
  projection from a trailing window, a saving on a model nobody ran, a
  session's cost split evenly across the skills it read, a category share
  apportioned by token counts.

The entries are built once per surface, here, so the local route and the
hosted snapshot slice that reuses the same builder carry identical words
(FLYWHEEL.md 0a, cloud parity). Each ``*_entries`` function returns a mapping
ready for :func:`clawmetry.provenance.stamp`; :func:`stamp` applies one and
never raises, because a labelling bug must not take a card down.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from clawmetry import cost_basis as _cb
from clawmetry import provenance as _prov

Entries = Dict[str, Dict[str, Any]]


def _pub(formula: str, source: str, *, basis: str = _prov.DERIVED,
         **kw: Any) -> Dict[str, Any]:
    return _cb.published_rate(formula, source, basis=basis, **kw)


def stamp(payload: Any, entries: Mapping[str, Mapping[str, Any]]) -> Any:
    """Attach ``entries`` to a dict payload. Never raises."""
    try:
        if isinstance(payload, dict):
            _prov.stamp(payload, entries)
    except Exception:  # pragma: no cover - never-crash rule
        pass
    return payload


# ── Efficiency grade, cache hit rate, savings ideas, routing advisor ────────

_EFF_SRC = "DuckDB rollup_model_daily on this node (clawmetry/efficiency.py)"


def efficiency_entries(days: int) -> Entries:
    window = "the last %d days, scaled to 30 days" % int(days or 30)
    return {
        "projected_monthly_cost_usd": _pub(
            "the recorded cost of the window divided by its days with data, "
            "times 30. It assumes the next month looks like this window",
            _EFF_SRC, basis=_prov.ESTIMATED, window=window),
        "cache_saved_monthly_usd": _pub(
            "cached-read tokens times the gap between the model's input rate "
            "and its cache-read rate, scaled to a month. It assumes the "
            "window's cache use continues",
            _EFF_SRC, basis=_prov.ESTIMATED, window=window),
        "left_on_table_monthly_usd": _pub(
            "the projected monthly input cost times the share of input that "
            "was not a cache hit, times an assumed 50% of it being cacheable, "
            "times the cache-read discount",
            _EFF_SRC, basis=_prov.ESTIMATED, window=window),
        "metrics.window_cost_usd": _pub(
            "sum of the recorded per-call cost over the window",
            _EFF_SRC, window="the last %d days" % int(days or 30)),
        "actions[].savings_monthly_usd": _pub(
            "what the window would have cost after the suggested change, "
            "subtracted from what it did cost, scaled to a month and capped "
            "at 90% of projected spend. It assumes the change keeps the "
            "results the same, which is the part that can be wrong",
            _EFF_SRC, basis=_prov.ESTIMATED, window=window),
        "actions[].data.window_cost_usd": _pub(
            "sum of the recorded per-call cost for this model over the window",
            _EFF_SRC, window="the last %d days" % int(days or 30)),
        "actions[].data.target_window_cost_usd": _pub(
            "the same token counts priced at the suggested model's published "
            "rates", _EFF_SRC, basis=_prov.ESTIMATED),
        "actions[].data.input_side_window_cost_usd": _pub(
            "the input-token share of the window's recorded cost", _EFF_SRC),
        "actions[].data.wasted_window_usd": _pub(
            "cache writes that expired unread, priced at the write rate",
            _EFF_SRC, basis=_prov.ESTIMATED),
        "actions[].data.thinking_window_cost_usd": _pub(
            "the thinking-token share of output cost over the window",
            "clawmetry/spend_flow.py over the events table",
            basis=_prov.ESTIMATED),
    }


# ── Where the money goes (spend flow) ────────────────────────────────────────

_SF_SRC = "DuckDB events on this node (clawmetry/spend_flow.py)"


def spend_flow_entries(days: int) -> Entries:
    window = "the last %d days" % int(days or 7)
    split = _pub(
        "each call's recorded cost split between categories by their token "
        "share of that call. Token shares are measured from event content "
        "and the system-prompt share is the residual, so the split is an "
        "estimate even where the total is not",
        _SF_SRC, basis=_prov.ESTIMATED, window=window)
    whole = _pub("sum of the recorded per-call cost", _SF_SRC, window=window)
    return {
        "totals.cost_usd": whole,
        "totals.input_cost_usd": split,
        "totals.output_cost_usd": split,
        "runtimes[].cost_usd": whole,
        "runtimes[].input_cost_usd": split,
        "runtimes[].output_cost_usd": split,
        "input_categories[].cost_usd": split,
        "output_categories[].cost_usd": split,
        "links[].cost_usd": split,
    }


# ── Cost Forecast ────────────────────────────────────────────────────────────

_FC_SRC = "DuckDB daily rollups on this node"


def forecast_entries(*, spent_so_far: float, daily_rate: float,
                     days_remaining: int) -> Entries:
    return {
        "projected_month_usd": _pub(
            "spend so far this month, plus the average of the last 7 days "
            "times the days left. It assumes the rest of the month looks "
            "like the last week",
            _FC_SRC, basis=_prov.ESTIMATED, window="the calendar month",
            inputs={"spent_so_far_usd": round(spent_so_far, 4),
                    "daily_rate_usd": round(daily_rate, 4),
                    "days_remaining": days_remaining}),
        "cost_this_month_usd": _pub(
            "sum of the priced cost of every call this month", _FC_SRC,
            window="this month, the local calendar month from the 1st"),
        "daily_rate_usd": _pub(
            "the priced cost of the last 7 days divided by 7", _FC_SRC,
            window="the last 7 days"),
        # A limit the operator typed, not usage value. It keeps its own
        # arithmetic label and no financial basis, because it is not money
        # anybody spent.
        "monthly_budget_usd": _prov.measured(
            "the monthly limit you set", "clawmetry budget config"),
    }


# ── Cost Comparison ──────────────────────────────────────────────────────────

def cost_comparison_entries(source: str) -> Entries:
    window = "the last 30 days"
    return {
        "actual.cost_usd": _pub(
            "sum of the recorded per-call cost, with duplicate sibling rows "
            "of the same turn removed. It is usage value, not an invoice",
            source, window=window),
        "alternatives[].estimated_cost": _pub(
            "the same total tokens priced at the alternative's published "
            "rates, assuming 60% input and 40% output. The real split and "
            "the alternative's output length are not known",
            source, basis=_prov.ESTIMATED, window=window),
        "alternatives[].savings_usd": _pub(
            "recorded usage value minus the alternative's estimate, on the "
            "same assumptions", source, basis=_prov.ESTIMATED, window=window),
    }


# ── Spend Optimization ───────────────────────────────────────────────────────

def spend_optimization_entries(tools_analysed: int) -> Entries:
    saving = _pub(
        "the measured cost of these tool calls over the window, times the "
        "published price gap between the model they ran on and the cheaper "
        "tier suggested. It assumes the cheaper model would have produced an "
        "equivalent result, which is the part that can be wrong",
        "duckdb spans, priced with the static model-tier ratio table",
        basis=_prov.ESTIMATED, window="the last 30 days",
        inputs={"tools_analysed": tools_analysed})
    return {
        "total_projected_savings_usd_30d": saving,
        "recommendations[].projected_savings_usd_30d": saving,
        "total_analyzed_cost_usd_30d": _pub(
            "sum of the measured cost of the analysed tool calls",
            "duckdb spans", window="the last 30 days"),
        "recommendations[].current_cost_usd_30d": _pub(
            "sum of the measured cost of this tool's calls",
            "duckdb spans", window="the last 30 days"),
    }


def spend_optimization_unavailable() -> Entries:
    return {
        "total_projected_savings_usd_30d": _cb.unavailable(
            "no spans were available to analyse, so there is nothing to "
            "compare a cheaper tier against",
            source="/api/usage/optimization-recommendations"),
        "total_analyzed_cost_usd_30d": _cb.unavailable(
            "no spans were available to analyse",
            source="/api/usage/optimization-recommendations"),
    }


# ── Cache performance (cache trends) ─────────────────────────────────────────

def cache_trends_entries(source: str, days: int) -> Entries:
    window = "the last %d days" % int(days or 14)
    parts = _pub("recorded tokens of this kind priced at the model's "
                 "published rate", source, window=window)
    saved = _pub(
        "cache-read tokens times the gap between the model's input rate and "
        "its cache-read rate: what the same reads would have cost uncached",
        source, basis=_prov.ESTIMATED, window=window)
    out: Entries = {}
    for scope in ("totals.", "daily[].", "by_model[]."):
        for key in ("input_cost_usd", "output_cost_usd", "cache_read_cost_usd",
                    "cache_write_cost_usd", "total_cost_usd"):
            out[scope + key] = parts
        out[scope + "est_savings_usd"] = saved
    return out


# ── Cache Re-read Tax ────────────────────────────────────────────────────────

def cache_risk_entries(source: str) -> Entries:
    return {
        "total_write_cost_usd": _pub(
            "sum of each affected session's cache-write tokens priced at the "
            "model's published cache-write rate", source),
        "total_saved_usd": _pub(
            "sum of each affected session's cache-read tokens times the gap "
            "between the input rate and the cache-read rate",
            source, basis=_prov.ESTIMATED),
    }


# ── Compression potential ────────────────────────────────────────────────────

def compression_entries(source: str) -> Entries:
    return {
        "recoverable_usd": _pub(
            "compressible tool-output tokens in qualifying sessions priced at "
            "the session model's input rate. It assumes the output could be "
            "summarised without losing what the agent needed",
            source, basis=_prov.ESTIMATED),
    }


# ── Cost By Plugin / Skill, Skill Cost Leaderboard, Cost by Team ─────────────

def by_plugin_entries(source: str) -> Entries:
    return {
        "plugins[].cost_usd": _pub(
            "sum of the recorded cost of the events attributed to this "
            "plugin or tool", source),
    }


def skill_attribution_entries(source: str) -> Entries:
    split = _pub(
        "each session's recorded cost split evenly between the skills it "
        "read. A session that read two skills gives each half, whatever each "
        "actually drove", source, basis=_prov.ESTIMATED)
    return {
        "skills[].total_cost_usd": split,
        "skills[].avg_cost_usd": split,
        "top5_week[].total_cost_usd": split,
        "top5_week[].avg_cost_usd": split,
        "total_cost": split,
    }


def by_team_entries(window_days: int) -> Entries:
    return {
        "teams[].cost_usd": _pub(
            "sum of the recorded cost of each session, grouped by the team "
            "label mapped to its runtime",
            "DuckDB rollup_session and team_mapping",
            window="the last %d days" % int(window_days or 7)),
    }


# ── Sessions transcript: per-message cost, summed per turn in the browser ───

def transcript_entries(source: str) -> Entries:
    return {
        "messages[].cost_usd": _pub(
            "the recorded cost of the event this message came from. A turn's "
            "cost is the sum of its messages", source),
    }
