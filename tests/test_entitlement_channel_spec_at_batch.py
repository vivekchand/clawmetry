"""Tests for ``channel_spec_at_batch(tier, channels)`` + ``GET
/api/entitlement/channel-spec-at-batch``.

What-if + batch sibling of :func:`channel_spec_batch`: return spec rows
for a caller-supplied subset of chat-channel ids, with ``allowed`` /
``locked`` / ``entitled`` computed as if the install were on ``tier``.
Channel-axis twin of :func:`feature_spec_at_batch` /
:func:`runtime_spec_at_batch`.

Pins:

* row shape matches a row from ``channel_catalog_at(tier)`` EXACTLY (so
  the scalar what-if / bulk what-if / batch what-if accessors cannot
  drift on the channel axis) -- parity test enumerates every
  ``(tier, channel)`` pair
* the row for a given channel is byte-identical to the LIVE
  ``channel_spec(channel)`` and to ``channel_spec_batch([channel])``
  regardless of the perspective tier -- the always-free invariant on the
  channel axis (the ``channels`` capacity axis governs how many
  concurrent channels each plan admits, not which adapters unlock)
* the row is also byte-identical to ``channel_spec_at(tier, channel)``
  for the same ``(tier, channel)`` pair -- pins the scalar / batch
  what-if no-drift contract
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved)
* unknown channel ids are echoed in ``unknown[]`` instead of 404'ing
* unknown / empty / ``None`` / non-string tier ids return ``None``
* every row is ``free=True`` / ``allowed=True`` / ``locked=False`` /
  ``entitled=True`` regardless of the perspective tier
* the helper is independent of the live resolver: switching enforcement
  or pointing HOME at a license cache does not change the rows the
  what-if surface returns
* never raises -- a synthesis failure short-circuits to the OSS-free
  fallback and a per-channel row build failure drops the id into
  ``unknown[]`` so the rest of the batch keeps rendering
* the endpoint 400s on missing / blank ``tier`` or ``channels``, 404s
  on unknown tier (with ``which: "tier"``), carries the standard
  ``perspective_tier`` / ``current_tier`` / ``grace`` / ``enforced``
  envelope, and never 5xxs on a resolver crash
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_CHANNEL_SPEC_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "allowed",
    "locked",
    "entitled",
}

_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``channel_spec_at_batch``
    is independent of either knob, so the fixture only needs to make
    sure the live resolver does not surprise the test."""
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


# ── helper: empty / bogus tier ────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at_batch("not_a_real_tier", [ch]) is None


def test_empty_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at_batch("", [ch]) is None


def test_none_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at_batch(None, [ch]) is None


def test_non_string_tier_returns_none(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec_at_batch(123, [ch]) is None
    assert ent.channel_spec_at_batch(object(), [ch]) is None


# ── helper: empty channel list ────────────────────────────────────────────────


def test_empty_channels_returns_empty_envelope(ent):
    assert ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, []) == {
        "channels": [],
        "unknown": [],
    }


def test_none_channels_returns_empty_envelope(ent):
    assert ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, None) == {
        "channels": [],
        "unknown": [],
    }


# ── helper: shape + parity ────────────────────────────────────────────────────


def test_row_shape_matches_catalog_at_row(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, [ch])
    assert len(body["channels"]) == 1
    assert set(body["channels"][0].keys()) == _CHANNEL_SPEC_KEYS


def test_parity_with_catalog_at_every_pair(ent):
    """For every (tier, channel) pair, the batch what-if accessor
    returns the same dict as the bulk what-if accessor. Pins the
    scalar/bulk/batch no-drift contract on the channel axis."""
    for tier in ent._TIER_ORDER:
        bulk_by_id = {row["id"]: row for row in ent.channel_catalog_at(tier)}
        ids = sorted(bulk_by_id)
        body = ent.channel_spec_at_batch(tier, ids)
        rows_by_id = {row["id"]: row for row in body["channels"]}
        assert set(rows_by_id) == set(ids), tier
        for cid in ids:
            assert rows_by_id[cid] == bulk_by_id[cid], (tier, cid)


def test_parity_with_scalar_channel_spec_at_every_pair(ent):
    """Pins ``channel_spec_at_batch(tier, [ch])[0]`` == ``channel_spec_at(tier, ch)``
    for every ``(tier, ch)`` -- scalar / batch no-drift contract."""
    for tier in ent._TIER_ORDER:
        for ch in ent.ALL_CHANNELS:
            body = ent.channel_spec_at_batch(tier, [ch])
            assert body["channels"] == [ent.channel_spec_at(tier, ch)], (tier, ch)


