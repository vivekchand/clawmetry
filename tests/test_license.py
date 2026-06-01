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
    # Clear the cloud server override too so `activate` stays fully offline (no
    # network) in unit tests — the self-hosted install path only phones home
    # when a server is explicitly configured.
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
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


# ── auto-provision-on-connect (cloud cm_ account path) ──────────────────────────


@pytest.fixture
def prov(lic, monkeypatch, tmp_path):
    """license module with the pro marker redirected to a temp file + the cloud
    base pointed at a fake server, and no real pro package present."""
    monkeypatch.setattr(lic.L, "_PRO_MARKER_PATH", str(tmp_path / "pro.json"))
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", "https://fake.clawmetry.test")
    monkeypatch.setattr(lic.L, "_pro_installed_version", lambda: None)
    return lic


def _fake_entitlement(monkeypatch, L, *, entitled, pro_available=True):
    """Stub urllib so the /api/license/entitlement probe returns a canned body
    and any download attempt is observable."""
    import io
    import json as _j
    import urllib.request

    calls = {"download": 0, "entitlement": 0}

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=0):
        url = req.full_url
        if "/api/license/entitlement" in url:
            calls["entitlement"] += 1
            assert req.headers.get("X-api-key", "").startswith("cm_")
            return _Resp(_j.dumps({"entitled": entitled, "plan": "cloud_pro" if entitled else "free", "pro_available": pro_available}).encode())
        if "/api/license/download" in url:
            calls["download"] += 1
            return _Resp(b"PK\x03\x04fake-wheel-bytes")
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    return calls


def test_auto_provision_free_account_installs_nothing(prov, monkeypatch):
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=False)
    installed, msg = L.auto_provision_pro("cm_freeuser", node_id="n1")
    assert installed is False
    assert msg == ""  # free accounts produce no user-facing message
    assert calls["entitlement"] == 1
    assert calls["download"] == 0  # NEVER downloads the wheel for a free account


def test_auto_provision_entitled_account_downloads_and_installs(prov, monkeypatch):
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=True)
    # Pro absent at probe time, present after the (stubbed) pip install — this
    # exercises the real download + install branch end to end.
    _state = {"v": None}
    monkeypatch.setattr(L, "_pro_installed_version", lambda: _state["v"])

    def _fake_pip(path):
        assert path and path.endswith(".whl")
        _state["v"] = "0.2.0"
        return True, "installed"

    monkeypatch.setattr(L, "_pip_install_wheel", _fake_pip)
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is True
    assert calls["entitlement"] == 1
    assert calls["download"] == 1  # actually fetched the wheel
    assert "installed" in msg.lower()


def test_auto_provision_non_cm_key_is_noop(prov):
    installed, msg = prov.L.auto_provision_pro("not-a-key", node_id="n1")
    assert installed is False and msg == ""


def test_auto_provision_never_raises_on_install_failure(prov, monkeypatch):
    L = prov.L
    _fake_entitlement(monkeypatch, L, entitled=True)
    monkeypatch.setattr(L, "_pip_install_wheel", lambda p: (False, "pip blew up"))
    # download succeeds, install fails -> installed=False, message, no raise.
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is False
    assert "failed" in msg.lower()


def test_auto_provision_idempotent_when_pro_present(prov, monkeypatch):
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=True)
    monkeypatch.setattr(L, "_pro_installed_version", lambda: "0.2.0")
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is True
    assert calls["download"] == 0  # already current -> no re-download
    assert "already installed" in msg


def test_download_wheel_refuses_non_https(prov):
    assert prov.L._download_wheel("http://evil.example.com/x.whl") is None
