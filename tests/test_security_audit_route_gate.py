"""Tests for the ``@gate("audit_logs")`` gate on
``routes/infra.py::api_security_audit`` (``GET /api/security/audit``).

Sibling of ``tests/test_audit_route_gate.py``. That test pins the gate
on ``/api/audit-log``; this pins the gate on the ``/api/security/audit``
mirror that the Security tab hits for its recent-activity feed. The two
routes read the same underlying ``clawmetry.audit`` store and return the
same rows — leaving the mirror ungated would let a Free/Starter/Pro
caller sidestep ``/api/audit-log``'s gate by asking the Security tab URL
instead. This file pins that closed.

Pins:

- Enforce mode returns the shared 402 ``upgrade_required`` envelope with
  ``feature="audit_logs"``, ``required_tier=enterprise`` (audit logs are
  Enterprise-only, not Pro), ``tier`` = the caller's current tier, and a
  ``hint`` string.
- Grace mode is transparent: the downstream handler runs and returns the
  ``{"entries": [...], "event_types": [...], "count": N}`` envelope even
  though the caller is OSS.
- The gate fires *before* the audit-store read so a broken audit DB
  can't leak through as a 200 in enforce mode.
- A resolver crash never surfaces as 402 (mirrors the defensive contract
  pinned across every other ``@gate``d route).
- The 402 wire shape is byte-identical to what other ``@gate``d routes
  return and specifically to what ``/api/audit-log`` returns, so an
  existing front-end that already handles 402 keeps working with the
  same branch.
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
    from routes.infra import bp_security

    app = Flask(__name__)
    app.register_blueprint(bp_security)
    return app


# ── enforce mode: 402 contract ──────────────────────────────────────────────


def test_security_audit_returns_402_when_enforced(enforce, monkeypatch):
    """The route wears ``@gate("audit_logs")`` so an OSS install in enforce
    mode gets the shared 402 body instead of the entries envelope. Belt-and-
    braces: even if the audit read were to succeed, the gate must short-
    circuit before it — stub the audit module lookup to something distinctive
    so a regression that dropped the decorator would produce a 200 with the
    sentinel in the body."""
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
        r = c.get("/api/security/audit")
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


def test_security_audit_402_body_matches_audit_log_402(enforce, monkeypatch):
    """The Security-tab mirror must return byte-identical 402 keys and
    ``feature`` / ``required_tier`` / ``tier`` values to the canonical
    ``/api/audit-log`` route, so the front-end can handle either URL with
    the same 402 branch. Pins the two gates cannot drift."""
    class _Empty:
        @staticmethod
        def read_audit_log(**_kw):
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Empty)

    from routes.audit import bp_audit
    from routes.infra import bp_security

    reference_app = Flask(__name__)
    reference_app.register_blueprint(bp_audit)
    mirror_app = Flask(__name__)
    mirror_app.register_blueprint(bp_security)

    with reference_app.test_client() as rc, mirror_app.test_client() as mc:
        ref = rc.get("/api/audit-log")
        mir = mc.get("/api/security/audit")
        assert ref.status_code == 402
        assert mir.status_code == 402
        ref_body = ref.get_json()
        mir_body = mir.get_json()
        assert set(ref_body.keys()) == set(mir_body.keys()) == {
            "error", "feature", "tier", "required_tier", "hint",
        }
        assert ref_body["feature"] == mir_body["feature"] == "audit_logs"
        assert ref_body["required_tier"] == mir_body["required_tier"]
        assert ref_body["tier"] == mir_body["tier"]


def test_security_audit_gate_fires_before_audit_read(enforce, monkeypatch):
    """The gate has to short-circuit the request *before* the audit-store
    read runs. Otherwise a slow SQLite open, or an ImportError where
    ``clawmetry.audit`` may not have provisioned a DB, would leak through
    as a 500 instead of the 402 the caller expects."""
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
        r = c.get("/api/security/audit?limit=42")
        assert r.status_code == 402
        # The gate ran and short-circuited: the audit read never started.
        assert calls == []


def test_security_audit_gate_wins_over_query_string_error(enforce):
    """Even a malformed ``?limit=`` value must not shadow the 402 — the
    gate fires before the query-string parse, so the enforcement signal
    reaches the caller regardless of how they hit the URL."""
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/security/audit?limit=not-a-number")
        assert r.status_code == 402


# ── grace mode: transparent ──────────────────────────────────────────────────


def test_security_audit_passes_in_grace_mode(grace, monkeypatch):
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
        r = c.get("/api/security/audit")
        assert r.status_code == 200
        body = r.get_json()
        assert "entries" in body
        assert "event_types" in body
        assert "count" in body


def test_security_audit_grace_forwards_limit_to_read(grace, monkeypatch):
    """Grace mode: the ``?limit=`` query param still reaches the read.
    Pins that adding the gate didn't accidentally hard-code the limit."""
    seen: list[int] = []

    class _Recorder:
        @staticmethod
        def read_audit_log(*, limit):
            seen.append(limit)
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Recorder)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/security/audit?limit=17")
        assert r.status_code == 200
        assert seen == [17]


def test_security_audit_grace_clamps_limit(grace, monkeypatch):
    """Grace mode: the route caps ``?limit=`` at 200 (and floors at 1)
    so a caller can't ask for 100k rows through the tab-scoped mirror.
    Pins that pre-existing behaviour survived the gate migration."""
    seen: list[int] = []

    class _Recorder:
        @staticmethod
        def read_audit_log(*, limit):
            seen.append(limit)
            return []

        @staticmethod
        def event_types():
            return []

    import sys
    monkeypatch.setitem(sys.modules, "clawmetry.audit", _Recorder)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/security/audit?limit=100000")
        assert r.status_code == 200
        assert seen == [200]
        seen.clear()
        r = c.get("/api/security/audit?limit=0")
        assert r.status_code == 200
        assert seen == [1]


# ── defensive fallthrough ────────────────────────────────────────────────────


def test_security_audit_never_raises_when_entitlement_lookup_fails(
    enforce, monkeypatch
):
    """If the entitlement read itself throws, the request must go through
    (grace-fallback contract). Mirrors the sibling test in
    ``tests/test_audit_route_gate.py``."""
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
        r = c.get("/api/security/audit")
        # Graceful fallthrough: 200 with the envelope, NOT 402 and NOT 5xx.
        assert r.status_code == 200
        body = r.get_json()
        assert "entries" in body
        assert "event_types" in body
        assert "count" in body


def test_security_audit_never_raises_when_audit_read_fails(grace, monkeypatch):
    """If the audit store read itself throws, the route still returns a
    well-formed empty envelope with 200, not a 500. Pins the
    ``never break the Security tab over a read`` contract."""
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
        r = c.get("/api/security/audit")
        assert r.status_code == 200
        body = r.get_json()
        assert body == {"entries": [], "event_types": [], "count": 0}
