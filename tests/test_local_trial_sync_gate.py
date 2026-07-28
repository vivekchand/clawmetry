"""The local trial must actually TURN ON the product (founder live-hit
2026-07-28: trial key active, dashboard tier=trial, `clawmetry status` said
"FREE plan, NOT syncing", 3 detected Claude Code sessions never ingested,
setup modal re-appeared on every load, and the empty-state banner told the
user to install OpenClaw).

Four guards, each anchored to one of the broken links:

1. ``_sync_allowed`` honours a valid self-hosted license even when the CLOUD
   account state says paused (the daemon-side gate that blocked LOCAL DuckDB
   ingest). Revert-proof: reverting the override turns
   ``test_sync_allowed_license_overrides_cloud_pause`` red.
2. ``/api/trial/activate`` spawns the local sync daemon (detached) so the
   detected runtime's sessions start ingesting immediately.
3. The setup modal suppresses itself when every detected runtime is already
   watched (JS contract).
4. The no-agent banner treats all-entitled detected runtimes as
   agent-present (JS contract).
"""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── 1. the daemon-side gate ─────────────────────────────────────────────────


def _ent(source="license", paid=True, expired=False):
    return SimpleNamespace(
        source=source,
        is_paid=lambda: paid,
        expired=lambda: expired,
    )


@pytest.fixture
def sync_mod(monkeypatch):
    from clawmetry import sync as S

    # Simulate the cloud verdict: paused (expired cloud account).
    monkeypatch.setitem(S._TRIAL_STATE, "sync_allowed", False)
    return S


def test_sync_allowed_license_overrides_cloud_pause(sync_mod, monkeypatch):
    """A valid self-hosted trial/pro key entitles LOCAL ingest regardless of
    the (possibly stale/expired) cloud account plan."""
    from clawmetry import entitlements as E

    monkeypatch.setattr(E, "get_entitlement", lambda force=False: _ent())
    assert sync_mod._sync_allowed() is True, \
        "a licensed node must never be 'paused' out of its own local store"


def test_sync_allowed_still_pauses_unlicensed(sync_mod, monkeypatch):
    from clawmetry import entitlements as E

    monkeypatch.setattr(
        E, "get_entitlement",
        lambda force=False: _ent(source="oss", paid=False),
    )
    assert sync_mod._sync_allowed() is False, \
        "without a license the cloud pause verdict stands"


def test_sync_allowed_expired_license_does_not_override(sync_mod, monkeypatch):
    from clawmetry import entitlements as E

    monkeypatch.setattr(
        E, "get_entitlement",
        lambda force=False: _ent(expired=True),
    )
    assert sync_mod._sync_allowed() is False, \
        "an expired key must not resurrect a paused node"


def test_sync_allowed_cloud_yes_stays_yes(monkeypatch):
    from clawmetry import sync as S

    monkeypatch.setitem(S._TRIAL_STATE, "sync_allowed", True)
    assert S._sync_allowed() is True


# ── 2. activation starts the daemon ─────────────────────────────────────────


def test_ensure_local_daemon_spawn_shape(monkeypatch):
    """The spawn is detached per-OS and runs `python -m clawmetry.sync`."""
    import routes.trial as T

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    captured = {}

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(pid=4242)

    monkeypatch.setattr(T.subprocess, "Popen", _fake_popen)
    T._ensure_local_daemon()
    assert captured["cmd"][-2:] == ["-m", "clawmetry.sync"]
    kw = captured["kwargs"]
    if os.name == "nt":
        assert kw.get("creationflags"), "Windows spawn must be detached"
    else:
        assert kw.get("start_new_session") is True


def test_trial_activation_calls_ensure_daemon(monkeypatch, tmp_path):
    """The activation handler must kick ingestion, not just write the key."""
    import routes.trial as T

    spawned = []
    monkeypatch.setattr(T, "_ensure_local_daemon", lambda: spawned.append(1))
    import clawmetry.license as L

    monkeypatch.setattr(L, "activate", lambda key, actor="": (True, "ok"))
    monkeypatch.setattr(L, "_cloud_base", lambda: "https://cloud.test")

    import io
    import json as _json
    import urllib.request as _ur

    class _Resp:
        def read(self):
            return _json.dumps({"ok": True, "key": "CLAW1.x.y"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(T.urllib.request, "urlopen", lambda req, timeout=0: _Resp())

    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(T.bp_trial)
    r = app.test_client().post(
        "/api/trial/activate", json={"email": "a@b.co", "code": "123456"}
    )
    assert r.status_code == 200, r.get_json()
    assert spawned == [1], "activation must start the local sync daemon"


# ── 3+4. frontend contracts ─────────────────────────────────────────────────


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def test_gw_setup_suppresses_modal_when_all_watched():
    src = _read("clawmetry/static/js/gw-setup.js")
    assert "if (show === false) return;" in src, \
        "checkGwConfig must honour the suppress signal"
    assert "return false;" in src, \
        "_gwApplyRuntimeDetection must return false when nothing needs setup"


def test_no_agent_banner_suppressed_for_entitled_runtimes():
    src = _read("clawmetry/static/js/app.js")
    assert "_detected.every(function(r){ return r && r.entitled; })" in src, \
        "checkAgentPresence must treat all-entitled detected runtimes as agent-present"
