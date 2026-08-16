"""The "needs you" detector — sessions blocked on a human.

Distinct from stuck detection, which finds agents SPINNING through tool
calls. This finds the opposite failure: an agent stopped dead waiting for
someone to answer a permission prompt. A spinning agent burns money and gets
noticed; a blocked one burns nothing and silently never finishes.

The detector is transcript inference, not observation — a permission dialog
is UI state no runtime writes down. These tests pin both the shape it matches
and, just as importantly, the shapes it must NOT match, since a false
"needs you" trains people to ignore the list.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    return ls.get_store()


def _ago(seconds: int) -> str:
    """Naive local wall-clock ISO stamp, matching what the store writes."""
    return (datetime.now() - timedelta(seconds=seconds)).isoformat()


def _session(store, sid, *, seconds_idle=300, status="active", **kw):
    row = {
        "agent_type": "claude_code",
        "session_id": sid,
        "status": status,
        "started_at": _ago(seconds_idle + 600),
        "last_active_at": _ago(seconds_idle),
    }
    row.update(kw)
    store.ingest_sessions_batch([row])


def _event(store, sid, event_type, seconds_ago, data=None, eid=None):
    store.ingest({
        "id": eid or f"{sid}:{event_type}:{seconds_ago}",
        "agent_type": "claude_code",
        "node_id": "test-node",
        "session_id": sid,
        "event_type": event_type,
        "ts": _ago(seconds_ago),
        "data": data or {},
    })
    store.flush()


def _detect(store):
    from clawmetry.sync import _detect_attention_sessions
    return _detect_attention_sessions(store)


# ── the shape it should match ───────────────────────────────────────────────

def test_pending_tool_call_flags_session(store):
    _session(store, "s-blocked", seconds_idle=300)
    _event(store, "s-blocked", "tool_call", 300,
           {"tool": "Bash", "input": {"command": "rm -rf build"}})
    rows = _detect(store)
    assert [r["session_id"] for r in rows] == ["s-blocked"]
    r = rows[0]
    assert r["state"] == "waiting_approval"
    assert r["waiting_seconds"] >= 45
    assert r["runtime"] == "claude_code"


def test_result_is_labelled_inference_not_certainty(store):
    """We read a transcript; we do not observe the dialog. Callers render
    that distinction, so the field must always be present and honest."""
    _session(store, "s-honest", seconds_idle=300)
    _event(store, "s-honest", "tool_call", 300, {"tool": "Bash"})
    assert _detect(store)[0]["signal"] == "inferred"


def test_tool_name_is_surfaced(store):
    """Knowing it is Bash rather than Read is most of what someone needs to
    decide whether to go approve it."""
    _session(store, "s-tool", seconds_idle=300)
    _event(store, "s-tool", "tool_call", 300, {"tool": "Bash"})
    assert _detect(store)[0]["tool"] == "Bash"


def test_location_rides_along(store):
    """The row is useless without saying WHICH project is blocked."""
    _session(store, "s-loc", seconds_idle=300,
             cwd="/Users/dev/projects/clawmetry", git_branch="main",
             title="Refactor ingest")
    _event(store, "s-loc", "tool_call", 300, {"tool": "Bash"})
    r = _detect(store)[0]
    assert r["cwd"] == "/Users/dev/projects/clawmetry"
    assert r["git_branch"] == "main"
    assert r["title"] == "Refactor ingest"


def test_longest_waiting_first(store):
    _session(store, "s-recent", seconds_idle=100)
    _event(store, "s-recent", "tool_call", 100, {"tool": "Read"})
    _session(store, "s-old", seconds_idle=900)
    _event(store, "s-old", "tool_call", 900, {"tool": "Bash"})
    assert [r["session_id"] for r in _detect(store)] == ["s-old", "s-recent"]


# ── real runtime envelopes ──────────────────────────────────────────────────
#
# These are the shapes that actually appear on disk, and the reason an
# earlier version of this detector silently found nothing: on Claude Code a
# pending tool call is NOT a `tool_call` event. It is an `assistant` envelope
# whose message.content carries a tool_use block and no text. Classifying by
# envelope type alone treated that as "the agent replied" and bailed.

def test_claude_code_assistant_envelope_hosting_tool_use(store):
    """The real Claude Code shape, copied from a live transcript."""
    _session(store, "s-cc", seconds_idle=300)
    _event(store, "s-cc", "assistant", 300, {
        "role": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_01", "name": "Bash",
             "input": {"command": "rm -rf build"}},
        ]},
    })
    rows = _detect(store)
    assert len(rows) == 1, "a tool-only assistant turn IS a pending tool call"
    assert rows[0]["tool"] == "Bash"


def test_assistant_envelope_with_text_is_a_reply_not_a_block(store):
    """Same envelope type, but it said something — the agent got far enough
    to reply, so it is not sitting on an unanswered prompt."""
    _session(store, "s-replied", seconds_idle=300)
    _event(store, "s-replied", "assistant", 300, {
        "role": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Here is what I found."},
        ]},
    })
    assert _detect(store) == []


def test_openclaw_v3_model_completed_hosting_tool(store):
    """OpenClaw v3 hosts its tool calls in ``data.toolMetas`` rather than
    message.content — a different shape hitting the same envelope trap."""
    _session(store, "s-oc", seconds_idle=300)
    _event(store, "s-oc", "model.completed", 300, {
        "role": "assistant",
        "toolMetas": [{"name": "shell"}],
    })
    rows = _detect(store)
    assert len(rows) == 1
    assert rows[0]["tool"] == "shell"


def test_mixed_text_and_tool_turn_counts_as_reply(store):
    """An assistant turn that both explains and calls a tool has already
    communicated, so it does not read as blocked-and-silent."""
    _session(store, "s-mixed", seconds_idle=300)
    _event(store, "s-mixed", "assistant", 300, {
        "role": "assistant",
        "message": {"content": [
            {"type": "text", "text": "Running the build now."},
            {"type": "tool_use", "name": "Bash", "input": {}},
        ]},
    })
    assert _detect(store) == []


# ── the shapes it must NOT match ────────────────────────────────────────────

def test_resolved_tool_is_not_blocked(store):
    """The tool came back — the agent is working, not waiting."""
    _session(store, "s-done", seconds_idle=300)
    _event(store, "s-done", "tool_call", 400, {"tool": "Bash"}, eid="a")
    _event(store, "s-done", "tool_result", 300, {"ok": True}, eid="b")
    assert _detect(store) == []


def test_assistant_turn_after_tool_is_not_blocked(store):
    """The agent moved on under its own power."""
    _session(store, "s-moved", seconds_idle=300)
    _event(store, "s-moved", "tool_call", 400, {"tool": "Bash"}, eid="a")
    _event(store, "s-moved", "assistant", 300, {"content": "done"}, eid="b")
    assert _detect(store) == []


def test_fresh_tool_call_is_not_blocked(store):
    """A tool that started two seconds ago is just a tool running. This is
    the false positive that would make the whole feature untrustworthy."""
    _session(store, "s-fresh", seconds_idle=2)
    _event(store, "s-fresh", "tool_call", 2, {"tool": "Bash"})
    assert _detect(store) == []


def test_ended_session_is_never_waiting(store):
    _session(store, "s-ended", seconds_idle=300, status="completed",
             ended_at=_ago(250))
    _event(store, "s-ended", "tool_call", 300, {"tool": "Bash"})
    assert _detect(store) == []


def test_abandoned_session_falls_out_of_the_list(store):
    """Flagging day-old sessions forever trains people to ignore the list."""
    _session(store, "s-abandoned", seconds_idle=60 * 60 * 24)
    _event(store, "s-abandoned", "tool_call", 60 * 60 * 24, {"tool": "Bash"})
    assert _detect(store) == []


def test_session_with_no_events_is_not_flagged(store):
    _session(store, "s-empty", seconds_idle=300)
    assert _detect(store) == []


def test_user_prompt_pending_is_not_an_approval(store):
    """A user turn is progress, not a blocked tool."""
    _session(store, "s-user", seconds_idle=300)
    _event(store, "s-user", "user", 300, {"content": "hello"})
    assert _detect(store) == []


# ── persistence onto session rows ───────────────────────────────────────────

def test_attention_persists_to_session_rows(store):
    _session(store, "s-persist", seconds_idle=300, cwd="/p/app", git_branch="main")
    _event(store, "s-persist", "tool_call", 300, {"tool": "Bash"})
    from clawmetry.sync import _refresh_attention_cache
    assert _refresh_attention_cache(store) == 1
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "s-persist"][0]
    assert row["attention_state"] == "waiting_approval"
    assert row["attention_signal"] == "inferred"
    assert row["attention_tool"] == "Bash"
    assert row["attention_since"] is not None


def test_attention_clears_once_answered(store):
    """A badge that persists after you answered is worse than no badge --
    it teaches people to ignore the real ones."""
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "s-clear", seconds_idle=300)
    _event(store, "s-clear", "tool_call", 300, {"tool": "Bash"}, eid="a")
    _refresh_attention_cache(store)
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-clear"][0]["attention_state"] is not None

    # The human approves; the tool comes back.
    _event(store, "s-clear", "tool_result", 1, {"ok": True}, eid="b")
    assert _refresh_attention_cache(store) == 0
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "s-clear"][0]
    assert row["attention_state"] is None
    assert row["attention_tool"] is None


def test_apply_attention_leaves_other_columns_alone(store):
    _session(store, "s-safe", seconds_idle=300, title="Important",
             cwd="/p/app", git_branch="main")
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-safe",
        "total_tokens": 999, "cost_usd": 1.25, "status": "active",
    }])
    store.apply_session_attention([{
        "session_id": "s-safe", "runtime": "claude_code",
        "state": "waiting_approval", "signal": "inferred",
        "tool": "Bash", "waiting_seconds": 120,
    }])
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "s-safe"][0]
    assert row["attention_state"] == "waiting_approval"
    assert row["total_tokens"] == 999
    assert row["cost_usd"] == pytest.approx(1.25)
    assert row["cwd"] == "/p/app"
    assert row["git_branch"] == "main"


def test_apply_attention_tolerates_junk(store):
    assert store.apply_session_attention(
        [None, "x", {}, {"session_id": ""}]) == 0


# ── hook rows outrank, and survive, the inference pass ──────────────────────
#
# A permission dialog leaves NO transcript event, so the inference pass
# literally cannot see one. If its full-set replace were allowed to touch hook
# rows it would wipe every ground-truth badge a second after the runtime set
# it — the feature would look broken precisely when it was most right.

def test_hook_row_survives_the_inference_pass(store):
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "s-hook", seconds_idle=300)
    store.set_session_attention("s-hook", agent_type="claude_code",
                                tool="Bash", signal="hook")
    _refresh_attention_cache(store)          # finds nothing; must not clear
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "s-hook"][0]
    assert row["attention_state"] == "waiting_approval"
    assert row["attention_signal"] == "hook"
    assert row["attention_tool"] == "Bash"


def test_inference_never_downgrades_a_hook_row(store):
    """Same session flagged by both paths: hook must win."""
    _session(store, "s-both", seconds_idle=300)
    _event(store, "s-both", "tool_call", 300, {"tool": "Read"})
    store.set_session_attention("s-both", agent_type="claude_code",
                                tool="Bash", signal="hook")
    from clawmetry.sync import _refresh_attention_cache
    _refresh_attention_cache(store)
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "s-both"][0]
    assert row["attention_signal"] == "hook"
    assert row["attention_tool"] == "Bash"


def test_inferred_rows_are_still_replaced(store):
    """The carve-out must not accidentally freeze inferred rows too."""
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "s-inf", seconds_idle=300)
    _event(store, "s-inf", "tool_call", 300, {"tool": "Bash"}, eid="a")
    _refresh_attention_cache(store)
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-inf"][0]["attention_state"] is not None
    _event(store, "s-inf", "tool_result", 1, {"ok": True}, eid="b")
    _refresh_attention_cache(store)
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-inf"][0]["attention_state"] is None


def test_clear_session_attention_drops_a_hook_row(store):
    _session(store, "s-clr", seconds_idle=300)
    store.set_session_attention("s-clr", agent_type="claude_code", tool="Bash")
    assert store.clear_session_attention("s-clr", agent_type="claude_code")
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-clr"][0]["attention_state"] is None


def test_stale_hook_row_is_aged_out(store):
    """A hook process that dies mid-prompt must not pin the badge forever."""
    import time as _t
    _session(store, "s-stale", seconds_idle=300)
    store.set_session_attention("s-stale", agent_type="claude_code", tool="Bash")
    # A fresh prompt is never expired -- people do leave prompts open.
    assert store.expire_stale_hook_attention(7200) == 0
    # Backdate it past the window (the method floors max_age at 60s, so the
    # row has to move, not the window).
    with store._write_lock:
        store._conn.execute(
            "UPDATE sessions SET attention_since = ? WHERE session_id = ?",
            [int((_t.time() - 10800) * 1000), "s-stale"])
    assert store.expire_stale_hook_attention(7200) >= 1
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-stale"][0]["attention_state"] is None


def test_hook_row_on_an_ended_session_is_cleared(store):
    _session(store, "s-done", seconds_idle=300)
    store.set_session_attention("s-done", agent_type="claude_code", tool="Bash")
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-done",
        "status": "completed", "ended_at": _ago(10),
    }])
    assert store.expire_stale_hook_attention(7200) >= 1
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "s-done"][0]["attention_state"] is None


def test_hook_write_paths_are_allowlisted_for_the_daemon_proxy():
    """The hook receiver runs in the dashboard process while the daemon owns
    the writer lock, so an unlisted method is a SILENT no-op and the badge
    would simply never appear."""
    from routes.local_query import _DAEMON_METHODS
    assert "set_session_attention" in _DAEMON_METHODS
    assert "clear_session_attention" in _DAEMON_METHODS


# ── the approvals queue as a source ─────────────────────────────────────────
#
# A pending approval is a human who HAS been asked and has not answered — as
# certain as a hook, and it covers every runtime the approvals engine reaches
# including ones with no hook of their own. But its PROVENANCE differs, and
# provenance decides who clears the row.

def _pending_approval(store, sid, action="rm -rf build"):
    store.ingest_approval({
        "id": "ap-" + sid,
        "requestor_session_id": sid,
        "action": action,
        "status": "pending",
        "created_at": _ago(200),
    })


def test_pending_approval_flags_its_session(store):
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "claude_code:ap1", seconds_idle=300)
    _pending_approval(store, "claude_code:ap1")
    _refresh_attention_cache(store)
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "claude_code:ap1"][0]
    assert row["attention_state"] == "waiting_approval"
    assert row["attention_signal"] == "queue"
    assert row["attention_tool"] == "rm -rf build"


def test_queue_row_clears_when_the_approval_is_answered(store):
    """The reason queue rows are NOT marked 'hook': they must vanish with the
    decision, not linger for the hook row's two-hour grace."""
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "claude_code:ap2", seconds_idle=300)
    _pending_approval(store, "claude_code:ap2")
    _refresh_attention_cache(store)
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "claude_code:ap2"][0]["attention_state"]

    store.update_approval_decision("ap-claude_code:ap2", decision="approved",
                                   resolver="tester", reason="fine")
    _refresh_attention_cache(store)
    assert [r for r in store.query_sessions_table(limit=20)
            if r["session_id"] == "claude_code:ap2"][0]["attention_state"] is None


