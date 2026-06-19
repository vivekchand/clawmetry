"""Tests for the capacity-axis ``min_tier_for_*`` helpers.

``min_tier_for_channel_count(n)`` and ``min_tier_for_retention_window(days)``
close the symmetry gap with ``min_tier_for_feature`` / ``min_tier_for_runtime``
so the lock affordance on the channel-overflow and history-range surfaces can
render "Available in <tier>" copy off a single canonical reverse lookup
instead of re-deriving the per-tier cap tables in JavaScript.

This file pins the bucket boundaries so a future tier-cap shuffle (e.g.
raising Starter retention from 30d to 45d, or dropping the free channel
limit) breaks loudly here instead of silently in the UI.
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


# ── min_tier_for_channel_count ───────────────────────────────────────────────


def test_channel_count_zero_or_negative_collapses_to_oss(ent):
    # zero/negative means "not measured yet" or trivially satisfied -- the free
    # floor covers it (mirrors allows_channel_count's grace-on-zero contract).
    assert ent.min_tier_for_channel_count(0) == ent.TIER_OSS
    assert ent.min_tier_for_channel_count(-5) == ent.TIER_OSS


def test_channel_count_within_free_cap_is_oss(ent):
    # Free cap is 3 (see _FREE_CHANNEL_LIMIT). 1/2/3 all fit on OSS.
    assert ent.min_tier_for_channel_count(1) == ent.TIER_OSS
    assert ent.min_tier_for_channel_count(2) == ent.TIER_OSS
    assert ent.min_tier_for_channel_count(3) == ent.TIER_OSS


def test_channel_count_over_free_cap_requires_starter(ent):
    # Every paid tier has channel_limit=None (unlimited), so the first tier
    # above the free cap is Starter -- the "Available in Starter" surface.
    assert ent.min_tier_for_channel_count(4) == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_channel_count(21) == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_channel_count(1_000_000) == ent.TIER_CLOUD_STARTER


def test_channel_count_non_int_returns_none(ent):
    # None / unparseable -- caller can distinguish "free" from "broken input".
    assert ent.min_tier_for_channel_count(None) is None
    assert ent.min_tier_for_channel_count("not a number") is None
    assert ent.min_tier_for_channel_count(object()) is None


def test_channel_count_string_digit_is_accepted(ent):
    # int() accepts numeric strings; documenting the wire-side contract.
    assert ent.min_tier_for_channel_count("3") == ent.TIER_OSS
    assert ent.min_tier_for_channel_count("4") == ent.TIER_CLOUD_STARTER


def test_channel_count_never_returns_trial(ent):
    # Trial is a promotional grant, not a price-page row -- the lock copy
    # should never advertise it. Sweep a representative range.
    for n in (0, 1, 3, 4, 5, 10, 21, 100):
        assert ent.min_tier_for_channel_count(n) != ent.TIER_TRIAL


def test_channel_count_returns_purchasable_tiers_only(ent):
    # Every answer must be selectable from /pricing (trial excluded by design).
    purchasable = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    for n in (0, 1, 3, 4, 21, 100):
        assert ent.min_tier_for_channel_count(n) in purchasable


# ── min_tier_for_retention_window ────────────────────────────────────────────


def test_retention_zero_or_negative_collapses_to_oss(ent):
    # Same posture as channel_count: zero history is trivially satisfied.
    assert ent.min_tier_for_retention_window(0) == ent.TIER_OSS
    assert ent.min_tier_for_retention_window(-30) == ent.TIER_OSS


def test_retention_within_free_cap_is_oss(ent):
    # Free cap is 7 days.
    assert ent.min_tier_for_retention_window(1) == ent.TIER_OSS
    assert ent.min_tier_for_retention_window(7) == ent.TIER_OSS


def test_retention_within_starter_cap_is_starter(ent):
    # Starter cap is 30 days. 8..30 fall in this bucket.
    assert ent.min_tier_for_retention_window(8) == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_retention_window(14) == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_retention_window(30) == ent.TIER_CLOUD_STARTER


def test_retention_within_pro_cap_is_cloud_pro(ent):
    # Pro cap is 90 days. 31..90 fall here.
    assert ent.min_tier_for_retention_window(31) == ent.TIER_CLOUD_PRO
    assert ent.min_tier_for_retention_window(60) == ent.TIER_CLOUD_PRO
    assert ent.min_tier_for_retention_window(90) == ent.TIER_CLOUD_PRO


def test_retention_above_pro_cap_requires_enterprise(ent):
    # Anything over 90 days only fits Enterprise (cap=None / unlimited).
    assert ent.min_tier_for_retention_window(91) == ent.TIER_ENTERPRISE
    assert ent.min_tier_for_retention_window(180) == ent.TIER_ENTERPRISE
    assert ent.min_tier_for_retention_window(3650) == ent.TIER_ENTERPRISE


def test_retention_unlimited_request_is_enterprise(ent):
    # ``days is None`` means "unlimited history", which only Enterprise grants
    # -- mirrors allows_retention_window's `days is None -> Enterprise only`.
    assert ent.min_tier_for_retention_window(None) == ent.TIER_ENTERPRISE


def test_retention_non_int_returns_none(ent):
    # Distinguishes "no answer" from "free floor". ``None`` is the explicit
    # unlimited request and is handled above.
    assert ent.min_tier_for_retention_window("not a number") is None
    assert ent.min_tier_for_retention_window(object()) is None


def test_retention_string_digit_is_accepted(ent):
    assert ent.min_tier_for_retention_window("7") == ent.TIER_OSS
    assert ent.min_tier_for_retention_window("30") == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_retention_window("90") == ent.TIER_CLOUD_PRO


def test_retention_never_returns_trial(ent):
    # Trial is excluded by design even though _TIER_RETENTION_DAYS lists it.
    for d in (0, 1, 7, 8, 30, 31, 90, 91, 365, None):
        assert ent.min_tier_for_retention_window(d) != ent.TIER_TRIAL


def test_retention_returns_purchasable_tiers_only(ent):
    purchasable = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    for d in (0, 1, 7, 8, 30, 31, 90, 91, 365, None):
        assert ent.min_tier_for_retention_window(d) in purchasable


def test_retention_buckets_are_monotonic_in_tier_rank(ent):
    # As days grow the answer should never get cheaper.
    samples = [1, 7, 8, 30, 31, 90, 91, 365]
    ranks = [ent.tier_rank(ent.min_tier_for_retention_window(d)) for d in samples]
    assert ranks == sorted(ranks), ranks


def test_channel_count_buckets_are_monotonic_in_tier_rank(ent):
    samples = [0, 1, 3, 4, 5, 21, 100]
    ranks = [ent.tier_rank(ent.min_tier_for_channel_count(n)) for n in samples]
    assert ranks == sorted(ranks), ranks


# ── never-raise contract ─────────────────────────────────────────────────────


def test_helpers_never_raise_on_garbage(ent):
    # The dashboard renders these inline; a stray non-numeric query string
    # must never crash the page.
    for bad in (None, "", "abc", [], {}, object()):
        try:
            ent.min_tier_for_channel_count(bad)
            ent.min_tier_for_retention_window(bad)
        except Exception as exc:  # pragma: no cover - regression guard
            pytest.fail(f"helper raised on {bad!r}: {exc}")
