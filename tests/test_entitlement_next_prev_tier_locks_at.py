"""Tests for ``next_tier_locks_at`` / ``previous_tier_locks_at`` --
scalar what-if siblings of the live ``Entitlement.next_tier_locks`` /
``Entitlement.previous_tier_locks`` instance methods, plus the
companion ``/api/entitlement/{next,previous}-tier-locks-at?tier=<src>``
endpoints.

Marginal-loss mirror of the ``unlocks_at`` scalar pair pinned in #3665
and scalar counterpart of the ``locks_at_batch`` sibling pinned in
#3656 -- where the batch answers "what does the rung above / below X
first lose" across every entry in :data:`_PURCHASABLE_TIERS` in one
pass, the scalar answers the same what-if one source at a time and
never wraps the row in an envelope (that framing lives on the endpoint,
not the raw helper).

Unlike ``next_tier_diff_at`` / ``previous_tier_diff_at`` -- which
surface the full ``tier_diff`` payload with ``row["from"]`` byte-equal
to the caller-supplied source -- these helpers surface the target's
own :func:`tier_locks` row (target-anchored: ``row["next_tier"]`` is
the target's natural next-higher purchasable, NOT the caller-supplied
source). That mirrors the live ``Entitlement.{next,previous}_tier_locks``
posture and is the shape a pricing-comparison card renders when it
wants "what does Pro first lose vs Enterprise" not "the diff from OSS
to Pro".

Pins covered here:

* ``next_tier_locks_at(tier)`` byte-equals
  ``tier_locks(_next_purchasable_tier_after(tier))`` across every valid
  source -- the convenience cannot drift from the explicit composition
* same identity for ``previous_tier_locks_at`` against
  ``_previous_purchasable_tier_before``
* the returned row is target-anchored: ``row["tier"]`` is the resolved
  target (NOT the caller-supplied source) and ``row["next_tier"]`` is
  that target's natural next-higher purchasable
* row.lost_features / row.lost_runtimes byte-equal
  :func:`tier_unlocks` of the target's own next-higher purchasable
  (the set-identity ``tier_locks(X)['lost_features'] ==
  tier_unlocks(next_tier(X))['features']`` documented on
  :func:`tier_locks`) -- pins the scalar-side of the cross-family
  identity so the two views cannot silently desync
* the scalar row byte-equals the ``row`` slot of the ``_at_batch``
  envelope for the same source -- pins the scalar-vs-batch parity
  documented in :func:`next_tier_locks_at_batch` for the scalar side
  (the batch tests pin the mirror direction)
* the scalar's target axis byte-equals ``next_tier_diff_at(src)["to"]``
  / ``previous_tier_diff_at(src)["to"]`` -- the same "step X -> Y"
  agreement pinned for the unlocks scalar, so a pricing card that
  combines the locks scalar with the diff scalar always renders one Y
* at the ceiling / floor (no rung strictly above / below source) both
  helpers return ``None``, not an empty dict, so a caller can render
  "you're at the top / bottom" copy from a truthy check
* trial-as-source resolves the same way the unlocks ``_at`` family
  does: next -> enterprise, previous -> cloud_starter
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* unknown / empty / ``None`` / non-string source returns ``None``;
  builder failures short-circuit to ``None``, never raise
* the API endpoints:

  * 400 when ``tier=`` is missing / blank
  * 404 with ``which=tier`` when ``tier`` is unknown
  * 200 envelope in :data:`_ENVELOPE_KEYS` shape otherwise, with
    ``envelope["tier"]`` byte-equal to the caller-supplied source
    (case-insensitive, trimmed) and ``envelope["row"]`` byte-equal
    to the scalar helper for the same source
  * at the ceiling / floor: 200 envelope with ``target=null`` /
    ``row=null`` -- never 404, so the pricing UI does not have to
    branch on status codes to render "top / bottom of ladder"
  * builder failure short-circuits to a grace-shape envelope with
    ``row=null`` -- never 5xxs
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_LOCKS_ROW_KEYS = {
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


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- the locks ``_at`` family
    is catalogue-derived and independent of the resolver, so the fixture
    only needs to keep the live resolver from surprising the test."""
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


# ── next_tier_locks_at ───────────────────────────────────────────────────────


def test_next_locks_at_matches_explicit_composition(ent):
    # The convenience is tier_locks(_next_purchasable_tier_after(tier)).
    # Byte-equal across every source so callers can swap between the
    # scalar helper and the explicit composition without drift.
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


