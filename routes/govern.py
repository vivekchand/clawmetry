"""routes/govern.py — agent identity: a principal you can attach things to.

The Agent Inventory (``routes/inventory.py``) rolls up one row per *runtime*,
so ownership attaches to "claude_code on this box" rather than to an agent. That
is the gap under three separate capabilities:

* a policy cannot say *this agent may not do that* without a principal,
* RBAC has no subject to bind a role to,
* the audit chain has no actor beyond a session id.

One primitive unblocks all three, so it lands before any of them.

  GET  /api/govern/principals                   — the roster, one row per agent
  GET  /api/govern/principals/<principal_id>    — one principal
  POST /api/govern/principals/<principal_id>/owner
                                                — claim it for a person or team

Identity is **derived, not minted**: ``principal_id`` is a stable hash of
(node_id, runtime, agent_id), all of which ``sessions`` already carries. There
is no enrolment step to hang a generated id off -- ClawMetry watches agents
nobody instrumented -- so identity has to fall out of what we already observe.
It is therefore stable across restarts, reproducible in any process without a
lookup, and works retroactively on history already in the store.

Ownership writes reuse ``set_agent_meta`` keyed by the principal id. That
table's key is a free-form VARCHAR, so agent-level and runtime-level labels
coexist without a migration and without colliding. An agent with no label of
its own inherits its runtime's, reported honestly as ``owner_source:
"runtime"`` rather than pretending someone named this agent.

CLOUD CONTRACT: every handler never-raises and returns an honest empty shape
with HTTP 200 on the store-less cloud container, matching
``routes/inventory.py`` so a cold fall-through paints an empty state rather
than an error.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from clawmetry.config import is_local_store_read_enabled

logger = logging.getLogger("clawmetry.routes.govern")

bp_govern = Blueprint("govern", __name__)

# Read methods must open the store read-only in the single-process fallback.
_READ_METHODS = frozenset({"query_agent_principals", "query_agent_meta"})


def _store_call(method_name: str, **kwargs):
    """Daemon-proxy first, direct open as a single-process fallback.

    Same shape as ``routes/assets.py._try_store_call``: the daemon owns the
    DuckDB writer lock, so the dashboard process must never open it writable.
    Returns ``None`` when both paths fail.
    """
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=method_name in _READ_METHODS)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _zero():
    return {"principals": [], "total": 0}


@bp_govern.route("/api/govern/principals", methods=["GET"])
def api_govern_principals():
    """The agent roster, one row per agent rather than per runtime.

    Optional ``node_id`` / ``runtime`` filters, and ``limit`` (1-2000).
    Never raises; an empty roster is an honest 200, not a 500.
    """
    if not is_local_store_read_enabled():
        return jsonify(_zero())

    node_id = (request.args.get("node_id") or "").strip() or None
    runtime = (request.args.get("runtime") or "").strip().lower() or None
    if runtime == "all":
        runtime = None
    try:
        limit = max(1, min(2000, int(request.args.get("limit", 500))))
    except (TypeError, ValueError):
        limit = 500

    rows = _store_call(
        "query_agent_principals", node_id=node_id, runtime=runtime, limit=limit
    )
    rows = rows or []
    return jsonify({"principals": rows, "total": len(rows)})


@bp_govern.route("/api/govern/principals/<principal_id>", methods=["GET"])
def api_govern_principal(principal_id: str):
    """One principal by id, or 404.

    Filtered from the same derived roster rather than re-deriving it, so the
    detail view can never disagree with the list view.
    """
    if not is_local_store_read_enabled():
        return jsonify({"error": "not_found"}), 404
    pid = (principal_id or "").strip()
    if not pid:
        return jsonify({"error": "not_found"}), 404
    rows = _store_call("query_agent_principals", limit=2000) or []
    for r in rows:
        if r.get("principal_id") == pid:
            return jsonify(r)
    return jsonify({"error": "not_found"}), 404


@bp_govern.route("/api/govern/principals/<principal_id>/owner", methods=["POST"])
def api_govern_set_owner(principal_id: str):
    """Claim a principal for a person or team.

    Local-only: the write goes through the daemon proxy to the writer-locked
    DuckDB, and the cloud relay is read-only so it cold-falls-through.

    The id must name a principal we have actually observed. Accepting an
    arbitrary key would let this endpoint write unbounded rows into
    ``agent_meta`` and would let an owner be attached to an agent that does
    not exist -- an inventory nobody can trust is worse than none.

    ``owner``/``notes`` follow set_agent_meta's partial-update contract:
    ``None`` means "leave this field alone", an empty string clears it.
    """
    if not is_local_store_read_enabled():
        return jsonify({"ok": False, "error": "local store disabled"}), 200
    pid = (principal_id or "").strip()
    if not pid:
        return jsonify({"ok": False, "error": "missing principal_id"}), 400

    known = _store_call("query_agent_principals", limit=2000) or []
    if not any(r.get("principal_id") == pid for r in known):
        return jsonify({"ok": False, "error": "unknown principal"}), 404

    body = request.get_json(silent=True) or {}
    owner = body.get("owner")
    notes = body.get("notes")
    if owner is not None:
        owner = str(owner).strip()
    if notes is not None:
        notes = str(notes)
    if owner is None and notes is None:
        return jsonify({"ok": False, "error": "nothing to set"}), 400

    try:
        _store_call("set_agent_meta", agent_key=pid, owner=owner, notes=notes)
    except Exception:
        return jsonify({"ok": False, "error": "write failed"}), 200
    return jsonify({"ok": True, "principalId": pid, "owner": owner})
