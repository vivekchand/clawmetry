"""Tests for the ``is_subject_at(subject, epoch)`` predicate on
``clawmetry.license`` and its paired ``/api/license/is-subject-at`` HTTP
endpoint.

The perspective-epoch predicate on the license-subject axis. Where
:func:`clawmetry.license.is_subject` answers "is this licensed to <X>
right now?", this pair answers "was this licensed to <X> as of
``epoch``?" -- the same retrospective / prospective question
:func:`is_tier_at` answers for the license-tier axis. Both this
predicate and the sibling accessor :func:`license_subject_at` refuse
the invalid-signature branch and use the same ``exp <= epoch`` cutoff,
so they cannot disagree at the boundary when the perspective epoch
equals "now".

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_subject_at.py`` /
``tests/test_license_is_tier_at.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_subject_at.py) -----------------------


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


# -- clawmetry.license.is_subject_at() ----------------------------------------


def test_is_subject_at_no_license(app):
    """No license file on disk -> ``False`` regardless of subject /
    epoch. Mirrors :func:`is_subject`'s no-license branch."""
    now = int(time.time())
    assert app.lic.is_subject_at("acct_test", now) is False
    assert app.lic.is_subject_at("acct_other", now) is False
    assert app.lic.is_subject_at("acct_test", 0) is False
    assert app.lic.is_subject_at("acct_test", 2_000_000_000) is False


def test_is_subject_at_now_matches_is_subject_active(app):
    """When ``epoch`` equals "now", predicate must agree with
    :func:`is_subject` on an active install. Both derive from the same
    signed ``sub`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("acct_test", now) is True
    assert app.lic.is_subject("acct_test") is True


def test_is_subject_at_now_matches_is_subject_lapsed(app):
    """Lapsed-key parity: at "now", both predicates must return
    ``False`` -- both refuse the expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.is_subject_at("acct_test", now) is False
    assert app.lic.is_subject("acct_test") is False


