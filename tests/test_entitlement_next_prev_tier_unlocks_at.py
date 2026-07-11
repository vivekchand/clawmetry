"""Tests for ``next_tier_unlocks_at`` / ``previous_tier_unlocks_at`` --
scalar what-if siblings of the live ``Entitlement.next_tier_unlocks`` /
``Entitlement.previous_tier_unlocks`` instance methods, plus the
companion ``/api/entitlement/{next,previous}-tier-unlocks-at?tier=<src>``
endpoints.

Scalar counterpart of the ``_at_batch`` sibling pinned in #3656 -- where
the batch answers "what does the rung above / below X first unlock"
across every entry in :data:`_PURCHASABLE_TIERS` in one pass, the scalar
answers the same what-if one source at a time and never wraps the row
in an envelope (that framing lives on the endpoint, not the raw helper).

Unlike ``next_tier_diff_at`` / ``previous_tier_diff_at`` -- which surface
the full ``tier_diff`` payload with ``row["from"]`` byte-equal to the
caller-supplied source -- these helpers surface the target's own
:func:`tier_unlocks` row (target-anchored: ``row["previous_tier"]`` is
the target's natural next-lower purchasable, NOT the caller-supplied
source). That mirrors the live ``Entitlement.{next,previous}_tier_unlocks``
posture and is the shape a pricing-comparison card renders when it wants
"what's new at Pro" not "the diff from OSS to Pro".

Pins covered here:

* ``next_tier_unlocks_at(tier)`` byte-equals
  ``tier_unlocks(_next_purchasable_tier_after(tier))`` across every
  valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``previous_tier_unlocks_at`` against
  ``_previous_purchasable_tier_before``
* the returned row is target-anchored: ``row["tier"]`` is the resolved
  target (NOT the caller-supplied source) and ``row["previous_tier"]``
  is that target's natural next-lower purchasable
* row features / runtimes byte-equal :func:`next_tier_diff_at` /
  :func:`previous_tier_diff_at` ``added_features`` /
  ``added_runtimes`` on the same source -- the scalar unlocks IS the
  grant slice of the scalar diff, so the two scalar what-ifs never
  silently desync
* the scalar row byte-equals the ``row`` slot of the ``_at_batch``
  envelope for the same source -- pins the scalar-vs-batch parity
  documented in :func:`next_tier_unlocks_at_batch` for the scalar
  side (the batch tests pin the mirror direction)
* at the ceiling / floor (no rung strictly above / below source) both
  helpers return ``None``, not an empty dict, so a caller can render
  "you're at the top / bottom" copy from a truthy check
* trial-as-source resolves the same way the diff ``_at`` family does:
  next -> enterprise, previous -> cloud_starter
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


_UNLOCKS_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "previous_tier",
    "previous_tier_label",
    "previous_tier_rank",
    "features",
    "runtimes",
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
    Enforcement off by default (grace mode) -- the unlocks ``_at``
    family is catalogue-derived and independent of the resolver, so the
    fixture only needs to keep the live resolver from surprising the
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


# ── next_tier_unlocks_at ─────────────────────────────────────────────────────


def test_next_unlocks_at_matches_explicit_composition(ent):
    # The convenience is tier_unlocks(_next_purchasable_tier_after(tier)).
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
        assert ent.next_tier_unlocks_at(src) == ent.tier_unlocks(nxt), src


def test_next_unlocks_at_returns_none_at_ceiling(ent):
    # Enterprise has no rung above -> None, mirroring the live method.
    assert ent.next_tier_unlocks_at(ent.TIER_ENTERPRISE) is None


def test_next_unlocks_at_row_shape(ent):
    body = ent.next_tier_unlocks_at(ent.TIER_OSS)
    assert body is not None
    assert set(body.keys()) == _UNLOCKS_ROW_KEYS
    # Row is target-anchored: row.tier IS the resolved target
    # (cloud_starter for OSS), NOT the caller-supplied source. That's
    # the key differentiator vs next_tier_diff_at which pins row.from
    # to the caller-supplied source.
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    # Sorted for stable rendering.
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


def test_next_unlocks_at_row_previous_tier_is_target_natural_prev(ent):
    # row.previous_tier is the target's natural next-lower purchasable,
    # NOT the caller-supplied source. Byte-equals what the live
    # /next-tier-unlocks surfaces off the resolver.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        target = ent._next_purchasable_tier_after(src)
        assert target is not None, src
        body = ent.next_tier_unlocks_at(src)
        assert body is not None, src
        assert body["previous_tier"] == ent.tier_unlocks(target)["previous_tier"], src


def test_next_unlocks_at_row_target_agrees_with_row_tier(ent):
    # For every valid source, the row.tier field IS the target the
    # scalar helper resolved to -- the invariant the batch test pins
    # cross-envelope (env.row.tier == env.target).
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        body = ent.next_tier_unlocks_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["tier"] == target, src


def test_next_unlocks_at_target_axis_matches_diff_at(ent):
    # Cross-family target parity: the diff ``_at`` scalar and the
    # unlocks ``_at`` scalar MUST agree on the target rung for every
    # valid source, otherwise a pricing card that combines both to
    # render "step X -> Y: adds features F, capacity C" would surface
    # two different Ys.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        diff = ent.next_tier_diff_at(src)
        unl = ent.next_tier_unlocks_at(src)
        assert diff is not None, src
        assert unl is not None, src
        assert unl["tier"] == diff["to"], src


def test_next_unlocks_at_features_match_diff_at_added_features(ent):
    # The unlocks scalar's row.features MUST byte-equal the diff
    # scalar's row.added_features for every purchasable source -- the
    # scalar-side companion of the ``_at_batch`` per-slice parity test.
    # Unlocks IS the grant slice of the diff.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        unl = ent.next_tier_unlocks_at(src)
        diff = ent.next_tier_diff_at(src)
        assert unl is not None and diff is not None, src
        assert unl["features"] == diff["added_features"], src
        assert unl["runtimes"] == diff["added_runtimes"], src


def test_next_unlocks_at_matches_batch_row_slot(ent):
    # Batch-vs-scalar parity from the scalar side: the ``_at_batch``
    # envelope's row slot for a given source MUST byte-equal the scalar
    # helper for the same source. The batch tests pin the mirror
    # direction (env.row == scalar for every env); this pins it from
    # the scalar side and defends against the batch drifting silently.
    by_tier = {env["tier"]: env for env in ent.next_tier_unlocks_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.next_tier_unlocks_at(src), src


def test_next_unlocks_at_matches_live_tier_unlocks_of_target(ent):
    # Anchoring the scalar what-if to the live cumulative accessor
    # keeps the ``_at`` helper from silently re-deriving unlocks off a
    # different code path.
    live = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        row = ent.next_tier_unlocks_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == live[target], src


def test_next_unlocks_at_trial_resolves_to_enterprise(ent):
    # Trial-as-source in the ``_at`` family walks past same-rank trial
    # to the strictly-higher rung; enterprise is the ceiling of
    # _PURCHASABLE_TIERS so the trial what-if answers enterprise.
    row = ent.next_tier_unlocks_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_ENTERPRISE


def test_next_unlocks_at_trims_and_lowercases(ent):
    body = ent.next_tier_unlocks_at("  OSS  ")
    assert body == ent.tier_unlocks(ent.TIER_CLOUD_STARTER)


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_next_unlocks_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_unlocks_at(bad) is None


def test_next_unlocks_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.next_tier_unlocks_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_unlocks_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_next_unlocks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_unlocks_at(ent.TIER_OSS)
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_next_unlocks_at_swallows_builder_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_unlocks", boom)
    assert ent.next_tier_unlocks_at(ent.TIER_OSS) is None


def test_next_unlocks_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    assert ent.next_tier_unlocks_at(ent.TIER_OSS) is None


# ── previous_tier_unlocks_at ─────────────────────────────────────────────────


def test_previous_unlocks_at_matches_explicit_composition(ent):
    # Convenience is tier_unlocks(_previous_purchasable_tier_before(tier)).
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_unlocks_at(src) == ent.tier_unlocks(prv), src


def test_previous_unlocks_at_returns_none_at_floor(ent):
    # OSS / cloud_free sit at rank 0 -- nothing strictly below.
    assert ent.previous_tier_unlocks_at(ent.TIER_OSS) is None
    assert ent.previous_tier_unlocks_at(ent.TIER_CLOUD_FREE) is None


def test_previous_unlocks_at_row_shape(ent):
    body = ent.previous_tier_unlocks_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert set(body.keys()) == _UNLOCKS_ROW_KEYS
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["tier"] == prv
    assert body["tier_label"] == ent.tier_label(prv)
    assert body["tier_rank"] == ent.tier_rank(prv)
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


def test_previous_unlocks_at_row_target_agrees_with_row_tier(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        body = ent.previous_tier_unlocks_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["tier"] == target, src


def test_previous_unlocks_at_row_previous_tier_is_target_natural_prev(ent):
    # row.previous_tier is the *target's* natural next-lower purchasable,
    # NOT the caller-supplied source -- the target-anchored posture the
    # live /previous-tier-unlocks endpoint surfaces.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(src)
        assert target is not None, src
        body = ent.previous_tier_unlocks_at(src)
        assert body is not None, src
        assert body["previous_tier"] == ent.tier_unlocks(target)["previous_tier"], src


def test_previous_unlocks_at_target_axis_matches_diff_at(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        diff = ent.previous_tier_diff_at(src)
        unl = ent.previous_tier_unlocks_at(src)
        assert diff is not None, src
        assert unl is not None, src
        assert unl["tier"] == diff["to"], src


def test_previous_unlocks_at_grant_slice_matches_diff_still_granted(ent):
    # In the downgrade direction, the *diff* pins added_features to the
    # features that would newly appear at the rung below (empty in the
    # standard ladder, since a lower rung strictly loses features).
    # The *unlocks* pins row.features / row.runtimes to the target's
    # OWN marginal-unlocks row (target-anchored), NOT the source diff's
    # added-features slice. That posture difference is why the previous-
    # direction test asserts the anchoring (target-anchored) rather than
    # the added-features parity that holds in the next-direction.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        target = ent._previous_purchasable_tier_before(src)
        assert target is not None, src
        unl = ent.previous_tier_unlocks_at(src)
        assert unl is not None, src
        # The row is byte-equal to :func:`tier_unlocks` of the target
        # (i.e. the target's OWN marginal-unlocks row), so the features
        # slice is the *target-vs-rung-below-target* set difference --
        # NOT the source-anchored diff's added_features.
        assert unl == ent.tier_unlocks(target), src


def test_previous_unlocks_at_matches_batch_row_slot(ent):
    by_tier = {env["tier"]: env for env in ent.previous_tier_unlocks_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.previous_tier_unlocks_at(src), src


def test_previous_unlocks_at_matches_live_tier_unlocks_of_target(ent):
    live = {row["tier"]: row for row in ent.tier_unlocks_batch()}
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        row = ent.previous_tier_unlocks_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == live[target], src


def test_previous_unlocks_at_trial_resolves_to_cloud_starter(ent):
    row = ent.previous_tier_unlocks_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_CLOUD_STARTER


def test_previous_unlocks_at_trims_and_lowercases(ent):
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert ent.previous_tier_unlocks_at("  ENTERPRISE  ") == ent.tier_unlocks(prv)


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_previous_unlocks_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_unlocks_at(bad) is None


def test_previous_unlocks_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.previous_tier_unlocks_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.previous_tier_unlocks_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_previous_unlocks_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_unlocks_at(ent.TIER_ENTERPRISE)
    assert body is not None
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["tier"] == prv


def test_previous_unlocks_at_swallows_builder_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_unlocks", boom)
    assert ent.previous_tier_unlocks_at(ent.TIER_ENTERPRISE) is None


def test_previous_unlocks_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    assert ent.previous_tier_unlocks_at(ent.TIER_ENTERPRISE) is None


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
    assert ent.next_tier_unlocks_at(ent.TIER_ENTERPRISE) is None
    assert ent.previous_tier_unlocks_at(ent.TIER_OSS) is None
    # But the mirror direction is still populated -- ceiling still has
    # a rung below, floor still has a rung above.
    assert ent.previous_tier_unlocks_at(ent.TIER_ENTERPRISE) is not None
    assert ent.next_tier_unlocks_at(ent.TIER_OSS) is not None


# ── /api/entitlement/next-tier-unlocks-at ────────────────────────────────────


def test_api_next_unlocks_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-unlocks-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_unlocks_at_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-unlocks-at?tier=%20%20")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_unlocks_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/next-tier-unlocks-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_next_unlocks_at_envelope_shape(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-unlocks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_next_unlocks_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-unlocks-at?tier={ent.TIER_OSS}")
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_next_unlocks_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(
            f"/api/entitlement/next-tier-unlocks-at?tier={src}"
        )
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.next_tier_unlocks_at(src), src


def test_api_next_unlocks_at_ceiling_returns_200_with_null_slots(client, ent):
    # Enterprise as source -> no rung above. Endpoint keeps 200 with a
    # populated envelope and null target / row so the pricing UI does
    # not have to status-code-branch to render "top of ladder".
    resp = client.get(
        f"/api/entitlement/next-tier-unlocks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_api_next_unlocks_at_case_insensitive_input(client, ent):
    resp = client.get("/api/entitlement/next-tier-unlocks-at?tier=%20OSS%20")
    assert resp.status_code == 200
    body = resp.get_json()
    # The endpoint canonicalises the source to lowercase before echoing
    # it back so a downstream renderer can key its response cache on the
    # canonical id.
    assert body["tier"] == ent.TIER_OSS


def test_api_next_unlocks_at_row_is_target_anchored(client, ent):
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        resp = client.get(f"/api/entitlement/next-tier-unlocks-at?tier={src}")
        body = resp.get_json()
        assert body["row"] is not None, src
        # row.tier IS envelope.target (target-anchored) -- the same
        # invariant the batch tests pin cross-envelope.
        assert body["row"]["tier"] == body["target"], src
        assert body["row"]["tier_rank"] == body["target_rank"], src
        assert body["row"]["tier_label"] == body["target_label"], src


def test_api_next_unlocks_at_row_features_match_diff_at_added(client, ent):
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        unl = client.get(
            f"/api/entitlement/next-tier-unlocks-at?tier={src}"
        ).get_json()
        diff = client.get(
            f"/api/entitlement/next-tier-diff-at?tier={src}"
        ).get_json()
        assert unl["row"] is not None, src
        assert diff["row"] is not None, src
        assert unl["row"]["features"] == diff["row"]["added_features"], src
        assert unl["row"]["runtimes"] == diff["row"]["added_runtimes"], src


def test_api_next_unlocks_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_unlocks_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-unlocks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    # Grace-shape envelope: source echoed verbatim, target / row null.
    assert body["tier"] == ent.TIER_OSS
    # The endpoint's row is populated from next_tier_unlocks_at() -- when
    # THAT raises, the row must collapse to None. The endpoint's inner
    # tier_label / _next_purchasable_tier_after calls stay live so the
    # source metadata and target axis remain populated where they can be.
    assert body["row"] is None


def test_api_next_unlocks_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    monkeypatch.setattr(ent, "next_tier_unlocks_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-unlocks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["row"] is None


# ── /api/entitlement/previous-tier-unlocks-at ────────────────────────────────


def test_api_previous_unlocks_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/previous-tier-unlocks-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_previous_unlocks_at_blank_tier_is_400(client):
    resp = client.get(
        "/api/entitlement/previous-tier-unlocks-at?tier=%20%20"
    )
    assert resp.status_code == 400


def test_api_previous_unlocks_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/previous-tier-unlocks-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_previous_unlocks_at_envelope_shape(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-unlocks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_previous_unlocks_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-unlocks-at?tier={ent.TIER_ENTERPRISE}"
    )
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_previous_unlocks_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(
            f"/api/entitlement/previous-tier-unlocks-at?tier={src}"
        )
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.previous_tier_unlocks_at(src), src


def test_api_previous_unlocks_at_floor_returns_200_with_null_slots(client, ent):
    # OSS / cloud_free as source -> no rung below. Endpoint keeps 200
    # with a populated envelope and null target / row.
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-unlocks-at?tier={floor}"
        )
        assert resp.status_code == 200, floor
        body = resp.get_json()
        assert body["tier"] == floor
        assert body["tier_label"] == ent.tier_label(floor)
        assert body["target"] is None
        assert body["target_label"] is None
        assert body["target_rank"] is None
        assert body["row"] is None


def test_api_previous_unlocks_at_case_insensitive_input(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-unlocks-at?tier=%20ENTERPRISE%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_api_previous_unlocks_at_row_is_target_anchored(client, ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-unlocks-at?tier={src}"
        )
        body = resp.get_json()
        assert body["row"] is not None, src
        assert body["row"]["tier"] == body["target"], src
        assert body["row"]["tier_rank"] == body["target_rank"], src
        assert body["row"]["tier_label"] == body["target_label"], src


def test_api_previous_unlocks_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_unlocks_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-unlocks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["row"] is None


def test_api_previous_unlocks_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    monkeypatch.setattr(ent, "previous_tier_unlocks_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-unlocks-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["row"] is None


# ── cross-endpoint pins ──────────────────────────────────────────────────────


def test_api_scalar_endpoints_target_axis_matches_diff_endpoints(client, ent):
    # The unlocks scalar endpoint and the diff scalar endpoint MUST agree
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
            unl = client.get(
                f"/api/entitlement/{direction}-tier-unlocks-at?tier={src}"
            ).get_json()
            diff = client.get(
                f"/api/entitlement/{direction}-tier-diff-at?tier={src}"
            ).get_json()
            assert unl["target"] == diff["target"], (direction, src)
            assert unl["target_rank"] == diff["target_rank"], (direction, src)
            assert unl["target_label"] == diff["target_label"], (direction, src)
            # The diff endpoint's inner ``row["to"]`` echoes the target on
            # the envelope -- pins the diff endpoint's row-vs-envelope
            # target agreement, and by transitivity keeps the unlocks
            # envelope target aligned with the diff row's ``to`` field.
            if diff["row"] is not None:
                assert unl["target"] == diff["row"]["to"], (direction, src)


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
            f"/api/entitlement/{batch_key}-tier-unlocks-at-batch"
        ).get_json()
        by_tier = {env["tier"]: env for env in batch["tiers"]}
        for src in ent._PURCHASABLE_TIERS:
            scalar = client.get(
                f"/api/entitlement/{direction}-tier-unlocks-at?tier={src}"
            ).get_json()
            assert by_tier[src]["row"] == scalar["row"], (direction, src)
            assert by_tier[src]["target"] == scalar["target"], (direction, src)
