"""Tests for the singular row-detail
``/api/entitlement/missing-all-bundle`` endpoint (plus the
:func:`clawmetry.entitlements.missing_all_bundle` helper).

Fills the singular-row slot for the aggregate 5-axis bundle row-detail
family alongside the batch ``/missing-all-bundle-batch`` so a paywall
walkthrough tile rendering one hypothetical whole-config cell at a time
reads the per-axis denial detail without wrapping in a length-one list
and unwrapping ``[0]`` from the batch.

Row-detail complement of ``/api/entitlement/has-all-bundle`` on the same
input shape: same POST body, same axis echoes, same never-crash posture.
The only per-row divergence is the fold slot -- this returns a per-axis
``missing`` dict where the boolean-fold sibling returns a single
``has_all`` bool.

These tests pin:

* helper: row shape byte-parity with :func:`missing_all_bundle_batch`
* helper: row shape byte-parity with :func:`has_all_bundle` on the axis
  echoes (only the fold slot diverges)
* helper: never-crash on ``None`` / non-dict / scalar bundle inputs
* helper: normalisation (feature/runtime CSV, runtime alias
  canonicalisation, capacity int coercion, blank / non-int axes collapse
  to ``None``)
* helper: grace pass-through (paid feature/runtime/capacity in grace ->
  empty ``missing`` shape)
* helper: post-enforce paid feature / runtime / capacity surfaces on the
  corresponding ``missing`` slot
* helper: :data:`FREE_RUNTIMES` (``openclaw``) reports
  ``missing.runtimes=[]`` regardless of rollout
* API happy path: 10-key envelope (6-key row + 4-key resolver), 200
* API error paths: 400 on missing / non-object ``bundle``
* API bare-dict shorthand (top-level body IS the bundle)
* API per-body byte-equals the batch's per-row body on the same bundle
* API row ``missing`` byte-equals the singular ``/missing-all`` endpoint
  on the same known bundle
* API cross-endpoint axis-echo parity with ``/has-all-bundle``
* API never-5xxs on a monkeypatched delegate crash
* API grace vs enforce fold divergence on a paid bundle
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ------------------------------------------------------------------


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
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` off so the grace pass-through collapses and paid
    axes report their post-enforce denial in ``missing``."""
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


# -- Row / envelope shape constants -------------------------------------------


_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "missing",
}

_MISSING_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}

_ENVELOPE_KEYS = _ROW_KEYS | {
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# -- helper: missing_all_bundle -----------------------------------------------


def test_helper_row_shape_across_all_five_axes(ent):
    row = ent.missing_all_bundle(
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        }
    )
    assert set(row.keys()) == _ROW_KEYS
    assert set(row["missing"].keys()) == _MISSING_KEYS
    assert row["features"] == ["fleet"]
    assert row["runtimes"] == ["claude_code"]
    assert row["channels"] == 5
    assert row["retention_days"] == 30
    assert row["nodes"] == 2
    # Grace pass-through: LIVE row reports empty missing shape while
    # ent.grace is on (every fully-known bundle is granted).
    assert row["missing"]["features"] == []
    assert row["missing"]["runtimes"] == []
    assert row["missing"]["channels"] is None
    assert row["missing"]["retention_days"] is None
    assert row["missing"]["nodes"] is None


def test_helper_row_byte_equals_batch_row(ent):
    """Row shape byte-parity contract: the singular row byte-equals
    the batch row for the same bundle, on every axis + fold slot."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    scalar_row = ent.missing_all_bundle(bundle)
    batch_row = ent.missing_all_bundle_batch([bundle])[0]
    assert scalar_row == batch_row


def test_helper_row_byte_equals_batch_row_across_representative_bundles(ent):
    """Row byte-parity holds across representative bundle shapes:
    empty, single-axis, mixed, paid-only, capacity-only."""
    bundles = [
        {},
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {"features": ["fleet", "sso"], "runtimes": ["claude_code", "codex"]},
        {"features": ["fleet"], "channels": 5, "nodes": 2},
    ]
    for bundle in bundles:
        assert ent.missing_all_bundle(bundle) == ent.missing_all_bundle_batch(
            [bundle]
        )[0], f"row drift for bundle={bundle!r}"


def test_helper_axis_echoes_byte_equal_has_all_bundle(ent):
    """The five axis-echo slots byte-equal the paired
    :func:`has_all_bundle` row -- only the fold slot diverges."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    missing_row = ent.missing_all_bundle(bundle)
    has_row = ent.has_all_bundle(bundle)
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert missing_row[axis] == has_row[axis], (
            f"axis-echo drift on {axis!r}: missing={missing_row[axis]!r}, "
            f"has={has_row[axis]!r}"
        )


