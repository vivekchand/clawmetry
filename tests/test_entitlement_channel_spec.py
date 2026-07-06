"""Tests for ``channel_spec(channel)`` and ``GET
/api/entitlement/channel-spec``.

``channel_spec`` is the scalar sibling of ``channel_catalog()`` -- the row
shape a channel-detail page or "which channels does this account have
turned on" tooltip hydrates against in one round-trip instead of fetching
the full catalogue and filtering client-side.

Pins:

* the row shape matches a row from ``channel_catalog()`` exactly (so the
  scalar and bulk accessors cannot drift)
* every id in ``ALL_CHANNELS`` round-trips through ``channel_spec``
* unknown / empty / ``None`` / non-string ids return ``None``
* the input is trimmed + lowercased before resolution
* every channel is FREE at every tier (the ``channels`` capacity axis
  governs capacity, not adapter unlock), so grace vs enforce yields a
  byte-identical row
* the endpoint 400s on a missing arg, 404s on an unknown id, and never
  5xxs (a resolver crash still returns a catalogue row built against the
  OSS-free fallback)
"""
from __future__ import annotations

import importlib
import json

import pytest


_SPEC_KEYS = {
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_spec_row_keys_match_catalog_row(ent):
    """A row from ``channel_spec`` carries the same keys as a
    ``channel_catalog()`` row -- defends against a rename on one side
    silently shipping a half-renamed payload to the UI."""
    cat_keys = set(ent.channel_catalog()[0].keys())
    assert cat_keys == _SPEC_KEYS
    ch = next(iter(ent.ALL_CHANNELS))
    spec = ent.channel_spec(ch)
    assert spec is not None
    assert set(spec.keys()) == _SPEC_KEYS


def test_spec_parity_with_every_catalog_row(ent):
    """For every row in the catalogue, the scalar accessor returns the
    same dict. Pins the scalar/bulk no-drift contract."""
    cat_by_id = {row["id"]: row for row in ent.channel_catalog()}
    assert set(cat_by_id.keys()) == set(ent.ALL_CHANNELS)
    for ch, row in cat_by_id.items():
        assert ent.channel_spec(ch) == row, ch


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_known_channel_round_trips(ent):
    for ch in ent.ALL_CHANNELS:
        spec = ent.channel_spec(ch)
        assert spec is not None, ch
        assert spec["id"] == ch


def test_unknown_channel_returns_none(ent):
    assert ent.channel_spec("not_a_real_channel") is None


def test_empty_returns_none(ent):
    assert ent.channel_spec("") is None


def test_whitespace_only_returns_none(ent):
    assert ent.channel_spec("   ") is None


def test_none_returns_none(ent):
    assert ent.channel_spec(None) is None


def test_non_string_returns_none(ent):
    # Defensive: a stray int / list / dict / object from a malformed caller
    # must not crash.
    assert ent.channel_spec(123) is None
    assert ent.channel_spec(1.5) is None
    assert ent.channel_spec(["telegram"]) is None
    assert ent.channel_spec({"id": "telegram"}) is None
    assert ent.channel_spec(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    ch = next(iter(ent.ALL_CHANNELS))
    assert ent.channel_spec(ch.upper()) == ent.channel_spec(ch)
    assert ent.channel_spec(f"  {ch}  ") == ent.channel_spec(ch)
    assert ent.channel_spec(f"\t{ch.upper()}\n") == ent.channel_spec(ch)


# ── always-free invariant ─────────────────────────────────────────────────────


def test_every_channel_is_always_free(ent):
    """Every chat channel is FREE at every tier -- the ``channels``
    capacity axis governs how many concurrent channels each plan admits,
    not which adapters unlock."""
    for ch in ent.ALL_CHANNELS:
        row = ent.channel_spec(ch)
        assert row["free"] is True, ch
        assert row["tier"] == "free", ch
        assert row["allowed"] is True, ch
        assert row["locked"] is False, ch
        assert row["entitled"] is True, ch


# ── label carriage ────────────────────────────────────────────────────────────


def test_label_matches_channel_label_helper(ent):
    for ch in ent.ALL_CHANNELS:
        row = ent.channel_spec(ch)
        assert row["label"] == ent.channel_label(ch), ch


# ── grace vs enforce ──────────────────────────────────────────────────────────


def test_grace_locks_nothing(ent):
    for ch in ent.ALL_CHANNELS:
        row = ent.channel_spec(ch)
        assert row["allowed"] is True, ch
        assert row["locked"] is False, ch


def test_enforce_oss_still_unlocks_every_channel(ent, monkeypatch):
    """Every chat channel is FREE at every tier -- enforcement is a
    no-op on the channel axis, so the row is byte-identical to grace."""
    grace_rows = {ch: ent.channel_spec(ch) for ch in ent.ALL_CHANNELS}
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    for ch in ent.ALL_CHANNELS:
        assert ent.channel_spec(ch) == grace_rows[ch], ch


def test_enforce_cloud_pro_yields_identical_row(ent, monkeypatch, tmp_path):
    grace_rows = {ch: ent.channel_spec(ch) for ch in ent.ALL_CHANNELS}
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    for ch in ent.ALL_CHANNELS:
        assert ent.channel_spec(ch) == grace_rows[ch], ch


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_resolver_crashes(ent, monkeypatch):
    """A blown resolver still returns the catalogue row built against
    the OSS-free fallback -- matches the never-crash contract on
    ``channel_catalog()``."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    row = ent.channel_spec(ch)
    assert row is not None
    assert row["id"] == ch
    assert row["free"] is True


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_channel_returns_row(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec?channel={ch}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == ent.channel_spec(ch)


def test_endpoint_lowercases_and_trims(client, ent):
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(
        f"/api/entitlement/channel-spec?channel=%20%20{ch.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == ch


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-spec")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-spec?channel=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_channel_returns_404(client):
    resp = client.get("/api/entitlement/channel-spec?channel=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["channel"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_known_channel_round_trips(client, ent):
    for ch in ent.ALL_CHANNELS:
        resp = client.get(f"/api/entitlement/channel-spec?channel={ch}")
        assert resp.status_code == 200, ch
        body = resp.get_json()
        assert body["id"] == ch, ch


def test_endpoint_body_byte_equals_catalog_row(client, ent):
    """The endpoint body must byte-equal the corresponding row in
    ``/api/entitlement/channel-catalog`` -- pins the scalar/bulk
    no-drift contract on the wire."""
    cat_resp = client.get("/api/entitlement/channel-catalog")
    assert cat_resp.status_code == 200
    cat_by_id = {row["id"]: row for row in cat_resp.get_json()["channels"]}
    for ch in ent.ALL_CHANNELS:
        resp = client.get(f"/api/entitlement/channel-spec?channel={ch}")
        assert resp.status_code == 200, ch
        assert resp.get_json() == cat_by_id[ch], ch


def test_endpoint_returns_grace_row_even_when_resolver_crashes(
    client, ent, monkeypatch
):
    """``channel_spec`` catches resolver failures internally and falls
    back to the OSS-free row, so the endpoint must return 200 + a
    valid catalogue row even when ``get_entitlement`` explodes."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    ch = next(iter(ent.ALL_CHANNELS))
    resp = client.get(f"/api/entitlement/channel-spec?channel={ch}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == ch
    assert body["free"] is True
