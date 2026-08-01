"""Tests for the plural ``has_features`` / ``has_runtimes`` boolean-gate
scalar helpers and their paired ``/api/entitlement/has-features`` /
``/api/entitlement/has-runtimes`` endpoints.

Plural siblings of ``has_feature`` / ``has_runtime`` on the same axis: where
the singular scalars answer "does the CURRENT resolved entitlement grant
THIS id?", these fold the answer across a whole bundle -- ``True`` iff every
item is granted (the tightest single-item denial wins). One boolean off the
whole set plus a surrounding tier envelope so a paywall tile gating on a
mixed bundle (``fleet + otel_export + sso``) can bind ``allowed`` directly
off ONE URL instead of parsing the fuller ``/api/entitlement/min-tier-for-
features`` body plus a follow-up hit to ``/has-feature`` per item.

This file pins:

1. Scalar behaviour under grace vs enforce for empty / non-iterable /
   None / unknown / mixed known+unknown / all-free / all-paid bundles.
2. Endpoint envelope shape parity (fixed 14-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
3. Never-5xx via monkeypatched blowup on both endpoints.
4. Cross-consistency with the sibling
   ``/api/entitlement/min-tier-for-features`` /
   ``/min-tier-for-runtimes`` endpoints -- same ``required_tier`` /
   ``current_tier`` for the same bundle, so a UI wiring both URLs into
   the same paywall tile can't see inconsistent tier state.
5. The grace-mode invariant: ``has_features`` / ``has_runtimes`` report
   ``True`` for every fully-known bundle while ``grace`` is on, so
   wiring these into a gate today changes NO current behavior.
6. Scalar-vs-endpoint parity: the URL ``has_<axis>`` value equals the
   module-level scalar byte-for-byte on the same input.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ───────────────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- same fixture the
    sibling ``test_entitlement_has_feature_has_runtime.py`` uses so the
    plural-helper assertions here reproduce the same install state the
    singular ones are pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips ``ent.grace``
    off so the grace pass-through collapses and paid axes report their
    post-enforce answers."""
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


# ── Envelope shape ────────────────────────────────────────────────────────────────────────

_FEATURES_KEYS = {
    "features",
    "unknown",
    "kind",
    "count",
    "has_features",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "upgrade_required",
}
_RUNTIMES_KEYS = {
    "runtimes",
    "unknown",
    "kind",
    "count",
    "has_runtimes",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "upgrade_required",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_features scalar ──────────────────────────────────────────────────────────────────────────


def test_has_features_all_free_is_true(ent):
    """A bundle of ONLY free features reports True regardless of rollout
    state -- the OSS-free entitlement grants ``FREE_FEATURES``
    unconditionally per item, so the AND-fold is True."""
    free = sorted(ent.FREE_FEATURES)
    assert ent.has_features(free) is True


def test_has_features_all_paid_is_true_in_grace(ent):
    """Grace invariant on the plural fold: while ``ent.grace`` is True,
    every paid feature reports True per item, so the AND-fold is True."""
    paid = sorted(ent.PAID_FEATURES)
    assert ent.has_features(paid) is True


def test_has_features_all_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, any paid feature on OSS collapses the fold to
    False -- the tightest single-item denial wins."""
    paid = sorted(enforced.PAID_FEATURES)
    assert enforced.has_features(paid) is False


def test_has_features_mixed_free_and_paid_is_true_in_grace(ent):
    """A mixed bundle (free + paid) reports True in grace because each
    per-item ``has_feature`` reports True."""
    mixed = [next(iter(ent.FREE_FEATURES)), next(iter(ent.PAID_FEATURES))]
    assert ent.has_features(mixed) is True


def test_has_features_mixed_free_and_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, a mixed bundle collapses to False -- the paid
    item denies the whole fold."""
    mixed = [
        next(iter(enforced.FREE_FEATURES)),
        next(iter(enforced.PAID_FEATURES)),
    ]
    assert enforced.has_features(mixed) is False


def test_has_features_any_unknown_is_false_in_grace(ent):
    """Even in grace, an unknown item collapses the fold to False --
    ``has_feature("bogus")`` is False and the AND-fold inherits that. Catches
    typos at the callsite before enforcement flips on."""
    assert ent.has_features(["fleet", "bogus_id"]) is False
    assert ent.has_features(["bogus_id"]) is False


def test_has_features_all_unknown_is_false(ent):
    """A bundle of only-unknown items reports False."""
    assert ent.has_features(["bogus_a", "bogus_b"]) is False


def test_has_features_empty_iterable_is_false(ent):
    """Empty iterable collapses to False (strict callsite-typo posture) --
    matches the singular ``has_feature("")`` empty-input False."""
    assert ent.has_features([]) is False
    assert ent.has_features(()) is False
    assert ent.has_features(iter(())) is False


def test_has_features_none_is_false(ent):
    """``None`` collapses to False without raising."""
    assert ent.has_features(None) is False  # type: ignore[arg-type]


def test_has_features_non_iterable_is_false(ent):
    """Non-iterable input (int, arbitrary object) collapses to False."""
    assert ent.has_features(123) is False  # type: ignore[arg-type]
    assert ent.has_features(object()) is False  # type: ignore[arg-type]


def test_has_features_case_insensitive(ent):
    """Casing / whitespace on known ids normalises via the per-item
    delegate."""
    known = next(iter(sorted(ent.PAID_FEATURES)))
    assert ent.has_features([known.upper(), f"  {known}  "]) is True


def test_has_features_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup in the underlying delegate collapses the fold to
    False so a caller can bind this into a boolean AND-chain without a
    try/except."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in [
        ["fleet"],
        ["fleet", "nemo_governance"],
        [],
        None,
        123,
    ]:
        assert ent.has_features(arg) is False  # type: ignore[arg-type]