def test_next_locks_at_returns_none_at_ceiling(ent):
    # Enterprise has no rung above -> None, mirroring the live method.
    assert ent.next_tier_locks_at(ent.TIER_ENTERPRISE) is None


def test_next_locks_at_row_shape(ent):
    body = ent.next_tier_locks_at(ent.TIER_OSS)
    assert body is not None
    assert set(body.keys()) == _LOCKS_ROW_KEYS
    # Row is target-anchored: row.tier IS the resolved target
    # (cloud_starter for OSS), NOT the caller-supplied source. That's
    # the key differentiator vs next_tier_diff_at which pins row.from
    # to the caller-supplied source.
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    # Sorted for stable rendering.
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


def test_next_locks_at_row_next_tier_is_target_natural_next(ent):
    # row.next_tier is the target's natural next-higher purchasable,
    # NOT the caller-supplied source. Byte-equals what the live
    # /next-tier-locks surfaces off the resolver.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(src)
        assert target is not None, src
        body = ent.next_tier_locks_at(src)
        assert body is not None, src
        assert body["next_tier"] == ent.tier_locks(target)["next_tier"], src


def test_next_locks_at_row_target_agrees_with_row_tier(ent):
    # For every valid source, the row.tier field IS the target the
    # scalar helper resolved to -- the invariant the batch test pins
    # cross-envelope (env.row.tier == env.target).
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        body = ent.next_tier_locks_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["tier"] == target, src


def test_next_locks_at_target_axis_matches_diff_at(ent):
    # Cross-family target parity: the diff ``_at`` scalar and the
    # locks ``_at`` scalar MUST agree on the target rung for every
    # valid source, otherwise a pricing card that combines both to
    # render "step X -> Y: adds features F, next-rung-lose C" would
    # surface two different Ys.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        diff = ent.next_tier_diff_at(src)
        loc = ent.next_tier_locks_at(src)
        assert diff is not None, src
        assert loc is not None, src
        assert loc["tier"] == diff["to"], src


def test_next_locks_at_lost_slice_matches_set_identity(ent):
    # Cross-family set-identity: tier_locks(X)['lost_features'] ==
    # tier_unlocks(next_tier(X))['features'] is documented on
    # :func:`tier_locks`. Since the scalar what-if returns
    # tier_locks(_next_purchasable_tier_after(src)), the identity
    # composes to lost_features(next_of(src)) ==
    # features(next_of(next_of(src))). Pin the scalar side so a future
    # reshuffle of the marginal-loss builder cannot drift from the
    # marginal-grant builder off the same rungs.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        loc = ent.next_tier_locks_at(src)
        if target is None:
            assert loc is None, src
            continue
        assert loc is not None, src
        two_up = ent._next_purchasable_tier_after(target)
        if two_up is None:
            # target is at the ceiling -- no rung above target to lose
            # anything to, so lost_features / lost_runtimes collapse.
            assert loc["lost_features"] == [], src
            assert loc["lost_runtimes"] == [], src
            continue
        two_up_row = ent.tier_unlocks(two_up)
        assert loc["lost_features"] == two_up_row["features"], src
        assert loc["lost_runtimes"] == two_up_row["runtimes"], src


