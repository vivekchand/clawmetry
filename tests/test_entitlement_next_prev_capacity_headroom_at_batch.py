"""Tests for ``next_tier_capacity_headroom_at_batch`` /
``previous_tier_capacity_headroom_at_batch`` -- batch siblings of the
scalar next / previous_tier_capacity_headroom_at what-if helpers,
plus the companion
``/api/entitlement/{next,previous}-tier-capacity-headroom-at-batch``
endpoints and the private :func:`_capacity_headroom_at_envelope`
builder they share.

These helpers let a pricing-comparison matrix UI render "on the rung
above / below each rung, given my usage, here's what my gauges
would look like" off **one** round-trip instead of N calls to the
scalar ``/{next,previous}-tier-capacity-headroom-at`` endpoint --
the batch counterpart of the scalar what-ifs.

Headroom-shaped mirror of
``/{next,previous}-tier-capacity-diff-at-batch``: envelope source /
target metadata line up byte-for-key so a UI can fold the diff and
headroom batches into one matrix without re-keying; the diff row's
capacity-transition triple is replaced by the per-axis headroom
envelope; every envelope additionally carries a ``direction`` echo.

Pins covered here:

* helper :func:`_capacity_headroom_at_envelope` composes the source /
  target metadata with the per-pair :func:`capacity_headroom_at`
  envelope in the same shape as :func:`_capacity_diff_at_envelope`,
  with ``row`` renamed ``headroom`` and ``direction`` added
* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)`` --
  byte-parallel to
  :func:`next_tier_capacity_diff_at_batch` /
  :func:`previous_tier_capacity_diff_at_batch`
* every envelope's ``headroom`` byte-equals
  ``capacity_headroom_at(_next_purchasable_tier_after(source), ...)``
  for the same source (or the previous-purchasable helper on the
  downgrade side) -- the batch-vs-composition parity that stops the
  batch what-if from drifting
* at the source-side ceiling (``enterprise`` as source for the next
  batch) and floor (``oss`` / ``cloud_free`` as source for the
  previous batch) the envelope carries ``target=null`` and
  ``headroom=null`` rather than being dropped
* every populated envelope on the next batch carries
  ``direction="upgrade"`` and every populated envelope on the
  previous batch carries ``direction="downgrade"``
* trial is excluded from the source axis (mirrors every other
  ``*_at_batch`` sibling)
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* the helpers never raise: a per-source builder failure collapses to
  ``headroom=null`` on the populated envelope; a top-level failure
  short-circuits to ``[]``
* the API endpoints never 5xx: a resolver failure yields an empty
  ``tiers`` list and a grace-shape envelope; per-axis stray query
  string short-circuits that axis to ``None`` on every envelope
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
    "direction",
    "headroom",
}

_HEADROOM_KEYS = {
    "tier",
    "tier_label",
    "channels",
    "retention_days",
    "nodes",
}

_HEADROOM_ROW_KEYS = {
    "kind",
    "used",
    "cap",
    "remaining",
    "is_unlimited",
    "at_limit",
    "over_limit",
    "pct_used",
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
    Enforcement off by default (grace mode). Both batch helpers walk
    the static catalogue and are independent of the resolver -- the
    fixture keeps the live resolver from surprising the test."""
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


# ── _capacity_headroom_at_envelope ────────────────────────────────────────────


def test_envelope_shape_for_known_pair(ent):
    env = ent._capacity_headroom_at_envelope(
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        "upgrade",
        channels=3,
        retention_days=5,
        nodes=1,
    )
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert env["direction"] == "upgrade"
    # headroom byte-equals the target's capacity_headroom_at for the
    # same usage inputs.
    assert env["headroom"] == ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=3, retention_days=5, nodes=1
    )


def test_envelope_none_target_collapses_headroom(ent):
    # No rung above / below: target=None collapses headroom to None,
    # envelope stays fully populated on source metadata.
    env = ent._capacity_headroom_at_envelope(
        ent.TIER_ENTERPRISE, None, "upgrade", channels=1
    )
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["direction"] == "upgrade"
    assert env["headroom"] is None


def test_envelope_unknown_source_keeps_target_side_populated(ent):
    # An unknown source still surfaces a populated envelope: the
    # target-side metadata is intact and headroom is the target's
    # capacity_headroom_at row unchanged.
    env = ent._capacity_headroom_at_envelope(
        "bogus", ent.TIER_CLOUD_STARTER, "upgrade", channels=1
    )
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == "bogus"
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["headroom"] == ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=1
    )


def test_envelope_trims_and_lowercases_source(ent):
    env = ent._capacity_headroom_at_envelope(
        "  OSS  ", ent.TIER_CLOUD_STARTER, "upgrade"
    )
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER


