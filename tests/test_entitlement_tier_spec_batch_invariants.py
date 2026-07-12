"""Invariants pinned on ``clawmetry.entitlements.tier_spec_batch`` and its
companion ``GET /api/entitlement/tier-spec-batch`` endpoint.

Follow-up to ``test_entitlement_tier_spec_batch.py`` in the same shape as
``test_entitlement_next_prev_tier_spec_at.py`` follows the initial
next/previous_tier_spec_at ship: the ship-tests pin shape / normalisation /
grace-vs-enforce / crash-safety on the helper and endpoint in isolation.
This file pins the CROSS-family / CROSS-axis invariants that would let
``tier_spec_batch`` silently drift away from its neighbours in the
``_at`` / catalogue / rank family without either file's coverage catching
it -- the class of drift that only shows up when a pricing-comparison UI
paints two accessors side by side and gets different numbers for the
same tier.

Pins covered here:

* **Batch row = tier_spec_at row from the resolved perspective.** The
  cross-batch parity contract: for the LIVE resolved tier ``t``,
  ``tier_spec_batch(ids)`` and ``tier_spec_at_batch(t, ids)`` must
  produce byte-identical row lists and unknown lists. That's the wire
  identity a matrix UI relies on when it swaps between "from my install"
  and "from my hypothetical" without cache invalidation.
* **Rank monotonicity.** For every batch row, the row's ``rank`` field
  IS the catalogue-position index into :data:`_TIER_ORDER` -- never the
  ladder rank from :data:`_TIER_RANK`. Passing the full ``_TIER_ORDER``
  in supply-order yields a strictly-increasing ``rank`` sequence
  ``0..len(_TIER_ORDER)-1``. Prevents a future refactor from silently
  swapping the two ranks (they overlap at OSS but diverge from
  cloud_starter upward).
* **Field-type invariants** across every row: ``features`` is a
  duplicate-free sorted list that is a subset of :data:`ALL_FEATURES`;
  ``runtimes`` is a duplicate-free sorted list; every ``runtimes`` list
  is either the exact sorted :data:`PAID_RUNTIMES` (unlocks paid) or
  empty (doesn't). ``retention_days`` / ``channel_limit`` /
  ``node_limit`` are either ``None`` or a positive int -- never ``0``,
  never a negative sentinel.
* **Catalogue-map agreement.** ``is_paid`` iff id in :data:`_PAID_TIERS`;
  ``unlocks_paid_runtimes`` iff id in :data:`_TIER_PAID_RUNTIMES`;
  ``retention_days`` matches :data:`_TIER_RETENTION_DAYS`;
  ``channel_limit`` matches :data:`_TIER_CHANNEL_LIMIT`; ``node_limit``
  matches :data:`_TIER_NODE_LIMIT`; ``features`` matches
  ``sorted(_TIER_FEATURES[id])``. These are the six catalogue maps the
  batch reads off in one pass -- one wrong lookup and the pricing card
  quotes the wrong price.
* **Row key exactness.** Every row's key set is EXACTLY
  :data:`_SPEC_KEYS` -- no missing keys (would render a blank cell) and
  no extras (would leak an unversioned field the frontend has never
  seen).
* **Idempotency.** Calling the batch N times with the same input under
  the same resolver state yields byte-identical bodies; the endpoint
  ditto on the wire. Rules out a hidden dict-order / floating cache
  regression.
* **Endpoint HTTP contract.** ``Content-Type`` is ``application/json``;
  ``POST`` (and other non-GET methods) returns 405 (never a body that
  looks like a 200 with an empty envelope, which would silently mask a
  broken caller); an unknown-only 200 preserves the source-order
  ``unknown[]``.
* **Envelope agreement with the live resolver.** The envelope's
  ``grace`` / ``enforced`` / ``current_tier`` / ``current_tier_rank``
  fields agree with ``get_entitlement()`` / ``is_enforced()`` /
  ``tier_rank()`` at the moment of the call. Rules out a stale-snapshot
  regression where the batch reads a fresh resolver but the envelope
  ships yesterday's values.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_SPEC_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
    "features",
    "runtimes",
}

_ENVELOPE_KEYS = {"tiers", "unknown", "current_tier", "current_tier_rank",
                  "grace", "enforced"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` / ``cloud_plan.json`` leaks in. Grace
    mode by default -- the invariants below are catalogue-derived and
    resolver-independent for every field except ``is_current``, so the
    fixture only needs to hold the live resolver stable across the test."""
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


