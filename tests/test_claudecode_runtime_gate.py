"""Runtime-gate wiring for ``bp_claudecode`` JSON endpoints.

The Claude Code dashboard variant (``dashboard_claudecode.py``) is the first
route surface to gate on a *runtime* rather than a *feature*. It uses
``@gate_runtime("claude_code")`` because ``claude_code`` sits in
``PAID_RUNTIMES`` — every non-``openclaw``/``nemoclaw`` runtime ships in the
closed-source ``clawmetry-pro`` package.

Pins the same contract ``tests/test_gate_runtime.py`` already covers on
synthetic Flask views, but on the real blueprint that ``dashboard.py``
registers:

* Enforce mode + OSS-free install → every JSON endpoint returns 402 with
  ``feature="upgrade_required"``, ``runtime="claude_code"``, and
  ``required_tier=cloud_starter`` (mirrors ``routes/fleet_history.py`` /
  ``routes/assets.py`` in what the frontend can key off).
* Grace mode (the default) → the gate is transparent so the request path is
  unchanged. Wiring the gate in must not shift any current behaviour.
* The ``/`` HTML shell and ``/favicon.ico`` stay reachable in enforce mode
  so the frontend can render an upgrade CTA in context, matching the choice
  ``routes/fleet_history.py`` made for ``/fleet``.
* A crashing entitlement read never surfaces as 402 — mirrors the
  defensive-fallthrough contract in ``tests/test_route_gates.py``.
"""
from __future__ import annotations

import importlib

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


def _make_app():
    from dashboard_claudecode import bp_claudecode

    app = Flask(__name__)
    app.register_blueprint(bp_claudecode)
    return app


# JSON endpoints that must go through @gate_runtime("claude_code"). The
# ``/`` HTML shell and ``/favicon.ico`` are intentionally NOT here.
_GATED_JSON = [
    ("/api/sessions", "GET"),
    ("/api/session/sid-123", "GET"),
    ("/api/analytics", "GET"),
    ("/api/projects", "GET"),
]


@pytest.mark.parametrize("path,method", _GATED_JSON)
def test_bp_claudecode_json_returns_402_when_enforced(enforce, path, method):
    app = _make_app()
    with app.test_client() as c:
        r = c.open(path, method=method)
        assert r.status_code == 402, f"{method} {path} → {r.status_code}"
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"
        assert body["required_tier"] == enforce.TIER_CLOUD_STARTER
        assert "hint" in body
        # The current tier is echoed so the UI can render "You're on
        # <tier>. Upgrade to <required_tier> to unlock claude_code."
        assert "tier" in body


@pytest.mark.parametrize("path,method", _GATED_JSON)
def test_bp_claudecode_json_transparent_in_grace_mode(grace, path, method):
    """Grace mode is the default until enforcement flips on; the wiring
    must not shift any current request path. The downstream handler may
    return anything from 200-empty to 500 depending on filesystem state --
    we only need to confirm the gate did NOT short-circuit with 402."""
    app = _make_app()
    with app.test_client() as c:
        r = c.open(path, method=method)
        assert r.status_code != 402, (
            f"{method} {path} unexpectedly gated in grace mode: {r.status_code}"
        )


def test_bp_claudecode_html_index_stays_reachable_in_enforce_mode(enforce):
    """The ``/`` HTML shell has to load in enforce mode so the frontend can
    render an upgrade CTA in context. A 402 on the whole page would leave
    the user stranded with a raw JSON error instead of a navigable page.
    Mirrors what ``routes/fleet_history.py`` does for ``/fleet``."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/")
        # Any 2xx is fine (200 today). What matters is that it's NOT 402.
        assert r.status_code != 402


def test_bp_claudecode_favicon_stays_reachable_in_enforce_mode(enforce):
    """The favicon is a static asset the browser fetches whenever the HTML
    shell loads. Gating it would leak a 402 into the network tab on every
    page load even after the user has dismissed the upgrade CTA."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/favicon.ico")
        assert r.status_code != 402


def test_bp_claudecode_health_stays_reachable_in_enforce_mode(enforce):
    """The ``/api/health`` endpoint is a diagnostics probe (does the
    process see the Claude Code home?). Gating it would make the frontend
    unable to distinguish "runtime not installed" from "not entitled",
    both of which the CTA needs to render differently."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/health")
        assert r.status_code != 402


def test_bp_claudecode_gate_swallows_entitlement_lookup_errors(
    enforce, monkeypatch
):
    """A flaky entitlement read must never break the request path -- the
    worst that happens is a paid runtime briefly serves a Free tier.
    Mirrors ``tests/test_gate_runtime.py::
    test_gate_runtime_never_raises_when_entitlement_lookup_fails``."""

    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", explode)

    app = _make_app()
    with app.test_client() as c:
        # Any of the gated JSON paths — a lookup crash falls through, so we
        # should see the downstream handler run (may be 2xx or 5xx, but
        # never 402).
        r = c.get("/api/sessions")
        assert r.status_code != 402


def test_bp_claudecode_gate_precedes_downstream_errors_in_enforce_mode(
    enforce,
):
    """A path parameter that would normally hit a downstream 404 (session
    not found) must still return 402 in enforce mode -- the upgrade CTA
    has to win, otherwise the UI would render "session not found" for a
    non-entitled user instead of the upgrade path. Mirrors the assets PR:
    ``@gate`` precedes body validation on ``POST /api/assets``."""
    app = _make_app()
    with app.test_client() as c:
        # Non-existent session id would normally 404 downstream.
        r = c.get("/api/session/does-not-exist")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"
