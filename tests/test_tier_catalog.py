"""Tests for the tier catalogue helpers in clawmetry/entitlements.py.

Pins:

* :data:`TIER_LABELS` covers every tier id ``Entitlement.tier`` can take.
* :func:`tier_label` returns the label for known ids, title-cases unknown ids
  (so a future plan code still renders with *something*), and falls back to the
  OSS label for empty / ``None`` input (never-crash contract).
* :func:`tier_catalog` returns one row per tier in the published ladder order,
  marks exactly one row ``is_current``, never raises, and is internally
  consistent with the per-tier feature / runtime / retention maps.

Plus an integration test for :func:`routes.entitlement.api_tiers` that confirms
the wire shape and the never-raise fallback.

Companion to ``tests/test_entitlements.py`` (grace/enforce mechanics) and
``tests/test_entitlements_catalogue.py`` (feature / retention buckets).
"""
from __future__ import annotations

import importlib
import json

import pytest


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


# -- tier_label ----------------------------------------------------------------


def test_tier_label_known_tier_ids_return_their_label(ent):
    assert ent.tier_label(ent.TIER_OSS) == "OSS"
    assert ent.tier_label(ent.TIER_CLOUD_FREE) == "Free"
    assert ent.tier_label(ent.TIER_TRIAL) == "Trial"
    assert ent.tier_label(ent.TIER_CLOUD_STARTER) == "Starter"
    assert ent.tier_label(ent.TIER_CLOUD_PRO) == "Pro"
    assert ent.tier_label(ent.TIER_PRO) == "Self-hosted Pro"
    assert ent.tier_label(ent.TIER_ENTERPRISE) == "Enterprise"


def test_tier_label_unknown_tier_title_cases(ent):
    # A future plan code added to ``Entitlement.tier`` but not yet in
    # TIER_LABELS still renders human-readable instead of leaking the raw
    # snake_case id into the UI.
    assert ent.tier_label("not_a_real_tier") == "Not A Real Tier"


def test_tier_label_handles_empty_and_none(ent):
    # Empty / None fall back to the OSS label so the dashboard's
    # "current tier" pill never renders as a blank string while the
    # entitlement is still resolving.
    oss_label = ent.TIER_LABELS[ent.TIER_OSS]
    assert ent.tier_label("") == oss_label
    assert ent.tier_label(None) == oss_label


def test_tier_label_is_case_insensitive(ent):
    assert ent.tier_label("CLOUD_PRO") == "Pro"
    assert ent.tier_label(" Cloud_Starter ") == "Starter"


def test_tier_labels_cover_every_known_tier(ent):
    """Every TIER_* constant exported by entitlements.py must have a label so
    the upgrade-ladder UI never has to fall back to a raw tier id for a tier
    we already know about. New tiers MUST add a TIER_LABELS entry to keep this
    test green."""
    known = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert known.issubset(set(ent.TIER_LABELS.keys()))


# -- tier_catalog --------------------------------------------------------------


def test_tier_catalog_returns_one_row_per_known_tier(ent):
    rows = ent.tier_catalog()
    ids = [row["id"] for row in rows]
    expected_known = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert expected_known.issubset(set(ids))
    assert len(ids) == len(set(ids))


def test_tier_catalog_order_is_oss_first_enterprise_last(ent):
    rows = ent.tier_catalog()
    assert rows[0]["id"] == ent.TIER_OSS
    assert rows[-1]["id"] == ent.TIER_ENTERPRISE
    ranks = [row["rank"] for row in rows]
    assert ranks == list(range(len(rows)))


def test_tier_catalog_marks_exactly_one_current_in_grace(ent):
    rows = ent.tier_catalog()
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1
    assert current[0]["id"] == ent.TIER_OSS


def test_tier_catalog_is_paid_matches_paid_tiers(ent):
    rows = ent.tier_catalog()
    paid_ids = {row["id"] for row in rows if row["is_paid"]}
    assert paid_ids == {
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }


def test_tier_catalog_unlocks_paid_runtimes_matches_is_paid(ent):
    """A paid tier always unlocks the paid runtime bundle (the open-core
    invariant). A free tier never does."""
    for row in ent.tier_catalog():
        assert row["unlocks_paid_runtimes"] == row["is_paid"]


