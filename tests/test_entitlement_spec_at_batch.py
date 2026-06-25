"""Tests for ``feature_spec_at_batch(tier, features)`` /
``runtime_spec_at_batch(tier, runtimes)`` plus their HTTP endpoints.

These are the what-if + batch siblings of ``feature_spec_at`` /
``runtime_spec_at``: where the scalar what-if accessors hydrate one row
at a hypothetical tier, the batch what-if accessors hydrate the N rows a
pricing-comparison matrix UI is about to render off a single round-trip.

Each returned row must be byte-identical to a row from the corresponding
``_catalog_at`` accessor (``feature_catalog_at`` / ``runtime_catalog_at``)
so the scalar what-if / bulk what-if / batch what-if accessors cannot
drift -- pinned by the parity tests below.

Coverage:

* row shape matches the catalog (and matches the scalar ``_spec_at`` row)
* perspective tier really shifts the ``allowed`` / ``locked`` / ``entitled``
  fields (paid feature locked at OSS but allowed at Cloud Pro)
* input is normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown ids are echoed in ``unknown[]`` instead of 404'ing the call
* runtime aliases canonicalise (``claude-code`` -> ``claude_code``) and
  collapse against already-supplied canonical ids without double-emitting
  a row
* unknown / blank ``tier`` returns ``None`` (helper) / 400 / 404 (HTTP)
* the helpers never raise -- a resolver crash short-circuits to the
  OSS-free fallback so the matrix keeps rendering
* the HTTP endpoints 400 on missing / empty input, 404 on unknown tier,
  never 5xx on a resolver crash, and carry the standard ``grace`` /
  ``enforced`` / ``current_tier`` / ``current_tier_rank`` envelope plus
  ``perspective_tier`` / ``perspective_tier_rank``.
"""
from __future__ import annotations

import importlib

import pytest


_FEATURE_SPEC_KEYS = {
    "id",
    "label",
    "tier",
    "tiers",
    "free",
    "allowed",
    "locked",
    "entitled",
    "alias",
}

_RUNTIME_SPEC_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}

_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement
    off by default (grace mode); the helpers still synthesise a non-grace
    hypothetical entitlement under the perspective tier so the ``locked``
    flags actually reflect the per-tier grant."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── feature_spec_at_batch helper: tier handling ──────────────────────────────


def test_feature_at_batch_unknown_tier_returns_none(ent):
    assert ent.feature_spec_at_batch("nope_tier", ["sessions"]) is None


def test_feature_at_batch_blank_tier_returns_none(ent):
    assert ent.feature_spec_at_batch("", ["sessions"]) is None
    assert ent.feature_spec_at_batch("  ", ["sessions"]) is None


def test_feature_at_batch_none_tier_returns_none(ent):
    assert ent.feature_spec_at_batch(None, ["sessions"]) is None


def test_feature_at_batch_int_tier_returns_none(ent):
    # Bad type must not raise.
    assert ent.feature_spec_at_batch(123, ["sessions"]) is None


# ── feature_spec_at_batch helper: shape + parity ─────────────────────────────


def test_feature_at_batch_empty_features_returns_empty_envelope(ent):
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, [])
    assert body == {"features": [], "unknown": []}


def test_feature_at_batch_none_features_returns_empty_envelope(ent):
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, None)
    assert body == {"features": [], "unknown": []}


def test_feature_at_batch_row_shape_matches_catalog(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, [fid])
    assert len(body["features"]) == 1
    assert set(body["features"][0].keys()) == _FEATURE_SPEC_KEYS


def test_feature_at_batch_every_row_matches_feature_spec_at_exactly(ent):
    """Pin scalar / batch no-drift: every batch row equals the scalar
    ``feature_spec_at`` row for the same tier + id."""
    ids = sorted(ent.ALL_FEATURES)
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, ids)
    rows_by_id = {row["id"]: row for row in body["features"]}
    assert set(rows_by_id) == set(ids)
    for fid in ids:
        assert rows_by_id[fid] == ent.feature_spec_at(ent.TIER_CLOUD_PRO, fid), fid


