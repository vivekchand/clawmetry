"""Tests for ``clawmetry.entitlements.has_capacity_batch`` +
``has_capacity_batch_at`` and their wrapper endpoints.

Boolean-gate twin of ``tiers_for_capacity_batch`` on the three capacity
axes. Closes the symmetry gap in the ``has_*`` family: ``has_batch`` covers
only features + runtimes (the grant axes) and doesn't accept capacity args
at all -- so a caller that wants a live "does this install admit N
channels / K retention days / M nodes?" answer for a
``(channels, retention_days, nodes)`` bundle had to fan out three
``has_<axis>`` calls or hydrate the full ``capacity_headroom`` payload.
These tests pin the contract:

  - envelope shape mirrors ``tiers_for_capacity_batch`` on the three
    capacity axes exactly (per-axis ``None`` "not supplied" sentinel,
    same never-raise contract)
  - each boolean byte-equals the matching singular ``has_<axis>`` helper
    -- the batch cannot silently drift from the scalars
  - ``retention_days=None`` means unset, NOT unlimited (matches
    ``tiers_for_capacity_batch`` on the same axis)
  - the live ``has_capacity_batch`` grants everything in grace (matches
    the singular ``has_<axis>`` helpers) -- ``_at`` is grace-independent
  - the wrapper endpoints 400 only when *no* axis parsed successfully;
    blank/non-int values on individual axes are treated as unsupplied
  - the ``_at`` endpoint 400s on missing/blank tier and 404s on unknown
    tier
  - never 5xxs on the wrapper endpoints
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
    body = ent.has_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    assert isinstance(body, dict)
    assert set(body.keys()) == {"channels", "retention_days", "nodes"}


def test_returns_all_none_when_nothing_supplied(ent):
    body = ent.has_capacity_batch()
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_omitted_axis_is_none(ent):
    body = ent.has_capacity_batch(channels=5)
    assert body["channels"] is not None
    assert isinstance(body["channels"], bool)
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_each_axis_is_a_bool_when_supplied(ent):
    body = ent.has_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    for axis in ("channels", "retention_days", "nodes"):
        assert isinstance(body[axis], bool)


# ══════════════════════════════════════════════════════════════════════════════
#   helper: parity with singular helpers
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("count", [0, 1, 3, 5, 10, 100])
def test_channels_axis_equals_singular_helper(ent, count):
    body = ent.has_capacity_batch(channels=count)
    assert body["channels"] == ent.has_channel_count(count)


@pytest.mark.parametrize("days", [0, 1, 7, 30, 90, 365])
def test_retention_axis_equals_singular_helper(ent, days):
    body = ent.has_capacity_batch(retention_days=days)
    assert body["retention_days"] == ent.has_retention_window(days)


@pytest.mark.parametrize("count", [0, 1, 2, 3, 10, 100])
def test_nodes_axis_equals_singular_helper(ent, count):
    body = ent.has_capacity_batch(nodes=count)
    assert body["nodes"] == ent.has_node_count(count)


# ══════════════════════════════════════════════════════════════════════════════
#   helper: grace semantics carry through
# ══════════════════════════════════════════════════════════════════════════════


def test_grace_grants_every_finite_axis(ent):
    """The live helper delegates to the resolved entitlement, and OSS-free
    installs are in grace by default -- so every finite capacity request
    on every axis grants ``True``. Mirrors ``has_channel_count`` /
    ``has_retention_window`` / ``has_node_count``'s grace-passthrough."""
    body = ent.has_capacity_batch(
        channels=100, retention_days=3650, nodes=100
    )
    assert body == {
        "channels": True,
        "retention_days": True,
        "nodes": True,
    }


# ══════════════════════════════════════════════════════════════════════════════
#   helper: retention_days=None means UNSET (not unlimited)
# ══════════════════════════════════════════════════════════════════════════════


def test_retention_none_means_unset_not_unlimited(ent):
    """``retention_days=None`` means the axis was not supplied. Distinct
    from the singular ``has_retention_window(None)`` semantics where
    ``None`` means the unlimited-retention request -- mirrors
    ``tiers_for_capacity_batch`` on the same axis so a caller supplying
    every other axis but leaving retention off does not get a mis-routed
    live-grant answer."""
    body = ent.has_capacity_batch(channels=5, nodes=3)
    assert body["retention_days"] is None


