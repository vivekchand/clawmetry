"""Tests for :func:`clawmetry.license.is_subject_at_batch` and the paired
``GET /api/license/is-subject-at-batch`` endpoint.

Shared-``subject`` batch sibling of :func:`clawmetry.license.is_subject_at`
/ ``/api/license/is-subject-at``. Where the scalar folds ONE
``(subject, epoch)`` pair to ONE bool, this batch preserves per-value
rows for a fixed ``subject`` and a sequence of perspective epochs so a
scheduled-audit tile answering "was this node bound to <account> on
each of these audit dates?" hydrates in ONE round-trip instead of
fanning out N scalar calls. Per-row parity with the singular scalar
(both the helper and the HTTP endpoint) is pinned so the batch cannot
silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_state_at_batch.py`` /
``tests/test_license_is_subject_at.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_subject_at.py) --------------------


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


# -- clawmetry.license.is_subject_at_batch() ---------------------------------


def test_is_subject_at_batch_none_epochs_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`is_state_at_batch` / :func:`is_tier_at_batch`."""
    assert app.lic.is_subject_at_batch("acct_test", None) == []


def test_is_subject_at_batch_non_iterable_epochs_returns_empty(app):
    """Non-iterable ``epochs`` -> ``[]`` rather than a crash."""
    assert app.lic.is_subject_at_batch("acct_test", 42) == []


def test_is_subject_at_batch_empty_epochs_returns_empty(app):
    """Empty iterable -> ``[]`` regardless of ``subject``."""
    assert app.lic.is_subject_at_batch("acct_test", []) == []
    assert app.lic.is_subject_at_batch("", ()) == []


def test_is_subject_at_batch_none_subject_all_false(app):
    """``subject=None`` collapses every row to ``is_subject=False``
    while preserving row slots (matches never-mis-gate scalar
    posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(None, [now, now + 86400])
    assert len(rows) == 2
    assert [r["is_subject"] for r in rows] == [False, False]


def test_is_subject_at_batch_empty_subject_all_false(app):
    """Empty ``subject`` collapses every row to ``is_subject=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch("", [now, now + 86400])
    assert [r["is_subject"] for r in rows] == [False, False]


def test_is_subject_at_batch_whitespace_only_subject_all_false(app):
    """A whitespace-only ``subject`` normalises to empty and collapses
    every row to ``False`` (matches the scalar's strip-then-check
    treatment)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch("   ", [now, now + 86400])
    assert [r["is_subject"] for r in rows] == [False, False]


def test_is_subject_at_batch_typo_subject_all_false(app):
    """A typo like ``"acct_test_"`` collapses every row to ``False`` --
    a caller cannot silently mis-gate on a mis-spelled account id."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "acct_test_", [now, now + 86400]
    )
    assert [r["is_subject"] for r in rows] == [False, False]


def test_is_subject_at_batch_unknown_subject_preserves_row_slots(app):
    """No license + non-empty ``subject`` still yields N rows so the
    response length matches N. Row slots must be preserved even when
    every value is False."""
    rows = app.lic.is_subject_at_batch("garbage", [0, 1, 2, 3])
    assert len(rows) == 4
    assert all(r["is_subject"] is False for r in rows)


def test_is_subject_at_batch_matching_subject_active_key(app):
    """Active key + matching subject: every row inside the key's ``exp``
    window fires ``True``; rows at-or-after ``exp`` collapse
    :func:`license_subject_at` to ``None`` so ``is_subject`` is
    ``False``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_subject_at_batch(
        "acct_test", [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    assert [r["is_subject"] for r in rows] == [True, True, False, False]


def test_is_subject_at_batch_non_matching_subject_active_key(app):
    """Active key + non-matching subject: every row inside the ``exp``
    window still fires ``False`` (subject mismatch overrides
    perspective-epoch match)."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_subject_at_batch(
        "someone_else", [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    assert [r["is_subject"] for r in rows] == [False, False, False, False]


def test_is_subject_at_batch_no_license_all_false(app):
    """No license file -> every row fires ``False`` (no subject to
    match against, matching the scalar's ``None`` fallback for
    :func:`license_subject_at`)."""
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "acct_test", [0, now, 2_000_000_000]
    )
    assert [r["is_subject"] for r in rows] == [False, False, False]


