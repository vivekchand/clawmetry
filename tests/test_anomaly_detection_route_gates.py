"""Enforce/grace-mode contract tests for the ``bp_usage`` anomaly-detection
endpoints in ``routes/usage.py``.

``anomaly_detection`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``). Three public JSON endpoints implement it,
so all three wear the ``@gate("anomaly_detection")`` decorator:

  * ``GET  /api/usage/anomalies``
  * ``GET  /api/anomalies``
  * ``POST /api/anomalies/<int:anomaly_id>/ack``

Sibling of ``tests/test_cost_optimizer_route_gates.py``,
``tests/test_assets_route_gates.py``,
``tests/test_fleet_route_gates.py``, ``tests/test_audit_route_gate.py``,
``tests/test_otel_export_route_gate.py``,
``tests/test_run_compare_route_gate.py``, and
``tests/test_error_triage_route_gate.py``. Pins the same contract for
these three routes so a future edit to ``routes/usage.py`` can't
silently drop the gate:

  1. Enforce mode: each endpoint returns the shared 402 ``upgrade_required``
     envelope with ``feature="anomaly_detection"`` and
     ``required_tier=TIER_CLOUD_PRO``. Because the gate check fires before
     any handler code runs, the 402 short-circuits before the DuckDB /
     ``dashboard.py`` helpers are even touched -- no ``dashboard`` stub
     is needed for the enforce path.
  2. Grace mode: the gate is transparent. Downstream handlers run with
     a stubbed ``dashboard`` so the payload builders can finish without
     pulling in the real 17k-line module.
  3. The 402 wire shape is byte-identical to what other ``@gate``d
     routes return, so an existing front-end that already handles 402s
     from ``bp_assets`` / ``bp_audit`` / ``bp_otel_export`` /
     ``bp_config`` keeps working here without a special-case branch on
     ``feature=="anomaly_detection"``.
  4. A resolver crash never surfaces as 402 -- mirrors the defensive
     contract pinned in ``tests/test_route_gates.py``.
"""
from __future__ import annotations

