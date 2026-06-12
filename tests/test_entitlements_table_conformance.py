"""Catalogue-table conformance tests for ``clawmetry/entitlements.py``.

Pins invariants that the existing entitlements suites do not cover and that
silently regress today:

* ``_TIER_FEATURES`` and ``_TIER_RETENTION_DAYS`` register a row for *every*
  public ``TIER_*`` constant. A future PR that adds ``TIER_FOO`` without
  registering it falls through ``dict.get(..., frozenset())`` / ``dict.get(..., 7)``
  and silently downgrades the new tier to free-tier feature grants and 7-day
  retention — visible nowhere until a customer reports missing data.

* ``Entitlement.to_dict()`` is ``json.dumps``-able for every tier. The dashboard
  route ``/api/entitlement`` wraps the call in a never-raise fallback that
  returns an OSS-free shape, so a non-serialisable type leaking into ``to_dict()``
  (e.g. a stray ``frozenset``) silently masks the real entitlement.

* ``allows_feature`` / ``allows_runtime`` for an unknown id are allowed in grace
  (matches the documented "grace allows everything" contract) but blocked once
  enforcement is on (matches the "deny-by-default for unknown keys" posture so a
  typo in a route gate can't silently leak access).

* ``event_retention_days()`` always returns ``None`` or a positive ``int`` —
  never ``0`` (which would prune everything on the next sweep) and never a
  negative value.

Tests-only, never-raise, GRACE-safe — no production code is touched.
"""
from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default (the tests opt in per-case)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _public_tier_constants(mod):
    """Every ``TIER_*`` string constant the module exports."""
    return [
        getattr(mod, name)
        for name in dir(mod)
        if name.startswith("TIER_") and isinstance(getattr(mod, name), str)
    ]


# ── per-tier tables cover every public tier constant ────────────────────────


def test_tier_features_table_covers_every_public_tier_constant(ent):
    tiers = _public_tier_constants(ent)
    assert tiers, "no TIER_* constants exported"
    missing = [t for t in tiers if t not in ent._TIER_FEATURES]
    assert not missing, (
        f"_TIER_FEATURES has no row for: {missing}. "
        "A tier without an explicit grant falls through to free-tier features "
        "via dict.get(..., frozenset()) and silently under-grants."
    )


def test_tier_retention_table_covers_every_public_tier_constant(ent):
    tiers = _public_tier_constants(ent)
    missing = [t for t in tiers if t not in ent._TIER_RETENTION_DAYS]
    assert not missing, (
        f"_TIER_RETENTION_DAYS has no row for: {missing}. "
        "A tier without an explicit retention falls through to "
        "dict.get(..., 7) and silently caps the new tier at 7 days."
    )


# ── to_dict() JSON round-trip ───────────────────────────────────────────────


def test_to_dict_is_json_serializable_for_every_tier(ent, monkeypatch, tmp_path):
    """A non-serialisable value leaking into ``to_dict()`` (e.g. a frozenset)
    breaks ``/api/entitlement`` — but the route's never-raise fallback hides
    the failure, so the regression goes undetected until a Cloud feature
    reads the entitlement directly. Pin every tier here."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    for tier in _public_tier_constants(ent):
        cache.write_text(json.dumps({"plan": tier, "node_limit": 3, "expiry": None}))
        en = ent.get_entitlement(force=True)
        d = en.to_dict()
        # Round-trip must produce identical primitive JSON (no set/frozenset slip).
        roundtripped = json.loads(json.dumps(d))
        assert roundtripped == d, f"{tier}: to_dict() did not round-trip cleanly"


# ── unknown feature / runtime ids ───────────────────────────────────────────


def test_unknown_feature_is_blocked_under_enforce(ent, monkeypatch):
    """A typo in a route-level ``@gate("feeture_x")`` decorator must NOT
    silently behave as allowed. Under enforce, an unknown id is blocked."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_feature("definitely_not_a_real_feature_id_xyzzy") is False


def test_unknown_feature_is_allowed_in_grace(ent):
    """Grace mode allows everything by contract — including unknown ids. The
    inverse (under enforce) is pinned by the test above."""
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.allows_feature("definitely_not_a_real_feature_id_xyzzy") is True


def test_unknown_runtime_is_blocked_under_enforce(ent, monkeypatch):
    """A typo in a runtime adapter id must not silently observe a runtime the
    plan does not grant. Under enforce + OSS, an unknown runtime is blocked."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.allows_runtime("brand_new_unknown_runtime") is False


def test_unknown_runtime_is_allowed_in_grace(ent):
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.allows_runtime("brand_new_unknown_runtime") is True


# ── retention values are well-formed for every tier ─────────────────────────


def test_event_retention_days_is_positive_int_or_none_for_every_tier(
    ent, monkeypatch, tmp_path
):
    """A regression that set a tier's retention to 0 / -1 would silently prune
    every event on the next sync sweep. Pin per-tier that the value is either
    ``None`` (unlimited) or a positive integer."""
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    for tier in _public_tier_constants(ent):
        cache.write_text(json.dumps({"plan": tier, "node_limit": 1, "expiry": None}))
        en = ent.get_entitlement(force=True)
        days = en.event_retention_days()
        if days is None:
            continue
        assert isinstance(days, int) and days > 0, (
            f"{tier}: event_retention_days() must be a positive int or None, got {days!r}"
        )
