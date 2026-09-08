"""Tests for the ``has_feature_at`` / ``has_runtime_at`` hypothetical-perspective
boolean-gate scalar helpers and their paired
``/api/entitlement/has-feature-at`` / ``/api/entitlement/has-runtime-at``
endpoints.

Hypothetical-perspective siblings of the live :func:`has_feature` /
:func:`has_runtime` scalars: where those answer "does the LIVE resolved
entitlement grant this?", these answer "would tier ``perspective_tier``
grant this?" -- one boolean per pricing-matrix cell, decoupled from the
live resolver's grace pass-through, so a "does Starter grant fleet? Pro?
Enterprise?" matrix can bind ``allowed`` directly off ONE URL per cell
without hydrating the full ``/feature-catalog-at`` payload.

Semantics diverge deliberately from the perspective-independent
:func:`min_tier_for_features_at` / :func:`tiers_for_feature_at` convention:
the boolean answer *is* perspective-shaped. Backed by
:func:`_hypothetical_entitlement`, which forces ``grace`` off so the
returned bit reflects the static per-tier grant in :data:`_TIER_FEATURES` /
:data:`_TIER_PAID_RUNTIMES` rather than the live resolver's grace
pass-through.

This file pins:

1. Scalar semantics: empty / None / non-string / unknown perspective,
   unknown axis-id, free / paid axis-id across every tier.
2. Perspective-shaped grace-independence: ``has_feature_at("oss", "fleet")``
   returns ``False`` in BOTH grace and enforce (unlike the live
   :func:`has_feature` sibling which returns ``True`` in grace) -- the
   whole point of the ``_at`` slot is to render the would-be-locked
   state alongside the live grant.
3. Runtime-axis alias posture: scalar is strict (no
   :func:`canonical_runtime` resolution -- matches sibling
   :func:`has_runtime`); endpoint canonicalises upstream (matches sibling
   ``/has-runtime`` endpoint).
4. Endpoint envelope shape (fixed 12-key set) across every input branch.
5. Never-4xx / never-5xx guarantees on both endpoints.
6. Cross-consistency with the sibling ``/api/entitlement/feature-spec-at``
   / ``/runtime-spec-at`` endpoints -- same ``allowed`` bit for the same
   perspective + axis id.
7. Cross-consistency with the live ``/api/entitlement/has-feature`` /
   ``/has-runtime`` endpoints on the ``current_tier`` / ``grace`` /
   ``enforced`` envelope slots (both endpoints share the resolver
   context; only the ``allowed`` bit differs by design).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- matches the
    sibling ``test_entitlement_has_feature_has_runtime.py`` fixture so
    the perspective assertions here reproduce the same install state the
    live boolean gates are pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` off. Included to pin the perspective-shaped
    grace-independence invariant -- ``has_*_at`` returns the same
    answer under grace vs enforce for the same (perspective, id)
    pair."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── Envelope shape ──────────────────────────────────────────────────────────

_FEATURE_KEYS = {
    "tier",
    "feature",
    "has_feature_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_RUNTIME_KEYS = {
    "tier",
    "runtime",
    "has_runtime_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_feature_at scalar ─────────────────────────────────────────────────


def test_has_feature_at_free_on_every_tier(ent):
    """A free feature is granted from every real tier (the free floor
    is baked into :func:`_hypothetical_entitlement`)."""
    free = next(iter(ent.FREE_FEATURES))
    for tier in ent._TIER_ORDER:
        assert ent.has_feature_at(tier, free) is True, tier


def test_has_feature_at_paid_only_on_granting_tiers(ent):
    """A paid feature is granted only from tiers whose static
    :data:`_TIER_FEATURES` map includes it."""
    for feat in sorted(ent.PAID_FEATURES):
        for tier in ent._TIER_ORDER:
            granted = feat in ent._TIER_FEATURES.get(tier, frozenset())
            assert ent.has_feature_at(tier, feat) is granted, (tier, feat)


def test_has_feature_at_oss_never_grants_paid(ent):
    """The OSS-free tier never statically grants a paid feature (the
    whole point of the ``_at`` slot: renders locked even in grace)."""
    for feat in sorted(ent.PAID_FEATURES):
        assert ent.has_feature_at("oss", feat) is False, feat


def test_has_feature_at_unknown_perspective_is_false(ent):
    """Perspective not in :data:`_TIER_ORDER` -> fail-closed False.
    Casing / whitespace normalises via ``.strip().lower()`` before the
    membership check, so ``"Pro"`` is a valid perspective and does NOT
    belong on this list (covered by the case-insensitive test)."""
    for bad in ["", " ", "mars", "pro_plus", "unknown_tier"]:
        assert ent.has_feature_at(bad, "fleet") is False, bad


def test_has_feature_at_unknown_feature_is_false(ent):
    """Feature id not in :data:`ALL_FEATURES` -> fail-closed False."""
    for bad in ["", " ", "bogus_id", "Fleet"]:
        # note: "Fleet" is uppercase, which the strict lower-normalise
        # collapses; the resulting "fleet" IS in ALL_FEATURES so the
        # scalar delegates to _hypothetical -- the typo does NOT
        # fail-closed here (matches has_feature's behaviour: the strict
        # gate is on the pre-normalised text after strip().lower(), not
        # on the raw casing). The "Fleet" case is exercised below.
        if bad == "Fleet":
            assert ent.has_feature_at("pro", bad) is True  # normalises to "fleet"
        else:
            assert ent.has_feature_at("pro", bad) is False, bad


def test_has_feature_at_non_string_perspective_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_feature_at(bad, "fleet") is False


def test_has_feature_at_non_string_feature_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_feature_at("pro", bad) is False


def test_has_feature_at_case_insensitive_normalises(ent):
    """Casing / whitespace on both args normalises via ``strip().lower()``
    -- a callsite passing raw config values doesn't have to pre-canonicalise."""
    assert ent.has_feature_at("  PRO  ", "  fleet  ") is True
    assert ent.has_feature_at("Pro", "FLEET") is True


