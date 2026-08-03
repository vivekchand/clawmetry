"""Tests for the perspective-shaped ``missing_features_at`` /
``missing_runtimes_at`` complement scalars and their paired
``/api/entitlement/missing-features-at`` /
``/api/entitlement/missing-runtimes-at`` endpoints.

Perspective-shaped siblings of :func:`missing_features` /
:func:`missing_runtimes` in the same relationship
:func:`has_features_at` has to :func:`has_features`: fills the
``_at`` slot in the row-detail complement family so a pricing matrix
that gates on a BUNDLE ("which of fleet + sso would still be locked at
Starter? at Pro?") can bind the per-item denial list off ONE URL per
(perspective, bundle) cell.

This file pins:

1. Scalar semantics: empty / None / non-iterable / unknown / all axes
   across free / paid / mixed bundles under every real ``_TIER_ORDER``
   perspective.
2. Perspective validation: empty / blank / unknown / non-string
   ``perspective_tier`` -> ``[]`` (fail-open on the diagnostic; matches
   the sibling :func:`missing_features` "no info to surface" posture on
   resolver blowup).
3. Complement invariant: ``missing_features_at(p, b) == []`` iff
   ``has_features_at(p, b) is True`` for every non-empty ``b``. Same for
   the runtimes twin.
4. Grace-independence: the answer is identical under grace vs enforce
   for the same (perspective, bundle) pair (backed by
   :func:`_hypothetical_entitlement`, grace off).
5. Order and dedup: first-seen preserved; canonical-key dedup collapses
   ``["fleet", "fleet"]`` -> one row.
6. Runtime scalar alias posture: no scalar-level canonicalisation --
   ``missing_runtimes_at("pro", ["claude-code"])`` surfaces
   ``"claude-code"`` in ``missing`` verbatim (matches
   :func:`has_runtimes_at` alias posture); the paired endpoint
   canonicalises upstream.
7. Never-raises on resolver / delegate blowup: log-and-return ``[]``.
8. Endpoint envelope shape (fixed 17-key set) across every input branch.
9. Never-5xx via monkeypatched blowup on both endpoints.
10. Scalar-vs-endpoint parity: URL ``missing`` byte-equals scalar output
    on the same (perspective, bundle) input.
11. Cross-consistency with the sibling ``/api/entitlement/has-features-at``
    / ``/has-runtimes-at`` -- ``any_missing`` negates the ``allowed`` /
    ``has_*_at`` bit on the same input.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ───────────────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode. The ``_at``
    scalars are grace-independent by construction so most assertions do
    not depend on this fixture's rollout state; it exists to keep
    parity with the sibling ``test_entitlement_missing_features_runtimes.py``
    setup so cross-file assertions read the same install state."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: pins the grace-independence contract by
    replaying every scalar assertion under grace=False and asserting the
    same answer as the grace ``ent`` fixture on the same input."""
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
    "tier",
    "features",
    "unknown",
    "missing",
    "kind",
    "count",
    "missing_count",
    "any_missing",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "upgrade_required",
}
_RUNTIMES_KEYS = {
    "tier",
    "runtimes",
    "unknown",
    "missing",
    "kind",
    "count",
    "missing_count",
    "any_missing",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier_rank",
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


def _paid_feature_tier(ent):
    """Cheapest tier that grants at least one paid feature (used to pick a
    perspective that flips at-least-one row from missing to granted)."""
    for tier in ent._TIER_ORDER:
        if tier == "oss":
            continue
        for f in ent.PAID_FEATURES:
            if ent.has_feature_at(tier, f):
                return tier
    return None


def _paid_runtime_tier(ent):
    """Cheapest tier that grants at least one paid runtime."""
    for tier in ent._TIER_ORDER:
        if tier == "oss":
            continue
        for rt in ent.PAID_RUNTIMES:
            if ent.has_runtime_at(tier, rt):
                return tier
    return None


# ── missing_features_at scalar ──────────────────────────────────────────────────────────


def test_missing_features_at_all_free_is_empty_every_tier(ent):
    """A bundle of ONLY free features is granted at every real tier
    (free floor lives in :func:`_hypothetical_entitlement`)."""
    free = sorted(ent.FREE_FEATURES)
    for tier in ent._TIER_ORDER:
        assert ent.missing_features_at(tier, free) == []


def test_missing_features_at_oss_denies_every_paid_feature(ent):
    """OSS-free perspective grants no paid features -- every paid id in
    the bundle lands in ``missing``. Grace-independent: same answer as
    the enforce fixture below."""
    paid = sorted(ent.PAID_FEATURES)
    missing = ent.missing_features_at("oss", paid)
    assert set(missing) == set(paid)
    assert len(missing) == len(paid)


def test_missing_features_at_enterprise_grants_every_known_feature(ent):
    """Enterprise perspective grants every known feature -- ``missing``
    is empty for the full paid bundle."""
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise tier not in _TIER_ORDER on this build")
    paid = sorted(ent.PAID_FEATURES)
    assert ent.missing_features_at("enterprise", paid) == []


def test_missing_features_at_grace_independence(ent, enforced):
    """The scalar is grace-independent by construction: the same
    (perspective, bundle) pair returns the same list under grace on and
    grace off."""
    paid = sorted(ent.PAID_FEATURES)
    for tier in ent._TIER_ORDER:
        grace_ans = ent.missing_features_at(tier, paid)
        enforce_ans = enforced.missing_features_at(tier, paid)
        assert grace_ans == enforce_ans, (tier, paid)


def test_missing_features_at_unknown_perspective_returns_empty(ent):
    """Unknown perspective -> ``[]`` (fail-open on the diagnostic --
    caller can distinguish "typo perspective" from "valid perspective
    that grants everything" via ``perspective_tier_rank == -1`` on the
    paired endpoint)."""
    assert ent.missing_features_at("Pro", ["fleet"]) == []  # dropped case
    assert ent.missing_features_at("", ["fleet"]) == []
    assert ent.missing_features_at(None, ["fleet"]) == []  # type: ignore[arg-type]
    assert ent.missing_features_at("bogus_tier", ["fleet"]) == []
    assert ent.missing_features_at(123, ["fleet"]) == []  # type: ignore[arg-type]


def test_missing_features_at_unknown_feature_surfaces_at_row_level(ent):
    """Unknown token at any valid perspective: only the typo lands in
    ``missing`` (mirrors :func:`missing_features` typo posture)."""
    tier = _paid_feature_tier(ent)
    if tier is None:
        pytest.skip("no paid-feature tier on this build")
    # pick a paid feature granted at this tier
    granted = next(f for f in ent.PAID_FEATURES if ent.has_feature_at(tier, f))
    missing = ent.missing_features_at(tier, [granted, "bogus_id"])
    assert missing == ["bogus_id"]


def test_missing_features_at_all_unknown_surfaces_every_id(ent):
    """All-unknown bundle: every id in ``missing`` (canonicalised)."""
    tier = _paid_feature_tier(ent) or "oss"
    missing = ent.missing_features_at(tier, ["bogus_a", "bogus_b"])
    assert missing == ["bogus_a", "bogus_b"]


def test_missing_features_at_empty_iterable_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_features_at(tier, []) == []
        assert ent.missing_features_at(tier, ()) == []
        assert ent.missing_features_at(tier, iter(())) == []


def test_missing_features_at_none_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_features_at(tier, None) == []


def test_missing_features_at_non_iterable_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_features_at(tier, 123) == []
        assert ent.missing_features_at(tier, object()) == []


def test_missing_features_at_case_insensitive_canonicalises(ent):
    """Whitespace / casing on a known id normalises via the delegate;
    at a tier that grants it, it comes back granted (empty missing)."""
    tier = _paid_feature_tier(ent)
    if tier is None:
        pytest.skip("no paid-feature tier on this build")
    granted = next(f for f in ent.PAID_FEATURES if ent.has_feature_at(tier, f))
    assert ent.missing_features_at(
        tier, [granted.upper(), f"  {granted}  "]
    ) == []


def test_missing_features_at_dedup_preserves_first_seen(ent):
    """A repeated denied id collapses to ONE row in first-seen order."""
    paid = sorted(ent.PAID_FEATURES)
    a, b = paid[0], paid[1]
    missing = ent.missing_features_at("oss", [a, b, a, b, a])
    assert missing == [a, b]


def test_missing_features_at_non_string_item_becomes_blank(ent):
    """Non-string entries canonicalise to ``""`` and are INCLUDED once
    (dedup on canonical key)."""
    missing = ent.missing_features_at("oss", [123, None, object()])
    assert missing == [""]


def test_missing_features_at_never_raises_on_delegate_blowup(monkeypatch, ent):
    """A delegate blowup collapses to ``[]`` (diagnostic fail-open) --
    a matrix cell keeps rendering instead of throwing."""
    def _boom(*a, **kw):
        raise RuntimeError("delegate blew up")

    monkeypatch.setattr(ent, "has_feature_at", _boom)
    for arg in [["fleet"], ["fleet", "sso"], [], None, 123]:
        assert ent.missing_features_at("pro", arg) == []


# ── missing_runtimes_at scalar ─────────────────────────────────────────────────────────


def test_missing_runtimes_at_all_free_is_empty_every_tier(ent):
    free = sorted(ent.FREE_RUNTIMES)
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at(tier, free) == []


def test_missing_runtimes_at_oss_denies_every_paid_runtime(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    missing = ent.missing_runtimes_at("oss", paid)
    assert set(missing) == set(paid)
    assert len(missing) == len(paid)


def test_missing_runtimes_at_grace_independence(ent, enforced):
    paid = sorted(ent.PAID_RUNTIMES)
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at(tier, paid) == enforced.missing_runtimes_at(
            tier, paid
        )


def test_missing_runtimes_at_unknown_perspective_returns_empty(ent):
    assert ent.missing_runtimes_at("Pro", ["claude_code"]) == []
    assert ent.missing_runtimes_at("", ["claude_code"]) == []
    assert ent.missing_runtimes_at(None, ["claude_code"]) == []  # type: ignore[arg-type]
    assert ent.missing_runtimes_at("bogus_tier", ["claude_code"]) == []
    assert ent.missing_runtimes_at(123, ["claude_code"]) == []  # type: ignore[arg-type]


def test_missing_runtimes_at_unknown_surfaces_at_row_level(ent):
    tier = _paid_runtime_tier(ent)
    if tier is None:
        pytest.skip("no paid-runtime tier on this build")
    granted = next(rt for rt in ent.PAID_RUNTIMES if ent.has_runtime_at(tier, rt))
    assert ent.missing_runtimes_at(tier, [granted, "bogus_runtime"]) == [
        "bogus_runtime"
    ]


def test_missing_runtimes_at_empty_iterable_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at(tier, []) == []


def test_missing_runtimes_at_none_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at(tier, None) == []


def test_missing_runtimes_at_non_iterable_is_empty(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at(tier, 123) == []
        assert ent.missing_runtimes_at(tier, object()) == []


def test_missing_runtimes_at_scalar_does_not_alias_canonicalise(ent):
    """Scalar mirrors :func:`has_runtimes_at` alias posture: the
    delegate :func:`has_runtime_at` does not resolve aliases, so at the
    scalar layer an alias input surfaces in ``missing`` in its
    ``.strip().lower()`` form. Alias tolerance is the endpoint's job."""
    tier = _paid_runtime_tier(ent) or "pro"
    assert ent.missing_runtimes_at(tier, ["claude-code"]) == ["claude-code"]


def test_missing_runtimes_at_scalar_no_dedup_across_alias_forms(ent):
    """Consequence of no scalar-level canonicalisation."""
    tier = _paid_runtime_tier(ent)
    if tier is None:
        pytest.skip("no paid-runtime tier on this build")
    if not ent.has_runtime_at(tier, "claude_code"):
        pytest.skip("perspective does not grant claude_code")
    missing = ent.missing_runtimes_at(tier, ["claude-code", "claude_code"])
    assert missing == ["claude-code"]  # canonical form granted; alias missing


def test_missing_runtimes_at_case_insensitive(ent):
    tier = _paid_runtime_tier(ent)
    if tier is None:
        pytest.skip("no paid-runtime tier on this build")
    granted = next(rt for rt in ent.PAID_RUNTIMES if ent.has_runtime_at(tier, rt))
    assert ent.missing_runtimes_at(tier, [granted.upper(), f"  {granted}  "]) == []


def test_missing_runtimes_at_dedup_preserves_first_seen(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    a, b = paid[0], paid[1]
    missing = ent.missing_runtimes_at("oss", [a, b, a, b])
    assert missing == [a, b]


def test_missing_runtimes_at_never_raises_on_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("delegate blew up")

    monkeypatch.setattr(ent, "has_runtime_at", _boom)
    for arg in [["openclaw"], ["claude_code", "cursor"], [], None, 123]:
        assert ent.missing_runtimes_at("pro", arg) == []


# ── Complement invariant: missing_*_at == [] iff has_*_at is True ─────────────────────


@pytest.mark.parametrize(
    "bundle",
    [
        ["fleet"],
        ["fleet", "sso"],
        ["bogus_id"],
        ["fleet", "bogus_id"],
    ],
)
def test_missing_features_at_complement_invariant(ent, bundle):
    """``missing_features_at(p, b) == []`` iff ``has_features_at(p, b) is
    True`` for every non-empty bundle at every real perspective."""
    for tier in ent._TIER_ORDER:
        # skip axes / tokens the ent build doesn't know about defensively
        missing = ent.missing_features_at(tier, bundle)
        has = ent.has_features_at(tier, bundle)
        assert (missing == []) is has, (tier, bundle)


@pytest.mark.parametrize(
    "bundle",
    [
        ["openclaw"],
        ["claude_code"],
        ["openclaw", "claude_code"],
        ["bogus_runtime"],
        ["openclaw", "bogus_runtime"],
    ],
)
def test_missing_runtimes_at_complement_invariant(ent, bundle):
    for tier in ent._TIER_ORDER:
        missing = ent.missing_runtimes_at(tier, bundle)
        has = ent.has_runtimes_at(tier, bundle)
        assert (missing == []) is has, (tier, bundle)


# ── /api/entitlement/missing-features-at endpoint ────────────────────────────────────


def test_endpoint_missing_features_at_shape_default(client):
    """Missing-arg CSV -> 200 with 17-key envelope and empty missing."""
    body = _get_json(client, "/api/entitlement/missing-features-at")
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tier"] == ""
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["missing"] == []
    assert body["kind"] == "features"
    assert body["count"] == 0
    assert body["missing_count"] == 0
    assert body["any_missing"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["perspective_tier_rank"] == -1
    assert body["grace"] is True
    assert body["upgrade_required"] is False


def test_endpoint_missing_features_at_unknown_perspective_missing_empty(client):
    """Unknown perspective still 200; ``missing=[]`` (fail-open on the
    diagnostic, same as scalar); ``perspective_tier_rank == -1`` so a UI
    can distinguish typo perspective from valid-but-fully-granted."""
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=bogus_tier&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tier"] == "bogus_tier"
    assert body["perspective_tier_rank"] == -1
    assert body["features"] == ["fleet", "sso"]
    assert body["missing"] == []


def test_endpoint_missing_features_at_oss_denies_paid(client):
    """OSS perspective denies every paid feature -- grace-independent."""
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,sso",
    )
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["tier"] == "oss"
    assert set(body["missing"]) == {"fleet", "sso"}
    assert body["missing_count"] == 2
    assert body["any_missing"] is True


def test_endpoint_missing_features_at_enterprise_grants_paid(client, ent):
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise tier not in _TIER_ORDER on this build")
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=enterprise&features=fleet,sso",
    )
    assert body["missing"] == []
    assert body["any_missing"] is False


def test_endpoint_missing_features_at_unknown_surfaces_in_missing_and_unknown(client):
    """Unknown token surfaces in BOTH ``unknown`` (raw) and ``missing``
    (canonicalised)."""
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,bogus_id",
    )
    assert body["features"] == ["fleet"]
    assert body["unknown"] == ["bogus_id"]
    assert set(body["missing"]) == {"fleet", "bogus_id"}
    assert body["any_missing"] is True


def test_endpoint_missing_features_at_dedup(client):
    """Repeated tokens collapse via _parse_csv_arg dedup."""
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,fleet,sso,fleet",
    )
    assert body["features"] == ["fleet", "sso"]
    assert body["count"] == 2


def test_endpoint_missing_features_at_scalar_vs_endpoint_parity(client, ent):
    """URL ``missing`` byte-equals module scalar on the same input."""
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,bogus_id",
    )
    assert body["missing"] == ent.missing_features_at(
        "oss", ["fleet", "bogus_id"]
    )


