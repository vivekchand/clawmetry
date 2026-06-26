"""Tests for ``Entitlement.next_tier_locks`` / ``previous_tier_locks``, the
module-level convenience helpers, the ``to_dict`` surface, and the companion
``/api/entitlement/{next,previous}-tier-locks`` endpoints.

The dashboard's downgrade confirmation card currently composes the marginal-
loss payload client-side by hitting ``/api/entitlement/tier-locks?tier=<prev>``
after a ``/api/entitlement`` round-trip; these helpers expose the same row in
one call so the card can render off a single fetch. Marginal-loss companion to
the existing ``next_tier_unlocks`` / ``previous_tier_unlocks`` family (same
shape, ``lost_*`` lists instead of ``features`` / ``runtimes`` grants), and
the fourth member of the ``next_tier_*`` / ``previous_tier_*`` family
alongside ``next_tier_diff`` (full ``upgrade_diff`` shape),
``next_tier_unlocks`` (marginal grant), and ``next_tier_capacity_diff``
(capacity-only marginal) -- the slot the family was missing before this PR.

Pins covered here:

* method-vs-tier_locks identity for next/previous
* method-vs-module-level helper identity
* tier_locks shape (8 stable keys, sorted lists, label/rank metadata)
* ceiling / floor behaviour (Enterprise has no next, OSS/cloud_free has no
  previous) -- returns ``None``
* enterprise-as-next collapses the rows ``lost_*`` lists to empty (Enterprise
  is the ladder ceiling, its tier_locks row has no rung above to step down
  from)
* set-identity invariant: previous_tier_locks's ``lost_*`` byte-equal the
  caller's marginal loss from ``downgrade_diff(previous_tier)`` -- so the row
  IS the "if I drop one rung, what would I lose" answer
* grace vs enforce yields the same body (catalogue-derived, not gated)
* trial source resolves to enterprise as next (rank 2 -> rank 3) and to the
  same-rank-cluster sibling for previous
* to_dict carries the two new fields with the expected null/body shape per
  tier
* API surface: 200 always (no 5xx), locks=null at the floor/ceiling,
  current_* tier metadata included, never-raise envelope on a synthetic
  resolver failure
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


_LOCKS_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "next_tier",
    "next_tier_label",
    "next_tier_rank",
    "lost_features",
    "lost_runtimes",
}


# ── Entitlement.next_tier_locks ──────────────────────────────────────────────


def test_next_tier_locks_matches_tier_locks_of_next(ent):
    # next_tier_locks() is a convenience for tier_locks(next_purchasable_tier())
    # -- they must be byte-equal across every purchasable tier so a caller can
    # use the singular helper interchangeably.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        assert nxt is not None
        assert e.next_tier_locks() == ent.tier_locks(nxt)


def test_next_tier_locks_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above to
    # upgrade to, so the convenience returns None just like
    # next_purchasable_tier().
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    assert e.next_tier_locks() is None


def test_next_tier_locks_shape(ent):
    # The row must carry the full tier_locks shape so the CTA can render
    # labels + rank without a second round-trip.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_locks()
    assert body is not None
    assert set(body.keys()) == _LOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


def test_next_tier_locks_enterprise_collapses_to_empty_when_caller_is_pro(ent):
    # Pro's next purchasable rung is Enterprise (the ceiling). tier_locks(ENT)
    # carries Enterprise as the destination of a step-down from the rung above
    # it -- but there IS no rung above Enterprise, so next_tier=None and the
    # lost_* lists collapse to []. The convenience must surface that shape, not
    # 500 or short-circuit to None.
    e = ent._build(ent.TIER_PRO, "license")
    nxt = e.next_purchasable_tier()
    assert nxt == ent.TIER_ENTERPRISE
    body = e.next_tier_locks()
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["next_tier"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


def test_next_tier_locks_never_raises_on_resolver_failure(ent, monkeypatch):
    # If next_purchasable_tier blows up, the helper must swallow and return
    # None so the dashboard CTA keeps rendering rather than 500-ing.
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_locks() is None


# ── Entitlement.previous_tier_locks ──────────────────────────────────────────


def test_previous_tier_locks_matches_tier_locks_of_previous(ent):
    # Symmetric to next_tier_locks: previous_tier_locks() must be byte-equal to
    # tier_locks(previous_purchasable_tier()).
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert e.previous_tier_locks() == ent.tier_locks(prev)


def test_previous_tier_locks_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below to step down to,
    # so the helper returns None mirroring previous_purchasable_tier().
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        assert e.previous_tier_locks() is None


def test_previous_tier_locks_shape(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    body = e.previous_tier_locks()
    assert body is not None
    assert set(body.keys()) == _LOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)


def test_previous_tier_locks_loss_matches_downgrade_by_one_rung(ent):
    # The whole point of previous_tier_locks: the row's lost_* lists represent
    # exactly what the caller would lose by stepping down one rung. Pin the
    # set-identity against the caller's own downgrade_diff(previous_tier)
    # across every tier with a previous rung so a future reshuffle of the
    # tier grant sets can't silently desync the convenience from the explicit
    # downgrade view.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        diff = e.downgrade_diff(prev)
        body = e.previous_tier_locks()
        assert body is not None
        assert body["lost_features"] == diff["lost_features"]
        assert body["lost_runtimes"] == diff["lost_runtimes"]


def test_previous_tier_locks_never_raises_on_resolver_failure(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_locks() is None


# ── trial source resolution ──────────────────────────────────────────────────


def test_trial_next_locks_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro / self-hosted pro, so the next
    # strictly-higher purchasable rung is enterprise (rank 3).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.next_tier_locks()
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_trial_previous_locks_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter) -- the highest rank strictly below
    # trial's rank 2.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.previous_tier_locks()
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


# ── grace vs enforce ─────────────────────────────────────────────────────────


def test_grace_and_enforce_yield_same_locks(ent, monkeypatch):
    # These helpers are catalogue-derived (off the static per-tier grants),
    # not gated -- so flipping enforce on must not change the body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_locks()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_locks()
    assert enforce_body == grace_body


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_level_next_helper_matches_method(ent):
    # The bare module-level helper resolves the current entitlement and
    # delegates, so it must agree with the bound method.
    assert ent.next_tier_locks() == ent.get_entitlement().next_tier_locks()


def test_module_level_previous_helper_matches_method(ent):
    assert (
        ent.previous_tier_locks() == ent.get_entitlement().previous_tier_locks()
    )


def test_module_level_next_helper_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_locks() is None


def test_module_level_previous_helper_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_locks() is None


# ── to_dict carries the new fields ───────────────────────────────────────────


def test_to_dict_carries_next_tier_locks(ent):
    body = ent._oss_free().to_dict()
    assert "next_tier_locks" in body
    # OSS has a next rung -> the field is a non-null row.
    assert body["next_tier_locks"] is not None
    assert body["next_tier_locks"]["tier"] == ent.TIER_CLOUD_STARTER


def test_to_dict_carries_prev_tier_locks(ent):
    body = ent._build(ent.TIER_CLOUD_PRO, "cloud").to_dict()
    assert "prev_tier_locks" in body
    assert body["prev_tier_locks"] is not None
    assert body["prev_tier_locks"]["tier"] == ent.TIER_CLOUD_STARTER


def test_to_dict_next_locks_null_at_ceiling(ent):
    body = ent._build(ent.TIER_ENTERPRISE, "license").to_dict()
    assert body["next_tier_locks"] is None


def test_to_dict_prev_locks_null_at_floor(ent):
    body = ent._oss_free().to_dict()
    assert body["prev_tier_locks"] is None


# ── API surface ──────────────────────────────────────────────────────────────


_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "locks",
    "grace",
    "enforced",
}


def test_next_tier_locks_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["locks"] is not None
    assert body["locks"]["tier"] == ent.TIER_CLOUD_STARTER
    assert body["grace"] is True
    assert body["enforced"] is False


def test_previous_tier_locks_endpoint_oss_default_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor; nothing below to step down to.
    assert body["locks"] is None


def test_next_tier_locks_endpoint_never_raises(client, ent, monkeypatch):
    # Synthesise a resolver failure and assert the envelope still returns 200
    # with the grace-shape body so the dashboard doesn't break on a flaky
    # entitlement read.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-locks")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["locks"] is None
    assert body["current_tier"] == "oss"


def test_previous_tier_locks_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-locks")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["locks"] is None
    assert body["current_tier"] == "oss"


def test_endpoint_locks_row_matches_tier_locks(client, ent):
    # The body's locks row must byte-equal what /tier-locks?tier=<next>
    # returns directly -- pin the equivalence so callers can swap between the
    # two endpoints without copy drift.
    rv = client.get("/api/entitlement/next-tier-locks")
    body = rv.get_json()
    assert body["locks"] == ent.tier_locks(ent.TIER_CLOUD_STARTER)
