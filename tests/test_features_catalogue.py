"""Tests for the feature catalogue helpers + ``/api/features`` endpoint.

Companion to ``tests/test_entitlements_catalogue.py`` (which pins the
per-tier feature sets) and ``tests/test_routes_runtimes.py`` (which covers
the runtime catalog endpoint). Where those tests guard the upstream catalogue
and the runtime API surface, this file guards the *feature* catalogue helpers
and the new ``/api/features`` route that the dashboard reads to render a
paywall/upgrade table for every known feature.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module + clean HOME, no enforce flag set."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement against a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── feature_label() ──────────────────────────────────────────────────────────


def test_feature_label_known_keys(ent):
    """Every known feature in the catalogue has a non-blank label."""
    for fid in ent.ALL_FEATURES:
        label = ent.feature_label(fid)
        assert isinstance(label, str)
        assert label.strip(), f"label for {fid!r} is blank"


def test_feature_label_falls_back_to_humanised_id(ent):
    """Unknown feature ids degrade gracefully into a humanised label."""
    assert ent.feature_label("brand_new_thing") == "Brand new thing"


def test_feature_label_handles_empty_and_none(ent):
    assert ent.feature_label("") == ""
    assert ent.feature_label(None) == ""


# ── feature_tier() ───────────────────────────────────────────────────────────


def test_feature_tier_classifies_free(ent):
    for fid in ent.FREE_FEATURES:
        assert ent.feature_tier(fid) == "free", fid


def test_feature_tier_classifies_starter(ent):
    for fid in ent.STARTER_FEATURES:
        assert ent.feature_tier(fid) == "starter", fid


def test_feature_tier_classifies_pro(ent):
    for fid in ent.PRO_ONLY_FEATURES:
        assert ent.feature_tier(fid) == "pro", fid


def test_feature_tier_classifies_enterprise(ent):
    for fid in ent.ENTERPRISE_FEATURES:
        assert ent.feature_tier(fid) == "enterprise", fid


def test_feature_tier_unknown_defaults_to_pro(ent):
    """Unknown feature ids default to ``pro`` so the UI errs on the side of
    showing a lock affordance rather than silently leaking access."""
    assert ent.feature_tier("never_heard_of_this") == "pro"


# ── feature_catalog() ────────────────────────────────────────────────────────


def test_feature_catalog_includes_every_known_feature(ent):
    """Catalog must cover every key in ALL_FEATURES exactly once."""
    cat = ent.feature_catalog()
    ids = [row["id"] for row in cat]
    assert sorted(ids) == sorted(ent.ALL_FEATURES)
    assert len(ids) == len(set(ids)), "duplicate feature ids in catalog"


def test_feature_catalog_row_shape_is_stable(ent):
    """Each row carries the keys the frontend reads — defends against an
    accidental rename breaking the paywall table."""
    cat = ent.feature_catalog()
    for row in cat:
        for key in ("id", "label", "tier", "free", "allowed", "locked"):
            assert key in row, row
        assert isinstance(row["id"], str)
        assert isinstance(row["label"], str)
        assert row["tier"] in ("free", "starter", "pro", "enterprise"), row
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        # locked = paid-and-not-allowed; mutually exclusive with free=True.
        if row["free"]:
            assert row["locked"] is False, row
            assert row["allowed"] is True, row


def test_feature_catalog_ordering_is_deterministic(ent):
    """Ordering: free -> starter -> pro -> enterprise, each alphabetical."""
    cat = ent.feature_catalog()
    # Tier appearance order must match the spec.
    tier_seen = []
    for row in cat:
        if not tier_seen or tier_seen[-1] != row["tier"]:
            tier_seen.append(row["tier"])
    assert tier_seen == ["free", "starter", "pro", "enterprise"]
    # Within each tier, ids must be sorted alphabetically.
    by_tier: dict[str, list[str]] = {}
    for row in cat:
        by_tier.setdefault(row["tier"], []).append(row["id"])
    for tier, ids in by_tier.items():
        assert ids == sorted(ids), f"{tier} not alpha-sorted: {ids}"


def test_feature_catalog_grace_locks_nothing(ent):
    """Default grace mode: every paid feature reports locked=False so the UI
    behaves exactly as it did before the catalog existed."""
    cat = ent.feature_catalog()
    for row in cat:
        assert row["locked"] is False, row
        assert row["allowed"] is True, row


def test_feature_catalog_enforced_oss_locks_paid(monkeypatch, tmp_path):
    """CLAWMETRY_ENFORCE=1 with no license: free stays unlocked, paid locks."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    cat = e.feature_catalog()
    rows = {row["id"]: row for row in cat}
    # Spot-check the headline free feature.
    assert rows["sessions"]["locked"] is False
    assert rows["sessions"]["allowed"] is True
    # Starter / Pro / Enterprise representatives all lock in OSS-enforced.
    for fid in ("multi_runtime", "self_evolve", "siem_export"):
        assert rows[fid]["locked"] is True, fid
        assert rows[fid]["allowed"] is False, fid


