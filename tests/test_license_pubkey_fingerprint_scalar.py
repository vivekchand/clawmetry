"""Tests for the ``is_pubkey_fingerprint(fp)`` predicate in
:mod:`clawmetry.license` plus its matching
``/api/license/pubkey-fingerprint`` and
``/api/license/is-pubkey-fingerprint`` HTTP endpoints.

``pubkey_fingerprint()`` itself already exists (returns the SHA-256 of
the embedded Ed25519 verification key), and ``/api/license/pubkey``
returns the full envelope (algorithm, format, PEM body, fingerprint).
This module pins the contract for the newly-added scalar endpoint that
surfaces JUST the fingerprint plus the matching boolean predicate a
supply-chain / trust-anchor audit widget needs -- mirroring the
``license_subject`` / ``is_subject`` and ``license_tier`` / ``is_tier``
scalar-plus-predicate pattern.

Hermetic: ephemeral Ed25519 keypair monkeypatched into
``_PUBLIC_KEY_PEM`` so nothing here depends on the canonical embedded
key. Independent of any installed license file -- the fingerprint is a
trust-anchor fact, not a license-payload fact.
"""
from __future__ import annotations

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


@pytest.fixture
def env(monkeypatch):
    import clawmetry.license as _lic

    priv, pub_pem = _keypair()
    monkeypatch.setattr(_lic, "_PUBLIC_KEY_PEM", pub_pem)

    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True

    return SimpleNamespace(app=flask_app, lic=_lic, priv=priv, pub_pem=pub_pem)


# ── is_pubkey_fingerprint(fp) ─────────────────────────────────────────────────


def test_is_pubkey_fingerprint_true_on_exact_full_match(env):
    fp = env.lic.pubkey_fingerprint()
    assert env.lic.is_pubkey_fingerprint(fp) is True


def test_is_pubkey_fingerprint_case_insensitive(env):
    fp = env.lic.pubkey_fingerprint()
    assert env.lic.is_pubkey_fingerprint(fp.upper()) is True


def test_is_pubkey_fingerprint_strips_whitespace(env):
    fp = env.lic.pubkey_fingerprint()
    assert env.lic.is_pubkey_fingerprint(f"  {fp}  ") is True
    assert env.lic.is_pubkey_fingerprint(f"\n{fp}\n") is True


def test_is_pubkey_fingerprint_strips_colon_separators(env):
    """Many display formats print fingerprints as ``ab:cd:ef:...``. The
    predicate accepts either colon-separated or bare-hex input so an
    operator pasting a fingerprint from a support ticket does not have
    to strip colons themselves."""
    fp = env.lic.pubkey_fingerprint()
    colonised = ":".join(fp[i : i + 2] for i in range(0, len(fp), 2))
    assert env.lic.is_pubkey_fingerprint(colonised) is True


def test_is_pubkey_fingerprint_short_form_matches(env):
    """The 16-char short-form matches iff it is a prefix of the full
    digest, mirroring ``pubkey_info()['fingerprint_short']``."""
    fp = env.lic.pubkey_fingerprint()
    assert env.lic.is_pubkey_fingerprint(fp[:16]) is True


def test_is_pubkey_fingerprint_false_on_wrong_short(env):
    # A 16-char hex string that is NOT a prefix of the real digest must
    # collapse to False -- otherwise short-form matching would let any
    # arbitrary 16-char hex pass.
    fp = env.lic.pubkey_fingerprint()
    # Flip every nibble of the first 16 chars so it is guaranteed not to
    # be a prefix.
    bad_short = "".join(f"{15 - int(c, 16):x}" for c in fp[:16])
    assert env.lic.is_pubkey_fingerprint(bad_short) is False


def test_is_pubkey_fingerprint_false_on_wrong_full(env):
    fp = env.lic.pubkey_fingerprint()
    # Flip the last char so it's still valid hex but a different digest.
    flipped_last = "0" if fp[-1] != "0" else "1"
    wrong = fp[:-1] + flipped_last
    assert env.lic.is_pubkey_fingerprint(wrong) is False


def test_is_pubkey_fingerprint_false_on_empty(env):
    assert env.lic.is_pubkey_fingerprint("") is False
    assert env.lic.is_pubkey_fingerprint("   ") is False


