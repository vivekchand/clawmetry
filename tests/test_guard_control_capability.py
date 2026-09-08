"""Control capability must be answered per SESSION, and honestly.

Two gaps this covers:

* **OpenClaw pause claimed enforcement it did not have.** A pause on an
  OpenClaw session writes ``~/.clawmetry/hitl/pause_<sid>``, and the only
  thing that enforces that file is the optional enforcement proxy. On a node
  with no proxy the old code still reported "the proxy refuses further LLM
  calls" — a pause that said it stopped an agent which was in fact still
  running.
* **Capability was answered per runtime.** Cursor was refused wholesale even
  though Cursor CLI sessions are real process trees, and the platform check
  refused every Windows node outright.
"""
import clawmetry.process_control as pc
import pytest


@pytest.fixture
def no_proxy(monkeypatch):
    monkeypatch.setattr(pc, "enforcement_proxy_status",
                        lambda: {"running": False, "pid": None,
                                 "reason": "no proxy pid file"})


@pytest.fixture
def live_proxy(monkeypatch):
    monkeypatch.setattr(pc, "enforcement_proxy_status",
                        lambda: {"running": True, "pid": 4242, "reason": ""})


# ── OpenClaw pause honesty ────────────────────────────────────────────────
def test_openclaw_pause_is_inert_without_the_proxy(no_proxy):
    cap = pc.openclaw_pause_capability()
    assert cap["effective"] is False
    assert cap["mechanism"] == "none"
    # It must say the agent keeps running, and point at the thing that works.
    assert "keeps running" in cap["detail"]
    assert "Stop" in cap["detail"]


def test_openclaw_pause_is_effective_with_the_proxy(live_proxy):
    cap = pc.openclaw_pause_capability()
    assert cap["effective"] is True
    assert cap["mechanism"] == "proxy_hitl"
    assert cap["proxy_pid"] == 4242


def test_openclaw_offers_no_pause_button_without_the_proxy(no_proxy):
    sup = pc.runtime_control_support("openclaw", "sess-1")
    assert sup["controllable"] is True          # Stop still works
    assert "pause" not in sup["actions"]
    assert sup["no_pause"] is True
    assert sup["actions"] == ["stop", "kill"]


def test_openclaw_offers_pause_when_the_proxy_is_live(live_proxy):
    sup = pc.runtime_control_support("openclaw", "sess-1")
    assert "pause" in sup["actions"] and "resume" in sup["actions"]
    assert sup["no_pause"] is False


def test_actuator_reports_openclaw_pause_as_failed_without_a_proxy(no_proxy, monkeypatch):
    """The actuator's own return value — what gets recorded in the audit
    trail and shown to the operator — must not claim success."""
    from clawmetry import sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, paused: None)
    res = sync._guard_actuate("openclaw", "sess-1", "", "pause")
    assert res["ok"] is False
    assert res["advisory_only"] is True
    assert res["detail"] == "unsupported_no_primitive"


def test_actuator_reports_openclaw_pause_as_real_with_a_proxy(live_proxy, monkeypatch):
    from clawmetry import sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, paused: None)
    res = sync._guard_actuate("openclaw", "sess-1", "", "pause")
    assert res["ok"] is True
    assert res["detail"] == "paused_via_proxy_hitl"
    assert res["advisory_only"] is False


def test_resume_goes_through_the_shared_actuator(live_proxy, monkeypatch):
    """Resume used to bypass _guard_actuate and call resume_session directly,
    so it returned 'unsupported' for OpenClaw sessions the proxy could have
    released."""
    from clawmetry import sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, paused: None)
    res = sync._guard_actuate("openclaw", "sess-1", "", "resume")
    assert res["ok"] is True
    assert res["detail"] == "resumed_via_proxy_hitl"


