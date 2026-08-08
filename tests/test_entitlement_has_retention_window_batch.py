"""Tests for the ``has_retention_window_batch`` per-value boolean-gate
scalar and its paired ``/api/entitlement/has-retention-window-batch``
endpoint.

Batch sibling of :func:`has_retention_window` on the ``retention_days``
capacity axis and retention-axis twin of :func:`has_node_count_batch` /
:func:`has_channel_count_batch`. Where the singular
``has_retention_window`` answers ONE (``has_retention_window``,
``required_tier``) pair per call, this batch answers all supplied
windows -- including the ``"unlimited"`` sentinel -- in ONE round-trip:
a history-range paywall matrix ("does the current install admit 7 / 30
/ 90 / unlimited?") binds off one URL instead of ``N`` calls.

Row shape for the finite windows is byte-parity with the
``retention_days`` axis row emitted by :func:`has_batch` via the shared
:func:`_has_row` row-shape helper; the ``"unlimited"`` sentinel row --
the ONE thing :func:`has_batch` cannot express (its
``retention_days=None`` argument is *unset*, not *unlimited*) -- is
built locally to match :func:`_retention_batch_row` on the
``min_tier_for_retention_window_batch`` side and the singular
``has_retention_window(None)`` scalar.

This file mirrors ``tests/test_entitlement_has_node_count_batch.py`` on
structure and adds unlimited-sentinel-specific assertions the sibling
batches don't need.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free grace mode."""
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


