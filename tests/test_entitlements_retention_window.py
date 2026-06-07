"""Tests for ``Entitlement.allows_retention_window`` — per-tier history-window
gate that mirrors the existing ``allows_runtime`` / ``allows_feature``
``allows_node_count`` family.

Companion to ``tests/test_entitlements_catalogue.py`` (which already pins the
per-tier ``event_retention_days`` cap) — this file pins the *check method*
that the frontend history-range toggles and the daemon's prune loop call.

The headline invariants:

* Grace mode (default OSS-free without ``CLAWMETRY_ENFORCE``) always returns
  ``True`` — wiring the gate in changes no current behaviour.
* Once enforce is on, every paid tier's window cap (Starter=30, Pro=90,
  Enterprise=unlimited) is respected.
* ``days <= 0`` is trivially allowed (asking for zero history is free).
* ``days is None`` (request unlimited) only passes on Enterprise.
* An expired entitlement denies any positive window.
"""
from __future__ import annotations

import importlib
import json
import time

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


def _write_plan(tmp_path, plan, **extra):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    body = {"plan": plan}
    body.update(extra)
    cache.write_text(json.dumps(body))


# ── grace mode ───────────────────────────────────────────────────────────────


def test_grace_allows_any_window(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.allows_retention_window(7) is True
    assert en.allows_retention_window(30) is True
    assert en.allows_retention_window(365) is True
    assert en.allows_retention_window(None) is True
    assert en.allows_retention_window(0) is True
    assert en.allows_retention_window(-1) is True


# ── enforce mode: per-tier caps ──────────────────────────────────────────────


def test_enforce_oss_caps_at_seven(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.allows_retention_window(1) is True
    assert en.allows_retention_window(7) is True       # at the cap
    assert en.allows_retention_window(8) is False      # one day over
    assert en.allows_retention_window(30) is False
    assert en.allows_retention_window(None) is False   # unlimited denied


def test_enforce_starter_caps_at_thirty(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "cloud_starter")
    en = ent.get_entitlement(force=True)
    assert en.allows_retention_window(7) is True
    assert en.allows_retention_window(30) is True      # at the cap
    assert en.allows_retention_window(31) is False
    assert en.allows_retention_window(90) is False
    assert en.allows_retention_window(None) is False


def test_enforce_pro_caps_at_ninety(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "cloud_pro")
    en = ent.get_entitlement(force=True)
    assert en.allows_retention_window(30) is True
    assert en.allows_retention_window(90) is True      # at the cap
    assert en.allows_retention_window(91) is False
    assert en.allows_retention_window(365) is False
    assert en.allows_retention_window(None) is False


def test_enforce_enterprise_is_unlimited(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "enterprise")
    en = ent.get_entitlement(force=True)
    assert en.allows_retention_window(7) is True
    assert en.allows_retention_window(90) is True
    assert en.allows_retention_window(10_000) is True
    assert en.allows_retention_window(None) is True    # unlimited explicitly granted


def test_enforce_trial_matches_starter_window(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "trial")
    en = ent.get_entitlement(force=True)
    # Trial uses the Starter retention cap (30) per _TIER_RETENTION_DAYS.
    assert en.allows_retention_window(30) is True
    assert en.allows_retention_window(31) is False


# ── edge cases ───────────────────────────────────────────────────────────────


def test_zero_or_negative_days_is_allowed_on_oss(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_retention_window(0) is True
    assert en.allows_retention_window(-5) is True


def test_zero_days_is_allowed_even_when_expired(ent, monkeypatch, tmp_path):
    """An expired tier still allows the trivial zero-day window — denying that
    would force any consumer to special-case `0` before calling, defeating the
    point of a single canonical check."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "cloud_pro", expiry=time.time() - 3600)
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_retention_window(0) is True


def test_expired_paid_tier_denies_positive_window(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "cloud_pro", expiry=time.time() - 3600)
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_retention_window(1) is False
    assert en.allows_retention_window(90) is False
    assert en.allows_retention_window(None) is False


def test_expired_enterprise_also_denies_positive_window(ent, monkeypatch, tmp_path):
    """Even Enterprise (unlimited cap) denies positive windows once expired —
    `expired` checks land before the cap lookup."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_plan(tmp_path, "enterprise", expiry=time.time() - 3600)
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_retention_window(7) is False
    assert en.allows_retention_window(None) is False
    # Zero-day window still trivially fine.
    assert en.allows_retention_window(0) is True


# ── consistency with event_retention_days() ──────────────────────────────────


def test_window_check_at_cap_matches_event_retention_days(ent, monkeypatch, tmp_path):
    """For every paid tier with a finite cap, `allows_retention_window(cap)` is
    True and `allows_retention_window(cap + 1)` is False — pins the gate
    against the catalogue table."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    for plan in ("cloud_starter", "cloud_pro", "trial"):
        _write_plan(tmp_path, plan)
        en = ent.get_entitlement(force=True)
        cap = en.event_retention_days()
        assert cap is not None, plan
        assert en.allows_retention_window(cap) is True, plan
        assert en.allows_retention_window(cap + 1) is False, plan
        ent.invalidate()
