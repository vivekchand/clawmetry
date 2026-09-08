"""Tests for the ``has_feature`` / ``has_runtime`` boolean-gate scalar
helpers and their paired ``/api/entitlement/has-feature`` /
``/api/entitlement/has-runtime`` endpoints.

These are the module-level scalar siblings of
:func:`clawmetry.entitlements.min_tier_for_feature` /
:func:`~clawmetry.entitlements.min_tier_for_runtime`: where those
answer "what is the CHEAPEST tier that unlocks this?", these answer
"does the CURRENT resolved entitlement grant it?" -- one boolean plus
the surrounding tier envelope so a paywall tile can bind ``allowed``
directly off the URL.

This file pins:

1. Scalar-helper behaviour under the two rollout modes (grace vs enforce)
   for free / paid / unknown / empty / non-string / case-normalised ids.
2. Endpoint envelope shape parity (fixed 9-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
3. Never-5xx via monkeypatched blowup on both endpoints.
4. Cross-consistency with the sibling ``/api/entitlement/required-tier``
   endpoint -- same ``required_tier`` / ``current_tier`` for the same
   key, so a UI wiring both URLs into the same paywall tile can't see
   inconsistent state.
5. The grace-mode invariant: ``has_feature`` / ``has_runtime`` report
   ``True`` for every known id while ``grace`` is on, so wiring these
   into a gate today changes no current behavior.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode. Mirrors the
    fixture used by ``tests/test_entitlements_min_tier.py`` so the
    scalar-helper assertions here reproduce the same install state the
    sibling ``min_tier_for_*`` helpers are pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture -- ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` to False so the grace pass-through collapses and the
    paid axes report their post-enforce answers."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── Envelope shape ──────────────────────────────────────────────────────────

_FEATURE_KEYS = {
    "feature",
    "has_feature",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "upgrade_required",
}
_RUNTIME_KEYS = {
    "runtime",
    "has_runtime",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "upgrade_required",
}


# ── has_feature scalar ──────────────────────────────────────────────────────


def test_has_feature_free_is_true(ent):
    """Free features return True regardless of rollout state -- the
    OSS-free entitlement grants ``FREE_FEATURES`` unconditionally."""
    for f in sorted(ent.FREE_FEATURES):
        assert ent.has_feature(f) is True, f


def test_has_feature_paid_is_true_in_grace(ent):
    """Grace invariant: while ``ent.grace`` is True, paid features
    report True. Wiring this into a gate today changes no behavior."""
    for f in sorted(ent.PAID_FEATURES):
        assert ent.has_feature(f) is True, f


def test_has_feature_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, paid features on an OSS-free install collapse
    to False -- the paywall gate wakes up when grace flips off."""
    for f in sorted(enforced.PAID_FEATURES):
        assert enforced.has_feature(f) is False, f


def test_has_feature_free_is_true_after_enforcement(enforced):
    """Free features stay True post-enforcement -- they're on OSS
    always."""
    for f in sorted(enforced.FREE_FEATURES):
        assert enforced.has_feature(f) is True, f


def test_has_feature_unknown_is_false(ent):
    """Unknown feature ids collapse to False -- we deliberately do NOT
    inherit the grace-mode "everything allowed" answer for junk input
    so a typo doesn't silently render as granted."""
    assert ent.has_feature("bogus_feature_id") is False
    assert ent.has_feature("Fleet") is False or ent.has_feature("fleet") is True
    # Case normalisation applies BEFORE the ALL_FEATURES check --
    # "Fleet" strips-lowers to "fleet" which IS known, so it returns
    # grace-True.
    assert ent.has_feature("Fleet") is True


def test_has_feature_empty_is_false(ent):
    """Empty / whitespace-only / None ids collapse to False."""
    assert ent.has_feature("") is False
    assert ent.has_feature("   ") is False
    assert ent.has_feature(None) is False  # type: ignore[arg-type]


def test_has_feature_non_string_is_false(ent):
    """Non-string ids collapse to False without raising."""
    assert ent.has_feature(123) is False  # type: ignore[arg-type]
    assert ent.has_feature([]) is False  # type: ignore[arg-type]
    assert ent.has_feature({}) is False  # type: ignore[arg-type]


def test_has_feature_case_insensitive(ent):
    """Casing / whitespace on a known id normalises before the
    membership check."""
    known = next(iter(sorted(ent.PAID_FEATURES)))
    assert ent.has_feature(known) is True
    assert ent.has_feature(known.upper()) is True
    assert ent.has_feature(f"  {known}  ") is True


def test_has_feature_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup in ``get_entitlement`` collapses to False so a caller
    can bind this into a boolean AND-chain without a try/except."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in ["fleet", "nemo_governance", "", None, 123]:
        assert ent.has_feature(arg) is False  # type: ignore[arg-type]


