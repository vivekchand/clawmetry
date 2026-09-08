"""Tests for the ``license_subject_at(epoch)`` scalar on
``clawmetry.license`` and its paired ``/api/license/subject-at`` HTTP
endpoint.

The perspective-epoch flavour of the ``license_subject`` scalar. Both
derive from the same signed ``sub`` claim and refuse the invalid-
signature branch, so they cannot disagree at the boundary when the
perspective epoch equals "now"; on any other epoch these helpers answer
"who would :func:`license_subject` have reported evaluated as of
``epoch``?" without the caller having to snapshot the license state at
that time or compare ``exp`` to a caller-supplied epoch themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_tier_at.py`` /
``tests/test_license_subject_scalar.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror tests/test_license_tier_at.py) --------------------


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
    sub="acct_test",
    tier="pro",
    nodes=3,
    exp_delta=365 * 86400,
    drop_exp=False,
    drop_sub=False,
):
    now = int(time.time())
    p = {
        "sub": sub,
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }
    if drop_exp:
        p.pop("exp", None)
    if drop_sub:
        p.pop("sub", None)
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


def _write_key_direct(app, exp_delta, sub="acct_test", drop_sub=False):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed."""
    import os

    tok = app.lic._encode_token(
        _payload(sub=sub, exp_delta=exp_delta, drop_sub=drop_sub), app.priv
    )
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_perpetual(app, sub="acct_test"):
    import os

    tok = app.lic._encode_token(_payload(sub=sub, drop_exp=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_subject_at() -----------------------------------


def test_license_subject_at_no_license(app):
    """No license file on disk -> ``None`` regardless of epoch."""
    assert app.lic.license_subject_at(int(time.time())) is None
    assert app.lic.license_subject_at(0) is None
    assert app.lic.license_subject_at(2_000_000_000) is None


def test_license_subject_at_now_matches_license_subject_active(app):
    """When ``epoch`` equals "now", perspective scalar must agree with
    :func:`license_subject` on an active install. Both derive from the
    same signed ``sub`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_subject_at(now) == "acct_test"
    assert app.lic.license_subject() == "acct_test"


def test_license_subject_at_now_matches_license_subject_lapsed(app):
    """Lapsed-key parity: at "now", perspective scalar and base scalar
    must both return ``None`` -- both refuse the expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.license_subject_at(now) is None
    assert app.lic.license_subject() is None


def test_license_subject_at_future_epoch_before_expiry(app):
    """Future perspective still before ``exp`` -> subject surfaces (key
    would NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.license_subject_at(epoch) == "acct_test"


def test_license_subject_at_future_epoch_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``None``
    (the key WILL be expired at that perspective). This is the "will
    this node still be bound to <X> at our next audit?" prospective
    scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.license_subject_at(epoch) is None


def test_license_subject_at_past_epoch_still_active(app):
    """Perspective BEFORE now on an active key -> subject surfaces (the
    key was not yet expired then, since ``exp`` is even further in the
    future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.license_subject_at(epoch) == "acct_test"


def test_license_subject_at_lapsed_key_pre_lapse_epoch_surfaces_subject(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    subject surfaces (retrospective "who was this licensed to on
    <date>?"). At "now" (past ``exp``) -> ``None``."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    assert app.lic.license_subject_at(now - 20 * 86400) == "acct_test"
    assert app.lic.license_subject_at(now - 3 * 86400) is None
    assert app.lic.license_subject_at(now) is None


def test_license_subject_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, the subject must collapse to
    ``None`` -- the ``<= epoch`` cutoff matches :func:`license_tier_at`
    and :func:`license_state_at`'s ``exp <= epoch`` boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    from clawmetry import license as _lic

    info = _lic.current_license_info()
    exp_epoch = int(info["exp"])
    assert app.lic.license_subject_at(exp_epoch - 1) == "acct_test"
    assert app.lic.license_subject_at(exp_epoch) is None
    assert app.lic.license_subject_at(exp_epoch + 1) is None


def test_license_subject_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> subject surfaces at every epoch."""
    _write_perpetual(app)
    assert app.lic.license_subject_at(0) == "acct_test"
    assert app.lic.license_subject_at(int(time.time())) == "acct_test"
    assert app.lic.license_subject_at(2_000_000_000) == "acct_test"


def test_license_subject_at_invalid_signature(app):
    """Bogus-signature file -> ``None`` regardless of epoch (time-
    independent, matching :func:`license_subject`)."""
    _write_bogus(app)
    assert app.lic.license_subject_at(0) is None
    assert app.lic.license_subject_at(int(time.time())) is None
    assert app.lic.license_subject_at(2_000_000_000) is None


def test_license_subject_at_preserves_casing(app):
    """Subject casing is PRESERVED -- unlike :func:`license_tier_at`
    which lowercases. Subjects are typically email addresses / account
    ids where case can matter for exact-match comparisons, so the
    perspective-epoch accessor must render the customer-facing form
    verbatim, matching :func:`license_subject`. Whitespace IS
    stripped."""
    tok = app.lic._encode_token(_payload(sub="  Acct_Test  "), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_subject_at(int(time.time())) == "Acct_Test"


def test_license_subject_at_missing_sub_claim_matches_scalar(app):
    """Signed payload with no ``sub`` claim: the perspective-epoch
    scalar MUST match :func:`license_subject` on the same install (both
    derive from :func:`current_license_info`). This test pins parity
    with the base scalar -- guards against the two scalars silently
    diverging on the same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_sub=True)
    now = int(time.time())
    assert app.lic.license_subject_at(now) == app.lic.license_subject()


def test_license_subject_at_empty_sub_claim(app):
    """Signed payload with an empty / whitespace-only ``sub`` -> ``None``
    (matches :func:`license_subject`: an empty string is nothing to
    surface)."""
    tok = app.lic._encode_token(_payload(sub="   "), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_subject_at(now) is None
    assert app.lic.license_subject() is None


def test_license_subject_at_bool_epoch_refused(app):
    """``bool`` is an ``int`` subclass but must be refused so a caller
    passing ``True`` / ``False`` gets ``None`` back, not a spurious
    "was subject X at epoch 1?" answer."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_subject_at(True) is None
    assert app.lic.license_subject_at(False) is None


def test_license_subject_at_non_numeric_epoch(app):
    """Non-numeric epoch -> ``None`` so a caller cannot silently mis-
    gate on a typo -- conservative fallback since ``None`` implies no
    trustworthy subject."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_subject_at("not-a-number") is None
    assert app.lic.license_subject_at(None) is None
    assert app.lic.license_subject_at([]) is None


def test_license_subject_at_string_epoch_coerced(app):
    """String epoch that ``int()`` accepts -> coerced and honoured,
    matching the behaviour of :func:`license_tier_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_subject_at(str(now)) == "acct_test"


def test_license_subject_at_never_raises(app, monkeypatch):
    """Any underlying introspection failure collapses to ``None`` --
    a scheduled audit tile bound to this helper never crashes on a
    partial install."""
    def _boom():
        raise RuntimeError("simulated introspection failure")

    monkeypatch.setattr(app.lic, "current_license_info", _boom)
    # Must not raise on any input.
    assert app.lic.license_subject_at(int(time.time())) is None
    assert app.lic.license_subject_at(0) is None


# -- GET /api/license/subject-at ----------------------------------------------


def test_api_subject_at_no_license(app):
    """No license file on disk -> ``subject_at=null``, current-time
    reference fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["subject_at"] is None
    assert body["requested_epoch"] == now
    assert body["subject"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_api_subject_at_active_key_now(app):
    """Active key at "now" -> ``subject_at=subject``, snapshot fields
    intact."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={now}")
    body = rv.get_json()
    assert body["subject_at"] == "acct_test"
    assert body["subject"] == "acct_test"
    assert body["expires_at"] is not None
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_subject_at_missing_epoch_collapses(app):
    """Missing / non-integer / bool ``epoch`` -> ``subject_at=null`` and
    ``requested_epoch=null`` so a caller cannot silently mis-gate on a
    typo. HTTP status stays 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as client:
        for qs in ("", "?epoch=", "?epoch=nope", "?epoch=true"):
            rv = client.get(f"/api/license/subject-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["subject_at"] is None, qs
            assert body["requested_epoch"] is None, qs


def test_api_subject_at_future_after_expiry(app):
    """Future perspective past ``exp`` on an active key ->
    ``subject_at=null`` even though ``subject`` (current-time) still
    surfaces the account."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={epoch}")
    body = rv.get_json()
    assert body["subject_at"] is None
    assert body["subject"] == "acct_test"


def test_api_subject_at_invalid_signature(app):
    """Bogus-signature file -> ``subject_at=null``. ``has_license=True``
    (a file exists) but ``valid=False``. Time-independent."""
    _write_bogus(app)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={int(time.time())}")
    body = rv.get_json()
    assert body["subject_at"] is None
    assert body["subject"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_subject_at_scalar_parity_with_python(app):
    """The endpoint must return exactly what
    :func:`license_subject_at` would return for the same epoch."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in [now - 10 * 86400, now, now + 5 * 86400, now + 40 * 86400]:
            rv = client.get(f"/api/license/subject-at?epoch={epoch}")
            body = rv.get_json()
            assert body["subject_at"] == app.lic.license_subject_at(epoch), epoch


def test_api_subject_at_lapsed_key_pre_lapse_epoch(app):
    """Endpoint mirrors the scalar retrospective behaviour: on a lapsed
    key at a perspective BEFORE its ``exp`` -> ``subject_at`` surfaces;
    at "now" (past ``exp``) -> ``null``. The current-time reference
    ``subject`` field stays ``null`` on the lapsed install throughout."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    with app.app.test_client() as client:
        rv_pre = client.get(
            f"/api/license/subject-at?epoch={now - 20 * 86400}"
        ).get_json()
        rv_now = client.get(f"/api/license/subject-at?epoch={now}").get_json()
    assert rv_pre["subject_at"] == "acct_test"
    assert rv_pre["subject"] is None  # current-time still lapsed
    assert rv_now["subject_at"] is None


def test_api_subject_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> subject surfaces at every epoch."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in (0, now, 2_000_000_000):
            rv = client.get(f"/api/license/subject-at?epoch={epoch}")
            body = rv.get_json()
            assert body["subject_at"] == "acct_test", epoch
            assert body["subject"] == "acct_test", epoch


def test_api_subject_at_preserves_casing(app):
    """Subject casing is preserved -- endpoint must render the customer-
    facing form verbatim, matching :func:`license_subject_at`."""
    tok = app.lic._encode_token(_payload(sub="  Acct_Test  "), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={now}")
    body = rv.get_json()
    assert body["subject_at"] == "Acct_Test"
    assert body["subject"] == "Acct_Test"


# -- cross-endpoint agreement -------------------------------------------------


def test_api_subject_at_agrees_with_license_subject_endpoint_at_now(app):
    """At ``epoch=now``, the ``subject_at`` field must byte-equal the
    ``subject`` returned by ``/api/license/subject`` (the current-time
    endpoint). Both derive from the same signed claim -- a UI binding
    both cannot catch them disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_now = client.get("/api/license/subject").get_json()
        rv_at = client.get(f"/api/license/subject-at?epoch={now}").get_json()
    assert rv_at["subject_at"] == rv_now["subject"]
    assert rv_at["subject"] == rv_now["subject"]


def test_api_subject_at_shared_snapshot_agreement_with_tier_at(app):
    """The current-time reference fields (``expires_at``,
    ``has_license``, ``valid``) on this response must byte-equal the
    same fields on the sibling ``/api/license/tier-at`` response for
    the same install -- both endpoints derive them from the same
    underlying ``current_license_info`` / ``license_expires_at`` read,
    so a UI binding both for the same install cannot catch them
    disagreeing on the reference fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_subject = client.get(
            f"/api/license/subject-at?epoch={now}"
        ).get_json()
        rv_tier = client.get(f"/api/license/tier-at?epoch={now}").get_json()
    assert rv_subject["expires_at"] == rv_tier["expires_at"]
    assert rv_subject["has_license"] == rv_tier["has_license"]
    assert rv_subject["valid"] == rv_tier["valid"]


def test_api_subject_at_never_5xxs_on_snapshot_failure(app, monkeypatch):
    """Underlying snapshot failure -> endpoint still returns HTTP 200
    with the OSS-free branch shape (never 5xxs), matching the surround-
    ing license endpoints."""
    def _boom():
        raise RuntimeError("simulated snapshot failure")

    monkeypatch.setattr(app.lic, "current_license_info", _boom)
    monkeypatch.setattr(app.lic, "license_subject", _boom)
    monkeypatch.setattr(app.lic, "license_expires_at", _boom)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/subject-at?epoch={int(time.time())}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["subject_at"] is None
    assert body["subject"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False
