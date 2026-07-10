"""Tests for the resolver-anchored ``next/previous_tier_feature_catalog``
and ``next/previous_tier_runtime_catalog`` accessors -- class methods,
module-level wrappers, and the four companion API endpoints:

* ``/api/entitlement/next-tier-feature-catalog``
* ``/api/entitlement/previous-tier-feature-catalog``
* ``/api/entitlement/next-tier-runtime-catalog``
* ``/api/entitlement/previous-tier-runtime-catalog``

Feature- and runtime-axis mirrors of ``next/previous_tier_channel_catalog``:
where the channel siblings return the full :func:`channel_catalog_at`
catalogue at the rung above / below the resolved entitlement, these
return the full :func:`feature_catalog_at` / :func:`runtime_catalog_at`
catalogue at that same rung -- one row per feature / runtime -- so a
pricing / upgrade-preview panel can hydrate the whole matrix at the next
(or previous) rung off ONE round-trip without threading the target tier
through query args or first fetching ``/entitlement`` for ``next_tier``.

Unlike the channel axis (every chat channel is free at every tier), the
feature / runtime axes tier-gate paid entries, so the returned rows DO
differ across target rungs -- rows for a locked feature flip
``locked`` / ``entitled`` when the resolved perspective climbs above
its ``tier`` threshold. Byte-parity with the explicit
:func:`feature_catalog_at` / :func:`runtime_catalog_at` composition is
pinned so a caller can substitute the convenience for the composition
without behavioural drift.

Pins covered here:

* method vs :func:`feature_catalog_at` / :func:`runtime_catalog_at`
  identity for next/previous across every purchasable source -- the
  convenience cannot drift from the explicit
  ``feature_catalog_at(self.next_purchasable_tier())`` composition
* ceiling / floor returns ``None`` (Enterprise has no next; OSS /
  cloud_free have no previous)
* trial-as-source resolves the same way the sibling next/previous
  channel-catalog / feature-runtime-spec families do: next -> enterprise,
  previous -> cloud_starter
* row key set matches the sibling ``*_catalog_at`` builder for every
  purchasable source (per-axis ``_ROW_KEYS``)
* row order matches the sibling ``*_catalog_at`` builder byte-for-byte
  (feature: free-first-by-tier-rank then id-sorted; runtime: free block
  alpha, then paid block alpha)
* row count matches ``ALL_FEATURES`` / ``FREE_RUNTIMES | PAID_RUNTIMES``
* labels come from the ``feature_label`` / ``runtime_label`` helper
* upgrade unlocks strictly more: at a lower source the next-tier catalog
  exposes at least as many entitled rows as the source catalog (paid
  entries unlock as the perspective climbs)
* grace vs enforce yields identical bodies (catalog-derived; no
  enforcement branch inside the builder)
* module-level wrappers agree with the class methods against the
  resolved entitlement
* the helpers never raise -- a resolver failure short-circuits to
  ``None`` so the panel stays mute instead of breaking
* the four API endpoints never 5xx: happy path returns a 200 envelope
  with the full ``features`` / ``runtimes`` list; at the ceiling / floor
  the list collapses to ``[]`` and ``target`` / ``target_label`` /
  ``target_rank`` to ``null``; a synthesised resolver failure yields
  the grace-shape envelope
* cross-endpoint parity: ``/next-tier-feature-catalog`` rows byte-match
  ``/feature-catalog-at?tier=<target>`` at the resolved target, and the
  runtime siblings mirror the same
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS_FEATURES = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
    "grace",
    "enforced",
}
_ENVELOPE_KEYS_RUNTIMES = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
    "grace",
    "enforced",
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
# ── Entitlement.next_tier_feature_catalog ────────────────────────────────


def test_next_tier_feature_catalog_matches_feature_catalog_at(ent):
    # The convenience must byte-equal
    # feature_catalog_at(self.next_purchasable_tier()) across every
    # purchasable source so callers can swap freely.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        assert nxt is not None
        assert e.next_tier_feature_catalog() == ent.feature_catalog_at(nxt)


def test_next_tier_feature_catalog_returns_none_at_ceiling(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    assert e.next_tier_feature_catalog() is None


def test_next_tier_feature_catalog_trial_source(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    target = e.next_purchasable_tier()
    assert target == ent.TIER_ENTERPRISE
    assert e.next_tier_feature_catalog() == ent.feature_catalog_at(target)


def test_next_tier_feature_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_feature_catalog()
    assert rows is not None
    assert len(rows) == len(ent.ALL_FEATURES)
    assert {row["id"] for row in rows} == set(ent.ALL_FEATURES)


def test_next_tier_feature_catalog_row_order_matches_sibling(ent):
    # Row order must match feature_catalog_at exactly (bit-identical),
    # so a pricing / upgrade panel doesn't reshuffle on redeploy.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_feature_catalog()
    sib = ent.feature_catalog_at(e.next_purchasable_tier())
    assert rows is not None and sib is not None
    assert [row["id"] for row in rows] == [row["id"] for row in sib]


def test_next_tier_feature_catalog_row_schema(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_feature_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _FEATURE_ROW_KEYS, row


def test_next_tier_feature_catalog_labels_come_from_feature_label(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_feature_catalog()
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.feature_label(row["id"])


def test_next_tier_feature_catalog_upgrade_never_regresses_entitled_count(ent):
    # Climbing the ladder can only ever unlock more; the next-tier
    # catalog must expose at least as many entitled rows as the resolved
    # source catalog.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        src = ent.feature_catalog_at(tier)
        nxt = e.next_tier_feature_catalog()
        assert src is not None and nxt is not None
        src_entitled = sum(1 for r in src if r["entitled"])
        nxt_entitled = sum(1 for r in nxt if r["entitled"])
        assert nxt_entitled >= src_entitled, tier


def test_next_tier_feature_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_feature_catalog() is None


def test_next_tier_feature_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.next_tier_feature_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.next_tier_feature_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Entitlement.previous_tier_feature_catalog ────────────────────────────


def test_previous_tier_feature_catalog_matches_feature_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert e.previous_tier_feature_catalog() == ent.feature_catalog_at(prev)


def test_previous_tier_feature_catalog_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        assert e.previous_tier_feature_catalog() is None


def test_previous_tier_feature_catalog_trial_source(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    prev = e.previous_purchasable_tier()
    assert prev == ent.TIER_CLOUD_STARTER
    assert e.previous_tier_feature_catalog() == ent.feature_catalog_at(prev)


def test_previous_tier_feature_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    rows = e.previous_tier_feature_catalog()
    assert rows is not None
    assert len(rows) == len(ent.ALL_FEATURES)
    assert {row["id"] for row in rows} == set(ent.ALL_FEATURES)


def test_previous_tier_feature_catalog_row_schema(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    rows = e.previous_tier_feature_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _FEATURE_ROW_KEYS, row


def test_previous_tier_feature_catalog_downgrade_never_gains_entitled_rows(ent):
    # A downgrade cannot unlock rows the source didn't have.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        src = ent.feature_catalog_at(tier)
        prev = e.previous_tier_feature_catalog()
        assert src is not None and prev is not None
        src_entitled = sum(1 for r in src if r["entitled"])
        prev_entitled = sum(1 for r in prev if r["entitled"])
        assert prev_entitled <= src_entitled, tier


def test_previous_tier_feature_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_feature_catalog() is None


def test_previous_tier_feature_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.previous_tier_feature_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.previous_tier_feature_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Module-level next/previous_tier_feature_catalog ──────────────────────


def test_module_next_tier_feature_catalog_matches_method(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_feature_catalog() == e.next_tier_feature_catalog()


def test_module_previous_tier_feature_catalog_matches_method(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert (
        ent.previous_tier_feature_catalog()
        == e.previous_tier_feature_catalog()
    )


def test_module_next_tier_feature_catalog_ceiling_is_none(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_feature_catalog() is None


def test_module_previous_tier_feature_catalog_floor_is_none(ent, monkeypatch):
    e = ent._build(ent.TIER_OSS, "auto")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.previous_tier_feature_catalog() is None


def test_module_next_tier_feature_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_feature_catalog() is None


def test_module_previous_tier_feature_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_feature_catalog() is None


# ── /api/entitlement/next-tier-feature-catalog ───────────────────────────


def test_endpoint_next_tier_feature_catalog_200(client):
    resp = client.get("/api/entitlement/next-tier-feature-catalog")
    assert resp.status_code == 200


def test_endpoint_next_tier_feature_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/next-tier-feature-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES


def test_endpoint_next_tier_feature_catalog_rows_byte_equal_helper(ent, client):
    resp = client.get("/api/entitlement/next-tier-feature-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        assert body["features"] == []
        return
    assert body["features"] == ent.feature_catalog_at(target)


def test_endpoint_next_tier_feature_catalog_ceiling_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_ENTERPRISE, "license"),
    )
    resp = client.get("/api/entitlement/next-tier-feature-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["features"] == []


def test_endpoint_next_tier_feature_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/next-tier-feature-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES
    assert body["features"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


# ── /api/entitlement/previous-tier-feature-catalog ───────────────────────


def test_endpoint_previous_tier_feature_catalog_200(client):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    assert resp.status_code == 200


def test_endpoint_previous_tier_feature_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES


def test_endpoint_previous_tier_feature_catalog_rows_byte_equal_helper(
    ent, client
):
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        assert body["features"] == []
        return
    assert body["features"] == ent.feature_catalog_at(target)


def test_endpoint_previous_tier_feature_catalog_floor_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_OSS, "auto"),
    )
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["features"] == []


def test_endpoint_previous_tier_feature_catalog_pro_perspective_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["features"] == ent.feature_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_feature_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/previous-tier-feature-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_FEATURES
    assert body["features"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


# ── Cross-endpoint parity with /feature-catalog-at ───────────────────────


def test_endpoint_next_tier_feature_catalog_matches_feature_catalog_at_endpoint(
    ent, monkeypatch, client
):
    # ``/next-tier-feature-catalog`` must be a byte-identical projection of
    # ``/feature-catalog-at?tier=<next_purchasable_tier>`` -- pins that
    # the convenience surface can't drift from the explicit what-if surface.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_CLOUD_STARTER, "cloud"),
    )
    a = client.get("/api/entitlement/next-tier-feature-catalog").get_json()
    b = client.get(
        f"/api/entitlement/feature-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["features"] == b["features"]


def test_endpoint_previous_tier_feature_catalog_matches_feature_catalog_at_endpoint(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    a = client.get(
        "/api/entitlement/previous-tier-feature-catalog"
    ).get_json()
    b = client.get(
        f"/api/entitlement/feature-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["features"] == b["features"]


# ═══════════════════════════════════════════════════════════════════════
# RUNTIME AXIS
# ═══════════════════════════════════════════════════════════════════════
#
# ── Entitlement.next_tier_runtime_catalog ────────────────────────────────


def test_next_tier_runtime_catalog_matches_runtime_catalog_at(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        assert nxt is not None
        assert e.next_tier_runtime_catalog() == ent.runtime_catalog_at(nxt)


def test_next_tier_runtime_catalog_returns_none_at_ceiling(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    assert e.next_tier_runtime_catalog() is None


def test_next_tier_runtime_catalog_trial_source(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    target = e.next_purchasable_tier()
    assert target == ent.TIER_ENTERPRISE
    assert e.next_tier_runtime_catalog() == ent.runtime_catalog_at(target)


def test_next_tier_runtime_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_runtime_catalog()
    assert rows is not None
    expected_ids = set(ent.FREE_RUNTIMES) | set(ent.PAID_RUNTIMES)
    assert len(rows) == len(expected_ids)
    assert {row["id"] for row in rows} == expected_ids


def test_next_tier_runtime_catalog_row_order_matches_sibling(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_runtime_catalog()
    sib = ent.runtime_catalog_at(e.next_purchasable_tier())
    assert rows is not None and sib is not None
    assert [row["id"] for row in rows] == [row["id"] for row in sib]


def test_next_tier_runtime_catalog_row_schema(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_runtime_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS, row


def test_next_tier_runtime_catalog_labels_come_from_runtime_label(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_runtime_catalog()
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.runtime_label(row["id"])


def test_next_tier_runtime_catalog_free_runtimes_always_entitled(ent):
    # Free runtimes stay free at every rung; a paid rung can only add
    # paid runtimes, never lock the free ones.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        rows = e.next_tier_runtime_catalog()
        assert rows is not None, tier
        for row in rows:
            if row["free"]:
                assert row["allowed"] is True, (tier, row)
                assert row["locked"] is False, (tier, row)
                assert row["entitled"] is True, (tier, row)


def test_next_tier_runtime_catalog_upgrade_never_regresses_entitled_count(
    ent,
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        src = ent.runtime_catalog_at(tier)
        nxt = e.next_tier_runtime_catalog()
        assert src is not None and nxt is not None
        src_entitled = sum(1 for r in src if r["entitled"])
        nxt_entitled = sum(1 for r in nxt if r["entitled"])
        assert nxt_entitled >= src_entitled, tier


def test_next_tier_runtime_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_runtime_catalog() is None


def test_next_tier_runtime_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.next_tier_runtime_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.next_tier_runtime_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Entitlement.previous_tier_runtime_catalog ────────────────────────────


def test_previous_tier_runtime_catalog_matches_runtime_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert e.previous_tier_runtime_catalog() == ent.runtime_catalog_at(prev)


def test_previous_tier_runtime_catalog_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        assert e.previous_tier_runtime_catalog() is None


def test_previous_tier_runtime_catalog_trial_source(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    prev = e.previous_purchasable_tier()
    assert prev == ent.TIER_CLOUD_STARTER
    assert e.previous_tier_runtime_catalog() == ent.runtime_catalog_at(prev)


def test_previous_tier_runtime_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    rows = e.previous_tier_runtime_catalog()
    assert rows is not None
    expected_ids = set(ent.FREE_RUNTIMES) | set(ent.PAID_RUNTIMES)
    assert len(rows) == len(expected_ids)
    assert {row["id"] for row in rows} == expected_ids


def test_previous_tier_runtime_catalog_row_schema(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    rows = e.previous_tier_runtime_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS, row


def test_previous_tier_runtime_catalog_free_runtimes_always_entitled(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        rows = e.previous_tier_runtime_catalog()
        assert rows is not None, tier
        for row in rows:
            if row["free"]:
                assert row["allowed"] is True, (tier, row)
                assert row["locked"] is False, (tier, row)
                assert row["entitled"] is True, (tier, row)


def test_previous_tier_runtime_catalog_downgrade_never_gains_entitled_rows(
    ent,
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        src = ent.runtime_catalog_at(tier)
        prev = e.previous_tier_runtime_catalog()
        assert src is not None and prev is not None
        src_entitled = sum(1 for r in src if r["entitled"])
        prev_entitled = sum(1 for r in prev if r["entitled"])
        assert prev_entitled <= src_entitled, tier


def test_previous_tier_runtime_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_runtime_catalog() is None


def test_previous_tier_runtime_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.previous_tier_runtime_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.previous_tier_runtime_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Module-level next/previous_tier_runtime_catalog ──────────────────────


def test_module_next_tier_runtime_catalog_matches_method(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_runtime_catalog() == e.next_tier_runtime_catalog()


def test_module_previous_tier_runtime_catalog_matches_method(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert (
        ent.previous_tier_runtime_catalog()
        == e.previous_tier_runtime_catalog()
    )


def test_module_next_tier_runtime_catalog_ceiling_is_none(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_runtime_catalog() is None


def test_module_previous_tier_runtime_catalog_floor_is_none(ent, monkeypatch):
    e = ent._build(ent.TIER_OSS, "auto")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.previous_tier_runtime_catalog() is None


def test_module_next_tier_runtime_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_runtime_catalog() is None


def test_module_previous_tier_runtime_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_runtime_catalog() is None


# ── /api/entitlement/next-tier-runtime-catalog ───────────────────────────


def test_endpoint_next_tier_runtime_catalog_200(client):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog")
    assert resp.status_code == 200


def test_endpoint_next_tier_runtime_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES


def test_endpoint_next_tier_runtime_catalog_rows_byte_equal_helper(ent, client):
    resp = client.get("/api/entitlement/next-tier-runtime-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        assert body["runtimes"] == []
        return
    assert body["runtimes"] == ent.runtime_catalog_at(target)


def test_endpoint_next_tier_runtime_catalog_ceiling_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_ENTERPRISE, "license"),
    )
    resp = client.get("/api/entitlement/next-tier-runtime-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["runtimes"] == []


def test_endpoint_next_tier_runtime_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/next-tier-runtime-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES
    assert body["runtimes"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


# ── /api/entitlement/previous-tier-runtime-catalog ───────────────────────


def test_endpoint_previous_tier_runtime_catalog_200(client):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    assert resp.status_code == 200


def test_endpoint_previous_tier_runtime_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES


def test_endpoint_previous_tier_runtime_catalog_rows_byte_equal_helper(
    ent, client
):
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        assert body["runtimes"] == []
        return
    assert body["runtimes"] == ent.runtime_catalog_at(target)


def test_endpoint_previous_tier_runtime_catalog_floor_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_OSS, "auto"),
    )
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["runtimes"] == []


def test_endpoint_previous_tier_runtime_catalog_pro_perspective_shape(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["runtimes"] == ent.runtime_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_runtime_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/previous-tier-runtime-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS_RUNTIMES
    assert body["runtimes"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


# ── Cross-endpoint parity with /runtime-catalog-at ───────────────────────


def test_endpoint_next_tier_runtime_catalog_matches_runtime_catalog_at_endpoint(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_CLOUD_STARTER, "cloud"),
    )
    a = client.get("/api/entitlement/next-tier-runtime-catalog").get_json()
    b = client.get(
        f"/api/entitlement/runtime-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["runtimes"] == b["runtimes"]


def test_endpoint_previous_tier_runtime_catalog_matches_runtime_catalog_at_endpoint(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    a = client.get(
        "/api/entitlement/previous-tier-runtime-catalog"
    ).get_json()
    b = client.get(
        f"/api/entitlement/runtime-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["runtimes"] == b["runtimes"]
