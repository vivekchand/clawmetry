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
