"""Tests for ``next_tier_capacity_diff_at`` /
``previous_tier_capacity_diff_at`` (scalar what-ifs) and their
``_at_batch`` siblings, plus the companion
``/api/entitlement/{next,previous}-tier-capacity-diff-at[-batch]``
endpoints and the private :func:`_capacity_diff_at_envelope` builder
the batches share.

Capacity-only narrow lens of the
``{next,previous}_tier_diff_at[_batch]`` family that landed in
#3359 / #3361: where those helpers return the full :func:`tier_diff`
payload (``added_*`` + ``lost_*`` + ``capacity_changes`` +
``direction``) for each ``source -> next/prev-of-source`` pair, these
helpers return only the capacity slice (the
``{target, channel_limit, retention_days, node_limit}`` shape
:func:`capacity_diff_at` publishes) so a capacity-only tooltip on a
pricing-comparison cell can render the upgrade- / downgrade-side
capacity delta for any hypothetical source rung off **one** round-trip,
without first hitting ``/api/entitlement`` and without monkey-patching
the entitlement context.

Pins covered here:

* ``next_tier_capacity_diff_at(tier)`` byte-equals
  ``capacity_diff_at(tier, _next_purchasable_tier_after(tier))`` across
  every valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``previous_tier_capacity_diff_at`` against
  ``_previous_purchasable_tier_before``
* at the ceiling / floor (no rung strictly above / below source) both
  scalar helpers return ``None``
* trial-as-source resolves the same way the diff ``_at`` family does:
  next -> enterprise, previous -> cloud_starter
* unknown / empty / ``None`` / non-string source returns ``None``
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* :func:`_capacity_diff_at_envelope` composes source / target metadata
  with the per-pair :func:`capacity_diff_at` row in the same envelope
  shape :func:`_diff_at_envelope` publishes -- ``tier``, ``tier_label``,
  ``tier_rank``, ``target``, ``target_label``, ``target_rank``, ``row``
* both batches return one envelope per entry in
  :data:`_PURCHASABLE_TIERS`, sorted by ``(tier_rank, tier_id)``
* every batch envelope byte-equals the scalar endpoint body for the
  same source -- the batch-vs-scalar parity that stops the batch
  what-if drifting from the scalar what-if
* per-slice parity with the full ``_at_batch`` diff siblings: each
  envelope's ``row`` capacity-axis triples byte-equal the corresponding
  diff batch envelope's ``row.capacity_changes`` slot for the same
  source, so the four ``_at_batch`` surfaces (diff / unlocks / locks /
  capacity) never silently desync
* at the source-side ceiling (``enterprise`` for next) / floor
  (``oss`` / ``cloud_free`` for previous) the envelope carries
  ``target=null`` and ``row=null`` rather than being dropped
* trial is excluded from the source axis (mirrors the diff batch)
* the helpers never raise: a per-source builder failure collapses to
  ``row=null`` on the populated envelope; a top-level failure
  short-circuits to ``[]``
* the API endpoints never 5xx: a resolver failure yields an empty
  ``tiers`` list and a grace-shape envelope; scalar endpoints 400 on
  missing input, 404 on unknown ids, and 200 with ``row=null`` at the
  ceiling / floor
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_CAPACITY_ROW_KEYS = {
    "target",
    "channel_limit",
    "retention_days",
    "node_limit",
}

_AXIS_KEYS = {"before", "after", "delta", "unlocked", "locked"}

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
    Enforcement off by default (grace mode) -- the capacity-diff ``_at``
    family is catalogue-derived and independent of the resolver, so the
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


# ── next_tier_capacity_diff_at ───────────────────────────────────────────────


def test_next_capacity_at_matches_explicit_composition(ent):
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        nxt = ent._next_purchasable_tier_after(src)
        assert nxt is not None, src
        assert ent.next_tier_capacity_diff_at(src) == ent.capacity_diff_at(
            src, nxt
        ), src


def test_next_capacity_at_returns_none_at_ceiling(ent):
    assert ent.next_tier_capacity_diff_at(ent.TIER_ENTERPRISE) is None


def test_next_capacity_at_row_shape(ent):
    body = ent.next_tier_capacity_diff_at(ent.TIER_OSS)
    assert body is not None
    assert set(body.keys()) == _CAPACITY_ROW_KEYS
    assert body["target"] == ent.TIER_CLOUD_STARTER
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert set(body[axis].keys()) == _AXIS_KEYS


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_capacity_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_capacity_diff_at(bad) is None


def test_next_capacity_at_trims_and_lowercases(ent):
    assert ent.next_tier_capacity_diff_at(
        "  OSS  "
    ) == ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)


def test_next_capacity_at_trial_source_resolves_to_enterprise(ent):
    body = ent.next_tier_capacity_diff_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["target"] == ent.TIER_ENTERPRISE


def test_next_capacity_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_capacity_diff_at(ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_capacity_diff_at(ent.TIER_CLOUD_STARTER)
    assert enforce == grace


def test_next_capacity_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "capacity_diff_at",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.next_tier_capacity_diff_at(ent.TIER_OSS) is None


def test_next_capacity_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_capacity_diff_at(ent.TIER_OSS)
    assert body is not None
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_next_capacity_at_matches_diff_capacity_changes(ent):
    # The capacity slice MUST byte-equal the matching axis triples from
    # the full diff for the same source/target pair -- otherwise a UI
    # consuming both surfaces will render inconsistent capacity
    # numbers. Pinned to stop a drift between the two helpers.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        cap = ent.next_tier_capacity_diff_at(src)
        diff = ent.next_tier_diff_at(src)
        assert cap is not None and diff is not None, src
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert cap[axis] == diff["capacity_changes"][axis], (src, axis)


# ── previous_tier_capacity_diff_at ───────────────────────────────────────────


def test_prev_capacity_at_matches_explicit_composition(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_capacity_diff_at(src) == ent.capacity_diff_at(
            src, prv
        ), src


def test_prev_capacity_at_returns_none_at_floor(ent):
    assert ent.previous_tier_capacity_diff_at(ent.TIER_OSS) is None
    assert ent.previous_tier_capacity_diff_at(ent.TIER_CLOUD_FREE) is None


def test_prev_capacity_at_row_shape(ent):
    body = ent.previous_tier_capacity_diff_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert set(body.keys()) == _CAPACITY_ROW_KEYS
    assert body["target"] == ent.TIER_CLOUD_PRO
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert set(body[axis].keys()) == _AXIS_KEYS


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_prev_capacity_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_capacity_diff_at(bad) is None


def test_prev_capacity_at_trims_and_lowercases(ent):
    assert ent.previous_tier_capacity_diff_at(
        "  CLOUD_STARTER  "
    ) == ent.capacity_diff_at(ent.TIER_CLOUD_STARTER, ent.TIER_OSS)


def test_prev_capacity_at_trial_source_resolves_to_cloud_starter(ent):
    body = ent.previous_tier_capacity_diff_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_prev_capacity_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_capacity_diff_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_capacity_diff_at(ent.TIER_CLOUD_PRO)
    assert enforce == grace


def test_prev_capacity_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "capacity_diff_at",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.previous_tier_capacity_diff_at(ent.TIER_ENTERPRISE) is None


def test_prev_capacity_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_capacity_diff_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert body["target"] == ent.TIER_CLOUD_PRO


def test_prev_capacity_at_matches_diff_capacity_changes(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        cap = ent.previous_tier_capacity_diff_at(src)
        diff = ent.previous_tier_diff_at(src)
        assert cap is not None and diff is not None, src
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert cap[axis] == diff["capacity_changes"][axis], (src, axis)


# ── _capacity_diff_at_envelope ───────────────────────────────────────────────


def test_capacity_envelope_shape_for_known_pair(ent):
    env = ent._capacity_diff_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    assert env["tier"] == ent.TIER_OSS
    assert env["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert env["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert env["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert env["row"] == ent.capacity_diff_at(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER
    )


def test_capacity_envelope_none_target_collapses_row(ent):
    env = ent._capacity_diff_at_envelope(ent.TIER_ENTERPRISE, None)
    assert env["tier"] == ent.TIER_ENTERPRISE
    assert env["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert env["target"] is None
    assert env["target_label"] is None
    assert env["target_rank"] is None
    assert env["row"] is None


def test_capacity_envelope_unknown_source_keeps_envelope_populated(ent):
    env = ent._capacity_diff_at_envelope("bogus", ent.TIER_CLOUD_STARTER)
    assert set(env.keys()) == _ENVELOPE_KEYS
    # capacity_diff_at returns None on unknown source -- the envelope
    # surfaces row=None but keeps target metadata so the batch row
    # stays visible.
    assert env["tier_label"] is None
    assert env["tier_rank"] == -1
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


def test_capacity_envelope_trims_and_lowercases(ent):
    env = ent._capacity_diff_at_envelope("  OSS  ", ent.TIER_CLOUD_STARTER)
    assert env["tier"] == ent.TIER_OSS
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] == ent.capacity_diff_at(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER
    )


def test_capacity_envelope_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_diff_at", boom)
    env = ent._capacity_diff_at_envelope(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert env["target"] == ent.TIER_CLOUD_STARTER
    assert env["row"] is None


# ── next_tier_capacity_diff_at_batch ─────────────────────────────────────────


def test_next_capacity_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.next_tier_capacity_diff_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_next_capacity_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.next_tier_capacity_diff_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_capacity_batch_source_axis_matches_purchasable(ent):
    rows = ent.next_tier_capacity_diff_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_next_capacity_batch_excludes_trial_from_sources(ent):
    sources = {env["tier"] for env in ent.next_tier_capacity_diff_at_batch()}
    assert ent.TIER_TRIAL not in sources


def test_next_capacity_batch_sorted_by_rank_then_id(ent):
    rows = ent.next_tier_capacity_diff_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_next_capacity_batch_enterprise_source_ceiling_collapses(ent):
    rows = ent.next_tier_capacity_diff_at_batch()
    ent_row = next(env for env in rows if env["tier"] == ent.TIER_ENTERPRISE)
    assert ent_row["target"] is None
    assert ent_row["target_label"] is None
    assert ent_row["target_rank"] is None
    assert ent_row["row"] is None


def test_next_capacity_batch_populated_rows_have_capacity_row_shape(ent):
    for env in ent.next_tier_capacity_diff_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _CAPACITY_ROW_KEYS
        # row.target is byte-equal to envelope.target on every
        # populated row -- the same pin the diff batch's row.from
        # holds against envelope.tier.
        assert env["row"]["target"] == env["target"]


def test_next_capacity_batch_matches_scalar_helper_per_source(ent):
    for env in ent.next_tier_capacity_diff_at_batch():
        assert env["row"] == ent.next_tier_capacity_diff_at(env["tier"])


def test_next_capacity_batch_matches_diff_batch_capacity_changes(ent):
    # The capacity batch row's per-axis triples MUST byte-equal the
    # diff batch row's ``capacity_changes`` slot for the same source --
    # the cross-surface invariant that stops the two ``_at_batch``
    # surfaces from silently disagreeing on the same pair.
    cap = {env["tier"]: env for env in ent.next_tier_capacity_diff_at_batch()}
    diff = {env["tier"]: env for env in ent.next_tier_diff_at_batch()}
    assert set(cap.keys()) == set(diff.keys())
    for tier in cap:
        c = cap[tier]["row"]
        d = diff[tier]["row"]
        if c is None:
            assert d is None
            continue
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert c[axis] == d["capacity_changes"][axis], (tier, axis)


def test_next_capacity_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_capacity_diff_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_capacity_diff_at_batch()
    assert enforce == grace


def test_next_capacity_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.next_tier_capacity_diff_at_batch() == []


def test_next_capacity_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_diff_at", boom)
    rows = ent.next_tier_capacity_diff_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_next_capacity_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.next_tier_capacity_diff_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── previous_tier_capacity_diff_at_batch ─────────────────────────────────────


def test_prev_capacity_batch_returns_list_for_every_purchasable_source(ent):
    rows = ent.previous_tier_capacity_diff_at_batch()
    assert isinstance(rows, list)
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


def test_prev_capacity_batch_each_envelope_has_envelope_shape(ent):
    for env in ent.previous_tier_capacity_diff_at_batch():
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_prev_capacity_batch_source_axis_matches_purchasable(ent):
    rows = ent.previous_tier_capacity_diff_at_batch()
    sources = {env["tier"] for env in rows}
    assert sources == set(ent._PURCHASABLE_TIERS)


def test_prev_capacity_batch_excludes_trial_from_sources(ent):
    sources = {
        env["tier"] for env in ent.previous_tier_capacity_diff_at_batch()
    }
    assert ent.TIER_TRIAL not in sources


def test_prev_capacity_batch_sorted_by_rank_then_id(ent):
    rows = ent.previous_tier_capacity_diff_at_batch()
    keys = [(env["tier_rank"], env["tier"]) for env in rows]
    assert keys == sorted(keys)


def test_prev_capacity_batch_floor_sources_collapse(ent):
    rows = {env["tier"]: env for env in ent.previous_tier_capacity_diff_at_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        env = rows[floor]
        assert env["target"] is None
        assert env["target_label"] is None
        assert env["target_rank"] is None
        assert env["row"] is None


def test_prev_capacity_batch_populated_rows_have_capacity_row_shape(ent):
    for env in ent.previous_tier_capacity_diff_at_batch():
        if env["row"] is None:
            continue
        assert set(env["row"].keys()) == _CAPACITY_ROW_KEYS
        assert env["row"]["target"] == env["target"]


def test_prev_capacity_batch_matches_scalar_helper_per_source(ent):
    for env in ent.previous_tier_capacity_diff_at_batch():
        assert env["row"] == ent.previous_tier_capacity_diff_at(env["tier"])


def test_prev_capacity_batch_matches_diff_batch_capacity_changes(ent):
    cap = {
        env["tier"]: env for env in ent.previous_tier_capacity_diff_at_batch()
    }
    diff = {env["tier"]: env for env in ent.previous_tier_diff_at_batch()}
    assert set(cap.keys()) == set(diff.keys())
    for tier in cap:
        c = cap[tier]["row"]
        d = diff[tier]["row"]
        if c is None:
            assert d is None
            continue
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert c[axis] == d["capacity_changes"][axis], (tier, axis)


def test_prev_capacity_batch_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_capacity_diff_at_batch()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_capacity_diff_at_batch()
    assert enforce == grace


def test_prev_capacity_batch_top_level_failure_short_circuits_to_empty(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", boom)
    assert ent.previous_tier_capacity_diff_at_batch() == []


def test_prev_capacity_batch_per_row_failure_collapses_to_row_null(
    ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "capacity_diff_at", boom)
    rows = ent.previous_tier_capacity_diff_at_batch()
    assert rows
    for env in rows:
        assert set(env.keys()) == _ENVELOPE_KEYS
        assert env["row"] is None


def test_prev_capacity_batch_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.previous_tier_capacity_diff_at_batch()
    assert len(rows) == len(ent._PURCHASABLE_TIERS)


# ── API: /api/entitlement/next-tier-capacity-diff-at ─────────────────────────


def test_next_capacity_at_endpoint_returns_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/next-tier-capacity-diff-at?tier={ent.TIER_OSS}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.next_tier_capacity_diff_at(ent.TIER_OSS)


def test_next_capacity_at_endpoint_missing_tier_400(client):
    rv = client.get("/api/entitlement/next-tier-capacity-diff-at")
    assert rv.status_code == 400
    assert rv.get_json() == {"error": "missing tier"}


def test_next_capacity_at_endpoint_unknown_tier_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-capacity-diff-at?tier=bogus"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_next_capacity_at_endpoint_ceiling_surfaces_null_target(client, ent):
    rv = client.get(
        f"/api/entitlement/next-tier-capacity-diff-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_next_capacity_at_endpoint_trims_and_lowercases(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-capacity-diff-at?tier=%20%20OSS%20%20"
    )
    assert rv.status_code == 200
    assert rv.get_json()["tier"] == ent.TIER_OSS


def test_next_capacity_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_capacity_diff_at", boom)
    rv = client.get(
        f"/api/entitlement/next-tier-capacity-diff-at?tier={ent.TIER_OSS}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["row"] is None


# ── API: /api/entitlement/previous-tier-capacity-diff-at ─────────────────────


def test_prev_capacity_at_endpoint_returns_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/previous-tier-capacity-diff-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.previous_tier_capacity_diff_at(
        ent.TIER_ENTERPRISE
    )


def test_prev_capacity_at_endpoint_missing_tier_400(client):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff-at")
    assert rv.status_code == 400


def test_prev_capacity_at_endpoint_unknown_tier_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-capacity-diff-at?tier=bogus"
    )
    assert rv.status_code == 404


def test_prev_capacity_at_endpoint_floor_surfaces_null_target(client, ent):
    rv = client.get(
        f"/api/entitlement/previous-tier-capacity-diff-at?tier={ent.TIER_OSS}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["row"] is None


def test_prev_capacity_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_capacity_diff_at", boom)
    rv = client.get(
        f"/api/entitlement/previous-tier-capacity-diff-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert rv.status_code == 200
    assert rv.get_json()["row"] is None


# ── API: /api/entitlement/next-tier-capacity-diff-at-batch ───────────────────


def test_next_capacity_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)
    for env in body["tiers"]:
        assert set(env.keys()) == _ENVELOPE_KEYS


def test_next_capacity_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_next_capacity_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff-at-batch")
    assert rv.get_json()["tiers"] == ent.next_tier_capacity_diff_at_batch()


def test_next_capacity_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/next-tier-capacity-diff-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/next-tier-capacity-diff-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_next_capacity_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_capacity_diff_at_batch", boom)
    rv = client.get("/api/entitlement/next-tier-capacity-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# ── API: /api/entitlement/previous-tier-capacity-diff-at-batch ───────────────


def test_prev_capacity_batch_endpoint_returns_envelopes(client, ent):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _BATCH_RESPONSE_KEYS
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_prev_capacity_batch_endpoint_resolver_context(client, ent):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff-at-batch")
    body = rv.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] == bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_prev_capacity_batch_endpoint_matches_helper(client, ent):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff-at-batch")
    assert rv.get_json()["tiers"] == ent.previous_tier_capacity_diff_at_batch()


def test_prev_capacity_batch_endpoint_matches_scalar_per_source(client, ent):
    batch = client.get(
        "/api/entitlement/previous-tier-capacity-diff-at-batch"
    ).get_json()["tiers"]
    by_tier = {env["tier"]: env for env in batch}
    for src in ent._PURCHASABLE_TIERS:
        scalar = client.get(
            f"/api/entitlement/previous-tier-capacity-diff-at?tier={src}"
        ).get_json()
        assert by_tier[src] == scalar


def test_prev_capacity_batch_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_capacity_diff_at_batch", boom)
    rv = client.get("/api/entitlement/previous-tier-capacity-diff-at-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
