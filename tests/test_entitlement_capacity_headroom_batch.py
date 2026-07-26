"""Tests for :func:`clawmetry.entitlements.capacity_headroom_batch`.

Plural sibling of :func:`capacity_headroom_at`. Fills the ``_batch`` slot
on the capacity-headroom axis alongside :func:`capacity_diff_batch` and
the per-axis ``tiers_for_{channel_count,retention_window,node_count}_batch``
families.

Pins:
  * one row per purchasable tier, walked in ``(rank, id)`` order --
    byte-stable against :func:`capacity_diff_batch` /
    :func:`tier_unlocks_batch` / :func:`tier_locks_batch` so a pricing
    table lines up rung-for-rung without client-side re-sort
  * trial tier excluded (mirrors the other batches -- not purchasable)
  * each row is byte-identical to the singular
    :func:`capacity_headroom_at` for the same axis inputs
  * decoupled from the resolved entitlement (grace vs enforce yields
    byte-identical rows)
  * per-axis "None means unset" posture propagates to every row
  * never raises: a walker failure returns ``[]``
"""
from __future__ import annotations

import importlib

import pytest


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


# -- shape ---------------------------------------------------------------


def test_returns_list(enforced):
    assert isinstance(enforced.capacity_headroom_batch(channels=2), list)


def test_one_row_per_purchasable_tier(enforced):
    rows = enforced.capacity_headroom_batch(channels=2)
    assert len(rows) == len(enforced._PURCHASABLE_TIERS)


def test_trial_tier_excluded(enforced):
    tiers = {r["tier"] for r in enforced.capacity_headroom_batch(channels=2)}
    assert enforced.TIER_TRIAL not in tiers


def test_row_envelope_shape(enforced):
    rows = enforced.capacity_headroom_batch(
        channels=2, retention_days=5, nodes=1
    )
    for r in rows:
        assert set(r) == {
            "tier", "tier_label", "channels", "retention_days", "nodes",
        }


# -- ordering: (rank, id) --------------------------------------------------


def test_rows_ordered_by_rank_then_id(enforced):
    rows = enforced.capacity_headroom_batch(channels=2)
    seen = [(enforced._TIER_RANK.get(r["tier"], -1), r["tier"]) for r in rows]
    assert seen == sorted(seen)


def test_ordering_matches_capacity_diff_batch(enforced):
    diff_ids = [r["target"] for r in enforced.capacity_diff_batch()]
    headroom_ids = [
        r["tier"] for r in enforced.capacity_headroom_batch(channels=2)
    ]
    assert diff_ids == headroom_ids


# -- row parity with singular ---------------------------------------------


def test_each_row_matches_capacity_headroom_at(enforced):
    rows = enforced.capacity_headroom_batch(
        channels=2, retention_days=5, nodes=1
    )
    for r in rows:
        singular = enforced.capacity_headroom_at(
            r["tier"], channels=2, retention_days=5, nodes=1
        )
        assert r == singular


def test_unsupplied_axis_stays_none_on_every_row(enforced):
    rows = enforced.capacity_headroom_batch(channels=2)
    for r in rows:
        assert r["channels"] is not None
        assert r["retention_days"] is None
        assert r["nodes"] is None


def test_nothing_supplied_returns_all_none_rows(enforced):
    rows = enforced.capacity_headroom_batch()
    assert len(rows) == len(enforced._PURCHASABLE_TIERS)
    for r in rows:
        assert r["channels"] is None
        assert r["retention_days"] is None
        assert r["nodes"] is None


# -- concrete per-tier caps ------------------------------------------------


def _row_for(rows, tier):
    for r in rows:
        if r["tier"] == tier:
            return r
    raise AssertionError(f"tier {tier!r} missing from batch rows")


def test_oss_channels_row_uses_free_cap(enforced):
    rows = enforced.capacity_headroom_batch(channels=2)
    row = _row_for(rows, enforced.TIER_OSS)["channels"]
    assert row["cap"] == enforced._FREE_CHANNEL_LIMIT
    assert row["is_unlimited"] is False


def test_starter_channels_row_is_unlimited(enforced):
    rows = enforced.capacity_headroom_batch(channels=99)
    row = _row_for(rows, enforced.TIER_CLOUD_STARTER)["channels"]
    assert row["cap"] is None
    assert row["is_unlimited"] is True


def test_pro_retention_row_cap_is_90d(enforced):
    rows = enforced.capacity_headroom_batch(retention_days=45)
    assert _row_for(rows, enforced.TIER_CLOUD_PRO)["retention_days"]["cap"] == 90


def test_enterprise_retention_row_unlimited(enforced):
    rows = enforced.capacity_headroom_batch(retention_days=365)
    row = _row_for(rows, enforced.TIER_ENTERPRISE)["retention_days"]
    assert row["cap"] is None
    assert row["is_unlimited"] is True


def test_starter_retention_over_limit_flag_flips(enforced):
    rows = enforced.capacity_headroom_batch(retention_days=45)
    row = _row_for(rows, enforced.TIER_CLOUD_STARTER)["retention_days"]
    assert row["over_limit"] is True
    assert row["remaining"] == -15


# -- decoupled from resolver ----------------------------------------------


def test_grace_vs_enforce_same_rows(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_rows = e_grace.capacity_headroom_batch(
        channels=2, retention_days=5, nodes=1
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e_enf

    importlib.reload(e_enf)
    e_enf.invalidate()
    enf_rows = e_enf.capacity_headroom_batch(
        channels=2, retention_days=5, nodes=1
    )

    assert grace_rows == enf_rows


# -- never raises ---------------------------------------------------------


def test_walker_failure_returns_empty_list(enforced, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(enforced, "capacity_headroom_at", _boom)
    # The batch shells failures per row (via _at); a top-level exception in
    # the sort/loop path collapses to [] rather than 500-ing.  We simulate
    # that by breaking the tier-rank lookup instead.
    monkeypatch.setattr(enforced, "_PURCHASABLE_TIERS", None)  # type: ignore[misc]
    assert enforced.capacity_headroom_batch(channels=2) == []


def test_per_row_helper_returning_none_is_dropped(enforced, monkeypatch):
    real = enforced.capacity_headroom_at

    def _drop_oss(perspective_tier, **kw):
        if perspective_tier == enforced.TIER_OSS:
            return None
        return real(perspective_tier, **kw)

    monkeypatch.setattr(enforced, "capacity_headroom_at", _drop_oss)
    rows = enforced.capacity_headroom_batch(channels=2)
    tiers = {r["tier"] for r in rows}
    assert enforced.TIER_OSS not in tiers
    # every other purchasable tier survives
    assert tiers == set(enforced._PURCHASABLE_TIERS) - {enforced.TIER_OSS}
