"""Tests for :func:`clawmetry.license.license_age_days_at_batch` and
the paired ``GET /api/license/age-days-at-batch`` endpoint.

Per-value axis batch sibling of
:func:`clawmetry.license.license_age_days_at` /
``/api/license/age-days-at``. Fills the ``_at_batch`` slot on the
``iat``-derived license-age axis alongside the ``exp``-derived
``/api/license/days-until-expiry-at-batch``, so a scheduled-audit tile
that wants to plot license age across a sequence of perspective dates
can hydrate the whole column in ONE round-trip. Per-row parity with
the singular scalar (both the helper and the HTTP endpoint) is pinned
so the batch cannot silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_expiring_at_batch.py`` /
``tests/test_license_state_at_batch.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror the sibling _at_batch tests) --------------------


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400, drop_exp=False, drop_iat=False):
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
    if drop_iat:
        p.pop("iat", None)
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


def _write_perpetual(app):
    import os

    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_no_iat(app):
    """Write a signature-valid token whose payload has no ``iat`` claim.
    ``activate()`` refuses this shape, so bypass it and write directly."""
    import os

    tok = app.lic._encode_token(_payload(drop_iat=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_age_days_at_batch() -----------------------


def test_license_age_days_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches the
    ``_at_batch`` siblings."""
    assert app.lic.license_age_days_at_batch(None) == []


def test_license_age_days_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.license_age_days_at_batch(42) == []


def test_license_age_days_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.license_age_days_at_batch([]) == []
    assert app.lic.license_age_days_at_batch(()) == []


def test_license_age_days_at_batch_no_license(app):
    """No license file -> every row ``days=None`` (nothing to derive an
    age from). Time-independent, matches the scalar."""
    rows = app.lic.license_age_days_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["days"] for r in rows] == [None, None, None]


def test_license_age_days_at_batch_active_key_signed_ages(app):
    """Active key: rows carry a signed int day-count against ``iat``.
    Zero on the ``iat`` second; positive N days after; negative N days
    before -- perspective-epoch semantics preserved per row."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    rows = app.lic.license_age_days_at_batch(
        [iat, iat + 5 * 86400, iat - 7 * 86400, iat + 86400]
    )
    assert [r["days"] for r in rows] == [0, 5, -7, 1]


def test_license_age_days_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`license_age_days_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    epochs = [iat - 10 * 86400, iat - 1, iat, iat + 1, iat + 60 * 86400]
    rows = app.lic.license_age_days_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["days"] == app.lic.license_age_days_at(epoch), epoch


def test_license_age_days_at_batch_perpetual_still_ages(app):
    """Perpetual (no ``exp``) key still carries ``iat`` -- rows must
    surface a real age. Mirrors :func:`license_age_days_at`, which is
    deliberately lenient on expiry."""
    _write_perpetual(app)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    rows = app.lic.license_age_days_at_batch(
        [iat, iat + 30 * 86400, iat - 3 * 86400]
    )
    assert [r["days"] for r in rows] == [0, 30, -3]


def test_license_age_days_at_batch_invalid_signature(app):
    """Bogus-signature file -> ``days=None`` at every epoch (an
    unsigned body is untrusted whatever the perspective; the scalar
    refuses to trust the payload's ``iat``)."""
    _write_bogus(app)
    rows = app.lic.license_age_days_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["days"] for r in rows] == [None, None, None]


def test_license_age_days_at_batch_missing_iat_returns_none(app):
    """Signature-valid payload with no ``iat`` claim -> ``days=None`` at
    every epoch (nothing to derive the age against). Matches the
    scalar's fallback."""
    _write_no_iat(app)
    rows = app.lic.license_age_days_at_batch([0, int(time.time())])
    assert [r["days"] for r in rows] == [None, None]


def test_license_age_days_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    rows = app.lic.license_age_days_at_batch([str(iat), str(iat + 86400)])
    assert [r["days"] for r in rows] == [0, 1]


def test_license_age_days_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    rows = app.lic.license_age_days_at_batch(
        [iat, iat + 100, iat, str(iat + 100), iat + 200]
    )
    assert [r["epoch"] for r in rows] == [iat, iat + 100, iat + 200]


