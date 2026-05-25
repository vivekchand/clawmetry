"""routes/scheduler.py — OpenClaw run-ledger + queue-lane endpoints.

OpenClaw 2026.5.x records every background run — sub-agents
(``runtime='subagent'``), cron jobs (``runtime='cron'``) and inline
CLI/agent turns (``runtime='cli'``) — in a unified SQLite ledger at
``~/.openclaw/tasks/runs.sqlite``. The sync daemon mirrors it into the
DuckDB ``run_ledger`` table (``clawmetry/sync.py:sync_run_ledger``).

This module exposes that ledger so three observability surfaces share
one source of truth:

  GET /api/run-ledger          — lanes rollup + recent runs (Scheduler tab)
  GET /api/run-ledger/tree     — sub-agent fan-out tree (parent -> children)

``runtime`` IS the OpenClaw queue lane, so the lanes rollup is the live
queue/concurrency monitor (P0-1) and the sub-agent slice is the fan-out
tree (P0-2). Reads go through the daemon proxy (the daemon owns the
DuckDB writer lock) with a single-process direct-read fallback — the
same pattern as ``routes/agents.py``.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_scheduler = Blueprint("scheduler", __name__)


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


def _coerce_runs(rows) -> list[dict]:
    """``local_store_via_daemon`` returns the raw method result (a list) or a
    ``{"result": [...]}`` envelope depending on transport — normalise both."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


@bp_scheduler.route("/api/run-ledger")
def api_run_ledger():
    """Lane rollup + recent runs.

    Query params: ``runtime`` (lane filter), ``status``, ``limit`` (<=1000).
    Returns ``{lanes, runs, _source}``. Never 500s — an empty ledger (fresh
    sync, OpenClaw < 2026.5, or daemon mid-restart) returns empty lists so
    the tab renders an honest "no background runs yet" state.
    """
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 200))))
    except (TypeError, ValueError):
        limit = 200
    runtime = (request.args.get("runtime") or "").strip() or None
    status = (request.args.get("status") or "").strip() or None

    lanes = _coerce_runs(_ls_call("query_run_ledger_lanes"))
    runs = _coerce_runs(
        _ls_call("query_run_ledger", runtime=runtime, status=status, limit=limit)
    )
    return jsonify({
        "lanes": lanes,
        "runs": runs,
        "_source": "local_store",
    })


@bp_scheduler.route("/api/run-ledger/tree")
def api_run_ledger_tree():
    """Sub-agent fan-out tree.

    Groups ``runtime='subagent'`` runs under the session that requested them
    (``requester_session_key``), with explicit ``parent_task_id`` edges where
    OpenClaw set them (nested orchestrators). Each node carries status +
    timing so the UI can render depth, lane saturation and per-run outcome.
    """
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 300))))
    except (TypeError, ValueError):
        limit = 300

    subs = _coerce_runs(_ls_call("query_run_ledger", runtime="subagent", limit=limit))

    # Group by requesting session; nest explicit parent_task_id children.
    by_parent_task: dict[str, list] = {}
    roots_by_session: dict[str, list] = {}
    for r in subs:
        node = {
            "task_id": r.get("task_id"),
            "run_id": r.get("run_id"),
            "label": r.get("label") or (str(r.get("task") or "")[:60]),
            "task": str(r.get("task") or "")[:200],
            "status": r.get("status"),
            "delivery_status": r.get("delivery_status"),
            "terminal_outcome": r.get("terminal_outcome"),
            "child_session_key": r.get("child_session_key"),
            "agent_id": r.get("agent_id"),
            "created_at": r.get("created_at"),
            "started_at": r.get("started_at"),
            "ended_at": r.get("ended_at"),
            "error": r.get("error"),
            "children": [],
        }
        pt = r.get("parent_task_id")
        if pt:
            by_parent_task.setdefault(str(pt), []).append(node)
        else:
            sess = r.get("requester_session_key") or "unknown"
            roots_by_session.setdefault(str(sess), []).append(node)

    # Attach explicit nested children to their parent node where present.
    def _attach(nodes: list):
        for n in nodes:
            kids = by_parent_task.get(str(n["task_id"]))
            if kids:
                n["children"] = kids
                _attach(kids)

    for nodes in roots_by_session.values():
        _attach(nodes)

    tree = [
        {"session_key": sess, "runs": nodes}
        for sess, nodes in roots_by_session.items()
    ]
    # Newest session group first.
    tree.sort(
        key=lambda g: max((n.get("created_at") or 0) for n in g["runs"]),
        reverse=True,
    )
    return jsonify({"tree": tree, "count": len(subs), "_source": "local_store"})
