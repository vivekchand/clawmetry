"""Tests for ``clawmetry.entitlements.tier_spec_batch`` + ``GET
/api/entitlement/tier-spec-batch``.

``tier_spec_batch`` is the plural / caller-subset sibling of
:func:`tier_spec` on the tier axis -- the batch accessor a pricing-page
matrix UI hydrates the N rows it is about to render off in ONE
round-trip instead of N calls to ``/api/entitlement/tier-spec``. Each
returned row must be byte-identical to the corresponding row from
:func:`tier_catalog` (and to the scalar :func:`tier_spec`) so the
scalar / bulk / batch accessors cannot drift; the parity tests below
pin that.

Coverage mirrors ``test_entitlement_channel_spec_batch.py`` /
``test_entitlement_feature_spec_batch``-style tests where they exist:

* helper row shape matches ``tier_spec`` / ``tier_catalog`` for the
  same id (no drift between the scalar and bulk accessors)
* input is normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved) and both CSV strings and
  iterables of ids are accepted
* unknown ids are echoed in ``unknown[]`` instead of 404'ing the call
* catalogue-derived fields are identical in grace vs enforce mode
  (only ``is_current`` shifts with the resolved tier)
* the helper never raises -- a resolver crash short-circuits to the
  OSS-free fallback so the matrix keeps rendering
* the HTTP endpoint 400s on missing / empty input, echoes unknown ids
  in a 200, never 5xxs on a resolver crash, and carries the standard
  ``grace`` / ``enforced`` / ``current_tier`` / ``current_tier_rank``
  envelope fields
* the wire body byte-equals the corresponding rows from
  ``/api/entitlement/tier-spec`` (pins the scalar/batch no-drift
  contract on the wire, not just in Python).
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

_ENVELOPE_KEYS = {"current_tier", "current_tier_rank", "grace", "enforced"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default (grace mode)."""
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


# ── helper: shape ─────────────────────────────────────────────────────────────


def test_batch_empty_list_returns_empty_envelope(ent):
    assert ent.tier_spec_batch([]) == {"tiers": [], "unknown": []}


def test_batch_none_input_returns_empty_envelope(ent):
    assert ent.tier_spec_batch(None) == {"tiers": [], "unknown": []}


def test_batch_empty_string_returns_empty_envelope(ent):
    assert ent.tier_spec_batch("") == {"tiers": [], "unknown": []}


def test_batch_row_shape_matches_scalar(ent):
    body = ent.tier_spec_batch([ent.TIER_CLOUD_STARTER])
    assert len(body["tiers"]) == 1
    assert set(body["tiers"][0].keys()) == _SPEC_KEYS
    assert body["tiers"][0]["id"] == ent.TIER_CLOUD_STARTER


# ── helper: parity with scalar tier_spec / tier_catalog ──────────────────────


def test_batch_every_row_matches_tier_spec_exactly(ent):
    ids = list(ent._TIER_ORDER)
    body = ent.tier_spec_batch(ids)
    rows_by_id = {row["id"]: row for row in body["tiers"]}
    assert set(rows_by_id) == set(ids)
    for tid in ids:
        assert rows_by_id[tid] == ent.tier_spec(tid), tid


def test_batch_rows_match_tier_catalog(ent):
    """Pin scalar / bulk / batch no-drift: every batch row is byte-identical
    to the same row from :func:`tier_catalog`."""
    cat_by_id = {row["id"]: row for row in ent.tier_catalog()}
    ids = list(cat_by_id)
    body = ent.tier_spec_batch(ids)
    assert body["unknown"] == []
    for row in body["tiers"]:
        assert row == cat_by_id[row["id"]], row["id"]


# ── helper: normalisation ─────────────────────────────────────────────────────


def test_batch_supply_order_preserved(ent):
    ids = [ent.TIER_ENTERPRISE, ent.TIER_OSS, ent.TIER_CLOUD_STARTER]
    body = ent.tier_spec_batch(ids)
    assert [r["id"] for r in body["tiers"]] == ids


