"""Cohort compare and similar runs (WO-60; requirement "Cohort compare and
similar runs", REQ-COH-001..004).

``GET /api/cohort-compare``            two filters in, a verdict out
``GET /api/cohort-compare/suggested``  ready-made comparisons from what
                                       changed recently in the store
``GET /api/sessions/<id>/similar``     runs shaped like this one

All store access goes through the daemon proxy (``_ls_call``); every rule
lives in the pure module ``clawmetry/cohort_compare.py`` so tests drive it
with fixture rows. Honesty contracts enforced here rather than in the UI:

* store unreachable is ``store_available: false``, distinct from an
  answered-but-empty window;
* a cohort that spans runtimes the tier does not include returns the same
  402 ``upgrade_required`` body the runtime gate returns, never partial
  numbers;
* the global runtime switcher (``?runtime=``) scopes both sides unless a
  side names its own runtime.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate, require_runtime

bp_cohort = Blueprint("cohort", __name__)

# How far back the cohort universe reaches for one request. Wider windows
# come from the filters themselves (``since`` on either side).
DEFAULT_WINDOW_DAYS = 28
MAX_WINDOW_DAYS = 365
SUGGESTED_CAP = 5


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


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _runtime_switch() -> str | None:
    rt = (request.args.get("runtime") or "").strip().lower()
    return rt if rt and rt != "all" else None


def _apply_switch(f: dict, rt: str | None) -> dict:
    if rt and not f.get("runtime"):
        f = dict(f)
        f["runtime"] = rt
    return f


def _earliest_since(filters: list[dict], default_days: int = DEFAULT_WINDOW_DAYS) -> str:
    """The scan lower bound: the earliest ``since`` any filter names, else
    the default window. Never wider than MAX_WINDOW_DAYS."""
    floor_dt = datetime.now(timezone.utc) - timedelta(days=MAX_WINDOW_DAYS)
    default = datetime.now(timezone.utc) - timedelta(days=default_days)
    candidates = [default]
    for f in filters:
        s = f.get("since")
        if s:
            try:
                candidates.append(datetime.fromisoformat(s[:19]).replace(tzinfo=timezone.utc))
            except ValueError:
                pass
    return _iso(max(floor_dt, min(candidates)))


def _blocked_runtime(runtimes) -> object | None:
    """First 402 response for a runtime the tier does not include, or None."""
    for rt in sorted(set(r for r in runtimes if r)):
        blocked = require_runtime(rt)
        if blocked is not None:
            return blocked
    return None


def _views_and_flags(since: str):
    """Scan once; return (views, signals_available, context_available,
    store_available)."""
    from clawmetry.cohort_compare import session_view

    rows = _ls_call("query_cohort_sessions", since=since)
    if rows is None:
        return [], False, False, False
    rows = [r for r in rows if isinstance(r, dict)]
    views = [session_view(r) for r in rows]
    signals_available = any("signals" in r for r in rows)
    context_available = any("instructions_hash" in r for r in rows)
    return views, signals_available, context_available, True


@bp_cohort.route("/api/cohort-compare")
@gate("per_run_compare")
def api_cohort_compare():
    """Two cohorts, one verdict. ``a`` and ``b`` are JSON filter objects or
    repeated params (``a.runtime=claude_code``). See
    ``clawmetry.cohort_compare.FILTER_KEYS`` for the accepted keys."""
    from clawmetry import cohort_compare as cc

    rt = _runtime_switch()
    filter_a = _apply_switch(cc.filter_from_params(request.args, "a"), rt)
    filter_b = _apply_switch(cc.filter_from_params(request.args, "b"), rt)
    if not filter_a and not filter_b:
        return jsonify({
            "error": "missing filters",
            "hint": "Pass a and b as JSON filter objects, e.g. "
                    "a={\"runtime\":\"claude_code\",\"model\":\"x\"}",
            "filter_keys": list(cc.FILTER_KEYS),
        }), 400

    # A named runtime the tier does not include is refused before any read.
    blocked = _blocked_runtime([filter_a.get("runtime"), filter_b.get("runtime")])
    if blocked is not None:
        return blocked

    since = _earliest_since([filter_a, filter_b])
    views, signals_available, _ctx, store_available = _views_and_flags(since)
    body = cc.compare(views, filter_a, filter_b, signals_available=signals_available)
    # An unnamed runtime that resolves to paid sessions is refused too: the
    # numbers would otherwise be a partial view of an entitlement the tier
    # does not hold.
    blocked = _blocked_runtime(body.get("runtimes") or [])
    if blocked is not None:
        return blocked
    body["store_available"] = store_available
    body["window_since"] = since
    body["runtime_version_recorded"] = any(v.get("runtime_version") for v in views)
    body["_source"] = "local_store" if store_available else "none"
    return jsonify(body)


def build_suggested_payload(views: list[dict], *, signals_available: bool,
                            context_available: bool, runtime: str | None,
                            cap: int = SUGGESTED_CAP, with_results: bool = True) -> dict:
    """Suggestions plus their computed results. Shared by the HTTP route and
    the daemon's snapshot slice so the hosted dashboard renders the same
    cards from ``cohortSuggested``."""
    from clawmetry import cohort_compare as cc

    suggestions = cc.build_suggestions(
        views, context_available=context_available, runtime=runtime, cap=cap)
    out = []
    for s in suggestions:
        item = dict(s)
        if with_results:
            res = cc.compare(views, s["a"], s["b"],
                             signals_available=signals_available,
                             sample_sessions=10)
            item["result"] = {
                "verdict": res["verdict"],
                "deltas": res["deltas"],
                "a": res["a"], "b": res["b"],
                "comparability": res["comparability"],
                "signals": res["signals"],
            }
        out.append(item)
    return {
        "schema": 1,
        "suggestions": out,
        "signals": "available" if signals_available else "not available",
        "context_available": context_available,
        "min_sessions": cc.min_sessions(),
    }


@bp_cohort.route("/api/cohort-compare/suggested")
@gate("per_run_compare")
def api_cohort_suggested():
    """Ready-made comparisons: a model first seen recently, a runtime version
    first seen, an instructions file changed (when the store records it),
    and this week vs last week per runtime."""
    rt = _runtime_switch()
    blocked = _blocked_runtime([rt]) if rt else None
    if blocked is not None:
        return blocked
    since = _iso(datetime.now(timezone.utc) - timedelta(days=DEFAULT_WINDOW_DAYS))
    views, signals_available, context_available, store_available = _views_and_flags(since)
    # Paid-runtime suggestions are not offered to a tier that cannot read
    # them; drop those views rather than return a 402 for the whole list.
    try:
        from clawmetry import entitlements as _ent
        en = _ent.get_entitlement()
        views = [v for v in views if en.allows_runtime(v.get("runtime") or "")]
    except Exception:
        pass
    body = build_suggested_payload(
        views, signals_available=signals_available,
        context_available=context_available, runtime=rt)
    body["store_available"] = store_available
    body["session_count"] = len(views)
    body["_source"] = "local_store" if store_available else "none"
    return jsonify(body)


def _parse_window(raw: str | None, default: int = 30) -> int:
    s = (raw or "").strip().lower()
    if not s:
        return default
    try:
        if s.endswith("d"):
            return max(1, min(365, int(s[:-1])))
        if s.endswith("w"):
            return max(1, min(365, int(s[:-1]) * 7))
        return max(1, min(365, int(s)))
    except ValueError:
        return default


@bp_cohort.route("/api/sessions/<path:session_id>/similar")
@gate("per_run_compare")
def api_session_similar(session_id: str):
    """Runs shaped like this one. ``?window=30d&limit=10``. The shape walk
    runs in the daemon (``query_similar_sessions``), never here."""
    sid = (session_id or "").strip()
    if not sid:
        return jsonify({"error": "session id required"}), 400
    prefix = sid.split(":", 1)[0] if ":" in sid else "openclaw"
    blocked = require_runtime(prefix)
    if blocked is not None:
        return blocked
    window_days = _parse_window(request.args.get("window"))
    try:
        limit = max(1, min(50, int(request.args.get("limit") or 10)))
    except (TypeError, ValueError):
        limit = 10
    body = _ls_call("query_similar_sessions", session_id=sid,
                    window_days=window_days, limit=limit)
    if not isinstance(body, dict):
        return jsonify({
            "session_id": sid, "neighbours": [], "store_available": False,
            "coverage": "store unreachable",
        })
    # Never hand back a neighbour from a runtime the tier does not include.
    try:
        from clawmetry import entitlements as _ent
        en = _ent.get_entitlement()
        body["neighbours"] = [
            n for n in body.get("neighbours") or []
            if en.allows_runtime(str(n.get("runtime") or ""))
        ]
    except Exception:
        pass
    body["store_available"] = True
    return jsonify(body)
