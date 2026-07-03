"""Tests for ``tier_catalog_at_batch(tiers)`` +
``GET /api/entitlement/tier-catalog-at-batch``.

Tier-axis twin of ``feature_catalog_at_batch`` /
``runtime_catalog_at_batch``: where the scalar ``tier_catalog_at``
hydrates the full tier ladder for ONE hypothetical source (with
``is_current`` flipped to that source), the batch what-if catalog
hydrates the same ladder for N hypothetical sources off a single
round-trip -- the perspective-tier axis is batched.

Each returned ``tiers[].tiers`` list must be byte-identical to the
scalar ``tier_catalog_at`` return for the same source tier, so the
scalar / batch what-if catalog accessors cannot drift -- pinned by
the parity tests below.

Coverage:

* per-source row shape matches the scalar catalog (parity pin)
* every tier in ``_TIER_ORDER`` (including ``trial``) round-trips
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved) -- same as ``_normalise_csv``
* unknown ids are echoed in ``unknown[]`` instead of short-circuiting
* the helper never raises -- a per-tier crash short-circuits that id
  into ``unknown[]`` so the matrix keeps rendering
* the HTTP endpoint 400s on missing / empty input, echoes unknown ids
  at 200, carries the standard envelope (``current_tier`` /
  ``current_tier_rank`` / ``grace`` / ``enforced``), and never 5xxs
  on a resolver crash
* grace vs enforce yields byte-identical bodies (catalogue-derived)
"""
from __future__ import annotations

import importlib

import pytest


_ROW_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
    "features",
    "runtimes",
}

_OUTER_ROW_KEYS = {"tier", "tier_label", "tier_rank", "tiers"}

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
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode); the helper is catalogue-
    derived and independent of either knob, but the fixture avoids
    live-resolver surprises."""
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


# ── helper: input handling ───────────────────────────────────────────────────


def test_empty_input_returns_empty_envelope(ent):
    assert ent.tier_catalog_at_batch([]) == {"tiers": [], "unknown": []}


def test_none_input_returns_empty_envelope(ent):
    assert ent.tier_catalog_at_batch(None) == {"tiers": [], "unknown": []}


def test_string_csv_input(ent):
    body = ent.tier_catalog_at_batch(
        f"{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_supply_order_preserved(ent):
    body = ent.tier_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]


def test_whitespace_and_case_normalised(ent):
    body = ent.tier_catalog_at_batch(
        ["  CLOUD_PRO  ", ent.TIER_CLOUD_STARTER.upper()]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_duplicates_dropped_first_seen_wins(ent):
    body = ent.tier_catalog_at_batch(
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


def test_unknown_ids_echoed_in_unknown(ent):
    body = ent.tier_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, "nope_tier", "also_bogus"]
    )
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_unknown_only_returns_empty_tiers(ent):
    body = ent.tier_catalog_at_batch(["nope_tier", "also_bogus"])
    assert body == {"tiers": [], "unknown": ["nope_tier", "also_bogus"]}


def test_non_iterable_input_falls_back_to_empty(ent):
    # ``_normalise_csv`` returns ``[]`` for non-iterable inputs (int,
    # object, etc.) so the batch collapses to an empty envelope rather
    # than raising.
    assert ent.tier_catalog_at_batch(12345) == {
        "tiers": [],
        "unknown": [],
    }
    assert ent.tier_catalog_at_batch(object()) == {
        "tiers": [],
        "unknown": [],
    }


def test_trial_source_accepted(ent):
    body = ent.tier_catalog_at_batch([ent.TIER_TRIAL])
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_TRIAL]
    assert body["unknown"] == []


# ── helper: shape + parity ───────────────────────────────────────────────────


def test_row_shape_matches_scalar(ent):
    body = ent.tier_catalog_at_batch([ent.TIER_CLOUD_PRO])
    assert len(body["tiers"]) == 1
    row = body["tiers"][0]
    assert set(row.keys()) == _OUTER_ROW_KEYS
    assert isinstance(row["tiers"], list)
    assert set(row["tiers"][0].keys()) == _ROW_KEYS


def test_ladder_matches_scalar_exactly(ent):
    """Pin scalar / batch no-drift: every batch source's ``tiers`` list
    equals the scalar ``tier_catalog_at`` list for the same source."""
    body = ent.tier_catalog_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["tiers"] == ent.tier_catalog_at(tid), tid


def test_tier_metadata_matches_scalar(ent):
    body = ent.tier_catalog_at_batch([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert row["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_every_tier_in_order_resolves(ent):
    body = ent.tier_catalog_at_batch(list(ent._TIER_ORDER))
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []
    for row in body["tiers"]:
        assert len(row["tiers"]) == len(ent._TIER_ORDER)


# ── helper: perspective shifts ───────────────────────────────────────────────


def test_is_current_flips_per_source(ent):
    """Same batch response carries ``is_current=True`` on exactly one
    row per source -- the requested source -- and False everywhere
    else."""
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    body = ent.tier_catalog_at_batch(sources)
    by_tier = {row["tier"]: row for row in body["tiers"]}
    for source in sources:
        rows = by_tier[source]["tiers"]
        current = [r for r in rows if r["is_current"]]
        assert len(current) == 1, source
        assert current[0]["id"] == source, source
        for r in rows:
            if r["id"] != source:
                assert r["is_current"] is False, (source, r["id"])


def test_non_is_current_fields_invariant_across_sources(ent):
    """Every catalogue-derived field on a tier row is stable across the
    source axis -- only ``is_current`` shifts. Any drift means a
    resolution-dependent field leaked into the catalog somehow."""
    body = ent.tier_catalog_at_batch(list(ent._TIER_ORDER))
    by_source = {row["tier"]: row["tiers"] for row in body["tiers"]}
    baseline_by_id = {r["id"]: r for r in by_source[ent.TIER_OSS]}
    invariant = _ROW_KEYS - {"is_current"}
    for source, rows in by_source.items():
        for r in rows:
            base = baseline_by_id[r["id"]]
            for key in invariant:
                assert r[key] == base[key], (source, r["id"], key)


# ── helper: resolver-independence ────────────────────────────────────────────


def test_grace_vs_enforce_byte_identical(ent, monkeypatch):
    """Enforcement is a live-resolver knob; the batch what-if helper
    is catalogue-derived and must produce byte-identical bodies."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.tier_catalog_at_batch(list(ent._TIER_ORDER))

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_catalog_at_batch(list(ent._TIER_ORDER))
    assert grace == enforced


