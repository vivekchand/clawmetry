"""Tests for ``tier_unlocks_from_path_batch(from_tiers, to)`` /
``tier_locks_from_path_batch(from_tiers, to)`` plus their HTTP endpoints.

Mirror-direction siblings of ``tier_unlocks_path_batch`` /
``tier_locks_path_batch`` (which fix ONE source and fan out over N
destinations): here we fix ONE destination and fan out over N sources.
Source-axis batch cousins of ``has_features_from_path_batch`` /
``has_runtimes_from_path_batch``.

Each per-source ``path`` must be byte-identical to the matching scalar
``tier_unlocks_path`` / ``tier_locks_path`` payload for the same
``(from, to)`` pair -- pinned by the parity tests below so the scalar
and source-batch path helpers cannot drift.

Coverage:

* per-source ``path`` byte-equal to the scalar path helper's payload
* per-source ``direction`` computed from tier ranks relative to the
  shared ``to`` (upgrade / downgrade / lateral / identity)
* helper envelope (``tiers`` + ``unknown``) and per-row shape
  (``from`` / ``from_label`` / ``from_rank`` / ``direction`` / ``path``)
* HTTP envelope (``to`` / ``to_label`` / ``to_rank`` + ``tiers`` +
  ``unknown``)
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown source ids echoed in ``unknown[]`` instead of 404'ing
* identity ``from == to`` yields a single-row envelope whose ``path``
  is ``[]``
* lateral (same rank, different id) yields a single-row envelope whose
  ``path`` has one row
* ``trial`` accepted as both source and destination (matches the scalar
  helpers)
* unknown / empty / garbage destination returns ``None`` (helper) /
  400 / 404 (HTTP)
* helpers never raise -- a per-source failure short-circuits that id
  into ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoints 400 on missing / empty input, 404 on unknown
  destination, never 5xx on a helper failure
* grace vs enforce yields identical rows
"""
from __future__ import annotations

import importlib

import pytest


_ITEM_KEYS = {"from", "from_label", "from_rank", "direction", "path"}
_HELPER_ENVELOPE_KEYS = {"tiers", "unknown"}
_HTTP_ENVELOPE_KEYS = {
    "to",
    "to_label",
    "to_rank",
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
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── tier_unlocks_from_path_batch: helper-level ────────────────────────────────


def test_unlocks_helper_returns_dict_shape(ent):
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER], ent.TIER_ENTERPRISE
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_unlocks_helper_each_row_carries_expected_keys(ent):
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER], ent.TIER_ENTERPRISE
    )
    for row in out["tiers"]:
        assert set(row.keys()) == _ITEM_KEYS
        assert isinstance(row["from"], str)
        assert isinstance(row["from_label"], str)
        assert isinstance(row["from_rank"], int)
        assert row["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }
        assert isinstance(row["path"], list)


def test_unlocks_helper_per_row_path_byte_equal_to_scalar(ent):
    """Pin: per-source ``path`` is byte-identical to the scalar
    :func:`tier_unlocks_path` payload for the same ``(from, to)`` pair."""
    sources = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]
    out = ent.tier_unlocks_from_path_batch(sources, ent.TIER_ENTERPRISE)
    by_id = {row["from"]: row["path"] for row in out["tiers"]}
    for fid in sources:
        assert by_id[fid] == ent.tier_unlocks_path(fid, ent.TIER_ENTERPRISE)


def test_unlocks_helper_per_row_path_matches_at_path_batch_column(ent):
    """The per-source column produced by fanning sources equals the per-
    destination column from the destination-side batch for the mirror
    pair -- both delegate to the same scalar, so a caller can pick the
    axis that matches its query shape without shape drift."""
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    to_tier = ent.TIER_ENTERPRISE
    from_batch = ent.tier_unlocks_from_path_batch(sources, to_tier)
    for row in from_batch["tiers"]:
        dest_batch = ent.tier_unlocks_path_batch(row["from"], [to_tier])
        assert dest_batch["tiers"][0]["path"] == row["path"]


def test_unlocks_helper_direction_matches_ranks(ent):
    """Direction is derived per source relative to the shared ``to`` --
    upgrade / downgrade / lateral / identity."""
    sources = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.tier_unlocks_from_path_batch(sources, ent.TIER_CLOUD_PRO)
    by_id = {row["from"]: row["direction"] for row in out["tiers"]}
    # cloud_pro rank == pro rank == 2
    assert by_id[ent.TIER_OSS] == "upgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "downgrade"


