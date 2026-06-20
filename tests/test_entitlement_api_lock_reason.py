"""Tests for ``GET /api/entitlement/lock-reason``.

Pins the HTTP contract on the lock-reason route so a dashboard tooltip /
paywall body / CLI diagnostic that reads it never receives a surprise
shape. The route wraps :meth:`Entitlement.lock_reason` (already covered by
``tests/test_entitlement_lock_reason.py``) so these tests focus on the
wire contract:

* mandatory exactly-one query param (400 otherwise)
* free / grace cases return ``reason: null`` + ``locked: false``
* paid items on enforced OSS return a non-empty reason naming the unlock
  tier (Starter / Pro / Enterprise) + ``locked: true``
* explicit ``feature=`` / ``runtime=`` carry the correct ``kind``
* the ``required_tier`` payload (id + label + rank, plus the current tier
  and an ``upgrade_required`` flag) rides alongside the message so a
  paywall tooltip can render "Locked: <reason>. [Upgrade to <X>]" in a
  single round-trip instead of pairing this call with
  ``/api/entitlement/required-tier``
* the never-raise grace fallback still returns the documented shape
"""
from __future__ import annotations

import importlib
import json

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
    return app.test_client(), tmp_path


# ── input validation ────────────────────────────────────────────────────────


def test_missing_both_params_is_400(client):
    c, _ = client
    resp = c.get("/api/entitlement/lock-reason")
    assert resp.status_code == 400
    assert "feature" in resp.get_json()["error"]


def test_both_params_is_400(client):
    c, _ = client
    resp = c.get(
        "/api/entitlement/lock-reason?feature=sessions&runtime=openclaw"
    )
    assert resp.status_code == 400


# ── grace mode locks nothing ────────────────────────────────────────────────


def test_grace_feature_is_unlocked(client):
    c, _ = client
    resp = c.get("/api/entitlement/lock-reason?feature=self_evolve")
    assert resp.status_code == 200
    d = resp.get_json()
    # Grace cancels the lock but still names the upgrade target so the UI can
    # render a "you're on grace -- Pro at enforce" badge off the same call.
    assert d["key"] == "self_evolve"
    assert d["kind"] == "feature"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] == "cloud_pro"
    assert d["required_tier_label"] == "Pro"
    assert d["required_tier_rank"] >= 2
    assert d["current_tier"] == "oss"
    assert d["current_tier_rank"] == 0
    assert d["upgrade_required"] is True


def test_grace_runtime_is_unlocked(client):
    c, _ = client
    resp = c.get("/api/entitlement/lock-reason?runtime=claude_code")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["key"] == "claude_code"
    assert d["kind"] == "runtime"
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True


# ── free items never lock, even when enforced ──────────────────────────────


def test_free_feature_never_locks_under_enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=sessions")
        .get_json()
    )
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is True


def test_free_runtime_never_locks_under_enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?runtime=openclaw")
        .get_json()
    )
    assert d["reason"] is None
    assert d["locked"] is False


# ── paid items on enforced OSS lock with a tier-naming reason ───────────────


def test_paid_runtime_on_enforced_oss_is_locked(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?runtime=claude_code")
        .get_json()
    )
    assert d["key"] == "claude_code"
    assert d["kind"] == "runtime"
    assert d["locked"] is True
    assert d["allowed"] is False
    assert d["reason"] is not None
    assert "claude_code" in d["reason"]


def test_starter_feature_reason_names_starter(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=fleet")
        .get_json()
    )
    assert d["locked"] is True
    assert d["allowed"] is False
    assert "Starter" in d["reason"]
    assert "fleet" in d["reason"]


def test_pro_feature_reason_names_pro(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=self_evolve")
        .get_json()
    )
    assert d["locked"] is True
    assert "Pro" in d["reason"]
    assert "self_evolve" in d["reason"]


# ── starter tier still locks Pro-only items ─────────────────────────────────


def test_starter_install_still_locks_pro_feature(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_starter", "node_limit": 1, "expiry": None})
    )

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    client = app.test_client()

    # Starter unlocks its own slice -- reason is None, allowed is True.
    starter_d = (
        client.get("/api/entitlement/lock-reason?feature=fleet").get_json()
    )
    assert starter_d["reason"] is None
    assert starter_d["allowed"] is True

    # Starter does NOT unlock self_evolve -- still locked with a Pro reason.
    pro_d = (
        client.get(
            "/api/entitlement/lock-reason?feature=self_evolve"
        ).get_json()
    )
    assert pro_d["locked"] is True
    assert pro_d["allowed"] is False
    assert "Pro" in pro_d["reason"]


