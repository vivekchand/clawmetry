"""Tests for ``feature_catalog_at_batch(tiers)`` /
``runtime_catalog_at_batch(tiers)`` plus their HTTP endpoints.

These are the batch what-if siblings of ``feature_catalog_at`` /
``runtime_catalog_at``: where the scalar what-if catalog hydrates the
full catalog at ONE hypothetical tier, the batch what-if catalog
hydrates the same catalog at N hypothetical tiers off a single
round-trip -- the perspective-tier axis is batched instead of the
feature/runtime id axis.

Each returned ``tiers[].features`` / ``tiers[].runtimes`` list must be
byte-identical to the corresponding scalar catalog helper's return for
the same tier, so the scalar / batch what-if catalog accessors cannot
drift -- pinned by the parity tests below.

Coverage:

* per-tier row shape matches the scalar catalog (parity pin)
* every tier in ``_TIER_ORDER`` (including ``trial``) round-trips through
  the batch
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved) -- same as ``_normalise_csv``
* unknown ids are echoed in ``unknown[]`` instead of short-circuiting
* the helpers never raise -- a synthesis failure short-circuits to
  ``unknown[]`` so the matrix keeps rendering
* the HTTP endpoints 400 on missing / empty input, echo unknown ids at
  200, carry the standard envelope (``current_tier`` /
  ``current_tier_rank`` / ``grace`` / ``enforced``), and never 5xx on a
  resolver crash
"""
from __future__ import annotations

import importlib

import pytest


_FEATURE_ROW_KEYS = {
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

_RUNTIME_ROW_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}

_TIER_ROW_KEYS = {"tier", "tier_label", "tier_rank"}

