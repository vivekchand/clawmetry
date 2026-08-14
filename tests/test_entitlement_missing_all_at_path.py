"""Tests for the aggregate mixed-axis ``missing_all_at_path(...)`` path
walker and its paired ``/api/entitlement/missing-all-at-path`` endpoint.

Aggregate mixed-axis path-shaped row-detail sibling of
:func:`clawmetry.entitlements.missing_features_at_path` /
:func:`clawmetry.entitlements.missing_runtimes_at_path` (per-axis path
walkers) and row-detail complement of :func:`has_all_at_path` (paired
boolean-fold path walker). Lets an upgrade-walkthrough tooltip render
"at which rung does each per-axis slot in this bundle clear?" off ONE
call instead of first calling ``tier_path`` and then N calls to
``missing_all_at``.

This file pins:

1. Walk semantics byte-parity with the per-axis path walkers and the
   paired boolean-fold ``has_all_at_path`` (same purchasable filter,
   same sort key, same destination-sibling exclusion).
2. Row-detail parity with the scalar ``missing_all_at`` on the known-
   only subset per rung (scalar-vs-endpoint layered typo posture).
3. Complement invariant against ``has_all_at_path``: per rung,
   any-per-axis-denied is the strict negation of the paired rung's
   boolean fold.
4. **Grace-independence invariant**: every per-rung ``missing`` dict is
   byte-identical under grace vs enforce for the same (endpoints,
   bundle) pair.
5. Endpoint envelope shape parity (fixed key set) across every input
   branch so a frontend can bind fields without a resolver branch.
6. Never-4xx on every input branch; never-5xx via the fallback
   envelope.
7. Runtime-alias canonicalisation upstream of the strict scalar; the
   alias-and-canonical pair dedups to ONE fold input per rung.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture. Perspective-shaped path answers are
    intentionally identical in grace and enforce; this fixture pins
    that invariant against the singular ``_at`` delegates."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- Envelope shape ----------------------------------------------------------


_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "path",
    "path_length",
    "denied_count",
    "all_denied",
    "any_denied",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_PER_RUNG_KEYS = {"tier", "tier_label", "tier_rank", "missing"}

_MISSING_DICT_KEYS = {"features", "runtimes", "channels", "retention_days", "nodes"}


# -- Scalar: walk semantics --------------------------------------------------


def test_scalar_identity_empty_path(ent):
    """``from == to`` -> empty path, regardless of bundle."""
    assert ent.missing_all_at_path("oss", "oss") == []
    assert ent.missing_all_at_path("oss", "oss", features=["fleet"]) == []
    assert (
        ent.missing_all_at_path(
            "enterprise", "enterprise", features=["fleet"], nodes=99
        )
        == []
    )


def test_scalar_unknown_endpoints_short_circuit_to_none(ent):
    """Unknown ids on either side short-circuit to ``None`` per the
    ``_path`` family contract."""
    assert ent.missing_all_at_path("bogus", "oss") is None
    assert ent.missing_all_at_path("oss", "bogus") is None
    assert ent.missing_all_at_path("bogus", "bogus") is None
    assert ent.missing_all_at_path("", "oss") is None
    assert ent.missing_all_at_path(None, "oss") is None


def test_scalar_upgrade_walk_matches_purchasable_filter(ent):
    """Upgrade walk from oss -> enterprise excludes the from_tier and
    includes all rungs above it. Rung sort key + same-rank sibling
    handling mirrors ``has_all_at_path`` byte-for-byte."""
    rows = ent.missing_all_at_path("oss", "enterprise")
    rungs = [r["tier"] for r in rows]
    assert rungs == ["cloud_starter", "cloud_pro", "pro", "enterprise"]


def test_scalar_downgrade_walk_reverses_and_includes_destination(ent):
    """Downgrade walk from enterprise -> oss includes oss as the
    destination (destination-inclusion mirrors the ``_path`` family)."""
    rows = ent.missing_all_at_path("enterprise", "oss")
    rungs = [r["tier"] for r in rows]
    assert rungs == ["cloud_pro", "pro", "cloud_starter", "oss"]


def test_scalar_lateral_walk_single_row(ent):
    """Same-rank different-id -> single-row path terminating at
    ``to_tier``. Uses cloud_pro (rank 2) and pro (rank 2)."""
    assert ent.tier_rank("cloud_pro") == ent.tier_rank("pro")
    assert ent.missing_all_at_path("cloud_pro", "pro") == [
        {
            "tier": "pro",
            "tier_label": ent.tier_label("pro"),
            "tier_rank": ent.tier_rank("pro"),
            "missing": {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            },
        }
    ]


def test_scalar_row_shape_pinned(ent):
    """Every row carries exactly the four documented keys, and the
    per-rung ``missing`` dict carries exactly the five axis slots."""
    rows = ent.missing_all_at_path("oss", "enterprise", features=["fleet"])
    for row in rows:
        assert set(row) == _PER_RUNG_KEYS
        assert set(row["missing"]) == _MISSING_DICT_KEYS


# -- Scalar: per-rung row-detail parity vs missing_all_at --------------------


def test_scalar_per_rung_missing_byte_equals_missing_all_at(ent):
    """Per-rung ``missing`` byte-equals ``missing_all_at`` for the same
    (rung, bundle) pair -- the parity that prevents scalar/path drift."""
    bundle = dict(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=100,
        retention_days=90,
        nodes=99,
    )
    rows = ent.missing_all_at_path("oss", "enterprise", **bundle)
    for row in rows:
        assert row["missing"] == ent.missing_all_at(row["tier"], **bundle)


def test_scalar_downgrade_per_rung_parity(ent):
    """Same parity holds on the downgrade branch (destination-inclusion
    means the oss row surfaces its lost grants)."""
    bundle = dict(features=["fleet"], runtimes=["claude_code"])
    rows = ent.missing_all_at_path("enterprise", "oss", **bundle)
    for row in rows:
        assert row["missing"] == ent.missing_all_at(row["tier"], **bundle)


# -- Scalar: complement invariant vs has_all_at_path -------------------------


def _row_any_denied(missing_dict) -> bool:
    """Match the endpoint's per-row any-denial fold: a list denies iff
    non-empty; a scalar denies iff not ``None``."""
    return any(
        (isinstance(v, list) and bool(v)) or (not isinstance(v, list) and v is not None)
        for v in missing_dict.values()
    )


def test_scalar_complement_invariant_vs_has_all_at_path(ent):
    """For every fully-parseable bundle, per rung
    ``any(missing_all_at_path(f,t,**b)[i]["missing"])`` is the strict
    negation of ``has_all_at(rung, **b)`` -- pins the row-detail path
    seat as the exact negation of the boolean-fold path."""
    bundle = dict(features=["fleet"], runtimes=["claude_code"])
    for f, t in [
        ("oss", "enterprise"),
        ("enterprise", "oss"),
        ("cloud_starter", "cloud_pro"),
    ]:
        rows = ent.missing_all_at_path(f, t, **bundle)
        for row in rows:
            assert _row_any_denied(row["missing"]) is not bool(
                ent.has_all_at(row["tier"], **bundle)
            )


# -- Scalar: bundle typo posture inherited from missing_all_at ---------------


def test_scalar_unknown_feature_surfaces_on_every_rung(ent):
    """Unknown feature id INCLUDED in every rung's ``missing["features"]``
    in canonicalised form (matches ``missing_features_at`` typo posture
    inherited through ``missing_all_at``)."""
    rows = ent.missing_all_at_path("oss", "enterprise", features=["bogus"])
    for row in rows:
        assert "bogus" in row["missing"]["features"]


def test_scalar_non_int_capacity_swallows_to_none_on_every_rung(ent):
    """Non-int capacity -> per-rung slot ``None`` (matches
    ``missing_all_at`` row-detail typo posture)."""
    rows = ent.missing_all_at_path("oss", "cloud_pro", channels="not-int")
    for row in rows:
        assert row["missing"]["channels"] is None


def test_scalar_empty_axis_yields_empty_per_rung_slot(ent):
    """Empty ``features=[]`` -> per-rung ``missing["features"]`` empty
    (matches ``missing_all_at`` empty-supplied posture)."""
    rows = ent.missing_all_at_path("oss", "enterprise", features=[])
    for row in rows:
        assert row["missing"]["features"] == []
        assert row["missing"]["runtimes"] == []


def test_scalar_none_axes_yields_empty_per_rung_slots(ent):
    """No axes supplied -> every per-rung slot empty/None."""
    rows = ent.missing_all_at_path("oss", "enterprise")
    for row in rows:
        assert row["missing"] == {
            "features": [],
            "runtimes": [],
            "channels": None,
            "retention_days": None,
            "nodes": None,
        }


def test_scalar_never_raises_on_hostile_input(ent):
    """The scalar swallows every hostile input variant to either
    ``None`` (unknown endpoint) or an empty per-rung slot (bad axis)."""
    # Non-iterable feature bundle -> collapses to [] per rung via the
    # scalar's typo posture (matches missing_all_at + missing_features_at).
    rows = ent.missing_all_at_path("oss", "cloud_pro", features=42)
    assert rows is not None
    for row in rows:
        assert row["missing"]["features"] == []


# -- Scalar: grace vs enforce invariant --------------------------------------


def test_scalar_grace_enforce_byte_identical(monkeypatch, tmp_path):
    """Perspective-shaped answers are intentionally identical in grace
    and enforce (they read the static per-tier tables via the singular
    ``_at`` delegates, not the resolver's ``grace`` bit)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    bundle = dict(
        features=[paid_f],
        runtimes=[paid_r],
        channels=1000,
        retention_days=999,
        nodes=99,
    )
    grace_rows = e.missing_all_at_path("oss", "enterprise", **bundle)

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforced_rows = e.missing_all_at_path("oss", "enterprise", **bundle)
    assert grace_rows == enforced_rows

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


