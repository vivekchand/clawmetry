"""Tests for ``tier_spec_at_batch(tier, targets)`` + ``GET
/api/entitlement/tier-spec-at-batch``.

What-if + batch sibling of :func:`tier_spec_at`: single-tier descriptor
rows for a caller-supplied subset of target tiers, all computed from the
perspective of one fixed hypothetical ``tier``. Fixed-source multi-target
companion to :func:`tier_spec_at` and tier-axis sibling of
:func:`feature_spec_at_batch` / :func:`runtime_spec_at_batch` (which
fix the source and batch over the feature / runtime axis).

Pins:

* per-row body is byte-identical to :func:`tier_spec_at(tier, target)`
  for the same target (scalar/batch no-drift contract) -- a parity test
  enumerates every (tier, target) pair
* only ``is_current`` varies row by row (``True`` iff the row's ``id``
  equals the perspective tier); every other field stays catalogue-derived
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved)
* unknown ids are echoed in ``unknown[]`` instead of short-circuiting
* unknown / blank / ``None`` / non-string perspective ``tier`` returns
  ``None`` (helper) / 400 (missing / blank) / 404 (unknown)
* ``trial`` is accepted as both perspective and target -- lenient ``_at``
  posture matching :func:`tier_spec_at` and :func:`feature_spec_at_batch`
* the helper is independent of the live resolver: switching enforcement
  or pointing HOME at a license cache does not change the rows the
  what-if surface returns
* the endpoint 400s on missing / empty input, 404s on unknown perspective
  tier, never 5xxs on a resolver crash, and carries the standard
  ``grace`` / ``enforced`` / ``current_tier`` / ``current_tier_rank``
  envelope plus ``perspective_tier`` / ``perspective_tier_rank``.
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
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default -- ``tier_spec_at_batch`` is independent
    of either knob, so the fixture only needs to keep the live resolver
    from surprising the test."""
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


# ── perspective tier handling ────────────────────────────────────────────────


def test_unknown_perspective_tier_returns_none(ent):
    assert ent.tier_spec_at_batch("bogus", ["oss"]) is None


def test_blank_perspective_tier_returns_none(ent):
    assert ent.tier_spec_at_batch("", ["oss"]) is None
    assert ent.tier_spec_at_batch("   ", ["oss"]) is None


def test_none_perspective_tier_returns_none(ent):
    assert ent.tier_spec_at_batch(None, ["oss"]) is None


def test_int_perspective_tier_returns_none(ent):
    assert ent.tier_spec_at_batch(0, ["oss"]) is None


def test_perspective_tier_whitespace_and_case_normalised(ent):
    got = ent.tier_spec_at_batch("  CLOUD_PRO  ", ["cloud_pro"])
    assert got is not None
    assert got["tiers"][0]["id"] == "cloud_pro"
    assert got["tiers"][0]["is_current"] is True


def test_trial_accepted_as_perspective(ent):
    got = ent.tier_spec_at_batch(ent.TIER_TRIAL, [ent.TIER_TRIAL])
    assert got is not None
    assert got["tiers"][0]["id"] == ent.TIER_TRIAL
    assert got["tiers"][0]["is_current"] is True


# ── targets input handling ───────────────────────────────────────────────────


def test_empty_targets_returns_empty_envelope(ent):
    got = ent.tier_spec_at_batch("cloud_pro", [])
    assert got == {"tiers": [], "unknown": []}


def test_none_targets_returns_empty_envelope(ent):
    got = ent.tier_spec_at_batch("cloud_pro", None)
    assert got == {"tiers": [], "unknown": []}


