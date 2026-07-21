"""Enforce/grace-mode contract tests for the alert-history read/ack surface
in ``routes/alerts.py``.

``custom_alerts`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``): the rule store (``/api/alerts/rules``) and
the evaluator (``clawmetry.sync._evaluate_alerts_local``) both already
require it, so nothing lands in the ``alert_history`` SQLite table on a
tier that doesn't unlock it. The three endpoints that read/ack that same
table therefore belong to the same feature; they all wear the
``@gate("custom_alerts")`` decorator:

  * ``GET  /api/alerts/history``
  * ``POST /api/alerts/history/<int:alert_id>/ack``
  * ``GET  /api/alerts/active``

Sibling of ``tests/test_cost_optimizer_route_gates.py``,
``tests/test_assets_route_gates.py``, ``tests/test_audit_route_gate.py``,
and ``tests/test_tool_policy_route_gate.py``. Pins the same contract for
this trio so a future edit to ``routes/alerts.py`` can't silently drop
the gate:

  1. Enforce mode: each endpoint returns the shared 402 ``upgrade_required``
     envelope with ``feature="custom_alerts"`` and
     ``required_tier=TIER_CLOUD_PRO``. The gate short-circuits before
     ``import dashboard as _d`` runs, so no dashboard stub is needed for
     the enforce path.
  2. Grace mode: the gate is transparent. The endpoint doesn't
     short-circuit with 402; the handler runs through its dashboard
     helpers and returns the pre-migration JSON envelope.
  3. The 402 wire shape is byte-identical to what other ``@gate``d
     routes return, so an existing front-end that already handles 402s
     from ``bp_alerts`` (via ``/api/alerts/rules``) or ``bp_audit`` keeps
     working here without a special-case branch on
     ``feature=="custom_alerts"``.
  4. A resolver crash never surfaces as 402 — mirrors the defensive
     contract pinned in ``tests/test_route_gates.py``.
"""
from __future__ import annotations

