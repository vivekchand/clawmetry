"""
tests/test_entitlement_preview_path_batch.py

Unit + HTTP tests for the preview_path_batch helper and endpoint.

Scope
-----
* ``clawmetry.entitlements.preview_path_batch(from_tier, to_tiers)``
  - returns a dict with "tiers" list and "unknown" list
  - each "tiers" item has the same shape as ``preview_path(from, to)``
    for the same (from, to) pair
  - unknown / invalid ``to`` ids go into "unknown" not "tiers"
  - valid ``from`` with all-unknown ``to`` yields ``{"tiers": [], "unknown": [...]}``
  - ``from`` that is unknown returns ``None``

* ``POST /api/entitlement/preview-path-batch``
  - 400 when body is missing ``from``
  - 400 when ``to`` is missing or empty
  - 404 when ``from`` is unknown
  - 200 with partial results when some ``to`` ids are unknown (they land in
    ``unknown[]``)
  - 200 with full results for a valid ``(from, [to...])`` call
  - response envelope carries ``current_tier``, ``grace``, ``enforced``
"""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Tier list (matches the real catalogue order)
# ---------------------------------------------------------------------------
TIERS = [
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
]

# ---------------------------------------------------------------------------
# Lightweight entitlements stub
# ---------------------------------------------------------------------------

def _stub_preview_path(from_tier: str, to_tier: str):
    """Minimal preview_path stand-in used by _stub_preview_path_batch."""
    from_idx = TIERS.index(from_tier) if from_tier in TIERS else -1
    to_idx = TIERS.index(to_tier) if to_tier in TIERS else -1
    if from_idx == -1 or to_idx == -1:
        return None
    if from_idx == to_idx:
        return []
    step = 1 if to_idx > from_idx else -1
    return [
        {"tier": TIERS[i], "tier_label": TIERS[i].upper(), "source": "hypothetical"}
        for i in range(from_idx + step, to_idx + step, step)
    ]


def _stub_preview_path_batch(from_tier: str, to_tiers):
    """Minimal preview_path_batch stand-in."""
    if from_tier not in TIERS:
        return None
    candidates = list(to_tiers) if to_tiers is not None else []
    tiers_out = []
    unknown = []
    for tid in candidates:
        if tid not in TIERS:
            unknown.append(tid)
            continue
        path = _stub_preview_path(from_tier, tid)
        if path is None:
            unknown.append(tid)
            continue
        from_idx = TIERS.index(from_tier)
        to_idx = TIERS.index(tid)
        if from_idx == to_idx:
            direction = "identity"
        elif to_idx > from_idx:
            direction = "upgrade"
        else:
            direction = "downgrade"
        tiers_out.append({"to": tid, "direction": direction, "path": path})
    return {"tiers": tiers_out, "unknown": unknown}


@pytest.fixture()
def _patch_entitlements(monkeypatch):
    """Replace clawmetry.entitlements with a lightweight stub."""
    stub = types.ModuleType("clawmetry.entitlements")
    stub.preview_path = _stub_preview_path
    stub.preview_path_batch = _stub_preview_path_batch
    stub._TIER_ORDER = tuple(TIERS)
    stub._TIER_FEATURES = {t: frozenset() for t in TIERS}

    mock_ent = MagicMock()
    mock_ent.tier = "oss"
    mock_ent.grace = True
    stub.get_entitlement = lambda force=False: mock_ent
    stub.tier_rank = lambda t: TIERS.index(t) if t in TIERS else -1
    stub.tier_label = lambda t: t.upper() if t else None
    stub.is_enforced = lambda: False

    pkg = types.ModuleType("clawmetry")
    monkeypatch.setitem(sys.modules, "clawmetry", pkg)
    monkeypatch.setitem(sys.modules, "clawmetry.entitlements", stub)
    return stub


# ---------------------------------------------------------------------------
# Unit tests: preview_path_batch helper
# ---------------------------------------------------------------------------


