"""Tests for the ``license_tier_at(epoch)`` scalar and
``license_tier_at_batch(epochs)`` batch helpers on ``clawmetry.license``
and their paired ``/api/license/tier-at`` / ``/api/license/tier-at-batch``
HTTP endpoints.

The perspective-epoch flavour of the ``license_tier`` scalar. Both
derive from the same signed ``tier`` claim and refuse the invalid-
signature branch, so they cannot disagree at the boundary when the
perspective epoch equals "now"; on any other epoch these helpers answer
"what tier would :func:`license_tier` have reported evaluated as of
``epoch``?" without the caller having to snapshot the license state at
that time or compare ``exp`` to a caller-supplied epoch themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_state_at_scalar.py`` /
``tests/test_license_state_at_batch.py`` so nothing depends on the real
production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_state_at_scalar.py) ------------------


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


# -- clawmetry.license.license_tier_at() --------------------------------------


def test_license_tier_at_no_license(app):
    """No license file on disk -> ``None`` regardless of epoch."""
    assert app.lic.license_tier_at(int(time.time())) is None
    assert app.lic.license_tier_at(0) is None
    assert app.lic.license_tier_at(2_000_000_000) is None


def test_license_tier_at_now_matches_license_tier_active(app):
    """When ``epoch`` equals "now", perspective scalar must agree with
    :func:`license_tier` on an active install. Both derive from the same
    signed ``tier`` claim, so a UI binding both cannot catch them
    disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_tier_at(now) == "pro"
    assert app.lic.license_tier() == "pro"


