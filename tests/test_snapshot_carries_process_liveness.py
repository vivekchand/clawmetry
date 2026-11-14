"""The node must ship process-liveness, because the cloud cannot measure it.

The local dashboard settles "is anything actually running?" by reading the
process table (routes/sessions.py::api_live_sessions, 0.12.914). The hosted
dashboard cannot: the container has no access to the user's machine. Without
the node carrying the answer, app.clawmetry.com is left asserting "It's idle
right now." from a snapshot it has no way to doubt.

That is the 2026-10-07 defect: seven Claude Code processes running against a
store whose newest row was 6.1 hours old.

So agentInventory carries ``processesLive``, node-wide and per runtime, and
``None`` when the probe failed, because unknown is not zero.
"""

from __future__ import annotations

import pytest


def _build(monkeypatch, procs):
    """Run the real builder with one Claude Code and one Codex runtime."""
    import clawmetry.sync as sync
    from clawmetry import process_control as pc
    if procs is BaseException:
        def boom():
            raise OSError("no process table")
        monkeypatch.setattr(pc, "live_sessions", boom)
    else:
        monkeypatch.setattr(pc, "live_sessions", lambda: procs)
    rs = {"claude_code": {"sessions": 2}, "codex": {"sessions": 1}}
    return sync._build_agent_inventory(
        rs, {}, {}, {}, {}, ["claude_code", "codex"], {}, "node-1")


def test_the_count_rides_the_snapshot(monkeypatch):
    node_wide, by_rt = _build(monkeypatch, [
        {"pid": 1, "runtime": "claude_code"},
        {"pid": 2, "runtime": "claude_code"},
        {"pid": 3, "runtime": "codex"},
    ])
    assert node_wide.get("processesLive") == 3, (
        "without this the hosted hero cannot tell a quiet machine from a "
        "snapshot that is hours behind")
    for rt, expected in (("claude_code", 2), ("codex", 1)):
        if rt in by_rt:
            assert by_rt[rt].get("processesLive") == expected, (
                "%s must carry its OWN count, never the node total" % rt)


def test_a_failed_probe_is_unknown_not_zero(monkeypatch):
    """A reader that sees 0 would conclude "nothing is running" and go back to
    asserting idle, which is the defect this field exists to prevent."""
    node_wide, by_rt = _build(monkeypatch, BaseException)
    assert node_wide.get("processesLive") is None
    for rt, slice_ in (by_rt or {}).items():
        assert slice_.get("processesLive") is None, rt


def test_no_processes_is_a_real_zero(monkeypatch):
    """A genuinely idle machine must still get a straight answer."""
    node_wide, _ = _build(monkeypatch, [])
    assert node_wide.get("processesLive") == 0


def test_the_probe_cannot_break_the_snapshot(monkeypatch):
    """Inventory is one slice of a shared blob; a probe failure must not cost
    the rest of it."""
    node_wide, _ = _build(monkeypatch, BaseException)
    assert "agents" in node_wide and "liveCounts" in node_wide
