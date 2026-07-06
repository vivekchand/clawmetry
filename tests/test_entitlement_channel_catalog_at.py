"""Tests for ``channel_catalog_at(tier)`` /
``channel_catalog_at_batch(tiers)`` plus their HTTP endpoints.

What-if siblings of :func:`channel_catalog` for the chat-channel axis.
Every chat channel is FREE -- there is no paid-channel tier, so every
row comes back unlocked regardless of the perspective tier. That parity
IS the answer a pricing-comparison matrix UI needs: "all N chat channels
included at every plan", rendered off ONE row-renderer shared with the
feature / runtime what-if catalog endpoints.

Coverage:

* row shape / ordering / labels match :func:`channel_catalog` exactly
* every row is unlocked at every tier in ``_TIER_ORDER`` (the always-free
  posture)
* rows across tiers are byte-identical (nothing depends on the
  perspective tier)
* helpers are independent of the live resolver (grace toggle / cached
  cloud plan do not affect the what-if rows)
* unknown / empty / ``None`` / non-string tier ids return ``None``
* the scalar endpoint 400s on missing input, 404s on unknown ids, never
  5xxs on resolver crashes
* the batch endpoint 400s on empty input, echoes unknown ids at 200, and
  carries the standard envelope
* scalar and batch stay in byte-parity (pinned)
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default; the helpers still synthesise a non-grace
    hypothetical entitlement per requested tier."""
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


