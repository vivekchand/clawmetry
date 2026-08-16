"""Tests for the OSS side of org-wide Claude coverage.

The feature answers what local ingest structurally cannot: what an org runs on
Claude surfaces that never touch this disk (claude.ai chat, Cowork's cloud
workspaces, Claude in Chrome). The implementation reads Anthropic's Enterprise
Analytics API and lives in the private ``clawmetry-pro`` package; public OSS
carries the catalogue key plus a 402 stub at the same URLs.

Pins:
- ``org_analytics`` is an Enterprise feature (the upstream API is Enterprise
  only, so gating it lower would sell a key the customer's plan cannot mint)
- every stub endpoint returns the shared 402 ``upgrade_required`` envelope
- the stub blueprint's name + URL rules match the Pro impl exactly, so the
  swap is transparent when clawmetry-pro is installed
"""
from __future__ import annotations

import pytest
from flask import Flask

from clawmetry import entitlements
from routes.org_analytics import bp_org_analytics


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(bp_org_analytics)
    return app.test_client()


# ── catalogue ────────────────────────────────────────────────────────────────


def test_org_analytics_is_an_enterprise_feature():
    assert "org_analytics" in entitlements.ENTERPRISE_FEATURES
    assert "org_analytics" in entitlements.ALL_FEATURES
    # Not sold on any lower tier — the upstream API would reject the key.
    assert "org_analytics" not in entitlements.FREE_FEATURES
    assert "org_analytics" not in entitlements.PAID_FEATURES


def test_only_enterprise_tier_unlocks_it():
    for tier, feats in entitlements._TIER_FEATURES.items():
        if tier == entitlements.TIER_ENTERPRISE:
            assert "org_analytics" in feats
        else:
            assert "org_analytics" not in feats, tier


# ── stub ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/org-analytics"),
        ("get", "/api/org-analytics/key"),
        ("post", "/api/org-analytics/key"),
    ],
)
def test_stub_returns_upgrade_required(client, method, path):
    resp = getattr(client, method)(path)
    assert resp.status_code == 402
    body = resp.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "org_analytics"
    # The card branches on the hint being present; an empty one renders a
    # locked box with no explanation.
    assert body.get("hint")


def test_stub_never_echoes_a_posted_key(client):
    """A key posted to the OSS stub must not come back in the 402 body."""
    resp = client.post("/api/org-analytics/key", json={"key": "sk-ant-secret"})
    assert resp.status_code == 402
    assert "sk-ant-secret" not in resp.get_data(as_text=True)


def test_blueprint_name_matches_the_pro_impl():
    # clawmetry_pro/routes/org_analytics.py registers the same name; a mismatch
    # would let both register and silently shadow one another.
    assert bp_org_analytics.name == "org_analytics"
