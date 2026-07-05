"""Tests for ``clawmetry.entitlements.min_tier_batch`` and the
``GET /api/entitlement/min-tier-batch`` endpoint.

Per-item plural sibling of :func:`min_tier_for_feature` /
:func:`min_tier_for_runtime` / :func:`min_tier_for_channel_count` /
:func:`min_tier_for_retention_window` / :func:`min_tier_for_node_count`.
Where :func:`min_tier_for_all` / ``/api/entitlement/required-tier-batch``
collapse the answer to the single most-constraining tier, this surface
preserves the per-item detail so a pricing-matrix UI ("show me each
requested feature + runtime + capacity row with its individual cheapest
tier") renders off ONE round-trip instead of N calls to
``/api/entitlement/min-tier``.

These tests pin:

* full response shape (per-axis rows, envelope keys, row fields)
* per-row parity with the singular ``min_tier_for_*`` helpers across
  every feature id in :data:`ALL_FEATURES`, every runtime id in
  :data:`ALL_RUNTIMES`, and the three capacity axes
* runtime canonicalisation (``claude-code`` -> ``claude_code``)
* dedup after canonicalisation
* unknown ids contribute an all-``None`` row (rather than raising)
* ``retention_days=None`` means unset, NOT unlimited
* grace vs enforce yields byte-identical rows (helper is decoupled
  from the resolver)
* never-raises contract
* API: 400 on no axis supplied, 200 with the batch shape + resolver
  envelope on happy path
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
}


# ── min_tier_batch -- shape ─────────────────────────────────────────────────


def test_helper_returns_envelope_with_five_axes(ent):
    out = ent.min_tier_batch(
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
    out = ent.min_tier_batch(features=["fleet"])
    row = out["features"][0]
    assert set(row.keys()) == _EXPECTED_ROW_KEYS
    assert row["kind"] == "feature"


def test_helper_no_inputs_returns_empty_shape(ent):
    out = ent.min_tier_batch()
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# ── min_tier_batch -- per-row parity with singular helpers ─────────────────


def test_feature_rows_match_singular_helper(ent):
    """Every feature id in ALL_FEATURES must have a batch row whose
    min_tier is byte-identical to :func:`min_tier_for_feature`."""
    for fid in sorted(ent.ALL_FEATURES):
        out = ent.min_tier_batch(features=[fid])
        assert len(out["features"]) == 1
        row = out["features"][0]
        assert row["key"] == fid
        assert row["min_tier"] == ent.min_tier_for_feature(fid)
        assert row["free"] is (row["min_tier"] == ent.TIER_OSS)
        if row["min_tier"]:
            assert row["min_tier_label"] == ent.tier_label(row["min_tier"])
            assert row["min_tier_rank"] == ent.tier_rank(row["min_tier"])
        else:
            assert row["min_tier_label"] is None
            assert row["min_tier_rank"] == -1


def test_runtime_rows_match_singular_helper(ent):
    for rt in sorted(ent.ALL_RUNTIMES):
        out = ent.min_tier_batch(runtimes=[rt])
        assert len(out["runtimes"]) == 1
        row = out["runtimes"][0]
        assert row["key"] == rt
        assert row["min_tier"] == ent.min_tier_for_runtime(rt)
        assert row["free"] is (row["min_tier"] == ent.TIER_OSS)


def test_channels_row_matches_singular_helper(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.min_tier_batch(channels=n)
        assert out["channels"]["min_tier"] == ent.min_tier_for_channel_count(n)
        assert out["channels"]["key"] == str(n)
        assert out["channels"]["kind"] == "channels"


def test_retention_row_matches_singular_helper(ent):
    for days in (0, 1, 7, 30, 90, 365, 3650):
        out = ent.min_tier_batch(retention_days=days)
        assert out["retention_days"]["min_tier"] == (
            ent.min_tier_for_retention_window(days)
        )
        assert out["retention_days"]["key"] == str(days)


def test_nodes_row_matches_singular_helper(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.min_tier_batch(nodes=n)
        assert out["nodes"]["min_tier"] == ent.min_tier_for_node_count(n)
        assert out["nodes"]["key"] == str(n)


# ── min_tier_batch -- runtime canonicalisation + dedup ─────────────────────


def test_runtime_alias_canonicalises(ent):
    out = ent.min_tier_batch(runtimes=["claude-code"])
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"
    assert out["runtimes"][0]["min_tier"] == ent.min_tier_for_runtime(
        "claude_code"
    )


def test_runtime_alias_dedups_against_canonical(ent):
    out = ent.min_tier_batch(runtimes=["claude-code", "claude_code"])
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


# ── min_tier_batch -- unknown ids ──────────────────────────────────────────


def test_unknown_feature_returns_all_none_row(ent):
    out = ent.min_tier_batch(features=["definitely_not_a_feature"])
    assert len(out["features"]) == 1
    row = out["features"][0]
    assert row["key"] == "definitely_not_a_feature"
    assert row["min_tier"] is None
    assert row["free"] is False
    assert row["min_tier_label"] is None
    assert row["min_tier_rank"] == -1


def test_unknown_runtime_returns_all_none_row(ent):
    out = ent.min_tier_batch(runtimes=["definitely_not_a_runtime"])
    assert len(out["runtimes"]) == 1
    row = out["runtimes"][0]
    assert row["min_tier"] is None
    assert row["free"] is False


def test_non_int_capacity_returns_all_none_row(ent):
    out = ent.min_tier_batch(channels="oops")
    assert out["channels"]["min_tier"] is None
    assert out["channels"]["free"] is False
    assert out["channels"]["min_tier_rank"] == -1


# ── min_tier_batch -- input normalisation ─────────────────────────────────


def test_features_are_lowercased_and_deduped(ent):
    out = ent.min_tier_batch(features=["FLEET", " fleet ", "sso", "fleet"])
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


def test_features_accepts_csv_string(ent):
    out = ent.min_tier_batch(features="fleet,sso")
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


# ── min_tier_batch -- unset vs unlimited ──────────────────────────────────


def test_retention_none_means_unset_not_unlimited(ent):
    """``retention_days=None`` here means axis-not-supplied, NOT the
    unlimited sentinel that would mis-route to Enterprise."""
    out = ent.min_tier_batch(retention_days=None)
    assert out["retention_days"] is None


def test_channels_none_means_unset(ent):
    out = ent.min_tier_batch(channels=None)
    assert out["channels"] is None


def test_nodes_none_means_unset(ent):
    out = ent.min_tier_batch(nodes=None)
    assert out["nodes"] is None


# ── min_tier_batch -- grace vs enforce parity ──────────────────────────────


def test_grace_vs_enforce_yields_byte_identical_rows(monkeypatch, tmp_path):
    """The helper walks the static per-tier maps via the singular
    ``min_tier_for_*`` helpers, so grace vs enforce yields byte-identical
    rows -- a pricing-page must render the same numbers on both sides of
    the enforcement cutover."""
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_out = e_grace.min_tier_batch(
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
    enf_out = e_enf.min_tier_batch(
        features=sorted(e_enf.ALL_FEATURES),
        runtimes=sorted(e_enf.ALL_RUNTIMES),
        channels=5,
        retention_days=30,
        nodes=3,
    )
    e_enf.invalidate()
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)

    assert grace_out == enf_out


# ── min_tier_batch -- never raises ─────────────────────────────────────────


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
        out = ent.min_tier_batch(
            features=features,
            runtimes=runtimes,
            channels=channels,
            retention_days=retention_days,
            nodes=nodes,
        )
    except Exception:  # pragma: no cover
        pytest.fail("min_tier_batch must not raise")
    assert set(out.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    }


# ── /api/entitlement/min-tier-batch ────────────────────────────────────────


def test_endpoint_400_on_no_axis(client):
    r = client.get("/api/entitlement/min-tier-batch")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_endpoint_happy_path_features(client):
    r = client.get(
        "/api/entitlement/min-tier-batch?features=fleet,sso"
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
        "/api/entitlement/min-tier-batch"
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
        "/api/entitlement/min-tier-batch?runtimes=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["runtimes"][0]["key"] == "claude_code"


def test_endpoint_unknown_id_does_not_500(client):
    r = client.get(
        "/api/entitlement/min-tier-batch"
        "?features=definitely_not_a_feature"
        "&runtimes=definitely_not_a_runtime"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"][0]["min_tier"] is None
    assert body["features"][0]["free"] is False
    assert body["runtimes"][0]["min_tier"] is None


def test_endpoint_non_int_capacity_treated_as_unsupplied(client):
    """Blank / non-int capacity args must be treated as "not supplied"
    (mirrors the singular endpoint's never-crash posture) rather than
    mis-routing a typo to Enterprise."""
    r = client.get(
        "/api/entitlement/min-tier-batch"
        "?features=fleet&channels=oops&retention_days=&nodes=oops"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_endpoint_per_row_parity_with_singular_min_tier(client, ent):
    """Each batch row's ``min_tier`` must byte-equal the singular
    ``/api/entitlement/min-tier?feature=<id>`` response for the same id.
    Pins the batch against the scalar so they can never silently
    drift."""
    for fid in sorted(ent.ALL_FEATURES):
        batch = client.get(
            f"/api/entitlement/min-tier-batch?features={fid}"
        ).get_json()
        singular = client.get(
            f"/api/entitlement/min-tier?feature={fid}"
        ).get_json()
        assert batch["features"][0]["min_tier"] == singular["min_tier"]
        assert batch["features"][0]["free"] == singular["free"]


def test_endpoint_carries_resolver_envelope(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-batch?features=fleet"
    )
    body = r.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
