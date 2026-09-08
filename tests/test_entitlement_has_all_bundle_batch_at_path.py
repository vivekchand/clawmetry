"""Tests for the bundle-axis batch path-walk pair:
:func:`clawmetry.entitlements.has_all_bundle_batch_at_path` /
:func:`clawmetry.entitlements.missing_all_bundle_batch_at_path` and
their paired POST ``/api/entitlement/has-all-bundle-batch-at-path`` /
``/api/entitlement/missing-all-bundle-batch-at-path`` endpoints.

Bundle-axis batch siblings of :func:`has_all_bundle_at_path` /
:func:`missing_all_bundle_at_path` (singular bundle) and path-shaped
counterparts of :func:`has_all_bundle_batch_at` /
:func:`missing_all_bundle_batch_at` (perspective-batch, no path).
Fills the ``_batch_at_path`` slot on the aggregate 5-axis bundle
boolean-fold and row-detail families.

Pins:

1. Per-cell ``path`` byte-parity with the singular
   :func:`has_all_bundle_at_path` / :func:`missing_all_bundle_at_path`
   for the same ``(from, to, bundle)`` triple.
2. Per-cell per-rung ``has_all_at`` / ``missing`` byte-parity with the
   perspective-batch seat (:func:`has_all_bundle_batch_at`).
3. Complement invariant per cell per rung: ``any(row['missing'].values())``
   byte-equals ``not paired_row['has_all_at']`` on the paired boolean-
   fold call for every fully-parseable bundle.
4. Grace-independence: same answer under grace-on vs enforce for the
   same ``(from, to, bundles)`` triple.
5. Unknown-endpoint short-circuit: either endpoint unknown -> scalar
   returns ``None``; endpoint returns 200 with ``bundles=[]`` /
   ``count=0`` and ``direction="unknown"`` (never 4xxs on endpoint
   validity).
6. Direction semantics (envelope-level, shared across every cell):
   ``upgrade`` / ``downgrade`` / ``lateral`` / ``identity`` /
   ``unknown``.
7. Bundles argument handling: list of bundle dicts, bare-dict
   shorthand, non-iterable / ``None`` bundles -> ``[]`` scalar
   short-circuit; missing / empty / non-list-non-dict body -> 400.
8. Bundle normalisation inherited from :func:`_normalise_all_bundle`:
   non-dict bundle collapses to empty axis echo; runtime alias
   canonicalisation (``claude-code`` -> ``claude_code``); unknown
   runtime id dropped from echo.
9. Endpoint envelope shape (fixed key set) across every input branch.
10. Never-raises on delegate blowup: scalar returns ``None`` on outer
    failure, endpoint returns the fallback envelope.
11. Per-cell rollups: ``allowed_count`` / ``all_allowed`` /
    ``any_allowed`` for the has-side; ``denied_count`` / ``all_denied``
    / ``any_denied`` for the missing-side.
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
    "bundles",
    "count",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_HAS_CELL_KEYS = {
    "bundle_index",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "path",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
}

_MISSING_CELL_KEYS = {
    "bundle_index",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "path",
    "path_length",
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
    assert resp.status_code == 200, (
        url,
        resp.status_code,
        resp.get_data(as_text=True),
    )
    return resp.get_json()


# ── Scalar: unknown-endpoint short-circuit ─────────────────────────────────


@pytest.mark.parametrize(
    "bad_from,bad_to",
    [
        ("bogus", "cloud_pro"),
        ("oss", "bogus"),
        ("bogus_a", "bogus_b"),
        ("", "cloud_pro"),
        (None, "cloud_pro"),
        ("oss", None),
    ],
)
def test_has_scalar_unknown_endpoint_returns_none(ent, bad_from, bad_to):
    assert (
        ent.has_all_bundle_batch_at_path(
            bad_from, bad_to, [{"features": ["fleet"]}]
        )
        is None
    )


@pytest.mark.parametrize(
    "bad_from,bad_to",
    [
        ("bogus", "cloud_pro"),
        ("oss", "bogus"),
        ("", "cloud_pro"),
        (None, "cloud_pro"),
    ],
)
def test_missing_scalar_unknown_endpoint_returns_none(ent, bad_from, bad_to):
    assert (
        ent.missing_all_bundle_batch_at_path(
            bad_from, bad_to, [{"features": ["fleet"]}]
        )
        is None
    )


# ── Scalar: bundles argument handling ──────────────────────────────────────


def test_has_scalar_none_bundles_returns_empty_list(ent):
    assert ent.has_all_bundle_batch_at_path("oss", "enterprise", None) == []


def test_missing_scalar_none_bundles_returns_empty_list(ent):
    assert (
        ent.missing_all_bundle_batch_at_path("oss", "enterprise", None) == []
    )


def test_has_scalar_non_iterable_bundles_returns_empty_list(ent):
    assert ent.has_all_bundle_batch_at_path("oss", "enterprise", 42) == []


def test_missing_scalar_non_iterable_bundles_returns_empty_list(ent):
    assert (
        ent.missing_all_bundle_batch_at_path("oss", "enterprise", 42) == []
    )


# ── Scalar: identity + lateral branches ────────────────────────────────────


def test_has_scalar_identity_yields_empty_path_per_cell(ent):
    bundles = [{"features": ["fleet"]}, {"runtimes": ["claude_code"]}]
    for tier in ent._TIER_ORDER:
        out = ent.has_all_bundle_batch_at_path(tier, tier, bundles)
        assert isinstance(out, list) and len(out) == len(bundles)
        for cell in out:
            assert cell["path"] == []


def test_missing_scalar_identity_yields_empty_path_per_cell(ent):
    bundles = [{"features": ["fleet"]}, {"runtimes": ["claude_code"]}]
    for tier in ent._TIER_ORDER:
        out = ent.missing_all_bundle_batch_at_path(tier, tier, bundles)
        assert isinstance(out, list) and len(out) == len(bundles)
        for cell in out:
            assert cell["path"] == []


# ── Scalar: per-cell path byte-parity with singular ────────────────────────


def test_has_scalar_cell_path_byte_parity_with_singular(ent):
    """Each cell's path list byte-equals has_all_bundle_at_path for the
    same (from, to, bundle) triple.
    """
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"], "channels": 5},
        {"channels": 500},
        {},
    ]
    batch = ent.has_all_bundle_batch_at_path("oss", "enterprise", bundles)
    assert isinstance(batch, list) and len(batch) == len(bundles)
    for cell in batch:
        singular = ent.has_all_bundle_at_path(
            "oss", "enterprise", bundles[cell["bundle_index"]]
        )
        assert cell["path"] == singular


def test_missing_scalar_cell_path_byte_parity_with_singular(ent):
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"], "channels": 500},
        {"nodes": 99},
        {},
    ]
    batch = ent.missing_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    assert isinstance(batch, list) and len(batch) == len(bundles)
    for cell in batch:
        singular = ent.missing_all_bundle_at_path(
            "oss", "enterprise", bundles[cell["bundle_index"]]
        )
        assert cell["path"] == singular


# ── Scalar: per-cell rung ordering + shape ─────────────────────────────────


def test_has_scalar_per_cell_walk_matches_has_all_at_path(ent):
    """The cell's rung sequence byte-equals has_all_at_path for the
    normalised bundle for the same (from, to) endpoint pair.
    """
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"], "channels": 5}
    batch = ent.has_all_bundle_batch_at_path("oss", "enterprise", [bundle])
    cell = batch[0]
    (
        features,
        runtimes,
        channels,
        retention_days,
        nodes,
    ) = ent._normalise_all_bundle(bundle)
    kwargs_path = ent.has_all_at_path(
        "oss",
        "enterprise",
        features=features or None,
        runtimes=runtimes or None,
        channels=channels,
        retention_days=retention_days,
        nodes=nodes,
    )
    assert [r["tier"] for r in cell["path"]] == [
        r["tier"] for r in kwargs_path
    ]
    for cell_row, kwargs_row in zip(cell["path"], kwargs_path):
        assert cell_row["has_all_at"] == kwargs_row["has_all_at"]


def test_has_scalar_cell_index_matches_input_position(ent):
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {},
    ]
    batch = ent.has_all_bundle_batch_at_path("oss", "enterprise", bundles)
    for i, cell in enumerate(batch):
        assert cell["bundle_index"] == i


# ── Scalar: complement invariant per cell per rung ─────────────────────────


def test_complement_invariant_per_cell_per_rung(ent):
    """any(row['missing'].values()) == not paired_row['has_all_at']
    for every fully-parseable bundle in the batch. (Empty bundles are
    the one deliberate divergence, matching the singular
    :func:`missing_all_bundle_at_path` docstring.)
    """
    bundles = [
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 500,
            "retention_days": 365,
            "nodes": 99,
        },
        {"features": ["sso"], "channels": 5},
    ]
    has_batch = ent.has_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    miss_batch = ent.missing_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    assert len(has_batch) == len(miss_batch)
    for has_cell, miss_cell in zip(has_batch, miss_batch):
        assert has_cell["bundle_index"] == miss_cell["bundle_index"]
        assert len(has_cell["path"]) == len(miss_cell["path"])
        for has_row, miss_row in zip(has_cell["path"], miss_cell["path"]):
            assert has_row["tier"] == miss_row["tier"]
            any_missing = any(
                v
                for v in miss_row["missing"].values()
                if v not in (None, [])
            )
            assert bool(any_missing) == (not has_row["has_all_at"]), (
                has_cell["bundle_index"],
                has_row["tier"],
                has_row["has_all_at"],
                miss_row["missing"],
            )


# ── Scalar: grace-independence ─────────────────────────────────────────────


def test_has_scalar_grace_independent(ent, enforced, tmp_path):
    """Same answer under grace-on vs enforce for the same
    (from, to, bundles) triple.
    """
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"], "channels": 5},
    ]
    grace = ent.has_all_bundle_batch_at_path("oss", "enterprise", bundles)
    enforce = enforced.has_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    assert grace == enforce


def test_missing_scalar_grace_independent(ent, enforced, tmp_path):
    bundles = [
        {"features": ["fleet"], "channels": 500},
        {"runtimes": ["claude_code"]},
    ]
    grace = ent.missing_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    enforce = enforced.missing_all_bundle_batch_at_path(
        "oss", "enterprise", bundles
    )
    assert grace == enforce


# ── Scalar: bundle normalisation ───────────────────────────────────────────


def test_has_scalar_runtime_alias_canonicalisation(ent):
    """A claude-code (dash) alias resolves to claude_code (underscore)
    on the axis echo.
    """
    batch = ent.has_all_bundle_batch_at_path(
        "oss", "enterprise", [{"runtimes": ["claude-code"]}]
    )
    cell = batch[0]
    assert cell["runtimes"] == ["claude_code"]


def test_has_scalar_unknown_runtime_collapses_has_all_at_false(ent):
    """Unknown runtime tokens survive :func:`_normalise_all_bundle` in
    canonical form and flow through the echo; the fold collapses every
    rung's ``has_all_at`` to ``False`` via the singular scalar's typo
    posture (byte-parity with the singular
    :func:`has_all_bundle_at_path`).
    """
    batch = ent.has_all_bundle_batch_at_path(
        "oss", "enterprise", [{"runtimes": ["not_a_real_runtime"]}]
    )
    cell = batch[0]
    # Byte-parity with the singular scalar: token flows through the echo
    # in canonical (lowercased) form and every rung reports has_all_at=False.
    singular = ent.has_all_bundle_at_path(
        "oss", "enterprise", {"runtimes": ["not_a_real_runtime"]}
    )
    assert cell["path"] == singular
    for row in cell["path"]:
        assert row["has_all_at"] is False


def test_has_scalar_non_dict_bundle_collapses_to_empty_echo(ent):
    """Non-dict bundle entries in the list surface as empty-echo cells."""
    batch = ent.has_all_bundle_batch_at_path(
        "oss", "enterprise", [None, 42, "nope", []]
    )
    assert len(batch) == 4
    for cell in batch:
        assert cell["features"] == []
        assert cell["runtimes"] == []
        assert cell["channels"] is None
        assert cell["retention_days"] is None
        assert cell["nodes"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_has_endpoint_envelope_shape_happy_path(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["from"] == "oss"
    assert d["to"] == "enterprise"
    assert d["direction"] == "upgrade"
    assert d["count"] == 1
    for cell in d["bundles"]:
        assert set(cell.keys()) == _HAS_CELL_KEYS
        for row in cell["path"]:
            assert set(row.keys()) == _HAS_ROW_KEYS


def test_missing_endpoint_envelope_shape_happy_path(client):
    d = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": [{"features": ["fleet"], "channels": 500}]},
    )
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["direction"] == "upgrade"
    for cell in d["bundles"]:
        assert set(cell.keys()) == _MISSING_CELL_KEYS
        for row in cell["path"]:
            assert set(row.keys()) == _MISSING_ROW_KEYS


def test_has_endpoint_envelope_shape_unknown_endpoint(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=bogus&to=cloud_pro",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["direction"] == "unknown"
    assert d["bundles"] == []
    assert d["count"] == 0


def test_missing_endpoint_envelope_shape_unknown_endpoint(client):
    d = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=bogus",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["direction"] == "unknown"
    assert d["bundles"] == []
    assert d["count"] == 0


def test_has_endpoint_envelope_shape_missing_from_to(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert set(d.keys()) == _ENVELOPE_KEYS
    assert d["direction"] == "unknown"
    assert d["bundles"] == []
    assert d["count"] == 0


def test_has_endpoint_identity_direction(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=cloud_pro&to=cloud_pro",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert d["direction"] == "identity"
    assert d["count"] == 1
    assert d["bundles"][0]["path"] == []
    assert d["bundles"][0]["path_length"] == 0


def test_has_endpoint_downgrade_direction(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=enterprise&to=oss",
        {"bundles": [{"features": ["fleet"]}]},
    )
    assert d["direction"] == "downgrade"


# ── Endpoint 400 branches ──────────────────────────────────────────────────


def test_has_endpoint_400_on_missing_bundles(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        json={},
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing bundles"}


def test_missing_endpoint_400_on_missing_bundles(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=enterprise",
        json={},
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing bundles"}


def test_has_endpoint_400_on_empty_bundles(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        json={"bundles": []},
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "empty bundles"}


def test_has_endpoint_400_on_non_list_non_dict_bundles(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        json={"bundles": "nope"},
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "bundles must be a list"}


# ── Endpoint bare-dict shorthand ───────────────────────────────────────────


def test_has_endpoint_bare_dict_bundle_shorthand(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": {"features": ["fleet"]}},
    )
    assert d["count"] == 1
    assert d["bundles"][0]["bundle_index"] == 0
    assert d["bundles"][0]["features"] == ["fleet"]


def test_missing_endpoint_bare_dict_bundle_shorthand(client):
    d = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": {"features": ["fleet"]}},
    )
    assert d["count"] == 1
    assert d["bundles"][0]["bundle_index"] == 0


# ── Endpoint per-cell parity with singular ─────────────────────────────────


def test_has_endpoint_per_cell_parity_with_singular_endpoint(client):
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"], "channels": 5},
    ]
    batch = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": bundles},
    )
    for cell in batch["bundles"]:
        singular = _post_json(
            client,
            "/api/entitlement/has-all-bundle-at-path?from=oss&to=enterprise",
            {"bundle": bundles[cell["bundle_index"]]},
        )
        assert len(cell["path"]) == len(singular["path"])
        for cell_row, single_row in zip(cell["path"], singular["path"]):
            assert cell_row["tier"] == single_row["tier"]
            assert cell_row["has_all_at"] == single_row["has_all_at"]


def test_missing_endpoint_per_cell_parity_with_singular_endpoint(client):
    bundles = [
        {"features": ["fleet"], "channels": 500},
        {"runtimes": ["claude_code"], "nodes": 99},
    ]
    batch = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": bundles},
    )
    for cell in batch["bundles"]:
        singular = _post_json(
            client,
            "/api/entitlement/missing-all-bundle-at-path?from=oss&to=enterprise",
            {"bundle": bundles[cell["bundle_index"]]},
        )
        assert len(cell["path"]) == len(singular["path"])
        for cell_row, single_row in zip(cell["path"], singular["path"]):
            assert cell_row["tier"] == single_row["tier"]
            assert cell_row["missing"] == single_row["missing"]


# ── Endpoint per-cell rollups ──────────────────────────────────────────────


def test_has_endpoint_per_cell_rollups(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        {
            "bundles": [
                {"features": ["fleet"]},
                {},  # empty bundle -> has_all_at=False at every rung
            ]
        },
    )
    for cell in d["bundles"]:
        assert cell["allowed_count"] == sum(
            1 for r in cell["path"] if r["has_all_at"]
        )
        assert cell["all_allowed"] == (
            bool(cell["path"])
            and all(r["has_all_at"] for r in cell["path"])
        )
        assert cell["any_allowed"] == any(
            r["has_all_at"] for r in cell["path"]
        )


def test_missing_endpoint_per_cell_rollups(client):
    d = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-batch-at-path?from=oss&to=enterprise",
        {
            "bundles": [
                {"features": ["fleet"], "channels": 500},
                {},
            ]
        },
    )
    for cell in d["bundles"]:
        expected_denied = sum(
            1
            for r in cell["path"]
            if any(
                v for v in r["missing"].values() if v not in (None, [])
            )
        )
        assert cell["denied_count"] == expected_denied
        assert cell["all_denied"] == (
            bool(cell["path"])
            and all(
                any(
                    v
                    for v in r["missing"].values()
                    if v not in (None, [])
                )
                for r in cell["path"]
            )
        )
        assert cell["any_denied"] == any(
            any(v for v in r["missing"].values() if v not in (None, []))
            for r in cell["path"]
        )


# ── Endpoint runtime alias canonicalisation ────────────────────────────────


def test_has_endpoint_runtime_alias_canonicalisation(client):
    d = _post_json(
        client,
        "/api/entitlement/has-all-bundle-batch-at-path?from=oss&to=enterprise",
        {"bundles": [{"runtimes": ["claude-code"]}]},
    )
    assert d["bundles"][0]["runtimes"] == ["claude_code"]
