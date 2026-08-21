"""Tests for the sync.py kill/pause/resume dispatch wiring.

Feeds fake kill_session / pause_session / resume_session actions through
``_dispatch_pending_action`` and asserts:

  * the right process_control path is called,
  * a result blob is POSTed back to /ingest/cache under the action's cache_key,
  * the proxy HITL pause file is written on kill/pause and removed on resume,
  * UNKNOWN action types are still dropped silently (no POST).

The cloud POST and the actual signal helpers are monkeypatched, so no real
process is touched and no network call is made.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.sync as sync  # noqa: E402
import clawmetry.process_control as pc  # noqa: E402


def _wait(predicate, timeout=4.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


@pytest.fixture
def captured_posts(monkeypatch):
    posts = []

    def _fake_post(path, payload, api_key, timeout=45):
        posts.append((path, payload))
        return {"ok": True}

    monkeypatch.setattr(sync, "_post", _fake_post)
    # encrypt_payload must not need a real key; pass through a marker.
    monkeypatch.setattr(sync, "encrypt_payload",
                        lambda obj, key: b"ENC:" + repr(obj).encode()[:200])
    return posts


@pytest.fixture
def hitl_dir(tmp_path, monkeypatch):
    # Redirect the HITL pause-file path into tmp by monkeypatching Path.home.
    import pathlib
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(sync.Path, "home", staticmethod(lambda: home))
    return home / ".clawmetry" / "hitl"


_CFG = {"encryption_key": "k" * 44, "api_key": "key123", "node_id": "node-1"}


def test_unknown_action_type_still_dropped(captured_posts):
    sync._dispatch_pending_action(_CFG, {"type": "definitely_not_a_real_action",
                                         "cache_key": "ck", "session_id": "s"})
    time.sleep(0.3)
    assert captured_posts == []


def test_kill_session_family_calls_process_control_and_posts(
        captured_posts, hitl_dir, monkeypatch):
    calls = {}

    def _fake_kill(runtime, session_id, cwd="", mode="kill"):
        calls["kill"] = (runtime, session_id, mode)
        return {"ok": True, "action": "graceful_kill", "pid": 4242,
                "runtime": runtime, "detail": "terminated"}

    monkeypatch.setattr(pc, "kill_session", _fake_kill)

    action = {"type": "kill_session", "session_id": "sess-xyz",
              "runtime": "claude_code", "cache_key": "ck-1", "id": "a1"}
    sync._dispatch_pending_action(_CFG, action)

    assert _wait(lambda: len(captured_posts) == 1), "no result posted"
    path, payload = captured_posts[0]
    assert path == "/ingest/cache"
    assert payload["cache_key"] == "ck-1"
    assert payload["shape"] == "process_control"
    assert payload["node_id"] == "node-1"
    # No mode given -> empty string passed through; kill_session treats any
    # non-"stop" mode as a graceful kill.
    assert calls["kill"] == ("claude_code", "sess-xyz", "")
    # belt-and-suspenders HITL pause file written on kill
    assert (hitl_dir / "pause_sess-xyz").exists()


def test_kill_session_stop_mode_passthrough(captured_posts, hitl_dir, monkeypatch):
    seen = {}

    def _fake_kill(runtime, session_id, cwd="", mode="kill"):
        seen["mode"] = mode
        return {"ok": True, "pid": 1, "detail": "sigint_sent"}

    monkeypatch.setattr(pc, "kill_session", _fake_kill)
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "s2", "runtime": "codex",
        "cache_key": "ck-2", "mode": "stop",
    })
    assert _wait(lambda: len(captured_posts) == 1)
    assert seen["mode"] == "stop"


def test_pause_then_resume_flips_hitl_file(captured_posts, hitl_dir, monkeypatch):
    monkeypatch.setattr(pc, "pause_session",
                        lambda r, s, c="": {"ok": True, "detail": "paused", "pid": 9})
    monkeypatch.setattr(pc, "resume_session",
                        lambda r, s, c="": {"ok": True, "detail": "resumed", "pid": 9})

    sync._dispatch_pending_action(_CFG, {
        "type": "pause_session", "session_id": "p1", "runtime": "goose",
        "cache_key": "ck-p"})
    assert _wait(lambda: (hitl_dir / "pause_p1").exists())

    sync._dispatch_pending_action(_CFG, {
        "type": "resume_session", "session_id": "p1", "runtime": "goose",
        "cache_key": "ck-r"})
    assert _wait(lambda: not (hitl_dir / "pause_p1").exists())
    assert _wait(lambda: len(captured_posts) == 2)


def test_openclaw_kill_uses_cli_cancel(captured_posts, hitl_dir, monkeypatch):
    seen = {}

    def _fake_cancel(lookup, timeout=30):
        seen["lookup"] = lookup
        return {"ok": True, "scope_pending": False, "error": "", "raw": ""}

    monkeypatch.setattr(sync, "_openclaw_cancel_task", _fake_cancel)
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "ocsess", "runtime": "openclaw",
        "cache_key": "ck-oc"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert seen["lookup"] == "ocsess"
    _, payload = captured_posts[0]
    assert payload["shape"] == "process_control"


def test_openclaw_pause_is_honest_unsupported(captured_posts, hitl_dir, monkeypatch):
    # pause/resume have no clean OpenClaw primitive — must report unsupported,
    # but still flip the HITL pause file so the user's click has a real effect.
    sync._dispatch_pending_action(_CFG, {
        "type": "pause_session", "session_id": "ocp", "runtime": "openclaw",
        "cache_key": "ck-ocp"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert (hitl_dir / "pause_ocp").exists()
    _, payload = captured_posts[0]
    # blob is our marker bytes; assert the repr embeds unsupported + the shape.
    assert b"unsupported" in payload["blob"]


def test_missing_cache_key_is_noop(captured_posts, hitl_dir):
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "s", "runtime": "claude_code"})
    time.sleep(0.3)
    assert captured_posts == []


def test_action_types_in_allowlist():
    for t in ("kill_session", "pause_session", "resume_session"):
        assert t in sync._PENDING_ACTIONS


def test_kill_consults_registered_handler_first(captured_posts, hitl_dir,
                                                monkeypatch):
    """n8n / antigravity / nanoclaw kills registered via
    approvals.register_kill_handler must be reachable from the cloud Stop
    button, not only from the approvals deny path (2026-08-19)."""
    from clawmetry import approvals
    seen = {}
    monkeypatch.setitem(approvals.KILL_HANDLERS, "n8n",
                        lambda ns_id: seen.setdefault("ns_id", ns_id) or True)
    pc_called = {}
    monkeypatch.setattr(pc, "kill_session",
                        lambda *a, **k: pc_called.setdefault("hit", a) or
                        {"ok": False})
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "exec-77", "runtime": "n8n",
        "cache_key": "ck-n8n", "id": "a1"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert seen["ns_id"] == "n8n:exec-77"
    # handler succeeded -> the signal engine must NOT be consulted
    assert "hit" not in pc_called


def test_kill_falls_back_to_signals_when_handler_fails(captured_posts,
                                                       hitl_dir, monkeypatch):
    from clawmetry import approvals
    monkeypatch.setitem(approvals.KILL_HANDLERS, "copilot", lambda ns_id: False)
    calls = {}

    def _fake_kill(runtime, session_id, cwd="", mode="kill"):
        calls["kill"] = (runtime, session_id, cwd)
        return {"ok": True, "action": "graceful_kill", "pid": 7,
                "runtime": runtime, "detail": "terminated"}

    monkeypatch.setattr(pc, "kill_session", _fake_kill)
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "sid-1", "runtime": "copilot",
        "cache_key": "ck-cp", "id": "a2"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert calls["kill"][0] == "copilot"


def test_cwd_backfill_from_store_when_action_lacks_cwd(captured_posts,
                                                       hitl_dir, monkeypatch):
    """The cloud relay sends no cwd; the daemon must look it up from the
    session row before resolving codex/goose/opencode/aider (2026-08-19 —
    without this every cwd-resolved kill failed with no_cwd)."""
    monkeypatch.setattr(sync, "_proc_control_cwd_backfill",
                        lambda rt, sid: "/work/dir")
    calls = {}

    def _fake_kill(runtime, session_id, cwd="", mode="kill"):
        calls["kill"] = (runtime, session_id, cwd)
        return {"ok": True, "action": "graceful_kill", "pid": 9,
                "runtime": runtime, "detail": "terminated"}

    monkeypatch.setattr(pc, "kill_session", _fake_kill)
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "sid-2", "runtime": "goose",
        "cache_key": "ck-g", "id": "a3"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert calls["kill"] == ("goose", "sid-2", "/work/dir")


def test_cwd_backfill_reads_store_row(monkeypatch, tmp_path):
    """_proc_control_cwd_backfill prefers sessions.cwd, falls back to the
    metadata aliases (goose workingDir / opencode directory)."""
    class _FakeStore:
        def __init__(self, rows):
            self.rows = rows
            self.calls = []

        def get_session_location(self, sid, agent_type=None):
            self.calls.append((sid, agent_type))
            return self.rows.get(sid)

    from clawmetry import local_store as _ls
    rows = {
        "goose:s1": {"cwd": None,
                     "metadata": {"workingDir": "/proj/demo"}},
        "opencode:s2": {"cwd": "/direct/col",
                        "metadata": {"directory": "/ignored"}},
    }
    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: _FakeStore(rows))
    assert sync._proc_control_cwd_backfill("goose", "s1") == "/proj/demo"
    assert sync._proc_control_cwd_backfill("opencode", "s2") == "/direct/col"
    assert sync._proc_control_cwd_backfill("aider", "nope") == ""


def test_nemoclaw_kill_routes_to_openclaw_cancel(captured_posts, hitl_dir,
                                                 monkeypatch):
    seen = {}
    monkeypatch.setattr(sync, "_openclaw_cancel_task",
                        lambda sid: seen.setdefault("sid", sid) or
                        {"ok": True, "scope_pending": False, "error": ""})
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "task-9", "runtime": "nemoclaw",
        "cache_key": "ck-n", "id": "a4"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert seen["sid"] == "task-9"


def test_cwd_backfill_is_runtime_scoped_and_has_no_bare_fallback(monkeypatch):
    """An unscoped/bare-id lookup could return a DIFFERENT runtime's
    directory, which would then be used to pick a process to signal."""
    seen = []

    class _Store:
        def get_session_location(self, sid, agent_type=None):
            seen.append((sid, agent_type))
            return None

    from clawmetry import local_store as _ls
    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: _Store())
    assert sync._proc_control_cwd_backfill("kimi", "uuid-1") == ""
    # exactly one lookup, namespaced, and scoped by agent_type
    assert seen == [("kimi:uuid-1", "openclaw")]


def test_relayed_runtime_case_is_normalised(captured_posts, hitl_dir,
                                             monkeypatch):
    """A relayed 'Copilot' must hit the same paths as 'copilot' — the
    handler lookup lowercases, so the SUPPORTED_RUNTIMES check must too."""
    calls = {}

    def _fake_kill(runtime, session_id, cwd="", mode="kill"):
        calls["kill"] = (runtime, session_id)
        return {"ok": True, "action": "graceful_kill", "pid": 5,
                "runtime": runtime, "detail": "terminated"}

    monkeypatch.setattr(pc, "kill_session", _fake_kill)
    monkeypatch.setattr(sync, "_proc_control_cwd_backfill", lambda rt, sid: "/w")
    sync._dispatch_pending_action(_CFG, {
        "type": "kill_session", "session_id": "s-1", "runtime": "Copilot",
        "cache_key": "ck-case", "id": "a9"})
    assert _wait(lambda: len(captured_posts) == 1)
    assert calls["kill"][0] == "copilot"
