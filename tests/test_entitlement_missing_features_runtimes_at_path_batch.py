"""Tests for the batch-path ``missing_features_at_path_batch`` /
``missing_runtimes_at_path_batch`` complement scalars and their paired
``/api/entitlement/missing-features-at-path-batch`` /
``/api/entitlement/missing-runtimes-at-path-batch`` endpoints.

Batch-path siblings of :func:`missing_features_at_path` /
:func:`missing_runtimes_at_path`: fix ONE bundle and walk the rungs
between ONE ``from`` and N candidate destinations in ONE round-trip.
Lets an upgrade-comparison surface render "for the bundle {fleet,
sso}, at which rung does each of these unlock on the way to each of
{starter, pro, enterprise}?" off ONE URL.

This file pins:

1. Scalar shape ({"tiers": [...], "unknown": [...]}) and byte-parity
   with :func:`tier_unlocks_path_batch` / :func:`tier_locks_path_batch`
   for the per-destination envelope (``to`` / ``to_label`` / ``to_rank``
   / ``direction`` / ``path``).
2. Per-destination ``path`` byte-parity with the scalar
   :func:`missing_features_at_path` / :func:`missing_runtimes_at_path`
   for the same ``(from, to, bundle)`` triple.
3. Unknown-``from`` short-circuit: scalar returns ``None``; endpoint
   returns 200 with ``tiers=[]`` (never 4xxs -- matches
   ``/missing-features-at-batch`` posture).
4. Unknown destinations echo into ``unknown[]`` (scalar) /
   ``unknown_tiers[]`` (endpoint) without short-circuiting the batch.
5. Direction detection per destination:
   ``upgrade`` / ``downgrade`` / ``lateral`` / ``identity``.
6. Grace-independence: same answer under grace on vs enforce for the
   same ``(from, to_list, bundle)`` triple.
7. Runtime scalar alias posture: no scalar-level canonicalisation --
   ``missing_runtimes_at_path_batch(f, [t], ["claude-code"])`` surfaces
   ``"claude-code"`` in every rung's ``missing`` verbatim; the paired
   endpoint canonicalises upstream (alias-and-canonical pair dedups to
   ONE entry in ``runtimes`` and therefore ONE entry in every rung's
   ``missing``).
8. Never-raises on delegate blowup: log-and-drop the destination into
   ``unknown[]`` at scalar layer; empty-tiers fallback envelope at
   endpoint layer (never 5xxs).
9. Endpoint envelope shape (fixed key set) across every input branch,
   including the unknown-``from`` branch and the empty-``to`` branch.
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
_TIER_ROW_KEYS = {"to", "to_label", "to_rank", "direction", "path", "path_length", "any_missing"}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── missing_features_at_path_batch scalar ──────────────────────────────────


def test_scalar_features_returns_dict_shape(ent):
    out = ent.missing_features_at_path_batch("oss", ["pro", "enterprise"], ["fleet"])
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_scalar_features_unknown_from_returns_none(ent):
    assert ent.missing_features_at_path_batch("bogus", ["pro"], ["fleet"]) is None
    assert ent.missing_features_at_path_batch("", ["pro"], ["fleet"]) is None
    assert ent.missing_features_at_path_batch(None, ["pro"], ["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_features_empty_destinations_returns_empty_tiers(ent):
    out = ent.missing_features_at_path_batch("oss", [], ["fleet"])
    assert out == {"tiers": [], "unknown": []}


def test_scalar_features_unknown_destination_echoes_to_unknown(ent):
    out = ent.missing_features_at_path_batch("oss", ["bogus_id"], ["fleet"])
    assert out is not None
    assert out["tiers"] == []
    assert out["unknown"] == ["bogus_id"]


def test_scalar_features_mixed_valid_and_unknown_partial_ok(ent):
    out = ent.missing_features_at_path_batch(
        "oss", ["enterprise", "bogus_id"], ["fleet"]
    )
    assert out is not None
    assert [row["to"] for row in out["tiers"]] == ["enterprise"]
    assert out["unknown"] == ["bogus_id"]


def test_scalar_features_dedup_and_normalise_destinations(ent):
    out = ent.missing_features_at_path_batch(
        "oss", " ENTERPRISE , enterprise , enterprise ", ["fleet"]
    )
    assert out is not None
    assert [row["to"] for row in out["tiers"]] == ["enterprise"]


def test_scalar_features_per_destination_row_shape(ent):
    out = ent.missing_features_at_path_batch(
        "oss", ["pro", "enterprise"], ["fleet", "sso"]
    )
    assert out is not None
    for row in out["tiers"]:
        assert set(row.keys()) == {"to", "to_label", "to_rank", "direction", "path"}
        assert isinstance(row["path"], list)


def test_scalar_features_per_destination_path_matches_scalar(ent):
    """Per-destination ``path`` byte-equals scalar
    :func:`missing_features_at_path` for the same triple -- the
    drift-blocker parity property."""
    bundle = ["fleet", "sso", "otel_export"]
    out = ent.missing_features_at_path_batch(
        "oss", ["cloud_starter", "cloud_pro", "enterprise"], bundle
    )
    assert out is not None
    for row in out["tiers"]:
        expected = ent.missing_features_at_path("oss", row["to"], bundle)
        assert row["path"] == expected, row["to"]


def test_scalar_features_identity_row_has_empty_path(ent):
    out = ent.missing_features_at_path_batch("oss", ["oss"], ["fleet"])
    assert out is not None
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_scalar_features_direction_detection(ent):
    out = ent.missing_features_at_path_batch(
        "cloud_starter", ["oss", "cloud_starter", "enterprise"], ["fleet"]
    )
    assert out is not None
    by_to = {row["to"]: row for row in out["tiers"]}
    assert by_to["oss"]["direction"] == "downgrade"
    assert by_to["cloud_starter"]["direction"] == "identity"
    assert by_to["enterprise"]["direction"] == "upgrade"


def test_scalar_features_empty_bundle_every_rung_empty(ent):
    out = ent.missing_features_at_path_batch("oss", ["enterprise"], [])
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["missing"] == []


def test_scalar_features_none_bundle_every_rung_empty(ent):
    out = ent.missing_features_at_path_batch("oss", ["enterprise"], None)
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["missing"] == []


def test_scalar_features_non_iterable_bundle_every_rung_empty(ent):
    out = ent.missing_features_at_path_batch("oss", ["enterprise"], 123)
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert r["missing"] == []


def test_scalar_features_grace_independence(ent, enforced):
    bundle = ["fleet", "sso"]
    a = ent.missing_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    b = enforced.missing_features_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert a == b


def test_scalar_features_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_features_at_path", _boom)
    out = ent.missing_features_at_path_batch("oss", ["pro"], ["fleet"])
    assert out is not None
    assert out["tiers"] == []
    assert "pro" in out["unknown"]


# ── missing_runtimes_at_path_batch scalar ──────────────────────────────────


def test_scalar_runtimes_returns_dict_shape(ent):
    out = ent.missing_runtimes_at_path_batch(
        "oss", ["pro", "enterprise"], ["claude_code"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}


def test_scalar_runtimes_unknown_from_returns_none(ent):
    assert ent.missing_runtimes_at_path_batch("bogus", ["pro"], ["claude_code"]) is None


def test_scalar_runtimes_per_destination_path_matches_scalar(ent):
    bundle = ["claude_code", "openclaw"]
    out = ent.missing_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert out is not None
    for row in out["tiers"]:
        expected = ent.missing_runtimes_at_path("oss", row["to"], bundle)
        assert row["path"] == expected, row["to"]


def test_scalar_runtimes_strict_alias_posture(ent):
    """Scalar layer does NOT resolve aliases -- ``claude-code`` surfaces
    in every rung's ``missing`` verbatim (matches
    ``missing_runtimes_at_path`` docstring; endpoint canonicalises
    upstream)."""
    out = ent.missing_runtimes_at_path_batch("oss", ["enterprise"], ["claude-code"])
    assert out is not None
    for row in out["tiers"]:
        for r in row["path"]:
            assert "claude-code" in r["missing"]


def test_scalar_runtimes_grace_independence(ent, enforced):
    bundle = ["claude_code", "cursor"]
    a = ent.missing_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    b = enforced.missing_runtimes_at_path_batch(
        "oss", ["cloud_starter", "enterprise"], bundle
    )
    assert a == b


def test_scalar_runtimes_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_runtimes_at_path", _boom)
    out = ent.missing_runtimes_at_path_batch("oss", ["pro"], ["claude_code"])
    assert out is not None
    assert out["tiers"] == []
    assert "pro" in out["unknown"]


# ── Endpoint: envelope shape ───────────────────────────────────────────────


def test_endpoint_features_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=cloud_starter,enterprise&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert body["from"] == "oss"
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_ROW_KEYS
        assert isinstance(row["path"], list)
        assert row["path_length"] == len(row["path"])


def test_endpoint_runtimes_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_ROW_KEYS


# ── Endpoint: never-4xx posture ────────────────────────────────────────────


def test_endpoint_features_missing_from_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path-batch?to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []


def test_endpoint_features_unknown_from_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path-batch?from=bogus&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []
    # ``unknown_tiers`` echoes the caller's ``to=`` set so the tooltip
    # can still show what was dropped.
    assert body["unknown_tiers"] == ["pro"]


def test_endpoint_features_empty_to_still_200(client):
    resp = client.get(
        "/api/entitlement/missing-features-at-path-batch?from=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["from"] == "oss"


def test_endpoint_features_unknown_destinations_bucketed(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=bogus_a,enterprise,bogus_b&features=fleet",
    )
    assert [row["to"] for row in body["tiers"]] == ["enterprise"]
    assert set(body["unknown_tiers"]) == {"bogus_a", "bogus_b"}


# ── Endpoint: per-destination parity with singular ``/missing-*-at-path`` ──


def test_endpoint_features_per_destination_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=cloud_starter,cloud_pro,enterprise&features=fleet,sso",
    )
    for row in body["tiers"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/missing-features-at-path?from=oss&to={row['to']}&features=fleet,sso",
        )
        assert row["path"] == sibling["path"], row["to"]
        assert row["direction"] == sibling["direction"], row["to"]


def test_endpoint_runtimes_per_destination_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path-batch?from=oss&to=cloud_starter,enterprise&runtimes=claude_code",
    )
    for row in body["tiers"]:
        sibling = _get_json(
            client,
            f"/api/entitlement/missing-runtimes-at-path?from=oss&to={row['to']}&runtimes=claude_code",
        )
        assert row["path"] == sibling["path"], row["to"]


# ── Endpoint: direction detection ──────────────────────────────────────────


def test_endpoint_features_direction_detection(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=cloud_starter&to=oss,cloud_starter,enterprise&features=fleet",
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
        "/api/entitlement/missing-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude-code",
    )
    # Alias resolved upstream -> ``runtimes`` list carries canonical.
    assert body["runtimes"] == ["claude_code"]
    # Every per-destination rung's ``missing`` is off the canonical, not
    # the alias.
    for row in body["tiers"]:
        for r in row["path"]:
            assert "claude-code" not in r["missing"]


def test_endpoint_runtimes_alias_and_canonical_dedup_to_one(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-path-batch?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1
    for row in body["tiers"]:
        for r in row["path"]:
            assert r["missing"].count("claude_code") <= 1


# ── Endpoint: rollup fields ────────────────────────────────────────────────


def test_endpoint_features_any_missing_true_when_row_missing_nonempty(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=cloud_starter&features=sso",
    )
    # SSO is enterprise-only, so cloud_starter path's rung has a
    # non-empty ``missing`` -> per-destination rollup True.
    assert body["tiers"][0]["any_missing"] is True


def test_endpoint_features_any_missing_false_on_all_granted(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=enterprise&features=sessions",
    )
    # ``sessions`` is a FREE feature -> granted at every rung -> no
    # per-destination rollup carries missing.
    for row in body["tiers"]:
        assert row["any_missing"] is False


def test_endpoint_features_required_tier_folds_off_known_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=enterprise&features=fleet",
    )
    # required_tier should point at the cheapest tier granting ``fleet``.
    assert body["required_tier"] is not None
    assert body["required_tier_rank"] >= 0


def test_endpoint_features_unknown_tokens_surface_in_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=pro&features=bogus_id",
    )
    assert body["unknown"] == ["bogus_id"]
    # Unknown-only bundle -> nothing to fold for required_tier.
    assert body["required_tier"] is None


# ── Endpoint: never-5xx guard ──────────────────────────────────────────────


def test_endpoint_features_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "missing_features_at_path_batch", _boom)
    resp = client.get(
        "/api/entitlement/missing-features-at-path-batch?from=oss&to=pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tiers"] == []


def test_endpoint_runtimes_never_5xx_on_helper_blowup(client, monkeypatch):
    import clawmetry.entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "missing_runtimes_at_path_batch", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes-at-path-batch?from=oss&to=pro&runtimes=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["tiers"] == []
