"""Tests for the license verification-key transparency surface.

The embedded Ed25519 public key in ``clawmetry/license.py`` is the trust
anchor for offline Pro/Enterprise license verification. If an attacker
could swap that constant for their own key on a target install, they
could mint "valid" license tokens locally. The ``pubkey_fingerprint()``
helper + the ``GET /api/license/pubkey`` route + the ``clawmetry license
fingerprint`` CLI subcommand all surface the SHA-256 of the embedded key
so an operator can compare it against the canonical fingerprint and
detect that tampering.

These tests pin the contract: stable hex digest, whitespace-independent,
never-raise on bad input, and the API shape stays stable.
"""
from __future__ import annotations

from types import SimpleNamespace

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


@pytest.fixture
def lic(monkeypatch):
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    return SimpleNamespace(L=L, pub_pem=pub_pem)


# ── pubkey_fingerprint() ──────────────────────────────────────────────────────


def test_fingerprint_is_64char_hex(lic):
    fp = lic.L.pubkey_fingerprint()
    assert fp is not None
    assert len(fp) == 64
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_is_stable_across_calls(lic):
    assert lic.L.pubkey_fingerprint() == lic.L.pubkey_fingerprint()


def test_fingerprint_is_whitespace_independent(lic, monkeypatch):
    """Re-formatting the PEM (extra newlines, CRLF, trailing whitespace) MUST
    NOT change the fingerprint — it's computed over the DER bytes."""
    fp_clean = lic.L.pubkey_fingerprint()
    # Re-wrap the same key with messy whitespace.
    pem = lic.pub_pem.decode("ascii")
    messy = ("\r\n  " + pem.replace("\n", "\r\n") + "\r\n\r\n").encode("ascii")
    monkeypatch.setattr(lic.L, "_PUBLIC_KEY_PEM", messy)
    assert lic.L.pubkey_fingerprint() == fp_clean


def test_fingerprint_changes_with_different_key(lic, monkeypatch):
    """A different keypair MUST produce a different fingerprint."""
    fp_a = lic.L.pubkey_fingerprint()
    _, other_pem = _keypair()
    monkeypatch.setattr(lic.L, "_PUBLIC_KEY_PEM", other_pem)
    fp_b = lic.L.pubkey_fingerprint()
    assert fp_a != fp_b


def test_fingerprint_never_raises_on_bad_pem(lic, monkeypatch):
    monkeypatch.setattr(lic.L, "_PUBLIC_KEY_PEM", b"not a pem")
    assert lic.L.pubkey_fingerprint() is None


# ── pubkey_info() ─────────────────────────────────────────────────────────────


def test_pubkey_info_shape(lic):
    info = lic.L.pubkey_info()
    assert info["algorithm"] == "ed25519"
    assert info["valid"] is True
    assert info["fingerprint_sha256"] == lic.L.pubkey_fingerprint()
    assert info["fingerprint_short"] == info["fingerprint_sha256"][:16]
    assert info["pem"].startswith("-----BEGIN PUBLIC KEY-----")
    assert info["pem"].rstrip().endswith("-----END PUBLIC KEY-----")


def test_pubkey_info_bad_pem_valid_false(lic, monkeypatch):
    monkeypatch.setattr(lic.L, "_PUBLIC_KEY_PEM", b"garbage")
    info = lic.L.pubkey_info()
    assert info["valid"] is False
    assert info["fingerprint_sha256"] is None
    assert info["fingerprint_short"] is None
    assert info["algorithm"] == "ed25519"


# ── /api/license/pubkey route ─────────────────────────────────────────────────


@pytest.fixture
def app(lic):
    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True
    return flask_app


def test_api_pubkey_returns_fingerprint(app, lic):
    with app.test_client() as c:
        resp = c.get("/api/license/pubkey")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["algorithm"] == "ed25519"
    assert data["valid"] is True
    assert data["fingerprint_sha256"] == lic.L.pubkey_fingerprint()
    assert data["fingerprint_short"] == data["fingerprint_sha256"][:16]
    assert data["pem"].startswith("-----BEGIN PUBLIC KEY-----")


def test_api_pubkey_never_raises_on_bad_pem(app, lic, monkeypatch):
    monkeypatch.setattr(lic.L, "_PUBLIC_KEY_PEM", b"definitely not pem")
    with app.test_client() as c:
        resp = c.get("/api/license/pubkey")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is False
    assert data["fingerprint_sha256"] is None


def test_api_pubkey_is_get_only(app):
    with app.test_client() as c:
        resp = c.post("/api/license/pubkey")
    assert resp.status_code == 405
