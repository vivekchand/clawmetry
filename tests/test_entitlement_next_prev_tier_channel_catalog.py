"""Tests for ``Entitlement.next_tier_channel_catalog`` /
``previous_tier_channel_catalog``, the module-level convenience helpers,
and the two companion
``/api/entitlement/{next,previous}-tier-channel-catalog`` endpoints.

Channel-axis catalog projection of ``{next,previous}_tier_spec``: where
those helpers return the full :func:`tier_spec`-shape descriptor of the
rung one above / below the resolved entitlement, these helpers return
the full :func:`channel_catalog_at`-shape catalogue for every
chat-channel adapter at that rung -- one row per adapter -- so an
upgrade-preview panel can hydrate the whole channel matrix at the next
(or previous) rung off ONE round-trip without threading the target tier
through query args or first fetching ``/entitlement`` for ``next_tier``.

Every chat channel is FREE at every tier (the ``channels`` capacity axis
governs how many concurrent channels each plan admits, not which
adapters unlock), so the returned rows are byte-identical across every
target rung: every row is ``free=True`` / ``allowed=True`` /
``locked=False`` / ``entitled=True``. That parity IS the answer: a
pricing tooltip / upgrade panel can render "all N chat channels included
at every plan" off ONE call without hard-coding the posture client-side.
The invariant is pinned in the tests.

Pins covered here:

* method vs :func:`channel_catalog_at` identity for next/previous across
  every purchasable source -- the convenience cannot drift from the
  explicit ``channel_catalog_at(self.next_purchasable_tier())``
  composition
* ceiling / floor returns ``None`` (Enterprise has no next; OSS /
  cloud_free have no previous)
* trial-as-source resolves the same way the sibling next/previous
  channel-spec / feature-runtime-spec families do: next -> enterprise,
  previous -> cloud_starter
* the always-free invariant reaches every row for every purchasable
  source (row-key set matches ``channel_catalog_at``; every row is
  ``free=True`` / ``allowed=True`` / ``locked=False`` /
  ``entitled=True``)
* row order is alphabetical (byte-identical to the sibling
  ``channel_catalog_at`` sort) so a pricing panel doesn't reshuffle on
  redeploy
* row count matches ``ALL_CHANNELS`` (one row per adapter)
* labels come from the ``channel_label`` helper
* grace vs enforce yields identical bodies (catalog-derived; every row
  is free)
* module-level wrappers agree with the class methods against the
  resolved entitlement
* the helpers never raise -- a resolver failure short-circuits to
  ``None`` so the panel stays mute instead of breaking
* the two API endpoints never 5xx: happy path returns a 200 envelope
  with the full ``channels`` list; at the ceiling / floor ``channels``
  collapses to ``[]`` and ``target`` / ``target_label`` /
  ``target_rank`` to ``null``; a synthesised resolver failure yields
  the grace-shape envelope
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "channels",
    "grace",
    "enforced",
}

_ROW_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}


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


# ── Entitlement.next_tier_channel_catalog ────────────────────────────────


def test_next_tier_channel_catalog_matches_channel_catalog_at(ent):
    # next_tier_channel_catalog() is a convenience for
    # channel_catalog_at(self.next_purchasable_tier()) -- they must be
    # byte-equal across every purchasable source so a caller can use the
    # convenience interchangeably with the explicit composition.
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
        assert e.next_tier_channel_catalog() == ent.channel_catalog_at(nxt)


def test_next_tier_channel_catalog_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above
    # to preview, so the convenience returns None just like
    # next_purchasable_tier().
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    assert e.next_tier_channel_catalog() is None


def test_next_tier_channel_catalog_trial_source(ent):
    # Trial acts as cloud_pro for reachability but sits above cloud_pro on
    # the ladder, so the "next" rung for a trial install is enterprise --
    # matching how the sibling next_tier_spec / next_tier_channel_spec
    # families resolve trial.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    target = e.next_purchasable_tier()
    assert target == ent.TIER_ENTERPRISE
    assert e.next_tier_channel_catalog() == ent.channel_catalog_at(target)


def test_next_tier_channel_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_channel_catalog()
    assert rows is not None
    assert len(rows) == len(ent.ALL_CHANNELS)
    assert {row["id"] for row in rows} == set(ent.ALL_CHANNELS)


def test_next_tier_channel_catalog_sorted_alphabetically(ent):
    # Row order must be stable across releases so a pricing / upgrade
    # panel doesn't reshuffle on redeploy.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_channel_catalog()
    assert rows is not None
    assert [row["id"] for row in rows] == sorted(ent.ALL_CHANNELS)


def test_next_tier_channel_catalog_row_schema(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_channel_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS, row


def test_next_tier_channel_catalog_every_row_is_free(ent):
    # Every chat channel is FREE at every tier, so every row must come back
    # unlocked / allowed / entitled regardless of the target rung.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        rows = e.next_tier_channel_catalog()
        assert rows is not None, tier
        for row in rows:
            assert row["free"] is True, (tier, row)
            assert row["tier"] == "free", (tier, row)
            assert row["allowed"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


def test_next_tier_channel_catalog_labels_come_from_channel_label(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    rows = e.next_tier_channel_catalog()
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.channel_label(row["id"])


def test_next_tier_channel_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    # If next_purchasable_tier blows up, the helper must swallow and return
    # None so the upgrade-preview panel stays mute rather than 500-ing.
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_channel_catalog() is None


def test_next_tier_channel_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    # Every row is free, so flipping enforcement must not change the
    # returned catalogue for any purchasable source.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.next_tier_channel_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.next_tier_channel_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Entitlement.previous_tier_channel_catalog ────────────────────────────


def test_previous_tier_channel_catalog_matches_channel_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert e.previous_tier_channel_catalog() == ent.channel_catalog_at(
            prev
        )


def test_previous_tier_channel_catalog_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below, so previous
    # convenience returns None.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        assert e.previous_tier_channel_catalog() is None


def test_previous_tier_channel_catalog_trial_source(ent):
    # Trial's previous purchasable rung is cloud_starter -- matches the
    # sibling previous_tier_* families.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    prev = e.previous_purchasable_tier()
    assert prev == ent.TIER_CLOUD_STARTER
    assert e.previous_tier_channel_catalog() == ent.channel_catalog_at(prev)


def test_previous_tier_channel_catalog_row_count_and_ids(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    rows = e.previous_tier_channel_catalog()
    assert rows is not None
    assert len(rows) == len(ent.ALL_CHANNELS)
    assert {row["id"] for row in rows} == set(ent.ALL_CHANNELS)


def test_previous_tier_channel_catalog_sorted_alphabetically(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    rows = e.previous_tier_channel_catalog()
    assert rows is not None
    assert [row["id"] for row in rows] == sorted(ent.ALL_CHANNELS)


def test_previous_tier_channel_catalog_row_schema(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    rows = e.previous_tier_channel_catalog()
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS, row


def test_previous_tier_channel_catalog_every_row_is_free(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        rows = e.previous_tier_channel_catalog()
        assert rows is not None, tier
        for row in rows:
            assert row["free"] is True, (tier, row)
            assert row["tier"] == "free", (tier, row)
            assert row["allowed"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


def test_previous_tier_channel_catalog_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_channel_catalog() is None


def test_previous_tier_channel_catalog_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e_grace = ent._build(tier, "test")
        grace = e_grace.previous_tier_channel_catalog()
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        e_enforce = ent._build(tier, "test")
        enforce = e_enforce.previous_tier_channel_catalog()
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── Module-level next_tier_channel_catalog / previous_tier_channel_catalog


def test_module_next_tier_channel_catalog_matches_method(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_channel_catalog() == e.next_tier_channel_catalog()


def test_module_previous_tier_channel_catalog_matches_method(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert (
        ent.previous_tier_channel_catalog()
        == e.previous_tier_channel_catalog()
    )


def test_module_next_tier_channel_catalog_ceiling_is_none(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.next_tier_channel_catalog() is None


def test_module_previous_tier_channel_catalog_floor_is_none(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_OSS, "auto")
    monkeypatch.setattr(ent, "get_entitlement", lambda: e)
    assert ent.previous_tier_channel_catalog() is None


def test_module_next_tier_channel_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_channel_catalog() is None


def test_module_previous_tier_channel_catalog_swallows_resolver_failure(
    ent, monkeypatch
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_channel_catalog() is None


# ── /api/entitlement/next-tier-channel-catalog ───────────────────────────


def test_endpoint_next_tier_channel_catalog_200(client):
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    assert resp.status_code == 200


def test_endpoint_next_tier_channel_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_endpoint_next_tier_channel_catalog_rows_byte_equal_helper(
    ent, client
):
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        # At the ceiling the endpoint collapses to channels=[]; nothing
        # to pin against the sibling helper.
        assert body["channels"] == []
        return
    assert body["channels"] == ent.channel_catalog_at(target)


def test_endpoint_next_tier_channel_catalog_ceiling_shape(
    ent, monkeypatch, client
):
    # Force an at-ceiling perspective so target must collapse.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_ENTERPRISE, "license"),
    )
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["channels"] == []


def test_endpoint_next_tier_channel_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["channels"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_next_tier_channel_catalog_always_free_invariant(client):
    resp = client.get("/api/entitlement/next-tier-channel-catalog")
    body = resp.get_json()
    for row in body["channels"]:
        assert row["free"] is True, row
        assert row["locked"] is False, row
        assert row["entitled"] is True, row


# ── /api/entitlement/previous-tier-channel-catalog ───────────────────────


def test_endpoint_previous_tier_channel_catalog_200(client):
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    assert resp.status_code == 200


def test_endpoint_previous_tier_channel_catalog_envelope_keys(client):
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_endpoint_previous_tier_channel_catalog_rows_byte_equal_helper(
    ent, client
):
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    body = resp.get_json()
    target = body["target"]
    if target is None:
        assert body["channels"] == []
        return
    assert body["channels"] == ent.channel_catalog_at(target)


def test_endpoint_previous_tier_channel_catalog_floor_shape(
    ent, monkeypatch, client
):
    # Force a floor perspective so target must collapse.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_OSS, "auto"),
    )
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["channels"] == []


def test_endpoint_previous_tier_channel_catalog_pro_perspective_shape(
    ent, monkeypatch, client
):
    # Cloud pro's previous rung is cloud_starter -- pin the target echo.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["channels"] == ent.channel_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_channel_catalog_never_5xxs_on_resolver_failure(
    ent, monkeypatch, client
):
    def boom():
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["channels"] == []
    assert body["target"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_previous_tier_channel_catalog_always_free_invariant(
    ent, monkeypatch, client
):
    # Force a non-floor perspective so rows populate.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    resp = client.get("/api/entitlement/previous-tier-channel-catalog")
    body = resp.get_json()
    assert body["channels"], "expected rows at cloud_pro perspective"
    for row in body["channels"]:
        assert row["free"] is True, row
        assert row["locked"] is False, row
        assert row["entitled"] is True, row


# ── Cross-endpoint parity with /channel-catalog-at ───────────────────────


def test_endpoint_next_tier_channel_catalog_matches_channel_catalog_at_endpoint(
    ent, monkeypatch, client
):
    # ``/next-tier-channel-catalog`` must be a byte-identical projection of
    # ``/channel-catalog-at?tier=<next_purchasable_tier>`` -- pinning the
    # cross-endpoint parity keeps the convenience surface from drifting
    # from the explicit what-if surface.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_STARTER, "cloud"),
    )
    a = client.get("/api/entitlement/next-tier-channel-catalog").get_json()
    b = client.get(
        f"/api/entitlement/channel-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["channels"] == b["channels"]


def test_endpoint_previous_tier_channel_catalog_matches_channel_catalog_at_endpoint(
    ent, monkeypatch, client
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud"),
    )
    a = client.get("/api/entitlement/previous-tier-channel-catalog").get_json()
    b = client.get(
        f"/api/entitlement/channel-catalog-at?tier={a['target']}"
    ).get_json()
    assert a["channels"] == b["channels"]