def test_helper_missing_body_byte_equals_missing_all(ent):
    """The per-axis ``missing`` sub-dict byte-equals the singular
    :func:`missing_all` scalar's return on the same known bundle."""
    features = ["fleet"]
    runtimes = ["claude_code"]
    channels = 5
    retention = 30
    nodes = 2
    row = ent.missing_all_bundle(
        {
            "features": features,
            "runtimes": runtimes,
            "channels": channels,
            "retention_days": retention,
            "nodes": nodes,
        }
    )
    scalar = ent.missing_all(
        features=features,
        runtimes=runtimes,
        channels=channels,
        retention_days=retention,
        nodes=nodes,
    )
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert row["missing"][axis] == scalar[axis]


@pytest.mark.parametrize("bad", [None, [], "not a dict", 5, 3.14, True])
def test_helper_never_crashes_on_bad_bundle_input(ent, bad):
    """Empty / non-dict / scalar bundle input returns the stable empty
    row shape (matches the batch's never-crash posture)."""
    row = ent.missing_all_bundle(bad)
    assert set(row.keys()) == _ROW_KEYS
    assert set(row["missing"].keys()) == _MISSING_KEYS
    # Empty / non-dict bundle -> every echo axis is empty / None.
    assert row["features"] == []
    assert row["runtimes"] == []
    assert row["channels"] is None
    assert row["retention_days"] is None
    assert row["nodes"] is None
    # And every missing slot is empty (nothing supplied -> nothing missing).
    assert row["missing"]["features"] == []
    assert row["missing"]["runtimes"] == []
    assert row["missing"]["channels"] is None
    assert row["missing"]["retention_days"] is None
    assert row["missing"]["nodes"] is None


def test_helper_never_raises_on_delegate_crash(ent, monkeypatch):
    """A crash inside the row helper is swallowed and the stable empty
    row shape is returned -- cannot 500 a caller wiring the scalar into
    a gate."""
    def _boom(*_a, **_kw):
        raise RuntimeError("simulated row helper blowup")

    monkeypatch.setattr(ent, "_missing_all_bundle_row", _boom)
    row = ent.missing_all_bundle({"features": ["fleet"]})
    assert set(row.keys()) == _ROW_KEYS
    assert row["missing"] == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_helper_csv_normalises_features_and_runtimes(ent):
    """CSV normalisation matches the batch: whitespace stripped,
    lowercased, deduplicated preserving first-seen order."""
    row = ent.missing_all_bundle(
        {
            "features": "fleet, sso , FLEET",
            "runtimes": "claude_code, CLAUDE_CODE, codex",
        }
    )
    assert row["features"] == ["fleet", "sso"]
    assert row["runtimes"] == ["claude_code", "codex"]


def test_helper_alias_canonicalises_claude_code(ent):
    """``claude-code`` (dash) canonicalises to ``claude_code`` at the
    normalisation layer -- alias + canonical pair dedupes to ONE entry."""
    row = ent.missing_all_bundle({"runtimes": ["claude-code", "claude_code"]})
    assert row["runtimes"] == ["claude_code"]


@pytest.mark.parametrize("bad", ["", "abc", None])
def test_helper_blank_or_non_int_capacity_collapses_to_none(ent, bad):
    """A blank / non-int capacity on the bundle collapses to ``None`` on
    the axis echo AND drops from the ``missing`` dict entirely."""
    row = ent.missing_all_bundle({"channels": bad})
    assert row["channels"] is None
    assert row["missing"]["channels"] is None


def test_helper_openclaw_runtime_never_denied(ent):
    """:data:`FREE_RUNTIMES` (``openclaw``) is never in
    ``missing.runtimes`` regardless of rollout state."""
    row = ent.missing_all_bundle({"runtimes": ["openclaw"]})
    assert "openclaw" not in row["missing"]["runtimes"]


def test_helper_grace_pass_through_on_paid_bundle(ent):
    """Grace pass-through: paid feature + paid runtime + tight capacity
    all report empty ``missing`` while ``ent.grace`` is on."""
    row = ent.missing_all_bundle(
        {
            "features": ["fleet", "sso"],
            "runtimes": ["claude_code"],
            "channels": 100,
            "retention_days": 365,
            "nodes": 50,
        }
    )
    assert row["missing"]["features"] == []
    assert row["missing"]["runtimes"] == []
    assert row["missing"]["channels"] is None
    assert row["missing"]["retention_days"] is None
    assert row["missing"]["nodes"] is None


def test_helper_post_enforce_paid_feature_surfaces_in_missing(enforced):
    """Post-enforce (grace off) a paid feature on an OSS resolver
    surfaces on ``missing.features``."""
    row = enforced.missing_all_bundle({"features": ["fleet"]})
    assert "fleet" in row["missing"]["features"]


def test_helper_post_enforce_paid_runtime_surfaces_in_missing(enforced):
    """Post-enforce a paid runtime on an OSS resolver surfaces on
    ``missing.runtimes``."""
    row = enforced.missing_all_bundle({"runtimes": ["claude_code"]})
    assert "claude_code" in row["missing"]["runtimes"]


