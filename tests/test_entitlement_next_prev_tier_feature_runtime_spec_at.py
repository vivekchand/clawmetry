"""Tests for the four directional scalar what-if helpers projecting
:func:`clawmetry.entitlements.next_tier_spec_at` /
:func:`previous_tier_spec_at` onto a single feature or runtime, and the
four companion ``/api/entitlement/{next,previous}-tier-{feature,runtime}-spec-at``
endpoints.

These helpers fill the per-axis directional gap between:

* :func:`feature_spec_at` / :func:`runtime_spec_at` -- scalar what-if of
  ONE feature/runtime at a caller-supplied target tier
* :func:`next_tier_spec_at` / :func:`previous_tier_spec_at` -- full
  tier-row descriptor of the rung above/below a caller-supplied source

The new helpers compose those: ``feature_spec_at`` /
``runtime_spec_at`` evaluated at the rung above/below the source. Lets a
paywall "does THIS feature/runtime unlock at my next rung?" tooltip
hydrate off ONE round-trip without re-walking the catalogue or asking
the resolver.

Pins covered here:

* per-rung byte-equality with :func:`feature_spec_at` /
  :func:`runtime_spec_at` at the resolved next/previous purchasable
  target (parity)
* ``next``/``previous`` align with :func:`_next_purchasable_tier_after`
  / :func:`_previous_purchasable_tier_before` so the helpers cannot
  drift from the rung-walker shared with the other ``next_*_at`` family
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  returns ``None`` from the helper, and the API surfaces 200 with
  ``row=null`` + ``target=null`` so the surface keeps rendering
* trial-as-source resolves the same way the sibling ``_at`` families
  do: next -> enterprise, previous -> cloud_starter
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``) on
  helper and API
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a builder failure short-circuits to
  ``None`` so the CTA surface keeps rendering rather than 500-ing
* the four API endpoints never 5xx: 400 on missing input, 404 on
  unknown ids, 200 with ``row=null`` at the ceiling / floor; an
  internal failure yields the same 200 envelope shape
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_AT_ENVELOPE_FEATURE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "feature",
    "target",
    "target_label",
    "target_rank",
    "row",
}

_AT_ENVELOPE_RUNTIME_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "runtime",
    "target",
    "target_label",
    "target_rank",
    "row",
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


# ── next_tier_feature_spec_at ────────────────────────────────────────────


def test_next_tier_feature_spec_at_byte_equals_feature_spec_at(ent):
    # Helper is convenience for feature_spec_at(_next_purchasable_tier_after(tier), feature).
    # The two must be byte-equal across every purchasable source for every
    # feature -- pinning so the projection cannot drift from the full-row
    # sibling.
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert ent.next_tier_feature_spec_at(src, feature) == ent.feature_spec_at(
                target, feature
            )


def test_next_tier_feature_spec_at_returns_none_at_ceiling(ent):
    # Enterprise sits at the top of the purchasable ladder -- no rung above,
    # so the helper returns None for every feature.
    assert ent._next_purchasable_tier_after(ent.TIER_ENTERPRISE) is None
    for feature in sorted(ent.ALL_FEATURES):
        assert ent.next_tier_feature_spec_at(ent.TIER_ENTERPRISE, feature) is None


def test_next_tier_feature_spec_at_trial_resolves_to_enterprise(ent):
    # Trial sits at rank 2 alongside cloud_pro / self-hosted pro -- the next
    # strictly-higher purchasable rung is enterprise (rank 3). Pinning so the
    # lenient _at posture matches the sibling ``next_*_at`` helpers.
    assert ent._next_purchasable_tier_after(ent.TIER_TRIAL) == ent.TIER_ENTERPRISE
    body = ent.next_tier_feature_spec_at(ent.TIER_TRIAL, "custom_alerts")
    assert body is not None
    assert body == ent.feature_spec_at(ent.TIER_ENTERPRISE, "custom_alerts")


def test_next_tier_feature_spec_at_unknown_inputs_return_none(ent):
    # The helper must not raise on garbage input -- empty/None/case/whitespace
    # mismatch must all short-circuit to None.
    assert ent.next_tier_feature_spec_at("", "custom_alerts") is None
    assert ent.next_tier_feature_spec_at(None, "custom_alerts") is None
    assert ent.next_tier_feature_spec_at("bogus_tier", "custom_alerts") is None
    assert ent.next_tier_feature_spec_at(ent.TIER_CLOUD_STARTER, "") is None
    assert ent.next_tier_feature_spec_at(ent.TIER_CLOUD_STARTER, None) is None
    assert ent.next_tier_feature_spec_at(ent.TIER_CLOUD_STARTER, "no_such_feature") is None


def test_next_tier_feature_spec_at_whitespace_and_case_insensitive(ent):
    # Whitespace + case normalisation must match the sibling _at helpers --
    # caller-supplied input is normalised before lookup.
    canon = ent.next_tier_feature_spec_at(ent.TIER_CLOUD_STARTER, "custom_alerts")
    assert canon is not None
    assert (
        ent.next_tier_feature_spec_at(" CLOUD_STARTER ", " CUSTOM_ALERTS ") == canon
    )


def test_next_tier_feature_spec_at_grace_and_enforce_match(ent, monkeypatch):
    # The row is catalogue-derived (off the static per-tier maps), so flipping
    # enforce on must not change the body.
    grace_body = ent.next_tier_feature_spec_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_body = ent.next_tier_feature_spec_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts"
    )
    assert enforce_body == grace_body


def test_next_tier_feature_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    # A synthesised failure in the underlying feature_spec_at must short-
    # circuit to None so the CTA surface stays mute rather than 500-ing.
    monkeypatch.setattr(
        ent,
        "feature_spec_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.next_tier_feature_spec_at(ent.TIER_CLOUD_STARTER, "custom_alerts")
        is None
    )


# ── previous_tier_feature_spec_at ────────────────────────────────────────────


def test_previous_tier_feature_spec_at_byte_equals_feature_spec_at(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for feature in sorted(ent.ALL_FEATURES):
            assert ent.previous_tier_feature_spec_at(
                src, feature
            ) == ent.feature_spec_at(target, feature)


def test_previous_tier_feature_spec_at_returns_none_at_floor(ent):
    # OSS and cloud_free both sit at rank 0 -- no rung below to step down to,
    # so the helper returns None for every feature on either source.
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        assert ent._previous_purchasable_tier_before(src) is None
        for feature in sorted(ent.ALL_FEATURES):
            assert ent.previous_tier_feature_spec_at(src, feature) is None


def test_previous_tier_feature_spec_at_trial_resolves_to_starter(ent):
    # Trial steps down to rank 1 (starter).
    assert ent._previous_purchasable_tier_before(ent.TIER_TRIAL) == ent.TIER_CLOUD_STARTER
    body = ent.previous_tier_feature_spec_at(ent.TIER_TRIAL, "custom_alerts")
    assert body is not None
    assert body == ent.feature_spec_at(ent.TIER_CLOUD_STARTER, "custom_alerts")


def test_previous_tier_feature_spec_at_unknown_inputs_return_none(ent):
    assert ent.previous_tier_feature_spec_at("", "custom_alerts") is None
    assert ent.previous_tier_feature_spec_at(None, "custom_alerts") is None
    assert ent.previous_tier_feature_spec_at("bogus", "custom_alerts") is None
    assert ent.previous_tier_feature_spec_at(ent.TIER_CLOUD_PRO, "") is None
    assert ent.previous_tier_feature_spec_at(ent.TIER_CLOUD_PRO, None) is None
    assert ent.previous_tier_feature_spec_at(ent.TIER_CLOUD_PRO, "no_such") is None


def test_previous_tier_feature_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    monkeypatch.setattr(
        ent,
        "feature_spec_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.previous_tier_feature_spec_at(ent.TIER_CLOUD_PRO, "custom_alerts")
        is None
    )


# ── next_tier_runtime_spec_at ────────────────────────────────────────────


def test_next_tier_runtime_spec_at_byte_equals_runtime_spec_at(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert ent.next_tier_runtime_spec_at(
                src, runtime
            ) == ent.runtime_spec_at(target, runtime)


def test_next_tier_runtime_spec_at_returns_none_at_ceiling(ent):
    for runtime in sorted(ent.ALL_RUNTIMES):
        assert ent.next_tier_runtime_spec_at(ent.TIER_ENTERPRISE, runtime) is None


def test_next_tier_runtime_spec_at_alias_resolution(ent):
    # ``claude-code`` aliases to ``claude_code`` -- the helper must
    # canonicalise so both spellings yield byte-equal output, matching the
    # sibling /runtime-spec-at posture.
    canon = ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, "claude_code")
    assert canon is not None
    assert (
        ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, "claude-code")
        == canon
    )
    assert (
        ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, " CLAUDE-CODE ")
        == canon
    )


def test_next_tier_runtime_spec_at_unknown_inputs_return_none(ent):
    assert ent.next_tier_runtime_spec_at("", "claude_code") is None
    assert ent.next_tier_runtime_spec_at(None, "claude_code") is None
    assert ent.next_tier_runtime_spec_at("bogus", "claude_code") is None
    assert ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, "") is None
    assert ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, None) is None
    assert ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, "no_such") is None


def test_next_tier_runtime_spec_at_grace_and_enforce_match(ent, monkeypatch):
    grace_body = ent.next_tier_runtime_spec_at(
        ent.TIER_CLOUD_STARTER, "claude_code"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_body = ent.next_tier_runtime_spec_at(
        ent.TIER_CLOUD_STARTER, "claude_code"
    )
    assert enforce_body == grace_body


def test_next_tier_runtime_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    monkeypatch.setattr(
        ent,
        "runtime_spec_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.next_tier_runtime_spec_at(ent.TIER_CLOUD_STARTER, "claude_code")
        is None
    )


# ── previous_tier_runtime_spec_at ────────────────────────────────────────────


def test_previous_tier_runtime_spec_at_byte_equals_runtime_spec_at(ent):
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert ent.previous_tier_runtime_spec_at(
                src, runtime
            ) == ent.runtime_spec_at(target, runtime)


def test_previous_tier_runtime_spec_at_returns_none_at_floor(ent):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        for runtime in sorted(ent.ALL_RUNTIMES):
            assert ent.previous_tier_runtime_spec_at(src, runtime) is None


def test_previous_tier_runtime_spec_at_alias_resolution(ent):
    canon = ent.previous_tier_runtime_spec_at(ent.TIER_CLOUD_PRO, "claude_code")
    assert canon is not None
    assert (
        ent.previous_tier_runtime_spec_at(ent.TIER_CLOUD_PRO, "claude-code") == canon
    )


def test_previous_tier_runtime_spec_at_never_raises_on_builder_failure(
    ent, monkeypatch
):
    monkeypatch.setattr(
        ent,
        "runtime_spec_at",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.previous_tier_runtime_spec_at(ent.TIER_CLOUD_PRO, "claude_code")
        is None
    )


# ── /api/entitlement/next-tier-feature-spec-at ───────────────────────────────────


def test_api_next_tier_feature_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=cloud_starter&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_FEATURE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["feature"] == "custom_alerts"
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["row"] == ent.feature_spec_at(ent.TIER_CLOUD_PRO, "custom_alerts")


def test_api_next_tier_feature_spec_at_at_ceiling_returns_200_with_null_row(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=enterprise&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["row"] is None


def test_api_next_tier_feature_spec_at_400_missing_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?feature=custom_alerts"
    )
    assert resp.status_code == 400


def test_api_next_tier_feature_spec_at_400_missing_feature(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=cloud_starter"
    )
    assert resp.status_code == 400


def test_api_next_tier_feature_spec_at_404_unknown_tier(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=bogus&feature=custom_alerts"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "tier"


def test_api_next_tier_feature_spec_at_404_unknown_feature(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=cloud_starter&feature=no_such"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("which") == "feature"


def test_api_next_tier_feature_spec_at_trial_endpoint(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at?tier=trial&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["row"] == ent.feature_spec_at(ent.TIER_ENTERPRISE, "custom_alerts")


# ── /api/entitlement/previous-tier-feature-spec-at ───────────────────────────────


def test_api_previous_tier_feature_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-spec-at?tier=cloud_pro&feature=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_FEATURE_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["feature"] == "custom_alerts"
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.feature_spec_at(
        ent.TIER_CLOUD_STARTER, "custom_alerts"
    )


def test_api_previous_tier_feature_spec_at_at_floor_returns_200_with_null_row(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-feature-spec-at?tier={src}&feature=custom_alerts"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert body["row"] is None


def test_api_previous_tier_feature_spec_at_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at?feature=custom_alerts"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at?tier=bogus&feature=custom_alerts"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-feature-spec-at?tier=cloud_pro&feature=no_such"
        ).status_code
        == 404
    )


# ── /api/entitlement/next-tier-runtime-spec-at ─────────────────────────────────


def test_api_next_tier_runtime_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at?tier=cloud_starter&runtime=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_RUNTIME_KEYS
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["runtime"] == "claude_code"
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "claude_code")


def test_api_next_tier_runtime_spec_at_alias_normalises(client, ent):
    # The route accepts ``claude-code`` and echoes the canonical id in the
    # envelope so a UI consuming the response sees the same id regardless of
    # the spelling sent in.
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at?tier=cloud_starter&runtime=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtime"] == "claude_code"
    assert body["row"] == ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "claude_code")


def test_api_next_tier_runtime_spec_at_at_ceiling_returns_200_with_null_row(
    client, ent
):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at?tier=enterprise&runtime=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["row"] is None


def test_api_next_tier_runtime_spec_at_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at?runtime=claude_code"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at?tier=cloud_starter"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at?tier=bogus&runtime=claude_code"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/entitlement/next-tier-runtime-spec-at?tier=cloud_starter&runtime=no_such"
        ).status_code
        == 404
    )


# ── /api/entitlement/previous-tier-runtime-spec-at ──────────────────────────────


def test_api_previous_tier_runtime_spec_at_happy_path(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-spec-at?tier=cloud_pro&runtime=claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_RUNTIME_KEYS
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["runtime"] == "claude_code"
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["row"] == ent.runtime_spec_at(
        ent.TIER_CLOUD_STARTER, "claude_code"
    )


def test_api_previous_tier_runtime_spec_at_at_floor_returns_200_with_null_row(
    client, ent
):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        resp = client.get(
            f"/api/entitlement/previous-tier-runtime-spec-at?tier={src}&runtime=claude_code"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tier"] == src
        assert body["target"] is None
        assert body["row"] is None


def test_api_previous_tier_runtime_spec_at_alias_normalises(client, ent):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-spec-at?tier=cloud_pro&runtime=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtime"] == "claude_code"


def test_api_previous_tier_runtime_spec_at_400s_and_404s(client):
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at?runtime=claude_code"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at?tier=cloud_pro"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at?tier=bogus&runtime=claude_code"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/entitlement/previous-tier-runtime-spec-at?tier=cloud_pro&runtime=no_such"
        ).status_code
        == 404
    )
