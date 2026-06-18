"""Tests for the entitlement gate decorator + route wiring.

Pins the 402 ``upgrade_required`` contract that paid routes return in enforce
mode and the decorator order (route registers gated function, not the bare
view). Companion to tests/test_entitlements_catalogue.py.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def grace(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── @gate decorator contract ─────────────────────────────────────────────────


def test_gate_decorator_blocks_in_enforce_mode(enforce):
    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/test")
    @gate("self_evolve")
    def test_view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "self_evolve"
        assert "tier" in body
        assert "hint" in body
        # required_tier lets the dashboard render the right "Upgrade to ___"
        # CTA directly off the 402 body.
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO


# ── required_tier mapping ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "feature_key,expected_tier_attr",
    [
        ("multi_runtime", "TIER_CLOUD_STARTER"),
        ("budget_limits", "TIER_CLOUD_STARTER"),
        ("self_evolve", "TIER_CLOUD_PRO"),
        ("otel_export", "TIER_CLOUD_PRO"),
        ("siem_export", "TIER_ENTERPRISE"),
        ("sso", "TIER_ENTERPRISE"),
    ],
)
def test_gate_required_tier_routes_to_correct_upgrade(
    enforce, feature_key, expected_tier_attr
):
    """The 402 body carries ``required_tier`` so the UI can render the right
    upgrade CTA (Starter vs Pro vs Enterprise) without re-deriving tier
    logic in JavaScript."""
    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/test")
    @gate(feature_key)
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 402
        body = r.get_json()
        assert body["required_tier"] == getattr(enforce, expected_tier_attr)


def test_gate_required_tier_helper_is_none_for_free_feature(enforce):
    """Free features never produce a 402, but if a caller asks the helper
    directly it returns ``None`` (no upgrade required)."""
    from clawmetry._gate import _required_tier

    assert _required_tier("sessions") is None
    assert _required_tier("usage") is None


def test_gate_required_tier_helper_is_none_for_unknown_feature(enforce):
    """Unknown / typo'd feature keys resolve to ``None`` rather than raising.
    Keeps the 402 body well-formed when a route uses a key that isn't yet in
    the catalogue (e.g. a clawmetry-pro plugin's private feature)."""
    from clawmetry._gate import _required_tier

    assert _required_tier("totally_unknown_feature_xyz") is None


def test_gate_required_tier_helper_swallows_entitlement_errors(monkeypatch):
    """If the catalogue lookup itself raises the helper returns ``None``
    rather than propagating — the 402 path stays defensive even if a flaky
    entitlements module is loaded."""
    from clawmetry import _gate

    def explode(_key):
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.min_tier_for_feature", explode)
    assert _gate._required_tier("self_evolve") is None


def test_gate_decorator_passes_in_grace_mode(grace):
    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/test")
    @gate("self_evolve")
    def test_view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}


def test_gate_decorator_allows_free_features_even_when_enforced(enforce):
    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/sessions")
    @gate("sessions")  # free feature
    def list_sessions():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/sessions")
        assert r.status_code == 200


def test_gate_decorator_never_raises_when_entitlement_lookup_fails(enforce, monkeypatch):
    """If the entitlement read itself throws, the request still goes through.
    The worst that happens is a paid feature briefly runs on a Free tier — a
    flaky entitlement check must never break the request path."""
    from clawmetry._gate import gate

    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", explode)

    app = Flask(__name__)

    @app.route("/test")
    @gate("self_evolve")
    def test_view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 200  # graceful fallthrough


# ── decorator order regression ───────────────────────────────────────────────


def test_gate_must_be_inside_route(enforce):
    """Regression: @gate has to be BELOW @bp.route or Flask registers the
    unwrapped view and the 402 never fires. We catch this by writing the
    route the right way and then asserting it returns 402.
    """
    from clawmetry._gate import gate

    app = Flask(__name__)

    @app.route("/test")
    @gate("self_evolve")
    def test_view():
        return {"ok": True}

    with app.test_client() as c:
        assert c.get("/test").status_code == 402


# ── live route wiring smoke check ────────────────────────────────────────────


def _make_app_with(blueprint):
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    return app


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/selfevolve/status", "GET"),
        ("/api/selfevolve/latest", "GET"),
        ("/api/assets", "GET"),
    ],
)
def test_gated_route_returns_402_when_enforced(enforce, path, method):
    """The actual blueprint routes return 402 when enforced and the tier
    doesn't include the feature."""
    if path.startswith("/api/selfevolve"):
        from routes.selfevolve import bp_selfevolve as bp
    else:
        from routes.assets import bp_assets as bp
    app = _make_app_with(bp)
    with app.test_client() as c:
        r = c.open(path, method=method)
        # The route may also short-circuit on missing daemon (5xx); the gate
        # check fires *before* the body, so 402 should win.
        assert r.status_code == 402, f"{method} {path} returned {r.status_code}"


def test_gated_route_passes_in_grace_mode(grace):
    from routes.assets import bp_assets

    app = _make_app_with(bp_assets)
    with app.test_client() as c:
        r = c.get("/api/assets")
        # In grace mode the gate is transparent; downstream handler runs (may
        # return 200 with an empty list, or a 500 if the daemon isn't up). We
        # only need to confirm we did NOT get the 402 short-circuit.
        assert r.status_code != 402
