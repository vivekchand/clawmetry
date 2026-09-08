"""Tests for the path-shaped ``has_features_at_path`` /
``has_runtimes_at_path`` boolean-fold scalars and their paired
``/api/entitlement/has-features-at-path`` /
``/api/entitlement/has-runtimes-at-path`` endpoints.

Path-shaped siblings of :func:`has_features_at` /
:func:`has_runtimes_at` and boolean-fold complements of
:func:`missing_features_at_path` / :func:`missing_runtimes_at_path`:
fixes ONE bundle and sweeps across every rung between ``from`` and
``to``, returning one row per rung with the fold boolean at that rung.
Lets an upgrade-walkthrough header render "at which tier does this
whole bundle unlock?" off ONE URL.

This file pins:

1. Scalar walk semantics byte-parity with :func:`feature_catalog_path`
   / :func:`missing_features_at_path` (rung ``tier`` sequence,
   direction detection, endpoint semantics, same-rank sibling filter).
2. Per-rung ``has_<axis>_at`` byte-parity with the scalar
   :func:`has_features_at` / :func:`has_runtimes_at` for the same
   (rung, bundle) pair.
3. Bundle-fold posture inherited from the ``_at`` siblings (fail-closed
   posture, NOT vacuous-truth): empty / None / non-iterable bundle ->
   every rung's fold is ``False``; unknown / typo tokens collapse every
   rung's fold to ``False``.
4. Unknown-endpoint short-circuit: either endpoint unknown -> scalar
   returns ``None``; endpoint returns 200 with ``path=[]`` and
   ``direction="unknown"`` (never 4xxs -- matches
   ``/has-features-at`` posture).
5. Direction semantics: ``upgrade`` / ``downgrade`` / ``lateral`` /
   ``identity`` / ``unknown``.
6. Grace-independence: same answer under grace on vs enforce for the
   same (from, to, bundle) triple.
7. Runtime scalar alias posture: no scalar-level canonicalisation --
   ``has_runtimes_at_path(f, t, ["claude-code"])`` collapses every
   rung's fold to ``False``; the paired endpoint canonicalises
   upstream (alias-and-canonical pair dedups to ONE entry in
   ``runtimes`` and therefore ONE fold input on every rung).
8. Never-raises on delegate blowup: log-and-return ``None`` at scalar
   layer; empty-path fallback envelope at endpoint layer (never 5xxs).
9. Endpoint envelope shape (fixed key set) across every input branch,
   including the unknown-endpoint branch.
10. Cross-consistency with the sibling ``/feature-catalog-path`` /
    ``/missing-features-at-path`` walks: same rung ``tier`` sequence
    rung-for-rung.
11. Rollup fields ``allowed_count`` / ``all_allowed`` / ``any_allowed``
    fold per-row ``has_<axis>_at`` as documented on
    :func:`_has_bundle_at_path_body`.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
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


# ── Envelope shape ─────────────────────────────────────────────────────────

_FEATURES_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "features",
    "unknown",
    "path",
    "kind",
    "count",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_RUNTIMES_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "runtimes",
    "unknown",
    "path",
    "kind",
    "count",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_features_at_path scalar ────────────────────────────────────────────


def test_scalar_identity_endpoints_returns_empty_path(ent):
    """``from == to`` -> empty path (identity branch)."""
    for tier in ent._TIER_ORDER:
        assert ent.has_features_at_path(tier, tier, ["fleet"]) == []


def test_scalar_unknown_endpoint_returns_none(ent):
    assert ent.has_features_at_path("bogus", "pro", ["fleet"]) is None
    assert ent.has_features_at_path("oss", "bogus", ["fleet"]) is None
    assert ent.has_features_at_path("bogus_a", "bogus_b", ["fleet"]) is None
    assert ent.has_features_at_path("", "pro", ["fleet"]) is None
    assert ent.has_features_at_path(None, "pro", ["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_upgrade_path_has_rows(ent):
    path = ent.has_features_at_path("oss", "enterprise", ["fleet", "sso"])
    assert isinstance(path, list) and len(path) >= 1
    # Row shape
    for row in path:
        assert set(row.keys()) == {
            "tier",
            "tier_label",
            "tier_rank",
            "has_features_at",
        }
        assert isinstance(row["has_features_at"], bool)


def test_scalar_downgrade_path_has_rows(ent):
    path = ent.has_features_at_path("enterprise", "oss", ["fleet", "sso"])
    assert isinstance(path, list) and len(path) >= 1


def test_scalar_lateral_path_single_row(ent):
    """Same-rank different-id endpoints -> single-row path carrying the
    ``has_features_at`` at ``to``."""
    same_rank_pairs = [
        (a, b)
        for a in ent._TIER_ORDER
        for b in ent._TIER_ORDER
        if a != b
        and ent._TIER_RANK.get(a) == ent._TIER_RANK.get(b)
        and a in ent._TIER_FEATURES
        and b in ent._TIER_FEATURES
    ]
    if not same_rank_pairs:
        pytest.skip("no same-rank pair on this build")
    for f, t in same_rank_pairs[:3]:
        path = ent.has_features_at_path(f, t, ["fleet"])
        assert isinstance(path, list) and len(path) == 1
        assert path[0]["tier"] == t


def test_scalar_per_rung_matches_has_features_at(ent):
    """Per-rung ``has_features_at`` byte-equals
    ``has_features_at(rung, bundle)`` for the same input -- the drift-
    blocker parity property."""
    bundle = ["fleet", "sso", "otel_export"]
    path = ent.has_features_at_path("oss", "enterprise", bundle)
    assert path is not None
    for row in path:
        assert row["has_features_at"] == ent.has_features_at(row["tier"], bundle)


def test_scalar_rungs_match_feature_catalog_path(ent):
    """Rung sequence byte-parity with :func:`feature_catalog_path` --
    both walk the same ``_PURCHASABLE_TIERS`` filter + sort key."""
    bundle = ["fleet"]
    ours = ent.has_features_at_path("oss", "enterprise", bundle)
    catalog = ent.feature_catalog_path("oss", "enterprise")
    assert ours is not None and catalog is not None
    assert [r["tier"] for r in ours] == [r["tier"] for r in catalog]


def test_scalar_rungs_match_missing_features_at_path(ent):
    """Rung sequence byte-parity with the complement helper
    :func:`missing_features_at_path` -- both walk the same
    ``_PURCHASABLE_TIERS`` filter + sort key so paired UI columns
    always line up rung-for-rung."""
    bundle = ["fleet"]
    ours = ent.has_features_at_path("oss", "enterprise", bundle)
    complement = ent.missing_features_at_path("oss", "enterprise", bundle)
    assert ours is not None and complement is not None
    assert [r["tier"] for r in ours] == [r["tier"] for r in complement]


def test_scalar_empty_bundle_every_rung_false(ent):
    """Empty bundle -- inherits the fail-closed posture from
    :func:`has_features_at` (refuses the vacuous-truth fold)."""
    path = ent.has_features_at_path("oss", "enterprise", [])
    assert path is not None
    for row in path:
        assert row["has_features_at"] is False


def test_scalar_none_bundle_every_rung_false(ent):
    path = ent.has_features_at_path("oss", "enterprise", None)
    assert path is not None
    for row in path:
        assert row["has_features_at"] is False


def test_scalar_non_iterable_bundle_every_rung_false(ent):
    path = ent.has_features_at_path("oss", "enterprise", 123)
    assert path is not None
    for row in path:
        assert row["has_features_at"] is False


def test_scalar_unknown_token_every_rung_false(ent):
    """Typo posture inherited from :func:`has_features_at`: any
    unknown item collapses the fold to ``False`` on every rung."""
    path = ent.has_features_at_path("oss", "enterprise", ["bogus_id"])
    assert path is not None
    for row in path:
        assert row["has_features_at"] is False


def test_scalar_grace_independence(ent, enforced):
    bundle = ["fleet", "sso"]
    a = ent.has_features_at_path("oss", "enterprise", bundle)
    b = enforced.has_features_at_path("oss", "enterprise", bundle)
    assert a == b


def test_scalar_upgrade_has_features_monotone_grow(ent):
    """As you climb rungs, per-rung ``has_features_at`` only flips
    ``False -> True`` (grants accumulate; never revoke on the way up)."""
    bundle = sorted(ent.PAID_FEATURES)
    path = ent.has_features_at_path("oss", "enterprise", bundle)
    assert path is not None
    seen_true = False
    for row in path:
        if seen_true:
            assert row["has_features_at"] is True, row["tier"]
        if row["has_features_at"]:
            seen_true = True


def test_scalar_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_features_at", _boom)
    assert ent.has_features_at_path("oss", "pro", ["fleet"]) is None


# ── has_runtimes_at_path scalar ────────────────────────────────────────────


def test_scalar_runtimes_identity_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.has_runtimes_at_path(tier, tier, ["claude_code"]) == []


def test_scalar_runtimes_unknown_endpoint(ent):
    assert ent.has_runtimes_at_path("bogus", "pro", ["claude_code"]) is None
    assert ent.has_runtimes_at_path("oss", "bogus", ["claude_code"]) is None


def test_scalar_runtimes_upgrade_path_rows(ent):
    path = ent.has_runtimes_at_path("oss", "enterprise", ["claude_code"])
    assert isinstance(path, list) and len(path) >= 1
    for row in path:
        assert set(row.keys()) == {
            "tier",
            "tier_label",
            "tier_rank",
            "has_runtimes_at",
        }


def test_scalar_runtimes_per_rung_matches_has_runtimes_at(ent):
    bundle = ["claude_code", "openclaw"]
    path = ent.has_runtimes_at_path("oss", "enterprise", bundle)
    assert path is not None
    for row in path:
        assert row["has_runtimes_at"] == ent.has_runtimes_at(row["tier"], bundle)


def test_scalar_runtimes_strict_alias_posture(ent):
    """Scalar layer does NOT resolve aliases -- ``claude-code`` (with a
    hyphen) is not in :data:`ALL_RUNTIMES`, so :func:`has_runtimes_at`
    collapses every rung's fold to ``False`` (matches ``has_runtimes_at``
    docstring; endpoint canonicalises upstream)."""
    path = ent.has_runtimes_at_path("oss", "enterprise", ["claude-code"])
    assert path is not None
    for row in path:
        assert row["has_runtimes_at"] is False


def test_scalar_runtimes_grace_independence(ent, enforced):
    bundle = ["claude_code", "cursor"]
    a = ent.has_runtimes_at_path("oss", "enterprise", bundle)
    b = enforced.has_runtimes_at_path("oss", "enterprise", bundle)
    assert a == b


def test_scalar_runtimes_never_raises(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_runtimes_at", _boom)
    assert ent.has_runtimes_at_path("oss", "pro", ["claude_code"]) is None


# ── Endpoint: envelope shape ───────────────────────────────────────────────


def test_endpoint_features_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"


def test_endpoint_runtimes_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"


def test_endpoint_features_missing_from_still_200(client):
    """Never 4xxs on missing ``from=``."""
    resp = client.get(
        "/api/entitlement/has-features-at-path?to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_missing_to_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path?from=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_unknown_tier_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path?from=bogus&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_identity_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path?from=oss&to=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_endpoint_features_upgrade_direction(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    if body["from_rank"] == body["to_rank"]:
        pytest.skip("no rank difference on this build")
    assert body["direction"] == "upgrade"
    assert body["path_length"] == len(body["path"])
    assert body["path_length"] >= 1


def test_endpoint_features_downgrade_direction(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=enterprise&to=oss&features=fleet",
    )
    if body["from_rank"] == body["to_rank"]:
        pytest.skip("no rank difference on this build")
    assert body["direction"] == "downgrade"


# ── Endpoint: per-rung parity with sibling ``/has-features-at`` ────────────


def test_endpoint_features_per_rung_matches_has_features_at(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    for row in body["path"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/has-features-at?tier={row['tier']}&features=fleet,sso",
        )
        assert row["has_features_at"] == sibling["allowed"], row["tier"]


def test_endpoint_runtimes_per_rung_matches_has_runtimes_at(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path?from=oss&to=enterprise&runtimes=claude_code",
    )
    for row in body["path"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at?tier={row['tier']}&runtimes=claude_code",
        )
        assert row["has_runtimes_at"] == sibling["allowed"], row["tier"]


# ── Endpoint: runtime alias canonicalisation upstream ──────────────────────


def test_endpoint_runtimes_alias_canonicalised(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path?from=oss&to=enterprise&runtimes=claude-code",
    )
    # Alias resolved upstream -> ``runtimes`` list carries canonical.
    assert body["runtimes"] == ["claude_code"]
    # No entry surfaces the raw alias in ``unknown``.
    assert "claude-code" not in body["unknown"]


def test_endpoint_runtimes_alias_and_canonical_dedup_to_one(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1


# ── Endpoint: rung sequence byte-parity ────────────────────────────────────


def test_endpoint_features_rung_sequence_matches_feature_catalog_path(client):
    ours = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    sibling = _get_json(
        client,
        "/api/entitlement/feature-catalog-path?from=oss&to=enterprise",
    )
    assert [r["tier"] for r in ours["path"]] == [
        r["tier"] for r in sibling["path"]
    ]


def test_endpoint_features_rung_sequence_matches_missing_features_at_path(client):
    ours = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    sibling = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    assert [r["tier"] for r in ours["path"]] == [
        r["tier"] for r in sibling["path"]
    ]


# ── Endpoint: rollup fields ────────────────────────────────────────────────


def test_endpoint_features_all_allowed_true_when_every_rung_grants(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=sessions",
    )
    # ``sessions`` is a FREE feature -> granted at every rung ->
    # every ``has_features_at`` is True.
    assert body["path_length"] >= 1
    assert body["all_allowed"] is True
    assert body["any_allowed"] is True
    assert body["allowed_count"] == body["path_length"]


def test_endpoint_features_all_allowed_false_when_only_top_grants(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=sso",
    )
    # ``sso`` is enterprise-only -> lower rungs deny it -> all_allowed is
    # False even though the last rung (enterprise) grants it.
    if body["path_length"] == 0:
        pytest.skip("no rungs to walk on this build")
    assert body["all_allowed"] is False


def test_endpoint_features_allowed_count_matches_row_folds(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    expected = sum(1 for r in body["path"] if r["has_features_at"])
    assert body["allowed_count"] == expected


def test_endpoint_features_any_allowed_off_row_folds(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    expected = any(r["has_features_at"] for r in body["path"])
    assert body["any_allowed"] is expected


def test_endpoint_features_all_allowed_false_on_empty_path(client):
    """Fail-closed rollup posture: empty ``path`` -> ``all_allowed`` is
    False (never vacuous-truth)."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=oss&features=fleet",
    )
    assert body["path_length"] == 0
    assert body["all_allowed"] is False
    assert body["any_allowed"] is False
    assert body["allowed_count"] == 0


