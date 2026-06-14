"""Tests for ``feature_catalog()`` + ``feature_tier()`` + ``feature_label()``.

The feature catalog is the source of truth the UI reads to render the locked-
but-visible upgrade affordance on paid *features* — the parallel of
``runtime_catalog()`` for the runtime switcher. These tests pin:

* every feature in ``ALL_FEATURES`` has a non-empty label and a recognised tier
* the catalog ordering is deterministic (free first, then by tier rank)
* grace mode reports zero locked rows (zero behaviour change)
* enforce mode locks paid rows for an OSS install and unlocks them for the
  paid tier that grants the feature
* unknown feature ids fall back to ``TIER_OSS`` (extension features never
  appear mysteriously locked)
"""
from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── helper invariants ─────────────────────────────────────────────────────────


def test_feature_label_falls_back_to_id(ent):
    """Unknown feature -> id back (matches the runtime helper)."""
    assert ent.feature_label("not_a_real_feature") == "not_a_real_feature"
    assert ent.feature_label("") == ""


def test_feature_label_strips_and_lowercases(ent):
    assert ent.feature_label("  Sessions  ") == "Sessions"
    assert ent.feature_label("SESSIONS") == "Sessions"


def test_feature_tier_free(ent):
    for fid in ent.FREE_FEATURES:
        assert ent.feature_tier(fid) == ent.TIER_OSS, fid


def test_feature_tier_starter(ent):
    for fid in ent.STARTER_FEATURES:
        assert ent.feature_tier(fid) == ent.TIER_CLOUD_STARTER, fid


def test_feature_tier_pro(ent):
    for fid in ent.PRO_ONLY_FEATURES:
        assert ent.feature_tier(fid) == ent.TIER_CLOUD_PRO, fid


def test_feature_tier_enterprise(ent):
    for fid in ent.ENTERPRISE_FEATURES:
        assert ent.feature_tier(fid) == ent.TIER_ENTERPRISE, fid


def test_feature_tier_unknown_defaults_to_oss(ent):
    """Extension features (not in any bucket) must not render as locked."""
    assert ent.feature_tier("plugin_feature_xyz") == ent.TIER_OSS


# ── label completeness ────────────────────────────────────────────────────────


def test_every_known_feature_has_a_label(ent):
    """A label gap silently regresses the upgrade copy to a raw id like
    'per_run_waste_flags' in the UI — pin it in CI."""
    missing = sorted(f for f in ent.ALL_FEATURES if f not in ent.FEATURE_LABELS)
    assert not missing, f"missing FEATURE_LABELS for: {missing}"


def test_every_label_is_non_blank(ent):
    for fid, label in ent.FEATURE_LABELS.items():
        assert isinstance(label, str) and label.strip(), fid


# ── catalog shape ─────────────────────────────────────────────────────────────


def test_catalog_covers_every_known_feature(ent):
    catalog = ent.feature_catalog()
    ids = {row["id"] for row in catalog}
    assert ids == set(ent.ALL_FEATURES)


def test_catalog_row_shape(ent):
    """Every row carries the keys the frontend reads — defends against an
    accidental rename breaking the upgrade surface."""
    catalog = ent.feature_catalog()
    assert catalog, "catalog must not be empty"
    for row in catalog:
        for key in ("id", "label", "tier", "free", "allowed", "locked", "entitled"):
            assert key in row, row
        assert isinstance(row["id"], str)
        assert isinstance(row["label"], str) and row["label"]
        assert row["tier"] in {
            ent.TIER_OSS,
            ent.TIER_CLOUD_STARTER,
            ent.TIER_CLOUD_PRO,
            ent.TIER_ENTERPRISE,
        }
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        assert isinstance(row["entitled"], bool)
        # locked = paid-and-not-allowed; mutually exclusive with free=True.
        if row["free"]:
            assert row["locked"] is False, row
            assert row["tier"] == ent.TIER_OSS, row