def test_is_subject_at_batch_missing_sub_claim_all_false(app):
    """Perpetual key with ``sub`` claim dropped: every row fires
    ``False`` (no subject on the token to match against)."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_sub=True)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "acct_test", [0, now, 2_000_000_000]
    )
    assert [r["is_subject"] for r in rows] == [False, False, False]


def test_is_subject_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_subject_at` -- pin every row and
    every subject combination against the singular helper."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    for subject in ("acct_test", "someone_else", "acct_test_typo"):
        rows = app.lic.is_subject_at_batch(subject, epochs)
        for row, epoch in zip(rows, epochs):
            assert row["is_subject"] == app.lic.is_subject_at(
                subject, epoch
            ), (subject, epoch)


def test_is_subject_at_batch_perpetual_matches(app):
    """Perpetual (no ``exp``) key + matching subject -> every good
    epoch fires ``True`` (perpetual has no expiry cutoff)."""
    _write_perpetual(app, sub="acct_test")
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "acct_test", [0, now, 2_000_000_000]
    )
    assert [r["is_subject"] for r in rows] == [True, True, True]


def test_is_subject_at_batch_perpetual_non_match_all_false(app):
    """Perpetual key + non-matching subject -> every row ``False``
    (subject mismatch is decisive independent of expiry)."""
    _write_perpetual(app, sub="acct_test")
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "someone_else", [0, now, 2_000_000_000]
    )
    assert [r["is_subject"] for r in rows] == [False, False, False]


def test_is_subject_at_batch_invalid_signature_all_false(app):
    """Bogus-signature file -> every row fires ``False`` at every
    epoch. The signature is untrusted, so there is no signed subject to
    trust -- matches the ``is_subject_at`` refusal on that branch."""
    _write_bogus(app)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch(
        "acct_test", [0, now, 2_000_000_000]
    )
    assert [r["is_subject"] for r in rows] == [False, False, False]


def test_is_subject_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the batch pre-
    parser's ``int()`` coercion)."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_subject_at_batch(
        "acct_test", [str(exp - 86400), str(exp - 1)]
    )
    assert [r["is_subject"] for r in rows] == [True, True]


def test_is_subject_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_subject_at_batch(
        "acct_test",
        [exp - 100, exp - 50, exp - 100, str(exp - 50), exp - 25],
    )
    assert [r["epoch"] for r in rows] == [exp - 100, exp - 50, exp - 25]


def test_is_subject_at_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` tokens collapse to
    ``is_subject=False`` (matches the scalar's rejection). Row still
    keeps its slot so output length matches N."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    rows = app.lic.is_subject_at_batch(
        "acct_test", [True, False, None, "garbage", ""]
    )
    # Each bad token keeps its own bucket (matches _license_epoch_batch_keys
    # semantics -- empty and None are distinguished by id()).
    assert len(rows) == 5
    assert all(r["is_subject"] is False for r in rows)


def test_is_subject_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``is_subject=False``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_subject_at_batch(
        "acct_test", [exp - 1, "garbage", exp, exp + 1]
    )
    # exp - 1 (active) -> True; garbage -> False; exp / exp+1 (expired) -> False
    assert [r["is_subject"] for r in rows] == [True, False, False, False]


def test_is_subject_at_batch_subject_case_insensitive(app):
    """``subject`` is normalised case-insensitively after strip,
    matching the scalar's ``.strip().lower()`` treatment. A stored
    ``"Acct_Test"`` matches a queried ``"acct_test"`` and vice
    versa."""
    tok = app.lic._encode_token(
        _payload(sub="Acct_Test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    for variant in ("acct_test", "ACCT_TEST", "  Acct_Test  ", "aCcT_tEsT"):
        rows = app.lic.is_subject_at_batch(variant, [exp - 86400])
        assert [r["is_subject"] for r in rows] == [True], variant


def test_is_subject_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`is_subject_at` ->
    ``is_subject=False`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_subject, _epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_subject_at", _boom)
    rows = _lic.is_subject_at_batch(
        "acct_test", [1_700_000_000, 1_800_000_000]
    )
    assert [r["is_subject"] for r in rows] == [False, False]
    assert len(rows) == 2


def test_is_subject_at_batch_boundary_agrees_with_is_subject(app):
    """At ``epoch = now``, the batch must agree with :func:`is_subject`
    for the same install and the same requested ``subject``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    for subject in ("acct_test", "someone_else", "ACCT_TEST"):
        rows = app.lic.is_subject_at_batch(subject, [now])
        assert rows[0]["is_subject"] == app.lic.is_subject(subject), subject


