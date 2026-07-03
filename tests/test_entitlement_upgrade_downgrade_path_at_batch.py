"""Tests for ``upgrade_path_at_batch(tiers)`` /
``downgrade_path_at_batch(tiers)`` + the companion
``/api/entitlement/{upgrade,downgrade}-path-at-batch`` endpoints.

Perspective-tier-batched siblings of the scalar
:func:`upgrade_path_at` / :func:`downgrade_path_at` what-ifs. Where
each scalar hydrates the ordered marginal-unlock (or cumulative-loss)
ladder from ONE hypothetical source, the batch hydrates the same
ladder for N hypothetical sources off a single round-trip -- the same
axis :func:`tier_catalog_at_batch` batches on.

Each returned ``tiers[].path`` list must be byte-identical to the
scalar's return for the same source tier so the scalar and batch
what-if path helpers cannot drift -- pinned by the parity tests
below.

Coverage (both helpers + both endpoints):

* per-source row shape (``tier`` / ``tier_label`` / ``tier_rank`` /
  ``path``) matches the outer envelope of the sibling ``_at_batch``
  family
* every tier in ``_TIER_ORDER`` (including ``trial``) round-trips
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved) -- same as ``_normalise_csv``
* unknown ids are echoed in ``unknown[]`` instead of short-circuiting;
  ceiling / floor sources are NOT ``unknown`` -- they yield a valid
  row with an empty ``path`` list
* the helper never raises -- a per-tier scalar crash / ``None``
  short-circuits that id into ``unknown[]`` so the matrix keeps
  rendering
* the HTTP endpoint 400s on missing / empty input, echoes unknown
  ids at 200, carries the standard envelope (``current_tier`` /
  ``current_tier_rank`` / ``grace`` / ``enforced``), and never 5xxs
  on a resolver crash
* grace vs enforce yields byte-identical bodies (catalogue-derived)
"""
from __future__ import annotations

import importlib

import pytest


_OUTER_ROW_KEYS = {"tier", "tier_label", "tier_rank", "path"}

