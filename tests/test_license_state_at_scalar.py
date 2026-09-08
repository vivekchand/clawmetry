"""Tests for the ``license_state_at(epoch)`` / ``is_state_at(state, epoch)``
scalar helpers on ``clawmetry.license`` and their paired
``/api/license/state-at`` and ``/api/license/is-state-at`` HTTP endpoints.

The perspective-epoch flavour of the ``license_state`` / ``is_state`` pair.
Both derive from the same signed ``exp`` claim so they cannot disagree at
the boundary when the perspective epoch equals "now"; on any other epoch
these helpers answer "what state would the installed license have
reported evaluated as of ``epoch``?" without the caller having to
snapshot the license state at that time or compare ``exp`` to a caller-
supplied epoch themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_expired_at.py`` /
``tests/test_license_state_scalar.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_expired_at.py) --------------------


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


def _write_perpetual(app):
    import os

    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_state_at() -------------------------------------


def test_license_state_at_no_license(app):
    """No license file on disk -> ``"no_license"`` regardless of epoch."""
    assert app.lic.license_state_at(int(time.time())) == "no_license"
    assert app.lic.license_state_at(0) == "no_license"
    assert app.lic.license_state_at(2_000_000_000) == "no_license"


def test_license_state_at_now_matches_license_state_active(app):
    """When ``epoch`` equals "now", the perspective-epoch scalar must agree
    with :func:`license_state` on the same install. Both derive from the
    same signed ``exp`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary for an active key."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_state_at(now) == "active"
    assert app.lic.license_state() == "active"


def test_license_state_at_now_matches_license_state_lapsed(app):
    """Lapsed-key parity: at "now", perspective scalar and base scalar
    must agree on ``"expired"`` -- both use the ``exp <= cutoff`` boundary."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.license_state_at(now) == "expired"
    assert app.lic.license_state() == "expired"


def test_license_state_at_future_epoch_before_expiry(app):
    """Future perspective still before ``exp`` -> ``"active"`` (key would
    NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.license_state_at(epoch) == "active"


def test_license_state_at_future_epoch_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``"expired"``
    (the key WILL be expired at that perspective). This is the "will the
    key be expired at our next audit?" prospective scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.license_state_at(epoch) == "expired"


def test_license_state_at_past_epoch_still_active(app):
    """Perspective BEFORE now on an active key -> ``"active"`` (the key
    was not yet expired then, since ``exp`` is even further in the future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.license_state_at(epoch) == "active"


def test_license_state_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, the classification must flip to
    ``"expired"`` -- the ``<= epoch`` cutoff matches
    :func:`current_license_info`'s ``status`` derivation (which uses
    ``exp <= now``)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    exp = info["exp"]
    assert app.lic.license_state_at(exp) == "expired"
    assert app.lic.license_state_at(exp - 1) == "active"


def test_license_state_at_lapsed_key_pre_lapse_epoch(app):
    """Lapsed-but-signed key evaluated at a perspective epoch BEFORE its
    ``exp`` -> ``"active"``. Retrospective "was this active on <date>
    before it lapsed?" is answerable without special-casing the expired
    branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    epoch = int(time.time()) - 20 * 86400  # 15 days before exp
    assert app.lic.license_state_at(epoch) == "active"


def test_license_state_at_perpetual_license(app):
    """Perpetual (no ``exp``) license -> ``"active"`` regardless of
    perspective epoch. Nothing to compare against; matches
    :func:`license_state`'s ``"active"`` classification for perpetual
    keys."""
    _write_perpetual(app)
    assert app.lic.license_state_at(int(time.time())) == "active"
    assert app.lic.license_state_at(0) == "active"
    assert app.lic.license_state_at(2_000_000_000) == "active"


def test_license_state_at_invalid_signature_time_independent(app):
    """File on disk but signature bogus -> ``"invalid"`` regardless of
    epoch (an unsigned body is untrusted whatever the perspective)."""
    _write_bogus(app)
    assert app.lic.license_state_at(int(time.time())) == "invalid"
    assert app.lic.license_state_at(0) == "invalid"
    assert app.lic.license_state_at(2_000_000_000) == "invalid"


def test_license_state_at_non_numeric_epoch(app):
    """A caller passing a typo must get ``"no_license"`` (the conservative
    fallback), not a crash. Mirrors :func:`is_expired_at` / typo posture."""
    tok = app.lic._encode_token(_payload(exp_delta=-5 * 86400), app.priv)
    _write_key_direct(app, exp_delta=-5 * 86400)
    assert app.lic.license_state_at("garbage") == "no_license"  # type: ignore[arg-type]
    assert app.lic.license_state_at(None) == "no_license"  # type: ignore[arg-type]
    assert app.lic.license_state_at([1]) == "no_license"  # type: ignore[arg-type]
    assert app.lic.license_state_at({}) == "no_license"  # type: ignore[arg-type]


def test_license_state_at_bool_epoch_rejected(app):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently ask "state at epoch 1?"
    and get a spurious classification. Mirrors :func:`is_expired_at`."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    assert app.lic.license_state_at(True) == "no_license"  # type: ignore[arg-type]
    assert app.lic.license_state_at(False) == "no_license"  # type: ignore[arg-type]


def test_license_state_at_float_epoch_coerced(app):
    """Float epoch must coerce through ``int()`` rather than crash --
    matches :func:`is_expired_at` / :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_state_at(float(time.time())) == "active"


def test_license_state_at_never_raises(monkeypatch):
    """Any underlying failure -> ``"no_license"``. Even a fully-broken
    current_license_info() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_state_at(int(time.time())) == "no_license"


# -- clawmetry.license.is_state_at() ------------------------------------------


def test_is_state_at_no_license_matches_no_license(app):
    """No file -> is_state_at('no_license', epoch) is True; every other
    canonical state is False. Boundary case for the OSS-free branch."""
    epoch = int(time.time())
    assert app.lic.is_state_at("no_license", epoch) is True
    assert app.lic.is_state_at("active", epoch) is False
    assert app.lic.is_state_at("expired", epoch) is False
    assert app.lic.is_state_at("invalid", epoch) is False


def test_is_state_at_now_matches_is_state_active(app):
    """At "now", the perspective-epoch predicate must agree with
    :func:`is_state` for every canonical requested state -- both derive
    from the same signed ``exp`` claim."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for state in ("active", "expired", "invalid", "no_license"):
        assert app.lic.is_state_at(state, now) == app.lic.is_state(state), state


def test_is_state_at_now_matches_is_state_lapsed(app):
    """Lapsed-key parity at "now": perspective predicate and base
    predicate must both fire ``True`` on ``state="expired"``."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    for state in ("active", "expired", "invalid", "no_license"):
        assert app.lic.is_state_at(state, now) == app.lic.is_state(state), state


def test_is_state_at_future_epoch_flips_active_to_expired(app):
    """An active key at a perspective epoch beyond ``exp`` flips the
    ``"expired"`` predicate to True and the ``"active"`` predicate to
    False -- the prospective question :func:`is_state` cannot answer."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.is_state_at("expired", epoch) is True
    assert app.lic.is_state_at("active", epoch) is False


def test_is_state_at_case_insensitive(app):
    """Requested state is compared case-insensitively after strip --
    mirrors :func:`is_state`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for cased in ("ACTIVE", "Active", " active ", "aCtIvE"):
        assert app.lic.is_state_at(cased, now) is True


def test_is_state_at_typo_state_rejected(app):
    """A typo like 'actiev' collapses to False -- a caller cannot
    silently mis-gate on a mis-spelled state name."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for bad in ("actiev", "expiring", "grace", "invalidated", ""):
        assert app.lic.is_state_at(bad, now) is False, bad


def test_is_state_at_bad_state_input_rejected(app):
    """Non-string / None state -> False, never a crash."""
    now = int(time.time())
    assert app.lic.is_state_at(None, now) is False  # type: ignore[arg-type]
    assert app.lic.is_state_at(123, now) is False  # type: ignore[arg-type]
    assert app.lic.is_state_at([], now) is False  # type: ignore[arg-type]


def test_is_state_at_bad_epoch_falls_back_to_no_license(app):
    """A bad epoch collapses ``license_state_at`` to ``"no_license"``, so
    the predicate answers truthfully for that fallback: True only when
    the caller also asks ``state="no_license"``. Documents the
    conservative "no entitlement" contract."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_state_at("no_license", "garbage") is True  # type: ignore[arg-type]
    assert app.lic.is_state_at("active", "garbage") is False  # type: ignore[arg-type]
    assert app.lic.is_state_at("no_license", True) is True  # type: ignore[arg-type]
    assert app.lic.is_state_at("active", True) is False  # type: ignore[arg-type]


def test_is_state_at_never_raises(monkeypatch):
    """Any underlying failure of license_state_at -> False. Even a fully-
    broken helper must not propagate."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_state_at", _boom)
    assert _lic.is_state_at("active", int(time.time())) is False


# -- GET /api/license/state-at -------------------------------------------------


def test_endpoint_state_at_no_license(app):
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "no_license"
    assert data["requested_epoch"] == epoch
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_state_at_active_at_now(app):
    """Active key at "now" -> state_at "active", state "active", valid
    True, expires_at populated for the sibling perspective-epoch tiles."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "active"
    assert data["state"] == "active"
    assert data["requested_epoch"] == now
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_state_at_active_at_future_after_exp(app):
    """Active key evaluated at a perspective epoch AFTER ``exp`` ->
    state_at "expired" (prospective), state STILL "active" (the key is
    not expired NOW). This is the whole point of the perspective-epoch
    scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "expired"
    assert data["state"] == "active"
    assert data["valid"] is True
    assert data["has_license"] is True


def test_endpoint_state_at_lapsed_at_now(app):
    """Lapsed-but-signed key at "now" -> state_at "expired", state
    "expired", valid False. Retrospective banner can bind on state_at."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "expired"
    assert data["state"] == "expired"
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_state_at_lapsed_at_pre_lapse_epoch(app):
    """Lapsed-but-signed key at a perspective epoch BEFORE its ``exp`` ->
    state_at "active" (retrospective), state "expired" (the key is
    expired NOW). state_at flips independently of the current-state."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    epoch = int(time.time()) - 20 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "active"
    assert data["state"] == "expired"
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_state_at_perpetual_license(app):
    """Perpetual license -> state_at "active" at any epoch. expires_at
    null because no ``exp`` claim; has_license True."""
    _write_perpetual(app)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "active"
    assert data["state"] == "active"
    assert data["expires_at"] is None
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_state_at_invalid_signature_time_independent(app):
    """File on disk but signature bogus -> state_at "invalid" at any
    epoch (time-independent), state "invalid", has_license True, valid
    False."""
    _write_bogus(app)
    for epoch in (0, int(time.time()), 2_000_000_000):
        with app.app.test_client() as c:
            resp = c.get(f"/api/license/state-at?epoch={epoch}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["state_at"] == "invalid", epoch
        assert data["state"] == "invalid"
        assert data["has_license"] is True
        assert data["valid"] is False


def test_endpoint_state_at_missing_epoch(app):
    """No ``epoch=`` -> state_at "no_license" (fallback), requested_epoch
    null, HTTP 200. The snapshot still populates state/expires_at from
    the on-disk key."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/state-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "no_license"
    assert data["requested_epoch"] is None
    assert data["state"] == "active"
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_state_at_non_integer_epoch(app):
    """Typo epoch -> state_at "no_license", requested_epoch null, HTTP
    200 (never a 4xx). Mirrors ``/api/license/is-expired-at``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/state-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state_at"] == "no_license"
    assert data["requested_epoch"] is None
    assert data["state"] == "active"
    assert data["has_license"] is True


def test_endpoint_state_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape (snapshot fallback
    kicks in, requested_epoch is still echoed)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_state_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    # Snapshot fell back; the derive() step still ran fine, so state_at
    # is honestly derived from the underlying (no-file) install.
    assert data["state_at"] == "no_license"
    assert data["requested_epoch"] == epoch
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# -- GET /api/license/is-state-at ---------------------------------------------


def test_endpoint_is_state_at_no_license_matches_no_license(app):
    """No file -> is_state_at true for state=no_license, false for the
    other three canonical values."""
    epoch = int(time.time())
    with app.app.test_client() as c:
        yes = c.get(f"/api/license/is-state-at?state=no_license&epoch={epoch}").get_json()
        no = c.get(f"/api/license/is-state-at?state=active&epoch={epoch}").get_json()
    assert yes["is_state_at"] is True
    assert yes["state_at"] == "no_license"
    assert no["is_state_at"] is False
    assert no["state_at"] == "no_license"


def test_endpoint_is_state_at_active_at_now(app):
    """Active key at "now" -> is_state_at true for state=active."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-state-at?state=active&epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state_at"] is True
    assert data["state_at"] == "active"
    assert data["state"] == "active"
    assert data["requested_state"] == "active"
    assert data["requested_epoch"] == now
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_state_at_flips_active_to_expired_at_future(app):
    """Active key at future epoch beyond ``exp`` -> state_at "expired",
    state STILL "active" (key is not expired NOW). is_state_at true for
    state=expired, false for state=active."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        exp_data = c.get(f"/api/license/is-state-at?state=expired&epoch={epoch}").get_json()
        act_data = c.get(f"/api/license/is-state-at?state=active&epoch={epoch}").get_json()
    assert exp_data["is_state_at"] is True
    assert act_data["is_state_at"] is False
    assert exp_data["state_at"] == "expired"
    assert exp_data["state"] == "active"


def test_endpoint_is_state_at_case_insensitive(app):
    """Requested state compared case-insensitively (matches
    ``/api/license/is-state``)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        for cased in ("ACTIVE", "Active", " active "):
            data = c.get(
                f"/api/license/is-state-at?state={cased}&epoch={now}"
            ).get_json()
            assert data["is_state_at"] is True, cased
            assert data["requested_state"] == "active"


def test_endpoint_is_state_at_typo_state(app):
    """Typo state -> is_state_at false. The endpoint STILL echoes state_at
    honestly (perspective-epoch state) so a UI can render the actual state
    alongside the "your state=<typo> is not matched" copy."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        data = c.get(
            f"/api/license/is-state-at?state=actiev&epoch={now}"
        ).get_json()
    assert data["is_state_at"] is False
    assert data["state_at"] == "active"
    assert data["requested_state"] == "actiev"


def test_endpoint_is_state_at_missing_args(app):
    """No state, no epoch -> is_state_at false, state_at "no_license"
    (bad epoch), requested_epoch null, requested_state '', HTTP 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state_at"] is False
    assert data["state_at"] == "no_license"
    assert data["requested_epoch"] is None
    assert data["requested_state"] == ""
    assert data["state"] == "active"


def test_endpoint_is_state_at_bad_epoch(app):
    """Typo epoch -> state_at "no_license"; requesting state=no_license
    against a real install is thus truthfully true. Documents the
    conservative "no entitlement" fallback."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        good = c.get(
            "/api/license/is-state-at?state=no_license&epoch=garbage"
        ).get_json()
        bad = c.get(
            "/api/license/is-state-at?state=active&epoch=garbage"
        ).get_json()
    assert good["is_state_at"] is True
    assert good["state_at"] == "no_license"
    assert good["requested_epoch"] is None
    assert bad["is_state_at"] is False
    assert bad["state_at"] == "no_license"


def test_endpoint_is_state_at_never_5xxs(app, monkeypatch):
    """Snapshot blowup -> OSS-free shape, HTTP 200. Mirrors
    ``/api/license/is-expired-at`` never-5xx invariant."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_state_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-state-at?state=active&epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state_at"] is False
    assert data["state_at"] == "no_license"
    assert data["state"] == "no_license"
    assert data["requested_epoch"] == epoch
    assert data["requested_state"] == "active"
    assert data["has_license"] is False
    assert data["valid"] is False


# -- cross-endpoint consistency ------------------------------------------------


def test_endpoint_state_at_now_agrees_with_state(app):
    """At "now", ``/api/license/state-at`` must byte-equal
    ``/api/license/state`` for the same install. Both derive from the
    same signed ``exp`` claim so a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/state-at?epoch={now}").get_json()
        b = c.get("/api/license/state").get_json()
    assert a["state_at"] == a["state"] == b["state"] == "active"
    assert a["has_license"] == b["has_license"] is True
    assert a["valid"] == b["valid"] is True


def test_endpoint_state_at_now_agrees_with_state_lapsed(app):
    """Lapsed-key parity: perspective endpoint at "now" and base endpoint
    must both classify as ``"expired"``."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/state-at?epoch={now}").get_json()
        b = c.get("/api/license/state").get_json()
    assert a["state_at"] == a["state"] == b["state"] == "expired"


def test_endpoint_is_state_at_now_agrees_with_is_state(app):
    """At "now", is-state-at must byte-match is-state for every canonical
    requested state. Boundary check for the UI binding both."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        for state in ("active", "expired", "invalid", "no_license"):
            a = c.get(
                f"/api/license/is-state-at?state={state}&epoch={now}"
            ).get_json()
            b = c.get(f"/api/license/is-state?state={state}").get_json()
            assert a["is_state_at"] == b["is_state"], state


def test_endpoint_state_at_shares_expires_with_is_expired_at(app):
    """``/api/license/state-at`` and ``/api/license/is-expired-at`` both
    surface ``expires_at`` / ``has_license`` / ``valid`` from an on-disk
    read. A UI binding both for the same install must not catch them
    disagreeing on those shared fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(f"/api/license/state-at?epoch={epoch}").get_json()
        b = c.get(f"/api/license/is-expired-at?epoch={epoch}").get_json()
    for key in ("expires_at", "has_license", "valid"):
        assert a[key] == b[key], (
            f"mismatch on {key}: state-at={a[key]!r} "
            f"is-expired-at={b[key]!r}"
        )
    assert a["requested_epoch"] == b["requested_epoch"] == epoch


def test_endpoint_is_state_at_agrees_with_state_at(app):
    """``is-state-at`` must fire ``True`` on the canonical value that
    ``state-at`` returned, and only that value. Boundary check for the UI
    binding the pair."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400  # active-now, expired-at-perspective
    with app.app.test_client() as c:
        sa = c.get(f"/api/license/state-at?epoch={epoch}").get_json()
        for state in ("active", "expired", "invalid", "no_license"):
            data = c.get(
                f"/api/license/is-state-at?state={state}&epoch={epoch}"
            ).get_json()
            assert data["is_state_at"] is (state == sa["state_at"]), state
