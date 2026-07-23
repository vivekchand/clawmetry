"""Tests for the ``_at`` variants of the scalar capacity-axis
``min-tier-for-<axis>`` endpoints:

* ``/api/entitlement/min-tier-for-channel-count-at``
* ``/api/entitlement/min-tier-for-node-count-at``
* ``/api/entitlement/min-tier-for-retention-window-at``

Fills the ``_at`` slot for the three scalar capacity axes alongside
``/min-tier-for-features-at`` / ``/min-tier-for-runtimes-at`` so a
pricing-matrix walkthrough (``?tier=<p>``) can hit every scalar
``min-tier-for-*`` axis uniformly at a fixed perspective. Wraps the new
:func:`clawmetry.entitlements.min_tier_for_channel_count_at` /
:func:`clawmetry.entitlements.min_tier_for_node_count_at` /
:func:`clawmetry.entitlements.min_tier_for_retention_window_at` helpers
so the ``_at`` family is uniform.

These tests pin:

* API happy path: shape, perspective envelope, resolver envelope
* API error paths: 400 on missing / blank / non-int, 404 on unknown tier
* perspective-independence parity: the ``_at`` answer byte-equals the
  bare helper's answer for every ``perspective_tier`` in
  ``_TIER_ORDER`` (the ``_at`` prefix must not shape rows)
* helper-side parity: the ``_at`` helper byte-equals the bare helper
* ``days=unlimited`` (case-insensitive) round-trips to ``item=null`` /
  ``label="unlimited"``
* zero / negative collapse to the free floor (parity with bare)
* uniform envelope keys across the three ``_at`` axes
* never-5xxs on a delegate crash
* grace vs enforce parity: the resolver-scoped body must not drift
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


_AT_ENVELOPE_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── helper-side: perspective-independence parity ──────────────────────────


@pytest.mark.parametrize("count", [1, 3, 5, 50, 1000])
def test_helper_channel_count_at_matches_bare_for_every_perspective(
    ent, count
):
    bare = ent.min_tier_for_channel_count(count)
    for p in ent._TIER_ORDER:
        assert ent.min_tier_for_channel_count_at(p, count) == bare, (
            f"drift at perspective {p!r}"
        )


@pytest.mark.parametrize("count", [1, 3, 5, 50, 1000])
def test_helper_node_count_at_matches_bare_for_every_perspective(ent, count):
    bare = ent.min_tier_for_node_count(count)
    for p in ent._TIER_ORDER:
        assert ent.min_tier_for_node_count_at(p, count) == bare, (
            f"drift at perspective {p!r}"
        )


@pytest.mark.parametrize("days", [1, 7, 30, 90, 365, None])
def test_helper_retention_window_at_matches_bare_for_every_perspective(
    ent, days
):
    bare = ent.min_tier_for_retention_window(days)
    for p in ent._TIER_ORDER:
        assert ent.min_tier_for_retention_window_at(p, days) == bare, (
            f"drift at perspective {p!r} days={days!r}"
        )


# ── helper-side: invalid perspective / bad input ──────────────────────────


def test_helper_channel_count_at_unknown_perspective_returns_none(ent):
    assert ent.min_tier_for_channel_count_at("bogus", 5) is None
    assert ent.min_tier_for_channel_count_at("", 5) is None
    assert ent.min_tier_for_channel_count_at(None, 5) is None


def test_helper_node_count_at_unknown_perspective_returns_none(ent):
    assert ent.min_tier_for_node_count_at("bogus", 5) is None
    assert ent.min_tier_for_node_count_at(None, 5) is None


def test_helper_retention_window_at_unknown_perspective_returns_none(ent):
    assert ent.min_tier_for_retention_window_at("bogus", 30) is None
    assert ent.min_tier_for_retention_window_at("bogus", None) is None


def test_helper_channel_count_at_nonint_count_returns_none(ent):
    assert ent.min_tier_for_channel_count_at("cloud_pro", "nope") is None


def test_helper_retention_window_at_nonint_days_returns_none(ent):
    assert ent.min_tier_for_retention_window_at("cloud_pro", "nope") is None


# ── API: happy path ────────────────────────────────────────────────────────


def test_api_channel_count_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["kind"] == "channel_count"
    assert j["item"] == 5
    assert j["label"] == "5 channels"
    assert j["required_tier"] == ent.min_tier_for_channel_count(5)
    assert j["perspective_tier"] == "cloud_pro"
    assert j["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_pro")


def test_api_node_count_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        "?tier=cloud_starter&count=4"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["kind"] == "node_count"
    assert j["item"] == 4
    assert j["label"] == "4 nodes"
    assert j["required_tier"] == ent.min_tier_for_node_count(4)
    assert j["perspective_tier"] == "cloud_starter"


def test_api_retention_window_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=enterprise&days=30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["kind"] == "retention_window"
    assert j["item"] == 30
    assert j["label"] == "30 days"
    assert j["required_tier"] == ent.min_tier_for_retention_window(30)
    assert j["perspective_tier"] == "enterprise"


# ── API: singular label conjugation ───────────────────────────────────────


def test_api_channel_count_at_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=1"
    ).get_json()
    assert j["label"] == "1 channel"


def test_api_node_count_at_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        "?tier=cloud_pro&count=1"
    ).get_json()
    assert j["label"] == "1 node"


def test_api_retention_window_at_singular_label(client):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=1"
    ).get_json()
    assert j["label"] == "1 day"


# ── API: error paths ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count-at?count=5",
        "/api/entitlement/min-tier-for-node-count-at?count=4",
        "/api/entitlement/min-tier-for-retention-window-at?days=30",
    ],
)
def test_api_at_missing_tier_returns_400(client, url):
    r = client.get(url)
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing tier"


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count-at?tier=&count=5",
        "/api/entitlement/min-tier-for-node-count-at?tier=%20%20&count=4",
    ],
)
def test_api_at_blank_tier_returns_400(client, url):
    r = client.get(url)
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing tier"


def test_api_channel_count_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=bogus&count=5"
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j.get("which") == "tier"
    assert j.get("tier") == "bogus"


def test_api_node_count_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-at?tier=bogus&count=4"
    )
    assert r.status_code == 404
    assert r.get_json().get("which") == "tier"


def test_api_retention_window_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=bogus&days=30"
    )
    assert r.status_code == 404
    assert r.get_json().get("which") == "tier"


def test_api_channel_count_at_missing_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at?tier=cloud_pro"
    )
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing count"


def test_api_channel_count_at_blank_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=%20%20"
    )
    assert r.status_code == 400


def test_api_channel_count_at_nonint_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=nope"
    )
    assert r.status_code == 400
    assert "integer" in r.get_json().get("error", "")


def test_api_node_count_at_missing_count_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-at?tier=cloud_pro"
    )
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing count"


def test_api_retention_window_at_missing_days_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at?tier=cloud_pro"
    )
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing days"


def test_api_retention_window_at_nonint_days_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=nope"
    )
    assert r.status_code == 400


# ── API: retention `unlimited` handling ───────────────────────────────────


def test_api_retention_window_at_unlimited(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=unlimited"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["item"] is None
    assert j["label"] == "unlimited"
    assert j["kind"] == "retention_window"
    assert j["required_tier"] == ent.min_tier_for_retention_window(None)
    assert j["perspective_tier"] == "cloud_pro"


def test_api_retention_window_at_unlimited_case_insensitive(client):
    for spelling in ("Unlimited", "UNLIMITED", "unLimIted"):
        j = client.get(
            "/api/entitlement/min-tier-for-retention-window-at"
            f"?tier=cloud_pro&days={spelling}"
        ).get_json()
        assert j["item"] is None
        assert j["label"] == "unlimited"


# ── API: zero / negative collapses to free floor (parity with bare) ───────


def test_api_channel_count_at_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


def test_api_node_count_at_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        "?tier=cloud_pro&count=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


def test_api_retention_window_at_zero_is_free(client, ent):
    j = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=0"
    ).get_json()
    assert j["required_tier"] == ent.TIER_OSS
    assert j["free"] is True


# ── API: cross-endpoint parity with bare ──────────────────────────────────


@pytest.mark.parametrize("n", [1, 3, 10, 50, 1000])
def test_api_channel_count_at_matches_bare(client, ent, n):
    bare = client.get(
        f"/api/entitlement/min-tier-for-channel-count?count={n}"
    ).get_json()
    at = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        f"?tier=cloud_pro&count={n}"
    ).get_json()
    # answer axis must not depend on perspective
    for k in ("required_tier", "required_tier_label", "required_tier_rank",
              "free", "kind", "item", "label"):
        assert bare[k] == at[k], f"key {k} drifted"


@pytest.mark.parametrize("n", [1, 3, 10, 50, 1000])
def test_api_node_count_at_matches_bare(client, ent, n):
    bare = client.get(
        f"/api/entitlement/min-tier-for-node-count?count={n}"
    ).get_json()
    at = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        f"?tier=cloud_pro&count={n}"
    ).get_json()
    for k in ("required_tier", "required_tier_label", "required_tier_rank",
              "free", "kind", "item", "label"):
        assert bare[k] == at[k], f"key {k} drifted"


@pytest.mark.parametrize("d", [1, 7, 30, 90, 365])
def test_api_retention_window_at_matches_bare(client, ent, d):
    bare = client.get(
        f"/api/entitlement/min-tier-for-retention-window?days={d}"
    ).get_json()
    at = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        f"?tier=cloud_pro&days={d}"
    ).get_json()
    for k in ("required_tier", "required_tier_label", "required_tier_rank",
              "free", "kind", "item", "label"):
        assert bare[k] == at[k], f"key {k} drifted"


# ── API: uniform envelope across the three `_at` axes ─────────────────────


def test_api_three_at_axes_share_envelope_keys(client):
    ch = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=5"
    ).get_json()
    nd = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        "?tier=cloud_pro&count=4"
    ).get_json()
    rw = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=30"
    ).get_json()
    assert set(ch.keys()) == set(nd.keys()) == set(rw.keys()) == (
        _AT_ENVELOPE_KEYS
    )


# ── API: perspective envelope carried ─────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count-at?tier=cloud_pro&count=5",
        "/api/entitlement/min-tier-for-node-count-at?tier=cloud_pro&count=4",
        "/api/entitlement/min-tier-for-retention-window-at?tier=cloud_pro&days=30",
    ],
)
def test_api_at_carries_perspective_envelope(client, ent, url):
    j = client.get(url).get_json()
    assert j["perspective_tier"] == "cloud_pro"
    assert j["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_pro")


# ── API: perspective-independence across every tier ──────────────────────


@pytest.mark.parametrize("perspective", ["oss", "cloud_starter", "cloud_pro",
                                          "enterprise", "trial"])
def test_api_channel_count_at_answer_independent_of_perspective(
    client, ent, perspective
):
    bare = client.get(
        "/api/entitlement/min-tier-for-channel-count?count=5"
    ).get_json()
    at = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        f"?tier={perspective}&count=5"
    ).get_json()
    assert at["required_tier"] == bare["required_tier"]
    assert at["perspective_tier"] == perspective


# ── API: resolver envelope carried on happy path ─────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/min-tier-for-channel-count-at?tier=cloud_pro&count=5",
        "/api/entitlement/min-tier-for-node-count-at?tier=cloud_pro&count=4",
        "/api/entitlement/min-tier-for-retention-window-at?tier=cloud_pro&days=30",
    ],
)
def test_api_at_carries_resolver_envelope(client, url):
    j = client.get(url).get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


# ── API: never-5xxs on a delegate crash ───────────────────────────────────


def test_api_channel_count_at_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_channel_count_at", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-channel-count-at"
        "?tier=cloud_pro&count=5"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 5
    assert j["kind"] == "channel_count"
    assert j["perspective_tier"] == "cloud_pro"


def test_api_node_count_at_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_node_count_at", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-node-count-at"
        "?tier=cloud_pro&count=4"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 4
    assert j["kind"] == "node_count"


def test_api_retention_window_at_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_retention_window_at", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=30"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["item"] == 30
    assert j["kind"] == "retention_window"


def test_api_retention_window_at_unlimited_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_retention_window_at", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at"
        "?tier=cloud_pro&days=unlimited"
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
        "/api/entitlement/min-tier-for-channel-count-at?tier=cloud_pro&count=5",
        "/api/entitlement/min-tier-for-node-count-at?tier=cloud_pro&count=4",
        "/api/entitlement/min-tier-for-retention-window-at?tier=cloud_pro&days=30",
    ],
)
def test_api_at_grace_vs_enforce_identical(client, ent, monkeypatch, url):
    grace = client.get(url).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.get(url).get_json()
    # The pricing-surface fields (item / kind / label / required_tier /
    # free / perspective_tier) must byte-equal between grace and enforce:
    # enforcement is a gating concern, not a description concern.
    for k in ("item", "kind", "label", "required_tier", "free",
              "perspective_tier"):
        assert grace[k] == enforce[k], (
            f"key {k} drifted grace vs enforce"
        )
