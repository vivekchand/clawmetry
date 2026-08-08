"""Tests for the ``has_retention_window_at_batch`` per-value what-if
boolean-gate scalar and its paired
``/api/entitlement/has-retention-window-at-batch`` endpoint.

Retention-axis twin of :func:`has_channel_count_at_batch`. Same
perspective-shaped contract, same never-5xx posture, same per-row
byte-parity with :func:`has_retention_window_at` (perspective-shaped
``has``) and :func:`min_tier_for_retention_window` (perspective-
independent reverse lookup). Admits the case-insensitive ``"unlimited"``
sentinel and ``None`` -- routed to a row with ``key="unlimited"`` and
``has=True`` iff the perspective's cap is ``None`` (Enterprise on the
current tier table).

This file pins:

1. Scalar semantics: perspective validation, ``None`` / non-iterable
   input -> ``[]``, non-int / non-``"unlimited"`` items surface as
   ``unknown=True`` / ``has=False``, zero / negative days are trivially
   satisfied, positive days reflect the STATIC per-tier cap in
   :data:`_TIER_RETENTION_DAYS`.
2. Unlimited sentinel: ``None`` and case-insensitive ``"unlimited"``
   both collapse to one row with ``key="unlimited"``. ``has=True`` iff
   the perspective's cap is ``None`` (Enterprise only on the current
   tier table).
3. Per-value dedup by normalised key (``"<n>"`` for parsed int,
   ``"unlimited"`` for every case-insensitive variant of the sentinel,
   ``str(raw)`` otherwise).
4. Byte-parity per row with :func:`has_retention_window_at` and
   :func:`min_tier_for_retention_window` on every ``_TIER_ORDER``
   perspective.
5. Endpoint envelope shape (fixed key set) across every input branch;
   ``label`` conjugation matches the sibling
   ``/min-tier-for-retention-window-at-batch`` shape ("1 day" /
   "7 days" / "unlimited").
6. 400 on missing / blank ``?tier=`` or ``?days=``; 404 on unknown
   ``?tier=``; every other input branch is never-4xx / never-5xx.
7. Cross-consistency with the singular
   ``/api/entitlement/has-retention-window-at`` and the sibling
   ``/api/entitlement/min-tier-for-retention-window-at-batch``.
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
    "days",
    "days_raw",
    "kind",
    "label",
    "unlimited",
    "has_retention_window_at",
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
    assert ent.has_retention_window_at_batch("", [7]) is None
    assert ent.has_retention_window_at_batch(None, [7]) is None
    assert ent.has_retention_window_at_batch("bogus", [7]) is None
    assert ent.has_retention_window_at_batch("Pro+", [7]) is None
    assert ent.has_retention_window_at_batch(123, [7]) is None


def test_scalar_valid_perspectives_covered(ent):
    for p in ent._TIER_ORDER:
        rows = ent.has_retention_window_at_batch(p, [7])
        assert rows is not None, p
        assert rows[0]["kind"] == "retention_days"


def test_scalar_none_days_list_returns_empty(ent):
    assert ent.has_retention_window_at_batch("oss", None) == []


def test_scalar_non_iterable_returns_empty(ent):
    assert ent.has_retention_window_at_batch("oss", 7) == []
    assert ent.has_retention_window_at_batch("oss", True) == []


def test_scalar_empty_iterable_returns_empty(ent):
    assert ent.has_retention_window_at_batch("oss", []) == []
    assert ent.has_retention_window_at_batch("oss", ()) == []


def test_scalar_zero_and_negative_are_free_floor(ent):
    rows = ent.has_retention_window_at_batch("oss", [0, -1, -100])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is True
        assert row["unknown"] is False


def test_scalar_positive_oss_capped_at_seven(ent):
    """OSS caps at 7 days; anything beyond fails even in grace."""
    rows = ent.has_retention_window_at_batch("oss", [1, 7, 8, 30, 90])
    by_key = {r["key"]: r for r in rows}
    assert by_key["1"]["has"] is True
    assert by_key["7"]["has"] is True
    assert by_key["8"]["has"] is False
    assert by_key["30"]["has"] is False
    assert by_key["90"]["has"] is False


def test_scalar_unlimited_only_admitted_on_enterprise(ent):
    for p in ent._TIER_ORDER:
        row = ent.has_retention_window_at_batch(p, [None])[0]
        assert row["key"] == "unlimited"
        expected = p == "enterprise"
        assert row["has"] is expected, p


def test_scalar_unlimited_string_variants_dedup(ent):
    rows = ent.has_retention_window_at_batch(
        "enterprise",
        [None, "unlimited", "UNLIMITED", "  Unlimited  "],
    )
    assert len(rows) == 1
    assert rows[0]["key"] == "unlimited"
    assert rows[0]["has"] is True


def test_scalar_string_int_parses(ent):
    rows = ent.has_retention_window_at_batch("cloud_pro", ["7", "30"])
    assert [r["key"] for r in rows] == ["7", "30"]
    for row in rows:
        assert row["unknown"] is False


def test_scalar_non_int_is_unknown_false(ent):
    rows = ent.has_retention_window_at_batch(
        "oss", ["seven", [], object()]
    )
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None
        assert row["required_tier_rank"] == -1


def test_scalar_dedupes_by_int_key(ent):
    rows = ent.has_retention_window_at_batch(
        "oss", [7, 7, "7", 30, 30, 7]
    )
    keys = [r["key"] for r in rows]
    assert keys == ["7", "30"]


def test_scalar_row_shape_keys(ent):
    row = ent.has_retention_window_at_batch("oss", [7])[0]
    assert set(row.keys()) == _HELPER_ROW_KEYS
    assert row["kind"] == "retention_days"


def test_scalar_parity_with_singular_has_retention_window_at(ent):
    """Every finite row's ``has`` byte-equals
    :func:`has_retention_window_at` on the same (perspective, days)."""
    days = [0, 1, 7, 8, 30, 90, 365]
    for p in ent._TIER_ORDER:
        rows = ent.has_retention_window_at_batch(p, days)
        assert rows is not None
        for row in rows:
            n = int(row["key"])
            assert row["has"] is ent.has_retention_window_at(p, n), (p, n)


def test_scalar_parity_unlimited_row_with_singular(ent):
    for p in ent._TIER_ORDER:
        row = ent.has_retention_window_at_batch(p, [None])[0]
        assert row["has"] is ent.has_retention_window_at(p, None), p


def test_scalar_required_tier_perspective_independent(ent):
    for n in (7, 30, 90):
        first: str | None = None
        for p in ent._TIER_ORDER:
            row = ent.has_retention_window_at_batch(p, [n])[0]
            if first is None:
                first = row["required_tier"]
            assert row["required_tier"] == first, (p, n)


def test_scalar_grace_independence(ent):
    row = ent.has_retention_window_at_batch("oss", [30])[0]
    assert row["has"] is False
    # Live sibling in grace admits any finite window.
    assert ent.has_retention_window(30) is True


def test_scalar_never_raises_on_min_tier_blowup(monkeypatch, ent):
    def _boom(*_a, **_kw):
        raise RuntimeError("min tier blew up")

    monkeypatch.setattr(ent, "min_tier_for_retention_window", _boom)
    rows = ent.has_retention_window_at_batch("oss", [7, 30, None])
    assert len(rows) == 3
    for row in rows:
        assert row["has"] is False
        assert row["unknown"] is True
        assert row["required_tier"] is None


# ── Endpoint envelope shape ────────────────────────────────────────────────


def test_endpoint_missing_tier_400(client):
    resp = client.get("/api/entitlement/has-retention-window-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=%20"
    )
    assert resp.status_code == 400


def test_endpoint_missing_days_400(client):
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=oss"
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing days"}
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days="
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=bogus&days=7"
    )
    assert resp.status_code == 404
    assert resp.get_json() == {
        "error": "unknown tier",
        "which": "tier",
        "tier": "bogus",
    }


def test_endpoint_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=cloud_starter&days=7,30,90,unlimited",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == "retention_window"
    assert body["count"] == 4
    assert body["perspective_tier"] == "cloud_starter"
    assert body["perspective_tier_label"] == "Starter"
    assert len(body["rows"]) == 4
    for row in body["rows"]:
        assert set(row.keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=cloud_pro&days=7,unlimited",
    )
    for row in body["rows"]:
        assert isinstance(row["days"], int) or row["days"] is None
        assert isinstance(row["days_raw"], str)
        assert row["kind"] == "retention_window"
        assert isinstance(row["label"], (str, type(None)))
        assert isinstance(row["has_retention_window_at"], bool)
        assert isinstance(row["allowed"], bool)
        assert row["has_retention_window_at"] == row["allowed"]
        assert isinstance(row["unlimited"], bool)
        assert isinstance(row["unknown"], bool)


def test_endpoint_label_conjugation(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=cloud_pro&days=1,7,unlimited",
    )
    by_key = {r["days"] if r["days"] is not None else "unlimited": r for r in body["rows"]}
    assert by_key[1]["label"] == "1 day"
    assert by_key[7]["label"] == "7 days"
    assert by_key["unlimited"]["label"] == "unlimited"
    assert by_key["unlimited"]["unlimited"] is True
    assert by_key["unlimited"]["days"] is None


def test_endpoint_perspective_shaped_at_oss(client):
    """OSS perspective caps at 7 days even in grace."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=1,7,8,30,unlimited",
    )
    by_key = {r["days"] if r["days"] is not None else "unlimited": r for r in body["rows"]}
    assert by_key[1]["has_retention_window_at"] is True
    assert by_key[7]["has_retention_window_at"] is True
    assert by_key[8]["has_retention_window_at"] is False
    assert by_key[30]["has_retention_window_at"] is False
    assert by_key["unlimited"]["has_retention_window_at"] is False


