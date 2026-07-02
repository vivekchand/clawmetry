"""Tests for the bare directional
``/api/entitlement/{next,previous}-tier-capacity-diff`` endpoints and
their live-resolver posture.

Capacity-only marginal companion to the already-shipped bare
directional family (``/next-tier-diff``, ``/next-tier-unlocks``,
``/next-tier-locks``, ``/next-tier-spec``): where those give the full
upgrade payload / grant row / loss row / spec descriptor for the rung
above (or below) the resolved entitlement, this pair returns just the
capacity slice (``target``, ``channel_limit``, ``retention_days``,
``node_limit``) so a capacity-only tooltip on the upgrade CTA card can
render off ONE round-trip.

The underlying ``Entitlement.next_tier_capacity_diff`` /
``previous_tier_capacity_diff`` instance methods and the module-level
convenience helpers already exist; this diff wires the HTTP endpoints
that were previously referenced only as "companions" in sibling
docstrings but never registered on ``bp_entitlement``.

Pins covered here:

* endpoint envelope shape (``current_tier`` / ``current_tier_label`` /
  ``current_tier_rank`` / ``row`` / ``grace`` / ``enforced``)
* endpoint ``row`` byte-equals the resolved
  ``Entitlement.next_tier_capacity_diff`` / ``previous_tier_capacity_diff``
  bound-method result -- so a caller can swap between the two entry
  points without copy drift
* floor / ceiling behaviour: ``row=null`` at OSS / cloud_free for
  previous and at Enterprise for next; envelope still populated so the
  surface never disappears
* trial-source resolution: next-of-trial is Enterprise (rank 2 -> 3),
  previous-of-trial is cloud_starter (rank 2 -> rank 1)
* live-resolver posture (unlike the ``_at`` sibling): under grace the
  ``before`` side of ``channel_limit`` collapses to the unlimited
  sentinel because :meth:`Entitlement.channel_limit` is grace-gated --
  documented on the endpoint so the semantic difference from the ``_at``
  variant is not a footgun
* endpoint never 5xxs on a resolver failure: falls back to the OSS
  grace-shape envelope with ``row=null``
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_CAPACITY_ROW_KEYS = {
    "target",
    "channel_limit",
    "retention_days",
    "node_limit",
}

_AXIS_KEYS = {"before", "after", "delta", "unlocked", "locked"}

_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "row",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode)."""
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


# ── envelope shape ─────────────────────────────────────────────────────


def test_next_endpoint_envelope_shape(client):
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_previous_endpoint_envelope_shape(client):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_next_endpoint_row_carries_capacity_row_shape(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    # OSS has a next rung -> row is populated.
    assert body["row"] is not None
    assert set(body["row"].keys()) == _CAPACITY_ROW_KEYS
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert set(body["row"][axis].keys()) == _AXIS_KEYS


def test_next_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER
    assert body["grace"] is True
    assert body["enforced"] is False


def test_previous_endpoint_oss_default_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    body = rv.get_json()
    # OSS is the floor -- nothing below to step down to.
    assert body["current_tier"] == ent.TIER_OSS
    assert body["row"] is None


# ── row equals the underlying method ───────────────────────────────────


def test_next_endpoint_row_matches_method(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["row"] == ent.get_entitlement().next_tier_capacity_diff()


def test_previous_endpoint_row_matches_method(client, ent, monkeypatch):
    # Move off the floor so previous_tier_capacity_diff() is non-null.
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud")
    )
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_CLOUD_PRO
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent._build(
        ent.TIER_CLOUD_PRO, "cloud"
    ).previous_tier_capacity_diff()


def test_next_endpoint_row_matches_module_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["row"] == ent.next_tier_capacity_diff()


def test_previous_endpoint_row_matches_module_helper(
    client, ent, monkeypatch
):
    monkeypatch.setattr(
        ent, "get_entitlement", lambda: ent._build(ent.TIER_CLOUD_PRO, "cloud")
    )
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    body = rv.get_json()
    assert body["row"] == ent.previous_tier_capacity_diff()


# ── ceiling / floor ────────────────────────────────────────────────────


def test_next_endpoint_row_null_at_ceiling(client, ent, monkeypatch):
    # Enterprise is the ladder ceiling -- no rung above to upgrade to,
    # so the row collapses to null but the envelope still populates.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_ENTERPRISE, "license"),
    )
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    assert body["row"] is None


