"""Tests for the ``is_license_valid_at(epoch)`` scalar helper on
``clawmetry.license``, the paired ``is_license_valid_at_batch(epochs)``
batch helper, and the two matching HTTP endpoints
``GET /api/license/is-valid-at`` and
``GET /api/license/is-valid-at-batch``.

The perspective-epoch flavour of the ``is_license_valid`` entitlement
gate. Both derive from the same signed ``exp`` claim so they cannot
disagree at the boundary when the perspective epoch equals "now"; on
any other epoch this helper answers "would this node have been entitled
at ``epoch``?" without the caller having to snapshot the license state
at that time or fold ``exp`` against a specific epoch themselves.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + LICENSE_PATH, mirroring
``tests/test_license_is_expired_at.py`` and
``tests/test_license_is_expiring_at_batch.py`` so nothing depends on the
real production signing key or on real filesystem state.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers (mirror test_license_is_expired_at.py) --------------------


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


# -- clawmetry.license.is_license_valid_at() ---------------------------------


def test_is_license_valid_at_no_license(app):
    """No license file on disk -> False (nothing to trust)."""
    assert app.lic.is_license_valid_at(int(time.time())) is False
    assert app.lic.is_license_valid_at(0) is False
    assert app.lic.is_license_valid_at(2_000_000_000) is False


def test_is_license_valid_at_now_matches_is_license_valid_on_active(app):
    """When ``epoch`` equals "now", the perspective-epoch gate must
    agree with :func:`is_license_valid` on the same install. Both derive
    from the same signed ``exp`` claim through :func:`license_state_at`
    / :func:`current_license_info`, so a UI binding both cannot catch
    them disagreeing at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    assert app.lic.is_license_valid_at(now) is True
    assert app.lic.is_license_valid() is True


def test_is_license_valid_at_now_matches_is_license_valid_on_lapsed(app):
    """A signed-but-lapsed key must return False on the "now"
    perspective, matching :func:`is_license_valid` -- both use the same
    ``exp <= now`` cutoff so they cannot disagree at the boundary."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    assert app.lic.is_license_valid_at(now) is False
    assert app.lic.is_license_valid() is False


def test_is_license_valid_at_future_before_exp(app):
    """A perspective epoch in the future but still before ``exp`` ->
    True (the key IS entitled at that perspective)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 10 * 86400  # 20 days before exp
    assert app.lic.is_license_valid_at(epoch) is True


def test_is_license_valid_at_future_after_exp(app):
    """A perspective epoch AFTER ``exp`` on an active key -> False (the
    key will NOT be entitled at that perspective). Prospective "will
    this key still be entitled at our next audit?" support scenario."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    assert app.lic.is_license_valid_at(epoch) is False


def test_is_license_valid_at_past_epoch_before_now(app):
    """A perspective epoch BEFORE the current time on an active key ->
    True (the key was entitled then, since exp is even further in the
    future)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) - 10 * 86400
    assert app.lic.is_license_valid_at(epoch) is True


def test_is_license_valid_at_exact_exp_epoch(app):
    """At the exact ``exp`` second, the predicate must NOT fire -- the
    ``exp <= epoch`` boundary in :func:`license_state_at` flips ``state``
    from ``"active"`` to ``"expired"`` at that second inclusive, so
    ``is_license_valid_at(exp)`` is ``False`` while
    ``is_license_valid_at(exp - 1)`` is ``True``. This is the exact
    complement of :func:`is_expired_at` at the boundary."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    assert isinstance(info, dict)
    exp = info["exp"]
    assert app.lic.is_license_valid_at(exp) is False
    assert app.lic.is_license_valid_at(exp - 1) is True


def test_is_license_valid_at_lapsed_key_true_at_pre_lapse_epoch(app):
    """A lapsed-but-signed key evaluated at a perspective epoch BEFORE
    its ``exp`` -> True. The retrospective question "was this key
    entitled a week before it lapsed?" is answerable without special-
    casing the currently-expired branch, exactly like
    :func:`is_expired_at` returns False on that same row."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    # Perspective 20 days before now = 15 days before exp -> still entitled.
    epoch = int(time.time()) - 20 * 86400
    assert app.lic.is_license_valid_at(epoch) is True


