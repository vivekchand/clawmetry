"""Tests for the channel-axis catalogue helpers and endpoint:

* :data:`clawmetry.entitlements.ALL_CHANNELS`
* :data:`clawmetry.entitlements.CHANNEL_LABELS`
* :func:`clawmetry.entitlements.channel_label`
* :func:`clawmetry.entitlements.channel_catalog`
* ``GET /api/entitlement/channel-catalog``

The channel axis has no paid-channel tier -- every chat-channel adapter is
FREE, and the ``channels`` capacity axis
(:func:`min_tier_for_channel_count` + the ``channels=`` arg on the
aggregate helpers) governs how many concurrent channels each plan admits.
So the catalogue is purely enumerative: one row per adapter, all
unlocked. The tests below defend that posture, the sort order, the
never-5xx contract, and pin :data:`ALL_CHANNELS` in lockstep with
``clawmetry.sync._CHANNEL_DIRS`` so a new adapter can't ship in the
daemon without also being catalogued.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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


# ── ALL_CHANNELS / CHANNEL_LABELS ─────────────────────────────────────────


def test_all_channels_is_a_tuple_of_strings(ent):
    assert isinstance(ent.ALL_CHANNELS, tuple)
    assert all(isinstance(ch, str) and ch for ch in ent.ALL_CHANNELS)


def test_all_channels_has_no_duplicates(ent):
    assert len(set(ent.ALL_CHANNELS)) == len(ent.ALL_CHANNELS)


def test_all_channels_is_nonempty(ent):
    assert len(ent.ALL_CHANNELS) >= 1


def test_channel_labels_covers_every_channel(ent):
    """Every id in :data:`ALL_CHANNELS` must have a curated label.

    :func:`channel_label` falls back to a title-cased echo, so a missing
    label doesn't render as a blank cell; but a curated label is the
    stronger guarantee -- the catalogue should never leak an id-shaped
    "Msteams" into a pricing page when the vendor spells it "Microsoft
    Teams".
    """
    missing = [ch for ch in ent.ALL_CHANNELS if ch not in ent.CHANNEL_LABELS]
    assert not missing, f"channels without a curated label: {missing}"


def test_all_channels_matches_sync_channel_dirs(ent):
    """Pin :data:`ALL_CHANNELS` to ``clawmetry.sync._CHANNEL_DIRS``.

    Adding a new chat-channel adapter is a two-place edit today (the
    daemon walks ``_CHANNEL_DIRS``, the catalogue reads
    :data:`ALL_CHANNELS`); this pin fails loudly the moment the two lists
    drift so a new adapter can't ship in the daemon without also being
    catalogued (which would silently hide it from the pricing UI).
    """
    from clawmetry import sync as _sync

    assert set(ent.ALL_CHANNELS) == set(_sync._CHANNEL_DIRS)


# ── channel_label ─────────────────────────────────────────────────────────


def test_channel_label_returns_curated_label(ent):
    assert ent.channel_label("telegram") == "Telegram"
    assert ent.channel_label("whatsapp") == "WhatsApp"
    assert ent.channel_label("imessage") == "iMessage"


def test_channel_label_case_insensitive_and_trimmed(ent):
    assert ent.channel_label("  TELEGRAM  ") == "Telegram"
    assert ent.channel_label("Telegram") == "Telegram"


def test_channel_label_unknown_falls_back_to_title_case_echo(ent):
    """Unknown ids don't crash and don't render as a blank cell."""
    assert ent.channel_label("brand_new_adapter") == "Brand New Adapter"


def test_channel_label_empty_and_none_return_empty_string(ent):
    assert ent.channel_label("") == ""
    assert ent.channel_label(None) == ""


def test_channel_label_never_raises_on_garbage(ent):
    assert ent.channel_label(42) == ""
    assert ent.channel_label(object()) == ""


# ── channel_catalog helper ────────────────────────────────────────────────


def test_channel_catalog_returns_a_list(ent):
    out = ent.channel_catalog()
    assert isinstance(out, list)


def test_channel_catalog_has_one_row_per_channel(ent):
    rows = ent.channel_catalog()
    assert len(rows) == len(ent.ALL_CHANNELS)


def test_channel_catalog_row_ids_match_all_channels(ent):
    ids = {row["id"] for row in ent.channel_catalog()}
    assert ids == set(ent.ALL_CHANNELS)


def test_channel_catalog_is_sorted_alphabetically(ent):
    """Row order must be stable across releases so a pricing table doesn't
    reshuffle on redeploy."""
    ids = [row["id"] for row in ent.channel_catalog()]
    assert ids == sorted(ent.ALL_CHANNELS)


def test_channel_catalog_row_schema(ent):
    """Row keys mirror :func:`_runtime_spec_row` for free runtimes so a
    matrix UI can render the two catalogues with one row-renderer."""
    expected = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}
    for row in ent.channel_catalog():
        assert set(row.keys()) == expected, row


def test_channel_catalog_every_row_is_free(ent):
    """There is no paid-channel tier: every row must be free / unlocked /
    allowed / entitled."""
    for row in ent.channel_catalog():
        assert row["free"] is True, row
        assert row["tier"] == "free", row
        assert row["allowed"] is True, row
        assert row["locked"] is False, row
        assert row["entitled"] is True, row


def test_channel_catalog_labels_come_from_channel_label_helper(ent):
    for row in ent.channel_catalog():
        assert row["label"] == ent.channel_label(row["id"])


def test_channel_catalog_never_raises_on_resolver_failure(ent, monkeypatch):
    """A crashing resolver must not propagate: the catalogue falls back
    to the OSS-free entitlement so the UI keeps rendering."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.channel_catalog()
    assert len(rows) == len(ent.ALL_CHANNELS)
    for row in rows:
        assert row["free"] is True


