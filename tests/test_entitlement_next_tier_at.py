"""Tests for ``next_tier_unlocks_at`` / ``next_tier_locks_at`` --
scalar what-if siblings of the live :meth:`Entitlement.next_tier_unlocks`
/ :meth:`Entitlement.next_tier_locks` instance methods, plus the
companion ``/api/entitlement/next-tier-{unlocks,locks}-at?tier=<src>``
endpoints and the private :func:`_next_purchasable_tier_after`
stepper they share.

These helpers let a pricing-comparison UI render "what's new / what's
lost at the next rung above X" for any hypothetical ``X`` without
first asking the resolver or monkey-patching the entitlement context
-- the source-anchored counterpart of the live methods that pin the
source to the resolved entitlement.

Pins covered here:

* helper :func:`_next_purchasable_tier_after` walks the static
  :data:`_PURCHASABLE_TIERS` rank ladder identically for every source
  tier -- ceiling returns ``None``, lenient on :data:`TIER_TRIAL`
* ``next_tier_unlocks_at(tier)`` byte-equals
  ``tier_unlocks(_next_purchasable_tier_after(tier))`` across every
  valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``next_tier_locks_at`` against :func:`tier_locks`
* at the ceiling (no rung strictly above source) both helpers return
  ``None`` -- mirrors the live :meth:`Entitlement.next_tier_unlocks`
  / :meth:`Entitlement.next_tier_locks` behaviour
* at the source rung whose next-above IS enterprise, the locks row
  collapses to empty ``lost_*`` lists with ``next_tier=null`` (the
  ladder ceiling's :func:`tier_locks` posture) -- a populated row,
  not ``None``
* trial-as-source resolves the same way :meth:`Entitlement.next_purchasable_tier`
  does for a trial entitlement: strictly-higher rank == enterprise
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* unknown / empty / ``None`` / non-string source returns ``None``
* the API surface 400s on missing input, 404s on unknown ids (with
  ``which``), surfaces 200 envelopes at the ceiling with ``row=null``,
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


# ── _next_purchasable_tier_after ─────────────────────────────────────────────


def test_next_after_walks_to_strictly_higher_rank(ent):
    # The stepper picks the first entry in _PURCHASABLE_TIERS with a
    # strictly higher rank. Pinned per known source so a reshuffle of
    # the static ladder cannot silently change the answer.
    expected = {
        ent.TIER_OSS: ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_FREE: ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_STARTER: ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO: ent.TIER_ENTERPRISE,
        ent.TIER_PRO: ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL: ent.TIER_ENTERPRISE,
    }
    for src, exp in expected.items():
        assert ent._next_purchasable_tier_after(src) == exp, src


def test_next_after_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- nothing
    # strictly above.
    assert ent._next_purchasable_tier_after(ent.TIER_ENTERPRISE) is None


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_after_returns_none_on_bad_input(ent, bad):
    assert ent._next_purchasable_tier_after(bad) is None


def test_next_after_trims_and_lowercases(ent):
    # Same canonicalisation the rest of the _at family applies.
    assert ent._next_purchasable_tier_after("  OSS  ") == ent.TIER_CLOUD_STARTER


def test_next_after_independent_of_resolver(ent, monkeypatch):
    # The stepper must not call get_entitlement at any point -- if it
    # does, swapping it to raise would make the helper return None.
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent._next_purchasable_tier_after(ent.TIER_OSS) == ent.TIER_CLOUD_STARTER


def test_next_after_never_raises(monkeypatch, ent):
    # Synthetic _TIER_RANK failure -- the helper must swallow and
    # return None rather than propagate.
    monkeypatch.setattr(
        ent,
        "_TIER_RANK",
        type("Boom", (), {"get": lambda *_, **__: (_ for _ in ()).throw(RuntimeError())})(),
    )
    assert ent._next_purchasable_tier_after(ent.TIER_OSS) is None


# ── next_tier_unlocks_at ─────────────────────────────────────────────────────


def test_next_tier_unlocks_at_matches_explicit_composition(ent):
    # The convenience is tier_unlocks(_next_purchasable_tier_after(tier)).
    # Byte-equal across every source so callers can swap between the
    # singular helper and the explicit composition without drift.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        nxt = ent._next_purchasable_tier_after(src)
        assert nxt is not None, src
        assert ent.next_tier_unlocks_at(src) == ent.tier_unlocks(nxt), src


def test_next_tier_unlocks_at_returns_none_at_ceiling(ent):
    # Enterprise has no rung above -> None, mirroring the live method.
    assert ent.next_tier_unlocks_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_unlocks_at_row_shape(ent):
    body = ent.next_tier_unlocks_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert set(body.keys()) == _UNLOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    # tier_unlocks sets previous_tier to target's natural next-lower
    # purchasable -- NOT the caller-supplied source -- so this carries
    # cloud_starter (the natural floor below cloud_pro), which here
    # happens to coincide with the source.
    assert body["previous_tier"] is not None
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_tier_unlocks_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_unlocks_at(bad) is None


def test_next_tier_unlocks_at_trims_and_lowercases(ent):
    assert ent.next_tier_unlocks_at("  OSS  ") == ent.tier_unlocks(
        ent.TIER_CLOUD_STARTER
    )


def test_next_tier_unlocks_at_trial_source_resolves_to_enterprise(ent):
    # Trial sits at rank 2, so the next strictly-higher purchasable
    # rung is enterprise -- matches the live method's posture when
    # called from a trial entitlement.
    body = ent.next_tier_unlocks_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_next_tier_unlocks_at_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived (off the static per-tier grants) -- flipping
    # enforcement on must not change the body.
    grace = ent.next_tier_unlocks_at(ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_unlocks_at(ent.TIER_CLOUD_STARTER)
    assert enforce == grace


def test_next_tier_unlocks_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_unlocks",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.next_tier_unlocks_at(ent.TIER_OSS) is None


def test_next_tier_unlocks_at_independent_of_resolver(ent, monkeypatch):
    # The whole point of the _at variant: it does not need the
    # resolver. Swap get_entitlement to raise and the helper must
    # still return a non-None body.
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_unlocks_at(ent.TIER_OSS)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


# ── next_tier_locks_at ───────────────────────────────────────────────────────


def test_next_tier_locks_at_matches_explicit_composition(ent):
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        nxt = ent._next_purchasable_tier_after(src)
        assert nxt is not None, src
        assert ent.next_tier_locks_at(src) == ent.tier_locks(nxt), src


def test_next_tier_locks_at_returns_none_at_ceiling(ent):
    assert ent.next_tier_locks_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_locks_at_row_shape(ent):
    body = ent.next_tier_locks_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert set(body.keys()) == _LOCKS_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


def test_next_tier_locks_at_pro_collapses_to_empty_at_ceiling(ent):
    # Pro -> next is Enterprise -- the ladder ceiling. tier_locks(ENT)
    # carries next_tier=None and empty lost_* lists. The convenience
    # must surface that populated row, not None.
    body = ent.next_tier_locks_at(ent.TIER_PRO)
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["next_tier"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


def test_next_tier_locks_at_cloud_pro_collapses_to_empty_at_ceiling(ent):
    # cloud_pro -> next is Enterprise (same ceiling) -- identical
    # collapse, even though cloud_pro and pro both sit at rank 2.
    body = ent.next_tier_locks_at(ent.TIER_CLOUD_PRO)
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["next_tier"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_tier_locks_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_locks_at(bad) is None


def test_next_tier_locks_at_trims_and_lowercases(ent):
    assert ent.next_tier_locks_at("  OSS  ") == ent.tier_locks(
        ent.TIER_CLOUD_STARTER
    )


def test_next_tier_locks_at_trial_source_resolves_to_enterprise(ent):
    body = ent.next_tier_locks_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_next_tier_locks_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_locks_at(ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_locks_at(ent.TIER_CLOUD_STARTER)
    assert enforce == grace


def test_next_tier_locks_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_locks",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.next_tier_locks_at(ent.TIER_OSS) is None


def test_next_tier_locks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_locks_at(ent.TIER_OSS)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


# ── API: /api/entitlement/next-tier-unlocks-at ──────────────────────────────


def test_next_tier_unlocks_at_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["row"] == ent.tier_unlocks(ent.TIER_CLOUD_STARTER)


def test_next_tier_unlocks_at_endpoint_enterprise_ceiling(client, ent):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=enterprise")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_next_tier_unlocks_at_endpoint_trial(client, ent):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=trial")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["row"] == ent.tier_unlocks(ent.TIER_ENTERPRISE)


def test_next_tier_unlocks_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/next-tier-unlocks-at")
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "missing tier"


def test_next_tier_unlocks_at_endpoint_blank_tier(client):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=%20%20")
    assert rv.status_code == 400


def test_next_tier_unlocks_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_next_tier_unlocks_at_endpoint_trims_and_lowercases(client, ent):
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=%20%20OSS%20%20")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_next_tier_unlocks_at_endpoint_never_raises(client, ent, monkeypatch):
    # Synthesise a builder failure and assert the envelope still
    # returns 200 with row=null so the dashboard doesn't break.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_unlocks_at", boom)
    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


# ── API: /api/entitlement/next-tier-locks-at ─────────────────────────────────


def test_next_tier_locks_at_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.tier_locks(ent.TIER_CLOUD_STARTER)


def test_next_tier_locks_at_endpoint_enterprise_ceiling(client, ent):
    rv = client.get("/api/entitlement/next-tier-locks-at?tier=enterprise")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["row"] is None


def test_next_tier_locks_at_endpoint_pro_collapses_to_empty(client, ent):
    # pro -> next is enterprise (ceiling). The row carries the empty
    # collapse, not null on the envelope.
    rv = client.get("/api/entitlement/next-tier-locks-at?tier=pro")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["row"] is not None
    assert body["row"]["next_tier"] is None
    assert body["row"]["lost_features"] == []
    assert body["row"]["lost_runtimes"] == []


def test_next_tier_locks_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/next-tier-locks-at")
    assert rv.status_code == 400


def test_next_tier_locks_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/next-tier-locks-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_next_tier_locks_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_locks_at", boom)
    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    rv = client.get("/api/entitlement/next-tier-locks-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


def test_endpoints_row_matches_helper(client, ent):
    # End-to-end parity: the endpoint body's row byte-equals the
    # module-level helper for the same source.
    unlocks_rv = client.get("/api/entitlement/next-tier-unlocks-at?tier=cloud_starter")
    assert unlocks_rv.get_json()["row"] == ent.next_tier_unlocks_at(
        ent.TIER_CLOUD_STARTER
    )
    locks_rv = client.get("/api/entitlement/next-tier-locks-at?tier=cloud_starter")
    assert locks_rv.get_json()["row"] == ent.next_tier_locks_at(
        ent.TIER_CLOUD_STARTER
    )
