"""Tests for the ``license_features_at(epoch)`` scalar and
``license_features_at_batch(epochs)`` batch helpers on
``clawmetry.license`` and their paired ``/api/license/features-at`` /
``/api/license/features-at-batch`` HTTP endpoints.

The perspective-epoch flavour of the ``license_features`` scalar. Both
derive from the same signed ``features`` claim and refuse the invalid-
signature branch, so they cannot disagree at the boundary when the
perspective epoch equals "now"; on any other epoch these helpers answer
"which features would :func:`license_features` have surfaced evaluated as
of ``epoch``?" without the caller having to snapshot the license state
at that time or compare ``exp`` to a caller-supplied epoch themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_features_accessor.py`` /
``tests/test_license_state_at_scalar.py`` so nothing depends on the
real production signing key or on real filesystem state.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_features_accessor.py) ----------------


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
    tier="pro",
    nodes=3,
    exp_delta=365 * 86400,
    features=("runtimes", "alerts", "fleet"),
    drop_exp=False,
    drop_features=False,
    features_value=None,
):
    """Build a license payload with knobs for every branch under test."""
    now = int(time.time())
    p = {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": list(features),
    }
    if features_value is not None:
        p["features"] = features_value
    if drop_features:
        p.pop("features", None)
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
    monkeypatch.setattr(_lic, "_CONFIG_PATH", str(tmp_path / "config.json"))
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


def _write_direct(app, payload):
    """Bypass :func:`activate` (which refuses expired tokens and phones
    home) and write a raw signed token to the license file."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.license_features_at() ---------------------------------


def test_license_features_at_no_license(app):
    """No license file on disk -> ``None`` regardless of epoch."""
    assert app.lic.license_features_at(int(time.time())) is None
    assert app.lic.license_features_at(0) is None
    assert app.lic.license_features_at(2_000_000_000) is None


def test_license_features_at_now_matches_license_features_active(app):
    """When ``epoch`` equals "now", perspective scalar must agree with
    :func:`license_features` on an active install. Both derive from the
    same signed ``features`` claim, so a UI binding both cannot catch
    them disagreeing at the boundary."""
    _write_direct(app, _payload(features=("runtimes", "alerts", "fleet")))
    now = int(time.time())
    assert app.lic.license_features_at(now) == ["alerts", "fleet", "runtimes"]
    assert app.lic.license_features() == ["alerts", "fleet", "runtimes"]


def test_license_features_at_now_matches_license_features_lapsed(app):
    """Lapsed-key parity: at "now", perspective scalar and base scalar
    must both return ``None`` -- both refuse the expired branch."""
    _write_direct(app, _payload(exp_delta=-5 * 86400))
    now = int(time.time())
    assert app.lic.license_features_at(now) is None
    assert app.lic.license_features() is None


def test_license_features_at_future_epoch_before_expiry(app):
    """Future perspective still before ``exp`` -> features surface."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    epoch = int(time.time()) + 10 * 86400
    assert app.lic.license_features_at(epoch) == ["alerts", "fleet", "runtimes"]


def test_license_features_at_future_epoch_after_expiry(app):
    """Future perspective AFTER ``exp`` on an active key -> ``None``
    (the key WILL be expired at that perspective). Prospective "will we
    still be entitled at the next audit?" scenario."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.license_features_at(epoch) is None


def test_license_features_at_past_epoch_still_active(app):
    """Perspective BEFORE now on an active key -> features surface (the
    key was not yet expired then)."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.license_features_at(epoch) == ["alerts", "fleet", "runtimes"]


def test_license_features_at_lapsed_key_pre_lapse_epoch_surfaces_features(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    features surface (retrospective "which were unlocked on <date>?").
    At "now" (past ``exp``) -> ``None``."""
    _write_direct(app, _payload(exp_delta=-5 * 86400))  # exp = now - 5d
    now = int(time.time())
    assert app.lic.license_features_at(now - 20 * 86400) == [
        "alerts",
        "fleet",
        "runtimes",
    ]
    assert app.lic.license_features_at(now - 3 * 86400) is None
    assert app.lic.license_features_at(now) is None


