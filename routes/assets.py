"""routes/assets.py — Asset registry HTTP surface.

Evidence + review layer that turns individual agent discoveries (Self-Evolve
findings, useful prompts, improved skills) into reviewable, reusable assets
without auto-promoting unreviewed local changes to team/company defaults
(see issue #2201 + ``spec/asset-registry`` in the evotown adoption thread).

Endpoints (first slice):

  GET  /api/assets                  — list, newest first; ``status``,
                                       ``asset_type``, ``source_run_id``,
                                       ``source_session_id``, ``limit`` query
                                       params
  GET  /api/assets/<asset_id>       — single asset detail
  POST /api/assets                  — create / upsert a candidate asset
                                       (``id``, ``asset_type``, ``name``
                                       required; ``source_run_id``,
                                       ``source_session_id``, ``description``,
                                       ``content``, ``tags``, ``author``,
                                       ``team_id`` optional)
  POST /api/assets/<asset_id>/review — move status (`approve`/`reject`/
                                       `deprecate`); body: ``reviewer``,
                                       ``reason``

All reads + writes go through the daemon proxy (``local_store_via_daemon``)
so the dashboard process never opens DuckDB writable — same pattern as
``query_approvals`` / ``ingest_approval``. Auth is intentionally not enforced
in this first slice; the dashboard binds to localhost and the richer
review/promote console (with reviewer identity + audit) is the planned Pro
surface.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_assets = Blueprint("assets", __name__)


# Mirrors the lifecycle in the LocalStore (kept in sync — the daemon validates
# again, this is just a friendlier 400 at the API edge).
_VALID_TYPES = frozenset({
    "skill", "prompt", "workflow", "playbook",
    "memory_snippet", "tool_config", "evaluation_case",
})
_REVIEW_ACTIONS = {
    "approve": "approved",
    "approved": "approved",
    "reject": "rejected",
    "rejected": "rejected",
    "deprecate": "deprecated",
    "deprecated": "deprecated",
}


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback. Mirrors the
    helper used by routes/agents.py / routes/components.py."""
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


def _int_arg(name: str, default: int, *, lo: int, hi: int) -> int:
    try:
        v = int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


@bp_assets.route("/api/assets", methods=["GET"])
def list_assets():
    kwargs = {"limit": _int_arg("limit", 100, lo=1, hi=1000)}
    for key in ("status", "asset_type", "source_run_id", "source_session_id"):
        val = (request.args.get(key) or "").strip()
        if val:
            kwargs[key] = val
    rows = _ls_call("query_assets", **kwargs) or []
    return jsonify({"assets": rows, "count": len(rows)})


@bp_assets.route("/api/assets/<asset_id>", methods=["GET"])
def get_asset_detail(asset_id: str):
    row = _ls_call("get_asset", asset_id=asset_id)
    if not row:
        return jsonify({"error": f"asset {asset_id!r} not found"}), 404
    return jsonify(row)


@bp_assets.route("/api/assets", methods=["POST"])
def create_asset():
    data = request.get_json(silent=True) or {}
    aid = (data.get("id") or "").strip()
    atype = (data.get("asset_type") or "").strip()
    name = (data.get("name") or "").strip()
    if not aid:
        return jsonify({"error": "'id' is required"}), 400
    if atype not in _VALID_TYPES:
        return jsonify({
            "error": f"'asset_type' must be one of {sorted(_VALID_TYPES)}",
        }), 400
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    # Whitelist — refuse silently-ignored extras so callers learn the schema.
    allowed = {
        "id", "asset_type", "name", "description", "source_run_id",
        "source_session_id", "node_id", "author", "team_id", "version",
        "status", "tags", "content", "reviewer", "review_reason",
        "created_at",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    result = _ls_call("ingest_asset", asset=payload)
    if result is None and not _ls_call("get_asset", asset_id=aid):
        return jsonify({"error": "asset store unavailable"}), 503
    row = _ls_call("get_asset", asset_id=aid)
    return jsonify(row or {"id": aid, "status": "pending"}), 201


@bp_assets.route("/api/assets/<asset_id>/review", methods=["POST"])
def review_asset(asset_id: str):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or data.get("status") or "").strip().lower()
    status = _REVIEW_ACTIONS.get(action)
    if not status:
        return jsonify({
            "error": f"'action' must be one of {sorted(set(_REVIEW_ACTIONS))}",
        }), 400
    reviewer = (data.get("reviewer") or "").strip()
    reason = (data.get("reason") or "").strip()
    ok = _ls_call(
        "update_asset_status",
        asset_id=asset_id, status=status, reviewer=reviewer, reason=reason,
    )
    if not ok:
        return jsonify({"error": f"asset {asset_id!r} not found"}), 404
    row = _ls_call("get_asset", asset_id=asset_id)
    return jsonify(row or {"id": asset_id, "status": status})
