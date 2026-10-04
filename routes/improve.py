"""Read-only guidance evidence, shared with the encrypted daemon snapshot."""
from __future__ import annotations

import logging
import os
import sys
from flask import Blueprint, jsonify, request

from clawmetry.improve_candidates import _build_candidates, unavailable  # compatibility for callers/tests

bp_improve = Blueprint("improve", __name__)
_LOGGER = logging.getLogger(__name__)


def _store_call(method_name: str, **kwargs):
    # get_store returns the daemon proxy when another process owns the writer.
    from clawmetry import local_store
    return getattr(local_store.get_store(read_only=True), method_name)(**kwargs)


def _window_days() -> int:
    raw = (request.args.get("window") or request.args.get("days") or "30").strip().lower().rstrip("d")
    try:
        return min(90, max(1, int(raw)))
    except (TypeError, ValueError):
        return 30


@bp_improve.route("/api/improve/candidates", methods=["GET"])
def get_improve_candidates():
    days = _window_days()
    runtime = request.args.get("runtime") or None
    node_id = request.args.get("node_id") or None
    # Hosted fallback must never inspect this container's local store. The
    # browser interceptor serves the node's encrypted snapshot in normal use.
    dashboard = sys.modules.get("dashboard")
    if (os.environ.get("CLAWMETRY_CLOUD", "").strip()
            or os.environ.get("CLOUD_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
            or getattr(dashboard, "CLOUD_MODE", False)
            or getattr(sys.modules.get("config"), "CLOUD_MODE", False)):
        body = unavailable(days=days, runtime=runtime, node_id=node_id)
        body["reason"] = "missing_snapshot"
        return jsonify(body), 200
    try:
        result = _store_call("query_improve_candidates", window_days=days,
                             runtime=runtime, node_id=node_id)
        if not isinstance(result, dict):
            raise RuntimeError("candidate query unavailable")
        status = {"locked": 402, "unavailable": 503, "invalid_scope": 400}.get(result.get("state"), 200)
        return jsonify(result), status
    except Exception:
        _LOGGER.warning("Improve candidate query unavailable", exc_info=False)
        return jsonify(unavailable(days=days, runtime=runtime, node_id=node_id)), 503