def test_queue_beats_inference_for_the_same_session(store):
    from clawmetry.sync import _refresh_attention_cache
    _session(store, "claude_code:ap3", seconds_idle=300)
    _event(store, "claude_code:ap3", "tool_call", 300, {"tool": "Read"})
    _pending_approval(store, "claude_code:ap3", action="Bash")
    _refresh_attention_cache(store)
    row = [r for r in store.query_sessions_table(limit=20)
           if r["session_id"] == "claude_code:ap3"][0]
    assert row["attention_signal"] == "queue"
    assert row["attention_tool"] == "Bash"


def test_bare_session_id_reads_as_openclaw(store):
    """Namespaced ids carry their runtime; a bare one is OpenClaw."""
    from clawmetry.sync import _pending_approval_attention
    _pending_approval(store, "plain-session")
    rows = _pending_approval_attention(store)
    assert rows and rows[0]["runtime"] == "openclaw"


def test_confirmed_signals_are_defined_once(store):
    """hook and queue are equally certain; only 'inferred' is a guess."""
    from routes.attention import CONFIRMED_SIGNALS
    assert CONFIRMED_SIGNALS == {"hook", "queue"}
    assert "inferred" not in CONFIRMED_SIGNALS


# ── never take the daemon down ──────────────────────────────────────────────

def test_store_failure_yields_empty_not_exception():
    class Broken:
        def query_sessions_table(self, **kw):
            raise RuntimeError("duckdb exploded")

    assert _detect(Broken()) == []


def test_event_query_failure_skips_that_session(store):
    _session(store, "s-ok", seconds_idle=300)
    _event(store, "s-ok", "tool_call", 300, {"tool": "Bash"})

    class PartlyBroken:
        def query_sessions_table(self, **kw):
            return store.query_sessions_table(**kw)

        def query_events(self, **kw):
            raise RuntimeError("boom")

    assert _detect(PartlyBroken()) == []


def test_malformed_rows_are_tolerated():
    class Junk:
        def query_sessions_table(self, **kw):
            return [None, "not-a-dict", {}, {"session_id": ""}]

    assert _detect(Junk()) == []
