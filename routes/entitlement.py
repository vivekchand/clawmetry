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
                                         feature=, runtime=, channels= or
                                         retention_days= key is locked,
                                         carrying the structured
                                         ``required_tier`` payload alongside
                                         the message so a paywall tooltip can
                                         render "Locked: <reason>. [Upgrade to
                                         <X>]" in one round-trip. The four
                                         axes match the ones on
                                         ``/api/entitlement/required-tier``.
  GET  /api/entitlement/upgrade-diff  -- features + runtimes a target tier
                                         would add on top of the current ent.
  GET  /api/entitlement/downgrade-diff -- features + runtimes a target tier
                                          would REMOVE from the current ent.
  GET  /api/entitlement/tier-diff     -- arbitrary-endpoint diff between any
                                         two tiers (``?from=&to=``);
                                         generalises ``/upgrade-diff`` /
                                         ``/downgrade-diff`` from "current vs
                                         target" to "any tier vs any tier" so
                                         a "Compare A vs B" pricing-page
                                         widget can render any pair without
                                         first switching the resolver.
  GET  /api/entitlement/preview        -- the full Entitlement.to_dict() shape
                                          rendered for an arbitrary tier so the
                                          upgrade-CTA card can show concrete
                                          numbers without per-tier derivation
                                          in JS.
  GET  /api/entitlement/required-tier-batch -- plural sibling of
                                          ``/required-tier``: takes
                                          ``features=a,b,c`` and/or
                                          ``runtimes=x,y,z`` (comma-separated)
                                          and returns the cheapest tier
                                          admitting *all* of them at once.
                                          Lets a dashboard answer "I'm using
                                          fleet + otel_export + sso -- what
                                          tier covers everything?" in a single
                                          round-trip.
  GET  /api/entitlement/lock-reason-batch -- per-item plural sibling of
                                          ``/lock-reason``: same CSV +
                                          capacity inputs as
                                          ``/required-tier-batch``, but
                                          preserves per-item ``reason`` /
                                          ``locked`` / ``required_tier`` rows
                                          so a Settings or paywall matrix UI
                                          renders N rows off one round-trip
                                          instead of N calls.
  GET  /api/entitlement/tier-unlocks-batch -- plural sibling of
                                          ``/tier-unlocks``: returns the full
                                          pricing-page marginal-unlock ladder
                                          in one pass.
  GET  /api/entitlement/tier-unlocks-path -- arbitrary-endpoint stepwise
                                          unlock path between any two tiers
                                          (``?from=&to=``); unlocks-focused
                                          analogue of ``/tier-path`` (full
                                          ``tier_diff`` per rung) and
                                          ``/capacity-diff-path`` (capacity-
                                          only per rung). Each row is a
                                          ``tier_unlocks`` payload between
                                          the previous step in the path and
                                          the current rung.
  GET  /api/entitlement/capacity-diff-batch -- plural sibling of
                                          ``/capacity-diff``: per-axis
                                          capacity transitions (channels /
                                          retention / nodes) for every
                                          purchasable tier in one pass so
                                          a pricing-page table can render
                                          the capacity column off one
                                          round-trip.
  GET  /api/entitlement/capacity-diff-path -- path analogue of
                                          ``/capacity-diff-batch``: per-rung
                                          capacity transition along an
                                          arbitrary ``?from=&to=`` segment,
                                          capacity-only mirror of
                                          ``/tier-path`` so a capacity-only
                                          pricing widget can render
                                          channel / retention / node
                                          marginal steps between two tiers
                                          off one round-trip.
  GET  /api/entitlement/preview-batch  -- plural sibling of ``/preview``:
                                         the full ``Entitlement.to_dict``
                                         shape rendered for every purchasable
                                         tier in one pass so a pricing-page
                                         table can render the cumulative-state
                                         column off one round-trip.
  GET  /api/entitlement/preview-path   -- arbitrary-endpoint stepwise
                                         cumulative-state path between any two
                                         tiers (``?from=&to=``); path analogue
                                         of ``/preview-batch`` and the
                                         cumulative-state sibling of
                                         ``/tier-path`` / ``/tier-unlocks-path``
                                         / ``/tier-locks-path`` /
                                         ``/capacity-diff-path``. Each row is
                                         the full ``/preview`` payload for that
                                         rung so an upgrade-walkthrough surface
                                         can render the "Cloud Pro: 90-day
                                         retention, ..." card at every step
                                         off one round-trip.
  GET  /api/entitlement/tier-locks    -- marginal-loss companion of
                                         ``/tier-unlocks``: features + runtimes
                                         that disappear when you step down to
                                         the named tier from the next-higher
                                         purchasable tier.
  GET  /api/entitlement/upgrade-path  -- ordered marginal-unlock ladder from
                                         the resolved tier upward (current-
                                         user-relative sibling of
                                         ``/tier-unlocks-batch``).
  GET  /api/entitlement/downgrade-path -- ordered cumulative-loss ladder from
                                         the resolved tier downward (direction-
                                         flipped sibling of ``/upgrade-path``).
  GET  /api/entitlement/tier-path     -- arbitrary-endpoint stepwise path
                                         between any two tiers (``?from=&to=``);
                                         path analogue of ``/tier-diff``,
                                         generalising ``/upgrade-path`` /
                                         ``/downgrade-path`` from "current vs
                                         target" to "any vs any" with each
                                         row a marginal-step ``tier_diff``
                                         payload.
  GET  /api/entitlement/affordable-tiers -- plural sibling of
                                         ``/required-tier-batch``: returns
                                         the full ordered list of purchasable
                                         tiers admitting a constraint bundle
                                         (not just the floor) so a pricing
                                         page can render "you need at least
                                         Starter -- Pro and Enterprise also
                                         qualify" off one round-trip.
  GET  /api/entitlement/tiers-for     -- inverse of ``/required-tier``: the
                                         full ladder of tiers that grant a
                                         ``feature=`` or ``runtime=`` key
                                         (the "Available in: Pro,
                                         Self-hosted Pro, Trial, Enterprise"
                                         availability list a pricing-page
                                         row or feature tooltip needs).
  GET  /api/runtimes                  -- the full runtime catalog.
  GET  /api/tiers                     -- the full tier ladder with per-tier metadata.
  GET  /api/entitlement/feature-spec  -- scalar sibling of ``/api/features``:
                                         single ``feature_catalog()`` row for
                                         ``feature=<id>`` so a feature-detail
                                         page or upgrade tooltip can hydrate
                                         without filtering the full catalogue
                                         client-side.
  GET  /api/entitlement/runtime-spec  -- scalar sibling of ``/api/runtimes``:
                                         single ``runtime_catalog()`` row for
                                         ``runtime=<id>`` (canonical id or
                                         alias) so a runtime-detail page or
                                         upgrade tooltip can hydrate without
                                         filtering the full catalogue
                                         client-side.
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
                "next_tier_unlocks": None,
                "prev_tier_unlocks": None,
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
                "next_tier_unlocks": None,
                "prev_tier_unlocks": None,
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


