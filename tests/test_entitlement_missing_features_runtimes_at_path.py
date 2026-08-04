"""Tests for the path-shaped ``missing_features_at_path`` /
``missing_runtimes_at_path`` complement scalars and their paired
``/api/entitlement/missing-features-at-path`` /
``/api/entitlement/missing-runtimes-at-path`` endpoints.

Path-shaped siblings of :func:`missing_features_at` /
:func:`missing_runtimes_at` and complement-shaped siblings of
:func:`feature_catalog_path` / :func:`runtime_catalog_path`: fixes ONE
bundle and sweeps across every rung between ``from`` and ``to``,
returning one row per rung with the per-item denial list at that rung.
Lets an upgrade-walkthrough tooltip render "at which tier does each of
these unlock?" off ONE URL.

This file pins:

1. Scalar walk semantics byte-parity with :func:`feature_catalog_path`
   (rung ``tier`` sequence, direction detection, endpoint semantics,
   same-rank sibling filter).
2. Per-rung ``missing`` byte-parity with the scalar
   :func:`missing_features_at` / :func:`missing_runtimes_at` for the
   same (rung, bundle) pair.
3. Bundle-fold posture inherited from the ``_at`` siblings:
   empty / None / non-iterable bundle -> every rung's ``missing`` is
   ``[]``; unknown / typo tokens surface in every rung's ``missing``
   (canonicalised).
4. Unknown-endpoint short-circuit: either endpoint unknown -> scalar
   returns ``None``; endpoint returns 200 with ``path=[]`` and
   ``direction="unknown"`` (never 4xxs -- matches
   ``/missing-features-at`` posture).
5. Direction semantics: ``upgrade`` / ``downgrade`` / ``lateral`` /
   ``identity`` / ``unknown``.
6. Grace-independence: same answer under grace on vs enforce for the
   same (from, to, bundle) triple.
7. Runtime scalar alias posture: no scalar-level canonicalisation --
   ``missing_runtimes_at_path(f, t, ["claude-code"])`` surfaces
   ``"claude-code"`` in every rung's ``missing`` verbatim; the paired
   endpoint canonicalises upstream (alias-and-canonical pair dedups to
   ONE entry in ``runtimes`` and therefore ONE entry in every rung's
   ``missing``).
8. Never-raises on delegate blowup: log-and-return ``None`` at scalar
   layer; empty-path fallback envelope at endpoint layer (never 5xxs).
9. Endpoint envelope shape (fixed key set) across every input branch,
   including the unknown-endpoint branch.
10. Cross-consistency with the sibling ``/feature-catalog-path`` walk:
    same rung ``tier`` sequence rung-for-rung.
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
    "any_missing",
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
    "any_missing",
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


# ── missing_features_at_path scalar ────────────────────────────────────────


def test_scalar_identity_endpoints_returns_empty_path(ent):
    """``from == to`` -> empty path (identity branch)."""
    for tier in ent._TIER_ORDER:
        assert ent.missing_features_at_path(tier, tier, ["fleet"]) == []


def test_scalar_unknown_endpoint_returns_none(ent):
    assert ent.missing_features_at_path("bogus", "pro", ["fleet"]) is None
    assert ent.missing_features_at_path("oss", "bogus", ["fleet"]) is None
    assert ent.missing_features_at_path("bogus_a", "bogus_b", ["fleet"]) is None
    assert ent.missing_features_at_path("", "pro", ["fleet"]) is None
    assert ent.missing_features_at_path(None, "pro", ["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_upgrade_path_has_rows(ent):
    path = ent.missing_features_at_path("oss", "enterprise", ["fleet", "sso"])
    assert isinstance(path, list) and len(path) >= 1
    # Row shape
    for row in path:
        assert set(row.keys()) == {"tier", "tier_label", "tier_rank", "missing"}
        assert isinstance(row["missing"], list)


def test_scalar_downgrade_path_has_rows(ent):
    path = ent.missing_features_at_path("enterprise", "oss", ["fleet", "sso"])
    assert isinstance(path, list) and len(path) >= 1


def test_scalar_lateral_path_single_row(ent):
    """Same-rank different-id endpoints -> single-row path carrying the
    ``missing`` at ``to``."""
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
        path = ent.missing_features_at_path(f, t, ["fleet"])
        assert isinstance(path, list) and len(path) == 1
        assert path[0]["tier"] == t


def test_scalar_per_rung_matches_missing_features_at(ent):
    """Per-rung ``missing`` byte-equals ``missing_features_at(rung, bundle)``
    for the same input -- the drift-blocker parity property."""
    bundle = ["fleet", "sso", "otel_export"]
    path = ent.missing_features_at_path("oss", "enterprise", bundle)
    assert path is not None
    for row in path:
        assert row["missing"] == ent.missing_features_at(row["tier"], bundle)


def test_scalar_rungs_match_feature_catalog_path(ent):
    """Rung sequence byte-parity with :func:`feature_catalog_path` --
    both walk the same ``_PURCHASABLE_TIERS`` filter + sort key."""
    bundle = ["fleet"]
    ours = ent.missing_features_at_path("oss", "enterprise", bundle)
    catalog = ent.feature_catalog_path("oss", "enterprise")
    assert ours is not None and catalog is not None
    assert [r["tier"] for r in ours] == [r["tier"] for r in catalog]


def test_scalar_empty_bundle_every_rung_empty(ent):
    path = ent.missing_features_at_path("oss", "enterprise", [])
    assert path is not None
    for row in path:
        assert row["missing"] == []


def test_scalar_none_bundle_every_rung_empty(ent):
    path = ent.missing_features_at_path("oss", "enterprise", None)
    assert path is not None
    for row in path:
        assert row["missing"] == []


def test_scalar_non_iterable_bundle_every_rung_empty(ent):
    path = ent.missing_features_at_path("oss", "enterprise", 123)
    assert path is not None
    for row in path:
        assert row["missing"] == []


def test_scalar_unknown_token_surfaces_every_rung(ent):
    path = ent.missing_features_at_path("oss", "enterprise", ["bogus_id"])
    assert path is not None
    for row in path:
        assert row["missing"] == ["bogus_id"]


def test_scalar_grace_independence(ent, enforced):
    bundle = ["fleet", "sso"]
    a = ent.missing_features_at_path("oss", "enterprise", bundle)
    b = enforced.missing_features_at_path("oss", "enterprise", bundle)
    assert a == b


def test_scalar_upgrade_missing_set_monotone_shrink(ent):
    """As you climb rungs, ``missing`` shrinks or stays equal (each rung
    grants a superset of prior rungs' grants)."""
    bundle = sorted(ent.PAID_FEATURES)
    path = ent.missing_features_at_path("oss", "enterprise", bundle)
    assert path is not None
    prev_set: set = set(bundle) | set()
    for row in path:
        cur = set(row["missing"])
        assert cur.issubset(prev_set), (row["tier"], cur, prev_set)
        prev_set = cur


def test_scalar_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_features_at", _boom)
    assert ent.missing_features_at_path("oss", "pro", ["fleet"]) is None


# ── missing_runtimes_at_path scalar ────────────────────────────────────────


def test_scalar_runtimes_identity_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at_path(tier, tier, ["claude_code"]) == []


def test_scalar_runtimes_unknown_endpoint(ent):
    assert ent.missing_runtimes_at_path("bogus", "pro", ["claude_code"]) is None
    assert ent.missing_runtimes_at_path("oss", "bogus", ["claude_code"]) is None


def test_scalar_runtimes_upgrade_path_rows(ent):
    path = ent.missing_runtimes_at_path("oss", "enterprise", ["claude_code"])
    assert isinstance(path, list) and len(path) >= 1
    for row in path:
        assert set(row.keys()) == {"tier", "tier_label", "tier_rank", "missing"}


def test_scalar_runtimes_per_rung_matches_missing_runtimes_at(ent):
    bundle = ["claude_code", "openclaw"]
    path = ent.missing_runtimes_at_path("oss", "enterprise", bundle)
    assert path is not None
    for row in path:
        assert row["missing"] == ent.missing_runtimes_at(row["tier"], bundle)


def test_scalar_runtimes_strict_alias_posture(ent):
    """Scalar layer does NOT resolve aliases -- ``claude-code`` surfaces
    in every rung's ``missing`` verbatim (matches ``missing_runtimes_at``
    docstring; endpoint canonicalises upstream)."""
    path = ent.missing_runtimes_at_path("oss", "enterprise", ["claude-code"])
    assert path is not None
    for row in path:
        assert "claude-code" in row["missing"]


def test_scalar_runtimes_grace_independence(ent, enforced):
    bundle = ["claude_code", "cursor"]
    a = ent.missing_runtimes_at_path("oss", "enterprise", bundle)
    b = enforced.missing_runtimes_at_path("oss", "enterprise", bundle)
    assert a == b


def test_scalar_runtimes_never_raises(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_runtimes_at", _boom)
    assert ent.missing_runtimes_at_path("oss", "pro", ["claude_code"]) is None


# ── Endpoint: envelope shape ───────────────────────────────────────────────


def test_endpoint_features_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"


def test_endpoint_runtimes_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"


def test_endpoint_features_missing_from_still_200(client):
    """Never 4xxs on missing ``from=``."""
    resp = client.get("/api/entitlement/missing-features-at-path?to=pro&features=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_missing_to_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path?from=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_unknown_tier_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path?from=bogus&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []
    assert body["direction"] == "unknown"


def test_endpoint_features_identity_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path?from=oss&to=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_endpoint_features_upgrade_direction(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    if body["from_rank"] == body["to_rank"]:
        pytest.skip("no rank difference on this build")
    assert body["direction"] == "upgrade"
    assert body["path_length"] == len(body["path"])
    assert body["path_length"] >= 1


def test_endpoint_features_downgrade_direction(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=enterprise&to=oss&features=fleet",
    )
    if body["from_rank"] == body["to_rank"]:
        pytest.skip("no rank difference on this build")
    assert body["direction"] == "downgrade"


# ── Endpoint: per-rung parity with sibling ``/missing-features-at`` ────────


def test_endpoint_features_per_rung_matches_missing_features_at(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet,sso",
    )
    for row in body["path"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/missing-features-at?tier={row['tier']}&features=fleet,sso",
        )
        assert row["missing"] == sibling["missing"], row["tier"]


def test_endpoint_runtimes_per_rung_matches_missing_runtimes_at(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path?from=oss&to=enterprise&runtimes=claude_code",
    )
    for row in body["path"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/missing-runtimes-at?tier={row['tier']}&runtimes=claude_code",
        )
        assert row["missing"] == sibling["missing"], row["tier"]


# ── Endpoint: runtime alias canonicalisation upstream ──────────────────────


def test_endpoint_runtimes_alias_canonicalised(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path?from=oss&to=enterprise&runtimes=claude-code",
    )
    # Alias resolved upstream -> ``runtimes`` list carries canonical.
    assert body["runtimes"] == ["claude_code"]
    # Every rung's ``missing`` is off the canonical, not the alias.
    for row in body["path"]:
        assert "claude-code" not in row["missing"]


def test_endpoint_runtimes_alias_and_canonical_dedup_to_one(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1
    # Dedup propagates into every rung's ``missing`` list.
    for row in body["path"]:
        assert row["missing"].count("claude_code") <= 1


# ── Endpoint: rung sequence byte-parity with ``/feature-catalog-path`` ─────


def test_endpoint_features_rung_sequence_matches_feature_catalog_path(client):
    ours = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    sibling = _get_json(
        client,
        "/api/entitlement/feature-catalog-path?from=oss&to=enterprise",
    )
    assert [r["tier"] for r in ours["path"]] == [r["tier"] for r in sibling["path"]]


# ── Endpoint: rollup fields ────────────────────────────────────────────────


def test_endpoint_features_any_missing_true_when_row_missing_nonempty(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=cloud_starter&features=sso",
    )
    # SSO is enterprise-only, so cloud_starter rung's ``missing`` is
    # non-empty -> rollup True.
    assert body["any_missing"] is True


def test_endpoint_features_any_missing_false_on_all_granted(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=sessions",
    )
    # ``sessions`` is a FREE feature -> granted at every rung -> no rung
    # has anything missing.
    assert body["any_missing"] is False


def test_endpoint_features_required_tier_folds_off_known_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    # required_tier should point at the cheapest tier granting ``fleet``.
    assert body["required_tier"] is not None
    assert body["required_tier_rank"] >= 0


def test_endpoint_features_unknown_tokens_surface_in_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path?from=oss&to=pro&features=bogus_id",
    )
    assert body["unknown"] == ["bogus_id"]
    # Unknown-only bundle -> nothing to fold for required_tier.
    assert body["required_tier"] is None


# ── Endpoint: never-5xx guard ──────────────────────────────────────────────


def test_endpoint_features_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "missing_features_at_path", _boom)
    resp = client.get(
        "/api/entitlement/missing-features-at-path?from=oss&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["path"] == []


def test_endpoint_runtimes_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "missing_runtimes_at_path", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes-at-path?from=oss&to=pro&runtimes=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["path"] == []
