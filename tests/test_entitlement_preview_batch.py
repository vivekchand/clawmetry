"""Tests for ``clawmetry.entitlements.preview_batch`` +
``GET /api/entitlement/preview-batch``.

Plural sibling of :func:`preview`. Where the singular helper answers
"what would the resulting Entitlement *look like* at tier X" one tier at
a time, the batch returns the same denormalised row for every entry in
``_PURCHASABLE_TIERS`` so a pricing-page table can render the full
cumulative-state column off **one** round-trip. Cumulative-state
companion to :func:`tier_unlocks_batch` (marginal grant per rung) and
:func:`tier_locks_batch` (marginal loss per rung) -- pair the three to
render a pricing table without client-side composition. These tests
pin the contract:

  - returns one row per purchasable tier in ``(rank, id)`` order
  - each row matches the singular ``preview(tier)`` output exactly
    (``source="preview"``, ``grace=False``, full ``to_dict`` shape)
  - trial is excluded (mirrors the singular helper's posture)
  - row order is byte-stable with ``tier_unlocks_batch`` /
    ``tier_locks_batch`` so a three-column pricing table lines up
    rung-for-rung without client-side re-sort
  - per-tier capacity (channel_limit, retention_days) surfaces because
    every row is rendered with ``grace=False`` -- a grace-mode preview
    would zero those out and defeat the purpose
  - never raises -- a resolver failure short-circuits to ``[]``
  - the wrapper endpoint always returns a 200 with the grace envelope
    so the pricing-page UI keeps rendering even when the resolver is
    sick
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # preview_batch() is grace-independent -- every row renders enforced
    # limits -- but match every other entitlement fixture in the suite so
    # the test env stays identical.
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
    rows = ent.preview_batch()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_full_to_dict_shape(ent):
    # The whole point is that every batch row matches what
    # /api/entitlement/preview returns -- pin the contract so a future
    # to_dict() key add/remove trips loudly here.
    expected = set(ent._build(ent.TIER_CLOUD_PRO, "preview").to_dict().keys())
    for row in ent.preview_batch():
        assert set(row.keys()) == expected


def test_excludes_trial(ent):
    rows = ent.preview_batch()
    ids = {row["tier"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier(ent):
    rows = ent.preview_batch()
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


# -- ordering -------------------------------------------------------------


def test_sorted_by_rank_ascending(ent):
    rows = ent.preview_batch()
    ranks = [row["tier_rank"] for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_tier_ids_sorted(ent):
    # Within a rank cluster (e.g. TIER_CLOUD_PRO + TIER_PRO at rank 2)
    # rows must be ordered by tier id so the response is byte-stable
    # across calls -- a UI rendering a fixed-key list wants no churn.
    rows = ent.preview_batch()
    by_rank: dict = {}
    for row in rows:
        by_rank.setdefault(row["tier_rank"], []).append(row["tier"])
    for rank, ids in by_rank.items():
        assert ids == sorted(ids), f"rank {rank} ids not sorted: {ids}"


def test_stable_across_calls(ent):
    first = ent.preview_batch()
    second = ent.preview_batch()
    assert first == second


def test_row_order_matches_tier_unlocks_batch(ent):
    # The three batches must walk ``_PURCHASABLE_TIERS`` in the same
    # ``(rank, id)`` order so a "what's at X / what's new at X / what
    # you'd give up at X" three-column matrix lines up rung-for-rung
    # without client-side re-sort.
    preview_ids = [row["tier"] for row in ent.preview_batch()]
    unlock_ids = [row["tier"] for row in ent.tier_unlocks_batch()]
    assert preview_ids == unlock_ids


def test_row_order_matches_tier_locks_batch(ent):
    # Round-trip mirror of the unlocks pin: the cumulative + marginal-loss
    # batches walk the ladder in the same order so a downgrade-warning
    # column on the pricing table lines up rung-for-rung with the
    # cumulative-state column above it.
    preview_ids = [row["tier"] for row in ent.preview_batch()]
    lock_ids = [row["tier"] for row in ent.tier_locks_batch()]
    assert preview_ids == lock_ids


# -- parity with singular helper ------------------------------------------


def test_each_row_equals_singular_call(ent):
    # Every row must be byte-identical to ``preview(tier)`` -- the batch
    # is a pure plural sibling, not a divergent path.
    for row in ent.preview_batch():
        assert row == ent.preview(row["tier"])


def test_every_row_is_source_preview(ent):
    # The UI must be able to tell a preview from a live entitlement -- if
    # a batch row ever leaked into the live state surface it would
    # silently over-grant. The "preview" source is the trip-wire (same
    # posture the singular helper pins).
    for row in ent.preview_batch():
        assert row["source"] == "preview"


def test_every_row_is_not_grace(ent, monkeypatch):
    # Grace zeroes out channel_limit / retention_days, which defeats the
    # purpose of a preview ("show concrete numbers"). Force grace ON in
    # the environment and verify every batch row still renders enforced
    # limits.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    for row in ent.preview_batch():
        assert row["grace"] is False
        assert row["enforced"] is True


# -- per-tier limits ------------------------------------------------------


def test_oss_row_has_free_caps(ent):
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    oss = by_id[ent.TIER_OSS]
    assert oss["retention_days"] == 7
    assert oss["channel_limit"] == ent._FREE_CHANNEL_LIMIT
    # OSS doesn't unlock any paid runtimes.
    assert set(oss["runtimes"]) == set(ent.FREE_RUNTIMES)


def test_starter_row_unlocks_paid_runtimes(ent):
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    starter = by_id[ent.TIER_CLOUD_STARTER]
    assert starter["retention_days"] == 30
    assert starter["channel_limit"] is None  # unlimited
    assert set(starter["runtimes"]) == set(ent.ALL_RUNTIMES)


def test_cloud_pro_row_caps(ent):
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    pro = by_id[ent.TIER_CLOUD_PRO]
    assert pro["retention_days"] == 90
    assert pro["channel_limit"] is None
    assert set(pro["features"]) == set(ent.FREE_FEATURES) | set(ent.PAID_FEATURES)


def test_enterprise_row_includes_enterprise_features(ent):
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    enterprise = by_id[ent.TIER_ENTERPRISE]
    assert enterprise["retention_days"] is None  # unlimited
    expected = (
        set(ent.FREE_FEATURES)
        | set(ent.PAID_FEATURES)
        | set(ent.ENTERPRISE_FEATURES)
    )
    assert set(enterprise["features"]) == expected


# -- locked_* shows nothing at higher tiers -------------------------------


def test_pro_row_has_no_locked_runtimes(ent):
    # In a Pro preview every paid runtime is unlocked -- locked_runtimes
    # is the inverse view and must therefore be empty so the CTA card
    # doesn't show ghost "still locked" rows.
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    assert by_id[ent.TIER_CLOUD_PRO]["locked_runtimes"] == []


def test_enterprise_row_has_no_locked_features(ent):
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    assert by_id[ent.TIER_ENTERPRISE]["locked_features"] == []


# -- same-rank symmetry ---------------------------------------------------


def test_same_rank_siblings_have_identical_grant(ent):
    # cloud_free / oss (rank 0) and cloud_pro / pro (rank 2) both
    # produce identical grants -- same feature set, same runtime set.
    # The denormalised preview row carries source-level differences
    # (tier id, tier_label, source) but the cumulative grant must match.
    by_id = {row["tier"]: row for row in ent.preview_batch()}
    for a_id, b_id in (
        (ent.TIER_OSS, ent.TIER_CLOUD_FREE),
        (ent.TIER_CLOUD_PRO, ent.TIER_PRO),
    ):
        a, b = by_id[a_id], by_id[b_id]
        assert set(a["features"]) == set(b["features"])
        assert set(a["runtimes"]) == set(b["runtimes"])


# -- invariants -----------------------------------------------------------


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.preview_batch()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "preview", boom)
    # Helper swallows the failure and returns [] -- never propagates.
    assert ent.preview_batch() == []


# -- API surface ----------------------------------------------------------


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/preview-batch")
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
    rv = client.get("/api/entitlement/preview-batch")
    assert rv.status_code == 200
    ids = {row["tier"] for row in rv.get_json()["tiers"]}
    assert ent.TIER_TRIAL not in ids
    assert ent.TIER_OSS in ids
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_ENTERPRISE in ids


def test_api_rows_match_singular_endpoint(client, ent):
    rv = client.get("/api/entitlement/preview-batch")
    assert rv.status_code == 200
    for row in rv.get_json()["tiers"]:
        single = client.get(
            f"/api/entitlement/preview?tier={row['tier']}"
        )
        assert single.status_code == 200
        assert single.get_json() == row


def test_api_envelope_reports_grace_in_oss_default(client):
    rv = client.get("/api/entitlement/preview-batch")
    body = rv.get_json()
    # OSS-free default is grace=True, enforced=False, tier="oss" -- the
    # envelope is the same shape the tier_unlocks_batch /
    # tier_locks_batch endpoints emit.
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_row_order_matches_tier_unlocks_batch(client):
    # HTTP-level mirror of the helper-level pin: pricing-table consumers
    # expect preview[i], unlocks[i], and locks[i] to describe the same
    # rung.
    preview = client.get("/api/entitlement/preview-batch").get_json()
    unlocks = client.get("/api/entitlement/tier-unlocks-batch").get_json()
    preview_ids = [row["tier"] for row in preview["tiers"]]
    unlock_ids = [row["tier"] for row in unlocks["tiers"]]
    assert preview_ids == unlock_ids


def test_api_row_order_matches_tier_locks_batch(client):
    preview = client.get("/api/entitlement/preview-batch").get_json()
    locks = client.get("/api/entitlement/tier-locks-batch").get_json()
    preview_ids = [row["tier"] for row in preview["tiers"]]
    lock_ids = [row["tier"] for row in locks["tiers"]]
    assert preview_ids == lock_ids


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    # Mirror the never-5xx posture: if the resolver raises the wrapper
    # short-circuits to the grace envelope with an empty tiers list so
    # the pricing-page UI keeps rendering instead of breaking.
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(e, "preview_batch", boom)
    rv = client.get("/api/entitlement/preview-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