def test_is_license_valid_at_perpetual_license(app):
    """Perpetual (no ``exp``) license -> True regardless of perspective
    epoch. Matches :func:`license_state_at`'s "``active`` always" branch
    for perpetual keys (nothing to expire against)."""
    _write_perpetual(app)
    assert app.lic.is_license_valid_at(int(time.time())) is True
    assert app.lic.is_license_valid_at(0) is True
    assert app.lic.is_license_valid_at(2_000_000_000) is True


def test_is_license_valid_at_invalid_signature(app):
    """File on disk but signature bogus -> False on every epoch. An
    unsigned body is untrusted whatever the perspective. Deliberately
    the same False verdict as :func:`is_expired_at` on this branch --
    both fold to False, but "not expired" is NOT the same as "entitled"
    on an unsigned body, and callers must distinguish the two via
    :func:`has_license` / :func:`license_state_at`."""
    _write_bogus(app)
    assert app.lic.is_license_valid_at(int(time.time())) is False
    assert app.lic.is_license_valid_at(2_000_000_000) is False


def test_is_license_valid_at_complementary_to_is_expired_at_on_signed_key(app):
    """On a signature-valid, non-perpetual key,
    ``is_license_valid_at(e) == not is_expired_at(e)`` at every epoch.
    Pinned so the two predicates cannot silently drift apart on the
    happy-path branch a paywall renders every request."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    for epoch in (exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400):
        assert app.lic.is_license_valid_at(epoch) == (
            not app.lic.is_expired_at(epoch)
        ), epoch


def test_is_license_valid_at_non_numeric_epoch(app):
    """A caller passing a typo must get False, not a crash."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    assert app.lic.is_license_valid_at("garbage") is False  # type: ignore[arg-type]
    assert app.lic.is_license_valid_at(None) is False  # type: ignore[arg-type]
    assert app.lic.is_license_valid_at([1]) is False  # type: ignore[arg-type]
    assert app.lic.is_license_valid_at({}) is False  # type: ignore[arg-type]


def test_is_license_valid_at_bool_epoch_rejected(app):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently ask "was the key valid
    at epoch 1?" on a perpetual key and get True back."""
    _write_perpetual(app)  # perpetual would answer True at epoch=1
    assert app.lic.is_license_valid_at(True) is False  # type: ignore[arg-type]
    assert app.lic.is_license_valid_at(False) is False  # type: ignore[arg-type]


def test_is_license_valid_at_float_epoch_coerced(app):
    """Float epoch coerces through ``int()`` -- same posture as
    :func:`is_expired_at` / :func:`is_expiring_at`."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    now_f = float(time.time())
    assert app.lic.is_license_valid_at(now_f) is True


def test_is_license_valid_at_never_raises(monkeypatch):
    """Any underlying failure -> False. Even a fully-broken
    :func:`license_state_at` must not propagate."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "license_state_at", _boom)
    assert _lic.is_license_valid_at(int(time.time())) is False


# -- clawmetry.license.is_license_valid_at_batch() ----------------------------


def test_batch_none_returns_empty(app):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`is_expired_at_batch` / :func:`license_state_at_batch`."""
    assert app.lic.is_license_valid_at_batch(None) == []


def test_batch_non_iterable_returns_empty(app):
    """Non-iterable ``epochs`` -> ``[]`` rather than a crash."""
    assert app.lic.is_license_valid_at_batch(42) == []


def test_batch_empty_returns_empty(app):
    """Empty iterable -> ``[]``."""
    assert app.lic.is_license_valid_at_batch([]) == []
    assert app.lic.is_license_valid_at_batch(()) == []


def test_batch_no_license(app):
    """No license file -> every row ``is_valid=False`` (nothing to
    trust). Time-independent, matches the never-mis-gate scalar
    posture."""
    rows = app.lic.is_license_valid_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["is_valid"] for r in rows] == [False, False, False]


def test_batch_active_key_before_and_after_exp(app):
    """Active key: rows whose ``epoch`` is strictly before ``exp`` fire
    True; ``epoch == exp`` and rows after fire False. Boundary matches
    :func:`is_expired_at`'s ``exp <= epoch`` cutoff exactly."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_license_valid_at_batch(
        [exp - 86400, exp - 1, exp, exp + 1, exp + 86400]
    )
    assert [r["is_valid"] for r in rows] == [True, True, False, False, False]


