"""Tests for the /api/license/* endpoints added in routes/entitlement.py.

Uses an ephemeral Ed25519 keypair (never the production key) and a tmp_path
license file so no real file system state is touched.
"""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# ── shared helpers (mirrors test_license.py) ──────────────────────────────────


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def app(monkeypatch, tmp_path):
    import clawmetry.license as _lic

    priv, pub_pem = _keypair()
    monkeypatch.setattr(_lic, "_PUBLIC_KEY_PEM", pub_pem)
    license_path = str(tmp_path / "license.key")
    monkeypatch.setattr(_lic, "LICENSE_PATH", license_path)
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)

    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True

    return SimpleNamespace(
        app=flask_app,
        lic=_lic,
        priv=priv,
        license_path=license_path,
    )


# ── /api/license/status ───────────────────────────────────────────────────────


def test_status_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is False
    assert data["status"] == "no_license"


def test_status_active_license(app):
    tok = app.lic._encode_token(_payload("pro", nodes=5), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is True
    assert data["tier"] == "pro"
    assert data["nodes"] == 5


# ── /api/license/activate ─────────────────────────────────────────────────────


def test_activate_valid_key(app):
    tok = app.lic._encode_token(_payload("pro", nodes=2), app.priv)
    with app.app.test_client() as c:
        resp = c.post(
            "/api/license/activate",
            data=json.dumps({"key": tok}),
            content_type="application/json",
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "pro" in data["message"].lower()


def test_activate_invalid_key(app):
    with app.app.test_client() as c:
        resp = c.post(
            "/api/license/activate",
            data=json.dumps({"key": "CLAW1.not.real"}),
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_activate_missing_key_body(app):
    with app.app.test_client() as c:
        resp = c.post(
            "/api/license/activate",
            data=json.dumps({}),
            content_type="application/json",
        )
    assert resp.status_code == 400


def test_activate_expired_key(app):
    tok = app.lic._encode_token(_payload(exp_delta=-3600), app.priv)
    with app.app.test_client() as c:
        resp = c.post(
            "/api/license/activate",
            data=json.dumps({"key": tok}),
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


# ── /api/license/deactivate ───────────────────────────────────────────────────


def test_deactivate_removes_file(app):
    import os

    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert os.path.isfile(app.license_path)

    with app.app.test_client() as c:
        resp = c.post("/api/license/deactivate")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["removed"] is True
    assert not os.path.isfile(app.license_path)


def test_deactivate_idempotent_when_no_license(app):
    with app.app.test_client() as c:
        resp = c.post("/api/license/deactivate")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["removed"] is False