# ── helper: never-raise ──────────────────────────────────────────────────────


def test_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    """A per-tier scalar helper crash must short-circuit that id into
    ``unknown[]`` and the rest of the batch keeps building -- matches
    every other ``_at_batch`` sibling's posture."""
    real = ent.tier_catalog_at

    def flaky(t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "tier_catalog_at", flaky)
    body = ent.tier_catalog_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


def test_never_raises_when_scalar_returns_none(ent, monkeypatch):
    """A per-tier scalar ``None`` return must land the id in
    ``unknown[]`` without raising."""
    real = ent.tier_catalog_at

    def none_pro(t):
        if t == ent.TIER_CLOUD_PRO:
            return None
        return real(t)

    monkeypatch.setattr(ent, "tier_catalog_at", none_pro)
    body = ent.tier_catalog_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


# ── HTTP endpoint: happy path ────────────────────────────────────────────────


def test_endpoint_known_tiers_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS.issubset(set(body.keys()))
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    # Each row's ladder matches the scalar catalog endpoint for the
    # same source -- pinned so scalar and batch cannot drift.
    for row in body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/tier-catalog-at?tier={row['tier']}"
        ).get_json()
        assert row["tiers"] == scalar["tiers"], row["tier"]


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/tier-catalog-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get(
        "/api/entitlement/tier-catalog-at-batch?tiers=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_ids_echoed_at_200(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_PRO},nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch"
        f"?tiers=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]


def test_endpoint_every_tier_in_order_round_trips(client, ent):
    tiers = ",".join(ent._TIER_ORDER)
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch?tiers={tiers}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


def test_endpoint_envelope_carries_current_tier_and_grace_flags(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


def test_endpoint_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/tier-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_unknown_only_returns_200_empty_rows(client, ent):
    resp = client.get(
        "/api/entitlement/tier-catalog-at-batch?tiers=nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["nope_tier", "also_bogus"]
