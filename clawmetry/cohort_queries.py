"""Store reads behind cohort compare and similar runs (WO-60).

The SQL lives here, in a leaf module, and ``LocalStore`` exposes it as two
thin methods (``query_cohort_sessions`` / ``query_similar_sessions``) so the
daemon proxy can serve both to the dashboard process. Everything is
bounded: a capped session scan, a capped candidate set for similarity, a
capped event walk per candidate, and no model call anywhere.

Optional tables are probed through ``information_schema`` at query time:
``signal_matches`` (behaviour signals, added by a parallel work order) and
``session_context`` (instructions-file hash). When absent the response says
so (``signals: "not available"``) rather than fabricating a zero rate.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

# Bounds. The sessions scan is the whole cohort universe for one request;
# the candidate cap keeps similarity inside the daemon budget.
SESSION_SCAN_LIMIT = 3000
SIMILAR_MAX_CANDIDATES = 120
SIMILAR_EVENTS_PER_SESSION = 300

# Event types that can carry a tool invocation (top-level tool events plus
# assistant turns whose content blocks hold tool_use entries).
_TOOL_BEARING_EVENT_TYPES = (
    "tool_call", "tool_use", "toolcall", "tool.call", "tool.invoked",
    "assistant", "message", "model.completed",
)


def _table_exists(store: Any, name: str) -> bool:
    try:
        rows = store._fetch(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_name = ? LIMIT 1", [name])
        return bool(rows)
    except Exception:
        return False


def _columns(store: Any, name: str) -> set[str]:
    try:
        rows = store._fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ?", [name])
        return {str(r[0]) for r in rows}
    except Exception:
        return set()


def _decode_meta(raw: Any) -> dict:
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            return {}
    elif isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return {}
    return raw if isinstance(raw, dict) else {}


def optional_tables(store: Any) -> dict:
    """Which optional inputs this store has. Cheap; probed per request."""
    return {
        "signal_matches": _table_exists(store, "signal_matches"),
        "session_context": _table_exists(store, "session_context"),
    }


def _signals_by_session(store: Any, session_ids: list[str]) -> dict[str, set]:
    """Behaviour signal names per session from ``signal_matches`` when the
    table exists and its column names can be resolved. Empty dict otherwise."""
    cols = _columns(store, "signal_matches")
    if "session_id" not in cols:
        return {}
    name_col = next((c for c in ("signal", "signal_id", "signal_name", "name", "kind")
                     if c in cols), None)
    if not name_col or not session_ids:
        return {}
    out: dict[str, set] = {}
    try:
        for i in range(0, len(session_ids), 500):
            chunk = session_ids[i:i + 500]
            ph = ",".join("?" * len(chunk))
            rows = store._fetch(
                f"SELECT session_id, {name_col} FROM signal_matches "
                f"WHERE session_id IN ({ph})", chunk)
            for sid, name in rows:
                if sid and name:
                    out.setdefault(str(sid), set()).add(str(name))
    except Exception:
        return {}
    return out


def _context_hash_by_session(store: Any, session_ids: list[str]) -> dict[str, str]:
    cols = _columns(store, "session_context")
    if "session_id" not in cols:
        return {}
    hash_col = next((c for c in ("instructions_hash", "instructions_sha", "context_hash", "hash")
                     if c in cols), None)
    if not hash_col or not session_ids:
        return {}
    out: dict[str, str] = {}
    try:
        for i in range(0, len(session_ids), 500):
            chunk = session_ids[i:i + 500]
            ph = ",".join("?" * len(chunk))
            rows = store._fetch(
                f"SELECT session_id, {hash_col} FROM session_context "
                f"WHERE session_id IN ({ph})", chunk)
            for sid, h in rows:
                if sid and h:
                    out[str(sid)] = str(h)
    except Exception:
        return {}
    return out


def cohort_sessions(store: Any, *, since: str | None = None,
                    until: str | None = None,
                    limit: int = SESSION_SCAN_LIMIT) -> list[dict]:
    """One row per session with everything the cohort math reads.

    Joins the guard tool-call counter and the git link table (both already
    maintained by the daemon) so steps and "finished" come from measured
    values where they exist. Rows carry ``signals`` only when the store has
    a ``signal_matches`` table, and ``instructions_hash`` only with
    ``session_context``.
    """
    clauses = [
        "s.session_id NOT LIKE 'nemoclaw-onboard-warmup-%'",
        "s.session_id NOT IN (SELECT subagent_id FROM subagents "
        "WHERE parent_session_id IS NOT NULL AND parent_session_id != '')",
    ]
    params: list[Any] = []
    if since:
        clauses.append("COALESCE(s.started_at, s.last_active_at, '') >= ?")
        params.append(str(since))
    if until:
        clauses.append("COALESCE(s.started_at, s.last_active_at, '') <= ?")
        params.append(str(until))
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        SELECT s.session_id, s.node_id, s.title, s.started_at, s.last_active_at,
               s.ended_at, s.status, s.cost_usd, s.total_tokens, s.metadata,
               s.outcome, s.cwd, s.git_branch, s.agent_type,
               g.tool_calls,
               (SELECT COUNT(*) FROM git_session_commits l
                 WHERE l.session_id = s.session_id) AS git_links
        FROM sessions s
        LEFT JOIN guard_session_stats g ON g.session_id = s.session_id
        {where}
        ORDER BY COALESCE(s.started_at, s.last_active_at, '') DESC
        LIMIT ?
    """
    params.append(int(max(1, min(int(limit), SESSION_SCAN_LIMIT))))
    cols = ["session_id", "node_id", "title", "started_at", "last_active_at",
            "ended_at", "status", "cost_usd", "total_tokens", "metadata",
            "outcome", "cwd", "git_branch", "agent_type", "tool_calls",
            "git_links"]
    out: list[dict] = []
    for r in store._fetch(sql, params):
        d = dict(zip(cols, r))
        d["metadata"] = _decode_meta(d.get("metadata"))
        links = d.pop("git_links", None)
        # Only claim a git basis when the repo scan has run for this session's
        # repo at all; otherwise the outcome label is the finishing signal.
        d["git_commits_linked"] = int(links) if links else None
        if d.get("tool_calls") is not None:
            d["tool_calls"] = int(d["tool_calls"])
        out.append(d)
    sids = [d["session_id"] for d in out]
    opt = optional_tables(store)
    if opt["signal_matches"]:
        sig = _signals_by_session(store, sids)
        for d in out:
            d["signals"] = sorted(sig.get(d["session_id"], ()))
    if opt["session_context"]:
        ctx = _context_hash_by_session(store, sids)
        for d in out:
            if d["session_id"] in ctx:
                d["instructions_hash"] = ctx[d["session_id"]]
    return out


