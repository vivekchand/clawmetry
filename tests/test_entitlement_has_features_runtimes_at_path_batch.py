"""Tests for the batch-path ``has_features_at_path_batch`` /
``has_runtimes_at_path_batch`` boolean-fold scalars and their paired
``/api/entitlement/has-features-at-path-batch`` /
``/api/entitlement/has-runtimes-at-path-batch`` endpoints.

Batch-path siblings of :func:`has_features_at_path` /
:func:`has_runtimes_at_path`: fix ONE bundle and walk the rungs
between ONE ``from`` and N candidate destinations in ONE round-trip.
Lets an upgrade-comparison surface render "for the bundle {fleet,
sso}, at which rung does this WHOLE bundle unlock along each of the
paths to {cloud_starter, cloud_pro, enterprise}?" off ONE URL.

This file pins:

1. Scalar shape ``{"tiers": [...], "unknown": [...]}`` and per-
   destination envelope (``to`` / ``to_label`` / ``to_rank`` /
   ``direction`` / ``path``) parity with
   :func:`missing_features_at_path_batch`.
2. Per-destination ``path`` byte-parity with the scalar
   :func:`has_features_at_path` / :func:`has_runtimes_at_path` for
   the same ``(from, to, bundle)`` triple.
3. Unknown-``from`` short-circuit: scalar returns ``None``; endpoint
   returns 200 with ``tiers=[]`` (never 4xxs -- matches
   ``/has-features-at-batch`` posture).
4. Unknown destinations echo into ``unknown[]`` (scalar) /
   ``unknown_tiers[]`` (endpoint) without short-circuiting the batch.
5. Direction detection per destination:
   ``upgrade`` / ``downgrade`` / ``lateral`` / ``identity``.
6. Grace-independence: same answer under grace on vs enforce for the
   same ``(from, to_list, bundle)`` triple.
7. Runtime scalar alias posture: no scalar-level canonicalisation --
   ``has_runtimes_at_path_batch(f, [t], ["claude-code"])`` collapses
   every rung's ``has_runtimes_at`` to ``False``; the paired endpoint
   canonicalises upstream (alias-and-canonical pair dedups to ONE
   entry in ``runtimes`` and therefore ONE fold input per rung).
8. Endpoint-level fold semantics: an unknown token in the bundle
   collapses per-rung ``has_<axis>_at`` to ``False`` on EVERY rung
   of EVERY destination (fail-closed at the endpoint layer).
9. Per-destination rollups ``allowed_count`` / ``all_allowed`` /
   ``any_allowed``.
10. Never-raises on delegate blowup: log-and-drop the destination into
    ``unknown[]`` at scalar layer; empty-tiers fallback envelope at
    endpoint layer (never 5xxs).
11. Endpoint envelope shape (fixed key set) across every input
    branch, including the unknown-``from`` branch and the empty-``to``
    branch.
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
    "features",
    "unknown",
    "unknown_tiers",
    "kind",
    "count",
    "tiers",
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
    "runtimes",
    "unknown",
    "unknown_tiers",
    "kind",
    "count",
    "tiers",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_TIER_ROW_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_features_at_path_batch scalar ──────────────────────────────────────


def test_scalar_features_returns_dict_shape(ent):
    out = ent.has_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], ["fleet"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_scalar_features_unknown_from_returns_none(ent):
    assert ent.has_features_at_path_batch("bogus", ["cloud_pro"], ["fleet"]) is None
    assert ent.has_features_at_path_batch("", ["cloud_pro"], ["fleet"]) is None
    assert ent.has_features_at_path_batch(None, ["cloud_pro"], ["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_features_empty_destinations_returns_empty_tiers(ent):
    out = ent.has_features_at_path_batch("oss", [], ["fleet"])
    assert out == {"tiers": [], "unknown": []}


def test_scalar_features_unknown_destination_echoes_to_unknown(ent):
    out = ent.has_features_at_path_batch("oss", ["bogus_id"], ["fleet"])
    assert out is not None
    assert out["tiers"] == []
    assert out["unknown"] == ["bogus_id"]


def test_scalar_features_mixed_valid_and_unknown_partial_ok(ent):
    out = ent.has_features_at_path_batch(
        "oss", ["enterprise", "bogus_id"], ["fleet"]
    )
    assert out is not None
    assert [row["to"] for row in out["tiers"]] == ["enterprise"]
    assert out["unknown"] == ["bogus_id"]


def test_scalar_features_dedup_and_normalise_destinations(ent):
    out = ent.has_features_at_path_batch(
        "oss", " ENTERPRISE , enterprise , enterprise ", ["fleet"]
    )
    assert out is not None
    assert [row["to"] for row in out["tiers"]] == ["enterprise"]


def test_scalar_features_per_destination_row_shape(ent):
    out = ent.has_features_at_path_batch(
        "oss", ["cloud_pro", "enterprise"], ["fleet", "sso"]
    )
    assert out is not None
    for row in out["tiers"]:
        assert set(row.keys()) == {
            "to",
            "to_label",
            "to_rank",
            "direction",
            "path",
        }
        assert isinstance(row["path"], list)


def test_scalar_features_per_destination_path_matches_scalar(ent):
    """Per-destination ``path`` byte-equals scalar
    :func:`has_features_at_path` for the same triple -- the drift-blocker
    parity property."""
    bundle = ["fleet", "sso", "otel_export"]
    out = ent.has_features_at_path_batch(
        "oss", ["cloud_starter", "cloud_pro", "enterprise"], bundle
    )
    assert out is not None
    for row in out["tiers"]:
        expected = ent.has_features_at_path("oss", row["to"], bundle)
        assert row["path"] == expected, row["to"]


def test_scalar_features_rungs_match_missing_batch_sibling(ent):
    """Per-destination rung sequence byte-parity with the complement
    helper :func:`missing_features_at_path_batch` -- both walk the same
    ``_PURCHASABLE_TIERS`` filter + sort key so paired UI columns line
    up rung-for-rung per destination."""
    bundle = ["fleet"]
    ours = ent.has_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    comp = ent.missing_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert ours is not None and comp is not None
    ours_by_to = {row["to"]: row for row in ours["tiers"]}
    comp_by_to = {row["to"]: row for row in comp["tiers"]}
    assert set(ours_by_to) == set(comp_by_to)
    for tid, row in ours_by_to.items():
        assert [r["tier"] for r in row["path"]] == [
            r["tier"] for r in comp_by_to[tid]["path"]
        ]


def test_scalar_features_identity_row_has_empty_path(ent):
    out = ent.has_features_at_path_batch("oss", ["oss"], ["fleet"])
    assert out is not None
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_scalar_features_direction_detection(ent):
    out = ent.has_features_at_path_batch(
        "cloud_starter",
        ["oss", "cloud_starter", "enterprise"],
        ["fleet"],
    )
    assert out is not None
    by_to = {row["to"]: row for row in out["tiers"]}
    assert by_to["oss"]["direction"] == "downgrade"
    assert by_to["cloud_starter"]["direction"] == "identity"
    assert by_to["enterprise"]["direction"] == "upgrade"


def test_scalar_features_empty_bundle_every_rung_false(ent):
    out = ent.has_features_at_path_batch("oss", ["enterprise"], [])
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["has_features_at"] is False


def test_scalar_features_none_bundle_every_rung_false(ent):
    out = ent.has_features_at_path_batch("oss", ["enterprise"], None)
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["has_features_at"] is False


def test_scalar_features_non_iterable_bundle_every_rung_false(ent):
    out = ent.has_features_at_path_batch("oss", ["enterprise"], 123)
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["has_features_at"] is False


def test_scalar_features_unknown_token_every_rung_false(ent):
    """Typo posture inherited from the singular scalar: an unknown feature
    id collapses every rung's ``has_features_at`` to ``False``."""
    out = ent.has_features_at_path_batch(
        "oss", ["enterprise"], ["fleet", "bogus_feature"]
    )
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["has_features_at"] is False


