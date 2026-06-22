"""Tests for ``clawmetry.entitlements.tier_path(from, to)`` + the
``GET /api/entitlement/tier-path`` endpoint.

Path analogue of :func:`tier_diff`: generalises :func:`upgrade_path` /
:func:`downgrade_path` (which pin one endpoint to the resolved
entitlement) to ANY pair of known tiers so a "Compare A vs B"
pricing-page widget can render the rung sequence between any two tiers
without first switching the resolver. Each row in the returned path is
a full :func:`tier_diff` payload between the previous step in the path
(or ``from`` for the first row) and the current rung -- so each row is a
marginal step diff and a consumer can fold the rows to reconstruct the
cumulative ``tier_diff(from, to)`` shape.

Pins:

* ascending path walks every purchasable rung strictly between ``from``
  and ``to`` and ends AT ``to`` (not a same-rank sibling of ``to``)
* descending path mirrors it (closest-to-from rung first, terminal rung
  is exactly ``to``)
* same-rank siblings strictly *between* the endpoints both appear
* identity (``from == to``) returns an empty path
* lateral (same rank, different id) returns a single-row path that
  byte-equals ``[tier_diff(from, to)]``
* each row is a full ``tier_diff`` payload (every key present) and the
  per-step ``from`` chains: row[i]["to"] == row[i+1]["from"]
* folding the marginal step deltas reproduces the cumulative
  ``tier_diff(from, to)`` feature + runtime sets
* trial accepted as an endpoint -- excluded from the walked rungs (not
  purchasable) but the endpoint computation still resolves
* unknown / empty / garbage ids return ``None`` and never raise
* API surface: 400 on missing args, 404 on unknown ids, 200 with the
  envelope shape on the happy path (incl. direction tag)
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


_DIFF_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
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


# ── helper-level: shape + invariants ─────────────────────────────────────────


def test_returns_list(ent):
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_is_full_tier_diff_payload(ent):
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _DIFF_KEYS
        cc = row["capacity_changes"]
        assert set(cc.keys()) == {"channel_limit", "retention_days", "node_limit"}
        for axis in cc.values():
            assert set(axis.keys()) == {
                "before",
                "after",
                "delta",
                "unlocked",
                "locked",
            }


def test_chain_is_continuous(ent):
    """Each row's ``to`` is the next row's ``from`` (marginal-step chain)."""
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[0]["from"] == ent.TIER_OSS
    for i in range(len(path) - 1):
        assert path[i]["to"] == path[i + 1]["from"]
    assert path[-1]["to"] == ent.TIER_ENTERPRISE


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must end
    exactly at ``pro`` and EXCLUDE the same-rank sibling ``cloud_pro`` from
    the final rung -- same-rank siblings of the destination are filtered
    out so the path terminates exactly at ``to``."""
    rungs = [r["to"] for r in ent.tier_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert rungs[-1] == ent.TIER_PRO
    assert rungs.count(ent.TIER_PRO) == 1
    # cloud_pro shares rank 2 with the destination -> excluded from this path
    assert ent.TIER_CLOUD_PRO not in rungs


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings cloud_pro AND pro both
    appear because they sit strictly *between* the rank-0 start and the
    rank-3 destination -- a pricing UI keyed off tier id keeps working."""
    rungs = [r["to"] for r in ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)]
    assert ent.TIER_CLOUD_PRO in rungs
    assert ent.TIER_PRO in rungs
    assert rungs[-1] == ent.TIER_ENTERPRISE


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
        assert ent.tier_path(tid, tid) == []


def test_lateral_is_single_row_byte_equal_to_tier_diff(ent):
    """Same rank, different id -- one row, byte-equal to a direct
    ``tier_diff`` call."""
    path = ent.tier_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    assert path[0] == ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert path[0]["direction"] == "lateral"


def test_oss_to_cloud_free_lateral(ent):
    """Both rank 0 -- lateral single-row path."""
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["direction"] == "lateral"
    assert path[0]["from"] == ent.TIER_OSS
    assert path[0]["to"] == ent.TIER_CLOUD_FREE


def test_descending_path_terminates_at_to(ent):
    path = ent.tier_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[0]["from"] == ent.TIER_ENTERPRISE
    assert path[-1]["to"] == ent.TIER_OSS
    # closest-to-from rung first: row 0's destination rank must be
    # strictly LESS than enterprise (rank 3) but at most the next rank down.
    assert path[0]["to_rank"] < path[0]["from_rank"]


def test_descending_terminates_at_explicit_floor(ent):
    """Asking for ``oss`` must NOT also include ``cloud_free`` (the other
    rank-0 sibling) as a terminal rung -- same rule as the ascending case."""
    rungs = [r["to"] for r in ent.tier_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)]
    assert rungs[-1] == ent.TIER_OSS
    assert rungs.count(ent.TIER_OSS) == 1


def test_fold_reproduces_cumulative_tier_diff(ent):
    """Folding the per-step marginal deltas across the path must reproduce
    the cumulative ``tier_diff(from, to)`` feature + runtime sets."""
    f, t = ent.TIER_OSS, ent.TIER_ENTERPRISE
    path = ent.tier_path(f, t)
    cum_added_features: set[str] = set()
    cum_lost_features: set[str] = set()
    cum_added_runtimes: set[str] = set()
    cum_lost_runtimes: set[str] = set()
    for row in path:
        cum_added_features |= set(row["added_features"])
        cum_lost_features |= set(row["lost_features"])
        cum_added_runtimes |= set(row["added_runtimes"])
        cum_lost_runtimes |= set(row["lost_runtimes"])
    direct = ent.tier_diff(f, t)
    assert cum_added_features >= set(direct["added_features"])
    assert cum_added_runtimes >= set(direct["added_runtimes"])
    # going ascending only, no losses anywhere on the path
    assert cum_lost_features == set()
    assert cum_lost_runtimes == set()


def test_ascending_path_unlocks_enterprise_at_top(ent):
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    final = path[-1]
    assert final["to"] == ent.TIER_ENTERPRISE
    # enterprise-only features land at the terminal rung
    assert "sso" in final["added_features"]
    assert "audit_logs" in final["added_features"]


def test_descending_path_loses_paid_runtimes_at_floor(ent):
    path = ent.tier_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    final = path[-1]
    assert final["to"] == ent.TIER_OSS
    # paid runtimes vanish by the time we reach the floor
    for rt in ("claude_code", "codex", "cursor"):
        assert rt in final["lost_runtimes"]


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on a
    path between purchasable tiers."""
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["to"] != ent.TIER_TRIAL
        assert row["from"] != ent.TIER_TRIAL
    # but trial AS an endpoint resolves
    upward = ent.tier_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["to"] == ent.TIER_ENTERPRISE
    downward = ent.tier_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["to"] == ent.TIER_OSS


def test_unknown_tiers_return_none(ent):
    assert ent.tier_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    assert ent.tier_path(ent.TIER_OSS, "still_not_a_tier") is None
    assert ent.tier_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.tier_path("", "") is None
    assert ent.tier_path(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_path("  ", "  ") is None
    assert ent.tier_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.tier_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.tier_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["from"] == ent.TIER_OSS
    assert path[0]["to"] == ent.TIER_CLOUD_STARTER
    assert path[0]["direction"] == "upgrade"


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert client.get("/api/entitlement/tier-path").status_code == 400
    assert client.get("/api/entitlement/tier-path?from=oss").status_code == 400
    assert client.get("/api/entitlement/tier-path?to=cloud_pro").status_code == 400


def test_api_404_on_unknown_tier(client):
    r = client.get("/api/entitlement/tier-path?from=oss&to=not_a_tier")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["to"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["to"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["from"] == ent.TIER_CLOUD_PRO
    assert body["path"][0]["to"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["to"] == ent.TIER_ENTERPRISE
