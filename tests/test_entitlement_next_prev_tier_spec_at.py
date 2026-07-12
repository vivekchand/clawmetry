"""Tests for ``next_tier_spec_at`` / ``previous_tier_spec_at`` -- scalar
what-if siblings of the live ``Entitlement.next_tier_spec`` /
``Entitlement.previous_tier_spec`` instance methods, plus the companion
``/api/entitlement/{next,previous}-tier-spec-at?tier=<src>`` endpoints.

Scalar counterpart of the ``_at_batch`` sibling pinned in
``test_entitlement_next_prev_tier_spec_at_batch.py`` -- where the batch
answers "what does the rung above / below X look like" across every
entry in :data:`_PURCHASABLE_TIERS` in one pass, the scalar answers the
same what-if one source at a time and never wraps the row in an envelope
(that framing lives on the endpoint, not the raw helper).

Unlike ``next_tier_unlocks_at`` / ``next_tier_locks_at`` (marginal grants
/ marginal losses), these helpers surface the target's full
:func:`tier_spec_at` row -- the cumulative ``id / label / is_paid /
is_current / rank / unlocks_paid_runtimes / retention_days / channel_limit
/ node_limit / features / runtimes`` descriptor of the rung above / below
the caller-supplied source. That's the shape a pricing-comparison card
renders when it wants "the full descriptor of Pro" not just "what changes
stepping OSS -> Pro".

Pins covered here:

* ``next_tier_spec_at(tier)`` byte-equals
  ``tier_spec_at(tier, _next_purchasable_tier_after(tier))`` across every
  valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``previous_tier_spec_at`` against
  ``_previous_purchasable_tier_before``
* the returned row's ``id`` is the resolved target (NOT the caller-
  supplied source) and its ``rank`` / ``label`` match that target
* on populated rows ``is_current`` is always ``False`` -- target is by
  definition strictly above / below source, so it cannot equal it
* the scalar row byte-equals the ``row`` slot of the ``_at_batch``
  envelope for the same source -- pins the scalar-vs-batch parity
  documented in :func:`next_tier_spec_at_batch` from the scalar side
  (the batch tests pin the mirror direction)
* the scalar target axis byte-equals :func:`next_tier_diff_at` /
  :func:`previous_tier_diff_at` ``to`` on the same source and the
  unlocks / locks scalar target axes -- the five source-anchored ``_at``
  helpers cannot disagree on the target rung
* at the ceiling / floor (no rung strictly above / below source) both
  helpers return ``None``, not an empty dict, so a caller can render
  "you're at the top / bottom" copy from a truthy check
* trial-as-source resolves the same way the diff / unlocks ``_at`` family
  does: next -> enterprise, previous -> cloud_starter
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* unknown / empty / ``None`` / non-string source returns ``None``;
  builder / stepper failures short-circuit to ``None``, never raise
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


_SPEC_ROW_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
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
    Enforcement off by default (grace mode) -- the spec ``_at`` family
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


# ── next_tier_spec_at ────────────────────────────────────────────────────────


def test_next_spec_at_matches_explicit_composition(ent):
    # The convenience is tier_spec_at(tier, _next_purchasable_tier_after(tier)).
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
        assert ent.next_tier_spec_at(src) == ent.tier_spec_at(src, nxt), src


def test_next_spec_at_returns_none_at_ceiling(ent):
    # Enterprise has no rung above -> None, mirroring the live method.
    assert ent.next_tier_spec_at(ent.TIER_ENTERPRISE) is None


def test_next_spec_at_row_shape(ent):
    body = ent.next_tier_spec_at(ent.TIER_OSS)
    assert body is not None
    assert set(body.keys()) == _SPEC_ROW_KEYS
    # Row.id IS the resolved target (cloud_starter for OSS), NOT the
    # caller-supplied source -- the target-anchored posture the batch
    # tests pin cross-envelope. Features / runtimes are sorted for
    # stable rendering (matches tier_spec_at's own convention).
    assert body["id"] == ent.TIER_CLOUD_STARTER
    assert body["label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    # ``row["rank"]`` is the *catalogue-position* index into
    # :data:`_TIER_ORDER` (which slots TIER_TRIAL between cloud_free and
    # cloud_starter), NOT the ladder-rank from :data:`_TIER_RANK` --
    # they differ for every tier at or above cloud_starter. Pinning to
    # ``_TIER_ORDER.index`` keeps the two ranks from silently merging.
    assert body["rank"] == ent._TIER_ORDER.index(ent.TIER_CLOUD_STARTER)
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


def test_next_spec_at_populated_row_is_current_false(ent):
    # Target is by definition strictly above source, so it cannot equal
    # it -- ``is_current`` is therefore always False on a populated row.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        body = ent.next_tier_spec_at(src)
        assert body is not None, src
        assert body["is_current"] is False, src


def test_next_spec_at_row_id_agrees_with_stepper(ent):
    # For every valid source, the row.id field IS the target the scalar
    # helper resolved to -- the invariant the batch test pins cross-
    # envelope (env.row.id == env.target). Row.rank is the catalogue-
    # position index into :data:`_TIER_ORDER`, NOT the ladder-rank from
    # :data:`_TIER_RANK` -- they diverge from cloud_starter upward.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        body = ent.next_tier_spec_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["id"] == target, src
        assert body["rank"] == ent._TIER_ORDER.index(target), src
        assert body["label"] == ent.tier_label(target), src


def test_next_spec_at_target_axis_matches_diff_at(ent):
    # Cross-family target parity: the diff ``_at`` scalar and the spec
    # ``_at`` scalar MUST agree on the target rung for every valid
    # source, otherwise a pricing card that combines both to render
    # "step X -> Y: full descriptor + diff" would surface two different
    # Ys.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        diff = ent.next_tier_diff_at(src)
        spec = ent.next_tier_spec_at(src)
        assert diff is not None, src
        assert spec is not None, src
        assert spec["id"] == diff["to"], src


def test_next_spec_at_target_axis_matches_unlocks_locks_at(ent):
    # Same cross-family invariant against the unlocks / locks scalar
    # ``_at`` helpers -- all four source-anchored ``_at`` scalars MUST
    # resolve to the same target for a given source, otherwise a
    # pricing surface that folds spec + unlocks + locks + diff into one
    # cell would render conflicting target rungs.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        spec = ent.next_tier_spec_at(src)
        unl = ent.next_tier_unlocks_at(src)
        locks = ent.next_tier_locks_at(src)
        assert spec is not None, src
        assert unl is not None, src
        assert locks is not None, src
        assert spec["id"] == unl["tier"], src
        assert spec["id"] == locks["tier"], src


def test_next_spec_at_matches_batch_row_slot(ent):
    # Batch-vs-scalar parity from the scalar side: the ``_at_batch``
    # envelope's row slot for a given source MUST byte-equal the scalar
    # helper for the same source. The batch tests pin the mirror
    # direction (env.row == scalar for every env); this pins it from
    # the scalar side and defends against the batch drifting silently.
    by_tier = {env["tier"]: env for env in ent.next_tier_spec_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.next_tier_spec_at(src), src


def test_next_spec_at_matches_live_tier_spec_at_of_target(ent):
    # Anchoring the scalar what-if to the live cumulative accessor keeps
    # the ``_at`` helper from silently re-deriving the row off a
    # different code path.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        row = ent.next_tier_spec_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == ent.tier_spec_at(src, target), src


def test_next_spec_at_trial_resolves_to_enterprise(ent):
    # Trial-as-source in the ``_at`` family walks past same-rank trial
    # to the strictly-higher rung; enterprise is the ceiling of
    # _PURCHASABLE_TIERS so the trial what-if answers enterprise.
    row = ent.next_tier_spec_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["id"] == ent.TIER_ENTERPRISE


def test_next_spec_at_trims_and_lowercases(ent):
    nxt = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert ent.next_tier_spec_at("  OSS  ") == ent.tier_spec_at(ent.TIER_OSS, nxt)


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_next_spec_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_spec_at(bad) is None


def test_next_spec_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.next_tier_spec_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.next_tier_spec_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_next_spec_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_spec_at(ent.TIER_OSS)
    assert body is not None
    assert body["id"] == ent.TIER_CLOUD_STARTER


def test_next_spec_at_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_spec_at", boom)
    assert ent.next_tier_spec_at(ent.TIER_OSS) is None


def test_next_spec_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    assert ent.next_tier_spec_at(ent.TIER_OSS) is None


# ── previous_tier_spec_at ────────────────────────────────────────────────────


def test_previous_spec_at_matches_explicit_composition(ent):
    # Convenience is tier_spec_at(tier, _previous_purchasable_tier_before(tier)).
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_spec_at(src) == ent.tier_spec_at(src, prv), src


def test_previous_spec_at_returns_none_at_floor(ent):
    # OSS / cloud_free sit at rank 0 -- nothing strictly below.
    assert ent.previous_tier_spec_at(ent.TIER_OSS) is None
    assert ent.previous_tier_spec_at(ent.TIER_CLOUD_FREE) is None


def test_previous_spec_at_row_shape(ent):
    body = ent.previous_tier_spec_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert set(body.keys()) == _SPEC_ROW_KEYS
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["id"] == prv
    assert body["label"] == ent.tier_label(prv)
    # See ``next_spec_at_row_shape`` -- row.rank is the position in
    # :data:`_TIER_ORDER`, not the ladder-rank :data:`_TIER_RANK` value.
    assert body["rank"] == ent._TIER_ORDER.index(prv)
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


def test_previous_spec_at_populated_row_is_current_false(ent):
    # Target is by definition strictly below source, so it cannot equal
    # it -- ``is_current`` is therefore always False on a populated row.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        body = ent.previous_tier_spec_at(src)
        assert body is not None, src
        assert body["is_current"] is False, src


def test_previous_spec_at_row_id_agrees_with_stepper(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        body = ent.previous_tier_spec_at(src)
        if target is None:
            assert body is None, src
            continue
        assert body is not None, src
        assert body["id"] == target, src
        assert body["rank"] == ent._TIER_ORDER.index(target), src
        assert body["label"] == ent.tier_label(target), src


def test_previous_spec_at_target_axis_matches_diff_at(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        diff = ent.previous_tier_diff_at(src)
        spec = ent.previous_tier_spec_at(src)
        assert diff is not None, src
        assert spec is not None, src
        assert spec["id"] == diff["to"], src


def test_previous_spec_at_target_axis_matches_unlocks_locks_at(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        spec = ent.previous_tier_spec_at(src)
        unl = ent.previous_tier_unlocks_at(src)
        locks = ent.previous_tier_locks_at(src)
        assert spec is not None, src
        assert unl is not None, src
        assert locks is not None, src
        assert spec["id"] == unl["tier"], src
        assert spec["id"] == locks["tier"], src


def test_previous_spec_at_matches_batch_row_slot(ent):
    by_tier = {env["tier"]: env for env in ent.previous_tier_spec_at_batch()}
    for src in ent._PURCHASABLE_TIERS:
        assert by_tier[src]["row"] == ent.previous_tier_spec_at(src), src


def test_previous_spec_at_matches_live_tier_spec_at_of_target(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        row = ent.previous_tier_spec_at(src)
        if target is None:
            assert row is None, src
            continue
        assert row == ent.tier_spec_at(src, target), src


def test_previous_spec_at_trial_resolves_to_cloud_starter(ent):
    row = ent.previous_tier_spec_at(ent.TIER_TRIAL)
    assert row is not None
    assert row["id"] == ent.TIER_CLOUD_STARTER


def test_previous_spec_at_trims_and_lowercases(ent):
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert ent.previous_tier_spec_at("  ENTERPRISE  ") == ent.tier_spec_at(
        ent.TIER_ENTERPRISE, prv
    )


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus", []])
def test_previous_spec_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_spec_at(bad) is None


def test_previous_spec_at_grace_and_enforce_match(ent, monkeypatch):
    for src in ent._PURCHASABLE_TIERS:
        grace = ent.previous_tier_spec_at(src)
        monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        importlib.reload(ent)
        ent.invalidate()
        enforce = ent.previous_tier_spec_at(src)
        assert enforce == grace, src
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(ent)
        ent.invalidate()


def test_previous_spec_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_spec_at(ent.TIER_ENTERPRISE)
    assert body is not None
    prv = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["id"] == prv


def test_previous_spec_at_swallows_builder_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_spec_at", boom)
    assert ent.previous_tier_spec_at(ent.TIER_ENTERPRISE) is None


def test_previous_spec_at_swallows_stepper_exception(ent, monkeypatch):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    assert ent.previous_tier_spec_at(ent.TIER_ENTERPRISE) is None


# ── cross-direction pins ─────────────────────────────────────────────────────


def test_scalar_helpers_return_none_for_same_side_of_ceiling_and_floor(ent):
    # Semantic sanity: at the ceiling the *next* helper returns None; at
    # the floor the *previous* helper returns None. They MUST NOT swap.
    assert ent.next_tier_spec_at(ent.TIER_ENTERPRISE) is None
    assert ent.previous_tier_spec_at(ent.TIER_OSS) is None
    # But the mirror direction is still populated -- ceiling still has
    # a rung below, floor still has a rung above.
    assert ent.previous_tier_spec_at(ent.TIER_ENTERPRISE) is not None
    assert ent.next_tier_spec_at(ent.TIER_OSS) is not None


# ── /api/entitlement/next-tier-spec-at ───────────────────────────────────────


def test_api_next_spec_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-spec-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_spec_at_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/next-tier-spec-at?tier=%20%20")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_next_spec_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/next-tier-spec-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_next_spec_at_envelope_shape(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_next_spec_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={ent.TIER_OSS}")
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_next_spec_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={src}")
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.next_tier_spec_at(src), src


def test_api_next_spec_at_ceiling_returns_200_with_null_slots(client, ent):
    # Enterprise as source -> no rung above. Endpoint keeps 200 with a
    # populated envelope and null target / row so the pricing UI does
    # not have to status-code-branch to render "top of ladder".
    resp = client.get(
        f"/api/entitlement/next-tier-spec-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_api_next_spec_at_case_insensitive_input(client, ent):
    resp = client.get("/api/entitlement/next-tier-spec-at?tier=%20OSS%20")
    assert resp.status_code == 200
    body = resp.get_json()
    # The endpoint canonicalises the source to lowercase before echoing
    # it back so a downstream renderer can key its response cache on the
    # canonical id.
    assert body["tier"] == ent.TIER_OSS


def test_api_next_spec_at_row_is_target_anchored(client, ent):
    # row.id IS envelope.target (target-anchored) -- the same invariant
    # the batch tests pin cross-envelope. Row.label agrees with
    # envelope.target_label. Row.rank sits on the *catalogue-position*
    # axis (:data:`_TIER_ORDER` index) while envelope.target_rank sits
    # on the *ladder-rank* axis (:data:`_TIER_RANK`) -- pin each to the
    # target's own value on the relevant axis so a consumer reading
    # either off the envelope gets the source of truth for that axis.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={src}")
        body = resp.get_json()
        assert body["row"] is not None, src
        assert body["row"]["id"] == body["target"], src
        assert body["row"]["label"] == body["target_label"], src
        assert body["target_rank"] == ent.tier_rank(body["target"]), src
        assert body["row"]["rank"] == ent._TIER_ORDER.index(body["target"]), src


def test_api_next_spec_at_row_is_current_false(client, ent):
    # Target is strictly above source on this endpoint, so the row's
    # is_current can never be True. Pinned at the endpoint layer so a
    # UI reading directly off the envelope can assume it.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        body = client.get(
            f"/api/entitlement/next-tier-spec-at?tier={src}"
        ).get_json()
        assert body["row"] is not None, src
        assert body["row"]["is_current"] is False, src


def test_api_next_spec_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_spec_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    # Grace-shape envelope: source echoed verbatim, target / row null.
    assert body["tier"] == ent.TIER_OSS
    # The endpoint's row is populated from next_tier_spec_at() -- when
    # THAT raises, the row must collapse to None. The endpoint's inner
    # tier_label / _next_purchasable_tier_after calls stay live so the
    # source metadata and target axis remain populated where they can be.
    assert body["row"] is None


def test_api_next_spec_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    monkeypatch.setattr(ent, "next_tier_spec_at", boom)
    resp = client.get(f"/api/entitlement/next-tier-spec-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["row"] is None


# ── /api/entitlement/previous-tier-spec-at ───────────────────────────────────


def test_api_previous_spec_at_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/previous-tier-spec-at")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "missing tier"


def test_api_previous_spec_at_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/previous-tier-spec-at?tier=%20%20")
    assert resp.status_code == 400


def test_api_previous_spec_at_unknown_tier_is_404_with_which(client):
    resp = client.get("/api/entitlement/previous-tier-spec-at?tier=bogus")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_previous_spec_at_envelope_shape(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-spec-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


def test_api_previous_spec_at_envelope_pins_source_and_target(client, ent):
    resp = client.get(
        f"/api/entitlement/previous-tier-spec-at?tier={ent.TIER_ENTERPRISE}"
    )
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    assert body["target"] == target
    assert body["target_label"] == ent.tier_label(target)
    assert body["target_rank"] == ent.tier_rank(target)


def test_api_previous_spec_at_envelope_row_matches_scalar_helper(client, ent):
    for src in ent._PURCHASABLE_TIERS + (ent.TIER_TRIAL,):
        resp = client.get(f"/api/entitlement/previous-tier-spec-at?tier={src}")
        assert resp.status_code == 200, src
        assert resp.get_json()["row"] == ent.previous_tier_spec_at(src), src


def test_api_previous_spec_at_floor_returns_200_with_null_slots(client, ent):
    # OSS / cloud_free as source -> no rung below. Endpoint keeps 200
    # with a populated envelope and null target / row.
    for floor in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-spec-at?tier={floor}"
        )
        assert resp.status_code == 200, floor
        body = resp.get_json()
        assert body["tier"] == floor
        assert body["tier_label"] == ent.tier_label(floor)
        assert body["target"] is None
        assert body["target_label"] is None
        assert body["target_rank"] is None
        assert body["row"] is None


def test_api_previous_spec_at_case_insensitive_input(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-spec-at?tier=%20ENTERPRISE%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_api_previous_spec_at_row_is_target_anchored(client, ent):
    # See ``next_spec_at_row_is_target_anchored`` for the row.rank vs
    # envelope.target_rank axis split -- pin each on its own axis so a
    # consumer reading either off the envelope has the source of truth.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        resp = client.get(
            f"/api/entitlement/previous-tier-spec-at?tier={src}"
        )
        body = resp.get_json()
        assert body["row"] is not None, src
        assert body["row"]["id"] == body["target"], src
        assert body["row"]["label"] == body["target_label"], src
        assert body["target_rank"] == ent.tier_rank(body["target"]), src
        assert body["row"]["rank"] == ent._TIER_ORDER.index(body["target"]), src


def test_api_previous_spec_at_row_is_current_false(client, ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        body = client.get(
            f"/api/entitlement/previous-tier-spec-at?tier={src}"
        ).get_json()
        assert body["row"] is not None, src
        assert body["row"]["is_current"] is False, src


def test_api_previous_spec_at_never_5xxs_on_builder_failure(
    client, ent, monkeypatch
):
    def boom(_):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_spec_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-spec-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["row"] is None


def test_api_previous_spec_at_5xx_free_on_total_meltdown(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("catastrophic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    monkeypatch.setattr(ent, "previous_tier_spec_at", boom)
    resp = client.get(
        f"/api/entitlement/previous-tier-spec-at?tier={ent.TIER_ENTERPRISE}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["row"] is None


# ── cross-endpoint pins ──────────────────────────────────────────────────────


def test_api_scalar_endpoints_target_axis_matches_diff_endpoints(client, ent):
    # The spec scalar endpoint and the diff scalar endpoint MUST agree on
    # the envelope target axis for every valid source -- otherwise a
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
            spec = client.get(
                f"/api/entitlement/{direction}-tier-spec-at?tier={src}"
            ).get_json()
            diff = client.get(
                f"/api/entitlement/{direction}-tier-diff-at?tier={src}"
            ).get_json()
            assert spec["target"] == diff["target"], (direction, src)
            assert spec["target_rank"] == diff["target_rank"], (direction, src)
            assert spec["target_label"] == diff["target_label"], (direction, src)
            if diff["row"] is not None:
                assert spec["target"] == diff["row"]["to"], (direction, src)


def test_api_scalar_endpoints_target_axis_matches_unlocks_locks_endpoints(
    client, ent
):
    # All four source-anchored scalar ``_at`` endpoints (spec / diff /
    # unlocks / locks) MUST agree on the envelope target axis for every
    # valid source. This is the cross-family invariant the pricing
    # surface relies on when it folds spec + diff + unlocks + locks into
    # one "step X -> Y" cell.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        for direction in ("next", "previous"):
            spec = client.get(
                f"/api/entitlement/{direction}-tier-spec-at?tier={src}"
            ).get_json()
            unl = client.get(
                f"/api/entitlement/{direction}-tier-unlocks-at?tier={src}"
            ).get_json()
            locks = client.get(
                f"/api/entitlement/{direction}-tier-locks-at?tier={src}"
            ).get_json()
            assert spec["target"] == unl["target"], (direction, src)
            assert spec["target"] == locks["target"], (direction, src)


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
            f"/api/entitlement/{batch_key}-tier-spec-at-batch"
        ).get_json()
        by_tier = {env["tier"]: env for env in batch["tiers"]}
        for src in ent._PURCHASABLE_TIERS:
            scalar = client.get(
                f"/api/entitlement/{direction}-tier-spec-at?tier={src}"
            ).get_json()
            assert by_tier[src]["row"] == scalar["row"], (direction, src)
            assert by_tier[src]["target"] == scalar["target"], (direction, src)
