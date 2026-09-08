"""Tests for the ``is_expired`` / ``is_perpetual`` scalar helpers on
``clawmetry.license`` and their paired ``/api/license/is-{expired,perpetual}``
endpoints on ``routes.entitlement``.

These are the two boolean gates on the license-lifecycle axis:

* ``is_expired`` -- installed, signature-valid, ``exp`` in the past.
* ``is_perpetual`` -- installed, signature-valid, no ``exp`` claim.

They complement the ``is_expiring_within`` renewal-window helper (already in
flight on a sibling PR) and let a paywall UI bind directly to a boolean URL
without parsing the full ``/api/license/status`` envelope.

Uses an ephemeral Ed25519 keypair (never the production key) and a tmp_path
license file so no real file system state is touched.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirrors test_license_api.py) --


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, perpetual=False):
    now = int(time.time())
    body = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "features": ["runtimes"],
    }
    if not perpetual:
        body["exp"] = now + exp_delta
    return body


# -- fixtures --


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Isolated license env: ephemeral pubkey, tmp license path, no network."""
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
        app=flask_app,
        lic=_lic,
        priv=priv,
        license_path=license_path,
    )


def _install(env, payload):
    """Write a signed token to the license path (bypasses ``activate``'s
    phone-home)."""
    tok = env.lic._encode_token(payload, env.priv)
    env.lic._secure_write(env.license_path, tok)


def _install_raw(env, raw: str):
    """Write raw (possibly-forged) contents to the license path."""
    env.lic._secure_write(env.license_path, raw)


# -- module-level scalar: is_expired --


def test_is_expired_no_license(env):
    assert env.lic.is_expired() is False


def test_is_expired_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    assert env.lic.is_expired() is False


def test_is_expired_expired(env):
    _install(env, _payload(exp_delta=-3600))
    assert env.lic.is_expired() is True


def test_is_expired_perpetual(env):
    """Lifetime keys must NOT surface as expired -- perpetual is neither
    expired nor expiring."""
    _install(env, _payload(perpetual=True))
    assert env.lic.is_expired() is False


def test_is_expired_invalid_signature(env):
    """An invalid-signature branch must NOT surface as expired -- a forger
    could stuff any ``exp`` into an unsigned body, so we refuse to trust it."""
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    assert env.lic.is_expired() is False