def test_endpoint_features_required_tier_folds_off_known_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    # required_tier should point at the cheapest tier granting ``fleet``.
    assert body["required_tier"] is not None
    assert body["required_tier_rank"] >= 0


def test_endpoint_features_unknown_tokens_surface_in_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=pro&features=bogus_id",
    )
    assert body["unknown"] == ["bogus_id"]
    # Unknown-only bundle -> nothing to fold for required_tier.
    assert body["required_tier"] is None


def test_endpoint_features_unknown_token_collapses_every_rung_fold(client):
    """An unknown token in the bundle collapses the endpoint-level fold
    to ``False`` on EVERY rung (matches ``/has-features-at`` posture)."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet,bogus_id",
    )
    assert body["unknown"] == ["bogus_id"]
    for row in body["path"]:
        assert row["has_features_at"] is False


def test_endpoint_features_empty_bundle_every_rung_false(client):
    """Empty bundle (``?features=``) -- endpoint-level fold is False on
    every rung (fail-closed, matches ``/has-features-at`` posture)."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=",
    )
    for row in body["path"]:
        assert row["has_features_at"] is False
    assert body["all_allowed"] is False
    assert body["any_allowed"] is False


# ── Endpoint: complementarity with ``/missing-features-at-path`` ───────────


def test_endpoint_features_complements_missing_features_at_path(client):
    """Per-rung ``has_features_at`` is ``True`` iff the sibling
    ``/missing-features-at-path`` reports ``missing == []`` for the
    same (rung, bundle) pair (only when the caller-supplied bundle is
    KNOWN -- an unknown token collapses the has_ fold to False on every
    row regardless of missing_'s per-item shape)."""
    body_has = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    body_missing = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    by_tier = {r["tier"]: r for r in body_missing["path"]}
    for row in body_has["path"]:
        m = by_tier.get(row["tier"])
        assert m is not None, row["tier"]
        assert row["has_features_at"] is (not m["missing"]), row["tier"]