def _tool_sequences(store: Any, session_ids: list[str],
                    per_session: int = SIMILAR_EVENTS_PER_SESSION) -> dict[str, list[str]]:
    """Ordered tool-name sequence per session from the events table."""
    from clawmetry.detectors import _iter_tool_calls_from_data

    if not session_ids:
        return {}
    ph = ",".join("?" * len(session_ids))
    tph = ",".join("?" * len(_TOOL_BEARING_EVENT_TYPES))
    sql = f"""
        SELECT session_id, event_type, data FROM (
            SELECT session_id, event_type, data, ts,
                   ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY ts) AS rn
            FROM events
            WHERE session_id IN ({ph}) AND event_type IN ({tph})
        ) WHERE rn <= ?
        ORDER BY session_id, ts
    """
    params: list[Any] = list(session_ids) + list(_TOOL_BEARING_EVENT_TYPES) + [int(per_session)]
    seqs: dict[str, list[str]] = {sid: [] for sid in session_ids}
    for sid, et, data in store._fetch(sql, params):
        payload = _decode_meta(data)
        for call in _iter_tool_calls_from_data(str(et or "").lower(), payload):
            name = call.get("tool")
            if isinstance(name, str) and name:
                seqs.setdefault(str(sid), []).append(name)
    return seqs


def similar_sessions(store: Any, *, session_id: str, window_days: int = 30,
                     limit: int = 10,
                     max_candidates: int = SIMILAR_MAX_CANDIDATES) -> dict:
    """Nearest sessions by tool-call shape inside a window.

    Candidates come from the same runtime first (session-id prefix), then
    other runtimes fill the remaining slots up to ``max_candidates``. The
    target's own tool stream decides coverage: a runtime that exposes no
    tool calls reports ``coverage`` and an empty list, never a fake match.
    """
    from clawmetry.cohort_compare import similar_by_shape

    sid = str(session_id or "").strip()
    if not sid:
        return {"session_id": "", "neighbours": [], "coverage": "session id required"}
    prefix = sid.split(":", 1)[0] if ":" in sid else "openclaw"
    days = max(1, min(int(window_days or 30), 365))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")

    target_seq = _tool_sequences(store, [sid]).get(sid, [])
    if not target_seq:
        return {
            "session_id": sid, "runtime": prefix, "window_days": days,
            "neighbours": [], "candidates": 0, "tool_calls": 0,
            "coverage": f"no tool stream exposed by {prefix}",
        }

    cap = max(1, min(int(max_candidates), SIMILAR_MAX_CANDIDATES))
    like = f"{prefix}:%"
    rows = store._fetch(
        """
        SELECT session_id, title, cost_usd, outcome, metadata, started_at
        FROM sessions
        WHERE session_id != ?
          AND COALESCE(last_active_at, started_at, '') >= ?
          AND session_id NOT LIKE 'nemoclaw-onboard-warmup-%'
        ORDER BY (CASE WHEN session_id LIKE ? THEN 0 ELSE 1 END),
                 COALESCE(last_active_at, started_at, '') DESC
        LIMIT ?
        """,
        [sid, since, like, cap],
    )
    meta_by: dict[str, dict] = {}
    for r in rows:
        meta = _decode_meta(r[4])
        rt = str(meta.get("runtime") or "").strip() or (
            r[0].split(":", 1)[0] if ":" in r[0] else "openclaw")
        meta_by[r[0]] = {
            "title": r[1] or "", "cost_usd": float(r[2] or 0.0),
            "outcome": r[3] or "unknown", "runtime": rt,
            "model": str(meta.get("model") or meta.get("recent_model") or ""),
            "started_at": r[5] or "",
        }
    seqs = _tool_sequences(store, list(meta_by))
    ranked = similar_by_shape(target_seq, seqs, limit=limit)
    neighbours = []
    for n in ranked:
        m = meta_by.get(n["session_id"], {})
        neighbours.append({**n, **m})
    return {
        "session_id": sid, "runtime": prefix, "window_days": days,
        "tool_calls": len(target_seq), "candidates": len(meta_by),
        "neighbours": neighbours,
        "coverage": "tool stream" if neighbours or meta_by else "no other sessions in window",
    }