@bp_entitlement.route("/api/entitlement/tier-diff")
def api_entitlement_tier_diff():
    """``GET /api/entitlement/tier-diff?from=<id>&to=<id>`` -- arbitrary-
    endpoint diff between any two tiers, generalising ``/upgrade-diff`` /
    ``/downgrade-diff`` (which pin one endpoint to the resolved entitlement)
    to ANY pair so a "Compare A vs B" pricing-page widget can render the
    transition between any two rungs without first switching the resolver.

    The payload carries both ``added_*`` and ``lost_*`` lists on every call,
    plus a ``direction`` tag (``upgrade`` | ``downgrade`` | ``lateral`` |
    ``identity``) and a ``capacity_changes`` dict for the three capacity
    axes (channels / retention / nodes), so the same shape covers all four
    transition kinds and the consumer reads the tag instead of inferring
    direction from the deltas.

    ``400`` when ``from=`` or ``to=`` is missing; ``404`` when either id
    is unknown. ``trial`` IS accepted -- it is unreachable via the
    purchasable-only helpers but is a valid hypothetical endpoint.
    Never 5xxs: a resolver failure short-circuits to ``404`` instead of
    raising so a paywall surface keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_diff(f, t)
        if body is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_tier_diff: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-path")
def api_entitlement_tier_path():
    """``GET /api/entitlement/tier-path?from=<id>&to=<id>`` -- arbitrary-
    endpoint stepwise path between any two tiers; the path analogue of
    ``/api/entitlement/tier-diff``, generalising ``/upgrade-path`` /
    ``/downgrade-path`` (which pin one endpoint to the resolved
    entitlement) to ANY pair so a "Compare A vs B" pricing-page widget
    can render the rung sequence between any two tiers without first
    switching the resolver.

    Each row in ``path`` is a full :func:`clawmetry.entitlements.tier_diff`
    payload between the previous step in the path (or ``from`` for the
    first row) and the current rung -- so each row is a marginal step
    diff. Same-rank siblings strictly between the endpoints are both
    included; same-rank siblings of the destination are excluded so the
    path terminates exactly at ``to``.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<tier_diff row>, ...],
        }

    Identity (``from == to``) returns an empty path. Lateral (same rank,
    different id) returns a single-row path. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial`` IS
    accepted as an endpoint -- it is excluded from the walked rungs (not
    purchasable) but the endpoint computation still resolves. Never
    5xxs: a resolver failure short-circuits to ``404`` so a pricing-page
    surface keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_path(f, t)
        if path is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        from_rank = _ent.tier_rank(f)
        to_rank = _ent.tier_rank(t)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-diff-batch")
