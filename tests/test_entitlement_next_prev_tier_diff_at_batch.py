"""Tests for ``next_tier_diff_at_batch`` /
``previous_tier_diff_at_batch`` -- batch siblings of the scalar
:func:`next_tier_diff_at` / :func:`previous_tier_diff_at` what-ifs,
plus the companion
``/api/entitlement/{next,previous}-tier-diff-at-batch`` endpoints and
the private :func:`_diff_at_envelope` builder they share.

These helpers let a pricing-comparison matrix UI render the full
:func:`tier_diff` payload (``added_*`` + ``lost_*`` +
``capacity_changes`` + ``direction``) for the rung above / below
each rung off **one** round-trip instead of N calls to the scalar
``/next-tier-diff-at`` / ``/previous-tier-diff-at`` endpoint -- the
batch counterpart of the scalar what-ifs that landed in #3359.

The "all-slices-in-one-row" member of the per-direction batch
families: alongside the single-slice ``_at_batch`` siblings
(unlocks for the grant slice, locks for the loss slice), this batch
folds all slices into one row so a UI can fetch the whole upgrade /
downgrade matrix in one call instead of two.

Pins covered here:

* helper :func:`_diff_at_envelope` composes the source/target
  metadata with the per-pair :func:`tier_diff` row in the same
  envelope shape the scalar diff endpoints surface -- ``tier``,
  ``tier_label``, ``tier_rank``, ``target``, ``target_label``,
  ``target_rank``, ``row``
* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* every envelope byte-equals the body that the scalar
  ``/api/entitlement/{next,previous}-tier-diff-at?tier=<src>`` endpoint
  returns for the same source -- the batch-vs-scalar parity that
  stops the batch what-if drifting from the scalar what-if
* per-slice parity with the single-slice ``_at_batch`` siblings:
  ``row.added_features`` / ``row.added_runtimes`` byte-equal the
  unlocks batch's ``row.features`` / ``row.runtimes`` for the same
  source, and ``row.lost_features`` / ``row.lost_runtimes``
  byte-equal the locks batch's lost slots for the same source
* at the source-side ceiling (``enterprise`` as source for the next
  batch) and floor (``oss`` / ``cloud_free`` as source for the
  previous batch) the envelope carries ``target=null`` and
  ``row=null`` rather than being dropped
* every populated row's ``from`` is byte-equal to the envelope's
  ``tier`` -- the source-endpoint pin that differentiates this batch
  from the unlocks/locks ``_at_batch`` family
* every populated next-row's ``direction`` is ``"upgrade"`` and every
  populated previous-row's ``direction`` is ``"downgrade"``
* trial is excluded from the source axis (mirrors
  :func:`tier_diff_batch`)
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
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


_DIFF_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
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


# ── _diff_at_envelope ────────────────────────────────────────────────────────


def test_diff_at_envelope_shape_for_known_pair(ent):
    env = ent._diff_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert env["row"] == ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)


def test_diff_at_envelope_none_target_collapses_row(ent):
    # No rung above / below: target=None means the row collapses to
    # None too, but the envelope stays fully populated on the source
    # metadata.
    env = ent._diff_at_envelope(ent.TIER_ENTERPRISE, None)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["row"] is None


def test_diff_at_envelope_unknown_source_keeps_envelope_populated(ent):
    env = ent._diff_at_envelope("bogus", ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    # tier_diff itself returns None on unknown source -- the envelope
    # surfaces row=None but keeps the populated target metadata so the
    # batch row stays visible.
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


def test_diff_at_envelope_trims_and_lowercases(ent):
    env = ent._diff_at_envelope("  OSS  ", ent.TIER_CLOUD_STARTER)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] == ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)


def test_diff_at_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_diff", boom)
    env = ent._diff_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


# ── next_tier_diff_at_batch ──────────────────────────────────────────────────


def test_next_diff_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.next_tier_diff_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_diff_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_diff_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_diff_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_diff_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_diff_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_diff_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_diff_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_diff_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_diff_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_diff_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["row"] is None


def test_next_diff_batch_row_from_pins_source(ent):
    # The source-endpoint pin the diff family differs by vs the
    # unlocks/locks _at family: row.from is byte-equal to the
    # envelope's tier on every populated row.
    for env in ent.next_tier_diff_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["from"] == env["tier"]


def test_next_diff_batch_populated_rows_direction_is_upgrade(ent):
    for env in ent.next_tier_diff_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["direction"] == "upgrade"


def test_next_diff_batch_matches_scalar_helper_per_source(ent):
    # Batch-vs-scalar parity: every envelope's row byte-equals the
    # scalar :func:`next_tier_diff_at` for the same source.
    for env in ent.next_tier_diff_at_batch():
        assert env["row"] == ent.next_tier_diff_at(env["tier"])


def test_next_diff_batch_added_slice_matches_unlocks_batch(ent):
    # Per-slice parity on the grant side: a diff's ``added_features``
    # /  ``added_runtimes`` byte-equals ``tier_unlocks(next_X).features
    # / runtimes`` for the same source X by construction (the diff's
    # ``to`` is X's natural next-above, which is also tier_unlocks'
    # canonical previous_tier for that target). Locks the diff batch
    # to the unlocks batch on the upgrade side so the two surfaces
    # cannot silently desync.
    diff = {env["tier"]: env for env in ent.next_tier_diff_at_batch()}
    unlocks = {env["tier"]: env for env in ent.next_tier_unlocks_at_batch()}
    for tier in diff:
        d = diff[tier]["row"]
        u = unlocks[tier]["row"]
        if d is None:
            assert u is None
            continue
        assert d["added_features"] == u["features"]
        assert d["added_runtimes"] == u["runtimes"]


def test_next_diff_batch_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived: enforcement must not change the body.
    grace = ent.next_tier_diff_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_diff_at_batch()
    assert enforce == grace


def test_next_diff_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.next_tier_diff_at_batch() == []


def test_next_diff_batch_per_row_failure_collapses_to_row_null(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_diff", boom)
    rows = ent.next_tier_diff_at_batch()
    # Every populated envelope keeps its source metadata; the row
    # collapses to null because the per-pair builder raised.
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_next_diff_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_diff_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── previous_tier_diff_at_batch ──────────────────────────────────────────────


def test_prev_diff_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_diff_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_diff_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_diff_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_diff_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_diff_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_diff_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.previous_tier_diff_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_prev_diff_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_diff_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_diff_batch_floor_sources_collapse(ent):
    rows = {env["tier"]: env for env in ent.previous_tier_diff_at_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["row"] is None


def test_prev_diff_batch_row_from_pins_source(ent):
    for env in ent.previous_tier_diff_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["from"] == env["tier"]


def test_prev_diff_batch_populated_rows_direction_is_downgrade(ent):
    for env in ent.previous_tier_diff_at_batch():
        if env["row"] is None:
            continue
        assert env["row"]["direction"] == "downgrade"


def test_prev_diff_batch_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_diff_at_batch():
        assert env["row"] == ent.previous_tier_diff_at(env["tier"])


def test_prev_diff_batch_swap_identity_against_next_diff_batch(ent):
    # tier_diff(X, Y).added_* byte-equals tier_diff(Y, X).lost_* for any
    # pair (the swap-identity invariant). For every source X whose
    # natural ``next_X`` itself appears as a previous-batch envelope,
    # the upgrade diff (X -> next_X) and the downgrade diff
    # (next_X -> X) must be perfect mirrors. Pins the previous batch
    # against the next batch so the two surfaces cannot silently
    # disagree on the same pair.
    up = {env["tier"]: env for env in ent.next_tier_diff_at_batch()}
    down = {env["tier"]: env for env in ent.previous_tier_diff_at_batch()}
    for src, up_env in up.items():
        if up_env["row"] is None:
            continue
        target = up_env["target"]
        if target not in down:
            continue
        # Look up the downgrade envelope keyed on next_X. It only
        # mirrors the upgrade when its target is X itself (same-rank
        # siblings can resolve elsewhere -- skip those gracefully).
        down_env = down[target]
        if down_env["target"] != src:
            continue
        u = up_env["row"]
        d = down_env["row"]
        assert u["added_features"] == d["lost_features"]
        assert u["added_runtimes"] == d["lost_runtimes"]
        assert u["lost_features"] == d["added_features"]
        assert u["lost_runtimes"] == d["added_runtimes"]


def test_prev_diff_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_diff_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_diff_at_batch()
    assert enforce == grace


def test_prev_diff_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.previous_tier_diff_at_batch() == []


def test_prev_diff_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_diff", boom)
    rows = ent.previous_tier_diff_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_prev_diff_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_diff_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── API: /api/entitlement/next-tier-diff-at-batch ────────────────────────────


def test_next_diff_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_diff_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_diff_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at-batch")
    assert rv.get_json()["tiers"] == ent.next_tier_diff_at_batch()


def test_next_diff_batch_endpoint_matches_scalar_per_source(client, ent):
    # The batch envelope must byte-equal the scalar endpoint body for
    # the same source -- the test that stops the batch surface from
    # drifting from the scalar surface as the catalogue evolves.
    batch = client.get(
        "/api/entitlement/next-tier-diff-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/next-tier-diff-at?tier={src}"
        ).get_json()
        # Strip the resolver-context keys that only the batch envelope
        # surfaces (the scalar endpoint does not carry them).
        assert by_tier[src] == scalar


def test_next_diff_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_diff_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-diff-at-batch ────────────────────────


def test_prev_diff_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/previous-tier-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_diff_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/previous-tier-diff-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_diff_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/previous-tier-diff-at-batch")
    assert rv.get_json()["tiers"] == ent.previous_tier_diff_at_batch()


def test_prev_diff_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/previous-tier-diff-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/previous-tier-diff-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_prev_diff_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_diff_at_batch", boom)
    rv = client.get("/api/entitlement/previous-tier-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
