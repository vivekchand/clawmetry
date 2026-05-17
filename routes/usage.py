"""
routes/usage.py — Usage / analytics / anomaly / attribution endpoints.

Extracted from dashboard.py as Phase 5.3 of the incremental modularisation.
Owns the 12 routes registered on bp_usage:

  GET  /api/usage                         — headline token/cost tracker
  GET  /api/usage/anomalies               — cost anomaly summary
  GET  /api/anomalies                     — rolling-baseline detector output
  POST /api/anomalies/<id>/ack            — acknowledge an anomaly
  GET  /api/usage/by-plugin               — plugin token/cost breakdown
  GET  /api/usage/by-plugin/trend         — plugin breakdown over time
  GET  /api/sessions/clusters             — behavioural session clustering
  GET  /api/usage/cost-comparison         — alt-model savings estimate
  GET  /api/usage/export                  — CSV export of usage
  GET  /api/model-attribution             — per-model turn/session split
  GET  /api/skill-attribution             — per-skill cost attribution
  GET  /api/token-velocity                — runaway-loop detection
  GET  /api/usage/cache-trends            — prompt-cache hit-rate analytics
  GET  /api/skills/fidelity              — dead-skill detector + body/linked-file stats

Module-level helpers (``_usage_cache``, ``_compute_transcript_analytics``,
``_detect_and_store_anomalies``, ``_get_anomaly_db``, ``SESSIONS_DIR`` etc.)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.
Pure mechanical move — zero behaviour change.
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, make_response, request
from clawmetry.config import is_local_store_read_enabled
from routes._dedupe import build_sibling_bucket_max, is_sibling_dup

bp_usage = Blueprint('usage', __name__)

_CLUSTER_CACHE = {"ts": 0.0, "key": None, "data": None}
_CLUSTER_CACHE_TTL_SECONDS = 120


# ────────────────────────────────────────────────────────────────────────────
# Epic #964 — DuckDB local-store fast paths for the Usage tab.
#
# Each helper below is the FIRST path tried by its sibling Flask route when
# CLAWMETRY_LOCAL_STORE_READ=1. They return ``None`` on any failure (import
# error, empty store, query crash, unknown shape) so the caller can fall
# straight through to the legacy JSONL/gateway/OTLP path with no behaviour
# change. Successful returns carry ``_source: "local_store"`` so callers (and
# tests) can verify which path served the request.
#
# Source data:
#   * events table — one row per tool call / message / spend event, written
#     by sync.py + the daemon. Columns: id, agent_type, node_id, agent_id,
#     session_id, event_type, ts (ISO), data (JSON BLOB), cost_usd,
#     token_count, model.
#   * daily_aggregates / sessions tables — pre-rolled summaries, populated
#     in parallel for cheap queries.
# ────────────────────────────────────────────────────────────────────────────


class _DaemonProxyStore:
    """Drop-in shim that mimics the LocalStore .query_* API by forwarding
    each call through ``local_store_via_daemon``. Used so the 7 callers in
    this module that do ``store = _ls_get_store(); store.query_X(...)``
    don't each need their own daemon-proxy plumbing.

    Issue #1291 cliff #3: a writable ``get_store()`` collided with the
    sync daemon's exclusive DuckDB lock — the entire usage module was
    silently falling through to the legacy sqlite scanners (the 6.6s p95
    the latency probe surfaced for ``usage.api_anomalies``).
    """
    def __getattr__(self, method_name):
        # Only proxy ``query_*`` methods (the read-side surface).
        if not method_name.startswith("query_"):
            raise AttributeError(method_name)
        from routes.local_query import local_store_via_daemon

        def _call(**kwargs):
            return local_store_via_daemon(method_name, **kwargs)
        return _call


def _ls_get_store():
    """Return a store-like object backed by the daemon HTTP proxy when
    the daemon is reachable; fall back to a single-process direct open
    for tests/dev mode where no daemon is running.

    Returns ``None`` if neither path is available.
    """
    # Prefer the daemon proxy under standard installs (daemon owns the
    # writer lock; direct opens fail with IOException).
    try:
        from routes.local_query import _cached_discovery
        if _cached_discovery():
            return _DaemonProxyStore()
    except Exception:
        pass
    # Single-process fallback (tests / dev mode without a sync daemon).
    try:
        from clawmetry import local_store
        return local_store.get_store(read_only=True)
    except Exception:
        return None


def _ls_iso_day(ts_str):
    """Pull YYYY-MM-DD off an ISO timestamp. Tolerates None / short strings."""
    if not ts_str or not isinstance(ts_str, str) or len(ts_str) < 10:
        return ""
    return ts_str[:10]


def _ls_event_plugin(ev):
    """Best-effort plugin/tool name extractor from an events-row data blob.

    Plugins are recorded under several historical keys depending on the
    writer (gateway, claude-cli adapter, sync.py): ``plugin``, ``tool``,
    ``tool_name``, ``name``. We try them in order and fall back to the
    event_type itself.
    """
    data = ev.get("data") if isinstance(ev, dict) else None
    if isinstance(data, dict):
        for k in ("plugin", "tool", "tool_name", "name"):
            v = data.get(k)
            if v and isinstance(v, str):
                return v
    et = (ev.get("event_type") or "").strip()
    return et or "unknown"


def _ls_event_skill(ev):
    """Pull a skill name out of an event's data blob, if any. Returns the
    bare skill name (e.g. ``review``) or ``None`` when no skill is named."""
    data = ev.get("data") if isinstance(ev, dict) else None
    if not isinstance(data, dict):
        return None
    for k in ("skill", "skill_name"):
        v = data.get(k)
        if v and isinstance(v, str):
            return v
    # Detect SKILL.md path references in input/file_path/path keys.
    for k in ("file_path", "path", "input"):
        v = data.get(k)
        if isinstance(v, str) and "SKILL.md" in v.upper():
            # Pull the parent dir name as the skill identifier.
            import re as _re
            m = _re.search(r"[/\\]([^/\\]+)[/\\]SKILL\.md", v, _re.IGNORECASE)
            if m:
                return m.group(1)
    return None


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Issue #1088: every direct ``get_store().query_*`` call is dead code in
    the standard install (daemon owns the writer lock, dashboard's open
    raises ``IOException: Could not set lock``). This wrapper hits the
    daemon's HTTP proxy first, then falls back to direct open for
    single-process boots (tests + dev mode).
    """
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    store = _ls_get_store()
    if store is None:
        return None
    try:
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _try_local_store_usage():
    """Fast path for /api/usage. Builds the daily token/cost chart by
    aggregating ``daily_aggregates`` (with a ``query_events`` fallback if
    the aggregates table is empty). Returns the same shape as the legacy
    handler: days[], today/week/month, todayCost/weekCost/monthCost,
    modelBreakdown, etc. Returns None to defer.

    Issue #1394: the fast-path used to set every per-day input/output/
    cache_read/cache_write split to 0 because ``query_aggregates`` only
    returns the coarse SUM(token_count) column. We now also call
    ``query_daily_usage_splits``, which walks each ``assistant`` /
    ``model.completed`` event blob and pulls the v3 Anthropic-SDK
    cache-token keys (``cache_read_input_tokens`` /
    ``cache_creation_input_tokens``) so the Tokens tab actually shows
    the breakdown on real OpenClaw installs.
    """
    # Pull pre-rolled day buckets first — these are the "blessed" data
    # the daemon writes once per ingest. Falls back to live event scan
    # when aggregates are empty (e.g. fresh install, only events seeded).
    agg_rows = _ls_call("query_aggregates")
    if agg_rows is None:
        return None
    daily_tokens = {}
    daily_cost = {}
    if agg_rows:
        for r in agg_rows:
            day = r.get("day") or ""
            if not day:
                continue
            daily_tokens[day] = daily_tokens.get(day, 0) + int(r.get("token_count") or 0)
            daily_cost[day] = daily_cost.get(day, 0.0) + float(r.get("cost_usd") or 0.0)
    else:
        evs = _ls_call("query_events", limit=10000)
        if not evs:
            return None
        for ev in evs:
            day = _ls_iso_day(ev.get("ts", ""))
            if not day:
                continue
            daily_tokens[day] = daily_tokens.get(day, 0) + int(ev.get("token_count") or 0)
            daily_cost[day] = daily_cost.get(day, 0.0) + float(ev.get("cost_usd") or 0.0)

    # Issue #1394: per-day input/output/cache_read/cache_write split. We
    # build this from the assistant-event blob walker so we don't have
    # to wait for the daemon to backfill split columns. Empty list is
    # fine (caller renders zeros for the missing days).
    splits_rows = _ls_call("query_daily_usage_splits") or []
    daily_input = {r["day"]: int(r.get("input_tokens") or 0) for r in splits_rows}
    daily_output = {r["day"]: int(r.get("output_tokens") or 0) for r in splits_rows}
    daily_cache_read = {r["day"]: int(r.get("cache_read_tokens") or 0) for r in splits_rows}
    daily_cache_write = {r["day"]: int(r.get("cache_write_tokens") or 0) for r in splits_rows}
    # Also fill in cost from splits_rows when query_aggregates' cost_usd
    # column was empty for that day (real-data common case — sync.py
    # only stamps cost_usd when ``usage.cost.total`` is present at
    # ingest time, which Anthropic-SDK echo events omit).
    for r in splits_rows:
        d = r["day"]
        cost_from_split = float(r.get("cost_usd") or 0.0)
        if cost_from_split > 0 and daily_cost.get(d, 0.0) <= 0:
            daily_cost[d] = cost_from_split

    # Issue #1394 + MOAT regression 2026-05-16: raw ``token_count`` aggregate
    # counts BOTH the ``assistant`` and the sibling ``model.completed`` event
    # for each LLM turn (different writers race ~100-300ms apart) AND any
    # non-billable-turn rows with a token_count column (tool_call rows in
    # synthetic harnesses, retries, etc.). The splits walker dedupes the
    # sibling pair but ignores non-message rows entirely, so blindly
    # overwriting raw with deduped silently drops those tokens.
    #
    # Decision: if raw >= 2*deduped, the sibling-doubling bug dominates →
    # subtract the doubled half and add any residual non-message tokens
    # back on top. If raw < 2*deduped, no full sibling pair exists for that
    # day (synthetic / partial install) → keep whichever is larger so we
    # don't lose data either way.
    for d in set(list(daily_input.keys()) + list(daily_output.keys())):
        deduped_total = int(daily_input.get(d, 0)) + int(daily_output.get(d, 0))
        if deduped_total <= 0:
            continue
        raw_total = int(daily_tokens.get(d, 0))
        sibling_doubled = 2 * deduped_total
        if raw_total >= sibling_doubled:
            non_msg = raw_total - sibling_doubled
            daily_tokens[d] = deduped_total + non_msg
        else:
            daily_tokens[d] = max(raw_total, deduped_total)

    if (
        not daily_tokens and not daily_cost
        and not daily_input and not daily_output
        and not daily_cache_read and not daily_cache_write
    ):
        return None

    today = datetime.now()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append({
            "date": ds,
            "tokens": int(daily_tokens.get(ds, 0)),
            "cost": round(float(daily_cost.get(ds, 0.0)), 6),
            "inputTokens": int(daily_input.get(ds, 0)),
            "outputTokens": int(daily_output.get(ds, 0)),
            "cacheReadTokens": int(daily_cache_read.get(ds, 0)),
            "cacheWriteTokens": int(daily_cache_write.get(ds, 0)),
        })

    today_str = today.strftime("%Y-%m-%d")
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    month_start = today.strftime("%Y-%m-01")

    today_tok = int(daily_tokens.get(today_str, 0))
    week_tok = int(sum(v for k, v in daily_tokens.items() if k >= week_start))
    month_tok = int(sum(v for k, v in daily_tokens.items() if k >= month_start))
    today_cost = float(daily_cost.get(today_str, 0.0))
    week_cost = float(sum(v for k, v in daily_cost.items() if k >= week_start))
    month_cost = float(sum(v for k, v in daily_cost.items() if k >= month_start))

    # Per-model breakdown: scan recent events and group.
    model_usage = {}
    recent = _ls_call("query_events", limit=5000) or []
    for ev in recent:
        m = ev.get("model") or "unknown"
        model_usage[m] = model_usage.get(m, 0) + int(ev.get("token_count") or 0)
    model_breakdown = [
        {"model": k, "tokens": v}
        for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
        if v > 0
    ]

    return {
        "source": "local_store",
        "_source": "local_store",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "todayCost": round(today_cost, 4),
        "weekCost": round(week_cost, 4),
        "monthCost": round(month_cost, 4),
        "modelBreakdown": model_breakdown,
        "modelBilling": [],
        "billingSummary": {},
        "sessionCosts": {},
        "sessions": _ls_top_sessions_by_cost(limit=20),
        "anomalies": [],
        "anomalySessionIds": [],
        "trend": {},
        "warnings": [],
    }


