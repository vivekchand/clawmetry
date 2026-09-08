"""Tests for the ``clawmetry.license.license_features`` scalar accessor
and its paired ``GET /api/license/features`` HTTP endpoint.

Thin scalar-accessor flavour of :func:`clawmetry.license.current_license_info`
for callers (an operator entitlement-diagnostic tile, a fleet-node column,
a "features unlocked by your key" chip row) that only need the ``features``
claim as a list of strings and don't want to unpack the full envelope OR
re-implement the "don't trust an unsigned body" rule client-side.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license.py`` so nothing depends on the real
production signing key or on real filesystem state. No network calls;
``CLAWMETRY_OFFLINE=1`` opts out of the ``clawmetry activate``
phone-home.
"""
from __future__ import annotations

import os
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


def _payload(
    tier="pro",
    nodes=3,
    exp_delta=365 * 86400,
    features=("runtimes", "alerts", "fleet"),
    drop_exp=False,
    drop_features=False,
    features_value=None,
):
    """Build a license payload with knobs for every branch under test.

    ``drop_features``   -> omit the ``features`` claim entirely (missing).
    ``features_value``  -> override the claim with an arbitrary value
                           (used to exercise non-list / non-string
                           branches). ``None`` = use ``features``.
    """
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
def lic(monkeypatch, tmp_path):
    """Ephemeral keypair + isolated ``LICENSE_PATH`` per test."""
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


def _write_direct(lic, payload):
    """Bypass :func:`activate` (which refuses expired tokens and phones home)
    and write a raw signed token to the license file. Lets a test build any
    payload shape -- expired, perpetual, features-list variants -- without
    round-tripping through the activation code path."""
    tok = lic.lic._encode_token(payload, lic.priv)
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(lic):
    """Write a syntactically-valid but signature-invalid token so the file
    exists on disk but ``verify_token`` refuses it."""
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_features() ------------------------------------


def test_license_features_no_file_returns_none(lic):
    """OSS-free install (no license file on disk) -> ``None``. Matches
    the never-mis-gate posture of the surrounding license helpers -- a
    paid feature can never be silently claimed without a key."""
    assert lic.lic.license_features() is None


def test_license_features_active_key_returns_sorted_list(lic):
    """A signature-valid, non-expired key surfaces its ``features``
    claim as a sorted, deduplicated, normalised list of strings."""
    _write_direct(lic, _payload(features=("runtimes", "alerts", "fleet")))
    assert lic.lic.license_features() == ["alerts", "fleet", "runtimes"]


def test_license_features_normalises_case_and_whitespace(lic):
    """Server-side typos in casing / whitespace on the feature ids
    normalise here, so gates comparing to lower-cased constants don't
    silently miss (``Alerts`` and `` alerts `` and ``ALERTS`` all
    collapse to the same id)."""
    _write_direct(
        lic, _payload(features=(" Alerts ", "FLEET", "runtimes "))
    )
    assert lic.lic.license_features() == ["alerts", "fleet", "runtimes"]


def test_license_features_dedupes_after_normalisation(lic):
    """After case/whitespace normalisation, duplicate ids collapse. A
    payload of ``["Alerts", "alerts", "ALERTS"]`` surfaces once."""
    _write_direct(
        lic, _payload(features=("Alerts", "alerts", "ALERTS", "fleet"))
    )
    assert lic.lic.license_features() == ["alerts", "fleet"]


def test_license_features_missing_claim_returns_empty_list(lic):
    """A signature-valid license with NO ``features`` claim surfaces
    ``[]`` (valid key, zero features itemised) -- distinct from ``None``
    (no valid license at all). Callers rendering "features unlocked"
    must NOT collapse these two branches."""
    _write_direct(lic, _payload(drop_features=True))
    assert lic.lic.license_features() == []


def test_license_features_non_list_claim_returns_empty_list(lic):
    """Malformed ``features`` claim (non-list) -> ``[]``. Never crash on
    bad server-side data: an operator diagnostic tile is more useful
    surfacing "valid key, features list malformed" than 500-ing."""
    _write_direct(lic, _payload(features_value="alerts,fleet"))
    assert lic.lic.license_features() == []


def test_license_features_empty_list_claim_returns_empty_list(lic):
    """An explicit empty list on the token surfaces as ``[]``. This is
    the same shape as a missing claim (both -> ``[]``) since a caller
    can't act differently on the two branches anyway."""
    _write_direct(lic, _payload(features=()))
    assert lic.lic.license_features() == []


def test_license_features_ignores_non_string_entries(lic):
    """Non-string entries in the ``features`` list (integer, bool, dict,
    None) are silently skipped rather than blowing up the tile.
    Legit string entries alongside still surface."""
    _write_direct(
        lic,
        _payload(features_value=["alerts", 42, None, {"k": "v"}, "fleet"]),
    )
    assert lic.lic.license_features() == ["alerts", "fleet"]


def test_license_features_all_non_string_returns_empty_list(lic):
    """A ``features`` list that holds only non-string entries collapses
    to ``[]`` (nothing usable) -- NOT ``None`` (the license is still
    signature-valid, we just can't surface any ids)."""
    _write_direct(lic, _payload(features_value=[1, 2, 3, None, True]))
    assert lic.lic.license_features() == []


def test_license_features_ignores_blank_strings(lic):
    """Blank / whitespace-only feature ids are dropped -- the sort
    order doesn't get polluted with empty leading rows."""
    _write_direct(lic, _payload(features=("", "   ", "alerts", "fleet")))
    assert lic.lic.license_features() == ["alerts", "fleet"]


