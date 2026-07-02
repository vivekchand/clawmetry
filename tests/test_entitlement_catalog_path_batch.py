"""Tests for ``clawmetry.entitlements.feature_catalog_path_batch`` +
``runtime_catalog_path_batch`` and their HTTP endpoints
``/api/entitlement/feature-catalog-path-batch`` +
``/api/entitlement/runtime-catalog-path-batch``.

Batch siblings of the scalar catalog-path helpers: where the scalar helper
walks one ``(from, to)`` pair, the batch helper walks N candidate
destinations from ONE source in ONE round-trip -- the full-catalog member
of the path-batch grid alongside ``tier_path_batch``,
``tier_spec_path_batch``, ``capacity_diff_path_batch``,
``tier_unlocks_path_batch``, ``tier_locks_path_batch`` and
``preview_path_batch``.

Pins:

* per-destination ``path`` byte-equal to the scalar
  :func:`feature_catalog_path` / :func:`runtime_catalog_path` payload
* per-rung ``features`` / ``runtimes`` list byte-equals
  :func:`feature_catalog_at` / :func:`runtime_catalog_at` for the same
  rung -- the scalar, at-batch and path-batch surfaces cannot drift
* per-destination ``direction`` derived from rank geometry, matches the
  scalar endpoint's derivation
* batch envelope mirrors the scalar path envelope on the source side
  (``from`` / ``from_label`` / ``from_rank``) and carries
  ``tiers`` + ``unknown``
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown destination ids echoed in ``unknown[]`` instead of 404'ing
* identity ``from == to`` yields a per-destination entry whose ``path``
  is ``[]``; lateral (same rank) yields a one-row ``path``
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


_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
}

_FEATURE_ROW_KEYS = {"tier", "tier_label", "tier_rank", "features"}
_RUNTIME_ROW_KEYS = {"tier", "tier_label", "tier_rank", "runtimes"}


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


# ── feature helper: shape ────────────────────────────────────────────────────


def test_feature_helper_returns_dict_shape(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_feature_helper_each_item_carries_full_envelope(ent):
    out = ent.feature_catalog_path_batch(
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


def test_feature_helper_per_row_matches_catalog_row_shape(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    for row in out["tiers"][0]["path"]:
        assert set(row.keys()) == _FEATURE_ROW_KEYS
        assert isinstance(row["features"], list)


# ── feature helper: parity ───────────────────────────────────────────────────


def test_feature_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-destination ``path`` is byte-identical to the scalar
    :func:`feature_catalog_path` payload for the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.feature_catalog_path_batch(ent.TIER_OSS, candidates)
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.feature_catalog_path(ent.TIER_OSS, tid)
        assert by_id[tid] == scalar


def test_feature_helper_per_rung_features_byte_equal_to_catalog_at(ent):
    """Every rung's ``features`` list is what :func:`feature_catalog_at`
    returns for the same tier -- the scalar / at-batch / path / path-batch
    surfaces cannot drift."""
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    for item in out["tiers"]:
        for row in item["path"]:
            assert row["features"] == ent.feature_catalog_at(row["tier"])


def test_feature_helper_per_item_direction_matches_rank_geometry(ent):
    candidates = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.feature_catalog_path_batch(ent.TIER_CLOUD_STARTER, candidates)
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


# ── feature helper: input normalisation ──────────────────────────────────────


def test_feature_helper_supply_order_preserved(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
    )
    assert [item["to"] for item in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_feature_helper_normalises_input(ent):
    out = ent.feature_catalog_path_batch(
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


def test_feature_helper_unknown_destination_ids_echoed(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, "bogus_tier", "still_bogus"],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert set(out["unknown"]) == {"bogus_tier", "still_bogus"}


# ── feature helper: direction branches ───────────────────────────────────────


def test_feature_helper_identity_yields_empty_path(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    by_id = {item["to"]: item for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO]["direction"] == "identity"
    assert by_id[ent.TIER_CLOUD_PRO]["path"] == []
    assert by_id[ent.TIER_ENTERPRISE]["direction"] == "upgrade"


def test_feature_helper_lateral_yields_one_row_path(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_PRO]
    )
    assert len(out["tiers"]) == 1
    item = out["tiers"][0]
    assert item["direction"] == "lateral"
    assert len(item["path"]) == 1
    assert item["path"][0]["tier"] == ent.TIER_PRO


def test_feature_helper_upgrade_walks_intermediate_rungs(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    item = out["tiers"][0]
    assert item["direction"] == "upgrade"
    tiers = [row["tier"] for row in item["path"]]
    assert tiers[-1] == ent.TIER_ENTERPRISE
    assert ent.TIER_OSS not in tiers


def test_feature_helper_downgrade_walks_descending(ent):
    out = ent.feature_catalog_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    item = out["tiers"][0]
    assert item["direction"] == "downgrade"
    tiers = [row["tier"] for row in item["path"]]
    ranks = [ent.tier_rank(t) for t in tiers]
    assert ranks == sorted(ranks, reverse=True)
    assert tiers[-1] == ent.TIER_OSS


# ── feature helper: trial endpoint ───────────────────────────────────────────


def test_feature_helper_trial_destination_accepted(ent):
    """``trial`` is a valid endpoint (matching
    :func:`feature_catalog_path` semantics) even though it is excluded
    from the walked intermediate rungs."""
    out = ent.feature_catalog_path_batch(ent.TIER_OSS, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_TRIAL]


# ── feature helper: error / edge cases ───────────────────────────────────────


def test_feature_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.feature_catalog_path_batch(
            "not_a_tier", [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_feature_helper_empty_destinations_yields_empty_envelope(ent):
    out = ent.feature_catalog_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}


def test_feature_helper_garbage_inputs_never_raise(ent):
    assert ent.feature_catalog_path_batch("", []) is None
    assert ent.feature_catalog_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.feature_catalog_path_batch("  ", "  ") is None


def test_feature_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    grace = ent.feature_catalog_path_batch(ent.TIER_OSS, candidates)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.feature_catalog_path_batch(ent.TIER_OSS, candidates)
    assert grace == enforced


def test_feature_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-destination failure pushes that id into ``unknown[]`` while
    the rest of the batch keeps building."""
    real = ent.feature_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "feature_catalog_path", fake)
    out = ent.feature_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── runtime helper: shape + parity ───────────────────────────────────────────


