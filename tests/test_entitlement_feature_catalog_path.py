"""Tests for ``clawmetry.entitlements.feature_catalog_path(from, to)`` + the
``GET /api/entitlement/feature-catalog-path`` endpoint.

Full-catalog path sibling of :func:`feature_spec_path` (single feature per
rung) and path-shaped sibling of :func:`feature_catalog_at_batch` (multi-
source what-if matrix). Where the parent scalar helper hydrates the feature
catalog at ONE hypothetical tier, this helper hydrates it at every rung
between two tiers off ONE round-trip -- the natural payload for an
upgrade-walkthrough UI that renders the full catalog card at each step.

Pins:

* per-rung row shape matches :func:`feature_catalog_at_batch` (``tier``,
  ``tier_label``, ``tier_rank``, ``features``) -- byte-stable so a UI can
  swap between the batch and the path without reshaping
* each ``features`` list byte-equals :func:`feature_catalog_at` for the
  same rung -- pinned so the scalar, batch and path what-if surfaces
  cannot drift
* rung walk byte-equals :func:`tier_path` on the destination axis and
  :func:`tier_spec_path` / :func:`feature_spec_path` /
  :func:`runtime_spec_path` on the perspective axis -- the ``_path``
  family stays in lock-step
* identity (``from == to``) -> ``[]``; lateral (same rank, different id)
  -> single-row path; ``trial`` accepted as an endpoint (excluded from
  the walked rungs but valid via the lateral branch)
* helper is decoupled from the resolver -- grace vs enforce yields the
  same rows
* unknown / empty / garbage ids return ``None`` and never raise; a
  synthesised failure in the inner row builder short-circuits to
  ``None``
* API: 400 on missing args, 404 on unknown ids, 200 with the standard
  ``_path`` envelope on the happy path; 404 (not 5xx) when the inner
  helper blows up
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


_ROW_KEYS = {"tier", "tier_label", "tier_rank", "features"}
_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
}


# ── helper: shape + per-row contract ─────────────────────────────────────


def test_returns_list(ent):
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_batch_row_shape(ent):
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["features"], list)


def test_last_rung_is_destination(ent):
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE
    assert path[-1]["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert path[-1]["tier_rank"] == ent._TIER_RANK[ent.TIER_ENTERPRISE]


# ── byte-parity with the scalar / batch what-if catalog helpers ──────────


def test_features_list_byte_equals_feature_catalog_at(ent):
    """Each rung's ``features`` list is what :func:`feature_catalog_at`
    returns for the same tier -- the scalar and path what-if catalog
    surfaces cannot drift."""
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["features"] == ent.feature_catalog_at(row["tier"])


def test_row_byte_equals_batch_row(ent):
    """A rung row is byte-identical to the same row from
    :func:`feature_catalog_at_batch` -- the batch and path surfaces
    stay in sync so a UI can switch between them freely."""
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    tiers = [row["tier"] for row in path]
    batch = ent.feature_catalog_at_batch(tiers)
    assert path == batch["tiers"]


# ── rung walk parity with the rest of the _path family ───────────────────


def test_rung_walk_byte_equal_to_tier_path(ent):
    catalog = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    full = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in catalog] == [r["to"] for r in full]


def test_rung_walk_byte_equal_to_tier_spec_path(ent):
    catalog = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    spec = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in catalog] == [r["id"] for r in spec]


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must
    end exactly at ``pro`` and EXCLUDE the same-rank sibling
    ``cloud_pro`` from the final rung -- same rule as ``tier_path``."""
    tiers = [
        r["tier"]
        for r in ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_PRO)
    ]
    assert tiers[-1] == ent.TIER_PRO
    assert tiers.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in tiers


def test_same_rank_siblings_between_endpoints_both_included(ent):
    tiers = [
        r["tier"]
        for r in ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    ]
    assert ent.TIER_CLOUD_PRO in tiers
    assert ent.TIER_PRO in tiers
    assert tiers[-1] == ent.TIER_ENTERPRISE


# ── identity / lateral / adjacent ────────────────────────────────────────


def test_identity_returns_empty(ent):
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        assert ent.feature_catalog_path(tid, tid) == []


def test_lateral_is_single_row(ent):
    path = ent.feature_catalog_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_PRO
    assert path[0]["features"] == ent.feature_catalog_at(ent.TIER_PRO)


def test_oss_to_cloud_free_lateral(ent):
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER


# ── descending mirror ───────────────────────────────────────────────────


def test_descending_path_terminates_at_to(ent):
    path = ent.feature_catalog_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[-1]["tier"] == ent.TIER_OSS
    # closest-to-from rung first
    assert (
        ent._TIER_RANK[path[0]["tier"]]
        < ent._TIER_RANK[ent.TIER_ENTERPRISE]
    )


def test_descending_terminates_at_explicit_floor(ent):
    """Asking for ``oss`` must NOT also include ``cloud_free`` (the
    other rank-0 sibling) as a terminal rung."""
    tiers = [
        r["tier"]
        for r in ent.feature_catalog_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    ]
    assert tiers[-1] == ent.TIER_OSS
    assert tiers.count(ent.TIER_OSS) == 1


# ── trial endpoint ───────────────────────────────────────────────────────


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on
    a path between purchasable tiers, but resolves as an endpoint."""
    path = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL
    upward = ent.feature_catalog_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE
    downward = ent.feature_catalog_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_OSS


# ── decoupled from the resolver ──────────────────────────────────────────


def test_grace_and_enforce_yield_identical_rows(ent, enforced):
    grace_rows = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    enforced_rows = enforced.feature_catalog_path(
        enforced.TIER_OSS, enforced.TIER_ENTERPRISE
    )
    assert grace_rows == enforced_rows


# ── unknown / garbage inputs never raise ─────────────────────────────────


def test_unknown_tiers_return_none(ent):
    assert (
        ent.feature_catalog_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    )
    assert (
        ent.feature_catalog_path(ent.TIER_OSS, "still_not_a_tier") is None
    )
    assert ent.feature_catalog_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.feature_catalog_path("", "") is None
    assert ent.feature_catalog_path(None, None) is None  # type: ignore[arg-type]
    assert ent.feature_catalog_path("  ", "  ") is None
    assert ent.feature_catalog_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.feature_catalog_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_helper_swallows_resolver_failure(monkeypatch, ent):
    """If the inner catalog builder blows up, the helper must short-
    circuit to ``None`` (logged-warning + graceful fallback contract)."""

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "feature_catalog_at", boom)
    assert (
        ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE) is None
    )


# ── API surface ──────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert (
        client.get("/api/entitlement/feature-catalog-path").status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/feature-catalog-path?from=oss"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/feature-catalog-path?to=cloud_pro"
        ).status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/feature-catalog-path?from=oss&to=not_a_tier"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["tier"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_path_byte_equals_helper(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["path"] == ent.feature_catalog_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE
    )


def test_api_404_on_resolver_failure(monkeypatch, client):
    """Force the resolver path used by the route to blow up; the route
    must short-circuit to a 404 envelope instead of leaking a 500."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "feature_catalog_path", boom)
    r = client.get(
        "/api/entitlement/feature-catalog-path?from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