def test_batch_per_row_parity_with_scalar(app):
    """Per-row parity with :func:`is_license_valid_at` -- the batch
    cannot silently drift from the scalar. Pin every row against the
    singular helper on the same install."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    rows = app.lic.is_license_valid_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["is_valid"] == app.lic.is_license_valid_at(epoch), epoch


def test_batch_perpetual_always_fires(app):
    """Perpetual (no ``exp``) key -> ``is_valid=True`` at every epoch.
    Mirrors :func:`is_license_valid_at`'s perpetual branch."""
    _write_perpetual(app)
    rows = app.lic.is_license_valid_at_batch([0, int(time.time()), 2_000_000_000])
    assert [r["is_valid"] for r in rows] == [True, True, True]


def test_batch_invalid_signature(app):
    """Bogus-signature file -> ``is_valid=False`` at every epoch (an
    unsigned body is untrusted whatever the perspective)."""
    _write_bogus(app)
    rows = app.lic.is_license_valid_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["is_valid"] for r in rows] == [False, False, False]


def test_batch_lapsed_key_split_around_exp(app):
    """A signature-valid but currently-lapsed key: rows BEFORE ``exp``
    still fire True (retrospective "was it entitled then?"), rows AT/
    after fire False. The batch stays sensitive to the perspective
    axis rather than folding to a single current-state answer."""
    _write_key_direct(app, exp_delta=-5 * 86400)  # exp = now - 5d
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_license_valid_at_batch(
        [exp - 86400, exp, exp + 1, int(time.time())]
    )
    assert [r["is_valid"] for r in rows] == [True, False, False, False]


def test_batch_string_int_tokens_parsed(app):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_license_valid_at_batch([str(exp - 1), str(exp)])
    assert [r["is_valid"] for r in rows] == [True, False]


def test_batch_dedupes_by_int_key_preserves_order(app):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_license_valid_at_batch(
        [exp - 100, exp - 50, exp - 100, str(exp - 50), exp - 10]
    )
    assert [r["epoch"] for r in rows] == [exp - 100, exp - 50, exp - 10]


def test_batch_bad_tokens_collapse_to_false(app):
    """``bool`` / non-numeric / ``None`` collapse to ``is_valid=False``
    (matches the scalar's rejection). Each bad input keeps its own slot
    so output length matches N."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    rows = app.lic.is_license_valid_at_batch([True, False, None, "garbage", ""])
    assert len(rows) == 5
    assert all(r["is_valid"] is False for r in rows)


def test_batch_mixed_good_and_bad(app):
    """Bad tokens don't fail the whole batch. Good rows resolve; bad
    rows still slot in with ``is_valid=False``."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    rows = app.lic.is_license_valid_at_batch(
        [exp - 1, "garbage", exp + 60 * 86400]
    )
    assert [r["is_valid"] for r in rows] == [True, False, False]


def test_batch_never_raises(monkeypatch):
    """Any per-row underlying failure of :func:`is_license_valid_at`
    -> ``is_valid=False`` for THAT row. The batch never propagates."""
    import clawmetry.license as _lic

    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(_lic, "is_license_valid_at", _boom)
    rows = _lic.is_license_valid_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["is_valid"] for r in rows] == [False, False]
    assert len(rows) == 2


