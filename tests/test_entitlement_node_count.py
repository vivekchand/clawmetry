"""Tests for :meth:`Entitlement.allows_node_count` -- the third corner of the
open-core gating triad (alongside :meth:`allows_runtime` /
:meth:`allows_feature`).

Pins the grace/enforce posture, the expiry collapse, the unlimited sentinel
for Enterprise grants, and the defensive never-crash behaviour on bad input.
Companion to ``tests/test_entitlements.py`` (general grace mechanics) and
``tests/test_entitlements_catalogue.py`` (per-tier buckets).
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


def test_grace_allows_any_node_count(ent):
    """Grace mode (default) mirrors ``allows_runtime`` / ``allows_feature``:
    nothing is ever blocked, regardless of node_limit. This is the headline
    invariant the rollout depends on -- wiring this helper into fleet routes
    must not change current behaviour before the enforce phase."""
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    for count in (0, 1, 2, 5, 100, 10_000):
        assert en.allows_node_count(count) is True, count


def test_grace_allows_count_above_explicit_node_limit(ent):
    """Even when an Entitlement is constructed with a low node_limit, grace
    mode short-circuits and allows the request."""
    en = ent._build(ent.TIER_OSS, "oss", node_limit=1)
    assert en.grace is True
    assert en.allows_node_count(50) is True


# -- enforce mode: limits actually apply --------------------------------------


def test_enforce_oss_caps_at_one_node(ent, monkeypatch):
    """OSS free in enforce mode is a single-node grant -- extra registered
    nodes fail the check."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.node_limit == 1
    assert en.allows_node_count(1) is True
    assert en.allows_node_count(2) is False
    assert en.allows_node_count(99) is False


def test_enforce_cloud_pro_respects_payload_node_limit(ent, monkeypatch, tmp_path):
    """A cloud_pro plan with ``node_limit=10`` allows up to 10 and blocks 11."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 10}))
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_PRO
    assert en.node_limit == 10
    assert en.allows_node_count(1) is True
    assert en.allows_node_count(10) is True
    assert en.allows_node_count(11) is False


def test_enforce_enterprise_unlimited_when_node_limit_is_zero(ent, monkeypatch):
    """An Enterprise grant with ``node_limit=0`` is the unlimited sentinel --
    keeps the wire format unchanged (license payloads use ``nodes=0`` /
    omit ``nodes`` for unlimited). Negative values are treated the same way
    as a defensive measure."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent._build(ent.TIER_ENTERPRISE, "license", node_limit=0)
    assert en.grace is False
    assert en.allows_node_count(1) is True
    assert en.allows_node_count(10_000) is True
    en_neg = ent._build(ent.TIER_ENTERPRISE, "license", node_limit=-1)
    assert en_neg.allows_node_count(99) is True


# -- expiry: collapse to single node ------------------------------------------


def test_enforce_expired_paid_plan_collapses_to_single_node(ent, monkeypatch, tmp_path):
    """An expired paid plan should behave like OSS-free for node-count checks
    too -- same posture as :meth:`allows_runtime`, which drops back to
    free-runtimes-only on expiry."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({
        "plan": "cloud_pro",
        "node_limit": 25,
        "expiry": time.time() - 60,
    }))
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_node_count(1) is True
    assert en.allows_node_count(2) is False


# -- edge cases ---------------------------------------------------------------


def test_enforce_zero_and_negative_current_always_allowed(ent, monkeypatch):
    """``current=0`` (no nodes registered yet) and stray negative values
    should never be the thing that blocks a request -- this matches the
    never-crash posture of the rest of the entitlements module."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_node_count(0) is True
    assert en.allows_node_count(-1) is True
    assert en.allows_node_count(-100) is True


def test_enforce_non_int_current_is_swallowed(ent, monkeypatch):
    """A non-int ``current`` (e.g. a stray ``None`` / string from a fleet
    table read) must not crash the check -- falls through to allowed so a
    flaky read never blocks a request path."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_node_count(None) is True
    assert en.allows_node_count("not-a-number") is True
    assert en.allows_node_count(object()) is True


def test_enforce_string_int_current_is_accepted(ent, monkeypatch):
    """A numeric string (``"3"``) coerces cleanly. Defensive convenience --
    a fleet count read from a query string parameter is already a str."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_node_count("1") is True
    assert en.allows_node_count("2") is False  # OSS caps at 1


# -- triad consistency: matches allows_runtime / allows_feature posture ------


def test_grace_triad_is_symmetric(ent):
    """In grace mode every gate corner returns True for any input -- the
    rollout invariant the dashboard / fleet / runtime ingest all depend on."""
    en = ent.get_entitlement(force=True)
    assert en.allows_runtime("claude_code") is True
    assert en.allows_feature("self_evolve") is True
    assert en.allows_node_count(999) is True
