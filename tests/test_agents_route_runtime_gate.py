"""Runtime-gate wiring for the per-agent sessions endpoint on ``bp_agents``.

``/api/agents/<name>/sessions`` returns per-runtime session data, so it is
gated with :func:`clawmetry._gate.require_runtime` — the same contract
``dashboard_claudecode.py`` enforces with ``@gate_runtime("claude_code")``
on its JSON endpoints. This module pins the contract on the real
``routes/agents.py`` blueprint that ``dashboard.py`` registers:

* Enforce mode + OSS-free install → paid-runtime session listings return
  402 with ``error="upgrade_required"``, ``runtime=<canonical>``, and
  ``required_tier=cloud_starter`` (mirrors ``tests/test_claudecode_runtime_gate``
  / ``routes/fleet_history.py``).
* Enforce mode + free runtime (``openclaw``, ``nemoclaw``) → gate passes
  through unchanged.
* Grace mode (the default) → gate is transparent for both free and paid
  runtimes so wiring the gate in does not shift any current behaviour.
* Runtime aliases (``claude-code``) canonicalise before the gate so an
  alias for a paid runtime still 402s consistently in enforce mode.
* The two detection endpoints (``/api/agents``, ``/api/agents/<name>``)
  intentionally stay ungated — the UI needs them in enforce mode to
  render locked runtime chips + an upgrade CTA. Mirrors the
  ``bp_claudecode`` decision to keep ``/api/health`` reachable.
* A flaky entitlement read never surfaces as 402 — the request falls
  through, matching the defensive contract in
  ``tests/test_route_gates.py`` and ``tests/test_claudecode_runtime_gate``.
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
    from routes.agents import bp_agents

    app = Flask(__name__)
    app.register_blueprint(bp_agents)
    return app


# One per PAID_RUNTIMES entry — the gate must 402 for every paid runtime,
# not just the (currently) most common one. Kept in lockstep with
# ``clawmetry.entitlements.PAID_RUNTIMES``; adding a new paid runtime
# there flows through this parametrisation automatically.
def _paid_runtime_ids():
    from clawmetry import entitlements as _ent
    return sorted(_ent.PAID_RUNTIMES)


@pytest.mark.parametrize("runtime", _paid_runtime_ids())
def test_paid_runtime_sessions_returns_402_when_enforced(enforce, runtime):
    app = _make_app()
    with app.test_client() as c:
        r = c.get(f"/api/agents/{runtime}/sessions")
        assert r.status_code == 402, (
            f"/api/agents/{runtime}/sessions → {r.status_code}"
        )
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == runtime
        assert body["required_tier"] == enforce.TIER_CLOUD_STARTER
        assert "hint" in body
        assert "tier" in body


@pytest.mark.parametrize("runtime", ["openclaw", "nemoclaw"])
def test_free_runtime_sessions_passes_through_when_enforced(enforce, runtime):
    """FREE_RUNTIMES must never 402 — even in enforce mode. The gate has to
    stay transparent for the OSS runtimes, otherwise every install would
    lose its own sessions view when enforcement flips on."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get(f"/api/agents/{runtime}/sessions")
        assert r.status_code != 402, (
            f"/api/agents/{runtime}/sessions unexpectedly 402'd for a free runtime"
        )


@pytest.mark.parametrize("runtime", ["claude_code", "openclaw", "codex"])
def test_sessions_transparent_in_grace_mode(grace, runtime):
    """Grace mode is the default until enforcement flips on; the wiring
    must not shift any current behaviour. Downstream may return 200-empty
    or 5xx depending on filesystem state — we only need to confirm the
    gate did NOT short-circuit with 402."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get(f"/api/agents/{runtime}/sessions")
        assert r.status_code != 402, (
            f"/api/agents/{runtime}/sessions unexpectedly gated in grace mode: "
            f"{r.status_code}"
        )


@pytest.mark.parametrize("alias,canonical", [
    ("claude-code", "claude_code"),
    ("claudecode", "claude_code"),
    ("qwen-code", "qwen_code"),
    ("deep-agents", "deepagents"),
])
def test_paid_runtime_alias_still_402s(enforce, alias, canonical):
    """``require_runtime`` canonicalises the runtime id (``claude-code`` →
    ``claude_code``) before the entitlement check, so an alias for a paid
    runtime still 402s with the canonical id echoed back."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get(f"/api/agents/{alias}/sessions")
        assert r.status_code == 402
        body = r.get_json()
        assert body["runtime"] == canonical


def test_top_level_agents_list_stays_reachable_in_enforce_mode(enforce):
    """``/api/agents`` renders the multi-agent chip bar (locked + unlocked
    together) so the UI can render an upgrade CTA on locked chips. Gating
    it would leave enforced installs with an empty chip bar and no way to
    discover paid runtimes exist. Mirrors ``routes/fleet_history.py``
    keeping ``/fleet`` reachable and ``dashboard_claudecode.py`` keeping
    ``/api/health`` reachable."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/agents")
        assert r.status_code != 402


def test_paid_agent_detail_stays_reachable_in_enforce_mode(enforce):
    """``/api/agents/<name>`` returns adapter ``detect()`` output — an
    install-probe (does the runtime workspace exist?), not the runtime's
    data. The UI needs it in enforce mode to distinguish "not installed"
    from "installed but not entitled" — otherwise the upgrade CTA can't
    render the right copy. Parallels ``dashboard_claudecode.py``'s
    decision to keep ``/api/health`` ungated."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/agents/claude_code")
        assert r.status_code != 402


def test_gate_swallows_entitlement_lookup_errors(enforce, monkeypatch):
    """A flaky entitlement read must never break the request path — the
    worst that happens is a paid runtime briefly serves a Free tier.
    Mirrors ``tests/test_gate_runtime.py::
    test_gate_runtime_never_raises_when_entitlement_lookup_fails``."""

    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", explode)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/agents/claude_code/sessions")
        assert r.status_code != 402


def test_gate_precedes_downstream_lookup_in_enforce_mode(enforce):
    """A path parameter that would normally hit a downstream ``Unknown
    agent: <name>`` 404 must still return 402 in enforce mode for a paid
    runtime — the upgrade CTA has to win, otherwise the UI would render
    "unknown agent" for a non-entitled user instead of the upgrade path.
    Mirrors the pattern pinned in ``tests/test_claudecode_runtime_gate.py::
    test_bp_claudecode_gate_precedes_downstream_errors_in_enforce_mode``."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/agents/claude_code/sessions")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"
