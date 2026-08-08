"""Tests for the source-axis batch-path
``has_features_from_path_batch`` / ``has_runtimes_from_path_batch``
boolean-fold scalars and their paired
``/api/entitlement/has-features-from-path-batch`` /
``/api/entitlement/has-runtimes-from-path-batch`` endpoints.

Mirror-direction siblings of :func:`has_features_at_path_batch` (which
fixes ONE source and fans out over N destinations): here we fix ONE
destination and fan out over N sources. Lets a surface render "for each
of the tiers my fleet currently sits on, does {fleet, sso} unlock at
every rung climbed toward Enterprise?" off ONE URL.

Pins:

1. Scalar envelope shape (``{"tiers": [...], "unknown": [...]}``) and
   per-source row shape (``from`` / ``from_label`` / ``from_rank`` /
   ``direction`` / ``path``).
2. Per-source ``path`` byte-parity against the scalar
   :func:`has_features_at_path` / :func:`has_runtimes_at_path` for the
   same ``(from, to, bundle)`` triple.
3. Unknown-``to`` short-circuits: scalar returns ``None``; endpoint
   returns 200 with ``tiers=[]`` (never 4xxs).
4. Unknown sources echo into ``unknown[]`` (scalar) /
   ``unknown_tiers[]`` (endpoint) without short-circuiting the batch.
5. Direction detection per source (``upgrade`` / ``downgrade`` /
   ``lateral`` / ``identity``) all computed relative to the shared
   ``to_tier``.
6. Grace-independence: same rows under grace on vs enforce.
7. Empty / ``None`` / non-iterable / typo'd bundle collapses every
   rung's fold to ``False`` on EVERY source (fail-closed).
8. Runtime scalar strict alias posture (no canonicalisation at scalar
   layer); paired endpoint canonicalises upstream + dedups alias-and-
   canonical to ONE fold input per rung.
9. Endpoint envelope shape (fixed key set) across every branch and
   per-source rollups ``path_length`` / ``allowed_count`` /
   ``all_allowed`` / ``any_allowed``.
10. Never 5xxs: fallback envelope on helper blowup.
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


# ── Envelope shape constants ───────────────────────────────────────────────

_FEATURES_KEYS = {
    "to",
    "to_label",
    "to_rank",
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
    "to",
    "to_label",
    "to_rank",
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
    "from",
    "from_label",
    "from_rank",
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


# ── Scalar shape ───────────────────────────────────────────────────────────


def test_scalar_features_returns_dict_shape(ent):
    out = ent.has_features_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", ["fleet"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_scalar_runtimes_returns_dict_shape(ent):
    out = ent.has_runtimes_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", ["claude_code"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}


def test_scalar_features_row_shape(ent):
    out = ent.has_features_from_path_batch(["oss"], "enterprise", ["fleet"])
    assert out is not None
    assert len(out["tiers"]) == 1
    row = out["tiers"][0]
    assert set(row.keys()) == {"from", "from_label", "from_rank", "direction", "path"}
    assert row["from"] == "oss"
    assert isinstance(row["path"], list)


# ── Unknown-``to`` short-circuit ───────────────────────────────────────────


def test_scalar_features_unknown_to_returns_none(ent):
    assert ent.has_features_from_path_batch(["oss"], "bogus", ["fleet"]) is None
    assert ent.has_features_from_path_batch(["oss"], "", ["fleet"]) is None
    # noinspection PyTypeChecker
    assert ent.has_features_from_path_batch(["oss"], None, ["fleet"]) is None


def test_scalar_runtimes_unknown_to_returns_none(ent):
    assert ent.has_runtimes_from_path_batch(["oss"], "bogus", ["claude_code"]) is None


# ── Empty / unknown sources ────────────────────────────────────────────────


def test_scalar_features_empty_sources_returns_empty_tiers(ent):
    out = ent.has_features_from_path_batch([], "enterprise", ["fleet"])
    assert out == {"tiers": [], "unknown": []}


def test_scalar_features_unknown_source_echoes_to_unknown(ent):
    out = ent.has_features_from_path_batch(
        ["bogus_id"], "enterprise", ["fleet"]
    )
    assert out == {"tiers": [], "unknown": ["bogus_id"]}


def test_scalar_features_partial_unknown_source(ent):
    out = ent.has_features_from_path_batch(
        ["bogus_a", "oss", "bogus_b"], "enterprise", ["fleet"]
    )
    assert out is not None
    from_ids = [r["from"] for r in out["tiers"]]
    assert from_ids == ["oss"]
    assert set(out["unknown"]) == {"bogus_a", "bogus_b"}


# ── Path byte-parity against singular ──────────────────────────────────────


def test_scalar_features_path_byte_parity_with_singular(ent):
    batch = ent.has_features_from_path_batch(
        ["oss", "cloud_starter", "cloud_pro"], "enterprise", ["fleet", "sso"]
    )
    assert batch is not None
    for row in batch["tiers"]:
        singular = ent.has_features_at_path(row["from"], "enterprise", ["fleet", "sso"])
        assert row["path"] == singular, row["from"]


def test_scalar_runtimes_path_byte_parity_with_singular(ent):
    batch = ent.has_runtimes_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", ["claude_code"]
    )
    assert batch is not None
    for row in batch["tiers"]:
        singular = ent.has_runtimes_at_path(row["from"], "enterprise", ["claude_code"])
        assert row["path"] == singular, row["from"]


# ── Direction detection ────────────────────────────────────────────────────


def test_scalar_direction_upgrade(ent):
    out = ent.has_features_from_path_batch(["oss"], "enterprise", ["fleet"])
    assert out is not None
    assert out["tiers"][0]["direction"] == "upgrade"


def test_scalar_direction_downgrade(ent):
    out = ent.has_features_from_path_batch(["enterprise"], "oss", ["fleet"])
    assert out is not None
    assert out["tiers"][0]["direction"] == "downgrade"


def test_scalar_direction_identity(ent):
    out = ent.has_features_from_path_batch(["oss"], "oss", ["fleet"])
    assert out is not None
    row = out["tiers"][0]
    assert row["direction"] == "identity"
    assert row["path"] == []


def test_scalar_mixed_directions_labelled_per_source(ent):
    out = ent.has_features_from_path_batch(
        ["oss", "cloud_starter", "cloud_pro"], "cloud_starter", ["fleet"]
    )
    assert out is not None
    directions = {r["from"]: r["direction"] for r in out["tiers"]}
    assert directions["oss"] == "upgrade"
    assert directions["cloud_starter"] == "identity"
    assert directions["cloud_pro"] == "downgrade"


# ── Bundle-fold semantics ──────────────────────────────────────────────────


def test_scalar_empty_features_folds_every_rung_false(ent):
    for empty in ([], None):
        out = ent.has_features_from_path_batch(["oss"], "enterprise", empty)
        assert out is not None
        for row in out["tiers"]:
            for rung in row["path"]:
                assert rung["has_features_at"] is False


def test_scalar_unknown_feature_folds_every_rung_false(ent):
    out = ent.has_features_from_path_batch(
        ["oss"], "enterprise", ["bogus_feature"]
    )
    assert out is not None
    for row in out["tiers"]:
        for rung in row["path"]:
            assert rung["has_features_at"] is False


def test_scalar_unknown_runtime_folds_every_rung_false(ent):
    out = ent.has_runtimes_from_path_batch(
        ["oss"], "enterprise", ["bogus_runtime"]
    )
    assert out is not None
    for row in out["tiers"]:
        for rung in row["path"]:
            assert rung["has_runtimes_at"] is False


def test_scalar_runtimes_strict_alias_posture(ent):
    # No canonical_runtime resolution at scalar layer: ``claude-code`` is
    # not in ALL_RUNTIMES after strip/lower, so every rung's fold collapses
    # to False. Alias tolerance lives on the endpoint.
    out = ent.has_runtimes_from_path_batch(
        ["oss"], "enterprise", ["claude-code"]
    )
    assert out is not None
    for row in out["tiers"]:
        for rung in row["path"]:
            assert rung["has_runtimes_at"] is False


# ── Grace-independence ─────────────────────────────────────────────────────


def test_scalar_features_grace_independent(ent, enforced):
    grace_out = ent.has_features_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", ["fleet"]
    )
    enforce_out = enforced.has_features_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", ["fleet"]
    )
    assert grace_out == enforce_out


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_features_envelope_keys(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert body["to"] == "enterprise"
    assert body["features"] == ["fleet"]
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_ROW_KEYS


def test_endpoint_runtimes_envelope_keys(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-from-path-batch?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"


# ── Endpoint never 4xxs ────────────────────────────────────────────────────


def test_endpoint_features_unknown_to_returns_200_empty(client):
    resp = client.get(
        "/api/entitlement/has-features-from-path-batch?from=oss&to=bogus&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["to"] == "bogus"
    assert body["to_rank"] == -1


def test_endpoint_features_missing_to_returns_200_empty(client):
    resp = client.get(
        "/api/entitlement/has-features-from-path-batch?from=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


def test_endpoint_features_unknown_source_bucketed(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=bogus_a,oss,bogus_b&to=enterprise&features=fleet",
    )
    from_ids = [r["from"] for r in body["tiers"]]
    assert from_ids == ["oss"]
    assert set(body["unknown_tiers"]) == {"bogus_a", "bogus_b"}


# ── Endpoint per-source rollups ────────────────────────────────────────────


def test_endpoint_identity_row_zeroed_rollups(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss&to=oss&features=fleet",
    )
    assert len(body["tiers"]) == 1
    row = body["tiers"][0]
    assert row["direction"] == "identity"
    assert row["path"] == []
    assert row["path_length"] == 0
    assert row["allowed_count"] == 0
    assert row["all_allowed"] is False
    assert row["any_allowed"] is False


def test_endpoint_upgrade_row_positive_rollups(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss&to=enterprise&features=fleet",
    )
    assert body["tiers"]
    row = body["tiers"][0]
    assert row["path_length"] > 0
    assert row["allowed_count"] >= 0
    assert row["allowed_count"] <= row["path_length"]
    # any_allowed / all_allowed derive consistently from allowed_count.
    assert row["any_allowed"] is (row["allowed_count"] > 0)
    assert row["all_allowed"] is (
        row["path_length"] > 0 and row["allowed_count"] == row["path_length"]
    )


def test_endpoint_direction_labels_per_source(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss,cloud_starter,cloud_pro&to=cloud_starter&features=fleet",
    )
    directions = {r["from"]: r["direction"] for r in body["tiers"]}
    assert directions["oss"] == "upgrade"
    assert directions["cloud_starter"] == "identity"
    assert directions["cloud_pro"] == "downgrade"


# ── Endpoint alias canonicalisation ────────────────────────────────────────


def test_endpoint_runtime_alias_canonicalised(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-from-path-batch?from=oss&to=enterprise&runtimes=claude-code",
    )
    # Alias canonicalises upstream to `claude_code`.
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1


def test_endpoint_runtime_alias_and_canonical_dedup(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes-from-path-batch?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["count"] == 1


# ── Endpoint fail-closed on unknown token ──────────────────────────────────


def test_endpoint_unknown_feature_token_fails_closed(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet,bogus_feature",
    )
    assert body["unknown"] == ["bogus_feature"]
    for row in body["tiers"]:
        assert row["allowed_count"] == 0
        assert row["all_allowed"] is False
        for rung in row["path"]:
            assert rung["has_features_at"] is False


# ── Endpoint parity with singular ``/has-features-at-path`` ────────────────


def test_endpoint_features_per_source_path_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/has-features-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    for row in body["tiers"]:
        singular = _get_json(
            client,
            f"/api/entitlement/has-features-at-path?from={row['from']}&to=enterprise&features=fleet",
        )
        assert row["path"] == singular["path"], row["from"]


# ── Never 5xxs ─────────────────────────────────────────────────────────────


def test_endpoint_features_never_5xxs_on_helper_blowup(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def _boom(*_a, **_kw):  # pragma: no cover - reached via helper stub
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "has_features_from_path_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-features-from-path-batch?from=oss&to=enterprise&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    # Fallback envelope preserves ``to`` + echoes both dropped sources & tokens.
    assert body["to"] == "enterprise"
    assert body["unknown_tiers"] == ["oss"]
    assert body["unknown"] == ["fleet"]
