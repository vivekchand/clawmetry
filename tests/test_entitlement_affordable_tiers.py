"""Tests for ``affordable_tiers`` and the
``/api/entitlement/affordable-tiers`` endpoint.

``affordable_tiers`` is the plural sibling of :func:`min_tier_for_all`
(which returns only the *floor* tier admitting a constraint bundle).
Same arg shape, same per-axis ``None`` "not supplied" sentinels, same
never-raise contract -- but returns the **full ordered list** of
purchasable tiers admitting the bundle (rank ascending, ``is_minimum``
flag on the first row) so a pricing-page surface can render
"you need at least Starter -- Pro and Enterprise also qualify" off
ONE round-trip instead of resolving the floor and then walking the
catalog client-side.

This file pins the row shape, the rung walk, the per-axis sentinels,
the grace/enforce row identity (decoupled from the resolved
entitlement), the never-raise contract, and the API envelope so a
future tier shuffle or resolver change breaks loudly here instead of
silently in the UI.
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


# ── helper: affordable_tiers row schema + ordering ─────────────────────────


def test_no_constraints_returns_none(ent):
    """Mirrors :func:`min_tier_for_all`: "nothing asked" -> ``None``."""
    assert ent.affordable_tiers() is None


def test_all_axes_none_returns_none(ent):
    assert (
        ent.affordable_tiers(
            features=None,
            runtimes=None,
            channels=None,
            retention_days=None,
            nodes=None,
        )
        is None
    )


def test_all_axes_collapse_to_none_returns_none(ent):
    """Empty iterables / all-unknown items collapse each axis to ``None``;
    when every axis collapses the helper returns ``None`` (matches the
    floor helper)."""
    out = ent.affordable_tiers(features=[], runtimes=())
    assert out is None


def test_all_unknown_items_returns_none(ent):
    out = ent.affordable_tiers(features=["nope", "still_nope"])
    assert out is None


def test_row_schema_matches_documented_shape(ent):
    out = ent.affordable_tiers(features=["fleet"])
    assert isinstance(out, list)
    assert out, "expected at least one qualifying tier"
    expected_keys = {"tier", "tier_label", "tier_rank", "is_minimum"}
    for row in out:
        assert set(row.keys()) == expected_keys, row


def test_rows_ordered_by_rank_ascending(ent):
    out = ent.affordable_tiers(features=["fleet"])
    ranks = [r["tier_rank"] for r in out]
    assert ranks == sorted(ranks), ranks


def test_only_first_row_is_minimum(ent):
    out = ent.affordable_tiers(features=["fleet"])
    flags = [r["is_minimum"] for r in out]
    assert flags[0] is True
    assert not any(flags[1:])


def test_starter_feature_lists_starter_and_above(ent):
    """fleet unlocks at Starter (rank 1). Affordable list must include
    Starter (floor), Pro (rank 2 -- both cloud_pro and pro), and
    Enterprise (rank 3). Trial (rank 2 but non-purchasable) is excluded."""
    out = ent.affordable_tiers(features=["fleet"])
    tiers = [r["tier"] for r in out]
    assert tiers[0] == ent.TIER_CLOUD_STARTER
    assert ent.TIER_CLOUD_PRO in tiers
    assert ent.TIER_PRO in tiers
    assert ent.TIER_ENTERPRISE in tiers
    assert ent.TIER_TRIAL not in tiers


def test_pro_feature_excludes_starter(ent):
    """otel_export needs Pro (rank 2). Starter (rank 1) must drop off."""
    out = ent.affordable_tiers(features=["otel_export"])
    tiers = [r["tier"] for r in out]
    assert ent.TIER_CLOUD_STARTER not in tiers
    assert ent.TIER_CLOUD_PRO in tiers
    assert ent.TIER_PRO in tiers
    assert ent.TIER_ENTERPRISE in tiers


def test_enterprise_feature_returns_only_enterprise(ent):
    """sso is Enterprise-only. Floor is Enterprise so the list collapses
    to a single row."""
    out = ent.affordable_tiers(features=["sso"])
    assert [r["tier"] for r in out] == [ent.TIER_ENTERPRISE]
    assert out[0]["is_minimum"] is True


def test_oss_features_include_full_purchasable_ladder(ent):
    """Free features have floor=OSS. Affordable list must enumerate every
    purchasable tier (Trial intentionally excluded)."""
    out = ent.affordable_tiers(features=["sessions", "usage", "brain"])
    tiers = {r["tier"] for r in out}
    assert tiers == {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert ent.TIER_TRIAL not in tiers


def test_trial_never_in_results(ent):
    """``TIER_TRIAL`` is a promotional grant, not a price-page row -- it
    must never appear in affordable_tiers output."""
    for inputs in (
        {"features": ["sessions"]},
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"features": ["sso"]},
        {"runtimes": ["claude_code"]},
        {"channels": 100},
        {"retention_days": 365},
        {"nodes": 50},
    ):
        out = ent.affordable_tiers(**inputs)
        if out is None:
            continue
        assert all(r["tier"] != ent.TIER_TRIAL for r in out), inputs


def test_unknown_items_skipped_then_resolved_off_known_subset(ent):
    """Mixed known + unknown items resolve off the known subset (mirrors
    :func:`min_tier_for_all` semantics)."""
    out = ent.affordable_tiers(features=["fleet", "not_a_real_feature"])
    assert out is not None
    assert out[0]["tier"] == ent.TIER_CLOUD_STARTER


# ── helper: capacity-axis sentinels ─────────────────────────────────────────


def test_channels_axis_floor_is_starter(ent):
    out = ent.affordable_tiers(channels=10)
    assert out is not None
    assert out[0]["tier"] == ent.TIER_CLOUD_STARTER


def test_retention_days_unset_is_distinct_from_unlimited(ent):
    """``retention_days=None`` to the helper means *unset*, NOT *unlimited*
    -- which would mis-route to Enterprise. With only features supplied
    the retention axis must contribute nothing."""
    out = ent.affordable_tiers(features=["fleet"], retention_days=None)
    assert out[0]["tier"] == ent.TIER_CLOUD_STARTER


def test_retention_above_pro_cap_collapses_to_enterprise(ent):
    """Pro cap is 90 days; only Enterprise has unlimited retention. 365
    days must collapse the floor to Enterprise."""
    out = ent.affordable_tiers(retention_days=365)
    assert out is not None
    assert [r["tier"] for r in out] == [ent.TIER_ENTERPRISE]


def test_most_constraining_axis_wins(ent):
    """fleet -> Starter; sso -> Enterprise. The aggregate floor must be
    Enterprise (most-constraining axis wins, same as min_tier_for_all)."""
    out = ent.affordable_tiers(features=["fleet", "sso"])
    assert [r["tier"] for r in out] == [ent.TIER_ENTERPRISE]


def test_mixed_axes_floor_is_max(ent):
    """fleet -> Starter (rank 1); 365-day retention -> Enterprise (rank 3).
    Floor must be Enterprise."""
    out = ent.affordable_tiers(features=["fleet"], retention_days=365)
    assert [r["tier"] for r in out] == [ent.TIER_ENTERPRISE]


# ── helper: contract guarantees ─────────────────────────────────────────────


def test_helper_never_raises_on_garbage_input(ent):
    """Non-iterables, exotic types, the wrong axes -- helper must collapse
    to ``None`` instead of bubbling up an exception."""
    assert ent.affordable_tiers(features=42) is None
    assert ent.affordable_tiers(runtimes=object()) is None
    assert ent.affordable_tiers(channels="not a number") is None
    assert ent.affordable_tiers(retention_days="x") is None
    assert ent.affordable_tiers(nodes={}) is None


def test_helper_grace_enforce_row_identity(monkeypatch, ent):
    """Decoupled from the resolved entitlement: grace vs enforce yields
    identical rows. The hypothetical "which tiers admit X" view doesn't
    move when the resolver flips modes."""
    grace_out = ent.affordable_tiers(features=["fleet"])

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_out = ent.affordable_tiers(features=["fleet"])

    assert grace_out == enforce_out


def test_helper_only_returns_purchasable_tiers(ent):
    """Every row must be a purchasable tier id (Trial excluded by design)."""
    purchasable = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    for inputs in (
        {"features": ["sessions"]},
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"channels": 10},
        {"retention_days": 60},
        {"nodes": 3},
    ):
        out = ent.affordable_tiers(**inputs)
        if out is None:
            continue
        for row in out:
            assert row["tier"] in purchasable, (inputs, row)


def test_helper_row_count_matches_purchasable_above_floor(ent):
    """Row count = number of purchasable tiers with rank >= floor."""
    purchasable_ranks = sorted(
        {ent.tier_rank(t) for t in (
            ent.TIER_OSS,
            ent.TIER_CLOUD_FREE,
            ent.TIER_CLOUD_STARTER,
            ent.TIER_CLOUD_PRO,
            ent.TIER_PRO,
            ent.TIER_ENTERPRISE,
        )}
    )
    # fleet -> floor rank 1 -> ranks [1, 2, 3] qualify
    out = ent.affordable_tiers(features=["fleet"])
    floor_rank = ent.tier_rank(ent.TIER_CLOUD_STARTER)
    expected_purchasable = [
        t for t in (
            ent.TIER_OSS,
            ent.TIER_CLOUD_FREE,
            ent.TIER_CLOUD_STARTER,
            ent.TIER_CLOUD_PRO,
            ent.TIER_PRO,
            ent.TIER_ENTERPRISE,
        )
        if ent.tier_rank(t) >= floor_rank
    ]
    assert len(out) == len(expected_purchasable)
    # And the rank set lines up too.
    assert sorted({r["tier_rank"] for r in out}) == sorted(
        {r for r in purchasable_ranks if r >= floor_rank}
    )


def test_helper_row_ordering_is_deterministic(ent):
    """Same-rank ties must break alphabetically by tier id so the row
    sequence is byte-stable across invocations."""
    out_a = ent.affordable_tiers(features=["sessions"])
    out_b = ent.affordable_tiers(features=["sessions"])
    assert [r["tier"] for r in out_a] == [r["tier"] for r in out_b]
    # Pro rung carries both cloud_pro and pro at rank 2 -- pin the order.
    rank2 = [r["tier"] for r in out_a if r["tier_rank"] == 2]
    assert rank2 == sorted(rank2), rank2


def test_helper_first_row_floor_matches_min_tier_for_all(ent):
    """``affordable_tiers[0].tier`` must equal ``min_tier_for_all`` for the
    same args -- the plural can't disagree with the singular on the floor."""
    cases = (
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"features": ["fleet", "otel_export"]},
        {"runtimes": ["claude_code"]},
        {"channels": 10},
        {"retention_days": 60},
        {"nodes": 3},
        {"features": ["fleet"], "retention_days": 365},
    )
    for inputs in cases:
        floor = ent.min_tier_for_all(**inputs)
        out = ent.affordable_tiers(**inputs)
        if floor is None:
            assert out is None, inputs
            continue
        assert out is not None and out[0]["tier"] == floor, inputs