# ══════════════════════════════════════════════════════════════════════════════
#   helper: bad input
# ══════════════════════════════════════════════════════════════════════════════


def test_channels_non_int_axis_is_false(ent):
    """Distinct from the ``None`` 'not supplied' sentinel: a non-int
    delegates to ``has_channel_count`` which returns ``False`` on typo
    (strict callsite-typo posture)."""
    body = ent.has_capacity_batch(channels="not-a-number")
    assert body["channels"] is False


def test_retention_non_int_axis_is_false(ent):
    body = ent.has_capacity_batch(retention_days="foo")
    assert body["retention_days"] is False


def test_nodes_non_int_axis_is_false(ent):
    body = ent.has_capacity_batch(nodes="bar")
    assert body["nodes"] is False


# ══════════════════════════════════════════════════════════════════════════════
#   helper: safety
# ══════════════════════════════════════════════════════════════════════════════


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.has_capacity_batch(channels=5, retention_days=30, nodes=3)
    after = ent.get_entitlement().to_dict()
    assert before == after


def test_never_raises_on_helper_boom(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "has_channel_count", boom)
    body = ent.has_capacity_batch(
        channels=5, retention_days=30, nodes=3
    )
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_stable_across_calls(ent):
    a = ent.has_capacity_batch(channels=5, retention_days=30, nodes=3)
    b = ent.has_capacity_batch(channels=5, retention_days=30, nodes=3)
    assert a == b


# ══════════════════════════════════════════════════════════════════════════════
#   _at helper
# ══════════════════════════════════════════════════════════════════════════════


def test_at_unknown_perspective_returns_none(ent):
    assert ent.has_capacity_batch_at("bogus", channels=5) is None


def test_at_empty_perspective_returns_none(ent):
    assert ent.has_capacity_batch_at("", channels=5) is None


def test_at_none_perspective_returns_none(ent):
    assert ent.has_capacity_batch_at(None, channels=5) is None


def test_at_returns_three_axis_envelope(ent):
    body = ent.has_capacity_batch_at(
        "cloud_pro", channels=5, retention_days=30, nodes=3
    )
    assert isinstance(body, dict)
    assert set(body.keys()) == {"channels", "retention_days", "nodes"}


def test_at_omitted_axis_is_none(ent):
    body = ent.has_capacity_batch_at("cloud_pro", channels=5)
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


@pytest.mark.parametrize("tier", ["oss", "cloud_free", "cloud_starter",
                                  "cloud_pro", "pro", "trial", "enterprise"])
def test_at_channels_axis_equals_singular_at_helper(ent, tier):
    body = ent.has_capacity_batch_at(tier, channels=5)
    assert body["channels"] == ent.has_channel_count_at(tier, 5)


@pytest.mark.parametrize("tier", ["oss", "cloud_free", "cloud_starter",
                                  "cloud_pro", "pro", "trial", "enterprise"])
def test_at_retention_axis_equals_singular_at_helper(ent, tier):
    body = ent.has_capacity_batch_at(tier, retention_days=30)
    assert body["retention_days"] == ent.has_retention_window_at(tier, 30)


@pytest.mark.parametrize("tier", ["oss", "cloud_free", "cloud_starter",
                                  "cloud_pro", "pro", "trial", "enterprise"])
def test_at_nodes_axis_equals_singular_at_helper(ent, tier):
    body = ent.has_capacity_batch_at(tier, nodes=3)
    assert body["nodes"] == ent.has_node_count_at(tier, 3)


def test_at_is_grace_independent(monkeypatch, ent):
    """The ``_at`` variant is backed by the static per-tier caps, not the
    resolved entitlement, so grace vs enforce yields byte-identical
    rows. That's the whole point of a what-if scalar."""
    grace = ent.has_capacity_batch_at(
        "oss", channels=100, retention_days=3650, nodes=100
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        enforced = e.has_capacity_batch_at(
            "oss", channels=100, retention_days=3650, nodes=100
        )
        assert enforced == grace
    finally:
        e.invalidate()


def test_at_oss_denies_over_free_floor(ent):
    """A cap-blowing request at ``oss`` returns ``False`` even in grace --
    the whole point of the ``_at`` scalar."""
    body = ent.has_capacity_batch_at(
        "oss", channels=100_000
    )
    assert body["channels"] is False


def test_at_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "has_channel_count_at", boom)
    body = ent.has_capacity_batch_at(
        "cloud_pro", channels=5, retention_days=30, nodes=3
    )
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#   API surface -- /has-capacity-batch
# ══════════════════════════════════════════════════════════════════════════════


