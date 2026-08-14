"""Tests for the aggregate mixed-axis path-shaped
:func:`clawmetry.entitlements.has_all_at_path` boolean-fold scalar and
its paired ``/api/entitlement/has-all-at-path`` endpoint.

Aggregate mixed-axis sibling of :func:`has_features_at_path` /
:func:`has_runtimes_at_path` (per-axis path walkers) and path-shaped
complement of :func:`has_all_at_batch` (fixes ONE 5-axis bundle and
sweeps across N caller-supplied perspective tiers). Fills the
``_at_path`` slot on the mixed-axis rollup family alongside
:func:`has_all_at` (singular perspective scalar),
:func:`has_all_at_batch` (multi-perspective batch), and
:func:`min_tier_for_all_at_batch` (reverse-lookup batch).

This file pins:

1. Scalar walk semantics byte-parity with :func:`has_features_at_path`
   / :func:`has_runtimes_at_path` / :func:`feature_catalog_path` /
   :func:`tier_path` (rung ``tier`` sequence, direction detection,
   endpoint semantics, same-rank sibling filter, purchasable-tier
   filter).
2. Per-rung ``has_all_at`` byte-parity with the scalar
   :func:`has_all_at` for the same (rung, bundle) pair.
3. Bundle-fold posture inherited from :func:`has_all_at`
   (fail-closed on empty / unknown / typo -- every rung's fold is
   ``False``).
4. Unknown-endpoint short-circuit: either endpoint unknown -> scalar
   returns ``None``; endpoint returns 200 with ``path=[]`` and
   ``direction="unknown"`` (never 4xxs).
5. Direction semantics: ``upgrade`` / ``downgrade`` / ``lateral`` /
   ``identity`` / ``unknown``.
6. Grace-independence: same answer under grace on vs enforce for the
   same (from, to, bundle) triple (delegates through
   :func:`has_all_at`, which reads the static per-tier grant tables).
7. Runtime alias posture: scalar is strict (``claude-code`` collapses
   the fold to ``False`` because it is not in :data:`ALL_RUNTIMES`);
   the paired endpoint canonicalises upstream so
   ``?runtimes=claude-code`` behaves like ``?runtimes=claude_code``.
8. Never-raises on delegate blowup: log-and-return ``None`` at scalar
   layer; empty-path fallback envelope at endpoint layer (never 5xxs).
9. Endpoint envelope shape (fixed key set) across every input branch,
   including the unknown-endpoint branch.
10. Cross-consistency with the sibling ``/tier-path`` /
    ``/feature-catalog-path`` / ``/has-features-at-path`` walks: same
    rung ``tier`` sequence rung-for-rung.
11. Rollup fields ``allowed_count`` / ``all_allowed`` / ``any_allowed``
    fold per-row ``has_all_at`` as documented on
    :func:`_has_all_at_path_body`.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask

# ── Fixtures ───────────────────────────────────────────────────────────────


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
def enforced(monkeypatch, tmp_path):
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


# ── Envelope shape ─────────────────────────────────────────────────────────

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "path",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_ROW_KEYS = {"tier", "tier_label", "tier_rank", "has_all_at"}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_all_at_path scalar ─────────────────────────────────────────────────


def test_scalar_identity_endpoints_returns_empty_path(ent):
    """``from == to`` -> empty path (identity branch)."""
    for tier in ent._TIER_ORDER:
        assert ent.has_all_at_path(tier, tier, features=["fleet"]) == []


def test_scalar_unknown_endpoint_returns_none(ent):
    assert ent.has_all_at_path("bogus", "pro", features=["fleet"]) is None
    assert ent.has_all_at_path("oss", "bogus", features=["fleet"]) is None
    assert ent.has_all_at_path("bogus_a", "bogus_b", features=["fleet"]) is None
    assert ent.has_all_at_path("", "pro", features=["fleet"]) is None
    assert ent.has_all_at_path(None, "pro", features=["fleet"]) is None  # type: ignore[arg-type]


def test_scalar_upgrade_path_row_shape(ent):
    path = ent.has_all_at_path(
        "oss", "enterprise", features=["fleet"], runtimes=["claude_code"]
    )
    assert isinstance(path, list) and len(path) >= 1
    for row in path:
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["has_all_at"], bool)


def test_scalar_downgrade_path_has_rows(ent):
    path = ent.has_all_at_path(
        "enterprise", "oss", features=["fleet"], channels=5
    )
    assert isinstance(path, list) and len(path) >= 1


def test_scalar_lateral_path_single_row(ent):
    """Same-rank different-id endpoints -> single-row path carrying the
    ``has_all_at`` at ``to`` (mirrors sibling path helpers)."""
    # cloud_pro / pro live at the same rank
    path = ent.has_all_at_path("cloud_pro", "pro", features=["fleet"])
    assert isinstance(path, list) and len(path) == 1
    assert path[0]["tier"] == "pro"
    assert path[0]["has_all_at"] == ent.has_all_at("pro", features=["fleet"])


def test_scalar_per_rung_parity_with_has_all_at(ent):
    """Per-rung ``has_all_at`` byte-equals :func:`has_all_at` for the
    same (rung, bundle) pair -- pins the scalar/path drift lock."""
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {
            "features": ["fleet", "sso"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    ]
    for bundle in bundles:
        path = ent.has_all_at_path("oss", "enterprise", **bundle)
        assert path is not None
        for row in path:
            assert row["has_all_at"] == ent.has_all_at(
                row["tier"], **bundle
            ), (row, bundle)


def test_scalar_walk_matches_has_features_at_path_walk(ent):
    """Rung ``tier`` sequence byte-equals the singular-axis path helpers
    -- pins byte-stability against the rest of the ``_path`` family."""
    agg = ent.has_all_at_path("oss", "enterprise", features=["fleet"])
    feat = ent.has_features_at_path("oss", "enterprise", ["fleet"])
    assert [r["tier"] for r in agg] == [r["tier"] for r in feat]


def test_scalar_walk_matches_has_runtimes_at_path_walk(ent):
    agg = ent.has_all_at_path("oss", "enterprise", runtimes=["claude_code"])
    rt = ent.has_runtimes_at_path("oss", "enterprise", ["claude_code"])
    assert [r["tier"] for r in agg] == [r["tier"] for r in rt]


def test_scalar_no_axes_supplied_all_rows_false(ent):
    """No axes supplied -> every row's ``has_all_at=False`` (matches
    :func:`has_all_at` empty-``False`` posture)."""
    path = ent.has_all_at_path("oss", "enterprise")
    assert path is not None and len(path) >= 1
    assert all(r["has_all_at"] is False for r in path)


def test_scalar_unknown_feature_collapses_all_rows(ent):
    path = ent.has_all_at_path("oss", "enterprise", features=["bogus"])
    assert path is not None and len(path) >= 1
    assert all(r["has_all_at"] is False for r in path)


def test_scalar_unknown_runtime_collapses_all_rows(ent):
    # strict scalar: raw alias ``claude-code`` is NOT canonicalised at
    # scalar layer, so it's treated as an unknown token
    path = ent.has_all_at_path("oss", "enterprise", runtimes=["claude-code"])
    assert path is not None and len(path) >= 1
    assert all(r["has_all_at"] is False for r in path)


def test_scalar_non_int_capacity_collapses_all_rows(ent):
    path = ent.has_all_at_path("oss", "enterprise", channels="huh")  # type: ignore[arg-type]
    assert path is not None and len(path) >= 1
    assert all(r["has_all_at"] is False for r in path)


def test_scalar_empty_bundle_lists_collapse_all_rows(ent):
    """``features=[]`` / ``runtimes=[]`` -- axis SUPPLIED but empty:
    collapses every rung's ``has_all_at`` to ``False`` (inherits the
    singular ``_at`` scalar's empty-``False`` typo posture)."""
    path = ent.has_all_at_path("oss", "enterprise", features=[])
    assert path is not None and all(r["has_all_at"] is False for r in path)
    path = ent.has_all_at_path("oss", "enterprise", runtimes=[])
    assert path is not None and all(r["has_all_at"] is False for r in path)


