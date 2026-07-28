"""The self-hosted trial lifecycle, end to end through the REAL gates
(founder directive 2026-07-28): a trial license key unlocks alerts and
approvals; when the trial EXPIRES they stop working even in grace mode;
a fully paid license keeps them working.

Hermetic: ephemeral Ed25519 keypair, monkeypatched public key, real
entitlement resolution over a real key file, real @gate decorators.
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


@pytest.fixture
def env(monkeypatch, tmp_path):
    import clawmetry.license as L
    from clawmetry import entitlements as E

    priv, pub_pem = _keypair()
    key_path = str(tmp_path / "license.key")
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", key_path)
    monkeypatch.setattr(E, "_LICENSE_PATH", key_path)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)  # GRACE mode: the hard case
    E.invalidate()

    def install(tier, days):
        now = int(time.time())
        tok = L._encode_token({
            "jti": "lic_t", "sub": "t@e.com", "tier": tier, "nodes": 2,
            "iat": now, "exp": now + days * 86400,
        }, priv)
        with open(key_path, "w", encoding="utf-8") as fh:
            fh.write(tok)
        E.invalidate()

    yield SimpleNamespace(install=install, E=E)
    E.invalidate()


def _gated_app():
    from flask import Flask, jsonify

    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/alerts")
    @gate("custom_alerts")
    def _alerts():
        return jsonify({"ok": True})

    @app.route("/approvals")
    @gate("approval_queue")
    def _approvals():
        return jsonify({"ok": True})

    return app.test_client()


def test_active_trial_unlocks_alerts_and_approvals(env):
    env.install("trial", days=6)
    c = _gated_app()
    assert c.get("/alerts").status_code == 200
    assert c.get("/approvals").status_code == 200


def test_expired_trial_locks_them_even_in_grace(env):
    """The revert-proof: in grace mode the old gates returned True for
    EVERYTHING, so an expired 7-day trial was a permanent unlock."""
    env.install("trial", days=-1)
    ent = env.E.get_entitlement(force=True)
    assert ent.grace is True, "precondition: the rollout is in grace mode"
    assert ent.expired is True, "precondition: the trial has lapsed"
    c = _gated_app()
    assert c.get("/alerts").status_code == 402, \
        "an expired trial must stop unlocking alerts"
    assert c.get("/approvals").status_code == 402, \
        "an expired trial must stop unlocking approvals"


def test_paid_license_keeps_them_working(env):
    env.install("pro", days=365)
    c = _gated_app()
    assert c.get("/alerts").status_code == 200
    assert c.get("/approvals").status_code == 200


def test_expired_trial_also_locks_paid_runtimes(env):
    env.install("trial", days=-1)
    ent = env.E.get_entitlement(force=True)
    assert ent.allows_runtime("claude_code") is False, \
        "the trial ending must stop the paid runtime watch too"
    assert ent.allows_runtime("openclaw") is True, \
        "free runtimes stay free after a lapsed trial"


def test_never_entitled_installs_keep_grace(env, tmp_path):
    """The rollout safety is untouched: no license file at all means grace
    still allows everything (enforce-day must not break bystanders)."""
    import os

    ent = env.E.get_entitlement(force=True)
    assert ent.grace is True and ent.expired is False
    c = _gated_app()
    assert c.get("/alerts").status_code == 200
    assert c.get("/approvals").status_code == 200
