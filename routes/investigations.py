"""Guard investigations backed by the shared encrypted query contract."""
import logging
import re

from flask import Blueprint, jsonify, request

from clawmetry.investigations import current_incident
from routes.local_query import _dispatch

log = logging.getLogger("clawmetry.investigations")
bp_investigations = Blueprint("investigations", __name__)


def _unavailable():
    return jsonify({"available": False, "error": "Investigation data is unavailable from this node.",
                    "coverage": {"node_reachable": False}}), 503


@bp_investigations.get("/api/guard/incidents")
def incidents():
    try:
        body = _dispatch("incidents", request.args.to_dict())
        body["rows"] = [current_incident(row) for row in body.get("rows", [])]
        return jsonify(dict(body, available=True))
    except ValueError:
        return jsonify({"error": "Invalid incident filters."}), 400
    except Exception:
        log.warning("Incident history read unavailable", exc_info=True)
        return _unavailable()


@bp_investigations.get("/api/investigation")
def investigation():
    try:
        return jsonify(dict(_dispatch("investigation", request.args.to_dict()), available=True))
    except ValueError:
        return jsonify({"error": "Choose a session, runtime and node to investigate."}), 400
    except Exception:
        log.warning("Investigation read unavailable", exc_info=True)
        return _unavailable()


@bp_investigations.post("/api/guard/incidents/<incident_id>/acknowledge")
def acknowledge(incident_id):
    from routes.guard import _same_origin_ok
    if not _same_origin_ok():
        return jsonify({"error": "Request origin does not match."}), 403
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or type(body.get("acknowledged")) is not bool
            or not re.fullmatch(r"inc_[0-9a-f]{32}", incident_id)):
        return jsonify({"error": "Provide an incident and an acknowledged boolean."}), 400
    try:
        from routes.local_query import PROXY_UNAVAILABLE, local_store_call_via_daemon
        kwargs = {"incident_id": incident_id, "acknowledged": body["acknowledged"]}
        result = local_store_call_via_daemon("acknowledge_incident", **kwargs)
        if result is PROXY_UNAVAILABLE:
            from clawmetry.local_store import get_store
            result = get_store().acknowledge_incident(**kwargs)
        if result is None:
            return jsonify({"error": "This incident is not available."}), 404
        return jsonify({"available": True, "incident": current_incident(result)})
    except Exception:
        log.warning("Incident acknowledgement unavailable", exc_info=True)
        return _unavailable()
