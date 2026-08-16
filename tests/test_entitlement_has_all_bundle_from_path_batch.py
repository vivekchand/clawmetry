"""Tests for the source-axis bundle-shape path-batch scalars
``has_all_bundle_from_path_batch`` / ``missing_all_bundle_from_path_batch``
and their paired ``/api/entitlement/has-all-bundle-from-path-batch`` /
``/api/entitlement/missing-all-bundle-from-path-batch`` endpoints.

Bundle-shape twin of :func:`has_features_from_path_batch` /
:func:`has_runtimes_from_path_batch` (source-batch on the kwargs
seat) and source-batch complement of the destination-batch
:func:`has_all_bundle_at_path_batch` (PR #4884). Where the singular
:func:`has_all_bundle_at_path` walks one source to one destination
for one bundle, this fans out over N candidate sources.

Pins:

1. Scalar envelope shape (``{"tiers": [...], "unknown": [...]}``) and
   per-source row shape (``from`` / ``from_label`` / ``from_rank`` /
   ``direction`` / ``path``).
2. Per-source ``path`` byte-parity against the scalar
   :func:`has_all_bundle_at_path` / :func:`missing_all_bundle_at_path`
   for the same ``(from, to, bundle)`` triple.
3. Unknown-``to`` short-circuits: scalar returns ``None``; endpoint
   returns 200 with ``tiers=[]`` (never 4xxs).
4. Unknown sources echo into ``unknown[]`` (scalar) /
   ``unknown_tiers[]`` (endpoint) without short-circuiting the batch.
5. Direction detection per source (``upgrade`` / ``downgrade`` /
   ``lateral`` / ``identity``) all computed relative to the shared
   ``to_tier``.
6. Grace-independence: same rows under grace on vs enforce for the
   same ``(from_tiers, to_tier, bundle)`` triple.
7. Complement invariant per source per rung between the boolean-fold
   and row-detail scalars.
8. Endpoint envelope shape (fixed key set) across every branch and
   per-source rollups (``path_length`` / ``allowed_count`` /
   ``all_allowed`` / ``any_allowed`` for has;
   ``denied_count`` / ``all_denied`` / ``any_denied`` for missing).
9. 400 branches (missing / non-object bundle); never 5xxs (fallback
   envelope on helper blowup).
10. Bare-axis body shorthand and CSV ``from_tiers`` acceptance.
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

_HAS_ENVELOPE_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_tiers",
    "count",
    "tiers",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_MISSING_ENVELOPE_KEYS = set(_HAS_ENVELOPE_KEYS)  # same header shape
_HAS_ROW_KEYS = {
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
_MISSING_ROW_KEYS = {
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


HAS_URL = "/api/entitlement/has-all-bundle-from-path-batch"
MISS_URL = "/api/entitlement/missing-all-bundle-from-path-batch"


# ── Scalar shape ───────────────────────────────────────────────────────────


def test_has_scalar_returns_dict_shape(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", {"features": ["fleet"]}
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_missing_scalar_returns_dict_shape(ent):
    out = ent.missing_all_bundle_from_path_batch(
        ["oss", "cloud_starter"], "enterprise", {"features": ["fleet"]}
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}


def test_has_scalar_row_shape(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss"], "enterprise", {"features": ["fleet"]}
    )
    assert out is not None
    assert len(out["tiers"]) == 1
    row = out["tiers"][0]
    assert set(row.keys()) == {
        "from",
        "from_label",
        "from_rank",
        "direction",
        "path",
    }
    assert row["from"] == "oss"
    assert isinstance(row["path"], list)


def test_missing_scalar_row_shape(ent):
    out = ent.missing_all_bundle_from_path_batch(
        ["oss"], "enterprise", {"features": ["fleet"]}
    )
    assert out is not None
    row = out["tiers"][0]
    assert set(row.keys()) == {
        "from",
        "from_label",
        "from_rank",
        "direction",
        "path",
    }


# ── Per-rung parity with singular scalars ──────────────────────────────────


def test_has_scalar_per_rung_parity_with_bundle_at_path(ent):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    from_tiers = ["oss", "cloud_starter", "cloud_pro"]
    to = "enterprise"
    out = ent.has_all_bundle_from_path_batch(from_tiers, to, bundle)
    for row in out["tiers"]:
        singular = ent.has_all_bundle_at_path(row["from"], to, bundle)
        assert row["path"] == singular


def test_missing_scalar_per_rung_parity_with_bundle_at_path(ent):
    bundle = {"features": ["fleet"], "channels": 5}
    from_tiers = ["oss", "cloud_starter"]
    to = "enterprise"
    out = ent.missing_all_bundle_from_path_batch(from_tiers, to, bundle)
    for row in out["tiers"]:
        singular = ent.missing_all_bundle_at_path(row["from"], to, bundle)
        assert row["path"] == singular


# ── Unknown-``to`` short-circuit ───────────────────────────────────────────


def test_has_scalar_unknown_to_returns_none(ent):
    assert (
        ent.has_all_bundle_from_path_batch(
            ["oss"], "bogus", {"features": ["fleet"]}
        )
        is None
    )
    assert (
        ent.has_all_bundle_from_path_batch(
            ["oss"], "", {"features": ["fleet"]}
        )
        is None
    )
    # noinspection PyTypeChecker
    assert (
        ent.has_all_bundle_from_path_batch(
            ["oss"], None, {"features": ["fleet"]}
        )
        is None
    )


def test_missing_scalar_unknown_to_returns_none(ent):
    assert (
        ent.missing_all_bundle_from_path_batch(
            ["oss"], "bogus", {"features": ["fleet"]}
        )
        is None
    )


# ── Empty / unknown sources ────────────────────────────────────────────────


def test_has_scalar_empty_sources(ent):
    assert ent.has_all_bundle_from_path_batch(
        [], "enterprise", {"features": ["fleet"]}
    ) == {"tiers": [], "unknown": []}


def test_has_scalar_unknown_source_echoes(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["bogus_id"], "enterprise", {"features": ["fleet"]}
    )
    assert out == {"tiers": [], "unknown": ["bogus_id"]}


def test_has_scalar_mixed_known_and_unknown_sources(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss", "bogus", "cloud_starter"],
        "enterprise",
        {"features": ["fleet"]},
    )
    assert [r["from"] for r in out["tiers"]] == ["oss", "cloud_starter"]
    assert out["unknown"] == ["bogus"]


# ── Direction detection ────────────────────────────────────────────────────


def test_has_scalar_direction_per_source(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss", "enterprise", "cloud_starter", "cloud_pro"],
        "cloud_pro",
        {"features": ["fleet"]},
    )
    directions = {r["from"]: r["direction"] for r in out["tiers"]}
    assert directions["oss"] == "upgrade"
    assert directions["enterprise"] == "downgrade"
    assert directions["cloud_starter"] == "upgrade"
    assert directions["cloud_pro"] == "identity"


def test_has_scalar_lateral_direction(ent):
    # cloud_pro and pro share rank 2 (Cloud Pro / Self-hosted Pro).
    out = ent.has_all_bundle_from_path_batch(
        ["pro"], "cloud_pro", {"features": ["fleet"]}
    )
    assert out["tiers"][0]["direction"] == "lateral"


# ── Grace-independence ────────────────────────────────────────────────────


def test_has_scalar_same_under_grace_and_enforce(ent, enforced):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    from_tiers = ["oss", "cloud_starter"]
    to = "enterprise"
    grace_out = ent.has_all_bundle_from_path_batch(from_tiers, to, bundle)
    enforced_out = enforced.has_all_bundle_from_path_batch(
        from_tiers, to, bundle
    )
    assert grace_out == enforced_out


# ── Complement invariant ──────────────────────────────────────────────────


def _row_has_missing(row):
    m = row.get("missing") or {}
    for v in m.values():
        if isinstance(v, list) and v:
            return True
        if isinstance(v, int) and not isinstance(v, bool):
            return True
        if v is not None and not isinstance(v, (list, int)):
            return True
    return False


def test_complement_per_source_per_rung(ent):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    from_tiers = ["oss", "cloud_starter"]
    to = "enterprise"
    hs = ent.has_all_bundle_from_path_batch(from_tiers, to, bundle)
    mi = ent.missing_all_bundle_from_path_batch(from_tiers, to, bundle)
    assert [r["from"] for r in hs["tiers"]] == [
        r["from"] for r in mi["tiers"]
    ]
    for h_row, m_row in zip(hs["tiers"], mi["tiers"]):
        assert len(h_row["path"]) == len(m_row["path"])
        for h_rung, m_rung in zip(h_row["path"], m_row["path"]):
            assert h_rung["tier"] == m_rung["tier"]
            assert h_rung["has_all_at"] is (not _row_has_missing(m_rung))


# ── Bundle normalisation posture ──────────────────────────────────────────


def test_has_scalar_none_bundle_folds_false_every_rung(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss"], "enterprise", None
    )
    assert out is not None
    for rung in out["tiers"][0]["path"]:
        assert rung["has_all_at"] is False


def test_has_scalar_non_dict_bundle_folds_false_every_rung(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss"], "enterprise", "not-a-dict"
    )
    assert out is not None
    for rung in out["tiers"][0]["path"]:
        assert rung["has_all_at"] is False


def test_has_scalar_unknown_feature_folds_false_every_rung(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss"], "enterprise", {"features": ["typo_feature"]}
    )
    assert out is not None
    for rung in out["tiers"][0]["path"]:
        assert rung["has_all_at"] is False


def test_has_scalar_runtime_alias_canonicalised(ent):
    out = ent.has_all_bundle_from_path_batch(
        ["oss"], "enterprise", {"runtimes": ["claude-code"]}
    )
    assert out is not None
    for rung in out["tiers"][0]["path"]:
        assert rung["runtimes"] == ["claude_code"]


# ── CSV ``from_tiers`` acceptance at scalar layer ─────────────────────────


def test_has_scalar_accepts_csv_from_tiers(ent):
    out = ent.has_all_bundle_from_path_batch(
        "oss,cloud_starter", "enterprise", {"features": ["fleet"]}
    )
    assert [r["from"] for r in out["tiers"]] == ["oss", "cloud_starter"]


# ── Endpoint envelope shape ───────────────────────────────────────────────


def test_endpoint_has_envelope_shape(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _HAS_ENVELOPE_KEYS
    assert j["to"] == "enterprise"
    assert j["count"] == 1
    assert len(j["tiers"]) == 1
    assert set(j["tiers"][0].keys()) == _HAS_ROW_KEYS


def test_endpoint_missing_envelope_shape(client):
    r = client.post(
        MISS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _MISSING_ENVELOPE_KEYS
    assert set(j["tiers"][0].keys()) == _MISSING_ROW_KEYS


def test_endpoint_axis_echoes_reflect_bundle(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={
            "from_tiers": ["oss"],
            "bundle": {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            },
        },
    )
    j = r.get_json()
    assert j["features"] == ["fleet"]
    assert j["runtimes"] == ["claude_code"]
    assert j["channels"] == 5
    assert j["retention_days"] == 30
    assert j["nodes"] == 2


def test_endpoint_axis_echoes_reflect_bundle_on_missing(client):
    r = client.post(
        MISS_URL + "?to=enterprise",
        json={
            "from_tiers": ["oss"],
            "bundle": {"features": ["fleet"], "channels": 5},
        },
    )
    j = r.get_json()
    assert j["features"] == ["fleet"]
    assert j["channels"] == 5


# ── Endpoint 400 branches ─────────────────────────────────────────────────


def test_endpoint_has_missing_bundle_returns_400(client):
    r = client.post(HAS_URL + "?to=cloud_pro", json={"from_tiers": ["oss"]})
    assert r.status_code == 400


def test_endpoint_has_non_dict_bundle_returns_400(client):
    r = client.post(
        HAS_URL + "?to=cloud_pro",
        json={"from_tiers": ["oss"], "bundle": "not-a-dict"},
    )
    assert r.status_code == 400


def test_endpoint_missing_missing_bundle_returns_400(client):
    r = client.post(MISS_URL + "?to=cloud_pro", json={"from_tiers": ["oss"]})
    assert r.status_code == 400


def test_endpoint_empty_body_returns_400(client):
    r = client.post(HAS_URL + "?to=cloud_pro", json={})
    assert r.status_code == 400


# ── Endpoint never-4xxs on endpoint validity ──────────────────────────────


def test_endpoint_unknown_to_returns_200_empty(client):
    r = client.post(
        HAS_URL + "?to=bogus",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["tiers"] == []
    assert j["count"] == 0


def test_endpoint_blank_to_returns_200_empty(client):
    r = client.post(
        HAS_URL,
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["tiers"] == []


def test_endpoint_empty_from_tiers_returns_200_empty(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": [], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["tiers"] == []


def test_endpoint_missing_from_tiers_returns_200_empty(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["tiers"] == []


def test_endpoint_unknown_source_echoes_unknown_tiers(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={
            "from_tiers": ["oss", "bogus"],
            "bundle": {"features": ["fleet"]},
        },
    )
    j = r.get_json()
    assert j["unknown_tiers"] == ["bogus"]
    assert [row["from"] for row in j["tiers"]] == ["oss"]


# ── Endpoint per-source rollups ──────────────────────────────────────────


def test_endpoint_has_per_source_rollups(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    j = r.get_json()
    row = j["tiers"][0]
    # fleet unlocks at Starter (rank 1) and every rung upward.
    assert row["path_length"] == len(row["path"])
    assert row["allowed_count"] == row["path_length"]
    assert row["all_allowed"] is True
    assert row["any_allowed"] is True


def test_endpoint_missing_per_source_rollups_none_denied(client):
    r = client.post(
        MISS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    j = r.get_json()
    row = j["tiers"][0]
    assert row["path_length"] == len(row["path"])
    assert row["denied_count"] == 0
    assert row["all_denied"] is False
    assert row["any_denied"] is False


def test_endpoint_missing_per_source_rollups_feature_denied(client):
    # sso stays denied at every rung below Enterprise.
    r = client.post(
        MISS_URL + "?to=cloud_pro",
        json={"from_tiers": ["oss"], "bundle": {"features": ["sso"]}},
    )
    j = r.get_json()
    row = j["tiers"][0]
    assert row["path_length"] > 0
    assert row["any_denied"] is True
    assert row["all_denied"] is True
    assert row["denied_count"] == row["path_length"]


# ── Endpoint bare-axis shorthand ─────────────────────────────────────────


def test_endpoint_bare_axis_shorthand(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "features": ["fleet"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == ["fleet"]
    assert j["tiers"][0]["from"] == "oss"


def test_endpoint_from_tiers_csv_string(client):
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={
            "from_tiers": "oss,cloud_starter",
            "bundle": {"features": ["fleet"]},
        },
    )
    j = r.get_json()
    assert [row["from"] for row in j["tiers"]] == ["oss", "cloud_starter"]


# ── Endpoint path parity with singular ───────────────────────────────────


def test_endpoint_path_parity_with_singular_has_all_bundle_at_path(
    client, ent
):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": ["oss", "cloud_starter"], "bundle": bundle},
    )
    j = r.get_json()
    for row in j["tiers"]:
        singular = ent.has_all_bundle_at_path(row["from"], "enterprise", bundle)
        assert row["path"] == singular


def test_endpoint_path_parity_with_singular_missing_all_bundle_at_path(
    client, ent
):
    bundle = {"features": ["fleet"], "channels": 5}
    r = client.post(
        MISS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": bundle},
    )
    j = r.get_json()
    for row in j["tiers"]:
        singular = ent.missing_all_bundle_at_path(
            row["from"], "enterprise", bundle
        )
        assert row["path"] == singular


# ── Endpoint fallback never-5xxs ─────────────────────────────────────────


def test_endpoint_scalar_blowup_yields_fallback(client, monkeypatch, ent):
    def _boom(*args, **kwargs):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "has_all_bundle_from_path_batch", _boom)
    r = client.post(
        HAS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _HAS_ENVELOPE_KEYS
    assert j["tiers"] == []
    assert j["count"] == 0
    assert j["unknown_tiers"] == ["oss"]


def test_endpoint_missing_scalar_blowup_yields_fallback(
    client, monkeypatch, ent
):
    def _boom(*args, **kwargs):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "missing_all_bundle_from_path_batch", _boom)
    r = client.post(
        MISS_URL + "?to=enterprise",
        json={"from_tiers": ["oss"], "bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _MISSING_ENVELOPE_KEYS
    assert j["tiers"] == []
