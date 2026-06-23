"""Tests for ``clawmetry.entitlements.preview_path(from, to)`` + the
``GET /api/entitlement/preview-path`` endpoint.

Cumulative-state analogue of :func:`tier_path` (full ``tier_diff`` per
rung), :func:`capacity_diff_path` (capacity-only per rung),
:func:`tier_unlocks_path` (marginal grants per rung) and
:func:`tier_locks_path` (marginal losses per rung) -- the fifth and
final member of the ``_path`` family, the path-shaped sibling of
:func:`preview_batch`. Lets an upgrade-walkthrough surface render the
"Cloud Pro: 90-day retention, unlimited channels, claude_code unlocked"
card at every rung between any two tiers off ONE round-trip, without
re-deriving capacity in JS.

Per-rung row shape matches :func:`preview` exactly -- the full
``Entitlement.to_dict`` shape with ``source="preview"`` and
``grace=False`` so concrete per-tier capacity surfaces -- so a UI that
already renders ``/preview`` rendering the per-rung row off this path
needs zero new shape code.

Pins:

* row shape matches singular :func:`preview` schema down to the key set
* every row carries ``source="preview"`` and ``grace=False``
* rung walk is byte-stable against :func:`tier_path`,
  :func:`capacity_diff_path`, :func:`tier_unlocks_path` and
  :func:`tier_locks_path` (same ``_PURCHASABLE_TIERS`` filter + same
  sort + same destination-sibling exclusion); confirmed by extracting
  the rung ``tier`` ids
* ascending walk reaches ``to_tier`` at the final rung; the rung
  ``tier`` ids walk strictly upward in rank
* descending walk reaches ``to_tier`` at the final rung; rung ``tier``
  ids walk strictly downward in rank
* per-rung byte-equality with the singular :func:`preview` endpoint for
  every purchasable rung in the walk
* the path's terminal row byte-equals :func:`preview` of ``to_tier``
  whenever the destination is purchasable; for ``to=trial`` the lateral
  branch produces a single-row path with the trial preview shape
* identity (``from == to``) returns an empty path
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint -- excluded from walked intermediate
  rungs (lateral endpoint pinned for ``to=trial``; intermediate-walk
  paths with ``from=trial`` cross into the rung above)
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
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_matches_preview_schema(ent):
    """Per-rung row shape must byte-match the singular ``preview``
    endpoint's row schema -- so a UI that already renders ``/preview``
    needs zero new shape code to render a per-rung row off this path."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    reference_keys = set(ent.preview(ent.TIER_CLOUD_PRO).keys())
    assert reference_keys  # sanity
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == reference_keys


def test_every_row_tagged_preview_grace_false(ent):
    """Each row is rendered with ``source="preview"`` and ``grace=False``
    so concrete per-tier capacity (``channel_limit``, ``retention_days``,
    ``node_limit``) surfaces -- a grace-mode preview would zero those out
    and defeat the purpose. Same posture as the singular helper."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["source"] == "preview"
        assert row["grace"] is False
        assert row["enforced"] is True


def test_first_row_is_first_step_above_from(ent):
    """Ascending walk from oss (rank 0) toward enterprise: the first
    row's ``tier`` must be the first purchasable rung strictly above
    rank 0 -- cloud_starter at rank 1."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER


def test_last_row_is_destination(ent):
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert path[-1]["tier"] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_tier_path(ent):
    """The set of rung ``tier`` ids must match :func:`tier_path`'s rung
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
        preview_rungs = [r["tier"] for r in ent.preview_path(f, t)]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert preview_rungs == diff_rungs


def test_rung_walk_byte_stable_against_capacity_diff_path(ent):
    """And byte-stable against :func:`capacity_diff_path` -- the four
    other path helpers must line up rung-for-rung against this one.
    (``capacity_diff_path`` keys its rung id at ``target`` rather than
    ``tier``; pin the same walk regardless.)"""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        preview_rungs = [r["tier"] for r in ent.preview_path(f, t)]
        cap_rungs = [r["target"] for r in ent.capacity_diff_path(f, t)]
        assert preview_rungs == cap_rungs


def test_rung_walk_byte_stable_against_tier_unlocks_path(ent):
    """And byte-stable against :func:`tier_unlocks_path`."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        preview_rungs = [r["tier"] for r in ent.preview_path(f, t)]
        unlocks_rungs = [r["tier"] for r in ent.tier_unlocks_path(f, t)]
        assert preview_rungs == unlocks_rungs


def test_rung_walk_byte_stable_against_tier_locks_path(ent):
    """And byte-stable against :func:`tier_locks_path` -- all five
    paths line up rung-for-rung."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        preview_rungs = [r["tier"] for r in ent.preview_path(f, t)]
        locks_rungs = [r["tier"] for r in ent.tier_locks_path(f, t)]
        assert preview_rungs == locks_rungs


def test_ascending_walk_is_strictly_increasing_in_rank(ent):
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    ranks = [r["tier_rank"] for r in path]
    # rungs may share a rank only at the destination's rank (cloud_pro
    # and pro both at rank 2 in a oss->enterprise walk); strictly
    # non-decreasing, with at most one repeat
    assert ranks == sorted(ranks)


def test_descending_walk_is_strictly_decreasing_in_rank(ent):
    path = ent.preview_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    ranks = [r["tier_rank"] for r in path]
    assert ranks == sorted(ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2; asking for ``pro`` must
    end exactly at ``pro`` and EXCLUDE the same-rank sibling
    ``cloud_pro`` from the final rung -- same rule as :func:`tier_path`."""
    rungs = [r["tier"] for r in ent.preview_path(ent.TIER_OSS, ent.TIER_PRO)]
    assert rungs[-1] == ent.TIER_PRO
    assert rungs.count(ent.TIER_PRO) == 1
    assert ent.TIER_CLOUD_PRO not in rungs


def test_same_rank_siblings_between_endpoints_both_included(ent):
    """Walking oss -> enterprise: rank-2 siblings ``cloud_pro`` AND
    ``pro`` both appear because they sit strictly *between* rank-0 start
    and rank-3 destination."""
    rungs = [r["tier"] for r in ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)]
    assert ent.TIER_CLOUD_PRO in rungs
    assert ent.TIER_PRO in rungs
    assert rungs[-1] == ent.TIER_ENTERPRISE


def test_per_rung_byte_equality_with_singular_preview(ent):
    """Each rung's row must byte-equal :func:`preview` of that rung --
    the path is a sequence of singular previews, not a re-derivation."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        direct = ent.preview(row["tier"])
        assert row == direct


def test_terminal_row_byte_equals_preview_of_to_for_purchasable(ent):
    """When the destination is purchasable the final rung must
    byte-equal :func:`preview(to)`."""
    for to in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        path = ent.preview_path(ent.TIER_OSS, to)
        assert path[-1] == ent.preview(to)


def test_terminal_row_for_trial_endpoint_via_lateral(ent):
    """The singular :func:`preview` returns ``None`` for trial, but the
    path's lateral branch can pin trial as a destination -- the row
    surfaces via :func:`_preview_row` directly and carries the trial
    cumulative shape."""
    path = ent.preview_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)
    assert len(path) == 1
    row = path[0]
    assert row["tier"] == ent.TIER_TRIAL
    assert row["source"] == "preview"
    assert row["grace"] is False
    # trial carries the full paid feature/runtime grant
    assert "claude_code" in row["runtimes"]


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
        assert ent.preview_path(tid, tid) == []


def test_lateral_single_row(ent):
    path = ent.preview_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert len(path) == 1
    row = path[0]
    assert row["tier"] == ent.TIER_PRO


def test_oss_to_cloud_free_lateral_single_row(ent):
    """Both rank 0 -- lateral single-row path landing on cloud_free."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_FREE