def test_license_features_at_exact_exp_boundary(app):
    """At the exact ``exp`` second, features must collapse to ``None``
    -- the ``<= epoch`` cutoff matches :func:`license_state_at`'s
    ``exp <= epoch`` boundary."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    info = app.lic.current_license_info()
    exp_epoch = int(info["exp"])
    assert app.lic.license_features_at(exp_epoch - 1) == [
        "alerts",
        "fleet",
        "runtimes",
    ]
    assert app.lic.license_features_at(exp_epoch) is None
    assert app.lic.license_features_at(exp_epoch + 1) is None


def test_license_features_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> features surface at every epoch."""
    _write_direct(app, _payload(drop_exp=True))
    assert app.lic.license_features_at(0) == ["alerts", "fleet", "runtimes"]
    assert app.lic.license_features_at(int(time.time())) == [
        "alerts",
        "fleet",
        "runtimes",
    ]
    assert app.lic.license_features_at(2_000_000_000) == [
        "alerts",
        "fleet",
        "runtimes",
    ]


def test_license_features_at_invalid_signature(app):
    """Bogus-signature file -> ``None`` regardless of epoch (time-
    independent, matches :func:`license_features`)."""
    _write_bogus(app)
    assert app.lic.license_features_at(0) is None
    assert app.lic.license_features_at(int(time.time())) is None
    assert app.lic.license_features_at(2_000_000_000) is None


def test_license_features_at_normalises_case_and_whitespace(app):
    """Server-side typos in casing / whitespace on the feature ids
    normalise here, so gates comparing to lower-cased constants don't
    silently miss."""
    _write_direct(app, _payload(features=(" Alerts ", "FLEET", "runtimes ")))
    assert app.lic.license_features_at(int(time.time())) == [
        "alerts",
        "fleet",
        "runtimes",
    ]


def test_license_features_at_dedup(app):
    """Duplicates on the claim (server-side typo) collapse to one
    normalised id."""
    _write_direct(
        app, _payload(features=("alerts", "ALERTS", "alerts ", "fleet"))
    )
    assert app.lic.license_features_at(int(time.time())) == ["alerts", "fleet"]


def test_license_features_at_missing_claim_returns_empty_list(app):
    """Valid signed key with the ``features`` claim omitted -> ``[]``
    (valid license, zero features itemised) -- distinct from ``None``
    which means no valid license at all."""
    _write_direct(app, _payload(drop_features=True))
    assert app.lic.license_features_at(int(time.time())) == []


def test_license_features_at_non_list_claim_returns_empty_list(app):
    """Server-side typo where the ``features`` claim is not a list ->
    ``[]``, matching :func:`license_features`. A non-list body cannot
    smuggle entitlement through, but the key is still valid so the row
    isn't ``None``."""
    _write_direct(app, _payload(features_value="alerts"))
    assert app.lic.license_features_at(int(time.time())) == []


def test_license_features_at_ignores_non_string_entries(app):
    """Non-string entries on the claim are skipped defensively. A legit
    server-side typo (integer feature id) shouldn't blow up the tile."""
    _write_direct(
        app, _payload(features_value=["alerts", 123, None, "fleet", ""])
    )
    assert app.lic.license_features_at(int(time.time())) == ["alerts", "fleet"]


def test_license_features_at_bool_epoch_refused(app):
    """``bool`` is an ``int`` subclass but must be refused so a caller
    passing ``True`` / ``False`` gets ``None`` back, not a spurious
    "was feature X entitled at epoch 1?" answer."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    assert app.lic.license_features_at(True) is None
    assert app.lic.license_features_at(False) is None


def test_license_features_at_non_numeric_epoch(app):
    """Non-numeric epoch -> ``None`` so a caller cannot silently mis-
    gate on a typo -- conservative fallback since ``None`` implies no
    entitlement."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    assert app.lic.license_features_at("not-a-number") is None
    assert app.lic.license_features_at(None) is None
    assert app.lic.license_features_at([]) is None


def test_license_features_at_string_epoch_coerced(app):
    """String epoch that ``int()`` accepts -> coerced and honoured,
    matching :func:`license_state_at`."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    assert app.lic.license_features_at(str(now)) == [
        "alerts",
        "fleet",
        "runtimes",
    ]


def test_license_features_at_never_raises(app, monkeypatch):
    """Any underlying failure -> ``None`` -- never propagates."""
    _write_direct(app, _payload(exp_delta=30 * 86400))

    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(app.lic, "current_license_info", _boom)
    assert app.lic.license_features_at(int(time.time())) is None


# -- clawmetry.license.license_features_at_batch() ---------------------------


def test_license_features_at_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Mirrors the never-raise posture of
    the sibling per-value axis batches."""
    assert app.lic.license_features_at_batch(None) == []


