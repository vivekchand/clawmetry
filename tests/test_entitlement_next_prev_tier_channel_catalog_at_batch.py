"""Tests for ``next_tier_channel_catalog_at_batch`` /
``previous_tier_channel_catalog_at_batch`` and the companion
``/api/entitlement/{next,previous}-tier-channel-catalog-at-batch`` endpoints.

Batch siblings of the source-anchored scalar
``{next,previous}_tier_channel_catalog_at`` (source-anchored channel-axis
catalog helpers). Where the scalar helpers answer "give me the full
channel matrix at the rung above / below THIS source", the batch
siblings return the same envelope for every entry in
:data:`_PURCHASABLE_TIERS` in one pass -- the catalog-shaped, channel-
axis member of the ``{next,previous}_tier_*_at_batch`` family alongside
the spec / diff / unlocks / locks / capacity siblings.

Every chat channel is FREE at every tier (the ``channels`` capacity axis
governs how many concurrent channels each plan admits, not which
adapters unlock), so every populated ``channels`` row is byte-identical
across every target rung: ``free=True`` / ``allowed=True`` /
``locked=False`` / ``entitled=True``. That parity IS the answer: a
pricing tooltip / upgrade panel can render "all N chat channels included
at every plan" off ONE batch call without hard-coding the posture
client-side. The invariant is pinned in the tests.

Pins covered here:

* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* every batch envelope byte-matches the scalar endpoint body for the
  same source -- the batch-vs-scalar parity that stops the batch
  what-if drifting from the scalar what-if
* per-envelope ``channels`` byte-equals the scalar helper for the same
  source: ``env["channels"] == next_tier_channel_catalog_at(env["tier"])``
* cross-batch parity with the spec / diff / unlocks / locks / capacity
  ``_at_batch`` siblings: the source axis (envelope ``tier`` /
  ``tier_label`` / ``tier_rank`` and ordering) byte-equals each sibling
  so a UI can fold all six batches into one matrix
* at the source-side ceiling (``enterprise`` for next) / floor (``oss``
  / ``cloud_free`` for previous) the envelope carries ``target=null``
  and ``channels=[]`` rather than being dropped
* trial is excluded from the source axis (mirrors the sibling batches)
* the always-free invariant reaches every row for every purchasable
  source (row-key set matches ``channel_catalog_at``; every row is
  ``free=True`` / ``allowed=True`` / ``locked=False`` /
  ``entitled=True``)
* per-envelope ``channels`` row count matches ``ALL_CHANNELS`` on every
  populated envelope
* per-envelope ``channels`` are sorted alphabetically (byte-identical
  to the sibling ``channel_catalog_at`` sort)
* grace vs enforce yields identical rows (the helpers walk the static
  catalogue, not the gated resolver)
* the helpers never raise: a per-source builder failure collapses to
  ``channels=[]`` on the populated envelope; a top-level failure
  short-circuits to ``[]``
* the API endpoints never 5xx: a resolver failure yields an empty
  ``tiers`` list and a grace-shape envelope
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "channels",
}

_ROW_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}

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
    Enforcement off by default (grace mode) -- the channel catalog
    ``_at_batch`` family is catalogue-derived and independent of the
    resolver, so the fixture only needs to keep the live resolver from
    surprising the test."""
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


# ── next_tier_channel_catalog_at_batch ───────────────────────────────────────


def test_next_catalog_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.next_tier_channel_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_catalog_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_catalog_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_channel_catalog_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_catalog_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_channel_catalog_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_catalog_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_channel_catalog_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_catalog_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_channel_catalog_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["channels"] == []


