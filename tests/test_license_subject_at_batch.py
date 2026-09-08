"""Tests for the ``clawmetry.license.license_subject_at_batch`` helper
and its paired ``/api/license/subject-at-batch`` HTTP endpoint.

Per-value batch flavour of :func:`clawmetry.license.license_subject_at`
-- fills the ``_at_batch`` slot on the license-subject axis so a
scheduled-audit tile that wants to plot the ``sub`` claim across a
sequence of perspective dates hydrates the whole column in ONE
round-trip instead of fanning out N calls to ``/api/license/subject-at``.
Per-row parity with the singular scalar (both Python-level and
HTTP-level) is pinned so the batch cannot silently drift from the
scalar endpoint.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_subject_at.py`` /
``tests/test_license_state_at_batch.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror tests/test_license_subject_at.py) ----------------


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


# -- clawmetry.license.license_subject_at_batch() ----------------------------


def test_license_subject_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Mirrors the never-raise posture of
    the sibling ``_at_batch`` helpers."""
    assert app.lic.license_subject_at_batch(None) == []


def test_license_subject_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.license_subject_at_batch(42) == []


def test_license_subject_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.license_subject_at_batch([]) == []
    assert app.lic.license_subject_at_batch(()) == []


def test_license_subject_at_batch_no_license(app):
    """No license file on disk -> every row ``subject=None`` regardless
    of epoch. Time-independent, matches the scalar."""
    rows = app.lic.license_subject_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["subject"] for r in rows] == [None, None, None]
    assert [r["epoch"] for r in rows] == [0, int(time.time()), 2_000_000_000]


