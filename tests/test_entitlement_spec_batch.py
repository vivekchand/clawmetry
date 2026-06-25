"""Tests for ``feature_spec_batch(features)`` / ``runtime_spec_batch(runtimes)``
plus their HTTP endpoints.

These are the plural / caller-subset siblings of ``feature_spec`` and
``runtime_spec``: where the scalar accessors hydrate one row, the batch
accessors hydrate the N rows a paywall matrix UI is about to render
off a single round-trip. Each returned row must be byte-identical to a
row from the corresponding catalogue (``feature_catalog`` /
``runtime_catalog``) so the scalar / bulk / batch accessors cannot
drift -- pinned by the parity tests below.

Coverage:

* row shape matches the catalogue (and matches the scalar ``_spec`` row)
* input is normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown ids are echoed in ``unknown[]`` instead of 404'ing the call
* runtime aliases canonicalise (``claude-code`` -> ``claude_code``) and
  collapse against already-supplied canonical ids without double-emitting
  a row
* grace mode reports zero locked rows (zero behaviour change)
* enforce-mode lock state matches what ``feature_catalog`` /
  ``runtime_catalog`` already report for the same install
* the helpers never raise -- a resolver crash short-circuits to the
  OSS-free fallback so the matrix keeps rendering
* the HTTP endpoints 400 on missing / empty input, never 5xx on a
  resolver crash, and carry the standard ``grace`` / ``enforced`` /
  ``current_tier`` / ``current_tier_rank`` envelope fields
"""
from __future__ import annotations

import importlib
import json

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

