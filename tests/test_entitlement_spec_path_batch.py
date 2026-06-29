"""Tests for ``feature_spec_path_batch(from, to, features)`` /
``runtime_spec_path_batch(from, to, runtimes)`` plus their HTTP
endpoints.

These are the batch siblings of ``feature_spec_path`` /
``runtime_spec_path``: where the scalar path helpers walk one
feature / one runtime across the rungs between two tiers, the batch
helpers walk N items in ONE round-trip.

Each per-item ``path`` must be byte-identical to the matching scalar
:func:`feature_spec_path` / :func:`runtime_spec_path` payload for the
same ``(from, to, item)`` triple -- pinned by the parity tests below so
the scalar and batch path accessors cannot drift.

Coverage:

* per-item ``path`` byte-equal to the scalar ``_spec_path`` payload
* rung walk identical across items in the same batch (rungs are
  item-agnostic)
* batch envelope mirrors ``/feature-spec-path`` / ``/runtime-spec-path``
  (from / from_label / from_rank / to / to_label / to_rank / direction)
  plus ``features`` / ``runtimes`` + ``unknown``
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown ids echoed in ``unknown[]`` instead of 404'ing the call
* runtime aliases canonicalise (``claude-code`` -> ``claude_code``) and
  collapse against already-supplied canonical ids without double-emitting
* identity ``from == to`` yields an envelope with one entry per supplied
  id whose ``path`` is ``[]``
* lateral (same rank) yields one-row paths per supplied id
* unknown / empty / garbage tier returns ``None`` (helper) / 400 / 404
  (HTTP)
* helpers never raise -- a row failure short-circuits that item into
  ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoints 400 on missing / empty input, 404 on unknown tier,
  never 5xx on a row failure
* grace vs enforce yields identical rows
"""
from __future__ import annotations

import importlib

import pytest


_FEATURE_ITEM_KEYS = {"feature", "path"}
_RUNTIME_ITEM_KEYS = {"runtime", "path"}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
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


# ── feature_spec_path_batch: helper-level ────────────────────────────────────


def test_feature_helper_returns_dict_shape(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["custom_alerts", "sessions"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"features", "unknown"}
    assert isinstance(out["features"], list)
    assert isinstance(out["unknown"], list)


def test_feature_helper_each_item_carries_feature_and_path(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["custom_alerts", "sessions"]
    )
    for item in out["features"]:
        assert set(item.keys()) == _FEATURE_ITEM_KEYS
        assert isinstance(item["feature"], str)
        assert isinstance(item["path"], list)


def test_feature_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-item ``path`` is byte-identical to the scalar
    :func:`feature_spec_path` payload for the same triple."""
    feats = ["custom_alerts", "sessions", "siem_export"]
    out = ent.feature_spec_path_batch(ent.TIER_OSS, ent.TIER_ENTERPRISE, feats)
    by_id = {item["feature"]: item["path"] for item in out["features"]}
    for fid in feats:
        scalar = ent.feature_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, fid
        )
        assert by_id[fid] == scalar


def test_feature_helper_rung_walk_item_agnostic(ent):
    """The walked rung sequence is feature-agnostic -- all per-item
    paths in the batch share the same rung sequence."""
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["custom_alerts", "sessions", "siem_export"],
    )
    rung_sequences = [
        [row["rung"] for row in item["path"]] for item in out["features"]
    ]
    assert len(rung_sequences) == 3
    assert rung_sequences[0] == rung_sequences[1] == rung_sequences[2]


def test_feature_helper_supply_order_preserved(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["siem_export", "sessions", "custom_alerts"],
    )
    assert [item["feature"] for item in out["features"]] == [
        "siem_export",
        "sessions",
        "custom_alerts",
    ]


def test_feature_helper_normalises_input(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["  CUSTOM_ALERTS  ", "sessions", "custom_alerts", ""],
    )
    # Duplicates collapse, whitespace stripped, lowercased.
    assert [item["feature"] for item in out["features"]] == [
        "custom_alerts",
        "sessions",
    ]


def test_feature_helper_unknown_ids_echoed(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["custom_alerts", "bogus_id", "still_bogus"],
    )
    assert [item["feature"] for item in out["features"]] == ["custom_alerts"]
    assert set(out["unknown"]) == {"bogus_id", "still_bogus"}


def test_feature_helper_identity_yields_empty_paths(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ["custom_alerts", "sessions"]
    )
    assert out["unknown"] == []
    for item in out["features"]:
        assert item["path"] == []


def test_feature_helper_lateral_yields_one_row_paths(ent):
    out = ent.feature_spec_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_PRO, ["custom_alerts", "sessions"]
    )
    for item in out["features"]:
        assert len(item["path"]) == 1
        assert item["path"][0]["rung"] == ent.TIER_PRO


def test_feature_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.feature_spec_path_batch(
            "not_a_tier", ent.TIER_ENTERPRISE, ["custom_alerts"]
        )
        is None
    )


def test_feature_helper_unknown_to_tier_returns_none(ent):
    assert (
        ent.feature_spec_path_batch(
            ent.TIER_OSS, "not_a_tier", ["custom_alerts"]
        )
        is None
    )


def test_feature_helper_empty_features_yields_empty_envelope(ent):
    out = ent.feature_spec_path_batch(ent.TIER_OSS, ent.TIER_ENTERPRISE, [])
    assert out == {"features": [], "unknown": []}


def test_feature_helper_garbage_inputs_never_raise(ent):
    assert ent.feature_spec_path_batch("", "", []) is None
    assert ent.feature_spec_path_batch(None, None, None) is None  # type: ignore[arg-type]
    assert ent.feature_spec_path_batch("  ", "  ", "  ") is None


def test_feature_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    feats = ["custom_alerts", "sessions"]
    grace = ent.feature_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, feats
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.feature_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, feats
    )
    assert grace == enforced


def test_feature_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-item failure pushes that id into ``unknown[]`` while the rest of
    the batch keeps building."""
    real = ent.feature_spec_path

    def fake(f, t, fid):
        if fid == "custom_alerts":
            raise RuntimeError("boom")
        return real(f, t, fid)

    monkeypatch.setattr(ent, "feature_spec_path", fake)
    out = ent.feature_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["custom_alerts", "sessions"],
    )
    assert [item["feature"] for item in out["features"]] == ["sessions"]
    assert "custom_alerts" in out["unknown"]


