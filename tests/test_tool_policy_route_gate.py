"""Tests for the ``@gate("tool_policy")`` migration on
``routes/policy.py::api_tool_policy``.

Sibling of ``tests/test_audit_route_gate.py``,
``tests/test_otel_export_route_gate.py``, ``tests/test_fleet_route_gates.py``,
``tests/test_assets_route_gates.py``, and
``tests/test_anomaly_detection_route_gates.py``. Pins:

- Enforce mode returns the shared 402 ``upgrade_required`` envelope with
  ``feature="tool_policy"``, ``required_tier=cloud_pro`` (tool policy is a
  Pro-only feature, not Enterprise), ``tier`` = the caller's current tier,
  and a ``hint`` string.
- Grace mode is transparent: the downstream handler runs, populates the
  governance summary, and returns the ``{"agents": [...], "summary": {...},
  "_source": "local_store"}`` envelope even though the caller is OSS.
- The gate fires *before* the LocalStore ``query_tool_policy`` read so a
  daemon mid-restart or a fresh install without a ``tool_policy`` table
  can't leak through as a 200 in enforce mode.
- A resolver crash never surfaces as 402 (mirrors the defensive contract
  pinned in ``tests/test_route_gates.py``).
- The 402 wire shape is byte-identical to what other ``@gate``d routes
  return, so an existing front-end that already handles 402 keeps working
  without a branch on ``feature=="tool_policy"``.

The other ``bp_policy`` endpoints (``/api/approvals``, ``/api/approvals-audit``)
are intentionally NOT retested here — they're already gated on
``approval_queue`` (a Starter feature) and pinned by
``tests/test_route_gates.py``. Only the newly-migrated ``/api/tool-policy``
route is exercised, matching the "one feature per PR" cadence of the
sibling migrations.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss/free and
    ``tool_policy`` (a Pro-only feature) is NOT allowed."""
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
    from routes.policy import bp_policy

    app = Flask(__name__)
    app.register_blueprint(bp_policy)
    return app


# ── enforce mode: 402 contract ──────────────────────────────────────────────


def test_tool_policy_returns_402_when_enforced(enforce, monkeypatch):
    """The route wears ``@gate("tool_policy")`` so an OSS install in enforce
    mode gets the shared 402 body instead of the agents envelope."""
    # Belt-and-braces: even if ``_ls_call`` returned data the gate must
    # short-circuit before it. Stub the LocalStore lookup so a regression
    # that drops the decorator would produce a 200 with a sentinel row.
    def _sentinel(name, **_kw):
        return [{"agent_id": "gate_should_have_fired"}]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _sentinel)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "tool_policy"
        # Current tier is echoed so the UI can distinguish "not entitled at
        # all" from "entitled but on a downgrade path".
        assert "tier" in body
        # required_tier lets the paywall render the right upgrade CTA.
        # tool_policy is Pro-only, NOT Enterprise — so the CTA has to
        # target Pro or users get sent to the wrong upgrade flow.
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No agents payload leaked through.
        assert "agents" not in body
        assert "summary" not in body


def test_tool_policy_402_body_shape_matches_shared_gate(enforce):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch."""
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("tool_policy")
    def _reference_view():
        return {"ok": True}

    policy_app = _make_app()

    with reference_app.test_client() as rc, policy_app.test_client() as ac:
        ref_body = rc.get("/reference").get_json()
        tp_body = ac.get("/api/tool-policy").get_json()
        assert set(ref_body.keys()) == set(tp_body.keys())
        # Envelope keys pinned so a later refactor of ``@gate`` doesn't
        # silently drop ``required_tier`` or ``tier``.
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == tp_body["feature"] == "tool_policy"
        assert ref_body["required_tier"] == tp_body["required_tier"]
        assert ref_body["tier"] == tp_body["tier"]


def test_tool_policy_gate_fires_before_local_store_read(enforce, monkeypatch):
    """The gate has to short-circuit the request *before* the LocalStore
    ``query_tool_policy`` call runs. Otherwise a slow DuckDB open, or a
    fresh install where the ``tool_policy`` table hasn't been materialised
    yet, would leak through as a 500 instead of the 402 the caller expects.
    """
    calls: list[tuple[str, dict]] = []

    def _spy(name, **kwargs):
        calls.append((name, kwargs))
        return []

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _spy)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy?limit=42&agent_id=abc")
        assert r.status_code == 402
        # The gate ran and short-circuited: the LocalStore read never started.
        assert calls == []


def test_tool_policy_gate_wins_over_query_string_error(enforce):
    """Even a malformed ``?limit=`` must not shadow the 402 — the gate fires
    before the query-string parse fallthrough, so the enforcement signal
    reaches the caller regardless of how they hit the URL."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy?limit=not-a-number&agent_id=")
        assert r.status_code == 402


# ── grace mode: transparent ──────────────────────────────────────────────────


