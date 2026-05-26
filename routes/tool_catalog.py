"""routes/tool_catalog.py — interactive tool catalog + provenance (PRD P1-3).

Every tool the agent actually invoked, grouped by **provenance** (builtin /
MCP / plugin), with per-tool **call count, p50/p95 latency, and error rate** —
plus a drill-down into the individual recent calls behind each tool row.

Where the numbers come from
===========================
Latency + counts + errors are derived from the DuckDB ``events`` table (the
same rows ClawMetry already ingests — no OTLP exporter, no gateway RPC). Each
``tool_call`` event is matched to its closing ``tool_result`` by the tool_use
id, exactly the join ``routes/turn_anatomy.py`` uses for its waterfall
(``_tool_use_ids`` open the span; ``_tool_result_id`` closes it). Duration is
``result_ts - call_ts``; an unmatched call contributes to the count but not the
latency percentiles. Aggregated per tool name → ``calls``, ``p50_ms``,
``p95_ms``, ``error_rate``.

Provenance is classified from two inputs:
  1. The OpenClaw sandbox tool universe, already mirrored into DuckDB by
     ``clawmetry/sync.py:sync_tool_policy`` (``openclaw sandbox explain
     --json`` → ``tool_policy.allow``) and read here via ``query_tool_policy``.
     A tool name in that allow set is **builtin**.
  2. Name shape: a name containing ``__`` / ``mcp__`` is an **MCP** tool (the
     provider is the prefix before ``__``). Anything left over is **plugin**.
If the sandbox universe is unavailable (fresh sync / OpenClaw build without
``sandbox explain``) we degrade to name-based classification only — never an
error.

Endpoints (bp_tool_catalog):
  GET /api/tool-catalog              — per-tool rollup grouped by provenance
  GET /api/tool-catalog/<name>/calls — recent individual calls for one tool

Reads go through the daemon proxy (the daemon owns the DuckDB writer lock)
with a single-process direct-read fallback — the same ``_ls_call`` pattern as
``routes/scheduler.py`` / ``routes/policy.py``. Neither endpoint ever 500s on
empty data.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

bp_tool_catalog = Blueprint("tool_catalog", __name__)


# ── DuckDB access (daemon proxy + single-process fallback) ──────────────────

def _ls_call(method_name: str, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088)."""
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