def test_is_subject_at_batch_row_shape_matches_family(app):
    """Row shape mirrors :func:`is_state_at_batch` /
    :func:`is_tier_at_batch`: exactly two keys per row (``epoch`` +
    ``is_subject``). A caller assembling an audit timeline can zip
    the responses index-for-index."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_subject_at_batch("acct_test", [now])
    assert len(rows) == 1
    assert set(rows[0].keys()) == {"epoch", "is_subject"}


def test_is_subject_at_batch_bad_epoch_token_shape(app):
    """Bad-epoch rows preserve the raw token in ``epoch`` (as a string)
    -- mirrors :func:`is_state_at_batch` / :func:`is_tier_at_batch` so
    callers can identify which input token collapsed."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    rows = app.lic.is_subject_at_batch("acct_test", ["garbage"])
    assert len(rows) == 1
    assert rows[0]["epoch"] == "garbage"
    assert rows[0]["is_subject"] is False


# -- GET /api/license/is-subject-at-batch ------------------------------------


def test_endpoint_is_subject_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-subject-at-batch?subject=acct_test")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_is_subject_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get(
            "/api/license/is-subject-at-batch?subject=acct_test&epochs="
        )
        resp2 = c.get(
            "/api/license/is-subject-at-batch?subject=acct_test&epochs=,,,"
        )
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_is_subject_at_batch_missing_subject_degrades_not_400(app):
    """``?subject=`` absent (with valid ``?epochs=``) does NOT 4xx --
    every row collapses to ``is_subject=false`` per the shared-``subject``
    posture. A stale UI shouldn't hide the whole batch behind a typo."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-subject-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_subject_at"
    assert data["count"] == 1
    assert data["requested_subject"] == ""
    assert data["rows"][0]["is_subject"] is False


def test_endpoint_is_subject_at_batch_no_license(app):
    """No license file -> every row ``False``, HTTP 200, current-time
    snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={now},0"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_subject_at"
    assert data["requested_subject"] == "acct_test"
    assert data["count"] == 2
    assert [r["is_subject"] for r in data["rows"]] == [False, False]
    assert data["subject"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_is_subject_at_batch_active_key_matching(app):
    """Active key + matching subject: rows inside the ``exp`` window
    fire ``True``; rows at-or-after ``exp`` fire ``False``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(
        str(e) for e in [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={csv}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_subject_at"
    assert data["requested_subject"] == "acct_test"
    assert data["count"] == 4
    assert [r["is_subject"] for r in data["rows"]] == [
        True,
        True,
        False,
        False,
    ]
    assert data["subject"] == "acct_test"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp


def test_endpoint_is_subject_at_batch_active_key_non_matching(app):
    """Active key + non-matching subject: every row ``False`` regardless
    of position in the ``exp`` window."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp - 10 * 86400, exp - 1, exp, exp + 1])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=someone_else&epochs={csv}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_subject"] == "someone_else"
    assert [r["is_subject"] for r in data["rows"]] == [
        False,
        False,
        False,
        False,
    ]
    # Current-time snapshot still reflects the real install.
    assert data["subject"] == "acct_test"
    assert data["has_license"] is True


def test_endpoint_is_subject_at_batch_subject_case_normalised_in_echo(app):
    """``requested_subject`` is normalised (stripped + lowered) in the
    echo field, matching the scalar endpoint's echo shape."""
    tok = app.lic._encode_token(
        _payload(sub="Acct_Test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=%20Acct_Test%20&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_subject"] == "acct_test"
    assert data["rows"][0]["is_subject"] is True


def test_endpoint_is_subject_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with the singular
    ``/api/license/is-subject-at?subject=<X>&epoch=<n>`` endpoint --
    pin every row and every subject combination against the scalar
    endpoint."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        for subject in ("acct_test", "someone_else", "acct_test_typo"):
            batch = c.get(
                f"/api/license/is-subject-at-batch?subject={subject}&epochs={csv}"
            ).get_json()
            for row, epoch in zip(batch["rows"], epochs):
                scalar = c.get(
                    f"/api/license/is-subject-at?subject={subject}&epoch={epoch}"
                ).get_json()
                assert row["is_subject"] == scalar["is_subject_at"], (
                    subject,
                    epoch,
                )


def test_endpoint_is_subject_at_batch_bad_tokens_collapse_to_false(app):
    """Bad tokens -> ``is_subject=false`` (never-mis-gate posture).
    Good rows still resolve alongside."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs=garbage,{exp - 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["is_subject"] for r in data["rows"]] == [False, True]


def test_endpoint_is_subject_at_batch_unknown_subject_all_false(app):
    """A typo like ``?subject=acct_test_`` collapses every row to
    ``False`` -- deliberately open-ended but never fuzzy-matched."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test_&epochs={now},{now + 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_subject"] == "acct_test_"
    assert [r["is_subject"] for r in data["rows"]] == [False, False]


