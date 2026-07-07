"""Tests for ``channel_spec_batch(channels)`` and ``GET
/api/entitlement/channel-spec-batch``.

``channel_spec_batch`` is the plural / caller-subset sibling of
``channel_spec`` on the chat-channel axis -- the batch accessor a paywall
matrix UI hydrates the N rows it is about to render off in ONE round-trip
instead of N calls to ``/api/entitlement/channel-spec``. Each returned
row must be byte-identical to the corresponding row from
``channel_catalog()`` so the scalar / bulk / batch accessors cannot
drift; the parity tests below pin that.

Coverage:

* row shape matches ``channel_catalog`` (and matches the scalar
  ``channel_spec`` row for the same id)
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved)
* unknown ids are echoed in ``unknown[]`` instead of 404'ing the call
* every chat channel is FREE at every tier, so grace vs enforce yields
  byte-identical rows and no row is ever ``locked`` regardless of the
  resolved tier
* the helper never raises -- a resolver crash short-circuits to the
  OSS-free fallback so the matrix keeps rendering
* the HTTP endpoint 400s on missing / empty input, never 5xxs on a
  resolver crash, and carries the standard ``grace`` / ``enforced`` /
  ``current_tier`` / ``current_tier_rank`` envelope fields
"""
from __future__ import annotations

import importlib
import json

import pytest


_CHANNEL_SPEC_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "allowed",
    "locked",
    "entitled",
}

