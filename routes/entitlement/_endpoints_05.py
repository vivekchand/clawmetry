"""routes/entitlement/_endpoints_05.py — endpoint handlers api_entitlement_next_tier_spec .. api_entitlement_feature_catalog_at_path.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/next-tier-spec")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_next_tier_spec: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "spec": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-spec")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_previous_tier_spec: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "spec": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-spec")
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
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if feature not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_feature_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("feature", feature))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-spec")
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
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if feature not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_feature_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("feature", feature))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-spec")
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
    raw_runtime = _shared.request.args.get("runtime")
    supplied = (raw_runtime or "").strip().lower()
    if not supplied:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(supplied)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_runtime_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("runtime", supplied))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec")
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
    raw_runtime = _shared.request.args.get("runtime")
    supplied = (raw_runtime or "").strip().lower()
    if not supplied:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(supplied)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_runtime_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("runtime", supplied))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-spec")
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
    raw_channel = _shared.request.args.get("channel")
    supplied = (raw_channel or "").strip().lower()
    if not supplied:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if supplied not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_channel_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("channel", supplied))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_channel_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_channel_catalog_grace_body())

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-spec")
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
    raw_channel = _shared.request.args.get("channel")
    supplied = (raw_channel or "").strip().lower()
    if not supplied:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if supplied not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_channel_spec: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_grace_body("channel", supplied))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_channel_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_channel_catalog_grace_body())

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_feature_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_catalog_grace_body("features"))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_feature_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_catalog_grace_body("features"))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_runtime_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_catalog_grace_body("runtimes"))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_runtime_catalog: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_catalog_grace_body("runtimes"))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-spec-batch")
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
        features = _shared._parse_csv_arg("features")
        if not features:
            return _shared.jsonify({"error": "supply features=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_feature_spec_batch(features)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_feature_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("features"))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-batch")
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
        features = _shared._parse_csv_arg("features")
        if not features:
            return _shared.jsonify({"error": "supply features=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_feature_spec_batch(features)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_feature_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("features"))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return _shared.jsonify({"error": "supply runtimes=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_runtime_spec_batch(runtimes)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_runtime_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("runtimes"))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return _shared.jsonify({"error": "supply runtimes=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_runtime_spec_batch(runtimes)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_runtime_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("runtimes"))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-spec-batch")
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
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return _shared.jsonify({"error": "supply channels=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.next_purchasable_tier()
        batch = ent.next_tier_channel_spec_batch(channels)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_channel_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("channels"))

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-batch")
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
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return _shared.jsonify({"error": "supply channels=<csv>"}), 400
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        target = ent.previous_purchasable_tier()
        batch = ent.previous_tier_channel_spec_batch(channels)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_channel_spec_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._next_prev_tier_axis_spec_batch_grace_body("channels"))

@_shared.bp_entitlement.route("/api/entitlement/next-tier-lock-reason")
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
    return _shared._next_prev_lock_reason("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-lock-reason")
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
    return _shared._next_prev_lock_reason("previous")

@_shared.bp_entitlement.route("/api/entitlement/next-tier-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_spec_at(tier_in)
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_next_tier_spec_at: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_spec_at(tier_in)
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_previous_tier_spec_at: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-spec-at-batch")
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
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-spec-at-batch")
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
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_spec_path(f, t)
        if path is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_tier_spec_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    feat = (_shared.request.args.get("feature") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    if not feat:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.feature_spec_path(f, t, feat)
        if path is None:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_feature_spec_path: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier or feature",
                    "from": f,
                    "to": t,
                    "feature": feat,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    rt_raw = (_shared.request.args.get("runtime") or "").strip()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    if not rt_raw:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        rt = _ent.canonical_runtime(rt_raw)
        path = _ent.runtime_spec_path(f, t, rt_raw)
        if path is None:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_runtime_spec_path: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier or runtime",
                    "from": f,
                    "to": t,
                    "runtime": rt_raw.lower(),
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.feature_catalog_path(f, t)
        if path is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_feature_catalog_path: error: %s", exc
        )
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.runtime_catalog_path(f, t)
        if path is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_runtime_catalog_path: error: %s", exc
        )
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.channel_catalog_path(f, t)
        if path is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_channel_catalog_path: error: %s", exc
        )
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    ch = (_shared.request.args.get("channel") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    if not ch:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.channel_spec_path(f, t, ch)
        if path is None:
            if f not in _ent._TIER_FEATURES or t not in _ent._TIER_FEATURES:
                which = "tier"
            else:
                which = "channel"
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_channel_spec_path: error: %s", exc
        )
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier or channel",
                    "from": f,
                    "to": t,
                    "channel": ch,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at-path")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    ch = (_shared.request.args.get("channel") or "").strip().lower()
    if not ch:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
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
                _shared.jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        if ch not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_channel_spec_at_path: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at-path-batch")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
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
                _shared.jsonify(
                    {"error": "unknown from", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify({"error": "unknown to", "which": "to", "to": t}),
                404,
            )
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return _shared.jsonify({"error": "supply channels=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_channel_spec_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return _shared.jsonify({"error": "supply channels=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_channel_spec_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_catalog_path(f, t)
        if path is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_tier_catalog_path: error: %s", exc
        )
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400

    feature = (_shared.request.args.get("feature") or "").strip().lower()
    runtime_in = (_shared.request.args.get("runtime") or "").strip().lower()
    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _shared._parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _shared._parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _shared._parse_capacity_arg("nodes")

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
            _shared.jsonify(
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
            _shared.jsonify(
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
                    _shared.jsonify(
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
                    _shared.jsonify(
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
                    _shared.jsonify(
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
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_lock_reason_path: error: %s", exc)
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
            _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_feature_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_feature_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_runtime = _shared.request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_runtime_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_runtime = _shared.request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_runtime_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_channel = _shared.request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_channel_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_channel = _shared.request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_channel_spec_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-lock-reason-at")
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
    return _shared._next_prev_lock_reason_at("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-at")
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
    return _shared._next_prev_lock_reason_at("previous")

@_shared.bp_entitlement.route("/api/entitlement/next-tier-lock-reason-at-batch")
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
    return _shared._next_prev_lock_reason_at_batch("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-at-batch")
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
    return _shared._next_prev_lock_reason_at_batch("previous")

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_spec_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_spec_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_catalog_path_batch(f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "from": f,
                "from_label": _ent.tier_label(f),
                "from_rank": _ent.tier_rank(f),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_catalog_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "from": f,
                "from_label": None,
                "from_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at-path")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.tier_catalog_at_path(p, f, t)
        if path is None:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_tier_catalog_at_path: error: %s", exc
        )
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at-path-batch")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_tier_catalog_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-at-path")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.capacity_diff_at_path(p, f, t)
        if path is None:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_capacity_diff_at_path: error: %s", exc
        )
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-at-path-batch")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_capacity_diff_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at-path")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": p}
                ),
                404,
            )
        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        if t not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "to", "to": t}
                ),
                404,
            )
        path = _ent.feature_catalog_at_path(p, f, t)
        if path is None:
            return (
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_feature_catalog_at_path: error: %s", exc
        )
        return (
            _shared.jsonify(
                {
                    "error": "unknown tier",
                    "tier": p,
                    "from": f,
                    "to": t,
                }
            ),
            404,
        )
