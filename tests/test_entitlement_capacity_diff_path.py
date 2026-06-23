"""Tests for ``clawmetry.entitlements.capacity_diff_path(from, to)`` + the
``GET /api/entitlement/capacity-diff-path`` endpoint.

Capacity-only path companion to :func:`tier_path`. Where the parent helper
returns the full :func:`tier_diff` payload per rung (added / lost features +
runtimes + ``capacity_changes``), this helper returns just the singular
:func:`capacity_diff` shape per rung (``target``, ``channel_limit``,
``retention_days``, ``node_limit``) so a capacity-only pricing widget can
render the per-rung channel / retention / node transitions off **one**
round-trip without paying for the feature / runtime set diff on every row.

Pins:

* same rung walk as :func:`tier_path` -- every purchasable tier strictly
  between ``from`` and ``to`` plus the destination itself, in tier-rank
  order; same-rank siblings of the destination excluded
* each row matches the singular :func:`capacity_diff` row shape exactly
  (``target``, ``channel_limit``, ``retention_days``, ``node_limit``)
  with the full ``{before, after, delta, unlocked, locked}`` triple per
  axis -- byte-stable against an arbitrary-endpoint call
* row chain is continuous on every axis: row[i].axis.after ==
  row[i+1].axis.before so a consumer can fold to reconstruct the
  cumulative ``tier_diff(from, to)['capacity_changes']`` shape
* identity (``from == to``) -> ``[]``; lateral (same rank, different id)
  -> single row carrying the from->to transition
* trial accepted as an endpoint -- excluded from the walked rungs (not
  purchasable) but the endpoint computation still resolves
* unknown / empty / garbage ids return ``None`` and never raise
* path is decoupled from the resolved entitlement -- grace vs enforce
  must NOT change the rows (same posture under both)
* API surface: 400 on missing args, 404 on unknown ids, 200 with the
  envelope shape on the happy path (incl. direction tag)
* API 404s instead of 5xxing when the inner helper blows up
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


_ROW_KEYS = {"target", "channel_limit", "retention_days", "node_limit"}
_AXIS_KEYS = {"before", "after", "delta", "unlocked", "locked"}
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
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_has_singular_capacity_diff_shape(ent):
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert set(row[axis].keys()) == _AXIS_KEYS


def test_target_is_the_destination_rung(ent):
    """Each row's ``target`` is the rung that step lands on (matches the
    singular ``capacity_diff(target)`` contract)."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[-1]["target"] == ent.TIER_ENTERPRISE
    for row in path:
        assert row["target"] in ent._PURCHASABLE_TIERS


# ── rung walk: same shape as tier_path ────────────────────────────────────


def test_chain_is_continuous_per_axis(ent):
    """row[i].axis.after == row[i+1].axis.before for every axis -- the
    marginal-step chain a consumer folds to reproduce the cumulative
    ``tier_diff(from, to)['capacity_changes']`` shape."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        for i in range(len(path) - 1):
            assert path[i][axis]["after"] == path[i + 1][axis]["before"]


def test_first_row_before_matches_from_tier_caps(ent):
    """First rung's ``before`` is the ``from`` tier's static caps (NOT the
    resolved entitlement's), so the path is hypothetical and decoupled
    from the resolver."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    first = path[0]
    assert first["channel_limit"]["before"] == ent._TIER_CHANNEL_LIMIT[ent.TIER_OSS]
    assert first["retention_days"]["before"] == ent._TIER_RETENTION_DAYS[ent.TIER_OSS]
    assert first["node_limit"]["before"] == ent._TIER_NODE_LIMIT[ent.TIER_OSS]


def test_last_row_after_matches_to_tier_caps(ent):
    """Terminal rung's ``after`` is the ``to`` tier's static caps."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    last = path[-1]
    assert last["channel_limit"]["after"] == ent._TIER_CHANNEL_LIMIT[ent.TIER_ENTERPRISE]
    assert (
        last["retention_days"]["after"] == ent._TIER_RETENTION_DAYS[ent.TIER_ENTERPRISE]
    )
    assert last["node_limit"]["after"] == ent._TIER_NODE_LIMIT[ent.TIER_ENTERPRISE]


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must end
    exactly at ``pro`` and EXCLUDE the same-rank sibling ``cloud_pro``
    from the final rung -- same rule as ``tier_path``."""
    targets = [r["target"] for r in ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert targets[-1] == ent.TIER_PRO
    assert targets.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in targets


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings cloud_pro AND pro both
    appear because they sit strictly *between* the rank-0 start and the
    rank-3 destination."""
    targets = [
        r["target"]
        for r in ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    ]
    assert ent.TIER_CLOUD_PRO in targets
    assert ent.TIER_PRO in targets
    assert targets[-1] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_equal_to_tier_path(ent):
    """``capacity_diff_path`` and ``tier_path`` must agree on which rungs
    to visit and in which order -- the capacity helper is just a narrower
    projection of the full-diff walk, so the pair stays in lock-step."""
    cap = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    full = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert [r["target"] for r in cap] == [r["to"] for r in full]


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
        assert ent.capacity_diff_path(tid, tid) == []


def test_lateral_is_single_row(ent):
    """Same rank, different id -- one row carrying the from->to transition.
    Note: lateral capacity transitions on the current ladder are no-ops
    (all paid tiers share unlimited channel/node caps), so this primarily
    pins the row count + endpoint identity, not the delta shape."""
    path = ent.capacity_diff_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    assert path[0]["target"] == ent.TIER_PRO
    # before-side reads off the from tier, after-side off the to tier
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert path[0][axis]["before"] == getattr(ent, f"_TIER_{axis.upper()}").get(
            ent.TIER_CLOUD_PRO,
            None,
        )
        assert path[0][axis]["after"] == getattr(ent, f"_TIER_{axis.upper()}").get(
            ent.TIER_PRO,
            None,
        )


def test_oss_to_cloud_free_lateral(ent):
    """Both rank 0 -- lateral single-row path."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["target"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["target"] == ent.TIER_CLOUD_STARTER
    # channels go from finite (3) to unlimited -- unlocked flag flips True
    assert path[0]["channel_limit"]["unlocked"] is True
    assert path[0]["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT
    assert path[0]["channel_limit"]["after"] is None


# ── descending mirror ───────────────────────────────────────────────────


def test_descending_path_terminates_at_to(ent):
    path = ent.capacity_diff_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[-1]["target"] == ent.TIER_OSS
    # closest-to-from rung first
    assert ent._TIER_RANK[path[0]["target"]] < ent._TIER_RANK[ent.TIER_ENTERPRISE]


def test_descending_terminates_at_explicit_floor(ent):
    """Asking for ``oss`` must NOT also include ``cloud_free`` (the other
    rank-0 sibling) as a terminal rung."""
    targets = [
        r["target"]
        for r in ent.capacity_diff_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    ]
    assert targets[-1] == ent.TIER_OSS
    assert targets.count(ent.TIER_OSS) == 1


def test_descending_chain_is_continuous(ent):
    path = ent.capacity_diff_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        for i in range(len(path) - 1):
            assert path[i][axis]["after"] == path[i + 1][axis]["before"]


def test_descending_loses_channel_cap_at_floor(ent):
    """Walking enterprise -> oss the channel cap goes unlimited -> 3 by the
    floor rung; the ``locked`` flag flips True there (unlimited becoming
    finite)."""
    path = ent.capacity_diff_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    final = path[-1]
    assert final["target"] == ent.TIER_OSS
    assert final["channel_limit"]["locked"] is True
    assert final["channel_limit"]["before"] is None
    assert final["channel_limit"]["after"] == ent._FREE_CHANNEL_LIMIT


# ── trial endpoint ───────────────────────────────────────────────────────


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on a
    path between purchasable tiers, but resolves as an endpoint."""
    path = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["target"] != ent.TIER_TRIAL
    upward = ent.capacity_diff_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["target"] == ent.TIER_ENTERPRISE
    downward = ent.capacity_diff_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["target"] == ent.TIER_OSS


# ── decoupled from the resolver ──────────────────────────────────────────


def test_grace_and_enforce_yield_identical_rows(ent, enforced):
    """The path is built off the static per-tier maps, not the resolved
    entitlement -- flipping enforce on must NOT change the rows."""
    grace_rows = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    enforced_rows = enforced.capacity_diff_path(
        enforced.TIER_OSS, enforced.TIER_ENTERPRISE
    )
    assert grace_rows == enforced_rows


# ── fold reproduces cumulative tier_diff capacity ────────────────────────


def test_fold_matches_cumulative_tier_diff_capacity(ent):
    """Folding the per-step marginal capacity rows reproduces the cumulative
    ``tier_diff(from, to)['capacity_changes']`` after/before pair."""
    f, t = ent.TIER_OSS, ent.TIER_ENTERPRISE
    path = ent.capacity_diff_path(f, t)
    direct = ent.tier_diff(f, t)["capacity_changes"]
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert path[0][axis]["before"] == direct[axis]["before"]
        assert path[-1][axis]["after"] == direct[axis]["after"]


# ── unknown / garbage inputs never raise ─────────────────────────────────


def test_unknown_tiers_return_none(ent):
    assert ent.capacity_diff_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    assert ent.capacity_diff_path(ent.TIER_OSS, "still_not_a_tier") is None
    assert ent.capacity_diff_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.capacity_diff_path("", "") is None
    assert ent.capacity_diff_path(None, None) is None  # type: ignore[arg-type]
    assert ent.capacity_diff_path("  ", "  ") is None
    assert ent.capacity_diff_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.capacity_diff_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_helper_swallows_resolver_failure(monkeypatch, ent):
    """A blow-up in the inner row builder must short-circuit the helper to
    ``None`` (logged-warning + graceful fallback contract)."""

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_capacity_row", boom)
    assert ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE) is None


# ── API surface ──────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert (
        client.get("/api/entitlement/capacity-diff-path").status_code == 400
    )
    assert (
        client.get("/api/entitlement/capacity-diff-path?from=oss").status_code == 400
    )
    assert (
        client.get("/api/entitlement/capacity-diff-path?to=cloud_pro").status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/capacity-diff-path?from=oss&to=not_a_tier"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["target"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["target"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["target"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["target"] == ent.TIER_ENTERPRISE


def test_api_path_byte_equals_helper(client, ent):
    """The wrapper endpoint must echo the module helper's rows verbatim --
    no client-side re-derivation in the route, otherwise the singular
    capacity_diff posture and the path rows can drift."""
    r = client.get(
        "/api/entitlement/capacity-diff-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["path"] == ent.capacity_diff_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)


def test_api_404_on_resolver_failure(monkeypatch, client):
    """Force the resolver path used by the route to blow up; the route
    must short-circuit to a 404 envelope instead of leaking a 500 to
    the pricing page."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "capacity_diff_path", boom)
    r = client.get(
        "/api/entitlement/capacity-diff-path?from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
