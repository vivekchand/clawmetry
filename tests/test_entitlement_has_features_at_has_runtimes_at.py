"""Tests for the plural ``has_features_at`` / ``has_runtimes_at`` hypothetical
-perspective boolean-gate scalar helpers and their paired
``/api/entitlement/has-features-at`` / ``/api/entitlement/has-runtimes-at``
endpoints.

Plural what-if siblings of :func:`has_feature_at` / :func:`has_runtime_at` on
the same axis, in the same relationship :func:`has_features` /
:func:`has_runtimes` have to :func:`has_feature` / :func:`has_runtime`. Fills
the plural ``_at`` slot in the grant-axis boolean-gate family so a pricing
matrix that gates on a BUNDLE (``fleet + otel_export + sso -- Available in
Enterprise``) can bind ONE boolean per (perspective, bundle) cell off ONE URL
each, instead of walking the singular :func:`has_feature_at` per item and AND
-ing on the client.

This file pins:

1. Scalar semantics: empty / None / non-iterable bundle, unknown
   perspective, unknown / non-string / empty item id, all-free / all-paid /
   mixed bundle across every tier.
2. Perspective-shaped grace-independence: ``has_features_at("oss",
   [<paid>...])`` is ``False`` in BOTH grace and enforce (unlike the live
   plural :func:`has_features` sibling which returns ``True`` in grace) --
   the whole point of the ``_at`` slot is to render the would-be-locked
   state alongside the live grant.
3. Runtime-axis alias posture: scalar is strict (no
   :func:`canonical_runtime` resolution -- matches sibling
   :func:`has_runtime_at`); endpoint canonicalises per-token upstream
   (matches sibling ``/has-runtimes`` endpoint).
4. Endpoint envelope shape (fixed 15-key set) across every input branch.
5. Never-4xx / never-5xx guarantees on both endpoints.
6. Cross-consistency with the sibling
   ``/api/entitlement/min-tier-for-features`` /
   ``/api/entitlement/min-tier-for-runtimes`` endpoints -- same
   ``required_tier`` for the same bundle.
7. Cross-consistency with the singular
   ``/api/entitlement/has-feature-at`` / ``/has-runtime-at`` endpoints on
   the ``current_tier`` / ``perspective_tier_rank`` slots and on the AND-
   fold of per-item ``allowed`` bits.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- matches the
    sibling ``test_entitlement_has_feature_at_has_runtime_at.py`` fixture
    so the plural perspective assertions here reproduce the same install
    state the singular ``_at`` gates are pinned against."""
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
    ``ent.grace`` off. Included to pin the perspective-shaped grace
    -independence invariant -- the plural ``_at`` scalars return the same
    answer under grace vs enforce for the same (perspective, bundle) pair."""
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

_FEATURES_KEYS = {
    "tier",
    "features",
    "unknown",
    "kind",
    "count",
    "has_features_at",
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
_RUNTIMES_KEYS = {
    "tier",
    "runtimes",
    "unknown",
    "kind",
    "count",
    "has_runtimes_at",
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


# ── has_features_at scalar ────────────────────────────────────────────────


def test_has_features_at_all_free_is_true_on_every_tier(ent):
    """A bundle of ONLY free features is granted from every real tier
    (the free floor is baked into ``_hypothetical_entitlement``)."""
    free = sorted(ent.FREE_FEATURES)
    if not free:
        pytest.skip("no FREE_FEATURES configured")
    for tier in ent._TIER_ORDER:
        assert ent.has_features_at(tier, free) is True, tier


def test_has_features_at_all_paid_is_false_on_oss(ent):
    """OSS never statically grants any paid feature (perspective-shaped:
    ``False`` even in grace, whereas the live sibling :func:`has_features`
    reports ``True`` in grace for the same bundle)."""
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    assert ent.has_features_at("oss", paid) is False


def test_has_features_at_all_paid_matches_per_item_and_fold(ent):
    """The plural fold equals the per-item AND-fold of the singular
    :func:`has_feature_at` for every tier + all-paid bundle."""
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    for tier in ent._TIER_ORDER:
        expected = all(ent.has_feature_at(tier, f) for f in paid)
        assert ent.has_features_at(tier, paid) is expected, tier


def test_has_features_at_mixed_free_and_paid_on_oss_is_false(ent):
    """Mixed bundle on OSS collapses to False -- the paid item denies
    the whole fold even though the free item is granted."""
    free = next(iter(ent.FREE_FEATURES), None)
    paid = next(iter(ent.PAID_FEATURES), None)
    if free is None or paid is None:
        pytest.skip("need at least one FREE and one PAID feature")
    assert ent.has_features_at("oss", [free, paid]) is False


def test_has_features_at_any_unknown_is_false_in_grace(ent):
    """Even in grace, an unknown item collapses the fold to False --
    catches typos at the callsite before enforcement flips on."""
    assert ent.has_features_at("pro", ["fleet", "bogus_id"]) is False
    assert ent.has_features_at("pro", ["bogus_id"]) is False


def test_has_features_at_empty_iterable_is_false(ent):
    """Empty iterable collapses to False (strict callsite-typo posture) --
    matches the plural :func:`has_features` empty-fold posture."""
    assert ent.has_features_at("pro", []) is False
    assert ent.has_features_at("pro", ()) is False
    assert ent.has_features_at("pro", iter(())) is False


def test_has_features_at_none_is_false(ent):
    assert ent.has_features_at("pro", None) is False  # type: ignore[arg-type]


def test_has_features_at_non_iterable_is_false(ent):
    assert ent.has_features_at("pro", 123) is False  # type: ignore[arg-type]
    assert ent.has_features_at("pro", object()) is False  # type: ignore[arg-type]


def test_has_features_at_unknown_perspective_is_false(ent):
    """Perspective not in :data:`_TIER_ORDER` -> fail-closed False."""
    for bad in ["", " ", "mars", "pro_plus", "unknown_tier"]:
        assert ent.has_features_at(bad, ["fleet"]) is False, bad


def test_has_features_at_non_string_perspective_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_features_at(bad, ["fleet"]) is False


def test_has_features_at_case_insensitive_perspective(ent):
    """Whitespace / casing on the perspective normalises via
    ``strip().lower()``."""
    paid = next(iter(ent.PAID_FEATURES), None)
    if paid is None:
        pytest.skip("no PAID_FEATURES configured")
    live = ent.has_features_at("pro", [paid])
    assert ent.has_features_at("  PRO  ", [paid]) is live
    assert ent.has_features_at("Pro", [paid]) is live


def test_has_features_at_grace_independence(ent, enforced):
    """The plural ``_at`` scalar is IDENTICAL under grace vs enforce for
    the same (perspective, bundle) pair. Diverges from the live plural
    :func:`has_features` which flips from True in grace to False in
    enforce for a paid bundle."""
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    for tier in ent._TIER_ORDER:
        assert ent.has_features_at(tier, paid) is enforced.has_features_at(
            tier, paid
        ), tier


def test_has_features_at_never_raises_on_delegate_blowup(monkeypatch, ent):
    """Any blowup in the per-item :func:`has_feature_at` collapses to
    ``False`` so a pricing matrix cell keeps rendering."""

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "has_feature_at", _boom)
    assert ent.has_features_at("pro", ["fleet", "sso"]) is False


# ── has_runtimes_at scalar ────────────────────────────────────────────────


def test_has_runtimes_at_all_free_is_true_on_every_tier(ent):
    free = sorted(ent.FREE_RUNTIMES)
    if not free:
        pytest.skip("no FREE_RUNTIMES configured")
    for tier in ent._TIER_ORDER:
        assert ent.has_runtimes_at(tier, free) is True, tier


def test_has_runtimes_at_all_paid_is_false_on_oss(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    assert ent.has_runtimes_at("oss", paid) is False


def test_has_runtimes_at_all_paid_matches_per_item_fold(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    for tier in ent._TIER_ORDER:
        expected = all(ent.has_runtime_at(tier, rt) for rt in paid)
        assert ent.has_runtimes_at(tier, paid) is expected, tier


def test_has_runtimes_at_mixed_free_and_paid_on_oss_is_false(ent):
    free = next(iter(ent.FREE_RUNTIMES), None)
    paid = next(iter(ent.PAID_RUNTIMES), None)
    if free is None or paid is None:
        pytest.skip("need at least one FREE and one PAID runtime")
    assert ent.has_runtimes_at("oss", [free, paid]) is False


def test_has_runtimes_at_scalar_does_not_alias_resolve(ent):
    """Strict alias posture mirrors the singular :func:`has_runtime_at`
    exactly: ``"claude-code"`` is not in :data:`ALL_RUNTIMES` after
    ``.strip().lower()``, so an alias input at scalar layer collapses
    the fold to ``False``."""
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code runtime not registered")
    assert ent.has_runtimes_at("pro", ["claude-code"]) is False


def test_has_runtimes_at_any_unknown_is_false_in_grace(ent):
    assert ent.has_runtimes_at("pro", ["openclaw", "bogus_rt"]) is False
    assert ent.has_runtimes_at("pro", ["bogus_rt"]) is False


def test_has_runtimes_at_empty_iterable_is_false(ent):
    assert ent.has_runtimes_at("pro", []) is False
    assert ent.has_runtimes_at("pro", ()) is False


def test_has_runtimes_at_none_is_false(ent):
    assert ent.has_runtimes_at("pro", None) is False  # type: ignore[arg-type]


def test_has_runtimes_at_non_iterable_is_false(ent):
    assert ent.has_runtimes_at("pro", 123) is False  # type: ignore[arg-type]


def test_has_runtimes_at_unknown_perspective_is_false(ent):
    for bad in ["", " ", "mars", "pro-plus", "unknown_tier"]:
        assert ent.has_runtimes_at(bad, ["openclaw"]) is False, bad


def test_has_runtimes_at_non_string_perspective_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_runtimes_at(bad, ["openclaw"]) is False


def test_has_runtimes_at_grace_independence(ent, enforced):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    for tier in ent._TIER_ORDER:
        assert ent.has_runtimes_at(tier, paid) is enforced.has_runtimes_at(
            tier, paid
        ), tier


def test_has_runtimes_at_never_raises_on_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "has_runtime_at", _boom)
    assert ent.has_runtimes_at("pro", ["openclaw"]) is False


# ── /api/entitlement/has-features-at endpoint ────────────────────────────


def test_endpoint_has_features_at_shape_default(client):
    """Missing all args -> 200 with 15-key envelope and fail-closed False."""
    body = _get_json(client, "/api/entitlement/has-features-at")
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tier"] == ""
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["kind"] == "features"
    assert body["count"] == 0
    assert body["has_features_at"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["perspective_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_endpoint_has_features_at_all_free_on_every_tier(client, ent):
    free = sorted(ent.FREE_FEATURES)
    if not free:
        pytest.skip("no FREE_FEATURES configured")
    csv = ",".join(free)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        body = _get_json(
            client,
            f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
        )
        assert body["tier"] == tier
        assert body["has_features_at"] is True, tier
        assert body["allowed"] is True
        assert body["count"] == len(free)
        assert body["unknown"] == []


def test_endpoint_has_features_at_paid_on_oss_is_denied(client, ent):
    """The whole point of the plural ``_at`` slot: OSS reports
    ``allowed=false`` for a paid bundle EVEN IN GRACE, unlike the live
    ``/has-features`` sibling which returns ``true`` in grace on the
    same bundle."""
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    csv = ",".join(paid)
    body = _get_json(
        client, f"/api/entitlement/has-features-at?tier=oss&features={csv}"
    )
    assert body["has_features_at"] is False
    assert body["allowed"] is False
    assert body["perspective_tier_rank"] == 0
    # Live sibling grace divergence: same bundle on the live endpoint reports
    # True in grace via the resolver's grace pass-through.
    live = _get_json(client, f"/api/entitlement/has-features?features={csv}")
    assert live["has_features"] is True
    assert body["current_tier"] == live["current_tier"]
    assert body["current_tier_rank"] == live["current_tier_rank"]


def test_endpoint_has_features_at_unknown_token_collapses(client):
    """Unknown token echoes into ``unknown`` and collapses the bundle
    to ``has_features_at=False`` -- matches the sibling
    :func:`_has_bundle_body` typo posture."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at?tier=pro&features=fleet,bogus_id",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["has_features_at"] is False
    assert "bogus_id" in body["unknown"]


