"""Tests for the ``license_age_days_at(epoch)`` scalar helper on
``clawmetry.license`` and its paired ``/api/license/age-days-at`` HTTP
endpoint.

The perspective-epoch flavour of the ``license_age_days`` scalar. Both
derive from the same signed ``iat`` claim so they cannot disagree at the
day boundary when the perspective epoch equals "now"; on any other
epoch this helper answers "how old was the license as of ``epoch``?"
without the caller having to snapshot the license state at that time or
compute ``(epoch - iat) // 86400`` themselves.

Mirrors ``tests/test_license_days_until_expiry_at.py`` line-for-line
where the two scalars share posture (bool-refused, non-numeric coerced
to None, never-raises, lenient on lapsed keys), and diverges on the
one axis they must differ on: this scalar is intentionally NOT clamped
to ``max(0, ...)`` because a perspective epoch BEFORE ``iat`` is a real
signal the caller asked for (as opposed to clock skew, which is the
only way ``iat`` can be in the future when reading against
``time.time()`` from :func:`license_age_days`).

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


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, drop_iat=False):
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }
    if drop_iat:
        p.pop("iat", None)
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


# -- clawmetry.license.license_age_days_at() ----------------------------------


def test_license_age_days_at_no_license(app):
    """No license file on disk -> None (nothing to compute against)."""
    assert app.lic.license_age_days_at(int(time.time())) is None


def test_license_age_days_at_now_matches_license_age_days(app):
    """When ``epoch`` equals "now", the perspective-epoch scalar must
    agree with :func:`license_age_days` at the day boundary (+/- 1 for
    the fractional-second drift between the two calls: the base scalar
    reads ``time.time()`` with sub-second precision inside itself, while
    the caller here passes an ``int(time.time())`` that already
    truncated the fraction)."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    at_now = app.lic.license_age_days_at(now)
    scalar_now = app.lic.license_age_days()
    assert isinstance(at_now, int)
    assert isinstance(scalar_now, int)
    assert abs(at_now - scalar_now) <= 1


def test_license_age_days_at_future_epoch(app):
    """A perspective epoch 10 days from now against a just-issued key
    should render age ~10 days."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    days = app.lic.license_age_days_at(epoch)
    assert isinstance(days, int)
    # Floor-divided; allow +/- 1 for the day-boundary jitter that also
    # affects license_age_days itself.
    assert 9 <= days <= 10


def test_license_age_days_at_far_future_epoch(app):
    """Perspective epoch 100 days from now against a just-issued key
    should render age ~100 days -- unlike the "now" flavour, no cap on
    how old the caller may ask about."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 100 * 86400
    days = app.lic.license_age_days_at(epoch)
    assert isinstance(days, int)
    assert 99 <= days <= 100


def test_license_age_days_at_negative_when_epoch_before_iat(app):
    """An operator asking "how old was the key on <date>?" where
    <date> is BEFORE issuance -- perspective epoch BEFORE ``iat`` ->
    negative int, NOT None and NOT clamped to 0. Distinct from
    :func:`license_age_days`, which clamps because it can only reach
    the future-``iat`` branch via clock skew (nothing to hide here --
    the caller explicitly asked a pre-issuance question)."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 15 * 86400
    days = app.lic.license_age_days_at(epoch)
    assert isinstance(days, int)
    assert days < 0
    # epoch - iat = -15d.
    assert -16 <= days <= -14


def test_license_age_days_at_zero_on_day_of_issuance(app):
    """Perspective epoch on the day of issuance -> 0."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    iat = info["issued_at"]
    assert app.lic.license_age_days_at(iat) == 0
    # Sub-day AFTER iat still floor-divides to 0.
    assert app.lic.license_age_days_at(iat + 3600) == 0


def test_license_age_days_at_signed_but_lapsed_still_countable(app):
    """A lapsed-but-signed key must still surface a meaningful
    ``age_days`` at an arbitrary perspective epoch -- support scenario
    "how old was this lapsed key evaluated as of last Friday?".
    Mirrors :func:`license_age_days`'s lenient posture on expiry."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # expired 5 days ago
    # Perspective epoch 20 days AFTER the current time (still lapsed,
    # but iat was ~now, so age_days ~ +20).
    epoch = int(time.time()) + 20 * 86400
    days = app.lic.license_age_days_at(epoch)
    assert isinstance(days, int)
    assert 19 <= days <= 20


def test_license_age_days_at_no_iat_claim(app):
    """A signed payload with the ``iat`` claim stripped -> None
    regardless of perspective epoch. Nothing to reference."""
    tok = app.lic._encode_token(_payload(drop_iat=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    assert app.lic.license_age_days_at(int(time.time())) is None
    assert app.lic.license_age_days_at(0) is None
    assert app.lic.license_age_days_at(2_000_000_000) is None


def test_license_age_days_at_invalid_signature(app):
    """File on disk but signature bogus -> None. current_license_info()
    already collapses the payload on this branch; the scalar must
    reflect that."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_age_days_at(int(time.time())) is None


