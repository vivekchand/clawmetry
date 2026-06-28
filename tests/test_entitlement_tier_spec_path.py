"""Tests for ``clawmetry.entitlements.tier_spec_path(from, to)`` + the
``GET /api/entitlement/tier-spec-path`` endpoint.

Spec-shaped sibling of :func:`tier_path` (full ``tier_diff`` per rung),
:func:`capacity_diff_path` (capacity-only per rung),
:func:`tier_unlocks_path` (marginal grants per rung),
:func:`tier_locks_path` (marginal losses per rung), and
:func:`preview_path` (cumulative ``Entitlement.to_dict`` per rung) -- the
spec-shaped member of the ``_path`` family, the path-shaped sibling of
:func:`tier_spec_at_batch` (fixed-source what-if matrix) and the bulk
what-if cousin of :func:`tier_spec_at`. Lets a pricing-comparison
"compare A vs B" surface render the slim catalogue-shaped descriptor
(``id``, ``label``, ``is_paid``, ``is_current``, ``rank``,
``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
``node_limit``, ``features``, ``runtimes``) at every rung between any
two tiers off ONE round-trip, without folding marketing fields
(``is_paid``, ``label``, ``unlocks_paid_runtimes``) back in from a
separate ``/tier-catalog`` lookup the way a ``/preview-path`` row
forces.

Pins:

* row shape matches singular :func:`tier_spec_at` schema down to the
  key set
* every walked row carries ``is_current=False`` (``from`` is excluded
  from the walked rungs)
* rung walk is byte-stable against :func:`tier_path`,
  :func:`capacity_diff_path`, :func:`tier_unlocks_path`,
  :func:`tier_locks_path` and :func:`preview_path` (same
  ``_PURCHASABLE_TIERS`` filter + same sort + same destination-sibling
  exclusion); confirmed by extracting the rung ``id`` ids and lining
  them up against ``tier`` / ``to`` / ``target`` keys on the other
  five paths
* ascending walk reaches ``to_tier`` at the final rung; rung ``id``
  ids walk strictly upward in rank
* descending walk reaches ``to_tier`` at the final rung; rung ``id``
  ids walk strictly downward in rank
* per-rung byte-equality with the singular :func:`tier_spec_at`
  helper pinned on ``(from_tier, rung_id)`` for every rung in the walk
* the path's terminal row byte-equals ``tier_spec_at(from, to)``
  whenever the destination is purchasable; for ``to=trial`` the
  lateral branch produces a single-row path with the trial spec shape
* identity (``from == to``) returns an empty path
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint -- excluded from walked intermediate
  rungs (lateral endpoint pinned for ``to=trial``; intermediate-walk
  paths with ``from=trial`` cross into the rung above)
* unknown / empty / garbage ids return ``None`` and never raise
* grace vs enforce yields identical rows (helper is decoupled from the
  resolved entitlement; it walks the static per-tier maps via
  :func:`tier_spec_at`)
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
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_tier_spec_at_schema(ent):
    """Per-rung row shape must byte-match the singular
    :func:`tier_spec_at` row schema -- so a UI that already renders a
    ``/tier-spec-at`` row needs zero new shape code to render a per-rung
    row off this path."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    reference_keys = set(
        ent.tier_spec_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO).keys()
    )
    assert reference_keys  # sanity
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == reference_keys


def test_every_walked_row_carries_is_current_false(ent):
    """``from`` is excluded from the walked rungs, so the
    rung-equals-from-tier perspective never appears -- every walked
    row must surface with ``is_current=False``."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
    ):
        for row in ent.tier_spec_path(f, t):
            assert row["is_current"] is False


def test_first_row_is_first_step_above_from(ent):
    """Ascending walk from oss (rank 0) toward enterprise: the first
    row's ``id`` must be the first purchasable rung strictly above
    rank 0 -- cloud_starter at rank 1."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[0]["id"] == ent.TIER_CLOUD_STARTER


def test_last_row_is_destination(ent):
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[-1]["id"] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_tier_path(ent):
    """The set of rung ``id`` ids must match :func:`tier_path`'s rung
    ``to`` ids byte-for-byte -- same ``_PURCHASABLE_TIERS`` filter +
    same sort + same destination-sibling exclusion."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_OSS, ent.TIER_CLOUD_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert spec_rungs == diff_rungs


def test_rung_walk_byte_stable_against_capacity_diff_path(ent):
    """And byte-stable against :func:`capacity_diff_path` -- the five
    other path helpers must line up rung-for-rung against this one."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        cap_rungs = [r["target"] for r in ent.capacity_diff_path(f, t)]
        assert spec_rungs == cap_rungs


def test_rung_walk_byte_stable_against_tier_unlocks_path(ent):
    """And byte-stable against :func:`tier_unlocks_path`."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        unlocks_rungs = [r["tier"] for r in ent.tier_unlocks_path(f, t)]
        assert spec_rungs == unlocks_rungs


def test_rung_walk_byte_stable_against_tier_locks_path(ent):
    """And byte-stable against :func:`tier_locks_path`."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        locks_rungs = [r["tier"] for r in ent.tier_locks_path(f, t)]
        assert spec_rungs == locks_rungs


def test_rung_walk_byte_stable_against_preview_path(ent):
    """And byte-stable against :func:`preview_path` -- all six paths
    line up rung-for-rung."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        preview_rungs = [r["tier"] for r in ent.preview_path(f, t)]
        assert spec_rungs == preview_rungs


def test_ascending_walk_is_non_decreasing_in_rank(ent):
    """Ascending walk: rungs may share a collapsed rank only at the
    destination's rank (cloud_pro and pro both at collapsed rank 2 in
    a oss->enterprise walk); the sequence is non-decreasing overall.
    Pinned against :func:`tier_rank` (collapsed ``_TIER_RANK``), the
    same comparator the walker uses -- the published ``rank`` field
    on the row is the strict ``_TIER_ORDER`` ordinal and does not
    preserve walk monotonicity for same-collapsed-rank siblings."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    walk_ranks = [ent.tier_rank(r["id"]) for r in path]
    assert walk_ranks == sorted(walk_ranks)


def test_descending_walk_is_non_increasing_in_rank(ent):
    """Descending walk: pinned against :func:`tier_rank` (collapsed
    ``_TIER_RANK``) for the same reason as the ascending sibling."""
    path = ent.tier_spec_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    walk_ranks = [ent.tier_rank(r["id"]) for r in path]
    assert walk_ranks == sorted(walk_ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must
    end exactly at ``pro`` and EXCLUDE the same-rank sibling
    ``cloud_pro`` from the final rung -- same rule as the rest of the
    ``_path`` family."""
    rungs = [r["id"] for r in ent.tier_spec_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert rungs[-1] == ent.TIER_PRO
    assert rungs.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in rungs


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings ``cloud_pro`` AND
    ``pro`` both appear because they sit strictly *between* rank-0
    start and rank-3 destination."""
    rungs = [
        r["id"]
        for r in ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    ]
    assert ent.TIER_CLOUD_PRO in rungs
    assert ent.TIER_PRO in rungs
    assert rungs[-1] == ent.TIER_ENTERPRISE


def test_per_rung_byte_equality_with_singular_tier_spec_at(ent):
    """Each rung's row must byte-equal :func:`tier_spec_at(from, rung)`
    -- the path is a sequence of singular what-if specs pinned on
    ``from``, not a re-derivation."""
    f = ent.TIER_OSS
    path = ent.tier_spec_path(f, ent.TIER_ENTERPRISE)
    for row in path:
        direct = ent.tier_spec_at(f, row["id"])
        assert row == direct


def test_terminal_row_byte_equals_tier_spec_at_of_to(ent):
    """When the destination is purchasable the final rung must
    byte-equal :func:`tier_spec_at(from, to)`."""
    f = ent.TIER_OSS
    for to in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        path = ent.tier_spec_path(f, to)
        assert path[-1] == ent.tier_spec_at(f, to)


def test_terminal_row_for_trial_endpoint_via_lateral(ent):
    """The walked-rungs filter excludes trial as an intermediate, but
    the lateral branch can pin trial as a destination -- the row
    surfaces via :func:`tier_spec_at` directly and carries the trial
    spec shape."""
    path = ent.tier_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)
    assert len(path) == 1
    row = path[0]
    assert row["id"] == ent.TIER_TRIAL
    assert row == ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)


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
        assert ent.tier_spec_path(tid, tid) == []


