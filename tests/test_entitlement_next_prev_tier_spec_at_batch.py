"""Tests for ``next_tier_spec_at_batch`` /
``previous_tier_spec_at_batch`` and the companion
``/api/entitlement/{next,previous}-tier-spec-at-batch`` endpoints,
plus the private :func:`_spec_at_envelope` builder the batches share.

Batch siblings of the scalar
``{next,previous}_tier_spec_at`` what-ifs that landed alongside the
live ``next_tier_spec`` / ``previous_tier_spec`` accessors. Where the
scalar what-ifs answer "what does the rung above / below ``tier``
look like" one source at a time, the batch siblings return the same
envelope for every entry in :data:`_PURCHASABLE_TIERS` in one pass --
the spec-shaped member of the ``{next,previous}_tier_*_at_batch``
family alongside the diff / unlocks / locks / capacity siblings.

Pins covered here:

* :func:`_spec_at_envelope` composes source / target metadata with
  the per-pair :func:`tier_spec_at` row in the same envelope shape
  :func:`_diff_at_envelope` / :func:`_capacity_diff_at_envelope`
  publish -- ``tier``, ``tier_label``, ``tier_rank``, ``target``,
  ``target_label``, ``target_rank``, ``row``
* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* every batch envelope byte-equals the scalar endpoint body for the
  same source -- the batch-vs-scalar parity that stops the batch
  what-if drifting from the scalar what-if
* cross-batch parity with the diff / unlocks / locks / capacity
  ``_at_batch`` siblings: the source axis (envelope ``tier`` /
  ``tier_label`` / ``tier_rank`` and ordering) byte-equals each
  sibling so a UI can fold all five batches into one matrix
* at the source-side ceiling (``enterprise`` for next) / floor
  (``oss`` / ``cloud_free`` for previous) the envelope carries
  ``target=null`` and ``row=null`` rather than being dropped
* trial is excluded from the source axis (mirrors the sibling
  batches)
* on populated rows the inner ``row.is_current`` is always ``False``
  (target is strictly above / below source by construction)
* the helpers never raise: a per-source builder failure collapses
  to ``row=null`` on the populated envelope; a top-level failure
  short-circuits to ``[]``
* grace vs enforce yields identical rows (the helpers walk the
  static catalogue, not the gated resolver)
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
    "row",
}

_SPEC_ROW_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
    "features",
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
    Enforcement off by default (grace mode) -- the spec ``_at`` family
    is catalogue-derived and independent of the resolver, so the
    fixture only needs to keep the live resolver from surprising the
    test."""
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


# ── _spec_at_envelope ────────────────────────────────────────────────────────


def test_spec_envelope_shape_for_known_pair(ent):
    env = ent._spec_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert env["row"] == ent.tier_spec_at(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER
    )


def test_spec_envelope_none_target_collapses_row(ent):
    env = ent._spec_at_envelope(ent.TIER_ENTERPRISE, None)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["row"] is None


def test_spec_envelope_unknown_source_keeps_envelope_populated(ent):
    env = ent._spec_at_envelope("bogus", ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    # tier_spec_at returns None on unknown source -- the envelope
    # surfaces row=None but keeps target metadata so the batch row
    # stays visible.
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


def test_spec_envelope_trims_and_lowercases(ent):
    env = ent._spec_at_envelope("  OSS  ", ent.TIER_CLOUD_STARTER)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] == ent.tier_spec_at(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER
    )


def test_spec_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_spec_at", boom)
    env = ent._spec_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


# ── next_tier_spec_at_batch ──────────────────────────────────────────────────


def test_next_spec_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.next_tier_spec_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_spec_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_spec_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_spec_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_spec_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_spec_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_spec_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_spec_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_spec_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_spec_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_spec_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["row"] is None


def test_next_spec_batch_populated_rows_have_spec_row_shape(ent):
    for env in ent.next_tier_spec_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _SPEC_ROW_KEYS
        # row.id is byte-equal to envelope.target on every populated
        # row -- the spec descriptor identifies the target tier so the
        # envelope's two slots must agree.
        assert env["row"]["id"] == env["target"]


def test_next_spec_batch_populated_rows_have_is_current_false(ent):
    # Target is strictly above source by construction, so it can never
    # equal it -- ``is_current`` is therefore always False on populated
    # rows. Mirrors :func:`next_tier_spec_at`.
    for env in ent.next_tier_spec_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["is_current"] is False


def test_next_spec_batch_matches_scalar_helper_per_source(ent):
    for env in ent.next_tier_spec_at_batch():
        assert env["row"] == ent.next_tier_spec_at(env["tier"])