# ── proxy liveness probe ──────────────────────────────────────────────────
def test_proxy_probe_treats_a_stale_pid_file_as_not_running(monkeypatch, tmp_path):
    pid_file = tmp_path / "proxy.pid"
    pid_file.write_text("999999")
    monkeypatch.setattr(pc, "_PROXY_PID_FILE", str(pid_file))
    monkeypatch.setattr(pc, "is_alive", lambda p: False)
    st = pc.enforcement_proxy_status()
    assert st["running"] is False and st["reason"] == "stale proxy pid file"


def test_proxy_probe_survives_a_garbage_pid_file(monkeypatch, tmp_path):
    pid_file = tmp_path / "proxy.pid"
    pid_file.write_text("not-a-pid")
    monkeypatch.setattr(pc, "_PROXY_PID_FILE", str(pid_file))
    assert pc.enforcement_proxy_status()["running"] is False


def test_proxy_probe_reports_a_live_proxy(monkeypatch, tmp_path):
    pid_file = tmp_path / "proxy.pid"
    pid_file.write_text("  4242\n")
    monkeypatch.setattr(pc, "_PROXY_PID_FILE", str(pid_file))
    monkeypatch.setattr(pc, "is_alive", lambda p: p == 4242)
    st = pc.enforcement_proxy_status()
    assert st["running"] is True and st["pid"] == 4242


# ── per-session capability, not per runtime ───────────────────────────────
def test_cursor_cli_session_is_controllable(monkeypatch):
    """A Cursor CLI session is a real process tree. Blanket-refusing the
    runtime hid working buttons from these sessions."""
    monkeypatch.setattr(pc, "resolve_session",
                        lambda rt, sid="", cwd="": {"ok": True, "pid": 500,
                                                    "runtime": "cursor"})
    sup = pc.runtime_control_support("cursor", "cli-sess", "/repo")
    assert sup["controllable"] is True
    assert sup["actions"] == ["pause", "resume", "stop", "kill"]
    assert sup["resolved_pid"] == 500


def test_cursor_editor_session_is_refused_with_a_readable_reason(monkeypatch):
    monkeypatch.setattr(
        pc, "resolve_session",
        lambda rt, sid="", cwd="": {
            "ok": False, "unsupported": True,
            "reason": "cursor_single_ide_process_no_per_session_signal"})
    sup = pc.runtime_control_support("cursor", "ide-sess")
    assert sup["controllable"] is False and sup["actions"] == []
    # An operator-readable sentence, not the raw resolver enum.
    assert "shared IDE process" in sup["reason"]
    assert "_no_per_session_signal" not in sup["reason"]


def test_every_supported_runtime_is_controllable(monkeypatch):
    """The list widened upstream (copilot, qwen_code, kimi, pi, grok,
    deepseek_harness); the capability answer must track it, not a stale copy.

    The resolver is stubbed because claude_code is now answered per session
    (as cursor already was): this test is about runtime COVERAGE, not about
    whether one synthetic session id happens to sit in the local session map.
    """
    monkeypatch.setattr(pc, "resolve_session",
                        lambda rt, sid="", cwd="": {"ok": True, "pid": 500,
                                                    "runtime": rt})
    monkeypatch.setattr(pc, "is_alive", lambda p: True)
    for rt in pc.SUPPORTED_RUNTIMES:
        sup = pc.runtime_control_support(rt, "s", "/tmp")
        assert sup["controllable"] is True, rt
        assert "kill" in sup["actions"], rt


def test_claude_code_session_with_no_live_process_is_refused(monkeypatch):
    """A claude_code session the map cannot resolve comes back disabled with a
    reason, not as four buttons whose only outcome is an alert box."""
    monkeypatch.setattr(
        pc, "resolve_session",
        lambda rt, sid="", cwd="": {"ok": False,
                                    "reason": "session_not_in_claude_map"})
    sup = pc.runtime_control_support("claude_code", "gone-sess")
    assert sup["controllable"] is False and sup["actions"] == []
    assert "no running process" in sup["reason"]
    # The operator gets a sentence, not the raw resolver enum.
    assert "session_not_in_claude_map" not in sup["reason"]


