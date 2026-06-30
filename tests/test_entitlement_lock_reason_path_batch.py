"""Tests for ``clawmetry.entitlements.lock_reason_path_batch(...)`` +
the ``GET /api/entitlement/lock-reason-path-batch`` endpoint.

Multi-axis batch sibling of :func:`lock_reason_path`: where the scalar
path helper walks ONE item across the rungs between two tiers, this
walks N items across all 5 axes (features + runtimes + 3 capacity
axes) in ONE round-trip. Pairs with :func:`lock_reason_path` the same
way :func:`lock_reasons_at_batch` pairs with :func:`lock_reason_at`.

Pins:

* per-item ``path`` byte-identical to the scalar
  :func:`lock_reason_path` payload for the same ``(from, to, item,
  kind)`` tuple -- so the scalar and batch path helpers cannot drift
* rung walk identical across items in the same batch (rungs are
  item-agnostic, matches the ``feature_spec_path_batch`` /
  ``runtime_spec_path_batch`` invariant)
* envelope mirrors ``/feature-spec-path-batch`` (from / from_label /
  from_rank / to / to_label / to_rank / direction) PLUS the 5-axis
  body of :func:`lock_reasons_at_batch` (features / runtimes /
  channels / retention_days / nodes) PLUS structured
  ``unknown.features`` / ``unknown.runtimes``
* feature/runtime input normalised (whitespace stripped, lowercased,
  duplicates dropped, first-seen order preserved); runtime aliases
  canonicalise and collapse against already-supplied canonical ids
* unknown feature/runtime ids echoed in ``unknown[...]`` instead of
  404'ing the call
* capacity axes are single-item (single int each); ``None`` /
  non-positive / non-int values render that axis as ``None``
  short-circuit (matches :func:`lock_reason_path`)
* identity ``from == to`` yields per-item paths of ``[]``
* lateral (same rank, different id) yields one-row paths per item
* helper never raises -- per-item failures short-circuit that item
  into ``unknown[...]`` and the rest of the batch keeps building
* HTTP endpoint: 400 on missing tier / no axis supplied; 404 on
  unknown tier; never 5xxs on row failure
* grace vs enforce yields byte-identical rows
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown",
}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}
_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
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


def _pick_feature(ent, *, paid: bool) -> str:
    pool = ent.PAID_FEATURES if paid else ent.FREE_FEATURES
    return sorted(pool)[0]


def _pick_paid_runtime(ent) -> str:
    return sorted(ent.PAID_RUNTIMES)[0]


# ── helper: envelope shape ──────────────────────────────────────────────────


def test_helper_returns_dict_with_5_axes_plus_unknown(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=[_pick_feature(ent, paid=True)],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
        retention_days=365,
        nodes=50,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "unknown",
    }
    assert isinstance(out["features"], list)
    assert isinstance(out["runtimes"], list)
    assert isinstance(out["unknown"], dict)
    assert set(out["unknown"].keys()) == {"features", "runtimes"}


def test_helper_each_axis_item_carries_key_and_path(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=[_pick_feature(ent, paid=True)],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
        retention_days=365,
        nodes=50,
    )
    for item in out["features"]:
        assert set(item.keys()) == {"key", "path"}
        assert isinstance(item["key"], str)
        assert isinstance(item["path"], list)
    for item in out["runtimes"]:
        assert set(item.keys()) == {"key", "path"}
    for axis in ("channels", "retention_days", "nodes"):
        assert set(out[axis].keys()) == {"key", "path"}


def test_helper_unsupplied_axes_default_to_empty_or_none(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, features=["custom_alerts"]
    )
    assert out["features"] != []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None
    assert out["unknown"] == {"features": [], "runtimes": []}


# ── helper: parity with scalar lock_reason_path ─────────────────────────────


def test_helper_feature_path_byte_equal_to_scalar(ent):
    feats = sorted(ent.PAID_FEATURES)[:3]
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, features=feats
    )
    by_id = {item["key"]: item["path"] for item in out["features"]}
    for fid in feats:
        scalar = ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, fid, kind="feature"
        )
        assert by_id[fid] == scalar


def test_helper_runtime_path_byte_equal_to_scalar(ent):
    rts = sorted(ent.PAID_RUNTIMES)[:2]
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, runtimes=rts
    )
    by_id = {item["key"]: item["path"] for item in out["runtimes"]}
    for rt in rts:
        scalar = ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, rt, kind="runtime"
        )
        assert by_id[rt] == scalar


@pytest.mark.parametrize(
    "axis,value",
    [
        ("channels", 99),
        ("retention_days", 365),
        ("nodes", 50),
    ],
)
def test_helper_capacity_path_byte_equal_to_scalar(ent, axis, value):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, **{axis: value}
    )
    scalar = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, str(value), kind=axis
    )
    assert out[axis] == {"key": str(value), "path": scalar}


# ── helper: rung walk item-agnostic ─────────────────────────────────────────


def test_helper_rung_walk_identical_across_items(ent):
    feats = sorted(ent.PAID_FEATURES)[:2]
    rts = sorted(ent.PAID_RUNTIMES)[:2]
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=feats,
        runtimes=rts,
        channels=99,
        retention_days=365,
        nodes=50,
    )
    sequences = []
    for item in out["features"] + out["runtimes"]:
        sequences.append([row["rung"] for row in item["path"]])
    for axis in ("channels", "retention_days", "nodes"):
        sequences.append([row["rung"] for row in out[axis]["path"]])
    assert all(seq == sequences[0] for seq in sequences)
    assert len(sequences[0]) >= 1


def test_helper_each_path_row_carries_rung_and_lock_keys(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["custom_alerts"],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
    )
    for item in out["features"] + out["runtimes"]:
        for row in item["path"]:
            assert set(row).issuperset(_RUNG_KEYS)
            assert set(row).issuperset(_ROW_KEYS)
    for row in out["channels"]["path"]:
        assert set(row).issuperset(_RUNG_KEYS)
        assert set(row).issuperset(_ROW_KEYS)


# ── helper: input normalisation + unknown bucketing ─────────────────────────


def test_helper_normalises_feature_input(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["  CUSTOM_ALERTS  ", "custom_alerts", ""],
    )
    assert [item["key"] for item in out["features"]] == ["custom_alerts"]


def test_helper_canonicalises_runtime_aliases(ent):
    # claude-code -> claude_code
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        runtimes=["claude-code", "claude_code"],
    )
    # Both inputs collapse to the same canonical id -> ONE row.
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


def test_helper_unknown_feature_ids_echo_in_unknown(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["custom_alerts", "bogus_feat_id"],
    )
    assert [item["key"] for item in out["features"]] == ["custom_alerts"]
    assert out["unknown"]["features"] == ["bogus_feat_id"]


def test_helper_unknown_runtime_ids_echo_in_unknown(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        runtimes=[_pick_paid_runtime(ent), "bogus_runtime_alias"],
    )
    assert out["unknown"]["runtimes"] == ["bogus_runtime_alias"]


def test_helper_supply_order_preserved_for_features(ent):
    feats = sorted(ent.PAID_FEATURES)[:3]
    reversed_feats = list(reversed(feats))
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, features=reversed_feats
    )
    assert [item["key"] for item in out["features"]] == reversed_feats


# ── helper: capacity short-circuit ──────────────────────────────────────────


@pytest.mark.parametrize("bad", [0, -1, None])
def test_helper_capacity_short_circuit_on_bad_value(ent, bad):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["custom_alerts"],
        channels=bad,
    )
    assert out["channels"] is None


# ── helper: identity + lateral ──────────────────────────────────────────────


def test_helper_identity_yields_empty_paths_per_item(ent):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, ent.TIER_OSS, features=["custom_alerts", "sessions"]
    )
    for item in out["features"]:
        assert item["path"] == []


# ── helper: unknown / empty / garbage tier ──────────────────────────────────


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier", None])
def test_helper_unknown_from_tier_returns_none(ent, bad):
    out = ent.lock_reason_path_batch(
        bad, ent.TIER_ENTERPRISE, features=["custom_alerts"]
    )
    assert out is None


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier", None])
def test_helper_unknown_to_tier_returns_none(ent, bad):
    out = ent.lock_reason_path_batch(
        ent.TIER_OSS, bad, features=["custom_alerts"]
    )
    assert out is None


# ── helper: grace vs enforce parity ─────────────────────────────────────────


def test_helper_grace_vs_enforce_byte_identical(ent, monkeypatch):
    base = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["custom_alerts"],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.lock_reason_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        features=["custom_alerts"],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
    )
    assert base == enforced


# ── HTTP: happy path ────────────────────────────────────────────────────────


def test_api_returns_200_with_envelope(client, ent):
    rt = _pick_paid_runtime(ent)
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        f"?from=oss&to=enterprise&features=custom_alerts&runtimes={rt}"
        "&channels=99&retention_days=365&nodes=50"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["direction"] == "upgrade"
    assert len(body["features"]) == 1
    assert len(body["runtimes"]) == 1
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None
    assert body["unknown"] == {"features": [], "runtimes": []}


def test_api_runtime_alias_canonicalises(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=oss&to=enterprise&runtimes=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["runtimes"]) == 1
    assert body["runtimes"][0]["key"] == "claude_code"


def test_api_unknown_feature_echoed_in_unknown_bucket(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=oss&to=enterprise&features=custom_alerts,bogus_id"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["unknown"]["features"] == ["bogus_id"]
    assert [it["key"] for it in body["features"]] == ["custom_alerts"]


def test_api_identity_yields_empty_per_item_paths(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=oss&to=oss&features=custom_alerts"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["direction"] == "identity"
    assert body["features"][0]["path"] == []


# ── HTTP: error paths ───────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch?to=enterprise"
        "&features=custom_alerts"
    )
    assert resp.status_code == 400


def test_api_400_on_missing_to(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch?from=oss"
        "&features=custom_alerts"
    )
    assert resp.status_code == 400


def test_api_400_on_no_axis_supplied(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch?from=oss&to=enterprise"
    )
    assert resp.status_code == 400


def test_api_404_on_unknown_from_tier(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=bogus&to=enterprise&features=custom_alerts"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_404_on_unknown_to_tier(client):
    resp = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=oss&to=bogus&features=custom_alerts"
    )
    assert resp.status_code == 404


# ── HTTP: parity with scalar /lock-reason-path ──────────────────────────────


def test_api_feature_path_byte_equal_to_scalar_endpoint(client):
    resp_batch = client.get(
        "/api/entitlement/lock-reason-path-batch"
        "?from=oss&to=enterprise&features=custom_alerts"
    )
    resp_scalar = client.get(
        "/api/entitlement/lock-reason-path"
        "?from=oss&to=enterprise&feature=custom_alerts"
    )
    assert resp_batch.status_code == 200 and resp_scalar.status_code == 200
    batch_path = resp_batch.get_json()["features"][0]["path"]
    scalar_path = resp_scalar.get_json()["path"]
    assert batch_path == scalar_path