_ROW_KEYS = {
    "days",
    "days_raw",
    "unlimited",
    "kind",
    "label",
    "has_retention_window",
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
    assert ent.has_retention_window_batch(None) == []


def test_scalar_non_iterable_returns_empty(ent):
    assert ent.has_retention_window_batch(5) == []
    assert ent.has_retention_window_batch(True) == []


def test_scalar_empty_iterable_returns_empty(ent):
    assert ent.has_retention_window_batch([]) == []
    assert ent.has_retention_window_batch(()) == []
    assert ent.has_retention_window_batch(set()) == []


def test_scalar_zero_and_negative_are_free_floor(ent):
    rows = ent.has_retention_window_batch([0, -1, -100])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is True
        assert row["unknown"] is False
        assert row["required_tier"] == "oss"


def test_scalar_positive_grace_passthrough(ent):
    rows = ent.has_retention_window_batch([1, 30, 365, 10_000])
    assert len(rows) == 4
    for row in rows:
        assert row["has"] is True, row
        assert row["unknown"] is False, row


def test_scalar_unlimited_sentinel_by_string(ent):
    rows = ent.has_retention_window_batch(["unlimited"])
    assert len(rows) == 1
    row = rows[0]
    assert row["key"] == "unlimited"
    assert row["kind"] == "retention_days"
    assert row["unknown"] is False
    # Grace mode -> has=True for every tier
    assert row["has"] is True
    # Cheapest tier admitting unlimited is whatever the singular helper says
    assert row["required_tier"] == ent.min_tier_for_retention_window(None)


def test_scalar_unlimited_sentinel_case_insensitive(ent):
    rows = ent.has_retention_window_batch(["UNLIMITED", "  unlimited  "])
    assert [r["key"] for r in rows] == ["unlimited"]


def test_scalar_unlimited_sentinel_by_none(ent):
    rows = ent.has_retention_window_batch([None])
    assert len(rows) == 1
    assert rows[0]["key"] == "unlimited"
    assert rows[0]["unknown"] is False


def test_scalar_non_int_non_unlimited_is_unknown_false(ent):
    rows = ent.has_retention_window_batch(["seven", [], object()])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is False, row
        assert row["unknown"] is True, row
        assert row["required_tier"] is None
        assert row["required_tier_rank"] == -1


def test_scalar_dedupes_by_int_key(ent):
    """Duplicates by normalised int key collapse, first-seen order preserved."""
    rows = ent.has_retention_window_batch([30, 30, "30", 7, 7, 30])
    keys = [r["key"] for r in rows]
    assert keys == ["30", "7"]


def test_scalar_dedupes_unlimited(ent):
    rows = ent.has_retention_window_batch(["unlimited", None, "UNLIMITED", 7])
    assert [r["key"] for r in rows] == ["unlimited", "7"]


def test_scalar_dedupes_non_int_by_raw_string(ent):
    rows = ent.has_retention_window_batch(["seven", "seven", "ten"])
    assert [r["key"] for r in rows] == ["seven", "ten"]


def test_scalar_string_int_parses(ent):
    """``int("30")`` succeeds so a string-int is treated as the int itself
    (matches :func:`has_retention_window`)."""
    rows = ent.has_retention_window_batch(["7", "30"])
    assert [r["key"] for r in rows] == ["7", "30"]
    for row in rows:
        assert row["unknown"] is False
        assert row["has"] is True  # grace


def test_scalar_row_shape_keys(ent):
    row = ent.has_retention_window_batch([30])[0]
    assert set(row.keys()) == {
        "key",
        "kind",
        "has",
        "unknown",
        "required_tier",
        "required_tier_label",
        "required_tier_rank",
    }
    assert row["kind"] == "retention_days"


def test_scalar_parity_with_singular_has_retention_window(ent):
    """Every row's ``has`` byte-equals :func:`has_retention_window` on the
    same value (finite ints AND the unlimited sentinel)."""
    values = [0, 1, 7, 30, 90, 365, 10_000, "unlimited", None]
    rows = ent.has_retention_window_batch(values)
    for row in rows:
        if row["key"] == "unlimited":
            assert row["has"] is ent.has_retention_window(None)
        else:
            n = int(row["key"])
            assert row["has"] is ent.has_retention_window(n), n


def test_scalar_parity_with_min_tier_for_retention_window(ent):
    """Every row's ``required_tier`` byte-equals
    :func:`min_tier_for_retention_window` on the same value."""
    values = [0, 7, 30, 90, "unlimited"]
    rows = ent.has_retention_window_batch(values)
    for row in rows:
        if row["key"] == "unlimited":
            assert row["required_tier"] == ent.min_tier_for_retention_window(None)
        else:
            n = int(row["key"])
            assert row["required_tier"] == ent.min_tier_for_retention_window(n), n


def test_scalar_finite_parity_with_has_batch_retention_row(ent):
    """Finite-window row shape is byte-parity with the ``retention_days``
    axis row emitted by :func:`has_batch` -- both delegate to
    :func:`_has_row`. The ``"unlimited"`` sentinel is not shared with
    :func:`has_batch`, whose ``retention_days=None`` argument is *unset*
    rather than *unlimited*, so this parity is asserted only for finite
    ints."""
    for n in (0, 7, 30, 90, 365):
        batch_row = ent.has_retention_window_batch([n])[0]
        has_batch_row = ent.has_batch(retention_days=n)["retention_days"]
        assert batch_row == has_batch_row, n


def test_scalar_never_raises_on_resolver_blowup(monkeypatch, ent):
    """A resolver blowup collapses to grace-shape fallback."""

    def _boom():
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    rows = ent.has_retention_window_batch([1, 30, "unlimited"])
    assert len(rows) == 3
    for row in rows:
        assert "has" in row and "required_tier" in row


def test_scalar_never_raises_on_has_row_blowup(monkeypatch, ent):
    """A per-row failure short-circuits to the fail-closed row shape for
    the finite rows; the unlimited row builds locally and stays intact."""

    def _boom(*_a, **_kw):
        raise RuntimeError("row blew up")

    monkeypatch.setattr(ent, "_has_row", _boom)
    rows = ent.has_retention_window_batch([1, 30])
    assert len(rows) == 2
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_missing_days_400(client):
    resp = client.get("/api/entitlement/has-retention-window-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing days"}


def test_endpoint_blank_days_400(client):
    resp = client.get("/api/entitlement/has-retention-window-batch?days=")
    assert resp.status_code == 400
    resp = client.get("/api/entitlement/has-retention-window-batch?days=%20%20")
    assert resp.status_code == 400


def test_endpoint_envelope_shape(client):
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=7,30,unlimited"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "retention_window"
    assert body["count"] == 3
    assert isinstance(body["rows"], list)
    assert len(body["rows"]) == 3
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=7,30,unlimited"
    )
    for row in body["rows"]:
        assert isinstance(row["days"], int) or row["days"] is None
        assert isinstance(row["days_raw"], str)
        assert row["kind"] == "retention_window"
        assert isinstance(row["label"], (str, type(None)))
        assert isinstance(row["has_retention_window"], bool)
        assert isinstance(row["allowed"], bool)
        assert row["has_retention_window"] == row["allowed"]
        assert isinstance(row["unlimited"], bool)
        assert isinstance(row["unknown"], bool)
        assert isinstance(row["required_tier_rank"], int)
        assert isinstance(row["upgrade_required"], bool)