# ── unknown ids are silently un-locked (mirrors the helper contract) ────────


def test_unknown_feature_id_returns_unlocked(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=not_a_real_feature_id")
        .get_json()
    )
    # ``lock_reason`` returns None for unknown ids (errs on the un-locked
    # side -- no catalogue, no claim). ``allows_feature`` is independently
    # decided by entitlement membership and stays False when enforced. The
    # frontend treats ``reason is null`` as "nothing to render", regardless
    # of the underlying allow answer.
    assert d["reason"] is None
    assert d["locked"] is False
    assert d["allowed"] is False


# ── never-raise: a flaky entitlement read collapses to the grace shape ──────


def test_never_raises_on_resolution_failure(monkeypatch, tmp_path):
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
        "/api/entitlement/lock-reason?feature=self_evolve"
    )
    assert resp.status_code == 200
    d = resp.get_json()
    # The fallback shape is fully populated -- including the required_tier
    # payload -- so a frontend never sees a half-shape regardless of which
    # branch served the response.
    assert d == {
        "key": "self_evolve",
        "kind": "feature",
        "reason": None,
        "locked": False,
        "allowed": True,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "upgrade_required": False,
    }


# ── required_tier payload rides alongside the message ──────────────────────


def test_paid_feature_carries_required_tier_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=fleet")
        .get_json()
    )
    assert d["locked"] is True
    assert d["allowed"] is False
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["required_tier_rank"] >= 1
    assert d["current_tier"] == "oss"
    assert d["current_tier_rank"] == 0
    assert d["upgrade_required"] is True


def test_paid_runtime_carries_required_tier_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?runtime=claude_code")
        .get_json()
    )
    assert d["locked"] is True
    assert d["allowed"] is False
    # PAID_RUNTIMES all unlock starting at cloud_starter -- mirrors
    # ``min_tier_for_runtime``.
    assert d["required_tier"] == "cloud_starter"
    assert d["required_tier_label"] == "Starter"
    assert d["required_tier_rank"] >= 1
    assert d["upgrade_required"] is True


def test_free_feature_required_tier_is_oss(monkeypatch, tmp_path):
    """Free items still surface their required_tier so a frontend can render
    a uniform "Available in <tier>" badge across the catalogue without a
    special case for the free row."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=sessions")
        .get_json()
    )
    assert d["locked"] is False
    assert d["allowed"] is True
    assert d["required_tier"] == "oss"
    assert d["required_tier_label"] == "OSS"
    assert d["required_tier_rank"] == 0
    # OSS == current tier => no upgrade needed.
    assert d["upgrade_required"] is False


def test_starter_install_paid_pro_feature_payload(monkeypatch, tmp_path):
    """When a Starter install hits a Pro-only feature the required_tier still
    reads Pro and ``upgrade_required`` reflects the rank delta from Starter,
    not from OSS."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"plan": "cloud_starter", "node_limit": 1, "expiry": None})
    )

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=self_evolve")
        .get_json()
    )
    assert d["locked"] is True
    assert d["allowed"] is False
    assert d["required_tier"] == "cloud_pro"
    assert d["required_tier_label"] == "Pro"
    assert d["current_tier"] == "cloud_starter"
    assert d["current_tier_rank"] == 1
    assert d["required_tier_rank"] >= 2
    assert d["upgrade_required"] is True


def test_unknown_feature_required_tier_is_none(monkeypatch, tmp_path):
    """Mirrors the ``required-tier`` endpoint's posture: an unknown id maps
    to ``required_tier: null`` with rank ``-1`` and ``upgrade_required: false``
    so a UI can quietly skip the row without rendering a broken badge."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = (
        app.test_client()
        .get("/api/entitlement/lock-reason?feature=not_a_real_feature_id")
        .get_json()
    )
    assert d["required_tier"] is None
    assert d["required_tier_label"] is None
    assert d["required_tier_rank"] == -1
    assert d["upgrade_required"] is False
