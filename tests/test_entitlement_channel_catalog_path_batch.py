"""Tests for ``clawmetry.entitlements.channel_catalog_path_batch(from, to)``
plus the ``GET /api/entitlement/channel-catalog-path-batch`` endpoint.

Batch sibling of :func:`channel_catalog_path`: where the scalar path
helper walks one ``(from, to)`` pair and hydrates the full channel
catalogue at each rung, the batch helper walks N candidate destinations
from one source in ONE round-trip. Channel-axis twin of
:func:`feature_catalog_path_batch` and :func:`runtime_catalog_path_batch`.

Because every chat-channel adapter is FREE at every tier, each rung's
inner ``channels`` list is byte-identical to :func:`channel_catalog` --
the scalar path helper already pins that invariant; here we pin that the
batch helper never drifts from the scalar.

Pins:

* per-destination ``path`` byte-equal to the scalar
  :func:`channel_catalog_path` payload for the same ``(from, to)``
  pair
* per-rung row shape mirrors :func:`channel_catalog_path`
  (``tier``, ``tier_label``, ``tier_rank``, ``channels``)
* per-destination ``direction`` derived from the same ranks the scalar
  endpoint uses (identity / lateral / upgrade / downgrade)
* batch envelope mirrors ``/tier-catalog-path-batch`` /
  ``/feature-catalog-path-batch`` / ``/runtime-catalog-path-batch``
  on the source side (``from`` / ``from_label`` / ``from_rank``) and
  carries ``tiers`` + ``unknown``
* input normalised (whitespace stripped, lowercased, duplicates dropped,
  first-seen order preserved)
* unknown destination ids echoed in ``unknown[]`` instead of 404'ing
  the call
* identity ``from == to`` yields a per-destination entry whose ``path``
  is ``[]``
* lateral (same rank) yields a one-row per-destination ``path``
* ``trial`` accepted as a destination and as a source
* unknown / empty / garbage ``from_tier`` returns ``None`` (helper) /
  400 / 404 (HTTP)
* helper never raises -- a per-destination failure short-circuits that
  id into ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoint 400 on missing / empty input, 404 on unknown source
  tier, never 5xx on a row failure
* grace vs enforce yields identical rows
"""
from __future__ import annotations

import importlib

import pytest


