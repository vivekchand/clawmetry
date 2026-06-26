"""Tests for ``tier_label`` / ``tier_rank`` / ``tier_catalog`` -- the
deterministic per-tier ladder helpers the pricing-comparison UI reads
to render every tier in the open-core ladder off ONE round-trip, plus
the companion ``/api/entitlement/tier-catalog`` endpoint.

Pins covered here:

* :data:`TIER_LABELS` has a display string for every tier in
  :data:`_TIER_ORDER` -- the UI never has to fall back to the raw id
* :func:`tier_label` falls back to a Title-cased id for unknown tiers
  so an unknown tier still renders with something
* :func:`tier_rank` returns -1 for unknown / empty / non-string input
  and never raises on garbage
* :func:`tier_catalog` walks :data:`_TIER_ORDER` in declaration order
  -- pinned per known id so a reshuffle of the static ladder cannot
  silently change the dropdown
* every catalog row carries the same eight keys -- shape lock
* free-tier rows (OSS / Cloud Free) carry only the free runtimes;
  paid-tier rows carry FREE_RUNTIMES ∪ PAID_RUNTIMES
* every catalog row's ``features`` includes the full :data:`FREE_FEATURES`
  set on top of the per-tier paid grants (free features are always on)
* the ``current`` flag flips on exactly the row matching the resolved
  entitlement's tier; the rest are False
* catalog is catalogue-derived -- flipping ``CLAWMETRY_ENFORCE`` on
  does NOT change the per-tier rows (only the ``current`` flag depends
  on the resolver)
* helpers never raise on garbage input
* the API endpoint surfaces the same body with ``current`` / ``grace``
  / ``enforced`` envelope flags
* a resolver failure short-circuits to an OSS-free envelope, never 5xx
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement
    off by default (grace mode) -- the catalog is catalogue-derived and
    independent of the resolver, so the fixture only needs to keep the live
    resolver from surprising the test."""
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
    "rank",
    "paid",
    "current",
    "features",
    "runtimes",
    "retention_days",
}

_ENVELOPE_KEYS = {"tiers", "current", "grace", "enforced"}


# ── TIER_LABELS / tier_label ────────────────────────────────────────────────


def test_tier_labels_cover_every_known_tier(ent):
    # The frontend pricing card never falls back to the raw id for any tier
    # the install ships with knowing about.
    for tid in ent._TIER_ORDER:
        assert tid in ent.TIER_LABELS, tid
        assert ent.TIER_LABELS[tid].strip() != "", tid


def test_tier_label_returns_known_label(ent):
    assert ent.tier_label(ent.TIER_OSS) == "OSS"
    assert ent.tier_label(ent.TIER_ENTERPRISE) == "Enterprise"
    assert ent.tier_label(ent.TIER_CLOUD_PRO) == "Cloud Pro"


def test_tier_label_trims_and_lowercases(ent):
    assert ent.tier_label("  OSS  ") == "OSS"
    assert ent.tier_label("ENTERPRISE") == "Enterprise"


def test_tier_label_falls_back_for_unknown(ent):
    # Title-cased id with underscores -> spaces, so the UI gets *something*.
    assert ent.tier_label("custom_plan") == "Custom Plan"


@pytest.mark.parametrize("bad", ["", "  ", None])
def test_tier_label_blank_returns_empty(ent, bad):
    assert ent.tier_label(bad) == ""


# ── tier_rank ────────────────────────────────────────────────────────────────


def test_tier_rank_values(ent):
    # Pinned ladder so a reshuffle of the static ranks cannot silently
    # change the pricing sort order.
    assert ent.tier_rank(ent.TIER_OSS) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_FREE) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_STARTER) == 1
    assert ent.tier_rank(ent.TIER_TRIAL) == 2
    assert ent.tier_rank(ent.TIER_CLOUD_PRO) == 2
    assert ent.tier_rank(ent.TIER_PRO) == 2
    assert ent.tier_rank(ent.TIER_ENTERPRISE) == 3


def test_tier_rank_trims_and_lowercases(ent):
    assert ent.tier_rank("  OSS  ") == 0


@pytest.mark.parametrize("bad", ["", "  ", None, "bogus", "BOGUS"])
def test_tier_rank_returns_minus_one_on_bad_input(ent, bad):
    assert ent.tier_rank(bad) == -1


def test_tier_rank_never_raises_on_garbage(ent):
    # Non-string input must not propagate the AttributeError -- the
    # gate-adjacent helpers all use the trim/lower idiom defensively.
    assert ent.tier_rank(0) == -1
    assert ent.tier_rank(1.5) == -1


# ── tier_catalog ─────────────────────────────────────────────────────────────


def test_catalog_walks_static_order(ent):
    cat = ent.tier_catalog()
    assert [row["id"] for row in cat] == list(ent._TIER_ORDER)


