"""Tests for the shared OSS-stub 402 ``upgrade_required`` body builder.

Pins the wire shape :func:`clawmetry._paywall.upgrade_required_body`
returns and the live 402 bodies emitted by the four stub blueprints that
adopt it. The shape must stay in lockstep with what ``@gate`` returns so
the dashboard can branch on the same fields regardless of which path
produced the 402.

Companion to :mod:`tests.test_route_gates`.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent_grace(monkeypatch, tmp_path):
    """Reload entitlements with HOME pointed at an empty tmp_path so the
    resolver collapses to the OSS-free entitlement deterministically."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── upgrade_required_body shape ──────────────────────────────────────────────


def test_body_shape_matches_gate_decorator(ent_grace):
    """The 402 body must carry the same five keys ``@gate`` produces so
    frontends can branch on either path with one handler."""
    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("self_evolve")
    assert set(body.keys()) == {
        "error",
        "feature",
        "tier",
        "required_tier",
        "hint",
    }
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "self_evolve"


def test_body_required_tier_starter_feature(ent_grace):
    """A Starter-card feature resolves ``required_tier`` to
    ``cloud_starter`` -- the cheapest purchasable tier that unlocks it."""
    from clawmetry._paywall import upgrade_required_body

    for key in ("multi_runtime", "fleet", "all_channels", "budget_limits"):
        body = upgrade_required_body(key)
        assert body["required_tier"] == ent_grace.TIER_CLOUD_STARTER, key


def test_body_required_tier_pro_feature(ent_grace):
    """A Pro-only feature resolves ``required_tier`` to ``cloud_pro``."""
    from clawmetry._paywall import upgrade_required_body

    for key in ("self_evolve", "custom_runtime_ingest", "otel_export"):
        body = upgrade_required_body(key)
        assert body["required_tier"] == ent_grace.TIER_CLOUD_PRO, key


def test_body_required_tier_enterprise_feature(ent_grace):
    """An Enterprise-only feature resolves ``required_tier`` to
    ``enterprise`` so the UI renders the Enterprise CTA, not the Pro one."""
    from clawmetry._paywall import upgrade_required_body

    for key in ("audit_logs", "sso", "siem_export"):
        body = upgrade_required_body(key)
        assert body["required_tier"] == ent_grace.TIER_ENTERPRISE, key


def test_body_required_tier_free_feature_is_none(ent_grace):
    """Free features don't have an upgrade target -- ``required_tier`` is
    ``None`` so the UI can short-circuit instead of rendering a CTA."""
    from clawmetry._paywall import upgrade_required_body

    for key in ent_grace.FREE_FEATURES:
        body = upgrade_required_body(key)
        assert body["required_tier"] is None, key


def test_body_required_tier_unknown_feature_is_none(ent_grace):
    """An unknown / typo'd feature key collapses to ``None`` rather than
    raising so a stub for a clawmetry-pro plugin's private key still
    returns a well-formed 402 body."""
    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("totally_unknown_feature_xyz")
    assert body["required_tier"] is None
    assert body["feature"] == "totally_unknown_feature_xyz"
    assert body["error"] == "upgrade_required"


def test_body_default_hint_used_when_omitted(ent_grace):
    """Omitting ``hint`` falls back to the default ('install clawmetry-pro
    or use Cloud') copy so stubs that don't care about the wording don't
    have to inline a string."""
    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("self_evolve")
    assert "clawmetry-pro" in body["hint"]
    assert body["hint"]  # non-empty


def test_body_custom_hint_overrides_default(ent_grace):
    """A feature-specific hint overrides the default so the audit-log stub
    can mention Enterprise explicitly, etc."""
    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("audit_logs", hint="Audit logs are Enterprise.")
    assert body["hint"] == "Audit logs are Enterprise."