def test_catalog_ordering_free_then_by_tier(ent):
    """Free first, then Starter, then Pro, then Enterprise. Stable order so
    the upgrade list does not reshuffle on refresh."""
    catalog = ent.feature_catalog()
    rank = {
        ent.TIER_OSS: 0,
        ent.TIER_CLOUD_STARTER: 1,
        ent.TIER_CLOUD_PRO: 2,
        ent.TIER_ENTERPRISE: 3,
    }
    ranks = [rank[row["tier"]] for row in catalog]
    assert ranks == sorted(ranks), ranks


# ── grace vs enforce behaviour ────────────────────────────────────────────────


def test_grace_locks_nothing(ent):
    """Headline invariant — grace mode keeps every row unlocked so wiring the
    catalog into the UI changes no current behaviour."""
    catalog = ent.feature_catalog()
    for row in catalog:
        assert row["allowed"] is True, row
        assert row["locked"] is False, row


def test_enforce_oss_locks_every_paid_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    catalog = ent.feature_catalog()
    by_id = {row["id"]: row for row in catalog}
    for fid in ent.FREE_FEATURES:
        assert by_id[fid]["locked"] is False, fid
        assert by_id[fid]["allowed"] is True, fid
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES:
        assert by_id[fid]["locked"] is True, fid
        assert by_id[fid]["allowed"] is False, fid
        assert by_id[fid]["entitled"] is False, fid


def test_enforce_cloud_pro_unlocks_paid_but_not_enterprise(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    catalog = ent.feature_catalog()
    by_id = {row["id"]: row for row in catalog}
    # Starter + Pro unlocked.
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES:
        assert by_id[fid]["allowed"] is True, fid
        assert by_id[fid]["locked"] is False, fid
        assert by_id[fid]["entitled"] is True, fid
    # Enterprise still locked.
    for fid in ent.ENTERPRISE_FEATURES:
        assert by_id[fid]["allowed"] is False, fid
        assert by_id[fid]["locked"] is True, fid
        assert by_id[fid]["entitled"] is False, fid


# ── alias flag (backwards-compat PRO_ONLY keys) ──────────────────────────────


def test_catalog_alias_flag_marks_backcompat_pro_keys(ent):
    """The four backwards-compat keys living inside PRO_ONLY_FEATURES carry
    ``alias=True`` so the UI can hide them from the user-facing feature list
    without hard-coding the ids on the frontend (where they'd drift the next
    time the PRO_ONLY set shuffles)."""
    by_id = {row["id"]: row for row in ent.feature_catalog()}
    for fid in ("custom_alerts", "alert_webhooks", "anomaly_detection", "cost_optimizer"):
        assert by_id[fid]["alias"] is True, fid


def test_catalog_alias_flag_false_for_canonical_keys(ent):
    """Canonical features — every tier bucket — must not be flagged as
    aliases. Guards against an accidental membership change in
    ``_ALIAS_FEATURES`` silently hiding a real feature from the catalog."""
    by_id = {row["id"]: row for row in ent.feature_catalog()}
    for fid in ent.FREE_FEATURES | ent.STARTER_FEATURES | ent.ENTERPRISE_FEATURES:
        assert by_id[fid]["alias"] is False, fid
    for fid in ("self_evolve", "otel_export", "custom_webhooks", "tool_policy"):
        assert by_id[fid]["alias"] is False, fid


def test_catalog_alias_keys_live_inside_pro_only(ent):
    """Every alias key must exist in PRO_ONLY_FEATURES — otherwise the flag
    advertises a row that ``allows_feature`` won't actually unlock."""
    import clawmetry.entitlements as e
    assert e._ALIAS_FEATURES.issubset(e.PRO_ONLY_FEATURES)


def test_enforce_enterprise_unlocks_everything_paid(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "enterprise"}))
    ent.invalidate()
    catalog = ent.feature_catalog()
    for row in catalog:
        assert row["allowed"] is True, row["id"]
        assert row["locked"] is False, row["id"]
