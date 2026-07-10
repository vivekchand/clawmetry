"""Tests for the bare (source-aware) directional channel-axis batch
projections ``Entitlement.next_tier_channel_spec_batch`` /
``Entitlement.previous_tier_channel_spec_batch``, their module-level
convenience wrappers, and the two companion
``/api/entitlement/{next,previous}-tier-channel-spec-batch`` endpoints.

Channel-axis twin of the feature/runtime pair covered by
``test_entitlement_next_prev_tier_feature_runtime_spec_batch.py``. Where
those project N features / runtimes onto the rung above (or below) the
resolved entitlement in ONE round-trip, these project N chat channels.
Batch sibling of the scalar bare channel projection
(``next/previous_tier_channel_spec``, merged in #3602).

The channel-axis invariant is stronger than the feature/runtime axes:
every chat channel is FREE at every tier (see :func:`channel_spec_at`),
so whenever ``row`` is not ``None`` it comes back ``free=True`` /
``locked=False`` / ``entitled=True`` regardless of the target rung. That
parity IS the answer -- an upgrade-preview panel walking a channel picker
can render "all supplied chat channels included at every plan" off ONE
call. These tests pin that invariant on both the helper and the endpoint.

Pins covered here:

* per-row byte-equality with the scalar bare sibling
  ``next/previous_tier_channel_spec(channel)`` across every purchasable
  source
* ceiling / floor produces per-row ``row=null`` with envelope entries
  still rendered so the matrix keeps a stable row count
* trial-as-source resolves next -> enterprise, previous -> cloud_starter
  (matches sibling scalar family)
* input normalisation (whitespace, lowercase, duplicate drop, first-seen
  order preserved)
* unknown ids bucketed in ``unknown[]`` alongside valid rows rather than
  short-circuiting
* always-free invariant: every non-null row reports ``free=True`` /
  ``locked=False`` / ``entitled=True`` at every rung
* grace vs enforce yields byte-identical bodies (catalogue-derived)
* module-level wrappers match the bound method on the resolved
  entitlement
* helpers never raise on synthesised resolver failure; module-level
  wrappers fall back to an empty envelope
* HTTP 400 / 200 error envelopes on both endpoints (missing csv,
  never-5xx grace fallback)
* endpoint rows byte-match the helper on the live perspective
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ROW_KEYS = {"channel", "row"}
_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "target",
    "target_label",
    "target_rank",
    "channels",
    "unknown",
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


def _some_channels(ent):
    # A short deterministic slice of channels so the batch has non-trivial
    # content to parity-check.
    return list(ent.ALL_CHANNELS[:3])


# ── Entitlement.next_tier_channel_spec_batch ────────────────────────────────


def test_next_tier_channel_spec_batch_parity_with_scalar(ent):
    # Each row must byte-equal next_tier_channel_spec(channel) so the scalar
    # and batch accessors cannot drift.
    channels = _some_channels(ent)
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        body = e.next_tier_channel_spec_batch(channels)
        assert set(body.keys()) == {"channels", "unknown"}
        assert body["unknown"] == []
        assert [row["channel"] for row in body["channels"]] == channels
        for row in body["channels"]:
            assert set(row.keys()) == _ROW_KEYS
            assert row["row"] == e.next_tier_channel_spec(row["channel"])


def test_next_tier_channel_spec_batch_at_ceiling(ent):
    # Enterprise has no rung above -- every row should be null but the
    # per-channel entries still render so the row count stays stable.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    channels = _some_channels(ent)
    body = e.next_tier_channel_spec_batch(channels)
    assert [row["channel"] for row in body["channels"]] == channels
    assert all(row["row"] is None for row in body["channels"])
    assert body["unknown"] == []


def test_next_tier_channel_spec_batch_normalises_input(ent):
    # Duplicates dropped, whitespace stripped, case-lowered, first-seen order
    # preserved -- shared _normalise_csv posture.
    channels = _some_channels(ent)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    raw = f"  {channels[0].upper()}  ,{channels[1]},{channels[0]},, "
    body = e.next_tier_channel_spec_batch(raw)
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == []


def test_next_tier_channel_spec_batch_unknown_ids_bucketed(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    channels = _some_channels(ent)
    body = e.next_tier_channel_spec_batch(
        [channels[0], "no_such_channel", channels[1]]
    )
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == ["no_such_channel"]


def test_next_tier_channel_spec_batch_empty_csv(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_channel_spec_batch("")
    assert body == {"channels": [], "unknown": []}


def test_next_tier_channel_spec_batch_never_raises(ent, monkeypatch):
    # If next_purchasable_tier blows up, the helper must swallow and return
    # rows with row=null so the matrix keeps rendering.
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    channels = _some_channels(ent)
    body = e.next_tier_channel_spec_batch(channels)
    assert [row["channel"] for row in body["channels"]] == channels
    assert all(row["row"] is None for row in body["channels"])


def test_next_tier_channel_spec_batch_always_free_invariant(ent):
    # Every non-null row must come back free=True / locked=False /
    # entitled=True regardless of the target rung -- pins the channel-axis
    # promise that the batch surface can rely on.
    channels = list(ent.ALL_CHANNELS)
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        body = e.next_tier_channel_spec_batch(channels)
        for row in body["channels"]:
            if row["row"] is None:
                continue
            assert row["row"]["free"] is True
            assert row["row"]["locked"] is False
            assert row["row"]["entitled"] is True


def test_next_tier_channel_spec_batch_all_channels_covered(ent):
    # Handing the full catalogue must return every channel in supply order
    # with no unknowns dropped.
    channels = list(ent.ALL_CHANNELS)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_channel_spec_batch(channels)
    assert [row["channel"] for row in body["channels"]] == channels
    assert body["unknown"] == []


# ── Entitlement.previous_tier_channel_spec_batch ────────────────────────────


def test_previous_tier_channel_spec_batch_parity_with_scalar(ent):
    channels = _some_channels(ent)
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        body = e.previous_tier_channel_spec_batch(channels)
        assert set(body.keys()) == {"channels", "unknown"}
        for row in body["channels"]:
            assert set(row.keys()) == _ROW_KEYS
            assert row["row"] == e.previous_tier_channel_spec(row["channel"])


def test_previous_tier_channel_spec_batch_at_floor(ent):
    # OSS / cloud_free -- nothing below to step down to.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        channels = _some_channels(ent)
        body = e.previous_tier_channel_spec_batch(channels)
        assert [row["channel"] for row in body["channels"]] == channels
        assert all(row["row"] is None for row in body["channels"])


def test_previous_tier_channel_spec_batch_never_raises(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    channels = _some_channels(ent)
    body = e.previous_tier_channel_spec_batch(channels)
    assert [row["channel"] for row in body["channels"]] == channels
    assert all(row["row"] is None for row in body["channels"])


def test_previous_tier_channel_spec_batch_always_free_invariant(ent):
    channels = list(ent.ALL_CHANNELS)
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        body = e.previous_tier_channel_spec_batch(channels)
        for row in body["channels"]:
            if row["row"] is None:
                continue
            assert row["row"]["free"] is True
            assert row["row"]["locked"] is False
            assert row["row"]["entitled"] is True


def test_previous_tier_channel_spec_batch_normalises_input(ent):
    channels = _some_channels(ent)
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    raw = f"  {channels[0].upper()}  ,{channels[1]},{channels[0]},, "
    body = e.previous_tier_channel_spec_batch(raw)
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == []


def test_previous_tier_channel_spec_batch_unknown_ids_bucketed(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    channels = _some_channels(ent)
    body = e.previous_tier_channel_spec_batch(
        [channels[0], "no_such_channel", channels[1]]
    )
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == ["no_such_channel"]


# ── trial source resolution ─────────────────────────────────────────────────


def test_trial_next_batch_resolves_to_enterprise(ent):
    # Trial's next purchasable is enterprise (matches next_tier_spec).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    channels = _some_channels(ent)
    body = e.next_tier_channel_spec_batch(channels)
    for row in body["channels"]:
        expected = ent.channel_spec_at(ent.TIER_ENTERPRISE, row["channel"])
        assert row["row"] == expected


def test_trial_previous_batch_resolves_to_starter(ent):
    e = ent._build(ent.TIER_TRIAL, "cloud")
    channels = _some_channels(ent)
    body = e.previous_tier_channel_spec_batch(channels)
    for row in body["channels"]:
        expected = ent.channel_spec_at(ent.TIER_CLOUD_STARTER, row["channel"])
        assert row["row"] == expected


# ── grace vs enforce ────────────────────────────────────────────────────────


def test_grace_vs_enforce_next_batch_identical(ent, monkeypatch):
    channels = _some_channels(ent)
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_channel_spec_batch(channels)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_channel_spec_batch(channels)
    assert enforce_body == grace_body


def test_grace_vs_enforce_previous_batch_identical(ent, monkeypatch):
    channels = _some_channels(ent)
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    grace_body = e.previous_tier_channel_spec_batch(channels)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    enforce_body = e2.previous_tier_channel_spec_batch(channels)
    assert enforce_body == grace_body


# ── module-level wrappers ───────────────────────────────────────────────────


def test_module_level_next_channel_batch_matches_method(ent):
    channels = _some_channels(ent)
    assert ent.next_tier_channel_spec_batch(channels) == (
        ent.get_entitlement().next_tier_channel_spec_batch(channels)
    )


def test_module_level_previous_channel_batch_matches_method(ent):
    channels = _some_channels(ent)
    assert ent.previous_tier_channel_spec_batch(channels) == (
        ent.get_entitlement().previous_tier_channel_spec_batch(channels)
    )


def test_module_level_next_channel_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    channels = _some_channels(ent)
    assert ent.next_tier_channel_spec_batch(channels) == {
        "channels": [],
        "unknown": [],
    }


def test_module_level_previous_channel_batch_never_raises(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    channels = _some_channels(ent)
    assert ent.previous_tier_channel_spec_batch(channels) == {
        "channels": [],
        "unknown": [],
    }


# ── /api/entitlement/next-tier-channel-spec-batch endpoint ──────────────────


def test_endpoint_next_channel_batch_default_oss(client, ent):
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert [row["channel"] for row in body["channels"]] == channels
    assert body["unknown"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_next_channel_batch_row_matches_helper(client, ent):
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    body = rv.get_json()
    helper = ent.next_tier_channel_spec_batch(channels)
    assert body["channels"] == helper["channels"]
    assert body["unknown"] == helper["unknown"]


def test_endpoint_next_channel_batch_row_matches_scalar(client, ent):
    # Endpoint row must byte-match /next-tier-channel-spec?channel=<id> .row
    # for the same channel -- pins the scalar/batch parity through HTTP.
    channels = _some_channels(ent)
    rv_batch = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join(channels)
    ).get_json()
    for row in rv_batch["channels"]:
        rv_scalar = client.get(
            f"/api/entitlement/next-tier-channel-spec?channel={row['channel']}"
        ).get_json()
        assert row["row"] == rv_scalar["row"]


def test_endpoint_next_channel_batch_missing_csv(client):
    rv = client.get("/api/entitlement/next-tier-channel-spec-batch")
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "supply channels=<csv>"


def test_endpoint_next_channel_batch_empty_csv(client):
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels=,"
    )
    assert rv.status_code == 400


def test_endpoint_next_channel_batch_unknown_bucketed(client, ent):
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join([channels[0], "no_such_channel", channels[1]])
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == ["no_such_channel"]


def test_endpoint_next_channel_batch_always_free_invariant(client, ent):
    channels = list(ent.ALL_CHANNELS)
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    body = rv.get_json()
    for row in body["channels"]:
        if row["row"] is None:
            continue
        assert row["row"]["free"] is True
        assert row["row"]["locked"] is False
        assert row["row"]["entitled"] is True


def test_endpoint_next_channel_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/next-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == "oss"
    assert body["channels"] == []
    assert body["unknown"] == []
    assert body["target"] is None


# ── /api/entitlement/previous-tier-channel-spec-batch endpoint ──────────────


def test_endpoint_previous_channel_batch_default_oss_floor(client, ent):
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- target and every row is null.
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert all(row["row"] is None for row in body["channels"])
    assert [row["channel"] for row in body["channels"]] == channels


def test_endpoint_previous_channel_batch_row_matches_scalar(client, ent):
    channels = _some_channels(ent)
    rv_batch = client.get(
        "/api/entitlement/previous-tier-channel-spec-batch?channels="
        + ",".join(channels)
    ).get_json()
    for row in rv_batch["channels"]:
        rv_scalar = client.get(
            "/api/entitlement/previous-tier-channel-spec"
            f"?channel={row['channel']}"
        ).get_json()
        assert row["row"] == rv_scalar["row"]


def test_endpoint_previous_channel_batch_missing_csv(client):
    rv = client.get("/api/entitlement/previous-tier-channel-spec-batch")
    assert rv.status_code == 400


def test_endpoint_previous_channel_batch_unknown_bucketed(client, ent):
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec-batch?channels="
        + ",".join([channels[0], "no_such_channel", channels[1]])
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert [row["channel"] for row in body["channels"]] == channels[:2]
    assert body["unknown"] == ["no_such_channel"]


def test_endpoint_previous_channel_batch_never_5xxs(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    channels = _some_channels(ent)
    rv = client.get(
        "/api/entitlement/previous-tier-channel-spec-batch?channels="
        + ",".join(channels)
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["channels"] == []