def test_endpoint_label_conjugation(client):
    """Label matches the sibling ``/min-tier-for-retention-window-batch`` shape."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=1,7,unlimited"
    )
    by_key = {(r["days"], r["unlimited"]): r for r in body["rows"]}
    assert by_key[(1, False)]["label"] == "1 day"
    assert by_key[(7, False)]["label"] == "7 days"
    assert by_key[(None, True)]["label"] == "unlimited"


def test_endpoint_unlimited_case_insensitive(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-batch?days=UNLIMITED",
    )
    assert len(body["rows"]) == 1
    row = body["rows"][0]
    assert row["unlimited"] is True
    assert row["days"] is None
    assert row["label"] == "unlimited"


def test_endpoint_deduped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-batch?days=30,30,7,30,unlimited,unlimited",
    )
    keys = [
        (r["days"], r["unlimited"]) for r in body["rows"]
    ]
    assert keys == [(30, False), (7, False), (None, True)]


def test_endpoint_grace_all_true(client):
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=1,30,365,unlimited"
    )
    for row in body["rows"]:
        assert row["has_retention_window"] is True
        assert row["allowed"] is True


def test_endpoint_zero_and_negative_free_floor(client):
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=0,-1,-100"
    )
    for row in body["rows"]:
        assert row["has_retention_window"] is True
        assert row["required_tier"] == "oss"


def test_endpoint_non_int_non_unlimited_tokens_unknown(client):
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=seven,ten,30"
    )
    by_raw = {r["days_raw"]: r for r in body["rows"]}
    assert by_raw["seven"]["unknown"] is True
    assert by_raw["seven"]["has_retention_window"] is False
    assert by_raw["seven"]["days"] is None
    assert by_raw["ten"]["unknown"] is True
    assert by_raw["30"]["unknown"] is False
    assert by_raw["30"]["days"] == 30


def test_endpoint_whitespace_tokens_dropped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-batch?days=7,%20,30,%20%20",
    )
    days = [r["days"] for r in body["rows"]]
    assert days == [7, 30]


def test_endpoint_upgrade_required_grace(client):
    """Grace-mode current tier is OSS (rank 0); any row with a paid
    required_tier reports upgrade_required=True."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=1,unlimited"
    )
    by_key = {(r["days"], r["unlimited"]): r for r in body["rows"]}
    assert by_key[(1, False)]["upgrade_required"] is False
    assert by_key[(None, True)]["upgrade_required"] is True


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-batch?days=7,unlimited"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["rows"] == []
    assert body["count"] == 0


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_retention_window_batch", _boom)
    resp = client.get("/api/entitlement/has-retention-window-batch?days=7,30")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


