"""routes/entitlement/_endpoints_06.py — endpoint handlers api_entitlement_feature_catalog_at_path_batch .. api_entitlement_channel_catalog_at_path_batch.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at-path-batch")
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
            "api_entitlement_feature_catalog_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-path-batch")
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
        features = _shared._parse_csv_arg("features")
        if not features:
            return _shared.jsonify({"error": "supply features=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_feature_spec_path_batch: error: %s", exc
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
                "features": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-path-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return _shared.jsonify({"error": "supply runtimes=<csv>"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_runtime_spec_path_batch: error: %s", exc
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
                "runtimes": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at-path")
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
    rt_raw = (_shared.request.args.get("runtime") or "").strip()
    if not rt_raw:
        return _shared.jsonify({"error": "missing runtime"}), 400
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
        rt = _ent.canonical_runtime(rt_raw)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
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
                "runtime": rt,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec_at_path: error: %s", exc)
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
                "runtime": rt_raw.lower(),
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at-path-batch")
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
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return _shared.jsonify({"error": "supply runtimes=<csv>"}), 400
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
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_spec_at_path_batch: error: %s", exc
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
                "runtimes": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-path-batch")
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
    30 runtimes + my channel count + my retention window, walk each one
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_lock_reason_path_batch: error: %s", exc
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
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "unknown": {"features": [], "runtimes": []},
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-spec-at-batch")
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
    return _shared._next_prev_tier_feature_spec_at_batch("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-spec-at-batch")
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
    return _shared._next_prev_tier_feature_spec_at_batch("previous")

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-spec-at-batch")
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
    return _shared._next_prev_tier_runtime_spec_at_batch("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-spec-at-batch")
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
    return _shared._next_prev_tier_runtime_spec_at_batch("previous")

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-spec-at-batch")
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

    Use case: a pricing-comparison "here are the 23 chat channels I
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
    return _shared._next_prev_tier_channel_spec_at_batch("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-spec-at-batch")
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
    return _shared._next_prev_tier_channel_spec_at_batch("previous")

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-path-batch")
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
        batch = _ent.capacity_diff_path_batch(f, targets)
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
            "api_entitlement_capacity_diff_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-path-batch")
def api_entitlement_capacity_headroom_path_batch():
    """``GET /api/entitlement/capacity-headroom-path-batch?from=<id>&to=a,b,c
    &channels=<int>&retention_days=<int>&nodes=<int>`` -- batch sibling of
    ``/api/entitlement/capacity-headroom-path``.

    Where ``/capacity-headroom-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between ONE ``from`` and N
    candidate ``to`` tiers in ONE round-trip. Pairs with
    ``/capacity-headroom-path`` the same way ``/capacity-diff-path-batch``
    pairs with ``/capacity-diff-path``: scalar -> matrix in one call.
    Headroom-shaped twin of ``/capacity-diff-path-batch`` (same fan-out
    shape, per-axis headroom body instead of marginal-transition body).

    Use case: a capacity-only pricing-comparison "from my current rung,
    here are the 3 tiers I'm considering -- watch my headroom recover rung
    by rung on the way to each" surface hydrates the per-rung headroom
    envelopes to every candidate off ONE call instead of N calls to
    ``/capacity-headroom-path``. Same-rank siblings strictly between the
    endpoints are included for each per-destination path; same-rank
    siblings of each destination are excluded so the per-destination path
    terminates exactly at its own ``to``. Per-destination path lengths can
    legitimately differ (the rungs walked depend on the destination),
    matching ``/capacity-diff-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/capacity-headroom-path?from=<from>&to=<to>&...`` -- pinned by the
    parity tests so the scalar and batch path accessors cannot drift.
    Supplied destination ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved). Unknown
    ids do not 404 the call -- they are echoed in ``unknown[]`` so a
    partially-bad caller still gets paths back for the valid ids.

    Per-axis ``None`` on every row means "axis not supplied" (matches
    ``/capacity-headroom-path``'s posture). A blank, non-int, negative, or
    ``bool``-in-disguise value on any axis short-circuits that axis to
    ``None`` on every row of every destination -- a stray query string
    cannot silently blank the whole matrix.

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
              "path":      [<capacity-headroom row>, ...],
            },
            ...
          ],
          "unknown":    ["bogus_id", ...],
        }

    - **400** when ``from=`` is missing / blank, or ``to=`` is missing /
      empty after normalisation
    - **404** when ``from`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown destination ids -- does
      NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an envelope
      with empty rows so the matrix keeps rendering.

    Decoupled from the resolved entitlement -- every rung walks the static
    per-tier caps via :func:`entitlements.capacity_headroom_at` -- so grace
    vs enforce yields byte-identical ``path`` payloads.
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
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        batch = _ent.capacity_headroom_path_batch(f, targets, **kwargs)
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
            "api_entitlement_capacity_headroom_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-at-path")
def api_entitlement_capacity_headroom_at_path():
    """``GET /api/entitlement/capacity-headroom-at-path?tier=<perspective>
    &from=<from>&to=<to>&channels=<int>&retention_days=<int>&nodes=<int>``
    -- per-rung capacity-headroom envelope along an arbitrary
    ``from -> to`` segment, rendered from a hypothetical
    ``perspective_tier``.

    What-if sibling of ``/capacity-headroom-path``: same rung walk, same
    per-rung headroom body (``tier`` / ``tier_label`` / ``channels`` /
    ``retention_days`` / ``nodes`` where each per-axis row matches the
    :func:`entitlements._headroom_row` shape), plus a ``perspective_tier``
    echo so a pricing-comparison walkthrough surface can call
    ``X_at_path(perspective, from, to)`` uniformly across the whole
    ``_at_path`` slot of the capacity-headroom family (alongside
    ``/capacity-headroom-at`` and ``/capacity-headroom-batch``, which
    fill the scalar-what-if and batch-what-if slots). Headroom-shaped
    mirror of ``/capacity-diff-at-path`` -- same posture, per-axis usage
    rows instead of marginal-transition rows.

    Body posture matches ``/capacity-headroom-at``: perspective is
    validated but does not shape the rows. Each row in ``path`` is
    byte-identical to a row from
    ``/capacity-headroom-path?from=<from>&to=<to>`` -- pinned by parity
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
          "path":                  [<capacity-headroom row>, ...],
          "current_tier":          "<tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,
          "enforced":              <bool>,
        }

    Per-axis ``None`` on every row means "axis not supplied" (matches
    ``/capacity-headroom-path``'s posture). A blank, non-int, negative,
    or ``bool``-in-disguise value on any axis short-circuits that axis
    to ``None`` on every row -- a stray query string cannot silently
    blank the whole walk.

    - **400** when ``tier=``, ``from=`` or ``to=`` is missing / blank
    - **404** when any id is unknown (body carries ``which: "tier" |
      "from" | "to"`` so the caller can point at the offender)
    - **Never 5xxs**: a resolver failure short-circuits to 404 so a
      capacity-only pricing-comparison walkthrough surface keeps
      rendering instead of breaking.
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
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        path = _ent.capacity_headroom_at_path(p, f, t, **kwargs)
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
            "api_entitlement_capacity_headroom_at_path: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/capacity-headroom-at-path-batch")
def api_entitlement_capacity_headroom_at_path_batch():
    """``GET /api/entitlement/capacity-headroom-at-path-batch?tier=<perspective>
    &from=<from>&to=a,b,c&channels=<int>&retention_days=<int>&nodes=<int>``
    -- batch sibling of ``/capacity-headroom-at-path``.

    Where ``/capacity-headroom-at-path`` walks the headroom rungs between
    ONE ``(from, to)`` pair from a hypothetical ``perspective_tier``, this
    walks ONE ``from`` to N candidate ``to`` tiers in ONE round-trip from
    the same hypothetical perspective -- the batch what-if sibling of
    ``/capacity-headroom-path-batch``, filling the ``_at_path_batch`` slot
    for the capacity-headroom family. Headroom-shaped twin of
    ``/capacity-diff-at-path-batch`` (same fan-out shape, per-axis
    headroom body instead of marginal-transition body).

    Body posture matches ``/capacity-headroom-at``: perspective is
    validated but does not shape rows. Each row in ``tiers[].path`` is
    byte-identical to a row from ``/capacity-headroom-path-batch`` for
    the same ``(from, to)`` pair with the same per-axis usage inputs --
    pinned by parity tests. Perspective acceptance is lenient: ``trial``
    IS accepted (matching every other ``_at`` sibling).

    Response shape (mirrors ``/capacity-headroom-path-batch`` plus the
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
              "path":      [<capacity-headroom row>, ...],
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
    lowercased, duplicates dropped, first-seen order preserved). Unknown
    destination ids do NOT 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for the
    valid ids alongside a list of what was dropped, matching every other
    ``*_path_batch`` sibling's posture.

    Per-axis ``None`` on every row means "axis not supplied" (matches
    ``/capacity-headroom-path-batch``'s posture). A blank, non-int,
    negative, or ``bool``-in-disguise value on any axis short-circuits
    that axis to ``None`` on every row of every destination -- a stray
    query string cannot silently blank the whole matrix.

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
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        batch = _ent.capacity_headroom_at_path_batch(p, f, targets, **kwargs)
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
            "api_entitlement_capacity_headroom_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-path-batch")
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
        batch = _ent.tier_unlocks_path_batch(f, targets)
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
            "api_entitlement_tier_unlocks_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-path-batch")
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
        batch = _ent.tier_locks_path_batch(f, targets)
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
            "api_entitlement_tier_locks_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-from-path-batch")
def api_entitlement_tier_unlocks_from_path_batch():
    """``GET /api/entitlement/tier-unlocks-from-path-batch?from=a,b,c&to=<id>``
    -- source-axis batch sibling of ``/api/entitlement/tier-unlocks-path``.

    Where ``/tier-unlocks-path`` walks the rungs between ONE
    ``(from, to)`` pair, this walks the rungs between N candidate
    sources and ONE ``to`` in ONE round-trip. Mirror-direction twin of
    ``/tier-unlocks-path-batch`` (which fans out over destinations);
    marginal-grant source-batch companion of
    ``/tier-locks-from-path-batch`` (locks) and same relationship
    ``/has-features-from-path-batch`` has to
    ``/has-features-at-path-batch``.

    Use case: a fleet-view "for each of the tiers my nodes currently
    sit on, show me the newly-unlocked features + runtimes at every
    rung climbed to reach Enterprise" surface hydrates the per-rung
    marginal unlocks for every source off ONE call instead of N calls
    to ``/tier-unlocks-path``. Same-rank siblings strictly between
    each ``(from, to)`` pair are included in each per-source path;
    same-rank siblings of the shared ``to`` are excluded so each per-
    source path terminates exactly at ``to``. Per-source path lengths
    can legitimately differ (the rungs walked depend on the source),
    matching ``/tier-unlocks-path-batch`` /
    ``/has-features-from-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-unlocks-path?from=<from>&to=<to>`` -- pinned by parity
    tests so the scalar and source-batch path accessors cannot drift.
    Supplied source ids are normalised (whitespace stripped,
    lowercased, duplicates dropped, first-seen order preserved).
    Unknown ids do not 404 the call -- they are echoed in
    ``unknown[]`` so a partially-bad caller still gets paths back for
    the valid ids.

    Response shape::

        {
          "to":       "<tier id>",
          "to_label": "...",
          "to_rank":  <int>,
          "tiers": [
            {
              "from":       "<tier id>",
              "from_label": "...",
              "from_rank":  <int>,
              "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
              "path":       [<tier-unlocks row>, ...],
            },
            ...
          ],
          "unknown":  ["bogus_id", ...],
        }

    - **400** when ``to=`` is missing / blank, or ``from=`` is missing
      / empty after normalisation
    - **404** when ``to`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown source ids -- does
      NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an
      envelope with empty rows so the matrix keeps rendering.
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400
        batch = _ent.tier_unlocks_from_path_batch(sources, t)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_unlocks_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-from-path-batch")