def test_is_pubkey_fingerprint_false_on_non_hex(env):
    # Non-hex must be rejected up-front -- an operator typo like "not-a-fp"
    # should collapse to False, not do a full comparison against the real
    # digest.
    assert env.lic.is_pubkey_fingerprint("not-a-fingerprint") is False
    assert env.lic.is_pubkey_fingerprint("z" * 64) is False


def test_is_pubkey_fingerprint_false_on_wrong_length(env):
    # 32-char (neither full 64 nor short 16) must collapse to False, even
    # though it is valid hex.
    fp = env.lic.pubkey_fingerprint()
    assert env.lic.is_pubkey_fingerprint(fp[:32]) is False


def test_is_pubkey_fingerprint_false_on_non_string(env):
    # ``str()`` coercion means ``None`` becomes "None" (non-hex) -> False.
    # An int similarly coerces to a decimal string with letters missing.
    assert env.lic.is_pubkey_fingerprint(None) is False
    assert env.lic.is_pubkey_fingerprint(12345) is False


def test_is_pubkey_fingerprint_false_when_pubkey_unparseable(env, monkeypatch):
    """If ``pubkey_fingerprint()`` collapses to None (tampered PEM), the
    predicate collapses to False even for a syntactically-plausible
    request -- an attacker cannot force ``is_pubkey_fingerprint`` to True
    by swapping in a broken PEM."""
    monkeypatch.setattr(env.lic, "pubkey_fingerprint", lambda: None)
    assert env.lic.is_pubkey_fingerprint("a" * 64) is False


def test_is_pubkey_fingerprint_never_raises_on_broken_read(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated fingerprint failure")

    monkeypatch.setattr(env.lic, "pubkey_fingerprint", _boom)
    # Wrapped in try/except -> collapses to False.
    assert env.lic.is_pubkey_fingerprint("a" * 64) is False


# ── GET /api/license/pubkey-fingerprint ───────────────────────────────────────


def test_api_pubkey_fingerprint_shape(env):
    client = env.app.test_client()
    resp = client.get("/api/license/pubkey-fingerprint")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == {
        "pubkey_fingerprint_sha256",
        "pubkey_fingerprint_short",
        "valid",
    }
    fp = env.lic.pubkey_fingerprint()
    assert data["pubkey_fingerprint_sha256"] == fp
    assert data["pubkey_fingerprint_short"] == fp[:16]
    assert data["valid"] is True


def test_api_pubkey_fingerprint_matches_pubkey_envelope(env):
    """The scalar endpoint and the existing ``/api/license/pubkey``
    envelope MUST agree on the fingerprint for the same install --
    they share :func:`pubkey_fingerprint` so a UI binding both cannot
    catch them disagreeing."""
    client = env.app.test_client()
    scalar = client.get("/api/license/pubkey-fingerprint").get_json()
    envelope = client.get("/api/license/pubkey").get_json()
    assert scalar["pubkey_fingerprint_sha256"] == envelope["fingerprint_sha256"]
    assert scalar["pubkey_fingerprint_short"] == envelope["fingerprint_short"]


def test_api_pubkey_fingerprint_survives_broken_pubkey(env, monkeypatch):
    """When the embedded PEM can't parse, the endpoint stays HTTP 200
    with the OSS-free branch shape -- never 5xx."""
    monkeypatch.setattr(env.lic, "pubkey_fingerprint", lambda: None)
    client = env.app.test_client()
    resp = client.get("/api/license/pubkey-fingerprint")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "pubkey_fingerprint_sha256": None,
        "pubkey_fingerprint_short": None,
        "valid": False,
    }


def test_api_pubkey_fingerprint_never_5xxs(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated read failure")

    monkeypatch.setattr(env.lic, "pubkey_fingerprint", _boom)
    client = env.app.test_client()
    resp = client.get("/api/license/pubkey-fingerprint")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "pubkey_fingerprint_sha256": None,
        "pubkey_fingerprint_short": None,
        "valid": False,
    }


# ── GET /api/license/is-pubkey-fingerprint ────────────────────────────────────


