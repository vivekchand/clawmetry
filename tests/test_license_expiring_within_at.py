"""Tests for the ``is_expiring_within_at(days, epoch)`` boolean helper on
``clawmetry.license`` and its paired ``/api/license/expiring-within-at``
HTTP endpoint.

The perspective-epoch flavour of the ``is_expiring_within`` gate. Both
derive from the same signed ``exp`` claim so they cannot disagree at the
day boundary when the perspective epoch equals "now"; on any other
epoch this helper answers "was the license inside the ``days``-day
renewal window on <date>?" without the caller having to snapshot the
license state at that time.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + LICENSE_PATH, mirroring
``tests/test_license_days_until_expiry_at.py`` so nothing depends on the
real production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# ── shared helpers (mirror test_license_days_until_expiry_at.py) ─────────────


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


# ── clawmetry.license.is_expiring_within_at() ────────────────────────────────


def test_is_expiring_within_at_no_license(app):
    """No license file on disk -> False regardless of threshold / epoch."""
    now = int(time.time())
    assert app.lic.is_expiring_within_at(30, now) is False
    assert app.lic.is_expiring_within_at(0, now) is False


def test_is_expiring_within_at_now_matches_bare(app):
    """When ``epoch`` equals "now", the perspective helper must agree
    with :func:`is_expiring_within` for the same threshold. Both derive
    from the same signed ``exp`` claim; the sub-second drift between the
    two calls is at most one day (matching the day-boundary jitter that
    also affects ``days_until_expiry`` vs ``days_until_expiry_at``)."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    # Threshold well inside the window: both must fire True.
    assert app.lic.is_expiring_within_at(30, now) is True
    assert app.lic.is_expiring_within(30) is True
    # Threshold outside the window: both must be False.
    assert app.lic.is_expiring_within_at(5, now) is False
    assert app.lic.is_expiring_within(5) is False


def test_is_expiring_within_at_future_perspective_pulls_into_window(app):
    """A perspective epoch 20 days from now pulls an exp 45 days from
    now down to 25 days remaining, so a 30-day threshold fires True
    while a 20-day threshold fires False."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 20 * 86400
    assert app.lic.is_expiring_within_at(30, epoch) is True
    assert app.lic.is_expiring_within_at(20, epoch) is False


def test_is_expiring_within_at_past_perspective_pushes_out_of_window(app):
    """A perspective epoch 20 days ago pushes an exp 15 days from now
    to 35 days remaining, so a 30-day threshold that fires True at
    "now" fires False at that older perspective."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_expiring_within_at(30, now) is True
    epoch = now - 20 * 86400
    assert app.lic.is_expiring_within_at(30, epoch) is False


def test_is_expiring_within_at_already_lapsed_at_epoch_returns_false(app):
    """A perspective epoch AFTER ``exp`` means the key had already
    lapsed at that time -- the renewal-window gate must return False
    (that's the "already expired then" branch, not the "warn" branch).
    Callers wanting the negative day-count signal go through
    :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 45 * 86400  # 15 days past exp
    assert app.lic.is_expiring_within_at(30, epoch) is False
    # Even an enormous threshold cannot rescue a lapsed-at-epoch state.
    assert app.lic.is_expiring_within_at(10_000, epoch) is False


def test_is_expiring_within_at_perpetual_license(app):
    """Perpetual (no ``exp``) license -> False regardless of epoch.
    Nothing to warn about."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    now = int(time.time())
    assert app.lic.is_expiring_within_at(30, now) is False
    assert app.lic.is_expiring_within_at(30, 0) is False
    assert app.lic.is_expiring_within_at(30, 2_000_000_000) is False


