"""Tests for ``clawmetry.entitlements.channel_catalog_at_path_batch(
perspective, from, to_tiers)`` + its HTTP endpoint
``GET /api/entitlement/channel-catalog-at-path-batch``.

Batch what-if sibling of :func:`channel_catalog_at_path`: walks
per-rung channel-catalog rows from ONE ``from_tier`` to N candidate
destinations from a hypothetical ``perspective_tier`` in ONE round-
trip. Fills the ``_at_path_batch`` slot for the channel-catalog
family alongside :func:`channel_catalog_at` /
:func:`channel_catalog_at_batch` / :func:`channel_catalog_at_path`
-- last remaining ``_at*`` cell on the channel-catalog axis, twin
of :func:`feature_catalog_at_path_batch` and
:func:`runtime_catalog_at_path_batch` on the feature / runtime axes.

Pins:

* body byte-identical to :func:`channel_catalog_path_batch` for
  every perspective -- the perspective is validated but does NOT
  shape the rows (parity with every other ``_at_path_batch`` helper
  the ``feature_catalog_at_path_batch`` /
  ``runtime_catalog_at_path_batch`` family ships).
* per-rung row shape carries the same 4 keys as
  :func:`channel_catalog_path` (``tier``, ``tier_label``,
  ``tier_rank``, ``channels``); each inner ``channels`` list byte-
  equals :func:`channel_catalog()` -- the "channels are always free
  at every tier" invariant is inherited from the delegate and pinned
  here so the ``_at_path_batch`` surface cannot drift from the
  scalar what-if or the current-perspective batch.
* per-destination ``direction`` derived from the same ranks the
  scalar endpoint uses (identity / lateral / upgrade / downgrade).
* ``trial`` accepted as perspective and as destination (matching
  every other ``_at`` sibling's lenient posture, unlike
  :func:`channel_catalog_path_batch` which excludes trial from the
  walked intermediate rungs but accepts it as an endpoint via the
  lateral / identity branches).
* case + whitespace normalisation on perspective, from, destinations.
* helper is decoupled from the resolver -- grace vs enforce yields
  byte-identical rows.
* unknown / empty / garbage ids return ``None`` and never raise;
  a delegate crash short-circuits to ``None`` and logs a warning.
* per-destination row failure short-circuits that id into
  ``unknown[]`` while the rest of the batch keeps building.
* API: 400 on missing / empty args, 404 with ``which: "tier" |
  "from"`` on unknown source ids, 200 with bucketed unknowns for
  unknown destinations, standard resolver-context tail every
  ``_at*`` endpoint carries.
"""
from __future__ import annotations

import importlib

import pytest


_INNER_ROW_KEYS = {"tier", "tier_label", "tier_rank", "channels"}
_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}
_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
    "current_tier",
    "current_tier_rank",
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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


def _all_tiers(mod):
    return [
        mod.TIER_OSS,
        mod.TIER_CLOUD_FREE,
        mod.TIER_TRIAL,
        mod.TIER_CLOUD_STARTER,
        mod.TIER_CLOUD_PRO,
        mod.TIER_PRO,
        mod.TIER_ENTERPRISE,
    ]


# ── helper: shape + happy path ────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_full_envelope(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
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
    :func:`channel_catalog_path` -- the ``_at_path_batch`` family stays
    in lock-step with the scalar ``_path`` family."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    assert item["path"]
    for row in item["path"]:
        assert set(row.keys()) == _INNER_ROW_KEYS
        assert isinstance(row["channels"], list)
        assert row["channels"]  # never empty


# ── helper: parity with channel_catalog_path_batch (byte-identical) ──────


def test_helper_body_parity_with_channel_catalog_path_batch(ent):
    """Body byte-identical to
    :func:`channel_catalog_path_batch(from, to_tiers)` for every
    ``(perspective, from, to_tiers)`` triple in
    ``ALL_TIERS × ALL_TIERS × ALL_TIERS`` -- the perspective is
    validated but does NOT shape rows."""
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            got = ent.channel_catalog_at_path_batch(p, f, tiers)
            want = ent.channel_catalog_path_batch(f, tiers)
            assert got == want, (p, f)


def test_helper_perspective_invariance(ent):
    """Two different perspectives yield byte-identical envelopes."""
    tiers = _all_tiers(ent)
    for f in tiers:
        a = ent.channel_catalog_at_path_batch(ent.TIER_OSS, f, tiers)
        b = ent.channel_catalog_at_path_batch(
            ent.TIER_ENTERPRISE, f, tiers
        )
        assert a == b, f


