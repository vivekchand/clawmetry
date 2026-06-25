"""Tests for ``feature_catalog()`` + ``feature_label()``.

``feature_catalog`` is the feature-side sibling of ``runtime_catalog`` — the
single shape the UI uses to render the locked-but-visible feature affordance
on settings + paywall surfaces. Companion to
``tests/test_entitlements_catalogue.py`` (which pins the underlying tier
buckets to /pricing).

Pins:

* every id in ``ALL_FEATURES`` appears exactly once in the catalog
* row ordering is free → starter → pro → enterprise; each bucket is sorted
  alphabetically so the UI is deterministic
* grace mode reports zero locked rows (zero behaviour change)
* enforce-mode lock state on an OSS install locks every paid feature
* every known feature has a non-empty label
* ``feature_label`` falls back to the id for unknown features and is empty-
  safe for missing input
"""
from __future__ import annotations

import importlib

import pytest


_ROW_KEYS = {"id", "label", "tier", "free", "allowed", "locked"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module against an empty HOME so no real
    ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off by
    default (grace mode)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── shape ─────────────────────────────────────────────────────────────────────


def test_catalog_lists_every_known_feature_exactly_once(ent):
    cat = ent.feature_catalog()
    ids = [row["id"] for row in cat]
    assert set(ids) == set(ent.ALL_FEATURES)
    assert len(ids) == len(set(ids))


def test_catalog_row_shape_is_stable(ent):
    for row in ent.feature_catalog():
        assert set(row.keys()) == _ROW_KEYS, row
        assert isinstance(row["id"], str) and row["id"]
        assert isinstance(row["label"], str) and row["label"]
        assert isinstance(row["tier"], str) and row["tier"]
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        # locked = paid-and-not-allowed; mutually exclusive with free=True.
        if row["free"]:
            assert row["locked"] is False, row


def test_catalog_ordering_is_free_starter_pro_enterprise(ent):
    cat = ent.feature_catalog()
    free = len(ent.FREE_FEATURES)
    starter = len(ent.STARTER_FEATURES)
    pro = len(ent.PRO_ONLY_FEATURES)
    ent_n = len(ent.ENTERPRISE_FEATURES)
    assert {r["id"] for r in cat[:free]} == set(ent.FREE_FEATURES)
    assert {r["id"] for r in cat[free : free + starter]} == set(ent.STARTER_FEATURES)
    assert {r["id"] for r in cat[free + starter : free + starter + pro]} == set(
        ent.PRO_ONLY_FEATURES
    )
    assert {
        r["id"] for r in cat[free + starter + pro : free + starter + pro + ent_n]
    } == set(ent.ENTERPRISE_FEATURES)


def test_catalog_bucket_rows_are_alphabetically_sorted(ent):
    """Within each tier bucket the rows are sorted by id so the UI is
    deterministic."""
    cat = ent.feature_catalog()
    free = len(ent.FREE_FEATURES)
    starter = len(ent.STARTER_FEATURES)
    pro = len(ent.PRO_ONLY_FEATURES)
    slices = {
        "free": [r["id"] for r in cat[:free]],
        "starter": [r["id"] for r in cat[free : free + starter]],
        "pro": [r["id"] for r in cat[free + starter : free + starter + pro]],
        "enterprise": [r["id"] for r in cat[free + starter + pro :]],
    }
    for name, ids in slices.items():
        assert ids == sorted(ids), name


def test_catalog_tier_field_matches_bucket(ent):
    by_id = {r["id"]: r for r in ent.feature_catalog()}
    for fid in ent.FREE_FEATURES:
        assert by_id[fid]["tier"] == ent.TIER_OSS, fid
    for fid in ent.STARTER_FEATURES:
        assert by_id[fid]["tier"] == ent.TIER_CLOUD_STARTER, fid
    for fid in ent.PRO_ONLY_FEATURES:
        assert by_id[fid]["tier"] == ent.TIER_CLOUD_PRO, fid
    for fid in ent.ENTERPRISE_FEATURES:
        assert by_id[fid]["tier"] == ent.TIER_ENTERPRISE, fid


def test_catalog_free_flag_matches_membership(ent):
    for row in ent.feature_catalog():
        assert row["free"] == (row["id"] in ent.FREE_FEATURES), row


# ── grace vs enforce ──────────────────────────────────────────────────────────


def test_catalog_grace_locks_nothing(ent):
    """Grace mode (the default until enforcement flips on): every row reports
    ``locked=False``/``allowed=True`` so the UI behaves exactly as it did
    before this endpoint existed."""
    for row in ent.feature_catalog():
        assert row["allowed"] is True, row
        assert row["locked"] is False, row


def test_catalog_enforced_oss_locks_every_paid_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    by_id = {r["id"]: r for r in ent.feature_catalog()}
    for fid in ent.FREE_FEATURES:
        assert by_id[fid]["allowed"] is True, fid
        assert by_id[fid]["locked"] is False, fid
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES:
        assert by_id[fid]["allowed"] is False, fid
        assert by_id[fid]["locked"] is True, fid


# ── labels ────────────────────────────────────────────────────────────────────


def test_every_known_feature_has_a_label(ent):
    """Catches "added a feature but forgot the human-readable label". The UI
    will still render the id as a fallback, but a deliberate label makes the
    paywall copy readable."""
    for fid in ent.ALL_FEATURES:
        assert fid in ent.FEATURE_LABELS, fid
        assert ent.FEATURE_LABELS[fid], fid


def test_feature_label_falls_back_to_id(ent):
    assert ent.feature_label("sessions") == "Sessions"
    # Unknown feature → graceful fallback to the id so future plugin features
    # still render with *something*.
    assert ent.feature_label("brand_new_plugin_feature") == "brand_new_plugin_feature"
    assert ent.feature_label("") == ""
    assert ent.feature_label(None) == ""


def test_feature_label_is_input_normalised(ent):
    assert ent.feature_label("SESSIONS") == ent.feature_label("sessions")
    assert ent.feature_label("  sessions  ") == ent.feature_label("sessions")


# ── never-raise ───────────────────────────────────────────────────────────────


def test_catalog_never_raises_when_resolver_crashes(ent, monkeypatch):
    """A blown resolver still returns the catalog built against the OSS-free
    fallback — matches the never-crash contract on ``runtime_catalog``."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    cat = ent.feature_catalog()
    assert isinstance(cat, list)
    ids = {row["id"] for row in cat}
    assert ids == set(ent.ALL_FEATURES)
    # OSS-free fallback in grace mode → nothing locked.
    for row in cat:
        assert row["allowed"] is True, row
        assert row["locked"] is False, row