def _ls_top_sessions_by_cost(limit=20):
    """Issue #68 — top-N sessions by total cost. Sources rows from the
    DuckDB ``events`` table aggregated per session, joined back to a
    sample event for the model column. Returns ``[]`` on any failure so
    the caller can drop the key silently."""
    try:
        sessions = _ls_call("query_sessions", limit=500)
    except Exception:
        sessions = None
    if not sessions:
        return []
    # Sort by cost desc and take top-N before the model lookup so we
    # avoid scanning events for hundreds of cheap sessions.
    ranked = sorted(
        sessions,
        key=lambda s: float(s.get("cost_usd") or 0.0),
        reverse=True,
    )[: max(1, int(limit))]
    out = []
    for s in ranked:
        sid = s.get("session_id") or ""
        if not sid:
            continue
        # Pull the most recent event for this session to grab the model
        # column. ``query_events`` returns rows newest-first.
        model = ""
        try:
            evs = _ls_call("query_events", session_id=sid, limit=1) or []
            if evs:
                model = evs[0].get("model") or ""
        except Exception:
            model = ""
        out.append({
            "session_id":      sid,
            "agent_id":        s.get("agent_id") or "",
            "model":           model,
            "total_tokens":    int(s.get("token_count") or 0),
            "total_cost_usd":  round(float(s.get("cost_usd") or 0.0), 6),
            "message_count":   int(s.get("event_count") or 0),
            "started_at":      s.get("started_at") or "",
        })
    return out


def _ls_compute_anomalies():
    """Shared rolling-baseline anomaly detection over events. Used by both
    /api/usage/anomalies and /api/anomalies. Buckets recent (24h) sessions
    and flags any whose cost exceeds 2x the 7-day rolling session-cost
    baseline. Returns ``(anomalies, baseline_avg)`` or ``(None, None)`` to
    defer."""
    store = _ls_get_store()
    if store is None:
        return None, None
    try:
        sessions = store.query_sessions(limit=500)
    except Exception:
        return None, None
    if not sessions:
        return None, None

    # Convert ISO start timestamps to epoch.
    def _to_epoch(s):
        if not s:
            return 0.0
        try:
            from datetime import datetime as _dt
            return _dt.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    enriched = []
    for s in sessions:
        enriched.append({
            "session_id": s.get("session_id"),
            "cost_usd": float(s.get("cost_usd") or 0.0),
            "start_ts": _to_epoch(s.get("started_at")),
        })

    now_ts = time.time()
    day_ago = now_ts - 86400
    week_ago = now_ts - 7 * 86400
    anomalies = []

    # Sort by start_ts ascending so the rolling-baseline window is well-defined.
    enriched.sort(key=lambda r: r["start_ts"])
    for i, sess in enumerate(enriched):
        ts = sess["start_ts"]
        if ts < day_ago:
            continue
        cost = sess["cost_usd"]
        if cost <= 0:
            continue
        window_start = ts - (7 * 86400)
        window_costs = [
            p["cost_usd"] for p in enriched[:i]
            if p["start_ts"] >= window_start and p["start_ts"] < ts and p["cost_usd"] > 0
        ]
        if not window_costs:
            continue
        avg = sum(window_costs) / float(len(window_costs))
        if avg <= 0:
            continue
        if cost > (2.0 * avg):
            anomalies.append({
                "session_id": sess["session_id"],
                "cost_usd": round(cost, 6),
                "rolling_avg_usd": round(avg, 6),
                "ratio": round(cost / avg, 3),
                "timestamp": int(ts * 1000),
            })

    anomalies.sort(key=lambda a: a.get("ratio", 0), reverse=True)
    baseline_costs = [s["cost_usd"] for s in enriched
                      if s["start_ts"] >= week_ago and s["cost_usd"] > 0]
    baseline_avg = (sum(baseline_costs) / float(len(baseline_costs))) if baseline_costs else 0.0
    return anomalies, baseline_avg


def _try_local_store_usage_anomalies():
    """Fast path for /api/usage/anomalies."""
    anomalies, baseline_avg = _ls_compute_anomalies()
    if anomalies is None:
        return None
    return {
        "anomalies": anomalies,
        "baseline_7d_avg_usd": round(baseline_avg or 0.0, 6),
        "threshold_multiplier": 2.0,
        "_source": "local_store",
    }


def _try_local_store_anomalies():
    """Fast path for /api/anomalies. The legacy handler stores acks in a
    sqlite db so we mirror its empty/no-ack defaults."""
    anomalies, baseline_avg = _ls_compute_anomalies()
    if anomalies is None:
        return None
    # Match the legacy response shape (anomaly id + ack + severity), even
    # though we can't persist acks in the local store yet — those need the
    # ~/.openclaw/clawmetry.db that the legacy detector owns.
    out = []
    for i, a in enumerate(anomalies):
        ratio = float(a.get("ratio") or 0)
        sev = "critical" if ratio >= 4.0 else ("high" if ratio >= 3.0 else "medium")
        out.append({
            "id": i + 1,
            "session_key": a.get("session_id"),
            "metric": "cost_spike",
            "value": a.get("cost_usd"),
            "baseline": a.get("rolling_avg_usd"),
            "ratio": ratio,
            "severity": sev,
            "detected_at": (a.get("timestamp") or 0) / 1000.0,
            "acknowledged": False,
        })
    active = [a for a in out if not a.get("acknowledged")]
    return {
        "anomalies": out,
        "active_count": len(active),
        "has_active": bool(active),
        "baselines": {"cost_7d_avg_usd": round(baseline_avg or 0.0, 6)},
        "threshold_cost_multiplier": 2.0,
        "threshold_token_multiplier": 2.0,
        "threshold_error_multiplier": 3.0,
        "_source": "local_store",
    }


def _try_local_store_usage_by_plugin(threshold_pct):
    """Fast path for /api/usage/by-plugin. Groups events by plugin/tool
    name, splits each event's tokens/cost across the plugins implicated.
    Returns shape: {plugins: [...], warnings: [...]}."""
    store = _ls_get_store()
    if store is None:
        return None
    try:
        evs = store.query_events(limit=20000)
    except Exception:
        return None
    if not evs:
        return None
    # Issue #1451: sibling-dedupe so v3 assistant + model.completed pairs
    # don't double-count per-plugin tokens.
    bucket_max = build_sibling_bucket_max(evs)
    plugin_stats = defaultdict(lambda: {"tokens": 0.0, "cost": 0.0, "calls": 0})
    saw_any = False
    for ev in evs:
        plugin = _ls_event_plugin(ev)
        if not plugin:
            continue
        if is_sibling_dup(ev, bucket_max):
            continue
        saw_any = True
        plugin_stats[plugin]["tokens"] += float(ev.get("token_count") or 0)
        plugin_stats[plugin]["cost"] += float(ev.get("cost_usd") or 0.0)
        plugin_stats[plugin]["calls"] += 1
    if not saw_any:
        return None
    total_tokens = sum(s["tokens"] for s in plugin_stats.values()) or 1.0
    rows = []
    warnings = []
    for plugin, st in plugin_stats.items():
        toks = st["tokens"]
        cost = st["cost"]
        calls = st["calls"]
        pct = round((toks / total_tokens) * 100.0, 2)
        rows.append({
            "plugin": plugin,
            "total_tokens": int(round(toks)),
            "cost_usd": round(cost, 6),
            "call_count": calls,
            "pct_of_total": pct,
            "trend": "flat",
        })
        if pct >= threshold_pct:
            warnings.append({
                "plugin": plugin,
                "pct_of_total": pct,
                "message": f"{plugin} accounts for {pct:.1f}% of total token usage "
                           f"(threshold: {threshold_pct:.0f}%)",
                "trend": "flat",
            })
    rows.sort(key=lambda r: r["total_tokens"], reverse=True)
    return {"plugins": rows, "warnings": warnings, "_source": "local_store"}


def _try_local_store_usage_by_plugin_trend(days_back):
    """Fast path for /api/usage/by-plugin/trend. Builds a per-day plugin
    breakdown from events. Same shape as the legacy handler:
      {days: [...], plugins: {name: [{day, tokens, cost_usd, calls}, ...]}}.
    """
    store = _ls_get_store()
    if store is None:
        return None
    try:
        evs = store.query_events(limit=20000)
    except Exception:
        return None
    if not evs:
        return None
    from datetime import date as _date
    today = _date.today()
    day_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(days_back - 1, -1, -1)]
    day_set = set(day_list)
    # Issue #1451: sibling-dedupe so v3 assistant + model.completed pairs
    # don't double-count per-plugin daily totals.
    bucket_max = build_sibling_bucket_max(evs)
    # plugin -> day -> stats
    plugin_daily: dict = defaultdict(lambda: defaultdict(
        lambda: {"tokens": 0.0, "cost": 0.0, "calls": 0}
    ))
    saw_any = False
    for ev in evs:
        day = _ls_iso_day(ev.get("ts", ""))
        if day not in day_set:
            continue
        plugin = _ls_event_plugin(ev)
        if not plugin:
            continue
        if is_sibling_dup(ev, bucket_max):
            continue
        saw_any = True
        bucket = plugin_daily[plugin][day]
        bucket["tokens"] += float(ev.get("token_count") or 0)
        bucket["cost"] += float(ev.get("cost_usd") or 0.0)
        bucket["calls"] += 1
    if not saw_any:
        return None
    result = {}
    for p in sorted(plugin_daily.keys()):
        series = []
        for d in day_list:
            day_data = plugin_daily[p].get(d, {"tokens": 0.0, "cost": 0.0, "calls": 0})
            series.append({
                "day": d,
                "tokens": int(round(day_data["tokens"])),
                "cost_usd": round(day_data["cost"], 6),
                "calls": day_data["calls"],
            })
        result[p] = series
    return {"days": day_list, "plugins": result, "_source": "local_store"}


