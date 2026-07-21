"""Tests for entitlement gating on the fleet (multi-node) JSON API.

Pins the 402 ``upgrade_required`` contract on the 4 endpoints registered by
``routes.fleet_history.bp_fleet`` that implement the paid ``fleet`` feature.
The ``/fleet`` HTML page is intentionally ungated so the shell stays
reachable and can render an upgrade CTA -- see the module docstring on
``routes/fleet_history.py``.

Companion to ``tests/test_route_gates.py`` (feature gating for other paid
surfaces) and ``tests/test_gate_runtime.py`` (runtime gating).
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


def _make_app():
    from routes.fleet_history import bp_fleet

    app = Flask(__name__)
    app.register_blueprint(bp_fleet)
    return app


# ── Enforce mode: OSS install gets 402 on every JSON endpoint ────────────────


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/nodes/register", "POST"),
        ("/api/nodes/node-abc/metrics", "POST"),
        ("/api/nodes", "GET"),
        ("/api/nodes/node-abc", "GET"),
    ],
)
def test_fleet_json_endpoints_return_402_when_enforced(enforce, path, method):
    """Every fleet JSON endpoint short-circuits with 402 on the OSS tier so
    a paid feature never briefly executes in enforce mode. The gate fires
    BEFORE any handler body — the fleet-key auth check, DuckDB open, etc.
    are all downstream of it — so we never touch the daemon or DB in the
    enforced-blocked path."""
    app = _make_app()
    with app.test_client() as c:
        r = c.open(
            path,
            method=method,
            data=json.dumps({}),
            content_type="application/json",
        )
        assert r.status_code == 402, f"{method} {path} returned {r.status_code}"
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "fleet"
        # required_tier lets the UI route to the correct upgrade CTA
        # (Starter, not Pro or Enterprise -- fleet is a Starter-tier feature).
        assert body["required_tier"] == enforce.TIER_CLOUD_STARTER


def test_fleet_402_body_carries_current_tier(enforce):
    """The 402 body includes ``tier`` = current install tier so the UI can
    distinguish "OSS user hitting fleet" from "Trial expired" without a
    second entitlement fetch."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/nodes")
        assert r.status_code == 402
        body = r.get_json()
        assert body["tier"] == enforce.TIER_OSS


# ── Grace mode: no gate short-circuit — request proceeds to handler body ─────


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/nodes/register", "POST"),
        ("/api/nodes/node-abc/metrics", "POST"),
        ("/api/nodes", "GET"),
        ("/api/nodes/node-abc", "GET"),
    ],
)
def test_fleet_json_endpoints_pass_in_grace_mode(grace, monkeypatch, path, method):
    """Grace mode (default until the enforce-phase release) is transparent:
    the gate lets every fleet call through unchanged. Downstream handler
    behaviour is out of scope for this suite — we only need to prove the
    gate did NOT short-circuit with 402. The write endpoints hit the
    fleet-key auth check and return 401; the read endpoints reach the
    handler body which we stub off to avoid needing a real DuckDB."""
    # Stub out the dashboard helpers the read endpoints use so we don't need
    # a running daemon / DuckDB. Any non-402 outcome is fine — we assert on
    # "not 402" (the gate short-circuit) rather than 200 specifically.
    import dashboard as _d

    monkeypatch.setattr(_d, "_fleet_check_key", lambda _r: False, raising=False)
    monkeypatch.setattr(_d, "_fleet_update_statuses", lambda: None, raising=False)

    app = _make_app()
    with app.test_client() as c:
        r = c.open(
            path,
            method=method,
            data=json.dumps({}),
            content_type="application/json",
        )
        assert r.status_code != 402, (
            f"{method} {path} returned 402 in grace mode — gate should be transparent"
        )


# ── /fleet HTML shell stays reachable so the UI can render its own CTA ───────


def test_fleet_html_page_is_not_gated(enforce, monkeypatch):
    """The ``/fleet`` HTML page is intentionally ungated. In enforce mode
    the shell still loads so the front-end can render an upgrade CTA in
    context — a 402 on the whole page would leave the user stranded with a
    raw JSON error. Only the JSON API endpoints (which paid features
    actually use) are gated."""
    # Stub the FLEET_HTML constant so the handler doesn't need the full
    # dashboard template to load in the test process.
    import dashboard as _d

    monkeypatch.setattr(_d, "FLEET_HTML", "<html>fleet</html>", raising=False)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/fleet")
        assert r.status_code != 402, (
            "/fleet HTML must stay reachable in enforce mode so the UI can "
            "render the upgrade CTA."
        )


# ── Defensive: entitlement lookup failure never blocks a fleet call ──────────


def test_fleet_gate_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement resolver itself raises, the gate swallows the
    error and lets the request through — the audit chain still records
    the call and the worst case is a paid feature briefly running on
    Free. A flaky entitlement read must never break the request path."""
    from clawmetry import entitlements

    def _explode(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(entitlements, "get_entitlement", _explode)

    # Stub the dashboard helpers to avoid daemon/DB deps on the fallthrough.
    import dashboard as _d

    monkeypatch.setattr(_d, "_fleet_update_statuses", lambda: None, raising=False)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/nodes")
        assert r.status_code != 402, (
            "Entitlement lookup errors must not surface as 402 — the gate "
            "should fall through and let the handler run."
        )
