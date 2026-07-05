"""Tests for the two directional scalar what-if helpers projecting
:func:`clawmetry.entitlements.lock_reason_at` onto the rung above /
below a caller-supplied source tier, and the two companion
``/api/entitlement/{next,previous}-tier-lock-reason-at`` endpoints.

These helpers fill the per-axis directional gap between:

* :func:`lock_reason_at` -- scalar what-if of ONE lock-row at a
  caller-supplied target tier
* :func:`next_tier_spec_at` / :func:`previous_tier_spec_at` -- full
  tier-row descriptor of the rung above/below a caller-supplied source

The new helpers compose those: ``lock_reason_at`` evaluated at the rung
above/below the source. Lets a paywall "what does the lock copy for
THIS item look like at my next rung?" tooltip hydrate off ONE round-trip
without re-walking the catalogue or asking the resolver. Pairs with
:func:`next_tier_feature_spec_at` / :func:`previous_tier_runtime_spec_at`
on the catalog-row side -- where those return the row, this returns the
human-readable sentence the paywall surface renders.

Pins covered here:

* per-rung byte-equality with :func:`lock_reason_at` at the resolved
  next/previous purchasable target (parity, all five axes)
* ``next``/``previous`` align with :func:`_next_purchasable_tier_after` /
  :func:`_previous_purchasable_tier_before` so the helpers cannot drift
  from the rung-walker shared with the other ``next_*_at`` family
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  returns ``None`` from the helper, and the API surfaces 200 with
  ``reason=null`` + ``locked=false`` + ``target=null`` so the surface
  keeps rendering
* trial-as-source resolves the same way the sibling ``_at`` families do:
  next -> enterprise, previous -> cloud_starter
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``)
* capacity axes (``channels`` / ``retention_days`` / ``nodes``) route
  through the ``kind=`` keyword path just like :func:`lock_reason_at`
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a builder failure short-circuits to
  ``None`` so the CTA surface keeps rendering rather than 500-ing
* the two API endpoints never 5xx: 400 on missing input / multi-axis,
  404 on unknown tier, 200 with ``reason=null`` at the ceiling / floor;
  an internal failure yields the same 200 envelope shape
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
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


# ── next_tier_lock_reason_at ────────────────────────────────────────────────


def test_next_tier_lock_reason_at_byte_equals_lock_reason_at_for_features(ent):
    # Helper is convenience for lock_reason_at(_next_purchasable_tier_after(tier), feature).
    # The two must be byte-equal across every purchasable source for every
    # feature -- pinning so the projection cannot drift from the full helper.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert ent.next_tier_lock_reason_at(
                src, feature, kind="feature"
            ) == ent.lock_reason_at(target, feature, kind="feature")


def test_next_tier_lock_reason_at_byte_equals_lock_reason_at_for_runtimes(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert ent.next_tier_lock_reason_at(
                src, runtime, kind="runtime"
            ) == ent.lock_reason_at(target, runtime, kind="runtime")


def test_next_tier_lock_reason_at_byte_equals_lock_reason_at_for_capacity(ent):
    # Capacity axes must route through ``kind=`` the same way lock_reason_at does.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for kind, count in (
            ("channels", 50),
            ("retention_days", 365),
            ("nodes", 10),
        ):
            assert ent.next_tier_lock_reason_at(
                src, str(count), kind=kind
            ) == ent.lock_reason_at(target, str(count), kind=kind)


def test_next_tier_lock_reason_at_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every item.
    assert ent._next_purchasable_tier_after(ent.TIER_ENTERPRISE) is None
    for feature in sorted(ent.ALL_FEATURES):
        assert (
            ent.next_tier_lock_reason_at(
                ent.TIER_ENTERPRISE, feature, kind="feature"
            )
            is None
        )


def test_next_tier_lock_reason_at_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro -- the next strictly-higher
    # purchasable rung is enterprise. Lenient _at posture pin.
    assert ent._next_purchasable_tier_after(ent.TIER_TRIAL) == ent.TIER_ENTERPRISE
    # An OSS-locked feature unlocks at enterprise, so the helper returns None
    # (no lock-reason -- it's allowed there).
    body = ent.next_tier_lock_reason_at(
        ent.TIER_TRIAL, "custom_alerts", kind="feature"
    )
    assert body == ent.lock_reason_at(
        ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )


def test_next_tier_lock_reason_at_inference_from_id(ent):
    # ``kind=None`` lets the inner method infer feature vs runtime from the id.
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    sample_feature = next(iter(ent.ALL_FEATURES))
    sample_runtime = next(iter(ent.ALL_RUNTIMES))
    assert ent.next_tier_lock_reason_at(
        ent.TIER_OSS, sample_feature
    ) == ent.lock_reason_at(target, sample_feature)
    assert ent.next_tier_lock_reason_at(
        ent.TIER_OSS, sample_runtime
    ) == ent.lock_reason_at(target, sample_runtime)


def test_next_tier_lock_reason_at_unknown_inputs_return_none(ent):
    # The helper must not raise on garbage input.
    assert ent.next_tier_lock_reason_at("", "custom_alerts") is None
    assert ent.next_tier_lock_reason_at(None, "custom_alerts") is None
    assert ent.next_tier_lock_reason_at("bogus_tier", "custom_alerts") is None


def test_next_tier_lock_reason_at_whitespace_and_case_insensitive(ent):
    canon = ent.next_tier_lock_reason_at(
        ent.TIER_OSS, "custom_alerts", kind="feature"
    )
    assert (
        ent.next_tier_lock_reason_at(" OSS ", " CUSTOM_ALERTS ", kind="feature")
        == canon
    )


def test_next_tier_lock_reason_at_grace_and_enforce_match(ent, monkeypatch):
    # The string is catalogue-derived (off the static per-tier maps), so
    # flipping enforce on must not change the body.
    grace_body = ent.next_tier_lock_reason_at(
        ent.TIER_OSS, "custom_alerts", kind="feature"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_body = ent.next_tier_lock_reason_at(
        ent.TIER_OSS, "custom_alerts", kind="feature"
    )
    assert enforce_body == grace_body


def test_next_tier_lock_reason_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    # A synthesised failure in the underlying lock_reason_at must short-
    # circuit to None so the CTA surface stays mute rather than 500-ing.
    monkeypatch.setattr(
        ent,
        "lock_reason_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.next_tier_lock_reason_at(
            ent.TIER_CLOUD_STARTER, "custom_alerts", kind="feature"
        )
        is None
    )


# ── previous_tier_lock_reason_at ────────────────────────────────────────────


def test_previous_tier_lock_reason_at_byte_equals_lock_reason_at_for_features(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert ent.previous_tier_lock_reason_at(
                src, feature, kind="feature"
            ) == ent.lock_reason_at(target, feature, kind="feature")


def test_previous_tier_lock_reason_at_byte_equals_lock_reason_at_for_runtimes(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert ent.previous_tier_lock_reason_at(
                src, runtime, kind="runtime"
            ) == ent.lock_reason_at(target, runtime, kind="runtime")


def test_previous_tier_lock_reason_at_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below to step down to.
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent._previous_purchasable_tier_before(src) is None
        for feature in sorted(ent.ALL_FEATURES):
            assert (
                ent.previous_tier_lock_reason_at(src, feature, kind="feature")
                is None
            )


def test_previous_tier_lock_reason_at_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter).
    assert (
        ent._previous_purchasable_tier_before(ent.TIER_TRIAL)
        == ent.TIER_CLOUD_STARTER
    )
    body = ent.previous_tier_lock_reason_at(
        ent.TIER_TRIAL, "custom_alerts", kind="feature"
    )
    assert body == ent.lock_reason_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts", kind="feature"
    )


def test_previous_tier_lock_reason_at_unknown_inputs_return_none(ent):
    assert ent.previous_tier_lock_reason_at("", "custom_alerts") is None
    assert ent.previous_tier_lock_reason_at(None, "custom_alerts") is None
    assert ent.previous_tier_lock_reason_at("bogus", "custom_alerts") is None


def test_previous_tier_lock_reason_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    monkeypatch.setattr(
        ent,
        "lock_reason_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.previous_tier_lock_reason_at(
            ent.TIER_CLOUD_PRO, "custom_alerts", kind="feature"
        )
        is None
    )


# ── /api/entitlement/next-tier-lock-reason-at ───────────────────────────────


def test_api_next_tier_lock_reason_at_happy_path_feature(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=cloud_starter&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["kind"] == "feature"
    assert body["key"] == "custom_alerts"
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["reason"] == ent.lock_reason_at(
        ent.TIER_CLOUD_PRO, "custom_alerts", kind="feature"
    )


def test_api_next_tier_lock_reason_at_happy_path_runtime(client, ent):
    sample = next(iter(ent.ALL_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/next-tier-lock-reason-at?tier=oss&runtime={sample}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kind"] == "runtime"
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert body["target"] == target
    assert body["reason"] == ent.lock_reason_at(
        target, sample, kind="runtime"
    )


def test_api_next_tier_lock_reason_at_alias_normalises(client, ent):
    # ``claude-code`` aliases to ``claude_code``.
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=oss&runtime=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["key"] == "claude_code"
    assert body["kind"] == "runtime"


def test_api_next_tier_lock_reason_at_capacity_axes(client, ent):
    for axis, val in (
        ("channels", "50"),
        ("retention_days", "365"),
        ("nodes", "10"),
    ):
        resp = client.get(
            f"/api/entitlement/next-tier-lock-reason-at?tier=oss&{axis}={val}"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["kind"] == axis
        assert body["key"] == val


def test_api_next_tier_lock_reason_at_at_ceiling_returns_200_with_null(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=enterprise&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["reason"] is None
    assert body["locked"] is False
    assert body["allowed"] is True


def test_api_next_tier_lock_reason_at_400_missing_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?feature=custom_alerts"
    )
    assert resp.status_code == 400


def test_api_next_tier_lock_reason_at_400_missing_axis(client):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=cloud_starter"
    )
    assert resp.status_code == 400


def test_api_next_tier_lock_reason_at_400_multi_axis(client):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=cloud_starter"
        "&feature=custom_alerts&runtime=claude_code"
    )
    assert resp.status_code == 400


def test_api_next_tier_lock_reason_at_404_unknown_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=bogus&feature=custom_alerts"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"


def test_api_next_tier_lock_reason_at_trial_endpoint(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-lock-reason-at?tier=trial&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["reason"] == ent.lock_reason_at(
        ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )


# ── /api/entitlement/previous-tier-lock-reason-at ───────────────────────────


def test_api_previous_tier_lock_reason_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-lock-reason-at?tier=cloud_pro&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["reason"] == ent.lock_reason_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts", kind="feature"
    )


def test_api_previous_tier_lock_reason_at_at_floor_returns_200_with_null(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-lock-reason-at?tier={src}&feature=custom_alerts"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert body["reason"] is None
        assert body["locked"] is False


def test_api_previous_tier_lock_reason_at_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-lock-reason-at?feature=custom_alerts"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-lock-reason-at?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-lock-reason-at?tier=cloud_pro"
            "&feature=custom_alerts&runtime=claude_code"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-lock-reason-at?tier=bogus&feature=custom_alerts"
        ).status_code
        == 404
    )


def test_api_previous_tier_lock_reason_at_capacity_axis(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-lock-reason-at?tier=cloud_pro&nodes=10"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kind"] == "nodes"
    assert body["key"] == "10"


def test_api_endpoints_never_5xx_on_internal_failure(client, ent, monkeypatch):
    # If the underlying helper raises, the wrapper must still return 200
    # with the grace-shape envelope so the surface stays mute.
    monkeypatch.setattr(
        ent,
        "_next_purchasable_tier_after",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    monkeypatch.setattr(
        ent,
        "_previous_purchasable_tier_before",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    for endpoint in (
        "/api/entitlement/next-tier-lock-reason-at?tier=cloud_starter&feature=custom_alerts",
        "/api/entitlement/previous-tier-lock-reason-at?tier=cloud_pro&feature=custom_alerts",
    ):
        resp = client.get(endpoint)
        assert resp.status_code == 200
        body = resp.get_json()
        assert set(body.keys()) == _ENVELOPE_KEYS
        assert body["target"] is None
        assert body["reason"] is None
        assert body["locked"] is False
        assert body["allowed"] is True