def test_endpoint_missing_features_at_any_missing_negates_has_features_at(client):
    """``any_missing`` here == not ``has_features_at`` on the sibling
    URL over the same (perspective, bundle)."""
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        for csv in ("fleet,sso", "fleet"):
            miss_body = _get_json(
                client,
                f"/api/entitlement/missing-features-at?tier={tier}&features={csv}",
            )
            has_body = _get_json(
                client,
                f"/api/entitlement/has-features-at?tier={tier}&features={csv}",
            )
            # Skip perspectives absent from _TIER_ORDER on this build.
            if has_body["perspective_tier_rank"] == -1:
                continue
            assert miss_body["any_missing"] is (not has_body["has_features_at"]), (
                tier,
                csv,
            )


def test_endpoint_missing_features_at_upgrade_required_compares_to_perspective(
    client,
):
    """``upgrade_required`` compares required-tier rank to PERSPECTIVE
    rank (not live current rank) so a matrix row reads "no upgrade
    needed at this tier" (False when perspective >= required) vs
    "upgrade needed beyond this tier" (True when perspective <
    required). Diverges deliberately from the live sibling's
    live-current comparison -- the whole point of the ``_at`` slot."""
    # OSS perspective + Enterprise-tier bundle -> upgrade_required True
    oss_body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,sso",
    )
    assert oss_body["required_tier"] is not None
    assert oss_body["upgrade_required"] is True

    # Enterprise perspective + same bundle -> upgrade_required False
    ent_body = _get_json(
        client,
        "/api/entitlement/missing-features-at?tier=enterprise&features=fleet,sso",
    )
    if ent_body["perspective_tier_rank"] != -1:
        assert ent_body["upgrade_required"] is False