def test_envelope_none_source_input_is_tolerated(ent):
    # Defensive: the private builder does not raise on a None source
    # -- the batch loops never feed None but the helper is public in
    # the module surface.
    env = ent._capacity_headroom_at_envelope(
        None, ent.TIER_CLOUD_STARTER, "upgrade"
    )
    assert env["tier"] == ""
    assert env["tier_label"] is None
    assert env["target"] == ent.TIER_CLOUD_STARTER


def test_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_headroom_at", boom)
    env = ent._capacity_headroom_at_envelope(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER, "upgrade", channels=1
    )
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["headroom"] is None


def test_envelope_direction_string_is_echoed_verbatim(ent):
    for direction in ("upgrade", "downgrade", "arbitrary"):
        env = ent._capacity_headroom_at_envelope(
            ent.TIER_OSS, ent.TIER_CLOUD_STARTER, direction
        )
        assert env["direction"] == direction


def test_envelope_metadata_parallel_to_diff_envelope(ent):
    # Cross-family parity: the source / target metadata mirror the
    # diff envelope byte-for-byte so a UI can fold the two families
    # into one matrix.
    headroom = ent._capacity_headroom_at_envelope(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER, "upgrade"
    )
    diff = ent._capacity_diff_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    for key in ("tier", "tier_label", "tier_rank",
                "target", "target_label", "target_rank"):
        assert headroom[key] == diff[key]


# ── next_tier_capacity_headroom_at_batch ──────────────────────────────────────


def test_next_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.next_tier_capacity_headroom_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_capacity_headroom_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_capacity_headroom_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_batch_excludes_trial_from_sources(ent):
    sources = {
        env["tier"] for env in ent.next_tier_capacity_headroom_at_batch()
    }
    assert ent.TIER_TRIAL not in sources


