"""routes/entitlement/_endpoints_07.py — endpoint handlers api_entitlement_lock_reason_at_path .. api_entitlement_min_tier_for_retention_window_at_batch.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-at-path")
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
                    _shared.jsonify(
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
                    _shared.jsonify(
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
                _shared.jsonify(
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
        _shared.logger.warning("api_entitlement_lock_reason_at_path: error: %s", exc)
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

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-at-path-batch")
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
        _shared.logger.warning(
            "api_entitlement_lock_reason_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at-path")
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
        path = _ent.tier_unlocks_at_path(p, f, t)
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
            "api_entitlement_tier_unlocks_at_path: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at-path")
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
        path = _ent.tier_locks_at_path(p, f, t)
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
            "api_entitlement_tier_locks_at_path: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at-path-batch")
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
            "api_entitlement_tier_unlocks_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at-path-batch")
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
            "api_entitlement_tier_locks_at_path_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-path-at")
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
        path = _ent.tier_path_at(p, f, t)
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
            "api_entitlement_tier_path_at: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-path-at-batch")
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
            "api_entitlement_tier_path_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog")
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
        return _shared.jsonify(
            {
                "tier": ent.tier,
                "features": _ent.feature_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_catalog: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": "oss",
                "features": [],
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog")
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
        return _shared.jsonify(
            {
                "tier": ent.tier,
                "runtimes": _ent.runtime_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_catalog: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": "oss",
                "runtimes": [],
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog")
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
        return _shared.jsonify(
            {
                "tier": ent.tier,
                "channels": _ent.channel_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_catalog: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": "oss",
                "channels": [],
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-at")
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
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.channel_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "channels": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "channel-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-catalog-at-batch")
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
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.channel_catalog_at_batch(tiers)
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
            "api_entitlement_channel_catalog_at_batch: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog")
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
        return _shared.jsonify(
            {
                "tier": ent.tier,
                "tiers": _ent.tier_catalog(),
                "grace": ent.grace,
                "enforced": not ent.grace,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_catalog: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": "oss",
                "tiers": [],
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-catalog-at")
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
        rows = _ent.next_tier_channel_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_channel_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog-at")
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
        rows = _ent.previous_tier_channel_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_channel_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-channel-catalog-at-batch")
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
            "api_entitlement_next_tier_channel_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-channel-catalog-at-batch")
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
            "api_entitlement_previous_tier_channel_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-catalog-at")
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
        rows = _ent.next_tier_feature_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_feature_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog-at")
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
        rows = _ent.previous_tier_feature_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_feature_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog-at")
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
        rows = _ent.next_tier_runtime_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_next_tier_runtime_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog-at")
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
        rows = _ent.previous_tier_runtime_catalog_at(tier_in) or []
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_previous_tier_runtime_catalog_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-feature-catalog-at-batch")
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
            "api_entitlement_next_tier_feature_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-feature-catalog-at-batch")
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
            "api_entitlement_previous_tier_feature_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/next-tier-runtime-catalog-at-batch")
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
            "api_entitlement_next_tier_runtime_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-runtime-catalog-at-batch")
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
            "api_entitlement_previous_tier_runtime_catalog_at_batch: error: %s",
            exc,
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-channel-count")
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
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_channel_count(n)
        env = _shared._resolver_envelope(_ent)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_channel_count: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-retention-window")
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
    raw = _shared.request.args.get("days")
    if raw is None:
        return _shared.jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                _shared.jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_retention_window(parsed)
        env = _shared._resolver_envelope(_ent)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_retention_window: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-node-count")
def api_entitlement_tiers_for_node_count():
    """``GET /api/entitlement/tiers-for-node-count?count=<int>`` --
    inverse of ``/api/entitlement/required-tier?nodes=<int>``: returns the
    full ladder of tiers admitting ``count`` registered nodes.

    ``count=`` is required. Missing key -> ``400``. Non-int / blank value
    -> ``400``. Never 5xxs.

    Response shape mirrors ``/api/entitlement/tiers-for-channel-count`` --
    ``kind`` is ``"node_count"``; ``label`` is ``"4 nodes"``.
    """
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_node_count(n)
        env = _shared._resolver_envelope(_ent)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_node_count: error: %s", exc
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-capacity-batch")
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
    (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
    (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
    (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

    if not channels_ok and not retention_ok and not nodes_ok:
        return (
            _shared.jsonify(
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
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "channels": body.get("channels"),
                "retention_days": body.get("retention_days"),
                "nodes": body.get("nodes"),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_capacity_batch: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-channel-count-batch"
)
def api_entitlement_tiers_for_channel_count_batch():
    """``GET /api/entitlement/tiers-for-channel-count-batch?counts=1,5,10``
    -- per-value batch sibling of
    ``/api/entitlement/tiers-for-channel-count``.

    Where the singular endpoint folds ONE channel count to ONE
    availability ladder, this preserves the per-value grouping so a
    pricing-matrix walkthrough comparing several hypothetical channel
    counts ("at 1 / 5 / 10 / 25 channels -- Fits in: <tiers> per row")
    renders off ONE round-trip instead of N calls to
    ``/tiers-for-channel-count`` + client-side row assembly. Wraps
    :func:`clawmetry.entitlements.tiers_for_channel_count_batch`.

    Distinct from ``/api/entitlement/tiers-for-capacity-batch`` (per-
    axis rows for a THREE-axis bundle -- one row per axis, single
    scalar per axis) and ``/api/entitlement/tiers-for-batch`` (per-
    bundle folded answer across N feature+runtime *bundles*). This
    endpoint preserves per-value rows on a SINGLE capacity axis.

    ``counts=`` is required. Missing / blank / only-commas ->
    ``400``. Comma-separated tokens are normalised: whitespace-
    stripped, deduplicated by parsed int key preserving first-seen
    order. Non-int tokens collapse to the all-``None`` row shape
    (matches the singular endpoint's ``None``-on-bad-input posture
    rather than failing the whole batch). Never 5xxs: the grace-shape
    envelope is returned on any resolver failure.

    Response shape::

        {
          "kind":  "channel_count",
          "count": <int>,
          "rows":  [<row>, ...],
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` mirrors the bare singular endpoint body minus the
    resolver envelope: ``item`` / ``kind`` (``"channel_count"``) /
    ``label`` / ``free`` / ``min_tier`` / ``min_tier_label`` /
    ``min_tier_rank`` / ``tiers``. Per-row parity with
    ``/api/entitlement/tiers-for-channel-count?count=<n>`` is pinned
    in the test suite so the batch cannot silently drift from the
    scalar.
    """
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "counts", unlimited_ok=False
    )
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tiers_for_channel_count_batch(values)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "kind": "channel_count",
                "count": len(rows),
                "rows": rows,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_channel_count_batch: error: %s",
            exc,
        )
        return _shared.jsonify(_shared._tiers_for_capacity_perval_fallback("channel_count"))

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-node-count-batch"
)
def api_entitlement_tiers_for_node_count_batch():
    """``GET /api/entitlement/tiers-for-node-count-batch?counts=1,3,5`` --
    per-value batch sibling of
    ``/api/entitlement/tiers-for-node-count``. Node-axis twin of
    ``/api/entitlement/tiers-for-channel-count-batch``.

    Same posture: ``counts=`` required (missing / blank / only-commas
    -> ``400``), comma-separated int tokens deduped by parsed int key
    preserving first-seen order, non-int tokens collapse to the all-
    ``None`` row shape, never 5xxs. Wraps
    :func:`clawmetry.entitlements.tiers_for_node_count_batch`.

    Response shape and row shape byte-identical to
    ``/api/entitlement/tiers-for-channel-count-batch`` with ``kind``
    ``"node_count"``.
    """
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "counts", unlimited_ok=False
    )
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tiers_for_node_count_batch(values)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "kind": "node_count",
                "count": len(rows),
                "rows": rows,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_node_count_batch: error: %s",
            exc,
        )
        return _shared.jsonify(_shared._tiers_for_capacity_perval_fallback("node_count"))

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-retention-window-batch"
)
def api_entitlement_tiers_for_retention_window_batch():
    """``GET /api/entitlement/tiers-for-retention-window-batch?days=7,30,unlimited``
    -- per-value batch sibling of
    ``/api/entitlement/tiers-for-retention-window``. Retention-axis
    twin of ``/api/entitlement/tiers-for-channel-count-batch``.

    Same posture with one addition: the case-insensitive token
    ``unlimited`` is accepted and routes to the unlimited-history row
    (``item=null`` / ``label="unlimited"``). This is the *only* per-
    value batch on the retention axis that admits the unlimited
    sentinel; ``/tiers-for-capacity-batch`` treats
    ``retention_days=None`` as *unset* (matching
    ``/min-tier-batch``'s posture), so a caller previously had to
    route the unlimited-history question through the singular
    endpoint.

    ``days=`` is required. Missing / blank / only-commas -> ``400``.
    Duplicates by parsed int key or the ``"unlimited"`` sentinel are
    dropped preserving first-seen order. Non-int / non-
    ``"unlimited"`` tokens collapse to the all-``None`` row shape.
    Never 5xxs.

    Response shape and row shape byte-identical to
    ``/api/entitlement/tiers-for-channel-count-batch`` with ``kind``
    ``"retention_window"``.
    """
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "days", unlimited_ok=True
    )
    if err == "missing":
        return _shared.jsonify({"error": "missing days"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.tiers_for_retention_window_batch(values)
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
            {
                "kind": "retention_window",
                "count": len(rows),
                "rows": rows,
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_retention_window_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_fallback("retention_window")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-channel-count-at-batch"
)
def api_entitlement_tiers_for_channel_count_at_batch():
    """``GET /api/entitlement/tiers-for-channel-count-at-batch?tier=<perspective>
    &counts=1,5,10`` -- hypothetical-perspective sibling of
    ``/api/entitlement/tiers-for-channel-count-batch``.

    Fills the last ``_at_batch`` slot on the channel-count capacity axis
    alongside ``/tiers-for-channel-count-at`` (singular ``_at``),
    ``/tiers-for-capacity-batch-at`` (grant-axis batch ``_at``) and
    ``/tiers-for-features-at-batch`` / ``/tiers-for-runtimes-at-batch``
    on the grant axes, so a pricing-matrix walkthrough (``?tier=<p>``)
    can hit every ``_at_batch`` sibling in the ``tiers-for-*`` family
    with a uniform URL.

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the batch is
    identical to ``/tiers-for-channel-count-batch`` regardless of
    perspective (parity-pinned by
    :func:`entitlements.tiers_for_channel_count_at_batch`). Response
    layers ``perspective_tier`` on top of the batch body so a
    walkthrough surface renders the "from <perspective>" copy off one
    round-trip.

    - **400** when ``tier=`` is missing / blank, OR when ``counts=`` is
      missing / blank / only-commas.
    - **404** when ``tier`` is unknown (body carries ``which=tier``).
    - **Never 5xxs**: resolver failure -> perspective-carrying grace
      body with empty ``rows``.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "counts", unlimited_ok=False
    )
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
        rows = _ent.tiers_for_channel_count_at_batch(tier_in, values) or []
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_body(
                _ent, tier_in, "channel_count", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_channel_count_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_fallback(tier_in, "channel_count")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-node-count-at-batch"
)
def api_entitlement_tiers_for_node_count_at_batch():
    """``GET /api/entitlement/tiers-for-node-count-at-batch?tier=<perspective>
    &counts=1,3,5`` -- node-axis twin of
    ``/api/entitlement/tiers-for-channel-count-at-batch``. Same
    perspective contract, same never-5xx posture, same perspective-
    independence guarantee (parity-pinned). Response shape and error
    paths mirror ``/tiers-for-channel-count-at-batch`` with ``kind``
    ``"node_count"``.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "counts", unlimited_ok=False
    )
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
        rows = _ent.tiers_for_node_count_at_batch(tier_in, values) or []
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_body(
                _ent, tier_in, "node_count", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_node_count_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_fallback(tier_in, "node_count")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/tiers-for-retention-window-at-batch"
)
def api_entitlement_tiers_for_retention_window_at_batch():
    """``GET /api/entitlement/tiers-for-retention-window-at-batch?tier=<perspective>
    &days=7,30,unlimited`` -- retention-axis twin of
    ``/api/entitlement/tiers-for-channel-count-at-batch``.

    Each token may be a finite int or the case-insensitive string
    ``"unlimited"``; the unlimited row surfaces with ``item=null`` /
    ``label="unlimited"``. This is the *only* per-value ``_at_batch``
    on the retention axis that admits the unlimited sentinel --
    ``/tiers-for-capacity-batch-at`` treats ``retention_days=None`` as
    *unset*, not *unlimited*.

    Same 400-on-missing-tier / 400-on-blank-days / 404-on-unknown-tier
    / never-5xx contracts as the two count-axis siblings.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    values, err = _shared._parse_tiers_for_capacity_batch_csv(
        "days", unlimited_ok=True
    )
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
        rows = (
            _ent.tiers_for_retention_window_at_batch(tier_in, values) or []
        )
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_body(
                _ent, tier_in, "retention_window", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_retention_window_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._tiers_for_capacity_perval_at_fallback(
                tier_in, "retention_window"
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-features")
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
    raw = _shared.request.args.get("features")
    if raw is None or not raw.strip():
        return _shared.jsonify({"error": "missing features"}), 400
    features = _shared._parse_csv_arg("features")
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_features(features)
        env = _shared._resolver_envelope(_ent)
        if body is None:
            return _shared.jsonify(
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
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_features: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-runtimes")
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
    raw = _shared.request.args.get("runtimes")
    if raw is None or not raw.strip():
        return _shared.jsonify({"error": "missing runtimes"}), 400
    runtimes = _shared._parse_csv_arg("runtimes")
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tiers_for_runtimes(runtimes)
        env = _shared._resolver_envelope(_ent)
        if body is None:
            return _shared.jsonify(
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
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_runtimes: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-channel-count-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_channel_count_at(p, n)
        env = _shared._perspective_envelope(_ent, p)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_channel_count_at: error: %s", exc
        )
        return _shared.jsonify({"tiers": [], **_shared._perspective_fallback(p)})

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-retention-window-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw = _shared.request.args.get("days")
    if raw is None:
        return _shared.jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                _shared.jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_retention_window_at(p, parsed)
        env = _shared._perspective_envelope(_ent, p)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_retention_window_at: error: %s", exc
        )
        return _shared.jsonify({"tiers": [], **_shared._perspective_fallback(p)})

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-node-count-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_node_count_at(p, n)
        env = _shared._perspective_envelope(_ent, p)
        if body is None:
            return _shared.jsonify({"tiers": [], **env})
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_node_count_at: error: %s", exc
        )
        return _shared.jsonify({"tiers": [], **_shared._perspective_fallback(p)})

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-capacity-batch-at")
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
    p = (_shared.request.args.get("tier") or "").strip().lower()
    if not p:
        return _shared.jsonify({"error": "missing tier"}), 400
    (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
    (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
    (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

    if not channels_ok and not retention_ok and not nodes_ok:
        return (
            _shared.jsonify(
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
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": p}),
                404,
            )
        body = _ent.tiers_for_capacity_batch_at(
            p,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )
        env = _shared._perspective_envelope(_ent, p)
        if body is None:
            body = {"channels": None, "retention_days": None, "nodes": None}
        return _shared.jsonify(
            {
                "channels": body.get("channels"),
                "retention_days": body.get("retention_days"),
                "nodes": body.get("nodes"),
                **env,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_capacity_batch_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "channels": None,
                "retention_days": None,
                "nodes": None,
                **_shared._perspective_fallback(p),
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-features-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    features_csv = _shared._parse_csv_arg("features")
    if not features_csv:
        return _shared.jsonify({"error": "missing features"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
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
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_min_tier_for_features_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-runtimes-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    runtimes_csv = _shared._parse_csv_arg("runtimes")
    if not runtimes_csv:
        return _shared.jsonify({"error": "missing runtimes"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
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
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_min_tier_for_runtimes_at: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-features-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    raw_features = _shared.request.args.get("features")
    if raw_features is None or not raw_features.strip():
        return _shared.jsonify({"error": "missing features"}), 400
    features_csv = _shared._parse_csv_arg("features")
    if not features_csv:
        return _shared.jsonify({"error": "missing features"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        body = _ent.tiers_for_features_at(tier_in, features_csv)
        env = _shared._perspective_envelope(_ent, tier_in)
        if body is None:
            return _shared.jsonify(
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
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_features_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "items": [],
                "unknown": features_csv,
                "kind": "features",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                **_shared._perspective_fallback(tier_in),
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tiers-for-runtimes-at")
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
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    raw_runtimes = _shared.request.args.get("runtimes")
    if raw_runtimes is None or not raw_runtimes.strip():
        return _shared.jsonify({"error": "missing runtimes"}), 400
    runtimes_csv = _shared._parse_csv_arg("runtimes")
    if not runtimes_csv:
        return _shared.jsonify({"error": "missing runtimes"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        body = _ent.tiers_for_runtimes_at(tier_in, runtimes_csv)
        env = _shared._perspective_envelope(_ent, tier_in)
        if body is None:
            return _shared.jsonify(
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
        return _shared.jsonify({**body, **env})
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tiers_for_runtimes_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "items": [],
                "unknown": runtimes_csv,
                "kind": "runtimes",
                "count": 0,
                "min_tier": None,
                "min_tier_label": None,
                "min_tier_rank": None,
                "tiers": [],
                **_shared._perspective_fallback(tier_in),
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-features")
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
    features_csv = _shared._parse_csv_arg("features")
    if not features_csv:
        return _shared.jsonify({"error": "missing features"}), 400

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
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_min_tier_for_features: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-runtimes")
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
    runtimes_csv = _shared._parse_csv_arg("runtimes")
    if not runtimes_csv:
        return _shared.jsonify({"error": "missing runtimes"}), 400

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
        env = _shared._resolver_envelope(_ent)
        return _shared.jsonify(
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
        _shared.logger.warning(
            "api_entitlement_min_tier_for_runtimes: error: %s", exc
        )
        return _shared.jsonify(
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

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-channel-count")
def api_entitlement_min_tier_for_channel_count():
    """``GET /api/entitlement/min-tier-for-channel-count?count=<int>`` --
    resolver-scoped sibling of :func:`min_tier_for_channel_count`: the
    cheapest *purchasable* tier admitting ``count`` configured channel
    adapters.

    Fills the *bare* slot for the scalar capacity-axis ``min_tier_for_*``
    family alongside the ladder-axis sibling
    ``/api/entitlement/tiers-for-channel-count`` (which returns the full
    "Fits in: <tier>, ..." availability list) and the plural grant-axis
    bare endpoints ``/min-tier-for-features`` / ``/min-tier-for-runtimes``
    (#3734). Symmetric with ``/min-tier-for-node-count`` and
    ``/min-tier-for-retention-window`` so the three scalar capacity axes
    look identical from the caller's side. A dashboard wiring "you have
    5 channels -- Available in Cloud Starter" can now hit ONE endpoint
    that folds the walk in place of scanning the full ladder from
    ``/tiers-for-channel-count``.

    ``count=`` is required. Missing key -> ``400``. Blank / non-int
    value -> ``400``. Never 5xxs: a resolver failure yields the grace-
    shape fallback envelope so the pricing surface keeps rendering.

    Response shape::

        {
          "item":                <int>,
          "kind":                "channel_count",
          "label":               "5 channels",
          "free":                <bool>,
          "required_tier":       "cloud_starter" | null,
          "required_tier_label": "Cloud Starter" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "...",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }
    """
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        required = _ent.min_tier_for_channel_count(n)
        label = f"{n} channel" if n == 1 else f"{n} channels"
        return _shared.jsonify(
            _shared._min_tier_for_capacity_body(
                _ent, n, "channel_count", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_channel_count: error: %s", exc
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_fallback(n, "channel_count")
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-node-count")
def api_entitlement_min_tier_for_node_count():
    """``GET /api/entitlement/min-tier-for-node-count?count=<int>`` --
    node-axis twin of ``/api/entitlement/min-tier-for-channel-count``.

    Resolver-scoped sibling of :func:`min_tier_for_node_count`: the
    cheapest *purchasable* tier admitting ``count`` registered nodes --
    the id the fleet-page lock affordance ("you have 4 nodes --
    Available in Cloud Starter") reads from.

    Same never-5xx posture, same 400-on-blank/non-int parsing. Response
    shape and error paths mirror ``/min-tier-for-channel-count`` exactly,
    with ``kind="node_count"`` and ``label="4 nodes"``.
    """
    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400
    try:
        from clawmetry import entitlements as _ent

        required = _ent.min_tier_for_node_count(n)
        label = f"{n} node" if n == 1 else f"{n} nodes"
        return _shared.jsonify(
            _shared._min_tier_for_capacity_body(
                _ent, n, "node_count", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_node_count: error: %s", exc
        )
        return _shared.jsonify(_shared._min_tier_for_capacity_fallback(n, "node_count"))

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-retention-window")
def api_entitlement_min_tier_for_retention_window():
    """``GET /api/entitlement/min-tier-for-retention-window?days=<int>`` --
    retention-axis twin of ``/api/entitlement/min-tier-for-channel-count``.

    Resolver-scoped sibling of :func:`min_tier_for_retention_window`: the
    cheapest *purchasable* tier admitting a ``days`` history window -- the
    id the history-range toggle lock affordance reads from.

    ``days=unlimited`` (case-insensitive) requests the unlimited-history
    window; only tiers whose retention cap is ``None`` admit the request
    (Enterprise on the current tier table). ``item`` is ``null`` and
    ``label`` is ``"unlimited"`` in that case.

    ``days=`` is required. Missing key -> ``400``. Blank / non-int /
    non-``unlimited`` value -> ``400``. Never 5xxs: same grace-shape
    fallback as the two count-axis siblings.

    Response shape mirrors ``/min-tier-for-channel-count`` with
    ``kind="retention_window"``.
    """
    raw = _shared.request.args.get("days")
    if raw is None:
        return _shared.jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                _shared.jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )
    try:
        from clawmetry import entitlements as _ent

        required = _ent.min_tier_for_retention_window(parsed)
        if parsed is None:
            label = "unlimited"
        else:
            label = (
                f"{parsed} day" if parsed == 1 else f"{parsed} days"
            )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_body(
                _ent, parsed, "retention_window", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_retention_window: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_fallback(parsed, "retention_window")
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-channel-count-at")
def api_entitlement_min_tier_for_channel_count_at():
    """``GET /api/entitlement/min-tier-for-channel-count-at?tier=<perspective>
    &count=<int>`` -- hypothetical-perspective sibling of
    ``/api/entitlement/min-tier-for-channel-count``.

    Fills the ``_at`` slot for the channel-count capacity axis alongside
    ``/min-tier-for-features-at`` / ``/min-tier-for-runtimes-at`` so a
    pricing-matrix walkthrough (``?tier=<p>``) can hit every scalar
    ``min-tier-for-*`` axis uniformly at a fixed perspective.

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the answer is
    perspective-independent (parity-pinned by
    :func:`entitlements.min_tier_for_channel_count_at`). Response layers
    ``perspective_tier`` on top of the ``/min-tier-for-channel-count``
    body so a walkthrough surface renders the "from <perspective>" copy
    off one round-trip.

    - **400** when ``tier=`` is missing / blank, OR when ``count=`` is
      missing / blank / non-int.
    - **404** when ``tier`` is unknown (body carries ``which=tier``).
    - **Never 5xxs**: resolver failure -> perspective-carrying grace body.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        required = _ent.min_tier_for_channel_count_at(tier_in, n)
        label = f"{n} channel" if n == 1 else f"{n} channels"
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_body(
                _ent, tier_in, n, "channel_count", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_channel_count_at: error: %s", exc
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_fallback(tier_in, n, "channel_count")
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-node-count-at")
def api_entitlement_min_tier_for_node_count_at():
    """``GET /api/entitlement/min-tier-for-node-count-at?tier=<perspective>
    &count=<int>`` -- node-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-at``. Same perspective
    contract, same never-5xx posture, same perspective-independence
    guarantee (parity-pinned). Response shape and error paths mirror
    ``/min-tier-for-channel-count-at`` with ``kind="node_count"`` and
    ``label="4 nodes"``.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    raw = _shared.request.args.get("count")
    if raw is None:
        return _shared.jsonify({"error": "missing count"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing count"}), 400
    try:
        n = int(raw_stripped)
    except (TypeError, ValueError):
        return _shared.jsonify({"error": "count must be an integer"}), 400

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        required = _ent.min_tier_for_node_count_at(tier_in, n)
        label = f"{n} node" if n == 1 else f"{n} nodes"
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_body(
                _ent, tier_in, n, "node_count", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_node_count_at: error: %s", exc
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_fallback(tier_in, n, "node_count")
        )

@_shared.bp_entitlement.route("/api/entitlement/min-tier-for-retention-window-at")
def api_entitlement_min_tier_for_retention_window_at():
    """``GET /api/entitlement/min-tier-for-retention-window-at?tier=<perspective>
    &days=<int|unlimited>`` -- retention-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-at``.

    ``days=unlimited`` (case-insensitive) requests the unlimited-history
    window; only tiers whose retention cap is ``None`` admit the request
    (Enterprise on the current tier table). ``item`` is ``null`` and
    ``label`` is ``"unlimited"`` in that case, matching the bare
    ``/min-tier-for-retention-window`` endpoint's shape.

    Same 400-on-missing-tier / 400-on-blank-days / 404-on-unknown-tier /
    never-5xx contracts as the two count-axis siblings.
    """
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400

    raw = _shared.request.args.get("days")
    if raw is None:
        return _shared.jsonify({"error": "missing days"}), 400
    raw_stripped = raw.strip()
    if not raw_stripped:
        return _shared.jsonify({"error": "missing days"}), 400
    unlimited = raw_stripped.lower() == "unlimited"
    if unlimited:
        parsed: int | None = None
    else:
        try:
            parsed = int(raw_stripped)
        except (TypeError, ValueError):
            return (
                _shared.jsonify(
                    {"error": "days must be an integer or 'unlimited'"}
                ),
                400,
            )

    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        required = _ent.min_tier_for_retention_window_at(tier_in, parsed)
        if parsed is None:
            label = "unlimited"
        else:
            label = (
                f"{parsed} day" if parsed == 1 else f"{parsed} days"
            )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_body(
                _ent, tier_in, parsed, "retention_window", label, required
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_retention_window_at: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_fallback(
                tier_in, parsed, "retention_window"
            )
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-channel-count-batch"
)
def api_entitlement_min_tier_for_channel_count_batch():
    """``GET /api/entitlement/min-tier-for-channel-count-batch?counts=1,5,10``
    -- per-value batch sibling of
    ``/api/entitlement/min-tier-for-channel-count``.

    Where the singular endpoint folds ONE channel count to ONE tier
    answer, this preserves the per-value grouping so a pricing-matrix
    walkthrough comparing several hypothetical channel counts
    ("at 1 / 5 / 10 / 25 channels -- cheapest qualifying tier per row")
    renders off ONE round-trip instead of N calls to
    ``/min-tier-for-channel-count`` + client-side row assembly. Wraps
    :func:`clawmetry.entitlements.min_tier_for_channel_count_batch`.

    Distinct from ``/api/entitlement/min-tier-batch`` (per-axis rows
    for a FIVE-axis bundle -- one row per axis, single scalar per
    axis) and ``/api/entitlement/min-tier-for-features-batch`` (per-
    bundle folded answer across N feature *bundles*). This endpoint
    preserves per-value rows on a SINGLE capacity axis.

    ``counts=`` is required. Missing / blank -> ``400``. Comma-
    separated tokens are normalised: whitespace-stripped, deduplicated
    by parsed int key preserving first-seen order. Non-int tokens
    collapse to the all-``None`` row shape (matches the singular
    endpoint's ``None``-on-bad-input posture rather than failing the
    whole batch). Never 5xxs: the grace-shape envelope is returned on
    any resolver failure.

    Response shape::

        {
          "kind":  "channel_count",
          "count": <int>,
          "rows":  [<row>, ...],
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each ``<row>`` mirrors the bare singular endpoint body minus the
    resolver envelope: ``item`` / ``kind`` (``"channel_count"``) /
    ``label`` / ``free`` / ``required_tier`` / ``required_tier_label``
    / ``required_tier_rank`` (``-1`` when ``required_tier`` is
    ``null``). Per-row parity with
    ``/api/entitlement/min-tier-for-channel-count?count=<n>`` is
    pinned in the test suite so the batch cannot silently drift from
    the scalar.
    """
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = [
            _shared._capacity_batch_row_to_body(r, "channel_count")
            for r in _ent.min_tier_for_channel_count_batch(values)
        ]
        return _shared.jsonify(
            {
                "kind": "channel_count",
                "count": len(rows),
                "rows": rows,
                **_shared._resolver_envelope(_ent),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_channel_count_batch: error: %s",
            exc,
        )
        return _shared.jsonify(_shared._min_tier_for_capacity_batch_fallback("channel_count"))

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-node-count-batch"
)
def api_entitlement_min_tier_for_node_count_batch():
    """``GET /api/entitlement/min-tier-for-node-count-batch?counts=1,3,5`` --
    node-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-batch``.

    Same never-5xx posture, same 400-on-missing-arg parsing, same
    per-value dedup. Row ``kind`` is ``"node_count"`` and ``label``
    conjugates as ``"1 node"`` / ``"5 nodes"``.
    """
    values, err = _shared._parse_capacity_batch_csv("counts", unlimited_ok=False)
    if err == "missing":
        return _shared.jsonify({"error": "missing counts"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = [
            _shared._capacity_batch_row_to_body(r, "node_count")
            for r in _ent.min_tier_for_node_count_batch(values)
        ]
        return _shared.jsonify(
            {
                "kind": "node_count",
                "count": len(rows),
                "rows": rows,
                **_shared._resolver_envelope(_ent),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_node_count_batch: error: %s",
            exc,
        )
        return _shared.jsonify(_shared._min_tier_for_capacity_batch_fallback("node_count"))

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-retention-window-batch"
)
def api_entitlement_min_tier_for_retention_window_batch():
    """``GET /api/entitlement/min-tier-for-retention-window-batch?days=7,30,unlimited``
    -- retention-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-batch``.

    Each token may be a finite int (``7`` / ``30`` / ``90``) or the
    case-insensitive string ``"unlimited"`` (routes to
    ``min_tier_for_retention_window(None)``). The unlimited row
    surfaces with ``item=null`` and ``label="unlimited"``; matches the
    singular endpoint's ``days=unlimited`` posture. This is the *only*
    per-axis batch on the retention axis that admits the unlimited
    sentinel -- ``/api/entitlement/min-tier-batch`` treats
    ``retention_days=`` (no value) as *unset*, not *unlimited*.

    ``days=`` is required. Missing / blank -> ``400``. Non-int / non-
    ``unlimited`` tokens collapse to the all-``None`` row shape rather
    than failing the whole batch. Never 5xxs: grace-shape fallback on
    any resolver failure.

    Row shape mirrors ``/api/entitlement/min-tier-for-retention-window``
    with ``kind="retention_window"``.
    """
    values, err = _shared._parse_capacity_batch_csv("days", unlimited_ok=True)
    if err == "missing":
        return _shared.jsonify({"error": "missing days"}), 400
    try:
        from clawmetry import entitlements as _ent

        rows = [
            _shared._capacity_batch_row_to_body(r, "retention_window")
            for r in _ent.min_tier_for_retention_window_batch(values)
        ]
        return _shared.jsonify(
            {
                "kind": "retention_window",
                "count": len(rows),
                "rows": rows,
                **_shared._resolver_envelope(_ent),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_retention_window_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_batch_fallback("retention_window")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-channel-count-at-batch"
)
def api_entitlement_min_tier_for_channel_count_at_batch():
    """``GET /api/entitlement/min-tier-for-channel-count-at-batch?tier=<perspective>
    &counts=1,5,10`` -- hypothetical-perspective sibling of
    ``/api/entitlement/min-tier-for-channel-count-batch``.

    Fills the last ``_at_batch`` slot on the channel-count capacity axis
    alongside ``/min-tier-for-channel-count-at`` (singular ``_at``) and
    ``/min-tier-for-features-at-batch`` /
    ``/min-tier-for-runtimes-at-batch`` on the grant axes, so a
    pricing-matrix walkthrough (``?tier=<p>``) can hit every
    ``_at_batch`` sibling in the ``min-tier-for-*`` family with a
    uniform URL.

    Perspective is validated against :data:`entitlements._TIER_ORDER`
    (including ``trial``) but does NOT shape rows -- the batch is
    identical to ``/min-tier-for-channel-count-batch`` regardless of
    perspective (parity-pinned by
    :func:`entitlements.min_tier_for_channel_count_at_batch`). Response
    layers ``perspective_tier`` on top of the batch body so a
    walkthrough surface renders the "from <perspective>" copy off one
    round-trip.

    - **400** when ``tier=`` is missing / blank, OR when ``counts=`` is
      missing / blank / only-commas.
    - **404** when ``tier`` is unknown (body carries ``which=tier``).
    - **Never 5xxs**: resolver failure -> perspective-carrying grace
      body with empty ``rows``.
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
        helper_rows = (
            _ent.min_tier_for_channel_count_at_batch(tier_in, values) or []
        )
        rows = [
            _shared._capacity_batch_row_to_body(r, "channel_count")
            for r in helper_rows
        ]
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_body(
                _ent, tier_in, "channel_count", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_channel_count_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_fallback(tier_in, "channel_count")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-node-count-at-batch"
)
def api_entitlement_min_tier_for_node_count_at_batch():
    """``GET /api/entitlement/min-tier-for-node-count-at-batch?tier=<perspective>
    &counts=1,3,5`` -- node-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-at-batch``. Same
    perspective contract, same never-5xx posture, same perspective-
    independence guarantee (parity-pinned). Response shape and error
    paths mirror ``/min-tier-for-channel-count-at-batch`` with ``kind``
    ``"node_count"`` and per-row ``label="1 node"`` /  ``"5 nodes"``.
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
        helper_rows = (
            _ent.min_tier_for_node_count_at_batch(tier_in, values) or []
        )
        rows = [
            _shared._capacity_batch_row_to_body(r, "node_count")
            for r in helper_rows
        ]
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_body(
                _ent, tier_in, "node_count", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_node_count_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_fallback(tier_in, "node_count")
        )

@_shared.bp_entitlement.route(
    "/api/entitlement/min-tier-for-retention-window-at-batch"
)
def api_entitlement_min_tier_for_retention_window_at_batch():
    """``GET /api/entitlement/min-tier-for-retention-window-at-batch?tier=<perspective>
    &days=7,30,unlimited`` -- retention-axis twin of
    ``/api/entitlement/min-tier-for-channel-count-at-batch``.

    Each token may be a finite int or the case-insensitive string
    ``"unlimited"`` (routes to
    ``min_tier_for_retention_window(None)``); the unlimited row
    surfaces with ``item=null`` / ``label="unlimited"``. This is the
    *only* per-axis ``_at_batch`` on the retention axis that admits
    the unlimited sentinel -- the grant-axis
    ``/tiers-for-capacity-batch-at`` treats ``retention_days=None`` as
    *unset*, not *unlimited* (matching ``/min-tier-batch``'s posture).

    Same 400-on-missing-tier / 400-on-blank-days / 404-on-unknown-tier
    / never-5xx contracts as the two count-axis siblings.
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
        helper_rows = (
            _ent.min_tier_for_retention_window_at_batch(tier_in, values) or []
        )
        rows = [
            _shared._capacity_batch_row_to_body(r, "retention_window")
            for r in helper_rows
        ]
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_body(
                _ent, tier_in, "retention_window", rows
            )
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_min_tier_for_retention_window_at_batch: "
            "error: %s",
            exc,
        )
        return _shared.jsonify(
            _shared._min_tier_for_capacity_at_batch_fallback(
                tier_in, "retention_window"
            )
        )
