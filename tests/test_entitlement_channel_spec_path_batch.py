"""Tests for ``clawmetry.entitlements.channel_spec_path_batch(from, to,
channels)`` + the ``GET /api/entitlement/channel-spec-path-batch``
endpoint.

Channel-axis batch sibling of :func:`channel_spec_path` -- twin of
:func:`feature_spec_path_batch` and :func:`runtime_spec_path_batch` on
the channel axis. Where the scalar path helper walks ONE channel across
the rungs between two tiers, this helper walks N channels across the
same rungs in ONE round-trip.

Each per-item ``path`` must be byte-identical to the matching scalar
:func:`channel_spec_path` payload for the same ``(from, to, channel)``
triple -- pinned below so the scalar and batch path accessors cannot
drift.

Coverage:

* per-item ``path`` byte-equal to the scalar
  :func:`channel_spec_path` payload for every supplied channel
* rung walk identical across items in the same batch (rungs are
  channel-agnostic because every chat-channel adapter is FREE at every
  tier)
* batch envelope mirrors ``/channel-spec-path`` (from / from_label /
  from_rank / to / to_label / to_rank / direction) plus ``channels`` +
  ``unknown``
* input normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved)
* unknown ids echoed in ``unknown[]`` instead of 404'ing the call
* identity ``from == to`` yields an envelope with one entry per
  supplied id whose ``path`` is ``[]``
* lateral (same rank, different id) yields one-row paths per supplied
  id
* every row remains ``free=True`` / ``allowed=True`` / ``locked=False``
  / ``entitled=True`` (every channel is FREE at every tier)
* unknown / empty / garbage tier returns ``None`` (helper) / 400 / 404
  (HTTP)
* helper never raises -- a row failure short-circuits that channel
  into ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoint 400 on missing / empty input, 404 on unknown tier,
  never 5xx on a row failure
* grace vs enforce yields byte-identical rows
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ITEM_KEYS = {"channel", "path"}
_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}
_SPEC_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}
_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
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


# ── helper-level: shape ──────────────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram", "signal"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"channels", "unknown"}
    assert isinstance(out["channels"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_channel_and_path(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram", "signal"]
    )
    for item in out["channels"]:
        assert set(item.keys()) == _ITEM_KEYS
        assert isinstance(item["channel"], str)
        assert isinstance(item["path"], list)


def test_helper_each_path_row_has_rung_and_spec_keys(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram", "signal"]
    )
    for item in out["channels"]:
        for row in item["path"]:
            assert set(row).issuperset(_RUNG_KEYS)
            assert set(row).issuperset(_SPEC_KEYS)


# ── parity + invariance pins ─────────────────────────────────────────────────


def test_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-item ``path`` is byte-identical to the scalar
    :func:`channel_spec_path` payload for the same triple."""
    chans = ["telegram", "signal", "discord", "slack"]
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    by_id = {item["channel"]: item["path"] for item in out["channels"]}
    for cid in chans:
        scalar = ent.channel_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, cid
        )
        assert by_id[cid] == scalar


def test_helper_rung_walk_channel_agnostic(ent):
    """The walked rung sequence is channel-agnostic -- all per-item
    paths in the batch share the same rung sequence (every channel is
    FREE at every tier so the walk is invariant)."""
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal", "discord"],
    )
    rung_sequences = [
        [row["rung"] for row in item["path"]] for item in out["channels"]
    ]
    assert len(rung_sequences) == 3
    assert rung_sequences[0] == rung_sequences[1] == rung_sequences[2]


def test_helper_every_row_free_and_allowed(ent):
    """Every chat-channel adapter is FREE at every tier -- so every row
    at every rung reports ``free=True`` / ``allowed=True`` /
    ``locked=False`` / ``entitled=True``, regardless of direction."""
    for endpoints in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
    ):
        out = ent.channel_spec_path_batch(
            endpoints[0], endpoints[1], ["telegram", "slack", "discord"]
        )
        for item in out["channels"]:
            for row in item["path"]:
                assert row["free"] is True
                assert row["allowed"] is True
                assert row["locked"] is False
                assert row["entitled"] is True