def test_endpoint_has_features_at_unknown_tier_never_4xx(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at?tier=mars&features=fleet",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tier"] == "mars"
    assert body["has_features_at"] is False
    assert body["perspective_tier_rank"] == -1


def test_endpoint_has_features_at_case_insensitive_tier(client, ent):
    paid = next(iter(ent.PAID_FEATURES), None)
    if paid is None:
        pytest.skip("no PAID_FEATURES configured")
    canonical = _get_json(
        client, f"/api/entitlement/has-features-at?tier=pro&features={paid}"
    )
    upper = _get_json(
        client, f"/api/entitlement/has-features-at?tier=%20PRO%20&features={paid}"
    )
    assert upper["tier"] == "pro"
    assert upper["has_features_at"] is canonical["has_features_at"]


def test_endpoint_has_features_at_required_tier_parity(client, ent):
    """``required_tier`` byte-equals the sibling
    ``/api/entitlement/min-tier-for-features`` answer for the same
    bundle -- a UI wiring both URLs into the same paywall matrix
    cannot see inconsistent tier state."""
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    csv = ",".join(paid)
    body = _get_json(
        client, f"/api/entitlement/has-features-at?tier=pro&features={csv}"
    )
    min_body = _get_json(
        client, f"/api/entitlement/min-tier-for-features?features={csv}"
    )
    assert body["required_tier"] == min_body["required_tier"]