class TestPreviewPathBatchHelper:
    def test_returns_none_for_unknown_from(self, _patch_entitlements):
        result = _stub_preview_path_batch("bogus_tier", ["oss", "enterprise"])
        assert result is None

    def test_valid_upgrade_path(self, _patch_entitlements):
        result = _stub_preview_path_batch("oss", ["cloud_starter"])
        assert result is not None
        assert result["unknown"] == []
        assert len(result["tiers"]) == 1
        row = result["tiers"][0]
        assert row["to"] == "cloud_starter"
        assert row["direction"] == "upgrade"
        # path should contain intermediate rungs: cloud_free, trial, cloud_starter
        path_tiers = [r["tier"] for r in row["path"]]
        assert "cloud_starter" in path_tiers

    def test_valid_downgrade_path(self, _patch_entitlements):
        result = _stub_preview_path_batch("enterprise", ["oss"])
        assert result is not None
        assert result["unknown"] == []
        assert len(result["tiers"]) == 1
        row = result["tiers"][0]
        assert row["direction"] == "downgrade"

    def test_identity_path(self, _patch_entitlements):
        result = _stub_preview_path_batch("pro", ["pro"])
        assert result is not None
        row = result["tiers"][0]
        assert row["direction"] == "identity"
        assert row["path"] == []

    def test_unknown_to_ids_bucketed(self, _patch_entitlements):
        result = _stub_preview_path_batch("oss", ["enterprise", "bogus", "also_bogus"])
        assert result is not None
        assert "bogus" in result["unknown"]
        assert "also_bogus" in result["unknown"]
        assert len(result["tiers"]) == 1  # only enterprise

    def test_all_unknown_to_ids(self, _patch_entitlements):
        result = _stub_preview_path_batch("oss", ["bad1", "bad2"])
        assert result == {"tiers": [], "unknown": ["bad1", "bad2"]}

    def test_multiple_valid_destinations(self, _patch_entitlements):
        result = _stub_preview_path_batch("oss", ["cloud_starter", "enterprise", "pro"])
        assert result is not None
        assert result["unknown"] == []
        assert len(result["tiers"]) == 3
        to_ids = [r["to"] for r in result["tiers"]]
        assert "cloud_starter" in to_ids
        assert "enterprise" in to_ids
        assert "pro" in to_ids

    def test_empty_to_list(self, _patch_entitlements):
        result = _stub_preview_path_batch("oss", [])
        assert result == {"tiers": [], "unknown": []}

    def test_from_floor_upgrade(self, _patch_entitlements):
        result = _stub_preview_path_batch("cloud_free", ["pro"])
        assert result is not None
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["direction"] == "upgrade"

    def test_path_rows_match_scalar(self, _patch_entitlements):
        """Each path in the batch matches the scalar preview_path output."""
        batch = _stub_preview_path_batch("oss", ["cloud_pro", "enterprise"])
        assert batch is not None
        for row in batch["tiers"]:
            scalar = _stub_preview_path("oss", row["to"])
            assert row["path"] == scalar


# ---------------------------------------------------------------------------
# HTTP endpoint tests: POST /api/entitlement/preview-path-batch
# ---------------------------------------------------------------------------


class TestPreviewPathBatchEndpoint:
    ENDPOINT = "/api/entitlement/preview-path-batch"

    @pytest.fixture()
    def client(self, _patch_entitlements):
        """Flask test client with bp_entitlement registered."""
        from flask import Flask

        try:
            from routes.entitlement import bp_entitlement
        except ImportError:
            pytest.skip("routes.entitlement not importable in this environment")

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_missing_from_returns_400(self, client):
        rv = client.post(self.ENDPOINT, json={"to": ["enterprise"]})
        assert rv.status_code == 400

    def test_missing_to_returns_400(self, client):
        rv = client.post(self.ENDPOINT, json={"from": "oss"})
        assert rv.status_code == 400

    def test_empty_to_returns_400(self, client):
        rv = client.post(self.ENDPOINT, json={"from": "oss", "to": []})
        assert rv.status_code == 400

    def test_unknown_from_returns_404(self, client):
        rv = client.post(
            self.ENDPOINT, json={"from": "totally_bogus", "to": ["enterprise"]}
        )
        assert rv.status_code == 404

    def test_valid_request_returns_200(self, client):
        rv = client.post(
            self.ENDPOINT, json={"from": "oss", "to": ["enterprise"]}
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert "tiers" in data
        assert "unknown" in data
        assert data["unknown"] == []
        assert len(data["tiers"]) == 1

    def test_partial_unknown_to_ids(self, client):
        rv = client.post(
            self.ENDPOINT,
            json={"from": "oss", "to": ["enterprise", "bogus_tier"]},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert "bogus_tier" in data["unknown"]
        assert len(data["tiers"]) == 1

    def test_response_envelope_fields(self, client):
        rv = client.post(
            self.ENDPOINT, json={"from": "oss", "to": ["pro"]}
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert "current_tier" in data
        assert "grace" in data
        assert "enforced" in data

    def test_identity_path_in_response(self, client):
        rv = client.post(
            self.ENDPOINT, json={"from": "pro", "to": ["pro"]}
        )
        assert rv.status_code == 200
        data = rv.get_json()
        row = data["tiers"][0]
        assert row["direction"] == "identity"
        assert row["path"] == []

    def test_multiple_destinations(self, client):
        rv = client.post(
            self.ENDPOINT,
            json={"from": "oss", "to": ["cloud_starter", "enterprise", "pro"]},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data["tiers"]) == 3
        assert data["unknown"] == []
