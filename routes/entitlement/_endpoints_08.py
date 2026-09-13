"""routes/entitlement/_endpoints_08.py — endpoint handlers api_entitlement_min_tier_for_features_batch .. api_entitlement_has_retention_window_at_batch.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-features-batch",
    methods=["POST"],
)
def api_entitlement_min_tier_for_features_batch():
    """``POST /api/entitlement/min-tier-for-features-batch`` -- bundle-
    axis batch sibling of ``/api/entitlement/min-tier-for-features``.

    Where the singular endpoint folds ONE bundle of features to ONE
    ``required_tier`` (the cheapest purchasable tier admitting the whole
    bundle), this folds N caller-supplied feature bundles to N
    ``required_tier`` rows in ONE round-trip. Distinct from
    ``/min-tier-batch`` (per-*item* cheapest tier for a single flat
    bundle -- rows are individual feature ids) and ``/required-tier-batch``
    (aggregate across the five capacity axes for ONE bundle): this
    preserves the per-*bundle* grouping so each row is the fold-answer
    for that whole bundle.

    Use case: a pricing-matrix or upgrade-walkthrough surface comparing
    several hypothetical feature sets ("Starter add-ons vs Pro add-ons
    vs Enterprise add-ons") renders off one call instead of N calls to
    ``/min-tier-for-features``.

    POST rather than GET because the caller-supplied set of bundles can
    grow past a comfortable query-string length; the sibling singular
    endpoint uses GET+CSV where the bundle is small.

    Request body::

        {
          "bundles": [
            ["fleet", "sso"],
            ["otel_export"],
            []
          ]
        }

    A shorthand ``{"bundles": ["fleet", "sso"]}`` (bare list of strings)
    is treated as ONE bundle, matching the singular endpoint's bare-CSV
    posture; a missing / non-list ``bundles`` value is a 400. An empty
    ``bundles=[]`` list is a 400 for the same reason the singular
    endpoint 400s on an empty ``features=`` -- distinguishes "caller
    asked for nothing" from "caller asked and every token was unknown".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` is byte-identical to the bare singular endpoint body
    minus the resolver envelope::

        {
          "features":            ["fleet", "sso"],
          "unknown":             ["bogus"],
          "kind":                "features",
          "count":               2,
          "required_tier":       "enterprise" | null,
          "required_tier_label": "Enterprise" | null,
          "required_tier_rank":  <int>,   # -1 when required_tier is null
          "free":                <bool>,
        }

    Per-bundle normalisation matches the singular endpoint: whitespace
    stripped, lowercased, deduplicated preserving first-seen order;
    unknown ids bucketed into the per-bundle ``unknown`` list instead
    of mis-routing the ladder to a higher tier. Empty / all-unknown
    bundles surface as a stable row with ``required_tier=null`` (does
    NOT short-circuit the batch).

    - **400** when ``bundles`` is missing / non-list / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the pricing surface keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.min_tier_for_features_batch(bundles)
        out_rows = [
            _shared._min_tier_for_bundle_row_to_body(row, "features") for row in rows
        ]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_features_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-runtimes-batch",
    methods=["POST"],
)
def api_entitlement_min_tier_for_runtimes_batch():
    """``POST /api/entitlement/min-tier-for-runtimes-batch`` -- runtime-
    axis twin of ``/api/entitlement/min-tier-for-features-batch``.

    Same never-5xx posture, same partial-unknown bucketing, same POST
    envelope. Runtime aliases (``claude-code`` -> ``claude_code``) are
    canonicalised per bundle through
    :func:`clawmetry.entitlements.canonical_runtime` so a caller does
    not need to normalise before calling; unknown ids land in the per-
    bundle ``unknown`` and drop from the ``required_tier`` walk (a typo
    does NOT silently mis-route the ladder to a higher tier).

    Request body::

        {
          "bundles": [
            ["claude_code", "codex"],
            ["openclaw"],
            []
          ]
        }

    Response shape and error paths mirror
    ``/min-tier-for-features-batch`` exactly, with ``kind="runtimes"``
    and a ``runtimes`` list in place of ``features`` per row.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.min_tier_for_runtimes_batch(bundles)
        out_rows = [
            _shared._min_tier_for_bundle_row_to_body(row, "runtimes") for row in rows
        ]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_runtimes_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-features-bundle-batch",
    methods=["POST"],
)
def api_entitlement_missing_features_bundle_batch():
    """``POST /api/entitlement/missing-features-bundle-batch`` -- row-
    detail complement of ``/api/entitlement/has-features-bundle-batch``
    on the LIVE per-install slot.

    Where the singular ``/api/entitlement/missing-features`` folds ONE
    bundle to ONE per-item denial list, this folds N caller-supplied
    feature bundles to N per-bundle ``missing`` rows in ONE round-trip
    so a paywall diagnostics matrix or upgrade-walkthrough surface
    comparing several hypothetical feature sets ("starter add-ons vs
    pro add-ons vs enterprise add-ons -- which items each is still
    missing on the LIVE grant?") hydrates the whole column off ONE
    call instead of N calls to ``/missing-features``.

    Distinct from ``/missing-features-at-batch`` (which fixes ONE
    bundle and sweeps N perspective tiers): this fixes N bundles and
    reads the LIVE per-install grant. Row-detail sibling of the
    reverse-lookup ``/min-tier-for-features-batch`` on the boolean-
    fold slot's complement seat -- the two responses pair on the same
    ``features`` / ``unknown`` / ``kind`` / ``count`` axes so a UI
    can render "denied right now? / cheapest tier that grants it?"
    side by side per bundle off two calls.

    POST rather than GET because the caller-supplied set of bundles
    can grow past a comfortable query-string length; the sibling
    singular ``/missing-features`` endpoint uses GET+CSV where the
    bundle is small.

    Request body::

        {
          "bundles": [
            ["fleet", "sso"],
            ["otel_export"],
            []
          ]
        }

    A shorthand ``{"bundles": ["fleet", "sso"]}`` (bare list of
    strings) is treated as ONE bundle, matching the singular
    endpoint's bare-CSV posture; a missing / non-list ``bundles``
    value is a 400. An empty ``bundles=[]`` is a 400 for the same
    reason ``/min-tier-for-features-batch`` 400s on empty input --
    distinguishes "caller asked for nothing" from "caller asked and
    every bundle was empty".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` is byte-identical to
    :func:`_min_tier_for_bundle_row_to_body` on the axis-echo slots
    with the ``min_tier*`` / ``free`` slots swapped for a ``missing``
    list matching the singular endpoint's ``missing`` slot::

        {
          "features": ["fleet", "sso"],
          "unknown":  ["bogus"],
          "kind":     "features",
          "count":    2,
          "missing":  [<subset not granted on LIVE>],
        }

    Per-bundle normalisation matches the singular endpoint: whitespace
    stripped, lowercased, deduplicated preserving first-seen order;
    unknown ids bucketed into the per-bundle ``unknown`` list instead
    of leaking into ``missing`` (a typo surfaces via ``unknown[]``
    rather than silently rendering "denied"). Empty / all-unknown
    bundles surface as a stable row with ``missing=[]`` (matches
    :func:`missing_features` empty-``[]`` posture).

    Grace posture per-row mirrors ``/missing-features`` byte-for-byte:
    while ``grace`` is ``True`` (the current rollout state) every
    fully-known bundle reports ``missing=[]``; post-enforcement each
    row reflects the underlying :meth:`Entitlement.allows_feature`
    answer per item.

    - **400** when ``bundles`` is missing / non-list / empty
    - **Never 5xxs**: a resolver / delegate failure yields the fallback
      envelope (empty ``bundles`` list) so the paywall matrix keeps
      rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.missing_features_bundle_batch(bundles)
        out_rows = [_shared._missing_bundle_row_body(row, "features") for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-runtimes-bundle-batch",
    methods=["POST"],
)
def api_entitlement_missing_runtimes_bundle_batch():
    """``POST /api/entitlement/missing-runtimes-bundle-batch`` -- runtime-
    axis twin of ``/api/entitlement/missing-features-bundle-batch``.

    Same never-5xx posture, same partial-unknown bucketing, same POST
    envelope. Runtime aliases (``claude-code`` -> ``claude_code``) are
    canonicalised per bundle through
    :func:`clawmetry.entitlements.canonical_runtime` so a caller does
    not need to normalise before calling; unknown ids land in the
    per-bundle ``unknown`` and drop from the ``missing`` walk (a typo
    does NOT silently render as "denied").

    :data:`clawmetry.entitlements.FREE_RUNTIMES` (``openclaw``)
    reports ``missing=[]`` on every row on the LIVE install
    regardless of rollout state.

    Request body::

        {
          "bundles": [
            ["claude_code", "codex"],
            ["openclaw"],
            []
          ]
        }

    Response shape and error paths mirror
    ``/missing-features-bundle-batch`` exactly, with ``kind="runtimes"``
    and a ``runtimes`` list in place of ``features`` per row.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.missing_runtimes_bundle_batch(bundles)
        out_rows = [_shared._missing_bundle_row_body(row, "runtimes") for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-features-bundle-batch",
    methods=["POST"],
)
def api_entitlement_has_features_bundle_batch():
    """``POST /api/entitlement/has-features-bundle-batch`` -- bundle-axis
    batch boolean-fold sibling of ``/api/entitlement/has-features``.

    Where the singular endpoint folds ONE bundle of features to ONE
    ``has_features`` boolean on the LIVE install, this folds N caller-
    supplied feature bundles to N ``has_features`` rows in ONE round-
    trip. Distinct from ``/has-features-at-batch`` (which fixes ONE
    feature bundle and sweeps N perspective tiers): this fixes N
    bundles and reads the LIVE per-install grant. Boolean-fold sibling
    of ``/min-tier-for-features-batch`` on the reverse-lookup slot; the
    two responses pair on the same ``features`` / ``unknown`` / ``kind``
    / ``count`` axes so a UI can render "granted right now? / cheapest
    tier that grants it?" side by side per bundle off two calls.

    Use case: a paywall matrix or upgrade-walkthrough surface comparing
    several hypothetical feature sets ("starter add-ons vs pro add-ons
    vs enterprise add-ons") hydrates the LIVE-grant column off ONE
    round-trip instead of N calls to ``/has-features``.

    POST rather than GET because the caller-supplied set of bundles can
    grow past a comfortable query-string length; the sibling singular
    endpoint uses GET+CSV where the bundle is small.

    Request body::

        {
          "bundles": [
            ["fleet", "sso"],
            ["otel_export"],
            []
          ]
        }

    A shorthand ``{"bundles": ["fleet", "sso"]}`` (bare list of strings)
    is treated as ONE bundle, matching the singular endpoint's bare-CSV
    posture; a missing / non-list ``bundles`` value is a 400. An empty
    ``bundles=[]`` list is a 400 for the same reason the singular
    endpoint 400s on an empty ``features=`` -- distinguishes "caller
    asked for nothing" from "caller asked and every token was unknown".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` is byte-stable across every input branch::

        {
          "features":     ["fleet", "sso"],
          "unknown":      ["bogus"],
          "kind":         "features",
          "count":        2,
          "has_features": <bool>,
        }

    Per-bundle normalisation matches the singular endpoint: whitespace
    stripped, lowercased, deduplicated preserving first-seen order;
    unknown ids bucketed into the per-bundle ``unknown`` list instead
    of mis-collapsing the fold. Any unknown token collapses that row's
    ``has_features`` to ``False`` (inherits the singular typo-catches-
    at-callsite posture). Empty / all-unknown bundles surface as a
    stable row with ``has_features=False`` (does NOT short-circuit the
    batch).

    - **400** when ``bundles`` is missing / non-list / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the paywall matrix keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.has_features_bundle_batch(bundles)
        out_rows = [_shared._has_bundle_row_body(row, "features") for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-runtimes-bundle-batch",
    methods=["POST"],
)
def api_entitlement_has_runtimes_bundle_batch():
    """``POST /api/entitlement/has-runtimes-bundle-batch`` -- runtime-
    axis twin of ``/api/entitlement/has-features-bundle-batch``.

    Same never-5xx posture, same partial-unknown bucketing, same POST
    envelope. Runtime aliases (``claude-code`` -> ``claude_code``) are
    canonicalised per bundle through
    :func:`clawmetry.entitlements.canonical_runtime` so a caller does
    not need to normalise before calling; unknown ids land in the per-
    bundle ``unknown`` and collapse that row's ``has_runtimes`` to
    ``False`` (a typo does NOT silently render "granted" even in
    grace).

    Request body::

        {
          "bundles": [
            ["claude_code", "codex"],
            ["openclaw"],
            []
          ]
        }

    Response shape and error paths mirror
    ``/has-features-bundle-batch`` exactly, with ``kind="runtimes"``,
    a ``runtimes`` list in place of ``features``, and ``has_runtimes``
    in place of ``has_features`` per row.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.has_runtimes_bundle_batch(bundles)
        out_rows = [_shared._has_bundle_row_body(row, "runtimes") for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-features-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_has_features_bundle_batch_at():
    """``POST /api/entitlement/has-features-bundle-batch-at?tier=<perspective>``
    -- hypothetical-perspective sibling of
    ``/api/entitlement/has-features-bundle-batch``.

    Wraps :func:`clawmetry.entitlements.has_features_bundle_batch_at`
    so a pricing-matrix walkthrough can call the per-bundle boolean-
    fold batch on the feature axis from any tier's perspective without
    first switching the resolver. Fills the ``_at`` slot for the
    feature-axis bundle-batch family alongside the aggregate
    ``/has-all-bundle-batch-at`` and the runtime-axis sibling
    ``/has-runtimes-bundle-batch-at``.

    **Perspective-shaped** (grace-independent by design): each row's
    ``has_features_at`` delegates to
    :func:`clawmetry.entitlements.has_features_at` (backed by the
    static per-tier grant table via
    :func:`clawmetry.entitlements._hypothetical_entitlement`), so grace
    vs enforce yields byte-identical row bodies (only the resolver
    envelope shifts). Whole point of the ``_at`` slot: at
    ``tier=oss`` a paid-feature bundle reports ``has_features_at=false``
    even in grace, whereas the LIVE ``/has-features-bundle-batch``
    reports ``has_features=true`` for the same bundle via grace pass-
    through.

    Request body is byte-identical to ``/has-features-bundle-batch``.
    The extra ``tier=<perspective>`` query arg is required.

    Response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the bare batch envelope so a
    caller can render "from <perspective> this bundle would be locked"
    copy off one call::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "bundles":                [<row>, ...],
          "count":                  <int>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    Each ``<row>`` mirrors the LIVE ``/has-features-bundle-batch`` row
    body byte-for-byte on the axis echo slots with the fold slot
    renamed ``has_features_at``::

        {
          "features":        ["fleet", "sso"],
          "unknown":         ["bogus"],
          "kind":            "features",
          "count":           2,
          "has_features_at": <bool>,
        }

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so a
      caller can render the right "unknown tier" message)
    - **400** when ``bundles`` is missing / non-list / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall matrix keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.has_features_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._has_bundle_row_at_body(row, "features") for row in rows]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": out_rows,
                "count": len(out_rows),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_bundle_batch_at: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": [],
                "count": 0,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-runtimes-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_has_runtimes_bundle_batch_at():
    """``POST /api/entitlement/has-runtimes-bundle-batch-at?tier=<perspective>``
    -- runtime-axis twin of
    ``/api/entitlement/has-features-bundle-batch-at``.

    Wraps :func:`clawmetry.entitlements.has_runtimes_bundle_batch_at`
    so a pricing-matrix walkthrough can call the per-bundle boolean-
    fold batch on the runtime axis from any tier's perspective without
    first switching the resolver. Pairs with
    ``/has-features-bundle-batch-at`` the same way
    ``/has-runtimes-bundle-batch`` pairs with
    ``/has-features-bundle-batch`` on the LIVE seat: together the two
    perspective-scoped bundle-batch endpoints let a caller render "from
    <perspective>, does this whole runtime set land granted?" copy off
    ONE call per axis instead of N calls to
    ``/has-runtime-at`` / ``/has-runtimes-at``.

    Response shape and error paths mirror
    ``/has-features-bundle-batch-at`` exactly, with ``kind="runtimes"``,
    a ``runtimes`` list in place of ``features``, and
    ``has_runtimes_at`` in place of ``has_features_at`` per row.
    Runtime aliases (``claude-code`` -> ``claude_code``) canonicalise
    per bundle inside the helper before the ``ALL_RUNTIMES`` membership
    check, matching the LIVE ``/has-runtimes-bundle-batch`` alias
    posture byte-for-byte.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.has_runtimes_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._has_bundle_row_at_body(row, "runtimes") for row in rows]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": out_rows,
                "count": len(out_rows),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_bundle_batch_at: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": [],
                "count": 0,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-features-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_missing_features_bundle_batch_at():
    """``POST /api/entitlement/missing-features-bundle-batch-at?tier=<perspective>``
    -- hypothetical-perspective row-detail sibling of
    ``/api/entitlement/missing-features-bundle-batch``.

    Wraps :func:`clawmetry.entitlements.missing_features_bundle_batch_at`
    so a pricing-matrix walkthrough can call the per-bundle row-detail
    denial batch on the feature axis from any tier's perspective without
    first switching the resolver. Fills the ``_at`` slot on the feature-
    axis row-detail bundle-batch family alongside the aggregate
    ``/missing-all-bundle-batch-at`` and the runtime-axis sibling
    ``/missing-runtimes-bundle-batch-at``. Row-detail complement of the
    boolean-fold ``/has-features-bundle-batch-at`` on the same
    perspective seat -- the two responses pair on the same ``features``
    / ``unknown`` / ``kind`` / ``count`` axes so a UI can render "would
    <perspective> grant this bundle? / which items would still be locked
    at <perspective>?" side by side per bundle off two calls.

    **Perspective-shaped** (grace-independent by design): each row's
    ``missing_features_at`` delegates to
    :func:`clawmetry.entitlements.missing_features_at` (backed by the
    static per-tier grant table via
    :func:`clawmetry.entitlements._hypothetical_entitlement`), so grace
    vs enforce yields byte-identical row bodies (only the resolver
    envelope shifts). Whole point of the ``_at`` slot: at
    ``tier=oss`` a paid-feature bundle reports
    ``missing_features_at=["fleet"]`` even in grace, whereas the LIVE
    ``/missing-features-bundle-batch`` reports ``missing=[]`` for the
    same bundle via grace pass-through.

    Request body is byte-identical to ``/missing-features-bundle-batch``.
    The extra ``tier=<perspective>`` query arg is required.

    Response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the bare batch envelope so a
    caller can render "at <perspective> these items would be locked"
    copy off one call::

        {
          "perspective_tier":       "oss",
          "perspective_tier_label": "OSS",
          "perspective_tier_rank":  <int>,
          "bundles":                [<row>, ...],
          "count":                  <int>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    Each ``<row>`` mirrors the LIVE ``/missing-features-bundle-batch``
    row body byte-for-byte on the axis-echo slots with the fold slot
    renamed ``missing_features_at``::

        {
          "features":            ["fleet", "sso"],
          "unknown":             ["bogus"],
          "kind":                "features",
          "count":               2,
          "missing_features_at": [<subset denied at perspective>],
        }

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so a
      caller can render the right "unknown tier" message)
    - **400** when ``bundles`` is missing / non-list / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall matrix keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.missing_features_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._missing_bundle_row_at_body(row, "features") for row in rows]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": out_rows,
                "count": len(out_rows),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_bundle_batch_at: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": [],
                "count": 0,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-runtimes-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_missing_runtimes_bundle_batch_at():
    """``POST /api/entitlement/missing-runtimes-bundle-batch-at?tier=<perspective>``
    -- runtime-axis twin of
    ``/api/entitlement/missing-features-bundle-batch-at``.

    Wraps :func:`clawmetry.entitlements.missing_runtimes_bundle_batch_at`
    so a pricing-matrix walkthrough can call the per-bundle row-detail
    denial batch on the runtime axis from any tier's perspective without
    first switching the resolver. Pairs with
    ``/missing-features-bundle-batch-at`` the same way
    ``/missing-runtimes-bundle-batch`` pairs with
    ``/missing-features-bundle-batch`` on the LIVE seat: together the
    two perspective-scoped row-detail bundle-batch endpoints let a
    caller render "from <perspective>, WHICH items of this whole runtime
    set would still be locked?" copy off ONE call per axis instead of N
    calls to ``/missing-runtime-at`` / ``/missing-runtimes-at``.

    Response shape and error paths mirror
    ``/missing-features-bundle-batch-at`` exactly, with
    ``kind="runtimes"``, a ``runtimes`` list in place of ``features``,
    and ``missing_runtimes_at`` in place of ``missing_features_at`` per
    row. Runtime aliases (``claude-code`` -> ``claude_code``)
    canonicalise per bundle inside the helper before the
    ``ALL_RUNTIMES`` membership check, matching the LIVE
    ``/missing-runtimes-bundle-batch`` alias posture byte-for-byte -- an
    alias input surfaces as its canonical id in ``runtimes`` (and, if
    denied at ``perspective_tier``, in ``missing_runtimes_at``) rather
    than in ``unknown``.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.missing_runtimes_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._missing_bundle_row_at_body(row, "runtimes") for row in rows]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": out_rows,
                "count": len(out_rows),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_bundle_batch_at: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                **env,
                "bundles": [],
                "count": 0,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/required-tier-bundle-batch",
    methods=["POST"],
)
def api_entitlement_required_tier_bundle_batch():
    """``POST /api/entitlement/required-tier-bundle-batch`` -- bundle-axis
    batch sibling of ``/api/entitlement/required-tier-batch``.

    Where the singular ``/required-tier-batch`` folds ONE aggregate 5-
    axis bundle (features + runtimes + channels + retention + nodes)
    to ONE ``required_tier``, this folds N caller-supplied aggregate
    bundles to N ``required_tier`` rows in ONE round-trip. Distinct from
    ``/min-tier-for-features-batch`` and ``/min-tier-for-runtimes-batch``
    (which batch N *single-axis* bundles): each row here spans the same
    five axes ``/required-tier-batch`` does, so a pricing-matrix or
    upgrade-walkthrough surface comparing several hypothetical *whole*
    configs ("Starter-shaped install vs Pro-shaped install vs
    Enterprise-shaped install") renders off one call instead of N calls
    to ``/required-tier-batch``.

    POST rather than GET because each bundle already carries five axes
    and N of them can grow well past a comfortable query-string length;
    the sibling singular endpoint uses GET+CSV where the input is small.

    Request body::

        {
          "bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
            {}
          ]
        }

    A shorthand ``{"bundles": {"features": ["fleet"]}}`` (a bare dict)
    is treated as ONE bundle for symmetry with the list-of-strings
    shorthand on ``/min-tier-for-features-batch``; a missing /
    non-list-non-dict ``bundles`` value is a 400. An empty
    ``bundles=[]`` list is a 400 for the same reason
    ``/min-tier-for-features-batch`` 400s on an empty ``bundles`` --
    distinguishes "caller asked for nothing" from "caller asked and
    every axis was empty".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` mirrors the ``/required-tier-batch`` endpoint body
    minus the resolver envelope::

        {
          "features":            ["fleet"],
          "runtimes":            ["claude_code"],
          "channels":            5 | null,
          "retention_days":      30 | null,
          "nodes":               2 | null,
          "required_tier":       "pro" | null,
          "required_tier_label": "Pro" | null,
          "required_tier_rank":  <int>,   # -1 when required_tier is null
          "free":                <bool>,
        }

    Per-bundle normalisation matches the singular endpoint: CSV
    normalisation on ``features`` / ``runtimes`` (whitespace stripped,
    lowercased, deduplicated preserving first-seen order); runtime
    aliases (``claude-code`` -> ``claude_code``) canonicalised; the
    three capacity axes coerced through ``int(...)`` with a blank /
    non-int collapsing to ``null`` so a typo cannot silently mis-route
    the aggregate to Enterprise. Critically, ``retention_days=null``
    here means *unset*, NOT *unlimited* -- matches every other batch
    endpoint's posture.

    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the pricing surface keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.min_tier_for_all_batch(bundles)
        out_rows = [_shared._min_tier_for_all_row_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_required_tier_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/required-tier-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_required_tier_bundle_batch_at():
    """``POST /api/entitlement/required-tier-bundle-batch-at?tier=<perspective>``
    -- hypothetical-perspective sibling of
    ``/api/entitlement/required-tier-bundle-batch``.

    Wraps :func:`clawmetry.entitlements.min_tier_for_all_at_batch` so a
    pricing-matrix walkthrough can call the aggregate bundle-batch from
    any tier's perspective without first switching the resolver. Fills
    the ``_at`` slot for the aggregate bundle-batch family alongside the
    per-single-axis ``_at_batch`` siblings so a caller can call
    ``X_at_batch(perspective, bundles)`` uniformly across every ``_at``
    family. Perspective is validated against
    :data:`entitlements._TIER_ORDER` (including ``trial``) but does NOT
    shape rows -- the per-row fold walks the static per-tier caps, so
    grace vs enforce yields byte-identical row bodies (only the
    ``perspective_tier`` / ``current_tier`` envelope shifts).

    Request body is byte-identical to
    ``/required-tier-bundle-batch``. The extra ``tier=<perspective>``
    query arg is required.

    Response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the bare batch envelope so a
    caller can render "from <perspective> this bundle needs Pro" copy
    off one call.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so a
      caller can render the right "unknown tier" message)
    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the pricing surface keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.min_tier_for_all_at_batch(tier_in, bundles) or []
        out_rows = [_shared._min_tier_for_all_row_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_required_tier_bundle_batch_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle",
    methods=["POST"],
)
def api_entitlement_has_all_bundle():
    """``POST /api/entitlement/has-all-bundle`` -- singular row-detail
    scalar sibling of ``/api/entitlement/has-all-bundle-batch``.

    Folds ONE caller-supplied aggregate 5-axis bundle
    (``features + runtimes + channels + retention_days + nodes``) to
    the canonical batch-row shape at the LIVE resolver in one
    round-trip so a paywall walkthrough tile rendering one bundle
    cell at a time (an upgrade-walkthrough carousel, a "does this
    hypothetical config land granted?" diagnostics popover) reads the
    row without wrapping in a length-one list and unwrapping ``[0]``
    from ``/has-all-bundle-batch``.

    Distinct from the singular ``/api/entitlement/has-all`` GET
    endpoint (whose 19-key diagnostic envelope carries unknown-token
    splits, ``required_tier`` resolution, and the ``upgrade_required``
    rollup): this returns the stripped six-key batch-row shape so a UI
    wiring the singular and the batch off the same helper sees
    byte-identical rows. Post-tier switch or grace flip the two
    endpoints stay in lockstep because :func:`has_all_bundle` delegates
    to the same :func:`_has_all_bundle_row` helper as the batch.

    POST rather than GET so the request body is byte-identical to the
    batch endpoint's per-row shape -- a caller with a single bundle in
    hand can POST it as-is without stitching a CSV query string.

    Request body::

        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
                    "channels": 5, "retention_days": 30, "nodes": 2}}

    A shorthand where the top-level body IS the bundle
    (``{"features": ["fleet"]}``) is also accepted so the same body the
    ``/has-all`` GET endpoint takes as query args maps 1:1 to a POST
    body. Missing / non-object ``bundle`` value is a 400.

    Response layers the resolver envelope on top of the batch-row
    shape (byte-identical to the batch's per-row body plus the
    envelope so a caller can render "on <tier>, is this granted?"
    without a second call)::

        {
          "features":          ["fleet"],
          "runtimes":          ["claude_code"],
          "channels":          5 | null,
          "retention_days":    30 | null,
          "nodes":             2 | null,
          "has_all":           <bool>,
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    - **400** when ``bundle`` is missing / non-object.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty row shape with ``has_all=false``) so the paywall tile
      keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    try:
        from clawmetry import entitlements as _ent

        row = _ent.has_all_bundle(bundle)
        out = _shared._has_all_bundle_row_to_body(row)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify({**out, **env})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_bundle: error: %s", exc)
        return _shared.jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "has_all": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-at",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_at():
    """``POST /api/entitlement/has-all-bundle-at?tier=<perspective>`` --
    hypothetical-perspective sibling of
    ``/api/entitlement/has-all-bundle``.

    Wraps :func:`clawmetry.entitlements.has_all_bundle_at` so a
    pricing-matrix or upgrade-walkthrough tile can call the aggregate
    boolean-fold singular from any tier's perspective without first
    switching the resolver. Fills the ``_at`` slot for the singular
    aggregate-bundle boolean-fold family alongside the batch
    ``/has-all-bundle-batch-at`` and the ``_at`` siblings of the
    per-single-axis bundle helpers so a caller can call the
    perspective-scoped singular uniformly across every ``_at`` family.

    Grace-independent by construction: :func:`has_all_bundle_at` reads
    from the static per-tier grant tables via
    :func:`_hypothetical_entitlement` on the feature / runtime axes and
    :data:`_TIER_CHANNEL_LIMIT` / :data:`_TIER_RETENTION_DAYS` /
    :data:`_TIER_NODE_LIMIT` on the capacity axes, so the row body is
    byte-identical under grace vs enforce for the same
    ``(perspective, bundle)`` pair. Whole point of the ``_at`` slot: at
    ``tier=oss`` a paid-feature bundle reports ``has_all_at=false`` even
    in grace, whereas the LIVE ``/has-all-bundle`` reports
    ``has_all=true`` for the same bundle via grace pass-through.

    Request body is byte-identical to ``/has-all-bundle``. The extra
    ``tier=<perspective>`` query arg is required.

    Response layers ``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank`` on top of
    the singular row body with the fold slot renamed ``has_all_at``::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "features":               ["fleet"],
          "runtimes":               ["claude_code"],
          "channels":               5 | null,
          "retention_days":         30 | null,
          "nodes":                  2 | null,
          "has_all_at":             <bool>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so
      a caller can render the right "unknown tier" message).
    - **400** when ``bundle`` is missing / non-object.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall matrix keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        row = _ent.has_all_bundle_at(tier_in, bundle) or {
            "features": [],
            "runtimes": [],
            "channels": None,
            "retention_days": None,
            "nodes": None,
            "has_all_at": False,
        }
        out = _shared._has_all_bundle_row_at_to_body(row)
        env = _shared._resolver_envelope(_ent)
        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": label,
                "perspective_tier_rank": rank,
                **out,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_bundle_at: error: %s", exc)
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
                "has_all_at": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-at-path",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_at_path():
    """``POST /api/entitlement/has-all-bundle-at-path?from=<id>&to=<id>``
    -- path-shaped bundle sibling of
    ``/api/entitlement/has-all-bundle-at`` (singular perspective) and
    bundle-shaped counterpart of ``/api/entitlement/has-all-at-path``
    (kwargs-shaped path walker).

    Wraps :func:`clawmetry.entitlements.has_all_bundle_at_path` so a
    pricing-matrix or upgrade-walkthrough tooltip can render "at which
    rung does this WHOLE 5-axis bundle unlock?" straight from the
    bundle dict off ONE round-trip instead of first normalising the
    bundle by hand and calling ``/has-all-at-path``, or first calling
    ``/tier-path`` and then N calls to ``/has-all-bundle-at``.

    Fills the ``_at_path`` slot on the aggregate bundle boolean-fold
    family alongside :func:`has_all_bundle_at` (singular perspective),
    ``/has-all-bundle-batch-at`` (multi-bundle perspective batch), and
    ``/has-all-at-path`` (kwargs-shaped path walker).

    Request body is byte-identical to ``/has-all-bundle-at``:
    ``{"bundle": {"features": [...], "runtimes": [...], "channels": N,
    "retention_days": N, "nodes": N}}`` -- or the bare-dict shorthand.
    ``from`` and ``to`` are required query args.

    Each row in ``path`` byte-equals the scalar
    :func:`clawmetry.entitlements.has_all_bundle_at_path` return with
    the standard ``_at_path`` per-rung header:
    ``{tier, tier_label, tier_rank, features, runtimes, channels,
    retention_days, nodes, has_all_at}``. Each rung's ``has_all_at``
    byte-equals ``/has-all-bundle-at?tier=<rung>`` for the same
    (rung, bundle) pair.

    Rung walk is byte-stable against ``/tier-path``,
    ``/has-features-at-path``, ``/has-runtimes-at-path``,
    ``/missing-features-at-path``, ``/missing-runtimes-at-path``,
    ``/has-all-at-path``, and ``/missing-all-at-path`` (same
    :data:`_PURCHASABLE_TIERS` filter + same sort + same destination-
    sibling exclusion). ``direction`` values: ``upgrade`` | ``downgrade``
    | ``lateral`` | ``identity`` | ``unknown``.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (read the static per-tier tables via
    :func:`_has_all_bundle_row_at`, not the resolver's ``grace`` bit).

    - **400** when ``bundle`` is missing / non-object.
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``from`` / ``to`` returns 200 with ``path=[]`` (``direction``
      reads ``"unknown"``); same posture as ``/has-all-at-path``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_has_all_bundle_at_path_fallback`) with ``path=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_from = _shared.request.args.get("from")
    raw_to = _shared.request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        path = _ent.has_all_bundle_at_path(from_tier, to_tier, bundle)
        env = _shared._resolver_envelope(_ent)
        if path is None:
            direction = "unknown"
            path_out: list = []
            from_label = None
            to_label = None
            from_rank = -1
            to_rank = -1
            features_echo: list = []
            runtimes_echo: list = []
            channels_echo = None
            retention_echo = None
            nodes_echo = None
        else:
            path_out = []
            for row in path:
                try:
                    tid = row.get("tier")
                except AttributeError:
                    continue
                path_out.append(
                    {
                        "tier": tid,
                        "tier_label": row.get(
                            "tier_label", _ent.tier_label(tid)
                        ),
                        "tier_rank": row.get(
                            "tier_rank", _ent.tier_rank(tid)
                        ),
                        **_shared._has_all_bundle_row_at_to_body(row),
                    }
                )
            from_rank = _ent.tier_rank(from_tier)
            to_rank = _ent.tier_rank(to_tier)
            from_label = _ent.tier_label(from_tier)
            to_label = _ent.tier_label(to_tier)
            if from_tier == to_tier:
                direction = "identity"
            elif from_rank == to_rank:
                direction = "lateral"
            elif to_rank > from_rank:
                direction = "upgrade"
            else:
                direction = "downgrade"

            # Bundle-shape axis echo at the envelope level: mirror the
            # normalised bundle so a caller sees exactly what the scalar
            # folded, independent of the per-rung echo. Read from the
            # first row (bundle normalisation is per-scalar not per-rung,
            # so every row's echo is byte-identical) and fall back to an
            # empty echo on an empty path.
            if path_out:
                head = path_out[0]
                features_echo = list(head.get("features") or [])
                runtimes_echo = list(head.get("runtimes") or [])
                channels_echo = head.get("channels")
                retention_echo = head.get("retention_days")
                nodes_echo = head.get("nodes")
            else:
                # Identity / cross-rung-empty branch: normalise the bundle
                # directly so the envelope-level axis echo still reflects
                # the caller-supplied bundle even when no rungs were walked.
                (
                    features_echo,
                    runtimes_echo,
                    channels_echo,
                    retention_echo,
                    nodes_echo,
                ) = _ent._normalise_all_bundle(bundle)

        allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
        all_allowed = bool(path_out) and all(
            r.get("has_all_at") for r in path_out
        )
        any_allowed = any(r.get("has_all_at") for r in path_out)

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": from_label,
                "from_rank": from_rank,
                "to": to_tier,
                "to_label": to_label,
                "to_rank": to_rank,
                "direction": direction,
                "features": features_echo,
                "runtimes": runtimes_echo,
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "path": path_out,
                "path_length": len(path_out),
                "allowed_count": allowed_count,
                "all_allowed": all_allowed,
                "any_allowed": any_allowed,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_at_path: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_bundle_at_path_fallback(from_tier, to_tier)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-at-path",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_at_path():
    """``POST /api/entitlement/missing-all-bundle-at-path?from=<id>&to=<id>``
    -- row-detail path-shaped bundle sibling of the boolean-fold
    ``/api/entitlement/has-all-bundle-at-path`` and bundle-shaped
    counterpart of ``/api/entitlement/missing-all-at-path``
    (kwargs-shaped path walker).

    Wraps :func:`clawmetry.entitlements.missing_all_bundle_at_path` so a
    pricing-matrix or upgrade-walkthrough tooltip can render "at which
    rung does each per-axis slot in this 5-axis bundle clear?" straight
    from the bundle dict off ONE round-trip instead of first
    normalising the bundle by hand and calling ``/missing-all-at-path``,
    or first calling ``/tier-path`` and then N calls to the singular
    row-detail per-perspective seat.

    Request body is byte-identical to ``/has-all-bundle-at-path``:
    ``{"bundle": {"features": [...], "runtimes": [...], "channels": N,
    "retention_days": N, "nodes": N}}`` -- or the bare-dict shorthand.
    ``from`` and ``to`` are required query args.

    Each row in ``path`` byte-equals the scalar
    :func:`clawmetry.entitlements.missing_all_bundle_at_path` return
    with the standard ``_at_path`` per-rung header:
    ``{tier, tier_label, tier_rank, features, runtimes, channels,
    retention_days, nodes, missing: {features, runtimes, channels,
    retention_days, nodes}}``.

    Rung walk is byte-stable against ``/tier-path``,
    ``/has-features-at-path``, ``/has-runtimes-at-path``,
    ``/missing-features-at-path``, ``/missing-runtimes-at-path``,
    ``/has-all-at-path``, ``/missing-all-at-path`` and
    ``/has-all-bundle-at-path`` (same :data:`_PURCHASABLE_TIERS`
    filter + same sort + same destination-sibling exclusion).
    ``direction`` values: ``upgrade`` | ``downgrade`` | ``lateral`` |
    ``identity`` | ``unknown``.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (read the static per-tier tables via
    :func:`_missing_all_bundle_row_at`, not the resolver's ``grace``
    bit).

    Complement invariant with ``/has-all-bundle-at-path``: per rung,
    ``any(row["missing"].values())`` byte-equals ``not row["has_all_at"]``
    on the paired boolean-fold row for every fully-parseable bundle.

    - **400** when ``bundle`` is missing / non-object.
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``from`` / ``to`` returns 200 with ``path=[]`` (``direction``
      reads ``"unknown"``); same posture as ``/missing-all-at-path``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_missing_all_bundle_at_path_fallback`) with ``path=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_from = _shared.request.args.get("from")
    raw_to = _shared.request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        path = _ent.missing_all_bundle_at_path(from_tier, to_tier, bundle)
        env = _shared._resolver_envelope(_ent)
        if path is None:
            direction = "unknown"
            path_out: list = []
            from_label = None
            to_label = None
            from_rank = -1
            to_rank = -1
            features_echo: list = []
            runtimes_echo: list = []
            channels_echo = None
            retention_echo = None
            nodes_echo = None
        else:
            path_out = []
            for row in path:
                try:
                    tid = row.get("tier")
                except AttributeError:
                    continue
                path_out.append(
                    {
                        "tier": tid,
                        "tier_label": row.get(
                            "tier_label", _ent.tier_label(tid)
                        ),
                        "tier_rank": row.get(
                            "tier_rank", _ent.tier_rank(tid)
                        ),
                        **_shared._missing_all_bundle_row_at_to_body(row),
                    }
                )
            from_rank = _ent.tier_rank(from_tier)
            to_rank = _ent.tier_rank(to_tier)
            from_label = _ent.tier_label(from_tier)
            to_label = _ent.tier_label(to_tier)
            if from_tier == to_tier:
                direction = "identity"
            elif from_rank == to_rank:
                direction = "lateral"
            elif to_rank > from_rank:
                direction = "upgrade"
            else:
                direction = "downgrade"

            if path_out:
                head = path_out[0]
                features_echo = list(head.get("features") or [])
                runtimes_echo = list(head.get("runtimes") or [])
                channels_echo = head.get("channels")
                retention_echo = head.get("retention_days")
                nodes_echo = head.get("nodes")
            else:
                (
                    features_echo,
                    runtimes_echo,
                    channels_echo,
                    retention_echo,
                    nodes_echo,
                ) = _ent._normalise_all_bundle(bundle)

        def _row_any_denied(row) -> bool:
            m = row.get("missing") or {}
            for k, v in m.items():
                if isinstance(v, list):
                    if v:
                        return True
                elif v is not None:
                    return True
            return False

        denied_count = sum(1 for r in path_out if _row_any_denied(r))
        all_denied = bool(path_out) and all(
            _row_any_denied(r) for r in path_out
        )
        any_denied = any(_row_any_denied(r) for r in path_out)

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": from_label,
                "from_rank": from_rank,
                "to": to_tier,
                "to_label": to_label,
                "to_rank": to_rank,
                "direction": direction,
                "features": features_echo,
                "runtimes": runtimes_echo,
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "path": path_out,
                "path_length": len(path_out),
                "denied_count": denied_count,
                "all_denied": all_denied,
                "any_denied": any_denied,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_at_path: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_all_bundle_at_path_fallback(from_tier, to_tier)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-at-path-batch",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_at_path_batch():
    """``POST /api/entitlement/has-all-bundle-at-path-batch?from=<id>&to=a,b,c``
    -- bundle-shaped batch-path sibling of
    ``/api/entitlement/has-all-bundle-at-path`` (singular destination)
    and bundle-shaped counterpart of
    ``/api/entitlement/has-all-at-path-batch`` (kwargs-shaped batch-
    path).

    Wraps :func:`clawmetry.entitlements.has_all_bundle_at_path_batch`
    so a pricing-matrix or upgrade-walkthrough tooltip can render
    "from my current rung, here are 3 tiers I'm considering: for this
    WHOLE 5-axis bundle dict show me at which rung this bundle unlocks
    along every candidate path" straight from the bundle dict off ONE
    round-trip instead of normalising the bundle by hand and calling
    ``/has-all-at-path-batch``, or N calls to
    ``/has-all-bundle-at-path``.

    Fills the ``_at_path_batch`` slot on the aggregate bundle boolean-
    fold family alongside ``/has-all-bundle-at-path`` (singular
    destination), ``/has-all-bundle-batch-at`` (multi-bundle
    perspective batch), and ``/has-all-at-path-batch`` (kwargs-shaped
    batch-path).

    Request body is byte-identical to ``/has-all-bundle-at-path``:
    ``{"bundle": {"features": [...], "runtimes": [...], "channels": N,
    "retention_days": N, "nodes": N}}`` -- or the bare-dict shorthand.
    ``from`` and ``to`` (CSV) are required query args.

    Response envelope (byte-stable across every input branch)::

        {
          "from":               "<tier id>",
          "from_label":         "..." | null,
          "from_rank":          <int>,
          "features":           [<echo>],
          "runtimes":           [<echo>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_tiers":      [...],
          "tiers": [
            {
              "to":            "<id>",
              "to_label":      "...",
              "to_rank":       <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_all_bundle_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,
              "all_allowed":   <bool>,
              "any_allowed":   <bool>,
            },
            ...
          ],
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/has-all-bundle-at-path?from=<from>&to=<to>``'s ``.path`` for the
    same triple -- pinned by the parity tests so the singular and batch
    bundle-shaped what-if boolean-fold path helpers cannot drift. Per-
    destination path lengths can legitimately differ (the rungs walked
    depend on the destination), matching
    ``/has-all-at-path-batch`` posture. ``trial`` IS accepted as a
    destination (excluded from the walked intermediate rungs the way
    ``/has-all-bundle-at-path`` already excludes it, but is a valid
    endpoint via the lateral / identity branches).

    Bundle normalisation semantics per rung per destination inherit
    ``/has-all-bundle-at-path`` byte-for-byte (via
    :func:`clawmetry.entitlements._normalise_all_bundle` +
    :func:`_has_all_bundle_row_at`):

    * Bare-dict shorthand accepted; missing / non-object ``bundle`` is
      a 400.
    * ``bundle={}`` (empty) collapses every rung of every destination
      to ``has_all_at=false`` (no axis supplied, singular
      :func:`has_all_at` collapses).
    * Runtime alias canonicalisation (``claude-code`` ->
      ``claude_code``) applied per-token; alias-and-canonical pair
      dedups to one entry on the echo.
    * Unknown runtime id dropped by normalisation. Unknown feature id
      survives normalisation and collapses every rung's fold to
      ``false``.
    * Non-int capacity value collapses to ``null`` on the echo AND
      drops from the fold.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (read the static per-tier tables via
    :func:`has_all_bundle_at_path_batch`'s per-rung
    :func:`_has_all_bundle_row_at` delegation, not the resolver's
    ``grace`` bit).

    Envelope-level axis echo mirrors the normalised bundle so a caller
    sees exactly what the scalar folded, independent of the per-rung
    echo. Reads from the first non-empty row (bundle normalisation is
    per-scalar not per-rung, so every row's echo is byte-identical
    within a destination and byte-identical across destinations); falls
    back to :func:`_normalise_all_bundle` directly when every path is
    empty (identity / cross-rung-empty branch) so the envelope-level
    echo still reflects the caller-supplied bundle even when no rungs
    were walked.

    - **400** when ``bundle`` is missing / non-object.
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``from``, or empty / all-unknown ``to`` CSV -> 200 with
      ``tiers=[]`` (matches ``/has-all-at-path-batch`` posture -- a
      pricing-comparison matrix binds ``tiers`` directly without a
      pre-validation round-trip).
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_has_all_bundle_at_path_batch_fallback`) with
      ``tiers=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_from = _shared.request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _shared._parse_csv_arg("to")
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.has_all_bundle_at_path_batch(
            from_tier, to_tokens, bundle
        )
        env = _shared._resolver_envelope(_ent)

        # Envelope-level axis echo: derive from the first available
        # per-rung row so the envelope reflects exactly what the scalar
        # folded. Bundle normalisation is per-scalar, not per-rung, so
        # every rung's echo is byte-identical within a destination and
        # byte-identical across destinations for the same bundle.
        features_echo: list = []
        runtimes_echo: list = []
        channels_echo = None
        retention_echo = None
        nodes_echo = None
        anchor = None
        if batch is not None:
            for row in batch.get("tiers", []) or []:
                for prow in row.get("path", []) or []:
                    anchor = prow
                    break
                if anchor is not None:
                    break
        if anchor is not None:
            features_echo = list(anchor.get("features") or [])
            runtimes_echo = list(anchor.get("runtimes") or [])
            channels_echo = anchor.get("channels")
            retention_echo = anchor.get("retention_days")
            nodes_echo = anchor.get("nodes")
        else:
            (
                features_echo,
                runtimes_echo,
                channels_echo,
                retention_echo,
                nodes_echo,
            ) = _ent._normalise_all_bundle(bundle)

        if batch is None:
            return _shared.jsonify(
                {
                    "from": from_tier,
                    "from_label": None,
                    "from_rank": -1,
                    "features": list(features_echo),
                    "runtimes": list(runtimes_echo),
                    "channels": channels_echo,
                    "retention_days": retention_echo,
                    "nodes": nodes_echo,
                    "unknown_tiers": list(to_tokens),
                    "tiers": [],
                    "current_tier": env["current_tier"],
                    "current_tier_rank": env["current_tier_rank"],
                    "grace": env["grace"],
                    "enforced": env["enforced"],
                }
            )

        tiers_out: list[dict] = []
        for row in batch.get("tiers", []) or []:
            try:
                path = list(row.get("path", []) or [])
            except AttributeError:
                continue
            path_out: list[dict] = []
            for prow in path:
                try:
                    tid = prow.get("tier")
                except AttributeError:
                    continue
                path_out.append(
                    {
                        "tier": tid,
                        "tier_label": prow.get(
                            "tier_label", _ent.tier_label(tid)
                        ),
                        "tier_rank": prow.get(
                            "tier_rank", _ent.tier_rank(tid)
                        ),
                        **_shared._has_all_bundle_row_at_to_body(prow),
                    }
                )
            allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
            all_allowed = bool(path_out) and all(
                r.get("has_all_at") for r in path_out
            )
            any_allowed = any(r.get("has_all_at") for r in path_out)
            tiers_out.append(
                {
                    "to": row.get("to"),
                    "to_label": row.get("to_label"),
                    "to_rank": row.get("to_rank", -1),
                    "direction": row.get("direction"),
                    "path": path_out,
                    "path_length": len(path_out),
                    "allowed_count": allowed_count,
                    "all_allowed": all_allowed,
                    "any_allowed": any_allowed,
                }
            )

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": _ent.tier_label(from_tier),
                "from_rank": _ent.tier_rank(from_tier),
                "features": list(features_echo),
                "runtimes": list(runtimes_echo),
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "unknown_tiers": list(batch.get("unknown", []) or []),
                "tiers": tiers_out,
                "current_tier": env["current_tier"],
                "current_tier_rank": env["current_tier_rank"],
                "grace": env["grace"],
                "enforced": env["enforced"],
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_bundle_at_path_batch_fallback(from_tier, to_tokens)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-at-path-batch",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_at_path_batch():
    """``POST /api/entitlement/missing-all-bundle-at-path-batch?from=<id>&to=a,b,c``
    -- row-detail bundle-shaped batch-path sibling of the boolean-fold
    ``/api/entitlement/has-all-bundle-at-path-batch``, bundle-shaped
    counterpart of ``/api/entitlement/missing-all-at-path-batch``
    (kwargs-shaped batch-path), and destination-batch sibling of
    ``/api/entitlement/missing-all-bundle-at-path`` (singular
    destination).

    Wraps :func:`clawmetry.entitlements.missing_all_bundle_at_path_batch`
    so a pricing-matrix or upgrade-walkthrough tooltip can render
    "from my current rung, here are 3 tiers I'm considering: for this
    WHOLE 5-axis bundle dict show me which per-axis slots are still
    locked at every rung climbed to reach each" straight from the
    bundle dict off ONE round-trip instead of normalising the bundle
    by hand and calling ``/missing-all-at-path-batch``, or N calls to
    ``/missing-all-bundle-at-path``.

    Request body is byte-identical to ``/missing-all-bundle-at-path``:
    ``{"bundle": {"features": [...], "runtimes": [...], "channels": N,
    "retention_days": N, "nodes": N}}`` -- or the bare-dict shorthand.
    ``from`` and ``to`` (CSV) are required query args.

    Response envelope mirrors ``/has-all-bundle-at-path-batch`` byte-
    for-byte on the axis-echo slots (byte-parity so a UI wiring both
    boolean-fold and row-detail matrices sees a consistent envelope)
    with the per-destination fold-rollup keys swapped
    (``denied_count`` / ``all_denied`` / ``any_denied`` in place of
    ``allowed_count`` / ``all_allowed`` / ``any_allowed``) and the per-
    rung row body swapped from the boolean-fold row to the row-detail
    row.

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/missing-all-bundle-at-path?from=<from>&to=<to>``'s ``.path`` for
    the same triple -- pinned by the parity tests so the singular and
    batch bundle-shaped what-if row-detail path helpers cannot drift.

    Complement invariant with ``/has-all-bundle-at-path-batch``: per
    destination per rung, ``any(row["missing"].values())`` byte-equals
    ``not row["has_all_at"]`` on the paired boolean-fold row for every
    fully-parseable bundle.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (read the static per-tier tables via
    :func:`missing_all_bundle_at_path_batch`'s per-rung
    :func:`_missing_all_bundle_row_at` delegation, not the resolver's
    ``grace`` bit).

    - **400** when ``bundle`` is missing / non-object.
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``from``, or empty / all-unknown ``to`` CSV -> 200 with
      ``tiers=[]``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_missing_all_bundle_at_path_batch_fallback`) with
      ``tiers=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_from = _shared.request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _shared._parse_csv_arg("to")
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.missing_all_bundle_at_path_batch(
            from_tier, to_tokens, bundle
        )
        env = _shared._resolver_envelope(_ent)

        features_echo: list = []
        runtimes_echo: list = []
        channels_echo = None
        retention_echo = None
        nodes_echo = None
        anchor = None
        if batch is not None:
            for row in batch.get("tiers", []) or []:
                for prow in row.get("path", []) or []:
                    anchor = prow
                    break
                if anchor is not None:
                    break
        if anchor is not None:
            features_echo = list(anchor.get("features") or [])
            runtimes_echo = list(anchor.get("runtimes") or [])
            channels_echo = anchor.get("channels")
            retention_echo = anchor.get("retention_days")
            nodes_echo = anchor.get("nodes")
        else:
            (
                features_echo,
                runtimes_echo,
                channels_echo,
                retention_echo,
                nodes_echo,
            ) = _ent._normalise_all_bundle(bundle)

        if batch is None:
            return _shared.jsonify(
                {
                    "from": from_tier,
                    "from_label": None,
                    "from_rank": -1,
                    "features": list(features_echo),
                    "runtimes": list(runtimes_echo),
                    "channels": channels_echo,
                    "retention_days": retention_echo,
                    "nodes": nodes_echo,
                    "unknown_tiers": list(to_tokens),
                    "tiers": [],
                    "current_tier": env["current_tier"],
                    "current_tier_rank": env["current_tier_rank"],
                    "grace": env["grace"],
                    "enforced": env["enforced"],
                }
            )

        def _row_any_denied(prow) -> bool:
            m = prow.get("missing") or {}
            for k, v in m.items():
                if isinstance(v, list):
                    if v:
                        return True
                elif v is not None:
                    return True
            return False

        tiers_out: list[dict] = []
        for row in batch.get("tiers", []) or []:
            try:
                path = list(row.get("path", []) or [])
            except AttributeError:
                continue
            path_out: list[dict] = []
            for prow in path:
                try:
                    tid = prow.get("tier")
                except AttributeError:
                    continue
                path_out.append(
                    {
                        "tier": tid,
                        "tier_label": prow.get(
                            "tier_label", _ent.tier_label(tid)
                        ),
                        "tier_rank": prow.get(
                            "tier_rank", _ent.tier_rank(tid)
                        ),
                        **_shared._missing_all_bundle_row_at_to_body(prow),
                    }
                )
            denied_count = sum(1 for r in path_out if _row_any_denied(r))
            all_denied = bool(path_out) and all(
                _row_any_denied(r) for r in path_out
            )
            any_denied = any(_row_any_denied(r) for r in path_out)
            tiers_out.append(
                {
                    "to": row.get("to"),
                    "to_label": row.get("to_label"),
                    "to_rank": row.get("to_rank", -1),
                    "direction": row.get("direction"),
                    "path": path_out,
                    "path_length": len(path_out),
                    "denied_count": denied_count,
                    "all_denied": all_denied,
                    "any_denied": any_denied,
                }
            )

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": _ent.tier_label(from_tier),
                "from_rank": _ent.tier_rank(from_tier),
                "features": list(features_echo),
                "runtimes": list(runtimes_echo),
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "unknown_tiers": list(batch.get("unknown", []) or []),
                "tiers": tiers_out,
                "current_tier": env["current_tier"],
                "current_tier_rank": env["current_tier_rank"],
                "grace": env["grace"],
                "enforced": env["enforced"],
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_all_bundle_at_path_batch_fallback(from_tier, to_tokens)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-batch-at-path",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_batch_at_path():
    """``POST /api/entitlement/has-all-bundle-batch-at-path?from=<id>&to=<id>``
    -- bundle-axis batch sibling of has-all-bundle-at-path.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    raw_from = _shared.request.args.get("from")
    raw_to = _shared.request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        cells = _ent.has_all_bundle_batch_at_path(
            from_tier, to_tier, bundles
        )
        env = _shared._resolver_envelope(_ent)
        if cells is None:
            direction = "unknown"
            out_cells: list = []
            from_label = None
            to_label = None
            from_rank = -1
            to_rank = -1
        else:
            out_cells = [
                _shared._bundle_batch_path_row_out(
                    cell, _shared._has_all_bundle_row_at_to_body, "has_all_at"
                )
                for cell in cells
            ]
            from_rank = _ent.tier_rank(from_tier)
            to_rank = _ent.tier_rank(to_tier)
            from_label = _ent.tier_label(from_tier)
            to_label = _ent.tier_label(to_tier)
            if from_tier == to_tier:
                direction = "identity"
            elif from_rank == to_rank:
                direction = "lateral"
            elif to_rank > from_rank:
                direction = "upgrade"
            else:
                direction = "downgrade"

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": from_label,
                "from_rank": from_rank,
                "to": to_tier,
                "to_label": to_label,
                "to_rank": to_rank,
                "direction": direction,
                "bundles": out_cells,
                "count": len(out_cells),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_batch_at_path: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_bundle_batch_at_path_fallback(from_tier, to_tier)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-batch-at-path",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_batch_at_path():
    """``POST /api/entitlement/missing-all-bundle-batch-at-path?from=<id>&to=<id>``
    -- row-detail bundle-axis batch sibling of missing-all-bundle-at-path.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    raw_from = _shared.request.args.get("from")
    raw_to = _shared.request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        cells = _ent.missing_all_bundle_batch_at_path(
            from_tier, to_tier, bundles
        )
        env = _shared._resolver_envelope(_ent)
        if cells is None:
            direction = "unknown"
            out_cells: list = []
            from_label = None
            to_label = None
            from_rank = -1
            to_rank = -1
        else:
            out_cells = [
                _shared._bundle_batch_path_row_out(
                    cell, _shared._missing_all_bundle_row_at_to_body, "missing"
                )
                for cell in cells
            ]
            from_rank = _ent.tier_rank(from_tier)
            to_rank = _ent.tier_rank(to_tier)
            from_label = _ent.tier_label(from_tier)
            to_label = _ent.tier_label(to_tier)
            if from_tier == to_tier:
                direction = "identity"
            elif from_rank == to_rank:
                direction = "lateral"
            elif to_rank > from_rank:
                direction = "upgrade"
            else:
                direction = "downgrade"

        return _shared.jsonify(
            {
                "from": from_tier,
                "from_label": from_label,
                "from_rank": from_rank,
                "to": to_tier,
                "to_label": to_label,
                "to_rank": to_rank,
                "direction": direction,
                "bundles": out_cells,
                "count": len(out_cells),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_batch_at_path: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_all_bundle_batch_at_path_fallback(from_tier, to_tier)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-from-path-batch",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_from_path_batch():
    """``POST /api/entitlement/has-all-bundle-from-path-batch?to=<id>``
    -- source-axis batch bundle-shaped sibling of
    ``/api/entitlement/has-all-bundle-at-path`` (singular source-path,
    one bundle) and bundle-shape twin of
    ``/api/entitlement/has-features-from-path-batch`` /
    ``/api/entitlement/has-runtimes-from-path-batch`` on the same
    source-batch seat.

    Wraps :func:`clawmetry.entitlements.has_all_bundle_from_path_batch`
    so a source-side upgrade-comparison surface can render "for each
    tier my fleet sits on today, does this whole 5-axis subscription
    state unlock at every rung climbed toward ``<to_tier>``?" straight
    from the bundle dict off ONE round-trip instead of N calls to
    ``/has-all-bundle-at-path``.

    Fills the ``_from_path_batch`` slot on the aggregate bundle
    boolean-fold family alongside ``/has-all-bundle-at`` (singular
    perspective), ``/has-all-bundle-batch-at`` (multi-bundle
    perspective batch), ``/has-all-bundle-at-path`` (singular source-
    path bundle), and the destination-axis
    ``/has-all-bundle-at-path-batch`` (PR #4884).

    Request body (canonical)::

        {"from_tiers": ["oss", "cloud_starter"],
         "bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
                    "channels": 5, "retention_days": 30, "nodes": 2}}

    Or bare-axis shorthand alongside ``from_tiers``::

        {"from_tiers": ["oss"], "features": ["fleet"]}

    ``to`` is a required query arg. Missing / blank / unknown ``to``
    returns 200 with ``tiers=[]`` (never 4xxs) -- matches the source-
    side ``/has-features-from-path-batch`` posture. Missing / empty
    ``from_tiers`` returns 200 with ``tiers=[]`` (nothing to fold).

    Envelope shape (byte-stable across every input branch)::

        {
          "to":                 "<tier id>",
          "to_label":           "...",
          "to_rank":            <int>,
          "features":           [<normalised features echo>],
          "runtimes":           [<normalised runtimes echo>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_tiers":      [<dropped source ids>],
          "count":              <int>,               # len(tiers)
          "tiers": [
            {
              "from":          "<id>",
              "from_label":    "...",
              "from_rank":     <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_all_bundle_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,                # rungs where fold=True
              "all_allowed":   <bool>,               # every rung True
              "any_allowed":   <bool>,               # any rung True
            },
            ...
          ],
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/has-all-bundle-at-path?from=<from>&to=<to>``'s ``.path`` for
    the same ``(from, to, bundle)`` triple -- a parity test pins this
    so the singular and source-batch bundle-shape path what-if
    boolean-fold helpers cannot drift.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (read the static per-tier tables via
    :func:`has_all_bundle_at_path`, not the resolver's ``grace`` bit).

    - **400** when ``bundle`` is missing / non-object (matches
      ``/has-all-bundle-at-path``'s 400 branch).
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``to`` returns 200 with ``tiers=[]`` (same posture as
      ``/has-features-from-path-batch``).
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_has_all_bundle_from_path_batch_fallback`) with
      ``tiers=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    from_tiers, bundle, err = _shared._parse_from_tiers_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_to = _shared.request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.has_all_bundle_from_path_batch(
            from_tiers, to_tier, bundle
        )
        env = _shared._resolver_envelope(_ent)
        (
            features_echo,
            runtimes_echo,
            channels_echo,
            retention_echo,
            nodes_echo,
        ) = _ent._normalise_all_bundle(bundle)
        if batch is None:
            return _shared.jsonify(
                {
                    "to": to_tier,
                    "to_label": None,
                    "to_rank": -1,
                    "features": features_echo,
                    "runtimes": runtimes_echo,
                    "channels": channels_echo,
                    "retention_days": retention_echo,
                    "nodes": nodes_echo,
                    "unknown_tiers": list(from_tiers),
                    "count": 0,
                    "tiers": [],
                    **env,
                }
            )
        tiers_out: list[dict] = []
        for row in batch.get("tiers", []) or []:
            try:
                path = list(row.get("path", []) or [])
            except AttributeError:
                continue
            allowed_count = sum(1 for r in path if bool(r.get("has_all_at")))
            path_length = len(path)
            all_allowed = path_length > 0 and allowed_count == path_length
            any_allowed = allowed_count > 0
            tiers_out.append(
                {
                    "from": row.get("from"),
                    "from_label": row.get("from_label"),
                    "from_rank": row.get("from_rank", -1),
                    "direction": row.get("direction"),
                    "path": path,
                    "path_length": path_length,
                    "allowed_count": allowed_count,
                    "all_allowed": all_allowed,
                    "any_allowed": any_allowed,
                }
            )
        unknown_tiers = list(batch.get("unknown", []) or [])
        return _shared.jsonify(
            {
                "to": to_tier,
                "to_label": _ent.tier_label(to_tier),
                "to_rank": _ent.tier_rank(to_tier),
                "features": features_echo,
                "runtimes": runtimes_echo,
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "unknown_tiers": unknown_tiers,
                "count": len(tiers_out),
                "tiers": tiers_out,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_bundle_from_path_batch_fallback(to_tier, from_tiers)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-from-path-batch",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_from_path_batch():
    """``POST /api/entitlement/missing-all-bundle-from-path-batch?to=<id>``
    -- row-detail complement of
    ``/api/entitlement/has-all-bundle-from-path-batch`` on the source-
    axis batch seat.

    Bundle-shape twin of ``/api/entitlement/missing-features-from-path-batch``
    / ``/api/entitlement/missing-runtimes-from-path-batch`` and source-
    batch complement of the destination-batch
    ``/api/entitlement/missing-all-bundle-at-path-batch`` (PR #4884).

    Wraps :func:`clawmetry.entitlements.missing_all_bundle_from_path_batch`
    so a source-side upgrade-comparison surface can render "for each
    tier my fleet sits on today, WHICH per-axis slots of this 5-axis
    bundle stay locked at every rung climbed toward ``<to_tier>``?"
    straight from the bundle dict off ONE round-trip instead of N
    calls to ``/missing-all-bundle-at-path``.

    Request body is byte-identical to
    ``/has-all-bundle-from-path-batch``:
    ``{"from_tiers": [...], "bundle": {...}}`` (or the bare-axis
    shorthand alongside ``from_tiers``). ``to`` is a required query
    arg.

    Envelope shape mirrors the boolean-fold sibling exactly on the
    header slots (``to`` / ``to_label`` / ``to_rank`` / axis echoes /
    ``unknown_tiers`` / ``count`` / envelope) with the ``tiers[]``
    entries carrying the row-detail rollups::

        {
          ...header slots identical to boolean-fold sibling...,
          "tiers": [
            {
              "from":         "<id>",
              "from_label":   "...",
              "from_rank":    <int>,
              "direction":    "upgrade" | ...,
              "path":         [<missing_all_bundle_at_path row>, ...],
              "path_length":  <int>,
              "denied_count": <int>,   # rungs with any missing axis
              "all_denied":   <bool>,  # every rung has a missing axis
              "any_denied":   <bool>,  # any rung has a missing axis
            },
            ...
          ],
          ...envelope tail identical...
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/missing-all-bundle-at-path?from=<from>&to=<to>``'s ``.path`` for
    the same ``(from, to, bundle)`` triple -- a parity test pins this
    so the singular and source-batch bundle-shape path what-if row-
    detail helpers cannot drift.

    Complement invariant with
    ``/has-all-bundle-from-path-batch``: per source per rung
    ``any(row["missing"].values())`` byte-equals
    ``not row["has_all_at"]`` on the paired boolean-fold call for
    every fully-parseable bundle. (Same non-int-capacity divergence
    :func:`missing_all_bundle_at_path` documents applies.)

    - **400** when ``bundle`` is missing / non-object.
    - **Never 4xxs on endpoint validity**: missing / blank / unknown
      ``to`` returns 200 with ``tiers=[]``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope
      (:func:`_missing_all_bundle_from_path_batch_fallback`) with
      ``tiers=[]``.
    """
    body = _shared.request.get_json(silent=True) or {}
    from_tiers, bundle, err = _shared._parse_from_tiers_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    raw_to = _shared.request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.missing_all_bundle_from_path_batch(
            from_tiers, to_tier, bundle
        )
        env = _shared._resolver_envelope(_ent)
        (
            features_echo,
            runtimes_echo,
            channels_echo,
            retention_echo,
            nodes_echo,
        ) = _ent._normalise_all_bundle(bundle)
        if batch is None:
            return _shared.jsonify(
                {
                    "to": to_tier,
                    "to_label": None,
                    "to_rank": -1,
                    "features": features_echo,
                    "runtimes": runtimes_echo,
                    "channels": channels_echo,
                    "retention_days": retention_echo,
                    "nodes": nodes_echo,
                    "unknown_tiers": list(from_tiers),
                    "count": 0,
                    "tiers": [],
                    **env,
                }
            )

        def _has_missing(row: dict) -> bool:
            m = row.get("missing") or {}
            if not isinstance(m, dict):
                return False
            for v in m.values():
                if isinstance(v, list) and v:
                    return True
                if isinstance(v, int) and not isinstance(v, bool):
                    return True
                if v is not None and not isinstance(v, (list, int)):
                    return True
            return False

        tiers_out: list[dict] = []
        for row in batch.get("tiers", []) or []:
            try:
                path = list(row.get("path", []) or [])
            except AttributeError:
                continue
            denied_count = sum(1 for r in path if _has_missing(r))
            path_length = len(path)
            all_denied = path_length > 0 and denied_count == path_length
            any_denied = denied_count > 0
            tiers_out.append(
                {
                    "from": row.get("from"),
                    "from_label": row.get("from_label"),
                    "from_rank": row.get("from_rank", -1),
                    "direction": row.get("direction"),
                    "path": path,
                    "path_length": path_length,
                    "denied_count": denied_count,
                    "all_denied": all_denied,
                    "any_denied": any_denied,
                }
            )
        unknown_tiers = list(batch.get("unknown", []) or [])
        return _shared.jsonify(
            {
                "to": to_tier,
                "to_label": _ent.tier_label(to_tier),
                "to_rank": _ent.tier_rank(to_tier),
                "features": features_echo,
                "runtimes": runtimes_echo,
                "channels": channels_echo,
                "retention_days": retention_echo,
                "nodes": nodes_echo,
                "unknown_tiers": unknown_tiers,
                "count": len(tiers_out),
                "tiers": tiers_out,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_from_path_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._missing_all_bundle_from_path_batch_fallback(to_tier, from_tiers)
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-batch",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_batch():
    """``POST /api/entitlement/has-all-bundle-batch`` -- bundle-axis batch
    sibling of ``/api/entitlement/has-all`` (singular boolean fold).

    Where the singular ``/has-all`` GET endpoint folds ONE aggregate
    5-axis bundle (features + runtimes + channels + retention + nodes)
    to ONE ``has_all`` boolean at the LIVE perspective, this folds N
    caller-supplied aggregate bundles to N ``has_all`` rows in ONE
    round-trip so a paywall matrix or upgrade-walkthrough surface
    comparing several hypothetical *whole* configs ("Starter-shaped
    install vs Pro-shaped install vs Enterprise-shaped install") reads
    the grant answer off one call instead of N calls to ``/has-all``.

    Symmetric to the reverse-lookup
    ``/api/entitlement/required-tier-bundle-batch`` on the same input
    shape: same POST body, same per-row axis echoes, same never-crash
    posture. The only per-row divergence is the fold slot -- this
    returns ``has_all`` (boolean) where the reverse-lookup sibling
    returns ``required_tier`` (id).

    Distinct from ``/api/entitlement/has-features-batch`` and
    ``/api/entitlement/has-runtimes-batch`` (which batch N *single-axis*
    bundles) and from ``/api/entitlement/has-batch`` (per-*item* rows
    for one flat bundle -- rows are individual feature / runtime /
    capacity ids). This endpoint preserves per-bundle grouping AND the
    cross-axis aggregation: each row is the aggregate fold-answer for
    that whole 5-axis bundle, not a fold-answer per item or per single
    axis.

    Also distinct from ``/api/entitlement/has-all-at-batch`` (which
    fixes ONE bundle and sweeps N perspective tiers): this fixes N
    bundles and reads the LIVE per-install grant.

    POST rather than GET because each bundle already carries five axes
    and N of them can grow well past a comfortable query-string length;
    the sibling singular ``/has-all`` endpoint uses GET where the
    bundle is small.

    Request body::

        {
          "bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
            {}
          ]
        }

    A shorthand ``{"bundles": {"features": ["fleet"]}}`` (a bare dict)
    is treated as ONE bundle for symmetry with the list-of-strings
    shorthand on ``/tiers-for-features-batch``; a missing /
    non-list-non-dict ``bundles`` value is a 400. An empty
    ``bundles=[]`` list is a 400 for the same reason
    ``/required-tier-bundle-batch`` 400s on an empty ``bundles`` --
    distinguishes "caller asked for nothing" from "caller asked and
    every bundle was a typo".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` mirrors the ``/required-tier-bundle-batch`` per-row
    axis echoes byte-for-byte with the fold slot swapped from
    ``required_tier`` to ``has_all``::

        {
          "features":       ["fleet"],
          "runtimes":       ["claude_code"],
          "channels":       5 | null,
          "retention_days": 30 | null,
          "nodes":          2 | null,
          "has_all":        <bool>,
        }

    Per-bundle normalisation matches the singular ``/has-all`` and the
    sibling ``/required-tier-bundle-batch``: CSV normalisation on
    ``features`` / ``runtimes`` (whitespace stripped, lowercased,
    deduplicated preserving first-seen order); runtime aliases
    (``claude-code`` -> ``claude_code``) canonicalised; the three
    capacity axes coerced through ``int(...)`` with a blank / non-int
    collapsing to ``null`` so a typo cannot silently grant on the
    aggregate. Critically, ``retention_days=null`` here means *unset*,
    NOT *unlimited* -- matches every other batch endpoint's posture.

    Grace posture per-row mirrors the LIVE ``/has-all`` byte-for-byte:
    while ``grace`` is ``true`` (the current rollout state) every fully-
    known bundle reports ``has_all=true``; post-enforcement each row
    reflects the underlying :meth:`Entitlement.allows_*` answer.

    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the paywall matrix keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.has_all_bundle_batch(bundles)
        out_rows = [_shared._has_all_bundle_row_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/has-all-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_has_all_bundle_batch_at():
    """``POST /api/entitlement/has-all-bundle-batch-at?tier=<perspective>``
    -- hypothetical-perspective sibling of
    ``/api/entitlement/has-all-bundle-batch``.

    Wraps :func:`clawmetry.entitlements.has_all_bundle_batch_at` so a
    pricing-matrix walkthrough can call the aggregate boolean-fold
    bundle-batch from any tier's perspective without first switching
    the resolver. Fills the ``_at`` slot for the aggregate bundle-batch
    boolean-fold family alongside the reverse-lookup
    ``/required-tier-bundle-batch-at`` and the per-single-axis
    ``_at_batch`` siblings so a caller can call the perspective-scoped
    batch uniformly across every ``_at`` family.

    **Perspective-shaped** (grace-independent by design): unlike the
    reverse-lookup ``/required-tier-bundle-batch-at`` (whose per-row
    ``required_tier`` is inherently perspective-independent -- the
    required tier is a property of the bundle, not the caller), each
    ``has_all_at`` row here DOES depend on ``perspective_tier``.
    Per-row folds delegate to :func:`has_all_at` (backed by the static
    per-tier tables via :func:`_hypothetical_entitlement` on the
    feature / runtime axes and :data:`_TIER_CHANNEL_LIMIT` /
    :data:`_TIER_RETENTION_DAYS` / :data:`_TIER_NODE_LIMIT` on the
    capacity axes), so grace vs enforce yields byte-identical row
    bodies (only the ``current_tier`` envelope shifts). Whole point of
    the ``_at`` slot: at ``tier=oss`` a paid-feature bundle reports
    ``has_all_at=false`` even in grace, whereas the LIVE
    ``/has-all-bundle-batch`` reports ``has_all=true`` for the same
    bundle via grace pass-through.

    Request body is byte-identical to
    ``/has-all-bundle-batch``. The extra ``tier=<perspective>`` query
    arg is required.

    Response layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the bare batch envelope so a
    caller can render "from <perspective> this bundle would be locked"
    copy off one call::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "bundles":                [<row>, ...],
          "count":                  <int>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    Each ``<row>`` mirrors the LIVE ``/has-all-bundle-batch`` row body
    byte-for-byte on the axis echo slots with the fold slot renamed
    ``has_all_at``::

        {
          "features":       ["fleet"],
          "runtimes":       ["claude_code"],
          "channels":       5 | null,
          "retention_days": 30 | null,
          "nodes":          2 | null,
          "has_all_at":     <bool>,
        }

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so a
      caller can render the right "unknown tier" message)
    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall matrix keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.has_all_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._has_all_bundle_row_at_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_bundle_batch_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-at",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_at():
    """``POST /api/entitlement/missing-all-bundle-at?tier=<perspective>``
    -- hypothetical-perspective row-detail singular sibling of
    ``/api/entitlement/missing-all-bundle-batch-at`` (perspective-shaped
    batch) and ``/api/entitlement/has-all-bundle-at`` (boolean fold on
    the same singular seat).

    Wraps :func:`clawmetry.entitlements.missing_all_bundle_at` so a
    paywall walkthrough tile rendering ONE bundle cell at a time can
    read the perspective-scoped denial detail without wrapping in a
    length-one list and unwrapping ``[0]`` from
    ``/missing-all-bundle-batch-at``. Fills the singular-row slot for
    the aggregate-bundle row-detail ``_at`` family alongside the batch
    ``/missing-all-bundle-batch-at``, the paired boolean-fold
    ``/has-all-bundle-at``, and the LIVE row-detail
    ``/missing-all-bundle`` so a caller can call the perspective-scoped
    singular row detail uniformly across every ``_at`` family.

    **Perspective-shaped** (grace-independent by design):
    :func:`missing_all_bundle_at` delegates to
    :func:`_missing_all_bundle_row_at`, which reads from the static
    per-tier grant tables via :func:`_hypothetical_entitlement` on the
    feature / runtime axes and :data:`_TIER_CHANNEL_LIMIT` /
    :data:`_TIER_RETENTION_DAYS` / :data:`_TIER_NODE_LIMIT` on the
    capacity axes, so the row body is byte-identical under grace vs
    enforce for the same ``(perspective, bundle)`` pair. Whole point of
    the ``_at`` slot: at ``tier=oss`` a paid-feature bundle reports
    ``missing.features=["fleet"]`` even in grace, whereas the LIVE
    ``/missing-all-bundle`` reports ``missing.features=[]`` for the
    same bundle via grace pass-through.

    Complement invariant with ``/has-all-bundle-at`` on the same
    ``(tier, bundle)`` inputs: for every fully-parseable non-empty
    bundle, ``any(row["missing"].values())`` is the strict negation of
    the paired ``has_all_at`` row -- a UI can render "which axes are
    still blocked at <perspective>?" from this endpoint and cross-check
    against the paired boolean fold.

    Request body is byte-identical to ``/has-all-bundle-at`` and
    ``/missing-all-bundle``. The extra ``tier=<perspective>`` query arg
    is required::

        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
                    "channels": 5, "retention_days": 30, "nodes": 2}}

    A shorthand where the top-level body IS the bundle
    (``{"features": ["fleet"]}``) is also accepted so the same body the
    ``/missing-all-at`` GET endpoint takes as query args maps 1:1 to a
    POST body. Missing / non-object ``bundle`` value is a 400.

    Response layers ``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank`` on top of
    the singular row body with the fold slot as a per-axis ``missing``
    dict matching :func:`missing_all_at`'s return shape::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "features":               ["fleet"],
          "runtimes":               ["claude_code"],
          "channels":               5 | null,
          "retention_days":         30 | null,
          "nodes":                  2 | null,
          "missing": {
              "features":       [<subset denied at perspective>],
              "runtimes":       [<subset denied at perspective>],
              "channels":       <requested int if denied, else null>,
              "retention_days": <requested int if denied, else null>,
              "nodes":          <requested int if denied, else null>,
          },
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    - **400** when ``tier=`` is missing / blank.
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so
      a caller can render the right "unknown tier" message).
    - **400** when ``bundle`` is missing / non-object.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall walkthrough keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        row = _ent.missing_all_bundle_at(tier_in, bundle) or {
            "features": [],
            "runtimes": [],
            "channels": None,
            "retention_days": None,
            "nodes": None,
            "missing": {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            },
        }
        out = _shared._missing_all_bundle_row_at_to_body(row)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                **out,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all_bundle_at: error: %s", exc)
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
                "missing": {
                    "features": [],
                    "runtimes": [],
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-batch-at",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_batch_at():
    """``POST /api/entitlement/missing-all-bundle-batch-at?tier=<perspective>``
    -- hypothetical-perspective row-detail sibling of
    ``/api/entitlement/has-all-bundle-batch-at`` (boolean fold) and
    ``/api/entitlement/missing-all-bundle-batch`` (LIVE row detail).

    Wraps :func:`clawmetry.entitlements.missing_all_bundle_batch_at`
    so a pricing-matrix walkthrough can call the aggregate row-detail
    bundle-batch from any tier's perspective without first switching
    the resolver. Fills the ``_at`` slot on the aggregate row-detail
    bundle-batch family alongside the boolean-fold
    ``/has-all-bundle-batch-at`` and the per-single-axis
    ``_bundle_batch`` siblings so a caller can call the perspective-
    scoped batch uniformly across every ``_at`` family.

    **Perspective-shaped** (grace-independent by design): each row's
    ``missing`` dict delegates to :func:`missing_all_at` (backed by
    the static per-tier tables via :func:`_hypothetical_entitlement`
    on the feature / runtime axes and :data:`_TIER_CHANNEL_LIMIT` /
    :data:`_TIER_RETENTION_DAYS` / :data:`_TIER_NODE_LIMIT` on the
    capacity axes), so grace vs enforce yields byte-identical row
    bodies (only the ``current_tier`` envelope shifts). Whole point of
    the ``_at`` slot: at ``tier=oss`` a paid-feature bundle reports
    ``missing.features=["fleet"]`` even in grace, whereas the LIVE
    ``/missing-all-bundle-batch`` reports ``missing.features=[]`` for
    the same bundle via grace pass-through.

    Complement invariant with ``/has-all-bundle-batch-at`` on the
    same ``(tier, bundles)`` inputs: for every fully-parseable bundle
    row, ``any(row["missing"].values())`` is the strict negation of
    the paired ``has_all_at`` row -- a UI can render "which axes are
    still blocked at <perspective>?" from this endpoint and cross-
    check against the paired boolean fold.

    Request body is byte-identical to ``/missing-all-bundle-batch``
    and ``/has-all-bundle-batch-at``. The extra ``tier=<perspective>``
    query arg is required.

    Response layers ``perspective_tier`` / ``perspective_tier_label``
    / ``perspective_tier_rank`` on top of the bare batch envelope so a
    caller can render "from <perspective> this bundle would still be
    missing X" copy off one call::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Cloud Pro",
          "perspective_tier_rank":  <int>,
          "bundles":                [<row>, ...],
          "count":                  <int>,
          "current_tier":           "...",
          "current_tier_rank":      <int>,
          "grace":                  <bool>,
          "enforced":               <bool>,
        }

    Each ``<row>`` mirrors the ``/has-all-bundle-batch-at`` row body
    byte-for-byte on the axis-echo slots with the fold slot swapped
    from ``has_all_at`` to a per-axis ``missing`` dict::

        {
          "features":       ["fleet"],
          "runtimes":       ["claude_code"],
          "channels":       5 | null,
          "retention_days": 30 | null,
          "nodes":          2 | null,
          "missing": {
              "features":       [<subset denied at perspective>],
              "runtimes":       [<subset denied at perspective>],
              "channels":       <requested int if denied, else null>,
              "retention_days": <requested int if denied, else null>,
              "nodes":          <requested int if denied, else null>,
          }
        }

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown (body carries ``which=tier`` so a
      caller can render the right "unknown tier" message)
    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      so the paywall matrix keeps rendering.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.missing_all_bundle_batch_at(tier_in, bundles) or []
        out_rows = [_shared._missing_all_bundle_row_at_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_batch_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle():
    """``POST /api/entitlement/missing-all-bundle`` -- singular row-detail
    scalar sibling of ``/api/entitlement/missing-all-bundle-batch`` on
    the LIVE aggregate seat.

    Row-detail complement of ``/api/entitlement/has-all-bundle`` on the
    same input shape: same POST body, same axis echoes, same never-crash
    posture. The only per-row divergence is the fold slot -- this returns
    a per-axis ``missing`` dict where the boolean-fold sibling returns a
    single ``has_all`` bool.

    Folds ONE caller-supplied aggregate 5-axis bundle to the canonical
    batch-row shape at the LIVE resolver so a paywall walkthrough tile
    rendering one hypothetical cell at a time ("would this whole config
    land granted on my install, and if not, which axes still block?")
    reads the per-axis denial detail without wrapping in a length-one
    list and unwrapping ``[0]`` from ``/missing-all-bundle-batch``.

    Distinct from the singular ``/api/entitlement/missing-all`` GET
    endpoint (whose response is just the per-axis ``missing`` dict
    without the axis-echo wrapper): this returns the wrapped six-key
    batch-row shape so a UI wiring the singular and the batch off the
    same helper sees byte-identical rows.

    POST rather than GET so the request body is byte-identical to the
    batch endpoint's per-row shape -- a caller with a single bundle in
    hand can POST it as-is without stitching a CSV query string, and can
    reuse the exact body they would send to ``/has-all-bundle``.

    Request body::

        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
                    "channels": 5, "retention_days": 30, "nodes": 2}}

    A shorthand where the top-level body IS the bundle
    (``{"features": ["fleet"]}``) is also accepted so the same body the
    ``/missing-all`` GET endpoint takes as query args maps 1:1 to a POST
    body. Missing / non-object ``bundle`` value is a 400.

    Response layers the resolver envelope on top of the batch-row shape
    (byte-identical to the batch's per-row body plus the envelope so a
    caller can render "on <tier>, what still blocks?" without a second
    call)::

        {
          "features":          ["fleet"],
          "runtimes":          ["claude_code"],
          "channels":          5 | null,
          "retention_days":    30 | null,
          "nodes":             2 | null,
          "missing": {
              "features":       [<subset not granted on LIVE>],
              "runtimes":       [<subset not granted on LIVE>],
              "channels":       <requested int if denied, else null>,
              "retention_days": <requested int if denied, else null>,
              "nodes":          <requested int if denied, else null>,
          },
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Grace posture mirrors the LIVE ``/missing-all`` byte-for-byte: while
    ``grace`` is ``true`` every fully-known bundle reports the empty
    ``missing`` shape; post-enforcement each slot reflects the underlying
    denial.

    - **400** when ``bundle`` is missing / non-object.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty row shape with empty ``missing``) so the paywall tile keeps
      rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundle, err = _shared._parse_single_bundle_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundle"}), 400
    if err == "bundle_must_be_object":
        return _shared.jsonify({"error": "bundle must be an object"}), 400
    try:
        from clawmetry import entitlements as _ent

        row = _ent.missing_all_bundle(bundle)
        out = _shared._missing_all_bundle_row_to_body(row)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify({**out, **env})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all_bundle: error: %s", exc)
        return _shared.jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "missing": {
                    "features": [],
                    "runtimes": [],
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/missing-all-bundle-batch",
    methods=["POST"],
)
def api_entitlement_missing_all_bundle_batch():
    """``POST /api/entitlement/missing-all-bundle-batch`` -- bundle-axis
    row-detail complement of ``/api/entitlement/has-all-bundle-batch``
    on the LIVE aggregate seat.

    Where the paired boolean-fold sibling
    ``/has-all-bundle-batch`` collapses each 5-axis bundle to ONE
    ``has_all`` boolean, this returns the per-axis denial detail for
    the same N bundles in ONE round-trip so a paywall diagnostics
    matrix or upgrade-walkthrough surface comparing several
    hypothetical *whole* configs ("Starter-shaped install vs Pro-
    shaped install vs Enterprise-shaped install -- for each, which
    axes are still blocked on the LIVE grant?") hydrates the per-axis
    denial column off ONE call instead of N calls to the singular
    aggregate helper.

    Symmetric to the reverse-lookup
    ``/api/entitlement/required-tier-bundle-batch`` and the paired
    ``/has-all-bundle-batch`` on the same input shape: same POST body,
    same per-row axis echoes, same never-crash posture. The only per-
    row divergence is the fold slot -- this returns a per-axis
    ``missing`` dict where the boolean-fold sibling returns
    ``has_all`` (bool) and the reverse-lookup returns
    ``required_tier`` (id).

    Distinct from ``/missing-features-bundle-batch`` /
    ``/missing-runtimes-bundle-batch`` (which batch N *single-axis*
    bundles): each row here spans the same five axes
    ``/missing-all`` does, so the per-row ``missing`` dict carries
    denial detail across features, runtimes, and the three capacity
    scalars in ONE shape.

    Also distinct from ``/missing-all-at`` (which fixes ONE bundle
    and reads ONE hypothetical perspective tier): this fixes N
    bundles and reads the LIVE per-install grant.

    POST rather than GET because each bundle already carries five
    axes and N of them can grow well past a comfortable query-string
    length; the sibling singular ``/missing-all`` endpoint uses GET
    where the input is small.

    Request body::

        {
          "bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
            {}
          ]
        }

    A shorthand ``{"bundles": {"features": ["fleet"]}}`` (a bare
    dict) is treated as ONE bundle for symmetry with the sibling
    ``/has-all-bundle-batch`` posture; a missing / non-list-non-dict
    ``bundles`` value is a 400. An empty ``bundles=[]`` list is a
    400 for the same reason ``/has-all-bundle-batch`` 400s on empty
    input -- distinguishes "caller asked for nothing" from "caller
    asked and every bundle was empty".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` mirrors the ``/has-all-bundle-batch`` per-row axis
    echoes byte-for-byte with the fold slot swapped from ``has_all``
    to a per-axis ``missing`` dict::

        {
          "features":       ["fleet"],
          "runtimes":       ["claude_code"],
          "channels":       5 | null,
          "retention_days": 30 | null,
          "nodes":          2 | null,
          "missing": {
              "features":       [<subset not granted on LIVE>],
              "runtimes":       [<subset not granted on LIVE>],
              "channels":       <requested int if denied, else null>,
              "retention_days": <requested int if denied, else null>,
              "nodes":          <requested int if denied, else null>,
          }
        }

    Per-bundle normalisation matches the singular ``/missing-all`` and
    the sibling ``/has-all-bundle-batch``: CSV normalisation on
    ``features`` / ``runtimes`` (whitespace stripped, lowercased,
    deduplicated preserving first-seen order); runtime aliases
    (``claude-code`` -> ``claude_code``) canonicalised; the three
    capacity axes coerced through ``int(...)`` with a blank / non-int
    collapsing to ``null`` so a typo cannot silently register as
    denied on the aggregate. Critically, ``retention_days=null`` here
    means *unset*, NOT *unlimited* -- matches every other batch
    endpoint's posture.

    Grace posture per-row mirrors the LIVE ``/missing-all`` byte-for-
    byte: while ``grace`` is ``true`` (the current rollout state)
    every fully-known bundle reports the empty ``missing`` shape
    (list ``[]`` per grant axis / capacity ``null``); post-enforcement
    each slot reflects the underlying denial per axis.

    - **400** when ``bundles`` is missing / non-list-non-dict / empty
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the paywall matrix keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_aggregate_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.missing_all_bundle_batch(bundles)
        out_rows = [_shared._missing_all_bundle_row_to_body(row) for row in rows]
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_bundle_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-features-batch",
    methods=["POST"],
)
def api_entitlement_tiers_for_features_batch():
    """``POST /api/entitlement/tiers-for-features-batch`` -- bundle-axis
    batch sibling of ``/api/entitlement/tiers-for-features``.

    Where the singular endpoint returns ONE ladder of tiers that grant
    a caller-supplied bundle of features, this returns N ladders for N
    caller-supplied bundles in ONE round-trip so a pricing-matrix /
    upgrade-walkthrough comparing several hypothetical feature sets
    ("Starter add-ons vs Pro add-ons vs Enterprise add-ons") renders off
    one call instead of N calls to ``/tiers-for-features``.

    Distinct from ``/min-tier-for-features-batch``, which collapses each
    bundle to a single cheapest ``required_tier``: this returns the FULL
    ladder per bundle so an "Available in: Starter, Cloud Pro, ..."
    tooltip renders directly off each row without a follow-up call. Same
    relationship the singular ``/tiers-for-features`` has to
    ``/min-tier-for-features``.

    POST rather than GET because the caller-supplied set of bundles can
    grow past a comfortable query-string length; the sibling singular
    endpoint uses GET+CSV where the bundle is small.

    Request body::

        {
          "bundles": [
            ["fleet", "sso"],
            ["otel_export"],
            []
          ]
        }

    A shorthand ``{"bundles": ["fleet", "sso"]}`` (bare list of strings)
    is treated as ONE bundle, matching the singular endpoint's bare-CSV
    posture; a missing / non-list ``bundles`` value is a 400. An empty
    ``bundles=[]`` list is a 400 for the same reason the singular
    endpoint 400s on an empty ``features=`` -- distinguishes "caller
    asked for nothing" from "caller asked and every token was unknown".

    Response shape::

        {
          "bundles": [<row>, ...],
          "count":   <int>,        # len(bundles)
          "current_tier":      "...",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<row>`` is byte-identical to the bare singular endpoint body
    minus the resolver envelope::

        {
          "items":          ["fleet", "sso"],
          "unknown":        ["bogus"],
          "kind":           "features",
          "count":          2,
          "min_tier":       "enterprise" | null,
          "min_tier_label": "Enterprise" | null,
          "min_tier_rank":  <int> | null,
          "tiers":          [<tier_row>, ...],
        }

    Per-bundle normalisation is delegated to
    :func:`clawmetry.entitlements.tiers_for_features` (whitespace
    stripped, lowercased, deduplicated preserving first-seen order;
    unknown ids bucketed into the per-bundle ``unknown`` instead of
    mis-routing the ladder to a higher tier). Empty / all-unknown
    bundles surface as a stable empty-shape row (``tiers=[]``,
    ``min_tier=null``); does NOT short-circuit the batch.

    - **400** when ``bundles`` is missing / non-list / empty.
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the pricing surface keeps rendering.
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tiers_for_features_batch(bundles)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": list(rows),
                "count": len(rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_features_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-runtimes-batch",
    methods=["POST"],
)
def api_entitlement_tiers_for_runtimes_batch():
    """``POST /api/entitlement/tiers-for-runtimes-batch`` -- runtime-axis
    twin of ``/api/entitlement/tiers-for-features-batch``.

    Same never-5xx posture, same partial-unknown bucketing, same POST
    envelope. Runtime aliases (``claude-code`` -> ``claude_code``) are
    canonicalised per bundle through
    :func:`clawmetry.entitlements.canonical_runtime` so a caller does
    not need to normalise before calling; unknown ids land in the per-
    bundle ``unknown`` and drop from the intersection (a typo does NOT
    silently mis-route the ladder to a higher tier).

    Request body::

        {
          "bundles": [
            ["claude_code", "codex"],
            ["openclaw"],
            []
          ]
        }

    Response shape and error paths mirror
    ``/tiers-for-features-batch`` exactly, with ``kind="runtimes"`` per
    row (``items`` is the runtime list).
    """
    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tiers_for_runtimes_batch(bundles)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "bundles": list(rows),
                "count": len(rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_runtimes_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-features-at-batch",
    methods=["POST"],
)
def api_entitlement_min_tier_for_features_at_batch():
    """``POST /api/entitlement/min-tier-for-features-at-batch?tier=<perspective>``
    -- what-if sibling of ``/api/entitlement/min-tier-for-features-batch``.

    Where the bare batch folds N feature bundles against the LIVE
    resolved entitlement's grace/enforce envelope, this folds them under
    a hypothetical ``perspective_tier`` supplied as the ``tier=`` query
    arg. The per-row body remains perspective-independent -- each row
    delegates to :func:`clawmetry.entitlements.min_tier_for_features`,
    which walks the static per-tier feature map -- but the outer
    envelope carries ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` alongside the live resolver keys so a
    pricing-matrix walkthrough can hit ``X_at`` uniformly across the
    whole ``_at`` batch surface.

    Body parity: per-row bodies byte-identical to the bare batch's
    per-row bodies for the same bundles -- pinned by parity tests so the
    bare and ``_at`` bodies cannot drift.

    Request body: mirrors ``/min-tier-for-features-batch`` exactly.

    Response envelope: adds ``perspective_tier`` / ``perspective_tier_label``
    / ``perspective_tier_rank`` on top of the bare batch envelope.

    - **400** when ``bundles`` is missing / non-list / empty
    - **404** when ``tier=`` is missing / blank / unknown -- caller
      renders "unknown tier"
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the pricing surface keeps rendering.
    """
    tier_in = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "tier": tier_in}),
                404,
            )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_features_at_batch: error: %s", exc
        )
        return _shared.jsonify({"error": "unknown tier", "tier": tier_in}), 404

    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400

    try:
        rows = _ent.min_tier_for_features_at_batch(tier_in, bundles) or []
        out_rows = [
            _shared._min_tier_for_bundle_row_to_body(row, "features") for row in rows
        ]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_features_at_batch: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                **env,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-runtimes-at-batch",
    methods=["POST"],
)
def api_entitlement_min_tier_for_runtimes_at_batch():
    """``POST /api/entitlement/min-tier-for-runtimes-at-batch?tier=<perspective>``
    -- runtime-axis twin of
    ``/api/entitlement/min-tier-for-features-at-batch``.

    Same perspective validation (``tier=`` must be a known member of
    ``_TIER_ORDER``, else 404), same never-5xx posture, same partial-
    unknown bucketing, same POST envelope shape.

    Response body per row and error paths mirror
    ``/min-tier-for-features-at-batch`` exactly, with ``kind="runtimes"``
    and a ``runtimes`` list in place of ``features`` per row.
    """
    tier_in = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "tier": tier_in}),
                404,
            )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_runtimes_at_batch: error: %s", exc
        )
        return _shared.jsonify({"error": "unknown tier", "tier": tier_in}), 404

    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400

    try:
        rows = _ent.min_tier_for_runtimes_at_batch(tier_in, bundles) or []
        out_rows = [
            _shared._min_tier_for_bundle_row_to_body(row, "runtimes") for row in rows
        ]
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                "bundles": out_rows,
                "count": len(out_rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_runtimes_at_batch: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                **env,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-features-at-batch",
    methods=["POST"],
)
def api_entitlement_tiers_for_features_at_batch():
    """``POST /api/entitlement/tiers-for-features-at-batch?tier=<perspective>``
    -- what-if sibling of ``/api/entitlement/tiers-for-features-batch``.

    Where the bare batch folds N feature bundles against the LIVE resolved
    entitlement's grace/enforce envelope, this folds them under a
    hypothetical ``perspective_tier`` supplied as the ``tier=`` query arg.
    The per-row body remains perspective-independent -- each row delegates
    to :func:`clawmetry.entitlements.tiers_for_features`, which walks the
    static per-tier feature map -- but the outer envelope carries
    ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` alongside the live resolver keys so a
    pricing-matrix walkthrough can hit ``X_at`` uniformly across the whole
    ``_at`` batch surface.

    Fills the ``_at_batch`` slot on the bundle-axis tiers-for family
    alongside ``/min-tier-for-features-at-batch`` (per-bundle cheapest
    tier what-if) and ``/affordable-tiers-at-batch`` (per-item plural
    what-if) so a pricing-matrix / upgrade-walkthrough can render "if I
    were on Starter, here are the tier ladders for these three
    hypothetical feature sets" off ONE round-trip instead of N calls to
    ``/tiers-for-features-at``.

    Body parity: per-row bodies byte-identical to the bare batch's
    per-row bodies for the same bundles -- pinned by parity tests so the
    bare and ``_at`` bodies cannot drift.

    Request body: mirrors ``/tiers-for-features-batch`` exactly. A
    shorthand ``{"bundles": ["fleet", "sso"]}`` (bare list of strings) is
    treated as ONE bundle, matching the singular endpoint's bare-CSV
    posture.

    Response envelope: adds ``perspective_tier`` /
    ``perspective_tier_label`` / ``perspective_tier_rank`` on top of the
    bare batch envelope.

    - **400** when ``tier=`` is missing / blank, or when ``bundles`` is
      missing / non-list / empty.
    - **404** when ``tier=`` is unknown -- caller renders "unknown tier".
    - **Never 5xxs**: a resolver failure yields the fallback envelope
      (empty ``bundles`` list) so the pricing surface keeps rendering.
    """
    tier_in = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "tier": tier_in}),
                404,
            )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_features_at_batch: error: %s", exc
        )
        return _shared.jsonify({"error": "unknown tier", "tier": tier_in}), 404

    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400

    try:
        rows = _ent.tiers_for_features_at_batch(tier_in, bundles) or []
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                "bundles": list(rows),
                "count": len(rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_features_at_batch: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                **env,
            }
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-runtimes-at-batch",
    methods=["POST"],
)
def api_entitlement_tiers_for_runtimes_at_batch():
    """``POST /api/entitlement/tiers-for-runtimes-at-batch?tier=<perspective>``
    -- runtime-axis twin of
    ``/api/entitlement/tiers-for-features-at-batch``.

    Same perspective validation (``tier=`` must be a known member of
    ``_TIER_ORDER``, else 404), same never-5xx posture, same partial-
    unknown bucketing, same POST envelope shape. Runtime aliases
    (``claude-code`` -> ``claude_code``) canonicalise per bundle so a
    caller posting either form gets the same ladder back.

    Response body per row and error paths mirror
    ``/tiers-for-features-at-batch`` exactly, with ``kind="runtimes"``
    per row (``items`` is the runtime list).
    """
    tier_in = (_shared.request.args.get("tier") or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "tier": tier_in}),
                404,
            )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_runtimes_at_batch: error: %s", exc
        )
        return _shared.jsonify({"error": "unknown tier", "tier": tier_in}), 404

    body = _shared.request.get_json(silent=True) or {}
    bundles, err = _shared._parse_bundles_body(body)
    if err == "missing":
        return _shared.jsonify({"error": "missing bundles"}), 400
    if err == "empty":
        return _shared.jsonify({"error": "empty bundles"}), 400
    if err == "bundles_must_be_list":
        return _shared.jsonify({"error": "bundles must be a list"}), 400

    try:
        rows = _ent.tiers_for_runtimes_at_batch(tier_in, bundles) or []
        env = _shared._perspective_envelope(_ent, tier_in)
        return _shared.jsonify(
            {
                "bundles": list(rows),
                "count": len(rows),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_runtimes_at_batch: error: %s", exc
        )
        env = _shared._perspective_fallback(tier_in)
        return _shared.jsonify(
            {
                "bundles": [],
                "count": 0,
                **env,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-detection")
def api_entitlement_runtime_detection():
    """``GET /api/entitlement/runtime-detection`` -- probe results merged with
    the resolved entitlement so a paywall CTA card can render "runtimes on
    this machine + which unlock at which tier" off a single round-trip.

    Never 5xx: on any resolver / probe failure returns the neutral empty
    envelope defined by :data:`_EMPTY_RUNTIME_DETECTION` so the frontend
    card stays rendered.
    """
    try:
        from clawmetry import runtime_probe as _probe
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_detection: probe import failed: %s", exc
        )
        return _shared.jsonify(dict(_shared._EMPTY_RUNTIME_DETECTION))

    try:
        from clawmetry import entitlements as _ent
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_detection: entitlements import failed: %s",
            exc,
        )
        # Still return whatever the probes found so the UI can at least list
        # "these runtimes are on this machine" without tier decoration.
        try:
            raw = _probe.probe_runtimes() or []
        except Exception:
            raw = []
        env = dict(_shared._EMPTY_RUNTIME_DETECTION)
        env["probes"] = [
            {
                "id": p.get("id"),
                "label": p.get("label"),
                "free": bool(p.get("free")),
                "found": bool(p.get("found")),
                "allowed": bool(p.get("free")),
                "required_tier": None,
                "required_tier_label": None,
                # NOT the probed paths. A first-run screen needs to know
                # THAT we looked and how widely, which the runtime list and
                # its count already say. Serving the expanded location of
                # every runtime turns each install into a copy-pasteable map
                # of our whole detection strategy, and carries the account
                # name into every screenshot of an empty dashboard. The map
                # lives in `clawmetry diagnose`, a local command whose output
                # a person runs and chooses to share.
                "env": p.get("env") or "",
            }
            for p in raw
        ]
        env["counts"] = _shared._runtime_detection_counts(env["probes"])
        env["detected_locked"] = [
            r["id"] for r in env["probes"] if r["found"] and not r["allowed"]
        ]
        env["ingest_running"] = _shared._ingest_is_running()
        return _shared.jsonify(env)

    try:
        ent = _ent.get_entitlement()
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_detection: resolver failed: %s", exc
        )
        try:
            ent = _ent._oss_free()
        except Exception:
            return _shared.jsonify(dict(_shared._EMPTY_RUNTIME_DETECTION))

    try:
        raw = _probe.probe_runtimes() or []
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_detection: probe_runtimes failed: %s", exc
        )
        raw = []

    allowed_runtimes = set()
    try:
        allowed_runtimes = set(getattr(ent, "runtimes", set()) or set())
    except Exception:
        allowed_runtimes = set()

    probes_out = []
    for p in raw:
        rid = p.get("id") if isinstance(p, dict) else None
        try:
            req_t = _ent.min_tier_for_runtime(rid or "")
        except Exception:
            req_t = None
        try:
            req_lbl = _ent.tier_label(req_t) if req_t else None
        except Exception:
            req_lbl = None
        probes_out.append(
            {
                "id": rid,
                "label": p.get("label") if isinstance(p, dict) else None,
                "free": bool(p.get("free")) if isinstance(p, dict) else False,
                "found": bool(p.get("found")) if isinstance(p, dict) else False,
                "allowed": bool(rid and rid in allowed_runtimes),
                "required_tier": req_t,
                "required_tier_label": req_lbl,
                "env": (p.get("env") or "") if isinstance(p, dict) else "",
            }
        )

    detected_locked = [
        r["id"] for r in probes_out if r["found"] and not r["allowed"] and r["id"]
    ]

    actionable_tier = None
    actionable_tier_label = None
    if detected_locked:
        try:
            actionable_tier = _ent.min_tier_for_runtimes(detected_locked)
        except Exception:
            actionable_tier = None
        if actionable_tier:
            try:
                actionable_tier_label = _ent.tier_label(actionable_tier)
            except Exception:
                actionable_tier_label = None

    try:
        current_tier = getattr(ent, "tier", None) or "oss"
    except Exception:
        current_tier = "oss"
    try:
        current_tier_label = _ent.tier_label(current_tier)
    except Exception:
        current_tier_label = "OSS"
    try:
        grace = bool(getattr(ent, "grace", True))
    except Exception:
        grace = True
    try:
        enforced = bool(_ent.is_enforced())
    except Exception:
        enforced = False

    # ``pending``: the plan has not resolved yet, so ``allowed=False`` on the
    # probes below means "unknown", not "not on your plan". Upsell surfaces
    # must stay silent while true. See entitlements.plan_pending().
    try:
        pending = _ent.plan_pending()
    except Exception:
        pending = False
    ingest_running = _shared._ingest_is_running()
    return _shared.jsonify(
        {
            "current_tier": current_tier,
            "current_tier_label": current_tier_label,
            "grace": grace,
            "enforced": enforced,
            "pending": pending,
            "probes": probes_out,
            "counts": _shared._runtime_detection_counts(probes_out),
            "detected_locked": detected_locked,
            "actionable_tier": actionable_tier,
            "actionable_tier_label": actionable_tier_label,
            "ingest_running": ingest_running,
        }
    )

@_shared.bp_entitlement.route("/api/entitlement/has-node-count-at-batch")
def api_entitlement_has_node_count_at_batch():
    """``GET /api/entitlement/has-node-count-at-batch?tier=<perspective>
    &counts=1,5,100`` -- per-value what-if boolean-gate batch sibling of
    ``/api/entitlement/has-node-count-at`` on the ``nodes`` capacity
    axis.

    Perspective-shaped twin of ``/api/entitlement/has-node-count-batch``
    (which uses the LIVE resolved entitlement). Fills the last
    ``_at_batch`` slot on the ``nodes`` capacity axis alongside
    ``/api/entitlement/min-tier-for-node-count-at-batch`` (the
    perspective-tier variant of the reverse-lookup batch on the same
    axis).

    Where the singular ``/has-node-count-at?tier=<perspective>&count=<N>``
    answers ONE (``has_node_count_at``, ``required_tier``) pair per
    request, this batch answers all requested counts in ONE round-trip
    so a pricing-matrix walkthrough ("at OSS -- does 1 / 5 / 25 / 100
    nodes fit?") binds off one URL per perspective instead of ``N``
    calls to ``/has-node-count-at?tier=oss&count=<N>``.

    - **400** when ``tier=`` is missing / blank, OR when ``counts=`` is
      missing / blank / only-commas.
    - **404** when ``tier`` is unknown (body carries ``which=tier``).
    - **Never 5xxs**: resolver failure -> perspective-carrying grace
      body with empty ``rows``.

    Per-row body shape (mirrors the sibling
    ``/has-node-count-batch`` per-row shape with ``has_node_count_at``
    in place of ``has_node_count`` and no ``upgrade_required`` bit --
    the ``_at`` slot is perspective-shaped, so comparing against the
    LIVE current-tier rank would double-count the perspective; matches
    the singular ``/has-node-count-at`` sibling which omits it for the
    same reason)::

        {
          "count":              <int> | null,
          "count_raw":          "<stripped raw token>",
          "kind":               "node_count",
          "label":              "1 node" | "5 nodes" | null,
          "has_node_count_at":  <bool>,
          "allowed":            <bool>,               # mirror of has_node_count_at
          "unknown":            <bool>,               # true iff non-int input
          "required_tier":      "<tier id>" | null,
          "required_tier_label":"<label>"   | null,
          "required_tier_rank": <int>,                # -1 when required_tier null
        }

    Envelope wraps ``rows`` with ``kind`` / ``count`` (row count) plus
    ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` and the standard resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``) so a UI can render "you are here" alongside the
    per-row grants under the requested perspective.

    Perspective-shaped (grace-independent by design): unlike the LIVE
    ``/has-node-count-batch`` sibling (which reports ``allowed=true``
    for every finite count while ``ent.grace`` is ``True``), each row
    here reflects the STATIC per-tier cap in :data:`_TIER_NODE_LIMIT`
    -- ``has-node-count-at-batch?tier=oss&counts=5`` returns
    ``allowed=false`` even in grace, which is the whole point of the
    ``_at`` slot.

    Cross-consistency: each row's ``has_node_count_at`` byte-equals the
    singular ``/api/entitlement/has-node-count-at`` endpoint for the
    same (``tier``, ``count``) pair; each row's ``required_tier``
    byte-equals the sibling
    ``/api/entitlement/min-tier-for-node-count-at-batch`` row for the
    same count.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        helper_rows = _ent.has_node_count_at_batch(tier_in, values) or []
        raw_by_key: dict[str, str] = {}
        for raw in values:
            try:
                key = str(int(raw))
            except (TypeError, ValueError):
                key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_node_count_at_batch_row_to_body(
                r,
                raw_by_key.get(str(r.get("key")), str(r.get("key"))),
            )
            for r in helper_rows
        ]
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "kind": "node_count",
                "count": len(rows),
                "rows": rows,
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": _ent.tier_rank(tier_in),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_node_count_at_batch: error: %s", exc
        )
        return _shared.jsonify(_shared._has_node_count_at_batch_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/has-channel-count-at-batch")
def api_entitlement_has_channel_count_at_batch():
    """``GET /api/entitlement/has-channel-count-at-batch?tier=<perspective>
    &counts=1,5,100`` -- per-value what-if boolean-gate batch sibling of
    ``/api/entitlement/has-channel-count-at`` on the ``channels``
    capacity axis.

    Perspective-shaped twin of ``/api/entitlement/has-node-count-batch``
    (which uses the LIVE resolved entitlement) and channel-axis twin of
    the paired ``/has-retention-window-at-batch``. Fills the last
    ``_at_batch`` slot on the channel-count axis alongside
    ``/api/entitlement/min-tier-for-channel-count-at-batch`` (the
    perspective-tier variant of the reverse-lookup batch on the same
    axis).

    Where the singular ``/has-channel-count-at?tier=<perspective>&count=<N>``
    answers ONE (``has_channel_count_at``, ``required_tier``) pair per
    request, this batch answers all requested counts in ONE round-trip
    so a pricing-matrix walkthrough ("at OSS -- does 1 / 5 / 25 / 100
    channels fit?") binds off one URL per perspective instead of ``N``
    calls to ``/has-channel-count-at?tier=oss&count=<N>``.

    - **400** when ``tier=`` is missing / blank, OR when ``counts=`` is
      missing / blank / only-commas.
    - **404** when ``tier`` is unknown (body carries ``which=tier``).
    - **Never 5xxs**: resolver failure -> perspective-carrying grace
      body with empty ``rows``.

    Per-row body shape (mirrors the sibling
    ``/has-node-count-batch`` per-row shape with ``has_channel_count_at``
    in place of ``has_node_count`` and no ``upgrade_required`` bit --
    the ``_at`` slot is perspective-shaped, so comparing against the
    LIVE current-tier rank would double-count the perspective; matches
    the singular ``/has-channel-count-at`` sibling which omits it for
    the same reason)::

        {
          "count":              <int> | null,
          "count_raw":          "<stripped raw token>",
          "kind":               "channel_count",
          "label":              "1 channel" | "5 channels" | null,
          "has_channel_count_at": <bool>,
          "allowed":            <bool>,               # mirror of has_channel_count_at
          "unknown":            <bool>,               # true iff non-int input
          "required_tier":      "<tier id>" | null,
          "required_tier_label":"<label>"   | null,
          "required_tier_rank": <int>,                # -1 when required_tier null
        }

    Envelope wraps ``rows`` with ``kind`` / ``count`` (row count) plus
    ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` and the standard resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``) so a UI can render "you are here" alongside the
    per-row grants under the requested perspective.

    Perspective-shaped (grace-independent by design): unlike the LIVE
    ``/has-channel-count-batch`` sibling (which will report
    ``allowed=true`` for every finite count while ``ent.grace`` is
    ``True``), each row here reflects the STATIC per-tier cap in
    :data:`_TIER_CHANNEL_LIMIT` -- ``has-channel-count-at-batch?tier=oss&counts=5``
    returns ``allowed=false`` even in grace, which is the whole point
    of the ``_at`` slot.

    Cross-consistency: each row's ``has_channel_count_at`` byte-
    equals the singular ``/api/entitlement/has-channel-count-at``
    endpoint for the same (``tier``, ``count``) pair; each row's
    ``required_tier`` byte-equals the sibling
    ``/api/entitlement/min-tier-for-channel-count-at-batch`` row for
    the same count.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        helper_rows = _ent.has_channel_count_at_batch(tier_in, values) or []
        raw_by_key: dict[str, str] = {}
        for raw in values:
            try:
                key = str(int(raw))
            except (TypeError, ValueError):
                key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_capacity_at_batch_row_to_body(
                r,
                raw_by_key.get(str(r.get("key")), str(r.get("key"))),
                "channel_count",
                "has_channel_count_at",
            )
            for r in helper_rows
        ]
        return _shared.jsonify(
            _shared._has_capacity_at_batch_body(
                _ent, tier_in, "channel_count", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_channel_count_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_capacity_at_batch_fallback(tier_in, "channel_count")
        )

@_shared.bp_entitlement.route("/api/entitlement/has-retention-window-at-batch")
def api_entitlement_has_retention_window_at_batch():
    """``GET /api/entitlement/has-retention-window-at-batch?tier=<perspective>
    &days=7,30,unlimited`` -- per-value what-if boolean-gate batch sibling
    of ``/api/entitlement/has-retention-window-at`` on the
    ``retention_days`` capacity axis. Retention-axis twin of
    ``/has-channel-count-at-batch``.

    Each token may be a finite int or the case-insensitive string
    ``"unlimited"`` (routes to
    :func:`has_retention_window_at_batch` unlimited-history branch);
    the unlimited row surfaces with ``days=null`` / ``unlimited=true``
    / ``label="unlimited"``. This is the *only* per-axis ``_at_batch``
    on the retention axis that admits the unlimited sentinel --
    matching the input side of
    ``/min-tier-for-retention-window-at-batch``.

    Same 400-on-missing-tier / 400-on-blank-days / 404-on-unknown-tier
    / never-5xx contracts as the two count-axis siblings.

    Per-row body shape (mirrors ``/has-channel-count-at-batch`` with a
    ``days`` slot in place of ``count`` and the extra
    ``unlimited`` flag for the sentinel row)::

        {
          "days":                <int> | null,
          "days_raw":            "<stripped raw token>",
          "kind":                "retention_window",
          "label":               "1 day" | "7 days" | "unlimited" | null,
          "unlimited":           <bool>,               # true iff the unlimited row
          "has_retention_window_at": <bool>,
          "allowed":             <bool>,               # mirror of has_retention_window_at
          "unknown":             <bool>,               # true iff non-int / non-"unlimited"
          "required_tier":       "<tier id>" | null,
          "required_tier_label": "<label>"   | null,
          "required_tier_rank":  <int>,                # -1 when required_tier null
        }
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_capacity_batch_csv("days", unlimited_ok=True)
    if err == "missing":
        return _shared.jsonify({"error": "missing days"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        helper_rows = _ent.has_retention_window_at_batch(tier_in, values) or []
        raw_by_key: dict[str, str] = {}
        for raw in values:
            if raw is None or (
                isinstance(raw, str) and raw.strip().lower() == "unlimited"
            ):
                key = "unlimited"
            else:
                try:
                    key = str(int(raw))
                except (TypeError, ValueError):
                    key = str(raw)
            raw_by_key.setdefault(key, str(raw))
        rows = [
            _shared._has_capacity_at_batch_row_to_body(
                r,
                raw_by_key.get(str(r.get("key")), str(r.get("key"))),
                "retention_window",
                "has_retention_window_at",
            )
            for r in helper_rows
        ]
        return _shared.jsonify(
            _shared._has_capacity_at_batch_body(
                _ent, tier_in, "retention_window", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_retention_window_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_capacity_at_batch_fallback(tier_in, "retention_window")
        )

