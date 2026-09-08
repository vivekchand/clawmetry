"""Tests for the ``license_issued_at()`` / ``license_age_days()`` scalar
helpers in :mod:`clawmetry.license` plus their matching
``/api/license/issued-at`` and ``/api/license/age-days`` HTTP endpoints.

Mirrors ``tests/test_license_days_until_expiry.py``'s hermetic pattern --
ephemeral Ed25519 keypair, ``LICENSE_PATH`` monkeypatched into
``tmp_path``, and ``CLAWMETRY_OFFLINE=1`` so ``activate()`` never phones
home during the suite. Nothing here touches the operator's real license
file.
"""
from __future__ import annotations

import os
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


def _payload(
    tier="pro",
    nodes=3,
    exp_delta=365 * 86400,
    iat_delta=0,
    drop_iat=False,
    bad_iat=None,
):
    """Build a signed-payload dict. ``iat_delta`` shifts ``iat`` from now
    (negative = older); ``drop_iat`` omits the claim; ``bad_iat`` forces
    a non-numeric value."""
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now + iat_delta,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }
    if drop_iat:
        p.pop("iat", None)
    if bad_iat is not None:
        p["iat"] = bad_iat
    return p


@pytest.fixture
def app(monkeypatch, tmp_path):
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


def _write_key_direct(app, payload):
    """Bypass ``activate()`` (which refuses expired/malformed tokens) and
    write a token directly to the license file. Simulates a licence that
    expired AFTER install or was signed with an anomalous ``iat``."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


# ── clawmetry.license.license_issued_at() ─────────────────────────────────────


def test_license_issued_at_none_when_no_license(app):
    """No license file on disk -> None (nothing to surface)."""
    assert app.lic.license_issued_at() is None


def test_license_issued_at_active_returns_epoch(app):
    """Active licence -> the exact ``iat`` epoch, unmodified from the
    signed payload."""
    now = int(time.time())
    tok = app.lic._encode_token(_payload(iat_delta=-3600), app.priv)  # 1h ago
    app.lic.activate(tok)
    issued = app.lic.license_issued_at()
    assert isinstance(issued, int)
    # Allow +/- 5s for wall-clock jitter around the call.
    assert (now - 3600) - 5 <= issued <= (now - 3600) + 5


def test_license_issued_at_expired_still_returns_epoch(app):
    """Expired-but-signed licence -> still surfaces ``iat``. Unlike
    :func:`license_tier` / :func:`license_nodes`, this scalar is lenient
    on expiry so a support UI can render "issued 800 days ago" on lapsed
    keys."""
    _write_key_direct(app, _payload(iat_delta=-800 * 86400, exp_delta=-5 * 86400))
    issued = app.lic.license_issued_at()
    assert isinstance(issued, int)
    assert issued < int(time.time())


def test_license_issued_at_invalid_signature(app):
    """File on disk but signature bogus -> None. An attacker could stuff
    any ``iat`` into an unsigned body, so we refuse to trust it."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_issued_at() is None


def test_license_issued_at_missing_iat_claim(app):
    """Payload with no ``iat`` claim -> None. Signed but nothing to surface."""
    _write_key_direct(app, _payload(drop_iat=True))
    assert app.lic.license_issued_at() is None


def test_license_issued_at_non_numeric_iat(app):
    """Payload with a non-numeric ``iat`` -> None (never raises)."""
    _write_key_direct(app, _payload(bad_iat="tomorrow"))
    assert app.lic.license_issued_at() is None


def test_license_issued_at_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    current_license_info() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_issued_at() is None


# ── clawmetry.license.license_age_days() ──────────────────────────────────────


def test_license_age_days_none_when_no_license(app):
    assert app.lic.license_age_days() is None


