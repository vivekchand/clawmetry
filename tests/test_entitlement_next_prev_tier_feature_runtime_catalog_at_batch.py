"""Tests for the four batch siblings of
:func:`clawmetry.entitlements.next_tier_feature_catalog_at` /
:func:`previous_tier_feature_catalog_at` /
:func:`next_tier_runtime_catalog_at` /
:func:`previous_tier_runtime_catalog_at`, and the four companion
``/api/entitlement/{next,previous}-tier-{feature,runtime}-catalog-at-batch``
endpoints (plus the private :func:`_feature_catalog_at_envelope` /
:func:`_runtime_catalog_at_envelope` builders they share).

Feature- and runtime-axis catalog analogues of
:func:`next_tier_capacity_diff_at_batch` /
:func:`previous_tier_capacity_diff_at_batch` and
:func:`next_tier_diff_at_batch` / :func:`previous_tier_diff_at_batch`:
the source axis walks :data:`_PURCHASABLE_TIERS` (trial excluded) in
one pass, and each envelope carries the full
:func:`feature_catalog_at` / :func:`runtime_catalog_at` catalogue for
the rung above / below that source.

Pins covered here:

* the two private envelope builders compose source/target metadata
  with the per-pair catalog list in the same envelope shape the scalar
  catalog endpoints surface (``tier``, ``tier_label``, ``tier_rank``,
  ``target``, ``target_label``, ``target_rank``, ``features`` /
  ``runtimes``)
* all four batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``, with
  trial excluded from the source axis
* every envelope byte-equals the scalar
  :func:`next_tier_feature_catalog_at` /
  :func:`next_tier_runtime_catalog_at` (etc.) helper for the same
  source -- the batch-vs-scalar parity that stops the batch what-if
  drifting from the scalar what-if
* per-envelope inner ``features`` / ``runtimes`` byte-equals
  :func:`feature_catalog_at(target)` / :func:`runtime_catalog_at(target)`
  for the resolved target -- pins the catalog projection to its
  sibling
* source-axis and envelope keys are byte-stable against the sibling
  ``next_*_at_batch`` / ``previous_*_at_batch`` families (diff,
  capacity, unlocks, locks) so a UI can fold responses into one
  matrix without re-sorting
* at the source-side ceiling (``enterprise`` as source for the next
  batch) and floor (``oss`` / ``cloud_free`` as source for the
  previous batch) the envelope carries ``target=null`` and
  ``features=[]`` / ``runtimes=[]`` rather than being dropped
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* the helpers never raise: a per-source builder failure collapses to
  ``features=[]`` / ``runtimes=[]`` on the populated envelope; a
  top-level failure short-circuits to ``[]``
* the four API endpoints never 5xx: on the happy path the batch body
  matches the helper output; a resolver failure yields an empty
  ``tiers`` list plus the grace-shape envelope
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_FEATURE_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
}

_RUNTIME_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
}

_BATCH_RESPONSE_KEYS = {
    "tiers",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- the batch helpers are
    catalogue-derived and independent of the resolver, so the fixture
    only needs to keep the live resolver from surprising the test."""
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


# ── _feature_catalog_at_envelope ────────────────────────────────────────────


def test_feature_envelope_shape_for_known_pair(ent):
    env = ent._feature_catalog_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _FEATURE_ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert env["features"] == ent.feature_catalog_at(ent.TIER_CLOUD_STARTER)


def test_feature_envelope_none_target_collapses_features(ent):
    env = ent._feature_catalog_at_envelope(ent.TIER_ENTERPRISE, None)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["features"] == []


def test_feature_envelope_unknown_source_keeps_target_populated(ent):
    env = ent._feature_catalog_at_envelope("bogus", ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _FEATURE_ENVELOPE_KEYS
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] == ent.TIER_CLOUD_STARTER
    # feature_catalog_at is target-driven -- unknown source doesn't
    # affect the projection, just leaves the source metadata unresolved.
    assert env["features"] == ent.feature_catalog_at(ent.TIER_CLOUD_STARTER)


