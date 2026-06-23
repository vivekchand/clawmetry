"""Tests for ``clawmetry.entitlements.tier_locks_path(from, to)`` + the
``GET /api/entitlement/tier-locks-path`` endpoint.

Marginal-loss mirror of :func:`tier_unlocks_path` and the fourth member
of the ``_path`` family alongside :func:`tier_path` (full ``tier_diff``
per rung), :func:`capacity_diff_path` (capacity-only per rung), and
:func:`tier_unlocks_path` (marginal grant per rung). Lets a downgrade-
walkthrough surface render only the *newly-lost* features + runtimes at
each rung between any two tiers off ONE round-trip, without the noise of
the capacity axes or the symmetric ``added_*`` lists :func:`tier_path`
carries.

Each row matches :func:`tier_locks`'s row shape exactly -- ``tier``,
``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
``next_tier_rank``, ``lost_features``, ``lost_runtimes`` -- with
``next_tier`` chained from the path (the previous step), NOT the global
next-higher-purchasable-tier anchor :func:`tier_locks` uses. The path-
chained source guarantees ``row[i]['tier'] == row[i+1]['next_tier']`` so
a consumer can fold ``lost_features`` / ``lost_runtimes`` across rows to
reconstruct the cumulative ``tier_diff(from, to)['lost_*']`` shape.

Pins:

* row shape matches singular ``tier_locks`` schema (down to the key set)
* ``next_tier`` is path-chained, not the global anchor (the *one*
  semantic difference vs :func:`tier_locks`); ``next_tier_*`` fields are
  NEVER ``None`` (the path always has a concrete source step)
* per-rung chain is continuous on the tier axis
  (``row[i]['tier'] == row[i+1]['next_tier']``)
* rung walk is byte-stable against :func:`tier_path` and
  :func:`tier_unlocks_path` (same ``_PURCHASABLE_TIERS`` filter + same
  sort + same destination-sibling exclusion); confirmed by extracting
  the rung ``to`` ids
* descending path lost_features + lost_runtimes fold to the cumulative
  ``tier_diff(from, to)['lost_*']`` sets
* ascending path rows carry empty loss lists (you gain things, you
  don't lose them) but still walk the rungs so a UI keyed off rung
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
    "next_tier",
    "next_tier_label",
    "next_tier_rank",
    "lost_features",
    "lost_runtimes",
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
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_tier_locks_schema(ent):
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["lost_features"], list)
        assert isinstance(row["lost_runtimes"], list)


def test_next_tier_fields_never_none_on_path(ent):
    """Singular :func:`tier_locks` returns ``next_tier=None`` at the
    ceiling rung (Enterprise has no purchasable tier above it). The
    path variant ALWAYS has a concrete previous step (``from_tier`` on
    the first row, the prior rung on later rows), so the ``next_tier_*``
    fields are never ``None`` -- pin this so a UI that strictly relies
    on the chained source can render confidently."""
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for row in path:
        assert row["next_tier"] is not None
        assert row["next_tier_label"] is not None
        assert row["next_tier_rank"] is not None


def test_first_row_next_is_from_tier(ent):
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert path[0]["next_tier"] == ent.TIER_ENTERPRISE
    assert path[0]["next_tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)


def test_chain_is_continuous_on_tier_axis(ent):
    """Each row's ``tier`` is the next row's ``next_tier`` -- the same
    chain-property :func:`tier_path`, :func:`capacity_diff_path`, and
    :func:`tier_unlocks_path` enforce on their rows."""
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for i in range(len(path) - 1):
        assert path[i]["tier"] == path[i + 1]["next_tier"]
        assert path[i]["tier_rank"] == path[i + 1]["next_tier_rank"]
    assert path[-1]["tier"] == ent.TIER_OSS


def test_path_terminates_at_to_not_a_sibling(ent):
    """``oss`` and ``cloud_free`` share rank 0; asking for ``oss`` must
    end exactly at ``oss`` and EXCLUDE the same-rank sibling
    ``cloud_free`` from the final rung -- same rule as
    :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)]
    assert rungs[-1] == ent.TIER_OSS
    assert rungs.count(ent.TIER_OSS) == 1
    assert ent.TIER_CLOUD_FREE not in rungs


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking enterprise -> oss: rank-2 siblings ``pro`` AND
    ``cloud_pro`` both appear because they sit strictly *between* rank-3
    start and rank-0 destination -- same rule as :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)]
    assert ent.TIER_CLOUD_PRO in rungs
    assert ent.TIER_PRO in rungs
    assert rungs[-1] == ent.TIER_OSS


def test_rung_walk_byte_stable_against_tier_path(ent):
    """The set of rung ``tier`` ids must match :func:`tier_path`'s set
    of rung ``to`` ids byte-for-byte -- same ``_PURCHASABLE_TIERS``
    filter + same sort + same destination-sibling exclusion."""
    for f, t in (
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_CLOUD_PRO, ent.TIER_OSS),
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_TRIAL, ent.TIER_OSS),
    ):
        locks_rungs = [r["tier"] for r in ent.tier_locks_path(f, t)]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert locks_rungs == diff_rungs


