"""Tests for the ``has_node_count_at_batch`` hypothetical-perspective per-
value boolean-gate scalar and its paired
``/api/entitlement/has-node-count-at-batch`` endpoint.

Perspective-shaped batch sibling of :func:`has_node_count_at` (singular)
and node-axis twin of :func:`has_channel_count_at_batch` /
:func:`has_retention_window_at_batch` on the capacity-axis
``_at_batch`` matrix. Fills the last ``_at_batch`` slot on the ``nodes``
capacity axis alongside :func:`min_tier_for_node_count_at_batch` (the
perspective-tier variant of the reverse-lookup batch on the same axis).

Where the singular ``/has-node-count-at?tier=<perspective>&count=<N>``
answers ONE (``has_node_count_at``, ``required_tier``) pair per request,
this batch answers all requested counts in ONE round-trip so a pricing-
matrix walkthrough ("at OSS -- does 1 / 5 / 25 / 100 nodes fit?") binds
off one URL per perspective instead of ``N`` calls to
``/has-node-count-at?tier=oss&count=<N>``.

This file pins:

1. Scalar semantics: empty / None / non-string / unknown perspective ->
   ``None`` (matches :func:`has_channel_count_at_batch` posture);
   None / non-iterable ``counts`` -> ``[]``; non-int items surface as
   one row with ``unknown=True`` / ``has=False`` (strict callsite-typo
   posture); zero / negative counts are trivially satisfied by the free
   floor on every perspective; positive counts reflect the perspective's
   STATIC cap in :data:`_TIER_NODE_LIMIT` (grace-independent by design).
2. Per-value dedup by normalised int key, preserving first-seen order.
3. Per-row byte-parity with :func:`has_node_count_at` (boolean gate) and
   :func:`min_tier_for_node_count` (perspective-independent reverse
   lookup) across a mixed (perspective, count) grid.
4. Endpoint envelope shape (fixed key set) across every input branch;
   ``label`` conjugation matches the sibling
   ``/min-tier-for-node-count-at-batch`` row shape ("1 node" /
   "5 nodes").
5. Missing / blank ``?tier=`` or ``?counts=`` -> 400; unknown ``tier``
   -> 404 with body ``{"error": "unknown tier", "which": "tier",
   "tier": ...}``. Every other input branch is never-4xx / never-5xx
   (resolver / scalar / row-shape helper blowups all collapse to the
   grace-shape envelope with an empty ``rows`` list).
6. Cross-consistency with the singular
   ``/api/entitlement/has-node-count-at`` and the sibling
   ``/api/entitlement/min-tier-for-node-count-at-batch`` endpoints on
   the ``has_node_count_at`` / ``required_tier`` slots -- byte-parity
   per row so a paywall matrix wiring both cannot see inconsistent
   tier state.
7. Grace-independence assertion: the ``_at`` batch reports ``has=false``
   on OSS even while ``ent.grace`` is True, whereas the LIVE
   :func:`has_node_count_batch` sibling reports True for every finite
   count in grace. Enforced-mode fixture returns byte-stable envelope
   with identical rows (perspective is grace-independent by design).
8. No ``upgrade_required`` bit on the row shape: this is the
   perspective-shaped ``_at`` slot, so comparing against the LIVE
   current-tier rank would double-count the perspective in the paywall
   matrix cell (matches the singular ``/has-node-count-at`` sibling
   which omits it for the same reason).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free grace mode -- matches the
    fixture shape in ``tests/test_entitlement_has_node_count_at.py`` so
    per-row assertions here reproduce the same install state the
    singular scalar is pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` off. Included to pin the perspective-shaped grace-
    independence invariant -- ``has_node_count_at_batch`` returns the
    same rows under grace vs enforce for the same (perspective, counts)
    pair."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── Envelope shape ──────────────────────────────────────────────────────────


_ROW_KEYS = {
    "count",
    "count_raw",
    "kind",
    "label",
    "has_node_count_at",
    "allowed",
    "unknown",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}

_ENVELOPE_KEYS = {
    "kind",
    "count",
    "rows",
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _get_json(client, url: str, expected_status: int = 200) -> dict:
    resp = client.get(url)
    assert resp.status_code == expected_status, (url, resp.status_code)
    return resp.get_json()


# ── Scalar-level tests ─────────────────────────────────────────────────────


def test_scalar_empty_perspective_returns_none(ent):
    for bad in ["", " ", "\t"]:
        assert ent.has_node_count_at_batch(bad, [1, 5]) is None, bad


def test_scalar_non_string_perspective_returns_none(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_node_count_at_batch(bad, [1, 5]) is None, bad


def test_scalar_unknown_perspective_returns_none(ent):
    for bad in ["mars", "pro_plus", "starter", "unknown_tier"]:
        assert ent.has_node_count_at_batch(bad, [1, 5]) is None, bad


def test_scalar_known_perspective_returns_list(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.has_node_count_at_batch(tier, [5])
        assert isinstance(rows, list), tier
        assert len(rows) == 1, tier


def test_scalar_perspective_normalised_uppercase(ent):
    """``strip().lower()`` before ``_TIER_ORDER`` check -- ``ENTERPRISE`` is
    the same perspective as ``enterprise``."""
    r_upper = ent.has_node_count_at_batch("  ENTERPRISE  ", [5])
    r_lower = ent.has_node_count_at_batch("enterprise", [5])
    assert r_upper == r_lower


def test_scalar_none_counts_returns_empty(ent):
    assert ent.has_node_count_at_batch("oss", None) == []


def test_scalar_non_iterable_counts_returns_empty(ent):
    assert ent.has_node_count_at_batch("oss", 5) == []
    assert ent.has_node_count_at_batch("oss", True) == []


def test_scalar_empty_iterable_counts_returns_empty(ent):
    assert ent.has_node_count_at_batch("oss", []) == []
    assert ent.has_node_count_at_batch("oss", ()) == []
    assert ent.has_node_count_at_batch("oss", set()) == []


def test_scalar_zero_and_negative_are_free_floor_on_every_perspective(ent):
    """``count <= 0`` is trivially satisfied by the free floor on every
    real tier (mirrors :func:`has_node_count_at`'s zero contract)."""
    for tier in ent._TIER_ORDER:
        rows = ent.has_node_count_at_batch(tier, [0, -1, -100])
        assert len(rows) == 3, tier
        for row in rows:
            assert row["has"] is True, (tier, row)
            assert row["unknown"] is False, (tier, row)
            assert row["required_tier"] == "oss", (tier, row)


def test_scalar_oss_cap_is_one(ent):
    """OSS statically caps at ``_FREE_NODE_LIMIT`` = 1. Any count above 1
    collapses to has=False regardless of grace state."""
    rows = ent.has_node_count_at_batch("oss", [1, 2, 5, 10_000])
    by_key = {r["key"]: r for r in rows}
    assert by_key["1"]["has"] is True
    for k in ("2", "5", "10000"):
        assert by_key[k]["has"] is False, k
        assert by_key[k]["unknown"] is False, k


def test_scalar_paid_tiers_are_unlimited(ent):
    """Every tier whose ``_TIER_NODE_LIMIT[tier] is None`` admits any
    positive count. Verifies the static per-tier cap table drives the
    per-row ``has`` slot."""
    for tier in ent._TIER_ORDER:
        cap = ent._TIER_NODE_LIMIT.get(tier, ent._FREE_NODE_LIMIT)
        rows = ent.has_node_count_at_batch(tier, [1, 100, 1_000_000])
        by_key = {r["key"]: r for r in rows}
        if cap is None:
            for k in ("1", "100", "1000000"):
                assert by_key[k]["has"] is True, (tier, k)
        else:
            # Finite cap: admits <= cap, denies > cap.
            for k in ("1", "100", "1000000"):
                n = int(k)
                assert by_key[k]["has"] is (n <= cap), (tier, k)


def test_scalar_non_int_is_unknown_false(ent):
    rows = ent.has_node_count_at_batch(
        "cloud_pro", ["five", None, [], object()]
    )
    assert len(rows) == 4
    for row in rows:
        assert row["has"] is False, row
        assert row["unknown"] is True, row
        assert row["required_tier"] is None
        assert row["required_tier_rank"] == -1


def test_scalar_dedupes_by_int_key(ent):
    """Duplicates by normalised int key collapse, first-seen order preserved."""
    rows = ent.has_node_count_at_batch("cloud_pro", [5, 5, "5", 1, 1, 5])
    keys = [r["key"] for r in rows]
    assert keys == ["5", "1"]


def test_scalar_dedupes_non_int_by_raw_string(ent):
    rows = ent.has_node_count_at_batch("cloud_pro", ["five", "five", "six"])
    assert [r["key"] for r in rows] == ["five", "six"]


def test_scalar_string_int_parses(ent):
    """``int("5")`` succeeds, so a string-int is treated as the int itself
    (matches :func:`has_node_count_at`)."""
    rows = ent.has_node_count_at_batch("cloud_pro", ["1", "5"])
    assert [r["key"] for r in rows] == ["1", "5"]
    for row in rows:
        assert row["unknown"] is False
        assert row["has"] is True  # cloud_pro is unlimited


def test_scalar_row_shape_keys(ent):
    row = ent.has_node_count_at_batch("cloud_pro", [5])[0]
    assert set(row.keys()) == {
        "key",
        "kind",
        "has",
        "unknown",
        "required_tier",
        "required_tier_label",
        "required_tier_rank",
    }
    assert row["kind"] == "nodes"


def test_scalar_parity_with_singular_has_node_count_at(ent):
    """Every row's ``has`` byte-equals :func:`has_node_count_at` on the
    same (perspective, count) pair across every tier."""
    counts = [0, 1, 2, 5, 10, 100, 1_000]
    for tier in ent._TIER_ORDER:
        rows = ent.has_node_count_at_batch(tier, counts)
        for row in rows:
            n = int(row["key"])
            assert row["has"] is ent.has_node_count_at(tier, n), (tier, n)


def test_scalar_required_tier_perspective_independent(ent):
    """``required_tier`` byte-equals :func:`min_tier_for_node_count` on the
    same count for every perspective -- the reverse-lookup answer is
    perspective-independent by design (matches
    :func:`has_channel_count_at_batch`)."""
    counts = [0, 1, 2, 5, 100]
    baseline = {n: ent.min_tier_for_node_count(n) for n in counts}
    for tier in ent._TIER_ORDER:
        rows = ent.has_node_count_at_batch(tier, counts)
        for row in rows:
            n = int(row["key"])
            assert row["required_tier"] == baseline[n], (tier, n)


def test_scalar_grace_independence_oss_denies_above_free_floor(ent):
    """The whole point of the ``_at`` slot: ``has_node_count_at_batch("oss",
    [5])`` returns ``has=False`` even while ``ent.grace`` is True,
    unlike the LIVE :func:`has_node_count_batch` sibling."""
    live = ent.get_entitlement()
    assert live.grace is True
    assert ent.has_node_count_batch([5])[0]["has"] is True
    assert ent.has_node_count_at_batch("oss", [5])[0]["has"] is False


def test_scalar_enforced_mode_returns_same_rows(ent, enforced):
    """Perspective-shaped rows are grace-independent by design: the same
    (perspective, counts) pair produces byte-identical rows under grace
    vs enforce."""
    counts = [0, 1, 5, 100, "five"]
    for tier in ent._TIER_ORDER:
        assert ent.has_node_count_at_batch(
            tier, counts
        ) == enforced.has_node_count_at_batch(tier, counts), tier


def test_scalar_never_raises_on_cap_lookup_blowup(monkeypatch, ent):
    """A ``_TIER_NODE_LIMIT`` lookup blowup returns ``None`` (matches the
    perspective-validation failure mode) instead of raising."""

    class _Boom(dict):
        def get(self, *_a, **_kw):
            raise RuntimeError("cap lookup blew up")

    monkeypatch.setattr(ent, "_TIER_NODE_LIMIT", _Boom())
    assert ent.has_node_count_at_batch("oss", [1, 5]) is None


def test_scalar_never_raises_on_min_tier_blowup(monkeypatch, ent):
    """A per-row ``min_tier_for_node_count`` blowup short-circuits to the
    fail-closed row shape so the batch keeps building."""

    def _boom(*_a, **_kw):
        raise RuntimeError("min tier blew up")

    monkeypatch.setattr(ent, "min_tier_for_node_count", _boom)
    rows = ent.has_node_count_at_batch("oss", [1, 5])
    assert len(rows) == 2
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_missing_tier_400(client):
    resp = client.get("/api/entitlement/has-node-count-at-batch?counts=5")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_blank_tier_400(client):
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=&counts=5"
    )
    assert resp.status_code == 400
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=%20&counts=5"
    )
    assert resp.status_code == 400


