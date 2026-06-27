"""Tests for ``next_tier_diff_at`` / ``previous_tier_diff_at`` -- scalar
what-if siblings of the live ``Entitlement.next_tier_diff`` /
``Entitlement.previous_tier_diff`` instance methods, plus the companion
``/api/entitlement/{next,previous}-tier-diff-at?tier=<src>`` endpoints.

These helpers let a pricing-comparison UI render the full ``tier_diff``
payload (``added_*``, ``lost_*``, ``capacity_changes``, ``direction``)
for the rung above / below any hypothetical source rung off **one**
round-trip, without first hitting ``/api/entitlement`` and without
monkey-patching the entitlement context -- the source-anchored
counterpart of the live methods that pin ``from`` to the resolved
entitlement.

Unlike ``next_tier_unlocks_at`` / ``previous_tier_unlocks_at`` -- which
surface the target's own ``tier_unlocks`` row (target-anchored,
``previous_tier`` is the target's natural next-lower purchasable, NOT
the caller-supplied source) -- these helpers pin **both** endpoints, so
``row["from"]`` is byte-equal to the caller-supplied ``tier``. That
mirrors the live ``Entitlement.{next,previous}_tier_diff`` posture and
is the natural shape for a two-endpoint diff.

Pins covered here:

* ``next_tier_diff_at(tier)`` byte-equals
  ``tier_diff(tier, _next_purchasable_tier_after(tier))`` across every
  valid source -- the convenience cannot drift from the explicit
  composition
* same identity for ``previous_tier_diff_at`` against
  ``_previous_purchasable_tier_before``
* the row's ``from`` is byte-equal to the caller-supplied source -- the
  key differentiator vs the unlocks/locks ``_at`` family
* ``direction`` is always ``"upgrade"`` for the next-direction helper
  (any purchasable source has only strictly-higher rungs above) and
  ``"downgrade"`` for the previous-direction helper
* at the ceiling / floor (no rung strictly above / below source) both
  helpers return ``None``
* trial-as-source resolves the same way the unlocks/locks ``_at``
  family does: next -> enterprise, previous -> cloud_starter
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* unknown / empty / ``None`` / non-string source returns ``None``
* the API surface 400s on missing input, 404s on unknown ids (with
  ``which``), surfaces 200 envelopes at the ceiling / floor with
  ``row=null``, and never 5xxs
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


_DIFF_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
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


# ── next_tier_diff_at ────────────────────────────────────────────────────────


def test_next_tier_diff_at_matches_explicit_composition(ent):
    # The convenience is tier_diff(tier, _next_purchasable_tier_after(tier)).
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
        assert ent.next_tier_diff_at(src) == ent.tier_diff(src, nxt), src


def test_next_tier_diff_at_returns_none_at_ceiling(ent):
    # Enterprise has no rung above -> None, mirroring the live method.
    assert ent.next_tier_diff_at(ent.TIER_ENTERPRISE) is None


def test_next_tier_diff_at_row_shape(ent):
    body = ent.next_tier_diff_at(ent.TIER_OSS)
    assert body is not None
    assert set(body.keys()) == _DIFF_KEYS
    # The from endpoint IS the caller-supplied source -- this is the
    # key differentiator vs next_tier_unlocks_at which pins only the
    # target.
    assert body["from"] == ent.TIER_OSS
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["to"] == ent.TIER_CLOUD_STARTER
    assert body["to_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["to_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["direction"] == "upgrade"
    assert body["added_features"] == sorted(body["added_features"])
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["added_runtimes"] == sorted(body["added_runtimes"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])
    # capacity_changes carries the three documented keys.
    assert set(body["capacity_changes"].keys()) == {
        "channel_limit",
        "retention_days",
        "node_limit",
    }


def test_next_tier_diff_at_pins_source_endpoint(ent):
    # The row's from endpoint is byte-equal to the caller-supplied
    # source across every purchasable rung -- the contract that lets a
    # downstream consumer use the row as-is for a "From X To Y"
    # pricing-comparison card without rewriting from.
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        body = ent.next_tier_diff_at(src)
        assert body is not None, src
        assert body["from"] == src, src


def test_next_tier_diff_at_direction_is_upgrade_for_every_purchasable_source(ent):
    # Every purchasable source has only strictly-higher rungs above
    # (the stepper picks strictly higher rank). So direction is
    # always "upgrade" -- never "lateral" / "identity" / "downgrade".
    for src in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_TRIAL,
    ):
        body = ent.next_tier_diff_at(src)
        assert body is not None, src
        assert body["direction"] == "upgrade", src


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_tier_diff_at_returns_none_on_bad_input(ent, bad):
    assert ent.next_tier_diff_at(bad) is None


def test_next_tier_diff_at_trims_and_lowercases(ent):
    assert ent.next_tier_diff_at("  OSS  ") == ent.tier_diff(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER
    )


def test_next_tier_diff_at_trial_source_resolves_to_enterprise(ent):
    # Trial sits at rank 2, so the next strictly-higher purchasable
    # rung is enterprise -- matches the live method's posture when
    # called from a trial entitlement, and the unlocks/locks family's
    # trial semantics.
    body = ent.next_tier_diff_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["from"] == ent.TIER_TRIAL
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"


def test_next_tier_diff_at_grace_and_enforce_match(ent, monkeypatch):
    # Catalogue-derived (off the static per-tier grants) -- flipping
    # enforcement on must not change the body.
    grace = ent.next_tier_diff_at(ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_diff_at(ent.TIER_CLOUD_STARTER)
    assert enforce == grace


def test_next_tier_diff_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_diff",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.next_tier_diff_at(ent.TIER_OSS) is None


def test_next_tier_diff_at_independent_of_resolver(ent, monkeypatch):
    # The whole point of the _at variant: it does not need the
    # resolver. Swap get_entitlement to raise and the helper must
    # still return a non-None body.
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_diff_at(ent.TIER_OSS)
    assert body is not None
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_CLOUD_STARTER


# ── previous_tier_diff_at ────────────────────────────────────────────────────


def test_previous_tier_diff_at_matches_explicit_composition(ent):
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_diff_at(src) == ent.tier_diff(src, prv), src


def test_previous_tier_diff_at_returns_none_at_floor(ent):
    # OSS and cloud_free both have nothing strictly below.
    assert ent.previous_tier_diff_at(ent.TIER_OSS) is None
    assert ent.previous_tier_diff_at(ent.TIER_CLOUD_FREE) is None


def test_previous_tier_diff_at_row_shape(ent):
    body = ent.previous_tier_diff_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert set(body.keys()) == _DIFF_KEYS
    assert body["from"] == ent.TIER_ENTERPRISE
    assert body["from_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    # Enterprise's previous_purchasable_tier_before is cloud_pro (the
    # first rank-2 entry in declaration order).
    assert body["to"] == ent.TIER_CLOUD_PRO
    assert body["direction"] == "downgrade"
    assert body["added_features"] == sorted(body["added_features"])
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["added_runtimes"] == sorted(body["added_runtimes"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])
    assert set(body["capacity_changes"].keys()) == {
        "channel_limit",
        "retention_days",
        "node_limit",
    }


def test_previous_tier_diff_at_pins_source_endpoint(ent):
    # Same source-endpoint pin as next_tier_diff_at, downgrade side.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        body = ent.previous_tier_diff_at(src)
        assert body is not None, src
        assert body["from"] == src, src


def test_previous_tier_diff_at_direction_is_downgrade_for_every_source_with_a_floor(
    ent,
):
    # Every source that has a strictly-lower rung below resolves to
    # direction="downgrade". Pinned per known source.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        body = ent.previous_tier_diff_at(src)
        assert body is not None, src
        assert body["direction"] == "downgrade", src


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_previous_tier_diff_at_returns_none_on_bad_input(ent, bad):
    assert ent.previous_tier_diff_at(bad) is None


def test_previous_tier_diff_at_trims_and_lowercases(ent):
    assert ent.previous_tier_diff_at("  CLOUD_STARTER  ") == ent.tier_diff(
        ent.TIER_CLOUD_STARTER, ent.TIER_OSS
    )


def test_previous_tier_diff_at_trial_source_resolves_to_cloud_starter(ent):
    # Trial sits at rank 2, so the next strictly-lower purchasable
    # rung is cloud_starter (rank 1) -- matches the live method's
    # posture and the unlocks/locks family's trial semantics.
    body = ent.previous_tier_diff_at(ent.TIER_TRIAL)
    assert body is not None
    assert body["from"] == ent.TIER_TRIAL
    assert body["to"] == ent.TIER_CLOUD_STARTER
    assert body["direction"] == "downgrade"


def test_previous_tier_diff_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_diff_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_diff_at(ent.TIER_CLOUD_PRO)
    assert enforce == grace


def test_previous_tier_diff_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "tier_diff",
        lambda *_: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert ent.previous_tier_diff_at(ent.TIER_ENTERPRISE) is None


def test_previous_tier_diff_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_diff_at(ent.TIER_ENTERPRISE)
    assert body is not None
    assert body["from"] == ent.TIER_ENTERPRISE
    assert body["to"] == ent.TIER_CLOUD_PRO


# ── set-identity vs tier_diff swap ───────────────────────────────────────────


def test_diff_at_pair_swap_identity(ent):
    # tier_diff(X, Y)["added_*"] byte-equals tier_diff(Y, X)["lost_*"]
    # for any pair. The _at convenience must inherit that invariant
    # against the corresponding helper composition, so a UI can flip
    # direction without re-fetching.
    for src in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        up = ent.next_tier_diff_at(src)
        # The reverse: from the rung above, downgrade back to source.
        nxt = ent._next_purchasable_tier_after(src)
        down = ent.tier_diff(nxt, src)
        assert up is not None and down is not None
        assert up["added_features"] == down["lost_features"]
        assert up["lost_features"] == down["added_features"]
        assert up["added_runtimes"] == down["lost_runtimes"]
        assert up["lost_runtimes"] == down["added_runtimes"]


# ── API: /api/entitlement/next-tier-diff-at ──────────────────────────────────


def test_next_tier_diff_at_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["row"] == ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)


def test_next_tier_diff_at_endpoint_row_from_pins_source(client, ent):
    # Pinned at the endpoint surface too -- a UI consuming the body
    # directly without re-checking can rely on row.from == query tier.
    rv = client.get(
        "/api/entitlement/next-tier-diff-at?tier=cloud_starter"
    )
    body = rv.get_json()
    assert body["row"]["from"] == ent.TIER_CLOUD_STARTER
    assert body["row"]["direction"] == "upgrade"


def test_next_tier_diff_at_endpoint_enterprise_ceiling(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=enterprise")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_next_tier_diff_at_endpoint_trial(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=trial")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["row"] == ent.tier_diff(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)


def test_next_tier_diff_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/next-tier-diff-at")
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "missing tier"


def test_next_tier_diff_at_endpoint_blank_tier(client):
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=%20%20")
    assert rv.status_code == 400


def test_next_tier_diff_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_next_tier_diff_at_endpoint_trims_and_lowercases(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-diff-at?tier=%20%20OSS%20%20"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_next_tier_diff_at_endpoint_never_raises(client, ent, monkeypatch):
    # Synthesise a builder failure and assert the envelope still
    # returns 200 with row=null so the dashboard doesn't break.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_diff_at", boom)
    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    rv = client.get("/api/entitlement/next-tier-diff-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


# ── API: /api/entitlement/previous-tier-diff-at ──────────────────────────────


def test_previous_tier_diff_at_endpoint_enterprise_default(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-diff-at?tier=enterprise"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.tier_diff(
        ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO
    )


def test_previous_tier_diff_at_endpoint_row_from_pins_source(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-diff-at?tier=cloud_starter"
    )
    body = rv.get_json()
    assert body["row"]["from"] == ent.TIER_CLOUD_STARTER
    assert body["row"]["direction"] == "downgrade"


def test_previous_tier_diff_at_endpoint_oss_floor(client, ent):
    rv = client.get("/api/entitlement/previous-tier-diff-at?tier=oss")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_previous_tier_diff_at_endpoint_cloud_free_floor(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-diff-at?tier=cloud_free"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] is None
    assert body["row"] is None


def test_previous_tier_diff_at_endpoint_trial(client, ent):
    rv = client.get("/api/entitlement/previous-tier-diff-at?tier=trial")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.tier_diff(ent.TIER_TRIAL, ent.TIER_CLOUD_STARTER)


def test_previous_tier_diff_at_endpoint_missing_tier(client):
    rv = client.get("/api/entitlement/previous-tier-diff-at")
    assert rv.status_code == 400


def test_previous_tier_diff_at_endpoint_unknown_tier(client):
    rv = client.get("/api/entitlement/previous-tier-diff-at?tier=bogus")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"


def test_previous_tier_diff_at_endpoint_never_raises(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "previous_tier_diff_at", boom)
    monkeypatch.setattr(ent, "_previous_purchasable_tier_before", boom)
    rv = client.get("/api/entitlement/previous-tier-diff-at?tier=enterprise")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


# ── end-to-end parity ────────────────────────────────────────────────────────


def test_endpoints_row_matches_helper(client, ent):
    # End-to-end parity: the endpoint body's row byte-equals the
    # module-level helper for the same source, on both directions.
    next_rv = client.get(
        "/api/entitlement/next-tier-diff-at?tier=cloud_starter"
    )
    assert next_rv.get_json()["row"] == ent.next_tier_diff_at(
        ent.TIER_CLOUD_STARTER
    )
    prev_rv = client.get(
        "/api/entitlement/previous-tier-diff-at?tier=cloud_pro"
    )
    assert prev_rv.get_json()["row"] == ent.previous_tier_diff_at(
        ent.TIER_CLOUD_PRO
    )