def test_lateral_single_row(ent):
    path = ent.tier_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    row = path[0]
    assert row["id"] == ent.TIER_PRO


def test_oss_to_cloud_free_lateral_single_row(ent):
    """Both rank 0 -- lateral single-row path landing on cloud_free."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["id"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["id"] == ent.TIER_CLOUD_STARTER


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    """``trial`` is not purchasable -- it must never appear as an
    *intermediate* rung on a walk between purchasable endpoints."""
    path = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["id"] != ent.TIER_TRIAL


def test_trial_endpoint_still_resolves(ent):
    """``trial`` IS a valid endpoint -- as the source (via the
    cross-rank branch landing at enterprise) or as the destination
    (via the lateral branch)."""
    upward = ent.tier_spec_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["id"] == ent.TIER_ENTERPRISE
    downward = ent.tier_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)
    assert downward is not None
    assert downward[-1]["id"] == ent.TIER_TRIAL


def test_unknown_tiers_return_none(ent):
    assert ent.tier_spec_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    assert ent.tier_spec_path(ent.TIER_OSS, "still_not_a_tier") is None
    assert ent.tier_spec_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.tier_spec_path("", "") is None
    assert ent.tier_spec_path(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_spec_path("  ", "  ") is None
    assert ent.tier_spec_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.tier_spec_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    """The helper is decoupled from the resolved entitlement -- it
    walks the static per-tier maps via :func:`tier_spec_at` so
    flipping enforce on must NOT change any row. Pins the
    resolver-independence property the whole ``_path`` family shares."""
    grace_rows = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert grace_rows == enforced_rows


def test_resolver_failure_returns_none(ent, monkeypatch):
    """A blown per-rung builder must not 5xx -- the wrapper swallows
    and returns ``None`` so a pricing surface keeps rendering."""
    monkeypatch.setattr(
        ent,
        "tier_spec_at",
        lambda _f, _t: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    result = ent.tier_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert result is None


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert client.get("/api/entitlement/tier-spec-path").status_code == 400
    assert (
        client.get("/api/entitlement/tier-spec-path?from=oss").status_code == 400
    )
    assert (
        client.get("/api/entitlement/tier-spec-path?to=cloud_pro").status_code
        == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get("/api/entitlement/tier-spec-path?from=oss&to=not_a_tier")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["id"] == ent.TIER_ENTERPRISE
    reference_keys = set(
        ent.tier_spec_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO).keys()
    )
    for row in body["path"]:
        assert set(row.keys()) == reference_keys
        assert row["is_current"] is False


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["id"] == ent.TIER_OSS
    walk_ranks = [ent.tier_rank(row["id"]) for row in body["path"]]
    assert walk_ranks == sorted(walk_ranks, reverse=True)


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["id"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["id"] == ent.TIER_ENTERPRISE


def test_api_trial_destination_via_lateral(client, ent):
    """``to=trial`` resolves via the lateral branch (cloud_pro and
    trial share rank 2)."""
    r = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_TRIAL}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["id"] == ent.TIER_TRIAL


def test_api_rungs_match_tier_path_route(client, ent):
    """API-level byte-equality: rung ``id`` ids from
    ``/tier-spec-path`` match rung ``to`` ids from ``/tier-path``."""
    a = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["id"] for r in a["path"]] == [r["to"] for r in b["path"]]


def test_api_rungs_match_preview_path_route(client, ent):
    """And against ``/preview-path`` rung-for-rung."""
    a = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["id"] for r in a["path"]] == [r["tier"] for r in b["path"]]


def test_api_per_rung_byte_equality_with_tier_spec_at_endpoint(client, ent):
    """Each rung's row must byte-equal the ``spec`` field of the
    singular ``/tier-spec-at?tier=<from>&target=<rung>`` endpoint for
    that rung -- the route returns a sequence of singular what-if
    specs, not a re-derivation."""
    f = ent.TIER_OSS
    body = client.get(
        f"/api/entitlement/tier-spec-path?from={f}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    for row in body["path"]:
        ref = client.get(
            f"/api/entitlement/tier-spec-at?tier={f}&target={row['id']}"
        ).get_json()
        assert ref["spec"] == row