def test_scalar_grace_independence(ent, enforced):
    """Same (from, to, bundle) triple -> byte-identical rows under
    grace vs enforce (delegates to static per-tier tables)."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    a = ent.has_all_at_path("oss", "enterprise", **bundle)
    b = enforced.has_all_at_path("oss", "enterprise", **bundle)
    # Compare per-row (label / rank / has_all_at); both should be equal
    assert [
        (r["tier"], r["has_all_at"]) for r in a
    ] == [(r["tier"], r["has_all_at"]) for r in b]


def test_scalar_direction_transitions_are_monotone(ent):
    """Upgrade: has_all_at only flips False -> True (never the
    reverse); downgrade: only True -> False."""
    # a bundle only Pro+ grants: fleet + claude_code + 5 channels
    up = ent.has_all_at_path(
        "oss", "enterprise", features=["fleet"], runtimes=["claude_code"]
    )
    assert up is not None
    seen_true = False
    for row in up:
        if row["has_all_at"]:
            seen_true = True
        else:
            # once we flip True we cannot go False again on an upgrade walk
            assert not seen_true
    down = ent.has_all_at_path(
        "enterprise", "oss", features=["fleet"], runtimes=["claude_code"]
    )
    assert down is not None
    seen_false = False
    for row in down:
        if not row["has_all_at"]:
            seen_false = True
        else:
            assert not seen_false


def test_scalar_never_raises_on_broken_bundle(ent, monkeypatch):
    """Delegate blowup -> log + return None."""

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "has_all_at", _boom)
    # Even with the scalar broken, we return either a list or None (not
    # crash). Because the delegate raises inside a row builder, the
    # outer try/except catches it and returns None.
    result = ent.has_all_at_path("oss", "enterprise", features=["fleet"])
    assert result is None


def test_scalar_non_iterable_bundle_collapses(ent):
    """Non-iterable ``features`` -> [] internally -> row folds to
    False (fail-closed typo posture)."""
    path = ent.has_all_at_path("oss", "enterprise", features=42)  # type: ignore[arg-type]
    assert path is not None
    assert all(r["has_all_at"] is False for r in path)


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_envelope_shape_stable_across_branches(client):
    urls = [
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=fleet",
        "/api/entitlement/has-all-at-path?from=oss&to=oss&features=fleet",
        "/api/entitlement/has-all-at-path?from=oss&to=nope&features=fleet",
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=bogus",
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise",
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&channels=huh",
        "/api/entitlement/has-all-at-path?from=&to=&features=fleet",
        "/api/entitlement/has-all-at-path",
    ]
    for url in urls:
        d = _get_json(client, url)
        assert set(d.keys()) == _ENVELOPE_KEYS, url
        for row in d["path"]:
            assert set(row.keys()) == _ROW_KEYS, url


def test_endpoint_happy_upgrade_path(client, ent):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=fleet",
    )
    assert d["direction"] == "upgrade"
    assert d["from"] == "oss" and d["to"] == "enterprise"
    assert d["path_length"] == len(d["path"]) >= 1
    # Rollup accounting
    assert d["allowed_count"] == sum(1 for r in d["path"] if r["has_all_at"])
    assert d["all_allowed"] == all(r["has_all_at"] for r in d["path"])
    assert d["any_allowed"] == any(r["has_all_at"] for r in d["path"])
    # Parity: per-rung endpoint answer byte-equals scalar
    for row in d["path"]:
        assert row["has_all_at"] == ent.has_all_at(
            row["tier"], features=["fleet"]
        )


def test_endpoint_downgrade_walk(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=enterprise&to=oss&features=fleet",
    )
    assert d["direction"] == "downgrade"
    # Descending tier ranks
    ranks = [r["tier_rank"] for r in d["path"]]
    assert ranks == sorted(ranks, reverse=True)


def test_endpoint_identity_returns_empty_path(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=pro&to=pro&features=fleet",
    )
    assert d["direction"] == "identity"
    assert d["path"] == [] and d["path_length"] == 0
    # Rollup fields collapse on empty path
    assert d["allowed_count"] == 0
    assert d["all_allowed"] is False
    assert d["any_allowed"] is False


def test_endpoint_lateral_single_row(client, ent):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=cloud_pro&to=pro&features=fleet",
    )
    assert d["direction"] == "lateral"
    assert d["path_length"] == 1
    assert d["path"][0]["tier"] == "pro"


def test_endpoint_unknown_endpoint_never_4xxs(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=nope&features=fleet",
    )
    assert d["direction"] == "unknown"
    assert d["path"] == [] and d["path_length"] == 0


def test_endpoint_missing_endpoint_never_4xxs(client):
    d = _get_json(client, "/api/entitlement/has-all-at-path")
    assert d["direction"] == "unknown"
    assert d["path"] == []


def test_endpoint_no_axes_supplied_all_rows_false(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise",
    )
    assert d["supplied_axes"] == []
    assert d["path"]  # walk still happens
    assert all(r["has_all_at"] is False for r in d["path"])
    assert d["allowed_count"] == 0


def test_endpoint_unknown_feature_collapses_all_rows(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=bogus",
    )
    assert d["unknown_features"] == ["bogus"]
    assert d["features"] == []
    assert d["path"] and all(r["has_all_at"] is False for r in d["path"])


def test_endpoint_alias_canonicalisation(client, ent):
    """``claude-code`` -> ``claude_code`` upstream: the endpoint
    canonicalises per-token before the strict scalar sees it."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&runtimes=claude-code",
    )
    assert d["runtimes"] == ["claude_code"]
    assert d["unknown_runtimes"] == []
    for row in d["path"]:
        assert row["has_all_at"] == ent.has_all_at(
            row["tier"], runtimes=["claude_code"]
        )


