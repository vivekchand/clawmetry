"""Tests for the three ``clawmetry.license`` ``_at_batch`` helpers
(:func:`license_state_at_batch`, :func:`is_expired_at_batch`,
:func:`days_until_expiry_at_batch`) and their paired ``/api/license/
state-at-batch``, ``/api/license/is-expired-at-batch`` and ``/api/license/
days-until-expiry-at-batch`` HTTP endpoints.

Per-value batch flavour of the singular ``_at`` trio -- fills the last
``_at_batch`` slot on the license-lifecycle axis so a scheduled-audit
tile that wants to render a per-epoch state / expired / days-remaining
timeline hydrates the full column in ONE round-trip instead of N calls
to the scalar endpoint. Per-row parity with the singular
``/api/license/state-at?epoch=<n>`` (and the ``is-expired-at`` /
``days-until-expiry-at`` siblings) is pinned so the batch cannot silently
drift from the scalar.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_state_at_scalar.py`` /
``tests/test_license_is_expired_at.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_state_at_scalar.py) -----------------


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


# -- clawmetry.license.license_state_at_batch() -------------------------------


def test_license_state_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Mirrors the never-raise posture of the
    per-value axis batches in ``clawmetry.entitlements``."""
    assert app.lic.license_state_at_batch(None) == []


def test_license_state_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller that
    forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.license_state_at_batch(42) == []


def test_license_state_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.license_state_at_batch([]) == []
    assert app.lic.license_state_at_batch(()) == []


def test_license_state_at_batch_no_license(app):
    """No license file on disk -> every row ``"no_license"`` regardless
    of epoch. Time-independent, matches the scalar."""
    rows = app.lic.license_state_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["state"] for r in rows] == ["no_license"] * 3
    assert [r["epoch"] for r in rows] == [0, int(time.time()), 2_000_000_000] or all(
        isinstance(r["epoch"], int) for r in rows
    )


def test_license_state_at_batch_active_key_mixed_epochs(app):
    """Active key: perspectives before ``exp`` -> ``"active"``; after
    ``exp`` -> ``"expired"``. The batch preserves per-row ordering."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    rows = app.lic.license_state_at_batch(epochs)
    assert [r["state"] for r in rows] == [
        "active",
        "active",
        "expired",
        "expired",
    ]
    assert [r["epoch"] for r in rows] == epochs


def test_license_state_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`license_state_at` -- the batch cannot
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
    rows = app.lic.license_state_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["state"] == app.lic.license_state_at(epoch), epoch


def test_license_state_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> every row ``"active"`` regardless of
    perspective. Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.license_state_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["state"] for r in rows] == ["active"] * 3


def test_license_state_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``"invalid"`` (time-independent)."""
    _write_bogus(app)
    rows = app.lic.license_state_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["state"] for r in rows] == ["invalid"] * 3


def test_license_state_at_batch_lapsed_key_pre_lapse_epoch(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    ``"active"`` row (retrospective "was this active on <date>"); at
    "now" -> ``"expired"``. Batch flips per row."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.license_state_at_batch(
        [now - 20 * 86400, now - 3 * 86400, now]
    )
    assert [r["state"] for r in rows] == ["active", "expired", "expired"]


def test_license_state_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_state_at_batch(
        [now, now + 100, now, str(now + 100), now + 200]
    )
    assert [r["epoch"] for r in rows] == [now, now + 100, now + 200]


def test_license_state_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_state_at_batch([str(now), str(now + 60 * 86400)])
    assert [r["state"] for r in rows] == ["active", "expired"]


def test_license_state_at_batch_bad_tokens_collapse_to_no_license(app):
    """``bool`` / non-numeric strings / ``None`` collapse to a
    ``state="no_license"`` row. Row still keeps its slot (each bad
    token gets its own bucket) so output length still matches N."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.license_state_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["state"] == "no_license" for r in rows)


def test_license_state_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``state="no_license"``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_state_at_batch([now, "garbage", now + 60 * 86400])
    assert [r["state"] for r in rows] == ["active", "no_license", "expired"]


def test_license_state_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`license_state_at` ->
    ``state="no_license"`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_state_at", _boom)
    rows = _lic.license_state_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["state"] for r in rows] == ["no_license", "no_license"]
    assert len(rows) == 2


# -- clawmetry.license.is_expired_at_batch() ----------------------------------


def test_is_expired_at_batch_no_license(app):
    """No license file -> every row ``expired=False`` (nothing to
    compare against). Mirrors the scalar posture."""
    rows = app.lic.is_expired_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["expired"] for r in rows] == [False, False, False]


def test_is_expired_at_batch_active_key_boundary(app):
    """At the exact ``exp`` second the classification flips: ``exp <= epoch``
    is True at the boundary; strictly less is False. Same boundary the
    scalar uses."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_expired_at_batch([exp - 1, exp, exp + 1])
    assert [r["expired"] for r in rows] == [False, True, True]


