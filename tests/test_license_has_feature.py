"""Tests for the ``clawmetry.license.has_feature`` predicate and its
paired ``GET /api/license/has-feature`` HTTP endpoint.

Predicate flavour of :func:`clawmetry.license.license_features` for
callers (a paywall banner, a fleet-node column, an operator
entitlement-diagnostic tile) that want a single-bit answer rather than
the full list. Fills the ``license_features -> has_feature`` seat that
the sibling ``license_tier -> is_tier`` / ``license_subject ->
is_subject`` / ``license_state -> is_state`` pairs already occupy on
the license axis.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_features_accessor.py`` so nothing depends
on the real production signing key or on real filesystem state. No
network calls; ``CLAWMETRY_OFFLINE=1`` opts out of the ``clawmetry
activate`` phone-home.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror tests/test_license_features_accessor.py) --------


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
    """Bypass :func:`activate` (which refuses expired tokens and phones
    home) and write a raw signed token to the license file. Lets a test
    build any payload shape -- expired, perpetual, features-list
    variants -- without round-tripping through the activation code
    path."""
    tok = lic.lic._encode_token(payload, lic.priv)
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(lic):
    """Write a syntactically-valid but signature-invalid token so the
    file exists on disk but ``verify_token`` refuses it."""
    os.makedirs(os.path.dirname(lic.license_path), exist_ok=True)
    with open(lic.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.has_feature() ----------------------------------------


def test_has_feature_no_file_returns_false(lic):
    """OSS-free install (no license file on disk) -> ``False`` for any
    query, matching the never-mis-gate posture of the surrounding
    license predicates."""
    assert lic.lic.has_feature("alerts") is False


def test_has_feature_active_key_claimed_returns_true(lic):
    """A signature-valid, non-expired key whose ``features`` claim
    contains the queried id -> ``True``."""
    _write_direct(lic, _payload(features=("runtimes", "alerts", "fleet")))
    assert lic.lic.has_feature("alerts") is True


def test_has_feature_active_key_unclaimed_returns_false(lic):
    """A signature-valid, non-expired key whose ``features`` claim does
    NOT contain the queried id -> ``False``. The predicate never mis-
    grants a feature the token omits."""
    _write_direct(lic, _payload(features=("runtimes", "alerts", "fleet")))
    assert lic.lic.has_feature("selfevolve") is False


def test_has_feature_case_insensitive_query(lic):
    """Query normalisation matches :func:`is_tier` / :func:`is_subject`
    -- ``"Alerts"`` / ``"alerts"`` / ``"  ALERTS "`` all resolve against
    the same normalised set on the token."""
    _write_direct(lic, _payload(features=("alerts", "fleet")))
    assert lic.lic.has_feature("Alerts") is True
    assert lic.lic.has_feature("ALERTS") is True
    assert lic.lic.has_feature("  Alerts  ") is True


def test_has_feature_case_insensitive_on_token_side(lic):
    """A server-side typo in casing on the ``features`` claim
    normalises before the membership check, so ``"Alerts"`` on the
    token and ``"alerts"`` in the query still match. This is the same
    normalisation :func:`license_features` runs on the token side."""
    _write_direct(lic, _payload(features=(" Alerts ", "FLEET")))
    assert lic.lic.has_feature("alerts") is True
    assert lic.lic.has_feature("fleet") is True


def test_has_feature_empty_query_returns_false(lic):
    """Missing / empty / whitespace-only query -> ``False`` (nothing
    "has feature empty-string"). Matches :func:`is_tier`'s posture on
    empty input."""
    _write_direct(lic, _payload(features=("alerts",)))
    assert lic.lic.has_feature("") is False
    assert lic.lic.has_feature("   ") is False


def test_has_feature_non_string_query_returns_false(lic):
    """Non-string query (int, list, None) coerces through ``str()``
    and normalises. Values that stringify to something the token
    doesn't claim -> ``False``; values that raise on ``str()`` also
    degrade to ``False`` rather than propagating."""
    _write_direct(lic, _payload(features=("alerts",)))
    assert lic.lic.has_feature(42) is False
    assert lic.lic.has_feature(None) is False


def test_has_feature_missing_claim_returns_false(lic):
    """A signature-valid key with NO ``features`` claim -> ``False``
    for every query (nothing itemised means nothing matches). Distinct
    from ``license_features`` which surfaces ``[]`` on this branch --
    a predicate can't render "no key" vs "key with no features"
    differently, so both collapse to the ``False`` bit here."""
    _write_direct(lic, _payload(drop_features=True))
    assert lic.lic.has_feature("alerts") is False


def test_has_feature_non_list_claim_returns_false(lic):
    """Malformed ``features`` claim (non-list) -> ``False`` for every
    query. The accessor normalises this branch to ``[]``, and an empty
    list can't contain anything."""
    _write_direct(lic, _payload(features_value="alerts,fleet"))
    assert lic.lic.has_feature("alerts") is False


