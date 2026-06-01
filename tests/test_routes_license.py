"""Tests for the ``/api/license`` endpoint (``routes/entitlement.py``).

The endpoint exposes the same metadata ``clawmetry license`` prints on the
CLI so the dashboard can render a license-status badge without shelling
out. The headline invariants:

* Without a license file on disk, the endpoint returns
  ``{"installed": False, "status": "none"}`` — no 4xx, never crashes.
* With a valid signed token, the endpoint returns ``installed=True`` plus
  the verified payload metadata (tier / nodes / days_left / status).
* Tampered or expired tokens never report ``status: "active"``.
* The endpoint NEVER leaks the raw key bytes or the Ed25519 signature into
  the response body — only the verified payload metadata.

Hermetic: each test mints tokens with its own ephemeral Ed25519 keypair and
monkeypatches the module's embedded public key, so nothing depends on the
real production signing key.
"""
from __future__ import annotations

import time

import pytest
from flask import Flask


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=7, exp_delta=365 * 86400, sub="acct_test"):
    now = int(time.time())
    return {
        "sub": sub,
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes", "alerts", "fleet"],
    }


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement against an isolated
    license path + an ephemeral signing keypair."""
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)

    class _Env:
        pass

    e = _Env()
    e.L = L
    e.priv = priv
    e.client = app.test_client()
    return e


def test_license_endpoint_no_license_installed(env):
    """No file on disk → 200 with installed=False, status=none."""
    resp = env.client.get("/api/license")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"installed": False, "status": "none"}


def test_license_endpoint_active_license(env):
    """Valid signed token → installed=True with verified payload metadata."""
    tok = env.L._encode_token(_payload("pro", nodes=42), env.priv)
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    data = env.client.get("/api/license").get_json()
    assert data["installed"] is True
    assert data["valid"] is True
    assert data["status"] == "active"
    assert data["tier"] == "pro"
    assert data["nodes"] == 42
    assert data["sub"] == "acct_test"
    assert isinstance(data["exp"], (int, float))
    assert data["days_left"] > 300


def test_license_endpoint_enterprise_tier(env):
    """Enterprise tier surfaces as-is in the response."""
    tok = env.L._encode_token(_payload("enterprise", nodes=5), env.priv)
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    data = env.client.get("/api/license").get_json()
    assert data["installed"] is True
    assert data["tier"] == "enterprise"
    assert data["nodes"] == 5


def test_license_endpoint_expired(env):
    """Expired but signature-valid token → status=expired, valid=false."""
    tok = env.L._encode_token(_payload(exp_delta=-3600), env.priv)
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    data = env.client.get("/api/license").get_json()
    assert data["installed"] is True
    assert data["valid"] is False
    assert data["status"] == "expired"


def test_license_endpoint_invalid_file(env):
    """Garbage in the license file → installed=True, valid=false, status=invalid.

    The file exists but does not verify — the endpoint never claims
    'active' for such a file, so the UI can render a 'reactivate' CTA."""
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write("not-a-real-token")
    data = env.client.get("/api/license").get_json()
    assert data["installed"] is True
    assert data["valid"] is False
    assert data["status"] == "invalid"


def test_license_endpoint_forged_signature(env):
    """A token signed by a DIFFERENT key must not verify even though the
    payload is well-formed — the embedded public key is the gate."""
    other_priv, _ = _keypair()
    tok = env.L._encode_token(_payload(), other_priv)
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    data = env.client.get("/api/license").get_json()
    assert data["installed"] is True
    assert data["valid"] is False
    assert data["status"] == "invalid"


def test_license_endpoint_never_leaks_key_or_signature(env):
    """The raw token (including its Ed25519 signature) MUST NOT appear in
    the response body — only the verified payload metadata is exposed."""
    tok = env.L._encode_token(_payload("pro", nodes=3), env.priv)
    with open(env.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    resp = env.client.get("/api/license")
    body_text = resp.get_data(as_text=True)
    # Neither the full token nor the signature segment may leak.
    assert tok not in body_text
    sig_segment = tok.split(".")[-1]
    assert sig_segment not in body_text
    # The CLAW1 prefix is the token marker; it must not appear either.
    assert "CLAW1" not in body_text


def test_license_endpoint_survives_unreadable_file(env, monkeypatch):
    """If ``current_license_info`` itself blows up, the endpoint must still
    return a safe shape rather than 500. The handler is part of the
    dashboard's always-on surface and must obey the never-crash rule."""

    def _boom():
        raise RuntimeError("simulated read failure")

    monkeypatch.setattr(env.L, "current_license_info", _boom)
    resp = env.client.get("/api/license")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"installed": False, "status": "error"}
