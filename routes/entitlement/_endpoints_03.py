"""routes/entitlement/_endpoints_03.py — endpoint handlers api_entitlement_min_tier .. api_license_is_valid_at.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/min-tier")
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
    feature = (_shared.request.args.get("feature") or "").strip()
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
                    ),
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
                    ),
                }
            ),
            400,
        )
    if channels_present and not channels_ok:
        return (
            _shared.jsonify({"error": "channels= must be an integer"}),
            400,
        )
    if retention_present and not retention_ok:
        return (
            _shared.jsonify({"error": "retention_days= must be an integer"}),
            400,
        )
    if nodes_present and not nodes_ok:
        return (
            _shared.jsonify({"error": "nodes= must be an integer"}),
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
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_min_tier: error: %s", exc)
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
        return _shared.jsonify(
            {
                "key": key,
                "value": value,
                "free": False,
                "min_tier": None,
                "tier_label": None,
                "tier_rank": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-batch")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_min_tier_batch: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/has-batch")
def api_entitlement_has_batch():
    """``GET /api/entitlement/has-batch?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-item plural sibling of
    ``/api/entitlement/has-feature`` / ``/has-runtime`` /
    ``/has-channel-count``.

    Where ``/api/entitlement/has-features`` / ``/has-runtimes`` fold a
    bundle to ONE boolean, this preserves the per-item detail so a
    paywall MATRIX UI ("show every requested feature + runtime + capacity
    row with its individual granted flag AND the cheapest tier that
    would unlock it") renders off ONE round-trip instead of N calls to
    ``/has-feature`` / ``/has-runtime`` / ``/has-channel-count``. Wraps
    :func:`clawmetry.entitlements.has_batch` and appends the same
    ``current_tier`` / ``grace`` / ``enforced`` resolver envelope
    ``/min-tier-batch`` and ``/lock-reasons-batch`` return so a caller
    sees the same resolver context alongside the per-item answers.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty /
    parseable after normalisation). ``features=`` / ``runtimes=`` take
    comma-separated tokens (whitespace and duplicates are normalised
    away; runtime aliases like ``claude-code`` canonicalise to
    ``claude_code``; unknown ids contribute a fail-closed
    ``unknown=True`` / ``has=False`` row -- they do NOT silently render
    as granted the way ``/lock-reasons-batch``'s ``allowed`` slot does).
    The three capacity axes take a single int each; a blank or non-int
    value is treated as "not supplied" (matches the singular endpoint's
    never-crash posture rather than fabricating a row for garbage
    input). Never 5xxs: the fail-closed envelope is returned on any
    resolver failure.

    Response shape (10 keys, byte-stable across every input branch)::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "has_all":            <bool>,   # True iff every emitted row is has=True AND unknown=False
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``has``, ``unknown``,
    ``required_tier``, ``required_tier_label`` and ``required_tier_rank``
    (``-1`` when ``required_tier`` is ``None``). Per-row parity with the
    singular ``/has-feature?feature=`` / ``/has-runtime?runtime=`` /
    ``/has-channel-count?count=`` endpoints is pinned in the test suite
    so the batch cannot silently drift from the scalar.

    ``has_all`` cross-consistency with the sibling
    ``/api/entitlement/has-features`` / ``/has-runtimes`` plural-fold
    endpoints is pinned: for a single-axis batch of features, this
    endpoint's ``has_all`` byte-equals the ``/has-features`` endpoint's
    ``has_features`` for the same bundle; ditto for runtimes.
    """
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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

        batch = _ent.has_batch(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        ent = _ent.get_entitlement()
        batch["has_all"] = _shared._has_batch_rollup(batch)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_batch: error: %s", exc)
        return _shared.jsonify(_shared._has_batch_fallback())

@_shared.bp_entitlement.route("/api/entitlement/has-batch-at")
def api_entitlement_has_batch_at():
    """``GET /api/entitlement/has-batch-at?tier=<perspective>&features=a,b,c
    &runtimes=x,y&channels=N&retention_days=K&nodes=M`` -- hypothetical-
    perspective sibling of ``/api/entitlement/has-batch``.

    Fills the missing ``_at`` slot on the ``has-batch`` mixed-axis batch
    surface alongside ``/api/entitlement/min-tier-batch-at`` (the
    perspective sibling on the reverse-lookup axis) and the singular
    ``/has-feature-at`` / ``/has-runtime-at`` / ``/has-channel-count-at``
    / ``/has-retention-window-at`` / ``/has-node-count-at`` scalars. A
    paywall matrix walkthrough at a hypothetical perspective ("if I
    were on Starter, does this bundle land granted?") renders off ONE
    round-trip instead of N calls to the singular ``_at`` scalars +
    client-side row assembly.

    Wraps :func:`clawmetry.entitlements.has_batch_at` and layers the
    perspective envelope (``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank``) plus the
    standard resolver envelope (``current_tier`` / ``current_tier_rank``
    / ``grace`` / ``enforced``) on top so a walkthrough surface can
    render the "from <perspective>" copy alongside "you are here" off
    one call.

    Perspective-shaped (grace-independent by design): unlike the LIVE
    ``/has-batch`` sibling (which reports ``has=true`` for every known
    row while ``ent.grace`` is ``true``), each row here reflects the
    STATIC per-tier grant for ``perspective_tier``. ``has-batch-at?
    tier=oss&features=fleet`` returns ``has=false`` for the fleet row
    even in grace -- the whole point of the ``_at`` slot (render the
    would-be-locked state alongside the live grant).

    Args mirror ``/has-batch`` byte-for-byte except for the additional
    ``tier=`` perspective arg. Same CSV normalisation, same capacity-
    axis parsing, same ``None`` = "not supplied" sentinel.

    Response shape (13 keys, byte-stable across every input branch)::

        {
          "perspective_tier":       "...",
          "perspective_tier_label": "...",
          "perspective_tier_rank":  <int>,
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
          "has_all":            <bool>,   # True iff every emitted row is has=True AND unknown=False
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``has``, ``unknown``,
    ``required_tier``, ``required_tier_label`` and ``required_tier_rank``
    (``-1`` when ``required_tier`` is ``None``). Per-row ``has_*_at``
    parity with the singular ``/has-feature-at?`` /
    ``/has-runtime-at?`` / ``/has-channel-count-at?`` /
    ``/has-retention-window-at?`` / ``/has-node-count-at?`` endpoints is
    pinned in the test suite so the batch cannot silently drift from
    the singular scalars.

    - **400** when ``tier=`` is missing / blank, OR when no constraint
      axis is supplied.
    - **404** when ``tier`` is unknown. The body carries ``which=tier``.
    - **Never 5xxs**: a resolver failure yields the perspective-carrying
      OSS-free shape (empty per-axis rows, ``has_all=False``) so the
      pricing walkthrough keeps rendering.
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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

        batch = _ent.has_batch_at(
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
        batch["has_all"] = _shared._has_batch_rollup(batch)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_batch_at: error: %s", exc)
        return _shared.jsonify(_shared._has_batch_at_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/min-tier-batch-at")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_min_tier_batch_at: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/min-tier-at")
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

        feature = (_shared.request.args.get("feature") or "").strip()
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
                _shared.jsonify(
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
                _shared.jsonify({"error": "channels= must be an integer"}),
                400,
            )
        if retention_present and not retention_ok:
            return (
                _shared.jsonify({"error": "retention_days= must be an integer"}),
                400,
            )
        if nodes_present and not nodes_ok:
            return (
                _shared.jsonify({"error": "nodes= must be an integer"}),
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
                _shared.jsonify(
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_min_tier_at: error: %s", exc)
        feature = (_shared.request.args.get("feature") or "").strip()
        runtime = (_shared.request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            _channels_ok,
            _channels_n,
            channels_raw,
        ) = _shared._parse_capacity_arg("channels")
        (
            retention_present,
            _retention_ok,
            _retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (
            nodes_present,
            _nodes_ok,
            _nodes_n,
            nodes_raw,
        ) = _shared._parse_capacity_arg("nodes")
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
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers-batch")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_affordable_tiers_batch: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers-at-batch")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_affordable_tiers_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route(
    "/api/entitlement/lock-reasons-batch",
    endpoint="api_entitlement_lock_reasons_batch",
)
@_shared.bp_entitlement.route("/api/entitlement/lock-reason-batch")
def api_entitlement_lock_reason_batch():
    """``GET /api/entitlement/lock-reason-batch?features=a,b,c&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-item plural sibling of
    ``/api/entitlement/lock-reason``.

    Also reachable at ``/api/entitlement/lock-reasons-batch`` (bare plural
    URL). Both URLs dispatch to the SAME view and return byte-identical
    JSON. The alias exists so callers can address this endpoint under the
    plural URL naming already used by its ``_at`` sibling
    ``/api/entitlement/lock-reasons-at-batch`` -- same bare / ``_at``
    symmetry that ``/min-tier-for-features`` <-> ``/min-tier-for-features-at``
    already exposes. Registering the alias with a distinct Flask endpoint
    name (``api_entitlement_lock_reasons_batch``) keeps ``url_for`` reverse
    lookups unambiguous while sharing one implementation. Pinned by parity
    tests in ``tests/test_entitlement_lock_reasons_batch_alias.py``.

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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_lock_reason_batch: error: %s", exc)
        return _shared.jsonify(
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

@_shared.bp_entitlement.route(
    "/api/entitlement/lock-reason-at-batch",
    endpoint="api_entitlement_lock_reason_at_batch",
)
@_shared.bp_entitlement.route("/api/entitlement/lock-reasons-at-batch")
def api_entitlement_lock_reasons_at_batch():
    """``GET /api/entitlement/lock-reasons-at-batch?tier=<perspective>
    &features=a,b,c&runtimes=x,y&channels=N&retention_days=K&nodes=M`` --
    what-if sibling of ``/api/entitlement/lock-reason-batch``.

    Also reachable at ``/api/entitlement/lock-reason-at-batch`` (bare
    singular URL). Both URLs dispatch to the SAME view and return
    byte-identical JSON. The alias exists so the ``_at`` URL naming
    matches the bare / plural pairing already registered on the LIVE
    sibling: ``/lock-reason-batch`` was aliased to
    ``/lock-reasons-batch`` for symmetry with this plural ``_at`` URL;
    this reverse alias completes the 2x2
    ({singular, plural} x {live, _at}) so callers can address either
    what-if or live under either naming convention. Registering the
    alias with a distinct Flask endpoint name
    (``api_entitlement_lock_reason_at_batch``) keeps ``url_for`` reverse
    lookups unambiguous while sharing one implementation. Pinned by
    parity tests in
    ``tests/test_entitlement_lock_reason_at_batch_alias.py``.

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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_lock_reasons_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/diagnostic")
def api_entitlement_diagnostic():
    try:
        from clawmetry import entitlements as _ent

        return _shared.jsonify(_ent.resolution_diagnostic())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_diagnostic: falling back to minimal: %s", exc)
        return _shared.jsonify(
            {
                "license_path": None,
                "license_present": False,
                "cloud_plan_path": None,
                "cloud_plan_present": False,
                "enforce_env": _shared.os.environ.get("CLAWMETRY_ENFORCE"),
                "is_enforced": False,
                "cache_age_seconds": None,
                "cache_ttl_seconds": None,
                "cache_hit_next_call": False,
                "cache_cached_tier": None,
                "error": str(exc),
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tiers-for")
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
    feat = (_shared.request.args.get("feature") or "").strip().lower()
    rt = (_shared.request.args.get("runtime") or "").strip().lower()
    if not feat and not rt:
        return _shared.jsonify({"error": "missing feature or runtime"}), 400
    if feat and rt:
        return _shared.jsonify(
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
            return _shared.jsonify({"error": f"unknown {kind}", kind: item}), 404
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tiers_for: error: %s", exc)
        return _shared.jsonify({"error": "tiers-for failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-batch")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_tiers_for_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "features": [],
                "runtimes": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    feat = (_shared.request.args.get("feature") or "").strip().lower()
    rt = (_shared.request.args.get("runtime") or "").strip().lower()
    if not feat and not rt:
        return _shared.jsonify({"error": "missing feature or runtime"}), 400
    if feat and rt:
        return _shared.jsonify(
            {"error": "pass feature OR runtime, not both"}
        ), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}), 404
        if feat:
            body = _ent.tiers_for_feature_at(p, feat)
            kind = "feature"
            item = feat
        else:
            body = _ent.tiers_for_runtime_at(p, rt)
            kind = "runtime"
            item = rt
        if body is None:
            return _shared.jsonify({"error": f"unknown {kind}", kind: item}), 404
        ent = _ent.get_entitlement()
        envelope = dict(body)
        envelope["perspective_tier"] = p
        envelope["perspective_tier_label"] = _ent.tier_label(p)
        envelope["perspective_tier_rank"] = _ent.tier_rank(p)
        envelope["current_tier"] = ent.tier
        envelope["current_tier_rank"] = _ent.tier_rank(ent.tier)
        envelope["grace"] = bool(ent.grace)
        envelope["enforced"] = _ent.is_enforced()
        return _shared.jsonify(envelope)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tiers_for_at: error: %s", exc)
        return _shared.jsonify({"error": "tiers-for-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-batch-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}), 404
        body = _ent.tiers_for_batch_at(p)
        if body is None:
            body = {"features": [], "runtimes": []}
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_tiers_for_batch_at: error: %s", exc)
        try:
            from clawmetry import entitlements as _ent

            label = _ent.tier_label(p)
            rank = _ent.tier_rank(p)
        except Exception:
            label = p
            rank = 0
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/runtimes")
def api_runtimes():
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        # ``pending`` = a linked account whose plan has not resolved yet (the
        # daemon writes cloud_plan.json a few seconds after boot). The rows
        # below then read entitled=False for every paid runtime, which is
        # "unknown", not "not allowed" — clients must not lock on it. See
        # entitlements.plan_pending().
        return _shared.jsonify(
            {
                "runtimes": _ent.runtime_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
                "pending": _ent.plan_pending(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_runtimes: falling back to OSS-free: %s", exc)
        return _shared.jsonify(
            {
                # Sorted by id, matching runtime_catalog()'s ordering, so the
                # fallback is shape-identical to the happy path. Keep this in
                # lockstep with entitlements.FREE_RUNTIMES — guarded by
                # tests/test_advertised_runtimes_match_catalogue.py.
                "runtimes": [
                    {
                        "id": "goose",
                        "label": "Goose",
                        "free": True,
                        "tier": "free",
                        "allowed": True,
                        "locked": False,
                    },
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
                "pending": True,
            }
        )

@_shared.bp_entitlement.route("/api/tiers")
def api_tiers():
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": _ent.tier_catalog(),
                "current": ent.tier,
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_tiers: falling back to OSS-free: %s", exc)
        return _shared.jsonify(
            {
                "tiers": [],
                "current": "oss",
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec")
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
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_spec(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_spec: error: %s", exc)
        return _shared.jsonify({"error": "tier-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-batch")
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
        tiers = _shared._parse_csv_arg("tiers")
        if not tiers:
            return (
                _shared.jsonify({"error": "supply tiers=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.tier_spec_batch(tiers)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_spec_batch: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/features")
def api_features():
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "features": _ent.feature_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_features: falling back to OSS-free: %s", exc)
        return _shared.jsonify({"features": [], "grace": True, "enforced": False})

@_shared.bp_entitlement.route("/api/license/status")
def api_license_status():
    """``GET /api/license/status`` -- current install's license state.

    Shape parity across all three branches: whether the healthy path
    (:func:`clawmetry.license.current_license_info` returns an active /
    expired / invalid dict), the no-license path, or the introspection-
    failure path, the response carries the SAME field set so a UI can
    render every case through one code path without special-casing which
    keys are present. Two branch-specific keys layer on top:

      * ``plan`` -- ``"oss"`` on the no-license and error branches so a
        legacy consumer that grew up when those branches returned only
        ``{"plan": "oss", ...}`` keeps working.
      * ``error`` -- populated only on the introspection-failure branch;
        carries ``str(exc)`` so an operator triaging a mixed deploy can
        see which import / stat went sideways without tailing daemon logs.

    Never 5xxs. If :func:`clawmetry.license.current_license_info` raises
    (import failure, corrupt install, cryptography-lib mismatch), the
    endpoint degrades to the no-license-shape envelope with
    ``status="unknown"`` at HTTP 200 -- matches the "never crash on bad
    input" posture of :func:`api_entitlement`, :func:`api_features`, and
    :func:`api_license_pubkey`, so a dashboard tile bound to this URL never
    breaks on a partial install.

    Trust anchor: ``pubkey_fingerprint_sha256`` populates on every branch
    where it can be resolved -- including no-license -- so an operator can
    verify the OSS trust anchor is intact BEFORE they install a key.
    """

    def _envelope(status, extras=None):
        pubkey_fp = None
        try:
            from clawmetry import license as _lic

            pubkey_fp = _lic.pubkey_fingerprint()
        except Exception as exc:
            _shared.logger.debug("api_license_status: pubkey fingerprint failed: %s", exc)
        payload = {
            "valid": False,
            "status": status,
            "plan": "oss",
            "tier": None,
            "nodes": None,
            "sub": None,
            "exp": None,
            "days_left": None,
            "pubkey_fingerprint_sha256": pubkey_fp,
            "permissions_safe": True,
            "file_mode": None,
        }
        if extras:
            payload.update(extras)
        return payload

    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        if info is None:
            return _shared.jsonify(_envelope("no_license"))
        return _shared.jsonify(info)
    except Exception as exc:
        _shared.logger.warning("api_license_status: error: %s", exc)
        return _shared.jsonify(_envelope("unknown", {"error": str(exc)}))

@_shared.bp_entitlement.route("/api/license/pubkey")
def api_license_pubkey():
    try:
        from clawmetry import license as _lic

        return _shared.jsonify(_lic.pubkey_info())
    except Exception as exc:
        _shared.logger.warning("api_license_pubkey: error: %s", exc)
        return _shared.jsonify(
            {
                "algorithm": "ed25519",
                "format": "SubjectPublicKeyInfo (DER, SHA-256)",
                "fingerprint_sha256": None,
                "fingerprint_short": None,
                "pem": "",
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/features")
def api_license_features():
    """``GET /api/license/features`` -- scalar accessor for the
    ``features`` claim on the currently-installed license, so an
    operator entitlement-diagnostic tile, a fleet-node column, or a
    "features unlocked by your key" chip row can render off ONE cheap
    endpoint without unpacking the full ``/api/license/status``
    envelope (or re-implementing the "don't trust an unsigned body"
    rule client-side).

    Wraps :func:`clawmetry.license.license_features`.

    Response shape (always HTTP 200)::

        {
          "features":    [<id>, ...] | null,
          "has_license": <bool>,   # a license file is on disk
          "valid":       <bool>    # signature-valid AND not expired NOW
        }

    ``features`` is:

      * ``null``    on OSS-free installs, invalid-signature files, and
                    signed-but-lapsed keys (a gate binding this endpoint
                    cannot silently keep granting features on an expired
                    key)
      * ``[]``      when the license IS valid but its payload carries no
                    explicit ``features`` claim -- distinct from ``null``
                    which means no valid license at all
      * a sorted, deduplicated, normalised (lower/strip) list of feature
        ids on a signature-valid, non-expired license

    ``has_license`` + ``valid`` are layered on top so a UI binding this
    endpoint can distinguish "no key" (``has_license=false``) from
    "valid key without a features list" (``valid=true, features=[]``)
    from "expired key" (``has_license=true, valid=false,
    features=null``) in one round-trip, without a second call to
    ``/api/license/status``.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. For the resolved feature set actually enforced by gates,
    read ``/api/entitlement`` (which layers this claim on top of the
    FREE-tier baseline). This endpoint surfaces the claim exactly as
    written on the token, so operator diagnostics can distinguish
    "feature X unlocked because the key claims it" from "feature X
    unlocked because the tier grants it by default".

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``features=null``, ``has_license=false``,
    ``valid=false``), matching the never-crash posture of the
    surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        feats = _lic.license_features()
        try:
            info = _lic.current_license_info()
        except Exception as exc:
            _shared.logger.debug("api_license_features: info read failed: %s", exc)
            info = None
        has_license = isinstance(info, dict)
        valid = bool(has_license and info.get("valid"))
        return _shared.jsonify(
            {
                "features": feats,
                "has_license": has_license,
                "valid": valid,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_features: error: %s", exc)
        return _shared.jsonify(
            {"features": None, "has_license": False, "valid": False}
        )

@_shared.bp_entitlement.route("/api/license/has-feature")
def api_license_has_feature():
    """``GET /api/license/has-feature?feature=<id>`` -- boolean gate for
    "does the installed key claim feature <X>?" UIs.

    Predicate flavour of :func:`clawmetry.license.license_features` (and
    its ``/api/license/features`` HTTP counterpart) for a paywall banner
    / fleet-node column / operator entitlement-tile that wants a single
    bit rather than the full list. Fills the same seat on the license
    axis the sibling ``/api/license/is-tier`` / ``/api/license/is-subject``
    / ``/api/license/is-state`` boolean endpoints occupy, so a caller can
    hit the predicate without list-membership boilerplate ("fetch the
    features list, normalise my query the same way the accessor
    normalises the token claims, then ``in``-check").

    Query parameters:
      * ``feature`` (str, required) -- the feature id to test against.
        Compared case-insensitively after strip, matching
        :func:`clawmetry.license.has_feature`. Missing / empty input
        degrades to ``has_feature=false`` rather than a 4xx, matching
        the surrounding endpoints' never-5xx / never-4xx posture.

    Response shape (always HTTP 200)::

        {
          "has_feature":      <bool>,
          "feature":          <str>,          # normalised echo of the query
          "requested_feature":<str>,          # alias for the normalised echo
          "features":         [<id>, ...] | null,
          "has_license":      <bool>,         # a license file is on disk
          "valid":            <bool>          # signature-valid AND not expired
        }

    ``has_feature`` is ``True`` iff a license is installed, signature-valid,
    NOT expired, and its normalised ``features`` claim contains the
    normalised ``feature`` query. An expired Pro install returns
    ``has_feature=false`` even for a feature the token itemises on
    purpose -- the caller wants "am I entitled right now" not "was I ever
    entitled", and the ``valid`` field carries the "signed but lapsed"
    signal so a paywall UI can drive both banners off one URL.

    The ``features`` / ``has_license`` / ``valid`` fields are layered on
    top of the bool so a UI binding this endpoint can render "you're on
    <X>" copy alongside the answer without a second call to
    ``/api/license/features`` or ``/api/license/status``.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. This endpoint answers *"does the KEY carry this feature
    id?"*, not *"is this feature enforced right now?"*. For the
    resolved feature set actually enforced by gates, read
    ``/api/entitlement`` (which layers this claim on top of the
    FREE-tier baseline). This endpoint surfaces the claim exactly as
    written on the token so operator diagnostics can distinguish
    "feature X unlocked because the key claims it" from "feature X
    unlocked because the tier grants it by default".

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``has_feature=false``, ``features=null``,
    ``has_license=false``, ``valid=false``), matching the never-crash
    posture of the surrounding license endpoints.
    """
    raw = _shared.request.args.get("feature", "") or ""
    try:
        requested = str(raw).strip().lower()
    except Exception:
        requested = ""
    try:
        from clawmetry import license as _lic

        feats = _lic.license_features()
        try:
            info = _lic.current_license_info()
        except Exception as exc:
            _shared.logger.debug(
                "api_license_has_feature: info read failed: %s", exc
            )
            info = None
        has_license = isinstance(info, dict)
        valid = bool(has_license and info.get("valid"))
        match = bool(
            requested
            and isinstance(feats, list)
            and requested in feats
        )
        return _shared.jsonify(
            {
                "has_feature": match,
                "feature": requested,
                "requested_feature": requested,
                "features": feats,
                "has_license": has_license,
                "valid": valid,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_has_feature: error: %s", exc)
        return _shared.jsonify(
            {
                "has_feature": False,
                "feature": requested,
                "requested_feature": requested,
                "features": None,
                "has_license": False,
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/days-until-expiry")
def api_license_days_until_expiry():
    """``GET /api/license/days-until-expiry`` -- scalar countdown for a
    renewal banner / days-left badge that wants ONE number rather than the
    whole ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "days_left": <int|null>,   # None if no license OR no exp claim
          "has_license": <bool>,     # is a license file installed at all?
          "expired": <bool>          # True iff days_left < 0
        }

    ``days_left`` sign matches :func:`clawmetry.license.days_until_expiry`:
    zero on the day of expiry, negative once expired, ``null`` for no
    license or perpetual (no-exp) key. A dashboard tile can bind directly
    off this URL without parsing the full license envelope; a caller who
    also wants ``tier``/``sub``/``pubkey_fingerprint_sha256`` should keep
    hitting ``/api/license/status``.

    Never 5xxs -- any underlying failure degrades to
    ``{days_left: null, has_license: false, expired: false}`` (the
    OSS-free branch shape), matching the "never crash on bad input"
    posture of the surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_expiry_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_days_until_expiry: error: %s", exc)
        return _shared.jsonify({"days_left": None, "has_license": False, "expired": False})

@_shared.bp_entitlement.route("/api/license/expiring-within")
def api_license_expiring_within():
    """``GET /api/license/expiring-within?days=<N>`` -- boolean gate for
    "should I show a renewal warning right now?" UIs.

    Query parameters:
      * ``days`` (int, required) -- the renewal-window threshold. Negative
        or non-numeric input degrades to ``expiring_within=false`` (nothing
        expires within -5 days) rather than a 4xx, matching the surrounding
        endpoints' never-5xx / never-4xx posture. Defaults to ``30`` when
        omitted so a bare hit still returns a sensible answer.

    Response shape (always HTTP 200)::

        {
          "expiring_within": <bool>,
          "days_left": <int|null>,
          "threshold_days": <int>,
          "has_license": <bool>,
          "expired": <bool>
        }

    ``expiring_within`` is ``True`` iff a license is installed AND its
    ``exp`` claim is between 0 and ``threshold_days`` inclusive. An
    already-expired license returns ``expiring_within=false`` on purpose
    -- the caller wants "warn about upcoming renewal" separate from "loud
    banner about an expired install", and the ``expired`` field carries
    the latter signal so both banners can drive off one URL.

    Mirrors :func:`clawmetry.license.is_expiring_within` -- the HTTP shape
    layers ``days_left`` / ``threshold_days`` / ``has_license`` /
    ``expired`` on top of that bool so a paywall widget never needs a
    second call to ``/api/license/status`` to render the accompanying
    "expires in N days" copy.
    """
    raw = _shared.request.args.get("days", "30")
    try:
        threshold = int(raw)
    except (TypeError, ValueError):
        # Bad input degrades to false -- nothing "expires within garbage".
        snap = _shared._license_expiry_snapshot()
        return _shared.jsonify(
            {
                "expiring_within": False,
                "days_left": snap["days_left"],
                "threshold_days": 0,
                "has_license": snap["has_license"],
                "expired": snap["expired"],
            }
        )
    if threshold < 0:
        threshold = 0
    try:
        snap = _shared._license_expiry_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_expiring_within: error: %s", exc)
        snap = {"days_left": None, "has_license": False, "expired": False}
    days_left = snap["days_left"]
    within = (
        snap["has_license"]
        and isinstance(days_left, int)
        and 0 <= days_left <= threshold
    )
    return _shared.jsonify(
        {
            "expiring_within": bool(within),
            "days_left": days_left,
            "threshold_days": threshold,
            "has_license": snap["has_license"],
            "expired": snap["expired"],
        }
    )

@_shared.bp_entitlement.route("/api/license/tier")
def api_license_tier():
    """``GET /api/license/tier`` -- scalar view of the installed license's
    tier claim, for a paywall tile / tier badge that wants ONE string
    rather than the whole ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "tier": <str|null>,        # normalised (lowercased, stripped) tier
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``tier`` mirrors :func:`clawmetry.license.license_tier`: ``None`` for
    no license, invalid signature, or expired install -- an expired Pro
    key deliberately collapses to ``null`` so a paywall tile that keys
    off this field cannot keep rendering "Pro" for a lapsed customer.
    A caller who wants ``sub`` / ``nodes`` / ``exp`` alongside should
    keep hitting ``/api/license/status``.

    Never 5xxs -- any underlying failure degrades to
    ``{tier: null, has_license: false, valid: false}`` (the OSS-free
    branch shape), matching the "never crash on bad input" posture of
    the surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_tier_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_tier: error: %s", exc)
        return _shared.jsonify({"tier": None, "has_license": False, "valid": False})

@_shared.bp_entitlement.route("/api/license/is-tier")
def api_license_is_tier():
    """``GET /api/license/is-tier?tier=<name>`` -- boolean gate for
    "am I on tier <X> right now?" UIs.

    Query parameters:
      * ``tier`` (str, required) -- the tier to test against. Compared
        case-insensitively after strip, matching
        :func:`clawmetry.license.is_tier`. Missing / empty input degrades
        to ``is_tier=false`` rather than a 4xx, matching the surrounding
        endpoints' never-5xx / never-4xx posture.

    Response shape (always HTTP 200)::

        {
          "is_tier": <bool>,
          "tier": <str|null>,          # currently-installed tier
          "requested_tier": <str>,     # normalised echo of the query
          "has_license": <bool>,
          "valid": <bool>              # signature-valid AND not expired
        }

    ``is_tier`` is ``True`` iff a license is installed, signature-valid,
    NOT expired, and its normalised tier byte-equals ``requested_tier``.
    An expired Pro install returns ``is_tier=false`` even for
    ``?tier=pro`` on purpose -- the caller wants "am I entitled right
    now" not "was I ever entitled", and the ``valid`` field carries the
    "signed but lapsed" signal so a paywall UI can drive both banners
    off one URL.

    Mirrors :func:`clawmetry.license.is_tier` -- the HTTP shape layers
    ``tier`` / ``requested_tier`` / ``has_license`` / ``valid`` on top
    of that bool so a widget never needs a second call to
    ``/api/license/status`` to render the accompanying "you're on X"
    copy.
    """
    raw = _shared.request.args.get("tier", "") or ""
    try:
        requested = str(raw).strip().lower()
    except Exception:
        requested = ""
    try:
        snap = _shared._license_tier_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_tier: error: %s", exc)
        snap = {"tier": None, "has_license": False, "valid": False}
    match = bool(
        requested
        and snap["valid"]
        and isinstance(snap["tier"], str)
        and snap["tier"] == requested
    )
    return _shared.jsonify(
        {
            "is_tier": match,
            "tier": snap["tier"],
            "requested_tier": requested,
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-expired")
def api_license_is_expired():
    """``GET /api/license/is-expired`` -- boolean gate for "already past the
    ``exp`` claim".

    Payload:

      * ``expired`` -- ``True`` iff an installed, signature-valid license
        carries an ``exp`` claim in the past. ``False`` for every other state
        (no license, invalid signature, perpetual key, active / future ``exp``)
        so a paywall tile can bind directly to this scalar without threading
        the full ``/api/license/status`` envelope through.
      * ``has_license`` -- ``True`` iff a license file is on disk and
        introspection succeeded, mirroring the ``/api/license/status`` "does a
        file exist" branch so a UI can distinguish "expired" from "never had
        one" without a second request.
      * ``status`` -- passes through ``current_license_info().status``
        (``"active"`` / ``"expired"`` / ``"invalid"`` / ``None``) so a shared
        renderer can decide whether to show the loud "expired" banner (from
        the boolean gate) or the quieter "invalid signature" warning
        (``status == "invalid"``) alongside it.

    Never 5xxs. Underlying introspection failure degrades to
    ``{"expired": False, "has_license": False, "status": null}`` at HTTP 200,
    matching the never-crash posture of ``/api/license/status`` and the
    surrounding entitlement gate endpoints.
    """
    try:
        snap = _shared._license_gate_snapshot()
        return _shared.jsonify(
            {
                "expired": snap["expired"],
                "has_license": snap["has_license"],
                "status": snap["status"],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_is_expired: error: %s", exc)
        return _shared.jsonify({"expired": False, "has_license": False, "status": None})

@_shared.bp_entitlement.route("/api/license/is-perpetual")
def api_license_is_perpetual():
    """``GET /api/license/is-perpetual`` -- boolean gate for "lifetime key,
    no renewal needed".

    Payload:

      * ``perpetual`` -- ``True`` iff an installed, signature-valid license
        carries NO ``exp`` claim. A UI reading this can hide the renewal
        counter and render a "Lifetime" badge instead of "Expires in
        N days". ``False`` for every other state -- no license, invalid
        signature (we refuse to infer "perpetual" from an untrusted body),
        and any signed key with an ``exp`` claim.
      * ``has_license`` -- ``True`` iff a license file is on disk and
        introspection succeeded, mirroring ``/api/license/is-expired`` so the
        paired endpoints agree on this key.
      * ``has_exp`` -- ``True`` iff the installed license carries an ``exp``
        claim (regardless of active-vs-expired). The complement of
        ``perpetual`` on the "signature-valid, on-disk" subset -- a UI
        showing an expiry-date tile can hide it when ``has_exp == False``.

    Never 5xxs. Underlying introspection failure degrades to
    ``{"perpetual": False, "has_license": False, "has_exp": False}`` at HTTP
    200.
    """
    try:
        snap = _shared._license_gate_snapshot()
        return _shared.jsonify(
            {
                "perpetual": snap["perpetual"],
                "has_license": snap["has_license"],
                "has_exp": snap["has_exp"],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_is_perpetual: error: %s", exc)
        return _shared.jsonify({"perpetual": False, "has_license": False, "has_exp": False})

@_shared.bp_entitlement.route("/api/license/pro-installed")
def api_license_pro_installed():
    """``GET /api/license/pro-installed`` -- scalar gate for "is the paid
    wheel actually importable right now?".

    Payload:

      * ``installed`` -- ``True`` iff Python can currently import
        ``clawmetry-pro``. Complements ``/api/license/tier`` (which reads
        the license *claim*): a healthy Pro node needs both a signed
        Pro-tier license AND the wheel on-disk, and splitting them lets
        an operator diagnose "activated but wheel missing"
        (``CLAWMETRY_OFFLINE=1`` install, air-gapped node, failed
        download) apart from "wheel installed but licence expired"
        (paid feature stops unlocking on renewal lapse).
      * ``version`` -- the ``importlib.metadata`` version string when
        installed, else ``None``. A UI can render ``vX.Y.Z`` next to a
        green "Pro installed" badge without a second call.

    Wrapper around :func:`clawmetry.license.pro_installed` /
    :func:`clawmetry.license.pro_installed_version`.

    Never 5xxs. Any underlying introspection failure degrades to
    ``{"installed": False, "version": None}`` at HTTP 200, matching the
    never-crash posture of the paired scalar license endpoints.
    """
    try:
        from clawmetry import license as _lic

        version = _lic.pro_installed_version()
        return _shared.jsonify(
            {
                "installed": bool(version),
                "version": version,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_pro_installed: error: %s", exc)
        return _shared.jsonify({"installed": False, "version": None})

@_shared.bp_entitlement.route("/api/license/pro-installation")
def api_license_pro_installation():
    """``GET /api/license/pro-installation`` -- combined install-state view
    for the ``clawmetry-pro`` wheel.

    Payload -- the same envelope
    :func:`clawmetry.license.pro_installation_info` returns:

      * ``installed`` -- ``True`` iff ``clawmetry-pro`` is currently
        importable.
      * ``version`` -- live ``importlib.metadata`` version string when
        installed, else ``None``.
      * ``marker`` -- ``~/.clawmetry/pro_installed.json`` sidecar written
        at provision time (``installed_at`` unix seconds, ``source``,
        ``node_id``, and the ``version`` recorded at write time). ``{}``
        when the marker file is missing / unreadable.

    Live version and marker can disagree in normal operation (marker
    present but wheel was pip-uninstalled; wheel present but marker
    never written on a pre-marker install), and that disagreement is
    exactly what an operator debugging a paywall glitch needs to see, so
    both are surfaced side-by-side rather than collapsed into a single
    boolean.

    Never 5xxs. Any underlying introspection failure degrades to
    ``{"installed": False, "version": None, "marker": {}}`` at HTTP 200.
    """
    try:
        from clawmetry import license as _lic

        return _shared.jsonify(_lic.pro_installation_info())
    except Exception as exc:
        _shared.logger.warning("api_license_pro_installation: error: %s", exc)
        return _shared.jsonify({"installed": False, "version": None, "marker": {}})

@_shared.bp_entitlement.route("/api/license/pro-installed-at")
def api_license_pro_installed_at():
    """``GET /api/license/pro-installed-at`` -- scalar view of the
    ``installed_at`` field of the ``clawmetry-pro`` provisioning marker
    (``~/.clawmetry/pro_installed.json``), for a "pro installed:
    <date>" row that wants ONE integer rather than the whole
    ``/api/license/pro-installation`` envelope.

    Response shape (always HTTP 200)::

        {
          "installed_at": <int|null>,    # epoch seconds; None if no marker
          "age_days": <int|null>,        # days since provisioning
          "marker_present": <bool>,      # is the marker file readable?
          "installed": <bool>            # can Python import clawmetry-pro right now?
        }

    ``installed_at`` mirrors :func:`clawmetry.license.pro_installed_at`:

      * ``null`` when the marker is missing (wheel was never provisioned
        OR was provisioned by a pre-marker version of ClawMetry), when
        the marker exists but has no ``installed_at`` key, or when the
        value carried by the marker is non-numeric / non-positive.
      * A positive epoch integer otherwise, unmodified from what
        :func:`clawmetry.license._write_pro_marker` wrote at provision
        time.

    Deliberately independent of ``installed``: an operator can have the
    marker on disk yet Python cannot currently import ``clawmetry-pro``
    (wheel was pip-uninstalled since), and that disagreement is exactly
    what a paywall-debugging tile needs to see rather than collapsing
    both facts into one boolean. The ``installed`` field on this
    envelope surfaces the live ``importlib.metadata`` probe so a caller
    binding a single endpoint gets both facts side-by-side.

    Pairs with ``/api/license/pro-install-age-days`` -- this endpoint
    surfaces the raw epoch for a debug row, that endpoint answers the
    "how old" gate without the caller having to do the arithmetic. The
    two endpoints share :func:`_pro_install_snapshot` so a UI binding
    both sees a consistent snapshot.

    Never 5xxs -- any underlying failure degrades to
    ``{installed_at: null, age_days: null, marker_present: false,
    installed: false}`` (the "no marker" branch shape), matching the
    never-crash posture of the surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._pro_install_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_pro_installed_at: error: %s", exc)
        return _shared.jsonify(
            {
                "installed_at": None,
                "age_days": None,
                "marker_present": False,
                "installed": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/pro-install-age-days")
def api_license_pro_install_age_days():
    """``GET /api/license/pro-install-age-days`` -- scalar view of how
    long ago the ``clawmetry-pro`` wheel was provisioned (days since the
    marker's ``installed_at``), for a support/audit tile that wants ONE
    integer rather than computing ``(now - installed_at) // 86400`` at
    the call site.

    Response shape (always HTTP 200)::

        {
          "age_days": <int|null>,        # days since provisioning
          "installed_at": <int|null>,    # epoch seconds
          "marker_present": <bool>,      # is the marker file readable?
          "installed": <bool>            # can Python import clawmetry-pro right now?
        }

    ``age_days`` mirrors :func:`clawmetry.license.pro_install_age_days`:

      * ``null`` when the marker is missing, has no ``installed_at``
        key, or carries a non-numeric / non-positive value.
      * A non-negative integer otherwise -- zero on the day of
        provisioning, growing monotonically thereafter. Clamped to
        ``max(0, ...)`` so a clock-skewed ``installed_at`` in the future
        never renders as a negative age.

    Days are floor-divided from seconds ``(now - installed_at) // 86400``,
    matching how ``/api/license/age-days`` derives its counterpart from
    the signed ``iat`` claim so the two scalars never disagree at the
    day boundary.

    Deliberately independent of ``installed`` (see
    ``/api/license/pro-installed-at``): a marker on disk with the wheel
    since uninstalled still surfaces its real ``age_days``. The
    ``installed`` field independently carries the live-importability
    signal for callers that DO want to hide the row on a broken
    install.

    Never 5xxs -- any underlying failure degrades to
    ``{age_days: null, installed_at: null, marker_present: false,
    installed: false}``.
    """
    try:
        snap = _shared._pro_install_snapshot()
        return _shared.jsonify(
            {
                "age_days": snap["age_days"],
                "installed_at": snap["installed_at"],
                "marker_present": snap["marker_present"],
                "installed": snap["installed"],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_pro_install_age_days: error: %s", exc)
        return _shared.jsonify(
            {
                "age_days": None,
                "installed_at": None,
                "marker_present": False,
                "installed": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/pro-install-age-days-at")
def api_license_pro_install_age_days_at():
    """``GET /api/license/pro-install-age-days-at?epoch=<int>`` -- scalar
    view of how old the ``clawmetry-pro`` install was at an operator-
    supplied perspective epoch, for a scheduled-audit / retrospective
    tile that wants to answer "how old was the pro wheel as of <date>?"
    without the caller having to snapshot the marker state at that
    time or compute ``(epoch - installed_at) // 86400`` at the call
    site.

    Response shape (always HTTP 200)::

        {
          "age_days": <int|null>,        # signed days from installed_at to epoch
          "requested_epoch": <int|null>, # int-coerced input, or null on typo
          "installed_at": <int|null>,    # current on-disk marker installed_at
          "marker_present": <bool>,      # is the marker file readable?
          "installed": <bool>            # can Python import clawmetry-pro right now?
        }

    ``age_days`` mirrors :func:`clawmetry.license.pro_install_age_days_at`:

      * ``null`` when there is no marker file, when the marker has no
        ``installed_at`` key, when ``installed_at`` is non-numeric /
        non-positive, OR when ``epoch`` doesn't parse as an integer.
      * A signed integer number of days otherwise. Zero when ``epoch``
        equals the ``installed_at`` second; positive when ``epoch`` is
        after ``installed_at`` (the normal case -- "N days old as of
        <date>"); negative when ``epoch`` is BEFORE ``installed_at``
        (support scenario: "the operator rolled a machine back to a
        pre-provisioning timestamp -- how far before install were
        we?").

    Deliberately NOT clamped to ``max(0, ...)`` -- unlike the "now"
    endpoint ``/api/license/pro-install-age-days``, which clamps
    because clock-skew is the only way ``installed_at`` can be in the
    future when reading against ``time.time()``. Here the caller
    EXPLICITLY passes a perspective epoch, so a negative result is a
    real, actionable signal (they asked a question that only makes
    sense pre-install), not clock skew to be hidden. Mirrors the
    signed-integer posture of ``/api/license/age-days-at``.

    Deliberately independent of ``installed``: an operator can have
    the marker on disk yet Python cannot currently import
    ``clawmetry-pro`` (wheel was pip-uninstalled since), and that
    disagreement is exactly what a paywall-debug / audit tile needs
    to see rather than collapsing both facts into one boolean. The
    ``installed`` field independently carries the live-importability
    signal for callers that DO want to hide the row on a broken
    install.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to ``age_days=null`` with
        ``requested_epoch=null`` so a caller cannot silently miscount on
        a typo. HTTP status is 200 either way -- the "bad input" signal
        is the ``null`` result, not a 4xx, matching the never-crash
        posture of the surrounding license endpoints.

    Pairs with ``/api/license/pro-installed-at`` and
    ``/api/license/pro-install-age-days`` -- all three share
    :func:`_pro_install_snapshot`, so a UI binding any pair of them for
    the same install cannot catch them disagreeing on ``installed_at``
    / ``marker_present`` / ``installed``. Together they let a
    dashboard render "on <date>, the pro install was N days old,
    provisioned at epoch E" from two orthogonal one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{age_days: null, requested_epoch: <echoed|null>, installed_at: null,
    marker_present: false, installed: false}`` (the "no marker" branch
    shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._pro_install_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_pro_install_age_days_at: snapshot error: %s", exc)
        snap = {
            "installed_at": None,
            "age_days": None,
            "marker_present": False,
            "installed": False,
        }
    age_days: int | None
    if requested is None:
        age_days = None
    else:
        try:
            from clawmetry import license as _lic

            age_days = _lic.pro_install_age_days_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_pro_install_age_days_at: derive error: %s", exc)
            age_days = None
    return _shared.jsonify(
        {
            "age_days": age_days,
            "requested_epoch": requested,
            "installed_at": snap["installed_at"],
            "marker_present": snap["marker_present"],
            "installed": snap["installed"],
        }
    )

@_shared.bp_entitlement.route("/api/license/pro-install-age-days-at-batch")
def api_license_pro_install_age_days_at_batch():
    """``GET /api/license/pro-install-age-days-at-batch?epochs=<int>,<int>,...``
    -- per-value batch sibling of ``/api/license/pro-install-age-days-at``.

    Pro-install-age axis batch companion to
    ``/api/license/pro-install-age-days`` (NOW) and
    ``/api/license/pro-install-age-days-at`` (singular perspective epoch).
    Where the singular endpoint folds ONE perspective epoch to ONE signed
    day-count, this preserves per-value rows so a scheduled audit tile
    that wants to plot install-age across a sequence of perspective dates
    (build timestamps, release timestamps, "was the wheel present when we
    shipped that?") hydrates the full column in one call. Wraps
    :func:`clawmetry.license.pro_install_age_days_at_batch`.

    Twin of ``/api/license/age-days-at-batch`` for the ``installed_at``
    axis -- one derives from the signed ``iat`` claim, this one from the
    on-disk provisioning marker -- so a caller assembling an install +
    entitlement timeline can zip the two batch responses index-for-index.

    Row shape::

        {
          "epoch":    <int|"<raw>">,
          "age_days": <int|null>,
        }

    Query-string posture mirrors the other ``/api/license/*-at-batch``
    endpoints: ``epochs=`` required (missing / blank / only-commas ->
    ``400``), comma-separated tokens deduped by parsed int key preserving
    first-seen order, non-int / ``bool`` / ``None`` tokens collapse to
    ``age_days=null`` (rather than a 4xx hiding the whole batch on a
    single typo -- callers can identify the offending entry in the
    response). Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":            "pro_install_age_days_at",
          "count":           <int>,
          "rows":            [
            {"epoch": <int|"<raw>">, "age_days": <int|null>},
            ...
          ],
          "installed_at":    <int|null>,   # current on-disk marker installed_at
          "marker_present":  <bool>,       # is the marker file readable?
          "installed":       <bool>        # can Python import clawmetry-pro right now?
        }

    Shares :func:`_pro_install_snapshot` with
    ``/api/license/pro-install-age-days`` /
    ``/api/license/pro-install-age-days-at`` /
    ``/api/license/pro-installed-at`` so a UI binding any pair of them for
    the same install cannot catch them disagreeing on ``installed_at`` /
    ``marker_present`` / ``installed``.

    Per-row parity with ``/api/license/pro-install-age-days-at?epoch=<n>``
    is pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._pro_install_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_pro_install_age_days_at_batch: snapshot error: %s", exc
        )
        snap = {
            "installed_at": None,
            "age_days": None,
            "marker_present": False,
            "installed": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.pro_install_age_days_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_pro_install_age_days_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "pro_install_age_days_at",
            "count": len(rows),
            "rows": rows,
            "installed_at": snap["installed_at"],
            "marker_present": snap["marker_present"],
            "installed": snap["installed"],
        }
    )

@_shared.bp_entitlement.route("/api/license/nodes")
def api_license_nodes():
    """``GET /api/license/nodes`` -- scalar view of the installed license's
    node-coverage count, for a fleet-capacity tile that wants ONE integer
    rather than the whole ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "nodes": <int|null>,       # covered node count (None if untrusted)
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``nodes`` mirrors :func:`clawmetry.license.license_nodes`: ``None`` for
    no license, invalid signature, or expired install -- an expired Pro key
    deliberately collapses to ``null`` so a fleet-capacity tile that keys
    off this field cannot keep rendering the paid coverage on a lapsed
    customer. A caller who wants the raw ``nodes`` claim even on an expired
    key (support: "how many nodes was this SUPPOSED to cover?") should keep
    hitting ``/api/license/status``.

    Never 5xxs -- any underlying failure degrades to
    ``{nodes: null, has_license: false, valid: false}`` (the OSS-free
    branch shape), matching the "never crash on bad input" posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_nodes_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_nodes: error: %s", exc)
        return _shared.jsonify({"nodes": None, "has_license": False, "valid": False})

@_shared.bp_entitlement.route("/api/license/within-node-limit")
def api_license_within_node_limit():
    """``GET /api/license/within-node-limit?nodes=<N>`` -- boolean gate for
    "does a fleet of N nodes fit under the installed license?" UIs.

    Query parameters:
      * ``nodes`` (int, required) -- the fleet size to test against.
        Non-numeric or missing input degrades to ``within_limit=false``
        rather than a 4xx, matching the surrounding endpoints' never-5xx /
        never-4xx posture. Values below 1 also collapse to ``false`` (a
        fleet of "connect zero nodes" is meaningless).

    Response shape (always HTTP 200)::

        {
          "within_limit": <bool>,
          "nodes": <int|null>,           # currently-covered node count
          "requested_nodes": <int>,      # normalised echo of the query
          "has_license": <bool>,
          "valid": <bool>                # signature-valid AND not expired
        }

    ``within_limit`` is ``True`` iff a license is installed, signature-
    valid, NOT expired, its ``nodes`` claim resolves to a positive
    integer, AND ``requested_nodes`` is between 1 and that limit
    inclusive. An expired Pro install returns ``within_limit=false`` on
    purpose -- the caller wants "am I entitled right now" not "was I ever
    entitled", and the ``valid`` field carries the "signed but lapsed"
    signal so a paywall UI can drive both banners off one URL.

    Mirrors :func:`clawmetry.license.is_within_node_limit` -- the HTTP
    shape layers ``nodes`` / ``requested_nodes`` / ``has_license`` /
    ``valid`` on top of that bool so a fleet widget never needs a second
    call to ``/api/license/status`` to render the accompanying "N of M
    nodes covered" copy.
    """
    raw = _shared.request.args.get("nodes", "")
    try:
        requested = int(raw)
    except (TypeError, ValueError):
        snap = _shared._license_nodes_snapshot()
        return _shared.jsonify(
            {
                "within_limit": False,
                "nodes": snap["nodes"],
                "requested_nodes": 0,
                "has_license": snap["has_license"],
                "valid": snap["valid"],
            }
        )
    if requested < 1:
        snap = _shared._license_nodes_snapshot()
        return _shared.jsonify(
            {
                "within_limit": False,
                "nodes": snap["nodes"],
                "requested_nodes": max(requested, 0),
                "has_license": snap["has_license"],
                "valid": snap["valid"],
            }
        )
    try:
        snap = _shared._license_nodes_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_within_node_limit: error: %s", exc)
        snap = {"nodes": None, "has_license": False, "valid": False}
    limit = snap["nodes"]
    within = (
        snap["has_license"]
        and snap["valid"]
        and isinstance(limit, int)
        and 1 <= requested <= limit
    )
    return _shared.jsonify(
        {
            "within_limit": bool(within),
            "nodes": limit,
            "requested_nodes": requested,
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/present")
def api_license_present():
    """``GET /api/license/present`` -- bare install-state gate for
    "does this operator have ANY license file at all?".

    Response shape (always HTTP 200)::

        {
          "present": <bool>,       # is a license file on disk at LICENSE_PATH?
          "valid": <bool>,          # signature-valid AND not expired
          "status": <str|null>     # "active"/"expired"/"invalid"/None
        }

    ``present`` mirrors :func:`clawmetry.license.has_license`: ``True`` iff
    a file exists at :data:`~clawmetry.license.LICENSE_PATH`, regardless of
    whether it verifies or whether ``exp`` is in the past. That's the
    signal a dashboard uses to render a subtly-different empty state for
    "Free (never activated)" vs "Free (license expired / broken)" -- an
    entitlement gate wanting "is this node currently entitled?" should
    bind ``/api/license/valid`` instead.

    ``valid`` / ``status`` are surfaced alongside so a UI can drive the
    "you have a file but it's not trustworthy" banner off the same
    request without a second call to ``/api/license/status``.

    Never 5xxs -- any underlying failure degrades to
    ``{present: false, valid: false, status: null}`` (the OSS-free branch
    shape), matching the "never crash on bad input" posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_presence_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_present: error: %s", exc)
        return _shared.jsonify({"present": False, "valid": False, "status": None})

@_shared.bp_entitlement.route("/api/license/valid")
def api_license_valid():
    """``GET /api/license/valid`` -- top-level entitlement gate for
    "is this node currently entitled?".

    Response shape (always HTTP 200)::

        {
          "valid": <bool>,          # signature-valid AND not expired
          "present": <bool>,       # is a license file on disk at all?
          "status": <str|null>     # "active"/"expired"/"invalid"/None
        }

    ``valid`` mirrors :func:`clawmetry.license.is_license_valid`: ``True``
    iff a license is installed, its signature verifies, and its ``exp``
    claim is not in the past. Every "not entitled" reason -- no file,
    forged signature, lapsed key -- collapses to ``valid=False`` so a
    paywall tile can bind directly to this scalar without threading the
    full ``/api/license/status`` envelope through.

    ``present`` and ``status`` are surfaced alongside so a UI can render
    the accompanying "you have a broken file" or "your key expired" copy
    from the same request. An expired install returns
    ``{valid: false, present: true, status: "expired"}``; an invalid
    signature returns ``{valid: false, present: true, status: "invalid"}``;
    an OSS-free node returns ``{valid: false, present: false, status: null}``.

    Never 5xxs -- any underlying failure degrades to
    ``{valid: false, present: false, status: null}`` (the OSS-free branch
    shape), matching the "never crash on bad input" posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_presence_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_valid: error: %s", exc)
        return _shared.jsonify({"valid": False, "present": False, "status": None})

@_shared.bp_entitlement.route("/api/license/subject")
def api_license_subject():
    """``GET /api/license/subject`` -- scalar view of the installed license's
    ``sub`` claim (the customer identifier -- typically an account id or a
    contact email), for a "Licensed to <X>" badge / support-context tile
    that wants ONE string rather than the whole ``/api/license/status``
    envelope.

    Response shape (always HTTP 200)::

        {
          "subject": <str|null>,     # customer identifier (None if untrusted)
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``subject`` mirrors :func:`clawmetry.license.license_subject`: ``None``
    for no license, invalid signature, or expired install -- an expired
    Pro key deliberately collapses to ``null`` so a support tile that keys
    off this field cannot keep rendering the paid customer on a lapsed
    install. A caller who wants the raw ``sub`` claim even on an expired
    key (support: "who was this key issued to?") should keep hitting
    ``/api/license/status``.

    Never 5xxs -- any underlying failure degrades to
    ``{subject: null, has_license: false, valid: false}`` (the OSS-free
    branch shape), matching the "never crash on bad input" posture of
    the surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_subject_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_subject: error: %s", exc)
        return _shared.jsonify({"subject": None, "has_license": False, "valid": False})

@_shared.bp_entitlement.route("/api/license/is-subject")
def api_license_is_subject():
    """``GET /api/license/is-subject?subject=<value>`` -- boolean gate for
    "is this license issued to subject <X> right now?" UIs.

    Query parameters:
      * ``subject`` (str, required) -- the subject to test against.
        Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_subject`. Missing / empty input
        degrades to ``is_subject=false`` rather than a 4xx, matching the
        surrounding endpoints' never-5xx / never-4xx posture.

    Response shape (always HTTP 200)::

        {
          "is_subject": <bool>,
          "subject": <str|null>,          # currently-active subject claim
          "requested_subject": <str>,     # normalised echo of the query
          "has_license": <bool>,
          "valid": <bool>                 # signature-valid AND not expired
        }

    ``is_subject`` is ``True`` iff a license is installed, signature-
    valid, NOT expired, its ``sub`` claim resolves to a non-empty string,
    AND ``requested_subject`` matches that string case-insensitively. An
    expired Pro install returns ``is_subject=false`` on purpose -- the
    caller wants "is this key still bound to <X>?" not "was it ever", and
    the ``valid`` field carries the "signed but lapsed" signal so a
    multi-tenant dispatcher can drive both branches off one URL.

    Mirrors :func:`clawmetry.license.is_subject` -- the HTTP shape layers
    ``subject`` / ``requested_subject`` / ``has_license`` / ``valid`` on
    top of that bool so an audit widget never needs a second call to
    ``/api/license/status`` to render the accompanying "Licensed to X"
    copy.
    """
    raw = _shared.request.args.get("subject", "") or ""
    requested = raw.strip()
    if not requested:
        snap = _shared._license_subject_snapshot()
        return _shared.jsonify(
            {
                "is_subject": False,
                "subject": snap["subject"],
                "requested_subject": "",
                "has_license": snap["has_license"],
                "valid": snap["valid"],
            }
        )
    try:
        snap = _shared._license_subject_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_subject: error: %s", exc)
        snap = {"subject": None, "has_license": False, "valid": False}
    actual = snap["subject"]
    matches = (
        snap["has_license"]
        and snap["valid"]
        and isinstance(actual, str)
        and actual.lower() == requested.lower()
    )
    return _shared.jsonify(
        {
            "is_subject": bool(matches),
            "subject": actual,
            "requested_subject": requested,
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/subject-at")
def api_license_subject_at():
    """``GET /api/license/subject-at?epoch=<int>`` -- scalar view of the
    installed license's ``sub`` claim evaluated as of ``epoch`` -- the
    perspective-epoch flavour of ``/api/license/subject``, for a
    scheduled-audit / retrospective badge that wants to answer "who was
    this node licensed to on <date>?" without the caller having to
    snapshot the license state at that time or compare ``exp`` to a
    caller-supplied epoch themselves.

    Response shape (always HTTP 200)::

        {
          "subject_at": <str|null>,       # subject as of epoch
          "requested_epoch": <int|null>,  # int-coerced input, or null on typo
          "subject": <str|null>,          # current-time subject
          "expires_at": <int|null>,       # on-disk exp for comparison
          "has_license": <bool>,          # is a license file installed at all?
          "valid": <bool>                 # signature-valid AND not expired NOW
        }

    ``subject_at`` mirrors :func:`clawmetry.license.license_subject_at`:
    ``None`` for no license, invalid signature, an ``exp`` claim that
    has already lapsed at ``epoch``, or a signed payload whose ``sub``
    claim is absent / non-string / empty; otherwise the
    whitespace-stripped subject string (casing preserved).

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer / bool value collapses to
        ``subject_at=null`` with ``requested_epoch=null`` so a caller
        cannot silently mis-gate on a typo. HTTP status is 200 either
        way -- the "bad input" signal is ``requested_epoch=null`` plus
        the ``null`` subject, not a 4xx, matching the never-crash
        posture of the surrounding license endpoints.

    Pairs with ``/api/license/tier-at`` / ``/api/license/state-at`` /
    ``/api/license/is-expired-at`` / ``/api/license/days-until-expiry-
    at`` / ``/api/license/expiring-within-at`` -- all share the
    perspective-epoch input pattern, and the
    ``_license_subject_at_snapshot`` reader here carries ``expires_at``
    / ``has_license`` / ``valid`` on the same shape the tier / state
    perspective-epoch scalars carry, so a UI binding two for the same
    install cannot catch them disagreeing on the current-time
    reference fields.

    When ``epoch`` equals "now", the ``subject_at`` field must byte-
    equal ``subject`` (both derive from the same signed ``sub`` claim,
    refuse the invalid-signature branch, and use the same
    ``exp <= cutoff`` boundary via :func:`license_subject_at` /
    :func:`license_subject`), so a UI binding both cannot catch them
    disagreeing at the boundary.

    Never 5xxs -- any underlying failure degrades to
    ``{subject_at: null, requested_epoch: <echo>, subject: null,
    expires_at: null, has_license: false, valid: false}`` (the OSS-
    free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    if isinstance(requested, bool):
        # Guard against ``bool`` subclassing ``int`` -- ``int("1")`` isn't
        # bool, but a query like ``?epoch=True`` gets coerced through the
        # same path the scalar predicate refuses on purpose. Belt-and-
        # braces symmetry with :func:`clawmetry.license.license_subject_at`.
        requested = None
    try:
        snap = _shared._license_subject_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_subject_at: snapshot error: %s", exc)
        snap = {
            "subject": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    subject_at: str | None = None
    if requested is not None:
        try:
            from clawmetry import license as _lic

            subject_at = _lic.license_subject_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_subject_at: derive error: %s", exc)
            subject_at = None
    if subject_at is not None and not isinstance(subject_at, str):
        subject_at = None
    return _shared.jsonify(
        {
            "subject_at": subject_at,
            "requested_epoch": requested,
            "subject": snap["subject"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-subject-at")
def api_license_is_subject_at():
    """``GET /api/license/is-subject-at?subject=<value>&epoch=<int>`` --
    boolean gate for "was the installed license issued to subject <X>
    evaluated as of ``epoch``?" -- the perspective-epoch flavour of
    ``/api/license/is-subject``, for a scheduled-audit tile that wants
    to answer "was this node licensed to <account> on <date>?" without
    the caller having to snapshot the license state at that time or
    compare ``exp`` to a caller-supplied epoch themselves.

    Query parameters:
      * ``subject`` (str, required in-spirit) -- the subject to test
        against. Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_subject_at` (and the current-time
        :func:`clawmetry.license.is_subject`). Missing / empty / non-
        string input degrades to ``is_subject_at=false`` rather than a
        4xx, matching the surrounding endpoints' never-5xx / never-4xx
        posture. Unlike ``/api/license/is-state-at`` (which validates
        against the closed ``LICENSE_STATES`` set), the subject axis
        is deliberately open-ended -- a subject typically encodes an
        account id / email / tenant handle that the code here has no
        business whitelisting, matching :func:`is_subject`'s open-
        ended posture on the current-time axis.
      * ``epoch`` (int, required in-spirit) -- Unix epoch seconds.
        Missing / non-integer / bool input collapses ``subject_at`` to
        ``null`` and the predicate to ``false`` (there is no subject
        to match against once the perspective is unusable -- the
        conservative "no entitlement" fallback matching the never-mis-
        gate posture of the surrounding ``_at`` family).

    Response shape (always HTTP 200)::

        {
          "is_subject_at":     <bool>,
          "subject_at":        <str|null>,    # subject as of epoch (case preserved)
          "requested_subject": <str>,         # normalised (strip+lower) echo of query
          "requested_epoch":   <int|null>,    # int-coerced input, or null on typo
          "subject":           <str|null>,    # current-time subject (case preserved)
          "expires_at":        <int|null>,
          "has_license":       <bool>,
          "valid":             <bool>         # signature-valid AND not expired NOW
        }

    ``is_subject_at`` is ``True`` iff the perspective-epoch subject
    matches ``requested_subject`` (both normalised via strip+lower)
    AND the requested value is a non-empty string -- an empty /
    missing ``subject=`` query returns ``is_subject_at=false`` so a
    caller cannot silently claim a subject that would grant unearned
    entitlement.

    ``subject_at`` mirrors :func:`clawmetry.license.license_subject_at`
    and preserves casing on read; ``requested_subject`` echoes the
    normalised form used for the comparison so a UI can render "you
    asked '<x>'" copy without re-deriving the normalisation itself.

    Mirrors :func:`clawmetry.license.is_subject_at` -- the HTTP shape
    layers ``subject_at`` / ``requested_subject`` / ``requested_epoch``
    / ``subject`` / ``expires_at`` / ``has_license`` / ``valid`` on
    top of that bool so a widget never needs a second call to
    ``/api/license/subject-at`` (or ``/api/license/subject``) to render
    the accompanying "you were licensed to <X>" copy.

    When ``epoch`` equals "now" and ``subject`` is a non-empty string,
    this endpoint must agree with ``/api/license/is-subject`` at the
    boundary for the same install -- both derive from the same signed
    ``sub`` claim via :func:`license_subject_at` /
    :func:`license_subject`, so a UI binding both cannot catch them
    disagreeing at the boundary.

    Shares :func:`_license_subject_at_snapshot` with ``/api/license/
    subject-at`` so the current-time reference fields (``subject`` /
    ``expires_at`` / ``has_license`` / ``valid``) cannot disagree
    between the sibling endpoints for the same install -- the same
    read-once pattern ``/api/license/is-tier-at`` uses with
    :func:`_license_tier_at_snapshot`.

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``is_subject_at=false``, ``subject_at=null``,
    ``subject=null``, ``expires_at=null``, ``has_license=false``,
    ``valid=false``), matching the never-crash posture of the
    surrounding license endpoints.
    """
    raw_subject = _shared.request.args.get("subject", "") or ""
    try:
        requested_subject = str(raw_subject).strip().lower()
    except Exception:
        requested_subject = ""
    raw_epoch = _shared.request.args.get("epoch", "")
    try:
        requested_epoch = int(str(raw_epoch).strip())
    except (TypeError, ValueError):
        requested_epoch = None
    if isinstance(requested_epoch, bool):
        # Guard against ``bool`` subclassing ``int`` -- ``int("1")`` isn't
        # bool, but a query like ``?epoch=True`` gets coerced through the
        # same path the scalar predicate refuses on purpose. Belt-and-
        # braces symmetry with :func:`clawmetry.license.is_subject_at`.
        requested_epoch = None
    try:
        snap = _shared._license_subject_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_subject_at: snapshot error: %s", exc)
        snap = {
            "subject": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    subject_at: str | None = None
    if requested_epoch is not None:
        try:
            from clawmetry import license as _lic

            subject_at = _lic.license_subject_at(requested_epoch)
        except Exception as exc:
            _shared.logger.warning("api_license_is_subject_at: derive error: %s", exc)
            subject_at = None
    if subject_at is not None and not isinstance(subject_at, str):
        subject_at = None
    match = bool(
        requested_subject
        and isinstance(subject_at, str)
        and subject_at.strip().lower() == requested_subject
    )
    return _shared.jsonify(
        {
            "is_subject_at": match,
            "subject_at": subject_at,
            "requested_subject": requested_subject,
            "requested_epoch": requested_epoch,
            "subject": snap["subject"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/permissions-safe")
def api_license_permissions_safe():
    """``GET /api/license/permissions-safe`` -- tri-state scalar of the
    installed license file's on-disk permission hygiene, for a
    security-posture tile that wants ONE field rather than the whole
    ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "permissions_safe": <bool|null>,   # None = no license file
          "file_mode": <str|null>,           # e.g. "0600"; null on Windows
          "has_license": <bool>              # is a license file installed?
        }

    ``permissions_safe`` mirrors
    :func:`clawmetry.license.license_permissions_safe`:

      * ``null`` when there is no license file (Free install -- nothing to
        protect).
      * ``true`` when the file exists AND has no group/world mode bits set
        (POSIX), OR when running on Windows where POSIX mode bits do not
        apply.
      * ``false`` when the file exists on POSIX AND has any of the
        group/other bits set -- exactly the state a "tighten file
        permissions" affordance should highlight.

    Deliberately orthogonal to signature validity: a tampered or expired
    license file still surfaces its real ``permissions_safe`` here, so a
    security-posture tile can render the hygiene banner even when the
    payload branches (``tier`` / ``sub`` / ``nodes``) have collapsed to
    ``null`` under the "refuse untrusted claims" posture used elsewhere.

    Never 5xxs -- any underlying failure degrades to
    ``{permissions_safe: null, file_mode: null, has_license: false}`` (the
    OSS-free branch shape), matching the never-crash posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_permissions_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_permissions_safe: error: %s", exc)
        return _shared.jsonify(
            {"permissions_safe": None, "file_mode": None, "has_license": False}
        )

@_shared.bp_entitlement.route("/api/license/file-mode")
def api_license_file_mode():
    """``GET /api/license/file-mode`` -- scalar view of the installed
    license file's POSIX mode, for a debug row / operator-hint tile that
    wants the raw octal (e.g. ``"0644"``) rather than the whole
    ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "file_mode": <str|null>,           # e.g. "0600"; null on Windows
          "permissions_safe": <bool|null>,   # None = no license file
          "has_license": <bool>              # is a license file installed?
        }

    ``file_mode`` mirrors :func:`clawmetry.license.license_file_mode`:

      * ``null`` when there is nothing meaningful to surface (no license
        file on disk, OR running on Windows where POSIX mode bits do not
        apply).
      * A four-character octal string like ``"0600"`` (safe), ``"0644"``
        (world-readable), or ``"0666"`` (world-writable) otherwise --
        stable format matching ``chmod`` so an operator can copy-paste
        the digits into a ``chmod 0600 <path>`` fix.

    Pairs with ``/api/license/permissions-safe`` the way
    ``/api/license/nodes`` pairs with ``/api/license/within-node-limit``
    -- this endpoint surfaces the raw octal for a debug row, that endpoint
    answers the yes/no question a security tile needs without the caller
    having to parse octal themselves. The two endpoints share
    :func:`_license_permissions_snapshot` so a UI binding both sees a
    consistent snapshot.

    Never 5xxs -- any underlying failure degrades to
    ``{file_mode: null, permissions_safe: null, has_license: false}``.
    """
    try:
        snap = _shared._license_permissions_snapshot()
        return _shared.jsonify(
            {
                "file_mode": snap["file_mode"],
                "permissions_safe": snap["permissions_safe"],
                "has_license": snap["has_license"],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_file_mode: error: %s", exc)
        return _shared.jsonify(
            {"file_mode": None, "permissions_safe": None, "has_license": False}
        )

@_shared.bp_entitlement.route("/api/license/issued-at")
def api_license_issued_at():
    """``GET /api/license/issued-at`` -- scalar view of the installed
    license's ``iat`` claim (epoch seconds), for a "license issued: <date>"
    row that wants ONE integer rather than the whole
    ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "issued_at": <int|null>,   # epoch seconds; None if untrusted
          "age_days": <int|null>,    # days since issuance
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``issued_at`` mirrors :func:`clawmetry.license.license_issued_at`:

      * ``null`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``iat`` into an unsigned body), OR when the signed payload has
        no ``iat`` claim.
      * A positive epoch integer otherwise, unmodified from the signed
        payload.

    Deliberately lenient on expiry, unlike ``/api/license/nodes`` and
    ``/api/license/tier``: a signed-but-lapsed key still surfaces its
    real ``issued_at`` so a support tile can render "issued 800 days ago"
    on an expired key. The ``valid`` field independently carries the
    "signature-valid AND not expired" signal for callers that DO want to
    hide the row on lapsed keys.

    Pairs with ``/api/license/age-days`` -- this endpoint surfaces the
    raw epoch for a debug row, that endpoint answers the "how old" gate a
    UI tile needs without the caller having to do the arithmetic. The two
    endpoints share :func:`_license_issued_snapshot` so a UI binding both
    sees a consistent snapshot.

    Never 5xxs -- any underlying failure degrades to
    ``{issued_at: null, age_days: null, has_license: false, valid: false}``
    (the OSS-free branch shape), matching the never-crash posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_issued_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_issued_at: error: %s", exc)
        return _shared.jsonify(
            {
                "issued_at": None,
                "age_days": None,
                "has_license": False,
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/age-days")
def api_license_age_days():
    """``GET /api/license/age-days`` -- scalar view of the installed
    license's age (days since the ``iat`` claim), for a support/audit
    tile that wants ONE integer rather than computing
    ``(now - iat) // 86400`` at the call site.

    Response shape (always HTTP 200)::

        {
          "age_days": <int|null>,    # days since issuance; None if untrusted
          "issued_at": <int|null>,   # epoch seconds
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``age_days`` mirrors :func:`clawmetry.license.license_age_days`:

      * ``null`` when there is no license file, on the invalid-signature
        branch, or when the signed payload has no ``iat`` claim.
      * A non-negative integer otherwise -- zero on the day of issuance,
        growing monotonically thereafter. Clamped to ``max(0, ...)`` so a
        clock-skew ``iat`` in the future never renders as a negative age.

    Days are floor-divided from seconds ``(now - iat) // 86400``,
    matching how ``/api/license/days-until-expiry`` derives its
    counterpart from ``(exp - now)`` so the two scalars never disagree at
    the day boundary.

    Deliberately lenient on expiry (see ``/api/license/issued-at``): a
    signed-but-lapsed key still surfaces its real ``age_days``. The
    ``valid`` field independently carries the "signature-valid AND not
    expired" signal for callers that want to hide the row on lapsed keys.

    Never 5xxs -- any underlying failure degrades to
    ``{age_days: null, issued_at: null, has_license: false, valid: false}``.
    """
    try:
        snap = _shared._license_issued_snapshot()
        return _shared.jsonify(
            {
                "age_days": snap["age_days"],
                "issued_at": snap["issued_at"],
                "has_license": snap["has_license"],
                "valid": snap["valid"],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_license_age_days: error: %s", exc)
        return _shared.jsonify(
            {
                "age_days": None,
                "issued_at": None,
                "has_license": False,
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/state")
def api_license_state():
    """``GET /api/license/state`` -- scalar view of the installed license's
    high-level lifecycle state, for a status badge / audit row that wants
    ONE string rather than the whole ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "state": "<active|expired|invalid|no_license>",
          "has_license": <bool>,     # is a license file installed at all?
          "valid": <bool>            # signature-valid AND not expired
        }

    ``state`` mirrors :func:`clawmetry.license.license_state` exactly:

      * ``"active"``   -- signature-valid AND not expired.
      * ``"expired"``  -- signature-valid but past its ``exp`` claim.
      * ``"invalid"``  -- file exists but signature is bogus.
      * ``"no_license"`` -- no license file on disk (OSS-free).

    Unlike ``/api/license/tier`` / ``/api/license/subject`` / ``/api/license/nodes``
    (which surface ``null`` on the invalid / expired / no-license branches),
    this endpoint always carries a non-null string -- "no license" is a
    real answer here, not a missing answer, so a UI switch can bind
    directly on ``data.state`` without a null branch.

    A caller who wants ``tier`` / ``sub`` / ``exp`` / ``nodes`` alongside
    should keep hitting ``/api/license/status``; this endpoint deliberately
    strips those to keep a lightweight status-badge tile cheap.

    Never 5xxs -- any underlying failure degrades to
    ``{state: "no_license", has_license: false, valid: false}`` (the
    OSS-free branch shape), matching the never-crash posture of the
    surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_state_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_state: error: %s", exc)
        return _shared.jsonify(
            {"state": "no_license", "has_license": False, "valid": False}
        )

@_shared.bp_entitlement.route("/api/license/is-state")
def api_license_is_state():
    """``GET /api/license/is-state?state=<name>`` -- boolean gate for
    "is the installed license in state <X> right now?" UIs.

    Query parameters:
      * ``state`` (str, required) -- the state to test against. One of
        ``"active"``, ``"expired"``, ``"invalid"``, ``"no_license"``.
        Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_state`. Missing / empty / unknown
        input degrades to ``is_state=false`` rather than a 4xx, matching
        the surrounding endpoints' never-5xx / never-4xx posture.

    Response shape (always HTTP 200)::

        {
          "is_state": <bool>,
          "state": "<active|expired|invalid|no_license>",  # currently-installed
          "requested_state": <str>,                        # normalised echo of query
          "has_license": <bool>,
          "valid": <bool>                                  # signature-valid AND not expired
        }

    ``is_state`` is ``True`` iff the currently-installed state
    byte-equals ``requested_state`` (after both are lower/stripped) AND
    the requested value is one of the four canonical states -- a typo
    like ``?state=actiev`` returns ``is_state=false`` so a caller cannot
    silently mis-gate on a mis-spelled state name.

    Mirrors :func:`clawmetry.license.is_state` -- the HTTP shape layers
    ``state`` / ``requested_state`` / ``has_license`` / ``valid`` on top
    of that bool so a widget never needs a second call to
    ``/api/license/state`` (or ``/api/license/status``) to render the
    accompanying "you're in state <X>" copy.
    """
    from clawmetry.license import LICENSE_STATES

    raw = _shared.request.args.get("state", "") or ""
    try:
        requested = str(raw).strip().lower()
    except Exception:
        requested = ""
    try:
        snap = _shared._license_state_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_state: error: %s", exc)
        snap = {"state": "no_license", "has_license": False, "valid": False}
    match = bool(
        requested
        and requested in LICENSE_STATES
        and isinstance(snap["state"], str)
        and snap["state"] == requested
    )
    return _shared.jsonify(
        {
            "is_state": match,
            "state": snap["state"],
            "requested_state": requested,
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/pubkey-fingerprint")
def api_license_pubkey_fingerprint():
    """``GET /api/license/pubkey-fingerprint`` -- scalar view of the embedded
    Ed25519 verification key's SHA-256 fingerprint, for a trust-anchor
    attestation tile that wants ONE string rather than the whole
    ``/api/license/pubkey`` envelope (algorithm, format, PEM body, ...).

    Response shape (always HTTP 200)::

        {
          "pubkey_fingerprint_sha256": <str|null>,   # 64-char lowercase hex
          "pubkey_fingerprint_short":  <str|null>,   # first 16 chars
          "valid": <bool>                            # embedded PEM parses?
        }

    Independent of any installed license file: this endpoint answers
    "which trust anchor is THIS install verifying against?" so an
    operator can compare the value to the canonical fingerprint published
    at ``https://clawmetry.com/security`` and detect that ``_PUBLIC_KEY_PEM``
    hasn't been swapped for an attacker-controlled key. A dashboard tile
    that only needs the fingerprint string should bind here rather than to
    ``/api/license/pubkey``; the two share :func:`pubkey_fingerprint` so
    they never disagree.

    Never 5xxs -- any underlying failure degrades to
    ``{pubkey_fingerprint_sha256: null, pubkey_fingerprint_short: null,
    valid: false}`` matching the never-crash posture of the surrounding
    license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_pubkey_fingerprint_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_pubkey_fingerprint: error: %s", exc)
        return _shared.jsonify(
            {
                "pubkey_fingerprint_sha256": None,
                "pubkey_fingerprint_short": None,
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/is-pubkey-fingerprint")
def api_license_is_pubkey_fingerprint():
    """``GET /api/license/is-pubkey-fingerprint?fp=<hex>`` -- boolean gate
    for "is this install verifying against pubkey <FP> right now?" UIs.

    Query parameters:
      * ``fp`` (str, required) -- the fingerprint to test against. Compared
        under the same tolerant normalisation as
        :func:`clawmetry.license.is_pubkey_fingerprint`: whitespace
        stripped, lowercased, ``:`` separators removed, either the full
        64-char hex OR the 16-char short-form accepted. Missing / empty
        input degrades to ``is_pubkey_fingerprint=false`` rather than a
        4xx, matching the surrounding endpoints' never-5xx / never-4xx
        posture.

    Response shape (always HTTP 200)::

        {
          "is_pubkey_fingerprint": <bool>,
          "pubkey_fingerprint_sha256": <str|null>,   # currently-active fp
          "pubkey_fingerprint_short":  <str|null>,   # first 16 chars
          "requested_fp": <str>,                     # normalised echo
          "valid": <bool>                            # embedded PEM parses?
        }

    ``is_pubkey_fingerprint`` is ``True`` iff the embedded PEM parses AND
    the normalised request matches (full or short form). A typo like
    ``?fp=abcxyz`` collapses to ``False`` (non-hex rejected up-front) so a
    caller cannot silently mis-gate on a bad string.

    Mirrors :func:`clawmetry.license.is_pubkey_fingerprint` -- the HTTP
    shape layers ``pubkey_fingerprint_sha256`` /
    ``pubkey_fingerprint_short`` / ``requested_fp`` / ``valid`` on top of
    that bool so a supply-chain audit widget never needs a second call to
    ``/api/license/pubkey-fingerprint`` to render the accompanying
    "expected <X>" copy.
    """
    raw = _shared.request.args.get("fp", "") or ""
    try:
        requested = raw.strip().lower().replace(":", "")
    except Exception:
        requested = ""
    try:
        snap = _shared._license_pubkey_fingerprint_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_pubkey_fingerprint: error: %s", exc)
        snap = {
            "pubkey_fingerprint_sha256": None,
            "pubkey_fingerprint_short": None,
            "valid": False,
        }
    actual = snap["pubkey_fingerprint_sha256"]
    matches = False
    if requested and isinstance(actual, str) and actual:
        if all(c in "0123456789abcdef" for c in requested):
            actual_norm = actual.strip().lower()
            if len(requested) == 64:
                matches = actual_norm == requested
            elif len(requested) == 16:
                matches = actual_norm.startswith(requested)
    return _shared.jsonify(
        {
            "is_pubkey_fingerprint": bool(matches),
            "pubkey_fingerprint_sha256": snap["pubkey_fingerprint_sha256"],
            "pubkey_fingerprint_short": snap["pubkey_fingerprint_short"],
            "requested_fp": requested,
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/expires-at")
def api_license_expires_at():
    """``GET /api/license/expires-at`` -- scalar view of the installed
    license's ``exp`` claim (epoch seconds), for a "license expires:
    <date>" row that wants ONE integer rather than the whole
    ``/api/license/status`` envelope.

    Response shape (always HTTP 200)::

        {
          "expires_at": <int|null>,          # epoch; None if untrusted / perpetual
          "days_until_expiry": <int|null>,   # signed days remaining
          "has_license": <bool>,             # is a license file installed at all?
          "valid": <bool>                    # signature-valid AND not expired
        }

    ``expires_at`` mirrors :func:`clawmetry.license.license_expires_at`:

      * ``null`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``exp`` into an unsigned body), OR when the signed payload has
        no ``exp`` claim (perpetual license -- distinguish from
        no-license via ``has_license``).
      * A positive epoch integer otherwise, unmodified from the signed
        payload.

    Deliberately lenient on expiry, unlike ``/api/license/tier`` and
    ``/api/license/nodes``: a signed-but-lapsed key still surfaces its
    real ``expires_at`` so a support tile can render "expired 12 days
    ago" on an expired key. The ``valid`` field independently carries
    the "signature-valid AND not expired" signal for callers that DO
    want to hide the row on lapsed keys.

    Pairs with ``/api/license/days-until-expiry`` -- this endpoint
    surfaces the raw epoch for an audit row, that endpoint answers the
    caller-friendly "how many days left" without the caller having to do
    the arithmetic. The two endpoints share :func:`_license_expires_snapshot`
    so a UI binding both sees a consistent snapshot.

    Never 5xxs -- any underlying failure degrades to
    ``{expires_at: null, days_until_expiry: null, has_license: false,
    valid: false}`` (the OSS-free branch shape), matching the never-crash
    posture of the surrounding license endpoints.
    """
    try:
        return _shared.jsonify(_shared._license_expires_snapshot())
    except Exception as exc:
        _shared.logger.warning("api_license_expires_at: error: %s", exc)
        return _shared.jsonify(
            {
                "expires_at": None,
                "days_until_expiry": None,
                "has_license": False,
                "valid": False,
            }
        )

@_shared.bp_entitlement.route("/api/license/is-expiring-at")
def api_license_is_expiring_at():
    """``GET /api/license/is-expiring-at?epoch=<int>`` -- predicate
    matching the operator-supplied epoch against the installed license's
    ``exp`` claim, for a "we noticed your key expires <date>" tile that
    binds a specific ``exp`` value and wants to detect renewal (the on-
    disk key no longer matches the value it was rendered with).

    Response shape (always HTTP 200)::

        {
          "is_expiring_at": <bool>,          # exact match; else false
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "expires_at": <int|null>,          # current on-disk exp for comparison
          "has_license": <bool>,
          "valid": <bool>                    # signature-valid AND not expired
        }

    ``is_expiring_at`` mirrors :func:`clawmetry.license.is_expiring_at`:

      * ``false`` when there is no license file, on the invalid-signature
        branch, on the expired branch (a predicate that fired ``true`` on
        a lapsed key would push callers to gate renewal UI on a value
        that no longer implies entitlement), on the perpetual-license
        branch (no ``exp`` to compare), OR when ``epoch`` doesn't parse
        as an integer.
      * ``true`` iff the installed key is signature-valid, not expired,
        carries an ``exp`` claim, AND that claim equals the supplied
        ``epoch`` exactly.

    Deliberately strict on validity, unlike the sibling
    ``/api/license/expires-at`` endpoint (which is lenient on expiry so a
    support tile can render "expired 12 days ago"). See the docstring on
    :func:`clawmetry.license.is_expiring_at` for the rationale.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to
        ``is_expiring_at=false`` with ``requested_epoch=null`` so a
        caller cannot silently mis-gate on a typo. HTTP status is 200
        either way -- the "bad input" signal is the ``false`` result,
        not a 4xx, matching the never-crash posture of the surrounding
        license endpoints.
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    snap = _shared._license_expires_snapshot()
    try:
        from clawmetry import license as _lic

        matched = _lic.is_expiring_at(requested) if requested is not None else False
    except Exception as exc:
        _shared.logger.warning("api_license_is_expiring_at: error: %s", exc)
        matched = False
    return _shared.jsonify(
        {
            "is_expiring_at": bool(matched),
            "requested_epoch": requested,
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/days-until-expiry-at")
def api_license_days_until_expiry_at():
    """``GET /api/license/days-until-expiry-at?epoch=<int>`` -- scalar
    countdown evaluated at an operator-supplied perspective epoch, for a
    scheduled-audit / retrospective tile that wants to answer "how many
    days until (or past) expiry was <date>?" without the caller having
    to compute ``(exp - epoch) // 86400`` at the call site.

    Response shape (always HTTP 200)::

        {
          "days_left": <int|null>,           # signed days from epoch to exp
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "expires_at": <int|null>,          # current on-disk exp
          "has_license": <bool>,             # is a license file installed at all?
          "valid": <bool>                    # signature-valid AND not expired
        }

    ``days_left`` mirrors :func:`clawmetry.license.days_until_expiry_at`:

      * ``null`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``exp`` into an unsigned body), on the perpetual-license branch
        (no ``exp`` to count against), OR when ``epoch`` doesn't parse
        as an integer.
      * A signed integer number of days otherwise. Zero when ``epoch``
        falls on the day of expiry; negative when ``epoch`` is after
        ``exp`` (support scenario: "how many days past expiry was
        <date>?"); positive when ``epoch`` is before ``exp``.

    Deliberately lenient on expiry, mirroring
    ``/api/license/days-until-expiry`` and ``/api/license/expires-at``: a
    signed-but-lapsed key still surfaces its real ``days_left`` (with a
    negative sign when ``epoch`` is after ``exp``) so a support/audit
    tile can render "would have been expired 12 days ago as of last
    Friday" without special-casing the expired branch. The ``valid``
    field independently carries the "signature-valid AND not expired"
    signal for callers that DO want to hide the row on lapsed keys.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to ``days_left=null`` with
        ``requested_epoch=null`` so a caller cannot silently miscount on
        a typo. HTTP status is 200 either way -- the "bad input" signal
        is the ``null`` result, not a 4xx, matching the never-crash
        posture of the surrounding license endpoints.

    Pairs with ``/api/license/is-expiring-at`` -- both share the
    perspective-epoch input pattern and the
    :func:`_license_expires_snapshot` reader, so a UI binding both
    endpoints for the same install cannot catch them disagreeing on
    ``expires_at`` / ``has_license`` / ``valid``. Together they let a
    dashboard render "on <date>, the license would have been N days
    from expiry -- an exact match against a specific ``exp`` value?"
    from two orthogonal one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{days_left: null, requested_epoch: null, expires_at: null,
    has_license: false, valid: false}`` (the OSS-free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_expires_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_days_until_expiry_at: snapshot error: %s", exc)
        snap = {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    days_left: int | None
    if requested is None:
        days_left = None
    else:
        try:
            from clawmetry import license as _lic

            days_left = _lic.days_until_expiry_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_days_until_expiry_at: derive error: %s", exc)
            days_left = None
    return _shared.jsonify(
        {
            "days_left": days_left,
            "requested_epoch": requested,
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/expiring-within-at")
def api_license_expiring_within_at():
    """``GET /api/license/expiring-within-at?days=<N>&epoch=<int>`` --
    boolean gate for "would we have shown a renewal warning as of
    ``epoch``?" -- the perspective-epoch flavour of
    ``/api/license/expiring-within``, for a scheduled-audit /
    retrospective tile that wants to answer "was the license inside the
    ``days``-day renewal window on <date>?" without having to snapshot
    the license state at that time.

    Response shape (always HTTP 200)::

        {
          "expiring_within": <bool>,
          "days_left": <int|null>,           # signed days from epoch to exp
          "threshold_days": <int>,           # normalised threshold echo
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "expires_at": <int|null>,          # current on-disk exp
          "has_license": <bool>,             # is a license file installed at all?
          "valid": <bool>                    # signature-valid AND not expired
        }

    ``expiring_within`` mirrors
    :func:`clawmetry.license.is_expiring_within_at`:

      * ``true`` iff a license is installed, signature-valid, carries an
        ``exp`` claim, AND the days from ``epoch`` until ``exp`` fall
        between 0 and ``threshold_days`` inclusive.
      * ``false`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``exp`` into an unsigned body), on the perpetual-license branch
        (no ``exp`` to gate against), on the already-lapsed-at-epoch
        branch (a caller wants "renewal window" separate from "already
        expired at that time"), OR when either query argument doesn't
        parse.

    ``days_left`` is layered on top of the bool so a paywall widget
    never needs a second call to
    ``/api/license/days-until-expiry-at`` to render the accompanying
    "expires in N days as of that date" copy. It mirrors
    :func:`clawmetry.license.days_until_expiry_at` -- lenient on
    expiry, so an already-lapsed-at-epoch key still surfaces its real
    (negative) ``days_left`` even though ``expiring_within`` collapses
    to ``false``. Callers that want to hide the row on lapsed keys have
    the ``valid`` signal.

    Query parameters:

      * ``days`` (int, optional) -- the renewal-window threshold.
        Defaults to ``30``. Negative input clamps to ``0``; non-numeric
        input collapses to ``expiring_within=false`` with
        ``threshold_days=0`` rather than a 4xx, matching the surrounding
        endpoints' never-5xx / never-4xx posture.
      * ``epoch`` (int, required) -- perspective epoch (Unix seconds).
        A missing / non-integer value collapses to
        ``expiring_within=false`` with ``requested_epoch=null`` and
        ``days_left=null`` so a caller cannot silently mis-gate on a
        typo.

    Pairs with ``/api/license/days-until-expiry-at`` /
    ``/api/license/is-expiring-at`` -- all three share the
    :func:`_license_expires_snapshot` reader so a UI binding any two
    endpoints for the same install cannot catch them disagreeing on
    ``expires_at`` / ``has_license`` / ``valid``. Together they let a
    dashboard render "on <date>, the license would have been N days
    from expiry -- and would we have warned?" from two orthogonal
    one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{expiring_within: false, days_left: null, threshold_days: 0,
    requested_epoch: null, expires_at: null, has_license: false,
    valid: false}`` (the OSS-free branch shape).
    """
    raw_days = _shared.request.args.get("days", "30")
    try:
        threshold = int(raw_days)
        threshold_ok = True
    except (TypeError, ValueError):
        threshold = 0
        threshold_ok = False
    if threshold < 0:
        threshold = 0
    raw_epoch = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw_epoch).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_expires_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_expiring_within_at: snapshot error: %s", exc)
        snap = {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    days_left: int | None
    within = False
    if requested is not None and threshold_ok:
        try:
            from clawmetry import license as _lic

            days_left = _lic.days_until_expiry_at(requested)
            within = _lic.is_expiring_within_at(threshold, requested)
        except Exception as exc:
            _shared.logger.warning("api_license_expiring_within_at: derive error: %s", exc)
            days_left = None
            within = False
    elif requested is not None:
        # Threshold garbage but epoch parsed: still surface days_left for
        # the accompanying "expires in N days" copy so the widget can
        # render even with the gate off. Matches the never-crash posture.
        try:
            from clawmetry import license as _lic

            days_left = _lic.days_until_expiry_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_expiring_within_at: derive error: %s", exc)
            days_left = None
    else:
        days_left = None
    return _shared.jsonify(
        {
            "expiring_within": bool(within),
            "days_left": days_left,
            "threshold_days": threshold,
            "requested_epoch": requested,
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/age-days-at")
def api_license_age_days_at():
    """``GET /api/license/age-days-at?epoch=<int>`` -- scalar view of the
    installed license's age evaluated at an operator-supplied perspective
    epoch, for a scheduled-audit / retrospective tile that wants to
    answer "how old was the license as of <date>?" without the caller
    having to snapshot the license state at that time or compute
    ``(epoch - iat) // 86400`` at the call site.

    Response shape (always HTTP 200)::

        {
          "age_days": <int|null>,        # signed days from iat to epoch
          "requested_epoch": <int|null>, # int-coerced input, or null on typo
          "issued_at": <int|null>,       # current on-disk iat
          "has_license": <bool>,         # is a license file installed at all?
          "valid": <bool>                # signature-valid AND not expired
        }

    ``age_days`` mirrors :func:`clawmetry.license.license_age_days_at`:

      * ``null`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``iat`` into an unsigned body), when the signed payload has no
        ``iat`` claim, OR when ``epoch`` doesn't parse as an integer.
      * A signed integer number of days otherwise. Zero when ``epoch``
        equals the ``iat`` second; positive when ``epoch`` is after
        ``iat`` (the normal case -- "N days old as of <date>"); negative
        when ``epoch`` is BEFORE ``iat`` (support scenario: "the operator
        rolled a machine back to a pre-issuance timestamp -- how far
        before issuance were we?").

    Deliberately NOT clamped to ``max(0, ...)`` -- unlike the "now"
    endpoint ``/api/license/age-days``, which clamps because clock-skew
    is the only way ``iat`` can be in the future when reading against
    ``time.time()``. Here the caller EXPLICITLY passes a perspective
    epoch, so a negative result is a real, actionable signal (they asked
    a question that only makes sense pre-issuance), not clock skew to be
    hidden. Mirrors the signed-integer posture of
    ``/api/license/days-until-expiry-at``.

    Deliberately lenient on expiry, mirroring ``/api/license/age-days``
    and ``/api/license/issued-at``: a signed-but-lapsed key still
    surfaces its real ``age_days`` at the perspective epoch, so a
    support tile can render "was 12 days old as of that date" without
    special-casing the expired branch. The ``valid`` field independently
    carries the "signature-valid AND not expired" signal for callers
    that DO want to hide the row on lapsed keys.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to ``age_days=null`` with
        ``requested_epoch=null`` so a caller cannot silently miscount on
        a typo. HTTP status is 200 either way -- the "bad input" signal
        is the ``null`` result, not a 4xx, matching the never-crash
        posture of the surrounding license endpoints.

    Pairs with ``/api/license/issued-at`` and ``/api/license/age-days``
    -- all three share :func:`_license_issued_snapshot`, so a UI binding
    any pair of them for the same install cannot catch them disagreeing
    on ``issued_at`` / ``has_license`` / ``valid``. Together they let a
    dashboard render "on <date>, the license was N days old, issued at
    epoch E" from two orthogonal one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{age_days: null, requested_epoch: null, issued_at: null,
    has_license: false, valid: false}`` (the OSS-free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_issued_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_age_days_at: snapshot error: %s", exc)
        snap = {
            "issued_at": None,
            "age_days": None,
            "has_license": False,
            "valid": False,
        }
    age_days: int | None
    if requested is None:
        age_days = None
    else:
        try:
            from clawmetry import license as _lic

            age_days = _lic.license_age_days_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_age_days_at: derive error: %s", exc)
            age_days = None
    return _shared.jsonify(
        {
            "age_days": age_days,
            "requested_epoch": requested,
            "issued_at": snap["issued_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-expired-at")
def api_license_is_expired_at():
    """``GET /api/license/is-expired-at?epoch=<int>`` -- boolean gate
    for "was the installed license expired evaluated as of ``epoch``?" --
    the perspective-epoch flavour of ``/api/license/is-expired``, for a
    scheduled-audit / retrospective tile that wants to answer "would we
    have shown the expired banner on <date>?" without the caller having
    to compare ``exp`` against a specific epoch themselves.

    Response shape (always HTTP 200)::

        {
          "is_expired_at": <bool>,           # true iff exp <= epoch on a signed key
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "expires_at": <int|null>,          # current on-disk exp for comparison
          "has_license": <bool>,             # is a license file installed at all?
          "valid": <bool>                    # signature-valid AND not expired NOW
        }

    ``is_expired_at`` mirrors :func:`clawmetry.license.is_expired_at`:

      * ``false`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``exp`` into an unsigned body), on the perpetual-license branch
        (no ``exp`` to compare against), when ``exp`` is strictly greater
        than ``epoch`` (the key was not yet expired at that perspective),
        OR when ``epoch`` doesn't parse as an integer.
      * ``true`` iff the installed key is signature-valid, carries an
        ``exp`` claim, AND ``exp <= epoch``.

    Deliberately lenient on expiry NOW, unlike ``/api/license/is-expiring-at``
    (which refuses lapsed keys because a renewal-window predicate on a
    lapsed key would push callers to gate the WRONG UI). A retrospective
    "was this expired on <date>?" tile absolutely should keep firing
    ``true`` on a lapsed key -- that IS the support scenario -- so
    ``is_expired_at`` still returns ``true`` on a signed-but-lapsed key
    when ``epoch`` falls at or after ``exp``. The ``valid`` field
    independently carries the "signature-valid AND not expired NOW"
    signal for callers that DO want to gate off the current-state
    validity.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to
        ``is_expired_at=false`` with ``requested_epoch=null`` so a
        caller cannot silently mis-gate on a typo. HTTP status is 200
        either way -- the "bad input" signal is the ``false`` result,
        not a 4xx, matching the never-crash posture of the surrounding
        license endpoints.

    Pairs with ``/api/license/is-expiring-at`` and
    ``/api/license/days-until-expiry-at`` -- all three share the
    perspective-epoch input pattern and the
    :func:`_license_expires_snapshot` reader, so a UI binding any two
    for the same install cannot catch them disagreeing on
    ``expires_at`` / ``has_license`` / ``valid``. Together they let a
    dashboard render "on <date>, the license would have been N days
    from expiry, matched a specific ``exp`` value, and was expired?"
    from three orthogonal one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{is_expired_at: false, requested_epoch: null, expires_at: null,
    has_license: false, valid: false}`` (the OSS-free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_expires_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_expired_at: snapshot error: %s", exc)
        snap = {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    matched = False
    if requested is not None:
        try:
            from clawmetry import license as _lic

            matched = _lic.is_expired_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_is_expired_at: derive error: %s", exc)
            matched = False
    return _shared.jsonify(
        {
            "is_expired_at": bool(matched),
            "requested_epoch": requested,
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-valid-at")
def api_license_is_valid_at():
    """``GET /api/license/is-valid-at?epoch=<int>`` -- boolean gate for
    "would the installed license have been valid evaluated as of
    ``epoch``?" -- the perspective-epoch flavour of
    ``/api/license/status``'s ``valid`` field, for a scheduled-audit /
    retrospective paywall tile that wants to answer "would this node
    have been entitled on <date>?" without the caller having to snapshot
    the license state at that time or fold the ``exp`` claim against a
    specific epoch themselves.

    Response shape (always HTTP 200)::

        {
          "is_valid_at": <bool>,             # signature-valid AND (perpetual OR exp > epoch)
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "expires_at": <int|null>,          # current on-disk exp for comparison
          "has_license": <bool>,             # is a license file installed at all?
          "valid": <bool>                    # signature-valid AND not expired NOW
        }

    ``is_valid_at`` mirrors :func:`clawmetry.license.is_license_valid_at`:

      * ``false`` when there is no license file, on the invalid-signature
        branch (payload cannot be trusted -- an attacker could stuff any
        ``exp`` into an unsigned body), when ``exp <= epoch`` (the key
        was not yet -- or no longer -- entitled at that perspective), OR
        when ``epoch`` doesn't parse as an integer.
      * ``true`` iff the installed key is signature-valid AND either
        carries no ``exp`` claim (perpetual key) OR ``exp > epoch``.

    Perfect complement to ``/api/license/is-expired-at`` on a signature-
    valid, non-perpetual key (``is_valid_at`` is the strict negation of
    ``is_expired_at``), but the two DIVERGE on the invalid-signature and
    no-license branches: both collapse to ``false`` on purpose, because
    "not expired" on an unsigned body is not the same as "still
    entitled". A UI wanting to distinguish "no license" / "broken
    license" / "lapsed at that time" / "valid at that time" reads this
    endpoint together with ``/api/license/is-expired-at`` and
    ``/api/license/state-at``.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer value collapses to ``is_valid_at=false``
        with ``requested_epoch=null`` so a caller cannot silently mis-
        gate on a typo. HTTP status is 200 either way -- the "bad input"
        signal is the ``false`` result, not a 4xx, matching the never-
        crash posture of the surrounding license endpoints.

    Pairs with ``/api/license/is-expired-at``,
    ``/api/license/is-expiring-at``, and
    ``/api/license/days-until-expiry-at`` -- all four share the
    perspective-epoch input pattern and the
    :func:`_license_expires_snapshot` reader, so a UI binding any two
    for the same install cannot catch them disagreeing on ``expires_at``
    / ``has_license`` / ``valid``. Together they let a dashboard render
    "on <date>, the license would have been entitled, N days from
    expiry, matched a specific ``exp`` value, and not yet expired?" from
    four orthogonal one-shot GETs.

    Never 5xxs -- any underlying failure degrades to
    ``{is_valid_at: false, requested_epoch: null, expires_at: null,
    has_license: false, valid: false}`` (the OSS-free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_expires_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_valid_at: snapshot error: %s", exc)
        snap = {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    matched = False
    if requested is not None:
        try:
            from clawmetry import license as _lic

            matched = _lic.is_license_valid_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_is_valid_at: derive error: %s", exc)
            matched = False
    return _shared.jsonify(
        {
            "is_valid_at": bool(matched),
            "requested_epoch": requested,
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )
