"""Tests for the two batch siblings of
:func:`clawmetry.entitlements.next_tier_channel_spec_at` /
:func:`previous_tier_channel_spec_at`, and the two companion
``/api/entitlement/{next,previous}-tier-channel-spec-at-batch``
endpoints.

Channel-axis twin of the four
:func:`{next,previous}_tier_{feature,runtime}_spec_at_batch` helpers.
Where the scalar projections walk ONE chat channel onto the rung
above/below a source tier, the batch siblings walk N channels onto
that same rung in ONE round-trip. They compose:

* :func:`next_tier_channel_spec_at` (scalar projection) +
  :func:`channel_spec_at_batch` (batch what-if) ->
  :func:`next_tier_channel_spec_at_batch`
* :func:`previous_tier_channel_spec_at` +
  :func:`channel_spec_at_batch` ->
  :func:`previous_tier_channel_spec_at_batch`

Pins covered here:

* per-row byte-equality with the scalar sibling for every valid
  (source, channel) pair across every purchasable source tier
  (parity)
* channel-axis always-free invariant: whenever ``row`` is not
  ``None`` it comes back ``free=True`` / ``locked=False`` /
  ``entitled=True``
* ceiling (enterprise as source for ``next_*``) / floor
  (``oss`` / ``cloud_free`` as source for ``previous_*``) yields
  ``row=None`` for every valid channel -- envelope rows still render
* trial-as-source resolves the same way the sibling ``_at`` families do
  (next -> enterprise, previous -> cloud_starter)
* unknown / empty / whitespace / case-insensitive id handling
* unknown ids echo into ``unknown[]`` rather than 404'ing the call
* normalisation is whitespace-stripped, lowercased, first-seen order
  preserved, duplicate-dropped (matches ``_normalise_csv``)
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a per-row builder failure short-circuits
  that row into ``unknown[]`` rather than 500-ing
* the two API endpoints never 5xx: 400 on missing input, 404 on
  unknown tier, 200 with ``row=null`` rows at ceiling/floor; an
  internal failure yields the same 200 envelope shape
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
    "unknown",
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


def _sample_channels(ent, n: int = 3) -> list[str]:
    """Return up to ``n`` chat-channel ids in a deterministic order."""
    return sorted(ent.ALL_CHANNELS)[:n]


# ── next_tier_channel_spec_at_batch (helper) ────────────────────────────────


def test_next_channel_batch_row_byte_equals_scalar(ent):
    # Per-row body equals next_tier_channel_spec_at(src, channel)
    # byte-for-byte across every purchasable source for every channel.
    # Pins so the batch accessor cannot drift from the scalar projection.
    chans = sorted(ent.ALL_CHANNELS)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.next_tier_channel_spec_at_batch(src, chans)
        assert body is not None
        assert body["unknown"] == []
        assert [r["channel"] for r in body["channels"]] == chans
        for row in body["channels"]:
            assert row["row"] == ent.next_tier_channel_spec_at(src, row["channel"])


def test_next_channel_batch_returns_row_null_at_ceiling(ent):
    # Enterprise is the top of the purchasable ladder -- no rung above.
    # Every valid channel must surface as a row with row=None so the
    # matrix's row count stays stable (the surface can still render
    # "you're at the top").
    chans = sorted(ent.ALL_CHANNELS)
    body = ent.next_tier_channel_spec_at_batch(ent.TIER_ENTERPRISE, chans)
    assert body is not None
    assert body["unknown"] == []
    assert [r["channel"] for r in body["channels"]] == chans
    assert all(r["row"] is None for r in body["channels"])


def test_next_channel_batch_trial_resolves_to_enterprise(ent):
    ch = _sample_channels(ent, 1)[0]
    body = ent.next_tier_channel_spec_at_batch(ent.TIER_TRIAL, [ch])
    assert body is not None
    assert body["channels"] == [
        {
            "channel": ch,
            "row": ent.channel_spec_at(ent.TIER_ENTERPRISE, ch),
        }
    ]


def test_next_channel_batch_unknown_inputs_short_circuit(ent):
    # Empty / None / unknown tier -> helper returns None (HTTP wrapper
    # turns into 400 / 404). Unknown channel ids are bucketed into
    # ``unknown[]``.
    ch = _sample_channels(ent, 1)[0]
    assert ent.next_tier_channel_spec_at_batch("", [ch]) is None
    assert ent.next_tier_channel_spec_at_batch(None, [ch]) is None
    assert ent.next_tier_channel_spec_at_batch("bogus", [ch]) is None
    body = ent.next_tier_channel_spec_at_batch(
        ent.TIER_CLOUD_STARTER, [ch, "no_such_channel", "also_bogus"]
    )
    assert body is not None
    assert [r["channel"] for r in body["channels"]] == [ch]
    assert body["unknown"] == ["no_such_channel", "also_bogus"]


def test_next_channel_batch_normalises_input(ent):
    # Whitespace stripped, lowercased, duplicates dropped, first-seen
    # order preserved -- matches _normalise_csv.
    ch = _sample_channels(ent, 1)[0]
    body = ent.next_tier_channel_spec_at_batch(
        ent.TIER_CLOUD_STARTER,
        [f" {ch.upper()} ", ch, "", ch.upper()],
    )
    assert body is not None
    assert [r["channel"] for r in body["channels"]] == [ch]
    assert body["unknown"] == []


def test_next_channel_batch_empty_channels_returns_empty_rows(ent):
    # An empty caller-supplied list returns {channels: [], unknown: []}
    # -- the HTTP layer turns that into a 400, the helper itself does
    # not raise.
    body = ent.next_tier_channel_spec_at_batch(ent.TIER_CLOUD_STARTER, [])
    assert body == {"channels": [], "unknown": []}


def test_next_channel_batch_always_free_when_row_present(ent):
    # Channel-axis always-free invariant: whenever ``row`` is not None
    # it comes back ``free=True`` / ``locked=False`` / ``entitled=True``
    # regardless of the source or target rung.
    chans = sorted(ent.ALL_CHANNELS)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.next_tier_channel_spec_at_batch(src, chans)
        assert body is not None
        for entry in body["channels"]:
            row = entry["row"]
            if row is None:
                continue
            assert row.get("free") is True
            assert row.get("locked") is False
            assert row.get("entitled") is True


def test_next_channel_batch_grace_and_enforce_match(ent, monkeypatch):
    chans = sorted(ent.ALL_CHANNELS)
    grace = ent.next_tier_channel_spec_at_batch(ent.TIER_CLOUD_STARTER, chans)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_channel_spec_at_batch(ent.TIER_CLOUD_STARTER, chans)
    assert enforce == grace


def test_next_channel_batch_row_failure_buckets_into_unknown(ent, monkeypatch):
    # A synthesised failure in channel_spec_at short-circuits that row
    # into ``unknown[]`` and the rest of the batch keeps building.
    chans = _sample_channels(ent, 2)
    boom, keep = chans[0], chans[1]
    real_spec_at = ent.channel_spec_at

    def fake_spec_at(tier, channel):
        if channel == boom:
            raise RuntimeError("synthetic")
        return real_spec_at(tier, channel)

    monkeypatch.setattr(ent, "channel_spec_at", fake_spec_at)
    body = ent.next_tier_channel_spec_at_batch(
        ent.TIER_CLOUD_STARTER, [boom, keep]
    )
    assert body is not None
    assert [r["channel"] for r in body["channels"]] == [keep]
    assert body["unknown"] == [boom]


# ── previous_tier_channel_spec_at_batch (helper) ────────────────────────────


def test_previous_channel_batch_row_byte_equals_scalar(ent):
    chans = sorted(ent.ALL_CHANNELS)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.previous_tier_channel_spec_at_batch(src, chans)
        assert body is not None
        for row in body["channels"]:
            assert row["row"] == ent.previous_tier_channel_spec_at(
                src, row["channel"]
            )


def test_previous_channel_batch_returns_row_null_at_floor(ent):
    chans = sorted(ent.ALL_CHANNELS)
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        body = ent.previous_tier_channel_spec_at_batch(src, chans)
        assert body is not None
        assert [r["channel"] for r in body["channels"]] == chans
        assert all(r["row"] is None for r in body["channels"])


def test_previous_channel_batch_trial_resolves_to_starter(ent):
    ch = _sample_channels(ent, 1)[0]
    body = ent.previous_tier_channel_spec_at_batch(ent.TIER_TRIAL, [ch])
    assert body is not None
    assert body["channels"] == [
        {
            "channel": ch,
            "row": ent.channel_spec_at(ent.TIER_CLOUD_STARTER, ch),
        }
    ]


def test_previous_channel_batch_unknown_inputs_short_circuit(ent):
    ch = _sample_channels(ent, 1)[0]
    assert (
        ent.previous_tier_channel_spec_at_batch("", [ch]) is None
    )
    assert (
        ent.previous_tier_channel_spec_at_batch("bogus", [ch]) is None
    )
    body = ent.previous_tier_channel_spec_at_batch(
        ent.TIER_CLOUD_PRO, [ch, "no_such_channel"]
    )
    assert body is not None
    assert [r["channel"] for r in body["channels"]] == [ch]
    assert body["unknown"] == ["no_such_channel"]


def test_previous_channel_batch_always_free_when_row_present(ent):
    chans = sorted(ent.ALL_CHANNELS)
    for src in ent._PURCHASABLE_TIERS:
        body = ent.previous_tier_channel_spec_at_batch(src, chans)
        assert body is not None
        for entry in body["channels"]:
            row = entry["row"]
            if row is None:
                continue
            assert row.get("free") is True
            assert row.get("locked") is False
            assert row.get("entitled") is True


# ── /api/entitlement/next-tier-channel-spec-at-batch ────────────────────────


def test_api_next_channel_batch_happy_path(client, ent):
    chans = _sample_channels(ent, 2)
    csv = ",".join(chans)
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        f"?tier=cloud_starter&channels={csv}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    # Every per-channel row matches /next-tier-channel-spec-at .row
    for row in body["channels"]:
        scalar = client.get(
            "/api/entitlement/next-tier-channel-spec-at"
            f"?tier=cloud_starter&channel={row['channel']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_next_channel_batch_at_ceiling_returns_200_with_null_rows(
    client, ent
):
    chans = _sample_channels(ent, 2)
    csv = ",".join(chans)
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        f"?tier=enterprise&channels={csv}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert [r["channel"] for r in body["channels"]] == chans
    assert all(r["row"] is None for r in body["channels"])


def test_api_next_channel_batch_400_missing_tier(client, ent):
    ch = _sample_channels(ent, 1)[0]
    resp = client.get(
        f"/api/entitlement/next-tier-channel-spec-at-batch?channels={ch}"
    )
    assert resp.status_code == 400


def test_api_next_channel_batch_400_missing_channels(client):
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch?tier=cloud_starter"
    )
    assert resp.status_code == 400


def test_api_next_channel_batch_400_empty_channels(client):
    # ``channels=,,,`` normalises to an empty list -> 400.
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        "?tier=cloud_starter&channels=,,,"
    )
    assert resp.status_code == 400


def test_api_next_channel_batch_404_unknown_tier(client, ent):
    ch = _sample_channels(ent, 1)[0]
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        f"?tier=bogus&channels={ch}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"


def test_api_next_channel_batch_unknown_channel_bucketed_200(client, ent):
    # An unknown channel does not 404 the call -- it lands in unknown[].
    ch = _sample_channels(ent, 1)[0]
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        f"?tier=cloud_starter&channels={ch},no_such_channel"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["channel"] for r in body["channels"]] == [ch]
    assert body["unknown"] == ["no_such_channel"]


def test_api_next_channel_batch_normalises_query_arg(client, ent):
    # Whitespace + uppercase + duplicate dropping happens at the route
    # layer via _parse_csv_arg before the helper sees the list.
    chans = _sample_channels(ent, 2)
    a, b = chans[0], chans[1]
    resp = client.get(
        "/api/entitlement/next-tier-channel-spec-at-batch"
        f"?tier=cloud_starter&channels= {a.upper()} ,{a},{b.upper()}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["channel"] for r in body["channels"]] == [a, b]


# ── /api/entitlement/previous-tier-channel-spec-at-batch ────────────────────


def test_api_previous_channel_batch_happy_path(client, ent):
    chans = _sample_channels(ent, 2)
    csv = ",".join(chans)
    resp = client.get(
        "/api/entitlement/previous-tier-channel-spec-at-batch"
        f"?tier=cloud_pro&channels={csv}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER
    for row in body["channels"]:
        scalar = client.get(
            "/api/entitlement/previous-tier-channel-spec-at"
            f"?tier=cloud_pro&channel={row['channel']}"
        ).get_json()
        assert row["row"] == scalar["row"]


def test_api_previous_channel_batch_at_floor_returns_200_with_null_rows(
    client, ent
):
    chans = _sample_channels(ent, 2)
    csv = ",".join(chans)
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            "/api/entitlement/previous-tier-channel-spec-at-batch"
            f"?tier={src}&channels={csv}"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert all(r["row"] is None for r in body["channels"])


def test_api_previous_channel_batch_400s_and_404s(client, ent):
    ch = _sample_channels(ent, 1)[0]
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at-batch"
            f"?channels={ch}"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at-batch?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-channel-spec-at-batch"
            f"?tier=bogus&channels={ch}"
        ).status_code
        == 404
    )
