"""Stored node observations and typed, local-origin governance operations."""
import logging

from flask import Blueprint, jsonify, request

from clawmetry.node_activity import unavailable, validate_preferences
from helpers.node_store import store_is_authoritative

log = logging.getLogger("clawmetry.routes.node_activity")

bp_node_activity = Blueprint("node_activity", __name__)


def _call(method, **kwargs):
    from routes.local_query import local_store_via_daemon
    return local_store_via_daemon(method, **kwargs)


@bp_node_activity.get("/api/node-activity")
def api_node_activity():
    if not store_is_authoritative():
        return jsonify(unavailable("Select a connected node to read its encrypted observations."))
    try:
        body = _call("query_node_activity_live" if request.args.get("live") == "1" else "query_node_activity")
        if not isinstance(body, dict):
            raise RuntimeError("unavailable")
        return jsonify(body)
    except Exception as exc:
        log.warning("Node observations unavailable: %s", type(exc).__name__)
        return jsonify(unavailable("The node observation store is unavailable.")), 503


def _write_allowed():
    from routes.guard import _same_origin_ok
    return store_is_authoritative() and _same_origin_ok()


@bp_node_activity.post("/api/node-activity/preferences")
def api_node_activity_preferences():
    if not _write_allowed():
        return jsonify(ok=False, saved=False, message="Open this node to save monitoring options."), 403
    try:
        values = validate_preferences(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify(ok=False, saved=False, message=str(exc)), 400
    try:
        result = _call("set_node_activity_preferences", preferences=values)
        if not isinstance(result, dict) or result.get("saved") is not True:
            raise RuntimeError("unconfirmed")
        return jsonify(result)
    except Exception as exc:
        log.warning("Node monitoring options were not confirmed: %s", type(exc).__name__)
        return jsonify(ok=False, saved=False, message="Monitoring options were not confirmed as saved. Try again when the node is connected."), 503


@bp_node_activity.post("/api/node-activity/reviews")
def api_node_activity_reviews():
    if not _write_allowed():
        return jsonify(ok=False, saved=False, message="Open this node to save a review."), 403
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or set(body) - {"event_id", "decision", "reason"} or
            not isinstance(body.get("event_id"), str) or not 1 <= len(body["event_id"]) <= 128 or
            body.get("decision") not in ("expected", "investigate") or
            not isinstance(body.get("reason", ""), str) or len(body.get("reason", "")) > 300 or
            any(ord(c) < 32 for c in body.get("reason", ""))):
        return jsonify(ok=False, saved=False, message="Choose a recorded change and a valid review decision."), 400
    try:
        result = _call("review_node_activity_event", event_id=body["event_id"],
                       decision=body["decision"], reason=body.get("reason", ""))
        if not isinstance(result, dict) or result.get("saved") is not True:
            raise RuntimeError("unconfirmed")
        return jsonify(result)
    except Exception as exc:
        log.warning("Node review was not confirmed: %s", type(exc).__name__)
        return jsonify(ok=False, saved=False, message="The review was not confirmed as saved. The change may no longer be available."), 503
