"""Tests for the two ``clawmetry.license`` scalar accessors
(:func:`license_tier`, :func:`license_expires_at`) and their paired
``/api/license/tier`` / ``/api/license/expires-at`` HTTP endpoints.

Thin scalar-accessor flavour of :func:`current_license_info` -- for a
status tile / fleet-node column that only needs the tier string or the
raw expiry epoch, so it doesn't have to unpack the full envelope OR
re-implement the "don't trust an unsigned body" rule client-side.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license.py`` so nothing depends on the real
production signing key or on real filesystem state. No network calls;
``CLAWMETRY_OFFLINE=1`` and the ``clawmetry activate`` phone-home is
opted out.

Note on ``/api/license/expires-at`` response shape: main's endpoint
returns ``{expires_at, days_until_expiry, has_license, valid}`` -- the
``days_until_expiry`` field is a convenience scalar computed by
:func:`clawmetry.license.days_until_expiry`. Tests for this endpoint
assert the fields that matter semantically rather than full-dict equality
so they remain correct if the response gains additional fields.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror tests/test_license.py) ---------------------------


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
def lic(monkeypatch, tmp_path):
    import clawmetry.license as _lic

    priv, pub_pem = _keypair()
    monkeypatch.setattr(_lic, "_PUBLIC_KEY_PEM", pub_pem)
    license_path = str(tmp_path / "license.key")
    monkeypatch.setattr(_lic, "LICENSE_PATH", license_path)
    monkeypatch.setattr(_lic, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    return SimpleNamespace(lic=_lic, priv=priv, license_path=license_path)


@pytest.fixture
def client(lic):
    """Flask test client with only ``bp_entitlement`` registered."""
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    app.config["TESTING"] = True
    return app.test_client()


def _write_key_direct(lic, exp_delta, tier="pro"):
    """Bypass ``activate()`` (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER it
    was installed."""
    import os

    tok = lic.lic._encode_token(_payload(tier=tier, exp_delta=exp_delta), lic.priv)
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_perpetual(lic, tier="enterprise"):
    import os

    tok = lic.lic._encode_token(_payload(tier=tier, drop_exp=True), lic.priv)
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(lic):
    import os

    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_tier() ----------------------------------------


def test_license_tier_no_file_returns_none(lic):
    """OSS-free install (no license file on disk) -> ``None``. Matches
    the never-mis-gate posture of the surrounding helpers -- a paid tier
    can never be silently claimed without a key."""
    assert lic.lic.license_tier() is None


def test_license_tier_active_key_returns_normalised_tier(lic):
    """A signature-valid, non-expired key surfaces its tier claim
    lower-cased and whitespace-stripped."""
    tok = lic.lic._encode_token(_payload(tier="pro"), lic.priv)
    lic.lic.activate(tok)
    assert lic.lic.license_tier() == "pro"


def test_license_tier_enterprise_key(lic):
    """Alternate paid tier -- confirm the accessor doesn't hard-code
    "pro"."""
    tok = lic.lic._encode_token(_payload(tier="enterprise"), lic.priv)
    lic.lic.activate(tok)
    assert lic.lic.license_tier() == "enterprise"


def test_license_tier_case_and_whitespace_normalised(lic):
    """Server-side typos in casing / whitespace on the ``tier`` claim
    normalise here, so gates comparing to lower-cased constants don't
    silently miss."""
    tok = lic.lic._encode_token(_payload(tier=" Pro "), lic.priv)
    lic.lic.activate(tok)
    assert lic.lic.license_tier() == "pro"


def test_license_tier_expired_key_returns_none(lic):
    """Signed-but-lapsed key -> ``None``. A gate binding this helper
    cannot silently keep rendering "Pro" on an expired key -- the copy
    that says "was Pro, expired" must go through ``current_license_info``
    which surfaces ``valid=false`` alongside the ``tier`` claim."""
    _write_key_direct(lic, exp_delta=-5 * 86400, tier="pro")
    assert lic.lic.license_tier() is None


def test_license_tier_invalid_signature_returns_none(lic):
    """Bogus-signature file -> ``None``. We never surface a tier claim
    from an unsigned body: an attacker who could edit the payload could
    otherwise claim any tier."""
    _write_bogus(lic)
    assert lic.lic.license_tier() is None


def test_license_tier_perpetual_key_returns_tier(lic):
    """Perpetual (no ``exp``) key -> the tier claim still surfaces (the
    key is signature-valid and never expires)."""
    _write_perpetual(lic, tier="enterprise")
    assert lic.lic.license_tier() == "enterprise"


def test_license_tier_never_raises_on_underlying_failure(monkeypatch):
    """Any per-row failure of :func:`current_license_info` -> ``None``.
    The helper never propagates -- matches the never-crash posture of
    the surrounding license helpers."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_tier() is None


# -- clawmetry.license.license_expires_at() ----------------------------------


def test_license_expires_at_no_file_returns_none(lic):
    """OSS-free install -> ``None``."""
    assert lic.lic.license_expires_at() is None


def test_license_expires_at_active_key_returns_exp(lic):
    """Signature-valid key -> the ``exp`` claim as an ``int`` (Unix
    epoch seconds)."""
    tok = lic.lic._encode_token(_payload(exp_delta=30 * 86400), lic.priv)
    lic.lic.activate(tok)
    exp = lic.lic.license_expires_at()
    assert isinstance(exp, int)
    now = int(time.time())
    # Bounded by the exp_delta above (30 days), so must be in the
    # (now, now + 31d] window -- doesn't rely on wall-clock stability.
    assert now < exp <= now + 31 * 86400


def test_license_expires_at_perpetual_key_returns_none(lic):
    """Perpetual (no ``exp``) key -> ``None``. There is no epoch to
    return -- a renewal banner binding this endpoint must render "never
    expires" copy instead."""
    _write_perpetual(lic)
    assert lic.lic.license_expires_at() is None


def test_license_expires_at_lapsed_key_still_returns_exp(lic):
    """Deliberately lenient on expiry (matches the ``current_license_info``
    posture): a signed-but-lapsed key still surfaces its ``exp`` so a
    support tile can render "expired on <date>" without a second call to
    :func:`current_license_info`. Callers wanting to hide the row must
    independently check :func:`license_tier` (which returns ``None`` on
    lapsed keys)."""
    _write_key_direct(lic, exp_delta=-5 * 86400)
    exp = lic.lic.license_expires_at()
    assert isinstance(exp, int)
    now = int(time.time())
    assert exp <= now  # already past


def test_license_expires_at_invalid_signature_returns_none(lic):
    """Bogus-signature file -> ``None``. We never trust an unsigned
    body's ``exp`` -- a forger who could edit the payload could claim
    a bogus expiry."""
    _write_bogus(lic)
    assert lic.lic.license_expires_at() is None


def test_license_expires_at_never_raises_on_underlying_failure(monkeypatch):
    """Any per-row failure of :func:`current_license_info` -> ``None``.
    Never propagates."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_expires_at() is None


# -- /api/license/tier -------------------------------------------------------


def test_api_license_tier_no_file(client, lic):
    """OSS-free install -> ``{"tier": null, "has_license": false, "valid":
    false}``. HTTP 200 -- the endpoint never 5xxs on a missing file."""
    resp = client.get("/api/license/tier")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"tier": None, "has_license": False, "valid": False}


def test_api_license_tier_active_key(client, lic):
    """Active key -> tier surfaces AND ``valid`` is ``True``."""
    tok = lic.lic._encode_token(_payload(tier="pro"), lic.priv)
    lic.lic.activate(tok)
    resp = client.get("/api/license/tier")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == "pro"
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_license_tier_expired_key(client, lic):
    """Signed-but-lapsed key -> ``tier`` is ``null`` (matches
    :func:`license_tier`) AND ``valid`` is ``False`` AND
    ``has_license`` is ``True`` -- the trio lets a UI render "was Pro,
    expired" copy without falling back to ``/api/license/status``."""
    _write_key_direct(lic, exp_delta=-5 * 86400, tier="pro")
    resp = client.get("/api/license/tier")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"tier": None, "has_license": True, "valid": False}


