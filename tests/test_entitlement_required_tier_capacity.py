"""Tests for the capacity-axis branches of ``GET /api/entitlement/required-tier``.

The Python helpers :func:`clawmetry.entitlements.min_tier_for_channel_count` and
:func:`clawmetry.entitlements.min_tier_for_retention_window` already close the
symmetry with :func:`min_tier_for_feature` / :func:`min_tier_for_runtime`
(see ``tests/test_entitlements_min_tier_capacity.py``). This file pins the
HTTP wrapper so the same endpoint answers all four "what tier do I need" axes
off one URL, and a future param rename / shape drift fails loudly here.

Companion to ``tests/test_entitlement_api.py`` (feature / runtime branches).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement and a clean HOME so the
    resolver collapses to OSS-free deterministically. Mirrors the fixture in
    ``tests/test_entitlement_api.py``."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── channels= branch ─────────────────────────────────────────────────────────


def test_channels_within_free_cap_resolves_to_oss(client):
    """1/2/3 channels fit on OSS (free cap = 3). Grace pass-through keeps
    ``allowed`` True."""
    resp = client.get("/api/entitlement/required-tier?channels=3")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["kind"] == "channels"
    assert d["key"] == "3"
    assert d["required_tier"] == "oss"
    assert d["required_tier_label"] == "OSS"
    assert d["required_tier_rank"] == 0
    assert d["allowed"] is True
    assert d["upgrade_required"] is False


def test_channels_over_free_cap_resolves_to_starter(client):
    """4+ channels require Starter -- the cheapest tier with channel_limit
    set to None (unlimited)."""
    d = client.get("/api/entitlement/required-tier?channels=21").get_json()
    assert d["kind"] == "channels"
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["required_tier_rank"] == 1


def test_channels_grace_keeps_allowed_true_even_over_cap(client):
    """The headline grace invariant -- wiring this endpoint must not change
    current behaviour. ``allowed`` is True for any count in grace mode."""
    d = client.get("/api/entitlement/required-tier?channels=999").get_json()
    assert d["allowed"] is True


def test_channels_non_int_swallows_to_required_none(client):
    """A non-int ``channels`` is swallowed by ``min_tier_for_channel_count``
    (which returns None). The HTTP wrapper inherits the never-crash posture --
    ``required_tier`` is None and the body still well-formed."""
    d = client.get("/api/entitlement/required-tier?channels=abc").get_json()
    assert d["kind"] == "channels"
    assert d["key"] == "abc"
    assert d["required_tier"] is None
    assert d["required_tier_label"] is None
    assert d["upgrade_required"] is False


def test_channels_blank_value_is_swallowed(client):
    """``?channels=`` (present but empty) parses to None, not to "fell
    through to a feature/runtime branch". The body returns required_tier
    None, kind="channels"."""
    d = client.get("/api/entitlement/required-tier?channels=").get_json()
    assert d["kind"] == "channels"
    assert d["required_tier"] is None


# ── retention_days= branch ───────────────────────────────────────────────────


def test_retention_seven_days_fits_oss(client):
    """7d fits the OSS cap (7d). Available on the free floor."""
    d = client.get("/api/entitlement/required-tier?retention_days=7").get_json()
    assert d["kind"] == "retention_days"
    assert d["key"] == "7"
    assert d["required_tier"] == "oss"


def test_retention_thirty_days_requires_starter(client):
    """30d needs Starter -- the cheapest tier whose retention cap admits it."""
    d = client.get("/api/entitlement/required-tier?retention_days=30").get_json()
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"


def test_retention_ninety_days_requires_pro(client):
    """90d needs Pro -- the next tier up after Starter (30d cap)."""
    d = client.get("/api/entitlement/required-tier?retention_days=90").get_json()
    assert d["required_tier"] == "cloud_pro"
    assert d["required_tier_label"] == "Pro"


def test_retention_over_pro_cap_requires_enterprise(client):
    """365d exceeds every finite cap -- only Enterprise admits it (unlimited
    sentinel)."""
    d = client.get("/api/entitlement/required-tier?retention_days=365").get_json()
    assert d["required_tier"] == "enterprise"
    assert d["required_tier_label"] == "Enterprise"


def test_retention_zero_collapses_to_oss(client):
    """retention_days=0 means "no history" -- trivially satisfied by the free
    floor. Mirrors :func:`min_tier_for_retention_window`."""
    d = client.get("/api/entitlement/required-tier?retention_days=0").get_json()
    assert d["required_tier"] == "oss"


def test_retention_non_int_returns_none(client):
    """A non-int ``retention_days`` swallows to required_tier=None -- the
    never-crash posture inherited from the underlying helper."""
    d = client.get("/api/entitlement/required-tier?retention_days=notanumber").get_json()
    assert d["kind"] == "retention_days"
    assert d["required_tier"] is None


# ── validation: exactly-one-param ────────────────────────────────────────────


def test_400_when_no_params_supplied(client):
    """Same posture as the existing feature/runtime branches -- empty query
    is a 400, not a silent 200."""
    resp = client.get("/api/entitlement/required-tier")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body
    assert "channels" in body["error"]
    assert "retention_days" in body["error"]


@pytest.mark.parametrize(
    "qs",
    [
        "feature=self_evolve&channels=5",
        "runtime=claude_code&retention_days=30",
        "channels=5&retention_days=30",
        "feature=self_evolve&runtime=claude_code&channels=5",
    ],
)
def test_400_when_multiple_params_supplied(client, qs):
    """Mixing axes is a 400 -- the same exactly-one-axis contract the
    original feature/runtime check enforced, extended to the capacity axes."""
    resp = client.get(f"/api/entitlement/required-tier?{qs}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ── feature / runtime branches still work after the refactor ────────────────


def test_feature_branch_unchanged(client):
    """Regression guard -- adding the capacity branches must not break the
    existing feature= response shape."""
    d = client.get("/api/entitlement/required-tier?feature=self_evolve").get_json()
    assert d["kind"] == "feature"
    assert d["key"] == "self_evolve"
    assert d["required_tier"] == "cloud_pro"
    assert d["required_tier_label"] == "Pro"


def test_runtime_branch_unchanged(client):
    """Regression guard for runtime= -- same shape as before the refactor."""
    d = client.get("/api/entitlement/required-tier?runtime=claude_code").get_json()
    assert d["kind"] == "runtime"
    assert d["key"] == "claude_code"
    assert d["required_tier"] == "cloud_starter"


# ── enforce mode: allowed reflects current entitlement ──────────────────────


def test_enforce_channels_over_cap_marks_not_allowed(client, monkeypatch):
    """Under enforce, an OSS install at 5 channels (over the free cap) sees
    ``allowed=False`` -- the gate axis is wired through, just inert in grace."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    e.invalidate()
    d = client.get("/api/entitlement/required-tier?channels=5").get_json()
    assert d["required_tier"] == "cloud_starter"
    assert d["allowed"] is False
    assert d["upgrade_required"] is True


def test_enforce_retention_over_cap_marks_not_allowed(client, monkeypatch):
    """Under enforce, an OSS install asking for 30d retention sees
    ``allowed=False`` -- matches the cap surfaced on /api/entitlement."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    e.invalidate()
    d = client.get("/api/entitlement/required-tier?retention_days=30").get_json()
    assert d["required_tier"] == "cloud_starter"
    assert d["allowed"] is False
    assert d["upgrade_required"] is True