# ── Endpoint: never-5xx guard ──────────────────────────────────────────────


def test_endpoint_features_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "has_features_at_path", _boom)
    resp = client.get(
        "/api/entitlement/has-features-at-path?from=oss&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []


def test_endpoint_runtimes_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "has_runtimes_at_path", _boom)
    resp = client.get(
        "/api/entitlement/has-runtimes-at-path?from=oss&to=pro&runtimes=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["path"] == []


# ── Endpoint: resolver envelope fields ─────────────────────────────────────


def test_endpoint_features_resolver_envelope_present(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_endpoint_features_lateral_direction(client, ent):
    """Same-rank distinct-id endpoints -> single-row lateral path."""
    same_rank_pairs = [
        (a, b)
        for a in ent._TIER_ORDER
        for b in ent._TIER_ORDER
        if a != b
        and ent._TIER_RANK.get(a) == ent._TIER_RANK.get(b)
        and a in ent._TIER_FEATURES
        and b in ent._TIER_FEATURES
    ]
    if not same_rank_pairs:
        pytest.skip("no same-rank pair on this build")
    f, t = same_rank_pairs[0]
    body = _get_json(
        client,
        f"/api/entitlement/has-features-at-path?from={f}&to={t}&features=fleet",
    )
    assert body["direction"] == "lateral"
    assert body["path_length"] == 1
    assert body["path"][0]["tier"] == t
