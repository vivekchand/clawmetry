"""Tests for the capacity-axis branches of
:meth:`clawmetry.entitlements.Entitlement.lock_reason`.

Closes the symmetry with
:func:`clawmetry.entitlements.min_tier_for_channel_count` and
:func:`clawmetry.entitlements.min_tier_for_retention_window` so the dashboard
can render "you have 5 channels -- Available in Starter" / "30-day window
exceeds your free cap -- Available in Starter" copy off the same helper that
already answers the feature= and runtime= axes.

Companion to ``tests/test_entitlement_lock_reason.py``
(feature / runtime helper contract) and
``tests/test_entitlements_min_tier_capacity.py`` (the reverse-lookup helpers
this branch consumes).
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


# ── grace mode locks nothing ────────────────────────────────────────────────


def test_grace_channels_overflow_is_unlocked(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.lock_reason("21", kind="channels") is None


def test_grace_retention_overflow_is_unlocked(ent):
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("365", kind="retention_days") is None


# ── enforced OSS: channels overflow surfaces a tier-naming reason ──────────


def test_channels_within_free_cap_is_unlocked_on_oss(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("3", kind="channels") is None


def test_channels_over_free_cap_on_oss_names_starter(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("5", kind="channels")
    assert reason is not None
    # Mentions the overflow count, the cap, and the unlock tier.
    assert "5 channels" in reason
    assert "Starter" in reason
    assert "3" in reason  # the OSS cap


# ── enforced OSS: retention overflow surfaces a tier-naming reason ─────────


def test_retention_within_free_cap_is_unlocked_on_oss(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("7", kind="retention_days") is None


def test_retention_thirty_days_on_oss_names_starter(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("30", kind="retention_days")
    assert reason is not None
    assert "30-day retention" in reason
    assert "Starter" in reason


def test_retention_ninety_days_on_oss_names_pro(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("90", kind="retention_days")
    assert reason is not None
    assert "Pro" in reason


def test_retention_year_on_oss_names_enterprise(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("365", kind="retention_days")
    assert reason is not None
    assert "Enterprise" in reason


# ── tier-dependent unlocks ──────────────────────────────────────────────────


def test_starter_unlocks_unlimited_channels(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud", node_limit=1, expiry=None)
    assert starter.lock_reason("21", kind="channels") is None


def test_starter_unlocks_thirty_day_retention(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud", node_limit=1, expiry=None)
    assert starter.lock_reason("30", kind="retention_days") is None


def test_starter_still_locks_ninety_day_retention_with_pro_message(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud", node_limit=1, expiry=None)
    reason = starter.lock_reason("90", kind="retention_days")
    assert reason is not None
    assert "Pro" in reason


# ── expiry ──────────────────────────────────────────────────────────────────


def test_expired_channels_overflow_says_expired(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    expired = ent._build(ent.TIER_PRO, "license", node_limit=1, expiry=1.0)
    assert expired.expired is True
    reason = expired.lock_reason("21", kind="channels")
    assert reason is not None
    assert "expired" in reason.lower()


def test_expired_retention_overflow_says_expired(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    expired = ent._build(ent.TIER_PRO, "license", node_limit=1, expiry=1.0)
    reason = expired.lock_reason("30", kind="retention_days")
    assert reason is not None
    assert "expired" in reason.lower()


# ── bad input is silently un-locked (never-crash, never-claim) ─────────────


def test_non_int_channels_returns_none(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("abc", kind="channels") is None
    assert en.lock_reason("", kind="channels") is None


def test_non_int_retention_returns_none(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("abc", kind="retention_days") is None


def test_zero_channels_returns_none(ent, monkeypatch):
    """Zero / negative counts are trivially satisfied; no lock to explain."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("0", kind="channels") is None
    assert en.lock_reason("-3", kind="channels") is None


def test_zero_retention_returns_none(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("0", kind="retention_days") is None
    assert en.lock_reason("-30", kind="retention_days") is None


# ── auto-infer never picks up a numeric key ────────────────────────────────


def test_numeric_input_requires_explicit_kind(ent, monkeypatch):
    """``lock_reason`` auto-infers ``kind`` from a known feature/runtime id.
    A bare digit string is neither, so without an explicit ``kind`` the helper
    silently returns None -- matching the pre-existing "unknown ids err on the
    un-locked side" contract."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("21") is None
    # ...but with kind=, the capacity branch fires.
    assert en.lock_reason("21", kind="channels") is not None
