"""Tests for the ``is_expired_at(epoch)`` scalar helper on
``clawmetry.license`` and its paired ``/api/license/is-expired-at``
HTTP endpoint.

The perspective-epoch flavour of the ``is_expired`` boolean gate. Both
derive from the same signed ``exp`` claim so they cannot disagree at
the boundary when the perspective epoch equals "now"; on any other
epoch this helper answers "was the license expired evaluated as of
``epoch``?" without the caller having to snapshot the license state at
that time or compare ``exp`` to a caller-supplied epoch themselves.

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


# -- shared helpers (mirror test_license_days_until_expiry_at.py) -------------


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


# -- clawmetry.license.is_expired_at() ----------------------------------------


def test_is_expired_at_no_license(app):
    """No license file on disk -> False (nothing to compare against)."""
    assert app.lic.is_expired_at(int(time.time())) is False
    assert app.lic.is_expired_at(0) is False
    assert app.lic.is_expired_at(2_000_000_000) is False


def test_is_expired_at_now_matches_is_expired_on_active(app):
    """When ``epoch`` equals "now", the perspective-epoch gate must agree
    with :func:`is_expired` on the same install. Both derive from the same
    signed ``exp`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary for an active key."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_expired_at(now) is False
    assert app.lic.is_expired() is False


def test_is_expired_at_now_matches_is_expired_on_lapsed(app):
    """A signed-but-lapsed key must return True on the "now" perspective,
    matching :func:`is_expired` -- both use the ``exp <= now`` cutoff so
    they cannot disagree at the boundary."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # expired 5 days ago
    now = int(time.time())
    assert app.lic.is_expired_at(now) is True
    assert app.lic.is_expired() is True


def test_is_expired_at_future_epoch_before_expiry(app):
    """A perspective epoch in the future, but still before ``exp`` -> False
    (the key would NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400  # 20 days before exp
    assert app.lic.is_expired_at(epoch) is False


def test_is_expired_at_future_epoch_after_expiry(app):
    """A perspective epoch AFTER ``exp`` on an active key -> True (the
    key WILL be expired at that perspective). This is the "will this key
    be expired at our next audit?" support scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.is_expired_at(epoch) is True


def test_is_expired_at_past_epoch_before_issuance(app):
    """A perspective epoch BEFORE the current time on an active key ->
    False (the key was not yet expired then, since exp is even further
    in the future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.is_expired_at(epoch) is False


def test_is_expired_at_exact_exp_epoch(app):
    """At the exact ``exp`` second, the predicate must fire ``True`` --
    the ``<= epoch`` cutoff matches :func:`is_expired`'s
    ``status == "expired"`` derivation (which uses ``exp <= now``)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    exp = info["exp"]
    assert app.lic.is_expired_at(exp) is True
    assert app.lic.is_expired_at(exp - 1) is False


def test_is_expired_at_lapsed_key_still_fires_true_at_now(app):
    """A lapsed-but-signed key evaluated at "now" -> True (the current
    support scenario). Deliberately lenient on expiry NOW, unlike
    :func:`is_expiring_at`."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    assert app.lic.is_expired_at(int(time.time())) is True


def test_is_expired_at_lapsed_key_false_at_pre_lapse_epoch(app):
    """A lapsed-but-signed key evaluated at a perspective epoch BEFORE
    its ``exp`` -> False. The retrospective question "was this expired
    on <date> a week before it lapsed?" is answerable without special-
    casing the expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    # Perspective 20 days before now = 15 days before exp -> not yet expired.
    epoch = int(time.time()) - 20 * 86400
    assert app.lic.is_expired_at(epoch) is False


def test_is_expired_at_perpetual_license(app):
    """Perpetual (no ``exp``) license -> False regardless of perspective
    epoch. Nothing to compare against; matches :func:`is_expired`'s
    False branch for perpetual keys."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.is_expired_at(int(time.time())) is False
    assert app.lic.is_expired_at(0) is False
    assert app.lic.is_expired_at(2_000_000_000) is False


def test_is_expired_at_invalid_signature(app):
    """File on disk but signature bogus -> False. We refuse to trust
    ``exp`` on an unsigned payload -- an attacker could stuff any value
    into it. Matches :func:`is_expired`'s untrusted-body posture."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.is_expired_at(int(time.time())) is False
    assert app.lic.is_expired_at(2_000_000_000) is False


def test_is_expired_at_non_numeric_epoch(app):
    """A caller passing a typo must get False, not a crash."""
    tok = app.lic._encode_token(_payload(exp_delta=-5 * 86400), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.is_expired_at("garbage") is False  # type: ignore[arg-type]
    assert app.lic.is_expired_at(None) is False  # type: ignore[arg-type]
    assert app.lic.is_expired_at([1]) is False  # type: ignore[arg-type]
    assert app.lic.is_expired_at({}) is False  # type: ignore[arg-type]


def test_is_expired_at_bool_epoch_rejected(app):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently ask "was the key expired
    at epoch 1?" and get a positive answer back."""
    # Use a lapsed key so the question "expired at epoch 1?" would
    # otherwise trivially answer True on the (exp <= 1) cutoff -- proving
    # the refusal is real, not accidental.
    _write_key_direct(app, exp_delta=-5 * 86400)
    assert app.lic.is_expired_at(True) is False  # type: ignore[arg-type]
    assert app.lic.is_expired_at(False) is False  # type: ignore[arg-type]


def test_is_expired_at_float_epoch_coerced(app):
    """Float epoch must coerce through ``int()`` rather than crash --
    same posture as :func:`is_expiring_at` / :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now_f = float(time.time())
    assert app.lic.is_expired_at(now_f) is False


def test_is_expired_at_never_raises(monkeypatch):
    """Any underlying failure -> False. Even a fully-broken
    license_expires_at() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_expires_at", _boom)
    assert _lic.is_expired_at(int(time.time())) is False


# -- GET /api/license/is-expired-at -------------------------------------------


def test_endpoint_is_expired_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert isinstance(data["requested_epoch"], int)
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_is_expired_at_active_at_now(app):
    """Active key at "now" -> is_expired_at false, valid true, expires_at
    populated for the sibling tile that renders the date."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["requested_epoch"] == now
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_expired_at_active_at_future_after_exp(app):
    """Active key evaluated at a perspective epoch AFTER ``exp`` ->
    is_expired_at true, valid still true (the key is not expired NOW)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is True
    assert data["requested_epoch"] == epoch
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_expired_at_lapsed_key_at_now(app):
    """Lapsed-but-signed key at "now" -> is_expired_at true, valid FALSE
    (signature valid but expired now). Retrospective banner can bind
    is_expired_at; a caller that wants to hide the row on lapsed keys
    still has the ``valid`` signal."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is True
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_expired_at_lapsed_key_at_pre_lapse_epoch(app):
    """Lapsed-but-signed key at a perspective epoch BEFORE its ``exp`` ->
    is_expired_at false, valid still false (key is expired NOW). The
    predicate flips independently of the current-state validity."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    epoch = int(time.time()) - 20 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_expired_at_perpetual_license(app):
    """Perpetual license -> is_expired_at false at any epoch. expires_at
    null because no ``exp`` claim; has_license true (there IS a file)."""
    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["expires_at"] is None
    assert data["has_license"] is True


def test_endpoint_is_expired_at_missing_epoch_arg(app):
    """No ``epoch=`` -> is_expired_at false, requested_epoch null, HTTP
    200. The snapshot still populates expires_at from the on-disk key."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expired-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["requested_epoch"] is None
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_is_expired_at_non_integer_epoch(app):
    """Typo epoch -> is_expired_at false, requested_epoch null, HTTP 200
    (never a 4xx). Mirrors the ``/api/license/is-expiring-at`` posture."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expired-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_is_expired_at_invalid_signature(app):
    """File on disk but signature bogus -> is_expired_at false (we refuse
    to trust ``exp``), has_license True (there IS a file), valid False."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_expired_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape (snapshot fallback
    kicks in, requested_epoch is still echoed, is_expired_at is false)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expires_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_expired_at"] is False
    assert data["requested_epoch"] == epoch
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# -- cross-endpoint consistency ------------------------------------------------


def test_endpoint_agrees_with_is_expired_at_now(app):
    """When ``epoch`` equals "now", the perspective endpoint must agree
    with ``/api/license/is-expired`` at the boundary. Both derive from
    the same signed ``exp`` claim and use the same ``<=`` cutoff so a
    UI binding both cannot catch them disagreeing for the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/is-expired-at?epoch={now}").get_json()
        b = c.get("/api/license/is-expired").get_json()
    assert a["is_expired_at"] == b["expired"] == False  # noqa: E712


def test_endpoint_agrees_with_is_expired_at_now_on_lapsed(app):
    """Lapsed-key parity: the perspective endpoint at "now" and the base
    endpoint must both fire ``true`` on a signed-but-lapsed key."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/is-expired-at?epoch={now}").get_json()
        b = c.get("/api/license/is-expired").get_json()
    assert a["is_expired_at"] is True
    assert b["expired"] is True


def test_endpoint_shared_snapshot_matches_days_until_expiry_at(app):
    """All three perspective-epoch endpoints share
    :func:`_license_expires_snapshot` -- they must surface identical
    ``expires_at`` / ``has_license`` / ``valid`` for the same install
    regardless of the epoch queried. If this test fails on ``expires_at``
    or ``valid``, a UI binding two of the three could catch them
    disagreeing on a shared field."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(f"/api/license/is-expired-at?epoch={epoch}").get_json()
        b = c.get(f"/api/license/days-until-expiry-at?epoch={epoch}").get_json()
        d = c.get(f"/api/license/is-expiring-at?epoch={epoch}").get_json()
    for key in ("expires_at", "has_license", "valid"):
        assert a[key] == b[key] == d[key], (
            f"mismatch on {key}: is-expired-at={a[key]!r} "
            f"days-until-expiry-at={b[key]!r} is-expiring-at={d[key]!r}"
        )
    assert a["requested_epoch"] == b["requested_epoch"] == d["requested_epoch"] == epoch