def test_endpoint_missing_counts_400(client):
    resp = client.get("/api/entitlement/has-node-count-at-batch?tier=oss")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing counts"}


def test_endpoint_blank_counts_400(client):
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts="
    )
    assert resp.status_code == 400
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_404_body_shape(client):
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=bogus&counts=5"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body == {"error": "unknown tier", "which": "tier", "tier": "bogus"}


def test_endpoint_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "node_count"
    assert body["count"] == 3
    assert isinstance(body["rows"], list)
    assert len(body["rows"]) == 3
    assert body["perspective_tier"] == "oss"
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=1,5",
    )
    for row in body["rows"]:
        assert isinstance(row["count"], int) or row["count"] is None
        assert isinstance(row["count_raw"], str)
        assert row["kind"] == "node_count"
        assert isinstance(row["label"], (str, type(None)))
        assert isinstance(row["has_node_count_at"], bool)
        assert isinstance(row["allowed"], bool)
        assert row["has_node_count_at"] == row["allowed"]
        assert isinstance(row["unknown"], bool)
        assert isinstance(row["required_tier_rank"], int)


def test_endpoint_no_upgrade_required_bit(client):
    """The ``_at`` slot is perspective-shaped, so ``upgrade_required``
    would double-count the perspective. Matches the singular
    ``/has-node-count-at`` sibling which omits it for the same reason."""
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5",
    )
    for row in body["rows"]:
        assert "upgrade_required" not in row


