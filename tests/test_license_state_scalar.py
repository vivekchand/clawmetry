"""Tests for the ``license_state()`` / ``is_state()`` scalar helpers in
:mod:`clawmetry.license` plus their matching ``/api/license/state`` and
``/api/license/is-state`` HTTP endpoints.

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


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, iat_delta=-3600):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now + iat_delta,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }


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
    expired AFTER install."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


# ── LICENSE_STATES canonical set ─────────────────────────────────────────────


def test_license_states_is_frozenset(app):
    """The canonical set is a frozenset so callers can't accidentally
    mutate it (or accept a typo by adding to it)."""
    assert isinstance(app.lic.LICENSE_STATES, frozenset)


def test_license_states_exact_membership(app):
    """The four canonical states -- and nothing else -- so tests catch
    accidental drift if a fifth state gets added without ceremony."""
    assert app.lic.LICENSE_STATES == frozenset(
        {"active", "expired", "invalid", "no_license"}
    )


# ── clawmetry.license.license_state() ────────────────────────────────────────


def test_license_state_no_license_when_no_file(app):
    """No license file on disk -> ``"no_license"`` (never None -- "no
    license" is a real answer here, not a missing one)."""
    assert app.lic.license_state() == "no_license"


def test_license_state_active(app):
    """Signature-valid + not expired -> ``"active"``."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_state() == "active"


def test_license_state_expired(app):
    """Signature-valid but past its ``exp`` claim -> ``"expired"``.
    Must not collapse to ``"invalid"`` -- signature is still trusted."""
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    assert app.lic.license_state() == "expired"


def test_license_state_invalid_signature(app):
    """File exists but signature is bogus -> ``"invalid"``. The trust
    anchor rejected the payload; the state must reflect that."""
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_state() == "invalid"


def test_license_state_returns_str_never_none(app):
    """Contract: :func:`license_state` returns a string, never None --
    the whole point of the scalar is that a switch can bind on
    ``state`` without a None branch."""
    # Sweep every branch and confirm each returns a non-empty str.
    assert isinstance(app.lic.license_state(), str)  # no_license
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert isinstance(app.lic.license_state(), str)  # active
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    assert isinstance(app.lic.license_state(), str)  # expired


def test_license_state_returns_only_canonical_values(app):
    """Sweep every real branch; each must return a member of the
    canonical :data:`LICENSE_STATES` set."""
    assert app.lic.license_state() in app.lic.LICENSE_STATES  # no_license
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_state() in app.lic.LICENSE_STATES
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    assert app.lic.license_state() in app.lic.LICENSE_STATES
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.license_state() in app.lic.LICENSE_STATES


def test_license_state_never_raises(monkeypatch):
    """Any underlying failure -> ``"no_license"``. A blown
    :func:`current_license_info` must not propagate."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_state() == "no_license"


def test_license_state_unexpected_status_collapses_to_invalid(monkeypatch, app):
    """If a downstream refactor introduces an unrecognised ``status``
    string on :func:`current_license_info`, :func:`license_state`
    collapses to ``"invalid"`` rather than leaking the bogus value --
    the file exists but we can't classify it."""
    import clawmetry.license as _lic

    monkeypatch.setattr(
        _lic,
        "current_license_info",
        lambda: {"status": "gremlin", "valid": False},
    )
    assert _lic.license_state() == "invalid"


def test_license_state_non_dict_info_collapses_to_no_license(monkeypatch):
    """If :func:`current_license_info` returns a non-dict (broken
    downstream), degrade to ``"no_license"`` rather than crashing."""
    import clawmetry.license as _lic

    monkeypatch.setattr(_lic, "current_license_info", lambda: "not a dict")
    assert _lic.license_state() == "no_license"


# ── clawmetry.license.is_state() ─────────────────────────────────────────────


def test_is_state_matches_active(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_state("active") is True
    assert app.lic.is_state("expired") is False
    assert app.lic.is_state("invalid") is False
    assert app.lic.is_state("no_license") is False


def test_is_state_matches_expired(app):
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    assert app.lic.is_state("expired") is True
    assert app.lic.is_state("active") is False


def test_is_state_matches_invalid(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    assert app.lic.is_state("invalid") is True
    assert app.lic.is_state("active") is False


def test_is_state_matches_no_license(app):
    """No file on disk -> ``is_state("no_license") is True``. Callers
    that key their OSS-free tile off this gate get a positive answer
    rather than having to check ``license_state() == "no_license"``
    themselves."""
    assert app.lic.is_state("no_license") is True
    assert app.lic.is_state("active") is False


def test_is_state_case_insensitive(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_state("ACTIVE") is True
    assert app.lic.is_state("  active  ") is True
    assert app.lic.is_state("Active") is True


def test_is_state_typo_returns_false(app):
    """A typo like ``"actiev"`` must not accept ANY installed state --
    callers cannot silently mis-gate on a mis-spelled state name."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_state("actiev") is False
    assert app.lic.is_state("perpetual") is False  # a real word, not a state
    assert app.lic.is_state("") is False


def test_is_state_none_input_returns_false(app):
    """Callers pushing ``None`` (missing form field) get False, not a
    TypeError."""
    assert app.lic.is_state(None) is False  # type: ignore[arg-type]


def test_is_state_never_raises(monkeypatch):
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_state", _boom)
    assert _lic.is_state("active") is False


# ── GET /api/license/state ───────────────────────────────────────────────────


def test_endpoint_state_no_license(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"state": "no_license", "has_license": False, "valid": False}


def test_endpoint_state_active(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_state_expired(app):
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    with app.app.test_client() as c:
        resp = c.get("/api/license/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "expired"
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_state_invalid(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    with app.app.test_client() as c:
        resp = c.get("/api/license/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "invalid"
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_state_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_state_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"state": "no_license", "has_license": False, "valid": False}


# ── GET /api/license/is-state ────────────────────────────────────────────────


def test_endpoint_is_state_no_query(app):
    """Missing ``state`` param -> ``is_state=false`` (never 4xx)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is False
    assert data["requested_state"] == ""


def test_endpoint_is_state_matches_active(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=active")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is True
    assert data["state"] == "active"
    assert data["requested_state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_is_state_matches_no_license_branch(app):
    """``?state=no_license`` on an unlicensed install returns True --
    callers who bind an OSS-free tile to this gate get a positive answer."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=no_license")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is True
    assert data["state"] == "no_license"
    assert data["has_license"] is False


def test_endpoint_is_state_matches_expired(app):
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is True
    assert data["state"] == "expired"
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_state_case_insensitive(app):
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=ACTIVE")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is True
    assert data["requested_state"] == "active"


def test_endpoint_is_state_typo_returns_false(app):
    """``?state=actiev`` on an active install returns False -- must
    not silently accept a typo as a valid state."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=actiev")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is False
    assert data["state"] == "active"
    assert data["requested_state"] == "actiev"


def test_endpoint_is_state_mismatch_active_vs_expired(app):
    """Real state = active; ``?state=expired`` -> False. And the response
    still echoes the correct current state so a widget can render "you
    asked about expired; you're actually active" with one call."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=expired")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is False
    assert data["state"] == "active"


def test_endpoint_is_state_never_5xxs(app, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_state_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state?state=active")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_state"] is False
    assert data["state"] == "no_license"


# ── consistency: both endpoints see the same snapshot ────────────────────────


def test_both_endpoints_agree_on_snapshot(app):
    """Both endpoints share :func:`_license_state_snapshot` -- they must
    surface identical ``state`` / ``has_license`` / ``valid`` values for
    the same install."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        a = c.get("/api/license/state").get_json()
        b = c.get("/api/license/is-state?state=active").get_json()
    for key in ("state", "has_license", "valid"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"


# ── mirror parity with current_license_info().status ─────────────────────────


def test_state_mirrors_current_license_info_status_active(app):
    """For the three file-exists branches, :func:`license_state` mirrors
    the ``status`` field on :func:`current_license_info` exactly. Only
    the None-info branch gets the added ``"no_license"`` value."""
    tok = app.lic._encode_token(_payload(), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert app.lic.license_state() == info["status"] == "active"


def test_state_mirrors_current_license_info_status_expired(app):
    _write_key_direct(app, _payload(exp_delta=-5 * 86400))
    info = app.lic.current_license_info()
    assert app.lic.license_state() == info["status"] == "expired"


def test_state_mirrors_current_license_info_status_invalid(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")
    info = app.lic.current_license_info()
    assert app.lic.license_state() == info["status"] == "invalid"


def test_state_no_license_when_current_license_info_returns_none(app):
    """The None-info branch of :func:`current_license_info` becomes
    ``"no_license"`` -- the added state not carried by the envelope."""
    assert app.lic.current_license_info() is None
    assert app.lic.license_state() == "no_license"
