"""Tests for the per-value ``/api/entitlement/tiers-for-channel-count-batch``
/ ``/api/entitlement/tiers-for-node-count-batch`` /
``/api/entitlement/tiers-for-retention-window-batch`` endpoints and the
underlying :func:`tiers_for_channel_count_batch` /
:func:`tiers_for_node_count_batch` /
:func:`tiers_for_retention_window_batch` helpers.

Closes the per-value slot on the three scalar capacity axes in the
``tiers_for_*`` family. Where :func:`tiers_for_capacity_batch` folds ONE
scalar per axis (three per-axis rows) and :func:`tiers_for_features` /
:func:`tiers_for_runtimes` fold N grant-axis bundles to N ladder answers,
this per-value batch preserves per-value grouping on a SINGLE capacity
axis so a pricing-matrix walkthrough comparing several hypothetical
channel / node / retention-window values renders every column off one
round-trip.

Mirrors the shape ``/api/entitlement/min-tier-for-<axis>-batch`` (PR
#3946) landed for the ``min_tier_for_*`` family.

Distinct from :mod:`tests.test_entitlement_tiers_for_capacity_batch`,
which covers the *per-axis* :func:`tiers_for_capacity_batch` (one scalar
per axis, three per-axis rows).
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


_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}

_ENVELOPE_KEYS = {
    "kind",
    "count",
    "rows",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── Helper: row shape mirrors singular tiers_for_* helper ─────────────────

def test_helper_channel_count_row_shape_mirrors_singular(ent):
    rows = ent.tiers_for_channel_count_batch([1, 5, 25])
    assert len(rows) == 3
    for row, n in zip(rows, [1, 5, 25]):
        assert set(row.keys()) == _ROW_KEYS
        singular = ent.tiers_for_channel_count(n)
        assert row == singular


def test_helper_node_count_row_shape_mirrors_singular(ent):
    rows = ent.tiers_for_node_count_batch([1, 3, 5])
    assert len(rows) == 3
    for row, n in zip(rows, [1, 3, 5]):
        assert set(row.keys()) == _ROW_KEYS
        singular = ent.tiers_for_node_count(n)
        assert row == singular


def test_helper_retention_window_row_shape_mirrors_singular(ent):
    rows = ent.tiers_for_retention_window_batch([7, 30, 365])
    assert len(rows) == 3
    for row, n in zip(rows, [7, 30, 365]):
        assert set(row.keys()) == _ROW_KEYS
        singular = ent.tiers_for_retention_window(n)
        assert row == singular


# ── Helper: retention admits None / "unlimited" sentinel ──────────────────

def test_helper_retention_admits_none_as_unlimited(ent):
    rows = ent.tiers_for_retention_window_batch([None])
    assert len(rows) == 1
    assert rows[0]["item"] is None
    assert rows[0]["label"] == "unlimited"
    assert rows[0] == ent.tiers_for_retention_window(None)


def test_helper_retention_admits_string_unlimited(ent):
    rows = ent.tiers_for_retention_window_batch(["unlimited"])
    assert len(rows) == 1
    assert rows[0]["item"] is None
    assert rows[0]["label"] == "unlimited"


def test_helper_retention_admits_unlimited_case_insensitive(ent):
    for spelling in ["UNLIMITED", "Unlimited", "  UnLiMiTeD  "]:
        rows = ent.tiers_for_retention_window_batch([spelling])
        assert len(rows) == 1, spelling
        assert rows[0]["item"] is None
        assert rows[0]["label"] == "unlimited"


def test_helper_retention_none_and_unlimited_dedup_together(ent):
    # Both surface as key "unlimited" so only the first survives.
    rows = ent.tiers_for_retention_window_batch(
        [None, "unlimited", "UNLIMITED"]
    )
    assert len(rows) == 1


def test_helper_channel_count_rejects_none(ent):
    rows = ent.tiers_for_channel_count_batch([None])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


def test_helper_node_count_rejects_none(ent):
    rows = ent.tiers_for_node_count_batch([None])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


# ── Helper: dedup by normalised int key preserving first-seen order ───────

def test_helper_channel_count_dedup_int_repeats(ent):
    rows = ent.tiers_for_channel_count_batch([5, 5, 5, 10, 5])
    assert [r["item"] for r in rows] == [5, 10]


def test_helper_node_count_dedup_int_repeats(ent):
    rows = ent.tiers_for_node_count_batch([3, 3, 5, 5, 3])
    assert [r["item"] for r in rows] == [3, 5]


def test_helper_channel_count_dedup_cross_type_string_int(ent):
    # "5" and 5 normalise to the same int key.
    rows = ent.tiers_for_channel_count_batch(["5", 5])
    assert len(rows) == 1
    assert rows[0]["item"] == 5


def test_helper_node_count_dedup_cross_type_string_int(ent):
    rows = ent.tiers_for_node_count_batch([3, "3"])
    assert len(rows) == 1


def test_helper_retention_dedup_cross_type_string_int(ent):
    rows = ent.tiers_for_retention_window_batch([30, "30"])
    assert len(rows) == 1


def test_helper_channel_count_preserves_first_seen_order(ent):
    rows = ent.tiers_for_channel_count_batch([25, 1, 10, 5])
    assert [r["item"] for r in rows] == [25, 1, 10, 5]


def test_helper_retention_preserves_first_seen_order(ent):
    rows = ent.tiers_for_retention_window_batch([365, "unlimited", 30, 7])
    assert [r["item"] for r in rows] == [365, None, 30, 7]
    assert rows[1]["label"] == "unlimited"


# ── Helper: bad-input row collapses to all-None shape ─────────────────────

def test_helper_channel_count_non_int_collapses_to_null_row(ent):
    rows = ent.tiers_for_channel_count_batch(["bogus"])
    assert len(rows) == 1
    r = rows[0]
    assert set(r.keys()) == _ROW_KEYS
    assert r["item"] == "bogus"
    assert r["min_tier"] is None
    assert r["min_tier_label"] is None
    assert r["min_tier_rank"] is None
    assert r["label"] is None
    assert r["free"] is False
    assert r["tiers"] == []


def test_helper_node_count_non_int_collapses_to_null_row(ent):
    rows = ent.tiers_for_node_count_batch(["nope"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


def test_helper_retention_non_int_non_unlimited_collapses_to_null_row(ent):
    rows = ent.tiers_for_retention_window_batch(["gibberish"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["tiers"] == []


def test_helper_bad_input_does_not_fail_batch(ent):
    # bogus + real value in same call — real value still resolves.
    rows = ent.tiers_for_channel_count_batch(["bogus", 5])
    assert len(rows) == 2
    assert rows[0]["min_tier"] is None
    assert rows[1]["item"] == 5
    assert rows[1]["min_tier"] == ent.min_tier_for_channel_count(5)


# ── Helper: empty / None / non-iterable input ─────────────────────────────

def test_helper_channel_count_none_input_returns_empty(ent):
    assert ent.tiers_for_channel_count_batch(None) == []


def test_helper_node_count_none_input_returns_empty(ent):
    assert ent.tiers_for_node_count_batch(None) == []


def test_helper_retention_none_input_returns_empty(ent):
    # NOTE: None-as-input (missing) is [], distinct from [None] which
    # asks for the unlimited-history row.
    assert ent.tiers_for_retention_window_batch(None) == []


def test_helper_channel_count_empty_list_returns_empty(ent):
    assert ent.tiers_for_channel_count_batch([]) == []


def test_helper_retention_empty_list_returns_empty(ent):
    assert ent.tiers_for_retention_window_batch([]) == []


def test_helper_channel_count_non_iterable_returns_empty(ent):
    assert ent.tiers_for_channel_count_batch(42) == []
    assert ent.tiers_for_channel_count_batch(3.14) == []


# ── Helper: grace vs enforce parity ───────────────────────────────────────

def test_helper_grace_enforce_parity_channel_count(ent, monkeypatch):
    baseline = ent.tiers_for_channel_count_batch([1, 5, 10, 25])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforced = ent.tiers_for_channel_count_batch([1, 5, 10, 25])
    assert baseline == enforced


def test_helper_grace_enforce_parity_node_count(ent, monkeypatch):
    baseline = ent.tiers_for_node_count_batch([1, 3, 5])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforced = ent.tiers_for_node_count_batch([1, 3, 5])
    assert baseline == enforced


def test_helper_grace_enforce_parity_retention(ent, monkeypatch):
    baseline = ent.tiers_for_retention_window_batch([7, 30, "unlimited"])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforced = ent.tiers_for_retention_window_batch([7, 30, "unlimited"])
    assert baseline == enforced


# ── API: happy path + envelope + row shape ────────────────────────────────

def test_api_channel_count_batch_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=1,5,25"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["kind"] == "channel_count"
    assert j["count"] == 3
    assert len(j["rows"]) == 3
    for row, n in zip(j["rows"], [1, 5, 25]):
        assert set(row.keys()) == _ROW_KEYS
        assert row["item"] == n
        assert row["kind"] == "channel_count"


def test_api_node_count_batch_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=1,3,5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["kind"] == "node_count"
    assert j["count"] == 3
    for row, n in zip(j["rows"], [1, 3, 5]):
        assert row["item"] == n
        assert row["kind"] == "node_count"


def test_api_retention_window_batch_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=7,30,365"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["kind"] == "retention_window"
    assert j["count"] == 3
    for row, n in zip(j["rows"], [7, 30, 365]):
        assert row["item"] == n
        assert row["kind"] == "retention_window"


# ── API: cross-endpoint parity vs singular ─────────────────────────────────

_ENV_KEYS = {"current_tier", "current_tier_rank", "grace", "enforced"}


def _strip_env(body: dict) -> dict:
    return {k: v for k, v in body.items() if k not in _ENV_KEYS}


def test_api_channel_count_parity_vs_singular(client, ent):
    j = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=1,5,10,25"
    ).get_json()
    for n, row in zip([1, 5, 10, 25], j["rows"]):
        singular = client.get(
            f"/api/entitlement/tiers-for-channel-count?count={n}"
        ).get_json()
        assert row == _strip_env(singular)


def test_api_node_count_parity_vs_singular(client, ent):
    j = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=1,3,5"
    ).get_json()
    for n, row in zip([1, 3, 5], j["rows"]):
        singular = client.get(
            f"/api/entitlement/tiers-for-node-count?count={n}"
        ).get_json()
        assert row == _strip_env(singular)


def test_api_retention_parity_vs_singular(client, ent):
    j = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=7,30"
    ).get_json()
    for n, row in zip([7, 30], j["rows"]):
        singular = client.get(
            f"/api/entitlement/tiers-for-retention-window?days={n}"
        ).get_json()
        assert row == _strip_env(singular)


def test_api_retention_unlimited_parity_vs_singular(client, ent):
    j = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=unlimited"
    ).get_json()
    singular = client.get(
        "/api/entitlement/tiers-for-retention-window?days=unlimited"
    ).get_json()
    assert j["rows"] == [_strip_env(singular)]
    assert j["rows"][0]["item"] is None
    assert j["rows"][0]["label"] == "unlimited"


# ── API: 400 on missing / blank / only-commas ─────────────────────────────

def test_api_channel_count_missing_arg_returns_400(client):
    r = client.get("/api/entitlement/tiers-for-channel-count-batch")
    assert r.status_code == 400
    assert "missing counts" in r.get_json()["error"]


def test_api_node_count_missing_arg_returns_400(client):
    r = client.get("/api/entitlement/tiers-for-node-count-batch")
    assert r.status_code == 400


def test_api_retention_missing_arg_returns_400(client):
    r = client.get("/api/entitlement/tiers-for-retention-window-batch")
    assert r.status_code == 400
    assert "missing days" in r.get_json()["error"]


def test_api_channel_count_blank_arg_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts="
    )
    assert r.status_code == 400


def test_api_retention_blank_arg_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days="
    )
    assert r.status_code == 400


def test_api_channel_count_only_commas_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=,,,,"
    )
    assert r.status_code == 400


def test_api_retention_only_commas_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=,,,"
    )
    assert r.status_code == 400


# ── API: non-int tokens surface as all-None rows without failing batch ────

def test_api_channel_count_non_int_row_collapses_to_null(client):
    r = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=bogus,5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 2
    assert j["rows"][0]["min_tier"] is None
    assert j["rows"][0]["tiers"] == []
    assert j["rows"][1]["item"] == 5
    assert j["rows"][1]["min_tier"] is not None


def test_api_node_count_non_int_row_collapses_to_null(client):
    r = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=nope,3"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 2
    assert j["rows"][0]["min_tier"] is None
    assert j["rows"][1]["item"] == 3


def test_api_retention_non_int_non_unlimited_row_collapses_to_null(client):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch"
        "?days=gibberish,30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 2
    assert j["rows"][0]["min_tier"] is None
    assert j["rows"][1]["item"] == 30


# ── API: retention unlimited round-trip (case-insensitive) ────────────────

def test_api_retention_unlimited_case_insensitive(client):
    for spelling in ["unlimited", "UNLIMITED", "Unlimited"]:
        r = client.get(
            "/api/entitlement/tiers-for-retention-window-batch"
            f"?days={spelling}"
        )
        assert r.status_code == 200, spelling
        j = r.get_json()
        assert len(j["rows"]) == 1
        assert j["rows"][0]["item"] is None
        assert j["rows"][0]["label"] == "unlimited"


def test_api_retention_unlimited_mixed_with_ints(client):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch"
        "?days=7,unlimited,30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert [row["item"] for row in j["rows"]] == [7, None, 30]
    assert j["rows"][1]["label"] == "unlimited"


# ── API: resolver envelope carried on happy path ──────────────────────────

def test_api_resolver_envelope_channel_count(client):
    j = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=1"
    ).get_json()
    assert "current_tier" in j
    assert "current_tier_rank" in j
    assert "grace" in j
    assert "enforced" in j
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_resolver_envelope_node_count(client):
    j = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=1"
    ).get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_resolver_envelope_retention(client):
    j = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=7"
    ).get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


# ── API: uniform envelope + row keys across the three axes ────────────────

def test_api_uniform_envelope_keys_across_axes(client):
    channel = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=5"
    ).get_json()
    node = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=3"
    ).get_json()
    retention = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=30"
    ).get_json()
    assert set(channel.keys()) == set(node.keys()) == set(retention.keys())
    assert set(channel.keys()) == _ENVELOPE_KEYS


def test_api_uniform_row_keys_across_axes(client):
    channel = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=5"
    ).get_json()["rows"][0]
    node = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=3"
    ).get_json()["rows"][0]
    retention = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=30"
    ).get_json()["rows"][0]
    assert set(channel.keys()) == set(node.keys()) == set(retention.keys())
    assert set(channel.keys()) == _ROW_KEYS


# ── API: never-5xxs on a delegate crash ───────────────────────────────────

def test_api_channel_count_never_5xxs_on_delegate_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def _boom(_x):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(_ent, "tiers_for_channel_count_batch", _boom)
    r = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=1"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["kind"] == "channel_count"
    assert j["rows"] == []
    assert j["count"] == 0
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_node_count_never_5xxs_on_delegate_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def _boom(_x):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(_ent, "tiers_for_node_count_batch", _boom)
    r = client.get(
        "/api/entitlement/tiers-for-node-count-batch?counts=1"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["rows"] == []
    assert j["kind"] == "node_count"


def test_api_retention_never_5xxs_on_delegate_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def _boom(_x):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(_ent, "tiers_for_retention_window_batch", _boom)
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-batch?days=7"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["rows"] == []
    assert j["kind"] == "retention_window"


# ── API: dedup happens through the query-string parser too ────────────────

def test_api_channel_count_dedups_repeated_tokens(client):
    j = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=5,5,5,10,5"
    ).get_json()
    assert [r["item"] for r in j["rows"]] == [5, 10]


def test_api_retention_dedups_unlimited_repeats(client):
    j = client.get(
        "/api/entitlement/tiers-for-retention-window-batch"
        "?days=unlimited,unlimited,UNLIMITED"
    ).get_json()
    assert [r["item"] for r in j["rows"]] == [None]


def test_api_channel_count_skips_blank_tokens(client):
    j = client.get(
        "/api/entitlement/tiers-for-channel-count-batch?counts=5,,10,,,25"
    ).get_json()
    assert [r["item"] for r in j["rows"]] == [5, 10, 25]
