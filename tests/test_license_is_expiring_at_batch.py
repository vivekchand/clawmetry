"""Tests for :func:`clawmetry.license.is_expiring_at_batch` and the
paired ``GET /api/license/is-expiring-at-batch`` endpoint.

Per-value axis batch sibling of :func:`clawmetry.license.is_expiring_at`
/ ``/api/license/is-expiring-at``. Rounds out the expiry axis alongside
the recently-shipped ``state-at-batch`` / ``is-expired-at-batch`` /
``days-until-expiry-at-batch`` trio: given a list of candidate ``exp``
values a renewal-reminder UI has cached, ONE round-trip answers "does
the on-disk key still match each of them?" instead of N calls to the
scalar. Per-row parity with the singular scalar (both the helper and
the HTTP endpoint) is pinned so the batch cannot silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_state_at_batch.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_state_at_batch.py) ------------------


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


def _write_key_direct(app, exp_delta):
    """Bypass activate() (which refuses expired tokens) and write a token
    directly to the license file. Simulates a license that expired AFTER
    it was installed."""
    import os

    tok = app.lic._encode_token(_payload(exp_delta=exp_delta), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_perpetual(app):
    import os

    tok = app.lic._encode_token(_payload(drop_exp=True), app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    import os

    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.is_expiring_at_batch() --------------------------------


def test_is_expiring_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`license_state_at_batch` / :func:`is_expired_at_batch`."""
    assert app.lic.is_expiring_at_batch(None) == []


def test_is_expiring_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.is_expiring_at_batch(42) == []


def test_is_expiring_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.is_expiring_at_batch([]) == []
    assert app.lic.is_expiring_at_batch(()) == []


def test_is_expiring_at_batch_no_license(app):
    """No license file on disk -> every row ``is_expiring=False``
    (nothing to compare against). Time-independent, matches the
    never-mis-gate scalar posture."""
    rows = app.lic.is_expiring_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["is_expiring"] for r in rows] == [False, False, False]


def test_is_expiring_at_batch_active_key_only_exact_match_fires(app):
    """Active key: only the row whose ``epoch`` equals the on-disk
    ``exp`` fires ``True``. Every other perspective -> ``False`` (a
    mismatch means the on-disk key was renewed to a different date)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expiring_at_batch([exp - 1, exp, exp + 1, exp + 86400])
    assert [r["is_expiring"] for r in rows] == [False, True, False, False]


def test_is_expiring_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_expiring_at` -- the batch cannot
    silently drift from the scalar. Pin every row against the singular
    helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    rows = app.lic.is_expiring_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["is_expiring"] == app.lic.is_expiring_at(epoch), epoch


def test_is_expiring_at_batch_perpetual_never_fires(app):
    """Perpetual (no ``exp``) key -> ``is_expiring=False`` at every
    epoch (no claim to compare against). Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.is_expiring_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["is_expiring"] for r in rows] == [False, False, False]


def test_is_expiring_at_batch_invalid_signature(app):
    """Bogus-signature file -> ``is_expiring=False`` at every epoch (an
    unsigned body is untrusted whatever the perspective; the scalar
    refuses to trust the payload's ``exp``)."""
    _write_bogus(app)
    rows = app.lic.is_expiring_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["is_expiring"] for r in rows] == [False, False, False]


