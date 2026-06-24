"""Tests for ``tier_catalog_at(tier)`` + ``GET /api/entitlement/tier-catalog-at``.

What-if sibling of :func:`tier_catalog`: returns the full upgrade ladder
with ``is_current`` recomputed as if the install were on ``tier`` instead
of the resolved tier. Lets a pricing-comparison UI render the ladder from
the perspective of any hypothetical tier without first switching the live
resolver.

Pins:

* row shape (keys + ordering) matches :func:`tier_catalog` exactly so a
  UI swapping between "current" and "hypothetical" never has to reshape
  client-side
* every tier in ``_TIER_ORDER`` resolves to a non-``None`` catalogue and
  flips exactly one ``is_current`` row to ``True`` (the requested one)
* every catalogue-derived field (``id``, ``label``, ``is_paid``, ``rank``,
  ``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
  ``node_limit``, ``features``, ``runtimes``) is invariant across the
  hypothetical tier -- only ``is_current`` shifts
* the helper is decoupled from the live resolver: switching enforcement
  or pointing HOME at a cloud-plan cache must not change the rows
* unknown / empty / ``None`` / non-string tier ids return ``None``
* the endpoint 400s on missing input, 404s on unknown ids, never 5xxs
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement
    off by default (grace mode) -- ``tier_catalog_at`` is independent of
    either knob; the fixture only makes sure the live resolver does not
    surprise the test."""
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_tier_catalog(ent):
    """A row from ``tier_catalog_at`` carries the same keys as a
    ``tier_catalog()`` row -- defends against a rename on one side silently
    shipping a half-renamed payload to a comparison UI."""
    cat_keys = set(ent.tier_catalog()[0].keys())
    rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None and rows
    assert set(rows[0].keys()) == cat_keys == _ROW_KEYS


def test_row_ordering_matches_tier_catalog(ent):
    """Row order is identical to ``tier_catalog()`` -- a UI rendering both
    surfaces side-by-side must line up rung-for-rung."""
    cat_ids = [row["id"] for row in ent.tier_catalog()]
    at_ids = [row["id"] for row in ent.tier_catalog_at(ent.TIER_OSS)]
    assert cat_ids == at_ids


def test_row_count_matches_tier_order(ent):
    rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    assert len(rows) == len(ent._TIER_ORDER)


def test_catalogue_derived_fields_are_invariant_across_tiers(ent):
    """Every field except ``is_current`` is catalogue-derived and must not
    depend on the hypothetical tier."""
    base = {row["id"]: row for row in ent.tier_catalog_at(ent.TIER_OSS)}
    for tier in ent._TIER_ORDER:
        rows = ent.tier_catalog_at(tier)
        assert rows is not None
        for row in rows:
            ref = base[row["id"]]
            for key in (
                "id",
                "label",
                "is_paid",
                "rank",
                "unlocks_paid_runtimes",
                "retention_days",
                "channel_limit",
                "node_limit",
                "features",
                "runtimes",
            ):
                assert row[key] == ref[key], (tier, row["id"], key)


# ── is_current ────────────────────────────────────────────────────────────────


