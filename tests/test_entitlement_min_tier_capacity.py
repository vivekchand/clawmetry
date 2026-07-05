"""Tests for the three capacity axes on ``/api/entitlement/min-tier``:
``channels``, ``retention_days`` and ``nodes``.

Previously the singular ``/min-tier`` endpoint accepted only ``feature=`` /
``runtime=`` while its plural sibling ``/min-tier-batch`` already answered on
all five axes. This module pins the closed-symmetry contract: the singular
now delegates to the same three helpers the batch calls
(``min_tier_for_channel_count`` / ``min_tier_for_retention_window`` /
``min_tier_for_node_count``) and returns the same ``key`` / ``value`` /
``free`` / ``min_tier`` / ``tier_label`` / ``tier_rank`` envelope the
``feature`` / ``runtime`` branches return so callers don't have to reshape
per axis.

Invariants pinned here:

* ``/min-tier?channels=<N>`` / ``retention_days=<N>`` / ``nodes=<N>`` return
  the byte-identical envelope shape ``feature`` / ``runtime`` returns
  (``key``, ``value``, ``free``, ``min_tier``, ``tier_label``, ``tier_rank``).
* ``key`` names the axis (``"channels"`` / ``"retention_days"`` /
  ``"nodes"``); ``value`` echoes the *parsed* integer input as a string so a
  pricing-page cell can display it back verbatim.
* Per-axis parity with the underlying helpers: each answer byte-equals
  ``min_tier_for_<axis>(N)`` at the ``min_tier`` field.
* Per-row parity with the plural ``/min-tier-batch`` sibling: for the same
  input ``N`` on the same axis, ``/min-tier`` and the corresponding row of
  ``/min-tier-batch`` land on the same ``min_tier``.
* Non-integer capacity values 400 (matching ``/required-tier``'s parse
  posture) rather than silently mis-routing.
* Mixing axes (``feature=`` + ``channels=`` etc.) 400 -- exactly-one
  constraint still applies across all five axes.
* Zero / negative capacity collapses to ``TIER_OSS`` (matching the helpers'
  grace-on-zero contract), so ``free=True`` -- the "trivially satisfied"
  answer, not an error.
* Catalogue-derived, so the answer is identical in grace and enforce mode.
* Never 5xxs: a resolver failure collapses to the all-``None`` shape so the
  pricing-page cell keeps rendering instead of breaking.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- channels ---------------------------------------------------------------


def test_channels_free_when_within_oss_cap(client, ent):
    # OSS admits at least one channel -- min_tier collapses to OSS.
    rv = client.get("/api/entitlement/min-tier?channels=1")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["key"] == "channels"
    assert body["value"] == "1"
    assert body["min_tier"] == ent.min_tier_for_channel_count(1)
    assert body["free"] is (body["min_tier"] == ent.TIER_OSS)
    assert body["tier_label"] == ent.tier_label(body["min_tier"])
    assert body["tier_rank"] == ent.tier_rank(body["min_tier"])


def test_channels_beyond_free_climbs_ladder(client, ent):
    # A very large channel count should climb past OSS to a paid rung.
    rv = client.get("/api/entitlement/min-tier?channels=1000")
    assert rv.status_code == 200
    body = rv.get_json()
    expected = ent.min_tier_for_channel_count(1000)
    assert body["min_tier"] == expected
    assert body["tier_rank"] == ent.tier_rank(expected)


def test_channels_zero_collapses_to_oss(client, ent):
    # Grace-on-zero contract: zero channels is trivially satisfied by OSS.
    rv = client.get("/api/entitlement/min-tier?channels=0")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_OSS
    assert body["free"] is True
    assert body["value"] == "0"


def test_channels_non_int_400(client):
    rv = client.get("/api/entitlement/min-tier?channels=abc")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "channels" in (body.get("error") or "").lower()


def test_channels_blank_400(client):
    # A supplied-but-empty capacity axis is a parse failure, not "unset" --
    # matches ``_parse_capacity_arg``'s ``present=True, ok=False`` shape.
    rv = client.get("/api/entitlement/min-tier?channels=")
    assert rv.status_code == 400


# -- retention_days ---------------------------------------------------------


def test_retention_days_finite_matches_helper(client, ent):
    rv = client.get("/api/entitlement/min-tier?retention_days=30")
    assert rv.status_code == 200
    body = rv.get_json()
    expected = ent.min_tier_for_retention_window(30)
    assert body["key"] == "retention_days"
    assert body["value"] == "30"
    assert body["min_tier"] == expected
    assert body["tier_label"] == ent.tier_label(expected)
    assert body["tier_rank"] == ent.tier_rank(expected)
    assert body["free"] is (expected == ent.TIER_OSS)


def test_retention_days_zero_collapses_to_oss(client, ent):
    rv = client.get("/api/entitlement/min-tier?retention_days=0")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_OSS
    assert body["free"] is True


def test_retention_days_non_int_400(client):
    rv = client.get("/api/entitlement/min-tier?retention_days=forever")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "retention_days" in (body.get("error") or "").lower()


def test_retention_days_large_climbs_ladder(client, ent):
    # A very long retention window should require Enterprise (the only tier
    # with an unlimited cap).
    rv = client.get("/api/entitlement/min-tier?retention_days=100000")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_ENTERPRISE


# -- nodes ------------------------------------------------------------------


def test_nodes_single_free(client, ent):
    rv = client.get("/api/entitlement/min-tier?nodes=1")
    assert rv.status_code == 200
    body = rv.get_json()
    expected = ent.min_tier_for_node_count(1)
    assert body["key"] == "nodes"
    assert body["value"] == "1"
    assert body["min_tier"] == expected
    assert body["free"] is (expected == ent.TIER_OSS)


def test_nodes_beyond_free_climbs_ladder(client, ent):
    rv = client.get("/api/entitlement/min-tier?nodes=999")
    assert rv.status_code == 200
    body = rv.get_json()
    expected = ent.min_tier_for_node_count(999)
    assert body["min_tier"] == expected
    assert body["tier_rank"] == ent.tier_rank(expected)


def test_nodes_zero_collapses_to_oss(client, ent):
    rv = client.get("/api/entitlement/min-tier?nodes=0")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_OSS
    assert body["free"] is True


def test_nodes_non_int_400(client):
    rv = client.get("/api/entitlement/min-tier?nodes=lots")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "nodes" in (body.get("error") or "").lower()


# -- exactly-one across all five axes ---------------------------------------


def test_no_axis_400(client):
    rv = client.get("/api/entitlement/min-tier")
    assert rv.status_code == 400


def test_two_axes_across_kinds_400(client):
    # feature + capacity axis mix.
    rv = client.get(
        "/api/entitlement/min-tier?feature=sessions&channels=5"
    )
    assert rv.status_code == 400
    # runtime + capacity axis mix.
    rv = client.get(
        "/api/entitlement/min-tier?runtime=openclaw&nodes=3"
    )
    assert rv.status_code == 400
    # Two capacity axes.
    rv = client.get(
        "/api/entitlement/min-tier?channels=5&retention_days=30"
    )
    assert rv.status_code == 400
    rv = client.get(
        "/api/entitlement/min-tier?channels=5&nodes=3"
    )
    assert rv.status_code == 400
    rv = client.get(
        "/api/entitlement/min-tier?retention_days=30&nodes=3"
    )
    assert rv.status_code == 400


def test_three_axes_400(client):
    rv = client.get(
        "/api/entitlement/min-tier?channels=5&retention_days=30&nodes=3"
    )
    assert rv.status_code == 400


# -- envelope shape parity across all five axes -----------------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier?feature=sessions",
        "/api/entitlement/min-tier?runtime=openclaw",
        "/api/entitlement/min-tier?channels=5",
        "/api/entitlement/min-tier?retention_days=30",
        "/api/entitlement/min-tier?nodes=3",
    ],
)
def test_envelope_shape_uniform_across_axes(client, url):
    rv = client.get(url)
    assert rv.status_code == 200
    body = rv.get_json()
    for k in ("key", "value", "free", "min_tier", "tier_label", "tier_rank"):
        assert k in body, k


# -- per-row parity with the plural /min-tier-batch sibling ----------------


def _batch_row(batch_body, axis):
    """Extract the row the plural batch returns for a given axis. Batch
    exposes ``features`` / ``runtimes`` as lists (0/1 rows here) and the
    three capacity axes as a scalar row-or-null."""
    if axis == "features":
        rows = batch_body.get("features") or []
        return rows[0] if rows else None
    if axis == "runtimes":
        rows = batch_body.get("runtimes") or []
        return rows[0] if rows else None
    return batch_body.get(axis)


def test_parity_channels_singular_vs_batch(client):
    single = client.get("/api/entitlement/min-tier?channels=5").get_json()
    batch = client.get("/api/entitlement/min-tier-batch?channels=5").get_json()
    row = _batch_row(batch, "channels")
    assert row is not None
    assert single["min_tier"] == row["min_tier"]
    assert single["free"] == row["free"]


def test_parity_retention_days_singular_vs_batch(client):
    single = client.get(
        "/api/entitlement/min-tier?retention_days=45"
    ).get_json()
    batch = client.get(
        "/api/entitlement/min-tier-batch?retention_days=45"
    ).get_json()
    row = _batch_row(batch, "retention_days")
    assert row is not None
    assert single["min_tier"] == row["min_tier"]
    assert single["free"] == row["free"]


def test_parity_nodes_singular_vs_batch(client):
    single = client.get("/api/entitlement/min-tier?nodes=7").get_json()
    batch = client.get("/api/entitlement/min-tier-batch?nodes=7").get_json()
    row = _batch_row(batch, "nodes")
    assert row is not None
    assert single["min_tier"] == row["min_tier"]
    assert single["free"] == row["free"]


# -- feature / runtime backward compat --------------------------------------


def test_backward_compat_feature_shape_unchanged(client, ent):
    # Same request that shipped in the previous release still returns the
    # historical shape -- extending the endpoint must not shift any existing
    # response.
    rv = client.get("/api/entitlement/min-tier?feature=sessions")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "key": "feature",
        "value": "sessions",
        "free": True,
        "min_tier": ent.TIER_OSS,
        "tier_label": "OSS",
        "tier_rank": 0,
    }


def test_backward_compat_runtime_shape_unchanged(client, ent):
    rv = client.get("/api/entitlement/min-tier?runtime=openclaw")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["key"] == "runtime"
    assert body["value"] == "openclaw"
    assert body["free"] is True
    assert body["min_tier"] == ent.TIER_OSS


def test_backward_compat_unknown_feature_still_404(client):
    rv = client.get("/api/entitlement/min-tier?feature=nonsense_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown"
    assert body["min_tier"] is None


def test_backward_compat_unknown_runtime_still_404(client):
    rv = client.get("/api/entitlement/min-tier?runtime=nonsense_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown"


# -- never-5xx across the three new axes -----------------------------------


def test_never_5xx_on_channels_helper_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "min_tier_for_channel_count", boom)
    rv = client.get("/api/entitlement/min-tier?channels=5")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] is None
    assert body["key"] == "channels"
    assert body["value"] == "5"


def test_never_5xx_on_retention_helper_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "min_tier_for_retention_window", boom)
    rv = client.get("/api/entitlement/min-tier?retention_days=30")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] is None
    assert body["key"] == "retention_days"


def test_never_5xx_on_nodes_helper_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "min_tier_for_node_count", boom)
    rv = client.get("/api/entitlement/min-tier?nodes=3")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] is None
    assert body["key"] == "nodes"


# -- enforce mode: same answer as grace ------------------------------------


def test_capacity_answer_identical_in_enforce_mode(client, ent, monkeypatch):
    # The three helpers walk the static ``_PURCHASABLE_TIERS`` ladder, so the
    # answer must not depend on whether the resolver is in grace or enforce.
    grace_bodies = [
        client.get(f"/api/entitlement/min-tier?{q}").get_json()
        for q in ("channels=5", "retention_days=30", "nodes=3")
    ]
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_bodies = [
        client.get(f"/api/entitlement/min-tier?{q}").get_json()
        for q in ("channels=5", "retention_days=30", "nodes=3")
    ]
    for g, e in zip(grace_bodies, enforce_bodies):
        assert g["min_tier"] == e["min_tier"]
        assert g["free"] == e["free"]