def test_endpoint_missing_features_at_never_5xx_on_resolver_blowup(
    monkeypatch, client
):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["missing"] == []
    assert body["any_missing"] is False
    assert body["grace"] is True
    assert body["current_tier"] == "oss"


def test_endpoint_missing_features_at_never_5xx_on_scalar_blowup(
    monkeypatch, client
):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "missing_features_at", _boom)
    resp = client.get(
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["missing"] == []


# ── /api/entitlement/missing-runtimes-at endpoint ────────────────────────────────────


def test_endpoint_missing_runtimes_at_shape_default(client):
    body = _get_json(client, "/api/entitlement/missing-runtimes-at")
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == []
    assert body["missing"] == []
    assert body["any_missing"] is False


def test_endpoint_missing_runtimes_at_oss_denies_paid(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=claude_code,cursor",
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert set(body["missing"]) == {"claude_code", "cursor"}
    assert body["missing_count"] == 2


def test_endpoint_missing_runtimes_at_alias_canonicalises(client):
    """Alias tokens canonicalise upstream before hitting the strict
    scalar so ``?runtimes=claude-code`` renders as ``claude_code`` in
    ``runtimes`` and (at a perspective that denies it) ``missing``."""
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=claude-code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["missing"] == ["claude_code"]


def test_endpoint_missing_runtimes_at_alias_and_canonical_dedup(client):
    """Alias + canonical pair collapses to ONE row in ``missing``."""
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=claude-code,claude_code",
    )
    assert body["missing"] == ["claude_code"]
    assert body["missing_count"] == 1


def test_endpoint_missing_runtimes_at_unknown_surfaces_in_missing(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw,bogus_runtime",
    )
    assert body["runtimes"] == ["openclaw"]
    assert body["unknown"] == ["bogus_runtime"]
    assert body["missing"] == ["bogus_runtime"]


def test_endpoint_missing_runtimes_at_any_missing_negates_has_runtimes_at(client):
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        for csv in ("openclaw,claude_code", "claude_code"):
            miss_body = _get_json(
                client,
                f"/api/entitlement/missing-runtimes-at?tier={tier}&runtimes={csv}",
            )
            has_body = _get_json(
                client,
                f"/api/entitlement/has-runtimes-at?tier={tier}&runtimes={csv}",
            )
            if has_body["perspective_tier_rank"] == -1:
                continue
            assert miss_body["any_missing"] is (not has_body["has_runtimes_at"]), (
                tier,
                csv,
            )


def test_endpoint_missing_runtimes_at_never_5xx_on_resolver_blowup(
    monkeypatch, client
):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["missing"] == []


def test_endpoint_missing_runtimes_at_never_5xx_on_scalar_blowup(
    monkeypatch, client
):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "missing_runtimes_at", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["missing"] == []


# ── Envelope stability across many input branches ───────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/missing-features-at",
        "/api/entitlement/missing-features-at?tier=",
        "/api/entitlement/missing-features-at?tier=oss",
        "/api/entitlement/missing-features-at?tier=oss&features=",
        "/api/entitlement/missing-features-at?tier=oss&features=fleet",
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,sso",
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,bogus_id",
        "/api/entitlement/missing-features-at?tier=oss&features=bogus_a,bogus_b",
        "/api/entitlement/missing-features-at?tier=oss&features=fleet,,sso,fleet",
        "/api/entitlement/missing-features-at?tier=oss&features=%20fleet%20,SSO",
        "/api/entitlement/missing-features-at?tier=bogus&features=fleet",
        "/api/entitlement/missing-features-at?tier=%20PRO%20&features=fleet",
    ],
)
def test_endpoint_missing_features_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert isinstance(body["tier"], str)
    assert isinstance(body["features"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["missing"], list)
    assert isinstance(body["count"], int)
    assert isinstance(body["missing_count"], int)
    assert body["missing_count"] == len(body["missing"])
    assert body["count"] == len(body["features"])
    assert isinstance(body["any_missing"], bool)
    assert body["any_missing"] is (bool(body["missing"]) or bool(body["unknown"]))
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["upgrade_required"], bool)


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/missing-runtimes-at",
        "/api/entitlement/missing-runtimes-at?tier=",
        "/api/entitlement/missing-runtimes-at?tier=oss",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw,claude_code",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=claude-code",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=claude-code,claude_code",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=openclaw,bogus_runtime",
        "/api/entitlement/missing-runtimes-at?tier=oss&runtimes=%20openclaw%20,CLAUDE_CODE",
        "/api/entitlement/missing-runtimes-at?tier=bogus&runtimes=openclaw",
    ],
)
def test_endpoint_missing_runtimes_at_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"
    assert isinstance(body["tier"], str)
    assert isinstance(body["runtimes"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["missing"], list)
    assert body["missing_count"] == len(body["missing"])
    assert body["count"] == len(body["runtimes"])
    assert isinstance(body["any_missing"], bool)
    assert body["any_missing"] is (bool(body["missing"]) or bool(body["unknown"]))
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["upgrade_required"], bool)
