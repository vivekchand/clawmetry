"""Tests for ``Entitlement.days_until_expiry()`` / ``expires_within()``.

These helpers are pure display/alerting helpers — they do not influence the
gate decision (``allows_runtime`` / ``allows_feature``), so the headline
invariant is "adding them changes no current behaviour" and the wire-shape
addition (``to_dict()["days_until_expiry"]``) is a purely additive key.

The tests pin:
  * Perpetual entitlements (``expiry is None``) -> ``None`` / ``False``.
  * Already-expired entitlements collapse to ``0`` (not negative).
  * Future expiry returns the floor in days.
  * Sub-day expiry (12 hours) returns ``0`` (floor).
  * ``expires_within`` threshold semantics + clamping of negative thresholds.
  * Defensive: non-numeric ``expiry`` returns ``None`` without raising.
  * ``to_dict()`` carries the new key with the right type.
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default — these helpers are read-only and grace-mode-agnostic, but the
    fixture mirrors the existing tests/test_entitlements.py pattern."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── days_until_expiry ────────────────────────────────────────────────────────


def test_perpetual_entitlement_returns_none(ent):
    en = ent.get_entitlement(force=True)
    assert en.expiry is None
    assert en.days_until_expiry() is None


def test_expired_entitlement_collapses_to_zero(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() - 3600})
    )
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.days_until_expiry() == 0


def test_five_days_in_future_returns_five(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    # 5 full days + 1 hour of slack so floor still yields 5 even if the test
    # straddles a second boundary.
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (5 * 86400) + 3600}
        )
    )
    en = ent.get_entitlement(force=True)
    assert en.days_until_expiry() == 5


def test_sub_day_expiry_floors_to_zero(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (12 * 3600)})
    )
    en = ent.get_entitlement(force=True)
    # 12 hours from now -> 0 full days (the UI should round its own display).
    assert en.days_until_expiry() == 0
    # And the entitlement is *not* yet expired.
    assert en.expired is False


def test_exactly_one_day_left(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + 86400 + 60}
        )
    )
    en = ent.get_entitlement(force=True)
    assert en.days_until_expiry() == 1


def test_non_numeric_expiry_defensive_fallback(ent):
    # The dataclass is frozen but ``dataclasses.replace`` honours the type
    # contract; we explicitly inject a broken value to confirm the helper
    # swallows it rather than crashing a render path.
    en = ent.get_entitlement(force=True)
    broken = dataclasses.replace(en, expiry="not-a-number")  # type: ignore[arg-type]
    assert broken.days_until_expiry() is None
    assert broken.expires_within(30) is False


# ── expires_within ───────────────────────────────────────────────────────────


def test_expires_within_perpetual_is_false(ent):
    en = ent.get_entitlement(force=True)
    assert en.expires_within(0) is False
    assert en.expires_within(7) is False
    assert en.expires_within(365) is False


def test_expires_within_already_expired_is_true(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() - 60})
    )
    en = ent.get_entitlement(force=True)
    assert en.expires_within(0) is True
    assert en.expires_within(7) is True


def test_expires_within_threshold_inclusive(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    # ~6 days out -> within 7-day banner threshold, outside 5-day.
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (6 * 86400) + 3600}
        )
    )
    en = ent.get_entitlement(force=True)
    assert en.days_until_expiry() == 6
    assert en.expires_within(7) is True
    assert en.expires_within(6) is True
    assert en.expires_within(5) is False


def test_expires_within_negative_threshold_clamped(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    # 5 days out + slack: comfortably beyond the clamped-to-zero threshold.
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (5 * 86400) + 3600}
        )
    )
    en = ent.get_entitlement(force=True)
    # Negative threshold clamps to 0 -> only "already expired" satisfies it,
    # and this entitlement isn't expired, so False.
    assert en.expires_within(-5) is False
    assert en.expires_within(-1) is False


def test_expires_within_nonnumeric_threshold_is_false(ent):
    en = ent.get_entitlement(force=True)
    assert en.expires_within("seven") is False  # type: ignore[arg-type]


# ── to_dict wire shape ────────────────────────────────────────────────────────


def test_to_dict_perpetual_carries_null(ent):
    d = ent.get_entitlement(force=True).to_dict()
    assert "days_until_expiry" in d
    assert d["days_until_expiry"] is None


def test_to_dict_finite_carries_int(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (10 * 86400) + 3600}
        )
    )
    d = ent.get_entitlement(force=True).to_dict()
    assert isinstance(d["days_until_expiry"], int)
    assert d["days_until_expiry"] == 10


def test_to_dict_expired_carries_zero(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() - 1})
    )
    d = ent.get_entitlement(force=True).to_dict()
    assert d["expired"] is True
    assert d["days_until_expiry"] == 0


# ── grace-mode contract: these helpers are display-only ──────────────────────


def test_helpers_do_not_affect_gate_decisions(ent, monkeypatch, tmp_path):
    """The new helpers are display-only; ``allows_runtime`` / ``allows_feature``
    still resolve identically. Pins the "no current behaviour change"
    contract that the rollout phase requires."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {"plan": "cloud_pro", "node_limit": 1, "expiry": time.time() + (20 * 86400) + 3600}
        )
    )
    en = ent.get_entitlement(force=True)
    # Helpers report something useful…
    assert en.days_until_expiry() == 20
    assert en.expires_within(30) is True
    # …but the underlying gate decisions are unchanged.
    assert en.allows_runtime("claude_code") is True
    assert en.allows_feature("self_evolve") is True
