"""Tests for the per-value capacity-axis batch helpers and endpoints:

* :func:`clawmetry.entitlements.min_tier_for_channel_count_batch`
* :func:`clawmetry.entitlements.min_tier_for_retention_window_batch`
* :func:`clawmetry.entitlements.min_tier_for_node_count_batch`
* ``GET /api/entitlement/min-tier-for-channel-count-batch?counts=…``
* ``GET /api/entitlement/min-tier-for-retention-window-batch?days=…``
* ``GET /api/entitlement/min-tier-for-node-count-batch?counts=…``

These helpers close the per-value slot on the three scalar capacity
``min_tier_for_*`` axes (channel_count / retention_window / node_count),
alongside the existing per-axis-scalar batch
:func:`clawmetry.entitlements.min_tier_batch` (which folds ONE scalar
per axis into a single row) and the per-bundle grant-axis batches
:func:`clawmetry.entitlements.min_tier_for_features_batch` /
:func:`clawmetry.entitlements.min_tier_for_runtimes_batch`. Neither of
those preserves per-value grouping on a SINGLE capacity axis; that is
the gap this suite pins.

These tests pin:

* Helper: happy path row shape mirrors ``_min_tier_row(n, "<kind>")``
* Helper: per-row parity with the singular ``min_tier_for_*`` helper
  across every value in a representative range on every axis
* Helper: dedup by normalised int key preserving first-seen order
* Helper: bad-input rows collapse to the all-``None`` shape rather
  than raising or dropping
* Helper: ``retention_days`` batch admits ``None`` / case-insensitive
  ``"unlimited"`` as the unlimited sentinel; every other axis rejects
* Helper: empty / None / non-iterable input -> ``[]``
* Helper: grace vs enforce parity (byte-identical rows across modes)
* API: happy path envelope + per-row body byte-identical to the
  singular endpoint minus the resolver envelope
* API: cross-endpoint parity vs ``/min-tier-for-<axis>?<param>=<v>``
  for every value in the batch
* API: 400 on missing / blank query arg
* API: non-int tokens do not fail the batch (per-row all-``None`` row)
* API: unlimited round-trips to ``item=null`` / ``label="unlimited"``
  (retention only, case-insensitive)
* API: resolver envelope carried on happy path
* API: never-5xxs on a delegate crash
* API: uniform envelope keys across the three axes so a pricing UI
  switching axes reads the same shape
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


_ENVELOPE_KEYS = {
    "kind",
    "count",
    "rows",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}


# ── Helper: happy path row shape ──────────────────────────────────────────


def test_helper_channel_count_row_shape(ent):
    rows = ent.min_tier_for_channel_count_batch([1, 5, 25])
    assert len(rows) == 3
    for row in rows:
        assert set(row.keys()) == {
            "key",
            "kind",
            "free",
            "min_tier",
            "min_tier_label",
            "min_tier_rank",
        }
        assert row["kind"] == "channels"


def test_helper_node_count_row_shape(ent):
    rows = ent.min_tier_for_node_count_batch([1, 4])
    for row in rows:
        assert row["kind"] == "nodes"


def test_helper_retention_row_shape(ent):
    rows = ent.min_tier_for_retention_window_batch([7, 30])
    for row in rows:
        assert row["kind"] == "retention_days"


# ── Helper: per-row parity with the singular helper ────────────────────────


@pytest.mark.parametrize("count", [0, 1, 3, 5, 10, 25, 50, 100, 500])
def test_helper_channel_count_parity(ent, count):
    (row,) = ent.min_tier_for_channel_count_batch([count])
    assert row["min_tier"] == ent.min_tier_for_channel_count(count)


@pytest.mark.parametrize("count", [0, 1, 2, 3, 5, 10, 25, 100])
def test_helper_node_count_parity(ent, count):
    (row,) = ent.min_tier_for_node_count_batch([count])
    assert row["min_tier"] == ent.min_tier_for_node_count(count)


@pytest.mark.parametrize("days", [0, 1, 7, 30, 90, 180, 365])
def test_helper_retention_parity(ent, days):
    (row,) = ent.min_tier_for_retention_window_batch([days])
    assert row["min_tier"] == ent.min_tier_for_retention_window(days)


def test_helper_retention_unlimited_none(ent):
    (row,) = ent.min_tier_for_retention_window_batch([None])
    assert row["key"] == "unlimited"
    assert row["min_tier"] == ent.min_tier_for_retention_window(None)


@pytest.mark.parametrize(
    "unlimited_token",
    ["unlimited", "Unlimited", "UNLIMITED", " unlimited "],
)
def test_helper_retention_unlimited_string(ent, unlimited_token):
    (row,) = ent.min_tier_for_retention_window_batch([unlimited_token])
    assert row["key"] == "unlimited"
    assert row["min_tier"] == ent.min_tier_for_retention_window(None)


# ── Helper: dedup preserving first-seen order ──────────────────────────────


def test_helper_channel_count_dedup(ent):
    rows = ent.min_tier_for_channel_count_batch([5, 5, 5, 1, 5])
    assert [r["key"] for r in rows] == ["5", "1"]


def test_helper_node_count_dedup(ent):
    rows = ent.min_tier_for_node_count_batch([4, 1, 4, 4])
    assert [r["key"] for r in rows] == ["4", "1"]


def test_helper_retention_dedup_across_int_and_unlimited(ent):
    rows = ent.min_tier_for_retention_window_batch(
        [30, "unlimited", None, 30, "Unlimited", 7]
    )
    assert [r["key"] for r in rows] == ["30", "unlimited", "7"]


def test_helper_channel_count_dedup_string_int_match(ent):
    """The batch should treat ``"5"`` and ``5`` as the same key."""
    rows = ent.min_tier_for_channel_count_batch([5, "5", 1])
    assert [r["key"] for r in rows] == ["5", "1"]


# ── Helper: bad-input rows collapse ──────────────────────────────────────


def test_helper_channel_count_bad_input_row(ent):
    rows = ent.min_tier_for_channel_count_batch(["bogus"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["min_tier_rank"] == -1
    assert rows[0]["free"] is False


def test_helper_retention_bad_input_row(ent):
    rows = ent.min_tier_for_retention_window_batch(["bogus"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None
    assert rows[0]["key"] == "bogus"


def test_helper_node_count_bad_input_row(ent):
    rows = ent.min_tier_for_node_count_batch(["nope"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None


# ── Helper: retention-only unlimited sentinel ─────────────────────────────


def test_helper_channel_count_none_is_bad_input(ent):
    """channels/nodes axes reject None (no unlimited semantic)."""
    rows = ent.min_tier_for_channel_count_batch([None])
    assert rows[0]["min_tier"] is None


def test_helper_node_count_none_is_bad_input(ent):
    rows = ent.min_tier_for_node_count_batch([None])
    assert rows[0]["min_tier"] is None


# ── Helper: empty / None / non-iterable input ────────────────────────────


def test_helper_channel_count_empty(ent):
    assert ent.min_tier_for_channel_count_batch([]) == []
    assert ent.min_tier_for_channel_count_batch(None) == []


def test_helper_retention_empty(ent):
    assert ent.min_tier_for_retention_window_batch([]) == []
    assert ent.min_tier_for_retention_window_batch(None) == []


def test_helper_node_count_empty(ent):
    assert ent.min_tier_for_node_count_batch([]) == []
    assert ent.min_tier_for_node_count_batch(None) == []


def test_helper_channel_count_non_iterable(ent):
    assert ent.min_tier_for_channel_count_batch(42) == []


def test_helper_retention_non_iterable(ent):
    assert ent.min_tier_for_retention_window_batch(42) == []


def test_helper_node_count_non_iterable(ent):
    assert ent.min_tier_for_node_count_batch(42) == []


# ── Helper: grace vs enforce parity ──────────────────────────────────────


def test_helper_channel_count_grace_enforce_parity(monkeypatch, tmp_path):
    """The helper walks the static per-tier map; grace vs enforce must
    yield byte-identical rows on the same input."""
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()
    grace_rows = e.min_tier_for_channel_count_batch([1, 5, 25])

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_rows = e.min_tier_for_channel_count_batch([1, 5, 25])

    assert grace_rows == enforce_rows


def test_helper_retention_grace_enforce_parity(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()
    grace_rows = e.min_tier_for_retention_window_batch([7, 30, "unlimited"])

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_rows = e.min_tier_for_retention_window_batch([7, 30, "unlimited"])

    assert grace_rows == enforce_rows


# ── API: happy path ──────────────────────────────────────────────────────


def test_api_channel_count_happy(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=1,5,25"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["kind"] == "channel_count"
    assert j["count"] == 3
    for row in j["rows"]:
        assert set(row.keys()) == _ROW_KEYS
        assert row["kind"] == "channel_count"
    assert [r["item"] for r in j["rows"]] == [1, 5, 25]


def test_api_node_count_happy(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-batch?counts=1,4"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["kind"] == "node_count"
    assert [r["item"] for r in j["rows"]] == [1, 4]
    for row in j["rows"]:
        assert row["kind"] == "node_count"


def test_api_retention_window_happy(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=7,30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["kind"] == "retention_window"
    assert [r["item"] for r in j["rows"]] == [7, 30]


def test_api_retention_unlimited(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=7,unlimited"
    )
    assert r.status_code == 200
    j = r.get_json()
    (finite, unlim) = j["rows"]
    assert finite["item"] == 7
    assert unlim["item"] is None
    assert unlim["label"] == "unlimited"


@pytest.mark.parametrize(
    "unlimited_token", ["unlimited", "Unlimited", "UNLIMITED"]
)
def test_api_retention_unlimited_case_insensitive(
    client, ent, unlimited_token
):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch"
        f"?days={unlimited_token}"
    )
    j = r.get_json()
    (row,) = j["rows"]
    assert row["label"] == "unlimited"


# ── API: singular label conjugation ──────────────────────────────────────


def test_api_channel_count_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=1,2"
    ).get_json()
    assert j["rows"][0]["label"] == "1 channel"
    assert j["rows"][1]["label"] == "2 channels"


def test_api_node_count_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-node-count-batch?counts=1,2"
    ).get_json()
    assert j["rows"][0]["label"] == "1 node"
    assert j["rows"][1]["label"] == "2 nodes"


def test_api_retention_window_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=1,2"
    ).get_json()
    assert j["rows"][0]["label"] == "1 day"
    assert j["rows"][1]["label"] == "2 days"


# ── API: cross-endpoint parity with the singular ──────────────────────────


@pytest.mark.parametrize("count", [1, 5, 10, 25])
def test_api_channel_count_parity_with_singular(client, ent, count):
    batch_row = client.get(
        f"/api/entitlement/min-tier-for-channel-count-batch?counts={count}"
    ).get_json()["rows"][0]
    singular = client.get(
        f"/api/entitlement/min-tier-for-channel-count?count={count}"
    ).get_json()
    for k in _ROW_KEYS:
        assert batch_row[k] == singular[k]


@pytest.mark.parametrize("count", [1, 4])
def test_api_node_count_parity_with_singular(client, ent, count):
    batch_row = client.get(
        f"/api/entitlement/min-tier-for-node-count-batch?counts={count}"
    ).get_json()["rows"][0]
    singular = client.get(
        f"/api/entitlement/min-tier-for-node-count?count={count}"
    ).get_json()
    for k in _ROW_KEYS:
        assert batch_row[k] == singular[k]


@pytest.mark.parametrize("days", [1, 7, 30, "unlimited"])
def test_api_retention_parity_with_singular(client, ent, days):
    batch_row = client.get(
        f"/api/entitlement/min-tier-for-retention-window-batch?days={days}"
    ).get_json()["rows"][0]
    singular = client.get(
        f"/api/entitlement/min-tier-for-retention-window?days={days}"
    ).get_json()
    for k in _ROW_KEYS:
        assert batch_row[k] == singular[k]


# ── API: error paths ────────────────────────────────────────────────────


def test_api_channel_count_missing_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch"
    )
    assert r.status_code == 400
    assert "missing counts" in r.get_json()["error"]


def test_api_channel_count_blank_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts="
    )
    assert r.status_code == 400


def test_api_channel_count_only_commas_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=,,,"
    )
    assert r.status_code == 400


def test_api_node_count_missing_400(client):
    assert (
        client.get(
            "/api/entitlement/min-tier-for-node-count-batch"
        ).status_code
        == 400
    )


def test_api_retention_missing_400(client):
    assert (
        client.get(
            "/api/entitlement/min-tier-for-retention-window-batch"
        ).status_code
        == 400
    )


# ── API: non-int tokens don't fail the batch ─────────────────────────────


def test_api_channel_count_bad_token_row(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=5,bogus"
    ).get_json()
    assert j["count"] == 2
    (good, bad) = j["rows"]
    assert good["required_tier"] == ent.min_tier_for_channel_count(5)
    assert bad["required_tier"] is None
    assert bad["required_tier_rank"] == -1


def test_api_retention_bad_token_row(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=7,bogus"
    ).get_json()
    assert j["count"] == 2
    (good, bad) = j["rows"]
    assert good["required_tier"] == ent.min_tier_for_retention_window(7)
    assert bad["required_tier"] is None


# ── API: dedup preserving first-seen order ───────────────────────────────


def test_api_channel_count_dedup(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=5,5,1,5"
    ).get_json()
    assert [r["item"] for r in j["rows"]] == [5, 1]


def test_api_retention_dedup(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=30,unlimited,30,Unlimited,7"
    ).get_json()
    assert [r["label"] for r in j["rows"]] == ["30 days", "unlimited", "7 days"]


# ── API: resolver envelope carried on happy path ─────────────────────────


def test_api_envelope_carries_resolver(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=1"
    ).get_json()
    assert j["current_tier"] == ent.get_entitlement().tier
    assert j["current_tier_rank"] == ent.tier_rank(j["current_tier"])
    assert isinstance(j["grace"], bool)
    assert isinstance(j["enforced"], bool)


# ── API: uniform envelope keys across the three axes ─────────────────────


def test_api_uniform_envelope_across_axes(client):
    ch = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=1"
    ).get_json()
    nd = client.get(
        "/api/entitlement/min-tier-for-node-count-batch?counts=1"
    ).get_json()
    rt = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=1"
    ).get_json()
    assert set(ch.keys()) == set(nd.keys()) == set(rt.keys()) == _ENVELOPE_KEYS


def test_api_uniform_row_keys_across_axes(client):
    ch = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=1"
    ).get_json()["rows"][0]
    nd = client.get(
        "/api/entitlement/min-tier-for-node-count-batch?counts=1"
    ).get_json()["rows"][0]
    rt = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=1"
    ).get_json()["rows"][0]
    assert set(ch.keys()) == set(nd.keys()) == set(rt.keys()) == _ROW_KEYS


# ── API: never-5xxs on a delegate crash ─────────────────────────────────


def test_api_channel_count_never_5xxs(monkeypatch, client, ent):
    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_channel_count_batch", boom)
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-batch?counts=5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["kind"] == "channel_count"
    assert j["rows"] == []
    assert j["grace"] is True


def test_api_retention_never_5xxs(monkeypatch, client, ent):
    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_retention_window_batch", boom)
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-batch?days=30"
    )
    assert r.status_code == 200
    assert r.get_json()["kind"] == "retention_window"


def test_api_node_count_never_5xxs(monkeypatch, client, ent):
    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_node_count_batch", boom)
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-batch?counts=1"
    )
    assert r.status_code == 200
    assert r.get_json()["kind"] == "node_count"
