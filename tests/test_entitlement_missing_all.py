"""Tests for the mixed-axis ``missing_all(...)`` row-detail complement scalar
and its paired ``/api/entitlement/missing-all`` endpoint.

Row-detail rollup twin of :func:`clawmetry.entitlements.has_all` (which folds
the same mixed bundle to ONE boolean). Where ``has_all`` says "does the whole
bundle pass?", this scalar preserves the per-axis denial detail so a paywall
diagnostics tile ("you're missing fleet, sso, claude_code, +75 channels,
+60 days retention, +99 nodes -- upgrade to unlock") binds the exact denial
roster off ONE URL instead of walking the five singular ``missing_*`` /
capacity endpoints and stitching client-side.

This file pins:

1. Scalar shape / axis fold under grace vs enforce for every combination of
   the five axes (features / runtimes / channels / retention_days / nodes),
   including per-axis empty / ``None`` / unknown / non-int inputs.
2. Grace pass-through invariant: every fully-known bundle reports empty
   per-axis slots while ``ent.grace`` is on -- wiring this into a
   diagnostics tile today surfaces NOTHING.
3. Symmetry with :func:`has_all` at row level: ``any_missing`` is always
   the strict negation of ``has_all`` on the same fully-parseable bundle
   (typo posture aside, which is documented separately below).
4. Endpoint envelope shape parity (fixed 19-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
5. Never-4xx / never-5xx guarantees on the endpoint.
6. Scalar-vs-endpoint parity: the URL per-axis missing values equal the
   module-level scalar byte-for-byte on the same (parseable) input.
7. Cross-consistency with the singular ``/missing-features`` /
   ``/missing-runtimes`` endpoints: the aggregate per-axis list equals the
   single-axis list byte-for-byte for every parametric input.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture."""
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


# -- Envelope shape ------------------------------------------------------------

_MISSING_ALL_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
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

_SCALAR_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# -- Scalar: shape -------------------------------------------------------------


def test_scalar_no_axes_supplied_shape(ent):
    """Nothing supplied returns every axis at its empty seat."""
    out = ent.missing_all()
    assert set(out.keys()) == _SCALAR_KEYS
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_scalar_key_set_stable_on_every_axis_combo(ent):
    """The 5-key set is byte-stable regardless of which axes are supplied."""
    combos = [
        {},
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 2},
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    ]
    for kwargs in combos:
        out = ent.missing_all(**kwargs)
        assert set(out.keys()) == _SCALAR_KEYS, kwargs


# -- Scalar: grace pass-through ------------------------------------------------


