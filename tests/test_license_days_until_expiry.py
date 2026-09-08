"""Tests for the days-until-expiry scalar helpers and endpoints.

Covers:
  * clawmetry.license.days_until_expiry() -- module-level scalar.
  * clawmetry.license.is_expiring_within() -- bool gate.
  * GET /api/license/days-until-expiry -- envelope, never-5xx.
  * GET /api/license/expiring-within  -- envelope, never-5xx, bad-input degrade.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + LICENSE_PATH so nothing
depends on the real production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# ── shared helpers (mirror test_license_api.py) ───────────────────────────────


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, drop_exp=False):
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }
    if drop_exp:
        p.pop("exp", None)
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


# ── clawmetry.license.days_until_expiry() ────────────────────────────────────


def test_days_until_expiry_no_license(app):
    """No license file on disk -> None (nothing to count down)."""
    assert app.lic.days_until_expiry() is None


def test_days_until_expiry_active_license(app):
    """Active license with a normal exp -> positive int roughly matching the delta."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    days = app.lic.days_until_expiry()
    assert isinstance(days, int)
    # Floor-divided from seconds; allow +/- 1 for clock jitter around midnight.
    assert 28 <= days <= 30


def test_days_until_expiry_zero_on_day_of_expiry(app):
    """A license expiring in <24h -> 0. Sign matters: caller distinguishes
    "expires today" from "expired 3 days ago" without a second call."""
    tok = app.lic._encode_token(_payload(exp_delta=3600), app.priv)  # 1h
    app.lic.activate(tok)
    days = app.lic.days_until_expiry()
    assert days == 0


def _write_key_direct(app, exp_delta):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed -- the branch current_license_info() has to handle."""
    import os

    tok = app.lic._encode_token(_payload(exp_delta=exp_delta), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def test_days_until_expiry_negative_on_expired_license(app):
    """Expired license -> negative int, NOT None. current_license_info()
    already accepts an expired-but-signed token; the scalar helper must
    surface the same sign so a UI can render "expired N days ago"."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    days = app.lic.days_until_expiry()
    assert isinstance(days, int)
    assert days < 0
    assert -6 <= days <= -4


def test_days_until_expiry_perpetual_license(app, monkeypatch):
    """Payload with no ``exp`` claim -> None. Perpetual keys don't count
    down. Bypass activate() (which forbids exp-less tokens) by encoding
    directly and writing the token file."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.days_until_expiry() is None


def test_days_until_expiry_invalid_signature(app):
    """File on disk but signature bogus -> None. current_license_info()
    already collapses tier/exp/days_left to None on this branch; the
    scalar must reflect that."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.days_until_expiry() is None


def test_days_until_expiry_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    current_license_info() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.days_until_expiry() is None


# ── clawmetry.license.is_expiring_within() ───────────────────────────────────


def test_is_expiring_within_no_license(app):
    """No license -> False regardless of the window."""
    assert app.lic.is_expiring_within(30) is False
    assert app.lic.is_expiring_within(0) is False


def test_is_expiring_within_perpetual_license(app):
    """Perpetual (no exp) license -> False. Nothing to warn about."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.is_expiring_within(30) is False


def test_is_expiring_within_inside_window(app):
    """Active license expiring in 5 days, threshold 30 -> True."""
    tok = app.lic._encode_token(_payload(exp_delta=5 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_within(30) is True


def test_is_expiring_within_outside_window(app):
    """Active license expiring in 60 days, threshold 30 -> False."""
    tok = app.lic._encode_token(_payload(exp_delta=60 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_within(30) is False


def test_is_expiring_within_already_expired(app):
    """Expired license -> False (a different, louder banner covers that
    case; is_expiring_within is renewal-window only)."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    assert app.lic.is_expiring_within(30) is False