def test_license_features_at_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` (an int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert app.lic.license_features_at_batch(42) == []


def test_license_features_at_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.license_features_at_batch([]) == []
    assert app.lic.license_features_at_batch(()) == []


def test_license_features_at_batch_no_license(app):
    """No license file on disk -> every row ``features=None`` regardless
    of epoch. Time-independent, matches the scalar."""
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.license_features_at_batch(epochs)
    assert [r["features"] for r in rows] == [None] * 3
    assert [r["epoch"] for r in rows] == epochs


def test_license_features_at_batch_active_key_mixed_epochs(app):
    """Active key: perspectives before ``exp`` -> features surface;
    after ``exp`` -> ``None``. Batch preserves per-row ordering."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    rows = app.lic.license_features_at_batch(epochs)
    assert [r["features"] for r in rows] == [
        ["alerts", "fleet", "runtimes"],
        ["alerts", "fleet", "runtimes"],
        None,
        None,
    ]
    assert [r["epoch"] for r in rows] == epochs


def test_license_features_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`license_features_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    epochs = [
        now - 10 * 86400,
        now,
        now + 5 * 86400,
        now + 40 * 86400,
        now + 200 * 86400,
    ]
    rows = app.lic.license_features_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["features"] == app.lic.license_features_at(epoch), epoch


def test_license_features_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> features surface at every row."""
    _write_direct(app, _payload(drop_exp=True))
    epochs = [0, int(time.time()), 2_000_000_000]
    rows = app.lic.license_features_at_batch(epochs)
    assert [r["features"] for r in rows] == [
        ["alerts", "fleet", "runtimes"]
    ] * 3


def test_license_features_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``None`` (time-independent)."""
    _write_bogus(app)
    rows = app.lic.license_features_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["features"] for r in rows] == [None] * 3


def test_license_features_at_batch_lapsed_key_flips_per_row(app):
    """Lapsed-but-signed key at a perspective BEFORE its ``exp`` ->
    features surface; at / after ``exp`` -> ``None``. Batch flips per
    row."""
    _write_direct(app, _payload(exp_delta=-5 * 86400))  # exp = now - 5d
    now = int(time.time())
    rows = app.lic.license_features_at_batch(
        [now - 20 * 86400, now - 3 * 86400, now]
    )
    assert [r["features"] for r in rows] == [
        ["alerts", "fleet", "runtimes"],
        None,
        None,
    ]


def test_license_features_at_batch_missing_claim_returns_empty_list_row(app):
    """Valid signed key with the ``features`` claim omitted -> per-row
    ``features=[]`` (valid license, zero features itemised) -- distinct
    from ``None`` which means no valid license at all."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    rows = app.lic.license_features_at_batch([now, now + 3600])
    assert [r["features"] for r in rows] == [[], []]


def test_license_features_at_batch_bad_epochs_collapse_per_row(app):
    """``bool`` / non-numeric epochs collapse the corresponding row to
    ``features=None`` with the raw token surfaced in ``epoch`` --
    matches the never-mis-gate posture the scalar uses for the same
    inputs."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    rows = app.lic.license_features_at_batch(
        [now, True, "nope", None, now + 3600]
    )
    assert len(rows) == 5
    good_rows = [
        r
        for r in rows
        if isinstance(r["epoch"], int) and r["features"] == [
            "alerts",
            "fleet",
            "runtimes",
        ]
    ]
    assert len(good_rows) == 2
    bad_rows = [r for r in rows if r["features"] is None]
    assert len(bad_rows) == 3


def test_license_features_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order for
    byte-stable output."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    rows = app.lic.license_features_at_batch([now, now, now + 10, now])
    assert [r["epoch"] for r in rows] == [now, now + 10]


def test_license_features_at_batch_string_epochs_coerced(app):
    """String tokens that ``int()`` accepts -> coerced and honoured,
    matching the query-string surface (the batch endpoint hands the
    helper stripped tokens)."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    rows = app.lic.license_features_at_batch([str(now), str(now + 10)])
    assert [r["features"] for r in rows] == [
        ["alerts", "fleet", "runtimes"],
        ["alerts", "fleet", "runtimes"],
    ]


def test_license_features_at_batch_never_raises(app, monkeypatch):
    """Any per-row underlying failure of :func:`license_features_at` ->
    ``features=None`` for THAT row. The batch never propagates."""
    _write_direct(app, _payload(exp_delta=30 * 86400))

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(app.lic, "license_features_at", _boom)
    rows = app.lic.license_features_at_batch([1_700_000_000, 1_700_000_010])
    assert [r["features"] for r in rows] == [None, None]
    assert len(rows) == 2


def test_license_features_at_batch_bytestable_across_calls(app):
    """Same input -> byte-stable output across repeated calls (dedup
    preserves first-seen order)."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    a = app.lic.license_features_at_batch([now, now + 10, now + 20])
    b = app.lic.license_features_at_batch([now, now + 10, now + 20])
    assert a == b