def test_runtime_helper_returns_dict_shape(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_runtime_helper_per_row_matches_catalog_row_shape(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    for row in out["tiers"][0]["path"]:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS
        assert isinstance(row["runtimes"], list)


def test_runtime_helper_per_item_path_byte_equal_to_scalar(ent):
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.runtime_catalog_path_batch(ent.TIER_OSS, candidates)
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.runtime_catalog_path(ent.TIER_OSS, tid)
        assert by_id[tid] == scalar


def test_runtime_helper_per_rung_runtimes_byte_equal_to_catalog_at(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    for item in out["tiers"]:
        for row in item["path"]:
            assert row["runtimes"] == ent.runtime_catalog_at(row["tier"])


def test_runtime_helper_identity_yields_empty_path(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO]
    )
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_runtime_helper_lateral_yields_one_row_path(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_PRO]
    )
    assert len(out["tiers"]) == 1
    item = out["tiers"][0]
    assert item["direction"] == "lateral"
    assert len(item["path"]) == 1
    assert item["path"][0]["tier"] == ent.TIER_PRO


def test_runtime_helper_upgrade_and_downgrade_terminate_at_to(ent):
    up = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    down = ent.runtime_catalog_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    assert up["tiers"][0]["path"][-1]["tier"] == ent.TIER_ENTERPRISE
    assert down["tiers"][0]["path"][-1]["tier"] == ent.TIER_OSS


def test_runtime_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.runtime_catalog_path_batch(
            "not_a_tier", [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_runtime_helper_unknown_destination_ids_echoed(ent):
    out = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, "bogus_tier"]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert out["unknown"] == ["bogus_tier"]


def test_runtime_helper_garbage_inputs_never_raise(ent):
    assert ent.runtime_catalog_path_batch("", []) is None
    assert ent.runtime_catalog_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.runtime_catalog_path_batch("  ", "  ") is None


def test_runtime_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    grace = ent.runtime_catalog_path_batch(ent.TIER_OSS, candidates)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.runtime_catalog_path_batch(ent.TIER_OSS, candidates)
    assert grace == enforced


def test_runtime_helper_row_failure_short_circuits_item(ent, monkeypatch):
    real = ent.runtime_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "runtime_catalog_path", fake)
    out = ent.runtime_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── HTTP: /api/entitlement/feature-catalog-path-batch ────────────────────────


def test_feature_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch?to=cloud_pro,enterprise"
    )
    assert r.status_code == 400


