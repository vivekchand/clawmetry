"""Tests for :func:`clawmetry.license.has_feature_at_batch` and the
paired ``GET /api/license/has-feature-at-batch`` endpoint.

Shared-``feature`` batch sibling of
:func:`clawmetry.license.has_feature_at` / ``/api/license/has-feature-at``.
Where the scalar folds ONE ``(feature, epoch)`` pair to ONE bool, this
batch preserves per-value rows for a fixed ``feature`` and a sequence of
perspective epochs so a scheduled-audit tile answering "was this node
entitled to feature <X> on each of these audit dates?" hydrates in ONE
round-trip instead of fanning out N scalar calls. Per-row parity with
the singular scalar (both the helper and the HTTP endpoint) is pinned
so the batch cannot silently drift.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_has_feature_at.py`` /
``tests/test_license_is_state_at_batch.py``.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_has_feature_at.py) ------------------


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

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
        client=flask_app.test_client(),
        lic=_lic,
        priv=priv,
        license_path=license_path,
    )


def _write_direct(app, payload):
    """Bypass :func:`activate` (which refuses expired tokens and phones
    home) and write a raw signed token to the license file. Lets a
    test build any payload shape -- expired, perpetual, features-list
    variants -- without round-tripping through the activation code
    path."""
    tok = app.lic._encode_token(payload, app.priv)
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write(tok)


def _write_bogus(app):
    os.makedirs(os.path.dirname(app.license_path), exist_ok=True)
    with open(app.license_path, "w", encoding="utf-8") as fh:
        fh.write("CLAW1.garbage.garbage")


# -- clawmetry.license.has_feature_at_batch() -------------------------------


def test_has_feature_at_batch_none_epochs_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`license_features_at_batch` / :func:`is_state_at_batch`."""
    assert app.lic.has_feature_at_batch("alerts", None) == []


def test_has_feature_at_batch_non_iterable_epochs_returns_empty(app):
    """Non-iterable ``epochs`` -> ``[]`` rather than a crash. Matches
    the shared pre-parser."""
    assert app.lic.has_feature_at_batch("alerts", 42) == []


def test_has_feature_at_batch_empty_epochs_returns_empty(app):
    """Empty iterable -> ``[]`` regardless of ``feature``."""
    assert app.lic.has_feature_at_batch("alerts", []) == []
    assert app.lic.has_feature_at_batch("", ()) == []


def test_has_feature_at_batch_none_feature_all_false(app):
    """``feature=None`` collapses every row to ``has_feature=False``
    while preserving row slots (matches never-mis-gate scalar
    posture)."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(None, [now, now + 86400])
    assert len(rows) == 2
    assert [r["has_feature"] for r in rows] == [False, False]


def test_has_feature_at_batch_empty_feature_all_false(app):
    """Empty / whitespace-only ``feature`` collapses every row to
    ``has_feature=False``. Preserves row slots so output length still
    matches N."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch("", [now, now + 86400])
    assert [r["has_feature"] for r in rows] == [False, False]
    rows2 = app.lic.has_feature_at_batch("   ", [now])
    assert [r["has_feature"] for r in rows2] == [False]


def test_has_feature_at_batch_no_license_all_false(app):
    """No license file on disk -> every good-epoch row ``False``
    regardless of feature. Mirrors :func:`has_feature_at`'s no-license
    branch."""
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts", [0, now, 2_000_000_000]
    )
    assert [r["has_feature"] for r in rows] == [False, False, False]


def test_has_feature_at_batch_active_key_claimed(app):
    """Active key + feature the token itemises: every row inside the
    key's ``exp`` window fires ``True``; rows past ``exp`` fire
    ``False`` (matches ``license_features_at`` boundary)."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    now = int(time.time())
    exp = now + 30 * 86400
    rows = app.lic.has_feature_at_batch(
        "alerts", [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    assert [r["has_feature"] for r in rows] == [True, True, False, False]


def test_has_feature_at_batch_active_key_unclaimed(app):
    """Active key + feature the token does NOT itemise: every row
    ``False``, even inside the ``exp`` window. Predicate never mis-
    grants a feature the token omits."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "selfevolve", [now - 86400, now, now + 86400]
    )
    assert [r["has_feature"] for r in rows] == [False, False, False]


def test_has_feature_at_batch_lapsed_key_pre_lapse_true(app):
    """A key whose ``exp`` has already passed at "now": perspective
    epochs BEFORE the lapse fire ``True`` on a claimed feature;
    perspective epochs AT-OR-AFTER the lapse fire ``False``. Answers
    "was I entitled to <feature> BEFORE the lapse?" without the caller
    eyeballing the token."""
    _write_direct(app, _payload(exp_delta=-5 * 86400, features=("alerts",)))
    now = int(time.time())
    exp = now - 5 * 86400
    rows = app.lic.has_feature_at_batch(
        "alerts", [exp - 10 * 86400, exp - 1, exp, now]
    )
    assert [r["has_feature"] for r in rows] == [True, True, False, False]


def test_has_feature_at_batch_perpetual_key(app):
    """Perpetual (no ``exp``) key -> every good-epoch row fires
    ``True`` on a claimed feature, ``False`` on an unclaimed one."""
    _write_direct(app, _payload(drop_exp=True, features=("alerts",)))
    for epoch in (0, int(time.time()), 2_000_000_000):
        rows = app.lic.has_feature_at_batch("alerts", [epoch])
        assert [r["has_feature"] for r in rows] == [True], epoch
        rows2 = app.lic.has_feature_at_batch("selfevolve", [epoch])
        assert [r["has_feature"] for r in rows2] == [False], epoch


def test_has_feature_at_batch_invalid_signature_all_false(app):
    """Bogus-signature file -> every row ``False`` at every epoch.
    Never trust an unsigned body -- an attacker who could edit the
    payload could otherwise smuggle any id into the ``features`` list
    for any perspective epoch."""
    _write_bogus(app)
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts", [0, now, 2_000_000_000]
    )
    assert [r["has_feature"] for r in rows] == [False, False, False]


def test_has_feature_at_batch_missing_features_claim(app):
    """A signature-valid key with NO ``features`` claim -> every row
    ``False``. The scalar collapses this branch to ``[]`` and an empty
    list can't contain anything."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts", [now - 86400, now, now + 86400]
    )
    assert [r["has_feature"] for r in rows] == [False, False, False]


def test_has_feature_at_batch_non_list_features_claim(app):
    """Malformed ``features`` claim (non-list) -> every row ``False``.
    The accessor normalises this branch to ``[]`` -> empty list ->
    membership always fails."""
    _write_direct(app, _payload(features_value="alerts,fleet"))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch("alerts", [now])
    assert [r["has_feature"] for r in rows] == [False]


def test_has_feature_at_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the batch pre-
    parser's ``int()`` coercion)."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts", [str(now), str(now + 86400)]
    )
    assert [r["has_feature"] for r in rows] == [True, True]


def test_has_feature_at_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts",
        [now, now + 100, now, str(now + 100), now + 200],
    )
    assert [r["epoch"] for r in rows] == [now, now + 100, now + 200]


def test_has_feature_at_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` -> ``has_feature=false``
    (matches the scalar's rejection of unusable epochs). Rows still
    keep their slots so output length matches N."""
    _write_direct(app, _payload(features=("alerts",)))
    rows = app.lic.has_feature_at_batch(
        "alerts", [True, False, None, "garbage", ""]
    )
    # Each bad token keeps its own bucket (matches
    # _license_epoch_batch_keys semantics -- empty and None distinguished
    # by id()).
    assert len(rows) == 5
    assert all(r["has_feature"] is False for r in rows)


def test_has_feature_at_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in per the shared-``feature`` semantics."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch(
        "alerts", [now - 86400, "garbage", now, None]
    )
    assert len(rows) == 4
    assert [r["has_feature"] for r in rows] == [True, False, True, False]


