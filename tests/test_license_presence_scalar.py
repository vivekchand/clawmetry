"""Tests for the ``has_license`` / ``is_license_valid`` install-state scalar
helpers on ``clawmetry.license`` and their paired
``/api/license/{present,valid}`` endpoints on ``routes.entitlement``.

These two scalars are the top-level install-state gates a paywall UI needs:

* ``has_license`` -- bare file-exists check, regardless of signature /
  expiry. Answers "does this operator have ANY license file at all?", the
  signal a dashboard uses to distinguish "Free (never activated)" from
  "Free (license expired or broken)".
* ``is_license_valid`` -- installed AND signature-valid AND not expired.
  The single boolean a paywall tile actually wants: "is this node
  entitled right now?".

Both are OSS-safe observational scalars. Ships in GRACE -- no enforcement
gate changes, no behaviour shift.

Uses an ephemeral Ed25519 keypair (never the production key) and a
tmp_path license file so no real filesystem state is touched.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirrors test_license_is_expired_is_perpetual.py) --


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


# -- module-level scalar: has_license --


def test_has_license_no_license(env):
    """Bare install: no file on disk -> has_license is False."""
    assert env.lic.has_license() is False


def test_has_license_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    assert env.lic.has_license() is True


def test_has_license_expired(env):
    """Expired keys still count as PRESENT -- the presence gate cares only
    about file existence, not entitlement."""
    _install(env, _payload(exp_delta=-3600))
    assert env.lic.has_license() is True


def test_has_license_perpetual(env):
    _install(env, _payload(perpetual=True))
    assert env.lic.has_license() is True


def test_has_license_invalid_signature(env):
    """A forged / bit-flipped file still counts as PRESENT -- the presence
    gate is deliberately blind to signature validity so a UI can render a
    "broken license file, please re-activate" banner rather than "no
    license"."""
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    assert env.lic.has_license() is True


def test_has_license_never_raises(env, monkeypatch):
    def boom(_path):
        raise OSError("simulated fs failure")

    monkeypatch.setattr(env.lic.os.path, "isfile", boom)
    # Must degrade to False, not propagate the OSError.
    assert env.lic.has_license() is False


# -- module-level scalar: is_license_valid --


def test_is_license_valid_no_license(env):
    assert env.lic.is_license_valid() is False


def test_is_license_valid_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    assert env.lic.is_license_valid() is True


def test_is_license_valid_perpetual(env):
    """A signed lifetime key with no ``exp`` claim is valid indefinitely."""
    _install(env, _payload(perpetual=True))
    assert env.lic.is_license_valid() is True


def test_is_license_valid_expired(env):
    """An installed, signature-valid, PAST-``exp`` key is not entitled --
    the paywall gate must refuse a lapsed customer."""
    _install(env, _payload(exp_delta=-3600))
    assert env.lic.is_license_valid() is False


def test_is_license_valid_invalid_signature(env):
    """Untrusted body -- refuse to grant entitlement from an unsigned
    payload; an attacker could stuff any tier / exp into a forged file."""
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    assert env.lic.is_license_valid() is False


