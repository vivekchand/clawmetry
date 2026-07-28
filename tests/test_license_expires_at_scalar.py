"""Tests for the ``license_expires_at()`` / ``is_expiring_at()`` scalar
helpers in :mod:`clawmetry.license` plus their matching
``/api/license/expires-at`` and ``/api/license/is-expiring-at`` HTTP
endpoints.

Mirrors ``tests/test_license_issued_scalar.py``'s hermetic pattern --
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
    drop_exp=False,
    bad_exp=None,
):
    """Build a signed-payload dict. ``exp_delta`` shifts ``exp`` from now
    (negative = expired); ``drop_exp`` omits the claim (perpetual);
    ``bad_exp`` forces a non-numeric value."""
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now + iat_delta,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }
    if drop_exp:
        p.pop("exp", None)
    if bad_exp is not None:
        p["exp"] = bad_exp
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
    expired AFTER install or was signed with an anomalous ``exp``."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


# ── clawmetry.license.license_expires_at() ────────────────────────────────────


def test_license_expires_at_none_when_no_license(app):
    """No license file on disk -> None (nothing to surface)."""
    assert app.lic.license_expires_at() is None


def test_license_expires_at_active_returns_epoch(app):
    """Active licence -> the exact ``exp`` epoch, unmodified from the
    signed payload."""
    now = int(time.time())
    delta = 365 * 86400
    tok = app.lic._encode_token(_payload(exp_delta=delta), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert isinstance(expires, int)
    # Allow +/- 5s for wall-clock jitter around the call.
    assert (now + delta) - 5 <= expires <= (now + delta) + 5


def test_license_expires_at_expired_still_returns_epoch(app):
    """Expired-but-signed licence -> still surfaces ``exp``. Unlike
    :func:`license_tier` / :func:`license_nodes`, this scalar is lenient
    on expiry so a support UI can render "expired 12 days ago" on lapsed
    keys."""
    _write_key_direct(app, _payload(exp_delta=-12 * 86400))
    expires = app.lic.license_expires_at()
    assert isinstance(expires, int)
    assert expires < int(time.time())


def test_license_expires_at_invalid_signature(app):
    """File on disk but signature bogus -> None. An attacker could stuff
    any ``exp`` into an unsigned body, so we refuse to trust it."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_expires_at() is None


def test_license_expires_at_missing_exp_claim(app):
    """Perpetual license (no ``exp`` claim) -> None. Signed but nothing
    to surface. Callers distinguish perpetual from no-license via
    :func:`is_perpetual` + :func:`has_license`."""
    _write_key_direct(app, _payload(drop_exp=True))
    assert app.lic.license_expires_at() is None


def test_license_expires_at_non_numeric_exp(app):
    """Payload with a non-numeric ``exp`` -> None (never raises)."""
    _write_key_direct(app, _payload(bad_exp="never"))
    assert app.lic.license_expires_at() is None


def test_license_expires_at_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    current_license_info() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_expires_at() is None


def test_license_expires_at_matches_days_until_expiry_boundary(app):
    """The raw scalar and the derived days-until-expiry scalar are
    floor-divided from the SAME ``exp`` claim: for any active licence,
    ``days_until_expiry() == (expires_at - now) // 86400`` (allowing a
    +/- 1 day tolerance for the wall-clock crossing a day boundary
    between the two reads)."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    days = app.lic.days_until_expiry()
    assert isinstance(expires, int)
    assert isinstance(days, int)
    derived = (expires - int(time.time())) // 86400
    assert abs(derived - days) <= 1


# ── clawmetry.license.is_expiring_at() ────────────────────────────────────────


def test_is_expiring_at_false_when_no_license(app):
    """No license file -> False. Nothing to compare against."""
    assert app.lic.is_expiring_at(int(time.time()) + 86400) is False


def test_is_expiring_at_true_on_exact_match(app):
    """Active licence, epoch matches ``exp`` -> True."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert expires is not None
    assert app.lic.is_expiring_at(expires) is True


def test_is_expiring_at_false_on_off_by_one(app):
    """A one-second-off epoch is NOT a match. The predicate is exact."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert expires is not None
    assert app.lic.is_expiring_at(expires + 1) is False
    assert app.lic.is_expiring_at(expires - 1) is False


def test_is_expiring_at_false_on_expired_key(app):
    """Deliberately strict on validity: an already-lapsed key returns
    False even for the correct ``exp`` value. See docstring rationale."""
    _write_key_direct(app, _payload(exp_delta=-1 * 86400))
    expires = app.lic.license_expires_at()
    assert expires is not None  # scalar is lenient on expiry
    assert app.lic.is_expiring_at(expires) is False  # predicate is strict


def test_is_expiring_at_false_on_perpetual_key(app):
    """Perpetual licence (no ``exp``) -> False for any epoch."""
    _write_key_direct(app, _payload(drop_exp=True))
    assert app.lic.is_expiring_at(int(time.time()) + 86400) is False


def test_is_expiring_at_false_on_invalid_signature(app):
    """Invalid-signature branch -> False. An attacker could stuff any
    ``exp`` into an unsigned body."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.is_expiring_at(int(time.time()) + 86400) is False


def test_is_expiring_at_typo_input_returns_false(app):
    """Non-integer input collapses to False. A caller cannot silently
    mis-gate on a typo."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_at("not-a-number") is False  # type: ignore[arg-type]
    assert app.lic.is_expiring_at(None) is False  # type: ignore[arg-type]


def test_is_expiring_at_coerces_numeric_strings(app):
    """A numeric-string epoch coerces via int() and can match."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert expires is not None
    assert app.lic.is_expiring_at(str(expires)) is True  # type: ignore[arg-type]


