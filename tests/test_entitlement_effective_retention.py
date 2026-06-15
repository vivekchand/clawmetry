"""Tests for Entitlement.effective_retention_days() — the env-aware retention
helper the daemon's prune loop reads.

The headline invariant: ``CLAWMETRY_RETENTION_DAYS`` only SHRINKS retention.
An override larger than the tier cap is clamped to the cap, so a Free install
cannot quietly extend its 7-day window by setting the env var to 90.

These mirror the (previously inline) logic the sync.py prune worker carried —
pinning them here means future refactors of the helper can't drift the prune
loop's behaviour without breaking a test.
"""
from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME at an empty tmp dir and a clean
    env so test order can't leak the env override."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.delenv("CLAWMETRY_RETENTION_DAYS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── default (no env override) ────────────────────────────────────────────────


def test_oss_default_matches_tier_cap(ent):
    en = ent.get_entitlement(force=True)
    assert en.effective_retention_days() == en.event_retention_days() == 7


def test_enterprise_default_is_unlimited(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise", "node_limit": 1, "expiry": None}))
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() is None
    assert en.effective_retention_days() is None


# ── env override: shrink-only ────────────────────────────────────────────────


def test_env_override_shrinks_below_cap(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "3")
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() == 7  # tier cap unchanged
    assert en.effective_retention_days() == 3


def test_env_override_clamped_to_cap(ent, monkeypatch):
    """Setting CLAWMETRY_RETENTION_DAYS above the tier cap is ignored — the
    operator cannot silently extend retention past what the tier grants."""
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "365")
    en = ent.get_entitlement(force=True)
    assert en.effective_retention_days() == 7


def test_env_override_honoured_when_cap_is_unlimited(ent, tmp_path, monkeypatch):
    """Enterprise has no cap so the override always wins (operator-controlled
    custom retention)."""
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise", "node_limit": 1, "expiry": None}))
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "180")
    en = ent.get_entitlement(force=True)
    assert en.effective_retention_days() == 180


# ── invalid / hostile env values ─────────────────────────────────────────────


@pytest.mark.parametrize("bad", ["", "  ", "abc", "1.5", "-1", "0", "nan"])
def test_env_override_invalid_falls_back_to_cap(ent, monkeypatch, bad):
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", bad)
    en = ent.get_entitlement(force=True)
    assert en.effective_retention_days() == en.event_retention_days() == 7


def test_explicit_argument_overrides_env(ent, monkeypatch):
    """Callers (tests, future programmatic prune triggers) can pass an override
    explicitly without mutating the process env."""
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "5")
    en = ent.get_entitlement(force=True)
    # Argument wins over the env var. 2 < cap=7 so it shrinks to 2.
    assert en.effective_retention_days(env_override=2) == 2


def test_explicit_argument_clamped_to_cap(ent):
    en = ent.get_entitlement(force=True)
    assert en.effective_retention_days(env_override=999) == 7


# ── to_dict shape + diagnostic surface ───────────────────────────────────────


def test_to_dict_carries_effective_retention(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "2")
    d = ent.get_entitlement(force=True).to_dict()
    assert d["retention_days"] == 7              # tier cap unchanged
    assert d["effective_retention_days"] == 2    # effective for the prune loop


def test_diagnostic_reports_env_override(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "4")
    diag = ent.resolution_diagnostic()
    assert diag["retention_override_env_name"] == "CLAWMETRY_RETENTION_DAYS"
    assert diag["retention_override_env_value"] == "4"


def test_diagnostic_reports_missing_env_as_none(ent):
    diag = ent.resolution_diagnostic()
    # The env var is intentionally not set; the diagnostic must report it
    # rather than omitting the key, so an operator can tell "unset" from "0".
    assert diag["retention_override_env_name"] == "CLAWMETRY_RETENTION_DAYS"
    assert diag["retention_override_env_value"] is None