_ENVELOPE_KEYS = {
    "tiers",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode); the batch helpers are
    catalogue-derived and independent of either knob, but the fixture
    avoids live-resolver surprises."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── helper: input handling (both) ────────────────────────────────────────────


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_empty_input_returns_empty_envelope(ent, fn):
    assert getattr(ent, fn)([]) == {"tiers": [], "unknown": []}


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_none_input_returns_empty_envelope(ent, fn):
    assert getattr(ent, fn)(None) == {"tiers": [], "unknown": []}


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_string_csv_input(ent, fn):
    body = getattr(ent, fn)(
        f"{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_supply_order_preserved(ent, fn):
    body = getattr(ent, fn)(
        [ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_whitespace_and_case_normalised(ent, fn):
    body = getattr(ent, fn)(
        ["  CLOUD_PRO  ", ent.TIER_CLOUD_STARTER.upper()]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_duplicates_dropped_first_seen_wins(ent, fn):
    body = getattr(ent, fn)(
        [
            ent.TIER_CLOUD_PRO,
            ent.TIER_CLOUD_PRO,
            ent.TIER_CLOUD_STARTER,
            ent.TIER_CLOUD_PRO,
        ]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_unknown_ids_echoed_in_unknown(ent, fn):
    body = getattr(ent, fn)(
        [ent.TIER_CLOUD_PRO, "nope_tier", "also_bogus"]
    )
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_unknown_only_returns_empty_tiers(ent, fn):
    body = getattr(ent, fn)(["nope_tier", "also_bogus"])
    assert body == {"tiers": [], "unknown": ["nope_tier", "also_bogus"]}


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_non_iterable_input_falls_back_to_empty(ent, fn):
    """``_normalise_csv`` returns ``[]`` for non-iterable inputs (int,
    object, etc.) so the batch collapses to an empty envelope rather
    than raising."""
    assert getattr(ent, fn)(12345) == {"tiers": [], "unknown": []}
    assert getattr(ent, fn)(object()) == {"tiers": [], "unknown": []}


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_trial_source_accepted(ent, fn):
    body = getattr(ent, fn)([ent.TIER_TRIAL])
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_TRIAL]
    assert body["unknown"] == []


# ── helper: shape + parity ───────────────────────────────────────────────────


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_row_shape_matches_outer_envelope(ent, fn):
    body = getattr(ent, fn)([ent.TIER_CLOUD_PRO])
    assert len(body["tiers"]) == 1
    row = body["tiers"][0]
    assert set(row.keys()) == _OUTER_ROW_KEYS
    assert isinstance(row["path"], list)


def test_upgrade_batch_matches_scalar_exactly(ent):
    """Pin scalar / batch no-drift: every batch source's ``path`` list
    byte-equals the scalar ``upgrade_path_at`` list for the same source
    across the full tier order (including ``trial``)."""
    body = ent.upgrade_path_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["path"] == ent.upgrade_path_at(tid), tid


def test_downgrade_batch_matches_scalar_exactly(ent):
    """Pin scalar / batch no-drift: every batch source's ``path`` list
    byte-equals the scalar ``downgrade_path_at`` list for the same
    source across the full tier order (including ``trial``)."""
    body = ent.downgrade_path_at_batch(list(ent._TIER_ORDER))
    by_tier = {row["tier"]: row for row in body["tiers"]}
    assert set(by_tier) == set(ent._TIER_ORDER)
    for tid in ent._TIER_ORDER:
        assert by_tier[tid]["path"] == ent.downgrade_path_at(tid), tid


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_tier_metadata_matches_scalar(ent, fn):
    body = getattr(ent, fn)([ent.TIER_CLOUD_PRO])
    row = body["tiers"][0]
    assert row["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


@pytest.mark.parametrize("fn", ["upgrade_path_at_batch", "downgrade_path_at_batch"])
def test_every_tier_in_order_resolves(ent, fn):
    body = getattr(ent, fn)(list(ent._TIER_ORDER))
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


# ── helper: ceiling / floor rows (not unknown) ───────────────────────────────


def test_upgrade_ceiling_yields_empty_path_not_unknown(ent):
    """Enterprise is the ceiling of the purchasable ladder -- there is
    nothing strictly higher-rank to walk. The scalar returns ``[]``, not
    ``None``, so the batch must include a valid row (not bucket it into
    ``unknown[]``)."""
    body = ent.upgrade_path_at_batch([ent.TIER_ENTERPRISE])
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["tier"] == ent.TIER_ENTERPRISE
    assert body["tiers"][0]["path"] == []


def test_downgrade_floor_yields_empty_path_not_unknown(ent):
    """``oss`` and ``cloud_free`` sit at the floor of the purchasable
    ladder -- nothing strictly below to walk. The scalar returns ``[]``,
    not ``None``, so the batch must include valid rows for both."""
    body = ent.downgrade_path_at_batch([ent.TIER_OSS, ent.TIER_CLOUD_FREE])
    assert body["unknown"] == []
    tiers = {row["tier"]: row["path"] for row in body["tiers"]}
    assert tiers[ent.TIER_OSS] == []
    assert tiers[ent.TIER_CLOUD_FREE] == []


def test_upgrade_mid_ladder_row_shape(ent):
    """A mid-ladder source (``cloud_starter``) walks strictly-higher-
    rank purchasable tiers. Each inner row is the shape
    ``tier_unlocks`` returns."""
    body = ent.upgrade_path_at_batch([ent.TIER_CLOUD_STARTER])
    inner = body["tiers"][0]["path"]
    assert inner, "starter is not the ceiling -- expected non-empty path"
    expected_keys = {
        "tier",
        "tier_label",
        "tier_rank",
        "previous_tier",
        "previous_tier_label",
        "previous_tier_rank",
        "features",
        "runtimes",
    }
    for row in inner:
        assert set(row.keys()) == expected_keys


def test_downgrade_mid_ladder_row_shape(ent):
    """A mid-ladder source (``cloud_pro``) walks strictly-lower-rank
    purchasable tiers. Each inner row carries the destination metadata
    + the walk's source echo + cumulative ``lost_*`` lists."""
    body = ent.downgrade_path_at_batch([ent.TIER_CLOUD_PRO])
    inner = body["tiers"][0]["path"]
    assert inner, "cloud_pro is not the floor -- expected non-empty path"
    expected_keys = {
        "target",
        "target_label",
        "target_rank",
        "current_tier",
        "current_tier_label",
        "current_tier_rank",
        "lost_features",
        "lost_runtimes",
    }
    for row in inner:
        assert set(row.keys()) == expected_keys
        assert row["current_tier"] == ent.TIER_CLOUD_PRO


# ── helper: resolver-independence ────────────────────────────────────────────


def test_upgrade_grace_vs_enforce_byte_identical(ent, monkeypatch):
    """Enforcement is a live-resolver knob; the batch what-if helper is
    catalogue-derived and must produce byte-identical bodies."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.upgrade_path_at_batch(list(ent._TIER_ORDER))

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.upgrade_path_at_batch(list(ent._TIER_ORDER))
    assert grace == enforced


def test_downgrade_grace_vs_enforce_byte_identical(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    grace = ent.downgrade_path_at_batch(list(ent._TIER_ORDER))

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.downgrade_path_at_batch(list(ent._TIER_ORDER))
    assert grace == enforced


# ── helper: never-raise ──────────────────────────────────────────────────────


def test_upgrade_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    """A per-tier scalar crash must short-circuit that id into
    ``unknown[]`` and the rest of the batch keeps building."""
    real = ent.upgrade_path_at

    def flaky(t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "upgrade_path_at", flaky)
    body = ent.upgrade_path_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


def test_downgrade_never_raises_when_scalar_helper_crashes(ent, monkeypatch):
    real = ent.downgrade_path_at

    def flaky(t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated scalar crash")
        return real(t)

    monkeypatch.setattr(ent, "downgrade_path_at", flaky)
    body = ent.downgrade_path_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


def test_upgrade_never_raises_when_scalar_returns_none(ent, monkeypatch):
    """A per-tier scalar ``None`` return must land the id in
    ``unknown[]`` without raising."""
    real = ent.upgrade_path_at

    def none_pro(t):
        if t == ent.TIER_CLOUD_PRO:
            return None
        return real(t)

    monkeypatch.setattr(ent, "upgrade_path_at", none_pro)
    body = ent.upgrade_path_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


def test_downgrade_never_raises_when_scalar_returns_none(ent, monkeypatch):
    real = ent.downgrade_path_at

    def none_pro(t):
        if t == ent.TIER_CLOUD_PRO:
            return None
        return real(t)

    monkeypatch.setattr(ent, "downgrade_path_at", none_pro)
    body = ent.downgrade_path_at_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
    ]
    assert body["unknown"] == [ent.TIER_CLOUD_PRO]


# ── HTTP endpoint: happy path ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path,helper_name",
    [
        ("upgrade-path-at-batch", "upgrade_path_at"),
        ("downgrade-path-at-batch", "downgrade_path_at"),
    ],
)
def test_endpoint_known_tiers_returns_rows(client, ent, path, helper_name):
    resp = client.get(
        f"/api/entitlement/{path}"
        f"?tiers={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS.issubset(set(body.keys()))
    assert [row["tier"] for row in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    # Each row's path matches the scalar helper for the same source --
    # pinned so scalar and batch cannot drift at the transport layer.
    helper = getattr(ent, helper_name)
    for row in body["tiers"]:
        assert row["path"] == helper(row["tier"]), row["tier"]


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_missing_arg_returns_400(client, path):
    resp = client.get(f"/api/entitlement/{path}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_blank_arg_returns_400(client, path):
    resp = client.get(f"/api/entitlement/{path}?tiers=%20%20")
    assert resp.status_code == 400


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_unknown_ids_echoed_at_200(client, ent, path):
    resp = client.get(
        f"/api/entitlement/{path}"
        f"?tiers={ent.TIER_CLOUD_PRO},nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["nope_tier", "also_bogus"]


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_lowercases_and_trims(client, ent, path):
    resp = client.get(
        f"/api/entitlement/{path}"
        f"?tiers=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_every_tier_in_order_round_trips(client, ent, path):
    tiers = ",".join(ent._TIER_ORDER)
    resp = client.get(f"/api/entitlement/{path}?tiers={tiers}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["tiers"]) == len(ent._TIER_ORDER)
    assert body["unknown"] == []


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_envelope_carries_current_tier_and_grace_flags(
    client, ent, path
):
    resp = client.get(
        f"/api/entitlement/{path}?tiers={ent.TIER_CLOUD_PRO}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_never_5xx_on_resolver_crash(client, ent, monkeypatch, path):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver crash")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/{path}?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["grace"] is True
    assert body["enforced"] is False


@pytest.mark.parametrize(
    "path", ["upgrade-path-at-batch", "downgrade-path-at-batch"]
)
def test_endpoint_unknown_only_returns_200_empty_rows(client, path):
    resp = client.get(
        f"/api/entitlement/{path}?tiers=nope_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["nope_tier", "also_bogus"]


def test_endpoint_upgrade_ceiling_row_included_not_unknown(client, ent):
    resp = client.get(
        f"/api/entitlement/upgrade-path-at-batch?tiers={ent.TIER_ENTERPRISE}"
    )
    body = resp.get_json()
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["path"] == []


def test_endpoint_downgrade_floor_row_included_not_unknown(client, ent):
    resp = client.get(
        f"/api/entitlement/downgrade-path-at-batch?tiers={ent.TIER_OSS}"
    )
    body = resp.get_json()
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["path"] == []