def test_helper_per_item_path_byte_equal_to_scalar_at_path(ent):
    """Per-destination ``path`` is byte-identical to the scalar
    :func:`channel_catalog_at_path` payload for the same
    ``(perspective, from, to)`` triple. If a future refactor teaches
    the batch helper to skip a rung or a per-channel column, this test
    fails."""
    candidates = [
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, candidates
    )
    by_id = {item["to"]: item["path"] for item in out["tiers"]}
    for tid in candidates:
        scalar = ent.channel_catalog_at_path(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, tid
        )
        assert by_id[tid] == scalar


def test_helper_per_rung_channels_byte_equal_to_channel_catalog(ent):
    """Each per-rung ``channels`` list byte-equals
    :func:`channel_catalog()` (the "channels are always free at every
    tier" invariant, inherited from :func:`channel_catalog_path`)."""
    baseline = ent.channel_catalog()
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    for row in item["path"]:
        assert row["channels"] == baseline


def test_helper_channel_list_invariant_across_all_walks(ent):
    """Every rung across every walk carries the same channels list."""
    baseline = ent.channel_catalog()
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            out = ent.channel_catalog_at_path_batch(p, f, tiers)
            if out is None:
                continue
            for item in out["tiers"]:
                for row in item["path"]:
                    assert row["channels"] == baseline


def test_helper_per_row_free_posture_preserved(ent):
    """Every row reported by this batch helper must surface
    ``free=True`` / ``allowed=True`` / ``locked=False`` /
    ``entitled=True``."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
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
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER, candidates
    )
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


def test_helper_per_item_to_label_matches_helper_pin(ent):
    """Per-destination ``to_label`` / ``to_rank`` byte-equal the
    :func:`tier_label` / :func:`tier_rank` helpers."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, candidates
    )
    for item in out["tiers"]:
        assert item["to_label"] == ent.tier_label(item["to"])
        assert item["to_rank"] == ent.tier_rank(item["to"])


# ── helper: input normalisation ──────────────────────────────────────────


def test_helper_supply_order_preserved(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER],
    )
    assert [item["to"] for item in out["tiers"]] == [
        ent.TIER_ENTERPRISE,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_STARTER,
    ]


def test_helper_normalises_destinations(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
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


def test_helper_perspective_and_from_normalised(ent):
    """Perspective + from also normalised (whitespace + case)."""
    a = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    b = ent.channel_catalog_at_path_batch(
        "  Cloud_Pro  ", "  OSS  ", [ent.TIER_ENTERPRISE]
    )
    assert a == b


def test_helper_unknown_destination_ids_echoed(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, "bogus_tier", "still_bogus"],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert set(out["unknown"]) == {"bogus_tier", "still_bogus"}


# ── helper: direction branches ───────────────────────────────────────────


def test_helper_identity_yields_empty_path(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE],
    )
    by_id = {item["to"]: item for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO]["direction"] == "identity"
    assert by_id[ent.TIER_CLOUD_PRO]["path"] == []
    assert by_id[ent.TIER_ENTERPRISE]["direction"] == "upgrade"


def test_helper_lateral_yields_one_row_path(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, [ent.TIER_PRO]
    )
    assert len(out["tiers"]) == 1
    item = out["tiers"][0]
    assert item["direction"] == "lateral"
    assert len(item["path"]) == 1
    assert item["path"][0]["tier"] == ent.TIER_PRO


def test_helper_upgrade_walks_intermediate_rungs(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    item = out["tiers"][0]
    assert item["direction"] == "upgrade"
    rungs = [row["tier"] for row in item["path"]]
    assert rungs[-1] == ent.TIER_ENTERPRISE
    assert ent.TIER_OSS not in rungs


def test_helper_downgrade_walks_descending(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    )
    item = out["tiers"][0]
    assert item["direction"] == "downgrade"
    rungs = [row["tier"] for row in item["path"]]
    ranks = [ent.tier_rank(r) for r in rungs]
    assert ranks == sorted(ranks, reverse=True)


def test_helper_all_four_branches_in_one_batch(ent):
    """Single call covers identity + lateral + upgrade + downgrade."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        [
            ent.TIER_CLOUD_PRO,   # identity
            ent.TIER_PRO,          # lateral
            ent.TIER_ENTERPRISE,   # upgrade
            ent.TIER_OSS,          # downgrade
        ],
    )
    by_id = {item["to"]: item["direction"] for item in out["tiers"]}
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "upgrade"
    assert by_id[ent.TIER_OSS] == "downgrade"


# ── helper: trial + endpoint acceptance ──────────────────────────────────


def test_helper_trial_accepted_as_perspective(ent):
    """Perspective acceptance is lenient: trial IS accepted."""
    got = ent.channel_catalog_at_path_batch(
        ent.TIER_TRIAL, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    assert got is not None
    assert got == ent.channel_catalog_path_batch(
        ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )


def test_helper_trial_destination_accepted(ent):
    """``trial`` is a valid endpoint (matching
    :func:`channel_catalog_path_batch` semantics) even though it is
    excluded from the walked intermediate rungs."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_TRIAL]
    )
    assert out["unknown"] == []
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_TRIAL]


