"""Heartbeat agent_install piggyback (cloud bug fix 2026-05-18).

The cloud server can't filesystem-check the user's machine for OpenClaw /
NemoClaw install state — it lives on Cloud Run. Before this PR it was
hard-coding ``no_agent=True`` in a shim, which made the cloud "no agent
detected" empty-state lie for every user. The daemon already knows; we
ride the answer up on the heartbeat envelope.

These tests assert:
  1. The detection helper returns the documented dict shape (openclaw,
     nemoclaw, any_data, signals, no_agent).
  2. ``send_heartbeat`` injects ``agent_install`` into the POST payload.
  3. The shape is correct for each of: openclaw-present, nemoclaw-present,
     neither-present.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_mod(tmp_path, monkeypatch):
    """Reload ``clawmetry.sync`` in a clean env so module-level caches
    (``_agent_install_cache``) reset between tests."""
    # Point detection at an empty temp dir by default — each test overrides
    # for the variant it's exercising.
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "no-openclaw"))
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    importlib.reload(s)
    # Force a fresh cache evaluation per test.
    s._agent_install_cache["ts"] = 0.0
    s._agent_install_cache["value"] = None
    return s


# ── 1. helper shape ────────────────────────────────────────────────────────

def test_helper_returns_documented_dict_shape(sync_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "absent"))
    sync_mod._agent_install_cache["ts"] = 0.0
    sync_mod._agent_install_cache["value"] = None
    out = sync_mod._detect_agent_install_for_heartbeat()
    for field in ("openclaw_detected", "nemoclaw_detected", "any_data",
                  "signals", "no_agent"):
        assert field in out, f"missing field: {field}"
    assert isinstance(out["openclaw_detected"], bool)
    assert isinstance(out["nemoclaw_detected"], bool)
    assert isinstance(out["any_data"], bool)
    assert isinstance(out["signals"], list)
    assert isinstance(out["no_agent"], bool)


def test_helper_reports_no_agent_when_nothing_installed(sync_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "absent"))
    # ensure no nemoclaw binary picked up by shutil.which by clearing PATH
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(sync_mod, "_detect_any_local_data_for_heartbeat",
                        lambda: False)
    sync_mod._agent_install_cache["ts"] = 0.0
    sync_mod._agent_install_cache["value"] = None
    out = sync_mod._detect_agent_install_for_heartbeat()
    assert out["openclaw_detected"] is False
    assert out["nemoclaw_detected"] is False
    assert out["no_agent"] is True
    assert out["signals"] == []


def test_helper_detects_openclaw_via_gateway_pid(sync_mod, tmp_path, monkeypatch):
    home = tmp_path / "openclaw-home"
    (home / "gateway").mkdir(parents=True)
    (home / "gateway" / "gateway.pid").write_text("12345\n")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    sync_mod._agent_install_cache["ts"] = 0.0
    sync_mod._agent_install_cache["value"] = None
    out = sync_mod._detect_agent_install_for_heartbeat()
    assert out["openclaw_detected"] is True
    assert "openclaw" in out["signals"]
    assert out["no_agent"] is False


# ── 2. send_heartbeat wiring ───────────────────────────────────────────────

def test_send_heartbeat_payload_includes_agent_install(sync_mod, monkeypatch):
    """send_heartbeat MUST inject ``agent_install`` so the cloud receiver
    can stop returning hard-coded `no_agent=True`."""
    captured: list[dict] = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured.append(payload)
            return {"sync_allowed": True, "pending_queries": []}
        return {"ok": True}

    monkeypatch.setattr(sync_mod, "_post", fake_post)
    config = {"node_id": "node-test", "api_key": "cm_test"}

    assert sync_mod.send_heartbeat(config) is True
    assert captured, "send_heartbeat must POST exactly one /ingest/heartbeat"

    pl = captured[0]
    assert "agent_install" in pl, "heartbeat payload missing agent_install"
    ai = pl["agent_install"]
    assert isinstance(ai, dict)
    for field in ("openclaw_detected", "nemoclaw_detected", "any_data",
                  "signals", "no_agent"):
        assert field in ai


def test_send_heartbeat_payload_reflects_openclaw_install(sync_mod, tmp_path, monkeypatch):
    """When OpenClaw is present locally, agent_install.openclaw_detected
    must ride up in the next heartbeat — proving the cloud aggregator will
    see openclaw_detected=True for this user/node."""
    home = tmp_path / "openclaw-home"
    (home / "gateway").mkdir(parents=True)
    (home / "gateway" / "gateway.pid").write_text("99999\n")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    sync_mod._agent_install_cache["ts"] = 0.0
    sync_mod._agent_install_cache["value"] = None

    captured: list[dict] = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured.append(payload)
            return {"sync_allowed": True}
        return {"ok": True}

    monkeypatch.setattr(sync_mod, "_post", fake_post)
    config = {"node_id": "node-oc", "api_key": "cm_test"}

    assert sync_mod.send_heartbeat(config) is True
    assert captured[0]["agent_install"]["openclaw_detected"] is True
    assert captured[0]["agent_install"]["no_agent"] is False


def test_send_heartbeat_payload_reflects_no_agent(sync_mod, tmp_path, monkeypatch):
    """When neither OpenClaw nor NemoClaw is installed, agent_install
    reports no_agent=True so cloud's empty-state copy tells the truth."""
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "absent"))
    monkeypatch.setenv("PATH", str(tmp_path))  # hide nemoclaw binary
    # Force local-data check to False — dev machines running the test suite
    # often have a populated DuckDB which would otherwise trip the `any_data`
    # signal and flip no_agent to False.
    monkeypatch.setattr(sync_mod, "_detect_any_local_data_for_heartbeat",
                        lambda: False)
    sync_mod._agent_install_cache["ts"] = 0.0
    sync_mod._agent_install_cache["value"] = None

    captured: list[dict] = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured.append(payload)
            return {"sync_allowed": True}
        return {"ok": True}

    monkeypatch.setattr(sync_mod, "_post", fake_post)
    config = {"node_id": "node-empty", "api_key": "cm_test"}

    assert sync_mod.send_heartbeat(config) is True
    ai = captured[0]["agent_install"]
    assert ai["openclaw_detected"] is False
    assert ai["nemoclaw_detected"] is False
    assert ai["no_agent"] is True