def test_targets_string_csv_input(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", "oss,cloud_starter,cloud_pro"
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == [
        "oss",
        "cloud_starter",
        "cloud_pro",
    ]


def test_targets_whitespace_and_case_normalised(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["  OSS ", "Cloud_Pro"]
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == ["oss", "cloud_pro"]


def test_targets_duplicates_dropped_first_seen_wins(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "oss", "cloud_pro"]
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == ["oss", "cloud_pro"]


def test_targets_supply_order_preserved(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["cloud_pro", "oss", "enterprise", "cloud_starter"]
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == [
        "cloud_pro",
        "oss",
        "enterprise",
        "cloud_starter",
    ]


def test_targets_unknown_ids_echoed_in_unknown(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "bogus", "cloud_pro", "also_bogus"]
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == ["oss", "cloud_pro"]
    assert got["unknown"] == ["bogus", "also_bogus"]


def test_targets_unknown_only_returns_empty_tiers(ent):
    got = ent.tier_spec_at_batch("cloud_pro", ["bogus", "also_bogus"])
    assert got is not None
    assert got["tiers"] == []
    assert got["unknown"] == ["bogus", "also_bogus"]


def test_trial_accepted_as_target(ent):
    got = ent.tier_spec_at_batch("cloud_pro", [ent.TIER_TRIAL])
    assert got is not None
    assert got["tiers"][0]["id"] == ent.TIER_TRIAL


# ── row shape + parity ───────────────────────────────────────────────────────


def test_row_shape_matches_tier_spec_at(ent):
    got = ent.tier_spec_at_batch("cloud_pro", ["oss", "cloud_pro"])
    assert got is not None
    for row in got["tiers"]:
        assert set(row.keys()) == _ROW_KEYS


def test_row_parity_with_scalar_tier_spec_at(ent):
    """For every (tier, target) pair, the batch row is byte-identical
    to the scalar. Pins the scalar/batch no-drift contract."""
    for tier in ent._TIER_ORDER:
        got = ent.tier_spec_at_batch(tier, list(ent._TIER_ORDER))
        assert got is not None
        rows_by_id = {row["id"]: row for row in got["tiers"]}
        for target in ent._TIER_ORDER:
            assert rows_by_id[target] == ent.tier_spec_at(tier, target), (
                tier,
                target,
            )


def test_row_parity_with_tier_catalog_at(ent):
    """Each returned row also matches the corresponding row in
    :func:`tier_catalog_at` -- three-way parity (scalar / bulk / batch)."""
    for tier in ent._TIER_ORDER:
        got = ent.tier_spec_at_batch(tier, list(ent._TIER_ORDER))
        assert got is not None
        catalog_by_id = {row["id"]: row for row in ent.tier_catalog_at(tier)}
        for row in got["tiers"]:
            assert row == catalog_by_id[row["id"]], (tier, row["id"])


def test_is_current_flips_with_perspective(ent):
    """``is_current`` is True iff the row's id equals the perspective
    tier, so shifting the perspective shifts which row (if any) carries
    the flag."""
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "cloud_starter", "cloud_pro", "enterprise"]
    )
    assert got is not None
    flags = {row["id"]: row["is_current"] for row in got["tiers"]}
    assert flags == {
        "oss": False,
        "cloud_starter": False,
        "cloud_pro": True,
        "enterprise": False,
    }


def test_is_current_absent_when_perspective_not_in_targets(ent):
    got = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "cloud_starter", "enterprise"]
    )
    assert got is not None
    assert all(row["is_current"] is False for row in got["tiers"])


# ── resolver independence ────────────────────────────────────────────────────


def test_resolver_independent_across_enforcement(ent, monkeypatch):
    """Grace vs enforce yields byte-identical rows -- ``tier_spec_at``
    reads the static per-tier maps, not the live resolver, so the batch
    inherits that property."""
    grace = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "enterprise"]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_spec_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "enterprise"]
    )
    assert grace == enforced


def test_never_raises_when_scalar_crashes(ent, monkeypatch):
    """A per-row failure short-circuits that id into ``unknown[]`` and
    the rest of the batch keeps building."""
    orig = ent.tier_spec_at

    def _boom(tier, target):
        if target == "cloud_pro":
            raise RuntimeError("boom")
        return orig(tier, target)

    monkeypatch.setattr(ent, "tier_spec_at", _boom)
    got = ent.tier_spec_at_batch(
        "enterprise", ["oss", "cloud_pro", "enterprise"]
    )
    assert got is not None
    assert [row["id"] for row in got["tiers"]] == ["oss", "enterprise"]
    assert got["unknown"] == ["cloud_pro"]


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_returns_rows_and_envelope(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch"
        "?tier=cloud_pro&targets=oss,cloud_pro,enterprise"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["id"] for row in body["tiers"]] == [
        "oss",
        "cloud_pro",
        "enterprise",
    ]
    assert body["unknown"] == []
    assert _ENVELOPE_KEYS.issubset(body.keys())
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")


def test_endpoint_perspective_flips_is_current(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch"
        "?tier=enterprise&targets=oss,cloud_pro,enterprise"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    flags = {row["id"]: row["is_current"] for row in body["tiers"]}
    assert flags == {
        "oss": False,
        "cloud_pro": False,
        "enterprise": True,
    }


def test_endpoint_missing_tier_returns_400(client, ent):
    resp = client.get("/api/entitlement/tier-spec-at-batch?targets=oss")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing tier"


def test_endpoint_blank_tier_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch?tier=%20%20&targets=oss"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing tier"


def test_endpoint_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch?tier=bogus&targets=oss"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_endpoint_missing_targets_returns_400(client, ent):
    resp = client.get("/api/entitlement/tier-spec-at-batch?tier=cloud_pro")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "supply targets=<csv>"


def test_endpoint_blank_targets_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch?tier=cloud_pro&targets=,,,"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "supply targets=<csv>"


def test_endpoint_unknown_only_returns_200(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch"
        "?tier=cloud_pro&targets=bogus,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["bogus", "also_bogus"]
    assert body["perspective_tier"] == "cloud_pro"


def test_endpoint_lowercases_tier_and_targets(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch"
        "?tier=CLOUD_PRO&targets=OSS,Cloud_Pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert [row["id"] for row in body["tiers"]] == ["oss", "cloud_pro"]


def test_endpoint_envelope_carries_current_tier(client, ent):
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch?tier=cloud_pro&targets=oss"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] is bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_endpoint_never_5xxs_when_resolver_crashes(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_spec_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch?tier=cloud_pro&targets=oss"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []
    assert body["perspective_tier"] == "cloud_pro"
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