def test_api_license_tier_invalid_signature(client, lic):
    """Bogus-signature file -> ``tier=null``, ``valid=false``, but
    ``has_license=true`` -- the file exists, we just don't trust its
    payload."""
    _write_bogus(lic)
    resp = client.get("/api/license/tier")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"tier": None, "has_license": True, "valid": False}


def test_api_license_tier_agrees_with_helper(client, lic):
    """Per-response parity with :func:`license_tier` -- the HTTP shape
    layers ``has_license`` / ``valid`` on top of the scalar, but ``tier``
    itself must byte-equal the underlying helper."""
    tok = lic.lic._encode_token(_payload(tier="enterprise"), lic.priv)
    lic.lic.activate(tok)
    resp = client.get("/api/license/tier")
    assert resp.get_json()["tier"] == lic.lic.license_tier()


# -- /api/license/expires-at -------------------------------------------------
# The endpoint response shape includes ``days_until_expiry`` alongside
# ``expires_at`` / ``has_license`` / ``valid``.  Tests assert fields
# individually so they stay correct if the response gains additional scalars.


def test_api_license_expires_at_no_file(client, lic):
    """OSS-free install -> neutral envelope: no expiry data."""
    resp = client.get("/api/license/expires-at")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False
    assert body["days_until_expiry"] is None


