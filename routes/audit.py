"""
routes/audit.py — Enterprise audit-log query endpoint.

Reads from the append-only :mod:`clawmetry.audit` store. Gated on the
``audit_logs`` entitlement (permissive during the open-core grace period,
Enterprise-only after enforce). Never raises.

Gating: the route uses the shared :func:`clawmetry._gate.gate` decorator
so the 402 body carries the same ``feature`` / ``tier`` / ``required_tier``
envelope every other paid-feature route returns. Callers who used to read
``feature`` and ``required_tier`` off other 402 responses now get the same
shape here.

  GET /api/audit-log?limit=200&event_type=X&since=<epoch>
    -> {"entries": [...], "event_types": [...], "count": N}
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

logger = logging.getLogger("clawmetry.routes.audit")

bp_audit = Blueprint("audit", __name__)


@bp_audit.route("/api/audit-log", methods=["GET"])
@gate("audit_logs")
def api_audit_log():
    """Query the append-only audit log. Enterprise entitlement-gated via
    the shared :func:`clawmetry._gate.gate` decorator; permissive during
    the open-core grace period. Never raises."""
    try:
        from clawmetry import audit as _audit

        try:
            limit = max(1, min(int(request.args.get("limit", 200) or 200), 5000))
        except Exception:
            limit = 200
        event_type = request.args.get("event_type") or None
        since_raw = request.args.get("since")
        since = float(since_raw) if since_raw else None

        entries = _audit.read_audit_log(limit=limit, event_type=event_type, since=since)
        return jsonify({
            "entries": entries,
            "event_types": _audit.event_types(),
            "count": len(entries),
        })
    except Exception as exc:  # never break the dashboard over a read
        logger.warning("api_audit_log: degraded: %s", exc)
        return jsonify({"entries": [], "event_types": [], "count": 0})
