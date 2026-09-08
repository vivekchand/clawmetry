"""Tests for the license-tier scalar helpers and endpoints.

Covers:
  * clawmetry.license.license_tier()   -- module-level scalar.
  * clawmetry.license.is_tier()        -- boolean gate.
  * GET /api/license/tier              -- envelope, never-5xx.
  * GET /api/license/is-tier           -- envelope, never-5xx, bad-input degrade.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + LICENSE_PATH so nothing
depends on the real production signing key or on real filesystem state.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_days_until_expiry.py) ---------------


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


def _write_key_direct(app, exp_delta, tier="pro"):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed -- the branch current_license_info() has to handle."""
    tok = app.lic._encode_token(_payload(tier=tier, exp_delta=exp_delta), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


# -- clawmetry.license.license_tier() ----------------------------------------


def test_license_tier_no_license(app):
    """No license file on disk -> None (nothing trustworthy to surface)."""
    assert app.lic.license_tier() is None


def test_license_tier_active_pro(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() == "pro"


def test_license_tier_active_enterprise(app):
    tok = app.lic._encode_token(_payload(tier="enterprise"), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() == "enterprise"


def test_license_tier_open_ended(app):
    """A future tier lands without a code change -- helper is deliberately
    open-ended, not a hard-coded enum."""
    tok = app.lic._encode_token(_payload(tier="ultra"), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() == "ultra"


def test_license_tier_normalises_casing(app):
    """A tier stored as ``"Pro"`` or ``"  PRO "`` -> lowercased + stripped."""
    tok = app.lic._encode_token(_payload(tier="  PRO  "), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() == "pro"


def test_license_tier_expired_collapses_to_none(app):
    """Expired keys collapse to None -- a lapsed Pro customer must NOT keep
    rendering as ``"pro"`` until they re-activate. The gate matches
    is_expired() semantics."""
    _write_key_direct(app, exp_delta=-5 * 86400, tier="pro")
    assert app.lic.license_tier() is None


def test_license_tier_invalid_signature(app):
    """File exists but signature bogus -> None. Never trust an unsigned
    body's tier claim; a forger could stuff any value."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_tier() is None


def test_license_tier_empty_string_claim(app):
    """A payload with ``tier=""`` -> None (nothing to gate off empty string)."""
    tok = app.lic._encode_token(_payload(tier=""), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() is None


def test_license_tier_whitespace_only_claim(app):
    """A payload with ``tier="   "`` -> None after strip."""
    tok = app.lic._encode_token(_payload(tier="   "), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier() is None


def test_license_tier_non_string_claim(app, monkeypatch):
    """A payload with ``tier=123`` -> None (never returns non-string)."""
    monkeypatch.setattr(
        app.lic,
        "current_license_info",
        lambda: {"valid": True, "tier": 123, "status": "active"},
    )
    assert app.lic.license_tier() is None


def test_license_tier_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    current_license_info() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_tier() is None


# -- clawmetry.license.is_tier() ---------------------------------------------


def test_is_tier_no_license(app):
    """No license -> False regardless of the requested tier."""
    assert app.lic.is_tier("pro") is False
    assert app.lic.is_tier("enterprise") is False


def test_is_tier_matching(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier("pro") is True


def test_is_tier_non_matching(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier("enterprise") is False


def test_is_tier_case_insensitive_query(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier("Pro") is True
    assert app.lic.is_tier("  PRO ") is True


def test_is_tier_case_insensitive_stored(app):
    """A tier stored as ``"Enterprise"`` still matches a plain
    ``"enterprise"`` query -- both sides are normalised."""
    tok = app.lic._encode_token(_payload(tier="Enterprise"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier("enterprise") is True


def test_is_tier_expired_is_not_current(app):
    """An expired Pro install returns False even for ``is_tier('pro')`` --
    the gate asks 'am I entitled right now', not 'was I ever entitled'."""
    _write_key_direct(app, exp_delta=-5 * 86400, tier="pro")
    assert app.lic.is_tier("pro") is False


def test_is_tier_invalid_signature(app):
    """Bogus file -> False regardless of the requested tier."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.is_tier("pro") is False


def test_is_tier_empty_query(app):
    """Empty / whitespace-only query -> False. Nothing 'is tier <blank>'."""
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier("") is False
    assert app.lic.is_tier("   ") is False


def test_is_tier_non_string_query(app):
    """Non-string / None input coerces safely to False without a TypeError."""
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier(None) is False  # type: ignore[arg-type]
    assert app.lic.is_tier(0) is False  # type: ignore[arg-type]


def test_is_tier_never_raises(monkeypatch):
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.is_tier("pro") is False


# -- GET /api/license/tier ---------------------------------------------------


def test_endpoint_tier_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"tier": None, "has_license": False, "valid": False}


def test_endpoint_tier_active(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"tier": "pro", "has_license": True, "valid": True}


def test_endpoint_tier_expired(app):
    """Expired install -> tier collapses to None but has_license stays True
    and valid flips to False. A UI can drive both 'no Pro right now' and
    'you had Pro' banners off one call."""
    _write_key_direct(app, exp_delta=-5 * 86400, tier="pro")
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["tier"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_tier_invalid_file(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["tier"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_tier_normalises_casing(app):
    tok = app.lic._encode_token(_payload(tier="  PRO "), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    assert resp.get_json()["tier"] == "pro"


def test_endpoint_tier_never_5xxs(app, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_tier_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"tier": None, "has_license": False, "valid": False}


# -- GET /api/license/is-tier ------------------------------------------------


def test_endpoint_is_tier_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=pro")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "is_tier": False,
        "tier": None,
        "requested_tier": "pro",
        "has_license": False,
        "valid": False,
    }


def test_endpoint_is_tier_matching(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=pro")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is True
    assert data["tier"] == "pro"
    assert data["requested_tier"] == "pro"
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_tier_non_matching(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=enterprise")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is False
    assert data["tier"] == "pro"
    assert data["requested_tier"] == "enterprise"
    assert data["valid"] is True


def test_endpoint_is_tier_case_insensitive(app):
    tok = app.lic._encode_token(_payload(tier="Enterprise"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=ENTERPRISE")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is True
    assert data["tier"] == "enterprise"
    assert data["requested_tier"] == "enterprise"


def test_endpoint_is_tier_expired_is_not_current(app):
    """Expired install -> is_tier=false even for the tier the payload
    carries -- ``valid`` still surfaces False so a UI can render an
    'was Pro, renew' banner from one call."""
    _write_key_direct(app, exp_delta=-5 * 86400, tier="pro")
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=pro")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is False
    assert data["tier"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_tier_empty_query(app):
    """Missing / empty ``tier`` param -> HTTP 200 with is_tier=false and
    requested_tier='' (never a 4xx)."""
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is False
    assert data["requested_tier"] == ""
    assert data["tier"] == "pro"
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_tier_whitespace_query(app):
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=%20%20")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is False
    assert data["requested_tier"] == ""


def test_endpoint_is_tier_never_5xxs(app, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_tier_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-tier?tier=pro")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_tier"] is False
    assert data["tier"] is None
    assert data["requested_tier"] == "pro"
    assert data["has_license"] is False
    assert data["valid"] is False


# -- cross-consistency --------------------------------------------------------


def test_tier_endpoints_agree_on_has_license(app):
    """Both endpoints must return the same ``has_license`` for the same
    install -- otherwise a UI binding one to each URL sees inconsistent
    state."""
    for scenario in ("none", "active", "expired", "invalid"):
        if scenario == "active":
            tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
            app.lic.activate(tok)
        elif scenario == "expired":
            _write_key_direct(app, exp_delta=-1 * 86400, tier="pro")
        elif scenario == "invalid":
            os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
            with open(app.license_path, "w", encoding="utf-8") as fh:
                fh.write("CLAW1.garbage.garbage")
        with app.app.test_client() as c:
            a = c.get("/api/license/tier").get_json()
            b = c.get("/api/license/is-tier?tier=pro").get_json()
        assert a["has_license"] == b["has_license"], scenario
        assert a["valid"] == b["valid"], scenario
        assert a["tier"] == b["tier"], scenario
        # Reset for next iteration.
        if os.path.exists(app.license_path):
            os.unlink(app.license_path)


def test_scalar_matches_endpoint(app):
    """The module-level scalar and the endpoint's ``tier`` field must
    byte-match across every install branch -- else a caller bound to one
    can see a different tier than a caller bound to the other."""
    # active
    tok = app.lic._encode_token(_payload(tier="pro"), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        assert c.get("/api/license/tier").get_json()["tier"] == app.lic.license_tier()

    # expired
    os.unlink(app.license_path)
    _write_key_direct(app, exp_delta=-1 * 86400, tier="pro")
    with app.app.test_client() as c:
        assert c.get("/api/license/tier").get_json()["tier"] == app.lic.license_tier()
    assert app.lic.license_tier() is None

    # invalid
    os.unlink(app.license_path)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        assert c.get("/api/license/tier").get_json()["tier"] == app.lic.license_tier()
    assert app.lic.license_tier() is None

    # no-license
    os.unlink(app.license_path)
    with app.app.test_client() as c:
        assert c.get("/api/license/tier").get_json()["tier"] == app.lic.license_tier()
    assert app.lic.license_tier() is None
