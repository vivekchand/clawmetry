"""Tests for the ``@gate("error_triage")`` migration on the three
``/api/error-triage/*`` routes in ``routes/sessions.py``.

Sibling of ``tests/test_audit_route_gate.py``,
``tests/test_otel_export_route_gate.py``, ``tests/test_fleet_route_gates.py``,
``tests/test_assets_route_gates.py``, and
``tests/test_cost_optimizer_route_gates.py``. Pins:

- Enforce mode returns the shared 402 ``upgrade_required`` envelope with
  ``feature="error_triage"``, ``required_tier=cloud_pro`` (error triage is
  Pro-only, per ``PRO_ONLY_FEATURES`` in ``clawmetry/entitlements.py``),
  ``tier`` = the caller's current tier, and a ``hint`` string.
- The gate fires *before* the daemon-proxy read/write so a broken or absent
  ``local_store_via_daemon`` cannot leak through as a 5xx in enforce mode.
- The gate wins over the handler's own 400 branch (missing ``event_id``),
  so an unauthenticated caller sees the upgrade CTA rather than an
  argument-validation error.
- Grace mode (the default until the enforce-phase release) is transparent:
  the downstream handler runs and returns the ``{"ok": ...}`` /
  ``{"resolved": ..., "count": ...}`` envelopes exactly as before.
- A resolver crash never surfaces as 402 (mirrors the defensive contract
  pinned in ``tests/test_route_gates.py``).
- The 402 wire shape is byte-identical to what other ``@gate``d routes
  return, so an existing front-end that already handles 402 keeps working
  without a branch on ``feature=="error_triage"``.

The behavioural tests for the store layer + the pre-migration Flask
lifecycle stay in ``tests/test_error_triage.py`` since they don't touch
the gate.
"""
from __future__ import annotations

import importlib
import inspect

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss/free and
    ``error_triage`` (a Pro-only feature) is NOT allowed."""
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
    from routes.sessions import bp_sessions

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    return app


# ── enforce mode: 402 contract ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/error-triage/resolve"),
        ("DELETE", "/api/error-triage/resolve?event_id=ev:abc"),
        ("GET", "/api/error-triage/resolved"),
    ],
)
def test_error_triage_returns_402_when_enforced(
    enforce, monkeypatch, method, path
):
    """Every route wears ``@gate("error_triage")`` so an OSS install in
    enforce mode gets the shared 402 body instead of the handler payload."""
    # Belt-and-braces: if the gate silently dropped, the daemon call below
    # would produce a distinctive body — a well-meaning revert would fail
    # loudly here.
    def _sentinel(method_name, **_kw):
        return {"gate_should_have_fired": True}

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _sentinel, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        if method == "POST":
            r = c.post(path, json={"event_id": "ev:abc", "note": "hi"})
        elif method == "DELETE":
            r = c.delete(path)
        else:
            r = c.get(path)
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "error_triage"
        # Current tier is echoed so the UI can distinguish "not entitled at
        # all" from "entitled but on a downgrade path".
        assert "tier" in body
        # required_tier lets the paywall render the right upgrade CTA.
        # Error triage is Pro-only — not Starter, not Enterprise.
        assert body["required_tier"] == enforce.TIER_CLOUD_PRO
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No triage payload leaked through.
        assert "ok" not in body
        assert "resolved" not in body
        assert "removed" not in body


def test_error_triage_402_body_shape_matches_shared_gate(enforce):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch."""
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("error_triage")
    def _reference_view():
        return {"ok": True}

    triage_app = _make_app()

    with reference_app.test_client() as rc, triage_app.test_client() as tc:
        ref_body = rc.get("/reference").get_json()
        tri_body = tc.get("/api/error-triage/resolved").get_json()
        assert set(ref_body.keys()) == set(tri_body.keys())
        # Envelope keys pinned so a later refactor of `@gate` doesn't
        # silently drop `required_tier` or `tier`.
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == tri_body["feature"] == "error_triage"
        assert ref_body["required_tier"] == tri_body["required_tier"]
        assert ref_body["tier"] == tri_body["tier"]


def test_error_triage_gate_fires_before_daemon_call(enforce, monkeypatch):
    """The gate has to short-circuit the request *before* the
    ``local_store_via_daemon`` call runs. Otherwise a hung / absent daemon
    would surface as 503 instead of the 402 the caller expects."""
    calls: list[tuple] = []

    def _spy(method_name, **kwargs):
        calls.append((method_name, kwargs))
        return True

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _spy, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        r_post = c.post(
            "/api/error-triage/resolve", json={"event_id": "ev:1"}
        )
        r_delete = c.delete("/api/error-triage/resolve?event_id=ev:1")
        r_get = c.get("/api/error-triage/resolved")
    assert r_post.status_code == 402
    assert r_delete.status_code == 402
    assert r_get.status_code == 402
    # The gate ran and short-circuited: the daemon call never started.
    assert calls == []