def test_feature_catalog_cloud_starter_unlocks_starter_only(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    rows = {row["id"]: row for row in e.feature_catalog()}
    # Starter unlocks.
    assert rows["multi_runtime"]["locked"] is False
    assert rows["budget_limits"]["locked"] is False
    # Pro and Enterprise stay locked.
    assert rows["self_evolve"]["locked"] is True
    assert rows["siem_export"]["locked"] is True


def test_feature_catalog_cloud_pro_unlocks_starter_plus_pro(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    rows = {row["id"]: row for row in e.feature_catalog()}
    assert rows["multi_runtime"]["locked"] is False
    assert rows["self_evolve"]["locked"] is False
    assert rows["otel_export"]["locked"] is False
    # Enterprise still locked under cloud_pro.
    assert rows["siem_export"]["locked"] is True
    assert rows["sso"]["locked"] is True


def test_feature_catalog_enterprise_unlocks_everything(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise"}))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    cat = e.feature_catalog()
    for row in cat:
        assert row["locked"] is False, row
        assert row["allowed"] is True, row


# ── /api/features endpoint ───────────────────────────────────────────────────


def test_api_features_shape_grace(client):
    resp = client.get("/api/features")
    assert resp.status_code == 200
    d = resp.get_json()
    assert "features" in d
    assert "grace" in d
    assert "enforced" in d
    assert d["grace"] is True
    assert d["enforced"] is False
    assert isinstance(d["features"], list)
    assert len(d["features"]) >= 1
    # Grace defaults: every row reports locked=False.
    for row in d["features"]:
        assert row["locked"] is False, row


def test_api_features_grace_enforced_are_inverse(client):
    """grace and enforced must always be exact inverses."""
    d = client.get("/api/features").get_json()
    assert d["grace"] == (not d["enforced"])


def test_api_features_enforced_oss_locks_paid(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/features").get_json()

    assert d["grace"] is False
    assert d["enforced"] is True
    rows = {row["id"]: row for row in d["features"]}
    assert rows["sessions"]["locked"] is False
    assert rows["multi_runtime"]["locked"] is True
    assert rows["siem_export"]["locked"] is True


def test_api_features_paid_tier_unlocks_paid_features(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/features").get_json()

    rows = {row["id"]: row for row in d["features"]}
    assert rows["self_evolve"]["locked"] is False
    assert rows["multi_runtime"]["locked"] is False
    # Enterprise still locked.
    assert rows["siem_export"]["locked"] is True


def test_api_features_never_raises_on_broken_module(monkeypatch, client):
    """A resolution error must degrade to a graceful free-only response,
    never a 5xx — the dashboard reads this endpoint on every page load."""
    import clawmetry.entitlements as e

    def _boom():
        raise RuntimeError("simulated catalog breakage")

    monkeypatch.setattr(e, "feature_catalog", _boom)
    resp = client.get("/api/features")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["grace"] is True
    assert d["enforced"] is False
    # Fallback still emits the free features so the UI has something to show.
    ids = {row["id"] for row in d["features"]}
    for fid in ("sessions", "overview", "channels"):
        assert fid in ids
    for row in d["features"]:
        assert row["tier"] == "free"
        assert row["locked"] is False
