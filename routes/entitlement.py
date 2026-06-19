"""
routes/entitlement.py — ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth — handlers never re-derive tier logic here.

  GET /api/entitlement                — the current Entitlement as JSON.
  GET /api/entitlement/required-tier  — minimum purchasable tier that unlocks a
                                        ``feature=<id>`` or ``runtime=<id>``.
  GET /api/runtimes                   — the full runtime catalog with
                                        locked/free flags.

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
                "tier_label": "OSS",
                "tier_rank": 0,
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


@bp_entitlement.route("/api/entitlement/required-tier")
def api_entitlement_required_tier():
    """Resolve the minimum *purchasable* tier that unlocks a given feature or
    runtime. Drives the lock-affordance copy ("Available in Starter" / "Available
    in Pro") so the dashboard never re-derives the per-feature tier bucket in
    JavaScript.

    Query: exactly one of ``feature=<id>`` or ``runtime=<id>``.

    Returns 200 with::

        {
          "key":                 "<id>",
          "kind":                "feature" | "runtime",
          "required_tier":       "<tier>" | null,
          "required_tier_label": "<Display>" | null,
          "required_tier_rank":  int,                 # -1 when unknown
          "current_tier":        "<tier>",
          "current_tier_rank":   int,
          "upgrade_required":    bool,                # required rank > current rank
          "allowed":             bool                 # resolved allows_* answer
        }

    Returns 400 when neither query param is supplied or both are given. Never
    5xx — any internal failure returns the never-raise grace shape so a flaky
    entitlement read can never break a paywall tooltip render.
    """
    try:
        from clawmetry import entitlements as _ent

        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        if not feature and not runtime:
            return jsonify({"error": "supply either feature=<id> or runtime=<id>"}), 400
        if feature and runtime:
            return jsonify({"error": "supply only one of feature= or runtime="}), 400
        ent = _ent.get_entitlement()
        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            allowed = ent.allows_feature(feature)
        else:
            key, kind = runtime, "runtime"
            required = _ent.min_tier_for_runtime(runtime)
            allowed = ent.allows_runtime(runtime)
        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "key": key,
                "kind": kind,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
                "allowed": allowed,
            }
        )
    except Exception as exc:  # never crash the dashboard over a gate read
        logger.warning("api_entitlement_required_tier: error: %s", exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        key = feature or runtime
        kind = "feature" if feature else ("runtime" if runtime else "")
        return jsonify(
            {
                "key": key,
                "kind": kind,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
                "allowed": True,
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