def test_scalar_grace_free_bundle_is_empty(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    out = ent.missing_all(
        features=[free_f],
        runtimes=[free_r],
        channels=1,
        retention_days=1,
        nodes=1,
    )
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_scalar_grace_paid_bundle_is_empty(ent):
    """While grace is on, even a paid bundle reports empty per-axis slots
    -- matches the ``has_all=True`` grace answer on the same bundle."""
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    out = ent.missing_all(
        features=[paid_f],
        runtimes=[paid_r],
        channels=5,
        retention_days=30,
        nodes=2,
    )
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None
    assert ent.has_all(
        features=[paid_f],
        runtimes=[paid_r],
        channels=5,
        retention_days=30,
        nodes=2,
    ) is True


# -- Scalar: post-enforcement --------------------------------------------------


def test_scalar_enforced_free_bundle_still_empty(enforced):
    free_f = next(iter(enforced.FREE_FEATURES))
    free_r = next(iter(enforced.FREE_RUNTIMES))
    out = enforced.missing_all(
        features=[free_f],
        runtimes=[free_r],
        channels=1,
        retention_days=1,
        nodes=1,
    )
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_scalar_enforced_paid_features_surfaces_denial(enforced):
    paid = sorted(enforced.PAID_FEATURES)
    assert paid, "test presumes at least one paid feature exists"
    out = enforced.missing_all(features=paid)
    assert out["features"] == paid


def test_scalar_enforced_paid_runtimes_surfaces_denial(enforced):
    paid = sorted(enforced.PAID_RUNTIMES)
    assert paid
    out = enforced.missing_all(runtimes=paid)
    assert out["runtimes"] == paid


def test_scalar_enforced_big_channels_surfaces_requested(enforced):
    out = enforced.missing_all(channels=9999)
    assert out["channels"] == 9999


def test_scalar_enforced_big_retention_surfaces_requested(enforced):
    out = enforced.missing_all(retention_days=9999)
    assert out["retention_days"] == 9999


def test_scalar_enforced_big_nodes_surfaces_requested(enforced):
    out = enforced.missing_all(nodes=999)
    assert out["nodes"] == 999


# -- Scalar: unknown / typo'd inputs -------------------------------------------


def test_scalar_unknown_feature_appears_in_missing(ent):
    """Unknown feature ids surface INSIDE the per-axis missing list, in
    canonicalised (strip/lower) form, matching :func:`missing_features`."""
    out = ent.missing_all(features=["fleet", "totally_fake_xyz"])
    assert "totally_fake_xyz" in out["features"]


def test_scalar_unknown_runtime_appears_in_missing(ent):
    out = ent.missing_all(runtimes=["openclaw", "totally_fake_rt"])
    assert "totally_fake_rt" in out["runtimes"]


# -- Scalar: non-int capacity swallows silently --------------------------------


def test_scalar_non_int_channels_is_none(ent):
    """Non-int capacity collapses that axis slot to ``None`` -- the paired
    ``has_all`` reports ``False`` via the strict singular scalar so the
    denial IS coherently surfaced through the paired call."""
    out = ent.missing_all(channels="five")  # type: ignore[arg-type]
    assert out["channels"] is None
    assert ent.has_all(channels="five") is False  # type: ignore[arg-type]


def test_scalar_non_int_nodes_is_none(ent):
    out = ent.missing_all(nodes="two")  # type: ignore[arg-type]
    assert out["nodes"] is None


def test_scalar_non_int_retention_is_none(ent):
    out = ent.missing_all(retention_days="seven")  # type: ignore[arg-type]
    assert out["retention_days"] is None


# -- Scalar: retention_days=None means unsupplied, NOT unlimited ---------------


def test_scalar_retention_none_is_unsupplied(ent):
    out = ent.missing_all(channels=1, retention_days=None)
    assert out["retention_days"] is None
    assert out["channels"] is None  # grace


# -- Scalar: unsupplied axis stays at empty seat ------------------------------


def test_scalar_unsupplied_axis_is_empty_seat(ent):
    """Every unsupplied axis stays at its empty seat regardless of what
    other axes are populated."""
    out = ent.missing_all(features=["fleet"])
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# -- Scalar: never raises ------------------------------------------------------


def test_scalar_never_raises_on_features_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "missing_features", _boom)
    out = ent.missing_all(features=["fleet"])
    assert out["features"] == []


def test_scalar_never_raises_on_runtimes_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "missing_runtimes", _boom)
    out = ent.missing_all(runtimes=["claude_code"])
    assert out["runtimes"] == []


def test_scalar_never_raises_on_capacity_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "has_channel_count", _boom)
    out = ent.missing_all(channels=1)
    assert out["channels"] is None


# -- Symmetry with has_all -----------------------------------------------------


def test_symmetry_grace_free_bundle(ent):
    """``has_all`` and ``missing_all`` agree on every fully-known bundle."""
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    kwargs = dict(
        features=[free_f],
        runtimes=[free_r],
        channels=1,
        retention_days=1,
        nodes=1,
    )
    ha = ent.has_all(**kwargs)
    ma = ent.missing_all(**kwargs)
    any_missing = (
        bool(ma["features"])
        or bool(ma["runtimes"])
        or ma["channels"] is not None
        or ma["retention_days"] is not None
        or ma["nodes"] is not None
    )
    assert ha is (not any_missing)


def test_symmetry_enforce_paid_bundle(enforced):
    paid_f = next(iter(enforced.PAID_FEATURES))
    paid_r = next(iter(enforced.PAID_RUNTIMES))
    kwargs = dict(
        features=[paid_f],
        runtimes=[paid_r],
        channels=999,
        retention_days=999,
        nodes=999,
    )
    ha = enforced.has_all(**kwargs)
    ma = enforced.missing_all(**kwargs)
    any_missing = (
        bool(ma["features"])
        or bool(ma["runtimes"])
        or ma["channels"] is not None
        or ma["retention_days"] is not None
        or ma["nodes"] is not None
    )
    assert ha is (not any_missing)


# -- Endpoint: envelope shape --------------------------------------------------


def test_endpoint_no_params_shape(client):
    body = _get_json(client, "/api/entitlement/missing-all")
    assert set(body.keys()) == _MISSING_ALL_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["unknown_features"] == []
    assert body["unknown_runtimes"] == []
    assert body["supplied_axes"] == []
    assert body["supplied_count"] == 0
    assert body["missing_count"] == 0
    assert body["any_missing"] is False