def api_entitlement_tier_locks_from_path_batch():
    """``GET /api/entitlement/tier-locks-from-path-batch?from=a,b,c&to=<id>``
    -- source-axis batch sibling of ``/api/entitlement/tier-locks-path``.

    Marginal-loss mirror of ``/tier-unlocks-from-path-batch`` (same
    source-batch axis, per-rung locks body instead of unlocks body)
    and source-axis twin of ``/tier-locks-path-batch`` (which fans
    over destinations). Same envelope, same per-source row shape, same
    unknown-bucketing posture as ``/tier-unlocks-from-path-batch`` --
    only the inner ``path`` list changes body.

    Use case: a fleet-consolidation "for each tier a node might drop
    to, show me the losses at every rung walked down from where each
    node currently sits" surface hydrates the per-rung marginal losses
    for every source off ONE call instead of N calls to
    ``/tier-locks-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/tier-locks-path?from=<from>&to=<to>`` -- pinned by parity tests
    so the scalar and source-batch path accessors cannot drift.

    Response shape mirrors ``/tier-unlocks-from-path-batch`` with the
    per-rung body swapped for tier-locks rows. Never 4xxs / 5xxs
    beyond the same short-circuit set (missing / unknown ``to`` ->
    400 / 404; helper blowup -> 200 with empty rows).
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400
        batch = _ent.tier_locks_from_path_batch(sources, t)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_locks_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/preview-from-path-batch")
def api_entitlement_preview_from_path_batch():
    """``GET /api/entitlement/preview-from-path-batch?from=a,b,c&to=<id>``
    -- source-axis batch sibling of ``/api/entitlement/preview-path``.

    Where ``/preview-path`` walks the rungs between ONE
    ``(from, to)`` pair carrying the cumulative ``Entitlement.to_dict``
    snapshot per rung, this walks the rungs between N candidate
    sources and ONE ``to`` in ONE round-trip. Mirror-direction twin of
    ``/preview-path-batch`` (which fans out over destinations);
    cumulative-state source-batch companion of
    ``/tier-unlocks-from-path-batch`` (marginal grants) /
    ``/tier-locks-from-path-batch`` (marginal losses) on the same
    source-batch axis, and same relationship
    ``/has-features-from-path-batch`` has to
    ``/has-features-at-path-batch``.

    Use case: a fleet-consolidation "for each tier my nodes currently
    sit on, show me the full Entitlement snapshot at every rung
    walked to reach Cloud Pro" surface hydrates the per-rung
    cumulative snapshot for every source off ONE call instead of N
    calls to ``/preview-path``. Same-rank siblings strictly between
    each ``(from, to)`` pair are included in each per-source path;
    same-rank siblings of the shared ``to`` are excluded so each per-
    source path terminates exactly at ``to``. Per-source path lengths
    can legitimately differ (the rungs walked depend on the source),
    matching ``/preview-path-batch`` /
    ``/tier-unlocks-from-path-batch``'s posture.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/preview-path?from=<from>&to=<to>`` -- pinned by parity tests so
    the scalar and source-batch path accessors cannot drift. Supplied
    source ids are normalised (whitespace stripped, lowercased,
    duplicates dropped, first-seen order preserved). Unknown ids do
    not 404 the call -- they are echoed in ``unknown[]`` so a
    partially-bad caller still gets paths back for the valid ids.

    Response shape::

        {
          "to":       "<tier id>",
          "to_label": "...",
          "to_rank":  <int>,
          "tiers": [
            {
              "from":       "<tier id>",
              "from_label": "...",
              "from_rank":  <int>,
              "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
              "path":       [<preview row>, ...],
            },
            ...
          ],
          "unknown":  ["bogus_id", ...],
        }

    - **400** when ``to=`` is missing / blank, or ``from=`` is missing
      / empty after normalisation
    - **404** when ``to`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown source ids -- does
      NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an
      envelope with empty rows so the matrix keeps rendering.
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400
        batch = _ent.preview_from_path_batch(sources, t)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_preview_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/capacity-diff-from-path-batch")
def api_entitlement_capacity_diff_from_path_batch():
    """``GET /api/entitlement/capacity-diff-from-path-batch?from=a,b,c&to=<id>``
    -- source-axis batch sibling of ``/api/entitlement/capacity-diff-path``.

    Capacity-slice mirror of ``/preview-from-path-batch`` (same
    source-batch axis, per-rung capacity body instead of the full
    cumulative snapshot) and source-axis twin of
    ``/capacity-diff-path-batch`` (which fans over destinations). Same
    envelope, same per-source row shape, same unknown-bucketing
    posture as ``/preview-from-path-batch`` -- only the inner
    ``path`` list changes body.

    Use case: a fleet-consolidation "for each tier a node currently
    sits on, show me the channels / retention / nodes bumps at every
    rung walked to reach Enterprise" surface hydrates the per-rung
    capacity walk for every source off ONE call instead of N calls to
    ``/capacity-diff-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/capacity-diff-path?from=<from>&to=<to>`` -- pinned by parity
    tests so the scalar and source-batch path accessors cannot drift.

    Response shape mirrors ``/preview-from-path-batch`` with the per-
    rung body swapped for capacity-diff rows. Never 4xxs / 5xxs
    beyond the same short-circuit set (missing / unknown ``to`` ->
    400 / 404; helper blowup -> 200 with empty rows).
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400
        batch = _ent.capacity_diff_from_path_batch(sources, t)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_capacity_diff_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-from-path-batch")
def api_entitlement_lock_reason_from_path_batch():
    """``GET /api/entitlement/lock-reason-from-path-batch?from=a,b,c
    &to=<id>&<axis>=<value>`` -- source-axis batch sibling of
    ``/api/entitlement/lock-reason-path``.

    Where ``/lock-reason-path`` walks the rungs between ONE
    ``(from, to)`` pair for ONE item, this fixes the destination and
    the item and fans out over N candidate sources in ONE round-trip.
    Mirror-direction twin of ``/lock-reason-path`` on the source axis;
    per-item, per-source companion of
    ``/tier-unlocks-from-path-batch`` / ``/tier-locks-from-path-batch``
    (marginal grants / losses) and ``/preview-from-path-batch`` /
    ``/capacity-diff-from-path-batch`` (cumulative state / capacity
    slice) -- same source-batch envelope, per-rung ``locked`` /
    ``allowed`` / ``reason`` body instead.

    Use case: a fleet-view "for each of the tiers my nodes currently
    sit on, does THIS one paywalled item stay locked at every rung
    climbed to reach Enterprise?" surface hydrates the per-rung lock
    row for every source off ONE call instead of N calls to
    ``/lock-reason-path``. Per-source path lengths can legitimately
    differ (the rungs walked depend on the source), matching every
    other ``/*-from-path-batch`` sibling.

    Exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied -- the same axis
    dispatcher as ``/lock-reason-path``.

    Each row in ``tiers[].path`` is byte-identical to a row from
    ``/lock-reason-path?from=<from>&to=<to>&<axis>=<value>`` -- pinned
    by parity tests so the scalar and source-batch path accessors
    cannot drift. Supplied source ids are normalised (whitespace
    stripped, lowercased, duplicates dropped, first-seen order
    preserved). Unknown source ids do not 404 the call -- they are
    echoed in ``unknown[]`` so a partially-bad caller still gets paths
    back for the valid ids.

    Response shape::

        {
          "to":       "<tier id>",
          "to_label": "...",
          "to_rank":  <int>,
          "key":      "<echoed item id>",
          "kind":     "feature" | "runtime" | "channels" |
                      "retention_days" | "nodes",
          "tiers": [
            {
              "from":       "<tier id>",
              "from_label": "...",
              "from_rank":  <int>,
              "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
              "path":       [<lock_reason_path row>, ...],
            },
            ...
          ],
          "unknown":  ["bogus_id", ...],
        }

    - **400** when ``to=`` is missing / blank, when ``from=`` is
      missing / empty after normalisation, when no axis is supplied,
      or when more than one axis is supplied
    - **404** when ``to`` is unknown (body carries ``which: "tier"``),
      or when the item id is unknown / non-positive for a capacity
      axis
    - **200** with bucketed unknowns for unknown source ids -- does
      NOT 404 the call, matching every other batch sibling
    - **Never 5xxs**: a synthesis failure short-circuits to an
      envelope with empty rows so the matrix keeps rendering.
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400

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

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400

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
                            "to": t,
                            "key": nodes_raw,
                            "kind": "nodes",
                        }
                    ),
                    404,
                )
            item, kind, echoed_key = str(nodes_n), "nodes", str(nodes_n)

        batch = _ent.lock_reason_from_path_batch(sources, t, item, kind=kind)
        if batch is None:
            # A None here means the item itself is unknown / non-positive
            # (source pre-flight would have echoed bogus sources into
            # ``unknown[]``, not collapsed the batch). Surface as 404 so
            # the paywall UI can render "no such feature / runtime /
            # capacity" cleanly.
            return (
                _shared.jsonify(
                    {
                        "error": "unknown tier or item",
                        "to": t,
                        "key": echoed_key,
                        "kind": kind,
                    }
                ),
                404,
            )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "key": echoed_key,
                "kind": kind,
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_lock_reason_from_path_batch: error: %s", exc
        )
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
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "key": echoed_key,
                "kind": kind,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/lock-reasons-from-path-batch")
def api_entitlement_lock_reasons_from_path_batch():
    """``GET /api/entitlement/lock-reasons-from-path-batch?from=a,b,c
    &to=<id>&features=x,y&runtimes=p,q&channels=N&retention_days=K
    &nodes=M`` -- multi-axis source-batch sibling of
    ``/api/entitlement/lock-reason-path-batch``.

    Where ``/lock-reason-path-batch`` walks N items across all 5 axes
    for ONE ``(from, to)`` pair, this fixes the destination and fans
    out over M candidate sources with the same multi-axis body per
    source in ONE round-trip. Source-axis fan-out companion of
    ``/lock-reason-path-batch`` -- the ``lock-reason`` axis's answer
    to ``/tier-unlocks-from-path-batch`` /
    ``/tier-locks-from-path-batch`` (single-slice source batches) with
    the whole 5-axis matrix preserved per source.

    Use case: a fleet-consolidation "for each of the 4 tiers our
    nodes currently sit on, walk the whole (features + runtimes +
    capacity) lock matrix up to Enterprise" surface hydrates every
    source column of the matrix off ONE call instead of M calls to
    ``/lock-reason-path-batch``.

    At least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=`` must be supplied (matches
    ``/lock-reason-path-batch``). CSV bundles are canonicalised once
    at the top so every per-source delegate sees the same iterable.

    Response shape wraps ``/lock-reason-path-batch``'s multi-axis
    payload per source::

        {
          "to":       "<tier id>",
          "to_label": "...",
          "to_rank":  <int>,
          "tiers": [
            {
              "from":       "<tier id>",
              "from_label": "...",
              "from_rank":  <int>,
              "direction":  "upgrade" | "downgrade" | "lateral" | "identity",
              "matrix": {
                "features": [{"key": "<id>", "path": [...]}, ...],
                "runtimes": [{"key": "<canonical id>", "path": [...]}, ...],
                "channels":       {"key": "<n>", "path": [...]} | None,
                "retention_days": {"key": "<n>", "path": [...]} | None,
                "nodes":          {"key": "<n>", "path": [...]} | None,
                "unknown": {"features": [...], "runtimes": [...]},
              },
            },
            ...
          ],
          "unknown":  ["bogus_id", ...],
        }

    Each per-source ``matrix`` is byte-identical to
    ``/lock-reason-path-batch?from=<from>&to=<to>&features=&runtimes=&...``
    for the corresponding source -- pinned by parity tests so the
    source-batch and scalar-batch multi-axis accessors cannot drift.

    - **400** when ``to=`` is missing / blank, when ``from=`` is
      missing / empty after normalisation, or when no axis is
      supplied
    - **404** when ``to`` is unknown (body carries ``which: "tier"``)
    - **200** with bucketed unknowns for unknown source ids (outer
      ``unknown[]``) and unknown item ids (per-source
      ``matrix.unknown``) -- does NOT 404 the call
    - **Never 5xxs**: a synthesis failure short-circuits to an
      envelope with empty rows so the matrix keeps rendering.
    """
    t = (_shared.request.args.get("to") or "").strip().lower()
    if not t:
        return _shared.jsonify({"error": "missing to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if t not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": t}
                ),
                404,
            )
        sources = _shared._parse_csv_arg("from")
        if not sources:
            return _shared.jsonify({"error": "supply from=<csv>"}), 400

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

        batch = _ent.lock_reasons_from_path_batch(
            sources,
            t,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        return _shared.jsonify(
            {
                "to": t,
                "to_label": _ent.tier_label(t),
                "to_rank": _ent.tier_rank(t),
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_lock_reasons_from_path_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "to": t,
                "to_label": None,
                "to_rank": -1,
                "tiers": [],
                "unknown": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-path-batch")
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
        batch = _ent.tier_path_batch(f, targets)
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
            "api_entitlement_tier_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/preview-path-batch", methods=["POST"])
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
    body = _shared.request.get_json(silent=True) or {}
    try:
        f_raw = body.get("from")
        f = str(f_raw or "").strip().lower()
    except Exception:
        f = ""
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    to_raw = body.get("to")
    if to_raw is None or (isinstance(to_raw, (list, tuple)) and not to_raw):
        return _shared.jsonify({"error": "missing or empty to"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "from", "from": f}
                ),
                404,
            )
        try:
            candidates = [str(t) for t in (to_raw or [])]
        except TypeError:
            return _shared.jsonify({"error": "to must be a list"}), 400
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_preview_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.feature_catalog_path_batch(f, targets)
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
            "api_entitlement_feature_catalog_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.runtime_catalog_path_batch(f, targets)
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
            "api_entitlement_runtime_catalog_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-path-batch")
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
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    try:
        from clawmetry import entitlements as _ent

        if f not in _ent._TIER_FEATURES:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": f}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.channel_catalog_path_batch(f, targets)
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
            "api_entitlement_channel_catalog_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-diff")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_diff: error: %s", exc
        )
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "row": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff")
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
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_diff: error: %s", exc
        )
        return _shared.jsonify(
            {
                "current_tier": "oss",
                "current_tier_label": "OSS",
                "current_tier_rank": 0,
                "row": None,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-diff")
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
        return _shared.jsonify({
            "current_tier": ent.tier,
            "current_tier_label": _ent.tier_label(ent.tier),
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "row": body,
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        })
    except Exception as exc:
        _shared.logger.warning("api_entitlement_next_tier_diff: error: %s", exc)
        return _shared.jsonify({"current_tier": "oss", "current_tier_label": "OSS",
                        "current_tier_rank": 0, "row": None, "grace": True, "enforced": False})

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-diff")
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
        return _shared.jsonify({
            "current_tier": ent.tier,
            "current_tier_label": _ent.tier_label(ent.tier),
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "row": body,
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        })
    except Exception as exc:
        _shared.logger.warning("api_entitlement_previous_tier_diff: error: %s", exc)
        return _shared.jsonify({"current_tier": "oss", "current_tier_label": "OSS",
                        "current_tier_rank": 0, "row": None, "grace": True, "enforced": False})

@_shared.bp_entitlement.route("/api/entitlement/next-tier-lock-reason-batch")
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
    return _shared._next_prev_lock_reason_batch("next")

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-lock-reason-batch")
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
    return _shared._next_prev_lock_reason_batch("previous")

@_shared.bp_entitlement.route("/api/entitlement/preview-at-path")
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
                _shared.jsonify({"error": "unknown tier", "which": "to", "to": t}),
                404,
            )
        path = _ent.preview_at_path(p, f, t)
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
        _shared.logger.warning("api_entitlement_preview_at_path: error: %s", exc)
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

@_shared.bp_entitlement.route(
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
    body = _shared.request.get_json(silent=True) or {}
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
        return _shared.jsonify({"error": "missing tier"}), 400
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
    to_raw = body.get("to")
    if to_raw is None or (isinstance(to_raw, (list, tuple)) and not to_raw):
        return _shared.jsonify({"error": "missing or empty to"}), 400
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
        try:
            candidates = [str(x) for x in (to_raw or [])]
        except TypeError:
            return _shared.jsonify({"error": "to must be a list"}), 400
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
            "api_entitlement_preview_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at-path")
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
    feat = (_shared.request.args.get("feature") or "").strip().lower()
    if not feat:
        return _shared.jsonify({"error": "missing feature"}), 400
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
        if feat not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
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
                "feature": feat,
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec_at_path: error: %s", exc)
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
                "feature": feat,
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at-path-batch")
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
        features = _shared._parse_csv_arg("features")
        if not features:
            return _shared.jsonify({"error": "supply features=<csv>"}), 400
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
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_feature_spec_at_path_batch: error: %s", exc
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
                "features": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at-path")
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
                "path": path,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_spec_at_path: error: %s", exc)
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
                "path": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at-path-batch")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    f = (_shared.request.args.get("from") or "").strip().lower()
    if not f:
        return _shared.jsonify({"error": "missing from"}), 400
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
        targets = _shared._parse_csv_arg("to")
        if not targets:
            return _shared.jsonify({"error": "supply to=<csv>"}), 400
        batch = _ent.tier_spec_at_path_batch(tier_in, f, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        ent = _ent.get_entitlement()
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_tier_spec_at_path_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at-path")
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
        path = _ent.runtime_catalog_at_path(p, f, t)
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
            "api_entitlement_runtime_catalog_at_path: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at-path-batch")
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
            "api_entitlement_runtime_catalog_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-at-path")
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
        path = _ent.channel_catalog_at_path(p, f, t)
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
            "api_entitlement_channel_catalog_at_path: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-at-path-batch")
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
            "api_entitlement_channel_catalog_at_path_batch: error: %s", exc
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