# -- Endpoint: envelope shape ------------------------------------------------


def test_endpoint_envelope_shape_happy_path(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=fleet"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j) == _ENVELOPE_KEYS
    for row in j["path"]:
        assert set(row) == _PER_RUNG_KEYS
        assert set(row["missing"]) == _MISSING_DICT_KEYS


def test_endpoint_envelope_shape_unknown_endpoint(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=bogus&to=oss")
    assert r.status_code == 200
    j = r.get_json()
    assert set(j) == _ENVELOPE_KEYS
    assert j["direction"] == "unknown"
    assert j["path"] == []
    assert j["path_length"] == 0


def test_endpoint_envelope_shape_no_axes(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=oss&to=cloud_pro")
    assert r.status_code == 200
    j = r.get_json()
    assert set(j) == _ENVELOPE_KEYS
    assert j["direction"] == "upgrade"
    assert j["supplied_axes"] == []
    assert j["supplied_count"] == 0
    assert j["any_denied"] is False


def test_endpoint_envelope_shape_missing_params(client):
    r = client.get("/api/entitlement/missing-all-at-path")
    assert r.status_code == 200
    j = r.get_json()
    assert set(j) == _ENVELOPE_KEYS
    assert j["direction"] == "unknown"
    assert j["path"] == []


# -- Endpoint: direction values ----------------------------------------------


def test_endpoint_direction_upgrade(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=oss&to=enterprise")
    assert r.get_json()["direction"] == "upgrade"


def test_endpoint_direction_downgrade(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=enterprise&to=oss")
    assert r.get_json()["direction"] == "downgrade"


def test_endpoint_direction_lateral(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=cloud_pro&to=pro")
    assert r.get_json()["direction"] == "lateral"


def test_endpoint_direction_identity(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=oss&to=oss")
    j = r.get_json()
    assert j["direction"] == "identity"
    assert j["path"] == []


def test_endpoint_direction_unknown(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=bogus&to=oss")
    assert r.get_json()["direction"] == "unknown"


# -- Endpoint: typo posture --------------------------------------------------


def test_endpoint_unknown_feature_surfaces_in_per_rung_and_envelope(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=bogus"
    )
    j = r.get_json()
    assert j["unknown_features"] == ["bogus"]
    assert j["all_denied"] is True
    assert j["any_denied"] is True
    for row in j["path"]:
        assert "bogus" in row["missing"]["features"]


def test_endpoint_unknown_runtime_surfaces(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&runtimes=bogus"
    )
    j = r.get_json()
    assert j["unknown_runtimes"] == ["bogus"]
    assert j["all_denied"] is True
    for row in j["path"]:
        assert "bogus" in row["missing"]["runtimes"]


def test_endpoint_non_int_capacity_surfaces_raw_string_on_every_rung(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=cloud_pro&channels=abc"
    )
    j = r.get_json()
    # Endpoint-layer typo posture: raw string surfaces per rung so a UI
    # can flag the typo (paired with the boolean-fold sibling's fail-
    # closed False on the same input).
    assert j["all_denied"] is True
    for row in j["path"]:
        assert row["missing"]["channels"] == "abc"


def test_endpoint_runtime_alias_canonicalisation_upstream(client):
    """``claude-code`` collapses to ``claude_code`` before the scalar
    sees it; alias-and-canonical pair dedups to ONE entry."""
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=cloud_pro&runtimes=claude-code"
    )
    j = r.get_json()
    assert j["runtimes"] == ["claude_code"]
    assert j["unknown_runtimes"] == []


def test_endpoint_alias_and_canonical_pair_dedups(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path"
        "?from=oss&to=cloud_pro&runtimes=claude-code,claude_code"
    )
    j = r.get_json()
    assert j["runtimes"] == ["claude_code"]


# -- Endpoint: scalar-vs-endpoint parity on known-only subsets --------------


def test_endpoint_per_rung_missing_matches_scalar_on_known_only(client, ent):
    """Endpoint's per-rung ``missing`` on the known-only subset is a
    strict superset of the module scalar (unknown tokens are appended
    at endpoint layer for the diagnostics tooltip)."""
    r = client.get(
        "/api/entitlement/missing-all-at-path"
        "?from=oss&to=enterprise&features=fleet,claude_code"
    )
    j = r.get_json()
    for row in j["path"]:
        scalar = ent.missing_all_at(row["tier"], features=["fleet"])
        # 'claude_code' is not a feature id -> falls into unknown_features
        # for the endpoint layer; the scalar sees only the known subset.
        assert scalar["features"] == row["missing"]["features"] or (
            "claude_code" in row["missing"]["features"]
            and set(row["missing"]["features"]) - {"claude_code"} == set(scalar["features"])
        )


# -- Endpoint: rung-vs-singular parity --------------------------------------


def test_endpoint_per_rung_matches_missing_all_at_endpoint(client):
    """Per-rung ``missing`` byte-equals ``/missing-all-at?tier=<rung>&<same bundle>``
    for the same (rung, bundle) pair -- pins the path endpoint against
    the singular endpoint the same way the scalar tests pin the module
    functions."""
    qs = "from=oss&to=enterprise&features=fleet&runtimes=claude_code&channels=100"
    j = client.get(f"/api/entitlement/missing-all-at-path?{qs}").get_json()
    for row in j["path"]:
        single = client.get(
            f"/api/entitlement/missing-all-at?tier={row['tier']}&features=fleet"
            f"&runtimes=claude_code&channels=100"
        ).get_json()
        # Per-rung ``missing`` slots correspond to the singular envelope's
        # per-axis slots (features, runtimes, channels, retention_days, nodes).
        for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
            assert row["missing"][axis] == single[axis], (
                f"drift on rung {row['tier']} axis {axis}: "
                f"path={row['missing'][axis]!r} vs singular={single[axis]!r}"
            )


# -- Endpoint: rollups --------------------------------------------------------


def test_endpoint_denied_count_reflects_row_any_denial(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=enterprise&to=oss&features=fleet"
    )
    j = r.get_json()
    # Only the oss rung (destination) lacks fleet; the three above grant it.
    assert j["denied_count"] == 1
    assert j["any_denied"] is True
    assert j["all_denied"] is False


def test_endpoint_all_denied_fold_empty_path_false(client):
    r = client.get("/api/entitlement/missing-all-at-path?from=oss&to=oss")
    j = r.get_json()
    assert j["path"] == []
    assert j["all_denied"] is False
    assert j["any_denied"] is False


def test_endpoint_required_tier_folds_known_only_subset(client):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=fleet"
    )
    j = r.get_json()
    # min_tier_for_features(["fleet"]) == "cloud_starter" (verified in the
    # broader entitlement suite).
    assert j["required_tier"] == "cloud_starter"
    assert j["required_tier_rank"] >= 0
    assert j["required_tier_label"]


# -- Grace / enforce parity at endpoint layer -------------------------------


def test_endpoint_grace_reports_grace_true_and_enforced_false(client, ent):
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=fleet"
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


# -- Never raises ------------------------------------------------------------


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    """If the scalar blows up, the endpoint falls back to the empty-path
    envelope (never 5xxs)."""
    import routes.entitlement as _routes

    def _boom(*a, **kw):
        raise RuntimeError("simulated")

    monkeypatch.setattr(_routes, "_missing_all_at_path_body", _boom)
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=fleet"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["path"] == []
    assert j["direction"] in {"identity", "unknown"}
    assert j["all_denied"] is False
    assert j["any_denied"] is False


def test_endpoint_fallback_envelope_shape(client, monkeypatch):
    import routes.entitlement as _routes

    def _boom(*a, **kw):
        raise RuntimeError("simulated")

    monkeypatch.setattr(_routes, "_missing_all_at_path_body", _boom)
    r = client.get(
        "/api/entitlement/missing-all-at-path?from=oss&to=enterprise&features=bogus"
    )
    j = r.get_json()
    assert set(j) == _ENVELOPE_KEYS
    assert j["unknown_features"] == ["bogus"]