def test_has_feature_at_batch_feature_case_insensitive(app):
    """``feature`` is normalised case-insensitively after strip,
    matching the scalar's ``.strip().lower()`` treatment."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    for variant in ("Alerts", "ALERTS", "  alerts  ", "AlErTs"):
        rows = app.lic.has_feature_at_batch(variant, [now])
        assert [r["has_feature"] for r in rows] == [True], variant


def test_has_feature_at_batch_token_case_normalised(app):
    """Server-side casing on the ``features`` claim normalises before
    the membership check -- ``"Alerts"`` on the token still matches
    ``"alerts"`` in the query. Same normalisation
    :func:`license_features_at` runs on the token side."""
    _write_direct(app, _payload(features=(" Alerts ", "FLEET")))
    now = int(time.time())
    rows = app.lic.has_feature_at_batch("alerts", [now])
    assert [r["has_feature"] for r in rows] == [True]
    rows2 = app.lic.has_feature_at_batch("fleet", [now])
    assert [r["has_feature"] for r in rows2] == [True]


def test_has_feature_at_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`has_feature_at` -- pin every row and
    every feature combination against the singular helper."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts", "fleet")))
    now = int(time.time())
    epochs = [
        now - 10 * 86400,
        now - 1,
        now,
        now + 1,
        now + 40 * 86400,
    ]
    for feature in ("alerts", "fleet", "selfevolve", ""):
        rows = app.lic.has_feature_at_batch(feature, epochs)
        for row, epoch in zip(rows, epochs):
            assert row["has_feature"] == app.lic.has_feature_at(
                feature, epoch
            ), (feature, epoch)


def test_has_feature_at_batch_boundary_agrees_with_has_feature(app):
    """At ``epoch = now``, the batch must agree with
    :func:`has_feature` for the same install and the same requested
    ``feature`` (boundary parity contract, matches the scalar's
    :func:`has_feature_at` -> :func:`has_feature` contract)."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    for feature in ("alerts", "fleet", "selfevolve"):
        rows = app.lic.has_feature_at_batch(feature, [now])
        assert rows[0]["has_feature"] == app.lic.has_feature(
            feature
        ), feature