def test_is_license_valid_never_raises(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    assert env.lic.is_license_valid() is False


# -- has_license / is_license_valid layering --


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
def test_valid_implies_present(env, installer):
    """is_license_valid=True must never fire without has_license=True --
    entitlement requires a file, but the reverse (present but invalid)
    is a normal branch we surface deliberately."""
    installer(env)
    if env.lic.is_license_valid():
        assert env.lic.has_license() is True


# -- endpoint: /api/license/present --


_PRESENCE_SHAPE = {"present", "valid", "status"}


def test_endpoint_present_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _PRESENCE_SHAPE
    assert data["present"] is False
    assert data["valid"] is False
    assert data["status"] is None


def test_endpoint_present_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["present"] is True
    assert data["valid"] is True
    assert data["status"] == "active"


def test_endpoint_present_expired(env):
    _install(env, _payload(exp_delta=-3600))
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    # File exists (present) but the ``exp`` claim is past (not valid).
    assert data["present"] is True
    assert data["valid"] is False
    assert data["status"] == "expired"


def test_endpoint_present_invalid_signature(env):
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    # A forged file still counts as PRESENT -- a UI can render a
    # "broken license file" banner off ``status == "invalid"``.
    assert data["present"] is True
    assert data["valid"] is False
    assert data["status"] == "invalid"


def test_endpoint_present_perpetual(env):
    _install(env, _payload(perpetual=True))
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["present"] is True
    assert data["valid"] is True
    assert data["status"] == "active"


def test_endpoint_present_never_5xx(env, monkeypatch):
    """Broken install (import / crypto mismatch) must degrade to the
    no-license shape at HTTP 200 rather than 500 -- matches the never-crash
    posture of ``/api/license/status`` and the surrounding entitlement
    gate endpoints."""
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/present")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _PRESENCE_SHAPE
    # ``current_license_info`` blowing up only affects the ``valid`` /
    # ``status`` fields; the presence check is a bare ``isfile`` and stays
    # honest regardless. A missing file returns present=False.
    assert data["present"] is False
    assert data["valid"] is False
    assert data["status"] is None


# -- endpoint: /api/license/valid --


_VALID_SHAPE = {"present", "valid", "status"}


def test_endpoint_valid_no_license(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _VALID_SHAPE
    assert data["valid"] is False
    assert data["present"] is False
    assert data["status"] is None


def test_endpoint_valid_active(env):
    _install(env, _payload(exp_delta=365 * 86400))
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is True
    assert data["present"] is True
    assert data["status"] == "active"


def test_endpoint_valid_expired(env):
    """Expired-but-signed keys must return valid=false + status=expired --
    the paywall gate refuses a lapsed customer even though the signature
    still checks out."""
    _install(env, _payload(exp_delta=-3600))
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is False
    assert data["present"] is True
    assert data["status"] == "expired"


def test_endpoint_valid_invalid_signature(env):
    _install_raw(env, "CLAW1.eyJ0aWVyIjoicHJvIn0=.not_a_real_signature")
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is False
    assert data["present"] is True
    assert data["status"] == "invalid"


def test_endpoint_valid_perpetual(env):
    _install(env, _payload(perpetual=True))
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is True
    assert data["present"] is True
    assert data["status"] == "active"


def test_endpoint_valid_never_5xx(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(env.lic, "current_license_info", boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/valid")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _VALID_SHAPE
    # No license file on disk (fixture) => present is False, valid is False.
    assert data["valid"] is False
    assert data["present"] is False
    assert data["status"] is None


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
def test_endpoint_pair_snapshots_agree(env, installer):
    """The paired endpoints share a single snapshot -- they must return
    byte-identical (present, valid, status) triples on every branch."""
    installer(env)
    with env.app.test_client() as c:
        pres = c.get("/api/license/present").get_json()
        valid = c.get("/api/license/valid").get_json()
    assert pres["present"] == valid["present"]
    assert pres["valid"] == valid["valid"]
    assert pres["status"] == valid["status"]


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
def test_endpoint_matches_module_scalar(env, installer):
    """Envelope ``present`` / ``valid`` must byte-match the module-level
    scalar on every branch -- else a UI bound to the URL sees a different
    answer than a script importing the helper directly."""
    installer(env)
    with env.app.test_client() as c:
        pres = c.get("/api/license/present").get_json()
        valid = c.get("/api/license/valid").get_json()
    assert pres["present"] == env.lic.has_license()
    assert valid["valid"] == env.lic.is_license_valid()


@pytest.mark.parametrize(
    "installer",
    [
        pytest.param(lambda e: _install(e, _payload(exp_delta=365 * 86400)), id="active"),
        pytest.param(lambda e: _install(e, _payload(exp_delta=-3600)), id="expired"),
        pytest.param(lambda e: _install(e, _payload(perpetual=True)), id="perpetual"),
        pytest.param(lambda e: _install_raw(e, "CLAW1.bad.bad"), id="invalid"),
    ],
)
def test_endpoint_status_matches_status_endpoint(env, installer):
    """The ``status`` field on ``/api/license/{present,valid}`` must match
    the ``status`` field on ``/api/license/status`` for the same install --
    else a UI binding one field from each URL sees inconsistent state."""
    installer(env)
    with env.app.test_client() as c:
        pres = c.get("/api/license/present").get_json()
        status = c.get("/api/license/status").get_json()
    # ``/api/license/status`` on the no-license branch returns
    # {"has_license": False, ...} without a "status" key, but this
    # parametrisation always installs some file, so ``status`` is set.
    assert pres["status"] == status.get("status")


def test_endpoint_valid_implies_present(env):
    """valid=True must never fire without present=True on the endpoint pair
    -- entitlement requires a file. Mirrors the module-scalar invariant."""
    for installer in (
        lambda: None,
        lambda: _install(env, _payload(exp_delta=365 * 86400)),
        lambda: _install(env, _payload(exp_delta=-3600)),
        lambda: _install(env, _payload(perpetual=True)),
        lambda: _install_raw(env, "CLAW1.bad.bad"),
    ):
        installer()
        with env.app.test_client() as c:
            data = c.get("/api/license/valid").get_json()
        if data["valid"]:
            assert data["present"] is True
