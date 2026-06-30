"""Tests for ``tier_unlocks_path_batch(from_tier, to_tiers)`` plus its
HTTP endpoint ``/api/entitlement/tier-unlocks-path-batch``.

Batch sibling of ``tier_unlocks_path``: where the scalar path helper
walks one ``(from, to)`` pair, the batch helper walks N candidate
destinations from one source in ONE round-trip. Multi-destination twin
of :func:`capacity_diff_path_batch` (same fan-out shape, marginal-
unlocks per-rung body) and unlocks-only sibling of
:func:`tier_spec_path_batch` (same multi-destination axis,
marginal-grant body instead of full per-rung spec).

Each per-destination ``path`` must be byte-identical to the matching
scalar :func:`tier_unlocks_path` payload for the same ``(from, to)``
pair -- pinned by the parity tests below so the scalar and batch path
accessors cannot drift.

Coverage:

* per-destination ``path`` byte-equal to the scalar
  :func:`tier_unlocks_path` payload
* per-row body matches the singular :func:`tier_unlocks` row shape
  (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
  ``previous_tier_label``, ``previous_tier_rank``, ``features``,
  ``runtimes``)
* ``previous_tier`` is path-chained (the previous step in the walked
  path, never ``None`` on any path row) -- matches the scalar helper's
  one semantic difference vs :func:`tier_unlocks`
* per-rung chain continuous on the tier axis
  (``row[i]['tier'] == row[i+1]['previous_tier']``) on every
  per-destination path
* per-destination ``direction`` derived from the same ranks the scalar
  endpoint uses
* batch envelope mirrors ``/tier-unlocks-path``'s envelope on the
  source side (``from`` / ``from_label`` / ``from_rank``) and carries
  ``tiers`` + ``unknown``
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown destination ids echoed in ``unknown[]`` instead of 404'ing
  the call (matching every other batch sibling)
* identity ``from == to`` yields a per-destination entry whose ``path``
  is ``[]``
* lateral (same rank) yields a one-row per-destination ``path``
* upgrade / downgrade direction labelled correctly; downgrade rows
  carry empty unlock lists but still walk the rungs
* trial accepted as a destination (lateral / identity endpoint only --
  excluded from intermediate rungs, same as the scalar helper)
* unknown / empty / garbage ``from_tier`` returns ``None`` (helper) /
  400 / 404 (HTTP)
* helpers never raise -- a per-destination failure short-circuits that
  id into ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoint 400 on missing / empty input, 404 on unknown source
  tier, never 5xx on a row failure
* grace vs enforce yields identical rows (resolver-independent)
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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

_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
}


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


# ── helper-level: shape ──────────────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_full_envelope(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    for item in out["tiers"]:
        assert set(item.keys()) == _ITEM_KEYS
        assert isinstance(item["to"], str)
        assert isinstance(item["to_label"], str)
        assert isinstance(item["to_rank"], int)
        assert item["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }
        assert isinstance(item["path"], list)


def test_helper_per_row_matches_tier_unlocks_schema(ent):
    """Per-row body must match the singular :func:`tier_unlocks` row
    shape exactly."""
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    for row in out["tiers"][0]["path"]:
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["features"], list)
        assert isinstance(row["runtimes"], list)


def test_helper_previous_tier_fields_never_none_on_path(ent):
    """Path-chained source guarantees ``previous_tier`` (+ label/rank)
    are concrete on every path row -- the one semantic difference vs
    the singular :func:`tier_unlocks` (which can carry ``None`` at the
    floor)."""
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    for item in out["tiers"]:
        for row in item["path"]:
            assert row["previous_tier"] is not None
            assert row["previous_tier_label"] is not None
            assert row["previous_tier_rank"] is not None


def test_helper_chain_continuous_on_tier_axis(ent):
    """``row[i]['tier'] == row[i+1]['previous_tier']`` on every
    per-destination path -- the path-chained invariant the scalar
    helper enforces."""
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    for item in out["tiers"]:
        path = item["path"]
        for i in range(len(path) - 1):
            assert path[i]["tier"] == path[i + 1]["previous_tier"]


# ── helper-level: parity with scalar ─────────────────────────────────────────


def test_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-destination ``path`` is byte-identical to the scalar
    :func:`tier_unlocks_path` payload for the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, candidates)
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.tier_unlocks_path(ent.TIER_OSS, tid)
        assert by_id[tid] == scalar


def test_helper_per_item_direction_matches_rank_geometry(ent):
    """Per-destination ``direction`` is derived from rank geometry and
    must agree with the scalar endpoint's derivation."""
    candidates = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.tier_unlocks_path_batch(ent.TIER_CLOUD_STARTER, candidates)
    by_id = {item["to"]: item for item in out["tiers"]}
    src_rank = ent.tier_rank(ent.TIER_CLOUD_STARTER)
    for tid in candidates:
        tgt_rank = ent.tier_rank(tid)
        if tid == ent.TIER_CLOUD_STARTER:
            expected = "identity"
        elif src_rank == tgt_rank:
            expected = "lateral"
        elif tgt_rank > src_rank:
            expected = "upgrade"
        else:
            expected = "downgrade"
        assert by_id[tid]["direction"] == expected


# ── helper-level: input normalisation ────────────────────────────────────────


def test_helper_supply_order_preserved(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
    )
    assert [item["to"] for item in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_helper_normalises_input(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [
            "  CLOUD_PRO  ",
            "cloud_starter",
            "cloud_pro",
            "",
        ],
    )
    assert [item["to"] for item in out["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_helper_unknown_destination_ids_echoed(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, "bogus_tier", "still_bogus"],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert set(out["unknown"]) == {"bogus_tier", "still_bogus"}


# ── helper-level: direction branches ─────────────────────────────────────────


def test_helper_identity_yields_empty_path(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    by_id = {item["to"]: item for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO]["direction"] == "identity"
    assert by_id[ent.TIER_CLOUD_PRO]["path"] == []
    assert by_id[ent.TIER_ENTERPRISE]["direction"] == "upgrade"


def test_helper_lateral_yields_one_row_path(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_PRO]
    )
    assert len(out["tiers"]) == 1
    item = out["tiers"][0]
    assert item["direction"] == "lateral"
    assert len(item["path"]) == 1


def test_helper_upgrade_walks_intermediate_rungs(ent):
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    item = out["tiers"][0]
    assert item["direction"] == "upgrade"
    tiers = [row["tier"] for row in item["path"]]
    assert tiers[-1] == ent.TIER_ENTERPRISE
    assert ent.TIER_OSS not in tiers


def test_helper_downgrade_walks_descending(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    item = out["tiers"][0]
    assert item["direction"] == "downgrade"
    tiers = [row["tier"] for row in item["path"]]
    ranks = [ent.tier_rank(r) for r in tiers]
    assert ranks == sorted(ranks, reverse=True)


def test_helper_downgrade_rows_carry_empty_unlocks(ent):
    """Descending walks still walk the rungs (so a UI keyed off rung
    shape keeps working) but every row carries empty unlock lists --
    you lose things on a downgrade, you don't unlock them. Matches the
    scalar helper's posture."""
    out = ent.tier_unlocks_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    for row in out["tiers"][0]["path"]:
        assert row["features"] == []
        assert row["runtimes"] == []


def test_helper_upgrade_folds_to_cumulative_diff(ent):
    """Folding ``features`` / ``runtimes`` across an ascending path
    reconstructs the cumulative ``tier_diff(from, to)['added_*']``
    sets -- the path-chained source guarantees this."""
    src, dst = ent.TIER_OSS, ent.TIER_ENTERPRISE
    out = ent.tier_unlocks_path_batch(src, [dst])
    path = out["tiers"][0]["path"]
    folded_features = set()
    folded_runtimes = set()
    for row in path:
        folded_features |= set(row["features"])
        folded_runtimes |= set(row["runtimes"])
    diff = ent.tier_diff(src, dst)
    assert folded_features == set(diff["added_features"])
    assert folded_runtimes == set(diff["added_runtimes"])


# ── helper-level: trial endpoint ─────────────────────────────────────────────


def test_helper_trial_destination_accepted(ent):
    """``trial`` is a valid endpoint (matching :func:`tier_unlocks_path`
    semantics) even though it is excluded from the walked intermediate
    rungs."""
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_TRIAL]


# ── helper-level: error / edge cases ─────────────────────────────────────────


def test_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.tier_unlocks_path_batch("not_a_tier", [ent.TIER_ENTERPRISE])
        is None
    )


def test_helper_empty_destinations_yields_empty_envelope(ent):
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}


def test_helper_garbage_inputs_never_raise(ent):
    assert ent.tier_unlocks_path_batch("", []) is None
    assert ent.tier_unlocks_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_path_batch("  ", "  ") is None


def test_helper_grace_and_enforce_yield_identical_output(ent, monkeypatch):
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    grace = ent.tier_unlocks_path_batch(ent.TIER_OSS, candidates)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_unlocks_path_batch(ent.TIER_OSS, candidates)
    assert grace == enforced


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-destination failure pushes that id into ``unknown[]`` while
    the rest of the batch keeps building."""
    real = ent.tier_unlocks_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_unlocks_path", fake)
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── HTTP: /api/entitlement/tier-unlocks-path-batch ───────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch?to=cloud_pro,enterprise"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get("/api/entitlement/tier-unlocks-path-batch?from=oss")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply to=<csv>"


def test_api_400_on_empty_to(client):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch?from=oss&to=,,"
    )
    assert r.status_code == 400


def test_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        "?from=not_a_tier&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_api_200_with_unknown_destination_bucketed(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert isinstance(body["from_label"], str)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    tos = [item["to"] for item in body["tiers"]]
    assert tos == [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    for item in body["tiers"]:
        assert item["direction"] == "upgrade"
        assert item["path"][-1]["tier"] == item["to"]


def test_api_identity_branch(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "identity"
    assert body["tiers"][0]["path"] == []


def test_api_lateral_branch(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "lateral"
    assert len(body["tiers"][0]["path"]) == 1


def test_api_downgrade_branch(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "downgrade"


def test_api_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/tier-unlocks-path?from=&to=`` ``path`` payload for
    the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to={','.join(candidates)}"
    ).get_json()
    for item in batch["tiers"]:
        scalar = client.get(
            f"/api/entitlement/tier-unlocks-path?from={ent.TIER_OSS}"
            f"&to={item['to']}"
        ).get_json()
        assert item["path"] == scalar["path"]
        assert item["direction"] == scalar["direction"]
        assert item["to_label"] == scalar["to_label"]
        assert item["to_rank"] == scalar["to_rank"]


def test_api_input_normalised(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to=  CLOUD_PRO  ,cloud_starter,cloud_pro,"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_api_grace_and_enforce_yield_identical_body(
    client, ent, monkeypatch
):
    grace = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    assert grace == enforced
