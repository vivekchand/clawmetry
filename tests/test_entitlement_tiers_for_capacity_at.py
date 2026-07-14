"""Tests for ``clawmetry.entitlements.tiers_for_channel_count_at`` /
``tiers_for_retention_window_at`` / ``tiers_for_node_count_at`` /
``tiers_for_capacity_batch_at`` plus their HTTP endpoints
``GET /api/entitlement/tiers-for-channel-count-at`` /
``.../tiers-for-retention-window-at`` /
``.../tiers-for-node-count-at`` /
``.../tiers-for-capacity-batch-at``.

Hypothetical-perspective siblings of the four capacity-axis
``tiers_for_*`` helpers. Same relationship to the base helpers that
``tiers_for_feature_at`` / ``tiers_for_runtime_at`` / ``tiers_for_batch_at``
have to their non-``_at`` siblings on the grant axes: the
``perspective_tier`` argument is validated against ``_TIER_ORDER``
(``trial`` accepted) but does NOT shape rows -- the ladder is
intrinsically perspective-independent because it walks static per-tier
capacity tables.

These tests pin:

* every ``p`` in ``_TIER_ORDER`` yields identical rows to the base
  helper (parity across perspectives) for every capacity axis
* perspective validation: empty / blank / ``None`` / unknown / non-str
  -> ``None`` at the helper layer, ``400`` / ``404`` at the HTTP layer
* helpers never raise and stay decoupled from the live entitlement
  (grace vs enforce yields byte-identical rows)
* the endpoints round-trip every axis and carry the perspective +
  resolver envelope; 400 on missing/blank ``tier=``, 404 on unknown
  ``tier=``, 400 on missing/blank/non-int capacity args (per-axis
  endpoints); the batch endpoint 400s only when NO axis parsed (matches
  ``/tiers-for-capacity-batch``'s never-mis-route posture)
* cross-endpoint parity: rows returned by ``/tiers-for-*-at`` byte-equal
  the non-``_at`` sibling (minus the perspective envelope) for every
  ``p``
* ``retention_days=None`` means *unset* in the batch, NOT unlimited
  (matches ``/tiers-for-capacity-batch``'s semantics); the singular
  ``/tiers-for-retention-window-at?days=unlimited`` call handles the
  unlimited request
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


_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}

_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_channel_count_at
# ══════════════════════════════════════════════════════════════════════════════


# ── shape parity ─────────────────────────────────────────────────────────────


def test_channel_at_returns_full_shape(ent):
    body = ent.tiers_for_channel_count_at(ent.TIER_CLOUD_STARTER, 5)
    assert body is not None
    assert set(body.keys()) == _ROW_KEYS
    assert body["kind"] == "channel_count"
    assert body["item"] == 5


def test_channel_at_row_shape_matches_singular(ent):
    body = ent.tiers_for_channel_count_at(ent.TIER_CLOUD_STARTER, 5)
    assert body["tiers"]
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}


# ── perspective-independence parity ──────────────────────────────────────────


def test_channel_at_byte_parity_across_perspectives(ent):
    """`tiers_for_channel_count_at(p, n) == tiers_for_channel_count(n)`
    for every ``p`` in ``_TIER_ORDER`` -- pins the ``_at`` prefix
    against silently shaping rows."""
    for n in (-1, 0, 1, 3, 5, 100, 10_000):
        base = ent.tiers_for_channel_count(n)
        for p in ent._TIER_ORDER:
            assert ent.tiers_for_channel_count_at(p, n) == base, (p, n)


# ── perspective validation ───────────────────────────────────────────────────


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier", "not_a_tier"])
def test_channel_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_channel_count_at(bad, 5) is None


def test_channel_at_none_perspective_returns_none(ent):
    assert ent.tiers_for_channel_count_at(None, 5) is None  # type: ignore[arg-type]


def test_channel_at_non_string_perspective_returns_none(ent):
    assert ent.tiers_for_channel_count_at(42, 5) is None  # type: ignore[arg-type]
    assert ent.tiers_for_channel_count_at([], 5) is None  # type: ignore[arg-type]


def test_channel_at_trial_perspective_accepted(ent):
    assert ent.tiers_for_channel_count_at(ent.TIER_TRIAL, 5) is not None


def test_channel_at_perspective_case_insensitive(ent):
    upper = ent.TIER_CLOUD_PRO.upper()
    assert (
        ent.tiers_for_channel_count_at(upper, 5)
        == ent.tiers_for_channel_count(5)
    )


def test_channel_at_perspective_whitespace_stripped(ent):
    padded = f"  {ent.TIER_CLOUD_PRO}  "
    assert (
        ent.tiers_for_channel_count_at(padded, 5)
        == ent.tiers_for_channel_count(5)
    )


# ── input validation ─────────────────────────────────────────────────────────


def test_channel_at_non_int_count_returns_none(ent):
    assert ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, "nope") is None  # type: ignore[arg-type]
    assert ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_channel_at_string_int_coerces(ent):
    body = ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, "5")  # type: ignore[arg-type]
    assert body is not None
    assert body["item"] == 5


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_retention_window_at
# ══════════════════════════════════════════════════════════════════════════════


def test_retention_at_returns_full_shape(ent):
    body = ent.tiers_for_retention_window_at(ent.TIER_CLOUD_STARTER, 30)
    assert body is not None
    assert set(body.keys()) == _ROW_KEYS
    assert body["kind"] == "retention_window"
    assert body["item"] == 30


def test_retention_at_unlimited_accepted(ent):
    """``days=None`` on the singular helper means "unlimited" -- the
    ``_at`` sibling must preserve that sentinel through the delegate."""
    body = ent.tiers_for_retention_window_at(ent.TIER_CLOUD_STARTER, None)
    assert body is not None
    assert body["item"] is None
    assert body["label"] == "unlimited"


def test_retention_at_byte_parity_across_perspectives(ent):
    for d in (-3, 0, 1, 7, 8, 30, 90, 365, None):
        base = ent.tiers_for_retention_window(d)
        for p in ent._TIER_ORDER:
            assert ent.tiers_for_retention_window_at(p, d) == base, (p, d)


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier"])
def test_retention_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_retention_window_at(bad, 30) is None


def test_retention_at_none_perspective_returns_none(ent):
    assert ent.tiers_for_retention_window_at(None, 30) is None  # type: ignore[arg-type]


def test_retention_at_trial_perspective_accepted(ent):
    assert (
        ent.tiers_for_retention_window_at(ent.TIER_TRIAL, 30)
        is not None
    )


def test_retention_at_non_int_days_returns_none(ent):
    assert (
        ent.tiers_for_retention_window_at(ent.TIER_CLOUD_PRO, "nope")  # type: ignore[arg-type]
        is None
    )


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_node_count_at
# ══════════════════════════════════════════════════════════════════════════════


def test_node_at_returns_full_shape(ent):
    body = ent.tiers_for_node_count_at(ent.TIER_CLOUD_STARTER, 4)
    assert body is not None
    assert set(body.keys()) == _ROW_KEYS
    assert body["kind"] == "node_count"
    assert body["item"] == 4


def test_node_at_byte_parity_across_perspectives(ent):
    for n in (-3, 0, 1, 4, 10, 100, 10_000):
        base = ent.tiers_for_node_count(n)
        for p in ent._TIER_ORDER:
            assert ent.tiers_for_node_count_at(p, n) == base, (p, n)


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier"])
def test_node_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_node_count_at(bad, 4) is None


def test_node_at_none_perspective_returns_none(ent):
    assert ent.tiers_for_node_count_at(None, 4) is None  # type: ignore[arg-type]


def test_node_at_trial_perspective_accepted(ent):
    assert ent.tiers_for_node_count_at(ent.TIER_TRIAL, 4) is not None


def test_node_at_non_int_returns_none(ent):
    assert ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, "nope") is None  # type: ignore[arg-type]
    assert ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


# ══════════════════════════════════════════════════════════════════════════════
#   tiers_for_capacity_batch_at
# ══════════════════════════════════════════════════════════════════════════════


def test_capacity_batch_at_returns_all_axes(ent):
    body = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_STARTER, channels=5, retention_days=30, nodes=4
    )
    assert body is not None
    assert set(body.keys()) == {"channels", "retention_days", "nodes"}
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None


def test_capacity_batch_at_omits_axis_when_unset(ent):
    body = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_STARTER, channels=5
    )
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_capacity_batch_at_retention_none_means_unset_not_unlimited(ent):
    """Critical: ``retention_days=None`` here is *unset*, NOT
    *unlimited*. If it silently mapped to unlimited a caller supplying
    every axis but leaving retention off would get a mis-routed
    Enterprise row instead of an omitted one -- matches
    ``tiers_for_capacity_batch`` on the same axis. The singular
    ``tiers_for_retention_window_at(p, None)`` call is how a caller
    asks for the unlimited-retention ladder."""
    body = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_STARTER, retention_days=None
    )
    assert body["retention_days"] is None


def test_capacity_batch_at_byte_parity_across_perspectives(ent):
    combos = [
        {"channels": 5},
        {"retention_days": 30},
        {"nodes": 4},
        {"channels": 5, "retention_days": 30, "nodes": 4},
        {"channels": 0, "retention_days": 7, "nodes": 1},
        {"channels": 10_000, "nodes": 10_000},
    ]
    for kwargs in combos:
        base = ent.tiers_for_capacity_batch(**kwargs)
        for p in ent._TIER_ORDER:
            assert (
                ent.tiers_for_capacity_batch_at(p, **kwargs) == base
            ), (p, kwargs)


@pytest.mark.parametrize("bad", ["", "   ", "bogus_tier"])
def test_capacity_batch_at_bad_perspective_returns_none(ent, bad):
    assert (
        ent.tiers_for_capacity_batch_at(bad, channels=5) is None
    )


def test_capacity_batch_at_none_perspective_returns_none(ent):
    assert (
        ent.tiers_for_capacity_batch_at(None, channels=5) is None  # type: ignore[arg-type]
    )


def test_capacity_batch_at_non_string_perspective_returns_none(ent):
    assert (
        ent.tiers_for_capacity_batch_at(42, channels=5) is None  # type: ignore[arg-type]
    )


def test_capacity_batch_at_trial_accepted(ent):
    assert (
        ent.tiers_for_capacity_batch_at(ent.TIER_TRIAL, channels=5)
        is not None
    )


def test_capacity_batch_at_case_insensitive(ent):
    upper = ent.TIER_CLOUD_PRO.upper()
    assert (
        ent.tiers_for_capacity_batch_at(upper, channels=5)
        == ent.tiers_for_capacity_batch(channels=5)
    )


# ── grace vs enforce (every helper) ──────────────────────────────────────────


def test_grace_vs_enforce_byte_identical_channel(monkeypatch, ent):
    grace = ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, 5)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, 5)
    assert grace == enforced


def test_grace_vs_enforce_byte_identical_retention(monkeypatch, ent):
    grace = ent.tiers_for_retention_window_at(ent.TIER_CLOUD_PRO, 30)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tiers_for_retention_window_at(ent.TIER_CLOUD_PRO, 30)
    assert grace == enforced


def test_grace_vs_enforce_byte_identical_node(monkeypatch, ent):
    grace = ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, 4)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, 4)
    assert grace == enforced


def test_grace_vs_enforce_byte_identical_capacity_batch(monkeypatch, ent):
    grace = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_PRO, channels=5, retention_days=30, nodes=4
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_PRO, channels=5, retention_days=30, nodes=4
    )
    assert grace == enforced


# ── never raises / no live-entitlement mutation ──────────────────────────────


def test_channel_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_channel_count", boom)
    assert (
        ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, 5) is None
    )


def test_retention_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_retention_window", boom)
    assert (
        ent.tiers_for_retention_window_at(ent.TIER_CLOUD_PRO, 30) is None
    )


def test_node_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_node_count", boom)
    assert ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, 4) is None


def test_capacity_batch_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_capacity_batch", boom)
    body = ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_PRO, channels=5, retention_days=30, nodes=4
    )
    # graceful fallback: all-None envelope, still a dict
    assert body == {
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_channel_count_at(ent.TIER_CLOUD_PRO, 5)
    ent.tiers_for_retention_window_at(ent.TIER_CLOUD_PRO, 30)
    ent.tiers_for_node_count_at(ent.TIER_CLOUD_PRO, 4)
    ent.tiers_for_capacity_batch_at(
        ent.TIER_CLOUD_PRO, channels=5, retention_days=30, nodes=4
    )
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ══════════════════════════════════════════════════════════════════════════════
#   HTTP: /api/entitlement/tiers-for-channel-count-at
# ══════════════════════════════════════════════════════════════════════════════


def test_api_channel_at_returns_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_STARTER}&count=5"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "channel_count"
    assert body["item"] == 5


def test_api_channel_at_carries_perspective_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO}&count=5"
    )
    body = rv.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["perspective_tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["perspective_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_api_channel_at_carries_resolver_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO}&count=5"
    )
    body = rv.get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_api_channel_at_case_insensitive_tier(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO.upper()}&count=5"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_api_channel_at_trial_perspective_accepted(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_TRIAL}&count=5"
    )
    assert rv.status_code == 200


def test_api_channel_at_missing_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-channel-count-at?count=5"
    )
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_channel_at_blank_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-channel-count-at?tier=&count=5"
    )
    assert rv.status_code == 400


def test_api_channel_at_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-channel-count-at?tier=bogus_tier&count=5"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_tier"


def test_api_channel_at_missing_count_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 400


def test_api_channel_at_blank_count_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO}&count="
    )
    assert rv.status_code == 400


def test_api_channel_at_non_int_count_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-channel-count-at?tier={ent.TIER_CLOUD_PRO}&count=nope"
    )
    assert rv.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#   HTTP: /api/entitlement/tiers-for-retention-window-at
# ══════════════════════════════════════════════════════════════════════════════


def test_api_retention_at_returns_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}&days=30"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "retention_window"
    assert body["item"] == 30


def test_api_retention_at_unlimited(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}&days=unlimited"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["item"] is None
    assert body["label"] == "unlimited"


def test_api_retention_at_unlimited_case_insensitive(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}&days=Unlimited"
    )
    assert rv.status_code == 200
    assert rv.get_json()["item"] is None


def test_api_retention_at_missing_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window-at?days=30"
    )
    assert rv.status_code == 400


def test_api_retention_at_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-retention-window-at?tier=bogus_tier&days=30"
    )
    assert rv.status_code == 404


def test_api_retention_at_missing_days_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 400


def test_api_retention_at_blank_days_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}&days="
    )
    assert rv.status_code == 400


def test_api_retention_at_non_int_days_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-retention-window-at?tier={ent.TIER_CLOUD_PRO}&days=forever"
    )
    assert rv.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#   HTTP: /api/entitlement/tiers-for-node-count-at
# ══════════════════════════════════════════════════════════════════════════════


def test_api_node_at_returns_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-node-count-at?tier={ent.TIER_CLOUD_PRO}&count=4"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "node_count"
    assert body["item"] == 4


def test_api_node_at_missing_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-node-count-at?count=4"
    )
    assert rv.status_code == 400


def test_api_node_at_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-node-count-at?tier=bogus_tier&count=4"
    )
    assert rv.status_code == 404


def test_api_node_at_missing_count_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-node-count-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 400


def test_api_node_at_non_int_count_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-node-count-at?tier={ent.TIER_CLOUD_PRO}&count=nope"
    )
    assert rv.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#   HTTP: /api/entitlement/tiers-for-capacity-batch-at
# ══════════════════════════════════════════════════════════════════════════════


def test_api_capacity_batch_at_shape(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_CLOUD_PRO}&channels=5&retention_days=30&nodes=4"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == (
        {"channels", "retention_days", "nodes"} | _ENVELOPE_KEYS
    )
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_api_capacity_batch_at_omits_axis(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_CLOUD_PRO}&channels=5"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_api_capacity_batch_at_missing_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch-at?channels=5"
    )
    assert rv.status_code == 400


def test_api_capacity_batch_at_blank_tier_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch-at?tier=&channels=5"
    )
    assert rv.status_code == 400


def test_api_capacity_batch_at_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-capacity-batch-at?tier=bogus_tier&channels=5"
    )
    assert rv.status_code == 404


def test_api_capacity_batch_at_no_axis_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 400


def test_api_capacity_batch_at_all_axes_bogus_is_400(client, ent):
    """Matches ``/tiers-for-capacity-batch`` never-mis-route posture --
    every axis unparseable is caller error, not a mis-routed Enterprise
    ladder."""
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_CLOUD_PRO}&channels=nope&retention_days=nope&nodes=nope"
    )
    assert rv.status_code == 400


def test_api_capacity_batch_at_trial_accepted(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_TRIAL}&channels=5"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_TRIAL


def test_api_capacity_batch_at_case_insensitive_tier(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-capacity-batch-at?tier={ent.TIER_CLOUD_PRO.upper()}&channels=5"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_CLOUD_PRO


# ══════════════════════════════════════════════════════════════════════════════
#   Cross-endpoint parity
# ══════════════════════════════════════════════════════════════════════════════


def test_api_channel_at_rows_byte_equal_non_at(client, ent):
    """For every ``p``, ``/tiers-for-channel-count-at?tier=<p>&count=<n>``
    returns the same core row shape as ``/tiers-for-channel-count?count=<n>``
    (minus the perspective envelope keys). Pins the ``_at`` endpoint
    against silently shaping rows."""
    base = client.get(
        "/api/entitlement/tiers-for-channel-count?count=5"
    ).get_json()
    # strip resolver envelope from base for comparison
    base_core = {
        k: v
        for k, v in base.items()
        if k not in _ENVELOPE_KEYS
    }
    for p in ent._TIER_ORDER:
        rv = client.get(
            f"/api/entitlement/tiers-for-channel-count-at?tier={p}&count=5"
        )
        assert rv.status_code == 200, p
        body = rv.get_json()
        core = {k: v for k, v in body.items() if k not in _ENVELOPE_KEYS}
        assert core == base_core, p


def test_api_retention_at_rows_byte_equal_non_at(client, ent):
    base = client.get(
        "/api/entitlement/tiers-for-retention-window?days=30"
    ).get_json()
    base_core = {
        k: v
        for k, v in base.items()
        if k not in _ENVELOPE_KEYS
    }
    for p in ent._TIER_ORDER:
        rv = client.get(
            f"/api/entitlement/tiers-for-retention-window-at?tier={p}&days=30"
        )
        assert rv.status_code == 200, p
        body = rv.get_json()
        core = {k: v for k, v in body.items() if k not in _ENVELOPE_KEYS}
        assert core == base_core, p


def test_api_node_at_rows_byte_equal_non_at(client, ent):
    base = client.get(
        "/api/entitlement/tiers-for-node-count?count=4"
    ).get_json()
    base_core = {
        k: v
        for k, v in base.items()
        if k not in _ENVELOPE_KEYS
    }
    for p in ent._TIER_ORDER:
        rv = client.get(
            f"/api/entitlement/tiers-for-node-count-at?tier={p}&count=4"
        )
        assert rv.status_code == 200, p
        body = rv.get_json()
        core = {k: v for k, v in body.items() if k not in _ENVELOPE_KEYS}
        assert core == base_core, p


def test_api_capacity_batch_at_rows_byte_equal_non_at(client, ent):
    base = client.get(
        "/api/entitlement/tiers-for-capacity-batch?channels=5&retention_days=30&nodes=4"
    ).get_json()
    for p in ent._TIER_ORDER:
        rv = client.get(
            f"/api/entitlement/tiers-for-capacity-batch-at?tier={p}&channels=5&retention_days=30&nodes=4"
        )
        assert rv.status_code == 200, p
        body = rv.get_json()
        for axis in ("channels", "retention_days", "nodes"):
            assert body[axis] == base[axis], (p, axis)