def test_has_feature_at_grace_independence(ent, enforced):
    """The whole point of the ``_at`` slot: perspective-shaped answers
    are IDENTICAL under grace vs enforce for the same (perspective, id)
    pair. Diverges from the live :func:`has_feature` which flips from
    ``True`` in grace to ``False`` in enforce for the same feature."""
    for feat in sorted(ent.PAID_FEATURES):
        for tier in ent._TIER_ORDER:
            assert ent.has_feature_at(tier, feat) is enforced.has_feature_at(
                tier, feat
            ), (tier, feat)


def test_has_feature_at_never_raises_on_hypothetical_blowup(monkeypatch, ent):
    """Any blowup in the hypothetical-entitlement builder collapses to
    ``False`` so a pricing matrix cell keeps rendering."""

    def _boom(*a, **kw):
        raise RuntimeError("hypothetical blew up")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", _boom)
    for tier in ent._TIER_ORDER:
        assert ent.has_feature_at(tier, "fleet") is False


# ── has_runtime_at scalar ─────────────────────────────────────────────────


def test_has_runtime_at_free_on_every_tier(ent):
    """A free runtime is granted from every real tier."""
    for rt in sorted(ent.FREE_RUNTIMES):
        for tier in ent._TIER_ORDER:
            assert ent.has_runtime_at(tier, rt) is True, (tier, rt)


def test_has_runtime_at_paid_only_on_paid_tiers(ent):
    """A paid runtime is granted only from tiers in
    :data:`_TIER_PAID_RUNTIMES`."""
    paid = next(iter(ent.PAID_RUNTIMES))
    for tier in ent._TIER_ORDER:
        granted = tier in ent._TIER_PAID_RUNTIMES
        assert ent.has_runtime_at(tier, paid) is granted, (tier, paid)


def test_has_runtime_at_oss_never_grants_paid(ent):
    """OSS-free never statically grants any paid runtime."""
    for rt in sorted(ent.PAID_RUNTIMES):
        assert ent.has_runtime_at("oss", rt) is False, rt


def test_has_runtime_at_unknown_perspective_is_false(ent):
    for bad in ["", " ", "mars", "pro-plus", "unknown_tier"]:
        assert ent.has_runtime_at(bad, "openclaw") is False, bad


def test_has_runtime_at_unknown_runtime_is_false(ent):
    for bad in ["", " ", "bogus_runtime"]:
        assert ent.has_runtime_at("pro", bad) is False, bad


def test_has_runtime_at_scalar_does_not_alias_resolve(ent):
    """The scalar mirrors the sibling :func:`has_runtime` alias posture
    exactly: ``"claude-code"`` is not in :data:`ALL_RUNTIMES` after
    ``.strip().lower()``, so an alias input at the scalar layer
    collapses to ``False``. Alias tolerance belongs to the endpoint,
    which canonicalises upstream."""
    assert ent.has_runtime_at("pro", "claude-code") is False


def test_has_runtime_at_non_string_perspective_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_runtime_at(bad, "openclaw") is False


def test_has_runtime_at_non_string_runtime_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_runtime_at("pro", bad) is False


