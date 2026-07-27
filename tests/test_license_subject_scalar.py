"""Tests for the ``license_subject()`` / ``is_subject()`` scalar helpers in
:mod:`clawmetry.license` plus their matching ``/api/license/subject`` and
``/api/license/is-subject`` HTTP endpoints.

Mirrors ``tests/test_license_nodes_scalar.py``'s hermetic pattern --
ephemeral Ed25519 keypair, ``LICENSE_PATH`` monkeypatched into
``tmp_path``, and ``CLAWMETRY_OFFLINE=1`` so ``activate()`` never phones
home during the suite. Nothing here touches the operator's real license
file.
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


def _payload(sub="acct_test", tier="pro", nodes=1, exp_delta=365 * 86400):
    now = int(time.time())
    payload = {
        "sub": sub,
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "features": ["runtimes"],
    }
    if exp_delta is not None:
        payload["exp"] = now + exp_delta
    return payload


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


# ── license_subject() ─────────────────────────────────────────────────────────


def test_license_subject_none_when_no_license(env):
    assert env.lic.license_subject() is None


def test_license_subject_active_returns_string(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() == "acme@company.com"


def test_license_subject_preserves_casing(env):
    # Subjects (emails, account ids) can be case-sensitive for exact-match
    # display, so the scalar preserves the operator-visible form verbatim.
    # is_subject() handles case-insensitive matching separately.
    tok = env.lic._encode_token(_payload(sub="Acct_MixedCase"), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() == "Acct_MixedCase"


def test_license_subject_strips_whitespace(env):
    tok = env.lic._encode_token(_payload(sub="  acme@company.com  "), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() == "acme@company.com"


def test_license_subject_expired_collapses_to_none(env):
    # A lapsed customer must NOT keep rendering as "Licensed to <X>" via
    # the scalar helper -- matches the license_tier() / license_nodes()
    # posture for expired keys.
    tok = env.lic._encode_token(
        _payload(sub="acme@company.com", exp_delta=-3600), env.priv
    )
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    assert env.lic.license_subject() is None


def test_license_subject_invalid_signature_collapses_to_none(env):
    """An unsigned / forged file must NOT surface a trusted subject."""
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(sub="attacker@evil.com"), other_priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    assert env.lic.license_subject() is None


def test_license_subject_missing_claim_collapses(env):
    """A signed payload with an empty ``sub`` claim collapses to None (an
    empty-string identifier is meaningless -- refuse it rather than
    surface it)."""
    tok = env.lic._encode_token(_payload(sub=""), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() is None


def test_license_subject_whitespace_only_claim_collapses(env):
    tok = env.lic._encode_token(_payload(sub="   "), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() is None


def test_license_subject_perpetual_key_returns_string(env):
    # No ``exp`` at all — the perpetual branch of current_license_info
    # returns valid=True with days_left=None, and the scalar surfaces the
    # subject just like it does for a normal active key.
    tok = env.lic._encode_token(_payload(sub="lifetime@company.com", exp_delta=None), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_subject() == "lifetime@company.com"


def test_license_subject_never_raises_on_broken_read(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", _boom)
    # Wrapped in try/except in the helper -> collapses to None.
    assert env.lic.license_subject() is None


# ── is_subject(subject) ───────────────────────────────────────────────────────


def test_is_subject_false_when_no_license(env):
    assert env.lic.is_subject("acme@company.com") is False


def test_is_subject_true_on_exact_match(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject("acme@company.com") is True


def test_is_subject_true_case_insensitive(env):
    tok = env.lic._encode_token(_payload(sub="Acme@Company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject("ACME@COMPANY.COM") is True
    assert env.lic.is_subject("acme@company.com") is True


def test_is_subject_strips_whitespace_on_query(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject("  acme@company.com  ") is True


def test_is_subject_false_on_mismatch(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject("other@company.com") is False


def test_is_subject_rejects_empty_and_whitespace(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject("") is False
    assert env.lic.is_subject("   ") is False


def test_is_subject_rejects_non_string(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    assert env.lic.is_subject(None) is False  # type: ignore[arg-type]
    assert env.lic.is_subject(42) is False  # type: ignore[arg-type]


def test_is_subject_expired_key_returns_false(env):
    tok = env.lic._encode_token(
        _payload(sub="acme@company.com", exp_delta=-3600), env.priv
    )
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    # Even with the exact subject, an expired license refuses the gate.
    assert env.lic.is_subject("acme@company.com") is False


def test_is_subject_invalid_signature_returns_false(env):
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), other_priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    assert env.lic.is_subject("acme@company.com") is False


# ── /api/license/subject ──────────────────────────────────────────────────────


def test_api_license_subject_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"subject": None, "has_license": False, "valid": False}


def test_api_license_subject_active(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "subject": "acme@company.com",
        "has_license": True,
        "valid": True,
    }


def test_api_license_subject_expired(env):
    tok = env.lic._encode_token(
        _payload(sub="acme@company.com", exp_delta=-3600), env.priv
    )
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    assert resp.status_code == 200
    body = resp.get_json()
    # subject collapses to null on the expired branch, but has_license
    # stays True — the file IS on disk, just no longer trusted for gating.
    assert body["subject"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_license_subject_invalid_signature(env):
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(sub="attacker@evil.com"), other_priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["subject"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_license_subject_never_5xx(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", _boom)
    monkeypatch.setattr(env.lic, "license_subject", _boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"subject": None, "has_license": False, "valid": False}


# ── /api/license/is-subject ───────────────────────────────────────────────────


def test_api_is_subject_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["has_license"] is False
    assert body["valid"] is False
    assert body["requested_subject"] == "acme@company.com"
    assert body["subject"] is None


def test_api_is_subject_exact_match(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is True
    assert body["subject"] == "acme@company.com"
    assert body["requested_subject"] == "acme@company.com"
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_is_subject_case_insensitive(env):
    tok = env.lic._encode_token(_payload(sub="Acme@Company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is True
    # subject echoes the stored (casing-preserved) form
    assert body["subject"] == "Acme@Company.com"
    # requested_subject echoes the query (already stripped)
    assert body["requested_subject"] == "acme@company.com"


def test_api_is_subject_mismatch(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=other@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["subject"] == "acme@company.com"
    assert body["requested_subject"] == "other@company.com"
    assert body["valid"] is True


def test_api_is_subject_empty_query_is_200_with_false(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["subject"] == "acme@company.com"
    assert body["requested_subject"] == ""


def test_api_is_subject_missing_query_is_200_with_false(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["requested_subject"] == ""


def test_api_is_subject_whitespace_query_collapses_to_empty(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=%20%20%20")
    assert resp.status_code == 200
    body = resp.get_json()
    # Whitespace-only strips to the empty branch, which returns False.
    assert body["is_subject"] is False
    assert body["requested_subject"] == ""


def test_api_is_subject_strips_whitespace_on_query(env):
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=%20acme@company.com%20")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is True
    assert body["requested_subject"] == "acme@company.com"


def test_api_is_subject_expired_returns_false(env):
    tok = env.lic._encode_token(
        _payload(sub="acme@company.com", exp_delta=-3600), env.priv
    )
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_is_subject_invalid_signature_returns_false(env):
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), other_priv)
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_is_subject_never_5xx(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", _boom)
    monkeypatch.setattr(env.lic, "license_subject", _boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=acme@company.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_subject"] is False
    # snapshot degrades — subject falls through as None
    assert body["subject"] is None


# ── cross-consistency ─────────────────────────────────────────────────────────


def test_scalar_matches_envelope_field(env):
    """The scalar helper and current_license_info()['sub'] should agree on
    the value for every branch where the scalar returns non-None."""
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    info = env.lic.current_license_info()
    scalar = env.lic.license_subject()
    # info['sub'] is the raw payload string; scalar is the stripped form.
    assert scalar == info["sub"].strip()


def test_scalar_and_endpoint_agree(env):
    """The scalar helper and the /api/license/subject endpoint must
    return the SAME subject for the same install."""
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    scalar = env.lic.license_subject()
    with env.app.test_client() as c:
        resp = c.get("/api/license/subject")
    body = resp.get_json()
    assert body["subject"] == scalar


def test_is_subject_and_endpoint_agree(env):
    """The is_subject() bool and the /api/license/is-subject endpoint
    must return the SAME verdict for the same query on the same install."""
    tok = env.lic._encode_token(_payload(sub="acme@company.com"), env.priv)
    env.lic.activate(tok)
    scalar = env.lic.is_subject("ACME@company.com")
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-subject?subject=ACME@company.com")
    body = resp.get_json()
    assert body["is_subject"] == scalar