def test_is_expired_never_raises(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    # Must degrade to False, not propagate the RuntimeError.
    assert env.lic.is_expired() is False


# -- module-level scalar: is_perpetual --


def test_is_perpetual_no_license(env):
    assert env.lic.is_perpetual() is False


def test_is_perpetual_active_timed(env):
    """A signed key with an ``exp`` claim is NOT perpetual, even while active."""
    _install(env, _payload(exp_delta=365 * 86400))
    assert env.lic.is_perpetual() is False


def test_is_perpetual_expired_timed(env):
    """A signed key with an ``exp`` claim in the past is expired, not
    perpetual -- the two gates are mutually exclusive on the same install."""
    _install(env, _payload(exp_delta=-3600))
    assert env.lic.is_perpetual() is False


def test_is_perpetual_true_when_no_exp_claim(env):
    _install(env, _payload(perpetual=True))
    assert env.lic.is_perpetual() is True


def test_is_perpetual_rejects_invalid_signature(env):
    """An invalid-signature branch collapses ``exp`` to ``None`` in
    ``current_license_info``, but we must NOT infer "perpetual" from an
    untrusted body -- a forger could produce a bogus file to bypass the
    renewal counter entirely."""
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    assert env.lic.is_perpetual() is False


def test_is_perpetual_never_raises(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    assert env.lic.is_perpetual() is False


# -- expired / perpetual mutual exclusion --


@pytest.mark.parametrize(
    "installer",
    [
        lambda e: None,  # no license
        lambda e: _install(e, _payload(exp_delta=365 * 86400)),  # active
        lambda e: _install(e, _payload(exp_delta=-3600)),  # expired
        lambda e: _install(e, _payload(perpetual=True)),  # perpetual
        lambda e: _install_raw(e, "CLAW1.bad.bad"),  # invalid
    ],
)
def test_expired_and_perpetual_never_both_true(env, installer):
    """The two gates are mutually exclusive -- a UI reading both should never
    have to decide which to prefer."""
    installer(env)
    assert not (env.lic.is_expired() and env.lic.is_perpetual())


# -- endpoint: /api/license/is-expired --


_EXPIRED_SHAPE = {"expired", "has_license", "status"}


def test_endpoint_is_expired_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _EXPIRED_SHAPE
    assert data["expired"] is False
    assert data["has_license"] is False
    assert data["status"] is None


def test_endpoint_is_expired_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expired"] is False
    assert data["has_license"] is True
    assert data["status"] == "active"


def test_endpoint_is_expired_expired(env):
    _install(env, _payload(exp_delta=-3600))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expired"] is True
    assert data["has_license"] is True
    assert data["status"] == "expired"


def test_endpoint_is_expired_perpetual(env):
    _install(env, _payload(perpetual=True))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expired"] is False
    assert data["has_license"] is True
    assert data["status"] == "active"  # perpetual keys are active


def test_endpoint_is_expired_invalid_signature(env):
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    # An invalid signature must NOT surface as "expired" -- the UI wants the
    # quieter "invalid" branch instead of the loud "expired" banner.
    assert data["expired"] is False
    assert data["has_license"] is True
    assert data["status"] == "invalid"


def test_endpoint_is_expired_never_5xx(env, monkeypatch):
    """Broken install (import / crypto mismatch) must degrade to the
    no-license shape at HTTP 200 rather than 500 -- matches the never-crash
    posture of ``/api/license/status`` and ``/api/entitlement``."""
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _EXPIRED_SHAPE
    assert data["expired"] is False
    assert data["has_license"] is False
    assert data["status"] is None


# -- endpoint: /api/license/is-perpetual --


_PERPETUAL_SHAPE = {"perpetual", "has_license", "has_exp"}


def test_endpoint_is_perpetual_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _PERPETUAL_SHAPE
    assert data["perpetual"] is False
    assert data["has_license"] is False
    assert data["has_exp"] is False


def test_endpoint_is_perpetual_active_timed(env):
    _install(env, _payload(exp_delta=365 * 86400))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["perpetual"] is False
    assert data["has_license"] is True
    assert data["has_exp"] is True


def test_endpoint_is_perpetual_expired_timed(env):
    _install(env, _payload(exp_delta=-3600))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    # Expired-timed is NOT perpetual; ``has_exp`` still True because the ``exp``
    # claim exists on-disk regardless of active-vs-past.
    assert data["perpetual"] is False
    assert data["has_license"] is True
    assert data["has_exp"] is True


def test_endpoint_is_perpetual_true(env):
    _install(env, _payload(perpetual=True))
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["perpetual"] is True
    assert data["has_license"] is True
    assert data["has_exp"] is False


def test_endpoint_is_perpetual_rejects_invalid_signature(env):
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    # Invalid branch: perpetual False (we don't trust the unsigned body),
    # has_license True (the file exists), has_exp False (the invalid branch
    # collapses ``exp`` to None on purpose).
    assert data["perpetual"] is False
    assert data["has_license"] is True
    assert data["has_exp"] is False


def test_endpoint_is_perpetual_never_5xx(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/is-perpetual")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _PERPETUAL_SHAPE
    assert data["perpetual"] is False
    assert data["has_license"] is False
    assert data["has_exp"] is False


# -- cross-consistency between the endpoint pair --


@pytest.mark.parametrize(
    "installer",
    [
        pytest.param(lambda e: None, id="no_license"),
        pytest.param(lambda e: _install(e, _payload(exp_delta=365 * 86400)), id="active"),
        pytest.param(lambda e: _install(e, _payload(exp_delta=-3600)), id="expired"),
        pytest.param(lambda e: _install(e, _payload(perpetual=True)), id="perpetual"),
        pytest.param(lambda e: _install_raw(e, "CLAW1.bad.bad"), id="invalid"),
    ],
)
def test_endpoint_pair_agrees_on_has_license(env, installer):
    """The paired endpoints share a single snapshot -- they must agree on
    ``has_license`` for every branch."""
    installer(env)
    with env.app.test_client() as c:
        exp_resp = c.get("/api/license/is-expired").get_json()
        per_resp = c.get("/api/license/is-perpetual").get_json()
    assert exp_resp["has_license"] == per_resp["has_license"]


@pytest.mark.parametrize(
    "installer",
    [
        pytest.param(lambda e: None, id="no_license"),
        pytest.param(lambda e: _install(e, _payload(exp_delta=365 * 86400)), id="active"),
        pytest.param(lambda e: _install(e, _payload(exp_delta=-3600)), id="expired"),
        pytest.param(lambda e: _install(e, _payload(perpetual=True)), id="perpetual"),
        pytest.param(lambda e: _install_raw(e, "CLAW1.bad.bad"), id="invalid"),
    ],
)
def test_endpoint_expired_and_perpetual_never_both_true(env, installer):
    """The two gates are mutually exclusive on every install branch."""
    installer(env)
    with env.app.test_client() as c:
        exp_resp = c.get("/api/license/is-expired").get_json()
        per_resp = c.get("/api/license/is-perpetual").get_json()
    assert not (exp_resp["expired"] and per_resp["perpetual"])


def test_endpoint_matches_module_scalar(env):
    """Envelope ``expired`` / ``perpetual`` must byte-match the module-level
    scalar on every branch -- else a UI bound to the URL sees a different
    answer than a script importing the helper directly."""
    for installer in (
        lambda: None,
        lambda: _install(env, _payload(exp_delta=365 * 86400)),
        lambda: _install(env, _payload(exp_delta=-3600)),
        lambda: _install(env, _payload(perpetual=True)),
    ):
        installer()
        with env.app.test_client() as c:
            exp_resp = c.get("/api/license/is-expired").get_json()
            per_resp = c.get("/api/license/is-perpetual").get_json()
        assert exp_resp["expired"] == env.lic.is_expired()
        assert per_resp["perpetual"] == env.lic.is_perpetual()


def test_endpoint_status_matches_status_endpoint(env):
    """The ``status`` field on ``/api/license/is-expired`` must match the
    ``status`` field on ``/api/license/status`` for the same install -- else
    a UI binding one field from each URL sees inconsistent state."""
    for installer in (
        lambda: _install(env, _payload(exp_delta=365 * 86400)),
        lambda: _install(env, _payload(exp_delta=-3600)),
        lambda: _install(env, _payload(perpetual=True)),
        lambda: _install_raw(env, "CLAW1.bad.bad"),
    ):
        installer()
        with env.app.test_client() as c:
            gate = c.get("/api/license/is-expired").get_json()
            status = c.get("/api/license/status").get_json()
        assert gate["status"] == status["status"]
