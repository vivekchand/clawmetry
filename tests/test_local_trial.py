"""Tests for the local trial-activation flow.

Two halves:

1. ``parse_license`` tier mapping — a signed token with ``tier="trial"``
   MUST resolve to :data:`clawmetry.entitlements.TIER_TRIAL`. This is the
   revert-proof guard for the fix: before it, the forward-compat fallback
   coerced unknown tiers to TIER_PRO, so a 7-day trial key silently granted
   a permanent-feature Pro entitlement (until exp) instead of a trial.

2. ``POST /api/trial/activate`` (routes/trial.py) — exchanges an email+OTP
   for a key minted by the (mocked) cloud, activates it on this install,
   and reports the refreshed entitlement. Hermetic: ephemeral keypair,
   monkeypatched public key, no network.
"""
from __future__ import annotations

import io
import json
import time
import urllib.error
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


def _trial_payload(exp_delta=7 * 86400):
    now = int(time.time())
    return {
        "jti": "lic_trial_test",
        "sub": "trial@example.com",
        "tier": "trial",
        "nodes": 2,
        "iat": now,
        "exp": now + exp_delta,
    }


@pytest.fixture
def lic(monkeypatch, tmp_path):
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


# ── tier mapping ─────────────────────────────────────────────────────────────


def test_trial_token_maps_to_tier_trial(lic):
    """The revert-proof: pre-fix this asserted-tier came back TIER_PRO."""
    from clawmetry import entitlements as ent

    tok = lic.L._encode_token(_trial_payload(), lic.priv)
    e = lic.L.parse_license(tok)
    assert e is not None
    assert e.tier == ent.TIER_TRIAL
    assert e.tier != ent.TIER_PRO


def test_trial_entitlement_unlocks_paid_runtimes(lic):
    """TIER_TRIAL is a paid tier: claude_code and friends must be allowed."""
    tok = lic.L._encode_token(_trial_payload(), lic.priv)
    e = lic.L.parse_license(tok)
    assert e.allows_runtime("claude_code")
    assert e.allows_runtime("cursor")
    assert e.allows_runtime("openclaw")  # free runtimes stay allowed


def test_expired_trial_token_does_not_entitle(lic):
    """An expired trial key must not resolve into an active entitlement.

    parse_license builds the entitlement with the token's exp; the resolver
    treats a past expiry as expired. Assert the expiry travels through.
    """
    tok = lic.L._encode_token(_trial_payload(exp_delta=-3600), lic.priv)
    e = lic.L.parse_license(tok)
    # The entitlement object carries the (past) expiry for the resolver.
    assert e is not None
    assert float(e.expiry) < time.time()


def test_starter_and_pro_mapping_unchanged(lic):
    """The trial branch must not disturb the existing tier mappings."""
    from clawmetry import entitlements as ent

    p = _trial_payload()
    p["tier"] = "starter"
    assert lic.L.parse_license(lic.L._encode_token(p, lic.priv)).tier == ent.TIER_CLOUD_STARTER
    p["tier"] = "pro"
    assert lic.L.parse_license(lic.L._encode_token(p, lic.priv)).tier == ent.TIER_PRO
    p["tier"] = "somefuturetier"
    assert lic.L.parse_license(lic.L._encode_token(p, lic.priv)).tier == ent.TIER_PRO


# ── /api/trial/activate ──────────────────────────────────────────────────────


@pytest.fixture
def trial_app(lic, monkeypatch):
    """Minimal Flask app carrying only bp_trial, with the cloud mocked."""
    from flask import Flask

    from routes.trial import bp_trial

    app = Flask(__name__)
    app.register_blueprint(bp_trial)
    return app


def _mock_cloud(monkeypatch, lic, status=200, body=None):
    """Route routes.trial's urlopen to a canned cloud response."""
    import routes.trial as T

    if body is None:
        key = lic.L._encode_token(_trial_payload(), lic.priv)
        body = {"ok": True, "key": key}
    raw = json.dumps(body).encode("utf-8")
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(req)
        if status >= 400:
            raise urllib.error.HTTPError(
                req.full_url, status, "err", {}, io.BytesIO(raw)
            )

        class _Resp:
            def read(self):
                return raw

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _Resp()

    monkeypatch.setattr(T.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_activate_happy_path_writes_key_and_reports_trial(trial_app, lic, monkeypatch):
    calls = _mock_cloud(monkeypatch, lic)
    # Entitlement resolution must read the SAME monkeypatched license path.
    from clawmetry import entitlements as ent

    monkeypatch.setattr(ent, "_LICENSE_PATH", lic.L.LICENSE_PATH)
    ent.invalidate()

    client = trial_app.test_client()
    r = client.post(
        "/api/trial/activate",
        json={"email": "Trial@Example.com", "code": "123456"},
    )
    assert r.status_code == 200, r.get_json()
    d = r.get_json()
    assert d["ok"] is True
    assert d["tier"] == ent.TIER_TRIAL
    # The signed key landed on disk and verifies offline.
    import os

    assert os.path.isfile(lic.L.LICENSE_PATH)
    with open(lic.L.LICENSE_PATH, encoding="utf-8") as fh:
        assert lic.L.verify_token(fh.read().strip())["tier"] == "trial"
    # The email was normalised before hitting the cloud.
    sent = json.loads(calls[0].data.decode("utf-8"))
    assert sent["email"] == "trial@example.com"


def test_activate_rejects_bad_email_and_code_shapes(trial_app):
    client = trial_app.test_client()
    assert client.post("/api/trial/activate", json={"email": "nope", "code": "123456"}).status_code == 400
    assert client.post("/api/trial/activate", json={"email": "a@b.co", "code": "12"}).status_code == 400
    assert client.post("/api/trial/activate", json={"email": "a@b.co", "code": "abcdef"}).status_code == 400


def test_activate_surfaces_cloud_error_message(trial_app, lic, monkeypatch):
    _mock_cloud(monkeypatch, lic, status=400, body={"ok": False, "error": "Invalid or expired code."})
    client = trial_app.test_client()
    r = client.post("/api/trial/activate", json={"email": "a@b.co", "code": "123456"})
    assert r.status_code == 400
    assert "Invalid or expired code." in r.get_json()["error"]


def test_activate_rejects_forged_key_from_cloud(trial_app, lic, monkeypatch):
    """A key signed by the wrong keypair must not activate."""
    other_priv, _ = _keypair()
    forged = lic.L._encode_token(_trial_payload(), other_priv)
    _mock_cloud(monkeypatch, lic, body={"ok": True, "key": forged})
    client = trial_app.test_client()
    r = client.post("/api/trial/activate", json={"email": "a@b.co", "code": "123456"})
    assert r.status_code == 502
    import os

    assert not os.path.isfile(lic.L.LICENSE_PATH)