def test_scalar_features_grace_independence(ent, enforced):
    bundle = ["fleet", "sso"]
    a = ent.has_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    b = enforced.has_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert a == b


def test_scalar_features_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_features_at_path", _boom)
    out = ent.has_features_at_path_batch("oss", ["cloud_pro"], ["fleet"])
    assert out is not None
    assert out["tiers"] == []
    assert "cloud_pro" in out["unknown"]


# ── has_runtimes_at_path_batch scalar ──────────────────────────────────────


def test_scalar_runtimes_returns_dict_shape(ent):
    out = ent.has_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], ["claude_code"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}


def test_scalar_runtimes_unknown_from_returns_none(ent):
    assert (
        ent.has_runtimes_at_path_batch("bogus", ["cloud_pro"], ["claude_code"])
        is None
    )


def test_scalar_runtimes_per_destination_path_matches_scalar(ent):
    bundle = ["claude_code", "openclaw"]
    out = ent.has_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert out is not None
    for row in out["tiers"]:
        expected = ent.has_runtimes_at_path("oss", row["to"], bundle)
        assert row["path"] == expected, row["to"]


def test_scalar_runtimes_strict_alias_posture(ent):
    """Scalar layer does NOT resolve aliases -- ``claude-code`` collapses
    every rung's ``has_runtimes_at`` to ``False`` because it is not in
    :data:`ALL_RUNTIMES` after ``.strip().lower()`` (matches the singular
    scalar; endpoint canonicalises upstream)."""
    out = ent.has_runtimes_at_path_batch(
        "oss", ["enterprise"], ["claude-code"]
    )
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["has_runtimes_at"] is False


