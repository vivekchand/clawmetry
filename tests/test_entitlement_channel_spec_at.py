"""Tests for ``channel_spec_at(tier, channel)`` + ``GET
/api/entitlement/channel-spec-at``.

Scalar what-if sibling of :func:`channel_catalog_at`: one catalogue row
for ``channel`` with ``allowed`` / ``locked`` / ``entitled`` computed as
if the install were on ``tier``. Lets a pricing-comparison tooltip
hydrate against ONE channel at a hypothetical tier in one round-trip
without fetching the full ``channel_catalog_at`` payload.

Pins:

* the row shape matches a row from ``channel_catalog_at(tier)``
  EXACTLY (so the scalar and bulk what-if accessors cannot drift) -- a
  parity test enumerates every (tier, channel) pair
* the row for a given channel is byte-identical to the LIVE
  ``channel_spec(channel)`` row regardless of the perspective tier --
  the always-free invariant on the channel axis (the ``channels``
  capacity axis governs how many concurrent channels each plan admits,
  not which adapters unlock)
* every (tier, channel) pair in ``_TIER_ORDER`` x ``ALL_CHANNELS``
  round-trips
* unknown / empty / ``None`` / non-string tier ids return ``None``
* unknown / empty / ``None`` / non-string channel ids return ``None``
* both args are trimmed + lowercased before resolution
* every row is ``free=True`` / ``allowed=True`` / ``locked=False`` /
  ``entitled=True`` regardless of the perspective tier
* the helper is independent of the live resolver: switching
  enforcement or pointing HOME at a license cache does not change the
  rows the what-if surface returns
* the endpoint 400s on missing input, 404s on unknown ids (with
  ``which`` so the caller can render the right "unknown ..." message),
  and never 5xxs
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_ROW_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "allowed",
    "locked",
    "entitled",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``channel_spec_at`` is
    independent of either knob, so the fixture only needs to make sure
    the live resolver does not surprise the test."""
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_catalog_at_row(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    spec = ent.channel_spec_at(ent.TIER_CLOUD_PRO, ch)
    assert spec is not None
    assert set(spec.keys()) == _ROW_KEYS


def test_parity_with_every_catalog_at_row(ent):
    """For every (tier, channel) pair, the scalar what-if accessor
    returns the same dict as the bulk what-if accessor. Pins the
    scalar/bulk no-drift contract -- this is THE invariant the helper
    exists to make hydratable in one round-trip."""
    for tier in ent._TIER_ORDER:
        bulk_by_id = {row["id"]: row for row in ent.channel_catalog_at(tier)}
        for cid, row in bulk_by_id.items():
            assert ent.channel_spec_at(tier, cid) == row, (tier, cid)


def test_parity_with_live_channel_spec(ent):
    """Because every chat channel is FREE at every tier, the scalar
    what-if row must byte-equal the LIVE :func:`channel_spec` row for
    the same id at every perspective tier -- the always-free posture is
    the whole point of the channel axis, and this test pins it end to
    end across the ``at`` surface."""
    for ch in sorted(ent.ALL_CHANNELS):
        live = ent.channel_spec(ch)
        assert live is not None, ch
        for tier in ent._TIER_ORDER:
            assert ent.channel_spec_at(tier, ch) == live, (tier, ch)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_pair_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        for ch in ent.ALL_CHANNELS:
            spec = ent.channel_spec_at(tier, ch)
            assert spec is not None, (tier, ch)
            assert spec["id"] == ch


# ── invalid tier ──────────────────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at("not_a_real_tier", ch) is None


def test_empty_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at("", ch) is None


def test_none_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at(None, ch) is None


def test_non_string_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at(123, ch) is None
    assert ent.channel_spec_at(object(), ch) is None


# ── invalid channel ───────────────────────────────────────────────────────────


def test_unknown_channel_returns_none(ent):
    assert ent.channel_spec_at(ent.TIER_CLOUD_PRO, "not_a_real_channel") is None


def test_empty_channel_returns_none(ent):
    assert ent.channel_spec_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_channel_returns_none(ent):
    assert ent.channel_spec_at(ent.TIER_CLOUD_PRO, None) is None


def test_non_string_channel_returns_none(ent):
    assert ent.channel_spec_at(ent.TIER_CLOUD_PRO, 123) is None
    assert ent.channel_spec_at(ent.TIER_CLOUD_PRO, object()) is None


# ── normalisation ─────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    a = ent.channel_spec_at(ent.TIER_CLOUD_PRO, ch)
    b = ent.channel_spec_at(ent.TIER_CLOUD_PRO.upper(), ch.upper())
    c = ent.channel_spec_at(f"  {ent.TIER_CLOUD_PRO}  ", f"  {ch}  ")
    assert a == b == c


# ── always-free invariant ────────────────────────────────────────────────────


def test_every_row_is_always_free(ent):
    """Every chat channel is FREE at every tier (the ``channels``
    capacity axis governs how many concurrent channels each plan
    admits, not which adapters unlock), so every row must come back
    ``free`` / ``allowed`` / ``entitled`` and never ``locked`` --
    regardless of the perspective tier or the resolver's current
    posture."""
    for tier in ent._TIER_ORDER:
        for ch in ent.ALL_CHANNELS:
            row = ent.channel_spec_at(tier, ch)
            assert row["free"] is True, (tier, ch)
            assert row["tier"] == "free", (tier, ch)
            assert row["allowed"] is True, (tier, ch)
            assert row["locked"] is False, (tier, ch)
            assert row["entitled"] is True, (tier, ch)


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    ch = next(iter(ent.ALL_CHANNELS))
    row = ent.channel_spec_at(ent.TIER_OSS, ch)
    assert row["allowed"] is True
    assert row["locked"] is False
    assert row["entitled"] is True


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    ch = next(iter(ent.ALL_CHANNELS))
    row = ent.channel_spec_at(ent.TIER_OSS, ch)
    assert row["allowed"] is True
    assert row["locked"] is False
    assert row["entitled"] is True


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its own hypothetical Entitlement and does not
    consult :func:`get_entitlement`, so a blown resolver must not
    affect the result. Pins the never-raise contract anyway."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    row = ent.channel_spec_at(ent.TIER_CLOUD_PRO, ch)
    assert row is not None
    assert row["id"] == ch
    assert row["free"] is True
    assert row["locked"] is False


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={ent.TIER_CLOUD_PRO}&channel={ch}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["channel"] == ch
    assert body["spec"] == ent.channel_spec_at(ent.TIER_CLOUD_PRO, ch)


def test_endpoint_lowercases_and_trims(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&channel=%20%20{ch.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["channel"] == ch


def test_endpoint_missing_tier_returns_400(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec-at?channel={ch}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier=%20%20&channel={ch}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_channel_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_channel_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={ent.TIER_CLOUD_PRO}&channel=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier=nonsense_xyz&channel={ch}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert body["which"] == "tier"
    assert "error" in body


def test_endpoint_unknown_channel_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={ent.TIER_CLOUD_PRO}"
        "&channel=not_a_real_channel"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["channel"] == "not_a_real_channel"
    assert body["which"] == "channel"
    assert "error" in body


def test_endpoint_every_pair_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for ch in ent.ALL_CHANNELS:
            resp = client.get(
                f"/api/entitlement/channel-spec-at?tier={tier}&channel={ch}"
            )
            assert resp.status_code == 200, (tier, ch)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, ch)
            assert body["channel"] == ch, (tier, ch)


def test_endpoint_body_spec_byte_equal_catalog_at_row(client, ent):
    """The endpoint body's ``spec`` field must byte-equal the
    corresponding row in ``/api/entitlement/channel-catalog-at`` at the
    same perspective tier -- pins the scalar / bulk no-drift contract
    on the wire."""
    tier = ent.TIER_CLOUD_PRO
    cat_resp = client.get(
        f"/api/entitlement/channel-catalog-at?tier={tier}"
    )
    assert cat_resp.status_code == 200
    cat_by_id = {row["id"]: row for row in cat_resp.get_json()["channels"]}
    for ch, row in cat_by_id.items():
        resp = client.get(
            f"/api/entitlement/channel-spec-at?tier={tier}&channel={ch}"
        )
        assert resp.status_code == 200, ch
        assert resp.get_json()["spec"] == row, ch


def test_endpoint_never_5xxs_when_resolver_crashes(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at?tier={ent.TIER_CLOUD_PRO}&channel={ch}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["spec"]["id"] == ch
    assert body["spec"]["free"] is True
    assert body["spec"]["locked"] is False
