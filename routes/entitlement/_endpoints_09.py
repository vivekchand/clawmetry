"""routes/entitlement/_endpoints_09.py — endpoint handlers api_entitlement_has_capacity_batch, api_entitlement_has_capacity_batch_at.

Migrated from feat/has-capacity-batch (PR #5114) into the entitlement package
that main split out of the former single-module routes/entitlement.py.
See _shared.py for shared helpers; see __init__.py for the full package index.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared


@_shared.bp_entitlement.route("/api/entitlement/has-capacity-batch")
def api_entitlement_has_capacity_batch():
    """``GET /api/entitlement/has-capacity-batch?channels=N
    &retention_days=K&nodes=M`` -- per-axis boolean grants for every
    supplied capacity axis in one pass.

    Boolean-gate twin of ``/api/entitlement/tiers-for-capacity-batch``
    on the three capacity axes. Closes the capacity-axis symmetry gap
    in the ``/has-*`` family: ``/has-batch`` covers only features +
    runtimes (the grant axes) and does not accept capacity args at all
    -- so a caller that wants a live "does this install admit N
    channels / K retention days / M nodes?" answer for a
    ``(channels, retention_days, nodes)`` bundle either had to fan out
    three ``/has-<axis>`` calls or hydrate the full
    ``/capacity-headroom`` payload. This endpoint delivers the same
    per-axis boolean those three singulars return, on all three axes,
    off ONE round-trip.

    At least one of ``channels=`` / ``retention_days=`` / ``nodes=``
    must be supplied (non-empty / parseable after normalisation). A
    blank or non-int value on an individual axis is treated as "not
    supplied" for that axis (matches
    ``/api/entitlement/tiers-for-capacity-batch``'s never-mis-route
    posture rather than silently reporting a typo as ``false``); the
    endpoint 400s only when *no* axis parsed successfully. Never
    5xxs: the grace-shape envelope is returned on any resolver
    failure.

    Response shape::

        {
          "channels":       <bool> | None,
          "retention_days": <bool> | None,
          "nodes":          <bool> | None,
          "current_tier":       "...",
          "current_tier_rank":  <int>,
          "grace":              <bool>,
          "enforced":           <bool>,
        }

    Each boolean matches the singular
    ``/has-channel-count?count=`` / ``/has-retention-window?days=`` /
    ``/has-node-count?count=`` endpoint byte-for-byte -- grace
    semantics carry through unchanged from the singular helpers.

    Critically, ``retention_days`` here treats ``None`` (parameter
    omitted / unparseable) as *unset* -- NOT *unlimited* (matches
    ``/tiers-for-capacity-batch``'s posture on the same axis).
    Asking the "does this install admit unlimited retention?"
    question is the singular ``/has-retention-window?days=unlimited``
    call's job.
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

        body = _ent.has_capacity_batch(
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
            "api_entitlement_has_capacity_batch: error: %s", exc
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


@_shared.bp_entitlement.route("/api/entitlement/has-capacity-batch-at")
def api_entitlement_has_capacity_batch_at():
    """``GET /api/entitlement/has-capacity-batch-at?tier=<perspective>
    &channels=N&retention_days=K&nodes=M`` --
    hypothetical-perspective sibling of
    ``/api/entitlement/has-capacity-batch``.

    Fills the last ``_at`` slot in the ``/has-*`` capacity family
    alongside ``/has-channel-count-at`` / ``/has-retention-window-at``
    / ``/has-node-count-at`` on the three per-axis grants and
    ``/tiers-for-capacity-batch-at`` on the ladder side. A pricing-
    matrix walkthrough can bind ONE URL per row across the whole batch
    ``_at`` family instead of fanning out three per-axis ``_at`` calls.

    Perspective is validated against ``_TIER_ORDER`` (``trial``
    accepted). Unlike ``/tiers-for-capacity-batch-at`` (which walks
    the static per-tier caps and produces perspective-independent
    rows), the boolean answer here IS perspective-shaped -- the whole
    point of the ``_at`` slot is to answer "would THIS tier admit
    ``N``?" per pricing-matrix cell. Grace-independent by construction:
    the answer depends only on the static per-tier cap, so
    ``has-capacity-batch-at?tier=oss&channels=100`` returns
    ``channels=false`` even in grace.

    Missing / blank ``tier=`` -> ``400``. Unknown ``tier=`` ->
    ``404``. At least one of ``channels=`` / ``retention_days=`` /
    ``nodes=`` must parse successfully; the endpoint 400s only when
    *no* axis parsed (matches ``/has-capacity-batch``'s
    never-mis-route posture). Never 5xxs.

    ``retention_days`` treats ``None`` (parameter omitted /
    unparseable) as *unset* -- NOT *unlimited* (matches
    ``/tiers-for-capacity-batch-at``'s posture). Asking the
    "would this tier admit unlimited retention?" question at a
    hypothetical perspective is the singular
    ``/has-retention-window-at?days=unlimited`` call's job.

    Response shape mirrors ``/api/entitlement/has-capacity-batch``
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
        body = _ent.has_capacity_batch_at(
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
            "api_entitlement_has_capacity_batch_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "channels": None,
                "retention_days": None,
                "nodes": None,
                **_shared._perspective_fallback(p),
            }
        )