def test_endpoint_never_5xx_on_row_shape_blowup(monkeypatch, client):
    import routes.entitlement as ent_route

    def _boom(*a, **kw):
        raise RuntimeError("row shape blew up")

    monkeypatch.setattr(
        ent_route, "_has_retention_window_batch_row_to_body", _boom
    )
    resp = client.get("/api/entitlement/has-retention-window-batch?days=7,30")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


# ── Cross-consistency with sibling endpoints ──────────────────────────────


def test_endpoint_required_tier_parity_with_min_tier_batch(client):
    """``required_tier`` on each row byte-equals the sibling
    ``/api/entitlement/min-tier-for-retention-window-batch`` row for the
    same value -- a UI wiring both cannot see inconsistent tier state."""
    body_has = _get_json(
        client, "/api/entitlement/has-retention-window-batch?days=7,30,unlimited"
    )
    body_min = _get_json(
        client,
        "/api/entitlement/min-tier-for-retention-window-batch?days=7,30,unlimited",
    )
    has_rt = {(r["days"], r["unlimited"]): r["required_tier"] for r in body_has["rows"]}
    # min-tier batch uses ``item`` (int on finite rows; null on unlimited)
    min_rt = {}
    for r in body_min["rows"]:
        if r["item"] is None:
            min_rt[(None, True)] = r["required_tier"]
        else:
            min_rt[(r["item"], False)] = r["required_tier"]
    assert has_rt == min_rt


def test_endpoint_has_retention_window_parity_with_singular(client):
    """Every row's ``has_retention_window`` byte-equals the singular
    ``/api/entitlement/has-retention-window`` endpoint for the same
    value."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-batch?days=1,7,30,unlimited",
    )
    for row in body["rows"]:
        if row["unlimited"]:
            singular = _get_json(
                client, "/api/entitlement/has-retention-window?days=unlimited"
            )
        else:
            singular = _get_json(
                client, f"/api/entitlement/has-retention-window?days={row['days']}"
            )
        assert row["has_retention_window"] == singular["has_retention_window"], row
        assert row["required_tier"] == singular["required_tier"], row
        assert row["required_tier_rank"] == singular["required_tier_rank"], row


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-batch?days=0,7,30,unlimited",
    )
    scalar = ent.has_retention_window_batch([0, 7, 30, "unlimited"])
    assert len(body["rows"]) == len(scalar)
    for row, s in zip(body["rows"], scalar):
        assert row["has_retention_window"] is s["has"]
        assert row["required_tier"] == s["required_tier"]
        assert row["unknown"] is s["unknown"]


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-retention-window-batch?days=7",
        "/api/entitlement/has-retention-window-batch?days=7,30,365",
        "/api/entitlement/has-retention-window-batch?days=unlimited",
        "/api/entitlement/has-retention-window-batch?days=0",
        "/api/entitlement/has-retention-window-batch?days=-1",
        "/api/entitlement/has-retention-window-batch?days=seven,7",
        "/api/entitlement/has-retention-window-batch?days=7,7,7",
        "/api/entitlement/has-retention-window-batch?days=%207%20,%2030%20",
        "/api/entitlement/has-retention-window-batch?days=7,unlimited,90",
    ],
)
def test_endpoint_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "retention_window"
    assert isinstance(body["rows"], list)
    assert body["count"] == len(body["rows"])
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_enforced_mode_still_never_5xx(enforced_client, enforced):
    """Post-enforce the OSS-free install caps at the free-retention floor;
    the batch still returns rows with byte-stable shape and the
    unlimited row collapses to Enterprise-only."""
    body = _get_json(
        enforced_client,
        "/api/entitlement/has-retention-window-batch?days=1,30,365,unlimited",
    )
    for row in body["rows"]:
        if row["unlimited"]:
            assert row["has_retention_window"] is enforced.has_retention_window(None)
        else:
            assert row["has_retention_window"] is enforced.has_retention_window(
                row["days"]
            )
    assert body["grace"] is False
    assert body["enforced"] is True
