"""Tests for :meth:`Entitlement.channel_limit` /
:meth:`Entitlement.allows_channel_count` -- the channel-adapter cap that backs
the ``all_channels`` Starter feature ("Free is limited to 3").

Same grace/enforce posture as :meth:`allows_node_count` and
:meth:`allows_retention_window`: wiring this into the channels route must not
change behaviour before the enforce phase, and a flaky read must never block
a request.
"""
from __future__ import annotations

import importlib
import json
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default -- matches the project rollout posture."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# -- grace mode: pure pass-through --------------------------------------------


def test_grace_channel_limit_is_none(ent):
    """In grace mode every tier reports ``None`` (unlimited) so wiring this
    into the channels route changes nothing before the enforce flip."""
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.channel_limit() is None


def test_grace_allows_any_channel_count(ent):
    """Headline rollout invariant: grace mode allows any count."""
    en = ent.get_entitlement(force=True)
    for count in (0, 1, 3, 4, 21, 100):
        assert en.allows_channel_count(count) is True, count


# -- enforce mode: free tier capped at 3, paid tiers unlimited ----------------


def test_enforce_oss_caps_channels_at_three(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.channel_limit() == 3
    assert en.allows_channel_count(1) is True
    assert en.allows_channel_count(3) is True
    assert en.allows_channel_count(4) is False
    assert en.allows_channel_count(21) is False


def test_enforce_cloud_starter_is_unlimited(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_STARTER
    assert en.channel_limit() is None
    assert en.allows_channel_count(4) is True
    assert en.allows_channel_count(21) is True
    assert en.allows_channel_count(100) is True


def test_enforce_cloud_pro_and_enterprise_are_unlimited(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    pro = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    ent_ent = ent._build(ent.TIER_ENTERPRISE, "license")
    assert pro.channel_limit() is None
    assert ent_ent.channel_limit() is None
    assert pro.allows_channel_count(21) is True
    assert ent_ent.allows_channel_count(21) is True


def test_enforce_cloud_free_caps_at_three(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent._build(ent.TIER_CLOUD_FREE, "cloud")
    assert en.channel_limit() == 3
    assert en.allows_channel_count(3) is True
    assert en.allows_channel_count(4) is False


# -- expiry: collapse to free cap ---------------------------------------------


def test_enforce_expired_paid_plan_collapses_to_free_cap(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({
        "plan": "cloud_pro",
        "expiry": time.time() - 60,
    }))
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_channel_count(3) is True
    assert en.allows_channel_count(4) is False


# -- edge cases ---------------------------------------------------------------


def test_enforce_zero_and_negative_current_always_allowed(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_channel_count(0) is True
    assert en.allows_channel_count(-1) is True
    assert en.allows_channel_count(-99) is True


def test_enforce_non_int_current_is_swallowed(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_channel_count(None) is True
    assert en.allows_channel_count("not-a-number") is True
    assert en.allows_channel_count(object()) is True


def test_enforce_string_int_current_is_accepted(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_channel_count("3") is True
    assert en.allows_channel_count("4") is False  # OSS caps at 3


# -- consistency with the rest of the allows_* family ------------------------


def test_grace_allows_family_is_symmetric(ent):
    """In grace mode every gate corner returns True -- the rollout invariant
    the channels route now joins."""
    en = ent.get_entitlement(force=True)
    assert en.allows_runtime("claude_code") is True
    assert en.allows_feature("self_evolve") is True
    assert en.allows_channel_count(21) is True