def test_api_is_pubkey_fingerprint_shape(env):
    client = env.app.test_client()
    fp = env.lic.pubkey_fingerprint()
    resp = client.get(f"/api/license/is-pubkey-fingerprint?fp={fp}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == {
        "is_pubkey_fingerprint",
        "pubkey_fingerprint_sha256",
        "pubkey_fingerprint_short",
        "requested_fp",
        "valid",
    }
    assert data["is_pubkey_fingerprint"] is True
    assert data["pubkey_fingerprint_sha256"] == fp
    assert data["requested_fp"] == fp.lower()
    assert data["valid"] is True


def test_api_is_pubkey_fingerprint_case_insensitive(env):
    client = env.app.test_client()
    fp = env.lic.pubkey_fingerprint()
    resp = client.get(f"/api/license/is-pubkey-fingerprint?fp={fp.upper()}")
    assert resp.get_json()["is_pubkey_fingerprint"] is True


def test_api_is_pubkey_fingerprint_accepts_colon_separators(env):
    client = env.app.test_client()
    fp = env.lic.pubkey_fingerprint()
    colonised = ":".join(fp[i : i + 2] for i in range(0, len(fp), 2))
    resp = client.get(f"/api/license/is-pubkey-fingerprint?fp={colonised}")
    data = resp.get_json()
    assert data["is_pubkey_fingerprint"] is True
    # Normalised echo strips the colons for a UI to render "vs. <fp>".
    assert ":" not in data["requested_fp"]


def test_api_is_pubkey_fingerprint_short_form_matches(env):
    client = env.app.test_client()
    fp = env.lic.pubkey_fingerprint()
    resp = client.get(f"/api/license/is-pubkey-fingerprint?fp={fp[:16]}")
    assert resp.get_json()["is_pubkey_fingerprint"] is True


def test_api_is_pubkey_fingerprint_false_on_wrong(env):
    client = env.app.test_client()
    resp = client.get("/api/license/is-pubkey-fingerprint?fp=" + ("a" * 64))
    data = resp.get_json()
    assert data["is_pubkey_fingerprint"] is False
    # Trust-anchor fields still populate so a UI can show
    # "expected <X>, got <Y>".
    assert data["pubkey_fingerprint_sha256"] == env.lic.pubkey_fingerprint()


def test_api_is_pubkey_fingerprint_false_on_missing_param(env):
    client = env.app.test_client()
    resp = client.get("/api/license/is-pubkey-fingerprint")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_pubkey_fingerprint"] is False
    assert data["requested_fp"] == ""
    # Trust-anchor still populates -- the missing-param branch must not
    # blank out the "currently-active" fields.
    assert data["pubkey_fingerprint_sha256"] == env.lic.pubkey_fingerprint()


def test_api_is_pubkey_fingerprint_false_on_typo(env):
    """A non-hex typo like ``?fp=abcxyz`` collapses to False (non-hex
    rejected up-front) -- a caller cannot silently mis-gate on a bad
    string."""
    client = env.app.test_client()
    resp = client.get("/api/license/is-pubkey-fingerprint?fp=abcxyz")
    data = resp.get_json()
    assert data["is_pubkey_fingerprint"] is False


def test_api_is_pubkey_fingerprint_never_5xxs(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated fingerprint failure")

    monkeypatch.setattr(env.lic, "pubkey_fingerprint", _boom)
    client = env.app.test_client()
    fp_guess = "a" * 64
    resp = client.get(f"/api/license/is-pubkey-fingerprint?fp={fp_guess}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_pubkey_fingerprint"] is False
    assert data["pubkey_fingerprint_sha256"] is None


def test_api_pubkey_fingerprint_and_is_endpoint_agree(env):
    """Binding both endpoints in the same UI tile MUST show a consistent
    trust-anchor snapshot -- they share the same underlying helper."""
    client = env.app.test_client()
    scalar = client.get("/api/license/pubkey-fingerprint").get_json()
    fp = scalar["pubkey_fingerprint_sha256"]
    predicate = client.get(
        f"/api/license/is-pubkey-fingerprint?fp={fp}"
    ).get_json()
    assert scalar["pubkey_fingerprint_sha256"] == predicate["pubkey_fingerprint_sha256"]
    assert scalar["pubkey_fingerprint_short"] == predicate["pubkey_fingerprint_short"]
    assert scalar["valid"] == predicate["valid"]
    assert predicate["is_pubkey_fingerprint"] is True
