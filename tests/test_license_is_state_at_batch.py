"""Tests for :func:`clawmetry.license.is_state_at_batch` and the paired
``GET /api/license/is-state-at-batch`` endpoint.

Shared-``state`` batch sibling of :func:`clawmetry.license.is_state_at`
/ ``/api/license/is-state-at``. Where the scalar folds ONE
``(state, epoch)`` pair to ONE bool, this batch preserves per-value
rows for a fixed ``state`` and a sequence of perspective epochs so a
scheduled-audit tile answering "would we have shown the <state> banner
on each of these audit dates?" hydrates in ONE round-trip instead of
fanning out N scalar calls. Per-row parity with the singular scalar
(both the helper and the HTTP endpoint) is pinned so the batch cannot
silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_expiring_at_batch.py``.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_expiring_at_batch.py) ------------


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


# -- clawmetry.license.is_state_at_batch() -----------------------------------


def test_is_state_at_batch_none_epochs_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`license_state_at_batch` / :func:`is_expiring_at_batch`."""
    assert app.lic.is_state_at_batch("active", None) == []


def test_is_state_at_batch_non_iterable_epochs_returns_empty(app):
    """Non-iterable ``epochs`` -> ``[]`` rather than a crash."""
    assert app.lic.is_state_at_batch("active", 42) == []


def test_is_state_at_batch_empty_epochs_returns_empty(app):
    """Empty iterable -> ``[]`` regardless of ``state``."""
    assert app.lic.is_state_at_batch("active", []) == []
    assert app.lic.is_state_at_batch("no_license", ()) == []


def test_is_state_at_batch_none_state_all_false(app):
    """``state=None`` collapses every row to ``is_state=False`` while
    preserving row slots (matches never-mis-gate scalar posture)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_state_at_batch(None, [now, now + 86400])
    assert len(rows) == 2
    assert [r["is_state"] for r in rows] == [False, False]


def test_is_state_at_batch_empty_state_all_false(app):
    """Empty ``state`` collapses every row to ``is_state=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_state_at_batch("", [now, now + 86400])
    assert [r["is_state"] for r in rows] == [False, False]