# ── has_runtime scalar ──────────────────────────────────────────────────────


def test_has_runtime_free_is_true(ent):
    """FREE_RUNTIMES return True regardless of rollout state."""
    for rt in sorted(ent.FREE_RUNTIMES):
        assert ent.has_runtime(rt) is True, rt


def test_has_runtime_paid_is_true_in_grace(ent):
    """Grace invariant on the runtime axis: paid runtimes report True
    while grace is on."""
    for rt in sorted(ent.PAID_RUNTIMES):
        assert ent.has_runtime(rt) is True, rt


def test_has_runtime_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, paid runtimes on OSS collapse to False."""
    for rt in sorted(enforced.PAID_RUNTIMES):
        assert enforced.has_runtime(rt) is False, rt


def test_has_runtime_free_is_true_after_enforcement(enforced):
    """Free runtimes stay True post-enforcement."""
    for rt in sorted(enforced.FREE_RUNTIMES):
        assert enforced.has_runtime(rt) is True, rt


def test_has_runtime_unknown_is_false(ent):
    """Unknown runtime ids collapse to False -- typo caught at the
    callsite in both grace and enforce."""
    assert ent.has_runtime("bogus_runtime") is False
    assert ent.has_runtime("clawmetry") is False


def test_has_runtime_empty_is_false(ent):
    """Empty / whitespace / None collapse to False."""
    assert ent.has_runtime("") is False
    assert ent.has_runtime("   ") is False
    assert ent.has_runtime(None) is False  # type: ignore[arg-type]


def test_has_runtime_non_string_is_false(ent):
    """Non-string collapses to False without raising."""
    assert ent.has_runtime(123) is False  # type: ignore[arg-type]
    assert ent.has_runtime([]) is False  # type: ignore[arg-type]


def test_has_runtime_case_insensitive(ent):
    """Casing / whitespace on a known runtime normalises."""
    assert ent.has_runtime("OPENCLAW") is True
    assert ent.has_runtime("  openclaw  ") is True
    assert ent.has_runtime("Claude_Code") is True  # grace pass-through


def test_has_runtime_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup collapses to False."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in ["openclaw", "claude_code", "", None, 123]:
        assert ent.has_runtime(arg) is False  # type: ignore[arg-type]


# ── /api/entitlement/has-feature envelope ───────────────────────────────────


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


def test_has_feature_endpoint_free_shape(client):
    body = _get_json(client, "/api/entitlement/has-feature?feature=nemo_governance")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == "nemo_governance"
    assert body["has_feature"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is False


def test_has_feature_endpoint_paid_grace_shape(client):
    """Paid feature under grace: has_feature=True (grace grant), but
    upgrade_required=True (post-enforce would need Starter)."""
    body = _get_json(client, "/api/entitlement/has-feature?feature=fleet")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == "fleet"
    assert body["has_feature"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["current_tier"] == "oss"
    assert body["upgrade_required"] is True


def test_has_feature_endpoint_unknown_shape(client):
    body = _get_json(client, "/api/entitlement/has-feature?feature=bogus")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == "bogus"
    assert body["has_feature"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False


def test_has_feature_endpoint_empty_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-feature")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == ""
    assert body["has_feature"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["upgrade_required"] is False


def test_has_feature_endpoint_blank_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-feature?feature=")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == ""
    assert body["has_feature"] is False


def test_has_feature_endpoint_whitespace_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-feature?feature=%20%20%20")
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == ""
    assert body["has_feature"] is False


def test_has_feature_endpoint_case_normalises(client):
    body = _get_json(client, "/api/entitlement/has-feature?feature=Fleet")
    assert body["feature"] == "fleet"
    assert body["has_feature"] is True
    assert body["required_tier"] == "cloud_starter"


# ── /api/entitlement/has-runtime envelope ───────────────────────────────────


def test_has_runtime_endpoint_free_shape(client):
    body = _get_json(client, "/api/entitlement/has-runtime?runtime=openclaw")
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["runtime"] == "openclaw"
    assert body["has_runtime"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["current_tier"] == "oss"
    assert body["upgrade_required"] is False


def test_has_runtime_endpoint_paid_grace_shape(client):
    """Paid runtime under grace: has_runtime=True (grace grant), but
    upgrade_required=True (post-enforce would need Starter)."""
    body = _get_json(client, "/api/entitlement/has-runtime?runtime=claude_code")
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["runtime"] == "claude_code"
    assert body["has_runtime"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["upgrade_required"] is True


def test_has_runtime_endpoint_unknown_shape(client):
    body = _get_json(client, "/api/entitlement/has-runtime?runtime=bogus")
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["runtime"] == "bogus"
    assert body["has_runtime"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False


def test_has_runtime_endpoint_empty_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-runtime")
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["runtime"] == ""
    assert body["has_runtime"] is False


def test_has_runtime_endpoint_case_normalises(client):
    body = _get_json(client, "/api/entitlement/has-runtime?runtime=CLAUDE_CODE")
    assert body["runtime"] == "claude_code"
    assert body["has_runtime"] is True


# ── Never-5xx (monkeypatched blowup) ────────────────────────────────────────


def test_has_feature_endpoint_never_5xx(monkeypatch, client, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_axis_body", _boom)
    resp = client.get("/api/entitlement/has-feature?feature=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURE_KEYS
    assert body["feature"] == "fleet"
    assert body["has_feature"] is False
    assert body["allowed"] is False


def test_has_runtime_endpoint_never_5xx(monkeypatch, client, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_axis_body", _boom)
    resp = client.get("/api/entitlement/has-runtime?runtime=claude_code")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIME_KEYS
    assert body["runtime"] == "claude_code"
    assert body["has_runtime"] is False


# ── Cross-consistency with /required-tier ───────────────────────────────────


@pytest.mark.parametrize("feature", ["nemo_governance", "fleet", "self_evolve"])
def test_has_feature_cross_consistent_with_required_tier(client, feature):
    """Same input -> same tier answer on both endpoints. A UI wiring
    ``/has-feature`` and ``/required-tier`` into the same paywall tile
    can't see inconsistent tier state."""
    has_body = _get_json(client, f"/api/entitlement/has-feature?feature={feature}")
    req_body = _get_json(client, f"/api/entitlement/required-tier?feature={feature}")
    assert has_body["required_tier"] == req_body["required_tier"]
    assert has_body["required_tier_label"] == req_body["required_tier_label"]
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"]
    assert has_body["current_tier"] == req_body["current_tier"]
    assert has_body["current_tier_rank"] == req_body["current_tier_rank"]
    assert has_body["upgrade_required"] == req_body["upgrade_required"]


