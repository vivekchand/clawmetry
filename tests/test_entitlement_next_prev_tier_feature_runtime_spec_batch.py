"""Tests for the bare (source-aware) directional per-axis batch
projections ``Entitlement.next_tier_feature_spec_batch`` /
``Entitlement.previous_tier_feature_spec_batch`` /
``Entitlement.next_tier_runtime_spec_batch`` /
``Entitlement.previous_tier_runtime_spec_batch``, their module-level
convenience wrappers, and the four companion
``/api/entitlement/{next,previous}-tier-{feature,runtime}-spec-batch``
endpoints.

Batch sibling of the scalar bare projections
(``next/previous_tier_{feature,runtime}_spec``, merged in #3452) and
current-relative sibling of the tier-parameterised
``next/previous_tier_{feature,runtime}_spec_at_batch`` family (merged in
#3401). Where the scalar bare projection walks ONE item against
``self.next_purchasable_tier()``, this batch sibling walks N items
against that same rung in ONE round-trip -- source-aware target
resolution (picks ``cloud_*`` when ``source == "cloud"``, self-hosted
otherwise).

Pins covered here:

* per-row byte-equality with the scalar bare sibling
  ``next/previous_tier_{feature,runtime}_spec(item)`` across every
  purchasable source
* ceiling / floor produces per-row ``row=null`` with envelope entries
  still rendered so the matrix keeps a stable row count
* trial-as-source resolves next -> enterprise, previous -> starter
  (matches sibling scalar family)
* input normalisation (whitespace, lowercase, duplicate drop, first-seen
  order preserved)
* unknown ids bucketed in ``unknown[]`` alongside valid rows rather than
  short-circuiting
* runtime alias canonicalisation + alias-to-canonical de-duplication
* grace vs enforce yields byte-identical bodies (catalogue-derived)
* module-level wrappers match the bound method on the resolved
  entitlement
* helpers never raise on synthesised resolver failure; module-level
  wrappers fall back to an empty envelope
* HTTP 400 / 200 error envelopes on all four endpoints (missing csv,
  never-5xx grace fallback)
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_FEATURE_ROW_KEYS = {"feature", "row"}
_RUNTIME_ROW_KEYS = {"runtime", "row"}
_FEATURE_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
    "unknown",
    "grace",
    "enforced",
}
_RUNTIME_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
    "unknown",
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
    # A short deterministic slice of features spanning free + paid axes so the
    # batch has non-trivial content to parity-check.
    return sorted(ent.ALL_FEATURES)[:3]


def _some_runtimes(ent):
    return sorted(ent.ALL_RUNTIMES)[:3]


# ── Entitlement.next_tier_feature_spec_batch ────────────────────────────────


def test_next_tier_feature_spec_batch_parity_with_scalar(ent):
    # Each row must byte-equal next_tier_feature_spec(feature) so the scalar
    # and batch accessors cannot drift.
    features = _some_features(ent)
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        body = e.next_tier_feature_spec_batch(features)
        assert set(body.keys()) == {"features", "unknown"}
        assert body["unknown"] == []
        assert [row["feature"] for row in body["features"]] == features
        for row in body["features"]:
            assert set(row.keys()) == _FEATURE_ROW_KEYS
            assert row["row"] == e.next_tier_feature_spec(row["feature"])


def test_next_tier_feature_spec_batch_at_ceiling(ent):
    # Enterprise has no rung above -- every row should be null but the
    # per-feature entries still render so the row count stays stable.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    features = _some_features(ent)
    body = e.next_tier_feature_spec_batch(features)
    assert [row["feature"] for row in body["features"]] == features
    assert all(row["row"] is None for row in body["features"])
    assert body["unknown"] == []


def test_next_tier_feature_spec_batch_normalises_input(ent):
    # Duplicates dropped, whitespace stripped, case-lowered, first-seen order
    # preserved -- shared _normalise_csv posture.
    features = _some_features(ent)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    raw = f"  {features[0].upper()}  ,{features[1]},{features[0]},, "
    body = e.next_tier_feature_spec_batch(raw)
    assert [row["feature"] for row in body["features"]] == features[:2]
    assert body["unknown"] == []


def test_next_tier_feature_spec_batch_unknown_ids_bucketed(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    features = _some_features(ent)
    body = e.next_tier_feature_spec_batch(
        [features[0], "no_such_feature", features[1]]
    )
    assert [row["feature"] for row in body["features"]] == features[:2]
    assert body["unknown"] == ["no_such_feature"]


def test_next_tier_feature_spec_batch_empty_csv(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_feature_spec_batch("")
    assert body == {"features": [], "unknown": []}


def test_next_tier_feature_spec_batch_never_raises(ent, monkeypatch):
    # If next_purchasable_tier blows up, the helper must swallow and return
    # rows with row=null so the matrix keeps rendering.
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    features = _some_features(ent)
    body = e.next_tier_feature_spec_batch(features)
    assert [row["feature"] for row in body["features"]] == features
    assert all(row["row"] is None for row in body["features"])


# ── Entitlement.previous_tier_feature_spec_batch ────────────────────────────


def test_previous_tier_feature_spec_batch_parity_with_scalar(ent):
    features = _some_features(ent)
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        body = e.previous_tier_feature_spec_batch(features)
        for row in body["features"]:
            assert row["row"] == e.previous_tier_feature_spec(row["feature"])


def test_previous_tier_feature_spec_batch_at_floor(ent):
    # OSS / cloud_free -- nothing below to step down to.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        features = _some_features(ent)
        body = e.previous_tier_feature_spec_batch(features)
        assert [row["feature"] for row in body["features"]] == features
        assert all(row["row"] is None for row in body["features"])


def test_previous_tier_feature_spec_batch_never_raises(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    features = _some_features(ent)
    body = e.previous_tier_feature_spec_batch(features)
    assert all(row["row"] is None for row in body["features"])


# ── Entitlement.next_tier_runtime_spec_batch ────────────────────────────────


def test_next_tier_runtime_spec_batch_parity_with_scalar(ent):
    runtimes = _some_runtimes(ent)
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        body = e.next_tier_runtime_spec_batch(runtimes)
        assert set(body.keys()) == {"runtimes", "unknown"}
        assert [row["runtime"] for row in body["runtimes"]] == runtimes
        for row in body["runtimes"]:
            assert set(row.keys()) == _RUNTIME_ROW_KEYS
            assert row["row"] == e.next_tier_runtime_spec(row["runtime"])


def test_next_tier_runtime_spec_batch_at_ceiling(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    runtimes = _some_runtimes(ent)
    body = e.next_tier_runtime_spec_batch(runtimes)
    assert [row["runtime"] for row in body["runtimes"]] == runtimes
    assert all(row["row"] is None for row in body["runtimes"])


def test_next_tier_runtime_spec_batch_alias_canonicalisation(ent):
    # claude-code -> claude_code
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code runtime not in catalogue")
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_runtime_spec_batch(["claude-code"])
    assert [row["runtime"] for row in body["runtimes"]] == ["claude_code"]
    assert body["unknown"] == []


def test_next_tier_runtime_spec_batch_alias_collapse(ent):
    # Alias + canonical id must collapse to ONE row on the canonical id.
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code runtime not in catalogue")
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_runtime_spec_batch(["claude-code", "claude_code"])
    assert [row["runtime"] for row in body["runtimes"]] == ["claude_code"]
    assert body["unknown"] == []


def test_next_tier_runtime_spec_batch_unknown_carries_supplied_alias(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_runtime_spec_batch(["no_such_runtime"])
    assert body["runtimes"] == []
    assert body["unknown"] == ["no_such_runtime"]


def test_next_tier_runtime_spec_batch_never_raises(ent, monkeypatch):
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    runtimes = _some_runtimes(ent)
    body = e.next_tier_runtime_spec_batch(runtimes)
    assert all(row["row"] is None for row in body["runtimes"])


# ── Entitlement.previous_tier_runtime_spec_batch ────────────────────────────


def test_previous_tier_runtime_spec_batch_parity_with_scalar(ent):
    runtimes = _some_runtimes(ent)
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        body = e.previous_tier_runtime_spec_batch(runtimes)
        for row in body["runtimes"]:
            assert row["row"] == e.previous_tier_runtime_spec(row["runtime"])


def test_previous_tier_runtime_spec_batch_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        runtimes = _some_runtimes(ent)
        body = e.previous_tier_runtime_spec_batch(runtimes)
        assert all(row["row"] is None for row in body["runtimes"])


# ── trial source resolution ─────────────────────────────────────────────────


def test_trial_next_batch_resolves_to_enterprise(ent):
    # Trial's next purchasable is enterprise.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    features = _some_features(ent)
    body = e.next_tier_feature_spec_batch(features)
    for row in body["features"]:
        expected = ent.feature_spec_at(ent.TIER_ENTERPRISE, row["feature"])
        assert row["row"] == expected


def test_trial_previous_batch_resolves_to_starter(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    features = _some_features(ent)
    body = e.previous_tier_feature_spec_batch(features)
    for row in body["features"]:
        expected = ent.feature_spec_at(ent.TIER_CLOUD_STARTER, row["feature"])
        assert row["row"] == expected


# ── grace vs enforce ────────────────────────────────────────────────────────


def test_grace_vs_enforce_batch_identical(ent, monkeypatch):
    features = _some_features(ent)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_feature_spec_batch(features)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_feature_spec_batch(features)
    assert enforce_body == grace_body


# ── module-level wrappers ───────────────────────────────────────────────────


def test_module_level_next_feature_batch_matches_method(ent):
    features = _some_features(ent)
    assert ent.next_tier_feature_spec_batch(features) == (
        ent.get_entitlement().next_tier_feature_spec_batch(features)
    )


def test_module_level_previous_feature_batch_matches_method(ent):
    features = _some_features(ent)
    assert ent.previous_tier_feature_spec_batch(features) == (
        ent.get_entitlement().previous_tier_feature_spec_batch(features)
    )


def test_module_level_next_runtime_batch_matches_method(ent):
    runtimes = _some_runtimes(ent)
    assert ent.next_tier_runtime_spec_batch(runtimes) == (
        ent.get_entitlement().next_tier_runtime_spec_batch(runtimes)
    )


def test_module_level_previous_runtime_batch_matches_method(ent):
    runtimes = _some_runtimes(ent)
    assert ent.previous_tier_runtime_spec_batch(runtimes) == (
        ent.get_entitlement().previous_tier_runtime_spec_batch(runtimes)
    )


def test_module_level_next_feature_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    features = _some_features(ent)
    assert ent.next_tier_feature_spec_batch(features) == {
        "features": [],
        "unknown": [],
    }


def test_module_level_previous_runtime_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    runtimes = _some_runtimes(ent)
    assert ent.previous_tier_runtime_spec_batch(runtimes) == {
        "runtimes": [],
        "unknown": [],
    }


# ── /api/entitlement/next-tier-feature-spec-batch endpoint ──────────────────


def test_endpoint_next_feature_batch_default_oss(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _FEATURE_ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert [row["feature"] for row in body["features"]] == features
    assert body["unknown"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_next_feature_batch_row_matches_helper(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec-batch?features="
        + ",".join(features)
    )
    body = rv.get_json()
    helper = ent.next_tier_feature_spec_batch(features)
    assert body["features"] == helper["features"]
    assert body["unknown"] == helper["unknown"]


def test_endpoint_next_feature_batch_missing_csv(client):
    rv = client.get("/api/entitlement/next-tier-feature-spec-batch")
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "supply features=<csv>"


def test_endpoint_next_feature_batch_empty_csv(client):
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec-batch?features=,"
    )
    assert rv.status_code == 400


def test_endpoint_next_feature_batch_unknown_bucketed(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec-batch?features="
        + ",".join([features[0], "no_such_feature", features[1]])
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert [row["feature"] for row in body["features"]] == features[:2]
    assert body["unknown"] == ["no_such_feature"]


def test_endpoint_next_feature_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _FEATURE_ENVELOPE_KEYS
    assert body["current_tier"] == "oss"
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["target"] is None


# ── /api/entitlement/previous-tier-feature-spec-batch endpoint ──────────────


def test_endpoint_previous_feature_batch_default_oss_floor(client, ent):
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-feature-spec-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _FEATURE_ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- target and every row is null.
    assert body["target"] is None
    assert all(row["row"] is None for row in body["features"])
    assert [row["feature"] for row in body["features"]] == features


def test_endpoint_previous_feature_batch_missing_csv(client):
    rv = client.get("/api/entitlement/previous-tier-feature-spec-batch")
    assert rv.status_code == 400


def test_endpoint_previous_feature_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    features = _some_features(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-feature-spec-batch?features="
        + ",".join(features)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _FEATURE_ENVELOPE_KEYS
    assert body["features"] == []


# ── /api/entitlement/next-tier-runtime-spec-batch endpoint ──────────────────


def test_endpoint_next_runtime_batch_default_oss(client, ent):
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec-batch?runtimes="
        + ",".join(runtimes)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert [row["runtime"] for row in body["runtimes"]] == runtimes
    assert body["unknown"] == []


def test_endpoint_next_runtime_batch_row_matches_helper(client, ent):
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec-batch?runtimes="
        + ",".join(runtimes)
    )
    body = rv.get_json()
    helper = ent.next_tier_runtime_spec_batch(runtimes)
    assert body["runtimes"] == helper["runtimes"]
    assert body["unknown"] == helper["unknown"]


def test_endpoint_next_runtime_batch_alias_canonicalisation(client, ent):
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code runtime not in catalogue")
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec-batch?runtimes=claude-code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert [row["runtime"] for row in body["runtimes"]] == ["claude_code"]
    assert body["unknown"] == []


def test_endpoint_next_runtime_batch_unknown_carries_supplied_alias(
    client, ent
):
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec-batch?runtimes=no_such_runtime"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["runtimes"] == []
    assert body["unknown"] == ["no_such_runtime"]


def test_endpoint_next_runtime_batch_missing_csv(client):
    rv = client.get("/api/entitlement/next-tier-runtime-spec-batch")
    assert rv.status_code == 400


def test_endpoint_next_runtime_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec-batch?runtimes="
        + ",".join(runtimes)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert body["runtimes"] == []


# ── /api/entitlement/previous-tier-runtime-spec-batch endpoint ──────────────


def test_endpoint_previous_runtime_batch_default_oss_floor(client, ent):
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec-batch?runtimes="
        + ",".join(runtimes)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert body["target"] is None
    assert all(row["row"] is None for row in body["runtimes"])


def test_endpoint_previous_runtime_batch_missing_csv(client):
    rv = client.get("/api/entitlement/previous-tier-runtime-spec-batch")
    assert rv.status_code == 400


def test_endpoint_previous_runtime_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    runtimes = _some_runtimes(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec-batch?runtimes="
        + ",".join(runtimes)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert body["runtimes"] == []