def test_feature_at_batch_rows_match_feature_catalog_at(ent):
    """Pin bulk / batch no-drift: every batch row is byte-identical to the
    same row from ``feature_catalog_at(tier)``."""
    cat_by_id = {
        row["id"]: row for row in ent.feature_catalog_at(ent.TIER_CLOUD_PRO)
    }
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, list(cat_by_id))
    for row in body["features"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── feature_spec_at_batch helper: perspective shifts ─────────────────────────


def test_feature_at_batch_paid_feature_locked_at_oss_allowed_at_pro(ent):
    fid = next(iter(ent.STARTER_FEATURES))
    at_oss = ent.feature_spec_at_batch(ent.TIER_OSS, [fid])
    at_pro = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, [fid])
    assert at_oss["features"][0]["locked"] is True
    assert at_oss["features"][0]["allowed"] is False
    assert at_pro["features"][0]["locked"] is False
    assert at_pro["features"][0]["allowed"] is True


def test_feature_at_batch_free_feature_always_allowed(ent):
    fid = next(iter(ent.FREE_FEATURES))
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO):
        body = ent.feature_spec_at_batch(tier, [fid])
        assert body["features"][0]["allowed"] is True
        assert body["features"][0]["locked"] is False


# ── feature_spec_at_batch helper: normalisation ──────────────────────────────


def test_feature_at_batch_supply_order_preserved(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["sso", "sessions", "fleet"]
    )
    assert [r["id"] for r in body["features"]] == ["sso", "sessions", "fleet"]


def test_feature_at_batch_string_csv_input(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, "sessions,fleet,sso"
    )
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet", "sso"]


def test_feature_at_batch_whitespace_and_case_normalised(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["  Sessions  ", "FLEET"]
    )
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet"]


def test_feature_at_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["sessions", "sessions", "fleet", "sessions"]
    )
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet"]


def test_feature_at_batch_tier_whitespace_and_case_normalised(ent):
    body = ent.feature_spec_at_batch(
        "  CLOUD_PRO  ", ["sessions"]
    )
    assert body is not None
    assert body["features"][0]["id"] == "sessions"


def test_feature_at_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["sessions", "nope_xyz", "also_bogus"]
    )
    assert [r["id"] for r in body["features"]] == ["sessions"]
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


def test_feature_at_batch_unknown_only_returns_empty_features(ent):
    body = ent.feature_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["nope_xyz", "also_bogus"]
    )
    assert body["features"] == []
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


# ── feature_spec_at_batch helper: never-raise ────────────────────────────────


def test_feature_at_batch_never_raises_when_synth_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated synth failure")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.feature_spec_at_batch(ent.TIER_CLOUD_PRO, [fid])
    assert len(body["features"]) == 1
    # Free feature stays free under the OSS-free fallback.
    assert body["features"][0]["free"] is True


# ── runtime_spec_at_batch helper: tier handling ──────────────────────────────


def test_runtime_at_batch_unknown_tier_returns_none(ent):
    assert ent.runtime_spec_at_batch("nope_tier", ["openclaw"]) is None


def test_runtime_at_batch_blank_tier_returns_none(ent):
    assert ent.runtime_spec_at_batch("", ["openclaw"]) is None
    assert ent.runtime_spec_at_batch("  ", ["openclaw"]) is None


def test_runtime_at_batch_none_tier_returns_none(ent):
    assert ent.runtime_spec_at_batch(None, ["openclaw"]) is None


# ── runtime_spec_at_batch helper: shape + parity ─────────────────────────────


def test_runtime_at_batch_empty_runtimes_returns_empty_envelope(ent):
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, [])
    assert body == {"runtimes": [], "unknown": []}


def test_runtime_at_batch_row_shape_matches_catalog(ent):
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, ["openclaw"])
    assert len(body["runtimes"]) == 1
    assert set(body["runtimes"][0].keys()) == _RUNTIME_SPEC_KEYS


