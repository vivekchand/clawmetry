"""Tests for ``clawmetry.entitlements.tier_locks_batch`` +
``GET /api/entitlement/tier-locks-batch``.

Plural sibling of :func:`tier_locks`. Where the singular helper answers
"what does *this* tier first lose vs the tier above it" one tier at a
time, the batch returns the same row shape for every entry in
``_PURCHASABLE_TIERS`` so a downgrade-warning matrix can render the full
"what you'd give up at X" column off **one** round-trip. Marginal-loss
companion to :func:`tier_unlocks_batch` -- pair the two to render the
upgrade-CTA + downgrade-warning columns of a pricing table without
client-side composition. These tests pin the contract:

  - returns one row per purchasable tier in rank order
  - each row matches the singular ``tier_locks(tier)`` output exactly
  - trial is excluded (mirrors the singular helper's posture)
  - never raises -- a resolver failure short-circuits to ``[]``
  - the wrapper endpoint always returns a 200 with the grace envelope
    so the downgrade-warning surface keeps rendering even when the
    resolver is sick
  - byte-stable ordering with ``tier_unlocks_batch`` so an "if you stay /
    if you drop" two-tone matrix lines up rung-for-rung without client
    re-sort
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


# -- shape ----------------------------------------------------------------


def test_returns_list(ent):
    rows = ent.tier_locks_batch()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_singular_shape(ent):
    rows = ent.tier_locks_batch()
    expected = {
        "tier",
        "tier_label",
        "tier_rank",
        "next_tier",
        "next_tier_label",
        "next_tier_rank",
        "lost_features",
        "lost_runtimes",
    }
    for row in rows:
        assert set(row.keys()) == expected


def test_excludes_trial(ent):
    rows = ent.tier_locks_batch()
    ids = {row["tier"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier(ent):
    rows = ent.tier_locks_batch()
    ids = {row["tier"] for row in rows}
    # Mirror the entitlements module's purchasable set verbatim. If the
    # set ever changes (new tier added / TIER_PRO removed) this trips so
    # the downgrade-warning row coverage stays in sync.
    expected = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert ids == expected


# -- ordering -------------------------------------------------------------


def test_sorted_by_rank_ascending(ent):
    rows = ent.tier_locks_batch()
    ranks = [row["tier_rank"] for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_tier_ids_sorted(ent):
    # Within a rank cluster (e.g. TIER_CLOUD_PRO + TIER_PRO at rank 2)
    # rows must be ordered by tier id so the response is byte-stable
    # across calls -- a UI rendering a fixed-key list wants no churn.
    rows = ent.tier_locks_batch()
    by_rank: dict = {}
    for row in rows:
        by_rank.setdefault(row["tier_rank"], []).append(row["tier"])
    for rank, ids in by_rank.items():
        assert ids == sorted(ids), f"rank {rank} ids not sorted: {ids}"


def test_stable_across_calls(ent):
    first = ent.tier_locks_batch()
    second = ent.tier_locks_batch()
    assert first == second


def test_row_order_matches_tier_unlocks_batch(ent):
    # The two batches must walk ``_PURCHASABLE_TIERS`` in the same
    # ``(rank, id)`` order so a downgrade/upgrade two-tone matrix lines
    # up rung-for-rung without client-side re-sort.
    lock_ids = [row["tier"] for row in ent.tier_locks_batch()]
    unlock_ids = [row["tier"] for row in ent.tier_unlocks_batch()]
    assert lock_ids == unlock_ids


# -- parity with singular helper ------------------------------------------


def test_each_row_equals_singular_call(ent):
    # Every row must be byte-identical to ``tier_locks(tier)`` -- the
    # batch is a pure plural sibling, not a divergent path.
    for row in ent.tier_locks_batch():
        assert row == ent.tier_locks(row["tier"])


def test_enterprise_row_has_no_next_tier(ent):
    rows = {row["tier"]: row for row in ent.tier_locks_batch()}
    enterprise = rows[ent.TIER_ENTERPRISE]
    assert enterprise["next_tier"] is None
    assert enterprise["next_tier_label"] is None
    assert enterprise["next_tier_rank"] is None
    assert enterprise["lost_features"] == []
    assert enterprise["lost_runtimes"] == []


def test_oss_row_loses_starter_grant(ent):
    rows = {row["tier"]: row for row in ent.tier_locks_batch()}
    oss = rows[ent.TIER_OSS]
    assert oss["next_tier"] == ent.TIER_CLOUD_STARTER
    assert set(oss["lost_features"]) == set(ent.STARTER_FEATURES)
    assert set(oss["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_starter_row_loses_pro_only_features(ent):
    rows = {row["tier"]: row for row in ent.tier_locks_batch()}
    starter = rows[ent.TIER_CLOUD_STARTER]
    assert starter["next_tier"] == ent.TIER_CLOUD_PRO
    assert set(starter["lost_features"]) == set(ent.PRO_ONLY_FEATURES)
    assert starter["lost_runtimes"] == []


def test_pro_rows_lose_enterprise_features(ent):
    rows = {row["tier"]: row for row in ent.tier_locks_batch()}
    for tid in (ent.TIER_CLOUD_PRO, ent.TIER_PRO):
        row = rows[tid]
        assert row["next_tier"] == ent.TIER_ENTERPRISE
        assert set(row["lost_features"]) == set(ent.ENTERPRISE_FEATURES)
        assert row["lost_runtimes"] == []


# -- set-identity vs tier_unlocks_batch -----------------------------------


def test_loss_at_X_equals_unlock_at_next(ent):
    # The marginal-loss row at X must byte-equal the marginal-unlock row
    # at the next-higher purchasable tier above X, for the same
    # features/runtimes set difference. Pinned at the batch level so
    # both views can be wired off one round-trip pair without drift.
    unlocks_by_tier = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    for row in ent.tier_locks_batch():
        nxt = row["next_tier"]
        if nxt is None:
            # Enterprise: no rung above, set-identity vacuously empty.
            assert row["lost_features"] == []
            assert row["lost_runtimes"] == []
            continue
        unlock = unlocks_by_tier[nxt]
        assert row["lost_features"] == unlock["features"]
        assert row["lost_runtimes"] == unlock["runtimes"]


# -- invariants -----------------------------------------------------------


def test_marginals_union_covers_paid_features(ent):
    # Every paid + enterprise feature must first-lock at exactly one row
    # -- the downgrade-warning column needs gapless coverage to match
    # the upgrade-CTA column's coverage in tier_unlocks_batch.
    seen: set = set()
    for row in ent.tier_locks_batch():
        seen |= set(row["lost_features"])
    assert set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES) <= seen


def test_marginal_losses_disjoint_across_distinct_ranks(ent):
    # A feature must first-lock at exactly *one* rank. Same-rank rows
    # (cloud_pro + pro) legitimately share their loss set so the
    # disjointness check is per-rank.
    by_rank: dict = {}
    for row in ent.tier_locks_batch():
        by_rank.setdefault(row["tier_rank"], set()).update(row["lost_features"])
    ranks = sorted(by_rank.keys())
    for i, ri in enumerate(ranks):
        for rj in ranks[i + 1:]:
            assert by_rank[ri].isdisjoint(
                by_rank[rj]
            ), f"feature overlap between rank {ri} and rank {rj}"


def test_same_rank_siblings_have_identical_loss(ent):
    # cloud_free / oss (rank 0) and cloud_pro / pro (rank 2) both
    # produce identical loss rows -- same next_tier, same lost_* lists.
    rows = {row["tier"]: row for row in ent.tier_locks_batch()}
    for a_id, b_id in (
        (ent.TIER_OSS, ent.TIER_CLOUD_FREE),
        (ent.TIER_CLOUD_PRO, ent.TIER_PRO),
    ):
        a, b = rows[a_id], rows[b_id]
        assert a["next_tier"] == b["next_tier"]
        assert a["lost_features"] == b["lost_features"]
        assert a["lost_runtimes"] == b["lost_runtimes"]


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tier_locks_batch()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "tier_locks", boom)
    # Helper swallows the failure and returns [] -- never propagates.
    assert ent.tier_locks_batch() == []


# -- API surface ----------------------------------------------------------


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/tier-locks-batch")
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
    rv = client.get("/api/entitlement/tier-locks-batch")
    assert rv.status_code == 200
    ids = {row["tier"] for row in rv.get_json()["tiers"]}
    assert ent.TIER_TRIAL not in ids
    assert ent.TIER_OSS in ids
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_ENTERPRISE in ids


def test_api_rows_match_singular_endpoint(client, ent):
    rv = client.get("/api/entitlement/tier-locks-batch")
    assert rv.status_code == 200
    for row in rv.get_json()["tiers"]:
        single = client.get(
            f"/api/entitlement/tier-locks?tier={row['tier']}"
        )
        assert single.status_code == 200
        assert single.get_json() == row


def test_api_envelope_reports_grace_in_oss_default(client):
    rv = client.get("/api/entitlement/tier-locks-batch")
    body = rv.get_json()
    # OSS-free default is grace=True, enforced=False, tier="oss" -- the
    # envelope is the same shape the tier_unlocks_batch endpoint emits.
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_row_order_matches_tier_unlocks_batch(client):
    # HTTP-level mirror of the helper-level pin: pricing-table consumers
    # expect locks[i] and unlocks[i] to describe the same rung.
    locks = client.get("/api/entitlement/tier-locks-batch").get_json()
    unlocks = client.get("/api/entitlement/tier-unlocks-batch").get_json()
    lock_ids = [row["tier"] for row in locks["tiers"]]
    unlock_ids = [row["tier"] for row in unlocks["tiers"]]
    assert lock_ids == unlock_ids


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    # Mirror the never-5xx posture: if the resolver raises the wrapper
    # short-circuits to the grace envelope with an empty tiers list so
    # the downgrade-warning UI keeps rendering instead of breaking.
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(e, "tier_locks_batch", boom)
    rv = client.get("/api/entitlement/tier-locks-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
