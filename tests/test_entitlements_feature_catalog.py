"""Tests for the feature catalog: ``feature_label`` / ``feature_tier`` /
``feature_catalog`` in ``clawmetry/entitlements.py`` and the
``GET /api/features`` endpoint in ``routes/entitlement.py``.

The catalog is the single source of truth the dashboard reads to render the
Settings feature matrix, the pricing-parity grid, and the upgrade-CTA copy
without re-deriving tier buckets in JS. These tests pin the per-tier bucket
membership, the catalog's locked/allowed/free flags under each representative
tier, the never-raise posture, and the route shape.

Companion to ``tests/test_entitlements_catalogue.py`` (which pins the bucket
*set* membership against /pricing) and ``tests/test_entitlement_api.py``
(which covers /api/entitlement + /api/runtimes).
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
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


# ── feature_label ─────────────────────────────────────────────────────────────


def test_feature_label_known_keys(ent):
    assert ent.feature_label("sessions") == "Sessions"
    assert ent.feature_label("fleet") == "Multi-node fleet"
    assert ent.feature_label("self_evolve") == "Self-Evolve"
    assert ent.feature_label("sso") == "SSO"


def test_feature_label_unknown_falls_back_to_id(ent):
    assert ent.feature_label("not_a_real_feature") == "not_a_real_feature"


def test_feature_label_empty_and_none_are_safe(ent):
    assert ent.feature_label("") == ""
    assert ent.feature_label(None) == ""  # type: ignore[arg-type]


def test_feature_label_case_insensitive(ent):
    assert ent.feature_label("SESSIONS") == "Sessions"
    assert ent.feature_label("  fleet  ") == "Multi-node fleet"


def test_every_known_feature_has_a_label(ent):
    """Every key in ALL_FEATURES should ship with a human-readable label —
    a missing label silently degrades to the snake_case id in the UI."""
    missing = sorted(ent.ALL_FEATURES - set(ent.FEATURE_LABELS))
    assert not missing, f"missing FEATURE_LABELS entries: {missing}"


# ── feature_tier ──────────────────────────────────────────────────────────────


def test_feature_tier_buckets(ent):
    assert ent.feature_tier("sessions") == ent.TIER_OSS
    assert ent.feature_tier("transcripts") == ent.TIER_OSS
    assert ent.feature_tier("fleet") == ent.TIER_CLOUD_STARTER
    assert ent.feature_tier("multi_runtime") == ent.TIER_CLOUD_STARTER
    assert ent.feature_tier("self_evolve") == ent.TIER_CLOUD_PRO
    assert ent.feature_tier("otel_export") == ent.TIER_CLOUD_PRO
    assert ent.feature_tier("sso") == ent.TIER_ENTERPRISE
    assert ent.feature_tier("siem_export") == ent.TIER_ENTERPRISE


def test_feature_tier_unknown_collapses_to_oss(ent):
    """Unknown ids must NOT spuriously render as a locked Enterprise row —
    they collapse to OSS (free) so the catalog stays grace-safe."""
    assert ent.feature_tier("not_a_real_feature") == ent.TIER_OSS


def test_feature_tier_empty_and_none_are_safe(ent):
    assert ent.feature_tier("") == ent.TIER_OSS
    assert ent.feature_tier(None) == ent.TIER_OSS  # type: ignore[arg-type]


def test_feature_tier_case_insensitive(ent):
    assert ent.feature_tier("FLEET") == ent.TIER_CLOUD_STARTER
    assert ent.feature_tier("  SSO  ") == ent.TIER_ENTERPRISE


# ── feature_catalog: grace mode ───────────────────────────────────────────────


def test_catalog_covers_every_known_feature(ent):
    cat = ent.feature_catalog()
    ids = {row["id"] for row in cat}
    assert ids == ent.ALL_FEATURES


def test_catalog_grace_all_allowed_none_locked(ent):
    cat = ent.feature_catalog()
    assert all(row["allowed"] is True for row in cat)
    assert all(row["locked"] is False for row in cat)


def test_catalog_shape_keys(ent):
    cat = ent.feature_catalog()
    assert cat, "catalog must not be empty"
    for row in cat:
        for k in ("id", "label", "tier", "free", "allowed", "locked"):
            assert k in row, f"row missing {k}: {row}"


def test_catalog_free_flag_matches_FREE_FEATURES(ent):
    cat = ent.feature_catalog()
    for row in cat:
        assert row["free"] == (row["id"] in ent.FREE_FEATURES)


def test_catalog_tier_column_matches_feature_tier(ent):
    """Every row's ``tier`` column must equal ``feature_tier(id)`` — the
    catalog should NEVER drift from the per-feature lookup."""
    cat = ent.feature_catalog()
    for row in cat:
        assert row["tier"] == ent.feature_tier(row["id"]), row


# ── feature_catalog: ordering invariant ───────────────────────────────────────


def test_catalog_ordering_free_then_starter_then_pro_then_enterprise(ent):
    """Stable ordering: free -> starter -> pro -> enterprise; alphabetical
    within each group. The UI relies on this for its deterministic grid."""
    tier_order = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    cat = ent.feature_catalog()
    seen_groups: list[str] = []
    prev_id_in_group: str | None = None
    for row in cat:
        t = row["tier"]
        if not seen_groups or seen_groups[-1] != t:
            seen_groups.append(t)
            prev_id_in_group = None
        if prev_id_in_group is not None:
            assert row["id"] > prev_id_in_group, (
                f"ids must be alphabetical within tier {t}: "
                f"{prev_id_in_group} >= {row['id']}"
            )
        prev_id_in_group = row["id"]
    assert seen_groups == tier_order


# ── feature_catalog: enforce mode ─────────────────────────────────────────────


def test_catalog_enforce_oss_free_allowed_paid_locked(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cat = ent.feature_catalog()
    for row in cat:
        if row["free"]:
            assert row["allowed"] is True, row
            assert row["locked"] is False, row
        else:
            assert row["allowed"] is False, row
            assert row["locked"] is True, row


def test_catalog_enforce_starter_grants_starter_only(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
    ent.invalidate()
    by_id = {row["id"]: row for row in ent.feature_catalog()}
    # Starter rows pass.
    assert by_id["fleet"]["allowed"] is True
    assert by_id["multi_runtime"]["allowed"] is True
    # Pro-only rows are still locked.
    assert by_id["self_evolve"]["allowed"] is False
    assert by_id["self_evolve"]["locked"] is True
    assert by_id["otel_export"]["allowed"] is False
    # Enterprise rows are still locked.
    assert by_id["sso"]["allowed"] is False
    assert by_id["sso"]["locked"] is True


def test_catalog_enforce_pro_grants_starter_plus_pro(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    by_id = {row["id"]: row for row in ent.feature_catalog()}
    assert by_id["multi_runtime"]["allowed"] is True  # starter
    assert by_id["self_evolve"]["allowed"] is True  # pro
    assert by_id["otel_export"]["allowed"] is True  # pro
    assert by_id["siem_export"]["allowed"] is False  # enterprise
    assert by_id["sso"]["locked"] is True


def test_catalog_enforce_enterprise_grants_everything(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise"}))
    ent.invalidate()
    cat = ent.feature_catalog()
    for row in cat:
        assert row["allowed"] is True, row
        assert row["locked"] is False, row


def test_catalog_swallows_resolver_failure(ent, monkeypatch):
    """A flaky entitlement resolver must NOT 500 the catalog — it falls back
    to the OSS-free grace shape so the UI can still render."""
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    cat = ent.feature_catalog()
    # Grace fallback: every row reports allowed=True, locked=False.
    assert cat, "fallback catalog must not be empty"
    assert all(row["allowed"] is True for row in cat)
    assert all(row["locked"] is False for row in cat)


# ── /api/features endpoint ────────────────────────────────────────────────────


def test_api_features_shape_grace(client, ent):
    rv = client.get("/api/features")
    assert rv.status_code == 200
    d = rv.get_json()
    assert "features" in d and isinstance(d["features"], list)
    assert d["grace"] is True
    assert d["enforced"] is False
    assert d["grace"] == (not d["enforced"])
    ids = {row["id"] for row in d["features"]}
    assert ids == ent.ALL_FEATURES


def test_api_features_grace_all_allowed(client):
    d = client.get("/api/features").get_json()
    assert all(row["allowed"] is True for row in d["features"])
    assert all(row["locked"] is False for row in d["features"])


def test_api_features_enforce_oss_locks_paid(monkeypatch, tmp_path):
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
    by_id = {row["id"]: row for row in d["features"]}
    assert by_id["sessions"]["allowed"] is True
    assert by_id["sessions"]["locked"] is False
    assert by_id["fleet"]["allowed"] is False
    assert by_id["fleet"]["locked"] is True
    assert by_id["sso"]["allowed"] is False
    assert by_id["sso"]["locked"] is True


def test_api_features_enforce_pro_unlocks_starter_and_pro(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/features").get_json()
    by_id = {row["id"]: row for row in d["features"]}
    assert by_id["fleet"]["allowed"] is True
    assert by_id["self_evolve"]["allowed"] is True
    assert by_id["sso"]["allowed"] is False
    assert by_id["sso"]["locked"] is True


def test_api_features_never_500s_on_resolver_failure(monkeypatch, tmp_path):
    """An exploded entitlement resolver must not 5xx the catalog endpoint —
    the route falls back to a grace-mode shape so the UI keeps rendering."""
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(e, "get_entitlement", boom)

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    rv = app.test_client().get("/api/features")
    assert rv.status_code == 200
    d = rv.get_json()
    assert d["grace"] is True
    assert d["enforced"] is False
    assert all(row["allowed"] is True for row in d["features"])
    assert all(row["locked"] is False for row in d["features"])