def test_parity_with_live_channel_spec(ent):
    """Because every chat channel is FREE at every tier, the batch
    what-if row must byte-equal the LIVE :func:`channel_spec` row for
    the same id at every perspective tier -- the always-free posture is
    the whole point of the channel axis, and this test pins it end to
    end across the ``at_batch`` surface."""
    ids = sorted(ent.ALL_CHANNELS)
    live = {cid: ent.channel_spec(cid) for cid in ids}
    for tier in ent._TIER_ORDER:
        body = ent.channel_spec_at_batch(tier, ids)
        rows_by_id = {row["id"]: row for row in body["channels"]}
        for cid in ids:
            assert rows_by_id[cid] == live[cid], (tier, cid)


def test_parity_with_channel_spec_batch(ent):
    """Because every chat channel is FREE at every tier, the batch
    what-if body must byte-equal the LIVE :func:`channel_spec_batch`
    body for the same ids at every perspective tier."""
    ids = sorted(ent.ALL_CHANNELS)
    live = ent.channel_spec_batch(ids)
    for tier in ent._TIER_ORDER:
        body = ent.channel_spec_at_batch(tier, ids)
        assert body["channels"] == live["channels"], tier
        assert body["unknown"] == live["unknown"], tier


# ── input normalisation ───────────────────────────────────────────────────────


def test_tier_is_lowercased_and_trimmed(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    a = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, [ch])
    b = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO.upper(), [ch])
    c = ent.channel_spec_at_batch(f"  {ent.TIER_CLOUD_PRO}  ", [ch])
    assert a == b == c


def test_channels_are_lowercased_and_trimmed(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    a = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, [ch])
    b = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, [ch.upper()])
    c = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, [f"  {ch}  "])
    assert a == b == c


def test_supply_order_preserved(ent):
    ids = list(sorted(ent.ALL_CHANNELS))
    reversed_ids = list(reversed(ids))
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, reversed_ids)
    assert [row["id"] for row in body["channels"]] == reversed_ids


def test_duplicates_dropped_first_seen_wins(ent):
    ids = list(sorted(ent.ALL_CHANNELS))
    if len(ids) < 2:
        pytest.skip("need >=2 channels")
    supply = [ids[0], ids[1], ids[0], ids[1]]
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, supply)
    assert [row["id"] for row in body["channels"]] == [ids[0], ids[1]]


# ── unknown ids echoed ───────────────────────────────────────────────────────


def test_unknown_channels_echoed(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_at_batch(
        ent.TIER_CLOUD_PRO, [ch, "not_a_channel", "also_not"]
    )
    assert [row["id"] for row in body["channels"]] == [ch]
    assert body["unknown"] == ["not_a_channel", "also_not"]


def test_only_unknown_channels_returns_empty_rows(ent):
    body = ent.channel_spec_at_batch(
        ent.TIER_CLOUD_PRO, ["bogus_a", "bogus_b"]
    )
    assert body["channels"] == []
    assert body["unknown"] == ["bogus_a", "bogus_b"]


# ── always-free invariant ────────────────────────────────────────────────────


def test_every_row_is_always_free(ent):
    """Every chat channel is FREE at every tier, so every row must come
    back ``free`` / ``allowed`` / ``entitled`` and never ``locked`` --
    regardless of the perspective tier or the resolver's current
    posture."""
    ids = sorted(ent.ALL_CHANNELS)
    for tier in ent._TIER_ORDER:
        body = ent.channel_spec_at_batch(tier, ids)
        for row in body["channels"]:
            assert row["free"] is True, (tier, row["id"])
            assert row["tier"] == "free", (tier, row["id"])
            assert row["allowed"] is True, (tier, row["id"])
            assert row["locked"] is False, (tier, row["id"])
            assert row["entitled"] is True, (tier, row["id"])


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_at_batch(ent.TIER_OSS, [ch])
    assert body["channels"][0]["allowed"] is True
    assert body["channels"][0]["locked"] is False
    assert body["channels"][0]["entitled"] is True


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_at_batch(ent.TIER_OSS, [ch])
    assert body["channels"][0]["allowed"] is True
    assert body["channels"][0]["locked"] is False
    assert body["channels"][0]["entitled"] is True


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its own hypothetical Entitlement and does not
    consult :func:`get_entitlement`, so a blown resolver must not
    affect the result. Pins the never-raise contract anyway."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ids = sorted(ent.ALL_CHANNELS)
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, ids)
    assert body is not None
    assert len(body["channels"]) == len(ids)
    for row in body["channels"]:
        assert row["free"] is True
        assert row["locked"] is False


