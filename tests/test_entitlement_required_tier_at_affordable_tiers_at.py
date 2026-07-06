"""Tests for the ``_at`` (hypothetical-perspective) siblings of the
aggregate constraint-bundle helpers:

* :func:`clawmetry.entitlements.min_tier_for_all_at`
* :func:`clawmetry.entitlements.affordable_tiers_at`

and their HTTP wrappers:

* ``GET /api/entitlement/required-tier-at``
* ``GET /api/entitlement/affordable-tiers-at``

These fill the ``_at`` slot for the aggregate constraint-bundle family
alongside the per-axis ``_at`` scalars (``capacity_diff_at``,
``tier_unlocks_at``, ``tier_locks_at``, ``tier_diff_at_batch``) so a
pricing-comparison tooltip can call ``X_at(perspective, ...)`` uniformly
across the whole ``_at`` scalar family.

The core invariant pinned in this file is the **parity contract**: for
every perspective in :data:`_TIER_ORDER`, the ``_at`` sibling returns
byte-identical results to the current-perspective helper for the same
constraint bundle. Perspective is validated but does NOT shape the
answer -- a future regression that leaks the perspective into the
computation breaks loudly here instead of silently in the UI.
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


# ── min_tier_for_all_at: perspective validation ───────────────────────────


def test_min_tier_for_all_at_missing_perspective_returns_none(ent):
    assert ent.min_tier_for_all_at("", features=["fleet"]) is None
    assert ent.min_tier_for_all_at(None, features=["fleet"]) is None


def test_min_tier_for_all_at_unknown_perspective_returns_none(ent):
    assert ent.min_tier_for_all_at("nope", features=["fleet"]) is None
    assert ent.min_tier_for_all_at("cloud", features=["fleet"]) is None


def test_min_tier_for_all_at_accepts_trial_perspective(ent):
    """Perspective validation mirrors every other ``_at`` helper: trial is
    a legitimate perspective even though it is not purchasable."""
    assert ent.min_tier_for_all_at(
        ent.TIER_TRIAL, features=["fleet"]
    ) == ent.TIER_CLOUD_STARTER


def test_min_tier_for_all_at_accepts_every_tier_in_tier_order(ent):
    """Every id in _TIER_ORDER must be accepted as a perspective."""
    for p in ent._TIER_ORDER:
        out = ent.min_tier_for_all_at(p, features=["fleet"])
        assert out == ent.TIER_CLOUD_STARTER, p


def test_min_tier_for_all_at_perspective_case_insensitive(ent):
    """Whitespace + case are normalised on the perspective."""
    a = ent.min_tier_for_all_at("  Cloud_Pro  ", features=["fleet"])
    b = ent.min_tier_for_all_at(ent.TIER_CLOUD_PRO, features=["fleet"])
    assert a == b


# ── min_tier_for_all_at: parity vs current-perspective sibling ────────────


def test_min_tier_for_all_at_parity_features(ent):
    """Byte-identical to :func:`min_tier_for_all` for every perspective."""
    for p in ent._TIER_ORDER:
        at = ent.min_tier_for_all_at(p, features=["fleet"])
        cur = ent.min_tier_for_all(features=["fleet"])
        assert at == cur, p


def test_min_tier_for_all_at_parity_across_axes(ent):
    """Parity holds across every axis combination."""
    cases = (
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"features": ["sso"]},
        {"features": ["fleet", "otel_export"]},
        {"runtimes": ["claude_code"]},
        {"channels": 10},
        {"retention_days": 60},
        {"retention_days": 365},
        {"nodes": 3},
        {"features": ["fleet"], "retention_days": 365},
        {"features": ["fleet"], "runtimes": ["claude_code"], "channels": 5},
    )
    for p in ent._TIER_ORDER:
        for inputs in cases:
            at = ent.min_tier_for_all_at(p, **inputs)
            cur = ent.min_tier_for_all(**inputs)
            assert at == cur, (p, inputs)


def test_min_tier_for_all_at_no_constraints_returns_none(ent):
    """No constraints supplied -- returns ``None`` even with a valid
    perspective."""
    assert ent.min_tier_for_all_at(ent.TIER_CLOUD_PRO) is None


def test_min_tier_for_all_at_retention_none_means_unset(ent):
    """``retention_days=None`` is *unset*, NOT *unlimited* (which would
    mis-route to Enterprise). Matches :func:`min_tier_for_all`."""
    out = ent.min_tier_for_all_at(
        ent.TIER_CLOUD_STARTER, features=["fleet"], retention_days=None
    )
    assert out == ent.TIER_CLOUD_STARTER


def test_min_tier_for_all_at_most_constraining_axis_wins(ent):
    """fleet -> Starter (rank 1); sso -> Enterprise (rank 3). The aggregate
    floor must be Enterprise regardless of perspective."""
    out = ent.min_tier_for_all_at(
        ent.TIER_OSS, features=["fleet", "sso"]
    )
    assert out == ent.TIER_ENTERPRISE


# ── min_tier_for_all_at: contract guarantees ──────────────────────────────


def test_min_tier_for_all_at_never_raises_on_garbage(ent):
    """Non-iterables, exotic types on the constraint axes -- helper must
    collapse to ``None`` instead of bubbling up an exception."""
    p = ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_all_at(p, features=42) is None
    assert ent.min_tier_for_all_at(p, runtimes=object()) is None
    assert ent.min_tier_for_all_at(p, channels="not a number") is None


def test_min_tier_for_all_at_never_raises_on_perspective_type(ent):
    """Perspective must accept anything without crashing."""
    assert ent.min_tier_for_all_at(42, features=["fleet"]) is None
    assert ent.min_tier_for_all_at(object(), features=["fleet"]) is None
    assert ent.min_tier_for_all_at([], features=["fleet"]) is None


def test_min_tier_for_all_at_grace_enforce_identity(monkeypatch, ent):
    """Decoupled from the resolved entitlement: grace vs enforce yields
    identical answers."""
    grace_out = ent.min_tier_for_all_at(
        ent.TIER_CLOUD_STARTER, features=["fleet"]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_out = ent.min_tier_for_all_at(
        ent.TIER_CLOUD_STARTER, features=["fleet"]
    )
    assert grace_out == enforce_out


# ── affordable_tiers_at: perspective validation ───────────────────────────


def test_affordable_tiers_at_missing_perspective_returns_none(ent):
    assert ent.affordable_tiers_at("", features=["fleet"]) is None
    assert ent.affordable_tiers_at(None, features=["fleet"]) is None


def test_affordable_tiers_at_unknown_perspective_returns_none(ent):
    assert ent.affordable_tiers_at("nope", features=["fleet"]) is None


def test_affordable_tiers_at_accepts_trial_perspective(ent):
    out = ent.affordable_tiers_at(ent.TIER_TRIAL, features=["fleet"])
    assert out is not None
    assert out[0]["tier"] == ent.TIER_CLOUD_STARTER


def test_affordable_tiers_at_accepts_every_tier_in_tier_order(ent):
    for p in ent._TIER_ORDER:
        out = ent.affordable_tiers_at(p, features=["fleet"])
        assert out is not None, p
        assert out[0]["tier"] == ent.TIER_CLOUD_STARTER, p


# ── affordable_tiers_at: parity vs current-perspective sibling ────────────


def test_affordable_tiers_at_parity_features(ent):
    """Byte-identical to :func:`affordable_tiers` for every perspective."""
    for p in ent._TIER_ORDER:
        at = ent.affordable_tiers_at(p, features=["fleet"])
        cur = ent.affordable_tiers(features=["fleet"])
        assert at == cur, p


def test_affordable_tiers_at_parity_across_axes(ent):
    cases = (
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"features": ["sso"]},
        {"features": ["fleet", "otel_export"]},
        {"runtimes": ["claude_code"]},
        {"channels": 10},
        {"retention_days": 60},
        {"retention_days": 365},
        {"nodes": 3},
        {"features": ["fleet"], "retention_days": 365},
    )
    for p in ent._TIER_ORDER:
        for inputs in cases:
            at = ent.affordable_tiers_at(p, **inputs)
            cur = ent.affordable_tiers(**inputs)
            assert at == cur, (p, inputs)


def test_affordable_tiers_at_no_constraints_returns_none(ent):
    assert ent.affordable_tiers_at(ent.TIER_CLOUD_PRO) is None


def test_affordable_tiers_at_row_schema(ent):
    """Row schema mirrors :func:`affordable_tiers` byte-for-byte."""
    out = ent.affordable_tiers_at(ent.TIER_CLOUD_STARTER, features=["fleet"])
    expected_keys = {"tier", "tier_label", "tier_rank", "is_minimum"}
    for row in out:
        assert set(row.keys()) == expected_keys, row


def test_affordable_tiers_at_trial_never_in_results(ent):
    """``TIER_TRIAL`` is never a purchasable row regardless of perspective."""
    for p in ent._TIER_ORDER:
        for inputs in (
            {"features": ["fleet"]},
            {"channels": 10},
            {"retention_days": 60},
            {"nodes": 3},
        ):
            out = ent.affordable_tiers_at(p, **inputs)
            if out is None:
                continue
            assert all(r["tier"] != ent.TIER_TRIAL for r in out), (p, inputs)


def test_affordable_tiers_at_first_row_matches_min_tier_for_all_at(ent):
    """``affordable_tiers_at[0].tier`` == ``min_tier_for_all_at`` for the
    same perspective + args -- the plural can't disagree with the singular."""
    cases = (
        {"features": ["fleet"]},
        {"features": ["otel_export"]},
        {"runtimes": ["claude_code"]},
        {"channels": 10},
        {"retention_days": 60},
        {"features": ["fleet"], "retention_days": 365},
    )
    for p in ent._TIER_ORDER:
        for inputs in cases:
            floor = ent.min_tier_for_all_at(p, **inputs)
            out = ent.affordable_tiers_at(p, **inputs)
            if floor is None:
                assert out is None, (p, inputs)
                continue
            assert out is not None and out[0]["tier"] == floor, (p, inputs)