def test_api_license_expires_at_active_key(client, lic):
    """Active key -> ``expires_at`` surfaces AND ``valid`` is ``True``."""
    tok = lic.lic._encode_token(_payload(exp_delta=60 * 86400), lic.priv)
    lic.lic.activate(tok)
    resp = client.get("/api/license/expires-at")
    assert resp.status_code == 200
    body = resp.get_json()
    now = int(time.time())
    assert isinstance(body["expires_at"], int)
    assert now < body["expires_at"] <= now + 61 * 86400
    assert body["has_license"] is True
    assert body["valid"] is True
    assert isinstance(body["days_until_expiry"], int)
    assert body["days_until_expiry"] > 0


def test_api_license_expires_at_perpetual(client, lic):
    """Perpetual key -> ``expires_at=null``, ``days_until_expiry=null``,
    ``valid=true``, ``has_license=true`` -- a renewal banner binding this
    endpoint should render "never expires" copy on this shape."""
    _write_perpetual(lic)
    resp = client.get("/api/license/expires-at")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["expires_at"] is None
    assert body["days_until_expiry"] is None
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_license_expires_at_lapsed_key(client, lic):
    """Signed-but-lapsed key -> ``expires_at`` still surfaces (matches
    :func:`license_expires_at`) AND ``valid`` is ``False`` -- a support
    tile can render "expired on <date>" off this one shape."""
    _write_key_direct(lic, exp_delta=-5 * 86400)
    resp = client.get("/api/license/expires-at")
    assert resp.status_code == 200
    body = resp.get_json()
    now = int(time.time())
    assert isinstance(body["expires_at"], int) and body["expires_at"] <= now
    assert body["has_license"] is True
    assert body["valid"] is False
    # days_until_expiry is negative for an expired key
    assert isinstance(body["days_until_expiry"], int)
    assert body["days_until_expiry"] < 0


def test_api_license_expires_at_invalid_signature(client, lic):
    """Bogus-signature file -> ``expires_at=null`` (we never trust an
    unsigned body's ``exp``)."""
    _write_bogus(lic)
    resp = client.get("/api/license/expires-at")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["expires_at"] is None
    assert body["has_license"] is True
    assert body["valid"] is False
    assert body["days_until_expiry"] is None


def test_api_license_expires_at_agrees_with_helper(client, lic):
    """Per-response parity with :func:`license_expires_at` -- the HTTP
    shape layers ``has_license`` / ``valid`` / ``days_until_expiry`` on
    top of the scalar, but ``expires_at`` itself must byte-equal the
    underlying helper."""
    tok = lic.lic._encode_token(_payload(exp_delta=90 * 86400), lic.priv)
    lic.lic.activate(tok)
    resp = client.get("/api/license/expires-at")
    assert resp.get_json()["expires_at"] == lic.lic.license_expires_at()
