"""Tests for :func:`clawmetry.license.license_features_at` and the
paired ``GET /api/license/features-at`` HTTP endpoint.

Perspective-epoch flavour of :func:`clawmetry.license.license_features`
/ ``/api/license/features``. Where the scalar answers "which paid
features does the KEY claim right now?", this pair answers "which paid
features would the KEY have claimed as of ``epoch``?" -- the same
retrospective / prospective question :func:`license_state_at` answers
for the license state. Both this pair and the scalar derive from the
same signed ``features`` / ``exp`` claim, refuse the invalid-signature
branch, and use the same ``exp <= cutoff`` boundary, so they cannot
disagree at the boundary when the perspective epoch equals "now".

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_state_at_scalar.py`` /
``tests/test_license_features_accessor.py`` so nothing depends on the
real production signing key or on real filesystem state. No network
calls; ``CLAWMETRY_OFFLINE=1`` opts out of the ``clawmetry activate``
phone-home.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers ---------------------------------------------------------


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
    features=("runtimes", "alerts", "fleet"),
    drop_exp=False,
    drop_features=False,
    features_value=None,
):
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": list(features),
    }
    if features_value is not None:
        p["features"] = features_value
    if drop_features:
        p.pop("features", None)
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
        client=flask_app.test_client(),
        lic=_lic,
        priv=priv,
        license_path=license_path,
    )


def _write_direct(app, payload):
    """Bypass :func:`activate` (which refuses expired tokens and phones
    home) and write a raw signed token to the license file. Lets a test
    build any payload shape -- expired, perpetual, features-list
    variants -- without round-tripping through the activation code
    path."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_features_at() --------------------------------


def test_features_at_no_license(app):
    """No license file -> ``None`` at every epoch. Mirrors
    :func:`license_features`'s no-license branch."""
    now = int(time.time())
    assert app.lic.license_features_at(now) is None
    assert app.lic.license_features_at(0) is None
    assert app.lic.license_features_at(2_000_000_000) is None


def test_features_at_now_matches_features_active(app):
    """When ``epoch`` equals "now", the perspective-epoch scalar must
    agree with :func:`license_features` for the same install -- pins the
    boundary the docstring guarantees."""
    _write_direct(app, _payload(features=("runtimes", "alerts", "fleet")))
    now = int(time.time())
    assert app.lic.license_features_at(now) == ["alerts", "fleet", "runtimes"]
    assert app.lic.license_features_at(now) == app.lic.license_features()


def test_features_at_now_matches_features_lapsed(app):
    """Lapsed-key parity: at "now", perspective scalar and base scalar
    both refuse the lapsed key and return ``None`` -- both use the
    ``exp <= cutoff`` boundary."""
    _write_direct(app, _payload(exp_delta=-5 * 86400))
    now = int(time.time())
    assert app.lic.license_features_at(now) is None
    assert app.lic.license_features() is None


def test_features_at_retrospective_lapsed_key_valid_then(app):
    """A key that has since lapsed WAS valid earlier -- pick an epoch
    before its ``exp`` and the retrospective scalar surfaces the
    features list. Answers the retrospective question
    :func:`license_features` cannot ("was this node entitled to alerts
    last quarter?")."""
    exp_delta = -5 * 86400  # expired 5 days ago
    _write_direct(app, _payload(exp_delta=exp_delta, features=("alerts",)))
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    # Ten days before the token was issued/expired: still valid then.
    long_ago = exp - 30 * 86400
    assert app.lic.license_features_at(long_ago) == ["alerts"]
    # But NOW (past exp) -> None (matches license_features).
    assert app.lic.license_features_at(int(time.time())) is None


