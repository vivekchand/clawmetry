"""Tests for :func:`clawmetry.license.is_expiring_within_at_batch` and the
paired ``GET /api/license/expiring-within-at-batch`` endpoint.

Per-value axis batch sibling of
:func:`clawmetry.license.is_expiring_within_at` /
``/api/license/expiring-within-at``. Rounds out the renewal-window
axis alongside the existing ``exp``-derived quartet
(``state-at-batch`` / ``is-expired-at-batch`` /
``days-until-expiry-at-batch`` / ``is-expiring-at-batch``): given a list
of perspective dates, ONE round-trip answers "would the renewal banner
have fired on each of them?" instead of N calls to the scalar. Per-row
parity with the singular scalar (both the helper and the HTTP endpoint)
is pinned so the batch cannot silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_expiring_at_batch.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_expiring_at_batch.py) -------------


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


# -- clawmetry.license.is_expiring_within_at_batch() -------------------------


def test_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`is_expiring_at_batch`."""
    assert app.lic.is_expiring_within_at_batch(30, None) == []


def test_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` -> ``[]`` rather than a crash."""
    assert app.lic.is_expiring_within_at_batch(30, 42) == []


def test_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.is_expiring_within_at_batch(30, []) == []
    assert app.lic.is_expiring_within_at_batch(30, ()) == []


def test_batch_no_license(app):
    """No license file on disk -> every row False (nothing to compare
    against). Time-independent, matches the never-mis-gate scalar."""
    rows = app.lic.is_expiring_within_at_batch(
        30, [0, int(time.time()), 2_000_000_000]
    )
    assert [r["is_expiring_within"] for r in rows] == [False, False, False]


def test_batch_active_key_inside_window_fires(app):
    """Active key with ``exp`` 10 days out: threshold 30 -> row for
    now fires; a row 40 days ago (60 days from exp) -> False."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_at_batch(
        30, [now, now - 40 * 86400, now + 5 * 86400]
    )
    # now: 10d from exp, inside window -> True
    # now - 40d: 50d from exp, outside 30d window -> False
    # now + 5d: 5d from exp, inside window -> True
    assert [r["is_expiring_within"] for r in rows] == [True, False, True]


def test_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_expiring_within_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [
        now - 30 * 86400,
        now - 1,
        now,
        now + 1,
        now + 10 * 86400,
        now + 20 * 86400,
    ]
    rows = app.lic.is_expiring_within_at_batch(30, epochs)
    for row, epoch in zip(rows, epochs):
        assert row["is_expiring_within"] == app.lic.is_expiring_within_at(
            30, epoch
        ), epoch


def test_batch_perpetual_never_fires(app):
    """Perpetual (no ``exp``) key -> False at every epoch (no claim to
    gate against). Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.is_expiring_within_at_batch(
        30, [0, int(time.time()), 2_000_000_000]
    )
    assert [r["is_expiring_within"] for r in rows] == [False, False, False]


def test_batch_invalid_signature(app):
    """Bogus-signature file -> False at every epoch (an unsigned body
    is untrusted whatever the perspective)."""
    _write_bogus(app)
    rows = app.lic.is_expiring_within_at_batch(
        30, [0, int(time.time()), 2_000_000_000]
    )
    assert [r["is_expiring_within"] for r in rows] == [False, False, False]


def test_batch_lapsed_at_epoch_returns_false(app):
    """A signature-valid key seen from a perspective where it has ALREADY
    lapsed -> False (negative remaining collapses; a different, louder
    ``is_expired_at`` banner covers that state).

    A row where the SAME key had NOT yet lapsed at that epoch (perspective
    epoch before exp) DOES fire True on purpose -- retrospectively, the
    renewal banner WOULD have fired at that time. Mirrors
    :func:`is_expiring_within_at`."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    # now:        exp - 5d ago, remaining=-5 -> already-lapsed -> False
    # now - 10d:  10d before now, so 5d BEFORE exp, remaining=5 -> True
    # now + 10d:  after exp, remaining=-15 -> already-lapsed -> False
    rows = app.lic.is_expiring_within_at_batch(
        30, [now, now - 10 * 86400, now + 10 * 86400]
    )
    assert [r["is_expiring_within"] for r in rows] == [False, True, False]


def test_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the scalar's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_at_batch(30, [str(now), str(now - 60 * 86400)])
    # str(now): 10d from exp -> True
    # str(now - 60d): 70d from exp -> False
    assert [r["is_expiring_within"] for r in rows] == [True, False]


def test_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_at_batch(
        30, [now, now + 100, now, str(now + 100), now + 200]
    )
    assert [r["epoch"] for r in rows] == [now, now + 100, now + 200]


def test_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` collapse to
    ``is_expiring_within=False`` (matches the scalar). Row still keeps
    its slot so output length matches N -- each bad input gets its
    own bucket."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_expiring_within_at_batch(30, [True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["is_expiring_within"] is False for r in rows)


