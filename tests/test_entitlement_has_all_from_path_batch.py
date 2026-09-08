"""Tests for the aggregate mixed-axis source-batch path
:func:`clawmetry.entitlements.has_all_from_path_batch` /
:func:`clawmetry.entitlements.missing_all_from_path_batch` scalars and
their paired ``/api/entitlement/{has,missing}-all-from-path-batch``
endpoints.

Source-axis batch companions of :func:`has_all_at_path` /
:func:`missing_all_at_path` (single source, single destination) and
5-axis aggregate extensions of :func:`has_features_from_path_batch` /
:func:`has_runtimes_from_path_batch` /
:func:`missing_features_from_path_batch` /
:func:`missing_runtimes_from_path_batch` (per-axis source-batch path
walkers). Mirror-direction siblings of :func:`has_all_at_path_batch` /
:func:`missing_all_at_path_batch` (destination-batch path): where those
fan out over N candidate destinations from ONE source, these fan out
over N candidate sources to ONE shared destination.

This file pins:

1. Scalar per-source row shape ({from, from_label, from_rank, direction,
   path}) with per-rung ``has_all_at`` / ``missing`` byte-parity against
   :func:`has_all_at_path` / :func:`missing_all_at_path` for the same
   (from, to, bundle) triple.
2. Multi-source walk semantics (source-specific path lengths, direction
   detection, purchasable-tier / destination-sibling filter inherited
   through the singular scalar).
3. Bundle-fold posture inherited from :func:`has_all_at_path` /
   :func:`missing_all_at_path` (fail-closed empty-``False`` on the
   boolean-fold side; row-detail complement on the missing side).
4. Complement invariant with paired call: per source per rung,
   ``any(missing_row["missing"].values())`` strict-negates
   ``has_row["has_all_at"]`` on the fully-parseable branch.
5. Unknown-``to`` short-circuit -> scalar returns ``None``; endpoint
   returns 200 with ``tiers=[]`` (never 4xxs).
6. Unknown / blank source ids -> echoed into ``unknown`` /
   ``unknown_tiers`` respectively; valid sources keep building.
7. Grace-independence: same answer under grace on vs enforce for the
   same (from_tiers, to, bundle) triple.
8. Runtime alias posture: scalar strict; endpoint canonicalises
   upstream so ``?runtimes=claude-code`` behaves like
   ``?runtimes=claude_code``.
9. Never-raises on per-source delegate blowup: log-and-``unknown[]``
   at scalar layer; empty-``tiers`` fallback envelope at endpoint layer.
10. Endpoint envelope shape (fixed key set) across every input branch
    including the unknown-``to`` branch.
11. Rollup fields per source (``allowed_count`` / ``all_allowed`` /
    ``any_allowed`` for has; ``denied_count`` / ``all_denied`` /
    ``any_denied`` for missing) fold as documented on
    :func:`_has_all_from_path_batch_body` /
    :func:`_missing_all_from_path_batch_body`.
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


_ENVELOPE_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "unknown_tiers",
    "supplied_axes",
    "supplied_count",
    "tiers",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_HAS_TIER_KEYS = {
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
_MISSING_TIER_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "direction",
    "path",
    "path_length",
    "denied_count",
    "all_denied",
    "any_denied",
}
_HAS_ROW_KEYS = {"tier", "tier_label", "tier_rank", "has_all_at"}
_MISSING_ROW_KEYS = {"tier", "tier_label", "tier_rank", "missing"}
_MISSING_INNER_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


def _any_denied(row) -> bool:
    m = row.get("missing") or {}
    for v in m.values():
        if isinstance(v, list):
            if v:
                return True
        elif v is not None:
            return True
    return False


# ── has_all_from_path_batch scalar ────────────────────────────────────────


def test_scalar_returns_dict_with_tiers_and_unknown(ent):
    r = ent.has_all_from_path_batch(["oss"], "enterprise", features=["fleet"])
    assert isinstance(r, dict)
    assert set(r.keys()) == {"tiers", "unknown"}
    assert isinstance(r["tiers"], list)
    assert isinstance(r["unknown"], list)


def test_scalar_unknown_to_returns_none(ent):
    assert ent.has_all_from_path_batch(["oss"], "bogus", features=["fleet"]) is None
    assert ent.has_all_from_path_batch(["oss"], "", features=["fleet"]) is None
    assert ent.has_all_from_path_batch(["oss"], None, features=["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_unknown_sources_go_to_unknown_bucket(ent):
    r = ent.has_all_from_path_batch(
        ["bogus", "oss", "other"], "enterprise", features=["fleet"]
    )
    assert [row["from"] for row in r["tiers"]] == ["oss"]
    assert r["unknown"] == ["bogus", "other"]


def test_scalar_normalise_sources(ent):
    r = ent.has_all_from_path_batch(
        "  OSS ,  cloud_starter ,oss ", "enterprise", features=["fleet"]
    )
    froms = [row["from"] for row in r["tiers"]]
    assert froms == ["oss", "cloud_starter"]  # dedup, first-seen, lowercased


def test_scalar_per_source_row_shape(ent):
    r = ent.has_all_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", features=["fleet"]
    )
    for row in r["tiers"]:
        assert set(row.keys()) == {
            "from",
            "from_label",
            "from_rank",
            "direction",
            "path",
        }
        assert isinstance(row["path"], list)


def test_scalar_per_rung_parity_with_has_all_at_path(ent):
    """Per-source ``path`` byte-equals :func:`has_all_at_path` for the
    same (from, to, bundle) triple -- pins the batch/scalar drift lock."""
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {
            "features": ["fleet", "sso"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    ]
    sources = ["oss", "trial", "cloud_starter", "cloud_pro"]
    for bundle in bundles:
        batch = ent.has_all_from_path_batch(sources, "enterprise", **bundle)
        for srow in batch["tiers"]:
            singular = ent.has_all_at_path(srow["from"], "enterprise", **bundle)
            assert srow["path"] == singular, (
                bundle,
                srow["from"],
                srow["path"],
                singular,
            )


def test_scalar_direction_semantics(ent):
    # upgrade
    r = ent.has_all_from_path_batch(["oss", "cloud_starter"], "enterprise", features=["fleet"])
    for row in r["tiers"]:
        assert row["direction"] == "upgrade"
    # downgrade
    r = ent.has_all_from_path_batch(["enterprise"], "oss", features=["fleet"])
    assert r["tiers"][0]["direction"] == "downgrade"
    # lateral (cloud_pro / pro live at rank 2)
    r = ent.has_all_from_path_batch(["cloud_pro"], "pro", features=["fleet"])
    assert r["tiers"][0]["direction"] == "lateral"
    assert len(r["tiers"][0]["path"]) == 1
    # identity
    r = ent.has_all_from_path_batch(["pro"], "pro", features=["fleet"])
    assert r["tiers"][0]["direction"] == "identity"
    assert r["tiers"][0]["path"] == []


def test_scalar_bundle_typo_fails_closed_per_source(ent):
    """Unknown token in the bundle collapses every rung of every source
    to ``has_all_at=False`` (inherits singular scalar's typo-``False``
    posture)."""
    r = ent.has_all_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", features=["notafeature"]
    )
    for srow in r["tiers"]:
        assert srow["path"]  # non-empty rung list
        for prow in srow["path"]:
            assert prow["has_all_at"] is False


def test_scalar_empty_axes_fails_closed(ent):
    """No axes supplied -> every rung of every source reports
    ``has_all_at=False`` (matches :func:`has_all_at` empty-``False``
    posture)."""
    r = ent.has_all_from_path_batch(["oss", "cloud_starter"], "enterprise")
    for srow in r["tiers"]:
        for prow in srow["path"]:
            assert prow["has_all_at"] is False


def test_scalar_generator_bundle_is_snapshotted(ent):
    """Generator / one-shot iterable is materialised once at fold top
    so fan-out across sources does not consume it."""
    def gen():
        yield "fleet"

    r = ent.has_all_from_path_batch(
        ["oss", "cloud_starter", "cloud_pro"], "enterprise", features=gen()
    )
    froms = [row["from"] for row in r["tiers"]]
    assert froms == ["oss", "cloud_starter", "cloud_pro"]  # all populated
    for srow in r["tiers"]:
        assert srow["path"]  # every source got its path


def test_scalar_trial_accepted_as_source(ent):
    r = ent.has_all_from_path_batch(["trial"], "enterprise", features=["fleet"])
    assert r["unknown"] == []
    assert r["tiers"][0]["from"] == "trial"


# ── missing_all_from_path_batch scalar ────────────────────────────────────


def test_scalar_missing_returns_dict_with_tiers_and_unknown(ent):
    r = ent.missing_all_from_path_batch(["oss"], "enterprise", features=["fleet"])
    assert isinstance(r, dict)
    assert set(r.keys()) == {"tiers", "unknown"}


def test_scalar_missing_unknown_to_returns_none(ent):
    assert (
        ent.missing_all_from_path_batch(["oss"], "bogus", features=["fleet"])
        is None
    )
    assert (
        ent.missing_all_from_path_batch(["oss"], None, features=["fleet"])  # type: ignore[arg-type]
        is None
    )


def test_scalar_missing_per_rung_parity_with_missing_all_at_path(ent):
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {
            "features": ["fleet", "sso"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    ]
    sources = ["oss", "trial", "cloud_starter", "cloud_pro"]
    for bundle in bundles:
        batch = ent.missing_all_from_path_batch(sources, "enterprise", **bundle)
        for srow in batch["tiers"]:
            singular = ent.missing_all_at_path(srow["from"], "enterprise", **bundle)
            assert srow["path"] == singular, (bundle, srow["from"])


def test_scalar_missing_direction_semantics(ent):
    r = ent.missing_all_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", features=["fleet"]
    )
    for row in r["tiers"]:
        assert row["direction"] == "upgrade"


def test_scalar_missing_generator_bundle_is_snapshotted(ent):
    def gen():
        yield "fleet"

    r = ent.missing_all_from_path_batch(
        ["oss", "cloud_starter", "cloud_pro"], "enterprise", features=gen()
    )
    for srow in r["tiers"]:
        assert srow["path"]


# ── Complement invariant ──────────────────────────────────────────────────


def test_scalar_complement_invariant(ent):
    """Per source per rung, any(missing.values()) strict-negates
    has_all_at on the paired call for the same fully-parseable
    inputs."""
    bundles = [
        {"features": ["fleet"]},
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    ]
    sources = ["oss", "trial", "cloud_starter", "cloud_pro"]
    for bundle in bundles:
        r_has = ent.has_all_from_path_batch(sources, "enterprise", **bundle)
        r_miss = ent.missing_all_from_path_batch(sources, "enterprise", **bundle)
        assert [d["from"] for d in r_has["tiers"]] == [
            d["from"] for d in r_miss["tiers"]
        ]
        for h_src, m_src in zip(r_has["tiers"], r_miss["tiers"]):
            for h_row, m_row in zip(h_src["path"], m_src["path"]):
                allowed = h_row["has_all_at"]
                any_denied = _any_denied(m_row)
                assert any_denied == (not allowed), (
                    bundle,
                    h_src["from"],
                    h_row,
                    m_row,
                )


# ── Grace independence ────────────────────────────────────────────────────


def test_scalar_grace_independence(ent, enforced):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"], "channels": 5}
    sources = ["oss", "cloud_starter"]
    ent_answer = ent.has_all_from_path_batch(sources, "enterprise", **bundle)
    enforced_answer = enforced.has_all_from_path_batch(sources, "enterprise", **bundle)
    assert ent_answer == enforced_answer

    miss_ent = ent.missing_all_from_path_batch(sources, "enterprise", **bundle)
    miss_enf = enforced.missing_all_from_path_batch(sources, "enterprise", **bundle)
    assert miss_ent == miss_enf


# ── Endpoint envelope + never-4xx ─────────────────────────────────────────


def test_endpoint_has_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    for tier in body["tiers"]:
        assert set(tier.keys()) == _HAS_TIER_KEYS
        for row in tier["path"]:
            assert set(row.keys()) == _HAS_ROW_KEYS


def test_endpoint_missing_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    for tier in body["tiers"]:
        assert set(tier.keys()) == _MISSING_TIER_KEYS
        for row in tier["path"]:
            assert set(row.keys()) == _MISSING_ROW_KEYS
            assert set(row["missing"].keys()) == _MISSING_INNER_KEYS


def test_endpoint_never_4xx_on_missing_to(client):
    body = _get_json(client, "/api/entitlement/has-all-from-path-batch")
    assert body["tiers"] == []
    assert body["to"] == ""
    assert set(body.keys()) == _ENVELOPE_KEYS

    body = _get_json(client, "/api/entitlement/missing-all-from-path-batch")
    assert body["tiers"] == []
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_endpoint_never_4xx_on_unknown_to(client):
    body = _get_json(
        client, "/api/entitlement/has-all-from-path-batch?from=oss&to=bogus"
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["oss"]


def test_endpoint_never_4xx_on_all_unknown_sources(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=bogus,other&to=enterprise&features=fleet",
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["bogus", "other"]


def test_endpoint_never_4xx_on_unknown_feature(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&features=notafeature",
    )
    assert body["unknown_features"] == ["notafeature"]
    # endpoint-level typo collapse: every rung of every source reads False
    for tier in body["tiers"]:
        for row in tier["path"]:
            assert row["has_all_at"] is False


def test_endpoint_never_4xx_on_non_int_capacity(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&channels=notanint",
    )
    # non-int capacity collapses every rung's has_all_at to False
    for tier in body["tiers"]:
        for row in tier["path"]:
            assert row["has_all_at"] is False

    # missing endpoint surfaces the raw string on every rung
    body_m = _get_json(
        client,
        "/api/entitlement/missing-all-from-path-batch?from=oss&to=enterprise&channels=notanint",
    )
    for tier in body_m["tiers"]:
        for row in tier["path"]:
            assert row["missing"]["channels"] == "notanint"


def test_endpoint_no_axes_supplied_fails_closed(client):
    body = _get_json(
        client, "/api/entitlement/has-all-from-path-batch?from=oss,cloud_starter&to=enterprise"
    )
    assert body["supplied_axes"] == []
    assert body["supplied_count"] == 0
    for tier in body["tiers"]:
        for row in tier["path"]:
            assert row["has_all_at"] is False


# ── Endpoint per-rung parity with single-source endpoint ──────────────────


def test_endpoint_per_rung_parity_with_singular_has(client):
    """Per source ``path`` byte-equals
    ``/has-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for
    the same triple -- pins the endpoint drift lock."""
    sources = ["oss", "cloud_starter", "cloud_pro"]
    bundle_qs = "features=fleet,sso&runtimes=claude_code&channels=5&retention_days=30&nodes=2"
    batch = _get_json(
        client,
        f"/api/entitlement/has-all-from-path-batch?from={','.join(sources)}&to=enterprise&{bundle_qs}",
    )
    by_from = {t["from"]: t for t in batch["tiers"]}
    for src in sources:
        singular = _get_json(
            client,
            f"/api/entitlement/has-all-at-path?from={src}&to=enterprise&{bundle_qs}",
        )
        assert by_from[src]["path"] == singular["path"], src


def test_endpoint_per_rung_parity_with_singular_missing(client):
    sources = ["oss", "cloud_starter", "cloud_pro"]
    bundle_qs = "features=fleet,sso&runtimes=claude_code&channels=5&retention_days=30&nodes=2"
    batch = _get_json(
        client,
        f"/api/entitlement/missing-all-from-path-batch?from={','.join(sources)}&to=enterprise&{bundle_qs}",
    )
    by_from = {t["from"]: t for t in batch["tiers"]}
    for src in sources:
        singular = _get_json(
            client,
            f"/api/entitlement/missing-all-at-path?from={src}&to=enterprise&{bundle_qs}",
        )
        assert by_from[src]["path"] == singular["path"], src


# ── Endpoint rollup fields ────────────────────────────────────────────────


def test_endpoint_has_rollup_fields(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    for tier in body["tiers"]:
        allowed = [r["has_all_at"] for r in tier["path"]]
        assert tier["path_length"] == len(tier["path"])
        assert tier["allowed_count"] == sum(1 for x in allowed if x)
        assert tier["all_allowed"] == (bool(allowed) and all(allowed))
        assert tier["any_allowed"] == any(allowed)


def test_endpoint_missing_rollup_fields(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    for tier in body["tiers"]:
        denied = [_any_denied(r) for r in tier["path"]]
        assert tier["path_length"] == len(tier["path"])
        assert tier["denied_count"] == sum(1 for x in denied if x)
        assert tier["all_denied"] == (bool(denied) and all(denied))
        assert tier["any_denied"] == any(denied)


# ── Endpoint runtime alias canonicalisation ───────────────────────────────


def test_endpoint_runtime_alias_canonicalisation(client):
    body_alias = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&runtimes=claude-code",
    )
    body_canon = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&runtimes=claude_code",
    )
    assert body_alias["runtimes"] == body_canon["runtimes"] == ["claude_code"]
    assert body_alias["unknown_runtimes"] == body_canon["unknown_runtimes"] == []
    assert body_alias["tiers"] == body_canon["tiers"]


def test_endpoint_runtime_alias_and_canonical_dedup(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    # alias + canonical -> ONE entry
    assert body["runtimes"] == ["claude_code"]


# ── Complement invariant at endpoint layer ────────────────────────────────


def test_endpoint_complement_invariant(client):
    sources = "oss,cloud_starter"
    bundle_qs = "features=fleet,sso&runtimes=claude_code&channels=5"
    h = _get_json(
        client,
        f"/api/entitlement/has-all-from-path-batch?from={sources}&to=enterprise&{bundle_qs}",
    )
    m = _get_json(
        client,
        f"/api/entitlement/missing-all-from-path-batch?from={sources}&to=enterprise&{bundle_qs}",
    )
    assert [t["from"] for t in h["tiers"]] == [t["from"] for t in m["tiers"]]
    for h_src, m_src in zip(h["tiers"], m["tiers"]):
        for h_row, m_row in zip(h_src["path"], m_src["path"]):
            allowed = h_row["has_all_at"]
            any_denied = _any_denied(m_row)
            assert any_denied == (not allowed), (h_src["from"], h_row, m_row)


# ── Endpoint direction semantics ──────────────────────────────────────────


def test_endpoint_direction_matches_singular(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=pro,enterprise,cloud_pro&to=cloud_pro&features=fleet",
    )
    by_from = {t["from"]: t for t in body["tiers"]}
    assert by_from["pro"]["direction"] == "lateral"
    assert by_from["enterprise"]["direction"] == "downgrade"
    assert by_from["cloud_pro"]["direction"] == "identity"


# ── Endpoint required_tier rollup ─────────────────────────────────────────


def test_endpoint_required_tier_matches_min_tier_for_all(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss,cloud_starter&to=enterprise&features=fleet",
    )
    expected = ent.min_tier_for_all(features=["fleet"])
    assert body["required_tier"] == expected
    assert body["required_tier_rank"] == ent.tier_rank(expected)


def test_endpoint_required_tier_none_when_no_axes(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise",
    )
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1


# ── Never-5xx fallback ────────────────────────────────────────────────────


def test_endpoint_never_5xx_on_body_blowup(client, monkeypatch):
    """Force the body-builder to raise; fallback envelope must still
    return 200 with the same key set."""
    from routes import entitlement as _re

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(_re, "_has_all_from_path_batch_body", _boom)
    body = _get_json(
        client,
        "/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&features=fleet",
    )
    assert body["tiers"] == []
    assert set(body.keys()) == _ENVELOPE_KEYS

    monkeypatch.setattr(_re, "_missing_all_from_path_batch_body", _boom)
    body = _get_json(
        client,
        "/api/entitlement/missing-all-from-path-batch?from=oss&to=enterprise&features=fleet",
    )
    assert body["tiers"] == []
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_scalar_never_raises_on_per_source_blowup(ent, monkeypatch):
    """Per-source delegate failure logs a warning and short-circuits
    that id into ``unknown[]`` while the rest of the batch keeps
    building."""
    calls = {"n": 0}
    real = ent.has_all_at_path

    def _sometimes_boom(f, t, **kw):
        calls["n"] += 1
        if f == "cloud_pro":
            raise RuntimeError("boom")
        return real(f, t, **kw)

    monkeypatch.setattr(ent, "has_all_at_path", _sometimes_boom)
    r = ent.has_all_from_path_batch(
        ["oss", "cloud_pro", "cloud_starter"], "enterprise", features=["fleet"]
    )
    assert "cloud_pro" in r["unknown"]
    assert [row["from"] for row in r["tiers"]] == ["oss", "cloud_starter"]


# ── Endpoint mirror-direction cross-consistency ───────────────────────────


def test_endpoint_source_batch_mirrors_destination_batch(client):
    """A single-source single-destination call through this endpoint has
    the same path as the mirror-direction destination-batch endpoint for
    the same (from, to, bundle) triple -- pins the twins together."""
    bundle_qs = "features=fleet&runtimes=claude_code&channels=5"
    src_batch = _get_json(
        client,
        f"/api/entitlement/has-all-from-path-batch?from=oss&to=enterprise&{bundle_qs}",
    )
    dest_batch = _get_json(
        client,
        f"/api/entitlement/has-all-at-path-batch?from=oss&to=enterprise&{bundle_qs}",
    )
    assert src_batch["tiers"][0]["path"] == dest_batch["tiers"][0]["path"]