def test_endpoint_is_subject_at_batch_perpetual_matching(app):
    """Perpetual key + matching subject -> every row ``True``; the
    current-time snapshot fields still reflect a valid install."""
    _write_perpetual(app, sub="acct_test")
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs=0,{now},2000000000"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["is_subject"] for r in data["rows"]] == [True, True, True]
    assert data["has_license"] is True
    assert data["expires_at"] is None


def test_endpoint_is_subject_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={exp - 100},{exp - 50},{exp - 100},{exp - 50}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [exp - 100, exp - 50]


def test_endpoint_is_subject_at_batch_bogus_signature_all_false(app):
    """Bogus-signature file -> every row ``False``. Signature is
    untrusted, so no signed subject to trust -- matches the scalar."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs=0,{now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["is_subject"] for r in data["rows"]] == [False, False]
    # Snapshot: file exists so has_license=True, but valid=False.
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_is_subject_at_batch_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the OSS-free snapshot fallback + honest
    per-row derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_subject_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["subject"] is None
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


def test_endpoint_is_subject_at_batch_derive_error_never_5xxs(
    app, monkeypatch
):
    """Even if the per-row derivation blows up mid-request, the
    endpoint still returns HTTP 200 with an empty rows envelope.
    Never-5xx posture is inherited from the surrounding
    ``/api/license/*-at-batch`` family."""
    import clawmetry.license as _lic

    def _boom(_subject, _epochs):
        raise RuntimeError("simulated blowup")

    monkeypatch.setattr(_lic, "is_subject_at_batch", _boom)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_subject_at"
    assert data["rows"] == []
    assert data["count"] == 0


def test_endpoint_is_subject_at_batch_envelope_keys(app):
    """Envelope carries exactly the documented keys: ``kind``,
    ``count``, ``requested_subject``, ``rows``, ``subject``,
    ``expires_at``, ``has_license``, ``valid``. A UI cannot silently
    depend on a spurious sibling field this endpoint doesn't emit."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == {
        "kind",
        "count",
        "requested_subject",
        "rows",
        "subject",
        "expires_at",
        "has_license",
        "valid",
    }


# -- cross-endpoint consistency: shared snapshot + row alignment -------------


def test_endpoint_is_subject_at_batch_shared_snapshot_fields_agree_with_siblings(
    app,
):
    """Shares the current-time snapshot fields (``subject`` /
    ``expires_at`` / ``has_license`` / ``valid``) with the sibling
    ``/api/license/subject-at{,-batch}`` and ``/api/license/is-subject-at``
    endpoints. A UI binding several for the same install must not catch
    them disagreeing on those fields."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        s = c.get(f"/api/license/subject-at?epoch={now}").get_json()
        sb = c.get(
            f"/api/license/subject-at-batch?epochs={now}"
        ).get_json()
        gate = c.get(
            f"/api/license/is-subject-at?subject=acct_test&epoch={now}"
        ).get_json()
        batch = c.get(
            f"/api/license/is-subject-at-batch?subject=acct_test&epochs={now}"
        ).get_json()
    for key in ("subject", "expires_at", "has_license", "valid"):
        assert s[key] == sb[key] == gate[key] == batch[key], key


def test_endpoint_is_subject_at_batch_rows_zip_with_subject_at_batch(app):
    """``/api/license/is-subject-at-batch`` row order MUST align with
    ``/api/license/subject-at-batch`` on the same ``?epochs=`` CSV so
    a caller can zip both responses index-for-index and cross-check
    (``is_subject`` iff per-row ``subject`` normalised equals
    ``requested_subject``)."""
    tok = app.lic._encode_token(
        _payload(sub="acct_test", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 5 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        subject_rows = c.get(
            f"/api/license/subject-at-batch?epochs={csv}"
        ).get_json()["rows"]
        for target in ("acct_test", "someone_else"):
            match_rows = c.get(
                f"/api/license/is-subject-at-batch?subject={target}&epochs={csv}"
            ).get_json()["rows"]
            for subj_row, match_row in zip(subject_rows, match_rows):
                assert subj_row["epoch"] == match_row["epoch"]
                stored = subj_row.get("subject")
                normalised = (
                    stored.strip().lower() if isinstance(stored, str) else None
                )
                assert match_row["is_subject"] == (
                    normalised is not None and normalised == target.lower()
                ), (target, subj_row["epoch"])
