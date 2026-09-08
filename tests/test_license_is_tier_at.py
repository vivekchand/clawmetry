"""Tests for the ``is_tier_at(tier, epoch)`` predicate and
``is_tier_at_batch(tier, epochs)`` batch on ``clawmetry.license`` and
their paired ``/api/license/is-tier-at`` / ``/api/license/is-tier-at-batch``
HTTP endpoints.

The perspective-epoch predicate on the license-tier axis. Where
:func:`clawmetry.license.is_tier` answers "am I on tier <X> right now?",
this pair answers "was I on tier <X> as of ``epoch``?" -- the same
retrospective / prospective question :func:`is_state_at` answers for
license state. Both this pair and the sibling accessor
:func:`license_tier_at` refuse the invalid-signature branch and use
the same ``exp <= epoch`` cutoff, so they cannot disagree at the
boundary when the perspective epoch equals "now".

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_tier_at.py`` / ``tests/test_license_
state_at_batch.py`` so nothing depends on the real production signing
key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_tier_at.py) --------------------------


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, drop_exp=False, drop_tier=False):
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
    if drop_tier:
        p.pop("tier", None)
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


def _write_key_direct(app, exp_delta, tier="pro", drop_tier=False):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed."""
    import os

    tok = app.lic._encode_token(
        _payload(tier=tier, exp_delta=exp_delta, drop_tier=drop_tier), app.priv
    )
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_perpetual(app, tier="pro"):
    import os

    tok = app.lic._encode_token(_payload(tier=tier, drop_exp=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.is_tier_at() -------------------------------------------


def test_is_tier_at_no_license(app):
    """No license file on disk -> ``False`` regardless of tier / epoch.
    Mirrors :func:`is_tier`'s no-license branch."""
    now = int(time.time())
    assert app.lic.is_tier_at("pro", now) is False
    assert app.lic.is_tier_at("enterprise", now) is False
    assert app.lic.is_tier_at("pro", 0) is False
    assert app.lic.is_tier_at("pro", 2_000_000_000) is False


def test_is_tier_at_now_matches_is_tier_active(app):
    """When ``epoch`` equals "now", predicate must agree with
    :func:`is_tier` on an active install. Both derive from the same
    signed ``tier`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("pro", now) is True
    assert app.lic.is_tier("pro") is True


def test_is_tier_at_now_matches_is_tier_lapsed(app):
    """Lapsed-key parity: at "now", both predicates must return
    ``False`` -- both refuse the expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.is_tier_at("pro", now) is False
    assert app.lic.is_tier("pro") is False


def test_is_tier_at_future_before_expiry(app):
    """Future perspective still before ``exp`` -> ``True`` (key would
    NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.is_tier_at("pro", epoch) is True


def test_is_tier_at_future_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``False``
    (the key WILL be expired at that perspective). This is the "will
    this node still be Pro at our next audit?" prospective scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.is_tier_at("pro", epoch) is False


def test_is_tier_at_past_still_active(app):
    """Perspective BEFORE now on an active key -> ``True`` (the key was
    not yet expired then, since ``exp`` is even further in the future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.is_tier_at("pro", epoch) is True


def test_is_tier_at_lapsed_key_pre_lapse_true(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    ``True`` (retrospective "was this Pro on <date>?"). At/after ``exp``
    -> ``False``."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    assert app.lic.is_tier_at("pro", now - 20 * 86400) is True
    assert app.lic.is_tier_at("pro", now - 3 * 86400) is False
    assert app.lic.is_tier_at("pro", now) is False


def test_is_tier_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, the predicate must collapse to
    ``False`` -- the ``<= epoch`` cutoff matches
    :func:`license_tier_at`'s ``exp <= epoch`` boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    from clawmetry import license as _lic

    info = _lic.current_license_info()
    exp_epoch = int(info["exp"])
    assert app.lic.is_tier_at("pro", exp_epoch - 1) is True
    assert app.lic.is_tier_at("pro", exp_epoch) is False
    assert app.lic.is_tier_at("pro", exp_epoch + 1) is False


def test_is_tier_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> ``True`` at every epoch."""
    _write_perpetual(app)
    assert app.lic.is_tier_at("pro", 0) is True
    assert app.lic.is_tier_at("pro", int(time.time())) is True
    assert app.lic.is_tier_at("pro", 2_000_000_000) is True


def test_is_tier_at_invalid_signature(app):
    """Bogus-signature file -> ``False`` regardless of epoch (time-
    independent, matching :func:`license_tier_at`)."""
    _write_bogus(app)
    assert app.lic.is_tier_at("pro", 0) is False
    assert app.lic.is_tier_at("pro", int(time.time())) is False
    assert app.lic.is_tier_at("pro", 2_000_000_000) is False


def test_is_tier_at_wrong_tier(app):
    """A tier that doesn't match the installed key -> ``False`` even
    on an otherwise-active install. The predicate is exact-match on
    the normalised tier."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("enterprise", now) is False
    assert app.lic.is_tier_at("trial", now) is False
    assert app.lic.is_tier_at("free", now) is False


def test_is_tier_at_normalises_query_casing(app):
    """Query tier casing / whitespace is normalised -- ``"Pro"``,
    ``"pro"``, and ``"  PRO  "`` all match a stored ``"pro"``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("Pro", now) is True
    assert app.lic.is_tier_at("pro", now) is True
    assert app.lic.is_tier_at("  PRO  ", now) is True


def test_is_tier_at_normalises_token_casing(app):
    """Token tier casing / whitespace is normalised the same way
    :func:`license_tier_at` normalises it -- stored ``"  PRO  "``
    matches a query ``"pro"``."""
    tok = app.lic._encode_token(_payload(tier="  PRO  "), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier_at("pro", int(time.time())) is True


def test_is_tier_at_bool_epoch_refused(app):
    """``bool`` is an ``int`` subclass but must be refused so a caller
    passing ``True`` / ``False`` gets ``False`` back, not a spurious
    "was tier X at epoch 1?" answer. Mirrors the ``_at`` family's
    stance."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier_at("pro", True) is False
    assert app.lic.is_tier_at("pro", False) is False


def test_is_tier_at_non_numeric_epoch(app):
    """Non-numeric epoch -> ``False`` so a caller cannot silently
    mis-gate on a typo."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier_at("pro", "not-a-number") is False
    assert app.lic.is_tier_at("pro", None) is False
    assert app.lic.is_tier_at("pro", []) is False


def test_is_tier_at_string_epoch_coerced(app):
    """String epoch that ``int()`` accepts -> coerced and honoured,
    matching :func:`license_tier_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("pro", str(now)) is True


def test_is_tier_at_empty_tier_query(app):
    """Empty / whitespace-only tier query -> ``False`` even on an
    active install. A caller cannot silently claim "is on tier
    empty-string"."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("", now) is False
    assert app.lic.is_tier_at("   ", now) is False


def test_is_tier_at_none_tier_query(app):
    """``None`` tier query -> ``False`` (never-raise posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_tier_at(None, int(time.time())) is False


def test_is_tier_at_open_ended_tier(app):
    """The tier axis is deliberately open-ended -- an unfamiliar tier
    name simply doesn't match, but the predicate doesn't gate on a
    whitelist (unlike :func:`is_state_at`). A future tier lands
    without a code change."""
    tok = app.lic._encode_token(_payload(tier="galactic", exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_tier_at("galactic", now) is True
    assert app.lic.is_tier_at("pro", now) is False


def test_is_tier_at_missing_tier_claim_matches_scalar(app):
    """Signed payload with no ``tier`` claim: the predicate must agree
    with :func:`license_tier_at` -- both derive from
    :func:`current_license_info` which today defaults a missing
    ``tier`` claim. Guards against the two silently diverging on the
    same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_tier=True)
    now = int(time.time())
    scalar_tier = app.lic.license_tier_at(now)
    if scalar_tier is None:
        assert app.lic.is_tier_at("pro", now) is False
        assert app.lic.is_tier_at("anything", now) is False
    else:
        assert app.lic.is_tier_at(scalar_tier, now) is True


def test_is_tier_at_parity_with_is_tier_at_now(app):
    """At ``epoch=now``, ``is_tier_at(t, now)`` must byte-equal
    ``is_tier(t)`` for every canonical tier. Both derive from the same
    signed ``tier`` claim."""
    tok = app.lic._encode_token(_payload(tier="enterprise", exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for t in ("pro", "enterprise", "trial", "free"):
        assert app.lic.is_tier_at(t, now) == app.lic.is_tier(t), t


def test_is_tier_at_parity_with_license_tier_at(app):
    """For a canonical set of tiers, ``is_tier_at(t, e)`` must equal
    ``license_tier_at(e) == t``. Pins the predicate to the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for epoch in [now - 10 * 86400, now, now + 10 * 86400, now + 60 * 86400]:
        scalar_tier = app.lic.license_tier_at(epoch)
        for t in ("pro", "enterprise", "trial"):
            expected = scalar_tier is not None and scalar_tier == t
            assert app.lic.is_tier_at(t, epoch) is expected, (t, epoch)


def test_is_tier_at_never_raises(app, monkeypatch):
    """If :func:`license_tier_at` blows up under this predicate, it
    collapses to ``False`` rather than propagating. A scheduled audit
    job bound to this gate cannot crash on a bad install."""
    def _boom(_epoch):
        raise RuntimeError("simulated corruption")

    monkeypatch.setattr(app.lic, "license_tier_at", _boom)
    assert app.lic.is_tier_at("pro", int(time.time())) is False


# -- clawmetry.license.is_tier_at_batch() -------------------------------------


def test_is_tier_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Mirrors the never-raise posture
    of the sibling per-value axis batches."""
    assert app.lic.is_tier_at_batch("pro", None) == []


def test_is_tier_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.is_tier_at_batch("pro", 42) == []


def test_is_tier_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.is_tier_at_batch("pro", []) == []
    assert app.lic.is_tier_at_batch("pro", ()) == []


def test_is_tier_at_batch_no_license(app):
    """No license file on disk -> every row ``False`` regardless of
    epoch. Time-independent, matches the scalar."""
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.is_tier_at_batch("pro", epochs)
    assert [r["is_tier"] for r in rows] == [False] * 3
    assert [r["epoch"] for r in rows] == epochs


def test_is_tier_at_batch_active_mixed(app):
    """Active key: rows before ``exp`` -> ``True``; rows after -> ``False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    rows = app.lic.is_tier_at_batch("pro", epochs)
    assert [r["is_tier"] for r in rows] == [True, True, False, False]
    assert [r["epoch"] for r in rows] == epochs


def test_is_tier_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_tier_at` -- the batch cannot
    silently drift from the scalar. Pin every row against the singular
    helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [
        now - 10 * 86400,
        now,
        now + 5 * 86400,
        now + 40 * 86400,
        now + 200 * 86400,
    ]
    rows = app.lic.is_tier_at_batch("pro", epochs)
    for row, epoch in zip(rows, epochs):
        assert row["is_tier"] == app.lic.is_tier_at("pro", epoch), epoch


def test_is_tier_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> ``True`` at every row."""
    _write_perpetual(app)
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.is_tier_at_batch("pro", epochs)
    assert [r["is_tier"] for r in rows] == [True] * 3


def test_is_tier_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``False`` (time-independent)."""
    _write_bogus(app)
    rows = app.lic.is_tier_at_batch("pro", [0, int(time.time()), 2_000_000_000])
    assert [r["is_tier"] for r in rows] == [False] * 3


def test_is_tier_at_batch_lapsed_key_flips_per_row(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    ``True``; at/after ``exp`` -> ``False``. Batch flips per row."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.is_tier_at_batch(
        "pro", [now - 20 * 86400, now - 3 * 86400, now]
    )
    assert [r["is_tier"] for r in rows] == [True, False, False]


def test_is_tier_at_batch_wrong_tier_all_false(app):
    """A tier that doesn't match the installed key -> every row
    ``False`` even on an otherwise-active install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch("enterprise", [now, now + 3600, now + 86400])
    assert [r["is_tier"] for r in rows] == [False, False, False]


def test_is_tier_at_batch_bad_epochs_collapse_per_row(app):
    """``bool`` / non-numeric epochs collapse to a row with
    ``is_tier=False`` with the raw token surfaced in ``epoch`` --
    matches the never-mis-gate posture the scalar uses for the same
    inputs."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch(
        "pro", [now, True, "nope", None, now + 3600]
    )
    assert len(rows) == 5
    good = [r for r in rows if isinstance(r["epoch"], int) and r["is_tier"] is True]
    assert len(good) == 2
    bad = [r for r in rows if r["is_tier"] is False]
    assert len(bad) == 3


def test_is_tier_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order for
    byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch("pro", [now, now, now + 10, now])
    assert [r["epoch"] for r in rows] == [now, now + 10]


def test_is_tier_at_batch_string_epochs_coerced(app):
    """String tokens that ``int()`` accepts -> coerced and honoured,
    matching the query-string surface (the batch endpoint hands the
    helper stripped tokens)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch("pro", [str(now), str(now + 10)])
    assert [r["is_tier"] for r in rows] == [True, True]


def test_is_tier_at_batch_normalises_query_casing(app):
    """Query tier casing / whitespace is normalised on the batch the
    same way the scalar normalises it. ``"  PRO  "`` matches a stored
    ``"pro"`` across every row."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch("  PRO  ", [now, now + 3600])
    assert [r["is_tier"] for r in rows] == [True, True]


def test_is_tier_at_batch_empty_tier_all_false(app):
    """Empty / whitespace-only tier collapses EVERY row to
    ``is_tier=False`` while preserving row slots. A caller on a stale
    UI shouldn't have the whole batch silently drop."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch("", [now, now + 3600])
    assert [r["is_tier"] for r in rows] == [False, False]
    assert len(rows) == 2


def test_is_tier_at_batch_none_tier_all_false(app):
    """``None`` tier query collapses every row to ``False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_tier_at_batch(None, [now, now + 3600])
    assert [r["is_tier"] for r in rows] == [False, False]


def test_is_tier_at_batch_missing_tier_claim_matches_scalar(app):
    """Signed payload with no ``tier`` claim: every row must byte-
    equal the singular :func:`is_tier_at` for the same tier / epoch.
    Guards the batch from silently diverging from the scalar on the
    same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_tier=True)
    now = int(time.time())
    epochs = [now, now + 3600, now + 86400]
    for query_tier in ("pro", "enterprise"):
        rows = app.lic.is_tier_at_batch(query_tier, epochs)
        for row, epoch in zip(rows, epochs):
            assert row["is_tier"] == app.lic.is_tier_at(query_tier, epoch), (
                query_tier,
                epoch,
            )


def test_is_tier_at_batch_byte_stable(app):
    """Byte-stable output on the same input: two calls return the
    same list. Guards against a stray non-deterministic path (e.g.
    dict iteration order leaking into row shape)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, True, "nope", now, None, now + 3600]
    first = app.lic.is_tier_at_batch("pro", epochs)
    second = app.lic.is_tier_at_batch("pro", epochs)
    assert first == second


def test_is_tier_at_batch_never_raises(app, monkeypatch):
    """If :func:`is_tier_at` blows up under a batch row, the row
    collapses to ``is_tier=False`` rather than crashing the batch."""
    def _boom(_tier, _epoch):
        raise RuntimeError("simulated corruption")

    monkeypatch.setattr(app.lic, "is_tier_at", _boom)
    rows = app.lic.is_tier_at_batch("pro", [int(time.time())])
    assert rows == [{"epoch": int(time.time()), "is_tier": False}] or (
        len(rows) == 1 and rows[0]["is_tier"] is False
    )


# -- GET /api/license/is-tier-at ----------------------------------------------


def test_api_is_tier_at_no_license(app):
    """No license file on disk -> ``is_tier_at=false``, current-time
    reference fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-tier-at?tier=pro&epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["is_tier_at"] is False
    assert body["tier_at"] is None
    assert body["requested_tier"] == "pro"
    assert body["requested_epoch"] == now
    assert body["tier"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_api_is_tier_at_active_key_now(app):
    """Active key, matching tier at "now" -> ``is_tier_at=true``,
    snapshot fields intact."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-tier-at?tier=pro&epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["is_tier_at"] is True
    assert body["tier_at"] == "pro"
    assert body["tier"] == "pro"
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_is_tier_at_missing_epoch_false(app):
    """Missing / non-integer / bool ``epoch`` -> ``is_tier_at=false``
    and ``requested_epoch=null`` so a caller cannot silently mis-gate
    on a typo. HTTP status stays 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as client:
        for qs in ("?tier=pro", "?tier=pro&epoch=", "?tier=pro&epoch=nope"):
            rv = client.get(f"/api/license/is-tier-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["is_tier_at"] is False, qs
            assert body["requested_epoch"] is None, qs


def test_api_is_tier_at_missing_tier_false(app):
    """Missing / empty ``tier`` -> ``is_tier_at=false`` and
    ``requested_tier=""`` so a caller cannot silently claim "is on
    tier empty-string". HTTP 200 (never 4xx)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for qs in (f"?epoch={now}", f"?tier=&epoch={now}", f"?tier=   &epoch={now}"):
            rv = client.get(f"/api/license/is-tier-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["is_tier_at"] is False, qs
            assert body["requested_tier"] == "", qs


def test_api_is_tier_at_future_after_expiry(app):
    """Future perspective past ``exp`` on an active key ->
    ``is_tier_at=false`` even though ``tier`` (current-time) still
    surfaces the tier."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-tier-at?tier=pro&epoch={epoch}")
    body = rv.get_json()
    assert body["is_tier_at"] is False
    assert body["tier_at"] is None
    assert body["tier"] == "pro"


def test_api_is_tier_at_invalid_signature(app):
    """Bogus-signature file -> ``is_tier_at=false``. ``has_license=true``
    (a file exists) but ``valid=false``. Time-independent."""
    _write_bogus(app)
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at?tier=pro&epoch={int(time.time())}"
        )
    body = rv.get_json()
    assert body["is_tier_at"] is False
    assert body["tier_at"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_is_tier_at_case_insensitive_query(app):
    """Query ``tier`` is normalised the same way the scalar
    normalises it -- ``"Pro"`` matches ``"pro"``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for query in ("Pro", "pro", "PRO"):
            rv = client.get(f"/api/license/is-tier-at?tier={query}&epoch={now}")
            body = rv.get_json()
            assert body["is_tier_at"] is True, query
            assert body["requested_tier"] == "pro", query


def test_api_is_tier_at_parity_with_python_scalar(app):
    """The endpoint must return exactly what
    :func:`clawmetry.license.is_tier_at` would return for the same
    (tier, epoch)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 5 * 86400, now + 40 * 86400]
    tiers = ["pro", "enterprise", "trial"]
    with app.app.test_client() as client:
        for t in tiers:
            for e in epochs:
                rv = client.get(f"/api/license/is-tier-at?tier={t}&epoch={e}")
                body = rv.get_json()
                assert body["is_tier_at"] == app.lic.is_tier_at(t, e), (t, e)


def test_api_is_tier_at_agrees_with_is_tier_at_now(app):
    """At ``epoch=now``, the ``is_tier_at`` field must byte-equal the
    ``is_tier`` field returned by ``/api/license/is-tier`` (the
    current-time predicate endpoint). Both derive from the same signed
    claim -- a UI binding both cannot catch them disagreeing at the
    boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_now = client.get("/api/license/is-tier?tier=pro").get_json()
        rv_at = client.get(f"/api/license/is-tier-at?tier=pro&epoch={now}").get_json()
    assert rv_at["is_tier_at"] == rv_now["is_tier"]


def test_api_is_tier_at_shared_snapshot_with_tier_at(app):
    """The current-time reference fields (``tier`` / ``expires_at`` /
    ``has_license`` / ``valid``) must byte-equal the fields returned
    by ``/api/license/tier-at`` for the same install -- both share
    :func:`_license_tier_at_snapshot` so a UI binding both cannot
    catch them disagreeing on the current-time reference."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_pred = client.get(
            f"/api/license/is-tier-at?tier=pro&epoch={now}"
        ).get_json()
        rv_scalar = client.get(f"/api/license/tier-at?epoch={now}").get_json()
    for field in ("tier", "expires_at", "has_license", "valid"):
        assert rv_pred[field] == rv_scalar[field], field


# -- GET /api/license/is-tier-at-batch ----------------------------------------


def test_api_is_tier_at_batch_missing_epochs_400(app):
    """Missing / blank / only-commas ``epochs=`` -> ``400 missing
    epochs`` (matches the sibling ``/api/license/*-at-batch``
    endpoints)."""
    with app.app.test_client() as client:
        for qs in ("?tier=pro", "?tier=pro&epochs=", "?tier=pro&epochs=,,"):
            rv = client.get(f"/api/license/is-tier-at-batch{qs}")
            assert rv.status_code == 400, qs
            assert rv.get_json() == {"error": "missing epochs"}


def test_api_is_tier_at_batch_missing_tier_all_false(app):
    """Missing / empty ``tier`` -> every row ``is_tier=false``,
    HTTP 200 (matches the scalar). A stale UI shouldn't have the whole
    batch hidden behind a typo."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for qs in (f"?epochs={now},{now + 3600}", f"?tier=&epochs={now},{now + 3600}"):
            rv = client.get(f"/api/license/is-tier-at-batch{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["count"] == 2
            assert body["requested_tier"] == "", qs
            assert [r["is_tier"] for r in body["rows"]] == [False, False]


def test_api_is_tier_at_batch_no_license(app):
    """No license file on disk -> every row ``is_tier=false``.
    Reference fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs={now},{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "is_tier_at"
    assert body["count"] == 2
    assert body["requested_tier"] == "pro"
    assert [r["is_tier"] for r in body["rows"]] == [False, False]
    assert body["tier"] is None
    assert body["has_license"] is False


def test_api_is_tier_at_batch_active_flips_per_row(app):
    """Active key: rows before ``exp`` -> ``true``; rows after ->
    ``false``. Batch preserves per-row ordering."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/is-tier-at-batch?tier=pro&epochs={qs}")
    body = rv.get_json()
    assert body["count"] == 4
    assert [r["is_tier"] for r in body["rows"]] == [True, True, False, False]
    assert [r["epoch"] for r in body["rows"]] == epochs
    assert body["tier"] == "pro"
    assert body["valid"] is True


def test_api_is_tier_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with ``/api/license/is-tier-at?tier=<X>&epoch=<n>``
    -- the batch cannot silently drift from the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 5 * 86400, now, now + 3 * 86400, now + 40 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv_batch = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs={qs}"
        )
        rows = rv_batch.get_json()["rows"]
        for row, epoch in zip(rows, epochs):
            rv_scalar = client.get(
                f"/api/license/is-tier-at?tier=pro&epoch={epoch}"
            )
            assert row["is_tier"] == rv_scalar.get_json()["is_tier_at"], epoch


def test_api_is_tier_at_batch_perpetual_key(app):
    """Perpetual key -> every row ``true``."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs=0,{now},2000000000"
        )
    body = rv.get_json()
    assert [r["is_tier"] for r in body["rows"]] == [True, True, True]
    assert body["valid"] is True


def test_api_is_tier_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``false`` (time-independent)."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs=0,{now},2000000000"
        )
    body = rv.get_json()
    assert [r["is_tier"] for r in body["rows"]] == [False, False, False]
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_is_tier_at_batch_bad_tokens_collapse_per_row(app):
    """Bad tokens (non-numeric) don't 400 the batch -- they collapse
    to ``is_tier=false`` rows so a caller can identify the offending
    entry."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs={now},nope,{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["count"] == 3
    good = [r for r in body["rows"] if r["is_tier"] is True]
    bad = [r for r in body["rows"] if r["is_tier"] is False]
    assert len(good) == 2 and len(bad) == 1


def test_api_is_tier_at_batch_shared_snapshot_agreement(app):
    """The current-time reference fields on the batch response must
    byte-equal the sibling ``/api/license/tier-at-batch`` fields for
    the same install -- both share :func:`_license_tier_at_snapshot`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_pred = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs={now}"
        ).get_json()
        rv_scalar = client.get(
            f"/api/license/tier-at-batch?epochs={now}"
        ).get_json()
    for field in ("tier", "expires_at", "has_license", "valid"):
        assert rv_pred[field] == rv_scalar[field], field


def test_api_is_tier_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order --
    matches the underlying batch helper."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=pro&epochs={now},{now},{now + 10},{now}"
        )
    body = rv.get_json()
    assert [r["epoch"] for r in body["rows"]] == [now, now + 10]


def test_api_is_tier_at_batch_case_insensitive_query(app):
    """Query ``tier`` is normalised the same way the scalar
    normalises it -- ``"Pro"`` matches ``"pro"`` across every row."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=%20%20PRO%20%20&epochs={now},{now + 3600}"
        )
    body = rv.get_json()
    assert body["requested_tier"] == "pro"
    assert [r["is_tier"] for r in body["rows"]] == [True, True]


def test_api_is_tier_at_batch_wrong_tier_all_false(app):
    """A tier that doesn't match the installed key -> every row
    ``false`` even on an otherwise-active install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/is-tier-at-batch?tier=enterprise&epochs={now},{now + 3600}"
        )
    body = rv.get_json()
    assert [r["is_tier"] for r in body["rows"]] == [False, False]