def test_endpoint_has_features_at_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-features-at?tier=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["has_features_at"] is False
    assert body["current_tier"] == "oss"


def test_endpoint_has_features_at_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_features_at", _boom)
    resp = client.get(
        "/api/entitlement/has-features-at?tier=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["has_features_at"] is False


# ── /api/entitlement/has-runtimes-at endpoint ────────────────────────────


def test_endpoint_has_runtimes_at_shape_default(client):
    body = _get_json(client, "/api/entitlement/has-runtimes-at")
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["tier"] == ""
    assert body["runtimes"] == []
    assert body["kind"] == "runtimes"
    assert body["has_runtimes_at"] is False
    assert body["perspective_tier_rank"] == -1


def test_endpoint_has_runtimes_at_all_free_on_every_tier(client, ent):
    free = sorted(ent.FREE_RUNTIMES)
    if not free:
        pytest.skip("no FREE_RUNTIMES configured")
    csv = ",".join(free)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        body = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
        )
        assert body["has_runtimes_at"] is True, tier


def test_endpoint_has_runtimes_at_paid_on_oss_is_denied(client, ent):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    csv = ",".join(paid)
    body = _get_json(
        client, f"/api/entitlement/has-runtimes-at?tier=oss&runtimes={csv}"
    )
    assert body["has_runtimes_at"] is False
    assert body["perspective_tier_rank"] == 0


