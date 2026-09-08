"""Tests for the ``has_feature_at(feature, epoch)`` predicate on
``clawmetry.license`` and its paired ``GET /api/license/has-feature-at``
HTTP endpoint.

The perspective-epoch predicate on the license-features axis. Where
:func:`clawmetry.license.has_feature` answers "does the KEY claim
feature <X> right now?", this pair answers "did the KEY claim feature
<X> as of ``epoch``?" -- the same retrospective / prospective question
:func:`is_tier_at` answers for the license tier. Both this pair and
the underlying accessor :func:`license_features_at` refuse the invalid-
signature branch and use the same ``exp <= epoch`` cutoff, so they
cannot disagree at the boundary when the perspective epoch equals
"now".

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key + ``LICENSE_PATH``,
mirroring ``tests/test_license_is_tier_at.py`` /
``tests/test_license_has_feature.py`` so nothing depends on the real
production signing key or on real filesystem state. No network calls;
``CLAWMETRY_OFFLINE=1`` opts out of the ``clawmetry activate`` phone-
home.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


# -- shared helpers ---------------------------------------------------------


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


# -- clawmetry.license.has_feature_at() -------------------------------------


def test_has_feature_at_no_license(app):
    """No license file on disk -> ``False`` regardless of feature /
    epoch. Mirrors :func:`has_feature`'s no-license branch."""
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is False
    assert app.lic.has_feature_at("alerts", 0) is False
    assert app.lic.has_feature_at("alerts", 2_000_000_000) is False


def test_has_feature_at_now_matches_has_feature_active(app):
    """When ``epoch`` equals "now", the perspective predicate must
    agree with :func:`has_feature` for the same install -- pins the
    boundary parity contract."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is True
    assert app.lic.has_feature_at("alerts", now) == app.lic.has_feature(
        "alerts"
    )
    assert app.lic.has_feature_at("selfevolve", now) is False
    assert app.lic.has_feature_at(
        "selfevolve", now
    ) == app.lic.has_feature("selfevolve")


def test_has_feature_at_now_matches_has_feature_lapsed(app):
    """Signed-but-lapsed key at "now" -> ``False`` for every query,
    matching :func:`has_feature`'s "not entitled RIGHT NOW" posture on
    the same install."""
    _write_direct(
        app, _payload(exp_delta=-5 * 86400, features=("alerts",))
    )
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is False
    assert app.lic.has_feature_at("alerts", now) == app.lic.has_feature(
        "alerts"
    )


def test_has_feature_at_future_before_expiry(app):
    """Prospective epoch that still falls before the token's ``exp``
    -> the ``features`` claim resolves. A caller can answer "will this
    node still have <feature> at our next audit?" without a manual
    ``exp`` comparison."""
    _write_direct(app, _payload(exp_delta=30 * 86400, features=("alerts",)))
    future = int(time.time()) + 5 * 86400
    assert app.lic.has_feature_at("alerts", future) is True


def test_has_feature_at_future_after_expiry(app):
    """Prospective epoch that falls PAST the token's ``exp`` ->
    ``False`` for every query. A key that will be expired by the audit
    date is not entitled AT the audit date."""
    _write_direct(app, _payload(exp_delta=10 * 86400, features=("alerts",)))
    future = int(time.time()) + 30 * 86400
    assert app.lic.has_feature_at("alerts", future) is False


def test_has_feature_at_past_still_active(app):
    """A retrospective epoch that falls before both "now" and ``exp``
    on an active key -> the ``features`` claim still resolves. The
    key was already valid then."""
    _write_direct(app, _payload(exp_delta=365 * 86400, features=("alerts",)))
    past = int(time.time()) - 10 * 86400
    assert app.lic.has_feature_at("alerts", past) is True


def test_has_feature_at_lapsed_key_pre_lapse_true(app):
    """A key whose ``exp`` has already passed at "now" but the
    perspective epoch predates ``exp`` -> ``True`` for a feature the
    token itemises. Answers "was I entitled to <feature> BEFORE the
    lapse?" without the caller having to eyeball the token."""
    _write_direct(
        app, _payload(exp_delta=-5 * 86400, features=("alerts",))
    )
    pre_lapse = int(time.time()) - 10 * 86400
    assert app.lic.has_feature_at("alerts", pre_lapse) is True
    assert app.lic.has_feature_at("selfevolve", pre_lapse) is False