def test_license_age_days_at_batch_bad_tokens_collapse_to_none(app):
    """``bool`` / non-numeric / ``None`` collapse to ``days=None``
    (matches the scalar's rejection). Row still keeps its slot so
    output length matches N -- each bad input gets its own bucket."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.license_age_days_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["days"] is None for r in rows)


def test_license_age_days_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``days=None``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    rows = app.lic.license_age_days_at_batch([iat + 86400, "garbage", iat - 86400])
    assert [r["days"] for r in rows] == [1, None, -1]


def test_license_age_days_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`license_age_days_at`
    -> ``days=None`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_age_days_at", _boom)
    rows = _lic.license_age_days_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["days"] for r in rows] == [None, None]
    assert len(rows) == 2


# -- GET /api/license/age-days-at-batch --------------------------------------


def test_endpoint_age_days_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints -- missing input is a real
    error, unlike bad input)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_age_days_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/age-days-at-batch?epochs=")
        resp2 = c.get("/api/license/age-days-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_age_days_at_batch_no_license(app):
    """No license file -> every row ``days=None``, HTTP 200, snapshot
    fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at-batch?epochs={now},0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "license_age_days_at"
    assert data["count"] == 2
    assert [r["days"] for r in data["rows"]] == [None, None]
    assert data["issued_at"] is None
    assert data["age_days"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_age_days_at_batch_active_key_signed_rows(app):
    """Active key: rows carry signed int day-counts. Snapshot reflects
    current install state."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    csv = ",".join(str(e) for e in [iat, iat + 3 * 86400, iat - 2 * 86400])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "license_age_days_at"
    assert data["count"] == 3
    assert [r["days"] for r in data["rows"]] == [0, 3, -2]
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["issued_at"] == iat


def test_endpoint_age_days_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/age-days-at?epoch=<n>`` endpoint -- the batch
    cannot silently drift from the scalar endpoint. Pin every row."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    epochs = [iat - 10 * 86400, iat - 1, iat, iat + 1, iat + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/age-days-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/age-days-at?epoch={epoch}"
            ).get_json()
            assert row["days"] == scalar["age_days"], epoch


def test_endpoint_age_days_at_batch_bad_tokens_collapse_to_null(app):
    """Bad tokens don't fail the whole batch. They slot in with
    ``days=null`` (the never-mis-count posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/age-days-at-batch?epochs=garbage,{iat + 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["days"] for r in data["rows"]] == [None, 1]


def test_endpoint_age_days_at_batch_perpetual_still_ages(app):
    """Perpetual key still carries ``iat`` -- rows must surface a real
    age. Snapshot shows a valid install."""
    _write_perpetual(app)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    csv = ",".join(str(e) for e in [iat, iat + 30 * 86400, iat - 3 * 86400])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["days"] for r in data["rows"]] == [0, 30, -3]
    assert data["has_license"] is True
    assert data["issued_at"] == iat


def test_endpoint_age_days_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/age-days-at-batch?epochs={iat},{iat + 100},{iat},{iat + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [iat, iat + 100]


def test_endpoint_age_days_at_batch_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the OSS-free snapshot fallback + honest
    per-row derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_issued_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/age-days-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["issued_at"] is None
    assert data["age_days"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# -- cross-endpoint consistency: pairs with days-until-expiry-at-batch -----


def test_endpoint_age_days_at_batch_rows_zip_with_days_until_expiry(app):
    """The ``iat``-derived age batch and the ``exp``-derived days-
    remaining batch admit the same input schema and emit rows in the
    same order, so a caller can zip them index-for-index to render
    "N days old, M days remaining" per perspective."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    iat = int(info["issued_at"])
    epochs = [iat, iat + 5 * 86400, iat + 10 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        age = c.get(f"/api/license/age-days-at-batch?epochs={csv}").get_json()
        rem = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={csv}"
        ).get_json()
    assert age["count"] == rem["count"] == 3
    for i, epoch in enumerate(epochs):
        assert age["rows"][i]["epoch"] == rem["rows"][i]["epoch"] == epoch
        # Age counts up from iat; days-remaining counts down to exp.
        # Their sum is a constant per install (the license's term in
        # days), give or take one from floor-division rounding.
        assert age["rows"][i]["days"] + rem["rows"][i]["days"] in (29, 30, 31)


def test_endpoint_age_days_at_batch_shared_snapshot_fields_agree_with_scalar(app):
    """Shares the snapshot fields (``issued_at`` / ``age_days`` /
    ``has_license`` / ``valid``) with the singular
    ``/api/license/age-days-at`` endpoint. A UI binding both for the
    same install must not catch them disagreeing on those fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        scalar = c.get(f"/api/license/age-days-at?epoch={now}").get_json()
        batch = c.get(f"/api/license/age-days-at-batch?epochs={now}").get_json()
    for key in ("issued_at", "has_license", "valid"):
        assert scalar[key] == batch[key], key