def test_license_tier_at_now_matches_license_tier_lapsed(app):
    """Lapsed-key parity: at "now", perspective scalar and base scalar
    must both return ``None`` -- both refuse the expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.license_tier_at(now) is None
    assert app.lic.license_tier() is None


def test_license_tier_at_future_epoch_before_expiry(app):
    """Future perspective still before ``exp`` -> tier surfaces (key would
    NOT yet be expired at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.license_tier_at(epoch) == "pro"


def test_license_tier_at_future_epoch_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``None`` (the
    key WILL be expired at that perspective). This is the "will this
    node still be Pro at our next audit?" prospective scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.license_tier_at(epoch) is None


def test_license_tier_at_past_epoch_still_active(app):
    """Perspective BEFORE now on an active key -> tier surfaces (the key
    was not yet expired then, since ``exp`` is even further in the
    future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.license_tier_at(epoch) == "pro"


def test_license_tier_at_lapsed_key_pre_lapse_epoch_surfaces_tier(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` -> tier
    surfaces (retrospective "was this Pro on <date>?"). At "now" (past
    ``exp``) -> ``None``."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    assert app.lic.license_tier_at(now - 20 * 86400) == "pro"
    assert app.lic.license_tier_at(now - 3 * 86400) is None
    assert app.lic.license_tier_at(now) is None


def test_license_tier_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, the tier must collapse to ``None``
    -- the ``<= epoch`` cutoff matches :func:`license_state_at`'s
    ``exp <= epoch`` boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    from clawmetry import license as _lic

    info = _lic.current_license_info()
    exp_epoch = int(info["exp"])
    assert app.lic.license_tier_at(exp_epoch - 1) == "pro"
    assert app.lic.license_tier_at(exp_epoch) is None
    assert app.lic.license_tier_at(exp_epoch + 1) is None


def test_license_tier_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> tier surfaces at every epoch."""
    _write_perpetual(app)
    assert app.lic.license_tier_at(0) == "pro"
    assert app.lic.license_tier_at(int(time.time())) == "pro"
    assert app.lic.license_tier_at(2_000_000_000) == "pro"


def test_license_tier_at_invalid_signature(app):
    """Bogus-signature file -> ``None`` regardless of epoch (time-
    independent, matching :func:`license_tier`)."""
    _write_bogus(app)
    assert app.lic.license_tier_at(0) is None
    assert app.lic.license_tier_at(int(time.time())) is None
    assert app.lic.license_tier_at(2_000_000_000) is None


def test_license_tier_at_normalises_casing(app):
    """Tier claim casing is normalised the same way :func:`license_tier`
    normalises it -- callers can compare against a hard-coded ``"pro"``
    without a .lower() on every read."""
    tok = app.lic._encode_token(_payload(tier="  PRO  "), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier_at(int(time.time())) == "pro"


def test_license_tier_at_missing_tier_claim_matches_scalar(app):
    """Signed payload with no ``tier`` claim: the perspective-epoch scalar
    MUST match :func:`license_tier` on the same install (both derive from
    :func:`current_license_info`, which today defaults a missing ``tier``
    claim to ``"pro"``). This test pins parity with the base scalar --
    it does NOT claim the default is desirable; it only guards against
    the two scalars silently diverging on the same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_tier=True)
    now = int(time.time())
    assert app.lic.license_tier_at(now) == app.lic.license_tier()


def test_license_tier_at_bool_epoch_refused(app):
    """``bool`` is an ``int`` subclass but must be refused so a caller
    passing ``True`` / ``False`` gets ``None`` back, not a spurious
    "was tier X at epoch 1?" answer."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier_at(True) is None
    assert app.lic.license_tier_at(False) is None


def test_license_tier_at_non_numeric_epoch(app):
    """Non-numeric epoch -> ``None`` so a caller cannot silently mis-gate
    on a typo -- conservative fallback since ``None`` implies no
    entitlement."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.license_tier_at("not-a-number") is None
    assert app.lic.license_tier_at(None) is None
    assert app.lic.license_tier_at([]) is None


def test_license_tier_at_string_epoch_coerced(app):
    """String epoch that ``int()`` accepts -> coerced and honoured, matching
    the behaviour of :func:`license_state_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.license_tier_at(str(now)) == "pro"


# -- clawmetry.license.license_tier_at_batch() --------------------------------


def test_license_tier_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Mirrors the never-raise posture of the
    sibling per-value axis batches."""
    assert app.lic.license_tier_at_batch(None) == []


def test_license_tier_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller that
    forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.license_tier_at_batch(42) == []


def test_license_tier_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.license_tier_at_batch([]) == []
    assert app.lic.license_tier_at_batch(()) == []


def test_license_tier_at_batch_no_license(app):
    """No license file on disk -> every row ``None`` regardless of epoch.
    Time-independent, matches the scalar."""
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.license_tier_at_batch(epochs)
    assert [r["tier"] for r in rows] == [None] * 3
    assert [r["epoch"] for r in rows] == epochs


def test_license_tier_at_batch_active_key_mixed_epochs(app):
    """Active key: perspectives before ``exp`` -> tier surfaces; after
    ``exp`` -> ``None``. Batch preserves per-row ordering."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    rows = app.lic.license_tier_at_batch(epochs)
    assert [r["tier"] for r in rows] == ["pro", "pro", None, None]
    assert [r["epoch"] for r in rows] == epochs


def test_license_tier_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`license_tier_at` -- the batch cannot
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
    rows = app.lic.license_tier_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["tier"] == app.lic.license_tier_at(epoch), epoch


def test_license_tier_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> tier surfaces at every row."""
    _write_perpetual(app)
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.license_tier_at_batch(epochs)
    assert [r["tier"] for r in rows] == ["pro"] * 3


def test_license_tier_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``None`` (time-independent)."""
    _write_bogus(app)
    rows = app.lic.license_tier_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["tier"] for r in rows] == [None] * 3


def test_license_tier_at_batch_lapsed_key_flips_per_row(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` -> tier
    surfaces; at / after ``exp`` -> ``None``. Batch flips per row."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.license_tier_at_batch(
        [now - 20 * 86400, now - 3 * 86400, now]
    )
    assert [r["tier"] for r in rows] == ["pro", None, None]


def test_license_tier_at_batch_bad_epochs_collapse_per_row(app):
    """``bool`` / non-numeric epochs collapse the corresponding row to
    ``tier=None`` with the raw token surfaced in ``epoch`` -- matches the
    never-mis-gate posture the scalar uses for the same inputs."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_tier_at_batch([now, True, "nope", None, now + 3600])
    assert len(rows) == 5
    good_rows = [r for r in rows if isinstance(r["epoch"], int) and r["tier"] == "pro"]
    assert len(good_rows) == 2
    bad_rows = [r for r in rows if r["tier"] is None]
    assert len(bad_rows) == 3


def test_license_tier_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order for
    byte-stable output."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_tier_at_batch([now, now, now + 10, now])
    assert [r["epoch"] for r in rows] == [now, now + 10]


def test_license_tier_at_batch_string_epochs_coerced(app):
    """String tokens that ``int()`` accepts -> coerced and honoured,
    matching the query-string surface (the batch endpoint hands the
    helper stripped tokens)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_tier_at_batch([str(now), str(now + 10)])
    assert [r["tier"] for r in rows] == ["pro", "pro"]


def test_license_tier_at_batch_normalises_casing(app):
    """Tier claim casing is normalised on every row the same way the
    scalar normalises it."""
    tok = app.lic._encode_token(_payload(tier="  PRO  "), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    rows = app.lic.license_tier_at_batch([now, now + 3600])
    assert [r["tier"] for r in rows] == ["pro", "pro"]


def test_license_tier_at_batch_missing_tier_claim_matches_scalar(app):
    """Signed payload with no ``tier`` claim: every row must byte-equal
    the singular :func:`license_tier_at` for the same epoch (which in
    turn pins parity with :func:`license_tier` -- see the scalar test).
    Guards the batch from silently diverging from the scalar on the
    same defect."""
    _write_key_direct(app, exp_delta=30 * 86400, drop_tier=True)
    now = int(time.time())
    epochs = [now, now + 3600, now + 86400]
    rows = app.lic.license_tier_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["tier"] == app.lic.license_tier_at(epoch), epoch


# -- GET /api/license/tier-at -------------------------------------------------


def test_api_tier_at_no_license(app):
    """No license file on disk -> ``tier_at=null``, current-time
    reference fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at?epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier_at"] is None
    assert body["requested_epoch"] == now
    assert body["tier"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_api_tier_at_active_key_now(app):
    """Active key at "now" -> ``tier_at=tier``, snapshot fields intact."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at?epoch={now}")
    body = rv.get_json()
    assert body["tier_at"] == "pro"
    assert body["tier"] == "pro"
    assert body["expires_at"] is not None
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_tier_at_missing_epoch_collapses(app):
    """Missing / non-integer / bool ``epoch`` -> ``tier_at=null`` and
    ``requested_epoch=null`` so a caller cannot silently mis-gate on a
    typo. HTTP status stays 200."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as client:
        for qs in ("", "?epoch=", "?epoch=nope", "?epoch=true"):
            rv = client.get(f"/api/license/tier-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["tier_at"] is None, qs
            assert body["requested_epoch"] is None, qs


def test_api_tier_at_future_after_expiry(app):
    """Future perspective past ``exp`` on an active key -> ``tier_at=null``
    even though ``tier`` (current-time) still surfaces the tier."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at?epoch={epoch}")
    body = rv.get_json()
    assert body["tier_at"] is None
    assert body["tier"] == "pro"


