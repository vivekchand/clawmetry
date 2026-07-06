"""Tests for ``clawmetry.entitlements.channel_catalog_path(from, to)`` + the
``GET /api/entitlement/channel-catalog-path`` endpoint.

Channel-axis twin of :func:`feature_catalog_path` and
:func:`runtime_catalog_path`: the full chat-channel catalogue at every
rung between two tiers off ONE round-trip. Because every chat-channel
adapter is FREE at every tier (the ``channels`` capacity axis governs
how many concurrent channels each plan admits, not which adapters
unlock), each rung's inner ``channels`` list is byte-identical to
:func:`channel_catalog`. The path helper is worth having anyway: a
pricing-comparison UI that renders feature and runtime columns off
``/feature-catalog-path`` and ``/runtime-catalog-path`` should be able
to render the channel column off a matching sibling instead of
hard-coding "channels don't vary by tier" client-side.

Pins:

* per-rung row shape matches :func:`feature_catalog_path` /
  :func:`runtime_catalog_path` with ``features`` / ``runtimes``
  renamed to ``channels`` (``tier``, ``tier_label``, ``tier_rank``,
  ``channels``) -- byte-stable so a UI can render all three columns
  off one row-renderer
* each ``channels`` list byte-equals :func:`channel_catalog` for
  every rung -- the "channels are always free" invariant is baked
  in and never drifts
* rung walk byte-equals :func:`tier_path` on the destination axis
  and :func:`feature_catalog_path` / :func:`runtime_catalog_path` /
  :func:`tier_catalog_path` on the perspective axis -- the
  ``_path`` family stays in lock-step
* identity (``from == to``) -> ``[]``; lateral (same rank,
  different id) -> single-row path; ``trial`` accepted as an
  endpoint (excluded from the walked rungs but valid via the
  lateral branch)
* helper is decoupled from the resolver -- grace vs enforce yields
  the same rows
* unknown / empty / garbage ids return ``None`` and never raise; a
  synthesised failure in the inner row builder short-circuits to
  ``None``
* API: 400 on missing args, 404 on unknown ids, 200 with the
  standard ``_path`` envelope on the happy path; 404 (not 5xx)
  when the inner helper blows up
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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


_ROW_KEYS = {"tier", "tier_label", "tier_rank", "channels"}
_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
}


# ── helper: shape + per-row contract ─────────────────────────────────────


def test_returns_list(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_catalog_path_row_shape(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["channels"], list)
        assert row["tier_rank"] == ent._TIER_RANK[row["tier"]]
        assert row["tier_label"] == ent.tier_label(row["tier"])


def test_last_rung_is_destination(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE
    assert path[-1]["tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert path[-1]["tier_rank"] == ent._TIER_RANK[ent.TIER_ENTERPRISE]


# ── byte-parity with the bare channel catalog ────────────────────────────


def test_channels_list_byte_equals_channel_catalog_every_rung(ent):
    """Each rung's ``channels`` list is byte-identical to
    :func:`channel_catalog` -- channels are always free, so the
    catalogue is invariant across the rung walk. Pinned so a future
    _at helper cannot drift and quietly re-gate the channel axis
    behind a tier."""
    baseline = ent.channel_catalog()
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["channels"] == baseline


def test_every_channel_row_reports_free_at_every_rung(ent):
    """Belt-and-braces: even if a future tier flip pretended to gate
    the channel axis, every row reported by this helper must still
    surface ``free=True`` / ``allowed=True`` / ``locked=False`` /
    ``entitled=True`` -- otherwise the "channels are always free"
    posture has been broken."""
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        for ch in row["channels"]:
            assert ch["free"] is True
            assert ch["allowed"] is True
            assert ch["locked"] is False
            assert ch["entitled"] is True
            assert ch["tier"] == "free"


def test_channels_list_sorted_alphabetically(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        ids = [c["id"] for c in row["channels"]]
        assert ids == sorted(ids)


def test_channels_list_covers_all_channels(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    expected = set(ent.ALL_CHANNELS)
    for row in path:
        assert {c["id"] for c in row["channels"]} == expected


# ── rung walk parity with the rest of the _path family ───────────────────


def test_rung_walk_byte_equal_to_tier_path(ent):
    catalog = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    full = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in catalog] == [r["to"] for r in full]


def test_rung_walk_byte_equal_to_feature_catalog_path(ent):
    channels = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    features = ent.feature_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in channels] == [r["tier"] for r in features]


def test_rung_walk_byte_equal_to_runtime_catalog_path(ent):
    channels = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    runtimes = ent.runtime_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in channels] == [r["tier"] for r in runtimes]


def test_rung_walk_byte_equal_to_tier_catalog_path(ent):
    channels = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    tiers = ent.tier_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in channels] == [r["tier"] for r in tiers]


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must
    end exactly at ``pro`` and EXCLUDE the same-rank sibling
    ``cloud_pro`` from the final rung -- same rule as ``tier_path``."""
    tiers = [
        r["tier"]
        for r in ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_PRO)
    ]
    assert tiers[-1] == ent.TIER_PRO
    assert tiers.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in tiers


def test_same_rank_siblings_between_endpoints_both_included(ent):
    tiers = [
        r["tier"]
        for r in ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    ]
    assert ent.TIER_CLOUD_PRO in tiers
    assert ent.TIER_PRO in tiers
    assert tiers[-1] == ent.TIER_ENTERPRISE


# ── identity / lateral / adjacent ────────────────────────────────────────


def test_identity_returns_empty(ent):
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ):
        assert ent.channel_catalog_path(tid, tid) == []


def test_lateral_is_single_row(ent):
    path = ent.channel_catalog_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_PRO
    assert path[0]["channels"] == ent.channel_catalog()


def test_oss_to_cloud_free_lateral(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER


# ── descending mirror ───────────────────────────────────────────────────


def test_descending_path_terminates_at_to(ent):
    path = ent.channel_catalog_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[-1]["tier"] == ent.TIER_OSS
    # closest-to-from rung first
    assert (
        ent._TIER_RANK[path[0]["tier"]]
        < ent._TIER_RANK[ent.TIER_ENTERPRISE]
    )


def test_descending_terminates_at_explicit_floor(ent):
    """Asking for ``oss`` must NOT also include ``cloud_free`` (the
    other rank-0 sibling) as a terminal rung."""
    tiers = [
        r["tier"]
        for r in ent.channel_catalog_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    ]
    assert tiers[-1] == ent.TIER_OSS
    assert tiers.count(ent.TIER_OSS) == 1


# ── trial endpoint ───────────────────────────────────────────────────────


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on
    a path between purchasable tiers, but resolves as an endpoint."""
    path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL
    upward = ent.channel_catalog_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE
    downward = ent.channel_catalog_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_OSS


# ── decoupled from the resolver ──────────────────────────────────────────


def test_grace_and_enforce_yield_identical_rows(ent, enforced):
    grace_rows = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    enforced_rows = enforced.channel_catalog_path(
        enforced.TIER_OSS, enforced.TIER_ENTERPRISE
    )
    assert grace_rows == enforced_rows


# ── unknown / garbage inputs never raise ─────────────────────────────────


def test_unknown_tiers_return_none(ent):
    assert (
        ent.channel_catalog_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    )
    assert (
        ent.channel_catalog_path(ent.TIER_OSS, "still_not_a_tier") is None
    )
    assert ent.channel_catalog_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.channel_catalog_path("", "") is None
    assert ent.channel_catalog_path(None, None) is None  # type: ignore[arg-type]
    assert ent.channel_catalog_path("  ", "  ") is None
    assert ent.channel_catalog_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.channel_catalog_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_helper_swallows_synthesis_failure(monkeypatch, ent):
    """If the per-rung entitlement synthesiser blows up, the helper must
    short-circuit gracefully -- either dropping the poisoned rung or
    logging + returning ``None`` -- and must never raise (logged-
    warning + graceful fallback contract)."""

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", boom)
    # Must not raise, and must not return anything with a poisoned row.
    result = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert result is None or result == []


def test_helper_swallows_row_builder_failure(monkeypatch, ent):
    """If the per-channel row builder itself blows up, the helper must
    also short-circuit to ``None`` / empty rather than leaking."""

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_channel_spec_row", boom)
    result = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert result is None or result == []


# ── API surface ──────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert (
        client.get("/api/entitlement/channel-catalog-path").status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/channel-catalog-path?from=oss"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/channel-catalog-path?to=cloud_pro"
        ).status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/channel-catalog-path?from=oss&to=not_a_tier"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["tier"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_path_byte_equals_helper(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["path"] == ent.channel_catalog_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE
    )


def test_api_envelope_channels_lists_match_channel_catalog(client, ent):
    """Cross-check the wire envelope's per-rung ``channels`` list against
    ``/api/entitlement/channel-catalog`` -- the two channel-axis
    surfaces stay in lock-step."""
    r = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    baseline = client.get("/api/entitlement/channel-catalog").get_json()
    baseline_channels = baseline["channels"]
    for row in body["path"]:
        assert row["channels"] == baseline_channels


def test_api_404_on_resolver_failure(monkeypatch, client):
    """Force the resolver path used by the route to blow up; the route
    must short-circuit to a 404 envelope instead of leaking a 500."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "channel_catalog_path", boom)
    r = client.get(
        "/api/entitlement/channel-catalog-path?from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
