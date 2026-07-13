"""Tests for the capacity-axis ``tiers_for_*`` helpers and their HTTP
wrappers:

* ``clawmetry.entitlements.tiers_for_channel_count``
* ``clawmetry.entitlements.tiers_for_retention_window``
* ``clawmetry.entitlements.tiers_for_node_count``
* ``GET /api/entitlement/tiers-for-channel-count``
* ``GET /api/entitlement/tiers-for-retention-window``
* ``GET /api/entitlement/tiers-for-node-count``

Inverse siblings of the ``min_tier_for_*`` capacity helpers -- where the
scalar helpers return the *cheapest* purchasable tier admitting a
capacity value (one id the upgrade-CTA renders), these list the **full**
ladder of tiers that admit it. Closes the feature/runtime symmetry gap:
``tiers_for_feature`` and ``tiers_for_runtime`` already exist for the
grant axes but the three capacity axes only exposed the scalar side.

Invariants pinned:

* ``min_tier`` on every row byte-equals the matching scalar
  ``min_tier_for_*`` helper -- keeps the ladder and the scalar in lock
  step
* free tiers appear in the ladder for values that fit under the free
  cap; do NOT appear for values above it
* Enterprise (unlimited on every axis) always appears
* row shape is identical to ``tiers_for_feature`` / ``tiers_for_runtime``
  (``item`` / ``kind`` / ``label`` / ``free`` / ``min_tier`` /
  ``min_tier_label`` / ``min_tier_rank`` / ``tiers``) so a matrix UI can
  render every ``tiers_for_*`` row through one component
* bad input (non-int, empty, ``None`` for non-retention axes) returns
  ``None`` from the helper and ``400`` from the endpoint
* helpers never raise
* endpoints never 5xx
* the live entitlement is not mutated by the helper
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ─────────────────────────────────────────────────────────────────


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


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_channel_count
# ══════════════════════════════════════════════════════════════════════════════


# ── shape ────────────────────────────────────────────────────────────────────


def test_channel_count_returns_full_shape(ent):
    body = ent.tiers_for_channel_count(5)
    assert body is not None
    assert set(body.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "channel_count"
    assert body["item"] == 5


def test_channel_count_row_shape_matches_tiers_for(ent):
    body = ent.tiers_for_channel_count(5)
    assert body["tiers"]
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}
        assert isinstance(row["id"], str) and row["id"]
        assert isinstance(row["label"], str) and row["label"]
        assert isinstance(row["rank"], int)
        assert isinstance(row["purchasable"], bool)


def test_channel_count_tier_rows_sorted_by_rank_then_id(ent):
    body = ent.tiers_for_channel_count(5)
    ranks = [(r["rank"], r["id"]) for r in body["tiers"]]
    assert ranks == sorted(ranks)


def test_channel_count_label_singular_vs_plural(ent):
    assert ent.tiers_for_channel_count(1)["label"] == "1 channel"
    assert ent.tiers_for_channel_count(2)["label"] == "2 channels"
    assert ent.tiers_for_channel_count(0)["label"] == "0 channels"


# ── carriage ─────────────────────────────────────────────────────────────────


def test_channel_count_within_free_cap_includes_oss(ent):
    body = ent.tiers_for_channel_count(ent._FREE_CHANNEL_LIMIT)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS in ids
    assert ent.TIER_CLOUD_FREE in ids
    assert body["free"] is True


def test_channel_count_above_free_cap_excludes_oss(ent):
    body = ent.tiers_for_channel_count(ent._FREE_CHANNEL_LIMIT + 1)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_CLOUD_FREE not in ids
    # unlimited-cap tiers still cover it
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_ENTERPRISE in ids
    assert body["free"] is False


def test_channel_count_zero_admitted_by_every_tier(ent):
    body = ent.tiers_for_channel_count(0)
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)
    assert body["free"] is True


def test_channel_count_negative_admitted_by_every_tier(ent):
    body = ent.tiers_for_channel_count(-3)
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


def test_channel_count_huge_still_admitted_by_unlimited_tiers(ent):
    body = ent.tiers_for_channel_count(10_000_000)
    ids = {row["id"] for row in body["tiers"]}
    # Every unlimited-cap tier must admit any finite count.
    for tier, cap in ent._TIER_CHANNEL_LIMIT.items():
        if cap is None:
            assert tier in ids, tier


# ── min_tier consistency ─────────────────────────────────────────────────────


def test_channel_count_min_tier_matches_scalar_helper(ent):
    for n in (-3, 0, 1, 3, 4, 10, 100, 10_000_000):
        body = ent.tiers_for_channel_count(n)
        assert body is not None, n
        assert body["min_tier"] == ent.min_tier_for_channel_count(n), n


def test_channel_count_min_tier_row_is_purchasable(ent):
    body = ent.tiers_for_channel_count(50)
    assert body["min_tier"] is not None
    by_id = {row["id"]: row for row in body["tiers"]}
    if body["min_tier"] in by_id:
        assert by_id[body["min_tier"]]["purchasable"] is True


def test_channel_count_trial_row_marked_non_purchasable(ent):
    body = ent.tiers_for_channel_count(50)
    by_id = {row["id"]: row for row in body["tiers"]}
    if ent.TIER_TRIAL in by_id:
        assert by_id[ent.TIER_TRIAL]["purchasable"] is False


# ── input handling / safety ──────────────────────────────────────────────────


def test_channel_count_non_int_returns_none(ent):
    assert ent.tiers_for_channel_count("nope") is None  # type: ignore[arg-type]
    assert ent.tiers_for_channel_count(None) is None  # type: ignore[arg-type]
    assert ent.tiers_for_channel_count(object()) is None  # type: ignore[arg-type]


def test_channel_count_string_int_coerces(ent):
    body = ent.tiers_for_channel_count("5")  # type: ignore[arg-type]
    assert body is not None
    assert body["item"] == 5


def test_channel_count_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_tier_row", boom)
    assert ent.tiers_for_channel_count(5) is None


def test_channel_count_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_channel_count(5)
    ent.tiers_for_channel_count(0)
    ent.tiers_for_channel_count(1_000_000)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── API ──────────────────────────────────────────────────────────────────────


def test_channel_count_api_returns_ladder(client, ent):
    rv = client.get("/api/entitlement/tiers-for-channel-count?count=5")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "channel_count"
    assert body["item"] == 5
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_ENTERPRISE in ids
    # resolver envelope
    assert body["current_tier"] == ent.get_entitlement().tier
    assert body["grace"] is True
    assert body["enforced"] is False


def test_channel_count_api_zero_returns_every_tier(client, ent):
    rv = client.get("/api/entitlement/tiers-for-channel-count?count=0")
    assert rv.status_code == 200
    body = rv.get_json()
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


def test_channel_count_api_missing_count_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-channel-count")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_channel_count_api_blank_count_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-channel-count?count=")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_channel_count_api_non_int_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-channel-count?count=nope")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_retention_window
# ══════════════════════════════════════════════════════════════════════════════


def test_retention_returns_full_shape(ent):
    body = ent.tiers_for_retention_window(30)
    assert body is not None
    assert set(body.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "retention_window"
    assert body["item"] == 30


def test_retention_row_shape(ent):
    body = ent.tiers_for_retention_window(30)
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}


def test_retention_label_singular_vs_plural(ent):
    assert ent.tiers_for_retention_window(1)["label"] == "1 day"
    assert ent.tiers_for_retention_window(7)["label"] == "7 days"
    assert ent.tiers_for_retention_window(0)["label"] == "0 days"
    assert ent.tiers_for_retention_window(None)["label"] == "unlimited"


def test_retention_free_flag(ent):
    # OSS retention cap is 7 days.
    assert ent.tiers_for_retention_window(1)["free"] is True
    assert ent.tiers_for_retention_window(7)["free"] is True
    assert ent.tiers_for_retention_window(8)["free"] is False
    assert ent.tiers_for_retention_window(0)["free"] is True
    assert ent.tiers_for_retention_window(None)["free"] is False


def test_retention_within_free_cap_includes_oss(ent):
    body = ent.tiers_for_retention_window(7)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS in ids


def test_retention_above_free_cap_excludes_oss(ent):
    body = ent.tiers_for_retention_window(30)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids


def test_retention_above_starter_cap_excludes_starter(ent):
    # Starter caps at 30 days; 31 requires cloud_pro or above.
    body = ent.tiers_for_retention_window(31)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_CLOUD_STARTER not in ids
    assert ent.TIER_CLOUD_PRO in ids
    assert ent.TIER_ENTERPRISE in ids


def test_retention_unlimited_only_enterprise(ent):
    body = ent.tiers_for_retention_window(None)
    ids = {row["id"] for row in body["tiers"]}
    # Every tier whose cap is None admits unlimited -- currently just Enterprise.
    expected = {
        t for t, cap in ent._TIER_RETENTION_DAYS.items() if cap is None
    }
    assert ids == expected
    assert ent.TIER_ENTERPRISE in ids


def test_retention_min_tier_matches_scalar_helper(ent):
    for d in (-3, 0, 1, 7, 8, 30, 90, 365, None):
        body = ent.tiers_for_retention_window(d)
        assert body is not None, d
        assert body["min_tier"] == ent.min_tier_for_retention_window(d), d


def test_retention_non_int_returns_none(ent):
    assert ent.tiers_for_retention_window("nope") is None  # type: ignore[arg-type]
    assert ent.tiers_for_retention_window(object()) is None  # type: ignore[arg-type]


def test_retention_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_tier_row", boom)
    assert ent.tiers_for_retention_window(30) is None
    assert ent.tiers_for_retention_window(None) is None


def test_retention_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_retention_window(30)
    ent.tiers_for_retention_window(None)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── API ──────────────────────────────────────────────────────────────────────


def test_retention_api_days_returns_ladder(client, ent):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window?days=30"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "retention_window"
    assert body["item"] == 30
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_CLOUD_STARTER in ids


def test_retention_api_unlimited(client, ent):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window?days=unlimited"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["item"] is None
    assert body["label"] == "unlimited"
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_ENTERPRISE in ids


def test_retention_api_unlimited_case_insensitive(client, ent):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window?days=Unlimited"
    )
    assert rv.status_code == 200
    assert rv.get_json()["item"] is None


def test_retention_api_missing_days_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-retention-window")
    assert rv.status_code == 400


def test_retention_api_blank_days_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window?days="
    )
    assert rv.status_code == 400


def test_retention_api_bad_days_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window?days=forever"
    )
    assert rv.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_node_count
# ══════════════════════════════════════════════════════════════════════════════


def test_node_count_returns_full_shape(ent):
    body = ent.tiers_for_node_count(4)
    assert body is not None
    assert set(body.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "node_count"
    assert body["item"] == 4


def test_node_count_row_shape(ent):
    body = ent.tiers_for_node_count(4)
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}


def test_node_count_label_singular_vs_plural(ent):
    assert ent.tiers_for_node_count(1)["label"] == "1 node"
    assert ent.tiers_for_node_count(2)["label"] == "2 nodes"
    assert ent.tiers_for_node_count(0)["label"] == "0 nodes"


def test_node_count_within_free_cap_includes_oss(ent):
    body = ent.tiers_for_node_count(ent._FREE_NODE_LIMIT)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS in ids
    assert body["free"] is True


def test_node_count_above_free_cap_excludes_oss(ent):
    body = ent.tiers_for_node_count(ent._FREE_NODE_LIMIT + 1)
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_ENTERPRISE in ids
    assert body["free"] is False


def test_node_count_zero_admitted_by_every_tier(ent):
    body = ent.tiers_for_node_count(0)
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


def test_node_count_min_tier_matches_scalar_helper(ent):
    for n in (-3, 0, 1, 4, 10, 100, 10_000):
        body = ent.tiers_for_node_count(n)
        assert body is not None, n
        assert body["min_tier"] == ent.min_tier_for_node_count(n), n


def test_node_count_non_int_returns_none(ent):
    assert ent.tiers_for_node_count("nope") is None  # type: ignore[arg-type]
    assert ent.tiers_for_node_count(None) is None  # type: ignore[arg-type]


def test_node_count_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_tier_row", boom)
    assert ent.tiers_for_node_count(4) is None


def test_node_count_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_node_count(4)
    ent.tiers_for_node_count(0)
    ent.tiers_for_node_count(1_000)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── API ──────────────────────────────────────────────────────────────────────


def test_node_count_api_returns_ladder(client, ent):
    rv = client.get("/api/entitlement/tiers-for-node-count?count=4")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "node_count"
    assert body["item"] == 4
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_ENTERPRISE in ids


def test_node_count_api_zero_returns_every_tier(client, ent):
    rv = client.get("/api/entitlement/tiers-for-node-count?count=0")
    assert rv.status_code == 200
    body = rv.get_json()
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


def test_node_count_api_missing_count_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-node-count")
    assert rv.status_code == 400


def test_node_count_api_blank_count_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-node-count?count=")
    assert rv.status_code == 400


def test_node_count_api_non_int_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-node-count?count=nope"
    )
    assert rv.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#   cross-axis symmetry
# ══════════════════════════════════════════════════════════════════════════════


def test_all_three_helpers_share_row_shape(ent):
    """Every capacity ``tiers_for_*`` row must share the ``tiers_for_feature``
    / ``tiers_for_runtime`` row shape so a matrix UI can render every row
    through one component."""
    shape = {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    for body in (
        ent.tiers_for_channel_count(5),
        ent.tiers_for_retention_window(30),
        ent.tiers_for_retention_window(None),
        ent.tiers_for_node_count(4),
        ent.tiers_for_feature("fleet"),
        ent.tiers_for_runtime("claude_code"),
    ):
        assert set(body.keys()) == shape


def test_kinds_match_endpoint_slugs(ent):
    """The ``kind`` field must match the endpoint slug so a client can
    round-trip a row back to the endpoint that produced it."""
    assert ent.tiers_for_channel_count(5)["kind"] == "channel_count"
    assert ent.tiers_for_retention_window(30)["kind"] == "retention_window"
    assert ent.tiers_for_node_count(4)["kind"] == "node_count"


def test_grace_vs_enforce_yields_identical_rows(monkeypatch, ent):
    """Row content is derived from the static tier tables, not the resolver,
    so flipping grace/enforce cannot shift the ladder."""
    a_channel = ent.tiers_for_channel_count(5)
    a_ret = ent.tiers_for_retention_window(30)
    a_node = ent.tiers_for_node_count(4)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    b_channel = ent.tiers_for_channel_count(5)
    b_ret = ent.tiers_for_retention_window(30)
    b_node = ent.tiers_for_node_count(4)
    assert a_channel == b_channel
    assert a_ret == b_ret
    assert a_node == b_node