def test_is_state_at_batch_typo_state_all_false(app):
    """A typo like ``"actiev"`` collapses every row to ``False`` --
    a caller cannot silently mis-gate on a mis-spelled state name."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.is_state_at_batch("actiev", [now, now + 86400])
    assert [r["is_state"] for r in rows] == [False, False]


def test_is_state_at_batch_unknown_state_preserves_row_slots(app):
    """Bad state still yields N rows so the response length matches N.
    Row slots must be preserved even when every value is False."""
    rows = app.lic.is_state_at_batch("garbage", [0, 1, 2, 3])
    assert len(rows) == 4
    assert all(r["is_state"] is False for r in rows)


def test_is_state_at_batch_active_state_active_key(app):
    """Active key + active state: every row inside the key's ``exp``
    window fires ``True``; rows past ``exp`` are "expired" per
    ``license_state_at`` so they fire ``False`` on ``state="active"``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    # Inside window (before exp) -> active; on-or-after exp -> expired.
    rows = app.lic.is_state_at_batch(
        "active", [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    assert [r["is_state"] for r in rows] == [True, True, False, False]


def test_is_state_at_batch_expired_state_matches_after_exp(app):
    """Active key + ``state="expired"``: only rows at-or-after ``exp``
    fire ``True`` (perspective-state semantics)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_state_at_batch(
        "expired", [exp - 1, exp, exp + 1, exp + 60 * 86400]
    )
    assert [r["is_state"] for r in rows] == [False, True, True, True]


def test_is_state_at_batch_no_license_state_no_license_key(app):
    """No license file -> every good-epoch row on
    ``state="no_license"`` fires ``True`` (perspective-state matches)."""
    now = int(time.time())
    rows = app.lic.is_state_at_batch(
        "no_license", [0, now, 2_000_000_000]
    )
    assert [r["is_state"] for r in rows] == [True, True, True]


def test_is_state_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_state_at` -- pin every row and
    every state combination against the singular helper."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    for state in ("active", "expired", "invalid", "no_license"):
        rows = app.lic.is_state_at_batch(state, epochs)
        for row, epoch in zip(rows, epochs):
            assert row["is_state"] == app.lic.is_state_at(state, epoch), (
                state,
                epoch,
            )


def test_is_state_at_batch_perpetual_active(app):
    """Perpetual (no ``exp``) key + ``state="active"`` -> every good
    epoch fires ``True`` (perpetual is always active)."""
    _write_perpetual(app)
    now = int(time.time())
    rows = app.lic.is_state_at_batch(
        "active", [0, now, 2_000_000_000]
    )
    assert [r["is_state"] for r in rows] == [True, True, True]


def test_is_state_at_batch_perpetual_never_expired(app):
    """Perpetual key + ``state="expired"`` -> every row ``False``
    (nothing to compare against). Mirrors the scalar."""
    _write_perpetual(app)
    now = int(time.time())
    rows = app.lic.is_state_at_batch(
        "expired", [0, now, 2_000_000_000]
    )
    assert [r["is_state"] for r in rows] == [False, False, False]


def test_is_state_at_batch_invalid_signature(app):
    """Bogus-signature file + ``state="invalid"`` -> every row fires
    ``True`` at every epoch. The signature is untrusted whatever the
    perspective."""
    _write_bogus(app)
    now = int(time.time())
    rows = app.lic.is_state_at_batch(
        "invalid", [0, now, 2_000_000_000]
    )
    assert [r["is_state"] for r in rows] == [True, True, True]


def test_is_state_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the batch pre-
    parser's ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_state_at_batch(
        "expired", [str(exp), str(exp + 1)]
    )
    assert [r["is_state"] for r in rows] == [True, True]


def test_is_state_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_state_at_batch(
        "expired",
        [exp, exp + 100, exp, str(exp + 100), exp + 200],
    )
    assert [r["epoch"] for r in rows] == [exp, exp + 100, exp + 200]


def test_is_state_at_batch_bad_tokens_collapse_active_to_false(app):
    """``bool`` / non-numeric / ``None`` + ``state="active"`` collapse
    to ``is_state=False`` (matches the scalar's rejection). Row still
    keeps its slot so output length matches N."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_state_at_batch(
        "active", [True, False, None, "garbage", ""]
    )
    # Each bad token keeps its own bucket (matches _license_epoch_batch_keys
    # semantics -- empty and None are distinguished by id())
    assert len(rows) == 5
    assert all(r["is_state"] is False for r in rows)


def test_is_state_at_batch_bad_tokens_state_no_license_truthful(app):
    """Bad tokens + ``state="no_license"`` -> ``True`` for the bad
    rows: the scalar's ``license_state_at`` collapses a bad epoch to
    ``"no_license"`` and the batch inherits that semantics. Matches
    the conservative "no entitlement" fallback of the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_state_at_batch(
        "no_license", [True, "garbage", None]
    )
    assert len(rows) == 3
    assert all(r["is_state"] is True for r in rows)


def test_is_state_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in per the shared-``state`` semantics."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_state_at_batch(
        "expired", [exp - 1, "garbage", exp, exp + 60 * 86400]
    )
    assert [r["is_state"] for r in rows] == [False, False, True, True]


def test_is_state_at_batch_state_case_insensitive(app):
    """``state`` is normalised case-insensitively after strip, matching
    the scalar's ``.strip().lower()`` treatment."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    for variant in ("Active", "ACTIVE", "  active  ", "AcTiVe"):
        rows = app.lic.is_state_at_batch(variant, [exp - 86400])
        assert [r["is_state"] for r in rows] == [True], variant


def test_is_state_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`is_state_at` ->
    ``is_state=False`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_state, _epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_state_at", _boom)
    rows = _lic.is_state_at_batch(
        "active", [1_700_000_000, 1_800_000_000]
    )
    assert [r["is_state"] for r in rows] == [False, False]
    assert len(rows) == 2


def test_is_state_at_batch_boundary_agrees_with_is_state(app):
    """At ``epoch = now``, the batch must agree with :func:`is_state`
    for the same install and the same requested ``state``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    for state in ("active", "expired", "invalid", "no_license"):
        rows = app.lic.is_state_at_batch(state, [now])
        assert rows[0]["is_state"] == app.lic.is_state(state), state


# -- GET /api/license/is-state-at-batch --------------------------------------


def test_endpoint_is_state_at_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state-at-batch?state=active")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_is_state_at_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-state-at-batch?state=active&epochs=")
        resp2 = c.get(
            "/api/license/is-state-at-batch?state=active&epochs=,,,"
        )
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_is_state_at_batch_missing_state_degrades_not_400(app):
    """``?state=`` absent (with valid ``?epochs=``) does NOT 4xx --
    every row collapses to ``is_state=false`` per the shared-``state``
    posture. A stale UI shouldn't hide the whole batch behind a typo."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-state-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_state_at"
    assert data["count"] == 1
    assert data["requested_state"] == ""
    assert data["rows"][0]["is_state"] is False


def test_endpoint_is_state_at_batch_no_license(app):
    """No license file + ``state="no_license"`` -> every row ``True``,
    HTTP 200, current-time snapshot fields set to the OSS-free branch
    shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=no_license&epochs={now},0"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_state_at"
    assert data["requested_state"] == "no_license"
    assert data["count"] == 2
    assert [r["is_state"] for r in data["rows"]] == [True, True]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_is_state_at_batch_active_key_active_state(app):
    """Active key + ``state="active"``: rows inside the ``exp`` window
    fire ``True``; rows at-or-after ``exp`` fire ``False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(
        str(e) for e in [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=active&epochs={csv}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_state_at"
    assert data["requested_state"] == "active"
    assert data["count"] == 4
    assert [r["is_state"] for r in data["rows"]] == [
        True,
        True,
        False,
        False,
    ]
    assert data["state"] == "active"
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp


def test_endpoint_is_state_at_batch_state_case_normalised_in_echo(app):
    """``requested_state`` is normalised (stripped + lowered) in the
    echo field, matching the scalar endpoint's echo shape."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=%20Active%20&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_state"] == "active"


def test_endpoint_is_state_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with the singular
    ``/api/license/is-state-at?state=<X>&epoch=<n>`` endpoint -- pin
    every row and every state combination against the scalar
    endpoint."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        for state in ("active", "expired", "invalid", "no_license"):
            batch = c.get(
                f"/api/license/is-state-at-batch?state={state}&epochs={csv}"
            ).get_json()
            for row, epoch in zip(batch["rows"], epochs):
                scalar = c.get(
                    f"/api/license/is-state-at?state={state}&epoch={epoch}"
                ).get_json()
                assert row["is_state"] == scalar["is_state_at"], (
                    state,
                    epoch,
                )


def test_endpoint_is_state_at_batch_bad_tokens_collapse_to_false(app):
    """Bad tokens + ``state="active"`` -> ``is_state=false`` (never-
    mis-gate posture). Good rows still resolve alongside."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=active&epochs=garbage,{exp - 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["is_state"] for r in data["rows"]] == [False, True]


def test_endpoint_is_state_at_batch_bad_tokens_no_license_state(app):
    """Bad tokens + ``state="no_license"`` -> ``True`` for those rows
    (the perspective is unusable, the conservative fallback holds)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=no_license&epochs=garbage,{now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    # Row 0 (bad epoch) -> True (fallback matches); row 1 (real epoch,
    # active key) -> False.
    assert [r["is_state"] for r in data["rows"]] == [True, False]


def test_endpoint_is_state_at_batch_unknown_state_all_false(app):
    """A typo like ``?state=actiev`` collapses every row to ``False``
    -- deliberately strict on the state parameter, matching the scalar
    endpoint's stance."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=actiev&epochs={now},{now + 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_state"] == "actiev"
    assert [r["is_state"] for r in data["rows"]] == [False, False]


def test_endpoint_is_state_at_batch_perpetual_active(app):
    """Perpetual key + ``state="active"`` -> every row ``True``, but
    the current-time snapshot fields still reflect a valid install."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=active&epochs=0,{now},2000000000"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["is_state"] for r in data["rows"]] == [True, True, True]
    assert data["has_license"] is True
    assert data["expires_at"] is None


def test_endpoint_is_state_at_batch_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    with app.app.test_client() as c:
        resp = c.get(
            f"/api/license/is-state-at-batch?state=expired&epochs={exp},{exp + 100},{exp},{exp + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [exp, exp + 100]


def test_endpoint_is_state_at_batch_never_5xxs(app, monkeypatch):
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
            f"/api/license/is-state-at-batch?state=active&epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["state"] == "no_license"
    assert data["has_license"] is False
    assert data["valid"] is False
    assert data["expires_at"] is None


# -- cross-endpoint consistency: shared snapshot + row alignment -------------


def test_endpoint_is_state_at_batch_shared_snapshot_fields_agree_with_siblings(
    app,
):
    """Shares the current-time snapshot fields (``state`` /
    ``expires_at`` / ``has_license`` / ``valid``) with the existing
    ``/api/license/*-at-batch`` quartet. A UI binding several for the
    same install must not catch them disagreeing on those fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        s = c.get(f"/api/license/state-at-batch?epochs={now}").get_json()
        ex = c.get(
            f"/api/license/is-expired-at-batch?epochs={now}"
        ).get_json()
        d = c.get(
            f"/api/license/days-until-expiry-at-batch?epochs={now}"
        ).get_json()
        it = c.get(
            f"/api/license/is-expiring-at-batch?epochs={now}"
        ).get_json()
        st = c.get(
            f"/api/license/is-state-at-batch?state=active&epochs={now}"
        ).get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert s[key] == ex[key] == d[key] == it[key] == st[key], key


def test_endpoint_is_state_at_batch_rows_zip_with_state_at_batch(app):
    """``/api/license/is-state-at-batch`` row order MUST align with
    ``/api/license/state-at-batch`` on the same ``?epochs=`` CSV so a
    caller can zip both responses index-for-index and cross-check
    (``is_state`` iff ``state == requested_state``)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 5 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        state_rows = c.get(
            f"/api/license/state-at-batch?epochs={csv}"
        ).get_json()["rows"]
        for target in ("active", "expired", "invalid", "no_license"):
            match_rows = c.get(
                f"/api/license/is-state-at-batch?state={target}&epochs={csv}"
            ).get_json()["rows"]
            for state_row, match_row in zip(state_rows, match_rows):
                assert state_row["epoch"] == match_row["epoch"]
                assert match_row["is_state"] == (
                    state_row["state"] == target
                ), (target, state_row["epoch"])