def test_is_subject_at_future_before_expiry(app):
    """Future perspective still before ``exp`` -> ``True`` (key would
    NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.is_subject_at("acct_test", epoch) is True


def test_is_subject_at_future_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``False``
    (the key WILL be expired at that perspective). This is the "will
    this node still be bound to <X> at our next audit?" prospective
    scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.is_subject_at("acct_test", epoch) is False


def test_is_subject_at_past_still_active(app):
    """Perspective BEFORE now on an active key -> ``True`` (the key was
    not yet expired then, since ``exp`` is even further in the
    future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.is_subject_at("acct_test", epoch) is True


def test_is_subject_at_lapsed_key_pre_lapse_true(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    ``True`` (retrospective "was this licensed to <X> on <date>?"). At
    or after ``exp`` -> ``False``."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    assert app.lic.is_subject_at("acct_test", now - 20 * 86400) is True
    assert app.lic.is_subject_at("acct_test", now - 3 * 86400) is False
    assert app.lic.is_subject_at("acct_test", now) is False


def test_is_subject_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, the predicate must collapse to
    ``False`` -- the ``<= epoch`` cutoff matches
    :func:`license_subject_at`'s ``exp <= epoch`` boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    from clawmetry import license as _lic

    info = _lic.current_license_info()
    exp_epoch = int(info["exp"])
    assert app.lic.is_subject_at("acct_test", exp_epoch - 1) is True
    assert app.lic.is_subject_at("acct_test", exp_epoch) is False
    assert app.lic.is_subject_at("acct_test", exp_epoch + 1) is False


def test_is_subject_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> ``True`` at every epoch."""
    _write_perpetual(app)
    assert app.lic.is_subject_at("acct_test", 0) is True
    assert app.lic.is_subject_at("acct_test", int(time.time())) is True
    assert app.lic.is_subject_at("acct_test", 2_000_000_000) is True


def test_is_subject_at_invalid_signature(app):
    """Bogus-signature file -> ``False`` regardless of epoch (time-
    independent, matching :func:`license_subject_at`)."""
    _write_bogus(app)
    assert app.lic.is_subject_at("acct_test", 0) is False
    assert app.lic.is_subject_at("acct_test", int(time.time())) is False
    assert app.lic.is_subject_at("acct_test", 2_000_000_000) is False


def test_is_subject_at_wrong_subject(app):
    """A subject that doesn't match the installed key -> ``False``
    even on an otherwise-active install. The predicate is exact-match
    on the normalised subject."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("acct_other", now) is False
    assert app.lic.is_subject_at("someone@example.com", now) is False


def test_is_subject_at_normalises_query_casing(app):
    """Query subject casing / whitespace is normalised (strip + lower)
    -- ``"Acct_Test"``, ``"acct_test"``, and ``"  ACCT_TEST  "`` all
    match a stored ``"acct_test"``. Matches :func:`is_subject`'s
    normalisation on the current-time axis."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("Acct_Test", now) is True
    assert app.lic.is_subject_at("acct_test", now) is True
    assert app.lic.is_subject_at("  ACCT_TEST  ", now) is True


def test_is_subject_at_normalises_token_casing(app):
    """Token subject casing / whitespace is normalised the same way
    :func:`is_subject` normalises it -- stored ``"  Acct_Test  "``
    matches a query ``"acct_test"``. Note that
    :func:`license_subject_at` PRESERVES casing on read (customer-
    facing form), but the boolean gate compares case-insensitively so
    a UI binding both can render the customer-facing form via
    :func:`license_subject_at` while still gating case-insensitively
    here."""
    tok = app.lic._encode_token(_payload(sub="  Acct_Test  "), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_subject_at("acct_test", int(time.time())) is True
    assert app.lic.license_subject_at(int(time.time())) == "Acct_Test"


def test_is_subject_at_bool_epoch_refused(app):
    """``bool`` is an ``int`` subclass but must be refused so a caller
    passing ``True`` / ``False`` gets ``False`` back, not a spurious
    "was subject X at epoch 1?" answer. Mirrors the ``_at`` family's
    stance."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_subject_at("acct_test", True) is False
    assert app.lic.is_subject_at("acct_test", False) is False


def test_is_subject_at_non_numeric_epoch(app):
    """Non-numeric epoch -> ``False`` so a caller cannot silently
    mis-gate on a typo."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_subject_at("acct_test", "not-a-number") is False
    assert app.lic.is_subject_at("acct_test", None) is False
    assert app.lic.is_subject_at("acct_test", []) is False


def test_is_subject_at_string_epoch_coerced(app):
    """String epoch that ``int()`` accepts -> coerced and honoured,
    matching :func:`license_subject_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("acct_test", str(now)) is True


def test_is_subject_at_empty_subject_query(app):
    """Empty / whitespace-only subject query -> ``False`` even on an
    active install. A caller cannot silently claim "is subject
    empty-string"."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("", now) is False
    assert app.lic.is_subject_at("   ", now) is False


def test_is_subject_at_none_subject_query(app):
    """``None`` subject query -> ``False`` (never-raise posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_subject_at(None, int(time.time())) is False


def test_is_subject_at_open_ended_subject(app):
    """The subject axis is deliberately open-ended -- an unfamiliar
    subject value (e.g. a raw email, a tenant handle) simply doesn't
    match the installed one, but the predicate doesn't gate on a
    whitelist (unlike :func:`is_state_at`). A new customer format
    lands without a code change."""
    tok = app.lic._encode_token(
        _payload(sub="user+tag@example.co.uk", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_subject_at("user+tag@example.co.uk", now) is True
    assert app.lic.is_subject_at("acct_test", now) is False


def test_is_subject_at_missing_sub_claim_matches_scalar(app):
    """Signed payload with no ``sub`` claim: the predicate must agree
    with :func:`license_subject_at` -- both derive from
    :func:`current_license_info`. Guards against the two silently
    diverging on the same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_sub=True)
    now = int(time.time())
    scalar_sub = app.lic.license_subject_at(now)
    if scalar_sub is None:
        assert app.lic.is_subject_at("acct_test", now) is False
        assert app.lic.is_subject_at("anything", now) is False
    else:
        assert app.lic.is_subject_at(scalar_sub, now) is True


def test_is_subject_at_parity_with_is_subject_at_now(app):
    """At ``epoch=now``, ``is_subject_at(s, now)`` must byte-equal
    ``is_subject(s)`` for every canonical subject. Both derive from
    the same signed ``sub`` claim."""
    tok = app.lic._encode_token(
        _payload(sub="acct_prod", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    for s in ("acct_prod", "acct_test", "someone@example.com", "ACCT_PROD"):
        assert app.lic.is_subject_at(s, now) == app.lic.is_subject(s), s


def test_is_subject_at_parity_with_license_subject_at(app):
    """For a canonical set of subjects, ``is_subject_at(s, e)`` must
    equal ``(license_subject_at(e) or "").strip().lower() ==
    s.strip().lower()`` for a non-empty ``s``. Pins the predicate to
    the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for epoch in [now - 10 * 86400, now, now + 10 * 86400, now + 60 * 86400]:
        scalar_sub = app.lic.license_subject_at(epoch)
        for s in ("acct_test", "acct_other", "Acct_Test"):
            requested = s.strip().lower()
            expected = (
                bool(requested)
                and isinstance(scalar_sub, str)
                and scalar_sub.strip().lower() == requested
            )
            assert app.lic.is_subject_at(s, epoch) is expected, (s, epoch)


def test_is_subject_at_never_raises(app, monkeypatch):
    """If :func:`license_subject_at` blows up under this predicate, it
    collapses to ``False`` rather than propagating. A scheduled audit
    job bound to this gate cannot crash on a bad install."""
    def _boom(_epoch):
        raise RuntimeError("simulated corruption")

    monkeypatch.setattr(app.lic, "license_subject_at", _boom)
    assert app.lic.is_subject_at("acct_test", int(time.time())) is False


# -- GET /api/license/is-subject-at -------------------------------------------


def test_api_is_subject_at_no_license(app):
    """No license file on disk -> ``is_subject_at=false``, all
    reference fields reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-subject-at?subject=acct_test&epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["is_subject_at"] is False
    assert body["subject_at"] is None
    assert body["requested_subject"] == "acct_test"
    assert body["requested_epoch"] == now
    assert body["subject"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_api_is_subject_at_active_key_now(app):
    """Active key at "now" -> ``is_subject_at=true``, snapshot fields
    intact."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-subject-at?subject=acct_test&epoch={now}")
    body = rv.get_json()
    assert body["is_subject_at"] is True
    assert body["subject_at"] == "acct_test"
    assert body["subject"] == "acct_test"
    assert body["expires_at"] is not None
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_is_subject_at_wrong_subject(app):
    """Active key + a subject that doesn't match -> ``is_subject_at=
    false`` but ``subject_at`` still surfaces the real subject so a UI
    can render the "you asked <X> but this is licensed to <Y>" copy."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-subject-at?subject=acct_other&epoch={now}")
    body = rv.get_json()
    assert body["is_subject_at"] is False
    assert body["subject_at"] == "acct_test"
    assert body["subject"] == "acct_test"
    assert body["requested_subject"] == "acct_other"


def test_api_is_subject_at_missing_epoch_collapses(app):
    """Missing / non-integer / bool ``epoch`` -> ``is_subject_at=false``
    and ``requested_epoch=null`` so a caller cannot silently mis-gate
    on a typo. HTTP status stays 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as client:
        for qs in (
            "?subject=acct_test",
            "?subject=acct_test&epoch=",
            "?subject=acct_test&epoch=nope",
            "?subject=acct_test&epoch=true",
        ):
            rv = client.get(f"/api/license/is-subject-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["is_subject_at"] is False, qs
            assert body["requested_epoch"] is None, qs


def test_api_is_subject_at_missing_subject_collapses(app):
    """Missing / empty ``subject`` -> ``is_subject_at=false`` even on
    an active install at a valid epoch. HTTP status stays 200. A
    caller cannot silently claim a subject that would grant unearned
    entitlement."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for qs in (
            f"?epoch={now}",
            f"?subject=&epoch={now}",
            f"?subject=%20%20%20&epoch={now}",
        ):
            rv = client.get(f"/api/license/is-subject-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["is_subject_at"] is False, qs
            assert body["requested_subject"] == "", qs
            # The snapshot fields still surface (this endpoint never
            # withholds them just because the query was blank).
            assert body["subject"] == "acct_test", qs


def test_api_is_subject_at_future_after_expiry(app):
    """Future perspective past ``exp`` on an active key ->
    ``is_subject_at=false`` and ``subject_at=null`` even though
    ``subject`` (current-time) still surfaces the account."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-subject-at?subject=acct_test&epoch={epoch}")
    body = rv.get_json()
    assert body["is_subject_at"] is False
    assert body["subject_at"] is None
    assert body["subject"] == "acct_test"


def test_api_is_subject_at_invalid_signature(app):
    """Bogus-signature file -> ``is_subject_at=false``. ``has_license
    =True`` (a file exists) but ``valid=False``. Time-independent."""
    _write_bogus(app)
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={int(time.time())}"
        )
    body = rv.get_json()
    assert body["is_subject_at"] is False
    assert body["subject_at"] is None
    assert body["subject"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_is_subject_at_normalises_casing(app):
    """Query subject casing / whitespace is normalised (strip + lower)
    server-side. ``requested_subject`` echoes the normalised form."""
    tok = app.lic._encode_token(_payload(sub="Acct_Test"), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for raw in ("Acct_Test", "acct_test", "  ACCT_TEST  "):
            from urllib.parse import quote

            rv = client.get(
                f"/api/license/is-subject-at?subject={quote(raw)}&epoch={now}"
            )
            body = rv.get_json()
            assert body["is_subject_at"] is True, raw
            assert body["requested_subject"] == "acct_test", raw
            # Case is preserved on the read-through field, matching
            # /api/license/subject-at.
            assert body["subject_at"] == "Acct_Test", raw


def test_api_is_subject_at_lapsed_key_pre_lapse(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    ``is_subject_at=true``; at "now" (past ``exp``) -> ``false``. The
    current-time reference ``subject`` field stays ``null`` on the
    lapsed install throughout."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    with app.app.test_client() as client:
        rv_pre = client.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={now - 20 * 86400}"
        ).get_json()
        rv_now = client.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={now}"
        ).get_json()
    assert rv_pre["is_subject_at"] is True
    assert rv_pre["subject_at"] == "acct_test"
    assert rv_pre["subject"] is None  # current-time still lapsed
    assert rv_now["is_subject_at"] is False
    assert rv_now["subject_at"] is None


def test_api_is_subject_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> ``is_subject_at=true`` at every
    epoch."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in (0, now, 2_000_000_000):
            rv = client.get(
                f"/api/license/is-subject-at?subject=acct_test&epoch={epoch}"
            )
            body = rv.get_json()
            assert body["is_subject_at"] is True, epoch
            assert body["subject_at"] == "acct_test", epoch
            assert body["subject"] == "acct_test", epoch


def test_api_is_subject_at_scalar_parity_with_python(app):
    """The endpoint must return exactly what
    :func:`is_subject_at` would return for the same (subject, epoch)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in [now - 10 * 86400, now, now + 5 * 86400, now + 40 * 86400]:
            for s in ("acct_test", "acct_other", "Acct_Test"):
                rv = client.get(
                    f"/api/license/is-subject-at?subject={s}&epoch={epoch}"
                )
                body = rv.get_json()
                assert body["is_subject_at"] == app.lic.is_subject_at(s, epoch), (
                    s,
                    epoch,
                )


# -- cross-endpoint agreement -------------------------------------------------


def test_api_is_subject_at_agrees_with_is_subject_endpoint_at_now(app):
    """At ``epoch=now``, the ``is_subject_at`` field must byte-equal
    the ``is_subject`` returned by ``/api/license/is-subject`` (the
    current-time endpoint) for the same subject. Both derive from the
    same signed claim -- a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for s in ("acct_test", "acct_other"):
            rv_now = client.get(f"/api/license/is-subject?subject={s}").get_json()
            rv_at = client.get(
                f"/api/license/is-subject-at?subject={s}&epoch={now}"
            ).get_json()
            assert rv_at["is_subject_at"] == rv_now["is_subject"], s


def test_api_is_subject_at_shared_snapshot_agreement_with_subject_at(app):
    """The current-time reference fields (``subject``, ``expires_at``,
    ``has_license``, ``valid``) on this response must byte-equal the
    same fields on the sibling ``/api/license/subject-at`` response
    for the same install -- both endpoints share
    :func:`_license_subject_at_snapshot`, so a UI binding both for the
    same install cannot catch them disagreeing on the reference
    fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_is = client.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={now}"
        ).get_json()
        rv_scalar = client.get(
            f"/api/license/subject-at?epoch={now}"
        ).get_json()
    assert rv_is["subject"] == rv_scalar["subject"]
    assert rv_is["subject_at"] == rv_scalar["subject_at"]
    assert rv_is["expires_at"] == rv_scalar["expires_at"]
    assert rv_is["has_license"] == rv_scalar["has_license"]
    assert rv_is["valid"] == rv_scalar["valid"]


def test_api_is_subject_at_never_5xxs_on_snapshot_failure(app, monkeypatch):
    """Underlying snapshot failure -> endpoint still returns HTTP 200
    with the OSS-free branch shape (never 5xxs), matching the
    surrounding license endpoints."""
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated snapshot failure")

    monkeypatch.setattr(app.lic, "current_license_info", _boom)
    monkeypatch.setattr(app.lic, "license_subject", _boom)
    monkeypatch.setattr(app.lic, "license_expires_at", _boom)
    monkeypatch.setattr(app.lic, "license_subject_at", _boom)
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={int(time.time())}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["is_subject_at"] is False
    assert body["subject_at"] is None
    assert body["subject"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False
