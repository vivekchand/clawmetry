"""Tests for ``Entitlement.lock_reason()`` + the module-level convenience.

The helper exists so every surface that needs to explain *why* a runtime or
feature is locked -- the ``@gate`` decorator's 402 body, the runtime/feature
catalog rows, the CLI diagnostics -- composes the same string from the same
place. The tests below pin that contract:

* grace mode locks nothing (never returns a reason)
* free runtimes / free features never have a reason
* paid items on a free tier surface a reason that mentions the tier where
  they unlock (Starter / Pro / Enterprise)
* an expired license locks the paid items it used to grant
* a higher tier (Pro) sees its grants as un-locked
* a Starter tier still sees Pro-only items as locked
* unknown / empty input is silently un-locked (never-raise, never-claim)
* the module-level :func:`clawmetry.entitlements.lock_reason` mirrors the
  instance method
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default; individual tests opt in via ``monkeypatch.setenv``."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── grace mode ──────────────────────────────────────────────────────────────


def test_grace_locks_nothing_runtime(ent):
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("claude_code") is None
    assert en.lock_reason("openclaw") is None


def test_grace_locks_nothing_feature(ent):
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("self_evolve") is None
    assert en.lock_reason("sessions") is None


# ── free items never lock ───────────────────────────────────────────────────


def test_free_runtime_never_locked_when_enforced(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.lock_reason("openclaw") is None
    assert en.lock_reason("nemoclaw") is None


def test_free_feature_never_locked_when_enforced(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("sessions") is None
    assert en.lock_reason("transcripts") is None
    assert en.lock_reason("nemo_governance") is None


# ── paid items on OSS in enforce mode ───────────────────────────────────────


def test_paid_runtime_locked_on_oss(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("claude_code")
    assert reason is not None
    assert "claude_code" in reason
    assert "Paid runtime" in reason


def test_paid_feature_reason_names_starter(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    # `fleet` is a Starter-tier feature.
    reason = en.lock_reason("fleet")
    assert reason is not None
    assert "Starter" in reason
    assert "fleet" in reason


def test_paid_feature_reason_names_pro(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    # `self_evolve` is a Pro-only feature.
    reason = en.lock_reason("self_evolve")
    assert reason is not None
    assert "Pro" in reason
    assert "self_evolve" in reason


def test_paid_feature_reason_names_enterprise(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    # `sso` is an Enterprise-only feature.
    reason = en.lock_reason("sso")
    assert reason is not None
    assert "Enterprise" in reason
    assert "sso" in reason


# ── explicit kind selection ─────────────────────────────────────────────────


def test_kind_runtime_explicit(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("claude_code", kind="runtime")
    assert reason is not None
    assert "runtime" in reason.lower()


def test_kind_feature_explicit(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("fleet", kind="feature")
    assert reason is not None
    assert "feature" in reason.lower()


# ── tier-dependent unlocks ──────────────────────────────────────────────────


def test_pro_tier_unlocks_paid_runtimes(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    pro = ent._build(ent.TIER_PRO, "license", node_limit=1, expiry=None)
    assert pro.lock_reason("claude_code") is None
    assert pro.lock_reason("self_evolve") is None


def test_starter_tier_still_locks_pro_only_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud", node_limit=1, expiry=None)
    # Starter grants `fleet`.
    assert starter.lock_reason("fleet") is None
    # Starter does NOT grant `self_evolve` (Pro-only).
    reason = starter.lock_reason("self_evolve")
    assert reason is not None
    assert "Pro" in reason


def test_starter_tier_still_locks_enterprise_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud", node_limit=1, expiry=None)
    reason = starter.lock_reason("sso")
    assert reason is not None
    assert "Enterprise" in reason


# ── expiry ──────────────────────────────────────────────────────────────────


def test_expired_paid_runtime_reason_says_expired(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    # Expiry in the distant past.
    expired = ent._build(ent.TIER_PRO, "license", node_limit=1, expiry=1.0)
    assert expired.expired is True
    reason = expired.lock_reason("claude_code")
    assert reason is not None
    assert "expired" in reason.lower()


def test_expired_paid_feature_reason_says_expired(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    expired = ent._build(ent.TIER_PRO, "license", node_limit=1, expiry=1.0)
    reason = expired.lock_reason("self_evolve")
    assert reason is not None
    assert "expired" in reason.lower()


# ── unknown / bad input ─────────────────────────────────────────────────────


def test_unknown_item_returns_none(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("not_a_real_thing") is None
    assert en.lock_reason("definitely_not_a_runtime", kind="runtime") is None
    assert en.lock_reason("definitely_not_a_feature", kind="feature") is None


def test_empty_and_none_input_is_safe(ent):
    en = ent.get_entitlement(force=True)
    assert en.lock_reason("") is None
    assert en.lock_reason(None) is None  # type: ignore[arg-type]
    # Whitespace, case mixing, and absurd length all stay safe.
    assert en.lock_reason("   ") is None
    assert en.lock_reason("X" * 4096) is None


def test_case_insensitive_input(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    reason = en.lock_reason("Claude_Code")
    assert reason is not None
    assert "claude_code" in reason


# ── module-level convenience ────────────────────────────────────────────────


def test_module_level_lock_reason_mirrors_instance(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    assert ent.lock_reason("claude_code") is not None
    assert ent.lock_reason("openclaw") is None
    assert ent.lock_reason("self_evolve") is not None


def test_module_level_lock_reason_grace_returns_none(ent):
    # Default fixture state: grace mode is on.
    assert ent.lock_reason("claude_code") is None
    assert ent.lock_reason("self_evolve") is None


def test_module_level_lock_reason_never_raises(ent, monkeypatch):
    """Even if ``get_entitlement`` itself raises, the module-level helper must
    swallow the error and return ``None`` (never-crash contract)."""

    def boom(*a, **kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.lock_reason("claude_code") is None
    assert ent.lock_reason("self_evolve") is None