def test_batch_string_csv_input(ent):
    csv = f"{ent.TIER_OSS},{ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    body = ent.tier_spec_batch(csv)
    assert [r["id"] for r in body["tiers"]] == [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_batch_whitespace_and_case_normalised(ent):
    body = ent.tier_spec_batch(["  CLOUD_STARTER  ", "Enterprise"])
    assert [r["id"] for r in body["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_ENTERPRISE,
    ]


def test_batch_duplicates_dropped_first_seen_wins(ent):
    body = ent.tier_spec_batch(
        [ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_CLOUD_PRO]
    )
    assert [r["id"] for r in body["tiers"]] == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
    ]


def test_batch_trial_is_accepted(ent):
    body = ent.tier_spec_batch([ent.TIER_TRIAL])
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["id"] == ent.TIER_TRIAL
    assert body["unknown"] == []


def test_batch_unknown_ids_echoed_in_unknown(ent):
    body = ent.tier_spec_batch([ent.TIER_OSS, "nope_xyz", "also_bogus"])
    assert [r["id"] for r in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


def test_batch_unknown_only_returns_empty_tiers(ent):
    body = ent.tier_spec_batch(["nope_xyz", "also_bogus"])
    assert body["tiers"] == []
    assert body["unknown"] == ["nope_xyz", "also_bogus"]


# ── helper: grace / enforce identity on catalogue fields ──────────────────────


def test_batch_grace_and_enforce_agree_on_catalogue_fields(ent, monkeypatch, tmp_path):
    ids = list(ent._TIER_ORDER)
    grace = ent.tier_spec_batch(ids)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    enforced = ent.tier_spec_batch(ids)
    # unknown[] must match, and every catalogue-derived field must byte-equal;
    # only is_current is allowed to shift with the resolved tier.
    assert enforced["unknown"] == grace["unknown"]
    g_by_id = {r["id"]: r for r in grace["tiers"]}
    for row in enforced["tiers"]:
        g = g_by_id[row["id"]]
        for k in _SPEC_KEYS - {"is_current"}:
            assert row[k] == g[k], (row["id"], k)


def test_batch_is_current_reflects_resolved_tier(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    body = ent.tier_spec_batch(list(ent._TIER_ORDER))
    for row in body["tiers"]:
        assert row["is_current"] is (row["id"] == ent.TIER_CLOUD_PRO), row["id"]


# ── helper: never-raise ───────────────────────────────────────────────────────


def test_batch_never_raises_when_resolver_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.tier_spec_batch([ent.TIER_CLOUD_PRO, ent.TIER_OSS])
    ids = [r["id"] for r in body["tiers"]]
    assert ids == [ent.TIER_CLOUD_PRO, ent.TIER_OSS]
    # Under the OSS-free fallback, only OSS is marked current.
    for row in body["tiers"]:
        assert row["is_current"] is (row["id"] == ent.TIER_OSS), row["id"]


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_returns_rows_and_envelope(client, ent):
    csv = f"{ent.TIER_OSS},{ent.TIER_CLOUD_PRO}"
    resp = client.get(f"/api/entitlement/tier-spec-batch?tiers={csv}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert _ENVELOPE_KEYS <= set(body.keys())
    assert [r["id"] for r in body["tiers"]] == [ent.TIER_OSS, ent.TIER_CLOUD_PRO]
    assert body["unknown"] == []
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/tier-spec-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/tier-spec-batch?tiers=%20%20,%20")
    assert resp.status_code == 400


def test_endpoint_unknown_only_returns_200(client):
    """Unknown ids alone do not 400 -- they normalise to a non-empty list
    so the helper runs and returns ``unknown=[...]`` with empty tiers."""
    resp = client.get(
        "/api/entitlement/tier-spec-batch?tiers=not_a_tier,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["not_a_tier", "also_bogus"]


def test_endpoint_lowercases_and_dedupes(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_CLOUD_PRO.upper()},"
        f"{ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["tiers"]] == [ent.TIER_CLOUD_PRO]


def test_endpoint_every_known_tier_round_trips(client, ent):
    csv = ",".join(ent._TIER_ORDER)
    resp = client.get(f"/api/entitlement/tier-spec-batch?tiers={csv}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert [r["id"] for r in body["tiers"]] == list(ent._TIER_ORDER)
    assert body["unknown"] == []


def test_endpoint_body_tiers_byte_equal_scalar(client, ent):
    """The batch endpoint body must byte-equal the corresponding rows from
    ``/api/entitlement/tier-spec`` -- pins the scalar / batch no-drift
    contract on the wire."""
    csv = ",".join(ent._TIER_ORDER)
    batch_resp = client.get(f"/api/entitlement/tier-spec-batch?tiers={csv}")
    assert batch_resp.status_code == 200
    for row in batch_resp.get_json()["tiers"]:
        scalar_resp = client.get(
            f"/api/entitlement/tier-spec?tier={row['id']}"
        )
        assert scalar_resp.status_code == 200
        assert row == scalar_resp.get_json(), row["id"]


def test_endpoint_envelope_carries_resolved_tier(
    client, ent, monkeypatch, tmp_path
):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_tier"] == ent.TIER_CLOUD_PRO
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert body["grace"] is False
    assert body["enforced"] is True


def test_endpoint_never_5xxs_when_resolver_crashes(client, ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        f"/api/entitlement/tier-spec-batch?tiers={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    # Endpoint short-circuits to the OSS-free envelope on resolver failure.
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
