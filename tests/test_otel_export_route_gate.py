"""Tests for the ``@gate("otel_export")`` migration on ``routes/otel_export.py``.

Sibling of ``tests/test_fleet_route_gates.py``, ``tests/test_assets_route_gates.py``,
and ``tests/test_claudecode_runtime_gate.py``. Pins:

- Enforce mode returns the shared 402 ``upgrade_required`` envelope with
  ``feature="otel_export"``, ``required_tier=cloud_pro``, ``tier`` = the
  caller's current tier, and a ``hint`` string.
- Grace mode is transparent: the downstream handler runs and returns the
  OTLP-JSON envelope.
- The gate fires *before* body building so an empty event list can't leak
  through as a 200 in enforce mode.
- A resolver crash never surfaces as 402 (mirrors the defensive contract
  pinned in ``tests/test_route_gates.py``).
- The 402 wire shape is byte-identical to what other ``@gate``d routes
  return, so an existing front-end that already handles 402 keeps working
  without a branch on ``feature=="otel_export"``.

The unit tests for the envelope shape and event → LogRecord mapping stay
in ``tests/test_otel_export.py`` since they don't touch the gate.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss/free and
    ``otel_export`` (a Pro-only feature) is NOT allowed."""
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
    from routes.otel_export import bp_otel_export

    app = Flask(__name__)
    app.register_blueprint(bp_otel_export)
    return app


# ── enforce mode: 402 contract ──────────────────────────────────────────────


def test_otel_export_returns_402_when_enforced(enforce, monkeypatch):
    """The route wears ``@gate("otel_export")`` so an OSS install in enforce
    mode gets the shared 402 body instead of the OTLP envelope."""
    # Belt-and-braces: even if _fetch_events were to succeed the gate must
    # short-circuit before it. Stub it to something distinctive so a
    # regression that dropped the decorator would produce a 200 with the
    # sentinel in the body.
    monkeypatch.setattr(
        "routes.otel_export._fetch_events",
        lambda limit: [{"ts": 0, "event_type": "gate_should_have_fired"}],
    )
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/otel/export")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "otel_export"
        # Current tier is echoed so the UI can distinguish "not entitled at
        # all" from "entitled but on a downgrade path".
        assert "tier" in body
        # required_tier lets the paywall render the right upgrade CTA.
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No OTLP payload leaked through.
        assert "resourceLogs" not in body


def test_otel_export_402_body_shape_matches_shared_gate(enforce):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch."""
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("otel_export")
    def _reference_view():
        return {"ok": True}

    otel_app = _make_app()

    with reference_app.test_client() as rc, otel_app.test_client() as oc:
        ref_body = rc.get("/reference").get_json()
        oel_body = oc.get("/api/otel/export").get_json()
        assert set(ref_body.keys()) == set(oel_body.keys())
        # Envelope keys pinned so a later refactor of `@gate` doesn't
        # silently drop `required_tier` or `tier`.
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == oel_body["feature"] == "otel_export"
        assert ref_body["required_tier"] == oel_body["required_tier"]
        assert ref_body["tier"] == oel_body["tier"]


def test_otel_export_gate_fires_before_body_build(enforce):
    """The gate has to short-circuit the request *before* ``_fetch_events``
    runs. Otherwise a slow local-query call would still fire on every 402,
    or an exception inside the daemon fetch would leak through as a 500
    instead of the 402 the caller expects."""
    from routes import otel_export as O

    calls: list[int] = []

    def _spy(limit):
        calls.append(limit)
        return []

    original = O._fetch_events
    O._fetch_events = _spy
    try:
        app = _make_app()
        with app.test_client() as c:
            r = c.get("/api/otel/export?limit=42")
            assert r.status_code == 402
            # The gate ran and short-circuited: the fetch never started.
            assert calls == []
    finally:
        O._fetch_events = original


def test_otel_export_gate_wins_over_query_string_error(enforce):
    """Even a malformed ``?limit=`` value must not shadow the 402 — the
    gate fires before the limit-parse fallthrough, so the enforcement
    signal reaches the caller regardless of how they hit the URL."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/otel/export?limit=not-a-number")
        assert r.status_code == 402


# ── grace mode: transparent ──────────────────────────────────────────────────


def test_otel_export_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler builds
    the OTLP-JSON envelope; the fetch is stubbed to keep the test hermetic."""
    monkeypatch.setattr("routes.otel_export._fetch_events", lambda limit: [])
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/otel/export")
        assert r.status_code == 200
        body = r.get_json()
        assert "resourceLogs" in body
        assert isinstance(body["resourceLogs"], list)
        # The pre-migration hand-rolled 402 body carried no `resourceLogs`,
        # so seeing it here proves the gate stayed transparent AND the
        # handler ran.


def test_otel_export_grace_forwards_limit_to_fetch(grace, monkeypatch):
    """Grace mode: the ``?limit=`` query param still reaches the fetch.
    Pins that the migration didn't accidentally hard-code the limit."""
    seen: list[int] = []

    monkeypatch.setattr(
        "routes.otel_export._fetch_events",
        lambda limit: (seen.append(limit) or []),
    )
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/otel/export?limit=17")
        assert r.status_code == 200
        assert seen == [17]


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_otel_export_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request must go through
    (grace-fallback contract). Mirrors
    ``tests/test_route_gates.py::test_gate_decorator_never_raises_when_entitlement_lookup_fails``."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)
    monkeypatch.setattr("routes.otel_export._fetch_events", lambda limit: [])

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/otel/export")
        # Graceful fallthrough: 200 with the envelope, NOT 402 and NOT 5xx.
        assert r.status_code == 200
        assert "resourceLogs" in r.get_json()


# ── legacy helper cleanup ────────────────────────────────────────────────────


def test_legacy_entitlement_allows_helper_removed():
    """The hand-rolled ``_entitlement_allows`` helper was removed as part
    of the migration. This pin fails loudly if a well-meaning revert
    reintroduces it, so the module has one and only one gate implementation
    (the shared ``@gate`` decorator) going forward."""
    from routes import otel_export as O

    assert not hasattr(O, "_entitlement_allows"), (
        "routes/otel_export.py should route entitlement checks through "
        "@gate('otel_export'); the hand-rolled _entitlement_allows helper "
        "must not come back."
    )