# ── runtime_spec_path_batch: helper-level ────────────────────────────────────


def test_runtime_helper_returns_dict_shape(ent):
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["openclaw", "claude_code"]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"runtimes", "unknown"}


def test_runtime_helper_per_item_path_byte_equal_to_scalar(ent):
    rts = ["openclaw", "claude_code"]
    out = ent.runtime_spec_path_batch(ent.TIER_OSS, ent.TIER_ENTERPRISE, rts)
    by_id = {item["runtime"]: item["path"] for item in out["runtimes"]}
    for rid in rts:
        scalar = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, rid)
        assert by_id[rid] == scalar


def test_runtime_helper_rung_walk_item_agnostic(ent):
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["openclaw", "claude_code"]
    )
    rung_sequences = [
        [row["rung"] for row in item["path"]] for item in out["runtimes"]
    ]
    assert len(rung_sequences) == 2
    assert rung_sequences[0] == rung_sequences[1]


def test_runtime_helper_alias_canonicalised(ent):
    """``claude-code`` resolves to ``claude_code`` and the per-row
    ``runtime`` value carries the canonical id, never the alias."""
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["claude-code"]
    )
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["runtime"] == "claude_code"
    assert out["unknown"] == []


def test_runtime_helper_alias_collapses_against_canonical(ent):
    """Supplying an alias and its canonical id only emits one row."""
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, ["claude_code", "claude-code"]
    )
    canon_ids = [item["runtime"] for item in out["runtimes"]]
    assert canon_ids.count("claude_code") == 1
    assert out["unknown"] == []


def test_runtime_helper_unknown_ids_echoed(ent):
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["claude_code", "bogus_runtime"],
    )
    assert [item["runtime"] for item in out["runtimes"]] == ["claude_code"]
    assert "bogus_runtime" in out["unknown"]


def test_runtime_helper_identity_yields_empty_paths(ent):
    out = ent.runtime_spec_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ["openclaw", "claude_code"]
    )
    for item in out["runtimes"]:
        assert item["path"] == []


def test_runtime_helper_lateral_yields_one_row_paths(ent):
    out = ent.runtime_spec_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_PRO, ["openclaw", "claude_code"]
    )
    for item in out["runtimes"]:
        assert len(item["path"]) == 1


def test_runtime_helper_unknown_tier_returns_none(ent):
    assert (
        ent.runtime_spec_path_batch(
            "not_a_tier", ent.TIER_ENTERPRISE, ["claude_code"]
        )
        is None
    )
    assert (
        ent.runtime_spec_path_batch(
            ent.TIER_OSS, "not_a_tier", ["claude_code"]
        )
        is None
    )


def test_runtime_helper_empty_runtimes_yields_empty_envelope(ent):
    out = ent.runtime_spec_path_batch(ent.TIER_OSS, ent.TIER_ENTERPRISE, [])
    assert out == {"runtimes": [], "unknown": []}


