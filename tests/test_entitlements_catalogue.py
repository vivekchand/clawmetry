"""Tests for the entitlement catalogue + per-tier retention.

These pin the catalogue to what /pricing on clawmetry.com promises so any
drift between catalogue and pricing page is caught in CI. Companion to
tests/test_entitlements.py (which covers grace/enforce mechanics).
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


# ── catalogue shape locks ─────────────────────────────────────────────────────


def test_starter_features_match_pricing(ent):
    """Starter card on /pricing promises these exact 7 keys."""
    expected = frozenset({
        "multi_runtime",
        "fleet",
        "cloud_sync",
        "all_channels",
        "approval_queue",
        "budget_limits",
        "per_runtime_health_timeline",
    })
    assert ent.STARTER_FEATURES == expected


def test_pro_only_features_include_published_pro_set(ent):
    """Pro card on /pricing puts these features above Starter."""
    must_have = {
        "per_run_waste_flags",
        "per_run_compare",
        "error_triage",
        "self_evolve",
        "asset_registry",
        "eval_suite",
        "tool_policy",
        "otel_export",
        "custom_webhooks",
        "custom_runtime_ingest",
    }
    assert must_have.issubset(ent.PRO_ONLY_FEATURES)


def test_enterprise_features_match_pricing(ent):
    """Enterprise card on /pricing promises these exact 6 keys."""
    expected = frozenset({
        "siem_export",
        "sso",
        "audit_logs",
        "rbac",
        "air_gapped_license",
        "custom_data_residency",
    })
    assert ent.ENTERPRISE_FEATURES == expected


def test_paid_features_is_starter_plus_pro_only(ent):
    assert ent.PAID_FEATURES == ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES


def test_otel_export_is_pro_not_enterprise(ent):
    """otel_export was moved from Enterprise → Pro to match /pricing."""
    assert "otel_export" in ent.PRO_ONLY_FEATURES
    assert "otel_export" not in ent.ENTERPRISE_FEATURES


def test_siem_export_is_enterprise(ent):
    """siem_export is an Enterprise-only feature added 2026-05-29."""
    assert "siem_export" in ent.ENTERPRISE_FEATURES
    assert "siem_export" not in ent.PAID_FEATURES


def test_disjoint_tier_buckets(ent):
    """A feature key never appears in two tier buckets simultaneously."""
    assert ent.STARTER_FEATURES.isdisjoint(ent.PRO_ONLY_FEATURES)
    assert ent.PAID_FEATURES.isdisjoint(ent.ENTERPRISE_FEATURES)
    assert ent.FREE_FEATURES.isdisjoint(ent.PAID_FEATURES)
    assert ent.FREE_FEATURES.isdisjoint(ent.ENTERPRISE_FEATURES)


def test_all_features_is_union(ent):
    assert ent.ALL_FEATURES == ent.FREE_FEATURES | ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES


# ── per-tier feature grants ────────────────────────────────────────────────────


def test_cloud_starter_grants_starter_only(ent, monkeypatch, tmp_path):
    import json

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
    en = ent.get_entitlement(force=True)
    # Starter features pass.
    assert en.allows_feature("multi_runtime") is True
    assert en.allows_feature("budget_limits") is True
    # Pro-only features don't.
    assert en.allows_feature("self_evolve") is False
    assert en.allows_feature("otel_export") is False


def test_cloud_pro_grants_starter_plus_pro(ent, monkeypatch, tmp_path):
    import json

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    en = ent.get_entitlement(force=True)
    assert en.allows_feature("multi_runtime") is True       # starter
    assert en.allows_feature("self_evolve") is True         # pro
    assert en.allows_feature("otel_export") is True         # pro
    assert en.allows_feature("siem_export") is False        # enterprise-only


def test_enterprise_grants_everything_paid(ent, monkeypatch, tmp_path):
    import json

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise"}))
    en = ent.get_entitlement(force=True)
    assert en.allows_feature("siem_export") is True
    assert en.allows_feature("sso") is True
    assert en.allows_feature("self_evolve") is True
    assert en.allows_feature("multi_runtime") is True


# ── per-tier retention ─────────────────────────────────────────────────────────


def test_retention_oss_is_seven_days(ent):
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() == 7


def test_retention_starter_is_thirty(ent, monkeypatch, tmp_path):
    import json

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() == 30


def test_retention_pro_is_ninety(ent, monkeypatch, tmp_path):
    import json

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() == 90


def test_retention_enterprise_is_unlimited(ent, monkeypatch, tmp_path):
    import json

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise"}))
    en = ent.get_entitlement(force=True)
    assert en.event_retention_days() is None