def _try_local_store_cost_comparison():
    """Fast path for /api/usage/cost-comparison. Sums actual tokens/cost
    over the past 30 days from the local store, then projects costs against
    a fixed alternatives table. Mirrors ``dashboard._build_cost_comparison``
    output shape exactly.

    MOAT 2026-05-16: the old implementation blindly summed ``token_count``
    across every event row. On real v3 installs the dual-writer pattern
    (``assistant`` + sibling ``model.completed``) double-counts every
    billable turn, inflating ``actual.tokens`` + ``actual.cost_usd`` ~2×
    and making the "savings vs alternative" dollar amounts look twice as
    big as truth. We now skip the slimmer ``model.completed`` row when an
    ``assistant``/``message`` sibling exists for the same
    (session_id, ts ±1 s) bucket — matches the dedup approach in
    ``query_daily_usage_splits``. Non-billable-turn rows (tool_call etc.)
    keep their tokens since they don't have a sibling.
    """
    store = _ls_get_store()
    if store is None:
        return None
    try:
        evs = store.query_events(limit=50000)
    except Exception:
        return None
    if not evs:
        return None

    # Window: last 30 days.
    cutoff = datetime.now() - timedelta(days=30)
    cutoff_iso = cutoff.strftime("%Y-%m-%d")

    # Sibling-dedup (issue #1451 / PR #1446): per (session_id, ts_sec, ±1 s)
    # bucket, keep only the richest-envelope row. ``assistant``/``message``
    # outrank ``model.completed`` for the same turn (writer race emits both
    # ~100 ms apart). Helper in ``routes/_dedupe.py``.
    in_window = [ev for ev in evs if (ev.get("ts", "") or "") >= cutoff_iso]
    bucket_max = build_sibling_bucket_max(in_window)

    actual_tokens = 0
    actual_cost = 0.0
    model_token_map: dict = {}
    saw_any = False
    for ev in in_window:
        if is_sibling_dup(ev, bucket_max):
            continue
        saw_any = True
        tok = int(ev.get("token_count") or 0)
        actual_tokens += tok
        actual_cost += float(ev.get("cost_usd") or 0.0)
        m = ev.get("model") or ""
        if m:
            model_token_map[m] = model_token_map.get(m, 0) + tok
    if not saw_any:
        return None

    actual_model = (max(model_token_map, key=lambda k: model_token_map[k])
                    if model_token_map else "unknown")

    ALTERNATIVES = [
        ("gemini-2.0-flash",   0.10,  0.40,  "Gemini 2.0 Flash",     "Google"),
        ("gemini-1.5-flash",   0.075, 0.30,  "Gemini 1.5 Flash",     "Google"),
        ("gpt-4o-mini",        0.15,  0.60,  "GPT-4o Mini",          "OpenAI"),
        ("claude-haiku-3.5",   0.80,  4.00,  "Claude Haiku 3.5",     "Anthropic"),
        ("qwen-plus",          0.40,  1.20,  "Qwen Plus",            "Alibaba"),
        ("claude-sonnet-3.5",  3.00, 15.00,  "Claude Sonnet 3.5",    "Anthropic"),
        ("claude-opus-4",     15.00, 75.00,  "Claude Opus 4",        "Anthropic"),
    ]
    INPUT_RATIO = 0.60
    OUTPUT_RATIO = 0.40
    alternatives = []
    for alt_id, in_price, out_price, display_name, provider in ALTERNATIVES:
        if actual_tokens == 0:
            alt_cost = 0.0
        else:
            alt_cost = (
                actual_tokens * INPUT_RATIO * (in_price / 1_000_000)
                + actual_tokens * OUTPUT_RATIO * (out_price / 1_000_000)
            )
        if actual_cost > 0:
            savings_pct = round((actual_cost - alt_cost) / actual_cost * 100, 1)
            savings_usd = round(actual_cost - alt_cost, 4)
        else:
            savings_pct = 0.0
            savings_usd = 0.0
        alternatives.append({
            "model_id": alt_id,
            "display_name": display_name,
            "provider": provider,
            "estimated_cost": round(alt_cost, 4),
            "savings_usd": savings_usd,
            "savings_pct": savings_pct,
        })
    alternatives.sort(key=lambda x: x["estimated_cost"])
    return {
        "actual": {
            "model": actual_model,
            "tokens": actual_tokens,
            "cost_usd": round(actual_cost, 4),
        },
        "alternatives": alternatives,
        "period": "30d",
        "_source": "local_store",
    }


def _try_local_store_model_attribution():
    """Fast path for /api/model-attribution. Per-model assistant turn count,
    session count, provider tag, and share %. Switches list is best-effort
    — derived from per-session model variation."""
    store = _ls_get_store()
    if store is None:
        return None
    try:
        evs = store.query_events(limit=20000)
    except Exception:
        return None
    if not evs:
        return None
    try:
        import dashboard as _d
        provider_fn = getattr(_d, "_provider_from_model", None)
    except Exception:
        provider_fn = None

    model_turns: dict = {}
    sess_models: dict = defaultdict(list)
    saw_any = False
    # Iterate oldest-first within each session so we can track switches.
    evs_sorted = sorted(evs, key=lambda e: (e.get("session_id") or "", e.get("ts") or ""))
    for ev in evs_sorted:
        m = (ev.get("model") or "").strip()
        if not m:
            continue
        saw_any = True
        # Each event is a turn for the purposes of attribution.
        model_turns[m] = model_turns.get(m, 0) + 1
        sid = ev.get("session_id") or ""
        if sid:
            if not sess_models[sid] or sess_models[sid][-1] != m:
                sess_models[sid].append(m)
    if not saw_any:
        return None
    model_sessions: dict = {}
    switches = []
    for sid, mlist in sess_models.items():
        primary = mlist[0]
        model_sessions[primary] = model_sessions.get(primary, 0) + 1
        for prev, nxt in zip(mlist, mlist[1:]):
            switches.append({"session": sid, "from_model": prev, "to_model": nxt})

    total_turns = sum(model_turns.values())
    sorted_models = sorted(model_turns.items(), key=lambda x: -x[1])
    primary_model = sorted_models[0][0] if sorted_models else ""
    models_out = []
    for m, turns in sorted_models:
        provider = ""
        if provider_fn:
            try:
                provider = provider_fn(m) or ""
            except Exception:
                provider = ""
        models_out.append({
            "model": m,
            "turns": turns,
            "sessions": model_sessions.get(m, 0),
            "provider": provider,
            "share_pct": round(turns / total_turns * 100, 2) if total_turns else 0,
        })
    return {
        "models": models_out,
        "primary_model": primary_model,
        "total_turns": total_turns,
        "model_count": len(model_turns),
        "switches": switches[:50],
        "switch_count": len(switches),
        "_source": "local_store",
    }


def _try_local_store_skill_attribution():
    """Fast path for /api/skill-attribution. Detects skill invocations from
    events whose data blob mentions a skill (``skill`` key or ``SKILL.md``
    path), then attributes per-session token cost to those skills with even
    sharing when multiple skills appear in one session."""
    store = _ls_get_store()
    if store is None:
        return None
    try:
        evs = store.query_events(limit=50000)
    except Exception:
        return None
    if not evs:
        return None

    # Group by session.
    sess_skills: dict = defaultdict(set)
    sess_cost: dict = defaultdict(float)
    sess_last_ts: dict = {}
    saw_any = False
    for ev in evs:
        sid = ev.get("session_id") or ""
        if not sid:
            continue
        skill = _ls_event_skill(ev)
        if skill:
            sess_skills[sid].add(skill)
            saw_any = True
        sess_cost[sid] += float(ev.get("cost_usd") or 0.0)
        ts = ev.get("ts") or ""
        if ts and ts > (sess_last_ts.get(sid) or ""):
            sess_last_ts[sid] = ts
    if not saw_any:
        return None

    skill_stats: dict = defaultdict(lambda: {"invocations": 0, "total_cost": 0.0,
                                              "last_used_ts": ""})
    for sid, skills in sess_skills.items():
        if not skills:
            continue
        share = sess_cost.get(sid, 0.0) / len(skills)
        last_ts = sess_last_ts.get(sid, "")
        for skill in skills:
            st = skill_stats[skill]
            st["invocations"] += 1
            st["total_cost"] += share
            if last_ts > st["last_used_ts"]:
                st["last_used_ts"] = last_ts

    skills_out = []
    total_cost = 0.0
    for name, st in sorted(skill_stats.items(), key=lambda x: -x[1]["total_cost"]):
        inv = st["invocations"]
        tc = round(float(st["total_cost"]), 6)
        avg = round(tc / inv, 6) if inv else 0.0
        last_used = st["last_used_ts"] or None
        total_cost += tc
        skills_out.append({
            "name": name,
            "invocations": inv,
            "total_cost_usd": tc,
            "avg_cost_usd": avg,
            "last_used": last_used,
            "clawhub_url": f"https://clawhub.dev/skills/{name}",
        })

    # Top 5 by cost in the past 7 days (use the session last-used ts as proxy).
    week_cutoff_iso = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    top5_week = [s for s in skills_out
                 if s["last_used"] and s["last_used"] >= week_cutoff_iso][:5]

    return {
        "skills": skills_out,
        "top5_week": top5_week,
        "total_cost": round(total_cost, 6),
        "note": "Skills detected from events table in the local DuckDB store.",
        "clawhub": {"enabled": False, "url": None},
        "_source": "local_store",
    }


def _apply_oss_24h_cap(result):
    """Issue #1448 surface 2 — clamp /api/usage history to the last 24h for
    OSS / Cloud-Free callers. Cloud-Pro users (gated by
    ``dashboard._is_pro_user``) get the full 14-day chart.

    Returns a (possibly copied) result dict that always carries
    ``capped_at_24h`` so the UI can render the upsell row. Crucially this
    runs AFTER ``_usage_cache`` / fast-path dedupe (see
    ``feedback_usage_dedupe_pattern``) so cached aggregates are never
    double-truncated; we shallow-copy + rewrite ``days`` so the long-lived
    cache stays full-fidelity.
    """
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if is_pro:
        result["capped_at_24h"] = False
        return result
    # Shallow-copy so we don't mutate the cached object; ``days`` is the
    # only field we rewrite so a list slice is enough.
    capped = dict(result)
    days = list(capped.get("days") or [])
    # 24h window = today's bucket + yesterday's bucket (covers any clock
    # crossing midnight). Keep the trailing 2 entries, zero the rest so
    # the bar chart still renders 14 slots without leaking history.
    if days:
        head = max(0, len(days) - 2)
        for i in range(head):
            d = dict(days[i])
            d["tokens"] = 0
            d["cost"] = 0
            d["inputTokens"] = 0
            d["outputTokens"] = 0
            d["cacheReadTokens"] = 0
            d["cacheWriteTokens"] = 0
            days[i] = d
        capped["days"] = days
    capped["capped_at_24h"] = True
    return capped


@bp_usage.route("/api/usage")
def api_usage():
    """Token/cost tracking from transcript files - Enhanced OTLP workaround."""
    import dashboard as _d
    import time as _time

    # Epic #964 — local-store fast path. Opt-in via CLAWMETRY_LOCAL_STORE_READ=1;
    # falls through to OTLP/transcript scan when the store is empty / disabled.
    if is_local_store_read_enabled():
        fast = _try_local_store_usage()
        if fast is not None:
            return jsonify(_apply_oss_24h_cap(fast))

    now = _time.time()
    if (
        _d._usage_cache["data"] is not None
        and (now - _d._usage_cache["ts"]) < _d._USAGE_CACHE_TTL
    ):
        return jsonify(_apply_oss_24h_cap(_d._usage_cache["data"]))

    # Prefer OTLP data when available
    if _d._has_otel_data():
        result = _d._get_otel_usage_data()
        _d._usage_cache["data"] = result
        _d._usage_cache["ts"] = now
        try:
            _d._ext_emit("usage.compiled", {"ok": True})
        except Exception:
            pass
        return jsonify(_apply_oss_24h_cap(result))

    analytics = _d._compute_transcript_analytics()
    daily_tokens = analytics.get("daily_tokens", {})
    daily_cost = analytics.get("daily_cost", {})
    daily_input_tokens = analytics.get("daily_input_tokens", {})
    daily_output_tokens = analytics.get("daily_output_tokens", {})
    daily_cache_read_tokens = analytics.get("daily_cache_read_tokens", {})
    daily_cache_write_tokens = analytics.get("daily_cache_write_tokens", {})
    model_usage = analytics.get("model_usage", {})
    session_summaries = analytics.get("sessions", [])
    session_costs = {
        s.get("session_id", ""): round(float(s.get("cost_usd", 0.0) or 0.0), 6)
        for s in session_summaries
    }
    anomalies = _d._compute_session_cost_anomalies(session_summaries)

    # Build response data with cache token breakdown
    today = datetime.now()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append(
            {
                "date": ds,
                "tokens": daily_tokens.get(ds, 0),
                "cost": daily_cost.get(ds, 0),
                "inputTokens": daily_input_tokens.get(ds, 0),
                "outputTokens": daily_output_tokens.get(ds, 0),
                "cacheReadTokens": daily_cache_read_tokens.get(ds, 0),
                "cacheWriteTokens": daily_cache_write_tokens.get(ds, 0),
            }
        )

    # Calculate aggregations
    today_str = today.strftime("%Y-%m-%d")
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    month_start = today.strftime("%Y-%m-01")

    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)

    today_cost = daily_cost.get(today_str, 0)
    week_cost = sum(v for k, v in daily_cost.items() if k >= week_start)
    month_cost = sum(v for k, v in daily_cost.items() if k >= month_start)

    # Trend analysis & predictions
    trend_data = _d._analyze_usage_trends(daily_tokens)

    # Model breakdown for display
    model_breakdown = [
        {"model": k, "tokens": v}
        for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
    ]
    model_billing, billing_summary = _d._build_model_billing(model_usage)

    # Cost warnings
    warnings = _d._generate_cost_warnings(
        today_cost, week_cost, month_cost, trend_data, month_tok, billing_summary
    )

    # Issue #68 — top-N sessions by cost for the per-session breakdown
    # table on the Tokens/Usage tab. We hand back the 20 most expensive
    # sessions sorted desc so the UI can rank "who burned the budget"
    # without re-aggregating.
    top_sessions = sorted(
        session_summaries,
        key=lambda s: float(s.get("cost_usd", 0.0) or 0.0),
        reverse=True,
    )[:20]
    top_sessions_rows = [
        {
            "session_id":     s.get("session_id") or "",
            "agent_id":       s.get("agent_id") or "",
            "model":          s.get("model") or "",
            "total_tokens":   int(s.get("tokens") or 0),
            "total_cost_usd": round(float(s.get("cost_usd") or 0.0), 6),
            "message_count":  int(s.get("message_count") or 0),
            "started_at":     (
                datetime.fromtimestamp(float(s.get("start_ts") or 0)).isoformat()
                if s.get("start_ts") else ""
            ),
        }
        for s in top_sessions
        if float(s.get("cost_usd") or 0.0) > 0
    ]

    result = {
        "source": "transcripts",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "todayCost": round(today_cost, 4),
        "weekCost": round(week_cost, 4),
        "monthCost": round(month_cost, 4),
        "modelBreakdown": model_breakdown,
        "modelBilling": model_billing,
        "billingSummary": billing_summary,
        "sessionCosts": session_costs,
        "sessions": top_sessions_rows,
        "anomalies": anomalies,
        "anomalySessionIds": [a.get("session_id") for a in anomalies],
        "trend": trend_data,
        "warnings": warnings,
    }
    import time as _time

    _d._usage_cache["data"] = result
    _d._usage_cache["ts"] = _time.time()
    return jsonify(_apply_oss_24h_cap(result))