def test_batch_complementary_to_is_expired_at_batch_on_signed_key(app):
    """Per-row: on a signature-valid, non-perpetual key,
    ``is_valid`` is the strict complement of ``expired`` from
    :func:`is_expired_at_batch`. Pinned so the two batches cannot drift
    apart on the happy-path branch that hydrates most paywall tiles."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 10 * 86400, exp - 1, exp, exp + 1, exp + 60 * 86400]
    valid_rows = app.lic.is_license_valid_at_batch(epochs)
    expired_rows = app.lic.is_expired_at_batch(epochs)
    for v_row, e_row in zip(valid_rows, expired_rows):
        assert v_row["epoch"] == e_row["epoch"]
        assert v_row["is_valid"] == (not e_row["expired"])


# -- GET /api/license/is-valid-at --------------------------------------------


def test_endpoint_no_license(app):
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert isinstance(data["requested_epoch"], int)
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_active_at_now(app):
    """Active key at "now" -> is_valid_at true, valid true, expires_at
    populated for the sibling tile that renders the date."""
    tok = app.lic._encode_token(_payload(exp_delta=45 * 86400), app.priv)
    app.lic.activate(tok)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is True
    assert data["requested_epoch"] == now
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_active_at_future_after_exp(app):
    """Active key evaluated at a perspective epoch AFTER ``exp`` ->
    is_valid_at false, valid still true (the key is not expired NOW)."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    epoch = int(time.time()) + 60 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["requested_epoch"] == epoch
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_lapsed_key_at_now(app):
    """Lapsed-but-signed key at "now" -> is_valid_at false, valid FALSE.
    Both signals collapse together on the currently-expired branch."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_lapsed_key_at_pre_lapse_epoch(app):
    """Lapsed-but-signed key at a perspective epoch BEFORE its ``exp``
    -> is_valid_at true (retrospective entitlement), valid still false
    (key is expired NOW). The predicate flips independently of the
    current-state validity."""
    _write_key_direct(app, exp_delta=-5 * 86400)
    epoch = int(time.time()) - 20 * 86400
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is True
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_perpetual_license(app):
    """Perpetual license -> is_valid_at true at any epoch. expires_at
    null because no ``exp`` claim; has_license true (there IS a file)."""
    _write_perpetual(app)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is True
    assert data["expires_at"] is None
    assert data["has_license"] is True


def test_endpoint_missing_epoch_arg(app):
    """No ``epoch=`` -> is_valid_at false, requested_epoch null, HTTP
    200. The snapshot still populates expires_at from the on-disk key."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-valid-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["requested_epoch"] is None
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True


def test_endpoint_non_integer_epoch(app):
    """Typo epoch -> is_valid_at false, requested_epoch null, HTTP 200
    (never a 4xx). Mirrors the ``/api/license/is-expired-at`` posture."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-valid-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["requested_epoch"] is None
    assert data["has_license"] is True


def test_endpoint_invalid_signature(app):
    """File on disk but signature bogus -> is_valid_at false, has_license
    True (there IS a file), valid False."""
    _write_bogus(app)
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["has_license"] is True
    assert data["valid"] is False


def test_endpoint_never_5xxs(app, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the OSS-free shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_license_expires_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_valid_at"] is False
    assert data["requested_epoch"] == epoch
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


# -- GET /api/license/is-valid-at-batch --------------------------------------


def test_endpoint_batch_missing_epochs(app):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints)."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-valid-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_batch_blank_epochs(app):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-valid-at-batch?epochs=")
        resp2 = c.get("/api/license/is-valid-at-batch?epochs=,,,")
    assert resp.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_batch_no_license(app):
    """No license file -> every row ``is_valid=False``, HTTP 200,
    current-time snapshot fields set to the OSS-free branch shape."""
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at-batch?epochs={now},0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_license_valid_at"
    assert data["count"] == 2
    assert [r["is_valid"] for r in data["rows"]] == [False, False]
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False


def test_endpoint_batch_active_key_boundary(app):
    """Active key: only rows strictly before ``exp`` fire True. Snapshot
    reflects current install state."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp - 1, exp, exp + 1])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_license_valid_at"
    assert data["count"] == 3
    assert [r["is_valid"] for r in data["rows"]] == [True, False, False]
    assert data["state"] == "active"
    assert isinstance(data["expires_at"], int)
    assert data["has_license"] is True
    assert data["valid"] is True