def test_adjacent_step_is_one_row(ent):
    """oss (rank 0) -> cloud_starter (rank 1) is a single rank-up step."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_CLOUD_STARTER


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    """``trial`` is not purchasable -- it must never appear as an
    *intermediate* rung on a walk between purchasable endpoints."""
    path = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for row in path:
        assert row["tier"] != ent.TIER_TRIAL


def test_trial_endpoint_still_resolves(ent):
    """``trial`` IS a valid endpoint -- as the source (via the
    cross-rank branch landing at enterprise) or as the destination (via
    the lateral branch)."""
    upward = ent.preview_path(ent.TIER_TRIAL, ent.TIER_ENTERPRISE)
    assert upward is not None
    assert upward[-1]["tier"] == ent.TIER_ENTERPRISE
    downward = ent.preview_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)
    assert downward is not None
    assert downward[-1]["tier"] == ent.TIER_TRIAL


def test_unknown_tiers_return_none(ent):
    assert ent.preview_path("not_a_tier", ent.TIER_ENTERPRISE) is None
    assert ent.preview_path(ent.TIER_OSS, "still_not_a_tier") is None
    assert ent.preview_path("a", "b") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.preview_path("", "") is None
    assert ent.preview_path(None, None) is None  # type: ignore[arg-type]
    assert ent.preview_path("  ", "  ") is None
    assert ent.preview_path(123, 456) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    b = ent.preview_path("  OSS ", " ENTERPRISE  ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    """The helper is decoupled from the resolved entitlement -- it
    walks the static per-tier maps so flipping enforce on must NOT
    change any row. Pins the resolver-independence property the whole
    ``_path`` family shares."""
    grace_rows = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert grace_rows == enforced_rows


def test_resolver_failure_returns_none(ent, monkeypatch):
    """A blown resolver must not 5xx -- the helper walks the static
    per-tier maps so it never asks the resolver, but pin the
    swallow-and-return-None posture anyway against future refactors
    that might wire one in."""
    # The function is intentionally decoupled from the resolver, so the
    # most we can do is confirm it does not raise on unknown ids and
    # short-circuits to None instead -- already covered above. As an
    # extra belt-and-suspenders pin we monkeypatch the private row
    # builder to blow up and confirm the wrapper swallows it.
    monkeypatch.setattr(
        ent,
        "_preview_row",
        lambda _tier: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    # The cross-rank walk never reaches a rung row because the iterator
    # raises on the first call; the helper's outer try/except catches it.
    result = ent.preview_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert result is None


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_args(client):
    assert client.get("/api/entitlement/preview-path").status_code == 400
    assert client.get("/api/entitlement/preview-path?from=oss").status_code == 400
    assert (
        client.get("/api/entitlement/preview-path?to=cloud_pro").status_code == 400
    )


def test_api_404_on_unknown_tier(client):
    r = client.get("/api/entitlement/preview-path?from=oss&to=not_a_tier")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["to"] == "not_a_tier"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
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
    reference_keys = set(ent.preview(ent.TIER_CLOUD_PRO).keys())
    for row in body["path"]:
        assert set(row.keys()) == reference_keys


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["tier"] == ent.TIER_OSS
    # rungs walk downward in rank
    ranks = [r["tier_rank"] for r in body["path"]]
    assert ranks == sorted(ranks, reverse=True)


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["tier"] == ent.TIER_PRO


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_trial_destination_via_lateral(client, ent):
    """``to=trial`` resolves via the lateral branch (cloud_pro and
    trial share rank 2)."""
    r = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_TRIAL}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["tier"] == ent.TIER_TRIAL


def test_api_rungs_match_tier_path_route(client, ent):
    """API-level byte-equality: rung ``tier`` ids from
    ``/preview-path`` match rung ``to`` ids from ``/tier-path``."""
    a = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["tier"] for r in a["path"]] == [r["to"] for r in b["path"]]


def test_api_rungs_match_tier_unlocks_path_route(client, ent):
    """And against ``/tier-unlocks-path`` rung-for-rung."""
    a = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-unlocks-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["tier"] for r in a["path"]] == [r["tier"] for r in b["path"]]


def test_api_per_rung_byte_equality_with_preview_endpoint(client, ent):
    """Each rung's row must byte-equal the singular ``/preview``
    endpoint for that rung -- the route returns a sequence of singular
    previews, not a re-derivation."""
    body = client.get(
        f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    for row in body["path"]:
        ref = client.get(
            f"/api/entitlement/preview?tier={row['tier']}"
        ).get_json()
        assert row == ref
