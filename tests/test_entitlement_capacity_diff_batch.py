"""Tests for ``clawmetry.entitlements.capacity_diff_batch`` +
``GET /api/entitlement/capacity-diff-batch``.

Plural sibling of :func:`capacity_diff`. Where the singular helper
answers "what would the channel cap / retention / node cap look like at
tier X" one tier at a time, the batch returns the same payload shape for
every entry in ``_PURCHASABLE_TIERS`` so a pricing-page table can render
the capacity column off **one** round-trip. These tests pin the
contract:

  - returns one row per purchasable tier in (rank, id) order
  - each row matches the singular ``capacity_diff(tier)`` output exactly
  - trial is excluded (mirrors the other ``*-batch`` siblings)
  - rung order is byte-stable against ``tier_unlocks_batch`` /
    ``tier_locks_batch`` / ``preview_batch`` so a pricing table lines up
    rung-for-rung
  - never raises -- a resolver failure short-circuits to ``[]``
  - the wrapper endpoint always returns a 200 with the grace envelope so
    the pricing page keeps rendering even when the resolver is sick
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── shape ─────────────────────────────────────────────────────────────────


def test_returns_list(ent):
    rows = ent.capacity_diff_batch()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_singular_shape(ent):
    rows = ent.capacity_diff_batch()
    expected = {"target", "channel_limit", "retention_days", "node_limit"}
    for row in rows:
        assert set(row.keys()) == expected


def test_each_axis_carries_full_triple(enforced):
    rows = enforced.capacity_diff_batch()
    for row in rows:
        for axis in ("channel_limit", "retention_days", "node_limit"):
            triple = row[axis]
            # Under enforce every purchasable tier resolves to a real
            # transition payload -- the singular helper's full triple.
            assert isinstance(triple, dict)
            assert set(triple) == {"before", "after", "delta", "unlocked", "locked"}


def test_excludes_trial(ent):
    rows = ent.capacity_diff_batch()
    ids = {row["target"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier(ent):
    rows = ent.capacity_diff_batch()
    ids = {row["target"] for row in rows}
    assert ids == set(ent._PURCHASABLE_TIERS)


# ── ordering ──────────────────────────────────────────────────────────────


def test_rows_sorted_by_rank_then_id(ent):
    rows = ent.capacity_diff_batch()
    keys = [(ent._TIER_RANK.get(r["target"], -1), r["target"]) for r in rows]
    assert keys == sorted(keys)


def test_ordering_byte_stable_against_other_batches(ent):
    cap_ids = [r["target"] for r in ent.capacity_diff_batch()]
    unlock_ids = [r["tier"] for r in ent.tier_unlocks_batch()]
    lock_ids = [r["tier"] for r in ent.tier_locks_batch()]
    preview_ids = [r["tier"] for r in ent.preview_batch()]
    # All four batches walk _PURCHASABLE_TIERS in the same (rank, id)
    # order so a pricing-page table lines up rung-for-rung without
    # client-side re-sort.
    assert cap_ids == unlock_ids == lock_ids == preview_ids


# ── per-row identity with the singular helper ────────────────────────────


def test_each_row_matches_singular_capacity_diff_under_enforce(enforced):
    rows = enforced.capacity_diff_batch()
    for row in rows:
        # The batch is a thin walker over :func:`capacity_diff` so the
        # singular endpoint and the batch must agree byte-for-byte per
        # row.
        assert row == enforced.capacity_diff(row["target"])


def test_each_row_matches_singular_capacity_diff_under_grace(ent):
    rows = ent.capacity_diff_batch()
    for row in rows:
        assert row == ent.capacity_diff(row["target"])


# ── grace posture ─────────────────────────────────────────────────────────


def test_grace_mode_collapses_channel_before_to_unlimited(ent):
    # Under grace the resolved entitlement reports
    # ``channel_limit() is None`` because there's no live cap. Each
    # row's channel ``before`` therefore comes off the grace-resolved
    # entitlement as ``None`` (the per-tier ``after`` is the target's
    # static cap, so ``unlocked`` / ``locked`` still varies by direction
    # -- that's the singular helper's job to settle).
    rows = ent.capacity_diff_batch()
    assert rows  # sanity: not short-circuiting under grace
    for row in rows:
        assert row["channel_limit"]["before"] is None


# ── never-raise contract ─────────────────────────────────────────────────


def test_batch_swallows_resolver_failure(monkeypatch, enforced):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(enforced, "capacity_diff", boom)
    # The batch wraps :func:`capacity_diff` in a try/except envelope, so
    # a synthetic blow-up inside the inner helper short-circuits to ``[]``
    # rather than 500-ing the pricing page.
    assert enforced.capacity_diff_batch() == []


# ── API surface ──────────────────────────────────────────────────────────


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/capacity-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body) == {
        "tiers",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert isinstance(body["tiers"], list)


def test_api_rows_match_module_helper(client, ent):
    rv = client.get("/api/entitlement/capacity-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tiers"] == ent.capacity_diff_batch()


def test_api_carries_current_tier_under_enforce(enforced_client, enforced):
    rv = enforced_client.get("/api/entitlement/capacity-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    cur = enforced.get_entitlement()
    assert body["current_tier"] == cur.tier
    assert body["current_tier_rank"] == enforced.tier_rank(cur.tier)
    assert body["enforced"] is True


def test_api_carries_grace_envelope(client, ent):
    rv = client.get("/api/entitlement/capacity-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    cur = ent.get_entitlement()
    assert body["grace"] is bool(cur.grace)
    assert body["enforced"] is False


def test_api_excludes_trial(client, ent):
    rv = client.get("/api/entitlement/capacity-diff-batch")
    body = rv.get_json()
    ids = {row["target"] for row in body["tiers"]}
    assert ent.TIER_TRIAL not in ids


def test_api_returns_200_envelope_on_resolver_failure(monkeypatch, client):
    # Force the resolver path used by the route to blow up; the route
    # must still return a 200 with the grace-shape envelope so the
    # pricing page keeps rendering instead of erroring out.
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "capacity_diff_batch", boom)
    rv = client.get("/api/entitlement/capacity-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