def test_endpoint_unlimited_only_admitted_on_enterprise(client):
    for p in (
        "oss",
        "cloud_free",
        "trial",
        "cloud_starter",
        "cloud_pro",
        "pro",
    ):
        body = _get_json(
            client,
            f"/api/entitlement/has-retention-window-at-batch?tier={p}&days=unlimited",
        )
        row = body["rows"][0]
        assert row["unlimited"] is True
        assert row["has_retention_window_at"] is False, p
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=enterprise&days=unlimited",
    )
    row = body["rows"][0]
    assert row["unlimited"] is True
    assert row["has_retention_window_at"] is True


def test_endpoint_deduped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,7,30,7,unlimited,UNLIMITED",
    )
    keys = [
        (r["days"] if r["days"] is not None else "unlimited")
        for r in body["rows"]
    ]
    assert keys == [7, 30, "unlimited"]


def test_endpoint_zero_and_negative_free_floor(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=0,-1,-100",
    )
    for row in body["rows"]:
        assert row["has_retention_window_at"] is True


def test_endpoint_non_int_tokens_unknown(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=seven,30",
    )
    by_raw = {r["days_raw"]: r for r in body["rows"]}
    assert by_raw["seven"]["unknown"] is True
    assert by_raw["seven"]["has_retention_window_at"] is False
    assert by_raw["seven"]["days"] is None
    assert by_raw["30"]["unknown"] is False
    assert by_raw["30"]["days"] == 30