def test_endpoint_label_conjugation(client):
    """Label matches the sibling ``/min-tier-for-node-count-at-batch`` shape."""
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=1,5,100",
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["label"] == "1 node"
    assert by_count[5]["label"] == "5 nodes"
    assert by_count[100]["label"] == "100 nodes"


def test_endpoint_deduped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=5,5,1,5,1",
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [5, 1]


def test_endpoint_oss_grace_independence(client):
    """``/has-node-count-at-batch?tier=oss`` reports ``allowed=false`` for
    counts above the free floor EVEN IN GRACE -- the whole point of the
    ``_at`` slot."""
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100",
    )
    assert body["grace"] is True
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["allowed"] is True
    assert by_count[5]["allowed"] is False
    assert by_count[100]["allowed"] is False


def test_endpoint_paid_tier_all_positive_true(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=1,5,100,10000",
    )
    for row in body["rows"]:
        assert row["allowed"] is True
        assert row["has_node_count_at"] is True


def test_endpoint_zero_and_negative_free_floor(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=0,-1,-100",
    )
    for row in body["rows"]:
        assert row["allowed"] is True
        assert row["required_tier"] == "oss"


def test_endpoint_non_int_tokens_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=five,ten,1",
    )
    by_raw = {r["count_raw"]: r for r in body["rows"]}
    assert by_raw["five"]["unknown"] is True
    assert by_raw["five"]["allowed"] is False
    assert by_raw["five"]["count"] is None
    assert by_raw["ten"]["unknown"] is True
    assert by_raw["1"]["unknown"] is False
    assert by_raw["1"]["count"] == 1


