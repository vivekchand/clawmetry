"""Tests for the bare ``/api/entitlement/min-tier-for-channel-count`` /
``/api/entitlement/min-tier-for-node-count`` /
``/api/entitlement/min-tier-for-retention-window`` endpoints.

Fills the *bare* slot for the three scalar capacity-axis
``min_tier_for_*`` helpers alongside the ladder-axis siblings
``/api/entitlement/tiers-for-channel-count`` /
``/tiers-for-node-count`` / ``/tiers-for-retention-window`` (which return
the full "Fits in: <tier>, ..." availability list) and the plural grant-
axis bare endpoints ``/min-tier-for-features`` / ``/min-tier-for-runtimes``
(#3734). Wraps the existing
:func:`clawmetry.entitlements.min_tier_for_channel_count` /
:func:`clawmetry.entitlements.min_tier_for_node_count` /
:func:`clawmetry.entitlements.min_tier_for_retention_window` helpers so
the three scalar capacity axes look identical from the caller's side.

These tests pin:

* API happy path: shape, resolver envelope, ``kind``, ``item``, ``label``,
  ``free``
* API error paths: 400 on missing / blank / non-int ``count`` / ``days``
* cross-endpoint parity: ``required_tier`` byte-equals the helper's return
* ``days=unlimited`` (case-insensitive) round-trips to ``item=null`` /
  ``label="unlimited"`` and required_tier=None-cap tier
* symmetry across the three axes: identical envelope shape
* uniform ``required_tier*`` naming with the plural grant-axis siblings
  so a UI switching axes reads the same envelope
* resolver envelope carried on happy path
* never-5xxs on a delegate crash
* grace vs enforce parity: the resolver-scoped body must not drift
  between grace and enforce modes
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


_BARE_ENVELOPE_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── API: happy path ────────────────────────────────────────────────────────


def test_api_channel_count_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _BARE_ENVELOPE_KEYS
    assert j["kind"] == "channel_count"
    assert j["item"] == 5
    assert j["label"] == "5 channels"
    assert j["required_tier"] == ent.min_tier_for_channel_count(5)
    assert j["required_tier_label"] == ent.tier_label(j["required_tier"])
    assert j["required_tier_rank"] == ent.tier_rank(j["required_tier"])


def test_api_node_count_happy_path(client, ent):
    r = client.get("/api/entitlement/min-tier-for-node-count?count=4")
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _BARE_ENVELOPE_KEYS
    assert j["kind"] == "node_count"
    assert j["item"] == 4
    assert j["label"] == "4 nodes"
    assert j["required_tier"] == ent.min_tier_for_node_count(4)


def test_api_retention_window_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _BARE_ENVELOPE_KEYS
    assert j["kind"] == "retention_window"
    assert j["item"] == 30
    assert j["label"] == "30 days"
    assert j["required_tier"] == ent.min_tier_for_retention_window(30)


# ── API: singular label conjugation ───────────────────────────────────────


def test_api_channel_count_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=1"
    ).get_json()
    assert j["label"] == "1 channel"


def test_api_node_count_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-node-count?count=1"
    ).get_json()
    assert j["label"] == "1 node"


def test_api_retention_window_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=1"
    ).get_json()
    assert j["label"] == "1 day"


# ── API: error paths ──────────────────────────────────────────────────────


def test_api_channel_count_missing_count_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-channel-count")
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing count"


def test_api_node_count_missing_count_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-node-count")
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing count"


def test_api_retention_window_missing_days_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-retention-window")
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing days"


def test_api_channel_count_blank_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=%20%20"
    )
    assert r.status_code == 400


def test_api_node_count_blank_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count?count=%20%20"
    )
    assert r.status_code == 400


def test_api_retention_window_blank_days_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=%20%20"
    )
    assert r.status_code == 400


def test_api_channel_count_nonint_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=nope"
    )
    assert r.status_code == 400
    assert "integer" in r.get_json().get("error", "")


def test_api_node_count_nonint_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count?count=nope"
    )
    assert r.status_code == 400


def test_api_retention_window_nonint_days_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=nope"
    )
    assert r.status_code == 400
    assert (
        "integer" in r.get_json().get("error", "")
        or "unlimited" in r.get_json().get("error", "")
    )


# ── API: retention `unlimited` handling ───────────────────────────────────


def test_api_retention_window_unlimited(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=unlimited"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["item"] is None
    assert j["label"] == "unlimited"
    assert j["kind"] == "retention_window"
    assert j["required_tier"] == ent.min_tier_for_retention_window(None)


def test_api_retention_window_unlimited_case_insensitive(client, ent):
    for spelling in ("Unlimited", "UNLIMITED", "unLimIted"):
        j = client.get(
            f"/api/entitlement/min-tier-for-retention-window?days={spelling}"
        ).get_json()
        assert j["item"] is None
        assert j["label"] == "unlimited"


# ── API: zero / negative collapses to free floor ──────────────────────────


def test_api_channel_count_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


def test_api_node_count_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-node-count?count=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


def test_api_retention_window_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


# ── API: cross-endpoint parity with helper ────────────────────────────────


@pytest.mark.parametrize("n", [1, 3, 10, 50, 1000])
def test_api_channel_count_required_tier_byte_equals_helper(
    client, ent, n
):
    j = client.get(
        f"/api/entitlement/min-tier-for-channel-count?count={n}"
    ).get_json()
    assert j["required_tier"] == ent.min_tier_for_channel_count(n)


@pytest.mark.parametrize("n", [1, 3, 10, 50, 1000])
def test_api_node_count_required_tier_byte_equals_helper(client, ent, n):
    j = client.get(
        f"/api/entitlement/min-tier-for-node-count?count={n}"
    ).get_json()
    assert j["required_tier"] == ent.min_tier_for_node_count(n)


@pytest.mark.parametrize("d", [1, 7, 30, 90, 365])
def test_api_retention_window_required_tier_byte_equals_helper(
    client, ent, d
):
    j = client.get(
        f"/api/entitlement/min-tier-for-retention-window?days={d}"
    ).get_json()
    assert j["required_tier"] == ent.min_tier_for_retention_window(d)


# ── API: uniform envelope across the three scalar capacity axes ──────────


def test_api_three_axes_share_envelope_keys(client):
    """A paywall UI switching capacity axes reads the same envelope --
    pin that the three scalar min-tier-for-<axis> bodies expose the
    same key set so no axis leaks a different shape."""
    ch = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=5"
    ).get_json()
    nd = client.get(
        "/api/entitlement/min-tier-for-node-count?count=4"
    ).get_json()
    rw = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=30"
    ).get_json()
    assert set(ch.keys()) == set(nd.keys()) == set(rw.keys()) == (
        _BARE_ENVELOPE_KEYS
    )


def test_api_capacity_axes_share_envelope_with_grant_axes(client):
    """The three scalar capacity axes must expose the same
    ``required_tier*`` naming as the plural grant-axis siblings
    (``/min-tier-for-features``/``/min-tier-for-runtimes``) so the
    ``min_tier_for_*`` HTTP family is uniform. Pins that the naming
    (``required_tier`` / ``required_tier_label`` / ``required_tier_rank``)
    is not axis-specific."""
    grant = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet"
    ).get_json()
    ch = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=5"
    ).get_json()
    shared = {
        "kind",
        "free",
        "required_tier",
        "required_tier_label",
        "required_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert shared <= set(grant.keys())
    assert shared <= set(ch.keys())


# ── API: resolver envelope carried ────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count?count=5",
        "/api/entitlement/min-tier-for-node-count?count=4",
        "/api/entitlement/min-tier-for-retention-window?days=30",
    ],
)
def test_api_carries_resolver_envelope(client, url):
    j = client.get(url).get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


# ── API: never-5xxs on a delegate crash ───────────────────────────────────


def test_api_channel_count_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_channel_count", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 5
    assert j["kind"] == "channel_count"


def test_api_node_count_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_node_count", _boom)
    r = client.get("/api/entitlement/min-tier-for-node-count?count=4")
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 4
    assert j["kind"] == "node_count"


def test_api_retention_window_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_retention_window", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 30
    assert j["kind"] == "retention_window"


def test_api_retention_window_unlimited_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_retention_window", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window?days=unlimited"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] is None
    assert j["kind"] == "retention_window"


# ── grace vs enforce parity ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count?count=5",
        "/api/entitlement/min-tier-for-node-count?count=4",
        "/api/entitlement/min-tier-for-retention-window?days=30",
    ],
)
def test_api_grace_vs_enforce_identical(client, ent, monkeypatch, url):
    grace = client.get(url).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.get(url).get_json()
    # The pricing-surface fields (item / kind / label / required_tier /
    # free) must byte-equal between grace and enforce: enforcement is a
    # gating concern, not a description concern.
    for k in ("item", "kind", "label", "required_tier", "free"):
        assert grace[k] == enforce[k], (
            f"key {k} drifted grace vs enforce"
        )