def test_is_expiring_within_at_invalid_signature(app):
    """File on disk but signature bogus -> False. current_license_info()
    collapses the payload on this branch; the gate must reflect that."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.is_expiring_within_at(30, int(time.time())) is False


def test_is_expiring_within_at_negative_threshold(app):
    """Negative / non-numeric threshold -> False (nothing "expires
    within -5 days"). Mirrors :func:`is_expiring_within`."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_expiring_within_at(-1, now) is False
    assert app.lic.is_expiring_within_at("garbage", now) is False  # type: ignore[arg-type]
    assert app.lic.is_expiring_within_at(None, now) is False  # type: ignore[arg-type]


def test_is_expiring_within_at_threshold_zero_day_of_expiry(app):
    """``days=0`` should fire True only when perspective epoch falls
    within the same day as ``exp`` (``days_left == 0``). Mirrors the
    ``is_expiring_within(0)`` semantics."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    exp = info["exp"]
    assert app.lic.is_expiring_within_at(0, exp) is True
    assert app.lic.is_expiring_within_at(0, exp - 3600) is True  # <24h before
    # 5 days before exp -> outside the zero-day window.
    assert app.lic.is_expiring_within_at(0, exp - 5 * 86400) is False


def test_is_expiring_within_at_bool_epoch_rejected(app):
    """``bool`` is a subclass of ``int``; refuse it explicitly so a
    caller that passes ``True`` doesn't silently ask "is this expiring
    within N days as of epoch 1?" and get an ancient-history answer
    back. Mirrors :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_within_at(30, True) is False  # type: ignore[arg-type]
    assert app.lic.is_expiring_within_at(30, False) is False  # type: ignore[arg-type]


def test_is_expiring_within_at_non_numeric_epoch(app):
    """A caller passing a typo must get False, not a crash."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_expiring_within_at(30, "garbage") is False  # type: ignore[arg-type]
    assert app.lic.is_expiring_within_at(30, None) is False  # type: ignore[arg-type]
    assert app.lic.is_expiring_within_at(30, [1]) is False  # type: ignore[arg-type]


def test_is_expiring_within_at_float_epoch_coerced(app):
    """Float epoch must coerce through ``int()`` rather than crash --
    same posture as :func:`is_expiring_at` / :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now_f = float(time.time())
    assert isinstance(app.lic.is_expiring_within_at(30, now_f), bool)


def test_is_expiring_within_at_never_raises(monkeypatch):
    """Any underlying failure -> False. Even a fully-broken
    days_until_expiry_at() must not propagate."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "days_until_expiry_at", _boom)
    assert _lic.is_expiring_within_at(30, int(time.time())) is False


# ── GET /api/license/expiring-within-at ──────────────────────────────────────


def test_endpoint_expiring_within_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at?days=30&epoch={int(time.time())}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["threshold_days"] == 30
    assert isinstance(data["requested_epoch"], int)
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_expiring_within_at_inside_window(app):
    """Active key with 15 days left, threshold 30 -> True; days_left
    layered on for the "expires in N days" copy."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=30&epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is True
    assert isinstance(data["days_left"], int)
    assert 14 <= data["days_left"] <= 15
    assert data["threshold_days"] == 30
    assert data["requested_epoch"] == now
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_expiring_within_at_outside_window(app):
    """Active key with 45 days left, threshold 30 -> False, but the
    days_left / expires_at payload still populates so the widget can
    render "expires in 45 days"."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=30&epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert isinstance(data["days_left"], int)
    assert 43 <= data["days_left"] <= 45
    assert data["threshold_days"] == 30
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_expiring_within_at_future_perspective_pulls_into_window(app):
    """Perspective epoch 20 days from now pulls an exp 45 days out into
    the 30-day window -> gate fires True."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 20 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=30&epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is True
    assert isinstance(data["days_left"], int)
    assert 24 <= data["days_left"] <= 25
    assert data["requested_epoch"] == epoch


def test_endpoint_expiring_within_at_lapsed_at_epoch_gate_false_days_negative(app):
    """Perspective epoch AFTER ``exp`` -> gate collapses to False (the
    key had already lapsed then), BUT days_left still surfaces the
    (negative) real value so a support tile can render the pair. Mirrors
    the lenient posture of ``/api/license/days-until-expiry-at``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=30&epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert isinstance(data["days_left"], int)
    assert data["days_left"] < 0
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_expiring_within_at_perpetual_license(app):
    """Perpetual license -> gate False, days_left null, expires_at
    null, has_license True (there IS a file)."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at?days=30&epoch={int(time.time())}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is True


def test_endpoint_expiring_within_at_default_threshold_is_30(app):
    """No ``days=`` -> threshold defaults to 30. Matches the bare
    ``/api/license/expiring-within`` posture."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["threshold_days"] == 30
    assert data["expiring_within"] is True


def test_endpoint_expiring_within_at_missing_epoch_arg(app):
    """No ``epoch=`` -> gate False, requested_epoch null, days_left
    null. The snapshot still populates expires_at from the on-disk
    key."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-at?days=30")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["requested_epoch"] is None
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_expiring_within_at_non_integer_epoch(app):
    """Typo epoch -> gate False, requested_epoch null, HTTP 200 (never
    a 4xx). Mirrors the ``/api/license/is-expiring-at`` posture."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-at?days=30&epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_expiring_within_at_non_integer_days_collapses(app):
    """Typo threshold -> gate False, threshold_days 0, but days_left
    still populates (widget can still render the "expires in N days"
    copy even with the gate off)."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at?days=garbage&epoch={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["threshold_days"] == 0
    assert isinstance(data["days_left"], int)
    assert data["requested_epoch"] == now


