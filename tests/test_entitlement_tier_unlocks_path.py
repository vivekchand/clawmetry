"""Tests for ``clawmetry.entitlements.tier_unlocks_path(from, to)`` + the
``GET /api/entitlement/tier-unlocks-path`` endpoint.

Unlocks-focused analogue of :func:`tier_path` (full ``tier_diff`` per
rung) and :func:`capacity_diff_path` (capacity-only per rung) -- the
third member of the ``_path`` family. Lets an upgrade-walkthrough
surface render only the *newly-unlocked* features + runtimes at each
rung between any two tiers off ONE round-trip, without the noise of the
capacity axes or the symmetric ``lost_*`` lists :func:`tier_path`
carries.

Each row matches :func:`tier_unlocks`'s row shape exactly --
``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
``previous_tier_label``, ``previous_tier_rank``, ``features``,
``runtimes`` -- with ``previous_tier`` chained from the path (the
previous step), NOT the global next-lower-purchasable-tier anchor
:func:`tier_unlocks` uses. The path-chained source guarantees
``row[i]['tier'] == row[i+1]['previous_tier']`` so a consumer can fold
``features`` / ``runtimes`` across rows to reconstruct the cumulative
``tier_diff(from, to)['added_*']`` shape.

Pins:

* row shape matches singular ``tier_unlocks`` schema (down to the key set)
* ``previous_tier`` is path-chained, not the global anchor (the *one*
  semantic difference vs :func:`tier_unlocks`); ``previous_tier_*``
  fields are NEVER ``None`` (the path always has a concrete source)
* per-rung chain is continuous on the tier axis
  (``row[i]['tier'] == row[i+1]['previous_tier']``)
* rung walk is byte-stable against :func:`tier_path` (same
  ``_PURCHASABLE_TIERS`` filter + same sort + same destination-sibling
  exclusion); confirmed by extracting the rung ``to`` ids
* ascending path features + runtimes fold to the cumulative
  ``tier_diff(from, to)['added_*']`` sets
* descending path rows carry empty unlock lists (you lose things, you
  don't unlock them) but still walk the rungs so a UI keyed off rung
  shape keeps working
* identity (``from == to``) returns an empty path
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint -- excluded from walked rungs but the
  endpoint computation still resolves
* unknown / empty / garbage ids return ``None`` and never raise
* grace vs enforce yields identical rows (helper is decoupled from the
  resolved entitlement; it walks the static per-tier maps)
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


_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "previous_tier",
    "previous_tier_label",
    "previous_tier_rank",
    "features",
    "runtimes",
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
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_tier_unlocks_schema(ent):
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["features"], list)
        assert isinstance(row["runtimes"], list)


def test_previous_tier_fields_never_none_on_path(ent):
    """Singular :func:`tier_unlocks` returns ``previous_tier=None`` at the
    floor rungs (oss / cloud_free have no purchasable tier below them).
    The path variant ALWAYS has a concrete previous step (``from_tier``
    on the first row, the prior rung on later rows), so the
    ``previous_tier_*`` fields are never ``None`` -- pin this so a UI
    that strictly relies on the chained source can render confidently."""
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["previous_tier"] is not None
        assert row["previous_tier_label"] is not None
        assert row["previous_tier_rank"] is not None


def test_first_row_previous_is_from_tier(ent):
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[0]["previous_tier"] == ent.TIER_OSS
    assert path[0]["previous_tier_rank"] == ent.tier_rank(ent.TIER_OSS)


def test_chain_is_continuous_on_tier_axis(ent):
    """Each row's ``tier`` is the next row's ``previous_tier`` -- the
    same chain-property :func:`tier_path` and :func:`capacity_diff_path`
    enforce on their rows."""
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for i in range(len(path) - 1):
        assert path[i]["tier"] == path[i + 1]["previous_tier"]
        assert path[i]["tier_rank"] == path[i + 1]["previous_tier_rank"]
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must end
    exactly at ``pro`` and EXCLUDE the same-rank sibling ``cloud_pro``
    from the final rung -- same rule as :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert rungs[-1] == ent.TIER_PRO
    assert rungs.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in rungs


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings ``cloud_pro`` AND
    ``pro`` both appear because they sit strictly *between* rank-0 start
    and rank-3 destination -- same rule as :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)]
    assert ent.TIER_CLOUD_PRO in rungs
    assert ent.TIER_PRO in rungs
    assert rungs[-1] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_tier_path(ent):
    """The set of rung ``tier`` ids must match :func:`tier_path`'s set
    of rung ``to`` ids byte-for-byte -- same ``_PURCHASABLE_TIERS``
    filter + same sort + same destination-sibling exclusion."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_OSS, ent.TIER_CLOUD_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        unlocks_rungs = [r["tier"] for r in ent.tier_unlocks_path(f, t)]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert unlocks_rungs == diff_rungs


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
        assert ent.tier_unlocks_path(tid, tid) == []


def test_lateral_single_row(ent):
    """Same rank, different id -- single-row path; row carries the set
    difference between the two same-rank tier grants."""
    path = ent.tier_unlocks_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    row = path[0]
    assert row["tier"] == ent.TIER_PRO
    assert row["previous_tier"] == ent.TIER_CLOUD_PRO
    # cloud_pro and pro share their grant set, so the set-diff is empty
    assert row["features"] == []
    assert row["runtimes"] == []