def test_api_returns_envelope_shape(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch"
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
        "/api/entitlement/has-capacity-batch?channels=5"
    ).get_json()
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_missing_all_axes_is_400(client):
    rv = client.get("/api/entitlement/has-capacity-batch")
    assert rv.status_code == 400


def test_api_all_blank_axes_is_400(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch"
        "?channels=&retention_days=&nodes="
    )
    assert rv.status_code == 400


def test_api_all_non_int_axes_is_400(client):
    """Non-int on every supplied axis short-circuits each to unsupplied,
    so the endpoint 400s (matches ``/tiers-for-capacity-batch``'s
    posture)."""
    rv = client.get(
        "/api/entitlement/has-capacity-batch"
        "?channels=abc&retention_days=xyz&nodes=nope"
    )
    assert rv.status_code == 400


def test_api_partial_bad_input_treats_that_axis_as_unset(client):
    """A blank / non-int value on ONE axis is treated as 'not supplied'
    for that axis. Other supplied axes still render."""
    rv = client.get(
        "/api/entitlement/has-capacity-batch"
        "?channels=5&retention_days=foo&nodes="
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_api_single_axis_supplied(client):
    rv = client.get("/api/entitlement/has-capacity-batch?channels=5")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is True  # grace in OSS default
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_api_zero_on_every_axis_returns_true(client):
    """Zero on any capacity axis is trivially satisfied by the free
    floor -- mirrors the singular ``has_<axis>`` helpers' zero-branch."""
    rv = client.get(
        "/api/entitlement/has-capacity-batch"
        "?channels=0&retention_days=0&nodes=0"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is True
    assert body["retention_days"] is True
    assert body["nodes"] is True


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(e, "has_capacity_batch", boom)
    rv = client.get(
        "/api/entitlement/has-capacity-batch?channels=5"
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


# ══════════════════════════════════════════════════════════════════════════════
#   API surface -- /has-capacity-batch-at
# ══════════════════════════════════════════════════════════════════════════════


def test_at_api_missing_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at?channels=5"
    )
    assert rv.status_code == 400


def test_at_api_blank_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at?tier=&channels=5"
    )
    assert rv.status_code == 400


def test_at_api_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at?tier=bogus&channels=5"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_at_api_missing_all_axes_is_400(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at?tier=cloud_pro"
    )
    assert rv.status_code == 400


def test_at_api_returns_envelope_shape(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at"
        "?tier=cloud_pro&channels=5&retention_days=30&nodes=3"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "channels",
        "retention_days",
        "nodes",
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_at_api_oss_denies_over_free_floor(client):
    """The ``_at`` endpoint is grace-independent -- an OSS perspective
    with a cap-blowing channel request returns ``false`` even in
    grace."""
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at"
        "?tier=oss&channels=100000"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is False


def test_at_api_partial_bad_input_treats_that_axis_as_unset(client):
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at"
        "?tier=cloud_pro&channels=5&retention_days=foo&nodes="
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_at_api_perspective_envelope_populated(client):
    body = client.get(
        "/api/entitlement/has-capacity-batch-at?tier=cloud_pro&channels=5"
    ).get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert isinstance(body["perspective_tier_label"], str)
    assert body["perspective_tier_label"]
    assert isinstance(body["perspective_tier_rank"], int)


def test_at_api_resolver_failure_returns_perspective_envelope(
    monkeypatch, client
):
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(e, "has_capacity_batch_at", boom)
    rv = client.get(
        "/api/entitlement/has-capacity-batch-at?tier=cloud_pro&channels=5"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["perspective_tier"] == "cloud_pro"
    assert body["grace"] is True
    assert body["enforced"] is False