# ── row-key exactness ─────────────────────────────────────────────────────────


def test_every_row_has_exact_spec_key_set(ent):
    """Row keys are EXACTLY :data:`_SPEC_KEYS` for every tier -- neither a
    missing key (blank cell) nor an extra unversioned key (frontend never
    saw it) is allowed to slip in."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert set(row.keys()) == _SPEC_KEYS, row["id"]


# ── rank invariants ──────────────────────────────────────────────────────────


def test_rank_is_catalogue_position_not_ladder_rank(ent):
    """``row["rank"]`` is the position in :data:`_TIER_ORDER`, NOT the
    ladder rank from :data:`_TIER_RANK` (they diverge from cloud_starter
    upward). Pin so a refactor cannot silently merge the two ranks."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["rank"] == ent._TIER_ORDER.index(row["id"]), row["id"]


def test_rank_sequence_strictly_increasing_in_order_supply(ent):
    """Feeding the batch ``_TIER_ORDER`` in order yields a strictly
    increasing ``rank`` sequence 0..N-1 -- the invariant a pricing table
    that renders rows top-down implicitly relies on."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    ranks = [row["rank"] for row in body["tiers"]]
    assert ranks == list(range(len(ent._TIER_ORDER)))


# ── field-type invariants ────────────────────────────────────────────────────


def test_features_list_is_sorted_and_duplicate_free(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        feats = row["features"]
        assert feats == sorted(feats), row["id"]
        assert len(feats) == len(set(feats)), row["id"]


def test_features_are_subset_of_all_features(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert set(row["features"]) <= ent.ALL_FEATURES, row["id"]


def test_runtimes_list_is_sorted_and_duplicate_free(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        runs = row["runtimes"]
        assert runs == sorted(runs), row["id"]
        assert len(runs) == len(set(runs)), row["id"]


def test_runtimes_is_empty_or_full_paid_runtimes(ent):
    """``runtimes`` is either the full sorted :data:`PAID_RUNTIMES` list
    (tier unlocks paid) or empty (doesn't). There is no per-tier subset
    of paid runtimes today -- pin so the batch never accidentally starts
    inventing one."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    full = sorted(ent.PAID_RUNTIMES)
    for row in body["tiers"]:
        if row["unlocks_paid_runtimes"]:
            assert row["runtimes"] == full, row["id"]
        else:
            assert row["runtimes"] == [], row["id"]


def test_capacity_fields_are_none_or_positive_int(ent):
    """``retention_days`` / ``channel_limit`` / ``node_limit`` are either
    ``None`` (unlimited sentinel) or a positive int. ``0`` / negative
    would be a silent regression the frontend renders as "no retention",
    "no channels", "no nodes"."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        for key in ("retention_days", "channel_limit", "node_limit"):
            val = row[key]
            assert val is None or (
                isinstance(val, int) and not isinstance(val, bool) and val > 0
            ), (row["id"], key, val)


# ── catalogue-map agreement ──────────────────────────────────────────────────


def test_is_paid_matches_paid_tiers_set(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["is_paid"] is (row["id"] in ent._PAID_TIERS), row["id"]


def test_unlocks_paid_runtimes_matches_tier_paid_runtimes_map(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["unlocks_paid_runtimes"] is (
            row["id"] in ent._TIER_PAID_RUNTIMES
        ), row["id"]


def test_retention_days_matches_map(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["retention_days"] == ent._TIER_RETENTION_DAYS.get(
            row["id"], 7
        ), row["id"]


def test_channel_limit_matches_map(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["channel_limit"] == ent._TIER_CHANNEL_LIMIT.get(
            row["id"], ent._FREE_CHANNEL_LIMIT
        ), row["id"]


def test_node_limit_matches_map(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["node_limit"] == ent._TIER_NODE_LIMIT.get(
            row["id"], ent._FREE_NODE_LIMIT
        ), row["id"]


def test_features_match_tier_features_map_sorted(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["features"] == sorted(
            ent._TIER_FEATURES.get(row["id"], frozenset())
        ), row["id"]


def test_label_matches_tier_label(ent):
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["label"] == ent.tier_label(row["id"]), row["id"]


# ── cross-family: batch vs tier_spec_at_batch(current, ids) ──────────────────


def test_batch_equals_tier_spec_at_batch_of_resolved_tier(ent):
    """From the resolver's perspective, ``tier_spec_batch(ids)`` and
    ``tier_spec_at_batch(current_tier, ids)`` must produce byte-identical
    row + unknown lists. That's the wire-identity a matrix UI relies on
    when it swaps between "from my install" and "from my hypothetical"
    without cache invalidation."""
    ids = list(ent._TIER_ORDER) + ["nope_xyz"]
    resolved = ent.get_entitlement().tier
    live = ent.tier_spec_batch(ids)
    whatif = ent.tier_spec_at_batch(resolved, ids)
    assert whatif is not None
    assert live["unknown"] == whatif["unknown"]
    assert live["tiers"] == whatif["tiers"]


# ── idempotency ──────────────────────────────────────────────────────────────


def test_batch_is_idempotent(ent):
    """Under stable resolver state, N repeated calls yield byte-identical
    bodies -- no hidden dict-order / floating cache regression."""
    ids = list(ent._TIER_ORDER)
    first = ent.tier_spec_batch(ids)
    for _ in range(10):
        assert ent.tier_spec_batch(ids) == first


def test_endpoint_is_idempotent_on_wire(client, ent):
    ids = ",".join(ent._TIER_ORDER)
    first = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ids}"
    ).get_data(as_text=True)
    for _ in range(10):
        again = client.get(
            f"/api/entitlement/tier-spec-batch?tiers={ids}"
        ).get_data(as_text=True)
        assert again == first


# ── endpoint HTTP contract ───────────────────────────────────────────────────


def test_endpoint_content_type_is_application_json(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    # Flask's ``jsonify`` sets ``application/json`` (Werkzeug's Content-Type
    # includes the charset; only the mimetype is contract).
    assert resp.mimetype == "application/json"


def test_endpoint_post_returns_405(client, ent):
    """The endpoint is GET-only -- a POST must 405, never a body that
    looks like a 200 with an empty envelope (which would silently mask a
    broken caller retrying with the wrong verb)."""
    resp = client.post(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    assert resp.status_code == 405


def test_endpoint_put_returns_405(client, ent):
    resp = client.put(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    assert resp.status_code == 405


def test_endpoint_unknown_only_preserves_source_order_unknown(client):
    resp = client.get(
        "/api/entitlement/tier-spec-batch?tiers=zzz,aaa,mmm"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["zzz", "aaa", "mmm"]


def test_endpoint_envelope_key_set_exact(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


# ── envelope agrees with live resolver ───────────────────────────────────────


def test_endpoint_envelope_grace_matches_resolver(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    body = resp.get_json()
    assert body["grace"] is bool(ent.get_entitlement().grace)
    assert body["enforced"] is ent.is_enforced()


def test_endpoint_envelope_current_tier_rank_matches_helper(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_OSS}"
    )
    body = resp.get_json()
    resolved = ent.get_entitlement().tier
    assert body["current_tier"] == resolved
    assert body["current_tier_rank"] == ent.tier_rank(resolved)


# ── JSON round-trip stability ────────────────────────────────────────────────


def test_batch_body_is_json_round_trip_stable(ent):
    """The Python body must survive ``json.dumps`` -> ``json.loads`` unchanged
    -- no non-JSON-safe sentinel (frozenset / tuple / ``None`` in a spot
    the spec calls out as a bool) can slip through."""
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    round_tripped = json.loads(json.dumps(body))
    assert round_tripped == body


# ── unknown-list source-order preservation ───────────────────────────────────


def test_unknown_list_preserves_supply_order(ent):
    body = ent.tier_spec_batch(["zzz", ent.TIER_OSS, "aaa", "mmm"])
    assert [r["id"] for r in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["zzz", "aaa", "mmm"]


def test_unknown_list_is_normalised_ids_not_raw(ent):
    """The unknown[] list echoes the normalised form (trimmed +
    lowercased), not the raw supplied variant. Otherwise a caller could
    see two entries in ``unknown`` for what is really one bogus id."""
    body = ent.tier_spec_batch(["  ZZZ  ", "zzz"])
    assert body["tiers"] == []
    # Duplicates collapse after normalisation -- the second "zzz" drops.
    assert body["unknown"] == ["zzz"]