def test_oss_to_cloud_free_lateral_empty_diff(ent):
    """Both rank 0 -- lateral single-row path with no unlock diff."""
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_FREE
    assert path[0]["previous_tier"] == ent.TIER_OSS
    assert path[0]["features"] == []
    assert path[0]["runtimes"] == []


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER
    assert path[0]["previous_tier"] == ent.TIER_OSS
    # every paid runtime first unlocks at Starter
    assert set(path[0]["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_ascending_path_unlocks_enterprise_at_top(ent):
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    final = path[-1]
    assert final["tier"] == ent.TIER_ENTERPRISE
    # enterprise-only features land at the terminal rung
    assert "sso" in final["features"]
    assert "audit_logs" in final["features"]


def test_descending_path_terminates_at_to_but_unlocks_are_empty(ent):
    """Descending walk still visits the rungs (so a UI keyed off rung
    shape keeps working), but each row's ``features`` / ``runtimes``
    collapse to empty lists -- you lose things, you don't unlock them."""
    path = ent.tier_unlocks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[0]["previous_tier"] == ent.TIER_ENTERPRISE
    assert path[-1]["tier"] == ent.TIER_OSS
    for row in path:
        assert row["features"] == []
        assert row["runtimes"] == []


def test_descending_terminates_at_explicit_floor(ent):
    """Asking for ``oss`` must NOT also include ``cloud_free`` (the other
    rank-0 sibling) as a terminal rung -- same rule as :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_unlocks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)]
    assert rungs[-1] == ent.TIER_OSS
    assert rungs.count(ent.TIER_OSS) == 1


def test_fold_reproduces_cumulative_added_features(ent):
    """Folding the per-step marginal unlock sets across the path must
    reproduce the cumulative ``tier_diff(from, to)['added_features']``
    set (and likewise for runtimes) -- the byte-level invariant that
    makes the path a true marginal decomposition."""
    f, t = ent.TIER_OSS, ent.TIER_ENTERPRISE
    path = ent.tier_unlocks_path(f, t)
    folded_features: set[str] = set()
    folded_runtimes: set[str] = set()
    for row in path:
        folded_features |= set(row["features"])
        folded_runtimes |= set(row["runtimes"])
    direct = ent.tier_diff(f, t)
    assert folded_features == set(direct["added_features"])
    assert folded_runtimes == set(direct["added_runtimes"])


def test_fold_handles_cloud_free_floor(ent):
    """cloud_free (rank 0) -> enterprise (rank 3) folds the same way as
    oss -> enterprise -- both floors share the same free grant so the
    cumulative ``added_*`` set is identical."""
    f, t = ent.TIER_CLOUD_FREE, ent.TIER_ENTERPRISE
    path = ent.tier_unlocks_path(f, t)
    folded_features: set[str] = set()
    for row in path:
        folded_features |= set(row["features"])
    direct = ent.tier_diff(f, t)
    assert folded_features == set(direct["added_features"])


def test_lists_are_sorted_per_row(ent):
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["features"] == sorted(row["features"])
        assert row["runtimes"] == sorted(row["runtimes"])


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on
    a path between purchasable tiers, but it IS a valid endpoint."""
    path = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL
        assert row["previous_tier"] != ent.TIER_TRIAL
    # trial as an endpoint still resolves
    upward = ent.tier_unlocks_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE
    downward = ent.tier_unlocks_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_OSS


def test_unknown_tiers_return_none(ent):
    assert ent.tier_unlocks_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    assert ent.tier_unlocks_path(ent.TIER_OSS, "still_not_a_tier") is None
    assert ent.tier_unlocks_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.tier_unlocks_path("", "") is None
    assert ent.tier_unlocks_path(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_path("  ", "  ") is None
    assert ent.tier_unlocks_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.tier_unlocks_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    """The helper is decoupled from the resolved entitlement -- it walks
    the static per-tier maps so flipping enforce on must NOT change any
    row. Pins the resolver-independence property the whole ``_path``
    family shares."""
    grace_rows = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert grace_rows == enforced_rows


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert client.get("/api/entitlement/tier-unlocks-path").status_code == 400
    assert (
        client.get("/api/entitlement/tier-unlocks-path?from=oss").status_code == 400
    )
    assert (
        client.get("/api/entitlement/tier-unlocks-path?to=cloud_pro").status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get("/api/entitlement/tier-unlocks-path?from=oss&to=not_a_tier")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE
    # row schema matches the singular endpoint
    for row in body["path"]:
        assert set(row.keys()) == _ROW_KEYS


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["tier"] == ent.TIER_OSS
    # descending: each row's unlock lists collapse to empty
    for row in body["path"]:
        assert row["features"] == []
        assert row["runtimes"] == []


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["previous_tier"] == ent.TIER_CLOUD_PRO
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_rungs_match_tier_path_route(client, ent):
    """API-level byte-equality: rung ``tier`` ids from
    ``/tier-unlocks-path`` match rung ``to`` ids from ``/tier-path``."""
    a = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["tier"] for r in a["path"]] == [r["to"] for r in b["path"]]