def test_license_age_days_at_non_numeric_epoch(app):
    """A caller passing a typo must get None, not a crash."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_age_days_at("garbage") is None  # type: ignore[arg-type]
    assert app.lic.license_age_days_at(None) is None  # type: ignore[arg-type]
    assert app.lic.license_age_days_at([1]) is None  # type: ignore[arg-type]


def test_license_age_days_at_bool_epoch_rejected(app):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently get "days from iat
    to epoch 1" back."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_age_days_at(True) is None  # type: ignore[arg-type]
    assert app.lic.license_age_days_at(False) is None  # type: ignore[arg-type]


def test_license_age_days_at_float_epoch_coerced(app):
    """Float epoch must coerce through ``int()`` rather than crash --
    same posture as :func:`days_until_expiry_at`."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    now_f = float(time.time())
    days = app.lic.license_age_days_at(now_f)
    assert isinstance(days, int)


def test_license_age_days_at_never_raises(monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    license_issued_at() must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_issued_at", _boom)
    assert _lic.license_age_days_at(int(time.time())) is None


# -- GET /api/license/age-days-at ---------------------------------------------


def test_endpoint_age_days_at_no_license(app):
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert isinstance(data["requested_epoch"], int)
    assert data["issued_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_age_days_at_active(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={now + 45 * 86400}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert 44 <= data["age_days"] <= 45
    assert data["requested_epoch"] == now + 45 * 86400
    assert isinstance(data["issued_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_age_days_at_negative_for_pre_issuance_epoch(app):
    """Perspective epoch BEFORE ``iat`` -> negative age_days, issued_at
    still populated so a support tile can render the pair without a
    second call."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 30 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert data["age_days"] < 0
    assert isinstance(data["issued_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_age_days_at_lapsed_key_still_surfaces_age(app):
    """A lapsed-but-signed key evaluated at a post-lapse perspective
    epoch -> positive age_days. ``valid`` is False (signature valid
    but past expiry now) so a caller that wants to hide the row on
    lapsed keys has the signal."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    epoch = int(time.time()) + 20 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert 19 <= data["age_days"] <= 20
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_age_days_at_no_iat_claim(app):
    """iat-less payload -> age_days null even for a valid epoch."""
    tok = app.lic._encode_token(_payload(drop_iat=True), app.priv)
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["issued_at"] is None
    assert data["has_license"] is True


def test_endpoint_age_days_at_missing_epoch_arg(app):
    """No ``epoch=`` -> age_days null, requested_epoch null, HTTP 200."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] is None
    # The snapshot still populates issued_at from the on-disk key.
    assert isinstance(data["issued_at"], int)
    assert data["has_license"] is True


def test_endpoint_age_days_at_non_integer_epoch(app):
    """Typo epoch -> age_days null, requested_epoch null, HTTP 200
    (never a 4xx). Mirrors the ``/api/license/days-until-expiry-at``
    posture."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_age_days_at_invalid_signature(app):
    """File on disk but signature bogus -> age_days null, has_license
    True (there IS a file), valid False."""
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_age_days_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape (snapshot fallback
    kicks in, requested_epoch is still echoed, age_days is null)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_issued_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] == epoch
    assert data["issued_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# -- cross-endpoint consistency -----------------------------------------------


def test_endpoint_agrees_with_age_days_at_now(app):
    """When ``epoch`` equals "now", the perspective endpoint must agree
    with ``/api/license/age-days`` at the day boundary (+/- 1 for the
    fractional-second drift between the two request handlers: the base
    endpoint reads ``time.time()`` with sub-second precision inside
    ``license_age_days`` at handle-time, while the perspective endpoint
    receives an ``int(time.time())`` from the caller that already
    truncated the fraction). Both derive from the same signed ``iat``
    claim, so a UI binding both cannot catch them disagreeing by more
    than a day for the same install."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        a = c.get(f"/api/license/age-days-at?epoch={now}").get_json()
        b = c.get("/api/license/age-days").get_json()
    assert isinstance(a["age_days"], int)
    assert isinstance(b["age_days"], int)
    assert abs(a["age_days"] - b["age_days"]) <= 1


def test_endpoint_agrees_with_issued_at_on_shared_snapshot(app):
    """Both endpoints share :func:`_license_issued_snapshot` -- they
    must surface identical ``issued_at`` / ``has_license`` / ``valid``
    for the same install regardless of the epoch queried."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 5 * 86400
    with app.app.test_client() as c:
        a = c.get(f"/api/license/age-days-at?epoch={epoch}").get_json()
        b = c.get("/api/license/issued-at").get_json()
    for key in ("issued_at", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
    assert a["requested_epoch"] == epoch
