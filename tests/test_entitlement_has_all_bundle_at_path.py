"""Tests for the bundle-shaped path-walk pair:
:func:`clawmetry.entitlements.has_all_bundle_at_path` /
:func:`clawmetry.entitlements.missing_all_bundle_at_path` and their
paired POST ``/api/entitlement/has-all-bundle-at-path`` /
``/api/entitlement/missing-all-bundle-at-path`` endpoints.

Path-shaped bundle siblings of :func:`has_all_bundle_at` /
:func:`_missing_all_bundle_row_at` (singular perspective) and
bundle-shaped counterparts of :func:`has_all_at_path` /
:func:`missing_all_at_path` (kwargs-shaped path walkers). Fills the
``_at_path`` slot on the aggregate 5-axis bundle boolean-fold and
row-detail families.

Pins:

1. Walk semantics byte-parity with :func:`has_all_at_path` /
   :func:`missing_all_at_path` (rung ``tier`` sequence, direction
   detection, endpoint semantics, purchasable-tier filter,
   destination-sibling exclusion).
2. Per-rung ``has_all_at`` byte-parity with
   :func:`has_all_bundle_at` for the same (rung, bundle) pair.
3. Per-rung ``missing`` byte-parity with
   :func:`_missing_all_bundle_row_at` for the same pair.
4. Complement invariant: ``any(missing.values())`` = ``not has_all_at``
   per rung on the paired boolean-fold row.
5. Grace-independence: same answer under grace-on vs enforce for the
   same (from, to, bundle) triple.
6. Unknown-endpoint short-circuit: either endpoint unknown -> scalar
   returns ``None``; endpoint returns 200 with ``path=[]`` and
   ``direction="unknown"`` (never 4xxs on endpoint validity).
7. Direction semantics: ``upgrade`` / ``downgrade`` / ``lateral`` /
   ``identity`` / ``unknown``.
8. Bundle normalisation semantics inherited from
   :func:`_normalise_all_bundle`: bare-dict shorthand accepted;
   non-dict / ``None`` bundle collapses to empty axis echo; runtime
   alias canonicalisation (``claude-code`` -> ``claude_code``); unknown
   runtime id dropped from echo.
9. Endpoint POST body: wrapped form + bare-dict shorthand both work;
   400 on missing / non-object bundle.
10. Never-raises on delegate blowup: scalar returns ``None``, endpoint
    returns the empty-path fallback envelope.
11. Endpoint envelope shape (fixed key set) across every input branch.
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


# ── Envelope + row shape constants ─────────────────────────────────────────

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
    "path",
    "path_length",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_HAS_ENVELOPE_KEYS = _ENVELOPE_KEYS | {
    "allowed_count",
    "all_allowed",
    "any_allowed",
}

_MISSING_ENVELOPE_KEYS = _ENVELOPE_KEYS | {
    "denied_count",
    "all_denied",
    "any_denied",
}

_HAS_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all_at",
}

_MISSING_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "missing",
}


def _post_json(client, url: str, body: dict) -> dict:
    resp = client.post(url, json=body)
    assert resp.status_code == 200, (url, resp.status_code, resp.get_data(as_text=True))
    return resp.get_json()


# ── Scalar: identity + unknown-endpoint short-circuit ──────────────────────


def test_has_scalar_identity_returns_empty_path(ent):
    for tier in ent._TIER_ORDER:
        assert ent.has_all_bundle_at_path(tier, tier, {"features": ["fleet"]}) == []


def test_missing_scalar_identity_returns_empty_path(ent):
    for tier in ent._TIER_ORDER:
        assert ent.missing_all_bundle_at_path(
            tier, tier, {"features": ["fleet"]}
        ) == []


@pytest.mark.parametrize("bad_from,bad_to", [
    ("bogus", "cloud_pro"),
    ("oss", "bogus"),
    ("bogus_a", "bogus_b"),
    ("", "cloud_pro"),
    (None, "cloud_pro"),
    ("oss", None),
])
def test_has_scalar_unknown_endpoint_returns_none(ent, bad_from, bad_to):
    assert ent.has_all_bundle_at_path(bad_from, bad_to, {"features": ["fleet"]}) is None


@pytest.mark.parametrize("bad_from,bad_to", [
    ("bogus", "cloud_pro"),
    ("oss", "bogus"),
    ("", "cloud_pro"),
    (None, "cloud_pro"),
])
def test_missing_scalar_unknown_endpoint_returns_none(ent, bad_from, bad_to):
    assert ent.missing_all_bundle_at_path(
        bad_from, bad_to, {"features": ["fleet"]}
    ) is None


# ── Row shape + per-rung parity ────────────────────────────────────────────


def test_has_scalar_row_shape_and_per_rung_parity_with_bundle_at(ent):
    """Each row's has_all_at byte-equals has_all_bundle_at(rung, bundle)."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
    }
    path = ent.has_all_bundle_at_path("oss", "enterprise", bundle)
    assert isinstance(path, list) and path
    for row in path:
        assert set(row.keys()) == _HAS_ROW_KEYS
        assert isinstance(row["has_all_at"], bool)
        assert row["tier_label"] == ent.tier_label(row["tier"])
        assert row["tier_rank"] == ent._TIER_RANK.get(row["tier"], -1)

        # Byte-parity with the singular has_all_bundle_at.
        singular = ent.has_all_bundle_at(row["tier"], bundle)
        assert singular is not None
        assert row["has_all_at"] == bool(singular["has_all_at"])
        assert row["features"] == list(singular["features"])
        assert row["runtimes"] == list(singular["runtimes"])
        assert row["channels"] == singular["channels"]
        assert row["retention_days"] == singular["retention_days"]
        assert row["nodes"] == singular["nodes"]


def test_missing_scalar_row_shape_and_per_rung_parity(ent):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 500,
    }
    path = ent.missing_all_bundle_at_path("oss", "enterprise", bundle)
    assert isinstance(path, list) and path
    for row in path:
        assert set(row.keys()) == _MISSING_ROW_KEYS
        assert isinstance(row["missing"], dict)
        assert set(row["missing"].keys()) == {
            "features",
            "runtimes",
            "channels",
            "retention_days",
            "nodes",
        }
        # Byte-parity with the private row helper (feeds
        # missing_all_bundle_batch_at which is the same code path).
        singular = ent._missing_all_bundle_row_at(row["tier"], bundle)
        assert row["features"] == list(singular["features"])
        assert row["runtimes"] == list(singular["runtimes"])
        assert row["channels"] == singular["channels"]
        assert row["retention_days"] == singular["retention_days"]
        assert row["nodes"] == singular["nodes"]
        assert row["missing"] == singular["missing"]


def test_complement_invariant_has_vs_missing_per_rung(ent):
    """any(row['missing'].values()) == not paired_row['has_all_at']."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 500,
        "retention_days": 365,
        "nodes": 99,
    }
    has_path = ent.has_all_bundle_at_path("oss", "enterprise", bundle)
    miss_path = ent.missing_all_bundle_at_path("oss", "enterprise", bundle)
    assert len(has_path) == len(miss_path)
    for has_row, miss_row in zip(has_path, miss_path):
        assert has_row["tier"] == miss_row["tier"]
        m = miss_row["missing"]
        any_missing = any(v for v in m.values() if v not in (None, []))
        assert bool(any_missing) == (not has_row["has_all_at"]), (
            has_row["tier"], has_row["has_all_at"], m,
        )


# ── Walk direction semantics ───────────────────────────────────────────────


def test_has_upgrade_direction_ascending_rungs(ent):
    path = ent.has_all_bundle_at_path(
        "oss", "enterprise", {"features": ["fleet"]}
    )
    ranks = [row["tier_rank"] for row in path]
    assert ranks == sorted(ranks)
    assert all(t in ent._PURCHASABLE_TIERS for t in [r["tier"] for r in path])
    # Grants only flip False -> True upward.
    seen_true = False
    for row in path:
        if row["has_all_at"]:
            seen_true = True
        else:
            assert not seen_true, "grant flipped back to False on ascent"


def test_missing_downgrade_direction_descending_rungs(ent):
    path = ent.missing_all_bundle_at_path(
        "enterprise", "oss", {"features": ["fleet"]}
    )
    ranks = [row["tier_rank"] for row in path]
    assert ranks == sorted(ranks, reverse=True)


def test_has_lateral_same_rank_single_row(ent):
    """cloud_pro and pro share rank 2 -> lateral, single row for the dest."""
    assert ent._TIER_RANK["cloud_pro"] == ent._TIER_RANK["pro"]
    path = ent.has_all_bundle_at_path(
        "cloud_pro", "pro", {"features": ["fleet"]}
    )
    assert isinstance(path, list) and len(path) == 1
    assert path[0]["tier"] == "pro"


# ── Bundle normalisation semantics ─────────────────────────────────────────


@pytest.mark.parametrize("bad_bundle", [None, "not-a-dict", 42, []])
def test_has_scalar_non_dict_bundle_collapses_to_empty_echo(ent, bad_bundle):
    path = ent.has_all_bundle_at_path("oss", "enterprise", bad_bundle)
    assert isinstance(path, list) and path
    for row in path:
        assert row["features"] == []
        assert row["runtimes"] == []
        assert row["channels"] is None
        assert row["retention_days"] is None
        assert row["nodes"] is None
        # No axes supplied -> singular has_all_bundle_at fold is False.
        assert row["has_all_at"] is False


def test_has_scalar_runtime_alias_canonicalised(ent):
    """claude-code (alias) canonicalises to claude_code in echo."""
    path = ent.has_all_bundle_at_path(
        "oss", "enterprise", {"runtimes": ["claude-code"]}
    )
    for row in path:
        assert row["runtimes"] == ["claude_code"]


def test_has_scalar_unknown_runtime_collapses_fold_on_every_rung(ent):
    """An unknown runtime id survives normalisation into the echo (matches
    :func:`has_all_bundle_batch` typo posture) and collapses every rung's
    ``has_all_at`` to ``False`` via :func:`has_all_at`'s strict typo
    posture."""
    path = ent.has_all_bundle_at_path(
        "oss", "enterprise", {"runtimes": ["totally_bogus"]}
    )
    assert isinstance(path, list) and path
    for row in path:
        assert row["has_all_at"] is False


# ── Grace-independence ────────────────────────────────────────────────────


def test_has_scalar_grace_independence(ent, enforced):
    """Same (from, to, bundle) triple -> byte-identical rows under grace
    vs enforce (delegates to the static per-tier tables)."""
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    grace_path = ent.has_all_bundle_at_path("oss", "enterprise", bundle)
    enforce_path = enforced.has_all_bundle_at_path(
        "oss", "enterprise", bundle
    )
    assert grace_path == enforce_path


def test_missing_scalar_grace_independence(ent, enforced):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    grace_path = ent.missing_all_bundle_at_path("oss", "enterprise", bundle)
    enforce_path = enforced.missing_all_bundle_at_path(
        "oss", "enterprise", bundle
    )
    assert grace_path == enforce_path


# ── Never-raises on delegate blowup ────────────────────────────────────────


def test_has_scalar_never_raises_on_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **k):
        raise RuntimeError("intentional")

    monkeypatch.setattr(ent, "_has_all_bundle_row_at", _boom)
    # Delegate blowup inside the row builder is caught inside the row
    # helper (wraps has_all_at); the outer walker also has its own
    # try/except that returns None. Either way the scalar never raises.
    result = ent.has_all_bundle_at_path(
        "oss", "enterprise", {"features": ["fleet"]}
    )
    # Result is either a path of empty-row shapes (row helper's own
    # try/except) or None (outer walker). Both are non-raising.
    assert result is None or isinstance(result, list)


# ── Endpoint: happy paths ──────────────────────────────────────────────────


def test_has_endpoint_upgrade_envelope_shape(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=enterprise",
        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert set(body.keys()) == _HAS_ENVELOPE_KEYS
    assert body["direction"] == "upgrade"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["path_length"] == len(body["path"])
    for row in body["path"]:
        assert set(row.keys()) == _HAS_ROW_KEYS


def test_missing_endpoint_upgrade_envelope_shape(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=enterprise",
        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert set(body.keys()) == _MISSING_ENVELOPE_KEYS
    assert body["direction"] == "upgrade"
    assert body["path_length"] == len(body["path"])
    for row in body["path"]:
        assert set(row.keys()) == _MISSING_ROW_KEYS
        assert set(row["missing"].keys()) == {
            "features",
            "runtimes",
            "channels",
            "retention_days",
            "nodes",
        }


def test_has_endpoint_bare_dict_shorthand_body(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=cloud_pro",
        {"features": ["fleet"]},
    )
    assert body["direction"] == "upgrade"
    assert body["path_length"] >= 1
    for row in body["path"]:
        assert row["features"] == ["fleet"]


def test_missing_endpoint_bare_dict_shorthand_body(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=cloud_pro",
        {"features": ["fleet"]},
    )
    assert body["direction"] == "upgrade"
    for row in body["path"]:
        assert row["features"] == ["fleet"]


def test_has_endpoint_identity_returns_empty_path(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=oss",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["direction"] == "identity"
    assert body["path"] == []
    assert body["path_length"] == 0
    assert body["allowed_count"] == 0
    assert body["all_allowed"] is False
    assert body["any_allowed"] is False


def test_missing_endpoint_identity_returns_empty_path(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=oss",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["direction"] == "identity"
    assert body["path"] == []
    assert body["denied_count"] == 0
    assert body["all_denied"] is False
    assert body["any_denied"] is False


def test_has_endpoint_downgrade_direction(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=enterprise&to=oss",
        {"features": ["fleet"]},
    )
    assert body["direction"] == "downgrade"
    ranks = [row["tier_rank"] for row in body["path"]]
    assert ranks == sorted(ranks, reverse=True)


def test_has_endpoint_lateral_direction(client, ent):
    assert ent._TIER_RANK["cloud_pro"] == ent._TIER_RANK["pro"]
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=cloud_pro&to=pro",
        {"features": ["fleet"]},
    )
    assert body["direction"] == "lateral"
    assert body["path_length"] == 1
    assert body["path"][0]["tier"] == "pro"


# ── Endpoint: unknown / missing endpoints ──────────────────────────────────


@pytest.mark.parametrize("qs", [
    "?from=&to=cloud_pro",
    "?from=oss&to=",
    "?from=bogus&to=cloud_pro",
    "?from=oss&to=bogus",
    "",  # both missing entirely
])
def test_has_endpoint_unknown_endpoint_returns_empty_path(client, qs):
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path" + qs,
        json={"bundle": {"features": ["fleet"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["path_length"] == 0
    # direction reads "unknown" (or "identity" only when the two happen to
    # be equal-string, which never happens on this parametrisation).
    assert body["direction"] in {"unknown", "identity"}


@pytest.mark.parametrize("qs", [
    "?from=&to=cloud_pro",
    "?from=oss&to=",
    "?from=bogus&to=cloud_pro",
    "?from=oss&to=bogus",
])
def test_missing_endpoint_unknown_endpoint_returns_empty_path(client, qs):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path" + qs,
        json={"bundle": {"features": ["fleet"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["path_length"] == 0
    assert body["direction"] in {"unknown", "identity"}


# ── Endpoint: 400 on missing / non-object bundle ───────────────────────────


def test_has_endpoint_missing_bundle_returns_400(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=cloud_pro",
        json={},
    )
    assert resp.status_code == 400
    assert "missing bundle" in resp.get_json()["error"]


def test_has_endpoint_non_object_bundle_returns_400(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=cloud_pro",
        json={"bundle": "not-a-dict"},
    )
    assert resp.status_code == 400
    assert "object" in resp.get_json()["error"]


def test_missing_endpoint_missing_bundle_returns_400(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=cloud_pro",
        json={},
    )
    assert resp.status_code == 400


def test_missing_endpoint_non_object_bundle_returns_400(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=cloud_pro",
        json={"bundle": 42},
    )
    assert resp.status_code == 400


# ── Endpoint: never-5xxs on delegate blowup ────────────────────────────────


def test_has_endpoint_fallback_on_delegate_blowup(monkeypatch, client):
    """Scalar returns garbage that trips row iteration -> endpoint still
    returns 200 with the fallback envelope."""
    from clawmetry import entitlements as _ent

    def _boom(*a, **k):
        raise RuntimeError("intentional")

    monkeypatch.setattr(_ent, "has_all_bundle_at_path", _boom)
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=enterprise",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["allowed_count"] == 0
    assert body["all_allowed"] is False
    assert body["any_allowed"] is False


def test_missing_endpoint_fallback_on_delegate_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **k):
        raise RuntimeError("intentional")

    monkeypatch.setattr(_ent, "missing_all_bundle_at_path", _boom)
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=enterprise",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["path"] == []
    assert body["denied_count"] == 0
    assert body["all_denied"] is False
    assert body["any_denied"] is False


# ── Endpoint: envelope rollup semantics ────────────────────────────────────


def test_has_endpoint_free_feature_grants_every_rung(client):
    """A FREE_RUNTIMES bundle grants on every rung (openclaw is free)."""
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path?from=oss&to=enterprise",
        {"bundle": {"runtimes": ["openclaw"]}},
    )
    assert body["path_length"] >= 1
    assert body["allowed_count"] == body["path_length"]
    assert body["all_allowed"] is True
    assert body["any_allowed"] is True


def test_missing_endpoint_free_feature_never_denied(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path?from=oss&to=enterprise",
        {"bundle": {"runtimes": ["openclaw"]}},
    )
    assert body["path_length"] >= 1
    assert body["denied_count"] == 0
    assert body["all_denied"] is False
    assert body["any_denied"] is False
    for row in body["path"]:
        assert row["missing"]["runtimes"] == []


# ── Rung walk cross-consistency with the kwargs-shaped sibling ─────────────


def test_has_rung_sequence_matches_kwargs_shaped_path_walker(ent):
    """has_all_bundle_at_path walks the SAME rung sequence as
    has_all_at_path for the same (from, to) endpoints."""
    bundle = {"features": ["fleet"]}
    bundle_path = ent.has_all_bundle_at_path("oss", "enterprise", bundle)
    kwargs_path = ent.has_all_at_path(
        "oss", "enterprise", features=["fleet"]
    )
    assert [r["tier"] for r in bundle_path] == [r["tier"] for r in kwargs_path]


def test_missing_rung_sequence_matches_kwargs_shaped_path_walker(ent):
    bundle = {"features": ["fleet"]}
    bundle_path = ent.missing_all_bundle_at_path(
        "oss", "enterprise", bundle
    )
    kwargs_path = ent.missing_all_at_path(
        "oss", "enterprise", features=["fleet"]
    )
    assert [r["tier"] for r in bundle_path] == [r["tier"] for r in kwargs_path]
