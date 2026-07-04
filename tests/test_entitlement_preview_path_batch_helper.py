"""Real-behavior tests for ``clawmetry.entitlements.preview_path_batch``
and its POST endpoint ``/api/entitlement/preview-path-batch``.

Companion to ``test_entitlement_preview_path_batch.py`` (which patches
the entitlements module with a lightweight stub). Where that suite pins
the endpoint contract shape, this suite pins the real helper's behavior
against the actual tier catalogue -- parity with the scalar
:func:`preview_path`, direction geometry, input normalisation, unknown
id bucketing, grace-vs-enforce byte parity, and never-raises posture.

Batch sibling of :func:`preview_path`: where the scalar path helper
walks one ``(from, to)`` pair, the batch walks N candidate destinations
from one source in ONE round-trip. Each per-destination ``path`` must
be byte-identical to the matching scalar :func:`preview_path` payload
for the same ``(from, to)`` pair -- the parity test below pins this so
the scalar and batch path helpers cannot drift.
"""
from __future__ import annotations

import importlib

import pytest


_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
    "current_tier",
    "grace",
    "enforced",
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


# ── helper-level: shape ──────────────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.preview_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_row_envelope(ent):
    out = ent.preview_path_batch(
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


def test_helper_each_row_is_full_preview_snapshot(ent):
    """Every per-rung row is a full :func:`preview` snapshot -- shape
    parity with :func:`preview_path`, which is itself byte-equal to
    :func:`preview` per rung."""
    out = ent.preview_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    item = out["tiers"][0]
    assert item["path"], "expected at least one rung in the path"
    scalar_shape = set(ent.preview(ent.TIER_CLOUD_STARTER).keys())
    for row in item["path"]:
        assert set(row.keys()) == scalar_shape
        assert row.get("source") == "preview"
        assert row.get("grace") is False


# ── helper-level: parity with scalar ─────────────────────────────────────────


def test_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-destination ``path`` is byte-identical to the scalar
    :func:`preview_path` payload for the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.preview_path_batch(ent.TIER_OSS, candidates)
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.preview_path(ent.TIER_OSS, tid)
        assert by_id[tid] == scalar


def test_helper_per_item_direction_matches_rank_geometry(ent):
    candidates = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.preview_path_batch(ent.TIER_CLOUD_STARTER, candidates)
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
    out = ent.preview_path_batch(
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
    )
    assert [item["to"] for item in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_helper_normalises_input(ent):
    out = ent.preview_path_batch(
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
    out = ent.preview_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, "bogus_tier", "still_bogus"],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert set(out["unknown"]) == {"bogus_tier", "still_bogus"}


# ── helper-level: direction branches ─────────────────────────────────────────


def test_helper_identity_yields_empty_path(ent):
    out = ent.preview_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    by_id = {item["to"]: item for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO]["direction"] == "identity"
    assert by_id[ent.TIER_CLOUD_PRO]["path"] == []
    assert by_id[ent.TIER_ENTERPRISE]["direction"] == "upgrade"


def test_helper_upgrade_walks_intermediate_rungs(ent):
    out = ent.preview_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    item = out["tiers"][0]
    assert item["direction"] == "upgrade"
    rungs = [row["tier"] for row in item["path"]]
    assert rungs[-1] == ent.TIER_ENTERPRISE
    assert ent.TIER_OSS not in rungs


def test_helper_downgrade_walks_descending(ent):
    out = ent.preview_path_batch(ent.TIER_ENTERPRISE, [ent.TIER_OSS])
    item = out["tiers"][0]
    assert item["direction"] == "downgrade"
    ranks = [ent.tier_rank(row["tier"]) for row in item["path"]]
    assert ranks == sorted(ranks, reverse=True)


def test_helper_trial_destination_accepted(ent):
    out = ent.preview_path_batch(ent.TIER_OSS, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_TRIAL]


# ── helper-level: error / edge cases ─────────────────────────────────────────


def test_helper_unknown_from_tier_returns_none(ent):
    assert ent.preview_path_batch("not_a_tier", [ent.TIER_ENTERPRISE]) is None


def test_helper_empty_destinations_yields_empty_envelope(ent):
    out = ent.preview_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}


def test_helper_garbage_inputs_never_raise(ent):
    assert ent.preview_path_batch("", []) is None
    assert ent.preview_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.preview_path_batch("  ", "  ") is None


def test_helper_grace_and_enforce_yield_identical_output(ent, monkeypatch):
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    grace = ent.preview_path_batch(ent.TIER_OSS, candidates)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.preview_path_batch(ent.TIER_OSS, candidates)
    assert grace == enforced


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-destination failure pushes that id into ``unknown[]``
    while the rest of the batch keeps building."""
    real = ent.preview_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "preview_path", fake)
    out = ent.preview_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── HTTP: POST /api/entitlement/preview-path-batch ───────────────────────────


def test_api_400_on_missing_from(client):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"to": ["enterprise"]},
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": "oss"},
    )
    assert r.status_code == 400


def test_api_400_on_empty_to(client):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": "oss", "to": []},
    )
    assert r.status_code == 400


def test_api_404_on_unknown_from_tier(client):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": "not_a_tier", "to": ["enterprise"]},
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_api_200_with_unknown_destination_bucketed(client, ent):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": ent.TIER_OSS, "to": [ent.TIER_CLOUD_PRO, "bogus_tier"]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_api_happy_path_response_envelope(client, ent):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={
            "from": ent.TIER_OSS,
            "to": [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
        },
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert isinstance(body["from_label"], str)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)
    tos = [item["to"] for item in body["tiers"]]
    assert tos == [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    for item in body["tiers"]:
        assert item["direction"] == "upgrade"


def test_api_identity_branch(client, ent):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": ent.TIER_CLOUD_PRO, "to": [ent.TIER_CLOUD_PRO]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "identity"
    assert body["tiers"][0]["path"] == []


def test_api_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/preview-path?from=&to=`` payload for the same
    ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": ent.TIER_OSS, "to": candidates},
    ).get_json()
    by_id = {item["to"]: item["path"] for item in batch["tiers"]}
    for tid in candidates:
        scalar = client.get(
            f"/api/entitlement/preview-path?from={ent.TIER_OSS}&to={tid}"
        ).get_json()
        assert by_id[tid] == scalar["path"]


def test_api_never_5xxs_on_helper_failure(client, ent, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("synthesis failure")

    monkeypatch.setattr(ent, "preview_path_batch", boom)
    r = client.post(
        "/api/entitlement/preview-path-batch",
        json={"from": ent.TIER_OSS, "to": [ent.TIER_ENTERPRISE]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []


def test_api_400_on_non_json_body(client):
    r = client.post(
        "/api/entitlement/preview-path-batch",
        data="not json",
        content_type="text/plain",
    )
    assert r.status_code == 400