def test_channel_catalog_grace_and_enforce_are_identical(ent, monkeypatch):
    """Every row is free, so flipping enforcement changes nothing."""
    grace = ent.channel_catalog()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.channel_catalog()
    assert grace == enforce


# ── API: /api/entitlement/channel-catalog ─────────────────────────────────


def test_channel_catalog_endpoint_200(client):
    resp = client.get("/api/entitlement/channel-catalog")
    assert resp.status_code == 200


def test_channel_catalog_endpoint_envelope_shape(client):
    body = client.get("/api/entitlement/channel-catalog").get_json()
    assert set(body.keys()) == {"tier", "channels", "grace", "enforced"}
    assert isinstance(body["channels"], list)
    assert isinstance(body["tier"], str)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_channel_catalog_endpoint_grace_and_enforced_are_negations(client):
    body = client.get("/api/entitlement/channel-catalog").get_json()
    assert body["grace"] is not body["enforced"]


def test_channel_catalog_endpoint_tier_matches_resolved(client, ent):
    body = client.get("/api/entitlement/channel-catalog").get_json()
    assert body["tier"] == ent.get_entitlement().tier


def test_channel_catalog_endpoint_rows_match_helper(client, ent):
    """Byte-parity with :func:`channel_catalog` so the endpoint can't
    drift from the helper a CLI wrapper might call directly."""
    body = client.get("/api/entitlement/channel-catalog").get_json()
    assert body["channels"] == ent.channel_catalog()


def test_channel_catalog_endpoint_covers_every_channel(client, ent):
    body = client.get("/api/entitlement/channel-catalog").get_json()
    ids = {row["id"] for row in body["channels"]}
    assert ids == set(ent.ALL_CHANNELS)


def test_channel_catalog_endpoint_never_5xxs_on_helper_failure(
    client, ent, monkeypatch
):
    """A crashing helper must not 500 the endpoint. Falls back to the
    OSS-free envelope so the pricing UI keeps rendering."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper failure")

    monkeypatch.setattr(ent, "channel_catalog", boom)
    resp = client.get("/api/entitlement/channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_channel_catalog_endpoint_never_5xxs_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get("/api/entitlement/channel-catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == "oss"
    assert body["channels"] == []
    assert body["grace"] is True
    assert body["enforced"] is False