def test_is_expiring_at_never_raises(monkeypatch):
    """Any underlying failure -> False. Never propagates."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.is_expiring_at(int(time.time()) + 86400) is False


# ── current_license_info() envelope carries ``exp`` on every branch ──────────


def test_current_license_info_active_carries_exp(app):
    tok = app.lic._encode_token(_payload(exp_delta=90 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert "exp" in info
    assert isinstance(info["exp"], (int, float))


def test_current_license_info_invalid_signature_exp_none(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert info["exp"] is None


def test_current_license_info_expired_carries_exp(app):
    _write_key_direct(app, _payload(exp_delta=-2 * 86400))
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    assert isinstance(info["exp"], (int, float))


# ── GET /api/license/expires-at ──────────────────────────────────────────────


def test_endpoint_expires_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "expires_at": None,
        "days_until_expiry": None,
        "has_license": False,
        "valid": False,
    }


def test_endpoint_expires_at_active(app):
    tok = app.lic._encode_token(_payload(exp_delta=60 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["expires_at"], int)
    assert isinstance(data["days_until_expiry"], int)
    assert 58 <= data["days_until_expiry"] <= 61
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_expires_at_expired(app):
    """Lenient on expiry: surface ``expires_at`` + signed ``days_until_expiry``
    on lapsed keys; ``valid=false`` carries the "signed but expired" signal."""
    _write_key_direct(app, _payload(exp_delta=-8 * 86400))
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["expires_at"], int)
    assert isinstance(data["days_until_expiry"], int)
    assert data["days_until_expiry"] < 0
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_expires_at_perpetual(app):
    """Perpetual licence (no ``exp``) -> ``expires_at=None`` but
    ``has_license=True``, so a UI distinguishes perpetual from no-license
    via ``has_license`` rather than a magic ``expires_at`` value."""
    _write_key_direct(app, _payload(drop_exp=True))
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expires_at"] is None
    assert data["days_until_expiry"] is None
    assert data["has_license"] is True


def test_endpoint_expires_at_invalid_file(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["has_license"] is True
    assert data["expires_at"] is None
    assert data["days_until_expiry"] is None
    assert data["valid"] is False


def test_endpoint_expires_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expires_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/expires-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "expires_at": None,
        "days_until_expiry": None,
        "has_license": False,
        "valid": False,
    }


# ── GET /api/license/is-expiring-at ──────────────────────────────────────────


def test_endpoint_is_expiring_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at?epoch=1800000000")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["requested_epoch"] == 1800000000
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_is_expiring_at_exact_match(app):
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert expires is not None
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at?epoch={expires}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expiring_at"] is True
    assert data["requested_epoch"] == expires
    assert data["expires_at"] == expires
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_expiring_at_off_by_one_rejected(app):
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    expires = app.lic.license_expires_at()
    assert expires is not None
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at?epoch={expires + 1}")
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["requested_epoch"] == expires + 1
    assert data["expires_at"] == expires


def test_endpoint_is_expiring_at_typo_rejected(app):
    """Non-integer ``epoch`` -> ``is_expiring_at=false`` with
    ``requested_epoch=null``. HTTP 200 either way -- the bad-input signal
    is the false result, not a 4xx."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at?epoch=tomorrow")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_is_expiring_at_missing_param(app):
    """No ``epoch`` at all -> false with ``requested_epoch=null``."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["requested_epoch"] is None


def test_endpoint_is_expiring_at_expired_key_rejected(app):
    """Deliberately strict on validity: an already-lapsed key returns
    ``is_expiring_at=false`` even for the correct ``exp`` value.
    ``expires_at`` still surfaces the actual on-disk value (lenient
    scalar) so the caller can see WHY the predicate said false."""
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    expires = app.lic.license_expires_at()
    assert expires is not None
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at?epoch={expires}")
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["expires_at"] == expires
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_expiring_at_perpetual_rejected(app):
    """Perpetual licence (no ``exp``) -> false for any epoch."""
    _write_key_direct(app, _payload(drop_exp=True))
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at?epoch=1800000000")
    data = resp.get_json()
    assert data["is_expiring_at"] is False
    assert data["expires_at"] is None
    assert data["has_license"] is True


# ── consistency: both endpoints see the same snapshot ────────────────────────


def test_both_endpoints_agree_on_snapshot(app):
    """Both endpoints share :func:`_license_expires_snapshot` -- they
    must surface identical ``expires_at`` / ``has_license`` / ``valid``
    values for the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=42 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        a = c.get("/api/license/expires-at").get_json()
        b = c.get("/api/license/is-expiring-at?epoch=1").get_json()
    for key in ("expires_at", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"


def test_expires_at_matches_days_until_expiry_endpoint_boundary(app):
    """``/api/license/expires-at`` and ``/api/license/days-until-expiry``
    are derived from the SAME ``exp`` claim: the scalar and the derived
    days must never disagree at the day boundary (allow +/- 1 for
    wall-clock crossings between the two reads). The two endpoints use
    different key names -- ``days_until_expiry`` here, ``days_left`` on
    the older endpoint -- but they floor-divide the same seconds."""
    tok = app.lic._encode_token(_payload(exp_delta=100 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        a = c.get("/api/license/expires-at").get_json()
        b = c.get("/api/license/days-until-expiry").get_json()
    assert isinstance(a["expires_at"], int)
    assert isinstance(a["days_until_expiry"], int)
    assert isinstance(b["days_left"], int)
    derived = (a["expires_at"] - int(time.time())) // 86400
    assert abs(derived - a["days_until_expiry"]) <= 1
    # Cross-endpoint consistency: the two derived-days scalars must agree.
    assert abs(a["days_until_expiry"] - b["days_left"]) <= 1
