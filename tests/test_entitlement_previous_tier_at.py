"""Tests for ``previous_tier_unlocks_at`` / ``previous_tier_locks_at`` --
scalar what-if siblings of the live :meth:`Entitlement.previous_tier_unlocks`
/ :meth:`Entitlement.previous_tier_locks` instance methods, plus the
companion ``/api/entitlement/previous-tier-{unlocks,locks}-at?tier=<src>``
endpoints and the private :func:`_previous_purchasable_tier_before`
stepper they share.

These helpers let a pricing-comparison UI render "what would still be
granted / first lose at the rung below X" for any hypothetical ``X``
without first asking the resolver or monkey-patching the entitlement
context -- the source-anchored counterpart of the live methods that
pin the source to the resolved entitlement.

Pins covered here:

* helper :func:`_previous_purchasable_tier_before` walks the static
  :data:`_PURCHASABLE_TIERS` rank ladder identically for every source
  tier -- floor returns ``None``, lenient on :data:`TIER_TRIAL`, and
  intentionally elides the cloud-vs-self-hosted preference the live
  :meth:`Entitlement.previous_purchasable_tier` applies (the ``_at``
  family is deterministic on the static catalogue)
* ``previous_tier_unlocks_at(tier)`` byte-equals
  ``tier_unlocks(_previous_purchasable_tier_before(tier))`` across
  every valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``previous_tier_locks_at`` against :func:`tier_locks`
* at the floor (no rung strictly below source -- oss / cloud_free)
  both helpers return ``None`` -- mirrors the live
  :meth:`Entitlement.previous_tier_unlocks` /
  :meth:`Entitlement.previous_tier_locks` behaviour
* trial-as-source resolves to the highest rank strictly below 2 ==
  cloud_starter (rank 1) -- the same rung the next-after-cloud-starter
  step lands on, walked in reverse
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* unknown / empty / ``None`` / non-string source returns ``None``
* the API surface 400s on missing input, 404s on unknown ids (with
  ``which``), surfaces 200 envelopes at the floor with ``row=null``,
  and never 5xxs
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- both helpers are
    catalogue-derived and independent of the resolver, so the fixture
    only needs to make sure the live resolver does not surprise the
    test."""
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


_UNLOCKS_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "previous_tier",
    "previous_tier_label",
    "previous_tier_rank",
    "features",
    "runtimes",
}

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

_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "row",
}


# ── _previous_purchasable_tier_before ───────────────────────────────────────


def test_previous_before_walks_to_highest_strictly_lower_rank(ent):
    # The stepper picks the highest rank strictly below source, then
    # the first entry in _PURCHASABLE_TIERS at that rank. Pinned per
    # known source so a reshuffle of the static ladder cannot silently
    # change the answer.
    expected = {
        ent.TIER_CLOUD_STARTER: ent.TIER_OSS,
        ent.TIER_TRIAL: ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO: ent.TIER_CLOUD_STARTER,
        ent.TIER_PRO: ent.TIER_CLOUD_STARTER,
        ent.TIER_ENTERPRISE: ent.TIER_CLOUD_PRO,
    }
    for src, exp in expected.items():
        assert ent._previous_purchasable_tier_before(src) == exp, src


def test_previous_before_returns_none_at_floor(ent):
    # oss and cloud_free both sit at rank 0 -- nothing strictly below.
    assert ent._previous_purchasable_tier_before(ent.TIER_OSS) is None
    assert ent._previous_purchasable_tier_before(ent.TIER_CLOUD_FREE) is None


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_previous_before_returns_none_on_bad_input(ent, bad):
    assert ent._previous_purchasable_tier_before(bad) is None


def test_previous_before_trims_and_lowercases(ent):
    # Same canonicalisation the rest of the _at family applies.
    assert (
        ent._previous_purchasable_tier_before("  CLOUD_STARTER  ")
        == ent.TIER_OSS
    )


def test_previous_before_independent_of_resolver(ent, monkeypatch):
    # The stepper must not call get_entitlement at any point -- if it
    # does, swapping it to raise would make the helper return None.
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert (
        ent._previous_purchasable_tier_before(ent.TIER_CLOUD_STARTER)
        == ent.TIER_OSS
    )