# ── API: /api/entitlement/affordable-tiers ──────────────────────────────────


def test_api_missing_all_args_returns_400(client):
    r = client.get("/api/entitlement/affordable-tiers")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_api_blank_csv_returns_400(client):
    r = client.get("/api/entitlement/affordable-tiers?features=&runtimes=")
    assert r.status_code == 400


def test_api_features_csv_happy_path(client, ent):
    r = client.get("/api/entitlement/affordable-tiers?features=fleet")
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"] == ["fleet"]
    assert body["minimum_tier"] == ent.TIER_CLOUD_STARTER
    assert body["minimum_tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["minimum_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["tiers"][0]["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tiers"][0]["is_minimum"] is True


def test_api_envelope_keys_are_complete(client):
    r = client.get("/api/entitlement/affordable-tiers?features=fleet")
    body = r.get_json()
    expected = {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "current_tier",
        "current_tier_rank",
        "minimum_tier",
        "minimum_tier_label",
        "minimum_tier_rank",
        "tiers",
    }
    assert expected <= set(body.keys())


def test_api_row_keys_carry_is_current(client):
    r = client.get("/api/entitlement/affordable-tiers?features=fleet")
    body = r.get_json()
    row_keys = {
        "tier",
        "tier_label",
        "tier_rank",
        "is_minimum",
        "is_current",
        "is_current_or_better",
    }
    for row in body["tiers"]:
        assert set(row.keys()) == row_keys, row


def test_api_is_current_marks_current_tier(client, ent):
    r = client.get("/api/entitlement/affordable-tiers?features=sessions")
    body = r.get_json()
    cur = body["current_tier"]
    flagged = [r for r in body["tiers"] if r["is_current"]]
    if cur in [row["tier"] for row in body["tiers"]]:
        assert len(flagged) == 1
        assert flagged[0]["tier"] == cur


def test_api_is_current_or_better_strictly_increases(client):
    r = client.get("/api/entitlement/affordable-tiers?features=sessions")
    body = r.get_json()
    cur_rank = body["current_tier_rank"]
    for row in body["tiers"]:
        assert row["is_current_or_better"] == (row["tier_rank"] >= cur_rank), row


def test_api_capacity_axes_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers?channels=10&retention_days=60&nodes=2",
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] == 10
    assert body["retention_days"] == 60
    assert body["nodes"] == 2
    assert body["minimum_tier"] is not None
    assert body["tiers"]


