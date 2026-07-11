"""Tests for ``next_tier_locks_at_batch`` /
``previous_tier_locks_at_batch`` and the companion
``/api/entitlement/{next,previous}-tier-locks-at-batch`` endpoints,
plus the private :func:`_next_at_envelope` / :func:`_previous_at_envelope`
builders they share with the ``_at_batch`` unlocks siblings when bound to
the :func:`tier_locks` builder.

Marginal-loss twin of the just-pinned
``test_entitlement_next_prev_tier_unlocks_at_batch.py``. Where the
unlocks batch is the upgrade-CTA column on a pricing matrix (what does
the next-up rung first grant), this batch is the downgrade-warning
column on the same matrix (what does the next-up rung first cost you at
the rung ABOVE it). Fills the last open test-file slot in the
source-anchored ``_at_batch`` family so a future refactor of the shared
envelope builder cannot silently drift the locks binding away from the
shape the diff / spec / unlocks / capacity siblings surface.

Pins covered here:

* :func:`_next_at_envelope` / :func:`_previous_at_envelope` BOUND TO
  :func:`tier_locks` compose source / target metadata with the
  per-target :func:`tier_locks` row in the same envelope shape
  :func:`_spec_at_envelope` / :func:`_diff_at_envelope` /
  :func:`_capacity_diff_at_envelope` publish -- ``tier``, ``tier_label``,
  ``tier_rank``, ``target``, ``target_label``, ``target_rank``, ``row``.
  The private builders are shared with the unlocks siblings, so pinning
  their behaviour under the locks builder guards against a refactor
  that only kept the unlocks binding intact.
* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* every batch envelope byte-equals the scalar helper
  (:func:`next_tier_locks_at` / :func:`previous_tier_locks_at`) for the
  same source -- the batch-vs-scalar parity that stops the batch
  what-if drifting from the scalar what-if (the same invariant the
  unlocks batch enforces against its scalar sibling)
* cross-batch parity with the diff / spec / unlocks / capacity
  ``_at_batch`` siblings: the source axis (envelope ``tier`` /
  ``tier_label`` / ``tier_rank`` and ordering) byte-equals each
  sibling, and the target axis (``target`` / ``target_label`` /
  ``target_rank``) matches the unlocks / diff / spec siblings, so a
  UI can fold all five batches into one matrix row-for-row
* at the source-side ceiling (``enterprise`` for next) / floor
  (``oss`` / ``cloud_free`` for previous) the envelope carries
  ``target=null`` and ``row=null`` rather than being dropped
* populated rows carry :func:`tier_locks` row shape: the inner
  ``row.tier`` is byte-equal to the envelope's ``target`` -- the
  locks descriptor identifies the target tier so the envelope's two
  slots must agree (the same row-vs-envelope invariant the unlocks
  batch pins on ``row.tier == envelope.target``)
* each populated envelope's row byte-equals the same-target row from
  :func:`tier_locks_batch` -- pins the batch to the live cumulative
  locks accessor so the source-anchored what-if cannot silently drift
  from the resolved-source ``/tier-locks-batch`` payload
* trial is excluded from the source axis (mirrors
  :func:`tier_locks_batch`)
* grace vs enforce yields identical rows (the helpers walk the static
  catalogue, not the gated resolver)
* the helpers never raise: a per-source builder failure collapses to
  ``row=null`` on the populated envelope; a top-level failure
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
    "row",
}

_LOCKS_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "next_tier",
    "next_tier_label",
    "next_tier_rank",
    "lost_features",
    "lost_runtimes",
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
    Enforcement off by default (grace mode) -- the locks ``_at`` family
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


# ── _next_at_envelope (locks binding) ────────────────────────────────────────


def test_next_envelope_shape_for_known_source(ent):
    env = ent._next_at_envelope(ent.TIER_OSS, ent.tier_locks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == target
    assert env["target_label"] == ent.tier_label(target)
    assert env["target_rank"] == ent.tier_rank(target)
    assert env["row"] == ent.tier_locks(target)


def test_next_envelope_enterprise_source_ceiling_collapses_row(ent):
    env = ent._next_at_envelope(ent.TIER_ENTERPRISE, ent.tier_locks)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["row"] is None


def test_next_envelope_unknown_source_keeps_envelope_populated(ent):
    env = ent._next_at_envelope("bogus", ent.tier_locks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    # Unknown source -- _next_purchasable_tier_after guards on _TIER_ORDER
    # so target collapses to None and the envelope surfaces row=None but
    # keeps the source id verbatim so the batch row stays visible.
    assert env["tier"] == "bogus"
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] is None
    assert env["row"] is None


def test_next_envelope_trims_and_lowercases_source(ent):
    env = ent._next_at_envelope("  OSS  ", ent.tier_locks)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == target
    assert env["row"] == ent.tier_locks(target)


def test_next_envelope_swallows_builder_exception(ent):
    def boom(_):
        raise RuntimeError("synthetic")

    env = ent._next_at_envelope(ent.TIER_OSS, boom)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    # Envelope stays populated with the resolved target metadata --
    # only ``row`` collapses so the pricing matrix can still render the
    # source rung with target labels intact.
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == target
    assert env["target_label"] == ent.tier_label(target)
    assert env["target_rank"] == ent.tier_rank(target)
    assert env["row"] is None


# ── _previous_at_envelope (locks binding) ────────────────────────────────────


def test_previous_envelope_shape_for_known_source(ent):
    env = ent._previous_at_envelope(ent.TIER_ENTERPRISE, ent.tier_locks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["target"] == target
    assert env["target_label"] == ent.tier_label(target)
    assert env["target_rank"] == ent.tier_rank(target)
    assert env["row"] == ent.tier_locks(target)


def test_previous_envelope_floor_source_collapses_row(ent):
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = ent._previous_at_envelope(floor, ent.tier_locks)
        assert env["tier"] == floor
        assert env["tier_label"] == ent.tier_label(floor)
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["row"] is None


def test_previous_envelope_unknown_source_keeps_envelope_populated(ent):
    env = ent._previous_at_envelope("bogus", ent.tier_locks)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == "bogus"
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] is None
    assert env["row"] is None


def test_previous_envelope_swallows_builder_exception(ent):
    def boom(_):
        raise RuntimeError("synthetic")

    env = ent._previous_at_envelope(ent.TIER_ENTERPRISE, boom)
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["target"] == target
    assert env["target_label"] == ent.tier_label(target)
    assert env["row"] is None


# ── next_tier_locks_at_batch ─────────────────────────────────────────────────


def test_next_batch_returns_envelope_per_purchasable_source(ent):
    rows = ent.next_tier_locks_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_locks_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_locks_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_locks_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_locks_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_locks_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["row"] is None


def test_next_batch_populated_rows_have_locks_row_shape(ent):
    for env in ent.next_tier_locks_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _LOCKS_ROW_KEYS
        # row.tier identifies the target tier so the envelope's two
        # slots must agree -- pins that the row-vs-envelope key doesn't
        # drift (the same invariant the unlocks ``_at_batch`` sibling
        # enforces with row.tier == envelope.target).
        assert env["row"]["tier"] == env["target"]
        assert env["row"]["tier_rank"] == env["target_rank"]
        assert env["row"]["tier_label"] == env["target_label"]


def test_next_batch_matches_scalar_helper_per_source(ent):
    for env in ent.next_tier_locks_at_batch():
        assert env["row"] == ent.next_tier_locks_at(env["tier"])


def test_next_batch_source_axis_matches_sibling_batches(ent):
    # The five ``_at_batch`` siblings (diff / spec / unlocks / locks /
    # capacity) MUST agree on the source axis -- envelope ``tier`` /
    # ``tier_label`` / ``tier_rank`` and ordering -- so a UI can fold
    # the five responses into one matrix without re-keying.
    lks = ent.next_tier_locks_at_batch()
    for sibling in (
        ent.next_tier_unlocks_at_batch(),
        ent.next_tier_diff_at_batch(),
        ent.next_tier_capacity_diff_at_batch(),
        ent.next_tier_spec_at_batch(),
    ):
        lks_keys = [(env["tier_rank"], env["tier"]) for env in lks]
        sib_keys = [(env["tier_rank"], env["tier"]) for env in sibling]
        assert sib_keys == lks_keys


def test_next_batch_target_axis_matches_sibling_batches(ent):
    # The target a UI lands on at each rung MUST agree across the
    # ``_at_batch`` siblings -- otherwise the locks column and the
    # unlocks / spec / diff columns would render different upgrade
    # rungs in the same matrix row.
    lks = {env["tier"]: env for env in ent.next_tier_locks_at_batch()}
    for sibling in (
        ent.next_tier_unlocks_at_batch(),
        ent.next_tier_diff_at_batch(),
        ent.next_tier_spec_at_batch(),
    ):
        by_tier = {env["tier"]: env for env in sibling}
        assert set(lks.keys()) == set(by_tier.keys())
        for tier in lks:
            assert lks[tier]["target"] == by_tier[tier]["target"], tier
            assert lks[tier]["target_rank"] == by_tier[tier]["target_rank"], tier
            assert lks[tier]["target_label"] == by_tier[tier]["target_label"], tier


def test_next_batch_row_matches_live_tier_locks_of_target(ent):
    # Each populated envelope's row byte-equals :func:`tier_locks`
    # invoked with the envelope's target -- pins the batch to the live
    # cumulative locks accessor so the batch what-if cannot silently
    # drift from the resolved-source ``/tier-locks-batch`` payload for
    # the same target tier (the same invariant the unlocks batch pins
    # against :func:`tier_unlocks_batch`).
    live = {row["tier"]: row for row in ent.tier_locks_batch()}
    for env in ent.next_tier_locks_at_batch():
        if env["row"] is None:
            continue
        assert env["row"] == live[env["target"]], env["target"]


def test_next_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_locks_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_locks_at_batch()
    assert enforce == grace


def test_next_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.next_tier_locks_at_batch() == []


def test_next_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_locks", boom)
    rows = ent.next_tier_locks_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_next_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_locks_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── previous_tier_locks_at_batch ─────────────────────────────────────────────


def test_prev_batch_returns_envelope_per_purchasable_source(ent):
    rows = ent.previous_tier_locks_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_locks_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_locks_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.previous_tier_locks_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_prev_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_locks_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_batch_floor_sources_collapse(ent):
    rows = {env["tier"]: env for env in ent.previous_tier_locks_at_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["row"] is None


def test_prev_batch_populated_rows_have_locks_row_shape(ent):
    for env in ent.previous_tier_locks_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _LOCKS_ROW_KEYS
        assert env["row"]["tier"] == env["target"]
        assert env["row"]["tier_rank"] == env["target_rank"]
        assert env["row"]["tier_label"] == env["target_label"]


def test_prev_batch_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_locks_at_batch():
        assert env["row"] == ent.previous_tier_locks_at(env["tier"])


def test_prev_batch_source_axis_matches_sibling_batches(ent):
    lks = ent.previous_tier_locks_at_batch()
    for sibling in (
        ent.previous_tier_unlocks_at_batch(),
        ent.previous_tier_diff_at_batch(),
        ent.previous_tier_capacity_diff_at_batch(),
        ent.previous_tier_spec_at_batch(),
    ):
        lks_keys = [(env["tier_rank"], env["tier"]) for env in lks]
        sib_keys = [(env["tier_rank"], env["tier"]) for env in sibling]
        assert sib_keys == lks_keys


def test_prev_batch_target_axis_matches_sibling_batches(ent):
    lks = {env["tier"]: env for env in ent.previous_tier_locks_at_batch()}
    for sibling in (
        ent.previous_tier_unlocks_at_batch(),
        ent.previous_tier_diff_at_batch(),
        ent.previous_tier_spec_at_batch(),
    ):
        by_tier = {env["tier"]: env for env in sibling}
        assert set(lks.keys()) == set(by_tier.keys())
        for tier in lks:
            assert lks[tier]["target"] == by_tier[tier]["target"], tier
            assert lks[tier]["target_rank"] == by_tier[tier]["target_rank"], tier
            assert lks[tier]["target_label"] == by_tier[tier]["target_label"], tier


def test_prev_batch_row_matches_live_tier_locks_of_target(ent):
    # Each populated envelope's row byte-equals :func:`tier_locks`
    # invoked with the envelope's target -- pins the batch to the live
    # cumulative locks accessor so the batch what-if cannot silently
    # drift from the resolved-source ``/tier-locks-batch`` payload for
    # the same target tier.
    live = {row["tier"]: row for row in ent.tier_locks_batch()}
    for env in ent.previous_tier_locks_at_batch():
        if env["row"] is None:
            continue
        assert env["row"] == live[env["target"]], env["target"]


def test_prev_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_locks_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_locks_at_batch()
    assert enforce == grace


def test_prev_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.previous_tier_locks_at_batch() == []


def test_prev_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_locks", boom)
    rows = ent.previous_tier_locks_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_prev_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_locks_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── API: /api/entitlement/next-tier-locks-at-batch ───────────────────────────


def test_next_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks-at-batch")
    assert rv.get_json()["tiers"] == ent.next_tier_locks_at_batch()


def test_next_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/next-tier-locks-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/next-tier-locks-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_next_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_locks_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-locks-at-batch ───────────────────────


def test_prev_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_prev_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    assert rv.get_json()["tiers"] == ent.previous_tier_locks_at_batch()


def test_prev_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/previous-tier-locks-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_prev_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_locks_at_batch", boom)
    rv = client.get("/api/entitlement/previous-tier-locks-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
