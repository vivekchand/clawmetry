"""``/api/guard/sessions`` must carry the two fields the tab needs after a Kill.

The store's ``status`` column is only as fresh as the last sync cycle, so a
session the operator just killed still reads ``running`` there for the next
60-80 seconds. The row therefore has to carry a SECOND, live answer —
``control_state`` — and the resume instruction that goes with it, or the tab is
left rendering "Running" beside a greyed-out control, which is what the field
report showed.

``resume`` is sent on every row, not only the dead ones: a row that flips to
``exited`` between two polls must already have its answer in hand.
"""
import json

import clawmetry.process_control as pc
import pytest
from flask import Flask

import routes.guard as guard


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    return app.test_client()


@pytest.fixture
def store_rows(monkeypatch):
    state = {"sessions": [], "signals": []}

    def _call(method, **kwargs):
        if method == "query_sessions_table":
            return state["sessions"]
        if method == "query_recent_loop_signals":
            return state["signals"]
        return None

    monkeypatch.setattr(guard, "_ls_call", _call)
    # No live probe: these tests are about what the STORE's rows say.
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    return state


def _rows(client):
    resp = client.get("/api/guard/sessions")
    assert resp.status_code == 200
    return json.loads(resp.data)["sessions"]


def _session(sid, runtime="claude_code", **over):
    row = {"session_id": sid, "agent_type": "openclaw", "status": "running",
           "title": "a session", "cost_usd": 1.25, "metadata": {}}
    row.update(over)
    return row


@pytest.fixture
def dead_claude(monkeypatch):
    """A claude_code session the runtime records no process for — the state a
    session lands in the instant Kill succeeds."""
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, a: "claude_code")
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": False,
                                         "reason": "session_not_in_claude_map"})


def test_a_killed_session_reports_exited_and_how_to_resume_it(
        client, store_rows, dead_claude):
    store_rows["sessions"] = [_session("claude_code:47c0dac8-d8ca")]
    row = _rows(client)[0]

    assert row["controllable"] is False
    # The word the tab branches on. Without it the row is indistinguishable
    # from a Grok Bot session that never had a local process at all.
    assert row["control_state"] == "exited"

    resume = row["resume"]
    assert resume["kind"] == "command"
    # The NATIVE id, not the store's namespaced one: `claude --resume
    # claude_code:47c0…` is a command line that fails.
    assert resume["command"] == "claude --resume 47c0dac8-d8ca"


def test_the_resume_answer_rides_along_on_a_live_row_too(
        client, store_rows, monkeypatch):
    """So the client never has to make a second request the moment a row dies."""
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, a: "claude_code")
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": True, "pid": 4242})
    monkeypatch.setattr(pc, "is_alive", lambda pid: True)

    store_rows["sessions"] = [_session("claude_code:live-1")]
    row = _rows(client)[0]
    assert row["controllable"] is True
    assert row["control_state"] == "controllable"
    assert row["resume"]["command"] == "claude --resume live-1"


def test_a_hosted_runtime_is_not_dressed_up_as_stopped(
        client, store_rows, monkeypatch):
    """grok_bot runs on xAI's cloud VM. It did not stop; there was never a
    local process. The tab must not offer to resume it as if there had been."""
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, a: "grok_bot")
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})

    store_rows["sessions"] = [_session("grok_bot:1", runtime="grok_bot")]
    row = _rows(client)[0]
    assert row["control_state"] == "unsupported"
    assert row["resume"]["kind"] == "app"
    assert row["resume"]["command"] == ""


def test_a_gateway_supplied_resume_command_wins(client, store_rows, monkeypatch):
    """OpenClaw's gateway knows the live session key; the shipped table only
    knows the command's shape."""
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, a: "openclaw")
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    monkeypatch.setattr(pc, "openclaw_pause_capability",
                        lambda: {"effective": False, "detail": "no proxy"})

    store_rows["sessions"] = [_session(
        "sess-pty", runtime="openclaw",
        metadata={"resumeCommand": "openclaw attach sess-pty"})]
    row = _rows(client)[0]
    assert row["resume"]["command"] == "openclaw attach sess-pty"


def test_a_broken_hint_module_does_not_take_the_tab_down(
        client, store_rows, dead_claude, monkeypatch):
    """Never crash on bad input: the row must still render without a hint."""
    def _boom(*a, **k):
        raise RuntimeError("hint lookup exploded")

    from clawmetry import resume_hints
    monkeypatch.setattr(resume_hints, "resume_hint", _boom)

    store_rows["sessions"] = [_session("claude_code:x")]
    row = _rows(client)[0]
    assert row["control_state"] == "exited"
    assert row["resume"]["kind"] == "unknown"
