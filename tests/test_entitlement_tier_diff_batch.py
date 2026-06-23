"""Tests for ``clawmetry.entitlements.tier_diff_batch`` +
``GET /api/entitlement/tier-diff-batch``.

Plural sibling of :func:`tier_diff` and the "all-slices-in-one-row"
member of the batch family alongside :func:`tier_unlocks_batch`
(feature/runtime grant slice), :func:`tier_locks_batch` (feature/
runtime loss slice) and :func:`capacity_diff_batch` (capacity slice).
Where each of those siblings carries a single slice of the per-rung
transition, ``tier_diff_batch`` carries ALL slices in one row so a
pricing-page table can render the full marginal column off ONE
round-trip. These tests pin the contract:

  - returns one row per purchasable tier in ``(rank, id)`` order
  - each row matches the singular ``tier_diff(prev_purchasable, tier)``
    output exactly (floor row collapses to ``tier_diff(tid, tid)``)
  - trial is excluded (mirrors the other batches' posture)
  - non-floor rows are byte-stable with ``tier_unlocks_batch`` (the
    feature/runtime grant slice byte-equals)
  - non-floor rows are byte-stable with the per-rung capacity steps
    in ``capacity_diff_path(TIER_OSS, TIER_ENTERPRISE)``
  - decoupled from the resolver: grace vs enforce yields identical rows
  - never raises -- a resolver failure short-circuits to ``[]``
  - the wrapper endpoint always returns 200 with the grace envelope
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
    rows = ent.tier_diff_batch()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_singular_shape(ent):
    rows = ent.tier_diff_batch()
    expected = {
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
    for row in rows:
        assert set(row.keys()) == expected


def test_each_row_capacity_axes_complete(ent):
    rows = ent.tier_diff_batch()
    expected = {"channel_limit", "retention_days", "node_limit"}
    for row in rows:
        assert set(row["capacity_changes"].keys()) == expected
        for axis in expected:
            triple = row["capacity_changes"][axis]
            assert set(triple.keys()) == {
                "before",
                "after",
                "delta",
                "unlocked",
                "locked",
            }


def test_excludes_trial(ent):
    rows = ent.tier_diff_batch()
    ids = {row["to"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier(ent):
    rows = ent.tier_diff_batch()
    ids = {row["to"] for row in rows}
    # Mirror the entitlements module's purchasable set verbatim. If the
    # set ever changes (new tier added / a tier removed) this trips so
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
    rows = ent.tier_diff_batch()
    ranks = [row["to_rank"] for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_tier_ids_sorted(ent):
    # Within a rank cluster (e.g. TIER_CLOUD_PRO + TIER_PRO at rank 2)
    # rows must be ordered by tier id so the response is byte-stable
    # across calls -- a UI rendering a fixed-key list wants no churn.
    rows = ent.tier_diff_batch()
    by_rank: dict = {}
    for row in rows:
        by_rank.setdefault(row["to_rank"], []).append(row["to"])
    for rank, ids in by_rank.items():
        assert ids == sorted(ids), f"rank {rank} ids not sorted: {ids}"


def test_stable_across_calls(ent):
    first = ent.tier_diff_batch()
    second = ent.tier_diff_batch()
    assert first == second


def test_row_order_matches_sibling_batches(ent):
    # The five batches must walk _PURCHASABLE_TIERS in the same (rank, id)
    # order so a pricing-page can line them up rung-for-rung off ONE
    # client-side join without client-side re-sort.
    diff_ids = [row["to"] for row in ent.tier_diff_batch()]
    unlocks_ids = [row["tier"] for row in ent.tier_unlocks_batch()]
    locks_ids = [row["tier"] for row in ent.tier_locks_batch()]
    capacity_ids = [row["target"] for row in ent.capacity_diff_batch()]
    preview_ids = [row["tier"] for row in ent.preview_batch()]
    assert diff_ids == unlocks_ids == locks_ids == preview_ids
    # capacity_diff_batch anchors against the resolved entitlement (not
    # adjacent rungs) so its row identifiers still walk the same set in
    # the same order even though its diff content has a different anchor.
    assert diff_ids == capacity_ids


# ── parity with singular helper ───────────────────────────────────────────


def test_each_row_equals_singular_tier_diff(ent):
    # Every row must be byte-identical to ``tier_diff(prev, this)`` for
    # the next-lower purchasable tier, or ``tier_diff(this, this)`` at
    # the floor. The batch is a pure plural sibling, not a divergent
    # path -- if these drift apart the pricing-page UI starts seeing
    # different shapes off the singular vs the batch endpoint. The
    # prev-purchasable resolution mirrors :func:`tier_unlocks` exactly:
    # walk :data:`_PURCHASABLE_TIERS` in tuple order, take the first
    # candidate at each higher rank below the target -- so same-rank
    # rank-0 siblings (TIER_OSS / TIER_CLOUD_FREE) and rank-2 siblings
    # (TIER_CLOUD_PRO / TIER_PRO) resolve to the same anchor the
    # unlocks batch already pins.
    for row in ent.tier_diff_batch():
        tid = row["to"]
        target_rank = ent._TIER_RANK.get(tid, -1)
        prev_id = None
        prev_rank_seen = -1
        for cand in ent._PURCHASABLE_TIERS:
            cand_rank = ent._TIER_RANK.get(cand, -1)
            if 0 <= cand_rank < target_rank and cand_rank > prev_rank_seen:
                prev_id = cand
                prev_rank_seen = cand_rank
        anchor = prev_id if prev_id is not None else tid
        assert row == ent.tier_diff(anchor, tid)


def test_floor_rows_are_identity(ent):
    rows = {row["to"]: row for row in ent.tier_diff_batch()}
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        r = rows[floor]
        assert r["from"] == floor
        assert r["to"] == floor
        assert r["direction"] == "identity"
        assert r["added_features"] == []
        assert r["lost_features"] == []
        assert r["added_runtimes"] == []
        assert r["lost_runtimes"] == []
        for axis in ("channel_limit", "retention_days", "node_limit"):
            triple = r["capacity_changes"][axis]
            assert triple["before"] == triple["after"]
            assert triple["delta"] in (0, None)
            assert triple["unlocked"] is False
            assert triple["locked"] is False


def test_starter_row_anchored_on_oss(ent):
    rows = {row["to"]: row for row in ent.tier_diff_batch()}
    starter = rows[ent.TIER_CLOUD_STARTER]
    assert starter["from"] == ent.TIER_OSS
    assert starter["direction"] == "upgrade"
    # Starter first unlocks the paid runtimes (the entire PAID_RUNTIMES
    # set lights up at rank 1 since OSS / Cloud Free have none of them).
    assert set(starter["added_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_pro_row_anchored_on_starter(ent):
    rows = {row["to"]: row for row in ent.tier_diff_batch()}
    pro = rows[ent.TIER_CLOUD_PRO]
    assert pro["from"] == ent.TIER_CLOUD_STARTER
    assert pro["direction"] == "upgrade"
    assert set(pro["added_features"]) == set(ent.PRO_ONLY_FEATURES)
    assert pro["added_runtimes"] == []


def test_enterprise_row_anchored_on_pro(ent):
    rows = {row["to"]: row for row in ent.tier_diff_batch()}
    ent_row = rows[ent.TIER_ENTERPRISE]
    # Enterprise's anchor is the highest-rank purchasable below it. Pro
    # + Cloud Pro share rank 2 so the anchor is the alphabetically-first
    # of them (cloud_pro) -- mirrors the tie-break the unlocks/locks
    # batches use.
    assert ent_row["from"] == ent.TIER_CLOUD_PRO
    assert ent_row["direction"] == "upgrade"
    assert set(ent_row["added_features"]) == set(ent.ENTERPRISE_FEATURES)


# ── byte-stability with sibling batches ───────────────────────────────────


def test_added_features_byte_equals_unlocks_batch(ent):
    # The per-rung ``added_features`` slice must byte-equal the
    # corresponding ``features`` slice in :func:`tier_unlocks_batch` for
    # every non-floor row (both anchor on prev-lower-purchasable). The
    # floor rows diverge because tier_unlocks_batch collapses to the
    # full free grant at the floor while tier_diff_batch collapses to
    # identity -- documented and pinned separately above.
    diff_rows = {row["to"]: row for row in ent.tier_diff_batch()}
    unlocks_rows = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    for tid, drow in diff_rows.items():
        if drow["from"] == drow["to"]:
            continue  # floor row
        urow = unlocks_rows[tid]
        assert drow["added_features"] == urow["features"], tid
        assert drow["added_runtimes"] == urow["runtimes"], tid


def test_capacity_changes_after_matches_tier_caps(ent):
    # Each non-floor row's per-axis ``after`` value must byte-equal the
    # static cap for the ``to`` tier on every capacity axis -- the cap
    # at the destination rung is the cap, regardless of which neighbor
    # the row anchors against. Pinned so a future reshuffle of the tier
    # cap maps surfaces here instead of silently desyncing the row.
    for row in ent.tier_diff_batch():
        tid = row["to"]
        if row["from"] == row["to"]:
            continue  # floor row collapses to identity
        assert (
            row["capacity_changes"]["channel_limit"]["after"]
            == ent._TIER_CHANNEL_LIMIT.get(tid, ent._FREE_CHANNEL_LIMIT)
        ), tid
        assert (
            row["capacity_changes"]["retention_days"]["after"]
            == ent._TIER_RETENTION_DAYS.get(tid, 7)
        ), tid
        assert (
            row["capacity_changes"]["node_limit"]["after"]
            == ent._TIER_NODE_LIMIT.get(tid, ent._FREE_NODE_LIMIT)
        ), tid


def test_ascending_direction_means_no_losses(ent):
    # Every non-floor row anchors prev-lower -> this so the direction is
    # always "upgrade" and the marginal-loss slices are empty by
    # construction (you can't lose anything climbing up).
    for row in ent.tier_diff_batch():
        if row["from"] == row["to"]:
            continue  # floor row, direction == "identity"
        assert row["direction"] == "upgrade"
        assert row["lost_features"] == []
        assert row["lost_runtimes"] == []


# ── invariants ────────────────────────────────────────────────────────────


def test_marginals_union_covers_paid_features(ent):
    # Every paid + enterprise feature must first-unlock at exactly one
    # row -- the pricing page needs gapless coverage.
    seen: set = set()
    for row in ent.tier_diff_batch():
        seen |= set(row["added_features"])
    assert set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES) <= seen


def test_marginal_paid_features_disjoint_across_distinct_ranks(ent):
    # A paid feature must first-unlock at exactly one rank. Same-rank
    # rows (CLOUD_PRO + PRO) share their marginal so we collapse the
    # check to per-rank sets.
    by_rank: dict = {}
    for row in ent.tier_diff_batch():
        by_rank.setdefault(row["to_rank"], set()).update(row["added_features"])
    ranks = sorted(by_rank.keys())
    for i, ri in enumerate(ranks):
        for rj in ranks[i + 1 :]:
            assert by_rank[ri].isdisjoint(
                by_rank[rj]
            ), f"feature overlap between rank {ri} and rank {rj}"


def test_decoupled_from_resolver_grace_vs_enforce(monkeypatch, ent):
    # The helper walks the static per-tier maps, NOT the resolved
    # entitlement, so toggling enforce-mode must not perturb the rows.
    rows_grace = ent.tier_diff_batch()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        rows_enforce = e.tier_diff_batch()
        assert rows_grace == rows_enforce
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tier_diff_batch()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "tier_diff", boom)
    # Helper swallows the failure and returns [] -- never propagates.
    assert ent.tier_diff_batch() == []


# ── API surface ───────────────────────────────────────────────────────────


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/tier-diff-batch")
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
    rv = client.get("/api/entitlement/tier-diff-batch")
    assert rv.status_code == 200
    ids = {row["to"] for row in rv.get_json()["tiers"]}
    assert ent.TIER_TRIAL not in ids
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_CLOUD_PRO in ids
    assert ent.TIER_ENTERPRISE in ids


def test_api_rows_match_singular_endpoint(client, ent):
    # Each row in the batch must byte-equal the singular ``/tier-diff``
    # endpoint for the same ``(prev_purchasable, this)`` pair (or
    # ``(this, this)`` at the floor). prev_purchasable resolution
    # mirrors :func:`tier_unlocks` byte-for-byte: walk
    # :data:`_PURCHASABLE_TIERS` in tuple order, taking the first
    # candidate at each higher rank below the target.
    rv = client.get("/api/entitlement/tier-diff-batch")
    assert rv.status_code == 200
    for row in rv.get_json()["tiers"]:
        tid = row["to"]
        target_rank = ent._TIER_RANK.get(tid, -1)
        prev_id = None
        prev_rank_seen = -1
        for cand in ent._PURCHASABLE_TIERS:
            cand_rank = ent._TIER_RANK.get(cand, -1)
            if 0 <= cand_rank < target_rank and cand_rank > prev_rank_seen:
                prev_id = cand
                prev_rank_seen = cand_rank
        anchor = prev_id if prev_id is not None else tid
        single = client.get(
            f"/api/entitlement/tier-diff?from={anchor}&to={tid}"
        )
        assert single.status_code == 200
        assert single.get_json() == row


def test_api_envelope_reports_grace_in_oss_default(client):
    rv = client.get("/api/entitlement/tier-diff-batch")
    body = rv.get_json()
    # OSS-free default is grace=True, enforced=False, tier="oss" -- the
    # envelope is the same shape the sibling batch endpoints emit.
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

    monkeypatch.setattr(e, "tier_diff_batch", boom)
    rv = client.get("/api/entitlement/tier-diff-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }


def test_api_row_order_matches_unlocks_batch(client):
    # The five batch endpoints must emit rows in the same (rank, id)
    # order so a pricing-page UI can join them row-for-row off ONE
    # client-side parallel-fetch without client-side re-sort.
    diff = client.get("/api/entitlement/tier-diff-batch").get_json()
    unlocks = client.get("/api/entitlement/tier-unlocks-batch").get_json()
    assert [row["to"] for row in diff["tiers"]] == [
        row["tier"] for row in unlocks["tiers"]
    ]


def test_api_garbage_query_never_5xxs(client):
    # Spray a few garbage querystrings and confirm the wrapper never
    # propagates a 5xx -- the grace-envelope fallback is the contract.
    for qs in (
        "?from=&to=",
        "?nonsense=1",
        "?tier=does-not-exist",
        "?from=oss&to=enterprise",
    ):
        rv = client.get("/api/entitlement/tier-diff-batch" + qs)
        assert rv.status_code == 200, qs