def test_next_catalog_batch_target_axis_is_next_purchasable(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        assert env["target"] == ent._next_purchasable_tier_after(env["tier"])


def test_next_catalog_batch_populated_channels_have_row_shape(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        if not env["channels"]:
            continue
        for row in env["channels"]:
            assert set(row.keys()) == _ROW_KEYS, row


def test_next_catalog_batch_populated_channels_len_matches_all_channels(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        if env["target"] is None:
            continue
        assert len(env["channels"]) == len(ent.ALL_CHANNELS), env["tier"]
        assert {row["id"] for row in env["channels"]} == set(ent.ALL_CHANNELS)


def test_next_catalog_batch_populated_channels_sorted_alphabetically(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        if not env["channels"]:
            continue
        assert [row["id"] for row in env["channels"]] == sorted(
            ent.ALL_CHANNELS
        )


def test_next_catalog_batch_always_free_invariant(ent):
    # Every chat channel is FREE at every tier -- pinned on every
    # populated envelope for every purchasable source.
    for env in ent.next_tier_channel_catalog_at_batch():
        for row in env["channels"]:
            assert row["free"] is True, (env["tier"], row)
            assert row["tier"] == "free", (env["tier"], row)
            assert row["allowed"] is True, (env["tier"], row)
            assert row["locked"] is False, (env["tier"], row)
            assert row["entitled"] is True, (env["tier"], row)


def test_next_catalog_batch_channels_byte_equal_scalar_helper(ent):
    for env in ent.next_tier_channel_catalog_at_batch():
        scalar = ent.next_tier_channel_catalog_at(env["tier"]) or []
        assert env["channels"] == scalar, env["tier"]


def test_next_catalog_batch_channels_byte_equal_channel_catalog_at_target(
    ent,
):
    for env in ent.next_tier_channel_catalog_at_batch():
        if env["target"] is None:
            assert env["channels"] == []
            continue
        assert env["channels"] == ent.channel_catalog_at(env["target"])


def test_next_catalog_batch_source_axis_matches_spec_batch(ent):
    # The six ``_at_batch`` siblings (spec / diff / unlocks / locks /
    # capacity / channel-catalog) MUST agree on the source axis --
    # envelope ``tier`` / ``tier_label`` / ``tier_rank`` and ordering
    # -- so a UI can fold the six responses into one matrix without
    # re-keying.
    catalog = ent.next_tier_channel_catalog_at_batch()
    spec = ent.next_tier_spec_at_batch()
    catalog_keys = [(env["tier_rank"], env["tier"]) for env in catalog]
    spec_keys = [(env["tier_rank"], env["tier"]) for env in spec]
    assert catalog_keys == spec_keys


def test_next_catalog_batch_target_axis_matches_spec_batch(ent):
    # The target a UI lands on at each rung MUST agree across the
    # ``_at_batch`` siblings -- otherwise catalog / spec would render
    # different upgrade rungs in the same matrix row.
    catalog = {
        env["tier"]: env for env in ent.next_tier_channel_catalog_at_batch()
    }
    spec = {env["tier"]: env for env in ent.next_tier_spec_at_batch()}
    assert set(catalog.keys()) == set(spec.keys())
    for tier in catalog:
        assert catalog[tier]["target"] == spec[tier]["target"], tier
        assert catalog[tier]["target_rank"] == spec[tier]["target_rank"], tier
        assert (
            catalog[tier]["target_label"] == spec[tier]["target_label"]
        ), tier


def test_next_catalog_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_channel_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_channel_catalog_at_batch()
    assert enforce == grace


def test_next_catalog_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    class Boom:
        def __iter__(self):
            raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", Boom())
    assert ent.next_tier_channel_catalog_at_batch() == []


def test_next_catalog_batch_per_row_failure_collapses_to_channels_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "channel_catalog_at", boom)
    rows = ent.next_tier_channel_catalog_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["channels"] == []


def test_next_catalog_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_channel_catalog_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── previous_tier_channel_catalog_at_batch ───────────────────────────────────


def test_prev_catalog_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_channel_catalog_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_catalog_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_catalog_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_channel_catalog_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_catalog_batch_excludes_trial_from_sources(ent):
    sources = {
        env["tier"] for env in ent.previous_tier_channel_catalog_at_batch()
    }
    assert ent.TIER_TRIAL not in sources


def test_prev_catalog_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_channel_catalog_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_catalog_batch_floor_sources_collapse(ent):
    rows = {env["tier"]: env for env in ent.previous_tier_channel_catalog_at_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["channels"] == []


def test_prev_catalog_batch_target_axis_is_previous_purchasable(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        assert env["target"] == ent._previous_purchasable_tier_before(
            env["tier"]
        )


def test_prev_catalog_batch_populated_channels_have_row_shape(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        if not env["channels"]:
            continue
        for row in env["channels"]:
            assert set(row.keys()) == _ROW_KEYS, row


def test_prev_catalog_batch_populated_channels_len_matches_all_channels(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        if env["target"] is None:
            continue
        assert len(env["channels"]) == len(ent.ALL_CHANNELS), env["tier"]
        assert {row["id"] for row in env["channels"]} == set(ent.ALL_CHANNELS)


def test_prev_catalog_batch_populated_channels_sorted_alphabetically(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        if not env["channels"]:
            continue
        assert [row["id"] for row in env["channels"]] == sorted(
            ent.ALL_CHANNELS
        )


def test_prev_catalog_batch_always_free_invariant(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        for row in env["channels"]:
            assert row["free"] is True, (env["tier"], row)
            assert row["tier"] == "free", (env["tier"], row)
            assert row["allowed"] is True, (env["tier"], row)
            assert row["locked"] is False, (env["tier"], row)
            assert row["entitled"] is True, (env["tier"], row)


def test_prev_catalog_batch_channels_byte_equal_scalar_helper(ent):
    for env in ent.previous_tier_channel_catalog_at_batch():
        scalar = ent.previous_tier_channel_catalog_at(env["tier"]) or []
        assert env["channels"] == scalar, env["tier"]


def test_prev_catalog_batch_channels_byte_equal_channel_catalog_at_target(
    ent,
):
    for env in ent.previous_tier_channel_catalog_at_batch():
        if env["target"] is None:
            assert env["channels"] == []
            continue
        assert env["channels"] == ent.channel_catalog_at(env["target"])


def test_prev_catalog_batch_source_axis_matches_spec_batch(ent):
    catalog = ent.previous_tier_channel_catalog_at_batch()
    spec = ent.previous_tier_spec_at_batch()
    catalog_keys = [(env["tier_rank"], env["tier"]) for env in catalog]
    spec_keys = [(env["tier_rank"], env["tier"]) for env in spec]
    assert catalog_keys == spec_keys


def test_prev_catalog_batch_target_axis_matches_spec_batch(ent):
    catalog = {
        env["tier"]: env
        for env in ent.previous_tier_channel_catalog_at_batch()
    }
    spec = {env["tier"]: env for env in ent.previous_tier_spec_at_batch()}
    assert set(catalog.keys()) == set(spec.keys())
    for tier in catalog:
        assert catalog[tier]["target"] == spec[tier]["target"], tier
        assert catalog[tier]["target_rank"] == spec[tier]["target_rank"], tier
        assert (
            catalog[tier]["target_label"] == spec[tier]["target_label"]
        ), tier


def test_prev_catalog_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_channel_catalog_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_channel_catalog_at_batch()
    assert enforce == grace


def test_prev_catalog_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    class Boom:
        def __iter__(self):
            raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", Boom())
    assert ent.previous_tier_channel_catalog_at_batch() == []


def test_prev_catalog_batch_per_row_failure_collapses_to_channels_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "channel_catalog_at", boom)
    rows = ent.previous_tier_channel_catalog_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["channels"] == []


def test_prev_catalog_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_channel_catalog_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── API: /api/entitlement/next-tier-channel-catalog-at-batch ─────────────────


def test_next_catalog_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-channel-catalog-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_catalog_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-channel-catalog-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_catalog_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-channel-catalog-at-batch")
    assert rv.get_json()["tiers"] == ent.next_tier_channel_catalog_at_batch()


def test_next_catalog_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/next-tier-channel-catalog-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/next-tier-channel-catalog-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_next_catalog_batch_endpoint_always_free_invariant(client, ent):
    body = client.get(
        "/api/entitlement/next-tier-channel-catalog-at-batch"
    ).get_json()
    for env in body["tiers"]:
        for row in env["channels"]:
            assert row["free"] is True, (env["tier"], row)
            assert row["locked"] is False, (env["tier"], row)
            assert row["entitled"] is True, (env["tier"], row)


def test_next_catalog_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_channel_catalog_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-channel-catalog-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-channel-catalog-at-batch ─────────────


def test_prev_catalog_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_prev_catalog_batch_endpoint_resolver_context(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    )
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_catalog_batch_endpoint_matches_helper(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    )
    assert (
        rv.get_json()["tiers"] == ent.previous_tier_channel_catalog_at_batch()
    )


def test_prev_catalog_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_prev_catalog_batch_endpoint_always_free_invariant(client, ent):
    body = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    ).get_json()
    for env in body["tiers"]:
        for row in env["channels"]:
            assert row["free"] is True, (env["tier"], row)
            assert row["locked"] is False, (env["tier"], row)
            assert row["entitled"] is True, (env["tier"], row)


def test_prev_catalog_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_channel_catalog_at_batch", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at-batch"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