def test_endpoint_expiring_within_at_negative_days_clamps_to_zero(app):
    """Negative threshold clamps to 0 -- gate fires True only on the
    exact day of expiry. Matches the bare ``/api/license/expiring-within``
    posture."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=-30&epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["threshold_days"] == 0
    assert data["expiring_within"] is False  # 15 days away, not the day-of


def test_endpoint_expiring_within_at_invalid_signature(app):
    """File on disk but signature bogus -> gate False, has_license True
    (there IS a file), valid False."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at?days=30&epoch={int(time.time())}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_expiring_within_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape (snapshot
    fallback kicks in; requested_epoch / threshold_days still echoed)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expires_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/expiring-within-at?days=30&epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["expiring_within"] is False
    assert data["days_left"] is None
    assert data["threshold_days"] == 30
    assert data["requested_epoch"] == epoch
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# ── cross-endpoint consistency ───────────────────────────────────────────────


def test_endpoint_agrees_with_expiring_within_at_now(app):
    """When ``epoch`` equals "now", the perspective endpoint must agree
    with ``/api/license/expiring-within`` for the same threshold. Both
    derive from the same signed ``exp`` claim; the sub-second drift
    between the two request handlers is at most one day (jitter also
    affects the paired ``days-until-expiry`` / ``days-until-expiry-at``
    endpoints)."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(
            f"/api/license/expiring-within-at?days=30&epoch={now}"
        ).get_json()
        b = c.get("/api/license/expiring-within?days=30").get_json()
    assert a["expiring_within"] == b["expiring_within"] is True
    assert isinstance(a["days_left"], int)
    assert isinstance(b["days_left"], int)
    assert abs(a["days_left"] - b["days_left"]) <= 1


def test_endpoint_agrees_with_days_until_expiry_at_on_shared_snapshot(app):
    """Both perspective-epoch endpoints share
    :func:`_license_expires_snapshot` -- they must surface identical
    ``expires_at`` / ``has_license`` / ``valid`` / ``days_left`` /
    ``requested_epoch`` for the same install & epoch. A UI binding
    both cannot catch them disagreeing on the shared quartet."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(
            f"/api/license/expiring-within-at?days=60&epoch={epoch}"
        ).get_json()
        b = c.get(
            f"/api/license/days-until-expiry-at?epoch={epoch}"
        ).get_json()
    for key in ("expires_at", "has_license", "valid", "days_left", "requested_epoch"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"


def test_endpoint_agrees_with_is_expiring_at_on_shared_snapshot(app):
    """The renewal-window gate and the exact-match predicate share the
    same snapshot reader -- ``expires_at`` / ``has_license`` / ``valid``
    must be identical for the same install regardless of the epoch
    queried."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(
            f"/api/license/expiring-within-at?days=30&epoch={epoch}"
        ).get_json()
        b = c.get(f"/api/license/is-expiring-at?epoch={epoch}").get_json()
    for key in ("expires_at", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
    assert a["requested_epoch"] == b["requested_epoch"] == epoch