def test_license_features_expired_key_returns_none(lic):
    """Signed-but-lapsed key -> ``None``. A gate binding this helper
    cannot silently keep granting features on an expired key. The copy
    that says "was Pro, features expired" must go through
    :func:`current_license_info` which surfaces ``valid=false`` alongside
    the ``tier`` claim."""
    _write_direct(lic, _payload(exp_delta=-5 * 86400))
    assert lic.lic.license_features() is None


def test_license_features_invalid_signature_returns_none(lic):
    """Bogus-signature file -> ``None``. We never surface a features
    list from an unsigned body: an attacker who could edit the payload
    could otherwise smuggle any features into the list."""
    _write_bogus(lic)
    assert lic.lic.license_features() is None


def test_license_features_perpetual_key_returns_list(lic):
    """Perpetual (no ``exp``) key -> the ``features`` claim still
    surfaces (the key is signature-valid and never expires)."""
    _write_direct(
        lic, _payload(drop_exp=True, features=("alerts", "runtimes"))
    )
    assert lic.lic.license_features() == ["alerts", "runtimes"]


def test_license_features_never_raises_on_underlying_failure(monkeypatch):
    """Any per-row failure of :func:`current_license_info` -> ``None``.
    The helper never propagates -- matches the never-crash posture of
    the surrounding license helpers."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "current_license_info", _boom)
    assert _lic.license_features() is None


def test_license_features_never_raises_on_token_reread_failure(lic, monkeypatch):
    """A failure on the second read (``verify_token`` re-open after the
    ``valid`` gate passes) still degrades to ``None`` rather than
    propagating. Simulates a race where the file is deleted between the
    two reads."""
    _write_direct(lic, _payload())

    # Force ``verify_token`` to blow up on the second read only. The
    # first read (inside ``current_license_info``) uses ``verify_token``
    # via the module import; we shadow it AFTER the ``valid`` gate has
    # already been resolved on the fresh info dict.
    real_info = lic.lic.current_license_info

    def _stubbed_info():
        info = real_info()
        return info

    monkeypatch.setattr(lic.lic, "current_license_info", _stubbed_info)

    def _boom(_):
        raise RuntimeError("simulated re-read race")

    monkeypatch.setattr(lic.lic, "verify_token", _boom)
    # The second read raises -> the helper returns None, doesn't
    # propagate. A UI tile bound to this scalar keeps rendering.
    assert lic.lic.license_features() is None


# -- /api/license/features endpoint parity ----------------------------------


def test_endpoint_no_license_returns_null_features_shape(lic, client):
    """OSS-free install (no license) -> ``{features: null, has_license:
    false, valid: false}``. Never 5xxs; the endpoint must always answer
    with the standard three-field envelope so a UI binding can render
    without special-casing HTTP status codes."""
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"features": None, "has_license": False, "valid": False}


def test_endpoint_active_key_returns_features_and_valid_true(lic, client):
    """A signature-valid key -> ``features`` populated, ``has_license``
    and ``valid`` both ``true``. Per-response parity with
    :func:`clawmetry.license.license_features` is pinned so the HTTP
    shape cannot silently drift from the Python helper."""
    _write_direct(lic, _payload(features=("alerts", "fleet", "runtimes")))
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == ["alerts", "fleet", "runtimes"]
    assert body["has_license"] is True
    assert body["valid"] is True
    # Endpoint MUST equal the underlying Python helper for the features
    # slot -- this is the drift guard.
    assert body["features"] == lic.lic.license_features()


def test_endpoint_expired_key_features_null_valid_false(lic, client):
    """Signed-but-lapsed key -> ``features=null`` (matching
    :func:`license_features` refusing to surface features on lapsed
    keys), but ``has_license=true`` and ``valid=false`` so a UI can
    render "was Pro, expired" copy without a second call to
    ``/api/license/status``."""
    _write_direct(lic, _payload(exp_delta=-5 * 86400))
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_invalid_signature_features_null(lic, client):
    """Bogus-signature file -> ``features=null``, ``has_license=true``
    (the file IS on disk), ``valid=false`` (signature failed). Matches
    the never-trust-an-unsigned-body posture of the underlying helper."""
    _write_bogus(lic)
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_missing_features_claim_returns_empty_list(lic, client):
    """A signature-valid license without a ``features`` claim ->
    ``features=[]`` (distinct from ``null``), ``has_license=true``,
    ``valid=true``. A UI binding must NOT collapse ``[]`` and ``null``:
    the former is "no features itemised on a valid key", the latter is
    "no valid key at all"."""
    _write_direct(lic, _payload(drop_features=True))
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_perpetual_key_returns_features(lic, client):
    """Perpetual (no ``exp``) key -> ``features`` populated,
    ``valid=true``. The token never expires so the endpoint surfaces
    its claim indefinitely."""
    _write_direct(
        lic, _payload(drop_exp=True, features=("alerts", "runtimes"))
    )
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == ["alerts", "runtimes"]
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_never_5xxs_on_underlying_failure(lic, client, monkeypatch):
    """Any exception under the hood -> HTTP 200 with the OSS-free
    branch shape (``features=null``, ``has_license=false``,
    ``valid=false``). The endpoint must never propagate a 500 -- a
    diagnostic tile bound to it stays rendered even on a partially-
    broken install."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_features", _boom)
    monkeypatch.setattr(_lic, "current_license_info", _boom)
    resp = client.get("/api/license/features")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"features": None, "has_license": False, "valid": False}