@bp_usage.route("/api/usage/anomalies")
def api_usage_anomalies():
    """Return session cost anomalies vs rolling 7-day baseline."""
    import dashboard as _d

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_usage_anomalies()
        if fast is not None:
            return jsonify(fast)

    analytics = _d._compute_transcript_analytics()
    session_summaries = analytics.get("sessions", [])
    anomalies = _d._compute_session_cost_anomalies(session_summaries)
    baseline_costs = [
        float(s.get("cost_usd", 0.0) or 0.0)
        for s in session_summaries
        if (time.time() - float(s.get("start_ts", 0) or 0)) <= (7 * 86400)
        and float(s.get("cost_usd", 0.0) or 0.0) > 0
    ]
    baseline_avg = (
        (sum(baseline_costs) / float(len(baseline_costs))) if baseline_costs else 0.0
    )
    return jsonify(
        {
            "anomalies": anomalies,
            "baseline_7d_avg_usd": round(baseline_avg, 6),
            "threshold_multiplier": 2.0,
        }
    )


@bp_usage.route("/api/anomalies")
def api_anomalies():
    """Rolling-baseline anomaly detection endpoint.

    Returns recent anomalies stored in ~/.openclaw/clawmetry.db with:
    - severity: critical/high/medium
    - metric: cost_spike / token_spike / error_rate_spike
    - value: the observed value that triggered the anomaly
    - baseline: the 7-day rolling average used as baseline
    - ratio: value / baseline
    - session_key: session ID (or '__error_rate__' for aggregate)
    - detected_at: Unix timestamp of detection
    """
    import dashboard as _d

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_anomalies()
        if fast is not None:
            return jsonify(fast)

    now = time.time()
    if (
        _d._anomaly_detection_cache["data"] is not None
        and (now - _d._anomaly_detection_cache["ts"]) < _d._ANOMALY_CACHE_TTL
    ):
        return jsonify(_d._anomaly_detection_cache["data"])

    anomalies, baselines = _d._detect_and_store_anomalies()
    active = [a for a in anomalies if not a.get("acknowledged")]
    result = {
        "anomalies": anomalies,
        "active_count": len(active),
        "has_active": bool(active),
        "baselines": baselines,
        "threshold_cost_multiplier": 2.0,
        "threshold_token_multiplier": 2.0,
        "threshold_error_multiplier": 3.0,
    }
    _d._anomaly_detection_cache["data"] = result
    _d._anomaly_detection_cache["ts"] = now
    return jsonify(result)


@bp_usage.route("/api/anomalies/<int:anomaly_id>/ack", methods=["POST"])
def api_anomaly_ack(anomaly_id):
    """Acknowledge an anomaly so it no longer appears in the active banner."""
    import dashboard as _d

    try:
        db = _d._get_anomaly_db()
        with _d._anomaly_db_lock:
            db.execute(
                "UPDATE anomalies SET acknowledged = 1 WHERE id = ?", (anomaly_id,)
            )
            db.commit()
        _d._anomaly_detection_cache["data"] = None  # invalidate cache
        return jsonify({"ok": True, "id": anomaly_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp_usage.route("/api/usage/by-plugin")
def api_usage_by_plugin():
    """Return plugin/skill token and cost attribution from transcript tool calls.

    Enhanced with trend direction (GH#201): compares recent 7-day vs prior 7-day
    cost share to flag plugins getting more expensive. Also emits threshold warnings
    when a plugin's cost share exceeds the configured limit (default 50%).
    """
    import dashboard as _d

    try:
        threshold_pct_arg = float(request.args.get("threshold", 50.0))
    except (ValueError, TypeError):
        threshold_pct_arg = 50.0

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_usage_by_plugin(threshold_pct_arg)
        if fast is not None:
            return jsonify(fast)

    analytics = _d._compute_transcript_analytics()
    plugin_stats = analytics.get("plugin_stats", {})
    plugin_daily_stats = analytics.get("plugin_daily_stats", {})
    total_tokens = sum(
        float(v.get("tokens", 0.0) or 0.0) for v in plugin_stats.values()
    )
    total_tokens = total_tokens if total_tokens > 0 else 1.0

    try:
        threshold_pct = float(request.args.get("threshold", 50.0))
    except (ValueError, TypeError):
        threshold_pct = 50.0

    warnings = []
    rows = []
    for plugin, stats in plugin_stats.items():
        toks = float(stats.get("tokens", 0.0) or 0.0)
        cost = float(stats.get("cost", 0.0) or 0.0)
        calls = int(stats.get("calls", 0) or 0)
        pct = round((toks / total_tokens) * 100.0, 2)
        trend = _d._compute_plugin_trend(plugin, plugin_daily_stats)
        rows.append(
            {
                "plugin": plugin,
                "total_tokens": int(round(toks)),
                "cost_usd": round(cost, 6),
                "call_count": calls,
                "pct_of_total": pct,
                "trend": trend,
            }
        )
        if pct >= threshold_pct:
            warnings.append(
                {
                    "plugin": plugin,
                    "pct_of_total": pct,
                    "message": f"{plugin} accounts for {pct:.1f}% of total token usage "
                               f"(threshold: {threshold_pct:.0f}%)",
                    "trend": trend,
                }
            )
    rows.sort(key=lambda r: r["total_tokens"], reverse=True)
    return jsonify({"plugins": rows, "warnings": warnings})


@bp_usage.route("/api/usage/by-plugin/trend")
def api_usage_by_plugin_trend():
    """Return per-day plugin token and cost breakdown for trend analysis (GH#201).

    Response shape:
      {
        "days": ["2026-03-20", ...],
        "plugins": {
          "exec": [{"day": "2026-03-20", "tokens": 120, "cost_usd": 0.001, "calls": 3}, ...],
          ...
        }
      }
    """
    import dashboard as _d

    try:
        days_back = int(request.args.get("days", 14))
    except (ValueError, TypeError):
        days_back = 14
    days_back = min(max(days_back, 1), 90)

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_usage_by_plugin_trend(days_back)
        if fast is not None:
            return jsonify(fast)

    analytics = _d._compute_transcript_analytics()
    plugin_daily_stats = analytics.get("plugin_daily_stats", {})

    from datetime import date, timedelta
    today = date.today()
    day_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back - 1, -1, -1)]

    # Collect all plugin names that appear in the window
    plugin_names: set = set()
    for d in day_list:
        plugin_names.update(plugin_daily_stats.get(d, {}).keys())

    result: dict = {}
    for p in sorted(plugin_names):
        series = []
        for d in day_list:
            day_data = plugin_daily_stats.get(d, {}).get(p, {})
            series.append(
                {
                    "day": d,
                    "tokens": int(round(float(day_data.get("tokens", 0.0) or 0.0))),
                    "cost_usd": round(float(day_data.get("cost", 0.0) or 0.0), 6),
                    "calls": int(day_data.get("calls", 0) or 0),
                }
            )
        result[p] = series

    return jsonify({"days": day_list, "plugins": result})


def _build_cluster_payload(session_profiles, *, days, now_ts):
    """Aggregate per-session profiles into clusters keyed by
    (tool_category, cost_tier, error_presence, model_family)."""
    def _model_family(model_str):
        m = (model_str or "").lower()
        if "claude" in m:
            return "claude"
        if "gpt" in m or "openai" in m:
            return "gpt"
        if "gemini" in m or "google" in m:
            return "gemini"
        if "llama" in m or "mistral" in m or "groq" in m:
            return "open-source"
        return "other"

    def _tool_category(tool_name):
        t = (tool_name or "").lower()
        if t in ("none", ""):
            return "no-tools"
        if t in ("exec", "bash", "shell", "run"):
            return "code-execution"
        if t in ("read", "write", "edit", "file_read", "file_write"):
            return "file-ops"
        if t in ("web_search", "web_fetch", "browser"):
            return "web"
        if t in ("message", "tts", "send_message"):
            return "communication"
        if t in ("sessions_spawn", "sessions_send", "subagents"):
            return "orchestration"
        if t in ("memory_search", "memory_get"):
            return "memory"
        return "other-tools"

    clusters_map = defaultdict(
        lambda: {
            "sessions": [], "total_tokens": 0, "total_cost_usd": 0.0,
            "error_count": 0, "tool_freq": defaultdict(int),
        }
    )
    for sp in session_profiles:
        mf = _model_family(sp["model"])
        tc = _tool_category(sp["top_tool"])
        has_errors = "errors" if sp["error_count"] > 0 else "clean"
        cluster_key = f"{tc}|{sp['cost_tier']}|{has_errors}|{mf}"
        c = clusters_map[cluster_key]
        c["sessions"].append(sp["session_id"])
        c["total_tokens"] += sp["tokens"]
        c["total_cost_usd"] += sp["cost_usd"]
        c["error_count"] += sp["error_count"]
        for tool, cnt in sp["tool_counts"].items():
            c["tool_freq"][tool] += cnt
        if "tool_category" not in c:
            c["tool_category"] = tc
            c["cost_tier"] = sp["cost_tier"]
            c["has_errors"] = has_errors == "errors"
            c["model_family"] = mf

    clusters_out = []
    for key, c in clusters_map.items():
        n = len(c["sessions"])
        avg_cost = c["total_cost_usd"] / n if n > 0 else 0.0
        top_tools_sorted = sorted(c["tool_freq"].items(), key=lambda x: x[1], reverse=True)[:5]
        tc = c.get("tool_category", "other")
        cost_tier = c.get("cost_tier", "cheap")
        mf = c.get("model_family", "other")
        has_err = c.get("has_errors", False)
        label_parts = []
        if tc == "code-execution": label_parts.append("Code execution")
        elif tc == "file-ops":     label_parts.append("File operations")
        elif tc == "web":          label_parts.append("Web browsing")
        elif tc == "communication":label_parts.append("Messaging")
        elif tc == "orchestration":label_parts.append("Agent orchestration")
        elif tc == "memory":       label_parts.append("Memory access")
        elif tc == "no-tools":     label_parts.append("Conversational")
        else:                       label_parts.append("Mixed tools")
        if cost_tier == "expensive": label_parts.append("high-cost")
        elif cost_tier == "medium":  label_parts.append("medium-cost")
        if has_err: label_parts.append("with errors")
        if mf not in ("claude", "other"): label_parts.append(mf)
        clusters_out.append({
            "cluster_id": key,
            "label": " ".join(label_parts),
            "session_count": n,
            "session_ids": c["sessions"][:10],
            "total_tokens": c["total_tokens"],
            "total_cost_usd": round(c["total_cost_usd"], 6),
            "avg_cost_usd": round(avg_cost, 6),
            "error_count": c["error_count"],
            "tool_category": tc,
            "cost_tier": cost_tier,
            "has_errors": has_err,
            "model_family": mf,
            "top_tools": [{"tool": t, "count": cnt} for t, cnt in top_tools_sorted],
        })
    clusters_out.sort(key=lambda x: x["session_count"], reverse=True)
    return {
        "clusters": clusters_out,
        "total_sessions": len(session_profiles),
        "days": days,
        "generated_at": int(now_ts * 1000),
    }


