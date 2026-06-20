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
                                        re-resolved Entitlement.
  GET  /api/entitlement/required-tier -- resolve the minimum purchasable tier
                                         for a feature=, runtime=, channels=,
                                         or retention_days= key. The capacity
                                         axes (channels / retention_days) wrap
                                         the matching ``min_tier_for_*`` Python
                                         helpers so the same endpoint answers
                                         all four "what tier do I need" axes
                                         off one URL.
  GET  /api/entitlement/lock-reason   -- human-readable explanation of why a
                                         feature= or runtime= key is locked,
                                         carrying the structured
                                         ``required_tier`` payload alongside
                                         the message so a paywall tooltip can
                                         render "Locked: <reason>. [Upgrade to
                                         <X>]" in one round-trip.
  GET  /api/entitlement/upgrade-diff  -- features + runtimes a target tier
                                         would add on top of the current ent.
  GET  /api/entitlement/downgrade-diff -- features + runtimes a target tier
                                          would REMOVE from the current ent.
  GET  /api/runtimes                  -- the full runtime catalog.
  GET  /api/tiers                     -- the full tier ladder with per-tier metadata.
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.entitlement")

bp_entitlement = Blueprint("entitlement", __name__)


@bp_entitlement.route("/api/entitlement")
def api_entitlement():
    try:
        from clawmetry import entitlements as _ent

        return jsonify(_ent.get_entitlement().to_dict())
    except Exception as exc:
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
                "enforce_at": None,
                "enforce_at_iso": None,
                "days_until_enforce": None,
                "retention_days": 7,
                "runtimes": ["nemoclaw", "openclaw"],
                "features": [],
                "locked_runtimes": [],
                "locked_features": [],
                "next_tier_diff": None,
                "prev_tier_diff": None,
            }
        )


@bp_entitlement.route("/api/entitlement/refresh", methods=["POST"])
def api_entitlement_refresh():
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
                "tier_rank": 0,
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
                "locked_runtimes": [],
                "locked_features": [],
                "next_tier_diff": None,
                "prev_tier_diff": None,
            }
        )


@bp_entitlement.route("/api/entitlement/upgrade-diff")
def api_entitlement_upgrade_diff():
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


@bp_entitlement.route("/api/entitlement/downgrade-diff")
def api_entitlement_downgrade_diff():
    try:
        target = (request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return jsonify(_ent.downgrade_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_downgrade_diff: error: %s", exc)
        return jsonify(
            {
                "target": (request.args.get("target") or "").strip().lower(),
                "lost_features": [],
                "lost_runtimes": [],
            }
        )


_CAPACITY_PARAMS = ("channels", "retention_days")


def _parse_capacity_arg(name: str) -> tuple[bool, bool, int | None, str]:
    """Parse a capacity query param.

    Returns ``(present, parsed_ok, value, raw)``. ``present`` is True iff the
    caller supplied the param at all (even with an empty value, so blank input
    doesn't silently fall through to a feature/runtime branch). ``parsed_ok``
    is False when the supplied value couldn't be coerced to ``int`` -- the
    HTTP wrapper then short-circuits to ``required_tier=None`` instead of
    handing ``None`` to the underlying helper (where, for retention, ``None``
    is the *unlimited* sentinel and would mis-route to Enterprise).
    """
    raw = request.args.get(name)
    if raw is None:
        return False, False, None, ""
    raw_stripped = raw.strip()
    if not raw_stripped:
        return True, False, None, raw_stripped
    try:
        return True, True, int(raw_stripped), raw_stripped
    except (TypeError, ValueError):
        return True, False, None, raw_stripped


@bp_entitlement.route("/api/entitlement/required-tier")
def api_entitlement_required_tier():
    try:
        from clawmetry import entitlements as _ent

        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            channels_ok,
            channels_n,
            channels_raw,
        ) = _parse_capacity_arg("channels")
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _parse_capacity_arg("retention_days")

        supplied = [
            bool(feature),
            bool(runtime),
            channels_present,
            retention_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, or retention_days=<int>"
                        )
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, channels=, "
                            "or retention_days="
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            allowed = ent.allows_feature(feature)
        elif runtime:
            key, kind = runtime, "runtime"
            required = _ent.min_tier_for_runtime(runtime)
            allowed = ent.allows_runtime(runtime)
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok:
                required = _ent.min_tier_for_channel_count(channels_n)
                allowed = ent.allows_channel_count(channels_n)
            else:
                # Blank / non-int: never-crash short-circuit. ``required_tier``
                # is None so the UI knows there's no upgrade target to render,
                # and ``allowed`` defaults to True (same posture as
                # ``allows_channel_count`` swallowing a non-int to True).
                required = None
                allowed = True
        else:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                allowed = ent.allows_retention_window(retention_n)
            else:
                # Blank / non-int: same posture as the channels branch.
                # Important: don't forward ``None`` to
                # :func:`min_tier_for_retention_window` -- there ``None`` is
                # the *unlimited* sentinel and would mis-route to Enterprise.
                required = None
                allowed = True
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
        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime:
            key, kind = runtime, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        else:
            key, kind = "", ""
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


@bp_entitlement.route("/api/entitlement/lock-reason")
def api_entitlement_lock_reason():
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
            allowed = ent.allows_feature(feature)
            required = _ent.min_tier_for_feature(feature)
        else:
            key, kind = runtime, "runtime"
            allowed = ent.allows_runtime(runtime)
            required = _ent.min_tier_for_runtime(runtime)
        reason = ent.lock_reason(key, kind=kind)
        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason: error: %s", exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime = (request.args.get("runtime") or "").strip().lower()
        if feature:
            key, kind = feature, "feature"
        elif runtime:
            key, kind = runtime, "runtime"
        else:
            key, kind = "", ""
        return jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": None,
                "locked": False,
                "allowed": True,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
            }
        )


@bp_entitlement.route("/api/entitlement/diagnostic")
def api_entitlement_diagnostic():
    try:
        from clawmetry import entitlements as _ent

        return jsonify(_ent.resolution_diagnostic())
    except Exception as exc:
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
    except Exception as exc:
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


@bp_entitlement.route("/api/tiers")
def api_tiers():
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": _ent.tier_catalog(),
                "current": ent.tier,
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_tiers: falling back to OSS-free: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current": "oss",
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/features")
def api_features():
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
    except Exception as exc:
        logger.warning("api_features: falling back to OSS-free: %s", exc)
        return jsonify({"features": [], "grace": True, "enforced": False})


@bp_entitlement.route("/api/license/status")
def api_license_status():
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
    try:
        from clawmetry import license as _lic

        return jsonify(_lic.pubkey_info())
    except Exception as exc:
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
    try:
        from clawmetry import license as _lic

        ok, removed = _lic.deactivate(actor=_route_actor())
        if not ok:
            return jsonify({"ok": False, "removed": False, "error": "remove_failed"}), 500
        return jsonify({"ok": True, "removed": removed})
    except Exception as exc:
        logger.warning("api_license_deactivate: error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500