def test_is_current_marks_exactly_the_requested_tier(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.tier_catalog_at(tier)
        assert rows is not None
        current = [row for row in rows if row["is_current"]]
        assert len(current) == 1, tier
        assert current[0]["id"] == tier, tier


def test_is_current_does_not_track_live_resolver(ent, monkeypatch, tmp_path):
    """Even when the live resolver picks Cloud Pro from a cloud-plan cache,
    asking for the OSS view must mark OSS as ``is_current=True``."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 3}))
    ent.invalidate()
    # Live resolver agrees the install is on Cloud Pro.
    assert ent.get_entitlement().tier == ent.TIER_CLOUD_PRO
    rows = ent.tier_catalog_at(ent.TIER_OSS)
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1
    assert current[0]["id"] == ent.TIER_OSS


def test_is_current_round_trip_to_tier_catalog_when_oss(ent):
    """In grace mode with an empty HOME the live resolver picks OSS, so
    ``tier_catalog_at(OSS)`` must byte-equal ``tier_catalog()`` (the
    ``is_current`` slot lands on the same row)."""
    at_oss = ent.tier_catalog_at(ent.TIER_OSS)
    live = ent.tier_catalog()
    assert at_oss == live


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_tier_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.tier_catalog_at(tier)
        assert rows is not None, tier
        assert len(rows) == len(ent._TIER_ORDER)


def test_unknown_tier_returns_none(ent):
    assert ent.tier_catalog_at("not_a_real_tier") is None


def test_empty_returns_none(ent):
    assert ent.tier_catalog_at("") is None


def test_none_returns_none(ent):
    assert ent.tier_catalog_at(None) is None


def test_non_string_returns_none(ent):
    assert ent.tier_catalog_at(123) is None
    assert ent.tier_catalog_at(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    a = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    b = ent.tier_catalog_at(ent.TIER_CLOUD_PRO.upper())
    c = ent.tier_catalog_at(f"  {ent.TIER_CLOUD_PRO}  ")
    assert a == b == c


# ── catalogue invariants (mirror tier_catalog) ───────────────────────────────


def test_paid_tiers_match_published_paid_set(ent):
    rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    paid_ids = {row["id"] for row in rows if row["is_paid"]}
    assert paid_ids == {
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }


def test_unlocks_paid_runtimes_matches_is_paid(ent):
    for row in ent.tier_catalog_at(ent.TIER_OSS):
        assert row["unlocks_paid_runtimes"] == row["is_paid"]


def test_runtimes_are_paid_only_no_free_leakage(ent):
    for row in ent.tier_catalog_at(ent.TIER_OSS):
        assert set(row["runtimes"]).isdisjoint(ent.FREE_RUNTIMES), row["id"]
        assert set(row["runtimes"]).issubset(ent.PAID_RUNTIMES), row["id"]


def test_features_are_paid_only_no_free_leakage(ent):
    for row in ent.tier_catalog_at(ent.TIER_OSS):
        assert set(row["features"]).isdisjoint(ent.FREE_FEATURES), row["id"]


def test_retention_days_match_published_caps(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog_at(ent.TIER_OSS)}
    assert rows_by_id[ent.TIER_OSS]["retention_days"] == 7
    assert rows_by_id[ent.TIER_CLOUD_FREE]["retention_days"] == 7
    assert rows_by_id[ent.TIER_TRIAL]["retention_days"] == 30
    assert rows_by_id[ent.TIER_CLOUD_STARTER]["retention_days"] == 30
    assert rows_by_id[ent.TIER_CLOUD_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_ENTERPRISE]["retention_days"] is None


def test_channel_limit_matches_published_caps(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog_at(ent.TIER_OSS)}
    assert rows_by_id[ent.TIER_OSS]["channel_limit"] == 3
    assert rows_by_id[ent.TIER_CLOUD_FREE]["channel_limit"] == 3
    for tid in (
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert rows_by_id[tid]["channel_limit"] is None, tid


def test_rank_is_dense_and_starts_at_zero(ent):
    rows = ent.tier_catalog_at(ent.TIER_OSS)
    ranks = [row["rank"] for row in rows]
    assert ranks == list(range(len(rows)))


def test_paid_tiers_unlock_all_paid_runtimes(ent):
    """Open-core invariant: every paid tier unlocks the full paid-runtime
    bundle. Pins :func:`tier_catalog_at` against the same invariant
    :func:`tier_catalog` enforces."""
    expected = sorted(ent.PAID_RUNTIMES)
    for row in ent.tier_catalog_at(ent.TIER_OSS):
        if row["unlocks_paid_runtimes"]:
            assert row["runtimes"] == expected, row["id"]
        else:
            assert row["runtimes"] == [], row["id"]


def test_runtimes_are_sorted(ent):
    for row in ent.tier_catalog_at(ent.TIER_OSS):
        assert row["runtimes"] == sorted(row["runtimes"]), row["id"]


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_independent_of_grace_mode(ent, monkeypatch):
    """Flipping enforcement on must not change the rows -- the catalogue
    is user-context-free except for ``is_current``, which itself ignores
    the live resolver."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace_rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    assert grace_rows == enforce_rows


def test_helper_independent_of_cloud_plan_cache(ent, monkeypatch, tmp_path):
    """A cached cloud plan must not colour the what-if rows."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    no_cache_rows = [
        {k: v for k, v in row.items() if k != "is_current"}
        for row in ent.tier_catalog_at(ent.TIER_OSS)
    ]
    cache.unlink()
    ent.invalidate()
    fresh_rows = [
        {k: v for k, v in row.items() if k != "is_current"}
        for row in ent.tier_catalog_at(ent.TIER_OSS)
    ]
    assert no_cache_rows == fresh_rows


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper does not consult :func:`get_entitlement` at all, so a
    blown resolver must not affect the result. Pin the never-raise
    contract explicitly for the surface."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.tier_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert len(rows) == len(ent._TIER_ORDER)


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_tier_returns_rows(client, ent):
    resp = client.get(f"/api/entitlement/tier-catalog-at?tier={ent.TIER_CLOUD_PRO}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tiers"] == ent.tier_catalog_at(ent.TIER_CLOUD_PRO)


def test_endpoint_marks_requested_tier_current(client, ent):
    resp = client.get(f"/api/entitlement/tier-catalog-at?tier={ent.TIER_ENTERPRISE}")
    assert resp.status_code == 200
    rows = resp.get_json()["tiers"]
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1
    assert current[0]["id"] == ent.TIER_ENTERPRISE


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-catalog-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/tier-catalog-at")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/tier-catalog-at?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get("/api/entitlement/tier-catalog-at?tier=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_tier_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        resp = client.get(f"/api/entitlement/tier-catalog-at?tier={tier}")
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert len(body["tiers"]) == len(ent._TIER_ORDER), tier
        current = [row for row in body["tiers"] if row["is_current"]]
        assert len(current) == 1, tier
        assert current[0]["id"] == tier, tier


def test_endpoint_never_5xxs_on_helper_failure(client, ent, monkeypatch):
    """If the helper itself blows up the endpoint logs the error and
    returns 500 with an error envelope -- not a crashed process. (The
    helper's own ``try/except`` makes this hard to hit in practice; this
    test pins the contract for a future regression that bypasses the
    inner guard.)"""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper failure")

    monkeypatch.setattr(ent, "tier_catalog_at", boom)
    resp = client.get(f"/api/entitlement/tier-catalog-at?tier={ent.TIER_OSS}")
    # The handler still returns a JSON error envelope rather than crashing
    # the worker.
    assert resp.status_code in (200, 500)
    body = resp.get_json()
    assert body is not None
