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
  GET  /api/entitlement/tiers-for-at  -- hypothetical-perspective sibling of
                                         ``/tiers-for``: same ladder scoped
                                         by a caller-supplied
                                         ``tier=<perspective>`` so an ``_at``
                                         walkthrough URL is uniform across
                                         every ``_at`` sibling.
  GET  /api/entitlement/tiers-for-batch-at -- hypothetical-perspective sibling
                                         of ``/tiers-for-batch``: every
                                         known feature + runtime in one pass
                                         scoped by ``tier=<perspective>``.
  GET  /api/runtimes                  -- the full runtime catalog.
  GET  /api/tiers                     -- the full tier ladder with per-tier metadata.
  GET  /api/entitlement/feature-catalog  -- bare sibling of
                                         ``/feature-catalog-at``: the resolved
                                         feature catalogue wrapped in the same
                                         ``{tier, features, grace, enforced}``
                                         envelope the ``-at`` sibling uses, so
                                         a client hydrating every catalog
                                         variant (bare, ``-at``,
                                         ``-at-batch``, ``-path``, ...) can do
                                         it off one prefix instead of mixing
                                         ``/api/features`` with
                                         ``/api/entitlement/feature-catalog-at``.
  GET  /api/entitlement/runtime-catalog  -- bare sibling of
                                         ``/runtime-catalog-at`` for the
                                         runtime axis; same envelope shape.
  GET  /api/entitlement/tier-catalog  -- bare sibling of
                                         ``/tier-catalog-at`` for the tier
                                         ladder; same envelope shape (with
                                         the resolved tier mirrored into the
                                         ``tier`` key to match the ``-at``
                                         sibling).
  GET  /api/entitlement/tier-spec     -- scalar sibling of ``/api/tiers``:
                                         full per-tier descriptor for one
                                         ``tier=`` key (label, rank,
                                         retention, channel/node limits,
                                         features + paid runtimes carried)
                                         so a pricing-page column / upsell
                                         tooltip can hydrate off one
                                         round-trip instead of walking the
                                         full ladder client-side.
  GET  /api/entitlement/tier-catalog-at -- what-if sibling of the tier
                                         ladder: returns the full
                                         ``tier_catalog`` rows but with
                                         ``is_current`` recomputed as if
                                         the install were on the named
                                         ``tier=`` instead of the live
                                         resolved entitlement. Mirrors
                                         ``/feature-catalog-at`` and
                                         ``/runtime-catalog-at`` for the
                                         tier ladder so a pricing-
                                         comparison UI can render any
                                         hypothetical "current tier"
                                         without first switching the live
                                         resolver.
  GET  /api/entitlement/tier-catalog-at-batch -- batch what-if sibling
                                         of ``/tier-catalog-at``: full tier
                                         ladders for N hypothetical source
                                         tiers (``?tiers=a,b,c``) off ONE
                                         call, each with ``is_current``
                                         flipped to its own source. Mirrors
                                         ``/feature-catalog-at-batch`` and
                                         ``/runtime-catalog-at-batch`` on the
                                         tier axis so a pricing-comparison
                                         matrix UI can render the ladder
                                         side-by-side from every hypothetical
                                         perspective off ONE round-trip
                                         instead of N calls.
  GET  /api/entitlement/tier-spec-at  -- scalar what-if sibling of
                                         ``/tier-catalog-at``: the single
                                         tier descriptor for ``target=`` with
                                         ``is_current`` computed as if the
                                         install were on ``tier=``. Lets a
                                         pricing-comparison tooltip hydrate
                                         against ONE tier descriptor from a
                                         hypothetical perspective in one
                                         round-trip instead of fetching the
                                         full ``/tier-catalog-at`` payload.
  GET  /api/entitlement/tier-spec-path -- arbitrary-endpoint stepwise spec-
                                         shaped path between any two tiers
                                         (``?from=&to=``); path-shaped
                                         sibling of ``/tier-spec-at-batch``
                                         and spec-shaped sibling of
                                         ``/tier-path`` / ``/capacity-diff-
                                         path`` / ``/tier-unlocks-path`` /
                                         ``/tier-locks-path`` / ``/preview-
                                         path``. Each row is a
                                         ``tier_spec_at`` row pinned on
                                         ``from=`` for ``target=<rung>``, so
                                         the marketing-shaped descriptor
                                         (``label``, ``is_paid``,
                                         ``unlocks_paid_runtimes``,
                                         ``retention_days``,
                                         ``channel_limit``, ``node_limit``,
                                         ``features``, ``runtimes``) hydrates
                                         at every rung between two tiers
                                         off one round-trip.
  GET  /api/entitlement/feature-catalog-path -- arbitrary-endpoint
                                         stepwise feature-catalog path between
                                         any two tiers (``?from=&to=``); the
                                         full-catalog sibling of
                                         ``/feature-spec-path`` and the path-
                                         shaped sibling of
                                         ``/feature-catalog-at-batch``. Each
                                         row is a ``/feature-catalog-at``
                                         payload at ``rung=<tier>`` so an
                                         upgrade-walkthrough surface hydrates
                                         every rung's full catalogue off one
                                         round-trip.
  GET  /api/entitlement/runtime-catalog-path -- runtime-axis twin of
                                         ``/feature-catalog-path``. Together
                                         the pair lets an upgrade-walkthrough
                                         UI render every feature + runtime
                                         column at every rung off two calls
                                         instead of first walking
                                         ``/tier-path`` and then hydrating
                                         each rung individually.
  GET  /api/entitlement/tier-catalog-path -- tier-axis twin of
                                         ``/feature-catalog-path`` /
                                         ``/runtime-catalog-path``. Each row
                                         is a ``/tier-catalog-at`` payload at
                                         ``rung=<tier>`` so an upgrade-
                                         walkthrough surface hydrates the
                                         full pricing ladder at every rung
                                         between two tiers off one round-
                                         trip. Together the three
                                         ``_catalog_path`` endpoints render
                                         every tier + feature + runtime
                                         column at every rung off three calls
                                         instead of walking ``/tier-path``
                                         and hydrating each rung
                                         individually.
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


@bp_entitlement.route("/api/entitlement/capacity-diff-at")
def api_entitlement_capacity_diff_at():
    """``GET /api/entitlement/capacity-diff-at?tier=<source>&target=<dest>``
    -- scalar what-if sibling of ``/api/entitlement/capacity-diff``: per-
    axis capacity transition (channels / retention / nodes) from a
    caller-supplied ``tier`` to ``target``, computed off the static
    per-tier caps rather than the resolved entitlement
    ``/capacity-diff`` anchors to.

    Lets a pricing-comparison tooltip render "capacity at B vs A" for
    any ``(A, B)`` pair in one round-trip without fetching the full
    ``/capacity-diff-path?from=A&to=B`` payload and reading the
    destination row client-side. The returned row matches the
    destination row of ``/capacity-diff-path`` for the same pair --
    a parity test pins this so the scalar what-if and the path-walker
    cannot drift.

    Accepts any tier id in :data:`entitlements._TIER_FEATURES` on either
    argument (including ``trial``), matching the other ``_at`` family
    endpoints. Direction is not normalised: an upgrade pair flips
    ``unlocked`` on axes that go from a finite cap to unlimited; a
    downgrade pair flips ``locked`` on axes that go from unlimited to
    finite; identity / lateral-rank pairs collapse every axis to a
    no-op triple.

    Response shape::

        {
          "tier":   "<source tier id>",
          "target": "<destination tier id>",
          "row":    {<capacity_diff row>},
        }

    The inner ``row`` matches the singular ``/capacity-diff`` row shape
    exactly (``target``, ``channel_limit``, ``retention_days``,
    ``node_limit`` where each axis is the same ``{before, after, delta,
    unlocked, locked}`` triple) -- with the ``before`` side carrying the
    caller-supplied ``tier``'s static caps (NOT the resolved
    entitlement's caps the singular endpoint uses).

    - **400** when either ``tier=`` or ``target=`` is missing / blank.
    - **404** when ``tier`` or ``target`` is unknown. The body carries
      ``which`` so a caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure falls through to a 404 so the
      tooltip surface stays mute instead of breaking.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_target = request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target_in,
                    }
                ),
                404,
            )
        row = _ent.capacity_diff_at(tier_in, target_in)
        if row is None:
            return (
                jsonify(
                    {
                        "error": "capacity-diff-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        logger.warning("api_entitlement_capacity_diff_at: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "capacity-diff-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/capacity-diff-at-batch")
def api_entitlement_capacity_diff_at_batch():
    """``GET /api/entitlement/capacity-diff-at-batch?tier=<source>`` --
    what-if + batch sibling of ``/api/entitlement/capacity-diff-batch``:
    per-axis capacity-transition rows for every purchasable tier as a
    target, computed against the caller-supplied ``tier`` rather than
    the resolved entitlement ``/capacity-diff-batch`` anchors to.

    Composes the scalar what-if (``/capacity-diff-at``) and the live
    batch (``/capacity-diff-batch``) -- same row shape and ordering as
    the live batch, same hypothetical perspective as the ``_at``
    endpoint. Lets a pricing-comparison matrix UI render the "capacity
    vs <hypothetical-tier>" column for every rung off **one** round-
    trip instead of N calls to ``/capacity-diff-at``.

    Pair with ``/tier-unlocks-at-batch`` (marginal feature/runtime
    grant per rung) and ``/tier-locks-at-batch`` (marginal loss per
    rung) to render the full "what's new at X / what you'd give up at
    X / capacity at X" view of a pricing matrix pivoted around any
    hypothetical perspective tier without client-side composition.

    Accepts any tier id in :data:`entitlements._TIER_FEATURES` on the
    ``tier`` arg (including ``trial``), matching the other ``_at``
    family endpoints. The target list mirrors ``/capacity-diff-batch``
    (purchasable tiers only -- trial excluded), so the rows match the
    live batch's target axis byte-for-byte and the response can be
    folded into the same pricing-page table.

    Response shape::

        {
          "tier":              "<source tier id>",
          "tiers":             [<row>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/capacity-diff-at`` for
    the same ``(tier, target)`` pair exactly (``target``,
    ``channel_limit``, ``retention_days``, ``node_limit``) -- with the
    ``before`` side carrying the caller-supplied ``tier``'s static
    caps (NOT the resolved entitlement's caps the live batch uses).

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.capacity_diff_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_capacity_diff_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-diff-at")
def api_entitlement_tier_diff_at():
    """``GET /api/entitlement/tier-diff-at?tier=<perspective>&from=<from>
    &to=<to>`` -- arbitrary-endpoint diff between two tiers, rendered
    from a hypothetical ``perspective_tier``.

    What-if sibling of ``/tier-diff``: same payload shape, plus a
    ``perspective_tier`` echo so a pricing-comparison tooltip surface
    can call ``X_at(perspective, from, to)`` uniformly across the whole
    ``_at`` scalar family (alongside ``/capacity-diff-at``,
    ``/tier-unlocks-at``, ``/tier-locks-at``, ``/tier-catalog-at`` and
    the ``_at_path`` walk siblings). Closes the ``_at`` slot of the
    ``tier_diff`` family alongside the existing ``/tier-diff-at-batch``
    (walk every purchasable target from one source) and the
    ``/tier-path-at`` walk-shape sibling in the open ``tier_path_at``
    PR.

    Body posture matches ``/tier-catalog-at-path``: perspective is
    validated against :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    but does NOT shape rows -- the diff is anchored to ``from`` /
    ``to``. A parity test pins the response body against
    ``/tier-diff?from=<from>&to=<to>`` for every valid perspective so
    the ``_at`` prefix cannot silently drift into shaping rows.

    Response body extends the ``/tier-diff`` shape with three extra
    fields at the top so a consumer can echo the perspective in a
    "Comparing A vs B from perspective P" tooltip without a second
    round-trip::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "perspective_tier_label":"...",
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "added_features":        [...],
          "lost_features":         [...],
          "added_runtimes":        [...],
          "lost_runtimes":         [...],
          "capacity_changes":      {...},
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank.
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender).
    - **200** on the happy path with the shape above.
    - Never 5xxs: a resolver failure short-circuits to 404 so a
      pricing-comparison tooltip keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        body = _ent.tier_diff_at(p, f, t)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
                404,
            )
        out = {
            "perspective_tier": p,
            "perspective_tier_rank": _ent.tier_rank(p),
            "perspective_tier_label": _ent.tier_label(p),
        }
        out.update(body)
        return jsonify(out)
    except Exception as exc:
        logger.warning("api_entitlement_tier_diff_at: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-diff-at-batch")
def api_entitlement_tier_diff_at_batch():
    """``GET /api/entitlement/tier-diff-at-batch?tier=<source>`` --
    what-if + batch sibling of ``/api/entitlement/tier-diff-batch``:
    full marginal :func:`tier_diff` payload between the caller-supplied
    ``tier`` and every purchasable tier as a target, in one pass.

    Composes the arbitrary-endpoint diff (``/tier-diff``) and the live
    batch (``/tier-diff-batch``) -- same row shape and ordering as the
    live batch, but every row's ``from`` side is anchored to the
    caller-supplied ``tier`` instead of the per-rung next-lower-
    purchasable anchor ``/tier-diff-batch`` carries. Lets a pricing-
    comparison matrix UI render the "full marginal vs <hypothetical-
    tier>" column for every rung off **one** round-trip instead of N
    calls to ``/tier-diff``.

    The "all-slices-in-one-row" member of the ``_at`` batch family
    alongside ``/tier-unlocks-at-batch`` (marginal feature/runtime
    grant slice), ``/tier-locks-at-batch`` (marginal feature/runtime
    loss slice) and ``/capacity-diff-at-batch`` (capacity slice). Pair
    them to render the full "what's new at X / what you'd give up at
    X / capacity at X" view of a pricing matrix pivoted around any
    hypothetical perspective tier without client-side composition;
    this endpoint folds the three slices into one row for callers that
    prefer a single call.

    Accepts any tier id in :data:`entitlements._TIER_FEATURES` on the
    ``tier`` arg (including ``trial``), matching the other ``_at``
    family endpoints. The target list mirrors ``/tier-diff-batch``
    (purchasable tiers only -- trial excluded), so the rows match the
    live batch's target axis byte-for-byte and the response can be
    folded into the same pricing-page table.

    Response shape::

        {
          "tier":              "<source tier id>",
          "tiers":             [<row>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-diff`` for the same
    ``(from=tier, to=target)`` pair exactly -- ``from``, ``from_label``,
    ``from_rank``, ``to``, ``to_label``, ``to_rank``, ``direction``,
    ``added_features``, ``lost_features``, ``added_runtimes``,
    ``lost_runtimes``, ``capacity_changes`` -- with ``from`` byte-equal
    to the caller-supplied ``tier`` on every row.

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_diff_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_diff_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
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


@bp_entitlement.route("/api/entitlement/preview-at")
def api_entitlement_preview_at():
    """``GET /api/entitlement/preview-at?tier=<perspective>&target=<id>`` --
    what-if sibling of ``/api/entitlement/preview``: the full
    :meth:`Entitlement.to_dict` snapshot at ``target`` rendered from the
    perspective of a hypothetical ``tier``.

    Fills the ``_at`` slot in the preview family alongside
    ``/api/entitlement/tier-spec-at``,
    ``/api/entitlement/feature-spec-at``,
    ``/api/entitlement/runtime-spec-at``,
    ``/api/entitlement/capacity-diff-at``,
    ``/api/entitlement/tier-unlocks-at``,
    ``/api/entitlement/tier-locks-at`` and
    ``/api/entitlement/lock-reason-at``. Lets a pricing-comparison
    tooltip hydrate one cumulative-state row from a hypothetical
    perspective in ONE round-trip using the uniform
    ``X_at(perspective, target)`` request shape the rest of the ``_at``
    family already exposes.

    Unlike ``/api/entitlement/preview`` (which 404s the non-purchasable
    :data:`TIER_TRIAL`), ``/preview-at`` accepts trial as a target and
    returns the trial preview row -- lenient ``_at`` posture matching
    ``/tier-spec-at`` / ``/feature-spec-at`` / ``/runtime-spec-at``. The
    perspective tier is validated but does not shape the returned row
    (byte-parity with :func:`entitlements._preview_row` holds for every
    perspective / target combination).

    Row shape matches ``/api/entitlement/preview`` exactly -- the full
    ``Entitlement.to_dict`` payload with ``source="preview"`` and
    ``grace=False`` so concrete per-tier capacity surfaces.

    - **400** when ``tier=`` or ``target=`` is missing / blank
    - **404** when ``tier`` is not in :data:`entitlements._TIER_ORDER`
      or ``target`` is not in :data:`entitlements._TIER_FEATURES`; the
      body carries ``which`` so a caller can render the right
      "unknown ..." message
    - **Never 5xxs**: the helper reads only the static per-tier maps, so
      a resolver failure short-circuits to ``404`` instead of 500
    """
    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    raw_target = request.args.get("target")
    target = (raw_target or "").strip().lower()
    if not target:
        return jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if target not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target,
                    }
                ),
                404,
            )
        body = _ent.preview_at(tier, target)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "preview-at failed",
                        "tier": tier,
                        "target": target,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier, "target": target, "preview": body})
    except Exception as exc:
        logger.warning("api_entitlement_preview_at: error: %s", exc)
        return jsonify({"error": "preview-at failed"}), 500


@bp_entitlement.route("/api/entitlement/preview-at-batch")
def api_entitlement_preview_at_batch():
    """``GET /api/entitlement/preview-at-batch?tier=<perspective>
    &targets=a,b,c`` -- what-if + batch sibling of
    ``/api/entitlement/preview-at``.

    Where ``/preview-at`` hydrates ONE cumulative-state row from a
    hypothetical perspective, this hydrates N rows for a caller-supplied
    subset of target tiers off a single round-trip. Fixed-perspective
    multi-target companion of ``/preview-at`` and
    caller-supplied-targets sibling of ``/preview-batch`` (which walks
    :data:`_PURCHASABLE_TIERS` unconditionally). Fills the ``_at_batch``
    slot alongside ``/api/entitlement/tier-spec-at-batch``,
    ``/api/entitlement/feature-spec-at-batch``,
    ``/api/entitlement/runtime-spec-at-batch``.

    Use case: a pricing-comparison matrix UI ("from my perspective tier,
    render the cumulative-state row for OSS, Cloud Starter, Cloud Pro
    and Enterprise") hydrates every column off ONE call instead of N
    calls to ``/preview-at``.

    Each ``tiers[]`` entry is byte-identical to a row from
    :func:`entitlements.preview_at` (and therefore
    :func:`entitlements._preview_row`) for the same target -- pinned by
    the parity tests so the scalar / batch what-if accessors cannot
    drift. Supplied ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do not
    404 the call -- they are echoed in ``unknown[]`` so a partially-bad
    caller still gets rows back for the valid ids alongside a list of
    what was dropped.

    Response shape (mirrors ``/tier-spec-at-batch`` /
    ``/feature-spec-at-batch`` / ``/runtime-spec-at-batch`` plus a
    ``perspective_tier`` echo)::

        {
          "tiers":                 [<preview_at row>, ...],
          "unknown":               ["bogus_id", ...],
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` is missing / blank or ``targets=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``) with the
      perspective tier echoed so the UI keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        targets = _parse_csv_arg("targets")
        if not targets:
            return (
                jsonify({"error": "supply targets=<csv>"}),
                400,
            )
        batch = _ent.preview_at_batch(tier_in, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_preview_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
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


@bp_entitlement.route("/api/entitlement/next-tier-locks")
def api_entitlement_next_tier_locks():
    """``GET /api/entitlement/next-tier-locks`` -- marginal locks row for the
    rung immediately above the resolved entitlement, in
    :func:`clawmetry.entitlements.tier_locks` shape (``tier``,
    ``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes``).

    Symmetric companion to ``/api/entitlement/next-tier-unlocks``: that
    endpoint carries the rung-above's first-grant row, this carries its
    first-loss row -- a pricing-table cell can render both off ONE
    entitlement round-trip. ``locks`` is ``null`` at the ladder's
    ceiling (no rung above). Never 5xxs: a resolver failure
    short-circuits to the grace-shape envelope so the dashboard CTA
    keeps rendering instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.next_tier_locks()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "locks": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_locks: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "locks": None,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-locks")
def api_entitlement_previous_tier_locks():
    """``GET /api/entitlement/previous-tier-locks`` -- marginal locks row for
    the rung immediately below the resolved entitlement, in
    :func:`clawmetry.entitlements.tier_locks` shape.

    The step-down confirmation detail row paired with
    ``/api/entitlement/previous-tier-diff`` (which carries the same
    marginal in ``downgrade_diff`` shape). ``lost_features`` /
    ``lost_runtimes`` here are what the rung below first loses vs the
    rung above it -- and since "the rung above" the previous purchasable
    tier *is* the caller's current tier in the simple single-step
    downgrade case, these lists byte-equal the caller's marginal loss
    when stepping down by one rung. ``locks`` is ``null`` at the
    ladder's floor (no rung below). Never 5xxs.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.previous_tier_locks()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "locks": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_locks: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "locks": None,
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


@bp_entitlement.route("/api/entitlement/upgrade-path-at")
def api_entitlement_upgrade_path_at():
    """``GET /api/entitlement/upgrade-path-at?tier=<source>`` -- scalar
    what-if sibling of ``/api/entitlement/upgrade-path``: ordered
    marginal-unlock ladder from the caller-supplied ``tier`` upward.

    Source-anchored equivalent of ``/upgrade-path`` (which pins the
    walk's starting point to the resolver) -- the ``_at`` sibling in
    the ladder-walk family alongside ``/next-tier-spec-at``,
    ``/next-tier-unlocks-at``, ``/next-tier-locks-at``,
    ``/next-tier-diff-at`` and ``/next-tier-capacity-diff-at``.
    Lets a pricing-page "from tier X" wizard render the full upgrade
    ladder for any hypothetical source rung without first switching
    the resolver.

    Response shape mirrors ``/upgrade-path`` with the ``current_tier`` /
    ``current_tier_rank`` echo replaced by the caller-supplied ``tier``::

        {
          "tier":              "<source>",
          "tier_label":        "<display>",
          "tier_rank":         <int>,
          "path":              [<row>, ...],
          "current_tier":      "<resolved tier>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-unlocks`` exactly
    (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``, ...),
    byte-identical to the corresponding row in ``/upgrade-path`` when
    ``tier`` equals the resolved entitlement -- pinned by parity tests so
    the source-anchored and live variants cannot drift.

    Missing / empty ``tier`` -> 400. Unknown ``tier`` -> 404. Enterprise
    source -> 200 with ``path: []`` (already at the top). Never 5xxs: a
    resolver failure yields the grace-shape envelope so the wizard keeps
    rendering.
    """
    tier = (request.args.get("tier") or "").strip().lower()
    if not tier:
        return jsonify({"error": "tier query parameter is required"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        path = _ent.upgrade_path_at(tier) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier,
                "tier_label": _ent.tier_label(tier),
                "tier_rank": _ent.tier_rank(tier),
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_upgrade_path_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier,
                "tier_label": tier,
                "tier_rank": -1,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/downgrade-path-at")
def api_entitlement_downgrade_path_at():
    """``GET /api/entitlement/downgrade-path-at?tier=<source>`` -- scalar
    what-if sibling of ``/api/entitlement/downgrade-path``: ordered
    cumulative-loss ladder from the caller-supplied ``tier`` downward.

    Source-anchored mirror of ``/api/entitlement/upgrade-path-at`` and
    downgrade-side counterpart of the live ``/downgrade-path`` (source
    pinned to the resolver). Lets a "compare from tier X" downgrade-
    warning surface render every rung's loss list for any hypothetical
    source without first asking the resolver.

    Response shape mirrors ``/downgrade-path`` with the ``current_tier`` /
    ``current_tier_rank`` echo replaced by the caller-supplied ``tier``::

        {
          "tier":              "<source>",
          "tier_label":        "<display>",
          "tier_rank":         <int>,
          "path":              [<row>, ...],
          "current_tier":      "<resolved tier>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` carries the destination tier metadata + the walk's
    source echo (``current_tier`` / ``current_tier_label`` /
    ``current_tier_rank`` retain their :func:`downgrade_path` names for
    byte-shape parity, and carry the ``_at`` source in this variant) +
    ``lost_features`` / ``lost_runtimes`` cumulative over the gap (see
    :func:`clawmetry.entitlements.downgrade_path_at`).

    Missing / empty ``tier`` -> 400. Unknown ``tier`` -> 404. Floor
    source (oss / cloud_free) -> 200 with ``path: []`` (no rung strictly
    below). Never 5xxs: a resolver failure yields the grace-shape
    envelope so the surface keeps rendering.
    """
    tier = (request.args.get("tier") or "").strip().lower()
    if not tier:
        return jsonify({"error": "tier query parameter is required"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        path = _ent.downgrade_path_at(tier) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier,
                "tier_label": _ent.tier_label(tier),
                "tier_rank": _ent.tier_rank(tier),
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_downgrade_path_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier,
                "tier_label": tier,
                "tier_rank": -1,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/upgrade-path-at-batch")
def api_entitlement_upgrade_path_at_batch():
    """``GET /api/entitlement/upgrade-path-at-batch?tiers=a,b,c`` -- batch
    what-if sibling of ``/api/entitlement/upgrade-path-at``.

    Where ``/upgrade-path-at`` hydrates the marginal-unlock ladder above
    ONE hypothetical source tier, this hydrates it for N hypothetical
    sources in ONE round-trip. Pairs with ``/upgrade-path-at`` the same
    way ``/tier-catalog-at-batch`` pairs with ``/tier-catalog-at``:
    scalar what-if -> matrix what-if across the perspective-tier axis.

    Use case: a pricing-comparison matrix UI ("show me the upgrade
    ladder as if I were on OSS vs Cloud Starter vs Cloud Pro vs
    Enterprise -- side by side") hydrates every column off ONE call
    instead of N calls to ``/upgrade-path-at``.

    Each ``tiers[].path`` list is byte-identical to the body of
    ``/upgrade-path-at?tier=<tier>`` (its ``path`` field) for the same
    source tier -- pinned by parity tests so the scalar and batch
    what-if upgrade-path helpers cannot drift. Supplied tier ids are
    normalised (whitespace stripped, lowercased, duplicates dropped,
    first-seen order preserved). Unknown ids do not 404 the call --
    they are echoed in ``unknown[]`` so a partially-bad caller still
    gets rows back for the valid ids alongside a list of what was
    dropped, matching every other ``_at_batch`` sibling's posture.

    A source at the ceiling of the purchasable ladder (Enterprise)
    still yields a valid row with an empty ``path`` list -- the
    ceiling is NOT ``unknown``. Only ids not in :data:`_TIER_ORDER`
    (or where the scalar returns ``None``) land in ``unknown[]``.

    Response shape::

        {
          "tiers": [
            {
              "tier":       "<id>",
              "tier_label": "...",
              "tier_rank":  <int>,
              "path":       [<upgrade-path-at row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids -- does NOT
      404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.upgrade_path_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_upgrade_path_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/downgrade-path-at-batch")
def api_entitlement_downgrade_path_at_batch():
    """``GET /api/entitlement/downgrade-path-at-batch?tiers=a,b,c`` --
    batch what-if sibling of ``/api/entitlement/downgrade-path-at``.

    Direction-flipped twin of ``/api/entitlement/upgrade-path-at-batch``:
    where the upgrade batch hydrates the marginal-unlock ladder strictly
    above each source, this hydrates the cumulative-loss ladder strictly
    below each source. Same envelope, same per-source row shape, same
    unknown-bucketing posture -- only the inner ``path`` list changes
    direction.

    Use case: a "compare from tier X" downgrade-warning matrix UI ("show
    me the cumulative-loss ladder as if I were on OSS vs Cloud Starter
    vs Cloud Pro vs Enterprise -- side by side") hydrates every column
    off ONE call instead of N calls to ``/downgrade-path-at``.

    Each ``tiers[].path`` list is byte-identical to the body of
    ``/downgrade-path-at?tier=<tier>`` (its ``path`` field) for the same
    source tier -- pinned by parity tests so the scalar and batch
    what-if downgrade-path helpers cannot drift. Supplied tier ids are
    normalised (whitespace stripped, lowercased, duplicates dropped,
    first-seen order preserved). Unknown ids do not 404 the call --
    they are echoed in ``unknown[]``.

    A source at the floor of the purchasable ladder (``oss`` /
    ``cloud_free``) still yields a valid row with an empty ``path``
    list -- the floor is NOT ``unknown``. Only ids not in
    :data:`_TIER_ORDER` (or where the scalar returns ``None``) land in
    ``unknown[]``.

    Response shape::

        {
          "tiers": [
            {
              "tier":       "<id>",
              "tier_label": "...",
              "tier_rank":  <int>,
              "path":       [<downgrade-path-at row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids -- does NOT
      404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.downgrade_path_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_downgrade_path_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
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
                required = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                allowed = ent.allows_retention_window(retention_n)
            else:
                required = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                allowed = ent.allows_node_count(nodes_n)
            else:
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


@bp_entitlement.route("/api/entitlement/lock-reason-at")
def api_entitlement_lock_reason_at():
    """``GET /api/entitlement/lock-reason-at?tier=<perspective>&<axis>=<id>``
    -- what-if sibling of ``/api/entitlement/lock-reason``: the lock-row
    for one item computed as if the install were on ``perspective_tier``,
    NOT against the live resolved entitlement.

    Same row shape as ``/api/entitlement/lock-reason`` -- ``key``,
    ``kind``, ``reason``, ``locked``, ``allowed``, ``required_tier``,
    ``required_tier_label``, ``required_tier_rank``, ``current_tier``
    (the perspective), ``current_tier_rank``, ``upgrade_required``.
    Lets a pricing-comparison tooltip preview the exact lock sentence a
    downgrade-to-target would surface in one round-trip, before the
    user commits.

    Pairs with :func:`api_entitlement_feature_spec_at` /
    :func:`api_entitlement_runtime_spec_at`: those return the catalog
    row at a hypothetical tier; this returns the lock copy and
    ``upgrade_required`` cue the paywall renders against that tier.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied.

    - **400** when ``tier=`` is missing / blank, when no axis is
      supplied, or when more than one axis is supplied
    - **404** when ``tier`` is unknown (not in
      :data:`entitlements._TIER_ORDER`). The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: a synthesis failure short-circuits to the
      grace-shape row (``reason=null`` / ``locked=false`` /
      ``allowed=true``) so the UI keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
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
            bool(runtime_in),
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

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = _ent.lock_reason_at(tier_in, feature, kind=kind)
            allowed = reason is None
        elif runtime_in:
            rt = _ent.canonical_runtime(runtime_in)
            key, kind = rt or runtime_in, "runtime"
            required = _ent.min_tier_for_runtime(rt) if rt else None
            reason = _ent.lock_reason_at(tier_in, rt or runtime_in, kind=kind)
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = _ent.lock_reason_at(
                    tier_in, str(channels_n), kind=kind
                )
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = _ent.lock_reason_at(
                    tier_in, str(retention_n), kind=kind
                )
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = _ent.lock_reason_at(tier_in, str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(tier_in)
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
                "current_tier": tier_in,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason_at: error: %s", exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
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
                "current_tier": tier_in,
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


@bp_entitlement.route("/api/entitlement/feature-catalog-at")
def api_entitlement_feature_catalog_at():
    """``GET /api/entitlement/feature-catalog-at?tier=<id>`` -- what-if
    sibling of ``/api/features``: returns the same feature-catalog rows but
    with ``allowed`` / ``locked`` / ``entitled`` computed as if the install
    were on ``tier``.

    Lets a pricing-comparison UI render the same row shape as
    :func:`entitlements.feature_catalog` for any tier in
    :data:`entitlements._TIER_ORDER` without first switching the live
    resolver.

    - **400** when ``tier=`` is missing / blank
    - **404** when the id is not a known tier (catalogue-derived; the
      id is echoed in the body so the caller can render "unknown tier")
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      fallback inside the helper, so the endpoint still returns the
      catalogue rows.
    """
    raw = request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_catalog_at(tier)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        return jsonify({"tier": tier, "features": body})
    except Exception as exc:
        logger.warning("api_entitlement_feature_catalog_at: error: %s", exc)
        return jsonify({"error": "feature-catalog-at failed"}), 500


@bp_entitlement.route("/api/entitlement/runtime-catalog-at")
def api_entitlement_runtime_catalog_at():
    """``GET /api/entitlement/runtime-catalog-at?tier=<id>`` -- what-if
    sibling of ``/api/runtimes``: returns the same runtime-catalog rows
    but with ``allowed`` / ``locked`` / ``entitled`` computed as if the
    install were on ``tier``.

    - **400** when ``tier=`` is missing / blank
    - **404** when the id is not a known tier
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      fallback so the catalogue still renders.
    """
    raw = request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_catalog_at(tier)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        return jsonify({"tier": tier, "runtimes": body})
    except Exception as exc:
        logger.warning("api_entitlement_runtime_catalog_at: error: %s", exc)
        return jsonify({"error": "runtime-catalog-at failed"}), 500


@bp_entitlement.route("/api/entitlement/tier-catalog-at")
def api_entitlement_tier_catalog_at():
    """``GET /api/entitlement/tier-catalog-at?tier=<id>`` -- what-if
    sibling of the tier ladder: returns the full tier-catalog rows but
    with ``is_current`` recomputed as if the install were on ``tier``
    instead of the live resolved entitlement.

    Row shape and ordering match :func:`entitlements.tier_catalog`
    exactly; only the ``is_current`` boolean shifts. Lets a pricing-
    comparison UI render the upgrade ladder from the perspective of any
    hypothetical tier without first switching the live resolver.

    - **400** when ``tier=`` is missing / blank
    - **404** when the id is not a known tier (catalogue-derived; the
      id is echoed in the body so the caller can render "unknown tier")
    - **Never 5xxs**: a catalogue failure short-circuits to the OSS-floor
      fallback inside the helper, so the endpoint still returns rows.
    """
    raw = request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_catalog_at(tier)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        return jsonify({"tier": tier, "tiers": body})
    except Exception as exc:
        logger.warning("api_entitlement_tier_catalog_at: error: %s", exc)
        return jsonify({"error": "tier-catalog-at failed"}), 500


@bp_entitlement.route("/api/entitlement/tier-catalog-at-batch")
def api_entitlement_tier_catalog_at_batch():
    """``GET /api/entitlement/tier-catalog-at-batch?tiers=a,b,c`` -- batch
    what-if sibling of ``/api/entitlement/tier-catalog-at``.

    Where ``/tier-catalog-at`` hydrates the full tier ladder for ONE
    hypothetical source tier (with ``is_current`` flipped to that
    source), this hydrates it for N hypothetical sources in ONE
    round-trip. Pairs with ``/tier-catalog-at`` the same way
    ``/feature-catalog-at-batch`` pairs with ``/feature-catalog-at`` and
    ``/runtime-catalog-at-batch`` pairs with ``/runtime-catalog-at``:
    scalar what-if -> matrix what-if across the perspective-tier axis
    rather than the feature-id / runtime-id axis.

    Use case: a pricing-comparison matrix UI ("show me the tier ladder
    as if I were on OSS vs Cloud Starter vs Cloud Pro vs Enterprise --
    side by side") hydrates every column off ONE call instead of N
    calls to ``/tier-catalog-at``.

    Each ``tiers[].tiers`` list is byte-identical to the body of
    ``/tier-catalog-at?tier=<tier>`` for the same source tier -- pinned
    by parity tests so the scalar and batch what-if catalog helpers
    cannot drift. Supplied tier ids are normalised (whitespace
    stripped, lowercased, duplicates dropped, first-seen order
    preserved). Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets rows back for
    the valid ids alongside a list of what was dropped, matching every
    other ``_at_batch`` sibling's posture.

    Response shape::

        {
          "tiers": [
            {
              "tier":       "<id>",
              "tier_label": "...",
              "tier_rank":  <int>,
              "tiers":      [<tier-catalog-at row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids -- does NOT
      404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.tier_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_catalog_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-catalog-at-batch")
def api_entitlement_feature_catalog_at_batch():
    """``GET /api/entitlement/feature-catalog-at-batch?tiers=a,b,c`` --
    batch what-if sibling of ``/api/entitlement/feature-catalog-at``.

    Where ``/feature-catalog-at`` hydrates the full feature catalog for
    ONE hypothetical tier, this hydrates it for N hypothetical tiers in
    ONE round-trip. Pairs with ``/feature-catalog-at`` the same way
    ``/feature-spec-at-batch`` pairs with ``/feature-spec-at``: scalar
    what-if -> matrix what-if across the perspective-tier axis rather
    than the feature-id axis.

    Use case: a pricing-comparison matrix UI ("show me the full feature
    catalog at OSS vs Cloud Starter vs Cloud Pro vs Enterprise")
    hydrates every column off ONE call instead of N calls to
    ``/feature-catalog-at``.

    Each ``tiers[].features`` list is byte-identical to the body of
    ``/feature-catalog-at?tier=<tier>`` for the same tier -- pinned by
    the parity tests so the scalar and batch what-if catalog helpers
    cannot drift. Supplied tier ids are normalised (whitespace
    stripped, lowercased, duplicates dropped, first-seen order
    preserved). Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets rows back for
    the valid ids alongside a list of what was dropped, matching every
    other ``_at_batch`` sibling's posture.

    Response shape::

        {
          "tiers": [
            {
              "tier":       "<id>",
              "tier_label": "...",
              "tier_rank":  <int>,
              "features":   [<feature-catalog-at row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids -- does NOT
      404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.feature_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_catalog_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog-at-batch")
def api_entitlement_runtime_catalog_at_batch():
    """``GET /api/entitlement/runtime-catalog-at-batch?tiers=a,b,c`` --
    batch what-if sibling of ``/api/entitlement/runtime-catalog-at``.

    Runtime-axis twin of ``/feature-catalog-at-batch``: same shape, same
    normalisation semantics, same unknown-echo posture. Together the
    two batches let a pricing-comparison matrix UI hydrate every
    feature + runtime column at every hypothetical rung off TWO calls
    instead of 2 * N calls to the scalar what-if catalog endpoints.

    Each ``tiers[].runtimes`` list is byte-identical to the body of
    ``/runtime-catalog-at?tier=<tier>`` for the same tier -- pinned by
    the parity tests.

    Response shape mirrors ``/feature-catalog-at-batch`` with
    ``features`` renamed to ``runtimes``.

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_catalog_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-spec-at")
def api_entitlement_tier_spec_at():
    """``GET /api/entitlement/tier-spec-at?tier=<id>&target=<id>`` -- scalar
    what-if sibling of ``/api/entitlement/tier-catalog-at``: the single tier
    descriptor for ``target`` with ``is_current`` computed as if the install
    were on ``tier``.

    Lets a pricing-comparison tooltip hydrate against ONE tier descriptor from
    a hypothetical perspective in one round-trip instead of fetching the full
    ``/api/entitlement/tier-catalog-at`` payload and filtering client-side.
    The returned row matches exactly one row from
    :func:`entitlements.tier_catalog_at`.

    - **400** when either ``tier=`` or ``target=`` is missing / blank
    - **404** when ``tier`` or ``target`` is unknown (not in
      :data:`entitlements._TIER_ORDER`). The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: the helper internally falls back to the OSS-floor view
      on catalogue failure, so the endpoint still returns 200 with a valid
      row.
    """
    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    raw_target = request.args.get("target")
    target = (raw_target or "").strip().lower()
    if not target:
        return jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if target not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target,
                    }
                ),
                404,
            )
        body = _ent.tier_spec_at(tier, target)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "tier-spec-at failed",
                        "tier": tier,
                        "target": target,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier, "target": target, "spec": body})
    except Exception as exc:
        logger.warning("api_entitlement_tier_spec_at: error: %s", exc)
        return jsonify({"error": "tier-spec-at failed"}), 500


@bp_entitlement.route("/api/entitlement/feature-spec-at")
def api_entitlement_feature_spec_at():
    """``GET /api/entitlement/feature-spec-at?tier=<id>&feature=<id>`` --
    scalar what-if sibling of ``/api/entitlement/feature-catalog-at``:
    the single catalogue row for ``feature`` with ``allowed`` /
    ``locked`` / ``entitled`` computed as if the install were on
    ``tier``.

    Lets a pricing-comparison tooltip hydrate against ONE feature at a
    hypothetical tier in one round-trip instead of fetching the full
    ``/api/entitlement/feature-catalog-at`` payload and filtering
    client-side. The returned row matches exactly one row from
    :func:`entitlements.feature_catalog_at`.

    - **400** when either ``tier=`` or ``feature=`` is missing / blank
    - **404** when ``tier`` is unknown (not in
      :data:`entitlements._TIER_ORDER`) or ``feature`` is unknown (not
      in :data:`ALL_FEATURES`). The body carries ``which`` so a caller
      can render the right "unknown ..." message.
    - **Never 5xxs**: the helper internally falls back to the OSS-free
      shape on resolver failure, so the endpoint still returns 200 with
      a valid row.
    """
    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    raw_feature = request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        body = _ent.feature_spec_at(tier, feature)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "feature-spec-at failed",
                        "tier": tier,
                        "feature": feature,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier, "feature": feature, "spec": body})
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec_at: error: %s", exc)
        return jsonify({"error": "feature-spec-at failed"}), 500


@bp_entitlement.route("/api/entitlement/runtime-spec-at")
def api_entitlement_runtime_spec_at():
    """``GET /api/entitlement/runtime-spec-at?tier=<id>&runtime=<id>`` --
    scalar what-if sibling of ``/api/entitlement/runtime-catalog-at``:
    the single catalogue row for ``runtime`` with ``allowed`` /
    ``locked`` / ``entitled`` computed as if the install were on
    ``tier``.

    Lets a pricing-comparison tooltip hydrate against ONE runtime at a
    hypothetical tier in one round-trip instead of fetching the full
    ``/api/entitlement/runtime-catalog-at`` payload and filtering
    client-side. Accepts aliases (``claude-code`` -> ``claude_code``)
    via :func:`entitlements.canonical_runtime`. The returned row
    matches exactly one row from :func:`entitlements.runtime_catalog_at`.

    - **400** when either ``tier=`` or ``runtime=`` is missing / blank
    - **404** when ``tier`` is unknown (not in
      :data:`entitlements._TIER_ORDER`) or ``runtime`` (after alias
      canonicalisation) is unknown (not in :data:`ALL_RUNTIMES`).
    - **Never 5xxs**: the helper internally falls back to the OSS-free
      shape on resolver failure, so the endpoint still returns 200 with
      a valid row.
    """
    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    raw_runtime = request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": runtime_in,
                    }
                ),
                404,
            )
        body = _ent.runtime_spec_at(tier, rt)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "runtime-spec-at failed",
                        "tier": tier,
                        "runtime": rt,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier, "runtime": rt, "spec": body})
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec_at: error: %s", exc)
        return jsonify({"error": "runtime-spec-at failed"}), 500


@bp_entitlement.route("/api/entitlement/feature-spec")
def api_entitlement_feature_spec():
    """``GET /api/entitlement/feature-spec?feature=<id>`` -- scalar sibling of
    ``/api/features``: the full catalogue row for one feature id in one shot,
    matching exactly one row from :func:`entitlements.feature_catalog`.

    Lets a feature-detail page / locked-row tooltip hydrate against a single
    feature without fetching the whole catalogue and filtering client-side.

    - **400** when ``feature=`` is missing / blank
    - **404** when the id is not in :data:`ALL_FEATURES`
    - **Never 5xxs**: the helper internally falls back to the OSS-free shape on
      resolver failure, so the endpoint still returns 200 with a valid row.
    """
    raw = request.args.get("feature")
    feature = (raw or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_spec(feature)
        if body is None:
            return (
                jsonify({"error": "unknown feature", "feature": feature}),
                404,
            )
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec: error: %s", exc)
        return jsonify({"error": "feature-spec failed"}), 500


@bp_entitlement.route("/api/entitlement/runtime-spec")
def api_entitlement_runtime_spec():
    """``GET /api/entitlement/runtime-spec?runtime=<id>`` -- scalar sibling of
    ``/api/runtimes``: the full catalogue row for one runtime id in one shot,
    matching exactly one row from :func:`entitlements.runtime_catalog`.

    Lets a runtime-detail page / locked-row tooltip hydrate against a single
    runtime without fetching the whole catalogue and filtering client-side.
    Accepts aliases (``claude-code`` -> ``claude_code``) via
    :func:`entitlements.canonical_runtime` so the URL surface matches what
    callers already pass to ``/api/entitlement/required-tier``.

    - **400** when ``runtime=`` is missing / blank
    - **404** when the id (after alias canonicalisation) is not in
      :data:`ALL_RUNTIMES`
    - **Never 5xxs**: the helper internally falls back to the OSS-free shape on
      resolver failure, so the endpoint still returns 200 with a valid row.
    """
    raw = request.args.get("runtime")
    runtime = (raw or "").strip().lower()
    if not runtime:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_spec(runtime)
        if body is None:
            return (
                jsonify({"error": "unknown runtime", "runtime": runtime}),
                404,
            )
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec: error: %s", exc)
        return jsonify({"error": "runtime-spec failed"}), 500


@bp_entitlement.route("/api/entitlement/channel-spec")
def api_entitlement_channel_spec():
    """``GET /api/entitlement/channel-spec?channel=<id>`` -- scalar sibling
    of ``/api/entitlement/channel-catalog``: the full catalogue row for one
    chat-channel adapter id in one shot, matching exactly one row from
    :func:`entitlements.channel_catalog`.

    Channel-axis analogue of ``/feature-spec`` / ``/runtime-spec`` -- lets
    a channel-detail page or a "which channels does this account have on"
    tooltip hydrate against one channel without fetching the whole
    catalogue and filtering client-side. Because every chat channel is
    FREE at every tier (the ``channels`` capacity axis governs how many
    concurrent channels each plan admits, not which adapters unlock), the
    returned row is always ``free=True`` / ``allowed=True`` /
    ``locked=False`` / ``entitled=True`` regardless of the resolved tier.

    - **400** when ``channel=`` is missing / blank
    - **404** when the id (after whitespace + case normalisation) is not
      in :data:`entitlements.ALL_CHANNELS`
    - **Never 5xxs**: the helper internally falls back to the OSS-free
      shape on resolver failure, so the endpoint still returns 200 with a
      valid row.
    """
    raw = request.args.get("channel")
    channel = (raw or "").strip().lower()
    if not channel:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.channel_spec(channel)
        if body is None:
            return (
                jsonify({"error": "unknown channel", "channel": channel}),
                404,
            )
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_channel_spec: error: %s", exc)
        return jsonify({"error": "channel-spec failed"}), 500


@bp_entitlement.route("/api/entitlement/channel-spec-batch")
def api_entitlement_channel_spec_batch():
    """``GET /api/entitlement/channel-spec-batch?channels=a,b,c`` -- plural
    sibling of ``/api/entitlement/channel-spec``.

    Returns the full catalogue spec row for every supplied chat-channel id
    in one round-trip. Mirrors :func:`api_entitlement_feature_spec_batch` /
    :func:`api_entitlement_runtime_spec_batch` for the chat-channel axis;
    together they let a Settings or paywall matrix UI hydrate the per-row
    state ("lock badge + required tier + entitled flag") for a viewport's
    worth of features + runtimes + channels off THREE calls instead of N +
    M + K.

    Each ``channels[]`` entry is byte-identical to a row from
    :func:`entitlements.channel_catalog` -- a parity test pins this so the
    scalar / bulk / batch accessors cannot drift. Supplied ids are
    normalised (whitespace stripped, lowercased, duplicates dropped while
    preserving first-seen order). Unknown ids do not 404 the call -- they
    are echoed in ``unknown[]`` so a partially-bad caller still gets rows
    back for the valid ids alongside a list of what was dropped.

    Because every chat channel is FREE at every tier (the ``channels``
    capacity axis governs how many concurrent channels each plan admits,
    not which adapters unlock), every returned row is ``free=True`` /
    ``allowed=True`` / ``locked=False`` / ``entitled=True`` regardless of
    the resolved tier.

    Response shape::

        {
          "channels":          [<spec_row>, ...],
          "unknown":           ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``channels=`` is missing or empty after normalisation
    - **Never 5xxs**: a resolver crash short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``).
    """
    try:
        channels = _parse_csv_arg("channels")
        if not channels:
            return (
                jsonify({"error": "supply channels=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.channel_spec_batch(channels)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_channel_spec_batch: error: %s", exc)
        return jsonify(
            {
                "channels": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-spec-at")
def api_entitlement_channel_spec_at():
    """``GET /api/entitlement/channel-spec-at?tier=<id>&channel=<id>`` --
    scalar what-if sibling of ``/api/entitlement/channel-catalog-at``:
    the single catalogue row for ``channel`` with ``allowed`` /
    ``locked`` / ``entitled`` computed as if the install were on
    ``tier``.

    Channel-axis analogue of ``/feature-spec-at`` / ``/runtime-spec-at``
    -- lets a pricing-comparison tooltip hydrate against ONE channel at
    a hypothetical tier in one round-trip instead of fetching the full
    ``/api/entitlement/channel-catalog-at`` payload and filtering
    client-side. The returned row matches exactly one row from
    :func:`entitlements.channel_catalog_at`.

    Because every chat channel is FREE at every tier (the ``channels``
    capacity axis governs how many concurrent channels each plan admits,
    not which adapters unlock), the returned row is always
    ``free=True`` / ``allowed=True`` / ``locked=False`` /
    ``entitled=True`` regardless of the perspective tier.

    - **400** when either ``tier=`` or ``channel=`` is missing / blank
    - **404** when ``tier`` is unknown (not in
      :data:`entitlements._TIER_ORDER`) or ``channel`` (after whitespace
      + case normalisation) is unknown (not in
      :data:`entitlements.ALL_CHANNELS`). The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: the helper internally falls back to the OSS-free
      shape on resolver failure, so the endpoint still returns 200 with
      a valid row.
    """
    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    raw_channel = request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": channel,
                    }
                ),
                404,
            )
        body = _ent.channel_spec_at(tier, channel)
        if body is None:
            return (
                jsonify(
                    {
                        "error": "channel-spec-at failed",
                        "tier": tier,
                        "channel": channel,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier, "channel": channel, "spec": body})
    except Exception as exc:
        logger.warning("api_entitlement_channel_spec_at: error: %s", exc)
        return jsonify({"error": "channel-spec-at failed"}), 500


@bp_entitlement.route("/api/entitlement/channel-spec-at-batch")
def api_entitlement_channel_spec_at_batch():
    """``GET /api/entitlement/channel-spec-at-batch?tier=<perspective>
    &channels=a,b,c`` -- what-if + batch sibling of
    ``/api/entitlement/channel-spec-batch``.

    Where ``/channel-spec-batch`` returns batch rows against the LIVE
    resolved entitlement, this returns them against a HYPOTHETICAL
    ``perspective_tier``. Pairs with ``/channel-spec-at`` the same way
    ``/channel-spec-batch`` pairs with ``/channel-spec``: scalar -> matrix
    in one round-trip. Channel-axis twin of ``/feature-spec-at-batch`` /
    ``/runtime-spec-at-batch`` -- together they let a pricing-comparison
    matrix UI hydrate a viewport's worth of feature + runtime + channel
    rows at a hypothetical tier off THREE calls instead of N + M + K.

    Each ``channels[]`` entry is byte-identical to a row from
    :func:`entitlements.channel_catalog_at` at the same perspective tier
    -- pinned by the parity tests so the scalar / bulk / batch what-if
    accessors cannot drift. And because every chat channel is FREE at
    every tier (the ``channels`` capacity axis governs how many
    concurrent channels each plan admits, not which adapters unlock),
    each row is ALSO byte-identical to the LIVE ``/channel-spec`` row
    for the same id regardless of the perspective tier.

    Supplied ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do not
    404 the call -- they are echoed in ``unknown[]`` so a partially-bad
    caller still gets rows back for the valid ids alongside a list of
    what was dropped.

    Response shape (mirrors ``/channel-spec-batch`` plus a
    ``perspective_tier`` echo for caller round-trip safety)::

        {
          "channels":              [<spec_row>, ...],
          "unknown":               ["bogus_id", ...],
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` is missing / blank or ``channels=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``) with the
      perspective tier echoed so the UI keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        channels = _parse_csv_arg("channels")
        if not channels:
            return (
                jsonify({"error": "supply channels=<csv>"}),
                400,
            )
        batch = _ent.channel_spec_at_batch(tier_in, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "channels": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-spec-batch")
def api_entitlement_feature_spec_batch():
    """``GET /api/entitlement/feature-spec-batch?features=a,b,c`` -- plural
    sibling of ``/api/entitlement/feature-spec``.

    Returns the full catalogue spec row for every supplied feature id in
    one round-trip. Mirrors the
    ``scalar -> /feature-spec`` / ``batch -> /feature-spec-batch`` pair
    that ``/lock-reason`` <-> ``/lock-reason-batch`` already establishes,
    so a paywall matrix UI hydrates the N visible rows off one call
    instead of N calls to ``/feature-spec``.

    Each ``features[]`` entry is byte-identical to a row from
    :func:`entitlements.feature_catalog` -- a parity test pins this so
    the scalar / bulk / batch accessors cannot drift. Supplied ids are
    normalised (whitespace stripped, lowercased, duplicates dropped while
    preserving first-seen order). Unknown ids do not 404 the call --
    they are echoed in ``unknown[]`` so a partially-bad caller still
    gets rows back for the valid ids alongside a list of what was
    dropped.

    Response shape::

        {
          "features":          [<spec_row>, ...],
          "unknown":           ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``features=`` is missing or empty after normalisation
    - **Never 5xxs**: a resolver crash short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``).
    """
    try:
        features = _parse_csv_arg("features")
        if not features:
            return (
                jsonify({"error": "supply features=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.feature_spec_batch(features)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec_batch: error: %s", exc)
        return jsonify(
            {
                "features": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-batch")
def api_entitlement_runtime_spec_batch():
    """``GET /api/entitlement/runtime-spec-batch?runtimes=a,b,c`` -- plural
    sibling of ``/api/entitlement/runtime-spec``.

    Returns the full catalogue spec row for every supplied runtime id in
    one round-trip. Mirrors :func:`api_entitlement_feature_spec_batch` for
    the runtime axis; together they let a Settings or paywall matrix UI
    hydrate the per-row state ("lock badge + required tier + entitled
    flag") for a viewport's worth of features + runtimes off TWO calls
    instead of N + M.

    Each ``runtimes[]`` entry is byte-identical to a row from
    :func:`entitlements.runtime_catalog`. Aliases are canonicalised the
    same way ``/api/entitlement/runtime-spec`` already does
    (``claude-code`` -> ``claude_code``), and aliases that collapse to a
    canonical id already in the response are silently de-duplicated so
    the row count matches the unique-canonical-id count.

    Response shape::

        {
          "runtimes":          [<spec_row>, ...],
          "unknown":           ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``runtimes=`` is missing or empty after normalisation
    - **Never 5xxs**: a resolver crash short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``).
    """
    try:
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return (
                jsonify({"error": "supply runtimes=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_spec_batch(runtimes)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec_batch: error: %s", exc)
        return jsonify(
            {
                "runtimes": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-spec-at-batch")
def api_entitlement_tier_spec_at_batch():
    """``GET /api/entitlement/tier-spec-at-batch?tier=<perspective>
    &targets=a,b,c`` -- what-if + batch sibling of
    ``/api/entitlement/tier-spec-at``.

    Where ``/tier-spec-at`` hydrates ONE tier descriptor from a
    hypothetical perspective, this hydrates N descriptor rows for a
    caller-supplied subset of target tiers off a single round-trip.
    Fixed-source multi-target companion of ``/tier-spec-at`` and
    tier-axis sibling of ``/feature-spec-at-batch`` /
    ``/runtime-spec-at-batch`` (which fix the source and batch across
    the feature / runtime axis instead).

    Use case: a pricing-comparison matrix UI ("from my perspective tier,
    render the descriptor rows for OSS, Cloud Starter, Cloud Pro and
    Enterprise") hydrates every column off ONE call instead of N calls
    to ``/tier-spec-at``.

    Each ``tiers[]`` entry is byte-identical to a row from
    :func:`entitlements.tier_spec_at` for the same ``target`` -- pinned
    by the parity tests so the scalar / batch what-if accessors cannot
    drift. Supplied ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do not
    404 the call -- they are echoed in ``unknown[]`` so a partially-bad
    caller still gets rows back for the valid ids alongside a list of
    what was dropped.

    Response shape (mirrors ``/feature-spec-at-batch`` /
    ``/runtime-spec-at-batch`` plus a ``perspective_tier`` echo)::

        {
          "tiers":                 [<tier_spec_at row>, ...],
          "unknown":               ["bogus_id", ...],
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` is missing / blank or ``targets=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``) with the
      perspective tier echoed so the UI keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        targets = _parse_csv_arg("targets")
        if not targets:
            return (
                jsonify({"error": "supply targets=<csv>"}),
                400,
            )
        batch = _ent.tier_spec_at_batch(tier_in, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-spec-at-batch")
def api_entitlement_feature_spec_at_batch():
    """``GET /api/entitlement/feature-spec-at-batch?tier=<perspective>
    &features=a,b,c`` -- what-if + batch sibling of
    ``/api/entitlement/feature-spec-batch``.

    Where ``/feature-spec-batch`` returns batch rows against the LIVE
    resolved entitlement, this returns them against a HYPOTHETICAL
    ``perspective_tier``. Pairs with ``/feature-spec-at`` the same way
    ``/feature-spec-batch`` pairs with ``/feature-spec``: scalar -> matrix
    in one round-trip.

    Use case: a pricing-comparison matrix UI ("here are the 6 features I
    want to render at Cloud Pro") hydrates the visible rows off ONE call
    instead of N calls to ``/feature-spec-at``.

    Each ``features[]`` entry is byte-identical to a row from
    :func:`entitlements.feature_catalog_at` -- pinned by the parity
    tests so the scalar / bulk / batch what-if accessors cannot drift.
    Supplied ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do not
    404 the call -- they are echoed in ``unknown[]`` so a partially-bad
    caller still gets rows back for the valid ids alongside a list of
    what was dropped.

    Response shape (mirrors ``/feature-spec-batch`` plus a
    ``perspective_tier`` echo for caller round-trip safety)::

        {
          "features":              [<spec_row>, ...],
          "unknown":               ["bogus_id", ...],
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` is missing / blank or ``features=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``) with the
      perspective tier echoed so the UI keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        features = _parse_csv_arg("features")
        if not features:
            return (
                jsonify({"error": "supply features=<csv>"}),
                400,
            )
        batch = _ent.feature_spec_at_batch(tier_in, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "features": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-at-batch")
def api_entitlement_runtime_spec_at_batch():
    """``GET /api/entitlement/runtime-spec-at-batch?tier=<perspective>
    &runtimes=a,b,c`` -- what-if + batch sibling of
    ``/api/entitlement/runtime-spec-batch``.

    Mirrors :func:`api_entitlement_feature_spec_at_batch` for the
    runtime axis; together they let a pricing-comparison matrix UI
    hydrate per-row state for a viewport's worth of features + runtimes
    at a hypothetical tier off TWO calls instead of N + M calls to
    ``/feature-spec-at`` + ``/runtime-spec-at``.

    Each ``runtimes[]`` entry is byte-identical to a row from
    :func:`entitlements.runtime_catalog_at`. Aliases are canonicalised
    the same way ``/runtime-spec`` already does (``claude-code`` ->
    ``claude_code``), and aliases that collapse to a canonical id
    already in the response are silently de-duplicated so the row count
    matches the unique-canonical-id count.

    Response shape (mirrors ``/runtime-spec-batch`` plus a
    ``perspective_tier`` echo)::

        {
          "runtimes":              [<spec_row>, ...],
          "unknown":               ["bogus_id", ...],
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` is missing / blank or ``runtimes=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``) with the
      perspective tier echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return (
                jsonify({"error": "supply runtimes=<csv>"}),
                400,
            )
        batch = _ent.runtime_spec_at_batch(tier_in, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "runtimes": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-at")
def api_entitlement_tier_unlocks_at():
    """``GET /api/entitlement/tier-unlocks-at?tier=<source>&target=<dest>`` --
    scalar what-if sibling of ``/api/entitlement/tier-unlocks``: marginal
    unlocks for ``target`` (features + runtimes that first become available
    at the destination) computed against the caller-supplied ``tier``
    rather than the global next-lower-purchasable-tier anchor
    ``/tier-unlocks`` uses.

    Lets a pricing-comparison tooltip render "what's new in B vs A" for
    any ``(A, B)`` pair in one round-trip without fetching the full
    ``/tier-unlocks-path?from=A&to=B`` payload and reading the destination
    row client-side. The returned row matches the destination row of
    :func:`entitlements.tier_unlocks_path` for the same pair -- a parity
    test pins this so the scalar what-if and the path-walker cannot drift.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` on either
    argument (including ``trial``), matching the other ``_at`` family
    endpoints. Direction is not normalised: a downgrade or identity pair
    returns empty ``features`` / ``runtimes`` lists; use
    ``/tier-locks-at`` for the marginal-loss view of a downgrade.

    Response shape::

        {
          "tier":   "<source tier id>",
          "target": "<destination tier id>",
          "row":    {<tier_unlocks row>},
        }

    The inner ``row`` matches the singular ``/tier-unlocks`` row shape
    exactly (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``) -- with ``previous_tier`` carrying the caller-supplied
    ``tier`` arg, NOT the global next-lower-purchasable anchor.

    - **400** when either ``tier=`` or ``target=`` is missing / blank
    - **404** when ``tier`` or ``target`` is unknown. The body carries
      ``which`` so a caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure falls through to a 404 so the
      tooltip surface stays mute instead of breaking.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_target = request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target_in,
                    }
                ),
                404,
            )
        row = _ent.tier_unlocks_at(tier_in, target_in)
        if row is None:
            return (
                jsonify(
                    {
                        "error": "tier-unlocks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks_at: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "tier-unlocks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-locks-at")
def api_entitlement_tier_locks_at():
    """``GET /api/entitlement/tier-locks-at?tier=<source>&target=<dest>`` --
    scalar what-if sibling of ``/api/entitlement/tier-locks``: marginal
    losses for ``target`` (features + runtimes that disappear at the
    destination) computed against the caller-supplied ``tier`` rather than
    the global next-higher-purchasable-tier anchor ``/tier-locks`` uses.

    Marginal-loss mirror of ``/tier-unlocks-at``. Lets a downgrade-warning
    tooltip render "what you'd give up dropping from A to B" for any
    ``(A, B)`` pair in one round-trip without fetching the full
    ``/tier-locks-path?from=A&to=B`` payload and reading the destination
    row client-side. The returned row matches the destination row of
    :func:`entitlements.tier_locks_path` for the same pair -- a parity
    test pins this so the scalar what-if and the path-walker cannot drift.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` on either
    argument (including ``trial``), matching the other ``_at`` family
    endpoints. Direction is not normalised: an upgrade or identity pair
    returns empty ``lost_features`` / ``lost_runtimes`` lists; use
    ``/tier-unlocks-at`` for the marginal-grant view of an upgrade.

    Response shape::

        {
          "tier":   "<source tier id>",
          "target": "<destination tier id>",
          "row":    {<tier_locks row>},
        }

    The inner ``row`` matches the singular ``/tier-locks`` row shape
    exactly (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``) -- with ``next_tier`` carrying the caller-supplied
    ``tier`` arg (the rung you're stepping FROM), NOT the global
    next-higher-purchasable anchor.

    - **400** when either ``tier=`` or ``target=`` is missing / blank
    - **404** when ``tier`` or ``target`` is unknown. The body carries
      ``which`` so a caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure falls through to a 404 so the
      tooltip surface stays mute instead of breaking.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_target = request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target_in,
                    }
                ),
                404,
            )
        row = _ent.tier_locks_at(tier_in, target_in)
        if row is None:
            return (
                jsonify(
                    {
                        "error": "tier-locks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        logger.warning("api_entitlement_tier_locks_at: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "tier-locks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-at-batch")
def api_entitlement_tier_unlocks_at_batch():
    """``GET /api/entitlement/tier-unlocks-at-batch?tier=<source>`` --
    what-if + batch sibling of ``/api/entitlement/tier-unlocks-batch``:
    marginal-unlocks rows for every purchasable tier as a target,
    computed against the caller-supplied ``tier`` rather than the
    global next-lower-purchasable-tier anchor ``/tier-unlocks-batch``
    uses.

    Composes the scalar what-if (``/tier-unlocks-at``) and the live
    batch (``/tier-unlocks-batch``) -- same row shape and ordering as
    the live batch, same hypothetical perspective as the ``_at``
    endpoint. Lets a pricing-comparison matrix UI render the "marginal
    unlocks vs <hypothetical-tier>" column for every rung off **one**
    round-trip instead of N calls to ``/tier-unlocks-at``.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` on the
    ``tier`` arg (including ``trial``), matching the other ``_at``
    family endpoints. The target list mirrors ``/tier-unlocks-batch``
    (purchasable tiers only -- trial excluded), so the rows match the
    live batch's target axis byte-for-byte and the response can be
    folded into the same pricing-page table.

    Response shape::

        {
          "tier":              "<source tier id>",
          "tiers":             [<row>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-unlocks-at`` for the
    same ``(tier, target)`` pair exactly (``tier``, ``tier_label``,
    ``tier_rank``, ``previous_tier``, ``previous_tier_label``,
    ``previous_tier_rank``, ``features``, ``runtimes``) -- with
    ``previous_tier`` carrying the caller-supplied ``tier`` arg, NOT
    the global next-lower-purchasable anchor.

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_unlocks_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_unlocks_at_batch: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-locks-at-batch")
def api_entitlement_tier_locks_at_batch():
    """``GET /api/entitlement/tier-locks-at-batch?tier=<source>`` --
    what-if + batch sibling of ``/api/entitlement/tier-locks-batch``:
    marginal-loss rows for every purchasable tier as a target, computed
    against the caller-supplied ``tier`` rather than the global next-
    higher-purchasable-tier anchor ``/tier-locks-batch`` uses.

    Marginal-loss mirror of ``/tier-unlocks-at-batch`` and pairs with
    ``/tier-locks-batch`` the same way ``/tier-unlocks-at-batch`` pairs
    with ``/tier-unlocks-batch``. Pair the two ``_at_batch`` endpoints
    to render the upgrade-CTA + downgrade-warning columns of a
    "compared against any hypothetical perspective" pricing matrix in
    two round-trips.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` on the
    ``tier`` arg (including ``trial``). The target list mirrors
    ``/tier-locks-batch`` (purchasable tiers only -- trial excluded).

    Response shape::

        {
          "tier":              "<source tier id>",
          "tiers":             [<row>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/tier-locks-at`` for the
    same ``(tier, target)`` pair exactly (``tier``, ``tier_label``,
    ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes``) -- with
    ``next_tier`` carrying the caller-supplied ``tier`` arg (the rung
    you'd be stepping FROM).

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``.
    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_locks_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_locks_at_batch: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
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


@bp_entitlement.route("/api/entitlement/required-tier-at")
def api_entitlement_required_tier_at():
    """``GET /api/entitlement/required-tier-at?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    hypothetical-perspective sibling of ``/api/entitlement/required-tier-batch``.

    Wraps :func:`entitlements.min_tier_for_all_at` so a pricing-comparison
    tooltip can render "if I were on Starter, this bundle would need Pro"
    off ONE round-trip without first switching the resolver. Fills the
    ``_at`` slot for the aggregate constraint-bundle family alongside the
    per-axis ``_at`` scalars (``/capacity-diff-at``, ``/tier-unlocks-at``,
    ``/tier-locks-at``) so a caller can call ``X_at`` uniformly across the
    whole ``_at`` scalar family.

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape the result -- the floor is
    anchored to the constraint bundle, matching every other ``_at``
    helper. A parity contract pinned in the test suite guarantees that
    per-row output byte-equals ``/api/entitlement/required-tier-batch`` for
    the same bundle regardless of perspective; the response layers
    ``perspective_tier`` / ``perspective_tier_rank`` /
    ``upgrade_required_from_perspective`` on top so a caller can render
    "from <perspective> this needs Pro" copy off one call.

    Args are byte-identical to ``/required-tier-batch`` except for the
    additional ``tier=`` perspective arg: at least one of ``features=`` /
    ``runtimes=`` / ``channels=`` / ``retention_days=`` / ``nodes=`` must
    be supplied (non-empty / parseable after normalisation). Same CSV
    normalisation, same capacity-axis parsing, same ``None`` = "not
    supplied" sentinel (so ``retention_days=`` blank is "unset", NOT
    the "unlimited" sentinel that would mis-route to Enterprise).

    - **400** when ``tier=`` is missing / blank, OR when no constraint
      axis is supplied.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields the OSS-free shape so the
      pricing tooltip keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

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

        required = _ent.min_tier_for_all_at(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        ent = _ent.get_entitlement()
        cur_rank = _ent.tier_rank(ent.tier)
        persp_rank = _ent.tier_rank(tier_in)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None

        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": persp_rank,
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
                "upgrade_required_from_perspective": (
                    bool(required) and req_rank > persp_rank
                ),
                "upgrade_required_from_current": (
                    bool(required) and req_rank > cur_rank
                ),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_required_tier_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
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
                "upgrade_required_from_perspective": False,
                "upgrade_required_from_current": False,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/affordable-tiers-at")
def api_entitlement_affordable_tiers_at():
    """``GET /api/entitlement/affordable-tiers-at?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    hypothetical-perspective sibling of ``/api/entitlement/affordable-tiers``.

    Wraps :func:`entitlements.affordable_tiers_at` so a pricing-page
    walkthrough can render "if I were on Starter, this bundle would
    qualify for Pro and Enterprise" off ONE round-trip without first
    switching the resolver. Plural what-if companion of
    ``/required-tier-at`` (which returns only the floor).

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the qualifying-tier
    list is anchored to the constraint bundle. A parity contract pinned
    in the test suite guarantees per-row output byte-equals
    ``/api/entitlement/affordable-tiers`` for the same bundle regardless
    of perspective; the response layers ``perspective_tier`` /
    ``is_at_or_better_than_perspective`` on top so a walkthrough surface
    can render "from <perspective> these tiers qualify" copy off one
    call, alongside the existing ``is_current`` /
    ``is_current_or_better`` current-resolver flags.

    Args are byte-identical to ``/affordable-tiers`` except for the
    additional ``tier=`` perspective arg. Same CSV normalisation, same
    capacity-axis parsing, same ``None`` = "not supplied" sentinel.

    - **400** when ``tier=`` is missing / blank, OR when no constraint
      axis is supplied.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields the OSS-free shape
      (empty tier list) so the pricing walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

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
        rows = _ent.affordable_tiers_at(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        ) or []

        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        persp_rank = _ent.tier_rank(tier_in)
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
                    "is_perspective": row["tier"] == tier_in,
                    "is_at_or_better_than_perspective": (
                        row["tier_rank"] >= persp_rank
                    ),
                }
            )

        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": persp_rank,
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
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_affordable_tiers_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
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
                "grace": True,
                "enforced": False,
            }
        )



@bp_entitlement.route("/api/entitlement/min-tier")
def api_entitlement_min_tier():
    """``GET /api/entitlement/min-tier?<axis>=<value>`` -- cheapest purchasable
    tier that admits the supplied constraint on ONE of the five capacity axes
    (``feature``, ``runtime``, ``channels``, ``retention_days``, ``nodes``).

    Singular sibling of :func:`api_entitlement_min_tier_batch`, closing the
    axis-symmetry gap: previously the singular endpoint accepted only
    ``feature=`` / ``runtime=``, while the batch already accepted all five.
    Same reverse-lookup contract as ``/required-tier`` (``feature``,
    ``runtime``, ``channels``, ``retention_days``, ``nodes``), rendered as
    the cheapest qualifying tier instead of the current-vs-required
    upgrade view -- so a pricing-page cell rendering "N nodes -- Available
    in Starter" can hit the same endpoint the feature / runtime lock
    affordances already use, and per-row parity with the plural
    ``/min-tier-batch`` shape is pinned in the test suite.

    Catalogue-derived, so the answer is identical in grace and enforce mode.
    Response shape::

        {
          "key":        "feature" | "runtime" | "channels"
                        | "retention_days" | "nodes",
          "value":      "<input>",
          "free":       <bool>,           # true when min_tier == OSS
          "min_tier":   "<tier id>" | null,
          "tier_label": "<Display Label>" | null,
          "tier_rank":  <int> | null,
        }

    400 when zero or more than one axis is supplied, or when a capacity
    axis value is non-int. 404 when the ``feature`` / ``runtime`` id is
    unknown -- the caller can show a neutral "not available" hint rather
    than pointing at a nonsense tier. Never 5xxs. The three capacity
    axes never 404: any parseable int (including zero / negative --
    which collapses to :data:`TIER_OSS` matching the helpers' contract)
    resolves to a real tier, so the ``error`` key never appears on a
    capacity response.
    """
    feature = (request.args.get("feature") or "").strip()
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
                    ),
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
                    ),
                }
            ),
            400,
        )
    if channels_present and not channels_ok:
        return (
            jsonify({"error": "channels= must be an integer"}),
            400,
        )
    if retention_present and not retention_ok:
        return (
            jsonify({"error": "retention_days= must be an integer"}),
            400,
        )
    if nodes_present and not nodes_ok:
        return (
            jsonify({"error": "nodes= must be an integer"}),
            400,
        )
    try:
        from clawmetry import entitlements as _ent

        if feature:
            min_t = _ent.min_tier_for_feature(feature)
            key, value = "feature", feature
            known = feature in _ent.ALL_FEATURES
        elif runtime:
            min_t = _ent.min_tier_for_runtime(runtime)
            key, value = "runtime", runtime
            known = runtime in _ent.ALL_RUNTIMES
        elif channels_present:
            min_t = _ent.min_tier_for_channel_count(channels_n)
            key, value = "channels", str(channels_n)
            known = True
        elif retention_present:
            min_t = _ent.min_tier_for_retention_window(retention_n)
            key, value = "retention_days", str(retention_n)
            known = True
        else:
            min_t = _ent.min_tier_for_node_count(nodes_n)
            key, value = "nodes", str(nodes_n)
            known = True
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
        if feature:
            key, value = "feature", feature
        elif runtime:
            key, value = "runtime", runtime
        elif channels_present:
            key, value = "channels", channels_raw
        elif retention_present:
            key, value = "retention_days", retention_raw
        else:
            key, value = "nodes", nodes_raw
        return jsonify(
            {
                "key": key,
                "value": value,
                "free": False,
                "min_tier": None,
                "tier_label": None,
                "tier_rank": None,
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier-batch")
def api_entitlement_min_tier_batch():
    """``GET /api/entitlement/min-tier-batch?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-item plural sibling of
    ``/api/entitlement/min-tier``.

    Where ``/required-tier-batch`` aggregates the most-constraining axis
    into one tier answer, this preserves the per-item detail so a
    pricing-matrix UI ("show me each requested feature + runtime +
    capacity row with its individual cheapest tier") renders off ONE
    round-trip instead of N calls to ``/min-tier``. Wraps
    :func:`clawmetry.entitlements.min_tier_batch` and appends the same
    ``current_tier`` / ``grace`` / ``enforced`` envelope
    ``/lock-reason-batch`` returns so a caller sees the same resolver
    context alongside the per-item answers.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty /
    parseable after normalisation). ``features=`` / ``runtimes=`` take
    comma-separated tokens (whitespace and duplicates are normalised
    away; runtime aliases like ``claude-code`` canonicalise to
    ``claude_code``; unknown ids contribute an all-``None`` row --
    they do not error). The three capacity axes take a single int
    each; a blank or non-int value is treated as "not supplied"
    (matches the singular endpoint's never-crash posture rather than
    mis-routing a typo to Enterprise). Never 5xxs: the grace-shape
    envelope is returned on any resolver failure.

    Response shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``free``, ``min_tier``,
    ``min_tier_label`` and ``min_tier_rank`` (``-1`` when
    ``min_tier`` is ``None``). Per-row parity with the singular
    ``/min-tier?feature=`` / ``?runtime=`` endpoint is pinned in the
    test suite so the batch cannot silently drift from the scalar.
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

        batch = _ent.min_tier_batch(
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
        logger.warning("api_entitlement_min_tier_batch: error: %s", exc)
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


@bp_entitlement.route("/api/entitlement/min-tier-batch-at")
def api_entitlement_min_tier_batch_at():
    """``GET /api/entitlement/min-tier-batch-at?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    hypothetical-perspective sibling of ``/api/entitlement/min-tier-batch``.

    Wraps :func:`clawmetry.entitlements.min_tier_batch_at` so a pricing-
    matrix walkthrough can render "if I were on Starter, this bundle's
    per-item cheapest tier is..." off ONE round-trip without first
    switching the resolver. Per-item plural what-if companion of
    ``/required-tier-at`` (which returns only the floor) and
    ``/affordable-tiers-at`` (which returns the full ordered list of
    qualifying tiers).

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the per-item envelope
    is anchored to the constraint bundle. A parity contract pinned in the
    test suite guarantees per-row output byte-equals
    ``/api/entitlement/min-tier-batch`` for the same bundle regardless of
    perspective; the response layers ``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank`` on top so a
    walkthrough surface can render the "from <perspective>" copy off one
    call alongside the existing ``current_tier`` / ``grace`` / ``enforced``
    resolver envelope.

    Args are byte-identical to ``/min-tier-batch`` except for the
    additional ``tier=`` perspective arg. Same CSV normalisation, same
    capacity-axis parsing, same ``None`` = "not supplied" sentinel.

    Response shape::

        {
          "perspective_tier":       "...",
          "perspective_tier_label": "...",
          "perspective_tier_rank":  <int>,
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    - **400** when ``tier=`` is missing / blank, OR when no constraint
      axis is supplied.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields the OSS-free shape
      (empty per-axis rows) so the pricing walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        batch = _ent.min_tier_batch_at(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_label"] = _ent.tier_label(tier_in)
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_min_tier_batch_at: error: %s", exc)
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
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


@bp_entitlement.route("/api/entitlement/min-tier-at")
def api_entitlement_min_tier_at():
    """``GET /api/entitlement/min-tier-at?tier=<perspective>&<axis>=<value>``
    -- hypothetical-perspective sibling of ``/api/entitlement/min-tier``.

    Wraps :func:`entitlements.min_tier_at` so a pricing-matrix walkthrough
    at a hypothetical perspective can render "if I were on Starter, this
    ONE axis constraint would land at Pro" off ONE round-trip without
    switching the resolver. Fills the ``_at`` slot for the singular
    scalar min-tier surface alongside :func:`api_entitlement_min_tier_batch_at`
    (per-item batch what-if) and :func:`api_entitlement_required_tier_at`
    (aggregate bundle what-if) so a caller can call ``X_at`` uniformly
    across the whole ``_at`` scalar / batch / bundle surface.

    Args mirror ``/api/entitlement/min-tier`` byte-for-byte -- exactly
    one of ``feature=<id>``, ``runtime=<id>``, ``channels=<int>``,
    ``retention_days=<int>``, or ``nodes=<int>`` must be supplied --
    plus the additional ``tier=`` perspective arg. Perspective is
    validated against :data:`entitlements._TIER_ORDER` (including
    :data:`entitlements.TIER_TRIAL`) but does NOT shape the result: the
    scalar answer is inherently perspective-independent (it walks the
    static per-tier caps via the matching ``min_tier_for_<axis>``
    helper), so per-row output byte-equals ``/min-tier`` for the same
    axis regardless of perspective. A cross-endpoint parity test pins
    this so the scalar what-if and the scalar current cannot silently
    drift.

    Response shape mirrors ``/min-tier`` (``key`` / ``value`` / ``free``
    / ``min_tier`` / ``tier_label`` / ``tier_rank``) with the
    ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` envelope and the standard resolver
    envelope (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``) layered on so the pricing surface reads current tier /
    grace / enforced off the same call.

    - **400** when ``tier=`` is missing / blank, or when zero / more
      than one axis is supplied, or when a capacity axis value is
      non-int.
    - **404** when ``tier=`` is unknown (body carries ``which=tier``),
      or when the ``feature=`` / ``runtime=`` id is unknown (matches
      ``/min-tier``'s 404 posture on unknown grant ids). Capacity axes
      never 404 -- any parseable int (including zero / negative --
      which collapses to :data:`entitlements.TIER_OSS` matching the
      helpers' contract) resolves to a real tier.
    - **Never 5xxs**: a resolver failure yields the same shape with
      ``min_tier=null`` and the perspective envelope populated so the
      pricing walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        feature = (request.args.get("feature") or "").strip()
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
                            "supply exactly one of feature=<id>, "
                            "runtime=<id>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        ),
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, "
                            "channels=, retention_days=, or nodes="
                        ),
                    }
                ),
                400,
            )
        if channels_present and not channels_ok:
            return (
                jsonify({"error": "channels= must be an integer"}),
                400,
            )
        if retention_present and not retention_ok:
            return (
                jsonify({"error": "retention_days= must be an integer"}),
                400,
            )
        if nodes_present and not nodes_ok:
            return (
                jsonify({"error": "nodes= must be an integer"}),
                400,
            )

        if feature:
            min_t = _ent.min_tier_for_feature(feature)
            key, value = "feature", feature
            known = feature in _ent.ALL_FEATURES
        elif runtime:
            min_t = _ent.min_tier_for_runtime(runtime)
            key, value = "runtime", runtime
            known = runtime in _ent.ALL_RUNTIMES
        elif channels_present:
            min_t = _ent.min_tier_for_channel_count(channels_n)
            key, value = "channels", str(channels_n)
            known = True
        elif retention_present:
            min_t = _ent.min_tier_for_retention_window(retention_n)
            key, value = "retention_days", str(retention_n)
            known = True
        else:
            min_t = _ent.min_tier_for_node_count(nodes_n)
            key, value = "nodes", str(nodes_n)
            known = True

        ent = _ent.get_entitlement()
        base = {
            "perspective_tier": tier_in,
            "perspective_tier_label": _ent.tier_label(tier_in),
            "perspective_tier_rank": _ent.tier_rank(tier_in),
            "current_tier": ent.tier,
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        }
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
                        **base,
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
                **base,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_min_tier_at: error: %s", exc)
        feature = (request.args.get("feature") or "").strip()
        runtime = (request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            _channels_ok,
            _channels_n,
            channels_raw,
        ) = _parse_capacity_arg("channels")
        (
            retention_present,
            _retention_ok,
            _retention_n,
            retention_raw,
        ) = _parse_capacity_arg("retention_days")
        (
            nodes_present,
            _nodes_ok,
            _nodes_n,
            nodes_raw,
        ) = _parse_capacity_arg("nodes")
        if feature:
            key, value = "feature", feature
        elif runtime:
            key, value = "runtime", runtime
        elif channels_present:
            key, value = "channels", channels_raw
        elif retention_present:
            key, value = "retention_days", retention_raw
        elif nodes_present:
            key, value = "nodes", nodes_raw
        else:
            key, value = "", ""
        return jsonify(
            {
                "key": key,
                "value": value,
                "free": False,
                "min_tier": None,
                "tier_label": None,
                "tier_rank": None,
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/affordable-tiers-batch")
def api_entitlement_affordable_tiers_batch():
    """``GET /api/entitlement/affordable-tiers-batch?features=a,b,c
    &runtimes=x,y&channels=N&retention_days=K&nodes=M`` -- per-item
    plural sibling of ``/api/entitlement/affordable-tiers``.

    Where ``/affordable-tiers`` collapses the answer to a single
    ordered list of qualifying tiers for a whole constraint bundle,
    this preserves the per-item detail so a pricing-matrix UI
    ("show me each requested feature + runtime + capacity row with
    its individual cheapest tier AND every tier above that also
    qualifies") renders off ONE round-trip instead of N calls to
    ``/affordable-tiers``. Same relationship it has to
    ``/affordable-tiers`` that ``/min-tier-batch`` has to
    ``/required-tier-batch``. Wraps
    :func:`clawmetry.entitlements.affordable_tiers_batch` and appends
    the same ``current_tier`` / ``grace`` / ``enforced`` envelope
    ``/lock-reason-batch`` returns so a caller sees the same resolver
    context alongside the per-item answers.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty /
    parseable after normalisation). ``features=`` / ``runtimes=``
    take comma-separated tokens (whitespace and duplicates are
    normalised away; runtime aliases like ``claude-code``
    canonicalise to ``claude_code``; unknown ids contribute an all-
    ``None`` row with ``tiers=[]`` -- they do not error). The three
    capacity axes take a single int each; a blank or non-int value
    is treated as "not supplied" (matches the singular endpoint's
    never-crash posture rather than mis-routing a typo to
    Enterprise). Never 5xxs: the grace-shape envelope is returned on
    any resolver failure.

    Response shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``free``, ``min_tier``,
    ``min_tier_label``, ``min_tier_rank`` (``-1`` when ``min_tier``
    is ``None``), and ``tiers`` -- the full ordered list of
    qualifying tiers for that single item (each entry carrying
    ``tier`` / ``tier_label`` / ``tier_rank`` / ``is_minimum``).
    Per-row parity with the singular
    ``/affordable-tiers?features=<id>`` endpoint is pinned in the
    test suite so the batch cannot silently drift from the scalar.
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

        batch = _ent.affordable_tiers_batch(
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
        logger.warning("api_entitlement_affordable_tiers_batch: error: %s", exc)
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


@bp_entitlement.route("/api/entitlement/affordable-tiers-at-batch")
def api_entitlement_affordable_tiers_at_batch():
    """``GET /api/entitlement/affordable-tiers-at-batch?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    hypothetical-perspective sibling of
    ``/api/entitlement/affordable-tiers-batch``.

    Wraps :func:`clawmetry.entitlements.affordable_tiers_at_batch` so a
    pricing-matrix walkthrough can render "if I were on Starter, each
    requested item's cheapest tier AND every tier above that also
    qualifies is..." off ONE round-trip without first switching the
    resolver. Per-item plural what-if companion of ``/min-tier-batch-at``
    (which returns only the per-item floor) and ``/affordable-tiers-at``
    (which aggregates the answer to a single bundle-wide ordered list).

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the per-item envelope
    is anchored to the constraint bundle. A parity contract pinned in the
    test suite guarantees per-row output byte-equals
    ``/api/entitlement/affordable-tiers-batch`` for the same bundle
    regardless of perspective; the response layers ``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank`` on top so a
    walkthrough surface can render the "from <perspective>" copy off one
    call alongside the existing ``current_tier`` / ``grace`` / ``enforced``
    resolver envelope.

    Args are byte-identical to ``/affordable-tiers-batch`` except for the
    additional ``tier=`` perspective arg. Same CSV normalisation, same
    capacity-axis parsing, same ``None`` = "not supplied" sentinel.

    Response shape::

        {
          "perspective_tier":       "...",
          "perspective_tier_label": "...",
          "perspective_tier_rank":  <int>,
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``free``, ``min_tier``,
    ``min_tier_label``, ``min_tier_rank`` (``-1`` when ``min_tier`` is
    ``None``), and ``tiers`` -- the full ordered list of qualifying tiers
    for that single item (each entry carrying ``tier`` / ``tier_label`` /
    ``tier_rank`` / ``is_minimum``). Per-row parity with the singular
    ``/affordable-tiers?features=<id>`` endpoint is pinned in the test
    suite so the batch cannot silently drift from the scalar.

    - **400** when ``tier=`` is missing / blank, OR when no constraint
      axis is supplied.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **Never 5xxs**: a resolver failure yields the grace-shape envelope
      (empty per-axis rows) so the pricing walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        batch = _ent.affordable_tiers_at_batch(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_label"] = _ent.tier_label(tier_in)
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_affordable_tiers_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
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


@bp_entitlement.route("/api/entitlement/lock-reasons-at-batch")
def api_entitlement_lock_reasons_at_batch():
    """``GET /api/entitlement/lock-reasons-at-batch?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    what-if sibling of ``/api/entitlement/lock-reason-batch``.

    Where ``/lock-reason-batch`` returns per-item lock rows against the
    LIVE resolved entitlement, this returns them against a HYPOTHETICAL
    ``perspective_tier``. Pairs with ``/lock-reason-at`` the same way
    ``/lock-reason-batch`` pairs with ``/lock-reason``: scalar -> matrix
    in one round-trip.

    Use case: a pricing-comparison matrix UI ("would my Settings page
    look like this on Cloud Pro vs Enterprise?") fetches all N rows for
    each hypothetical tier in one call instead of N calls to
    ``/lock-reason-at`` per tier.

    Exactly one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` is NOT required -- at least one
    must be supplied (matches ``/lock-reason-batch``); supply as many
    as you like. ``features=`` / ``runtimes=`` take comma-separated
    tokens (whitespace + duplicates are normalised away; unknown ids
    contribute a grace-shape row). The three capacity axes take a
    single int each; blank / non-int values are treated as "not
    supplied" (matches ``/lock-reason-batch``).

    - **400** when ``tier=`` is missing / blank or no axis is supplied
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``
      so the caller can render the right "unknown ..." message)
    - **Never 5xxs**: a synthesis failure short-circuits to the
      grace-shape payload (empty / None rows) with the perspective
      tier echoed so the UI keeps rendering.

    Response shape (byte-identical to ``/lock-reason-batch`` plus a
    ``perspective_tier`` echo for caller round-trip safety)::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "perspective_tier":      "...",
          "perspective_tier_rank": <int>,
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason``, ``locked``,
    ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank`` -- the same 8 keys ``/lock-reason-batch``
    returns. ``current_tier`` reflects the LIVE resolved tier (so the
    matrix UI can also show "you are here" badges); ``perspective_tier``
    reflects the requested hypothetical.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        batch = _ent.lock_reasons_at_batch(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning(
            "api_entitlement_lock_reasons_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
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


@bp_entitlement.route("/api/entitlement/tiers-for-at")
def api_entitlement_tiers_for_at():
    """``GET /api/entitlement/tiers-for-at?tier=<perspective>&feature=<id>``
    (or ``&runtime=<id>``) -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for``: returns the full ladder of tiers
    that grant the named feature or runtime, scoped by a caller-supplied
    ``perspective_tier``.

    Perspective is validated against ``_TIER_ORDER`` (``trial``
    accepted) but does NOT shape rows -- the ladder is intrinsically
    perspective-independent (walks static per-tier tables). The
    ``perspective_tier`` envelope lets an ``_at`` walkthrough URL be
    uniform across every ``_at`` sibling (``min_tier_batch_at``,
    ``affordable_tiers_at``, ``tiers_for_*_at``, ...).

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``
    (``which=tier``). Exactly one of ``feature=`` or ``runtime=`` must
    be supplied -- missing both is ``400``, both at once is ``400``.
    Unknown feature / runtime id is ``404``. Never 5xxs.

    Response shape mirrors ``/api/entitlement/tiers-for`` (``item``,
    ``kind``, ``label``, ``free``, ``min_tier``, ``min_tier_label``,
    ``min_tier_rank``, ``tiers``) plus a perspective envelope
    (``perspective_tier``, ``perspective_tier_label``,
    ``perspective_tier_rank``) and the resolver envelope
    (``current_tier``, ``current_tier_rank``, ``grace``, ``enforced``).
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
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

        if p not in _ent._TIER_ORDER:
            return jsonify({"error": "unknown tier", "which": "tier", "tier": p}), 404
        if feat:
            body = _ent.tiers_for_feature_at(p, feat)
            kind = "feature"
            item = feat
        else:
            body = _ent.tiers_for_runtime_at(p, rt)
            kind = "runtime"
            item = rt
        if body is None:
            return jsonify({"error": f"unknown {kind}", kind: item}), 404
        ent = _ent.get_entitlement()
        envelope = dict(body)
        envelope["perspective_tier"] = p
        envelope["perspective_tier_label"] = _ent.tier_label(p)
        envelope["perspective_tier_rank"] = _ent.tier_rank(p)
        envelope["current_tier"] = ent.tier
        envelope["current_tier_rank"] = _ent.tier_rank(ent.tier)
        envelope["grace"] = bool(ent.grace)
        envelope["enforced"] = _ent.is_enforced()
        return jsonify(envelope)
    except Exception as exc:
        logger.warning("api_entitlement_tiers_for_at: error: %s", exc)
        return jsonify({"error": "tiers-for-at failed"}), 500


@bp_entitlement.route("/api/entitlement/tiers-for-batch-at")
def api_entitlement_tiers_for_batch_at():
    """``GET /api/entitlement/tiers-for-batch-at?tier=<perspective>`` --
    hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-batch``: returns the full availability
    ladder for every known feature *and* runtime in one pass, scoped by
    a caller-supplied ``perspective_tier``.

    Fills the ``_at`` slot on the batch tiers-for axis alongside
    ``/tiers-for-at`` so a pricing-matrix walkthrough can call every
    ``_at`` sibling with a uniform ``tier=<perspective>`` URL.
    Perspective is validated but does NOT shape rows -- the batch is
    identical to ``/tiers-for-batch`` regardless of perspective
    (pinned by cross-endpoint parity test).

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``.
    Never 5xxs: a resolver failure yields empty ``features`` /
    ``runtimes`` lists plus the perspective + grace envelope so the
    pricing UI keeps rendering.

    Response shape::

        {
          "features":               [<row>, ...],
          "runtimes":               [<row>, ...],
          "perspective_tier":       "...",
          "perspective_tier_label": "...",
          "perspective_tier_rank":  <int>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return jsonify({"error": "unknown tier", "which": "tier", "tier": p}), 404
        body = _ent.tiers_for_batch_at(p)
        if body is None:
            body = {"features": [], "runtimes": []}
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "features": body.get("features", []),
                "runtimes": body.get("runtimes", []),
                "perspective_tier": p,
                "perspective_tier_label": _ent.tier_label(p),
                "perspective_tier_rank": _ent.tier_rank(p),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tiers_for_batch_at: error: %s", exc)
        try:
            from clawmetry import entitlements as _ent

            label = _ent.tier_label(p)
            rank = _ent.tier_rank(p)
        except Exception:
            label = p
            rank = 0
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "perspective_tier": p,
                "perspective_tier_label": label,
                "perspective_tier_rank": rank,
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


@bp_entitlement.route("/api/entitlement/tier-spec")
def api_entitlement_tier_spec():
    """``GET /api/entitlement/tier-spec?tier=<id>`` -- scalar sibling of
    ``/api/tiers``: the full per-tier descriptor for one tier id in one
    shot, matching exactly one row from :func:`entitlements.tier_catalog`.

    Lets a pricing-page column / upsell tooltip hydrate against a single
    tier without fetching the whole ladder and filtering client-side.

    - **400** when ``tier=`` is missing / blank
    - **404** when the id is not a known tier (catalogue-derived; the
      id is echoed in the body so the caller can render "unknown tier")
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      shape (``is_current=False`` for the resolved fields) but still
      returns the catalogue row for the requested tier.
    """
    raw = request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_spec(tier)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        return jsonify(body)
    except Exception as exc:
        logger.warning("api_entitlement_tier_spec: error: %s", exc)
        return jsonify({"error": "tier-spec failed"}), 500


@bp_entitlement.route("/api/entitlement/tier-spec-batch")
def api_entitlement_tier_spec_batch():
    """``GET /api/entitlement/tier-spec-batch?tiers=a,b,c`` -- plural
    sibling of ``/api/entitlement/tier-spec``.

    Returns the full catalogue spec row for every supplied tier id in
    one round-trip. Mirrors the scalar / batch pair
    :func:`api_entitlement_feature_spec_batch` and
    :func:`api_entitlement_runtime_spec_batch` establish on the feature
    / runtime axes, so a pricing-comparison matrix UI hydrates the N
    visible tier rows off one call instead of N calls to
    ``/tier-spec``.

    Each ``tiers[]`` entry is byte-identical to a row from
    :func:`entitlements.tier_catalog` (and to the scalar
    :func:`entitlements.tier_spec` for the same id) -- a parity test
    pins this so the scalar / bulk / batch accessors cannot drift.
    Supplied ids are normalised (whitespace stripped, lowercased,
    duplicates dropped while preserving first-seen order). Unknown ids
    do not 404 the call -- they are echoed in ``unknown[]`` so a
    partially-bad caller still gets rows back for the valid ids
    alongside a list of what was dropped.

    Response shape::

        {
          "tiers":             [<spec_row>, ...],
          "unknown":           ["bogus_id", ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing or empty after normalisation
    - **Never 5xxs**: a resolver crash short-circuits to the OSS-free
      shape (empty rows, ``current_tier=oss``, ``grace=true``).
    """
    try:
        tiers = _parse_csv_arg("tiers")
        if not tiers:
            return (
                jsonify({"error": "supply tiers=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.tier_spec_batch(tiers)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("api_entitlement_tier_spec_batch: error: %s", exc)
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
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


@bp_entitlement.route("/api/entitlement/next-tier-unlocks-at")
def api_entitlement_next_tier_unlocks_at():
    """``GET /api/entitlement/next-tier-unlocks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/next-tier-unlocks``:
    marginal unlocks row at the rung above the caller-supplied
    ``tier``, in :func:`clawmetry.entitlements.tier_unlocks` shape.

    Lets a pricing page render the "what's new at the next rung above
    X" upgrade-CTA cell for any hypothetical ``X`` without first asking
    the resolver and without monkey-patching the entitlement context --
    the scalar what-if the live ``/next-tier-unlocks`` endpoint surfaces
    against the resolved entitlement, parameterised over the source.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_unlocks row>} | null,
        }

    The inner ``row`` matches the live ``/next-tier-unlocks`` ``locks``-
    style row shape (``tier``, ``tier_label``, ``tier_rank``,
    ``previous_tier``, ``previous_tier_label``, ``previous_tier_rank``,
    ``features``, ``runtimes``). The row IS the tier-property row of
    the rung above (its ``previous_tier`` is that rung's natural next-
    lower purchasable, NOT the caller-supplied ``tier``) -- the same
    posture the live endpoint surfaces. Callers who want the source-
    anchored ``previous_tier`` should use ``/tier-unlocks-at`` with the
    explicit ``(tier, target)`` pair.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source) -- the surface stays 200 with a populated
    envelope so callers can render "you're at the top" copy without
    a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_unlocks_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_unlocks_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-locks-at")
def api_entitlement_next_tier_locks_at():
    """``GET /api/entitlement/next-tier-locks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/next-tier-locks``:
    marginal locks row at the rung above the caller-supplied ``tier``,
    in :func:`clawmetry.entitlements.tier_locks` shape.

    Marginal-loss mirror of ``/next-tier-unlocks-at`` and pairs with
    the live ``/next-tier-locks`` (source pinned to the resolver) the
    same way ``/tier-locks-at`` pairs with ``/tier-locks``. Lets a
    pricing page render the "what does the rung above X first lose vs
    the rung above IT" detail cell for any hypothetical ``X`` without
    asking the resolver.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_locks row>} | null,
        }

    The inner ``row`` matches the live ``/next-tier-locks`` ``locks``
    row shape (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``). At the rung where the next-above IS the ladder
    ceiling (enterprise), the row's ``next_tier`` is ``null`` and the
    ``lost_*`` lists collapse to ``[]`` -- :func:`tier_locks` shape
    for "this rung has no rung above to step down from", not ``null``
    on the envelope.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the
    source-side ceiling (enterprise as source -- no rung strictly
    above) -- the surface stays 200 with a populated envelope.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so
      a caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_locks_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_locks_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-unlocks-at")
def api_entitlement_previous_tier_unlocks_at():
    """``GET /api/entitlement/previous-tier-unlocks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/previous-tier-unlocks``:
    marginal unlocks row at the rung below the caller-supplied
    ``tier``, in :func:`clawmetry.entitlements.tier_unlocks` shape.

    Source-anchored mirror of ``/api/entitlement/next-tier-unlocks-at``
    and downgrade-side counterpart of the live
    ``/api/entitlement/previous-tier-unlocks`` endpoint. Lets a pricing
    page render the "what would still be granted at the rung below X"
    downgrade-CTA cell for any hypothetical ``X`` without first asking
    the resolver and without monkey-patching the entitlement context.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_unlocks row>} | null,
        }

    The inner ``row`` matches the live ``/previous-tier-unlocks`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``). The row IS the tier-property row of the rung below
    (its ``previous_tier`` is that rung's natural next-lower
    purchasable, NOT the caller-supplied ``tier``). Callers who want
    the source-anchored ``previous_tier`` should use ``/tier-unlocks-at``
    with the explicit ``(tier, target)`` pair.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly below
    the source -- oss / cloud_free) -- the surface stays 200 with a
    populated envelope so callers can render "you're at the bottom"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_unlocks_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_unlocks_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-locks-at")
def api_entitlement_previous_tier_locks_at():
    """``GET /api/entitlement/previous-tier-locks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/previous-tier-locks``:
    marginal locks row at the rung below the caller-supplied ``tier``,
    in :func:`clawmetry.entitlements.tier_locks` shape.

    Source-anchored mirror of ``/api/entitlement/next-tier-locks-at``.
    Marginal-loss companion to ``/previous-tier-unlocks-at`` on a
    hypothetical pricing matrix cell -- where the unlocks form shows
    "what the rung below still grants" the locks form shows "what the
    rung below first loses vs the rung above IT".

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_locks row>} | null,
        }

    The inner ``row`` matches the live ``/previous-tier-locks`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``). The row's ``next_tier`` is the rung-below's
    natural next-higher purchasable, NOT the caller-supplied source.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor
    (no rung strictly below the source -- oss / cloud_free) -- the
    surface stays 200 with a populated envelope.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_locks_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_locks_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-unlocks-at-batch")
def api_entitlement_next_tier_unlocks_at_batch():
    """``GET /api/entitlement/next-tier-unlocks-at-batch`` -- batch
    sibling of ``/api/entitlement/next-tier-unlocks-at``: one
    ``next-tier-unlocks-at`` envelope per purchasable source tier, in
    one round-trip.

    Composes the scalar what-if (``/next-tier-unlocks-at``) and the
    live batch (``/tier-unlocks-batch``) -- same envelope shape per row
    as the scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "what's new at the rung
    above each rung" upgrade-CTA column off **one** call instead of N
    calls to ``/next-tier-unlocks-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-unlocks-batch``
    endpoint, so the envelopes fold into the same pricing-page table
    byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-unlocks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side ceiling (``enterprise`` as source -- no rung strictly
    above) the envelope carries ``target=null`` and ``row=null`` rather
    than being dropped, so the matrix keeps a row for every purchasable
    rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_unlocks_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_unlocks_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-locks-at-batch")
def api_entitlement_next_tier_locks_at_batch():
    """``GET /api/entitlement/next-tier-locks-at-batch`` -- batch
    sibling of ``/api/entitlement/next-tier-locks-at``: one
    ``next-tier-locks-at`` envelope per purchasable source tier, in one
    round-trip.

    Marginal-loss mirror of ``/next-tier-unlocks-at-batch`` and pairs
    with ``/tier-locks-batch`` the same way
    ``/next-tier-unlocks-at-batch`` pairs with ``/tier-unlocks-batch``.
    Pair the two ``_at_batch`` endpoints to render the upgrade-CTA +
    downgrade-warning columns of an "above each rung" pricing matrix
    in two round-trips.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-locks-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-locks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side ceiling (``enterprise`` as source) the envelope
    carries ``target=null`` and ``row=null``. At a source rung whose
    next-above IS the ladder ceiling (``cloud_pro`` / ``pro`` ->
    ``enterprise``) the row carries ``next_tier=null`` and empty
    ``lost_*`` lists -- :func:`tier_locks` shape for "the target has no
    rung above to step down from", NOT ``null`` on the envelope.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_locks_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_locks_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-unlocks-at-batch")
def api_entitlement_previous_tier_unlocks_at_batch():
    """``GET /api/entitlement/previous-tier-unlocks-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-unlocks-at``: one
    ``previous-tier-unlocks-at`` envelope per purchasable source tier,
    in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-unlocks-at-batch``. Composes the
    scalar what-if (``/previous-tier-unlocks-at``) and the live batch
    (``/tier-unlocks-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "what would still be
    granted at the rung below each rung" downgrade-CTA column off
    **one** call instead of N calls to ``/previous-tier-unlocks-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-unlocks-batch``
    endpoint, so the envelopes fold into the same pricing-page table
    byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-unlocks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side floor (``oss`` / ``cloud_free`` as source -- no rung
    strictly below) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_unlocks_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_unlocks_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-locks-at-batch")
def api_entitlement_previous_tier_locks_at_batch():
    """``GET /api/entitlement/previous-tier-locks-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-locks-at``: one
    ``previous-tier-locks-at`` envelope per purchasable source tier,
    in one round-trip.

    Marginal-loss mirror of ``/previous-tier-unlocks-at-batch`` and
    pairs with ``/tier-locks-batch`` the same way
    ``/previous-tier-unlocks-at-batch`` pairs with
    ``/tier-unlocks-batch``. Pair the two ``previous-*-at-batch``
    endpoints to render the downgrade-CTA + downgrade-warning columns
    of a "below each rung" pricing matrix in two round-trips.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-locks-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-locks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side floor (``oss`` / ``cloud_free`` as source) the
    envelope carries ``target=null`` and ``row=null``. At a source
    rung whose next-below IS the ladder floor (``cloud_starter`` ->
    ``oss``) the row carries populated ``lost_features`` /
    ``lost_runtimes`` lists -- :func:`tier_locks` shape against the
    floor's next-above rung -- NOT ``null`` on the envelope.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_locks_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_locks_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-diff-at")
def api_entitlement_next_tier_diff_at():
    """``GET /api/entitlement/next-tier-diff-at?tier=<source>`` --
    scalar what-if sibling of the live ``Entitlement.next_tier_diff``:
    full :func:`clawmetry.entitlements.tier_diff` row from the caller-
    supplied ``tier`` to the rung above it.

    Lets a pricing-comparison or upgrade-CTA card render the full
    upgrade payload (``added_*``, ``lost_*``, ``capacity_changes``,
    ``direction``) for any hypothetical source rung off **one** round-
    trip, without first hitting ``/api/entitlement`` and without
    monkey-patching the entitlement context. Pairs with
    ``/api/entitlement/next-tier-unlocks-at`` and
    ``/api/entitlement/next-tier-locks-at`` (the marginal-grant /
    marginal-loss views of the same step) on a hypothetical pricing
    matrix cell.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_diff row>} | null,
        }

    Unlike ``/api/entitlement/next-tier-unlocks-at`` -- which surfaces
    the target's own ``tier_unlocks`` row (target-anchored,
    ``previous_tier`` is the target's natural next-lower purchasable,
    NOT the caller-supplied source) -- this endpoint pins **both**
    endpoints, so ``row.from`` is byte-equal to ``tier``. That mirrors
    the live ``Entitlement.next_tier_diff`` posture and is the natural
    shape for a two-endpoint diff. ``row.direction`` is always
    ``"upgrade"`` for any purchasable source that has a strictly-higher
    rung above; from ``trial`` ``row.direction`` is ``"upgrade"`` too
    (next strictly-higher purchasable resolves to enterprise).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source -- enterprise as source) -- the surface stays 200
    with a populated envelope so callers can render "you're at the top"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_diff_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_diff_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-diff-at")
def api_entitlement_previous_tier_diff_at():
    """``GET /api/entitlement/previous-tier-diff-at?tier=<source>`` --
    scalar what-if sibling of the live
    ``Entitlement.previous_tier_diff``: full
    :func:`clawmetry.entitlements.tier_diff` row from the caller-
    supplied ``tier`` to the rung below it.

    Source-anchored mirror of ``/api/entitlement/next-tier-diff-at``
    and downgrade-side counterpart of the live
    ``Entitlement.previous_tier_diff``. Lets a downgrade-confirmation
    card or pricing-comparison cell render the full step-down payload
    for any hypothetical source rung off **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_diff row>} | null,
        }

    Like ``/api/entitlement/next-tier-diff-at`` (and unlike
    ``/api/entitlement/previous-tier-unlocks-at`` which surfaces the
    target's own ``tier_unlocks`` row), this endpoint pins **both**
    endpoints, so ``row.from`` is byte-equal to ``tier``. That mirrors
    the live ``Entitlement.previous_tier_diff`` posture and is the
    natural shape for a two-endpoint diff. ``row.direction`` is always
    ``"downgrade"`` for any purchasable source that has a strictly-
    lower rung below; from ``trial`` ``row.direction`` is
    ``"downgrade"`` (next strictly-lower purchasable resolves to
    cloud_starter).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly
    below the source -- oss / cloud_free) -- the surface stays 200
    with a populated envelope so callers can render "you're at the
    bottom" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_diff_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_diff_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-diff-at-batch")
def api_entitlement_next_tier_diff_at_batch():
    """``GET /api/entitlement/next-tier-diff-at-batch`` -- batch sibling
    of ``/api/entitlement/next-tier-diff-at``: one ``next-tier-diff-at``
    envelope per purchasable source tier, in one round-trip.

    Composes the scalar what-if (``/next-tier-diff-at``) and the live
    batch (``/tier-diff-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    above each rung" upgrade-CTA column off **one** call instead of N
    calls to ``/next-tier-diff-at``.

    The "all-slices-in-one-row" member of the ``next-*-at-batch``
    family alongside ``/next-tier-unlocks-at-batch`` (feature / runtime
    grant slice) and ``/next-tier-locks-at-batch`` (feature / runtime
    loss slice). Where each of those siblings carries a single slice of
    the per-rung transition, this batch carries ALL slices in one row
    so a UI can render the whole upgrade matrix off one call instead of
    two.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint,
    so the envelopes fold into the same pricing-page table byte-for-
    byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-diff-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the full :func:`tier_diff` payload pinned on both
    endpoints (``row.from`` is byte-equal to the envelope's ``tier``).
    At the source-side ceiling (``enterprise`` as source -- no rung
    strictly above) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_diff_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_diff_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-diff-at-batch")
def api_entitlement_previous_tier_diff_at_batch():
    """``GET /api/entitlement/previous-tier-diff-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-diff-at``: one
    ``previous-tier-diff-at`` envelope per purchasable source tier, in
    one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-diff-at-batch``. Composes the scalar
    what-if (``/previous-tier-diff-at``) and the live batch
    (``/tier-diff-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    below each rung" downgrade-CTA column off **one** call instead of N
    calls to ``/previous-tier-diff-at``.

    The "all-slices-in-one-row" member of the ``previous-*-at-batch``
    family alongside ``/previous-tier-unlocks-at-batch`` (feature /
    runtime grant slice on a downgrade) and
    ``/previous-tier-locks-at-batch`` (feature / runtime loss slice on
    a downgrade). Where each of those siblings carries a single slice
    of the per-rung transition, this batch carries ALL slices in one
    row so a UI can render the whole downgrade matrix off one call
    instead of two.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-diff-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the full :func:`tier_diff` payload pinned on both
    endpoints (``row.from`` is byte-equal to the envelope's ``tier``).
    At the source-side floor (``oss`` / ``cloud_free`` as source -- no
    rung strictly below) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_diff_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_diff_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-capacity-diff-at")
def api_entitlement_next_tier_capacity_diff_at():
    """``GET /api/entitlement/next-tier-capacity-diff-at?tier=<source>`` --
    scalar what-if sibling of the live
    ``Entitlement.next_tier_capacity_diff``: per-axis capacity
    transition from the caller-supplied ``tier`` to the rung above it.

    Capacity-only narrow lens of
    ``/api/entitlement/next-tier-diff-at`` -- the latter returns the
    full :func:`tier_diff` payload for the same step; this endpoint
    returns only the capacity slice
    (``{target, channel_limit, retention_days, node_limit}``) so a
    capacity-only tooltip on a pricing-comparison cell can render the
    upgrade-side capacity delta for any hypothetical source rung off
    **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<capacity_diff_at row>} | null,
        }

    ``row`` is byte-equal to
    ``/api/entitlement/next-tier-diff-at?tier=<source>``'s
    ``row.capacity_changes`` for the same source (modulo the outer
    :func:`_capacity_row` ``target`` key the diff row does not carry).
    The ``before`` side of each axis comes off the static per-tier
    caps anchored at the caller-supplied ``tier`` (NOT the resolved
    entitlement), so the endpoint is independent of grace mode.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source -- enterprise as source) -- the surface stays 200
    with a populated envelope so callers can render "you're at the top"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_capacity_diff_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_capacity_diff_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff-at")
def api_entitlement_previous_tier_capacity_diff_at():
    """``GET /api/entitlement/previous-tier-capacity-diff-at?tier=<source>``
    -- scalar what-if sibling of the live
    ``Entitlement.previous_tier_capacity_diff``: per-axis capacity
    transition from the caller-supplied ``tier`` to the rung below it.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-diff-at`` and capacity-only
    narrow lens of ``/api/entitlement/previous-tier-diff-at``. Lets a
    downgrade-confirmation tooltip render the step-down capacity
    delta for any hypothetical source rung off **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<capacity_diff_at row>} | null,
        }

    ``row`` is byte-equal to
    ``/api/entitlement/previous-tier-diff-at?tier=<source>``'s
    ``row.capacity_changes`` for the same source (modulo the outer
    :func:`_capacity_row` ``target`` key the diff row does not carry).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly
    below the source -- oss / cloud_free) -- the surface stays 200
    with a populated envelope so callers can render "you're at the
    bottom" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_capacity_diff_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_capacity_diff_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-capacity-diff-at-batch")
def api_entitlement_next_tier_capacity_diff_at_batch():
    """``GET /api/entitlement/next-tier-capacity-diff-at-batch`` --
    batch sibling of ``/api/entitlement/next-tier-capacity-diff-at``:
    one ``next-tier-capacity-diff-at`` envelope per purchasable source
    tier, in one round-trip.

    Capacity-only narrow lens of
    ``/api/entitlement/next-tier-diff-at-batch``. Lets a pricing-
    comparison matrix UI render the "capacity at the rung above each
    rung" upgrade-tooltip column off **one** call instead of N calls
    to ``/next-tier-capacity-diff-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint
    and the sibling diff / unlocks / locks ``_at_batch`` endpoints, so
    the four batches fold into the same pricing-page table byte-for-
    byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-capacity-diff-at?tier=<source>`` for
    that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the :func:`capacity_diff_at` row pinned on both
    endpoints. At the source-side ceiling (``enterprise`` as source --
    no rung strictly above) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_capacity_diff_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_capacity_diff_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff-at-batch")
def api_entitlement_previous_tier_capacity_diff_at_batch():
    """``GET /api/entitlement/previous-tier-capacity-diff-at-batch`` --
    batch sibling of ``/api/entitlement/previous-tier-capacity-diff-at``:
    one ``previous-tier-capacity-diff-at`` envelope per purchasable
    source tier, in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-diff-at-batch`` and capacity-
    only narrow lens of
    ``/api/entitlement/previous-tier-diff-at-batch``. Lets a pricing-
    comparison matrix UI render the "capacity at the rung below each
    rung" downgrade-tooltip column off **one** call instead of N calls
    to ``/previous-tier-capacity-diff-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint
    and the sibling diff / unlocks / locks ``_at_batch`` endpoints.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/previous-tier-capacity-diff-at?tier=<source>``
    for that source exactly. At the source-side floor (``oss`` /
    ``cloud_free`` as source -- no rung strictly below) the envelope
    carries ``target=null`` and ``row=null`` rather than being
    dropped, so the matrix keeps a row for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_capacity_diff_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_capacity_diff_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-spec")
def api_entitlement_next_tier_spec():
    """``GET /api/entitlement/next-tier-spec`` -- full
    :func:`clawmetry.entitlements.tier_spec` descriptor for the rung
    immediately above the resolved entitlement.

    Current-relative convenience for
    ``/api/entitlement/tier-spec?tier=<next_purchasable_tier>``; the
    upgrade-CTA companion to ``/api/entitlement/next-tier-diff``
    (full ``upgrade_diff`` shape), ``/next-tier-unlocks`` (marginal
    grants), ``/next-tier-locks`` (marginal losses), and
    ``/next-tier-capacity-diff`` (capacity-only). Returns
    ``{"spec": null, ...}`` at the ceiling (no rung above to upgrade
    to). Never 5xxs: a resolver failure short-circuits to the
    grace-shape envelope so the dashboard CTA keeps rendering
    instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.next_tier_spec()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "spec": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_spec: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "spec": None,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-spec")
def api_entitlement_previous_tier_spec():
    """``GET /api/entitlement/previous-tier-spec`` -- full
    :func:`clawmetry.entitlements.tier_spec` descriptor for the rung
    immediately below the resolved entitlement.

    Symmetric companion to ``/api/entitlement/next-tier-spec`` -- the
    full tier-row of the rung below current, useful on a downgrade-
    confirmation card alongside ``/previous-tier-diff``,
    ``/previous-tier-unlocks``, ``/previous-tier-locks``, and
    ``/previous-tier-capacity-diff``. ``spec`` collapses to ``null`` at
    the floor (no rung below). Never 5xxs: a resolver failure
    short-circuits to the grace-shape envelope so the confirmation
    surface keeps rendering instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.previous_tier_spec()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "spec": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_spec: error: %s", exc)
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "spec": None,
                "grace": True,
                "enforced": False,
            }
        )


def _next_prev_tier_axis_spec_grace_body(
    axis: str, item: str | None
) -> dict:
    """Fallback envelope shared by the four bare next/previous per-axis
    spec routes. Keeps the shape identical to the happy path so a
    resolver failure never breaks a paywall tooltip client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        axis: item or "",
        "target": None,
        "target_label": None,
        "target_rank": None,
        "row": None,
        "grace": True,
        "enforced": False,
    }


@bp_entitlement.route("/api/entitlement/next-tier-feature-spec")
def api_entitlement_next_tier_feature_spec():
    """``GET /api/entitlement/next-tier-feature-spec?feature=<id>`` --
    current-relative sibling of ``/api/entitlement/next-tier-feature-spec-at``:
    the :func:`feature_spec_at`-shape row for ``feature`` at the rung
    above the resolved entitlement.

    Feature-axis projection of ``/api/entitlement/next-tier-spec``. Lets
    a paywall tooltip ask "does THIS feature unlock at my next rung?"
    off ONE round-trip without threading the current tier through the
    query args or first fetching ``/feature-catalog-at`` at the target
    rung and filtering client-side. Companion to ``/next-tier-spec``,
    ``/next-tier-unlocks``, ``/next-tier-diff``, and
    ``/next-tier-capacity-diff`` on the feature axis.

    Response shape::

        {
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<resolved label>",
          "current_tier_rank":  <resolved rank>,
          "feature":            "<feature id>",
          "target":             "<next-above tier id>" | null,
          "target_label":       "<next-above label>" | null,
          "target_rank":        <next-above rank> | null,
          "row":                {<feature_spec_at row>} | null,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    ``target`` and ``row`` collapse to ``null`` at the ceiling (resolved
    entitlement already at enterprise -- no rung above to upgrade to);
    the surface stays 200 so callers render "you're at the top" copy
    without a status-code branch.

    - **400** on missing / blank ``feature=``
    - **404** on unknown ``feature`` (not in ``ALL_FEATURES``)
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with ``row=null`` so the tooltip stays mute.
    """
    raw_feature = request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        row = ent.next_tier_feature_spec(feature)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "feature": feature,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_feature_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("feature", feature))


@bp_entitlement.route("/api/entitlement/previous-tier-feature-spec")
def api_entitlement_previous_tier_feature_spec():
    """``GET /api/entitlement/previous-tier-feature-spec?feature=<id>``
    -- symmetric downgrade-side companion of
    ``/next-tier-feature-spec``: the :func:`feature_spec_at`-shape row
    for ``feature`` at the rung below the resolved entitlement.

    Same envelope as ``/next-tier-feature-spec``; ``target`` and ``row``
    collapse to ``null`` at the floor (resolved entitlement at
    ``oss`` / ``cloud_free`` -- no rung below).

    - **400** on missing / blank ``feature=``
    - **404** on unknown ``feature``
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    raw_feature = request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        row = ent.previous_tier_feature_spec(feature)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "feature": feature,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_feature_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("feature", feature))


@bp_entitlement.route("/api/entitlement/next-tier-runtime-spec")
def api_entitlement_next_tier_runtime_spec():
    """``GET /api/entitlement/next-tier-runtime-spec?runtime=<id>`` --
    runtime-axis mirror of ``/next-tier-feature-spec``: the
    :func:`runtime_spec_at`-shape row for ``runtime`` at the rung above
    the resolved entitlement.

    Accepts aliases (``claude-code`` -> ``claude_code``) via
    :func:`canonical_runtime`, matching ``/next-tier-runtime-spec-at``
    and ``/api/entitlement/required-tier``. The canonical id is echoed
    back in the ``runtime`` field so callers can compare.

    Envelope matches ``/next-tier-feature-spec`` with ``feature`` swapped
    for ``runtime``.

    - **400** on missing / blank ``runtime=``
    - **404** on unknown ``runtime`` (not in ``ALL_RUNTIMES`` after
      alias canonicalisation). The body echoes the original supplied
      alias so callers can render "unknown runtime <alias>" copy.
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    raw_runtime = request.args.get("runtime")
    supplied = (raw_runtime or "").strip().lower()
    if not supplied:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(supplied)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": supplied,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        row = ent.next_tier_runtime_spec(rt)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "runtime": rt,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_runtime_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("runtime", supplied))


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec")
def api_entitlement_previous_tier_runtime_spec():
    """``GET /api/entitlement/previous-tier-runtime-spec?runtime=<id>``
    -- symmetric downgrade-side companion of
    ``/next-tier-runtime-spec``: the :func:`runtime_spec_at`-shape row
    for ``runtime`` at the rung below the resolved entitlement.

    Accepts aliases via :func:`canonical_runtime`.

    Same envelope as ``/next-tier-runtime-spec``; ``target`` and ``row``
    collapse to ``null`` at the floor.

    - **400** on missing / blank ``runtime=``
    - **404** on unknown ``runtime``
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    raw_runtime = request.args.get("runtime")
    supplied = (raw_runtime or "").strip().lower()
    if not supplied:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(supplied)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": supplied,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        row = ent.previous_tier_runtime_spec(rt)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "runtime": rt,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_runtime_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("runtime", supplied))


@bp_entitlement.route("/api/entitlement/next-tier-channel-spec")
def api_entitlement_next_tier_channel_spec():
    """``GET /api/entitlement/next-tier-channel-spec?channel=<id>`` --
    channel-axis mirror of ``/next-tier-feature-spec`` and
    ``/next-tier-runtime-spec``: the :func:`channel_spec_at`-shape row
    for ``channel`` at the rung above the resolved entitlement.

    Envelope matches ``/next-tier-runtime-spec`` with ``runtime``
    swapped for ``channel``.

    Every chat channel is FREE at every tier -- see
    :func:`channel_spec_at` -- so ``row`` always comes back
    ``free=True`` / ``locked=False`` regardless of the target rung.
    That parity IS the answer: pricing tooltips can render "chat
    channel included at every plan" off ONE call.

    - **400** on missing / blank ``channel=``
    - **404** on unknown ``channel`` (not in ``ALL_CHANNELS``). The
      body echoes the original supplied id so callers can render
      "unknown channel <id>" copy.
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    raw_channel = request.args.get("channel")
    supplied = (raw_channel or "").strip().lower()
    if not supplied:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if supplied not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": supplied,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        row = ent.next_tier_channel_spec(supplied)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "channel": supplied,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_channel_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("channel", supplied))


def _next_prev_tier_channel_catalog_grace_body() -> dict:
    """Fallback envelope shared by the two next/previous channel-catalog
    routes. Keeps the shape identical to the happy path so a resolver
    failure never breaks an upgrade-preview panel client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "channels": [],
        "grace": True,
        "enforced": False,
    }


def _next_prev_tier_axis_catalog_grace_body(axis: str) -> dict:
    """Fallback envelope shared by the next/previous feature- and
    runtime-catalog routes. Same shape as the happy path so a resolver
    failure never breaks an upgrade-preview matrix client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        axis: [],
        "grace": True,
        "enforced": False,
    }


@bp_entitlement.route("/api/entitlement/next-tier-channel-catalog")
def api_entitlement_next_tier_channel_catalog():
    """``GET /api/entitlement/next-tier-channel-catalog`` -- channel-axis
    catalog projection of ``/next-tier-spec``: the full
    :func:`channel_catalog_at`-shape catalogue for every chat-channel
    adapter at the rung above the resolved entitlement.

    Current-relative, no-arg sibling of
    ``/api/entitlement/channel-catalog-at``. Convenience for
    ``/channel-catalog-at?tier=<next_purchasable_tier>`` so an
    upgrade-preview panel can hydrate the whole channel matrix at the
    next rung off ONE round-trip without threading the current tier
    through query args or first fetching ``/entitlement`` for
    ``next_tier``.

    Anchored on :meth:`Entitlement.next_purchasable_tier` (source-aware),
    matching ``/next-tier-spec`` and ``/next-tier-channel-spec``.

    Response shape::

        {
          "current_tier":       "<resolved id>",
          "current_tier_label": ...,
          "current_tier_rank":  <int>,
          "target":             "<next_purchasable_tier id or null>",
          "target_label":       ...,
          "target_rank":        <int or null>,
          "channels":           [<catalog_row>, ...],  # empty at ceiling
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    ``channels`` is byte-identical to the body of
    ``/channel-catalog-at?tier=<target>`` for the same tier -- pinned by
    a parity test so the endpoint cannot drift from the sibling.

    Every chat channel is FREE at every tier, so every row comes back
    ``free=True`` / ``locked=False`` / ``entitled=True`` regardless of
    the target rung.

    Never 5xxs: at the ceiling ``channels`` collapses to ``[]`` (no rung
    above to preview); a resolver failure short-circuits to the
    grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        rows = ent.next_tier_channel_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_channel_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_channel_catalog_grace_body())


@bp_entitlement.route("/api/entitlement/previous-tier-channel-spec")
def api_entitlement_previous_tier_channel_spec():
    """``GET /api/entitlement/previous-tier-channel-spec?channel=<id>``
    -- symmetric downgrade-side companion of
    ``/next-tier-channel-spec``: the :func:`channel_spec_at`-shape row
    for ``channel`` at the rung below the resolved entitlement.

    Same envelope as ``/next-tier-channel-spec``; ``target`` and ``row``
    collapse to ``null`` at the floor.

    - **400** on missing / blank ``channel=``
    - **404** on unknown ``channel``
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    raw_channel = request.args.get("channel")
    supplied = (raw_channel or "").strip().lower()
    if not supplied:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if supplied not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": supplied,
                    }
                ),
                404,
            )
        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        row = ent.previous_tier_channel_spec(supplied)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "channel": supplied,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_channel_spec: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_grace_body("channel", supplied))


@bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog")
def api_entitlement_previous_tier_channel_catalog():
    """``GET /api/entitlement/previous-tier-channel-catalog`` --
    symmetric downgrade-side companion of
    ``/next-tier-channel-catalog``: the full
    :func:`channel_catalog_at`-shape catalogue for every chat-channel
    adapter at the rung below the resolved entitlement.

    Same envelope as ``/next-tier-channel-catalog``; ``channels``
    collapses to ``[]`` at the floor and ``target`` / ``target_label``
    / ``target_rank`` to ``null``.

    Anchored on :meth:`Entitlement.previous_purchasable_tier`
    (source-aware), matching ``/previous-tier-spec`` and
    ``/previous-tier-channel-spec``.

    Never 5xxs: grace-shape envelope on resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        rows = ent.previous_tier_channel_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_channel_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_channel_catalog_grace_body())


@bp_entitlement.route("/api/entitlement/next-tier-feature-catalog")
def api_entitlement_next_tier_feature_catalog():
    """``GET /api/entitlement/next-tier-feature-catalog`` -- feature-axis
    catalog projection of ``/next-tier-spec``: the full
    :func:`feature_catalog_at`-shape catalogue for every feature at the
    rung above the resolved entitlement.

    Current-relative, no-arg sibling of
    ``/api/entitlement/feature-catalog-at`` and feature-axis mirror of
    ``/api/entitlement/next-tier-channel-catalog``. Convenience for
    ``/feature-catalog-at?tier=<next_purchasable_tier>`` so a pricing /
    upgrade-preview panel can hydrate the whole feature matrix at the
    next rung off ONE round-trip without threading the current tier
    through query args or first fetching ``/entitlement`` for
    ``next_tier``.

    Anchored on :meth:`Entitlement.next_purchasable_tier` (source-aware),
    matching ``/next-tier-spec`` and ``/next-tier-feature-spec``.

    Response shape::

        {
          "current_tier":       "<resolved id>",
          "current_tier_label": ...,
          "current_tier_rank":  <int>,
          "target":             "<next_purchasable_tier id or null>",
          "target_label":       ...,
          "target_rank":        <int or null>,
          "features":           [<catalog_row>, ...],  # empty at ceiling
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    ``features`` is byte-identical to the body of
    ``/feature-catalog-at?tier=<target>`` for the same tier -- pinned by
    a parity test so the endpoint cannot drift from the sibling.

    Never 5xxs: at the ceiling ``features`` collapses to ``[]`` (no rung
    above to preview); a resolver failure short-circuits to the
    grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        rows = ent.next_tier_feature_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_feature_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_catalog_grace_body("features"))


@bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog")
def api_entitlement_previous_tier_feature_catalog():
    """``GET /api/entitlement/previous-tier-feature-catalog`` --
    symmetric downgrade-side companion of
    ``/next-tier-feature-catalog``: the full
    :func:`feature_catalog_at`-shape catalogue for every feature at the
    rung below the resolved entitlement.

    Same envelope as ``/next-tier-feature-catalog``; ``features``
    collapses to ``[]`` at the floor and ``target`` / ``target_label``
    / ``target_rank`` to ``null``.

    Anchored on :meth:`Entitlement.previous_purchasable_tier`
    (source-aware), matching ``/previous-tier-spec`` and
    ``/previous-tier-feature-spec``.

    Never 5xxs: grace-shape envelope on resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        rows = ent.previous_tier_feature_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_feature_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_catalog_grace_body("features"))


@bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog")
def api_entitlement_next_tier_runtime_catalog():
    """``GET /api/entitlement/next-tier-runtime-catalog`` -- runtime-axis
    catalog projection of ``/next-tier-spec``: the full
    :func:`runtime_catalog_at`-shape catalogue for every runtime at the
    rung above the resolved entitlement.

    Current-relative, no-arg sibling of
    ``/api/entitlement/runtime-catalog-at`` and runtime-axis mirror of
    ``/api/entitlement/next-tier-channel-catalog`` /
    ``/next-tier-feature-catalog``. Convenience for
    ``/runtime-catalog-at?tier=<next_purchasable_tier>``.

    Anchored on :meth:`Entitlement.next_purchasable_tier` (source-aware),
    matching ``/next-tier-spec`` and ``/next-tier-runtime-spec``.

    Response shape::

        {
          "current_tier":       "<resolved id>",
          "current_tier_label": ...,
          "current_tier_rank":  <int>,
          "target":             "<next_purchasable_tier id or null>",
          "target_label":       ...,
          "target_rank":        <int or null>,
          "runtimes":           [<catalog_row>, ...],  # empty at ceiling
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    ``runtimes`` is byte-identical to the body of
    ``/runtime-catalog-at?tier=<target>`` -- pinned by a parity test.

    Never 5xxs: grace-shape envelope on resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        rows = ent.next_tier_runtime_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_runtime_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_catalog_grace_body("runtimes"))


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog")
def api_entitlement_previous_tier_runtime_catalog():
    """``GET /api/entitlement/previous-tier-runtime-catalog`` --
    symmetric downgrade-side companion of
    ``/next-tier-runtime-catalog``: the full
    :func:`runtime_catalog_at`-shape catalogue for every runtime at the
    rung below the resolved entitlement.

    Same envelope as ``/next-tier-runtime-catalog``; ``runtimes``
    collapses to ``[]`` at the floor and ``target`` / ``target_label``
    / ``target_rank`` to ``null``.

    Anchored on :meth:`Entitlement.previous_purchasable_tier`
    (source-aware), matching ``/previous-tier-spec`` and
    ``/previous-tier-runtime-spec``.

    Never 5xxs: grace-shape envelope on resolver failure.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        rows = ent.previous_tier_runtime_catalog() or []
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": rows,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_runtime_catalog: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_catalog_grace_body("runtimes"))


def _next_prev_tier_axis_spec_batch_grace_body(axis: str) -> dict:
    """Fallback envelope shared by the four bare next/previous per-axis
    spec-batch routes. Keeps the shape identical to the happy path so a
    resolver failure never breaks a paywall matrix client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        axis: [],
        "unknown": [],
        "grace": True,
        "enforced": False,
    }


@bp_entitlement.route("/api/entitlement/next-tier-feature-spec-batch")
def api_entitlement_next_tier_feature_spec_batch():
    """``GET /api/entitlement/next-tier-feature-spec-batch?features=a,b,c``
    -- current-relative sibling of
    ``/api/entitlement/next-tier-feature-spec-at-batch`` and batch
    sibling of ``/api/entitlement/next-tier-feature-spec``.

    Where ``/next-tier-feature-spec`` projects ONE feature onto the
    rung above the resolved entitlement, this projects N features onto
    that same rung in ONE round-trip. Pairs with
    ``/next-tier-feature-spec`` the same way
    ``/feature-spec-at-batch`` pairs with ``/feature-spec-at``: scalar
    what-if -> batch what-if -- but source-aware (anchored on the
    resolved entitlement's ``next_purchasable_tier``) rather than
    caller-supplied ``tier=``.

    Use case: a pricing-comparison tooltip that walks a fixed column
    of N features and asks "do these unlock at MY next rung?" without
    threading the current tier through the query args or first
    fetching ``/next-tier-feature-spec`` N times.

    Each row in ``features[].row`` is byte-identical to the body of
    ``/next-tier-feature-spec?feature=<id>`` ``.row`` -- pinned by
    parity tests so the scalar and batch accessors cannot drift.
    Supplied feature ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets rows back for the valid ids,
    matching the ``_at`` sibling.

    At the ceiling (resolved entitlement already at enterprise -- no
    rung above) every per-feature ``row`` is ``null`` while
    ``target`` / ``target_label`` / ``target_rank`` collapse to
    ``null``; the surface stays 200 so callers can render "you're at
    the top" copy without a status-code branch.

    Response shape::

        {
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<resolved label>",
          "current_tier_rank":  <resolved rank>,
          "target":             "<next-above tier id>" | null,
          "target_label":       "<next-above label>" | null,
          "target_rank":        <next-above rank> | null,
          "features": [
            {"feature": "<id>", "row": {<feature_spec_at row>} | null},
            ...
          ],
          "unknown": ["bogus_id", ...],
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    - **400** when ``features=`` is missing / empty after normalisation
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with empty rows so the matrix keeps rendering.
    """
    try:
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_feature_spec_batch(features)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_feature_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("features"))


@bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-batch")
def api_entitlement_previous_tier_feature_spec_batch():
    """``GET /api/entitlement/previous-tier-feature-spec-batch
    ?features=a,b,c`` -- symmetric downgrade-side companion of
    ``/next-tier-feature-spec-batch``.

    Same envelope as ``/next-tier-feature-spec-batch``; ``target`` and
    every per-feature ``row`` collapse to ``null`` at the floor
    (resolved entitlement at ``oss`` / ``cloud_free`` -- no rung
    below).

    Each row in ``features[].row`` is byte-identical to
    ``/previous-tier-feature-spec?feature=<id>`` ``.row``.

    - **400** when ``features=`` is missing / empty after normalisation
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    try:
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_feature_spec_batch(features)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_feature_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("features"))


@bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-batch")
def api_entitlement_next_tier_runtime_spec_batch():
    """``GET /api/entitlement/next-tier-runtime-spec-batch?runtimes=a,b,c``
    -- runtime-axis mirror of ``/next-tier-feature-spec-batch`` and
    batch sibling of ``/next-tier-runtime-spec``.

    Aliases are canonicalised the same way ``/next-tier-runtime-spec``
    already does (``claude-code`` -> ``claude_code``), and aliases
    that collapse to a canonical id already in the response are
    silently de-duplicated so the row count matches the unique-
    canonical-id count.

    Each row in ``runtimes[].row`` is byte-identical to the body of
    ``/next-tier-runtime-spec?runtime=<id>`` ``.row``. Unknown ids do
    not 404 the call -- they are echoed in ``unknown[]`` carrying the
    supplied alias so the caller can correlate against what was sent.

    At the ceiling every per-runtime ``row`` is ``null`` while
    ``target`` / ``target_label`` / ``target_rank`` collapse to
    ``null``.

    Response shape mirrors ``/next-tier-feature-spec-batch`` with
    ``"runtimes"`` in place of ``"features"`` and a per-row
    ``"runtime"`` key (canonical id) in place of ``"feature"``.

    - **400** when ``runtimes=`` is missing / empty after normalisation
    - **Never 5xxs**.
    """
    try:
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_runtime_spec_batch(runtimes)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_runtime_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("runtimes"))


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-batch")
def api_entitlement_previous_tier_runtime_spec_batch():
    """``GET /api/entitlement/previous-tier-runtime-spec-batch
    ?runtimes=a,b,c`` -- source-anchored mirror of
    ``/next-tier-runtime-spec-batch`` and batch sibling of
    ``/previous-tier-runtime-spec``.

    Each row in ``runtimes[].row`` is byte-identical to
    ``/previous-tier-runtime-spec?runtime=<id>`` ``.row``. At the
    floor every per-runtime ``row`` is ``null``.

    Response shape, alias handling, validation, and never-5xx posture
    are identical to ``/next-tier-runtime-spec-batch``.
    """
    try:
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_runtime_spec_batch(runtimes)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_runtime_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("runtimes"))


@bp_entitlement.route("/api/entitlement/next-tier-channel-spec-batch")
def api_entitlement_next_tier_channel_spec_batch():
    """``GET /api/entitlement/next-tier-channel-spec-batch?channels=a,b,c``
    -- channel-axis mirror of ``/next-tier-feature-spec-batch`` and
    ``/next-tier-runtime-spec-batch``; batch sibling of
    ``/next-tier-channel-spec``.

    Where ``/next-tier-channel-spec`` projects ONE channel onto the rung
    above the resolved entitlement, this projects N channels onto that
    same rung in ONE round-trip. Pairs with ``/next-tier-channel-spec``
    the same way ``/channel-spec-at-batch`` pairs with
    ``/channel-spec-at``: scalar what-if -> batch what-if -- but source-
    aware (anchored on the resolved entitlement's
    ``next_purchasable_tier``) rather than caller-supplied ``tier=``.

    Use case: an upgrade-preview panel walking a channel picker of N
    chat adapters and asking "do these unlock at MY next rung?" without
    threading the current tier through the query args or first fetching
    ``/next-tier-channel-spec`` N times.

    Each row in ``channels[].row`` is byte-identical to the body of
    ``/next-tier-channel-spec?channel=<id>`` ``.row`` -- pinned by
    parity tests so the scalar and batch accessors cannot drift.
    Supplied channel ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets rows back for the valid ids,
    matching the feature/runtime siblings.

    At the ceiling (resolved entitlement already at enterprise -- no
    rung above) every per-channel ``row`` is ``null`` while ``target``
    / ``target_label`` / ``target_rank`` collapse to ``null``; the
    surface stays 200 so callers can render "you're at the top" copy
    without a status-code branch.

    Every chat channel is FREE at every tier, so whenever ``row`` is
    not ``null`` it comes back ``free=True`` / ``locked=False`` /
    ``entitled=True`` -- pricing tooltips can render "chat channels
    included at every plan" off ONE call.

    Response shape mirrors ``/next-tier-feature-spec-batch`` with
    ``"channels"`` in place of ``"features"`` and a per-row
    ``"channel"`` key in place of ``"feature"``.

    - **400** when ``channels=`` is missing / empty after normalisation
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with empty rows so the matrix keeps rendering.
    """
    try:
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_channel_spec_batch(channels)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_channel_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("channels"))


@bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-batch")
def api_entitlement_previous_tier_channel_spec_batch():
    """``GET /api/entitlement/previous-tier-channel-spec-batch
    ?channels=a,b,c`` -- symmetric downgrade-side companion of
    ``/next-tier-channel-spec-batch``.

    Same envelope as ``/next-tier-channel-spec-batch``; ``target`` and
    every per-channel ``row`` collapse to ``null`` at the floor
    (resolved entitlement at ``oss`` / ``cloud_free`` -- no rung
    below).

    Each row in ``channels[].row`` is byte-identical to
    ``/previous-tier-channel-spec?channel=<id>`` ``.row``.

    The channel-axis always-free invariant holds here too: whenever
    ``row`` is not ``null`` it comes back ``free=True`` /
    ``locked=False`` / ``entitled=True``.

    - **400** when ``channels=`` is missing / empty after normalisation
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    try:
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_channel_spec_batch(channels)
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_channel_spec_batch: error: %s", exc
        )
        return jsonify(_next_prev_tier_axis_spec_batch_grace_body("channels"))


def _next_prev_lock_reason_grace_body(key: str, kind: str) -> dict:
    """Fallback envelope shared by the bare next/previous lock-reason
    routes. Keeps the shape identical to the happy path so a resolver
    failure never breaks a paywall tooltip client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "key": key,
        "kind": kind,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "reason": None,
        "locked": False,
        "allowed": True,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "upgrade_required": False,
        "grace": True,
        "enforced": False,
    }


def _next_prev_lock_reason(direction: str):
    """Shared handler body for ``/{next,previous}-tier-lock-reason``.

    Current-relative sibling of the ``_next_prev_lock_reason_at`` handler
    -- takes no ``tier=`` (the source is the resolved entitlement) and
    walks :meth:`Entitlement.next_tier_lock_reason` /
    :meth:`Entitlement.previous_tier_lock_reason` instead of the source-
    parameterised ``_at`` module helpers, matching the pattern of
    ``/next-tier-feature-spec`` vs ``/next-tier-feature-spec-at``.

    Mirrors the axis-parsing contract of ``/lock-reason`` /
    ``/lock-reason-at`` (exactly one of ``feature=`` / ``runtime=`` /
    ``channels=`` / ``retention_days=`` / ``nodes=``). ``target`` /
    ``reason`` collapse to ``null`` at the rung edge (ceiling for
    ``next``, floor for ``previous``) so the surface stays 200.

    ``direction`` is ``"next"`` or ``"previous"``. Never 5xxs: resolver
    failure short-circuits to the grace-shape envelope so the paywall
    surface stays mute.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason"
    try:
        from clawmetry import entitlements as _ent

        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
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
            bool(runtime_in),
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

        if feature and feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        canonical_rt = None
        if runtime_in:
            canonical_rt = _ent.canonical_runtime(runtime_in)
            if not canonical_rt or canonical_rt not in _ent.ALL_RUNTIMES:
                return (
                    jsonify(
                        {
                            "error": "unknown runtime",
                            "which": "runtime",
                            "runtime": runtime_in,
                        }
                    ),
                    404,
                )

        ent = _ent.get_entitlement()
        if direction == "next":
            target = ent.next_purchasable_tier()
            walk = ent.next_tier_lock_reason
        else:
            target = ent.previous_purchasable_tier()
            walk = ent.previous_tier_lock_reason

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = walk(feature, kind=kind) if target else None
            allowed = reason is None
        elif runtime_in:
            key, kind = canonical_rt, "runtime"
            required = _ent.min_tier_for_runtime(canonical_rt)
            reason = walk(canonical_rt, kind=kind) if target else None
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok and target:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = walk(str(channels_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_channel_count(channels_n)
                    if channels_ok
                    else None
                )
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok and target:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = walk(str(retention_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_retention_window(retention_n)
                    if retention_ok
                    else None
                )
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok and target:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = walk(str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_node_count(nodes_n)
                    if nodes_ok
                    else None
                )
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": cur_rank,
                "key": key,
                "kind": kind,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
        else:
            key, kind = "", ""
        return jsonify(_next_prev_lock_reason_grace_body(key, kind))


@bp_entitlement.route("/api/entitlement/next-tier-lock-reason")
def api_entitlement_next_tier_lock_reason():
    """``GET /api/entitlement/next-tier-lock-reason?<axis>=<id>`` --
    current-relative sibling of ``/api/entitlement/next-tier-lock-reason-at``:
    the lock-reason sentence for one item (interpreted as ``kind``)
    projected onto the rung above the resolved entitlement.

    Lock-reason-axis projection of ``/api/entitlement/next-tier-spec``
    and lock-reason companion of ``/next-tier-feature-spec`` /
    ``/next-tier-runtime-spec``. Where those return the catalog row at
    the rung above, this returns the human-readable lock sentence the
    paywall surface would render there. Lets a paywall "what's the lock
    copy for THIS item at my next rung?" tooltip hydrate off ONE round-
    trip without the caller threading the current tier through query
    args or first fetching ``/lock-reason-at`` at the target rung.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied. Response shape::

        {
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<label>",
          "current_tier_rank":  <rank>,
          "key":                "<id-as-passed | canonical runtime>",
          "kind":               "feature|runtime|channels|retention_days|nodes",
          "target":             "<next-above tier id>" | null,
          "target_label":       "<label>" | null,
          "target_rank":        <rank> | null,
          "reason":             "<lock sentence>" | null,
          "locked":             <bool>,
          "allowed":            <bool>,
          "required_tier":      "<min purchasable tier>" | null,
          "required_tier_label":"<label>" | null,
          "required_tier_rank": <rank>,
          "upgrade_required":   <bool>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    The ``reason`` field matches
    ``/lock-reason-at?tier=<target>&<axis>=<id>`` byte-for-byte when
    ``target`` is populated.

    ``target`` and ``reason`` collapse to ``null`` at the ceiling
    (no rung above); the surface stays 200 with a populated envelope.

    - **400** when no axis is supplied, or when more than one axis is
      supplied
    - **404** when ``feature=`` is unknown or ``runtime=`` is unknown
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    return _next_prev_lock_reason("next")


@bp_entitlement.route("/api/entitlement/previous-tier-lock-reason")
def api_entitlement_previous_tier_lock_reason():
    """``GET /api/entitlement/previous-tier-lock-reason?<axis>=<id>`` --
    symmetric downgrade-side companion of ``/next-tier-lock-reason``:
    the lock-reason sentence for one item projected onto the rung below
    the resolved entitlement.

    Response shape matches ``/next-tier-lock-reason`` byte-for-byte.
    The ``reason`` field matches ``/lock-reason-at?tier=<target>&<axis>=<id>``
    byte-for-byte when ``target`` is populated.

    ``target`` and ``reason`` collapse to ``null`` at the floor
    (resolved entitlement at ``oss`` / ``cloud_free`` -- no rung below).

    - **400** when no axis is supplied, or when more than one axis is
      supplied
    - **404** when ``feature=`` / ``runtime=`` is unknown
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    return _next_prev_lock_reason("previous")


@bp_entitlement.route("/api/entitlement/next-tier-spec-at")
def api_entitlement_next_tier_spec_at():
    """``GET /api/entitlement/next-tier-spec-at?tier=<source>`` -- scalar
    what-if sibling of ``/api/entitlement/next-tier-spec``: full
    :func:`clawmetry.entitlements.tier_spec_at`-shape descriptor of the
    rung above the caller-supplied ``tier``.

    Lets a pricing page render the "full descriptor of the rung above X"
    upgrade-CTA cell for any hypothetical ``X`` without first asking the
    resolver -- the scalar what-if the live ``/next-tier-spec`` endpoint
    surfaces against the resolved entitlement, parameterised over the
    source.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_spec_at row>} | null,
        }

    The inner ``row`` matches the live ``/tier-spec-at?tier=<source>
    &target=<next-above>`` row exactly -- catalogue-derived fields
    (``id``, ``label``, ``is_paid``, ``rank``, ``unlocks_paid_runtimes``,
    ``retention_days``, ``channel_limit``, ``node_limit``, ``features``,
    ``runtimes``) come straight from the static per-tier maps; the
    ``is_current`` boolean is always ``False`` (target is by definition
    strictly above source).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source) -- the surface stays 200 with a populated
    envelope so callers can render "you're at the top" copy without
    a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_spec_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_spec_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-spec-at")
def api_entitlement_previous_tier_spec_at():
    """``GET /api/entitlement/previous-tier-spec-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/previous-tier-spec``:
    full :func:`clawmetry.entitlements.tier_spec_at`-shape descriptor of
    the rung below the caller-supplied ``tier``.

    Source-anchored mirror of ``/next-tier-spec-at`` and downgrade-side
    counterpart of the live ``/previous-tier-spec`` (source pinned to
    the resolver). Lets a pricing page render the "full descriptor of
    the rung below X" downgrade-confirmation detail cell for any
    hypothetical ``X`` without asking the resolver.

    Response shape matches ``/next-tier-spec-at`` byte-for-byte
    (``tier``, ``tier_label``, ``tier_rank``, ``target``, ``target_label``,
    ``target_rank``, ``row``). Inner ``row`` matches
    ``/tier-spec-at?tier=<source>&target=<previous-below>`` exactly; the
    ``is_current`` boolean is always ``False`` (target is by definition
    strictly below source).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor
    (no rung strictly below the source -- ``oss`` / ``cloud_free`` as
    source) -- the surface stays 200 with a populated envelope so
    callers can render "you're at the floor" copy without a status-
    code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_spec_at(tier_in)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_spec_at: error: %s", exc)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-spec-at-batch")
def api_entitlement_next_tier_spec_at_batch():
    """``GET /api/entitlement/next-tier-spec-at-batch`` -- batch sibling
    of ``/api/entitlement/next-tier-spec-at``: one ``next-tier-spec-at``
    envelope per purchasable source tier, in one round-trip.

    Spec-shaped sibling of ``/api/entitlement/next-tier-diff-at-batch``,
    ``/next-tier-unlocks-at-batch``, ``/next-tier-locks-at-batch``, and
    ``/next-tier-capacity-diff-at-batch``. Lets a pricing-comparison
    matrix UI render the "full descriptor of the rung above each rung"
    upgrade-CTA column off **one** call instead of N calls to
    ``/next-tier-spec-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint
    and the sibling diff / unlocks / locks / capacity ``_at_batch``
    endpoints, so the five batches fold into the same pricing-page
    table byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-spec-at?tier=<source>`` for that
    source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the :func:`tier_spec_at` row pinned on both
    endpoints; ``is_current`` is always ``False`` on populated rows
    (target is strictly above source). At the source-side ceiling
    (``enterprise`` as source) the envelope carries ``target=null``
    and ``row=null`` rather than being dropped.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_spec_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-spec-at-batch")
def api_entitlement_previous_tier_spec_at_batch():
    """``GET /api/entitlement/previous-tier-spec-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-spec-at``: one
    ``previous-tier-spec-at`` envelope per purchasable source tier, in
    one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-spec-at-batch`` and spec-shaped
    sibling of ``/previous-tier-diff-at-batch``,
    ``/previous-tier-unlocks-at-batch``,
    ``/previous-tier-locks-at-batch``, and
    ``/previous-tier-capacity-diff-at-batch``. Lets a pricing-
    comparison matrix UI render the "full descriptor of the rung below
    each rung" downgrade-confirmation column off **one** call instead
    of N calls to ``/previous-tier-spec-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the sibling ``_at_batch`` endpoints, so
    the five batches fold into the same pricing-page table byte-for-
    byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/previous-tier-spec-at?tier=<source>`` for that
    source exactly. The ``row`` carries the :func:`tier_spec_at` row
    pinned on both endpoints; ``is_current`` is always ``False`` on
    populated rows (target is strictly below source). At the
    source-side floor (``oss`` / ``cloud_free`` as source) the
    envelope carries ``target=null`` and ``row=null`` rather than
    being dropped.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_spec_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_spec_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-spec-path")
def api_entitlement_tier_spec_path():
    """``GET /api/entitlement/tier-spec-path?from=<id>&to=<id>`` --
    arbitrary-endpoint stepwise spec-shaped path between any two
    tiers; the spec-shaped sibling of ``/tier-path`` (full
    ``tier_diff`` per rung), ``/capacity-diff-path`` (capacity-only per
    rung), ``/tier-unlocks-path`` (marginal grants per rung),
    ``/tier-locks-path`` (marginal losses per rung) and
    ``/preview-path`` (cumulative ``Entitlement.to_dict`` per rung) --
    the spec-shaped member of the ``_path`` family, the path-shaped
    sibling of ``/tier-spec-at-batch`` and the bulk what-if cousin of
    ``/tier-spec-at``. Lets a pricing-comparison "compare A vs B"
    surface render the slim catalogue-shaped descriptor (``label``,
    ``is_paid``, ``unlocks_paid_runtimes``, ``retention_days``,
    ``channel_limit``, ``node_limit``, ``features``, ``runtimes``) at
    every rung between any two tiers off ONE round-trip, without
    folding marketing fields back in from a separate
    ``/tier-catalog`` lookup the way a ``/preview-path`` row forces.

    Each row in ``path`` matches the ``/tier-spec-at?tier=<from>&target=<rung>``
    payload exactly -- the same key set with ``is_current=False`` on
    every walked rung (``from`` is excluded from the walked rungs) --
    so a UI that already renders ``/tier-spec-at`` needs zero new
    shape code to render a per-rung row off this path. Rung walk is
    byte-stable against ``/tier-path``, ``/capacity-diff-path``,
    ``/tier-unlocks-path``, ``/tier-locks-path`` and ``/preview-path``
    (same ``_PURCHASABLE_TIERS`` filter + same sort + same
    destination-sibling exclusion), so the six paths line up rung-for-
    rung.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<tier-spec-at row>, ...],
        }

    Direction semantics:

    * ``upgrade`` (ascending) -- rows climb cumulatively rung by rung
      from the rung above ``from`` toward ``to``.
    * ``downgrade`` (descending) -- rows shrink cumulatively rung by
      rung; the cancellation-walkthrough counterpart.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the cumulative spec at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Same-rank siblings strictly between the endpoints are both
    included; same-rank siblings of the destination are excluded so
    the path terminates exactly at ``to``. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial``
    IS accepted as an endpoint -- it is excluded from the walked
    intermediate rungs (not purchasable) but is a valid endpoint via
    the lateral branch. Never 5xxs: a resolver failure short-circuits
    to ``404`` so a pricing-comparison surface keeps rendering
    instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_spec_path(f, t)
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
        logger.warning("api_entitlement_tier_spec_path: error: %s", exc)
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/feature-spec-path")
def api_entitlement_feature_spec_path():
    """``GET /api/entitlement/feature-spec-path?from=<id>&to=<id>&feature=<id>``

    Arbitrary-endpoint stepwise single-feature spec path between any two
    tiers; the single-feature sibling of ``/tier-spec-path`` (full slim
    spec per rung) and the perspective-walked sibling of
    ``/feature-spec-at``. Lets a paywall surface render every rung's
    ``allowed`` / ``locked`` / ``entitled`` status for a SINGLE feature
    off ONE round-trip without fetching the full
    ``/feature-catalog-at`` at every rung.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``,
    ``/tier-locks-path``, ``/preview-path`` and ``/tier-spec-path``
    (same ``_PURCHASABLE_TIERS`` filter + same sort + same destination-
    sibling exclusion), so the seven paths line up rung-for-rung.

    Each row in ``path`` is the ``/feature-spec-at?tier=<rung>&feature=<feature>``
    body augmented with three rung-identification keys -- ``rung``,
    ``rung_label``, ``rung_rank`` -- naming the perspective tier the
    row was computed at. Dropping the three ``rung*`` keys yields exact
    byte-equality with ``/feature-spec-at?tier=<rung>&feature=<feature>``
    (a parity test pins this).

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "feature":    "<feature id>",
          "path":       [<augmented feature-spec-at row>, ...],
        }

    Direction semantics:

    * ``upgrade`` (ascending) -- rows climb rung by rung from the rung
      above ``from`` toward ``to``.
    * ``downgrade`` (descending) -- rows shrink rung by rung.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the spec at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Same-rank siblings strictly between the endpoints are both included;
    same-rank siblings of the destination are excluded so the path
    terminates exactly at ``to``. ``400`` when ``from=``, ``to=`` or
    ``feature=`` is missing; ``404`` when any id is unknown. ``trial``
    IS accepted as an endpoint -- it is excluded from the walked
    intermediate rungs (not purchasable) but is a valid endpoint via
    the lateral branch. Never 5xxs: a resolver failure short-circuits
    to ``404`` so a paywall surface keeps rendering instead of
    breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    feat = (request.args.get("feature") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    if not feat:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.feature_spec_path(f, t, feat)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier or feature",
                        "from": f,
                        "to": t,
                        "feature": feat,
                    }
                ),
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
                "feature": feat,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec_path: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "unknown tier or feature",
                    "from": f,
                    "to": t,
                    "feature": feat,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-path")
def api_entitlement_runtime_spec_path():
    """``GET /api/entitlement/runtime-spec-path?from=<id>&to=<id>&runtime=<id>``

    Runtime-axis twin of ``/feature-spec-path`` -- the single-runtime
    sibling of ``/tier-spec-path`` and perspective-walked sibling of
    ``/runtime-spec-at``. Lets a paywall surface render every rung's
    ``allowed`` / ``locked`` / ``entitled`` status for a SINGLE runtime
    off ONE round-trip without fetching the full
    ``/runtime-catalog-at`` at every rung.

    Accepts runtime aliases (``claude-code`` -> ``claude_code``) via
    :func:`clawmetry.entitlements.canonical_runtime` so the URL surface
    matches what callers already pass to
    ``/api/entitlement/required-tier``.

    Rung walk is byte-stable against the other ``_path`` helpers. Each
    row in ``path`` is the ``/runtime-spec-at?tier=<rung>&runtime=<runtime>``
    body augmented with the ``rung`` / ``rung_label`` / ``rung_rank``
    keys; dropping the three ``rung*`` keys yields exact byte-equality
    with the singular ``/runtime-spec-at`` (a parity test pins this).

    Response shape mirrors ``/feature-spec-path`` with ``"runtime"`` in
    place of ``"feature"`` in the envelope.

    ``400`` when ``from=``, ``to=`` or ``runtime=`` is missing; ``404``
    when any id is unknown. Never 5xxs.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    rt_raw = (request.args.get("runtime") or "").strip()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    if not rt_raw:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(rt_raw)
        path = _ent.runtime_spec_path(f, t, rt_raw)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier or runtime",
                        "from": f,
                        "to": t,
                        "runtime": rt or rt_raw.lower(),
                    }
                ),
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
                "runtime": rt or rt_raw.lower(),
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec_path: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "unknown tier or runtime",
                    "from": f,
                    "to": t,
                    "runtime": rt_raw.lower(),
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/feature-catalog-path")
def api_entitlement_feature_catalog_path():
    """``GET /api/entitlement/feature-catalog-path?from=<id>&to=<id>`` --
    arbitrary-endpoint stepwise feature-catalog path between any two
    tiers; the full-catalog sibling of ``/feature-spec-path`` (single
    feature per rung), the path-shaped sibling of
    ``/feature-catalog-at-batch`` (multi-source what-if matrix) and the
    bulk what-if cousin of ``/feature-catalog-at``. Lets an upgrade-
    walkthrough UI render the full feature catalogue at every rung
    between any two tiers off ONE round-trip, without first calling
    ``/tier-path`` for the rung list and then N calls to
    ``/feature-catalog-at``.

    Each row in ``path`` mirrors the ``/feature-catalog-at-batch`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``features``); the
    ``features`` list byte-equals ``/feature-catalog-at?tier=<rung>``
    for the same rung -- pinned by the parity tests so the scalar,
    batch and path what-if catalog surfaces cannot drift.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``, ``/tier-locks-path``,
    ``/preview-path``, ``/tier-spec-path``, ``/feature-spec-path`` and
    ``/runtime-spec-path`` (same ``_PURCHASABLE_TIERS`` filter + same
    sort + same destination-sibling exclusion), so the paths line up
    rung-for-rung.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<feature-catalog-at-batch row>, ...],
        }

    Direction semantics:

    * ``upgrade`` (ascending) -- rows climb cumulatively rung by rung
      from the rung above ``from`` toward ``to``.
    * ``downgrade`` (descending) -- rows shrink cumulatively rung by
      rung; the cancellation-walkthrough counterpart.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the catalog at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Same-rank siblings strictly between the endpoints are both
    included; same-rank siblings of the destination are excluded so
    the path terminates exactly at ``to``. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial``
    IS accepted as an endpoint -- excluded from the walked intermediate
    rungs (not purchasable) but valid via the lateral branch. Never
    5xxs: a resolver failure short-circuits to ``404`` so a pricing-
    page surface keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.feature_catalog_path(f, t)
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
        logger.warning(
            "api_entitlement_feature_catalog_path: error: %s", exc
        )
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog-path")
def api_entitlement_runtime_catalog_path():
    """``GET /api/entitlement/runtime-catalog-path?from=<id>&to=<id>`` --
    runtime-axis twin of ``/feature-catalog-path``: full runtime
    catalogue at every rung between any two tiers off ONE round-trip.

    Pairs with ``/feature-catalog-path`` the same way
    ``/runtime-catalog-at-batch`` pairs with
    ``/feature-catalog-at-batch``. Together the two path endpoints let
    an upgrade-walkthrough UI render every feature + runtime column at
    every rung off TWO calls instead of first calling ``/tier-path``
    and then 2 * N calls to the scalar what-if catalog endpoints.

    Each row in ``path`` mirrors the ``/runtime-catalog-at-batch`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``runtimes``); the
    ``runtimes`` list byte-equals ``/runtime-catalog-at?tier=<rung>``
    for the same rung -- pinned by the parity tests.

    Rung walk, direction semantics and error posture match
    ``/feature-catalog-path`` (byte-stable against the rest of the
    ``_path`` family). Never 5xxs.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.runtime_catalog_path(f, t)
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
        logger.warning(
            "api_entitlement_runtime_catalog_path: error: %s", exc
        )
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/channel-catalog-path")
def api_entitlement_channel_catalog_path():
    """``GET /api/entitlement/channel-catalog-path?from=<id>&to=<id>`` --
    channel-axis twin of ``/feature-catalog-path`` and
    ``/runtime-catalog-path``: the full chat-channel catalogue at every
    rung between any two tiers off ONE round-trip.

    Pairs with ``/feature-catalog-path`` and ``/runtime-catalog-path``
    the same way ``/channel-catalog`` pairs with ``/feature-catalog``
    and ``/runtime-catalog``. Together the three ``_catalog_path``
    endpoints let an upgrade-walkthrough UI render every feature +
    runtime + channel column at every rung off THREE calls instead of
    first calling ``/tier-path`` and then N * 3 calls to the scalar
    catalog endpoints.

    Each row in ``path`` mirrors the ``/feature-catalog-path`` /
    ``/runtime-catalog-path`` row shape with ``features`` / ``runtimes``
    renamed to ``channels`` (``tier``, ``tier_label``, ``tier_rank``,
    ``channels``); the ``channels`` list byte-equals
    ``/channel-catalog`` for every rung -- pinned by the parity tests
    (every chat-channel adapter is FREE at every tier, so the catalogue
    is invariant across the rung walk).

    Rung walk, direction semantics and error posture match
    ``/feature-catalog-path`` (byte-stable against the rest of the
    ``_path`` family). Never 5xxs: a resolver failure short-circuits to
    ``404`` so a pricing-page surface keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.channel_catalog_path(f, t)
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
        logger.warning(
            "api_entitlement_channel_catalog_path: error: %s", exc
        )
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/channel-spec-path")
def api_entitlement_channel_spec_path():
    """``GET /api/entitlement/channel-spec-path?from=<id>&to=<id>&channel=<id>``

    Channel-axis twin of ``/feature-spec-path`` and
    ``/runtime-spec-path`` -- the single-channel sibling of
    ``/channel-catalog-path`` and perspective-walked sibling of
    ``/channel-spec``. Lets a paywall / channel-picker "how does THIS
    one channel look as I climb the ladder" UI render every rung's
    ``allowed`` / ``locked`` / ``entitled`` status off ONE round-trip
    without fetching the full ``/channel-catalog-path`` payload and
    filtering client-side.

    Rung walk is byte-stable against ``/tier-path``,
    ``/tier-spec-path``, ``/feature-spec-path``, ``/runtime-spec-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``,
    ``/tier-locks-path``, ``/preview-path`` and
    ``/channel-catalog-path`` (same ``_PURCHASABLE_TIERS`` filter + same
    sort + same destination-sibling exclusion).

    Each row in ``path`` mirrors the ``/feature-spec-path`` /
    ``/runtime-spec-path`` row shape with the singular ``feature`` /
    ``runtime`` body replaced by the ``/channel-spec`` body (``id``,
    ``label``, ``free``, ``tier``, ``allowed``, ``locked``,
    ``entitled``) augmented with three rung-identification keys --
    ``rung``, ``rung_label``, ``rung_rank`` -- naming the perspective
    tier the row was computed at. Dropping the three ``rung*`` keys
    yields exact byte-equality with the LIVE ``/channel-spec?channel=<id>``
    row (every chat-channel adapter is FREE at every tier, so the row
    is invariant across the rung walk). Parity tests pin this.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "channel":    "<channel id>",
          "path":       [<augmented channel-spec row>, ...],
        }

    Direction semantics mirror ``/feature-spec-path``:

    * ``upgrade`` (ascending) -- rows climb rung by rung from the rung
      above ``from`` toward ``to``.
    * ``downgrade`` (descending) -- rows shrink rung by rung.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the spec at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    ``400`` when ``from=``, ``to=`` or ``channel=`` is missing; ``404``
    when any id is unknown -- ``which`` echoes ``tier`` or ``channel`` so
    the caller can render the right "unknown ..." message. ``trial`` IS
    accepted as an endpoint -- excluded from the walked intermediate
    rungs (not purchasable) but a valid endpoint via the lateral branch.
    Never 5xxs: a resolver failure short-circuits to ``404`` so a
    paywall surface keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    ch = (request.args.get("channel") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    if not ch:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.channel_spec_path(f, t, ch)
        if path is None:
            if f not in _ent._TIER_FEATURES or t not in _ent._TIER_FEATURES:
                which = "tier"
            else:
                which = "channel"
            return (
                jsonify(
                    {
                        "error": f"unknown {which}",
                        "which": which,
                        "from": f,
                        "to": t,
                        "channel": ch,
                    }
                ),
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
                "channel": ch,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_spec_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier or channel",
                    "from": f,
                    "to": t,
                    "channel": ch,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/channel-spec-at-path")
def api_entitlement_channel_spec_at_path():
    """``GET /api/entitlement/channel-spec-at-path?tier=<perspective>
    &from=<id>&to=<id>&channel=<id>`` -- perspective-validated what-if
    sibling of ``/api/entitlement/channel-spec-path``.

    Channel-axis twin of ``/feature-spec-at-path`` /
    ``/runtime-spec-at-path``; fills the ``_at_path`` slot of the
    ``channel-spec`` family alongside ``/channel-spec`` (scalar
    current), ``/channel-spec-at`` (scalar what-if),
    ``/channel-spec-batch`` (batch current),
    ``/channel-spec-at-batch`` (batch what-if), and
    ``/channel-spec-path`` (path current). The perspective is validated
    (400 on missing, 404 on unknown) but does NOT shape the ``path``
    rows -- the body is byte-identical to
    ``/channel-spec-path?from=<from>&to=<to>&channel=<channel>`` for
    every perspective. Pinned by parity tests so the ``_at_path`` and
    ``_path`` endpoints cannot drift.

    Response shape (mirrors ``/channel-spec-path`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-
    context tail so a paywall matrix UI can render "at Cloud Pro this
    channel is free at every rung" without a second call to
    ``/entitlement``)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "channel":               "<channel id>",
          "path":                  [<channel_spec_path row>, ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` or ``channel=`` is
      missing / blank
    - **404** when any id is unknown (body carries
      ``which: "tier" | "from" | "to" | "channel"`` so the caller can
      point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with the perspective echoed so the UI keeps
      rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    ch = (request.args.get("channel") or "").strip().lower()
    if not ch:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        if ch not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": ch,
                    }
                ),
                404,
            )
        path = _ent.channel_spec_at_path(tier_in, f, t, ch)
        if path is None:
            path = []
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "channel": ch,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_channel_spec_at_path: error: %s", exc)
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "channel": ch,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-spec-at-path-batch")
def api_entitlement_channel_spec_at_path_batch():
    """``GET /api/entitlement/channel-spec-at-path-batch?tier=<perspective>
    &from=<id>&to=<id>&channels=a,b,c`` -- perspective-validated what-if
    batch sibling of ``/api/entitlement/channel-spec-path-batch``.

    Fills the ``_at_path_batch`` slot of the ``channel-spec`` family;
    fixed-perspective, fixed-from, fixed-to, multi-channel companion of
    ``/channel-spec-at-path``. Channel-axis twin of
    ``/feature-spec-at-path-batch`` and ``/runtime-spec-at-path-batch``.
    Per-channel body byte-identical to ``/channel-spec-path-batch`` for
    the same ``(from, to, channels)`` triple -- scalar / batch no-drift
    contract, pinned by parity tests.

    Response shape (mirrors ``/channel-spec-path-batch`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "channels": [
            {"channel": "<id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` is missing / blank, or
      ``channels=`` is missing / empty after normalisation
    - **404** when any tier id is unknown (body carries
      ``which: "tier" | "from" | "to"``)
    - Unknown channel ids do NOT 404 the call -- they are echoed in
      ``unknown[]`` so a partially-bad caller still gets paths back for
      the valid ids alongside a list of what was dropped, matching
      every other ``*_path_batch`` sibling's posture.
    - **Never 5xxs**: a synthesis failure short-circuits to a grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        batch = _ent.channel_spec_at_path_batch(tier_in, f, t, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_spec_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "channels": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-spec-path-batch")
def api_entitlement_channel_spec_path_batch():
    """``GET /api/entitlement/channel-spec-path-batch?from=<id>&to=<id>
    &channels=a,b,c`` -- batch sibling of
    ``/api/entitlement/channel-spec-path``.

    Where ``/channel-spec-path`` walks ONE channel across the rungs
    between two tiers, this walks N channels across the same rungs in
    ONE round-trip. Channel-axis twin of ``/feature-spec-path-batch``
    and ``/runtime-spec-path-batch``. Pairs with ``/channel-spec-path``
    the same way ``/feature-spec-path-batch`` pairs with
    ``/feature-spec-path``: scalar -> matrix in one call.

    Use case: a paywall / channel-picker "compare A vs B, here are the
    6 channels I care about" surface hydrates every rung for every
    channel off ONE call instead of N calls to ``/channel-spec-path``.
    Rung walk is channel-agnostic (every chat-channel adapter is FREE
    at every tier), so all per-channel paths share the same length and
    rung sequence -- the client can render the matrix as
    rows = channels x cols = rungs without re-deriving the column
    headers per channel.

    Each row in ``channels[].path`` is byte-identical to a row from
    ``/channel-spec-path?from=<from>&to=<to>&channel=<id>`` -- pinned
    by the parity tests so the scalar and batch path accessors cannot
    drift. Supplied channel ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "channels": [
            {"channel": "<id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=``, ``to=`` is missing / blank, or ``channels=``
      is missing / empty after normalisation
    - **404** when ``from`` or ``to`` is unknown (body carries
      ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        if t not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        batch = _ent.channel_spec_path_batch(f, t, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
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
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_spec_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "channels": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/tier-catalog-path")
def api_entitlement_tier_catalog_path():
    """``GET /api/entitlement/tier-catalog-path?from=<id>&to=<id>`` --
    tier-axis twin of ``/feature-catalog-path`` and
    ``/runtime-catalog-path``: the FULL tier ladder at every rung
    between any two tiers off ONE round-trip, with each rung's inner
    ``tiers`` list carrying the ladder from the perspective of that
    rung (``is_current`` pinned on the rung id).

    Pairs with the two sibling ``_catalog_path`` endpoints the same
    way ``/tier-catalog-at`` pairs with ``/feature-catalog-at`` /
    ``/runtime-catalog-at``. Together the three ``_catalog_path``
    endpoints let an upgrade-walkthrough UI render every tier +
    feature + runtime column at every rung off THREE calls instead
    of first calling ``/tier-path`` and then 3 * N calls to the
    scalar what-if catalog endpoints.

    Each row in ``path`` mirrors the ``/feature-catalog-path`` /
    ``/runtime-catalog-path`` row shape with ``features`` /
    ``runtimes`` renamed to ``tiers`` (``tier``, ``tier_label``,
    ``tier_rank``, ``tiers``); the inner ``tiers`` list byte-equals
    ``/tier-catalog-at?tier=<rung>`` for the same rung -- pinned by
    the parity tests so the scalar and path what-if tier-ladder
    surfaces cannot drift.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "path":       [<per-rung row>, ...],
        }

    Rung walk, direction semantics and error posture match
    ``/feature-catalog-path`` (byte-stable against the rest of the
    ``_path`` family). ``400`` when ``from=`` or ``to=`` is missing;
    ``404`` when either id is unknown. ``trial`` IS accepted as an
    endpoint -- excluded from the walked intermediate rungs (not
    purchasable) but valid via the lateral branch. Never 5xxs: a
    resolver failure short-circuits to ``404`` so a pricing-page
    surface keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_catalog_path(f, t)
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
        logger.warning(
            "api_entitlement_tier_catalog_path: error: %s", exc
        )
        return (
            jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )


@bp_entitlement.route("/api/entitlement/lock-reason-path")
def api_entitlement_lock_reason_path():
    """``GET /api/entitlement/lock-reason-path?from=<id>&to=<id>&<axis>=<id>``

    Arbitrary-endpoint stepwise lock-row path between any two tiers; the
    lock-row analogue of ``/feature-spec-path`` / ``/runtime-spec-path``
    and the path-walking sibling of ``/lock-reason-at``. Lets a paywall
    surface render every rung's ``locked`` / ``allowed`` / ``reason``
    sentence for a SINGLE item off ONE round-trip without fetching the
    full ``/lock-reasons-at-batch`` payload at every rung.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied -- the same axis
    dispatcher as ``/lock-reason`` and ``/lock-reason-at``.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``,
    ``/tier-locks-path``, ``/preview-path``, ``/tier-spec-path``,
    ``/feature-spec-path`` and ``/runtime-spec-path`` (same
    ``_PURCHASABLE_TIERS`` filter + same sort + same destination-sibling
    exclusion), so the nine paths line up rung-for-rung.

    Each row in ``path`` is the same 8-key lock-row shape ``/lock-reason``
    / ``/lock-reason-at`` / ``/lock-reasons-at-batch`` already emit
    (``key``, ``kind``, ``reason``, ``locked``, ``allowed``,
    ``required_tier``, ``required_tier_label``, ``required_tier_rank``)
    augmented with three rung-identification keys -- ``rung``,
    ``rung_label``, ``rung_rank`` -- naming the perspective tier the row
    was computed at. Dropping the three ``rung*`` keys yields exact
    byte-equality with the corresponding axis row of
    ``/lock-reasons-at-batch?perspective_tier=<rung>``.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "key":        "<echoed item id>",
          "kind":       "feature" | "runtime" | "channels" |
                        "retention_days" | "nodes",
          "path":       [<rung-augmented lock-row>, ...],
        }

    Direction semantics mirror ``/feature-spec-path``:

    * ``upgrade`` (ascending) -- rows climb rung by rung from the rung
      above ``from`` toward ``to``.
    * ``downgrade`` (descending) -- rows shrink rung by rung.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the lock-row at ``to``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Runtime ids accept aliases (``claude-code`` -> ``claude_code``) via
    :func:`clawmetry.entitlements.canonical_runtime` so the URL surface
    matches ``/api/entitlement/required-tier``.

    ``400`` when ``from=`` / ``to=`` is missing, when no axis is
    supplied, or when more than one axis is supplied. ``404`` when any
    tier id is unknown, when a feature/runtime id is unknown, or when a
    capacity value is missing / non-int / non-positive (the helper
    short-circuits to ``None``). ``trial`` IS accepted as an endpoint --
    it is excluded from the walked intermediate rungs (not purchasable)
    but is a valid endpoint via the lateral branch. Never 5xxs: a
    resolver failure short-circuits to ``404`` so a paywall surface
    keeps rendering instead of breaking.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400

    feature = (request.args.get("feature") or "").strip().lower()
    runtime_in = (request.args.get("runtime") or "").strip().lower()
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
        bool(runtime_in),
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

    try:
        from clawmetry import entitlements as _ent

        if feature:
            item, kind, echoed_key = feature, "feature", feature
        elif runtime_in:
            canon = _ent.canonical_runtime(runtime_in)
            item, kind, echoed_key = (
                canon or runtime_in,
                "runtime",
                canon or runtime_in,
            )
        elif channels_present:
            if not channels_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "from": f,
                            "to": t,
                            "key": channels_raw,
                            "kind": "channels",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = str(channels_n), "channels", str(channels_n)
        elif retention_present:
            if not retention_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "from": f,
                            "to": t,
                            "key": retention_raw,
                            "kind": "retention_days",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = (
                str(retention_n),
                "retention_days",
                str(retention_n),
            )
        else:
            if not nodes_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "from": f,
                            "to": t,
                            "key": nodes_raw,
                            "kind": "nodes",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = str(nodes_n), "nodes", str(nodes_n)

        path = _ent.lock_reason_path(f, t, item, kind=kind)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier or item",
                        "from": f,
                        "to": t,
                        "key": echoed_key,
                        "kind": kind,
                    }
                ),
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
                "key": echoed_key,
                "kind": kind,
                "path": path,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason_path: error: %s", exc)
        if feature:
            echoed_key, kind = feature, "feature"
        elif runtime_in:
            echoed_key, kind = runtime_in, "runtime"
        elif channels_present:
            echoed_key, kind = channels_raw, "channels"
        elif retention_present:
            echoed_key, kind = retention_raw, "retention_days"
        else:
            echoed_key, kind = nodes_raw, "nodes"
        return (
            jsonify(
                {
                    "error": "unknown tier or item",
                    "from": f,
                    "to": t,
                    "key": echoed_key,
                    "kind": kind,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/next-tier-feature-spec-at")
def api_entitlement_next_tier_feature_spec_at():
    """``GET /api/entitlement/next-tier-feature-spec-at?tier=<source>&feature=<id>``
    -- scalar what-if sibling of ``/api/entitlement/next-tier-spec-at``
    projected onto a SINGLE feature: the
    :func:`clawmetry.entitlements.feature_spec_at`-shape catalogue row for
    ``feature`` evaluated on the rung above the caller-supplied ``tier``.

    Feature-axis projection of ``/next-tier-spec-at`` (full tier-row
    descriptor of the rung above the source) and feature-side mirror of
    ``/next-tier-runtime-spec-at``. Lets a paywall "does THIS feature
    unlock at my next rung?" tooltip hydrate off ONE round-trip instead
    of fetching the full ``/feature-catalog-at`` at the next rung and
    filtering client-side.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "feature":        "<feature id>",
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<feature_spec_at row>} | null,
        }

    The inner ``row`` matches
    ``/feature-spec-at?tier=<target>&feature=<feature>`` byte-for-byte
    when ``target`` is populated -- a parity test pins this so the
    projection cannot drift from the full-row sibling.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the ceiling
    (no rung strictly above the source -- enterprise as source) -- the
    surface stays 200 with a populated envelope so callers can render
    "you're at the top" copy without a status-code branch.

    - **400** when ``tier=`` or ``feature=`` is missing / blank
    - **404** when ``tier`` is unknown or ``feature`` is unknown (not in
      :data:`ALL_FEATURES`). The body carries ``which`` so a caller can
      render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope so the paywall surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_feature = request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_feature_spec_at(tier_in, feature)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "feature": feature,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_feature_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "feature": feature,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-at")
def api_entitlement_previous_tier_feature_spec_at():
    """``GET /api/entitlement/previous-tier-feature-spec-at?tier=<source>&feature=<id>``
    -- scalar what-if sibling of
    ``/api/entitlement/previous-tier-spec-at`` projected onto a SINGLE
    feature: the :func:`clawmetry.entitlements.feature_spec_at`-shape
    catalogue row for ``feature`` evaluated on the rung below the
    caller-supplied ``tier``.

    Source-anchored mirror of ``/next-tier-feature-spec-at`` and
    downgrade-confirmation counterpart on the feature axis. Lets a
    downgrade-confirmation card render "does THIS feature still unlock
    one rung down?" without re-walking the catalogue.

    Response shape matches ``/next-tier-feature-spec-at`` byte-for-byte
    (``tier``, ``tier_label``, ``tier_rank``, ``feature``, ``target``,
    ``target_label``, ``target_rank``, ``row``). Inner ``row`` matches
    ``/feature-spec-at?tier=<target>&feature=<feature>`` byte-for-byte
    when ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor
    (``oss`` / ``cloud_free`` as source).

    - **400** when ``tier=`` or ``feature=`` is missing / blank
    - **404** when ``tier`` is unknown or ``feature`` is unknown.
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_feature = request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_feature_spec_at(tier_in, feature)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "feature": feature,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_feature_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "feature": feature,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-at")
def api_entitlement_next_tier_runtime_spec_at():
    """``GET /api/entitlement/next-tier-runtime-spec-at?tier=<source>&runtime=<id>``
    -- scalar what-if sibling of ``/api/entitlement/next-tier-spec-at``
    projected onto a SINGLE runtime: the
    :func:`clawmetry.entitlements.runtime_spec_at`-shape catalogue row
    for ``runtime`` evaluated on the rung above the caller-supplied
    ``tier``.

    Runtime-axis projection of ``/next-tier-spec-at`` (full tier-row
    descriptor of the rung above the source) and runtime-side mirror of
    ``/next-tier-feature-spec-at``. Accepts aliases (``claude-code`` ->
    ``claude_code``) via :func:`entitlements.canonical_runtime` so the
    URL surface matches what callers already pass to
    ``/api/entitlement/required-tier`` and ``/runtime-spec-at``.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "runtime":        "<canonical runtime id>",
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<runtime_spec_at row>} | null,
        }

    The inner ``row`` matches
    ``/runtime-spec-at?tier=<target>&runtime=<runtime>`` byte-for-byte
    when ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the
    ceiling.

    - **400** when ``tier=`` or ``runtime=`` is missing / blank
    - **404** when ``tier`` is unknown or ``runtime`` (after alias
      canonicalisation) is unknown (not in :data:`ALL_RUNTIMES`).
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_runtime = request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": runtime_in,
                    }
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_runtime_spec_at(tier_in, rt)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "runtime": rt,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_runtime_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "runtime": runtime_in,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-at")
def api_entitlement_previous_tier_runtime_spec_at():
    """``GET /api/entitlement/previous-tier-runtime-spec-at?tier=<source>&runtime=<id>``
    -- scalar what-if sibling of
    ``/api/entitlement/previous-tier-spec-at`` projected onto a SINGLE
    runtime: the :func:`clawmetry.entitlements.runtime_spec_at`-shape
    catalogue row for ``runtime`` evaluated on the rung below the
    caller-supplied ``tier``.

    Source-anchored mirror of ``/next-tier-runtime-spec-at`` and
    downgrade-confirmation counterpart on the runtime axis. Accepts
    aliases (``claude-code`` -> ``claude_code``) via
    :func:`entitlements.canonical_runtime`.

    Response shape matches ``/next-tier-runtime-spec-at`` byte-for-byte
    (``tier``, ``tier_label``, ``tier_rank``, ``runtime``, ``target``,
    ``target_label``, ``target_rank``, ``row``). Inner ``row`` matches
    ``/runtime-spec-at?tier=<target>&runtime=<runtime>`` byte-for-byte
    when ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor.

    - **400** when ``tier=`` or ``runtime=`` is missing / blank
    - **404** when ``tier`` is unknown or ``runtime`` is unknown.
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_runtime = request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": runtime_in,
                    }
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_runtime_spec_at(tier_in, rt)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "runtime": rt,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_runtime_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "runtime": runtime_in,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-channel-spec-at")
def api_entitlement_next_tier_channel_spec_at():
    """``GET /api/entitlement/next-tier-channel-spec-at?tier=<source>&channel=<id>``
    -- scalar what-if sibling of ``/api/entitlement/next-tier-spec-at``
    projected onto a SINGLE chat channel: the
    :func:`clawmetry.entitlements.channel_spec_at`-shape catalogue row
    for ``channel`` evaluated on the rung above the caller-supplied
    ``tier``.

    Channel-axis projection of ``/next-tier-spec-at`` (full tier-row
    descriptor of the rung above the source) and channel-side mirror of
    ``/next-tier-feature-spec-at`` / ``/next-tier-runtime-spec-at``.
    Source-anchored companion of
    ``/api/entitlement/next-tier-channel-spec`` (which anchors on the
    resolved entitlement's ``next_purchasable_tier``): where that
    endpoint reads the live perspective off the resolver, this one takes
    an explicit ``tier=`` so a pricing-comparison matrix can pivot the
    "at my next rung" question across every source rung off one shape.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "channel":        "<channel id>",
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<channel_spec_at row>} | null,
        }

    The inner ``row`` matches
    ``/channel-spec-at?tier=<target>&channel=<channel>`` byte-for-byte
    when ``target`` is populated -- a parity test pins this so the
    projection cannot drift from the full-row sibling.

    Every chat channel is FREE at every tier (the ``channels`` capacity
    axis governs how many concurrent channels each plan admits, not
    which adapters unlock), so whenever ``target`` resolves the row
    comes back ``free=True`` / ``locked=False`` / ``entitled=True``
    regardless of the target rung. That parity IS the answer: the
    tooltip can render "channel included at every plan" off ONE call
    without hard-coding that posture client-side.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the ceiling
    (no rung strictly above the source -- enterprise as source) -- the
    surface stays 200 with a populated envelope so callers can render
    "you're at the top" copy without a status-code branch.

    - **400** when ``tier=`` or ``channel=`` is missing / blank
    - **404** when ``tier`` is unknown or ``channel`` is unknown (not in
      :data:`ALL_CHANNELS`). The body carries ``which`` so a caller can
      render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope so the paywall surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_channel = request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": channel,
                    }
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_channel_spec_at(tier_in, channel)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "channel": channel,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_channel_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "channel": channel,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-at")
def api_entitlement_previous_tier_channel_spec_at():
    """``GET /api/entitlement/previous-tier-channel-spec-at?tier=<source>&channel=<id>``
    -- scalar what-if sibling of
    ``/api/entitlement/previous-tier-spec-at`` projected onto a SINGLE
    chat channel: the :func:`clawmetry.entitlements.channel_spec_at`-shape
    catalogue row for ``channel`` evaluated on the rung below the
    caller-supplied ``tier``.

    Source-anchored mirror of ``/next-tier-channel-spec-at`` and
    downgrade-confirmation counterpart on the channel axis. Lets a
    downgrade-confirmation card render "does THIS chat channel still
    unlock one rung down?" without re-walking the catalogue.

    Response shape matches ``/next-tier-channel-spec-at`` byte-for-byte
    (``tier``, ``tier_label``, ``tier_rank``, ``channel``, ``target``,
    ``target_label``, ``target_rank``, ``row``). Inner ``row`` matches
    ``/channel-spec-at?tier=<target>&channel=<channel>`` byte-for-byte
    when ``target`` is populated.

    Channel-axis always-free invariant applies on the downgrade side as
    well: whenever ``target`` resolves the row comes back ``free=True``
    / ``locked=False`` / ``entitled=True`` regardless of the downgrade
    target -- pinning that "chat channel included at every plan"
    posture on both directions.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor
    (``oss`` / ``cloud_free`` as source).

    - **400** when ``tier=`` or ``channel=`` is missing / blank
    - **404** when ``tier`` is unknown or ``channel`` is unknown.
    - **Never 5xxs**: builder failure short-circuits to ``row=null`` on
      the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    raw_channel = request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": channel,
                    }
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_channel_spec_at(tier_in, channel)
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "channel": channel,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_channel_spec_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "channel": channel,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )


def _next_prev_lock_reason_at(direction: str):
    """Shared handler body for ``/{next,previous}-tier-lock-reason-at``.

    Mirrors the axis-parsing contract of ``/api/entitlement/lock-reason-at``
    (exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=``) and the ceiling/floor envelope shape of
    ``/next-tier-feature-spec-at`` / ``/previous-tier-feature-spec-at``
    (``target`` / ``target_label`` / ``target_rank`` collapse to ``null``
    at the rung edge, lock fields collapse to the grace-shape unlocked
    row so the surface keeps rendering).

    ``direction`` is ``"next"`` or ``"previous"``: picks
    :func:`entitlements._next_purchasable_tier_after` vs
    :func:`entitlements._previous_purchasable_tier_before` and the matching
    log-name. Never 5xxs: synthesis failure short-circuits to the
    grace-shape envelope with ``target=null`` so the paywall surface stays
    mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    log_name = f"api_entitlement_{direction}_tier_lock_reason_at"
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
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
            bool(runtime_in),
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

        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            walk = _ent.next_tier_lock_reason_at
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            walk = _ent.previous_tier_lock_reason_at

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = walk(tier_in, feature, kind=kind) if target else None
            allowed = reason is None
        elif runtime_in:
            rt = _ent.canonical_runtime(runtime_in)
            key, kind = rt or runtime_in, "runtime"
            required = _ent.min_tier_for_runtime(rt) if rt else None
            reason = (
                walk(tier_in, rt or runtime_in, kind=kind) if target else None
            )
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok and target:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = walk(tier_in, str(channels_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_channel_count(channels_n)
                    if channels_ok
                    else None
                )
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok and target:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = walk(tier_in, str(retention_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_retention_window(retention_n)
                    if retention_ok
                    else None
                )
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok and target:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = walk(tier_in, str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_node_count(nodes_n)
                    if nodes_ok
                    else None
                )
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(tier_in)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": cur_rank,
                "key": key,
                "kind": kind,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": (
                    _ent.tier_rank(target) if target else None
                ),
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
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
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "key": key,
                "kind": kind,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "reason": None,
                "locked": False,
                "allowed": True,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "upgrade_required": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-lock-reason-at")
def api_entitlement_next_tier_lock_reason_at():
    """``GET /api/entitlement/next-tier-lock-reason-at?tier=<source>&<axis>=<id>``
    -- scalar what-if sibling of ``/api/entitlement/lock-reason-at``
    projected onto the rung above the caller-supplied ``tier``.

    Lock-reason-axis projection of ``/next-tier-spec-at`` and lock-reason
    sibling of ``/next-tier-feature-spec-at`` / ``/next-tier-runtime-spec-at``
    -- where those return the catalog row at the rung above, this returns
    the lock sentence the paywall surface would render there. Lets a
    paywall "what's the lock copy for THIS item at my next rung?"
    tooltip hydrate off ONE round-trip without the caller computing the
    target tier.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied. Response shape::

        {
          "tier":                 "<source tier id>",
          "tier_label":           "<source label>",
          "tier_rank":            <source rank>,
          "key":                  "<id-as-passed>",
          "kind":                 "feature|runtime|channels|retention_days|nodes",
          "target":               "<next-above tier id>" | null,
          "target_label":         "<next-above label>" | null,
          "target_rank":          <next-above rank> | null,
          "reason":               "<lock sentence>" | null,
          "locked":               <bool>,
          "allowed":              <bool>,
          "required_tier":        "<min purchasable tier>" | null,
          "required_tier_label":  "<label>" | null,
          "required_tier_rank":   <rank>,
          "upgrade_required":     <bool>,
        }

    The ``reason`` field matches
    ``/lock-reason-at?tier=<target>&<axis>=<id>`` byte-for-byte when
    ``target`` is populated -- a parity test pins this so the projection
    cannot drift from the full ``/lock-reason-at`` sibling.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``reason`` collapse to ``null`` (with
    ``locked=false`` / ``allowed=true``) at the ceiling -- the surface
    stays 200 with a populated envelope so callers can render "you're at
    the top" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank, when no axis is
      supplied, or when more than one axis is supplied
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: builder failure short-circuits to the grace-shape
      envelope with ``target=null`` so the paywall surface stays mute.
    """
    return _next_prev_lock_reason_at("next")


@bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-at")
def api_entitlement_previous_tier_lock_reason_at():
    """``GET /api/entitlement/previous-tier-lock-reason-at?tier=<source>&<axis>=<id>``
    -- scalar what-if sibling of ``/api/entitlement/lock-reason-at``
    projected onto the rung below the caller-supplied ``tier``.

    Source-anchored mirror of ``/next-tier-lock-reason-at`` and
    downgrade-confirmation counterpart on the lock-reason axis. Lets a
    downgrade-confirmation card render "what lock sentence would surface
    for THIS item if I drop one rung?" without recomputing the target
    tier.

    Response shape matches ``/next-tier-lock-reason-at`` byte-for-byte
    (``tier``, ``tier_label``, ``tier_rank``, ``key``, ``kind``,
    ``target``, ``target_label``, ``target_rank``, ``reason``,
    ``locked``, ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank``, ``upgrade_required``). The ``reason`` field
    matches ``/lock-reason-at?tier=<target>&<axis>=<id>`` byte-for-byte
    when ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``reason`` collapse to ``null`` (with
    ``locked=false`` / ``allowed=true``) at the floor (``oss`` /
    ``cloud_free`` as source).

    - **400** when ``tier=`` is missing / blank, when no axis is
      supplied, or when more than one axis is supplied
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: builder failure short-circuits to the grace-shape
      envelope with ``target=null``.
    """
    return _next_prev_lock_reason_at("previous")


def _next_prev_lock_reason_at_batch(direction: str):
    """Shared body for the ``/next-tier-lock-reason-at-batch`` and
    ``/previous-tier-lock-reason-at-batch`` endpoints. ``direction`` is
    ``"next"`` or ``"previous"``.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason_at_batch"
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_lock_reason_at_batch(
                tier_in,
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_lock_reason_at_batch(
                tier_in,
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        ent = _ent.get_entitlement()
        batch["tier"] = tier_in
        batch["tier_label"] = _ent.tier_label(tier_in)
        batch["tier_rank"] = _ent.tier_rank(tier_in)
        batch["target"] = target
        batch["target_label"] = _ent.tier_label(target) if target else None
        batch["target_rank"] = _ent.tier_rank(target) if target else None
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-lock-reason-at-batch")
def api_entitlement_next_tier_lock_reason_at_batch():
    """``GET /api/entitlement/next-tier-lock-reason-at-batch?tier=<source>
    &features=a,b&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    batch sibling of ``/api/entitlement/next-tier-lock-reason-at``.

    Where ``/next-tier-lock-reason-at`` returns ONE lock sentence for
    ONE item at the rung above ``tier``, this returns per-item rows for
    every supplied item across all 5 axes in ONE round-trip. Pairs with
    ``/next-tier-lock-reason-at`` the same way
    ``/lock-reasons-at-batch`` pairs with ``/lock-reason-at``: scalar ->
    matrix in one call. Fills the lock-reason-axis batch member of the
    ``next_*_at_batch`` family alongside
    ``/next-tier-feature-spec-at-batch`` and
    ``/next-tier-runtime-spec-at-batch``.

    Use case: a paywall "does THIS column of features / runtimes /
    capacity axes unlock at my next rung?" matrix surface hydrates every
    row off ONE call instead of N calls to ``/next-tier-lock-reason-at``
    per axis.

    Body is byte-identical to
    ``/lock-reasons-at-batch?tier=<target>&...`` for the resolved
    ``target = _next_purchasable_tier_after(tier)`` plus a ``tier`` /
    ``target`` echo -- a parity test pins this so the two batch surfaces
    cannot drift.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (matches
    ``/lock-reasons-at-batch``); supply as many as you like.
    ``features=`` / ``runtimes=`` take comma-separated tokens
    (whitespace + duplicates are normalised away; unknown ids contribute
    a grace-shape row). The three capacity axes take a single int each;
    blank / non-int values are treated as "not supplied".

    Response shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "tier":                 "<source tier id>",
          "tier_label":           "<source label>",
          "tier_rank":            <source rank>,
          "target":               "<next-above tier id>" | null,
          "target_label":         "<next-above label>" | null,
          "target_rank":          <next-above rank> | null,
          "current_tier":         "<live resolved tier>",
          "current_tier_rank":    <int>,
          "grace":                <bool>,
          "enforced":             <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason``, ``locked``,
    ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank`` -- the same 8 keys ``/lock-reasons-at-batch``
    returns.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). At the ceiling (enterprise as source) ``target`` is
    ``null`` and rows still render for every supplied item with
    ``reason=null`` / ``locked=false`` / ``allowed=true`` so callers can
    render "you're at the top" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank or no axis is supplied
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: builder failure short-circuits to the grace-shape
      envelope with ``target=null`` so the paywall surface stays mute.
    """
    return _next_prev_lock_reason_at_batch("next")


@bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-at-batch")
def api_entitlement_previous_tier_lock_reason_at_batch():
    """``GET /api/entitlement/previous-tier-lock-reason-at-batch?tier=<source>
    &features=a,b&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    batch sibling of ``/api/entitlement/previous-tier-lock-reason-at``.

    Source-anchored mirror of ``/next-tier-lock-reason-at-batch`` and
    downgrade-confirmation counterpart on the lock-reason axis. Lets a
    downgrade-confirmation matrix surface render "what lock sentences
    would surface for THIS column of items if I drop one rung?" without
    recomputing the target tier client-side.

    Response shape matches ``/next-tier-lock-reason-at-batch`` byte-for-
    byte (``features``, ``runtimes``, ``channels``, ``retention_days``,
    ``nodes``, ``tier``, ``tier_label``, ``tier_rank``, ``target``,
    ``target_label``, ``target_rank``, ``current_tier``,
    ``current_tier_rank``, ``grace``, ``enforced``). Body is
    byte-identical to ``/lock-reasons-at-batch?tier=<target>&...`` for
    the resolved
    ``target = _previous_purchasable_tier_before(tier)``.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). At the floor (``oss`` / ``cloud_free`` as source)
    ``target`` is ``null`` and rows still render for every supplied item
    with ``reason=null`` / ``locked=false`` / ``allowed=true``.

    - **400** when ``tier=`` is missing / blank or no axis is supplied
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: builder failure short-circuits to the grace-shape
      envelope with ``target=null``.
    """
    return _next_prev_lock_reason_at_batch("previous")


@bp_entitlement.route("/api/entitlement/tier-spec-path-batch")
def api_entitlement_tier_spec_path_batch():
    """``GET /api/entitlement/tier-spec-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/tier-spec-path``.

    Where ``/tier-spec-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between ONE ``from`` and
    N candidate ``to`` tiers in ONE round-trip. Pairs with
    ``/tier-spec-path`` the same way ``/feature-spec-path-batch`` pairs
    with ``/feature-spec-path``: scalar -> matrix in one call. Mirrors
    the multi-destination axis of ``/tier-spec-at-batch`` (which fans
    the same source across many targets one-rung-at-a-time) -- this
    batch fans the same source across many targets ALL-rungs-at-a-time.

    Use case: a pricing-comparison "from my current rung, here are the
    3 tiers I'm considering" surface hydrates the per-rung spec path to
    every candidate off ONE call instead of N calls to
    ``/tier-spec-path``. Same-rank siblings strictly between the
    endpoints are included for each per-destination path; same-rank
    siblings of each destination are excluded so the per-destination
    path terminates exactly at its own ``to``. Per-destination path
    lengths can legitimately differ (the rungs walked depend on the
    destination), unlike ``/feature-spec-path-batch`` whose rungs are
    feature-agnostic across the supplied feature set.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-spec-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-spec-at row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_spec_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_spec_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/tier-catalog-path-batch")
def api_entitlement_tier_catalog_path_batch():
    """``GET /api/entitlement/tier-catalog-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/tier-catalog-path`` and
    tier-axis member of the ``_catalog-path-batch`` family alongside
    ``/feature-catalog-path-batch`` and ``/runtime-catalog-path-batch``.

    Where ``/tier-catalog-path`` walks the rungs between ONE
    ``(from, to)`` pair and hydrates the full tier ladder at each rung,
    this walks the rungs between ONE ``from`` and N candidate ``to``
    tiers in ONE round-trip. Pairs with ``/tier-catalog-path`` the same
    way ``/tier-spec-path-batch`` pairs with ``/tier-spec-path``:
    scalar -> matrix in one call. Mirrors the multi-destination axis
    of ``/tier-catalog-at-batch`` (which fans the same perspective
    axis across many candidates one-rung-at-a-time) -- this batch fans
    the same source across many targets ALL-rungs-at-a-time.

    Use case: an upgrade-walkthrough / pricing-comparison "from my
    current rung, here are the 3 tiers I'm considering" surface
    hydrates the FULL tier ladder at every rung for every candidate
    off ONE call instead of first calling ``/tier-catalog-path`` N
    times (once per destination). Together with
    ``/feature-catalog-path-batch`` and ``/runtime-catalog-path-batch``
    the three ``_catalog-path-batch`` endpoints let the same surface
    hydrate every tier + feature + runtime column at every rung for
    every candidate off THREE calls instead of first calling
    ``/tier-path`` and then 3 * N calls to the scalar
    ``_catalog-path`` endpoints. Same-rank siblings strictly between
    the endpoints are included for each per-destination path;
    same-rank siblings of each destination are excluded so the
    per-destination path terminates exactly at its own ``to``.
    Per-destination path lengths can legitimately differ (the rungs
    walked depend on the destination), matching
    ``/tier-spec-path-batch`` / ``/feature-catalog-path-batch`` /
    ``/runtime-catalog-path-batch`` -- unlike
    ``/feature-spec-path-batch`` / ``/runtime-spec-path-batch`` whose
    rungs are item-agnostic across the supplied feature / runtime set.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-catalog-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets paths back for the valid ids.

    Response shape (mirrors ``/tier-spec-path-batch`` envelope with
    per-rung ``path`` rows carrying the full tier ladder rather than a
    single spec row)::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_catalog_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_catalog_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/tier-catalog-at-path")
def api_entitlement_tier_catalog_at_path():
    """``GET /api/entitlement/tier-catalog-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise tier-ladder
    path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/tier-catalog-path``: same rung walk, same per-
    rung body, plus a ``perspective_tier`` echo so a pricing-comparison
    walkthrough surface can call ``X_at_path(perspective, from, to)``
    uniformly across the whole ``_at_path`` slot of the tier-catalog
    family (alongside ``/tier-catalog-at`` and ``/tier-catalog-at-batch``,
    which fill the scalar-what-if and batch-what-if slots).

    Body posture matches ``/tier-catalog-at``: perspective is validated
    but does not shape the rows. Each row in ``path`` is byte-identical
    to a row from ``/tier-catalog-path?from=<from>&to=<to>`` -- pinned
    by parity tests. Perspective acceptance is lenient: ``trial`` IS
    accepted (matching every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<tier-catalog-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.tier_catalog_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_catalog_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-catalog-at-path-batch")
def api_entitlement_tier_catalog_at_path_batch():
    """``GET /api/entitlement/tier-catalog-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of ``/tier-catalog-at-path``.

    Where ``/tier-catalog-at-path`` walks the tier-ladder rungs between
    ONE ``(from, to)`` pair from a hypothetical ``perspective_tier``,
    this walks ONE ``from`` to N candidate ``to`` tiers in ONE round-
    trip from the same hypothetical perspective -- the batch what-if
    sibling of ``/tier-catalog-path-batch``, filling the
    ``_at_path_batch`` slot for the tier-catalog family.

    Body posture matches ``/tier-catalog-at``: perspective is validated
    but does not shape rows. Each row in ``tiers[].path`` is byte-
    identical to a row from ``/tier-catalog-path-batch`` for the same
    ``(from, to)`` pair. Perspective acceptance is lenient: ``trial``
    IS accepted (matching every other ``_at`` sibling). The GET+CSV
    query surface matches the ``/tier-catalog-path-batch`` sibling
    rather than the POST+JSON ``/preview-at-path-batch`` shape -- keeps
    the tier-catalog family internally consistent.

    Response shape (mirrors ``/tier-catalog-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_catalog_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_catalog_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/capacity-diff-at-path")
def api_entitlement_capacity_diff_at_path():
    """``GET /api/entitlement/capacity-diff-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise capacity
    transition path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/capacity-diff-path``: same rung walk, same
    per-rung capacity body (``target``, ``channel_limit``,
    ``retention_days``, ``node_limit`` where each axis is the
    ``{before, after, delta, unlocked, locked}`` triple), plus a
    ``perspective_tier`` echo so a pricing-comparison walkthrough
    surface can call ``X_at_path(perspective, from, to)`` uniformly
    across the whole ``_at_path`` slot of the capacity-diff family
    (alongside ``/capacity-diff-at`` and ``/capacity-diff-at-batch``,
    which fill the scalar-what-if and batch-what-if slots). Capacity-
    only mirror of ``/tier-catalog-at-path`` / ``/feature-catalog-at-
    path`` / ``/runtime-catalog-at-path`` -- same posture, capacity
    rows instead of catalog rows.

    Body posture matches ``/capacity-diff-at``: perspective is
    validated but does not shape the rows. Each row in ``path`` is
    byte-identical to a row from
    ``/capacity-diff-path?from=<from>&to=<to>`` -- pinned by parity
    tests. Perspective acceptance is lenient: ``trial`` IS accepted
    (matching every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<capacity-diff-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so a
      capacity-only pricing-comparison surface keeps rendering instead
      of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.capacity_diff_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_capacity_diff_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/capacity-diff-at-path-batch")
def api_entitlement_capacity_diff_at_path_batch():
    """``GET /api/entitlement/capacity-diff-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/capacity-diff-at-path``.

    Where ``/capacity-diff-at-path`` walks the capacity rungs between
    ONE ``(from, to)`` pair from a hypothetical ``perspective_tier``,
    this walks ONE ``from`` to N candidate ``to`` tiers in ONE round-
    trip from the same hypothetical perspective -- the batch what-if
    sibling of ``/capacity-diff-path-batch``, filling the
    ``_at_path_batch`` slot for the capacity-diff family.

    Body posture matches ``/capacity-diff-at``: perspective is
    validated but does not shape rows. Each row in ``tiers[].path`` is
    byte-identical to a row from ``/capacity-diff-path-batch`` for the
    same ``(from, to)`` pair. Perspective acceptance is lenient:
    ``trial`` IS accepted (matching every other ``_at`` sibling). The
    GET+CSV query surface matches the ``/capacity-diff-path-batch``
    sibling rather than the POST+JSON ``/preview-at-path-batch`` shape
    -- keeps the capacity-diff family internally consistent.

    Response shape (mirrors ``/capacity-diff-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<capacity-diff-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.capacity_diff_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_capacity_diff_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-catalog-at-path")
def api_entitlement_feature_catalog_at_path():
    """``GET /api/entitlement/feature-catalog-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise feature-catalog
    path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/feature-catalog-path``: same rung walk, same
    per-rung body, plus a ``perspective_tier`` echo so a pricing-
    comparison walkthrough surface can call
    ``X_at_path(perspective, from, to)`` uniformly across the whole
    ``_at_path`` slot of the feature-catalog family (alongside
    ``/feature-catalog-at`` and ``/feature-catalog-at-batch``, which
    fill the scalar-what-if and batch-what-if slots).

    Body posture matches ``/feature-catalog-at``: perspective is
    validated but does not shape the rows. Each row in ``path`` is
    byte-identical to a row from
    ``/feature-catalog-path?from=<from>&to=<to>`` -- pinned by parity
    tests. Perspective acceptance is lenient: ``trial`` IS accepted
    (matching every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<feature-catalog-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.feature_catalog_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_catalog_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/feature-catalog-at-path-batch")
def api_entitlement_feature_catalog_at_path_batch():
    """``GET /api/entitlement/feature-catalog-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/feature-catalog-at-path``.

    Where ``/feature-catalog-at-path`` walks the feature-catalog rungs
    between ONE ``(from, to)`` pair from a hypothetical
    ``perspective_tier``, this walks ONE ``from`` to N candidate ``to``
    tiers in ONE round-trip from the same hypothetical perspective --
    the batch what-if sibling of ``/feature-catalog-path-batch``,
    filling the ``_at_path_batch`` slot for the feature-catalog family.

    Body posture matches ``/feature-catalog-at``: perspective is
    validated but does not shape rows. Each row in ``tiers[].path`` is
    byte-identical to a row from ``/feature-catalog-path-batch`` for
    the same ``(from, to)`` pair. Perspective acceptance is lenient:
    ``trial`` IS accepted (matching every other ``_at`` sibling). The
    GET+CSV query surface matches the ``/feature-catalog-path-batch``
    sibling rather than the POST+JSON ``/preview-at-path-batch`` shape
    -- keeps the feature-catalog family internally consistent.

    Response shape (mirrors ``/feature-catalog-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<feature-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.feature_catalog_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_catalog_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-spec-path-batch")
def api_entitlement_feature_spec_path_batch():
    """``GET /api/entitlement/feature-spec-path-batch?from=<id>&to=<id>
    &features=a,b,c`` -- batch sibling of
    ``/api/entitlement/feature-spec-path``.

    Where ``/feature-spec-path`` walks ONE feature across the rungs
    between two tiers, this walks N features across the same rungs in
    ONE round-trip. Pairs with ``/feature-spec-path`` the same way
    ``/feature-spec-at-batch`` pairs with ``/feature-spec-at``: scalar
    -> matrix in one call.

    Use case: a pricing-comparison "compare A vs B, here are the 6
    features I care about" surface hydrates every rung for every
    feature off ONE call instead of N calls to ``/feature-spec-path``.
    Rung walk is feature-agnostic, so all per-feature paths share the
    same length and rung sequence -- the client can render the matrix
    as rows = features x cols = rungs without re-deriving the column
    headers per feature.

    Each row in ``features[].path`` is byte-identical to a row from
    ``/feature-spec-path?from=<from>&to=<to>&feature=<id>`` -- pinned
    by the parity tests so the scalar and batch path accessors cannot
    drift. Supplied feature ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    so a partially-bad caller still gets paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "features": [
            {"feature": "<id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=``, ``to=`` is missing / blank, or ``features=``
      is missing / empty after normalisation
    - **404** when ``from`` or ``to`` is unknown (body carries
      ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        if t not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        batch = _ent.feature_spec_path_batch(f, t, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
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
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_spec_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "features": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-path-batch")
def api_entitlement_runtime_spec_path_batch():
    """``GET /api/entitlement/runtime-spec-path-batch?from=<id>&to=<id>
    &runtimes=a,b,c`` -- batch sibling of
    ``/api/entitlement/runtime-spec-path``.

    Runtime-axis twin of ``/feature-spec-path-batch``. Aliases are
    canonicalised the same way ``/runtime-spec-path`` already does
    (``claude-code`` -> ``claude_code``), and aliases that collapse to a
    canonical id already in the response are silently de-duplicated so
    the row count matches the unique-canonical-id count.

    Each row in ``runtimes[].path`` is byte-identical to a row from
    ``/runtime-spec-path?from=<from>&to=<to>&runtime=<id>``. Unknown
    ids do not 404 the call -- they are echoed in ``unknown[]`` carrying
    the supplied alias so the caller can correlate against what was
    sent.

    Response shape mirrors ``/feature-spec-path-batch`` with
    ``"runtimes"`` in place of ``"features"`` and a per-row
    ``"runtime"`` key in place of ``"feature"``.

    - **400** when ``from=`` / ``to=`` is missing or ``runtimes=`` is
      missing / empty after normalisation
    - **404** when ``from`` or ``to`` is unknown
    - **Never 5xxs**.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        if t not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        batch = _ent.runtime_spec_path_batch(f, t, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
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
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_spec_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "runtimes": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-at-path")
def api_entitlement_runtime_spec_at_path():
    """``GET /api/entitlement/runtime-spec-at-path?tier=<perspective>
    &from=<id>&to=<id>&runtime=<id>`` -- perspective-validated what-if
    sibling of ``/api/entitlement/runtime-spec-path``.

    Runtime-axis twin of ``/feature-spec-at-path``; fills the
    ``_at_path`` slot of the ``runtime-spec`` family, matching the
    already-shipping ``preview_at_path`` / ``tier_catalog_at_path``
    pattern on the ``preview`` / ``tier_catalog`` axes. The perspective
    is validated (400 on missing, 404 on unknown) but does NOT shape
    the ``path`` rows -- the body is byte-identical to
    ``/runtime-spec-path?from=<from>&to=<to>&runtime=<runtime>`` for
    every perspective. Pinned by parity tests so the ``_at_path`` and
    ``_path`` endpoints cannot drift.

    Accepts runtime aliases (``claude-code`` -> ``claude_code``) via
    :func:`clawmetry.entitlements.canonical_runtime` so the URL surface
    matches what callers already pass to ``/api/entitlement/required-tier``.

    Response shape (mirrors ``/runtime-spec-path`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail so a paywall matrix UI can render "at Cloud Pro this runtime
    unlocks at Starter" without a second call to ``/entitlement``)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "runtime":               "<canonical runtime id>",
          "path":                  [<runtime_spec_path row>, ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` or ``runtime=`` is
      missing / blank
    - **404** when any id is unknown (body carries
      ``which: "tier" | "from" | "to" | "runtime"`` so the caller can
      point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with the perspective echoed so the UI keeps
      rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    rt_raw = (request.args.get("runtime") or "").strip()
    if not rt_raw:
        return jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        rt = _ent.canonical_runtime(rt_raw)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": rt or rt_raw.lower(),
                    }
                ),
                404,
            )
        path = _ent.runtime_spec_at_path(tier_in, f, t, rt_raw)
        if path is None:
            path = []
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "runtime": rt,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_runtime_spec_at_path: error: %s", exc)
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "runtime": rt_raw.lower(),
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-spec-at-path-batch")
def api_entitlement_runtime_spec_at_path_batch():
    """``GET /api/entitlement/runtime-spec-at-path-batch?tier=<perspective>
    &from=<id>&to=<id>&runtimes=a,b,c`` -- perspective-validated what-if
    batch sibling of ``/api/entitlement/runtime-spec-path-batch``.

    Fills the ``_at_path_batch`` slot of the ``runtime-spec`` family;
    fixed-perspective, fixed-from, fixed-to, multi-runtime companion of
    ``/runtime-spec-at-path``. Per-runtime body byte-identical to
    ``/runtime-spec-path-batch`` for the same ``(from, to, runtimes)``
    triple -- scalar / batch no-drift contract.

    Aliases are canonicalised the same way ``/runtime-spec-path`` does
    (``claude-code`` -> ``claude_code``), and aliases that collapse to
    a canonical id already in the response are silently de-duplicated
    so the row count matches the unique-canonical-id count. Unknown
    ids do NOT 404 the call -- they are echoed in ``unknown[]``
    carrying the supplied alias (not the canonical id) so the caller
    can correlate against what was sent.

    Response shape (mirrors ``/runtime-spec-path-batch`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "runtimes": [
            {"runtime": "<canonical id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` is missing / blank, or
      ``runtimes=`` is missing / empty after normalisation
    - **404** when any tier id is unknown (body carries
      ``which: "tier" | "from" | "to"``)
    - Unknown runtime ids do NOT 404 the call -- they are echoed in
      ``unknown[]`` so a partially-bad caller still gets paths back for
      the valid ids alongside a list of what was dropped, matching
      every other ``*_path_batch`` sibling's posture.
    - **Never 5xxs**: a synthesis failure short-circuits to a grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        batch = _ent.runtime_spec_at_path_batch(tier_in, f, t, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_spec_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "runtimes": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/lock-reason-path-batch")
def api_entitlement_lock_reason_path_batch():
    """``GET /api/entitlement/lock-reason-path-batch?from=<id>&to=<id>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M``
    -- multi-axis batch sibling of
    ``/api/entitlement/lock-reason-path``.

    Where ``/lock-reason-path`` walks ONE item across the rungs between
    two tiers, this walks N items across all 5 axes (features +
    runtimes + 3 capacity axes) across the same rungs in ONE
    round-trip. Pairs with ``/lock-reason-path`` the same way
    ``/lock-reasons-at-batch`` pairs with ``/lock-reason-at``: scalar
    what-if -> matrix what-if.

    Use case: a paywall comparison surface ("here are the 6 features +
    2 runtimes + my channel count + my retention window, walk each one
    from OSS to Enterprise") hydrates the full matrix off ONE call
    instead of N calls to ``/lock-reason-path`` per item. Rung walk is
    item-agnostic, so all per-item paths share the same length and
    rung sequence -- the client can render the matrix as rows = items
    x cols = rungs without re-deriving the column headers per item.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (matches
    ``/lock-reasons-at-batch``); supply as many as you like.
    ``features=`` / ``runtimes=`` take comma-separated tokens
    (whitespace + duplicates are normalised away; unknown ids are
    echoed in ``unknown[]`` instead of 404'ing the call). The three
    capacity axes take a single int each; blank / non-int / non-
    positive values render that axis as ``None`` (matches
    ``/lock-reason-path``'s short-circuit posture).

    Each row in ``features[].path`` / ``runtimes[].path`` /
    ``channels.path`` / ``retention_days.path`` / ``nodes.path`` is
    byte-identical to a row from ``/lock-reason-path?from=<from>
    &to=<to>&<axis>=<id>`` -- pinned by the parity tests so the scalar
    and batch path accessors cannot drift.

    Response shape (mirrors ``/feature-spec-path-batch`` envelope plus
    the 5-axis body from ``/lock-reasons-at-batch``)::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "to":         "<tier id>",
          "to_label":   "...",
          "to_rank":    <int>,
          "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
          "features": [{"key": "<id>", "path": [<augmented row>, ...]}, ...],
          "runtimes": [{"key": "<canonical id>", "path": [...]}, ...],
          "channels":       {"key": "<n>", "path": [...]} | None,
          "retention_days": {"key": "<n>", "path": [...]} | None,
          "nodes":          {"key": "<n>", "path": [...]} | None,
          "unknown": {"features": [...], "runtimes": [...]},
        }

    - **400** when ``from=`` / ``to=`` is missing / blank, or no axis
      is supplied
    - **404** when ``from`` or ``to`` is unknown (body carries
      ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f or not t:
        return jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        if t not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        batch = _ent.lock_reason_path_batch(
            f,
            t,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "unknown": {"features": [], "runtimes": []},
            }
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
                "features": batch.get("features", []),
                "runtimes": batch.get("runtimes", []),
                "channels": batch.get("channels"),
                "retention_days": batch.get("retention_days"),
                "nodes": batch.get("nodes"),
                "unknown": batch.get(
                    "unknown", {"features": [], "runtimes": []}
                ),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_lock_reason_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "unknown": {"features": [], "runtimes": []},
            }
        )


def _next_prev_tier_feature_spec_at_batch(
    direction: str,
):
    """Shared helper for the two ``/api/entitlement/{next,previous}-tier-
    feature-spec-at-batch`` handlers.

    ``direction`` selects the rung helper (``next`` / ``previous``).
    Returned envelope shape is identical for both directions so the
    paywall surface can swap one URL for the other without re-deriving
    the row schema.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_feature_spec_at_batch(tier_in, features)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_feature_spec_at_batch(tier_in, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_feature_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "features": [],
                "unknown": [],
            }
        )


def _next_prev_tier_runtime_spec_at_batch(
    direction: str,
):
    """Runtime-axis twin of :func:`_next_prev_tier_feature_spec_at_batch`.
    Aliases are canonicalised one layer below in the helper -- this
    wrapper just shuttles the supplied CSV through ``_parse_csv_arg``
    and lets the helper de-duplicate, mirroring ``/runtime-spec-path-
    batch``.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_runtime_spec_at_batch(tier_in, runtimes)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_runtime_spec_at_batch(tier_in, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_runtime_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "runtimes": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-feature-spec-at-batch")
def api_entitlement_next_tier_feature_spec_at_batch():
    """``GET /api/entitlement/next-tier-feature-spec-at-batch?tier=<source>
    &features=a,b,c`` -- batch sibling of
    ``/api/entitlement/next-tier-feature-spec-at``.

    Where ``/next-tier-feature-spec-at`` projects ONE feature onto the
    rung above the caller-supplied source, this projects N features
    onto that same rung in ONE round-trip. Pairs with
    ``/next-tier-feature-spec-at`` the same way
    ``/feature-spec-at-batch`` pairs with ``/feature-spec-at``: scalar
    what-if -> batch what-if.

    Use case: a pricing-comparison "here are the 6 features I care
    about -- what do they look like at my next rung?" surface hydrates
    every feature off ONE call instead of N calls to
    ``/next-tier-feature-spec-at``.

    Each row in ``features[].row`` is byte-identical to the body of
    ``/next-tier-feature-spec-at?tier=<source>&feature=<id>`` ``.row``
    -- pinned by parity tests so the scalar and batch accessors cannot
    drift. Supplied feature ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved). Unknown
    ids do not 404 the call -- they are echoed in ``unknown[]`` so a
    partially-bad caller still gets rows back for the valid ids.

    At the ceiling (enterprise as source, no rung above) every per-
    feature ``row`` is ``null`` while the envelope's ``target`` /
    ``target_label`` / ``target_rank`` collapse to ``null`` -- the
    surface stays 200 so callers can render "you're at the top" copy
    without a status-code branch.

    Response shape::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "features": [
            {"feature": "<id>", "row": {<feature_spec_at row>} | null},
            ...
          ],
          "unknown": ["bogus_id", ...],
        }

    - **400** when ``tier=`` is missing / blank, or ``features=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    return _next_prev_tier_feature_spec_at_batch("next")


@bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-at-batch")
def api_entitlement_previous_tier_feature_spec_at_batch():
    """``GET /api/entitlement/previous-tier-feature-spec-at-batch
    ?tier=<source>&features=a,b,c`` -- source-anchored mirror of
    ``/api/entitlement/next-tier-feature-spec-at-batch`` and batch
    sibling of ``/api/entitlement/previous-tier-feature-spec-at``.

    Lets a downgrade-confirmation card render "here are the N features
    I care about -- do they still unlock one rung down?" off ONE round-
    trip instead of N calls to ``/previous-tier-feature-spec-at``.

    Each row in ``features[].row`` is byte-identical to the body of
    ``/previous-tier-feature-spec-at?tier=<source>&feature=<id>``
    ``.row``. At the floor (``oss`` / ``cloud_free`` as source) every
    per-feature ``row`` is ``null`` while ``target`` / ``target_label``
    / ``target_rank`` collapse to ``null``.

    Response shape, validation, and never-5xx posture are identical to
    ``/next-tier-feature-spec-at-batch``.
    """
    return _next_prev_tier_feature_spec_at_batch("previous")


@bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-at-batch")
def api_entitlement_next_tier_runtime_spec_at_batch():
    """``GET /api/entitlement/next-tier-runtime-spec-at-batch?tier=<source>
    &runtimes=a,b,c`` -- runtime-axis twin of
    ``/api/entitlement/next-tier-feature-spec-at-batch``.

    Aliases are canonicalised the same way ``/next-tier-runtime-spec-at``
    already does (``claude-code`` -> ``claude_code``), and aliases that
    collapse to a canonical id already in the response are silently
    de-duplicated so the row count matches the unique-canonical-id
    count.

    Each row in ``runtimes[].row`` is byte-identical to the body of
    ``/next-tier-runtime-spec-at?tier=<source>&runtime=<id>`` ``.row``.
    Unknown ids do not 404 the call -- they are echoed in ``unknown[]``
    carrying the supplied alias so the caller can correlate against
    what was sent.

    At the ceiling every per-runtime ``row`` is ``null`` while
    ``target`` / ``target_label`` / ``target_rank`` collapse to
    ``null``.

    Response shape mirrors ``/next-tier-feature-spec-at-batch`` with
    ``"runtimes"`` in place of ``"features"`` and a per-row
    ``"runtime"`` key (canonical id) in place of ``"feature"``.

    - **400** when ``tier=`` is missing or ``runtimes=`` is missing /
      empty after normalisation
    - **404** when ``tier`` is unknown
    - **Never 5xxs**.
    """
    return _next_prev_tier_runtime_spec_at_batch("next")


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-at-batch")
def api_entitlement_previous_tier_runtime_spec_at_batch():
    """``GET /api/entitlement/previous-tier-runtime-spec-at-batch
    ?tier=<source>&runtimes=a,b,c`` -- source-anchored mirror of
    ``/api/entitlement/next-tier-runtime-spec-at-batch`` and batch
    sibling of ``/api/entitlement/previous-tier-runtime-spec-at``.

    Each row in ``runtimes[].row`` is byte-identical to the body of
    ``/previous-tier-runtime-spec-at?tier=<source>&runtime=<id>``
    ``.row``. At the floor every per-runtime ``row`` is ``null``.

    Response shape, alias handling, validation, and never-5xx posture
    are identical to ``/next-tier-runtime-spec-at-batch``.
    """
    return _next_prev_tier_runtime_spec_at_batch("previous")


def _next_prev_tier_channel_spec_at_batch(
    direction: str,
):
    """Shared helper for the two ``/api/entitlement/{next,previous}-tier-
    channel-spec-at-batch`` handlers.

    Channel-axis twin of :func:`_next_prev_tier_feature_spec_at_batch`
    / :func:`_next_prev_tier_runtime_spec_at_batch`. ``direction``
    selects the rung helper (``next`` / ``previous``). Returned
    envelope shape is identical for both directions so the paywall
    surface can swap one URL for the other without re-deriving the row
    schema.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_channel_spec_at_batch(tier_in, channels)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_channel_spec_at_batch(tier_in, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_channel_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "channels": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-channel-spec-at-batch")
def api_entitlement_next_tier_channel_spec_at_batch():
    """``GET /api/entitlement/next-tier-channel-spec-at-batch?tier=<source>
    &channels=a,b,c`` -- channel-axis twin of
    ``/api/entitlement/next-tier-feature-spec-at-batch`` /
    ``/api/entitlement/next-tier-runtime-spec-at-batch`` and batch
    sibling of ``/api/entitlement/next-tier-channel-spec-at``.

    Where ``/next-tier-channel-spec-at`` projects ONE chat channel
    onto the rung above the caller-supplied source, this projects N
    channels onto that same rung in ONE round-trip. Pairs with
    ``/next-tier-channel-spec-at`` the same way
    ``/channel-spec-at-batch`` pairs with ``/channel-spec-at``: scalar
    what-if -> batch what-if.

    Use case: a pricing-comparison "here are the 6 chat channels I
    care about -- what do they look like at my next rung?" surface
    hydrates every channel off ONE call instead of N calls to
    ``/next-tier-channel-spec-at``.

    Each row in ``channels[].row`` is byte-identical to the body of
    ``/next-tier-channel-spec-at?tier=<source>&channel=<id>`` ``.row``
    -- pinned by parity tests so the scalar and batch accessors cannot
    drift. Supplied channel ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets rows back for
    the valid ids.

    Every chat channel is FREE at every tier (see
    ``/channel-spec-at``), so whenever ``row`` is not ``null`` it
    comes back ``free=true`` / ``locked=false`` / ``entitled=true``
    regardless of the target rung -- the surface can render "chat
    channel included at every plan" off ONE call without hard-coding
    that posture client-side.

    At the ceiling (enterprise as source, no rung above) every per-
    channel ``row`` is ``null`` while the envelope's ``target`` /
    ``target_label`` / ``target_rank`` collapse to ``null`` -- the
    surface stays 200 so callers can render "you're at the top" copy
    without a status-code branch.

    Response shape::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "channels": [
            {"channel": "<id>", "row": {<channel_spec_at row>} | null},
            ...
          ],
          "unknown": ["bogus_id", ...],
        }

    - **400** when ``tier=`` is missing / blank, or ``channels=`` is
      missing / empty after normalisation
    - **404** when ``tier`` is unknown (body carries ``which: "tier"``)
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    return _next_prev_tier_channel_spec_at_batch("next")


@bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-at-batch")
def api_entitlement_previous_tier_channel_spec_at_batch():
    """``GET /api/entitlement/previous-tier-channel-spec-at-batch
    ?tier=<source>&channels=a,b,c`` -- source-anchored mirror of
    ``/api/entitlement/next-tier-channel-spec-at-batch`` and batch
    sibling of ``/api/entitlement/previous-tier-channel-spec-at``.

    Lets a downgrade-confirmation card render "here are the N chat
    channels I care about -- do they still unlock one rung down?" off
    ONE round-trip instead of N calls to
    ``/previous-tier-channel-spec-at``.

    Each row in ``channels[].row`` is byte-identical to the body of
    ``/previous-tier-channel-spec-at?tier=<source>&channel=<id>``
    ``.row``. At the floor (``oss`` / ``cloud_free`` as source) every
    per-channel ``row`` is ``null`` while ``target`` / ``target_label``
    / ``target_rank`` collapse to ``null``.

    Response shape, validation, and never-5xx posture are identical to
    ``/next-tier-channel-spec-at-batch``.
    """
    return _next_prev_tier_channel_spec_at_batch("previous")


@bp_entitlement.route("/api/entitlement/capacity-diff-path-batch")
def api_entitlement_capacity_diff_path_batch():
    """``GET /api/entitlement/capacity-diff-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/capacity-diff-path``.

    Where ``/capacity-diff-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between ONE ``from`` and
    N candidate ``to`` tiers in ONE round-trip. Pairs with
    ``/capacity-diff-path`` the same way ``/tier-spec-path-batch``
    pairs with ``/tier-spec-path``: scalar -> matrix in one call.
    Mirrors the multi-destination axis of ``/tier-spec-path-batch`` --
    same fan-out shape, capacity-only per-rung body.

    Use case: a capacity-only pricing-comparison "from my current
    rung, here are the 3 tiers I'm considering -- show me the
    channels / retention / nodes bumps to each" surface hydrates the
    per-rung capacity transitions to every candidate off ONE call
    instead of N calls to ``/capacity-diff-path``. Same-rank siblings
    strictly between the endpoints are included for each
    per-destination path; same-rank siblings of each destination are
    excluded so the per-destination path terminates exactly at its own
    ``to``. Per-destination path lengths can legitimately differ (the
    rungs walked depend on the destination), matching
    ``/tier-spec-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/capacity-diff-path?from=<from>&to=<to>`` -- pinned by the
    parity tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<capacity-diff row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.capacity_diff_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_capacity_diff_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-path-batch")
def api_entitlement_tier_unlocks_path_batch():
    """``GET /api/entitlement/tier-unlocks-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/tier-unlocks-path``.

    Where ``/tier-unlocks-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between ONE ``from`` and
    N candidate ``to`` tiers in ONE round-trip. Pairs with
    ``/tier-unlocks-path`` the same way ``/capacity-diff-path-batch``
    pairs with ``/capacity-diff-path``: scalar -> matrix in one call.
    Multi-destination twin of ``/capacity-diff-path-batch`` (same
    fan-out shape, marginal-unlocks per-rung body) and unlocks-only
    sibling of ``/tier-spec-path-batch`` (same multi-destination axis,
    marginal-grant body instead of full per-rung spec).

    Use case: an upgrade-comparison "from my current rung, here are
    the 3 tiers I'm considering -- show me the newly-unlocked features
    + runtimes at every rung climbed to reach each" surface hydrates
    the per-rung marginal unlocks to every candidate off ONE call
    instead of N calls to ``/tier-unlocks-path``. Same-rank siblings
    strictly between the endpoints are included for each
    per-destination path; same-rank siblings of each destination are
    excluded so the per-destination path terminates exactly at its own
    ``to``. Per-destination path lengths can legitimately differ (the
    rungs walked depend on the destination), matching
    ``/capacity-diff-path-batch`` and ``/tier-spec-path-batch``'s
    posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-unlocks-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-unlocks row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_unlocks_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_unlocks_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/tier-locks-path-batch")
def api_entitlement_tier_locks_path_batch():
    """``GET /api/entitlement/tier-locks-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/tier-locks-path``.

    Where ``/tier-locks-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between ONE ``from`` and
    N candidate ``to`` tiers in ONE round-trip. Pairs with
    ``/tier-locks-path`` the same way ``/tier-unlocks-path-batch``
    pairs with ``/tier-unlocks-path``: scalar -> matrix in one call.
    Marginal-loss mirror of ``/tier-unlocks-path-batch`` (same multi-
    destination axis, locks body instead of unlocks body) and locks-
    only sibling of ``/tier-spec-path-batch`` (same fan-out shape,
    marginal-loss body instead of full per-rung spec).

    Use case: a downgrade-walkthrough "from my current rung, here are
    the 3 tiers I'm considering dropping to -- show me the newly-lost
    features + runtimes at every rung walked to reach each" surface
    hydrates the per-rung marginal losses to every candidate off ONE
    call instead of N calls to ``/tier-locks-path``. Same-rank
    siblings strictly between the endpoints are included for each
    per-destination path; same-rank siblings of each destination are
    excluded so the per-destination path terminates exactly at its own
    ``to``. Per-destination path lengths can legitimately differ (the
    rungs walked depend on the destination), matching
    ``/tier-unlocks-path-batch`` and ``/tier-spec-path-batch``'s
    posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-locks-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-locks row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_locks_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_locks_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )




@bp_entitlement.route("/api/entitlement/tier-path-batch")
def api_entitlement_tier_path_batch():
    """``GET /api/entitlement/tier-path-batch?from=<id>&to=a,b,c`` --
    batch sibling of ``/api/entitlement/tier-path``.

    Where ``/tier-path`` walks the rungs between ONE ``(from, to)``
    pair, this walks the rungs between ONE ``from`` and N candidate
    ``to`` tiers in ONE round-trip. Pairs with ``/tier-path`` the same
    way ``/tier-spec-path-batch`` pairs with ``/tier-spec-path``:
    scalar -> matrix in one call. All-slices member of the path-batch
    grid -- carries the full marginal ``tier_diff`` per rung (added +
    lost features, added + lost runtimes, capacity changes) rather
    than a single slice the way ``/tier-unlocks-path-batch`` /
    ``/tier-locks-path-batch`` / ``/capacity-diff-path-batch`` do.

    Use case: a pricing-comparison "from my current rung, here are the
    3 tiers I'm considering" surface hydrates the per-rung full
    marginal step diff to every candidate off ONE call instead of N
    calls to ``/tier-path``. Same-rank siblings strictly between the
    endpoints are included for each per-destination path; same-rank
    siblings of each destination are excluded so the per-destination
    path terminates exactly at its own ``to``. Per-destination path
    lengths can legitimately differ (the rungs walked depend on the
    destination), matching ``/tier-spec-path-batch`` /
    ``/capacity-diff-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-path?from=<from>&to=<to>`` -- pinned by the parity tests
    so the scalar and batch path accessors cannot drift. Supplied
    destination ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do
    not 404 the call -- they are echoed in ``unknown[]`` so a
    partially-bad caller still gets paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier_diff row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/preview-path-batch", methods=["POST"])
def api_entitlement_preview_path_batch():
    """``POST /api/entitlement/preview-path-batch`` -- batch sibling of
    ``/api/entitlement/preview-path``.

    Where ``/preview-path`` walks the cumulative-state rungs between
    ONE ``(from, to)`` pair, this walks the cumulative-state rungs
    between ONE ``from`` and N candidate ``to`` tiers in ONE round-trip
    -- the cumulative-state member of the path-batch grid alongside
    ``/tier-path-batch`` (all-slices marginal),
    ``/tier-spec-path-batch`` (spec envelope),
    ``/capacity-diff-path-batch`` (capacity slice),
    ``/tier-unlocks-path-batch`` (grants slice) and
    ``/tier-locks-path-batch`` (losses slice).

    Use case: an upgrade-walkthrough surface hydrates the per-rung
    ``Entitlement`` snapshot to every candidate destination off ONE
    call instead of N calls to ``/preview-path``. Per-destination path
    lengths can legitimately differ (the rungs walked depend on the
    destination), matching every other ``*_path_batch`` sibling's
    posture.

    Request body::

        {
          "from": "<tier id>",
          "to":   ["<tier id>", ...]
        }

    Response shape::

        {
          "from":         "<tier id>",
          "from_label":   "...",
          "from_rank":    <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<preview row>, ...],
            },
            ...
          ],
          "unknown":       ["bogus_id", ...],
          "current_tier":  "<tier id>",
          "grace":         <bool>,
          "enforced":      <bool>,
        }

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/preview-path?from=<from>&to=<to>``. Supplied destination ids are
    normalised (whitespace stripped, lowercased, duplicates dropped,
    first-seen order preserved). Unknown destination ids do NOT 404 the
    call -- they are echoed in ``unknown[]`` so a partially-bad caller
    still gets paths back for the valid ids.

    - **400** when ``from`` is missing / blank, or ``to`` is missing /
      empty
    - **404** when ``from`` is unknown (body carries ``which: "from"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.

    POST rather than GET because ``to`` is a list of tier ids that may
    grow past a comfortable query-string length; the sibling
    ``/tier-path-batch`` uses GET+CSV where the list is expected to
    stay small. Both response envelopes carry the same shape so a
    single UI walker can consume either family.
    """
    body = request.get_json(silent=True) or {}
    try:
        f_raw = body.get("from")
        f = str(f_raw or "").strip().lower()
    except Exception:
        f = ""
    if not f:
        return jsonify({"error": "missing from"}), 400
    to_raw = body.get("to")
    if to_raw is None or (isinstance(to_raw, (list, tuple)) and not to_raw):
        return jsonify({"error": "missing or empty to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        try:
            candidates = [str(t) for t in (to_raw or [])]
        except TypeError:
            return jsonify({"error": "to must be a list"}), 400
        batch = _ent.preview_path_batch(f, candidates)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_preview_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-catalog-path-batch")
def api_entitlement_feature_catalog_path_batch():
    """``GET /api/entitlement/feature-catalog-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/feature-catalog-path``.

    Where ``/feature-catalog-path`` walks the full-catalog rungs between
    ONE ``(from, to)`` pair, this walks the full-catalog rungs between
    ONE ``from`` and N candidate ``to`` tiers in ONE round-trip. Pairs
    with ``/feature-catalog-path`` the same way
    ``/capacity-diff-path-batch`` pairs with ``/capacity-diff-path``:
    scalar -> matrix in one call. Full-catalog member of the path-batch
    grid alongside ``/tier-path-batch`` (all-slices marginal),
    ``/tier-spec-path-batch`` (spec envelope),
    ``/capacity-diff-path-batch`` (capacity slice),
    ``/tier-unlocks-path-batch`` (grants slice),
    ``/tier-locks-path-batch`` (losses slice) and
    ``/preview-path-batch`` (cumulative snapshot).

    Use case: an upgrade-comparison walkthrough surface hydrates the
    per-rung feature catalog to every candidate destination off ONE call
    instead of N calls to ``/feature-catalog-path``. Same-rank siblings
    strictly between the endpoints are included for each per-destination
    path; same-rank siblings of each destination are excluded so the
    per-destination path terminates exactly at its own ``to``. Per-
    destination path lengths can legitimately differ (rungs walked
    depend on the destination), matching ``/tier-spec-path-batch`` /
    ``/capacity-diff-path-batch`` / ``/preview-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/feature-catalog-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift. Supplied
    destination ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do not
    404 the call -- they are echoed in ``unknown[]`` so a partially-bad
    caller still gets paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<feature-catalog-at-batch row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.feature_catalog_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_catalog_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog-path-batch")
def api_entitlement_runtime_catalog_path_batch():
    """``GET /api/entitlement/runtime-catalog-path-batch?from=<id>&to=a,b,c``
    -- runtime-axis twin of ``/feature-catalog-path-batch``.

    Pairs with ``/feature-catalog-path-batch`` the same way
    ``/runtime-catalog-at-batch`` pairs with
    ``/feature-catalog-at-batch`` and ``/runtime-catalog-path`` pairs
    with ``/feature-catalog-path``. Together the two batch path endpoints
    let an upgrade-comparison walkthrough UI render every feature +
    runtime column at every rung walked to N candidate destinations off
    TWO calls instead of first calling ``/tier-path-batch`` (or
    ``/tier-path`` per destination) and then 2 * N calls to the scalar
    what-if catalog endpoints.

    Each row in ``tiers[].path`` mirrors the ``/runtime-catalog-at-batch``
    row shape (``tier``, ``tier_label``, ``tier_rank``, ``runtimes``); the
    ``runtimes`` list byte-equals ``/runtime-catalog-at?tier=<rung>`` for
    the same rung -- pinned by the parity tests. Supplied destination ids
    are normalised (whitespace stripped, lowercased, duplicates dropped,
    first-seen order preserved). Unknown ids do not 404 the call -- they
    are echoed in ``unknown[]``.

    Response shape, direction semantics and error posture match
    ``/feature-catalog-path-batch`` exactly. Never 5xxs.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.runtime_catalog_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_catalog_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/channel-catalog-path-batch")
def api_entitlement_channel_catalog_path_batch():
    """``GET /api/entitlement/channel-catalog-path-batch?from=<id>&to=a,b,c``
    -- batch sibling of ``/api/entitlement/channel-catalog-path``.

    Where ``/channel-catalog-path`` walks the full-catalog rungs between
    ONE ``(from, to)`` pair, this walks the full-catalog rungs between
    ONE ``from`` and N candidate ``to`` tiers in ONE round-trip.
    Channel-axis twin of ``/feature-catalog-path-batch`` and
    ``/runtime-catalog-path-batch``: pairs with them the same way
    ``/channel-catalog-at-batch`` pairs with
    ``/feature-catalog-at-batch`` / ``/runtime-catalog-at-batch``.
    Together the three catalog ``-path-batch`` endpoints on the feature /
    runtime / channel axes plus the ``-path-batch`` endpoint on the tier
    axis let an upgrade-comparison walkthrough UI render every feature +
    runtime + channel + tier column at every rung walked to N candidate
    destinations off FOUR calls instead of first calling
    ``/tier-path-batch`` (or ``/tier-path`` per destination) and then 4 *
    N calls to the scalar what-if catalog endpoints.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/channel-catalog-path?from=<from>&to=<to>`` -- pinned by the parity
    tests so the scalar and batch path accessors cannot drift. Per-rung
    ``channels`` list byte-equals ``/channel-catalog`` for every rung
    (every chat-channel adapter is FREE at every tier, so the catalogue
    is invariant across the rung walk). Supplied destination ids are
    normalised (whitespace stripped, lowercased, duplicates dropped,
    first-seen order preserved). Unknown ids do not 404 the call -- they
    are echoed in ``unknown[]`` so a partially-bad caller still gets
    paths back for the valid ids.

    Response shape::

        {
          "from":       "<tier id>",
          "from_label": "...",
          "from_rank":  <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<channel-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing
      / empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids --
      does NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.channel_catalog_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_catalog_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-capacity-diff")
def api_entitlement_next_tier_capacity_diff():
    """``GET /api/entitlement/next-tier-capacity-diff`` -- capacity-only
    marginal row for the rung immediately above the resolved
    entitlement, in :func:`clawmetry.entitlements.capacity_diff` shape
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``
    where each capacity axis is the
    ``{before, after, delta, unlocked, locked}`` triple
    :func:`_capacity_transition` builds).

    Current-relative convenience for
    ``/api/entitlement/next-tier-capacity-diff-at?tier=<current>``; the
    upgrade-CTA capacity-only companion to
    ``/api/entitlement/next-tier-diff`` (full ``upgrade_diff`` shape),
    ``/next-tier-unlocks`` (marginal grants), ``/next-tier-locks``
    (marginal losses), and ``/next-tier-spec`` (full tier row). Fills
    the bare-directional slot the family was missing next to the
    already-shipped source-parameterised ``_at`` variant.

    Response shape::

        {
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<resolved label>",
          "current_tier_rank":  <resolved rank>,
          "row":                {<capacity_diff row>} | null,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    ``row`` collapses to ``null`` at the ceiling (no rung above -- the
    resolved entitlement is already at Enterprise). Never 5xxs: a
    resolver failure short-circuits to the grace-shape envelope so the
    dashboard CTA keeps rendering instead of disappearing.

    Unlike the ``_at`` variant, the resolved entitlement drives the
    ``before`` side of each capacity axis -- so under grace mode where
    the live :func:`capacity_diff` reports the unlimited-sentinel caps,
    the ``before`` triple carries the grace-shape values. Callers that
    want the strict per-tier caps regardless of grace should use
    ``/api/entitlement/next-tier-capacity-diff-at?tier=<current>``
    instead.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.next_tier_capacity_diff()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "row": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_capacity_diff: error: %s", exc
        )
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "row": None,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff")
def api_entitlement_previous_tier_capacity_diff():
    """``GET /api/entitlement/previous-tier-capacity-diff`` --
    capacity-only marginal row for the rung immediately below the
    resolved entitlement, in :func:`clawmetry.entitlements.capacity_diff`
    shape.

    Symmetric companion to
    ``/api/entitlement/next-tier-capacity-diff``: that endpoint carries
    the rung-above's capacity delta (upgrade side), this carries the
    rung-below's capacity delta (downgrade side). Useful on a
    downgrade-confirmation card alongside ``/previous-tier-diff``,
    ``/previous-tier-unlocks``, ``/previous-tier-locks``, and
    ``/previous-tier-spec``.

    ``row`` collapses to ``null`` at the floor (no rung below -- the
    resolved entitlement is already at OSS or cloud_free). Never 5xxs:
    a resolver failure short-circuits to the grace-shape envelope so
    the confirmation surface keeps rendering instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        body = ent.previous_tier_capacity_diff()
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "row": body,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_capacity_diff: error: %s", exc
        )
        return jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "row": None,
                "grace": True,
                "enforced": False,
            }
        )

@bp_entitlement.route("/api/entitlement/next-tier-diff")
def api_entitlement_next_tier_diff():
    """GET /api/entitlement/next-tier-diff -- marginal
    :func:`clawmetry.entitlements.upgrade_diff` row from the resolved
    entitlement to the rung immediately above.

    Current-relative convenience for
    ``/api/entitlement/upgrade-diff?target=<next_purchasable_tier>``; the
    upgrade-CTA companion to ``/api/entitlement/next-tier-unlocks``
    (same marginal, ``tier_unlocks`` shape), ``/next-tier-locks``
    (marginal losses), and ``/next-tier-spec`` (full tier row). ``row``
    collapses to ``null`` at the ceiling (resolved entitlement already at
    enterprise -- no rung above to upgrade to). Never 5xxs: a resolver
    failure short-circuits to the grace-shape envelope so the dashboard
    CTA keeps rendering instead of disappearing.
    """
    try:
        from clawmetry import entitlements as _ent
        ent = _ent.get_entitlement()
        body = ent.next_tier_diff()
        return jsonify({
            "current_tier": ent.tier,
            "current_tier_label": _ent.tier_label(ent.tier),
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "row": body,
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        })
    except Exception as exc:
        logger.warning("api_entitlement_next_tier_diff: error: %s", exc)
        return jsonify({"current_tier": "oss", "current_tier_label": "OSS",
                        "current_tier_rank": 0, "row": None, "grace": True, "enforced": False})


@bp_entitlement.route("/api/entitlement/previous-tier-diff")
def api_entitlement_previous_tier_diff():
    """GET /api/entitlement/previous-tier-diff -- marginal
    :func:`clawmetry.entitlements.downgrade_diff` row from the resolved
    entitlement to the rung immediately below.

    Symmetric companion to ``/api/entitlement/next-tier-diff``. ``row``
    collapses to ``null`` at the floor. Never 5xxs.
    """
    try:
        from clawmetry import entitlements as _ent
        ent = _ent.get_entitlement()
        body = ent.previous_tier_diff()
        return jsonify({
            "current_tier": ent.tier,
            "current_tier_label": _ent.tier_label(ent.tier),
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "row": body,
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        })
    except Exception as exc:
        logger.warning("api_entitlement_previous_tier_diff: error: %s", exc)
        return jsonify({"current_tier": "oss", "current_tier_label": "OSS",
                        "current_tier_rank": 0, "row": None, "grace": True, "enforced": False})


def _next_prev_lock_reason_batch_grace_body() -> dict:
    """Fallback envelope for the resolved-tier lock-reason batch routes.
    Shape mirrors the happy path (5-axis empty rows + tier / target
    echo) so a resolver failure never breaks a paywall matrix client-
    side."""
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "grace": True,
        "enforced": False,
    }


def _next_prev_lock_reason_batch(direction: str):
    """Shared handler body for
    ``/api/entitlement/{next,previous}-tier-lock-reason-batch``.

    Current-relative sibling of the ``_next_prev_lock_reason_at_batch``
    handler -- takes no ``tier=`` (the source is the resolved
    entitlement) and walks
    :meth:`Entitlement.next_tier_lock_reason_batch` /
    :meth:`Entitlement.previous_tier_lock_reason_batch` instead of the
    source-parameterised ``_at_batch`` module helpers, matching the
    pattern of ``/next-tier-feature-spec-batch`` vs
    ``/next-tier-feature-spec-at-batch``.

    Mirrors the axis-parsing contract of the ``_at_batch`` handler (at
    least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=``). Body is byte-identical to
    ``/lock-reasons-at-batch?tier=<target>&...`` for the resolved
    ``target = ent.next_purchasable_tier()`` (or
    ``previous_purchasable_tier()``), same as
    ``/next-tier-lock-reason-at-batch`` is byte-identical for
    caller-supplied ``tier``. ``target`` collapses to ``null`` at the
    rung edge (ceiling for ``next``, floor for ``previous``) while
    every supplied item still renders a grace-shape row so the paywall
    matrix's row count stays stable.

    ``direction`` is ``"next"`` or ``"previous"``. Never 5xxs: resolver
    failure short-circuits to the grace-shape envelope so the paywall
    surface stays mute.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason_batch"
    try:
        from clawmetry import entitlements as _ent

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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
        if direction == "next":
            target = ent.next_purchasable_tier()
            batch = ent.next_tier_lock_reason_batch(
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        else:
            target = ent.previous_purchasable_tier()
            batch = ent.previous_tier_lock_reason_batch(
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        batch["current_tier"] = ent.tier
        batch["current_tier_label"] = _ent.tier_label(ent.tier)
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["target"] = target
        batch["target_label"] = _ent.tier_label(target) if target else None
        batch["target_rank"] = _ent.tier_rank(target) if target else None
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        return jsonify(_next_prev_lock_reason_batch_grace_body())


@bp_entitlement.route("/api/entitlement/next-tier-lock-reason-batch")
def api_entitlement_next_tier_lock_reason_batch():
    """``GET /api/entitlement/next-tier-lock-reason-batch?features=a,b
    &runtimes=x,y&channels=N&retention_days=K&nodes=M`` -- current-
    relative sibling of
    ``/api/entitlement/next-tier-lock-reason-at-batch`` and batch
    sibling of ``/api/entitlement/next-tier-lock-reason``.

    Where ``/next-tier-lock-reason`` returns ONE lock sentence for ONE
    item at the rung above the resolved entitlement, this returns per-
    item rows for every supplied item across all 5 axes in ONE round-
    trip. Pairs with ``/next-tier-lock-reason`` the same way
    ``/lock-reasons-batch`` pairs with ``/lock-reason``: scalar ->
    matrix in one call. Fills the lock-reason-axis batch member of the
    resolved-tier ``next_*_batch`` family alongside
    ``/next-tier-feature-spec-batch`` and
    ``/next-tier-runtime-spec-batch``.

    Use case: a paywall "does THIS column of features / runtimes /
    capacity axes unlock at MY next rung?" matrix surface hydrates
    every row off ONE call instead of N calls to
    ``/next-tier-lock-reason`` per axis, without threading the current
    tier through the query args.

    Body is byte-identical to
    ``/next-tier-lock-reason-at-batch?tier=<current>&...`` for every
    source EXCEPT at the free/starter boundary where source-aware
    (``ent.next_purchasable_tier()``) and source-agnostic
    (``_next_purchasable_tier_after(tier)``) diverge -- matches
    ``/next-tier-feature-spec-batch`` vs
    ``/next-tier-feature-spec-at-batch``. Pinned by parity tests so
    the two batch surfaces cannot drift outside that boundary.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied; supply as many
    as you like. ``features=`` / ``runtimes=`` take comma-separated
    tokens (whitespace + duplicates are normalised away; unknown ids
    contribute a grace-shape row). The three capacity axes take a
    single int each; blank / non-int values are treated as "not
    supplied".

    Response shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<resolved label>",
          "current_tier_rank":  <resolved rank>,
          "target":             "<next-above tier id>" | null,
          "target_label":       "<next-above label>" | null,
          "target_rank":        <next-above rank> | null,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason``, ``locked``,
    ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank`` -- the same 8 keys ``/lock-reasons-batch``
    returns.

    At the ceiling (resolved entitlement already at enterprise -- no
    rung above) ``target`` is ``null`` and rows still render for every
    supplied item with ``reason=null`` / ``locked=false`` /
    ``allowed=true`` so callers can render "you're at the top" copy
    without a status-code branch.

    - **400** when no axis is supplied
    - **Never 5xxs**: resolver failure short-circuits to the grace-
      shape envelope with ``target=null`` so the paywall surface stays
      mute.
    """
    return _next_prev_lock_reason_batch("next")


@bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-batch")
def api_entitlement_previous_tier_lock_reason_batch():
    """``GET /api/entitlement/previous-tier-lock-reason-batch?features=a,b
    &runtimes=x,y&channels=N&retention_days=K&nodes=M`` -- symmetric
    downgrade-side companion of ``/next-tier-lock-reason-batch``.

    Same envelope as ``/next-tier-lock-reason-batch``. ``target``
    collapses to ``null`` at the floor (resolved entitlement at
    ``oss`` / ``cloud_free`` -- no rung below) while every supplied
    item still renders a grace-shape row so the downgrade-confirmation
    matrix's row count stays stable.

    Body is byte-identical to
    ``/previous-tier-lock-reason-at-batch?tier=<current>&...`` for
    every source except at the free/starter boundary where source-
    aware and source-agnostic diverge -- matches
    ``/previous-tier-feature-spec-batch`` vs
    ``/previous-tier-feature-spec-at-batch``.

    - **400** when no axis is supplied
    - **Never 5xxs**: grace-shape envelope on resolver failure.
    """
    return _next_prev_lock_reason_batch("previous")


@bp_entitlement.route("/api/entitlement/preview-at-path")
def api_entitlement_preview_at_path():
    """``GET /api/entitlement/preview-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise cumulative-
    state path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/preview-path``: same rung walk, same per-rung
    body, plus a ``perspective_tier`` echo so a pricing-comparison
    walkthrough surface can call ``X_at_path(perspective, from, to)``
    uniformly across the whole ``_at_path`` slot of the preview family
    (alongside ``/preview-at`` and ``/preview-at-batch``, which fill
    the scalar-what-if and batch-what-if slots).

    Body posture matches ``/preview-at``: perspective is validated but
    does not shape the rows. Each row in ``path`` is byte-identical to
    a row from ``/preview-path?from=<from>&to=<to>`` -- pinned by
    parity tests. Perspective acceptance is lenient: ``trial`` IS
    accepted (matching ``/preview-at``).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<preview row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown tier", "which": "to", "to": t}),
                404,
            )
        path = _ent.preview_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_preview_at_path: error: %s", exc)
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route(
    "/api/entitlement/preview-at-path-batch", methods=["POST"]
)
def api_entitlement_preview_at_path_batch():
    """``POST /api/entitlement/preview-at-path-batch`` -- batch sibling of
    ``/preview-at-path``.

    Where ``/preview-at-path`` walks the cumulative-state rungs between
    ONE ``(from, to)`` pair from a hypothetical ``perspective_tier``,
    this walks ONE ``from`` to N candidate ``to`` tiers in ONE round-
    trip from the same hypothetical perspective -- the batch what-if
    sibling of ``/preview-path-batch``, filling the ``_at_path_batch``
    slot for the preview family.

    Body posture matches ``/preview-at``: perspective is validated but
    does not shape rows. Each row in ``tiers[].path`` is byte-identical
    to a row from ``/preview-path-batch`` for the same ``(from, to)``
    pair. Perspective acceptance is lenient: ``trial`` IS accepted.

    Request body::

        {
          "tier": "<perspective tier id>",
          "from": "<tier id>",
          "to":   ["<tier id>", ...]
        }

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<preview row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier`` / ``from`` is missing / blank, or ``to`` is
      missing / empty
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.

    POST rather than GET because ``to`` is a list of tier ids that may
    grow past a comfortable query-string length, matching the sibling
    ``/preview-path-batch`` (which also uses POST+JSON).
    """
    body = request.get_json(silent=True) or {}
    try:
        p_raw = body.get("tier")
        p = str(p_raw or "").strip().lower()
    except Exception:
        p = ""
    try:
        f_raw = body.get("from")
        f = str(f_raw or "").strip().lower()
    except Exception:
        f = ""
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    to_raw = body.get("to")
    if to_raw is None or (isinstance(to_raw, (list, tuple)) and not to_raw):
        return jsonify({"error": "missing or empty to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        try:
            candidates = [str(x) for x in (to_raw or [])]
        except TypeError:
            return jsonify({"error": "to must be a list"}), 400
        batch = _ent.preview_at_path_batch(p, f, candidates)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_preview_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-spec-at-path")
def api_entitlement_feature_spec_at_path():
    """``GET /api/entitlement/feature-spec-at-path?tier=<perspective>
    &from=<id>&to=<id>&feature=<id>`` -- perspective-validated what-if
    sibling of ``/api/entitlement/feature-spec-path``.

    Fills the ``_at_path`` slot of the ``feature-spec`` family, matching
    the already-shipping ``preview_at_path`` / ``tier_catalog_at_path``
    pattern on the ``preview`` / ``tier_catalog`` axes. The perspective
    is validated (400 on missing, 404 on unknown) but does NOT shape the
    ``path`` rows -- the body is byte-identical to
    ``/feature-spec-path?from=<from>&to=<to>&feature=<feature>`` for
    every perspective. Pinned by parity tests so the ``_at_path`` and
    ``_path`` endpoints cannot drift.

    Response shape (mirrors ``/feature-spec-path`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail so a paywall matrix UI can render "at Cloud Pro this feature
    unlocks at Starter" without a second call to ``/entitlement``)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "feature":               "<feature id>",
          "path":                  [<feature_spec_path row>, ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` or ``feature=`` is
      missing / blank
    - **404** when any id is unknown (body carries
      ``which: "tier" | "from" | "to" | "feature"`` so the caller can
      point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with the perspective echoed so the UI keeps
      rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    feat = (request.args.get("feature") or "").strip().lower()
    if not feat:
        return jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        if feat not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feat,
                    }
                ),
                404,
            )
        path = _ent.feature_spec_at_path(tier_in, f, t, feat)
        if path is None:
            path = []
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "feature": feat,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_feature_spec_at_path: error: %s", exc)
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "feature": feat,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-spec-at-path-batch")
def api_entitlement_feature_spec_at_path_batch():
    """``GET /api/entitlement/feature-spec-at-path-batch?tier=<perspective>
    &from=<id>&to=<id>&features=a,b,c`` -- perspective-validated what-if
    batch sibling of ``/api/entitlement/feature-spec-path-batch``.

    Fills the ``_at_path_batch`` slot of the ``feature-spec`` family;
    fixed-perspective, fixed-from, fixed-to, multi-feature companion of
    ``/feature-spec-at-path``. Per-feature body byte-identical to
    ``/feature-spec-path-batch`` for the same ``(from, to, features)``
    triple -- scalar / batch no-drift contract.

    Response shape (mirrors ``/feature-spec-path-batch`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "features": [
            {"feature": "<id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=``, ``to=`` is missing / blank, or
      ``features=`` is missing / empty after normalisation
    - **404** when any tier id is unknown (body carries
      ``which: "tier" | "from" | "to"``)
    - Unknown feature ids do NOT 404 the call -- they are echoed in
      ``unknown[]`` so a partially-bad caller still gets paths back for
      the valid ids alongside a list of what was dropped, matching
      every other ``*_path_batch`` sibling's posture.
    - **Never 5xxs**: a synthesis failure short-circuits to a grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        batch = _ent.feature_spec_at_path_batch(tier_in, f, t, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_feature_spec_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "features": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-spec-at-path")
def api_entitlement_tier_spec_at_path():
    """``GET /api/entitlement/tier-spec-at-path?tier=<perspective>
    &from=<id>&to=<id>`` -- perspective-validated what-if sibling of
    ``/api/entitlement/tier-spec-path``.

    Fills the ``_at_path`` slot of the ``tier-spec`` family, matching
    the already-shipping ``preview_at_path`` / ``tier_catalog_at_path``
    / ``feature_spec_at_path`` / ``runtime_spec_at_path`` pattern. The
    perspective is validated (400 on missing, 404 on unknown) but does
    NOT shape the ``path`` rows -- the body is byte-identical to
    ``/tier-spec-path?from=<from>&to=<to>`` for every perspective.
    Pinned by parity tests so the ``_at_path`` and ``_path`` endpoints
    cannot drift.

    Response shape (mirrors ``/tier-spec-path`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail so a paywall matrix UI can render "at Cloud Pro, here is the
    spec ladder from Starter to Enterprise" without a second call to
    ``/entitlement``)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<tier_spec_path row>, ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries
      ``which: "tier" | "from" | "to"`` so the caller can point at the
      offender)
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with the perspective echoed so the UI keeps
      rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        path = _ent.tier_spec_at_path(tier_in, f, t)
        if path is None:
            path = []
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_spec_at_path: error: %s", exc)
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-spec-at-path-batch")
def api_entitlement_tier_spec_at_path_batch():
    """``GET /api/entitlement/tier-spec-at-path-batch?tier=<perspective>
    &from=<id>&to=a,b,c`` -- perspective-validated what-if batch sibling
    of ``/api/entitlement/tier-spec-path-batch``.

    Fills the ``_at_path_batch`` slot of the ``tier-spec`` family;
    fixed-perspective, fixed-from, multi-destination companion of
    ``/tier-spec-at-path``. Per-destination body byte-identical to
    ``/tier-spec-path-batch`` for the same ``(from, to_tiers)`` pair --
    scalar / batch no-drift contract.

    Response shape (mirrors ``/tier-spec-path-batch`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier_spec_path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - Unknown destination ids do NOT 404 the call -- they are echoed in
      ``unknown[]`` so a partially-bad caller still gets paths back for
      the valid ids alongside a list of what was dropped, matching
      every other ``*_at_path_batch`` sibling's posture.
    - **Never 5xxs**: a synthesis failure short-circuits to a grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_spec_at_path_batch(tier_in, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_spec_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog-at-path")
def api_entitlement_runtime_catalog_at_path():
    """``GET /api/entitlement/runtime-catalog-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise runtime-catalog
    path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/runtime-catalog-path``: same rung walk, same
    per-rung body, plus a ``perspective_tier`` echo so a pricing-
    comparison walkthrough surface can call
    ``X_at_path(perspective, from, to)`` uniformly across the whole
    ``_at_path`` slot of the runtime-catalog family (alongside
    ``/runtime-catalog-at`` and ``/runtime-catalog-at-batch``, which
    fill the scalar-what-if and batch-what-if slots).

    Body posture matches ``/runtime-catalog-at``: perspective is
    validated but does not shape the rows. Each row in ``path`` is
    byte-identical to a row from
    ``/runtime-catalog-path?from=<from>&to=<to>`` -- pinned by parity
    tests. Perspective acceptance is lenient: ``trial`` IS accepted
    (matching every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<runtime-catalog-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.runtime_catalog_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_catalog_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog-at-path-batch")
def api_entitlement_runtime_catalog_at_path_batch():
    """``GET /api/entitlement/runtime-catalog-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/runtime-catalog-at-path``.

    Where ``/runtime-catalog-at-path`` walks the runtime-catalog rungs
    between ONE ``(from, to)`` pair from a hypothetical
    ``perspective_tier``, this walks ONE ``from`` to N candidate ``to``
    tiers in ONE round-trip from the same hypothetical perspective --
    the batch what-if sibling of ``/runtime-catalog-path-batch``,
    filling the ``_at_path_batch`` slot for the runtime-catalog family.

    Body posture matches ``/runtime-catalog-at``: perspective is
    validated but does not shape rows. Each row in ``tiers[].path`` is
    byte-identical to a row from ``/runtime-catalog-path-batch`` for
    the same ``(from, to)`` pair. Perspective acceptance is lenient:
    ``trial`` IS accepted (matching every other ``_at`` sibling). The
    GET+CSV query surface matches the ``/runtime-catalog-path-batch``
    sibling rather than the POST+JSON ``/preview-at-path-batch`` shape
    -- keeps the runtime-catalog family internally consistent.

    Response shape (mirrors ``/runtime-catalog-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<runtime-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.runtime_catalog_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_runtime_catalog_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-catalog-at-path")
def api_entitlement_channel_catalog_at_path():
    """``GET /api/entitlement/channel-catalog-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise channel-catalog
    path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/channel-catalog-path``: same rung walk, same
    per-rung body, plus a ``perspective_tier`` echo so a pricing-
    comparison walkthrough surface can call
    ``X_at_path(perspective, from, to)`` uniformly across the whole
    ``_at_path`` slot of the channel-catalog family (alongside
    ``/channel-catalog-at`` and ``/channel-catalog-at-batch``, which
    fill the scalar-what-if and batch-what-if slots). Family-complete
    twin of ``/feature-catalog-at-path`` / ``/runtime-catalog-at-path``
    / ``/tier-catalog-at-path``.

    Body posture matches ``/channel-catalog-at``: perspective is
    validated but does not shape the rows. Each row in ``path`` is
    byte-identical to a row from
    ``/channel-catalog-path?from=<from>&to=<to>`` -- pinned by parity
    tests. Perspective acceptance is lenient: ``trial`` IS accepted
    (matching every other ``_at`` sibling).

    Because every chat-channel adapter is FREE at every tier (the
    ``channels`` capacity axis governs how many concurrent channels
    each plan admits, not which adapters unlock), each rung's inner
    ``channels`` list is byte-identical to ``/channel-catalog`` --
    inherited from the delegate, pinned by parity tests so a
    walkthrough UI can render the channel column off the same
    row-renderer as the feature and runtime columns.

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<channel-catalog-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-walkthrough surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.channel_catalog_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_catalog_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/channel-catalog-at-path-batch")
def api_entitlement_channel_catalog_at_path_batch():
    """``GET /api/entitlement/channel-catalog-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/channel-catalog-at-path``.

    Where ``/channel-catalog-at-path`` walks the channel-catalog rungs
    between ONE ``(from, to)`` pair from a hypothetical
    ``perspective_tier``, this walks ONE ``from`` to N candidate ``to``
    tiers in ONE round-trip from the same hypothetical perspective --
    the batch what-if sibling of ``/channel-catalog-path-batch``,
    filling the ``_at_path_batch`` slot for the channel-catalog family
    (last remaining ``_at*`` cell on the channel-catalog axis, twin of
    ``/feature-catalog-at-path-batch`` and
    ``/runtime-catalog-at-path-batch``).

    Body posture matches ``/channel-catalog-at``: perspective is
    validated but does not shape rows. Each row in ``tiers[].path`` is
    byte-identical to a row from ``/channel-catalog-path-batch`` for
    the same ``(from, to)`` pair. Perspective acceptance is lenient:
    ``trial`` IS accepted (matching every other ``_at`` sibling).

    Because every chat-channel adapter is FREE at every tier, each
    rung's inner ``channels`` list is byte-identical to
    ``/channel-catalog`` -- inherited from the delegate, pinned by
    parity tests so a walkthrough UI can render the channel column
    off the same row-renderer as the feature and runtime columns.

    Response shape (mirrors ``/channel-catalog-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<channel-catalog-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.channel_catalog_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_catalog_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/lock-reason-at-path")
def api_entitlement_lock_reason_at_path():
    """``GET /api/entitlement/lock-reason-at-path?tier=<perspective>
    &from=<id>&to=<id>&<axis>=<id>`` -- perspective-validated what-if
    sibling of ``/api/entitlement/lock-reason-path``.

    Fills the ``_at_path`` slot of the ``lock-reason`` family, matching
    the already-shipping ``feature-spec-at-path`` /
    ``runtime-spec-at-path`` / ``tier-spec-at-path`` /
    ``feature-catalog-at-path`` / ``runtime-catalog-at-path`` /
    ``tier-catalog-at-path`` / ``capacity-diff-at-path`` /
    ``preview-at-path`` pattern on the eight other axes -- so every
    ``*-path`` endpoint now has a perspective-validated ``_at_path``
    sibling and a paywall walkthrough UI can call
    ``.../X-at-path?tier=<perspective>&from=<f>&to=<t>&...`` uniformly
    across the whole ``_at_path`` family without special-casing the
    lock-reason axis.

    The perspective is validated (400 on missing, 404 on unknown) but
    does NOT shape the ``path`` rows -- the body is byte-identical to
    ``/lock-reason-path?from=<f>&to=<t>&<axis>=<id>`` for every
    perspective. Pinned by parity tests so the ``_at_path`` and
    ``_path`` endpoints cannot drift.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied -- the same axis
    dispatcher as ``/lock-reason-path``. Runtime aliases
    (``claude-code`` -> ``claude_code``) are canonicalised via
    :func:`clawmetry.entitlements.canonical_runtime`.

    Response shape (mirrors ``/lock-reason-path`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail so a paywall matrix UI can render "at Cloud Pro this lock-row
    unlocks at Starter" without a second call to ``/entitlement``)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "key":                   "<echoed item id>",
          "kind":                  "feature" | "runtime" | "channels" |
                                   "retention_days" | "nodes",
          "path":                  [<lock_reason_path row>, ...],
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank,
      when no axis is supplied, or when more than one axis is supplied
    - **404** when any tier id is unknown (body carries
      ``which: "tier" | "from" | "to"``), or when a feature / runtime
      id is unknown, or when a capacity value is missing / non-int /
      non-positive
    - **Never 5xxs**: a resolver failure short-circuits to the grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400

    feature = (request.args.get("feature") or "").strip().lower()
    runtime_in = (request.args.get("runtime") or "").strip().lower()
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
        bool(runtime_in),
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

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )

        if feature:
            item, kind, echoed_key = feature, "feature", feature
        elif runtime_in:
            canon = _ent.canonical_runtime(runtime_in)
            item, kind, echoed_key = (
                canon or runtime_in,
                "runtime",
                canon or runtime_in,
            )
        elif channels_present:
            if not channels_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "which": "item",
                            "from": f,
                            "to": t,
                            "key": channels_raw,
                            "kind": "channels",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = (
                str(channels_n),
                "channels",
                str(channels_n),
            )
        elif retention_present:
            if not retention_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "which": "item",
                            "from": f,
                            "to": t,
                            "key": retention_raw,
                            "kind": "retention_days",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = (
                str(retention_n),
                "retention_days",
                str(retention_n),
            )
        else:
            if not nodes_ok:
                return (
                    jsonify(
                        {
                            "error": "unknown tier or item",
                            "which": "item",
                            "from": f,
                            "to": t,
                            "key": nodes_raw,
                            "kind": "nodes",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = str(nodes_n), "nodes", str(nodes_n)

        path = _ent.lock_reason_at_path(tier_in, f, t, item, kind=kind)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier or item",
                        "which": "item",
                        "from": f,
                        "to": t,
                        "key": echoed_key,
                        "kind": kind,
                    }
                ),
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "key": echoed_key,
                "kind": kind,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_lock_reason_at_path: error: %s", exc)
        if feature:
            echoed_key, kind = feature, "feature"
        elif runtime_in:
            echoed_key, kind = runtime_in, "runtime"
        elif channels_present:
            echoed_key, kind = channels_raw, "channels"
        elif retention_present:
            echoed_key, kind = retention_raw, "retention_days"
        else:
            echoed_key, kind = nodes_raw, "nodes"
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "key": echoed_key,
                "kind": kind,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/lock-reason-at-path-batch")
def api_entitlement_lock_reason_at_path_batch():
    """``GET /api/entitlement/lock-reason-at-path-batch?tier=<perspective>
    &from=<id>&to=<id>&features=a,b,c&runtimes=x,y&channels=N
    &retention_days=K&nodes=M`` -- perspective-validated what-if batch
    sibling of ``/api/entitlement/lock-reason-path-batch``.

    Fills the ``_at_path_batch`` slot of the ``lock-reason`` family;
    fixed-perspective, fixed-from, fixed-to, multi-axis companion of
    ``/lock-reason-at-path``. Per-axis body byte-identical to
    ``/lock-reason-path-batch`` for the same ``(from, to, features,
    runtimes, channels, retention_days, nodes)`` tuple -- scalar / batch
    no-drift contract.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (matches
    ``/lock-reason-path-batch``); supply as many as you like. Runtime
    aliases are canonicalised (``claude-code`` -> ``claude_code``) and
    aliases that collapse to a canonical id already in the response are
    silently de-duplicated. Unknown ids do NOT 404 the call -- they are
    echoed in ``unknown.features`` / ``unknown.runtimes`` carrying the
    supplied alias.

    Response shape (mirrors ``/lock-reason-path-batch`` plus a
    ``perspective_tier`` echo and the standard ``_at*`` resolver-context
    tail)::

        {
          "perspective_tier":      "<id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "features": [{"key": "<id>", "path": [...]}, ...],
          "runtimes": [{"key": "<canonical id>", "path": [...]}, ...],
          "channels":       {"key": "<n>", "path": [...]} | None,
          "retention_days": {"key": "<n>", "path": [...]} | None,
          "nodes":          {"key": "<n>", "path": [...]} | None,
          "unknown": {"features": [...], "runtimes": [...]},
          "current_tier":          "...",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=`` / ``from=`` / ``to=`` is missing / blank,
      or when no axis is supplied
    - **404** when any tier id is unknown (body carries
      ``which: "tier" | "from" | "to"``)
    - Unknown feature / runtime ids do NOT 404 the call -- they are
      echoed in ``unknown[]`` so a partially-bad caller still gets paths
      back for the valid ids alongside a list of what was dropped
    - **Never 5xxs**: a synthesis failure short-circuits to a grace-
      shape envelope with the perspective echoed.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "which": "tier",
                        "tier": tier_in,
                    }
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
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

        batch = _ent.lock_reason_at_path_batch(
            tier_in,
            f,
            t,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "unknown": {"features": [], "runtimes": []},
            }
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
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "features": batch.get("features", []),
                "runtimes": batch.get("runtimes", []),
                "channels": batch.get("channels"),
                "retention_days": batch.get("retention_days"),
                "nodes": batch.get("nodes"),
                "unknown": batch.get(
                    "unknown", {"features": [], "runtimes": []}
                ),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_lock_reason_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "direction": "identity" if f == t else "upgrade",
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "unknown": {"features": [], "runtimes": []},
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-at-path")
def api_entitlement_tier_unlocks_at_path():
    """``GET /api/entitlement/tier-unlocks-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise marginal-
    unlocks path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/tier-unlocks-path``: same rung walk, same
    per-rung marginal-unlocks body, plus a ``perspective_tier`` echo
    so a pricing-comparison walkthrough surface can call
    ``X_at_path(perspective, from, to)`` uniformly across the whole
    ``_at_path`` slot of the ``tier_unlocks`` family (alongside
    ``/tier-unlocks-at`` and ``/tier-unlocks-at-batch``, which fill the
    scalar-what-if and batch-what-if slots). Unlocks-only mirror of
    ``/capacity-diff-at-path`` -- same posture, marginal-unlocks rows
    instead of capacity rows.

    Body posture matches ``/tier-unlocks-at`` and every other
    ``_at_path`` sibling: perspective is validated but does not shape
    the rows. Each row in ``path`` is byte-identical to a row from
    ``/tier-unlocks-path?from=<from>&to=<to>`` -- pinned by parity
    tests. Perspective acceptance is lenient: ``trial`` IS accepted
    (matching every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<tier-unlocks-path row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so an
      upgrade-comparison surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.tier_unlocks_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_unlocks_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-locks-at-path")
def api_entitlement_tier_locks_at_path():
    """``GET /api/entitlement/tier-locks-at-path?tier=<perspective>
    &from=<from>&to=<to>`` -- arbitrary-endpoint stepwise marginal-
    locks path between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    Marginal-loss mirror of ``/tier-unlocks-at-path``. What-if sibling
    of ``/tier-locks-path``: same rung walk, same per-rung marginal-
    losses body, plus a ``perspective_tier`` echo. Locks-only mirror
    of ``/capacity-diff-at-path``.

    Body posture matches ``/tier-locks-at``: perspective is validated
    but does not shape the rows. Each row in ``path`` is byte-
    identical to a row from ``/tier-locks-path?from=<from>&to=<to>``
    -- pinned by parity tests. Perspective acceptance is lenient:
    ``trial`` IS accepted.

    Response shape mirrors ``/tier-unlocks-at-path`` with ``path`` rows
    carrying ``lost_features`` / ``lost_runtimes`` instead of
    ``features`` / ``runtimes``.

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"``)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so a
      downgrade-warning surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.tier_locks_at_path(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_locks_at_path: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-unlocks-at-path-batch")
def api_entitlement_tier_unlocks_at_path_batch():
    """``GET /api/entitlement/tier-unlocks-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/tier-unlocks-at-path``.

    Where ``/tier-unlocks-at-path`` walks the marginal-unlocks rungs
    between ONE ``(from, to)`` pair from a hypothetical
    ``perspective_tier``, this walks ONE ``from`` to N candidate ``to``
    tiers in ONE round-trip from the same hypothetical perspective --
    the batch what-if sibling of ``/tier-unlocks-path-batch``, filling
    the ``_at_path_batch`` slot for the ``tier_unlocks`` family.
    Multi-destination cousin of ``/capacity-diff-at-path-batch`` (same
    fan-out shape, marginal-unlocks body instead of capacity body).

    Body posture matches ``/tier-unlocks-at``: perspective is validated
    but does not shape rows. Each row in ``tiers[].path`` is byte-
    identical to a row from ``/tier-unlocks-path-batch`` for the same
    ``(from, to)`` pair. Perspective acceptance is lenient: ``trial``
    IS accepted (matching every other ``_at`` sibling).

    Response shape (mirrors ``/tier-unlocks-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier-unlocks-path row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]``, matching every other ``*_path_batch`` sibling's
    posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_unlocks_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_unlocks_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-locks-at-path-batch")
def api_entitlement_tier_locks_at_path_batch():
    """``GET /api/entitlement/tier-locks-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c`` -- batch sibling of
    ``/tier-locks-at-path``.

    Marginal-loss mirror of ``/tier-unlocks-at-path-batch``. Batch
    what-if sibling of ``/tier-locks-path-batch``. Locks-only cousin
    of ``/capacity-diff-at-path-batch``.

    Body posture matches ``/tier-locks-at``: perspective is validated
    but does not shape rows. Each row in ``tiers[].path`` is byte-
    identical to a row from ``/tier-locks-path-batch``. Perspective
    acceptance is lenient: ``trial`` IS accepted.

    Response shape mirrors ``/tier-unlocks-at-path-batch`` with
    per-rung ``path`` rows carrying ``lost_features`` /
    ``lost_runtimes`` instead of ``features`` / ``runtimes``.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids
    - **Never 5xxs**.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_locks_at_path_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_locks_at_path_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-path-at")
def api_entitlement_tier_path_at():
    """``GET /api/entitlement/tier-path-at?tier=<perspective>&from=<id>
    &to=<id>`` -- arbitrary-endpoint stepwise marginal ``tier_diff`` path
    between any two tiers, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/tier-path``: same rung walk, same per-rung full
    marginal ``tier_diff`` body (``added_features`` + ``lost_features`` +
    ``added_runtimes`` + ``lost_runtimes`` + ``capacity_changes``), plus
    a ``perspective_tier`` echo so a pricing-comparison walkthrough
    surface can call ``X_at(perspective, from, to)`` uniformly across
    the whole ``tier_path`` family (alongside ``/tier-path`` and
    ``/tier-path-batch`` which fill the current-perspective scalar and
    batch slots). All-slices companion of ``/capacity-diff-at-path``
    (capacity-only), ``/tier-unlocks-at-path`` / ``/tier-locks-at-path``
    (grant / loss slice) so a UI that already renders one member of the
    ``_at_path`` family can render every rung's full marginal diff via
    the same posture and envelope.

    Body posture matches ``/capacity-diff-at-path`` and every other
    ``_at_path`` sibling: perspective is validated but does not shape
    the rows. Each row in ``path`` is byte-identical to a row from
    ``/tier-path?from=<from>&to=<to>`` -- pinned by parity tests.
    Perspective acceptance is lenient: ``trial`` IS accepted (matching
    every other ``_at`` sibling).

    Response shape::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "to":                    "<tier id>",
          "to_label":              "...",
          "to_rank":               <int>,
          "direction":             "upgrade" | "downgrade" | "lateral" | "identity",
          "path":                  [<tier_diff row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so a
      pricing-comparison surface keeps rendering instead of breaking.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    t = (request.args.get("to") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    if not t:
        return jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.tier_path_at(p, f, t)
        if path is None:
            return (
                jsonify(
                    {
                        "error": "unknown tier",
                        "tier": p,
                        "from": f,
                        "to": t,
                    }
                ),
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
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": from_rank,
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": to_rank,
                "direction": direction,
                "path": path,
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_path_at: error: %s", exc
        )
        return (
            jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )


@bp_entitlement.route("/api/entitlement/tier-path-at-batch")
def api_entitlement_tier_path_at_batch():
    """``GET /api/entitlement/tier-path-at-batch?tier=<perspective>
    &from=<id>&to=a,b,c`` -- batch sibling of ``/tier-path-at``.

    Where ``/tier-path-at`` walks the marginal ``tier_diff`` rungs
    between ONE ``(from, to)`` pair from a hypothetical
    ``perspective_tier``, this walks ONE ``from`` to N candidate ``to``
    tiers in ONE round-trip from the same hypothetical perspective --
    the batch what-if sibling of ``/tier-path-batch``, filling the
    ``_at_batch`` slot of the ``tier_path`` family.

    Body posture matches ``/tier-path-at``: perspective is validated
    but does not shape rows. Each row in ``tiers[].path`` is byte-
    identical to a row from ``/tier-path-batch`` for the same
    ``(from, to)`` pair. Perspective acceptance is lenient: ``trial``
    IS accepted (matching every other ``_at`` sibling). The GET+CSV
    query surface matches the ``/tier-path-batch`` sibling rather than
    the POST+JSON ``/preview-at-path-batch`` shape -- keeps the
    ``tier_path`` family internally consistent.

    Response shape (mirrors ``/tier-path-batch`` plus the
    ``perspective_tier`` echo and the resolver-context tail every
    ``_at*`` endpoint carries)::

        {
          "perspective_tier":      "<tier id>",
          "perspective_tier_rank": <int>,
          "from":                  "<tier id>",
          "from_label":            "...",
          "from_rank":             <int>,
          "tiers": [
            {
              "to":        "<tier id>",
              "to_label":  "...",
              "to_rank":   <int>,
              "direction": "upgrade" | "downgrade" | "lateral" | "identity",
              "path":      [<tier_diff row>, ...],
            },
            ...
          ],
          "unknown":               ["bogus_id", ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching every
    other ``*_path_batch`` sibling's posture.

    - **400** when ``tier=`` or ``from=`` is missing / blank, or ``to=``
      is missing / empty after normalisation
    - **404** when ``tier`` or ``from`` is unknown (body carries
      ``which: "tier" | "from"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    p = (request.args.get("tier") or "").strip().lower()
    f = (request.args.get("from") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    if not f:
        return jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _parse_csv_arg("to")
        if not targets:
            return jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_path_at_batch(p, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        try:
            ent = _ent.get_entitlement()
            current_tier = getattr(ent, "tier", "oss") or "oss"
            grace = bool(getattr(ent, "grace", True))
        except Exception:
            current_tier = "oss"
            grace = True
        try:
            enforced = bool(_ent.is_enforced())
        except Exception:
            enforced = False
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": _ent.tier_rank(p),
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": current_tier,
                "current_tier_rank": _ent.tier_rank(current_tier),
                "grace": grace,
                "enforced": enforced,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tier_path_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "perspective_tier": p,
                "perspective_tier_rank": 0,
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/feature-catalog")
def api_entitlement_feature_catalog():
    """``GET /api/entitlement/feature-catalog`` -- bare sibling of
    ``/api/entitlement/feature-catalog-at``: returns the full feature
    catalogue for the *resolved* entitlement, wrapped with the same
    envelope keys the ``-at`` sibling uses so a pricing UI can swap
    between "current" and "hypothetical" without reshaping.

    Same rows as ``/api/features``; this alias lives under
    ``/api/entitlement/`` so a client hydrating every catalog variant
    (bare, ``-at``, ``-at-batch``, ``-path``, ...) can do it off one
    prefix instead of mixing ``/api/features`` with
    ``/api/entitlement/feature-catalog-at``.

    Response shape::

        {
          "tier":     "<resolved tier id>",
          "features": [<catalog_row>, ...],   # from feature_catalog()
          "grace":    <bool>,                 # resolver is in grace mode
          "enforced": <bool>,                 # negation of grace, for symmetry
        }

    - **Never 5xxs**: helper failures short-circuit to the OSS-free
      envelope so the pricing UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": ent.tier,
                "features": _ent.feature_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_feature_catalog: error: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "features": [],
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/runtime-catalog")
def api_entitlement_runtime_catalog():
    """``GET /api/entitlement/runtime-catalog`` -- bare sibling of
    ``/api/entitlement/runtime-catalog-at``: returns the full runtime
    catalogue for the *resolved* entitlement, wrapped with the same
    envelope keys the ``-at`` sibling uses so a pricing UI can swap
    between "current" and "hypothetical" without reshaping.

    Same rows as ``/api/runtimes``; this alias lives under
    ``/api/entitlement/`` so a client hydrating every catalog variant
    can do it off one prefix.

    Response shape::

        {
          "tier":     "<resolved tier id>",
          "runtimes": [<catalog_row>, ...],   # from runtime_catalog()
          "grace":    <bool>,
          "enforced": <bool>,
        }

    - **Never 5xxs**: helper failures short-circuit to the OSS-free
      envelope so the pricing UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": ent.tier,
                "runtimes": _ent.runtime_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_runtime_catalog: error: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "runtimes": [],
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-catalog")
def api_entitlement_channel_catalog():
    """``GET /api/entitlement/channel-catalog`` -- catalogue sibling of
    :func:`api_entitlement_feature_catalog` /
    :func:`api_entitlement_runtime_catalog` for the chat-channel axis.

    Returns every chat-channel adapter ClawMetry can observe (see
    :data:`clawmetry.entitlements.ALL_CHANNELS`, kept in lockstep with
    ``clawmetry.sync._CHANNEL_DIRS``). Every row is unlocked -- there is
    no paid-channel tier; the ``channels`` capacity axis
    (:func:`min_tier_for_channel_count` and the ``channels=`` arg on the
    aggregate helpers) governs *how many* concurrent channels each plan
    admits, not *which* adapters unlock. That posture lets a pricing page
    render "all N chat channels included in every plan" off one call
    instead of hard-coding the adapter list client-side.

    Response shape mirrors ``/api/entitlement/feature-catalog`` and
    ``/api/entitlement/runtime-catalog``::

        {
          "tier":     "<resolved tier id>",
          "channels": [<catalog_row>, ...],   # from channel_catalog()
          "grace":    <bool>,
          "enforced": <bool>,
        }

    - **Never 5xxs**: helper failures short-circuit to the OSS-free
      envelope so the pricing UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": ent.tier,
                "channels": _ent.channel_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_channel_catalog: error: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "channels": [],
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/channel-catalog-at")
def api_entitlement_channel_catalog_at():
    """``GET /api/entitlement/channel-catalog-at?tier=<id>`` -- what-if
    sibling of ``/api/entitlement/channel-catalog``.

    Returns the full chat-channel catalogue with every row computed as if
    the install were on ``tier``. Mirrors
    ``/api/entitlement/feature-catalog-at`` and
    ``/api/entitlement/runtime-catalog-at`` for the channel axis so a
    pricing-comparison matrix UI can swap "current state" against "if I
    were on Cloud Pro" using ONE row-renderer across all three axes.

    Every chat channel is FREE (there is no paid-channel tier -- the
    ``channels`` capacity axis governs how many concurrent channels each
    plan admits, not which adapters unlock), so every row comes back
    unlocked regardless of the perspective tier. That parity IS the
    answer: the UI can render "all N chat channels included at every
    plan" without having to hard-code the posture client-side.

    Response shape::

        {
          "tier":     "<perspective tier id>",
          "channels": [<catalog_row>, ...],   # from channel_catalog_at()
        }

    Each ``channels`` list is byte-identical to
    :func:`entitlements.channel_catalog_at` for the same tier -- a
    parity test pins this so the endpoint cannot drift from the helper.

    - **400** when ``tier=`` is missing / blank
    - **404** when the id is not a known tier
    - **Never 5xxs**: a resolver failure short-circuits to the OSS-free
      fallback so the catalogue still renders.
    """
    raw = request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.channel_catalog_at(tier)
        if body is None:
            return jsonify({"error": "unknown tier", "tier": tier}), 404
        return jsonify({"tier": tier, "channels": body})
    except Exception as exc:
        logger.warning("api_entitlement_channel_catalog_at: error: %s", exc)
        return jsonify({"error": "channel-catalog-at failed"}), 500


@bp_entitlement.route("/api/entitlement/channel-catalog-at-batch")
def api_entitlement_channel_catalog_at_batch():
    """``GET /api/entitlement/channel-catalog-at-batch?tiers=a,b,c`` --
    batch what-if sibling of ``/api/entitlement/channel-catalog-at``.

    Channel-axis twin of ``/feature-catalog-at-batch`` /
    ``/runtime-catalog-at-batch``: same envelope shape, same
    normalisation semantics, same unknown-echo posture. Together the
    three batches let a pricing-comparison matrix UI hydrate every
    feature + runtime + channel column at every hypothetical rung off
    THREE calls instead of 3 * N calls to the scalar what-if catalog
    endpoints.

    Each ``tiers[].channels`` list is byte-identical to the body of
    ``/channel-catalog-at?tier=<tier>`` for the same tier -- pinned by
    the parity tests.

    Response shape mirrors ``/feature-catalog-at-batch`` /
    ``/runtime-catalog-at-batch`` with ``features`` / ``runtimes``
    renamed to ``channels``::

        {
          "tiers": [
            {"tier": "<id>", "tier_label": ..., "tier_rank": ..., "channels": [...]},
            ...
          ],
          "unknown":           ["bogus_id", ...],
          "current_tier":      "<resolved id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``tiers=`` is missing / empty after normalisation
    - **200** with bucketed unknowns for unknown tier ids
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.
    """
    tiers = _parse_csv_arg("tiers")
    if not tiers:
        return jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.channel_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_channel_catalog_at_batch: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tier-catalog")
def api_entitlement_tier_catalog():
    """``GET /api/entitlement/tier-catalog`` -- bare sibling of
    ``/api/entitlement/tier-catalog-at``: returns the full tier ladder
    for the *resolved* entitlement, wrapped with the same envelope
    keys the ``-at`` sibling uses so a pricing UI can swap between
    "current" and "hypothetical" without reshaping.

    Same rows as ``/api/tiers`` (with ``current`` mirrored into
    ``tier`` to match the ``-at`` sibling); this alias lives under
    ``/api/entitlement/`` so a client hydrating every catalog variant
    can do it off one prefix.

    Response shape::

        {
          "tier":     "<resolved tier id>",   # matches _at sibling key
          "tiers":    [<catalog_row>, ...],   # from tier_catalog()
          "grace":    <bool>,
          "enforced": <bool>,
        }

    - **Never 5xxs**: helper failures short-circuit to the OSS-floor
      envelope so the pricing UI keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return jsonify(
            {
                "tier": ent.tier,
                "tiers": _ent.tier_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        logger.warning("api_entitlement_tier_catalog: error: %s", exc)
        return jsonify(
            {
                "tier": "oss",
                "tiers": [],
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-channel-catalog-at")
def api_entitlement_next_tier_channel_catalog_at():
    """``GET /api/entitlement/next-tier-channel-catalog-at?tier=<source>``
    -- source-anchored channel-axis catalog sibling of
    ``/api/entitlement/next-tier-spec-at``: the full
    :func:`clawmetry.entitlements.channel_catalog_at`-shape catalogue for
    every chat-channel adapter evaluated on the rung above the
    caller-supplied ``tier``.

    Source-anchored companion of ``/next-tier-channel-catalog``
    (resolver-anchored, no-arg) and channel-axis catalog analogue of
    ``/next-tier-feature-spec-at`` / ``/next-tier-runtime-spec-at``
    (which project onto a single feature / runtime). Lets an
    upgrade-preview panel walking an explicit source rung (a pricing
    comparison matrix, an "at each rung" table) hydrate the whole
    channel matrix at the next rung off ONE round-trip without threading
    the target tier through query args or first fetching ``/entitlement``
    for ``next_tier``.

    Response shape::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "channels":     [<catalog_row>, ...],   # empty at ceiling
        }

    Inner ``channels`` matches
    ``/channel-catalog-at?tier=<target>`` byte-for-byte when ``target``
    is populated -- a parity test pins this so the projection cannot
    drift from the sibling.

    Every chat channel is FREE at every tier (the ``channels`` capacity
    axis governs how many concurrent channels each plan admits, not
    which adapters unlock), so every row comes back ``free=True`` /
    ``locked=False`` / ``entitled=True`` regardless of the source or
    target rung. That parity IS the answer: the panel can render "all N
    chat channels included at every plan" off ONE call without
    hard-coding that posture client-side.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``channels`` collapses to ``[]`` at the ceiling (no rung
    strictly above -- enterprise as source) -- the surface stays 200 so
    callers can render "you're at the top" copy without a status-code
    branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``channels=[]``
      on the same 200 envelope so the preview surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        rows = _ent.next_tier_channel_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_channel_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "channels": [],
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog-at")
def api_entitlement_previous_tier_channel_catalog_at():
    """``GET /api/entitlement/previous-tier-channel-catalog-at?tier=<source>``
    -- symmetric downgrade-side companion of
    ``/next-tier-channel-catalog-at``: the full
    :func:`clawmetry.entitlements.channel_catalog_at`-shape catalogue for
    every chat-channel adapter evaluated on the rung below the
    caller-supplied ``tier``.

    Source-anchored companion of ``/previous-tier-channel-catalog``
    (resolver-anchored, no-arg). Lets a downgrade-confirmation card
    walking an explicit source rung render "which channels stay when I
    step down from THIS tier?" off ONE round-trip.

    Response shape matches ``/next-tier-channel-catalog-at``
    byte-for-byte (``tier``, ``tier_label``, ``tier_rank``, ``target``,
    ``target_label``, ``target_rank``, ``channels``). Inner ``channels``
    matches ``/channel-catalog-at?tier=<target>`` byte-for-byte when
    ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``channels`` collapses to ``[]`` at the floor (``oss`` /
    ``cloud_free`` as source) and ``target`` / ``target_label`` /
    ``target_rank`` to ``null``.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``channels=[]``
      on the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        rows = _ent.previous_tier_channel_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_channel_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "channels": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-channel-catalog-at-batch")
def api_entitlement_next_tier_channel_catalog_at_batch():
    """``GET /api/entitlement/next-tier-channel-catalog-at-batch`` --
    batch sibling of ``/api/entitlement/next-tier-channel-catalog-at``:
    one ``next-tier-channel-catalog-at`` envelope per purchasable source
    tier, in one round-trip.

    Channel-axis catalog analogue of
    ``/api/entitlement/next-tier-spec-at-batch`` (full
    :func:`tier_spec_at` row per source),
    ``/next-tier-diff-at-batch`` (marginal :func:`tier_diff` per
    source), and the sibling ``/next-tier-feature-spec-at-batch`` /
    ``/next-tier-runtime-spec-at-batch`` axes. Lets a pricing-
    comparison matrix UI render the "chat channels included at the
    rung above each rung" column off **one** call instead of N calls
    to ``/next-tier-channel-catalog-at``.

    No query params. The source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded), matching
    the sibling ``_at_batch`` endpoints, so the batches fold into the
    same pricing-page table byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-channel-catalog-at?tier=<source>`` for
    that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``channels``). The
    inner ``channels`` matches
    ``/channel-catalog-at?tier=<target>`` byte-for-byte when
    ``target`` is populated. At the source-side ceiling (``enterprise``
    as source) the envelope carries ``target=null`` and
    ``channels=[]`` rather than being dropped.

    Every chat channel is FREE at every tier, so every populated
    ``channels`` row comes back ``free=True`` / ``locked=False`` /
    ``entitled=True`` regardless of the source or target rung -- the
    pricing surface can render "all N chat channels included at every
    plan" off ONE call without hard-coding the posture client-side.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_channel_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_channel_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog-at-batch")
def api_entitlement_previous_tier_channel_catalog_at_batch():
    """``GET /api/entitlement/previous-tier-channel-catalog-at-batch``
    -- batch sibling of
    ``/api/entitlement/previous-tier-channel-catalog-at``: one
    ``previous-tier-channel-catalog-at`` envelope per purchasable source
    tier, in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-channel-catalog-at-batch`` and
    channel-axis catalog analogue of
    ``/api/entitlement/previous-tier-spec-at-batch``. Lets a
    downgrade-confirmation matrix UI render the "chat channels that
    stay when I step down from each rung" column off **one** call
    instead of N calls to ``/previous-tier-channel-catalog-at``.

    No query params. The source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded), matching
    the sibling ``_at_batch`` endpoints, so the batches fold into the
    same pricing-page table byte-for-byte on the source axis.

    Response shape matches
    ``/api/entitlement/next-tier-channel-catalog-at-batch`` byte-for-
    byte (``tiers`` / ``current_tier`` / ``current_tier_rank`` /
    ``grace`` / ``enforced``); each envelope in ``tiers`` matches
    ``/api/entitlement/previous-tier-channel-catalog-at?tier=<source>``
    for that source exactly. At the source-side floor (``oss`` /
    ``cloud_free`` as source) the envelope carries ``target=null`` and
    ``channels=[]`` rather than being dropped.

    Channel-axis always-free invariant applies here as well: every
    populated ``channels`` row comes back ``free=True`` /
    ``locked=False`` / ``entitled=True``.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_channel_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_channel_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-feature-catalog-at")
def api_entitlement_next_tier_feature_catalog_at():
    """``GET /api/entitlement/next-tier-feature-catalog-at?tier=<source>``
    -- source-anchored feature-axis catalog sibling of
    ``/api/entitlement/next-tier-spec-at``: the full
    :func:`clawmetry.entitlements.feature_catalog_at`-shape catalogue for
    every feature evaluated on the rung above the caller-supplied
    ``tier``.

    Source-anchored companion of ``/next-tier-feature-catalog``
    (resolver-anchored, no-arg) and feature-axis catalog analogue of
    ``/next-tier-channel-catalog-at`` / ``/next-tier-runtime-catalog-at``.
    Lets an upgrade-preview panel walking an explicit source rung (a
    pricing comparison matrix, an "at each rung" table) hydrate the whole
    feature matrix at the next rung off ONE round-trip without threading
    the target tier through query args or first fetching
    ``/entitlement`` for ``next_tier``.

    Response shape::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "features":     [<catalog_row>, ...],   # empty at ceiling
        }

    Inner ``features`` matches
    ``/feature-catalog-at?tier=<target>`` byte-for-byte when ``target``
    is populated -- a parity test pins this so the projection cannot
    drift from the sibling.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``features`` collapses to ``[]`` at the ceiling (no rung
    strictly above -- enterprise as source) -- the surface stays 200 so
    callers can render "you're at the top" copy without a status-code
    branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``features=[]``
      on the same 200 envelope so the preview surface stays mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        rows = _ent.next_tier_feature_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_feature_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "features": [],
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog-at")
def api_entitlement_previous_tier_feature_catalog_at():
    """``GET /api/entitlement/previous-tier-feature-catalog-at?tier=<source>``
    -- symmetric downgrade-side companion of
    ``/next-tier-feature-catalog-at``: the full
    :func:`clawmetry.entitlements.feature_catalog_at`-shape catalogue for
    every feature evaluated on the rung below the caller-supplied
    ``tier``.

    Source-anchored companion of ``/previous-tier-feature-catalog``
    (resolver-anchored, no-arg). Lets a downgrade-confirmation card
    walking an explicit source rung render "which features stay when I
    step down from THIS tier?" off ONE round-trip.

    Response shape matches ``/next-tier-feature-catalog-at``
    byte-for-byte (``tier``, ``tier_label``, ``tier_rank``, ``target``,
    ``target_label``, ``target_rank``, ``features``). Inner ``features``
    matches ``/feature-catalog-at?tier=<target>`` byte-for-byte when
    ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``features`` collapses to ``[]`` at the floor (``oss`` /
    ``cloud_free`` as source) and ``target`` / ``target_label`` /
    ``target_rank`` to ``null``.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``features=[]``
      on the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        rows = _ent.previous_tier_feature_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_feature_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "features": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog-at")
def api_entitlement_next_tier_runtime_catalog_at():
    """``GET /api/entitlement/next-tier-runtime-catalog-at?tier=<source>``
    -- source-anchored runtime-axis catalog sibling of
    ``/api/entitlement/next-tier-spec-at``: the full
    :func:`clawmetry.entitlements.runtime_catalog_at`-shape catalogue for
    every runtime evaluated on the rung above the caller-supplied
    ``tier``.

    Source-anchored companion of ``/next-tier-runtime-catalog``
    (resolver-anchored, no-arg) and runtime-axis catalog analogue of
    ``/next-tier-channel-catalog-at`` / ``/next-tier-feature-catalog-at``.
    Lets an upgrade-preview panel walking an explicit source rung
    hydrate the whole runtime matrix at the next rung off ONE
    round-trip.

    Response shape::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "runtimes":     [<catalog_row>, ...],   # empty at ceiling
        }

    Inner ``runtimes`` matches ``/runtime-catalog-at?tier=<target>``
    byte-for-byte when ``target`` is populated -- pinned by a parity
    test.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``runtimes`` collapses to ``[]`` at the ceiling.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``runtimes=[]``
      on the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        rows = _ent.next_tier_runtime_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_next_tier_runtime_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "runtimes": [],
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog-at")
def api_entitlement_previous_tier_runtime_catalog_at():
    """``GET /api/entitlement/previous-tier-runtime-catalog-at?tier=<source>``
    -- symmetric downgrade-side companion of
    ``/next-tier-runtime-catalog-at``: the full
    :func:`clawmetry.entitlements.runtime_catalog_at`-shape catalogue for
    every runtime evaluated on the rung below the caller-supplied
    ``tier``.

    Source-anchored companion of ``/previous-tier-runtime-catalog``
    (resolver-anchored, no-arg). Lets a downgrade-confirmation card
    walking an explicit source rung render "which runtimes stay when I
    step down from THIS tier?" off ONE round-trip.

    Response shape matches ``/next-tier-runtime-catalog-at``
    byte-for-byte (``tier``, ``tier_label``, ``tier_rank``, ``target``,
    ``target_label``, ``target_rank``, ``runtimes``). Inner ``runtimes``
    matches ``/runtime-catalog-at?tier=<target>`` byte-for-byte when
    ``target`` is populated.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``runtimes`` collapses to ``[]`` at the floor
    (``oss`` / ``cloud_free`` as source) and ``target`` /
    ``target_label`` / ``target_rank`` to ``null``.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown
    - **Never 5xxs**: builder failure short-circuits to ``runtimes=[]``
      on the same 200 envelope.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        rows = _ent.previous_tier_runtime_catalog_at(tier_in) or []
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": rows,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_previous_tier_runtime_catalog_at: error: %s", exc
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "runtimes": [],
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-feature-catalog-at-batch")
def api_entitlement_next_tier_feature_catalog_at_batch():
    """``GET /api/entitlement/next-tier-feature-catalog-at-batch`` --
    batch sibling of ``/api/entitlement/next-tier-feature-catalog-at``:
    one ``next-tier-feature-catalog-at`` envelope per purchasable source
    tier, in one round-trip.

    Feature-axis catalog analogue of
    ``/api/entitlement/next-tier-capacity-diff-at-batch`` (capacity-only
    narrow lens) / ``/api/entitlement/next-tier-diff-at-batch`` (full
    diff). Lets a pricing-comparison matrix UI render the "features at
    the rung above each rung" upgrade-preview column off **one** call
    instead of N calls to ``/next-tier-feature-catalog-at``.

    No query params. The source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded), matching
    the sibling diff / unlocks / locks / capacity ``_at_batch``
    endpoints, so the batches fold into the same pricing-page table
    byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-feature-catalog-at?tier=<source>`` for
    that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``features``). The
    inner ``features`` list carries the :func:`feature_catalog_at` rows
    for the resolved target and is pinned byte-for-byte across both
    endpoints. At the source-side ceiling (``enterprise`` as source --
    no rung strictly above) the envelope carries ``target=null`` and
    ``features=[]`` rather than being dropped, so the matrix keeps a
    row for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_feature_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_feature_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog-at-batch")
def api_entitlement_previous_tier_feature_catalog_at_batch():
    """``GET /api/entitlement/previous-tier-feature-catalog-at-batch`` --
    batch sibling of ``/api/entitlement/previous-tier-feature-catalog-at``:
    one ``previous-tier-feature-catalog-at`` envelope per purchasable
    source tier, in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-feature-catalog-at-batch`` and
    feature-axis catalog analogue of
    ``/api/entitlement/previous-tier-capacity-diff-at-batch``. Lets a
    pricing-comparison matrix UI render the "features at the rung below
    each rung" downgrade-preview column off **one** call.

    No query params. Source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded).

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/previous-tier-feature-catalog-at?tier=<source>``
    for that source exactly. At the source-side floor (``oss`` /
    ``cloud_free`` as source -- no rung strictly below) the envelope
    carries ``target=null`` and ``features=[]`` rather than being
    dropped.

    - **Never 5xxs**: resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_feature_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_feature_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog-at-batch")
def api_entitlement_next_tier_runtime_catalog_at_batch():
    """``GET /api/entitlement/next-tier-runtime-catalog-at-batch`` --
    batch sibling of ``/api/entitlement/next-tier-runtime-catalog-at``:
    one ``next-tier-runtime-catalog-at`` envelope per purchasable source
    tier, in one round-trip.

    Runtime-axis catalog analogue of
    ``/api/entitlement/next-tier-feature-catalog-at-batch`` (feature
    axis) and ``/api/entitlement/next-tier-capacity-diff-at-batch``
    (capacity axis). Lets a pricing-comparison matrix UI render the
    "runtimes at the rung above each rung" upgrade-preview column off
    **one** call.

    No query params. Source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded).

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-runtime-catalog-at?tier=<source>`` for
    that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``runtimes``). At the
    source-side ceiling the envelope carries ``target=null`` and
    ``runtimes=[]`` rather than being dropped.

    - **Never 5xxs**: resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_runtime_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_next_tier_runtime_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog-at-batch")
def api_entitlement_previous_tier_runtime_catalog_at_batch():
    """``GET /api/entitlement/previous-tier-runtime-catalog-at-batch`` --
    batch sibling of ``/api/entitlement/previous-tier-runtime-catalog-at``:
    one ``previous-tier-runtime-catalog-at`` envelope per purchasable
    source tier, in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-runtime-catalog-at-batch`` and
    runtime-axis catalog analogue of
    ``/api/entitlement/previous-tier-feature-catalog-at-batch``.

    No query params. Source list is
    :data:`entitlements._PURCHASABLE_TIERS` (trial excluded).

    Response shape mirrors
    ``/api/entitlement/next-tier-runtime-catalog-at-batch`` byte-for-byte
    on the envelope keys. Each ``<envelope>`` matches
    ``/api/entitlement/previous-tier-runtime-catalog-at?tier=<source>``
    for that source exactly. At the source-side floor (``oss`` /
    ``cloud_free`` as source) the envelope carries ``target=null`` and
    ``runtimes=[]``.

    - **Never 5xxs**: resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_runtime_catalog_at_batch() or []
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
        logger.warning(
            "api_entitlement_previous_tier_runtime_catalog_at_batch: error: %s",
            exc,
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


# ── capacity-axis tiers-for endpoints ────────────────────────────────────────
#
# Inverse siblings of ``/api/entitlement/required-tier?channels=`` /
# ``retention_days=`` / ``nodes=``. Where ``required-tier`` returns the
# cheapest tier that admits a capacity value (one id used by the upgrade-CTA),
# these return the full "Fits in: ..." availability ladder a pricing-page row
# or capacity tooltip needs. Same relationship the existing
# ``/api/entitlement/tiers-for?feature=|runtime=`` endpoint has to
# ``/api/entitlement/required-tier?feature=|runtime=``, extended to the three
# capacity axes.


def _resolver_envelope(_ent) -> dict:
    ent = _ent.get_entitlement()
    return {
        "current_tier": ent.tier,
        "current_tier_rank": _ent.tier_rank(ent.tier),
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }


@bp_entitlement.route("/api/entitlement/tiers-for-channel-count")
def api_entitlement_tiers_for_channel_count():
    """``GET /api/entitlement/tiers-for-channel-count?count=<int>`` --
    inverse of ``/api/entitlement/required-tier?channels=<int>``: returns
    the full ladder of tiers that admit ``count`` configured channel
    adapters, not just the cheapest one. The "Fits in: Starter, Cloud Pro,
    Self-hosted Pro, Trial, Enterprise" availability list a pricing-page
    row or capacity tooltip needs.

    ``count=`` is required. Missing key -> ``400``. Non-int / blank value
    -> ``400``. Never 5xxs: a resolver failure yields empty ``tiers`` list
    and the grace-shape envelope so the pricing UI keeps rendering.

    Response shape mirrors ``/api/entitlement/tiers-for`` exactly plus the
    resolver envelope::

        {
          "item":              <int>,
          "kind":              "channel_count",
          "label":             "5 channels",
          "free":              <bool>,
          "min_tier":          "<tier id>" | null,
          "min_tier_label":    "<label>" | null,
          "min_tier_rank":     <int> | null,
          "tiers":             [<row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }
    """
    raw = request.args.get("count")
    if raw is None:
        return jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_channel_count(n)
        env = _resolver_envelope(_ent)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_channel_count: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-retention-window")
def api_entitlement_tiers_for_retention_window():
    """``GET /api/entitlement/tiers-for-retention-window?days=<int>`` --
    inverse of ``/api/entitlement/required-tier?retention_days=<int>``:
    returns the full ladder of tiers admitting a ``days`` history window.

    ``days=`` is required. Pass ``days=unlimited`` (case-insensitive) for
    the unlimited-history request; the helper only accepts tiers whose
    retention cap is ``None`` (Enterprise on the current tier table).
    Missing key -> ``400``. Blank / non-int / non-``unlimited`` value ->
    ``400``. Never 5xxs.

    Response shape mirrors ``/api/entitlement/tiers-for-channel-count`` --
    ``item`` is the parsed ``days`` value, or ``null`` for the unlimited
    request; ``kind`` is ``"retention_window"``; ``label`` is ``"30
    days"`` / ``"unlimited"``.
    """
    raw = request.args.get("days")
    if raw is None:
        return jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_retention_window(parsed)
        env = _resolver_envelope(_ent)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_retention_window: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-node-count")
def api_entitlement_tiers_for_node_count():
    """``GET /api/entitlement/tiers-for-node-count?count=<int>`` --
    inverse of ``/api/entitlement/required-tier?nodes=<int>``: returns the
    full ladder of tiers admitting ``count`` registered nodes.

    ``count=`` is required. Missing key -> ``400``. Non-int / blank value
    -> ``400``. Never 5xxs.

    Response shape mirrors ``/api/entitlement/tiers-for-channel-count`` --
    ``kind`` is ``"node_count"``; ``label`` is ``"4 nodes"``.
    """
    raw = request.args.get("count")
    if raw is None:
        return jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_node_count(n)
        env = _resolver_envelope(_ent)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_node_count: error: %s", exc
        )
        return jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-capacity-batch")
def api_entitlement_tiers_for_capacity_batch():
    """``GET /api/entitlement/tiers-for-capacity-batch?channels=N
    &retention_days=K&nodes=M`` -- per-item availability ladder for every
    supplied capacity axis in one pass.

    Per-item plural sibling of the three ``/tiers-for-<axis>`` endpoints.
    Closes the capacity-axis symmetry gap in the ``/tiers-for-*`` family:
    ``/tiers-for-batch`` collapses to the two grant axes (features +
    runtimes) and does not accept capacity args at all -- so a pricing-
    page that wants the full "Fits in: <tier>, ..." ladder for a caller-
    supplied ``(channels, retention_days, nodes)`` capacity bundle
    either had to fan out three ``/tiers-for-<axis>`` calls or build the
    ladder client-side from ``/min-tier-batch``. This endpoint delivers
    the same per-axis row shape those three singulars return, on all
    three axes, off ONE round-trip.

    At least one of ``channels=`` / ``retention_days=`` / ``nodes=``
    must be supplied (non-empty / parseable after normalisation). A
    blank or non-int value on an individual axis is treated as "not
    supplied" for that axis (matches
    ``/api/entitlement/min-tier-batch``'s never-crash posture rather
    than mis-routing a typo to Enterprise); the endpoint 400s only when
    *no* axis parsed successfully. Never 5xxs: the grace-shape envelope
    is returned on any resolver failure.

    Response shape::

        {
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` matches the singular
    ``/tiers-for-channel-count?count=`` /
    ``/tiers-for-retention-window?days=`` /
    ``/tiers-for-node-count?count=`` endpoint byte-for-byte (``item`` /
    ``kind`` / ``label`` / ``free`` / ``min_tier`` / ``min_tier_label``
    / ``min_tier_rank`` / ``tiers``) so a caller can pass any row
    through the existing ``tiers_for_*`` rendering components without
    reshaping. Per-row parity with the singular endpoints is pinned in
    the test suite so the batch cannot silently drift from the scalars.

    Critically, ``retention_days`` here treats ``None`` (parameter
    omitted / unparseable) as *unset* -- NOT *unlimited* (matches
    ``/min-tier-batch``'s posture on the same axis). Asking for the
    unlimited-retention ladder is the singular
    ``/tiers-for-retention-window?days=unlimited`` call's job.
    """
    (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
    (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
    (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

    if not channels_ok and not retention_ok and not nodes_ok:
        return (
            jsonify(
                {
                    "error": (
                        "supply at least one of channels=<int>, "
                        "retention_days=<int>, or nodes=<int>"
                    )
                }
            ),
            400,
        )

    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_capacity_batch(
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        env = _resolver_envelope(_ent)
        return jsonify(
            {
                "channels": body.get("channels"),
                "retention_days": body.get("retention_days"),
                "nodes": body.get("nodes"),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_capacity_batch: error: %s", exc
        )
        return jsonify(
            {
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-features")
def api_entitlement_tiers_for_features():
    """``GET /api/entitlement/tiers-for-features?features=a,b,c`` --
    ladder-intersection sibling of ``/api/entitlement/tiers-for``: the
    set of tiers that grant **every** supplied feature at once, wrapped
    in the same row shape a pricing-page component consumes off
    ``/tiers-for?feature=<id>``.

    Closes the ``tiers_for_*`` symmetry gap alongside the singular /
    fixed-batch siblings: the caller-supplied-list shape had no plural
    on the ladder axis, so a UI building the bundle-ladder off
    ``/required-tier-batch?features=`` had to fan out one ``/tiers-for``
    call per known id + intersect on the client. This wraps
    :func:`clawmetry.entitlements.tiers_for_features` so the whole
    "you use fleet + sso -- Available in: Enterprise" ladder lands in
    one round-trip.

    - **400** when ``features=`` is missing / blank after parsing
      (empty string or all-empty tokens). All-unknown IS 200 with an
      ``unknown`` list and empty ``tiers`` -- distinguishes "caller
      asked for nothing" from "caller asked but every token was a typo"
      so the paywall UI can render "these ids are unknown: X" instead
      of a null.
    - Blank / whitespace tokens are dropped; ids are lowercased and
      de-duplicated preserving first-seen order (matches
      ``_parse_csv_arg``).
    - Unknown ids (not in ``ALL_FEATURES``) contribute nothing to the
      intersection so a typo does NOT silently mis-route the ladder to
      Enterprise. Every unknown id lands in the ``unknown`` list on the
      response so the caller can echo them.
    - Never 5xxs: a resolver failure yields the empty shape + the
      grace-shape envelope so the pricing UI keeps rendering.

    Response shape::

        {
          "items":             ["fleet", "sso"],
          "unknown":           ["bogus"],
          "kind":              "features",
          "count":             2,
          "min_tier":          "enterprise" | null,
          "min_tier_label":    "Enterprise" | null,
          "min_tier_rank":     <int> | null,
          "tiers":             [<_tier_row>, ...],
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Where ``<_tier_row>`` matches ``/api/entitlement/tiers-for`` exactly
    (``id`` / ``label`` / ``rank`` / ``purchasable``). ``min_tier``
    byte-equals ``/api/entitlement/required-tier-batch?features=<same>``
    ``.required_tier`` for the same input (parity is the answer).
    """
    raw = request.args.get("features")
    if raw is None or not raw.strip():
        return jsonify({"error": "missing features"}), 400
    features = _parse_csv_arg("features")
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_features(features)
        env = _resolver_envelope(_ent)
        if body is None:
            return jsonify(
                {
                    "items": [],
                    "unknown": features,
                    "kind": "features",
                    "count": 0,
                    "min_tier": None,
                    "min_tier_label": None,
                    "min_tier_rank": None,
                    "tiers": [],
                    **env,
                }
            )
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_features: error: %s", exc
        )
        return jsonify(
            {
                "items": [],
                "unknown": features,
                "kind": "features",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-runtimes")
def api_entitlement_tiers_for_runtimes():
    """``GET /api/entitlement/tiers-for-runtimes?runtimes=x,y,z`` --
    runtime-axis twin of ``/api/entitlement/tiers-for-features``.

    Wraps :func:`clawmetry.entitlements.tiers_for_runtimes`. Runtime
    aliases (``claude-code`` -> ``claude_code``) are canonicalised
    before intersection; input order is preserved after canonical
    de-duplication so the response ``items`` list is stable.

    - **400** when ``runtimes=`` is missing / blank after parsing.
      All-unknown IS 200 with the ``unknown`` list populated (mirrors
      ``/tiers-for-features``).
    - Never 5xxs: a resolver failure yields the empty shape + the
      grace-shape envelope.

    Response shape mirrors ``/tiers-for-features`` with
    ``kind="runtimes"``.
    """
    raw = request.args.get("runtimes")
    if raw is None or not raw.strip():
        return jsonify({"error": "missing runtimes"}), 400
    runtimes = _parse_csv_arg("runtimes")
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_runtimes(runtimes)
        env = _resolver_envelope(_ent)
        if body is None:
            return jsonify(
                {
                    "items": [],
                    "unknown": runtimes,
                    "kind": "runtimes",
                    "count": 0,
                    "min_tier": None,
                    "min_tier_label": None,
                    "min_tier_rank": None,
                    "tiers": [],
                    **env,
                }
            )
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_runtimes: error: %s", exc
        )
        return jsonify(
            {
                "items": [],
                "unknown": runtimes,
                "kind": "runtimes",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )



# ── capacity-axis tiers-for-*-at endpoints ───────────────────────────────────
#
# Hypothetical-perspective siblings of the four capacity-axis ``tiers_for_*``
# endpoints above. Fill the ``_at`` slot on the capacity family alongside
# ``/api/entitlement/tiers-for-at`` / ``/tiers-for-batch-at`` on the grant
# axes, so a pricing-matrix walkthrough can call every ``/tiers-for-*-at``
# endpoint with a uniform ``tier=<perspective>`` URL. The ladder itself is
# perspective-independent (walks the static per-tier caps via the singular
# helpers) so parity with the non-``_at`` sibling is pinned in the test suite.


def _perspective_envelope(_ent, p: str) -> dict:
    ent = _ent.get_entitlement()
    return {
        "perspective_tier": p,
        "perspective_tier_label": _ent.tier_label(p),
        "perspective_tier_rank": _ent.tier_rank(p),
        "current_tier": ent.tier,
        "current_tier_rank": _ent.tier_rank(ent.tier),
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }


def _perspective_fallback(p: str) -> dict:
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(p)
        rank = _ent.tier_rank(p)
    except Exception:
        label = p
        rank = 0
    return {
        "perspective_tier": p,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }


@bp_entitlement.route("/api/entitlement/tiers-for-channel-count-at")
def api_entitlement_tiers_for_channel_count_at():
    """``GET /api/entitlement/tiers-for-channel-count-at?tier=<perspective>
    &count=<int>`` -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-channel-count``: returns the full ladder
    of tiers admitting ``count`` configured channel adapters, scoped by a
    caller-supplied ``perspective_tier``.

    Perspective is validated against ``_TIER_ORDER`` (``trial``
    accepted) but does NOT shape rows -- the ladder is intrinsically
    perspective-independent (walks the static per-tier channel-cap
    table). The ``perspective_tier`` envelope keeps every ``_at`` URL
    uniform across the ``tiers_for_*`` family.

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``
    (``which=tier``). Missing / blank / non-int ``count=`` -> ``400``.
    Never 5xxs: a resolver failure yields empty ``tiers`` list plus the
    perspective + grace envelope so the pricing UI keeps rendering.

    Response shape mirrors ``/api/entitlement/tiers-for-channel-count``
    plus the perspective envelope (``perspective_tier``,
    ``perspective_tier_label``, ``perspective_tier_rank``).
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    raw = request.args.get("count")
    if raw is None:
        return jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_channel_count_at(p, n)
        env = _perspective_envelope(_ent, p)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_channel_count_at: error: %s", exc
        )
        return jsonify({"tiers": [], **_perspective_fallback(p)})


@bp_entitlement.route("/api/entitlement/tiers-for-retention-window-at")
def api_entitlement_tiers_for_retention_window_at():
    """``GET /api/entitlement/tiers-for-retention-window-at?tier=<perspective>
    &days=<int>`` -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-retention-window``.

    Pass ``days=unlimited`` (case-insensitive) for the unlimited-history
    request; the helper only accepts tiers whose retention cap is
    ``None`` (Enterprise on the current tier table). Perspective is
    validated but does NOT shape rows.

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``.
    Missing ``days=`` -> ``400``. Blank / non-int / non-``unlimited``
    value -> ``400``. Never 5xxs.

    Response shape mirrors
    ``/api/entitlement/tiers-for-retention-window`` plus the perspective
    envelope.
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    raw = request.args.get("days")
    if raw is None:
        return jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_retention_window_at(p, parsed)
        env = _perspective_envelope(_ent, p)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_retention_window_at: error: %s", exc
        )
        return jsonify({"tiers": [], **_perspective_fallback(p)})


@bp_entitlement.route("/api/entitlement/tiers-for-node-count-at")
def api_entitlement_tiers_for_node_count_at():
    """``GET /api/entitlement/tiers-for-node-count-at?tier=<perspective>
    &count=<int>`` -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-node-count``.

    Perspective is validated against ``_TIER_ORDER`` (``trial``
    accepted) but does NOT shape rows.

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``.
    Missing / blank / non-int ``count=`` -> ``400``. Never 5xxs.

    Response shape mirrors ``/api/entitlement/tiers-for-node-count``
    plus the perspective envelope.
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    raw = request.args.get("count")
    if raw is None:
        return jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_node_count_at(p, n)
        env = _perspective_envelope(_ent, p)
        if body is None:
            return jsonify({"tiers": [], **env})
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_node_count_at: error: %s", exc
        )
        return jsonify({"tiers": [], **_perspective_fallback(p)})


@bp_entitlement.route("/api/entitlement/tiers-for-capacity-batch-at")
def api_entitlement_tiers_for_capacity_batch_at():
    """``GET /api/entitlement/tiers-for-capacity-batch-at?tier=<perspective>
    &channels=N&retention_days=K&nodes=M`` -- hypothetical-perspective
    sibling of ``/api/entitlement/tiers-for-capacity-batch``.

    Fills the last ``_at`` slot in the ``/tiers-for-*`` family alongside
    ``/tiers-for-at`` / ``/tiers-for-batch-at`` on the grant axes and the
    three per-axis capacity ``/tiers-for-*-at`` endpoints, so a pricing-
    matrix walkthrough can call every ``/tiers-for-*-at`` endpoint with
    a uniform ``tier=<perspective>`` URL.

    Perspective is validated against ``_TIER_ORDER`` (``trial``
    accepted) but does NOT shape rows -- the batch is identical to
    ``/tiers-for-capacity-batch`` regardless of perspective (pinned by
    cross-endpoint parity test).

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` -> ``404``.
    At least one of ``channels=`` / ``retention_days=`` / ``nodes=``
    must parse successfully; the endpoint 400s only when *no* axis
    parsed (matches ``/tiers-for-capacity-batch``'s never-mis-route
    posture). Never 5xxs.

    ``retention_days`` treats ``None`` (parameter omitted /
    unparseable) as *unset* -- NOT *unlimited* (matches
    ``/min-tier-batch``'s posture). Asking for the unlimited-retention
    ladder at a hypothetical perspective is the singular
    ``/tiers-for-retention-window-at?days=unlimited`` call's job.

    Response shape mirrors ``/api/entitlement/tiers-for-capacity-batch``
    plus the perspective envelope.
    """
    p = (request.args.get("tier") or "").strip().lower()
    if not p:
        return jsonify({"error": "missing tier"}), 400
    (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
    (_, retention_ok, retention_n, _) = _parse_capacity_arg("retention_days")
    (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

    if not channels_ok and not retention_ok and not nodes_ok:
        return (
            jsonify(
                {
                    "error": (
                        "supply at least one of channels=<int>, "
                        "retention_days=<int>, or nodes=<int>"
                    )
                }
            ),
            400,
        )

    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_capacity_batch_at(
            p,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        env = _perspective_envelope(_ent, p)
        if body is None:
            body = {"channels": None, "retention_days": None, "nodes": None}
        return jsonify(
            {
                "channels": body.get("channels"),
                "retention_days": body.get("retention_days"),
                "nodes": body.get("nodes"),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_capacity_batch_at: error: %s", exc
        )
        return jsonify(
            {
                "channels": None,
                "retention_days": None,
                "nodes": None,
                **_perspective_fallback(p),
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier-for-features-at")
def api_entitlement_min_tier_for_features_at():
    """``GET /api/entitlement/min-tier-for-features-at?tier=<perspective>
    &features=a,b,c`` -- hypothetical-perspective sibling of
    ``min_tier_for_features``: the cheapest *purchasable* tier admitting
    every feature in the bundle, scoped by a caller-supplied
    ``perspective_tier``.

    Fills the ``_at`` slot for the ``min_tier_for_features`` scalar so a
    pricing-matrix walkthrough (``?tier=<p>``) can hit
    ``/min-tier-for-features-at`` uniformly across the whole ``_at``
    family instead of falling back to ``/required-tier-batch?features=<csv>``
    (which combines features + runtimes and lacks the perspective envelope).

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape the answer -- the scalar tier
    id depends only on the static per-tier feature map. A parity contract
    pinned in the test suite guarantees the ``required_tier`` byte-equals
    ``min_tier_for_features(features)`` for every perspective. The
    response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard resolver envelope so
    a walkthrough surface can render the "from <perspective>" copy off
    one round-trip.

    Response shape::

        {
          "features":               ["fleet", "sso"],
          "unknown":                ["bogus"],
          "kind":                   "features",
          "count":                  2,
          "required_tier":          "enterprise" | null,
          "required_tier_label":    "Enterprise" | null,
          "required_tier_rank":     <int>,
          "free":                   <bool>,
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "current_tier":           "oss",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    - **400** when ``tier=`` is missing / blank, OR when ``features=`` is
      missing / blank after CSV normalisation.
    - **404** when ``tier`` is unknown. The body carries ``which=tier`` so
      a caller can render the right "unknown tier" message.
    - **All-unknown features IS 200** with ``unknown`` populated and
      ``required_tier=null`` -- distinguishes "caller asked for nothing"
      from "caller asked but every token was a typo" so a paywall UI can
      render "these ids are unknown: X" instead of a null.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``features`` list, ``required_tier=null``) so the pricing
      walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400

    features_csv = _parse_csv_arg("features")
    if not features_csv:
        return jsonify({"error": "missing features"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        known: list[str] = []
        unknown: list[str] = []
        for fid in features_csv:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            else:
                if fid not in unknown:
                    unknown.append(fid)

        required = _ent.min_tier_for_features_at(tier_in, known) if known else None
        env = _resolver_envelope(_ent)
        return jsonify(
            {
                "features": known,
                "unknown": unknown,
                "kind": "features",
                "count": len(known),
                "required_tier": required,
                "required_tier_label": (
                    _ent.tier_label(required) if required else None
                ),
                "required_tier_rank": (
                    _ent.tier_rank(required) if required else -1
                ),
                "free": bool(required == _ent.TIER_OSS),
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_min_tier_for_features_at: error: %s", exc
        )
        return jsonify(
            {
                "features": [],
                "unknown": features_csv,
                "kind": "features",
                "count": 0,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "free": False,
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier-for-runtimes-at")
def api_entitlement_min_tier_for_runtimes_at():
    """``GET /api/entitlement/min-tier-for-runtimes-at?tier=<perspective>
    &runtimes=x,y,z`` -- runtime-axis twin of
    ``/api/entitlement/min-tier-for-features-at``.

    Same perspective contract, same never-5xx posture, same
    perspective-independence guarantee (pinned by a parity test).
    Runtime aliases (``claude-code`` -> ``claude_code``) are canonicalised
    through :func:`clawmetry.entitlements.canonical_runtime` so a caller
    does not need to normalise before calling; unknown ids land in
    ``unknown`` and drop from the ``required_tier`` walk (a typo does NOT
    silently mis-route the ladder to Enterprise).

    Response shape and error paths mirror
    ``/min-tier-for-features-at`` exactly, with ``kind="runtimes"`` and a
    ``runtimes`` list in place of ``features``.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400

    runtimes_csv = _parse_csv_arg("runtimes")
    if not runtimes_csv:
        return jsonify({"error": "missing runtimes"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        known: list[str] = []
        unknown: list[str] = []
        for rt in runtimes_csv:
            canon = _ent.canonical_runtime(rt)
            if canon and canon in _ent.ALL_RUNTIMES:
                if canon not in known:
                    known.append(canon)
            else:
                if rt not in unknown:
                    unknown.append(rt)

        required = _ent.min_tier_for_runtimes_at(tier_in, known) if known else None
        env = _resolver_envelope(_ent)
        return jsonify(
            {
                "runtimes": known,
                "unknown": unknown,
                "kind": "runtimes",
                "count": len(known),
                "required_tier": required,
                "required_tier_label": (
                    _ent.tier_label(required) if required else None
                ),
                "required_tier_rank": (
                    _ent.tier_rank(required) if required else -1
                ),
                "free": bool(required == _ent.TIER_OSS),
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_min_tier_for_runtimes_at: error: %s", exc
        )
        return jsonify(
            {
                "runtimes": [],
                "unknown": runtimes_csv,
                "kind": "runtimes",
                "count": 0,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "free": False,
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-features-at")
def api_entitlement_tiers_for_features_at():
    """``GET /api/entitlement/tiers-for-features-at?tier=<perspective>
    &features=a,b,c`` -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-features``: the full ladder of tiers
    admitting every feature in the bundle, scoped by a caller-supplied
    ``perspective_tier``.

    Fills the ``_at`` slot for the ``tiers_for_features`` ladder axis so
    a pricing-matrix walkthrough (``?tier=<p>``) can hit
    ``/tiers-for-features-at`` uniformly across the whole ``_at`` family
    (alongside ``/min-tier-for-features-at`` on the scalar axis and the
    four capacity-axis ``/tiers-for-*-at`` endpoints on the capacity
    axis).

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape the answer -- the ladder id
    list depends only on the static per-tier feature map. A parity
    contract pinned in the test suite guarantees the six body keys
    (``items`` / ``unknown`` / ``kind`` / ``count`` / ``min_tier`` /
    ``min_tier_label`` / ``min_tier_rank`` / ``tiers``) byte-equal
    ``/tiers-for-features?features=<same>`` for every perspective. The
    response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard resolver envelope
    so a walkthrough surface can render the "from <perspective>" copy
    off one round-trip.

    Response shape::

        {
          "items":                  ["fleet", "sso"],
          "unknown":                ["bogus"],
          "kind":                   "features",
          "count":                  2,
          "min_tier":               "enterprise" | null,
          "min_tier_label":         "Enterprise" | null,
          "min_tier_rank":          <int> | null,
          "tiers":                  [<_tier_row>, ...],
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  3,
          "current_tier":           "oss",
          "current_tier_rank":      0,
          "grace":                  true,
          "enforced":               false,
        }

    - **400** when ``tier=`` is missing / blank, OR when ``features=``
      is missing / blank after CSV normalisation.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``
      so a caller can render the right "unknown tier" message.
    - **All-unknown features IS 200** with ``unknown`` populated and
      ``tiers=[]`` / ``min_tier=null`` -- distinguishes "caller asked
      for nothing" from "caller asked but every token was a typo" so a
      paywall UI can render "these ids are unknown: X" instead of a
      null.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``items`` / ``tiers`` list, ``min_tier=null``) so the
      pricing walkthrough keeps rendering.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400

    raw_features = request.args.get("features")
    if raw_features is None or not raw_features.strip():
        return jsonify({"error": "missing features"}), 400
    features_csv = _parse_csv_arg("features")
    if not features_csv:
        return jsonify({"error": "missing features"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        body = _ent.tiers_for_features_at(tier_in, features_csv)
        env = _perspective_envelope(_ent, tier_in)
        if body is None:
            return jsonify(
                {
                    "items": [],
                    "unknown": features_csv,
                    "kind": "features",
                    "count": 0,
                    "min_tier": None,
                    "min_tier_label": None,
                    "min_tier_rank": None,
                    "tiers": [],
                    **env,
                }
            )
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_features_at: error: %s", exc
        )
        return jsonify(
            {
                "items": [],
                "unknown": features_csv,
                "kind": "features",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                **_perspective_fallback(tier_in),
            }
        )


@bp_entitlement.route("/api/entitlement/tiers-for-runtimes-at")
def api_entitlement_tiers_for_runtimes_at():
    """``GET /api/entitlement/tiers-for-runtimes-at?tier=<perspective>
    &runtimes=x,y,z`` -- runtime-axis twin of
    ``/api/entitlement/tiers-for-features-at``.

    Wraps :func:`clawmetry.entitlements.tiers_for_runtimes_at`. Runtime
    aliases (``claude-code`` -> ``claude_code``) are canonicalised
    before intersection; the perspective envelope layers on top of the
    standard resolver envelope. Perspective is validated but does NOT
    shape rows -- the ladder byte-equals
    ``/tiers-for-runtimes?runtimes=<same>`` for every perspective
    (pinned by the parity tests).

    - **400** when ``tier=`` is missing / blank, OR when ``runtimes=``
      is missing / blank after CSV normalisation.
    - **404** when ``tier`` is unknown (``which=tier``).
    - **All-unknown runtimes IS 200** with the ``unknown`` list
      populated (mirrors ``/tiers-for-runtimes``).
    - **Never 5xxs**: a resolver failure yields the fallback envelope.

    Response shape mirrors ``/tiers-for-features-at`` with
    ``kind="runtimes"``.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400

    raw_runtimes = request.args.get("runtimes")
    if raw_runtimes is None or not raw_runtimes.strip():
        return jsonify({"error": "missing runtimes"}), 400
    runtimes_csv = _parse_csv_arg("runtimes")
    if not runtimes_csv:
        return jsonify({"error": "missing runtimes"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        body = _ent.tiers_for_runtimes_at(tier_in, runtimes_csv)
        env = _perspective_envelope(_ent, tier_in)
        if body is None:
            return jsonify(
                {
                    "items": [],
                    "unknown": runtimes_csv,
                    "kind": "runtimes",
                    "count": 0,
                    "min_tier": None,
                    "min_tier_label": None,
                    "min_tier_rank": None,
                    "tiers": [],
                    **env,
                }
            )
        return jsonify({**body, **env})
    except Exception as exc:
        logger.warning(
            "api_entitlement_tiers_for_runtimes_at: error: %s", exc
        )
        return jsonify(
            {
                "items": [],
                "unknown": runtimes_csv,
                "kind": "runtimes",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                **_perspective_fallback(tier_in),
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier-for-features")
def api_entitlement_min_tier_for_features():
    """``GET /api/entitlement/min-tier-for-features?features=a,b,c`` --
    resolver-scoped sibling of ``min_tier_for_features``: the cheapest
    *purchasable* tier admitting every feature in the bundle.

    Fills the *bare* slot for the plural grant-axis ``min_tier_for_*``
    family alongside the singular ``/min-tier?feature=<id>`` route (which
    resolves ONE feature at a time) and the ``_at`` sibling
    ``/min-tier-for-features-at?tier=<perspective>&features=<csv>`` (which
    layers a hypothetical-perspective envelope on top). A dashboard wiring
    "you are using fleet + otel_export + sso -- Available in Enterprise"
    can now hit ONE endpoint that folds the per-feature ``max-by-rank``
    walk in place of N calls to ``/min-tier?feature=`` + client-side
    aggregation.

    Body byte-identical to ``/min-tier-for-features-at?tier=<p>&features=``
    with the three ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` envelope keys stripped -- pinned by a
    parity test so the bare and ``_at`` bodies cannot drift.

    Response shape::

        {
          "features":            ["fleet", "sso"],
          "unknown":             ["bogus"],
          "kind":                "features",
          "count":               2,
          "required_tier":       "enterprise" | null,
          "required_tier_label": "Enterprise" | null,
          "required_tier_rank":  <int>,
          "free":                <bool>,
          "current_tier":        "oss",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    - **400** when ``features=`` is missing / blank after CSV
      normalisation.
    - **All-unknown features IS 200** with ``unknown`` populated and
      ``required_tier=null`` -- distinguishes "caller asked for nothing"
      from "caller asked but every token was a typo" so a paywall UI can
      render "these ids are unknown: X" instead of a null.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``features`` list, ``required_tier=null``) so the pricing
      surface keeps rendering.
    """
    features_csv = _parse_csv_arg("features")
    if not features_csv:
        return jsonify({"error": "missing features"}), 400

    try:
        from clawmetry import entitlements as _ent

        known: list[str] = []
        unknown: list[str] = []
        for fid in features_csv:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            else:
                if fid not in unknown:
                    unknown.append(fid)

        required = _ent.min_tier_for_features(known) if known else None
        env = _resolver_envelope(_ent)
        return jsonify(
            {
                "features": known,
                "unknown": unknown,
                "kind": "features",
                "count": len(known),
                "required_tier": required,
                "required_tier_label": (
                    _ent.tier_label(required) if required else None
                ),
                "required_tier_rank": (
                    _ent.tier_rank(required) if required else -1
                ),
                "free": bool(required == _ent.TIER_OSS),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_min_tier_for_features: error: %s", exc
        )
        return jsonify(
            {
                "features": [],
                "unknown": features_csv,
                "kind": "features",
                "count": 0,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "free": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )


@bp_entitlement.route("/api/entitlement/min-tier-for-runtimes")
def api_entitlement_min_tier_for_runtimes():
    """``GET /api/entitlement/min-tier-for-runtimes?runtimes=x,y,z`` --
    runtime-axis twin of ``/api/entitlement/min-tier-for-features``.

    Same never-5xx posture, same partial-unknown bucketing.
    Runtime aliases (``claude-code`` -> ``claude_code``) are canonicalised
    through :func:`clawmetry.entitlements.canonical_runtime` so a caller
    does not need to normalise before calling; unknown ids land in
    ``unknown`` and drop from the ``required_tier`` walk (a typo does NOT
    silently mis-route the ladder to a higher tier).

    Response shape and error paths mirror
    ``/min-tier-for-features`` exactly, with ``kind="runtimes"`` and a
    ``runtimes`` list in place of ``features``.
    """
    runtimes_csv = _parse_csv_arg("runtimes")
    if not runtimes_csv:
        return jsonify({"error": "missing runtimes"}), 400

    try:
        from clawmetry import entitlements as _ent

        known: list[str] = []
        unknown: list[str] = []
        for rt in runtimes_csv:
            canon = _ent.canonical_runtime(rt)
            if canon and canon in _ent.ALL_RUNTIMES:
                if canon not in known:
                    known.append(canon)
            else:
                if rt not in unknown:
                    unknown.append(rt)

        required = _ent.min_tier_for_runtimes(known) if known else None
        env = _resolver_envelope(_ent)
        return jsonify(
            {
                "runtimes": known,
                "unknown": unknown,
                "kind": "runtimes",
                "count": len(known),
                "required_tier": required,
                "required_tier_label": (
                    _ent.tier_label(required) if required else None
                ),
                "required_tier_rank": (
                    _ent.tier_rank(required) if required else -1
                ),
                "free": bool(required == _ent.TIER_OSS),
                **env,
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_min_tier_for_runtimes: error: %s", exc
        )
        return jsonify(
            {
                "runtimes": [],
                "unknown": runtimes_csv,
                "kind": "runtimes",
                "count": 0,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "free": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )
