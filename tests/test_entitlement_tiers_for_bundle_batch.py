"""Tests for the bundle-batch ``/api/entitlement/tiers-for-features-batch``
and ``/api/entitlement/tiers-for-runtimes-batch`` endpoints (plus their
:func:`clawmetry.entitlements.tiers_for_features_batch` /
:func:`clawmetry.entitlements.tiers_for_runtimes_batch` helpers).

Fills the bundle-axis batch slot alongside the singular
``/tiers-for-features`` / ``/tiers-for-runtimes`` endpoints (which fold
ONE bundle to ONE ladder) so a pricing-matrix surface comparing several
hypothetical feature/runtime sets renders off ONE round-trip instead of
N calls to the singular endpoints. Same relationship the existing
``/min-tier-for-features-batch`` has to ``/min-tier-for-features``.

These tests pin:

  * helper: bundle normalisation (whitespace, lowercase, dedup preserving
    first-seen order), unknown-id bucketing, runtime alias
    canonicalisation, empty / all-unknown bundles surface as a stable row
  * helper: per-row parity with the singular helper
    (``tiers_for_features_batch([b])[0]`` byte-equals ``tiers_for_features(b)``)
  * API happy path: shape, resolver envelope, ``count``
  * API error paths: 400 on missing / non-list / empty ``bundles``
  * API per-row body byte-equals the bare singular endpoint body minus
    the resolver envelope
  * API never-5xxs on a delegate crash
  * grace vs enforce yields byte-identical per-row bodies (rows are
    perspective-independent)
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


# ── helper: features batch ────────────────────────────────────────────────


def test_helper_features_batch_returns_list(ent):
    rows = ent.tiers_for_features_batch([["fleet"], ["otel_export"]])
    assert isinstance(rows, list)
    assert len(rows) == 2


def test_helper_features_batch_row_shape(ent):
    rows = ent.tiers_for_features_batch([["fleet", "sso"]])
    row = rows[0]
    assert set(row.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert row["kind"] == "features"


def test_helper_features_batch_dedups_and_lowers(ent):
    """Delegates to :func:`tiers_for_features` per bundle, so normalisation
    matches the singular helper byte-for-byte: whitespace stripped,
    lowercased, deduplicated preserving first-seen order."""
    rows = ent.tiers_for_features_batch(
        [["fleet", "SSO", "fleet"], ["otel_export"]]
    )
    assert rows[0]["items"] == ["fleet", "sso"]
    assert rows[0]["count"] == 2
    assert rows[1]["items"] == ["otel_export"]


def test_helper_features_batch_buckets_unknown(ent):
    rows = ent.tiers_for_features_batch([["fleet", "bogus"]])
    assert rows[0]["items"] == ["fleet"]
    assert rows[0]["unknown"] == ["bogus"]
    # Unknown does NOT mis-route the ladder to a higher tier.
    assert rows[0]["min_tier"] == ent.min_tier_for_features(["fleet"])


def test_helper_features_batch_empty_bundle_is_stable_row(ent):
    rows = ent.tiers_for_features_batch([[]])
    assert len(rows) == 1
    assert rows[0]["items"] == []
    assert rows[0]["unknown"] == []
    assert rows[0]["count"] == 0
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


def test_helper_features_batch_all_unknown_is_stable_row(ent):
    rows = ent.tiers_for_features_batch([["bogus", "also-bogus"]])
    assert rows[0]["items"] == []
    # Bare hyphen ids get lowercased but the raw string still lands.
    assert set(rows[0]["unknown"]) == {"bogus", "also-bogus"}
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


def test_helper_features_batch_none_bundles_is_empty(ent):
    assert ent.tiers_for_features_batch(None) == []


def test_helper_features_batch_non_iterable_is_empty(ent):
    assert ent.tiers_for_features_batch(123) == []


def test_helper_features_batch_none_per_bundle_is_stable_row(ent):
    rows = ent.tiers_for_features_batch([None, ["fleet"]])
    assert len(rows) == 2
    assert rows[0]["items"] == []
    assert rows[0]["count"] == 0
    assert rows[0]["tiers"] == []
    assert rows[1]["items"] == ["fleet"]


def test_helper_features_batch_row_equals_singular(ent):
    for bundle in (["fleet", "sso"], ["otel_export"], ["fleet", "bogus"], []):
        rows = ent.tiers_for_features_batch([bundle])
        assert rows[0] == ent.tiers_for_features(bundle)


def test_helper_features_batch_free_bundle_covers_all_tiers(ent):
    # A bundle of only free features must be available at every tier.
    free_ids = list(sorted(ent.FREE_FEATURES))[:2]
    rows = ent.tiers_for_features_batch([free_ids])
    tier_ids = {t["id"] for t in rows[0]["tiers"]}
    assert tier_ids == set(ent._TIER_ORDER)
    assert rows[0]["min_tier"] == ent.TIER_OSS


# ── helper: runtimes batch ────────────────────────────────────────────────


def test_helper_runtimes_batch_row_shape(ent):
    rows = ent.tiers_for_runtimes_batch([["openclaw"]])
    assert set(rows[0].keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert rows[0]["kind"] == "runtimes"


def test_helper_runtimes_batch_canonicalises_alias(ent):
    # ``claude-code`` (hyphen) should canonicalise to ``claude_code``.
    rows = ent.tiers_for_runtimes_batch([["claude-code"]])
    assert rows[0]["items"] == ["claude_code"]
    assert rows[0]["unknown"] == []


def test_helper_runtimes_batch_row_equals_singular(ent):
    for bundle in (["openclaw"], ["claude_code", "codex"], ["bogus"], []):
        rows = ent.tiers_for_runtimes_batch([bundle])
        assert rows[0] == ent.tiers_for_runtimes(bundle)


def test_helper_runtimes_batch_free_runtimes_appear_everywhere(ent):
    rows = ent.tiers_for_runtimes_batch([list(sorted(ent.FREE_RUNTIMES))])
    tier_ids = {t["id"] for t in rows[0]["tiers"]}
    assert tier_ids == set(ent._TIER_ORDER)


def test_helper_runtimes_batch_paid_runtimes_skip_floor(ent):
    paid = list(sorted(ent.PAID_RUNTIMES))[:1]
    rows = ent.tiers_for_runtimes_batch([paid])
    tier_ids = {t["id"] for t in rows[0]["tiers"]}
    assert ent.TIER_OSS not in tier_ids
    assert ent.TIER_CLOUD_FREE not in tier_ids


def test_helper_runtimes_batch_none_bundles_is_empty(ent):
    assert ent.tiers_for_runtimes_batch(None) == []


def test_helper_runtimes_batch_non_iterable_is_empty(ent):
    assert ent.tiers_for_runtimes_batch(42) == []


# ── perspective independence ─────────────────────────────────────────────


def test_helper_features_batch_grace_vs_enforce_same_rows(monkeypatch, ent):
    """Rows are decoupled from the resolved entitlement -- they walk the
    static per-tier feature map, not the caller's tier. Flipping enforce
    on must yield byte-identical rows."""
    grace_rows = ent.tiers_for_features_batch(
        [["fleet", "sso"], ["otel_export"], []]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_rows = ent.tiers_for_features_batch(
        [["fleet", "sso"], ["otel_export"], []]
    )
    assert grace_rows == enforce_rows


# ── API: features batch ──────────────────────────────────────────────────


def test_api_features_batch_happy_path(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": [["fleet", "sso"], ["otel_export"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= {
        "bundles",
        "count",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert body["count"] == 2
    assert len(body["bundles"]) == 2
    assert body["bundles"][0]["kind"] == "features"


def test_api_features_batch_row_shape(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": [["fleet", "sso"]]},
    )
    row = r.get_json()["bundles"][0]
    assert set(row.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }


def test_api_features_batch_row_byte_equals_helper(client, ent):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": bundles},
    )
    body = r.get_json()
    for row, bundle in zip(body["bundles"], bundles):
        assert row == ent.tiers_for_features(bundle)


def test_api_features_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={},
    )
    assert r.status_code == 400
    assert "bundles" in r.get_json()["error"]


def test_api_features_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert "empty" in r.get_json()["error"]


def test_api_features_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": "fleet,sso"},
    )
    assert r.status_code == 400


def test_api_features_batch_bare_list_of_strings_is_one_bundle(client):
    """The bundles-shorthand documented on the endpoint: a bare list of
    strings is treated as ONE bundle."""
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 1
    assert body["bundles"][0]["items"] == ["fleet", "sso"]


def test_api_features_batch_never_5xxs_on_delegate_crash(client, monkeypatch, ent):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(ent, "tiers_for_features_batch", _boom)
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0
    assert body["grace"] is True


def test_api_features_batch_all_unknown_row_still_populates(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": [["bogus"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    row = body["bundles"][0]
    assert row["items"] == []
    assert row["unknown"] == ["bogus"]
    assert row["min_tier"] is None
    assert row["tiers"] == []


# ── API: runtimes batch ──────────────────────────────────────────────────


def test_api_runtimes_batch_happy_path(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": [["claude_code", "codex"], ["openclaw"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert body["bundles"][0]["kind"] == "runtimes"


def test_api_runtimes_batch_row_byte_equals_helper(client, ent):
    bundles = [["claude_code", "codex"], ["openclaw"], []]
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": bundles},
    )
    body = r.get_json()
    for row, bundle in zip(body["bundles"], bundles):
        assert row == ent.tiers_for_runtimes(bundle)


def test_api_runtimes_batch_canonicalises_alias(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": [["claude-code"]]},
    )
    body = r.get_json()
    assert body["bundles"][0]["items"] == ["claude_code"]


def test_api_runtimes_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={},
    )
    assert r.status_code == 400


def test_api_runtimes_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400


def test_api_runtimes_batch_never_5xxs_on_delegate_crash(client, monkeypatch, ent):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(ent, "tiers_for_runtimes_batch", _boom)
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0


# ── envelope parity ──────────────────────────────────────────────────────


def test_api_batch_envelope_matches_resolver(client, ent):
    r = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": [["fleet"]]},
    )
    body = r.get_json()
    ent_obj = ent.get_entitlement()
    assert body["current_tier"] == ent_obj.tier
    assert body["current_tier_rank"] == ent.tier_rank(ent_obj.tier)
    assert body["grace"] is bool(ent_obj.grace)
    assert body["enforced"] is ent.is_enforced()