def test_feature_envelope_trims_and_lowercases_source(ent):
    env = ent._feature_catalog_at_envelope("  OSS  ", ent.TIER_CLOUD_STARTER)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER


def test_feature_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "feature_catalog_at", boom)
    env = ent._feature_catalog_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["features"] == []


# ── _runtime_catalog_at_envelope ────────────────────────────────────────────


def test_runtime_envelope_shape_for_known_pair(ent):
    env = ent._runtime_catalog_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["runtimes"] == ent.runtime_catalog_at(ent.TIER_CLOUD_STARTER)


def test_runtime_envelope_none_target_collapses_runtimes(ent):
    env = ent._runtime_catalog_at_envelope(ent.TIER_ENTERPRISE, None)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["runtimes"] == []


def test_runtime_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "runtime_catalog_at", boom)
    env = ent._runtime_catalog_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["runtimes"] == []


# ── next_tier_feature_catalog_at_batch (helper) ─────────────────────────────


def test_next_feature_batch_returns_one_envelope_per_purchasable(ent):
    rows = ent.next_tier_feature_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_feature_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_feature_catalog_at_batch():
        assert set(env.keys()) == _FEATURE_ENVELOPE_KEYS


def test_next_feature_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_feature_catalog_at_batch()
    assert {env["tier"] for env in rows} == set(ent._PURCHASABLE_TIERS)


def test_next_feature_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_feature_catalog_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_feature_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_feature_catalog_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_feature_batch_ceiling_collapses_to_empty(ent):
    rows = ent.next_tier_feature_catalog_at_batch()
    top = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert top["target"] is None
    assert top["target_label"] is None
    assert top["target_rank"] is None
    assert top["features"] == []


def test_next_feature_batch_features_matches_scalar_helper_per_source(ent):
    # Batch-vs-scalar parity: every envelope's features byte-equals the
    # scalar :func:`next_tier_feature_catalog_at` for the same source.
    for env in ent.next_tier_feature_catalog_at_batch():
        scalar = ent.next_tier_feature_catalog_at(env["tier"]) or []
        assert env["features"] == scalar


def test_next_feature_batch_features_matches_feature_catalog_at_target(ent):
    # Inner catalog parity: per-envelope features byte-equals
    # :func:`feature_catalog_at(target)` for the resolved target.
    for env in ent.next_tier_feature_catalog_at_batch():
        if env["target"] is None:
            assert env["features"] == []
        else:
            assert env["features"] == ent.feature_catalog_at(env["target"])


def test_next_feature_batch_sort_matches_capacity_batch(ent):
    # Byte-stable against the sibling capacity batch so a UI can fold
    # both responses into one matrix without re-sorting client-side.
    feat_sources = [
        env["tier"] for env in ent.next_tier_feature_catalog_at_batch()
    ]
    cap_sources = [
        env["tier"] for env in ent.next_tier_capacity_diff_at_batch()
    ]
    assert feat_sources == cap_sources


def test_next_feature_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_feature_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_feature_catalog_at_batch()
    assert enforce == grace


def test_next_feature_batch_per_source_builder_failure_keeps_envelope(
    ent, monkeypatch
):
    real = ent.feature_catalog_at
    boom_target = ent._next_purchasable_tier_after(ent.TIER_OSS)

    def maybe_boom(tier):
        if tier == boom_target:
            raise RuntimeError("synthetic")
        return real(tier)

    monkeypatch.setattr(ent, "feature_catalog_at", maybe_boom)
    rows = ent.next_tier_feature_catalog_at_batch()
    oss_env = next(env for env in rows if env["tier"] == ent.TIER_OSS)
    assert oss_env["target"] == boom_target
    assert oss_env["features"] == []
    # A different source with a different target still hydrates fully.
    other_env = next(
        env
        for env in rows
        if env["target"] not in (None, boom_target)
    )
    assert other_env["features"] != []


def test_next_feature_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("top-level")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    assert ent.next_tier_feature_catalog_at_batch() == []


# ── previous_tier_feature_catalog_at_batch (helper) ─────────────────────────


