"""Tests for the ``nodes=`` branch of
``GET /api/entitlement/required-tier`` and
``GET /api/entitlement/lock-reason``.

The Python helpers :func:`clawmetry.entitlements.min_tier_for_node_count` and
:meth:`Entitlement.lock_reason(kind="nodes")` are pinned in
``tests/test_entitlements_min_tier_nodes.py`` and
``tests/test_entitlement_lock_reason_nodes.py``. This file pins the HTTP
wrappers so the same two endpoints answer all four capacity axes off the
same URL shape, and a future param rename / shape drift fails loudly here.

Companion to ``tests/test_entitlement_required_tier_capacity.py`` (the
channels / retention HTTP branches this file mirrors).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement and a clean HOME so the
    resolver collapses to OSS-free deterministically. Mirrors the fixture in
    ``tests/test_entitlement_required_tier_capacity.py``."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── /api/entitlement/required-tier?nodes= ─────────────────────────────────


def test_required_tier_one_node_fits_oss(client):
    """1 node fits the OSS single-node grant. Grace pass-through keeps
    ``allowed`` True."""
    resp = client.get("/api/entitlement/required-tier?nodes=1")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["kind"] == "nodes"
    assert d["key"] == "1"
    assert d["required_tier"] == "oss"
    assert d["required_tier_label"] == "OSS"
    assert d["required_tier_rank"] == 0
    assert d["allowed"] is True
    assert d["upgrade_required"] is False


def test_required_tier_two_nodes_resolves_to_starter(client):
    """2+ nodes require Starter -- the cheapest tier with node_limit set
    to None (unlimited)."""
    d = client.get("/api/entitlement/required-tier?nodes=4").get_json()
    assert d["kind"] == "nodes"
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["required_tier_rank"] == 1


def test_required_tier_grace_keeps_allowed_true_over_cap(client):
    """The headline grace invariant -- wiring this branch must not change
    current behaviour. ``allowed`` is True for any count in grace mode."""
    d = client.get("/api/entitlement/required-tier?nodes=999").get_json()
    assert d["allowed"] is True


def test_required_tier_zero_nodes_collapses_to_oss(client):
    """``nodes=0`` means "no nodes registered yet" -- trivially satisfied
    by the free floor. Mirrors :func:`min_tier_for_node_count`."""
    d = client.get("/api/entitlement/required-tier?nodes=0").get_json()
    assert d["required_tier"] == "oss"


def test_required_tier_non_int_swallows_to_required_none(client):
    """A non-int ``nodes`` is swallowed by ``min_tier_for_node_count``
    (which returns None). The HTTP wrapper inherits the never-crash
    posture -- ``required_tier`` is None and the body still well-formed."""
    d = client.get("/api/entitlement/required-tier?nodes=abc").get_json()
    assert d["kind"] == "nodes"
    assert d["key"] == "abc"
    assert d["required_tier"] is None
    assert d["required_tier_label"] is None
    assert d["upgrade_required"] is False


def test_required_tier_blank_value_is_swallowed(client):
    """``?nodes=`` (present but empty) parses to None, not "fell through
    to a feature/runtime branch". The body returns required_tier None,
    kind="nodes"."""
    d = client.get("/api/entitlement/required-tier?nodes=").get_json()
    assert d["kind"] == "nodes"
    assert d["required_tier"] is None


# ── /api/entitlement/lock-reason?nodes= ───────────────────────────────────


def test_lock_reason_one_node_is_unlocked(client):
    """1 node fits OSS -- no reason to render."""
    d = client.get("/api/entitlement/lock-reason?nodes=1").get_json()
    assert d["kind"] == "nodes"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] == "oss"


def test_lock_reason_grace_keeps_locked_false_over_cap(client):
    """Grace mode locks nothing -- the rollout invariant. The endpoint still
    reports the required_tier so the UI can render the upgrade affordance
    once enforce flips on, but ``locked`` stays False today."""
    d = client.get("/api/entitlement/lock-reason?nodes=21").get_json()
    assert d["kind"] == "nodes"
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] == "cloud_starter"


def test_lock_reason_non_int_swallows_to_none(client):
    """A non-int ``nodes`` lands the never-crash branch -- reason / locked /
    required_tier all neutral, no 500."""
    d = client.get("/api/entitlement/lock-reason?nodes=abc").get_json()
    assert d["kind"] == "nodes"
    assert d["key"] == "abc"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["required_tier"] is None


# ── validation: exactly-one-param ────────────────────────────────────────


def test_required_tier_400_when_no_params(client):
    """No params is still a 400 -- the error message now mentions ``nodes``
    alongside the other three axes."""
    resp = client.get("/api/entitlement/required-tier")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body
    assert "nodes" in body["error"]


def test_lock_reason_400_when_no_params(client):
    resp = client.get("/api/entitlement/lock-reason")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body
    assert "nodes" in body["error"]


@pytest.mark.parametrize(
    "qs",
    [
        "feature=self_evolve&nodes=5",
        "runtime=claude_code&nodes=5",
        "channels=5&nodes=5",
        "retention_days=30&nodes=5",
    ],
)
def test_required_tier_400_when_nodes_paired_with_other_axis(client, qs):
    """Mixing the new nodes= axis with any other axis is a 400 -- same
    exactly-one-axis contract the other three branches already enforce."""
    resp = client.get(f"/api/entitlement/required-tier?{qs}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.parametrize(
    "qs",
    [
        "feature=self_evolve&nodes=5",
        "runtime=claude_code&nodes=5",
        "channels=5&nodes=5",
        "retention_days=30&nodes=5",
    ],
)
def test_lock_reason_400_when_nodes_paired_with_other_axis(client, qs):
    resp = client.get(f"/api/entitlement/lock-reason?{qs}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ── existing branches still work after the refactor ──────────────────────


def test_required_tier_feature_branch_unchanged(client):
    """Regression guard -- adding the nodes branch must not break the
    existing feature= response shape."""
    d = client.get("/api/entitlement/required-tier?feature=self_evolve").get_json()
    assert d["kind"] == "feature"
    assert d["required_tier"] == "cloud_pro"


def test_required_tier_retention_branch_unchanged(client):
    """Regression guard -- retention_days= still resolves the same way."""
    d = client.get("/api/entitlement/required-tier?retention_days=30").get_json()
    assert d["kind"] == "retention_days"
    assert d["required_tier"] == "cloud_starter"


# ── enforce mode: allowed reflects current entitlement ──────────────────


def test_enforce_two_nodes_marks_not_allowed(client, monkeypatch):
    """Under enforce, an OSS install at 2 nodes (over the single-node grant)
    sees ``allowed=False`` -- the gate axis is wired through, just inert in
    grace."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    e.invalidate()
    d = client.get("/api/entitlement/required-tier?nodes=2").get_json()
    assert d["required_tier"] == "cloud_starter"
    assert d["allowed"] is False
    assert d["upgrade_required"] is True


def test_enforce_lock_reason_two_nodes_returns_reason(client, monkeypatch):
    """Under enforce, lock-reason on 2 nodes returns the rendered string
    naming the overflow count, the cap, and the unlock tier."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    e.invalidate()
    d = client.get("/api/entitlement/lock-reason?nodes=2").get_json()
    assert d["locked"] is True
    assert d["reason"] is not None
    assert "2 nodes" in d["reason"]
    assert "Starter" in d["reason"]