def test_body_tier_reflects_current_install(ent_grace):
    """Free / OSS installs report ``tier="oss"`` in the 402 body so the
    UI knows where the user is starting from when rendering the upgrade
    delta."""
    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("self_evolve")
    assert body["tier"] == ent_grace.TIER_OSS


def test_body_swallows_feature_set_errors(monkeypatch):
    """If a catalogue set itself raises on membership lookup, the helper
    still produces a well-formed body with ``required_tier=None`` rather
    than 500-ing the request."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body

    class _Boom:
        def __contains__(self, _key):
            raise RuntimeError("boom")

    monkeypatch.setattr(ent, "PRO_ONLY_FEATURES", _Boom())
    body = upgrade_required_body("self_evolve")
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "self_evolve"
    assert body["required_tier"] is None


def test_body_swallows_get_entitlement_errors(monkeypatch):
    """If ``get_entitlement`` itself raises, ``tier`` falls back to ``oss``
    rather than crashing the request path."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body

    def explode(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "get_entitlement", explode)
    body = upgrade_required_body("self_evolve")
    assert body["tier"] == "oss"
    assert body["error"] == "upgrade_required"


# ── live stub-blueprint smoke checks ─────────────────────────────────────────


def _make_app_with(blueprint):
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    return app


@pytest.mark.parametrize(
    "path,method,bp_import,expected_feature,expected_required_attr",
    [
        # selfevolve stub: 6 endpoints, all return the same body
        (
            "/api/selfevolve/status",
            "GET",
            "routes.selfevolve:bp_selfevolve",
            "self_evolve",
            "TIER_CLOUD_PRO",
        ),
        (
            "/api/selfevolve/latest",
            "GET",
            "routes.selfevolve:bp_selfevolve",
            "self_evolve",
            "TIER_CLOUD_PRO",
        ),
        # runtime_ingest stub: every write endpoint returns 402
        (
            "/api/v1/runs",
            "POST",
            "routes.runtime_ingest:bp_runtime_ingest",
            "custom_runtime_ingest",
            "TIER_CLOUD_PRO",
        ),
        (
            "/api/v1/runs/abc/events",
            "POST",
            "routes.runtime_ingest:bp_runtime_ingest",
            "custom_runtime_ingest",
            "TIER_CLOUD_PRO",
        ),
    ],
)
def test_stub_blueprint_402_carries_required_tier(
    ent_grace,
    path,
    method,
    bp_import,
    expected_feature,
    expected_required_attr,
):
    """The 402 body emitted by the live stub blueprints carries the full
    ``{error, feature, tier, required_tier, hint}`` shape so the dashboard
    can render the right upgrade CTA off the stub 402 the same way it
    already does off the ``@gate`` 402."""
    mod_name, attr = bp_import.split(":")
    bp = getattr(importlib.import_module(mod_name), attr)
    app = _make_app_with(bp)
    with app.test_client() as c:
        r = c.open(path, method=method)
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == expected_feature
        assert body["tier"] == ent_grace.TIER_OSS
        assert body["required_tier"] == getattr(ent_grace, expected_required_attr)
        assert "hint" in body and body["hint"]


def test_audit_stub_402_uses_paywall_shape(ent_grace, monkeypatch):
    """``routes/audit.py`` gates on the Enterprise-only ``audit_logs``
    feature; forcing the entitlement check to deny exercises the 402 path
    and the shared body builder. ``required_tier`` must be
    ``enterprise`` (not ``cloud_pro``) so the UI offers the right plan."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    # Reload so is_enforced() picks up the env change.
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.audit import bp_audit

    app = _make_app_with(bp_audit)
    with app.test_client() as c:
        r = c.get("/api/audit-log")
        assert r.status_code == 402
        body = r.get_json()
        assert body["feature"] == "audit_logs"
        assert body["required_tier"] == e.TIER_ENTERPRISE
        assert body["tier"] in (e.TIER_OSS, e.TIER_CLOUD_FREE)

    e.invalidate()
