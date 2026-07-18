"""Enforce/grace-mode contract tests for the ``bp_evals`` endpoints in
``routes/evals.py``.

``eval_suite`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``). Seven public JSON endpoints implement it,
so all seven wear the ``@gate("eval_suite")`` decorator:

  * ``GET  /api/evals/recent``
  * ``GET  /api/evals/summary``
  * ``POST /api/evals/rescore/<session_id>``
  * ``GET  /api/evals/rubric``
  * ``POST /api/evals/rubric``
  * ``GET  /api/evals/regression-summary``
  * ``GET  /api/evals/key``
  * ``POST /api/evals/key``

The eighth route on ``bp_evals`` — ``GET /api/evaluators`` — is the
shop-menu catalogue. It intentionally exposes the ``locked: true`` state
of Pro evaluators so the UI can render an upgrade CTA, so it stays free
and is deliberately *not* gated. This test file pins that split so a
well-meaning refactor that gates the catalogue too (which would blank
the CTA under enforce and confuse the upgrade flow) fails loudly.

Sibling of ``tests/test_anomaly_detection_route_gates.py``,
``tests/test_cost_optimizer_route_gates.py``,
``tests/test_assets_route_gates.py``,
``tests/test_fleet_route_gates.py``, ``tests/test_audit_route_gate.py``,
``tests/test_otel_export_route_gate.py``,
``tests/test_run_compare_route_gate.py``, and
``tests/test_error_triage_route_gate.py``. Pins the same contract for
these eight routes so a future edit to ``routes/evals.py`` can't
silently drop the gate:

  1. Enforce mode: each gated endpoint returns the shared 402
     ``upgrade_required`` envelope with ``feature="eval_suite"`` and
     ``required_tier=TIER_CLOUD_PRO``. The gate check fires before any
     handler code runs, so the 402 short-circuits before
     ``clawmetry.eval_runner`` or the DuckDB helpers are even imported.
  2. Grace mode: the gate is transparent. Downstream handlers run with
     a stubbed ``clawmetry.eval_runner`` + local-store hop so the
     payload builders can finish without touching disk.
  3. The 402 wire shape is byte-identical to what other ``@gate``d
     routes return, so an existing front-end that already handles 402s
     from ``bp_assets`` / ``bp_audit`` / ``bp_otel_export`` /
     ``bp_config`` keeps working here without a special-case branch on
     ``feature=="eval_suite"``.
  4. A resolver crash never surfaces as 402 -- mirrors the defensive
     contract pinned in ``tests/test_route_gates.py``.
  5. The catalogue ``/api/evaluators`` stays free -- a whole-blueprint
     gate would break the upgrade CTA render path.
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
    """OSS install under ``CLAWMETRY_ENFORCE=1`` -- the tier is oss and
    ``eval_suite`` (a Pro-only feature) is NOT allowed."""
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
    from routes.evals import bp_evals

    app = Flask(__name__)
    app.register_blueprint(bp_evals)
    return app


def _stub_eval_runner(monkeypatch):
    """Install a stub ``clawmetry.eval_runner`` so the handlers'
    ``from clawmetry import eval_runner`` calls resolve to a hermetic
    object with the surface the routes actually touch.

    The handlers touch a handful of module-level attributes and helper
    functions; we stub each to return the smallest well-shaped value
    that keeps the payload builders from raising. This lets grace-mode
    tests exercise the whole handler without touching the real
    disk-backed rubric or judge-key files.
    """
    stub = types.ModuleType("clawmetry.eval_runner")

    stub.RUBRIC_PATH = "/tmp/does-not-exist.yaml"
    stub.DEFAULT_RUBRIC = {"kind": "default", "criteria": []}

    def is_enabled():
        return True

    def get_rubric_yaml():
        return "kind: default\n"

    def judge_keys_present():
        return {"anthropic": False, "openai": False}

    def save_judge_key(_provider, _api_key):
        return None

    def save_rubric_yaml(_text):
        return None

    def load_rubric(_name):
        return {"kind": "default", "criteria": []}

    class _Result:
        def to_dict(self):
            return {"session_id": "sid", "score": 0.5}

    class _Runner:
        def score_session(self, _sid):
            return _Result()

    stub.is_enabled = is_enabled
    stub.get_rubric_yaml = get_rubric_yaml
    stub.judge_keys_present = judge_keys_present
    stub.save_judge_key = save_judge_key
    stub.save_rubric_yaml = save_rubric_yaml
    stub.load_rubric = load_rubric
    stub.EvalRunner = _Runner

    monkeypatch.setitem(sys.modules, "clawmetry.eval_runner", stub)
    return stub


def _stub_regression_replay(monkeypatch):
    """Install a stub ``clawmetry.eval_regression_replay`` for the
    regression-summary handler so grace-mode tests don't hit the real
    DuckDB reader."""
    stub = types.ModuleType("clawmetry.eval_regression_replay")

    def regression_summary(window_days: int = 7):
        return {
            "tested": 0, "improved": 0, "regressed": 0, "same": 0,
            "errored": 0, "window_days": window_days, "last_run_at": None,
        }

    stub.regression_summary = regression_summary
    monkeypatch.setitem(sys.modules, "clawmetry.eval_regression_replay", stub)
    return stub


def _stub_store_helpers(monkeypatch):
    """Stub the ``routes.local_query.local_store_via_daemon`` and
    ``clawmetry.local_store`` calls so grace-mode tests don't require a
    live daemon or a DuckDB file. Both return ``None`` -- the handlers
    already treat that as "no rows" and emit an empty envelope.
    """
    from routes import evals as evals_module

    def _none(*_a, **_kw):
        return None

    monkeypatch.setattr(evals_module, "_store_via_daemon_or_direct", _none)


# ── enforce mode: 402 on every gated endpoint ────────────────────────────────


# Each entry is (http_method, path). Route decorators declare methods
# explicitly (GET/POST) on each endpoint.
_ENFORCE_MATRIX = [
    ("GET",  "/api/evals/recent"),
    ("GET",  "/api/evals/summary"),
    ("POST", "/api/evals/rescore/sid-42"),
    ("GET",  "/api/evals/rubric"),
    ("POST", "/api/evals/rubric"),
    ("GET",  "/api/evals/regression-summary"),
    ("GET",  "/api/evals/key"),
    ("POST", "/api/evals/key"),
]


def _call(client, method, path, *, json=None):
    if method == "GET":
        return client.get(path)
    if method == "POST":
        return client.post(path, json=json or {})
    raise AssertionError(f"unhandled method {method!r}")


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_evals_endpoint_returns_402_when_enforced(enforce, method, path):
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
        assert body["feature"] == "eval_suite"
        # Pro-only feature -- required_tier must be TIER_CLOUD_PRO so the
        # paywall CTA routes users to the right plan (not Starter, not
        # Enterprise).
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier so the UI can
        # render the delta ("you have X, upgrade to Y"). On an OSS
        # install with no license, this is TIER_OSS.
        assert body["tier"] == enforce.TIER_OSS
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No eval payload leaked through -- the gate short-circuited.
        assert "evals" not in body
        assert "avg_score" not in body
        assert "yaml" not in body
        assert "present" not in body


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_evals_402_body_shape_matches_shared_gate(enforce, method, path):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch. Pins that a later refactor of ``@gate`` doesn't
    silently drop ``required_tier`` or ``tier`` on these routes.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("eval_suite")
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
        assert ref_body["feature"] == act_body["feature"] == "eval_suite"
        assert ref_body["required_tier"] == act_body["required_tier"]
        assert ref_body["tier"] == act_body["tier"]


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_evals_gate_fires_before_eval_runner_import(
    enforce, monkeypatch, method, path
):
    """The gate has to short-circuit the request *before* the handler
    runs. Prove it by installing a distinctive booby-trap
    ``clawmetry.eval_runner`` module: if the gate were missing, the
    handler's ``from clawmetry import eval_runner`` would either succeed
    (leaking a 200) or blow up with an ``AssertionError`` -- neither is
    a 402. The gate short-circuits, so we never reach the import.
    """
    class _Boom:  # pragma: no cover - only hit on regression
        def __getattr__(self, name):
            raise AssertionError(
                f"gate should have short-circuited before "
                f"eval_runner.{name} was reached"
            )

    monkeypatch.setitem(sys.modules, "clawmetry.eval_runner", _Boom())
    monkeypatch.setitem(sys.modules, "clawmetry.eval_regression_replay", _Boom())

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path)
        assert r.status_code == 402


# ── grace mode: gate is transparent on every endpoint ───────────────────────


@pytest.mark.parametrize("method,path", _ENFORCE_MATRIX)
def test_evals_endpoint_is_transparent_in_grace_mode(
    monkeypatch, grace, method, path
):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler runs
    with a stubbed ``clawmetry.eval_runner`` + local-store hop so the
    payload builder is exercised without touching disk.
    """
    _stub_eval_runner(monkeypatch)
    _stub_regression_replay(monkeypatch)
    _stub_store_helpers(monkeypatch)

    body_json = None
    if method == "POST" and path == "/api/evals/key":
        body_json = {"provider": "anthropic", "api_key": "sk-test"}
    if method == "POST" and path == "/api/evals/rubric":
        body_json = {"yaml": "kind: default\n"}

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path, json=body_json)
        assert r.status_code != 402, (
            f"{method} {path} 402'd in grace mode; gate is not transparent"
        )
        body = r.get_json()
        assert isinstance(body, dict)
        # The 402 short-circuit body has ``error="upgrade_required"``;
        # the handler payload never does. Pins that the gate stayed
        # transparent AND the handler emitted its own body.
        assert body.get("error") != "upgrade_required"