def test_endpoint_alias_and_canonical_pair_dedups(client):
    """``claude-code,claude_code`` collapses to ONE entry (alias dedup
    matches sibling ``/has-runtimes-at-path`` posture)."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&runtimes=claude-code,claude_code",
    )
    assert d["runtimes"] == ["claude_code"]


def test_endpoint_capacity_axis_int_ok(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&channels=5",
    )
    assert d["channels"] == 5
    assert "channels" in d["supplied_axes"]


def test_endpoint_capacity_axis_blank_collapses_all_rows(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&channels=",
    )
    assert d["channels"] is None
    assert "channels" in d["supplied_axes"]
    # blank capacity collapses every row to False
    assert all(r["has_all_at"] is False for r in d["path"])


def test_endpoint_capacity_axis_non_int_collapses_all_rows(client):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&channels=huh",
    )
    assert d["channels"] is None
    assert all(r["has_all_at"] is False for r in d["path"])


def test_endpoint_mixed_axes_happy_path(client, ent):
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise"
        "&features=fleet&runtimes=claude-code&channels=5"
        "&retention_days=30&nodes=2",
    )
    assert d["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]
    assert d["supplied_count"] == 5
    # Per-rung parity vs scalar for same (rung, full bundle)
    kw = dict(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=2,
    )
    for row in d["path"]:
        assert row["has_all_at"] == ent.has_all_at(row["tier"], **kw)


def test_endpoint_rung_walk_matches_has_features_at_path_endpoint(client):
    """Rung ``tier`` sequence byte-equals ``/has-features-at-path`` on
    the same (from, to)."""
    a = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=fleet",
    )
    b = _get_json(
        client,
        "/api/entitlement/has-features-at-path?from=oss&to=enterprise&features=fleet",
    )
    assert [r["tier"] for r in a["path"]] == [r["tier"] for r in b["path"]]


def test_endpoint_required_tier_rollup_matches_singular(client, ent):
    """``required_tier`` folds through
    :func:`min_tier_for_all` on the KNOWN-only subset -- matches the
    singular ``/has-all-at`` endpoint byte-for-byte."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise"
        "&features=fleet&runtimes=claude_code",
    )
    required = ent.min_tier_for_all(
        features=["fleet"], runtimes=["claude_code"]
    )
    assert d["required_tier"] == required
    assert d["required_tier_label"] == (
        ent.tier_label(required) if required else None
    )
    assert d["required_tier_rank"] == (
        ent.tier_rank(required) if required else -1
    )


