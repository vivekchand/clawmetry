"""Invariants pinned on ``clawmetry.entitlements.tier_spec_at_batch`` and
its companion ``GET /api/entitlement/tier-spec-at-batch`` endpoint.

Follow-up to ``test_entitlement_tier_spec_at_batch.py`` in the same shape
as ``test_entitlement_tier_spec_batch_invariants.py`` follows the
initial ``tier_spec_batch`` ship: the ship-tests pin shape /
normalisation / grace-vs-enforce / crash-safety on the helper and
endpoint in isolation. This file pins the CROSS-family / CROSS-axis
invariants that would let ``tier_spec_at_batch`` silently drift away
from its neighbours in the resolved-batch / scalar / catalogue / rank
family without either file's coverage catching it -- the class of
drift that only shows up when a pricing-comparison matrix UI paints
two accessors side by side (its "from my install" and "from my
hypothetical" columns) and gets different numbers for the same target
tier.

Pins covered here:

* **Batch row (at current) = tier_spec_batch row.** The cross-batch
  parity contract from the OTHER direction: for the LIVE resolved tier
  ``t``, ``tier_spec_at_batch(t, ids)`` and ``tier_spec_batch(ids)``
  must produce byte-identical row + unknown lists. That's the same
  wire-identity contract the ``tier_spec_batch`` invariants file pins,
  but written from the ``_at_batch`` side so a regression in either
  direction is caught by both files.
* **Perspective-independence of non-``is_current`` fields.** For every
  target tier T and every perspective tier P, the row for T in
  ``tier_spec_at_batch(P, [T])`` has byte-identical NON-``is_current``
  fields regardless of P. Only ``is_current`` moves with the
  perspective. This is the matrix-UI contract: swapping which column
  the user thinks of as "current" cannot change any of the price /
  retention / capacity numbers on any other row.
* **``is_current`` is exclusively perspective-anchored.** For every
  (P, T) pair, ``row["is_current"] is (T == P)``. Prevents a refactor
  from smuggling the resolved tier into the ``is_current`` computation
  (which would make the surface leak the caller's install to a UI that
  wants a purely hypothetical view).
* **Rank monotonicity.** For every batch row, the row's ``rank`` field
  IS the catalogue-position index into :data:`_TIER_ORDER` -- never the
  ladder rank from :data:`_TIER_RANK`. Passing the full ``_TIER_ORDER``
  in supply-order yields a strictly-increasing ``rank`` sequence
  ``0..len(_TIER_ORDER)-1``. Pins from the ``_at_batch`` side that a
  refactor cannot silently swap the two ranks (they overlap at OSS but
  diverge from cloud_starter upward).
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
  ``sorted(_TIER_FEATURES[id])``. Six catalogue maps the batch reads
  off in one pass -- one wrong lookup and the pricing card quotes the
  wrong price on the wrong perspective column.
* **Row key exactness.** Every row's key set is EXACTLY
  :data:`_SPEC_KEYS` -- no missing keys (would render a blank cell) and
  no extras (would leak an unversioned field the frontend has never
  seen).
* **Idempotency.** Calling the batch N times with the same input under
  the same resolver state yields byte-identical bodies; the endpoint
  ditto on the wire. Rules out a hidden dict-order / floating cache
  regression.
* **Endpoint HTTP contract.** ``Content-Type`` is ``application/json``;
  ``POST`` (and other non-GET methods) return 405 (never a body that
  looks like a 200 with an empty envelope, which would silently mask a
  broken caller); an unknown-only 200 preserves the source-order
  ``unknown[]``.
* **Envelope key set exactness.** The envelope's key set is EXACTLY
  ``{tiers, unknown, perspective_tier, perspective_tier_rank,
  current_tier, current_tier_rank, grace, enforced}`` -- no missing
  key (blank field a UI reads as ``None``) and no extras (unversioned
  field the frontend has never seen).
* **Envelope agreement with the live resolver.** The envelope's
  ``grace`` / ``enforced`` / ``current_tier`` / ``current_tier_rank``
  fields agree with ``get_entitlement()`` / ``is_enforced()`` /
  ``tier_rank()`` at the moment of the call. Rules out a stale-snapshot
  regression where the batch reads a fresh resolver but the envelope
  ships yesterday's values.
* **Envelope perspective echo.** The envelope's ``perspective_tier``
  is the caller-supplied, normalised perspective; ``perspective_tier_rank``
  agrees with ``tier_rank(perspective_tier)``. A UI relying on the
  echo to label its columns cannot be fed a mismatched pair.
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

_ENVELOPE_KEYS = {
    "tiers",
    "unknown",
    "perspective_tier",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    no real ``~/.clawmetry/license.key`` / ``cloud_plan.json`` leaks in.
    Grace mode by default -- the invariants below are catalogue-derived
    and resolver-independent for every field except ``is_current``
    (which is perspective-, not resolver-, driven), so the fixture only
    needs to hold the live resolver stable across the test."""
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
    """Row keys are EXACTLY :data:`_SPEC_KEYS` for every (perspective,
    target) pair -- neither a missing key (blank cell) nor an extra
    unversioned key (frontend never saw it) is allowed to slip in."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None, perspective
        for row in body["tiers"]:
            assert set(row.keys()) == _SPEC_KEYS, (perspective, row["id"])


# ── rank invariants ──────────────────────────────────────────────────────────


def test_rank_is_catalogue_position_not_ladder_rank(ent):
    """``row["rank"]`` is the position in :data:`_TIER_ORDER`, NOT the
    ladder rank from :data:`_TIER_RANK` (they diverge from cloud_starter
    upward). Pin so a refactor cannot silently merge the two ranks."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["rank"] == ent._TIER_ORDER.index(row["id"]), (
                perspective,
                row["id"],
            )


