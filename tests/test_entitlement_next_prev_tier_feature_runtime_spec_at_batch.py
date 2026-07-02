"""Tests for the four batch siblings of
:func:`clawmetry.entitlements.next_tier_feature_spec_at` /
:func:`previous_tier_feature_spec_at` /
:func:`next_tier_runtime_spec_at` /
:func:`previous_tier_runtime_spec_at`, and the four companion
``/api/entitlement/{next,previous}-tier-{feature,runtime}-spec-at-batch``
endpoints.

Where the scalar projections walk ONE feature/runtime onto the rung
above/below a source tier, the batch siblings walk N items onto that
same rung in ONE round-trip. They compose:

* :func:`next_tier_feature_spec_at` (scalar projection) +
  :func:`feature_spec_at_batch` (batch what-if) ->
  :func:`next_tier_feature_spec_at_batch`

* :func:`feature_spec_path_batch` (batch path) ->
  :func:`next_tier_feature_spec_at_batch` (batch what-if)

Pins covered here:

* per-row byte-equality with the scalar sibling for every valid
  (source, item) pair across every purchasable source tier (parity)
* item-agnostic target resolution: every per-item row resolves
  ``feature_spec_at(target, item)`` (or ``None`` at ceiling/floor)
* ceiling (enterprise as source for ``next_*``) / floor
  (``oss`` / ``cloud_free`` as source for ``previous_*``) yields
  ``row=None`` for every valid item -- envelope rows still render
* trial-as-source resolves the same way the sibling ``_at`` families do
  (next -> enterprise, previous -> cloud_starter)
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``) on
  helper and API, alias-to-canonical collapse de-duplicates
* unknown ids echo into ``unknown[]`` (carrying the supplied alias for
  the runtime axis, the lowercased id for the feature axis) rather
  than 404'ing the call
* normalisation is whitespace-stripped, lowercased, first-seen order
  preserved, duplicate-dropped (matches ``_normalise_csv``)
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a per-row builder failure short-circuits
  that row into ``unknown[]`` rather than 500-ing
* the four API endpoints never 5xx: 400 on missing input, 404 on
  unknown tier, 200 with ``row=null`` rows at ceiling/floor; an
  internal failure yields the same 200 envelope shape
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_FEATURE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
    "unknown",
}

_ENVELOPE_RUNTIME_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
    "unknown",
}


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


# ── next_tier_feature_spec_at_batch (helper) ─────────────────────────────────


def test_next_feature_batch_row_byte_equals_scalar(ent):
    # Per-row body equals next_tier_feature_spec_at(src, feature) byte-for-byte
    # across every purchasable source for every feature. Pins so the batch
    # accessor cannot drift from the scalar projection.
    feats = sorted(ent.ALL_FEATURES)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.next_tier_feature_spec_at_batch(src, feats)
        assert body is not None
        assert body["unknown"] == []
        for row in body["features"]:
            assert row["row"] == ent.next_tier_feature_spec_at(src, row["feature"])


def test_next_feature_batch_returns_row_null_at_ceiling(ent):
    # Enterprise is the top of the purchasable ladder -- no rung above. Every
    # valid feature must surface as a row with row=None so the matrix's row
    # count stays stable (the surface can still render "you're at the top").
    feats = sorted(ent.ALL_FEATURES)
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_ENTERPRISE, feats)
    assert body is not None
    assert body["unknown"] == []
    assert [r["feature"] for r in body["features"]] == feats
    assert all(r["row"] is None for r in body["features"])


def test_next_feature_batch_trial_resolves_to_enterprise(ent):
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_TRIAL, ["custom_alerts"])
    assert body is not None
    assert body["features"] == [
        {
            "feature": "custom_alerts",
            "row": ent.feature_spec_at(ent.TIER_ENTERPRISE, "custom_alerts"),
        }
    ]


def test_next_feature_batch_unknown_inputs_short_circuit(ent):
    # Empty / None / unknown tier -> helper returns None (HTTP wrapper turns
    # into 400 / 404). Unknown feature ids are bucketed into unknown[].
    assert ent.next_tier_feature_spec_at_batch("", ["custom_alerts"]) is None
    assert ent.next_tier_feature_spec_at_batch(None, ["custom_alerts"]) is None
    assert ent.next_tier_feature_spec_at_batch("bogus", ["custom_alerts"]) is None
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_CLOUD_STARTER, ["custom_alerts", "no_such", "also_bogus"]
    )
    assert body is not None
    assert [r["feature"] for r in body["features"]] == ["custom_alerts"]
    assert body["unknown"] == ["no_such", "also_bogus"]


def test_next_feature_batch_normalises_input(ent):
    # Whitespace stripped, lowercased, duplicates dropped, first-seen order
    # preserved -- matches _normalise_csv.
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_CLOUD_STARTER,
        [" CUSTOM_ALERTS ", "custom_alerts", "", "CUSTOM_ALERTS"],
    )
    assert body is not None
    assert [r["feature"] for r in body["features"]] == ["custom_alerts"]
    assert body["unknown"] == []


def test_next_feature_batch_empty_features_returns_empty_rows(ent):
    # An empty caller-supplied list returns {features: [], unknown: []} --
    # the HTTP layer turns that into a 400, the helper itself does not raise.
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_CLOUD_STARTER, [])
    assert body == {"features": [], "unknown": []}


def test_next_feature_batch_grace_and_enforce_match(ent, monkeypatch):
    feats = sorted(ent.ALL_FEATURES)
    grace = ent.next_tier_feature_spec_at_batch(ent.TIER_CLOUD_STARTER, feats)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_feature_spec_at_batch(ent.TIER_CLOUD_STARTER, feats)
    assert enforce == grace


def test_next_feature_batch_row_failure_buckets_into_unknown(ent, monkeypatch):
    # A synthesised failure in feature_spec_at short-circuits that row into
    # unknown[] and the rest of the batch keeps building.
    real_spec_at = ent.feature_spec_at

    def fake_spec_at(tier, feature):
        if feature == "custom_alerts":
            raise RuntimeError("synthetic")
        return real_spec_at(tier, feature)

    monkeypatch.setattr(ent, "feature_spec_at", fake_spec_at)
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_CLOUD_STARTER, ["custom_alerts", "sso"]
    )
    assert body is not None
    assert [r["feature"] for r in body["features"]] == ["sso"]
    assert body["unknown"] == ["custom_alerts"]


# ── previous_tier_feature_spec_at_batch (helper) ─────────────────────────────


def test_previous_feature_batch_row_byte_equals_scalar(ent):
    feats = sorted(ent.ALL_FEATURES)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.previous_tier_feature_spec_at_batch(src, feats)
        assert body is not None
        for row in body["features"]:
            assert row["row"] == ent.previous_tier_feature_spec_at(
                src, row["feature"]
            )


def test_previous_feature_batch_returns_row_null_at_floor(ent):
    feats = sorted(ent.ALL_FEATURES)
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        body = ent.previous_tier_feature_spec_at_batch(src, feats)
        assert body is not None
        assert [r["feature"] for r in body["features"]] == feats
        assert all(r["row"] is None for r in body["features"])


def test_previous_feature_batch_trial_resolves_to_starter(ent):
    body = ent.previous_tier_feature_spec_at_batch(
        ent.TIER_TRIAL, ["custom_alerts"]
    )
    assert body is not None
    assert body["features"] == [
        {
            "feature": "custom_alerts",
            "row": ent.feature_spec_at(ent.TIER_CLOUD_STARTER, "custom_alerts"),
        }
    ]


def test_previous_feature_batch_unknown_inputs_short_circuit(ent):
    assert (
        ent.previous_tier_feature_spec_at_batch("", ["custom_alerts"]) is None
    )
    assert (
        ent.previous_tier_feature_spec_at_batch("bogus", ["custom_alerts"])
        is None
    )
    body = ent.previous_tier_feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["custom_alerts", "no_such"]
    )
    assert body is not None
    assert [r["feature"] for r in body["features"]] == ["custom_alerts"]
    assert body["unknown"] == ["no_such"]


# ── next_tier_runtime_spec_at_batch (helper) ─────────────────────────────────


def test_next_runtime_batch_row_byte_equals_scalar(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.next_tier_runtime_spec_at_batch(src, rts)
        assert body is not None
        assert body["unknown"] == []
        for row in body["runtimes"]:
            assert row["row"] == ent.next_tier_runtime_spec_at(src, row["runtime"])


def test_next_runtime_batch_returns_row_null_at_ceiling(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    body = ent.next_tier_runtime_spec_at_batch(ent.TIER_ENTERPRISE, rts)
    assert body is not None
    assert [r["runtime"] for r in body["runtimes"]] == rts
    assert all(r["row"] is None for r in body["runtimes"])


def test_next_runtime_batch_alias_canonicalises(ent):
    # ``claude-code`` aliases to ``claude_code``; per-row ``runtime`` carries
    # the canonical id and supplying both spellings collapses to ONE row.
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_CLOUD_STARTER, ["claude-code", "CLAUDE_CODE", " claude_code "]
    )
    assert body is not None
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]
    assert body["runtimes"][0]["row"] == ent.runtime_spec_at(
        ent.TIER_CLOUD_PRO, "claude_code"
    )


def test_next_runtime_batch_unknown_alias_bucketed_with_supplied_value(ent):
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_CLOUD_STARTER, ["claude_code", "bogus-runtime"]
    )
    assert body is not None
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]
    # ``_normalise_csv`` lower-cases its input before the helper sees it, so the
    # alias surfaces in ``unknown[]`` as the lowercased form, matching the
    # ``runtime_spec_at_batch`` posture.
    assert body["unknown"] == ["bogus-runtime"]


def test_next_runtime_batch_unknown_tier_returns_none(ent):
    assert ent.next_tier_runtime_spec_at_batch("", ["claude_code"]) is None
    assert ent.next_tier_runtime_spec_at_batch("bogus", ["claude_code"]) is None


def test_next_runtime_batch_grace_and_enforce_match(ent, monkeypatch):
    rts = sorted(ent.ALL_RUNTIMES)
    grace = ent.next_tier_runtime_spec_at_batch(ent.TIER_CLOUD_STARTER, rts)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_runtime_spec_at_batch(ent.TIER_CLOUD_STARTER, rts)
    assert enforce == grace


def test_next_runtime_batch_row_failure_buckets_into_unknown(ent, monkeypatch):
    real_spec_at = ent.runtime_spec_at

    def fake_spec_at(tier, runtime):
        if runtime == "claude_code":
            raise RuntimeError("synthetic")
        return real_spec_at(tier, runtime)

    monkeypatch.setattr(ent, "runtime_spec_at", fake_spec_at)
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_CLOUD_STARTER, ["claude_code", "openclaw"]
    )
    assert body is not None
    assert [r["runtime"] for r in body["runtimes"]] == ["openclaw"]
    assert body["unknown"] == ["claude_code"]


# ── previous_tier_runtime_spec_at_batch (helper) ─────────────────────────────


def test_previous_runtime_batch_row_byte_equals_scalar(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.previous_tier_runtime_spec_at_batch(src, rts)
        assert body is not None
        for row in body["runtimes"]:
            assert row["row"] == ent.previous_tier_runtime_spec_at(
                src, row["runtime"]
            )


def test_previous_runtime_batch_returns_row_null_at_floor(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        body = ent.previous_tier_runtime_spec_at_batch(src, rts)
        assert body is not None
        assert [r["runtime"] for r in body["runtimes"]] == rts
        assert all(r["row"] is None for r in body["runtimes"])


def test_previous_runtime_batch_alias_canonicalises(ent):
    body = ent.previous_tier_runtime_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["claude-code", "claude_code"]
    )
    assert body is not None
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]


# ── /api/entitlement/next-tier-feature-spec-at-batch ─────────────────────────


def test_api_next_feature_batch_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=cloud_starter&features=custom_alerts,sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_FEATURE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    # Every per-feature row matches the scalar /next-tier-feature-spec-at .row
    for row in body["features"]:
        scalar = client.get(
            f"/api/entitlement/next-tier-feature-spec-at"
            f"?tier=cloud_starter&feature={row['feature']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_next_feature_batch_at_ceiling_returns_200_with_null_rows(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=enterprise&features=custom_alerts,sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert [r["feature"] for r in body["features"]] == ["custom_alerts", "sso"]
    assert all(r["row"] is None for r in body["features"])


def test_api_next_feature_batch_400_missing_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch?features=custom_alerts"
    )
    assert resp.status_code == 400


def test_api_next_feature_batch_400_missing_features(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch?tier=cloud_starter"
    )
    assert resp.status_code == 400


def test_api_next_feature_batch_400_empty_features(client):
    # ``features=,,,`` normalises to an empty list -> 400.
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch?tier=cloud_starter&features=,,,"
    )
    assert resp.status_code == 400


def test_api_next_feature_batch_404_unknown_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=bogus&features=custom_alerts"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"


def test_api_next_feature_batch_unknown_feature_bucketed_200(client, ent):
    # An unknown feature does not 404 the call -- it lands in unknown[].
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=cloud_starter&features=custom_alerts,no_such"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["feature"] for r in body["features"]] == ["custom_alerts"]
    assert body["unknown"] == ["no_such"]


def test_api_next_feature_batch_normalises_query_arg(client, ent):
    # Whitespace + uppercase + duplicate dropping happens at the route layer
    # via _parse_csv_arg before the helper sees the list.
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=cloud_starter&features= CUSTOM_ALERTS ,custom_alerts,SSO"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["feature"] for r in body["features"]] == ["custom_alerts", "sso"]


# ── /api/entitlement/previous-tier-feature-spec-at-batch ─────────────────────


def test_api_previous_feature_batch_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-spec-at-batch"
        "?tier=cloud_pro&features=custom_alerts,sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_FEATURE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER
    for row in body["features"]:
        scalar = client.get(
            f"/api/entitlement/previous-tier-feature-spec-at"
            f"?tier=cloud_pro&feature={row['feature']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_previous_feature_batch_at_floor_returns_200_with_null_rows(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-feature-spec-at-batch"
            f"?tier={src}&features=custom_alerts,sso"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert all(r["row"] is None for r in body["features"])


def test_api_previous_feature_batch_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at-batch?features=custom_alerts"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at-batch?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at-batch?tier=bogus&features=custom_alerts"
        ).status_code
        == 404
    )


# ── /api/entitlement/next-tier-runtime-spec-at-batch ─────────────────────────


def test_api_next_runtime_batch_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=cloud_starter&runtimes=claude_code,openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_RUNTIME_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["target"] == ent.TIER_CLOUD_PRO
    for row in body["runtimes"]:
        scalar = client.get(
            f"/api/entitlement/next-tier-runtime-spec-at"
            f"?tier=cloud_starter&runtime={row['runtime']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_next_runtime_batch_alias_normalises_and_collapses(client, ent):
    # ``claude-code`` aliases to ``claude_code``; both spellings collapse to
    # ONE row with the canonical id, matching /runtime-spec-at-batch.
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=cloud_starter&runtimes=claude-code,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]


def test_api_next_runtime_batch_at_ceiling_returns_200_with_null_rows(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=enterprise&runtimes=claude_code,openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code", "openclaw"]
    assert all(r["row"] is None for r in body["runtimes"])


def test_api_next_runtime_batch_unknown_runtime_bucketed_200(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=cloud_starter&runtimes=claude_code,bogus-rt"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]
    assert body["unknown"] == ["bogus-rt"]


def test_api_next_runtime_batch_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at-batch?runtimes=claude_code"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at-batch?tier=cloud_starter"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at-batch?tier=bogus&runtimes=claude_code"
        ).status_code
        == 404
    )


# ── /api/entitlement/previous-tier-runtime-spec-at-batch ─────────────────────


def test_api_previous_runtime_batch_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-spec-at-batch"
        "?tier=cloud_pro&runtimes=claude_code,openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_RUNTIME_KEYS
    assert body["target"] == ent.TIER_CLOUD_STARTER
    for row in body["runtimes"]:
        scalar = client.get(
            f"/api/entitlement/previous-tier-runtime-spec-at"
            f"?tier=cloud_pro&runtime={row['runtime']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_previous_runtime_batch_at_floor_returns_200_with_null_rows(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-runtime-spec-at-batch"
            f"?tier={src}&runtimes=claude_code,openclaw"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["target"] is None
        assert all(r["row"] is None for r in body["runtimes"])


def test_api_previous_runtime_batch_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at-batch?runtimes=claude_code"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at-batch?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at-batch?tier=bogus&runtimes=claude_code"
        ).status_code
        == 404
    )


# ── cross-axis parity with the path-batch sibling ────────────────────────────


def test_next_feature_batch_first_row_matches_path_batch_first_rung(ent):
    # The first rung of /feature-spec-path-batch from src -> next purchasable
    # equals the body of /next-tier-feature-spec-at-batch from src. Pins the
    # path-vs-what-if relationship at the boundary so the two batch helpers
    # cannot drift.
    src = ent.TIER_CLOUD_STARTER
    target = ent._next_purchasable_tier_after(src)
    feats = ["custom_alerts", "sso"]
    at_batch = ent.next_tier_feature_spec_at_batch(src, feats)
    path_batch = ent.feature_spec_path_batch(src, target, feats)
    assert at_batch is not None
    assert path_batch is not None
    # path_batch[features][i].path is a list of rung augmented rows from src
    # to target; the LAST rung is the target itself (because feature_spec_path
    # walks rungs strictly between from and to and includes the target row).
    # Each at_batch row equals feature_spec_at(target, feature).
    for at_row in at_batch["features"]:
        assert at_row["row"] == ent.feature_spec_at(target, at_row["feature"])
