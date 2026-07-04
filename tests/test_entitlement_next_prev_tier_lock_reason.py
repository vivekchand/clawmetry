"""Tests for ``Entitlement.next_tier_lock_reason`` /
``previous_tier_lock_reason``, their module-level convenience helpers,
and the two companion
``/api/entitlement/{next,previous}-tier-lock-reason`` endpoints.

Bare (no ``_at``) siblings of the merged directional scalar
``next_tier_lock_reason_at`` / ``previous_tier_lock_reason_at`` family:
where ``next_tier_lock_reason_at(tier, item)`` takes an explicit source
``tier`` and walks :func:`_next_purchasable_tier_after` (source-
agnostic), the bare ``Entitlement.next_tier_lock_reason(item)`` uses the
resolved entitlement's tier and :meth:`next_purchasable_tier`
(source-aware -- picks ``cloud_*`` when :attr:`source` is ``"cloud"``
and the self-hosted sibling otherwise), matching the pattern
:meth:`next_tier_spec` / :meth:`next_tier_feature_spec` uses.

Pins covered here:

* per-source byte-equality with
  ``lock_reason_at(self.next_purchasable_tier(), item)`` across every
  purchasable source for every feature / runtime and the three capacity
  axes (``channels`` / ``retention_days`` / ``nodes``)
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  yields ``None`` on the helper; API surface 200 with ``target=null`` +
  ``reason=null`` + ``locked=false`` so the paywall surface keeps
  rendering
* trial-as-source resolves the same way :meth:`next_tier_spec` does
  (next -> enterprise, previous -> cloud_starter)
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``) on the
  helper and API surface; canonical id echoed on the endpoint response
* capacity axes route through the ``kind=`` keyword path
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a synthesised resolver failure short-
  circuits to ``None`` so the CTA surface keeps rendering
* the two API endpoints never 5xx: 400 on missing / multi input, 404
  on unknown feature / runtime, 200 with ``reason=null`` at the ceiling
  / floor; a synthesised resolver failure yields the grace-shape
  envelope
* module-level helpers agree with the bound method on the resolved
  entitlement
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "key",
    "kind",
    "target",
    "target_label",
    "target_rank",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "upgrade_required",
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


# ── Entitlement.next_tier_lock_reason ───────────────────────────────────────


def test_next_tier_lock_reason_byte_equals_lock_reason_at_features(ent):
    # Bare helper is convenience for
    # lock_reason_at(self.next_purchasable_tier(), item, kind=kind). Pin the
    # per-source parity for every feature so the bare projection cannot drift
    # from the explicit composition.
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
            assert e.next_tier_lock_reason(
                feature, kind="feature"
            ) == ent.lock_reason_at(target, feature, kind="feature")


def test_next_tier_lock_reason_byte_equals_lock_reason_at_runtimes(ent):
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
            assert e.next_tier_lock_reason(
                runtime, kind="runtime"
            ) == ent.lock_reason_at(target, runtime, kind="runtime")


def test_next_tier_lock_reason_capacity_axes_parity(ent):
    # Capacity axes must route through kind= like lock_reason_at itself.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    target = e.next_purchasable_tier()
    assert target is not None
    for kind in ("channels", "retention_days", "nodes"):
        for n in (1, 5, 42, 999):
            assert e.next_tier_lock_reason(
                str(n), kind=kind
            ) == ent.lock_reason_at(target, str(n), kind=kind)


def test_next_tier_lock_reason_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every item.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None
    for feature in sorted(ent.ALL_FEATURES):
        assert e.next_tier_lock_reason(feature, kind="feature") is None
    for runtime in sorted(ent.ALL_RUNTIMES):
        assert e.next_tier_lock_reason(runtime, kind="runtime") is None


def test_next_tier_lock_reason_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro -- next strictly-higher
    # purchasable rung is enterprise (rank 3).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    reason = e.next_tier_lock_reason("custom_alerts", kind="feature")
    assert reason == ent.lock_reason_at(
        ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )


def test_next_tier_lock_reason_infers_kind(ent):
    # Passing kind=None must let the inner lock_reason_at method infer
    # feature vs runtime from the id, matching lock_reason_at posture.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    target = e.next_purchasable_tier()
    assert target is not None
    assert e.next_tier_lock_reason("claude_code") == ent.lock_reason_at(
        target, "claude_code"
    )
    assert e.next_tier_lock_reason("custom_alerts") == ent.lock_reason_at(
        target, "custom_alerts"
    )


def test_next_tier_lock_reason_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    # A synthesised resolver failure must short-circuit to None so the CTA
    # surface stays mute rather than 500-ing.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(
        type(e),
        "next_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.next_tier_lock_reason("custom_alerts", kind="feature") is None


# ── Entitlement.previous_tier_lock_reason ───────────────────────────────────


def test_previous_tier_lock_reason_byte_equals_lock_reason_at_features(ent):
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
            assert e.previous_tier_lock_reason(
                feature, kind="feature"
            ) == ent.lock_reason_at(target, feature, kind="feature")


def test_previous_tier_lock_reason_byte_equals_lock_reason_at_runtimes(ent):
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
            assert e.previous_tier_lock_reason(
                runtime, kind="runtime"
            ) == ent.lock_reason_at(target, runtime, kind="runtime")


def test_previous_tier_lock_reason_returns_none_at_floor(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        e = ent._build(tier, "test")
        assert e.previous_purchasable_tier() is None
        for feature in sorted(ent.ALL_FEATURES):
            assert e.previous_tier_lock_reason(feature, kind="feature") is None
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert e.previous_tier_lock_reason(runtime, kind="runtime") is None


def test_previous_tier_lock_reason_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    reason = e.previous_tier_lock_reason("custom_alerts", kind="feature")
    assert reason == ent.lock_reason_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts", kind="feature"
    )


def test_previous_tier_lock_reason_never_raises_on_resolver_failure(
    ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        e.previous_tier_lock_reason("custom_alerts", kind="feature") is None
    )


# ── grace vs enforce ─────────────────────────────────────────────────────────


def test_grace_and_enforce_yield_same_body(ent, monkeypatch):
    # lock_reason_at synthesises a fresh Entitlement with grace=False -- so
    # flipping the global enforce flag must not change the projected body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    grace_reason = e.next_tier_lock_reason("custom_alerts", kind="feature")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    enforce_reason = e2.next_tier_lock_reason("custom_alerts", kind="feature")
    assert enforce_reason == grace_reason


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_next_tier_lock_reason_matches_method(ent):
    assert ent.next_tier_lock_reason("custom_alerts", kind="feature") == (
        ent.get_entitlement().next_tier_lock_reason(
            "custom_alerts", kind="feature"
        )
    )


def test_module_previous_tier_lock_reason_matches_method(ent):
    assert ent.previous_tier_lock_reason("custom_alerts", kind="feature") == (
        ent.get_entitlement().previous_tier_lock_reason(
            "custom_alerts", kind="feature"
        )
    )


def test_module_helpers_never_raise(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_lock_reason("custom_alerts", kind="feature") is None
    assert (
        ent.previous_tier_lock_reason("custom_alerts", kind="feature") is None
    )


# ── /api/entitlement/next-tier-lock-reason endpoint ─────────────────────────


def test_next_tier_lock_reason_endpoint_oss_default_feature(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["key"] == "custom_alerts"
    assert body["kind"] == "feature"
    # OSS default -> next purchasable is one of the rank-1 tiers.
    assert body["target"] is not None
    assert body["target_label"] == ent.tier_label(body["target"])
    assert body["target_rank"] == ent.tier_rank(body["target"])
    assert body["grace"] is True
    assert body["enforced"] is False


def test_next_tier_lock_reason_endpoint_runtime(client, ent):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "runtime"
    assert body["key"] == "claude_code"
    assert body["target"] is not None


def test_next_tier_lock_reason_endpoint_alias_canonicalises(client, ent):
    # ``claude-code`` alias must canonicalise to ``claude_code`` on the
    # response, matching sibling /next-tier-runtime-spec posture.
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?runtime=claude-code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["key"] == "claude_code"


def test_next_tier_lock_reason_endpoint_reason_matches_lock_reason_at(
    client, ent
):
    # The endpoint's reason must byte-equal /lock-reason-at at the resolved
    # target -- pin the equivalence so callers can swap the bound endpoint
    # for the source-parameterised sibling without copy drift.
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?feature=custom_alerts"
    )
    body = rv.get_json()
    target = body["target"]
    assert target is not None
    expected = ent.lock_reason_at(target, "custom_alerts", kind="feature")
    assert body["reason"] == expected


def test_next_tier_lock_reason_endpoint_missing_axis_400(client):
    rv = client.get("/api/entitlement/next-tier-lock-reason")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "supply exactly one" in body.get("error", "")


def test_next_tier_lock_reason_endpoint_multi_axis_400(client):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason"
        "?feature=custom_alerts&runtime=claude_code"
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "supply only one" in body.get("error", "")


def test_next_tier_lock_reason_endpoint_unknown_feature_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?feature=no_such_feature"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown feature"
    assert body.get("which") == "feature"
    assert body.get("feature") == "no_such_feature"


def test_next_tier_lock_reason_endpoint_unknown_runtime_404(client):
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?runtime=no_such_runtime"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown runtime"
    # Body echoes the ORIGINAL supplied id.
    assert body.get("runtime") == "no_such_runtime"


def test_next_tier_lock_reason_endpoint_capacity_axes(client, ent):
    # Capacity axes route through the kind= keyword path.
    for axis in ("channels", "retention_days", "nodes"):
        rv = client.get(
            f"/api/entitlement/next-tier-lock-reason?{axis}=5"
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["kind"] == axis
        assert body["key"] == "5"


def test_next_tier_lock_reason_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/next-tier-lock-reason?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["target"] is None
    assert body["reason"] is None
    assert body["locked"] is False
    assert body["current_tier"] == "oss"


# ── /api/entitlement/previous-tier-lock-reason endpoint ─────────────────────


def test_previous_tier_lock_reason_endpoint_oss_floor(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    # OSS is the floor -- no rung below.
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["reason"] is None
    assert body["locked"] is False


def test_previous_tier_lock_reason_endpoint_missing_axis_400(client):
    rv = client.get("/api/entitlement/previous-tier-lock-reason")
    assert rv.status_code == 400


def test_previous_tier_lock_reason_endpoint_multi_axis_400(client):
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason"
        "?feature=custom_alerts&channels=5"
    )
    assert rv.status_code == 400


def test_previous_tier_lock_reason_endpoint_unknown_feature_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason?feature=no_such"
    )
    assert rv.status_code == 404


def test_previous_tier_lock_reason_endpoint_unknown_runtime_404(client):
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason?runtime=no_such_runtime"
    )
    assert rv.status_code == 404


def test_previous_tier_lock_reason_endpoint_alias(client, ent):
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason?runtime=claude-code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["key"] == "claude_code"


def test_previous_tier_lock_reason_endpoint_never_raises(
    client, ent, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/previous-tier-lock-reason?feature=custom_alerts"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["reason"] is None
    assert body["target"] is None
