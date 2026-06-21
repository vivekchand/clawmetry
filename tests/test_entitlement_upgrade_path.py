"""Tests for ``clawmetry.entitlements.upgrade_path`` +
``GET /api/entitlement/upgrade-path``.

Where :func:`tier_unlocks` answers "what does tier X unlock vs the tier
below it" for one named tier, ``upgrade_path`` answers the
current-user-relative question: "which purchasable tiers are still
*above* my current tier, and what does each one unlock?"

Coverage
--------
* Module-level ``upgrade_path()`` returns a list.
* OSS tier -> all four purchasable tiers above rank 0 appear in order.
* Enterprise (top) -> empty list.
* Starter -> only Pro + Enterprise appear.
* Row shape matches ``tier_unlocks`` shape exactly.
* Resolver error falls back to ``[]``.
* HTTP route ``GET /api/entitlement/upgrade-path`` returns 200 + list.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ent_module():
    """Import clawmetry.entitlements; skip the test if not installed."""
    pytest.importorskip("clawmetry.entitlements")
    import clawmetry.entitlements as e

    return e


@pytest.fixture()
def oss_tier(ent_module, monkeypatch):
    """Pin the resolved entitlement to OSS free."""
    e = ent_module
    oss = e._oss_free()
    monkeypatch.setattr(e, "get_entitlement", lambda force=False: oss)
    return oss


@pytest.fixture()
def enterprise_tier(ent_module, monkeypatch):
    """Pin the resolved entitlement to Enterprise."""
    e = ent_module
    ent = e._build(e.TIER_ENTERPRISE, "test", node_limit=0)
    monkeypatch.setattr(e, "get_entitlement", lambda force=False: ent)
    return ent


@pytest.fixture()
def starter_tier(ent_module, monkeypatch):
    """Pin the resolved entitlement to Cloud Starter."""
    e = ent_module
    ent = e._build(e.TIER_CLOUD_STARTER, "test")
    monkeypatch.setattr(e, "get_entitlement", lambda force=False: ent)
    return ent


# ---------------------------------------------------------------------------
# upgrade_path() -- module-level function
# ---------------------------------------------------------------------------


class TestUpgradePath:
    def test_returns_list(self, ent_module, oss_tier):
        result = ent_module.upgrade_path()
        assert isinstance(result, list)

    def test_oss_sees_all_higher_tiers(self, ent_module, oss_tier):
        """OSS rank=0; every purchasable tier above rank 0 must appear."""
        result = ent_module.upgrade_path()
        returned_tiers = {row["tier"] for row in result}
        # cloud_starter (rank 1), cloud_pro (rank 2), pro (rank 2), enterprise (rank 3)
        assert ent_module.TIER_CLOUD_STARTER in returned_tiers
        assert ent_module.TIER_CLOUD_PRO in returned_tiers
        assert ent_module.TIER_PRO in returned_tiers
        assert ent_module.TIER_ENTERPRISE in returned_tiers

    def test_oss_does_not_include_oss_or_cloud_free(self, ent_module, oss_tier):
        result = ent_module.upgrade_path()
        returned_tiers = {row["tier"] for row in result}
        assert ent_module.TIER_OSS not in returned_tiers
        assert ent_module.TIER_CLOUD_FREE not in returned_tiers

    def test_enterprise_returns_empty(self, ent_module, enterprise_tier):
        result = ent_module.upgrade_path()
        assert result == []

    def test_starter_excludes_lower_tiers(self, ent_module, starter_tier):
        """Starter is rank 1; only rank > 1 tiers (Pro, Enterprise) appear."""
        result = ent_module.upgrade_path()
        returned_tiers = {row["tier"] for row in result}
        assert ent_module.TIER_OSS not in returned_tiers
        assert ent_module.TIER_CLOUD_FREE not in returned_tiers
        assert ent_module.TIER_CLOUD_STARTER not in returned_tiers
        # Pro and Enterprise must be present
        assert ent_module.TIER_CLOUD_PRO in returned_tiers or ent_module.TIER_PRO in returned_tiers
        assert ent_module.TIER_ENTERPRISE in returned_tiers

    def test_row_shape_matches_tier_unlocks(self, ent_module, oss_tier):
        """Every row must carry the same keys as tier_unlocks() returns."""
        result = ent_module.upgrade_path()
        assert result, "expected non-empty for OSS"
        expected_keys = {
            "tier",
            "tier_label",
            "tier_rank",
            "previous_tier",
            "previous_tier_label",
            "previous_tier_rank",
            "features",
            "runtimes",
        }
        for row in result:
            assert expected_keys <= set(row.keys()), (
                f"Row for {row.get('tier')} missing keys: "
                f"{expected_keys - set(row.keys())}"
            )

    def test_rows_sorted_ascending(self, ent_module, oss_tier):
        """Rows must be sorted cheapest -> most capable (tier_rank non-decreasing)."""
        result = ent_module.upgrade_path()
        ranks = [row["tier_rank"] for row in result]
        assert ranks == sorted(ranks), f"upgrade_path rows not sorted: {ranks}"

    def test_trial_excluded(self, ent_module, oss_tier):
        """TIER_TRIAL is not purchasable and must not appear."""
        result = ent_module.upgrade_path()
        returned_tiers = {row["tier"] for row in result}
        assert ent_module.TIER_TRIAL not in returned_tiers

    def test_resolver_error_returns_empty(self, ent_module, monkeypatch):
        """Any exception from get_entitlement must collapse to []."""

        def _boom(force=False):
            raise RuntimeError("simulated resolver failure")

        monkeypatch.setattr(ent_module, "get_entitlement", _boom)
        result = ent_module.upgrade_path()
        assert result == []

    def test_features_are_sorted_lists(self, ent_module, oss_tier):
        result = ent_module.upgrade_path()
        for row in result:
            assert isinstance(row["features"], list)
            assert row["features"] == sorted(row["features"])
            assert isinstance(row["runtimes"], list)
            assert row["runtimes"] == sorted(row["runtimes"])


# ---------------------------------------------------------------------------
# HTTP route -- GET /api/entitlement/upgrade-path
# ---------------------------------------------------------------------------


class TestUpgradePathRoute:
    @pytest.fixture()
    def client(self):
        """Minimal Flask test client wired to bp_entitlement."""
        pytest.importorskip("flask")
        pytest.importorskip("clawmetry.entitlements")
        from flask import Flask
        from routes.entitlement import bp_entitlement

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_route_200(self, client, ent_module, oss_tier):
        resp = client.get("/api/entitlement/upgrade-path")
        assert resp.status_code == 200

    def test_route_returns_list(self, client, ent_module, oss_tier):
        resp = client.get("/api/entitlement/upgrade-path")
        data = resp.get_json()
        assert isinstance(data, list)

    def test_route_oss_non_empty(self, client, ent_module, oss_tier):
        resp = client.get("/api/entitlement/upgrade-path")
        data = resp.get_json()
        assert len(data) > 0

    def test_route_enterprise_empty(self, client, ent_module, enterprise_tier):
        resp = client.get("/api/entitlement/upgrade-path")
        data = resp.get_json()
        assert data == []

    def test_route_row_has_expected_keys(self, client, ent_module, oss_tier):
        resp = client.get("/api/entitlement/upgrade-path")
        data = resp.get_json()
        assert data
        expected_keys = {"tier", "tier_label", "tier_rank", "features", "runtimes"}
        for row in data:
            assert expected_keys <= set(row.keys())
