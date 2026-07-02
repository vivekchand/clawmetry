"""Tests for the daemon -> dashboard cloud-plan bridge.

The Flask dashboard process resolves entitlements via
``clawmetry.entitlements.get_entitlement`` which reads
``~/.clawmetry/cloud_plan.json``. Until now the daemon mirrored the heartbeat
``plan`` only into in-process ``_TRIAL_STATE``, so a cloud Pro plan never made
it across the process boundary and ``/api/entitlement`` reported ``tier=oss``
on real Pro installs.

These tests pin the new behaviour: whenever ``_update_trial_state`` learns of
a plan change, ``_persist_cloud_plan_to_disk`` writes a mapped tier code to
the cache file (or removes it on inactive plans), and the entitlements module
picks the new plan up on its next resolution.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync(monkeypatch, tmp_path):
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s

    cache_path = str(tmp_path / ".clawmetry" / "cloud_plan.json")
    monkeypatch.setattr(s, "_CLOUD_PLAN_CACHE_PATH", cache_path)
    s._TRIAL_STATE["sync_allowed"] = True
    s._TRIAL_STATE["plan"] = None
    s._TRIAL_STATE["trial_days_left"] = None
    s._TRIAL_STATE["last_log_day"] = ""

    import clawmetry.entitlements as e
    monkeypatch.setattr(e, "_CLOUD_PLAN_CACHE", cache_path)
    monkeypatch.setattr(e, "_LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    e.invalidate()
    return s


# ── _persist_cloud_plan_to_disk ───────────────────────────────────────────────


def test_persist_writes_cloud_pro_for_pro_plan(sync):
    sync._persist_cloud_plan_to_disk("pro")
    assert os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH)
    payload = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())
    assert payload["plan"] == "cloud_pro"


@pytest.mark.parametrize(
    "heartbeat_plan,expected_tier",
    [
        ("pro", "cloud_pro"),
        ("cloud_pro", "cloud_pro"),
        ("starter", "cloud_starter"),
        ("cloud_starter", "cloud_starter"),
        ("trial", "trial"),
        ("cloud_trial", "trial"),
        ("free", "cloud_free"),
        ("cloud_free", "cloud_free"),
        ("enterprise", "enterprise"),
        ("PRO", "cloud_pro"),  # case-insensitive
        (" pro ", "cloud_pro"),  # whitespace-tolerant
    ],
)
def test_persist_maps_known_plan_codes(sync, heartbeat_plan, expected_tier):
    sync._persist_cloud_plan_to_disk(heartbeat_plan)
    payload = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())
    assert payload["plan"] == expected_tier


@pytest.mark.parametrize("dead_plan", ["trial_expired", "", None, "unknown_plan"])
def test_persist_removes_cache_for_inactive_plans(sync, dead_plan):
    # Seed an existing cache so the removal path is exercised.
    os.makedirs(os.path.dirname(sync._CLOUD_PLAN_CACHE_PATH), exist_ok=True)
    with open(sync._CLOUD_PLAN_CACHE_PATH, "w") as fh:
        json.dump({"plan": "cloud_pro"}, fh)
    sync._persist_cloud_plan_to_disk(dead_plan)
    assert not os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH)


def test_persist_trial_writes_expiry_from_days_left(sync):
    before = time.time()
    sync._persist_cloud_plan_to_disk("trial", trial_days_left=7)
    payload = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())
    assert payload["plan"] == "trial"
    # 7d ± slack for test timing.
    assert payload["expiry"] is not None
    assert (payload["expiry"] - before) > 6 * 86400
    assert (payload["expiry"] - before) < 8 * 86400


def test_persist_pro_has_no_expiry(sync):
    sync._persist_cloud_plan_to_disk("pro", trial_days_left=99)
    payload = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())
    # Only trials get a derived expiry from trial_days_left.
    assert payload["expiry"] is None


def test_persist_is_atomic_no_partial_file(sync):
    sync._persist_cloud_plan_to_disk("pro")
    # The tmp file used for the atomic rename must not be left behind.
    assert not os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH + ".tmp")


def test_persist_swallows_filesystem_errors(sync, monkeypatch):
    # Point the cache at a path inside a non-existent root that cannot be
    # mkdired. Persist must not raise.
    monkeypatch.setattr(sync, "_CLOUD_PLAN_CACHE_PATH", "/nonexistent/root/x/cloud_plan.json")
    sync._persist_cloud_plan_to_disk("pro")  # no exception


# ── _update_trial_state writes through to the cache ──────────────────────────


def test_update_trial_state_persists_pro(sync):
    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    payload = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())
    assert payload["plan"] == "cloud_pro"


def test_update_trial_state_clears_cache_on_expiry(sync):
    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    assert os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH)
    sync._update_trial_state({"sync_allowed": False, "plan": "trial_expired"})
    assert not os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH)


def test_update_trial_state_reconciles_persist_each_heartbeat(sync, monkeypatch):
    """Every heartbeat carrying a plan now RECONCILES the cache (calls persist),
    so a stale/drifted cache self-heals. Redundant disk writes are avoided
    inside _persist_cloud_plan_to_disk itself, which is idempotent (see
    test_persist_is_idempotent_when_tier_unchanged), NOT by skipping the call."""
    calls = {"n": 0}

    def _spy(plan, trial_days_left=None):
        calls["n"] += 1

    monkeypatch.setattr(sync, "_persist_cloud_plan_to_disk", _spy)
    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    assert calls["n"] == 2  # reconciles each heartbeat; persist no-ops when unchanged


# ── integration: dashboard sees the cloud plan after persist ────────────────


def test_entitlements_sees_cloud_pro_after_heartbeat(sync, monkeypatch):
    import clawmetry.entitlements as e

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")  # bypass grace so tier shows
    e.invalidate()

    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    en = e.get_entitlement(force=True)
    assert en.tier == e.TIER_CLOUD_PRO
    assert en.source == "cloud"
    assert en.allows_runtime("claude_code") is True


def test_entitlements_falls_back_to_oss_after_trial_expiry(sync, monkeypatch):
    import clawmetry.entitlements as e

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    e.invalidate()

    sync._update_trial_state({"sync_allowed": True, "plan": "pro"})
    assert e.get_entitlement(force=True).tier == e.TIER_CLOUD_PRO

    sync._update_trial_state({"sync_allowed": False, "plan": "trial_expired"})
    en = e.get_entitlement(force=True)
    assert en.tier == e.TIER_OSS
    assert en.allows_runtime("claude_code") is False


# ── reconcile-every-heartbeat + idempotency (founder ask 2026-06-30) ─────────

def test_persist_is_idempotent_when_tier_unchanged(sync, monkeypatch):
    """Calling _persist with the same tier twice must not re-write the file or
    re-invalidate entitlements (it now runs on every heartbeat)."""
    import clawmetry.entitlements as e
    calls = {"n": 0}
    monkeypatch.setattr(e, "invalidate", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1))

    sync._persist_cloud_plan_to_disk("trial")
    assert calls["n"] == 1
    mtime1 = os.path.getmtime(sync._CLOUD_PLAN_CACHE_PATH)
    plan1 = json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"]
    assert plan1 == "trial"

    time.sleep(0.02)
    sync._persist_cloud_plan_to_disk("trial")  # same tier -> no-op
    assert calls["n"] == 1, "must NOT re-invalidate when the tier is unchanged"
    assert os.path.getmtime(sync._CLOUD_PLAN_CACHE_PATH) == mtime1, "must NOT re-write"


def test_persist_rewrites_on_tier_change(sync, monkeypatch):
    import clawmetry.entitlements as e
    calls = {"n": 0}
    monkeypatch.setattr(e, "invalidate", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1))
    sync._persist_cloud_plan_to_disk("free")
    assert json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"] == "cloud_free"
    sync._persist_cloud_plan_to_disk("pro")  # upgrade -> rewrite + invalidate
    assert json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"] == "cloud_pro"
    assert calls["n"] == 2


def test_update_trial_state_reconciles_when_cache_drifts(sync):
    """The reconcile fires every heartbeat: even when _TRIAL_STATE['plan']
    didn't 'change', a deleted/stale cache is re-written from the live plan.
    This is the user's case: daemon cached free, account upgraded, the cache
    must self-heal on the next heartbeat."""
    sync._TRIAL_STATE["plan"] = "trial"  # state already thinks trial (no "change")
    if os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH):
        os.remove(sync._CLOUD_PLAN_CACHE_PATH)
    # A heartbeat carrying the plan -> reconcile rewrites the missing cache.
    sync._update_trial_state({"sync_allowed": True, "plan": "trial", "trial_days_left": 6})
    assert os.path.isfile(sync._CLOUD_PLAN_CACHE_PATH)
    assert json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"] == "trial"


def test_update_trial_state_upgrade_free_to_trial_flips_cache(sync):
    """free -> trial within one heartbeat writes the entitled tier so paid
    runtimes flip on without a daemon restart."""
    sync._update_trial_state({"sync_allowed": True, "plan": "free"})
    assert json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"] == "cloud_free"
    sync._update_trial_state({"sync_allowed": True, "plan": "trial", "trial_days_left": 7})
    assert json.loads(open(sync._CLOUD_PLAN_CACHE_PATH).read())["plan"] == "trial"
