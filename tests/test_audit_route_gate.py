"""Tests for the ``@gate("audit_logs")`` migration on ``routes/audit.py``.

Sibling of ``tests/test_otel_export_route_gate.py``,
``tests/test_fleet_route_gates.py``, ``tests/test_assets_route_gates.py``,
and ``tests/test_claudecode_runtime_gate.py``. Pins:

- Enforce mode returns the shared 402 ``upgrade_required`` envelope with
  ``feature="audit_logs"``, ``required_tier=enterprise`` (audit logs are
  Enterprise-only, not Pro), ``tier`` = the caller's current tier, and a
  ``hint`` string.
- Grace mode is transparent: the downstream handler runs and returns the
  ``{"entries": [...], "event_types": [...], "count": N}`` envelope even
  though the caller is OSS.
- The gate fires *before* the audit-store read so a broken audit DB in
  cloud (no ``~/.clawmetry/audit.db`` present) can't leak through as a 200
  in enforce mode.
- A resolver crash never surfaces as 402 (mirrors the defensive contract
  pinned in ``tests/test_route_gates.py``).
- The 402 wire shape is byte-identical to what other ``@gate``d routes
  return, so an existing front-end that already handles 402 keeps working
  without a branch on ``feature=="audit_logs"``.

The behavioural tests for ``clawmetry.audit`` (record/read roundtrip,
never-raise contract, filtering) stay in ``tests/test_audit.py`` since
they don't touch the gate.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` — the tier is oss/free and
    ``audit_logs`` (an Enterprise-only feature) is NOT allowed."""
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
    from routes.audit import bp_audit

    app = Flask(__name__)
    app.register_blueprint(bp_audit)
    return app


# ── enforce mode: 402 contract ──────────────────────────────────────────────


def test_audit_log_returns_402_when_enforced(enforce, monkeypatch):
    """The route wears ``@gate("audit_logs")`` so an OSS install in enforce
    mode gets the shared 402 body instead of the entries envelope."""
    # Belt-and-braces: even if read_audit_log were to succeed the gate must
    # short-circuit before it. Stub the audit module lookup to something
    # distinctive so a regression that dropped the decorator would produce
    # a 200 with the sentinel in the body.
    class _Sentinel:
        @staticmethod
        def read_audit_log(**_kw):
            return [{"event_type": "gate_should_have_fired"}]

        @staticmethod
        def event_types():
            return ["gate_should_have_fired"]

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Sentinel)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log")
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "audit_logs"
        # Current tier is echoed so the UI can distinguish "not entitled at
        # all" from "entitled but on a downgrade path".
        assert "tier" in body
        # required_tier lets the paywall render the right upgrade CTA.
        # Audit logs are Enterprise-only, NOT Pro — so the CTA has to
        # target Enterprise or users get sent to the wrong upgrade flow.
        assert body["required_tier"] == enforce.TIER_ENTERPRISE
        assert isinstance(body.get("hint"), str) and body["hint"]
        # No entries payload leaked through.
        assert "entries" not in body


def test_audit_log_402_body_shape_matches_shared_gate(enforce):
    """The 402 body must carry the *same top-level keys* every other
    ``@gate``d route returns so the front-end can handle any paid-feature
    402 with one branch."""
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("audit_logs")
    def _reference_view():
        return {"ok": True}

    audit_app = _make_app()

    with reference_app.test_client() as rc, audit_app.test_client() as ac:
        ref_body = rc.get("/reference").get_json()
        aud_body = ac.get("/api/audit-log").get_json()
        assert set(ref_body.keys()) == set(aud_body.keys())
        # Envelope keys pinned so a later refactor of `@gate` doesn't
        # silently drop `required_tier` or `tier`.
        assert set(ref_body.keys()) == {
            "error",
            "feature",
            "tier",
            "required_tier",
            "hint",
        }
        assert ref_body["feature"] == aud_body["feature"] == "audit_logs"
        assert ref_body["required_tier"] == aud_body["required_tier"]
        assert ref_body["tier"] == aud_body["tier"]


def test_audit_log_gate_fires_before_audit_read(enforce, monkeypatch):
    """The gate has to short-circuit the request *before* the audit-store
    read runs. Otherwise a slow SQLite open, or an ImportError in cloud
    (where ``clawmetry.audit`` may not have provisioned a DB), would leak
    through as a 500 instead of the 402 the caller expects."""
    calls: list[dict] = []

    class _Spy:
        @staticmethod
        def read_audit_log(**kw):
            calls.append(kw)
            return []

        @staticmethod
        def event_types():
            calls.append({"event_types": True})
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Spy)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log?limit=42")
        assert r.status_code == 402
        # The gate ran and short-circuited: the audit read never started.
        assert calls == []


