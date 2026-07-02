"""Tests for the bare (source-aware) directional 5-axis batch
projections ``Entitlement.next_tier_lock_reason_batch`` /
``Entitlement.previous_tier_lock_reason_batch``, their module-level
convenience wrappers, and the two companion
``/api/entitlement/{next,previous}-tier-lock-reason-batch`` endpoints.

Batch sibling of the scalar bare projection
``Entitlement.next_tier_lock_reason`` / ``previous_tier_lock_reason``
(single item, resolved current tier) and current-relative sibling of
the tier-parameterised
``next_tier_lock_reason_at_batch`` / ``previous_tier_lock_reason_at_batch``
family (5-axis matrix what-if, arbitrary source tier). Where the scalar
bare projection walks ONE item against ``self.next_purchasable_tier()``,
this batch sibling walks N items across all 5 axes against that same
rung in ONE round-trip -- source-aware target resolution (picks
``cloud_*`` when ``source == "cloud"``, self-hosted otherwise).

Fills the lock-reason-axis batch member of the resolved-tier
``next_*_batch`` / ``previous_*_batch`` family alongside the existing:

* :meth:`Entitlement.next_tier_feature_spec_batch` /
  :meth:`Entitlement.previous_tier_feature_spec_batch`
* :meth:`Entitlement.next_tier_runtime_spec_batch` /
  :meth:`Entitlement.previous_tier_runtime_spec_batch`

Pins covered here:

* per-rung byte-equality with :func:`lock_reasons_at_batch` at the
  resolved next / previous purchasable target (parity, all five axes)
* per-rung byte-equality with the source-agnostic
  :func:`next_tier_lock_reason_at_batch` /
  :func:`previous_tier_lock_reason_at_batch` sibling for every source
  where source-aware and source-agnostic resolve to the same rung
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  still emit per-item rows with ``reason=null`` / ``locked=false`` /
  ``allowed=true`` so the matrix's row count stays stable (no shape
  branch for edge tiers)
* trial-as-source resolves the same way the sibling ``_batch``
  families do: next -> enterprise, previous -> starter
* capacity axes (``channels`` / ``retention_days`` / ``nodes``) route
  through the batch helper's kwarg surface just like
  :func:`lock_reasons_at_batch`
* grace vs enforce yields byte-identical bodies (catalogue-derived)
* module-level wrappers match the bound method on the resolved
  entitlement, and fall back to the grace-shape 5-axis envelope on a
  synthesised resolver failure
* helpers never raise -- a builder failure short-circuits to grace-
  shape rows so the matrix keeps rendering rather than 500-ing
* the two API endpoints never 5xx: 400 on no-axis, 200 with grace-
  shape rows at the ceiling / floor; an internal failure yields the
  same 200 envelope shape
* the endpoint response is byte-identical to the helper body plus a
  ``current_tier`` / ``target`` echo -- parity pin so the two batch
  surfaces cannot drift
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}

_HELPER_BATCH_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}

_API_ENVELOPE_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "grace",
    "enforced",
}


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def _some_features(ent):
    # A short deterministic slice of features so the batch has non-trivial
    # content to parity-check.
    return sorted(ent.ALL_FEATURES)[:3]


def _some_runtimes(ent):
    return sorted(ent.ALL_RUNTIMES)[:3]


# ── Entitlement.next_tier_lock_reason_batch: shape ──────────────────────────


def test_next_helper_returns_dict_with_axis_keys(ent):
    e = ent._build(ent.TIER_OSS, "test")
    out = e.next_tier_lock_reason_batch(features=_some_features(ent))
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_BATCH_KEYS


def test_next_helper_features_row_shape(ent):
    e = ent._build(ent.TIER_OSS, "test")
    features = _some_features(ent)
    out = e.next_tier_lock_reason_batch(features=features)
    assert isinstance(out["features"], list)
    assert len(out["features"]) == len(features)
    for row in out["features"]:
        assert set(row.keys()) == _ROW_KEYS


def test_next_helper_every_purchasable_tier_returns_dict(ent):
    features = _some_features(ent)
    for tier in ent._TIER_ORDER:
        e = ent._build(tier, "test")
        out = e.next_tier_lock_reason_batch(features=features)
        assert isinstance(out, dict), tier
        assert set(out.keys()) == _HELPER_BATCH_KEYS


# ── byte-parity with lock_reasons_at_batch at the resolved target ───────────


def test_next_helper_body_equals_lock_reasons_at_batch_target(ent):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    for tier in ent._TIER_ORDER:
        e = ent._build(tier, "test")
        target = e.next_purchasable_tier()
        got = e.next_tier_lock_reason_batch(
            features=features,
            runtimes=runtimes,
            channels=5,
            retention_days=30,
            nodes=3,
        )
        if target is None:
            # Ceiling -> grace-shape rows for every supplied item.
            for row in got["features"] + got["runtimes"]:
                assert row["reason"] is None
                assert row["locked"] is False
                assert row["allowed"] is True
            assert got["channels"] is not None
            assert got["retention_days"] is not None
            assert got["nodes"] is not None
        else:
            assert got == ent.lock_reasons_at_batch(
                target,
                features=features,
                runtimes=runtimes,
                channels=5,
                retention_days=30,
                nodes=3,
            )


def test_previous_helper_body_equals_lock_reasons_at_batch_target(ent):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    for tier in ent._TIER_ORDER:
        e = ent._build(tier, "test")
        target = e.previous_purchasable_tier()
        got = e.previous_tier_lock_reason_batch(
            features=features,
            runtimes=runtimes,
        )
        if target is None:
            for row in got["features"] + got["runtimes"]:
                assert row["reason"] is None
                assert row["locked"] is False
                assert row["allowed"] is True
        else:
            assert got == ent.lock_reasons_at_batch(
                target,
                features=features,
                runtimes=runtimes,
            )


# ── parity with the source-agnostic _at_batch sibling ───────────────────────


def test_next_helper_matches_at_batch_when_target_matches(ent):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    for tier in ent._TIER_ORDER:
        # Skip trial (source-aware vs source-agnostic can pick different
        # rungs at the free/starter boundary; parity holds when both
        # resolvers agree).
        e = ent._build(tier, "test")
        aware = e.next_purchasable_tier()
        agnostic = ent._next_purchasable_tier_after(tier)
        if aware != agnostic:
            continue
        bare = e.next_tier_lock_reason_batch(
            features=features, runtimes=runtimes
        )
        at = ent.next_tier_lock_reason_at_batch(
            tier, features=features, runtimes=runtimes
        )
        assert bare == at, tier


def test_previous_helper_matches_at_batch_when_target_matches(ent):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    for tier in ent._TIER_ORDER:
        e = ent._build(tier, "test")
        aware = e.previous_purchasable_tier()
        agnostic = ent._previous_purchasable_tier_before(tier)
        if aware != agnostic:
            continue
        bare = e.previous_tier_lock_reason_batch(
            features=features, runtimes=runtimes
        )
        at = ent.previous_tier_lock_reason_at_batch(
            tier, features=features, runtimes=runtimes
        )
        assert bare == at, tier


# ── ceiling / floor ─────────────────────────────────────────────────────────


def test_next_helper_at_ceiling_returns_grace_rows(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    features = _some_features(ent)
    out = e.next_tier_lock_reason_batch(features=features)
    assert [row["key"] for row in out["features"]] == features
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


def test_previous_helper_at_floor_returns_grace_rows(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        features = _some_features(ent)
        out = e.previous_tier_lock_reason_batch(features=features)
        assert [row["key"] for row in out["features"]] == features
        for row in out["features"]:
            assert row["reason"] is None
            assert row["locked"] is False
            assert row["allowed"] is True


# ── trial source resolution ─────────────────────────────────────────────────


def test_trial_next_batch_resolves_to_enterprise(ent):
    features = _some_features(ent)
    e = ent._build(ent.TIER_TRIAL, "cloud")
    got = e.next_tier_lock_reason_batch(features=features)
    assert got == ent.lock_reasons_at_batch(
        ent.TIER_ENTERPRISE, features=features
    )


def test_trial_previous_batch_resolves_to_starter(ent):
    features = _some_features(ent)
    e = ent._build(ent.TIER_TRIAL, "cloud")
    got = e.previous_tier_lock_reason_batch(features=features)
    assert got == ent.lock_reasons_at_batch(
        ent.TIER_CLOUD_STARTER, features=features
    )


# ── capacity axes ───────────────────────────────────────────────────────────


def test_next_helper_capacity_axes_present(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    out = e.next_tier_lock_reason_batch(
        channels=10, retention_days=60, nodes=5
    )
    assert out["channels"] is not None
    assert out["retention_days"] is not None
    assert out["nodes"] is not None
    assert set(out["channels"].keys()) == _ROW_KEYS
    assert set(out["retention_days"].keys()) == _ROW_KEYS
    assert set(out["nodes"].keys()) == _ROW_KEYS


def test_next_helper_capacity_axes_none_when_not_supplied(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    out = e.next_tier_lock_reason_batch(features=_some_features(ent))
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# ── grace vs enforce ────────────────────────────────────────────────────────


def test_grace_vs_enforce_batch_identical(ent, monkeypatch):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_lock_reason_batch(
        features=features, runtimes=runtimes
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_lock_reason_batch(
        features=features, runtimes=runtimes
    )
    assert enforce_body == grace_body


# ── never raises on resolver failure ────────────────────────────────────────


def test_next_helper_never_raises_on_resolver_failure(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    features = _some_features(ent)
    out = e.next_tier_lock_reason_batch(features=features)
    # Fell through to _empty_lock_reasons_at_batch -> grace-shape rows.
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


def test_previous_helper_never_raises_on_resolver_failure(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    features = _some_features(ent)
    out = e.previous_tier_lock_reason_batch(features=features)
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


# ── module-level wrappers ───────────────────────────────────────────────────


def test_module_level_next_batch_matches_method(ent):
    features = _some_features(ent)
    assert ent.next_tier_lock_reason_batch(features=features) == (
        ent.get_entitlement().next_tier_lock_reason_batch(features=features)
    )


def test_module_level_previous_batch_matches_method(ent):
    features = _some_features(ent)
    assert ent.previous_tier_lock_reason_batch(features=features) == (
        ent.get_entitlement().previous_tier_lock_reason_batch(
            features=features
        )
    )


def test_module_level_next_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    features = _some_features(ent)
    out = ent.next_tier_lock_reason_batch(features=features)
    # Falls back to _empty_lock_reasons_at_batch -> grace-shape rows.
    assert set(out.keys()) == _HELPER_BATCH_KEYS
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


def test_module_level_previous_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    features = _some_features(ent)
    out = ent.previous_tier_lock_reason_batch(features=features)
    assert set(out.keys()) == _HELPER_BATCH_KEYS
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


# ── /api/entitlement/next-tier-lock-reason-batch endpoint ───────────────────


def test_endpoint_next_batch_default_oss(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _API_ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert [row["key"] for row in body["features"]] == features
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_next_batch_body_matches_helper(client, ent):
    features = _some_features(ent)
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason-batch?features="
        + ",".join(features)
        + "&runtimes="
        + ",".join(runtimes)
        + "&channels=5&retention_days=30&nodes=3"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    helper = ent.next_tier_lock_reason_batch(
        features=features,
        runtimes=runtimes,
        channels=5,
        retention_days=30,
        nodes=3,
    )
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert body[axis] == helper[axis], axis


def test_endpoint_next_batch_missing_axis_returns_400(client):
    rv = client.get("/api/entitlement/next-tier-lock-reason-batch")
    assert rv.status_code == 400
    err = rv.get_json()["error"]
    assert "features" in err
    assert "runtimes" in err
    assert "channels" in err


def test_endpoint_next_batch_empty_csv_and_no_capacity_returns_400(client):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason-batch?features=&runtimes=,"
    )
    assert rv.status_code == 400


def test_endpoint_next_batch_capacity_only_returns_200(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason-batch?channels=5"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


# ── /api/entitlement/previous-tier-lock-reason-batch endpoint ───────────────


def test_endpoint_previous_batch_at_floor(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    # Default resolved tier is OSS -> no rung below.
    assert body["current_tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    # But per-feature rows still render so the matrix's row count stays
    # stable.
    assert [row["key"] for row in body["features"]] == features
    for row in body["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True


def test_endpoint_previous_batch_missing_axis_returns_400(client):
    rv = client.get("/api/entitlement/previous-tier-lock-reason-batch")
    assert rv.status_code == 400


def test_endpoint_previous_batch_body_matches_helper(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason-batch?features="
        + ",".join(features)
    )
    body = rv.get_json()
    helper = ent.previous_tier_lock_reason_batch(features=features)
    assert body["features"] == helper["features"]
    assert body["runtimes"] == helper["runtimes"]


def test_endpoint_never_5xx_on_internal_failure(client, monkeypatch):
    import clawmetry.entitlements as ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason-batch?features=x"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _API_ENVELOPE_KEYS
    assert body["grace"] is True
    assert body["enforced"] is False
