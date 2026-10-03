"""Apply encrypted acknowledgement on the owning node and confirm its state."""
import logging
import re
import time


def apply_acknowledgement(config, action):
    from clawmetry import local_store, sync
    result = {"ok": False, "applied": False}
    try:
        body = sync.decrypt_payload(action.get("sealed"), config.get("encryption_key"))
        if not isinstance(body, dict):
            raise TypeError("unreadable acknowledgement")
        requested = body.get("requested_at_ms")
        if type(requested) is not int or not -60_000 <= time.time() * 1000 - requested <= 600_000:
            raise ValueError("expired acknowledgement")
        incident_id, acknowledged = body.get("incident_id"), body.get("acknowledged")
        if (not isinstance(incident_id, str) or not re.fullmatch(r"inc_[0-9a-f]{32}", incident_id)
                or type(acknowledged) is not bool):
            raise ValueError("invalid acknowledgement")
        store = local_store.get_store()
        rows = store.query_incidents(incident_id=incident_id, node_id=config.get("node_id"), limit=1)
        if not config.get("node_id") or not rows:
            raise ValueError("finding unavailable on this node")
        incident = store.acknowledge_incident(incident_id=incident_id, acknowledged=acknowledged,
                                             requested_at_ms=requested)
        result = {"ok": True, "applied": bool(incident.get("acknowledged_at")) == acknowledged,
                  "incident": incident}
    except Exception as exc:  # noqa: BLE001 -- relay boundary must confirm failure without private payloads
        logging.getLogger(__name__).warning("Incident acknowledgement failed: %s", type(exc).__name__)
    sync._post_process_control_result(config, action, result)
