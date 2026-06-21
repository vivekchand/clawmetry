"""
routes/entitlement.py — ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth — handlers never re-derive tier logic here.

  GET /api/entitlement — the current Entitlement as JSON.
  GET /api/runtimes    — the full runtime catalog with locked/free flags.
  GET /api/features    — the full feature catalog with locked/free/tier flags.

Side-effect-free and never-raise, so it is safe to classify ``oss-passthrough``
on the cloud side: when no license/cloud plan is present it returns a graceful
OSS-free shape, never a 4xx.
"""

from __future__ import annotations

import logging

import os

from flask import Blueprint, jsonify, request

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
                "runtimes": ["nemoclaw", "openclaw"],
                "features": [],
            }
        )


@bp_entitlement.route("/api/runtimes")
def api_runtimes():
    """Return the full runtime catalog with per-runtime ``free``/``allowed``/
    ``locked`` flags so the dashboard can render *every* known runtime in the
    switcher — including paid ones with zero local sessions — and overlay a
    lock affordance on the locked rows once enforcement is on.

    Shape::

        {
          "runtimes": [
            {"id": "openclaw", "label": "OpenClaw",
             "free": true, "allowed": true, "locked": false},
            ...
          ],
          "grace":    true | false,   # mirrors /api/entitlement.grace
          "enforced": true | false
        }

    Side-effect-free and never-raise: any resolution error falls back to a
    grace OSS-free shape with the OpenClaw row, so the UI still has something
    safe to render.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "runtimes": _ent.runtime_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:  # never crash the dashboard over a gate read
        logger.warning("api_runtimes: falling back to OSS-free: %s", exc)
        return jsonify(
            {
                "runtimes": [
                    {
                        "id": "nemoclaw",
                        "label": "NemoClaw",
                        "free": True,
                        "allowed": True,
                        "locked": False,
                    },
                    {
                        "id": "openclaw",
                        "label": "OpenClaw",
                        "free": True,
                        "allowed": True,
                        "locked": False,
                    },
                ],
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/features")
def api_features():
    """Return the full feature catalog with per-feature ``free``/``tier``/
    ``allowed``/``locked`` flags so the dashboard's Settings matrix, the
    pricing-parity grid, and the upgrade-CTA copy all read off one canonical
    list instead of re-deriving tier buckets in JS.

    Shape::

        {
          "features": [
            {"id": "sessions", "label": "Sessions", "tier": "oss",
             "free": true, "allowed": true, "locked": false},
            {"id": "fleet", "label": "Multi-node fleet",
             "tier": "cloud_starter", "free": false,
             "allowed": true, "locked": false},
            ...
          ],
          "grace":    true | false,   # mirrors /api/entitlement.grace
          "enforced": true | false
        }

    Side-effect-free and never-raise: any resolution error falls back to a
    grace-mode shape (every feature ``allowed=True``, ``locked=False``) so
    the UI still has something safe to render.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "features": _ent.feature_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:  # never crash the dashboard over a gate read
        logger.warning("api_features: falling back to grace shape: %s", exc)
        try:
            from clawmetry import entitlements as _ent

            fallback = [
                {
                    "id": fid,
                    "label": _ent.feature_label(fid),
                    "tier": _ent.feature_tier(fid),
                    "free": fid in _ent.FREE_FEATURES,
                    "allowed": True,
                    "locked": False,
                }
                for tier, bucket in _ent._FEATURE_TIER_ORDER
                for fid in sorted(bucket)
            ]
        except Exception:
            fallback = []
        return jsonify(
            {
                "features": fallback,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/license/status")
def api_license_status():
    """Return the current self-hosted license info as JSON.
    Returns ``{plan: 'oss', status: 'no_license'}`` when nothing is installed."""
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        if info is None:
            return jsonify({"plan": "oss", "status": "no_license", "valid": False})
        return jsonify(info)
    except Exception as exc:
        logger.warning("api_license_status: error: %s", exc)
        return jsonify({"error": str(exc)}), 500


@bp_entitlement.route("/api/paywall/event", methods=["POST"])
def api_paywall_event():
    """Accept a client-side paywall telemetry ping (fire-and-forget).

    Body: ``{"event": "paywall_view"|"paywall_cta_click",
             "feature": "...", "harness": "...", "source": "..."}``
    Always returns 204 — callers never need the response.
    """
    try:
        body = request.get_json(silent=True) or {}
        event = str(body.get("event", ""))[:64]
        harness = str(body.get("harness", ""))[:64]
        source = str(body.get("source", ""))[:64]
        feature = str(body.get("feature", ""))[:128]
        logger.info(
            "paywall: event=%s harness=%s feature=%s source=%s",
            event, harness, feature, source,
        )
    except Exception as exc:
        logger.debug("api_paywall_event: ignored error: %s", exc)
    return "", 204


@bp_entitlement.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    """Activate a self-hosted Pro/Enterprise license key.

    Body: ``{"key": "CLAW1.…"}``.
    Returns ``{"ok": true, "message": "…"}`` on success or 400 on failure.
    """
    try:
        body = request.get_json(silent=True) or {}
        key = str(body.get("key", "")).strip()
        if not key:
            return jsonify({"ok": False, "error": "key is required"}), 400
        from clawmetry import license as _lic

        ok, msg = _lic.activate(key)
        status_code = 200 if ok else 400
        return jsonify({"ok": ok, "message": msg}), status_code
    except Exception as exc:
        logger.warning("api_license_activate: error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@bp_entitlement.route("/api/license/deactivate", methods=["POST"])
def api_license_deactivate():
    """Remove the installed license key and revert to OSS tier.

    Idempotent — returns ``{"ok": true, "removed": false}`` when no key was
    installed.
    """
    try:
        from clawmetry import license as _lic

        removed = False
        if os.path.isfile(_lic.LICENSE_PATH):
            os.remove(_lic.LICENSE_PATH)
            removed = True
        try:
            from clawmetry import entitlements as _ent

            _ent.invalidate()
        except Exception:
            pass
        return jsonify({"ok": True, "removed": removed})
    except Exception as exc:
        logger.warning("api_license_deactivate: error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500
