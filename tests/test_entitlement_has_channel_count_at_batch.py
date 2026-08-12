"""Tests for the ``has_channel_count_at_batch`` per-value what-if
boolean-gate scalar and its paired
``/api/entitlement/has-channel-count-at-batch`` endpoint.

Perspective-shaped batch sibling of :func:`has_channel_count_at` on the
``channels`` capacity axis: where the singular
``has_channel_count_at(perspective, count)`` answers ONE
(``has_channel_count_at``, ``required_tier``) pair per call, this batch
answers all supplied counts in ONE round-trip -- a pricing paywall
matrix ("at OSS -- does 1 / 5 / 25 / 100 channels fit?") binds off one
URL per perspective instead of N calls.

Row shape mirrors :func:`has_node_count_batch` on the sibling capacity
axis so a UI already wired for the node-axis batch can rebind to this
channel-axis batch without reshaping. Perspective is grace-independent
by construction: unlike the LIVE ``has_channel_count_batch`` sibling,
``has_channel_count_at_batch("oss", [5])`` returns ``has=False`` even
in grace -- the whole point of the ``_at`` slot.

This file pins:

1. Scalar semantics: perspective validation (unknown -> ``None``),
   ``None`` / non-iterable input -> ``[]``, non-int items surface as
   ``unknown=True`` / ``has=False`` rows, zero / negative counts are
   trivially satisfied by the free floor, positive counts reflect the
   STATIC per-tier cap in :data:`_TIER_CHANNEL_LIMIT`.
2. Per-value dedup by normalised int key, preserving first-seen order,
   matching :func:`has_node_count_batch`.
3. Byte-parity per row with :func:`has_channel_count_at` (perspective-
   shaped ``has``) and :func:`min_tier_for_channel_count` (perspective-
   independent reverse lookup) across a mixed grid of perspective
   tiers and counts.
4. Perspective-independence of ``required_tier``: pinned by comparing
   the same row across every ``_TIER_ORDER`` perspective.
5. Endpoint envelope shape (fixed key set) across every input branch;
   ``label`` conjugation matches the sibling
   ``/min-tier-for-channel-count-batch`` row shape ("1 channel" /
   "5 channels").
6. 400 on missing / blank ``?tier=`` or ``?counts=``; 404 on unknown
   ``?tier=``; every other input branch is never-4xx / never-5xx.
7. Cross-consistency with the singular
   ``/api/entitlement/has-channel-count-at`` and the sibling
   ``/api/entitlement/min-tier-for-channel-count-at-batch`` endpoints
   on the ``required_tier`` slot -- byte-parity per row so a paywall
   matrix wiring both can't see inconsistent tier state.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


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


_HELPER_ROW_KEYS = {
    "key",
    "kind",
    "has",
    "unknown",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}

_ROW_KEYS = {
    "count",
    "count_raw",
    "kind",
    "label",
    "has_channel_count_at",
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


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.has_channel_count_at_batch("", [1]) is None
    assert ent.has_channel_count_at_batch(None, [1]) is None
    assert ent.has_channel_count_at_batch("bogus", [1]) is None
    assert ent.has_channel_count_at_batch("Pro+", [1]) is None
    assert ent.has_channel_count_at_batch(123, [1]) is None


def test_scalar_perspective_strip_lower_normalises(ent):
    rows = ent.has_channel_count_at_batch("  OSS  ", [5])
    assert rows is not None
    assert rows[0]["has"] is False  # OSS caps at 3 channels


def test_scalar_valid_perspectives_covered(ent):
    for p in ent._TIER_ORDER:
        rows = ent.has_channel_count_at_batch(p, [1])
        assert rows is not None, p
        assert rows[0]["kind"] == "channels"


def test_scalar_none_counts_returns_empty(ent):
    assert ent.has_channel_count_at_batch("oss", None) == []


def test_scalar_non_iterable_counts_returns_empty(ent):
    assert ent.has_channel_count_at_batch("oss", 5) == []
    assert ent.has_channel_count_at_batch("oss", True) == []


def test_scalar_empty_iterable_returns_empty(ent):
    assert ent.has_channel_count_at_batch("oss", []) == []
    assert ent.has_channel_count_at_batch("oss", ()) == []
    assert ent.has_channel_count_at_batch("oss", set()) == []


def test_scalar_zero_and_negative_are_free_floor(ent):
    rows = ent.has_channel_count_at_batch("oss", [0, -1, -100])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is True
        assert row["unknown"] is False
        assert row["required_tier"] == "oss"


def test_scalar_positive_oss_capped_at_free_floor(ent):
    """OSS caps at ``_FREE_CHANNEL_LIMIT`` (3) even in grace."""
    rows = ent.has_channel_count_at_batch("oss", [1, 3, 4, 5, 100])
    by_key = {r["key"]: r for r in rows}
    assert by_key["1"]["has"] is True
    assert by_key["3"]["has"] is True
    assert by_key["4"]["has"] is False
    assert by_key["5"]["has"] is False
    assert by_key["100"]["has"] is False


def test_scalar_positive_paid_tiers_unlimited(ent):
    """Every paid tier has ``channel_limit=None`` (unlimited)."""
    for p in ("cloud_starter", "cloud_pro", "pro", "enterprise", "trial"):
        rows = ent.has_channel_count_at_batch(p, [1, 5, 100, 10_000])
        assert rows is not None, p
        for row in rows:
            assert row["has"] is True, (p, row)


def test_scalar_non_int_is_unknown_false(ent):
    rows = ent.has_channel_count_at_batch(
        "oss", ["five", None, [], object()]
    )
    assert len(rows) == 4
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None
        assert row["required_tier_rank"] == -1


def test_scalar_dedupes_by_int_key(ent):
    rows = ent.has_channel_count_at_batch("oss", [5, 5, "5", 1, 1, 5])
    keys = [r["key"] for r in rows]
    assert keys == ["5", "1"]


def test_scalar_dedupes_non_int_by_raw_string(ent):
    rows = ent.has_channel_count_at_batch("oss", ["five", "five", "six"])
    assert [r["key"] for r in rows] == ["five", "six"]


def test_scalar_string_int_parses(ent):
    rows = ent.has_channel_count_at_batch("cloud_pro", ["1", "5"])
    assert [r["key"] for r in rows] == ["1", "5"]
    for row in rows:
        assert row["unknown"] is False
        assert row["has"] is True


def test_scalar_row_shape_keys(ent):
    row = ent.has_channel_count_at_batch("oss", [5])[0]
    assert set(row.keys()) == _HELPER_ROW_KEYS
    assert row["kind"] == "channels"


def test_scalar_parity_with_singular_has_channel_count_at(ent):
    """Every row's ``has`` byte-equals :func:`has_channel_count_at` on
    the same (perspective, count)."""
    counts = [0, 1, 2, 3, 4, 5, 10, 100, 1_000]
    for p in ent._TIER_ORDER:
        rows = ent.has_channel_count_at_batch(p, counts)
        assert rows is not None, p
        for row in rows:
            n = int(row["key"])
            assert row["has"] is ent.has_channel_count_at(p, n), (p, n)


def test_scalar_required_tier_parity_with_min_tier(ent):
    """Row ``required_tier`` byte-equals :func:`min_tier_for_channel_count`
    on the same count (perspective-independent)."""
    counts = [0, 1, 3, 5, 100]
    for p in ("oss", "cloud_pro", "enterprise"):
        rows = ent.has_channel_count_at_batch(p, counts)
        for row in rows:
            n = int(row["key"])
            assert row["required_tier"] == ent.min_tier_for_channel_count(n), (
                p,
                n,
            )


def test_scalar_required_tier_perspective_independent(ent):
    """Same count -> same ``required_tier`` on every perspective."""
    for n in (1, 5, 100):
        first: str | None = None
        for p in ent._TIER_ORDER:
            row = ent.has_channel_count_at_batch(p, [n])[0]
            if first is None:
                first = row["required_tier"]
            assert row["required_tier"] == first, (p, n)


def test_scalar_grace_independence(ent):
    """Even in grace, ``has_channel_count_at("oss", 5)`` is False --
    the batch reflects the same static per-tier cap."""
    row = ent.has_channel_count_at_batch("oss", [5])[0]
    assert row["has"] is False
    # Live sibling in grace admits it via grace-passthrough.
    assert ent.has_channel_count(5) is True


def test_scalar_never_raises_on_min_tier_blowup(monkeypatch, ent):
    def _boom(*_a, **_kw):
        raise RuntimeError("min tier blew up")

    monkeypatch.setattr(ent, "min_tier_for_channel_count", _boom)
    rows = ent.has_channel_count_at_batch("oss", [1, 5])
    assert len(rows) == 2
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_missing_tier_400(client):
    resp = client.get("/api/entitlement/has-channel-count-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}
    resp = client.get("/api/entitlement/has-channel-count-at-batch?tier=%20")
    assert resp.status_code == 400


def test_endpoint_missing_counts_400(client):
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss"
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing counts"}
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts="
    )
    assert resp.status_code == 400
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=bogus&counts=5"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body == {"error": "unknown tier", "which": "tier", "tier": "bogus"}


def test_endpoint_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,5,100",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "channel_count"
    assert body["count"] == 3
    assert body["perspective_tier"] == "oss"
    assert body["perspective_tier_label"] == "OSS"
    assert body["perspective_tier_rank"] == 0
    assert len(body["rows"]) == 3
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=cloud_pro&counts=1,5",
    )
    for row in body["rows"]:
        assert isinstance(row["count"], int) or row["count"] is None
        assert isinstance(row["count_raw"], str)
        assert row["kind"] == "channel_count"
        assert isinstance(row["label"], (str, type(None)))
        assert isinstance(row["has_channel_count_at"], bool)
        assert isinstance(row["allowed"], bool)
        assert row["has_channel_count_at"] == row["allowed"]
        assert isinstance(row["unknown"], bool)
        assert isinstance(row["required_tier_rank"], int)


def test_endpoint_label_conjugation(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=cloud_pro&counts=1,5,100",
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["label"] == "1 channel"
    assert by_count[5]["label"] == "5 channels"
    assert by_count[100]["label"] == "100 channels"


def test_endpoint_perspective_shaped_at_oss(client):
    """OSS perspective caps at 3 channels even in grace."""
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,3,4,5",
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["has_channel_count_at"] is True
    assert by_count[3]["has_channel_count_at"] is True
    assert by_count[4]["has_channel_count_at"] is False
    assert by_count[5]["has_channel_count_at"] is False


def test_endpoint_perspective_shaped_paid_unlimited(client):
    for p in ("cloud_starter", "cloud_pro", "pro", "enterprise", "trial"):
        body = _get_json(
            client,
            f"/api/entitlement/has-channel-count-at-batch?tier={p}&counts=1,5,100,10000",
        )
        for row in body["rows"]:
            assert row["has_channel_count_at"] is True, (p, row)


def test_endpoint_deduped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=5,5,1,5,1",
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [5, 1]


def test_endpoint_zero_and_negative_free_floor(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=0,-1,-100",
    )
    for row in body["rows"]:
        assert row["has_channel_count_at"] is True
        assert row["required_tier"] == "oss"


def test_endpoint_non_int_tokens_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=five,ten,1",
    )
    by_raw = {r["count_raw"]: r for r in body["rows"]}
    assert by_raw["five"]["unknown"] is True
    assert by_raw["five"]["has_channel_count_at"] is False
    assert by_raw["five"]["count"] is None
    assert by_raw["ten"]["unknown"] is True
    assert by_raw["1"]["unknown"] is False
    assert by_raw["1"]["count"] == 1


def test_endpoint_whitespace_tokens_dropped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,%20,3,%20%20",
    )
    counts = [r["count"] for r in body["rows"]]
    assert counts == [1, 3]


def test_endpoint_perspective_tier_normalisation(client):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=%20CLOUD_PRO%20&counts=5",
    )
    assert body["perspective_tier"] == "cloud_pro"
    assert body["rows"][0]["has_channel_count_at"] is True


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "oss"


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_channel_count_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


def test_endpoint_never_5xx_on_row_shape_blowup(monkeypatch, client):
    import routes.entitlement as ent_route

    def _boom(*a, **kw):
        raise RuntimeError("row shape blew up")

    monkeypatch.setattr(ent_route, "_has_capacity_at_batch_row_to_body", _boom)
    resp = client.get(
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


# ── Cross-consistency with sibling endpoints ──────────────────────────────


def test_endpoint_required_tier_parity_with_min_tier_at_batch(client):
    """``required_tier`` on each row byte-equals the sibling
    ``/api/entitlement/min-tier-for-channel-count-at-batch`` row for the
    same count -- a UI wiring both cannot see inconsistent tier state."""
    body_has = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,5,100",
    )
    body_min = _get_json(
        client,
        "/api/entitlement/min-tier-for-channel-count-at-batch?tier=oss&counts=1,5,100",
    )
    has_rt = {r["count"]: r["required_tier"] for r in body_has["rows"]}
    min_rt = {r["item"]: r["required_tier"] for r in body_min["rows"]}
    assert has_rt == min_rt


def test_endpoint_has_parity_with_singular_at(client):
    """Every row's ``has_channel_count_at`` byte-equals the singular
    ``/api/entitlement/has-channel-count-at`` endpoint for the same
    (tier, count) pair."""
    for p in ("oss", "cloud_pro", "enterprise"):
        body = _get_json(
            client,
            f"/api/entitlement/has-channel-count-at-batch?tier={p}&counts=1,5,100,0",
        )
        for row in body["rows"]:
            n = row["count"]
            singular = _get_json(
                client,
                f"/api/entitlement/has-channel-count-at?tier={p}&count={n}",
            )
            assert (
                row["has_channel_count_at"]
                == singular["has_channel_count_at"]
            ), (p, n)
            assert row["required_tier"] == singular["required_tier"], (p, n)


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-channel-count-at-batch?tier=cloud_pro&counts=0,1,5,100",
    )
    scalar = ent.has_channel_count_at_batch("cloud_pro", [0, 1, 5, 100])
    assert len(body["rows"]) == len(scalar)
    for row, s in zip(body["rows"], scalar):
        assert row["has_channel_count_at"] is s["has"]
        assert row["required_tier"] == s["required_tier"]
        assert row["unknown"] is s["unknown"]


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1",
        "/api/entitlement/has-channel-count-at-batch?tier=cloud_pro&counts=1,5,100",
        "/api/entitlement/has-channel-count-at-batch?tier=enterprise&counts=0",
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=-1",
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=five,1",
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,1,1",
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=%201%20,%205%20",
    ],
)
def test_endpoint_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "channel_count"
    assert isinstance(body["rows"], list)
    assert body["count"] == len(body["rows"])
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_enforced_mode_still_never_5xx(enforced_client):
    """Post-enforce the answer is unchanged (perspective is grace-
    independent). OSS still caps at 3 channels; the envelope carries
    ``enforced=true`` / ``grace=false`` on the resolver envelope."""
    body = _get_json(
        enforced_client,
        "/api/entitlement/has-channel-count-at-batch?tier=oss&counts=1,3,5",
    )
    by_count = {r["count"]: r for r in body["rows"]}
    assert by_count[1]["has_channel_count_at"] is True
    assert by_count[3]["has_channel_count_at"] is True
    assert by_count[5]["has_channel_count_at"] is False
    assert body["grace"] is False
    assert body["enforced"] is True
