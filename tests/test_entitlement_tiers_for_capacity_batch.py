"""Tests for ``clawmetry.entitlements.tiers_for_capacity_batch`` +
``GET /api/entitlement/tiers-for-capacity-batch``.

Per-item plural sibling of ``tiers_for_channel_count`` /
``tiers_for_retention_window`` / ``tiers_for_node_count`` for the three
capacity axes. Closes the symmetry gap in the ``tiers_for_*`` family:
``tiers_for_batch`` covers only features + runtimes (the grant axes) and
doesn't accept capacity args at all -- so a pricing-page that wants the
full "Fits in: <tier>, ..." ladder for a caller-supplied ``(channels,
retention_days, nodes)`` capacity bundle either had to fan out three
``/tiers-for-<axis>`` calls or build the ladder client-side from
``/min-tier-batch``. These tests pin the contract:

  - envelope shape mirrors ``min_tier_batch`` on the three capacity axes
    exactly (per-axis ``None`` "not supplied" sentinel, same never-raise
    contract)
  - each row byte-equals the matching singular ``tiers_for_<axis>``
    helper -- the batch cannot silently drift from the scalars
  - ``retention_days=None`` means unset, NOT unlimited (matches
    ``min_tier_batch`` on the same axis)
  - grace vs enforce yields byte-identical rows
  - the wrapper endpoint 400s only when *no* axis parsed successfully;
    blank/non-int values on individual axes are treated as unsupplied
  - never 5xxs on the wrapper endpoint
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
#   helper: shape
# ══════════════════════════════════════════════════════════════════════════════


def test_returns_three_axis_envelope(ent):
    body = ent.tiers_for_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    assert isinstance(body, dict)
    assert set(body.keys()) == {"channels", "retention_days", "nodes"}


def test_returns_all_none_when_nothing_supplied(ent):
    body = ent.tiers_for_capacity_batch()
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_omitted_axis_is_none(ent):
    body = ent.tiers_for_capacity_batch(channels=5)
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_channels_row_has_singular_shape(ent):
    body = ent.tiers_for_capacity_batch(channels=5)
    row = body["channels"]
    assert set(row.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert row["kind"] == "channel_count"
    assert row["item"] == 5


def test_retention_row_has_singular_shape(ent):
    body = ent.tiers_for_capacity_batch(retention_days=30)
    row = body["retention_days"]
    assert set(row.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert row["kind"] == "retention_window"
    assert row["item"] == 30


def test_nodes_row_has_singular_shape(ent):
    body = ent.tiers_for_capacity_batch(nodes=3)
    row = body["nodes"]
    assert set(row.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert row["kind"] == "node_count"
    assert row["item"] == 3


def test_tier_rows_have_expected_keys(ent):
    body = ent.tiers_for_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    for axis in ("channels", "retention_days", "nodes"):
        for tier_row in body[axis]["tiers"]:
            assert set(tier_row.keys()) == {
                "id",
                "label",
                "rank",
                "purchasable",
            }


# ══════════════════════════════════════════════════════════════════════════════
#   helper: parity with singular helpers
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("count", [0, 1, 3, 5, 10, 100])
def test_channels_row_equals_singular_helper(ent, count):
    body = ent.tiers_for_capacity_batch(channels=count)
    assert body["channels"] == ent.tiers_for_channel_count(count)


@pytest.mark.parametrize("days", [0, 1, 7, 30, 90, 365])
def test_retention_row_equals_singular_helper(ent, days):
    body = ent.tiers_for_capacity_batch(retention_days=days)
    assert body["retention_days"] == ent.tiers_for_retention_window(days)


@pytest.mark.parametrize("count", [0, 1, 2, 3, 10, 100])
def test_nodes_row_equals_singular_helper(ent, count):
    body = ent.tiers_for_capacity_batch(nodes=count)
    assert body["nodes"] == ent.tiers_for_node_count(count)


# ══════════════════════════════════════════════════════════════════════════════
#   helper: retention_days=None means UNSET (not unlimited)
# ══════════════════════════════════════════════════════════════════════════════


def test_retention_none_means_unset_not_unlimited(ent):
    """``retention_days=None`` means the axis was not supplied. Distinct
    from the singular ``tiers_for_retention_window(None)`` semantics
    where ``None`` means the unlimited-retention request -- mirrors
    ``min_tier_batch`` / ``lock_reasons_batch`` on the same axis so a
    caller supplying every other axis but leaving retention off does not
    get a mis-routed Enterprise row."""
    body = ent.tiers_for_capacity_batch(channels=5, nodes=3)
    assert body["retention_days"] is None
    # sanity: the singular helper would have returned an Enterprise row
    unlimited = ent.tiers_for_retention_window(None)
    assert unlimited is not None
    assert unlimited["label"] == "unlimited"


# ══════════════════════════════════════════════════════════════════════════════
#   helper: bad input
# ══════════════════════════════════════════════════════════════════════════════


def test_channels_non_int_row_is_none(ent):
    body = ent.tiers_for_capacity_batch(channels="not-a-number")
    assert body["channels"] is None


def test_retention_non_int_row_is_none(ent):
    body = ent.tiers_for_capacity_batch(retention_days="foo")
    assert body["retention_days"] is None


def test_nodes_non_int_row_is_none(ent):
    body = ent.tiers_for_capacity_batch(nodes="bar")
    assert body["nodes"] is None


# ══════════════════════════════════════════════════════════════════════════════
#   helper: safety
# ══════════════════════════════════════════════════════════════════════════════


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tiers_for_capacity_batch(channels=5, retention_days=30, nodes=3)
    after = ent.get_entitlement().to_dict()
    assert before == after


def test_never_raises_on_helper_boom(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_channel_count", boom)
    body = ent.tiers_for_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_stable_across_calls(ent):
    a = ent.tiers_for_capacity_batch(channels=5, retention_days=30, nodes=3)
    b = ent.tiers_for_capacity_batch(channels=5, retention_days=30, nodes=3)
    assert a == b


# ══════════════════════════════════════════════════════════════════════════════
#   helper: grace vs enforce parity
# ══════════════════════════════════════════════════════════════════════════════


def test_grace_vs_enforce_yields_identical_rows(monkeypatch, ent):
    """The helper walks the static per-tier caps via the singular
    ``tiers_for_*`` helpers, so per-axis rows are perspective-independent
    on grace vs enforce."""
    grace = ent.tiers_for_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        enforced = e.tiers_for_capacity_batch(
            channels=5, retention_days=30, nodes=3
        )
        assert enforced == grace
    finally:
        e.invalidate()


# ══════════════════════════════════════════════════════════════════════════════
#   API surface
# ══════════════════════════════════════════════════════════════════════════════


def test_api_returns_envelope_shape(client):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=5&retention_days=30&nodes=3"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "channels",
        "retention_days",
        "nodes",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_api_reports_grace_in_oss_default(client):
    body = client.get(
        "/api/entitlement/tiers-for-capacity-batch?channels=5"
    ).get_json()
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_missing_all_axes_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-capacity-batch")
    assert rv.status_code == 400


def test_api_all_blank_axes_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=&retention_days=&nodes="
    )
    assert rv.status_code == 400


def test_api_all_non_int_axes_is_400(client):
    """Non-int on every supplied axis short-circuits each to unsupplied,
    so the endpoint 400s (matches min-tier-batch's posture)."""
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=abc&retention_days=xyz&nodes=nope"
    )
    assert rv.status_code == 400