def _try_local_store_sessions_clusters(days: int):
    """Fast path for /api/sessions/clusters. Reads sessions + events from
    DuckDB and runs the same cluster aggregation as the legacy JSONL walker.

    Issue #1088: routes through the daemon HTTP proxy via ``_ls_call``.
    Returns ``None`` to defer to the JSONL fallback when DuckDB has no
    sessions in the time window.
    """
    now_ts = time.time()
    cutoff_ts = now_ts - (days * 86400)
    cutoff_iso = datetime.utcfromtimestamp(cutoff_ts).isoformat()
    sessions = _ls_call("query_sessions", since=cutoff_iso, limit=2000)
    if not sessions:
        return None
    # One bulk events fetch; group by session_id (avoids N+1 daemon hops).
    events = _ls_call("query_events", since=cutoff_iso, limit=20000) or []
    # Issue #1451: sibling-dedupe so the per-session token fallback below
    # doesn't double-count assistant + model.completed pairs on v3 installs.
    bucket_max = build_sibling_bucket_max(events)
    by_session: dict = defaultdict(list)
    for ev in events:
        sid = ev.get("session_id")
        if sid:
            by_session[sid].append(ev)

    import dashboard as _d
    usd_per_tok = _d._estimate_usd_per_token()
    session_profiles = []
    for s in sessions:
        sid = s.get("session_id")
        if not sid:
            continue
        evs = by_session.get(sid, [])
        tool_counts: dict = defaultdict(int)
        error_count = 0
        s_model = "unknown"
        has_cron = False
        has_subagent = False
        turn_count = 0
        # Issue #1451: ``query_sessions`` returns ``SUM(token_count)`` from
        # the events table, which on real v3 installs double-counts the
        # ``assistant`` + ``model.completed`` sibling pair for every billable
        # turn. Compute s_tokens from the deduped event list instead so the
        # cluster aggregator doesn't inflate per-session totals. Falls back
        # to the (still-inflated) session-row sum only when no events were
        # joined in for this session.
        s_tokens = sum(
            int(ev.get("token_count") or 0)
            for ev in evs
            if not is_sibling_dup(ev, bucket_max)
        )
        if s_tokens == 0:
            s_tokens = int(s.get("token_count") or 0)
        for ev in evs:
            data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
            msg = data.get("message") if isinstance(data.get("message"), dict) else {}
            mdl = ev.get("model") or msg.get("model") or data.get("model")
            if mdl:
                s_model = mdl
            for t in _d._extract_tool_plugins(data) or []:
                tool_counts[t] += 1
            etype = ev.get("event_type") or data.get("type") or ""
            if etype in ("error", "tool_error"):
                error_count += 1
            if isinstance(data.get("error"), dict) and data["error"]:
                error_count += 1
            blob = json.dumps(data, default=str).lower()
            if "cron" in blob or "scheduled" in blob:
                has_cron = True
            if "subagent" in blob or "spawned" in blob:
                has_subagent = True
            if etype == "message":
                turn_count += 1
        if s_tokens == 0 and not tool_counts:
            continue
        total_tools = sum(tool_counts.values())
        top_tool = max(tool_counts, key=tool_counts.get) if tool_counts else "none"
        cost = float(s.get("cost_usd") or 0.0)
        if cost == 0.0 and s_tokens:
            cost = round(s_tokens * usd_per_tok, 6)
        if cost >= 0.10:
            cost_tier = "expensive"
        elif cost >= 0.02:
            cost_tier = "medium"
        else:
            cost_tier = "cheap"
        session_profiles.append({
            "session_id": sid, "model": s_model, "top_tool": top_tool,
            "tool_counts": dict(tool_counts), "total_tools": total_tools,
            "error_count": error_count, "tokens": s_tokens, "cost_usd": cost,
            "cost_tier": cost_tier, "has_cron": has_cron,
            "has_subagent": has_subagent, "turn_count": turn_count,
        })
    if not session_profiles:
        return None
    payload = _build_cluster_payload(session_profiles, days=days, now_ts=now_ts)
    payload["_source"] = "local_store"
    return payload