def test_claude_code_capability_refuses_a_dead_pid(monkeypatch):
    monkeypatch.setattr(pc, "resolve_session",
                        lambda rt, sid="", cwd="": {"ok": True, "pid": 4242})
    monkeypatch.setattr(pc, "is_alive", lambda p: False)
    sup = pc.runtime_control_support("claude_code", "stale-sess")
    assert sup["controllable"] is False and sup["actions"] == []
    assert "4242" in sup["reason"]


def test_unknown_runtime_is_refused():
    sup = pc.runtime_control_support("some-new-harness", "s")
    assert sup["controllable"] is False
    assert "some-new-harness" in sup["reason"]


def test_unsupported_platform_refuses_every_runtime(monkeypatch):
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_IS_WINDOWS", False)
    for rt in ("claude_code", "openclaw", "cursor"):
        sup = pc.runtime_control_support(rt, "s")
        assert sup["controllable"] is False and sup["actions"] == []


def test_windows_node_is_controllable(monkeypatch):
    """The gap: every Guard button was inert on Windows."""
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_IS_WINDOWS", True)
    monkeypatch.setattr(pc, "resolve_session",
                        lambda rt, sid="", cwd="": {"ok": True, "pid": 500,
                                                    "runtime": rt})
    monkeypatch.setattr(pc, "is_alive", lambda p: True)
    sup = pc.runtime_control_support("claude_code", "s")
    assert sup["controllable"] is True
    assert sup["platform"]["mechanism"] == "win32_native"


def test_capability_never_raises(monkeypatch):
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        pc.resolve_session("cursor")
    # The route wrapper is the layer that must absorb it.
    from routes.guard import _runtime_supports_signals
    sup = _runtime_supports_signals("cursor", "s", "/tmp")
    assert sup["controllable"] is False and sup["actions"] == []


# ── the store's namespaced session id must reach the resolvers as a native id ─
def test_store_prefixed_session_id_resolves(monkeypatch):
    """BURN 2026-09-05: the Guard tab posted ``claude_code:<uuid>`` (the store's
    namespaced id) and every Pause/Stop/Kill answered
    ``session_not_in_claude_map``, because the map is keyed on the bare uuid
    Claude Code writes. The kill switch was inert on every family runtime."""
    monkeypatch.setattr(
        pc, "claude_code_session_map",
        lambda: {"native-uuid": {"pid": 4242, "cwd": "/repo",
                                 "procStart": None, "status": "busy"}})
    info = pc.resolve_session("claude_code", "claude_code:native-uuid")
    assert info["ok"] is True and info["pid"] == 4242
    # A bare id keeps working — OpenClaw ids were never namespaced.
    assert pc.resolve_session("claude_code", "native-uuid")["ok"] is True


def test_native_session_id_only_strips_its_own_runtime_head():
    assert pc.native_session_id("claude_code", "claude_code:u") == "u"
    assert pc.native_session_id("CLAUDE_CODE", "claude_code:u") == "u"
    # Not this runtime's prefix: left alone, so nothing is silently truncated.
    assert pc.native_session_id("codex", "claude_code:u") == "claude_code:u"
    # Only the FIRST head goes; a native id may legitimately contain a colon.
    assert pc.native_session_id("codex", "codex:a:b") == "a:b"
    assert pc.native_session_id("openclaw", "bare-uuid") == "bare-uuid"
    assert pc.native_session_id("", "bare-uuid") == "bare-uuid"


def test_claude_session_map_memo_invalidates_when_a_session_appears(tmp_path,
                                                                    monkeypatch):
    """The memo exists so a 50-row Guard list does not re-scan the directory 50
    times; it must not hide a session that just started."""
    import json

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    pc._CLAUDE_MAP_CACHE.update({"key": None, "at": 0.0, "map": {}})

    assert pc.claude_code_session_map() == {}
    (sessions / "77.json").write_text(json.dumps(
        {"pid": 77, "sessionId": "fresh", "cwd": "/repo"}))
    assert "fresh" in pc.claude_code_session_map()