def test_endpoint_whitespace_tokens_dropped(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,%20,30,%20%20",
    )
    days = [r["days"] for r in body["rows"]]
    assert days == [7, 30]


def test_endpoint_perspective_tier_normalisation(client):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=%20ENTERPRISE%20&days=unlimited",
    )
    assert body["perspective_tier"] == "enterprise"
    assert body["rows"][0]["has_retention_window_at"] is True


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,30"
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

    monkeypatch.setattr(_ent, "has_retention_window_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,30"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


def test_endpoint_never_5xx_on_row_shape_blowup(monkeypatch, client):
    import routes.entitlement as ent_route

    def _boom(*a, **kw):
        raise RuntimeError("row shape blew up")

    monkeypatch.setattr(
        ent_route, "_has_capacity_at_batch_row_to_body", _boom
    )
    resp = client.get(
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,30"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rows"] == []


# ── Cross-consistency with sibling endpoints ──────────────────────────────


def test_endpoint_required_tier_parity_with_min_tier_at_batch(client):
    body_has = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,30,unlimited",
    )
    body_min = _get_json(
        client,
        "/api/entitlement/min-tier-for-retention-window-at-batch?tier=oss&days=7,30,unlimited",
    )
    has_rt = {}
    for r in body_has["rows"]:
        k = "unlimited" if r["days"] is None else r["days"]
        has_rt[k] = r["required_tier"]
    min_rt = {}
    for r in body_min["rows"]:
        k = "unlimited" if r["item"] is None else r["item"]
        min_rt[k] = r["required_tier"]
    assert has_rt == min_rt


def test_endpoint_has_parity_with_singular_at(client):
    for p in ("oss", "cloud_pro", "enterprise"):
        body = _get_json(
            client,
            f"/api/entitlement/has-retention-window-at-batch?tier={p}&days=7,30,90,unlimited",
        )
        for row in body["rows"]:
            days_arg = "unlimited" if row["days"] is None else row["days"]
            singular = _get_json(
                client,
                f"/api/entitlement/has-retention-window-at?tier={p}&days={days_arg}",
            )
            assert (
                row["has_retention_window_at"]
                == singular["has_retention_window_at"]
            ), (p, days_arg)
            assert row["required_tier"] == singular["required_tier"], (p, days_arg)


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at-batch?tier=cloud_pro&days=0,7,30,90,unlimited",
    )
    scalar = ent.has_retention_window_at_batch(
        "cloud_pro", [0, 7, 30, 90, None]
    )
    assert len(body["rows"]) == len(scalar)
    for row, s in zip(body["rows"], scalar):
        assert row["has_retention_window_at"] is s["has"]
        assert row["required_tier"] == s["required_tier"]
        assert row["unknown"] is s["unknown"]


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7",
        "/api/entitlement/has-retention-window-at-batch?tier=cloud_pro&days=7,30,90",
        "/api/entitlement/has-retention-window-at-batch?tier=enterprise&days=unlimited",
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=0",
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=-1",
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=seven,30,unlimited",
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,7,7",
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=%207%20,%2030%20,unlimited",
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


def test_endpoint_enforced_mode_still_never_5xx(enforced_client):
    body = _get_json(
        enforced_client,
        "/api/entitlement/has-retention-window-at-batch?tier=oss&days=7,30,unlimited",
    )
    by_key = {r["days"] if r["days"] is not None else "unlimited": r for r in body["rows"]}
    assert by_key[7]["has_retention_window_at"] is True
    assert by_key[30]["has_retention_window_at"] is False
    assert by_key["unlimited"]["has_retention_window_at"] is False
    assert body["grace"] is False
    assert body["enforced"] is True
