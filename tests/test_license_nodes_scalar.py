"""Tests for the ``license_nodes()`` / ``is_within_node_limit()`` scalar
helpers in :mod:`clawmetry.license` plus their matching
``/api/license/nodes`` and ``/api/license/within-node-limit`` HTTP endpoints.

Mirrors ``tests/test_license_api.py``'s hermetic pattern -- ephemeral
Ed25519 keypair, ``LICENSE_PATH`` monkeypatched into ``tmp_path``, and
``CLAWMETRY_OFFLINE=1`` so ``activate()`` never phones home during the
suite. Nothing here touches the operator's real license file.
"""
from __future__ import annotations

import time
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


@pytest.fixture
def env(monkeypatch, tmp_path):
    import clawmetry.license as _lic

    priv, pub_pem = _keypair()
    monkeypatch.setattr(_lic, "_PUBLIC_KEY_PEM", pub_pem)
    license_path = str(tmp_path / "license.key")
    monkeypatch.setattr(_lic, "LICENSE_PATH", license_path)
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")

    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True

    return SimpleNamespace(
        app=flask_app, lic=_lic, priv=priv, license_path=license_path
    )


# ── license_nodes() ───────────────────────────────────────────────────────────


def test_license_nodes_none_when_no_license(env):
    assert env.lic.license_nodes() is None


def test_license_nodes_active_returns_int(env):
    tok = env.lic._encode_token(_payload(nodes=7), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_nodes() == 7


def test_license_nodes_expired_collapses_to_none(env):
    # A lapsed customer must NOT keep rendering as "N nodes covered" via the
    # scalar helper -- matches the license_tier() posture for expired keys.
    tok = env.lic._encode_token(_payload(nodes=5, exp_delta=-3600), env.priv)
    env.lic.activate(tok)
    # activate refuses expired keys, so we write the file directly to
    # simulate the "expired since activation" state.
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    assert env.lic.license_nodes() is None


def test_license_nodes_invalid_signature_collapses_to_none(env, monkeypatch):
    """An unsigned / forged file must NOT surface a trusted node count."""
    # A signature-invalid file: write a token minted with a DIFFERENT keypair
    # than the one _PUBLIC_KEY_PEM was patched to.
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(nodes=99), other_priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    assert env.lic.license_nodes() is None


def test_license_nodes_nonpositive_claim_collapses(env):
    """A signed but nonsensical ``nodes=0`` claim collapses to None (a covered
    fleet of zero is meaningless — refuse it rather than surface it)."""
    tok = env.lic._encode_token(_payload(nodes=0), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_nodes() is None


# ── is_within_node_limit(n) ───────────────────────────────────────────────────


def test_is_within_node_limit_false_when_no_license(env):
    assert env.lic.is_within_node_limit(1) is False
    assert env.lic.is_within_node_limit(100) is False


def test_is_within_node_limit_true_at_and_below_limit(env):
    tok = env.lic._encode_token(_payload(nodes=5), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_within_node_limit(1) is True
    assert env.lic.is_within_node_limit(5) is True


def test_is_within_node_limit_false_above_limit(env):
    tok = env.lic._encode_token(_payload(nodes=3), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_within_node_limit(4) is False


def test_is_within_node_limit_rejects_zero_and_negative(env):
    tok = env.lic._encode_token(_payload(nodes=5), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_within_node_limit(0) is False
    assert env.lic.is_within_node_limit(-1) is False


def test_is_within_node_limit_rejects_non_int(env):
    tok = env.lic._encode_token(_payload(nodes=5), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_within_node_limit("garbage") is False  # type: ignore[arg-type]
    assert env.lic.is_within_node_limit(None) is False  # type: ignore[arg-type]


def test_is_within_node_limit_expired_key_returns_false(env):
    tok = env.lic._encode_token(_payload(nodes=5, exp_delta=-3600), env.priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    # Even at nodes=1, an expired license refuses the gate.
    assert env.lic.is_within_node_limit(1) is False


# ── /api/license/nodes ────────────────────────────────────────────────────────


def test_api_license_nodes_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/nodes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"nodes": None, "has_license": False, "valid": False}


def test_api_license_nodes_active(env):
    tok = env.lic._encode_token(_payload(nodes=8), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/nodes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"nodes": 8, "has_license": True, "valid": True}


def test_api_license_nodes_expired(env):
    tok = env.lic._encode_token(_payload(nodes=8, exp_delta=-3600), env.priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/nodes")
    assert resp.status_code == 200
    body = resp.get_json()
    # nodes collapses to null on the expired branch, but has_license stays
    # True — the file IS on disk, just no longer trusted for gating.
    assert body["nodes"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


# ── /api/license/within-node-limit ────────────────────────────────────────────


def test_api_within_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit?nodes=1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is False
    assert body["has_license"] is False
    assert body["valid"] is False
    assert body["requested_nodes"] == 1


def test_api_within_at_limit(env):
    tok = env.lic._encode_token(_payload(nodes=5), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit?nodes=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is True
    assert body["nodes"] == 5
    assert body["requested_nodes"] == 5
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_within_above_limit(env):
    tok = env.lic._encode_token(_payload(nodes=3), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit?nodes=4")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is False
    assert body["nodes"] == 3
    assert body["requested_nodes"] == 4
    assert body["valid"] is True


def test_api_within_bad_query_is_200_with_false(env):
    tok = env.lic._encode_token(_payload(nodes=3), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit?nodes=garbage")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is False
    assert body["nodes"] == 3
    assert body["requested_nodes"] == 0


def test_api_within_missing_query_is_200_with_false(env):
    tok = env.lic._encode_token(_payload(nodes=3), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is False
    assert body["requested_nodes"] == 0


def test_api_within_zero_and_negative(env):
    tok = env.lic._encode_token(_payload(nodes=5), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        r0 = c.get("/api/license/within-node-limit?nodes=0")
        rn = c.get("/api/license/within-node-limit?nodes=-3")
    for r, requested in ((r0, 0), (rn, 0)):
        assert r.status_code == 200
        body = r.get_json()
        assert body["within_limit"] is False
        assert body["requested_nodes"] == requested


def test_api_within_expired_returns_false(env):
    tok = env.lic._encode_token(_payload(nodes=5, exp_delta=-3600), env.priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/within-node-limit?nodes=1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["within_limit"] is False
    assert body["has_license"] is True
    assert body["valid"] is False
