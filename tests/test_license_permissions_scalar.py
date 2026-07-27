"""Tests for the ``license_permissions_safe()`` / ``license_file_mode()``
scalar helpers in :mod:`clawmetry.license` plus their matching
``/api/license/permissions-safe`` and ``/api/license/file-mode`` HTTP
endpoints.

These scalars cover the on-disk hygiene axis of the license file --
independent from tier / subject / nodes, which gate on the signed
PAYLOAD. A tampered or expired license file still has meaningful
hygiene state (in fact, more urgent to surface -- loose permissions may
indicate the same corruption that broke the signature), so the
permission-hygiene branch deliberately never collapses to ``None`` on
the invalid-signature or expired branches the way ``license_tier`` /
``license_subject`` / ``license_nodes`` do.

Mirrors ``tests/test_license_subject_scalar.py``'s hermetic pattern --
ephemeral Ed25519 keypair, ``LICENSE_PATH`` monkeypatched into
``tmp_path``, and ``CLAWMETRY_OFFLINE=1`` so ``activate()`` never
phones home during the suite. Nothing here touches the operator's
real license file.
"""
from __future__ import annotations

import os
import sys
import time
from types import SimpleNamespace

import pytest
from flask import Flask


POSIX_ONLY = pytest.mark.skipif(
    sys.platform.startswith("win") or os.name != "posix",
    reason="POSIX file mode bits do not apply on Windows",
)


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
    _lic._warned_perms_for.clear()

    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True

    return SimpleNamespace(
        app=flask_app, lic=_lic, priv=priv, license_path=license_path
    )


def _write_raw(env, token: str, mode: int | None = None) -> None:
    with open(env.license_path, "w", encoding="utf-8") as fh:
        fh.write(token + "\n")
    if mode is not None and os.name == "posix":
        os.chmod(env.license_path, mode)


# -- license_permissions_safe() --


def test_license_permissions_safe_none_when_no_license(env):
    """No license file on disk -- nothing to protect, so the scalar
    returns None rather than True. A UI tile keying off this should
    render as "not applicable" not "safe"."""
    assert env.lic.license_permissions_safe() is None


@POSIX_ONLY
def test_license_permissions_safe_true_after_activate(env):
    """activate() writes 0o600 via _secure_write, so the scalar
    reports safe immediately after activation."""
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_permissions_safe() is True


@POSIX_ONLY
def test_license_permissions_safe_false_on_loose_mode(env):
    """A license file with any group/world bits set collapses to False --
    exactly the state a "tighten permissions" affordance should surface."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    assert env.lic.license_permissions_safe() is False


@POSIX_ONLY
def test_license_permissions_safe_false_on_world_writable(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o666)
    assert env.lic.license_permissions_safe() is False


@POSIX_ONLY
def test_license_permissions_safe_false_on_group_readable(env):
    """Just group-read (0o640) is enough to flag: the license is a bearer
    secret, so any group visibility is a leak."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o640)
    assert env.lic.license_permissions_safe() is False