def test_runtime_helper_garbage_inputs_never_raise(ent):
    assert ent.runtime_spec_path_batch("", "", []) is None
    assert ent.runtime_spec_path_batch(None, None, None) is None  # type: ignore[arg-type]
    assert ent.runtime_spec_path_batch("  ", "  ", "  ") is None


def test_runtime_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    rts = ["openclaw", "claude_code"]
    grace = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, rts
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.runtime_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, rts
    )
    assert grace == enforced


def test_runtime_helper_row_failure_short_circuits_item(ent, monkeypatch):
    real = ent.runtime_spec_path

    def fake(f, t, rid):
        if (rid or "").strip().lower() == "claude_code":
            raise RuntimeError("boom")
        return real(f, t, rid)

    monkeypatch.setattr(ent, "runtime_spec_path", fake)
    out = ent.runtime_spec_path_batch(
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["openclaw", "claude_code"],
    )
    assert [item["runtime"] for item in out["runtimes"]] == ["openclaw"]
    assert "claude_code" in out["unknown"]


# ── HTTP: /api/entitlement/feature-spec-path-batch ───────────────────────────


def test_feature_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/feature-spec-path-batch"
        "?to=cloud_pro&features=sessions"
    )
    assert r.status_code == 400


def test_feature_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/feature-spec-path-batch?from=oss&features=sessions"
    )
    assert r.status_code == 400


def test_feature_api_400_on_missing_features(client):
    r = client.get(
        "/api/entitlement/feature-spec-path-batch?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply features=<csv>"


def test_feature_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-path-batch"
        "?from=not_a_tier&to=enterprise&features=sessions"
    )
    assert r.status_code == 404


def test_feature_api_404_on_unknown_to_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-path-batch"
        "?from=oss&to=not_a_tier&features=sessions"
    )
    assert r.status_code == 404


def test_feature_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&features=custom_alerts,sessions"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()).issuperset(_ENVELOPE_KEYS)
    assert "features" in body
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert [item["feature"] for item in body["features"]] == [
        "custom_alerts",
        "sessions",
    ]
    for item in body["features"]:
        assert item["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_feature_api_unknown_id_echoed(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&features=custom_alerts,bogus_id"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["feature"] for item in body["features"]] == ["custom_alerts"]
    assert body["unknown"] == ["bogus_id"]


def test_feature_api_identity_empty_paths(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path-batch?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&features=custom_alerts,sessions"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    for item in body["features"]:
        assert item["path"] == []


def test_feature_api_per_item_path_matches_scalar_route(client, ent):
    batch = client.get(
        f"/api/entitlement/feature-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&features=custom_alerts,sessions"
    ).get_json()
    for item in batch["features"]:
        scalar = client.get(
            f"/api/entitlement/feature-spec-path?from={ent.TIER_OSS}"
            f"&to={ent.TIER_ENTERPRISE}&feature={item['feature']}"
        ).get_json()
        assert item["path"] == scalar["path"]


# ── HTTP: /api/entitlement/runtime-spec-path-batch ───────────────────────────


def test_runtime_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path-batch"
        "?to=cloud_pro&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_runtime_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path-batch?from=oss&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_runtime_api_400_on_missing_runtimes(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path-batch?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply runtimes=<csv>"


def test_runtime_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path-batch"
        "?from=not_a_tier&to=enterprise&runtimes=claude_code"
    )
    assert r.status_code == 404


def test_runtime_api_404_on_unknown_to_tier(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path-batch"
        "?from=oss&to=not_a_tier&runtimes=claude_code"
    )
    assert r.status_code == 404


def test_runtime_api_happy_path(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtimes=openclaw,claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert "runtimes" in body and "unknown" in body
    assert body["direction"] == "upgrade"
    assert [item["runtime"] for item in body["runtimes"]] == [
        "openclaw",
        "claude_code",
    ]


def test_runtime_api_alias_canonicalised(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtimes=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["runtime"] for item in body["runtimes"]] == ["claude_code"]


def test_runtime_api_unknown_id_echoed(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtimes=claude_code,bogus_runtime"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["runtime"] for item in body["runtimes"]] == ["claude_code"]
    assert "bogus_runtime" in body["unknown"]


def test_runtime_api_identity_empty_paths(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path-batch?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&runtimes=openclaw,claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    for item in body["runtimes"]:
        assert item["path"] == []


def test_runtime_api_per_item_path_matches_scalar_route(client, ent):
    batch = client.get(
        f"/api/entitlement/runtime-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtimes=openclaw,claude_code"
    ).get_json()
    for item in batch["runtimes"]:
        scalar = client.get(
            f"/api/entitlement/runtime-spec-path?from={ent.TIER_OSS}"
            f"&to={ent.TIER_ENTERPRISE}&runtime={item['runtime']}"
        ).get_json()
        assert item["path"] == scalar["path"]