def test_has_feature_at_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`has_feature_at` ->
    ``has_feature=False`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_feature, _epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "has_feature_at", _boom)
    rows = _lic.has_feature_at_batch(
        "alerts", [1_700_000_000, 1_800_000_000]
    )
    assert [r["has_feature"] for r in rows] == [False, False]
    assert len(rows) == 2


# -- GET /api/license/has-feature-at-batch ----------------------------------


def test_endpoint_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints)."""
    resp = app.client.get(
        "/api/license/has-feature-at-batch?feature=alerts"
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    r1 = app.client.get(
        "/api/license/has-feature-at-batch?feature=alerts&epochs="
    )
    r2 = app.client.get(
        "/api/license/has-feature-at-batch?feature=alerts&epochs=,,,"
    )
    assert r1.status_code == 400
    assert r2.status_code == 400


def test_endpoint_missing_feature_degrades_not_400(app):
    """``?feature=`` absent (with valid ``?epochs=``) does NOT 4xx --
    every row collapses to ``has_feature=false`` per the shared-
    ``feature`` posture. A stale UI shouldn't hide the whole batch
    behind a typo."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?epochs={now}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "has_feature_at"
    assert data["count"] == 1
    assert data["requested_feature"] == ""
    assert data["rows"][0]["has_feature"] is False


def test_endpoint_empty_feature_all_false(app):
    """Empty / whitespace-only ``feature`` -> every row false;
    ``requested_feature`` normalised to ``""``."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=%20%20&epochs={now}"
    )
    data = resp.get_json()
    assert data["requested_feature"] == ""
    assert [r["has_feature"] for r in data["rows"]] == [False]


def test_endpoint_no_license(app):
    """No license file -> every row ``false``, HTTP 200, current-time
    snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now},0"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "has_feature_at"
    assert data["requested_feature"] == "alerts"
    assert data["count"] == 2
    assert [r["has_feature"] for r in data["rows"]] == [False, False]
    assert data["features"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_active_key_claimed(app):
    """Active key + feature the token itemises: rows inside the
    ``exp`` window fire ``true``; rows at-or-after ``exp`` fire
    ``false``. Envelope carries the current-time snapshot."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts", "fleet")))
    now = int(time.time())
    exp = now + 30 * 86400
    csv = ",".join(
        str(e) for e in [exp - 10 * 86400, exp - 1, exp, exp + 1]
    )
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={csv}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "has_feature_at"
    assert data["requested_feature"] == "alerts"
    assert data["count"] == 4
    assert [r["has_feature"] for r in data["rows"]] == [
        True,
        True,
        False,
        False,
    ]
    assert data["features"] == ["alerts", "fleet"]
    assert data["has_license"] is True
    assert data["valid"] is True
    assert data["expires_at"] == exp


def test_endpoint_active_key_unclaimed(app):
    """Active key + feature NOT itemised -> every row ``false`` even
    inside the ``exp`` window, but ``features`` still populated on the
    envelope so a UI can render 'you're on Pro but that feature is not
    on your key' copy off ONE call."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=selfevolve&epochs={now - 86400},{now},{now + 86400}"
    )
    data = resp.get_json()
    assert [r["has_feature"] for r in data["rows"]] == [
        False,
        False,
        False,
    ]
    assert data["features"] == ["alerts", "fleet"]
    assert data["valid"] is True
    assert data["requested_feature"] == "selfevolve"


def test_endpoint_feature_case_normalised_in_echo(app):
    """``requested_feature`` is normalised (stripped + lowered) in the
    echo field, matching the scalar endpoint's echo shape."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=%20Alerts%20&epochs={now}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_feature"] == "alerts"
    assert [r["has_feature"] for r in data["rows"]] == [True]


def test_endpoint_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric tokens -> ``has_feature=false``. Good
    rows still resolve alongside; rows preserve slots so length
    matches N."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs=garbage,{now - 86400}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["has_feature"] for r in data["rows"]] == [False, True]


def test_endpoint_dedupe_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output. Matches the shared batch pre-parser."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now},{now + 100},{now},{now + 100}"
    )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [now, now + 100]


def test_endpoint_perpetual_key(app):
    """Perpetual (no ``exp``) key -> every good-epoch row fires
    ``true`` on a claimed feature. Envelope carries a valid-install
    snapshot with ``expires_at=null``."""
    _write_direct(app, _payload(drop_exp=True, features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs=0,{now},2000000000"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 3
    assert [r["has_feature"] for r in data["rows"]] == [True, True, True]
    assert data["has_license"] is True
    assert data["expires_at"] is None


def test_endpoint_invalid_signature(app):
    """Bogus-signature file -> every row ``false``, ``features=null``
    on the envelope, ``has_license=true`` (the file IS on disk),
    ``valid=false``. Matches the scalar endpoint's error branch."""
    _write_bogus(app)
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now},0,2000000000"
    )
    data = resp.get_json()
    assert [r["has_feature"] for r in data["rows"]] == [False, False, False]
    assert data["features"] is None
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_missing_features_claim(app):
    """A signature-valid key without a ``features`` claim -> every
    row ``false``, but ``valid=true`` on the envelope. A UI can
    distinguish 'valid key with nothing itemised' from 'no key'
    without a second call."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now}"
    )
    data = resp.get_json()
    assert [r["has_feature"] for r in data["rows"]] == [False]
    assert data["valid"] is True
    assert data["has_license"] is True


def test_endpoint_per_row_parity_with_scalar(app):
    """Per-row parity with the singular
    ``/api/license/has-feature-at?feature=<X>&epoch=<n>`` endpoint --
    pin every row and every feature combination against the scalar
    endpoint."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts", "fleet")))
    now = int(time.time())
    epochs = [
        now - 10 * 86400,
        now - 1,
        now,
        now + 1,
        now + 40 * 86400,
    ]
    csv = ",".join(str(e) for e in epochs)
    for feature in ("alerts", "fleet", "selfevolve"):
        batch = app.client.get(
            f"/api/license/has-feature-at-batch?feature={feature}&epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = app.client.get(
                f"/api/license/has-feature-at?feature={feature}&epoch={epoch}"
            ).get_json()
            assert row["has_feature"] == scalar["has_feature_at"], (
                feature,
                epoch,
            )


def test_endpoint_boundary_agrees_with_has_feature_endpoint(app):
    """At ``epoch = now``, the batch must agree with the "now"
    ``/api/license/has-feature`` sibling endpoint per feature. Pins
    the boundary parity contract at the HTTP layer."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    for feature in ("alerts", "fleet", "selfevolve"):
        batch = app.client.get(
            f"/api/license/has-feature-at-batch?feature={feature}&epochs={now}"
        ).get_json()
        now_body = app.client.get(
            f"/api/license/has-feature?feature={feature}"
        ).get_json()
        assert (
            batch["rows"][0]["has_feature"] == now_body["has_feature"]
        ), feature


def test_endpoint_agrees_with_features_at_batch(app):
    """``/api/license/has-feature-at-batch`` row order MUST align with
    ``/api/license/features-at-batch`` on the same ``?epochs=`` CSV so
    a caller can zip both responses index-for-index and cross-check
    (``has_feature`` iff ``requested_feature`` in ``features``)."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts", "fleet")))
    now = int(time.time())
    exp = now + 30 * 86400
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 5 * 86400]
    csv = ",".join(str(e) for e in epochs)
    features_rows = app.client.get(
        f"/api/license/features-at-batch?epochs={csv}"
    ).get_json()["rows"]
    for feature in ("alerts", "fleet", "selfevolve"):
        match_rows = app.client.get(
            f"/api/license/has-feature-at-batch?feature={feature}&epochs={csv}"
        ).get_json()["rows"]
        for feat_row, match_row in zip(features_rows, match_rows):
            assert feat_row["epoch"] == match_row["epoch"]
            expected = bool(
                isinstance(feat_row["features"], list)
                and feature in feat_row["features"]
            )
            assert match_row["has_feature"] == expected, (
                feature,
                feat_row["epoch"],
            )


def test_endpoint_shared_snapshot_fields_agree_with_siblings(app):
    """Shares the current-time snapshot fields (``features`` /
    ``expires_at`` / ``has_license`` / ``valid``) with the existing
    ``/api/license/features-at{,-batch}`` /
    ``/api/license/has-feature-at`` trio. A UI binding several for the
    same install must not catch them disagreeing on those fields."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    now = int(time.time())
    fa = app.client.get(
        f"/api/license/features-at?epoch={now}"
    ).get_json()
    fb = app.client.get(
        f"/api/license/features-at-batch?epochs={now}"
    ).get_json()
    hf = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    ).get_json()
    hb = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now}"
    ).get_json()
    for key in ("features", "expires_at", "has_license", "valid"):
        assert fa[key] == fb[key] == hf[key] == hb[key], key


def test_endpoint_never_5xxs_on_snapshot_failure(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the OSS-free snapshot fallback + honest
    per-row derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_features_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["features"] is None
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_never_5xxs_on_derive_failure(app, monkeypatch):
    """Even if :func:`has_feature_at_batch` blows up mid-request, the
    endpoint still returns HTTP 200 with the empty-rows envelope."""
    import clawmetry.license as _lic

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "has_feature_at_batch", _boom)
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at-batch?feature=alerts&epochs={now}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["rows"] == []
    assert data["count"] == 0
    assert data["requested_feature"] == "alerts"