_INNER_ROW_KEYS = {"tier", "tier_label", "tier_rank", "channels"}

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
    from flask import Flask

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── helper-level: shape ──────────────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_full_envelope(ent):
    out = ent.channel_catalog_path_batch(
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


def test_helper_per_rung_row_shape(ent):
    """Per-rung rows carry the same 4-key shape as
    :func:`channel_catalog_path` -- the ``_path`` family stays in
    lock-step."""
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    assert item["path"]
    for row in item["path"]:
        assert set(row.keys()) == _INNER_ROW_KEYS
        assert isinstance(row["channels"], list)
        assert row["channels"]  # never empty


# ── helper-level: parity with scalar ─────────────────────────────────────────


def test_helper_per_item_path_byte_equal_to_scalar(ent):
    """Pin: per-destination ``path`` is byte-identical to the scalar
    :func:`channel_catalog_path` payload for the same ``(from, to)``
    pair. If a future refactor teaches the batch helper to skip a rung
    or a per-channel column, this test fails."""
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.channel_catalog_path_batch(ent.TIER_OSS, candidates)
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.channel_catalog_path(ent.TIER_OSS, tid)
        assert by_id[tid] == scalar


def test_helper_per_rung_channels_byte_equal_to_channel_catalog(ent):
    """Cross-check: each rung's inner ``channels`` list equals
    :func:`channel_catalog` -- inherited from the scalar
    :func:`channel_catalog_path` "channels are always free" pin."""
    baseline = ent.channel_catalog()
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    for row in item["path"]:
        assert row["channels"] == baseline


def test_helper_per_row_free_posture_preserved(ent):
    """Belt-and-braces: even if a future tier flip pretended to gate
    the channel axis, every row reported by this batch helper must
    still surface ``free=True`` / ``allowed=True`` / ``locked=False``
    / ``entitled=True``."""
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    for row in item["path"]:
        for ch in row["channels"]:
            assert ch["free"] is True
            assert ch["allowed"] is True
            assert ch["locked"] is False
            assert ch["entitled"] is True
            assert ch["tier"] == "free"


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
    out = ent.channel_catalog_path_batch(ent.TIER_CLOUD_STARTER, candidates)
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


def test_helper_per_item_to_label_matches_scalar_pin(ent):
    """Per-destination ``to_label`` / ``to_rank`` byte-equal the
    :func:`tier_label` / :func:`tier_rank` helpers (matching the
    sibling ``_path_batch`` envelopes)."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.channel_catalog_path_batch(ent.TIER_OSS, candidates)
    for item in out["tiers"]:
        assert item["to_label"] == ent.tier_label(item["to"])
        assert item["to_rank"] == ent.tier_rank(item["to"])


# ── helper-level: input normalisation ────────────────────────────────────────


def test_helper_supply_order_preserved(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
    )
    assert [item["to"] for item in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_helper_normalises_input(ent):
    out = ent.channel_catalog_path_batch(
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


def test_helper_from_tier_normalised(ent):
    """``from_tier`` also normalised (whitespace + case) -- matches the
    scalar :func:`channel_catalog_path`."""
    a = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    b = ent.channel_catalog_path_batch(
        "  OSS  ", [ent.TIER_ENTERPRISE]
    )
    assert a == b


def test_helper_unknown_destination_ids_echoed(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, "bogus_tier", "still_bogus"],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert set(out["unknown"]) == {"bogus_tier", "still_bogus"}


# ── helper-level: direction branches ─────────────────────────────────────────


def test_helper_identity_yields_empty_path(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    by_id = {item["to"]: item for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO]["direction"] == "identity"
    assert by_id[ent.TIER_CLOUD_PRO]["path"] == []
    assert by_id[ent.TIER_ENTERPRISE]["direction"] == "upgrade"


def test_helper_lateral_yields_one_row_path(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_CLOUD_PRO, [ent.TIER_PRO]
    )
    assert len(out["tiers"]) == 1
    item = out["tiers"][0]
    assert item["direction"] == "lateral"
    assert len(item["path"]) == 1
    assert item["path"][0]["tier"] == ent.TIER_PRO


def test_helper_upgrade_walks_intermediate_rungs(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    item = out["tiers"][0]
    assert item["direction"] == "upgrade"
    rungs = [row["tier"] for row in item["path"]]
    assert rungs[-1] == ent.TIER_ENTERPRISE
    assert ent.TIER_OSS not in rungs


def test_helper_downgrade_walks_descending(ent):
    out = ent.channel_catalog_path_batch(
        ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    item = out["tiers"][0]
    assert item["direction"] == "downgrade"
    rungs = [row["tier"] for row in item["path"]]
    ranks = [ent.tier_rank(r) for r in rungs]
    assert ranks == sorted(ranks, reverse=True)


def test_helper_all_four_branches_in_one_batch(ent):
    """Single call covers identity + lateral + upgrade + downgrade."""
    out = ent.channel_catalog_path_batch(
        ent.TIER_CLOUD_PRO,
        [
            ent.TIER_CLOUD_PRO,       # identity
            ent.TIER_PRO,             # lateral
            ent.TIER_ENTERPRISE,      # upgrade
            ent.TIER_OSS,             # downgrade
        ],
    )
    by_id = {item["to"]: item["direction"] for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "upgrade"
    assert by_id[ent.TIER_OSS] == "downgrade"


# ── helper-level: trial endpoint ─────────────────────────────────────────────


def test_helper_trial_destination_accepted(ent):
    """``trial`` is a valid endpoint (matching
    :func:`channel_catalog_path` semantics) even though it is excluded
    from the walked intermediate rungs."""
    out = ent.channel_catalog_path_batch(ent.TIER_OSS, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_TRIAL]


def test_helper_trial_source_accepted(ent):
    """``trial`` is a valid source (matching
    :func:`channel_catalog_path` semantics)."""
    out = ent.channel_catalog_path_batch(
        ent.TIER_TRIAL, [ent.TIER_ENTERPRISE]
    )
    assert out is not None
    assert out["unknown"] == []
    (item,) = out["tiers"]
    assert item["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_helper_trial_never_appears_as_intermediate_rung(ent):
    """``trial`` is not purchasable -- it must never appear as a stop
    on a path between purchasable tiers."""
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    rungs = [row["tier"] for row in item["path"]]
    assert ent.TIER_TRIAL not in rungs


# ── helper-level: error / edge cases ─────────────────────────────────────────


def test_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.channel_catalog_path_batch("not_a_tier", [ent.TIER_ENTERPRISE])
        is None
    )


def test_helper_empty_destinations_yields_empty_envelope(ent):
    out = ent.channel_catalog_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}


def test_helper_garbage_from_tier_returns_none(ent):
    assert ent.channel_catalog_path_batch("", []) is None
    assert ent.channel_catalog_path_batch(None, None) is None  # type: ignore[arg-type]
    assert ent.channel_catalog_path_batch("  ", []) is None
    assert ent.channel_catalog_path_batch(123, []) is None  # type: ignore[arg-type]


def test_helper_grace_and_enforce_yield_identical_output(ent, monkeypatch):
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    grace = ent.channel_catalog_path_batch(ent.TIER_OSS, candidates)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.channel_catalog_path_batch(ent.TIER_OSS, candidates)
    assert grace == enforced


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-destination failure pushes that id into ``unknown[]``
    while the rest of the batch keeps building."""
    real = ent.channel_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "channel_catalog_path", fake)
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


