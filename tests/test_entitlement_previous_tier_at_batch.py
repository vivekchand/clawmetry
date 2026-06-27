"""Tests for ``previous_tier_unlocks_at_batch`` /
``previous_tier_locks_at_batch`` -- batch siblings of the scalar
:func:`previous_tier_unlocks_at` / :func:`previous_tier_locks_at`
what-ifs, plus the companion
``/api/entitlement/previous-tier-{unlocks,locks}-at-batch`` endpoints
and the private :func:`_previous_at_envelope` builder they share.

Downgrade-side mirror of the next-tier batch siblings: where the
next-tier ``_at_batch`` family answers "what would the rung above each
rung first unlock / first lose", this family answers "what would the
rung below each rung still grant / first lose at that rung". Together
they cover both directions of the per-source pricing-comparison matrix
in two round-trips per direction.

Pins covered here:

* helper :func:`_previous_at_envelope` composes the source/target
  metadata with the per-target row in the same envelope shape the
  scalar endpoints surface -- ``tier``, ``tier_label``, ``tier_rank``,
  ``target``, ``target_label``, ``target_rank``, ``row``
* ``previous_tier_unlocks_at_batch()`` returns one envelope per entry
  in :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* same shape / ordering for ``previous_tier_locks_at_batch``
* every envelope byte-equals the body that the scalar
  ``/api/entitlement/previous-tier-{unlocks,locks}-at?tier=<src>``
  endpoint returns for the same source -- the batch-vs-scalar parity
  that stops the batch what-if drifting from the scalar what-if
* at the source-side floor (``oss`` / ``cloud_free`` as source) the
  envelope carries ``target=null`` and ``row=null`` rather than being
  dropped
* at a source rung whose next-below IS the ladder floor
  (``cloud_starter`` -> ``oss``) the locks row carries populated
  ``lost_features`` / ``lost_runtimes`` lists -- :func:`tier_locks`
  shape against the floor's next-above rung -- NOT ``null`` on the
  envelope
* trial is excluded from the source axis (mirrors
  :func:`tier_unlocks_batch`)
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* the helpers never raise: builder failure on a single source
  collapses to ``row=null`` on the populated envelope; a top-level
  failure short-circuits to ``[]``
* the API endpoints never 5xx: a resolver failure yields an empty
  ``tiers`` list and a grace-shape envelope
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_UNLOCKS_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "previous_tier",
    "previous_tier_label",
    "previous_tier_rank",
    "features",
    "runtimes",
}

_LOCKS_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "next_tier",
    "next_tier_label",
    "next_tier_rank",
    "lost_features",
    "lost_runtimes",
}

_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "row",
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
    Enforcement off by default (grace mode) -- both batch helpers are
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


# -- _previous_at_envelope ---------------------------------------------------


def test_envelope_builder_shape_for_known_source(ent):
    env = ent._previous_at_envelope(ent.TIER_CLOUD_STARTER, ent.tier_unlocks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_CLOUD_STARTER
    assert env["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    target = ent._previous_purchasable_tier_before(ent.TIER_CLOUD_STARTER)
    assert env["target"] == target
    assert env["target_label"] == ent.tier_label(target)
    assert env["target_rank"] == ent.tier_rank(target)
    assert env["row"] == ent.tier_unlocks(target)


def test_envelope_builder_locks_branch(ent):
    env = ent._previous_at_envelope(ent.TIER_CLOUD_PRO, ent.tier_locks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    target = ent._previous_purchasable_tier_before(ent.TIER_CLOUD_PRO)
    assert env["target"] == target
    assert env["row"] == ent.tier_locks(target)


def test_envelope_builder_floor_collapses_target_and_row(ent):
    env = ent._previous_at_envelope(ent.TIER_OSS, ent.tier_unlocks)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["row"] is None


def test_envelope_builder_cloud_free_floor_also_collapses(ent):
    env = ent._previous_at_envelope(ent.TIER_CLOUD_FREE, ent.tier_locks)
    assert env["tier"] == ent.TIER_CLOUD_FREE
    assert env["target"] is None
    assert env["row"] is None


def test_envelope_builder_unknown_source_keeps_envelope_populated(ent):
    env = ent._previous_at_envelope("bogus", ent.tier_unlocks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["target"] is None
    assert env["row"] is None


def test_envelope_builder_trims_and_lowercases(ent):
    env = ent._previous_at_envelope("  CLOUD_STARTER  ", ent.tier_unlocks)
    assert env["tier"] == ent.TIER_CLOUD_STARTER
    assert env["target"] == ent._previous_purchasable_tier_before(
        ent.TIER_CLOUD_STARTER
    )


def test_envelope_builder_swallows_builder_exception(ent):
    def boom(_target):
        raise RuntimeError("synthetic")

    env = ent._previous_at_envelope(ent.TIER_CLOUD_STARTER, boom)
    assert env["target"] == ent._previous_purchasable_tier_before(
        ent.TIER_CLOUD_STARTER
    )
    assert env["row"] is None


# -- previous_tier_unlocks_at_batch ------------------------------------------


def test_unlocks_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_unlocks_batch_each_envelope_has_envelope_shape(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_unlocks_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_unlocks_batch_excludes_trial_from_sources(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    assert ent.TIER_TRIAL not in {env["tier"] for env in rows}


def test_unlocks_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_unlocks_batch_ordering_matches_tier_unlocks_batch(ent):
    """The source axis is byte-stable against
    :func:`tier_unlocks_batch`'s ordering so the two responses fold
    into the same pricing-page table without re-sorting client-side."""
    at_rows = ent.previous_tier_unlocks_at_batch()
    live_rows = ent.tier_unlocks_batch()
    assert [r["tier"] for r in at_rows] == [r["tier"] for r in live_rows]


def test_unlocks_batch_ordering_matches_locks_batch(ent):
    """The two ``previous-*-at_batch`` siblings emit the source axis in
    the same order so the unlocks/locks columns line up row-for-row."""
    unlocks = ent.previous_tier_unlocks_at_batch()
    locks = ent.previous_tier_locks_at_batch()
    assert [r["tier"] for r in unlocks] == [r["tier"] for r in locks]


def test_unlocks_batch_each_envelope_byte_equals_scalar_helper(ent):
    """Every envelope byte-equals the body the scalar
    :func:`previous_tier_unlocks_at` helper produces for the same
    source -- the parity that stops the batch what-if drifting from the
    scalar what-if."""
    rows = ent.previous_tier_unlocks_at_batch()
    for env in rows:
        scalar_row = ent.previous_tier_unlocks_at(env["tier"])
        assert env["row"] == scalar_row, env["tier"]


def test_unlocks_batch_target_resolves_via_previous_purchasable_before(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    for env in rows:
        assert env["target"] == ent._previous_purchasable_tier_before(env["tier"])


def test_unlocks_batch_target_metadata_consistent(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    for env in rows:
        if env["target"] is None:
            assert env["target_label"] is None
            assert env["target_rank"] is None
        else:
            assert env["target_label"] == ent.tier_label(env["target"])
            assert env["target_rank"] == ent.tier_rank(env["target"])


def test_unlocks_batch_oss_source_collapses_to_null(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    oss = next(env for env in rows if env["tier"] == ent.TIER_OSS)
    assert oss["target"] is None
    assert oss["target_label"] is None
    assert oss["target_rank"] is None
    assert oss["row"] is None


def test_unlocks_batch_cloud_free_source_collapses_to_null(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    cf = next(env for env in rows if env["tier"] == ent.TIER_CLOUD_FREE)
    assert cf["target"] is None
    assert cf["row"] is None


def test_unlocks_batch_each_row_matches_unlocks_keys_when_populated(ent):
    rows = ent.previous_tier_unlocks_at_batch()
    for env in rows:
        if env["row"] is not None:
            assert set(env["row"].keys()) == _UNLOCKS_KEYS


def test_unlocks_batch_enterprise_source_has_populated_row(ent):
    """enterprise -> previous is the highest rank below 3 -- a paid
    rung (cloud_pro or pro). The row must be populated, not null."""
    rows = ent.previous_tier_unlocks_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is not None
    assert ent_row["row"] is not None
    assert set(ent_row["row"].keys()) == _UNLOCKS_KEYS


def test_unlocks_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_unlocks_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_unlocks_at_batch()
    assert enforce == grace


def test_unlocks_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_unlocks_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_unlocks_batch_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.previous_tier_unlocks_at_batch()
    after = ent.get_entitlement().to_dict()
    assert before == after


def test_unlocks_batch_returns_empty_on_top_level_failure(ent, monkeypatch):
    """A top-level failure short-circuits to ``[]`` so the matrix keeps
    rendering instead of breaking."""
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", property(boom))
    out = ent.previous_tier_unlocks_at_batch()
    assert out == []


def test_unlocks_batch_per_source_failure_collapses_row_only(ent, monkeypatch):
    """A per-source builder failure collapses to ``row=null`` on the
    populated envelope -- the source rung stays visible in the matrix."""
    def boom(_t):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_unlocks", boom)
    rows = ent.previous_tier_unlocks_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)
    for env in rows:
        assert env["row"] is None
        if env["tier"] not in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
            assert env["target"] is not None


# -- previous_tier_locks_at_batch --------------------------------------------


def test_locks_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_locks_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_locks_batch_each_envelope_has_envelope_shape(ent):
    rows = ent.previous_tier_locks_at_batch()
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_locks_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_locks_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_locks_batch_excludes_trial_from_sources(ent):
    rows = ent.previous_tier_locks_at_batch()
    assert ent.TIER_TRIAL not in {env["tier"] for env in rows}


def test_locks_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_locks_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_locks_batch_ordering_matches_tier_locks_batch(ent):
    at_rows = ent.previous_tier_locks_at_batch()
    live_rows = ent.tier_locks_batch()
    assert [r["tier"] for r in at_rows] == [r["tier"] for r in live_rows]


def test_locks_batch_each_envelope_byte_equals_scalar_helper(ent):
    rows = ent.previous_tier_locks_at_batch()
    for env in rows:
        scalar_row = ent.previous_tier_locks_at(env["tier"])
        assert env["row"] == scalar_row, env["tier"]


def test_locks_batch_target_resolves_via_previous_purchasable_before(ent):
    rows = ent.previous_tier_locks_at_batch()
    for env in rows:
        assert env["target"] == ent._previous_purchasable_tier_before(env["tier"])


def test_locks_batch_oss_source_collapses_to_null(ent):
    rows = ent.previous_tier_locks_at_batch()
    oss = next(env for env in rows if env["tier"] == ent.TIER_OSS)
    assert oss["target"] is None
    assert oss["row"] is None


def test_locks_batch_cloud_free_source_collapses_to_null(ent):
    rows = ent.previous_tier_locks_at_batch()
    cf = next(env for env in rows if env["tier"] == ent.TIER_CLOUD_FREE)
    assert cf["target"] is None
    assert cf["row"] is None


def test_locks_batch_cloud_starter_source_row_points_to_floor(ent):
    """cloud_starter -> previous is the floor (oss or cloud_free).
    tier_locks(floor) carries next_tier = floor's natural next-above
    rung (cloud_starter itself) and populated lost_* lists. The
    envelope must surface that populated row, not None on the
    envelope."""
    rows = ent.previous_tier_locks_at_batch()
    cs = next(env for env in rows if env["tier"] == ent.TIER_CLOUD_STARTER)
    assert cs["target"] in (ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert cs["row"] is not None
    assert cs["row"]["next_tier"] == ent.TIER_CLOUD_STARTER


def test_locks_batch_each_row_matches_locks_keys_when_populated(ent):
    rows = ent.previous_tier_locks_at_batch()
    for env in rows:
        if env["row"] is not None:
            assert set(env["row"].keys()) == _LOCKS_KEYS


def test_locks_batch_enterprise_source_row_populated(ent):
    """enterprise -> previous is a paid rung (cloud_pro or pro). The
    row must be populated, not null."""
    rows = ent.previous_tier_locks_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is not None
    assert ent_row["row"] is not None


def test_locks_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_locks_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_locks_at_batch()
    assert enforce == grace


def test_locks_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_locks_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_locks_batch_returns_empty_on_top_level_failure(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", property(boom))
    out = ent.previous_tier_locks_at_batch()
    assert out == []


# -- API: /api/entitlement/previous-tier-unlocks-at-batch -------------------


def test_unlocks_endpoint_returns_full_ladder(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert body["tiers"] == ent.previous_tier_unlocks_at_batch()
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_unlocks_endpoint_envelope_shape(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    body = rv.get_json()
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_unlocks_endpoint_cloud_starter_envelope_matches_scalar(client, ent):
    """The cloud_starter envelope in the batch byte-equals the body the
    scalar ``/previous-tier-unlocks-at?tier=cloud_starter`` endpoint
    returns (sans the resolver-context fields the batch wrapper adds)."""
    batch_rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    scalar_rv = client.get(
        "/api/entitlement/previous-tier-unlocks-at?tier=cloud_starter"
    )
    batch_cs = next(
        env
        for env in batch_rv.get_json()["tiers"]
        if env["tier"] == ent.TIER_CLOUD_STARTER
    )
    assert batch_cs == scalar_rv.get_json()


def test_unlocks_endpoint_resolver_context_present(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    body = rv.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


def test_unlocks_endpoint_oss_envelope_collapses(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    body = rv.get_json()
    oss = next(env for env in body["tiers"] if env["tier"] == ent.TIER_OSS)
    assert oss["target"] is None
    assert oss["row"] is None


def test_unlocks_endpoint_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_unlocks_at_batch", boom)
    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-unlocks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


def test_unlocks_endpoint_ignores_extra_query_args(client, ent):
    """The endpoint takes no params -- extra args are silently ignored
    rather than 400'd."""
    rv = client.get(
        "/api/entitlement/previous-tier-unlocks-at-batch?tier=oss&foo=bar"
    )
    assert rv.status_code == 200


