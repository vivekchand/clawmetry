"""Tests for Entitlement.locked_runtimes() / locked_features() — the inverse
view of allows_runtime / allows_feature restricted to the paid universe.

These helpers exist so the UI can render a "N runtimes locked — upgrade"
badge off /api/entitlement in one call, without iterating PAID_RUNTIMES or
re-deriving feature-set membership on the frontend.

Invariants pinned here:

* Grace mode → both helpers return empty tuples (every gate passes).
* Enforce + OSS → every paid runtime / paid+enterprise feature is locked.
* Enforce + Pro tier → no paid runtimes locked, only ENTERPRISE_FEATURES
  are locked.
* Enforce + Enterprise tier → nothing is locked.
* Expired paid licence → paid runtimes / features collapse back to locked
  (mirrors the ``expired`` short-circuit in ``allows_*``).
* ``to_dict()`` exposes the two lists with stable, alphabetical ordering.
* Free runtimes / free features are NEVER reported as locked — they cannot
  be (they're always allowed).
* The helpers never raise: a flaky ``allows_*`` call falls back to ``()``.
* Grace mode is byte-for-byte gate-irrelevant: with the helpers wired in,
  ``allows_runtime`` / ``allows_feature`` decisions are unchanged.
"""
from __future__ import annotations

import importlib
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement
    off by default."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── grace mode: nothing is ever locked ────────────────────────────────────────


def test_grace_locked_runtimes_is_empty(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.locked_runtimes() == ()


def test_grace_locked_features_is_empty(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.locked_features() == ()


# ── enforce + OSS: the full paid universe is locked ───────────────────────────


def test_enforce_oss_locks_every_paid_runtime(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert set(en.locked_runtimes()) == set(ent.PAID_RUNTIMES)
    # No free runtime ever appears.
    assert not (set(en.locked_runtimes()) & set(ent.FREE_RUNTIMES))


def test_enforce_oss_locks_paid_and_enterprise_features(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    expected = ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES
    assert set(en.locked_features()) == expected
    # No free feature ever appears.
    assert not (set(en.locked_features()) & set(ent.FREE_FEATURES))


# ── enforce + Pro: paid runtimes open, enterprise features still locked ───────


def test_enforce_pro_unlocks_paid_runtimes(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_PRO, "license")
    assert pro.locked_runtimes() == ()


def test_enforce_pro_still_locks_enterprise_features(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_PRO, "license")
    locked = set(pro.locked_features())
    # Pro covers PAID_FEATURES but not ENTERPRISE_FEATURES.
    assert locked == ent.ENTERPRISE_FEATURES
    # And no free feature leaks in.
    assert not (locked & ent.FREE_FEATURES)


# ── enforce + Enterprise: nothing is locked ───────────────────────────────────


def test_enforce_enterprise_locks_nothing(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent_tier = ent._build(ent.TIER_ENTERPRISE, "license")
    assert ent_tier.locked_runtimes() == ()
    assert ent_tier.locked_features() == ()


# ── expired licence: paid surface collapses back to locked ────────────────────


def test_enforce_expired_pro_locks_paid_runtimes(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_PRO, "license", expiry=time.time() - 60)
    assert pro.expired is True
    # Expired short-circuit in allows_runtime → paid runtimes locked again.
    assert set(pro.locked_runtimes()) == set(ent.PAID_RUNTIMES)


def test_enforce_expired_pro_locks_paid_features(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_PRO, "license", expiry=time.time() - 60)
    assert pro.expired is True
    expected = ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES
    assert set(pro.locked_features()) == expected


# ── ordering + shape ──────────────────────────────────────────────────────────


def test_locked_runtimes_is_sorted_tuple(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    result = en.locked_runtimes()
    assert isinstance(result, tuple)
    assert list(result) == sorted(result)


def test_locked_features_is_sorted_tuple(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    result = en.locked_features()
    assert isinstance(result, tuple)
    assert list(result) == sorted(result)


# ── to_dict wire shape ────────────────────────────────────────────────────────


def test_to_dict_carries_locked_lists(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    d = en.to_dict()
    assert "locked_runtimes" in d
    assert "locked_features" in d
    assert isinstance(d["locked_runtimes"], list)
    assert isinstance(d["locked_features"], list)
    assert set(d["locked_runtimes"]) == set(ent.PAID_RUNTIMES)
    assert set(d["locked_features"]) == ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES


def test_to_dict_in_grace_has_empty_locked_lists(ent):
    en = ent.get_entitlement(force=True)
    d = en.to_dict()
    assert d["locked_runtimes"] == []
    assert d["locked_features"] == []


# ── gate-irrelevance: the helpers don't change the decision surface ──────────


def test_helpers_never_change_allows_decisions(ent, monkeypatch):
    """Adding the inverse helpers must not alter what ``allows_*`` decides
    for the same input. This is the no-behaviour-change contract."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_PRO, "license")
    # Trigger the helpers first — must not mutate any state.
    pro.locked_runtimes()
    pro.locked_features()
    assert pro.allows_runtime("openclaw") is True
    assert pro.allows_runtime("claude_code") is True
    assert pro.allows_feature("custom_alerts") is True
    assert pro.allows_feature("sso") is False  # Enterprise-only


# ── never-raise contract ──────────────────────────────────────────────────────


def test_locked_runtimes_swallows_flaky_gate(ent, monkeypatch):
    """A raising ``allows_runtime`` (e.g. a bad subclass) must collapse the
    helper to ``()`` rather than break a UI render."""
    en = ent.get_entitlement(force=True)

    class _Boom(ent.Entitlement):
        def allows_runtime(self, runtime: str) -> bool:  # type: ignore[override]
            raise RuntimeError("boom")

    boom = _Boom(
        tier=en.tier,
        source=en.source,
        node_limit=en.node_limit,
        expiry=en.expiry,
        features=en.features,
        runtimes=en.runtimes,
        grace=en.grace,
    )
    assert boom.locked_runtimes() == ()


def test_locked_features_swallows_flaky_gate(ent, monkeypatch):
    en = ent.get_entitlement(force=True)

    class _Boom(ent.Entitlement):
        def allows_feature(self, feature: str) -> bool:  # type: ignore[override]
            raise RuntimeError("boom")

    boom = _Boom(
        tier=en.tier,
        source=en.source,
        node_limit=en.node_limit,
        expiry=en.expiry,
        features=en.features,
        runtimes=en.runtimes,
        grace=en.grace,
    )
    assert boom.locked_features() == ()