def test_has_feature_at_exact_exp_boundary(app):
    """``epoch == exp`` -> ``False``. The scalar treats ``exp <=
    cutoff`` as already-lapsed (matches
    :func:`license_features_at`), so the boundary evaluates at "no
    longer entitled". Pins the boundary rule so it can't silently
    drift."""
    exp_delta = 60
    _write_direct(app, _payload(exp_delta=exp_delta, features=("alerts",)))
    exp_epoch = int(time.time()) + exp_delta
    assert app.lic.has_feature_at("alerts", exp_epoch) is False
    assert app.lic.has_feature_at("alerts", exp_epoch - 1) is True


def test_has_feature_at_perpetual_key(app):
    """Perpetual (no ``exp``) key -> the ``features`` claim resolves
    for any perspective epoch."""
    _write_direct(app, _payload(drop_exp=True, features=("alerts",)))
    for epoch in (0, int(time.time()), 2_000_000_000):
        assert app.lic.has_feature_at("alerts", epoch) is True
        assert app.lic.has_feature_at("selfevolve", epoch) is False


def test_has_feature_at_invalid_signature(app):
    """Bogus-signature file -> ``False`` regardless of feature / epoch.
    Never trust an unsigned body: an attacker who could edit the
    payload could otherwise smuggle any id into the ``features`` list
    for any perspective epoch."""
    _write_bogus(app)
    for epoch in (0, int(time.time()), 2_000_000_000):
        assert app.lic.has_feature_at("alerts", epoch) is False


def test_has_feature_at_wrong_feature(app):
    """Feature the token does NOT itemise -> ``False`` even on a
    signature-valid, unexpired key. The predicate never mis-grants a
    feature the token omits."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    assert app.lic.has_feature_at("selfevolve", now) is False


def test_has_feature_at_normalises_query_casing(app):
    """``"Alerts"``, ``"ALERTS"``, ``"  alerts  "`` all resolve against
    the same normalised set on the token. Matches :func:`has_feature`
    and :func:`is_tier_at` on the same axis."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    assert app.lic.has_feature_at("Alerts", now) is True
    assert app.lic.has_feature_at("ALERTS", now) is True
    assert app.lic.has_feature_at("  alerts  ", now) is True


def test_has_feature_at_normalises_token_casing(app):
    """A server-side typo in casing on the ``features`` claim
    normalises before the membership check, so ``"Alerts"`` on the
    token and ``"alerts"`` in the query still match. Same normalisation
    :func:`license_features_at` runs on the token side."""
    _write_direct(app, _payload(features=(" Alerts ", "FLEET")))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is True
    assert app.lic.has_feature_at("fleet", now) is True


def test_has_feature_at_bool_epoch_refused(app):
    """``bool`` (subclass of ``int``) collapses to ``False`` -- the
    accessor refuses ``True`` / ``False`` epochs so a caller cannot
    silently mis-gate on a boolean passed instead of an epoch."""
    _write_direct(app, _payload(features=("alerts",)))
    assert app.lic.has_feature_at("alerts", True) is False
    assert app.lic.has_feature_at("alerts", False) is False


def test_has_feature_at_non_numeric_epoch(app):
    """Non-numeric / non-parseable epoch -> ``False``. Matches the
    never-mis-gate posture of the ``_at`` family: a typo collapses to
    "not entitled" not to a spurious grant."""
    _write_direct(app, _payload(features=("alerts",)))
    assert app.lic.has_feature_at("alerts", "not-a-number") is False
    assert app.lic.has_feature_at("alerts", None) is False


def test_has_feature_at_string_epoch_coerced(app):
    """Int-parseable string epoch coerces through ``int()``. Mirrors
    :func:`license_features_at`'s coercion rule so the two scalars
    cannot disagree on numeric input shape."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", str(now)) is True


def test_has_feature_at_empty_feature_query(app):
    """Missing / empty / whitespace-only ``feature`` -> ``False``
    (nothing "has feature empty-string"). Matches :func:`has_feature`'s
    posture on empty input."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    assert app.lic.has_feature_at("", now) is False
    assert app.lic.has_feature_at("   ", now) is False


