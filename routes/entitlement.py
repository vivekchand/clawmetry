"""
routes/entitlement.py -- ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth for "what is this install allowed to do".

Blueprint: ``bp_entitlement`` (url_prefix ``/api/entitlement``)

Endpoints
---------
GET /api/entitlement/                   — current resolved entitlement (to_dict)
GET /api/entitlement/summary            — compact snapshot (tier/source/grace/is_paid)
GET /api/entitlement/check              — allowed? check for one runtime or feature
GET /api/entitlement/lock-check         — bulk lock-status across all axes
GET /api/entitlement/preview            — to_dict for a hypothetical tier
GET /api/entitlement/upgrade-diff       — features/runtimes added by upgrading
GET /api/entitlement/downgrade-diff     — features/runtimes lost by downgrading
GET /api/entitlement/next-tier-diff     — upgrade_diff for the next purchasable tier
GET /api/entitlement/prev-tier-diff     — downgrade_diff for the prev purchasable tier
GET /api/entitlement/capacity-diff      — capacity-axis transition to a target tier
GET /api/entitlement/next-tier-capacity-diff  — capacity_diff for the next tier
GET /api/entitlement/prev-tier-capacity-diff  — capacity_diff for the prev tier
GET /api/entitlement/tier-unlocks       — marginal unlocks at a single named tier
GET /api/entitlement/tier-unlocks-batch — marginal unlocks for all purchasable tiers
GET /api/entitlement/upgrade-path       — ordered unlock ladder above current tier
GET /api/entitlement/tier-matrix        — full feature x tier matrix
GET /api/entitlement/tier-matrix-subset — matrix restricted to supplied tiers
GET /api/entitlement/pricing-page       — one-shot pricing bundle (previews+matrix+unlocks)
GET /api/entitlement/runtimes           — available runtimes for this install
GET /api/entitlement/lock-reason        — human-readable lock reason for one item
GET /api/entitlement/diagnostic         — resolution diagnostic (license / cache state)
POST /api/entitlement/invalidate        — flush the entitlement cache
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.entitlement")

bp_entitlement = Blueprint("entitlement", __name__, url_prefix="/api/entitlement")


def _ent():
    """Lazy import so the module loads even if clawmetry.entitlements is absent."""
    import clawmetry.entitlements as _e

    return _e


# ---------------------------------------------------------------------------
# GET /api/entitlement/
# ---------------------------------------------------------------------------


@bp_entitlement.route("/", methods=["GET"])
def api_entitlement_get():
    """Return the full resolved entitlement as JSON.

    Shape mirrors :meth:`clawmetry.entitlements.Entitlement.to_dict`.
    Always 200; a resolution error falls back to the OSS-free entitlement.
    """
    try:
        e = _ent()
        ent = e.get_entitlement()
        return jsonify(ent.to_dict())
    except Exception as exc:
        logger.warning("api_entitlement_get failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/summary
# ---------------------------------------------------------------------------


@bp_entitlement.route("/summary", methods=["GET"])
def api_entitlement_summary():
    """Compact entitlement snapshot safe for telemetry / healthcheck.

    Returns tier, source, grace, enforced, is_paid, expired,
    days_until_expiry -- no feature or runtime list.
    """
    try:
        e = _ent()
        return jsonify(e.entitlement_summary())
    except Exception as exc:
        logger.warning("api_entitlement_summary failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/check?runtime=<rt>  OR  ?feature=<feat>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/check", methods=["GET"])
def api_entitlement_check():
    """Check whether a single runtime or feature is allowed.

    Query params (one required):
      ``runtime``  -- runtime id (e.g. ``claude_code``)
      ``feature``  -- feature id (e.g. ``fleet``)

    Response::

        {"allowed": true|false, "grace": true|false,
         "tier": "<current_tier>", "required_tier": "<min_tier>|null"}
    """
    try:
        e = _ent()
        ent = e.get_entitlement()
        runtime = (request.args.get("runtime") or "").strip().lower()
        feature = (request.args.get("feature") or "").strip().lower()
        if runtime:
            allowed = ent.allows_runtime(runtime)
            required = e.min_tier_for_runtime(runtime)
            return jsonify(
                {
                    "kind": "runtime",
                    "key": runtime,
                    "allowed": allowed,
                    "grace": ent.grace,
                    "tier": ent.tier,
                    "required_tier": required,
                    "required_tier_label": e.tier_label(required) if required else None,
                }
            )
        if feature:
            allowed = ent.allows_feature(feature)
            required = e.min_tier_for_feature(feature)
            return jsonify(
                {
                    "kind": "feature",
                    "key": feature,
                    "allowed": allowed,
                    "grace": ent.grace,
                    "tier": ent.tier,
                    "required_tier": required,
                    "required_tier_label": e.tier_label(required) if required else None,
                }
            )
        return jsonify({"error": "supply ?runtime= or ?feature="}), 400
    except Exception as exc:
        logger.warning("api_entitlement_check failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/lock-check
# ---------------------------------------------------------------------------


@bp_entitlement.route("/lock-check", methods=["GET"])
def api_entitlement_lock_check():
    """Bulk lock-status check across all axes.

    Query params (all optional, comma-separated):
      ``features``        -- feature ids
      ``runtimes``        -- runtime ids
      ``channels``        -- channel counts (integers)
      ``retention_days``  -- retention window sizes (integers)
      ``nodes``           -- node counts (integers)

    Response mirrors :func:`clawmetry.entitlements.bulk_lock_check`.
    """
    try:
        e = _ent()
        result = e.bulk_lock_check(
            features=request.args.get("features"),
            runtimes=request.args.get("runtimes"),
            channels=request.args.get("channels"),
            retention_days=request.args.get("retention_days"),
            nodes=request.args.get("nodes"),
        )
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_lock_check failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/preview?tier=<tier_id>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/preview", methods=["GET"])
def api_entitlement_preview():
    """Return the ``to_dict`` shape for a hypothetical tier.

    Query param: ``tier`` -- tier id (e.g. ``cloud_pro``)

    Returns 404 when the tier id is unknown / non-purchasable.
    """
    try:
        e = _ent()
        tier = (request.args.get("tier") or "").strip().lower()
        if not tier:
            return jsonify({"error": "supply ?tier="}), 400
        result = e.preview(tier)
        if result is None:
            return jsonify({"error": f"unknown tier: {tier!r}"}), 404
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_preview failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/upgrade-diff?target=<tier_id>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/upgrade-diff", methods=["GET"])
def api_entitlement_upgrade_diff():
    """Features and runtimes added by upgrading to ``target``.

    Query param: ``target`` -- tier id to upgrade to.
    """
    try:
        e = _ent()
        target = (request.args.get("target") or "").strip().lower()
        if not target:
            return jsonify({"error": "supply ?target="}), 400
        return jsonify(e.upgrade_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_upgrade_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/downgrade-diff?target=<tier_id>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/downgrade-diff", methods=["GET"])
def api_entitlement_downgrade_diff():
    """Features and runtimes lost by downgrading to ``target``.

    Query param: ``target`` -- tier id to downgrade to.
    """
    try:
        e = _ent()
        target = (request.args.get("target") or "").strip().lower()
        if not target:
            return jsonify({"error": "supply ?target="}), 400
        return jsonify(e.downgrade_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_downgrade_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/next-tier-diff
# ---------------------------------------------------------------------------


@bp_entitlement.route("/next-tier-diff", methods=["GET"])
def api_entitlement_next_tier_diff():
    """upgrade_diff for the next purchasable tier above the current one.

    Returns 204 when the install is already at the top tier.
    """
    try:
        e = _ent()
        result = e.next_tier_diff()
        if result is None:
            return "", 204
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/prev-tier-diff
# ---------------------------------------------------------------------------


@bp_entitlement.route("/prev-tier-diff", methods=["GET"])
def api_entitlement_prev_tier_diff():
    """downgrade_diff for the previous purchasable tier below the current one.

    Returns 204 when the install is already at the floor.
    """
    try:
        e = _ent()
        result = e.previous_tier_diff()
        if result is None:
            return "", 204
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_prev_tier_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/capacity-diff?target=<tier_id>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/capacity-diff", methods=["GET"])
def api_entitlement_capacity_diff():
    """Per-axis capacity transition from the current entitlement to ``target``.

    Query param: ``target`` -- tier id.

    Response mirrors :meth:`Entitlement.capacity_diff`.
    """
    try:
        e = _ent()
        target = (request.args.get("target") or "").strip().lower()
        if not target:
            return jsonify({"error": "supply ?target="}), 400
        return jsonify(e.capacity_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_capacity_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/next-tier-capacity-diff
# ---------------------------------------------------------------------------


@bp_entitlement.route("/next-tier-capacity-diff", methods=["GET"])
def api_entitlement_next_tier_capacity_diff():
    """capacity_diff for the next purchasable tier. 204 at top."""
    try:
        e = _ent()
        result = e.next_tier_capacity_diff()
        if result is None:
            return "", 204
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_capacity_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/prev-tier-capacity-diff
# ---------------------------------------------------------------------------


@bp_entitlement.route("/prev-tier-capacity-diff", methods=["GET"])
def api_entitlement_prev_tier_capacity_diff():
    """capacity_diff for the previous purchasable tier. 204 at floor."""
    try:
        e = _ent()
        result = e.previous_tier_capacity_diff()
        if result is None:
            return "", 204
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_prev_tier_capacity_diff failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/tier-unlocks?tier=<tier_id>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/tier-unlocks", methods=["GET"])
def api_entitlement_tier_unlocks():
    """Marginal unlocks at a single named tier (vs. the tier below it).

    Query param: ``tier`` -- purchasable tier id.

    Returns 404 for unknown or non-purchasable tiers (e.g. ``trial``).
    """
    try:
        e = _ent()
        tier = (request.args.get("tier") or "").strip().lower()
        if not tier:
            return jsonify({"error": "supply ?tier="}), 400
        result = e.tier_unlocks(tier)
        if result is None:
            return jsonify({"error": f"unknown or non-purchasable tier: {tier!r}"}), 404
        return jsonify(result)
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/tier-unlocks-batch
# ---------------------------------------------------------------------------


@bp_entitlement.route("/tier-unlocks-batch", methods=["GET"])
def api_entitlement_tier_unlocks_batch():
    """Marginal unlocks for every purchasable tier in one round-trip.

    Returns a JSON array of :func:`clawmetry.entitlements.tier_unlocks`
    rows, sorted cheapest -> most capable (same as
    :func:`clawmetry.entitlements.tier_unlocks_batch`).  Never 500s;
    returns ``[]`` on resolver failure.
    """
    try:
        e = _ent()
        return jsonify(e.tier_unlocks_batch())
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks_batch failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/upgrade-path
# ---------------------------------------------------------------------------


@bp_entitlement.route("/upgrade-path", methods=["GET"])
def api_entitlement_upgrade_path():
    """Ordered marginal-unlock ladder from the resolved tier upward.

    Returns a JSON array of :func:`clawmetry.entitlements.tier_unlocks`
    rows for every purchasable tier whose rank is strictly above the
    current install's tier, sorted cheapest -> most capable.

    Empty array when already at the top (Enterprise).  Never 500s;
    returns ``[]`` on resolver failure.
    """
    try:
        e = _ent()
        return jsonify(e.upgrade_path())
    except Exception as exc:
        logger.warning("api_entitlement_upgrade_path failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/tier-matrix
# ---------------------------------------------------------------------------


@bp_entitlement.route("/tier-matrix", methods=["GET"])
def api_entitlement_tier_matrix():
    """Full feature x tier matrix for a pricing-page table.

    Each row in the response array has ``{key, label, kind, tiers}``
    where ``tiers`` maps tier id -> bool. See
    :func:`clawmetry.entitlements.tier_matrix` for the full shape.
    """
    try:
        e = _ent()
        return jsonify(e.tier_matrix())
    except Exception as exc:
        logger.warning("api_entitlement_tier_matrix failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/tier-matrix-subset?tiers=<comma-separated>
# ---------------------------------------------------------------------------


@bp_entitlement.route("/tier-matrix-subset", methods=["GET"])
def api_entitlement_tier_matrix_subset():
    """Feature x tier matrix restricted to the supplied tiers.

    Query param: ``tiers`` -- comma-separated purchasable tier ids.
    Falls back to the full matrix when ``tiers`` is empty or all-invalid.
    """
    try:
        e = _ent()
        tiers_param = request.args.get("tiers") or ""
        return jsonify(e.tier_matrix_for_tiers(tiers_param))
    except Exception as exc:
        logger.warning("api_entitlement_tier_matrix_subset failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/pricing-page
# ---------------------------------------------------------------------------


@bp_entitlement.route("/pricing-page", methods=["GET"])
def api_entitlement_pricing_page():
    """One-shot pricing bundle: tier previews + matrix + tier_unlocks rows.

    Response shape::

        {
          "tiers": [{"tier": "...", "preview": {...}, "unlocks": {...}}, ...],
          "matrix": [...]
        }

    See :func:`clawmetry.entitlements.pricing_page_payload`.
    """
    try:
        e = _ent()
        return jsonify(e.pricing_page_payload())
    except Exception as exc:
        logger.warning("api_entitlement_pricing_page failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/runtimes
# ---------------------------------------------------------------------------


@bp_entitlement.route("/runtimes", methods=["GET"])
def api_entitlement_runtimes():
    """Available runtimes for this install.

    Returns all runtimes (grace mode) or only the entitled subset
    (enforce mode). Response::

        {
          "runtimes": ["openclaw", ...],
          "free_runtimes": [...],
          "paid_runtimes": [...],
          "all_runtimes": [...],
          "grace": true|false
        }
    """
    try:
        e = _ent()
        ent = e.get_entitlement()
        return jsonify(
            {
                "runtimes": e.available_runtimes(),
                "free_runtimes": sorted(e.FREE_RUNTIMES),
                "paid_runtimes": sorted(e.PAID_RUNTIMES),
                "all_runtimes": sorted(e.ALL_RUNTIMES),
                "grace": ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_runtimes failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/lock-reason?item=<item>[&kind=runtime|feature|...]
# ---------------------------------------------------------------------------


@bp_entitlement.route("/lock-reason", methods=["GET"])
def api_entitlement_lock_reason():
    """Human-readable lock reason for one item.

    Query params:
      ``item``  -- runtime id, feature id, or integer (channels/nodes/days)
      ``kind``  -- optional: ``runtime``, ``feature``, ``channels``,
                   ``retention_days``, ``nodes``

    Returns ``{"reason": null}`` when the item is not locked.
    """
    try:
        e = _ent()
        item = (request.args.get("item") or "").strip()
        kind = (request.args.get("kind") or "").strip().lower() or None
        if not item:
            return jsonify({"error": "supply ?item="}), 400
        reason = e.lock_reason(item, kind=kind)
        return jsonify({"item": item, "kind": kind, "reason": reason, "locked": reason is not None})
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/entitlement/diagnostic
# ---------------------------------------------------------------------------


@bp_entitlement.route("/diagnostic", methods=["GET"])
def api_entitlement_diagnostic():
    """Resolution diagnostic: license file, cloud-plan cache, enforce state.

    Exposes :func:`clawmetry.entitlements.resolution_diagnostic` as JSON.
    Useful for ``clawmetry status`` and the settings panel.
    """
    try:
        e = _ent()
        return jsonify(e.resolution_diagnostic())
    except Exception as exc:
        logger.warning("api_entitlement_diagnostic failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# POST /api/entitlement/invalidate
# ---------------------------------------------------------------------------


@bp_entitlement.route("/invalidate", methods=["POST"])
def api_entitlement_invalidate():
    """Flush the entitlement cache so the next read re-resolves from disk.

    Called by the sync daemon after it writes a fresh ``cloud_plan.json``.
    Returns ``{"ok": true}``.
    """
    try:
        e = _ent()
        e.invalidate()
        return jsonify({"ok": True})
    except Exception as exc:
        logger.warning("api_entitlement_invalidate failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