@pytest.mark.parametrize("runtime", ["openclaw", "nemoclaw", "claude_code", "codex"])
def test_has_runtime_cross_consistent_with_required_tier(client, runtime):
    has_body = _get_json(client, f"/api/entitlement/has-runtime?runtime={runtime}")
    req_body = _get_json(client, f"/api/entitlement/required-tier?runtime={runtime}")
    assert has_body["required_tier"] == req_body["required_tier"]
    assert has_body["required_tier_label"] == req_body["required_tier_label"]
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"]
    assert has_body["current_tier"] == req_body["current_tier"]
    assert has_body["upgrade_required"] == req_body["upgrade_required"]


# ── Scalar-vs-endpoint parity ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "feature",
    ["nemo_governance", "fleet", "self_evolve", "bogus_id", ""],
)
def test_has_feature_endpoint_matches_scalar(client, ent, feature):
    """Envelope ``has_feature`` value matches the module-level scalar
    byte-for-byte -- no drift possible between the two."""
    body = _get_json(client, f"/api/entitlement/has-feature?feature={feature}")
    assert body["has_feature"] is ent.has_feature(feature)
    assert body["allowed"] is ent.has_feature(feature)


@pytest.mark.parametrize(
    "runtime",
    ["openclaw", "claude_code", "codex", "bogus_id", ""],
)
def test_has_runtime_endpoint_matches_scalar(client, ent, runtime):
    body = _get_json(client, f"/api/entitlement/has-runtime?runtime={runtime}")
    assert body["has_runtime"] is ent.has_runtime(runtime)
    assert body["allowed"] is ent.has_runtime(runtime)


# ── Grace invariant on both axes ────────────────────────────────────────────


def test_grace_invariant_all_known_features_report_true(ent):
    """The headline grace invariant: while grace is on, every known
    feature (free OR paid) reports ``has_feature=True``. This is what
    makes wiring this into a gate today a no-op behavior change."""
    for f in sorted(ent.ALL_FEATURES):
        assert ent.has_feature(f) is True, f


def test_grace_invariant_all_known_runtimes_report_true(ent):
    """Grace invariant on the runtime axis -- every known runtime
    reports ``has_runtime=True`` while grace is on."""
    for rt in sorted(ent.ALL_RUNTIMES):
        assert ent.has_runtime(rt) is True, rt


def test_enforce_paid_runtimes_all_locked_on_oss(enforced):
    """Symmetric assertion on the enforcement side: every paid runtime
    reports ``has_runtime=False`` on an OSS install once enforcement is
    on."""
    for rt in sorted(enforced.PAID_RUNTIMES):
        assert enforced.has_runtime(rt) is False, rt


def test_enforce_paid_features_all_locked_on_oss(enforced):
    """Symmetric assertion on the feature axis under enforcement."""
    for f in sorted(enforced.PAID_FEATURES):
        assert enforced.has_feature(f) is False, f
