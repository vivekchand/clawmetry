"""Contract-lock tests for the ``/api/entitlement`` fallback shape.

The route in :mod:`routes.entitlement` guards ``get_entitlement()`` with a
``try/except`` so a resolver hiccup can never take down the paywall UI. Before
this test file, the ``except`` branch returned a hand-rolled dict that had
drifted from the healthy ``Entitlement.to_dict()`` shape: it was missing
``free_runtimes`` / ``paid_runtimes`` / ``all_runtimes`` / ``channel_limit`` /
``next_tier_capacity_diff`` / ``next_tier_locks`` / ``prev_tier_locks`` /
``effective_retention_days`` / ``days_until_expiry`` / ``next_tier`` /
``next_tier_label`` / ``prev_tier`` / ``prev_tier_label``, and carried
``features: []`` instead of the 12-item ``FREE_FEATURES`` set the healthy path
returns.

The consequence: a caller reading ``data.features`` (say, a paywall UI
deciding which cards to render) sees the 12 free features in the healthy
path but an empty list on any transient failure -- which once enforcement
is live would render as "OSS install has no free features, lock everything".
That silent contract flip is exactly what these tests pin down.

The tests exercise three layers of fallback:

1. Happy path -- ``get_entitlement()`` returns the healthy shape.
2. Resolver crash -- ``get_entitlement`` raises, route falls to
   ``_oss_free().to_dict()``. Body shape and ``features`` set must match the
   healthy OSS-free path exactly.
3. Total-module failure -- both the resolver AND ``_oss_free`` raise. Route
   falls to the in-line ``_MINIMAL_OSS_FREE_SNAPSHOT``. Body still carries
   the same TOP-LEVEL KEYS so downstream ``data.<key>`` reads never KeyError.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app_and_module(monkeypatch, tmp_path):
    """Flask app + freshly-reloaded entitlements module with a clean HOME.

    Reloads the entitlements module so any stale enforcement env from a
    previous test in the same worker does not bleed in, then mints the
    Blueprint fresh so the fixture never returns a client bound to a
    stale monkeypatch.
    """
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client(), e


# ── canonical shape ───────────────────────────────────────────────────────────


def _healthy_body(app_and_module):
    client, _ = app_and_module
    resp = client.get("/api/entitlement")
    assert resp.status_code == 200
    return resp.get_json()


def test_healthy_body_carries_all_documented_top_level_keys(app_and_module):
    """Anchor: the healthy path returns the full ``to_dict`` shape."""
    body = _healthy_body(app_and_module)
    for key in (
        "tier",
        "tier_label",
        "tier_rank",
        "source",
        "node_limit",
        "channel_limit",
        "expiry",
        "expired",
        "days_until_expiry",
        "is_paid",
        "grace",
        "enforced",
        "enforce_at",
        "enforce_at_iso",
        "days_until_enforce",
        "retention_days",
        "effective_retention_days",
        "runtimes",
        "features",
        "free_runtimes",
        "paid_runtimes",
        "all_runtimes",
        "locked_runtimes",
        "locked_features",
        "next_tier",
        "next_tier_label",
        "prev_tier",
        "prev_tier_label",
        "next_tier_diff",
        "prev_tier_diff",
        "next_tier_capacity_diff",
        "prev_tier_capacity_diff",
        "next_tier_unlocks",
        "prev_tier_unlocks",
        "next_tier_locks",
        "prev_tier_locks",
    ):
        assert key in body, key


def test_healthy_body_features_matches_free_features(app_and_module):
    """Healthy OSS-free response lists sorted FREE_FEATURES, not an empty set."""
    body = _healthy_body(app_and_module)
    _, ent_mod = app_and_module
    assert set(body["features"]) == set(ent_mod.FREE_FEATURES)
    assert body["features"] == sorted(ent_mod.FREE_FEATURES)


# ── resolver-crash fallback ───────────────────────────────────────────────────


def test_resolver_crash_falls_through_to_oss_free_snapshot(monkeypatch, app_and_module):
    """When ``get_entitlement`` raises, the route returns the OSS-free ``to_dict``.

    Body must carry the SAME top-level keys as the healthy path -- a paywall
    UI reading ``data.free_runtimes`` / ``data.channel_limit`` /
    ``data.next_tier_locks`` must not KeyError just because a resolver
    hiccup routed the response through the fallback.
    """
    client, ent_mod = app_and_module
    healthy = _healthy_body(app_and_module)

    def _raise(*_a, **_kw):
        raise RuntimeError("resolver crashed")

    monkeypatch.setattr(ent_mod, "get_entitlement", _raise)

    resp = client.get("/api/entitlement")
    assert resp.status_code == 200
    body = resp.get_json()
    # Same top-level shape as the healthy path (no key silently missing).
    assert set(body.keys()) == set(healthy.keys())
    # Features are the canonical FREE_FEATURES set, not an empty list.
    assert set(body["features"]) == set(ent_mod.FREE_FEATURES)
    # Runtimes carry the FREE_RUNTIMES set.
    assert set(body["runtimes"]) == set(ent_mod.FREE_RUNTIMES)
    # ``tier`` / ``source`` / ``grace`` all match the OSS-free anchor.
    assert body["tier"] == "oss"
    assert body["source"] == "oss"
    assert body["grace"] is True
    assert body["is_paid"] is False


def test_resolver_crash_features_never_empty(monkeypatch, app_and_module):
    """Regression: the pre-fix fallback returned ``features: []``.

    Pins that the OSS-free ``to_dict()`` path never yields an empty
    ``features`` list so a downstream ``if not data.features: lock_all()``
    never trips on a transient resolver failure.
    """
    client, ent_mod = app_and_module
    monkeypatch.setattr(
        ent_mod, "get_entitlement", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    body = client.get("/api/entitlement").get_json()
    assert body["features"], "features must never be empty on OSS-free fallback"
    assert len(body["features"]) == len(ent_mod.FREE_FEATURES)


# ── total-module failure fallback ─────────────────────────────────────────────


def test_total_module_failure_returns_minimal_snapshot(monkeypatch, app_and_module):
    """When both the resolver AND ``_oss_free()`` raise, route returns the
    in-line minimal snapshot.

    Simulates the pathological case where the entitlements module itself is
    broken (e.g. import-time syntax error) -- the fallback must still return
    200 with the shape's top-level keys populated so callers do not KeyError.
    """
    client, ent_mod = app_and_module

    def _raise(*_a, **_kw):
        raise RuntimeError("module wedged")

    monkeypatch.setattr(ent_mod, "get_entitlement", _raise)
    monkeypatch.setattr(ent_mod, "_oss_free", _raise)

    resp = client.get("/api/entitlement")
    assert resp.status_code == 200
    body = resp.get_json()
    # Minimal snapshot still carries the healthy-path top-level keys.
    from routes.entitlement import _MINIMAL_OSS_FREE_SNAPSHOT

    for key in _MINIMAL_OSS_FREE_SNAPSHOT:
        assert key in body, key
    # Features carry the OSS-free set (populated, not empty).
    assert body["features"], "minimal snapshot must never carry an empty features list"
    assert "nemo_governance" in body["features"]
    assert "sessions" in body["features"]
    assert set(body["free_runtimes"]) == {"openclaw", "nemoclaw"}
    assert body["tier"] == "oss"
    assert body["grace"] is True


def test_minimal_snapshot_matches_healthy_top_level_keys(app_and_module):
    """Static shape lock: the in-line snapshot's keys are a superset of the
    healthy-path keys minus the two that require a live entitlement object.

    If a future PR adds a new top-level key to ``Entitlement.to_dict``, this
    test fails and forces the author to also add the key to
    ``_MINIMAL_OSS_FREE_SNAPSHOT`` -- keeping the two shapes from drifting.
    """
    healthy = _healthy_body(app_and_module)
    from routes.entitlement import _MINIMAL_OSS_FREE_SNAPSHOT

    missing = set(healthy.keys()) - set(_MINIMAL_OSS_FREE_SNAPSHOT.keys())
    assert missing == set(), (
        f"minimal fallback snapshot is missing top-level keys that the "
        f"healthy /api/entitlement response returns: {sorted(missing)!r}. "
        f"Update _MINIMAL_OSS_FREE_SNAPSHOT in routes/entitlement.py to keep "
        f"the fallback shape in parity with Entitlement.to_dict()."
    )


# ── mutation isolation ────────────────────────────────────────────────────────


def test_minimal_snapshot_is_copied_per_response(monkeypatch, app_and_module):
    """Regression: the fallback must return a COPY of the module-level snapshot
    so a Flask response mutation cannot poison the next request.

    Flask's ``jsonify`` reads the dict at serialisation time; if a caller
    (or a hook) mutated the body dict in place, the next fallback request
    would inherit the mutation. Pinning that back-to-back fallback calls
    return equal-but-distinct dicts locks this in.
    """
    from routes.entitlement import _MINIMAL_OSS_FREE_SNAPSHOT

    client, ent_mod = app_and_module

    def _raise(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent_mod, "get_entitlement", _raise)
    monkeypatch.setattr(ent_mod, "_oss_free", _raise)

    baseline_features = list(_MINIMAL_OSS_FREE_SNAPSHOT["features"])

    body1 = client.get("/api/entitlement").get_json()
    body1["features"].append("__mutated__")
    body2 = client.get("/api/entitlement").get_json()

    assert "__mutated__" not in body2["features"]
    assert list(_MINIMAL_OSS_FREE_SNAPSHOT["features"]) == baseline_features
