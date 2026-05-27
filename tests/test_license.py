"""Tests for clawmetry/license.py — Ed25519 self-hosted license client.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key, so nothing depends on the real
production signing key. Covers signature verification (valid/forged/tampered),
expiry, entitlement mapping, file load, the activate flow, and the integration
back into clawmetry.entitlements.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=10, exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes", "alerts", "fleet"],
    }


@pytest.fixture
def lic(monkeypatch, tmp_path):
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


# ── signature verification ────────────────────────────────────────────────────


def test_valid_token_verifies(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    payload = lic.L.verify_token(tok)
    assert payload is not None
    assert payload["tier"] == "pro"
    assert payload["nodes"] == 10


def test_forged_token_rejected(lic):
    other_priv, _ = _keypair()  # signed by a DIFFERENT key
    tok = lic.L._encode_token(_payload(), other_priv)
    assert lic.L.verify_token(tok) is None


def test_tampered_payload_rejected(lic):
    tok = lic.L._encode_token(_payload(nodes=1), lic.priv)
    prefix, body, sig = tok.split(".")
    # swap in a different (validly-signed-elsewhere) body but keep the old sig
    forged_body = lic.L._b64u_encode(b'{"tier":"enterprise","nodes":9999}')
    assert lic.L.verify_token(f"{prefix}.{forged_body}.{sig}") is None


@pytest.mark.parametrize("bad", ["", "garbage", "NOPE.a.b", "CLAW1.only-two"])
def test_malformed_tokens_rejected(lic, bad):
    assert lic.L.verify_token(bad) is None


# ── entitlement mapping ────────────────────────────────────────────────────────


def test_parse_license_pro(lic):
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("pro", nodes=42), lic.priv)
    en = lic.L.parse_license(tok)
    assert en is not None
    assert en.tier == e.TIER_PRO
    assert en.source == "license"
    assert en.node_limit == 42
    assert en.is_paid is True


def test_parse_license_enterprise(lic):
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("enterprise", nodes=5), lic.priv)
    en = lic.L.parse_license(tok)
    assert en.tier == e.TIER_ENTERPRISE


def test_invalid_token_parses_to_none(lic):
    assert lic.L.parse_license("CLAW1.bogus.bogus") is None


# ── file load + activate ───────────────────────────────────────────────────────


def test_load_license_from_file(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    with open(lic.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    en = lic.L.load_license(lic.L.LICENSE_PATH)
    assert en is not None and en.is_paid


def test_load_missing_file_returns_none(lic):
    assert lic.L.load_license(lic.L.LICENSE_PATH) is None


def test_activate_valid_key(lic):
    import os

    tok = lic.L._encode_token(_payload("pro", nodes=7), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert "pro" in msg.lower()
    assert os.path.isfile(lic.L.LICENSE_PATH)
    # deferred install message when no server configured
    assert "deferred" in msg.lower()


def test_activate_invalid_key(lic):
    ok, msg = lic.L.activate("CLAW1.not.real")
    assert ok is False
    assert not __import__("os").path.isfile(lic.L.LICENSE_PATH)


def test_activate_expired_key(lic):
    tok = lic.L._encode_token(_payload(exp_delta=-3600), lic.priv)  # already expired
    ok, msg = lic.L.activate(tok)
    assert ok is False
    assert "expired" in msg.lower()


def test_current_license_info(lic):
    tok = lic.L._encode_token(_payload("pro", nodes=3), lic.priv)
    lic.L.activate(tok)
    info = lic.L.current_license_info()
    assert info["valid"] is True
    assert info["tier"] == "pro"
    assert info["nodes"] == 3
    assert info["days_left"] > 300


# ── integration with entitlements ──────────────────────────────────────────────


def test_activate_then_entitlement_resolves_pro(lic, monkeypatch):
    import clawmetry.entitlements as e

    monkeypatch.setattr(e, "_LICENSE_PATH", lic.L.LICENSE_PATH)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")  # enforce so grace can't mask it
    e.invalidate()

    tok = lic.L._encode_token(_payload("pro", nodes=42), lic.priv)
    ok, _ = lic.L.activate(tok)
    assert ok

    en = e.get_entitlement(force=True)
    assert en.tier == e.TIER_PRO
    assert en.node_limit == 42
    assert en.allows_runtime("claude_code") is True  # paid runtime unlocked
    assert en.grace is False
