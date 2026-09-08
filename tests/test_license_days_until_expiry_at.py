"""Tests for the ``days_until_expiry_at(epoch)`` scalar helper on
``clawmetry.license`` and its paired ``/api/license/days-until-expiry-at``
HTTP endpoint.

The perspective-epoch flavour of the ``days_until_expiry`` scalar. Both
derive from the same signed ``exp`` claim so they cannot disagree at the
day boundary when the perspective epoch equals "now"; on any other
epoch this helper answers "how many days from ``epoch`` until (or past)
expiry?" without the caller having to snapshot the license state at
that time or do the ``(exp - epoch) // 86400`` arithmetic themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + LICENSE_PATH, mirroring
``tests/test_license_days_until_expiry.py`` so nothing depends on the
real production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# ── shared helpers (mirror test_license_days_until_expiry.py) ────────────────


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


def _write_key_direct(app, exp_delta):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed."""
    import os

    tok = app.lic._encode_token(_payload(exp_delta=exp_delta), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


# ── clawmetry.license.days_until_expiry_at() ─────────────────────────────────


def test_days_until_expiry_at_no_license(app):
    """No license file on disk -> None (nothing to count down against)."""
    assert app.lic.days_until_expiry_at(int(time.time())) is None


def test_days_until_expiry_at_now_matches_days_until_expiry(app):
    """When ``epoch`` equals "now", the perspective-epoch scalar must
    agree with :func:`days_until_expiry` at the day boundary (+/- 1 for
    the fractional-second drift between the two calls: the base scalar
    reads ``time.time()`` with sub-second precision inside
    ``current_license_info``, while the caller here passes an
    ``int(time.time())`` that already truncated the fraction)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    at_now = app.lic.days_until_expiry_at(now)
    scalar_now = app.lic.days_until_expiry()
    assert isinstance(at_now, int)
    assert isinstance(scalar_now, int)
    assert abs(at_now - scalar_now) <= 1


def test_days_until_expiry_at_future_epoch(app):
    """A perspective epoch 10 days from now should count down 20 days
    against an exp 30 days from now."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    days = app.lic.days_until_expiry_at(epoch)
    assert isinstance(days, int)
    # Floor-divided; allow +/- 1 for the day-boundary jitter that also
    # affects days_until_expiry itself.
    assert 19 <= days <= 20


def test_days_until_expiry_at_past_epoch(app):
    """A perspective epoch 5 days ago should count 35 days remaining
    against an exp 30 days from now."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 5 * 86400
    days = app.lic.days_until_expiry_at(epoch)
    assert isinstance(days, int)
    assert 34 <= days <= 35


def test_days_until_expiry_at_negative_when_epoch_past_exp(app):
    """An operator asking "how many days past expiry would we have been
    on <date>?" -- a perspective epoch AFTER ``exp`` -> negative int,
    NOT None. The scalar must let a support tile render "expired 10 days
    before that date" without a second call."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 45 * 86400
    days = app.lic.days_until_expiry_at(epoch)
    assert isinstance(days, int)
    assert days < 0
    # exp - epoch = 30d - 45d = -15d.
    assert -16 <= days <= -14


def test_days_until_expiry_at_zero_on_day_of_expiry(app):
    """Perspective epoch on the day of expiry -> 0."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    # Snap perspective to the same second as exp so (exp - epoch)//86400 == 0.
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    exp = info["exp"]
    assert app.lic.days_until_expiry_at(exp) == 0
    assert app.lic.days_until_expiry_at(exp - 3600) == 0  # <24h before


def test_days_until_expiry_at_signed_but_lapsed_still_countable(app):
    """A lapsed-but-signed key must still surface a meaningful
    ``days_left`` at an arbitrary perspective epoch -- support scenario
    "when did we tell them it was going to lapse, evaluated as of last
    Friday?". Mirrors :func:`license_expires_at`'s lenient posture."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # expired 5 days ago
    # Perspective epoch 20 days BEFORE the current time -> the exp was
    # (5 + 20) = 25 days INTO the future then, so days_left ~ +15.
    epoch = int(time.time()) - 20 * 86400
    days = app.lic.days_until_expiry_at(epoch)
    assert isinstance(days, int)
    assert 14 <= days <= 15


def test_days_until_expiry_at_perpetual_license(app):
    """Perpetual (no ``exp``) license -> None regardless of perspective
    epoch. Nothing to count down to."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.days_until_expiry_at(int(time.time())) is None
    assert app.lic.days_until_expiry_at(0) is None
    assert app.lic.days_until_expiry_at(2_000_000_000) is None


def test_days_until_expiry_at_invalid_signature(app):
    """File on disk but signature bogus -> None. current_license_info()
    already collapses the payload on this branch; the scalar must
    reflect that."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.days_until_expiry_at(int(time.time())) is None


def test_days_until_expiry_at_non_numeric_epoch(app):
    """A caller passing a typo must get None, not a crash."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.days_until_expiry_at("garbage") is None  # type: ignore[arg-type]
    assert app.lic.days_until_expiry_at(None) is None  # type: ignore[arg-type]
    assert app.lic.days_until_expiry_at([1]) is None  # type: ignore[arg-type]


def test_days_until_expiry_at_bool_epoch_rejected(app):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently get "days until
    epoch 1" back."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.days_until_expiry_at(True) is None  # type: ignore[arg-type]
    assert app.lic.days_until_expiry_at(False) is None  # type: ignore[arg-type]


def test_days_until_expiry_at_float_epoch_coerced(app):
    """Float epoch must coerce through ``int()`` rather than crash --
    same posture as :func:`is_expiring_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now_f = float(time.time())
    days = app.lic.days_until_expiry_at(now_f)
    assert isinstance(days, int)


def test_days_until_expiry_at_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    license_expires_at() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_expires_at", _boom)
    assert _lic.days_until_expiry_at(int(time.time())) is None


# ── GET /api/license/days-until-expiry-at ────────────────────────────────────


def test_endpoint_days_until_expiry_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert isinstance(data["requested_epoch"], int)
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_days_until_expiry_at_active(app):
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["days_left"], int)
    assert 43 <= data["days_left"] <= 45
    assert data["requested_epoch"] == now
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_days_until_expiry_at_negative_for_past_epoch(app):
    """Perspective epoch AFTER ``exp`` -> negative days_left, expires_at
    still populated so a support tile can render the pair without a
    second call."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["days_left"], int)
    assert data["days_left"] < 0
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_days_until_expiry_at_lapsed_key_still_surfaces_days(app):
    """A lapsed-but-signed key evaluated at a pre-lapse perspective
    epoch -> positive days_left. ``valid`` is False (signature valid
    but past expiry now) so a caller that wants to hide the row on
    lapsed keys has the signal."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    epoch = int(time.time()) - 20 * 86400  # 15 days before the exp
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["days_left"], int)
    assert 14 <= data["days_left"] <= 15
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_days_until_expiry_at_perpetual_license(app):
    """Perpetual license -> days_left null even for a valid epoch."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is True


def test_endpoint_days_until_expiry_at_missing_epoch_arg(app):
    """No ``epoch=`` -> days_left null, requested_epoch null, HTTP 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert data["requested_epoch"] is None
    # The snapshot still populates expires_at from the on-disk key.
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_days_until_expiry_at_non_integer_epoch(app):
    """Typo epoch -> days_left null, requested_epoch null, HTTP 200
    (never a 4xx). Mirrors the ``/api/license/is-expiring-at`` posture."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_days_until_expiry_at_invalid_signature(app):
    """File on disk but signature bogus -> days_left null, has_license
    True (there IS a file), valid False."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_days_until_expiry_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape (snapshot fallback
    kicks in, requested_epoch is still echoed, days_left is null)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expires_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["days_left"] is None
    assert data["requested_epoch"] == epoch
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# ── cross-endpoint consistency ───────────────────────────────────────────────


def test_endpoint_agrees_with_days_until_expiry_at_now(app):
    """When ``epoch`` equals "now", the perspective endpoint must
    agree with ``/api/license/days-until-expiry`` at the day boundary
    (+/- 1 for the fractional-second drift between the two request
    handlers: the base endpoint reads ``time.time()`` with sub-second
    precision inside ``current_license_info`` at handle-time, while the
    perspective endpoint receives an ``int(time.time())`` from the
    caller that already truncated the fraction). Both derive from the
    same signed ``exp`` claim, so a UI binding both cannot catch them
    disagreeing by more than a day for the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/days-until-expiry-at?epoch={now}").get_json()
        b = c.get("/api/license/days-until-expiry").get_json()
    assert isinstance(a["days_left"], int)
    assert isinstance(b["days_left"], int)
    assert abs(a["days_left"] - b["days_left"]) <= 1


def test_endpoint_agrees_with_is_expiring_at_on_shared_snapshot(app):
    """Both perspective-epoch endpoints share :func:`_license_expires_snapshot`
    -- they must surface identical ``expires_at`` / ``has_license`` /
    ``valid`` for the same install regardless of the epoch queried."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(f"/api/license/days-until-expiry-at?epoch={epoch}").get_json()
        b = c.get(f"/api/license/is-expiring-at?epoch={epoch}").get_json()
    for key in ("expires_at", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
    assert a["requested_epoch"] == b["requested_epoch"] == epoch
