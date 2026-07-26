"""Tests for ``clawmetry.entitlements.capacity_headroom_path(from, to, ...)``
+ the ``GET /api/entitlement/capacity-headroom-path`` endpoint.

Path-shaped sibling of :func:`capacity_headroom_batch` and headroom-shaped
mirror of :func:`capacity_diff_path` / :func:`tier_unlocks_path` /
:func:`tier_locks_path` / :func:`preview_path`. Where the marginal capacity
``_path`` sibling answers "what changes at each rung" and the plural
``_batch`` sibling answers "at every purchasable rung, would my usage fit",
this helper answers "at each rung on the way from A to B, given my current
usage, what would the per-axis headroom look like" -- the natural walk-
through for an upgrade-CTA "watch your headroom recover rung by rung" view.

Pins:

* per-rung row shape matches :func:`capacity_headroom_at` byte-for-byte
  (``tier`` / ``tier_label`` / ``channels`` / ``retention_days`` /
  ``nodes``) with each per-axis row matching :func:`_headroom_row`
* rung walk is byte-stable against :func:`capacity_diff_path` /
  :func:`tier_unlocks_path` / :func:`tier_locks_path` /
  :func:`preview_path` -- same ``_PURCHASABLE_TIERS`` filter + same
  sort key + same destination-sibling exclusion -- so the five path
  helpers line up rung-for-rung
* identity (``from == to``) -> ``[]``; lateral (same rank, different id)
  -> single row carrying the ``to`` tier's headroom
* trial accepted as an endpoint -- excluded from the walked rungs (not
  purchasable) but the lateral / identity branch still resolves
* unknown / empty / garbage ids return ``None`` and never raise
* per-axis "None means axis not supplied" posture propagates to every
  rung; a supplied axis is echoed on every rung
* decoupled from the resolved entitlement -- grace vs enforce yields
  byte-identical rows
* API surface: 400 on missing args, 404 on unknown ids, 200 with the
  envelope shape (incl. direction tag) on the happy path; a stray
  ``?channels=junk`` cannot silently blank the walk; API 404s instead
  of 5xxing when the inner helper blows up
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


_ROW_KEYS = {"tier", "tier_label", "channels", "retention_days", "nodes"}
_AXIS_KEYS = {
    "kind",
    "used",
    "cap",
    "remaining",
    "is_unlimited",
    "at_limit",
    "over_limit",
    "pct_used",
}
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


# ── helper-level: shape + per-row contract ────────────────────────────────


def test_returns_list(ent):
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_headroom_at_envelope_shape(ent):
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2, retention_days=5, nodes=1
    )
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        for axis in ("channels", "retention_days", "nodes"):
            assert set(row[axis].keys()) == _AXIS_KEYS


def test_tier_is_the_destination_rung(ent):
    """Each row's ``tier`` is the rung that step lands on -- matches the
    singular :func:`capacity_headroom_at` contract."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE
    for row in path:
        assert row["tier"] in ent._PURCHASABLE_TIERS


def test_each_row_byte_equal_to_headroom_at(ent):
    """The path helper is a walker over :func:`capacity_headroom_at`;
    every row must be byte-identical to a singular call for the same
    tier + axis inputs so a UI reusing the ``_at`` renderer stays in
    lock-step."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2, retention_days=5, nodes=1
    )
    for row in path:
        singular = ent.capacity_headroom_at(
            row["tier"], channels=2, retention_days=5, nodes=1
        )
        assert row == singular


# ── rung walk: byte-stable against the other _path siblings ────────────────


def test_rung_walk_byte_equal_to_capacity_diff_path(ent):
    """``capacity_headroom_path`` and ``capacity_diff_path`` walk the same
    rungs in the same order -- the headroom helper is a narrower per-tier
    projection over the same walker, so the pair stays in lock-step."""
    headroom = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    diff = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in headroom] == [r["target"] for r in diff]


def test_rung_walk_byte_equal_to_preview_path(ent):
    """Also byte-stable against the fifth ``_path`` sibling
    (:func:`preview_path`) -- pins the "five _path helpers line up rung-
    for-rung" contract."""
    headroom = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    preview = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["tier"] for r in headroom] == [r["tier"] for r in preview]


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must end
    exactly at ``pro`` and EXCLUDE the same-rank sibling ``cloud_pro``
    from the final rung -- same rule as :func:`capacity_diff_path`."""
    tiers = [
        r["tier"]
        for r in ent.capacity_headroom_path(
            ent.TIER_OSS, ent.TIER_PRO, channels=2
        )
    ]
    assert tiers[-1] == ent.TIER_PRO
    assert tiers.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in tiers


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings ``cloud_pro`` AND ``pro``
    both appear because they sit strictly *between* the rank-0 start and
    the rank-3 destination."""
    tiers = [
        r["tier"]
        for r in ent.capacity_headroom_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
        )
    ]
    assert ent.TIER_CLOUD_PRO in tiers
    assert ent.TIER_PRO in tiers
    assert tiers[-1] == ent.TIER_ENTERPRISE


# ── per-axis "None means axis not supplied" posture ───────────────────────


def test_unsupplied_axis_stays_none_on_every_rung(ent):
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    for row in path:
        assert row["channels"] is not None
        assert row["retention_days"] is None
        assert row["nodes"] is None


def test_nothing_supplied_returns_all_none_rows(ent):
    path = ent.capacity_headroom_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert len(path) >= 1
    for row in path:
        assert row["channels"] is None
        assert row["retention_days"] is None
        assert row["nodes"] is None


def test_supplied_axis_echoed_on_every_rung(ent):
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=42
    )
    for row in path:
        assert row["channels"]["used"] == 42


# ── headroom values recover / erode along the walk ────────────────────────


def test_channels_over_limit_recovers_on_upgrade_walk(ent):
    """Walking oss -> enterprise with 99 channels: the OSS floor is over-
    limit (cap=3), but every paid rung has unlimited channels so the
    ``over_limit`` flag flips off on the higher rungs."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=99
    )
    tail = [row for row in path if row["tier"] != ent.TIER_OSS]
    assert tail, "path must have at least one non-oss rung"
    for row in tail:
        assert row["channels"]["is_unlimited"] is True
        assert row["channels"]["over_limit"] is False


def test_retention_headroom_tightens_on_downgrade_walk(ent):
    """Walking enterprise -> oss with 45 days retention: enterprise is
    unlimited, but the OSS floor caps at 7 so ``over_limit`` flips on by
    the terminal rung."""
    path = ent.capacity_headroom_path(
        ent.TIER_ENTERPRISE, ent.TIER_OSS, retention_days=45
    )
    final = path[-1]
    assert final["tier"] == ent.TIER_OSS
    assert final["retention_days"]["over_limit"] is True
    assert final["retention_days"]["remaining"] == 7 - 45


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
        assert ent.capacity_headroom_path(tid, tid, channels=2) == []


def test_lateral_is_single_row(ent):
    """Same rank, different id -- one row carrying the ``to`` tier's
    headroom envelope."""
    path = ent.capacity_headroom_path(
        ent.TIER_CLOUD_PRO, ent.TIER_PRO, channels=2
    )
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_PRO
    assert path[0] == ent.capacity_headroom_at(ent.TIER_PRO, channels=2)


def test_oss_to_cloud_free_lateral(ent):
    """Both rank 0 -- lateral single-row path terminating at cloud_free."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_CLOUD_FREE, channels=2
    )
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_CLOUD_STARTER, channels=2
    )
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER


# ── trial endpoint ───────────────────────────────────────────────────────


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on a
    path between purchasable tiers, but resolves as an endpoint via the
    lateral / identity branch."""
    path = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL
    upward = ent.capacity_headroom_path(
        ent.TIER_TRIAL, ent.TIER_ENTERPRISE, channels=2
    )
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE
    downward = ent.capacity_headroom_path(
        ent.TIER_TRIAL, ent.TIER_OSS, channels=2
    )
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_OSS


# ── decoupled from the resolver ──────────────────────────────────────────


def test_grace_and_enforce_yield_identical_rows(ent, enforced):
    """The path is built off the static per-tier maps, not the resolved
    entitlement -- flipping enforce on must NOT change the rows."""
    grace_rows = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2, retention_days=5, nodes=1
    )
    enforced_rows = enforced.capacity_headroom_path(
        enforced.TIER_OSS,
        enforced.TIER_ENTERPRISE,
        channels=2,
        retention_days=5,
        nodes=1,
    )
    assert grace_rows == enforced_rows


# ── unknown / garbage inputs never raise ─────────────────────────────────


def test_unknown_tiers_return_none(ent):
    assert (
        ent.capacity_headroom_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    )
    assert (
        ent.capacity_headroom_path(ent.TIER_OSS, "still_not_a_tier") is None
    )
    assert ent.capacity_headroom_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.capacity_headroom_path("", "") is None
    assert ent.capacity_headroom_path(None, None) is None  # type: ignore[arg-type]
    assert ent.capacity_headroom_path("  ", "  ") is None
    assert ent.capacity_headroom_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )
    b = ent.capacity_headroom_path(
        "  OSS ", " ENTERPRISE  ", channels=2
    )
    assert a == b


def test_helper_swallows_walker_failure(monkeypatch, ent):
    """A blow-up in the inner ``capacity_headroom_at`` walker must short-
    circuit the helper to ``None`` (logged-warning + graceful fallback
    contract)."""

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_PURCHASABLE_TIERS", None)  # type: ignore[misc]
    assert (
        ent.capacity_headroom_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
        )
        is None
    )


# ── API surface ──────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert (
        client.get("/api/entitlement/capacity-headroom-path").status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/capacity-headroom-path?from=oss"
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/api/entitlement/capacity-headroom-path?to=cloud_pro"
        ).status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-path?from=oss&to=not_a_tier"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&channels=2"
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
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}&channels=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["tier"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}&channels=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}&channels=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_path_byte_equals_helper(client, ent):
    """The wrapper endpoint must echo the module helper's rows verbatim --
    no client-side re-derivation in the route, otherwise the singular
    ``capacity_headroom_at`` posture and the path rows can drift."""
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&channels=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["path"] == ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=2
    )


def test_api_bad_axis_collapses_to_none_on_every_row(client, ent):
    """A stray ``?channels=junk`` cannot silently blank the whole walk --
    the bad axis short-circuits to ``None`` on every rung (matches the
    ``/capacity-headroom-batch`` posture)."""
    r = client.get(
        "/api/entitlement/capacity-headroom-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&channels=junk"
    )
    assert r.status_code == 200
    body = r.get_json()
    for row in body["path"]:
        assert row["channels"] is None


def test_api_404_on_resolver_failure(monkeypatch, client):
    """Force the resolver path used by the route to blow up; the route
    must short-circuit to a 404 envelope instead of leaking a 500 to
    the pricing page."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "capacity_headroom_path", boom)
    r = client.get(
        "/api/entitlement/capacity-headroom-path?from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