# -- GET /api/license/features-at --------------------------------------------


def test_api_features_at_no_license(app):
    """No license file on disk -> ``features_at=null``, current-time
    reference fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at?epoch={now}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["features_at"] is None
    assert body["requested_epoch"] == now
    assert body["features"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_api_features_at_active_key_now(app):
    """Active key at "now" -> ``features_at=features``, snapshot fields
    intact."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at?epoch={now}")
    body = rv.get_json()
    assert body["features_at"] == ["alerts", "fleet", "runtimes"]
    assert body["features"] == ["alerts", "fleet", "runtimes"]
    assert body["expires_at"] is not None
    assert body["has_license"] is True
    assert body["valid"] is True


def test_api_features_at_missing_epoch_collapses(app):
    """Missing / non-integer / bool ``epoch`` -> ``features_at=null``
    and ``requested_epoch=null`` so a caller cannot silently mis-gate on
    a typo. HTTP status stays 200."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    with app.app.test_client() as client:
        for qs in ("", "?epoch=", "?epoch=nope", "?epoch=true"):
            rv = client.get(f"/api/license/features-at{qs}")
            assert rv.status_code == 200, qs
            body = rv.get_json()
            assert body["features_at"] is None, qs
            assert body["requested_epoch"] is None, qs


def test_api_features_at_future_after_expiry(app):
    """Future perspective past ``exp`` on an active key ->
    ``features_at=null`` even though ``features`` (current-time) still
    surfaces the list."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at?epoch={epoch}")
    body = rv.get_json()
    assert body["features_at"] is None
    assert body["features"] == ["alerts", "fleet", "runtimes"]


def test_api_features_at_invalid_signature(app):
    """Bogus-signature file -> ``features_at=null``. ``has_license=True``
    (a file exists) but ``valid=False``. Time-independent."""
    _write_bogus(app)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at?epoch={int(time.time())}")
    body = rv.get_json()
    assert body["features_at"] is None
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_features_at_missing_claim_returns_empty_list(app):
    """Valid signed key with the ``features`` claim omitted ->
    ``features_at=[]`` (distinct from ``null``)."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at?epoch={now}")
    body = rv.get_json()
    assert body["features_at"] == []
    assert body["features"] == []


def test_api_features_at_scalar_parity_with_python(app):
    """The endpoint must return exactly what ``license_features_at``
    would return for the same epoch."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        for epoch in [now - 10 * 86400, now, now + 5 * 86400, now + 40 * 86400]:
            rv = client.get(f"/api/license/features-at?epoch={epoch}")
            body = rv.get_json()
            assert body["features_at"] == app.lic.license_features_at(epoch), epoch


# -- GET /api/license/features-at-batch --------------------------------------


def test_api_features_at_batch_missing_epochs_400(app):
    """Missing / blank / only-commas ``epochs=`` -> ``400 missing
    epochs`` (matches the sibling ``/api/license/*-at-batch`` endpoints)."""
    with app.app.test_client() as client:
        for qs in ("", "?epochs=", "?epochs=,,"):
            rv = client.get(f"/api/license/features-at-batch{qs}")
            assert rv.status_code == 400, qs
            assert rv.get_json() == {"error": "missing epochs"}


