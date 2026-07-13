"""Tests for ``clawmetry.entitlements.affordable_tiers_batch`` and the
``GET /api/entitlement/affordable-tiers-batch`` endpoint.

Per-item plural sibling of :func:`affordable_tiers`. Where
:func:`affordable_tiers` / ``/api/entitlement/affordable-tiers`` collapse
the answer to a single ordered list of qualifying tiers for a whole
constraint bundle, this surface preserves the per-item detail so a
pricing-matrix UI ("show me each requested feature + runtime + capacity
row with its individual cheapest tier -- and every tier above that also
qualifies") renders off ONE round-trip instead of N calls to
``/affordable-tiers``. Same relationship it has to
:func:`affordable_tiers` that :func:`min_tier_batch` has to
:func:`min_tier_for_all`.

These tests pin:

* full response shape (per-axis rows, envelope keys, row fields incl.
  ``tiers``)
* per-row parity with :func:`affordable_tiers` across every feature id
  in :data:`ALL_FEATURES`, every runtime id in :data:`ALL_RUNTIMES`,
  and the three capacity axes
* per-row ``min_tier`` parity with :func:`_min_tier_row` -- the batch
  ``_at`` slot / floor must byte-equal :func:`min_tier_batch` for the
  same inputs
* runtime canonicalisation (``claude-code`` -> ``claude_code``)
* dedup after canonicalisation
* unknown ids contribute an all-``None`` row with ``tiers=[]`` (rather
  than raising)
* ``retention_days=None`` means unset, NOT unlimited
* grace vs enforce yields byte-identical rows (helper is decoupled
  from the resolver)
* never-raises contract
* API: 400 on no axis supplied, 200 with the batch shape + resolver
  envelope on happy path
* API cross-parity with the singular ``/affordable-tiers`` endpoint
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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


_EXPECTED_ROW_KEYS = {
    "key",
    "kind",
    "free",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}

_EXPECTED_TIER_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "is_minimum",
}


# ── affordable_tiers_batch -- shape ─────────────────────────────────────────


def test_helper_returns_envelope_with_five_axes(ent):
    out = ent.affordable_tiers_batch(
        features=["fleet", "sso"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=3,
    )
    assert set(out.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    }
    assert isinstance(out["features"], list)
    assert isinstance(out["runtimes"], list)
    for axis in ("channels", "retention_days", "nodes"):
        assert isinstance(out[axis], dict)


def test_helper_row_shape(ent):
    out = ent.affordable_tiers_batch(features=["fleet"])
    row = out["features"][0]
    assert set(row.keys()) == _EXPECTED_ROW_KEYS
    assert row["kind"] == "feature"
    assert isinstance(row["tiers"], list)


def test_helper_tier_row_shape(ent):
    """Each tier entry in a row's ``tiers`` list must carry the same
    ``tier`` / ``tier_label`` / ``tier_rank`` / ``is_minimum`` keys that
    :func:`affordable_tiers` returns."""
    out = ent.affordable_tiers_batch(features=["fleet"])
    row = out["features"][0]
    if row["tiers"]:
        assert set(row["tiers"][0].keys()) == _EXPECTED_TIER_ROW_KEYS


def test_helper_no_inputs_returns_empty_shape(ent):
    out = ent.affordable_tiers_batch()
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# ── affordable_tiers_batch -- per-row parity with affordable_tiers ─────────


def test_feature_row_tiers_match_affordable_tiers(ent):
    """Every feature id in ALL_FEATURES must have a batch row whose
    ``tiers`` list byte-equals :func:`affordable_tiers` for the same
    single-feature bundle."""
    for fid in sorted(ent.ALL_FEATURES):
        out = ent.affordable_tiers_batch(features=[fid])
        assert len(out["features"]) == 1
        row = out["features"][0]
        assert row["key"] == fid
        expected = ent.affordable_tiers(features=[fid]) or []
        assert row["tiers"] == expected


def test_runtime_row_tiers_match_affordable_tiers(ent):
    for rt in sorted(ent.ALL_RUNTIMES):
        out = ent.affordable_tiers_batch(runtimes=[rt])
        assert len(out["runtimes"]) == 1
        row = out["runtimes"][0]
        assert row["key"] == rt
        expected = ent.affordable_tiers(runtimes=[rt]) or []
        assert row["tiers"] == expected


def test_channels_row_tiers_match_affordable_tiers(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.affordable_tiers_batch(channels=n)
        expected = ent.affordable_tiers(channels=n) or []
        assert out["channels"]["tiers"] == expected
        assert out["channels"]["key"] == str(n)
        assert out["channels"]["kind"] == "channels"


def test_retention_row_tiers_match_affordable_tiers(ent):
    for days in (0, 1, 7, 30, 90, 365, 3650):
        out = ent.affordable_tiers_batch(retention_days=days)
        expected = ent.affordable_tiers(retention_days=days) or []
        assert out["retention_days"]["tiers"] == expected
        assert out["retention_days"]["key"] == str(days)


def test_nodes_row_tiers_match_affordable_tiers(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.affordable_tiers_batch(nodes=n)
        expected = ent.affordable_tiers(nodes=n) or []
        assert out["nodes"]["tiers"] == expected
        assert out["nodes"]["key"] == str(n)


# ── affordable_tiers_batch -- floor parity with min_tier_batch ─────────────


def test_feature_row_min_tier_matches_min_tier_batch(ent):
    """The per-row floor scalar (``min_tier`` / ``free`` / label /
    rank) must byte-equal :func:`min_tier_batch` for the same input.
    Pins the two batches against each other so the aggregate view
    (batch min_tier + batch full-list) stays internally consistent."""
    for fid in sorted(ent.ALL_FEATURES):
        aff = ent.affordable_tiers_batch(features=[fid])["features"][0]
        mtb = ent.min_tier_batch(features=[fid])["features"][0]
        assert aff["min_tier"] == mtb["min_tier"]
        assert aff["free"] == mtb["free"]
        assert aff["min_tier_label"] == mtb["min_tier_label"]
        assert aff["min_tier_rank"] == mtb["min_tier_rank"]


def test_runtime_row_min_tier_matches_min_tier_batch(ent):
    for rt in sorted(ent.ALL_RUNTIMES):
        aff = ent.affordable_tiers_batch(runtimes=[rt])["runtimes"][0]
        mtb = ent.min_tier_batch(runtimes=[rt])["runtimes"][0]
        assert aff["min_tier"] == mtb["min_tier"]
        assert aff["free"] == mtb["free"]


def test_capacity_rows_min_tier_match_min_tier_batch(ent):
    for axis, values in (
        ("channels", (0, 1, 5, 25, 100)),
        ("retention_days", (0, 7, 30, 90, 365)),
        ("nodes", (0, 1, 5, 25, 100)),
    ):
        for n in values:
            aff = ent.affordable_tiers_batch(**{axis: n})[axis]
            mtb = ent.min_tier_batch(**{axis: n})[axis]
            assert aff["min_tier"] == mtb["min_tier"], (axis, n)
            assert aff["free"] == mtb["free"], (axis, n)


# ── affordable_tiers_batch -- runtime canonicalisation + dedup ─────────────


def test_runtime_alias_canonicalises(ent):
    out = ent.affordable_tiers_batch(runtimes=["claude-code"])
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"
    expected = ent.affordable_tiers(runtimes=["claude_code"]) or []
    assert out["runtimes"][0]["tiers"] == expected


def test_runtime_alias_dedups_against_canonical(ent):
    out = ent.affordable_tiers_batch(runtimes=["claude-code", "claude_code"])
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


# ── affordable_tiers_batch -- unknown ids ──────────────────────────────────


def test_unknown_feature_returns_all_none_row(ent):
    out = ent.affordable_tiers_batch(features=["definitely_not_a_feature"])
    assert len(out["features"]) == 1
    row = out["features"][0]
    assert row["key"] == "definitely_not_a_feature"
    assert row["min_tier"] is None
    assert row["free"] is False
    assert row["min_tier_label"] is None
    assert row["min_tier_rank"] == -1
    assert row["tiers"] == []


def test_unknown_runtime_returns_all_none_row(ent):
    out = ent.affordable_tiers_batch(runtimes=["definitely_not_a_runtime"])
    assert len(out["runtimes"]) == 1
    row = out["runtimes"][0]
    assert row["min_tier"] is None
    assert row["free"] is False
    assert row["tiers"] == []


def test_non_int_capacity_returns_all_none_row(ent):
    out = ent.affordable_tiers_batch(channels="oops")
    assert out["channels"]["min_tier"] is None
    assert out["channels"]["free"] is False
    assert out["channels"]["min_tier_rank"] == -1
    assert out["channels"]["tiers"] == []


# ── affordable_tiers_batch -- input normalisation ─────────────────────────


def test_features_are_lowercased_and_deduped(ent):
    out = ent.affordable_tiers_batch(features=["FLEET", " fleet ", "sso", "fleet"])
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


def test_features_accepts_csv_string(ent):
    out = ent.affordable_tiers_batch(features="fleet,sso")
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


# ── affordable_tiers_batch -- unset vs unlimited ──────────────────────────


def test_retention_none_means_unset_not_unlimited(ent):
    out = ent.affordable_tiers_batch(retention_days=None)
    assert out["retention_days"] is None


def test_channels_none_means_unset(ent):
    out = ent.affordable_tiers_batch(channels=None)
    assert out["channels"] is None


def test_nodes_none_means_unset(ent):
    out = ent.affordable_tiers_batch(nodes=None)
    assert out["nodes"] is None


# ── affordable_tiers_batch -- grace vs enforce parity ──────────────────────


def test_grace_vs_enforce_yields_byte_identical_rows(monkeypatch, tmp_path):
    """The helper walks the static per-tier maps via
    :func:`affordable_tiers`, so grace vs enforce yields byte-identical
    rows -- a pricing-page must render the same numbers on both sides of
    the enforcement cutover."""
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_out = e_grace.affordable_tiers_batch(
        features=sorted(e_grace.ALL_FEATURES),
        runtimes=sorted(e_grace.ALL_RUNTIMES),
        channels=5,
        retention_days=30,
        nodes=3,
    )
    e_grace.invalidate()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e_enf

    importlib.reload(e_enf)
    e_enf.invalidate()
    enf_out = e_enf.affordable_tiers_batch(
        features=sorted(e_enf.ALL_FEATURES),
        runtimes=sorted(e_enf.ALL_RUNTIMES),
        channels=5,
        retention_days=30,
        nodes=3,
    )
    e_enf.invalidate()
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)

    assert grace_out == enf_out


# ── affordable_tiers_batch -- never raises ─────────────────────────────────


@pytest.mark.parametrize(
    "features,runtimes,channels,retention_days,nodes",
    [
        (None, None, None, None, None),
        ([], [], None, None, None),
        ([""], [""], None, None, None),
        (["fleet", None, ""], ["claude_code"], "oops", "oops", "oops"),
        (["FLEET"], ["CLAUDE-CODE"], -1, -1, -1),
        (object(), object(), None, None, None),
        ("fleet,sso", "claude_code,codex", 5, 30, 3),
    ],
)
def test_helper_never_raises(ent, features, runtimes, channels, retention_days, nodes):
    try:
        out = ent.affordable_tiers_batch(
            features=features,
            runtimes=runtimes,
            channels=channels,
            retention_days=retention_days,
            nodes=nodes,
        )
    except Exception:  # pragma: no cover
        pytest.fail("affordable_tiers_batch must not raise")
    assert set(out.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    }


# ── /api/entitlement/affordable-tiers-batch ────────────────────────────────


def test_endpoint_400_on_no_axis(client):
    r = client.get("/api/entitlement/affordable-tiers-batch")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_endpoint_happy_path_features(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch?features=fleet,sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert [r["key"] for r in body["features"]] == ["fleet", "sso"]
    assert body["runtimes"] == []
    assert body["channels"] is None


def test_endpoint_happy_path_all_axes(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch"
        "?features=fleet"
        "&runtimes=claude_code"
        "&channels=5"
        "&retention_days=30"
        "&nodes=3"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"][0]["key"] == "fleet"
    assert body["runtimes"][0]["key"] == "claude_code"
    assert body["channels"]["key"] == "5"
    assert body["retention_days"]["key"] == "30"
    assert body["nodes"]["key"] == "3"


def test_endpoint_runtime_alias_canonicalises(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch?runtimes=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["runtimes"][0]["key"] == "claude_code"


def test_endpoint_unknown_id_does_not_500(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch"
        "?features=definitely_not_a_feature"
        "&runtimes=definitely_not_a_runtime"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"][0]["min_tier"] is None
    assert body["features"][0]["free"] is False
    assert body["features"][0]["tiers"] == []
    assert body["runtimes"][0]["min_tier"] is None
    assert body["runtimes"][0]["tiers"] == []


def test_endpoint_non_int_capacity_treated_as_unsupplied(client):
    """Blank / non-int capacity args must be treated as "not supplied"
    (mirrors the singular endpoint's never-crash posture) rather than
    mis-routing a typo to Enterprise."""
    r = client.get(
        "/api/entitlement/affordable-tiers-batch"
        "?features=fleet&channels=oops&retention_days=&nodes=oops"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_endpoint_per_row_parity_with_singular_affordable_tiers(client, ent):
    """Each batch row's ``tiers`` list must byte-equal the singular
    ``/api/entitlement/affordable-tiers?features=<id>`` response's
    ``tiers`` (stripped to the same 4-key rows). Pins the batch against
    the scalar so they can never silently drift."""
    for fid in sorted(ent.ALL_FEATURES):
        batch = client.get(
            f"/api/entitlement/affordable-tiers-batch?features={fid}"
        ).get_json()
        singular = client.get(
            f"/api/entitlement/affordable-tiers?features={fid}"
        ).get_json()
        # The singular endpoint augments each tier row with ``is_current`` /
        # ``is_current_or_better`` -- strip them for the batch comparison.
        singular_stripped = [
            {
                "tier": r["tier"],
                "tier_label": r["tier_label"],
                "tier_rank": r["tier_rank"],
                "is_minimum": r["is_minimum"],
            }
            for r in singular["tiers"]
        ]
        assert batch["features"][0]["tiers"] == singular_stripped


def test_endpoint_carries_resolver_envelope(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch?features=fleet"
    )
    body = r.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


def test_endpoint_tiers_ordered_by_rank(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-batch?features=fleet"
    )
    body = r.get_json()
    tiers = body["features"][0]["tiers"]
    ranks = [t["tier_rank"] for t in tiers]
    assert ranks == sorted(ranks)


def test_endpoint_first_tier_is_minimum(client, ent):
    """Only the first (cheapest) row in a per-item ``tiers`` list has
    ``is_minimum=True``; every row above must have ``is_minimum=False``."""
    for fid in sorted(ent.ALL_FEATURES):
        r = client.get(
            f"/api/entitlement/affordable-tiers-batch?features={fid}"
        )
        tiers = r.get_json()["features"][0]["tiers"]
        if not tiers:
            continue
        assert tiers[0]["is_minimum"] is True
        for row in tiers[1:]:
            assert row["is_minimum"] is False