def _coerce_rows(rows) -> list:
    """``local_store_via_daemon`` returns the raw method result (a list) or a
    ``{"result": [...]}`` / ``{"rows": [...]}`` envelope depending on transport
    — normalise both to a plain list."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


# ── Event helpers (mirror routes/turn_anatomy.py tool-timing join) ──────────

def _data(e):
    d = e.get("data")
    return d if isinstance(d, dict) else {}


def _ts_ms(ts):
    """Coerce an event ts (ISO-8601 string or epoch s/ms) to ms-since-epoch."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return int(ts * 1000) if ts < 1e12 else int(ts)
    try:
        return int(datetime.fromisoformat(
            str(ts).replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:
        return None


def _tool_name(e):
    """The tool name a ``tool_call`` event invokes. Strips the OpenClaw-native
    ``mcp__openclaw__`` wrapper so a builtin reads as its plain name."""
    d = _data(e)
    name = d.get("tool_name")
    if name:
        return str(name).replace("mcp__openclaw__", "")
    tcs = d.get("tool_calls")
    if isinstance(tcs, list) and tcs and isinstance(tcs[0], dict):
        n = tcs[0].get("name") or (tcs[0].get("function") or {}).get("name")
        if n:
            return str(n).replace("mcp__openclaw__", "")
    return ""


def _tool_use_ids(e):
    """tool_use ids this event opens (a tool_call) — for start→end matching."""
    d = _data(e)
    ids = []
    tcs = d.get("tool_calls")
    if isinstance(tcs, list):
        for tc in tcs:
            if isinstance(tc, dict) and tc.get("id"):
                ids.append(str(tc["id"]))
    return ids


def _tool_result_id(e):
    """tool_use id this tool_result closes (the join key)."""
    d = _data(e)
    ex = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    return ex.get("toolUseId") or ex.get("tool_use_id") or d.get("tool_use_id")


def _is_error(e):
    d = _data(e)
    ex = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    return bool(ex.get("isError") or d.get("isError") or d.get("is_error")
                or (e.get("event_type") or "").endswith("error"))


def _is_tool_call(e):
    """True for a tool-invocation event (NOT its result).

    Substring match on the v3 ``tool_call`` / ``tool.call`` names plus the
    multi-runtime ``data.tool_name`` / ``data.tool_calls`` shape — never an
    equality check against pre-v3 envelope names, so this can't silent-zero
    on a real v3 install (MOAT v3-shape gate)."""
    et = (e.get("event_type") or "").lower()
    if "tool_result" in et or "tool_use_result" in et:
        return False
    d = _data(e)
    if (d.get("role") or "").lower() == "tool":
        return False
    return bool("tool_call" in et or "tool.call" in et
                or d.get("tool_name") or d.get("tool_calls"))


def _is_tool_result(e):
    """True for a tool-result event (the closing half of the join)."""
    et = (e.get("event_type") or "").lower()
    if "tool_result" in et or "tool_use_result" in et:
        return True
    return (_data(e).get("role") or "").lower() == "tool"


# ── Provenance classification ───────────────────────────────────────────────

def _builtin_tool_set() -> set:
    """The OpenClaw sandbox builtin-tool universe, read from the DuckDB
    ``tool_policy`` table (mirrored from ``openclaw sandbox explain --json`` by
    the sync daemon). The union of every agent's ``allow`` list. Empty set when
    the policy hasn't been synced yet — callers then fall back to name shape
    only."""
    builtin: set = set()
    for r in _coerce_rows(_ls_call("query_tool_policy", limit=25)):
        allow = r.get("allow")
        if isinstance(allow, list):
            for n in allow:
                if n:
                    builtin.add(str(n).replace("mcp__openclaw__", ""))
    return builtin


def _classify(name: str, builtin: set):
    """Return ``(provenance, provider)`` for a tool name.

    ``mcp__<provider>__<tool>`` or any ``a__b`` → MCP (provider = the segment
    before ``__``); a name in the sandbox builtin universe → builtin; anything
    else → plugin/unknown. Name shape wins for MCP even when the policy lists
    it, because an ``__``-bearing name is unambiguously an MCP-namespaced tool.
    """
    if not name:
        return ("plugin", "")
    if "__" in name:
        parts = [p for p in name.split("__") if p]
        if name.startswith("mcp__"):
            provider = parts[1] if len(parts) > 1 else "mcp"
        else:
            provider = parts[0] if parts else "mcp"
        return ("mcp", provider)
    if name in builtin:
        return ("builtin", "")
    return ("plugin", "")


# ── Aggregation ─────────────────────────────────────────────────────────────

def _percentile(sorted_vals: list, p: float):
    """Linear-interpolated percentile (p in 0..100) over a SORTED list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return int(sorted_vals[0])
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    if f + 1 < len(sorted_vals):
        return int(sorted_vals[f] + (sorted_vals[f + 1] - sorted_vals[f]) * (k - f))
    return int(sorted_vals[f])


def _result_index(rows: list) -> dict:
    """Index every tool_result by the tool_use id it closes → {ts_ms, error}."""
    idx: dict = {}
    for e in rows:
        if not _is_tool_result(e):
            continue
        rid = _tool_result_id(e)
        if rid is None:
            continue
        idx[str(rid)] = {"ts": _ts_ms(e.get("ts")), "error": _is_error(e)}
    return idx


def _iter_tool_calls(rows: list, res_idx: dict):
    """Yield ``(name, ts_ms, duration_ms_or_None, is_error, session_id)`` for
    every tool_call, matching its result by tool_use id where present."""
    for e in rows:
        if not _is_tool_call(e):
            continue
        name = _tool_name(e)
        if not name:
            continue
        start = _ts_ms(e.get("ts"))
        ids = _tool_use_ids(e)
        dur = None
        err = _is_error(e)
        for tuid in ids:
            m = res_idx.get(str(tuid))
            if m:
                if m["error"]:
                    err = True
                if m["ts"] is not None and start is not None:
                    dur = max(0, m["ts"] - start)
                break
        yield (name, start, dur, err, (e.get("session_id") or ""))


# ── Endpoints ───────────────────────────────────────────────────────────────

@bp_tool_catalog.route("/api/tool-catalog")
def api_tool_catalog():
    """Per-tool rollup grouped by provenance.

    Returns ``{tools:[...], groups:{builtin,mcp,plugin}, totals, _source}``.
    Each tool row: ``{name, provenance, provider, calls, p50_ms, p95_ms,
    error_rate}``. Never 500s — an empty/unreadable store returns empty lists
    (HTTP 200) so the tab paints an honest "no tool calls recorded yet" state.

    Query params: ``limit`` (event scan window, <=5000), ``provenance``
    (filter to one of builtin/mcp/plugin).
    """
    try:
        limit = max(1, min(5000, int(request.args.get("limit", 5000))))
    except (TypeError, ValueError):
        limit = 5000
    prov_filter = (request.args.get("provenance") or "").strip().lower() or None

    rows = _coerce_rows(_ls_call("query_events", limit=limit))
    builtin = _builtin_tool_set()
    res_idx = _result_index(rows)

    agg: dict = {}
    for name, _start, dur, err, _sid in _iter_tool_calls(rows, res_idx):
        a = agg.setdefault(name, {"calls": 0, "durs": [], "errs": 0})
        a["calls"] += 1
        if dur is not None:
            a["durs"].append(dur)
        if err:
            a["errs"] += 1

    tools = []
    groups = {"builtin": 0, "mcp": 0, "plugin": 0}
    for name, a in agg.items():
        prov, provider = _classify(name, builtin)
        if prov_filter and prov != prov_filter:
            continue
        durs = sorted(a["durs"])
        calls = a["calls"]
        tools.append({
            "name": name,
            "provenance": prov,
            "provider": provider or None,
            "calls": calls,
            "p50_ms": _percentile(durs, 50),
            "p95_ms": _percentile(durs, 95),
            "error_rate": round(a["errs"] / calls, 4) if calls else 0.0,
            "errors": a["errs"],
            "timed_calls": len(durs),
        })
        if prov in groups:
            groups[prov] += 1

    # Busiest tool first; ties broken by slowest p95 then name (stable, useful).
    tools.sort(key=lambda t: (-t["calls"], -(t["p95_ms"] or 0), t["name"]))

    return jsonify({
        "tools": tools,
        "groups": groups,
        "totals": {
            "tool_count": len(tools),
            "total_calls": sum(t["calls"] for t in tools),
            "builtin_universe": len(builtin),
        },
        "_source": "local_store",
    })


@bp_tool_catalog.route("/api/tool-catalog/<path:name>/calls")
def api_tool_catalog_calls(name):
    """Recent individual calls for one tool (the drill-down).

    Returns ``{name, provenance, provider, calls:[...], _source}`` where each
    call is ``{ts_ms, duration_ms, status, session_id}`` — newest first — so
    the UI can expand a tool row into its per-call detail and link each call to
    its session transcript. Never 500s.

    Query params: ``limit`` (event scan window, <=5000); the call list is
    capped to the 100 most-recent invocations of this tool.
    """
    name = (name or "").strip().replace("mcp__openclaw__", "")
    if not name:
        return jsonify({"name": "", "calls": []}), 400
    try:
        limit = max(1, min(5000, int(request.args.get("limit", 5000))))
    except (TypeError, ValueError):
        limit = 5000

    rows = _coerce_rows(_ls_call("query_events", limit=limit))
    builtin = _builtin_tool_set()
    res_idx = _result_index(rows)

    calls = []
    for tname, start, dur, err, sid in _iter_tool_calls(rows, res_idx):
        if tname != name:
            continue
        calls.append({
            "ts_ms": start,
            "duration_ms": dur,
            "status": "error" if err else "ok",
            "session_id": sid or None,
        })
    # Newest first; cap so a hot tool can't return an unbounded list.
    calls.sort(key=lambda c: c["ts_ms"] or 0, reverse=True)
    calls = calls[:100]

    prov, provider = _classify(name, builtin)
    return jsonify({
        "name": name,
        "provenance": prov,
        "provider": provider or None,
        "calls": calls,
        "call_count": len(calls),
        "_source": "local_store",
    })