_ENVELOPE_KEYS = {
    "tiers",
    "unknown",
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
    hypothetical entitlement per requested tier so the ``locked`` flags
    actually reflect the per-tier grant."""
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


# ── feature_catalog_at_batch helper: input handling ──────────────────────────


def test_feature_batch_empty_input_returns_empty_envelope(ent):
    assert ent.feature_catalog_at_batch([]) == {"tiers": [], "unknown": []}


def test_feature_batch_none_input_returns_empty_envelope(ent):
    assert ent.feature_catalog_at_batch(None) == {"tiers": [], "unknown": []}


def test_feature_batch_string_csv_input(ent):
    body = ent.feature_catalog_at_batch(
        f"{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_feature_batch_supply_order_preserved(ent):
    body = ent.feature_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]


def test_feature_batch_whitespace_and_case_normalised(ent):
    body = ent.feature_catalog_at_batch(
        ["  CLOUD_PRO  ", ent.TIER_CLOUD_STARTER.upper()]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_feature_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.feature_catalog_at_batch(
        [
            ent.TIER_CLOUD_PRO,
            ent.TIER_CLOUD_PRO,
            ent.TIER_CLOUD_STARTER,
            ent.TIER_CLOUD_PRO,
        ]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_feature_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.feature_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, "nope_tier", "also_bogus"]
    )
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_feature_batch_unknown_only_returns_empty_tiers(ent):
    body = ent.feature_catalog_at_batch(["nope_tier", "also_bogus"])
    assert body == {"tiers": [], "unknown": ["nope_tier", "also_bogus"]}


def test_feature_batch_non_iterable_input_falls_back_to_empty(ent):
    # ``_normalise_csv`` returns ``[]`` for non-iterable inputs (int,
    # object, etc.) so the batch collapses to an empty envelope rather
    # than raising.
    assert ent.feature_catalog_at_batch(12345) == {
        "tiers": [],
        "unknown": [],
    }
    assert ent.feature_catalog_at_batch(object()) == {
        "tiers": [],
        "unknown": [],
    }


# ── feature_catalog_at_batch helper: shape + parity ──────────────────────────


def test_feature_batch_row_shape_matches_scalar(ent):
    body = ent.feature_catalog_at_batch([ent.TIER_CLOUD_PRO])
    assert len(body["tiers"]) == 1
    row = body["tiers"][0]
    assert _TIER_ROW_KEYS.issubset(set(row.keys()))
    assert "features" in row
    assert set(row["features"][0].keys()) == _FEATURE_ROW_KEYS


def test_feature_batch_features_list_matches_scalar_exactly(ent):
    """Pin scalar / batch no-drift: every batch tier's ``features`` list
    equals the scalar ``feature_catalog_at`` list for the same tier."""
    body = ent.feature_catalog_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["features"] == ent.feature_catalog_at(tid), tid


def test_feature_batch_tier_metadata_matches_scalar(ent):
    body = ent.feature_catalog_at_batch([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert row["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_feature_batch_every_tier_in_order_resolves(ent):
    body = ent.feature_catalog_at_batch(list(ent._TIER_ORDER))
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []
    for row in body["tiers"]:
        assert len(row["features"]) == len(ent.ALL_FEATURES)


# ── feature_catalog_at_batch helper: perspective shifts ──────────────────────


def test_feature_batch_perspective_shift_locks_at_oss_unlocks_at_pro(ent):
    """Same feature id resolves to locked at OSS and unlocked at Cloud Pro
    within the same batch response -- the whole point of the helper."""
    fid = next(iter(ent.STARTER_FEATURES))
    body = ent.feature_catalog_at_batch([ent.TIER_OSS, ent.TIER_CLOUD_PRO])
    by_tier = {row["tier"]: row for row in body["tiers"]}
    at_oss = {r["id"]: r for r in by_tier[ent.TIER_OSS]["features"]}
    at_pro = {r["id"]: r for r in by_tier[ent.TIER_CLOUD_PRO]["features"]}
    assert at_oss[fid]["locked"] is True
    assert at_oss[fid]["allowed"] is False
    assert at_pro[fid]["locked"] is False
    assert at_pro[fid]["allowed"] is True


def test_feature_batch_free_features_always_allowed(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.feature_catalog_at_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        by_id = {r["id"]: r for r in row["features"]}
        assert by_id[fid]["allowed"] is True, row["tier"]
        assert by_id[fid]["locked"] is False, row["tier"]


def test_feature_batch_enterprise_unlocks_everything(ent):
    body = ent.feature_catalog_at_batch([ent.TIER_ENTERPRISE])
    for r in body["tiers"][0]["features"]:
        assert r["allowed"] is True, r["id"]
        assert r["locked"] is False, r["id"]


# ── feature_catalog_at_batch helper: never-raise ─────────────────────────────


def test_feature_batch_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    """A per-tier scalar helper crash must short-circuit that id into
    ``unknown[]`` and the rest of the batch keeps building -- matches
    every other ``_at_batch`` sibling's posture."""
    real = ent.feature_catalog_at

    def flaky(t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "feature_catalog_at", flaky)
    body = ent.feature_catalog_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


# ── feature_catalog_at_batch helper: resolver-independent ────────────────────


def test_feature_batch_grace_vs_enforce_byte_identical(ent, monkeypatch):
    """Enforcement is a live-resolver knob; the batch what-if helper builds
    a fresh hypothetical Entitlement per tier and must be independent."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.feature_catalog_at_batch(list(ent._TIER_ORDER))

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.feature_catalog_at_batch(list(ent._TIER_ORDER))
    assert grace == enforced


# ── runtime_catalog_at_batch helper: shape + parity ──────────────────────────


def test_runtime_batch_empty_input_returns_empty_envelope(ent):
    assert ent.runtime_catalog_at_batch([]) == {"tiers": [], "unknown": []}


def test_runtime_batch_none_input_returns_empty_envelope(ent):
    assert ent.runtime_catalog_at_batch(None) == {"tiers": [], "unknown": []}


def test_runtime_batch_row_shape_matches_scalar(ent):
    body = ent.runtime_catalog_at_batch([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert _TIER_ROW_KEYS.issubset(set(row.keys()))
    assert "runtimes" in row
    assert set(row["runtimes"][0].keys()) == _RUNTIME_ROW_KEYS


def test_runtime_batch_runtimes_list_matches_scalar_exactly(ent):
    body = ent.runtime_catalog_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["runtimes"] == ent.runtime_catalog_at(tid), tid


def test_runtime_batch_every_tier_in_order_resolves(ent):
    body = ent.runtime_catalog_at_batch(list(ent._TIER_ORDER))
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []
    for row in body["tiers"]:
        assert len(row["runtimes"]) == len(ent.ALL_RUNTIMES)


# ── runtime_catalog_at_batch helper: normalisation ───────────────────────────


def test_runtime_batch_supply_order_preserved(ent):
    body = ent.runtime_catalog_at_batch(
        [ent.TIER_ENTERPRISE, ent.TIER_OSS, ent.TIER_CLOUD_PRO]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
    ]


def test_runtime_batch_whitespace_and_case_normalised(ent):
    body = ent.runtime_catalog_at_batch(["  OSS  ", "CLOUD_PRO"])
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
    ]


def test_runtime_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.runtime_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_OSS]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
    ]


def test_runtime_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.runtime_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, "nope_tier"]
    )
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier"]


# ── runtime_catalog_at_batch helper: perspective shifts ──────────────────────


def test_runtime_batch_paid_runtime_locked_at_oss_allowed_at_pro(ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    body = ent.runtime_catalog_at_batch([ent.TIER_OSS, ent.TIER_CLOUD_PRO])
    by_tier = {row["tier"]: row for row in body["tiers"]}
    at_oss = {r["id"]: r for r in by_tier[ent.TIER_OSS]["runtimes"]}
    at_pro = {r["id"]: r for r in by_tier[ent.TIER_CLOUD_PRO]["runtimes"]}
    assert at_oss[rt]["locked"] is True
    assert at_oss[rt]["allowed"] is False
    assert at_pro[rt]["locked"] is False
    assert at_pro[rt]["allowed"] is True


def test_runtime_batch_free_runtimes_always_allowed(ent):
    body = ent.runtime_catalog_at_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        by_id = {r["id"]: r for r in row["runtimes"]}
        for rt in ent.FREE_RUNTIMES:
            assert by_id[rt]["allowed"] is True, (row["tier"], rt)
            assert by_id[rt]["locked"] is False, (row["tier"], rt)


# ── runtime_catalog_at_batch helper: never-raise ─────────────────────────────


def test_runtime_batch_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    real = ent.runtime_catalog_at

    def flaky(t):
        if t == ent.TIER_CLOUD_STARTER:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "runtime_catalog_at", flaky)
    body = ent.runtime_catalog_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_STARTER]


# ── HTTP endpoint: feature-catalog-at-batch ──────────────────────────────────


def test_endpoint_feature_batch_known_tiers_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS.issubset(set(body.keys()))
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    # Every row's features list matches the scalar catalog endpoint for
    # the same tier -- pinned so scalar and batch cannot drift.
    for row in body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/feature-catalog-at?tier={row['tier']}"
        ).get_json()
        assert row["features"] == scalar["features"], row["tier"]


def test_endpoint_feature_batch_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-catalog-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_feature_batch_blank_arg_returns_400(client):
    resp = client.get(
        "/api/entitlement/feature-catalog-at-batch?tiers=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_feature_batch_unknown_ids_echoed_at_200(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_PRO},nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_endpoint_feature_batch_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch"
        f"?tiers=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]


def test_endpoint_feature_batch_every_tier_in_order_round_trips(client, ent):
    tiers = ",".join(ent._TIER_ORDER)
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch?tiers={tiers}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


def test_endpoint_feature_batch_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


# ── HTTP endpoint: runtime-catalog-at-batch ──────────────────────────────────


def test_endpoint_runtime_batch_known_tiers_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS.issubset(set(body.keys()))
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    for row in body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/runtime-catalog-at?tier={row['tier']}"
        ).get_json()
        assert row["runtimes"] == scalar["runtimes"], row["tier"]


def test_endpoint_runtime_batch_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-catalog-at-batch")
    assert resp.status_code == 400


def test_endpoint_runtime_batch_blank_arg_returns_400(client):
    resp = client.get(
        "/api/entitlement/runtime-catalog-at-batch?tiers=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_runtime_batch_unknown_ids_echoed_at_200(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_PRO},nope_tier"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier"]


def test_endpoint_runtime_batch_every_tier_in_order_round_trips(client, ent):
    tiers = ",".join(ent._TIER_ORDER)
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at-batch?tiers={tiers}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


def test_endpoint_runtime_batch_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_envelope_carries_current_tier_and_grace_flags(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
