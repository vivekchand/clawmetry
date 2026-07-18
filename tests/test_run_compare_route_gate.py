"""Enforce-mode contract tests for the ``/api/run-compare`` endpoint gate.

``per_run_compare`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``). ``/api/run-compare`` lives on ``bp_sessions``
(``routes/sessions.py``) and wears ``@gate("per_run_compare")`` so its 402
body carries the same ``feature`` / ``tier`` / ``required_tier`` envelope
every other ``@gate``-migrated route returns (matches the pattern in
``tests/test_assets_route_gates.py``, ``tests/test_audit_route_gate.py``,
``tests/test_fleet_route_gates.py``, ``tests/test_otel_export_route_gate.py``).

Pins:

  1. Enforce mode: the endpoint returns 402 ``upgrade_required`` with
     ``feature="per_run_compare"`` and ``required_tier=TIER_CLOUD_PRO``.
     The gate short-circuits before any handler code runs, so no daemon
     / DuckDB path is touched.
  2. Enforce mode: the 402 wins over the endpoint's own missing-param 400
     validation. A caller that hits ``/api/run-compare`` with no ``a`` /
     ``b`` still gets the paywall body (so the UI renders the upgrade CTA,
     not a validation error).
  3. Grace mode: the gate is transparent. Whatever the downstream handler
     returns (a 400 on missing params, a 200 on a valid pair) wins; the
     response is not a 402.
  4. Defensive fallthrough: an entitlement-lookup crash never surfaces as
     402 (mirrors ``tests/test_route_gates.py``'s contract).
  5. Decorator wiring pin: static-source assertion that
     ``from clawmetry._gate import gate`` and ``@gate("per_run_compare")``
     are both present in ``routes/sessions.py``. A well-meaning revert
     that drops the decorator (leaving the endpoint unguarded,
     indistinguishable in grace-mode tests) fails loudly here.
"""
from __future__ import annotations

import importlib
from pathlib import Path

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


def _app_with_sessions_bp():
    from routes.sessions import bp_sessions

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    return app


# ── enforce mode: 402 on the endpoint ────────────────────────────────────────


def test_run_compare_returns_402_when_enforced(enforce):
    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare?a=run-a&b=run-b")
        assert r.status_code == 402, (
            f"/api/run-compare returned {r.status_code}, expected 402 "
            "(gate should short-circuit before handler runs)"
        )
        payload = r.get_json()
        assert payload["error"] == "upgrade_required"
        assert payload["feature"] == "per_run_compare"
        assert payload["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier so the UI can render
        # the delta ("you have X, upgrade to Y"). On an OSS install with no
        # license, this is TIER_OSS.
        assert payload["tier"] == enforce.TIER_OSS


def test_enforce_mode_402_precedes_query_validation(enforce):
    """Gate must fire before query-param validation. A GET with no ``a`` /
    ``b`` params would normally 400 with ``missing 'a' or 'b' query
    parameter``; in enforce mode it should still 402 so the UI renders
    the upgrade CTA, not a validation error."""
    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare")  # no params at all
        assert r.status_code == 402
        assert r.get_json()["feature"] == "per_run_compare"


def test_enforce_mode_402_precedes_same_id_validation(enforce):
    """Same as above for the ``a == b`` rejection path — 402 wins over the
    handler's own 400 branch, so the UI never renders the "'a' and 'b' must
    be different" copy on a paid tier."""
    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare?a=same&b=same")
        assert r.status_code == 402
        assert r.get_json()["feature"] == "per_run_compare"


def test_enforce_mode_402_does_not_touch_daemon(monkeypatch, enforce):
    """Static proof the gate short-circuits before the daemon proxy runs.

    Booby-trap ``routes.local_query.local_store_via_daemon`` so any call
    to it raises ``AssertionError``. In enforce mode we still get a clean
    402 back — i.e. the paywall check landed before the handler could
    reach the DuckDB layer. If the gate ever regresses to run after the
    handler body, this test fails loudly.
    """
    def _boom(*a, **kw):
        raise AssertionError("daemon proxy must not be reached in enforce mode")

    import routes.local_query as _lq_mod
    monkeypatch.setattr(_lq_mod, "local_store_via_daemon", _boom)

    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare?a=run-a&b=run-b")
        assert r.status_code == 402
        assert r.get_json()["feature"] == "per_run_compare"


# ── grace mode: gate is transparent ──────────────────────────────────────────


def test_run_compare_missing_params_is_400_in_grace_mode(grace):
    """Grace mode leaves the handler's own 400 validation alone — the gate
    is a no-op, so a caller with no ``a`` / ``b`` still gets the pre-gate
    400 body, not a 402. Pins that the decorator hasn't been misconfigured
    to always fire."""
    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare")
        assert r.status_code == 400, (
            f"/api/run-compare returned {r.status_code}, expected 400 "
            "(handler's own missing-param branch, not a 402)"
        )
        # Body carries the handler's own error copy; NOT the gate's paywall body.
        payload = r.get_json()
        assert payload.get("error", "").startswith("missing"), payload
        assert "feature" not in payload


def test_run_compare_valid_pair_is_not_402_in_grace_mode(monkeypatch, grace):
    """A valid pair returns whatever the handler would have returned. Stub
    the DuckDB path so the handler runs deterministically in-process without
    the sync daemon. The gate should be transparent; only pin that the
    response is NOT a 402."""
    def _stub_daemon(method, **kwargs):
        if method == "query_session_quality":
            return {}
        if method == "query_sessions":
            return []
        if method == "query_events":
            return []
        return None

    import routes.local_query as _lq_mod
    monkeypatch.setattr(_lq_mod, "local_store_via_daemon", _stub_daemon)

    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare?a=run-a&b=run-b")
        assert r.status_code != 402, (
            f"/api/run-compare 402'd in grace mode; gate is not transparent"
        )


# ── defensive: an entitlement-lookup crash falls through, does NOT 402 ──────


def test_entitlement_lookup_crash_falls_through(monkeypatch, enforce):
    """Mirrors the contract in tests/test_route_gates.py: if the entitlement
    read itself raises, the request path stays defensive and the handler
    runs — the worst that happens is a paid feature briefly runs on a Free
    tier. A flaky entitlement check must never fail closed."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    def _stub_daemon(method, **kwargs):
        return [] if method in ("query_sessions", "query_events") else {}

    import routes.local_query as _lq_mod
    monkeypatch.setattr(_lq_mod, "local_store_via_daemon", _stub_daemon)

    app = _app_with_sessions_bp()
    with app.test_client() as c:
        r = c.get("/api/run-compare?a=run-a&b=run-b")
        assert r.status_code != 402


# ── decorator wiring pin: source-level guard against silent reverts ──────────


def test_run_compare_source_has_gate_decorator():
    """A future revert of the ``@gate`` decorator would leave the endpoint
    open in grace mode (indistinguishable from the transparent-gate test)
    AND open in enforce mode (silently free again). Pin the wiring at the
    source level so a well-meaning cleanup breaks CI here first, loud."""
    src = Path(__file__).resolve().parents[1] / "routes" / "sessions.py"
    text = src.read_text(encoding="utf-8")
    assert "from clawmetry._gate import gate" in text, (
        "routes/sessions.py must import the shared gate decorator"
    )
    assert '@gate("per_run_compare")' in text, (
        "routes/sessions.py must decorate /api/run-compare with "
        '@gate("per_run_compare") -- do not remove without moving the '
        "endpoint off the per_run_compare feature key"
    )