def test_has_feature_expired_key_returns_false(lic):
    """Signed-but-lapsed key -> ``False`` even for a feature the token
    itemises. A gate binding this predicate cannot silently keep
    granting features on an expired key -- matches :func:`is_tier`'s
    "not entitled RIGHT NOW" posture. A caller wanting to distinguish
    "was ever" from "is now" should read
    :func:`current_license_info` directly."""
    _write_direct(lic, _payload(exp_delta=-5 * 86400, features=("alerts",)))
    assert lic.lic.has_feature("alerts") is False


def test_has_feature_invalid_signature_returns_false(lic):
    """Bogus-signature file -> ``False``. We never grant a feature
    from an unsigned body: an attacker who could edit the payload
    could otherwise smuggle any id into the ``features`` list."""
    _write_bogus(lic)
    assert lic.lic.has_feature("alerts") is False


def test_has_feature_perpetual_key_returns_true(lic):
    """Perpetual (no ``exp``) key -> the ``features`` claim still
    resolves (the key is signature-valid and never expires)."""
    _write_direct(
        lic, _payload(drop_exp=True, features=("alerts", "runtimes"))
    )
    assert lic.lic.has_feature("alerts") is True
    assert lic.lic.has_feature("runtimes") is True
    assert lic.lic.has_feature("fleet") is False


def test_has_feature_ignores_non_string_token_entries(lic):
    """Non-string entries in the token's ``features`` list are skipped
    by the underlying accessor, so a query against a string neighbour
    still matches even when the surrounding entries are junk."""
    _write_direct(
        lic,
        _payload(features_value=["alerts", 42, None, {"k": "v"}, "fleet"]),
    )
    assert lic.lic.has_feature("alerts") is True
    assert lic.lic.has_feature("fleet") is True


def test_has_feature_ignores_blank_token_entries(lic):
    """Blank / whitespace-only token entries are dropped by the
    accessor, and a query for the empty string is refused up-front, so
    a payload full of blanks never mis-grants."""
    _write_direct(lic, _payload(features=("", "   ", "alerts")))
    assert lic.lic.has_feature("alerts") is True
    assert lic.lic.has_feature("") is False


def test_has_feature_never_raises_on_underlying_failure(monkeypatch):
    """Any per-row failure of :func:`license_features` -> ``False``.
    The predicate never propagates -- matches the never-crash posture
    of the surrounding license helpers."""
    import clawmetry.license as _lic

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_features", _boom)
    assert _lic.has_feature("alerts") is False


def test_has_feature_parity_with_accessor(lic):
    """Per-id parity with :func:`license_features`: for every id in the
    normalised list, ``has_feature`` returns ``True``; for a novel id,
    ``False``. Pins the "predicate is exactly membership-in-accessor"
    contract so a future refactor of either side can't drift."""
    _write_direct(
        lic, _payload(features=("Alerts", "FLEET", "runtimes "))
    )
    feats = lic.lic.license_features()
    assert feats == ["alerts", "fleet", "runtimes"]
    for f in feats:
        assert lic.lic.has_feature(f) is True
    assert lic.lic.has_feature("selfevolve") is False


# -- /api/license/has-feature endpoint parity -------------------------------


