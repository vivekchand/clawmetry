"""Tests for the row-detail ``missing_features`` / ``missing_runtimes``
complement scalars and their paired ``/api/entitlement/missing-features`` /
``/api/entitlement/missing-runtimes`` endpoints.

Complements of the plural boolean-fold ``has_features`` / ``has_runtimes``
scalars at row level: where the boolean fold answers "does the WHOLE
bundle pass?", these preserve the per-item denial list so a paywall
diagnostics tile ("you're missing fleet, sso -- upgrade to unlock") can
bind the exact list off ONE URL without walking the ``/has-batch``
matrix and filtering ``has=False`` client-side.

This file pins:

1. Scalar semantics: empty / None / non-iterable / unknown / grace vs
   enforce over free / paid / mixed bundles.
2. Complement invariant: ``missing_features(bundle) == []`` iff
   ``has_features(bundle) is True``. Same for the runtimes twin.
3. Order and dedup: first-seen preserved; canonical-key dedup collapses
   ``["fleet", "fleet"]`` -> one row and, for runtimes, alias-and-canonical
   pair (``["claude-code", "claude_code"]``) -> one row too.
4. Runtime-alias canonicalisation via :func:`canonical_runtime` inside the
   missing list (a granted alias registers as granted).
5. Never-raises on resolver blowup: both scalars log-and-return ``[]``.
6. Endpoint envelope shape (fixed 15-key set) across every input branch
   so a frontend can bind fields off the URL without a branch on the
   resolver state.
7. Never-5xx via monkeypatched blowup on both endpoints.
8. Cross-consistency with the sibling ``/api/entitlement/has-features``
   / ``/has-runtimes`` and ``/api/entitlement/min-tier-for-features`` /
   ``/min-tier-for-runtimes`` endpoints -- same ``required_tier`` /
   ``current_tier`` for the same bundle, so a UI wiring both URLs into
   the same paywall tile can't see inconsistent tier state.
9. The grace-mode invariant: ``missing`` is ``[]`` for every fully-known
   bundle while ``grace`` is on, so wiring these into a diagnostics tile
   today changes NO current behavior.
10. Scalar-vs-endpoint parity: the URL ``missing`` list equals the
    module-level scalar output byte-for-byte on the same input.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ───────────────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- matches the
    sibling ``test_entitlement_has_features_has_runtimes.py`` fixture so
    the complement assertions here reproduce the same install state the
    boolean fold ones are pinned against."""
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
    post-enforce denial in the complement."""
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


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── Envelope shape ────────────────────────────────────────────────────────────────────────

_FEATURES_KEYS = {
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
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "upgrade_required",
}
_RUNTIMES_KEYS = {
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


# ── missing_features scalar ──────────────────────────────────────────────────────────────


def test_missing_features_all_free_is_empty(ent):
    """A bundle of ONLY free features is fully granted regardless of the
    rollout state, so nothing is missing."""
    free = sorted(ent.FREE_FEATURES)
    assert ent.missing_features(free) == []


def test_missing_features_all_paid_is_empty_in_grace(ent):
    """Grace invariant on the complement: every paid feature reports
    granted per item, so ``missing`` is empty."""
    paid = sorted(ent.PAID_FEATURES)
    assert ent.missing_features(paid) == []


def test_missing_features_all_paid_lists_all_after_enforcement(enforced):
    """Post-enforcement, EVERY paid feature on OSS lands in the missing
    list -- the complement of the ``has_features`` False-fold."""
    paid = sorted(enforced.PAID_FEATURES)
    missing = enforced.missing_features(paid)
    # Every paid id shows up (in canonical form) exactly once.
    assert set(missing) == set(paid)
    assert len(missing) == len(paid)


def test_missing_features_mixed_free_and_paid_after_enforcement(enforced):
    """Post-enforcement, only the paid item lands in ``missing`` -- the
    free item is still granted."""
    free = next(iter(enforced.FREE_FEATURES))
    paid = next(iter(enforced.PAID_FEATURES))
    missing = enforced.missing_features([free, paid])
    assert missing == [paid]


def test_missing_features_unknown_in_grace_surfaces_only_the_typo(ent):
    """A grace-mode call with one known + one typo returns ONLY the typo
    in ``missing``. The known id is granted (grace); the typo fails the
    strict callsite check -- exactly the split the sibling
    ``has_features`` collapses to a single ``False`` fold."""
    missing = ent.missing_features(["fleet", "bogus_id"])
    assert missing == ["bogus_id"]


def test_missing_features_all_unknown_surfaces_every_id(ent):
    """All-unknown bundle: every id in ``missing`` (canonicalised)."""
    missing = ent.missing_features(["bogus_a", "bogus_b"])
    assert missing == ["bogus_a", "bogus_b"]


def test_missing_features_empty_iterable_is_empty(ent):
    """Empty iterable -> empty missing (nothing to check). Diverges from
    ``has_features`` (which strict-``False``s an empty bundle) because
    the complement of "no bundle" is naturally empty."""
    assert ent.missing_features([]) == []
    assert ent.missing_features(()) == []
    assert ent.missing_features(iter(())) == []


def test_missing_features_none_is_empty(ent):
    """``None`` -> empty without raising."""
    assert ent.missing_features(None) == []


def test_missing_features_non_iterable_is_empty(ent):
    """Non-iterable input -> empty without raising."""
    assert ent.missing_features(123) == []
    assert ent.missing_features(object()) == []


def test_missing_features_case_insensitive_canonicalises(ent):
    """Casing / whitespace normalises via the per-item delegate, so a
    typo like ``"  Fleet  "`` on a known id in grace comes back granted
    (empty missing)."""
    known = next(iter(sorted(ent.PAID_FEATURES)))
    assert ent.missing_features([known.upper(), f"  {known}  "]) == []


def test_missing_features_dedup_preserves_first_seen(enforced):
    """A repeated denied id collapses to ONE row in first-seen order."""
    paid = sorted(enforced.PAID_FEATURES)
    a, b = paid[0], paid[1]
    missing = enforced.missing_features([a, b, a, b, a])
    assert missing == [a, b]


def test_missing_features_non_string_item_becomes_blank(ent):
    """A non-string entry canonicalises to ``""`` and is INCLUDED in
    missing (there is nothing to grant). Dedups against other non-string
    entries."""
    missing = ent.missing_features([123, None, object()])
    assert missing == [""]


def test_missing_features_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup in the resolver collapses to ``[]`` -- the diagnostic
    fail-open posture (see scalar docstring). A resolver we cannot query
    tells us nothing about what's granted, so we cannot say what's
    missing; returning ``[]`` prevents a diagnostics tile from silently
    rendering a spurious denial banner."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in [["fleet"], ["fleet", "nemo_governance"], [], None, 123]:
        assert ent.missing_features(arg) == []


# ── missing_runtimes scalar ──────────────────────────────────────────────────────────────


def test_missing_runtimes_all_free_is_empty(ent):
    """Bundle of ONLY free runtimes -- nothing missing."""
    free = sorted(ent.FREE_RUNTIMES)
    assert ent.missing_runtimes(free) == []


def test_missing_runtimes_all_paid_is_empty_in_grace(ent):
    """Grace invariant on runtimes axis."""
    paid = sorted(ent.PAID_RUNTIMES)
    assert ent.missing_runtimes(paid) == []


def test_missing_runtimes_all_paid_lists_all_after_enforcement(enforced):
    """Post-enforcement: every paid runtime shows up as missing exactly
    once."""
    paid = sorted(enforced.PAID_RUNTIMES)
    missing = enforced.missing_runtimes(paid)
    assert set(missing) == set(paid)
    assert len(missing) == len(paid)


def test_missing_runtimes_mixed_free_and_paid_after_enforcement(enforced):
    """Post-enforcement, only the paid runtime lands in ``missing``."""
    free = next(iter(enforced.FREE_RUNTIMES))
    paid = next(iter(enforced.PAID_RUNTIMES))
    assert enforced.missing_runtimes([free, paid]) == [paid]


def test_missing_runtimes_unknown_surfaces_at_row_level(ent):
    """Unknown runtime in grace: only the unknown lands in ``missing``
    (the known id is granted in grace)."""
    assert ent.missing_runtimes(["openclaw", "bogus_runtime"]) == ["bogus_runtime"]


def test_missing_runtimes_empty_iterable_is_empty(ent):
    assert ent.missing_runtimes([]) == []


def test_missing_runtimes_none_is_empty(ent):
    assert ent.missing_runtimes(None) == []


def test_missing_runtimes_non_iterable_is_empty(ent):
    assert ent.missing_runtimes(123) == []
    assert ent.missing_runtimes(object()) == []


def test_missing_runtimes_scalar_does_not_alias_canonicalise(ent):
    """The scalar mirrors the sibling :func:`has_runtimes` alias posture
    exactly: the delegate :func:`has_runtime` does not resolve aliases
    (``has_runtime("claude-code")`` is ``False``), so at the scalar
    layer an alias input surfaces in ``missing`` in its
    ``.strip().lower()`` form. Alias tolerance belongs to the paired
    ``/api/entitlement/missing-runtimes`` endpoint, which canonicalises
    upstream before delegating (see endpoint tests below)."""
    # grace mode: "claude-code" is unknown at the scalar delegate, so
    # it's marked missing verbatim (not canonicalised).
    assert ent.missing_runtimes(["claude-code"]) == ["claude-code"]


def test_missing_runtimes_scalar_no_dedup_across_alias_forms(ent):
    """Consequence of no scalar-level canonicalisation: an alias +
    canonical pair does NOT collapse at the scalar (each has a distinct
    ``.strip().lower()`` key). The endpoint's own upstream-canonicalise
    step is what collapses them for a URL caller."""
    missing = ent.missing_runtimes(["claude-code", "claude_code"])
    # first entry marked missing (unknown at scalar); second granted in
    # grace (known canonical form).
    assert missing == ["claude-code"]


def test_missing_runtimes_case_insensitive(ent):
    """Casing / whitespace on a known runtime normalises via the delegate."""
    known = next(iter(sorted(ent.PAID_RUNTIMES)))
    assert ent.missing_runtimes([known.upper(), f"  {known}  "]) == []


def test_missing_runtimes_dedup_preserves_first_seen(enforced):
    paid = sorted(enforced.PAID_RUNTIMES)
    a, b = paid[0], paid[1]
    missing = enforced.missing_runtimes([a, b, a, b])
    assert missing == [a, b]


def test_missing_runtimes_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Resolver blowup -> empty missing (diagnostic fail-open, see
    :func:`missing_features` twin)."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in [["openclaw"], ["claude_code", "cursor"], [], None, 123]:
        assert ent.missing_runtimes(arg) == []


# ── Complement invariant: missing == [] iff has_* is True ────────────────────────────────


@pytest.mark.parametrize(
    "bundle",
    [
        ["fleet"],
        ["nemo_governance"],
        ["fleet", "nemo_governance"],
        ["bogus_id"],
        ["fleet", "bogus_id"],
        [],
        None,
    ],
)
def test_missing_features_complement_invariant_grace(ent, bundle):
    """``missing_features(b) == []`` iff ``has_features(b) is True`` for
    every non-empty bundle. Empty and ``None`` diverge deliberately (see
    module docstring: complement of no-bundle is naturally empty; boolean
    seat strict-``False``s the same input for callsite typo posture)."""
    missing = ent.missing_features(bundle)
    if bundle in (None, [], (), []):
        # empty/None: missing==[], has_features==False -- documented split
        assert missing == []
    else:
        has = ent.has_features(bundle)
        assert (missing == []) is has


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
def test_missing_runtimes_complement_invariant_grace(ent, bundle):
    """``missing_runtimes(b) == []`` iff ``has_runtimes(b) is True`` for
    every non-empty CANONICAL bundle. Alias inputs at the scalar layer
    are not part of this invariant -- both scalars fail-closed on aliases
    (the delegate does not resolve them); the endpoint's own upstream
    canonicalise is what re-establishes the invariant at URL level (see
    the endpoint parity tests)."""
    missing = ent.missing_runtimes(bundle)
    has = ent.has_runtimes(bundle)
    assert (missing == []) is has


@pytest.mark.parametrize(
    "bundle",
    [
        ["fleet"],
        ["nemo_governance"],
        ["fleet", "nemo_governance"],
    ],
)
def test_missing_features_complement_invariant_enforce(enforced, bundle):
    """Same complement invariant post-enforcement -- when the boolean
    fold flips to ``False`` at least one row shows up in missing."""
    missing = enforced.missing_features(bundle)
    has = enforced.has_features(bundle)
    assert (missing == []) is has


@pytest.mark.parametrize(
    "bundle",
    [
        ["openclaw"],
        ["claude_code"],
        ["openclaw", "claude_code"],
    ],
)
def test_missing_runtimes_complement_invariant_enforce(enforced, bundle):
    missing = enforced.missing_runtimes(bundle)
    has = enforced.has_runtimes(bundle)
    assert (missing == []) is has


# ── /api/entitlement/missing-features endpoint ───────────────────────────────────────────


def test_endpoint_missing_features_shape_default(client):
    """Missing-arg CSV -> 200 with 15-key envelope and empty missing."""
    body = _get_json(client, "/api/entitlement/missing-features")
    assert set(body.keys()) == _FEATURES_KEYS
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
    assert body["grace"] is True
    assert body["upgrade_required"] is False


def test_endpoint_missing_features_shape_all_known_grace(client):
    """Grace + all-known bundle: envelope stable, missing empty."""
    body = _get_json(client, "/api/entitlement/missing-features?features=fleet,sso")
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["features"] == ["fleet", "sso"]
    assert body["count"] == 2
    assert body["missing"] == []
    assert body["missing_count"] == 0
    assert body["any_missing"] is False
    assert body["grace"] is True


def test_endpoint_missing_features_unknown_surfaces_in_missing_and_unknown(client):
    """Unknown token in grace: surfaces in BOTH ``unknown`` (raw) and
    ``missing`` (canonicalised) so a diagnostics tile can distinguish
    "typo" from "denied by tier" without a follow-up call."""
    body = _get_json(client, "/api/entitlement/missing-features?features=fleet,bogus_id")
    assert body["features"] == ["fleet"]
    assert body["unknown"] == ["bogus_id"]
    assert body["missing"] == ["bogus_id"]
    assert body["missing_count"] == 1
    assert body["any_missing"] is True


def test_endpoint_missing_features_all_paid_enforced(enforced_client):
    """Post-enforcement: every paid id shows up in ``missing``."""
    body = _get_json(
        enforced_client, "/api/entitlement/missing-features?features=fleet,sso"
    )
    assert set(body["missing"]) == {"fleet", "sso"}
    assert body["missing_count"] == 2
    assert body["any_missing"] is True


def test_endpoint_missing_features_dedup(client):
    """Repeated tokens collapse via _parse_csv_arg dedup (upstream of
    the scalar)."""
    body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,fleet,sso,fleet"
    )
    assert body["features"] == ["fleet", "sso"]
    assert body["count"] == 2


def test_endpoint_missing_features_scalar_vs_endpoint_parity(client, ent):
    """URL ``missing`` byte-equals module scalar on the same input."""
    body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,bogus_id"
    )
    # csv parser lowercases + dedups upstream of the scalar
    assert body["missing"] == ent.missing_features(["fleet", "bogus_id"])


def test_endpoint_missing_features_required_tier_parity_with_min_tier_endpoint(client):
    """``required_tier`` byte-equals the sibling
    ``/api/entitlement/min-tier-for-features`` answer over the same
    known subset -- a UI wiring both URLs into one paywall tile cannot
    see inconsistent tier state. (``/min-tier-for-features`` names its
    own payload key ``required_tier`` too; both endpoints share the
    resolver-envelope shape from :func:`_resolver_envelope`.)"""
    missing_body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,sso"
    )
    min_tier_body = _get_json(
        client, "/api/entitlement/min-tier-for-features?features=fleet,sso"
    )
    assert missing_body["required_tier"] == min_tier_body["required_tier"]


def test_endpoint_missing_features_current_tier_parity_with_has_features(client):
    """``current_tier`` / ``grace`` / ``enforced`` byte-equal the sibling
    ``/has-features`` envelope so both URLs render the same resolver
    context."""
    missing_body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,sso"
    )
    has_body = _get_json(
        client, "/api/entitlement/has-features?features=fleet,sso"
    )
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert missing_body[k] == has_body[k]


def test_endpoint_missing_features_any_missing_is_negation_of_has_features(client):
    """Grace + fully-known: ``any_missing`` False here mirrors
    ``has_features`` True on the sibling."""
    missing_body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,sso"
    )
    has_body = _get_json(
        client, "/api/entitlement/has-features?features=fleet,sso"
    )
    assert missing_body["any_missing"] is (not has_body["has_features"])


def test_endpoint_missing_features_any_missing_flips_on_unknown(client):
    """Grace + one unknown: ``any_missing`` True, mirroring
    ``has_features`` collapsing to False on the sibling."""
    missing_body = _get_json(
        client, "/api/entitlement/missing-features?features=fleet,bogus_id"
    )
    has_body = _get_json(
        client, "/api/entitlement/has-features?features=fleet,bogus_id"
    )
    assert missing_body["any_missing"] is True
    assert has_body["has_features"] is False


def test_endpoint_missing_features_never_5xx_on_resolver_blowup(monkeypatch, client):
    """Endpoint stays 200 with fallback envelope on any resolver blowup."""
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/missing-features?features=fleet,sso")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["missing"] == []
    assert body["any_missing"] is False
    assert body["grace"] is True
    assert body["current_tier"] == "oss"


def test_endpoint_missing_features_never_5xx_on_scalar_blowup(monkeypatch, client):
    """Endpoint stays 200 with fallback envelope when the underlying
    scalar itself throws before the resolver wrap catches it."""
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "missing_features", _boom)
    resp = client.get("/api/entitlement/missing-features?features=fleet,sso")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["missing"] == []


# ── /api/entitlement/missing-runtimes endpoint ───────────────────────────────────────────


def test_endpoint_missing_runtimes_shape_default(client):
    body = _get_json(client, "/api/entitlement/missing-runtimes")
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["runtimes"] == []
    assert body["missing"] == []
    assert body["any_missing"] is False


def test_endpoint_missing_runtimes_all_known_grace(client):
    body = _get_json(
        client, "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code"
    )
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert set(body["runtimes"]) == {"openclaw", "claude_code"}
    assert body["missing"] == []
    assert body["any_missing"] is False


def test_endpoint_missing_runtimes_alias_canonicalises(client):
    """Alias tokens canonicalise before the known/unknown split so
    ``?runtimes=claude-code`` renders as ``claude_code`` in ``runtimes``
    and (post-enforce) in ``missing`` too."""
    body = _get_json(
        client, "/api/entitlement/missing-runtimes?runtimes=claude-code"
    )
    assert body["runtimes"] == ["claude_code"]
    # grace: still no missing (granted)
    assert body["missing"] == []


def test_endpoint_missing_runtimes_alias_and_canonical_dedup(enforced_client):
    """Alias + canonical pair post-enforce collapses to ONE row in
    ``missing`` -- dedup on canonical key."""
    body = _get_json(
        enforced_client,
        "/api/entitlement/missing-runtimes?runtimes=claude-code,claude_code",
    )
    assert body["missing"] == ["claude_code"]
    assert body["missing_count"] == 1


def test_endpoint_missing_runtimes_all_paid_enforced(enforced_client):
    body = _get_json(
        enforced_client,
        "/api/entitlement/missing-runtimes?runtimes=claude_code,cursor",
    )
    assert set(body["missing"]) == {"claude_code", "cursor"}
    assert body["missing_count"] == 2
    assert body["any_missing"] is True


def test_endpoint_missing_runtimes_unknown_surfaces_in_missing(client):
    """Unknown runtime in grace: surfaces in ``missing`` AND ``unknown``."""
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes?runtimes=openclaw,bogus_runtime",
    )
    assert body["runtimes"] == ["openclaw"]
    assert body["unknown"] == ["bogus_runtime"]
    assert body["missing"] == ["bogus_runtime"]


def test_endpoint_missing_runtimes_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes?runtimes=openclaw,bogus_runtime",
    )
    assert body["missing"] == ent.missing_runtimes(["openclaw", "bogus_runtime"])


def test_endpoint_missing_runtimes_required_tier_parity_with_min_tier_endpoint(client):
    missing_body = _get_json(
        client,
        "/api/entitlement/missing-runtimes?runtimes=claude_code,cursor",
    )
    min_tier_body = _get_json(
        client,
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code,cursor",
    )
    assert missing_body["required_tier"] == min_tier_body["required_tier"]


def test_endpoint_missing_runtimes_current_tier_parity_with_has_runtimes(client):
    missing_body = _get_json(
        client,
        "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code",
    )
    has_body = _get_json(
        client,
        "/api/entitlement/has-runtimes?runtimes=openclaw,claude_code",
    )
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert missing_body[k] == has_body[k]


def test_endpoint_missing_runtimes_any_missing_negates_has_runtimes(client):
    missing_body = _get_json(
        client,
        "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code",
    )
    has_body = _get_json(
        client,
        "/api/entitlement/has-runtimes?runtimes=openclaw,claude_code",
    )
    assert missing_body["any_missing"] is (not has_body["has_runtimes"])


def test_endpoint_missing_runtimes_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["missing"] == []
    assert body["any_missing"] is False


def test_endpoint_missing_runtimes_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "missing_runtimes", _boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["missing"] == []


# ── Per-id parametrised parity with the singular has_feature / has_runtime ─────────────


@pytest.mark.parametrize("fid", sorted({"fleet", "sso", "nemo_governance", "otel_export"}))
def test_endpoint_missing_features_single_row_parity_with_has_feature(client, ent, fid):
    """Per-id: the row's absence-from-missing byte-equals the singular
    ``has_feature`` answer."""
    # skip unknown ids in the parametrisation defensively
    if fid not in ent.ALL_FEATURES:
        pytest.skip(f"{fid!r} not in ALL_FEATURES on this build")
    body = _get_json(client, f"/api/entitlement/missing-features?features={fid}")
    has_scalar = ent.has_feature(fid)
    is_missing = fid in body["missing"]
    assert is_missing is (not has_scalar)


@pytest.mark.parametrize("rid", sorted({"openclaw", "claude_code", "cursor", "codex"}))
def test_endpoint_missing_runtimes_single_row_parity_with_has_runtime(client, ent, rid):
    if rid not in ent.ALL_RUNTIMES:
        pytest.skip(f"{rid!r} not in ALL_RUNTIMES on this build")
    body = _get_json(client, f"/api/entitlement/missing-runtimes?runtimes={rid}")
    has_scalar = ent.has_runtime(rid)
    is_missing = rid in body["missing"]
    assert is_missing is (not has_scalar)


# ── Envelope stability across many input branches ──────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/missing-features",
        "/api/entitlement/missing-features?features=",
        "/api/entitlement/missing-features?features=fleet",
        "/api/entitlement/missing-features?features=fleet,sso",
        "/api/entitlement/missing-features?features=fleet,bogus_id",
        "/api/entitlement/missing-features?features=bogus_a,bogus_b",
        "/api/entitlement/missing-features?features=fleet,,sso,fleet",
        "/api/entitlement/missing-features?features=%20fleet%20,SSO",
    ],
)
def test_endpoint_missing_features_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _FEATURES_KEYS
    assert body["kind"] == "features"
    assert isinstance(body["features"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["missing"], list)
    assert isinstance(body["count"], int)
    assert isinstance(body["missing_count"], int)
    assert body["missing_count"] == len(body["missing"])
    assert body["count"] == len(body["features"])
    assert isinstance(body["any_missing"], bool)
    assert body["any_missing"] is (bool(body["missing"]) or bool(body["unknown"]))


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/missing-runtimes",
        "/api/entitlement/missing-runtimes?runtimes=",
        "/api/entitlement/missing-runtimes?runtimes=openclaw",
        "/api/entitlement/missing-runtimes?runtimes=openclaw,claude_code",
        "/api/entitlement/missing-runtimes?runtimes=claude-code",
        "/api/entitlement/missing-runtimes?runtimes=claude-code,claude_code",
        "/api/entitlement/missing-runtimes?runtimes=openclaw,bogus_runtime",
        "/api/entitlement/missing-runtimes?runtimes=%20openclaw%20,CLAUDE_CODE",
    ],
)
def test_endpoint_missing_runtimes_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _RUNTIMES_KEYS
    assert body["kind"] == "runtimes"
    assert isinstance(body["runtimes"], list)
    assert isinstance(body["unknown"], list)
    assert isinstance(body["missing"], list)
    assert body["missing_count"] == len(body["missing"])
    assert body["count"] == len(body["runtimes"])
    assert isinstance(body["any_missing"], bool)
    assert body["any_missing"] is (bool(body["missing"]) or bool(body["unknown"]))