def test_next_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_capacity_headroom_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_capacity_headroom_at_batch(channels=5)
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["headroom"] is None
    # Envelope still populated on the source side even at the ceiling.
    assert ent_row["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)


def test_next_batch_direction_is_upgrade_on_every_envelope(ent):
    # Direction echo pins to "upgrade" whether headroom is populated
    # or None -- the ceiling row keeps the direction so a UI does not
    # need to branch on the collapsed row.
    for env in ent.next_tier_capacity_headroom_at_batch():
        assert env["direction"] == "upgrade"


def test_next_batch_headroom_byte_equals_composition_per_source(ent):
    # Batch-vs-composition parity: every envelope's headroom byte-
    # equals ``capacity_headroom_at(_next_purchasable_tier_after(src), ...)``
    # for the same source and usage inputs.
    rows = ent.next_tier_capacity_headroom_at_batch(
        channels=7, retention_days=14, nodes=3
    )
    for env in rows:
        expected_target = ent._next_purchasable_tier_after(env["tier"])
        assert env["target"] == expected_target
        if expected_target is None:
            assert env["headroom"] is None
            continue
        assert env["headroom"] == ent.capacity_headroom_at(
            expected_target, channels=7, retention_days=14, nodes=3
        )


def test_next_batch_headroom_row_shape_when_populated(ent):
    rows = ent.next_tier_capacity_headroom_at_batch(
        channels=1, retention_days=1, nodes=1
    )
    for env in rows:
        if env["headroom"] is None:
            continue
        assert set(env["headroom"].keys()) == _HEADROOM_KEYS
        for axis in ("channels", "retention_days", "nodes"):
            row = env["headroom"][axis]
            assert row is not None
            assert set(row.keys()) == _HEADROOM_ROW_KEYS


def test_next_batch_headroom_tier_pins_target(ent):
    rows = ent.next_tier_capacity_headroom_at_batch(channels=1)
    for env in rows:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["tier"] == env["target"]


def test_next_batch_no_axes_supplied_yields_none_per_axis(ent):
    # "None means axis not supplied" posture: with no channels /
    # retention_days / nodes passed, every axis on every populated
    # headroom envelope is None.
    rows = ent.next_tier_capacity_headroom_at_batch()
    for env in rows:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["channels"] is None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None


def test_next_batch_partial_axes_supplied_are_echoed_only_there(ent):
    # Only channels was supplied: every populated envelope's headroom
    # has a populated channels row and None retention_days / nodes rows.
    rows = ent.next_tier_capacity_headroom_at_batch(channels=2)
    saw_populated = False
    for env in rows:
        if env["headroom"] is None:
            continue
        saw_populated = True
        assert env["headroom"]["channels"] is not None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None
    assert saw_populated


def test_next_batch_metadata_parallel_to_diff_batch_per_source(ent):
    # Envelope source / target metadata line up rung-for-rung with
    # next_tier_capacity_diff_at_batch so a UI can fold the two
    # batches into one matrix without re-sorting or re-keying.
    headroom = {
        env["tier"]: env for env in ent.next_tier_capacity_headroom_at_batch()
    }
    diff = {
        env["tier"]: env for env in ent.next_tier_capacity_diff_at_batch()
    }
    assert set(headroom) == set(diff)
    for src in headroom:
        for key in ("tier", "tier_label", "tier_rank",
                    "target", "target_label", "target_rank"):
            assert headroom[src][key] == diff[src][key]


def test_next_batch_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived: enforcement must not change the body.
    grace = ent.next_tier_capacity_headroom_at_batch(channels=1)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_capacity_headroom_at_batch(channels=1)
    assert enforce == grace


def test_next_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_capacity_headroom_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    # A crash on the top-level walker collapses to [] -- the pricing
    # table falls back to an empty list instead of 5xxing.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.next_tier_capacity_headroom_at_batch() == []


def test_next_batch_per_row_failure_collapses_to_headroom_null(
    ent, monkeypatch
):
    # A per-pair builder crash collapses the affected envelope's
    # headroom to None while the surrounding envelope stays visible.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_headroom_at", boom)
    rows = ent.next_tier_capacity_headroom_at_batch(channels=1)
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["headroom"] is None


# ── previous_tier_capacity_headroom_at_batch ──────────────────────────────────


def test_prev_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_capacity_headroom_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_batch_excludes_trial_from_sources(ent):
    sources = {
        env["tier"] for env in ent.previous_tier_capacity_headroom_at_batch()
    }
    assert ent.TIER_TRIAL not in sources


def test_prev_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_batch_floor_sources_collapse(ent):
    rows = {
        env["tier"]: env
        for env in ent.previous_tier_capacity_headroom_at_batch(channels=1)
    }
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["headroom"] is None
        assert env["tier_label"] == ent.tier_label(floor)


def test_prev_batch_direction_is_downgrade_on_every_envelope(ent):
    for env in ent.previous_tier_capacity_headroom_at_batch():
        assert env["direction"] == "downgrade"


def test_prev_batch_headroom_byte_equals_composition_per_source(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch(
        channels=7, retention_days=14, nodes=3
    )
    for env in rows:
        expected_target = ent._previous_purchasable_tier_before(env["tier"])
        assert env["target"] == expected_target
        if expected_target is None:
            assert env["headroom"] is None
            continue
        assert env["headroom"] == ent.capacity_headroom_at(
            expected_target, channels=7, retention_days=14, nodes=3
        )


def test_prev_batch_headroom_row_shape_when_populated(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch(
        channels=1, retention_days=1, nodes=1
    )
    for env in rows:
        if env["headroom"] is None:
            continue
        assert set(env["headroom"].keys()) == _HEADROOM_KEYS
        for axis in ("channels", "retention_days", "nodes"):
            row = env["headroom"][axis]
            assert row is not None
            assert set(row.keys()) == _HEADROOM_ROW_KEYS


def test_prev_batch_headroom_tier_pins_target(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch(channels=1)
    for env in rows:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["tier"] == env["target"]


def test_prev_batch_no_axes_supplied_yields_none_per_axis(ent):
    rows = ent.previous_tier_capacity_headroom_at_batch()
    for env in rows:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["channels"] is None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None


def test_prev_batch_metadata_parallel_to_diff_batch_per_source(ent):
    headroom = {
        env["tier"]: env
        for env in ent.previous_tier_capacity_headroom_at_batch()
    }
    diff = {
        env["tier"]: env for env in ent.previous_tier_capacity_diff_at_batch()
    }
    assert set(headroom) == set(diff)
    for src in headroom:
        for key in ("tier", "tier_label", "tier_rank",
                    "target", "target_label", "target_rank"):
            assert headroom[src][key] == diff[src][key]


def test_prev_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_capacity_headroom_at_batch(channels=1)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_capacity_headroom_at_batch(channels=1)
    assert enforce == grace


def test_prev_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_capacity_headroom_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.previous_tier_capacity_headroom_at_batch() == []


def test_prev_batch_per_row_failure_collapses_to_headroom_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_headroom_at", boom)
    rows = ent.previous_tier_capacity_headroom_at_batch(channels=1)
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["headroom"] is None


# ── cross-family parity: next vs previous ─────────────────────────────────────


def test_next_and_previous_batches_share_source_axis(ent):
    up = {env["tier"] for env in ent.next_tier_capacity_headroom_at_batch()}
    down = {
        env["tier"] for env in ent.previous_tier_capacity_headroom_at_batch()
    }
    assert up == down == set(ent._PURCHASABLE_TIERS)


def test_next_and_previous_batches_swap_at_matching_pairs(ent):
    # For every source X whose upgrade envelope resolves to a target
    # Y that itself appears as a downgrade envelope with X as its
    # target, the two envelopes describe the same (X, Y) pair -- the
    # headroom rows must be recognisably paired: the upgrade row's
    # headroom is at Y, the downgrade row's headroom is at X.
    up = {env["tier"]: env for env in ent.next_tier_capacity_headroom_at_batch()}
    down = {
        env["tier"]: env
        for env in ent.previous_tier_capacity_headroom_at_batch()
    }
    for src, up_env in up.items():
        if up_env["headroom"] is None:
            continue
        target = up_env["target"]
        if target not in down:
            continue
        down_env = down[target]
        if down_env["target"] != src:
            continue
        assert up_env["headroom"]["tier"] == target
        assert down_env["headroom"]["tier"] == src


# ── API: /api/entitlement/next-tier-capacity-headroom-at-batch ────────────────


def test_next_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-headroom-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-headroom-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_batch_endpoint_matches_helper_no_axes(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-headroom-at-batch")
    assert (
        rv.get_json()["tiers"] == ent.next_tier_capacity_headroom_at_batch()
    )


def test_next_batch_endpoint_matches_helper_with_axes(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-capacity-headroom-at-batch?"
        "channels=4&retention_days=9&nodes=2"
    )
    assert rv.get_json()["tiers"] == ent.next_tier_capacity_headroom_at_batch(
        channels=4, retention_days=9, nodes=2
    )


def test_next_batch_endpoint_bad_axis_short_circuits(client, ent):
    # Stray query strings for one axis must not silently blank other
    # axes on every envelope: channels=abc + retention_days= +
    # nodes=-1 all short-circuit to None on their axis.
    rv = client.get(
        "/api/entitlement/next-tier-capacity-headroom-at-batch?"
        "channels=abc&retention_days=&nodes=-1"
    )
    body = rv.get_json()
    for env in body["tiers"]:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["channels"] is None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None


def test_next_batch_endpoint_bool_in_disguise_short_circuits(client, ent):
    # ``true`` / ``false`` come in as text; the parser rejects them
    # rather than coerce them to ints so a stray typed value cannot
    # silently blank the matrix.
    rv = client.get(
        "/api/entitlement/next-tier-capacity-headroom-at-batch?"
        "channels=true&retention_days=false&nodes=True"
    )
    body = rv.get_json()
    for env in body["tiers"]:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["channels"] is None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None


def test_next_batch_endpoint_matches_scalar_capacity_headroom_at(client, ent):
    # Cross-endpoint parity: for every populated envelope, the batch's
    # headroom byte-equals the scalar
    # ``/api/entitlement/capacity-headroom-at?tier=<target>&channels=...``
    # body -- the test that stops the batch surface from drifting from
    # the singular ``_at`` sibling as the catalogue evolves.
    rv = client.get(
        "/api/entitlement/next-tier-capacity-headroom-at-batch?"
        "channels=3&retention_days=5&nodes=1"
    )
    for env in rv.get_json()["tiers"]:
        if env["headroom"] is None:
            continue
        scalar = client.get(
            f"/api/entitlement/capacity-headroom-at?tier={env['target']}"
            "&channels=3&retention_days=5&nodes=1"
        ).get_json()
        assert env["headroom"] == scalar


def test_next_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_capacity_headroom_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-capacity-headroom-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-capacity-headroom-at-batch ────────────


def test_prev_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_batch_endpoint_resolver_context(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch"
    )
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_batch_endpoint_matches_helper_no_axes(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch"
    )
    assert (
        rv.get_json()["tiers"]
        == ent.previous_tier_capacity_headroom_at_batch()
    )


def test_prev_batch_endpoint_matches_helper_with_axes(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch?"
        "channels=4&retention_days=9&nodes=2"
    )
    assert (
        rv.get_json()["tiers"]
        == ent.previous_tier_capacity_headroom_at_batch(
            channels=4, retention_days=9, nodes=2
        )
    )


def test_prev_batch_endpoint_bad_axis_short_circuits(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch?"
        "channels=abc&retention_days=&nodes=-1"
    )
    body = rv.get_json()
    for env in body["tiers"]:
        if env["headroom"] is None:
            continue
        assert env["headroom"]["channels"] is None
        assert env["headroom"]["retention_days"] is None
        assert env["headroom"]["nodes"] is None


def test_prev_batch_endpoint_direction_is_downgrade(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch"
    )
    for env in rv.get_json()["tiers"]:
        assert env["direction"] == "downgrade"


def test_prev_batch_endpoint_matches_scalar_capacity_headroom_at(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch?"
        "channels=3&retention_days=5&nodes=1"
    )
    for env in rv.get_json()["tiers"]:
        if env["headroom"] is None:
            continue
        scalar = client.get(
            f"/api/entitlement/capacity-headroom-at?tier={env['target']}"
            "&channels=3&retention_days=5&nodes=1"
        ).get_json()
        assert env["headroom"] == scalar


def test_prev_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_capacity_headroom_at_batch", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-headroom-at-batch"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
