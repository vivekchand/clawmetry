"""Tests for clawmetry/entitlements.py — open-core entitlement resolution.

Validates the grace-vs-enforce behaviour, the free/paid runtime split,
graceful fallback on bad input, and the /api/entitlement JSON shape.

The headline invariant: with no license + no cloud plan + no CLAWMETRY_ENFORCE,
the resolver returns OSS-free in GRACE mode where every allows_* check passes,
so wiring the gate in changes no behaviour.
"""
from __future__ import annotations

import importlib
import json
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)  # re-expand ~ against the patched HOME
    e.invalidate()
    yield e
    e.invalidate()


# ── grace mode (default) ──────────────────────────────────────────────────────


def test_default_is_oss_free_in_grace(ent):
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS
    assert en.source == "oss"
    assert en.grace is True
    assert en.is_paid is False
    assert en.expired is False


def test_grace_allows_everything(ent):
    en = ent.get_entitlement(force=True)
    # Paid runtimes + paid features all pass while in grace.
    assert en.allows_runtime("claude_code") is True
    assert en.allows_runtime("openclaw") is True
    assert en.allows_feature("otel_export") is True
    assert en.allows_feature("custom_alerts") is True


def test_available_runtimes_grace_shows_all(ent):
    assert set(ent.available_runtimes()) == set(ent.ALL_RUNTIMES)


# ── enforce mode ───────────────────────────────────────────────────────────────


def test_enforce_blocks_paid_runtime(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.tier == ent.TIER_OSS
    assert en.allows_runtime("openclaw") is True          # free stays free
    assert en.allows_runtime("claude_code") is False      # paid is blocked
    assert en.allows_feature("custom_alerts") is False
    # core features are always free even when enforced
    assert en.allows_feature("sessions") is True


def test_available_runtimes_enforced_oss_is_free_only(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    assert ent.available_runtimes() == sorted(ent.FREE_RUNTIMES)


def test_is_enforced_env_parsing(ent, monkeypatch):
    for v in ("1", "true", "YES", "On"):
        monkeypatch.setenv("CLAWMETRY_ENFORCE", v)
        assert ent.is_enforced() is True
    for v in ("0", "false", "", "no"):
        monkeypatch.setenv("CLAWMETRY_ENFORCE", v)
        assert ent.is_enforced() is False


# ── catalogue invariants ────────────────────────────────────────────────────────


def test_free_runtimes_is_openclaw_only(ent):
    assert ent.FREE_RUNTIMES == frozenset({"openclaw"})
    assert "claude_code" in ent.PAID_RUNTIMES
    assert "nemoclaw" not in ent.PAID_RUNTIMES  # NeMo is governance, not a runtime
    assert ent.FREE_RUNTIMES.isdisjoint(ent.PAID_RUNTIMES)


def test_nemo_governance_is_a_free_feature(ent):
    assert "nemo_governance" in ent.FREE_FEATURES


# ── cloud plan cache (stub source) ───────────────────────────────────────────────


def test_cloud_plan_cache_grants_tier(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 10, "expiry": None}))
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_PRO
    assert en.source == "cloud"
    assert en.node_limit == 10
    assert en.is_paid is True


def test_expired_cloud_plan_blocks_when_enforced(ent, tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 5, "expiry": time.time() - 60}))
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_runtime("claude_code") is False  # expired => no paid runtime


# ── robustness ────────────────────────────────────────────────────────────────


def test_corrupt_cloud_plan_falls_back_to_oss(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("{not valid json")
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS  # never raises, falls through


def test_to_dict_shape(ent):
    d = ent.get_entitlement(force=True).to_dict()
    for key in ("tier", "source", "grace", "enforced", "runtimes", "features", "all_runtimes"):
        assert key in d
    assert d["enforced"] == (not d["grace"])
    assert isinstance(d["runtimes"], list)


# ── runtime_catalog (Phase 5: locked-but-visible foundation) ────────────────


def test_runtime_catalog_grace_locks_nothing(ent):
    cat = ent.runtime_catalog()
    # Every known runtime is present exactly once.
    ids = [r["id"] for r in cat]
    assert set(ids) == set(ent.ALL_RUNTIMES)
    assert len(ids) == len(set(ids))
    # Free runtimes first, paid runtimes after — stable ordering.
    free_count = len(ent.FREE_RUNTIMES)
    assert set(ids[:free_count]) == set(ent.FREE_RUNTIMES)
    assert set(ids[free_count:]) == set(ent.PAID_RUNTIMES)
    # Grace mode: nothing is locked, everything is allowed.
    for row in cat:
        assert row["allowed"] is True
        assert row["locked"] is False
        assert isinstance(row["label"], str) and row["label"]
        # `free` matches FREE_RUNTIMES membership.
        assert row["free"] == (row["id"] in ent.FREE_RUNTIMES)


def test_runtime_catalog_enforced_oss_locks_paid(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cat = {r["id"]: r for r in ent.runtime_catalog()}
    # Free stays free + allowed.
    for rt in ent.FREE_RUNTIMES:
        assert cat[rt]["allowed"] is True
        assert cat[rt]["locked"] is False
    # Every paid runtime is locked when enforced + no entitlement.
    for rt in ent.PAID_RUNTIMES:
        assert cat[rt]["allowed"] is False, rt
        assert cat[rt]["locked"] is True, rt


def test_runtime_catalog_labels_match_paid_runtimes(ent):
    # Every paid runtime has a human-readable label (not just the id) so the
    # UI never has to guess. Catches "added a runtime but forgot the label".
    for rt in ent.PAID_RUNTIMES | ent.FREE_RUNTIMES:
        assert rt in ent.RUNTIME_LABELS, rt
        assert ent.RUNTIME_LABELS[rt], rt


def test_runtime_label_falls_back_to_id(ent):
    assert ent.runtime_label("openclaw") == "OpenClaw"
    # Unknown runtime → graceful fallback to the id so plugin runtimes still
    # render with *something* in the UI.
    assert ent.runtime_label("brand_new_plugin_runtime") == "brand_new_plugin_runtime"
    assert ent.runtime_label("") == ""
    assert ent.runtime_label(None) == ""
