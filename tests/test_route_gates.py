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
