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


def _arg_preview(args) -> str:
    """Short single-line preview of tool-call arguments — never the full body."""
    if args is None:
        return ""
    if isinstance(args, dict):
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

    return jsonify(_approvals_audit_payload(status=status, limit=limit))


@bp_policy.route("/api/approvals")
def api_approvals_queue():
    """Pending approvals queue — compact format for mobile/remote clients.

    Returns {approvals:[...], count:int, _source}. Each entry carries
    action_token (the id a remote client uses to POST an approve/deny decision
    to the cloud) plus a short args_preview so mobile UI can show context.

    Query params: limit (<=100, default 50).
    """
    try:
        limit = max(1, min(100, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    rows = _coerce_rows(_ls_call("query_approvals", status="pending", limit=limit))
    approvals = [
        {
            "id":                   r.get("id"),
            "action_token":         r.get("id"),
            "action":               r.get("action"),
            "status":               r.get("status") or "pending",
            "created_at":           r.get("created_at"),
            "requestor_session_id": r.get("requestor_session_id"),
            "args_preview":         _arg_preview(r.get("args")),
        }
        for r in rows
    ]
    return jsonify({"approvals": approvals, "count": len(approvals), "_source": "local_store"})


def _approvals_audit_payload(status=None, limit=100):
    """Exec-approval decision audit payload, shared by the HTTP route and the
    cloud snapshot builder (trial-bug #22: the Policy tab audit was blank on the
    hosted dashboard). Returns {decisions, summary, _source}."""
    rows = _coerce_rows(_ls_call("query_approvals", status=status, limit=limit))

    decisions = []
    pending = approved = denied = simulated = 0
    for r in rows:
        st = (r.get("status") or "pending")
        dec = (r.get("decision") or "")
        if st == "simulated":
            # Monitor-mode (dry-run) policies record what WOULD have paused.
            simulated += 1
        elif st == "pending":
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
        "simulated": simulated,
    }
    return {"decisions": decisions, "summary": summary, "_source": "local_store"}


@bp_policy.route("/api/policy/replay", methods=["POST"])
def api_policy_replay():
    """Replay a CANDIDATE approval policy over recent tool-call history.

    The "eval before you enable" loop: before saving a rule, see what it
    would have paused over the last N days, across every runtime. Nothing is
    created, blocked, or sent to the cloud; this is a pure read.

    Body: ``{policy: {...}, days: int (default 14, max 30),
             limit: int (default 5000, max 10000)}``
    ``policy`` uses the same shape as ``~/.clawmetry/policies.yml`` rows or
    cloud-builder rows (``tool`` / ``match.command_regex`` / ...).

    Returns the ``clawmetry.approvals.replay_policy`` payload plus
    ``days`` + ``since``. Invalid input returns 400 with ``{ok: False}``;
    an empty store returns an honest all-zeros payload, never a 500.
    """
    body = request.get_json(silent=True) or {}
    policy = body.get("policy")
    if not isinstance(policy, dict) or not policy:
        return jsonify({"ok": False,
                        "error": "body must include a 'policy' object"}), 400
    try:
        days = max(1, min(30, int(body.get("days", 14))))
    except (TypeError, ValueError):
        days = 14
    try:
        limit = max(100, min(10000, int(body.get("limit", 5000))))
    except (TypeError, ValueError):
        limit = 5000

    import time as _time
    since = _time.strftime("%Y-%m-%dT%H:%M:%SZ",
                           _time.gmtime(_time.time() - days * 86400))
    # Same merged-event_type read as the live watcher: import the SHARED
    # list from approvals so replay and enforcement cannot drift (a replay
    # that scans different event types than the watcher would "predict"
    # pauses the watcher never fires, or miss ones it does).
    try:
        from clawmetry.approvals import replay_policy, _TOOL_EVENT_TYPES
    except Exception as e:
        return jsonify({"ok": False, "error": f"approvals engine unavailable: {e}"}), 500
    rows: list[dict] = []
    for et in _TOOL_EVENT_TYPES:
        rows.extend(_coerce_rows(
            _ls_call("query_events", event_type=et, since=since, limit=limit)))

    try:
        result = replay_policy(policy, rows)
    except Exception as e:
        result = {"ok": False, "error": f"replay failed: {e}"}
    result["days"] = days
    result["since"] = since
    return jsonify(result), (200 if result.get("ok") else 400)