def test_row_build_failure_drops_id_into_unknown(ent, monkeypatch):
    """A per-channel row build failure drops the id into ``unknown[]``
    so the rest of the batch keeps rendering. Pins the batch's never-
    raise + partial-response contract on the channel axis."""
    ids = sorted(ent.ALL_CHANNELS)
    victim = ids[0]
    real = ent._channel_spec_row

    def selective(entobj, ch):
        if ch == victim:
            raise RuntimeError("simulated per-channel row build failure")
        return real(entobj, ch)

    monkeypatch.setattr(ent, "_channel_spec_row", selective)
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, ids)
    row_ids = {row["id"] for row in body["channels"]}
    assert victim not in row_ids
    assert victim in body["unknown"]
    assert len(row_ids) == len(ids) - 1


def test_synthesis_failure_still_returns_rows(ent, monkeypatch):
    """A ``_hypothetical_entitlement`` crash short-circuits to the
    OSS-free fallback so the matrix keeps rendering."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated synthesis failure")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", boom)
    ids = sorted(ent.ALL_CHANNELS)
    body = ent.channel_spec_at_batch(ent.TIER_CLOUD_PRO, ids)
    assert body is not None
    assert len(body["channels"]) == len(ids)
    # Every chat channel is FREE at every tier, so the fallback rows are
    # byte-identical to the intended rows.
    for row in body["channels"]:
        assert row["free"] is True
        assert row["locked"] is False


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_rows(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&channels={ch}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["perspective_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["channels"] == [ent.channel_spec_at(ent.TIER_CLOUD_PRO, ch)]
    assert body["unknown"] == []
    for key in _ENVELOPE_KEYS:
        assert key in body, key


def test_endpoint_lowercases_and_trims(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch"
        f"?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&channels=%20%20{ch.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert [row["id"] for row in body["channels"]] == [ch]


def test_endpoint_missing_tier_returns_400(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?channels={ch}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier=%20%20&channels={ch}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_channels_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_channels_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&channels=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier=nonsense_xyz"
        f"&channels={ch}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert body["which"] == "tier"
    assert "error" in body


def test_endpoint_unknown_channels_echoed(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&channels={ch},not_a_channel"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["id"] for row in body["channels"]] == [ch]
    assert body["unknown"] == ["not_a_channel"]


def test_endpoint_every_pair_round_trips(client, ent):
    ids = ",".join(sorted(ent.ALL_CHANNELS))
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/channel-spec-at-batch?tier={tier}"
            f"&channels={ids}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["perspective_tier"] == tier, tier
        assert len(body["channels"]) == len(ent.ALL_CHANNELS), tier
        assert body["unknown"] == [], tier


def test_endpoint_byte_equal_channel_catalog_at(client, ent):
    """The endpoint's ``channels[]`` must byte-equal the corresponding
    rows in ``/api/entitlement/channel-catalog-at`` at the same
    perspective tier -- pins the scalar / bulk / batch no-drift contract
    on the wire."""
    tier = ent.TIER_CLOUD_PRO
    cat_resp = client.get(
        f"/api/entitlement/channel-catalog-at?tier={tier}"
    )
    assert cat_resp.status_code == 200
    cat_by_id = {row["id"]: row for row in cat_resp.get_json()["channels"]}
    ids = ",".join(sorted(cat_by_id))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={tier}&channels={ids}"
    )
    assert resp.status_code == 200
    rows_by_id = {row["id"]: row for row in resp.get_json()["channels"]}
    assert set(rows_by_id) == set(cat_by_id)
    for cid, row in rows_by_id.items():
        assert row == cat_by_id[cid], cid


def test_endpoint_byte_equal_channel_spec_batch(client, ent):
    """Because every chat channel is FREE at every tier, the endpoint's
    ``channels[]`` must byte-equal the LIVE ``/channel-spec-batch``
    body's ``channels[]`` at every perspective tier."""
    ids = ",".join(sorted(ent.ALL_CHANNELS))
    live = client.get(
        f"/api/entitlement/channel-spec-batch?channels={ids}"
    ).get_json()
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/channel-spec-at-batch?tier={tier}"
            f"&channels={ids}"
        )
        assert resp.status_code == 200, tier
        assert resp.get_json()["channels"] == live["channels"], tier


def test_endpoint_never_5xxs_when_resolver_crashes(client, ent, monkeypatch):
    """A ``get_entitlement`` crash inside the handler (used for the
    envelope's ``current_tier`` / ``grace`` / ``enforced`` fields)
    short-circuits to the OSS-free fallback shape -- empty rows,
    ``current_tier=oss``, ``grace=true``, ``enforced=false`` -- with the
    perspective tier echoed so the UI keeps rendering. Mirrors
    ``/feature-spec-at-batch`` / ``/runtime-spec-at-batch``."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&channels={ch}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["channels"] == []
    assert body["unknown"] == []
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_carries_envelope_flags(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&channels={ch}"
    )
    body = resp.get_json()
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)
