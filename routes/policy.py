"""routes/policy.py — tool-policy + sandbox + exec-approval audit (PRD P1-1).

This is the governance surface (our moat): "which tools can run, where they
run, and what got blocked/approved and why."

Two read-only endpoints, both backed by DuckDB through the daemon proxy
(the daemon owns the writer lock) with a single-process direct-read fallback
— the same ``_ls_call`` pattern as ``routes/agents.py`` / ``routes/scheduler.py``:

  GET /api/tool-policy      — per-agent effective sandbox mode + tool
                              allow/deny, mirrored from
                              ``openclaw sandbox explain --json``
                              (``clawmetry/sync.py:sync_tool_policy``).
  GET /api/approvals-audit  — exec-approval decisions (approved / denied /
                              pending) from the approvals table, summarised
                              into a decision rollup + recent decisions feed.

Neither endpoint ever 500s on empty data: a fresh sync, an OpenClaw build
without ``sandbox explain``, or a daemon mid-restart all return empty lists so
the tab paints an honest "nothing recorded yet" state.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_policy = Blueprint("policy", __name__)


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


def _coerce_rows(rows) -> list[dict]:
    """``local_store_via_daemon`` returns the raw method result (a list) or a
    ``{"result": [...]}`` / ``{"rows": [...]}`` envelope depending on transport
    — normalise both to a plain list."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


@bp_policy.route("/api/tool-policy")
def api_tool_policy():
    """Per-agent effective sandbox mode + tool allow/deny.

    Returns ``{agents:[...], summary:{...}, _source}``. Each agent row carries
    the sandbox mode (``off`` / ``non-main`` / ``all``), scope, workspace
    access, and the effective tool ``allow`` / ``deny`` lists with their
    config provenance (``sources``). The summary rolls up how many agents are
    sandboxed and the most-restricted mode seen, so the UI can show a
    one-glance governance posture chip.

    Query params: ``agent_id`` (filter to one agent), ``limit`` (<=100).
    """
    try:
        limit = max(1, min(100, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    agent_id = (request.args.get("agent_id") or "").strip() or None

    agents = _coerce_rows(_ls_call("query_tool_policy", agent_id=agent_id, limit=limit))

    # Governance posture rollup. ``mode`` ordering: all > non-main > off
    # (most → least restrictive). We surface the most-restrictive mode in use
    # plus how many agents run with a non-off sandbox.
    _MODE_RANK = {"all": 3, "non-main": 2, "nonmain": 2, "off": 1}
    sandboxed = 0
    strongest = None
    strongest_rank = 0
    total_allow = 0
    total_deny = 0
    for a in agents:
        mode = (a.get("sandbox_mode") or "off")
        if mode and mode != "off":
            sandboxed += 1
        rank = _MODE_RANK.get(str(mode), 0)
        if rank > strongest_rank:
            strongest_rank = rank
            strongest = mode
        total_allow += int(a.get("allow_count") or 0)
        total_deny += int(a.get("deny_count") or 0)

    summary = {
        "agent_count": len(agents),
        "sandboxed_agents": sandboxed,
        "strongest_mode": strongest or ("off" if agents else None),
        "total_allowed_tools": total_allow,
        "total_denied_tools": total_deny,
    }
    return jsonify({"agents": agents, "summary": summary, "_source": "local_store"})


@bp_policy.route("/api/approvals-audit")
def api_approvals_audit():
    """Exec-approval decision audit — what got approved / denied / is pending.

    Returns ``{decisions:[...], summary:{...}, _source}``. Each decision row is
    a normalised slice of an approvals-table row (the heavy ``args`` BLOB is
    reduced to a short preview so the audit feed can't bloat). The summary
    counts pending / approved / denied so the UI can render a posture bar.

    Query params: ``status`` (filter), ``limit`` (<=300).
    """
    try:
        limit = max(1, min(300, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    status = (request.args.get("status") or "").strip() or None

    rows = _coerce_rows(_ls_call("query_approvals", status=status, limit=limit))

    def _arg_preview(args) -> str:
        """A short, single-line preview of the tool-call arguments — never the
        full body (avoids snapshot/response bloat)."""
        if args is None:
            return ""
        if isinstance(args, dict):
            # exec-style calls usually carry a command; surface it first.
            for k in ("command", "cmd", "tool", "path", "url"):
                v = args.get(k)
                if v:
                    return str(v)[:160]
            try:
                import json as _json
                return _json.dumps(args, separators=(",", ":"))[:160]
            except Exception:
                return str(args)[:160]
        return str(args)[:160]

    decisions = []
    pending = approved = denied = 0
    for r in rows:
        st = (r.get("status") or "pending")
        dec = (r.get("decision") or "")
        if st == "pending":
            pending += 1
        elif st in ("approved", "allow", "allowed") or dec in ("approve", "allow"):
            approved += 1
        elif st in ("denied", "deny", "blocked", "rejected") or dec in ("deny", "block"):
            denied += 1
        decisions.append({
            "id": r.get("id"),
            "action": r.get("action"),
            "args_preview": _arg_preview(r.get("args")),
            "status": st,
            "decision": dec or None,
            "decision_reason": (str(r.get("decision_reason"))[:300]
                                if r.get("decision_reason") else None),
            "resolver": r.get("resolver"),
            "requestor_session_id": r.get("requestor_session_id"),
            "created_at": r.get("created_at"),
            "resolved_at": r.get("resolved_at"),
        })

    summary = {
        "total": len(decisions),
        "pending": pending,
        "approved": approved,
        "denied": denied,
    }
    return jsonify({"decisions": decisions, "summary": summary, "_source": "local_store"})