def test_error_triage_gate_wins_over_missing_event_id_400(enforce):
    """The pre-migration handler returned 400 on a missing ``event_id``.
    Under enforce, the 402 must win so the UI shows the upgrade CTA rather
    than a confusing validation error to an OSS caller."""
    app = _make_app()
    with app.test_client() as c:
        # POST with an empty body — pre-gate this returned 400.
        r_post = c.post("/api/error-triage/resolve", json={})
        # DELETE with no query string — pre-gate this returned 400.
        r_delete = c.delete("/api/error-triage/resolve")
    assert r_post.status_code == 402
    assert r_delete.status_code == 402
    assert r_post.get_json().get("feature") == "error_triage"
    assert r_delete.get_json().get("feature") == "error_triage"


# ── grace mode: transparent ──────────────────────────────────────────────────


def test_error_triage_resolve_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode: POST /resolve reaches the daemon proxy and returns the
    pre-migration ``{"ok": True, "event_id": ...}`` envelope."""
    captured: list[tuple] = []

    def _fake(method_name, **kwargs):
        captured.append((method_name, kwargs))
        # ``mark_error_resolved`` returns True on success.
        return True

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _fake, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        r = c.post(
            "/api/error-triage/resolve",
            json={"event_id": "ev:1", "note": "known flaky"},
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body == {"ok": True, "event_id": "ev:1"}
    assert captured == [
        ("mark_error_resolved", {"event_id": "ev:1", "note": "known flaky"})
    ]


def test_error_triage_unresolve_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode: DELETE /resolve reaches the daemon proxy and returns
    the pre-migration ``{"ok": True, "removed": bool, "event_id": ...}``
    envelope. ``removed=False`` is the idempotent "wasn't there" case."""
    def _fake(method_name, **kwargs):
        assert method_name == "unmark_error_resolved"
        # Returning False mirrors the idempotent unmark path.
        return False

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _fake, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        r = c.delete("/api/error-triage/resolve?event_id=ev:missing")
        assert r.status_code == 200
        assert r.get_json() == {
            "ok": True, "removed": False, "event_id": "ev:missing",
        }


def test_error_triage_resolved_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode: GET /resolved reaches the daemon proxy and returns the
    pre-migration ``{"resolved": {...}, "count": N}`` envelope. The
    ``?limit=`` query param still reaches the read call."""
    seen_kwargs: list[dict] = []

    def _fake(method_name, **kwargs):
        seen_kwargs.append(kwargs)
        assert method_name == "query_resolved_errors"
        return {
            "ev:abc": {"resolved_at": 1700000000.0, "note": "known"},
            "ev:def": {"resolved_at": 1700000001.0, "note": None},
        }

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _fake, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/error-triage/resolved?limit=17")
        assert r.status_code == 200
        body = r.get_json()
        assert body["count"] == 2
        assert set(body["resolved"].keys()) == {"ev:abc", "ev:def"}
        # ?limit=17 reaches the store call (clamped 1..5000).
        assert seen_kwargs == [{"limit": 17}]


def test_error_triage_grace_preserves_missing_event_id_400(grace):
    """Grace mode: the pre-migration validation error still fires on a
    missing ``event_id`` so callers with a real license keep getting the
    same argument-validation contract. Pins that the gate didn't accidentally
    swallow the 400."""
    app = _make_app()
    with app.test_client() as c:
        r_post = c.post("/api/error-triage/resolve", json={})
        r_delete = c.delete("/api/error-triage/resolve")
    for r in (r_post, r_delete):
        assert r.status_code == 400
        body = r.get_json()
        assert body.get("ok") is False
        assert "event_id" in (body.get("error") or "")
        # No paywall keys leaked into the 400.
        assert "feature" not in body
        assert "required_tier" not in body


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_error_triage_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request must go through
    (grace-fallback contract). Mirrors
    ``tests/test_route_gates.py::test_gate_decorator_never_raises_when_entitlement_lookup_fails``."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    def _fake(method_name, **_kw):
        if method_name == "query_resolved_errors":
            return {}
        return True

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _fake, raising=False,
    )

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/error-triage/resolved")
        # Graceful fallthrough: 200 with the envelope, NOT 402 and NOT 5xx.
        assert r.status_code == 200
        body = r.get_json()
        assert body == {"resolved": {}, "count": 0}


# ── static wiring pins ───────────────────────────────────────────────────────


def test_error_triage_gate_decorator_wired_in_source():
    """Static-source assertion: ``from clawmetry._gate import gate`` and
    ``@gate("error_triage")`` are both present in ``routes/sessions.py``.
    A well-meaning revert that drops the decorator (leaving the endpoints
    unguarded, indistinguishable in grace-mode tests) fails loudly here."""
    from routes import sessions as S

    src = inspect.getsource(S)
    assert "from clawmetry._gate import gate" in src, (
        "routes/sessions.py must import the shared gate decorator so the "
        "error-triage endpoints stay on the shared paywall envelope."
    )
    # The three routes each get their own @gate("error_triage") — pin the
    # count so a partial revert (dropping the decorator on one of the three
    # while leaving the others) also fails loudly.
    assert src.count('@gate("error_triage")') == 3, (
        "All three /api/error-triage/* routes must carry "
        "@gate('error_triage'); a partial gate is a covert paywall bypass."
    )