# -- API: /api/entitlement/previous-tier-locks-at-batch ---------------------


def test_locks_endpoint_returns_full_ladder(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert body["tiers"] == ent.previous_tier_locks_at_batch()
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_locks_endpoint_envelope_shape(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    body = rv.get_json()
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_locks_endpoint_cloud_starter_envelope_matches_scalar(client, ent):
    batch_rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    scalar_rv = client.get(
        "/api/entitlement/previous-tier-locks-at?tier=cloud_starter"
    )
    batch_cs = next(
        env
        for env in batch_rv.get_json()["tiers"]
        if env["tier"] == ent.TIER_CLOUD_STARTER
    )
    assert batch_cs == scalar_rv.get_json()


def test_locks_endpoint_resolver_context_present(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    body = rv.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


def test_locks_endpoint_oss_envelope_collapses(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    body = rv.get_json()
    oss = next(env for env in body["tiers"] if env["tier"] == ent.TIER_OSS)
    assert oss["target"] is None
    assert oss["row"] is None


def test_locks_endpoint_cloud_starter_row_populated(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    body = rv.get_json()
    cs = next(env for env in body["tiers"] if env["tier"] == ent.TIER_CLOUD_STARTER)
    assert cs["target"] in (ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert cs["row"] is not None
    assert cs["row"]["next_tier"] == ent.TIER_CLOUD_STARTER


def test_locks_endpoint_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_locks_at_batch", boom)
    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


def test_locks_endpoint_ignores_extra_query_args(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-locks-at-batch?tier=oss&foo=bar"
    )
    assert rv.status_code == 200


# -- cross-endpoint: source axis lines up -----------------------------------


def test_endpoints_source_axis_aligned(client, ent):
    """The unlocks/locks batch endpoints emit the source axis in the
    same order so a UI can fold them into a single matrix row-for-row
    without re-sorting."""
    unlocks = client.get(
        "/api/entitlement/previous-tier-unlocks-at-batch"
    ).get_json()
    locks = client.get(
        "/api/entitlement/previous-tier-locks-at-batch"
    ).get_json()
    assert [r["tier"] for r in unlocks["tiers"]] == [
        r["tier"] for r in locks["tiers"]
    ]


def test_endpoints_each_scalar_source_byte_equal(client, ent):
    """End-to-end parity: every batched envelope byte-equals what the
    scalar endpoint would return for the same source."""
    unlocks_body = client.get(
        "/api/entitlement/previous-tier-unlocks-at-batch"
    ).get_json()
    locks_body = client.get(
        "/api/entitlement/previous-tier-locks-at-batch"
    ).get_json()
    for env in unlocks_body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/previous-tier-unlocks-at?tier={env['tier']}"
        ).get_json()
        assert env == scalar, env["tier"]
    for env in locks_body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={env['tier']}"
        ).get_json()
        assert env == scalar, env["tier"]