def test_api_features_at_batch_no_license(app):
    """No license file on disk -> every row ``features=null``. Reference
    fields all reflect the OSS-free branch."""
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/features-at-batch?epochs={now},{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "license_features_at"
    assert body["count"] == 2
    assert [r["features"] for r in body["rows"]] == [None, None]
    assert body["features"] is None
    assert body["has_license"] is False


def test_api_features_at_batch_active_key_flips_per_row(app):
    """Active key: rows before ``exp`` surface features, rows after
    ``exp`` collapse to ``null``."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    epochs = [now, now + 10 * 86400, now + 60 * 86400, now + 90 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at-batch?epochs={qs}")
    body = rv.get_json()
    assert body["count"] == 4
    assert [r["features"] for r in body["rows"]] == [
        ["alerts", "fleet", "runtimes"],
        ["alerts", "fleet", "runtimes"],
        None,
        None,
    ]
    assert [r["epoch"] for r in body["rows"]] == epochs
    assert body["features"] == ["alerts", "fleet", "runtimes"]
    assert body["valid"] is True


def test_api_features_at_batch_per_row_parity_with_scalar_endpoint(app):
    """Per-row parity with ``/api/license/features-at?epoch=<n>`` -- the
    batch cannot silently drift from the scalar."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    epochs = [now - 5 * 86400, now, now + 3 * 86400, now + 40 * 86400]
    qs = ",".join(str(e) for e in epochs)
    with app.app.test_client() as client:
        rv_batch = client.get(f"/api/license/features-at-batch?epochs={qs}")
        rows = rv_batch.get_json()["rows"]
        for row, epoch in zip(rows, epochs):
            rv_scalar = client.get(f"/api/license/features-at?epoch={epoch}")
            assert row["features"] == rv_scalar.get_json()["features_at"], epoch


def test_api_features_at_batch_perpetual_key(app):
    """Perpetual key -> every row surfaces the features list."""
    _write_direct(app, _payload(drop_exp=True))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/features-at-batch?epochs=0,{now},2000000000"
        )
    body = rv.get_json()
    assert [r["features"] for r in body["rows"]] == [
        ["alerts", "fleet", "runtimes"]
    ] * 3
    assert body["valid"] is True


def test_api_features_at_batch_invalid_signature(app):
    """Bogus-signature file -> every row ``null`` (time-independent)."""
    _write_bogus(app)
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/features-at-batch?epochs=0,{now},2000000000"
        )
    body = rv.get_json()
    assert [r["features"] for r in body["rows"]] == [None, None, None]
    assert body["has_license"] is True
    assert body["valid"] is False


def test_api_features_at_batch_bad_tokens_collapse_per_row(app):
    """Bad tokens (non-numeric) don't 400 the batch -- they collapse to
    ``features=null`` rows so a caller can identify the offending
    entry."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/features-at-batch?epochs={now},nope,{now + 3600}"
        )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["count"] == 3
    good = [r for r in body["rows"] if r["features"] == [
        "alerts",
        "fleet",
        "runtimes",
    ]]
    bad = [r for r in body["rows"] if r["features"] is None]
    assert len(good) == 2 and len(bad) == 1


def test_api_features_at_batch_missing_claim_row(app):
    """Valid signed key with the ``features`` claim omitted -> per-row
    ``features=[]`` on the endpoint, matching the scalar."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(f"/api/license/features-at-batch?epochs={now}")
    body = rv.get_json()
    assert body["rows"][0]["features"] == []


def test_api_features_at_batch_shared_snapshot_agreement(app):
    """The current-time reference fields on the batch response must
    byte-equal the sibling ``/api/license/state-at-batch`` fields for
    the same install -- both endpoints share the state snapshot pattern
    (batch's ``expires_at`` / ``has_license`` / ``valid`` come from the
    same underlying ``current_license_info`` / ``license_expires_at``
    read)."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        rv_feats = client.get(
            f"/api/license/features-at-batch?epochs={now}"
        ).get_json()
        rv_state = client.get(
            f"/api/license/state-at-batch?epochs={now}"
        ).get_json()
    assert rv_feats["expires_at"] == rv_state["expires_at"]
    assert rv_feats["has_license"] == rv_state["has_license"]
    assert rv_feats["valid"] == rv_state["valid"]


def test_api_features_at_batch_dedup_preserves_first_seen(app):
    """Duplicate epochs are dropped preserving first-seen order --
    matches the underlying batch helper."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        rv = client.get(
            f"/api/license/features-at-batch?epochs={now},{now},{now + 10},{now}"
        )
    body = rv.get_json()
    assert [r["epoch"] for r in body["rows"]] == [now, now + 10]


# -- cross-endpoint agreement -------------------------------------------------


def test_api_features_at_agrees_with_features_endpoint_at_now(app):
    """At ``epoch=now``, the ``features_at`` field must byte-equal the
    ``features`` returned by ``/api/license/features`` (the current-time
    endpoint). Both derive from the same signed claim -- a UI binding
    both cannot catch them disagreeing at the boundary."""
    _write_direct(app, _payload(exp_delta=30 * 86400))
    now = int(time.time())
    with app.app.test_client() as client:
        rv_now = client.get("/api/license/features").get_json()
        rv_at = client.get(f"/api/license/features-at?epoch={now}").get_json()
    assert rv_at["features_at"] == rv_now["features"]
    assert rv_at["features"] == rv_now["features"]