# ── input normalisation ──────────────────────────────────────────────────────


def test_helper_supply_order_preserved(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["signal", "telegram", "discord"],
    )
    assert [item["channel"] for item in out["channels"]] == [
        "signal",
        "telegram",
        "discord",
    ]


def test_helper_normalises_input(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["  TELEGRAM  ", "signal", "telegram", ""],
    )
    assert [item["channel"] for item in out["channels"]] == [
        "telegram",
        "signal",
    ]


def test_helper_normalises_tier_input(ent):
    out = ent.channel_spec_path_batch(
        "  OSS  ", "  ENTERPRISE  ", ["telegram"]
    )
    assert out is not None
    assert [item["channel"] for item in out["channels"]] == ["telegram"]


# ── unknown-id handling ──────────────────────────────────────────────────────


def test_helper_unknown_ids_echoed(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "bogus_channel", "still_bogus"],
    )
    assert [item["channel"] for item in out["channels"]] == ["telegram"]
    assert set(out["unknown"]) == {"bogus_channel", "still_bogus"}


def test_helper_all_unknown_ids_yields_empty_channels(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["bogus_1", "bogus_2"]
    )
    assert out == {
        "channels": [],
        "unknown": ["bogus_1", "bogus_2"],
    }


# ── direction branches ──────────────────────────────────────────────────────


def test_helper_identity_yields_empty_paths(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        ["telegram", "signal"],
    )
    assert out["unknown"] == []
    for item in out["channels"]:
        assert item["path"] == []


def test_helper_lateral_yields_one_row_paths(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_PRO, ["telegram", "signal"]
    )
    for item in out["channels"]:
        assert len(item["path"]) == 1
        assert item["path"][0]["rung"] == ent.TIER_PRO


def test_helper_downgrade_walks_descending(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_ENTERPRISE, ent.TIER_OSS, ["telegram"]
    )
    assert out is not None
    for item in out["channels"]:
        ranks = [row["rung_rank"] for row in item["path"]]
        assert ranks == sorted(ranks, reverse=True)


def test_helper_upgrade_walks_ascending(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram"]
    )
    assert out is not None
    for item in out["channels"]:
        ranks = [row["rung_rank"] for row in item["path"]]
        assert ranks == sorted(ranks)


def test_helper_trial_accepted_as_endpoint(ent):
    """`trial` is not purchasable but IS a valid endpoint via the
    lateral / identity branches -- matches the scalar helper's posture."""
    out = ent.channel_spec_path_batch(
        ent.TIER_TRIAL, ent.TIER_TRIAL, ["telegram"]
    )
    assert out is not None
    assert out["channels"][0]["path"] == []


# ── error / edge branches ────────────────────────────────────────────────────


def test_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.channel_spec_path_batch(
            "not_a_tier", ent.TIER_ENTERPRISE, ["telegram"]
        )
        is None
    )


def test_helper_unknown_to_tier_returns_none(ent):
    assert (
        ent.channel_spec_path_batch(
            ent.TIER_OSS, "not_a_tier", ["telegram"]
        )
        is None
    )


def test_helper_empty_channels_yields_empty_envelope(ent):
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, []
    )
    assert out == {"channels": [], "unknown": []}


