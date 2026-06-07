"""Pin ``retention_days`` in :meth:`Entitlement.to_dict` and on
``/api/entitlement``.

``Entitlement.event_retention_days()`` has been the canonical per-tier quota for
months, but the wire format the dashboard reads on every page load
(``/api/entitlement``) did not include it — every consumer had to call a second
endpoint or hardcode the per-tier number to render "data retained for N days".

The :meth:`to_dict` serializer now surfaces the same value under
``retention_days`` so:

* the dashboard's data-retention badge and history-range picker can read it off
  ``/api/entitlement`` directly,
* the API fallback returns the OSS-free default (``7``) instead of dropping the
  key entirely, and
* a future drift between :meth:`Entitlement.event_retention_days` and the
  catalogue cap is caught in CI.

This file is the parametric pin across every published tier, plus the API
shape + safe-fallback paths in ``routes/entitlement.py::api_entitlement``.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    real ``~/.clawmetry/license.key`` / ``cloud_plan.json`` never leak in.
    Enforcement off by default."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement and a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client(), tmp_path


def _write_cloud_plan(tmp_path, plan: str, **extra):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    body = {"plan": plan}
    body.update(extra)
    cache.write_text(json.dumps(body))


# ── to_dict() pins ────────────────────────────────────────────────────────────


def test_to_dict_includes_retention_days_in_grace(ent):
    d = ent.get_entitlement(force=True).to_dict()
    assert "retention_days" in d
    # OSS / grace defaults to the published 7-day cap.
    assert d["retention_days"] == 7


def test_to_dict_retention_matches_event_retention_days(ent):
    en = ent.get_entitlement(force=True)
    assert en.to_dict()["retention_days"] == en.event_retention_days()


@pytest.mark.parametrize(
    "plan, expected",
    [
        ("cloud_free", 7),
        ("cloud_starter", 30),
        ("trial", 30),
        ("cloud_pro", 90),
        ("pro", 90),
        ("enterprise", None),
    ],
)
def test_to_dict_retention_per_tier(ent, tmp_path, monkeypatch, plan, expected):
    """Every cloud-plan tier surfaces its catalogue retention through
    ``to_dict`` — no drift between the dict and ``event_retention_days``."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    _write_cloud_plan(tmp_path, plan)
    ent.invalidate()
    d = ent.get_entitlement(force=True).to_dict()
    assert d["retention_days"] == expected
    # The whole point of the field is the dashboard can render it without
    # calling event_retention_days() separately — pin the symmetry.
    assert d["retention_days"] == ent.get_entitlement().event_retention_days()


def test_to_dict_retention_unaffected_by_grace_flip(ent, monkeypatch):
    """Toggling enforcement does not change the per-tier cap — only the gate
    bypass — so ``retention_days`` should be identical in grace vs enforce
    on the same tier."""
    grace_val = ent.get_entitlement(force=True).to_dict()["retention_days"]
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_val = ent.get_entitlement(force=True).to_dict()["retention_days"]
    assert grace_val == enforce_val == 7


def test_to_dict_existing_keys_preserved(ent):
    """Adding ``retention_days`` must not drop any pre-existing field — the
    dashboard reads ``tier``, ``runtimes``, ``features`` etc. on every load."""
    d = ent.get_entitlement(force=True).to_dict()
    for key in (
        "tier",
        "source",
        "node_limit",
        "expiry",
        "expired",
        "is_paid",
        "grace",
        "enforced",
        "runtimes",
        "features",
        "free_runtimes",
        "paid_runtimes",
        "all_runtimes",
        "retention_days",
    ):
        assert key in d, key


# ── /api/entitlement shape ────────────────────────────────────────────────────


def test_api_entitlement_includes_retention_days_in_grace(client):
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    assert "retention_days" in d
    assert d["retention_days"] == 7


def test_api_entitlement_retention_for_paid_tier(monkeypatch, tmp_path):
    """A cached cloud-pro plan should bubble its 90-day cap through the API."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    _write_cloud_plan(tmp_path, "cloud_pro")

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()
    assert d["tier"] == "cloud_pro"
    assert d["retention_days"] == 90


def test_api_entitlement_retention_for_enterprise_is_null(monkeypatch, tmp_path):
    """Enterprise is unlimited — the API must serialise that as JSON ``null``,
    not a sentinel int, so the UI never renders ``-1 days``."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    _write_cloud_plan(tmp_path, "enterprise")

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()
    assert d["tier"] == "enterprise"
    assert d["retention_days"] is None


def test_api_entitlement_safe_fallback_includes_retention(monkeypatch):
    """When ``get_entitlement`` itself blows up, the dashboard still gets a
    safe OSS-free shape — including ``retention_days`` so the data-retention
    badge degrades gracefully rather than disappearing."""
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)

    import clawmetry.entitlements as e

    def _boom(*a, **kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(e, "get_entitlement", _boom)
    d = app.test_client().get("/api/entitlement").get_json()
    assert d["tier"] == "oss"
    assert d["retention_days"] == 7