def test_next_spec_batch_source_axis_matches_diff_batch(ent):
    # The five ``_at_batch`` siblings (diff / unlocks / locks /
    # capacity / spec) MUST agree on the source axis -- envelope
    # ``tier``, ``tier_label``, ``tier_rank`` and ordering -- so a UI
    # can fold the five responses into one matrix without re-keying.
    spec = ent.next_tier_spec_at_batch()
    diff = ent.next_tier_diff_at_batch()
    cap = ent.next_tier_capacity_diff_at_batch()
    unl = ent.next_tier_unlocks_at_batch()
    lck = ent.next_tier_locks_at_batch()
    spec_keys = [(env["tier_rank"], env["tier"]) for env in spec]
    for sibling in (diff, cap, unl, lck):
        sibling_keys = [(env["tier_rank"], env["tier"]) for env in sibling]
        assert sibling_keys == spec_keys


def test_next_spec_batch_target_axis_matches_diff_batch(ent):
    # The target a UI lands on at each rung MUST agree across the
    # ``_at_batch`` siblings -- otherwise spec / diff would render
    # different upgrade rungs in the same matrix row.
    spec = {env["tier"]: env for env in ent.next_tier_spec_at_batch()}
    diff = {env["tier"]: env for env in ent.next_tier_diff_at_batch()}
    assert set(spec.keys()) == set(diff.keys())
    for tier in spec:
        assert spec[tier]["target"] == diff[tier]["target"], tier
        assert spec[tier]["target_rank"] == diff[tier]["target_rank"], tier
        assert spec[tier]["target_label"] == diff[tier]["target_label"], tier


def test_next_spec_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_spec_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_spec_at_batch()
    assert enforce == grace


def test_next_spec_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.next_tier_spec_at_batch() == []


def test_next_spec_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_spec_at", boom)
    rows = ent.next_tier_spec_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_next_spec_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_spec_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── previous_tier_spec_at_batch ──────────────────────────────────────────────


def test_prev_spec_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_spec_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_spec_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_spec_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_spec_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_spec_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_spec_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.previous_tier_spec_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_prev_spec_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_spec_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_spec_batch_floor_sources_collapse(ent):
    rows = {env["tier"]: env for env in ent.previous_tier_spec_at_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["row"] is None


def test_prev_spec_batch_populated_rows_have_spec_row_shape(ent):
    for env in ent.previous_tier_spec_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _SPEC_ROW_KEYS
        assert env["row"]["id"] == env["target"]


def test_prev_spec_batch_populated_rows_have_is_current_false(ent):
    for env in ent.previous_tier_spec_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["is_current"] is False


def test_prev_spec_batch_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_spec_at_batch():
        assert env["row"] == ent.previous_tier_spec_at(env["tier"])


def test_prev_spec_batch_source_axis_matches_diff_batch(ent):
    spec = ent.previous_tier_spec_at_batch()
    diff = ent.previous_tier_diff_at_batch()
    cap = ent.previous_tier_capacity_diff_at_batch()
    unl = ent.previous_tier_unlocks_at_batch()
    lck = ent.previous_tier_locks_at_batch()
    spec_keys = [(env["tier_rank"], env["tier"]) for env in spec]
    for sibling in (diff, cap, unl, lck):
        sibling_keys = [(env["tier_rank"], env["tier"]) for env in sibling]
        assert sibling_keys == spec_keys


def test_prev_spec_batch_target_axis_matches_diff_batch(ent):
    spec = {env["tier"]: env for env in ent.previous_tier_spec_at_batch()}
    diff = {env["tier"]: env for env in ent.previous_tier_diff_at_batch()}
    assert set(spec.keys()) == set(diff.keys())
    for tier in spec:
        assert spec[tier]["target"] == diff[tier]["target"], tier
        assert spec[tier]["target_rank"] == diff[tier]["target_rank"], tier
        assert spec[tier]["target_label"] == diff[tier]["target_label"], tier


def test_prev_spec_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_spec_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_spec_at_batch()
    assert enforce == grace


def test_prev_spec_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.previous_tier_spec_at_batch() == []


def test_prev_spec_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_spec_at", boom)
    rows = ent.previous_tier_spec_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_prev_spec_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_spec_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── API: /api/entitlement/next-tier-spec-at-batch ────────────────────────────


def test_next_spec_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-spec-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_spec_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-spec-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_spec_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-spec-at-batch")
    assert rv.get_json()["tiers"] == ent.next_tier_spec_at_batch()


def test_next_spec_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/next-tier-spec-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/next-tier-spec-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_next_spec_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_spec_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-spec-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-spec-at-batch ────────────────────────


def test_prev_spec_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/previous-tier-spec-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_prev_spec_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/previous-tier-spec-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_spec_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/previous-tier-spec-at-batch")
    assert rv.get_json()["tiers"] == ent.previous_tier_spec_at_batch()


def test_prev_spec_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/previous-tier-spec-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/previous-tier-spec-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_prev_spec_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_spec_at_batch", boom)
    rv = client.get("/api/entitlement/previous-tier-spec-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