def test_api_partial_bad_input_treats_that_axis_as_unset(client):
    """A blank / non-int value on ONE axis is treated as 'not supplied'
    for that axis (matches min-tier-batch's never-crash posture rather
    than mis-routing a typo to Enterprise). Other supplied axes still
    render."""
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=5&retention_days=foo&nodes="
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_api_single_axis_supplied(client):
    rv = client.get("/api/entitlement/tiers-for-capacity-batch?channels=5")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is not None
    assert body["channels"]["kind"] == "channel_count"
    assert body["channels"]["item"] == 5
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_api_zero_on_every_axis_returns_all_tiers(client, ent):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=0&retention_days=0&nodes=0"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    for axis in ("channels", "retention_days", "nodes"):
        ids = {t["id"] for t in body[axis]["tiers"]}
        assert ids == set(ent._TIER_ORDER)


def test_api_rows_match_singular_endpoints(client, ent):
    """Per-row parity with the singular ``/tiers-for-<axis>`` endpoints
    is the answer -- drop the envelope off any row and it byte-equals
    the singular response for the same value."""
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch"
        "?channels=5&retention_days=30&nodes=3"
    ).get_json()
    envelope_keys = {
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }

    ch_single = client.get(
        "/api/entitlement/tiers-for-channel-count?count=5"
    ).get_json()
    ch_row = {k: v for k, v in ch_single.items() if k not in envelope_keys}
    assert rv["channels"] == ch_row

    rt_single = client.get(
        "/api/entitlement/tiers-for-retention-window?days=30"
    ).get_json()
    rt_row = {k: v for k, v in rt_single.items() if k not in envelope_keys}
    assert rv["retention_days"] == rt_row

    nd_single = client.get(
        "/api/entitlement/tiers-for-node-count?count=3"
    ).get_json()
    nd_row = {k: v for k, v in nd_single.items() if k not in envelope_keys}
    assert rv["nodes"] == nd_row


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(e, "tiers_for_capacity_batch", boom)
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch?channels=5"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
