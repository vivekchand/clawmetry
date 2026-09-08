"""Tests for :func:`clawmetry.license.is_expiring_within_days_at_batch`
and the paired ``GET /api/license/expiring-within-days-at-batch``
endpoint.

Days-axis batch sibling of :func:`clawmetry.license.is_expiring_within_at`
/ ``/api/license/expiring-within-at``. Complements
``expiring-within-at-batch`` on the orthogonal axis: where the existing
epochs-axis batch fans a fixed ``days`` threshold across N perspective
epochs, this fans N ``days`` thresholds across a SINGLE perspective
epoch -- the natural shape for a "renewal urgency" tile with multiple
thresholds. Per-row parity with the singular scalar (both the helper and
the HTTP endpoint) is pinned so the batch cannot silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_expiring_within_at_batch.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_expiring_within_at_batch.py) ------


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


# -- clawmetry.license.is_expiring_within_days_at_batch() --------------------


def test_batch_none_returns_empty(app):
    """``days_list is None`` -> ``[]``. Never-raise posture, matches
    :func:`is_expiring_within_at_batch` on the sibling axis."""
    assert app.lic.is_expiring_within_days_at_batch(None, int(time.time())) == []


def test_batch_non_iterable_returns_empty(app):
    """Non-iterable ``days_list`` -> ``[]`` rather than a crash."""
    assert app.lic.is_expiring_within_days_at_batch(42, int(time.time())) == []


def test_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.is_expiring_within_days_at_batch([], int(time.time())) == []
    assert app.lic.is_expiring_within_days_at_batch((), int(time.time())) == []


def test_batch_no_license(app):
    """No license file on disk -> every row False (nothing to compare
    against). Threshold-independent, matches the never-mis-gate
    scalar."""
    rows = app.lic.is_expiring_within_days_at_batch(
        [0, 7, 30, 365], int(time.time())
    )
    assert [r["is_expiring_within"] for r in rows] == [False, False, False, False]


def test_batch_active_key_inside_window_fires(app):
    """Active key with ``exp`` 10 days out at now:
    threshold 7  -> False (10 > 7)
    threshold 14 -> True  (10 <= 14)
    threshold 30 -> True  (10 <= 30)
    threshold 60 -> True  (10 <= 60)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch([7, 14, 30, 60], now)
    assert [r["is_expiring_within"] for r in rows] == [False, True, True, True]


def test_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_expiring_within_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install / epoch."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    days_list = [0, 1, 7, 14, 15, 16, 30, 90]
    rows = app.lic.is_expiring_within_days_at_batch(days_list, now)
    for row, days in zip(rows, days_list):
        assert row["is_expiring_within"] == app.lic.is_expiring_within_at(
            days, now
        ), days


def test_batch_perpetual_never_fires(app):
    """Perpetual (no ``exp``) key -> False at every threshold (no claim
    to gate against). Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.is_expiring_within_days_at_batch(
        [0, 7, 30, 365, 3650], int(time.time())
    )
    assert all(r["is_expiring_within"] is False for r in rows)
    assert len(rows) == 5


def test_batch_invalid_signature(app):
    """Bogus-signature file -> False at every threshold (an unsigned body
    is untrusted whatever the threshold)."""
    _write_bogus(app)
    rows = app.lic.is_expiring_within_days_at_batch(
        [0, 7, 30, 365], int(time.time())
    )
    assert all(r["is_expiring_within"] is False for r in rows)


def test_batch_lapsed_at_epoch_all_false(app):
    """A signature-valid key seen from a perspective where it has ALREADY
    lapsed -> False on EVERY threshold (negative remaining doesn't sit
    inside any threshold >= 0 -- a different, louder ``is_expired_at``
    banner covers that state). Mirrors :func:`is_expiring_within_at`."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch([0, 7, 30, 365, 3650], now)
    assert all(r["is_expiring_within"] is False for r in rows)


def test_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the scalar's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch(["7", "14", "30"], now)
    # exp is 10 days out
    assert [r["is_expiring_within"] for r in rows] == [False, True, True]
    assert [r["days"] for r in rows] == [7, 14, 30]


def test_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch(
        [7, 30, 7, "30", 60], now
    )
    assert [r["days"] for r in rows] == [7, 30, 60]