def test_endpoint_all_free_axes_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all?"
        "features=nemo_governance&runtimes=openclaw"
        "&channels=1&retention_days=1&nodes=1",
    )
    assert set(body.keys()) == _MISSING_ALL_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["missing_count"] == 0
    assert body["any_missing"] is False
    assert body["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]
    assert body["supplied_count"] == 5
    assert body["required_tier"] == "oss"
    assert body["upgrade_required"] is False


def test_endpoint_paid_bundle_grace_shape(client):
    """Grace: paid bundle reports empty missing slots even though
    ``required_tier`` still resolves to a paid tier."""
    body = _get_json(
        client,
        "/api/entitlement/missing-all?features=fleet&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=2",
    )
    assert set(body.keys()) == _MISSING_ALL_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["missing_count"] == 0
    assert body["any_missing"] is False
    assert body["required_tier"] is not None
    assert body["required_tier"] != "oss"
    assert body["upgrade_required"] is True


def test_endpoint_features_only_shape(client):
    body = _get_json(client, "/api/entitlement/missing-all?features=fleet")
    assert body["supplied_axes"] == ["features"]
    assert body["supplied_count"] == 1
    assert body["features"] == []  # grace


def test_endpoint_runtimes_only_shape(client):
    body = _get_json(
        client, "/api/entitlement/missing-all?runtimes=claude_code"
    )
    assert body["supplied_axes"] == ["runtimes"]
    assert body["runtimes"] == []  # grace


def test_endpoint_channels_only_shape(client):
    body = _get_json(client, "/api/entitlement/missing-all?channels=5")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None  # grace


# -- Endpoint: unknown tokens surface inside missing ---------------------------


def test_endpoint_unknown_feature_appears_in_missing(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all?features=fleet,totally_fake_xyz",
    )
    # unknown surfaces INSIDE the missing list (and still split into
    # ``unknown_features`` for a diagnostics tooltip)
    assert "totally_fake_xyz" in body["features"]
    assert body["unknown_features"] == ["totally_fake_xyz"]
    assert body["any_missing"] is True


def test_endpoint_unknown_runtime_appears_in_missing(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all?runtimes=openclaw,totally_fake_rt",
    )
    assert "totally_fake_rt" in body["runtimes"]
    assert body["unknown_runtimes"] == ["totally_fake_rt"]
    assert body["any_missing"] is True


def test_endpoint_runtime_alias_canonicalises(client):
    """Alias-and-canonical pair collapses to one row inside the missing
    list (matches ``/has-all`` and ``/missing-runtimes`` posture)."""
    body = _get_json(
        client,
        "/api/entitlement/missing-all?runtimes=claude-code,claude_code",
    )
    assert body["unknown_runtimes"] == []
    # grace: nothing missing
    assert body["runtimes"] == []


# -- Endpoint: capacity axes ---------------------------------------------------


def test_endpoint_non_int_channels_echoes_raw(client):
    """A supplied-but-unparseable capacity axis echoes the raw string in
    that slot so a UI can surface the typo."""
    body = _get_json(client, "/api/entitlement/missing-all?channels=five")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] == "five"
    assert body["any_missing"] is True


def test_endpoint_blank_channels_echoes_raw(client):
    body = _get_json(client, "/api/entitlement/missing-all?channels=")
    assert body["supplied_axes"] == ["channels"]
    # _parse_capacity_arg treats blank as present-but-unparseable, so we
    # echo the raw empty string here (matches the ``has_all=false``
    # answer the paired endpoint returns on the same input)
    assert body["channels"] == ""
    assert body["any_missing"] is True


def test_endpoint_zero_channels_reports_empty_missing(client):
    body = _get_json(client, "/api/entitlement/missing-all?channels=0")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None  # 0 admitted by free floor
    assert body["any_missing"] is False


# -- Endpoint: enforce mode ----------------------------------------------------