def test_license_subject_at_batch_active_key_mixed_epochs(app):
    """Active key: perspectives before ``exp`` -> subject string;
    perspectives at/after ``exp`` -> ``None`` (retrospective view of the
    lapsed side). The batch preserves per-row ordering."""
    tok = app.lic._encode_token(
        _payload(sub="acct_active", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    rows = app.lic.license_subject_at_batch(epochs)
    assert [r["subject"] for r in rows] == [
        "acct_active",
        "acct_active",
        None,
        None,
    ]
    assert [r["epoch"] for r in rows] == epochs


def test_license_subject_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`license_subject_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install."""
    tok = app.lic._encode_token(
        _payload(sub="acct_parity", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [
        now - 10 * 86400,
        now,
        now + 5 * 86400,
        now + 40 * 86400,
        now + 200 * 86400,
    ]
    rows = app.lic.license_subject_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["subject"] == app.lic.license_subject_at(epoch), epoch


def test_license_subject_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> every row surfaces the subject
    regardless of perspective. Mirrors the scalar."""
    _write_perpetual(app, sub="acct_forever")
    rows = app.lic.license_subject_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["subject"] for r in rows] == ["acct_forever"] * 3


def test_license_subject_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``None`` (an unsigned body is
    untrusted whatever the perspective; matches the scalar)."""
    _write_bogus(app)
    rows = app.lic.license_subject_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["subject"] for r in rows] == [None, None, None]


def test_license_subject_at_batch_lapsed_key_pre_lapse_epoch(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    subject string (retrospective "who was this licensed to on <date>");
    at "now" -> ``None``. Batch flips per row."""
    _write_key_direct(
        app, exp_delta=-5 * 86400, sub="acct_lapsed"
    )  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.license_subject_at_batch(
        [now - 20 * 86400, now - 3 * 86400, now]
    )
    assert [r["subject"] for r in rows] == ["acct_lapsed", None, None]


def test_license_subject_at_batch_missing_sub_claim(app):
    """Signed payload with no ``sub`` claim -> every row ``None``
    (matches the scalar's `sub`-not-a-string branch)."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_sub=True)
    now = int(time.time())
    rows = app.lic.license_subject_at_batch([now, now + 5 * 86400])
    assert [r["subject"] for r in rows] == [None, None]


def test_license_subject_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(
        _payload(sub="acct_dedup", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_subject_at_batch(
        [now, now + 100, now, str(now + 100), now + 200]
    )
    assert [r["epoch"] for r in rows] == [now, now + 100, now + 200]


def test_license_subject_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(
        _payload(sub="acct_strings", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_subject_at_batch(
        [str(now), str(now + 60 * 86400)]
    )
    assert [r["subject"] for r in rows] == ["acct_strings", None]


def test_license_subject_at_batch_bad_tokens_collapse_to_none(app):
    """``bool`` / non-numeric strings / ``None`` collapse to a
    ``subject=None`` row. Row still keeps its slot (each bad token gets
    its own bucket) so output length still matches N."""
    tok = app.lic._encode_token(
        _payload(sub="acct_bad", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    rows = app.lic.license_subject_at_batch(
        [True, False, None, "garbage", ""]
    )
    assert len(rows) == 5
    assert all(r["subject"] is None for r in rows)


def test_license_subject_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``subject=None``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_mixed", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_subject_at_batch(
        [now, "garbage", now + 60 * 86400]
    )
    assert [r["subject"] for r in rows] == ["acct_mixed", None, None]


def test_license_subject_at_batch_bad_tokens_stringified_in_epoch(app):
    """Bad tokens surface as their stringified form in ``epoch`` so a
    caller can identify the offending entry in the response."""
    tok = app.lic._encode_token(
        _payload(sub="acct_x", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    rows = app.lic.license_subject_at_batch(["garbage", None])
    assert rows[0]["epoch"] == "garbage"
    # ``None`` stringifies to "None" via ``str(None)``.
    assert rows[1]["epoch"] == "None"


def test_license_subject_at_batch_now_row_matches_current_subject(app):
    """When any row's ``epoch`` equals "now", its ``subject`` field
    must byte-equal :func:`license_subject` -- both derive from the
    same signed ``sub`` claim, refuse the invalid-signature branch,
    and use the same ``exp <= cutoff`` boundary."""
    tok = app.lic._encode_token(
        _payload(sub="acct_now_ref", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_subject_at_batch([now])
    assert rows[0]["subject"] == app.lic.license_subject()


def test_license_subject_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`license_subject_at` ->
    ``subject=None`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_subject_at", _boom)
    rows = _lic.license_subject_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["subject"] for r in rows] == [None, None]
    assert len(rows) == 2


def test_license_subject_at_batch_bool_rejected_as_bad_input(app):
    """``bool`` -- an ``int`` subclass -- is explicitly refused so a
    caller who passes ``True`` / ``False`` doesn't silently get a
    "was subject X at epoch 1?" classification. Matches
    :func:`license_subject_at`."""
    tok = app.lic._encode_token(
        _payload(sub="acct_bool", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    rows = app.lic.license_subject_at_batch([True, False])
    assert [r["subject"] for r in rows] == [None, None]
    # Rows still slot in -- each bad token gets its own bucket.
    assert len(rows) == 2


def test_license_subject_at_batch_generator_input(app):
    """Batch admits any iterable, not just ``list`` / ``tuple``.
    Generator input works the same way."""
    tok = app.lic._encode_token(
        _payload(sub="acct_gen", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())

    def _gen():
        yield now
        yield now + 60 * 86400

    rows = app.lic.license_subject_at_batch(_gen())
    assert [r["subject"] for r in rows] == ["acct_gen", None]


# -- GET /api/license/subject-at-batch ---------------------------------------


def test_endpoint_subject_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the sibling
    ``/api/license/*-at-batch`` endpoints -- missing input is a real
    error, unlike bad input)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/subject-at-batch")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data == {"error": "missing epochs"}


def test_endpoint_subject_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/subject-at-batch?epochs=")
        resp2 = c.get("/api/license/subject-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_subject_at_batch_no_license(app):
    """No license file -> every row ``subject=null``, HTTP 200,
    current-time snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/subject-at-batch?epochs={now},0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "license_subject_at"
    assert data["count"] == 2
    assert [r["subject"] for r in data["rows"]] == [None, None]
    assert data["subject"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_subject_at_batch_active_key_mixed_epochs(app):
    """Active key at mixed perspectives -> per-row subjects match the
    scalar. Snapshot reflects current install state."""
    tok = app.lic._encode_token(
        _payload(sub="acct_endpoint", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 60 * 86400]
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/subject-at-batch?epochs={epochs[0]},{epochs[1]}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["subject"] for r in data["rows"]] == ["acct_endpoint", None]
    assert data["subject"] == "acct_endpoint"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert isinstance(data["expires_at"], int)


def test_endpoint_subject_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/subject-at?epoch=<n>`` endpoint -- the batch cannot
    silently drift from the scalar endpoint. Pin every row."""
    tok = app.lic._encode_token(
        _payload(sub="acct_scalar_parity", exp_delta=45 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 5 * 86400, now, now + 30 * 86400, now + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/subject-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/subject-at?epoch={epoch}"
            ).get_json()
            assert row["subject"] == scalar["subject_at"], epoch


def test_endpoint_subject_at_batch_shared_snapshot_agrees_with_scalar(app):
    """Batch envelope's current-time reference fields (``subject`` /
    ``expires_at`` / ``has_license`` / ``valid``) share
    :func:`_license_subject_at_snapshot` with the scalar endpoint --
    a UI binding both cannot catch them disagreeing on the current-time
    reference for the same install."""
    tok = app.lic._encode_token(
        _payload(sub="acct_shared", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/subject-at-batch?epochs={now}"
        ).get_json()
        scalar = c.get(
            f"/api/license/subject-at?epoch={now}"
        ).get_json()
    for key in ("subject", "expires_at", "has_license", "valid"):
        assert batch[key] == scalar[key], key


def test_endpoint_subject_at_batch_bad_tokens_do_not_400(app):
    """Bad tokens don't fail the whole batch -- they slot in with
    ``subject=null``. The 400 is reserved for ``?epochs=`` entirely
    missing / blank."""
    tok = app.lic._encode_token(
        _payload(sub="acct_badtok", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/subject-at-batch?epochs={now},garbage,true,"
            f"{now + 60 * 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 4
    assert [r["subject"] for r in data["rows"]] == [
        "acct_badtok",
        None,
        None,
        None,
    ]


def test_endpoint_subject_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(
        _payload(sub="acct_order", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/subject-at-batch?epochs={now},{now + 100},"
            f"{now},{now + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [now, now + 100]


def test_endpoint_subject_at_batch_perpetual_key(app):
    """Perpetual key -> every row surfaces the subject regardless of
    perspective. Snapshot reports ``has_license=True`` +
    ``expires_at=None``."""
    _write_perpetual(app, sub="acct_perp")
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/subject-at-batch?epochs=0,{now},2000000000"
        )
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["subject"] for r in data["rows"]] == ["acct_perp"] * 3
    assert data["has_license"] is True
    assert data["expires_at"] is None
    assert data["subject"] == "acct_perp"


def test_endpoint_subject_at_batch_bogus_signature_all_none(app):
    """Bogus-signature file -> every row ``subject=null``. Envelope
    snapshot reports ``valid=False`` / ``subject=None`` (matches the
    scalar endpoint on the same install)."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/subject-at-batch?epochs={now},0")
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["subject"] for r in data["rows"]] == [None, None]
    assert data["valid"] is False
    assert data["subject"] is None


def test_endpoint_subject_at_batch_never_5xxs_snapshot_blowup(app, monkeypatch):
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
        resp = c.get(f"/api/license/subject-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["subject"] is None
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


def test_endpoint_subject_at_batch_never_5xxs_derive_blowup(app, monkeypatch):
    """Even if :func:`license_subject_at_batch` itself raises mid-
    request, the endpoint still returns HTTP 200 with an empty rows
    envelope + intact current-time snapshot."""
    import clawmetry.license as _lic

    def _boom(_epochs):
        raise RuntimeError("simulated batch blowup")

    tok = app.lic._encode_token(
        _payload(sub="acct_5xx", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    monkeypatch.setattr(_lic, "license_subject_at_batch", _boom)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/subject-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 0
    assert data["rows"] == []
    # Snapshot still hydrates because it was read BEFORE the derive
    # helper was called.
    assert data["subject"] == "acct_5xx"
    assert data["has_license"] is True
    assert data["valid"] is True


# -- cross-endpoint consistency ----------------------------------------------


def test_endpoint_subject_at_batch_zips_index_for_index_with_tier_at_batch(app):
    """All ``/api/license/*-at-batch`` endpoints admit the same input
    schema (``?epochs=`` CSV) and emit the same row ordering, so a
    caller assembling an audit timeline can zip the responses index-for-
    index by epoch column. Sibling of the same guarantee held by
    ``/api/license/state-at-batch`` / ``.../is-expired-at-batch`` /
    ``.../days-until-expiry-at-batch`` in
    ``tests/test_license_state_at_batch.py``."""
    tok = app.lic._encode_token(
        _payload(sub="acct_zip", exp_delta=30 * 86400), app.priv
    )
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 5 * 86400, now + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        subj = c.get(
            f"/api/license/subject-at-batch?epochs={csv}"
        ).get_json()
        tier = c.get(
            f"/api/license/tier-at-batch?epochs={csv}"
        ).get_json()
        state = c.get(
            f"/api/license/state-at-batch?epochs={csv}"
        ).get_json()
    assert subj["count"] == tier["count"] == state["count"] == 4
    for i, epoch in enumerate(epochs):
        assert (
            subj["rows"][i]["epoch"]
            == tier["rows"][i]["epoch"]
            == state["rows"][i]["epoch"]
            == epoch
        )
        # A row with a non-null tier at ``epoch`` must also carry a
        # non-null subject at the same epoch (both derive from the same
        # signed payload; both refuse the same expired branch).
        if tier["rows"][i]["tier"] is not None:
            assert subj["rows"][i]["subject"] is not None, epoch
        else:
            assert subj["rows"][i]["subject"] is None, epoch