def test_helper_garbage_inputs_never_raise(ent):
    assert ent.channel_spec_path_batch("", "", []) is None
    assert ent.channel_spec_path_batch(None, None, None) is None  # type: ignore[arg-type]
    assert ent.channel_spec_path_batch("  ", "  ", "  ") is None
    assert (
        ent.channel_spec_path_batch(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, 42
        )
        == {"channels": [], "unknown": []}
    )


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-item failure pushes that id into ``unknown[]`` while the
    rest of the batch keeps building."""
    real = ent.channel_spec_path

    def fake(f, t, cid):
        if cid == "telegram":
            raise RuntimeError("boom")
        return real(f, t, cid)

    monkeypatch.setattr(ent, "channel_spec_path", fake)
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    assert [item["channel"] for item in out["channels"]] == ["signal"]
    assert "telegram" in out["unknown"]


def test_helper_row_returning_none_pushes_to_unknown(ent, monkeypatch):
    real = ent.channel_spec_path

    def fake(f, t, cid):
        if cid == "signal":
            return None
        return real(f, t, cid)

    monkeypatch.setattr(ent, "channel_spec_path", fake)
    out = ent.channel_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    assert [item["channel"] for item in out["channels"]] == ["telegram"]
    assert "signal" in out["unknown"]


def test_helper_grace_and_enforce_yield_identical_output(ent, monkeypatch):
    chans = ["telegram", "signal", "discord"]
    grace = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    assert grace == enforced


# ── HTTP: /api/entitlement/channel-spec-path-batch ───────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch"
        "?to=enterprise&channels=telegram"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch?from=oss&channels=telegram"
    )
    assert r.status_code == 400


def test_api_400_on_missing_channels(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply channels=<csv>"


def test_api_400_on_empty_channels(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch"
        "?from=oss&to=enterprise&channels="
    )
    assert r.status_code == 400


def test_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch"
        "?from=not_a_tier&to=enterprise&channels=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"


def test_api_404_on_unknown_to_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-path-batch"
        "?from=oss&to=not_a_tier&channels=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert [item["channel"] for item in body["channels"]] == [
        "telegram",
        "signal",
    ]
    for item in body["channels"]:
        assert item["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_direction_downgrade(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&channels=telegram"
    )
    body = r.get_json()
    assert body["direction"] == "downgrade"


def test_api_direction_lateral(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&channels=telegram"
    )
    body = r.get_json()
    assert body["direction"] == "lateral"
    for item in body["channels"]:
        assert len(item["path"]) == 1
        assert item["path"][0]["rung"] == ent.TIER_PRO


def test_api_direction_identity(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    for item in body["channels"]:
        assert item["path"] == []


def test_api_unknown_id_echoed(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,bogus_channel"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == ["telegram"]
    assert body["unknown"] == ["bogus_channel"]


def test_api_normalises_channels(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=%20TELEGRAM%20,signal,telegram"
    )
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == [
        "telegram",
        "signal",
    ]


def test_api_trial_accepted_as_endpoint(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_TRIAL}"
        f"&to={ent.TIER_TRIAL}&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["channels"][0]["path"] == []


def test_api_per_item_path_matches_scalar_route(client, ent):
    """Pin: per-item ``path`` in the batch response byte-equals the scalar
    ``/api/entitlement/channel-spec-path`` response for the same triple."""
    batch = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal,discord"
    ).get_json()
    for item in batch["channels"]:
        scalar = client.get(
            f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
            f"&to={ent.TIER_ENTERPRISE}&channel={item['channel']}"
        ).get_json()
        assert item["path"] == scalar["path"]


def test_api_never_5xx_on_helper_failure(client, ent, monkeypatch):
    """If ``channel_spec_path_batch`` raises deep in the helper, the
    endpoint must fall back to an empty envelope instead of 5xxing."""
    import clawmetry.entitlements as _ent

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "channel_spec_path_batch", boom)
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] == []
    assert body["unknown"] == []


def test_api_row_failure_short_circuits_item(client, ent, monkeypatch):
    """A helper-level per-channel failure lands the channel in
    ``unknown[]`` while the rest of the batch keeps building -- the
    endpoint should render this without dropping to 5xx."""
    import clawmetry.entitlements as _ent

    real = _ent.channel_spec_path

    def fake(f, t, cid):
        if cid == "signal":
            raise RuntimeError("boom")
        return real(f, t, cid)

    monkeypatch.setattr(_ent, "channel_spec_path", fake)
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == ["telegram"]
    assert "signal" in body["unknown"]


def test_api_envelope_ranks_populated(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    body = r.get_json()
    assert isinstance(body["from_rank"], int) and body["from_rank"] >= 0
    assert isinstance(body["to_rank"], int) and body["to_rank"] >= 0
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["to_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