def test_helper_post_enforce_channel_over_cap_surfaces_in_missing(enforced):
    """Post-enforce a channel-count over the OSS cap surfaces on
    ``missing.channels`` as the requested int."""
    row = enforced.missing_all_bundle({"channels": 100})
    assert row["missing"]["channels"] == 100


# -- API: happy path ----------------------------------------------------------


def test_api_happy_path_envelope_shape(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle",
        json={
            "bundle": {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            }
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert set(body["missing"].keys()) == _MISSING_KEYS
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == ["claude_code"]
    assert body["channels"] == 5
    assert body["retention_days"] == 30
    assert body["nodes"] == 2
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_api_bare_dict_shorthand_accepted(client):
    """Bare-dict body (no ``bundle`` wrapper) is treated as the bundle
    -- matches the ``/has-all-bundle`` shorthand posture."""
    resp = client.post(
        "/api/entitlement/missing-all-bundle",
        json={
            "features": ["fleet"],
            "runtimes": ["claude_code"],
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == ["claude_code"]


def test_api_body_byte_equals_batch_row(client):
    """The singular endpoint's per-row body byte-equals the batch
    endpoint's row on the same bundle (with the resolver envelope keys
    stripped off)."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    scalar = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": bundle}
    ).get_json()
    batch = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    scalar_row = {k: scalar[k] for k in _ROW_KEYS}
    assert scalar_row == batch["bundles"][0]


def test_api_axis_echoes_byte_equal_has_all_bundle(client):
    """Endpoint axis echoes byte-equal the paired ``/has-all-bundle``
    endpoint -- only the fold slot diverges."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    missing = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": bundle}
    ).get_json()
    has = client.post(
        "/api/entitlement/has-all-bundle", json={"bundle": bundle}
    ).get_json()
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert missing[axis] == has[axis], f"axis-echo drift on {axis!r}"


def test_api_missing_body_byte_equals_missing_all_endpoint(client):
    """Row's ``missing`` sub-dict byte-equals the singular
    ``/missing-all`` endpoint on the same known bundle."""
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    scalar = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": bundle}
    ).get_json()
    query = (
        "/api/entitlement/missing-all?"
        "features=fleet&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=2"
    )
    singular = client.get(query).get_json()
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert scalar["missing"][axis] == singular[axis]


# -- API: error paths ---------------------------------------------------------


def test_api_missing_bundle_returns_400(client):
    resp = client.post("/api/entitlement/missing-all-bundle", json={})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing bundle"}


def test_api_null_bundle_returns_400(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": None}
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing bundle"}


@pytest.mark.parametrize("bad", [[], "not a dict", 5, 3.14, True])
def test_api_non_object_bundle_returns_400(client, bad):
    resp = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": bad}
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "bundle must be an object"}


def test_api_empty_bundle_is_valid_input(client):
    """An explicit empty ``bundle={}`` is valid: collapses to the
    stable empty row shape with an empty ``missing`` dict."""
    resp = client.post(
        "/api/entitlement/missing-all-bundle", json={"bundle": {}}
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["missing"]["features"] == []
    assert body["missing"]["runtimes"] == []
    assert body["missing"]["channels"] is None


# -- API: never-5xx contract --------------------------------------------------


def test_api_never_5xxs_on_delegate_crash(client, monkeypatch):
    """A resolver / helper failure yields the fallback envelope, not a
    500 -- paywall tile keeps rendering."""
    from clawmetry import entitlements as _ent

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated helper blowup")

    monkeypatch.setattr(_ent, "missing_all_bundle", _boom)
    resp = client.post(
        "/api/entitlement/missing-all-bundle",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["missing"] == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


# -- API: grace vs enforce ----------------------------------------------------


def test_api_grace_pass_through_on_paid_bundle(client):
    """LIVE endpoint: while grace is on, a paid bundle reports empty
    ``missing`` shape (matches sibling helper posture)."""
    resp = client.post(
        "/api/entitlement/missing-all-bundle",
        json={"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["grace"] is True
    assert body["missing"]["features"] == []
    assert body["missing"]["runtimes"] == []


def test_api_post_enforce_paid_bundle_surfaces_in_missing(enforced_client):
    """LIVE endpoint post-enforce: paid feature + paid runtime surface
    on the corresponding ``missing`` slots."""
    resp = enforced_client.post(
        "/api/entitlement/missing-all-bundle",
        json={"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["grace"] is False
    assert "fleet" in body["missing"]["features"]
    assert "claude_code" in body["missing"]["runtimes"]


def test_api_free_runtime_openclaw_never_denied_endpoint(client):
    """Endpoint parity with helper: ``openclaw`` never denied even on
    the LIVE OSS-in-grace resolver."""
    resp = client.post(
        "/api/entitlement/missing-all-bundle",
        json={"bundle": {"runtimes": ["openclaw"]}},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "openclaw" not in body["missing"]["runtimes"]