_ROW_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}
_TIER_ROW_KEYS = {"tier", "tier_label", "tier_rank"}
_ENVELOPE_KEYS = {
    "tiers",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── channel_catalog_at helper: shape + parity ────────────────────────────────


def test_row_shape_matches_channel_catalog(ent):
    cat_keys = set(ent.channel_catalog()[0].keys())
    rows = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None and len(rows) > 0
    assert set(rows[0].keys()) == cat_keys == _ROW_KEYS


def test_row_ordering_matches_channel_catalog(ent):
    cat_ids = [row["id"] for row in ent.channel_catalog()]
    at_ids = [row["id"] for row in ent.channel_catalog_at(ent.TIER_OSS)]
    assert cat_ids == at_ids


def test_row_ids_match_all_channels(ent):
    ids = {row["id"] for row in ent.channel_catalog_at(ent.TIER_CLOUD_PRO)}
    assert ids == set(ent.ALL_CHANNELS)


def test_row_count_matches_all_channels(ent):
    rows = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert len(rows) == len(ent.ALL_CHANNELS)


def test_labels_come_from_channel_label_helper(ent):
    for row in ent.channel_catalog_at(ent.TIER_CLOUD_PRO):
        assert row["label"] == ent.channel_label(row["id"])


# ── channel_catalog_at helper: always-free posture ───────────────────────────


def test_every_row_is_free_at_every_tier(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.channel_catalog_at(tier)
        assert rows is not None, tier
        for row in rows:
            assert row["free"] is True, (tier, row["id"])
            assert row["tier"] == "free", (tier, row["id"])
            assert row["allowed"] is True, (tier, row["id"])
            assert row["locked"] is False, (tier, row["id"])
            assert row["entitled"] is True, (tier, row["id"])


def test_rows_are_byte_identical_across_tiers(ent):
    """The perspective tier does not affect any per-row field, so every
    tier's rows must be byte-identical to every other tier's rows -- the
    parity IS the answer a pricing UI renders off this endpoint."""
    baseline = ent.channel_catalog_at(ent.TIER_OSS)
    for tier in ent._TIER_ORDER:
        rows = ent.channel_catalog_at(tier)
        assert rows == baseline, tier


def test_rows_are_byte_identical_to_bare_channel_catalog(ent):
    """The bare :func:`channel_catalog` and the what-if
    :func:`channel_catalog_at` are equivalent by construction; pin it so
    a future refactor cannot let them drift."""
    for tier in ent._TIER_ORDER:
        assert ent.channel_catalog_at(tier) == ent.channel_catalog(), tier


# ── channel_catalog_at helper: round-trip ────────────────────────────────────


def test_every_tier_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.channel_catalog_at(tier)
        assert rows is not None, tier
        assert len(rows) == len(ent.ALL_CHANNELS)


def test_unknown_tier_returns_none(ent):
    assert ent.channel_catalog_at("not_a_real_tier") is None


def test_empty_returns_none(ent):
    assert ent.channel_catalog_at("") is None


def test_none_returns_none(ent):
    assert ent.channel_catalog_at(None) is None


def test_non_string_returns_none(ent):
    assert ent.channel_catalog_at(123) is None
    assert ent.channel_catalog_at(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    a = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    b = ent.channel_catalog_at(ent.TIER_CLOUD_PRO.upper())
    c = ent.channel_catalog_at(f"  {ent.TIER_CLOUD_PRO}  ")
    assert a == b == c


# ── channel_catalog_at helper: independent of live resolver ──────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert grace == enforced


# ── channel_catalog_at helper: never-raise ───────────────────────────────────


def test_never_raises_when_hypothetical_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated synthesis failure")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", boom)
    rows = ent.channel_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert len(rows) == len(ent.ALL_CHANNELS)


# ── channel_catalog_at_batch helper: input handling ──────────────────────────


def test_batch_empty_input_returns_empty_envelope(ent):
    assert ent.channel_catalog_at_batch([]) == {"tiers": [], "unknown": []}


def test_batch_none_input_returns_empty_envelope(ent):
    assert ent.channel_catalog_at_batch(None) == {"tiers": [], "unknown": []}


def test_batch_string_csv_input(ent):
    body = ent.channel_catalog_at_batch(
        f"{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_batch_supply_order_preserved(ent):
    body = ent.channel_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]


def test_batch_whitespace_and_case_normalised(ent):
    body = ent.channel_catalog_at_batch(
        ["  CLOUD_PRO  ", ent.TIER_CLOUD_STARTER.upper()]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.channel_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_OSS]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
    ]


def test_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.channel_catalog_at_batch(
        [ent.TIER_CLOUD_PRO, "nope_tier", "also_bogus"]
    )
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_batch_unknown_only_returns_empty_tiers(ent):
    body = ent.channel_catalog_at_batch(["nope_tier", "also_bogus"])
    assert body == {"tiers": [], "unknown": ["nope_tier", "also_bogus"]}


def test_batch_non_iterable_input_falls_back_to_empty(ent):
    assert ent.channel_catalog_at_batch(12345) == {"tiers": [], "unknown": []}
    assert ent.channel_catalog_at_batch(object()) == {"tiers": [], "unknown": []}


# ── channel_catalog_at_batch helper: shape + parity ──────────────────────────


def test_batch_row_shape_carries_tier_metadata(ent):
    body = ent.channel_catalog_at_batch([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert _TIER_ROW_KEYS.issubset(set(row.keys()))
    assert "channels" in row
    assert set(row["channels"][0].keys()) == _ROW_KEYS


def test_batch_tier_metadata_matches_scalar(ent):
    body = ent.channel_catalog_at_batch([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert row["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_batch_channels_list_matches_scalar_exactly(ent):
    """Pin scalar / batch no-drift: every batch tier's ``channels`` list
    equals the scalar ``channel_catalog_at`` list for the same tier."""
    body = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["channels"] == ent.channel_catalog_at(tid), tid


def test_batch_every_tier_in_order_resolves(ent):
    body = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []
    for row in body["tiers"]:
        assert len(row["channels"]) == len(ent.ALL_CHANNELS)


# ── channel_catalog_at_batch helper: perspective invariance ──────────────────


def test_batch_channels_are_identical_across_tiers(ent):
    """Every chat channel is free, so batching across the perspective-
    tier axis returns identical ``channels`` lists per tier."""
    body = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    lists = [row["channels"] for row in body["tiers"]]
    assert all(lst == lists[0] for lst in lists)


def test_batch_every_row_is_free_at_every_tier(ent):
    body = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        for ch in row["channels"]:
            assert ch["free"] is True, (row["tier"], ch["id"])
            assert ch["allowed"] is True, (row["tier"], ch["id"])
            assert ch["locked"] is False, (row["tier"], ch["id"])
            assert ch["entitled"] is True, (row["tier"], ch["id"])


# ── channel_catalog_at_batch helper: never-raise / resolver-independent ──────


def test_batch_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    """A per-tier scalar helper crash must short-circuit that id into
    ``unknown[]`` and the rest of the batch keeps building -- matches
    every other ``_at_batch`` sibling's posture."""
    real = ent.channel_catalog_at

    def flaky(t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "channel_catalog_at", flaky)
    body = ent.channel_catalog_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


def test_batch_grace_vs_enforce_byte_identical(ent, monkeypatch):
    """Enforcement is a live-resolver knob; the batch what-if helper
    builds a fresh hypothetical Entitlement per tier and must be
    independent."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.channel_catalog_at_batch(list(ent._TIER_ORDER))
    assert grace == enforced


# ── HTTP endpoint: /api/entitlement/channel-catalog-at ───────────────────────


def test_endpoint_known_tier_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["channels"] == ent.channel_catalog_at(ent.TIER_CLOUD_PRO)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-catalog-at")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-catalog-at?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get("/api/entitlement/channel-catalog-at?tier=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_tier_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/channel-catalog-at?tier={tier}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert len(body["channels"]) == len(ent.ALL_CHANNELS), tier


def test_endpoint_channels_match_bare_channel_catalog(client, ent):
    """Every ``-at`` variant is byte-parity with the bare
    :func:`channel_catalog` -- the channel axis has no paid-channel
    tier, so the perspective tier does not change any row field."""
    for tier in ent._TIER_ORDER:
        body = client.get(
            f"/api/entitlement/channel-catalog-at?tier={tier}"
        ).get_json()
        assert body["channels"] == ent.channel_catalog(), tier


# ── HTTP endpoint: /api/entitlement/channel-catalog-at-batch ─────────────────


def test_endpoint_batch_known_tiers_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS.issubset(set(body.keys()))
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    for row in body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/channel-catalog-at?tier={row['tier']}"
        ).get_json()
        assert row["channels"] == scalar["channels"], row["tier"]


def test_endpoint_batch_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/channel-catalog-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_batch_blank_arg_returns_400(client):
    resp = client.get(
        "/api/entitlement/channel-catalog-at-batch?tiers=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_batch_unknown_ids_echoed_at_200(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch"
        f"?tiers={ent.TIER_CLOUD_PRO},nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_endpoint_batch_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch"
        f"?tiers=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]


def test_endpoint_batch_every_tier_in_order_round_trips(client, ent):
    tiers = ",".join(ent._TIER_ORDER)
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch?tiers={tiers}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


def test_endpoint_batch_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_batch_envelope_carries_current_tier_and_grace_flags(client, ent):
    resp = client.get(
        f"/api/entitlement/channel-catalog-at-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


def test_endpoint_scalar_never_5xx_on_helper_crash(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper crash")

    monkeypatch.setattr(ent, "channel_catalog_at", boom)
    resp = client.get(
        f"/api/entitlement/channel-catalog-at?tier={ent.TIER_CLOUD_PRO}"
    )
    # Scalar endpoint surfaces the crash as a 500 with an ``error`` body;
    # the never-5xx guarantee for the axis lives on the -batch envelope.
    assert resp.status_code == 500
    assert "error" in resp.get_json()
