"""Regression: OpenClaw "installed" must require a REAL artifact, not the bare
~/.openclaw dir that ClawMetry itself creates.

Bug (verified live 2026-05-30): on a machine where OpenClaw was uninstalled,
`agent_install.openclaw_detected` was `true` because the heartbeat detector
fell back to "~/.openclaw exists and is non-empty" — but ClawMetry drops its own
`.clawmetry-fleet.db` / `.clawmetry-metrics.json` into `~/.openclaw/workspace`,
so the dir is never actually empty. These tests pin the tightened rule.

Pure OSS (no clawmetry_pro needed), so this runs in OSS CI.
"""
from __future__ import annotations

import os

import pytest

import clawmetry.sync as sync


@pytest.fixture(autouse=True)
def _no_global_signals(monkeypatch):
    # Neutralize host-level signals so tests only see the tmp OPENCLAW_HOME.
    import shutil
    monkeypatch.setattr(shutil, "which", lambda *_a, **_k: None)
    # /Applications/OpenClaw.app is absent on CI (Linux); guard anyway.
    real_isdir = os.path.isdir
    monkeypatch.setattr(os.path, "isdir",
                        lambda p: False if p == "/Applications/OpenClaw.app" else real_isdir(p))
    # clear the agent_install cache between cases
    sync._agent_install_cache.pop("value", None)
    sync._agent_install_cache["ts"] = 0


def test_bare_openclaw_dir_is_not_detected(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    home.mkdir()
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert sync._detect_openclaw_install_for_heartbeat() is False


def test_clawmetry_own_workspace_files_are_not_a_signal(monkeypatch, tmp_path):
    # The exact false-positive scenario: only ClawMetry's scratch files exist.
    home = tmp_path / ".openclaw"
    ws = home / "workspace"
    ws.mkdir(parents=True)
    (ws / ".clawmetry-fleet.db").write_text("x")
    (ws / ".clawmetry-metrics.json").write_text("{}")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert sync._detect_openclaw_install_for_heartbeat() is False
    assert sync._openclaw_gateway_running() is False


def test_real_workspace_markers_are_detected(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    ws = home / "workspace"
    ws.mkdir(parents=True)
    (ws / "SOUL.md").write_text("# soul")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert sync._detect_openclaw_install_for_heartbeat() is True


def test_real_session_jsonl_is_detected(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    sess = home / "agents" / "main" / "sessions"
    sess.mkdir(parents=True)
    (sess / "abc.jsonl").write_text('{"type":"session"}\n')
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert sync._detect_openclaw_install_for_heartbeat() is True


def test_live_gateway_is_detected_and_running(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    gw = home / "gateway"
    gw.mkdir(parents=True)
    # our own pid is guaranteed alive -> os.kill(pid, 0) succeeds
    (gw / "gateway.pid").write_text(str(os.getpid()))
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert sync._detect_openclaw_install_for_heartbeat() is True
    assert sync._openclaw_gateway_running() is True


def test_agent_install_payload_carries_openclaw_running(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    home.mkdir()
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    payload = sync._detect_agent_install_for_heartbeat()
    assert payload["openclaw_detected"] is False
    assert payload["openclaw_running"] is False
    assert "openclaw" not in payload["signals"]