def test_evals_recent_grace_payload_shape(monkeypatch, grace):
    """Grace mode: /api/evals/recent must still emit the pre-migration
    ``{evals, limit}`` envelope."""
    _stub_store_helpers(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/evals/recent").get_json()
        assert "evals" in body
        assert body.get("limit") == 50


def test_evals_summary_grace_payload_shape(monkeypatch, grace):
    """Grace mode: /api/evals/summary must still emit the pre-migration
    aggregate envelope."""
    _stub_store_helpers(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/evals/summary").get_json()
        for key in ("avg_score", "total", "scored", "p50", "p10",
                    "window_hours"):
            assert key in body, f"grace payload missing {key!r}"


def test_evals_rubric_grace_payload_shape(monkeypatch, grace):
    """Grace mode: GET /api/evals/rubric must still emit the pre-migration
    ``{yaml, rubric_path, default, enabled}`` envelope."""
    _stub_eval_runner(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/evals/rubric").get_json()
        for key in ("yaml", "rubric_path", "default", "enabled"):
            assert key in body, f"grace payload missing {key!r}"


def test_evals_key_grace_payload_shape(monkeypatch, grace):
    """Grace mode: GET /api/evals/key must still emit the pre-migration
    ``{present, any}`` envelope (no key values leaked)."""
    _stub_eval_runner(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/evals/key").get_json()
        assert "present" in body
        assert "any" in body
        assert body["any"] is False
        # Presence-only endpoint must never echo a raw key back.
        assert "api_key" not in body


def test_evals_regression_summary_grace_payload_shape(monkeypatch, grace):
    """Grace mode: /api/evals/regression-summary must still emit the
    aggregate envelope."""
    _stub_regression_replay(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/evals/regression-summary").get_json()
        for key in ("tested", "improved", "regressed", "same", "errored",
                    "window_days", "last_run_at"):
            assert key in body, f"grace payload missing {key!r}"


# ── /api/evaluators catalogue stays free ────────────────────────────────────


def test_evaluators_catalogue_is_not_gated_in_enforce_mode(monkeypatch, enforce):
    """``/api/evaluators`` is the shop-menu catalogue -- it exposes the
    ``locked: true`` state of Pro evaluators so the dashboard can render
    an upgrade CTA. Gating it too would blank the CTA target under
    enforce mode and break the very upgrade flow it exists to serve.

    So this endpoint deliberately stays free. Pin the split here: if a
    later refactor blanket-gates the whole ``bp_evals`` blueprint
    (rather than the seven paid endpoints), this test fails and calls
    the reviewer's attention to the CTA regression.
    """
    # Even without a store, the catalogue returns the static evaluator
    # list. Any 402 here would signal the wrong-shape gate.
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/evaluators")
        assert r.status_code != 402, (
            "/api/evaluators must not be gated -- it's the shop-menu "
            "catalogue that carries the upgrade CTA."
        )
        body = r.get_json()
        # The catalogue must at least respond with a dict envelope even
        # when the evaluators module has nothing to return; the handler
        # is defensive by design (returns ``{evaluators: [], error: ...}``
        # on catalog import failure).
        assert isinstance(body, dict)


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
    _stub_eval_runner(monkeypatch)
    _stub_regression_replay(monkeypatch)
    _stub_store_helpers(monkeypatch)

    body_json = None
    if method == "POST" and path == "/api/evals/key":
        body_json = {"provider": "anthropic", "api_key": "sk-test"}
    if method == "POST" and path == "/api/evals/rubric":
        body_json = {"yaml": "kind: default\n"}

    app = _make_app()
    with app.test_client() as c:
        r = _call(c, method, path, json=body_json)
        # Graceful fallthrough: NOT 402. Handler runs and returns
        # whatever it would have returned pre-migration (200 with the
        # payload envelope on the happy path, or a 4xx/5xx envelope if
        # a helper raises -- both acceptable, the key is we did not
        # fail closed with a 402).
        assert r.status_code != 402


# ── decorator wiring pin ─────────────────────────────────────────────────────


def test_evals_routes_wear_gate_decorator():
    """All seven paid eval routes must be wired with
    ``@gate("eval_suite")``. Pin this at the module level so a
    well-meaning revert that drops the decorator from any single route
    (leaving a partial gate -- indistinguishable in a single-route grace
    test) fails loudly instead of silently reverting the gate.

    We check by inspecting the source rather than by calling the route
    because the ``@gate`` decorator is transparent in grace mode; a
    regression that dropped it would look identical in grace tests.
    """
    import inspect

    from routes import evals as evals_module

    src = inspect.getsource(evals_module)
    assert 'from clawmetry._gate import gate' in src, (
        "routes/evals.py must import @gate from clawmetry._gate"
    )
    # Exactly seven distinct paid endpoints exist today (recent, summary,
    # rescore, rubric GET+POST, regression-summary, key GET+POST = 8
    # route entries, one route decorator each). If a ninth is added it
    # should also wear the gate, so this pin should be updated in the
    # same PR that adds it (a mismatch is a signal to inspect).
    assert src.count('@gate("eval_suite")') == 8, (
        'routes/evals.py must decorate all eight paid eval routes with '
        '@gate("eval_suite") -- this is the only enforcement point '
        'until the closed-source clawmetry-pro package overrides the '
        'blueprint via the extensions entry point.'
    )
    # The shop-menu catalogue must NOT wear the gate -- gating it would
    # blank the upgrade CTA target under enforce mode.
    catalogue_src = inspect.getsource(evals_module.evaluators_catalogue)
    assert '@gate' not in catalogue_src, (
        "/api/evaluators (the shop-menu catalogue) must stay free; "
        "gating it would blank the upgrade CTA target under enforce."
    )


def test_gate_symbol_is_shared():
    """Wiring pin -- ``routes.evals.gate`` must resolve to the shared
    ``clawmetry._gate.gate`` symbol. A local shadow would defeat the
    shared 402 envelope contract, since the envelope shape is enforced
    by the shared decorator's implementation.
    """
    from routes import evals as evals_module

    assert evals_module.gate.__module__ == "clawmetry._gate"
