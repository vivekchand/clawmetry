"""Tests for ``lock_reasons_at_batch(perspective_tier, ...)`` +
``GET /api/entitlement/lock-reasons-at-batch``.

What-if sibling of ``lock_reasons_batch`` -- per-item lock-reason rows
for many items at once, computed as if the install were on
``perspective_tier`` rather than against the live resolved entitlement.

Pins:

* the helper is independent of the live resolver (grace mode,
  enforcement, license cache, and cloud_plan.json all have no effect)
* every tier in ``_TIER_ORDER`` returns a dict with the 5 axis keys
* unknown / empty / ``None`` / non-string perspective ids return ``None``
* free features / free runtimes are unlocked at every tier (matches
  the scalar ``lock_reason_at``)
* paid features / paid runtimes are unlocked at the tier their
  ``min_tier_for_*`` answer reports (so the matrix agrees with the
  affordability surface)
* capacity axes use the per-tier caps (``_TIER_CHANNEL_LIMIT`` /
  ``_TIER_RETENTION_DAYS`` / ``_TIER_NODE_LIMIT``) rather than the
  single-node OSS default ``_hypothetical_entitlement`` uses for
  feature/runtime-only callers -- so asking about 100 nodes from
  Enterprise is unlocked, not locked
* the helper never raises -- a synthesis failure short-circuits to
  grace-shape rows
* the endpoint 400s on missing ``tier=`` / no-axis input, 404s on
  unknown tier (with ``which`` carrier), and never 5xxs
* the row shape is byte-identical to ``lock_reasons_batch`` (same 8
  keys per row); the dict adds a ``perspective_tier`` echo for caller
  round-trip safety
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}

_BATCH_KEYS = {"features", "runtimes", "channels", "retention_days", "nodes"}

_API_EXTRA_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- the helper is
    independent of either knob, so the fixture only needs to make sure
    the live resolver does not surprise the test."""
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


# ── helper: shape + round-trip ───────────────────────────────────────────────


def test_helper_returns_dict_with_axis_keys(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_CLOUD_PRO, features=[fid])
    assert isinstance(out, dict)
    assert set(out.keys()) == _BATCH_KEYS


def test_helper_features_row_shape(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_CLOUD_PRO, features=[fid])
    assert isinstance(out["features"], list)
    assert len(out["features"]) == 1
    assert set(out["features"][0].keys()) == _ROW_KEYS


def test_helper_every_tier_returns_dict(ent):
    """Every tier in ``_TIER_ORDER`` resolves to a dict, no crashes."""
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    fid = next(iter(paid_universe))
    for tier in ent._TIER_ORDER:
        out = ent.lock_reasons_at_batch(tier, features=[fid])
        assert isinstance(out, dict), tier
        assert set(out.keys()) == _BATCH_KEYS


# ── invalid perspective tier ─────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reasons_at_batch("not_a_real_tier", features=[fid]) is None


def test_empty_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reasons_at_batch("", features=[fid]) is None


def test_none_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reasons_at_batch(None, features=[fid]) is None


def test_non_string_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reasons_at_batch(123, features=[fid]) is None


# ── feature rows: free + paid ────────────────────────────────────────────────


def test_free_feature_unlocked_at_every_tier(ent):
    """A free feature should never be locked, regardless of perspective."""
    fid = next(iter(ent.FREE_FEATURES))
    for tier in ent._TIER_ORDER:
        out = ent.lock_reasons_at_batch(tier, features=[fid])
        row = out["features"][0]
        assert row["locked"] is False, (tier, fid, row)
        assert row["allowed"] is True, (tier, fid, row)
        assert row["reason"] is None, (tier, fid, row)


def test_paid_feature_locked_on_oss(ent):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, features=[fid])
    row = out["features"][0]
    assert row["locked"] is True
    assert row["allowed"] is False
    assert isinstance(row["reason"], str) and row["reason"]


def test_paid_feature_unlocked_at_pro(ent):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_CLOUD_PRO, features=[fid])
    row = out["features"][0]
    assert row["locked"] is False
    assert row["allowed"] is True
    assert row["reason"] is None