def test_previous_endpoint_row_null_at_floor(client, ent, monkeypatch):
    # OSS and cloud_free both sit at rank 0 -- no rung below.
    for floor_tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        monkeypatch.setattr(
            ent, "get_entitlement", lambda t=floor_tier: ent._build(t, "test")
        )
        rv = client.get("/api/entitlement/previous-tier-capacity-diff")
        body = rv.get_json()
        assert body["current_tier"] == floor_tier
        assert body["row"] is None


# ── trial resolution ───────────────────────────────────────────────────


def test_next_endpoint_trial_resolves_to_enterprise(client, ent, monkeypatch):
    # Trial sits at rank 2 alongside cloud_pro / pro. Next strictly-higher
    # purchasable rung is Enterprise.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_TRIAL, "cloud"),
    )
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_TRIAL
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_ENTERPRISE


def test_previous_endpoint_trial_resolves_to_starter(
    client, ent, monkeypatch
):
    # Trial's previous purchasable rung is cloud_starter (rank 1).
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_TRIAL, "cloud"),
    )
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_TRIAL
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER


# ── live-resolver posture (grace vs enforce differs) ───────────────────


def test_grace_before_channel_limit_is_unlimited_sentinel(
    client, ent, monkeypatch
):
    # Unlike the _at variant, the bare endpoint's row.before comes off
    # the live Entitlement -- and Entitlement.channel_limit() is
    # grace-gated (returns None as the unlimited sentinel under grace).
    # Pin the sentinel so a future reshuffle of grace semantics does not
    # silently change the endpoint's before-side behaviour.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_CLOUD_STARTER, "cloud"),
    )
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["grace"] is True
    assert body["row"] is not None
    assert body["row"]["channel_limit"]["before"] is None


def test_enforce_before_channel_limit_is_static_cap(
    monkeypatch, tmp_path
):
    # Flip enforce on, rebuild the module, and confirm the bare endpoint's
    # row.before switches to the strict per-tier cap (not the unlimited
    # sentinel). This is the semantic difference from
    # /next-tier-capacity-diff-at documented on the endpoint.
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    monkeypatch.setattr(
        e, "get_entitlement", lambda: e._build(e.TIER_CLOUD_STARTER, "cloud")
    )
    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    rv = app.test_client().get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["grace"] is False
    assert body["enforced"] is True
    assert body["row"] is not None
    # Under enforce, channel_limit.before pulls from _TIER_CHANNEL_LIMIT
    # for cloud_starter, not the unlimited sentinel.
    assert body["row"]["channel_limit"]["before"] == e._TIER_CHANNEL_LIMIT.get(
        e.TIER_CLOUD_STARTER, e._FREE_CHANNEL_LIMIT
    )


def test_retention_days_axis_is_static_regardless_of_grace(
    client, ent, monkeypatch
):
    # event_retention_days() is NOT grace-gated -- it pulls straight from
    # the per-tier catalogue. Pin so a future gating of retention doesn't
    # silently break this endpoint's contract.
    monkeypatch.setattr(
        ent,
        "get_entitlement",
        lambda: ent._build(ent.TIER_CLOUD_STARTER, "cloud"),
    )
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    body = rv.get_json()
    assert body["row"]["retention_days"]["before"] == ent._TIER_RETENTION_DAYS.get(
        ent.TIER_CLOUD_STARTER
    )


# ── never 5xxs ─────────────────────────────────────────────────────────


def test_next_endpoint_never_raises_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-capacity-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == "oss"
    assert body["current_tier_label"] == "OSS"
    assert body["current_tier_rank"] == 0
    assert body["row"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


def test_previous_endpoint_never_raises_on_resolver_failure(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-capacity-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == "oss"
    assert body["row"] is None
    assert body["grace"] is True
    assert body["enforced"] is False