def test_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``is_expiring_within=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_at_batch(
        30, [now, "garbage", now + 60 * 86400]
    )
    assert [r["is_expiring_within"] for r in rows] == [True, False, False]


def test_batch_bad_days_collapses_every_row_to_false(app):
    """``days=`` non-numeric / ``bool`` / negative -> every row
    collapses to ``is_expiring_within=False``. Row slots are still
    preserved so the output length matches N (the bad-input rows keep
    the never-mis-gate posture on the ``days`` axis, mirroring the
    ``epochs`` axis)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for bad_days in ("garbage", None, True, False, -1, -365):
        rows = app.lic.is_expiring_within_at_batch(
            bad_days, [now, now + 5 * 86400, now + 60 * 86400]
        )
        assert len(rows) == 3, bad_days
        assert all(r["is_expiring_within"] is False for r in rows), bad_days


def test_batch_zero_days_only_fires_on_day_of_expiry(app):
    """``days=0`` fires only when remaining == 0 -- the "expires
    today" boundary. Callers wanting a wider window supply a larger
    threshold."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    # exp - 86400 = 1 day out, days_until_expiry_at ~ 1 -> False
    # exp = 0 days out, remaining=0 -> True
    # exp - 1 = same-day boundary, remaining=0 -> True (floor div)
    rows = app.lic.is_expiring_within_at_batch(
        0, [exp - 86400, exp - 1, exp, exp + 1]
    )
    assert rows[0]["is_expiring_within"] is False
    assert rows[1]["is_expiring_within"] is True
    assert rows[2]["is_expiring_within"] is True
    # 1s past exp -> remaining=-1 -> False (already lapsed at epoch)
    assert rows[3]["is_expiring_within"] is False