@bp_usage.route("/api/sessions/clusters")
def api_sessions_clusters():
    """Cluster sessions by behavior pattern (tool usage, cost profile, error type, model).

    Implements trace clustering similar to PostHog's Clusters for LLM Analytics,
    but with OpenClaw-native dimensions (tool names, skill invocations, cron sessions).
    Closes vivekchand/clawmetry#406.
    """
    import dashboard as _d

    _CLUSTER_ANALYTICS_TTL = 120  # seconds
    now_ts = time.time()
    try:
        days_arg = int(request.args.get("days", 30))
    except (ValueError, TypeError):
        days_arg = 30
    if is_local_store_read_enabled():
        fast = _try_local_store_sessions_clusters(days_arg)
        if fast is not None:
            return jsonify(fast)

    # Optional time window filter (days)
    try:
        days = int(request.args.get("days", 30))
    except (ValueError, TypeError):
        days = 30
    cache_key = f"days:{days}"
    cached = _CLUSTER_CACHE.get("data")
    if cached is not None and _CLUSTER_CACHE.get("key") == cache_key and (now_ts - float(_CLUSTER_CACHE.get("ts") or 0)) < _CLUSTER_CACHE_TTL_SECONDS:
        return jsonify(cached)
    cutoff_ts = now_ts - (days * 86400)

    sessions_dir = _d._get_sessions_dir()
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return jsonify(
            {
                "clusters": [],
                "total_sessions": 0,
                "days": days,
                "generated_at": int(now_ts * 1000),
            }
        )

    usd_per_tok = _d._estimate_usd_per_token()
    session_profiles = []

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        if ".trajectory." in fname or ".checkpoint." in fname or ".deleted." in fname:
            continue
        fpath = os.path.join(sessions_dir, fname)
        try:
            fmtime = os.path.getmtime(fpath)
            if fmtime < cutoff_ts:
                continue

            sid = fname.replace(".jsonl", "")
            tool_counts = defaultdict(int)
            error_count = 0
            s_tokens = 0
            s_model = "unknown"
            has_cron = False
            has_subagent = False
            turn_count = 0
            s_start = fmtime

            with open(fpath, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue

                    # Detect model
                    message = (
                        obj.get("message", {})
                        if isinstance(obj.get("message"), dict)
                        else {}
                    )
                    model = message.get("model") or obj.get("model")
                    if model:
                        s_model = model

                    # Count tool calls
                    tools = _d._extract_tool_plugins(obj)
                    for t in tools:
                        tool_counts[t] += 1

                    # Count errors
                    if obj.get("type") in ("error", "tool_error") or (
                        isinstance(obj.get("error"), dict) and obj["error"]
                    ):
                        error_count += 1

                    # Detect cron / subagent hints
                    content_str = json.dumps(obj, default=str).lower()
                    if "cron" in content_str or "scheduled" in content_str:
                        has_cron = True
                    if "subagent" in content_str or "spawned" in content_str:
                        has_subagent = True

                    # Usage metrics
                    metrics = _d._extract_usage_metrics(obj)
                    if metrics["tokens"] > 0:
                        s_tokens += metrics["tokens"]
                        turn_count += 1

            if s_tokens == 0 and not tool_counts:
                continue

            total_tools = sum(tool_counts.values())
            top_tool = max(tool_counts, key=tool_counts.get) if tool_counts else "none"
            cost = round(s_tokens * usd_per_tok, 6)

            # Determine cost tier
            if cost >= 0.10:
                cost_tier = "expensive"
            elif cost >= 0.02:
                cost_tier = "medium"
            else:
                cost_tier = "cheap"

            session_profiles.append(
                {
                    "session_id": sid,
                    "model": s_model,
                    "top_tool": top_tool,
                    "tool_counts": dict(tool_counts),
                    "total_tools": total_tools,
                    "error_count": error_count,
                    "tokens": s_tokens,
                    "cost_usd": cost,
                    "cost_tier": cost_tier,
                    "has_cron": has_cron,
                    "has_subagent": has_subagent,
                    "turn_count": turn_count,
                    "fmtime": fmtime,
                }
            )
        except Exception:
            continue

    # ── Clustering logic ────────────────────────────────────────────────────────
    # Cluster key = (dominant_tool_category, cost_tier, error_presence, model_family)

    def _model_family(model_str):
        m = (model_str or "").lower()
        if "claude" in m:
            return "claude"
        if "gpt" in m or "openai" in m:
            return "gpt"
        if "gemini" in m or "google" in m:
            return "gemini"
        if "llama" in m or "mistral" in m or "groq" in m:
            return "open-source"
        return "other"

    def _tool_category(tool_name):
        t = (tool_name or "").lower()
        if t in ("none", ""):
            return "no-tools"
        if t in ("exec", "bash", "shell", "run"):
            return "code-execution"
        if t in ("read", "write", "edit", "file_read", "file_write"):
            return "file-ops"
        if t in ("web_search", "web_fetch", "browser"):
            return "web"
        if t in ("message", "tts", "send_message"):
            return "communication"
        if t in ("sessions_spawn", "sessions_send", "subagents"):
            return "orchestration"
        if t in ("memory_search", "memory_get"):
            return "memory"
        return "other-tools"

    clusters_map = defaultdict(
        lambda: {
            "sessions": [],
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "error_count": 0,
            "tool_freq": defaultdict(int),
        }
    )

    for sp in session_profiles:
        mf = _model_family(sp["model"])
        tc = _tool_category(sp["top_tool"])
        has_errors = "errors" if sp["error_count"] > 0 else "clean"
        cluster_key = f"{tc}|{sp['cost_tier']}|{has_errors}|{mf}"

        c = clusters_map[cluster_key]
        c["sessions"].append(sp["session_id"])
        c["total_tokens"] += sp["tokens"]
        c["total_cost_usd"] += sp["cost_usd"]
        c["error_count"] += sp["error_count"]
        for tool, cnt in sp["tool_counts"].items():
            c["tool_freq"][tool] += cnt

        # Tag attributes (set once)
        if "tool_category" not in c:
            c["tool_category"] = tc
            c["cost_tier"] = sp["cost_tier"]
            c["has_errors"] = has_errors == "errors"
            c["model_family"] = mf

    # ── Build response ──────────────────────────────────────────────────────────
    clusters_out = []
    for key, c in clusters_map.items():
        n = len(c["sessions"])
        avg_cost = c["total_cost_usd"] / n if n > 0 else 0.0
        top_tools_sorted = sorted(
            c["tool_freq"].items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Auto-label cluster
        tc = c.get("tool_category", "other")
        cost_tier = c.get("cost_tier", "cheap")
        mf = c.get("model_family", "other")
        has_err = c.get("has_errors", False)
        label_parts = []
        if tc == "code-execution":
            label_parts.append("Code execution")
        elif tc == "file-ops":
            label_parts.append("File operations")
        elif tc == "web":
            label_parts.append("Web browsing")
        elif tc == "communication":
            label_parts.append("Messaging")
        elif tc == "orchestration":
            label_parts.append("Agent orchestration")
        elif tc == "memory":
            label_parts.append("Memory access")
        elif tc == "no-tools":
            label_parts.append("Conversational")
        else:
            label_parts.append("Mixed tools")
        if cost_tier == "expensive":
            label_parts.append("high-cost")
        elif cost_tier == "medium":
            label_parts.append("medium-cost")
        if has_err:
            label_parts.append("with errors")
        if mf not in ("claude", "other"):
            label_parts.append(mf)

        cluster_label = " ".join(label_parts)

        clusters_out.append(
            {
                "cluster_id": key,
                "label": cluster_label,
                "session_count": n,
                "session_ids": c["sessions"][:10],  # first 10 for drill-down
                "total_tokens": c["total_tokens"],
                "total_cost_usd": round(c["total_cost_usd"], 6),
                "avg_cost_usd": round(avg_cost, 6),
                "error_count": c["error_count"],
                "tool_category": tc,
                "cost_tier": cost_tier,
                "has_errors": has_err,
                "model_family": mf,
                "top_tools": [{"tool": t, "count": cnt} for t, cnt in top_tools_sorted],
            }
        )

    clusters_out.sort(key=lambda x: x["session_count"], reverse=True)

    payload = {
        "clusters": clusters_out,
        "total_sessions": len(session_profiles),
        "days": days,
        "generated_at": int(now_ts * 1000),
    }
    _CLUSTER_CACHE["data"] = payload
    _CLUSTER_CACHE["key"] = cache_key
    _CLUSTER_CACHE["ts"] = time.time()
    return jsonify(payload)


@bp_usage.route("/api/usage/cost-comparison")
def api_usage_cost_comparison():
    """Return cost comparison: actual spend vs alternatives (GH#554)."""
    import dashboard as _d

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_cost_comparison()
        if fast is not None:
            return jsonify(fast)

    try:
        return jsonify(_d._build_cost_comparison())
    except Exception as e:
        return jsonify({"error": str(e), "alternatives": [], "actual": {}}), 500


@bp_usage.route("/api/usage/forecast")
def api_usage_forecast():
    """7-day rolling spend rate projected to end-of-month (issue #1413).

    Math: daily_rate = sum(cost_usd last 7 days) / 7
          projected_month = cost_so_far + daily_rate * days_remaining
          days_to_budget = (budget - cost_so_far) / daily_rate

    Returns {available, daily_rate_usd, cost_this_month_usd,
             projected_month_usd, days_remaining_in_month,
             monthly_budget_usd, budget_exceeded, days_to_budget,
             budget_cross_date, pro_dispatch_enabled, budget_alert,
             window_days, daily_window, _source}.
    Returns {available: false} when no local-store data is present.
    """
    import calendar
    import math
    import dashboard as _d
    from datetime import datetime, timedelta, timezone

    today = datetime.now(timezone.utc).date()

    rows = _ls_call("query_daily_usage_splits") or []
    if not rows:
        rows = _ls_call("query_aggregates") or []

    if not rows:
        return jsonify({"available": False, "reason": "no_data"})

    daily_costs: dict[str, float] = {}
    for r in rows:
        day = r.get("day", "")
        if day:
            daily_costs[day] = float(r.get("cost_usd") or 0)

    window_days = 7
    window: list[float] = []
    for i in range(window_days):
        d = (today - timedelta(days=i)).isoformat()
        window.append(daily_costs.get(d, 0.0))

    daily_rate = sum(window) / window_days

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = today.day
    days_remaining = days_in_month - days_elapsed

    month_str = today.strftime("%Y-%m")
    cost_this_month = sum(v for k, v in daily_costs.items() if k.startswith(month_str))

    projected_month = cost_this_month + daily_rate * days_remaining

    budget_cfg = _d._get_budget_config()
    monthly_budget = float(budget_cfg.get("monthly_limit") or 0)
    monthly_cap = float(budget_cfg.get("monthly_cap_usd") or 0)
    effective_budget = monthly_budget or monthly_cap or 0.0

    budget_exceeded = bool(effective_budget > 0 and projected_month > effective_budget)
    days_to_budget: float | None = None
    budget_cross_date: str | None = None
    if effective_budget > 0 and daily_rate > 0:
        remaining_budget = effective_budget - cost_this_month
        days_to_budget = max(0.0, remaining_budget / daily_rate)
        if budget_exceeded:
            cross_offset_days = min(days_remaining, math.ceil(days_to_budget))
            budget_cross_date = (
                today + timedelta(days=cross_offset_days)
            ).isoformat()

    try:
        pro_dispatch_enabled = bool(_d._is_pro_user())
    except Exception:
        pro_dispatch_enabled = False

    return jsonify({
        "available": True,
        "daily_rate_usd": round(daily_rate, 4),
        "cost_this_month_usd": round(cost_this_month, 4),
        "projected_month_usd": round(projected_month, 4),
        "days_remaining_in_month": days_remaining,
        "monthly_budget_usd": effective_budget,
        "budget_exceeded": budget_exceeded,
        "days_to_budget": round(days_to_budget, 1) if days_to_budget is not None else None,
        "budget_cross_date": budget_cross_date,
        "pro_dispatch_enabled": pro_dispatch_enabled,
        "budget_alert": {
            "available": budget_exceeded,
            "pro_required": True,
            "pro_dispatch_enabled": pro_dispatch_enabled,
            "upgrade_url": "/cloud/billing",
        },
        "window_days": window_days,
        "daily_window": [round(c, 4) for c in reversed(window)],
        "_source": "local_store",
    })


@bp_usage.route("/api/usage/export")
def api_usage_export():
    """Export usage data as CSV."""
    import dashboard as _d

    try:
        # Get usage data
        if _d._has_otel_data():
            data = _d._get_otel_usage_data()
        else:
            # Call the same logic as /api/usage but get full data
            sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
                "~/.openclaw/agents/main/sessions"
            )
            daily_tokens = {}

            if os.path.isdir(sessions_dir):
                for fname in os.listdir(sessions_dir):
                    if not fname.endswith(".jsonl"):
                        continue
                    fpath = os.path.join(sessions_dir, fname)
                    try:
                        fmtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        with open(fpath, "r") as f:
                            for line in f:
                                try:
                                    obj = json.loads(line.strip())
                                    tokens = 0
                                    usage = (
                                        obj.get("usage") or obj.get("tokens_used") or {}
                                    )
                                    if isinstance(usage, dict):
                                        tokens = (
                                            usage.get("total_tokens")
                                            or usage.get("totalTokens")
                                            or (
                                                usage.get("input_tokens", 0)
                                                + usage.get("output_tokens", 0)
                                            )
                                            or 0
                                        )
                                    elif isinstance(usage, (int, float)):
                                        tokens = int(usage)
                                    if not tokens:
                                        content = obj.get("content", "")
                                        if (
                                            isinstance(content, str)
                                            and len(content) > 0
                                        ):
                                            tokens = max(1, len(content) // 4)
                                        elif isinstance(content, list):
                                            total_len = sum(
                                                len(str(c.get("text", "")))
                                                for c in content
                                                if isinstance(c, dict)
                                            )
                                            tokens = (
                                                max(1, total_len // 4)
                                                if total_len
                                                else 0
                                            )
                                    ts = (
                                        obj.get("timestamp")
                                        or obj.get("time")
                                        or obj.get("created_at")
                                    )
                                    if ts:
                                        if isinstance(ts, (int, float)):
                                            dt = datetime.fromtimestamp(
                                                ts / 1000 if ts > 1e12 else ts
                                            )
                                        else:
                                            try:
                                                dt = datetime.fromisoformat(
                                                    str(ts).replace("Z", "+00:00")
                                                )
                                            except Exception:
                                                dt = fmtime
                                    else:
                                        dt = fmtime
                                    day = dt.strftime("%Y-%m-%d")
                                    if tokens > 0:
                                        daily_tokens[day] = (
                                            daily_tokens.get(day, 0) + tokens
                                        )
                                except (json.JSONDecodeError, ValueError):
                                    pass
                    except Exception:
                        pass

            today = datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            month_start = today.strftime("%Y-%m-01")

            # Build data structure similar to OTLP
            days = []
            for i in range(30, -1, -1):  # Last 30 days for export
                d = today - timedelta(days=i)
                ds = d.strftime("%Y-%m-%d")
                tokens = daily_tokens.get(ds, 0)
                cost = round(tokens * (30.0 / 1_000_000), 4)  # Default pricing
                days.append({"date": ds, "tokens": tokens, "cost": cost})

            data = {'days': days}

        # Generate CSV content
        csv_lines = ['Date,Tokens,Cost']
        for day in data['days']:
            csv_lines.append(f"{day['date']},{day['tokens']},{day.get('cost', 0):.4f}")

        csv_content = '\n'.join(csv_lines)

        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=openclaw-usage-{datetime.now().strftime("%Y%m%d")}.csv'
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_usage.route('/api/model-attribution')
def api_model_attribution():
    """Per-model turn/session breakdown and switch history (GH #300)."""
    import dashboard as _d

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_model_attribution()
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    model_turns = {}    # model -> assistant turn count
    model_sessions = {} # model -> session count
    switches = []       # list of {session, from_model, to_model}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl') or 'deleted' in fname:
                continue
            sid = fname.replace('.jsonl', '')
            fpath = os.path.join(sessions_dir, fname)
            try:
                current_model = None
                session_start_model = None
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except (json.JSONDecodeError, ValueError):
                            continue
                        t = obj.get('type', '')
                        # Detect model changes
                        if t == 'model_change':
                            new_model = obj.get('modelId') or obj.get('model') or ''
                            if new_model:
                                if current_model and current_model != new_model:
                                    switches.append({
                                        'session': sid,
                                        'from_model': current_model,
                                        'to_model': new_model,
                                    })
                                current_model = new_model
                                if session_start_model is None:
                                    session_start_model = new_model
                        elif t == 'custom':
                            ct = obj.get('customType', '')
                            if ct == 'model-snapshot':
                                d = obj.get('data', {})
                                m = d.get('modelId') or d.get('model') or ''
                                if m and current_model is None:
                                    current_model = m
                                    session_start_model = m
                        # Count assistant turns per model
                        msg = obj.get('message', {})
                        if isinstance(msg, dict) and msg.get('role') == 'assistant':
                            m = msg.get('model') or obj.get('model') or current_model or 'unknown'
                            if m:
                                model_turns[m] = model_turns.get(m, 0) + 1
                # Track which model a session primarily used (first detected)
                primary = session_start_model or current_model
                if primary:
                    model_sessions[primary] = model_sessions.get(primary, 0) + 1
            except Exception:
                pass

    total_turns = sum(model_turns.values())
    # Build sorted model list
    sorted_models = sorted(model_turns.items(), key=lambda x: -x[1])
    primary_model = sorted_models[0][0] if sorted_models else ''

    models_out = []
    for m, turns in sorted_models:
        models_out.append({
            'model': m,
            'turns': turns,
            'sessions': model_sessions.get(m, 0),
            'provider': _d._provider_from_model(m),
            'share_pct': round(turns / total_turns * 100, 2) if total_turns else 0,
        })

    return jsonify({
        'models': models_out,
        'primary_model': primary_model,
        'total_turns': total_turns,
        'model_count': len(model_turns),
        'switches': switches[:50],  # cap at 50 for response size
        'switch_count': len(switches),
    })


@bp_usage.route('/api/skill-attribution')
def api_skill_attribution():
    """Per-skill cost attribution with ClawHub integration hooks (GH #308).

    Detects skill invocations by scanning session transcripts for SKILL.md file
    reads. Each time a SKILL.md is read, the session's token cost is attributed
    to that skill (shared equally when multiple skills are read in one session).

    Returns:
        {
          "skills": [
            {
              "name": str,
              "invocations": int,
              "total_cost_usd": float,
              "avg_cost_usd": float,
              "last_used": str | null,   # ISO timestamp
              "clawhub_url": str,        # future ClawHub skill marketplace link
            }
          ],
          "top5_week": [...],            # top 5 by total_cost_usd in last 7 days
          "total_cost": float,
          "note": str,
          "clawhub": {"enabled": false, "url": null},
        }
    """
    import dashboard as _d
    import re as _re

    # Epic #964 — local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_skill_attribution()
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d._get_sessions_dir()
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return jsonify({
            "skills": [], "top5_week": [], "total_cost": 0.0,
            "note": "No sessions directory found.",
            "clawhub": {"enabled": False, "url": None},
        })

    SKILL_MD_RE = _re.compile(r'[/\\]([^/\\]+)[/\\]SKILL\.md', _re.IGNORECASE)
    # Also match bare "SKILL.md" references with skill name in path context
    SKILL_PATH_RE = _re.compile(r'skills[/\\]([^/\\]+)', _re.IGNORECASE)

    skill_stats = {}   # name -> {invocations, total_cost, last_used_ts}
    now_ts = time.time()
    week_cutoff = now_ts - 7 * 86400
    usd_per_token = _d._estimate_usd_per_token()

    try:
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(sessions_dir, fname)
            session_skills = set()
            session_tokens = 0
            session_cost = 0.0
            session_ts = os.path.getmtime(fpath)

            try:
                with open(fpath, 'r', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue

                        # Detect SKILL.md file reads in tool calls / tool results
                        raw = json.dumps(obj)
                        for m in SKILL_MD_RE.finditer(raw):
                            skill_name = m.group(1)
                            if skill_name and skill_name.lower() != 'skills':
                                session_skills.add(skill_name)
                        # Fallback: skills/ path pattern
                        if not session_skills:
                            for m in SKILL_PATH_RE.finditer(raw):
                                candidate = m.group(1)
                                if candidate and 'SKILL' in raw[m.start():m.end()+30].upper():
                                    session_skills.add(candidate)

                        # Accumulate session tokens/cost
                        usage = _d._extract_usage_metrics(obj)
                        if usage['tokens'] > 0:
                            session_tokens += usage['tokens']
                            session_cost += usage['cost'] if usage['cost'] > 0 else (
                                usage['tokens'] * usd_per_token
                            )
            except Exception:
                continue

            if not session_skills:
                continue

            share = session_cost / len(session_skills) if session_skills else 0.0
            for skill in session_skills:
                if skill not in skill_stats:
                    skill_stats[skill] = {'invocations': 0, 'total_cost': 0.0, 'last_used_ts': 0.0}
                skill_stats[skill]['invocations'] += 1
                skill_stats[skill]['total_cost'] += share
                if session_ts > skill_stats[skill]['last_used_ts']:
                    skill_stats[skill]['last_used_ts'] = session_ts
    except Exception:
        pass

    skills_out = []
    total_cost = 0.0
    for name, st in sorted(skill_stats.items(), key=lambda x: -x[1]['total_cost']):
        inv = st['invocations']
        tc = round(float(st['total_cost']), 6)
        avg = round(tc / inv, 6) if inv else 0.0
        lts = st['last_used_ts']
        last_used = datetime.utcfromtimestamp(lts).strftime('%Y-%m-%dT%H:%M:%SZ') if lts else None
        total_cost += tc
        skills_out.append({
            'name': name,
            'invocations': inv,
            'total_cost_usd': tc,
            'avg_cost_usd': avg,
            'last_used': last_used,
            'clawhub_url': f'https://clawhub.dev/skills/{name}',
        })

    # top5 this week
    top5_week = [
        s for s in skills_out
        if s['last_used'] and s['last_used'] >= datetime.utcfromtimestamp(week_cutoff).strftime('%Y-%m-%dT%H:%M:%SZ')
    ][:5]

    note = 'Skills detected from SKILL.md file reads in session transcripts.'

    return jsonify({
        'skills': skills_out,
        'top5_week': top5_week,
        'total_cost': round(total_cost, 6),
        'note': note,
        'clawhub': {'enabled': False, 'url': None},
    })


@bp_usage.route('/api/token-velocity')
def api_token_velocity():
    """Sliding 2-min token velocity endpoint — detects runaway agent loops (GH #313).

    Returns:
      {
        alert: bool,
        level: "ok" | "warning" | "critical",
        velocity_2min: int,       # total tokens in last 2 minutes
        cost_per_min: float,      # estimated USD/min burn rate
        flagged_sessions: [       # sessions exceeding thresholds
          {id, tokens_2min, tool_chain_len, cost_per_min}
        ]
      }

    Thresholds:
      warning:  velocity_2min >= 8000
      critical: velocity_2min >= 15000 OR tool_chain_len >= 20
    """
    import dashboard as _d

    WARN_TOKENS   = 8000
    CRIT_TOKENS   = 15000
    CRIT_TOOLS    = 20

    now        = time.time()
    window_2min = now - 120

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    total_tokens_2min = 0
    flagged = []

    try:
        if os.path.isdir(sessions_dir):
            candidates = sorted(
                [f for f in os.listdir(sessions_dir)
                 if f.endswith('.jsonl') and 'deleted' not in f],
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True
            )[:20]

            for fname in candidates:
                fpath = os.path.join(sessions_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > 300:          # skip inactive sessions > 5 min
                        continue
                    tokens_2min   = 0
                    consecutive   = 0
                    max_chain     = 0
                    with open(fpath, 'r', errors='replace') as fh:
                        lines = list(fh)
                    for line in lines:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue
                        ts = _d._json_ts_to_epoch(
                            obj.get('timestamp') or obj.get('time') or obj.get('created_at')
                        )
                        msg     = obj.get('message', {}) if isinstance(obj.get('message'), dict) else {}
                        role    = msg.get('role', '') or obj.get('role', '')
                        content = msg.get('content', [])
                        is_tool = False
                        if isinstance(content, list):
                            for blk in content:
                                if isinstance(blk, dict) and blk.get('type') == 'tool_use':
                                    is_tool = True
                                    break
                        if role == 'user' and not is_tool:
                            consecutive = 0
                        elif is_tool or role == 'assistant':
                            consecutive += 1
                            max_chain = max(max_chain, consecutive)
                        if ts and ts >= window_2min:
                            usage = msg.get('usage', {}) if isinstance(msg.get('usage'), dict) else {}
                            tok = float(
                                usage.get('total_tokens')
                                or usage.get('totalTokens')
                                or (usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                                or 0
                            )
                            tokens_2min += int(tok)

                    total_tokens_2min += tokens_2min
                    usd_per_token = _d._estimate_usd_per_token()
                    sess_tpm = _d._session_burn_stats(fname.replace('.jsonl', '')).get('tokensPerMin', 0)
                    sess_cpm = round(sess_tpm * usd_per_token, 5)

                    if tokens_2min >= WARN_TOKENS or max_chain >= CRIT_TOOLS:
                        flagged.append({
                            'id':           fname.replace('.jsonl', ''),
                            'tokens_2min':  tokens_2min,
                            'tool_chain_len': max_chain,
                            'cost_per_min': sess_cpm,
                        })
                except Exception:
                    continue
    except Exception:
        pass

    if total_tokens_2min >= CRIT_TOKENS or any(s['tool_chain_len'] >= CRIT_TOOLS for s in flagged):
        level = 'critical'
    elif total_tokens_2min >= WARN_TOKENS:
        level = 'warning'
    else:
        level = 'ok'

    usd_per_token  = _d._estimate_usd_per_token()
    cost_per_min   = round(total_tokens_2min / 2 * usd_per_token, 5)   # tokens/2min → per min

    return jsonify({
        'alert':            level != 'ok',
        'level':            level,
        'velocity_2min':    total_tokens_2min,
        'cost_per_min':     cost_per_min,
        'flagged_sessions': flagged,
    })


# ── Prompt-cache analytics (GH #851) ────────────────────────────────────


def _empty_cache_bucket():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "cache_read_cost": 0.0,
        "cache_write_cost": 0.0,
        "total_cost": 0.0,
    }


def _summarise_cache_bucket(label, b, key):
    in_plus_cache = b["input_tokens"] + b["cache_read_tokens"]
    cache_hit_pct = (
        round(b["cache_read_tokens"] / in_plus_cache * 100, 1)
        if in_plus_cache
        else 0.0
    )
    # Anthropic prompt-cache reads cost ~10% of fresh input tokens, so the
    # "saved" amount is the difference between what those tokens would have
    # cost as fresh input vs. what they actually cost as cache reads.
    est_fresh_input_cost = b["cache_read_cost"] * 10.0
    est_savings = max(0.0, est_fresh_input_cost - b["cache_read_cost"])
    est_savings_pct = (
        round(est_savings / (b["input_cost"] + est_fresh_input_cost) * 100, 1)
        if (b["input_cost"] + est_fresh_input_cost)
        else 0.0
    )
    return {
        key: label,
        "input_tokens": b["input_tokens"],
        "output_tokens": b["output_tokens"],
        "cache_read_tokens": b["cache_read_tokens"],
        "cache_write_tokens": b["cache_write_tokens"],
        "input_cost_usd": round(b["input_cost"], 6),
        "output_cost_usd": round(b["output_cost"], 6),
        "cache_read_cost_usd": round(b["cache_read_cost"], 6),
        "cache_write_cost_usd": round(b["cache_write_cost"], 6),
        "total_cost_usd": round(b["total_cost"], 6),
        "cache_hit_ratio_pct": cache_hit_pct,
        "est_savings_usd": round(est_savings, 6),
        "est_savings_pct": est_savings_pct,
    }


def _cache_recommendations(totals, by_model):
    tips = []
    hit = totals.get("cache_hit_ratio_pct", 0.0)
    if totals.get("input_tokens", 0) + totals.get("cache_read_tokens", 0) == 0:
        tips.append(
            "No cache-eligible traffic in window. Connect a recent agent run to see "
            "cache analytics."
        )
        return tips
    if hit < 30.0:
        tips.append(
            f"Cache hit ratio is low ({hit}%). Stabilise your system prompt and "
            "front-load static context — Anthropic charges ~10% for cache reads vs. "
            "fresh input."
        )
    elif hit < 60.0:
        tips.append(
            f"Cache hit ratio is moderate ({hit}%). Look for prompt suffixes that "
            "rotate per turn (timestamps, RNG nonces) — they invalidate the cache "
            "block above them."
        )
    else:
        tips.append(
            f"Cache hit ratio is healthy ({hit}%). Most repeat prompts are landing "
            "in the cache."
        )

    cw = totals.get("cache_write_tokens", 0)
    cr = totals.get("cache_read_tokens", 0)
    if cw and cr and cw > cr:
        tips.append(
            "Cache writes outweigh reads — sessions are short-lived or your prompt "
            "block is changing often. A longer-lived session prefix would amortise "
            "the write cost."
        )

    poor_models = [
        m for m in by_model
        if (m.get("input_tokens", 0) + m.get("cache_read_tokens", 0)) >= 5000
        and m.get("cache_hit_ratio_pct", 0.0) < 20.0
    ]
    if poor_models:
        names = ", ".join(sorted({m["model"] for m in poor_models})[:3])
        tips.append(
            f"Models with notably low cache utilisation: {names}. Check whether "
            "their system prompt is wrapped in a cache_control breakpoint."
        )
    return tips


@bp_usage.route("/api/usage/cache-trends")
def api_usage_cache_trends():
    """Daily + per-model prompt-cache hit ratio and estimated savings (GH #851).

    Query params:
      days  — window size in days (default 14, max 90)

    Returns:
      {
        days:    int,
        daily:   [{date, input_tokens, output_tokens, cache_read_tokens,
                    cache_write_tokens, *cost_usd, cache_hit_ratio_pct,
                    est_savings_usd, est_savings_pct}],
        by_model:[same shape, keyed by `model`],
        totals:  same shape, keyed by `label`,
        recommendations: [str],
      }
    """
    import dashboard as _d

    try:
        days = max(1, min(int(request.args.get("days", "14")), 90))
    except ValueError:
        days = 14

    sessions_dir = _d._get_sessions_dir()
    cutoff_ts = time.time() - (days * 86400)

    daily: dict = {}
    by_model: dict = {}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not (fname.endswith(".jsonl") or ".jsonl.reset." in fname):
                continue
            if (
                ".trajectory." in fname
                or ".checkpoint." in fname
                or ".deleted." in fname
            ):
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                fallback_dt = datetime.fromtimestamp(os.path.getmtime(fpath))
            except OSError:
                continue
            # Skip files whose mtime is older than the window AND whose name
            # doesn't include a reset suffix — saves IO on stale archives.
            if fallback_dt.timestamp() < cutoff_ts and ".jsonl.reset." not in fname:
                continue
            last_seen_model = ""
            try:
                with open(fpath, "r", errors="replace") as fh:
                    for raw in fh:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            ev = json.loads(raw)
                        except Exception:
                            continue
                        t = ev.get("type", "")
                        if t == "model_change":
                            m = ev.get("modelId") or ev.get("model") or ""
                            if m:
                                last_seen_model = m
                            continue
                        msg = ev.get("message", {}) or {}
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage", {}) or {}
                        if not isinstance(usage, dict) or not usage:
                            continue
                        msg_model = msg.get("model") or last_seen_model or "unknown"
                        if msg_model:
                            last_seen_model = msg_model

                        ts = _d._parse_event_timestamp(
                            ev.get("timestamp")
                            or ev.get("time")
                            or ev.get("created_at"),
                            fallback_dt,
                        )
                        if not ts:
                            ts = fallback_dt
                        if ts.timestamp() < cutoff_ts:
                            continue
                        date_str = ts.strftime("%Y-%m-%d")

                        in_toks = int(
                            usage.get("input", usage.get("input_tokens", 0)) or 0
                        )
                        out_toks = int(
                            usage.get("output", usage.get("output_tokens", 0)) or 0
                        )
                        cr_toks = int(
                            usage.get(
                                "cacheRead", usage.get("cache_read_tokens", 0)
                            )
                            or 0
                        )
                        cw_toks = int(
                            usage.get(
                                "cacheWrite", usage.get("cache_write_tokens", 0)
                            )
                            or 0
                        )
                        cost_obj = usage.get("cost", {}) or {}
                        if not isinstance(cost_obj, dict):
                            cost_obj = {}
                        in_cost = float(cost_obj.get("input", 0) or 0)
                        out_cost = float(cost_obj.get("output", 0) or 0)
                        cr_cost = float(cost_obj.get("cacheRead", 0) or 0)
                        cw_cost = float(cost_obj.get("cacheWrite", 0) or 0)
                        total_cost = float(
                            cost_obj.get(
                                "total", in_cost + out_cost + cr_cost + cw_cost
                            )
                            or 0
                        )

                        for bucket in (
                            daily.setdefault(date_str, _empty_cache_bucket()),
                            by_model.setdefault(msg_model, _empty_cache_bucket()),
                        ):
                            bucket["input_tokens"] += in_toks
                            bucket["output_tokens"] += out_toks
                            bucket["cache_read_tokens"] += cr_toks
                            bucket["cache_write_tokens"] += cw_toks
                            bucket["input_cost"] += in_cost
                            bucket["output_cost"] += out_cost
                            bucket["cache_read_cost"] += cr_cost
                            bucket["cache_write_cost"] += cw_cost
                            bucket["total_cost"] += total_cost
            except Exception:
                continue

    today = datetime.now()
    daily_out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        daily_out.append(
            _summarise_cache_bucket(ds, daily.get(ds, _empty_cache_bucket()), key="date")
        )

    by_model_out = [
        _summarise_cache_bucket(m, b, key="model")
        for m, b in sorted(by_model.items(), key=lambda kv: -kv[1]["total_cost"])
    ]

    totals_bucket = _empty_cache_bucket()
    for b in daily.values():
        for k in totals_bucket:
            totals_bucket[k] += b[k]
    totals_out = _summarise_cache_bucket("totals", totals_bucket, key="label")

    return jsonify({
        "days": days,
        "daily": daily_out,
        "by_model": by_model_out,
        "totals": totals_out,
        "recommendations": _cache_recommendations(totals_out, by_model_out),
    })


# ── Skills fidelity telemetry (GH #687) ─────────────────────────────────


@bp_usage.route('/api/skills/fidelity')
def api_skills_fidelity():
    """Skills fidelity telemetry: dead-skill detector + body/linked-file stats (GH #687).

    Compares skills installed in workspace/skills/ against SKILL.md body-fetches
    seen in recent session JSONL files and classifies each skill as:

      dead   — installed (header always in system context) but body never fetched
      stuck  — body fetched but linked files in the skill dir never accessed
      active — body fetched (and either no linked files, or at least one accessed)
      orphan — body-fetched in sessions but not installed (untracked / removed)

    Query params:
      sessions  — number of recent session files to scan (default 200, max 500)

    Returns:
      {
        skills: [{name, installed, body_fetches, linked_file_fetches,
                  sessions_seen, status, token_roi}],
        dead_count, stuck_count, active_count, orphan_count,
        total_installed, note
      }
    """
    import dashboard as _d
    import re as _re

    try:
        max_sessions = max(1, min(int(request.args.get("sessions", 200)), 500))
    except (TypeError, ValueError):
        max_sessions = 200

    workspace = (
        _d.WORKSPACE
        or os.environ.get("OPENCLAW_WORKSPACE")
        or os.environ.get("OPENCLAW_HOME")
        or os.path.expanduser("~/.openclaw/workspace")
    )
    sessions_dir = _d._get_sessions_dir()

    # 1. List installed skills — each subdir containing SKILL.md is one skill
    skills_dir = os.path.join(workspace, "skills")
    installed_skills: set = set()
    skill_has_linked: dict = {}  # name -> bool (has non-SKILL.md, non-hidden files)
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            entry_path = os.path.join(skills_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            if not os.path.isfile(os.path.join(entry_path, "SKILL.md")):
                continue
            installed_skills.add(entry)
            linked = [
                f for f in os.listdir(entry_path)
                if f.upper() != "SKILL.MD"
                and not f.startswith('.')
                and os.path.isfile(os.path.join(entry_path, f))
            ]
            skill_has_linked[entry] = bool(linked)

    # 2. Scan recent session JSONLs for SKILL.md body-fetches and linked-file reads
    SKILL_MD_RE = _re.compile(r'[/\\]([^/\\]+)[/\\]SKILL\.md', _re.IGNORECASE)
    SKILL_LINKED_RE = _re.compile(
        r'skills[/\\]([^/\\]+)[/\\]([^/\\\'">\s]{1,80})', _re.IGNORECASE
    )

    body_fetches: dict = {}    # skill_name -> count
    linked_fetches: dict = {}  # skill_name -> count
    skill_sessions: dict = {}  # skill_name -> set of session filenames

    if sessions_dir and os.path.isdir(sessions_dir):
        try:
            all_files = [
                f for f in os.listdir(sessions_dir)
                if f.endswith('.jsonl')
                and '.trajectory.' not in f
                and '.checkpoint.' not in f
            ]
            all_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True,
            )
            for fname in all_files[:max_sessions]:
                fpath = os.path.join(sessions_dir, fname)
                try:
                    with open(fpath, 'r', errors='replace') as fh:
                        for raw in fh:
                            raw = raw.strip()
                            if not raw:
                                continue
                            try:
                                obj = json.loads(raw)
                            except Exception:
                                continue
                            if obj.get('role') not in ('assistant', 'tool', 'user'):
                                continue
                            line_str = json.dumps(obj)
                            for m in SKILL_MD_RE.finditer(line_str):
                                sname = m.group(1)
                                if sname.lower() in ('skills', ''):
                                    continue
                                body_fetches[sname] = body_fetches.get(sname, 0) + 1
                                skill_sessions.setdefault(sname, set()).add(fname)
                            for m in SKILL_LINKED_RE.finditer(line_str):
                                sname = m.group(1)
                                if m.group(2).upper() == 'SKILL.MD':
                                    continue
                                linked_fetches[sname] = linked_fetches.get(sname, 0) + 1
                except Exception:
                    continue
        except Exception:
            pass

    # 3. Build per-skill stats and classify
    all_names = installed_skills | set(body_fetches) | set(linked_fetches)
    skills_out = []
    dead_count = stuck_count = active_count = orphan_count = 0

    for name in sorted(all_names):
        installed = name in installed_skills
        bf = body_fetches.get(name, 0)
        lf = linked_fetches.get(name, 0)
        sess = len(skill_sessions.get(name, set()))
        has_linked = skill_has_linked.get(name, False)

        if installed and bf == 0:
            status = 'dead'
            dead_count += 1
        elif not installed and bf > 0:
            status = 'orphan'
            orphan_count += 1
        elif bf > 0 and has_linked and lf == 0:
            status = 'stuck'
            stuck_count += 1
        else:
            status = 'active'
            active_count += 1

        skills_out.append({
            'name': name,
            'installed': installed,
            'body_fetches': bf,
            'linked_file_fetches': lf,
            'sessions_seen': sess,
            'status': status,
            'token_roi': round(bf / sess, 3) if sess > 0 else None,
        })

    _STATUS_ORDER = {'dead': 0, 'stuck': 1, 'orphan': 2, 'active': 3}
    skills_out.sort(key=lambda s: (_STATUS_ORDER[s['status']], -s['body_fetches']))

    return jsonify({
        'skills': skills_out,
        'dead_count': dead_count,
        'stuck_count': stuck_count,
        'active_count': active_count,
        'orphan_count': orphan_count,
        'total_installed': len(installed_skills),
        'note': (
            'Dead: installed but body never fetched — remove to save header tokens. '
            'Stuck: body fetched but linked files unread despite existing. '
            'Orphan: body-fetched in sessions but not installed (skill removed?).'
        ),
    })


@bp_usage.route('/api/token-attribution')
def api_token_attribution():
    """Per-message cost attribution with cache token breakdown.

    Returns granular token/cost breakdown per message type (input, output, cache-read, cache-write)
    for the specified session or across recent sessions.
    """
    import dashboard as _d

    wanted_sid = request.args.get('session_id', '').strip()
    try:
        limit = max(1, min(int(request.args.get('limit', '100')), 1000))
    except ValueError:
        limit = 100

    sessions_dir = _d._get_sessions_dir()
    if not os.path.isdir(sessions_dir):
        return jsonify({"messages": [], "totals": {}, "note": "sessions dir not found"})

    try:
        all_files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith('.jsonl') and '.deleted.' not in f and '.reset.' not in f
        ]
    except OSError:
        all_files = []

    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True
        )[:50]

    messages = []
    totals = {
        'input_tokens': 0,
        'output_tokens': 0,
        'cache_read_tokens': 0,
        'cache_write_tokens': 0,
        'total_tokens': 0,
        'input_cost': 0.0,
        'output_cost': 0.0,
        'cache_read_cost': 0.0,
        'cache_write_cost': 0.0,
        'total_cost': 0.0,
    }

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        sid = fname[:-6] if fname.endswith('.jsonl') else fname

        try:
            with open(fpath, 'r', errors='replace') as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue

                    if ev.get('type') != 'message':
                        continue

                    msg = ev.get('message', {}) or {}
                    if not isinstance(msg, dict):
                        continue

                    usage = msg.get('usage', {}) or {}
                    if not isinstance(usage, dict) or not usage:
                        continue

                    # Get token breakdown
                    input_tok = int(usage.get('input', usage.get('input_tokens', 0)) or 0)
                    output_tok = int(usage.get('output', usage.get('output_tokens', 0)) or 0)
                    cache_read = int(usage.get('cacheRead', usage.get('cache_read_tokens', 0)) or 0)
                    cache_write = int(usage.get('cacheWrite', usage.get('cache_write_tokens', 0)) or 0)

                    # Get cost breakdown
                    cost_obj = usage.get('cost', {}) or {}
                    if isinstance(cost_obj, dict):
                        input_cost = float(cost_obj.get('input', 0) or 0)
                        output_cost = float(cost_obj.get('output', 0) or 0)
                        cache_read_cost = float(cost_obj.get('cacheRead', 0) or 0)
                        cache_write_cost = float(cost_obj.get('cacheWrite', 0) or 0)
                        total_cost = float(cost_obj.get('total', cost_obj.get('usd', 0)) or 0)
                    else:
                        input_cost = output_cost = cache_read_cost = cache_write_cost = total_cost = 0.0

                    total_tok = input_tok + output_tok + cache_read + cache_write

                    if total_tok == 0:
                        continue

                    msg_data = {
                        'session_id': sid,
                        'timestamp': ev.get('timestamp') or ev.get('time') or ev.get('created_at'),
                        'model': msg.get('model', 'unknown'),
                        'role': msg.get('role', 'unknown'),
                        'tokens': {
                            'input': input_tok,
                            'output': output_tok,
                            'cache_read': cache_read,
                            'cache_write': cache_write,
                            'total': total_tok,
                        },
                        'cost': {
                            'input': round(input_cost, 8),
                            'output': round(output_cost, 8),
                            'cache_read': round(cache_read_cost, 8),
                            'cache_write': round(cache_write_cost, 8),
                            'total': round(total_cost, 8),
                        },
                        'cache_hit_ratio': round(cache_read / (input_tok + cache_read) * 100, 1) if (input_tok + cache_read) > 0 else 0.0,
                    }

                    messages.append(msg_data)

                    # Update totals
                    totals['input_tokens'] += input_tok
                    totals['output_tokens'] += output_tok
                    totals['cache_read_tokens'] += cache_read
                    totals['cache_write_tokens'] += cache_write
                    totals['total_tokens'] += total_tok
                    totals['input_cost'] += input_cost
                    totals['output_cost'] += output_cost
                    totals['cache_read_cost'] += cache_read_cost
                    totals['cache_write_cost'] += cache_write_cost
                    totals['total_cost'] += total_cost
        except Exception:
            continue

    # Round totals
    for k in ['input_cost', 'output_cost', 'cache_read_cost', 'cache_write_cost', 'total_cost']:
        totals[k] = round(totals[k], 6)

    # Sort by timestamp descending and apply limit
    messages.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
    messages = messages[:limit]

    # Calculate cache hit ratio
    input_plus_cache = totals['input_tokens'] + totals['cache_read_tokens']
    totals['cache_hit_ratio_pct'] = round(totals['cache_read_tokens'] / input_plus_cache * 100, 1) if input_plus_cache else 0.0

    return jsonify({
        'messages': messages,
        'totals': totals,
        'session_id': wanted_sid if wanted_sid else None,    })