def test_has_feature_at_none_feature_query(app):
    """``None`` ``feature`` -> ``False`` -- guarded before ``str()`` so
    a caller passing ``None`` from a stale form field doesn't produce
    a spurious grant on the stringified ``"None"``."""
    _write_direct(app, _payload(features=("alerts",)))
    assert app.lic.has_feature_at(None, int(time.time())) is False


def test_has_feature_at_missing_features_claim(app):
    """A signature-valid key with NO ``features`` claim -> ``False``
    for every query at every epoch. Distinct from
    :func:`license_features_at` which surfaces ``[]`` on this branch;
    a predicate collapses "empty list" to the ``False`` bit."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is False


def test_has_feature_at_non_list_features_claim(app):
    """Malformed ``features`` claim (non-list) -> ``False`` for every
    query. The accessor normalises this branch to ``[]``, and an empty
    list can't contain anything."""
    _write_direct(app, _payload(features_value="alerts,fleet"))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is False


def test_has_feature_at_ignores_blank_token_entries(app):
    """Blank / whitespace-only token entries are dropped by the
    accessor, and the empty-string query is refused up-front, so a
    payload full of blanks never mis-grants."""
    _write_direct(app, _payload(features=("", "   ", "alerts")))
    now = int(time.time())
    assert app.lic.has_feature_at("alerts", now) is True
    assert app.lic.has_feature_at("", now) is False


def test_has_feature_at_parity_with_accessor(app):
    """Per-id parity with :func:`license_features_at`: for every id
    the accessor surfaces at ``epoch``, the predicate returns
    ``True``; for a novel id, ``False``. Pins the "predicate is
    exactly membership-in-accessor" contract so a future refactor of
    either side can't drift."""
    _write_direct(
        app, _payload(features=("Alerts", "FLEET", "runtimes "))
    )
    now = int(time.time())
    feats = app.lic.license_features_at(now)
    assert feats == ["alerts", "fleet", "runtimes"]
    for f in feats:
        assert app.lic.has_feature_at(f, now) is True
    assert app.lic.has_feature_at("selfevolve", now) is False


def test_has_feature_at_never_raises_on_underlying_failure(app, monkeypatch):
    """Any per-row failure of :func:`license_features_at` -> ``False``.
    The predicate never propagates -- matches the never-crash posture
    of the surrounding license helpers."""

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(app.lic, "license_features_at", _boom)
    assert app.lic.has_feature_at("alerts", int(time.time())) is False


# -- /api/license/has-feature-at endpoint parity ----------------------------


def test_endpoint_no_license_returns_false_shape(app):
    """OSS-free install (no license) -> ``has_feature_at=false``,
    ``features_at=null``, ``features=null``, ``has_license=false``,
    ``valid=false``. Never 5xxs; the endpoint must always answer with
    the standard envelope so a UI binding can render without special-
    casing HTTP status codes."""
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["requested_feature"] == "alerts"
    assert body["requested_epoch"] == now
    assert body["features"] is None
    assert body["expires_at"] is None
    assert body["has_license"] is False
    assert body["valid"] is False