def test_next_locks_at_matches_batch_row_slot(ent):
    # Batch-vs-scalar parity from the scalar side: the ``_at_batch``
    # envelope's row slot for a given source MUST byte-equal the scalar
    # helper for the same source. The batch tests pin the mirror
    # direction (env.row == scalar for every env); this pins it from
    # the scalar side and defends against the batch drifting silently.
    by_tier = {env["tier"]: env for env in ent.next_tier_locks_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.next_tier_locks_at(src), src


def test_next_locks_at_matches_live_tier_locks_of_target(ent):
    # Anchoring the scalar what-if to the live cumulative accessor
    # keeps the ``_at`` helper from silently re-deriving locks off a
    # different code path.
    live = {row["tier"]: row for row in ent.tier_locks_batch()}
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        row = ent.next_tier_locks_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == live[target], src


def test_next_locks_at_trial_resolves_to_enterprise(ent):
    # Trial-as-source in the ``_at`` family walks past same-rank trial
    # to the strictly-higher rung; enterprise is the ceiling of
    # _PURCHASABLE_TIERS so the trial what-if answers enterprise.
    row = ent.next_tier_locks_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_ENTERPRISE


def test_next_locks_at_trims_and_lowercases(ent):
    body = ent.next_tier_locks_at("  OSS  ")
    assert body == ent.tier_locks(ent.TIER_CLOUD_STARTER)


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_next_locks_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_locks_at(bad) is None


def test_next_locks_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.next_tier_locks_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_locks_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_next_locks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_locks_at(ent.TIER_OSS)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_next_locks_at_swallows_builder_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_locks", boom)
    assert ent.next_tier_locks_at(ent.TIER_OSS) is None


def test_next_locks_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    assert ent.next_tier_locks_at(ent.TIER_OSS) is None


# ── previous_tier_locks_at ───────────────────────────────────────────────────


def test_previous_locks_at_matches_explicit_composition(ent):
    # Convenience is tier_locks(_previous_purchasable_tier_before(tier)).
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_locks_at(src) == ent.tier_locks(prv), src


def test_previous_locks_at_returns_none_at_floor(ent):
    # OSS / cloud_free sit at rank 0 -- nothing strictly below.
    assert ent.previous_tier_locks_at(ent.TIER_OSS) is None
    assert ent.previous_tier_locks_at(ent.TIER_CLOUD_FREE) is None


def test_previous_locks_at_row_shape(ent):
    body = ent.previous_tier_locks_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert set(body.keys()) == _LOCKS_ROW_KEYS
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["tier"] == prv
    assert body["tier_label"] == ent.tier_label(prv)
    assert body["tier_rank"] == ent.tier_rank(prv)
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


def test_previous_locks_at_row_target_agrees_with_row_tier(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        body = ent.previous_tier_locks_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["tier"] == target, src


def test_previous_locks_at_row_next_tier_is_target_natural_next(ent):
    # row.next_tier is the *target's* natural next-higher purchasable,
    # NOT the caller-supplied source -- the target-anchored posture the
    # live /previous-tier-locks endpoint surfaces.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(src)
        assert target is not None, src
        body = ent.previous_tier_locks_at(src)
        assert body is not None, src
        assert body["next_tier"] == ent.tier_locks(target)["next_tier"], src


def test_previous_locks_at_target_axis_matches_diff_at(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        diff = ent.previous_tier_diff_at(src)
        loc = ent.previous_tier_locks_at(src)
        assert diff is not None, src
        assert loc is not None, src
        assert loc["tier"] == diff["to"], src


def test_previous_locks_at_lost_slice_is_target_anchored(ent):
    # In the downgrade direction, the *diff* pins removed_features to
    # the features that would disappear when descending source->target
    # (source-anchored, source-vs-target set difference). The *locks*
    # pins row.lost_features to the target's OWN marginal-loss row
    # (target-anchored: what target first loses vs rung-above-target),
    # NOT the source diff's removed-features slice. That posture
    # difference is why the previous-direction test asserts the target-
    # anchoring rather than the removed-features parity that would hold
    # only if the row were source-anchored.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(src)
        assert target is not None, src
        loc = ent.previous_tier_locks_at(src)
        assert loc is not None, src
        # The row is byte-equal to :func:`tier_locks` of the target
        # (i.e. the target's OWN marginal-loss row), so the lost slice
        # is the target-vs-rung-above-target set difference -- NOT the
        # source-anchored diff's removed_features.
        assert loc == ent.tier_locks(target), src


def test_previous_locks_at_lost_slice_matches_set_identity(ent):
    # Same cross-family set-identity as the next direction:
    # tier_locks(X)['lost_features'] ==
    # tier_unlocks(next_of(X))['features']. Since the scalar what-if
    # returns tier_locks(_previous_purchasable_tier_before(src)), the
    # identity composes to lost_features(prev_of(src)) ==
    # features(next_of(prev_of(src))). Pin the scalar side so a future
    # reshuffle cannot silently desync the marginal-loss builder from
    # the marginal-grant builder off the same rungs.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        loc = ent.previous_tier_locks_at(src)
        if target is None:
            assert loc is None, src
            continue
        assert loc is not None, src
        two_up = ent._next_purchasable_tier_after(target)
        if two_up is None:
            assert loc["lost_features"] == [], src
            assert loc["lost_runtimes"] == [], src
            continue
        two_up_row = ent.tier_unlocks(two_up)
        assert loc["lost_features"] == two_up_row["features"], src
        assert loc["lost_runtimes"] == two_up_row["runtimes"], src


def test_previous_locks_at_matches_batch_row_slot(ent):
    by_tier = {env["tier"]: env for env in ent.previous_tier_locks_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.previous_tier_locks_at(src), src


def test_previous_locks_at_matches_live_tier_locks_of_target(ent):
    live = {row["tier"]: row for row in ent.tier_locks_batch()}
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        row = ent.previous_tier_locks_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == live[target], src


def test_previous_locks_at_trial_resolves_to_cloud_starter(ent):
    row = ent.previous_tier_locks_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_CLOUD_STARTER


def test_previous_locks_at_trims_and_lowercases(ent):
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert ent.previous_tier_locks_at("  ENTERPRISE  ") == ent.tier_locks(prv)


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_previous_locks_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_locks_at(bad) is None


def test_previous_locks_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.previous_tier_locks_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.previous_tier_locks_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_previous_locks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_locks_at(ent.TIER_ENTERPRISE)
    assert body is not None
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["tier"] == prv


def test_previous_locks_at_swallows_builder_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_locks", boom)
    assert ent.previous_tier_locks_at(ent.TIER_ENTERPRISE) is None


def test_previous_locks_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    assert ent.previous_tier_locks_at(ent.TIER_ENTERPRISE) is None


# ── cross-direction pins ─────────────────────────────────────────────────────


def test_scalar_helpers_are_mirror_across_step_direction(ent):
    # Stepping OSS -> next -> cloud_starter -> previous MUST land on the
    # OSS-cluster floor (the standard-ladder mirror invariant). Concretely,
    # previous(next(oss)) resolves to the natural floor of the ladder,
    # which is OSS since it is the anchor of _PURCHASABLE_TIERS.
    src = ent.TIER_OSS
    up = ent._next_purchasable_tier_after(src)
    assert up is not None
    down = ent._previous_purchasable_tier_before(up)
    assert down is not None
    # The floor is either OSS or cloud_free depending on which anchors
    # rank 0 -- previous_purchasable_tier_before picks the highest-rank
    # rung strictly below cloud_starter, which is that rank-0 anchor.
    assert down in (ent.TIER_OSS, ent.TIER_CLOUD_FREE)


def test_scalar_helpers_return_none_for_same_side_of_ceiling_and_floor(ent):
    # Semantic sanity: at the ceiling the *next* helper returns None; at
    # the floor the *previous* helper returns None. They MUST NOT swap.
    assert ent.next_tier_locks_at(ent.TIER_ENTERPRISE) is None
    assert ent.previous_tier_locks_at(ent.TIER_OSS) is None
    # But the mirror direction is still populated -- ceiling still has
    # a rung below, floor still has a rung above.
    assert ent.previous_tier_locks_at(ent.TIER_ENTERPRISE) is not None
    assert ent.next_tier_locks_at(ent.TIER_OSS) is not None


def test_locks_and_unlocks_scalar_share_target_axis(ent):
    # The scalar unlocks and scalar locks MUST agree on the target rung
    # for every valid source and both directions -- otherwise a pricing
    # card that pairs the "what's new at Y" cell with the "what does Y
    # first lose" cell would render two different Ys.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        # next direction: enterprise has no rung above -> both None.
        n_unl = ent.next_tier_unlocks_at(src)
        n_loc = ent.next_tier_locks_at(src)
        if n_unl is None:
            assert n_loc is None, src
        else:
            assert n_loc is not None, src
            assert n_unl["tier"] == n_loc["tier"], src
        # previous direction: oss / cloud_free have no rung below -> both None.
        p_unl = ent.previous_tier_unlocks_at(src)
        p_loc = ent.previous_tier_locks_at(src)
        if p_unl is None:
            assert p_loc is None, src
        else:
            assert p_loc is not None, src
            assert p_unl["tier"] == p_loc["tier"], src


# ── /api/entitlement/next-tier-locks-at ──────────────────────────────────────


def test_api_next_locks_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-locks-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_locks_at_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-locks-at?tier=%20%20")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_locks_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/next-tier-locks-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_next_locks_at_envelope_shape(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_next_locks_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={ent.TIER_OSS}")
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_next_locks_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(
            f"/api/entitlement/next-tier-locks-at?tier={src}"
        )
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.next_tier_locks_at(src), src


def test_api_next_locks_at_ceiling_returns_200_with_null_slots(client, ent):
    # Enterprise as source -> no rung above. Endpoint keeps 200 with a
    # populated envelope and null target / row so the pricing UI does
    # not have to status-code-branch to render "top of ladder".
    resp = client.get(
        f"/api/entitlement/next-tier-locks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_api_next_locks_at_case_insensitive_input(client, ent):
    resp = client.get("/api/entitlement/next-tier-locks-at?tier=%20OSS%20")
    assert resp.status_code == 200
    body = resp.get_json()
    # The endpoint canonicalises the source to lowercase before echoing
    # it back so a downstream renderer can key its response cache on the
    # canonical id.
    assert body["tier"] == ent.TIER_OSS


def test_api_next_locks_at_row_is_target_anchored(client, ent):
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={src}")
        body = resp.get_json()
        assert body["row"] is not None, src
        # row.tier IS envelope.target (target-anchored) -- the same
        # invariant the batch tests pin cross-envelope.
        assert body["row"]["tier"] == body["target"], src
        assert body["row"]["tier_rank"] == body["target_rank"], src
        assert body["row"]["tier_label"] == body["target_label"], src


def test_api_next_locks_at_row_lost_slice_matches_set_identity(client, ent):
    # Cross-family set-identity at the endpoint layer: row.lost_features
    # == tier_unlocks(next_of(target)).features for every source whose
    # target has a rung above. Pins the endpoint's rendering of the
    # marginal-loss slice against the marginal-grant builder so the two
    # views cannot silently desync at the wire.
    for src in ent._PURCHASABLE_TIERS:
        resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={src}")
        body = resp.get_json()
        if body["target"] is None:
            assert body["row"] is None, src
            continue
        two_up = ent._next_purchasable_tier_after(body["target"])
        if two_up is None:
            # target is at the ceiling -- lost lists collapse to [].
            assert body["row"]["lost_features"] == [], src
            assert body["row"]["lost_runtimes"] == [], src
            continue
        two_up_row = ent.tier_unlocks(two_up)
        assert body["row"]["lost_features"] == two_up_row["features"], src
        assert body["row"]["lost_runtimes"] == two_up_row["runtimes"], src


def test_api_next_locks_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_locks_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    # Grace-shape envelope: source echoed verbatim, row null.
    assert body["tier"] == ent.TIER_OSS
    # The endpoint's row is populated from next_tier_locks_at() -- when
    # THAT raises, the outer try / except returns the fallback envelope
    # with row=None.
    assert body["row"] is None


def test_api_next_locks_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    monkeypatch.setattr(ent, "next_tier_locks_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-locks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["row"] is None


# ── /api/entitlement/previous-tier-locks-at ──────────────────────────────────


def test_api_previous_locks_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/previous-tier-locks-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_previous_locks_at_blank_tier_is_400(client):
    resp = client.get(
        "/api/entitlement/previous-tier-locks-at?tier=%20%20"
    )
    assert resp.status_code == 400


def test_api_previous_locks_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/previous-tier-locks-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_previous_locks_at_envelope_shape(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-locks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_previous_locks_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-locks-at?tier={ent.TIER_ENTERPRISE}"
    )
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_previous_locks_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={src}"
        )
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.previous_tier_locks_at(src), src


def test_api_previous_locks_at_floor_returns_200_with_null_slots(client, ent):
    # OSS / cloud_free as source -> no rung below. Endpoint keeps 200
    # with a populated envelope and null target / row.
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={floor}"
        )
        assert resp.status_code == 200, floor
        body = resp.get_json()
        assert body["tier"] == floor
        assert body["tier_label"] == ent.tier_label(floor)
        assert body["target"] is None
        assert body["target_label"] is None
        assert body["target_rank"] is None
        assert body["row"] is None


def test_api_previous_locks_at_case_insensitive_input(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-locks-at?tier=%20ENTERPRISE%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_api_previous_locks_at_row_is_target_anchored(client, ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={src}"
        )
        body = resp.get_json()
        assert body["row"] is not None, src
        assert body["row"]["tier"] == body["target"], src
        assert body["row"]["tier_rank"] == body["target_rank"], src
        assert body["row"]["tier_label"] == body["target_label"], src


def test_api_previous_locks_at_row_lost_slice_matches_set_identity(
    client, ent
):
    # Cross-family set-identity at the endpoint layer, mirror of the
    # next-direction test. Pins the endpoint's rendering of the marginal-
    # loss slice against the marginal-grant builder off the target's
    # own next-higher rung.
    for src in ent._PURCHASABLE_TIERS:
        resp = client.get(
            f"/api/entitlement/previous-tier-locks-at?tier={src}"
        )
        body = resp.get_json()
        if body["target"] is None:
            assert body["row"] is None, src
            continue
        two_up = ent._next_purchasable_tier_after(body["target"])
        if two_up is None:
            assert body["row"]["lost_features"] == [], src
            assert body["row"]["lost_runtimes"] == [], src
            continue
        two_up_row = ent.tier_unlocks(two_up)
        assert body["row"]["lost_features"] == two_up_row["features"], src
        assert body["row"]["lost_runtimes"] == two_up_row["runtimes"], src


def test_api_previous_locks_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_locks_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-locks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["row"] is None


def test_api_previous_locks_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    monkeypatch.setattr(ent, "previous_tier_locks_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-locks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["row"] is None


# ── cross-endpoint pins ──────────────────────────────────────────────────────


def test_api_scalar_endpoints_target_axis_matches_diff_endpoints(client, ent):
    # The locks scalar endpoint and the diff scalar endpoint MUST agree
    # on the envelope target axis for every valid source -- otherwise a
    # pricing card that fetches both would render two different Ys for
    # the same "step X -> Y" row. Both endpoints wrap their row in the
    # same envelope shape (``tier`` / ``tier_label`` / ``tier_rank`` /
    # ``target`` / ``target_label`` / ``target_rank`` / ``row``) so the
    # target axis lives on the envelope, and the diff endpoint's inner
    # ``row["to"]`` must also byte-equal the envelope target.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        for direction in ("next", "previous"):
            loc = client.get(
                f"/api/entitlement/{direction}-tier-locks-at?tier={src}"
            ).get_json()
            diff = client.get(
                f"/api/entitlement/{direction}-tier-diff-at?tier={src}"
            ).get_json()
            assert loc["target"] == diff["target"], (direction, src)
            assert loc["target_rank"] == diff["target_rank"], (direction, src)
            assert loc["target_label"] == diff["target_label"], (direction, src)
            # The diff endpoint's inner ``row["to"]`` echoes the target on
            # the envelope -- pins the diff endpoint's row-vs-envelope
            # target agreement, and by transitivity keeps the locks
            # envelope target aligned with the diff row's ``to`` field.
            if diff["row"] is not None:
                assert loc["target"] == diff["row"]["to"], (direction, src)


def test_api_scalar_endpoints_target_axis_matches_unlocks_endpoints(
    client, ent
):
    # The locks scalar endpoint and the unlocks scalar endpoint MUST
    # agree on the envelope target axis for every valid source and both
    # directions -- otherwise the "what's new at Y" pricing cell and
    # the "what does Y first lose" pricing cell would render two
    # different Ys for the same rung.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        for direction in ("next", "previous"):
            loc = client.get(
                f"/api/entitlement/{direction}-tier-locks-at?tier={src}"
            ).get_json()
            unl = client.get(
                f"/api/entitlement/{direction}-tier-unlocks-at?tier={src}"
            ).get_json()
            assert loc["target"] == unl["target"], (direction, src)
            assert loc["target_rank"] == unl["target_rank"], (direction, src)
            assert loc["target_label"] == unl["target_label"], (direction, src)


def test_api_scalar_endpoints_agree_with_batch_row_slot(client, ent):
    # The scalar endpoint MUST byte-equal the batch endpoint's row slot
    # for the same source across both directions -- pins the scalar-vs-
    # batch parity documented on the batch surface, from the endpoint
    # side (helper-side parity is pinned in the raw-function tests above).
    for direction, batch_key in (
        ("next", "next"),
        ("previous", "previous"),
    ):
        batch = client.get(
            f"/api/entitlement/{batch_key}-tier-locks-at-batch"
        ).get_json()
        by_tier = {env["tier"]: env for env in batch["tiers"]}
        for src in ent._PURCHASABLE_TIERS:
            scalar = client.get(
                f"/api/entitlement/{direction}-tier-locks-at?tier={src}"
            ).get_json()
            assert by_tier[src]["row"] == scalar["row"], (direction, src)
            assert by_tier[src]["target"] == scalar["target"], (direction, src)
