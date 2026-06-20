"""Tests for the ``nodes`` capacity-axis branch of
:meth:`clawmetry.entitlements.Entitlement.lock_reason`.

Closes the symmetry with :func:`min_tier_for_node_count` so the dashboard /
fleet route can render "you have 5 nodes -- Available in Starter" copy off
the same helper that already answers the feature / runtime / channels /
retention_days axes.

Companion to ``tests/test_entitlement_lock_reason.py`` (feature / runtime
contract) and ``tests/test_entitlement_lock_reason_capacity.py`` (the
channels= / retention_days= branches this mirrors).
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


def test_grace_nodes_overflow_is_unlocked(ent):
    """Headline rollout invariant -- wiring this branch must not change
    current behaviour. Grace returns None for any node count."""
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.lock_reason("99", kind="nodes") is None


# ── enforced OSS: node overflow surfaces a tier-naming reason ──────────────


def test_single_node_within_free_cap_is_unlocked_on_oss(ent, monkeypatch):
    """1 node fits the OSS single-node grant -- no lock to explain."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("1", kind="nodes") is None


def test_two_nodes_on_oss_names_starter(ent, monkeypatch):
    """2 nodes over the OSS single-node grant names Starter, the cap, and
    the overflow count -- mirrors the channels branch's reason shape."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("2", kind="nodes")
    assert reason is not None
    # Mentions the overflow count, the cap, and the unlock tier.
    assert "2 nodes" in reason
    assert "Starter" in reason
    assert "1" in reason  # the OSS cap surfaced from Entitlement.node_limit


# ── tier-dependent unlocks ─────────────────────────────────────────────────


def test_starter_unlocks_higher_node_counts(ent, monkeypatch):
    """A Starter grant with node_limit=10 admits 1..10 and locks 11+. Lock
    reason on 11 cites Starter's per-license cap (10), not the static
    per-tier ceiling (None / unlimited)."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(
        ent.TIER_CLOUD_STARTER, "cloud", node_limit=10, expiry=None,
    )
    assert starter.lock_reason("10", kind="nodes") is None
    reason = starter.lock_reason("11", kind="nodes")
    assert reason is not None
    assert "11 nodes" in reason
    assert "10" in reason  # the license-bound cap surfaces, not "unlimited"


def test_enterprise_unlimited_grant_unlocks_everything(ent, monkeypatch):
    """An Enterprise grant with ``node_limit=0`` (the unlimited sentinel)
    locks nothing -- matches :meth:`Entitlement.allows_node_count`'s
    contract."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent._build(ent.TIER_ENTERPRISE, "license", node_limit=0, expiry=None)
    assert en.lock_reason("1000", kind="nodes") is None


# ── expiry ─────────────────────────────────────────────────────────────────


def test_expired_paid_grant_says_expired(ent, monkeypatch):
    """An expired paid plan should behave like OSS for node-count checks
    too -- same posture as the channels / retention branches."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    expired = ent._build(ent.TIER_PRO, "license", node_limit=25, expiry=1.0)
    assert expired.expired is True
    reason = expired.lock_reason("2", kind="nodes")
    assert reason is not None
    assert "expired" in reason.lower()


# ── bad input is silently un-locked (never-crash, never-claim) ────────────


def test_non_int_nodes_returns_none(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("abc", kind="nodes") is None
    assert en.lock_reason("", kind="nodes") is None


def test_zero_nodes_returns_none(ent, monkeypatch):
    """Zero / negative counts are trivially satisfied; no lock to explain."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("0", kind="nodes") is None
    assert en.lock_reason("-3", kind="nodes") is None


# ── auto-infer never picks up a numeric key ────────────────────────────────


def test_numeric_input_requires_explicit_nodes_kind(ent, monkeypatch):
    """``lock_reason`` auto-infers ``kind`` only from a known feature/runtime
    id. A bare digit string is neither, so without an explicit ``kind`` the
    helper returns None -- matches the channels / retention_days branches."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("5") is None
    # ...but with kind=, the nodes branch fires.
    assert en.lock_reason("5", kind="nodes") is not None