def test_previous_feature_batch_returns_one_envelope_per_purchasable(ent):
    rows = ent.previous_tier_feature_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_previous_feature_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_feature_catalog_at_batch():
        assert set(env.keys()) == _FEATURE_ENVELOPE_KEYS


def test_previous_feature_batch_source_axis_matches_purchasable(ent):
    sources = {
        env["tier"] for env in ent.previous_tier_feature_catalog_at_batch()
    }
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_previous_feature_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_feature_catalog_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_previous_feature_batch_floor_collapses_to_empty(ent):
    rows = ent.previous_tier_feature_catalog_at_batch()
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        floor_env = next(env for env in rows if env["tier"] == src)
        assert floor_env["target"] is None
        assert floor_env["target_label"] is None
        assert floor_env["target_rank"] is None
        assert floor_env["features"] == []


def test_previous_feature_batch_features_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_feature_catalog_at_batch():
        scalar = ent.previous_tier_feature_catalog_at(env["tier"]) or []
        assert env["features"] == scalar


def test_previous_feature_batch_features_matches_feature_catalog_at_target(ent):
    for env in ent.previous_tier_feature_catalog_at_batch():
        if env["target"] is None:
            assert env["features"] == []
        else:
            assert env["features"] == ent.feature_catalog_at(env["target"])


def test_previous_feature_batch_sort_matches_capacity_batch(ent):
    feat_sources = [
        env["tier"] for env in ent.previous_tier_feature_catalog_at_batch()
    ]
    cap_sources = [
        env["tier"] for env in ent.previous_tier_capacity_diff_at_batch()
    ]
    assert feat_sources == cap_sources


def test_previous_feature_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_feature_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_feature_catalog_at_batch()
    assert enforce == grace


