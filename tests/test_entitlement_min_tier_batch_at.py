"""Tests for ``clawmetry.entitlements.min_tier_batch_at`` and the
``GET /api/entitlement/min-tier-batch-at`` endpoint.

Hypothetical-perspective sibling of :func:`min_tier_batch`: per-item
cheapest qualifying tier for every supplied item across all five
capacity axes, scoped by a caller-supplied ``perspective_tier``.
Same relationship to :func:`min_tier_batch` that :func:`min_tier_for_all_at`
has to :func:`min_tier_for_all` and :func:`affordable_tiers_at` has to
:func:`affordable_tiers` -- perspective is validated but does NOT shape
rows so a walkthrough surface can call ``X_at(perspective, ...)``
uniformly across every ``_at`` sibling.

These tests pin:

* perspective validation: empty / unknown short-circuits to ``None`` /
  400 / 404
* row shape and envelope keys (same five axes as :func:`min_tier_batch`
  plus the ``perspective_tier`` copy)
* parity with :func:`min_tier_batch` for every perspective in
  :data:`_TIER_ORDER` (including ``trial``) -- the ``_at`` prefix cannot
  silently drift into shaping rows
* per-row parity with the singular ``min_tier_for_*`` helpers across
  every feature id in :data:`ALL_FEATURES`, every runtime id in
  :data:`ALL_RUNTIMES`, and the three capacity axes
* runtime canonicalisation (``claude-code`` -> ``claude_code``)
* unknown ids contribute an all-``None`` row (rather than raising)
* ``retention_days=None`` means unset, NOT unlimited
* grace vs enforce yields byte-identical rows
* never-raises contract on the helper
* API: 400 on missing / blank ``tier=``, 400 on no axis, 404 on unknown
  ``tier=``, 200 with the batch shape + resolver envelope on happy path
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

_EXPECTED_ENVELOPE_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}


# ── helper: perspective validation ─────────────────────────────────────────


def test_helper_empty_perspective_returns_none(ent):
    assert ent.min_tier_batch_at("", features=["fleet"]) is None


def test_helper_blank_perspective_returns_none(ent):
    assert ent.min_tier_batch_at("   ", features=["fleet"]) is None


def test_helper_unknown_perspective_returns_none(ent):
    assert ent.min_tier_batch_at("bogus", features=["fleet"]) is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.min_tier_batch_at(None, features=["fleet"]) is None


def test_helper_non_string_perspective_returns_none(ent):
    assert ent.min_tier_batch_at(object(), features=["fleet"]) is None
    assert ent.min_tier_batch_at(123, features=["fleet"]) is None


def test_helper_perspective_is_case_insensitive(ent):
    got = ent.min_tier_batch_at("CLOUD_STARTER", features=["fleet"])
    assert got is not None
    assert set(got.keys()) == _EXPECTED_ENVELOPE_KEYS


def test_helper_perspective_is_whitespace_stripped(ent):
    got = ent.min_tier_batch_at("  cloud_starter  ", features=["fleet"])
    assert got is not None


def test_helper_trial_is_accepted_as_perspective(ent):
    """Trial is in :data:`_TIER_ORDER` even though it is non-purchasable
    -- match the rest of the ``_at`` family which accepts it as a valid
    hypothetical perspective."""
    got = ent.min_tier_batch_at(ent.TIER_TRIAL, features=["fleet"])
    assert got is not None
    assert set(got.keys()) == _EXPECTED_ENVELOPE_KEYS


# ── helper: shape parity with min_tier_batch ─────────────────────────────


def test_helper_returns_envelope_with_five_axes(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER,
        features=["fleet", "sso"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=3,
    )
    assert set(out.keys()) == _EXPECTED_ENVELOPE_KEYS
    assert isinstance(out["features"], list)
    assert isinstance(out["runtimes"], list)
    for axis in ("channels", "retention_days", "nodes"):
        assert isinstance(out[axis], dict)


def test_helper_row_shape_matches_batch(ent):
    out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, features=["fleet"])
    row = out["features"][0]
    assert set(row.keys()) == _EXPECTED_ROW_KEYS
    assert row["kind"] == "feature"


# ── helper: perspective-independence parity ──────────────────────────────


def test_helper_parity_with_min_tier_batch_across_every_perspective(ent):
    """The ``_at`` prefix must NOT shape rows. For every perspective in
    :data:`_TIER_ORDER`, the batch envelope must byte-equal the current-
    perspective :func:`min_tier_batch` for the same constraint bundle."""
    kwargs = dict(
        features=sorted(ent.ALL_FEATURES),
        runtimes=sorted(ent.ALL_RUNTIMES),
        channels=5,
        retention_days=30,
        nodes=3,
    )
    baseline = ent.min_tier_batch(**kwargs)
    for p in sorted(ent._TIER_ORDER):
        got = ent.min_tier_batch_at(p, **kwargs)
        assert got == baseline, p


def test_helper_features_only_parity_across_perspectives(ent):
    baseline = ent.min_tier_batch(features=sorted(ent.ALL_FEATURES))
    for p in sorted(ent._TIER_ORDER):
        assert (
            ent.min_tier_batch_at(p, features=sorted(ent.ALL_FEATURES))
            == baseline
        ), p


def test_helper_runtimes_only_parity_across_perspectives(ent):
    baseline = ent.min_tier_batch(runtimes=sorted(ent.ALL_RUNTIMES))
    for p in sorted(ent._TIER_ORDER):
        assert (
            ent.min_tier_batch_at(p, runtimes=sorted(ent.ALL_RUNTIMES))
            == baseline
        ), p


def test_helper_capacity_only_parity_across_perspectives(ent):
    baseline = ent.min_tier_batch(channels=5, retention_days=30, nodes=3)
    for p in sorted(ent._TIER_ORDER):
        assert (
            ent.min_tier_batch_at(p, channels=5, retention_days=30, nodes=3)
            == baseline
        ), p


# ── helper: per-row parity with singular helpers ─────────────────────────


def test_helper_feature_rows_match_singular_helper(ent):
    for fid in sorted(ent.ALL_FEATURES):
        out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, features=[fid])
        assert len(out["features"]) == 1
        row = out["features"][0]
        assert row["key"] == fid
        assert row["min_tier"] == ent.min_tier_for_feature(fid)
        assert row["free"] is (row["min_tier"] == ent.TIER_OSS)


def test_helper_runtime_rows_match_singular_helper(ent):
    for rt in sorted(ent.ALL_RUNTIMES):
        out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, runtimes=[rt])
        assert len(out["runtimes"]) == 1
        row = out["runtimes"][0]
        assert row["key"] == rt
        assert row["min_tier"] == ent.min_tier_for_runtime(rt)


def test_helper_channels_row_matches_singular_helper(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, channels=n)
        assert out["channels"]["min_tier"] == ent.min_tier_for_channel_count(n)
        assert out["channels"]["key"] == str(n)
        assert out["channels"]["kind"] == "channels"


def test_helper_retention_row_matches_singular_helper(ent):
    for days in (0, 1, 7, 30, 90, 365, 3650):
        out = ent.min_tier_batch_at(
            ent.TIER_CLOUD_STARTER, retention_days=days
        )
        assert out["retention_days"]["min_tier"] == (
            ent.min_tier_for_retention_window(days)
        )
        assert out["retention_days"]["key"] == str(days)


def test_helper_nodes_row_matches_singular_helper(ent):
    for n in (0, 1, 3, 5, 25, 100, 10000):
        out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, nodes=n)
        assert out["nodes"]["min_tier"] == ent.min_tier_for_node_count(n)
        assert out["nodes"]["key"] == str(n)


# ── helper: runtime canonicalisation + dedup ─────────────────────────────


def test_helper_runtime_alias_canonicalises(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, runtimes=["claude-code"]
    )
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


def test_helper_runtime_alias_dedups_against_canonical(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, runtimes=["claude-code", "claude_code"]
    )
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


# ── helper: unknown ids ──────────────────────────────────────────────────


def test_helper_unknown_feature_returns_all_none_row(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, features=["definitely_not_a_feature"]
    )
    assert len(out["features"]) == 1
    row = out["features"][0]
    assert row["key"] == "definitely_not_a_feature"
    assert row["min_tier"] is None
    assert row["free"] is False
    assert row["min_tier_label"] is None
    assert row["min_tier_rank"] == -1


def test_helper_unknown_runtime_returns_all_none_row(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, runtimes=["definitely_not_a_runtime"]
    )
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["min_tier"] is None
    assert out["runtimes"][0]["free"] is False


def test_helper_non_int_capacity_returns_all_none_row(ent):
    out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, channels="oops")
    assert out["channels"]["min_tier"] is None
    assert out["channels"]["free"] is False
    assert out["channels"]["min_tier_rank"] == -1


# ── helper: input normalisation ──────────────────────────────────────────


def test_helper_features_are_lowercased_and_deduped(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER,
        features=["FLEET", " fleet ", "sso", "fleet"],
    )
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


def test_helper_features_accepts_csv_string(ent):
    out = ent.min_tier_batch_at(ent.TIER_CLOUD_STARTER, features="fleet,sso")
    keys = [r["key"] for r in out["features"]]
    assert keys == ["fleet", "sso"]


# ── helper: unset vs unlimited ───────────────────────────────────────────


def test_helper_retention_none_means_unset_not_unlimited(ent):
    """``retention_days=None`` here means axis-not-supplied, NOT the
    unlimited sentinel that would mis-route to Enterprise. Inherited
    from :func:`min_tier_batch`."""
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, retention_days=None, features=["fleet"]
    )
    assert out["retention_days"] is None


def test_helper_channels_none_means_unset(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, channels=None, features=["fleet"]
    )
    assert out["channels"] is None


def test_helper_nodes_none_means_unset(ent):
    out = ent.min_tier_batch_at(
        ent.TIER_CLOUD_STARTER, nodes=None, features=["fleet"]
    )
    assert out["nodes"] is None


# ── helper: grace vs enforce parity ──────────────────────────────────────


def test_helper_grace_vs_enforce_yields_byte_identical_rows(
    monkeypatch, tmp_path
):
    """The helper walks the static per-tier maps via :func:`min_tier_batch`,
    so grace vs enforce yields byte-identical rows -- a pricing walkthrough
    must render the same numbers on both sides of the enforcement cutover."""
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_out = e_grace.min_tier_batch_at(
        e_grace.TIER_CLOUD_STARTER,
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
    enf_out = e_enf.min_tier_batch_at(
        e_enf.TIER_CLOUD_STARTER,
        features=sorted(e_enf.ALL_FEATURES),
        runtimes=sorted(e_enf.ALL_RUNTIMES),
        channels=5,
        retention_days=30,
        nodes=3,
    )
    e_enf.invalidate()
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)

    assert grace_out == enf_out


# ── helper: never raises ─────────────────────────────────────────────────


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
def test_helper_never_raises(
    ent, features, runtimes, channels, retention_days, nodes
):
    try:
        out = ent.min_tier_batch_at(
            ent.TIER_CLOUD_STARTER,
            features=features,
            runtimes=runtimes,
            channels=channels,
            retention_days=retention_days,
            nodes=nodes,
        )
    except Exception:  # pragma: no cover
        pytest.fail("min_tier_batch_at must not raise")
    # Either a shaped envelope or None on delegate failure -- never crash.
    assert out is None or set(out.keys()) == _EXPECTED_ENVELOPE_KEYS


@pytest.mark.parametrize("bad_perspective", ["", "   ", None, "bogus", 123])
def test_helper_bad_perspective_never_raises(ent, bad_perspective):
    try:
        got = ent.min_tier_batch_at(bad_perspective, features=["fleet"])
    except Exception:  # pragma: no cover
        pytest.fail("min_tier_batch_at must not raise on bad perspective")
    assert got is None


# ── /api/entitlement/min-tier-batch-at ───────────────────────────────────


def test_endpoint_400_on_missing_tier(client):
    r = client.get("/api/entitlement/min-tier-batch-at")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "missing tier"


def test_endpoint_400_on_blank_tier(client):
    r = client.get("/api/entitlement/min-tier-batch-at?tier=%20")
    assert r.status_code == 400


def test_endpoint_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at?tier=bogus&features=fleet"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_endpoint_400_on_no_axis(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at?tier=cloud_starter"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_endpoint_happy_path_features(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter&features=fleet,sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= {
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
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
    assert body["perspective_tier"] == "cloud_starter"
    assert [r["key"] for r in body["features"]] == ["fleet", "sso"]
    assert body["runtimes"] == []
    assert body["channels"] is None


def test_endpoint_happy_path_all_axes(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter"
        "&features=fleet"
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


def test_endpoint_tier_is_case_insensitive(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=CLOUD_STARTER&features=fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_starter"


def test_endpoint_tier_is_whitespace_stripped(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=%20cloud_starter%20&features=fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_starter"


def test_endpoint_trial_is_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/min-tier-batch-at"
        f"?tier={ent.TIER_TRIAL}&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL


def test_endpoint_runtime_alias_canonicalises(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter&runtimes=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["runtimes"][0]["key"] == "claude_code"


def test_endpoint_unknown_id_does_not_500(client):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter"
        "&features=definitely_not_a_feature"
        "&runtimes=definitely_not_a_runtime"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"][0]["min_tier"] is None
    assert body["features"][0]["free"] is False
    assert body["runtimes"][0]["min_tier"] is None


def test_endpoint_non_int_capacity_treated_as_unsupplied(client):
    """Blank / non-int capacity args must be treated as "not supplied"
    (mirrors the singular endpoint's never-crash posture)."""
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter"
        "&features=fleet&channels=oops&retention_days=&nodes=oops"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_endpoint_per_row_parity_with_min_tier_batch(client, ent):
    """For the same constraint bundle, the ``_at`` endpoint's per-axis
    rows must byte-equal ``/min-tier-batch``. Pins the ``_at`` prefix
    against silent row-shaping regardless of perspective."""
    for fid in sorted(ent.ALL_FEATURES):
        at_body = client.get(
            f"/api/entitlement/min-tier-batch-at"
            f"?tier=cloud_starter&features={fid}"
        ).get_json()
        batch_body = client.get(
            f"/api/entitlement/min-tier-batch?features={fid}"
        ).get_json()
        assert at_body["features"] == batch_body["features"]
        assert at_body["runtimes"] == batch_body["runtimes"]


def test_endpoint_per_row_parity_across_perspectives(client, ent):
    """Regardless of the ``tier=`` perspective, per-axis rows must
    byte-equal the current-perspective ``/min-tier-batch`` for the same
    bundle."""
    batch_body = client.get(
        "/api/entitlement/min-tier-batch?features=fleet,sso"
        "&runtimes=claude_code&channels=5&retention_days=30&nodes=3"
    ).get_json()
    for p in sorted(ent._TIER_ORDER):
        at_body = client.get(
            f"/api/entitlement/min-tier-batch-at"
            f"?tier={p}&features=fleet,sso"
            f"&runtimes=claude_code&channels=5&retention_days=30&nodes=3"
        ).get_json()
        for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
            assert at_body[axis] == batch_body[axis], (p, axis)


def test_endpoint_carries_perspective_envelope(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter&features=fleet"
    )
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_starter"
    assert body["perspective_tier_label"] == ent.tier_label("cloud_starter")
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_starter")


def test_endpoint_carries_resolver_envelope(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-batch-at"
        "?tier=cloud_starter&features=fleet"
    )
    body = r.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