def test_scalar_runtimes_grace_independence(ent, enforced):
    bundle = ["claude_code", "cursor"]
    a = ent.has_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    b = enforced.has_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert a == b


def test_scalar_runtimes_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_runtimes_at_path", _boom)
    out = ent.has_runtimes_at_path_batch(
        "oss", ["cloud_pro"], ["claude_code"]
    )
    assert out is not None
    assert out["tiers"] == []
    assert "cloud_pro" in out["unknown"]


# ── Endpoint: envelope shape ───────────────────────────────────────────────


def test_endpoint_features_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_starter,enterprise&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert body["from"] == "oss"
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_ROW_KEYS
        assert isinstance(row["path"], list)
        assert row["path_length"] == len(row["path"])
        for r in row["path"]:
            assert set(r.keys()) == {
                "tier",
                "tier_label",
                "tier_rank",
                "has_features_at",
            }
            assert isinstance(r["has_features_at"], bool)


def test_endpoint_runtimes_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_ROW_KEYS
        for r in row["path"]:
            assert set(r.keys()) == {
                "tier",
                "tier_label",
                "tier_rank",
                "has_runtimes_at",
            }


# ── Endpoint: never-4xx posture ────────────────────────────────────────────


def test_endpoint_features_missing_from_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path-batch?to=cloud_pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []


def test_endpoint_features_unknown_from_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path-batch?from=bogus&to=cloud_pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []
    # ``unknown_tiers`` echoes the caller's ``to=`` set so the tooltip
    # can still show what was dropped.
    assert body["unknown_tiers"] == ["cloud_pro"]


def test_endpoint_features_empty_to_still_200(client):
    resp = client.get(
        "/api/entitlement/has-features-at-path-batch?from=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["from"] == "oss"


def test_endpoint_features_unknown_destinations_bucketed(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=bogus_a,enterprise,bogus_b&features=fleet",
    )
    assert [row["to"] for row in body["tiers"]] == ["enterprise"]
    assert set(body["unknown_tiers"]) == {"bogus_a", "bogus_b"}


# ── Endpoint: per-destination parity with singular ``/has-*-at-path`` ──────


def test_endpoint_features_per_destination_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_starter,cloud_pro,enterprise&features=fleet,sso",
    )
    for row in body["tiers"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/has-features-at-path?from=oss&to={row['to']}&features=fleet,sso",
        )
        assert row["path"] == sibling["path"], row["to"]
        assert row["direction"] == sibling["direction"], row["to"]


def test_endpoint_runtimes_per_destination_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path-batch?from=oss&to=cloud_starter,enterprise&runtimes=claude_code",
    )
    for row in body["tiers"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/has-runtimes-at-path?from=oss&to={row['to']}&runtimes=claude_code",
        )
        assert row["path"] == sibling["path"], row["to"]


