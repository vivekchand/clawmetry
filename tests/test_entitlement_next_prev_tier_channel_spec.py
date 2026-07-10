"""Tests for ``Entitlement.next_tier_channel_spec`` /
``previous_tier_channel_spec``, their module-level convenience helpers,
and the two companion
``/api/entitlement/{next,previous}-tier-channel-spec`` endpoints.

Channel-axis siblings of the feature/runtime pair covered by
``test_entitlement_next_prev_tier_feature_runtime_spec.py``. Where those
project ONE feature/runtime onto the rung above (or below) the resolved
entitlement, these project ONE chat channel.

The channel-axis invariant is stronger than the feature/runtime axes:
every chat channel is FREE at every tier (see :func:`channel_spec_at`),
so the row always comes back ``free=True`` / ``locked=False`` /
``entitled=True`` regardless of the target rung. That parity IS the
answer -- pricing tooltips can render "chat channel included at every
plan" off ONE call. These tests pin that invariant on both the helper
and the endpoint.

Pins covered here:

* per-source parity with
  ``channel_spec_at(self.next_purchasable_tier(), channel)`` across
  every purchasable source for every channel in ``ALL_CHANNELS``
* ceiling / floor: helper returns ``None`` at the top/bottom rungs;
  endpoint returns 200 with ``target=null`` + ``row=null``
* always-free invariant: whenever ``row`` is not ``None`` it comes back
  ``free=True`` / ``locked=False`` / ``entitled=True`` at every rung
* trial-as-source resolves the same way :meth:`next_tier_spec` does
  (next -> enterprise, previous -> cloud_starter)
* unknown / empty / whitespace / case-insensitive id handling
* grace vs enforce yields byte-identical bodies (catalogue-derived,
  not gated)
* the helpers never raise -- a synthesised resolver failure short-
  circuits to ``None``
* the two endpoints never 5xx: 400 on missing input, 404 on unknown
  ids, 200 with ``row=null`` at the ceiling / floor; a synthesised
  resolver failure yields the grace-shape envelope
* module-level helpers agree with the bound method on the resolved
  entitlement
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENDPOINT_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "channel",
    "target",
    "target_label",
    "target_rank",
    "row",
    "grace",
    "enforced",
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


# ── Entitlement.next_tier_channel_spec ───────────────────────────────────────


def test_next_tier_channel_spec_byte_equals_channel_spec_at(ent):
    # Bare helper is convenience for
    # channel_spec_at(self.next_purchasable_tier(), channel). Pin the
    # per-source parity across every purchasable source for every channel
    # so the bare projection cannot drift from the explicit composition.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        target = e.next_purchasable_tier()
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            assert e.next_tier_channel_spec(channel) == ent.channel_spec_at(
                target, channel
            )


def test_next_tier_channel_spec_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every channel.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    for channel in sorted(ent.ALL_CHANNELS):
        assert e.next_tier_channel_spec(channel) is None


def test_next_tier_channel_spec_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro -- next strictly-higher
    # purchasable rung is enterprise (rank 3). Pins that the bare helper
    # matches the sibling next_tier_spec semantics on trial.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.next_tier_channel_spec("telegram")
    assert body is not None
    assert body == ent.channel_spec_at(ent.TIER_ENTERPRISE, "telegram")


def test_next_tier_channel_spec_unknown_inputs_return_none(ent):
    # Defensive null-paths -- empty / unknown / None / whitespace all
    # collapse to None rather than raising.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    assert e.next_tier_channel_spec("") is None
    assert e.next_tier_channel_spec(None) is None  # type: ignore[arg-type]
    assert e.next_tier_channel_spec("no_such_channel") is None


def test_next_tier_channel_spec_whitespace_and_case_insensitive(ent):
    # Whitespace + case normalisation matches the sibling _at helpers.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    canon = e.next_tier_channel_spec("telegram")
    assert canon is not None
    assert e.next_tier_channel_spec(" TELEGRAM ") == canon


def test_next_tier_channel_spec_always_free_invariant(ent):
    # Channel-axis invariant: every chat channel is FREE at every tier,
    # so the row always comes back free=True / locked=False / entitled=True
    # regardless of the target rung. That parity IS the answer.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        target = e.next_purchasable_tier()
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            row = e.next_tier_channel_spec(channel)
            assert row is not None
            assert row["id"] == channel
            assert row["free"] is True
            assert row["locked"] is False
            assert row["entitled"] is True
            assert row["allowed"] is True


def test_next_tier_channel_spec_never_raises_on_resolver_failure(ent, monkeypatch):
    # A synthesised resolver failure must short-circuit to None so the CTA
    # surface stays mute rather than 500-ing.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_channel_spec("telegram") is None


# ── Entitlement.previous_tier_channel_spec ───────────────────────────────────


def test_previous_tier_channel_spec_byte_equals_channel_spec_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        target = e.previous_purchasable_tier()
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            assert e.previous_tier_channel_spec(channel) == ent.channel_spec_at(
                target, channel
            )


def test_previous_tier_channel_spec_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        for channel in sorted(ent.ALL_CHANNELS):
            assert e.previous_tier_channel_spec(channel) is None


def test_previous_tier_channel_spec_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter) -- highest rank strictly below
    # trial's rank 2.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.previous_tier_channel_spec("telegram")
    assert body is not None
    assert body == ent.channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")


def test_previous_tier_channel_spec_unknown_inputs_return_none(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    assert e.previous_tier_channel_spec("") is None
    assert e.previous_tier_channel_spec(None) is None  # type: ignore[arg-type]
    assert e.previous_tier_channel_spec("no_such") is None


def test_previous_tier_channel_spec_always_free_invariant(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        target = e.previous_purchasable_tier()
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            row = e.previous_tier_channel_spec(channel)
            assert row is not None
            assert row["id"] == channel
            assert row["free"] is True
            assert row["locked"] is False
            assert row["entitled"] is True


def test_previous_tier_channel_spec_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_channel_spec("telegram") is None


# ── grace vs enforce ─────────────────────────────────────────────────────────


def test_grace_and_enforce_yield_same_next_body(ent, monkeypatch):
    # Catalogue-derived (off static per-tier maps), not gated -- so
    # flipping enforce on must not change the body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_channel_spec("telegram")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_channel_spec("telegram")
    assert enforce_body == grace_body


def test_grace_and_enforce_yield_same_previous_body(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    grace_body = e.previous_tier_channel_spec("telegram")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    enforce_body = e2.previous_tier_channel_spec("telegram")
    assert enforce_body == grace_body


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_next_tier_channel_spec_matches_method(ent):
    assert ent.next_tier_channel_spec("telegram") == (
        ent.get_entitlement().next_tier_channel_spec("telegram")
    )


def test_module_previous_tier_channel_spec_matches_method(ent):
    assert ent.previous_tier_channel_spec("telegram") == (
        ent.get_entitlement().previous_tier_channel_spec("telegram")
    )


def test_module_helpers_never_raise(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_channel_spec("telegram") is None
    assert ent.previous_tier_channel_spec("telegram") is None


# ── /api/entitlement/next-tier-channel-spec endpoint ────────────────────────


def test_next_tier_channel_spec_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-channel-spec?channel=telegram")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["channel"] == "telegram"
    # OSS default -> next purchasable is one of the rank-1 tiers.
    assert body["target"] is not None
    assert body["target_label"] == ent.tier_label(body["target"])
    assert body["target_rank"] == ent.tier_rank(body["target"])
    assert body["row"] is not None
    # Always-free invariant reaches the endpoint.
    assert body["row"]["free"] is True
    assert body["row"]["locked"] is False
    assert body["row"]["entitled"] is True
    assert body["grace"] is True
    assert body["enforced"] is False


def test_next_tier_channel_spec_endpoint_missing_channel_400(client):
    rv = client.get("/api/entitlement/next-tier-channel-spec")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing channel"


def test_next_tier_channel_spec_endpoint_blank_channel_400(client):
    rv = client.get("/api/entitlement/next-tier-channel-spec?channel=%20%20")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing channel"


def test_next_tier_channel_spec_endpoint_unknown_channel_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec?channel=no_such_channel"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown channel"
    assert body.get("which") == "channel"
    assert body.get("channel") == "no_such_channel"


def test_next_tier_channel_spec_endpoint_case_normalises(client, ent):
    # Case + whitespace normalisation on the endpoint matches the helper.
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec?channel=%20TELEGRAM%20"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channel"] == "telegram"
    assert body["row"] == ent.get_entitlement().next_tier_channel_spec("telegram")


def test_next_tier_channel_spec_endpoint_row_matches_helper(client, ent):
    # The endpoint's row must byte-equal the underlying helper on the live
    # resolved entitlement -- pin the equivalence so callers can swap the
    # bound endpoint for the helper without copy drift.
    rv = client.get("/api/entitlement/next-tier-channel-spec?channel=telegram")
    body = rv.get_json()
    assert body["row"] == ent.next_tier_channel_spec("telegram")


def test_next_tier_channel_spec_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-channel-spec?channel=telegram")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_KEYS
    assert body["row"] is None
    assert body["target"] is None
    assert body["current_tier"] == "oss"


# ── /api/entitlement/previous-tier-channel-spec endpoint ────────────────────


def test_previous_tier_channel_spec_endpoint_oss_floor(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec?channel=telegram"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- no rung below.
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_previous_tier_channel_spec_endpoint_missing_channel_400(client):
    rv = client.get("/api/entitlement/previous-tier-channel-spec")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing channel"


def test_previous_tier_channel_spec_endpoint_unknown_channel_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec?channel=no_such"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown channel"
    assert body.get("which") == "channel"
    assert body.get("channel") == "no_such"


def test_previous_tier_channel_spec_endpoint_never_raises(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec?channel=telegram"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_KEYS
    assert body["row"] is None
    assert body["target"] is None
    assert body["current_tier"] == "oss"