# ── has_runtimes scalar ──────────────────────────────────────────────────────────────────────────


def test_has_runtimes_all_free_is_true(ent):
    """A bundle of ONLY free runtimes reports True regardless of rollout
    state."""
    free = sorted(ent.FREE_RUNTIMES)
    assert ent.has_runtimes(free) is True


def test_has_runtimes_all_paid_is_true_in_grace(ent):
    """Grace invariant on the runtime axis."""
    paid = sorted(ent.PAID_RUNTIMES)
    assert ent.has_runtimes(paid) is True


def test_has_runtimes_all_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, any paid runtime on OSS collapses the fold."""
    paid = sorted(enforced.PAID_RUNTIMES)
    assert enforced.has_runtimes(paid) is False


def test_has_runtimes_mixed_free_and_paid_is_false_after_enforcement(enforced):
    """Post-enforcement, a mixed bundle collapses to False."""
    mixed = [
        next(iter(enforced.FREE_RUNTIMES)),
        next(iter(enforced.PAID_RUNTIMES)),
    ]
    assert enforced.has_runtimes(mixed) is False


def test_has_runtimes_any_unknown_is_false(ent):
    """Unknown runtime id in the bundle collapses to False even in grace."""
    assert ent.has_runtimes(["openclaw", "bogus_runtime"]) is False


def test_has_runtimes_empty_iterable_is_false(ent):
    """Empty iterable collapses to False."""
    assert ent.has_runtimes([]) is False


def test_has_runtimes_none_is_false(ent):
    assert ent.has_runtimes(None) is False  # type: ignore[arg-type]


def test_has_runtimes_non_iterable_is_false(ent):
    assert ent.has_runtimes(42) is False  # type: ignore[arg-type]


def test_has_runtimes_case_insensitive(ent):
    """Casing / whitespace normalises via ``has_runtime``."""
    assert ent.has_runtimes(["OPENCLAW", "  nemoclaw  "]) is True


def test_has_runtimes_never_raises_on_resolver_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in [["openclaw"], ["openclaw", "claude_code"], [], None]:
        assert ent.has_runtimes(arg) is False  # type: ignore[arg-type]


# ── /api/entitlement/has-features envelope ────────────────────────────────────────────────


def test_has_features_endpoint_all_free_shape(client):
    body = _get_json(
        client, "/api/entitlement/has-features?features=nemo_governance"
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == ["nemo_governance"]
    assert body["unknown"] == []
    assert body["kind"] == "features"
    assert body["count"] == 1
    assert body["has_features"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["upgrade_required"] is False


def test_has_features_endpoint_mixed_paid_grace_shape(client):
    """Mixed free+paid bundle under grace: has_features=True (grace grants
    every known id) but upgrade_required=True (post-enforce needs Starter)."""
    body = _get_json(
        client,
        "/api/entitlement/has-features?features=nemo_governance,fleet",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == ["nemo_governance", "fleet"]
    assert body["unknown"] == []
    assert body["count"] == 2
    assert body["has_features"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["current_tier"] == "oss"
    assert body["upgrade_required"] is True


def test_has_features_endpoint_unknown_collapses_bundle(client):
    """An unknown token collapses has_features to False even in grace,
    but the known part still routes ``required_tier`` correctly."""
    body = _get_json(
        client, "/api/entitlement/has-features?features=fleet,bogus_id"
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == ["fleet"]
    assert body["unknown"] == ["bogus_id"]
    assert body["count"] == 1
    assert body["has_features"] is False
    assert body["allowed"] is False
    assert body["required_tier"] == "cloud_starter"
    assert body["upgrade_required"] is True


def test_has_features_endpoint_all_unknown_shape(client):
    body = _get_json(
        client, "/api/entitlement/has-features?features=bogus_a,bogus_b"
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == []
    assert body["unknown"] == ["bogus_a", "bogus_b"]
    assert body["count"] == 0
    assert body["has_features"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False


def test_has_features_endpoint_missing_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-features")
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["count"] == 0
    assert body["has_features"] is False
    assert body["allowed"] is False


def test_has_features_endpoint_blank_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-features?features=")
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["has_features"] is False


def test_has_features_endpoint_whitespace_and_dupe_stripping(client):
    """CSV normalisation strips whitespace, drops empties, dedupes
    (first-seen order preserved) via ``_parse_csv_arg`` -- same rule the
    ``/api/entitlement/min-tier-for-features`` endpoint uses."""
    body = _get_json(
        client,
        "/api/entitlement/has-features?features=%20fleet%20,,fleet,%20sso%20",
    )
    assert body["features"] == ["fleet", "sso"]
    assert body["unknown"] == []
    assert body["count"] == 2


def test_has_features_endpoint_case_normalises(client):
    body = _get_json(client, "/api/entitlement/has-features?features=Fleet,SSO")
    assert body["features"] == ["fleet", "sso"]
    assert body["has_features"] is True


# ── /api/entitlement/has-runtimes envelope ────────────────────────────────────────────────


def test_has_runtimes_endpoint_all_free_shape(client):
    body = _get_json(
        client, "/api/entitlement/has-runtimes?runtimes=openclaw,nemoclaw"
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == ["openclaw", "nemoclaw"]
    assert body["unknown"] == []
    assert body["kind"] == "runtimes"
    assert body["count"] == 2
    assert body["has_runtimes"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_rank"] == 0
    assert body["upgrade_required"] is False


def test_has_runtimes_endpoint_paid_grace_shape(client):
    body = _get_json(
        client, "/api/entitlement/has-runtimes?runtimes=claude_code,codex"
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == ["claude_code", "codex"]
    assert body["unknown"] == []
    assert body["count"] == 2
    assert body["has_runtimes"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["upgrade_required"] is True


def test_has_runtimes_endpoint_unknown_collapses_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-runtimes?runtimes=openclaw,bogus_runtime",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == ["openclaw"]
    assert body["unknown"] == ["bogus_runtime"]
    assert body["count"] == 1
    assert body["has_runtimes"] is False
    assert body["allowed"] is False


def test_has_runtimes_endpoint_missing_param_shape(client):
    body = _get_json(client, "/api/entitlement/has-runtimes")
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == []
    assert body["unknown"] == []
    assert body["has_runtimes"] is False


def test_has_runtimes_endpoint_case_normalises(client):
    body = _get_json(
        client, "/api/entitlement/has-runtimes?runtimes=OPENCLAW,CLAUDE_CODE"
    )
    assert body["runtimes"] == ["openclaw", "claude_code"]
    assert body["has_runtimes"] is True


def test_has_runtimes_endpoint_alias_canonicalises(client):
    """Runtime aliases (``claude-code`` -> ``claude_code``) canonicalise via
    :func:`clawmetry.entitlements.canonical_runtime` before the known/unknown
    split, so a caller doesn't need to normalise before hitting the URL."""
    body = _get_json(
        client, "/api/entitlement/has-runtimes?runtimes=claude-code"
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["unknown"] == []
    assert body["has_runtimes"] is True


# ── Never-5xx (monkeypatched blowup) ──────────────────────────────────────────────────────────────────


def test_has_features_endpoint_never_5xx(monkeypatch, client):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_bundle_body", _boom)
    resp = client.get("/api/entitlement/has-features?features=fleet,sso")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == []
    assert body["unknown"] == ["fleet", "sso"]
    assert body["has_features"] is False
    assert body["allowed"] is False


def test_has_runtimes_endpoint_never_5xx(monkeypatch, client):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_bundle_body", _boom)
    resp = client.get(
        "/api/entitlement/has-runtimes?runtimes=claude_code,codex"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == []
    assert body["unknown"] == ["claude_code", "codex"]
    assert body["has_runtimes"] is False


# ── Cross-consistency with /min-tier-for-features and /min-tier-for-runtimes


@pytest.mark.parametrize(
    "features_csv",
    [
        "nemo_governance",
        "fleet",
        "fleet,otel_export",
        "nemo_governance,fleet",
    ],
)
def test_has_features_cross_consistent_with_min_tier_for_features(
    client, features_csv
):
    """Same input -> same tier answer on both endpoints. A UI wiring
    ``/has-features`` and ``/min-tier-for-features`` into the same
    paywall tile can't see inconsistent tier state."""
    has_body = _get_json(
        client, f"/api/entitlement/has-features?features={features_csv}"
    )
    req_body = _get_json(
        client, f"/api/entitlement/min-tier-for-features?features={features_csv}"
    )
    assert has_body["required_tier"] == req_body["required_tier"]
    assert has_body["required_tier_label"] == req_body["required_tier_label"]
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"]
    assert has_body["current_tier"] == req_body["current_tier"]
    assert has_body["current_tier_rank"] == req_body["current_tier_rank"]
    assert has_body["features"] == req_body["features"]
    assert has_body["unknown"] == req_body["unknown"]


@pytest.mark.parametrize(
    "runtimes_csv",
    [
        "openclaw",
        "claude_code",
        "openclaw,nemoclaw",
        "claude_code,codex",
        "openclaw,claude_code",
    ],
)
def test_has_runtimes_cross_consistent_with_min_tier_for_runtimes(
    client, runtimes_csv
):
    has_body = _get_json(
        client, f"/api/entitlement/has-runtimes?runtimes={runtimes_csv}"
    )
    req_body = _get_json(
        client, f"/api/entitlement/min-tier-for-runtimes?runtimes={runtimes_csv}"
    )
    assert has_body["required_tier"] == req_body["required_tier"]
    assert has_body["required_tier_label"] == req_body["required_tier_label"]
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"]
    assert has_body["current_tier"] == req_body["current_tier"]
    assert has_body["runtimes"] == req_body["runtimes"]


# ── Scalar-vs-endpoint parity ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "features_csv",
    [
        "nemo_governance",
        "fleet",
        "nemo_governance,fleet",
        "fleet,bogus",
        "bogus_a,bogus_b",
        "",
    ],
)
def test_has_features_endpoint_matches_scalar(client, ent, features_csv):
    """Envelope ``has_features`` value matches the module-level scalar
    byte-for-byte on the ORIGINAL CSV (unknowns collapse both sides)."""
    body = _get_json(
        client, f"/api/entitlement/has-features?features={features_csv}"
    )
    tokens = [
        t.strip().lower() for t in features_csv.split(",") if t.strip()
    ]
    assert body["has_features"] is ent.has_features(tokens)
    assert body["allowed"] is ent.has_features(tokens)


@pytest.mark.parametrize(
    "runtimes_csv",
    [
        "openclaw",
        "claude_code",
        "openclaw,claude_code",
        "openclaw,bogus",
        "bogus_a,bogus_b",
        "",
    ],
)
def test_has_runtimes_endpoint_matches_scalar(client, ent, runtimes_csv):
    body = _get_json(
        client, f"/api/entitlement/has-runtimes?runtimes={runtimes_csv}"
    )
    tokens = [
        t.strip().lower() for t in runtimes_csv.split(",") if t.strip()
    ]
    assert body["has_runtimes"] is ent.has_runtimes(tokens)
    assert body["allowed"] is ent.has_runtimes(tokens)


# ── Grace invariant on both axes ───────────────────────────────────────────────────────────────────────


def test_grace_invariant_all_known_features_bundle_reports_true(ent):
    """Headline grace invariant: while grace is on, the WHOLE
    ``ALL_FEATURES`` set is granted -- wiring the plural gate into a UI
    today is a no-op behavior change."""
    assert ent.has_features(sorted(ent.ALL_FEATURES)) is True


def test_grace_invariant_all_known_runtimes_bundle_reports_true(ent):
    assert ent.has_runtimes(sorted(ent.ALL_RUNTIMES)) is True


def test_enforce_all_paid_features_bundle_locked_on_oss(enforced):
    """Symmetric enforcement assertion: post-enforce, the paid-feature
    bundle collapses to False on OSS."""
    assert enforced.has_features(sorted(enforced.PAID_FEATURES)) is False


def test_enforce_all_paid_runtimes_bundle_locked_on_oss(enforced):
    assert enforced.has_runtimes(sorted(enforced.PAID_RUNTIMES)) is False


def test_enforce_free_features_bundle_still_true(enforced):
    """FREE_FEATURES stay granted post-enforce."""
    assert enforced.has_features(sorted(enforced.FREE_FEATURES)) is True


def test_enforce_free_runtimes_bundle_still_true(enforced):
    assert enforced.has_runtimes(sorted(enforced.FREE_RUNTIMES)) is True