def test_has_runtime_at_case_insensitive_normalises(ent):
    assert ent.has_runtime_at("  PRO  ", "  openclaw  ") is True
    assert ent.has_runtime_at("Pro", "OPENCLAW") is True


def test_has_runtime_at_grace_independence(ent, enforced):
    """Grace-independence invariant for the runtime axis."""
    for rt in sorted(ent.ALL_RUNTIMES):
        for tier in ent._TIER_ORDER:
            assert ent.has_runtime_at(tier, rt) is enforced.has_runtime_at(
                tier, rt
            ), (tier, rt)


def test_has_runtime_at_never_raises_on_hypothetical_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("hypothetical blew up")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", _boom)
    for tier in ent._TIER_ORDER:
        assert ent.has_runtime_at(tier, "openclaw") is False


# ── Cross-consistency: has_*_at parity with feature_spec_at.allowed ────────


def test_has_feature_at_parity_with_feature_spec_at(ent):
    """The scalar bit byte-equals the sibling :func:`feature_spec_at`'s
    ``allowed`` field for every (tier, feature) pair."""
    for tier in ent._TIER_ORDER:
        for feat in sorted(ent.ALL_FEATURES):
            spec = ent.feature_spec_at(tier, feat)
            assert spec is not None, (tier, feat)
            assert ent.has_feature_at(tier, feat) is bool(spec["allowed"]), (
                tier,
                feat,
            )


def test_has_runtime_at_parity_with_runtime_spec_at(ent):
    for tier in ent._TIER_ORDER:
        for rt in sorted(ent.ALL_RUNTIMES):
            spec = ent.runtime_spec_at(tier, rt)
            assert spec is not None, (tier, rt)
            assert ent.has_runtime_at(tier, rt) is bool(spec["allowed"]), (
                tier,
                rt,
            )


# ── /api/entitlement/has-feature-at endpoint ──────────────────────────────


def test_endpoint_has_feature_at_shape_default(client):
    """Missing all args -> 200 with 12-key envelope and fail-closed False."""
    body = _get_json(client, "/api/entitlement/has-feature-at")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["tier"] == ""
    assert body["feature"] == ""
    assert body["has_feature_at"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["perspective_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_endpoint_has_feature_at_paid_on_granting_tier(client):
    """Grace-independence at URL level: a paid feature on a granting tier
    reports ``allowed=true`` even in grace."""
    body = _get_json(client, "/api/entitlement/has-feature-at?tier=pro&feature=fleet")
    assert body["tier"] == "pro"
    assert body["feature"] == "fleet"
    assert body["has_feature_at"] is True
    assert body["allowed"] is True
    assert body["perspective_tier_rank"] > 0
    assert body["current_tier"] == "oss"


def test_endpoint_has_feature_at_paid_on_oss_is_denied(client):
    """The whole point of the ``_at`` slot: OSS reports ``allowed=false``
    for a paid feature EVEN IN GRACE, unlike the live ``/has-feature``
    sibling which returns ``true`` in grace on the same feature."""
    body = _get_json(client, "/api/entitlement/has-feature-at?tier=oss&feature=fleet")
    assert body["has_feature_at"] is False
    assert body["allowed"] is False
    assert body["perspective_tier_rank"] == 0
    # Live sibling parity: same current_tier envelope (the live
    # /has-feature endpoint's 8-key body does not carry ``grace`` /
    # ``enforced``; those are what-if-only slots on the ``_at`` body).
    live = _get_json(client, "/api/entitlement/has-feature?feature=fleet")
    assert live["has_feature"] is True  # grace-passthrough on live
    assert body["current_tier"] == live["current_tier"]
    assert body["current_tier_rank"] == live["current_tier_rank"]


def test_endpoint_has_feature_at_unknown_tier_never_4xx(client):
    body = _get_json(client, "/api/entitlement/has-feature-at?tier=mars&feature=fleet")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["tier"] == "mars"
    assert body["has_feature_at"] is False
    assert body["perspective_tier_rank"] == -1


def test_endpoint_has_feature_at_unknown_feature_never_4xx(client):
    body = _get_json(client, "/api/entitlement/has-feature-at?tier=pro&feature=bogus_id")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["tier"] == "pro"
    assert body["feature"] == "bogus_id"
    assert body["has_feature_at"] is False
    assert body["required_tier"] is None


def test_endpoint_has_feature_at_case_insensitive(client):
    body = _get_json(
        client, "/api/entitlement/has-feature-at?tier=%20PRO%20&feature=%20FLEET%20"
    )
    assert body["tier"] == "pro"
    assert body["feature"] == "fleet"
    assert body["has_feature_at"] is True


def test_endpoint_has_feature_at_required_tier_parity(client):
    """``required_tier`` byte-equals the sibling
    ``/api/entitlement/min-tier-for-feature`` answer for the same
    feature id -- a UI wiring both URLs into the same paywall matrix
    cannot see inconsistent tier state."""
    body = _get_json(client, "/api/entitlement/has-feature-at?tier=pro&feature=fleet")
    min_body = _get_json(client, "/api/entitlement/required-tier?feature=fleet")
    assert body["required_tier"] == min_body["required_tier"]


def test_endpoint_has_feature_at_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-feature-at?tier=pro&feature=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["has_feature_at"] is False
    assert body["current_tier"] == "oss"


def test_endpoint_has_feature_at_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_feature_at", _boom)
    resp = client.get("/api/entitlement/has-feature-at?tier=pro&feature=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["has_feature_at"] is False


# ── /api/entitlement/has-runtime-at endpoint ──────────────────────────────


def test_endpoint_has_runtime_at_shape_default(client):
    body = _get_json(client, "/api/entitlement/has-runtime-at")
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["tier"] == ""
    assert body["runtime"] == ""
    assert body["has_runtime_at"] is False
    assert body["perspective_tier_rank"] == -1


def test_endpoint_has_runtime_at_paid_on_granting_tier(client):
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=pro&runtime=claude_code"
    )
    assert body["runtime"] == "claude_code"
    assert body["has_runtime_at"] is True
    assert body["allowed"] is True


def test_endpoint_has_runtime_at_paid_on_oss_is_denied(client):
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=oss&runtime=claude_code"
    )
    assert body["has_runtime_at"] is False
    assert body["perspective_tier_rank"] == 0


def test_endpoint_has_runtime_at_alias_canonicalises_upstream(client):
    """Alias input at URL level collapses to the granted canonical form
    before delegating to the strict scalar. Matches the sibling
    ``/has-runtime`` endpoint's own upstream canonicalise pattern."""
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=pro&runtime=claude-code"
    )
    assert body["runtime"] == "claude_code"
    assert body["has_runtime_at"] is True


