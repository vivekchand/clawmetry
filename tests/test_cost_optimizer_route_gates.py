"""Enforce/grace-mode contract tests for the ``bp_config`` cost-optimizer
endpoints in ``routes/infra.py``.

``cost_optimizer`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``). Both public cost-optimizer JSON endpoints
implement it, so they both wear the ``@gate("cost_optimizer")`` decorator:

  * ``GET /api/cost-optimizer``
  * ``GET /api/cost-optimization``

Sibling of ``tests/test_assets_route_gates.py``,
``tests/test_fleet_route_gates.py``, ``tests/test_audit_route_gate.py``,
and ``tests/test_otel_export_route_gate.py``. Pins the same contract for
this pair of routes so a future edit to ``routes/infra.py`` can't
silently drop the gate:

  1. Enforce mode: each endpoint returns the shared 402 ``upgrade_required``
     envelope with ``feature="cost_optimizer"`` and
     ``required_tier=TIER_CLOUD_PRO``. Because the gate check fires before
     any handler code runs, the 402 short-circuits before the DuckDB /
     ``dashboard.py`` helpers are even touched — no ``dashboard`` stub
     is needed for the enforce path.
  2. Grace mode: the gate is transparent. The endpoint doesn't
     short-circuit with 402; whatever the downstream handler returns
     (200 with the cost payload, an error envelope with 200 if a helper
     raises, etc.) wins.
  3. The 402 wire shape is byte-identical to what other ``@gate``d
     routes return, so an existing front-end that already handles 402s
     from ``bp_assets`` / ``bp_audit`` / ``bp_otel_export`` keeps working
     here without a special-case branch on ``feature=="cost_optimizer"``.
  4. A resolver crash never surfaces as 402 — mirrors the defensive
     contract pinned in ``tests/test_route_gates.py``.

Companion to ``tests/test_cost_optimizer_local_store_v3.py`` (which
pins the DuckDB fast-path shape) — the two files test orthogonal
concerns and neither imports the other.
"""
from __future__ import annotations

import importlib
import types

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss and
    ``cost_optimizer`` (a Pro-only feature) is NOT allowed."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def grace(monkeypatch, tmp_path):
    """Default grace mode — every feature key passes through the gate."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _make_app():
    from routes.infra import bp_config

    app = Flask(__name__)
    app.register_blueprint(bp_config)
    return app


def _stub_dashboard(monkeypatch):
    """Install a stub ``dashboard`` module so the cost-optimizer handlers'
    ``import dashboard as _d`` calls resolve to a hermetic object.

    The handlers read a handful of helpers off ``dashboard``; we stub them
    to return the smallest well-shaped values that keep the payload
    builders from raising. This lets grace-mode tests exercise the whole
    handler without needing the real 17k-line ``dashboard.py`` (which
    would pull in Flask app state, DuckDB, and the interceptor).
    """
    import sys

    stub = types.ModuleType("dashboard")

    def _cost_summary():
        return {"today": 0.0, "week": 0.0, "month": 0.0, "projected": 0.0}

    def _expensive_ops():
        return []

    def _detect_ollama():
        return False

    def _detect_host_hardware():
        return {
            "cpu": "test-cpu",
            "cores": 1,
            "ram_gb": 1,
            "backend": "cpu",
        }

    def _check_ollama_availability():
        return {"available": False, "count": 0, "models": []}

    def _generate_cost_recommendations(_costs, _local):
        return []

    def _get_llmfit_recommendations():
        return {
            "available": False,
            "recommendations": [],
            "codingModels": [],
            "chatModels": [],
            "system": {},
        }

    def _generate_savings_opportunities():
        return []

    stub._get_cost_summary = _cost_summary
    stub._get_expensive_operations = _expensive_ops
    stub._detect_ollama = _detect_ollama
    stub._detect_host_hardware = _detect_host_hardware
    stub._check_ollama_availability = _check_ollama_availability
    stub._generate_cost_recommendations = _generate_cost_recommendations
    stub._get_llmfit_recommendations = _get_llmfit_recommendations
    stub._generate_savings_opportunities = _generate_savings_opportunities

    monkeypatch.setitem(sys.modules, "dashboard", stub)
    return stub


# ── enforce mode: 402 on every gated endpoint ────────────────────────────────


_ENFORCE_MATRIX = [
    "/api/cost-optimizer",
    "/api/cost-optimization",
]


@pytest.mark.parametrize("path", _ENFORCE_MATRIX)
def test_cost_optimizer_endpoint_returns_402_when_enforced(enforce, path):
    """Each gated endpoint returns the shared 402 body in enforce mode."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get(path)
        assert r.status_code == 402, (
            f"GET {path} returned {r.status_code}, expected 402 "
            "(gate should short-circuit before handler runs)"
        )
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "cost_optimizer"
        # Pro-only feature — required_tier must be TIER_CLOUD_PRO so the
        # paywall CTA routes users to the right plan (not Starter, not
        # Enterprise).
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier so the UI can render
        # the delta ("you have X, upgrade to Y"). On an OSS install with
        # no license, this is TIER_OSS.
        assert body["tier"] == enforce.TIER_OSS
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No cost payload leaked through — the gate short-circuited.
        assert "costs" not in body
        assert "localModels" not in body


