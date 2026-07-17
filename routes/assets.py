"""routes/assets.py — OSS asset registry API.

Basic CRUD + review workflow over the ``assets`` DuckDB table.
All storage-layer plumbing (table, LocalStore methods, daemon-proxy
allowlist) lives in the OSS ``local_store.py`` / ``local_query.py``.
These routes expose that plumbing to dashboard users when
``clawmetry-pro`` is NOT installed; when Pro is installed its own
blueprint registers via the ``clawmetry.extensions`` entry point and
``dashboard.py`` skips registering this one.
"""
from __future__ import annotations

import logging
import uuid

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

logger = logging.getLogger("clawmetry.routes.assets")

bp_assets = Blueprint("assets", __name__)

_ASSET_TYPES = frozenset({
    "skill", "prompt", "workflow", "playbook",
    "memory_snippet", "tool_config", "evaluation_case",
})

# Maps the user-facing review action to the DuckDB status string.
_REVIEW_ACTION_TO_STATUS = {"approve": "approved", "reject": "rejected"}

# Methods that must open the store read-only in the direct fallback path.
_READ_METHODS = frozenset({"query_assets", "get_asset"})


def _try_store_call(method_name: str, **kwargs):
    """Route a LocalStore call through the daemon proxy first.

    Falls back to a direct DuckDB open for single-process boots (dev
    mode, tests). Matches the pattern in routes/hitl.py._try_store_call.
    Returns the method's return value, or None when both paths fail.
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


@bp_assets.route("/api/assets", methods=["GET"])
@gate("asset_registry")
def list_assets():
    """List assets newest-first.

    Query params: status, asset_type, source_session_id, limit (1–500).
    """
    status = (request.args.get("status") or "").strip() or None
    asset_type = (request.args.get("asset_type") or "").strip() or None
    source_session_id = (
        request.args.get("source_session_id") or ""
    ).strip() or None
    try:
        limit = max(1, min(500, int(request.args.get("limit", 100))))
    except (ValueError, TypeError):
        limit = 100

    assets = _try_store_call(
        "query_assets",
        status=status,
        asset_type=asset_type,
        source_session_id=source_session_id,
        limit=limit,
    )
    assets = assets or []
    return jsonify({"assets": assets, "count": len(assets)})


@bp_assets.route("/api/assets/<asset_id>", methods=["GET"])
@gate("asset_registry")
def get_asset(asset_id: str):
    """Return one asset by id, or 404."""
    asset = _try_store_call("get_asset", asset_id=asset_id)
    if asset is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(asset)


@bp_assets.route("/api/assets", methods=["POST"])
@gate("asset_registry")
def create_asset():
    """Create or upsert an asset.

    Required body fields: ``asset_type`` (one of the canonical types),
    ``name`` (non-empty string). All other fields are optional.
    """
    body = request.get_json(silent=True) or {}
    asset_type = (body.get("asset_type") or "").strip()
    if asset_type not in _ASSET_TYPES:
        return jsonify(
            {"error": f"asset_type must be one of {sorted(_ASSET_TYPES)}"}
        ), 400
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    asset = {
        "id": (body.get("id") or "").strip() or str(uuid.uuid4()),
        "asset_type": asset_type,
        "name": name,
        "description": body.get("description") or "",
        "source_session_id": body.get("source_session_id") or "",
        "source_run_id": body.get("source_run_id") or "",
        "author": body.get("author") or "",
        "tags": body.get("tags"),
        "content": body.get("content"),
        "status": body.get("status") or "pending",
    }
    _try_store_call("ingest_asset", asset=asset)
    return jsonify({"ok": True, "id": asset["id"], "status": asset["status"]}), 201


@bp_assets.route("/api/assets/<asset_id>/review", methods=["POST"])
@gate("asset_registry")
def review_asset(asset_id: str):
    """Approve or reject an asset.

    Body: ``{"action": "approve"|"reject", "reviewer"?: str, "reason"?: str}``.
    Returns 404 when the asset does not exist.
    """
    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip().lower()
    if action not in _REVIEW_ACTION_TO_STATUS:
        return jsonify(
            {"error": "action must be 'approve' or 'reject'"}
        ), 400

    new_status = _REVIEW_ACTION_TO_STATUS[action]
    updated = _try_store_call(
        "update_asset_status",
        asset_id=asset_id,
        status=new_status,
        reviewer=body.get("reviewer") or "",
        reason=body.get("reason") or "",
    )
    # update_asset_status returns False when the asset_id does not exist.
    if updated is False:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"ok": True, "asset_id": asset_id, "status": new_status})
