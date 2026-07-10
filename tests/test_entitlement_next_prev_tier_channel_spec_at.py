"""Tests for the two channel-axis scalar what-if helpers projecting
:func:`clawmetry.entitlements.next_tier_spec_at` /
:func:`previous_tier_spec_at` onto a single chat channel, and the two
companion ``/api/entitlement/{next,previous}-tier-channel-spec-at``
endpoints.

Channel-axis siblings of the feature/runtime ``_at`` pair covered by
``test_entitlement_next_prev_tier_feature_runtime_spec_at.py``. Where
those project ONE feature/runtime onto the rung above (or below) a
caller-supplied source ``tier``, these project ONE chat channel and
follow the same envelope shape.

Source-anchored companions of the resolver-anchored
``next_tier_channel_spec`` / ``previous_tier_channel_spec`` pair
already covered by
``test_entitlement_next_prev_tier_channel_spec.py``: the resolver
version reads the live perspective off the resolved entitlement, this
pair takes an explicit ``tier=`` so a pricing-comparison matrix can
pivot the "at my next / previous rung" question across every source
rung off one shape.

The channel-axis invariant is stronger than the feature/runtime axes:
every chat channel is FREE at every tier (see :func:`channel_spec_at`),
so the row always comes back ``free=True`` / ``locked=False`` /
``entitled=True`` regardless of the target rung. That parity IS the
answer -- pricing tooltips can render "chat channel included at every
plan" off ONE call. These tests pin that invariant on both the helper
and the endpoint.

Pins covered here:

* per-rung byte-equality with :func:`channel_spec_at` at the resolved
  next/previous purchasable target across every purchasable source for
  every channel in ``ALL_CHANNELS`` (parity)
* ``next`` / ``previous`` align with
  :func:`_next_purchasable_tier_after` /
  :func:`_previous_purchasable_tier_before` so the helpers cannot
  drift from the rung-walker shared with the other ``next_*_at`` family
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  returns ``None`` from the helper, and the API surfaces 200 with
  ``row=null`` + ``target=null`` so the surface keeps rendering
* trial-as-source resolves the same way the sibling ``_at`` families
  do: next -> enterprise, previous -> cloud_starter
* unknown / empty / whitespace / case-insensitive id handling
* always-free invariant: whenever ``row`` is not ``None`` it comes back
  ``free=True`` / ``locked=False`` / ``entitled=True`` at every rung
* grace vs enforce yields byte-identical bodies (catalogue-derived,
  not gated)
* the helpers never raise -- a builder failure short-circuits to
  ``None`` so the CTA surface keeps rendering rather than 500-ing
* the two API endpoints never 5xx: 400 on missing input, 404 on
  unknown ids, 200 with ``row=null`` at the ceiling / floor; an
  internal failure yields the same 200 envelope shape
* endpoint ``row`` byte-matches the helper AND the standalone
  ``/channel-spec-at`` endpoint at the resolved target (no drift
  between the two surfaces)
* module-level helpers match the
  ``Entitlement.next_tier_channel_spec`` /
  ``previous_tier_channel_spec`` methods when the source is the
  resolved entitlement's rank (source-anchored / resolver-anchored
  parity for the shared perspective)
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_AT_ENVELOPE_CHANNEL_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "channel",
    "target",
    "target_label",
    "target_rank",
    "row",
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


# ── next_tier_channel_spec_at ───────────────────────────────────────────────


def test_next_tier_channel_spec_at_byte_equals_channel_spec_at(ent):
    # Helper is convenience for
    # channel_spec_at(_next_purchasable_tier_after(tier), channel). The two
    # must be byte-equal across every purchasable source for every channel
    # -- pinning so the projection cannot drift from the full-row sibling.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            assert ent.next_tier_channel_spec_at(src, channel) == ent.channel_spec_at(
                target, channel
            )


def test_next_tier_channel_spec_at_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every channel.
    assert ent._next_purchasable_tier_after(ent.TIER_ENTERPRISE) is None
    for channel in sorted(ent.ALL_CHANNELS):
        assert ent.next_tier_channel_spec_at(ent.TIER_ENTERPRISE, channel) is None


def test_next_tier_channel_spec_at_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro -- next strictly-higher
    # purchasable rung is enterprise (rank 3). Pins that the source-anchored
    # helper matches the sibling _at semantics on trial.
    body = ent.next_tier_channel_spec_at(ent.TIER_TRIAL, "telegram")
    assert body is not None
    assert body == ent.channel_spec_at(ent.TIER_ENTERPRISE, "telegram")


def test_next_tier_channel_spec_at_unknown_inputs_return_none(ent):
    # Defensive null-paths -- empty / unknown / None / whitespace all
    # collapse to None rather than raising.
    assert ent.next_tier_channel_spec_at("", "telegram") is None
    assert ent.next_tier_channel_spec_at(None, "telegram") is None  # type: ignore[arg-type]
    assert ent.next_tier_channel_spec_at("bogus", "telegram") is None
    assert ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, "") is None
    assert ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, None) is None  # type: ignore[arg-type]
    assert ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, "no_such") is None


def test_next_tier_channel_spec_at_whitespace_and_case_insensitive(ent):
    # Whitespace + case normalisation matches the sibling _at helpers.
    canon = ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")
    assert canon is not None
    assert ent.next_tier_channel_spec_at(" CLOUD_STARTER ", "telegram") == canon
    assert ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, " TELEGRAM ") == canon


def test_next_tier_channel_spec_at_always_free_invariant(ent):
    # Channel-axis invariant: every chat channel is FREE at every tier,
    # so the row always comes back free=True / locked=False / entitled=True
    # regardless of the target rung. That parity IS the answer.
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            row = ent.next_tier_channel_spec_at(src, channel)
            assert row is not None
            assert row["id"] == channel
            assert row["free"] is True
            assert row["locked"] is False
            assert row["entitled"] is True
            assert row["allowed"] is True


def test_next_tier_channel_spec_at_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived (off static per-tier maps), not gated -- so flipping
    # enforce on must not change the body.
    grace_body = ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_body = ent.next_tier_channel_spec_at(
        ent.TIER_CLOUD_STARTER, "telegram"
    )
    assert enforce_body == grace_body


def test_next_tier_channel_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    # A synthesised builder failure must short-circuit to None so the CTA
    # surface stays mute rather than 500-ing.
    monkeypatch.setattr(
        ent,
        "channel_spec_at",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.next_tier_channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram") is None


# ── previous_tier_channel_spec_at ────────────────────────────────────────────


def test_previous_tier_channel_spec_at_byte_equals_channel_spec_at(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            assert ent.previous_tier_channel_spec_at(
                src, channel
            ) == ent.channel_spec_at(target, channel)


def test_previous_tier_channel_spec_at_returns_none_at_floor(ent):
    # OSS + cloud_free both sit at rank 0 -- no purchasable rung below.
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent._previous_purchasable_tier_before(src) is None
        for channel in sorted(ent.ALL_CHANNELS):
            assert ent.previous_tier_channel_spec_at(src, channel) is None


def test_previous_tier_channel_spec_at_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter) -- highest rank strictly below
    # trial's rank 2.
    body = ent.previous_tier_channel_spec_at(ent.TIER_TRIAL, "telegram")
    assert body is not None
    assert body == ent.channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")


def test_previous_tier_channel_spec_at_unknown_inputs_return_none(ent):
    assert ent.previous_tier_channel_spec_at("", "telegram") is None
    assert ent.previous_tier_channel_spec_at(None, "telegram") is None  # type: ignore[arg-type]
    assert ent.previous_tier_channel_spec_at("bogus", "telegram") is None
    assert ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, "") is None
    assert ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, "no_such") is None


def test_previous_tier_channel_spec_at_whitespace_and_case_insensitive(ent):
    canon = ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, "telegram")
    assert canon is not None
    assert ent.previous_tier_channel_spec_at(" CLOUD_PRO ", "telegram") == canon
    assert ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, " TELEGRAM ") == canon


def test_previous_tier_channel_spec_at_always_free_invariant(ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for channel in sorted(ent.ALL_CHANNELS):
            row = ent.previous_tier_channel_spec_at(src, channel)
            assert row is not None
            assert row["id"] == channel
            assert row["free"] is True
            assert row["locked"] is False
            assert row["entitled"] is True


def test_previous_tier_channel_spec_at_grace_and_enforce_match(ent, monkeypatch):
    grace_body = ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, "telegram")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_body = ent.previous_tier_channel_spec_at(
        ent.TIER_CLOUD_PRO, "telegram"
    )
    assert enforce_body == grace_body


def test_previous_tier_channel_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    monkeypatch.setattr(
        ent,
        "channel_spec_at",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.previous_tier_channel_spec_at(ent.TIER_CLOUD_PRO, "telegram") is None
    )


# ── resolver-anchored parity with the method siblings ───────────────────────


def test_module_at_helper_matches_method_at_resolved_source(ent):
    # When the source ``tier`` equals the resolved entitlement's rank, the
    # source-anchored helper must byte-equal the resolver-anchored method
    # sibling -- both compose the same channel_spec_at call.
    resolved = ent.get_entitlement()
    src = resolved.tier
    if ent._next_purchasable_tier_after(src) is not None:
        for channel in sorted(ent.ALL_CHANNELS):
            assert ent.next_tier_channel_spec_at(
                src, channel
            ) == resolved.next_tier_channel_spec(channel)
    if ent._previous_purchasable_tier_before(src) is not None:
        for channel in sorted(ent.ALL_CHANNELS):
            assert ent.previous_tier_channel_spec_at(
                src, channel
            ) == resolved.previous_tier_channel_spec(channel)


# ── /api/entitlement/next-tier-channel-spec-at ──────────────────────────────


def test_api_next_tier_channel_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_CHANNEL_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["channel"] == "telegram"
    # Next purchasable rung after cloud_starter (rank 1) is cloud_pro (rank 2).
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    # Row byte-matches the helper AND the underlying channel_spec_at.
    assert body["row"] == ent.next_tier_channel_spec_at(
        ent.TIER_CLOUD_STARTER, "telegram"
    )
    assert body["row"] == ent.channel_spec_at(ent.TIER_CLOUD_PRO, "telegram")
    # Always-free invariant reaches the endpoint.
    assert body["row"]["free"] is True
    assert body["row"]["locked"] is False
    assert body["row"]["entitled"] is True


def test_api_next_tier_channel_spec_at_at_ceiling_returns_200_with_null_row(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=enterprise&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_api_next_tier_channel_spec_at_400_missing_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?channel=telegram"
    )
    assert resp.status_code == 400
    assert resp.get_json().get("error") == "missing tier"


def test_api_next_tier_channel_spec_at_400_missing_channel(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter"
    )
    assert resp.status_code == 400
    assert resp.get_json().get("error") == "missing channel"


def test_api_next_tier_channel_spec_at_400_blank_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=%20%20&channel=telegram"
    )
    assert resp.status_code == 400


def test_api_next_tier_channel_spec_at_400_blank_channel(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter&channel=%20%20"
    )
    assert resp.status_code == 400


def test_api_next_tier_channel_spec_at_404_unknown_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=bogus&channel=telegram"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("error") == "unknown tier"
    assert body.get("which") == "tier"
    assert body.get("tier") == "bogus"


def test_api_next_tier_channel_spec_at_404_unknown_channel(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter&channel=no_such"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("error") == "unknown channel"
    assert body.get("which") == "channel"
    assert body.get("channel") == "no_such"


def test_api_next_tier_channel_spec_at_trial_endpoint(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=trial&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["row"] == ent.channel_spec_at(ent.TIER_ENTERPRISE, "telegram")


def test_api_next_tier_channel_spec_at_case_and_whitespace_normalise(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=%20CLOUD_STARTER%20&channel=%20TELEGRAM%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["channel"] == "telegram"
    assert body["row"] == ent.next_tier_channel_spec_at(
        ent.TIER_CLOUD_STARTER, "telegram"
    )


def test_api_next_tier_channel_spec_at_row_matches_channel_spec_at_endpoint(
    client, ent
):
    # Cross-endpoint no-drift: the inner ``row`` must byte-match
    # /channel-spec-at at the resolved target so callers can swap one
    # endpoint for the other without copy drift.
    at_resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter&channel=telegram"
    )
    target = at_resp.get_json()["target"]
    assert target is not None
    plain_resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={target}&channel=telegram"
    )
    assert plain_resp.status_code == 200
    # ``/channel-spec-at`` wraps its row under the ``spec`` key while this
    # projection surface calls it ``row`` (matching ``/next-tier-*-spec-at``);
    # the row content itself must match byte-for-byte.
    assert at_resp.get_json()["row"] == plain_resp.get_json()["spec"]


def test_api_next_tier_channel_spec_at_never_raises(client, ent, monkeypatch):
    # A synthesised resolver failure inside the handler must land on the
    # grace-shape envelope so the surface stays 200 with row=null.
    from clawmetry import entitlements as _ent

    monkeypatch.setattr(
        _ent,
        "next_tier_channel_spec_at",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at?tier=cloud_starter&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_CHANNEL_KEYS
    assert body["row"] is None
    assert body["target"] is None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


# ── /api/entitlement/previous-tier-channel-spec-at ──────────────────────────


def test_api_previous_tier_channel_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-spec-at?tier=cloud_pro&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_CHANNEL_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["channel"] == "telegram"
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["row"] == ent.channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")
    assert body["row"]["free"] is True
    assert body["row"]["locked"] is False
    assert body["row"]["entitled"] is True


def test_api_previous_tier_channel_spec_at_at_floor_returns_200_with_null_row(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-channel-spec-at?tier={src}&channel=telegram"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert body["target_label"] is None
        assert body["target_rank"] is None
        assert body["row"] is None


def test_api_previous_tier_channel_spec_at_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at?channel=telegram"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at?tier=bogus&channel=telegram"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at?tier=cloud_pro&channel=no_such"
        ).status_code
        == 404
    )


def test_api_previous_tier_channel_spec_at_trial_endpoint(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-spec-at?tier=trial&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.channel_spec_at(ent.TIER_CLOUD_STARTER, "telegram")


def test_api_previous_tier_channel_spec_at_case_and_whitespace_normalise(
    client, ent
):
    resp = client.get(
        "/api/entitlement/previous-tier-channel-spec-at?tier=%20CLOUD_PRO%20&channel=%20TELEGRAM%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["channel"] == "telegram"
    assert body["row"] == ent.previous_tier_channel_spec_at(
        ent.TIER_CLOUD_PRO, "telegram"
    )


def test_api_previous_tier_channel_spec_at_never_raises(client, ent, monkeypatch):
    from clawmetry import entitlements as _ent

    monkeypatch.setattr(
        _ent,
        "previous_tier_channel_spec_at",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    resp = client.get(
        "/api/entitlement/previous-tier-channel-spec-at?tier=cloud_pro&channel=telegram"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_CHANNEL_KEYS
    assert body["row"] is None
    assert body["target"] is None
    assert body["tier"] == ent.TIER_CLOUD_PRO


# ── shared: every purchasable source rung yields an always-free row ────────


def test_api_next_and_prev_yield_always_free_row_across_every_source(client, ent):
    # Table-drive both endpoints across every source rung + every channel.
    # Whenever ``target`` is populated the row must come back always-free.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
        ent.TIER_ENTERPRISE,
    ):
        for direction in ("next", "previous"):
            for channel in sorted(ent.ALL_CHANNELS):
                resp = client.get(
                    f"/api/entitlement/{direction}-tier-channel-spec-at"
                    f"?tier={src}&channel={channel}"
                )
                assert resp.status_code == 200
                body = resp.get_json()
                assert body["tier"] == src
                assert body["channel"] == channel
                if body["target"] is None:
                    assert body["row"] is None
                else:
                    row = body["row"]
                    assert row is not None
                    assert row["id"] == channel
                    assert row["free"] is True
                    assert row["locked"] is False
                    assert row["entitled"] is True