@pytest.mark.parametrize("path", _ENFORCE_MATRIX)
def test_cost_optimizer_402_body_shape_matches_shared_gate(enforce, path):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch. Pins that a later refactor of ``@gate`` doesn't
    silently drop ``required_tier`` or ``tier`` on this route.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("cost_optimizer")
    def _reference_view():  # pragma: no cover - never runs in enforce mode
        return {"ok": True}

    cost_app = _make_app()

    with reference_app.test_client() as rc, cost_app.test_client() as ac:
        ref_body = rc.get("/reference").get_json()
        act_body = ac.get(path).get_json()
        assert set(ref_body.keys()) == set(act_body.keys())
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == act_body["feature"] == "cost_optimizer"
        assert ref_body["required_tier"] == act_body["required_tier"]
        assert ref_body["tier"] == act_body["tier"]


@pytest.mark.parametrize("path", _ENFORCE_MATRIX)
def test_cost_optimizer_gate_fires_before_dashboard_import(
    enforce, monkeypatch, path
):
    """The gate has to short-circuit the request *before* the handler
    runs. Prove it by NOT stubbing ``dashboard``: if the gate were
    missing, the handler's ``import dashboard as _d`` would either
    succeed (leaking a 200) or blow up with an exception — neither is a
    402. The gate short-circuits, so we never reach the import.
    """
    # Make dashboard import a distinctive failure — if the handler ever
    # tries to import it during an enforce-mode call, this exception
    # bubbles up as 500, NOT 402. So a 402 here proves the gate fired
    # before the import.
    import sys

    class _Boom:  # pragma: no cover - only hit on regression
        def __getattr__(self, name):
            raise AssertionError(
                f"gate should have short-circuited before "
                f"dashboard.{name} was reached"
            )

    monkeypatch.setitem(sys.modules, "dashboard", _Boom())

    app = _make_app()
    with app.test_client() as c:
        r = c.get(path)
        assert r.status_code == 402


# ── grace mode: gate is transparent on every endpoint ───────────────────────


@pytest.mark.parametrize("path", _ENFORCE_MATRIX)
def test_cost_optimizer_endpoint_is_transparent_in_grace_mode(
    monkeypatch, grace, path
):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler runs
    with a stubbed ``dashboard`` so the payload builder can finish
    without pulling in the real 17k-line module.
    """
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get(path)
        assert r.status_code != 402, (
            f"GET {path} 402'd in grace mode; gate is not transparent"
        )
        # Handler ran and returned SOMETHING with a body — the payload
        # builder in the pre-migration handler always emitted a JSON
        # dict, even on the exception-fallback branch.
        body = r.get_json()
        assert isinstance(body, dict)
        # The 402 short-circuit body has ``error="upgrade_required"``;
        # the handler payload (from either endpoint, on either the happy
        # or the exception-fallback branch) never does. Pins that the
        # gate stayed transparent AND the handler emitted its own body.
        assert body.get("error") != "upgrade_required"
        # Both endpoints emit ``localModels`` on both happy and error
        # branches — pins that the handler's payload builder ran through.
        assert "localModels" in body


# ── defensive fallthrough ────────────────────────────────────────────────────


@pytest.mark.parametrize("path", _ENFORCE_MATRIX)
def test_entitlement_lookup_crash_falls_through(monkeypatch, enforce, path):
    """Mirrors the contract in ``tests/test_route_gates.py``: if the
    entitlement read itself raises, the request path stays defensive and
    the handler runs — the worst that happens is a paid feature briefly
    runs on a Free tier. A flaky entitlement check must never fail
    closed.
    """
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get(path)
        # Graceful fallthrough: NOT 402. Handler runs (may 200 with the
        # payload envelope, or 200 with the exception-fallback envelope
        # if a helper raises inside — both are acceptable, the key is we
        # did not fail closed with a 402).
        assert r.status_code != 402


# ── decorator wiring pin ─────────────────────────────────────────────────────


def test_cost_optimizer_routes_wear_gate_decorator():
    """The two cost-optimizer routes must be wired with
    ``@gate("cost_optimizer")``. Pin this at the module level so a
    well-meaning revert that drops the decorator (leaving the endpoints
    unguarded) fails loudly instead of silently reverting the gate.

    We check by inspecting the source rather than by calling the route
    because the ``@gate`` decorator is transparent in grace mode; a
    regression that dropped it would look identical in grace tests.
    """
    import inspect

    from routes import infra

    src = inspect.getsource(infra)
    assert 'from clawmetry._gate import gate' in src, (
        "routes/infra.py must import @gate from clawmetry._gate"
    )
    assert '@gate("cost_optimizer")' in src, (
        'routes/infra.py must decorate the cost-optimizer routes with '
        '@gate("cost_optimizer") — this is the only enforcement point '
        'until the closed-source clawmetry-pro package overrides the '
        'blueprint via the extensions entry point.'
    )