@POSIX_ONLY
def test_license_permissions_safe_true_on_0o400(env):
    """0o400 -- owner-read-only -- has no group/world bits, so it's safe
    even though write access has been removed."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o400)
    assert env.lic.license_permissions_safe() is True


@POSIX_ONLY
def test_license_permissions_safe_true_on_expired_key(env):
    """The hygiene scalar is deliberately orthogonal to signature
    validity -- an expired key file with tight permissions still reads
    as safe (the "refuse untrusted claims" posture doesn't apply
    because we're not surfacing a claim, we're surfacing a mode)."""
    tok = env.lic._encode_token(_payload(exp_delta=-3600), env.priv)
    _write_raw(env, tok, mode=0o600)
    assert env.lic.license_permissions_safe() is True


@POSIX_ONLY
def test_license_permissions_safe_true_on_invalid_signature(env):
    """Same orthogonality: an unsigned / forged file with tight
    permissions still reads as safe on the hygiene axis. A UI that
    wants "is this trustworthy?" should combine this with
    /api/license/valid, not with this scalar alone."""
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(), other_priv)
    _write_raw(env, tok, mode=0o600)
    assert env.lic.license_permissions_safe() is True


@POSIX_ONLY
def test_license_permissions_safe_false_on_expired_with_loose_mode(env):
    """The MOST urgent state to surface: expired key AND loose permissions.
    The scalar reports False so a security tile can highlight both."""
    tok = env.lic._encode_token(_payload(exp_delta=-3600), env.priv)
    _write_raw(env, tok, mode=0o644)
    assert env.lic.license_permissions_safe() is False


def test_license_permissions_safe_never_raises(env, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated stat() failure")

    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    monkeypatch.setattr(env.lic.os.path, "isfile", _boom)
    assert env.lic.license_permissions_safe() is None


# -- license_file_mode() --


def test_license_file_mode_none_when_no_license(env):
    assert env.lic.license_file_mode() is None


@POSIX_ONLY
def test_license_file_mode_returns_octal_after_activate(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    assert env.lic.license_file_mode() == "0600"


@POSIX_ONLY
def test_license_file_mode_reflects_loose_mode(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    assert env.lic.license_file_mode() == "0644"


@POSIX_ONLY
def test_license_file_mode_reflects_world_writable(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o666)
    assert env.lic.license_file_mode() == "0666"


@POSIX_ONLY
def test_license_file_mode_reflects_owner_only(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o400)
    assert env.lic.license_file_mode() == "0400"


@POSIX_ONLY
def test_license_file_mode_always_four_digit_string(env):
    """Format is stable: always four characters, matching ``chmod`` --
    an operator can copy-paste the digits verbatim into a fix command."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o600)
    mode = env.lic.license_file_mode()
    assert isinstance(mode, str)
    assert len(mode) == 4
    assert mode.startswith("0")
    # All chars are valid octal digits (0-7).
    assert all(c in "01234567" for c in mode)


@POSIX_ONLY
def test_license_file_mode_reflects_expired_file(env):
    """Same orthogonality as permissions_safe: mode reflects the file's
    actual bits regardless of signature validity."""
    tok = env.lic._encode_token(_payload(exp_delta=-3600), env.priv)
    _write_raw(env, tok, mode=0o600)
    assert env.lic.license_file_mode() == "0600"


@POSIX_ONLY
def test_license_file_mode_reflects_invalid_signature(env):
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(), other_priv)
    _write_raw(env, tok, mode=0o600)
    assert env.lic.license_file_mode() == "0600"


def test_license_file_mode_never_raises(env, monkeypatch):
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated stat() failure")

    monkeypatch.setattr(env.lic.os, "stat", _boom)
    assert env.lic.license_file_mode() is None


def test_license_file_mode_none_on_windows(env, monkeypatch):
    """On Windows POSIX modes don't apply, so the scalar returns None
    even when a license file is present."""
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    monkeypatch.setattr(env.lic.os, "name", "nt")
    assert env.lic.license_file_mode() is None


# -- /api/license/permissions-safe --


def test_api_permissions_safe_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "permissions_safe": None,
        "file_mode": None,
        "has_license": False,
    }


@POSIX_ONLY
def test_api_permissions_safe_after_activate(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "permissions_safe": True,
        "file_mode": "0600",
        "has_license": True,
    }


@POSIX_ONLY
def test_api_permissions_safe_loose_mode(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["permissions_safe"] is False
    assert body["file_mode"] == "0644"
    assert body["has_license"] is True


@POSIX_ONLY
def test_api_permissions_safe_expired_key(env):
    """Signature-invalid / expired branch: the file IS on disk so
    has_license is True, permissions_safe reflects the real mode
    (orthogonal to signature validity)."""
    tok = env.lic._encode_token(_payload(exp_delta=-3600), env.priv)
    _write_raw(env, tok, mode=0o600)
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["permissions_safe"] is True
    assert body["file_mode"] == "0600"
    assert body["has_license"] is True


@POSIX_ONLY
def test_api_permissions_safe_invalid_signature(env):
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(), other_priv)
    _write_raw(env, tok, mode=0o600)
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["permissions_safe"] is True
    assert body["file_mode"] == "0600"
    assert body["has_license"] is True