def test_is_expired_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_expired_at` -- the batch cannot
    silently drift from the scalar. Pin every row against the singular
    helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 60 * 86400]
    rows = app.lic.is_expired_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["expired"] == app.lic.is_expired_at(epoch), epoch


def test_is_expired_at_batch_perpetual_never_expired(app):
    """Perpetual key -> ``expired=False`` at every epoch (no ``exp`` to
    compare against). Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.is_expired_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["expired"] for r in rows] == [False, False, False]


def test_is_expired_at_batch_invalid_signature(app):
    """Bogus-signature file -> ``expired=False`` at every epoch (an
    unsigned body is untrusted whatever the perspective; the scalar
    refuses to trust the payload's ``exp``)."""
    _write_bogus(app)
    rows = app.lic.is_expired_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["expired"] for r in rows] == [False, False, False]


def test_is_expired_at_batch_dedupes_by_int_key(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_expired_at_batch(
        [now, now + 60 * 86400, str(now), now + 60 * 86400]
    )
    assert [r["epoch"] for r in rows] == [now, now + 60 * 86400]


def test_is_expired_at_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` collapse to
    ``expired=False`` (mirrors the scalar's rejection). Row still keeps
    its slot so length matches N."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_expired_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["expired"] is False for r in rows)


def test_is_expired_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure -> ``expired=False`` for THAT row."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_expired_at", _boom)
    rows = _lic.is_expired_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["expired"] for r in rows] == [False, False]


# -- clawmetry.license.days_until_expiry_at_batch() --------------------------


def test_days_until_expiry_at_batch_no_license(app):
    """No license file -> every row ``days=None`` (nothing to count down
    to). Mirrors the scalar."""
    rows = app.lic.days_until_expiry_at_batch([0, int(time.time())])
    assert [r["days"] for r in rows] == [None, None]


def test_days_until_expiry_at_batch_signed_countdown(app):
    """Days are floor-divided seconds ``(exp - epoch) // 86400``. Signed:
    positive when ``epoch`` is before ``exp``, zero on the day of,
    negative when ``epoch`` is after ``exp``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.days_until_expiry_at_batch([exp, exp - 10 * 86400, exp + 3 * 86400])
    assert [r["days"] for r in rows] == [0, 10, -3]


def test_days_until_expiry_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`days_until_expiry_at` -- the batch
    cannot silently drift from the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 20 * 86400, now + 60 * 86400]
    rows = app.lic.days_until_expiry_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["days"] == app.lic.days_until_expiry_at(epoch), epoch


def test_days_until_expiry_at_batch_perpetual_all_none(app):
    """Perpetual key -> every row ``days=None`` (no ``exp`` to count
    down to). Mirrors the scalar."""
    _write_perpetual(app)
    rows = app.lic.days_until_expiry_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["days"] for r in rows] == [None, None, None]


def test_days_until_expiry_at_batch_bad_tokens_collapse_to_none(app):
    """``bool`` / non-numeric / ``None`` collapse to ``days=None``,
    matching the scalar's ``None``-on-bad-input posture."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.days_until_expiry_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["days"] is None for r in rows)


def test_days_until_expiry_at_batch_dedupes_by_int_key(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.days_until_expiry_at_batch(
        [now, str(now), now + 86400, now + 86400]
    )
    assert [r["epoch"] for r in rows] == [now, now + 86400]


def test_days_until_expiry_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure -> ``days=None`` for THAT row."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "days_until_expiry_at", _boom)
    rows = _lic.days_until_expiry_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["days"] for r in rows] == [None, None]


# -- GET /api/license/state-at-batch -----------------------------------------


def test_endpoint_state_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the batch
    endpoints in ``routes/entitlement.py`` -- missing input is a real
    error, unlike bad input)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/state-at-batch")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data == {"error": "missing epochs"}


def test_endpoint_state_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/state-at-batch?epochs=")
        resp2 = c.get("/api/license/state-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_state_at_batch_no_license(app):
    """No license file -> every row ``state="no_license"``, HTTP 200,
    current-time snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/state-at-batch?epochs={now},0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "license_state_at"
    assert data["count"] == 2
    assert [r["state"] for r in data["rows"]] == ["no_license", "no_license"]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_state_at_batch_active_key_mixed_epochs(app):
    """Active key at mixed perspectives -> per-row states match the
    scalar. Snapshot reflects current install state."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 60 * 86400]
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/state-at-batch?epochs={epochs[0]},{epochs[1]}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["state"] for r in data["rows"]] == ["active", "expired"]
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert isinstance(data["expires_at"], int)


def test_endpoint_state_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular ``/api/license/state-at?epoch=<n>``
    endpoint -- the batch cannot silently drift from the scalar
    endpoint. Pin every row."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 5 * 86400, now, now + 30 * 86400, now + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(f"/api/license/state-at-batch?epochs={csv}").get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/state-at?epoch={epoch}"
            ).get_json()
            assert row["state"] == scalar["state_at"], epoch