def test_affordable_tiers_at_grace_enforce_identity(monkeypatch, ent):
    grace_out = ent.affordable_tiers_at(
        ent.TIER_CLOUD_STARTER, features=["fleet"]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce_out = ent.affordable_tiers_at(
        ent.TIER_CLOUD_STARTER, features=["fleet"]
    )
    assert grace_out == enforce_out


def test_affordable_tiers_at_never_raises_on_garbage(ent):
    p = ent.TIER_CLOUD_STARTER
    assert ent.affordable_tiers_at(p, features=42) is None
    assert ent.affordable_tiers_at(p, runtimes=object()) is None
    assert ent.affordable_tiers_at(p, channels="not a number") is None


def test_affordable_tiers_at_never_raises_on_perspective_type(ent):
    assert ent.affordable_tiers_at(42, features=["fleet"]) is None
    assert ent.affordable_tiers_at(object(), features=["fleet"]) is None


# ── API: /api/entitlement/required-tier-at ────────────────────────────────


def test_api_required_tier_at_missing_tier_returns_400(client):
    r = client.get("/api/entitlement/required-tier-at?features=fleet")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_api_required_tier_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/required-tier-at?tier=nope&features=fleet"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_api_required_tier_at_missing_all_axes_returns_400(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier=" + ent.TIER_CLOUD_PRO
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_api_required_tier_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_STARTER
    assert body["perspective_tier_rank"] == ent.tier_rank(
        ent.TIER_CLOUD_STARTER
    )
    assert body["required_tier"] == ent.TIER_CLOUD_STARTER
    assert body["required_tier_label"] == ent.tier_label(
        ent.TIER_CLOUD_STARTER
    )
    assert body["required_tier_rank"] == ent.tier_rank(
        ent.TIER_CLOUD_STARTER
    )


def test_api_required_tier_at_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet"
    )
    body = r.get_json()
    expected = {
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "required_tier",
        "required_tier_label",
        "required_tier_rank",
        "current_tier",
        "current_tier_rank",
        "upgrade_required_from_perspective",
        "upgrade_required_from_current",
        "grace",
        "enforced",
    }
    assert expected <= set(body.keys())


