"""Tests for ``clawmetry.entitlements.tiers_for_features`` /
``tiers_for_runtimes`` + the matching HTTP wrappers
``GET /api/entitlement/tiers-for-features`` /
``GET /api/entitlement/tiers-for-runtimes``.

Ladder-intersection sibling of :func:`min_tier_for_features` /
:func:`min_tier_for_runtimes`: where the ``min_tier_for_*`` plurals
collapse a caller-supplied bundle to a single ``min_tier`` id, the
``tiers_for_*`` plurals return the *full* ladder of tiers that grant
every supplied item at once. Closes the ``tiers_for_*`` symmetry gap
alongside the singular / fixed-batch siblings.

These tests pin:

* the intersection ladder matches the singular ``tiers_for_*`` grant
  sets (set-intersection is the answer)
* ``min_tier`` matches the existing ``min_tier_for_features`` /
  ``min_tier_for_runtimes`` helpers byte-for-byte (consistency
  invariant)
* unknown ids never mis-route the ladder to Enterprise -- they land in
  ``unknown`` and drop from the intersection
* runtime aliases (``claude-code`` -> ``claude_code``) canonicalise
* the endpoints reject missing/blank ``features=`` / ``runtimes=``
  cleanly and never 5xx
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


# ── shape ─────────────────────────────────────────────────────────────────


def test_features_returns_full_shape(ent):
    body = ent.tiers_for_features(["fleet", "sso"])
    assert body is not None
    assert set(body.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "features"


def test_runtimes_returns_full_shape(ent):
    body = ent.tiers_for_runtimes(["claude_code", "codex"])
    assert body is not None
    assert set(body.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "runtimes"


def test_tier_rows_have_expected_keys(ent):
    body = ent.tiers_for_features(["fleet"])
    assert body["tiers"], "paid feature must list at least one tier"
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}


def test_tier_rows_sorted_by_rank_then_id(ent):
    body = ent.tiers_for_features(["fleet"])
    ranks = [(r["rank"], r["id"]) for r in body["tiers"]]
    assert ranks == sorted(ranks)


# ── intersection semantics ────────────────────────────────────────────────


def test_features_ladder_is_intersection_of_singular_rows(ent):
    ids = ["fleet", "self_evolve"]
    body = ent.tiers_for_features(ids)
    common = None
    for fid in ids:
        s = {row["id"] for row in ent.tiers_for_feature(fid)["tiers"]}
        common = s if common is None else common & s
    assert {row["id"] for row in body["tiers"]} == common


def test_runtimes_ladder_is_intersection_of_singular_rows(ent):
    ids = ["claude_code", "codex", "openclaw"]
    body = ent.tiers_for_runtimes(ids)
    common = None
    for rid in ids:
        s = {row["id"] for row in ent.tiers_for_runtime(rid)["tiers"]}
        common = s if common is None else common & s
    assert {row["id"] for row in body["tiers"]} == common


def test_single_feature_ladder_matches_singular(ent):
    body = ent.tiers_for_features(["fleet"])
    singular = ent.tiers_for_feature("fleet")
    assert {r["id"] for r in body["tiers"]} == {
        r["id"] for r in singular["tiers"]
    }


def test_single_runtime_ladder_matches_singular(ent):
    body = ent.tiers_for_runtimes(["claude_code"])
    singular = ent.tiers_for_runtime("claude_code")
    assert {r["id"] for r in body["tiers"]} == {
        r["id"] for r in singular["tiers"]
    }


# ── min_tier consistency ──────────────────────────────────────────────────


def test_min_tier_matches_min_tier_for_features(ent):
    inputs = [
        ["fleet"],
        ["fleet", "self_evolve"],
        ["fleet", "self_evolve", "sso"],
        ["sessions"],  # all free
        ["sessions", "fleet"],  # mixed free + paid
    ]
    for bundle in inputs:
        body = ent.tiers_for_features(bundle)
        assert body["min_tier"] == ent.min_tier_for_features(bundle), bundle


def test_min_tier_matches_min_tier_for_runtimes(ent):
    inputs = [
        ["openclaw"],
        ["claude_code"],
        ["claude_code", "codex"],
        ["openclaw", "claude_code"],  # mixed free + paid
    ]
    for bundle in inputs:
        body = ent.tiers_for_runtimes(bundle)
        assert body["min_tier"] == ent.min_tier_for_runtimes(bundle), bundle


# ── all-free bundles ──────────────────────────────────────────────────────


def test_all_free_features_intersect_to_every_tier(ent):
    body = ent.tiers_for_features(["sessions"])
    assert body["min_tier"] == ent.TIER_OSS
    assert {r["id"] for r in body["tiers"]} == set(ent._TIER_ORDER)


def test_all_free_runtimes_intersect_to_every_tier(ent):
    body = ent.tiers_for_runtimes(["openclaw", "nemoclaw"])
    assert body["min_tier"] == ent.TIER_OSS
    assert {r["id"] for r in body["tiers"]} == set(ent._TIER_ORDER)


# ── enterprise-only feature narrows the intersection ──────────────────────


def test_enterprise_feature_narrows_intersection_to_enterprise(ent):
    body = ent.tiers_for_features(["fleet", "sso"])
    # ``sso`` is enterprise-only -> the intersection collapses to
    # {enterprise} regardless of what other paid features are stacked in.
    assert {r["id"] for r in body["tiers"]} == {ent.TIER_ENTERPRISE}
    assert body["min_tier"] == ent.TIER_ENTERPRISE


# ── input handling: unknown / dedup / alias ───────────────────────────────


def test_unknown_feature_lands_in_unknown_and_drops_from_intersection(ent):
    body = ent.tiers_for_features(["fleet", "bogus"])
    assert "bogus" in body["unknown"]
    assert body["items"] == ["fleet"]
    # unknown must NOT mis-route the ladder to Enterprise
    assert body["min_tier"] == ent.min_tier_for_feature("fleet")


def test_unknown_runtime_lands_in_unknown_and_drops_from_intersection(ent):
    body = ent.tiers_for_runtimes(["claude_code", "not_a_runtime"])
    assert "not_a_runtime" in body["unknown"]
    assert body["items"] == ["claude_code"]
    assert body["min_tier"] == ent.min_tier_for_runtime("claude_code")


def test_all_unknown_features_returns_empty_shape(ent):
    body = ent.tiers_for_features(["nope1", "nope2"])
    assert body["items"] == []
    assert body["unknown"] == ["nope1", "nope2"]
    assert body["tiers"] == []
    assert body["min_tier"] is None
    assert body["count"] == 0


def test_all_unknown_runtimes_returns_empty_shape(ent):
    body = ent.tiers_for_runtimes(["nope1", "nope2"])
    assert body["items"] == []
    assert body["unknown"] == ["nope1", "nope2"]
    assert body["tiers"] == []
    assert body["min_tier"] is None
    assert body["count"] == 0


def test_features_dedup_preserves_first_seen_order(ent):
    body = ent.tiers_for_features(["fleet", "self_evolve", "fleet"])
    assert body["items"] == ["fleet", "self_evolve"]


def test_runtimes_dedup_preserves_first_seen_order(ent):
    body = ent.tiers_for_runtimes(["claude_code", "codex", "claude_code"])
    assert body["items"] == ["claude_code", "codex"]


def test_runtime_alias_canonicalises(ent):
    body = ent.tiers_for_runtimes(["claude-code"])
    assert body["items"] == ["claude_code"]
    # min_tier matches the canonical singular
    assert body["min_tier"] == ent.min_tier_for_runtime("claude_code")


def test_features_case_and_whitespace_normalised(ent):
    body = ent.tiers_for_features(["  FLEET  ", "Self_Evolve"])
    assert body["items"] == ["fleet", "self_evolve"]


# ── safety: never raise, well-defined None/empty ──────────────────────────


def test_features_none_returns_none(ent):
    assert ent.tiers_for_features(None) is None


def test_runtimes_none_returns_none(ent):
    assert ent.tiers_for_runtimes(None) is None


def test_features_non_iterable_returns_none(ent):
    assert ent.tiers_for_features(42) is None  # type: ignore[arg-type]


def test_runtimes_non_iterable_returns_none(ent):
    assert ent.tiers_for_runtimes(42) is None  # type: ignore[arg-type]


def test_features_empty_returns_empty_shape(ent):
    body = ent.tiers_for_features([])
    assert body is not None
    assert body["items"] == []
    assert body["tiers"] == []
    assert body["min_tier"] is None
    assert body["count"] == 0


def test_runtimes_empty_returns_empty_shape(ent):
    body = ent.tiers_for_runtimes([])
    assert body is not None
    assert body["items"] == []
    assert body["tiers"] == []
    assert body["min_tier"] is None
    assert body["count"] == 0


def test_features_non_string_tokens_land_in_unknown(ent):
    body = ent.tiers_for_features([None, 42, "fleet"])  # type: ignore[list-item]
    assert body["items"] == ["fleet"]
    # Non-string tokens count as unknown but never crash.
    assert len(body["unknown"]) == 2


# ── grace vs enforce (rows are perspective-independent) ───────────────────


def test_grace_vs_enforce_ladder_is_identical(ent, monkeypatch):
    body_grace = ent.tiers_for_features(["fleet", "self_evolve"])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    body_enforce = ent.tiers_for_features(["fleet", "self_evolve"])
    assert body_grace == body_enforce


# ── does not mutate the live entitlement ──────────────────────────────────


def test_call_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().tier
    ent.tiers_for_features(["fleet", "sso"])
    ent.tiers_for_runtimes(["claude_code", "codex"])
    after = ent.get_entitlement().tier
    assert before == after


# ── API: happy path ───────────────────────────────────────────────────────


def _envelope_keys():
    return {"current_tier", "current_tier_rank", "grace", "enforced"}


def _body_keys():
    return {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }


def test_features_api_happy_path(client):
    r = client.get("/api/entitlement/tiers-for-features?features=fleet,sso")
    assert r.status_code == 200
    data = r.get_json()
    assert set(data.keys()) == _body_keys() | _envelope_keys()
    assert data["items"] == ["fleet", "sso"]
    assert data["kind"] == "features"
    # sso is enterprise-only -> intersection collapses to {enterprise}
    assert {row["id"] for row in data["tiers"]} == {"enterprise"}


def test_runtimes_api_happy_path(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude_code,codex"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert set(data.keys()) == _body_keys() | _envelope_keys()
    assert data["items"] == ["claude_code", "codex"]
    assert data["kind"] == "runtimes"


def test_features_api_alias_and_case(client):
    r = client.get(
        "/api/entitlement/tiers-for-features?features=%20FLEET%20,Self_Evolve"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["items"] == ["fleet", "self_evolve"]


def test_runtimes_api_alias(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude-code"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["items"] == ["claude_code"]


def test_features_api_dedup(client):
    r = client.get(
        "/api/entitlement/tiers-for-features?features=fleet,fleet,self_evolve"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["items"] == ["fleet", "self_evolve"]


# ── API: error paths ─────────────────────────────────────────────────────


def test_features_api_missing_400(client):
    r = client.get("/api/entitlement/tiers-for-features")
    assert r.status_code == 400
    assert "features" in r.get_json().get("error", "").lower()


def test_features_api_blank_400(client):
    r = client.get("/api/entitlement/tiers-for-features?features=%20%20")
    assert r.status_code == 400


def test_runtimes_api_missing_400(client):
    r = client.get("/api/entitlement/tiers-for-runtimes")
    assert r.status_code == 400
    assert "runtimes" in r.get_json().get("error", "").lower()


def test_runtimes_api_blank_400(client):
    r = client.get("/api/entitlement/tiers-for-runtimes?runtimes=%20%20")
    assert r.status_code == 400


# ── API: all-unknown IS 200 (echo the unknown list) ──────────────────────


def test_features_api_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/tiers-for-features?features=bogus1,bogus2"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["items"] == []
    assert set(data["unknown"]) == {"bogus1", "bogus2"}
    assert data["tiers"] == []
    assert data["min_tier"] is None


def test_runtimes_api_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=bogus1,bogus2"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["items"] == []
    assert set(data["unknown"]) == {"bogus1", "bogus2"}
    assert data["tiers"] == []
    assert data["min_tier"] is None


# ── API: min_tier parity with /required-tier-batch ───────────────────────


def test_features_api_min_tier_matches_required_tier_batch(client):
    a = client.get("/api/entitlement/tiers-for-features?features=fleet,sso")
    b = client.get(
        "/api/entitlement/required-tier-batch?features=fleet,sso"
    )
    assert a.status_code == 200 and b.status_code == 200
    assert a.get_json()["min_tier"] == b.get_json()["required_tier"]


def test_runtimes_api_min_tier_matches_required_tier_batch(client):
    a = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude_code,codex"
    )
    b = client.get(
        "/api/entitlement/required-tier-batch?runtimes=claude_code,codex"
    )
    assert a.status_code == 200 and b.status_code == 200
    assert a.get_json()["min_tier"] == b.get_json()["required_tier"]


# ── API: envelope shape ──────────────────────────────────────────────────


def test_envelope_present_on_features_endpoint(client):
    r = client.get("/api/entitlement/tiers-for-features?features=fleet")
    assert r.status_code == 200
    data = r.get_json()
    assert data["current_tier"] == "oss"
    assert data["current_tier_rank"] == 0
    assert data["grace"] is True


def test_envelope_present_on_runtimes_endpoint(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude_code"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["current_tier"] == "oss"
    assert data["current_tier_rank"] == 0
    assert data["grace"] is True


# ── cross-endpoint parity: singular vs plural for a one-item bundle ──────


def test_features_singleton_parity_with_singular_endpoint(client):
    plural = client.get(
        "/api/entitlement/tiers-for-features?features=fleet"
    ).get_json()
    singular = client.get(
        "/api/entitlement/tiers-for?feature=fleet"
    ).get_json()
    assert {r["id"] for r in plural["tiers"]} == {
        r["id"] for r in singular["tiers"]
    }
    assert plural["min_tier"] == singular["min_tier"]


def test_runtimes_singleton_parity_with_singular_endpoint(client):
    plural = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude_code"
    ).get_json()
    singular = client.get(
        "/api/entitlement/tiers-for?runtime=claude_code"
    ).get_json()
    assert {r["id"] for r in plural["tiers"]} == {
        r["id"] for r in singular["tiers"]
    }
    assert plural["min_tier"] == singular["min_tier"]