def test_endpoint_no_license_returns_false_shape(lic, client):
    """OSS-free install (no license) -> ``has_feature=false``,
    ``features=null``, ``has_license=false``, ``valid=false``. Never
    5xxs; the endpoint must always answer with the standard envelope
    so a UI binding can render without special-casing HTTP status
    codes."""
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["feature"] == "alerts"
    assert body["requested_feature"] == "alerts"
    assert body["features"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_endpoint_active_key_claimed_returns_true_shape(lic, client):
    """A signature-valid key whose ``features`` claim contains the
    queried id -> ``has_feature=true``, ``features`` populated,
    ``has_license``/``valid`` both ``true``. Per-response parity with
    :func:`clawmetry.license.has_feature` is pinned so the HTTP shape
    cannot silently drift from the Python helper."""
    _write_direct(lic, _payload(features=("alerts", "fleet", "runtimes")))
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is True
    assert body["feature"] == "alerts"
    assert body["requested_feature"] == "alerts"
    assert body["features"] == ["alerts", "fleet", "runtimes"]
    assert body["has_license"] is True
    assert body["valid"] is True
    # Endpoint MUST equal the underlying Python helper for the bool
    # slot -- this is the drift guard.
    assert body["has_feature"] == lic.lic.has_feature("alerts")


def test_endpoint_active_key_unclaimed_returns_false_shape(lic, client):
    """A signature-valid key whose ``features`` claim does NOT contain
    the queried id -> ``has_feature=false`` but ``features`` still
    populated, ``valid=true``. A UI can render "you're on Pro, but
    this feature isn't on your key" copy off ONE call."""
    _write_direct(lic, _payload(features=("alerts", "fleet")))
    resp = client.get("/api/license/has-feature?feature=selfevolve")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["feature"] == "selfevolve"
    assert body["features"] == ["alerts", "fleet"]
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_case_insensitive_query(lic, client):
    """The endpoint normalises the query the same way the predicate
    does (lower / strip), so ``?feature=Alerts`` and ``?feature=%20alerts%20``
    both resolve against the same normalised set. The echoed ``feature``
    field carries the normalised form so a caller can pin the shape."""
    _write_direct(lic, _payload(features=("alerts",)))
    for q in ("Alerts", "ALERTS", "%20alerts%20"):
        resp = client.get(f"/api/license/has-feature?feature={q}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["has_feature"] is True
        assert body["feature"] == "alerts"


def test_endpoint_missing_query_returns_false_shape(lic, client):
    """Missing ``feature`` param -> ``has_feature=false`` with an
    empty echo, HTTP 200. Never 4xxs (matches the surrounding
    endpoints' never-4xx posture)."""
    _write_direct(lic, _payload(features=("alerts",)))
    resp = client.get("/api/license/has-feature")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["feature"] == ""
    assert body["requested_feature"] == ""
    # A valid key is still installed, so the surrounding fields must
    # still surface truthfully -- the missing query doesn't erase
    # them.
    assert body["features"] == ["alerts"]
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_empty_query_returns_false_shape(lic, client):
    """Empty / whitespace-only ``feature`` param -> ``has_feature=false``
    for the same reason as the underlying predicate (nothing "has
    feature empty-string")."""
    _write_direct(lic, _payload(features=("alerts",)))
    resp = client.get("/api/license/has-feature?feature=%20%20")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["feature"] == ""


def test_endpoint_expired_key_returns_false_valid_false(lic, client):
    """Signed-but-lapsed key -> ``has_feature=false`` even for a
    feature the token itemises, but ``has_license=true`` and
    ``valid=false`` so a UI can render "was Pro, expired" copy without
    a second call to ``/api/license/status``. ``features`` is
    ``null`` because the underlying accessor refuses to surface a
    features list on lapsed keys."""
    _write_direct(lic, _payload(exp_delta=-5 * 86400, features=("alerts",)))
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_invalid_signature_returns_false(lic, client):
    """Bogus-signature file -> ``has_feature=false``, ``features=null``,
    ``has_license=true`` (the file IS on disk), ``valid=false``.
    Matches the never-trust-an-unsigned-body posture of the
    underlying predicate."""
    _write_bogus(lic)
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_perpetual_key_returns_true(lic, client):
    """Perpetual (no ``exp``) key -> ``has_feature`` resolves against
    the token's ``features`` list indefinitely."""
    _write_direct(
        lic, _payload(drop_exp=True, features=("alerts", "runtimes"))
    )
    resp = client.get("/api/license/has-feature?feature=runtimes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is True
    assert body["features"] == ["alerts", "runtimes"]
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_missing_features_claim_returns_false(lic, client):
    """A signature-valid license without a ``features`` claim ->
    ``has_feature=false`` for every query, ``features=[]``,
    ``valid=true``. A UI can distinguish "valid key with nothing
    itemised" (``features=[]``) from "no key" (``features=null``)
    without a second call."""
    _write_direct(lic, _payload(drop_features=True))
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["features"] == []
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_agrees_with_features_endpoint(lic, client):
    """Per-id agreement with ``/api/license/features``: for every id
    the list endpoint surfaces, the predicate endpoint must return
    ``True``; for a novel id, ``False``. Pins the "predicate is
    exactly membership-in-list" contract at the HTTP layer so a future
    refactor of either endpoint can't drift."""
    _write_direct(
        lic, _payload(features=("alerts", "fleet", "runtimes"))
    )
    list_body = client.get("/api/license/features").get_json()
    for f in list_body["features"]:
        body = client.get(f"/api/license/has-feature?feature={f}").get_json()
        assert body["has_feature"] is True, f"expected has_feature=true for {f!r}"
        assert body["features"] == list_body["features"]
    body = client.get("/api/license/has-feature?feature=selfevolve").get_json()
    assert body["has_feature"] is False


def test_endpoint_never_5xxs_on_underlying_failure(lic, client, monkeypatch):
    """Any exception under the hood -> HTTP 200 with the OSS-free
    branch shape (``has_feature=false``, ``features=null``,
    ``has_license=false``, ``valid=false``). The endpoint must never
    propagate a 500 -- a diagnostic tile bound to it stays rendered
    even on a partially-broken install."""
    import clawmetry.license as _lic

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_features", _boom)
    monkeypatch.setattr(_lic, "current_license_info", _boom)
    resp = client.get("/api/license/has-feature?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature"] is False
    assert body["features"] is None
    assert body["has_license"] is False
    assert body["valid"] is False
    # The echo fields still carry the normalised query even on the
    # error branch, so a caller can distinguish "no license, but the
    # server saw my query" from "no license, and the server dropped
    # my query" (which would indicate a routing / proxy bug).
    assert body["feature"] == "alerts"
    assert body["requested_feature"] == "alerts"
