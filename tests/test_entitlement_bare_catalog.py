"""Tests for the bare ``/api/entitlement/{feature,runtime,tier}-catalog``
endpoints.

These are the bare siblings of the ``*-catalog-at`` what-if endpoints.
Where ``-catalog-at?tier=X`` hydrates the catalogue as if the install
were on tier ``X``, the bare form hydrates it for the *resolved*
entitlement. Both share the same ``{tier, features/runtimes/tiers,
grace, enforced}`` envelope so a pricing UI can swap between "current"
and "hypothetical" without reshaping.

The bare catalogs are already served under the legacy
``/api/features``, ``/api/runtimes``, ``/api/tiers`` URLs; these tests
pin the new aliases under ``/api/entitlement/`` and defend the
never-5xx contract.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default -- grace mode is the current shipping default
    and the bare catalog must render correctly in it."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── feature-catalog ────────────────────────────────────────────────────────────


def test_feature_catalog_200(client):
    resp = client.get("/api/entitlement/feature-catalog")
    assert resp.status_code == 200


def test_feature_catalog_envelope_shape(client):
    body = client.get("/api/entitlement/feature-catalog").get_json()
    assert set(body.keys()) == {"tier", "features", "grace", "enforced"}
    assert isinstance(body["features"], list)
    assert isinstance(body["tier"], str)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_feature_catalog_grace_and_enforced_are_negations(client):
    body = client.get("/api/entitlement/feature-catalog").get_json()
    assert body["grace"] is not body["enforced"]


def test_feature_catalog_tier_matches_resolved(client, ent):
    body = client.get("/api/entitlement/feature-catalog").get_json()
    assert body["tier"] == ent.get_entitlement().tier


def test_feature_catalog_rows_match_helper(client, ent):
    """Byte-parity with :func:`feature_catalog` -- a pricing UI reading
    the bare endpoint must see the same rows the helper produces."""
    body = client.get("/api/entitlement/feature-catalog").get_json()
    assert body["features"] == ent.feature_catalog()


def test_feature_catalog_covers_every_feature(client, ent):
    body = client.get("/api/entitlement/feature-catalog").get_json()
    assert len(body["features"]) == len(ent.ALL_FEATURES)
    ids = {row["id"] for row in body["features"]}
    assert ids == set(ent.ALL_FEATURES)


def test_feature_catalog_never_5xxs_on_helper_failure(client, ent, monkeypatch):
    """The endpoint must not 500 when the helper explodes. It falls back
    to the OSS-free envelope so the pricing UI keeps rendering."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper failure")

    monkeypatch.setattr(ent, "feature_catalog", boom)
    resp = client.get("/api/entitlement/feature-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


# ── runtime-catalog ────────────────────────────────────────────────────────────


def test_runtime_catalog_200(client):
    resp = client.get("/api/entitlement/runtime-catalog")
    assert resp.status_code == 200


def test_runtime_catalog_envelope_shape(client):
    body = client.get("/api/entitlement/runtime-catalog").get_json()
    assert set(body.keys()) == {"tier", "runtimes", "grace", "enforced"}
    assert isinstance(body["runtimes"], list)


def test_runtime_catalog_grace_and_enforced_are_negations(client):
    body = client.get("/api/entitlement/runtime-catalog").get_json()
    assert body["grace"] is not body["enforced"]


def test_runtime_catalog_tier_matches_resolved(client, ent):
    body = client.get("/api/entitlement/runtime-catalog").get_json()
    assert body["tier"] == ent.get_entitlement().tier


def test_runtime_catalog_rows_match_helper(client, ent):
    body = client.get("/api/entitlement/runtime-catalog").get_json()
    assert body["runtimes"] == ent.runtime_catalog()


def test_runtime_catalog_lists_free_before_paid(client, ent):
    """Ordering contract: free runtimes come before paid runtimes (matches
    :func:`runtime_catalog`)."""
    rows = client.get("/api/entitlement/runtime-catalog").get_json()["runtimes"]
    ids = [row["id"] for row in rows]
    free_positions = [ids.index(r) for r in ent.FREE_RUNTIMES if r in ids]
    paid_positions = [ids.index(r) for r in ent.PAID_RUNTIMES if r in ids]
    if free_positions and paid_positions:
        assert max(free_positions) < min(paid_positions)


def test_runtime_catalog_never_5xxs_on_helper_failure(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper failure")

    monkeypatch.setattr(ent, "runtime_catalog", boom)
    resp = client.get("/api/entitlement/runtime-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtimes"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


# ── tier-catalog ───────────────────────────────────────────────────────────────


def test_tier_catalog_200(client):
    resp = client.get("/api/entitlement/tier-catalog")
    assert resp.status_code == 200


def test_tier_catalog_envelope_shape(client):
    body = client.get("/api/entitlement/tier-catalog").get_json()
    assert set(body.keys()) == {"tier", "tiers", "grace", "enforced"}
    assert isinstance(body["tiers"], list)


def test_tier_catalog_grace_and_enforced_are_negations(client):
    body = client.get("/api/entitlement/tier-catalog").get_json()
    assert body["grace"] is not body["enforced"]


def test_tier_catalog_tier_matches_resolved(client, ent):
    body = client.get("/api/entitlement/tier-catalog").get_json()
    assert body["tier"] == ent.get_entitlement().tier


def test_tier_catalog_rows_match_helper(client, ent):
    body = client.get("/api/entitlement/tier-catalog").get_json()
    assert body["tiers"] == ent.tier_catalog()


def test_tier_catalog_is_current_lines_up_with_tier_field(client):
    """The rung marked ``is_current=True`` in ``tiers`` must be the one
    identified by the top-level ``tier`` field -- otherwise a UI would
    highlight one row and label the header with a different tier id."""
    body = client.get("/api/entitlement/tier-catalog").get_json()
    current_rows = [r for r in body["tiers"] if r.get("is_current")]
    assert len(current_rows) == 1
    assert current_rows[0]["id"] == body["tier"]


def test_tier_catalog_covers_every_known_tier(client, ent):
    body = client.get("/api/entitlement/tier-catalog").get_json()
    ids = [row["id"] for row in body["tiers"]]
    assert ids == list(ent._TIER_ORDER)


def test_tier_catalog_never_5xxs_on_helper_failure(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper failure")

    monkeypatch.setattr(ent, "tier_catalog", boom)
    resp = client.get("/api/entitlement/tier-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


# ── parity with `-at` sibling ──────────────────────────────────────────────────


def test_feature_catalog_bare_parity_with_at_at_resolved_tier(client, ent):
    """The bare endpoint at the resolved tier and the ``-at`` endpoint
    parameterised with the resolved tier must return the same rows (only
    the envelope differs: the bare form adds ``grace`` / ``enforced``,
    the ``-at`` form echoes the requested ``tier``). Pins the "swap
    without reshaping" promise: rows are one-to-one."""
    resolved = ent.get_entitlement().tier
    bare = client.get("/api/entitlement/feature-catalog").get_json()
    atr = client.get(
        f"/api/entitlement/feature-catalog-at?tier={resolved}"
    ).get_json()
    bare_ids = [r["id"] for r in bare["features"]]
    at_ids = [r["id"] for r in atr["features"]]
    assert bare_ids == at_ids


def test_runtime_catalog_bare_parity_with_at_at_resolved_tier(client, ent):
    resolved = ent.get_entitlement().tier
    bare = client.get("/api/entitlement/runtime-catalog").get_json()
    atr = client.get(
        f"/api/entitlement/runtime-catalog-at?tier={resolved}"
    ).get_json()
    bare_ids = [r["id"] for r in bare["runtimes"]]
    at_ids = [r["id"] for r in atr["runtimes"]]
    assert bare_ids == at_ids


def test_tier_catalog_bare_parity_with_at_at_resolved_tier(client, ent):
    """Rows from the bare tier-catalog and the ``-at`` sibling at the
    resolved tier must match exactly -- the ``-at`` sibling's whole
    point is that its rows are byte-identical to :func:`tier_catalog`
    when the perspective is the live resolved tier."""
    resolved = ent.get_entitlement().tier
    bare = client.get("/api/entitlement/tier-catalog").get_json()
    atr = client.get(
        f"/api/entitlement/tier-catalog-at?tier={resolved}"
    ).get_json()
    assert bare["tiers"] == atr["tiers"]


# ── legacy alias parity ────────────────────────────────────────────────────────


def test_feature_catalog_matches_legacy_features_endpoint(client):
    """The bare ``/api/entitlement/feature-catalog`` must return the same
    catalogue rows as the legacy ``/api/features`` alias -- the two
    surfaces share a helper and must not drift."""
    bare = client.get("/api/entitlement/feature-catalog").get_json()
    legacy = client.get("/api/features").get_json()
    assert bare["features"] == legacy["features"]
    assert bare["grace"] == legacy["grace"]
    assert bare["enforced"] == legacy["enforced"]


def test_runtime_catalog_matches_legacy_runtimes_endpoint(client):
    bare = client.get("/api/entitlement/runtime-catalog").get_json()
    legacy = client.get("/api/runtimes").get_json()
    assert bare["runtimes"] == legacy["runtimes"]
    assert bare["grace"] == legacy["grace"]
    assert bare["enforced"] == legacy["enforced"]


def test_tier_catalog_matches_legacy_tiers_endpoint(client):
    """Rows must match ``/api/tiers``; the bare endpoint just renames
    ``current`` to ``tier`` for symmetry with the ``-at`` sibling."""
    bare = client.get("/api/entitlement/tier-catalog").get_json()
    legacy = client.get("/api/tiers").get_json()
    assert bare["tiers"] == legacy["tiers"]
    assert bare["tier"] == legacy["current"]
    assert bare["grace"] == legacy["grace"]
    assert bare["enforced"] == legacy["enforced"]