def test_endpoint_has_runtime_at_unknown_tier_never_4xx(client):
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=mars&runtime=openclaw"
    )
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["tier"] == "mars"
    assert body["has_runtime_at"] is False


def test_endpoint_has_runtime_at_unknown_runtime_never_4xx(client):
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=pro&runtime=bogus_rt"
    )
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["has_runtime_at"] is False


def test_endpoint_has_runtime_at_required_tier_parity(client):
    body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=pro&runtime=claude_code"
    )
    min_body = _get_json(client, "/api/entitlement/required-tier?runtime=claude_code")
    assert body["required_tier"] == min_body["required_tier"]


def test_endpoint_has_runtime_at_current_tier_parity_with_live(client):
    """The what-if endpoint shares the live resolver context slots
    (``current_tier`` / ``current_tier_rank``) with the sibling live
    ``/has-runtime`` endpoint. The live endpoint's 8-key body does not
    carry ``grace`` / ``enforced``; those are what-if-only slots on
    the ``_at`` body (so a cell can render both bits alongside the
    perspective-shaped ``allowed``)."""
    at_body = _get_json(
        client, "/api/entitlement/has-runtime-at?tier=oss&runtime=openclaw"
    )
    live_body = _get_json(client, "/api/entitlement/has-runtime?runtime=openclaw")
    for k in ("current_tier", "current_tier_rank"):
        assert at_body[k] == live_body[k], k


def test_endpoint_has_runtime_at_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-runtime-at?tier=pro&runtime=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["has_runtime_at"] is False


