"""Enforce/grace-mode contract for the ``/api/health-timeline`` endpoint
in ``routes/overview.py``.

The endpoint returns a per-runtime sparkline of recent-session severity --
it is the surface behind the ``per_runtime_health_timeline`` feature key
in ``clawmetry.entitlements`` (a Starter-tier feature). Every other paid
route on the ``bp_overview`` blueprint stays free (the top-bar overview,
channel list, timeline, cloud-CTA endpoints, device summary, prompt-error
scans, activity heatmap): only the per-runtime health sparkline is paid.

Sibling of ``tests/test_fleet_route_gates.py``,
``tests/test_evals_route_gates.py``, ``tests/test_assets_route_gates.py``,
``tests/test_anomaly_detection_route_gates.py``,
``tests/test_cost_optimizer_route_gates.py``,
``tests/test_audit_route_gate.py``, ``tests/test_otel_export_route_gate.py``,
``tests/test_run_compare_route_gate.py``, and
``tests/test_error_triage_route_gate.py``. Pins the same contract for the
per-runtime health-timeline endpoint so a future edit to
``routes/overview.py`` cannot silently drop the gate:

  1. Enforce mode: ``/api/health-timeline`` returns the shared 402
     ``upgrade_required`` envelope with
     ``feature="per_runtime_health_timeline"`` and
     ``required_tier=TIER_CLOUD_STARTER`` (Starter is the lowest paid
     tier that unlocks Starter features).
  2. Grace mode (default until the enforce-phase release): the gate is
     transparent and the handler runs.
  3. The 402 wire shape is byte-identical to the shared decorator's
     envelope so an existing front-end that already handles 402s from
     ``bp_fleet`` / ``bp_evals`` / ``bp_assets`` keeps working here
     without a special-case branch.
  4. Entitlement-lookup crashes never surface as 402 -- the gate falls
     through and the handler runs (mirrors the defensive contract pinned
     across the other gate tests).
  5. The remaining ``bp_overview`` endpoints stay ungated -- the shell
     endpoints have to stay reachable on OSS installs so the dashboard
     shell renders and the upgrade CTA has somewhere to live.
"""
from __future__ import annotations