def test_endpoint_has_runtimes_at_alias_canonicalises_upstream(client, ent):
    """Alias input at URL level collapses per-token to the canonical form
    BEFORE delegating to the strict scalar. Matches the sibling
    ``/has-runtimes`` endpoint's own upstream canonicalise pattern."""
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code runtime not registered")
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=claude-code,openclaw",
    )
    # Canonicalised into the known list.
    assert "claude_code" in body["runtimes"]
    assert "openclaw" in body["runtimes"]
    assert body["unknown"] == []
    # And Pro grants claude_code (all-known bundle on granting tier).
    assert body["has_runtimes_at"] is True


def test_endpoint_has_runtimes_at_unknown_token_collapses(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=openclaw,bogus_rt",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["has_runtimes_at"] is False
    assert "bogus_rt" in body["unknown"]


def test_endpoint_has_runtimes_at_unknown_tier_never_4xx(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at?tier=mars&runtimes=openclaw",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["has_runtimes_at"] is False


def test_endpoint_has_runtimes_at_required_tier_parity(client, ent):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    csv = ",".join(paid)
    body = _get_json(
        client, f"/api/entitlement/has-runtimes-at?tier=pro&runtimes={csv}"
    )
    min_body = _get_json(
        client, f"/api/entitlement/min-tier-for-runtimes?runtimes={csv}"
    )
    assert body["required_tier"] == min_body["required_tier"]


def test_endpoint_has_runtimes_at_current_tier_parity_with_live(client):
    """Shares the live resolver context slots with the sibling live
    ``/has-runtimes`` endpoint."""
    at_body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at?tier=oss&runtimes=openclaw",
    )
    live = _get_json(
        client, "/api/entitlement/has-runtimes?runtimes=openclaw"
    )
    for k in ("current_tier", "current_tier_rank"):
        assert at_body[k] == live[k], k


def test_endpoint_has_runtimes_at_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["has_runtimes_at"] is False


def test_endpoint_has_runtimes_at_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_runtimes_at", _boom)
    resp = client.get(
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["has_runtimes_at"] is False


# ── Scalar-vs-endpoint parity ─────────────────────────────────────────────


def test_endpoint_has_features_at_scalar_vs_endpoint_parity(client, ent):
    paid = sorted(ent.PAID_FEATURES)
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    csv = ",".join(paid[:3])
    subset = paid[:3]
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        body = _get_json(
            client,
            f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
        )
        assert body["has_features_at"] is ent.has_features_at(tier, subset), tier


def test_endpoint_has_runtimes_at_scalar_vs_endpoint_parity(client, ent):
    paid = sorted(ent.PAID_RUNTIMES)
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    csv = ",".join(paid[:3])
    subset = paid[:3]
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        body = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
        )
        assert body["has_runtimes_at"] is ent.has_runtimes_at(tier, subset), tier


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-features-at",
        "/api/entitlement/has-features-at?tier=",
        "/api/entitlement/has-features-at?features=",
        "/api/entitlement/has-features-at?tier=&features=",
        "/api/entitlement/has-features-at?tier=pro",
        "/api/entitlement/has-features-at?features=fleet",
        "/api/entitlement/has-features-at?tier=pro&features=fleet",
        "/api/entitlement/has-features-at?tier=oss&features=fleet",
        "/api/entitlement/has-features-at?tier=pro&features=fleet,sso",
        "/api/entitlement/has-features-at?tier=pro&features=bogus",
        "/api/entitlement/has-features-at?tier=mars&features=fleet",
        "/api/entitlement/has-features-at?tier=%20PRO%20&features=%20FLEET%20",
    ],
)
def test_endpoint_has_features_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _FEATURES_KEYS
    assert isinstance(body["tier"], str)
    assert isinstance(body["features"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["kind"], str)
    assert isinstance(body["count"], int)
    assert isinstance(body["has_features_at"], bool)
    assert isinstance(body["allowed"], bool)
    assert body["has_features_at"] == body["allowed"]
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["required_tier_rank"], int)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-runtimes-at",
        "/api/entitlement/has-runtimes-at?tier=",
        "/api/entitlement/has-runtimes-at?runtimes=",
        "/api/entitlement/has-runtimes-at?tier=&runtimes=",
        "/api/entitlement/has-runtimes-at?tier=pro",
        "/api/entitlement/has-runtimes-at?runtimes=openclaw",
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=openclaw",
        "/api/entitlement/has-runtimes-at?tier=oss&runtimes=claude_code",
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=openclaw,claude_code",
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=claude-code",
        "/api/entitlement/has-runtimes-at?tier=pro&runtimes=bogus_rt",
        "/api/entitlement/has-runtimes-at?tier=mars&runtimes=openclaw",
        "/api/entitlement/has-runtimes-at?tier=%20PRO%20&runtimes=%20OPENCLAW%20",
    ],
)
def test_endpoint_has_runtimes_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert isinstance(body["tier"], str)
    assert isinstance(body["runtimes"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["has_runtimes_at"], bool)
    assert isinstance(body["allowed"], bool)
    assert body["has_runtimes_at"] == body["allowed"]
    assert isinstance(body["perspective_tier_rank"], int)


# ── Enforced-mode grace-independence at endpoint level ────────────────────


def test_endpoint_has_features_at_grace_independence(client, enforced_client, ent):
    """Endpoint answers for the SAME (perspective, bundle) pair are
    identical under grace vs enforce -- perspective-shaped by design.
    Only the ``grace`` / ``enforced`` envelope slots differ."""
    paid = sorted(ent.PAID_FEATURES)[:2]
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    csv = ",".join(paid)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        grace_body = _get_json(
            client,
            f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
        )
        enf_body = _get_json(
            enforced_client,
            f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
        )
        assert grace_body["has_features_at"] == enf_body["has_features_at"], tier
        assert grace_body["required_tier"] == enf_body["required_tier"]
        assert grace_body["required_tier_rank"] == enf_body["required_tier_rank"]
        assert (
            grace_body["perspective_tier_rank"] == enf_body["perspective_tier_rank"]
        )


def test_endpoint_has_runtimes_at_grace_independence(client, enforced_client, ent):
    paid = sorted(ent.PAID_RUNTIMES)[:2]
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    csv = ",".join(paid)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        grace_body = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
        )
        enf_body = _get_json(
            enforced_client,
            f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
        )
        assert grace_body["has_runtimes_at"] == enf_body["has_runtimes_at"], tier