def test_api_permissions_safe_never_5xx(env, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "license_permissions_safe", _boom)
    monkeypatch.setattr(env.lic, "license_file_mode", _boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/permissions-safe")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "permissions_safe": None,
        "file_mode": None,
        "has_license": False,
    }


# -- /api/license/file-mode --


def test_api_file_mode_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "file_mode": None,
        "permissions_safe": None,
        "has_license": False,
    }


@POSIX_ONLY
def test_api_file_mode_after_activate(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    env.lic.activate(tok)
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "file_mode": "0600",
        "permissions_safe": True,
        "has_license": True,
    }


@POSIX_ONLY
def test_api_file_mode_loose_mode(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["file_mode"] == "0644"
    assert body["permissions_safe"] is False
    assert body["has_license"] is True


@POSIX_ONLY
def test_api_file_mode_owner_only(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o400)
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["file_mode"] == "0400"
    assert body["permissions_safe"] is True


@POSIX_ONLY
def test_api_file_mode_world_writable(env):
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o666)
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["file_mode"] == "0666"
    assert body["permissions_safe"] is False


def test_api_file_mode_never_5xx(env, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "license_permissions_safe", _boom)
    monkeypatch.setattr(env.lic, "license_file_mode", _boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/file-mode")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "file_mode": None,
        "permissions_safe": None,
        "has_license": False,
    }


# -- cross-consistency between the pair --


@POSIX_ONLY
def test_scalar_matches_endpoint(env):
    """Scalar helpers and the endpoints must agree on the same install."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    scalar_safe = env.lic.license_permissions_safe()
    scalar_mode = env.lic.license_file_mode()
    with env.app.test_client() as c:
        perms_body = c.get("/api/license/permissions-safe").get_json()
        mode_body = c.get("/api/license/file-mode").get_json()
    assert perms_body["permissions_safe"] == scalar_safe
    assert perms_body["file_mode"] == scalar_mode
    assert mode_body["file_mode"] == scalar_mode
    assert mode_body["permissions_safe"] == scalar_safe


@POSIX_ONLY
def test_paired_endpoints_return_identical_snapshot(env):
    """The two endpoints share ``_license_permissions_snapshot`` -- so
    a UI binding both cannot catch them disagreeing on the trio."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o640)
    with env.app.test_client() as c:
        perms = c.get("/api/license/permissions-safe").get_json()
        mode = c.get("/api/license/file-mode").get_json()
    for field in ("permissions_safe", "file_mode", "has_license"):
        assert perms[field] == mode[field]


@POSIX_ONLY
def test_envelope_permissions_match_scalars(env):
    """The scalars must agree with the ``current_license_info`` envelope's
    ``permissions_safe`` / ``file_mode`` fields on the active branch --
    a UI mixing the two must never see them disagree."""
    tok = env.lic._encode_token(_payload(), env.priv)
    _write_raw(env, tok, mode=0o644)
    info = env.lic.current_license_info()
    assert env.lic.license_permissions_safe() == info["permissions_safe"]
    assert env.lic.license_file_mode() == info["file_mode"]


@POSIX_ONLY
def test_hygiene_orthogonal_to_valid(env):
    """A signature-invalid file with tight permissions surfaces
    ``permissions_safe=True`` even though ``/api/license/status`` reports
    ``valid=False``. This is the point: hygiene is a file-mode axis, not
    a payload-trust axis."""
    other_priv, _ = _keypair()
    tok = env.lic._encode_token(_payload(), other_priv)
    _write_raw(env, tok, mode=0o600)
    with env.app.test_client() as c:
        perms = c.get("/api/license/permissions-safe").get_json()
    assert perms["permissions_safe"] is True
    assert perms["has_license"] is True
    info = env.lic.current_license_info()
    assert info["valid"] is False  # signature check failed
    assert info["permissions_safe"] is True  # but mode is tight
