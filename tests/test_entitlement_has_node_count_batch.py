"""Tests for the ``has_node_count_batch`` per-value boolean-gate scalar and
its paired ``/api/entitlement/has-node-count-batch`` endpoint.

Batch sibling of :func:`has_node_count` on the ``nodes`` capacity axis:
where the singular ``has_node_count`` answers ONE (has_node_count,
required_tier) pair per call, this batch answers all supplied counts in
ONE round-trip -- a fleet paywall matrix ("does the current install admit
1? 5? 100 nodes?") binds off one URL instead of N calls.

Row shape is byte-parity with the ``nodes`` axis row emitted by
:func:`has_batch` via the shared :func:`_has_row` row-shape helper so a
UI already wired for ``has_batch`` rows can rebind to this per-axis batch
without reshaping.

This file pins:

1. Scalar semantics: ``None`` / non-iterable input -> ``[]``; non-int
   items surface as ``unknown=True`` / ``has=False`` rows; zero /
   negative counts are trivially satisfied by the free floor; positive
   counts reflect the resolver's grace-passthrough (True in grace) and
   the underlying :meth:`Entitlement.allows_node_count` post-enforce.
2. Per-value dedup by normalised int key, preserving first-seen order,
   matching :func:`min_tier_for_node_count_batch`.
3. Byte-parity per row with :func:`has_node_count` (live grant) and
   :func:`min_tier_for_node_count` (reverse lookup) across a mixed grid.
4. Byte-parity per row with the ``nodes`` row emitted by
   :func:`has_batch` for the same count -- the shared ``_has_row``
   helper produces both, so the invariant catches any drift in either.
5. Endpoint envelope shape (fixed key set) across every input branch;
   ``label`` conjugation matches the sibling
   ``/min-tier-for-node-count-batch`` row shape ("1 node" / "5 nodes").
6. Missing / blank ``?counts=`` -> 400; every other input branch is
   never-4xx / never-5xx.
7. Cross-consistency with the singular ``/api/entitlement/has-node-count``
   and the sibling ``/api/entitlement/min-tier-for-node-count-batch``
   endpoints on the ``required_tier`` slot -- byte-parity per row so
   a paywall matrix wiring both can't see inconsistent tier state.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free grace mode -- matches the
    fixture shape in ``tests/test_entitlement_has_node_count.py`` so
    per-row assertions here reproduce the same install state the
    live singular scalar is pinned against."""
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
    ``ent.grace`` off so per-row ``has`` reflects the underlying
    :meth:`Entitlement.allows_node_count` answer instead of the grace
    passthrough. Same shape as the sibling
    ``test_entitlement_has_node_count.py::enforced`` fixture."""
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
    "has_node_count",
    "allowed",
    "unknown",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "upgrade_required",
}

_ENVELOPE_KEYS = {
    "kind",
    "count",
    "rows",
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


def test_scalar_none_returns_empty(ent):
    assert ent.has_node_count_batch(None) == []


def test_scalar_non_iterable_returns_empty(ent):
    assert ent.has_node_count_batch(5) == []
    assert ent.has_node_count_batch(True) == []


def test_scalar_empty_iterable_returns_empty(ent):
    assert ent.has_node_count_batch([]) == []
    assert ent.has_node_count_batch(()) == []
    assert ent.has_node_count_batch(set()) == []


def test_scalar_zero_and_negative_are_free_floor(ent):
    rows = ent.has_node_count_batch([0, -1, -100])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is True
        assert row["unknown"] is False
        assert row["required_tier"] == "oss"


def test_scalar_positive_grace_passthrough(ent):
    rows = ent.has_node_count_batch([1, 5, 100, 10_000])
    assert len(rows) == 4
    for row in rows:
        assert row["has"] is True, row
        assert row["unknown"] is False, row


def test_scalar_positive_after_enforcement(enforced):
    """Post-enforce the OSS-free install caps at 1 node."""
    rows = enforced.has_node_count_batch([1, 2, 5, 100])
    by_key = {r["key"]: r for r in rows}
    assert by_key["1"]["has"] is True
    for k in ("2", "5", "100"):
        assert by_key[k]["has"] is False, k
        # Reverse-lookup tier is unchanged (perspective-independent).
        assert by_key[k]["required_tier"] is not None
        assert by_key[k]["required_tier_rank"] > 0


def test_scalar_non_int_is_unknown_false(ent):
    rows = ent.has_node_count_batch(["five", None, [], object()])
    assert len(rows) == 4
    for row in rows:
        assert row["has"] is False, row
        assert row["unknown"] is True, row
        assert row["required_tier"] is None
        assert row["required_tier_rank"] == -1


def test_scalar_dedupes_by_int_key(ent):
    """Duplicates by normalised int key collapse, first-seen order preserved."""
    rows = ent.has_node_count_batch([5, 5, "5", 1, 1, 5])
    keys = [r["key"] for r in rows]
    assert keys == ["5", "1"]


def test_scalar_dedupes_non_int_by_raw_string(ent):
    rows = ent.has_node_count_batch(["five", "five", "six"])
    assert [r["key"] for r in rows] == ["five", "six"]


def test_scalar_string_int_parses(ent):
    """``int("5")`` succeeds, so a string-int is treated as the int itself
    (matches :func:`has_node_count`)."""
    rows = ent.has_node_count_batch(["1", "5"])
    assert [r["key"] for r in rows] == ["1", "5"]
    for row in rows:
        assert row["unknown"] is False
        assert row["has"] is True  # grace


def test_scalar_row_shape_keys(ent):
    row = ent.has_node_count_batch([5])[0]
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


def test_scalar_parity_with_singular_has_node_count(ent):
    """Every row's ``has`` byte-equals :func:`has_node_count` on the same
    count."""
    counts = [0, 1, 2, 5, 10, 100, 1_000]
    rows = ent.has_node_count_batch(counts)
    for row in rows:
        n = int(row["key"])
        assert row["has"] is ent.has_node_count(n), n


def test_scalar_parity_with_min_tier_for_node_count(ent):
    """Every row's ``required_tier`` byte-equals :func:`min_tier_for_node_count`
    on the same count (perspective-independent)."""
    counts = [0, 1, 2, 5, 100]
    rows = ent.has_node_count_batch(counts)
    for row in rows:
        n = int(row["key"])
        assert row["required_tier"] == ent.min_tier_for_node_count(n), n


def test_scalar_parity_with_has_batch_nodes_row(ent):
    """Row shape is byte-parity with the ``nodes`` axis row emitted by
    :func:`has_batch` -- both delegate to :func:`_has_row`."""
    for n in (0, 1, 5, 100):
        batch_row = ent.has_node_count_batch([n])[0]
        has_batch_row = ent.has_batch(nodes=n)["nodes"]
        assert batch_row == has_batch_row, n


def test_scalar_never_raises_on_resolver_blowup(monkeypatch, ent):
    """A resolver blowup collapses to grace-shape fallback -- the batch
    still returns rows built off the free-tier entitlement."""

    def _boom():
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    rows = ent.has_node_count_batch([1, 5])
    assert len(rows) == 2
    for row in rows:
        assert "has" in row and "required_tier" in row


def test_scalar_never_raises_on_has_row_blowup(monkeypatch, ent):
    """A per-row failure short-circuits to the fail-closed row shape so
    the batch keeps building."""

    def _boom(*_a, **_kw):
        raise RuntimeError("row blew up")

    monkeypatch.setattr(ent, "_has_row", _boom)
    rows = ent.has_node_count_batch([1, 5])
    assert len(rows) == 2
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_missing_counts_400(client):
    resp = client.get("/api/entitlement/has-node-count-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing counts"}


def test_endpoint_blank_counts_400(client):
    resp = client.get("/api/entitlement/has-node-count-batch?counts=")
    assert resp.status_code == 400
    resp = client.get("/api/entitlement/has-node-count-batch?counts=%20%20")
    assert resp.status_code == 400


def test_endpoint_envelope_shape(client):
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=1,5,100")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "node_count"
    assert body["count"] == 3
    assert isinstance(body["rows"], list)
    assert len(body["rows"]) == 3
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=1,5")
    for row in body["rows"]:
        assert isinstance(row["count"], int) or row["count"] is None
        assert isinstance(row["count_raw"], str)
        assert row["kind"] == "node_count"
        assert isinstance(row["label"], (str, type(None)))
        assert isinstance(row["has_node_count"], bool)
        assert isinstance(row["allowed"], bool)
        assert row["has_node_count"] == row["allowed"]
        assert isinstance(row["unknown"], bool)
        assert isinstance(row["required_tier_rank"], int)
        assert isinstance(row["upgrade_required"], bool)


def test_endpoint_label_conjugation(client):
    """Label matches the sibling ``/min-tier-for-node-count-batch`` shape."""
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=1,5,100")
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["label"] == "1 node"
    assert by_count[5]["label"] == "5 nodes"
    assert by_count[100]["label"] == "100 nodes"


def test_endpoint_deduped(client):
    body = _get_json(
        client, "/api/entitlement/has-node-count-batch?counts=5,5,1,5,1"
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [5, 1]


def test_endpoint_grace_all_positive_true(client):
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=1,5,100")
    for row in body["rows"]:
        assert row["has_node_count"] is True
        assert row["allowed"] is True


def test_endpoint_zero_and_negative_free_floor(client):
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=0,-1,-100")
    for row in body["rows"]:
        assert row["has_node_count"] is True
        assert row["required_tier"] == "oss"


def test_endpoint_non_int_tokens_unknown(client):
    body = _get_json(
        client, "/api/entitlement/has-node-count-batch?counts=five,ten,1"
    )
    by_raw = {r["count_raw"]: r for r in body["rows"]}
    assert by_raw["five"]["unknown"] is True
    assert by_raw["five"]["has_node_count"] is False
    assert by_raw["five"]["count"] is None
    assert by_raw["ten"]["unknown"] is True
    assert by_raw["1"]["unknown"] is False
    assert by_raw["1"]["count"] == 1


def test_endpoint_whitespace_tokens_dropped(client):
    body = _get_json(
        client, "/api/entitlement/has-node-count-batch?counts=1,%20,5,%20%20"
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [1, 5]


def test_endpoint_upgrade_required_grace(client):
    """Grace-mode current tier is OSS (rank 0); any row with a paid
    required_tier reports upgrade_required=True."""
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=1,5")
    by_count = {r["count"]: r for r in body["rows"]}
    # count=1 -> required_tier=oss (rank 0) -> not an upgrade
    assert by_count[1]["upgrade_required"] is False
    # count=5 -> required_tier=paid (rank > 0) -> upgrade needed from oss
    assert by_count[5]["upgrade_required"] is True


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-node-count-batch?counts=1,5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["rows"] == []
    assert body["count"] == 0


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_node_count_batch", _boom)
    resp = client.get("/api/entitlement/has-node-count-batch?counts=1,5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


def test_endpoint_never_5xx_on_row_shape_blowup(monkeypatch, client):
    import routes.entitlement as ent_route

    def _boom(*a, **kw):
        raise RuntimeError("row shape blew up")

    monkeypatch.setattr(ent_route, "_has_node_count_batch_row_to_body", _boom)
    resp = client.get("/api/entitlement/has-node-count-batch?counts=1,5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


# ── Cross-consistency with sibling endpoints ──────────────────────────────


def test_endpoint_required_tier_parity_with_min_tier_batch(client):
    """``required_tier`` on each row byte-equals the sibling
    ``/api/entitlement/min-tier-for-node-count-batch`` row for the same
    count -- a UI wiring both cannot see inconsistent tier state."""
    body_has = _get_json(
        client, "/api/entitlement/has-node-count-batch?counts=1,5,100"
    )
    body_min = _get_json(
        client, "/api/entitlement/min-tier-for-node-count-batch?counts=1,5,100"
    )
    has_rt = {r["count"]: r["required_tier"] for r in body_has["rows"]}
    min_rt = {r["item"]: r["required_tier"] for r in body_min["rows"]}
    assert has_rt == min_rt


def test_endpoint_has_node_count_parity_with_singular(client):
    """Every row's ``has_node_count`` byte-equals the singular
    ``/api/entitlement/has-node-count`` endpoint for the same count."""
    body = _get_json(
        client, "/api/entitlement/has-node-count-batch?counts=1,5,100,0"
    )
    for row in body["rows"]:
        n = row["count"]
        singular = _get_json(
            client, f"/api/entitlement/has-node-count?count={n}"
        )
        assert row["has_node_count"] == singular["has_node_count"], n
        assert row["required_tier"] == singular["required_tier"], n
        assert row["required_tier_rank"] == singular["required_tier_rank"], n


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(client, "/api/entitlement/has-node-count-batch?counts=0,1,5,100")
    scalar = ent.has_node_count_batch([0, 1, 5, 100])
    assert len(body["rows"]) == len(scalar)
    for row, s in zip(body["rows"], scalar):
        assert row["has_node_count"] is s["has"]
        assert row["required_tier"] == s["required_tier"]
        assert row["unknown"] is s["unknown"]


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-node-count-batch?counts=1",
        "/api/entitlement/has-node-count-batch?counts=1,5,100",
        "/api/entitlement/has-node-count-batch?counts=0",
        "/api/entitlement/has-node-count-batch?counts=-1",
        "/api/entitlement/has-node-count-batch?counts=five,1",
        "/api/entitlement/has-node-count-batch?counts=1,1,1",
        "/api/entitlement/has-node-count-batch?counts=%201%20,%205%20",
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


def test_endpoint_enforced_mode_still_never_5xx(enforced_client):
    """Post-enforce the OSS-free install caps at 1 node; the batch still
    returns rows with byte-stable shape."""
    body = _get_json(
        enforced_client, "/api/entitlement/has-node-count-batch?counts=1,5,100"
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["has_node_count"] is True
    assert by_count[5]["has_node_count"] is False
    assert by_count[100]["has_node_count"] is False
    assert body["grace"] is False
    assert body["enforced"] is True
