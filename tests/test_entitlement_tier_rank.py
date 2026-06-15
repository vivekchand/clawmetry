"""Tests for ``tier_rank()`` + ``Entitlement.is_at_least()``.

Ordinal tier ranking is the primitive ``_gate`` and the UI use to ask "is this
install at least Pro?" without re-encoding the pricing ladder in every caller.
The headline invariants:

* Every known tier has a non-negative rank; unknown tier strings rank as -1.
* The ladder is monotonic: OSS < Cloud Free < Cloud Starter < Pro <= Enterprise.
* Tiers that share a feature set share a rank (Trial / Cloud Pro / self-hosted
  Pro all rank 3 -- they all unlock the full Pro feature set).
* ``is_at_least`` is GRACE-INDEPENDENT -- it reports a plan fact, not a gate
  decision, so the result does not change when ``CLAWMETRY_ENFORCE`` flips.
* The ``rank`` field is exposed on ``to_dict()`` so the dashboard / API
  consumers can drive UI affordances off the same number.
"""
from __future__ import annotations

import importlib

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


# -- tier_rank() -------------------------------------------------------------


def test_tier_rank_known_tiers_are_non_negative(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert ent.tier_rank(tier) >= 0, tier


def test_tier_rank_unknown_is_minus_one(ent):
    assert ent.tier_rank("nonsense") == -1
    assert ent.tier_rank("") == -1
    assert ent.tier_rank(None) == -1  # type: ignore[arg-type]


def test_tier_rank_ladder_monotonic(ent):
    assert ent.tier_rank(ent.TIER_OSS) < ent.tier_rank(ent.TIER_CLOUD_FREE)
    assert ent.tier_rank(ent.TIER_CLOUD_FREE) < ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert ent.tier_rank(ent.TIER_CLOUD_STARTER) < ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert ent.tier_rank(ent.TIER_CLOUD_PRO) < ent.tier_rank(ent.TIER_ENTERPRISE)


def test_tier_rank_pro_tiers_tied(ent):
    """Trial / Cloud Pro / self-hosted Pro all grant the same feature set, so
    they share a rank -- gating "at least Pro" must accept all three."""
    r = ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert ent.tier_rank(ent.TIER_TRIAL) == r
    assert ent.tier_rank(ent.TIER_PRO) == r


def test_tier_rank_is_case_insensitive(ent):
    assert ent.tier_rank("PRO") == ent.tier_rank(ent.TIER_PRO)
    assert ent.tier_rank("  enterprise  ") == ent.tier_rank(ent.TIER_ENTERPRISE)


# -- Entitlement.is_at_least() -----------------------------------------------


def test_is_at_least_oss_satisfies_only_oss(ent):
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS
    assert en.is_at_least(ent.TIER_OSS) is True
    assert en.is_at_least(ent.TIER_CLOUD_STARTER) is False
    assert en.is_at_least(ent.TIER_PRO) is False
    assert en.is_at_least(ent.TIER_ENTERPRISE) is False


def test_is_at_least_pro_satisfies_starter_and_pro(ent):
    pro = ent._build(ent.TIER_PRO, "license")
    assert pro.is_at_least(ent.TIER_OSS) is True
    assert pro.is_at_least(ent.TIER_CLOUD_STARTER) is True
    assert pro.is_at_least(ent.TIER_PRO) is True
    assert pro.is_at_least(ent.TIER_ENTERPRISE) is False


def test_is_at_least_enterprise_satisfies_everything(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
        ent.TIER_ENTERPRISE,
    ):
        assert e.is_at_least(tier) is True, tier


def test_is_at_least_unknown_min_tier_is_false(ent):
    pro = ent._build(ent.TIER_PRO, "license")
    assert pro.is_at_least("nonsense") is False
    assert pro.is_at_least("") is False


def test_is_at_least_is_grace_independent(ent, monkeypatch):
    """is_at_least reports a plan fact, not a gate decision -- it must NOT
    flip with the grace/enforce switch the way allows_* does."""
    oss = ent.get_entitlement(force=True)
    assert oss.is_at_least(ent.TIER_PRO) is False
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    oss2 = ent.get_entitlement(force=True)
    assert oss2.is_at_least(ent.TIER_PRO) is False  # unchanged


# -- to_dict() ---------------------------------------------------------------


def test_to_dict_includes_rank(ent):
    en = ent.get_entitlement(force=True)
    d = en.to_dict()
    assert "rank" in d
    assert d["rank"] == ent.tier_rank(en.tier)
    assert d["rank"] == 0  # OSS


def test_to_dict_rank_matches_pro_tier(ent):
    pro = ent._build(ent.TIER_PRO, "license")
    d = pro.to_dict()
    assert d["tier"] == ent.TIER_PRO
    assert d["rank"] == ent.tier_rank(ent.TIER_PRO)
    assert d["rank"] > 0