import importlib
import inspect

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` -- the tier is oss and
    ``per_runtime_health_timeline`` (a Starter feature) is NOT allowed."""
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
    from routes.overview import bp_overview

    app = Flask(__name__)
    app.register_blueprint(bp_overview)
    return app


def _stub_store_helpers(monkeypatch):
    """Stub ``routes.local_query.local_store_via_daemon`` and the
    ``clawmetry.waste_flags`` helpers the handler leans on so grace-mode
    tests don't require a live daemon / DuckDB. ``local_store_via_daemon``
    returns an empty list -- the handler treats that as "no sessions"
    and emits an empty ``runtimes`` envelope, which is enough to exercise
    the gate + handler path without touching disk.
    """
    import routes.local_query as _lq

    monkeypatch.setattr(
        _lq, "local_store_via_daemon", lambda *_a, **_kw: [], raising=False,
    )


# ── enforce mode: 402 with the shared upgrade-required envelope ─────────────


def test_health_timeline_returns_402_when_enforced(enforce):
    """OSS install + ``CLAWMETRY_ENFORCE=1`` short-circuits with 402 so the
    handler never touches DuckDB / the sessions scan."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/health-timeline")
        assert r.status_code == 402, (
            f"/api/health-timeline returned {r.status_code}, expected 402 "
            "(gate should short-circuit before the sessions scan runs)"
        )
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "per_runtime_health_timeline"
        # Starter feature -- required_tier must be TIER_CLOUD_STARTER so the
        # paywall CTA routes users to Starter (not Pro, not Enterprise).
        assert body["required_tier"] == enforce.TIER_CLOUD_STARTER
        # ``tier`` reflects the caller's current tier so the UI can render
        # the delta ("you have OSS, upgrade to Starter"). On an OSS install
        # with no license, this is TIER_OSS.
        assert body["tier"] == enforce.TIER_OSS
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No timeline payload leaked through -- the gate short-circuited.
        assert "runtimes" not in body
        assert "generated_at" not in body


def test_health_timeline_402_body_shape_matches_shared_gate(enforce):
    """The 402 body carries the exact same top-level keys every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch. Pins that a later refactor of ``@gate`` doesn't
    silently drop ``required_tier`` or ``tier`` on this route.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("per_runtime_health_timeline")
    def _reference_view():  # pragma: no cover - never runs in enforce mode
        return {"ok": True}

    target_app = _make_app()

    with reference_app.test_client() as rc, target_app.test_client() as ac:
        ref_body = rc.get("/reference").get_json()
        act_body = ac.get("/api/health-timeline").get_json()
        assert set(ref_body.keys()) == set(act_body.keys())
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == act_body["feature"]
        assert ref_body["feature"] == "per_runtime_health_timeline"
        assert ref_body["required_tier"] == act_body["required_tier"]
        assert ref_body["tier"] == act_body["tier"]


def test_health_timeline_gate_fires_before_sessions_scan(enforce, monkeypatch):
    """The gate must short-circuit the request *before* the handler runs.
    Prove it by wiring a distinctive booby-trap onto the sessions scan: if
    the gate were missing, the handler's ``local_store_via_daemon`` call
    would either succeed (leaking a 200) or blow up with an
    ``AssertionError`` -- neither is a 402. The gate short-circuits, so we
    never reach the scan.
    """
    import routes.local_query as _lq

    def _boom(*_a, **_kw):  # pragma: no cover - only hit on regression
        raise AssertionError(
            "gate should have short-circuited before the sessions scan ran"
        )

    monkeypatch.setattr(_lq, "local_store_via_daemon", _boom, raising=False)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/health-timeline")
        assert r.status_code == 402


# ── grace mode: gate is transparent ─────────────────────────────────────────


def test_health_timeline_is_transparent_in_grace_mode(monkeypatch, grace):
    """Grace mode (the current default until the enforce-phase release) must
    let the request through unchanged. The downstream handler runs with a
    stubbed store hop so the payload builder is exercised without touching
    disk.
    """
    _stub_store_helpers(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/health-timeline")
        assert r.status_code != 402, (
            "/api/health-timeline 402'd in grace mode; gate is not transparent"
        )
        body = r.get_json()
        assert isinstance(body, dict)
        # The 402 short-circuit body has ``error="upgrade_required"``;
        # the handler payload never does. Pins that the gate stayed
        # transparent AND the handler emitted its own body shape.
        assert body.get("error") != "upgrade_required"


def test_health_timeline_grace_payload_shape(monkeypatch, grace):
    """Grace mode: the handler must still emit the pre-migration
    ``{runtimes, generated_at}`` envelope even when the store is empty.
    Pins the wire shape the dashboard's sparkline widget consumes so an
    unrelated refactor cannot silently break the front-end.
    """
    _stub_store_helpers(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/health-timeline").get_json()
        assert "runtimes" in body
        assert isinstance(body["runtimes"], list)
        assert "generated_at" in body


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_entitlement_lookup_crash_falls_through(monkeypatch, enforce):
    """Mirrors the contract in ``tests/test_route_gates.py``: if the
    entitlement read itself raises, the request path stays defensive and
    the handler runs -- the worst that happens is a paid feature briefly
    runs on a Free tier. A flaky entitlement check must never fail closed.
    """
    def _explode(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)
    _stub_store_helpers(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/health-timeline")
        # Graceful fallthrough: NOT 402. The handler runs and returns
        # whatever it would have returned pre-migration (200 with the
        # payload envelope on the happy path).
        assert r.status_code != 402


# ── decorator wiring pin ─────────────────────────────────────────────────────


def test_health_timeline_wears_gate_decorator():
    """``routes/overview.py`` must wire ``/api/health-timeline`` with
    ``@gate("per_runtime_health_timeline")``. Pin at the source level so a
    well-meaning revert that drops the decorator (indistinguishable in a
    single-route grace test) fails loudly.
    """
    from routes import overview as overview_module

    src = inspect.getsource(overview_module)
    assert "from clawmetry._gate import gate" in src, (
        "routes/overview.py must import @gate from clawmetry._gate"
    )
    handler_src = inspect.getsource(overview_module.api_health_timeline)
    # ``inspect.getsource`` returns the decorator lines above the def when
    # the function is fetched by name, so grepping the source is enough.
    assert '@gate("per_runtime_health_timeline")' in handler_src, (
        'api_health_timeline must be decorated with '
        '@gate("per_runtime_health_timeline") -- this is the only '
        "enforcement point until the closed-source clawmetry-pro package "
        "overrides the endpoint via the extensions entry point."
    )


def test_gate_symbol_is_shared():
    """Wiring pin -- ``routes.overview.gate`` must resolve to the shared
    ``clawmetry._gate.gate`` symbol. A local shadow would defeat the shared
    402 envelope contract, since the envelope shape is enforced by the
    shared decorator's implementation.
    """
    from routes import overview as overview_module

    assert overview_module.gate.__module__ == "clawmetry._gate"


# ── neighbouring bp_overview endpoints stay free ────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "/api/cloud-cta/status",
    ],
)
def test_sibling_bp_overview_endpoints_stay_free(enforce, path):
    """Only ``/api/health-timeline`` is gated on the ``bp_overview``
    blueprint. The shell endpoints have to stay reachable on OSS installs
    so the dashboard shell renders and the upgrade CTA has somewhere to
    live. Pin the split here: if a later refactor blanket-gates the whole
    ``bp_overview`` blueprint (rather than just the paid endpoint), this
    test fails and calls the reviewer's attention to the CTA regression.

    Only the endpoints with no external dependencies are asserted here --
    ``/api/overview``/``/api/timeline``/``/api/channels`` reach into
    ``dashboard`` helpers and the sync daemon and would require broader
    stubbing than "not gated" needs.
    """
    app = _make_app()
    with app.test_client() as c:
        r = c.get(path)
        assert r.status_code != 402, (
            f"{path} 402'd in enforce mode -- shell endpoints must stay "
            "reachable so the OSS dashboard renders."
        )
