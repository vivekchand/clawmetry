"""Tests for the aggregate bundle-batch
``/api/entitlement/required-tier-bundle-batch`` and
``/api/entitlement/required-tier-bundle-batch-at`` endpoints (plus their
:func:`clawmetry.entitlements.min_tier_for_all_batch` /
:func:`clawmetry.entitlements.min_tier_for_all_at_batch` helpers).

Fills the bundle-axis batch slot for the aggregate 5-axis
``/api/entitlement/required-tier-batch`` singular endpoint (which folds
ONE aggregate bundle across features + runtimes + channels + retention +
nodes to ONE ``required_tier``) so a pricing-matrix or upgrade-
walkthrough surface comparing several hypothetical *whole* configs
("Starter-shaped install vs Pro-shaped install vs Enterprise-shaped
install") renders off ONE round-trip instead of N calls to
``/required-tier-batch``. Same relationship the existing
``/min-tier-for-features-batch`` has to ``/min-tier-for-features``.

These tests pin:

  * helper: per-bundle normalisation (feature/runtime CSV normalisation,
    runtime alias canonicalisation, capacity coercion, blank / non-int
    axes collapse to ``None``, empty bundle surfaces as a stable row)
  * helper: per-row parity with the singular helper
    (``min_tier_for_all_batch([b])[0]['required_tier']`` byte-equals
    ``min_tier_for_all(**b)``)
  * helper: never-crash contract on ``None`` / non-iterable / non-dict
    bundle inputs
  * helper: perspective-independence of the ``_at_batch`` variant across
    every ``p`` in ``_TIER_ORDER``
  * API happy path: shape, resolver envelope, ``count``
  * API error paths: 400 on missing / non-list / empty ``bundles``
  * API single-dict shorthand: ``{"bundles": {"features": ["fleet"]}}``
    treated as ONE bundle
  * API per-row body byte-equals the bare singular endpoint body minus
    the resolver envelope
  * API ``_at_batch`` perspective envelope keys present + 400 on missing
    ``tier=``, 404 on unknown ``tier=``
  * API never-5xxs on a delegate crash
  * grace vs enforce yields byte-identical per-row bodies
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── helper: bundle normalisation ─────────────────────────────────────────


def test_helper_batch_folds_across_all_five_axes(ent):
    rows = ent.min_tier_for_all_batch(
        [{"features": ["fleet"], "runtimes": ["claude_code"],
          "channels": 5, "retention_days": 30, "nodes": 2}]
    )
    assert len(rows) == 1
    r = rows[0]
    assert r["features"] == ["fleet"]
    assert r["runtimes"] == ["claude_code"]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2
    assert r["required_tier"] is not None
    assert r["required_tier_label"] is not None
    assert r["required_tier_rank"] >= 0
    assert isinstance(r["free"], bool)


def test_helper_batch_normalises_features_csv(ent):
    rows = ent.min_tier_for_all_batch(
        [{"features": ["FLEET", "fleet", "", "otel_export"]}]
    )
    # Whitespace stripped, lowercased, deduped preserving first-seen order.
    assert rows[0]["features"] == ["fleet", "otel_export"]


def test_helper_batch_canonicalises_runtime_aliases(ent):
    rows = ent.min_tier_for_all_batch(
        [{"runtimes": ["claude-code", "codex", "claude_code"]}]
    )
    # ``claude-code`` and ``claude_code`` collapse to one entry after
    # canonicalisation; ordering preserves first-seen.
    assert rows[0]["runtimes"] == ["claude_code", "codex"]


def test_helper_batch_capacity_coerces_ints(ent):
    rows = ent.min_tier_for_all_batch(
        [{"channels": "5", "retention_days": "30", "nodes": "2"}]
    )
    assert rows[0]["channels"] == 5
    assert rows[0]["retention_days"] == 30
    assert rows[0]["nodes"] == 2


def test_helper_batch_capacity_non_int_collapses_to_none(ent):
    """A typo on ``retention_days`` must NOT silently mis-route the
    aggregate to Enterprise -- it collapses to ``None`` (unset)."""
    rows = ent.min_tier_for_all_batch(
        [{"channels": "abc", "retention_days": "", "nodes": None}]
    )
    assert rows[0]["channels"] is None
    assert rows[0]["retention_days"] is None
    assert rows[0]["nodes"] is None


def test_helper_batch_empty_bundle_is_stable_row(ent):
    rows = ent.min_tier_for_all_batch([{}])
    assert len(rows) == 1
    r = rows[0]
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    assert r["required_tier"] is None
    assert r["required_tier_label"] is None
    assert r["required_tier_rank"] == -1
    assert r["free"] is False


def test_helper_batch_non_dict_row_collapses_to_empty_row(ent):
    """A non-dict entry in ``bundles`` must not raise -- it surfaces as
    the empty-row shape so the batch keeps building."""
    rows = ent.min_tier_for_all_batch([{"features": ["fleet"]}, "not a dict", 42])
    assert len(rows) == 3
    assert rows[0]["features"] == ["fleet"]
    # Non-dict entries collapse cleanly.
    for r in rows[1:]:
        assert r["features"] == []
        assert r["required_tier"] is None


def test_helper_batch_none_returns_empty(ent):
    assert ent.min_tier_for_all_batch(None) == []


def test_helper_batch_non_iterable_returns_empty(ent):
    assert ent.min_tier_for_all_batch(42) == []


def test_helper_batch_empty_list_returns_empty(ent):
    assert ent.min_tier_for_all_batch([]) == []


# ── helper: per-row parity with the singular helper ──────────────────────


def test_helper_batch_per_row_parity_with_singular(ent):
    """Per-row ``required_tier`` byte-equals :func:`min_tier_for_all`
    for the same bundle."""
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30, "nodes": 2},
        {"features": ["sso"]},
        {},
    ]
    rows = ent.min_tier_for_all_batch(bundles)
    for row, bundle in zip(rows, bundles):
        expected = ent.min_tier_for_all(
            features=bundle.get("features") or None,
            runtimes=bundle.get("runtimes") or None,
            channels=bundle.get("channels"),
            retention_days=bundle.get("retention_days"),
            nodes=bundle.get("nodes"),
        )
        assert row["required_tier"] == expected


# ── helper: _at_batch perspective-independence ───────────────────────────


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_helper_at_batch_perspective_independent(ent, perspective):
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ]
    assert (
        ent.min_tier_for_all_at_batch(perspective, bundles)
        == ent.min_tier_for_all_batch(bundles)
    )


def test_helper_at_batch_unknown_perspective_none(ent):
    assert ent.min_tier_for_all_at_batch("bogus", [{"features": ["fleet"]}]) is None
    assert ent.min_tier_for_all_at_batch("", [{"features": ["fleet"]}]) is None
    assert ent.min_tier_for_all_at_batch(None, [{"features": ["fleet"]}]) is None


# ── API: happy path ──────────────────────────────────────────────────────


_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "free",
}


def test_api_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
            {},
        ]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == {
        "bundles",
        "count",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _ROW_KEYS
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["runtimes"] == ["claude_code"]
    assert j["bundles"][1]["channels"] == 5
    assert j["bundles"][1]["retention_days"] == 30
    assert j["bundles"][2]["required_tier"] is None
    assert j["bundles"][2]["required_tier_rank"] == -1


def test_api_batch_single_dict_shorthand(client, ent):
    """A bare dict is treated as ONE bundle (matches the list-of-strings
    shorthand on ``/min-tier-for-features-batch``)."""
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet"]


# ── API: error paths ─────────────────────────────────────────────────────


def test_api_batch_missing_bundles_400(client):
    r = client.post("/api/entitlement/required-tier-bundle-batch", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch", json={"bundles": []}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch", json={"bundles": 42}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


# ── API: per-row body byte-equals the bare singular endpoint body ────────


def test_api_batch_row_matches_bare_singular(client, ent):
    """Each per-bundle row's ``required_tier`` byte-equals the
    ``/required-tier-batch`` singular endpoint's ``required_tier`` for
    the same bundle."""
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    batch = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    row = batch["bundles"][0]
    singular = client.get(
        "/api/entitlement/required-tier-batch"
        "?features=fleet&runtimes=claude_code"
    ).get_json()
    assert row["required_tier"] == singular["required_tier"]
    assert row["required_tier_label"] == singular["required_tier_label"]
    assert row["required_tier_rank"] == singular["required_tier_rank"]
    assert row["features"] == singular["features"]
    assert row["runtimes"] == singular["runtimes"]


# ── API: _at_batch perspective envelope ──────────────────────────────────


def test_api_at_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch-at?tier=cloud_pro",
        json={"bundles": [
            {"features": ["fleet"]},
            {"runtimes": ["claude_code"]},
        ]},
    )
    assert r.status_code == 200
    j = r.get_json()
    for k in (
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    ):
        assert k in j
    assert j["perspective_tier"] == "cloud_pro"
    assert j["count"] == 2
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][1]["runtimes"] == ["claude_code"]


def test_api_at_batch_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch-at?tier=bogus",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j["error"] == "unknown tier"
    assert j["which"] == "tier"
    assert j["tier"] == "bogus"


def test_api_at_batch_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch-at",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_at_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch-at?tier=cloud_pro",
        json={},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


# ── API: _at_batch row body byte-equals the bare batch row body ──────────


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_at_batch_row_matches_bare_batch(client, perspective):
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ]
    bare = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": bundles},
    ).get_json()
    at = client.post(
        f"/api/entitlement/required-tier-bundle-batch-at?tier={perspective}",
        json={"bundles": bundles},
    ).get_json()
    assert bare["bundles"] == at["bundles"]
    assert bare["count"] == at["count"]


# ── API: never-5xxs on a delegate crash ──────────────────────────────────


def test_api_batch_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_all_batch", _boom)
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0


def test_api_at_batch_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_all_at_batch", _boom)
    r = client.post(
        "/api/entitlement/required-tier-bundle-batch-at?tier=cloud_pro",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["perspective_tier"] == "cloud_pro"


# ── grace vs enforce parity ──────────────────────────────────────────────


def test_api_batch_grace_vs_enforce_identical(client, ent, monkeypatch):
    grace = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5},
        ]},
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5},
        ]},
    ).get_json()
    assert grace["bundles"] == enforce["bundles"]
    assert grace["count"] == enforce["count"]