def test_runtime_at_batch_every_row_matches_runtime_spec_at_exactly(ent):
    ids = sorted(ent.ALL_RUNTIMES)
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, ids)
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    assert set(rows_by_id) == set(ids)
    for rt in ids:
        assert rows_by_id[rt] == ent.runtime_spec_at(ent.TIER_CLOUD_PRO, rt), rt


def test_runtime_at_batch_rows_match_runtime_catalog_at(ent):
    cat_by_id = {
        row["id"]: row for row in ent.runtime_catalog_at(ent.TIER_CLOUD_PRO)
    }
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, list(cat_by_id))
    for row in body["runtimes"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── runtime_spec_at_batch helper: perspective shifts ─────────────────────────


def test_runtime_at_batch_paid_runtime_locked_at_oss(ent):
    """All PAID_RUNTIMES are locked at the OSS perspective; FREE_RUNTIMES
    stay free."""
    body = ent.runtime_spec_at_batch(ent.TIER_OSS, sorted(ent.ALL_RUNTIMES))
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    for rt in ent.FREE_RUNTIMES:
        assert rows_by_id[rt]["locked"] is False, rt
        assert rows_by_id[rt]["allowed"] is True, rt
    for rt in ent.PAID_RUNTIMES:
        assert rows_by_id[rt]["locked"] is True, rt
        assert rows_by_id[rt]["allowed"] is False, rt


def test_runtime_at_batch_paid_runtime_allowed_at_pro(ent):
    body = ent.runtime_spec_at_batch(
        ent.TIER_CLOUD_PRO, sorted(ent.ALL_RUNTIMES)
    )
    for row in body["runtimes"]:
        assert row["allowed"] is True, row["id"]
        assert row["locked"] is False, row["id"]


# ── runtime_spec_at_batch helper: aliasing + de-dup ──────────────────────────


def test_runtime_at_batch_alias_canonicalises(ent):
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, ["claude-code"])
    assert [r["id"] for r in body["runtimes"]] == ["claude_code"]


def test_runtime_at_batch_alias_collapses_against_seen_canonical(ent):
    body = ent.runtime_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["claude-code", "claude_code", "openclaw"]
    )
    assert [r["id"] for r in body["runtimes"]] == ["claude_code", "openclaw"]


def test_runtime_at_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.runtime_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["openclaw", "nope_runtime"]
    )
    assert [r["id"] for r in body["runtimes"]] == ["openclaw"]
    assert body["unknown"] == ["nope_runtime"]


def test_runtime_at_batch_whitespace_and_case_normalised(ent):
    body = ent.runtime_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["  Openclaw  ", "CLAUDE-CODE"]
    )
    assert [r["id"] for r in body["runtimes"]] == ["openclaw", "claude_code"]


# ── runtime_spec_at_batch helper: never-raise ────────────────────────────────


def test_runtime_at_batch_never_raises_when_synth_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated synth failure")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", boom)
    body = ent.runtime_spec_at_batch(ent.TIER_CLOUD_PRO, ["openclaw"])
    assert len(body["runtimes"]) == 1
    assert body["runtimes"][0]["free"] is True


# ── HTTP: feature-spec-at-batch endpoint ─────────────────────────────────────


def test_endpoint_feature_at_batch_returns_rows_and_envelope(client, ent):
    fid_free = next(iter(ent.FREE_FEATURES))
    fid_paid = next(iter(ent.STARTER_FEATURES))
    resp = client.get(
        "/api/entitlement/feature-spec-at-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&features={fid_free},{fid_paid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["features"]] == [fid_free, fid_paid]
    assert body["unknown"] == []
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["perspective_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_endpoint_feature_at_batch_perspective_shifts_lock(client, ent):
    fid = next(iter(ent.STARTER_FEATURES))
    at_oss = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier={ent.TIER_OSS}&features={fid}"
    )
    at_pro = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&features={fid}"
    )
    assert at_oss.get_json()["features"][0]["locked"] is True
    assert at_pro.get_json()["features"][0]["locked"] is False