def test_helper_trial_source_accepted(ent):
    """``trial`` is a valid source (matching
    :func:`channel_catalog_path_batch` semantics)."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, [ent.TIER_ENTERPRISE]
    )
    assert out is not None
    assert out["unknown"] == []
    (item,) = out["tiers"]
    assert item["path"][-1]["tier"] == ent.TIER_ENTERPRISE


def test_helper_trial_never_appears_as_intermediate_rung(ent):
    """``trial`` is not purchasable -- it must never appear as a stop
    on a path between purchasable tiers."""
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    (item,) = out["tiers"]
    rungs = [row["tier"] for row in item["path"]]
    assert ent.TIER_TRIAL not in rungs


# ── helper: unknown / robustness ─────────────────────────────────────────


def test_helper_unknown_perspective_returns_none(ent):
    assert (
        ent.channel_catalog_at_path_batch(
            "bogus", ent.TIER_OSS, [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_helper_unknown_from_returns_none(ent):
    assert (
        ent.channel_catalog_at_path_batch(
            ent.TIER_CLOUD_PRO, "bogus", [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_helper_none_perspective_returns_none(ent):
    assert (
        ent.channel_catalog_at_path_batch(
            None, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_helper_empty_perspective_returns_none(ent):
    assert (
        ent.channel_catalog_at_path_batch(
            "", ent.TIER_OSS, [ent.TIER_ENTERPRISE]
        )
        is None
    )
    assert (
        ent.channel_catalog_at_path_batch(
            "   ", ent.TIER_OSS, [ent.TIER_ENTERPRISE]
        )
        is None
    )


def test_helper_empty_destinations_yields_empty_envelope(ent):
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, []
    )
    assert out == {"tiers": [], "unknown": []}


def test_helper_never_raises_on_weird_types(ent):
    """Garbage inputs return None, never raise."""
    for bad_p in (123, 4.5, [], {}, object()):
        assert (
            ent.channel_catalog_at_path_batch(
                bad_p, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
            )
            is None
        )


def test_helper_grace_vs_enforce_identical(ent, enforced):
    """Grace vs enforce yields byte-identical rows."""
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            a = ent.channel_catalog_at_path_batch(p, f, tiers)
            b = enforced.channel_catalog_at_path_batch(p, f, tiers)
            assert a == b, (p, f)


def test_helper_delegate_crash_returns_none(ent, monkeypatch):
    """A top-level crash inside :func:`channel_catalog_path_batch`
    short-circuits to ``None`` instead of propagating."""

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "channel_catalog_path_batch", _boom)
    got = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    )
    assert got is None


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-destination failure inside the delegate chain pushes that
    id into ``unknown[]`` while the rest of the batch keeps building
    (inherited from :func:`channel_catalog_path_batch`)."""
    real = ent.channel_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "channel_catalog_path", fake)
    out = ent.channel_catalog_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE],
    )
    assert [item["to"] for item in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in out["unknown"]


# ── HTTP: /api/entitlement/channel-catalog-at-path-batch ─────────────────


def test_http_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    tos = [item["to"] for item in body["tiers"]]
    assert tos == [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    for item in body["tiers"]:
        assert item["direction"] == "upgrade"
        assert item["path"][-1]["tier"] == item["to"]
        for row in item["path"]:
            assert set(row.keys()) == _INNER_ROW_KEYS


def test_http_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_missing_from_400(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_missing_to_400(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply to=<csv>"


def test_http_empty_to_400(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=cloud_pro&from=oss&to=,,"
    )
    assert r.status_code == 400


def test_http_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "from"
    assert body["from"] == "bogus"


def test_http_200_with_unknown_destination_bucketed(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_PRO},bogus_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_CLOUD_PRO]
    assert body["unknown"] == ["bogus_tier"]


def test_http_trial_accepted_as_perspective(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_TRIAL}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL


def test_http_trial_destination_accepted(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_TRIAL}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["unknown"] == []
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_TRIAL]


def test_http_identity_branch(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "identity"
    assert body["tiers"][0]["path"] == []


def test_http_lateral_branch(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_STARTER}&from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "lateral"
    assert len(body["tiers"][0]["path"]) == 1
    assert body["tiers"][0]["path"][0]["tier"] == ent.TIER_PRO


def test_http_downgrade_branch(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"][0]["direction"] == "downgrade"


def test_http_per_item_path_matches_scalar_route(client, ent):
    """HTTP parity: each per-destination ``path`` is byte-identical to
    the scalar ``/channel-catalog-at-path?tier=&from=&to=`` ``path``
    payload for the same ``(perspective, from, to)`` triple."""
    candidates = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]
    batch = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={','.join(candidates)}"
    ).get_json()
    for item in batch["tiers"]:
        scalar = client.get(
            "/api/entitlement/channel-catalog-at-path"
            f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
            f"&to={item['to']}"
        ).get_json()
        assert item["path"] == scalar["path"]
        assert item["direction"] == scalar["direction"]
        assert item["to_label"] == scalar["to_label"]
        assert item["to_rank"] == scalar["to_rank"]


def test_http_per_item_path_matches_bare_path_batch_route(client, ent):
    """HTTP parity vs the current-perspective batch route: per-item
    ``path`` byte-equals ``/channel-catalog-path-batch?from=&to=`` for
    the same ``(from, to_tiers)`` pair."""
    candidates = [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE]
    r_at = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={','.join(candidates)}"
    ).get_json()
    r_bare = client.get(
        "/api/entitlement/channel-catalog-path-batch"
        f"?from={ent.TIER_OSS}&to={','.join(candidates)}"
    ).get_json()
    at_paths = [item["path"] for item in r_at["tiers"]]
    bare_paths = [item["path"] for item in r_bare["tiers"]]
    assert at_paths == bare_paths


def test_http_input_normalised(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20"
        "&to=  CLOUD_PRO  ,cloud_starter,cloud_pro,"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    assert [item["to"] for item in body["tiers"]] == [
        "cloud_pro",
        "cloud_starter",
    ]


def test_http_perspective_invariance(client, ent):
    """Wire body's per-item ``path`` is byte-identical across two
    perspectives."""
    r_a = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_OSS}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    r_b = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_ENTERPRISE}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    a_paths = [item["path"] for item in r_a["tiers"]]
    b_paths = [item["path"] for item in r_b["tiers"]]
    assert a_paths == b_paths