def test_previous_before_elides_cloud_vs_self_hosted_preference(ent):
    # The live Entitlement.previous_purchasable_tier applies a cloud-
    # vs-self-hosted tie-break against the resolved source -- the _at
    # stepper intentionally does NOT (declaration-order tie-break),
    # since the source is hypothetical. Enterprise's strictly-lower
    # cluster is rank 2 == {cloud_pro, pro}; _PURCHASABLE_TIERS declares
    # cloud_pro before pro, so the helper deterministically picks
    # cloud_pro regardless of how the resolver is currently sourced.
    assert (
        ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
        == ent.TIER_CLOUD_PRO
    )


def test_previous_before_never_raises(monkeypatch, ent):
    # Synthetic _TIER_RANK failure -- the helper must swallow and
    # return None rather than propagate.
    monkeypatch.setattr(
        ent,
        "_TIER_RANK",
        type("Boom", (), {"get": lambda *_, **__: (_ for _ in ()).throw(RuntimeError())})(),
    )
    assert (
        ent._previous_purchasable_tier_before(ent.TIER_CLOUD_STARTER) is None
    )


# ── previous_tier_unlocks_at ────────────────────────────────────────────────


def test_previous_tier_unlocks_at_matches_explicit_composition(ent):
    # The convenience is tier_unlocks(_previous_purchasable_tier_before(tier)).
    # Byte-equal across every source above the floor so callers can swap
    # between the singular helper and the explicit composition without
    # drift.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_unlocks_at(src) == ent.tier_unlocks(prv), src


def test_previous_tier_unlocks_at_returns_none_at_floor(ent):
    # oss / cloud_free have no rung below -> None, mirroring the live
    # method.
    assert ent.previous_tier_unlocks_at(ent.TIER_OSS) is None
    assert ent.previous_tier_unlocks_at(ent.TIER_CLOUD_FREE) is None


def test_previous_tier_unlocks_at_row_shape(ent):
    body = ent.previous_tier_unlocks_at(ent.TIER_CLOUD_PRO)
    assert body is not None
    assert set(body.keys()) == _UNLOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    # tier_unlocks sets previous_tier to target's natural next-lower
    # purchasable -- NOT the caller-supplied source -- so this carries
    # the rung below cloud_starter, not cloud_pro.
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_previous_tier_unlocks_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_unlocks_at(bad) is None


def test_previous_tier_unlocks_at_trims_and_lowercases(ent):
    assert ent.previous_tier_unlocks_at("  CLOUD_STARTER  ") == ent.tier_unlocks(
        ent.TIER_OSS
    )


def test_previous_tier_unlocks_at_trial_source_resolves_to_cloud_starter(ent):
    # Trial sits at rank 2, so the highest strictly-lower purchasable
    # rung is cloud_starter (rank 1).
    body = ent.previous_tier_unlocks_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_previous_tier_unlocks_at_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived (off the static per-tier grants) -- flipping
    # enforcement on must not change the body.
    grace = ent.previous_tier_unlocks_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_unlocks_at(ent.TIER_CLOUD_PRO)
    assert enforce == grace


def test_previous_tier_unlocks_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_unlocks",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.previous_tier_unlocks_at(ent.TIER_CLOUD_PRO) is None


def test_previous_tier_unlocks_at_independent_of_resolver(ent, monkeypatch):
    # The whole point of the _at variant: it does not need the
    # resolver. Swap get_entitlement to raise and the helper must
    # still return a non-None body above the floor.
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_unlocks_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert body["tier"] == ent.TIER_OSS


# ── previous_tier_locks_at ──────────────────────────────────────────────────