def test_api_unparseable_capacity_falls_through(client):
    """Non-int capacity -> axis treated as not supplied (matches the
    never-crash posture of /required-tier-batch)."""
    r = client.get(
        "/api/entitlement/affordable-tiers?features=fleet&channels=xx",
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["features"] == ["fleet"]


def test_api_csv_normalisation_dedup_and_lowercase(client):
    r = client.get(
        "/api/entitlement/affordable-tiers?features=fleet,FLEET,,fleet",
    )
    body = r.get_json()
    assert body["features"] == ["fleet"]


def test_api_unknown_items_collapse_to_400_when_alone(client):
    """If the only supplied axis collapses to all-unknown items, the helper
    returns ``None``; the wrapper still surfaces an envelope (not a 400)
    because the *input* axes were supplied even if they collapsed."""
    r = client.get(
        "/api/entitlement/affordable-tiers?features=not_a_real_feature",
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"] == ["not_a_real_feature"]
    assert body["minimum_tier"] is None
    assert body["minimum_tier_rank"] == -1
    assert body["tiers"] == []


def test_api_enterprise_feature_returns_single_row(client, ent):
    r = client.get("/api/entitlement/affordable-tiers?features=sso")
    body = r.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_ENTERPRISE]


def test_api_csv_runtimes_axis(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers?runtimes=claude_code",
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["runtimes"] == ["claude_code"]
    assert body["minimum_tier"] is not None
    assert body["tiers"]


def test_api_mixed_axes_floor_matches_helper(client, ent):
    """API floor must equal :func:`min_tier_for_all` for the same args."""
    r = client.get(
        "/api/entitlement/affordable-tiers?features=fleet&retention_days=365",
    )
    body = r.get_json()
    assert body["minimum_tier"] == ent.min_tier_for_all(
        features=["fleet"], retention_days=365,
    )


def test_api_byte_equality_against_required_tier_batch_floor(client, ent):
    """``/affordable-tiers.minimum_tier`` must match
    ``/required-tier-batch.required_tier`` for the same args -- the two
    endpoints share a floor."""
    q = "features=fleet,otel_export&nodes=2&retention_days=45"
    a = client.get("/api/entitlement/affordable-tiers?" + q).get_json()
    b = client.get("/api/entitlement/required-tier-batch?" + q).get_json()
    assert a["minimum_tier"] == b["required_tier"]
    assert a["minimum_tier_rank"] == b["required_tier_rank"]


def test_api_never_crashes_on_garbage_query(client):
    """Wrapper must serve a 200 envelope (or 400 on missing args) for any
    junk input -- never a 5xx."""
    junk_queries = (
        "features=,,,&runtimes=,,",
        "channels=NaN&retention_days=&nodes=",
        "features=%00bad%01",
    )
    for q in junk_queries:
        r = client.get("/api/entitlement/affordable-tiers?" + q)
        assert r.status_code in (200, 400), (q, r.status_code)