def test_endpoint_has_runtime_at_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_runtime_at", _boom)
    resp = client.get(
        "/api/entitlement/has-runtime-at?tier=pro&runtime=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["has_runtime_at"] is False


# ── Scalar-vs-endpoint parity ─────────────────────────────────────────────


def test_endpoint_has_feature_at_scalar_vs_endpoint_parity(client, ent):
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        for feat in ("fleet", "nemo_governance", "sso"):
            if feat not in ent.ALL_FEATURES:
                continue
            body = _get_json(
                client,
                f"/api/entitlement/has-feature-at?tier={tier}&feature={feat}",
            )
            assert body["has_feature_at"] is ent.has_feature_at(tier, feat), (
                tier,
                feat,
            )


def test_endpoint_has_runtime_at_scalar_vs_endpoint_parity(client, ent):
    """Endpoint value equals the scalar for every (tier, canonical runtime)
    pair -- the endpoint's own upstream canonicalisation is what makes
    the alias-input variant work, so we test against canonical ids
    here (aliases are covered by a separate test above)."""
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        for rt in ("openclaw", "claude_code", "codex"):
            if rt not in ent.ALL_RUNTIMES:
                continue
            body = _get_json(
                client,
                f"/api/entitlement/has-runtime-at?tier={tier}&runtime={rt}",
            )
            assert body["has_runtime_at"] is ent.has_runtime_at(tier, rt), (
                tier,
                rt,
            )


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-feature-at",
        "/api/entitlement/has-feature-at?tier=",
        "/api/entitlement/has-feature-at?feature=",
        "/api/entitlement/has-feature-at?tier=&feature=",
        "/api/entitlement/has-feature-at?tier=pro",
        "/api/entitlement/has-feature-at?feature=fleet",
        "/api/entitlement/has-feature-at?tier=pro&feature=fleet",
        "/api/entitlement/has-feature-at?tier=oss&feature=fleet",
        "/api/entitlement/has-feature-at?tier=pro&feature=bogus",
        "/api/entitlement/has-feature-at?tier=mars&feature=fleet",
        "/api/entitlement/has-feature-at?tier=%20PRO%20&feature=%20FLEET%20",
    ],
)
def test_endpoint_has_feature_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _FEATURE_KEYS
    assert isinstance(body["tier"], str)
    assert isinstance(body["feature"], str)
    assert isinstance(body["has_feature_at"], bool)
    assert isinstance(body["allowed"], bool)
    assert body["has_feature_at"] == body["allowed"]
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["required_tier_rank"], int)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-runtime-at",
        "/api/entitlement/has-runtime-at?tier=",
        "/api/entitlement/has-runtime-at?runtime=",
        "/api/entitlement/has-runtime-at?tier=&runtime=",
        "/api/entitlement/has-runtime-at?tier=pro",
        "/api/entitlement/has-runtime-at?runtime=openclaw",
        "/api/entitlement/has-runtime-at?tier=pro&runtime=openclaw",
        "/api/entitlement/has-runtime-at?tier=oss&runtime=claude_code",
        "/api/entitlement/has-runtime-at?tier=pro&runtime=claude-code",
        "/api/entitlement/has-runtime-at?tier=pro&runtime=bogus_rt",
        "/api/entitlement/has-runtime-at?tier=mars&runtime=openclaw",
        "/api/entitlement/has-runtime-at?tier=%20PRO%20&runtime=%20OPENCLAW%20",
    ],
)
def test_endpoint_has_runtime_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _RUNTIME_KEYS
    assert isinstance(body["tier"], str)
    assert isinstance(body["runtime"], str)
    assert isinstance(body["has_runtime_at"], bool)
    assert isinstance(body["allowed"], bool)
    assert body["has_runtime_at"] == body["allowed"]
    assert isinstance(body["perspective_tier_rank"], int)


# ── Enforced-mode grace-independence at endpoint level ────────────────────


def test_endpoint_has_feature_at_grace_independence(client, enforced_client):
    """Endpoint answers for the SAME (perspective, feature) pair are
    identical under grace vs enforce -- perspective-shaped by design.
    Only the ``grace`` / ``enforced`` envelope slots differ."""
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        for feat in ("fleet", "sso"):
            grace_body = _get_json(
                client,
                f"/api/entitlement/has-feature-at?tier={tier}&feature={feat}",
            )
            enf_body = _get_json(
                enforced_client,
                f"/api/entitlement/has-feature-at?tier={tier}&feature={feat}",
            )
            assert grace_body["has_feature_at"] == enf_body["has_feature_at"], (
                tier,
                feat,
            )
            # The two envelopes should diverge ONLY on the resolver-shaped
            # slots (grace / enforced / current_tier / current_tier_rank).
            assert grace_body["required_tier"] == enf_body["required_tier"]
            assert grace_body["required_tier_rank"] == enf_body["required_tier_rank"]
            assert grace_body["perspective_tier_rank"] == enf_body["perspective_tier_rank"]


def test_endpoint_has_runtime_at_grace_independence(client, enforced_client):
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        for rt in ("openclaw", "claude_code"):
            grace_body = _get_json(
                client,
                f"/api/entitlement/has-runtime-at?tier={tier}&runtime={rt}",
            )
            enf_body = _get_json(
                enforced_client,
                f"/api/entitlement/has-runtime-at?tier={tier}&runtime={rt}",
            )
            assert grace_body["has_runtime_at"] == enf_body["has_runtime_at"], (
                tier,
                rt,
            )