def test_is_expiring_at_batch_expired_key_never_fires(app):
    """A signature-valid but already-expired key -> ``is_expiring=False``
    at every epoch (including the epoch equal to its stored ``exp``).
    Mirrors :func:`is_expiring_at`, which is deliberately strict on
    validity: a predicate that fired ``True`` on a lapsed key would
    push callers to gate renewal UI on a value that no longer implies
    entitlement."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expiring_at_batch(
        [exp, exp - 1, exp + 1, int(time.time())]
    )
    assert [r["is_expiring"] for r in rows] == [False, False, False, False]


def test_is_expiring_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expiring_at_batch([str(exp), str(exp + 1)])
    assert [r["is_expiring"] for r in rows] == [True, False]


def test_is_expiring_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expiring_at_batch(
        [exp, exp + 100, exp, str(exp + 100), exp + 200]
    )
    assert [r["epoch"] for r in rows] == [exp, exp + 100, exp + 200]


def test_is_expiring_at_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` collapse to
    ``is_expiring=False`` (matches the scalar's rejection). Row still
    keeps its slot so output length matches N -- each bad input gets
    its own bucket."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_expiring_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["is_expiring"] is False for r in rows)


def test_is_expiring_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``is_expiring=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expiring_at_batch([exp, "garbage", exp + 60 * 86400])
    assert [r["is_expiring"] for r in rows] == [True, False, False]


def test_is_expiring_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`is_expiring_at` ->
    ``is_expiring=False`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_expiring_at", _boom)
    rows = _lic.is_expiring_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["is_expiring"] for r in rows] == [False, False]
    assert len(rows) == 2


# -- GET /api/license/is-expiring-at-batch -----------------------------------


def test_endpoint_is_expiring_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints -- missing input is a real
    error, unlike bad input)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_is_expiring_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expiring-at-batch?epochs=")
        resp2 = c.get("/api/license/is-expiring-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_is_expiring_at_batch_no_license(app):
    """No license file -> every row ``is_expiring=False``, HTTP 200,
    current-time snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at-batch?epochs={now},0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_expiring_at"
    assert data["count"] == 2
    assert [r["is_expiring"] for r in data["rows"]] == [False, False]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_is_expiring_at_batch_active_key_exact_match(app):
    """Active key: only the row whose ``epoch`` equals the on-disk
    ``exp`` fires ``True``. Snapshot reflects current install state."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp - 1, exp, exp + 1])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_expiring_at"
    assert data["count"] == 3
    assert [r["is_expiring"] for r in data["rows"]] == [False, True, False]
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp


def test_endpoint_is_expiring_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/is-expiring-at?epoch=<n>`` endpoint -- the batch
    cannot silently drift from the scalar endpoint. Pin every row."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/is-expiring-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/is-expiring-at?epoch={epoch}"
            ).get_json()
            assert row["is_expiring"] == scalar["is_expiring_at"], epoch


def test_endpoint_is_expiring_at_batch_bad_tokens_collapse_to_false(app):
    """Bad tokens don't fail the whole batch. They slot in with
    ``is_expiring=False`` (the never-mis-gate posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-expiring-at-batch?epochs=garbage,{exp}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["is_expiring"] for r in data["rows"]] == [False, True]


def test_endpoint_is_expiring_at_batch_perpetual_never_fires(app):
    """Perpetual key -> every row ``is_expiring=False``, but the
    current-time snapshot fields still reflect a valid install."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-expiring-at-batch?epochs=0,{now},2000000000"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["is_expiring"] for r in data["rows"]] == [False, False, False]
    assert data["has_license"] is True
    assert data["expires_at"] is None


def test_endpoint_is_expiring_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-expiring-at-batch?epochs={exp},{exp + 100},{exp},{exp + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [exp, exp + 100]


def test_endpoint_is_expiring_at_batch_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the OSS-free snapshot fallback + honest
    per-row derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_state_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expiring-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "no_license"
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


# -- cross-endpoint consistency: shared snapshot + row alignment -------------


def test_endpoint_is_expiring_at_batch_shared_snapshot_fields_agree_with_siblings(app):
    """Shares the current-time snapshot fields (``state`` /
    ``expires_at`` / ``has_license`` / ``valid``) with the existing
    ``/api/license/*-at-batch`` trio. A UI binding several for the
    same install must not catch them disagreeing on those fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        s = c.get(f"/api/license/state-at-batch?epochs={now}").get_json()
        ex = c.get(f"/api/license/is-expired-at-batch?epochs={now}").get_json()
        d = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={now}"
        ).get_json()
        it = c.get(
            f"/api/license/is-expiring-at-batch?epochs={now}"
        ).get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert s[key] == ex[key] == d[key] == it[key], key


def test_endpoint_is_expiring_at_batch_rows_zip_with_siblings(app):
    """All four ``/api/license/*-at-batch`` endpoints admit the same
    input schema (``?epochs=`` CSV) and emit the same row ordering,
    so a caller can zip the responses index-for-index by epoch."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp, exp + 5 * 86400, exp + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        s = c.get(f"/api/license/state-at-batch?epochs={csv}").get_json()
        ex = c.get(f"/api/license/is-expired-at-batch?epochs={csv}").get_json()
        d = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={csv}"
        ).get_json()
        it = c.get(
            f"/api/license/is-expiring-at-batch?epochs={csv}"
        ).get_json()
    assert s["count"] == ex["count"] == d["count"] == it["count"] == 4
    for i, epoch in enumerate(epochs):
        assert (
            s["rows"][i]["epoch"]
            == ex["rows"][i]["epoch"]
            == d["rows"][i]["epoch"]
            == it["rows"][i]["epoch"]
            == epoch
        )
        # Exactly one row -- ``epoch == exp`` -- fires is_expiring
        # (validity is checked NOW, so a currently-valid key fires on
        # the row whose days_until_expiry_at is 0). Every other row is
        # False. Note: license_state_at(exp) is "expired" at the exact
        # boundary because ``exp <= epoch`` flips there -- perspective
        # state and NOW-validity intentionally disagree on the boundary.
        if d["rows"][i]["days"] == 0:
            assert it["rows"][i]["is_expiring"] is True, epoch
        else:
            assert it["rows"][i]["is_expiring"] is False, epoch
