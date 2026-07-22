"""Tests for ``dashboard._is_pro_user()`` self-hosted signed-license branch.

The helper originally returned True only for cm_-authed cloud-paired nodes
with a cached Pro plan. Self-hosted paid licensees (source="license", tier
in {pro, cloud_pro, trial, enterprise}) were treated as Free, so per-agent
Telegram alert fan-out and auto-pause never fired for customers who had
already paid.

These tests pin:
  * The signed-license branch flips True for every Pro-equivalent tier.
  * TIER_CLOUD_STARTER stays False (Starter has no Pro-only features and
    the auto-pause / Telegram-dispatch code paths gated by this helper
    are Pro-only in ``project_alerts_pro_feature.md``).
  * The pre-existing cm_ + cached-plan path is unchanged (True for
    cloud_pro/pro/trial, False otherwise).
  * Any exception in the entitlements read fails closed to False so a
    flaky lookup never leaks paid dispatch onto a free node.

Sibling of the #3755 pattern (``_evaluate_alerts_local`` +
``_approvals_local_blocking_watcher``), both of which added the same
``entitlements.get_entitlement()`` normalisation for signed-license
self-hosted nodes.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def dash(monkeypatch, tmp_path):
    """Fresh dashboard + entitlements modules with HOME pointed at a
    disposable tmp dir so ~/.clawmetry/* lookups are hermetic."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    # Reload entitlements first so its module-level _LICENSE_PATH picks up
    # the new HOME (the path is captured at import time).
    import importlib

    import clawmetry.entitlements as _ent

    importlib.reload(_ent)
    _ent.invalidate()

    import dashboard as _d

    # The plan cache is a module global; reset it so cross-test leakage
    # from other suites can't taint _is_pro_user's second read path.
    _d._cloud_plan_cache = {}
    yield _d
    _ent.invalidate()


def _stub_no_token(monkeypatch, dash):
    """Force the cm_ path to fail (no token on disk)."""
    monkeypatch.setattr(dash, "_read_cloud_token", lambda: "")


def _stub_cm_token_with_plan(monkeypatch, dash, plan: str):
    """Force the cm_ path: token present + given plan cached."""
    monkeypatch.setattr(dash, "_read_cloud_token", lambda: "cm_test_token")
    dash._cloud_plan_cache = {"plan": plan}


def _stub_entitlement(monkeypatch, dash, *, tier: str, source: str):
    """Force ``get_entitlement()`` to return a canned Entitlement."""
    from clawmetry import entitlements as _ent

    ent = _ent._build(tier, source)
    monkeypatch.setattr(_ent, "get_entitlement", lambda force=False: ent)


# ── License branch ────────────────────────────────────────────────────────


@pytest.mark.parametrize("tier", ["pro", "cloud_pro", "trial", "enterprise"])
def test_signed_license_pro_equivalent_tiers_are_pro(monkeypatch, dash, tier):
    """A signed self-hosted license on a Pro-equivalent tier flips True
    even when no cm_ token / cached plan is present."""
    _stub_no_token(monkeypatch, dash)
    _stub_entitlement(monkeypatch, dash, tier=tier, source="license")
    assert dash._is_pro_user() is True


def test_signed_license_starter_is_not_pro(monkeypatch, dash):
    """TIER_CLOUD_STARTER is a paid tier but doesn't unlock Pro-only
    features (auto-pause, Telegram fan-out). The gate must stay False."""
    _stub_no_token(monkeypatch, dash)
    _stub_entitlement(monkeypatch, dash, tier="cloud_starter", source="license")
    assert dash._is_pro_user() is False


def test_cloud_source_pro_tier_alone_does_not_flip_license_branch(monkeypatch, dash):
    """The license branch only fires for ``source == "license"``. A
    cloud-sourced entitlement (source="cloud") still routes through the
    cm_ + cached-plan path — with no cm_ token here, that returns False."""
    _stub_no_token(monkeypatch, dash)
    _stub_entitlement(monkeypatch, dash, tier="cloud_pro", source="cloud")
    assert dash._is_pro_user() is False


def test_oss_free_entitlement_is_not_pro(monkeypatch, dash):
    """No license + no cm_ token → OSS free entitlement → not pro."""
    _stub_no_token(monkeypatch, dash)
    # Default get_entitlement() with HOME pointed at empty tmp dir already
    # returns the OSS-free entitlement; don't stub it out here.
    assert dash._is_pro_user() is False


def test_entitlement_lookup_exception_fails_closed(monkeypatch, dash):
    """A raising entitlements resolver must NOT flip the gate True."""
    _stub_no_token(monkeypatch, dash)
    from clawmetry import entitlements as _ent

    def _boom(force=False):
        raise RuntimeError("entitlements is unhappy")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    assert dash._is_pro_user() is False


# ── Pre-existing cm_ + cached-plan branch (behaviour preservation) ────────


@pytest.mark.parametrize("plan", ["cloud_pro", "pro", "trial"])
def test_cm_token_plus_pro_plan_still_flips_true(monkeypatch, dash, plan):
    """The original cm_ + cached-plan path must be unchanged."""
    _stub_cm_token_with_plan(monkeypatch, dash, plan)
    # Ensure the license branch is inert so we prove the cm_ path fires.
    _stub_entitlement(monkeypatch, dash, tier="oss", source="oss")
    assert dash._is_pro_user() is True


@pytest.mark.parametrize("plan", ["free", "cloud_free", "cloud_starter", ""])
def test_cm_token_plus_non_pro_plan_still_stays_false(monkeypatch, dash, plan):
    """Non-Pro cached plans (including Starter) must not flip the gate."""
    _stub_cm_token_with_plan(monkeypatch, dash, plan)
    _stub_entitlement(monkeypatch, dash, tier="oss", source="oss")
    assert dash._is_pro_user() is False


def test_no_cm_token_and_oss_entitlement_is_not_pro(monkeypatch, dash):
    """Belt-and-braces: no token, no license → False (fail-closed)."""
    monkeypatch.setattr(dash, "_read_cloud_token", lambda: None)
    _stub_entitlement(monkeypatch, dash, tier="oss", source="oss")
    assert dash._is_pro_user() is False
