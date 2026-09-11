"""routes/entitlement/_endpoints_01.py — endpoint handlers api_entitlement .. api_entitlement_has_runtimes_at_batch.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement")
def api_entitlement():
    try:
        from clawmetry import entitlements as _ent

        out = _ent.get_entitlement().to_dict()
        # "We do not know this account's plan yet" — distinct from "this
        # account is on the free plan". Gating UI must not lock while true.
        out["pending"] = _ent.plan_pending()
        return _shared.jsonify(out)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement: primary resolver failed, falling back to OSS-free: %s",
            exc,
        )
    # Preferred fallback: build the canonical OSS-free entitlement and return
    # its ``to_dict()`` so the shape matches the healthy path exactly (30+
    # keys including ``features``, ``free_runtimes``, ``channel_limit``,
    # ``next_tier_capacity_diff``, ``next_tier_locks``...). Only if this ALSO
    # fails -- typically an import failure of the entitlements module itself
    # -- do we fall through to the in-line snapshot below.
    try:
        from clawmetry import entitlements as _ent

        degraded = _ent._oss_free().to_dict()
        # The resolver just failed, so this is "unknown", never "confirmed
        # free". Gating UI must not lock on it.
        degraded["pending"] = True
        return _shared.jsonify(degraded)
    except Exception as exc2:
        _shared.logger.warning(
            "api_entitlement: OSS-free fallback also failed, using minimal snapshot: %s",
            exc2,
        )
    snap = dict(_shared._MINIMAL_OSS_FREE_SNAPSHOT)
    # Merge the live hard-block signal on top of the frozen snapshot so the
    # overlay never sees a stale ``False`` on the resolver-crashed path.
    try:
        from clawmetry import trial_enforcement as _te
        snap["hard_blocked"] = bool(_te.is_hard_blocked())
        snap["free_only_mode"] = bool(_te.free_only_mode_enabled())
    except Exception:
        pass
    return _shared.jsonify(snap)

@_shared.bp_entitlement.route("/api/entitlement/refresh", methods=["POST"])
def api_entitlement_refresh():
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
        return _shared.jsonify(_ent.get_entitlement(force=True).to_dict())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_refresh: falling back to OSS-free: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/upgrade-diff")
def api_entitlement_upgrade_diff():
    try:
        target = (_shared.request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return _shared.jsonify(_ent.upgrade_diff(target))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_upgrade_diff: error: %s", exc)
        return _shared.jsonify(
            {
                "target": (_shared.request.args.get("target") or "").strip().lower(),
                "added_features": [],
                "added_runtimes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/downgrade-diff")
def api_entitlement_downgrade_diff():
    try:
        target = (_shared.request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return _shared.jsonify(_ent.downgrade_diff(target))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_downgrade_diff: error: %s", exc)
        return _shared.jsonify(
            {
                "target": (_shared.request.args.get("target") or "").strip().lower(),
                "lost_features": [],
                "lost_runtimes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-diff")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_diff(f, t)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_diff: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_path(f, t)
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
        _shared.logger.warning("api_entitlement_tier_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-diff-batch")
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
        _shared.logger.warning("api_entitlement_tier_diff_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff")
def api_entitlement_capacity_diff():
    """``GET /api/entitlement/capacity-diff?target=<tier>`` -- per-axis
    capacity transition (channels / retention / nodes) from the resolved
    entitlement to ``target``. Companion to ``/upgrade-diff`` (feature +
    runtime adds) and ``/downgrade-diff`` (feature + runtime losses). The
    payload is direction-agnostic: each axis carries the same
    ``{before, after, delta, unlocked, locked}`` triple so both the
    upgrade-to and the cancellation-to CTAs read off one shape."""
    try:
        target = (_shared.request.args.get("target") or "").strip().lower()
        from clawmetry import entitlements as _ent

        return _shared.jsonify(_ent.capacity_diff(target))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_capacity_diff: error: %s", exc)
        return _shared.jsonify(
            {
                "target": (_shared.request.args.get("target") or "").strip().lower(),
                "channel_limit": None,
                "retention_days": None,
                "node_limit": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom")
def api_entitlement_capacity_headroom():
    """``GET /api/entitlement/capacity-headroom?channels=<int>&retention_days=<int>&nodes=<int>``
    -- per-axis "how much room is left" against the resolved entitlement's
    capacity caps.

    Resolver-pinned companion to
    ``/api/entitlement/tiers-for-capacity-batch`` (which is decoupled from
    the resolver and returns the full pricing ladder): given caller-
    supplied *current usage* on any of the three capacity axes, returns one
    row per supplied axis describing how close to (or past) the current
    tier's cap the caller is. A quota gauge or a "you're at 4/5 channels
    on Starter" badge reads off this single primitive without re-deriving
    per-tier caps client-side.

    Envelope shape::

        {
          "tier":           "<resolved>",
          "tier_label":     "<human>",
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
        }

    Each ``<row>`` (matches :func:`clawmetry.entitlements._headroom_row`
    byte-for-byte)::

        {
          "kind":         "channels" | "retention_days" | "nodes",
          "used":         <int>,
          "cap":          <int> | None,
          "remaining":    <int> | None,
          "is_unlimited": <bool>,
          "at_limit":     <bool>,
          "over_limit":   <bool>,
          "pct_used":     <float> | None,
        }

    Per-axis ``None`` means "axis not supplied" (matches
    ``/tiers-for-capacity-batch``'s "None means unset, not unlimited"
    posture). A blank, non-int, negative, or ``bool``-in-disguise
    (``?channels=true``) value on any axis short-circuits that axis to
    ``None`` -- a stray query string cannot silently blank a gauge; the
    caller opts in per-axis by supplying a real int.

    In grace mode :meth:`Entitlement.channel_limit` returns ``None``
    (unlimited), so every axis collapses to the unlimited-side row shape
    and the gauge renders "unlimited / N used" instead of a bogus
    percentage while the grace window is still open.

    Never 5xxs: on a resolver failure the neutral envelope shape
    (``tier=oss``, every axis ``None``) is returned so a paywall tile
    keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        return _shared.jsonify(_ent.capacity_headroom(**kwargs))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_capacity_headroom: error: %s", exc)
        try:
            from clawmetry import entitlements as _ent

            return _shared.jsonify(
                {
                    "tier": _ent.TIER_OSS,
                    "tier_label": _ent.tier_label(_ent.TIER_OSS),
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                }
            )
        except Exception:
            return _shared.jsonify(
                {
                    "tier": "oss",
                    "tier_label": "OSS",
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                }
            )

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-at")
def api_entitlement_capacity_headroom_at():
    """``GET /api/entitlement/capacity-headroom-at?tier=<perspective>&channels=<int>&retention_days=<int>&nodes=<int>``
    -- hypothetical-perspective sibling of
    ``/api/entitlement/capacity-headroom``: per-axis headroom against a
    caller-supplied ``tier``'s static caps rather than the resolved
    entitlement.

    Fills the ``_at`` slot on the capacity-headroom axis alongside
    ``/tiers-for-channel-count-at`` / ``/tiers-for-retention-window-at``
    / ``/tiers-for-node-count-at``, so a pricing-page "what would my
    usage look like on tier X?" walk-through can call every ``_at``
    endpoint uniformly.

    Response shape mirrors ``/api/entitlement/capacity-headroom``
    byte-for-byte; the ``tier`` echo carries the perspective. Returns
    ``{"error": "unknown tier"}`` + HTTP 404 for an empty / unknown
    ``?tier=`` (matches ``/tier-diff-at`` / ``/tiers-for-batch-at``).

    Decoupled from the resolved entitlement (walks the static per-tier
    caps), so grace vs enforce yields byte-identical rows. Never 5xxs.
    """
    try:
        from clawmetry import entitlements as _ent

        perspective = (_shared.request.args.get("tier") or "").strip().lower()
        if not perspective:
            return _shared.jsonify({"error": "unknown tier"}), 404
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        row = _ent.capacity_headroom_at(perspective, **kwargs)
        if row is None:
            return _shared.jsonify({"error": "unknown tier"}), 404
        return _shared.jsonify(row)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_capacity_headroom_at: error: %s", exc)
        return _shared.jsonify({"error": "capacity-headroom-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-headroom")
def api_entitlement_next_tier_capacity_headroom():
    """``GET /api/entitlement/next-tier-capacity-headroom?channels=<int>
    &retention_days=<int>&nodes=<int>`` -- per-axis headroom envelope for
    the tier immediately above the resolved entitlement, given the caller-
    supplied per-axis usage.

    Scalar "one rung up" sibling of ``/api/entitlement/capacity-headroom``.
    Composes ``next_purchasable_tier()`` + ``capacity_headroom_at(next)``
    so an upgrade-CTA card can render "here's what your gauges would look
    like on <next tier>" off ONE call instead of a resolve + at-tier
    round-trip. Sits alongside the caps-only
    ``/api/entitlement/next-tier-capacity-diff`` (which reports cap
    deltas without folding in current usage) and the marginal-features
    ``/api/entitlement/next-tier-unlocks``.

    Response shape (matches ``/api/entitlement/next-tier-unlocks``'s
    envelope byte-for-key so an upgrade-CTA can bind the two off one
    fetch shape)::

        {
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<human>",
          "current_tier_rank":  <int>,
          "direction":          "upgrade",
          "headroom":           <capacity-headroom-at row> | null,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<capacity-headroom-at row>`` -- when non-null -- matches
    ``/api/entitlement/capacity-headroom-at`` byte-for-byte (``tier``
    echoing the next-tier id, per-axis rows in the
    :func:`entitlements._headroom_row` shape) so an existing
    ``/capacity-headroom-at`` renderer consumes the ``headroom`` field
    unchanged.

    ``headroom`` is ``null`` (still HTTP 200) when the resolved
    entitlement is already on the top rung (no next-purchasable tier),
    so the CTA can hide itself off ``headroom == null`` instead of
    branching on status code. Same per-axis "None means axis not
    supplied" posture as ``/api/entitlement/capacity-headroom`` -- an
    axis the caller didn't pass stays ``None`` on the inner row. Same
    bad-arg short-circuit as ``/capacity-headroom`` (blank / non-int /
    negative axis stays ``None``).

    Decoupled from grace vs enforce on the headroom side --
    ``capacity_headroom_at`` walks the static per-tier caps, so the
    inner rows are byte-identical across modes. The "next tier"
    identity itself still tracks the live resolver, so an operator
    moving from ``cloud_starter`` to ``cloud_pro`` sees the target
    flip once activation lands.

    Never 5xxs: on a resolver / delegation failure returns the neutral
    grace envelope (``current_tier=oss``, ``headroom=null``) so a
    paywall tile keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        row = _ent.next_tier_capacity_headroom(**kwargs)
        return _shared.jsonify(
            _shared._neighbour_tier_headroom_envelope(
                direction="upgrade", headroom=row
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_headroom: error: %s", exc
        )
        return _shared.jsonify(
            _shared._neighbour_tier_headroom_envelope(
                direction="upgrade", headroom=None
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-headroom")
def api_entitlement_previous_tier_capacity_headroom():
    """``GET /api/entitlement/previous-tier-capacity-headroom?channels=<int>
    &retention_days=<int>&nodes=<int>`` -- per-axis headroom envelope for
    the tier immediately below the resolved entitlement, given the caller-
    supplied per-axis usage.

    Downgrade twin of ``/api/entitlement/next-tier-capacity-headroom``.
    Composes ``previous_purchasable_tier()`` +
    ``capacity_headroom_at(prev)`` so a downgrade-preview card can show
    "here's what would break on <prev tier>" -- axes whose inner
    ``over_limit`` flips ``True`` are exactly the ones the caller would
    lose headroom on. Sits alongside the caps-only
    ``/api/entitlement/previous-tier-capacity-diff`` and the marginal-
    features ``/api/entitlement/previous-tier-unlocks``.

    Envelope shape matches
    ``/api/entitlement/next-tier-capacity-headroom`` byte-for-key --
    with ``direction`` echoing ``"downgrade"`` -- so a single renderer
    can consume both. Inner ``headroom`` (when non-null) matches
    ``/api/entitlement/capacity-headroom-at`` byte-for-byte.

    ``headroom`` is ``null`` (still HTTP 200) when the resolved
    entitlement is already on the bottom rung (no previous-purchasable
    tier) so the downgrade card can hide itself off ``headroom == null``
    instead of branching on status code. Same per-axis "None means axis
    not supplied" posture, bad-arg short-circuit, and grace / enforce
    invariance as ``/api/entitlement/next-tier-capacity-headroom``.
    Never 5xxs.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        row = _ent.previous_tier_capacity_headroom(**kwargs)
        return _shared.jsonify(
            _shared._neighbour_tier_headroom_envelope(
                direction="downgrade", headroom=row
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_headroom: error: %s", exc
        )
        return _shared.jsonify(
            _shared._neighbour_tier_headroom_envelope(
                direction="downgrade", headroom=None
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-batch")
def api_entitlement_capacity_headroom_batch():
    """``GET /api/entitlement/capacity-headroom-batch?channels=<int>
    &retention_days=<int>&nodes=<int>`` -- per-tier headroom envelope for
    every purchasable tier in one pass, given the caller-supplied per-axis
    usage.

    Plural sibling of ``/api/entitlement/capacity-headroom-at``: where the
    singular ``_at`` endpoint returns one hypothetical tier's per-axis
    envelope, the batch returns the same envelope for every entry in
    :data:`entitlements._PURCHASABLE_TIERS` so a pricing-page "at each
    tier, would my usage fit?" table can render every rung off **one**
    round-trip instead of N calls to ``/capacity-headroom-at``.

    Fills the ``_batch`` slot on the capacity-headroom axis alongside
    ``/capacity-diff-batch`` (per-tier per-axis transition triples against
    the resolved entitlement) and the per-axis
    ``/tiers-for-channel-count-batch`` / ``/tiers-for-retention-window-batch``
    / ``/tiers-for-node-count-batch`` families.

    Response shape::

        {
          "tiers":             [<row>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` matches ``/api/entitlement/capacity-headroom-at`` for
    the same axis inputs byte-for-byte
    (``tier`` / ``tier_label`` / ``channels`` / ``retention_days`` /
    ``nodes``, with each per-axis row matching the
    :func:`entitlements._headroom_row` shape). Rows are sorted by tier
    rank ascending with ``id`` as a stable tiebreaker -- byte-stable
    against ``/capacity-diff-batch`` / ``/tier-unlocks-batch`` /
    ``/tier-locks-batch`` / ``/preview-batch`` so a pricing table lines
    up rung-for-rung without client-side re-sort. The trial tier is
    excluded (mirrors the other ``*-batch`` siblings -- not purchasable).

    Per-axis ``None`` on every row means "axis not supplied" (matches
    ``/capacity-headroom`` and ``/tiers-for-capacity-batch``'s posture).
    A blank, non-int, negative, or ``bool``-in-disguise value on any
    axis short-circuits that axis to ``None`` on every row -- a stray
    query string cannot silently blank the whole ladder.

    Decoupled from the resolved entitlement -- every row walks the
    static per-tier caps -- so grace vs enforce yields byte-identical
    ``tiers`` payloads. The envelope's ``current_tier`` / ``grace`` /
    ``enforced`` still track the live resolver so the UI can highlight
    the caller's current rung on the ladder.

    Never 5xxs: on a resolver failure the empty-tiers grace envelope is
    returned so a pricing table falls back to an empty list instead of
    500-ing.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        rows = _ent.capacity_headroom_batch(**kwargs)
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
            "api_entitlement_capacity_headroom_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-path")
def api_entitlement_capacity_headroom_path():
    """``GET /api/entitlement/capacity-headroom-path?from=<id>&to=<id>
    &channels=<int>&retention_days=<int>&nodes=<int>`` -- per-rung
    capacity-headroom envelope along an arbitrary ``from -> to`` segment,
    given the caller-supplied per-axis usage.

    Path analogue of ``/capacity-headroom-batch`` (which walks every
    purchasable tier) and headroom-shaped mirror of
    ``/capacity-diff-path`` (per-rung marginal capacity transitions),
    ``/tier-unlocks-path`` (marginal grants per rung),
    ``/tier-locks-path`` (marginal losses per rung) and
    ``/preview-path`` (cumulative ``Entitlement.to_dict`` per rung) --
    the fifth member of the capacity axis's ``_path`` family. Lets an
    upgrade-walkthrough surface render the "watch your headroom recover
    rung by rung" view off ONE round-trip without re-deriving per-tier
    caps in JS.

    Rung walk matches ``/capacity-diff-path`` / ``/preview-path`` /
    ``/tier-unlocks-path`` / ``/tier-locks-path`` byte-for-byte (same
    ``_PURCHASABLE_TIERS`` filter + same ``(rank, id)`` /
    ``(-rank, id)`` sort key + same destination-sibling exclusion), so
    the rung ids from this endpoint line up rung-for-rung with those
    four siblings. Same-rank siblings between the endpoints are both
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
          "path":       [<capacity_headroom_at row>, ...],
        }

    Each ``<row>`` matches ``/api/entitlement/capacity-headroom-at`` for
    the same axis inputs byte-for-byte (``tier`` / ``tier_label`` /
    ``channels`` / ``retention_days`` / ``nodes``, with each per-axis row
    matching the :func:`entitlements._headroom_row` shape). Identity
    (``from == to``) returns an empty ``path``. Lateral (same rank,
    different id) returns a single-row path. ``400`` when ``from=`` or
    ``to=`` is missing; ``404`` when either id is unknown. ``trial`` IS
    accepted as an endpoint -- excluded from the walked rungs (not
    purchasable) but the lateral / identity branch still resolves.

    Per-axis ``None`` on every row means "axis not supplied" (matches
    ``/capacity-headroom-batch``'s posture). A blank, non-int, negative,
    or ``bool``-in-disguise value on any axis short-circuits that axis
    to ``None`` on every row -- a stray query string cannot silently
    blank the whole walk.

    Decoupled from the resolved entitlement -- every rung walks the
    static per-tier caps via
    :func:`entitlements.capacity_headroom_at` -- so grace vs enforce
    yields byte-identical ``path`` payloads. Never 5xxs: a resolver
    failure short-circuits to ``404`` so an upgrade-walkthrough surface
    keeps rendering instead of breaking.
    """
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        path = _ent.capacity_headroom_path(f, t, **kwargs)
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
            "api_entitlement_capacity_headroom_path: error: %s", exc
        )
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-batch")
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
        _shared.logger.warning("api_entitlement_capacity_diff_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_target = _shared.request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return _shared.jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
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
                _shared.jsonify(
                    {
                        "error": "capacity-diff-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_capacity_diff_at: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "capacity-diff-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-at-batch")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.capacity_diff_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_capacity_diff_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-diff-at")
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
        body = _ent.tier_diff_at(p, f, t)
        if body is None:
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
        out = {
            "perspective_tier": p,
            "perspective_tier_rank": _ent.tier_rank(p),
            "perspective_tier_label": _ent.tier_label(p),
        }
        out.update(body)
        return _shared.jsonify(out)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_diff_at: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/entitlement/tier-diff-at-batch")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_diff_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_tier_diff_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.capacity_diff_path(f, t)
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
        _shared.logger.warning("api_entitlement_capacity_diff_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/preview")
def api_entitlement_preview():
    """``GET /api/entitlement/preview?tier=<id>`` -- the full
    :meth:`Entitlement.to_dict` shape rendered for a hypothetical tier so an
    upgrade-CTA card can show concrete numbers ("365-day retention, unlimited
    channels, claude_code unlocked") without the client re-deriving per-tier
    capacity. ``404`` when the tier id is unknown."""
    target = (_shared.request.args.get("tier") or "").strip().lower()
    if not target:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.preview(target)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": target}), 404
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_preview: error: %s", exc)
        return _shared.jsonify({"error": "preview failed", "tier": target}), 500

@_shared.bp_entitlement.route("/api/entitlement/preview-batch")
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
        _shared.logger.warning("api_entitlement_preview_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/preview-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_target = _shared.request.args.get("target")
    target = (raw_target or "").strip().lower()
    if not target:
        return _shared.jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if target not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
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
                _shared.jsonify(
                    {
                        "error": "preview-at failed",
                        "tier": tier,
                        "target": target,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "target": target, "preview": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_preview_at: error: %s", exc)
        return _shared.jsonify({"error": "preview-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/preview-at-batch")
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
        targets = _shared._parse_csv_arg("targets")
        if not targets:
            return (
                _shared.jsonify({"error": "supply targets=<csv>"}),
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_preview_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/preview-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.preview_path(f, t)
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
        _shared.logger.warning("api_entitlement_preview_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks")
def api_entitlement_tier_unlocks():
    """``GET /api/entitlement/tier-unlocks?tier=<id>`` -- marginal unlocks
    for ``tier`` (features + runtimes that first become available at that
    tier vs the next-lower purchasable tier). Sibling of ``/preview``
    (cumulative shape). ``404`` when the tier id is unknown (including
    ``trial`` -- not purchasable)."""
    target = (_shared.request.args.get("tier") or "").strip().lower()
    if not target:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_unlocks(target)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": target}), 404
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_unlocks: error: %s", exc)
        return _shared.jsonify({"error": "tier-unlocks failed", "tier": target}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-batch")
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
        _shared.logger.warning("api_entitlement_tier_unlocks_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_unlocks_path(f, t)
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
        _shared.logger.warning("api_entitlement_tier_unlocks_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-unlocks")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_next_tier_unlocks: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "unlocks": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-unlocks")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_previous_tier_unlocks: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "unlocks": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-locks")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_next_tier_locks: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "locks": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-locks")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_previous_tier_locks: error: %s", exc)
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "locks": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks")
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
    target = (_shared.request.args.get("tier") or "").strip().lower()
    if not target:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_locks(target)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": target}), 404
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_locks: error: %s", exc)
        return _shared.jsonify({"error": "tier-locks failed", "tier": target}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-batch")
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
        _shared.logger.warning("api_entitlement_tier_locks_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-path")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not f or not t:
        return _shared.jsonify({"error": "missing from or to"}), 400
    try:
        from clawmetry import entitlements as _ent

        path = _ent.tier_locks_path(f, t)
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
        _shared.logger.warning("api_entitlement_tier_locks_path: error: %s", exc)
        return (
            _shared.jsonify({"error": "unknown tier", "from": f, "to": t}),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/upgrade-path")
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
        return _shared.jsonify(
            {
                "path": _ent.upgrade_path(),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_upgrade_path: error: %s", exc)
        return _shared.jsonify(
            {
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/downgrade-path")
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
        return _shared.jsonify(
            {
                "path": _ent.downgrade_path(),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_downgrade_path: error: %s", exc)
        return _shared.jsonify(
            {
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/upgrade-path-at")
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
    tier = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "tier query parameter is required"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        path = _ent.upgrade_path_at(tier) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_upgrade_path_at: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/downgrade-path-at")
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
    tier = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "tier query parameter is required"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        path = _ent.downgrade_path_at(tier) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_downgrade_path_at: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/upgrade-path-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.upgrade_path_at_batch(tiers)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_upgrade_path_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/downgrade-path-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.downgrade_path_at_batch(tiers)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_downgrade_path_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/required-tier")
def api_entitlement_required_tier():
    try:
        from clawmetry import entitlements as _ent

        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime = (_shared.request.args.get("runtime") or "").strip().lower()
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
            bool(runtime),
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_required_tier: error: %s", exc)
        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime = (_shared.request.args.get("runtime") or "").strip().lower()
        channels_raw = (_shared.request.args.get("channels") or "").strip()
        retention_raw = (_shared.request.args.get("retention_days") or "").strip()
        nodes_raw = (_shared.request.args.get("nodes") or "").strip()
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
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/has-feature")
def api_entitlement_has_feature():
    """``GET /api/entitlement/has-feature?feature=<id>`` -- boolean-gate
    scalar sibling of ``/api/entitlement/required-tier?feature=<id>``.

    Returns ONE boolean (``has_feature``) plus the surrounding tier
    envelope (``current_tier``, ``required_tier``, ``upgrade_required``)
    so a paywall tile can bind ``allowed`` directly off this URL without
    parsing the full required-tier body. Grace-safe: while
    :attr:`Entitlement.grace` is ``True`` (the current rollout state)
    ``has_feature`` reports ``True`` for every KNOWN feature id, so
    wiring this into a gate today changes NO current behavior.
    Unknown / empty / non-string ids collapse to ``has_feature=False``
    without an HTTP 4xx (the never-crash posture matches the sibling
    ``/api/entitlement/required-tier`` and ``/api/entitlement/lock-reason``
    endpoints). Never 5xx.
    """
    try:
        from clawmetry import entitlements as _ent

        return _shared.jsonify(
            _shared._has_axis_body(
                "feature",
                _ent.min_tier_for_feature,
                _ent.has_feature,
            )
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_feature: error: %s", exc)
        key = (_shared.request.args.get("feature") or "").strip().lower()
        return _shared.jsonify(_shared._has_axis_fallback("feature", key))

@_shared.bp_entitlement.route("/api/entitlement/has-runtime")
def api_entitlement_has_runtime():
    """``GET /api/entitlement/has-runtime?runtime=<id>`` -- runtime-axis
    mirror of ``/api/entitlement/has-feature``.

    Same 8-key envelope with ``runtime`` / ``has_runtime`` in the
    axis-specific slots. Grace-safe: ``has_runtime`` reports ``True``
    for every known runtime id while grace is on; unknown / empty ids
    collapse to ``False``. Never 5xx.
    """
    try:
        from clawmetry import entitlements as _ent

        return _shared.jsonify(
            _shared._has_axis_body(
                "runtime",
                _ent.min_tier_for_runtime,
                _ent.has_runtime,
            )
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_runtime: error: %s", exc)
        key = (_shared.request.args.get("runtime") or "").strip().lower()
        return _shared.jsonify(_shared._has_axis_fallback("runtime", key))

@_shared.bp_entitlement.route("/api/entitlement/has-feature-at")
def api_entitlement_has_feature_at():
    """``GET /api/entitlement/has-feature-at?tier=<perspective>&feature=<id>``
    -- what-if boolean-gate scalar sibling of ``/api/entitlement/has-feature``.

    Returns ONE boolean (``has_feature_at``) plus a what-if envelope that
    tells the caller which perspective they asked about, whether the
    requested feature is admitted by that perspective, the cheapest tier
    that would unlock it (``required_tier``, byte-parity with the sibling
    ``/api/entitlement/min-tier-for-feature`` answer), and the LIVE
    resolver context (``current_tier`` / ``grace`` / ``enforced``) so a
    pricing matrix can render "you are here" alongside "would tier X
    grant this?" off ONE URL per cell.

    Unlike the live ``/has-feature`` sibling this endpoint is
    perspective-shaped: even in grace ``has_feature_at="oss","fleet"`` is
    ``False`` (because OSS-free does not statically grant ``fleet``),
    whereas ``/has-feature?feature=fleet`` in grace returns ``True``.
    That is the whole point of the ``_at`` slot -- render the
    would-be-locked state alongside the live grant.

    Never 4xxs (missing / blank / unknown tier or feature -> 200 with
    ``has_feature_at=false``, matching the ``/has-feature`` posture --
    a paywall matrix tile binds ``allowed`` directly without a
    pre-validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_has_axis_at_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_axis_at_body("feature"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_feature_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        key = (_shared.request.args.get("feature") or "").strip().lower()
        return _shared.jsonify(_shared._has_axis_at_fallback("feature", tier, key))

@_shared.bp_entitlement.route("/api/entitlement/has-runtime-at")
def api_entitlement_has_runtime_at():
    """``GET /api/entitlement/has-runtime-at?tier=<perspective>&runtime=<id>``
    -- runtime-axis twin of ``/api/entitlement/has-feature-at``.

    Same 12-key envelope with ``runtime`` / ``has_runtime_at`` in the
    axis-specific slots. Runtime-alias canonicalisation
    (``claude-code`` -> ``claude_code``) is applied upstream at the
    endpoint layer so ``?runtime=claude-code`` collapses to the granted
    ``claude_code`` -- matches the sibling ``/has-runtime`` endpoint's
    own upstream-canonicalise pattern. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_axis_at_body("runtime"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_runtime_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        raw_key = (_shared.request.args.get("runtime") or "").strip().lower()
        try:
            from clawmetry import entitlements as _ent

            key = _ent.canonical_runtime(raw_key) or raw_key
        except Exception:
            key = raw_key
        return _shared.jsonify(_shared._has_axis_at_fallback("runtime", tier, key))

@_shared.bp_entitlement.route("/api/entitlement/has-channel-count")
def api_entitlement_has_channel_count():
    """``GET /api/entitlement/has-channel-count?count=<N>`` -- capacity-axis
    boolean-gate scalar sibling of ``/api/entitlement/has-feature`` /
    ``/api/entitlement/has-runtime``.

    Returns ONE boolean (``has_channel_count``) plus the surrounding tier
    envelope (``current_tier``, ``required_tier``, ``upgrade_required``) so a
    paywall tile on the channels surface can bind ``allowed`` directly off this
    URL without parsing the full ``/api/entitlement/required-tier?channels=<N>``
    body. Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) ``has_channel_count`` reports ``True`` for every finite
    count, so wiring this into a gate today changes NO current behavior.

    Envelope shape (10 keys, byte-stable across every input branch)::

        {
          "count": 5,                    # parsed int, null on missing/unparseable/blowup
          "count_raw": "5",              # stripped raw string echo
          "has_channel_count": True,
          "allowed": True,               # mirror of has_channel_count
          "required_tier": "cloud_starter",
          "required_tier_label": "Starter",
          "required_tier_rank": 1,
          "current_tier": "oss",
          "current_tier_rank": 0,
          "upgrade_required": True,
        }

    Input semantics:

    * ``?count=`` missing / blank / whitespace / unparseable -- ``count=null``,
      ``has_channel_count=false``, ``required_tier=null``. Never 4xx (matches
      the never-crash posture of ``/api/entitlement/required-tier`` and
      ``/api/entitlement/lock-reason`` on their capacity axes).
    * ``count <= 0`` -- ``has_channel_count=true``, ``required_tier="oss"``
      (trivially satisfied by the free floor -- mirrors
      :func:`min_tier_for_channel_count` and
      :meth:`Entitlement.allows_channel_count`).
    * Positive int -- ``has_channel_count`` reflects the resolver;
      ``required_tier`` is the cheapest tier admitting ``count`` per
      :func:`min_tier_for_channel_count`.

    Cross-consistency: ``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank`` agree byte-for-byte with
    ``/api/entitlement/required-tier?channels=<N>`` for the same ``count`` so a
    UI wiring both endpoints for the same paywall tile can't see inconsistent
    tier state.

    Never 5xx: any resolver blowup collapses to :func:`_has_channel_count_fallback`.
    """
    count_raw = (_shared.request.args.get("count") or "").strip()
    try:
        from clawmetry import entitlements as _ent

        try:
            n = int(count_raw)
            parsed_ok = True
        except (TypeError, ValueError):
            n = None
            parsed_ok = False

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)

        if not parsed_ok:
            return _shared.jsonify(
                {
                    "count": None,
                    "count_raw": count_raw,
                    "has_channel_count": False,
                    "allowed": False,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "upgrade_required": False,
                }
            )

        has_flag = _ent.has_channel_count(n)
        required = _ent.min_tier_for_channel_count(n)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "count": n,
                "count_raw": count_raw,
                "has_channel_count": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_channel_count: error: %s", exc)
        return _shared.jsonify(_shared._has_channel_count_fallback(count_raw))

@_shared.bp_entitlement.route("/api/entitlement/has-channel-count-at")
def api_entitlement_has_channel_count_at():
    """``GET /api/entitlement/has-channel-count-at?tier=<perspective>&count=<N>``
    -- what-if capacity-axis boolean-gate scalar sibling of
    ``/api/entitlement/has-channel-count``.

    Channel-capacity twin of ``/api/entitlement/has-feature-at`` /
    ``/api/entitlement/has-runtime-at`` on the grant axes and of
    ``/api/entitlement/has-node-count-at`` on the sibling fleet capacity
    axis. Returns ONE boolean (``has_channel_count_at``) plus a what-if
    envelope that tells the caller which perspective they asked about,
    whether that perspective admits ``count`` channels, the cheapest
    tier that would admit it (``required_tier``, byte-parity with the
    sibling ``/api/entitlement/required-tier?channels=<N>`` answer), and
    the LIVE resolver context (``current_tier`` / ``grace`` /
    ``enforced``) so a channels pricing matrix can render "you are here"
    alongside "would tier X admit this?" off ONE URL per cell.

    Unlike the live ``/has-channel-count`` sibling this endpoint is
    perspective-shaped: even in grace
    ``/has-channel-count-at?tier=oss&count=5`` returns ``allowed=false``
    (because the OSS-free tier statically caps at
    :data:`_FREE_CHANNEL_LIMIT` channels), whereas
    ``/has-channel-count?count=5`` in grace returns ``true`` via
    :meth:`Entitlement.allows_channel_count`'s grace-passthrough. That
    is the whole point of the ``_at`` slot -- render the would-be-locked
    state alongside the live grant.

    13-key envelope (adds ``tier`` + ``perspective_tier_rank`` + ``grace``
    / ``enforced`` on top of the sibling ``/has-channel-count`` shape,
    drops ``upgrade_required`` since the perspective is the what-if
    tier, not the actual current one)::

        {
          "tier":                  "<perspective tier id>" | "",
          "count":                 <int> | null,        # parsed, null on missing/unparseable
          "count_raw":             "<stripped raw>",
          "has_channel_count_at":  <bool>,
          "allowed":               <bool>,              # alias of has_channel_count_at
          "required_tier":         "<tier id>" | null,  # min_tier_for_channel_count(count)
          "required_tier_label":   "<label>"   | null,
          "required_tier_rank":    <int>,               # -1 when required_tier null
          "perspective_tier_rank": <int>,               # -1 when tier unknown/blank
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,              # live resolver grace bit
          "enforced":              <bool>,
        }

    Input semantics mirror the sibling ``/has-feature-at`` +
    ``/has-node-count-at`` + ``/has-channel-count`` endpoints:

    * ``?tier=`` missing / blank / whitespace / unknown perspective ->
      ``has_channel_count_at=false``, ``perspective_tier_rank=-1``.
      Never 4xx.
    * ``?count=`` missing / blank / whitespace / unparseable ->
      ``count=null``, ``has_channel_count_at=false``,
      ``required_tier=null``. Never 4xx.
    * ``count <= 0`` on a valid perspective ->
      ``has_channel_count_at=true``, ``required_tier="oss"``
      (trivially satisfied by the free floor -- mirrors
      :func:`min_tier_for_channel_count`).
    * Positive int on a valid perspective -> ``has_channel_count_at``
      reflects the static per-tier cap in :data:`_TIER_CHANNEL_LIMIT`;
      ``required_tier`` is the cheapest tier admitting ``count`` per
      :func:`min_tier_for_channel_count` (perspective-independent;
      matches the ``/has-channel-count`` sibling byte-for-byte).

    Never 5xx: any resolver blowup collapses to
    :func:`_has_channel_count_at_fallback`.
    """
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    count_raw = (_shared.request.args.get("count") or "").strip()
    try:
        from clawmetry import entitlements as _ent

        try:
            n = int(count_raw)
            parsed_ok = True
        except (TypeError, ValueError):
            n = None
            parsed_ok = False

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        persp_rank = (
            _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
        )

        if not parsed_ok:
            return _shared.jsonify(
                {
                    "tier": tier,
                    "count": None,
                    "count_raw": count_raw,
                    "has_channel_count_at": False,
                    "allowed": False,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "perspective_tier_rank": persp_rank,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "grace": bool(ent.grace),
                    "enforced": _ent.is_enforced(),
                }
            )

        has_flag = _ent.has_channel_count_at(tier, n)
        required = _ent.min_tier_for_channel_count(n)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "tier": tier,
                "count": n,
                "count_raw": count_raw,
                "has_channel_count_at": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "perspective_tier_rank": persp_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_channel_count_at: error: %s", exc)
        return _shared.jsonify(_shared._has_channel_count_at_fallback(tier, count_raw))

@_shared.bp_entitlement.route("/api/entitlement/has-retention-window")
def api_entitlement_has_retention_window():
    """``GET /api/entitlement/has-retention-window?days=<N|unlimited>`` --
    capacity-axis boolean-gate scalar sibling of
    ``/api/entitlement/has-feature`` / ``/api/entitlement/has-runtime`` /
    ``/api/entitlement/has-channel-count`` on the ``retention_days`` axis.

    Returns ONE boolean (``has_retention_window``) plus the surrounding tier
    envelope (``current_tier``, ``required_tier``, ``upgrade_required``) so a
    history-range paywall tile can bind ``allowed`` directly off this URL
    without parsing the full
    ``/api/entitlement/required-tier?retention_days=<N>`` body. Grace-safe:
    while :attr:`Entitlement.grace` is ``True`` (the current rollout state)
    ``has_retention_window`` reports ``True`` for every finite ``days`` value
    AND the ``unlimited`` request, so wiring this into a gate today changes
    NO current behavior.

    Envelope shape (11 keys, byte-stable across every input branch)::

        {
          "days": 30,                    # parsed int, null on missing/unparseable/unlimited/blowup
          "days_raw": "30",              # stripped raw string echo
          "unlimited": False,            # True iff ?days=unlimited (case-insensitive)
          "has_retention_window": True,
          "allowed": True,               # mirror of has_retention_window
          "required_tier": "cloud_starter",
          "required_tier_label": "Starter",
          "required_tier_rank": 1,
          "current_tier": "oss",
          "current_tier_rank": 0,
          "upgrade_required": True,
        }

    Input semantics:

    * ``?days=`` missing / blank / whitespace -- ``days=null``,
      ``unlimited=false``, ``has_retention_window=false``,
      ``required_tier=null``. Never 4xx (matches the never-crash posture of
      ``/api/entitlement/required-tier`` and ``/api/entitlement/lock-reason``
      on their capacity axes).
    * ``?days=unlimited`` (case-insensitive) -- explicit unlimited-history
      request. ``days=null``, ``unlimited=true``,
      ``has_retention_window`` reflects the resolver (grace: ``true`` on
      every tier; enforce: only Enterprise grants it), ``required_tier`` is
      the cheapest tier admitting the unlimited window per
      :func:`min_tier_for_retention_window(None)` (Enterprise on the current
      tier table).
    * ``?days=`` non-int junk (``bogus`` / ``5.5`` / ...) --
      ``has_retention_window=false``, ``days=null``, ``required_tier=null``,
      ``unlimited=false``. Fail-closed matches
      :func:`has_retention_window` / :func:`has_channel_count` on parse
      failure.
    * ``days <= 0`` -- ``has_retention_window=true``,
      ``required_tier="oss"`` (trivially satisfied by the free floor --
      mirrors :func:`min_tier_for_retention_window` and
      :meth:`Entitlement.allows_retention_window`).
    * Positive int -- ``has_retention_window`` reflects the resolver;
      ``required_tier`` is the cheapest tier admitting ``days`` per
      :func:`min_tier_for_retention_window`.

    Cross-consistency: ``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank`` agree byte-for-byte with
    ``/api/entitlement/required-tier?retention_days=<N>`` for the same
    parsed ``days`` so a UI wiring both endpoints for the same paywall tile
    can't see inconsistent tier state.

    Never 5xx: any resolver blowup collapses to
    :func:`_has_retention_window_fallback`.
    """
    days_raw = (_shared.request.args.get("days") or "").strip()
    unlimited = days_raw.lower() == "unlimited"
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)

        if unlimited:
            n: int | None = None
            has_flag = _ent.has_retention_window(None)
            required = _ent.min_tier_for_retention_window(None)
        elif not days_raw:
            n = None
            has_flag = False
            required = None
        else:
            try:
                n = int(days_raw)
            except (TypeError, ValueError):
                n = None
                has_flag = False
                required = None
            else:
                has_flag = _ent.has_retention_window(n)
                required = _ent.min_tier_for_retention_window(n)

        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "days": n,
                "days_raw": days_raw,
                "unlimited": unlimited,
                "has_retention_window": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_retention_window: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_retention_window_fallback(days_raw, unlimited)
        )

@_shared.bp_entitlement.route("/api/entitlement/has-retention-window-at")
def api_entitlement_has_retention_window_at():
    """``GET /api/entitlement/has-retention-window-at?tier=<perspective>&days=<N|unlimited>``
    -- what-if capacity-axis boolean-gate scalar sibling of
    ``/api/entitlement/has-retention-window``.

    Retention-capacity twin of ``/api/entitlement/has-feature-at`` /
    ``/api/entitlement/has-runtime-at`` on the grant axes and of
    ``/api/entitlement/has-channel-count-at`` /
    ``/api/entitlement/has-node-count-at`` on the sibling capacity axes.
    Returns ONE boolean (``has_retention_window_at``) plus a what-if
    envelope that tells the caller which perspective they asked about,
    whether that perspective admits ``days`` of history, the cheapest tier
    that would admit it (``required_tier``, byte-parity with the sibling
    ``/api/entitlement/required-tier?retention_days=<N>`` answer), and the
    LIVE resolver context (``current_tier`` / ``grace`` / ``enforced``) so
    a history-range pricing matrix can render "you are here" alongside
    "would tier X admit this?" off ONE URL per cell.

    Unlike the live ``/has-retention-window`` sibling this endpoint is
    perspective-shaped: even in grace
    ``/has-retention-window-at?tier=oss&days=30`` returns ``allowed=false``
    (because the OSS-free tier statically caps at 7 days), whereas
    ``/has-retention-window?days=30`` in grace returns ``true`` via
    :meth:`Entitlement.allows_retention_window`'s grace-passthrough. That
    is the whole point of the ``_at`` slot -- render the would-be-locked
    state alongside the live grant.

    14-key envelope (adds ``tier`` + ``perspective_tier_rank`` + ``grace``
    / ``enforced`` on top of the sibling ``/has-retention-window`` shape,
    drops ``upgrade_required`` since the perspective is the what-if tier,
    not the actual current one)::

        {
          "tier":                    "<perspective tier id>" | "",
          "days":                    <int> | null,        # parsed, null on missing/unparseable/unlimited/blowup
          "days_raw":                "<stripped raw>",
          "unlimited":               <bool>,              # True iff ?days=unlimited (case-insensitive)
          "has_retention_window_at": <bool>,
          "allowed":                 <bool>,              # alias of has_retention_window_at
          "required_tier":           "<tier id>" | null,  # min_tier_for_retention_window(days)
          "required_tier_label":     "<label>"   | null,
          "required_tier_rank":      <int>,               # -1 when required_tier null
          "perspective_tier_rank":   <int>,               # -1 when tier unknown/blank
          "current_tier":            "<live tier id>",
          "current_tier_rank":       <int>,
          "grace":                   <bool>,              # live resolver grace bit
          "enforced":                <bool>,
        }

    Input semantics mirror the sibling ``/has-feature-at`` +
    ``/has-channel-count-at`` + ``/has-node-count-at`` +
    ``/has-retention-window`` endpoints:

    * ``?tier=`` missing / blank / whitespace / unknown perspective ->
      ``has_retention_window_at=false``, ``perspective_tier_rank=-1``.
      Never 4xx.
    * ``?days=`` missing / blank / whitespace ->
      ``has_retention_window_at=false``, ``days=null``,
      ``required_tier=null``, ``unlimited=false``. Never 4xx (matches
      the never-crash posture of the sibling ``/has-retention-window``
      endpoint on missing input).
    * ``?days=unlimited`` (case-insensitive) -- explicit unlimited-history
      request. ``days=null``, ``unlimited=true``,
      ``has_retention_window_at`` reflects the perspective's static cap
      (Enterprise -> ``true``; every other perspective -> ``false``,
      even in grace), ``required_tier`` routes to
      :func:`min_tier_for_retention_window(None)` (Enterprise on the
      current tier table).
    * ``?days=`` non-int junk (``bogus`` / ``5.5`` / ...) ->
      ``has_retention_window_at=false``, ``days=null``,
      ``required_tier=null``, ``unlimited=false``. Fail-closed matches
      :func:`has_retention_window_at` / :func:`has_channel_count_at` on
      parse failure.
    * ``days <= 0`` on a valid perspective ->
      ``has_retention_window_at=true``, ``required_tier="oss"``
      (trivially satisfied by the free floor -- mirrors
      :func:`min_tier_for_retention_window`).
    * Positive int on a valid perspective ->
      ``has_retention_window_at`` reflects the static per-tier cap in
      :data:`_TIER_RETENTION_DAYS`; ``required_tier`` is the cheapest
      tier admitting ``days`` per
      :func:`min_tier_for_retention_window` (perspective-independent;
      matches the ``/has-retention-window`` sibling byte-for-byte).

    Never 5xx: any resolver blowup collapses to
    :func:`_has_retention_window_at_fallback`.
    """
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    days_raw = (_shared.request.args.get("days") or "").strip()
    unlimited = days_raw.lower() == "unlimited"
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        persp_rank = (
            _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
        )

        if unlimited:
            n: int | None = None
            has_flag = _ent.has_retention_window_at(tier, None)
            required = _ent.min_tier_for_retention_window(None)
        elif not days_raw:
            n = None
            has_flag = False
            required = None
        else:
            try:
                n = int(days_raw)
            except (TypeError, ValueError):
                n = None
                has_flag = False
                required = None
            else:
                has_flag = _ent.has_retention_window_at(tier, n)
                required = _ent.min_tier_for_retention_window(n)

        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "tier": tier,
                "days": n,
                "days_raw": days_raw,
                "unlimited": unlimited,
                "has_retention_window_at": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "perspective_tier_rank": persp_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_retention_window_at: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_retention_window_at_fallback(tier, days_raw, unlimited)
        )

@_shared.bp_entitlement.route("/api/entitlement/has-node-count")
def api_entitlement_has_node_count():
    """``GET /api/entitlement/has-node-count?count=<N>`` -- capacity-axis
    boolean-gate scalar sibling of ``/api/entitlement/has-feature`` /
    ``/api/entitlement/has-runtime`` / ``/api/entitlement/has-channel-count``.

    Returns ONE boolean (``has_node_count``) plus the surrounding tier
    envelope (``current_tier``, ``required_tier``, ``upgrade_required``) so a
    paywall tile on the fleet surface can bind ``allowed`` directly off this
    URL without parsing the full ``/api/entitlement/required-tier?nodes=<N>``
    body. Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) ``has_node_count`` reports ``True`` for every finite count,
    so wiring this into a gate today changes NO current behavior.

    Envelope shape (10 keys, byte-stable across every input branch)::

        {
          "count": 5,                    # parsed int, null on missing/unparseable/blowup
          "count_raw": "5",              # stripped raw string echo
          "has_node_count": True,
          "allowed": True,               # mirror of has_node_count
          "required_tier": "cloud_starter",
          "required_tier_label": "Starter",
          "required_tier_rank": 1,
          "current_tier": "oss",
          "current_tier_rank": 0,
          "upgrade_required": True,
        }

    Input semantics:

    * ``?count=`` missing / blank / whitespace / unparseable -- ``count=null``,
      ``has_node_count=false``, ``required_tier=null``. Never 4xx (matches
      the never-crash posture of ``/api/entitlement/required-tier`` and
      ``/api/entitlement/lock-reason`` on their capacity axes).
    * ``count <= 0`` -- ``has_node_count=true``, ``required_tier="oss"``
      (trivially satisfied by the free floor -- mirrors
      :func:`min_tier_for_node_count` and
      :meth:`Entitlement.allows_node_count`).
    * Positive int -- ``has_node_count`` reflects the resolver;
      ``required_tier`` is the cheapest tier admitting ``count`` per
      :func:`min_tier_for_node_count`.

    Cross-consistency: ``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank`` agree byte-for-byte with
    ``/api/entitlement/required-tier?nodes=<N>`` for the same ``count`` so a
    UI wiring both endpoints for the same paywall tile can't see inconsistent
    tier state.

    Never 5xx: any resolver blowup collapses to :func:`_has_node_count_fallback`.
    """
    count_raw = (_shared.request.args.get("count") or "").strip()
    try:
        from clawmetry import entitlements as _ent

        try:
            n = int(count_raw)
            parsed_ok = True
        except (TypeError, ValueError):
            n = None
            parsed_ok = False

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)

        if not parsed_ok:
            return _shared.jsonify(
                {
                    "count": None,
                    "count_raw": count_raw,
                    "has_node_count": False,
                    "allowed": False,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "upgrade_required": False,
                }
            )

        has_flag = _ent.has_node_count(n)
        required = _ent.min_tier_for_node_count(n)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "count": n,
                "count_raw": count_raw,
                "has_node_count": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_node_count: error: %s", exc)
        return _shared.jsonify(_shared._has_node_count_fallback(count_raw))

@_shared.bp_entitlement.route("/api/entitlement/has-node-count-at")
def api_entitlement_has_node_count_at():
    """``GET /api/entitlement/has-node-count-at?tier=<perspective>&count=<N>``
    -- what-if capacity-axis boolean-gate scalar sibling of
    ``/api/entitlement/has-node-count``.

    Node-capacity twin of ``/api/entitlement/has-feature-at`` /
    ``/api/entitlement/has-runtime-at``. Returns ONE boolean
    (``has_node_count_at``) plus a what-if envelope that tells the
    caller which perspective they asked about, whether that perspective
    admits ``count`` nodes, the cheapest tier that would admit it
    (``required_tier``, byte-parity with the sibling
    ``/api/entitlement/required-tier?nodes=<N>`` answer), and the LIVE
    resolver context (``current_tier`` / ``grace`` / ``enforced``) so a
    fleet pricing matrix can render "you are here" alongside "would tier
    X admit this?" off ONE URL per cell.

    Unlike the live ``/has-node-count`` sibling this endpoint is
    perspective-shaped: even in grace
    ``/has-node-count-at?tier=oss&count=5`` returns ``allowed=false``
    (because the OSS-free tier statically caps at 1 node), whereas
    ``/has-node-count?count=5`` in grace returns ``true`` via
    :meth:`Entitlement.allows_node_count`'s grace-passthrough. That is
    the whole point of the ``_at`` slot -- render the would-be-locked
    state alongside the live grant.

    13-key envelope (adds ``tier`` + ``perspective_tier_rank`` + ``grace``
    / ``enforced`` on top of the sibling ``/has-node-count`` shape, drops
    ``upgrade_required`` since the perspective is the what-if tier, not
    the actual current one)::

        {
          "tier":                  "<perspective tier id>" | "",
          "count":                 <int> | null,        # parsed, null on missing/unparseable
          "count_raw":             "<stripped raw>",
          "has_node_count_at":     <bool>,
          "allowed":               <bool>,               # alias of has_node_count_at
          "required_tier":         "<tier id>" | null,  # min_tier_for_node_count(count)
          "required_tier_label":   "<label>"   | null,
          "required_tier_rank":    <int>,               # -1 when required_tier null
          "perspective_tier_rank": <int>,               # -1 when tier unknown/blank
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,              # live resolver grace bit
          "enforced":              <bool>,
        }

    Input semantics mirror the sibling ``/has-feature-at`` +
    ``/has-node-count`` endpoints:

    * ``?tier=`` missing / blank / whitespace / unknown perspective ->
      ``has_node_count_at=false``, ``perspective_tier_rank=-1``. Never 4xx.
    * ``?count=`` missing / blank / whitespace / unparseable -> ``count=null``,
      ``has_node_count_at=false``, ``required_tier=null``. Never 4xx.
    * ``count <= 0`` on a valid perspective -> ``has_node_count_at=true``,
      ``required_tier="oss"`` (trivially satisfied by the free floor --
      mirrors :func:`min_tier_for_node_count`).
    * Positive int on a valid perspective -> ``has_node_count_at``
      reflects the static per-tier cap in :data:`_TIER_NODE_LIMIT`;
      ``required_tier`` is the cheapest tier admitting ``count`` per
      :func:`min_tier_for_node_count` (perspective-independent; matches
      the ``/has-node-count`` sibling byte-for-byte).

    Never 5xx: any resolver blowup collapses to
    :func:`_has_node_count_at_fallback`.
    """
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    count_raw = (_shared.request.args.get("count") or "").strip()
    try:
        from clawmetry import entitlements as _ent

        try:
            n = int(count_raw)
            parsed_ok = True
        except (TypeError, ValueError):
            n = None
            parsed_ok = False

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        persp_rank = (
            _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
        )

        if not parsed_ok:
            return _shared.jsonify(
                {
                    "tier": tier,
                    "count": None,
                    "count_raw": count_raw,
                    "has_node_count_at": False,
                    "allowed": False,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "perspective_tier_rank": persp_rank,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "grace": bool(ent.grace),
                    "enforced": _ent.is_enforced(),
                }
            )

        has_flag = _ent.has_node_count_at(tier, n)
        required = _ent.min_tier_for_node_count(n)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "tier": tier,
                "count": n,
                "count_raw": count_raw,
                "has_node_count_at": bool(has_flag),
                "allowed": bool(has_flag),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "perspective_tier_rank": persp_rank,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_node_count_at: error: %s", exc)
        return _shared.jsonify(_shared._has_node_count_at_fallback(tier, count_raw))

@_shared.bp_entitlement.route("/api/entitlement/has-node-count-batch")
def api_entitlement_has_node_count_batch():
    """``GET /api/entitlement/has-node-count-batch?counts=1,5,100`` -- per-
    value boolean-gate batch sibling of ``/api/entitlement/has-node-count``
    on the ``nodes`` capacity axis.

    Node-axis twin of the not-yet-existing has-channel-count-batch /
    has-retention-window-batch endpoints. Where the singular
    ``/has-node-count?count=<N>`` endpoint answers ONE
    (``has_node_count``, ``required_tier``) pair per request, this batch
    answers all requested counts in ONE round-trip so a fleet paywall
    matrix ("does the current install admit 1? 5? 100 nodes?") binds
    off one URL instead of ``N`` calls.

    ``?counts=`` is a comma-separated list. Empty / whitespace tokens
    are dropped, duplicates by normalised int key are dropped preserving
    first-seen order, non-int tokens pass through as one row with
    ``unknown=true`` / ``has_node_count=false`` (matches
    :func:`has_node_count`'s strict callsite-typo posture). Missing /
    blank ``?counts=`` -> ``400`` (matches the sibling
    ``/api/entitlement/min-tier-for-node-count-batch`` posture).

    Per-row body shape (extends the singular ``/has-node-count`` shape
    with ``kind`` / ``label`` / ``unknown`` / ``count_raw`` so a UI
    already rendering ``min-tier-for-node-count-batch`` rows can rebind
    without reshaping)::

        {
          "count":              <int> | null,
          "count_raw":          "<stripped raw token>",
          "kind":               "node_count",
          "label":              "1 node" | "5 nodes" | null,
          "has_node_count":     <bool>,
          "allowed":            <bool>,               # mirror of has_node_count
          "unknown":            <bool>,               # true iff non-int input
          "required_tier":      "<tier id>" | null,
          "required_tier_label":"<label>"   | null,
          "required_tier_rank": <int>,                # -1 when required_tier null
          "upgrade_required":   <bool>,               # required_tier_rank > current_tier_rank
        }

    Envelope wraps ``rows`` with ``kind`` / ``count`` (row count) plus
    the standard resolver envelope (``current_tier`` /
    ``current_tier_rank`` / ``grace`` / ``enforced``) so a UI can render
    "you are here" once alongside the per-row grants.

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) every KNOWN row reports ``has_node_count=true``, so
    wiring this into a fleet gate today changes NO current behavior.
    Post-enforcement each row reflects the resolver's live grant.

    Cross-consistency: the ``required_tier`` on each row agrees byte-for-
    byte with ``/api/entitlement/required-tier?nodes=<count>`` and with
    the per-row ``required_tier`` on the sibling
    ``/api/entitlement/min-tier-for-node-count-batch`` -- a UI wiring
    both for the same paywall matrix cannot see inconsistent tier state.

    Never 5xx: any resolver blowup collapses to
    :func:`_has_node_count_batch_fallback`.
    """
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        scalar_rows = _ent.has_node_count_batch(values)
        raw_by_key: dict[str, str] = {}
        for raw in values:
            try:
                key = str(int(raw))
            except (TypeError, ValueError):
                key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_node_count_batch_row_to_body(
                r, raw_by_key.get(str(r.get("key")), str(r.get("key"))), cur_rank
            )
            for r in scalar_rows
        ]
        return _shared.jsonify(
            {
                "kind": "node_count",
                "count": len(rows),
                "rows": rows,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_node_count_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._has_node_count_batch_fallback())

@_shared.bp_entitlement.route("/api/entitlement/has-channel-count-batch")
def api_entitlement_has_channel_count_batch():
    """``GET /api/entitlement/has-channel-count-batch?counts=1,5,100`` --
    per-value boolean-gate batch sibling of
    ``/api/entitlement/has-channel-count`` on the ``channels`` capacity
    axis.

    Channel-axis twin of ``/api/entitlement/has-node-count-batch`` and
    of the retention-axis
    ``/api/entitlement/has-retention-window-batch``. Where the singular
    ``/has-channel-count?count=<N>`` endpoint answers ONE
    (``has_channel_count``, ``required_tier``) pair per request, this
    batch answers all requested counts in ONE round-trip so a channels
    paywall matrix ("does the current install admit 1? 5? 25 channels?")
    binds off one URL instead of ``N`` calls.

    ``?counts=`` is a comma-separated list. Empty / whitespace tokens
    are dropped, duplicates by normalised int key are dropped preserving
    first-seen order, non-int tokens pass through as one row with
    ``unknown=true`` / ``has_channel_count=false`` (matches
    :func:`has_channel_count`'s strict callsite-typo posture). Missing /
    blank ``?counts=`` -> ``400`` (matches the sibling
    ``/api/entitlement/min-tier-for-channel-count-batch`` /
    ``/has-node-count-batch`` posture).

    Per-row body shape (extends the singular ``/has-channel-count``
    shape with ``kind`` / ``label`` / ``unknown`` / ``count_raw`` so a
    UI already rendering ``min-tier-for-channel-count-batch`` rows can
    rebind without reshaping)::

        {
          "count":              <int> | null,
          "count_raw":          "<stripped raw token>",
          "kind":               "channel_count",
          "label":              "1 channel" | "5 channels" | null,
          "has_channel_count":  <bool>,
          "allowed":            <bool>,               # mirror of has_channel_count
          "unknown":            <bool>,               # true iff non-int input
          "required_tier":      "<tier id>" | null,
          "required_tier_label":"<label>"   | null,
          "required_tier_rank": <int>,                # -1 when required_tier null
          "upgrade_required":   <bool>,               # required_tier_rank > current_tier_rank
        }

    Envelope wraps ``rows`` with ``kind`` / ``count`` (row count) plus
    the standard resolver envelope (``current_tier`` /
    ``current_tier_rank`` / ``grace`` / ``enforced``) so a UI can render
    "you are here" once alongside the per-row grants.

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) every KNOWN row reports ``has_channel_count=true``,
    so wiring this into a channels gate today changes NO current
    behavior. Post-enforcement each row reflects the resolver's live
    grant.

    Cross-consistency: the ``required_tier`` on each row agrees byte-
    for-byte with ``/api/entitlement/required-tier?channels=<count>``
    and with the per-row ``required_tier`` on the sibling
    ``/api/entitlement/min-tier-for-channel-count-batch`` -- a UI wiring
    both for the same paywall matrix cannot see inconsistent tier state.

    Never 5xx: any resolver blowup collapses to
    :func:`_has_channel_count_batch_fallback`.
    """
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        scalar_rows = _ent.has_channel_count_batch(values)
        raw_by_key: dict[str, str] = {}
        for raw in values:
            try:
                key = str(int(raw))
            except (TypeError, ValueError):
                key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_channel_count_batch_row_to_body(
                r, raw_by_key.get(str(r.get("key")), str(r.get("key"))), cur_rank
            )
            for r in scalar_rows
        ]
        return _shared.jsonify(
            {
                "kind": "channel_count",
                "count": len(rows),
                "rows": rows,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_channel_count_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._has_channel_count_batch_fallback())

@_shared.bp_entitlement.route("/api/entitlement/has-retention-window-batch")
def api_entitlement_has_retention_window_batch():
    """``GET /api/entitlement/has-retention-window-batch?days=7,30,unlimited``
    -- per-value boolean-gate batch sibling of
    ``/api/entitlement/has-retention-window`` on the ``retention_days``
    capacity axis.

    Retention-axis twin of ``/api/entitlement/has-channel-count-batch``
    and of ``/api/entitlement/has-node-count-batch``. Each token may be
    a finite int (``7`` / ``30`` / ``90``) or the case-insensitive
    string ``"unlimited"`` (routes to
    :func:`has_retention_window(None)`). The unlimited row surfaces
    with ``days=null``, ``unlimited=true`` and ``label="unlimited"``;
    matches the singular ``/has-retention-window?days=unlimited``
    posture. This is the *only* per-axis batch on the retention axis
    that admits the unlimited sentinel -- distinct from
    ``/api/entitlement/has-batch`` where ``retention_days=`` (no value)
    is *unset*.

    ``?days=`` is a comma-separated list. Empty / whitespace tokens are
    dropped, duplicates by normalised key are dropped preserving first-
    seen order, non-int / non-``"unlimited"`` tokens pass through as
    one row with ``unknown=true`` / ``has_retention_window=false``
    (matches :func:`has_retention_window`'s strict callsite-typo
    posture). Missing / blank ``?days=`` -> ``400`` (matches the
    sibling ``/api/entitlement/min-tier-for-retention-window-batch``
    posture).

    Per-row body shape::

        {
          "days":                 <int> | null,
          "days_raw":             "<stripped raw token>",
          "unlimited":            <bool>,               # true iff ?days=unlimited
          "kind":                 "retention_window",
          "label":                "1 day" | "5 days" | "unlimited" | null,
          "has_retention_window": <bool>,
          "allowed":              <bool>,               # mirror of has_retention_window
          "unknown":              <bool>,               # true iff junk input
          "required_tier":        "<tier id>" | null,
          "required_tier_label":  "<label>"   | null,
          "required_tier_rank":   <int>,                # -1 when required_tier null
          "upgrade_required":     <bool>,               # required_tier_rank > current_tier_rank
        }

    Envelope wraps ``rows`` with ``kind`` / ``count`` (row count) plus
    the standard resolver envelope (``current_tier`` /
    ``current_tier_rank`` / ``grace`` / ``enforced``).

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) every KNOWN row -- including the ``"unlimited"``
    row -- reports ``has_retention_window=true``, so wiring this into
    a history-range gate today changes NO current behavior. Post-
    enforcement each row reflects the resolver's live grant; notably
    the ``"unlimited"`` row collapses to Enterprise-only there.

    Cross-consistency: the ``required_tier`` on each row agrees byte-
    for-byte with
    ``/api/entitlement/required-tier?retention_days=<days>`` and with
    the per-row ``required_tier`` on the sibling
    ``/api/entitlement/min-tier-for-retention-window-batch`` -- a UI
    wiring both for the same paywall matrix cannot see inconsistent
    tier state.

    Never 5xx: any resolver blowup collapses to
    :func:`_has_retention_window_batch_fallback`.
    """
    values, err = _shared._parse_capacity_batch_csv("days", unlimited_ok=True)
    if err == "missing":
        return _shared.jsonify({"error": "missing days"}), 400
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        scalar_rows = _ent.has_retention_window_batch(values)
        raw_by_key: dict[str, str] = {}
        for raw in values:
            if isinstance(raw, str) and raw.strip().lower() == "unlimited":
                key = "unlimited"
            else:
                try:
                    key = str(int(raw))
                except (TypeError, ValueError):
                    key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_retention_window_batch_row_to_body(
                r, raw_by_key.get(str(r.get("key")), str(r.get("key"))), cur_rank
            )
            for r in scalar_rows
        ]
        return _shared.jsonify(
            {
                "kind": "retention_window",
                "count": len(rows),
                "rows": rows,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_retention_window_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._has_retention_window_batch_fallback())

@_shared.bp_entitlement.route("/api/entitlement/has-features")
def api_entitlement_has_features():
    """``GET /api/entitlement/has-features?features=a,b,c`` -- plural
    boolean-gate scalar sibling of ``/api/entitlement/has-feature?feature=<id>``.

    Returns ONE boolean (``has_features``) plus the surrounding tier envelope
    (``current_tier``, ``required_tier``, ``upgrade_required``) and a
    known/unknown split of the caller's CSV, so a paywall tile that gates on
    a bundle (``fleet + otel_export + sso -- Available in Enterprise``) can
    bind ``allowed`` directly off this URL without parsing the fuller
    ``/api/entitlement/min-tier-for-features`` body plus a follow-up hit to
    the singular ``/has-feature`` endpoint per item.

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) ``has_features`` reports ``True`` for every fully-known
    bundle, so wiring this into a gate today changes NO current behavior.
    Unknown tokens collapse the bundle to ``has_features=False`` (matches
    the scalar's typo-catches-at-callsite posture -- a UI can still show
    ``unknown`` in a diagnostics tooltip). Missing / blank / all-unknown
    CSV -> 200 with ``has_features=False``, ``features=[]``, ``count=0``
    (never 4xx, matching the singular ``/has-feature`` envelope). Never
    5xx.

    Envelope shape (14 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet", "sso"],   # known ids only, dedup, first-seen order
          "unknown":             ["bogus"],           # tokens not in ALL_FEATURES, echoed raw
          "kind":                "features",
          "count":               2,                   # len(features)
          "has_features":        false,               # scalar over the ORIGINAL CSV (unknowns collapse)
          "allowed":             false,               # alias of has_features
          "required_tier":       "enterprise" | null, # min_tier_for_features(known); null if empty
          "required_tier_label": "Enterprise" | null,
          "required_tier_rank":  <int>,               # -1 when required_tier is null
          "current_tier":        "oss",
          "current_tier_rank":   0,
          "grace":               true,
          "enforced":            false,
          "upgrade_required":    <bool>               # required_rank > current_rank
        }
    """
    try:
        return _shared.jsonify(_shared._has_bundle_body("features"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_features: error: %s", exc)
        return _shared.jsonify(_shared._has_bundle_fallback("features", _shared._parse_csv_arg("features")))

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes")
def api_entitlement_has_runtimes():
    """``GET /api/entitlement/has-runtimes?runtimes=x,y,z`` -- runtime-axis
    twin of ``/api/entitlement/has-features``.

    Same 14-key envelope with ``runtimes`` / ``has_runtimes`` in the
    axis-specific slots. Runtime-alias canonicalisation (``claude-code`` ->
    ``claude_code``) is applied per token before the known/unknown split so
    a caller doesn't need to normalise before hitting the URL. Grace
    pass-through, unknown-collapses-bundle, never-4xx, never-5xx
    guarantees mirror the features sibling exactly.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_runtimes: error: %s", exc)
        return _shared.jsonify(_shared._has_bundle_fallback("runtimes", _shared._parse_csv_arg("runtimes")))

@_shared.bp_entitlement.route("/api/entitlement/has-features-at")
def api_entitlement_has_features_at():
    """``GET /api/entitlement/has-features-at?tier=<perspective>&features=a,b,c``
    -- plural what-if boolean-gate scalar sibling of
    ``/api/entitlement/has-features``.

    Returns ONE boolean (``has_features_at``) plus a what-if envelope that
    tells the caller which perspective they asked about, whether the whole
    bundle is admitted by that perspective, the cheapest tier that would
    unlock it (``required_tier``, byte-parity with the sibling
    ``/api/entitlement/min-tier-for-features`` answer), and the LIVE
    resolver context (``current_tier`` / ``grace`` / ``enforced``) so a
    pricing matrix can render "you are here" alongside "would tier X grant
    this bundle?" off ONE URL per cell.

    Unlike the live ``/has-features`` sibling this endpoint is
    perspective-shaped: even in grace ``has_features_at?tier=oss&features=fleet,sso``
    is ``False`` (because OSS-free does not statically grant ``fleet`` /
    ``sso``), whereas ``/has-features?features=fleet,sso`` in grace returns
    ``True``. That is the whole point of the ``_at`` slot -- render the
    would-be-locked state alongside the live grant.

    Never 4xxs (missing / blank / unknown tier or all-unknown CSV -> 200
    with ``has_features_at=false``, matching the sibling ``/has-features``
    posture). Never 5xxs: any helper blowup collapses to
    :func:`_has_bundle_at_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_body("features"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_features_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_fallback("features", tier, _shared._parse_csv_arg("features"))
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at")
def api_entitlement_has_runtimes_at():
    """``GET /api/entitlement/has-runtimes-at?tier=<perspective>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/has-features-at``.

    Same 15-key envelope with ``runtimes`` / ``has_runtimes_at`` in the
    axis-specific slots. Runtime-alias canonicalisation
    (``claude-code`` -> ``claude_code``) is applied per-token upstream at
    the endpoint layer so ``?runtimes=claude-code,openclaw`` collapses to
    the granted ``claude_code,openclaw`` -- matches the sibling
    ``/has-runtimes`` endpoint's own upstream-canonicalise pattern.
    Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_runtimes_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_fallback("runtimes", tier, _shared._parse_csv_arg("runtimes"))
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features")
def api_entitlement_missing_features():
    """``GET /api/entitlement/missing-features?features=a,b,c`` -- row-detail
    complement of ``/api/entitlement/has-features``.

    Returns the SUBSET of ``features`` NOT granted by the resolved
    entitlement (the exact list of ids blocking the bundle) plus the
    surrounding tier envelope. Where ``/has-features`` folds the bundle to
    ONE boolean ("does the whole set pass?"), this preserves the per-item
    denial so a paywall diagnostics tile ("you're missing fleet, sso") can
    bind the missing list directly off ONE URL instead of walking the
    ``/has-batch`` matrix and filtering ``has=False`` client-side.

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) ``missing=[]`` for every fully-known bundle -- ``True``
    grace answer on ``/has-features`` collapses to an empty complement here
    -- so wiring this into a diagnostics tile today changes NO current
    behavior. Unknown tokens surface INSIDE ``missing`` (canonicalised to
    ``.strip().lower()``), matching the scalar's typo-catches-at-callsite
    posture; the ``unknown`` slot still splits them out for a diagnostics
    tooltip that wants to distinguish "denied by tier" vs "not a real id".
    Missing / blank / all-unknown CSV -> 200 with ``missing=[]``,
    ``features=[]``, ``count=0``, ``any_missing=false`` (never 4xx,
    matching the sibling envelope). Never 5xx.

    Envelope shape (15 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet", "sso"],   # known ids only, dedup, first-seen order
          "unknown":             ["bogus"],           # tokens not in ALL_FEATURES, echoed raw
          "missing":             ["bogus", "sso"],    # subset NOT granted (denials + unknowns)
          "kind":                "features",
          "count":               2,                   # len(features) known
          "missing_count":       2,                   # len(missing)
          "any_missing":         true,                # missing != [] OR unknown != []
          "required_tier":       "enterprise" | null, # min_tier_for_features(known); null if empty
          "required_tier_label": "Enterprise" | null,
          "required_tier_rank":  <int>,               # -1 when required_tier is null
          "current_tier":        "oss",
          "current_tier_rank":   0,
          "grace":               true,
          "enforced":            false,
          "upgrade_required":    <bool>               # required_rank > current_rank
        }
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_body("features"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_features: error: %s", exc)
        return _shared.jsonify(_shared._missing_bundle_fallback("features", _shared._parse_csv_arg("features")))

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes")
def api_entitlement_missing_runtimes():
    """``GET /api/entitlement/missing-runtimes?runtimes=x,y,z`` -- runtime-axis
    twin of ``/api/entitlement/missing-features``.

    Same 15-key envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``) is
    applied per token before the known/unknown split and inside
    :func:`missing_runtimes` so an alias-and-canonical pair
    (``?runtimes=claude-code,claude_code``) collapses to one row in
    ``missing``. Grace pass-through, unknown-surfaces-inside-missing,
    never-4xx, never-5xx guarantees mirror the features sibling exactly.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_runtimes: error: %s", exc)
        return _shared.jsonify(_shared._missing_bundle_fallback("runtimes", _shared._parse_csv_arg("runtimes")))

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at")
def api_entitlement_missing_features_at():
    """``GET /api/entitlement/missing-features-at?tier=<perspective>&features=a,b,c``
    -- perspective-shaped row-detail complement of
    ``/api/entitlement/has-features-at``.

    Returns the SUBSET of ``features`` that ``perspective_tier`` would
    NOT grant (the exact list of ids blocking the bundle at that tier)
    plus the surrounding tier envelope. Where ``/has-features-at`` folds
    the bundle to ONE boolean per (perspective, bundle) cell, this
    preserves the per-item denial so a paywall matrix column ("at
    Starter you'd still be missing fleet, sso -- upgrade to Enterprise
    to unlock") can bind the missing list directly off ONE URL per cell
    instead of walking the ``/has-batch`` matrix and filtering
    ``has=False`` client-side.

    Unlike the live ``/missing-features`` sibling this endpoint is
    perspective-shaped: even in grace
    ``/missing-features-at?tier=oss&features=fleet,sso`` returns
    ``missing=["fleet", "sso"]`` (because OSS-free does not statically
    grant them), whereas ``/missing-features?features=fleet,sso`` in
    grace returns ``missing=[]``. That is the whole point of the ``_at``
    slot -- render the would-be-locked state alongside the live grant.

    Never 4xxs (missing / blank / unknown tier or all-unknown CSV -> 200
    with ``missing=[]``, matching the sibling ``/missing-features``
    posture). Never 5xxs: any helper blowup collapses to
    :func:`_missing_bundle_at_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_body("features"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_features_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_fallback(
                "features", tier, _shared._parse_csv_arg("features")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at")
def api_entitlement_missing_runtimes_at():
    """``GET /api/entitlement/missing-runtimes-at?tier=<perspective>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/missing-features-at``.

    Same 17-key envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict scalar -- matches
    the sibling ``/missing-runtimes`` endpoint's own upstream-
    canonicalise pattern. Alias-and-canonical pair dedups to ONE row in
    both ``runtimes`` and ``missing``. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_runtimes_at: error: %s", exc)
        tier = (_shared.request.args.get("tier") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_fallback(
                "runtimes", tier, _shared._parse_csv_arg("runtimes")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at-batch")
def api_entitlement_missing_features_at_batch():
    """``GET /api/entitlement/missing-features-at-batch?tiers=<a,b,...>&features=<x,y,...>``
    -- batch what-if sibling of ``/api/entitlement/missing-features-at``.

    Fixes ONE feature bundle and sweeps across N perspective tiers,
    returning one row per tier with the per-item denial list plus the
    surrounding tier envelope. Lets a pricing-matrix column ("out of
    {fleet, sso}, which are still locked at OSS vs Cloud Starter vs
    Cloud Pro vs Enterprise?") hydrate the whole column off ONE URL
    instead of N calls to ``/missing-features-at``.

    Envelope shape is fully documented on :func:`_missing_bundle_at_batch_body`.
    Never 4xxs (missing / blank / unknown tiers or all-unknown CSV -> 200
    with ``tiers=[]``, matching the sibling ``/missing-features-at``
    posture -- a paywall matrix binds ``tiers`` directly without a
    pre-validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_missing_bundle_at_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_bundle_at_batch_fallback(
                "features",
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at-batch")
def api_entitlement_missing_runtimes_at_batch():
    """``GET /api/entitlement/missing-runtimes-at-batch?tiers=<a,b,...>&runtimes=<x,y,...>``
    -- runtime-axis twin of ``/api/entitlement/missing-features-at-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot. Runtime-
    alias canonicalisation (``claude-code`` -> ``claude_code``) is
    applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict batch scalar --
    matches the sibling ``/missing-runtimes-at`` endpoint's own
    upstream-canonicalise pattern. Alias-and-canonical pair dedups to
    ONE row in both ``runtimes`` and every per-tier ``missing``. Never
    4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_bundle_at_batch_fallback(
                "runtimes",
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-at-batch")
def api_entitlement_has_features_at_batch():
    """``GET /api/entitlement/has-features-at-batch?tiers=<a,b,...>&features=<x,y,...>``
    -- batch what-if sibling of ``/api/entitlement/has-features-at``.

    Fixes ONE feature bundle and sweeps across N perspective tiers,
    returning one row per tier with the fold boolean plus the surrounding
    tier envelope. Boolean-fold complement of
    ``/api/entitlement/missing-features-at-batch`` (per-item denial list);
    the two paired endpoints share the tier envelope so a UI can render
    "is this granted?" and "which items are still locked?" side by side
    without a second round of tier normalisation.

    Envelope shape is fully documented on :func:`_has_bundle_at_batch_body`.
    Never 4xxs (missing / blank / unknown tiers or all-unknown CSV -> 200
    with ``tiers=[]``, matching the sibling ``/has-features-at`` posture --
    a paywall matrix binds ``tiers`` directly without a pre-validation
    round-trip). Never 5xxs: any helper blowup collapses to
    :func:`_has_bundle_at_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_bundle_at_batch_fallback(
                "features",
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at-batch")
def api_entitlement_has_runtimes_at_batch():
    """``GET /api/entitlement/has-runtimes-at-batch?tiers=<a,b,...>&runtimes=<x,y,...>``
    -- runtime-axis twin of ``/api/entitlement/has-features-at-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot. Runtime-
    alias canonicalisation (``claude-code`` -> ``claude_code``) is
    applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict batch scalar --
    matches the sibling ``/has-runtimes-at`` endpoint's own upstream-
    canonicalise pattern. Alias-and-canonical pair dedups to ONE row in
    both ``runtimes`` and every per-tier fold. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_bundle_at_batch_fallback(
                "runtimes",
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("runtimes"),
            )
        )