# ── Endpoint: direction detection ──────────────────────────────────────────


def test_endpoint_features_direction_detection(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=cloud_starter&to=oss,cloud_starter,enterprise&features=fleet",
    )
    by_to = {row["to"]: row for row in body["tiers"]}
    assert by_to["oss"]["direction"] == "downgrade"
    assert by_to["cloud_starter"]["direction"] == "identity"
    assert by_to["cloud_starter"]["path"] == []
    assert by_to["enterprise"]["direction"] == "upgrade"


# ── Endpoint: runtime alias canonicalisation upstream ──────────────────────


def test_endpoint_runtimes_alias_canonicalised(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude-code",
    )
    # Alias resolved upstream -> ``runtimes`` list carries canonical.
    assert body["runtimes"] == ["claude_code"]


def test_endpoint_runtimes_alias_and_canonical_dedup_to_one(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1


# ── Endpoint: fold rollups ─────────────────────────────────────────────────


def test_endpoint_features_all_allowed_false_when_row_denied(client):
    """SSO is enterprise-only, so cloud_starter path's rung has
    ``has_features_at=False`` -> per-destination rollups reflect the
    denial."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_starter&features=sso",
    )
    row = body["tiers"][0]
    assert row["all_allowed"] is False
    assert row["allowed_count"] == 0
    assert row["any_allowed"] is False


def test_endpoint_features_all_allowed_true_when_free_feature(client):
    """``sessions`` is a FREE feature -> granted at every rung ->
    per-destination rollups all True."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=enterprise&features=sessions",
    )
    for row in body["tiers"]:
        # Path can be non-empty; if empty (identity/lateral edge) rollups
        # follow fail-closed AND-fold posture. Non-empty path here.
        if row["path"]:
            assert row["all_allowed"] is True
            assert row["allowed_count"] == row["path_length"]
            assert row["any_allowed"] is True


def test_endpoint_features_allowed_count_sums_row_grants(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=enterprise&features=fleet",
    )
    for row in body["tiers"]:
        expected = sum(1 for r in row["path"] if r["has_features_at"])
        assert row["allowed_count"] == expected


def test_endpoint_features_required_tier_folds_off_known_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=enterprise&features=fleet",
    )
    # ``required_tier`` should point at the cheapest tier granting ``fleet``.
    assert body["required_tier"] is not None
    assert body["required_tier_rank"] >= 0


def test_endpoint_features_unknown_token_fold_false_everywhere(client):
    """An unknown token in the bundle collapses the endpoint-level fold
    to ``False`` on EVERY rung of EVERY destination (matches the
    singular ``/has-features-at-path`` fail-closed posture)."""
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_starter,enterprise&features=fleet,bogus_feature",
    )
    assert body["unknown"] == ["bogus_feature"]
    for row in body["tiers"]:
        for r in row["path"]:
            assert r["has_features_at"] is False
        assert row["all_allowed"] is False
        assert row["allowed_count"] == 0
        assert row["any_allowed"] is False


def test_endpoint_features_unknown_tokens_surface_in_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_pro&features=bogus_id",
    )
    assert body["unknown"] == ["bogus_id"]
    # Unknown-only bundle -> nothing to fold for required_tier.
    assert body["required_tier"] is None


def test_endpoint_features_identity_row_zeroed_rollups(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-at-path-batch?from=oss&to=oss&features=fleet",
    )
    row = body["tiers"][0]
    assert row["direction"] == "identity"
    assert row["path"] == []
    # Empty path -> AND-fold False, OR-fold False, count zero (matches
    # the singular ``_has_bundle_at_path_body`` posture).
    assert row["all_allowed"] is False
    assert row["any_allowed"] is False
    assert row["allowed_count"] == 0


# ── Endpoint: never-5xx guard ──────────────────────────────────────────────


def test_endpoint_features_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "has_features_at_path_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-features-at-path-batch?from=oss&to=cloud_pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []


def test_endpoint_runtimes_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "has_runtimes_at_path_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-runtimes-at-path-batch?from=oss&to=cloud_pro&runtimes=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["tiers"] == []