def test_is_expiring_within_negative_threshold(app):
    """Negative or bad threshold -> False. Nothing expires within -5 days."""
    tok = app.lic._encode_token(_payload(exp_delta=5 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_within(-1) is False
    assert app.lic.is_expiring_within("garbage") is False  # type: ignore[arg-type]


def test_is_expiring_within_threshold_zero_matches_day_of(app):
    """Threshold 0 -> True only on the day of expiry (days_left == 0)."""
    tok = app.lic._encode_token(_payload(exp_delta=3600), app.priv)  # 1h
    app.lic.activate(tok)
    assert app.lic.is_expiring_within(0) is True


def test_is_expiring_within_never_raises(monkeypatch):
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.is_expiring_within(30) is False


# ── GET /api/license/days-until-expiry ───────────────────────────────────────


def test_endpoint_days_until_expiry_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"days_left": None, "has_license": False, "expired": False}


def test_endpoint_days_until_expiry_active(app):
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["days_left"], int)
    assert 43 <= data["days_left"] <= 45
    assert data["has_license"] is True
    assert data["expired"] is False


def test_endpoint_days_until_expiry_expired(app):
    _write_key_direct(app, exp_delta=-5 * 86400)
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["days_left"], int)
    assert data["days_left"] < 0
    assert data["has_license"] is True
    assert data["expired"] is True


def test_endpoint_days_until_expiry_invalid_file(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry")
    assert resp.status_code == 200
    data = resp.get_json()
    # File present but unverified -> the license library reports has_license
    # (there IS a file) but no meaningful days_left / expired.
    assert data["has_license"] is True
    assert data["days_left"] is None
    assert data["expired"] is False


def test_endpoint_days_until_expiry_never_5xxs(app, monkeypatch):
    """Even if the license module blows up mid-request, the endpoint must
    still return HTTP 200 with the OSS-free shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expiry_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"days_left": None, "has_license": False, "expired": False}


# ── GET /api/license/expiring-within ─────────────────────────────────────────


def test_endpoint_expiring_within_default_window_no_license(app):
    """Bare hit (no ``days=``) defaults to 30 and returns a sensible shape."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 30
    assert data["has_license"] is False
    assert data["expired"] is False
    assert data["days_left"] is None


def test_endpoint_expiring_within_inside_window(app):
    tok = app.lic._encode_token(_payload(exp_delta=5 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is True
    assert data["threshold_days"] == 30
    assert data["has_license"] is True
    assert data["expired"] is False
    assert isinstance(data["days_left"], int)


def test_endpoint_expiring_within_outside_window(app):
    tok = app.lic._encode_token(_payload(exp_delta=60 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 30
    assert data["has_license"] is True
    assert data["expired"] is False


def test_endpoint_expiring_within_expired_is_not_expiring(app):
    """An already-expired install is NOT ``expiring_within=true`` -- caller
    branches off ``expired`` for the loud banner instead."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["expired"] is True
    assert data["has_license"] is True
    assert isinstance(data["days_left"], int)
    assert data["days_left"] < 0


def test_endpoint_expiring_within_bad_days_degrades_gracefully(app):
    """Non-integer ``days`` -> HTTP 200 with ``expiring_within=false`` and
    ``threshold_days=0`` (not a 4xx)."""
    tok = app.lic._encode_token(_payload(exp_delta=5 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=notanumber")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 0
    assert data["has_license"] is True


def test_endpoint_expiring_within_negative_days_clamped_to_zero(app):
    """Negative ``days`` clamps to 0 (still HTTP 200); an active license
    that isn't on its day-of-expiry returns False."""
    tok = app.lic._encode_token(_payload(exp_delta=5 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=-30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 0


def test_endpoint_expiring_within_threshold_zero_matches_day_of(app):
    """``days=0`` + license expiring in <24h -> True (matches
    ``is_expiring_within(0)`` semantics)."""
    tok = app.lic._encode_token(_payload(exp_delta=3600), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is True
    assert data["threshold_days"] == 0
    assert data["days_left"] == 0


def test_endpoint_expiring_within_never_5xxs(app, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expiry_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within?days=30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 30
    assert data["has_license"] is False
    assert data["expired"] is False
    assert data["days_left"] is None
