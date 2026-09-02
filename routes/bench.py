"""Harness Engineering tab endpoints (Blueprint: Harness Benchmarks &
Comparison; REQ-HB-001..007).

One cross-runtime fan-out payload (`GET /api/bench`) plus the deep-dive
surfaces: published third-party pairs, workload recommendations, the
per-session flow trace, and context-window curves. All store access goes
through the daemon proxy (`_ls_call`); every scoring rule lives in the pure
modules `clawmetry/harness_bench.py`, `clawmetry/workload_profiles.py`,
`clawmetry/flow_trace.py` so tests drive them with fixture rows.

Honesty contracts enforced here rather than in the UI:
- store unreachable (None) is reported as `store_available: false`, distinct
  from an answered-but-empty window;
- a harness with no measurable completion signal is never ranked;
- published pairs always carry source, date, runner, and historical flag.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

bp_bench = Blueprint("bench", __name__)

_SESSION_LIMIT = 1500
_EVENTS_PER_SESSION = 4000
_DEFAULT_DAYS = 30


def _ls_call(method_name: str, **kwargs):
    """Cross-process LocalStore call with single-process fallback."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _days_arg() -> int:
    try:
        days = int(request.args.get("days") or _DEFAULT_DAYS)
    except (TypeError, ValueError):
        days = _DEFAULT_DAYS
    return max(7, min(90, days))


def _iso_cutoff(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%S")


def _sessions_by_runtime(days: int):
    """All quality-session rows in the window, grouped by runtime.
    Returns (grouped_or_None, store_available)."""
    rows = _ls_call("query_quality_sessions", since=_iso_cutoff(days),
                    limit=_SESSION_LIMIT)
    if rows is None:
        return None, False
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        rt = str(r.get("runtime") or "openclaw")
        grouped.setdefault(rt, []).append(r)
    return grouped, True


@bp_bench.route("/api/bench")
def api_bench():
    """The whole bench in one payload: scorecards, workload profiles, and
    recommendation cards. One set of store calls per tab load; the daemon
    proxy is not cheap and the quality-session scan must not run twice
    (FLYWHEEL performance budget)."""
    from clawmetry.efficiency import build_efficiency_slice
    from clawmetry.harness_bench import build_bench, build_headtohead
    from clawmetry.published_benchmarks import published_pairs
    from clawmetry.workload_profiles import build_recommendations, profile_spend

    days = _days_arg()
    grouped, store_available = _sessions_by_runtime(days)

    eff_rows = _ls_call("query_efficiency_rollup", days=days) or []
    eff = build_efficiency_slice(eff_rows, days=days)
    sub_stats = _ls_call("query_subagent_stats_by_runtime", days=days)
    if not isinstance(sub_stats, dict):
        sub_stats = {}

    out = build_bench(
        grouped or {},
        efficiency_by_runtime=eff.get("byRuntime") or {},
        subagent_stats_by_runtime=sub_stats,
        days=days,
    )
    spend = profile_spend(grouped or {})
    out["profiles"] = spend.get("profiles", [])
    out["total_spend_usd"] = spend.get("total_spend_usd", 0.0)
    out["recommendations"] = build_recommendations(
        spend, out.get("byRuntime"), published_pairs())
    out["headtohead"] = build_headtohead(grouped or {})
    out["store_available"] = store_available
    out["_source"] = "local_store" if store_available else "none"
    return jsonify(out)


@bp_bench.route("/api/bench/published")
def api_bench_published():
    from clawmetry.published_benchmarks import published_pairs

    days = _days_arg()
    eff_rows = _ls_call("query_efficiency_rollup", days=days) or []
    observed_models = sorted({str(r.get("model") or "") for r in eff_rows
                              if isinstance(r, dict) and r.get("model")})
    observed_runtimes = sorted({str(r.get("runtime") or "") for r in eff_rows
                                if isinstance(r, dict) and r.get("runtime")})
    return jsonify({
        "pairs": published_pairs(),
        "observed_models": observed_models,
        "observed_runtimes": observed_runtimes,
        "_source": "static_catalog",
    })




@bp_bench.route("/api/bench/flow/<path:session_id>")
def api_bench_flow(session_id: str):
    from clawmetry.flow_trace import build_flow_trace

    sid = (session_id or "").strip()
    if not sid:
        return jsonify({"error": "session_id required"}), 400
    events = _ls_call("query_events", session_id=sid, limit=_EVENTS_PER_SESSION)
    if events is None:
        return jsonify({"available": False, "store_available": False,
                        "session_id": sid})
    bare = sid.split(":", 1)[1] if ":" in sid else sid
    subs = _ls_call(
        "query_subagents_lite",
        parent_session_ids=sorted({sid, bare}),
        parent_like=["%:" + bare, bare + "::%"],
        limit=500,
    ) or []
    runtime = sid.split(":", 1)[0] if ":" in sid else "openclaw"
    last_ts = None
    for r in reversed(events):
        if isinstance(r, dict) and r.get("ts"):
            last_ts = r.get("ts")
            break
    trace = build_flow_trace(
        {"session_id": sid, "last_active_at": last_ts},
        events, subs, runtime=runtime,
    )
    trace["available"] = bool(events)
    trace["store_available"] = True
    return jsonify(trace)


@bp_bench.route("/api/bench/context-curves")
def api_bench_context_curves():
    from clawmetry.harness_bench import build_context_curves

    session_id = (request.args.get("session_id") or "").strip() or None
    runtime = (request.args.get("runtime") or "").strip().lower() or None
    if runtime == "all":
        runtime = None
    kwargs = {"util_limit": 800}
    if session_id:
        kwargs["session_id"] = session_id
    if runtime:
        kwargs["runtime"] = runtime
    econ = _ls_call("query_context_economics", **kwargs)
    if econ is None:
        return jsonify({"available": False, "store_available": False,
                        "curves": [], "byRuntime": {}})

    shaped = build_context_curves(econ, max_sessions=6)
    # Per-runtime grouping for the small-multiples strip: the runtime is the
    # session-id prefix (bare UUIDs are OpenClaw), same bucketing as the store.
    by_runtime: dict[str, dict] = {}
    if not session_id:
        all_curves = build_context_curves(econ, max_sessions=60)["curves"]
        for c in all_curves:
            sid = c.get("session_id") or ""
            rt = sid.split(":", 1)[0] if ":" in sid else "openclaw"
            slot = by_runtime.setdefault(rt, {"curves": 0, "peaks": [],
                                              "compactions": 0, "overflows": 0})
            slot["curves"] += 1
            slot["peaks"].append(c.get("peak_pct") or 0)
            slot["compactions"] += len(c.get("compactions") or [])
            if c.get("overflowed"):
                slot["overflows"] += 1
        for slot in by_runtime.values():
            peaks = sorted(slot.pop("peaks"))
            slot["median_peak_pct"] = (round(peaks[len(peaks) // 2], 1)
                                       if peaks else None)
    return jsonify({
        "available": True,
        "store_available": True,
        "curves": shaped["curves"],
        "session_count": shaped["session_count"],
        "summary": econ.get("summary") if isinstance(econ, dict) else None,
        "byRuntime": by_runtime,
        "_source": "local_store",
    })
