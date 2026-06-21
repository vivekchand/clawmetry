"""Tests for ``clawmetry.entitlements.tier_unlocks_batch`` +
``GET /api/entitlement/tier-unlocks-batch``.

Plural sibling of :func:`tier_unlocks`. Where the singular helper
answers "what does *this* tier first unlock vs the tier below it" one
tier at a time, the batch returns the same row shape for every entry in
``_PURCHASABLE_TIERS`` so a pricing-page table can render the full
"what's new in X" column off **one** round-trip. These tests pin the
contract:

  - returns one row per purchasable tier in rank order
  - each row matches the singular ``tier_unlocks(tier)`` output exactly
  - trial is excluded (mirrors the singular helper's posture)
  - never raises -- a resolver failure short-circuits to ``[]``
  - the wrapper endpoint always returns a 200 with the grace envelope
    so the pricing page keeps rendering even when the resolver is sick
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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── shape ─────────────────────────────────────────────────────────────────


def test_returns_list(ent):
    rows = ent.tier_unlocks_batch()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_singular_shape(ent):
    rows = ent.tier_unlocks_batch()
    expected = {
        "tier",
        "tier_label",
        "tier_rank",
        "previous_tier",
        "previous_tier_label",
        "previous_tier_rank",
        "features",
        "runtimes",
    }
    for row in rows:
        assert set(row.keys()) == expected


def test_excludes_trial(ent):
    rows = ent.tier_unlocks_batch()
    ids = {row["tier"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier(ent):
    rows = ent.tier_unlocks_batch()
    ids = {row["tier"] for row in rows}
    # Mirror the entitlements module's purchasable set verbatim. If the
    # set ever changes (new tier added / TIER_PRO removed) this trips so
    # the pricing-page row coverage stays in sync.
    expected = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert ids == expected


# ── ordering ──────────────────────────────────────────────────────────────


def test_sorted_by_rank_ascending(ent):
    rows = ent.tier_unlocks_batch()
    ranks = [row["tier_rank"] for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_tier_ids_sorted(ent):
    # Within a rank cluster (e.g. TIER_CLOUD_PRO + TIER_PRO at rank 2)
    # rows must be ordered by tier id so the response is byte-stable
    # across calls -- a UI rendering a fixed-key list wants no churn.
    rows = ent.tier_unlocks_batch()
    by_rank: dict = {}
    for row in rows:
        by_rank.setdefault(row["tier_rank"], []).append(row["tier"])
    for rank, ids in by_rank.items():
        assert ids == sorted(ids), f"rank {rank} ids not sorted: {ids}"


def test_stable_across_calls(ent):
    first = ent.tier_unlocks_batch()
    second = ent.tier_unlocks_batch()
    assert first == second


# ── parity with singular helper ───────────────────────────────────────────


def test_each_row_equals_singular_call(ent):
    # Every row must be byte-identical to ``tier_unlocks(tier)`` -- the
    # batch is a pure plural sibling, not a divergent path.
    for row in ent.tier_unlocks_batch():
        assert row == ent.tier_unlocks(row["tier"])


def test_floor_tiers_have_no_previous(ent):
    rows = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert rows[floor]["previous_tier"] is None
        assert rows[floor]["previous_tier_label"] is None
        assert rows[floor]["previous_tier_rank"] is None


def test_starter_row_unlocks_paid_runtimes(ent):
    rows = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    starter = rows[ent.TIER_CLOUD_STARTER]
    assert starter["previous_tier"] == ent.TIER_OSS
    assert set(starter["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_pro_row_unlocks_pro_only_features(ent):
    rows = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    pro = rows[ent.TIER_CLOUD_PRO]
    assert pro["previous_tier"] == ent.TIER_CLOUD_STARTER
    assert set(pro["features"]) == set(ent.PRO_ONLY_FEATURES)
    assert pro["runtimes"] == []


def test_enterprise_row_unlocks_enterprise_features(ent):
    rows = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    ent_row = rows[ent.TIER_ENTERPRISE]
    assert ent_row["previous_tier"] == ent.TIER_CLOUD_PRO
    assert set(ent_row["features"]) == set(ent.ENTERPRISE_FEATURES)


# ── invariants ────────────────────────────────────────────────────────────


def test_marginals_union_covers_paid_features(ent):
    # Every paid + enterprise feature must first-unlock at exactly one
    # row -- the pricing page needs gapless coverage.
    seen: set = set()
    for row in ent.tier_unlocks_batch():
        seen |= set(row["features"])
    # FREE_FEATURES are folded into the floor-tier rows (TIER_OSS /
    # TIER_CLOUD_FREE) so they show up in `seen` too; the union with
    # PAID + ENTERPRISE covers the full ALL_FEATURES set.
    assert set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES) <= seen


def test_marginal_paid_features_disjoint_across_distinct_ranks(ent):
    # A paid feature must first-unlock at exactly *one* rank. Same-rank
    # rows (CLOUD_PRO + PRO) share their marginal so we collapse the
    # check to per-rank sets.
    by_rank: dict = {}
    for row in ent.tier_unlocks_batch():
        by_rank.setdefault(row["tier_rank"], set()).update(row["features"])
    # Subtract the free grant once -- it appears on every rank-0 row.
    by_rank[0] -= set(ent.FREE_FEATURES)
    ranks = sorted(by_rank.keys())
    for i, ri in enumerate(ranks):
        for rj in ranks[i + 1 :]:
            assert by_rank[ri].isdisjoint(
                by_rank[rj]
            ), f"feature overlap between rank {ri} and rank {rj}"


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tier_unlocks_batch()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "tier_unlocks", boom)
    # Helper swallows the failure and returns [] -- never propagates.
    assert ent.tier_unlocks_batch() == []


# ── API surface ───────────────────────────────────────────────────────────


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/tier-unlocks-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "tiers",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert isinstance(body["tiers"], list)


def test_api_returns_one_row_per_purchasable_tier(client, ent):
    rv = client.get("/api/entitlement/tier-unlocks-batch")
    assert rv.status_code == 200
    ids = {row["tier"] for row in rv.get_json()["tiers"]}
    assert ent.TIER_TRIAL not in ids
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_CLOUD_PRO in ids
    assert ent.TIER_ENTERPRISE in ids


def test_api_rows_match_singular_endpoint(client, ent):
    rv = client.get("/api/entitlement/tier-unlocks-batch")
    assert rv.status_code == 200
    for row in rv.get_json()["tiers"]:
        single = client.get(
            f"/api/entitlement/tier-unlocks?tier={row['tier']}"
        )
        assert single.status_code == 200
        assert single.get_json() == row


def test_api_envelope_reports_grace_in_oss_default(client):
    rv = client.get("/api/entitlement/tier-unlocks-batch")
    body = rv.get_json()
    # OSS-free default is grace=True, enforced=False, tier="oss" -- the
    # envelope is the same shape the lock-reason-batch endpoint emits.
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    # Mirror the never-5xx posture: if the resolver raises the wrapper
    # short-circuits to the grace envelope with an empty tiers list so
    # the pricing-page UI keeps rendering instead of breaking.
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(e, "tier_unlocks_batch", boom)
    rv = client.get("/api/entitlement/tier-unlocks-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
