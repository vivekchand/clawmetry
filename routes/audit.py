"""
routes/audit.py — Enterprise audit-log query endpoint.

Reads from the append-only :mod:`clawmetry.audit` store. Gated on the
``audit_logs`` entitlement (permissive during the open-core grace period,
Enterprise-only after enforce). Never raises.

  GET /api/audit-log?limit=200&event_type=X&since=<epoch>
    -> {"entries": [...], "event_types": [...], "count": N}
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.audit")

bp_audit = Blueprint("audit", __name__)


def _allowed() -> tuple[bool, dict]:
    try:
        from clawmetry import entitlements as _ent

        en = _ent.get_entitlement()
        return en.allows_feature("audit_logs"), en.to_dict()
    except Exception as exc:  # pragma: no cover
        logger.warning("audit: entitlement read failed, defaulting open: %s", exc)
        return True, {"tier": "oss", "grace": True}


@bp_audit.route("/api/audit-log", methods=["GET"])
def api_audit_log():
    ok, ent = _allowed()
    if not ok:
        return jsonify({
            "error": "upgrade_required",
            "feature": "audit_logs",
            "tier": ent.get("tier"),
            "hint": "Audit logs are an Enterprise feature. https://clawmetry.com/pricing",
        }), 402
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