def test_http_channel_list_invariant_across_rungs(client, ent):
    """Every rung's ``channels`` list is byte-equal to
    ``/channel-catalog`` (the "channels are always free" invariant
    inherited from the delegate)."""
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    r_bare = client.get("/api/entitlement/channel-catalog")
    assert r.status_code == 200
    assert r_bare.status_code == 200
    baseline = r_bare.get_json()["channels"]
    for item in r.get_json()["tiers"]:
        for row in item["path"]:
            assert row["channels"] == baseline


def test_http_carries_resolver_context_tail(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_http_never_5xxs_on_row_failure(client, ent, monkeypatch):
    """A per-destination synthesis crash short-circuits to ``unknown[]``
    -- the endpoint still returns 200 with a rendered envelope."""
    real = ent.channel_catalog_path

    def fake(f, t):
        if t == ent.TIER_CLOUD_PRO:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "channel_catalog_path", fake)
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["to"] for item in body["tiers"]] == [ent.TIER_ENTERPRISE]
    assert ent.TIER_CLOUD_PRO in body["unknown"]


def test_http_never_5xx_on_delegate_crash(client, ent, monkeypatch):
    """A crash inside the helper short-circuits to an empty envelope,
    not 5xx."""

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "channel_catalog_at_path_batch", _boom)
    r = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []


def test_http_grace_vs_enforce_identical(client, ent, enforced):
    """Wire body's per-item ``path`` is byte-identical across grace /
    enforce."""
    r_a = client.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    )
    assert r_a.status_code == 200

    from flask import Flask

    from routes.entitlement import bp_entitlement

    app_e = Flask(__name__)
    app_e.register_blueprint(bp_entitlement)
    client_e = app_e.test_client()
    r_b = client_e.get(
        "/api/entitlement/channel-catalog-at-path-batch"
        f"?tier={enforced.TIER_CLOUD_PRO}&from={enforced.TIER_OSS}"
        f"&to={enforced.TIER_CLOUD_STARTER},{enforced.TIER_ENTERPRISE}"
    )
    assert r_b.status_code == 200
    a_paths = [item["path"] for item in r_a.get_json()["tiers"]]
    b_paths = [item["path"] for item in r_b.get_json()["tiers"]]
    assert a_paths == b_paths