def test_endpoint_active_key_claimed_returns_true_shape(app):
    """A signature-valid key at "now" whose ``features`` claim contains
    the queried id -> ``has_feature_at=true``, ``features_at``
    populated, ``features`` populated, ``has_license``/``valid`` both
    ``true``."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is True
    assert body["features_at"] == ["alerts", "fleet"]
    assert body["features"] == ["alerts", "fleet"]
    assert body["requested_feature"] == "alerts"
    assert body["requested_epoch"] == now
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_active_key_unclaimed_returns_false_shape(app):
    """A signature-valid key whose ``features`` claim does NOT contain
    the queried id -> ``has_feature_at=false`` but ``features_at``
    still populated, ``valid=true``. A UI can render "you were on
    Pro then, but that feature wasn't on your key" copy off ONE call."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=selfevolve&epoch={now}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] == ["alerts", "fleet"]
    assert body["requested_feature"] == "selfevolve"
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_case_insensitive_query(app):
    """The endpoint normalises the query the same way the predicate
    does (lower / strip), so ``?feature=Alerts`` and
    ``?feature=%20alerts%20`` both resolve against the same normalised
    set."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    for q in ("Alerts", "ALERTS", "%20alerts%20"):
        resp = app.client.get(
            f"/api/license/has-feature-at?feature={q}&epoch={now}"
        )
        body = resp.get_json()
        assert body["has_feature_at"] is True
        assert body["requested_feature"] == "alerts"


def test_endpoint_missing_epoch_returns_false_shape(app):
    """Missing ``epoch`` -> ``has_feature_at=false``,
    ``features_at=null``, ``requested_epoch=null``, HTTP 200. Never
    4xxs (matches the surrounding endpoints' never-4xx posture)."""
    _write_direct(app, _payload(features=("alerts",)))
    resp = app.client.get("/api/license/has-feature-at?feature=alerts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["requested_epoch"] is None
    # A valid key is still installed, so the surrounding fields must
    # still surface truthfully.
    assert body["features"] == ["alerts"]
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_missing_feature_returns_false_shape(app):
    """Missing ``feature`` -> ``has_feature_at=false``,
    ``requested_feature=""``, HTTP 200."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(f"/api/license/has-feature-at?epoch={now}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["requested_feature"] == ""
    # ``features_at`` still surfaces because the epoch is valid and the
    # key is signed -- the missing feature query doesn't erase the
    # accessor's response.
    assert body["features_at"] == ["alerts"]


def test_endpoint_empty_feature_returns_false_shape(app):
    """Empty / whitespace-only ``feature`` param -> ``has_feature_at=false``.
    Matches the underlying predicate."""
    _write_direct(app, _payload(features=("alerts",)))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=%20%20&epoch={now}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["requested_feature"] == ""


def test_endpoint_bool_epoch_refused(app):
    """``bool`` / non-numeric epoch -> ``features_at=null`` and
    ``has_feature_at=false``. Matches the never-mis-gate posture of
    the ``_at`` family."""
    _write_direct(app, _payload(features=("alerts",)))
    resp = app.client.get(
        "/api/license/has-feature-at?feature=alerts&epoch=true"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["requested_epoch"] is None


def test_endpoint_non_numeric_epoch_returns_false(app):
    """Non-numeric epoch -> ``requested_epoch=null``,
    ``has_feature_at=false``, HTTP 200."""
    _write_direct(app, _payload(features=("alerts",)))
    resp = app.client.get(
        "/api/license/has-feature-at?feature=alerts&epoch=not-a-number"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["requested_epoch"] is None


def test_endpoint_expired_key_returns_false_valid_false(app):
    """Signed-but-lapsed key at "now" -> ``has_feature_at=false``,
    ``features_at=null``, but ``has_license=true`` and ``valid=false``
    so a UI can render "was Pro, expired" copy without a second call
    to ``/api/license/status``."""
    _write_direct(
        app, _payload(exp_delta=-5 * 86400, features=("alerts",))
    )
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_lapsed_key_pre_lapse_epoch_returns_true(app):
    """A key whose ``exp`` has already passed at "now", queried at a
    perspective epoch BEFORE the lapse -> ``has_feature_at=true`` even
    though ``valid=false`` at "now"."""
    _write_direct(
        app, _payload(exp_delta=-5 * 86400, features=("alerts",))
    )
    pre_lapse = int(time.time()) - 10 * 86400
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={pre_lapse}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is True
    assert body["features_at"] == ["alerts"]
    # Current-time reference fields still surface the lapsed state, so
    # a UI can render both perspectives ("was Pro then, not now") off
    # ONE call.
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_invalid_signature_returns_false(app):
    """Bogus-signature file -> ``has_feature_at=false``,
    ``features_at=null``, ``features=null``, ``has_license=true`` (the
    file IS on disk), ``valid=false``."""
    _write_bogus(app)
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["features"] is None
    assert body["has_license"] is True
    assert body["valid"] is False


def test_endpoint_perpetual_key_returns_true(app):
    """Perpetual (no ``exp``) key -> ``has_feature_at`` resolves
    against the token's ``features`` list at any perspective epoch."""
    _write_direct(
        app, _payload(drop_exp=True, features=("alerts", "runtimes"))
    )
    for epoch in (0, int(time.time()), 2_000_000_000):
        resp = app.client.get(
            f"/api/license/has-feature-at?feature=runtimes&epoch={epoch}"
        )
        body = resp.get_json()
        assert body["has_feature_at"] is True, epoch
        assert body["features_at"] == ["alerts", "runtimes"]


def test_endpoint_missing_features_claim(app):
    """A signature-valid key without a ``features`` claim ->
    ``has_feature_at=false``, ``features_at=[]``, ``valid=true``. A UI
    can distinguish "valid key with nothing itemised"
    (``features_at=[]``) from "no key" (``features_at=null``) without
    a second call."""
    _write_direct(app, _payload(drop_features=True))
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] == []
    assert body["has_license"] is True
    assert body["valid"] is True


def test_endpoint_agrees_with_has_feature_at_now(app):
    """When ``epoch`` equals "now" and ``feature`` is a non-empty
    string, the endpoint agrees with the "now" ``/api/license/has-feature``
    sibling endpoint. Pins the boundary parity contract at the HTTP
    layer."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    for feature in ("alerts", "fleet", "selfevolve"):
        at_body = app.client.get(
            f"/api/license/has-feature-at?feature={feature}&epoch={now}"
        ).get_json()
        now_body = app.client.get(
            f"/api/license/has-feature?feature={feature}"
        ).get_json()
        assert at_body["has_feature_at"] == now_body["has_feature"], feature
        assert at_body["features_at"] == now_body["features"], feature


def test_endpoint_agrees_with_features_at_endpoint(app):
    """Per-id agreement with ``/api/license/features-at``: for every
    id that endpoint surfaces at ``epoch``, the predicate endpoint
    returns ``True`` at the same ``epoch``; for a novel id, ``False``.
    Pins the "predicate is exactly membership-in-accessor" contract at
    the HTTP layer."""
    _write_direct(app, _payload(features=("alerts", "fleet", "runtimes")))
    now = int(time.time())
    list_body = app.client.get(
        f"/api/license/features-at?epoch={now}"
    ).get_json()
    for f in list_body["features_at"]:
        body = app.client.get(
            f"/api/license/has-feature-at?feature={f}&epoch={now}"
        ).get_json()
        assert body["has_feature_at"] is True, f
        assert body["features_at"] == list_body["features_at"]
    body = app.client.get(
        f"/api/license/has-feature-at?feature=selfevolve&epoch={now}"
    ).get_json()
    assert body["has_feature_at"] is False


def test_endpoint_parity_with_python_helper(app):
    """Per-response parity with :func:`clawmetry.license.has_feature_at`:
    the HTTP endpoint MUST equal the Python helper for the bool slot.
    Pins the drift guard."""
    _write_direct(app, _payload(features=("alerts", "fleet")))
    now = int(time.time())
    for feature in ("alerts", "fleet", "selfevolve", ""):
        body = app.client.get(
            f"/api/license/has-feature-at?feature={feature}&epoch={now}"
        ).get_json()
        assert body["has_feature_at"] == app.lic.has_feature_at(
            feature, now
        ), feature


def test_endpoint_never_5xxs_on_underlying_failure(app, monkeypatch):
    """Any exception under the hood -> HTTP 200 with the OSS-free
    branch shape. The endpoint must never propagate a 500 -- a
    diagnostic tile bound to it stays rendered even on a partially-
    broken install."""

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(app.lic, "license_features_at", _boom)
    monkeypatch.setattr(app.lic, "license_features", _boom)
    monkeypatch.setattr(app.lic, "current_license_info", _boom)
    monkeypatch.setattr(app.lic, "license_expires_at", _boom)
    now = int(time.time())
    resp = app.client.get(
        f"/api/license/has-feature-at?feature=alerts&epoch={now}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_feature_at"] is False
    assert body["features_at"] is None
    assert body["features"] is None
    assert body["has_license"] is False
    assert body["valid"] is False
    # The echo fields still carry the normalised query even on the
    # error branch, so a caller can distinguish "no license, but the
    # server saw my query" from "no license, and the server dropped
    # my query" (which would indicate a routing / proxy bug).
    assert body["requested_feature"] == "alerts"
    assert body["requested_epoch"] == now
