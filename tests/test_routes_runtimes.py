"""Tests for the ``/api/runtimes`` endpoint (``routes/entitlement.py``).

The endpoint feeds the locked-but-visible runtime affordance in the global
runtime switcher — every paid runtime appears in the catalog even when the
local install has zero sessions for it, with ``locked`` set from the resolved
entitlement.

The headline invariant: in GRACE mode (the default), every catalog row reports
``locked=False`` so the UI behaves exactly as it did before this endpoint
existed. ``CLAWMETRY_ENFORCE=1`` flips the paid rows to ``locked=True`` for an
OSS install.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement against a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def test_runtimes_grace_locks_nothing(client):
    resp = client.get("/api/runtimes")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["grace"] is True
    assert data["enforced"] is False
    runtimes = {r["id"]: r for r in data["runtimes"]}
    # OpenClaw is always free.
    assert runtimes["openclaw"]["free"] is True
    assert runtimes["openclaw"]["locked"] is False
    # Every paid runtime is present and not locked in grace mode.
    for rt in ("claude_code", "codex", "cursor", "aider", "goose",
               "opencode", "qwen_code", "hermes", "picoclaw", "nanoclaw"):
        assert rt in runtimes, rt
        assert runtimes[rt]["free"] is False, rt
        assert runtimes[rt]["locked"] is False, rt
        assert runtimes[rt]["label"], rt  # never blank


def test_runtimes_enforced_oss_locks_paid(monkeypatch, tmp_path):
    """When CLAWMETRY_ENFORCE=1 and no license/cloud plan is present every
    paid runtime is reported locked — the UI uses this to render the 🔒
    affordance in the switcher even for runtimes with zero local sessions."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    c = app.test_client()
    data = c.get("/api/runtimes").get_json()
    assert data["enforced"] is True
    assert data["grace"] is False
    runtimes = {r["id"]: r for r in data["runtimes"]}
    assert runtimes["openclaw"]["locked"] is False  # free stays free
    assert runtimes["claude_code"]["locked"] is True
    assert runtimes["picoclaw"]["locked"] is True


def test_runtimes_shape_is_stable(client):
    """Each row carries the keys the frontend reads — defends against an
    accidental rename breaking the dropdown."""
    data = client.get("/api/runtimes").get_json()
    assert isinstance(data["runtimes"], list)
    for row in data["runtimes"]:
        for key in ("id", "label", "free", "allowed", "locked"):
            assert key in row, row
        assert isinstance(row["id"], str)
        assert isinstance(row["label"], str)
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        # locked = paid-and-not-allowed; mutually exclusive with free=True.
        if row["free"]:
            assert row["locked"] is False, row