def test_api_tier_at_invalid_signature(app):
    """Bogus-signature file -> ``tier_at=null``. ``has_license=True``
    (a file exists) but ``valid=False``. Time-independent."""
    _write_bogus(app)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at?epoch={int(time.time())}")
    body = rv.get_json()
    assert body["tier_at"] is None
    assert body["tier"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_tier_at_scalar_parity_with_python(app):
    """The endpoint must return exactly what ``license_tier_at`` would
    return for the same epoch."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in [now - 10 * 86400, now, now + 5 * 86400, now + 40 * 86400]:
            rv = client.get(f"/api/license/tier-at?epoch={epoch}")
            body = rv.get_json()
            assert body["tier_at"] == app.lic.license_tier_at(epoch), epoch


# -- GET /api/license/tier-at-batch -------------------------------------------


def test_api_tier_at_batch_missing_epochs_400(app):
    """Missing / blank / only-commas ``epochs=`` -> ``400 missing epochs``
    (matches the sibling ``/api/license/*-at-batch`` endpoints)."""
    with app.app.test_client() as client:
        for qs in ("", "?epochs=", "?epochs=,,"):
            rv = client.get(f"/api/license/tier-at-batch{qs}")
            assert rv.status_code == 400, qs
            assert rv.get_json() == {"error": "missing epochs"}


def test_api_tier_at_batch_no_license(app):
    """No license file on disk -> every row ``tier=null``. Reference
    fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/tier-at-batch?epochs={now},{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "license_tier_at"
    assert body["count"] == 2
    assert [r["tier"] for r in body["rows"]] == [None, None]
    assert body["tier"] is None
    assert body["has_license"] is False


def test_api_tier_at_batch_active_key_flips_per_row(app):
    """Active key: rows before ``exp`` surface tier, rows after ``exp``
    collapse to ``null``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at-batch?epochs={qs}")
    body = rv.get_json()
    assert body["count"] == 4
    assert [r["tier"] for r in body["rows"]] == ["pro", "pro", None, None]
    assert [r["epoch"] for r in body["rows"]] == epochs
    assert body["tier"] == "pro"
    assert body["valid"] is True


def test_api_tier_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with ``/api/license/tier-at?epoch=<n>`` -- the batch
    cannot silently drift from the scalar."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    epochs = [now - 5 * 86400, now, now + 3 * 86400, now + 40 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv_batch = client.get(f"/api/license/tier-at-batch?epochs={qs}")
        rows = rv_batch.get_json()["rows"]
        for row, epoch in zip(rows, epochs):
            rv_scalar = client.get(f"/api/license/tier-at?epoch={epoch}")
            assert row["tier"] == rv_scalar.get_json()["tier_at"], epoch


def test_api_tier_at_batch_perpetual_key(app):
    """Perpetual key -> every row surfaces the tier."""
    _write_perpetual(app)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at-batch?epochs=0,{now},2000000000")
    body = rv.get_json()
    assert [r["tier"] for r in body["rows"]] == ["pro", "pro", "pro"]
    assert body["valid"] is True


def test_api_tier_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``null`` (time-independent)."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/tier-at-batch?epochs=0,{now},2000000000")
    body = rv.get_json()
    assert [r["tier"] for r in body["rows"]] == [None, None, None]
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_tier_at_batch_bad_tokens_collapse_per_row(app):
    """Bad tokens (non-numeric) don't 400 the batch -- they collapse to
    ``tier=null`` rows so a caller can identify the offending entry."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/tier-at-batch?epochs={now},nope,{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["count"] == 3
    good = [r for r in body["rows"] if r["tier"] == "pro"]
    bad = [r for r in body["rows"] if r["tier"] is None]
    assert len(good) == 2 and len(bad) == 1


def test_api_tier_at_batch_shared_snapshot_agreement(app):
    """The current-time reference fields on the batch response must
    byte-equal the sibling ``/api/license/state-at-batch`` fields for
    the same install -- both endpoints share the state snapshot pattern
    (batch's ``expires_at`` / ``has_license`` / ``valid`` come from the
    same underlying ``current_license_info`` / ``license_expires_at``
    read)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_tier = client.get(f"/api/license/tier-at-batch?epochs={now}").get_json()
        rv_state = client.get(f"/api/license/state-at-batch?epochs={now}").get_json()
    assert rv_tier["expires_at"] == rv_state["expires_at"]
    assert rv_tier["has_license"] == rv_state["has_license"]
    assert rv_tier["valid"] == rv_state["valid"]


def test_api_tier_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order --
    matches the underlying batch helper."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/tier-at-batch?epochs={now},{now},{now + 10},{now}"
        )
    body = rv.get_json()
    assert [r["epoch"] for r in body["rows"]] == [now, now + 10]


# -- cross-endpoint agreement -------------------------------------------------


def test_api_tier_at_agrees_with_license_tier_endpoint_at_now(app):
    """At ``epoch=now``, the ``tier_at`` field must byte-equal the
    ``tier`` returned by ``/api/license/tier`` (the current-time
    endpoint). Both derive from the same signed claim -- a UI binding
    both cannot catch them disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as client:
        rv_now = client.get("/api/license/tier").get_json()
        rv_at = client.get(f"/api/license/tier-at?epoch={now}").get_json()
    assert rv_at["tier_at"] == rv_now["tier"]
    assert rv_at["tier"] == rv_now["tier"]
