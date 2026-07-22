"""routes/inventory.py — Agent Inventory tab API.

A single-pane control-tower roster of every agent on the node: what it runs,
what it costs, whether it is alive, and who owns it. One row per runtime (the
``_runtime_of_session`` prefix bucket; ``openclaw`` is always present as the
default bucket), enriched with the local owner label.

  GET  /api/inventory                  — the node-wide roster (or a single
                                         runtime's row when ?runtime=<rt> is set)
  POST /api/inventory/<agent_key>/owner — set the owner/notes label (local only)

The roster is composed from the SAME rollups the daemon ships in the snapshot
(``sync._build_runtime_summary`` + ``sync._build_agent_inventory``), so the
local dashboard and the hosted dashboard render identical numbers. Reads go
through the daemon proxy (``local_store_via_daemon``) so the dashboard process
never opens the writer-locked DuckDB.

CLOUD CONTRACT: this handler MUST never-raise and return
``{"agents": [], "total": 0}`` HTTP 200 on the store-less cloud container, so
the ``cm-cloud-inventory`` interceptor can cold-fall-through to it gracefully
(no silent blank card). The interceptor serves the real data from the snapshot
slice; this handler is the cold floor.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_inventory = Blueprint("inventory", __name__)


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088).

    Copied from routes/agents.py so the inventory route stays decoupled from
    dashboard.py."""
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


def _zero():
    return {"agents": [], "total": 0}


def _daemon_running() -> bool:
    try:
        from routes.local_query import _cached_discovery
        return _cached_discovery() is not None
    except Exception:
        return False


def _detected_runtimes() -> list:
    try:
        from clawmetry.adapters import registry
        return [
            r.to_dict()
            for r in registry.detect_all()
            if getattr(r, "detected", False)
        ]
    except Exception:
        return []


def _build_local_inventory():
    """Compose the node-wide roster locally, reusing the daemon's builder so the
    shape matches the snapshot byte-for-byte. Never raises; returns the
    node-wide dict (``{nodeId, agents, nodeWideToolGroups, nodeWideEval,
    total}``) or ``None`` when there is no store to read."""
    try:
        from clawmetry import sync as _sync
    except Exception:
        return None

    try:
        runtime_summary = _sync._build_runtime_summary() or {}
    except Exception:
        runtime_summary = {}
    if not isinstance(runtime_summary, dict):
        runtime_summary = {}

    # Per-runtime outcome + activity, same helpers the snapshot uses.
    outcomes_by_rt: dict = {}
    activity_by_rt: dict = {}
    for rt in list(runtime_summary.keys()):
        try:
            o = _sync._outcomes_slice_for_snapshot(runtime=rt)
            if o:
                outcomes_by_rt[rt] = o
            a = _sync._collect_activity_counters_today(runtime=rt)
            if a:
                activity_by_rt[rt] = a
        except Exception:
            continue

    # Detected family runtimes (display name / running / workspace).
    try:
        from clawmetry.adapters import registry
        detected = [
            r.to_dict() for r in registry.detect_all()
            if getattr(r, "detected", False)
        ]
    except Exception:
        detected = []

    # Node-wide tool provenance + eval summary (header strip, NOT per-row).
    tool_groups = {}
    eval_summary = {}
    try:
        tc = _sync._build_tool_catalog_slice() or {}
        tool_groups = tc.get("groups", {}) or {}
    except Exception:
        tool_groups = {}
    try:
        es = _ls_call("query_eval_summary", window_hours=24)
        eval_summary = es if isinstance(es, dict) else {}
    except Exception:
        eval_summary = {}

    # Owner labels (local DuckDB) + node id.
    agent_meta = _ls_call("query_agent_meta") or {}
    if not isinstance(agent_meta, dict):
        agent_meta = {}
    node_id = ""
    try:
        from clawmetry import local_store
        node_id = local_store.get_store(read_only=True)._node_id()
    except Exception:
        node_id = ""

    try:
        node_wide, _by_rt = _sync._build_agent_inventory(
            runtime_summary,
            outcomes_by_rt,
            activity_by_rt,
            tool_groups,
            eval_summary,
            detected,
            agent_meta,
            node_id,
        )
        return node_wide
    except Exception:
        return None


@bp_inventory.route("/api/inventory")
def api_inventory():
    """Agent-Inventory roster. Never-raises; returns ``{agents:[],total:0}`` HTTP
    200 when there is no local store (the cloud cold-fallthrough contract)."""
    # Store-less / cloud: honest zero, HTTP 200 (NOT a 500).
    if not is_local_store_read_enabled():
        return jsonify(_zero())

    try:
        node_wide = _build_local_inventory()
    except Exception:
        node_wide = None
    if not node_wide or not isinstance(node_wide, dict) or not node_wide.get("agents"):
        # Local store enabled but roster empty — surface detected runtimes so
        # the UI can render an honest "daemon not ingesting yet" state instead
        # of the misleading "No agents yet" copy (issue #3917).
        detected = _detected_runtimes()
        if detected:
            return jsonify({
                "agents": [],
                "total": 0,
                "detectedRuntimes": detected,
                "daemonRunning": _daemon_running(),
            })
        return jsonify(_zero())

    # Per-runtime no-leak: when a specific runtime is requested, return ONLY
    # that runtime's row (or zero), never the node-wide set.
    rt = (request.args.get("runtime") or "").strip().lower()
    if rt and rt != "all":
        for a in node_wide.get("agents", []):
            if a.get("agentKey") == rt:
                out = {
                    "nodeId": node_wide.get("nodeId", ""),
                    "agents": [a],
                    "total": 1,
                }
                return jsonify(out)
        return jsonify(_zero())

    return jsonify(node_wide)


@bp_inventory.route("/api/inventory/<agent_key>/owner", methods=["POST"])
def api_inventory_set_owner(agent_key: str):
    """Set the owner (and optional note) label for a runtime. Local-only: the
    write goes through the daemon proxy to the writer-locked DuckDB; cloud
    cold-falls-through (the cloud relay is read-only)."""
    if not is_local_store_read_enabled():
        return jsonify({"ok": False, "error": "local store disabled"}), 200
    key = (agent_key or "").strip().lower()
    if not key:
        return jsonify({"ok": False, "error": "missing agent_key"}), 400
    body = request.get_json(silent=True) or {}
    owner = body.get("owner")
    notes = body.get("notes")
    # Normalise empty owner to a stored empty string (client renders "me");
    # None means "don't touch" so a notes-only update keeps the owner.
    if owner is not None:
        owner = str(owner).strip()
    if notes is not None:
        notes = str(notes)
    try:
        _ls_call("set_agent_meta", agent_key=key, owner=owner, notes=notes)
    except Exception:
        return jsonify({"ok": False, "error": "write failed"}), 200
    return jsonify({"ok": True, "agentKey": key, "owner": owner})