def test_batch_threshold_applies_uniformly(app):
    """The ``days`` threshold applies to EVERY row uniformly; wider
    windows admit more rows."""
    tok = app.lic._encode_token(_payload(exp_delta=100 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [
        now,                  # 100 days out
        now + 30 * 86400,     # 70 days out
        now + 60 * 86400,     # 40 days out
        now + 80 * 86400,     # 20 days out
        now + 95 * 86400,     # 5 days out
    ]
    narrow = app.lic.is_expiring_within_at_batch(30, epochs)
    wide = app.lic.is_expiring_within_at_batch(90, epochs)
    # Narrow (30d): only the 20d and 5d rows fire
    assert [r["is_expiring_within"] for r in narrow] == [
        False,
        False,
        False,
        True,
        True,
    ]
    # Wide (90d): all rows within 90d fire; the "100 days out" one
    # does NOT because 100 > 90.
    assert [r["is_expiring_within"] for r in wide] == [
        False,
        True,
        True,
        True,
        True,
    ]


def test_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`is_expiring_within_at`
    -> ``is_expiring_within=False`` for THAT row. The batch never
    propagates."""
    import clawmetry.license as _lic

    def _boom(_days, _epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_expiring_within_at", _boom)
    rows = _lic.is_expiring_within_at_batch(30, [1_700_000_000, 1_800_000_000])
    assert [r["is_expiring_within"] for r in rows] == [False, False]
    assert len(rows) == 2


# -- GET /api/license/expiring-within-at-batch ----------------------------


def test_endpoint_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_missing_epochs_with_days(app):
    """``?days=`` present but ``?epochs=`` absent -> 400 missing
    epochs. The days-only knob doesn't imply epoch."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-at-batch?days=30")
    assert resp.status_code == 400


def test_endpoint_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-at-batch?epochs=")
        resp2 = c.get("/api/license/expiring-within-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_no_license(app):
    """No license file -> every row ``is_expiring_within=False``, HTTP
    200, current-time snapshot fields set to the OSS-free branch
    shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?epochs={now},0"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "expiring_within_at"
    assert data["count"] == 2
    assert data["threshold_days"] == 30
    assert [r["expiring_within"] for r in data["rows"]] == [False, False]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_default_days_is_30(app):
    """Default ``?days=`` -> 30 (matches the singular endpoint's
    default). A key 40 days out doesn't fire; a key 10 days out
    does."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?epochs={now}"
        )
    data = resp.get_json()
    assert data["threshold_days"] == 30
    assert data["rows"][0]["expiring_within"] is True


def test_endpoint_active_key_inside_window(app):
    """Active key with ``exp`` 10 days out and ``days=30``: current
    epoch fires; 40 days-ago perspective does not."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    now = int(time.time())
    csv = ",".join(str(e) for e in [now, now - 40 * 86400, now + 5 * 86400])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={csv}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "expiring_within_at"
    assert data["count"] == 3
    assert data["threshold_days"] == 30
    assert [r["expiring_within"] for r in data["rows"]] == [
        True,
        False,
        True,
    ]
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp


def test_endpoint_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/is-expiring-within-at?days=<d>&epoch=<n>`` endpoint
    -- the batch cannot silently drift from the scalar endpoint. Pin
    every row."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [
        now - 30 * 86400,
        now - 1,
        now,
        now + 1,
        now + 10 * 86400,
        now + 20 * 86400,
    ]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/expiring-within-at?days=30&epoch={epoch}"
            ).get_json()
            assert row["expiring_within"] == scalar["expiring_within"], epoch


def test_endpoint_bad_tokens_collapse_to_false(app):
    """Bad tokens don't fail the whole batch. They slot in with
    ``is_expiring_within=False`` (the never-mis-gate posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs=garbage,{now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["expiring_within"] for r in data["rows"]] == [False, True]


def test_endpoint_bad_days_collapses_every_row_to_false(app):
    """``?days=`` non-numeric -> every row False,
    ``threshold_days=0``. Row slots preserved (matches the singular
    ``/api/license/is-expiring-within-at``'s never-4xx posture on a
    ``days`` typo)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=garbage&epochs={now},{now + 5 * 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["threshold_days"] == 0
    assert data["count"] == 2
    assert all(r["expiring_within"] is False for r in data["rows"])


def test_endpoint_negative_days_clamps_to_zero(app):
    """``?days=-5`` clamps to 0 (matches the singular endpoint)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=-5&epochs={now}"
        )
    data = resp.get_json()
    assert data["threshold_days"] == 0
    # Threshold 0 -> current epoch (10 days from exp) is outside window
    assert data["rows"][0]["expiring_within"] is False


def test_endpoint_perpetual_never_fires(app):
    """Perpetual key -> every row False, but the current-time snapshot
    fields still reflect a valid install."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs=0,{now},2000000000"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["expiring_within"] for r in data["rows"]] == [
        False,
        False,
        False,
    ]
    assert data["has_license"] is True
    assert data["expires_at"] is None


def test_endpoint_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=30"
            f"&epochs={now},{now + 100},{now},{now + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [now, now + 100]


def test_endpoint_never_5xxs(app, monkeypatch):
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
        resp = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "no_license"
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None
    assert data["threshold_days"] == 30


# -- cross-endpoint consistency: shared snapshot + row alignment -------------


def test_endpoint_shared_snapshot_fields_agree_with_siblings(app):
    """Shares the current-time snapshot fields (``state`` /
    ``expires_at`` / ``has_license`` / ``valid``) with the existing
    ``/api/license/*-at-batch`` quartet. A UI binding several for the
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
        itw = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={now}"
        ).get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert s[key] == ex[key] == d[key] == it[key] == itw[key], key


def test_endpoint_rows_zip_with_siblings(app):
    """All five ``/api/license/*-at-batch`` endpoints admit the same
    input schema (``?epochs=`` CSV) and emit the same row ordering,
    so a caller can zip the responses index-for-index by epoch."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 60 * 86400, exp - 10 * 86400, exp - 1, exp + 5 * 86400]
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
        itw = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={csv}"
        ).get_json()
    assert s["count"] == ex["count"] == d["count"] == it["count"] == itw[
        "count"
    ] == 4
    for i, epoch in enumerate(epochs):
        assert (
            s["rows"][i]["epoch"]
            == ex["rows"][i]["epoch"]
            == d["rows"][i]["epoch"]
            == it["rows"][i]["epoch"]
            == itw["rows"][i]["epoch"]
            == epoch
        )
        # is_expiring_within fires on rows where 0 <= days_until <= 30
        # per-row; pin against the days batch so the two cannot drift.
        remaining = d["rows"][i]["days"]
        expected = remaining is not None and 0 <= remaining <= 30
        assert itw["rows"][i]["expiring_within"] is bool(expected), epoch