def test_previous_feature_batch_top_level_failure_short_circuits(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("top-level")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    assert ent.previous_tier_feature_catalog_at_batch() == []


# ── next_tier_runtime_catalog_at_batch (helper) ─────────────────────────────


def test_next_runtime_batch_returns_one_envelope_per_purchasable(ent):
    rows = ent.next_tier_runtime_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_runtime_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_runtime_catalog_at_batch():
        assert set(env.keys()) == _RUNTIME_ENVELOPE_KEYS


def test_next_runtime_batch_source_axis_matches_purchasable(ent):
    sources = {env["tier"] for env in ent.next_tier_runtime_catalog_at_batch()}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_runtime_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_runtime_catalog_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_runtime_batch_ceiling_collapses_to_empty(ent):
    rows = ent.next_tier_runtime_catalog_at_batch()
    top = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert top["target"] is None
    assert top["target_label"] is None
    assert top["target_rank"] is None
    assert top["runtimes"] == []


def test_next_runtime_batch_runtimes_matches_scalar_helper_per_source(ent):
    for env in ent.next_tier_runtime_catalog_at_batch():
        scalar = ent.next_tier_runtime_catalog_at(env["tier"]) or []
        assert env["runtimes"] == scalar


def test_next_runtime_batch_runtimes_matches_runtime_catalog_at_target(ent):
    for env in ent.next_tier_runtime_catalog_at_batch():
        if env["target"] is None:
            assert env["runtimes"] == []
        else:
            assert env["runtimes"] == ent.runtime_catalog_at(env["target"])


def test_next_runtime_batch_sort_matches_feature_batch(ent):
    # Byte-stable against the sibling feature batch so a UI can fold
    # both responses into one matrix without re-sorting client-side.
    rt_sources = [
        env["tier"] for env in ent.next_tier_runtime_catalog_at_batch()
    ]
    feat_sources = [
        env["tier"] for env in ent.next_tier_feature_catalog_at_batch()
    ]
    assert rt_sources == feat_sources


def test_next_runtime_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_runtime_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_runtime_catalog_at_batch()
    assert enforce == grace


def test_next_runtime_batch_top_level_failure_short_circuits(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("top-level")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    assert ent.next_tier_runtime_catalog_at_batch() == []


# ── previous_tier_runtime_catalog_at_batch (helper) ─────────────────────────


def test_previous_runtime_batch_returns_one_envelope_per_purchasable(ent):
    rows = ent.previous_tier_runtime_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_previous_runtime_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_runtime_catalog_at_batch():
        assert set(env.keys()) == _RUNTIME_ENVELOPE_KEYS


def test_previous_runtime_batch_floor_collapses_to_empty(ent):
    rows = ent.previous_tier_runtime_catalog_at_batch()
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        floor_env = next(env for env in rows if env["tier"] == src)
        assert floor_env["target"] is None
        assert floor_env["runtimes"] == []


def test_previous_runtime_batch_runtimes_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_runtime_catalog_at_batch():
        scalar = ent.previous_tier_runtime_catalog_at(env["tier"]) or []
        assert env["runtimes"] == scalar


def test_previous_runtime_batch_runtimes_matches_runtime_catalog_at_target(ent):
    for env in ent.previous_tier_runtime_catalog_at_batch():
        if env["target"] is None:
            assert env["runtimes"] == []
        else:
            assert env["runtimes"] == ent.runtime_catalog_at(env["target"])


def test_previous_runtime_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_runtime_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_runtime_catalog_at_batch()
    assert enforce == grace


# ── /api/entitlement/next-tier-feature-catalog-at-batch ─────────────────────


def test_api_next_feature_batch_happy_path(client, ent):
    resp = client.get("/api/entitlement/next-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _FEATURE_ENVELOPE_KEYS


def test_api_next_feature_batch_matches_helper_body(client, ent):
    resp = client.get("/api/entitlement/next-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == ent.next_tier_feature_catalog_at_batch()


def test_api_next_feature_batch_never_5xxs_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom():
        raise RuntimeError("resolver dead")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/next-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


# ── /api/entitlement/previous-tier-feature-catalog-at-batch ─────────────────


def test_api_previous_feature_batch_happy_path(client, ent):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_api_previous_feature_batch_matches_helper_body(client, ent):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == ent.previous_tier_feature_catalog_at_batch()


def test_api_previous_feature_batch_never_5xxs_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom():
        raise RuntimeError("resolver dead")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/previous-tier-feature-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


# ── /api/entitlement/next-tier-runtime-catalog-at-batch ─────────────────────


def test_api_next_runtime_batch_happy_path(client, ent):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _RUNTIME_ENVELOPE_KEYS


def test_api_next_runtime_batch_matches_helper_body(client, ent):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == ent.next_tier_runtime_catalog_at_batch()


def test_api_next_runtime_batch_never_5xxs_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom():
        raise RuntimeError("resolver dead")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/next-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


# ── /api/entitlement/previous-tier-runtime-catalog-at-batch ─────────────────


def test_api_previous_runtime_batch_happy_path(client, ent):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_api_previous_runtime_batch_matches_helper_body(client, ent):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == ent.previous_tier_runtime_catalog_at_batch()


def test_api_previous_runtime_batch_never_5xxs_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom():
        raise RuntimeError("resolver dead")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog-at-batch")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


# ── Cross-endpoint axis parity ──────────────────────────────────────────────


def test_all_four_endpoints_share_source_axis_order(client, ent):
    # A UI can fold all four responses into one matrix without
    # re-sorting: the source axis (envelope.tier order) is identical
    # across all four endpoints and equal to the shipped
    # /next-tier-capacity-diff-at-batch axis.
    urls = [
        "/api/entitlement/next-tier-feature-catalog-at-batch",
        "/api/entitlement/previous-tier-feature-catalog-at-batch",
        "/api/entitlement/next-tier-runtime-catalog-at-batch",
        "/api/entitlement/previous-tier-runtime-catalog-at-batch",
        "/api/entitlement/next-tier-capacity-diff-at-batch",
    ]
    axes = []
    for url in urls:
        body = client.get(url).get_json()
        axes.append([env["tier"] for env in body["tiers"]])
    for axis in axes[1:]:
        assert axis == axes[0]