def test_api_required_tier_at_upgrade_flags_from_oss_perspective(
    client, ent
):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_OSS
        + "&features=fleet"
    )
    body = r.get_json()
    assert body["upgrade_required_from_perspective"] is True


def test_api_required_tier_at_upgrade_flags_from_enterprise_perspective(
    client, ent
):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_ENTERPRISE
        + "&features=fleet"
    )
    body = r.get_json()
    assert body["upgrade_required_from_perspective"] is False


def test_api_required_tier_at_byte_equal_floor_regardless_of_perspective(
    client, ent
):
    """The floor is anchored to the constraint bundle, NOT the perspective."""
    q = "&features=fleet,otel_export&nodes=2&retention_days=45"
    floors = []
    for p in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ):
        r = client.get(
            "/api/entitlement/required-tier-at?tier=" + p + q
        )
        floors.append(r.get_json()["required_tier"])
    assert len(set(floors)) == 1, floors


def test_api_required_tier_at_parity_vs_required_tier_batch(client, ent):
    """Perspective-independent parity: the ``_at`` floor matches
    ``/required-tier-batch`` for the same bundle."""
    q = "features=fleet,otel_export&nodes=2&retention_days=45"
    a = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&"
        + q
    ).get_json()
    b = client.get("/api/entitlement/required-tier-batch?" + q).get_json()
    assert a["required_tier"] == b["required_tier"]
    assert a["required_tier_rank"] == b["required_tier_rank"]