_ENVELOPE_KEYS = {"current_tier", "current_tier_rank", "grace", "enforced"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default (grace mode)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── helper: shape + parity ────────────────────────────────────────────────────


def test_batch_empty_input_returns_empty_envelope(ent):
    assert ent.channel_spec_batch([]) == {"channels": [], "unknown": []}


def test_batch_none_input_returns_empty_envelope(ent):
    assert ent.channel_spec_batch(None) == {"channels": [], "unknown": []}


def test_batch_row_shape_matches_catalog(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_batch([ch])
    assert len(body["channels"]) == 1
    assert set(body["channels"][0].keys()) == _CHANNEL_SPEC_KEYS


def test_batch_every_row_matches_channel_spec_exactly(ent):
    ids = sorted(ent.ALL_CHANNELS)
    body = ent.channel_spec_batch(ids)
    rows_by_id = {row["id"]: row for row in body["channels"]}
    assert set(rows_by_id) == set(ids)
    for cid in ids:
        assert rows_by_id[cid] == ent.channel_spec(cid), cid


def test_batch_rows_match_channel_catalog(ent):
    """Pin scalar / bulk / batch no-drift: every batch row is byte-identical
    to the same row from ``channel_catalog()``."""
    cat_by_id = {row["id"]: row for row in ent.channel_catalog()}
    ids = list(cat_by_id)
    body = ent.channel_spec_batch(ids)
    assert body["unknown"] == []
    for row in body["channels"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── helper: normalisation ────────────────────────────────────────────────────


def test_batch_supply_order_preserved(ent):
    ids = list(ent.ALL_CHANNELS)[:3]
    body = ent.channel_spec_batch(list(reversed(ids)))
    assert [r["id"] for r in body["channels"]] == list(reversed(ids))


def test_batch_string_csv_input(ent):
    ids = list(ent.ALL_CHANNELS)[:3]
    csv = ",".join(ids)
    body = ent.channel_spec_batch(csv)
    assert [r["id"] for r in body["channels"]] == ids


def test_batch_whitespace_and_case_normalised(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_batch([f"  {ch.upper()}  "])
    assert [r["id"] for r in body["channels"]] == [ch]


def test_batch_duplicates_dropped_first_seen_wins(ent):
    ids = list(ent.ALL_CHANNELS)[:2]
    a, b = ids
    body = ent.channel_spec_batch([a, a, b, a])
    assert [r["id"] for r in body["channels"]] == [a, b]


def test_batch_unknown_ids_echoed_in_unknown(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_batch([ch, "nope_xyz", "also_bogus"])
    assert [r["id"] for r in body["channels"]] == [ch]
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


def test_batch_unknown_only_returns_empty_channels(ent):
    body = ent.channel_spec_batch(["nope_xyz", "also_bogus"])
    assert body["channels"] == []
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


# ── helper: always-free invariant ────────────────────────────────────────────


def test_batch_every_channel_is_always_free(ent):
    body = ent.channel_spec_batch(sorted(ent.ALL_CHANNELS))
    assert len(body["channels"]) == len(ent.ALL_CHANNELS)
    for row in body["channels"]:
        assert row["free"] is True, row["id"]
        assert row["tier"] == "free", row["id"]
        assert row["allowed"] is True, row["id"]
        assert row["locked"] is False, row["id"]
        assert row["entitled"] is True, row["id"]


def test_batch_grace_locks_nothing(ent):
    body = ent.channel_spec_batch(sorted(ent.ALL_CHANNELS))
    assert all(r["locked"] is False for r in body["channels"])
    assert all(r["allowed"] is True for r in body["channels"])


def test_batch_enforce_oss_still_unlocks_every_channel(ent, monkeypatch):
    """Enforcement is a no-op on the channel axis, so a batch under
    enforce-mode is byte-identical to a batch under grace."""
    ids = sorted(ent.ALL_CHANNELS)
    grace_body = ent.channel_spec_batch(ids)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_body = ent.channel_spec_batch(ids)
    assert enforced_body["channels"] == grace_body["channels"]
    assert enforced_body["unknown"] == grace_body["unknown"]


def test_batch_enforce_cloud_pro_yields_identical_rows(ent, monkeypatch, tmp_path):
    ids = sorted(ent.ALL_CHANNELS)
    grace_body = ent.channel_spec_batch(ids)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    enforced_body = ent.channel_spec_batch(ids)
    assert enforced_body["channels"] == grace_body["channels"]


# ── helper: never-raise ──────────────────────────────────────────────────────


def test_batch_never_raises_when_resolver_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    body = ent.channel_spec_batch([ch])
    assert len(body["channels"]) == 1
    row = body["channels"][0]
    assert row["id"] == ch
    # Every channel is free under the OSS-free fallback -- matches the
    # never-crash contract on ``channel_catalog()`` / ``channel_spec``.
    assert row["free"] is True
    assert row["locked"] is False


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_returns_rows_and_envelope(client, ent):
    ids = list(ent.ALL_CHANNELS)[:2]
    csv = ",".join(ids)
    resp = client.get(f"/api/entitlement/channel-spec-batch?channels={csv}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["channels"]] == ids
    assert body["unknown"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-spec-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-spec-batch?channels=%20%20,%20")
    assert resp.status_code == 400


def test_endpoint_unknown_only_returns_200(client):
    """Unknown ids alone do not 400 -- they normalise to a non-empty list
    so the helper runs and returns ``unknown=[...]`` with empty channels."""
    resp = client.get(
        "/api/entitlement/channel-spec-batch?channels=not_a_channel,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] == []
    assert body["unknown"] == ["not_a_channel", "also_bogus"]


def test_endpoint_lowercases_and_dedupes(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec-batch?channels={ch.upper()},{ch}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["channels"]] == [ch]


def test_endpoint_every_known_channel_round_trips(client, ent):
    csv = ",".join(sorted(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec-batch?channels={csv}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(r["id"] for r in body["channels"]) == set(ent.ALL_CHANNELS)
    assert body["unknown"] == []


def test_endpoint_body_channels_byte_equal_catalog_rows(client, ent):
    """The endpoint body must byte-equal the corresponding rows in
    ``/api/entitlement/channel-catalog`` -- pins the scalar / bulk /
    batch no-drift contract on the wire."""
    cat_resp = client.get("/api/entitlement/channel-catalog")
    assert cat_resp.status_code == 200
    cat_by_id = {row["id"]: row for row in cat_resp.get_json()["channels"]}
    csv = ",".join(sorted(cat_by_id))
    resp = client.get(f"/api/entitlement/channel-spec-batch?channels={csv}")
    assert resp.status_code == 200
    for row in resp.get_json()["channels"]:
        assert row == cat_by_id[row["id"]], row["id"]


def test_endpoint_envelope_carries_resolved_tier(client, ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec-batch?channels={ch}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_tier"] == ent.TIER_CLOUD_PRO
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["grace"] is False
    assert body["enforced"] is True


def test_endpoint_never_5xxs_when_resolver_crashes(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec-batch?channels={ch}")
    assert resp.status_code == 200
    body = resp.get_json()
    # Endpoint short-circuits to the OSS-free envelope on resolver failure.
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