def test_rank_sequence_strictly_increasing_in_order_supply(ent):
    """Feeding the batch ``_TIER_ORDER`` in order yields a strictly
    increasing ``rank`` sequence 0..N-1 for every perspective -- the
    invariant a pricing table that renders rows top-down implicitly
    relies on."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        ranks = [row["rank"] for row in body["tiers"]]
        assert ranks == list(range(len(ent._TIER_ORDER))), perspective


# ── field-type invariants ────────────────────────────────────────────────────


def test_features_list_is_sorted_and_duplicate_free(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            feats = row["features"]
            assert feats == sorted(feats), (perspective, row["id"])
            assert len(feats) == len(set(feats)), (perspective, row["id"])


def test_features_are_subset_of_all_features(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert set(row["features"]) <= ent.ALL_FEATURES, (
                perspective,
                row["id"],
            )


def test_runtimes_list_is_sorted_and_duplicate_free(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            runs = row["runtimes"]
            assert runs == sorted(runs), (perspective, row["id"])
            assert len(runs) == len(set(runs)), (perspective, row["id"])


def test_runtimes_is_empty_or_full_paid_runtimes(ent):
    """``runtimes`` is either the full sorted :data:`PAID_RUNTIMES` list
    (tier unlocks paid) or empty (doesn't). There is no per-tier subset
    of paid runtimes today -- pin so the batch never accidentally starts
    inventing one under any perspective."""
    full = sorted(ent.PAID_RUNTIMES)
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            if row["unlocks_paid_runtimes"]:
                assert row["runtimes"] == full, (perspective, row["id"])
            else:
                assert row["runtimes"] == [], (perspective, row["id"])


def test_capacity_fields_are_none_or_positive_int(ent):
    """``retention_days`` / ``channel_limit`` / ``node_limit`` are either
    ``None`` (unlimited sentinel) or a positive int. ``0`` / negative
    would be a silent regression the frontend renders as "no retention",
    "no channels", "no nodes"."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            for key in ("retention_days", "channel_limit", "node_limit"):
                val = row[key]
                assert val is None or (
                    isinstance(val, int)
                    and not isinstance(val, bool)
                    and val > 0
                ), (perspective, row["id"], key, val)


# ── catalogue-map agreement ──────────────────────────────────────────────────


def test_is_paid_matches_paid_tiers_set(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["is_paid"] is (row["id"] in ent._PAID_TIERS), (
                perspective,
                row["id"],
            )


def test_unlocks_paid_runtimes_matches_tier_paid_runtimes_map(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["unlocks_paid_runtimes"] is (
                row["id"] in ent._TIER_PAID_RUNTIMES
            ), (perspective, row["id"])


def test_retention_days_matches_map(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["retention_days"] == ent._TIER_RETENTION_DAYS.get(
                row["id"], 7
            ), (perspective, row["id"])


def test_channel_limit_matches_map(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["channel_limit"] == ent._TIER_CHANNEL_LIMIT.get(
                row["id"], ent._FREE_CHANNEL_LIMIT
            ), (perspective, row["id"])


def test_node_limit_matches_map(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["node_limit"] == ent._TIER_NODE_LIMIT.get(
                row["id"], ent._FREE_NODE_LIMIT
            ), (perspective, row["id"])


def test_features_match_tier_features_map_sorted(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["features"] == sorted(
                ent._TIER_FEATURES.get(row["id"], frozenset())
            ), (perspective, row["id"])


def test_label_matches_tier_label(ent):
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["label"] == ent.tier_label(row["id"]), (
                perspective,
                row["id"],
            )


# ── perspective-axis invariants (unique to _at_batch) ────────────────────────


def test_is_current_is_exclusively_perspective_anchored(ent):
    """For every (perspective, target) pair, ``row["is_current"]`` is
    exactly ``target == perspective`` -- never leaks the resolved
    (live) tier into a surface the caller wanted to be purely
    hypothetical. Pin so a refactor cannot smuggle the live resolver
    into the ``is_current`` computation."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            assert row["is_current"] is (row["id"] == perspective), (
                perspective,
                row["id"],
            )


def test_non_is_current_fields_are_perspective_independent(ent):
    """For every target T, the row's NON-``is_current`` fields are
    byte-identical across every perspective P. Only ``is_current`` moves
    with P. This is the matrix-UI contract: swapping which column the
    user thinks of as "current" cannot change any of the price /
    retention / capacity numbers on any other row."""
    non_is_current = _SPEC_KEYS - {"is_current"}
    reference: dict[str, dict] = {}
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        for row in body["tiers"]:
            projected = {k: row[k] for k in non_is_current}
            prior = reference.get(row["id"])
            if prior is None:
                reference[row["id"]] = projected
            else:
                assert projected == prior, (perspective, row["id"])


def test_exactly_one_row_per_perspective_when_perspective_in_targets_carries_flag(
    ent,
):
    """When the perspective is among the supplied targets, EXACTLY one
    row -- the perspective row -- carries ``is_current=True``. Rules out
    a regression where the flag could stick to two rows (e.g. the
    perspective AND the resolved tier) or none."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        flagged = [row for row in body["tiers"] if row["is_current"]]
        assert len(flagged) == 1, perspective
        assert flagged[0]["id"] == perspective


def test_no_row_carries_flag_when_perspective_not_in_targets(ent):
    """When the perspective is NOT among the supplied targets, NO row
    carries ``is_current=True`` -- there is no "closest-tier" fallback
    the surface could quietly promote to the flag."""
    for perspective in ent._TIER_ORDER:
        others = [t for t in ent._TIER_ORDER if t != perspective]
        body = ent.tier_spec_at_batch(perspective, others)
        assert body is not None
        assert all(row["is_current"] is False for row in body["tiers"]), (
            perspective
        )


# ── cross-family: at_batch(current, ids) vs tier_spec_batch(ids) ─────────────


def test_at_batch_at_current_equals_tier_spec_batch(ent):
    """The mirror of the parity contract pinned by
    ``test_entitlement_tier_spec_batch_invariants.py``: from the
    resolver's perspective ``t``, ``tier_spec_at_batch(t, ids)`` and
    ``tier_spec_batch(ids)`` must produce byte-identical row + unknown
    lists. Written from the ``_at_batch`` side so a regression in
    either direction is caught by both files."""
    ids = list(ent._TIER_ORDER) + ["nope_xyz"]
    resolved = ent.get_entitlement().tier
    whatif = ent.tier_spec_at_batch(resolved, ids)
    live = ent.tier_spec_batch(ids)
    assert whatif is not None
    assert whatif["unknown"] == live["unknown"]
    assert whatif["tiers"] == live["tiers"]


def test_at_batch_row_parity_with_scalar_tier_spec_at_full_matrix(ent):
    """For every (perspective, target) pair in the full matrix, the
    batch row is byte-identical to the scalar ``tier_spec_at`` -- the
    scalar/batch no-drift contract, pinned across the full cross-tier
    matrix (not just a spot-check)."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        rows_by_id = {row["id"]: row for row in body["tiers"]}
        for target in ent._TIER_ORDER:
            assert rows_by_id[target] == ent.tier_spec_at(perspective, target), (
                perspective,
                target,
            )


# ── idempotency ──────────────────────────────────────────────────────────────


def test_batch_is_idempotent(ent):
    """Under stable resolver state, N repeated calls yield byte-identical
    bodies -- no hidden dict-order / floating cache regression."""
    ids = list(ent._TIER_ORDER)
    for perspective in ent._TIER_ORDER:
        first = ent.tier_spec_at_batch(perspective, ids)
        for _ in range(10):
            assert ent.tier_spec_at_batch(perspective, ids) == first, perspective


def test_endpoint_is_idempotent_on_wire(client, ent):
    ids_csv = ",".join(ent._TIER_ORDER)
    for perspective in ent._TIER_ORDER:
        first = client.get(
            f"/api/entitlement/tier-spec-at-batch"
            f"?tier={perspective}&targets={ids_csv}"
        ).get_data(as_text=True)
        for _ in range(10):
            again = client.get(
                f"/api/entitlement/tier-spec-at-batch"
                f"?tier={perspective}&targets={ids_csv}"
            ).get_data(as_text=True)
            assert again == first, perspective


# ── endpoint HTTP contract ───────────────────────────────────────────────────


def test_endpoint_content_type_is_application_json(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
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
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
    )
    assert resp.status_code == 405


def test_endpoint_put_returns_405(client, ent):
    resp = client.put(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
    )
    assert resp.status_code == 405


def test_endpoint_unknown_only_preserves_source_order_unknown(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets=zzz,aaa,mmm"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["zzz", "aaa", "mmm"]


def test_endpoint_envelope_key_set_exact(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


# ── envelope agrees with live resolver ───────────────────────────────────────


def test_endpoint_envelope_grace_matches_resolver(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
    )
    body = resp.get_json()
    assert body["grace"] is bool(ent.get_entitlement().grace)
    assert body["enforced"] is ent.is_enforced()


def test_endpoint_envelope_current_tier_rank_matches_helper(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at-batch"
        f"?tier={ent.TIER_OSS}&targets={ent.TIER_OSS}"
    )
    body = resp.get_json()
    resolved = ent.get_entitlement().tier
    assert body["current_tier"] == resolved
    assert body["current_tier_rank"] == ent.tier_rank(resolved)


def test_endpoint_envelope_perspective_tier_matches_input(client, ent):
    """The envelope's ``perspective_tier`` is the caller-supplied,
    normalised perspective; ``perspective_tier_rank`` byte-agrees with
    ``tier_rank(perspective_tier)``. A UI relying on the echo to label
    its columns cannot be fed a mismatched pair."""
    for perspective in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/tier-spec-at-batch"
            f"?tier={perspective}&targets={ent.TIER_OSS}"
        )
        assert resp.status_code == 200, perspective
        body = resp.get_json()
        assert body["perspective_tier"] == perspective, perspective
        assert body["perspective_tier_rank"] == ent.tier_rank(perspective), (
            perspective
        )


def test_endpoint_perspective_tier_normalised_before_echo(client, ent):
    """A perspective supplied with surrounding whitespace / mixed case
    normalises to the canonical id BEFORE echoing -- the envelope
    always ships the normalised form so a UI can compare it to
    ``current_tier`` for equality without renormalising."""
    resp = client.get(
        "/api/entitlement/tier-spec-at-batch"
        f"?tier=%20%20CLOUD_PRO%20%20&targets={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")


# ── JSON round-trip stability ────────────────────────────────────────────────


def test_batch_body_is_json_round_trip_stable(ent):
    """The Python body must survive ``json.dumps`` -> ``json.loads``
    unchanged -- no non-JSON-safe sentinel (frozenset / tuple / ``None``
    in a spot the spec calls out as a bool) can slip through, for any
    perspective."""
    for perspective in ent._TIER_ORDER:
        body = ent.tier_spec_at_batch(perspective, list(ent._TIER_ORDER))
        assert body is not None
        round_tripped = json.loads(json.dumps(body))
        assert round_tripped == body, perspective


# ── unknown-list source-order preservation ───────────────────────────────────


def test_unknown_list_preserves_supply_order(ent):
    body = ent.tier_spec_at_batch(
        ent.TIER_OSS, ["zzz", ent.TIER_OSS, "aaa", "mmm"]
    )
    assert body is not None
    assert [r["id"] for r in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["zzz", "aaa", "mmm"]


def test_unknown_list_is_normalised_ids_not_raw(ent):
    """The unknown[] list echoes the normalised form (trimmed +
    lowercased), not the raw supplied variant. Otherwise a caller could
    see two entries in ``unknown`` for what is really one bogus id."""
    body = ent.tier_spec_at_batch(ent.TIER_OSS, ["  ZZZ  ", "zzz"])
    assert body is not None
    assert body["tiers"] == []
    # Duplicates collapse after normalisation -- the second "zzz" drops.
    assert body["unknown"] == ["zzz"]


# ── enforcement independence ────────────────────────────────────────────────


def test_batch_body_is_enforcement_independent(ent, monkeypatch):
    """Grace vs enforce yields byte-identical batch bodies for every
    perspective -- ``tier_spec_at_batch`` reads the static per-tier
    maps via ``tier_spec_at``, not the live resolver's enforcement
    knob, so the batch inherits that property. Pins from the invariants
    side that the ship-test's spot-check isn't a coincidence."""
    ids = list(ent._TIER_ORDER)
    grace_bodies = {
        p: ent.tier_spec_at_batch(p, ids) for p in ent._TIER_ORDER
    }
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    for perspective in ent._TIER_ORDER:
        enforced = ent.tier_spec_at_batch(perspective, ids)
        assert enforced == grace_bodies[perspective], perspective