def test_feature_api_400_on_missing_to(client):
    r = client.get("/api/entitlement/feature-catalog-path-batch?from=oss")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply to=<csv>"


def test_feature_api_400_on_empty_to(client):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch?from=oss&to=,,"
    )
    assert r.status_code == 400


def test_feature_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        "?from=not_a_tier&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_feature_api_200_with_unknown_destination_bucketed(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_feature_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
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


def test_feature_api_identity_branch(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "identity"
    assert body["tiers"][0]["path"] == []


def test_feature_api_lateral_branch(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "lateral"
    assert len(body["tiers"][0]["path"]) == 1


def test_feature_api_downgrade_branch(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "downgrade"


def test_feature_api_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/feature-catalog-path?from=&to=`` ``path`` payload for
    the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={','.join(candidates)}"
    ).get_json()
    for item in batch["tiers"]:
        scalar = client.get(
            "/api/entitlement/feature-catalog-path"
            f"?from={ent.TIER_OSS}&to={item['to']}"
        ).get_json()
        assert item["path"] == scalar["path"]
        assert item["direction"] == scalar["direction"]
        assert item["to_label"] == scalar["to_label"]
        assert item["to_rank"] == scalar["to_rank"]


def test_feature_api_input_normalised(client, ent):
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        "&to=  CLOUD_PRO  ,cloud_starter,cloud_pro,"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_feature_api_grace_and_enforce_yield_identical_body(
    client, ent, monkeypatch
):
    grace = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    assert grace == enforced


def test_feature_api_never_5xx_on_helper_failure(client, monkeypatch, ent):
    """Force the underlying helper to blow up; the route must degrade
    gracefully to an empty envelope instead of leaking a 500."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "feature_catalog_path_batch", boom)
    r = client.get(
        "/api/entitlement/feature-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []


# ── HTTP: /api/entitlement/runtime-catalog-path-batch ────────────────────────


def test_runtime_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch?to=cloud_pro"
    )
    assert r.status_code == 400


def test_runtime_api_400_on_missing_to(client):
    r = client.get("/api/entitlement/runtime-catalog-path-batch?from=oss")
    assert r.status_code == 400


def test_runtime_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        "?from=not_a_tier&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_runtime_api_200_with_unknown_destination_bucketed(client, ent):
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_runtime_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    tos = [item["to"] for item in body["tiers"]]
    assert tos == [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    for item in body["tiers"]:
        assert item["direction"] == "upgrade"
        assert item["path"][-1]["tier"] == item["to"]


def test_runtime_api_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/runtime-catalog-path?from=&to=`` ``path`` payload for
    the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={','.join(candidates)}"
    ).get_json()
    for item in batch["tiers"]:
        scalar = client.get(
            "/api/entitlement/runtime-catalog-path"
            f"?from={ent.TIER_OSS}&to={item['to']}"
        ).get_json()
        assert item["path"] == scalar["path"]
        assert item["direction"] == scalar["direction"]
        assert item["to_label"] == scalar["to_label"]
        assert item["to_rank"] == scalar["to_rank"]


def test_runtime_api_input_normalised(client, ent):
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        "&to=  CLOUD_PRO  ,cloud_starter,cloud_pro,"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_runtime_api_grace_and_enforce_yield_identical_body(
    client, ent, monkeypatch
):
    grace = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    assert grace == enforced


def test_runtime_api_never_5xx_on_helper_failure(client, monkeypatch, ent):
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "runtime_catalog_path_batch", boom)
    r = client.get(
        "/api/entitlement/runtime-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []
