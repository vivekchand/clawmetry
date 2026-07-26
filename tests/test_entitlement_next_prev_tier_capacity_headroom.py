"""Tests for ``next_tier_capacity_headroom`` / ``previous_tier_capacity_headroom``
+ the ``/api/entitlement/{next,previous}-tier-capacity-headroom`` endpoints.

Scalar "one rung up / down" siblings of :func:`capacity_headroom` that fold
current usage into the neighbouring tier's static caps. The upgrade CTA card
uses these to render "here's what your gauges would look like on <next tier>"
off one call, and the downgrade preview card mirrors it for "here's what
would break on <prev tier>".

Pins:
  * inner ``headroom`` row shape matches :func:`capacity_headroom_at`
    byte-for-byte so the existing renderer consumes it unchanged
  * per-axis "None means axis not supplied" posture
  * boundary case: ``headroom`` is ``None`` (helpers) / ``null`` (endpoints
    at HTTP 200) when no next / previous tier exists
  * grace vs enforce yields byte-identical inner rows
  * envelope shape mirrors ``/next-tier-unlocks`` (current-tier context +
    null-at-boundary + direction echo) so a UI can bind both off one shape
  * never raises / never 5xxs
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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


# ── helper: shape + delegation ───────────────────────────────────────────────


def test_next_helper_envelope_matches_capacity_headroom_at(ent):
    # An OSS-default install upgrades to cloud_starter, so the returned
    # envelope must be byte-identical to `capacity_headroom_at(cloud_starter, ...)`.
    row = ent.next_tier_capacity_headroom(channels=3, retention_days=10, nodes=1)
    expected = ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER,
        channels=3,
        retention_days=10,
        nodes=1,
    )
    assert row == expected


def test_prev_helper_envelope_matches_capacity_headroom_at(ent, monkeypatch):
    # Force a resolved entitlement of cloud_pro so previous_purchasable_tier
    # returns cloud_starter (a real rung), then compare.
    e_pro = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e_pro)
    row = ent.previous_tier_capacity_headroom(channels=2, retention_days=25)
    expected = ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=2, retention_days=25,
    )
    assert row == expected


def test_next_row_inner_shape(ent):
    row = ent.next_tier_capacity_headroom(channels=3)
    assert set(row) == {"tier", "tier_label", "channels", "retention_days", "nodes"}
    assert row["tier"] == ent.TIER_CLOUD_STARTER
    # channels axis supplied -> full row; others stay None
    assert isinstance(row["channels"], dict)
    assert row["retention_days"] is None
    assert row["nodes"] is None
    # per-axis row shape matches _headroom_row
    assert set(row["channels"]) == {
        "kind",
        "used",
        "cap",
        "remaining",
        "is_unlimited",
        "at_limit",
        "over_limit",
        "pct_used",
    }


# ── helper: axis semantics ───────────────────────────────────────────────────


def test_no_axes_supplied_returns_neutral_envelope(ent):
    row = ent.next_tier_capacity_headroom()
    assert row is not None
    assert row["channels"] is None
    assert row["retention_days"] is None
    assert row["nodes"] is None


def test_channels_over_prev_tier_cap_flips_over_limit(ent, monkeypatch):
    # Force cloud_starter as the resolved tier so `previous_purchasable_tier`
    # returns cloud_free (or oss) where the channel cap is finite; supply a
    # channel count that exceeds it and pin `over_limit`.
    e_starter = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e_starter)
    prev_tier = ent.previous_purchasable_tier()
    assert prev_tier is not None
    prev_cap = ent._TIER_CHANNEL_LIMIT.get(prev_tier)
    if prev_cap is None:
        pytest.skip("previous tier has unlimited channels; over_limit not applicable")
    row = ent.previous_tier_capacity_headroom(channels=prev_cap + 5)
    axis = row["channels"]
    assert axis["cap"] == prev_cap
    assert axis["used"] == prev_cap + 5
    assert axis["over_limit"] is True
    assert axis["is_unlimited"] is False


# ── helper: boundary cases ───────────────────────────────────────────────────


def test_next_helper_returns_none_at_top_rung(ent, monkeypatch):
    e_ent = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e_ent)
    assert ent.next_tier_capacity_headroom(channels=3) is None


def test_prev_helper_returns_none_at_bottom_rung(ent):
    # Fresh OSS default has no previous purchasable tier.
    assert ent.previous_purchasable_tier() is None
    assert ent.previous_tier_capacity_headroom(channels=3) is None


def test_helpers_never_raise_on_broken_resolver(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_purchasable_tier", boom)
    monkeypatch.setattr(ent, "previous_purchasable_tier", boom)
    assert ent.next_tier_capacity_headroom(channels=3) is None
    assert ent.previous_tier_capacity_headroom(channels=3) is None


# ── grace vs enforce invariance ──────────────────────────────────────────────


def test_next_helper_rows_grace_enforce_identical(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()
    grace_row = e.next_tier_capacity_headroom(channels=3, retention_days=10, nodes=1)

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_row = e.next_tier_capacity_headroom(channels=3, retention_days=10, nodes=1)

    assert grace_row == enforce_row


# ── endpoint: envelope shape ─────────────────────────────────────────────────


def test_next_endpoint_envelope_keys(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-headroom?channels=3")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body) == {
        "current_tier",
        "current_tier_label",
        "current_tier_rank",
        "direction",
        "headroom",
        "grace",
        "enforced",
    }
    assert body["direction"] == "upgrade"
    assert body["current_tier"] == ent.TIER_OSS
    # OSS -> cloud_starter; headroom present and matches capacity_headroom_at
    assert body["headroom"]["tier"] == ent.TIER_CLOUD_STARTER
    assert body["headroom"] == ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=3
    )


def test_prev_endpoint_envelope_keys(client, ent, monkeypatch):
    # Force cloud_pro so previous exists.
    e_pro = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e_pro)
    rv = client.get("/api/entitlement/previous-tier-capacity-headroom?channels=2")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["direction"] == "downgrade"
    assert body["current_tier"] == ent.TIER_CLOUD_PRO
    assert body["headroom"]["tier"] == ent.TIER_CLOUD_STARTER


def test_next_endpoint_null_at_top_rung(client, ent, monkeypatch):
    e_ent = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e_ent)
    rv = client.get("/api/entitlement/next-tier-capacity-headroom?channels=3")
    # Still HTTP 200 -- callers branch on `headroom is None`, not status code
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["direction"] == "upgrade"
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    assert body["headroom"] is None


def test_prev_endpoint_null_at_bottom_rung(client, ent):
    # OSS-default install has no previous purchasable rung.
    rv = client.get("/api/entitlement/previous-tier-capacity-headroom?channels=3")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["direction"] == "downgrade"
    assert body["current_tier"] == ent.TIER_OSS
    assert body["headroom"] is None


# ── endpoint: query-arg semantics ────────────────────────────────────────────


def test_endpoint_bad_axis_short_circuits_to_none(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-capacity-headroom"
        "?channels=notanint&retention_days=&nodes=-1"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["headroom"] is not None  # tier known -> envelope present
    # every axis discarded -> per-axis rows None
    assert body["headroom"]["channels"] is None
    assert body["headroom"]["retention_days"] is None
    assert body["headroom"]["nodes"] is None


def test_endpoint_no_query_args_is_neutral(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-headroom")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["headroom"]["tier"] == ent.TIER_CLOUD_STARTER
    assert body["headroom"]["channels"] is None
    assert body["headroom"]["retention_days"] is None
    assert body["headroom"]["nodes"] is None


# ── endpoint: never 5xxs ─────────────────────────────────────────────────────


def test_next_endpoint_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def boom(**_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_capacity_headroom", boom)
    rv = client.get("/api/entitlement/next-tier-capacity-headroom?channels=3")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["headroom"] is None
    assert body["direction"] == "upgrade"


def test_prev_endpoint_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def boom(**_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_capacity_headroom", boom)
    rv = client.get("/api/entitlement/previous-tier-capacity-headroom?channels=3")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["headroom"] is None
    assert body["direction"] == "downgrade"
