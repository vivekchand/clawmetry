"""Tests for the capacity-axis branches of ``GET /api/entitlement/lock-reason``.

Sibling of ``tests/test_entitlement_required_tier_capacity.py``: the
``required-tier`` route already answers all four "which tier do I need" axes
(feature / runtime / channels / retention_days) off one URL. This pins the
matching ``lock-reason`` axes so the paywall tooltip on the channels and
history-range surfaces can render

    Locked: <reason>. [Upgrade to <X>]

in a single round-trip -- same wire contract as the feature= and runtime=
branches in ``tests/test_entitlement_api_lock_reason.py``.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def _enforced_client(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── grace: nothing locks, but the required_tier payload still rides along ──


def test_channels_grace_is_unlocked_but_carries_required_tier(client):
    d = client.get("/api/entitlement/lock-reason?channels=21").get_json()
    assert d["kind"] == "channels"
    assert d["key"] == "21"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    # Even in grace the upgrade target is named so a "you're on grace --
    # Starter at enforce" badge can render off the same call.
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["required_tier_rank"] == 1
    assert d["upgrade_required"] is True


def test_retention_grace_is_unlocked_but_carries_required_tier(client):
    d = client.get("/api/entitlement/lock-reason?retention_days=30").get_json()
    assert d["kind"] == "retention_days"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] == "cloud_starter"
    assert d["upgrade_required"] is True


# ── enforced OSS: capacity overflow surfaces a tier-naming reason ──────────


def test_channels_overflow_on_enforced_oss_is_locked(monkeypatch, tmp_path):
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?channels=5").get_json()
    assert d["kind"] == "channels"
    assert d["key"] == "5"
    assert d["locked"] is True
    assert d["allowed"] is False
    assert d["reason"] is not None
    assert "5 channels" in d["reason"]
    assert "Starter" in d["reason"]
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["upgrade_required"] is True


def test_channels_within_free_cap_on_enforced_oss_is_unlocked(monkeypatch, tmp_path):
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?channels=3").get_json()
    assert d["kind"] == "channels"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True


def test_retention_thirty_days_on_enforced_oss_is_locked(monkeypatch, tmp_path):
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?retention_days=30").get_json()
    assert d["kind"] == "retention_days"
    assert d["locked"] is True
    assert d["allowed"] is False
    assert "30-day retention" in d["reason"]
    assert "Starter" in d["reason"]
    assert d["required_tier"] == "cloud_starter"


def test_retention_ninety_days_on_enforced_oss_names_pro(monkeypatch, tmp_path):
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?retention_days=90").get_json()
    assert d["locked"] is True
    assert "Pro" in d["reason"]
    assert d["required_tier"] == "cloud_pro"


def test_retention_year_on_enforced_oss_names_enterprise(monkeypatch, tmp_path):
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?retention_days=365").get_json()
    assert d["locked"] is True
    assert "Enterprise" in d["reason"]
    assert d["required_tier"] == "enterprise"


# ── never-crash posture mirrors the required-tier wrapper ──────────────────


def test_non_int_channels_returns_unlocked(client):
    d = client.get("/api/entitlement/lock-reason?channels=abc").get_json()
    assert d["kind"] == "channels"
    assert d["key"] == "abc"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] is None
    assert d["required_tier_rank"] == -1


def test_non_int_retention_returns_unlocked(client):
    d = client.get(
        "/api/entitlement/lock-reason?retention_days=notanumber"
    ).get_json()
    assert d["kind"] == "retention_days"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] is None


def test_blank_channels_swallows_to_required_none(client):
    """``?channels=`` (present but empty) parses to None, not "fell through
    to a feature/runtime branch"."""
    d = client.get("/api/entitlement/lock-reason?channels=").get_json()
    assert d["kind"] == "channels"
    assert d["required_tier"] is None
    assert d["reason"] is None


# ── validation: exactly-one-of {feature, runtime, channels, retention_days} ─


def test_400_when_no_params_supplied(client):
    resp = client.get("/api/entitlement/lock-reason")
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
    resp = client.get(f"/api/entitlement/lock-reason?{qs}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ── feature / runtime branches still work after the refactor ────────────────


def test_feature_branch_unchanged(monkeypatch, tmp_path):
    """Regression guard -- the existing feature= response shape is preserved
    after the capacity branches landed."""
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?feature=fleet").get_json()
    assert d["kind"] == "feature"
    assert d["locked"] is True
    assert "Starter" in d["reason"]
    assert d["required_tier"] == "cloud_starter"


def test_runtime_branch_unchanged(monkeypatch, tmp_path):
    """Regression guard for runtime= -- same shape as before the refactor."""
    c = _enforced_client(monkeypatch, tmp_path)
    d = c.get("/api/entitlement/lock-reason?runtime=claude_code").get_json()
    assert d["kind"] == "runtime"
    assert d["locked"] is True
    assert d["required_tier"] == "cloud_starter"


# ── never-raise on resolution failure (matches feature/runtime fallback) ───


def test_never_raises_on_resolution_failure_capacity(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    def boom(*_a, **_kw):
        raise RuntimeError("entitlement read sad")

    monkeypatch.setattr(e, "get_entitlement", boom)

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    resp = app.test_client().get(
        "/api/entitlement/lock-reason?channels=21"
    )
    assert resp.status_code == 200
    d = resp.get_json()
    # The fallback fully populates the shape on the capacity axis too --
    # ``kind`` reflects which axis the caller asked about so a frontend
    # branch on ``kind`` keeps working through the failure mode.
    assert d["kind"] == "channels"
    assert d["key"] == "21"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] is None
    assert d["required_tier_rank"] == -1
    assert d["upgrade_required"] is False