def test_catalog_row_shape(ent):
    for row in ent.tier_catalog():
        assert set(row.keys()) == _ROW_KEYS, row["id"]
        assert isinstance(row["features"], list)
        assert isinstance(row["runtimes"], list)
        assert isinstance(row["paid"], bool)
        assert isinstance(row["current"], bool)


def test_catalog_features_sorted_and_include_free(ent):
    for row in ent.tier_catalog():
        # Sorted determinism so the dashboard JSON is byte-stable.
        assert row["features"] == sorted(row["features"]), row["id"]
        # Free features are always on -- a row missing them would be a
        # silent regression that flipped /api/entitlement.allows_feature
        # for some baseline cap.
        assert frozenset(ent.FREE_FEATURES).issubset(row["features"]), row["id"]


def test_catalog_runtimes_sorted(ent):
    for row in ent.tier_catalog():
        assert row["runtimes"] == sorted(row["runtimes"]), row["id"]


def test_catalog_free_rows_only_have_free_runtimes(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog()}
    for tid in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert rows_by_id[tid]["runtimes"] == sorted(ent.FREE_RUNTIMES)
        assert rows_by_id[tid]["paid"] is False


def test_catalog_paid_rows_have_all_runtimes(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog()}
    for tid in (
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert rows_by_id[tid]["runtimes"] == sorted(ent.ALL_RUNTIMES), tid
        assert rows_by_id[tid]["paid"] is True


def test_catalog_paid_flag_matches_paid_tiers(ent):
    for row in ent.tier_catalog():
        assert row["paid"] is (row["id"] in ent._PAID_TIERS), row["id"]


def test_catalog_retention_days_per_tier(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog()}
    assert rows_by_id[ent.TIER_OSS]["retention_days"] == 7
    assert rows_by_id[ent.TIER_CLOUD_FREE]["retention_days"] == 7
    assert rows_by_id[ent.TIER_CLOUD_STARTER]["retention_days"] == 30
    assert rows_by_id[ent.TIER_TRIAL]["retention_days"] == 30
    assert rows_by_id[ent.TIER_CLOUD_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_ENTERPRISE]["retention_days"] is None


def test_catalog_current_flag_marks_oss_on_oss_install(ent):
    cat = ent.tier_catalog()
    current_rows = [row for row in cat if row["current"]]
    # OSS-free fallback -> exactly one row carries current=True.
    assert len(current_rows) == 1
    assert current_rows[0]["id"] == ent.TIER_OSS


def test_catalog_current_flag_follows_resolved_tier(ent, monkeypatch):
    # Swap the resolver to a higher tier and the flag must move with it.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda *_, **__: ent._build(ent.TIER_CLOUD_PRO, "cloud", node_limit=5),
    )
    cat = ent.tier_catalog()
    current_rows = [row for row in cat if row["current"]]
    assert len(current_rows) == 1
    assert current_rows[0]["id"] == ent.TIER_CLOUD_PRO


def test_catalog_rows_identical_under_grace_and_enforce(ent, monkeypatch):
    # Catalogue-derived -- only the `current` flag depends on the resolver,
    # never the per-tier features/runtimes/retention slice.
    grace_rows = [
        {k: v for k, v in row.items() if k != "current"} for row in ent.tier_catalog()
    ]
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_rows = [
        {k: v for k, v in row.items() if k != "current"} for row in ent.tier_catalog()
    ]
    assert enforce_rows == grace_rows


def test_catalog_never_raises_when_resolver_fails(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    # Catalog still surfaces every tier; current flag collapses to OSS.
    cat = ent.tier_catalog()
    assert [row["id"] for row in cat] == list(ent._TIER_ORDER)
    current_rows = [row for row in cat if row["current"]]
    assert len(current_rows) == 1
    assert current_rows[0]["id"] == ent.TIER_OSS


# ── API: /api/entitlement/tier-catalog ──────────────────────────────────────


def test_tier_catalog_endpoint_envelope(client, ent):
    rv = client.get("/api/entitlement/tier-catalog")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current"] == ent.TIER_OSS
    assert body["grace"] is True
    assert body["enforced"] is False
    # Same body as the module-level helper.
    assert body["tiers"] == ent.tier_catalog()


def test_tier_catalog_endpoint_rows_match_helper(client, ent):
    rv = client.get("/api/entitlement/tier-catalog")
    rows = rv.get_json()["tiers"]
    assert [row["id"] for row in rows] == list(ent._TIER_ORDER)
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS


def test_tier_catalog_endpoint_never_raises_on_resolver_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    monkeypatch.setattr(ent, "tier_catalog", boom)
    rv = client.get("/api/entitlement/tier-catalog")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tiers"] == []
    assert body["current"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


def test_tier_catalog_endpoint_enforced_envelope(client, ent, monkeypatch):
    # Pretend enforcement is on -- the envelope flips grace/enforced but the
    # per-row body still matches the helper.
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    rv = client.get("/api/entitlement/tier-catalog")
    body = rv.get_json()
    assert body["grace"] is False
    assert body["enforced"] is True
    assert body["tiers"] == ent.tier_catalog()