def test_features_at_prospective_active_key_beyond_exp(app):
    """An active key with a finite ``exp`` -- pick an epoch beyond exp
    and the prospective scalar refuses ("will this node still have
    alerts at our next audit?"). Same ``exp <= cutoff`` boundary the
    scalar uses at "now"."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    assert app.lic.license_features_at(exp - 1) == ["alerts"]
    assert app.lic.license_features_at(exp) is None
    assert app.lic.license_features_at(exp + 1) is None


def test_features_at_perpetual_key_always_returns_list(app):
    """Perpetual (no ``exp``) key -> features list at every epoch.
    Matches :func:`license_state_at`'s perpetual branch which classifies
    as ``"active"`` regardless of epoch."""
    _write_direct(app, _payload(drop_exp=True, features=("alerts", "fleet")))
    for epoch in (0, int(time.time()), 2_000_000_000):
        assert app.lic.license_features_at(epoch) == ["alerts", "fleet"]


def test_features_at_invalid_signature_returns_none(app):
    """Bogus-signature file -> ``None`` at every epoch. An unsigned body
    is untrusted whatever the perspective (an attacker who could edit
    the payload could otherwise smuggle any features list into an
    unsigned body, for any perspective epoch)."""
    _write_bogus(app)
    for epoch in (0, int(time.time()), 2_000_000_000):
        assert app.lic.license_features_at(epoch) is None


def test_features_at_missing_epoch_returns_none(app):
    """Missing / non-numeric / bool epoch -> ``None`` (the perspective
    is unusable; conservative "no entitlement" fallback matching the
    never-mis-gate posture of the surrounding ``_at`` family)."""
    _write_direct(app, _payload(features=("alerts",)))
    assert app.lic.license_features_at(None) is None
    assert app.lic.license_features_at("garbage") is None
    assert app.lic.license_features_at("") is None
    assert app.lic.license_features_at(True) is None
    assert app.lic.license_features_at(False) is None


def test_features_at_int_parseable_string_epoch(app):
    """Int-parseable strings coerce cleanly (matches
    :func:`license_state_at`'s ``int()`` coercion)."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    assert app.lic.license_features_at(str(now)) == ["alerts"]


def test_features_at_signed_but_no_features_claim_returns_empty(app):
    """Signature-valid AS OF ``epoch`` but the payload carries no
    ``features`` claim -> ``[]``. Distinct from ``None`` (no valid
    license as of that time) -- callers rendering "features unlocked at
    <date>" must NOT collapse these two branches."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    assert app.lic.license_features_at(now) == []


def test_features_at_normalises_case_and_whitespace(app):
    """Case/whitespace normalisation is the same as
    :func:`license_features` so gates comparing to lower-cased constants
    don't silently miss."""
    _write_direct(
        app, _payload(features=(" Alerts ", "FLEET", "runtimes "))
    )
    now = int(time.time())
    assert app.lic.license_features_at(now) == ["alerts", "fleet", "runtimes"]


def test_features_at_ignores_non_string_entries(app):
    """Non-string entries in the ``features`` list (integer, bool, dict,
    None) are silently skipped rather than blowing up the tile -- matches
    the scalar's handling."""
    _write_direct(
        app,
        _payload(features_value=["alerts", 42, None, {"k": "v"}, "fleet"]),
    )
    now = int(time.time())
    assert app.lic.license_features_at(now) == ["alerts", "fleet"]


def test_features_at_never_raises(monkeypatch):
    """Any underlying failure of :func:`current_license_info` collapses
    the scalar to ``None`` -- never propagates."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_features_at(int(time.time())) is None


# -- GET /api/license/features-at -------------------------------------------


def test_endpoint_features_at_missing_epoch(app):
    """``?epoch=`` absent -> HTTP 200 with ``features_at=null`` +
    ``requested_epoch=null``. Never-4xx posture matching
    ``/api/license/state-at``."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/features-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features_at"] is None
    assert data["requested_epoch"] is None


def test_endpoint_features_at_non_integer_epoch(app):
    """Non-integer / bool epoch collapses to ``features_at=null`` +
    ``requested_epoch=null``. The "bad input" signal is
    ``requested_epoch=null``, not a 4xx."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/features-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features_at"] is None
    assert data["requested_epoch"] is None


def test_endpoint_features_at_no_license(app):
    """No license file -> ``features_at=null`` + OSS-free snapshot
    fields, HTTP 200."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features_at"] is None
    assert data["requested_epoch"] == now
    assert data["features"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_features_at_active_key_now_matches_features(app):
    """Active key at "now": ``features_at`` byte-equals ``features``.
    Pins the boundary the docstring guarantees."""
    _write_direct(app, _payload(features=("runtimes", "alerts", "fleet")))
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features_at"] == ["alerts", "fleet", "runtimes"]
    assert data["features"] == ["alerts", "fleet", "runtimes"]
    assert data["features_at"] == data["features"]
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_features_at_retrospective_lapsed_key(app):
    """A key that has since lapsed: retrospective at a pre-exp epoch
    still surfaces the features list; current-time ``features`` is
    ``null`` (lapsed now)."""
    _write_direct(
        app, _payload(exp_delta=-5 * 86400, features=("alerts",))
    )
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    long_ago = exp - 30 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={long_ago}")
    data = resp.get_json()
    assert data["features_at"] == ["alerts"]
    assert data["features"] is None  # lapsed now
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_features_at_prospective_beyond_exp(app):
    """Active key + prospective epoch past ``exp``: ``features_at=null``
    while ``features`` is still surfaced for the current time."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={exp + 1}")
    data = resp.get_json()
    assert data["features_at"] is None
    assert data["features"] == ["alerts"]
    assert data["valid"] is True


def test_endpoint_features_at_signed_but_no_features_claim(app):
    """Signed key with no ``features`` claim: ``features_at=[]`` (valid
    key at that time, zero features itemised) -- distinct from ``null``."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={now}")
    data = resp.get_json()
    assert data["features_at"] == []
    assert data["features"] == []


def test_endpoint_features_at_invalid_signature(app):
    """Bogus-signature file: ``features_at=null`` at every epoch; the
    envelope surfaces ``has_license=true`` (a file is on disk) but
    ``valid=false``."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={now}")
    data = resp.get_json()
    assert data["features_at"] is None
    assert data["features"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_features_at_parity_with_scalar(app):
    """Per-epoch parity: the endpoint's ``features_at`` value must match
    :func:`license_features_at` for the same epoch. Pins the endpoint
    against silent drift from the scalar."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        for epoch in (exp - 10 * 86400, exp - 1, exp, exp + 1):
            resp = c.get(f"/api/license/features-at?epoch={epoch}")
            data = resp.get_json()
            assert data["features_at"] == app.lic.license_features_at(epoch), epoch


def test_endpoint_features_at_shared_snapshot_agrees_with_features(app):
    """Shared current-time snapshot fields (``features`` / ``has_license``
    / ``valid``) must byte-equal ``/api/license/features`` for the same
    install so a UI binding both cannot catch them disagreeing on the
    current-time reference."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    with app.app.test_client() as c:
        f = c.get("/api/license/features").get_json()
        fa = c.get(f"/api/license/features-at?epoch={now}").get_json()
    assert fa["features"] == f["features"]
    assert fa["has_license"] == f["has_license"]
    assert fa["valid"] == f["valid"]


def test_endpoint_features_at_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the OSS-free snapshot fallback + honest
    per-request derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_features_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/features-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False
