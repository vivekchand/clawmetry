"""Tests for ``Entitlement.next_tier_spec`` / ``previous_tier_spec``, the
module-level convenience helpers, the scalar what-if
``next_tier_spec_at`` / ``previous_tier_spec_at`` helpers, and the four
companion ``/api/entitlement/{next,previous}-tier-spec[-at]`` endpoints.

Full :func:`tier_spec`-shape descriptor lens of the
``{next,previous}_tier_{diff,unlocks,locks,capacity_diff}`` family that
already exists: where those helpers return marginal step / capacity rows
between the resolved entitlement (or a hypothetical source ``_at``) and
the rung one above / below, these helpers return the FULL tier-row
descriptor of the rung above / below in :func:`tier_spec` shape (``id``,
``label``, ``is_paid``, ``is_current``, ``rank``,
``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
``node_limit``, ``features``, ``runtimes``) so a pricing-table cell can
hydrate the rung-above / rung-below column off ONE round-trip without
fetching the full catalogue and filtering client-side.

Pins covered here:

* method-vs-tier_spec identity for next/previous across every
  purchasable source -- the convenience cannot drift from the explicit
  ``tier_spec(self.next_purchasable_tier())`` composition
* ``next_tier_spec_at(tier)`` byte-equals
  ``tier_spec_at(tier, _next_purchasable_tier_after(tier))`` and the
  symmetric pin for previous
* ``is_current`` is always ``False`` on the returned row -- the target
  is by definition strictly above / below the source
* ceiling / floor returns ``None`` (Enterprise has no next, OSS /
  cloud_free has no previous)
* trial-as-source resolves the same way the sibling ``_at`` families
  do: next -> enterprise, previous -> cloud_starter
* unknown / empty / ``None`` / non-string source on the ``_at`` helpers
  returns ``None``
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a resolver failure short-circuits to
  ``None`` so the CTA surface keeps rendering
* the four API endpoints never 5xx: scalar endpoints surface a 200
  envelope with ``spec=null`` at the ceiling / floor; ``_at`` endpoints
  400 on missing input, 404 on unknown ids, and 200 with ``row=null``
  at the ceiling / floor; a synthesised resolver failure yields the
  grace-shape envelope on every surface
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_SPEC_KEYS = {
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

_AT_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "row",
}

_SCALAR_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "spec",
    "grace",
    "enforced",
}


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


# ── Entitlement.next_tier_spec ───────────────────────────────────────────────


def test_next_tier_spec_matches_tier_spec_at(ent):
    # next_tier_spec() is a convenience for
    # tier_spec_at(self.tier, next_purchasable_tier()) -- they must be
    # byte-equal across every purchasable source so a caller can use the
    # singular helper interchangeably. Delegates to tier_spec_at (not
    # tier_spec) so is_current is anchored on self.tier rather than the
    # live resolver -- the helper is self-anchored, not resolver-anchored.
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
        assert e.next_tier_spec() == ent.tier_spec_at(tier, nxt)


def test_next_tier_spec_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above
    # to upgrade to, so the convenience returns None just like
    # next_purchasable_tier().
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    assert e.next_tier_spec() is None


def test_next_tier_spec_shape(ent):
    # The row must carry the full tier_spec shape so a pricing-cell can
    # hydrate every column without a second round-trip.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    body = e.next_tier_spec()
    assert body is not None
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_PRO
    assert body["label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    # tier_spec carries the position-in-_TIER_ORDER rank, not the ladder
    # tier_rank value -- pin against the source-of-truth field.
    assert body["rank"] == ent._TIER_ORDER.index(ent.TIER_CLOUD_PRO)
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


def test_next_tier_spec_is_current_always_false(ent):
    # By definition the target is strictly above the source -- it can never
    # equal current, so is_current must always be False.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        body = e.next_tier_spec()
        assert body is not None
        assert body["is_current"] is False


def test_next_tier_spec_never_raises_on_resolver_failure(ent, monkeypatch):
    # If next_purchasable_tier blows up, the helper must swallow and return
    # None so the dashboard CTA keeps rendering rather than 500-ing.
    e = ent._oss_free()
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_spec() is None


# ── Entitlement.previous_tier_spec ───────────────────────────────────────────


def test_previous_tier_spec_matches_tier_spec_at(ent):
    # Symmetric to next_tier_spec: previous_tier_spec() must be byte-equal
    # to tier_spec_at(self.tier, previous_purchasable_tier()).
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert e.previous_tier_spec() == ent.tier_spec_at(tier, prev)


def test_previous_tier_spec_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below to step down to,
    # so the helper returns None mirroring previous_purchasable_tier().
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        assert e.previous_tier_spec() is None


def test_previous_tier_spec_shape(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    body = e.previous_tier_spec()
    assert body is not None
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_STARTER
    assert body["label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)


def test_previous_tier_spec_is_current_always_false(ent):
    # By definition the target is strictly below source -- can never equal
    # current.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        body = e.previous_tier_spec()
        assert body is not None
        assert body["is_current"] is False


def test_previous_tier_spec_never_raises_on_resolver_failure(ent, monkeypatch):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_spec() is None


# ── trial source resolution ──────────────────────────────────────────────────


def test_trial_next_spec_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro / self-hosted pro, so the next
    # strictly-higher purchasable rung is enterprise (rank 3).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.next_tier_spec()
    assert body is not None
    assert body["id"] == ent.TIER_ENTERPRISE


def test_trial_previous_spec_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter) -- the highest rank strictly below
    # trial's rank 2.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.previous_tier_spec()
    assert body is not None
    assert body["id"] == ent.TIER_CLOUD_STARTER


# ── grace vs enforce ─────────────────────────────────────────────────────────


def test_grace_and_enforce_yield_same_spec(ent, monkeypatch):
    # These helpers are catalogue-derived (off the static per-tier maps),
    # not gated -- so flipping enforce on must not change the body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_spec()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_spec()
    assert enforce_body == grace_body


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_level_next_helper_matches_method(ent):
    # The bare module-level helper resolves the current entitlement and
    # delegates, so it must agree with the bound method.
    assert ent.next_tier_spec() == ent.get_entitlement().next_tier_spec()


def test_module_level_previous_helper_matches_method(ent):
    assert (
        ent.previous_tier_spec() == ent.get_entitlement().previous_tier_spec()
    )


def test_module_level_next_helper_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_spec() is None


def test_module_level_previous_helper_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_spec() is None


# ── next_tier_spec_at scalar what-if ─────────────────────────────────────────


def test_next_tier_spec_at_matches_explicit_composition(ent):
    # The convenience is just tier_spec_at(tier, _next_purchasable_tier_after(tier))
    # -- pin the equivalence across every source in _TIER_ORDER so the scalar
    # accessor cannot drift from the explicit composition.
    for tier in ent._TIER_ORDER:
        target = ent._next_purchasable_tier_after(tier)
        if target is None:
            assert ent.next_tier_spec_at(tier) is None
        else:
            assert ent.next_tier_spec_at(tier) == ent.tier_spec_at(tier, target)


def test_next_tier_spec_at_ceiling_returns_none(ent):
    # enterprise sits at the source-side ceiling -- nothing strictly above.
    assert ent.next_tier_spec_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_spec_at_shape(ent):
    body = ent.next_tier_spec_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_PRO
    assert body["is_current"] is False


def test_next_tier_spec_at_is_current_always_false(ent):
    # The target is by definition strictly above source -- is_current can
    # never be True on the returned row.
    for tier in ent._TIER_ORDER:
        body = ent.next_tier_spec_at(tier)
        if body is not None:
            assert body["is_current"] is False


def test_next_tier_spec_at_trial_resolves_to_enterprise(ent):
    body = ent.next_tier_spec_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["id"] == ent.TIER_ENTERPRISE


def test_next_tier_spec_at_unknown_inputs(ent):
    # Defensive null-paths -- empty / unknown / None / non-string all
    # collapse to None rather than raising.
    assert ent.next_tier_spec_at("") is None
    assert ent.next_tier_spec_at("nope") is None
    assert ent.next_tier_spec_at(None) is None  # type: ignore[arg-type]
    assert ent.next_tier_spec_at(123) is None  # type: ignore[arg-type]


def test_next_tier_spec_at_independent_of_resolver(ent, monkeypatch):
    # The _at family walks the static catalogue, not the gated resolver --
    # so a synthetic resolver failure must not affect the answer.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_spec_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert body["id"] == ent.TIER_CLOUD_PRO


def test_next_tier_spec_at_grace_vs_enforce(ent, monkeypatch):
    grace = ent.next_tier_spec_at(ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_spec_at(ent.TIER_CLOUD_STARTER)
    assert grace == enforce


# ── previous_tier_spec_at scalar what-if ─────────────────────────────────────


def test_previous_tier_spec_at_matches_explicit_composition(ent):
    for tier in ent._TIER_ORDER:
        target = ent._previous_purchasable_tier_before(tier)
        if target is None:
            assert ent.previous_tier_spec_at(tier) is None
        else:
            assert ent.previous_tier_spec_at(tier) == ent.tier_spec_at(
                tier, target
            )


def test_previous_tier_spec_at_floor_returns_none(ent):
    # OSS and cloud_free both sit at the source-side floor.
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent.previous_tier_spec_at(tier) is None


def test_previous_tier_spec_at_shape(ent):
    body = ent.previous_tier_spec_at(ent.TIER_CLOUD_PRO)
    assert body is not None
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_STARTER
    assert body["is_current"] is False


def test_previous_tier_spec_at_is_current_always_false(ent):
    for tier in ent._TIER_ORDER:
        body = ent.previous_tier_spec_at(tier)
        if body is not None:
            assert body["is_current"] is False


def test_previous_tier_spec_at_trial_resolves_to_starter(ent):
    body = ent.previous_tier_spec_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["id"] == ent.TIER_CLOUD_STARTER


def test_previous_tier_spec_at_unknown_inputs(ent):
    assert ent.previous_tier_spec_at("") is None
    assert ent.previous_tier_spec_at("nope") is None
    assert ent.previous_tier_spec_at(None) is None  # type: ignore[arg-type]
    assert ent.previous_tier_spec_at(123) is None  # type: ignore[arg-type]


def test_previous_tier_spec_at_grace_vs_enforce(ent, monkeypatch):
    grace = ent.previous_tier_spec_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_spec_at(ent.TIER_CLOUD_PRO)
    assert grace == enforce


# ── /api/entitlement/next-tier-spec endpoint ────────────────────────────────


def test_next_tier_spec_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-spec")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["spec"] is not None
    assert body["spec"]["id"] == ent.TIER_CLOUD_STARTER
    assert body["spec"]["is_current"] is False
    assert body["grace"] is True
    assert body["enforced"] is False


def test_next_tier_spec_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-spec")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["spec"] is None
    assert body["current_tier"] == "oss"


def test_next_tier_spec_endpoint_row_matches_helper(client, ent):
    # The body's spec row must byte-equal the underlying helper for the
    # live resolved entitlement -- pin the equivalence so callers can
    # swap between the bound endpoint and the helper without copy drift.
    rv = client.get("/api/entitlement/next-tier-spec")
    body = rv.get_json()
    assert body["spec"] == ent.next_tier_spec()


# ── /api/entitlement/previous-tier-spec endpoint ────────────────────────────


def test_previous_tier_spec_endpoint_oss_default_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-spec")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor; nothing below to step down to.
    assert body["spec"] is None


def test_previous_tier_spec_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-spec")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["spec"] is None
    assert body["current_tier"] == "oss"


# ── /api/entitlement/next-tier-spec-at endpoint ─────────────────────────────


def test_next_tier_spec_at_endpoint_starter_source(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-spec-at",
        query_string={"tier": ent.TIER_CLOUD_STARTER},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["row"] is not None
    assert body["row"]["id"] == ent.TIER_CLOUD_PRO
    assert body["row"]["is_current"] is False


def test_next_tier_spec_at_endpoint_ceiling_returns_null_row(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-spec-at",
        query_string={"tier": ent.TIER_ENTERPRISE},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_next_tier_spec_at_endpoint_missing_tier_400(client):
    rv = client.get("/api/entitlement/next-tier-spec-at")
    assert rv.status_code == 400
    assert rv.get_json() == {"error": "missing tier"}


def test_next_tier_spec_at_endpoint_blank_tier_400(client):
    rv = client.get(
        "/api/entitlement/next-tier-spec-at", query_string={"tier": "   "}
    )
    assert rv.status_code == 400


def test_next_tier_spec_at_endpoint_unknown_tier_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-spec-at",
        query_string={"tier": "nope"},
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "nope"


def test_next_tier_spec_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    rv = client.get(
        "/api/entitlement/next-tier-spec-at",
        query_string={"tier": ent.TIER_CLOUD_STARTER},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


def test_next_tier_spec_at_endpoint_row_matches_helper(client, ent):
    # Endpoint row byte-equals the underlying helper for any valid source.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        rv = client.get(
            "/api/entitlement/next-tier-spec-at", query_string={"tier": tier}
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["row"] == ent.next_tier_spec_at(tier)


# ── /api/entitlement/previous-tier-spec-at endpoint ─────────────────────────


def test_previous_tier_spec_at_endpoint_pro_source(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-spec-at",
        query_string={"tier": ent.TIER_CLOUD_PRO},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] is not None
    assert body["row"]["id"] == ent.TIER_CLOUD_STARTER
    assert body["row"]["is_current"] is False


def test_previous_tier_spec_at_endpoint_floor_returns_null_row(client, ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        rv = client.get(
            "/api/entitlement/previous-tier-spec-at",
            query_string={"tier": tier},
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["target"] is None
        assert body["row"] is None


def test_previous_tier_spec_at_endpoint_missing_tier_400(client):
    rv = client.get("/api/entitlement/previous-tier-spec-at")
    assert rv.status_code == 400


def test_previous_tier_spec_at_endpoint_unknown_tier_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-spec-at",
        query_string={"tier": "nope"},
    )
    assert rv.status_code == 404


def test_previous_tier_spec_at_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-spec-at",
        query_string={"tier": ent.TIER_CLOUD_PRO},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


def test_previous_tier_spec_at_endpoint_row_matches_helper(client, ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        rv = client.get(
            "/api/entitlement/previous-tier-spec-at",
            query_string={"tier": tier},
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["row"] == ent.previous_tier_spec_at(tier)


# ── cross-helper parity (rank-unambiguous sources only) ─────────────────────
#
# The live ``Entitlement.previous_purchasable_tier`` applies a cloud-vs-
# self-hosted tie-break against the resolved source, while
# ``_previous_purchasable_tier_before`` (used by the ``_at`` family) elides
# that preference and breaks ties by declaration order. They therefore
# diverge for sources whose rank cluster is ambiguous (e.g. enterprise's
# previous can land on cloud_pro or pro). Only assert parity for sources
# whose target rank carries a single candidate.


def test_next_spec_scalar_equals_at_unambiguous(ent):
    # Sources whose target rank carries a single purchasable candidate --
    # the scalar live posture and the static _at posture must agree.
    # oss -> cloud_starter (rank 1), cloud_free -> cloud_starter, and
    # cloud_starter -> rank-2 cluster (ambiguous, skip).
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.next_tier_spec() == ent.next_tier_spec_at(tier)


def test_previous_spec_scalar_equals_at_unambiguous(ent):
    # cloud_starter -> rank 0 cluster (oss / cloud_free both candidates),
    # rank-2 sources -> rank 1 (unambiguous: cloud_starter).
    for tier in (ent.TIER_CLOUD_PRO, ent.TIER_PRO):
        e = ent._build(tier, "test")
        assert e.previous_tier_spec() == ent.previous_tier_spec_at(tier)