def test_endpoint_feature_at_batch_missing_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec-at-batch?features={fid}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_feature_at_batch_blank_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier=%20%20&features={fid}"
    )
    assert resp.status_code == 400


def test_endpoint_feature_at_batch_unknown_tier_returns_404(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier=nope_tier&features={fid}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"
    assert body.get("tier") == "nope_tier"


def test_endpoint_feature_at_batch_missing_features_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400


def test_endpoint_feature_at_batch_blank_features_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/feature-spec-at-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&features=%20%20,%20"
    )
    assert resp.status_code == 400


def test_endpoint_feature_at_batch_unknown_only_returns_200(client, ent):
    """Unknown ids alone do not 400 -- they normalise to a non-empty list
    so the helper runs and returns ``unknown=[...]`` with empty features."""
    resp = client.get(
        "/api/entitlement/feature-spec-at-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&features=not_a_feature,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["unknown"] == ["not_a_feature", "also_bogus"]


def test_endpoint_feature_at_batch_lowercases_tier_and_features(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        "/api/entitlement/feature-spec-at-batch"
        f"?tier=CLOUD_PRO&features={fid.upper()},{fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert [r["id"] for r in body["features"]] == [fid]


def test_endpoint_feature_at_batch_envelope_carries_current_tier(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&features={fid}"
    )
    body = resp.get_json()
    # Live resolved tier is OSS (no license / no cloud plan); perspective is Pro.
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == ent.tier_rank("oss")
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_feature_at_batch_never_5xxs_when_resolver_crashes(
    client, ent, monkeypatch
):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&features={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    # Endpoint short-circuits to the OSS-free envelope on resolver failure.
    assert body["current_tier"] == "oss"
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["grace"] is True
    assert body["enforced"] is False


# ── HTTP: runtime-spec-at-batch endpoint ─────────────────────────────────────


def test_endpoint_runtime_at_batch_returns_rows_and_envelope(client, ent):
    resp = client.get(
        "/api/entitlement/runtime-spec-at-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["runtimes"]] == ["openclaw", "claude_code"]
    assert body["unknown"] == []
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_endpoint_runtime_at_batch_perspective_shifts_lock(client, ent):
    """A PAID runtime is locked at OSS but allowed at Cloud Pro."""
    paid_rt = next(iter(ent.PAID_RUNTIMES))
    at_oss = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_OSS}&runtimes={paid_rt}"
    )
    at_pro = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&runtimes={paid_rt}"
    )
    assert at_oss.get_json()["runtimes"][0]["locked"] is True
    assert at_pro.get_json()["runtimes"][0]["locked"] is False


def test_endpoint_runtime_at_batch_missing_tier_returns_400(client):
    resp = client.get("/api/entitlement/runtime-spec-at-batch?runtimes=openclaw")
    assert resp.status_code == 400


def test_endpoint_runtime_at_batch_unknown_tier_returns_404(client):
    resp = client.get(
        "/api/entitlement/runtime-spec-at-batch?tier=nope_tier&runtimes=openclaw"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"


def test_endpoint_runtime_at_batch_missing_runtimes_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400


def test_endpoint_runtime_at_batch_blank_runtimes_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&runtimes=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_runtime_at_batch_alias_canonicalises(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&runtimes=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["runtimes"]] == ["claude_code"]


def test_endpoint_runtime_at_batch_unknown_only_returns_200(client, ent):
    resp = client.get(
        "/api/entitlement/runtime-spec-at-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&runtimes=not_a_runtime"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtimes"] == []
    assert body["unknown"] == ["not_a_runtime"]


def test_endpoint_runtime_at_batch_never_5xxs_when_resolver_crashes(
    client, ent, monkeypatch
):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/runtime-spec-at-batch?tier={ent.TIER_CLOUD_PRO}&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_tier"] == "oss"
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["grace"] is True
    assert body["enforced"] is False
