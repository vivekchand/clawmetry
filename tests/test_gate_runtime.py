"""Tests for the runtime-level gate decorator + inline helper.

Pins the 402 ``upgrade_required`` contract for routes that gate on a
specific runtime (``claude_code``, ``codex``, ...) rather than a feature
key. Companion to ``tests/test_route_gates.py`` (feature gating) and
``tests/test_entitlements_catalogue.py`` (catalogue invariants).

Grace mode (default) always passes through, including for paid runtimes,
so wiring a runtime gate into a route changes no current behaviour. Once
``CLAWMETRY_ENFORCE=1`` flips on, paid runtimes return the structured
402 body the dashboard already knows how to render.
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


# -- @gate_runtime decorator contract -----------------------------------------


def test_gate_runtime_blocks_paid_runtime_in_enforce_mode(enforce):
    """A paid runtime on an OSS-free install returns 402 with the runtime
    id, current tier, and an upgrade hint."""
    from clawmetry._gate import gate_runtime

    app = Flask(__name__)

    @app.route("/test")
    @gate_runtime("claude_code")
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"
        assert "tier" in body
        assert "hint" in body


@pytest.mark.parametrize("free_rt", ["openclaw", "nemoclaw"])
def test_gate_runtime_passes_free_runtimes_even_when_enforced(enforce, free_rt):
    """The free-tier runtimes always pass through, regardless of enforce
    mode -- they're free in every plan including OSS."""
    from clawmetry._gate import gate_runtime

    app = Flask(__name__)

    @app.route("/test")
    @gate_runtime(free_rt)
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}


@pytest.mark.parametrize(
    "paid_rt",
    ["claude_code", "codex", "cursor", "aider", "goose"],
)
def test_gate_runtime_passes_paid_runtimes_in_grace_mode(grace, paid_rt):
    """Grace mode (default) lets every known runtime through so wiring the
    gate in changes no current behaviour. Enforcement is opt-in via
    ``CLAWMETRY_ENFORCE=1``."""
    from clawmetry._gate import gate_runtime

    app = Flask(__name__)

    @app.route("/test")
    @gate_runtime(paid_rt)
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}


