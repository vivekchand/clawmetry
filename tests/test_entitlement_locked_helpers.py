"""Tests for ``Entitlement.locked_runtimes()`` / ``locked_features()``.

The dashboard wants a single, never-raises source for "what is the paywall
covering on this install?" so the paywall summary / "N runtimes locked"
badge does not have to iterate :data:`PAID_RUNTIMES` and re-derive the
gate. These tests pin the inverse-of-``allows_*`` contract across grace,
each paid tier, and the expired-license case so a future tier shuffle or
a misbehaving gate breaks loudly here instead of silently in the UI.
"""
from __future__ import annotations

import importlib
import json
import time
from dataclasses import replace

import pytest
from flask import Flask


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── grace mode (the default) ────────────────────────────────────────────────


def test_grace_locks_nothing(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.locked_runtimes() == ()
    assert en.locked_features() == ()


# ── enforced: each tier reports the right paid-gap ──────────────────────────


def test_oss_enforced_locks_every_paid_runtime_and_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS
    assert en.grace is False
    assert set(en.locked_runtimes()) == set(ent.PAID_RUNTIMES)
    assert set(en.locked_features()) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )
    # Free items must never appear in either list.
    assert set(en.locked_runtimes()).isdisjoint(ent.FREE_RUNTIMES)
    assert set(en.locked_features()).isdisjoint(ent.FREE_FEATURES)


def test_starter_enforced_locks_pro_only_plus_enterprise(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_starter", "node_limit": 1, "expiry": None})
    )
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_STARTER
    # Starter unlocks every paid runtime, so the locked list is empty.
    assert en.locked_runtimes() == ()
    # Starter does NOT unlock pro-only or enterprise features.
    expected = (set(ent.PAID_FEATURES) - set(ent.STARTER_FEATURES)) | set(
        ent.ENTERPRISE_FEATURES
    )
    assert set(en.locked_features()) == expected


def test_pro_enforced_locks_only_enterprise_features(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": None})
    )
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_PRO
    assert en.locked_runtimes() == ()
    assert set(en.locked_features()) == set(ent.ENTERPRISE_FEATURES)


def test_enterprise_enforced_locks_nothing(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "enterprise", "node_limit": 0, "expiry": None})
    )
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_ENTERPRISE
    assert en.locked_runtimes() == ()
    assert en.locked_features() == ()


# ── expired entitlement collapses back to the OSS-paywall ───────────────────


def test_expired_pro_enforced_locks_every_paid_again(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    expired = ent._build(
        ent.TIER_CLOUD_PRO,
        "cloud",
        node_limit=1,
        expiry=time.time() - 3600,  # one hour ago
    )
    assert expired.expired is True
    assert set(expired.locked_runtimes()) == set(ent.PAID_RUNTIMES)
    assert set(expired.locked_features()) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )


# ── shape invariants ────────────────────────────────────────────────────────


def test_locked_runtimes_returns_sorted_tuple(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    locked = en.locked_runtimes()
    assert isinstance(locked, tuple)
    assert list(locked) == sorted(locked)


def test_locked_features_returns_sorted_tuple(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    locked = en.locked_features()
    assert isinstance(locked, tuple)
    assert list(locked) == sorted(locked)


def test_locked_helpers_match_allows_inverse(ent, monkeypatch):
    """Per-item invariant: `locked_*` lists exactly the paid items
    `allows_*` rejects. Drift between the two would mean the paywall
    summary and the per-gate decision disagree."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    en = ent.get_entitlement(force=True)
    for rt in ent.PAID_RUNTIMES:
        assert (rt in en.locked_runtimes()) is (not en.allows_runtime(rt)), rt
    for f in set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES):
        assert (f in en.locked_features()) is (not en.allows_feature(f)), f


def test_locked_helpers_never_raise_on_corrupt_state(ent):
    """A locked-list call on a deeply broken Entitlement (e.g. ``features``
    swapped for a non-iterable) must collapse to ``()`` rather than crash a
    request path."""
    broken = replace(ent._oss_free(), grace=False, features=None, runtimes=None)
    assert broken.locked_runtimes() == ()
    assert broken.locked_features() == ()


# ── to_dict / API surface ───────────────────────────────────────────────────


def test_to_dict_includes_locked_keys_in_grace(ent):
    payload = ent._oss_free().to_dict()
    assert "locked_runtimes" in payload
    assert "locked_features" in payload
    assert payload["locked_runtimes"] == []
    assert payload["locked_features"] == []


def test_to_dict_includes_locked_keys_when_enforced(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    payload = ent.get_entitlement(force=True).to_dict()
    assert set(payload["locked_runtimes"]) == set(ent.PAID_RUNTIMES)
    assert set(payload["locked_features"]) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )


def test_api_entitlement_surfaces_locked_keys(client):
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    assert "locked_runtimes" in body
    assert "locked_features" in body
    # Default install is OSS in grace -> both empty.
    assert body["locked_runtimes"] == []
    assert body["locked_features"] == []
