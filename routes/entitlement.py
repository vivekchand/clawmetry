"""
routes/entitlement.py — ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth — handlers never re-derive tier logic here.

  GET /api/entitlement — the current Entitlement as JSON.

Side-effect-free and never-raise, so it is safe to classify ``oss-passthrough``
on the cloud side: when no license/cloud plan is present it returns a graceful
OSS-free shape, never a 4xx.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.entitlement")

bp_entitlement = Blueprint("entitlement", __name__)


@bp_entitlement.route("/api/entitlement")
def api_entitlement():
    """Return the resolved entitlement. Falls back to an OSS-free shape on any
    error so the UI always has something safe to render."""
    try:
        from clawmetry import entitlements as _ent

        return jsonify(_ent.get_entitlement().to_dict())
    except Exception as exc:  # never crash the dashboard over a gate read
        logger.warning("api_entitlement: falling back to OSS-free: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "source": "oss",
                "node_limit": 1,
                "expiry": None,
                "expired": False,
                "is_paid": False,
                "grace": True,
                "enforced": False,
                "runtimes": ["openclaw"],
                "features": [],
            }
        )
