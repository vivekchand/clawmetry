"""Tests for ``next_tier_channel_catalog_at`` /
``previous_tier_channel_catalog_at``, the source-anchored channel-axis
catalog helpers, and the two companion
``/api/entitlement/{next,previous}-tier-channel-catalog-at`` endpoints.

Source-anchored channel-axis catalog projection of
``{next,previous}_tier_spec_at``: where those helpers return the full
:func:`tier_spec`-shape descriptor of the rung one above / below an
explicit source, these helpers return the full
:func:`channel_catalog_at`-shape catalogue for every chat-channel adapter
at that rung -- one row per adapter -- so an upgrade-preview panel
walking an explicit source rung (a pricing-comparison matrix, an "at
each rung" table) can hydrate the whole channel matrix at the next / previous
rung off ONE round-trip.

Every chat channel is FREE at every tier (the ``channels`` capacity axis
governs how many concurrent channels each plan admits, not which
adapters unlock), so the returned rows are byte-identical across every
target rung: every row is ``free=True`` / ``allowed=True`` /
``locked=False`` / ``entitled=True``. That parity IS the answer: a
pricing tooltip / upgrade panel can render "all N chat channels included
at every plan" off ONE call without hard-coding the posture client-side.
The invariant is pinned in the tests.

Pins covered here:

* helper vs :func:`channel_catalog_at` identity for next/previous across
  every purchasable source -- the convenience cannot drift from the
  explicit ``channel_catalog_at(_next_purchasable_tier_after(tier))``
  composition
* helper vs resolver-anchored ``Entitlement.next_tier_channel_catalog``
  byte-identity at the shared source rung (the two must agree when
  ``tier`` matches the resolved current)
* ceiling / floor returns ``None`` (enterprise has no next; oss /
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
* unknown / empty / whitespace / case handling: helpers return ``None``,
  endpoints return 400 on missing tier and 404 on unknown tier
* the helpers never raise -- a builder failure short-circuits to
  ``None`` so the panel stays mute instead of breaking
* the two API endpoints never 5xx: happy path returns a 200 envelope
  with the full ``channels`` list; at the ceiling / floor ``channels``
  collapses to ``[]`` and ``target`` / ``target_label`` /
  ``target_rank`` to ``null``; a synthesised failure yields the
  grace-shape envelope (200 with ``channels=[]``)
* endpoint ``channels`` byte-matches ``/channel-catalog-at?tier=<target>``
  at the resolved target rung
* end-to-end sweep across every source rung confirms the always-free
  posture holds at both the helper and endpoint layer
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "channels",
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


# ── next_tier_channel_catalog_at helper ──────────────────────────────────


def test_next_tier_channel_catalog_at_matches_channel_catalog_at(ent):
    # next_tier_channel_catalog_at(tier) is a convenience for
    # channel_catalog_at(_next_purchasable_tier_after(tier)) -- they must
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
        assert ent.next_tier_channel_catalog_at(tier) == ent.channel_catalog_at(
            target
        )


def test_next_tier_channel_catalog_at_agrees_with_resolver_method(
    ent, monkeypatch
):
    # At the resolved source the helper and the resolver-anchored method
    # must return byte-identical bodies (both compose channel_catalog_at
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
        assert ent.next_tier_channel_catalog_at(
            tier
        ) == e.next_tier_channel_catalog()


def test_next_tier_channel_catalog_at_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung
    # above to preview, so the convenience returns None just like
    # _next_purchasable_tier_after.
    assert ent.next_tier_channel_catalog_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_channel_catalog_at_trial_source(ent):
    # Trial acts as cloud_pro for reachability but sits above cloud_pro
    # on the ladder, so the "next" rung for a trial source is enterprise
    # -- matching how the sibling next_tier_spec / next_tier_channel_spec
    # families resolve trial.
    target = ent._next_purchasable_tier_after(ent.TIER_TRIAL)
    assert target == ent.TIER_ENTERPRISE
    assert ent.next_tier_channel_catalog_at(
        ent.TIER_TRIAL
    ) == ent.channel_catalog_at(target)


def test_next_tier_channel_catalog_at_row_count_and_ids(ent):
    rows = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    assert len(rows) == len(ent.ALL_CHANNELS)
    assert {row["id"] for row in rows} == set(ent.ALL_CHANNELS)


def test_next_tier_channel_catalog_at_sorted_alphabetically(ent):
    rows = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    assert [row["id"] for row in rows] == sorted(ent.ALL_CHANNELS)


def test_next_tier_channel_catalog_at_row_schema(ent):
    rows = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS, row


def test_next_tier_channel_catalog_at_every_row_is_free(ent):
    # Every chat channel is FREE at every tier, so every row must come
    # back unlocked / allowed / entitled regardless of the source rung.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        rows = ent.next_tier_channel_catalog_at(tier)
        assert rows is not None, tier
        for row in rows:
            assert row["free"] is True, (tier, row)
            assert row["tier"] == "free", (tier, row)
            assert row["allowed"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


def test_next_tier_channel_catalog_at_labels_from_channel_label(ent):
    rows = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER)
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.channel_label(row["id"])


def test_next_tier_channel_catalog_at_none_for_empty_tier(ent):
    assert ent.next_tier_channel_catalog_at("") is None
    assert ent.next_tier_channel_catalog_at("   ") is None
    assert ent.next_tier_channel_catalog_at(None) is None


def test_next_tier_channel_catalog_at_none_for_unknown_tier(ent):
    assert ent.next_tier_channel_catalog_at("bogus_tier_xyz") is None


def test_next_tier_channel_catalog_at_case_insensitive(ent):
    lower = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER)
    upper = ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER.upper())
    mixed = ent.next_tier_channel_catalog_at(
        f" {ent.TIER_CLOUD_STARTER.capitalize()}  "
    )
    assert lower == upper == mixed


def test_next_tier_channel_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    # If channel_catalog_at blows up, the helper must swallow and return
    # None so the preview surface stays mute rather than 500-ing.
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "channel_catalog_at", boom)
    assert ent.next_tier_channel_catalog_at(ent.TIER_CLOUD_STARTER) is None


def test_next_tier_channel_catalog_at_grace_and_enforce_are_identical(
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
        grace = ent.next_tier_channel_catalog_at(tier)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_channel_catalog_at(tier)
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── previous_tier_channel_catalog_at helper ──────────────────────────────


def test_previous_tier_channel_catalog_at_matches_channel_catalog_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(tier)
        assert target is not None, tier
        assert ent.previous_tier_channel_catalog_at(
            tier
        ) == ent.channel_catalog_at(target)


def test_previous_tier_channel_catalog_at_agrees_with_resolver_method(
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
        assert ent.previous_tier_channel_catalog_at(
            tier
        ) == e.previous_tier_channel_catalog()


def test_previous_tier_channel_catalog_at_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below, so previous
    # convenience returns None.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent.previous_tier_channel_catalog_at(tier) is None


def test_previous_tier_channel_catalog_at_trial_source(ent):
    # Trial's previous purchasable rung is cloud_starter -- matches the
    # sibling previous_tier_* families.
    target = ent._previous_purchasable_tier_before(ent.TIER_TRIAL)
    assert target == ent.TIER_CLOUD_STARTER
    assert ent.previous_tier_channel_catalog_at(
        ent.TIER_TRIAL
    ) == ent.channel_catalog_at(target)


def test_previous_tier_channel_catalog_at_row_count_and_ids(ent):
    rows = ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert len(rows) == len(ent.ALL_CHANNELS)
    assert {row["id"] for row in rows} == set(ent.ALL_CHANNELS)


def test_previous_tier_channel_catalog_at_sorted_alphabetically(ent):
    rows = ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert [row["id"] for row in rows] == sorted(ent.ALL_CHANNELS)


def test_previous_tier_channel_catalog_at_row_schema(ent):
    rows = ent.previous_tier_channel_catalog_at(ent.TIER_ENTERPRISE)
    assert rows is not None
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS, row


def test_previous_tier_channel_catalog_at_every_row_is_free(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        rows = ent.previous_tier_channel_catalog_at(tier)
        assert rows is not None, tier
        for row in rows:
            assert row["free"] is True, (tier, row)
            assert row["tier"] == "free", (tier, row)
            assert row["allowed"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


def test_previous_tier_channel_catalog_at_labels_from_channel_label(ent):
    rows = ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    for row in rows:
        assert row["label"] == ent.channel_label(row["id"])


def test_previous_tier_channel_catalog_at_none_for_empty_tier(ent):
    assert ent.previous_tier_channel_catalog_at("") is None
    assert ent.previous_tier_channel_catalog_at("   ") is None
    assert ent.previous_tier_channel_catalog_at(None) is None


def test_previous_tier_channel_catalog_at_none_for_unknown_tier(ent):
    assert ent.previous_tier_channel_catalog_at("bogus_tier_xyz") is None


def test_previous_tier_channel_catalog_at_case_insensitive(ent):
    lower = ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO)
    upper = ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO.upper())
    mixed = ent.previous_tier_channel_catalog_at(
        f" {ent.TIER_CLOUD_PRO.capitalize()}  "
    )
    assert lower == upper == mixed


def test_previous_tier_channel_catalog_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "channel_catalog_at", boom)
    assert ent.previous_tier_channel_catalog_at(ent.TIER_CLOUD_PRO) is None


def test_previous_tier_channel_catalog_at_grace_and_enforce_are_identical(
    ent, monkeypatch
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        grace = ent.previous_tier_channel_catalog_at(tier)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.previous_tier_channel_catalog_at(tier)
        assert grace == enforce, tier
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


# ── /api/entitlement/next-tier-channel-catalog-at ────────────────────────


def test_endpoint_next_tier_channel_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200


def test_endpoint_next_tier_channel_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_endpoint_next_tier_channel_catalog_at_rows_byte_equal_helper(
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
            f"/api/entitlement/next-tier-channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["channels"] == ent.next_tier_channel_catalog_at(tier)


def test_endpoint_next_tier_channel_catalog_at_source_echo(ent, client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)


def test_endpoint_next_tier_channel_catalog_at_target_echo(ent, client):
    # cloud_starter's next rung is cloud_pro -- pin the target echo.
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=cloud_starter"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_endpoint_next_tier_channel_catalog_at_ceiling_shape(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-channel-catalog-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["channels"] == []


def test_endpoint_next_tier_channel_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/next-tier-channel-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["channels"] == ent.channel_catalog_at(ent.TIER_ENTERPRISE)


def test_endpoint_next_tier_channel_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/next-tier-channel-catalog-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_endpoint_next_tier_channel_catalog_at_blank_tier_400(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_next_tier_channel_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_xyz"


def test_endpoint_next_tier_channel_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_channel_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/next-tier-channel-catalog-at?tier=cloud_starter"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] == []
    assert body["tier"] == "cloud_starter"


def test_endpoint_next_tier_channel_catalog_at_always_free_invariant(
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
            f"/api/entitlement/next-tier-channel-catalog-at?tier={tier}"
        )
        body = resp.get_json()
        assert body["channels"], tier
        for row in body["channels"]:
            assert row["free"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


# ── /api/entitlement/previous-tier-channel-catalog-at ────────────────────


def test_endpoint_previous_tier_channel_catalog_at_200(client):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200


def test_endpoint_previous_tier_channel_catalog_at_envelope_keys(client):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_endpoint_previous_tier_channel_catalog_at_rows_byte_equal_helper(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["channels"] == ent.previous_tier_channel_catalog_at(tier)


def test_endpoint_previous_tier_channel_catalog_at_target_echo(ent, client):
    # cloud_pro's previous rung is cloud_starter -- pin the target echo.
    resp = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at?tier=cloud_pro"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_channel_catalog_at_floor_shape(ent, client):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert body["target"] is None, tier
        assert body["target_label"] is None, tier
        assert body["target_rank"] is None, tier
        assert body["channels"] == [], tier


def test_endpoint_previous_tier_channel_catalog_at_trial_source(ent, client):
    resp = client.get(
        f"/api/entitlement/previous-tier-channel-catalog-at?tier={ent.TIER_TRIAL}"
    )
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["channels"] == ent.channel_catalog_at(ent.TIER_CLOUD_STARTER)


def test_endpoint_previous_tier_channel_catalog_at_missing_tier_400(client):
    resp = client.get("/api/entitlement/previous-tier-channel-catalog-at")
    assert resp.status_code == 400


def test_endpoint_previous_tier_channel_catalog_at_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at?tier=bogus_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_xyz"


def test_endpoint_previous_tier_channel_catalog_at_never_5xxs_on_failure(
    ent, monkeypatch, client
):
    def boom(_tier):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_channel_catalog_at", boom)
    resp = client.get(
        "/api/entitlement/previous-tier-channel-catalog-at?tier=cloud_pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] == []
    assert body["tier"] == "cloud_pro"


def test_endpoint_previous_tier_channel_catalog_at_always_free_invariant(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={tier}"
        )
        body = resp.get_json()
        assert body["channels"], tier
        for row in body["channels"]:
            assert row["free"] is True, (tier, row)
            assert row["locked"] is False, (tier, row)
            assert row["entitled"] is True, (tier, row)


# ── Cross-endpoint parity with /channel-catalog-at ───────────────────────


def test_endpoint_next_tier_channel_catalog_at_matches_channel_catalog_at(
    ent, client
):
    # /next-tier-channel-catalog-at?tier=X must byte-match
    # /channel-catalog-at?tier=<_next_purchasable_tier_after(X)> so the
    # source-anchored convenience surface cannot drift from the
    # explicit what-if surface.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        a = client.get(
            f"/api/entitlement/next-tier-channel-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/channel-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["channels"] == b["channels"], tier


def test_endpoint_previous_tier_channel_catalog_at_matches_channel_catalog_at(
    ent, client
):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        a = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={tier}"
        ).get_json()
        assert a["target"] is not None, tier
        b = client.get(
            f"/api/entitlement/channel-catalog-at?tier={a['target']}"
        ).get_json()
        assert a["channels"] == b["channels"], tier


# ── End-to-end sweep across every source rung ────────────────────────────


def test_next_tier_channel_catalog_at_endpoint_full_sweep(ent, client):
    # Every purchasable source rung + trial must yield a 200 envelope
    # whose channels list is byte-identical to the helper. At the ceiling
    # (enterprise) channels collapses to [].
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/next-tier-channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS, tier
        expected = ent.next_tier_channel_catalog_at(tier) or []
        assert body["channels"] == expected, tier


def test_previous_tier_channel_catalog_at_endpoint_full_sweep(ent, client):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/previous-tier-channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS, tier
        expected = ent.previous_tier_channel_catalog_at(tier) or []
        assert body["channels"] == expected, tier