def test_helper_row_none_return_short_circuits_item(ent, monkeypatch):
    """A per-destination ``None`` return also pushes that id into
    ``unknown[]`` (helper never emits a row with ``path=None``)."""
    real = ent.channel_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            return None
        return real(f, t)

    monkeypatch.setattr(ent, "channel_catalog_path", fake)
    out = ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── HTTP: /api/entitlement/channel-catalog-path-batch ────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch?to=cloud_pro,enterprise"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch?from=oss"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "supply to=<csv>"


def test_api_400_on_empty_to(client):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch?from=oss&to=,,"
    )
    assert r.status_code == 400


def test_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        "?from=not_a_tier&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_api_200_with_unknown_destination_bucketed(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
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
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "identity"
    assert body["tiers"][0]["path"] == []


def test_api_lateral_branch(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "lateral"
    assert len(body["tiers"][0]["path"]) == 1
    assert body["tiers"][0]["path"][0]["tier"] == ent.TIER_PRO


def test_api_downgrade_branch(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "downgrade"


def test_api_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/channel-catalog-path?from=&to=`` ``path`` payload for
    the same ``(from, to)`` pair."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={','.join(candidates)}"
    ).get_json()
    for item in batch["tiers"]:
        scalar = client.get(
            "/api/entitlement/channel-catalog-path"
            f"?from={ent.TIER_OSS}&to={item['to']}"
        ).get_json()
        assert item["path"] == scalar["path"]
        assert item["direction"] == scalar["direction"]
        assert item["to_label"] == scalar["to_label"]
        assert item["to_rank"] == scalar["to_rank"]


def test_api_input_normalised(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to=  CLOUD_PRO  ,cloud_starter,cloud_pro,"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_api_trial_endpoint_accepted(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    assert body["unknown"] == []
    (item,) = body["tiers"]
    assert item["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_api_grace_and_enforce_yield_identical_body(
    client, ent, monkeypatch
):
    grace = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    ).get_json()
    assert grace == enforced


def test_api_never_5xxs_on_row_failure(client, ent, monkeypatch):
    """A per-destination synthesis crash short-circuits to ``unknown[]``
    -- the endpoint still returns 200 with a rendered envelope."""
    real = ent.channel_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "channel_catalog_path", fake)
    r = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in body["unknown"]