def test_api_required_tier_at_unparseable_capacity_falls_through(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet&channels=xx"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["features"] == ["fleet"]


def test_api_required_tier_at_csv_normalisation(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet,FLEET,,fleet"
    )
    body = r.get_json()
    assert body["features"] == ["fleet"]


def test_api_required_tier_at_accepts_trial_perspective(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier="
        + ent.TIER_TRIAL
        + "&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL


def test_api_required_tier_at_perspective_whitespace_normalised(client, ent):
    r = client.get(
        "/api/entitlement/required-tier-at?tier=%20cloud_pro%20"
        "&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO


# ── API: /api/entitlement/affordable-tiers-at ─────────────────────────────


def test_api_affordable_tiers_at_missing_tier_returns_400(client):
    r = client.get("/api/entitlement/affordable-tiers-at?features=fleet")
    assert r.status_code == 400


def test_api_affordable_tiers_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier=nope&features=fleet"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_api_affordable_tiers_at_missing_all_axes_returns_400(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier=" + ent.TIER_CLOUD_PRO
    )
    assert r.status_code == 400


def test_api_affordable_tiers_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_STARTER
    assert body["minimum_tier"] == ent.TIER_CLOUD_STARTER
    assert body["tiers"][0]["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tiers"][0]["is_minimum"] is True


def test_api_affordable_tiers_at_row_keys(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet"
    )
    body = r.get_json()
    row_keys = {
        "tier",
        "tier_label",
        "tier_rank",
        "is_minimum",
        "is_current",
        "is_current_or_better",
        "is_perspective",
        "is_at_or_better_than_perspective",
    }
    for row in body["tiers"]:
        assert set(row.keys()) == row_keys, row


def test_api_affordable_tiers_at_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=fleet"
    )
    body = r.get_json()
    expected = {
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
        "minimum_tier",
        "minimum_tier_label",
        "minimum_tier_rank",
        "tiers",
        "grace",
        "enforced",
    }
    assert expected <= set(body.keys())


def test_api_affordable_tiers_at_is_perspective_marks_row(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_PRO
        + "&features=fleet"
    )
    body = r.get_json()
    flagged = [row for row in body["tiers"] if row["is_perspective"]]
    assert len(flagged) == 1
    assert flagged[0]["tier"] == ent.TIER_CLOUD_PRO


def test_api_affordable_tiers_at_at_or_better_from_perspective(client, ent):
    """``is_at_or_better_than_perspective`` must line up with rank
    comparison against the perspective."""
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_PRO
        + "&features=sessions"
    )
    body = r.get_json()
    persp_rank = body["perspective_tier_rank"]
    for row in body["tiers"]:
        assert row["is_at_or_better_than_perspective"] == (
            row["tier_rank"] >= persp_rank
        ), row