# ── Cross-consistency with singular /has-feature-at / /has-runtime-at ─────


def test_endpoint_has_features_at_matches_singular_and_fold(client, ent):
    """Plural URL's ``allowed`` bit equals the per-item AND-fold of the
    singular ``/has-feature-at`` ``allowed`` bits for the same bundle."""
    paid = sorted(ent.PAID_FEATURES)[:3]
    if not paid:
        pytest.skip("no PAID_FEATURES configured")
    csv = ",".join(paid)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        plural = _get_json(
            client,
            f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
        )
        singular_bits = []
        for f in paid:
            s = _get_json(
                client,
                f"/api/entitlement/has-feature-at?tier={tier}&feature={f}",
            )
            singular_bits.append(bool(s["has_feature_at"]))
        assert plural["has_features_at"] is all(singular_bits), tier


def test_endpoint_has_runtimes_at_matches_singular_and_fold(client, ent):
    paid = sorted(ent.PAID_RUNTIMES)[:3]
    if not paid:
        pytest.skip("no PAID_RUNTIMES configured")
    csv = ",".join(paid)
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        plural = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
        )
        singular_bits = []
        for rt in paid:
            s = _get_json(
                client,
                f"/api/entitlement/has-runtime-at?tier={tier}&runtime={rt}",
            )
            singular_bits.append(bool(s["has_runtime_at"]))
        assert plural["has_runtimes_at"] is all(singular_bits), tier