def test_license_age_days_zero_on_day_of_issue(app):
    """Just-issued licence -> 0 days old."""
    tok = app.lic._encode_token(_payload(iat_delta=0), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_age_days() == 0


def test_license_age_days_positive_after_days(app):
    """Licence issued N days ago -> ~N days old (floor-divided from seconds)."""
    _write_key_direct(app, _payload(iat_delta=-30 * 86400))
    age = app.lic.license_age_days()
    assert isinstance(age, int)
    # Allow +/- 1 for clock jitter across the day boundary.
    assert 29 <= age <= 31


def test_license_age_days_works_on_expired_licence(app):
    """Expired-but-signed licence -> still returns an age. The scalar
    mirrors :func:`license_issued_at` (lenient on expiry)."""
    _write_key_direct(app, _payload(iat_delta=-400 * 86400, exp_delta=-30 * 86400))
    age = app.lic.license_age_days()
    assert isinstance(age, int)
    assert 399 <= age <= 401


def test_license_age_days_clock_skew_iat_in_future_clamps_to_zero(app):
    """A clock-skewed ``iat`` in the future must not render as a negative
    age -- clamped to 0 so callers can safely render ``f"{age} days old"``."""
    _write_key_direct(app, _payload(iat_delta=+7 * 86400))
    age = app.lic.license_age_days()
    assert age == 0


def test_license_age_days_invalid_signature(app):
    """File on disk but signature bogus -> None (refuse to derive age
    from an untrusted ``iat``)."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_age_days() is None


def test_license_age_days_missing_iat_claim(app):
    _write_key_direct(app, _payload(drop_iat=True))
    assert app.lic.license_age_days() is None


def test_license_age_days_never_raises(monkeypatch):
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_issued_at", _boom)
    assert _lic.license_age_days() is None


# ── current_license_info() / inspect_key() envelope carry ``issued_at`` ──────


def test_current_license_info_active_carries_issued_at(app):
    tok = app.lic._encode_token(_payload(iat_delta=-3600), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert "issued_at" in info
    assert isinstance(info["issued_at"], int)


def test_current_license_info_invalid_signature_issued_at_none(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert info["issued_at"] is None


def test_current_license_info_expired_carries_issued_at(app):
    _write_key_direct(app, _payload(iat_delta=-100 * 86400, exp_delta=-1 * 86400))
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert isinstance(info["issued_at"], int)


def test_inspect_key_carries_issued_at(app):
    """Dry-run inspector must expose ``issued_at`` too so a UI can render
    a "would install" summary the same way it renders the on-disk one."""
    tok = app.lic._encode_token(_payload(iat_delta=-2 * 86400), app.priv)
    dry = app.lic.inspect_key(tok)
    assert isinstance(dry, dict)
    assert "issued_at" in dry
    assert isinstance(dry["issued_at"], int)


# ── GET /api/license/issued-at ───────────────────────────────────────────────


def test_endpoint_issued_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/issued-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "issued_at": None,
        "age_days": None,
        "has_license": False,
        "valid": False,
    }


def test_endpoint_issued_at_active(app):
    tok = app.lic._encode_token(_payload(iat_delta=-3 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/issued-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["issued_at"], int)
    assert isinstance(data["age_days"], int)
    assert 2 <= data["age_days"] <= 4
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_issued_at_expired(app):
    """Lenient on expiry: surface ``issued_at`` + ``age_days`` on lapsed
    keys; ``valid=false`` carries the "signed but expired" signal."""
    _write_key_direct(app, _payload(iat_delta=-500 * 86400, exp_delta=-5 * 86400))
    with app.app.test_client() as c:
        resp = c.get("/api/license/issued-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["issued_at"], int)
    assert isinstance(data["age_days"], int)
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_issued_at_invalid_file(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get("/api/license/issued-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["has_license"] is True
    assert data["issued_at"] is None
    assert data["age_days"] is None
    assert data["valid"] is False


def test_endpoint_issued_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_issued_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/issued-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "issued_at": None,
        "age_days": None,
        "has_license": False,
        "valid": False,
    }


# ── GET /api/license/age-days ────────────────────────────────────────────────


def test_endpoint_age_days_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "age_days": None,
        "issued_at": None,
        "has_license": False,
        "valid": False,
    }


def test_endpoint_age_days_active(app):
    tok = app.lic._encode_token(_payload(iat_delta=-14 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert 13 <= data["age_days"] <= 15
    assert isinstance(data["issued_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_age_days_clock_skew_clamps_to_zero(app):
    """``iat`` in the future -> age_days clamps to 0, never negative."""
    _write_key_direct(app, _payload(iat_delta=+30 * 86400))
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] == 0
    assert data["has_license"] is True


def test_endpoint_age_days_missing_iat(app):
    _write_key_direct(app, _payload(drop_iat=True))
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["issued_at"] is None
    assert data["has_license"] is True


def test_endpoint_age_days_never_5xxs(app, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_issued_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "age_days": None,
        "issued_at": None,
        "has_license": False,
        "valid": False,
    }


# ── consistency: both endpoints see the same snapshot ────────────────────────


def test_both_endpoints_agree_on_snapshot(app):
    """Both endpoints share :func:`_license_issued_snapshot` -- they must
    surface identical ``issued_at`` / ``age_days`` / ``has_license`` /
    ``valid`` values for the same install."""
    tok = app.lic._encode_token(_payload(iat_delta=-42 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        a = c.get("/api/license/issued-at").get_json()
        b = c.get("/api/license/age-days").get_json()
    for key in ("issued_at", "age_days", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
