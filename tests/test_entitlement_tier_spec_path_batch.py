"""Tests for ``clawmetry.entitlements.tier_spec_path_batch(from, to_tiers)``
+ the ``GET /api/entitlement/tier-spec-path-batch`` endpoint.

Batch sibling of :func:`tier_spec_path` (walks the rungs between ONE
``(from, to)`` pair). This helper walks the rungs between ONE source and
N candidate destinations in ONE round-trip. Multi-destination axis
mirrors :func:`tier_spec_at_batch` (fixed-source what-if matrix over many
targets) the same way :func:`feature_spec_path_batch` mirrors
:func:`feature_spec_at_batch`.

Pins:

* per-destination ``path`` list byte-equals the scalar
  :func:`tier_spec_path` helper for the same ``(from, to)`` pair
* per-destination ``direction`` derived from the same rank geometry the
  scalar ``/tier-spec-path`` endpoint uses (identity / lateral / upgrade /
  downgrade), matching the scalar branch it takes for the same pair
* per-destination ``to_label`` / ``to_rank`` byte-equal :func:`tier_label`
  / :func:`tier_rank` for the same id
* supply order preserved through input normalisation
  (whitespace stripped, lowercased, duplicates dropped, first-seen order
  preserved)
* unknown destination ids echoed in ``unknown[]`` -- helper does not
  short-circuit on partially-bad callers
* all four direction branches surface: identity / lateral / upgrade /
  downgrade
* trial IS accepted as a destination (identity + lateral branches);
  excluded from walked intermediate rungs the way :func:`tier_spec_path`
  already excludes it
* per-destination row-failure short-circuits that id into ``unknown[]``
  instead of raising
* grace vs enforce yields byte-identical helper output (walks the static
  per-tier maps via :func:`tier_spec_at`)
* empty / unknown ``from_tier`` returns ``None``; garbage inputs never
  raise
* empty destinations returns ``{"tiers": [], "unknown": []}``
* HTTP: 400 on missing / empty ``from`` or ``to``, 404 on unknown ``from``,
  200 with bucketed unknowns for destination ids; envelope keys pinned
* HTTP per-destination ``path`` byte-equals the scalar
  ``/api/entitlement/tier-spec-path`` payload's ``path``
* HTTP grace-vs-enforce body parity
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
    "tiers",
    "unknown",
}
_ROW_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
}


# ── helper-level: shape + invariants ─────────────────────────────────────────


def test_returns_dict_with_tiers_and_unknown(ent):
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)
    assert len(out["tiers"]) == 2
    assert out["unknown"] == []


def test_each_row_has_the_row_key_set(ent):
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    )
    for row in out["tiers"]:
        assert set(row.keys()) == _ROW_KEYS


def test_per_destination_path_byte_equals_scalar(ent):
    """``path`` for each destination must be byte-identical to the scalar
    :func:`tier_spec_path(from, to)` payload for the same ``(from, to)``
    pair -- the parity pin so scalar and batch cannot drift."""
    f = ent.TIER_OSS
    tos = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ]
    out = ent.tier_spec_path_batch(f, tos)
    by_to = {row["to"]: row for row in out["tiers"]}
    for tid in tos:
        assert by_to[tid]["path"] == ent.tier_spec_path(f, tid)


def test_per_destination_to_label_and_to_rank_match_helpers(ent):
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, ent.TIER_PRO, ent.TIER_ENTERPRISE],
    )
    for row in out["tiers"]:
        assert row["to_label"] == ent.tier_label(row["to"])
        assert row["to_rank"] == ent.tier_rank(row["to"])


def test_direction_identity_when_to_equals_from(ent):
    out = ent.tier_spec_path_batch(ent.TIER_CLOUD_PRO, [ent.TIER_CLOUD_PRO])
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_direction_lateral_when_same_rank_different_id(ent):
    # cloud_pro and pro both at collapsed rank 2
    out = ent.tier_spec_path_batch(ent.TIER_CLOUD_PRO, [ent.TIER_PRO])
    assert out["tiers"][0]["direction"] == "lateral"
    assert len(out["tiers"][0]["path"]) == 1
    assert out["tiers"][0]["path"][0]["id"] == ent.TIER_PRO


def test_direction_upgrade_when_to_rank_above_from(ent):
    out = ent.tier_spec_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    assert out["tiers"][0]["direction"] == "upgrade"
    assert out["tiers"][0]["path"][-1]["id"] == ent.TIER_ENTERPRISE


def test_direction_downgrade_when_to_rank_below_from(ent):
    out = ent.tier_spec_path_batch(ent.TIER_ENTERPRISE, [ent.TIER_OSS])
    assert out["tiers"][0]["direction"] == "downgrade"
    assert out["tiers"][0]["path"][-1]["id"] == ent.TIER_OSS


def test_all_four_direction_branches_in_one_batch(ent):
    """One batch surfaces all four direction branches at once -- pins the
    per-destination geometry against the pairwise scalar mapping."""
    f = ent.TIER_CLOUD_PRO
    out = ent.tier_spec_path_batch(
        f,
        [
            ent.TIER_CLOUD_PRO,  # identity
            ent.TIER_PRO,  # lateral (both rank 2)
            ent.TIER_ENTERPRISE,  # upgrade
            ent.TIER_OSS,  # downgrade
        ],
    )
    by_to = {row["to"]: row["direction"] for row in out["tiers"]}
    assert by_to[ent.TIER_CLOUD_PRO] == "identity"
    assert by_to[ent.TIER_PRO] == "lateral"
    assert by_to[ent.TIER_ENTERPRISE] == "upgrade"
    assert by_to[ent.TIER_OSS] == "downgrade"


def test_supply_order_preserved(ent):
    tos = [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]
    out = ent.tier_spec_path_batch(ent.TIER_OSS, tos)
    assert [row["to"] for row in out["tiers"]] == tos


def test_whitespace_case_and_duplicates_normalised(ent):
    tos = [
        "  ENTERPRISE  ",
        "cloud_pro",
        "ENTERPRISE",  # duplicate after normalisation
        "  Cloud_Pro ",  # another duplicate
        "cloud_starter",
    ]
    out = ent.tier_spec_path_batch(ent.TIER_OSS, tos)
    assert [row["to"] for row in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_unknown_destinations_bucketed_not_short_circuiting(ent):
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS,
        [
            ent.TIER_CLOUD_PRO,
            "not_a_tier",
            ent.TIER_ENTERPRISE,
            "still_not_a_tier",
        ],
    )
    assert [row["to"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    assert out["unknown"] == ["not_a_tier", "still_not_a_tier"]


def test_empty_destinations_returns_empty_envelope(ent):
    out = ent.tier_spec_path_batch(ent.TIER_OSS, [])
    assert out == {"tiers": [], "unknown": []}
    assert ent.tier_spec_path_batch(ent.TIER_OSS, "") == {
        "tiers": [],
        "unknown": [],
    }
    assert ent.tier_spec_path_batch(ent.TIER_OSS, None) == {
        "tiers": [],
        "unknown": [],
    }


def test_none_or_unknown_from_tier_returns_none(ent):
    assert ent.tier_spec_path_batch("", [ent.TIER_CLOUD_PRO]) is None
    assert ent.tier_spec_path_batch(None, [ent.TIER_CLOUD_PRO]) is None
    assert ent.tier_spec_path_batch("  ", [ent.TIER_CLOUD_PRO]) is None
    assert (
        ent.tier_spec_path_batch("not_a_tier", [ent.TIER_CLOUD_PRO])
        is None
    )


def test_garbage_from_tier_never_raises(ent):
    assert ent.tier_spec_path_batch(123, [ent.TIER_CLOUD_PRO]) is None
    assert ent.tier_spec_path_batch([], [ent.TIER_CLOUD_PRO]) is None
    assert ent.tier_spec_path_batch({}, [ent.TIER_CLOUD_PRO]) is None


def test_trial_accepted_as_destination_via_lateral(ent):
    """cloud_pro and trial both at collapsed rank 2 -- trial resolves via
    the lateral branch as a single-row path."""
    out = ent.tier_spec_path_batch(ent.TIER_CLOUD_PRO, [ent.TIER_TRIAL])
    assert out["unknown"] == []
    row = out["tiers"][0]
    assert row["direction"] == "lateral"
    assert len(row["path"]) == 1
    assert row["path"][0]["id"] == ent.TIER_TRIAL


def test_trial_as_source_still_walks(ent):
    """trial IS a valid source -- the walker crosses into the rank above."""
    out = ent.tier_spec_path_batch(ent.TIER_TRIAL, [ent.TIER_ENTERPRISE])
    assert out["unknown"] == []
    row = out["tiers"][0]
    assert row["direction"] == "upgrade"
    assert row["path"][-1]["id"] == ent.TIER_ENTERPRISE


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    """trial is not purchasable -- it must never appear as an intermediate
    rung between two purchasable endpoints, in the batch response the
    same way it never appears in the scalar."""
    out = ent.tier_spec_path_batch(ent.TIER_OSS, [ent.TIER_ENTERPRISE])
    for rung in out["tiers"][0]["path"]:
        assert rung["id"] != ent.TIER_TRIAL


def test_grace_and_enforce_yield_identical_batch(ent, monkeypatch):
    """The helper is decoupled from the resolved entitlement -- flipping
    enforce on must NOT change any row. Pins the resolver-independence
    property the whole ``_path`` family shares."""
    tos = [
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    grace = ent.tier_spec_path_batch(ent.TIER_OSS, tos)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_spec_path_batch(ent.TIER_OSS, tos)
    assert grace == enforced


def test_per_destination_failure_bucketed_not_5xxd(ent, monkeypatch):
    """When the underlying scalar helper raises for a single destination,
    that id must short-circuit into ``unknown[]`` while the rest of the
    batch keeps building -- pins the never-raise batch posture."""
    real = ent.tier_spec_path

    def blow_up_on_pro(f, t):
        if t == ent.TIER_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_spec_path", blow_up_on_pro)
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, ent.TIER_PRO, ent.TIER_ENTERPRISE],
    )
    assert [row["to"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    assert ent.TIER_PRO in out["unknown"]


def test_per_destination_none_bucketed(ent, monkeypatch):
    """When the scalar helper returns ``None`` for a destination, that id
    is bucketed into ``unknown[]`` instead of appearing as a
    ``path: None`` row."""

    def none_on_pro(f, t):
        if t == ent.TIER_PRO:
            return None
        # Fall through to a real call.
        return ent.tier_spec_at(f, t) and [ent.tier_spec_at(f, t)]

    monkeypatch.setattr(ent, "tier_spec_path", none_on_pro)
    out = ent.tier_spec_path_batch(
        ent.TIER_OSS, [ent.TIER_CLOUD_PRO, ent.TIER_PRO]
    )
    assert ent.TIER_PRO in out["unknown"]
    tos = [row["to"] for row in out["tiers"]]
    assert ent.TIER_PRO not in tos


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get("/api/entitlement/tier-spec-path-batch")
    assert r.status_code == 400


def test_api_400_on_missing_to(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
    )
    assert r.status_code == 400
    r2 = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}&to="
    )
    assert r2.status_code == 400


def test_api_404_on_unknown_from(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from=not_a_tier"
        f"&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "not_a_tier"


def test_api_happy_path_envelope(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert isinstance(body["tiers"], list)
    assert len(body["tiers"]) == 3
    for row in body["tiers"]:
        assert set(row.keys()) == _ROW_KEYS
    assert body["unknown"] == []


def test_api_bucketed_unknowns_do_not_404(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_api_direction_branches_end_to_end(client, ent):
    """Each destination in a single request should carry the same
    direction the scalar ``/tier-spec-path`` endpoint returns for the
    same pair."""
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO},{ent.TIER_PRO},{ent.TIER_ENTERPRISE},{ent.TIER_OSS}"
    )
    assert r.status_code == 200
    by_to = {row["to"]: row["direction"] for row in r.get_json()["tiers"]}
    assert by_to[ent.TIER_CLOUD_PRO] == "identity"
    assert by_to[ent.TIER_PRO] == "lateral"
    assert by_to[ent.TIER_ENTERPRISE] == "upgrade"
    assert by_to[ent.TIER_OSS] == "downgrade"


def test_api_per_destination_path_byte_equals_scalar_route(client, ent):
    """The per-destination ``path`` in the batch response must be
    byte-identical to the scalar ``/tier-spec-path?from=&to=`` payload's
    ``path`` for the same pair."""
    f = ent.TIER_OSS
    tos = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    batch = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={f}"
        f"&to={','.join(tos)}"
    ).get_json()
    by_to = {row["to"]: row for row in batch["tiers"]}
    for tid in tos:
        scalar = client.get(
            f"/api/entitlement/tier-spec-path?from={f}&to={tid}"
        ).get_json()
        assert by_to[tid]["path"] == scalar["path"]
        assert by_to[tid]["direction"] == scalar["direction"]
        assert by_to[tid]["to_label"] == scalar["to_label"]
        assert by_to[tid]["to_rank"] == scalar["to_rank"]


def test_api_supply_order_preserved(client, ent):
    tos = [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]
    body = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={','.join(tos)}"
    ).get_json()
    assert [row["to"] for row in body["tiers"]] == tos


def test_api_grace_vs_enforce_body_parity(client, ent, monkeypatch):
    tos = [ent.TIER_CLOUD_PRO, ent.TIER_PRO, ent.TIER_ENTERPRISE]
    grace_body = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={','.join(tos)}"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_body = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_OSS}"
        f"&to={','.join(tos)}"
    ).get_json()
    assert grace_body == enforced_body


def test_api_trial_endpoints_accepted(client, ent):
    r = client.get(
        f"/api/entitlement/tier-spec-path-batch?from={ent.TIER_TRIAL}"
        f"&to={ent.TIER_ENTERPRISE},{ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["from"] == ent.TIER_TRIAL
    tos = [row["to"] for row in body["tiers"]]
    assert ent.TIER_ENTERPRISE in tos
    assert ent.TIER_CLOUD_PRO in tos