def test_rung_walk_byte_stable_against_tier_unlocks_path(ent):
    """The set of rung ``tier`` ids must also match
    :func:`tier_unlocks_path`'s set of rung ``tier`` ids byte-for-byte
    -- pins the rung walk against the other ``_path`` family members so
    the four endpoints stay in lockstep."""
    for f, t in (
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_CLOUD_PRO, ent.TIER_OSS),
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_TRIAL, ent.TIER_OSS),
    ):
        locks_rungs = [r["tier"] for r in ent.tier_locks_path(f, t)]
        unlocks_rungs = [r["tier"] for r in ent.tier_unlocks_path(f, t)]
        assert locks_rungs == unlocks_rungs


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
        assert ent.tier_locks_path(tid, tid) == []


def test_lateral_single_row(ent):
    """Same rank, different id -- single-row path; row carries the set
    difference (``from`` minus ``to``) between the two same-rank tier
    grants."""
    path = ent.tier_locks_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    row = path[0]
    assert row["tier"] == ent.TIER_PRO
    assert row["next_tier"] == ent.TIER_CLOUD_PRO
    # cloud_pro and pro share their grant set, so the set-diff is empty
    assert row["lost_features"] == []
    assert row["lost_runtimes"] == []


def test_cloud_free_to_oss_lateral_empty_diff(ent):
    """Both rank 0 -- lateral single-row path with no loss diff."""
    path = ent.tier_locks_path(ent.TIER_CLOUD_FREE, ent.TIER_OSS)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_OSS
    assert path[0]["next_tier"] == ent.TIER_CLOUD_FREE
    assert path[0]["lost_features"] == []
    assert path[0]["lost_runtimes"] == []


