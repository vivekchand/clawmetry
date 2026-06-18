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
    assert d == {
        "key": "self_evolve",
        "kind": "feature",
        "reason": None,
        "locked": False,
        "allowed": True,
    }


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
    assert d == {
        "key": "self_evolve",
        "kind": "feature",
        "reason": None,
        "locked": False,
        "allowed": True,
    }
