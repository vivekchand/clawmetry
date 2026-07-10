"""Tests for the source-anchored ``next/previous_tier_feature_catalog_at``
and ``next/previous_tier_runtime_catalog_at`` helpers, and the four
companion API endpoints:

* ``/api/entitlement/next-tier-feature-catalog-at``
* ``/api/entitlement/previous-tier-feature-catalog-at``
* ``/api/entitlement/next-tier-runtime-catalog-at``
* ``/api/entitlement/previous-tier-runtime-catalog-at``

Source-anchored feature-/runtime-axis catalog projection of
``{next,previous}_tier_spec_at``: where those helpers return the full
:func:`tier_spec`-shape descriptor of the rung one above / below an
explicit source, these helpers return the full
:func:`feature_catalog_at` / :func:`runtime_catalog_at`-shape catalogue
at that rung -- one row per feature / runtime -- so an upgrade-preview
panel walking an explicit source rung (a pricing-comparison matrix, an
"at each rung" table) can hydrate the whole matrix at the next /
previous rung off ONE round-trip.

Unlike the channel axis (every chat channel is free at every tier), the
feature / runtime axes tier-gate paid entries, so the returned rows DO
differ across target rungs -- rows for a locked feature flip
``locked`` / ``entitled`` when the resolved perspective climbs above
its ``tier`` threshold. Byte-parity with the explicit
``feature_catalog_at(_next_purchasable_tier_after(tier))`` /
``runtime_catalog_at(_next_purchasable_tier_after(tier))`` composition
is pinned so a caller can substitute the convenience for the
composition without behavioural drift.

Pins covered here:

* helper vs :func:`feature_catalog_at` / :func:`runtime_catalog_at`
  identity for next/previous across every purchasable source
* helper vs resolver-anchored
  ``Entitlement.next_tier_feature_catalog`` /
  ``Entitlement.next_tier_runtime_catalog`` byte-identity at the shared
  source rung (the two must agree when ``tier`` matches the resolved
  current)
* ceiling / floor returns ``None`` (enterprise has no next; oss /
  cloud_free have no previous)
* trial-as-source resolves the same way the sibling next/previous
  channel-spec / feature-runtime-spec families do: next -> enterprise,
  previous -> cloud_starter
* row key set matches the sibling ``*_catalog_at`` builder for every
  purchasable source (per-axis ``_ROW_KEYS``)
* row order matches the sibling ``*_catalog_at`` builder byte-for-byte
* row count matches ``ALL_FEATURES`` / ``ALL_RUNTIMES``
* labels come from the ``feature_label`` / ``runtime_label`` helper
* upgrade unlocks strictly more: at a lower source the next-tier catalog
  exposes at least as many entitled rows as the source catalog
* grace vs enforce yields identical bodies (catalog-derived; no
  enforcement branch inside the builder)
* unknown / empty / whitespace / case handling: helpers return ``None``,
  endpoints return 400 on missing tier and 404 on unknown tier
* the helpers never raise -- a builder failure short-circuits to
  ``None`` so the panel stays mute instead of breaking
* the four API endpoints never 5xx: happy path returns a 200 envelope
  with the full ``features`` / ``runtimes`` list; at the ceiling / floor
  the list collapses to ``[]`` and ``target`` / ``target_label`` /
  ``target_rank`` to ``null``; a synthesised failure yields the
  grace-shape envelope (200 with an empty list)
* endpoint list byte-matches ``/feature-catalog-at?tier=<target>`` /
  ``/runtime-catalog-at?tier=<target>`` at the resolved target rung
* end-to-end sweep across every source rung confirms the parity holds
  at both the helper and endpoint layer
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS_FEATURES = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
}
_ENVELOPE_KEYS_RUNTIMES = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
}

_FEATURE_ROW_KEYS = {
    "id",
    "label",
    "tier",
    "tiers",
    "free",
    "allowed",
    "locked",
    "entitled",
    "alias",
}
_RUNTIME_ROW_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}


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


# ═══════════════════════════════════════════════════════════════════════
# FEATURE AXIS
# ═══════════════════════════════════════════════════════════════════════
#
# ── next_tier_feature_catalog_at helper ──────────────────────────────────


def test_next_tier_feature_catalog_at_matches_feature_catalog_at(ent):
    # next_tier_feature_catalog_at(tier) is a convenience for
    # feature_catalog_at(_next_purchasable_tier_after(tier)) -- they must
    # be byte-equal across every purchasable source so a caller can use
    # the convenience interchangeably with the explicit composition.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(tier)
        assert target is not None, tier
        assert ent.next_tier_feature_catalog_at(tier) == ent.feature_catalog_at(
            target
        )


def test_next_tier_feature_catalog_at_agrees_with_resolver_method(
    ent, monkeypatch
):
    # At the resolved source the helper and the resolver-anchored method
    # must return byte-identical bodies (both compose feature_catalog_at
    # at the same next_purchasable_tier).
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        monkeypatch.setattr(ent, "get_entitlement", lambda e=e: e)
        assert ent.next_tier_feature_catalog_at(
            tier
        ) == e.next_tier_feature_catalog()


def test_next_tier_feature_catalog_at_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung
    # above to preview, so the convenience returns None just like
    # _next_purchasable_tier_after.
    assert ent.next_tier_feature_catalog_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_feature_catalog_at_trial_source(ent):
    # Trial's next purchasable rung is enterprise -- matches the sibling
    # next_tier_* families.
    target = ent._next_purchasable_tier_after(ent.TIER_TRIAL)
    assert target == ent.TIER_ENTERPRISE
    assert ent.next_tier_feature_catalog_at(
        ent.TIER_TRIAL
    ) == ent.feature_catalog_at(target)


def test_next_tier_feature_catalog_at_row_count_and_ids(ent):
    rows = ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    assert len(rows) == len(ent.ALL_FEATURES)
    assert {row["id"] for row in rows} == set(ent.ALL_FEATURES)


def test_next_tier_feature_catalog_at_row_order_matches_sibling(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(tier)
        assert [row["id"] for row in ent.next_tier_feature_catalog_at(tier)] == [
            row["id"] for row in ent.feature_catalog_at(target)
        ], tier


def test_next_tier_feature_catalog_at_row_schema(ent):
    rows = ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _FEATURE_ROW_KEYS, row


def test_next_tier_feature_catalog_at_labels_from_feature_label(ent):
    rows = ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.feature_label(row["id"])


def test_next_tier_feature_catalog_at_upgrade_unlocks_at_least_as_many(ent):
    # Climbing the ladder must never REMOVE an entitled feature. So the
    # set of entitled features at the next rung must be a superset of the
    # set at the current rung -- pins the "upgrade never regresses" law
    # via the catalog helpers.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ):
        here = ent.feature_catalog_at(tier)
        there = ent.next_tier_feature_catalog_at(tier)
        assert there is not None, tier
        here_entitled = {r["id"] for r in here if r["entitled"]}
        there_entitled = {r["id"] for r in there if r["entitled"]}
        assert here_entitled <= there_entitled, tier


def test_next_tier_feature_catalog_at_none_for_empty_tier(ent):
    assert ent.next_tier_feature_catalog_at("") is None
    assert ent.next_tier_feature_catalog_at("   ") is None
    assert ent.next_tier_feature_catalog_at(None) is None


def test_next_tier_feature_catalog_at_none_for_unknown_tier(ent):
    assert ent.next_tier_feature_catalog_at("bogus_tier_xyz") is None


def test_next_tier_feature_catalog_at_case_insensitive(ent):
    lower = ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER)
    upper = ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER.upper())
    mixed = ent.next_tier_feature_catalog_at(
        f" {ent.TIER_CLOUD_STARTER.capitalize()}  "
    )
    assert lower == upper == mixed


def test_next_tier_feature_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    # If feature_catalog_at blows up, the helper must swallow and return
    # None so the preview surface stays mute rather than 500-ing.
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "feature_catalog_at", boom)
    assert ent.next_tier_feature_catalog_at(ent.TIER_CLOUD_STARTER) is None


def test_next_tier_feature_catalog_at_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    # Catalog helpers are pure static-catalogue projections -- flipping
    # enforcement must not change the returned bodies.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        grace = ent.next_tier_feature_catalog_at(tier)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_feature_catalog_at(tier)
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── previous_tier_feature_catalog_at helper ──────────────────────────────


def test_previous_tier_feature_catalog_at_matches_feature_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(tier)
        assert target is not None, tier
        assert ent.previous_tier_feature_catalog_at(
            tier
        ) == ent.feature_catalog_at(target)


def test_previous_tier_feature_catalog_at_agrees_with_resolver_method(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        monkeypatch.setattr(ent, "get_entitlement", lambda e=e: e)
        assert ent.previous_tier_feature_catalog_at(
            tier
        ) == e.previous_tier_feature_catalog()


def test_previous_tier_feature_catalog_at_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent.previous_tier_feature_catalog_at(tier) is None


def test_previous_tier_feature_catalog_at_trial_source(ent):
    target = ent._previous_purchasable_tier_before(ent.TIER_TRIAL)
    assert target == ent.TIER_CLOUD_STARTER
    assert ent.previous_tier_feature_catalog_at(
        ent.TIER_TRIAL
    ) == ent.feature_catalog_at(target)


def test_previous_tier_feature_catalog_at_row_schema(ent):
    rows = ent.previous_tier_feature_catalog_at(ent.TIER_ENTERPRISE)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _FEATURE_ROW_KEYS, row


def test_previous_tier_feature_catalog_at_downgrade_never_gains(ent):
    # Downgrading must never ADD an entitled feature. So the set of
    # entitled features at the previous rung must be a subset of the set
    # at the current rung -- the mirror of the upgrade invariant.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        here = ent.feature_catalog_at(tier)
        there = ent.previous_tier_feature_catalog_at(tier)
        assert there is not None, tier
        here_entitled = {r["id"] for r in here if r["entitled"]}
        there_entitled = {r["id"] for r in there if r["entitled"]}
        assert there_entitled <= here_entitled, tier


def test_previous_tier_feature_catalog_at_none_for_empty_tier(ent):
    assert ent.previous_tier_feature_catalog_at("") is None
    assert ent.previous_tier_feature_catalog_at("   ") is None
    assert ent.previous_tier_feature_catalog_at(None) is None


def test_previous_tier_feature_catalog_at_none_for_unknown_tier(ent):
    assert ent.previous_tier_feature_catalog_at("bogus_tier_xyz") is None


def test_previous_tier_feature_catalog_at_case_insensitive(ent):
    lower = ent.previous_tier_feature_catalog_at(ent.TIER_CLOUD_PRO)
    upper = ent.previous_tier_feature_catalog_at(ent.TIER_CLOUD_PRO.upper())
    mixed = ent.previous_tier_feature_catalog_at(
        f" {ent.TIER_CLOUD_PRO.capitalize()}  "
    )
    assert lower == upper == mixed


def test_previous_tier_feature_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "feature_catalog_at", boom)
    assert ent.previous_tier_feature_catalog_at(ent.TIER_CLOUD_PRO) is None


# ═══════════════════════════════════════════════════════════════════════
# RUNTIME AXIS
# ═══════════════════════════════════════════════════════════════════════
#
# ── next_tier_runtime_catalog_at helper ──────────────────────────────────


def test_next_tier_runtime_catalog_at_matches_runtime_catalog_at(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(tier)
        assert target is not None, tier
        assert ent.next_tier_runtime_catalog_at(tier) == ent.runtime_catalog_at(
            target
        )


def test_next_tier_runtime_catalog_at_agrees_with_resolver_method(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        monkeypatch.setattr(ent, "get_entitlement", lambda e=e: e)
        assert ent.next_tier_runtime_catalog_at(
            tier
        ) == e.next_tier_runtime_catalog()


def test_next_tier_runtime_catalog_at_returns_none_at_ceiling(ent):
    assert ent.next_tier_runtime_catalog_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_runtime_catalog_at_trial_source(ent):
    target = ent._next_purchasable_tier_after(ent.TIER_TRIAL)
    assert target == ent.TIER_ENTERPRISE
    assert ent.next_tier_runtime_catalog_at(
        ent.TIER_TRIAL
    ) == ent.runtime_catalog_at(target)


def test_next_tier_runtime_catalog_at_row_count_and_ids(ent):
    rows = ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    assert len(rows) == len(ent.ALL_RUNTIMES)
    assert {row["id"] for row in rows} == set(ent.ALL_RUNTIMES)


def test_next_tier_runtime_catalog_at_row_order_matches_sibling(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(tier)
        assert [row["id"] for row in ent.next_tier_runtime_catalog_at(tier)] == [
            row["id"] for row in ent.runtime_catalog_at(target)
        ], tier


def test_next_tier_runtime_catalog_at_row_schema(ent):
    rows = ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS, row


def test_next_tier_runtime_catalog_at_free_runtimes_always_free(ent):
    # The free-runtimes block stays free at every target rung -- pin so
    # the free tier can't be silently regressed.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        rows = ent.next_tier_runtime_catalog_at(tier)
        assert rows is not None, tier
        for row in rows:
            if row["id"] in ent.FREE_RUNTIMES:
                assert row["free"] is True, (tier, row)
                assert row["allowed"] is True, (tier, row)
                assert row["locked"] is False, (tier, row)
                assert row["entitled"] is True, (tier, row)


def test_next_tier_runtime_catalog_at_labels_from_runtime_label(ent):
    rows = ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.runtime_label(row["id"])


def test_next_tier_runtime_catalog_at_upgrade_unlocks_at_least_as_many(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ):
        here = ent.runtime_catalog_at(tier)
        there = ent.next_tier_runtime_catalog_at(tier)
        assert there is not None, tier
        here_entitled = {r["id"] for r in here if r["entitled"]}
        there_entitled = {r["id"] for r in there if r["entitled"]}
        assert here_entitled <= there_entitled, tier


def test_next_tier_runtime_catalog_at_none_for_empty_tier(ent):
    assert ent.next_tier_runtime_catalog_at("") is None
    assert ent.next_tier_runtime_catalog_at("   ") is None
    assert ent.next_tier_runtime_catalog_at(None) is None


def test_next_tier_runtime_catalog_at_none_for_unknown_tier(ent):
    assert ent.next_tier_runtime_catalog_at("bogus_tier_xyz") is None


def test_next_tier_runtime_catalog_at_case_insensitive(ent):
    lower = ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER)
    upper = ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER.upper())
    mixed = ent.next_tier_runtime_catalog_at(
        f" {ent.TIER_CLOUD_STARTER.capitalize()}  "
    )
    assert lower == upper == mixed


def test_next_tier_runtime_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "runtime_catalog_at", boom)
    assert ent.next_tier_runtime_catalog_at(ent.TIER_CLOUD_STARTER) is None


def test_next_tier_runtime_catalog_at_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        grace = ent.next_tier_runtime_catalog_at(tier)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_runtime_catalog_at(tier)
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── previous_tier_runtime_catalog_at helper ──────────────────────────────


def test_previous_tier_runtime_catalog_at_matches_runtime_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(tier)
        assert target is not None, tier
        assert ent.previous_tier_runtime_catalog_at(
            tier
        ) == ent.runtime_catalog_at(target)


def test_previous_tier_runtime_catalog_at_agrees_with_resolver_method(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        monkeypatch.setattr(ent, "get_entitlement", lambda e=e: e)
        assert ent.previous_tier_runtime_catalog_at(
            tier
        ) == e.previous_tier_runtime_catalog()


def test_previous_tier_runtime_catalog_at_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent.previous_tier_runtime_catalog_at(tier) is None


def test_previous_tier_runtime_catalog_at_trial_source(ent):
    target = ent._previous_purchasable_tier_before(ent.TIER_TRIAL)
    assert target == ent.TIER_CLOUD_STARTER
    assert ent.previous_tier_runtime_catalog_at(
        ent.TIER_TRIAL
    ) == ent.runtime_catalog_at(target)


def test_previous_tier_runtime_catalog_at_row_schema(ent):
    rows = ent.previous_tier_runtime_catalog_at(ent.TIER_ENTERPRISE)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS, row


def test_previous_tier_runtime_catalog_at_downgrade_never_gains(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        here = ent.runtime_catalog_at(tier)
        there = ent.previous_tier_runtime_catalog_at(tier)
        assert there is not None, tier
        here_entitled = {r["id"] for r in here if r["entitled"]}
        there_entitled = {r["id"] for r in there if r["entitled"]}
        assert there_entitled <= here_entitled, tier


def test_previous_tier_runtime_catalog_at_none_for_empty_tier(ent):
    assert ent.previous_tier_runtime_catalog_at("") is None
    assert ent.previous_tier_runtime_catalog_at("   ") is None
    assert ent.previous_tier_runtime_catalog_at(None) is None


def test_previous_tier_runtime_catalog_at_none_for_unknown_tier(ent):
    assert ent.previous_tier_runtime_catalog_at("bogus_tier_xyz") is None


def test_previous_tier_runtime_catalog_at_case_insensitive(ent):
    lower = ent.previous_tier_runtime_catalog_at(ent.TIER_CLOUD_PRO)
    upper = ent.previous_tier_runtime_catalog_at(ent.TIER_CLOUD_PRO.upper())
    mixed = ent.previous_tier_runtime_catalog_at(
        f" {ent.TIER_CLOUD_PRO.capitalize()}  "
    )
    assert lower == upper == mixed


def test_previous_tier_runtime_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "runtime_catalog_at", boom)
    assert ent.previous_tier_runtime_catalog_at(ent.TIER_CLOUD_PRO) is None


# ═══════════════════════════════════════════════════════════════════════
# /api/entitlement/next-tier-feature-catalog-at
# ═══════════════════════════════════════════════════════════════════════


def test_endpoint_next_tier_feature_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200


def test_endpoint_next_tier_feature_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES


def test_endpoint_next_tier_feature_catalog_at_rows_byte_equal_helper(
    ent, client
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        resp = client.get(
            f"/api/entitlement/next-tier-feature-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["features"] == ent.next_tier_feature_catalog_at(tier)


def test_endpoint_next_tier_feature_catalog_at_source_echo(ent, client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)


def test_endpoint_next_tier_feature_catalog_at_target_echo(ent, client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_endpoint_next_tier_feature_catalog_at_ceiling_shape(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-feature-catalog-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["features"] == []


def test_endpoint_next_tier_feature_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-feature-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["features"] == ent.feature_catalog_at(ent.TIER_ENTERPRISE)


def test_endpoint_next_tier_feature_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/next-tier-feature-catalog-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_endpoint_next_tier_feature_catalog_at_blank_tier_400(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_next_tier_feature_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_xyz"


def test_endpoint_next_tier_feature_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_feature_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/next-tier-feature-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["tier"] == "cloud_starter"


# ═══════════════════════════════════════════════════════════════════════
# /api/entitlement/previous-tier-feature-catalog-at
# ═══════════════════════════════════════════════════════════════════════


def test_endpoint_previous_tier_feature_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200


def test_endpoint_previous_tier_feature_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES


def test_endpoint_previous_tier_feature_catalog_at_rows_byte_equal_helper(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-feature-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["features"] == ent.previous_tier_feature_catalog_at(tier)


def test_endpoint_previous_tier_feature_catalog_at_target_echo(ent, client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_feature_catalog_at_floor_shape(ent, client):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-feature-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert body["target"] is None, tier
        assert body["target_label"] is None, tier
        assert body["target_rank"] is None, tier
        assert body["features"] == [], tier


def test_endpoint_previous_tier_feature_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/previous-tier-feature-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["features"] == ent.feature_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_feature_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog-at")
    assert resp.status_code == 400


def test_endpoint_previous_tier_feature_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_xyz"


def test_endpoint_previous_tier_feature_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_feature_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/previous-tier-feature-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["tier"] == "cloud_pro"


# ═══════════════════════════════════════════════════════════════════════
# /api/entitlement/next-tier-runtime-catalog-at
# ═══════════════════════════════════════════════════════════════════════


def test_endpoint_next_tier_runtime_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200


def test_endpoint_next_tier_runtime_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES


def test_endpoint_next_tier_runtime_catalog_at_rows_byte_equal_helper(
    ent, client
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        resp = client.get(
            f"/api/entitlement/next-tier-runtime-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["runtimes"] == ent.next_tier_runtime_catalog_at(tier)


def test_endpoint_next_tier_runtime_catalog_at_target_echo(ent, client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_endpoint_next_tier_runtime_catalog_at_ceiling_shape(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-runtime-catalog-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["runtimes"] == []


def test_endpoint_next_tier_runtime_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-runtime-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["runtimes"] == ent.runtime_catalog_at(ent.TIER_ENTERPRISE)


def test_endpoint_next_tier_runtime_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog-at")
    assert resp.status_code == 400


def test_endpoint_next_tier_runtime_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404


def test_endpoint_next_tier_runtime_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_runtime_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/next-tier-runtime-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtimes"] == []
    assert body["tier"] == "cloud_starter"


# ═══════════════════════════════════════════════════════════════════════
# /api/entitlement/previous-tier-runtime-catalog-at
# ═══════════════════════════════════════════════════════════════════════


def test_endpoint_previous_tier_runtime_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200


def test_endpoint_previous_tier_runtime_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES


def test_endpoint_previous_tier_runtime_catalog_at_rows_byte_equal_helper(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-runtime-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["runtimes"] == ent.previous_tier_runtime_catalog_at(tier)


def test_endpoint_previous_tier_runtime_catalog_at_target_echo(ent, client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_endpoint_previous_tier_runtime_catalog_at_floor_shape(ent, client):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-runtime-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert body["target"] is None, tier
        assert body["runtimes"] == [], tier


def test_endpoint_previous_tier_runtime_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/previous-tier-runtime-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["runtimes"] == ent.runtime_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_runtime_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog-at")
    assert resp.status_code == 400


def test_endpoint_previous_tier_runtime_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404


def test_endpoint_previous_tier_runtime_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_runtime_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtimes"] == []
    assert body["tier"] == "cloud_pro"


# ═══════════════════════════════════════════════════════════════════════
# Cross-endpoint parity with /feature-catalog-at and /runtime-catalog-at
# ═══════════════════════════════════════════════════════════════════════


def test_endpoint_next_tier_feature_catalog_at_matches_feature_catalog_at(
    ent, client
):
    # /next-tier-feature-catalog-at?tier=X must byte-match
    # /feature-catalog-at?tier=<_next_purchasable_tier_after(X)> so the
    # source-anchored convenience surface cannot drift from the explicit
    # what-if surface.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        a = client.get(
            f"/api/entitlement/next-tier-feature-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/feature-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["features"] == b["features"], tier


def test_endpoint_previous_tier_feature_catalog_at_matches_feature_catalog_at(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        a = client.get(
            f"/api/entitlement/previous-tier-feature-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/feature-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["features"] == b["features"], tier


def test_endpoint_next_tier_runtime_catalog_at_matches_runtime_catalog_at(
    ent, client
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        a = client.get(
            f"/api/entitlement/next-tier-runtime-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/runtime-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["runtimes"] == b["runtimes"], tier


def test_endpoint_previous_tier_runtime_catalog_at_matches_runtime_catalog_at(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        a = client.get(
            f"/api/entitlement/previous-tier-runtime-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/runtime-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["runtimes"] == b["runtimes"], tier


# ═══════════════════════════════════════════════════════════════════════
# End-to-end sweep across every source rung
# ═══════════════════════════════════════════════════════════════════════


def test_next_tier_feature_catalog_at_endpoint_full_sweep(ent, client):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/next-tier-feature-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES, tier
        expected = ent.next_tier_feature_catalog_at(tier) or []
        assert body["features"] == expected, tier


def test_previous_tier_feature_catalog_at_endpoint_full_sweep(ent, client):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/previous-tier-feature-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES, tier
        expected = ent.previous_tier_feature_catalog_at(tier) or []
        assert body["features"] == expected, tier


def test_next_tier_runtime_catalog_at_endpoint_full_sweep(ent, client):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/next-tier-runtime-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES, tier
        expected = ent.next_tier_runtime_catalog_at(tier) or []
        assert body["runtimes"] == expected, tier


def test_previous_tier_runtime_catalog_at_endpoint_full_sweep(ent, client):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/previous-tier-runtime-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES, tier
        expected = ent.previous_tier_runtime_catalog_at(tier) or []
        assert body["runtimes"] == expected, tier