import importlib
import sys
import threading
import types

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` -- the tier is oss and
    ``anomaly_detection`` (a Pro-only feature) is NOT allowed."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def grace(monkeypatch, tmp_path):
    """Default grace mode -- every feature key passes through the gate."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _make_app():
    from routes.usage import bp_usage

    app = Flask(__name__)
    app.register_blueprint(bp_usage)
    return app


def _stub_dashboard(monkeypatch):
    """Install a stub ``dashboard`` module so the anomaly handlers'
    ``import dashboard as _d`` calls resolve to a hermetic object.

    The handlers read a handful of helpers off ``dashboard``; we stub
    them to return the smallest well-shaped values that keep the payload
    builders from raising. This lets grace-mode tests exercise the whole
    handler without needing the real 17k-line ``dashboard.py``.
    """
    stub = types.ModuleType("dashboard")

    def _compute_transcript_analytics():
        return {"sessions": []}

    def _compute_session_cost_anomalies(_sessions):
        return []

    def _detect_and_store_anomalies():
        return ([], {})

    class _FakeDB:
        def execute(self, *_a, **_kw):
            return self

        def commit(self):
            return None

        def close(self):
            return None

    def _get_anomaly_db():
        return _FakeDB()

    stub._compute_transcript_analytics = _compute_transcript_analytics
    stub._compute_session_cost_anomalies = _compute_session_cost_anomalies
    stub._detect_and_store_anomalies = _detect_and_store_anomalies
    stub._get_anomaly_db = _get_anomaly_db
    stub._anomaly_db_lock = threading.Lock()
    stub._anomaly_detection_cache = {"data": None, "ts": 0.0}
    stub._ANOMALY_CACHE_TTL = 60.0

    monkeypatch.setitem(sys.modules, "dashboard", stub)
    return stub


def _disable_local_store(monkeypatch):
    """Force the handlers off their DuckDB fast paths so the grace-mode
    tests exercise the dashboard-import branch (which is what the gate
    protects).

    The GET /api/usage/anomalies and GET /api/anomalies handlers both
    short-circuit to ``_try_local_store_*`` when
    ``is_local_store_read_enabled()`` is truthy. Setting the env var to
    ``0`` sends them down the ``import dashboard as _d`` branch instead.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")


# ── enforce mode: 402 on every gated endpoint ────────────────────────────────


# Each entry is (http_method, path). Route decorator: methods=["POST"] on
# ack, GET on the other two.
_ENFORCE_MATRIX = [
    ("GET", "/api/usage/anomalies"),
    ("GET", "/api/anomalies"),
    ("POST", "/api/anomalies/1/ack"),
]


def _call(client, method, path):
    if method == "GET":
        return client.get(path)
    if method == "POST":
        return client.post(path)
    raise AssertionError(f"unhandled method {method!r}")


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_anomaly_endpoint_returns_402_when_enforced(enforce, method, path):
    """Each gated endpoint returns the shared 402 body in enforce mode."""
    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path)
        assert r.status_code == 402, (
            f"{method} {path} returned {r.status_code}, expected 402 "
            "(gate should short-circuit before handler runs)"
        )
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "anomaly_detection"
        # Pro-only feature -- required_tier must be TIER_CLOUD_PRO so the
        # paywall CTA routes users to the right plan (not Starter, not
        # Enterprise).
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier so the UI can render
        # the delta ("you have X, upgrade to Y"). On an OSS install with
        # no license, this is TIER_OSS.
        assert body["tier"] == enforce.TIER_OSS
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No anomaly payload leaked through -- the gate short-circuited.
        assert "anomalies" not in body
        assert "baselines" not in body
        assert "baseline_7d_avg_usd" not in body


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_anomaly_402_body_shape_matches_shared_gate(enforce, method, path):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch. Pins that a later refactor of ``@gate`` doesn't
    silently drop ``required_tier`` or ``tier`` on these routes.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("anomaly_detection")
    def _reference_view():  # pragma: no cover - never runs in enforce mode
        return {"ok": True}

    target_app = _make_app()

    with reference_app.test_client() as rc, target_app.test_client() as ac:
        ref_body = rc.get("/reference").get_json()
        act_body = _call(ac, method, path).get_json()
        assert set(ref_body.keys()) == set(act_body.keys())
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == act_body["feature"] == "anomaly_detection"
        assert ref_body["required_tier"] == act_body["required_tier"]
        assert ref_body["tier"] == act_body["tier"]


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_anomaly_gate_fires_before_dashboard_import(
    enforce, monkeypatch, method, path
):
    """The gate has to short-circuit the request *before* the handler
    runs. Prove it by installing a distinctive booby-trap ``dashboard``
    module: if the gate were missing, the handler's ``import dashboard
    as _d`` would either succeed (leaking a 200) or blow up with an
    ``AssertionError`` -- neither is a 402. The gate short-circuits, so
    we never reach the import.

    Also disables the DuckDB fast path via env so a lazy handler that
    somehow bypassed the gate couldn't hide inside the local-store
    branch and produce a green false negative.
    """
    _disable_local_store(monkeypatch)

    class _Boom:  # pragma: no cover - only hit on regression
        def __getattr__(self, name):
            raise AssertionError(
                f"gate should have short-circuited before "
                f"dashboard.{name} was reached"
            )

    monkeypatch.setitem(sys.modules, "dashboard", _Boom())

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path)
        assert r.status_code == 402


# ── grace mode: gate is transparent on every endpoint ───────────────────────


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_anomaly_endpoint_is_transparent_in_grace_mode(
    monkeypatch, grace, method, path
):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler runs
    with a stubbed ``dashboard`` and the DuckDB fast path disabled so
    the payload builder is exercised without pulling in the real
    17k-line module.
    """
    _disable_local_store(monkeypatch)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path)
        assert r.status_code != 402, (
            f"{method} {path} 402'd in grace mode; gate is not transparent"
        )
        body = r.get_json()
        assert isinstance(body, dict)
        # The 402 short-circuit body has ``error="upgrade_required"``;
        # the handler payload never does. Pins that the gate stayed
        # transparent AND the handler emitted its own body.
        assert body.get("error") != "upgrade_required"


def test_usage_anomalies_grace_payload_shape(monkeypatch, grace):
    """Grace mode: /api/usage/anomalies must still emit the pre-migration
    envelope keys."""
    _disable_local_store(monkeypatch)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/usage/anomalies").get_json()
        assert "anomalies" in body
        assert "baseline_7d_avg_usd" in body
        assert "threshold_multiplier" in body


def test_anomalies_grace_payload_shape(monkeypatch, grace):
    """Grace mode: /api/anomalies must still emit the pre-migration
    envelope keys."""
    _disable_local_store(monkeypatch)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/anomalies").get_json()
        assert "anomalies" in body
        assert "active_count" in body
        assert "has_active" in body
        assert "baselines" in body


def test_anomaly_ack_grace_payload_shape(monkeypatch, grace):
    """Grace mode: POST /api/anomalies/<id>/ack must still return the
    pre-migration ``{ok, id}`` envelope."""
    _disable_local_store(monkeypatch)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/anomalies/42/ack")
        body = r.get_json()
        assert body.get("ok") is True
        assert body.get("id") == 42


# ── defensive fallthrough ────────────────────────────────────────────────────


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_entitlement_lookup_crash_falls_through(
    monkeypatch, enforce, method, path
):
    """Mirrors the contract in ``tests/test_route_gates.py``: if the
    entitlement read itself raises, the request path stays defensive and
    the handler runs -- the worst that happens is a paid feature briefly
    runs on a Free tier. A flaky entitlement check must never fail
    closed.
    """
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)
    _disable_local_store(monkeypatch)
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path)
        # Graceful fallthrough: NOT 402. Handler runs and returns
        # whatever it would have returned pre-migration (200 with the
        # payload envelope on the happy path, or 500 with the ack
        # error-fallback envelope if a helper raises -- both acceptable,
        # the key is we did not fail closed with a 402).
        assert r.status_code != 402


# ── decorator wiring pin ─────────────────────────────────────────────────────


def test_anomaly_routes_wear_gate_decorator():
    """All three anomaly-detection routes must be wired with
    ``@gate("anomaly_detection")``. Pin this at the module level so a
    well-meaning revert that drops the decorator from any single route
    (leaving a partial gate -- indistinguishable in a single-route grace
    test) fails loudly instead of silently reverting the gate.

    We check by inspecting the source rather than by calling the route
    because the ``@gate`` decorator is transparent in grace mode; a
    regression that dropped it would look identical in grace tests.
    """
    import inspect

    from routes import usage

    src = inspect.getsource(usage)
    assert 'from clawmetry._gate import gate' in src, (
        "routes/usage.py must import @gate from clawmetry._gate"
    )
    # Exactly three anomaly-detection routes exist today; if a fourth is
    # added it should also wear the gate, so this pin should be updated
    # in the same PR that adds it (a mismatch is a signal to inspect).
    assert src.count('@gate("anomaly_detection")') == 3, (
        'routes/usage.py must decorate all three anomaly-detection '
        'routes with @gate("anomaly_detection") -- this is the only '
        'enforcement point until the closed-source clawmetry-pro '
        'package overrides the blueprint via the extensions entry '
        'point.'
    )
