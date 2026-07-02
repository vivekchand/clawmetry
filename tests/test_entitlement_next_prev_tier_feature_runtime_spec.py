"""Tests for ``Entitlement.next_tier_feature_spec`` /
``previous_tier_feature_spec`` / ``next_tier_runtime_spec`` /
``previous_tier_runtime_spec``, their module-level convenience helpers,
and the four companion
``/api/entitlement/{next,previous}-tier-{feature,runtime}-spec``
endpoints.

Bare (no ``_at``) siblings of the merged directional scalar
``_at`` family: where ``next_tier_feature_spec_at(tier, feature)`` takes
an explicit source ``tier`` and walks
:func:`_next_purchasable_tier_after` (source-agnostic), the bare
``Entitlement.next_tier_feature_spec(feature)`` uses the resolved
entitlement's tier and :meth:`next_purchasable_tier` (source-aware --
picks ``cloud_*`` when :attr:`source` is ``"cloud"`` and the
self-hosted sibling otherwise), matching the pattern
:meth:`next_tier_spec` uses.

Pins covered here:

* per-source parity with
  ``feature_spec_at(self.next_purchasable_tier(), feature)`` (feature
  axis) and the runtime mirror across every purchasable source for
  every feature / runtime
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  yields ``None`` on the helper; API surface 200 with ``target=null`` +
  ``row=null`` so the paywall surface keeps rendering
* trial-as-source resolves the same way :meth:`next_tier_spec` does
  (next -> enterprise, previous -> cloud_starter)
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``) on the
  helpers and API surface; canonical id echoed on the endpoint response
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a synthesised resolver failure short-
  circuits to ``None`` so the CTA surface keeps rendering
* the four API endpoints never 5xx: 400 on missing input, 404 on
  unknown ids, 200 with ``row=null`` at the ceiling / floor; a
  synthesised resolver failure yields the grace-shape envelope
* module-level helpers agree with the bound method on the resolved
  entitlement
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENDPOINT_FEATURE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "feature",
    "target",
    "target_label",
    "target_rank",
    "row",
    "grace",
    "enforced",
}

_ENDPOINT_RUNTIME_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "runtime",
    "target",
    "target_label",
    "target_rank",
    "row",
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


# ── Entitlement.next_tier_feature_spec ───────────────────────────────────────


def test_next_tier_feature_spec_byte_equals_feature_spec_at(ent):
    # Bare helper is convenience for
    # feature_spec_at(self.next_purchasable_tier(), feature). Pin the
    # per-source parity across every purchasable source for every feature
    # so the bare projection cannot drift from the explicit composition.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        target = e.next_purchasable_tier()
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert e.next_tier_feature_spec(feature) == ent.feature_spec_at(
                target, feature
            )


def test_next_tier_feature_spec_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every feature.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    for feature in sorted(ent.ALL_FEATURES):
        assert e.next_tier_feature_spec(feature) is None


def test_next_tier_feature_spec_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro -- next strictly-higher
    # purchasable rung is enterprise (rank 3). Pins that the bare helper
    # matches the sibling next_tier_spec semantics on trial.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.next_tier_feature_spec("custom_alerts")
    assert body is not None
    assert body == ent.feature_spec_at(ent.TIER_ENTERPRISE, "custom_alerts")


def test_next_tier_feature_spec_unknown_inputs_return_none(ent):
    # Defensive null-paths -- empty / unknown / None / whitespace all
    # collapse to None rather than raising.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    assert e.next_tier_feature_spec("") is None
    assert e.next_tier_feature_spec(None) is None  # type: ignore[arg-type]
    assert e.next_tier_feature_spec("no_such_feature") is None


def test_next_tier_feature_spec_whitespace_and_case_insensitive(ent):
    # Whitespace + case normalisation matches the sibling _at helpers.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    canon = e.next_tier_feature_spec("custom_alerts")
    assert canon is not None
    assert e.next_tier_feature_spec(" CUSTOM_ALERTS ") == canon


def test_next_tier_feature_spec_never_raises_on_resolver_failure(ent, monkeypatch):
    # A synthesised resolver failure must short-circuit to None so the CTA
    # surface stays mute rather than 500-ing.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_feature_spec("custom_alerts") is None


# ── Entitlement.previous_tier_feature_spec ───────────────────────────────────


def test_previous_tier_feature_spec_byte_equals_feature_spec_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        target = e.previous_purchasable_tier()
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert e.previous_tier_feature_spec(feature) == ent.feature_spec_at(
                target, feature
            )


def test_previous_tier_feature_spec_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        for feature in sorted(ent.ALL_FEATURES):
            assert e.previous_tier_feature_spec(feature) is None


def test_previous_tier_feature_spec_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter) -- highest rank strictly below
    # trial's rank 2.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    body = e.previous_tier_feature_spec("custom_alerts")
    assert body is not None
    assert body == ent.feature_spec_at(ent.TIER_CLOUD_STARTER, "custom_alerts")


def test_previous_tier_feature_spec_unknown_inputs_return_none(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    assert e.previous_tier_feature_spec("") is None
    assert e.previous_tier_feature_spec(None) is None  # type: ignore[arg-type]
    assert e.previous_tier_feature_spec("no_such") is None


def test_previous_tier_feature_spec_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_feature_spec("custom_alerts") is None


# ── Entitlement.next_tier_runtime_spec ───────────────────────────────────────


def test_next_tier_runtime_spec_byte_equals_runtime_spec_at(ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        target = e.next_purchasable_tier()
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert e.next_tier_runtime_spec(runtime) == ent.runtime_spec_at(
                target, runtime
            )


def test_next_tier_runtime_spec_returns_none_at_ceiling(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    for runtime in sorted(ent.ALL_RUNTIMES):
        assert e.next_tier_runtime_spec(runtime) is None


def test_next_tier_runtime_spec_alias_resolution(ent):
    # ``claude-code`` aliases to ``claude_code`` -- the helper must
    # canonicalise so both spellings yield byte-equal output, matching the
    # sibling /next-tier-runtime-spec-at posture.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    canon = e.next_tier_runtime_spec("claude_code")
    assert canon is not None
    assert e.next_tier_runtime_spec("claude-code") == canon
    assert e.next_tier_runtime_spec(" CLAUDE-CODE ") == canon


def test_next_tier_runtime_spec_unknown_inputs_return_none(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    assert e.next_tier_runtime_spec("") is None
    assert e.next_tier_runtime_spec(None) is None  # type: ignore[arg-type]
    assert e.next_tier_runtime_spec("no_such_runtime") is None


def test_next_tier_runtime_spec_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_runtime_spec("claude_code") is None


# ── Entitlement.previous_tier_runtime_spec ───────────────────────────────────


def test_previous_tier_runtime_spec_byte_equals_runtime_spec_at(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        target = e.previous_purchasable_tier()
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert e.previous_tier_runtime_spec(runtime) == ent.runtime_spec_at(
                target, runtime
            )


def test_previous_tier_runtime_spec_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert e.previous_tier_runtime_spec(runtime) is None


def test_previous_tier_runtime_spec_alias_resolution(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    canon = e.previous_tier_runtime_spec("claude_code")
    assert canon is not None
    assert e.previous_tier_runtime_spec("claude-code") == canon


def test_previous_tier_runtime_spec_unknown_inputs_return_none(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    assert e.previous_tier_runtime_spec("") is None
    assert e.previous_tier_runtime_spec(None) is None  # type: ignore[arg-type]
    assert e.previous_tier_runtime_spec("no_such") is None


def test_previous_tier_runtime_spec_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_runtime_spec("claude_code") is None


# ── grace vs enforce ─────────────────────────────────────────────────────────


def test_grace_and_enforce_yield_same_feature_body(ent, monkeypatch):
    # Catalogue-derived (off static per-tier maps), not gated -- so
    # flipping enforce on must not change the body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_feature_spec("custom_alerts")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_feature_spec("custom_alerts")
    assert enforce_body == grace_body


def test_grace_and_enforce_yield_same_runtime_body(ent, monkeypatch):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_body = e.next_tier_runtime_spec("claude_code")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_body = e2.next_tier_runtime_spec("claude_code")
    assert enforce_body == grace_body


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_next_tier_feature_spec_matches_method(ent):
    assert ent.next_tier_feature_spec("custom_alerts") == (
        ent.get_entitlement().next_tier_feature_spec("custom_alerts")
    )


def test_module_previous_tier_feature_spec_matches_method(ent):
    assert ent.previous_tier_feature_spec("custom_alerts") == (
        ent.get_entitlement().previous_tier_feature_spec("custom_alerts")
    )


def test_module_next_tier_runtime_spec_matches_method(ent):
    assert ent.next_tier_runtime_spec("claude_code") == (
        ent.get_entitlement().next_tier_runtime_spec("claude_code")
    )


def test_module_previous_tier_runtime_spec_matches_method(ent):
    assert ent.previous_tier_runtime_spec("claude_code") == (
        ent.get_entitlement().previous_tier_runtime_spec("claude_code")
    )


def test_module_helpers_never_raise(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_feature_spec("custom_alerts") is None
    assert ent.previous_tier_feature_spec("custom_alerts") is None
    assert ent.next_tier_runtime_spec("claude_code") is None
    assert ent.previous_tier_runtime_spec("claude_code") is None


# ── /api/entitlement/next-tier-feature-spec endpoint ────────────────────────


def test_next_tier_feature_spec_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-feature-spec?feature=custom_alerts")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_FEATURE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["feature"] == "custom_alerts"
    # OSS default -> next purchasable is one of the rank-1 tiers.
    assert body["target"] is not None
    assert body["target_label"] == ent.tier_label(body["target"])
    assert body["target_rank"] == ent.tier_rank(body["target"])
    assert body["row"] is not None
    assert body["grace"] is True
    assert body["enforced"] is False


def test_next_tier_feature_spec_endpoint_missing_feature_400(client):
    rv = client.get("/api/entitlement/next-tier-feature-spec")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing feature"


def test_next_tier_feature_spec_endpoint_blank_feature_400(client):
    rv = client.get("/api/entitlement/next-tier-feature-spec?feature=%20%20")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing feature"


def test_next_tier_feature_spec_endpoint_unknown_feature_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-feature-spec?feature=no_such_feature"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown feature"
    assert body.get("which") == "feature"
    assert body.get("feature") == "no_such_feature"


def test_next_tier_feature_spec_endpoint_row_matches_helper(client, ent):
    # The endpoint's row must byte-equal the underlying helper on the live
    # resolved entitlement -- pin the equivalence so callers can swap the
    # bound endpoint for the helper without copy drift.
    rv = client.get("/api/entitlement/next-tier-feature-spec?feature=custom_alerts")
    body = rv.get_json()
    assert body["row"] == ent.next_tier_feature_spec("custom_alerts")


def test_next_tier_feature_spec_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-feature-spec?feature=custom_alerts")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_FEATURE_KEYS
    assert body["row"] is None
    assert body["target"] is None
    assert body["current_tier"] == "oss"


# ── /api/entitlement/previous-tier-feature-spec endpoint ────────────────────


def test_previous_tier_feature_spec_endpoint_oss_floor(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-feature-spec?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_FEATURE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- no rung below.
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_previous_tier_feature_spec_endpoint_missing_feature_400(client):
    rv = client.get("/api/entitlement/previous-tier-feature-spec")
    assert rv.status_code == 400


def test_previous_tier_feature_spec_endpoint_unknown_feature_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-feature-spec?feature=no_such"
    )
    assert rv.status_code == 404


def test_previous_tier_feature_spec_endpoint_never_raises(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-feature-spec?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None


# ── /api/entitlement/next-tier-runtime-spec endpoint ────────────────────────


def test_next_tier_runtime_spec_endpoint_oss_default(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec?runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_RUNTIME_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["runtime"] == "claude_code"
    assert body["target"] is not None


def test_next_tier_runtime_spec_endpoint_alias_canonicalises(client, ent):
    # ``claude-code`` alias must canonicalise to ``claude_code`` on the
    # response, matching sibling /next-tier-runtime-spec-at posture.
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec?runtime=claude-code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["runtime"] == "claude_code"
    assert body["row"] == ent.get_entitlement().next_tier_runtime_spec("claude_code")


def test_next_tier_runtime_spec_endpoint_missing_runtime_400(client):
    rv = client.get("/api/entitlement/next-tier-runtime-spec")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing runtime"


def test_next_tier_runtime_spec_endpoint_unknown_runtime_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec?runtime=no_such_runtime"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown runtime"
    assert body.get("which") == "runtime"
    # The body echoes the ORIGINAL supplied id (not canonical) so callers
    # can render an "unknown runtime <alias>" error message.
    assert body.get("runtime") == "no_such_runtime"


def test_next_tier_runtime_spec_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/next-tier-runtime-spec?runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
    assert body["target"] is None


# ── /api/entitlement/previous-tier-runtime-spec endpoint ────────────────────


def test_previous_tier_runtime_spec_endpoint_oss_floor(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec?runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENDPOINT_RUNTIME_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- no rung below.
    assert body["target"] is None
    assert body["row"] is None


def test_previous_tier_runtime_spec_endpoint_alias(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec?runtime=claude-code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["runtime"] == "claude_code"


def test_previous_tier_runtime_spec_endpoint_missing_runtime_400(client):
    rv = client.get("/api/entitlement/previous-tier-runtime-spec")
    assert rv.status_code == 400


def test_previous_tier_runtime_spec_endpoint_unknown_runtime_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec?runtime=no_such_runtime"
    )
    assert rv.status_code == 404


def test_previous_tier_runtime_spec_endpoint_never_raises(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-runtime-spec?runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["row"] is None