def test_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` / negative int collapse to
    ``is_expiring_within=False`` (matches the scalar). Row still keeps
    its slot so output length matches N -- each bad input gets its own
    bucket."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch(
        [True, False, None, "garbage", -1, -365], now
    )
    assert len(rows) == 6
    assert all(r["is_expiring_within"] is False for r in rows)


def test_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``is_expiring_within=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expiring_within_days_at_batch(
        [30, "garbage", 5, -1], now
    )
    # 30d threshold at 10d remaining -> True
    # "garbage" -> False (bad)
    # 5d threshold at 10d remaining -> False (10 > 5)
    # -1 -> False (bad)
    assert [r["is_expiring_within"] for r in rows] == [True, False, False, False]


def test_batch_bad_epoch_collapses_every_row_to_false(app):
    """``epoch=`` non-numeric / ``bool`` -> every row collapses to
    ``is_expiring_within=False``. Row slots are still preserved so the
    output length matches N (mirrors the sibling batch's never-mis-gate
    posture on the ``days`` axis)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    for bad_epoch in ("garbage", None, True, False):
        rows = app.lic.is_expiring_within_days_at_batch(
            [7, 30, 60], bad_epoch
        )
        assert len(rows) == 3, bad_epoch
        assert all(r["is_expiring_within"] is False for r in rows), bad_epoch


def test_batch_zero_days_only_fires_on_day_of_expiry(app):
    """``days=0`` fires only when remaining == 0 -- the "expires
    today" boundary. Callers wanting a wider window supply a larger
    threshold."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    # At epoch = exp - 86400: 1 day out, days_until_expiry_at ~ 1 ->
    # threshold 0 -> False; threshold 1+ -> True.
    rows_day_before = app.lic.is_expiring_within_days_at_batch(
        [0, 1, 7], exp - 86400
    )
    assert [r["is_expiring_within"] for r in rows_day_before] == [
        False,
        True,
        True,
    ]
    # At epoch = exp: 0 days out -> threshold 0 fires.
    rows_at_exp = app.lic.is_expiring_within_days_at_batch(
        [0, 1, 7], exp
    )
    assert rows_at_exp[0]["is_expiring_within"] is True
    # 1s past exp -> remaining=-1 -> False everywhere (lapsed at epoch)
    rows_past = app.lic.is_expiring_within_days_at_batch(
        [0, 1, 7, 30], exp + 1
    )
    assert all(r["is_expiring_within"] is False for r in rows_past)


def test_batch_epoch_applies_uniformly(app):
    """The perspective ``epoch`` applies to EVERY row uniformly;
    earlier perspective admits more rows."""
    tok = app.lic._encode_token(_payload(exp_delta=100 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    days_list = [1, 7, 30, 60, 90, 120]
    close = app.lic.is_expiring_within_days_at_batch(
        days_list, now + 95 * 86400
    )  # 5 days out
    far = app.lic.is_expiring_within_days_at_batch(days_list, now)  # 100 days out
    # Close (5 days remaining): threshold 7+ fires.
    assert [r["is_expiring_within"] for r in close] == [
        False,
        True,
        True,
        True,
        True,
        True,
    ]
    # Far (100 days remaining): only threshold 120 fires (100 <= 120).
    assert [r["is_expiring_within"] for r in far] == [
        False,
        False,
        False,
        False,
        False,
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
    rows = _lic.is_expiring_within_days_at_batch([7, 30], 1_700_000_000)
    assert [r["is_expiring_within"] for r in rows] == [False, False]
    assert len(rows) == 2


def test_batch_bytestable_across_calls(app):
    """Same input -> byte-stable output across repeated calls (dedup
    preserves first-seen order)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    a = app.lic.is_expiring_within_days_at_batch([7, 30, 60], now)
    b = app.lic.is_expiring_within_days_at_batch([7, 30, 60], now)
    assert a == b


# -- GET /api/license/expiring-within-days-at-batch --------------------------


def test_endpoint_missing_days(app):
    """``?days=`` absent -> 400 missing days."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-days-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing days"}


def test_endpoint_missing_days_with_epoch(app):
    """``?epoch=`` present but ``?days=`` absent -> 400 missing days.
    The epoch-only knob doesn't imply days."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-days-at-batch?epoch={now}"
        )
    assert resp.status_code == 400


def test_endpoint_blank_days(app):
    """``?days=`` blank / only-commas -> 400 missing days."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/expiring-within-days-at-batch?days=")
        resp2 = c.get("/api/license/expiring-within-days-at-batch?days=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_no_license(app):
    """No license file -> every row ``expiring_within=False``, HTTP
    200, current-time snapshot fields set to the OSS-free branch
    shape."""
    with app.app.test_client() as c:
        resp = c.get(
            "/api/license/expiring-within-days-at-batch?days=7,30,60"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "expiring_within_days_at"
    assert data["count"] == 3
    assert [r["expiring_within"] for r in data["rows"]] == [False, False, False]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_default_epoch_is_now(app):
    """Default ``?epoch=`` -> current time (matches the singular
    ``/api/license/expiring-within-at`` on the "now" branch). A key 10
    days out fires for threshold 30."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    before = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            "/api/license/expiring-within-days-at-batch?days=30"
        )
    after = int(time.time())
    data = resp.get_json()
    assert isinstance(data["epoch"], int)
    assert before <= data["epoch"] <= after
    assert data["rows"][0]["expiring_within"] is True


def test_endpoint_active_key_multi_threshold(app):
    """Active key with ``exp`` 10 days out at now: threshold 7 -> False,
    14 -> True, 30 -> True."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-days-at-batch?days=7,14,30&epoch={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "expiring_within_days_at"
    assert data["count"] == 3
    assert [r["expiring_within"] for r in data["rows"]] == [False, True, True]
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp
    assert data["epoch"] == now


def test_endpoint_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/expiring-within-at?days=<d>&epoch=<n>`` endpoint --
    the batch cannot silently drift from the scalar endpoint. Pin every
    row."""
    tok = app.lic._encode_token(_payload(exp_delta=15 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    days_list = [0, 1, 7, 14, 15, 16, 30, 90]
    csv = ",".join(str(d) for d in days_list)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/expiring-within-days-at-batch?days={csv}&epoch={now}"
        ).get_json()
        for row, days in zip(batch["rows"], days_list):
            scalar = c.get(
                f"/api/license/expiring-within-at?days={days}&epoch={now}"
            ).get_json()
            assert row["expiring_within"] == scalar["expiring_within"], days


def test_endpoint_bad_tokens_collapse_to_false(app):
    """Bad tokens don't fail the whole batch. They slot in with
    ``expiring_within=false`` (the never-mis-gate posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-days-at-batch?days=garbage,30&epoch={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["expiring_within"] for r in data["rows"]] == [False, True]


def test_endpoint_bad_epoch_collapses_every_row_to_false(app):
    """``?epoch=`` non-numeric -> every row False, ``epoch`` echoed
    back as the raw token. Row slots preserved (matches the surrounding
    batch endpoints' never-4xx posture on an ``epoch`` typo)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get(
            "/api/license/expiring-within-days-at-batch?days=7,30&epoch=garbage"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["epoch"] == "garbage"
    assert data["count"] == 2
    assert all(r["expiring_within"] is False for r in data["rows"])


def test_endpoint_negative_days_collapses_row(app):
    """A negative ``days=`` threshold collapses THAT row to False while
    preserving its slot (the scalar collapses to False on negatives, so
    the batch cannot silently diverge)."""
    tok = app.lic._encode_token(_payload(exp_delta=10 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-days-at-batch?days=-5,30&epoch={now}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["expiring_within"] for r in data["rows"]] == [False, True]


def test_endpoint_perpetual_never_fires(app):
    """Perpetual key -> every row False, but the current-time snapshot
    fields still reflect a valid install."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/expiring-within-days-at-batch?days=7,30,365&epoch={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert all(r["expiring_within"] is False for r in data["rows"])
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
            f"/api/license/expiring-within-days-at-batch"
            f"?days=7,30,7,30,60&epoch={now}"
        )
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["days"] for r in data["rows"]] == [7, 30, 60]


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
            f"/api/license/expiring-within-days-at-batch?days=7,30&epoch={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "no_license"
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


# -- cross-endpoint consistency: shared snapshot + row alignment -------------


def test_endpoint_shared_snapshot_fields_agree_with_epochs_axis(app):
    """Shares the current-time snapshot fields with
    ``/api/license/expiring-within-at-batch`` (the epochs-axis
    complement). A UI binding both for the same install must not catch
    them disagreeing on ``state`` / ``expires_at`` / ``has_license`` /
    ``valid``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        days_batch = c.get(
            f"/api/license/expiring-within-days-at-batch"
            f"?days=7,30&epoch={now}"
        ).get_json()
        epochs_batch = c.get(
            f"/api/license/expiring-within-at-batch?days=30&epochs={now}"
        ).get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert days_batch[key] == epochs_batch[key], key


def test_endpoint_days_row_matches_epochs_row_at_same_coords(app):
    """A row ``(days=D, epoch=E)`` in the days-axis batch must equal the
    row ``(epochs=E)`` in the epochs-axis batch called with ``days=D``.
    The two batches share the same underlying scalar
    :func:`is_expiring_within_at` -- they must agree at every
    ``(D, E)`` intersection."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epoch = exp - 20 * 86400  # 20 days out
    days_list = [7, 14, 21, 30, 45]
    with app.app.test_client() as c:
        days_axis = c.get(
            f"/api/license/expiring-within-days-at-batch"
            f"?days={','.join(str(d) for d in days_list)}&epoch={epoch}"
        ).get_json()
        for row, days in zip(days_axis["rows"], days_list):
            epochs_axis = c.get(
                f"/api/license/expiring-within-at-batch"
                f"?days={days}&epochs={epoch}"
            ).get_json()
            assert row["expiring_within"] == epochs_axis["rows"][0][
                "expiring_within"
            ], (days, epoch)