def test_endpoint_state_at_batch_bad_tokens_do_not_400(app):
    """Bad tokens don't fail the whole batch -- they slot in with
    ``state="no_license"``. The 400 is reserved for ``?epochs=``
    entirely missing / blank."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/state-at-batch?epochs={now},garbage,true,{now + 60 * 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 4
    assert [r["state"] for r in data["rows"]] == [
        "active",
        "no_license",
        "no_license",
        "expired",
    ]


def test_endpoint_state_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/state-at-batch?epochs={now},{now + 100},{now},{now + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [now, now + 100]


def test_endpoint_state_at_batch_never_5xxs(app, monkeypatch):
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
        resp = c.get(f"/api/license/state-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "no_license"
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


# -- GET /api/license/is-expired-at-batch ------------------------------------


def test_endpoint_is_expired_at_batch_missing_epochs(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-expired-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_is_expired_at_batch_active_key_boundary(app):
    """Active key evaluated at pre-exp / exp / post-exp epochs ->
    per-row expired matches the scalar's ``<= exp`` cutoff."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp - 1, exp, exp + 1])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-expired-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_expired_at"
    assert data["count"] == 3
    assert [r["expired"] for r in data["rows"]] == [False, True, True]


def test_endpoint_is_expired_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular ``/api/license/is-expired-at?epoch=<n>``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/is-expired-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/is-expired-at?epoch={epoch}"
            ).get_json()
            assert row["expired"] == scalar["is_expired_at"], epoch


def test_endpoint_is_expired_at_batch_bad_tokens_collapse_to_false(app):
    """Bad tokens don't fail the whole batch. They slot in with
    ``expired=False`` (the never-mis-gate posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-expired-at-batch?epochs=garbage,{now + 60 * 86400}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["expired"] for r in data["rows"]] == [False, True]


def test_endpoint_is_expired_at_batch_perpetual_never_expired(app):
    """Perpetual key -> every row ``expired=False``."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-expired-at-batch?epochs=0,{now},2000000000"
        )
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["expired"] for r in data["rows"]] == [False, False, False]
    assert data["has_license"] is True
    assert data["expires_at"] is None


# -- GET /api/license/days-until-expiry-at-batch -----------------------------


def test_endpoint_days_until_expiry_at_batch_missing_epochs(app):
    with app.app.test_client() as c:
        resp = c.get("/api/license/days-until-expiry-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_days_until_expiry_at_batch_signed_countdown(app):
    """Days are floor-divided seconds; the row shape carries ``days``
    as a signed int (or ``None`` on bad inputs)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp, exp - 5 * 86400, exp + 3 * 86400])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/days-until-expiry-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "days_until_expiry_at"
    assert data["count"] == 3
    assert [r["days"] for r in data["rows"]] == [0, 5, -3]


def test_endpoint_days_until_expiry_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with the singular
    ``/api/license/days-until-expiry-at?epoch=<n>``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 5 * 86400, now + 30 * 86400, now + 90 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/days-until-expiry-at?epoch={epoch}"
            ).get_json()
            assert row["days"] == scalar["days_left"], epoch


def test_endpoint_days_until_expiry_at_batch_perpetual_all_none(app):
    """Perpetual -> every row ``days=None``."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs=0,{now}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["days"] for r in data["rows"]] == [None, None]


def test_endpoint_days_until_expiry_at_batch_bad_tokens_collapse_to_none(app):
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs=garbage,{now}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert data["rows"][0]["days"] is None
    assert isinstance(data["rows"][1]["days"], int)


# -- cross-endpoint consistency: rows can be zipped index-for-index ----------


def test_endpoints_batch_rows_zip_index_for_index(app):
    """All three ``/api/license/*-at-batch`` endpoints admit the same
    input schema (``?epochs=`` CSV) and emit the same row ordering, so a
    caller assembling an audit timeline can zip the responses index-for-
    index by epoch column."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 10 * 86400, now, now + 5 * 86400, now + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        s = c.get(f"/api/license/state-at-batch?epochs={csv}").get_json()
        e = c.get(f"/api/license/is-expired-at-batch?epochs={csv}").get_json()
        d = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={csv}"
        ).get_json()
    assert s["count"] == e["count"] == d["count"] == 4
    for i, epoch in enumerate(epochs):
        assert s["rows"][i]["epoch"] == e["rows"][i]["epoch"] == d["rows"][i][
            "epoch"
        ] == epoch
        # A row classified "expired" must also carry expired=True at the
        # same epoch (both derive from the same exp <= epoch cutoff).
        expected_expired = s["rows"][i]["state"] == "expired"
        assert e["rows"][i]["expired"] is expected_expired, epoch


def test_endpoints_batch_shared_snapshot_fields_agree(app):
    """All three batch endpoints share the current-time snapshot fields
    (``state`` / ``expires_at`` / ``has_license`` / ``valid``). A UI
    binding several for the same install must not catch them
    disagreeing on those fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        s = c.get(f"/api/license/state-at-batch?epochs={now}").get_json()
        e = c.get(f"/api/license/is-expired-at-batch?epochs={now}").get_json()
        d = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={now}"
        ).get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert s[key] == e[key] == d[key], key