def test_previous_tier_locks_at_matches_explicit_composition(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_locks_at(src) == ent.tier_locks(prv), src


def test_previous_tier_locks_at_returns_none_at_floor(ent):
    assert ent.previous_tier_locks_at(ent.TIER_OSS) is None
    assert ent.previous_tier_locks_at(ent.TIER_CLOUD_FREE) is None


def test_previous_tier_locks_at_row_shape(ent):
    body = ent.previous_tier_locks_at(ent.TIER_CLOUD_PRO)
    assert body is not None
    assert set(body.keys()) == _LOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_previous_tier_locks_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_locks_at(bad) is None


def test_previous_tier_locks_at_trims_and_lowercases(ent):
    assert ent.previous_tier_locks_at("  CLOUD_STARTER  ") == ent.tier_locks(
        ent.TIER_OSS
    )


def test_previous_tier_locks_at_trial_source_resolves_to_cloud_starter(ent):
    body = ent.previous_tier_locks_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_previous_tier_locks_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_locks_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_locks_at(ent.TIER_CLOUD_PRO)
    assert enforce == grace


def test_previous_tier_locks_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_locks",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.previous_tier_locks_at(ent.TIER_CLOUD_PRO) is None


def test_previous_tier_locks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_locks_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert body["tier"] == ent.TIER_OSS


# ── API: /api/entitlement/previous-tier-unlocks-at ──────────────────────────


def test_previous_tier_unlocks_at_endpoint_cloud_starter_default(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=cloud_starter")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["target"] == ent.TIER_OSS
    assert body["target_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["row"] == ent.tier_unlocks(ent.TIER_OSS)


def test_previous_tier_unlocks_at_endpoint_oss_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_previous_tier_unlocks_at_endpoint_cloud_free_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=cloud_free")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_CLOUD_FREE
    assert body["target"] is None
    assert body["row"] is None


def test_previous_tier_unlocks_at_endpoint_trial(client, ent):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=trial")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.tier_unlocks(ent.TIER_CLOUD_STARTER)


def test_previous_tier_unlocks_at_endpoint_enterprise(client, ent):
    # Enterprise -> highest-rank-below is rank 2 == {cloud_pro, pro};
    # declaration order in _PURCHASABLE_TIERS picks cloud_pro.
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=enterprise")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.tier_unlocks(ent.TIER_CLOUD_PRO)


def test_previous_tier_unlocks_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at")
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "missing tier"


def test_previous_tier_unlocks_at_endpoint_blank_tier(client):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=%20%20")
    assert rv.status_code == 400


def test_previous_tier_unlocks_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_previous_tier_unlocks_at_endpoint_trims_and_lowercases(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-unlocks-at?tier=%20%20CLOUD_STARTER%20%20"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["target"] == ent.TIER_OSS


def test_previous_tier_unlocks_at_endpoint_never_raises(client, ent, monkeypatch):
    # Synthesise a builder failure and assert the envelope still
    # returns 200 with row=null so the dashboard doesn't break.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_unlocks_at", boom)
    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    rv = client.get("/api/entitlement/previous-tier-unlocks-at?tier=cloud_starter")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


# ── API: /api/entitlement/previous-tier-locks-at ────────────────────────────


def test_previous_tier_locks_at_endpoint_cloud_starter_default(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=cloud_starter")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["target"] == ent.TIER_OSS
    assert body["row"] == ent.tier_locks(ent.TIER_OSS)


def test_previous_tier_locks_at_endpoint_oss_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["row"] is None


def test_previous_tier_locks_at_endpoint_cloud_free_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=cloud_free")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] is None
    assert body["row"] is None


def test_previous_tier_locks_at_endpoint_trial(client, ent):
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=trial")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.tier_locks(ent.TIER_CLOUD_STARTER)


def test_previous_tier_locks_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/previous-tier-locks-at")
    assert rv.status_code == 400


def test_previous_tier_locks_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_previous_tier_locks_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_locks_at", boom)
    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    rv = client.get("/api/entitlement/previous-tier-locks-at?tier=cloud_starter")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


def test_endpoints_row_matches_helper(client, ent):
    # End-to-end parity: the endpoint body's row byte-equals the
    # module-level helper for the same source.
    unlocks_rv = client.get(
        "/api/entitlement/previous-tier-unlocks-at?tier=cloud_pro"
    )
    assert unlocks_rv.get_json()["row"] == ent.previous_tier_unlocks_at(
        ent.TIER_CLOUD_PRO
    )
    locks_rv = client.get(
        "/api/entitlement/previous-tier-locks-at?tier=cloud_pro"
    )
    assert locks_rv.get_json()["row"] == ent.previous_tier_locks_at(
        ent.TIER_CLOUD_PRO
    )