def test_audit_log_gate_wins_over_query_string_error(enforce):
    """Even a malformed ``?limit=`` or ``?since=`` value must not shadow
    the 402 — the gate fires before the query-string parse fallthrough, so
    the enforcement signal reaches the caller regardless of how they hit
    the URL."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log?limit=not-a-number&since=nope")
        assert r.status_code == 402


# ── grace mode: transparent ──────────────────────────────────────────────────


def test_audit_log_passes_in_grace_mode(grace, monkeypatch):
    """Grace mode (the current default until the enforce-phase release)
    must let the request through unchanged. The downstream handler builds
    the entries envelope; the audit store is stubbed to keep the test
    hermetic."""
    class _Empty:
        @staticmethod
        def read_audit_log(**_kw):
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Empty)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log")
        assert r.status_code == 200
        body = r.get_json()
        assert "entries" in body
        assert "event_types" in body
        assert "count" in body
        # The pre-migration hand-rolled 402 body carried no `entries`,
        # so seeing it here proves the gate stayed transparent AND the
        # handler ran.


def test_audit_log_grace_forwards_limit_to_read(grace, monkeypatch):
    """Grace mode: the ``?limit=`` query param still reaches the read.
    Pins that the migration didn't accidentally hard-code the limit."""
    seen: list[int] = []

    class _Recorder:
        @staticmethod
        def read_audit_log(*, limit, event_type=None, since=None):
            seen.append(limit)
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Recorder)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log?limit=17")
        assert r.status_code == 200
        assert seen == [17]


def test_audit_log_grace_forwards_event_type_and_since(grace, monkeypatch):
    """Grace mode: ``?event_type=`` and ``?since=`` also reach the read
    call. Pins the full filter surface across the gate migration."""
    captured: list[dict] = []

    class _Recorder:
        @staticmethod
        def read_audit_log(*, limit, event_type=None, since=None):
            captured.append({"limit": limit, "event_type": event_type, "since": since})
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Recorder)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log?event_type=license.activated&since=1700000000")
        assert r.status_code == 200
        assert captured == [{
            "limit": 200,
            "event_type": "license.activated",
            "since": 1700000000.0,
        }]


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_audit_log_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request must go through
    (grace-fallback contract). Mirrors
    ``tests/test_route_gates.py::test_gate_decorator_never_raises_when_entitlement_lookup_fails``."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    class _Empty:
        @staticmethod
        def read_audit_log(**_kw):
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Empty)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log")
        # Graceful fallthrough: 200 with the envelope, NOT 402 and NOT 5xx.
        assert r.status_code == 200
        body = r.get_json()
        assert "entries" in body
        assert "event_types" in body
        assert "count" in body


def test_audit_log_never_raises_when_audit_read_fails(grace, monkeypatch):
    """If the audit store read itself throws, the route still returns a
    well-formed empty envelope with 200, not a 500. Mirrors the
    ``never break the dashboard over a read`` contract that lived in the
    pre-migration handler."""
    class _Broken:
        @staticmethod
        def read_audit_log(**_kw):
            raise RuntimeError("audit db locked")

        @staticmethod
        def event_types():
            raise RuntimeError("audit db locked")

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Broken)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/audit-log")
        assert r.status_code == 200
        body = r.get_json()
        assert body == {"entries": [], "event_types": [], "count": 0}


# ── legacy helper cleanup ────────────────────────────────────────────────────


def test_legacy_allowed_helper_removed():
    """The hand-rolled ``_allowed`` helper was removed as part of the
    migration. This pin fails loudly if a well-meaning revert reintroduces
    it, so the module has one and only one gate implementation (the shared
    ``@gate`` decorator) going forward."""
    from routes import audit as A

    assert not hasattr(A, "_allowed"), (
        "routes/audit.py should route entitlement checks through "
        "@gate('audit_logs'); the hand-rolled _allowed helper must not "
        "come back."
    )


def test_legacy_paywall_import_removed():
    """The pre-migration handler imported ``upgrade_required_body`` from
    ``clawmetry._paywall``; the migration removed it because the shared
    ``@gate`` decorator builds the body itself. Pin that the import
    doesn't sneak back — a duplicate import would signal a partial
    revert."""
    import inspect

    from routes import audit as A

    src = inspect.getsource(A)
    assert "from clawmetry._paywall" not in src, (
        "routes/audit.py must not re-import clawmetry._paywall — the "
        "shared @gate('audit_logs') decorator already emits the 402 body."
    )