import importlib
import sys
import types

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss and
    ``custom_alerts`` (a Pro-only feature) is NOT allowed."""
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
    from routes.alerts import bp_alerts

    app = Flask(__name__)
    app.register_blueprint(bp_alerts)
    return app


class _DummyDb:
    """Minimal stand-in for the SQLite connection ``_fleet_db()`` returns.

    The ack handler runs ``UPDATE alert_history … WHERE id = ?`` and then
    ``commit()`` / ``close()``. None of those need to touch a real DB for
    the gate test — we just need the calls not to explode.
    """

    executed: list[tuple[str, tuple]] = []
    commits: int = 0
    closes: int = 0

    def execute(self, sql, params=()):
        self.__class__.executed.append((sql, tuple(params)))
        return self

    def commit(self):
        self.__class__.commits += 1

    def close(self):
        self.__class__.closes += 1


class _NoopLock:
    """Fake context manager for ``dashboard._fleet_db_lock`` — the ack
    handler wraps its DB work in ``with _d._fleet_db_lock:``; we only need
    ``__enter__``/``__exit__`` to be callable."""

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


def _stub_dashboard(monkeypatch):
    """Install a stub ``dashboard`` module so the three handlers'
    ``import dashboard as _d`` calls resolve to a hermetic object.

    Lets grace-mode tests exercise the whole handler without needing the
    real 17k-line ``dashboard.py`` (which would pull in Flask app state,
    DuckDB, and the interceptor)."""
    _DummyDb.executed = []
    _DummyDb.commits = 0
    _DummyDb.closes = 0

    stub = types.ModuleType("dashboard")

    stub.calls = {"history": [], "active": 0}

    def _get_alert_history(limit=50):
        stub.calls["history"].append(limit)
        return [{"id": 1, "rule_id": "r1", "fired_at": 123.0}]

    def _get_active_alerts():
        stub.calls["active"] += 1
        return [{"id": 1, "rule_id": "r1", "fired_at": 123.0}]

    stub._get_alert_history = _get_alert_history
    stub._get_active_alerts = _get_active_alerts
    stub._fleet_db_lock = _NoopLock()
    stub._fleet_db = lambda: _DummyDb()

    monkeypatch.setitem(sys.modules, "dashboard", stub)
    return stub


# ── enforce mode: 402 on every gated endpoint ────────────────────────────────


_ENFORCE_MATRIX = [
    ("GET", "/api/alerts/history"),
    ("POST", "/api/alerts/history/1/ack"),
    ("GET", "/api/alerts/active"),
]


def _call(client, method, path):
    if method == "GET":
        return client.get(path)
    if method == "POST":
        return client.post(path)
    raise AssertionError(f"unknown method {method}")  # pragma: no cover


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_alerts_history_endpoint_returns_402_when_enforced(enforce, method, path):
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
        assert body["feature"] == "custom_alerts"
        # Pro-only feature — required_tier must be TIER_CLOUD_PRO so the
        # paywall CTA routes users to the right plan (not Starter, not
        # Enterprise).
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier on an OSS install
        # with no license, this is TIER_OSS.
        assert body["tier"] == enforce.TIER_OSS
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No alerts payload leaked through — the gate short-circuited.
        assert "alerts" not in body
        assert "ok" not in body


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_alerts_history_402_body_shape_matches_shared_gate(enforce, method, path):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch. Pins that a later refactor of ``@gate`` doesn't
    silently drop ``required_tier`` or ``tier`` on this route.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference", methods=["GET", "POST"])
    @_gate("custom_alerts")
    def _reference_view():  # pragma: no cover - never runs in enforce mode
        return {"ok": True}

    alerts_app = _make_app()

    with reference_app.test_client() as rc, alerts_app.test_client() as ac:
        ref_body = _call(rc, method, "/reference").get_json()
        act_body = _call(ac, method, path).get_json()
        assert set(ref_body.keys()) == set(act_body.keys())
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == act_body["feature"] == "custom_alerts"
        assert ref_body["required_tier"] == act_body["required_tier"]
        assert ref_body["tier"] == act_body["tier"]


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_alerts_history_gate_fires_before_dashboard_import(
    enforce, monkeypatch, method, path
):
    """The gate has to short-circuit the request *before* the handler
    runs. Prove it by NOT stubbing ``dashboard``: install a booby-trapped
    module whose every attribute access raises, so if the gate were
    missing, the handler's ``import dashboard as _d`` would either succeed
    (leaking a 200) or blow up with an exception. A clean 402 here proves
    the gate fired before the import.
    """
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


def test_alerts_history_transparent_in_grace_mode(monkeypatch, grace):
    """Grace mode (the current default until the enforce-phase release)
    must let ``GET /api/alerts/history`` through unchanged."""
    stub = _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/alerts/history?limit=17")
        assert r.status_code == 200
        body = r.get_json()
        # The pre-migration handler always returned this envelope.
        assert "alerts" in body
        assert body["alerts"] == [{"id": 1, "rule_id": "r1", "fired_at": 123.0}]
        # The ``?limit=`` query param reached ``_get_alert_history``.
        assert stub.calls["history"] == [17]


def test_alerts_history_default_limit_in_grace_mode(monkeypatch, grace):
    """Grace mode: with no ``?limit=`` the handler defaults to 50 —
    pins the pre-migration behaviour across the gate migration."""
    stub = _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/alerts/history")
        assert r.status_code == 200
        assert stub.calls["history"] == [50]


def test_alerts_active_transparent_in_grace_mode(monkeypatch, grace):
    """Grace mode: ``GET /api/alerts/active`` also runs through."""
    stub = _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/alerts/active")
        assert r.status_code == 200
        body = r.get_json()
        assert "alerts" in body
        assert stub.calls["active"] == 1


def test_alerts_ack_transparent_in_grace_mode(monkeypatch, grace):
    """Grace mode: ``POST /api/alerts/history/<id>/ack`` runs the update
    against ``dashboard._fleet_db()`` and returns ``{"ok": true}``.
    """
    _stub_dashboard(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/alerts/history/42/ack")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}
    # The handler executed exactly one UPDATE against the fake DB and
    # committed + closed the connection.
    assert len(_DummyDb.executed) == 1
    sql, params = _DummyDb.executed[0]
    assert "UPDATE alert_history" in sql
    assert "acknowledged = 1" in sql
    # id 42 is the second positional param; the first is time.time().
    assert params[1] == 42
    assert _DummyDb.commits == 1
    assert _DummyDb.closes == 1


# ── defensive fallthrough ────────────────────────────────────────────────────


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_entitlement_lookup_crash_falls_through(
    monkeypatch, enforce, method, path
):
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
        r = _call(c, method, path)
        # Graceful fallthrough: NOT 402. Handler runs and returns 200.
        assert r.status_code != 402
        assert r.status_code == 200


# ── decorator wiring pin ─────────────────────────────────────────────────────


def test_alerts_history_routes_wear_gate_decorator():
    """The three alert-history routes must be wired with
    ``@gate("custom_alerts")``. Pin this at the module level so a
    well-meaning revert that drops the decorator (leaving the endpoints
    unguarded) fails loudly instead of silently reverting the gate.

    We check by inspecting the source rather than by calling the route
    because the ``@gate`` decorator is transparent in grace mode; a
    regression that dropped it would look identical in grace tests.
    """
    import inspect

    from routes import alerts

    src = inspect.getsource(alerts)
    assert "from clawmetry._gate import gate" in src, (
        "routes/alerts.py must import @gate from clawmetry._gate"
    )
    # Count of ``@gate("custom_alerts")`` occurrences. Before this
    # migration there were two (``/api/alerts/rules`` and
    # ``/api/alerts/rules/<rule_id>``); after, five — the three
    # history/active/ack routes added here plus the two existing.
    single = src.count("@gate(\"custom_alerts\")")
    double = src.count("@gate('custom_alerts')")
    assert single + double >= 5, (
        "routes/alerts.py should decorate the alert-history/active/ack "
        "routes with @gate('custom_alerts') in addition to the existing "
        "rules routes."
    )


def test_alerts_history_handlers_are_specifically_gated():
    """Belt-and-braces: inspect each handler's ``__wrapped__`` chain to
    confirm ``@gate('custom_alerts')`` is present on each of the three
    handlers. A drive-by refactor that reorders decorators must not drop
    the gate on any single one.
    """
    from routes import alerts as A

    for name in ("api_alert_history", "api_alert_ack", "api_alerts_active"):
        fn = getattr(A, name)
        # ``@gate`` wraps with ``functools.wraps``; the wrapper's own
        # ``__wrapped__`` points at the inner view. Walk the module source
        # near each function to prove the decorator sits above the route.
        import inspect
        module_src = inspect.getsource(A)
        idx = module_src.find(f"def {name}(")
        assert idx > 0, f"could not locate def {name}(…) in routes/alerts.py"
        # Look at the ~200 chars immediately preceding the def — that's
        # where the decorators sit.
        prefix = module_src[max(0, idx - 200):idx]
        assert "@gate(\"custom_alerts\")" in prefix or "@gate('custom_alerts')" in prefix, (
            f"routes/alerts.py::{name} must wear @gate('custom_alerts')"
        )