def test_gate_runtime_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request still goes
    through (mirrors the ``@gate`` defensive fallback). A flaky entitlement
    check must never break the request path."""
    from clawmetry._gate import gate_runtime

    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", explode)

    app = Flask(__name__)

    @app.route("/test")
    @gate_runtime("claude_code")
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 200  # graceful fallthrough


# -- require_runtime() inline helper contract ---------------------------------


def test_require_runtime_returns_none_for_free_runtime(enforce):
    """Free runtimes return ``None`` so the caller falls through to its
    normal logic."""
    from clawmetry._gate import require_runtime

    assert require_runtime("openclaw") is None
    assert require_runtime("nemoclaw") is None


def test_require_runtime_returns_402_for_paid_runtime_when_enforced(enforce):
    """Inline form returns a Flask response tuple (body, status) for the
    caller to ``return`` directly."""
    from clawmetry._gate import require_runtime

    app = Flask(__name__)
    with app.test_request_context("/test"):
        result = require_runtime("claude_code")
        assert result is not None
        resp, status = result
        assert status == 402
        body = resp.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"


def test_require_runtime_normalises_case_and_whitespace(enforce):
    """Runtime ids are matched case-insensitively after trimming so a
    request that sends ``"Claude_Code"`` or ``" codex "`` still hits the
    gate."""
    from clawmetry._gate import require_runtime

    app = Flask(__name__)
    with app.test_request_context("/test"):
        # Paid runtime with messy casing still gated.
        blocked = require_runtime("  Claude_Code  ")
        assert blocked is not None
        assert blocked[1] == 402
        # Free runtime with messy casing still passes.
        assert require_runtime("  OpenClaw  ") is None


def test_require_runtime_passes_in_grace_mode(grace):
    """Grace mode (default) returns ``None`` for every runtime so existing
    request paths see no change until enforcement is on."""
    from clawmetry._gate import require_runtime

    for rt in ("openclaw", "nemoclaw", "claude_code", "codex", "totally_unknown"):
        assert require_runtime(rt) is None


def test_require_runtime_swallows_lookup_errors(enforce, monkeypatch):
    """A failing entitlement read returns ``None`` rather than propagating
    -- the request path keeps working even on a partially-broken install."""
    from clawmetry._gate import require_runtime

    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", explode)
    assert require_runtime("claude_code") is None


def test_require_runtime_unknown_runtime_returns_402_when_enforced(enforce):
    """Unknown runtime ids (typo, future runtime, plugin) are NOT in
    ``FREE_RUNTIMES`` so enforce mode rejects them -- opt-in only via the
    entitled set, the same posture as the catalogue contract."""
    from clawmetry._gate import require_runtime

    app = Flask(__name__)
    with app.test_request_context("/test"):
        result = require_runtime("totally_unknown_xyz")
        assert result is not None
        assert result[1] == 402


# -- required_tier + alias canonicalisation -----------------------------------


def test_require_runtime_402_body_includes_required_tier(enforce):
    """The 402 body carries the cheapest purchasable tier that unlocks the
    runtime so the dashboard can render the correct upgrade CTA without
    re-deriving tier logic in JS. Mirrors the ``@gate`` feature contract."""
    from clawmetry._gate import require_runtime
    from clawmetry import entitlements as _ent

    app = Flask(__name__)
    with app.test_request_context("/test"):
        resp, status = require_runtime("claude_code")
        assert status == 402
        body = resp.get_json()
        assert body["required_tier"] == _ent.TIER_CLOUD_STARTER


def test_gate_runtime_402_body_includes_required_tier(enforce):
    """``@gate_runtime`` shares the same 402 body shape as the inline form,
    so it surfaces ``required_tier`` too."""
    from clawmetry._gate import gate_runtime
    from clawmetry import entitlements as _ent

    app = Flask(__name__)

    @app.route("/test")
    @gate_runtime("codex")
    def view():
        return {"ok": True}

    with app.test_client() as c:
        r = c.get("/test")
        assert r.status_code == 402
        body = r.get_json()
        assert body["required_tier"] == _ent.TIER_CLOUD_STARTER


def test_require_runtime_402_body_required_tier_none_for_unknown(enforce):
    """Unknown runtimes have no known purchasable tier, so ``required_tier``
    is ``None`` rather than absent -- the field is part of the contract."""
    from clawmetry._gate import require_runtime

    app = Flask(__name__)
    with app.test_request_context("/test"):
        resp, status = require_runtime("totally_unknown_xyz")
        assert status == 402
        body = resp.get_json()
        assert "required_tier" in body
        assert body["required_tier"] is None


@pytest.mark.parametrize(
    "alias",
    ["open-claw", "open_claw", "nemo-claw", "nemo_claw"],
)
def test_require_runtime_canonicalises_free_runtime_aliases(enforce, alias):
    """Aliases for the FREE runtimes (``open-claw`` → ``openclaw``) must
    pass through even in enforce mode -- they map onto a free runtime."""
    from clawmetry._gate import require_runtime

    app = Flask(__name__)
    with app.test_request_context("/test"):
        assert require_runtime(alias) is None


@pytest.mark.parametrize(
    "alias",
    ["claude-code", "claudecode", "qwen-code", "qwencode"],
)
def test_require_runtime_canonicalises_paid_runtime_aliases(enforce, alias):
    """Aliases for paid runtimes still get gated, and the 402 body reports
    the *canonical* runtime id so the UI can render its proper label."""
    from clawmetry._gate import require_runtime
    from clawmetry import entitlements as _ent

    app = Flask(__name__)
    with app.test_request_context("/test"):
        result = require_runtime(alias)
        assert result is not None
        resp, status = result
        assert status == 402
        body = resp.get_json()
        assert body["runtime"] == _ent.canonical_runtime(alias)
        assert body["required_tier"] == _ent.TIER_CLOUD_STARTER