def test_tier_catalog_retention_days_match_published_caps(ent):
    rows_by_id = {row["id"]: row for row in ent.tier_catalog()}
    assert rows_by_id[ent.TIER_OSS]["retention_days"] == 7
    assert rows_by_id[ent.TIER_CLOUD_FREE]["retention_days"] == 7
    assert rows_by_id[ent.TIER_TRIAL]["retention_days"] == 30
    assert rows_by_id[ent.TIER_CLOUD_STARTER]["retention_days"] == 30
    assert rows_by_id[ent.TIER_CLOUD_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_PRO]["retention_days"] == 90
    assert rows_by_id[ent.TIER_ENTERPRISE]["retention_days"] is None


def test_tier_catalog_features_are_paid_only_no_free_leakage(ent):
    for row in ent.tier_catalog():
        assert set(row["features"]).isdisjoint(ent.FREE_FEATURES)


def test_tier_catalog_channel_limit_matches_published_caps(ent):
    """Free / OSS caps at 3 (the ``all_channels`` Starter unlock has teeth);
    every paid tier is unlimited (``None``). Mirrors
    ``_TIER_CHANNEL_LIMIT`` so the UI gets the same value the route gate
    will eventually enforce."""
    rows_by_id = {row["id"]: row for row in ent.tier_catalog()}
    assert rows_by_id[ent.TIER_OSS]["channel_limit"] == 3
    assert rows_by_id[ent.TIER_CLOUD_FREE]["channel_limit"] == 3
    assert rows_by_id[ent.TIER_TRIAL]["channel_limit"] is None
    assert rows_by_id[ent.TIER_CLOUD_STARTER]["channel_limit"] is None
    assert rows_by_id[ent.TIER_CLOUD_PRO]["channel_limit"] is None
    assert rows_by_id[ent.TIER_PRO]["channel_limit"] is None
    assert rows_by_id[ent.TIER_ENTERPRISE]["channel_limit"] is None


def test_tier_catalog_runtimes_are_paid_only_no_free_leakage(ent):
    """Symmetric with ``features``: each row lists only the paid runtimes the
    tier grants -- free runtimes are implicit-everywhere and never repeated
    on the upgrade-ladder rows."""
    for row in ent.tier_catalog():
        assert set(row["runtimes"]).isdisjoint(ent.FREE_RUNTIMES), row["id"]
        assert set(row["runtimes"]).issubset(ent.PAID_RUNTIMES), row["id"]


def test_tier_catalog_paid_tiers_unlock_all_paid_runtimes(ent):
    """Open-core invariant: every paid tier unlocks the full paid-runtime
    bundle (all paid runtimes ship together via the Starter ``multi_runtime``
    grant). Pins this against the ``unlocks_paid_runtimes`` flag so the two
    columns can never drift."""
    expected = sorted(ent.PAID_RUNTIMES)
    for row in ent.tier_catalog():
        if row["unlocks_paid_runtimes"]:
            assert row["runtimes"] == expected, row["id"]
        else:
            assert row["runtimes"] == [], row["id"]


def test_tier_catalog_runtimes_are_sorted(ent):
    """Stable display order: paid runtimes are returned sorted so the UI
    list is deterministic across reloads (same contract as ``features``)."""
    for row in ent.tier_catalog():
        assert row["runtimes"] == sorted(row["runtimes"]), row["id"]


def test_tier_catalog_marks_active_paid_tier_when_license_resolves(ent, monkeypatch, tmp_path):
    """A cloud-plan cache file lights up the matching tier as current."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 3}))
    ent.invalidate()
    rows = ent.tier_catalog()
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1
    assert current[0]["id"] == ent.TIER_CLOUD_PRO


def test_tier_catalog_never_raises_on_resolution_failure(ent, monkeypatch):
    """If get_entitlement explodes, tier_catalog still returns the ladder with
    OSS as the (default) current row -- never propagates an exception."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated entitlement failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.tier_catalog()
    assert any(row["id"] == ent.TIER_OSS for row in rows)
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1
    assert current[0]["id"] == ent.TIER_OSS


# -- /api/tiers endpoint -------------------------------------------------------


@pytest.fixture
def client(ent):
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def test_api_tiers_returns_ladder_shape(client, ent):
    resp = client.get("/api/tiers")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "tiers" in body and isinstance(body["tiers"], list) and body["tiers"]
    assert body["current"] == ent.TIER_OSS
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["tiers"][0]["id"] == ent.TIER_OSS
    assert body["tiers"][-1]["id"] == ent.TIER_ENTERPRISE


def test_api_tiers_falls_back_on_internal_error(client, ent, monkeypatch):
    """If both ``get_entitlement`` AND ``tier_catalog`` explode the route still
    returns 200 with the safe OSS-free fallback (never 5xx)."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated catalog failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    monkeypatch.setattr(ent, "tier_catalog", boom)
    resp = client.get("/api/tiers")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["tiers"] == []
