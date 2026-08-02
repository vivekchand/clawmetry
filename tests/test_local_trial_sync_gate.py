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
    """A REAL Entitlement, not a shape-alike double.

    The first version of these tests used a SimpleNamespace with is_paid /
    expired as LAMBDAS — but on the real class they are PROPERTIES, so the
    production code calling ``ent.is_paid()`` raised TypeError while the
    tests stayed green. The bug shipped and the founder hit it live twice
    (status said "FREE plan" under a valid trial key). Doubles must match
    the real contract; the cheapest way is to not use a double at all.
    """
    import time as _t

    from clawmetry import entitlements as E

    tier = E.TIER_TRIAL if paid else E.TIER_OSS
    expiry = (_t.time() - 3600) if expired else (_t.time() + 6 * 86400)
    return E._build(tier, source, expiry=expiry)


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
    """The spawn is detached per-OS, runs `python -m clawmetry.sync` from a
    neutral CWD, and bootstraps a local-only config first (a config-less
    daemon crash-loops in load_config and the store never fills)."""
    import routes.trial as T
    import clawmetry.sync as S

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    captured = {}
    calls = []

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(pid=4242)

    monkeypatch.setattr(T.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(S, "ensure_local_config",
                        lambda: calls.append("config") or True)
    T._ensure_local_daemon()
    assert calls == ["config"], "config must be bootstrapped before the spawn"
    assert captured["cmd"][-2:] == ["-m", "clawmetry.sync"]
    kw = captured["kwargs"]
    assert kw.get("cwd") == os.path.expanduser("~"), \
        "`python -m` puts the CWD on sys.path; a repo CWD runs stale source"
    if os.name == "nt":
        assert kw.get("creationflags"), "Windows spawn must be detached"
    else:
        assert kw.get("start_new_session") is True


def test_ensure_local_config_writes_once(monkeypatch, tmp_path):
    """Missing config -> local-only shape written 0600; existing -> no-op."""
    import clawmetry.sync as S
    import json as _json
    import pathlib

    cfg = pathlib.Path(tmp_path) / "config.json"
    monkeypatch.setattr(S, "CONFIG_DIR", pathlib.Path(tmp_path))
    monkeypatch.setattr(S, "CONFIG_FILE", cfg)

    assert S.ensure_local_config() is True
    data = _json.loads(cfg.read_text())
    assert data["local_only"] is True
    assert data["api_key"] == ""
    assert data["node_id"]

    cfg.write_text(_json.dumps({"api_key": "keep-me"}))
    assert S.ensure_local_config() is False, "existing config must survive"
    assert _json.loads(cfg.read_text()) == {"api_key": "keep-me"}


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


def test_auth_check_no_openclaw_is_not_needs_setup(monkeypatch):
    """/api/auth/check must not demand gateway setup on a machine with no
    OpenClaw: needsSetup drives app.js into a MANDATORY (uncloseable) modal,
    and without an OpenClaw install there is no token that could ever be
    pasted. Revert-proof for the unclosable-popup live-hit (2026-07-28)."""
    import dashboard as _d
    from flask import Flask

    from routes.meta import bp_auth

    app = Flask(__name__)
    app.register_blueprint(bp_auth)
    monkeypatch.setattr(_d, "GATEWAY_TOKEN", "", raising=False)
    monkeypatch.delenv("OPENCLAW_GATEWAY_TOKEN", raising=False)

    monkeypatch.setattr(_d, "_detect_openclaw_install", lambda: False)
    r = app.test_client().get("/api/auth/check").get_json()
    assert r["needsSetup"] is False, \
        "no OpenClaw on the machine: the mandatory setup modal must not fire"
    assert r["authRequired"] is False

    monkeypatch.setattr(_d, "_detect_openclaw_install", lambda: True)
    r = app.test_client().get("/api/auth/check").get_json()
    assert r["needsSetup"] is True, \
        "OpenClaw present without a token still needs the setup step"


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