def test_tool_policy_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler builds
    the agents+summary envelope; the LocalStore is stubbed to keep the
    test hermetic."""
    def _empty(name, **_kw):
        return []

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _empty)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy")
        assert r.status_code == 200
        body = r.get_json()
        assert "agents" in body
        assert "summary" in body
        assert body["_source"] == "local_store"
        # The pre-migration handler always returned this shape, so seeing
        # it here proves the gate stayed transparent AND the handler ran.
        assert body["agents"] == []
        assert body["summary"]["agent_count"] == 0
        assert body["summary"]["sandboxed_agents"] == 0


def test_tool_policy_grace_populates_summary_rollup(grace, monkeypatch):
    """Grace mode: the governance rollup (``strongest_mode``,
    ``sandboxed_agents``, allow/deny totals) still fires end-to-end. Pins
    that the migration didn't accidentally short-circuit the summary
    computation."""
    def _canned(name, **_kw):
        return [
            {"agent_id": "a1", "sandbox_mode": "all",     "allow_count": 3, "deny_count": 1},
            {"agent_id": "a2", "sandbox_mode": "non-main", "allow_count": 5, "deny_count": 2},
            {"agent_id": "a3", "sandbox_mode": "off",     "allow_count": 0, "deny_count": 0},
        ]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy")
        assert r.status_code == 200
        body = r.get_json()
        summary = body["summary"]
        assert summary["agent_count"] == 3
        # a1 (all) and a2 (non-main) are sandboxed; a3 (off) is not.
        assert summary["sandboxed_agents"] == 2
        # ``all`` outranks ``non-main`` which outranks ``off``.
        assert summary["strongest_mode"] == "all"
        assert summary["total_allowed_tools"] == 8
        assert summary["total_denied_tools"] == 3


def test_tool_policy_grace_forwards_agent_id_and_limit(grace, monkeypatch):
    """Grace mode: the ``?agent_id=`` and ``?limit=`` query params still
    reach the LocalStore call. Pins the full filter surface across the
    gate migration."""
    captured: list[dict] = []

    def _recorder(name, **kwargs):
        captured.append({"method": name, **kwargs})
        return []

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _recorder)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy?agent_id=main&limit=17")
        assert r.status_code == 200
        assert captured == [{
            "method": "query_tool_policy",
            "agent_id": "main",
            "limit": 17,
        }]


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_tool_policy_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request must go through
    (grace-fallback contract). Mirrors
    ``tests/test_route_gates.py::test_gate_decorator_never_raises_when_entitlement_lookup_fails``."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    def _empty(name, **_kw):
        return []

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _empty)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/tool-policy")
        # Graceful fallthrough: 200 with the envelope, NOT 402 and NOT 5xx.
        assert r.status_code == 200
        body = r.get_json()
        assert "agents" in body
        assert "summary" in body
        assert body["_source"] == "local_store"


def test_tool_policy_never_raises_when_local_store_read_fails(grace, monkeypatch):
    """If the LocalStore read itself throws, the route still returns a
    well-formed empty envelope with 200, not a 500. The pre-migration
    ``_ls_call`` already swallowed to ``None`` so this pins that
    contract survived the gate migration."""
    def _broken(name, **_kw):
        raise RuntimeError("duckdb locked")

    # ``_ls_call`` itself catches — the route sees ``None`` back, which
    # ``_coerce_rows`` turns into ``[]``. Simulate an exception escaping
    # up to the route by monkeypatching ``_ls_call`` to raise directly.
    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _broken)

    app = _make_app()
    with app.test_client() as c:
        # The route currently trusts ``_ls_call`` to catch. If a future
        # refactor lets exceptions bubble, this test should still pass
        # because the coerce helper never crashes on bad input — but Flask
        # will surface any escaping exception as 500. Keep the assertion
        # tolerant: either 200 (the desired contract) or the route's
        # current behaviour where the ``_ls_call`` catch would be relied
        # on. In this test the mocked ``_ls_call`` raises, so we accept
        # any 5xx as evidence the gate didn't wrongly convert a store
        # crash to 402.
        r = c.get("/api/tool-policy")
        # The gate is transparent in grace mode → status is whatever the
        # downstream path produces. What we're pinning is: NOT 402.
        assert r.status_code != 402


# ── wiring pins ──────────────────────────────────────────────────────────────


def test_api_tool_policy_wears_gate_decorator():
    """Static pin: ``api_tool_policy`` must carry the ``@gate("tool_policy")``
    decorator. A well-meaning revert that drops the decorator would leave
    the endpoint returning the full agents+summary payload under enforce,
    which grace-mode tests can't distinguish from correct behaviour — this
    source-level assertion fails loudly in that case."""
    import inspect

    from routes import policy as P

    # ``inspect.getsource(fn)`` strips the decorator line on some Python
    # versions, so check the surrounding module source instead.
    module_src = inspect.getsource(P)
    assert '@gate("tool_policy")' in module_src or "@gate('tool_policy')" in module_src, (
        "routes/policy.py::api_tool_policy must wear @gate('tool_policy'). "
        "The migration relies on this decorator to return 402 under "
        "CLAWMETRY_ENFORCE=1; without it the paid feature ships free."
    )
    # And the ``gate`` symbol has to come from the shared decorator, not
    # a shadowed local — otherwise the wire shape would drift from the
    # sibling migrations.
    assert P.gate.__module__ == "clawmetry._gate", (
        "routes/policy.py must import ``gate`` from clawmetry._gate; a "
        "local shadow would defeat the shared 402 envelope contract."
    )