def api_entitlement_tier_diff_batch():
    """``GET /api/entitlement/tier-diff-batch`` -- full marginal
    :func:`tier_diff` for every purchasable tier in one pass. Plural
    sibling of ``/api/entitlement/tier-diff`` and the "all-slices-in-one-
    row" member of the batch family alongside ``/tier-unlocks-batch``
    (feature/runtime grant slice), ``/tier-locks-batch`` (feature/
    runtime loss slice) and ``/capacity-diff-batch`` (capacity slice).
    Where each of those siblings carries a single slice of the per-rung
    transition, this endpoint carries ALL slices (``added_features`` +
    ``lost_features`` + ``added_runtimes`` + ``lost_runtimes`` +
    ``capacity_changes``) in one row so a pricing-page UI can render the
    full marginal column off **one** round-trip instead of N calls to
    ``/tier-diff``.

    Anchor matches ``/tier-unlocks-batch``: each row is the
    :func:`clawmetry.entitlements.tier_diff` payload between the next-
    lower-rank purchasable tier and the current rung. At the floor
    (``TIER_OSS`` / ``TIER_CLOUD_FREE``) the row collapses to an
    identity diff (``from == to``, ``direction == "identity"``, empty
    marginal lists) -- every row stays byte-stable with a valid
    ``/tier-diff`` payload so the singular and batch never diverge in
    shape.

    Response shape::

        {
          "tiers":             [<tier_diff row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-diff`` exactly
    (``from``, ``from_label``, ``from_rank``, ``to``, ``to_label``,
    ``to_rank``, ``direction``, ``added_features``, ``lost_features``,
    ``added_runtimes``, ``lost_runtimes``, ``capacity_changes``). The
    trial tier is excluded -- it is not purchasable, same posture as the
    other batches. Never 5xxs: a resolver failure yields an empty
    ``tiers`` list and the grace-shape envelope so the pricing page
    keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tier_diff_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_diff_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/capacity-diff")
def api_entitlement_capacity_diff():
    """``GET /api/entitlement/capacity-diff?target=<tier>`` -- per-axis
    capacity transition (channels / retention / nodes) from the resolved
    entitlement to ``target``. Companion to ``/upgrade-diff`` (feature +
    runtime adds) and ``/downgrade-diff`` (feature + runtime losses). The
    payload is direction-agnostic: each axis carries the same
    ``{before, after, delta, unlocked, locked}`` triple so both the
    upgrade-to and the cancellation-to CTAs read off one shape."""
    try:
        target = (request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return jsonify(_ent.capacity_diff(target))
    except Exception as exc:
        logger.warning("api_entitlement_capacity_diff: error: %s", exc)
        return jsonify(
            {
                "target": (request.args.get("target") or "").strip().lower(),
                "channel_limit": None,
                "retention_days": None,
                "node_limit": None,
            }
        )


@bp_entitlement.route("/api/entitlement/capacity-diff-batch")
def api_entitlement_capacity_diff_batch():
    """``GET /api/entitlement/capacity-diff-batch`` -- per-axis capacity
    transition for every purchasable tier in one pass. Plural sibling of
    ``/api/entitlement/capacity-diff``: where the singular endpoint
    returns one tier's per-axis triple, the batch returns the full
    pricing-page ladder in tier-rank order so a pricing-table UI can
    render the capacity column ("channels: 3 -> unlimited, retention:
    7d -> 30d, nodes: 1 -> unlimited") off **one** round-trip instead
    of N calls.

    Direction-agnostic capacity companion to ``/tier-unlocks-batch``
    (marginal feature / runtime grant per rung), ``/tier-locks-batch``
    (marginal feature / runtime loss per rung) and ``/preview-batch``
    (cumulative ``Entitlement.to_dict`` shape per rung): pair them to
    render the full "what's at X / what's new at X / what you'd give
    up at X / capacity at X" view of a pricing table without
    client-side composition.

    Response shape::

        {
          "tiers":             [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/capacity-diff`` exactly
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``
    where each axis is the same ``{before, after, delta, unlocked,
    locked}`` triple). The trial tier is excluded -- not purchasable,
    same posture as the other ``*-batch`` siblings. Never 5xxs: a
    resolver failure yields an empty ``tiers`` list and the grace-shape
    envelope so the pricing page keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.capacity_diff_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_capacity_diff_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/capacity-diff-path")
def api_entitlement_capacity_diff_path():
    """``GET /api/entitlement/capacity-diff-path?from=<id>&to=<id>`` --
    per-rung capacity transition along an arbitrary ``from -> to`` segment.
    Path analogue of ``/capacity-diff-batch`` (which walks every purchasable
    tier off the resolved entitlement); capacity-only mirror of
    ``/tier-path`` (which carries the full ``tier_diff`` per rung). Lets a
    capacity-only pricing widget render the channels / retention / nodes
    marginal steps between any two tiers off ONE round-trip without paying
    for the feature / runtime set diff on every row.

    Rung walk matches ``/tier-path``: visit every purchasable tier strictly
    between ``from`` and ``to`` plus the destination ``to`` itself, in
    tier-rank order. Same-rank siblings between the endpoints are both
    included; same-rank siblings of the destination are excluded so the
    path terminates exactly at ``to``. Each row's ``before`` side comes
    off the previous step's static caps (or ``from`` for the first row),
    so a consumer can fold the rows to reconstruct the cumulative
    ``tier_diff(from, to)['capacity_changes']`` shape.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<capacity_diff row>, ...],
        }

    Each ``<capacity_diff row>`` matches ``/capacity-diff`` exactly
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``
    where each axis is the same ``{before, after, delta, unlocked,
    locked}`` triple). Identity (``from == to``) returns an empty path.
    Lateral (same rank, different id) returns a single-row path. ``400``
    when ``from=`` or ``to=`` is missing; ``404`` when either id is
    unknown. ``trial`` IS accepted as an endpoint -- it is excluded from
    the walked rungs (not purchasable) but the endpoint computation
    still resolves. Never 5xxs: a resolver failure short-circuits to
    ``404`` so a pricing-page surface keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.capacity_diff_path(f, t)
        if path is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        from_rank = _ent.tier_rank(f)
        to_rank = _ent.tier_rank(t)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_capacity_diff_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/preview")
def api_entitlement_preview():
    """``GET /api/entitlement/preview?tier=<id>`` -- the full
    :meth:`Entitlement.to_dict` shape rendered for a hypothetical tier so an
    upgrade-CTA card can show concrete numbers ("365-day retention, unlimited
    channels, claude_code unlocked") without the client re-deriving per-tier
    capacity. ``404`` when the tier id is unknown."""
    target = (request.args.get("tier") or "").strip().lower()
    if not target:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.preview(target)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": target}), 404
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_preview: error: %s", exc)
        return jsonify({"error": "preview failed", "tier": target}), 500


@bp_entitlement.route("/api/entitlement/preview-batch")
def api_entitlement_preview_batch():
    """``GET /api/entitlement/preview-batch`` -- the full
    :meth:`Entitlement.to_dict` shape rendered for every purchasable tier
    in one pass. Plural sibling of ``/api/entitlement/preview``: where the
    singular endpoint returns one tier's row (and 404s on an unknown id),
    the batch returns the full pricing-page ladder in tier-rank order so a
    pricing-table UI can render the cumulative-state column off **one**
    round-trip instead of N calls.

    Cumulative-state companion to ``/api/entitlement/tier-unlocks-batch``
    (marginal grant per rung) and ``/api/entitlement/tier-locks-batch``
    (marginal loss per rung): pair the three to render the "what's at X /
    what's new at X / what you'd give up at X" three-column view of a
    pricing table without client-side composition.

    Response shape::

        {
          "tiers":             [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/preview`` exactly -- the
    full ``Entitlement.to_dict`` shape with ``source="preview"`` and
    ``grace=False`` so concrete per-tier capacity surfaces. The trial
    tier is excluded -- it is not purchasable, same posture as the
    singular helper. Row order matches ``/api/entitlement/tier-unlocks-batch``
    and ``/api/entitlement/tier-locks-batch`` rung-for-rung. Never 5xxs:
    a resolver failure yields an empty ``tiers`` list and the grace-shape
    envelope so the pricing page keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.preview_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_preview_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/preview-path")
def api_entitlement_preview_path():
    """``GET /api/entitlement/preview-path?from=<id>&to=<id>`` --
    arbitrary-endpoint stepwise cumulative-state path between any two
    tiers; the cumulative-state analogue of ``/tier-path`` (full
    ``tier_diff`` per rung), ``/capacity-diff-path`` (capacity-only per
    rung), ``/tier-unlocks-path`` (marginal grants per rung) and
    ``/tier-locks-path`` (marginal losses per rung) -- the fifth and
    final member of the ``_path`` family, the path-shaped sibling of
    ``/preview-batch``. Lets an upgrade-walkthrough surface render the
    "Cloud Pro: 90-day retention, unlimited channels, claude_code
    unlocked" card at every rung between any two tiers off ONE
    round-trip, without re-deriving capacity in JS.

    Each row in ``path`` is the full
    :meth:`Entitlement.to_dict` payload at that rung -- identical shape
    to a single ``/preview`` row, with ``source="preview"`` and
    ``grace=False`` so concrete per-tier capacity surfaces. Rung walk
    is byte-stable against ``/tier-path``, ``/capacity-diff-path``,
    ``/tier-unlocks-path`` and ``/tier-locks-path`` (same
    ``_PURCHASABLE_TIERS`` filter + same sort + same destination-sibling
    exclusion), so the five paths line up rung-for-rung.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<preview row>, ...],
        }

    Direction semantics:

    * ``upgrade`` (ascending) -- rows climb cumulatively rung by rung.
    * ``downgrade`` (descending) -- rows shrink cumulatively rung by
      rung; the cancellation-walkthrough counterpart.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the cumulative preview at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Same-rank siblings strictly between the endpoints are both
    included; same-rank siblings of the destination are excluded so the
    path terminates exactly at ``to``. ``400`` when ``from=`` or ``to=``
    is missing; ``404`` when either id is unknown. ``trial`` IS accepted
    as an endpoint -- it is excluded from the walked intermediate rungs
    (not purchasable) but is a valid endpoint via the lateral branch.
    Never 5xxs: a resolver failure short-circuits to ``404`` so an
    upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.preview_path(f, t)
        if path is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        from_rank = _ent.tier_rank(f)
        to_rank = _ent.tier_rank(t)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_preview_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks")
def api_entitlement_tier_unlocks():
    """``GET /api/entitlement/tier-unlocks?tier=<id>`` -- marginal unlocks
    for ``tier`` (features + runtimes that first become available at that
    tier vs the next-lower purchasable tier). Sibling of ``/preview``
    (cumulative shape). ``404`` when the tier id is unknown (including
    ``trial`` -- not purchasable)."""
    target = (request.args.get("tier") or "").strip().lower()
    if not target:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_unlocks(target)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": target}), 404
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks: error: %s", exc)
        return jsonify({"error": "tier-unlocks failed", "tier": target}), 500


@bp_entitlement.route("/api/entitlement/tier-unlocks-batch")
def api_entitlement_tier_unlocks_batch():
    """``GET /api/entitlement/tier-unlocks-batch`` -- marginal unlocks for
    every purchasable tier in one pass. Plural sibling of
    ``/api/entitlement/tier-unlocks``: where the singular endpoint
    returns one tier's row (and 404s on an unknown id), the batch
    returns the full pricing-page ladder in tier-rank order so a
    pricing-table UI can render the "what's new in X" column off
    **one** round-trip instead of N calls.

    Response shape::

        {
          "tiers":             [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-unlocks`` exactly
    (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``). The trial tier is excluded -- it is not purchasable,
    same posture as the singular helper. Never 5xxs: a resolver failure
    yields an empty ``tiers`` list and the grace-shape envelope so the
    pricing page keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tier_unlocks_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-path")
def api_entitlement_tier_unlocks_path():
    """``GET /api/entitlement/tier-unlocks-path?from=<id>&to=<id>`` --
    arbitrary-endpoint stepwise unlock path between any two tiers; the
    unlocks-focused analogue of ``/tier-path`` (full ``tier_diff`` per
    rung) and ``/capacity-diff-path`` (capacity-only per rung). Lets an
    upgrade-walkthrough surface render only the *newly-unlocked* features
    + runtimes at each rung between any two tiers off ONE round-trip,
    without the noise of the capacity axes or the symmetric ``lost_*``
    lists ``/tier-path`` carries.

    Each row in ``path`` is a :func:`clawmetry.entitlements.tier_unlocks`
    payload between the previous step in the path (or ``from`` for the
    first row) and the current rung -- so each row is a marginal-step
    unlock and a consumer can fold ``features`` / ``runtimes`` across
    rows to reconstruct the cumulative
    ``tier_diff(from, to)['added_*']`` shape (the same chain-property
    ``/tier-path`` and ``/capacity-diff-path`` enforce on their rows).
    Same-rank siblings strictly between the endpoints are both included;
    same-rank siblings of the destination are excluded so the path
    terminates exactly at ``to``. Rung walk is byte-stable against
    ``/tier-path`` and ``/capacity-diff-path``.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<tier_unlocks row>, ...],
        }

    Each ``<row>`` matches the singular ``/tier-unlocks`` row shape
    exactly (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``) -- with ``previous_tier`` chained from the path (the
    previous step), NOT the global next-lower-purchasable-tier anchor
    the singular helper uses.

    Direction semantics:

    * ``upgrade`` (ascending) -- each row's ``features`` / ``runtimes``
      are the marginal grant at that rung.
    * ``downgrade`` (descending) -- each row's ``features`` /
      ``runtimes`` are typically empty (use ``/tier-path`` for the
      marginal-loss view of a downgrade). The path still walks rungs so
      a UI keyed off rung shape keeps working.
    * ``lateral`` (same rank, different id) -- single-row path; carries
      the set difference between the two same-rank tier grants.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Identity (``from == to``) returns an empty path. Lateral (same rank,
    different id) returns a single-row path. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial`` IS
    accepted as an endpoint -- it is excluded from the walked rungs (not
    purchasable) but the endpoint computation still resolves. Never
    5xxs: a resolver failure short-circuits to ``404`` so an upgrade-
    walkthrough surface keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_unlocks_path(f, t)
        if path is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        from_rank = _ent.tier_rank(f)
        to_rank = _ent.tier_rank(t)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/next-tier-unlocks")
def api_entitlement_next_tier_unlocks():
    """``GET /api/entitlement/next-tier-unlocks`` -- marginal unlocks row
    for the rung immediately above the resolved entitlement, in
    :func:`clawmetry.entitlements.tier_unlocks` shape (``tier``,
    ``tier_label``, ``tier_rank``, ``previous_tier``, ``previous_tier_label``,
    ``previous_tier_rank``, ``features``, ``runtimes``).

    Current-relative convenience for ``/api/entitlement/tier-unlocks
    ?tier=<next_purchasable_tier>``; the upgrade-CTA companion to
    ``/api/entitlement/next-tier-diff`` (same marginal, ``upgrade_diff``
    shape). Returns ``{"unlocks": null, ...}`` at the ceiling
    (no rung above to upgrade to). Never 5xxs: a resolver failure
    short-circuits to the grace-shape envelope so the dashboard CTA
    keeps rendering instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.next_tier_unlocks()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "unlocks": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_unlocks: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "unlocks": None,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-unlocks")
def api_entitlement_previous_tier_unlocks():
    """``GET /api/entitlement/previous-tier-unlocks`` -- marginal unlocks row
    for the rung immediately below the resolved entitlement, in
    :func:`clawmetry.entitlements.tier_unlocks` shape.

    Current-relative convenience for ``/api/entitlement/tier-unlocks
    ?tier=<previous_purchasable_tier>``. Useful as a downgrade-confirmation
    detail row alongside :func:`previous_tier_diff` -- ``features`` /
    ``runtimes`` here are what the rung below *first* unlocked vs the rung
    below it (a tier-property), so a "you'd still keep X" copy can
    reference the same set the rung-below was originally sold on. Returns
    ``{"unlocks": null, ...}`` at the floor (no rung below). Never 5xxs.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.previous_tier_unlocks()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "unlocks": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_unlocks: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "unlocks": None,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-locks")
def api_entitlement_tier_locks():
    """``GET /api/entitlement/tier-locks?tier=<id>`` -- marginal locks for
    ``tier`` (features + runtimes that disappear when descending from
    the next-higher purchasable tier into ``tier``). Marginal-loss
    companion to ``/tier-unlocks``: where the unlocks endpoint answers
    "what does X first unlock vs the tier below it", this answers "what
    does X first lose vs the tier above it" -- the per-rung
    downgrade-warning row a step-down CTA renders, paired with
    ``/downgrade-path`` the way ``/tier-unlocks`` is paired with
    ``/upgrade-path``.

    Returns ``404`` when the tier id is unknown (including ``trial`` --
    not purchasable). Enterprise callers get a populated envelope with
    ``next_tier=null`` and empty loss lists (nothing above to step down
    from), not a 404 -- the tier is valid, the marginal just collapses
    to nothing.
    """
    target = (request.args.get("tier") or "").strip().lower()
    if not target:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_locks(target)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": target}), 404
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_tier_locks: error: %s", exc)
        return jsonify({"error": "tier-locks failed", "tier": target}), 500


@bp_entitlement.route("/api/entitlement/tier-locks-batch")
def api_entitlement_tier_locks_batch():
    """``GET /api/entitlement/tier-locks-batch`` -- marginal locks for
    every purchasable tier in one pass. Plural sibling of
    ``/api/entitlement/tier-locks``: where the singular endpoint
    returns one tier's row (and 404s on an unknown id), the batch
    returns the full purchasable ladder in tier-rank order so a
    downgrade-warning matrix can render the "what you'd give up at X"
    column off **one** round-trip instead of N calls.

    Marginal-loss companion to ``/api/entitlement/tier-unlocks-batch``:
    pair the two endpoints to render the upgrade-CTA + downgrade-warning
    columns on a pricing table without client-side composition.

    Response shape::

        {
          "tiers":             [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-locks`` exactly
    (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``). The trial tier is excluded -- it is not
    purchasable, same posture as the singular helper. Never 5xxs: a
    resolver failure yields an empty ``tiers`` list and the grace-shape
    envelope so the downgrade-warning UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tier_locks_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_locks_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-locks-path")
def api_entitlement_tier_locks_path():
    """``GET /api/entitlement/tier-locks-path?from=<id>&to=<id>`` --
    arbitrary-endpoint stepwise marginal-loss path between any two
    tiers; the locks-focused mirror of ``/tier-unlocks-path`` and the
    fourth member of the ``_path`` family alongside ``/tier-path`` (full
    ``tier_diff`` per rung) and ``/capacity-diff-path`` (capacity-only
    per rung). Lets a downgrade-walkthrough surface render only the
    *newly-lost* features + runtimes at each rung between any two tiers
    off ONE round-trip, without the noise of the capacity axes or the
    symmetric ``added_*`` lists ``/tier-path`` carries.

    Each row in ``path`` is a :func:`clawmetry.entitlements.tier_locks`
    payload between the previous step in the path (or ``from`` for the
    first row) and the current rung -- so each row is a marginal-step
    loss and a consumer can fold ``lost_features`` / ``lost_runtimes``
    across rows to reconstruct the cumulative
    ``tier_diff(from, to)['lost_*']`` shape (the same chain-property
    ``/tier-path``, ``/capacity-diff-path``, and ``/tier-unlocks-path``
    enforce on their rows). Same-rank siblings strictly between the
    endpoints are both included; same-rank siblings of the destination
    are excluded so the path terminates exactly at ``to``. Rung walk is
    byte-stable against ``/tier-path``, ``/capacity-diff-path``, and
    ``/tier-unlocks-path``.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<tier_locks row>, ...],
        }

    Each ``<row>`` matches the singular ``/tier-locks`` row shape
    exactly (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``) -- with ``next_tier`` chained from the path (the
    previous step), NOT the global next-higher-purchasable-tier anchor
    the singular helper uses.

    Direction semantics:

    * ``downgrade`` (descending) -- each row's ``lost_features`` /
      ``lost_runtimes`` are the marginal loss at that rung.
    * ``upgrade`` (ascending) -- each row's ``lost_features`` /
      ``lost_runtimes`` are typically empty (use ``/tier-unlocks-path``
      for the marginal-grant view of an upgrade). The path still walks
      rungs so a UI keyed off rung shape keeps working.
    * ``lateral`` (same rank, different id) -- single-row path; carries
      the set difference (``from`` minus ``to``) between the two
      same-rank tier grants.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Identity (``from == to``) returns an empty path. Lateral (same rank,
    different id) returns a single-row path. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial`` IS
    accepted as an endpoint -- it is excluded from the walked rungs (not
    purchasable) but the endpoint computation still resolves. Never
    5xxs: a resolver failure short-circuits to ``404`` so a downgrade-
    walkthrough surface keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_locks_path(f, t)
        if path is None:
            return (
                jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        from_rank = _ent.tier_rank(f)
        to_rank = _ent.tier_rank(t)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_locks_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/upgrade-path")
def api_entitlement_upgrade_path():
    """``GET /api/entitlement/upgrade-path`` -- ordered marginal-unlock
    ladder from the resolved tier upward.

    Current-user-relative sibling of ``/api/entitlement/tier-unlocks-batch``:
    where the batch returns the full purchasable ladder, this returns only
    tiers whose rank is *strictly above* the caller's resolved entitlement
    rank, so an upgrade-CTA wizard renders its step sequence without
    client-side filtering.

    Response shape::

        {
          "path":              [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-unlocks`` exactly
    (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``). Enterprise callers get an empty ``path`` (already at
    the top). Never 5xxs: a resolver failure yields ``path: []`` with the
    grace-shape envelope so the upgrade CTA keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "path": _ent.upgrade_path(),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_upgrade_path: error: %s", exc)
        return jsonify(
            {
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/downgrade-path")
def api_entitlement_downgrade_path():
    """``GET /api/entitlement/downgrade-path`` -- ordered cumulative-loss
    ladder from the resolved tier downward.

    Direction-flipped sibling of ``/api/entitlement/upgrade-path``: rows
    cover the purchasable tiers whose rank is strictly *below* the caller's
    resolved entitlement rank, closest rung first. Lets a downgrade-warning
    surface render every rung's full loss list without per-tier round-trips.

    Response shape::

        {
          "path":              [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` carries the destination tier metadata + the caller's
    current-tier context + ``lost_features`` / ``lost_runtimes`` cumulative
    over the gap (see :func:`clawmetry.entitlements.downgrade_path`). Floor
    callers (OSS / Cloud Free) get an empty ``path`` -- no rung below to
    descend to. Never 5xxs: a resolver failure yields ``path: []`` with the
    grace-shape envelope so the downgrade CTA keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "path": _ent.downgrade_path(),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_downgrade_path: error: %s", exc)
        return jsonify(
            {
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


_CAPACITY_PARAMS = ("channels", "retention_days", "nodes")


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
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
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
                            "retention_days=, or nodes="
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
        elif retention_present:
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
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                allowed = ent.allows_node_count(nodes_n)
            else:
                # Same never-crash posture as the channels / retention_days
                # branches -- a blank or non-int ``nodes`` swallows to
                # ``required_tier=None`` rather than 500ing.
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
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime:
            key, kind = runtime, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
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
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
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
                            "retention_days=, or nodes="
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        if feature:
            key, kind = feature, "feature"
            allowed = ent.allows_feature(feature)
            required = _ent.min_tier_for_feature(feature)
            reason = ent.lock_reason(key, kind=kind)
        elif runtime:
            key, kind = runtime, "runtime"
            allowed = ent.allows_runtime(runtime)
            required = _ent.min_tier_for_runtime(runtime)
            reason = ent.lock_reason(key, kind=kind)
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok:
                required = _ent.min_tier_for_channel_count(channels_n)
                allowed = ent.allows_channel_count(channels_n)
                reason = ent.lock_reason(str(channels_n), kind=kind)
            else:
                # Blank / non-int: mirror the required-tier wrapper's
                # never-crash posture -- ``reason`` is None so the UI has
                # nothing to render, ``required_tier`` is None, and
                # ``allowed`` defaults to True (same as
                # ``allows_channel_count`` swallowing a non-int to True).
                required = None
                allowed = True
                reason = None
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                allowed = ent.allows_retention_window(retention_n)
                reason = ent.lock_reason(str(retention_n), kind=kind)
            else:
                # Same never-crash posture as the channels branch. Important:
                # don't forward ``None`` to
                # :func:`min_tier_for_retention_window` -- there ``None`` is
                # the *unlimited* sentinel and would mis-route to Enterprise.
                required = None
                allowed = True
                reason = None
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                allowed = ent.allows_node_count(nodes_n)
                reason = ent.lock_reason(str(nodes_n), kind=kind)
            else:
                # Same never-crash posture as the other capacity branches --
                # a blank or non-int ``nodes`` swallows to ``reason=None``.
                required = None
                allowed = True
                reason = None
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
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime:
            key, kind = runtime, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
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


def _parse_csv_arg(name: str) -> list[str]:
    """Parse a comma-separated query arg into a normalised id list.

    Empty / whitespace tokens are dropped; remaining tokens are lowercased and
    deduplicated while preserving first-seen order so the response payload is
    stable. ``features=otel_export,,sso,otel_export`` -> ``["otel_export", "sso"]``.
    Never raises (a missing arg returns ``[]``).
    """
    raw = request.args.get(name, "") or ""
    out: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        t = token.strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


@bp_entitlement.route("/api/entitlement/required-tier-batch")
def api_entitlement_required_tier_batch():
    """``GET /api/entitlement/required-tier-batch?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- aggregate sibling of
    ``/api/entitlement/required-tier``.

    Returns the cheapest *purchasable* tier admitting **all** supplied
    constraints across every capacity axis at once: the most-constraining
    item across all five wins. Wraps :func:`min_tier_for_all` so a
    dashboard surface that mixes axes ("you are using fleet + claude_code
    + 5 channels + 30-day retention + 2 nodes -- Available in Pro") gets
    the answer in one round-trip instead of five calls + max-by-rank on
    the client.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty / parseable
    after normalisation). ``features=`` / ``runtimes=`` take comma-separated
    tokens (whitespace and duplicates are normalised away; unknown ids
    contribute nothing). The three capacity axes take a single int each;
    a blank or non-int value is treated as "not supplied" (matches the
    singular endpoint's never-crash posture rather than mis-routing a typo
    to Enterprise). Never 5xxs: the OSS-free shape is returned on any
    resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, channels_raw) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, retention_raw) = _parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, nodes_raw) = _parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        required = _ent.min_tier_for_all(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None

        feat_allowed = all(ent.allows_feature(f) for f in features)
        runtime_allowed = all(ent.allows_runtime(r) for r in runtimes)
        channels_allowed = (
            ent.allows_channel_count(channels_n) if channels_ok else True
        )
        retention_allowed = (
            ent.allows_retention_window(retention_n) if retention_ok else True
        )
        nodes_allowed = ent.allows_node_count(nodes_n) if nodes_ok else True
        allowed = (
            feat_allowed
            and runtime_allowed
            and channels_allowed
            and retention_allowed
            and nodes_allowed
        )

        return jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
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
        logger.warning("api_entitlement_required_tier_batch: error: %s", exc)
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")
        return jsonify(
            {
                "features": _parse_csv_arg("features"),
                "runtimes": _parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
                "allowed": True,
            }
        )


@bp_entitlement.route("/api/entitlement/affordable-tiers")
def api_entitlement_affordable_tiers():
    """``GET /api/entitlement/affordable-tiers?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- plural sibling of
    ``/api/entitlement/required-tier-batch``.

    ``/required-tier-batch`` returns only the *floor* tier admitting a
    constraint bundle. ``/affordable-tiers`` returns the **full ordered
    list** of purchasable tiers admitting the same bundle, so a pricing-
    page surface can render "you need at least Starter -- Pro and
    Enterprise also qualify" off ONE round-trip instead of resolving the
    floor and then walking the catalog client-side.

    Args are byte-identical to ``/required-tier-batch``: at least one of
    ``features=`` / ``runtimes=`` / ``channels=`` / ``retention_days=`` /
    ``nodes=`` must be supplied (non-empty / parseable after normalisation).
    Same CSV normalisation, same capacity-axis parsing, same ``None`` =
    "not supplied" sentinel (so ``retention_days=`` blank is "unset", NOT
    the "unlimited" sentinel that would mis-route to Enterprise).

    Envelope::

        {
            "features":       [...],            # echoed, normalised
            "runtimes":       [...],            # echoed, normalised
            "channels":       <int|None>,
            "retention_days": <int|None>,
            "nodes":          <int|None>,
            "current_tier":      "<id>",
            "current_tier_rank": <int>,
            "minimum_tier":      "<id|null>",   # floor; null on resolver miss
            "minimum_tier_label":"<human|null>",
            "minimum_tier_rank": <int>,         # -1 on resolver miss
            "tiers": [                          # ordered rank ascending
                {
                    "tier":               "<id>",
                    "tier_label":         "<human>",
                    "tier_rank":          <int>,
                    "is_minimum":         <bool>,  # True on first row only
                    "is_current":         <bool>,
                    "is_current_or_better": <bool>,
                },
                ...
            ]
        }

    Decoupled from the resolved entitlement off the helper side: grace vs
    enforce yields identical ``tiers`` rows. ``current_tier`` /
    ``is_current`` / ``is_current_or_better`` are layered on the response
    here (not the helper) so the helper stays a pure tier-catalog walker
    while the HTTP wrapper still answers "where am I" off one call.

    Never 5xxs: the OSS-free shape (empty tier list, current_tier=oss) is
    returned on any resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        rows = _ent.affordable_tiers(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        ) or []

        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        minimum_tier = rows[0]["tier"] if rows else None
        minimum_label = rows[0]["tier_label"] if rows else None
        minimum_rank = rows[0]["tier_rank"] if rows else -1

        augmented: list[dict] = []
        for row in rows:
            augmented.append(
                {
                    "tier": row["tier"],
                    "tier_label": row["tier_label"],
                    "tier_rank": row["tier_rank"],
                    "is_minimum": row["is_minimum"],
                    "is_current": row["tier"] == cur_tier,
                    "is_current_or_better": row["tier_rank"] >= cur_rank,
                }
            )

        return jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "minimum_tier": minimum_tier,
                "minimum_tier_label": minimum_label,
                "minimum_tier_rank": minimum_rank,
                "tiers": augmented,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_affordable_tiers: error: %s", exc)
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")
        return jsonify(
            {
                "features": _parse_csv_arg("features"),
                "runtimes": _parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "minimum_tier": None,
                "minimum_tier_label": None,
                "minimum_tier_rank": -1,
                "tiers": [],
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier")
def api_entitlement_min_tier():
    """``GET /api/entitlement/min-tier?feature=<f>`` or ``?runtime=<r>`` --
    cheapest purchasable tier that unlocks the named feature or runtime.

    Catalogue-derived, so the answer is identical in grace and enforce mode.
    Response shape::

        {
          "key":        "feature" | "runtime",
          "value":      "<input>",
          "free":       <bool>,           # true when min_tier == OSS
          "min_tier":   "<tier id>" | null,
          "tier_label": "<Display Label>" | null,
          "tier_rank":  <int> | null,
        }

    400 when neither ``feature`` nor ``runtime`` is supplied (or both are).
    404 when the input id is unknown -- the caller can show a neutral
    "not available" hint rather than pointing at a nonsense tier. Never 5xxs.
    """
    feature = (request.args.get("feature") or "").strip()
    runtime = (request.args.get("runtime") or "").strip().lower()
    if bool(feature) == bool(runtime):
        return (
            jsonify(
                {
                    "error": "exactly one of feature= or runtime= is required",
                }
            ),
            400,
        )
    try:
        from clawmetry import entitlements as _ent

        if feature:
            min_t = _ent.min_tier_for_feature(feature)
            key, value = "feature", feature
            known = feature in _ent.ALL_FEATURES
        else:
            min_t = _ent.min_tier_for_runtime(runtime)
            key, value = "runtime", runtime
            known = runtime in _ent.ALL_RUNTIMES
        if not known:
            return (
                jsonify(
                    {
                        "key": key,
                        "value": value,
                        "free": False,
                        "min_tier": None,
                        "tier_label": None,
                        "tier_rank": None,
                        "error": "unknown",
                    }
                ),
                404,
            )
        return jsonify(
            {
                "key": key,
                "value": value,
                "free": min_t == _ent.TIER_OSS,
                "min_tier": min_t,
                "tier_label": _ent.tier_label(min_t) if min_t else None,
                "tier_rank": _ent.tier_rank(min_t) if min_t else None,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_min_tier: error: %s", exc)
        return jsonify(
            {
                "key": "feature" if feature else "runtime",
                "value": feature or runtime,
                "free": False,
                "min_tier": None,
                "tier_label": None,
                "tier_rank": None,
            }
        )


@bp_entitlement.route("/api/entitlement/lock-reason-batch")
def api_entitlement_lock_reason_batch():
    """``GET /api/entitlement/lock-reason-batch?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-item plural sibling of
    ``/api/entitlement/lock-reason``.

    Where ``/required-tier-batch`` aggregates the most-constraining axis into
    one tier answer, this preserves the per-item detail so a Settings or
    paywall matrix UI ("show me each runtime + feature row with its
    individual lock + required tier") renders off **one** round-trip instead
    of N calls to ``/lock-reason``.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied. ``features=`` /
    ``runtimes=`` take comma-separated tokens (whitespace + duplicates are
    normalised away; unknown ids contribute a grace-shape row -- they don't
    error). The three capacity axes take a single int each; a blank or
    non-int value is treated as "not supplied" (matches the singular
    endpoint's never-crash posture rather than mis-routing a typo to
    Enterprise). Never 5xxs: the per-axis grace shape is returned on any
    resolver failure.

    Response shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":   "...",
          "current_tier_rank": <int>,
          "grace":          <bool>,
          "enforced":       <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason``, ``locked``,
    ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank``.
    """
    try:
        from clawmetry import entitlements as _ent

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        batch = _ent.lock_reasons_batch(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason_batch: error: %s", exc)
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
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


@bp_entitlement.route("/api/entitlement/tiers-for")
def api_entitlement_tiers_for():
    """``GET /api/entitlement/tiers-for?feature=<id>`` (or
    ``?runtime=<id>``) -- inverse of ``/required-tier``: returns the
    full ladder of tiers that grant the named feature or runtime, not
    just the cheapest one. The "Available in: Pro, Self-hosted Pro,
    Trial, Enterprise" availability list a pricing-page row or feature
    tooltip needs.

    Exactly one of ``feature=`` or ``runtime=`` must be supplied -- a
    missing key is ``400``, both keys at once is ``400`` (no implicit
    precedence so callers cannot accidentally query the wrong axis).
    An unknown id (not in ``ALL_FEATURES`` / ``ALL_RUNTIMES``) is
    ``404``. Never 5xxs.
    """
    feat = (request.args.get("feature") or "").strip().lower()
    rt = (request.args.get("runtime") or "").strip().lower()
    if not feat and not rt:
        return jsonify({"error": "missing feature or runtime"}), 400
    if feat and rt:
        return jsonify(
            {"error": "pass feature OR runtime, not both"}
        ), 400
    try:
        from clawmetry import entitlements as _ent

        if feat:
            body = _ent.tiers_for_feature(feat)
            kind = "feature"
            item = feat
        else:
            body = _ent.tiers_for_runtime(rt)
            kind = "runtime"
            item = rt
        if body is None:
            return jsonify({"error": f"unknown {kind}", kind: item}), 404
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_tiers_for: error: %s", exc)
        return jsonify({"error": "tiers-for failed"}), 500


@bp_entitlement.route("/api/entitlement/tiers-for-batch")
def api_entitlement_tiers_for_batch():
    """``GET /api/entitlement/tiers-for-batch`` -- full availability
    ladder for every feature *and* runtime in one pass. Plural sibling
    of ``/api/entitlement/tiers-for``: where the singular endpoint
    returns one feature-or-runtime row (and 400s on a missing axis,
    404s on an unknown id), the batch returns both surfaces in tier-rank
    order so a pricing-table / feature-comparison matrix UI can render
    the full "Available in X" grid off **one** round-trip instead of an
    N+1 fan-out.

    Response shape::

        {
          "features":          [<row>, ...],
          "runtimes":          [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tiers-for`` exactly
    (``item``, ``kind``, ``label``, ``free``, ``min_tier``,
    ``min_tier_label``, ``min_tier_rank``, ``tiers``). Never 5xxs: a
    resolver failure yields empty ``features`` / ``runtimes`` lists and
    the grace-shape envelope so the pricing UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_batch()
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "features": body.get("features", []),
                "runtimes": body.get("runtimes", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tiers_for_batch: error: %s", exc)
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
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


@bp_entitlement.route("/api/entitlement/feature-spec")
def api_entitlement_feature_spec():
    """``GET /api/entitlement/feature-spec?feature=<id>`` -- scalar
    sibling of ``/api/features``: return the single catalogue row a
    feature-detail page or upgrade tooltip needs without forcing the
    caller to fetch the full ladder and filter client-side.

    Response shape matches a row from ``feature_catalog()`` exactly
    (``id``, ``label``, ``tier``, ``tiers``, ``free``, ``allowed``,
    ``locked``, ``entitled``, ``alias``).

    - **400** when ``feature=`` is missing / blank.
    - **404** for unknown ids (the requested id is echoed back so the
      caller can render ``"unknown feature"``).
    - Never 5xxs: a resolver failure still returns the catalogue row
      built against the OSS-free fallback.
    """
    feat_raw = request.args.get("feature")
    if feat_raw is None or not feat_raw.strip():
        return jsonify({"error": "missing feature"}), 400
    feat = feat_raw.strip().lower()
    try:
        from clawmetry import entitlements as _ent

        row = _ent.feature_spec(feat)
        if row is None:
            return jsonify({"error": "unknown feature", "feature": feat}), 404
        return jsonify(row)
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec: error: %s", exc)
        return jsonify({"error": "feature-spec failed", "feature": feat}), 500


@bp_entitlement.route("/api/entitlement/runtime-spec")
def api_entitlement_runtime_spec():
    """``GET /api/entitlement/runtime-spec?runtime=<id>`` -- scalar
    sibling of ``/api/runtimes``: return the single catalogue row a
    runtime-detail page or upgrade tooltip needs without forcing the
    caller to fetch the full ladder and filter client-side.

    Accepts the canonical id (``claude_code``) or any registered alias
    (``claude-code``) -- the response always echoes the canonical id.

    Response shape matches a row from ``runtime_catalog()`` exactly
    (``id``, ``label``, ``free``, ``tier``, ``tiers``, ``allowed``,
    ``locked``, ``entitled``).

    - **400** when ``runtime=`` is missing / blank.
    - **404** for unknown ids (the requested id is echoed back so the
      caller can render ``"unknown runtime"``).
    - Never 5xxs: a resolver failure still returns the catalogue row
      built against the OSS-free fallback.
    """
    rt_raw = request.args.get("runtime")
    if rt_raw is None or not rt_raw.strip():
        return jsonify({"error": "missing runtime"}), 400
    rt_input = rt_raw.strip().lower()
    try:
        from clawmetry import entitlements as _ent

        row = _ent.runtime_spec(rt_input)
        if row is None:
            return jsonify({"error": "unknown runtime", "runtime": rt_input}), 404
        return jsonify(row)
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec: error: %s", exc)
        return jsonify({"error": "runtime-spec failed", "runtime": rt_input}), 500


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