def test_endpoint_whitespace_tokens_dropped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=1,%20,5,%20%20",
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [1, 5]


def test_endpoint_perspective_tier_normalised_uppercase(client):
    """``strip().lower()`` before ``_TIER_ORDER`` check -- ``ENTERPRISE`` is
    the same perspective as ``enterprise``."""
    body_upper = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=%20ENTERPRISE%20&counts=5",
    )
    body_lower = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=enterprise&counts=5",
    )
    assert body_upper["perspective_tier"] == "enterprise"
    assert body_upper["rows"] == body_lower["rows"]


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["rows"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "oss"


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_node_count_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


def test_endpoint_never_5xx_on_row_shape_blowup(monkeypatch, client):
    import routes.entitlement as ent_route

    def _boom(*a, **kw):
        raise RuntimeError("row shape blew up")

    monkeypatch.setattr(
        ent_route, "_has_node_count_at_batch_row_to_body", _boom
    )
    resp = client.get(
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


# ── Cross-consistency with sibling endpoints ──────────────────────────────


def test_endpoint_required_tier_parity_with_min_tier_at_batch(client):
    """``required_tier`` on each row byte-equals the sibling
    ``/api/entitlement/min-tier-for-node-count-at-batch`` row for the
    same count -- a UI wiring both cannot see inconsistent tier state."""
    body_has = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100",
    )
    body_min = _get_json(
        client,
        "/api/entitlement/min-tier-for-node-count-at-batch?tier=oss&counts=1,5,100",
    )
    has_rt = {r["count"]: r["required_tier"] for r in body_has["rows"]}
    min_rt = {r["item"]: r["required_tier"] for r in body_min["rows"]}
    assert has_rt == min_rt


def test_endpoint_has_node_count_at_parity_with_singular(client):
    """Every row's ``has_node_count_at`` byte-equals the singular
    ``/api/entitlement/has-node-count-at`` endpoint for the same
    (perspective, count) pair."""
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100,0",
    )
    for row in body["rows"]:
        n = row["count"]
        singular = _get_json(
            client,
            f"/api/entitlement/has-node-count-at?tier=oss&count={n}",
        )
        assert row["has_node_count_at"] == singular["has_node_count_at"], n
        assert row["required_tier"] == singular["required_tier"], n
        assert row["required_tier_rank"] == singular["required_tier_rank"], n


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=0,1,5,100",
    )
    scalar = ent.has_node_count_at_batch("oss", [0, 1, 5, 100])
    assert len(body["rows"]) == len(scalar)
    for row, s in zip(body["rows"], scalar):
        assert row["has_node_count_at"] is s["has"]
        assert row["required_tier"] == s["required_tier"]
        assert row["unknown"] is s["unknown"]


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=0",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=-1",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=five,1",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,1,1",
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=%201%20,%205%20",
        "/api/entitlement/has-node-count-at-batch?tier=cloud_pro&counts=1,5,100",
        "/api/entitlement/has-node-count-at-batch?tier=enterprise&counts=1,10000",
        "/api/entitlement/has-node-count-at-batch?tier=trial&counts=1,5",
    ],
)
def test_endpoint_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "node_count"
    assert isinstance(body["rows"], list)
    assert body["count"] == len(body["rows"])
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_enforced_mode_returns_byte_stable_envelope(enforced_client):
    """Perspective-shaped rows are grace-independent by design: the
    enforced-mode envelope still returns byte-stable rows for the same
    (perspective, counts) pair."""
    body = _get_json(
        enforced_client,
        "/api/entitlement/has-node-count-at-batch?tier=oss&counts=1,5,100",
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["has_node_count_at"] is True
    assert by_count[5]["has_node_count_at"] is False
    assert by_count[100]["has_node_count_at"] is False
    assert body["grace"] is False
    assert body["enforced"] is True


def test_endpoint_perspective_envelope_carries_correct_metadata(client, ent):
    """``perspective_tier_label`` / ``perspective_tier_rank`` byte-equal
    :func:`tier_label` / :func:`tier_rank` on the perspective."""
    for tier in ent._TIER_ORDER:
        body = _get_json(
            client,
            f"/api/entitlement/has-node-count-at-batch?tier={tier}&counts=5",
        )
        assert body["perspective_tier"] == tier
        assert body["perspective_tier_label"] == ent.tier_label(tier)
        assert body["perspective_tier_rank"] == ent.tier_rank(tier)
