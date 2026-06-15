"""
routes/entitlement.py -- ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth -- handlers never re-derive tier logic here.

  GET  /api/entitlement              -- the current Entitlement as JSON.
  GET  /api/entitlement/diagnostic   -- the *inputs* the resolver consulted
                                        (license/cloud-plan presence, enforce
                                        env, cache liveness) for operator
                                        triage.
  POST /api/entitlement/refresh      -- drop the cache and return the freshly
                                        re-resolved Entitlement (used after a
                                        license is dropped in or the daemon
                                        writes a new cloud_plan.json, so the
                                        UI does not have to wait for the 60 s
                                        TTL).
  GET  /api/entitlement/required-tier -- resolve the minimum purchasable tier
                                         for a feature= or runtime= key.
  GET  /api/entitlement/upgrade-diff  -- features + runtimes a target tier
                                         would add on top of the current ent.
  GET  /api/runtimes                  -- the full runtime catalog with
                                         locked/free/tier flags.

Side-effect-free and never-raise (refresh's only side effect is busting the
in-process cache), so it is safe to classify ``oss-passthrough`` on the cloud
side: when no license/cloud plan is present every endpoint returns a graceful
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
                "source": "oss",
                "node_limit": 1,
                "expiry": None,
                "expired": False,
                "is_paid": False,
                "grace": True,
                "enforced": False,
                "enforce_at": None,
                "enforce_at_iso": None,
                "days_until_enforce": None,
                "retention_days": 7,
                "runtimes": ["nemoclaw", "openclaw"],
                "features": [],
            }
        )


@bp_entitlement.route("/api/entitlement/refresh", methods=["POST"])
def api_entitlement_refresh():
    """Force-drop the in-process entitlement cache and re-resolve.

    The resolver caches for 60 s; this endpoint covers the manual / out-of-band
    install path where the operator just dropped a license file or the daemon
    wrote a fresh cloud_plan.json and does not want to wait for the TTL.
    Returns the freshly resolved Entitlement (same shape as ``/api/entitlement``).
    Falls back to the grace OSS-free shape on any error.
    """
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
        return jsonify(_ent.get_entitlement(force=True).to_dict())
    except Exception as exc:
        logger.warning("api_entitlement_refresh: falling back to OSS-free: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "tier_label": "OSS",
                "source": "oss",
                "node_limit": 1,
                "expiry": None,
                "expired": False,
                "is_paid": False,
                "grace": True,
                "enforced": False,
                "enforce_at": None,
                "enforce_at_iso": None,
                "days_until_enforce": None,
                "runtimes": ["nemoclaw", "openclaw"],
                "features": [],
            }
        )


@bp_entitlement.route("/api/entitlement/upgrade-diff")
def api_entitlement_upgrade_diff():
    """Return the features + runtimes ``?target=<tier>`` would unlock on top of
    the current entitlement. Drives the upgrade CTA shown on locked rows.

    Shape: ``{"target": "<tier>", "added_features": [...], "added_runtimes": [...]}``

    Unknown / missing ``target`` returns empty lists; never raises."""
    try:
        target = (request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return jsonify(_ent.upgrade_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_upgrade_diff: error: %s", exc)
        return jsonify(
            {
                "target": (request.args.get("target") or "").strip().lower(),
                "added_features": [],
                "added_runtimes": [],
            }
        )


@bp_entitlement.route("/api/entitlement/required-tier")
def api_entitlement_required_tier():
    """Resolve the minimum *purchasable* tier that unlocks a given feature or
    runtime. Drives the lock affordance copy ("Available in Starter" / "Available
    in Pro").

    Query: exactly one of ``feature=<id>`` or ``runtime=<id>``.

    Returns 200 with key, kind, required_tier, current_tier, upgrade_required,
    allowed. Returns 400 when neither query param is supplied or both are given.
    """
    try:
        from clawmetry import entitlements as _ent

        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        if not feature and not runtime:
            return jsonify({"error": "supply either feature=<id> or runtime=<id>"}), 400
        if feature and runtime:
            return jsonify({"error": "supply only one of feature= or runtime="}), 400
        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            allowed = _ent.get_entitlement().allows_feature(feature)
        else:
            key, kind = runtime, "runtime"
            required = _ent.min_tier_for_runtime(runtime)
            allowed = _ent.get_entitlement().allows_runtime(runtime)
        ent = _ent.get_entitlement()
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
    except Exception as exc:
        logger.warning("api_entitlement_required_tier: error: %s", exc)
        return jsonify({"error": str(exc)}), 500


@bp_entitlement.route("/api/entitlement/diagnostic")
def api_entitlement_diagnostic():
    """Return the *inputs* the entitlement resolver consulted.

    Where ``/api/entitlement`` reports the resolved outputs, this endpoint
    reports the inputs — license/cloud-plan path presence (not contents), the
    raw ``CLAWMETRY_ENFORCE`` env var and the boolean it resolves to, and the
    cache liveness for the next call. Lets operators answer "why does this
    install think it's on tier X?" without shelling into the host.

    Side-effect-free, never reads file contents, never raises: on any
    diagnostic-collection failure the route returns a minimal safe shape so a
    dashboard panel can always render something.
    """
    try:
        from clawmetry import entitlements as _ent

        return jsonify(_ent.resolution_diagnostic())
    except Exception as exc:  # never crash the dashboard over a diagnostic read
        logger.warning("api_entitlement_diagnostic: falling back to minimal: %s", exc)
        return jsonify(
            {
                "license_path": None,
                "license_present": False,
                "cloud_plan_path": None,
                "cloud_plan_present": False,
                "enforce_env": os.environ.get("CLAWMETRY_ENFORCE"),
                "is_enforced": False,
                "cache_age_seconds": None,
                "cache_ttl_seconds": None,
                "cache_hit_next_call": False,
                "cache_cached_tier": None,
                "error": str(exc),
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
                        "tier": "free",
                        "allowed": True,
                        "locked": False,
                    },
                    {
                        "id": "openclaw",
                        "label": "OpenClaw",
                        "free": True,
                        "tier": "free",
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
    """Return the full feature catalog with per-feature ``free``/``allowed``/
    ``locked`` flags + the minimum tier that unlocks each one, so the dashboard
    can render *every* known feature in the upgrade surface — including paid
    ones the local install does not have — and overlay a lock affordance + an
    accurate "Requires <Tier>" CTA once enforcement is on.

    Shape::

        {
          "features": [
            {"id": "sessions",  "label": "Sessions",
             "tier": "oss",          "free": true,  "allowed": true,
             "locked": false, "entitled": true},
            {"id": "self_evolve", "label": "Self-Evolve",
             "tier": "cloud_pro",    "free": false, "allowed": true,
             "locked": false, "entitled": false},
            ...
          ],
          "grace":    true | false,   # mirrors /api/entitlement.grace
          "enforced": true | false
        }

    Side-effect-free and never-raise: any resolution error falls back to a
    grace OSS-free shape so the UI still has something safe to render.
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
        logger.warning("api_features: falling back to OSS-free: %s", exc)
        return jsonify({"features": [], "grace": True, "enforced": False})


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


@bp_entitlement.route("/api/license/pubkey")
def api_license_pubkey():
    """Return the embedded Ed25519 license-verification key + its SHA-256
    fingerprint, so operators can confirm the OSS install carries the genuine
    trust anchor (the same one published at https://clawmetry.com/security).

    Read-only, no auth, no license required — the public key is, by
    construction, public. Never raises: on a parse failure the body still
    includes ``valid: false`` so callers always get a stable shape.
    """
    try:
        from clawmetry import license as _lic

        return jsonify(_lic.pubkey_info())
    except Exception as exc:  # never crash the dashboard over a key read
        logger.warning("api_license_pubkey: error: %s", exc)
        return jsonify(
            {
                "algorithm": "ed25519",
                "format": "SubjectPublicKeyInfo (DER, SHA-256)",
                "fingerprint_sha256": None,
                "fingerprint_short": None,
                "pem": "",
                "valid": False,
            }
        )


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


def _route_actor() -> str:
    """Best-effort actor identity for the audit log. Routes don't have a
    full auth surface yet; the dashboard sends an ``X-Actor`` header when
    available, falling back to ``X-Forwarded-For`` then the remote address.
    Empty string is fine — the audit reader UI shows ``system`` for
    blank actors."""
    try:
        for h in ("X-Actor", "X-Forwarded-For"):
            v = request.headers.get(h, "") or ""
            v = v.split(",")[0].strip()
            if v:
                return v[:128]
        return (request.remote_addr or "")[:128]
    except Exception:
        return ""


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

        ok, msg = _lic.activate(key, actor=_route_actor())
        status_code = 200 if ok else 400
        return jsonify({"ok": ok, "message": msg}), status_code
    except Exception as exc:
        logger.warning("api_license_activate: error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@bp_entitlement.route("/api/license/verify", methods=["POST"])
def api_license_verify():
    """Verify a license key OFFLINE without persisting it (dry-run).

    Body: ``{"key": "CLAW1.…"}``. Returns the same shape as
    ``/api/license/status`` plus a ``"dry_run": true`` marker, so the UI can
    show "this is what activating this key would unlock" before the user
    commits. Always 200 on a malformed/forged key (the body carries
    ``valid=false``) — only a missing ``key`` field is a 400. The server never
    writes the key to disk, never touches the entitlement cache, and never
    raises.
    """
    try:
        body = request.get_json(silent=True) or {}
        key = str(body.get("key", "")).strip()
        if not key:
            return jsonify({"ok": False, "error": "key is required"}), 400
        from clawmetry import license as _lic

        info = _lic.inspect_key(key)
        if info is None:
            return jsonify(
                {"valid": False, "status": "invalid", "dry_run": True}
            )
        info = dict(info)
        info["dry_run"] = True
        return jsonify(info)
    except Exception as exc:
        logger.warning("api_license_verify: error: %s", exc)
        return jsonify({"valid": False, "status": "invalid", "dry_run": True})


@bp_entitlement.route("/api/license/deactivate", methods=["POST"])
def api_license_deactivate():
    """Remove the installed license key and revert to OSS tier.

    Idempotent — returns ``{"ok": true, "removed": false}`` when no key was
    installed.
    """
    try:
        from clawmetry import license as _lic

        ok, removed = _lic.deactivate(actor=_route_actor())
        if not ok:
            return jsonify({"ok": False, "removed": False, "error": "remove_failed"}), 500
        return jsonify({"ok": True, "removed": removed})
    except Exception as exc:
        logger.warning("api_license_deactivate: error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500