_ENVELOPE_KEYS = {"current_tier", "current_tier_rank", "grace", "enforced"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default (grace mode)."""
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


# ── feature_spec_batch helper: shape + parity ────────────────────────────────


def test_feature_batch_empty_input_returns_empty_envelope(ent):
    body = ent.feature_spec_batch([])
    assert body == {"features": [], "unknown": []}


def test_feature_batch_none_input_returns_empty_envelope(ent):
    body = ent.feature_spec_batch(None)
    assert body == {"features": [], "unknown": []}


def test_feature_batch_row_shape_matches_catalog(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.feature_spec_batch([fid])
    assert len(body["features"]) == 1
    assert set(body["features"][0].keys()) == _FEATURE_SPEC_KEYS


def test_feature_batch_every_row_matches_feature_spec_exactly(ent):
    ids = sorted(ent.ALL_FEATURES)
    body = ent.feature_spec_batch(ids)
    rows_by_id = {row["id"]: row for row in body["features"]}
    assert set(rows_by_id) == set(ids)
    for fid in ids:
        assert rows_by_id[fid] == ent.feature_spec(fid), fid


def test_feature_batch_rows_match_feature_catalog(ent):
    """Pin scalar / bulk / batch no-drift: every batch row is byte-identical
    to the same row from feature_catalog()."""
    cat_by_id = {row["id"]: row for row in ent.feature_catalog()}
    ids = list(cat_by_id)
    body = ent.feature_spec_batch(ids)
    for row in body["features"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── feature_spec_batch helper: normalisation ─────────────────────────────────


def test_feature_batch_supply_order_preserved(ent):
    body = ent.feature_spec_batch(["sso", "sessions", "fleet"])
    assert [r["id"] for r in body["features"]] == ["sso", "sessions", "fleet"]


def test_feature_batch_string_csv_input(ent):
    body = ent.feature_spec_batch("sessions,fleet,sso")
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet", "sso"]


def test_feature_batch_whitespace_and_case_normalised(ent):
    body = ent.feature_spec_batch(["  Sessions  ", "FLEET"])
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet"]


def test_feature_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.feature_spec_batch(["sessions", "sessions", "fleet", "sessions"])
    assert [r["id"] for r in body["features"]] == ["sessions", "fleet"]


def test_feature_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.feature_spec_batch(["sessions", "nope_xyz", "also_bogus"])
    assert [r["id"] for r in body["features"]] == ["sessions"]
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


def test_feature_batch_unknown_only_returns_empty_features(ent):
    body = ent.feature_spec_batch(["nope_xyz", "also_bogus"])
    assert body["features"] == []
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


# ── feature_spec_batch helper: grace vs enforce ──────────────────────────────


def test_feature_batch_grace_locks_nothing(ent):
    body = ent.feature_spec_batch(sorted(ent.ALL_FEATURES))
    assert all(r["locked"] is False for r in body["features"])
    assert all(r["allowed"] is True for r in body["features"])


def test_feature_batch_enforce_oss_matches_catalog_locks(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cat_by_id = {row["id"]: row for row in ent.feature_catalog()}
    body = ent.feature_spec_batch(sorted(cat_by_id))
    for row in body["features"]:
        assert row["locked"] == cat_by_id[row["id"]]["locked"], row["id"]
        assert row["allowed"] == cat_by_id[row["id"]]["allowed"], row["id"]


# ── feature_spec_batch helper: never-raise ───────────────────────────────────


def test_feature_batch_never_raises_when_resolver_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.feature_spec_batch([fid])
    assert len(body["features"]) == 1
    # Free feature stays free under the OSS-free fallback.
    assert body["features"][0]["free"] is True


# ── runtime_spec_batch helper: shape + parity ────────────────────────────────


def test_runtime_batch_empty_input_returns_empty_envelope(ent):
    assert ent.runtime_spec_batch([]) == {"runtimes": [], "unknown": []}


def test_runtime_batch_row_shape_matches_catalog(ent):
    body = ent.runtime_spec_batch(["openclaw"])
    assert len(body["runtimes"]) == 1
    assert set(body["runtimes"][0].keys()) == _RUNTIME_SPEC_KEYS


def test_runtime_batch_every_row_matches_runtime_spec_exactly(ent):
    ids = sorted(ent.ALL_RUNTIMES)
    body = ent.runtime_spec_batch(ids)
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    assert set(rows_by_id) == set(ids)
    for rt in ids:
        assert rows_by_id[rt] == ent.runtime_spec(rt), rt


def test_runtime_batch_rows_match_runtime_catalog(ent):
    cat_by_id = {row["id"]: row for row in ent.runtime_catalog()}
    body = ent.runtime_spec_batch(list(cat_by_id))
    for row in body["runtimes"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── runtime_spec_batch helper: aliasing + de-dup ─────────────────────────────


def test_runtime_batch_alias_canonicalises(ent):
    body = ent.runtime_spec_batch(["claude-code"])
    assert [r["id"] for r in body["runtimes"]] == ["claude_code"]


def test_runtime_batch_alias_collapses_against_seen_canonical(ent):
    """``claude-code`` and ``claude_code`` both normalise to the same id;
    the row appears once, in first-seen position."""
    body = ent.runtime_spec_batch(["claude-code", "claude_code", "openclaw"])
    assert [r["id"] for r in body["runtimes"]] == ["claude_code", "openclaw"]


def test_runtime_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.runtime_spec_batch(["openclaw", "nope_runtime"])
    assert [r["id"] for r in body["runtimes"]] == ["openclaw"]
    assert body["unknown"] == ["nope_runtime"]


def test_runtime_batch_whitespace_and_case_normalised(ent):
    body = ent.runtime_spec_batch(["  Openclaw  ", "CLAUDE-CODE"])
    assert [r["id"] for r in body["runtimes"]] == ["openclaw", "claude_code"]


# ── runtime_spec_batch helper: grace vs enforce ──────────────────────────────


def test_runtime_batch_grace_locks_nothing(ent):
    body = ent.runtime_spec_batch(sorted(ent.ALL_RUNTIMES))
    assert all(r["locked"] is False for r in body["runtimes"])
    assert all(r["allowed"] is True for r in body["runtimes"])


def test_runtime_batch_enforce_oss_locks_paid_runtimes(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    body = ent.runtime_spec_batch(sorted(ent.ALL_RUNTIMES))
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    for rt in ent.FREE_RUNTIMES:
        assert rows_by_id[rt]["locked"] is False, rt
        assert rows_by_id[rt]["allowed"] is True, rt
    for rt in ent.PAID_RUNTIMES:
        assert rows_by_id[rt]["locked"] is True, rt
        assert rows_by_id[rt]["allowed"] is False, rt


# ── runtime_spec_batch helper: never-raise ───────────────────────────────────


def test_runtime_batch_never_raises_when_resolver_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.runtime_spec_batch(["openclaw"])
    assert len(body["runtimes"]) == 1
    assert body["runtimes"][0]["free"] is True


# ── HTTP: feature-spec-batch endpoint ────────────────────────────────────────


def test_endpoint_feature_batch_returns_rows_and_envelope(client, ent):
    fid_free = next(iter(ent.FREE_FEATURES))
    fid_paid = next(iter(ent.STARTER_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-batch?features={fid_free},{fid_paid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["features"]] == [fid_free, fid_paid]
    assert body["unknown"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_feature_batch_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-spec-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_feature_batch_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-spec-batch?features=%20%20,%20")
    assert resp.status_code == 400


def test_endpoint_feature_batch_unknown_only_returns_200(client):
    """Unknown ids alone do not 400 -- they normalise to a non-empty list
    so the helper runs and returns ``unknown=[...]`` with empty features."""
    resp = client.get(
        "/api/entitlement/feature-spec-batch?features=not_a_feature,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["unknown"] == ["not_a_feature", "also_bogus"]


def test_endpoint_feature_batch_lowercases_and_dedupes(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-batch?features={fid.upper()},{fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["features"]] == [fid]


def test_endpoint_feature_batch_envelope_carries_resolved_tier(client, ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    fid = next(iter(ent.STARTER_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec-batch?features={fid}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_tier"] == ent.TIER_CLOUD_PRO
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["grace"] is False
    assert body["enforced"] is True


def test_endpoint_feature_batch_never_5xxs_when_resolver_crashes(
    client, ent, monkeypatch
):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec-batch?features={fid}")
    assert resp.status_code == 200
    body = resp.get_json()
    # Endpoint short-circuits to the OSS-free envelope on resolver failure.
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


# ── HTTP: runtime-spec-batch endpoint ────────────────────────────────────────


def test_endpoint_runtime_batch_returns_rows_and_envelope(client):
    resp = client.get(
        "/api/entitlement/runtime-spec-batch?runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["runtimes"]] == ["openclaw", "claude_code"]
    assert body["unknown"] == []
    assert body["grace"] is True


def test_endpoint_runtime_batch_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-spec-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_runtime_batch_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-spec-batch?runtimes=%20%20")
    assert resp.status_code == 400


def test_endpoint_runtime_batch_alias_canonicalises(client):
    resp = client.get(
        "/api/entitlement/runtime-spec-batch?runtimes=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["runtimes"]] == ["claude_code"]


def test_endpoint_runtime_batch_unknown_only_returns_200(client):
    resp = client.get(
        "/api/entitlement/runtime-spec-batch?runtimes=not_a_runtime"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtimes"] == []
    assert body["unknown"] == ["not_a_runtime"]


def test_endpoint_runtime_batch_never_5xxs_when_resolver_crashes(
    client, ent, monkeypatch
):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        "/api/entitlement/runtime-spec-batch?runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