def test_adjacent_step_is_one_row(ent):
    """cloud_starter (rank 1) -> oss (rank 0) is a single rank-down
    step. Every paid runtime first appears at Starter, so the drop to
    the floor loses every paid runtime in one rung."""
    path = ent.tier_locks_path(ent.TIER_CLOUD_STARTER, ent.TIER_OSS)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_OSS
    assert path[0]["next_tier"] == ent.TIER_CLOUD_STARTER
    assert set(path[0]["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_descending_path_loses_enterprise_at_top_step(ent):
    """The first rung of an enterprise -> oss descent is the one that
    sheds the enterprise-only features (``sso`` + ``audit_logs``)."""
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    first = path[0]
    assert first["next_tier"] == ent.TIER_ENTERPRISE
    assert "sso" in first["lost_features"]
    assert "audit_logs" in first["lost_features"]


def test_ascending_path_terminates_at_to_but_losses_are_empty(ent):
    """Ascending walk still visits the rungs (so a UI keyed off rung
    shape keeps working), but each row's ``lost_features`` /
    ``lost_runtimes`` collapse to empty lists -- you gain things, you
    don't lose them."""
    path = ent.tier_locks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[0]["next_tier"] == ent.TIER_OSS
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE
    for row in path:
        assert row["lost_features"] == []
        assert row["lost_runtimes"] == []


def test_ascending_terminates_at_explicit_ceiling(ent):
    """Asking for ``pro`` must NOT also include ``cloud_pro`` (the other
    rank-2 sibling) as a terminal rung -- same rule as
    :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.tier_locks_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert rungs[-1] == ent.TIER_PRO
    assert rungs.count(ent.TIER_PRO) == 1


def test_fold_reproduces_cumulative_lost_features(ent):
    """Folding the per-step marginal loss sets across the path must
    reproduce the cumulative ``tier_diff(from, to)['lost_features']``
    set (and likewise for runtimes) -- the byte-level invariant that
    makes the path a true marginal decomposition. Mirror of
    :func:`tier_unlocks_path`'s ``added_*`` fold."""
    f, t = ent.TIER_ENTERPRISE, ent.TIER_OSS
    path = ent.tier_locks_path(f, t)
    folded_features: set[str] = set()
    folded_runtimes: set[str] = set()
    for row in path:
        folded_features |= set(row["lost_features"])
        folded_runtimes |= set(row["lost_runtimes"])
    direct = ent.tier_diff(f, t)
    assert folded_features == set(direct["lost_features"])
    assert folded_runtimes == set(direct["lost_runtimes"])


def test_fold_handles_cloud_free_floor(ent):
    """enterprise (rank 3) -> cloud_free (rank 0) folds the same way as
    enterprise -> oss -- both floors share the same free grant so the
    cumulative ``lost_*`` set is identical."""
    f, t = ent.TIER_ENTERPRISE, ent.TIER_CLOUD_FREE
    path = ent.tier_locks_path(f, t)
    folded_features: set[str] = set()
    for row in path:
        folded_features |= set(row["lost_features"])
    direct = ent.tier_diff(f, t)
    assert folded_features == set(direct["lost_features"])


def test_set_identity_with_unlocks_path_swap(ent):
    """Set-identity mirror of :func:`tier_diff`'s swap invariant: the
    cumulative ``lost_*`` fold of ``tier_locks_path(X, Y)`` byte-equals
    the cumulative ``added_*`` fold of ``tier_unlocks_path(Y, X)``. The
    two ``_path`` family members carry the same information from
    opposite ends -- pin this so a future reshuffle of the tier grant
    sets cannot silently desync them."""
    f, t = ent.TIER_ENTERPRISE, ent.TIER_OSS
    locks = ent.tier_locks_path(f, t)
    unlocks = ent.tier_unlocks_path(t, f)
    locks_feats: set[str] = set()
    locks_runtimes: set[str] = set()
    for row in locks:
        locks_feats |= set(row["lost_features"])
        locks_runtimes |= set(row["lost_runtimes"])
    unlocks_feats: set[str] = set()
    unlocks_runtimes: set[str] = set()
    for row in unlocks:
        unlocks_feats |= set(row["features"])
        unlocks_runtimes |= set(row["runtimes"])
    assert locks_feats == unlocks_feats
    assert locks_runtimes == unlocks_runtimes


def test_lists_are_sorted_per_row(ent):
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for row in path:
        assert row["lost_features"] == sorted(row["lost_features"])
        assert row["lost_runtimes"] == sorted(row["lost_runtimes"])


def test_trial_excluded_from_walked_rungs_but_valid_endpoint(ent):
    """``trial`` is not purchasable -- it must never appear as a stop on
    a path between purchasable tiers, but it IS a valid endpoint."""
    path = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL
        assert row["next_tier"] != ent.TIER_TRIAL
    # trial as an endpoint still resolves
    downward = ent.tier_locks_path(ent.TIER_TRIAL, ent.TIER_OSS)
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_OSS
    upward = ent.tier_locks_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE


def test_unknown_tiers_return_none(ent):
    assert ent.tier_locks_path("not_a_tier", ent.TIER_OSS) is None
    assert ent.tier_locks_path(ent.TIER_ENTERPRISE, "still_not_a_tier") is None
    assert ent.tier_locks_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.tier_locks_path("", "") is None
    assert ent.tier_locks_path(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_locks_path("  ", "  ") is None
    assert ent.tier_locks_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    b = ent.tier_locks_path(" ENTERPRISE  ", "  OSS ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    """The helper is decoupled from the resolved entitlement -- it walks
    the static per-tier maps so flipping enforce on must NOT change any
    row. Pins the resolver-independence property the whole ``_path``
    family shares."""
    grace_rows = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert grace_rows == enforced_rows


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert client.get("/api/entitlement/tier-locks-path").status_code == 400
    assert (
        client.get("/api/entitlement/tier-locks-path?from=enterprise").status_code
        == 400
    )
    assert (
        client.get("/api/entitlement/tier-locks-path?to=oss").status_code == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get("/api/entitlement/tier-locks-path?from=enterprise&to=not_a_tier")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_ENTERPRISE
    assert body["to"] == ent.TIER_OSS
    assert body["direction"] == "downgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["tier"] == ent.TIER_OSS
    # row schema matches the singular endpoint
    for row in body["path"]:
        assert set(row.keys()) == _ROW_KEYS


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "upgrade"
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE
    # ascending: each row's loss lists collapse to empty
    for row in body["path"]:
        assert row["lost_features"] == []
        assert row["lost_runtimes"] == []


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["next_tier"] == ent.TIER_CLOUD_PRO
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_TRIAL}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_OSS


def test_api_rungs_match_tier_path_route(client, ent):
    """API-level byte-equality: rung ``tier`` ids from
    ``/tier-locks-path`` match rung ``to`` ids from ``/tier-path``."""
    a = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    ).get_json()
    assert [r["tier"] for r in a["path"]] == [r["to"] for r in b["path"]]


def test_api_rungs_match_tier_unlocks_path_route(client, ent):
    """API-level byte-equality: rung ``tier`` ids from
    ``/tier-locks-path`` match rung ``tier`` ids from
    ``/tier-unlocks-path`` -- the two locks/unlocks ``_path`` siblings
    walk identical rungs (they only differ on the per-row payload)."""
    a = client.get(
        f"/api/entitlement/tier-locks-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    ).get_json()
    assert [r["tier"] for r in a["path"]] == [r["tier"] for r in b["path"]]


def test_api_garbage_query_never_5xx(client):
    """A garbage-query sweep must never 5xx -- a downgrade-warning surface
    must keep rendering instead of breaking."""
    for f, t in (
        ("", ""),
        ("nope", "nope"),
        ("oss", "still_not"),
        ("not_a_tier", "oss"),
        ("%%%", "***"),
    ):
        r = client.get(
            f"/api/entitlement/tier-locks-path?from={f}&to={t}"
        )
        assert r.status_code < 500