def test_api_affordable_tiers_at_tiers_bytewise_equal_across_perspectives(
    client, ent
):
    """The row LIST (minus the ``is_perspective`` /
    ``is_at_or_better_than_perspective`` flags) is anchored to the bundle,
    not the perspective."""
    q = "&features=fleet"
    lists = []
    for p in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ):
        r = client.get(
            "/api/entitlement/affordable-tiers-at?tier=" + p + q
        )
        body = r.get_json()
        stripped = [
            {
                "tier": row["tier"],
                "tier_label": row["tier_label"],
                "tier_rank": row["tier_rank"],
                "is_minimum": row["is_minimum"],
            }
            for row in body["tiers"]
        ]
        lists.append(stripped)
    for lst in lists[1:]:
        assert lst == lists[0]


def test_api_affordable_tiers_at_parity_vs_affordable_tiers(client, ent):
    """The stripped tier list must byte-equal ``/affordable-tiers`` for the
    same bundle regardless of perspective."""
    q = "features=fleet,otel_export&nodes=2&retention_days=45"
    a = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_STARTER
        + "&"
        + q
    ).get_json()
    b = client.get("/api/entitlement/affordable-tiers?" + q).get_json()
    a_stripped = [
        {
            "tier": r["tier"],
            "tier_label": r["tier_label"],
            "tier_rank": r["tier_rank"],
            "is_minimum": r["is_minimum"],
        }
        for r in a["tiers"]
    ]
    b_stripped = [
        {
            "tier": r["tier"],
            "tier_label": r["tier_label"],
            "tier_rank": r["tier_rank"],
            "is_minimum": r["is_minimum"],
        }
        for r in b["tiers"]
    ]
    assert a_stripped == b_stripped
    assert a["minimum_tier"] == b["minimum_tier"]


def test_api_affordable_tiers_at_capacity_axes_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_CLOUD_PRO
        + "&channels=10&retention_days=60&nodes=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] == 10
    assert body["retention_days"] == 60
    assert body["nodes"] == 2
    assert body["minimum_tier"] is not None
    assert body["tiers"]


def test_api_affordable_tiers_at_never_crashes_on_garbage(client, ent):
    for q in (
        "features=,,,&runtimes=,,",
        "channels=NaN&retention_days=&nodes=",
        "features=%00bad%01",
    ):
        r = client.get(
            "/api/entitlement/affordable-tiers-at?tier="
            + ent.TIER_CLOUD_STARTER
            + "&"
            + q
        )
        # 200 (envelope) or 400 (no axis) -- never 5xx.
        assert r.status_code in (200, 400), (q, r.status_code)


def test_api_required_tier_at_never_crashes_on_garbage(client, ent):
    for q in (
        "features=,,,&runtimes=,,",
        "channels=NaN&retention_days=&nodes=",
        "features=%00bad%01",
    ):
        r = client.get(
            "/api/entitlement/required-tier-at?tier="
            + ent.TIER_CLOUD_STARTER
            + "&"
            + q
        )
        assert r.status_code in (200, 400), (q, r.status_code)


def test_api_affordable_tiers_at_accepts_trial_perspective(client, ent):
    r = client.get(
        "/api/entitlement/affordable-tiers-at?tier="
        + ent.TIER_TRIAL
        + "&features=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL
