"""Tests for ``tier_unlocks_path_batch(from, to_tiers)`` /
``tier_locks_path_batch(from, to_tiers)`` plus their HTTP endpoints.

Batch siblings of ``tier_unlocks_path`` / ``tier_locks_path``: where the
scalar path helpers walk the rungs between ONE ``(from, to)`` pair, the
batch helpers walk ONE ``from`` to N candidate ``to`` tiers in ONE
round-trip -- the multi-destination cousins of
``feature_spec_path_batch`` / ``runtime_spec_path_batch``.

Each per-destination ``path`` must be byte-identical to the matching
scalar ``tier_unlocks_path`` / ``tier_locks_path`` payload for the same
``(from, to)`` pair -- pinned by the parity tests below so the scalar
and batch path helpers cannot drift.

Coverage:

* per-destination ``path`` byte-equal to the scalar path helper's payload
* per-destination ``direction`` computed from tier ranks
  (upgrade / downgrade / lateral / identity)
* batch envelope (``tiers`` + ``unknown``) at helper level
* HTTP envelope (``from`` / ``from_label`` / ``from_rank`` + ``tiers`` +
  ``unknown``)
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown ids echoed in ``unknown[]`` instead of 404'ing the call
* identity ``from == to`` yields a single-row envelope whose ``path``
  is ``[]``
* lateral (same rank, different id) yields a single-row envelope whose
  ``path`` has one row
* ``trial`` accepted as both source and destination (matches the scalar
  helpers)
* unknown / empty / garbage source returns ``None`` (helper) / 400 / 404
  (HTTP)
* helpers never raise -- a row failure short-circuits that id into
  ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoints 400 on missing / empty input, 404 on unknown source,
  never 5xx on a row failure
* grace vs enforce yields identical rows
"""
from __future__ import annotations

import importlib

import pytest


_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}
_HELPER_ENVELOPE_KEYS = {"tiers", "unknown"}
_HTTP_ENVELOPE_KEYS = {
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
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── tier_unlocks_path_batch: helper-level ────────────────────────────────────


def test_unlocks_helper_returns_dict_shape(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_unlocks_helper_each_row_carries_expected_keys(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    for row in out["tiers"]:
        assert set(row.keys()) == _ITEM_KEYS
        assert isinstance(row["to"], str)
        assert isinstance(row["to_label"], str)
        assert isinstance(row["to_rank"], int)
        assert row["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }
        assert isinstance(row["path"], list)


def test_unlocks_helper_per_row_path_byte_equal_to_scalar(ent):
    """Pin: per-destination ``path`` is byte-identical to the scalar
    :func:`tier_unlocks_path` payload for the same ``(from, to)`` pair."""
    targets = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, targets)
    by_id = {row["to"]: row["path"] for row in out["tiers"]}
    for tid in targets:
        assert by_id[tid] == ent.tier_unlocks_path(ent.TIER_OSS, tid)


def test_unlocks_helper_direction_matches_ranks(ent):
    """Direction is derived from tier ranks -- upgrade / downgrade /
    lateral / identity."""
    targets = [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_OSS,
    ]
    out = ent.tier_unlocks_path_batch(ent.TIER_CLOUD_PRO, targets)
    by_id = {row["to"]: row["direction"] for row in out["tiers"]}
    # cloud_pro rank == pro rank == 2
    assert by_id[ent.TIER_ENTERPRISE] == "upgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_OSS] == "downgrade"


def test_unlocks_helper_supply_order_preserved(ent):
    targets = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER, ent.TIER_PRO]
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, targets)
    assert [row["to"] for row in out["tiers"]] == targets


def test_unlocks_helper_normalises_input(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        ["  CLOUD_STARTER  ", "cloud_pro", "cloud_starter", ""],
    )
    assert [row["to"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_unlocks_helper_accepts_csv_string(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS, "cloud_starter,cloud_pro,enterprise"
    )
    assert [row["to"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_unlocks_helper_unknown_ids_echoed(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, "bogus_id", "still_bogus"],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_CLOUD_STARTER]
    assert set(out["unknown"]) == {"bogus_id", "still_bogus"}


def test_unlocks_helper_identity_row_carries_empty_path(ent):
    out = ent.tier_unlocks_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO]
    )
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_unlocks_helper_lateral_row_has_single_step(ent):
    out = ent.tier_unlocks_path_batch(ent.TIER_CLOUD_PRO, [ent.TIER_PRO])
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "lateral"
    assert len(out["tiers"][0]["path"]) == 1
    assert out["tiers"][0]["path"][0]["tier"] == ent.TIER_PRO


def test_unlocks_helper_trial_accepted_as_endpoint(ent):
    """``trial`` is not purchasable but IS a valid endpoint -- matches
    :func:`tier_unlocks_path`."""
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["to"] == ent.TIER_TRIAL


def test_unlocks_helper_unknown_from_returns_none(ent):
    assert (
        ent.tier_unlocks_path_batch("not_a_tier", [ent.TIER_ENTERPRISE])
        is None
    )


def test_unlocks_helper_empty_to_list_yields_empty_envelope(ent):
    out = ent.tier_unlocks_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}


def test_unlocks_helper_garbage_inputs_never_raise(ent):
    assert ent.tier_unlocks_path_batch("", []) is None
    assert ent.tier_unlocks_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_path_batch("  ", "  ") is None


def test_unlocks_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    targets = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    grace = ent.tier_unlocks_path_batch(ent.TIER_OSS, targets)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_unlocks_path_batch(ent.TIER_OSS, targets)
    assert grace == enforced


def test_unlocks_helper_row_failure_short_circuits_id(ent, monkeypatch):
    """A per-destination failure pushes that id into ``unknown[]`` while
    the rest of the batch keeps building."""
    real = ent.tier_unlocks_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_STARTER:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_unlocks_path", fake)
    out = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_STARTER in out["unknown"]


# ── tier_locks_path_batch: helper-level ──────────────────────────────────────


def test_locks_helper_returns_dict_shape(ent):
    out = ent.tier_locks_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS, ent.TIER_CLOUD_STARTER]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS


def test_locks_helper_per_row_path_byte_equal_to_scalar(ent):
    targets = [ent.TIER_PRO, ent.TIER_CLOUD_STARTER, ent.TIER_OSS]
    out = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, targets)
    by_id = {row["to"]: row["path"] for row in out["tiers"]}
    for tid in targets:
        assert by_id[tid] == ent.tier_locks_path(ent.TIER_ENTERPRISE, tid)


def test_locks_helper_direction_matches_ranks(ent):
    targets = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.tier_locks_path_batch(ent.TIER_CLOUD_PRO, targets)
    by_id = {row["to"]: row["direction"] for row in out["tiers"]}
    assert by_id[ent.TIER_OSS] == "downgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "upgrade"


def test_locks_helper_identity_row_carries_empty_path(ent):
    out = ent.tier_locks_path_batch(ent.TIER_OSS, [ent.TIER_OSS])
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_locks_helper_trial_accepted_as_endpoint(ent):
    out = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["to"] == ent.TIER_TRIAL


def test_locks_helper_unknown_from_returns_none(ent):
    assert ent.tier_locks_path_batch("not_a_tier", [ent.TIER_OSS]) is None


def test_locks_helper_unknown_ids_echoed(ent):
    out = ent.tier_locks_path_batch(
        ent.TIER_ENTERPRISE,
        [ent.TIER_OSS, "bogus_id"],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert out["unknown"] == ["bogus_id"]


def test_locks_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    targets = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_PRO]
    grace = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, targets)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, targets)
    assert grace == enforced


def test_locks_helper_row_failure_short_circuits_id(ent, monkeypatch):
    real = ent.tier_locks_path

    def fake(f, t):
        if t == ent.TIER_OSS:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_locks_path", fake)
    out = ent.tier_locks_path_batch(
        ent.TIER_ENTERPRISE,
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_CLOUD_STARTER]
    assert ent.TIER_OSS in out["unknown"]


# ── cross-family symmetry ─────────────────────────────────────────────────────


def test_unlocks_and_locks_path_batch_walk_same_length(ent):
    """Rung counts from :func:`tier_unlocks_path_batch` (ascending) and
    :func:`tier_locks_path_batch` (descending) match for the same tier
    endpoints -- both walks visit every purchasable rung strictly between
    the endpoints plus the destination, so the walk length is
    direction-agnostic even though the walked rung ids are not (each
    walk includes the destination and excludes the source)."""
    up = ent.tier_unlocks_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    down = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, [ent.TIER_OSS])
    assert len(up["tiers"][0]["path"]) == len(down["tiers"][0]["path"])


# ── /api/entitlement/tier-unlocks-path-batch endpoint ────────────────────────


def test_http_unlocks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_ENVELOPE_KEYS


def test_http_unlocks_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER},"
        f"{ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    )
    body = r.get_json()
    helper = ent.tier_unlocks_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE],
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["from"] == ent.TIER_OSS
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)


def test_http_unlocks_missing_from_400(client):
    r = client.get("/api/entitlement/tier-unlocks-path-batch")
    assert r.status_code == 400


def test_http_unlocks_missing_to_400(client, ent):
    r = client.get(
        f"/api/entitlement/tier-unlocks-path-batch?from={ent.TIER_OSS}"
    )
    assert r.status_code == 400


def test_http_unlocks_bad_from_404(client):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch?from=bogus&to=cloud_starter"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_unlocks_unknown_to_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER},bogus"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [ent.TIER_CLOUD_STARTER]
    assert body["unknown"] == ["bogus"]


def test_http_unlocks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER}"
    )
    assert r.status_code < 500


def test_http_unlocks_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_TRIAL}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["to"] == ent.TIER_TRIAL


# ── /api/entitlement/tier-locks-path-batch endpoint ──────────────────────────


def test_http_locks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_ENVELOPE_KEYS


def test_http_locks_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_PRO},"
        f"{ent.TIER_CLOUD_STARTER},{ent.TIER_OSS}"
    )
    body = r.get_json()
    helper = ent.tier_locks_path_batch(
        ent.TIER_ENTERPRISE,
        [ent.TIER_PRO, ent.TIER_CLOUD_STARTER, ent.TIER_OSS],
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["from"] == ent.TIER_ENTERPRISE


def test_http_locks_missing_from_400(client):
    r = client.get("/api/entitlement/tier-locks-path-batch")
    assert r.status_code == 400


def test_http_locks_missing_to_400(client, ent):
    r = client.get(
        f"/api/entitlement/tier-locks-path-batch?from={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_locks_bad_from_404(client):
    r = client.get(
        "/api/entitlement/tier-locks-path-batch?from=bogus&to=oss"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_locks_unknown_to_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS},bogus"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["bogus"]


def test_http_locks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-locks-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code < 500
