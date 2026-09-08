"""Agent Inventory liveness — the roster must agree with /api/live-sessions.

The roster's ``running`` flag is a PROCESS heartbeat and only OpenClaw/NemoClaw
emit one, so the Agents tab reported "0 of 11 alive / Idle / Resting" for a
Claude Code with four live sessions, on the same node whose Home tab said "4
sessions are working right now" (founder report 2026-08-16). These tests pin
the recency signal that replaced it, and pin it to the SAME 120s/600s windows
``routes/sessions.py::_live_state`` uses so the two surfaces cannot drift.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from clawmetry import sync


def _iso(secs_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=secs_ago)).isoformat()


def _row(sid, runtime, secs_ago, status="active"):
    return {
        "session_id": sid,
        "metadata": {"runtime": runtime},
        "last_active_at": _iso(secs_ago),
        "status": status,
    }


def test_working_and_waiting_use_the_live_sessions_windows():
    """<120s is working, 120-600s is waiting, >600s is neither."""
    rows = [
        _row("claude_code:a", "claude_code", 5),
        _row("claude_code:b", "claude_code", 119),
        _row("claude_code:c", "claude_code", 300),
        _row("claude_code:d", "claude_code", 5000),
    ]
    live = sync._live_counts_by_runtime(rows)
    assert live["claude_code"]["working"] == 2
    assert live["claude_code"]["waiting"] == 1
    # lastSeenSecs is the freshest session regardless of state, so a quiet
    # agent can still say when it last moved.
    assert live["claude_code"]["lastSeenSecs"] <= 6


def test_explicit_terminal_status_beats_recency():
    """A runtime that ASSERTS the session ended is believed over the clock."""
    rows = [_row("codex:done", "codex", 5, status="completed")]
    live = sync._live_counts_by_runtime(rows)
    assert live["codex"]["working"] == 0
    assert live["codex"]["waiting"] == 0
    # ...but it still counts as "last seen", which is a separate question.
    assert live["codex"]["lastSeenSecs"] <= 6


def test_a_freshly_ended_session_is_never_counted_as_alive():
    """The end signal beats recency even when the row is seconds old.

    Drift Bot flagged the ordering here (PR #4911): the blueprint says "an
    explicit end signal always wins over recency", so a session the runtime
    ENDED one second ago must not appear as working. It does still set
    ``lastSeenSecs`` — "when did this agent last move" is a different question
    from "is it alive", and dropping ended rows there would print "never" for
    an agent with obvious recent activity.
    """
    rows = [
        _row("openclaw:just-finished", "openclaw", 1, status="completed"),
        _row("openclaw:also-done", "openclaw", 2, status="failed"),
    ]
    live = sync._live_counts_by_runtime(rows)
    assert live["openclaw"]["working"] == 0
    assert live["openclaw"]["waiting"] == 0
    assert live["openclaw"]["lastSeenSecs"] <= 2


def test_ended_session_does_not_mask_a_live_one_in_the_same_runtime():
    rows = [
        _row("claude_code:ended", "claude_code", 1, status="completed"),
        _row("claude_code:alive", "claude_code", 30),
    ]
    live = sync._live_counts_by_runtime(rows)
    assert live["claude_code"]["working"] == 1


def test_subagents_are_not_counted_as_peers():
    rows = [
        _row("claude_code:subagent-x", "claude_code", 5),
        _row("claude_code:sub-agent-y", "claude_code", 5),
    ]
    assert sync._live_counts_by_runtime(rows) == {}


def test_missing_runtime_falls_back_to_the_openclaw_bucket():
    rows = [{"session_id": "bare-uuid", "metadata": {}, "last_active_at": _iso(10),
             "status": "active"}]
    live = sync._live_counts_by_runtime(rows)
    assert live["openclaw"]["working"] == 1


@pytest.mark.parametrize("bad", [
    [{"session_id": "x", "metadata": {"runtime": "codex"}, "last_active_at": "not-a-date"}],
    [{"session_id": "x", "metadata": {"runtime": "codex"}, "last_active_at": ""}],
    [{"session_id": "x", "metadata": None, "last_active_at": None}],
    ["not-a-dict"],
    None,
])
def test_never_raises_on_junk(bad):
    assert isinstance(sync._live_counts_by_runtime(bad), dict)


def test_future_timestamp_is_clamped_not_trusted():
    """A skewed clock must not be able to report negative age."""
    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    rows = [{"session_id": "claude_code:a", "metadata": {"runtime": "claude_code"},
             "last_active_at": future, "status": "active"}]
    live = sync._live_counts_by_runtime(rows)
    assert live["claude_code"]["lastSeenSecs"] == 0
    assert live["claude_code"]["working"] == 1


def _inventory(live_by_rt):
    runtime_summary = {
        "claude_code": {"sessions": 3, "tokens": 100, "cost_usd": 1.0,
                        "last_activity_ms": 1700000000000},
        "goose": {"sessions": 1, "tokens": 5, "cost_usd": 0.0},
    }
    node_wide, _by_rt = sync._build_agent_inventory(
        runtime_summary, {}, {}, {}, {}, [], {}, "node-1", live_by_rt=live_by_rt,
    )
    return node_wide


def test_inventory_carries_live_counts_per_agent_and_node_wide():
    node = _inventory({"claude_code": {"working": 4, "waiting": 1, "lastSeenSecs": 12}})
    rows = {a["agentKey"]: a for a in node["agents"]}
    assert rows["claude_code"]["liveWorking"] == 4
    assert rows["claude_code"]["liveWaiting"] == 1
    assert rows["claude_code"]["lastSeenSecs"] == 12
    assert rows["claude_code"]["lastActivityMs"] == 1700000000000
    # An agent with no live sessions reports zero, not absent.
    assert rows["goose"]["liveWorking"] == 0
    assert node["liveKnown"] is True
    assert node["liveCounts"] == {"working": 4, "waiting": 1,
                                  "agentsWorking": 1, "agentsWaiting": 0}


def test_unreadable_session_table_is_unknown_not_zero():
    """``None`` must not render as a confident "nothing is running"."""
    node = _inventory(None)
    assert node["liveKnown"] is False
    assert all(a["liveKnown"] is False for a in node["agents"])
    assert node["liveCounts"]["working"] == 0


def test_waiting_only_agent_is_not_double_counted_as_working():
    node = _inventory({"claude_code": {"working": 0, "waiting": 2, "lastSeenSecs": 300}})
    assert node["liveCounts"]["agentsWorking"] == 0
    assert node["liveCounts"]["agentsWaiting"] == 1