def test_endpoint_paid_bundle_denied_after_enforcement(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    c = app.test_client()

    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    body = _get_json(
        c,
        f"/api/entitlement/missing-all?"
        f"features={paid_f}&runtimes={paid_r}"
        f"&channels=999&retention_days=999&nodes=999",
    )
    assert body["features"] == [paid_f]
    assert body["runtimes"] == [paid_r]
    assert body["channels"] == 999
    assert body["retention_days"] == 999
    assert body["nodes"] == 999
    assert body["missing_count"] == 5
    assert body["any_missing"] is True
    assert body["grace"] is False
    assert body["enforced"] is True

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


# -- Endpoint: never 4xx / never 5xx ------------------------------------------


def test_endpoint_never_4xxs(client):
    """No supplied axes, blank axes, all-unknown -- always 200."""
    for url in (
        "/api/entitlement/missing-all",
        "/api/entitlement/missing-all?features=",
        "/api/entitlement/missing-all?features=,,,",
        "/api/entitlement/missing-all?features=only_bogus_xyz",
        "/api/entitlement/missing-all?channels=",
    ):
        resp = client.get(url)
        assert resp.status_code == 200, url
        assert set(resp.get_json().keys()) == _MISSING_ALL_KEYS, url


def test_endpoint_never_5xxs_on_body_blowup(monkeypatch, client):
    from routes import entitlement as _route

    def _boom():
        raise RuntimeError("body-builder blowup")

    monkeypatch.setattr(_route, "_missing_all_body", _boom)
    resp = client.get(
        "/api/entitlement/missing-all?features=fleet&channels=5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _MISSING_ALL_KEYS
    # fallback envelope: every slot at its empty seat
    assert body["features"] == []
    assert body["channels"] is None
    assert body["missing_count"] == 0
    assert body["any_missing"] is False


# -- Endpoint: scalar-vs-endpoint parity --------------------------------------


@pytest.mark.parametrize(
    "url,scalar_kwargs",
    [
        (
            "/api/entitlement/missing-all?features=fleet",
            {"features": ["fleet"]},
        ),
        (
            "/api/entitlement/missing-all?runtimes=claude_code",
            {"runtimes": ["claude_code"]},
        ),
        (
            "/api/entitlement/missing-all?channels=5",
            {"channels": 5},
        ),
        (
            "/api/entitlement/missing-all?retention_days=30",
            {"retention_days": 30},
        ),
        (
            "/api/entitlement/missing-all?nodes=2",
            {"nodes": 2},
        ),
        (
            "/api/entitlement/missing-all?features=fleet&runtimes=claude_code"
            "&channels=5&retention_days=30&nodes=2",
            {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            },
        ),
    ],
)
def test_endpoint_matches_scalar_per_axis(ent, client, url, scalar_kwargs):
    """URL missing values byte-equal the module scalar per axis on every
    parametric input."""
    body = _get_json(client, url)
    scalar = ent.missing_all(**scalar_kwargs)
    for axis in ("features", "runtimes"):
        assert body[axis] == scalar[axis], (url, axis)
    for axis in ("channels", "retention_days", "nodes"):
        assert body[axis] == scalar[axis], (url, axis)


# -- Endpoint: cross-consistency with singular /missing-* ---------------------


def test_endpoint_features_matches_missing_features_endpoint(client):
    """The aggregate ``features`` list equals the singular
    ``/api/entitlement/missing-features`` list byte-for-byte on the same
    input (grace or enforce)."""
    url_agg = "/api/entitlement/missing-all?features=fleet,totally_fake_xyz"
    url_sing = "/api/entitlement/missing-features?features=fleet,totally_fake_xyz"
    body_agg = _get_json(client, url_agg)
    body_sing = _get_json(client, url_sing)
    assert body_agg["features"] == body_sing["missing"]


def test_endpoint_runtimes_matches_missing_runtimes_endpoint(client):
    url_agg = "/api/entitlement/missing-all?runtimes=openclaw,totally_fake_rt"
    url_sing = "/api/entitlement/missing-runtimes?runtimes=openclaw,totally_fake_rt"
    body_agg = _get_json(client, url_agg)
    body_sing = _get_json(client, url_sing)
    assert body_agg["runtimes"] == body_sing["missing"]


# -- Endpoint: missing_count fold --------------------------------------------


def test_endpoint_missing_count_folds_across_axes(monkeypatch, tmp_path):
    """``missing_count`` = len(features) + len(runtimes) + 1 per denied
    capacity axis."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    c = app.test_client()

    paid_features = sorted(e.PAID_FEATURES)[:2]  # take two
    paid_runtimes = sorted(e.PAID_RUNTIMES)[:1]  # take one
    body = _get_json(
        c,
        f"/api/entitlement/missing-all?"
        f"features={','.join(paid_features)}"
        f"&runtimes={','.join(paid_runtimes)}"
        f"&channels=999",
    )
    expected = len(paid_features) + len(paid_runtimes) + 1  # channels denied
    assert body["missing_count"] == expected
    assert body["any_missing"] is True

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


# -- Endpoint: resolver envelope stability -------------------------------------


def test_endpoint_resolver_envelope_stable(client):
    """The 6 resolver-envelope slots stay stable across every input branch."""
    for url in (
        "/api/entitlement/missing-all",
        "/api/entitlement/missing-all?features=fleet",
        "/api/entitlement/missing-all?features=,,,",
        "/api/entitlement/missing-all?channels=five",
    ):
        body = _get_json(client, url)
        assert body["current_tier"] == "oss"
        assert body["current_tier_rank"] == 0
        assert body["grace"] is True
        assert body["enforced"] is False