def test_unlocks_helper_supply_order_preserved(ent):
    sources = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER, ent.TIER_OSS]
    out = ent.tier_unlocks_from_path_batch(sources, ent.TIER_CLOUD_PRO)
    assert [row["from"] for row in out["tiers"]] == sources


def test_unlocks_helper_normalises_input(ent):
    out = ent.tier_unlocks_from_path_batch(
        ["  CLOUD_STARTER  ", "cloud_pro", "cloud_starter", ""],
        ent.TIER_ENTERPRISE,
    )
    assert [row["from"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_unlocks_helper_accepts_csv_string(ent):
    out = ent.tier_unlocks_from_path_batch(
        "cloud_starter,cloud_pro,oss", ent.TIER_ENTERPRISE
    )
    assert [row["from"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
    ]


def test_unlocks_helper_unknown_ids_echoed(ent):
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_OSS, "bogus_id", "still_bogus"], ent.TIER_ENTERPRISE
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert set(out["unknown"]) == {"bogus_id", "still_bogus"}


def test_unlocks_helper_identity_row_carries_empty_path(ent):
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_CLOUD_PRO], ent.TIER_CLOUD_PRO
    )
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_unlocks_helper_lateral_row_has_single_step(ent):
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_PRO], ent.TIER_CLOUD_PRO
    )
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "lateral"
    assert len(out["tiers"][0]["path"]) == 1
    assert out["tiers"][0]["path"][0]["tier"] == ent.TIER_CLOUD_PRO


def test_unlocks_helper_trial_accepted_as_source(ent):
    """``trial`` is not purchasable but IS a valid endpoint -- matches
    :func:`tier_unlocks_path`."""
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_TRIAL], ent.TIER_ENTERPRISE
    )
    assert out["unknown"] == []
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["from"] == ent.TIER_TRIAL


def test_unlocks_helper_unknown_to_returns_none(ent):
    assert (
        ent.tier_unlocks_from_path_batch([ent.TIER_OSS], "not_a_tier")
        is None
    )


def test_unlocks_helper_empty_from_list_yields_empty_envelope(ent):
    out = ent.tier_unlocks_from_path_batch([], ent.TIER_ENTERPRISE)
    assert out == {"tiers": [], "unknown": []}


def test_unlocks_helper_garbage_inputs_never_raise(ent):
    assert ent.tier_unlocks_from_path_batch([], "") is None
    assert ent.tier_unlocks_from_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_from_path_batch("  ", "  ") is None


def test_unlocks_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    grace = ent.tier_unlocks_from_path_batch(sources, ent.TIER_ENTERPRISE)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_unlocks_from_path_batch(sources, ent.TIER_ENTERPRISE)
    assert grace == enforced


def test_unlocks_helper_row_failure_short_circuits_id(ent, monkeypatch):
    """A per-source failure pushes that id into ``unknown[]`` while the
    rest of the batch keeps building."""
    real = ent.tier_unlocks_path

    def fake(f, t):
        if f == ent.TIER_CLOUD_STARTER:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_unlocks_path", fake)
    out = ent.tier_unlocks_from_path_batch(
        [ent.TIER_CLOUD_STARTER, ent.TIER_OSS], ent.TIER_ENTERPRISE
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert ent.TIER_CLOUD_STARTER in out["unknown"]


# ── tier_locks_from_path_batch: helper-level ─────────────────────────────────


def test_locks_helper_returns_dict_shape(ent):
    out = ent.tier_locks_from_path_batch(
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO], ent.TIER_OSS
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS


def test_locks_helper_per_row_path_byte_equal_to_scalar(ent):
    sources = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER]
    out = ent.tier_locks_from_path_batch(sources, ent.TIER_OSS)
    by_id = {row["from"]: row["path"] for row in out["tiers"]}
    for fid in sources:
        assert by_id[fid] == ent.tier_locks_path(fid, ent.TIER_OSS)


def test_locks_helper_per_row_path_matches_at_path_batch_column(ent):
    sources = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER]
    to_tier = ent.TIER_OSS
    from_batch = ent.tier_locks_from_path_batch(sources, to_tier)
    for row in from_batch["tiers"]:
        dest_batch = ent.tier_locks_path_batch(row["from"], [to_tier])
        assert dest_batch["tiers"][0]["path"] == row["path"]


def test_locks_helper_direction_matches_ranks(ent):
    sources = [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_OSS,
    ]
    out = ent.tier_locks_from_path_batch(sources, ent.TIER_CLOUD_PRO)
    by_id = {row["from"]: row["direction"] for row in out["tiers"]}
    assert by_id[ent.TIER_ENTERPRISE] == "downgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_OSS] == "upgrade"


def test_locks_helper_identity_row_carries_empty_path(ent):
    out = ent.tier_locks_from_path_batch([ent.TIER_OSS], ent.TIER_OSS)
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_locks_helper_trial_accepted_as_source(ent):
    out = ent.tier_locks_from_path_batch([ent.TIER_TRIAL], ent.TIER_OSS)
    assert out["unknown"] == []
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["from"] == ent.TIER_TRIAL


def test_locks_helper_unknown_to_returns_none(ent):
    assert (
        ent.tier_locks_from_path_batch([ent.TIER_OSS], "not_a_tier") is None
    )


def test_locks_helper_unknown_ids_echoed(ent):
    out = ent.tier_locks_from_path_batch(
        [ent.TIER_ENTERPRISE, "bogus_id"], ent.TIER_OSS
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert out["unknown"] == ["bogus_id"]


def test_locks_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    sources = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_PRO]
    grace = ent.tier_locks_from_path_batch(sources, ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_locks_from_path_batch(sources, ent.TIER_OSS)
    assert grace == enforced


def test_locks_helper_row_failure_short_circuits_id(ent, monkeypatch):
    real = ent.tier_locks_path

    def fake(f, t):
        if f == ent.TIER_ENTERPRISE:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_locks_path", fake)
    out = ent.tier_locks_from_path_batch(
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO], ent.TIER_OSS
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert ent.TIER_ENTERPRISE in out["unknown"]


# ── cross-family symmetry ─────────────────────────────────────────────────────


def test_unlocks_and_locks_from_path_batch_walk_same_length(ent):
    """Rung counts from :func:`tier_unlocks_from_path_batch` (ascending)
    and :func:`tier_locks_from_path_batch` (descending) match for the
    mirror endpoints -- both walks visit every purchasable rung
    strictly between the endpoints plus the destination."""
    up = ent.tier_unlocks_from_path_batch([ent.TIER_OSS], ent.TIER_ENTERPRISE)
    down = ent.tier_locks_from_path_batch(
        [ent.TIER_ENTERPRISE], ent.TIER_OSS
    )
    assert len(up["tiers"][0]["path"]) == len(down["tiers"][0]["path"])


# ── /api/entitlement/tier-unlocks-from-path-batch endpoint ───────────────────


def test_http_unlocks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_ENVELOPE_KEYS


def test_http_unlocks_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_OSS},{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    body = r.get_json()
    helper = ent.tier_unlocks_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO],
        ent.TIER_ENTERPRISE,
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["to_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    assert body["to_label"] == ent.tier_label(ent.TIER_ENTERPRISE)


def test_http_unlocks_missing_to_400(client):
    r = client.get("/api/entitlement/tier-unlocks-from-path-batch")
    assert r.status_code == 400


def test_http_unlocks_missing_from_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_unlocks_bad_to_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_OSS}&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_unlocks_unknown_from_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_OSS},bogus&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["from"] for row in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["bogus"]


def test_http_unlocks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_from_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code < 500


def test_http_unlocks_trial_source_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-from-path-batch"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["from"] == ent.TIER_TRIAL


# ── /api/entitlement/tier-locks-from-path-batch endpoint ─────────────────────


def test_http_locks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-from-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_ENVELOPE_KEYS


def test_http_locks_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-from-path-batch"
        f"?from={ent.TIER_ENTERPRISE},{ent.TIER_CLOUD_PRO},{ent.TIER_CLOUD_STARTER}"
        f"&to={ent.TIER_OSS}"
    )
    body = r.get_json()
    helper = ent.tier_locks_from_path_batch(
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
        ent.TIER_OSS,
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["to"] == ent.TIER_OSS


def test_http_locks_missing_to_400(client):
    r = client.get("/api/entitlement/tier-locks-from-path-batch")
    assert r.status_code == 400


def test_http_locks_missing_from_400(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-from-path-batch?to={ent.TIER_OSS}"
    )
    assert r.status_code == 400


def test_http_locks_bad_to_404(client):
    r = client.get(
        "/api/entitlement/tier-locks-from-path-batch?from=oss&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_locks_unknown_from_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-from-path-batch"
        f"?from={ent.TIER_ENTERPRISE},bogus&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["from"] for row in body["tiers"]] == [ent.TIER_ENTERPRISE]
    assert body["unknown"] == ["bogus"]


def test_http_locks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_from_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-locks-from-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code < 500
