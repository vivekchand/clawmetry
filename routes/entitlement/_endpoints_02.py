"""routes/entitlement/_endpoints_02.py — endpoint handlers api_entitlement_missing_features_at_path .. api_entitlement_affordable_tiers_at.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at-path")
def api_entitlement_missing_features_at_path():
    """``GET /api/entitlement/missing-features-at-path?from=<id>&to=<id>&features=a,b,c``
    -- path-shaped complement of ``/api/entitlement/missing-features-at-batch``
    (multi-source what-if matrix over a caller-supplied tier list) and
    the bulk what-if cousin of ``/api/entitlement/missing-features-at``.

    Fixes ONE feature bundle and sweeps across every rung between
    ``from`` and ``to``, returning one row per rung with the per-item
    denial list at that rung -- the "at which tier does each of these
    unlock?" column an upgrade-walkthrough tooltip needs, off ONE URL
    instead of first calling ``/tier-path`` for the rung list and then N
    calls to ``/missing-features-at``.

    Each row in ``path`` byte-equals the scalar
    ``missing_features_at_path`` return
    (``{tier, tier_label, tier_rank, missing}``); each ``missing`` list
    byte-equals ``/missing-features-at?tier=<rung>&features=<bundle>``'s
    ``.missing`` for the same (rung, bundle) pair -- pinned by the parity
    tests so the scalar, batch and path what-if complement helpers cannot
    drift.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``, ``/tier-locks-path``,
    ``/preview-path``, ``/tier-spec-path``, ``/feature-spec-path``,
    ``/runtime-spec-path``, ``/feature-catalog-path`` and
    ``/runtime-catalog-path`` (same ``_PURCHASABLE_TIERS`` filter + same
    sort + same destination-sibling exclusion).

    Response shape: the ``/feature-catalog-path`` envelope
    (``from`` / ``from_label`` / ``from_rank`` / ``to`` / ``to_label`` /
    ``to_rank`` / ``direction`` / ``path``) plus the axis-shared bundle
    metadata (``features`` / ``unknown`` / ``kind`` / ``count`` /
    ``path_length`` / ``any_missing``), the bundle rollup
    (``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank``) and the live resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``).

    ``direction`` values: ``upgrade`` (ascending) | ``downgrade``
    (descending) | ``lateral`` (same rank, different id, single-row
    path) | ``identity`` (``from == to``, empty path) | ``unknown``
    (either endpoint unknown -> empty path). Same-rank siblings strictly
    between the endpoints are both included; same-rank siblings of the
    destination are excluded so the path terminates exactly at ``to``.
    ``trial`` IS accepted as an endpoint -- excluded from the walked
    intermediate rungs (not purchasable) but valid via the lateral
    branch.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown CSV
    -> 200 with ``path=[]``, matching the sibling
    ``/missing-features-at`` posture). Never 5xxs: any helper blowup
    collapses to the empty-path fallback envelope.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_fallback(
                "features", from_tier, to_tier, _shared._parse_csv_arg("features")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at-path")
def api_entitlement_missing_runtimes_at_path():
    """``GET /api/entitlement/missing-runtimes-at-path?from=<id>&to=<id>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/missing-features-at-path``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict scalar -- matches
    the sibling ``/missing-runtimes-at`` upstream-canonicalise pattern.
    Alias-and-canonical pair dedups to ONE entry in ``runtimes`` and
    therefore ONE entry in every rung's ``missing`` list. Never 4xxs;
    never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_fallback(
                "runtimes", from_tier, to_tier, _shared._parse_csv_arg("runtimes")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-at-path")
def api_entitlement_has_features_at_path():
    """``GET /api/entitlement/has-features-at-path?from=<id>&to=<id>&features=a,b,c``
    -- path-shaped boolean-fold sibling of
    ``/api/entitlement/has-features-at-batch`` (multi-source what-if
    matrix over a caller-supplied tier list) and the bulk what-if cousin
    of ``/api/entitlement/has-features-at``.

    Fixes ONE feature bundle and sweeps across every rung between
    ``from`` and ``to``, returning one row per rung with the fold
    boolean at that rung -- the "at which tier does this whole bundle
    unlock?" column an upgrade-walkthrough header needs, off ONE URL
    instead of first calling ``/tier-path`` for the rung list and then N
    calls to ``/has-features-at``. Boolean-fold complement of
    ``/api/entitlement/missing-features-at-path`` (per-item denial list);
    the two paired path endpoints share the walk-metadata envelope so a
    walkthrough UI can render "is this granted?" and "which items are
    still locked?" side by side without a second rung walk.

    Each row in ``path`` byte-equals the scalar
    ``has_features_at_path`` return
    (``{tier, tier_label, tier_rank, has_features_at}``); each
    ``has_features_at`` byte-equals
    ``/has-features-at?tier=<rung>&features=<bundle>``'s ``.allowed``
    for the same (rung, bundle) pair -- pinned by the parity tests so
    the scalar, batch and path what-if boolean-fold helpers cannot
    drift.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``, ``/tier-locks-path``,
    ``/preview-path``, ``/tier-spec-path``, ``/feature-spec-path``,
    ``/runtime-spec-path``, ``/feature-catalog-path``,
    ``/runtime-catalog-path``, ``/missing-features-at-path`` and
    ``/missing-runtimes-at-path`` (same ``_PURCHASABLE_TIERS`` filter +
    same sort + same destination-sibling exclusion).

    Response shape: the ``/feature-catalog-path`` envelope
    (``from`` / ``from_label`` / ``from_rank`` / ``to`` / ``to_label`` /
    ``to_rank`` / ``direction`` / ``path``) plus the axis-shared bundle
    metadata (``features`` / ``unknown`` / ``kind`` / ``count`` /
    ``path_length``), the boolean-fold rollup (``allowed_count`` /
    ``all_allowed`` / ``any_allowed``), the bundle-level required-tier
    rollup (``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank``) and the live resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``).

    ``direction`` values: ``upgrade`` (ascending) | ``downgrade``
    (descending) | ``lateral`` (same rank, different id, single-row
    path) | ``identity`` (``from == to``, empty path) | ``unknown``
    (either endpoint unknown -> empty path). Same-rank siblings strictly
    between the endpoints are both included; same-rank siblings of the
    destination are excluded so the path terminates exactly at ``to``.
    ``trial`` IS accepted as an endpoint -- excluded from the walked
    intermediate rungs (not purchasable) but valid via the lateral
    branch.

    Endpoint-level fold semantics inherit ``/has-features-at-batch``
    byte-for-byte: an unknown token in the bundle collapses the
    endpoint-level fold to ``False`` on EVERY rung (``unknown != []`` ->
    every row's ``has_features_at`` reads ``False``), so a bundle typo
    fails-closed at the endpoint layer the same way it fails-closed on
    the singular ``/has-features-at`` endpoint.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown CSV
    -> 200 with ``path=[]``, matching the sibling ``/has-features-at``
    posture). Never 5xxs: any helper blowup collapses to the empty-path
    fallback envelope.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_fallback(
                "features", from_tier, to_tier, _shared._parse_csv_arg("features")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at-path")
def api_entitlement_has_runtimes_at_path():
    """``GET /api/entitlement/has-runtimes-at-path?from=<id>&to=<id>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/has-features-at-path``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict scalar -- matches
    the sibling ``/has-runtimes-at`` /
    ``/has-runtimes-at-batch`` upstream-canonicalise pattern. Alias-and-
    canonical pair dedups to ONE entry in ``runtimes`` and therefore
    ONE fold input on every rung. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_fallback(
                "runtimes", from_tier, to_tier, _shared._parse_csv_arg("runtimes")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at-path-batch")
def api_entitlement_missing_features_at_path_batch():
    """``GET /api/entitlement/missing-features-at-path-batch?from=<id>&to=a,b,c&features=x,y,z``
    -- batch sibling of ``/api/entitlement/missing-features-at-path``.

    Where ``/missing-features-at-path`` walks the rungs between ONE
    ``(from, to)`` pair under ONE feature bundle, this walks the
    rungs between ONE ``from`` and N candidate ``to`` tiers under
    ONE bundle in ONE round-trip. Pairs with
    ``/missing-features-at-path`` the same way
    ``/tier-unlocks-path-batch`` pairs with ``/tier-unlocks-path``:
    scalar -> matrix in one call. Multi-destination twin of
    ``/tier-unlocks-path-batch`` (same fan-out shape, per-item denial
    body instead of marginal-grant body) and matrix-shaped cousin of
    ``/missing-features-at-batch`` (which fans out over perspective
    tiers rather than destinations).

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/missing-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` for the same triple -- pinned by the parity tests so
    the scalar and batch path accessors cannot drift. Per-destination
    path lengths can legitimately differ (the rungs walked depend on
    the destination), matching ``/tier-unlocks-path-batch`` /
    ``/tier-locks-path-batch`` / ``/capacity-diff-path-batch``'s
    posture.

    Envelope shape is fully documented on
    :func:`_missing_bundle_at_path_batch_body`. ``trial`` IS accepted
    as a destination (excluded from the walked intermediate rungs the
    way ``/missing-features-at-path`` already excludes it, but is a
    valid endpoint via the lateral / identity branches).

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/missing-features-at-batch`` posture -- a pricing-
    comparison matrix binds ``tiers`` directly without a pre-
    validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_missing_bundle_at_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_batch_fallback(
                "features",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at-path-batch")
def api_entitlement_missing_runtimes_at_path_batch():
    """``GET /api/entitlement/missing-runtimes-at-path-batch?from=<id>&to=a,b,c&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/missing-features-at-path-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` ->
    ``claude_code``) is applied per-token upstream at the endpoint
    layer so ``?runtimes=claude-code,openclaw`` collapses to the
    canonical ``claude_code,openclaw`` before hitting the strict
    scalar -- matches the sibling ``/missing-runtimes-at-path``
    upstream-canonicalise pattern. Alias-and-canonical pair dedups
    to ONE entry in ``runtimes`` and therefore ONE entry in every
    per-destination rung's ``missing`` list. Never 4xxs; never
    5xxs.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_batch_fallback(
                "runtimes",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-at-path-batch")
def api_entitlement_has_features_at_path_batch():
    """``GET /api/entitlement/has-features-at-path-batch?from=<id>&to=a,b,c&features=x,y,z``
    -- batch sibling of ``/api/entitlement/has-features-at-path``.

    Where ``/has-features-at-path`` walks the rungs between ONE
    ``(from, to)`` pair under ONE feature bundle, this walks the
    rungs between ONE ``from`` and N candidate ``to`` tiers under
    ONE bundle in ONE round-trip. Pairs with
    ``/has-features-at-path`` the same way
    ``/missing-features-at-path-batch`` pairs with
    ``/missing-features-at-path``: scalar -> matrix in one call.
    Multi-destination twin of ``/missing-features-at-path-batch``
    (same fan-out shape, per-rung fold-boolean body instead of
    per-item denial body) and matrix-shaped cousin of
    ``/has-features-at-batch`` (which fans out over perspective
    tiers rather than destinations).

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/has-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` for the same triple -- pinned by the parity tests so
    the scalar and batch path accessors cannot drift. Per-destination
    path lengths can legitimately differ (the rungs walked depend on
    the destination), matching ``/missing-features-at-path-batch`` /
    ``/tier-unlocks-path-batch`` / ``/tier-locks-path-batch`` /
    ``/capacity-diff-path-batch``'s posture.

    Envelope shape is fully documented on
    :func:`_has_bundle_at_path_batch_body`. ``trial`` IS accepted
    as a destination (excluded from the walked intermediate rungs the
    way ``/has-features-at-path`` already excludes it, but is a
    valid endpoint via the lateral / identity branches).

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/has-features-at-batch`` posture -- a pricing-
    comparison matrix binds ``tiers`` directly without a pre-
    validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_has_bundle_at_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_batch_fallback(
                "features",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at-path-batch")
def api_entitlement_has_runtimes_at_path_batch():
    """``GET /api/entitlement/has-runtimes-at-path-batch?from=<id>&to=a,b,c&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/has-features-at-path-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` ->
    ``claude_code``) is applied per-token upstream at the endpoint
    layer so ``?runtimes=claude-code,openclaw`` collapses to the
    canonical ``claude_code,openclaw`` before hitting the strict
    scalar -- matches the sibling ``/has-runtimes-at-path``
    upstream-canonicalise pattern. Alias-and-canonical pair dedups
    to ONE entry in ``runtimes`` and therefore ONE fold input on
    every rung of every destination. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_batch_fallback(
                "runtimes",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-from-path-batch")
def api_entitlement_has_features_from_path_batch():
    """``GET /api/entitlement/has-features-from-path-batch?from=a,b,c&to=<id>&features=x,y,z``
    -- source-axis batch sibling of ``/api/entitlement/has-features-at-path``.

    Where ``/has-features-at-path`` walks the rungs between ONE
    ``(from, to)`` pair under ONE feature bundle, this walks the rungs
    between N candidate sources and ONE ``to`` under ONE bundle in ONE
    round-trip. Mirror-direction twin of ``/has-features-at-path-batch``
    (which fans out over destinations); boolean-fold complement of a
    hypothetical ``/missing-features-from-path-batch`` at the source-
    batch layer, in the same relationship ``/has-features-at-path``
    has to ``/missing-features-at-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/has-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` for the same triple -- pinned by the parity tests so
    the scalar and source-batch path accessors cannot drift. Per-source
    path lengths can legitimately differ (the rungs walked depend on
    the source), matching ``/tier-unlocks-path-batch`` /
    ``/has-features-at-path-batch``'s posture.

    Envelope shape is fully documented on
    :func:`_has_bundle_from_path_batch_body`. ``trial`` IS accepted as
    a source id (excluded from the walked intermediate rungs the way
    ``/has-features-at-path`` already excludes it, but is a valid
    endpoint via the lateral / identity branches).

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-at-batch`` posture -- a source-side comparison
    matrix binds ``tiers`` directly without a pre-validation round-
    trip). Never 5xxs: any helper blowup collapses to
    :func:`_has_bundle_from_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_from_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_from_path_batch_fallback(
                "features",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-from-path-batch")
def api_entitlement_has_runtimes_from_path_batch():
    """``GET /api/entitlement/has-runtimes-from-path-batch?from=a,b,c&to=<id>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/has-features-from-path-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict scalar --
    matches the sibling ``/has-runtimes-at-path`` upstream-canonicalise
    pattern. Alias-and-canonical pair dedups to ONE entry in
    ``runtimes`` and therefore ONE fold input on every per-source rung.
    Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._has_bundle_from_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_from_path_batch_fallback(
                "runtimes",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features-from-path-batch")
def api_entitlement_missing_features_from_path_batch():
    """``GET /api/entitlement/missing-features-from-path-batch?from=a,b,c&to=<id>&features=x,y,z``
    -- source-axis batch sibling of ``/api/entitlement/missing-features-at-path``.

    Where ``/missing-features-at-path`` walks the rungs between ONE
    ``(from, to)`` pair under ONE feature bundle, this walks the rungs
    between N candidate sources and ONE ``to`` under ONE bundle in ONE
    round-trip. Mirror-direction twin of
    ``/missing-features-at-path-batch`` (which fans out over
    destinations); complement-shaped sibling of
    ``/has-features-from-path-batch`` at the source-batch layer, in
    the same relationship ``/missing-features-at-path`` has to
    ``/has-features-at-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/missing-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` for the same triple -- pinned by the parity tests so
    the scalar and source-batch path accessors cannot drift. Per-source
    path lengths can legitimately differ (the rungs walked depend on
    the source), matching ``/has-features-from-path-batch``'s posture.

    Envelope shape is fully documented on
    :func:`_missing_bundle_from_path_batch_body`. ``trial`` IS accepted
    as a source id (excluded from the walked intermediate rungs the way
    ``/missing-features-at-path`` already excludes it, but is a valid
    endpoint via the lateral / identity branches).

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-from-path-batch`` posture -- a source-side
    comparison matrix binds ``tiers`` directly without a pre-
    validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_missing_bundle_from_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_from_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_from_path_batch_fallback(
                "features",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-from-path-batch")
def api_entitlement_missing_runtimes_from_path_batch():
    """``GET /api/entitlement/missing-runtimes-from-path-batch?from=a,b,c&to=<id>&runtimes=x,y,z``
    -- runtime-axis twin of ``/api/entitlement/missing-features-from-path-batch``.

    Same envelope with ``runtimes`` in the axis-specific slot.
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream at the endpoint layer so
    ``?runtimes=claude-code,openclaw`` collapses to the canonical
    ``claude_code,openclaw`` before hitting the strict scalar --
    matches the sibling ``/missing-runtimes-at-path`` upstream-
    canonicalise pattern. Alias-and-canonical pair dedups to ONE entry
    in ``runtimes`` and therefore ONE entry in every per-source rung's
    ``missing`` list. Never 4xxs; never 5xxs.
    """
    try:
        return _shared.jsonify(_shared._missing_bundle_from_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_from_path_batch_fallback(
                "runtimes",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at")
def api_entitlement_has_all_at():
    """``GET /api/entitlement/has-all-at?tier=<perspective>
    &features=a,b&runtimes=x,y&channels=5&retention_days=30&nodes=2`` --
    hypothetical-perspective mixed-axis boolean-gate scalar.

    Perspective-shaped sibling of ``/api/entitlement/has-all``: same
    aggregate mixed-axis fold, but the boolean answers "would tier
    ``<perspective>`` grant everything?" from the static per-tier grant
    tables instead of "does the resolved entitlement grant everything
    right now?" from the live resolver. A pricing-matrix walkthrough
    that renders "if I were on Pro, this whole bundle would be
    granted -- upgrade?" binds ``allowed`` directly off this URL per
    perspective without switching the resolver.

    Fills the ``_at`` slot on the mixed-axis rollup family alongside
    :func:`min_tier_for_all_at` (scalar tier-id sibling) and the singular
    ``_at`` scalars (``has_feature_at`` / ``has_runtime_at`` /
    ``has_channel_count_at`` / ``has_retention_window_at`` /
    ``has_node_count_at``), and completes the mixed-axis batch matrix
    alongside ``/has-batch-at`` (per-row perspective sibling of
    ``/has-batch``).

    Every axis is OPTIONAL. Supply any non-empty subset; the fold
    answers off just those axes and every unsupplied axis is skipped
    (contributes ``True`` to the fold). Runtime-alias canonicalisation
    (``claude-code`` -> ``claude_code``) is applied per token before
    the known/unknown split. Capacity axes accept a single int (``5``);
    blank / non-int values collapse ``has_all_at`` to ``False`` (matches
    the singular capacity ``_at`` scalars' strict-``False`` typo
    posture).

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the singular
    ``_at`` delegates, not the resolver's ``grace`` bit) -- the whole
    point of the ``_at`` slot: ``/has-all-at?tier=oss&features=fleet``
    returns ``has_all_at=false`` even in grace (because OSS statically
    does not grant ``fleet``), whereas the LIVE
    ``/has-all?features=fleet`` reports ``true`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **400** on missing / blank ``tier=``.
    - **404** on unknown ``tier=`` (body carries ``which=tier``).
    - **Never 4xxs** on axis-side inputs -- no axes supplied returns 200
      with ``has_all_at=false`` (matches ``/has-all`` empty-``False``
      posture); non-int capacity / unknown token collapses
      ``has_all_at`` to ``False`` with the offending token surfaced via
      ``unknown_features`` / ``unknown_runtimes``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope with ``has_all_at=false`` so the pricing
      walkthrough keeps rendering.

    Envelope shape (21 keys, byte-stable across every input branch)::

        {
          "perspective_tier":       "cloud_pro",
          "perspective_tier_label": "Pro",
          "perspective_tier_rank":  <int>,
          "features":               ["fleet"],           # known ids only
          "runtimes":               ["claude_code"],     # canonicalised, known only
          "channels":               5 | null,            # parsed int or null
          "retention_days":         30 | null,
          "nodes":                  2 | null,
          "unknown_features":       ["bogus"],           # tokens not in ALL_FEATURES
          "unknown_runtimes":       [],                  # tokens not in ALL_RUNTIMES
          "supplied_axes":          ["features", "channels"],
          "supplied_count":         2,
          "has_all_at":             true,                # perspective boolean
          "allowed":                true,                # alias of has_all_at
          "required_tier":          "cloud_pro" | null,
          "required_tier_label":    "Pro" | null,
          "required_tier_rank":     <int>,               # -1 when null
          "current_tier":           "oss",
          "current_tier_rank":      0,
          "grace":                  true,
          "enforced":               false
        }

    Note the deliberate absence of ``upgrade_required``: this is the
    perspective-shaped ``_at`` slot, so comparing against the LIVE
    current-tier rank would double-count the perspective (matches the
    singular ``/has-feature-at`` / ``/has-runtime-at`` / ``/has-batch-at``
    siblings which omit it for the same reason).
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
        return _shared.jsonify(_shared._has_all_at_body(tier_in))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_at: error: %s", exc)
        return _shared.jsonify(_shared._has_all_at_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at")
def api_entitlement_missing_all_at():
    """``GET /api/entitlement/missing-all-at?tier=<perspective>
    &features=a,b&runtimes=x,y&channels=5&retention_days=30&nodes=2`` --
    hypothetical-perspective mixed-axis row-detail complement scalar.

    Perspective-shaped row-detail sibling of ``/api/entitlement/missing-all``:
    same aggregate mixed-axis fold, but the per-axis missing lists answer
    "which subset would tier ``<perspective>`` NOT grant?" from the static
    per-tier grant tables instead of "which subset does the resolved
    entitlement not grant right now?" from the live resolver. A paywall
    diagnostics tile that renders "on OSS you'd still be missing fleet +
    claude_code + 100 channels + 90d retention + 99 nodes -- upgrade to
    unlock" binds every per-axis slot directly off this URL per
    perspective without switching the resolver.

    Fills the ``_at`` slot on the mixed-axis row-detail complement family
    alongside :func:`_has_all_at_body` (boolean-fold sibling) and the
    singular row-detail ``_at`` endpoints ``/missing-features-at`` /
    ``/missing-runtimes-at`` for the two grant axes.

    Every axis is OPTIONAL. Supply any non-empty subset; the envelope
    always carries every axis' slot for byte-stable shape across every
    URL branch. Runtime-alias canonicalisation (``claude-code`` ->
    ``claude_code``) is applied per token before the known/unknown split.
    Capacity axes accept a single int (``5``); blank / non-int values
    surface the raw string in the per-axis missing slot so a UI can flag
    the typo. Unknown feature / runtime tokens are surfaced INSIDE the
    per-axis missing list AND echoed in ``unknown_features`` /
    ``unknown_runtimes`` for a diagnostics tooltip.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the singular
    ``_at`` delegates, not the resolver's ``grace`` bit) -- the whole
    point of the ``_at`` slot: ``/missing-all-at?tier=oss&features=fleet``
    returns ``features=["fleet"]`` even in grace (because OSS statically
    does not grant ``fleet``), whereas the LIVE
    ``/missing-all?features=fleet`` reports ``features=[]`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **400** on missing / blank ``tier=``.
    - **404** on unknown ``tier=`` (body carries ``which=tier``).
    - **Never 4xxs** on axis-side inputs -- no axes supplied returns 200
      with every per-axis slot empty and ``any_missing=false`` (matches
      ``/missing-all`` empty posture).
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope with every per-axis slot empty and
      ``any_missing=false`` so the pricing walkthrough keeps rendering.

    Envelope shape (21 keys, byte-stable across every input branch)::

        {
          "perspective_tier":       "oss",
          "perspective_tier_label": "OSS",
          "perspective_tier_rank":  <int>,
          "features":               ["fleet"],           # DENIED subset (+ unknowns)
          "runtimes":               ["claude_code"],     # DENIED subset (+ unknowns)
          "channels":               100 | null,          # supplied int if denied, else null
          "retention_days":         90  | null,
          "nodes":                  99  | null,
          "unknown_features":       ["bogus"],
          "unknown_runtimes":       [],
          "supplied_axes":          ["features"],
          "supplied_count":         1,
          "missing_count":          1,
          "any_missing":            true,
          "required_tier":          "cloud_pro" | null,
          "required_tier_label":    "Pro" | null,
          "required_tier_rank":     <int>,               # -1 when null
          "current_tier":           "oss",
          "current_tier_rank":      0,
          "grace":                  true,
          "enforced":               false
        }

    Note the deliberate absence of ``upgrade_required``: this is the
    perspective-shaped ``_at`` slot, so comparing against the LIVE
    current-tier rank would double-count the perspective (matches the
    singular ``/missing-features-at`` / ``/missing-runtimes-at`` and the
    paired ``/has-all-at`` siblings which omit it for the same reason).
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
        return _shared.jsonify(_shared._missing_all_at_body(tier_in))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all_at: error: %s", exc)
        return _shared.jsonify(_shared._missing_all_at_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-path")
def api_entitlement_missing_all_at_path():
    """``GET /api/entitlement/missing-all-at-path?from=<id>&to=<id>
    &features=a,b&runtimes=x,y&channels=5&retention_days=30&nodes=2`` --
    aggregate mixed-axis path-shaped row-detail complement of
    ``/api/entitlement/has-all-at-path`` (paired boolean-fold path) and
    path-shaped sibling of ``/api/entitlement/missing-all-at``.

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    ``from`` and ``to``, returning one row per rung with the per-axis
    missing rollup at that rung -- the "at which tier does each per-axis
    slot in this bundle clear?" column an upgrade-walkthrough tooltip
    needs, off ONE URL instead of first calling ``/tier-path`` for the
    rung list and then N calls to ``/missing-all-at``, or 5 * N calls
    fanned out across the per-axis path endpoints
    (``/missing-features-at-path`` + ``/missing-runtimes-at-path`` +
    three capacity axes) plus a client-side per-axis stitch per rung.

    Aggregate mixed-axis extension of
    ``/api/entitlement/missing-features-at-path`` /
    ``/api/entitlement/missing-runtimes-at-path`` (single-axis path).
    Fills the ``_at_path`` slot on the mixed-axis row-detail complement
    family alongside :func:`missing_all_at` (singular perspective
    scalar), :func:`missing_all_at_batch` (multi-perspective batch),
    and :func:`missing_all_bundle_batch` (per-bundle batch).

    Each row in ``path`` byte-equals the scalar
    :func:`clawmetry.entitlements.missing_all_at_path` return
    (``{tier, tier_label, tier_rank, missing: {features, runtimes,
    channels, retention_days, nodes}}``); each rung's ``missing`` dict
    byte-equals ``/missing-all-at?tier=<rung>&<same bundle>``'s
    per-axis slots for the same (rung, bundle) pair -- pinned by the
    parity tests so the scalar, batch and path what-if row-detail
    helpers cannot drift.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``, ``/tier-locks-path``,
    ``/preview-path``, ``/tier-spec-path``, ``/feature-spec-path``,
    ``/runtime-spec-path``, ``/feature-catalog-path``,
    ``/runtime-catalog-path``, ``/has-features-at-path``,
    ``/has-runtimes-at-path``, ``/missing-features-at-path``,
    ``/missing-runtimes-at-path`` and ``/has-all-at-path`` (same
    ``_PURCHASABLE_TIERS`` filter + same sort + same destination-
    sibling exclusion).

    Every axis is OPTIONAL. Supply any non-empty subset; the row-detail
    rollup answers off just those axes per row and every unsupplied
    axis' per-rung slot is empty/None (nothing to check on that axis).
    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per token upstream of the strict scalar. Capacity axes
    accept a single int (``5``); blank / non-int values surface the raw
    string in every rung's per-axis capacity slot so a UI can flag the
    typo.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the
    singular ``_at`` delegates, not the resolver's ``grace`` bit) --
    the whole point of the ``_at`` slot:
    ``/missing-all-at-path?from=oss&to=enterprise&features=fleet``
    shows ``oss``-adjacent rungs' ``missing["features"]=["fleet"]``
    even in grace where they still lack the grant, whereas the LIVE
    ``/missing-all?features=fleet`` reports ``features=[]`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **Never 4xxs** on any input branch: missing / blank / unknown
      endpoints returns 200 with ``path=[]`` (``direction`` reads
      ``"unknown"``); no axes supplied returns 200 with the path still
      populated but every rung's per-axis missing empty/None (matches
      the singular ``/missing-all-at`` empty posture); unknown token /
      non-int capacity surfaces the offending token in every rung's
      per-axis slot with the caller-supplied set echoed via
      ``unknown_features`` / ``unknown_runtimes``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope (:func:`_missing_all_at_path_fallback`)
      with ``path=[]`` so the pricing walkthrough keeps rendering.

    Envelope shape is fully documented on :func:`_missing_all_at_path_body`.
    """
    try:
        return _shared.jsonify(_shared._missing_all_at_path_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_at_path_fallback(
                from_tier,
                to_tier,
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-batch")
def api_entitlement_has_all_at_batch():
    """``GET /api/entitlement/has-all-at-batch?tiers=<a,b,...>
    &features=<x,y,...>&runtimes=<r,s,...>&channels=N&retention_days=K
    &nodes=M`` -- batch what-if sibling of ``/api/entitlement/has-all-at``.

    Fixes ONE mixed-axis bundle and sweeps across N perspective tiers,
    returning one row per tier with the aggregate mixed-axis fold boolean
    plus the surrounding tier envelope. Mixed-axis extension of
    ``/api/entitlement/has-features-at-batch`` /
    ``/api/entitlement/has-runtimes-at-batch`` (single-axis batch): a
    pricing-matrix column ("does OSS admit fleet + claude_code + 100
    channels + 90d retention + 100 nodes? Starter? Cloud Pro? Enterprise?")
    hydrates the whole column off ONE URL instead of five ``_at-batch``
    round-trips + a client-side AND-chain. Fills the ``_at_batch`` slot
    on the mixed-axis rollup family alongside :func:`has_all_at` (the
    singular per-perspective scalar) and :func:`min_tier_for_all_at_batch`
    (the reverse-lookup batch sibling).

    Every axis is OPTIONAL. Supply any non-empty subset; the fold answers
    off just those axes per row and every unsupplied axis is skipped
    (contributes ``True`` to each row's fold). Runtime-alias
    canonicalisation (``claude-code`` -> ``claude_code``) is applied per
    token upstream of the strict scalar. Capacity axes accept a single
    int (``5``); blank / non-int values collapse every row's
    ``has_all_at`` to ``False`` (matches the singular capacity ``_at``
    scalars' strict-``False`` typo posture).

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the singular
    ``_at`` delegates, not the resolver's ``grace`` bit) -- the whole
    point of the ``_at`` slot:
    ``/has-all-at-batch?tiers=oss,cloud_pro&features=fleet`` returns the
    ``oss`` row's ``has_all_at=false`` even in grace (because OSS
    statically does not grant ``fleet``), whereas the LIVE
    ``/has-all?features=fleet`` reports ``true`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **Never 4xxs** on any input branch: missing / blank / all-unknown
      ``tiers=`` returns 200 with ``tiers=[]`` (matches the sibling
      ``/has-features-at-batch`` posture -- a paywall matrix binds
      ``tiers`` directly without a pre-validation round-trip). No axes
      supplied returns 200 with ``tiers`` still populated but every
      row's ``has_all_at=false`` (matches the singular
      ``/has-all-at`` empty-``False`` posture). Unknown token / non-int
      capacity in the bundle collapses every row to ``False`` with the
      offending token surfaced via ``unknown_features`` /
      ``unknown_runtimes``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope with ``tiers=[]`` so the pricing walkthrough
      keeps rendering.

    Envelope shape is fully documented on :func:`_has_all_at_batch_body`.

    Per-row parity is pinned by tests: each row's ``has_all_at`` byte-
    equals :func:`has_all_at` for the same ``(row.tier, bundle)`` pair,
    and byte-equals ``/api/entitlement/has-all-at?tier=<row.tier>&...``'s
    ``has_all_at`` on the same bundle -- so any future contract change
    on either side has to update both.
    """
    try:
        return _shared.jsonify(_shared._has_all_at_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_at_batch_fallback(
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-path")
def api_entitlement_has_all_at_path():
    """``GET /api/entitlement/has-all-at-path?from=<id>&to=<id>
    &features=a,b&runtimes=x,y&channels=5&retention_days=30&nodes=2`` --
    aggregate mixed-axis path-shaped boolean-fold sibling of
    ``/api/entitlement/has-all-at-batch`` (multi-source what-if matrix
    over a caller-supplied tier list) and the bulk what-if cousin of
    ``/api/entitlement/has-all-at``.

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    ``from`` and ``to``, returning one row per rung with the aggregate
    fold boolean at that rung -- the "at which tier does this WHOLE
    5-axis bundle unlock?" column an upgrade-walkthrough header needs,
    off ONE URL instead of first calling ``/tier-path`` for the rung
    list and then N calls to ``/has-all-at``, or 5 * N calls fanned
    out across the per-axis path endpoints (``/has-features-at-path``
    + ``/has-runtimes-at-path`` + three capacity axes) plus a client-
    side AND-chain per rung.

    Aggregate mixed-axis extension of ``/api/entitlement/has-features-at-path``
    / ``/api/entitlement/has-runtimes-at-path`` (single-axis path).
    Fills the ``_at_path`` slot on the mixed-axis rollup family
    alongside :func:`has_all_at` (singular perspective scalar),
    ``/api/entitlement/has-all-at-batch`` (multi-perspective batch),
    and :func:`min_tier_for_all_at_batch` (reverse-lookup batch).

    Each row in ``path`` byte-equals the scalar
    :func:`clawmetry.entitlements.has_all_at_path` return
    (``{tier, tier_label, tier_rank, has_all_at}``); each ``has_all_at``
    byte-equals ``/has-all-at?tier=<rung>&<same bundle>``'s
    ``has_all_at`` for the same (rung, bundle) pair -- pinned by the
    parity tests so the scalar, batch and path what-if boolean-fold
    helpers cannot drift.

    Rung walk is byte-stable against ``/tier-path``,
    ``/capacity-diff-path``, ``/tier-unlocks-path``, ``/tier-locks-path``,
    ``/preview-path``, ``/tier-spec-path``, ``/feature-spec-path``,
    ``/runtime-spec-path``, ``/feature-catalog-path``,
    ``/runtime-catalog-path``, ``/has-features-at-path``,
    ``/has-runtimes-at-path``, ``/missing-features-at-path`` and
    ``/missing-runtimes-at-path`` (same ``_PURCHASABLE_TIERS`` filter +
    same sort + same destination-sibling exclusion).

    Every axis is OPTIONAL. Supply any non-empty subset; the fold
    answers off just those axes per row and every unsupplied axis is
    skipped (contributes ``True`` to each row's fold). Runtime-alias
    canonicalisation (``claude-code`` -> ``claude_code``) is applied
    per token upstream of the strict scalar. Capacity axes accept a
    single int (``5``); blank / non-int values collapse every row's
    ``has_all_at`` to ``False``.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the
    singular ``_at`` delegates, not the resolver's ``grace`` bit) --
    the whole point of the ``_at`` slot:
    ``/has-all-at-path?from=oss&to=enterprise&features=fleet`` shows
    the ``oss`` rung ``has_all_at=false`` even in grace (because OSS
    statically does not grant ``fleet``), whereas the LIVE
    ``/has-all?features=fleet`` reports ``true`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **Never 4xxs** on any input branch: missing / blank / unknown
      endpoints returns 200 with ``path=[]`` (``direction`` reads
      ``"unknown"``); no axes supplied returns 200 with the path still
      populated but every row's ``has_all_at=false`` (matches the
      singular ``/has-all-at`` empty-``False`` posture); unknown token /
      non-int capacity collapses every row to ``False`` with the
      offending token surfaced via ``unknown_features`` /
      ``unknown_runtimes``.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope (:func:`_has_all_at_path_fallback`) with
      ``path=[]`` so the pricing walkthrough keeps rendering.

    Envelope shape is fully documented on :func:`_has_all_at_path_body`.
    """
    try:
        return _shared.jsonify(_shared._has_all_at_path_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_at_path_fallback(
                from_tier,
                to_tier,
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-path-batch")
def api_entitlement_has_all_at_path_batch():
    """``GET /api/entitlement/has-all-at-path-batch?from=<id>&to=a,b,c
    &features=x,y&runtimes=p,q&channels=5&retention_days=30&nodes=2`` --
    aggregate mixed-axis batch-path boolean-fold sibling of
    ``/api/entitlement/has-all-at-path`` (single destination) and 5-axis
    extension of ``/api/entitlement/has-features-at-path-batch`` /
    ``/api/entitlement/has-runtimes-at-path-batch`` (per-axis batch path).

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    ``from`` and each of the N candidate ``to`` tiers, returning per-
    destination path lists of aggregate ``has_all_at`` fold rows -- the
    "from my current rung, here are 3 tiers I'm considering: for the
    WHOLE 5-axis bundle show me at which rung this bundle unlocks along
    every candidate path" matrix an upgrade-comparison surface needs,
    off ONE URL instead of N calls to ``/has-all-at-path``, or 5 * N
    calls fanned out across the per-axis path-batch endpoints plus a
    client-side AND-chain per rung per destination.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/has-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for
    the same triple. Per-destination path lengths can legitimately
    differ (the rungs walked depend on the destination), matching
    ``/has-features-at-path-batch`` / ``/has-runtimes-at-path-batch``
    posture. ``trial`` IS accepted as a destination (excluded from the
    walked intermediate rungs the way ``/has-all-at-path`` already
    excludes it, but is a valid endpoint via the lateral / identity
    branches).

    Envelope shape is fully documented on :func:`_has_all_at_path_batch_body`.

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/has-features-at-path-batch`` posture). Never 5xxs: any
    helper blowup collapses to :func:`_has_all_at_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_all_at_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_at_path_batch_fallback(
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-path-batch")
def api_entitlement_missing_all_at_path_batch():
    """``GET /api/entitlement/missing-all-at-path-batch?from=<id>&to=a,b,c
    &features=x,y&runtimes=p,q&channels=5&retention_days=30&nodes=2`` --
    aggregate mixed-axis batch-path row-detail sibling of
    ``/api/entitlement/missing-all-at-path`` (single destination),
    row-detail complement of ``/api/entitlement/has-all-at-path-batch``
    (paired boolean-fold batch-path), and 5-axis extension of
    ``/api/entitlement/missing-features-at-path-batch`` /
    ``/api/entitlement/missing-runtimes-at-path-batch``.

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    ``from`` and each of the N candidate ``to`` tiers, returning per-
    destination path lists of aggregate per-axis ``missing`` row-detail
    rows -- the "from my current rung, here are 3 tiers I'm considering:
    for the WHOLE 5-axis bundle show me which per-axis slots are still
    locked at every rung climbed to reach each" matrix an upgrade-
    comparison surface needs, off ONE URL instead of N calls to
    ``/missing-all-at-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/missing-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path``
    for the same triple. Per-destination path lengths can legitimately
    differ. ``trial`` IS accepted as a destination.

    Envelope shape is fully documented on
    :func:`_missing_all_at_path_batch_body`.

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``). Never 5xxs: any
    helper blowup collapses to
    :func:`_missing_all_at_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_all_at_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_at_path_batch_fallback(
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-from-path-batch")
def api_entitlement_has_all_from_path_batch():
    """``GET /api/entitlement/has-all-from-path-batch?from=a,b,c&to=<id>
    &features=x,y&runtimes=p,q&channels=5&retention_days=30&nodes=2`` --
    mirror-direction source-batch sibling of
    ``/api/entitlement/has-all-at-path-batch`` (destination-side batch),
    aggregate mixed-axis extension of
    ``/api/entitlement/has-features-from-path-batch`` /
    ``/api/entitlement/has-runtimes-from-path-batch`` (per-axis source-
    batch path).

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    each of the N candidate ``from`` tiers and the shared ``to`` tier,
    returning per-source path lists of aggregate ``has_all_at`` fold
    rows -- the "for each of the tiers my fleet currently sits on,
    walking up to Enterprise for the WHOLE 5-axis bundle, at which rung
    does this bundle unlock along every candidate ladder?" matrix a
    source-side upgrade-comparison surface needs, off ONE URL instead
    of N calls to ``/has-all-at-path``, or 5 * N calls fanned out across
    the per-axis source-batch endpoints plus a client-side AND-chain per
    rung per source.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/has-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for
    the same triple. Per-source path lengths can legitimately differ
    (the rungs walked depend on the source), matching
    ``/has-features-from-path-batch`` /
    ``/has-runtimes-from-path-batch`` /
    ``/has-all-at-path-batch`` posture. ``trial`` IS accepted as a
    source id (excluded from the walked intermediate rungs the way
    ``/has-all-at-path`` already excludes it, but is a valid endpoint
    via the lateral / identity branches).

    Envelope shape is fully documented on
    :func:`_has_all_from_path_batch_body`.

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-from-path-batch`` posture). Never 5xxs: any helper
    blowup collapses to :func:`_has_all_from_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._has_all_from_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_from_path_batch_fallback(
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-from-path-batch")
def api_entitlement_missing_all_from_path_batch():
    """``GET /api/entitlement/missing-all-from-path-batch?from=a,b,c&to=<id>
    &features=x,y&runtimes=p,q&channels=5&retention_days=30&nodes=2`` --
    mirror-direction source-batch sibling of
    ``/api/entitlement/missing-all-at-path-batch`` (destination-side
    batch), row-detail complement of
    ``/api/entitlement/has-all-from-path-batch`` (paired source-batch
    boolean-fold), and 5-axis extension of
    ``/api/entitlement/missing-features-from-path-batch`` /
    ``/api/entitlement/missing-runtimes-from-path-batch``.

    Fixes ONE 5-axis mixed bundle and sweeps across every rung between
    each of the N candidate ``from`` tiers and the shared ``to`` tier,
    returning per-source path lists of aggregate per-axis ``missing``
    row-detail rows -- the "for each of the tiers my fleet currently
    sits on, walking toward Enterprise for the WHOLE 5-axis bundle,
    which per-axis slots are still locked at every rung climbed to
    reach it?" matrix a source-side upgrade-comparison surface needs,
    off ONE URL instead of N calls to ``/missing-all-at-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/missing-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path``
    for the same triple. Per-source path lengths can legitimately
    differ. ``trial`` IS accepted as a source id.

    Envelope shape is fully documented on
    :func:`_missing_all_from_path_batch_body`.

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``). Never 5xxs: any
    helper blowup collapses to
    :func:`_missing_all_from_path_batch_fallback`.
    """
    try:
        return _shared.jsonify(_shared._missing_all_from_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_from_path_batch_fallback(
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-batch")
def api_entitlement_missing_all_at_batch():
    """``GET /api/entitlement/missing-all-at-batch?tiers=<a,b,...>
    &features=<x,y,...>&runtimes=<r,s,...>&channels=N&retention_days=K
    &nodes=M`` -- batch what-if row-detail complement of
    ``/api/entitlement/has-all-at-batch``.

    Row-detail sibling of ``/api/entitlement/has-all-at-batch`` on the
    aggregate what-if seat, in the same relationship
    ``/api/entitlement/missing-features-at-batch`` /
    ``/api/entitlement/missing-runtimes-at-batch`` have to
    ``/api/entitlement/has-features-at-batch`` /
    ``/api/entitlement/has-runtimes-at-batch`` on the single-axis seat.
    Where the paired boolean-fold sibling collapses each
    ``(perspective_tier, bundle)`` pair to ONE ``has_all_at`` bool, this
    returns WHAT is missing on each supplied axis for the same N
    perspectives in ONE round-trip so a paywall diagnostics matrix ("out
    of {fleet, sso, claude_code, 100 channels, 90d retention, 100 nodes},
    which axes are still blocked at OSS vs Cloud Starter vs Cloud Pro vs
    Enterprise?") hydrates the per-axis denial column off ONE URL
    instead of five ``_at-batch`` row-detail round-trips + a client-side
    per-axis stitch. Fills the ``_at_batch`` slot on the mixed-axis row-
    detail family alongside :func:`missing_all_at` (the singular per-
    perspective scalar) and ``/api/entitlement/missing-all`` (the LIVE
    per-install scalar).

    Every axis is OPTIONAL. Supply any non-empty subset; the row-detail
    answers off just those axes per row and every unsupplied axis is
    skipped (``missing.features`` / ``missing.runtimes`` -> ``[]`` on
    that row; capacity axis -> ``null``). Runtime-alias canonicalisation
    (``claude-code`` -> ``claude_code``) is applied per token upstream
    of the strict scalar. Capacity axes accept a single int (``5``);
    blank / non-int values swallow to ``null`` on every row's per-axis
    slot (matches the singular ``/missing-all-at`` capacity swallow
    posture); the paired ``/has-all-at-batch`` collapses every row's
    fold to ``False`` on the same input via the boolean scalar's
    strict-typo posture so a UI wiring both endpoints together gets a
    coherent "supplied but denied" story on the paired call.

    Perspective-shaped answers are **intentionally identical in grace
    and enforce** (they read the static per-tier tables via the singular
    ``_at`` delegates, not the resolver's ``grace`` bit) -- the whole
    point of the ``_at`` slot:
    ``/missing-all-at-batch?tiers=oss,cloud_pro&features=fleet`` returns
    the ``oss`` row's ``missing.features=["fleet"]`` even in grace
    (because OSS statically does not grant ``fleet``), whereas the LIVE
    ``/missing-all?features=fleet`` reports ``features=[]`` for it via
    :attr:`Entitlement.grace` pass-through.

    - **Never 4xxs** on any input branch: missing / blank / all-unknown
      ``tiers=`` returns 200 with ``tiers=[]`` (matches the sibling
      ``/missing-features-at-batch`` posture -- a paywall matrix binds
      ``tiers`` directly without a pre-validation round-trip). No axes
      supplied returns 200 with ``tiers`` still populated but every
      row's ``missing`` reporting the empty 5-key seat (matches the
      singular ``/missing-all-at`` empty-per-axis posture; distinct
      from the paired ``/has-all-at-batch`` which collapses every row's
      ``has_all_at`` to ``False`` on the same input for typo-``False``
      posture reasons -- see the paired doc). Unknown token in the
      bundle surfaces via ``unknown_features`` / ``unknown_runtimes``
      and folds into per-row ``any_missing``. Non-int capacity swallows
      to ``null`` on every row's per-axis slot; the paired
      ``/has-all-at-batch`` denies every row on the same input.
    - **Never 5xxs**: a resolver / scalar / body-builder blowup yields
      the fallback envelope with ``tiers=[]`` so the pricing walkthrough
      keeps rendering.

    Envelope shape is fully documented on
    :func:`_missing_all_at_batch_body`.

    Per-row parity is pinned by tests: each row's ``missing`` byte-
    equals :func:`missing_all_at` for the same ``(row.tier, bundle)``
    pair, and each row's per-axis denial byte-equals
    ``/api/entitlement/missing-all-at?tier=<row.tier>&...``'s ``missing``
    on the same bundle -- so any future contract change on either side
    has to update both. The paired boolean-fold sibling's per-row
    ``has_all_at`` is the strict negation of ``any(row.missing.values())``
    on every fully-parseable bundle (with the deliberate non-int
    capacity divergence documented on :func:`missing_all_at`).
    """
    try:
        return _shared.jsonify(_shared._missing_all_at_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_all_at_batch_fallback(
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all")
def api_entitlement_has_all():
    """``GET /api/entitlement/has-all?features=a,b&runtimes=x,y&channels=5&retention_days=30&nodes=2``
    -- aggregate mixed-axis boolean-gate scalar.

    Aggregate boolean sibling of ``/api/entitlement/required-tier`` (which
    resolves the cheapest tier that covers a mixed bundle across all five
    axes) and ``/api/entitlement/has-features`` / ``/has-runtimes`` (which
    fold ONE single-axis CSV to ONE boolean). A paywall diagnostics tile
    that gates on the full subscription state ("fleet + claude_code + 5
    channels + 30-day retention + 2 nodes -- does the resolved
    entitlement grant everything?") binds ``allowed`` directly off this
    URL without five singular ``/has-*`` round-trips + a client-side
    AND-chain.

    Every axis is OPTIONAL. Supply any non-empty subset; the fold
    answers off just those axes and every unsupplied axis is skipped
    (contributes ``True`` to the fold). Runtime-alias canonicalisation
    (``claude-code`` -> ``claude_code``) is applied per token before the
    known/unknown split. Capacity axes accept a single int (``5``);
    blank / non-int values collapse ``has_all`` to ``False`` (matches
    the singular capacity scalars' strict-``False`` typo posture).

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) ``has_all`` reports ``True`` for every fully-known
    bundle, so wiring this into a gate today changes NO current
    behavior. Never 4xxs (no axes supplied -> 200 with ``has_all=False``,
    matching the singular ``/has-features`` empty-``False`` posture).
    Never 5xxs (resolver blowup -> fallback envelope with
    ``has_all=False``).

    Envelope shape (19 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet"],           # known ids only
          "runtimes":            ["claude_code"],     # canonicalised, known only
          "channels":            5 | null,            # parsed int or null
          "retention_days":      30 | null,
          "nodes":               2 | null,
          "unknown_features":    ["bogus"],           # tokens not in ALL_FEATURES
          "unknown_runtimes":    [],                  # tokens not in ALL_RUNTIMES
          "supplied_axes":       ["features", "channels"],
          "supplied_count":      2,
          "has_all":             true,                # aggregate boolean
          "allowed":             true,                # alias of has_all
          "required_tier":       "cloud_pro" | null,
          "required_tier_label": "Pro" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "oss",
          "current_tier_rank":   0,
          "grace":               true,
          "enforced":            false,
          "upgrade_required":    <bool>
        }
    """
    try:
        return _shared.jsonify(_shared._has_all_body())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all: error: %s", exc)
        return _shared.jsonify(_shared._has_all_fallback())

@_shared.bp_entitlement.route("/api/entitlement/missing-all")
def api_entitlement_missing_all():
    """``GET /api/entitlement/missing-all?features=a,b&runtimes=x,y&channels=100&retention_days=90&nodes=100``
    -- row-detail complement of ``/api/entitlement/has-all``.

    Aggregate row-detail sibling of ``/api/entitlement/missing-features``
    (single-axis complement of ``/has-features``) and
    ``/api/entitlement/missing-runtimes`` at the mixed-axis rollup layer:
    where ``/has-all`` folds the bundle to ONE boolean, this preserves
    the per-axis denial detail so a paywall diagnostics tile ("you're
    missing fleet, sso, claude_code, +75 channels, +60 days retention,
    +99 nodes -- upgrade to Enterprise") binds every slot directly off
    ONE URL instead of walking the five singular ``/missing-*`` / capacity
    endpoints and stitching client-side.

    Every axis is OPTIONAL. Supply any non-empty subset; the response
    populates just those axes' missing slots and every unsupplied axis
    stays at its empty seat (``[]`` for grant axes, ``None`` for
    capacity axes). Runtime-alias canonicalisation (``claude-code`` ->
    ``claude_code``) is applied per token before the known/unknown
    split. Capacity axes accept a single int; blank / non-int values
    surface the raw string in that axis' slot (matches the singular
    ``missing_features`` scalar's typo-catches-at-callsite posture).

    Grace-safe: while :attr:`Entitlement.grace` is ``True`` (the current
    rollout state) every per-axis slot reports empty for every
    fully-known bundle -- matches the ``has_all=True`` grace answer on
    the same bundle -- so wiring this into a diagnostics tile today
    surfaces NOTHING. Never 4xxs (no axes supplied -> 200 with empty
    per-axis slots and ``any_missing=false``, matching ``/has-all``'s
    empty-``False`` posture). Never 5xxs (resolver blowup -> fallback
    envelope with empty per-axis slots and ``any_missing=false``).

    Envelope shape (19 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet", "sso"],   # missing grant ids
          "runtimes":            ["claude_code"],
          "channels":            100 | null,          # requested int if denied
          "retention_days":      90 | null,
          "nodes":               100 | null,
          "unknown_features":    ["bogus"],
          "unknown_runtimes":    [],
          "supplied_axes":       ["features", "channels"],
          "supplied_count":      2,
          "missing_count":       3,                   # total items across all axes
          "any_missing":         true,                # missing_count > 0
          "required_tier":       "enterprise" | null,
          "required_tier_label": "Enterprise" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "oss",
          "current_tier_rank":   0,
          "grace":               true,
          "enforced":            false,
          "upgrade_required":    <bool>
        }
    """
    try:
        return _shared.jsonify(_shared._missing_all_body())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all: error: %s", exc)
        return _shared.jsonify(_shared._missing_all_fallback())

@_shared.bp_entitlement.route("/api/entitlement/lock-reason")
def api_entitlement_lock_reason():
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_lock_reason: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-at")
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
        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_lock_reason_at: error: %s", exc)
        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime_in = (_shared.request.args.get("runtime") or "").strip().lower()
        channels_raw = (_shared.request.args.get("channels") or "").strip()
        retention_raw = (_shared.request.args.get("retention_days") or "").strip()
        nodes_raw = (_shared.request.args.get("nodes") or "").strip()
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
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/required-tier-batch")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, retention_raw) = _shared._parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")

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

        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_required_tier_batch: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
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

@_shared.bp_entitlement.route("/api/entitlement/required-tier-breakdown")
def api_entitlement_required_tier_breakdown():
    """``GET /api/entitlement/required-tier-breakdown?features=a,b&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-axis breakdown sibling of
    ``/api/entitlement/required-tier-batch``.

    Wraps :func:`entitlements.min_tier_for_all_breakdown`. Where
    ``/required-tier-batch`` collapses to a single ``required_tier`` id,
    this endpoint additionally returns each axis' individual ``min_tier``
    and calls out which axis (or axes, on a tie) is the *binding*
    constraint driving the aggregate floor -- so a paywall CTA can render
    "You need Pro *because* you have 8 channels (Starter caps at 5)" off
    ONE round-trip instead of five ``/required-tier`` calls + a
    client-side max-by-rank.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty /
    parseable after normalisation) -- otherwise 400. The three capacity
    axes accept a single int each; a blank or non-int value contributes
    nothing to the aggregate floor (the axis row still renders with
    ``min_tier=null`` so the caller can flag the bad input in a
    tooltip, matching the never-crash posture of the singular endpoint).
    ``retention_days=`` mirrors the strict :func:`min_tier_for_all`
    posture: an unset param is *unset*, NOT *unlimited* -- asking for
    the unlimited-retention floor is the singular
    ``/required-tier?retention_days=`` call's job.

    Response body::

        {
          "features":       [<normalised csv>],
          "runtimes":       [<normalised csv>],
          "channels":       <int> | null,
          "retention_days": <int> | null,
          "nodes":          <int> | null,
          "required_tier":       "cloud_pro" | null,
          "required_tier_label": "Pro" | null,
          "required_tier_rank":  <int>,      # -1 when required_tier is null
          "current_tier":        <resolved-tier>,
          "current_tier_rank":   <int>,
          "upgrade_required":    <bool>,
          "axes":         { <axis row per supplied kwarg> | null },
          "binding_axes": ["features", "channels"]  # ordered; empty on null
        }

    ``axes`` and ``binding_axes`` come straight from
    :func:`min_tier_for_all_breakdown`; see that helper's docstring for
    the row shape. The ``required_tier*`` / ``current_tier*`` /
    ``upgrade_required`` fields match ``/required-tier-batch`` exactly
    so a caller migrating from the batch endpoint can adopt the
    breakdown without reshaping its main paywall payload.

    Never 5xxs: the OSS-fallback shape is returned on any resolver
    failure.
    """
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (channels_present, channels_ok, channels_n, _) = _shared._parse_capacity_arg(
            "channels"
        )
        (retention_present, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (nodes_present, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_present
            and not retention_present
            and not nodes_present
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

        breakdown = _ent.min_tier_for_all_breakdown(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        ent = _ent.get_entitlement()
        required = breakdown.get("min_tier")
        required_label = breakdown.get("min_tier_label")
        req_rank = _ent.tier_rank(required) if required else -1
        cur_rank = _ent.tier_rank(ent.tier)

        return _shared.jsonify(
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
                "axes": breakdown.get("axes")
                or {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "binding_axes": breakdown.get("binding_axes") or [],
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_required_tier_breakdown: error: %s", exc
        )
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
                "axes": {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "binding_axes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-breakdown")
def api_entitlement_has_all_breakdown():
    """``GET /api/entitlement/has-all-breakdown?features=a,b&runtimes=x,y
    &channels=N&retention_days=K&nodes=M`` -- per-axis boolean-fold
    breakdown sibling of ``/api/entitlement/required-tier-breakdown``.

    Wraps :func:`entitlements.has_all_breakdown`. Where the reverse-
    lookup breakdown identifies which axis (or axes, on a tie) is
    *binding* the aggregate min-tier floor, this endpoint identifies
    which axis (or axes) is *blocking* the LIVE aggregate grant -- so
    a paywall diagnostics tile can render "denied here BECAUSE of
    channels (Starter caps at 5, you asked for 8)" off ONE round-trip
    instead of five ``/api/entitlement/has-*`` calls + a client-side
    which-axis-is-false walk. Pairs directly with
    ``/required-tier-breakdown`` on the same query args so a UI can
    render "denied because axis Y" alongside "cheapest tier that
    would grant it is Z because axis W".

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (non-empty /
    parseable after normalisation) -- otherwise 400. The three
    capacity axes accept a single int each; a blank or non-int value
    still surfaces the axis in the response (with ``has=false`` and
    the raw input in ``value`` so the caller can flag the typo in a
    tooltip), matching the never-crash posture of the singular
    ``/has-*`` endpoints. ``retention_days=`` mirrors the strict
    :func:`has_all` posture: an unset param is *unset*, NOT
    *unlimited* -- asking about the unlimited-retention live grant is
    the singular ``/api/entitlement/has-retention-window`` call's job.

    Response body::

        {
          "features":       [<normalised csv>],
          "runtimes":       [<normalised csv>],
          "channels":       <int> | null,
          "retention_days": <int> | null,
          "nodes":          <int> | null,
          "has_all":        <bool>,
          "current_tier":       <resolved-tier>,
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
          "axes":          { <axis row per supplied kwarg> | null },
          "blocking_axes": ["channels"]   # ordered; empty when has_all=true
        }

    ``axes`` and ``blocking_axes`` come straight from
    :func:`has_all_breakdown`; see that helper's docstring for the
    row shape. The ``current_tier*`` / ``grace`` / ``enforced``
    fields match the sibling ``/has-*`` endpoints so a caller
    migrating from the singular endpoints can adopt the breakdown
    without reshaping its diagnostics payload.

    Never 5xxs: the OSS-fallback shape is returned on any resolver
    failure (``has_all=false``, empty ``blocking_axes``, every axis
    ``null``).
    """
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (channels_present, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg(
            "channels"
        )
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (nodes_present, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_present
            and not retention_present
            and not nodes_present
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

        # A capacity arg that is present-but-unparseable still routes to
        # the helper (as the raw string) so the axis row surfaces with
        # ``has=false`` and ``value=<raw>``. Matches the never-crash
        # posture of the singular ``/has-*`` endpoints: a typo returns
        # a shape a UI can render, not a 400 wall.
        def _capacity_kw(present: bool, ok: bool, n: int | None, raw: str):
            if not present:
                return None
            if ok:
                return n
            return raw

        breakdown = _ent.has_all_breakdown(
            features=features or None,
            runtimes=runtimes or None,
            channels=_capacity_kw(channels_present, channels_ok, channels_n, channels_raw),
            retention_days=_capacity_kw(
                retention_present, retention_ok, retention_n, retention_raw
            ),
            nodes=_capacity_kw(nodes_present, nodes_ok, nodes_n, nodes_raw),
        )

        ent = _ent.get_entitlement()
        cur_rank = _ent.tier_rank(ent.tier)

        return _shared.jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else (channels_raw if channels_present else None),
                "retention_days": retention_n if retention_ok else (retention_raw if retention_present else None),
                "nodes": nodes_n if nodes_ok else (nodes_raw if nodes_present else None),
                "has_all": bool(breakdown.get("has_all")),
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "grace": bool(getattr(ent, "grace", False)),
                "enforced": not bool(getattr(ent, "grace", False)),
                "axes": breakdown.get("axes")
                or {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "blocking_axes": breakdown.get("blocking_axes") or [],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_breakdown: error: %s", exc)
        (channels_present, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg(
            "channels"
        )
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (nodes_present, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else (channels_raw if channels_present else None),
                "retention_days": retention_n if retention_ok else (retention_raw if retention_present else None),
                "nodes": nodes_n if nodes_ok else (nodes_raw if nodes_present else None),
                "has_all": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
                "axes": {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "blocking_axes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at")
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
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "features": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "feature-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at")
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
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "runtimes": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "runtime-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at")
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
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "tiers": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "tier-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.tier_catalog_at_batch(tiers)
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
            "api_entitlement_tier_catalog_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.feature_catalog_at_batch(tiers)
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
            "api_entitlement_feature_catalog_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_catalog_at_batch(tiers)
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
            "api_entitlement_runtime_catalog_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at")
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
        if target not in _ent._TIER_ORDER:
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
        body = _ent.tier_spec_at(tier, target)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-spec-at failed",
                        "tier": tier,
                        "target": target,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "target": target, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "tier-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
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
        body = _ent.feature_spec_at(tier, feature)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "feature-spec-at failed",
                        "tier": tier,
                        "feature": feature,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "feature": feature, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "feature-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_runtime = _shared.request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
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
        body = _ent.runtime_spec_at(tier, rt)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "runtime-spec-at failed",
                        "tier": tier,
                        "runtime": rt,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "runtime": rt, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "runtime-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/feature-spec")
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
    raw = _shared.request.args.get("feature")
    feature = (raw or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_spec(feature)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown feature", "feature": feature}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec: error: %s", exc)
        return _shared.jsonify({"error": "feature-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec")
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
    raw = _shared.request.args.get("runtime")
    runtime = (raw or "").strip().lower()
    if not runtime:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_spec(runtime)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown runtime", "runtime": runtime}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec: error: %s", exc)
        return _shared.jsonify({"error": "runtime-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec")
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
    raw = _shared.request.args.get("channel")
    channel = (raw or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.channel_spec(channel)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown channel", "channel": channel}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec: error: %s", exc)
        return _shared.jsonify({"error": "channel-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-batch")
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
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return (
                _shared.jsonify({"error": "supply channels=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.channel_spec_batch(channels)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "channels": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_channel = _shared.request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
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
        body = _ent.channel_spec_at(tier, channel)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "channel-spec-at failed",
                        "tier": tier,
                        "channel": channel,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "channel": channel, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "channel-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at-batch")
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
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return (
                _shared.jsonify({"error": "supply channels=<csv>"}),
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_channel_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-batch")
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
        features = _shared._parse_csv_arg("features")
        if not features:
            return (
                _shared.jsonify({"error": "supply features=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.feature_spec_batch(features)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "features": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return (
                _shared.jsonify({"error": "supply runtimes=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_spec_batch(runtimes)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "runtimes": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at-batch")
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_spec_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at-batch")
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
        if not features:
            return (
                _shared.jsonify({"error": "supply features=<csv>"}),
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_feature_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return (
                _shared.jsonify({"error": "supply runtimes=<csv>"}),
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
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at")
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

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
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
        row = _ent.tier_unlocks_at(tier_in, target_in)
        if row is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-unlocks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_unlocks_at: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "tier-unlocks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at")
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

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
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
        row = _ent.tier_locks_at(tier_in, target_in)
        if row is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-locks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_locks_at: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "tier-locks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at-batch")
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
        rows = _ent.tier_unlocks_at_batch(tier_in) or []
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
        _shared.logger.warning("api_entitlement_tier_unlocks_at_batch: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at-batch")
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
        rows = _ent.tier_locks_at_batch(tier_in) or []
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
        _shared.logger.warning("api_entitlement_tier_locks_at_batch: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers")
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

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days",
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

        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_affordable_tiers: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
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

@_shared.bp_entitlement.route("/api/entitlement/required-tier-at")
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
            "retention_days",
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

        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_required_tier_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
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

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers-at")
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
            "retention_days",
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

        return _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_affordable_tiers_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
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