def test_endpoint_grace_pass_through_in_resolver_slot(client):
    """The LIVE resolver envelope stays in grace mode (rollout state);
    per-rung ``has_all_at`` reads the static tables regardless."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=fleet",
    )
    assert d["grace"] is True
    assert d["enforced"] is False


def test_endpoint_never_5xxs_on_scalar_blowup(monkeypatch, client, ent):
    """Scalar blowup -> fallback envelope (never 5xxs)."""

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(ent, "has_all_at_path", _boom)
    resp = client.get(
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&features=fleet"
    )
    assert resp.status_code == 200
    d = resp.get_json()
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["path"] == []
    assert d["all_allowed"] is False
    assert d["any_allowed"] is False


def test_endpoint_per_rung_byte_parity_with_has_all_at_endpoint(client):
    """Per-rung endpoint answer byte-equals
    ``/has-all-at?tier=<rung>&<same bundle>``'s ``has_all_at`` -- pins
    the endpoint drift lock."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise"
        "&features=fleet&runtimes=claude_code&channels=5",
    )
    for row in d["path"]:
        singular = _get_json(
            client,
            "/api/entitlement/has-all-at?tier="
            + row["tier"]
            + "&features=fleet&runtimes=claude_code&channels=5",
        )
        assert row["has_all_at"] == singular["has_all_at"], row["tier"]


def test_endpoint_free_runtime_openclaw_pass_through(client, ent):
    """FREE_RUNTIMES (`openclaw`) always grants at every rung
    (mirrors the free-tier posture the rest of the family carries)."""
    d = _get_json(
        client,
        "/api/entitlement/has-all-at-path?from=oss&to=enterprise&runtimes=openclaw",
    )
    for row in d["path"]:
        assert row["has_all_at"] is True, row


def test_endpoint_enforce_matches_grace_shape(monkeypatch, tmp_path):
    """Under ``CLAWMETRY_ENFORCE=1`` the envelope shape and per-rung
    ``has_all_at`` are byte-identical to grace (the ``_at_path`` slot
    reads static tables, not the resolver's ``grace`` bit)."""
    from flask import Flask

    from routes.entitlement import bp_entitlement

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        c = app.test_client()
        r = c.get(
            "/api/entitlement/has-all-at-path?from=oss&to=enterprise"
            "&features=fleet&runtimes=claude_code"
        )
        assert r.status_code == 200
        d = r.get_json()
        assert set(d.keys()) == _ENVELOPE_KEYS
        # Enforce mode: resolver slot flips
        assert d["enforced"] is True
        # Per-rung answer still delegates to static tables
        for row in d["path"]:
            assert row["has_all_at"] == e.has_all_at(
                row["tier"], features=["fleet"], runtimes=["claude_code"]
            )
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()