def test_enterprise_feature_locked_below_enterprise(ent):
    fid = next(iter(ent.ENTERPRISE_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_CLOUD_PRO, features=[fid])
    row = out["features"][0]
    assert row["locked"] is True
    assert row["allowed"] is False


def test_enterprise_feature_unlocked_at_enterprise(ent):
    fid = next(iter(ent.ENTERPRISE_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_ENTERPRISE, features=[fid])
    row = out["features"][0]
    assert row["locked"] is False
    assert row["allowed"] is True


def test_unknown_feature_does_not_error(ent):
    """Unknown ids must not raise -- they contribute a row with ``reason
    is None`` (the inner ``lock_reason`` short-circuits on ids it
    doesn't recognise) rather than crashing the matrix."""
    out = ent.lock_reasons_at_batch(
        ent.TIER_OSS, features=["definitely_not_a_real_feature"]
    )
    row = out["features"][0]
    assert row["reason"] is None
    assert row["locked"] is False


# ── runtime rows ─────────────────────────────────────────────────────────────


def test_free_runtime_unlocked_everywhere(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    for tier in ent._TIER_ORDER:
        out = ent.lock_reasons_at_batch(tier, runtimes=[rt])
        row = out["runtimes"][0]
        assert row["locked"] is False, (tier, rt)
        assert row["allowed"] is True, (tier, rt)


def test_paid_runtime_locked_on_oss(ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, runtimes=[rt])
    row = out["runtimes"][0]
    assert row["locked"] is True
    assert row["allowed"] is False


def test_paid_runtime_unlocked_at_paid_tier(ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    out = ent.lock_reasons_at_batch(ent.TIER_CLOUD_STARTER, runtimes=[rt])
    row = out["runtimes"][0]
    assert row["locked"] is False
    assert row["allowed"] is True


# ── capacity rows ────────────────────────────────────────────────────────────


def test_capacity_axes_default_to_none_when_unset(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, features=[fid])
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_nodes_unlocked_at_enterprise_for_large_count(ent):
    """100 nodes at Enterprise must be unlocked. This is the pin
    that ``_hypothetical_entitlement``'s hardcoded ``node_limit=1``
    would get wrong; the helper synthesises its own Entitlement with
    ``_TIER_NODE_LIMIT.get(tier)`` so the per-tier cap flows."""
    out = ent.lock_reasons_at_batch(ent.TIER_ENTERPRISE, nodes=100)
    row = out["nodes"]
    assert row is not None
    assert row["locked"] is False, row
    assert row["allowed"] is True, row


def test_nodes_locked_at_oss_for_large_count(ent):
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, nodes=100)
    row = out["nodes"]
    assert row is not None
    assert row["locked"] is True
    assert row["allowed"] is False


def test_channels_axis_resolves(ent):
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, channels=50)
    row = out["channels"]
    assert row is not None
    assert row["kind"] == "channels"


def test_retention_days_axis_resolves(ent):
    out = ent.lock_reasons_at_batch(ent.TIER_OSS, retention_days=365)
    row = out["retention_days"]
    assert row is not None
    assert row["kind"] == "retention_days"


# ── independence from the live resolver ──────────────────────────────────────


def test_helper_independent_of_grace_mode(ent, monkeypatch):
    """The helper synthesises its own Entitlement so toggling enforcement
    on or off should NOT change the answer at a given perspective."""
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    grace = ent.lock_reasons_at_batch(ent.TIER_OSS, features=[fid])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    enforced = ent.lock_reasons_at_batch(ent.TIER_OSS, features=[fid])
    assert grace["features"][0]["locked"] == enforced["features"][0]["locked"]
    assert grace["features"][0]["reason"] == enforced["features"][0]["reason"]


# ── never-raise + grace-shape fallback ───────────────────────────────────────


def test_helper_never_raises_on_garbage_features(ent):
    """Garbage tokens must not raise -- they contribute grace-shape rows."""
    out = ent.lock_reasons_at_batch(
        ent.TIER_OSS, features=["", None, "valid_id"]  # type: ignore[list-item]
    )
    assert isinstance(out, dict)
    assert isinstance(out["features"], list)


def test_helper_empty_inputs_returns_empty_lists(ent):
    out = ent.lock_reasons_at_batch(ent.TIER_OSS)
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# ── endpoint: error contract ─────────────────────────────────────────────────


def test_endpoint_missing_tier_400(client):
    fid = "any"
    r = client.get(f"/api/entitlement/lock-reasons-at-batch?features={fid}")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_endpoint_blank_tier_400(client):
    r = client.get("/api/entitlement/lock-reasons-at-batch?tier=&features=any")
    assert r.status_code == 400


def test_endpoint_unknown_tier_404(client):
    r = client.get(
        "/api/entitlement/lock-reasons-at-batch?tier=nonsense&features=any"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"
    assert body.get("tier") == "nonsense"


def test_endpoint_no_axis_400(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


# ── endpoint: happy path + shape ─────────────────────────────────────────────


def test_endpoint_returns_full_envelope(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert _BATCH_KEYS.issubset(body.keys())
    assert _API_EXTRA_KEYS.issubset(body.keys())


def test_endpoint_perspective_tier_echoed(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_ENTERPRISE}"
        f"&features={fid}"
    )
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_ENTERPRISE
    assert body["perspective_tier_rank"] == ent.tier_rank(
        ent.TIER_ENTERPRISE
    )


def test_endpoint_current_tier_reflects_live_not_perspective(client, ent):
    """``current_tier`` echoes the live entitlement (OSS/grace by default
    in the fixture), distinct from ``perspective_tier`` -- so a matrix UI
    can render both a 'you are here' badge and a hypothetical column."""
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_ENTERPRISE}"
        f"&features={fid}"
    )
    body = r.get_json()
    assert body["current_tier"] != ent.TIER_ENTERPRISE
    assert body["current_tier"] in ent._TIER_ORDER


def test_endpoint_multi_axis_one_shot(client, ent):
    """The endpoint accepts all 5 axes in one call -- distinguishes it
    from the scalar ``/lock-reason-at`` which is exactly one axis."""
    fid = next(iter(ent.FREE_FEATURES))
    rt = next(iter(ent.FREE_RUNTIMES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid}&runtimes={rt}&channels=5&retention_days=30"
        f"&nodes=2"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert len(body["features"]) == 1
    assert len(body["runtimes"]) == 1
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None


def test_endpoint_csv_dedupe(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid},,{fid}"
    )
    body = r.get_json()
    assert len(body["features"]) == 1


def test_endpoint_blank_capacity_is_not_supplied(client, ent):
    """Blank capacity args don't count as supplied -- matches the
    singular endpoint's never-crash-on-typo posture."""
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid}&channels=&nodes="
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["nodes"] is None


def test_endpoint_non_int_capacity_is_not_supplied(client, ent):
    """Garbage capacity args don't error -- treated as not supplied."""
    fid = next(iter(ent.FREE_FEATURES))
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid}&channels=abc&nodes=xyz"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] is None
    assert body["nodes"] is None


# ── endpoint: row shape parity with /lock-reason-batch ───────────────────────


def test_endpoint_row_shape_matches_lock_reason_batch(client, ent):
    """The per-row shape is byte-identical to ``/lock-reason-batch`` so
    a matrix UI can swap endpoints without reshape logic."""
    fid = next(iter(ent.FREE_FEATURES))
    r_at = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_CLOUD_PRO}"
        f"&features={fid}"
    )
    r_live = client.get(
        f"/api/entitlement/lock-reason-batch?features={fid}"
    )
    row_at = r_at.get_json()["features"][0]
    row_live = r_live.get_json()["features"][0]
    assert set(row_at.keys()) == set(row_live.keys())


def test_endpoint_nodes_at_enterprise_unlocked(client, ent):
    """End-to-end pin of the per-tier node cap correctness."""
    r = client.get(
        f"/api/entitlement/lock-reasons-at-batch?tier={ent.TIER_ENTERPRISE}"
        f"&nodes=100"
    )
    body = r.get_json()
    row = body["nodes"]
    assert row is not None
    assert row["locked"] is False
    assert row["allowed"] is True