def test_endpoint_batch_perpetual_all_true(app):
    """Perpetual license -> is_valid=True at every epoch."""
    _write_perpetual(app)
    csv = ",".join(str(e) for e in [0, int(time.time()), 2_000_000_000])
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert [r["is_valid"] for r in data["rows"]] == [True, True, True]
    assert data["expires_at"] is None
    assert data["has_license"] is True


def test_endpoint_batch_per_row_matches_scalar_endpoint(app):
    """Per-row parity with the scalar endpoint: for every epoch in the
    batch, ``rows[i].is_valid`` must equal what
    ``/api/license/is-valid-at?epoch=<epoch>`` returns for that same
    epoch alone. Pins the batch against the singular endpoint so it
    cannot drift silently."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    epochs = [exp - 5 * 86400, exp - 1, exp, exp + 1, exp + 30 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with app.app.test_client() as c:
        batch = c.get(f"/api/license/is-valid-at-batch?epochs={csv}").get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/is-valid-at?epoch={epoch}"
            ).get_json()
            assert row["is_valid"] == scalar["is_valid_at"], epoch


def test_endpoint_batch_shared_snapshot_matches_is_expired_at_batch(app):
    """Both ``/api/license/is-valid-at-batch`` and
    ``/api/license/is-expired-at-batch`` share
    :func:`_license_state_at_snapshot` -- they must surface identical
    ``state`` / ``expires_at`` / ``has_license`` / ``valid`` snapshot
    fields for the same install. Guards a UI that renders the two batch
    tiles side-by-side from catching them disagreeing on shared fields."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    info = app.lic.current_license_info()
    exp = int(info["exp"])
    csv = ",".join(str(e) for e in [exp - 1, exp, exp + 1])
    with app.app.test_client() as c:
        a = c.get(f"/api/license/is-valid-at-batch?epochs={csv}").get_json()
        b = c.get(f"/api/license/is-expired-at-batch?epochs={csv}").get_json()
    for key in ("state", "expires_at", "has_license", "valid"):
        assert a[key] == b[key], (
            f"mismatch on {key}: is-valid-at-batch={a[key]!r} "
            f"is-expired-at-batch={b[key]!r}"
        )


def test_endpoint_batch_bad_tokens_collapse_to_false(app):
    """Non-numeric / ``bool``-ish CSV tokens collapse to
    ``is_valid=false`` with the raw token echoed in ``epoch``. Each row
    keeps its slot so ``count`` still matches the number of usable
    tokens after de-dup."""
    tok = app.lic._encode_token(_payload(exp_delta=30 * 86400), app.priv)
    app.lic.activate(tok)
    with app.app.test_client() as c:
        resp = c.get("/api/license/is-valid-at-batch?epochs=garbage,also-bad")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert all(r["is_valid"] is False for r in data["rows"])


def test_endpoint_batch_never_5xxs(app, monkeypatch):
    """Snapshot blowup + underlying batch blowup -> HTTP 200 with the
    OSS-free branch shape and an empty ``rows`` list rather than a 5xx."""
    from routes import entitlement as _routes
    import clawmetry.license as _lic

    monkeypatch.setattr(
        _routes,
        "_license_state_at_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )

    def _boom(_epochs):
        raise RuntimeError("simulated batch blowup")

    monkeypatch.setattr(_lic, "is_license_valid_at_batch", _boom)
    now = int(time.time())
    with app.app.test_client() as c:
        resp = c.get(f"/api/license/is-valid-at-batch?epochs={now}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "is_license_valid_at"
    assert data["count"] == 0
    assert data["rows"] == []
    assert data["state"] == "no_license"
    assert data["expires_at"] is None
    assert data["has_license"] is False
    assert data["valid"] is False
