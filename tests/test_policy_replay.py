"""Tests for policy replay (eval-before-enable) + monitor (dry-run) mode.

Two features adopted from the agent-guardrail tools' playbook (CrabTrap's
"replay the audit log against a candidate policy" eval loop):

  1. ``clawmetry.approvals.replay_policy`` — a PURE function that replays a
     candidate policy over historical events-table rows and reports what it
     WOULD have paused (counts, per-runtime / per-tool buckets, samples).
     Exposed at ``POST /api/policy/replay`` (routes/policy.py).
  2. ``action: monitor`` policies — ``process_tool_call`` records a
     ``simulated`` approval row and returns immediately: no cloud
     round-trip, no blocking, no session kill.

Revert-proof: with the monitor branch removed, the monitor tests fail
because ``process_tool_call`` reaches the cloud round-trip (the patched
``_post_approval_request`` fails the test). With ``replay_policy`` removed,
the replay tests fail on import and the route returns non-200.

Synthetic rows are fine here — these are isolated unit tests of pure
matching/replay logic, not a claim that the live pipeline works (that is
the watcher + E2E suites' job).
"""

from __future__ import annotations

import json
import os
import sys
import uuid

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import approvals


# ── helpers ───────────────────────────────────────────────────────────────


def _row(eid: str, sid: str, ts: str, tool_blocks, flavor: str = "openclaw") -> dict:
    """Build an events-table row carrying assistant tool-invocation blocks.

    ``flavor='openclaw'`` emits ``toolCall``+``arguments`` blocks;
    ``flavor='claude'`` emits ``tool_use``+``input`` (Claude Code shape).
    """
    blocks = []
    for i, (name, args) in enumerate(tool_blocks):
        if flavor == "claude":
            blocks.append({"type": "tool_use", "id": f"{eid}-{i}",
                           "name": name, "input": args})
        else:
            blocks.append({"type": "toolCall", "id": f"{eid}-{i}",
                           "name": name, "arguments": args})
    return {
        "id": eid,
        "session_id": sid,
        "ts": ts,
        "event_type": "message",
        "data": {"type": "message",
                 "message": {"role": "assistant", "content": blocks}},
    }


_RM_POLICY = {
    "name": "gate-rm-rf",
    "match": {"tool": "exec", "command_regex": r"rm\s+-rf"},
    "action": "require_approval",
}


# ── replay_policy (pure) ──────────────────────────────────────────────────


def test_replay_matches_across_harness_aliases():
    """A policy authored for ``exec`` must match OpenClaw ``exec`` AND Claude
    Code ``Bash`` (tool_use) rows, with per-runtime attribution."""
    rows = [
        _row("e1", "0f0e-uuid-openclaw", "2026-06-01T00:00:00Z",
             [("exec", {"command": "rm -rf /tmp/scratch"})]),
        _row("e2", "claude_code:sess-1", "2026-06-01T00:00:01Z",
             [("Bash", {"command": "rm -rf node_modules"})], flavor="claude"),
        _row("e3", "claude_code:sess-1", "2026-06-01T00:00:02Z",
             [("Bash", {"command": "ls -la"})], flavor="claude"),
        _row("e4", "0f0e-uuid-openclaw", "2026-06-01T00:00:03Z",
             [("read", {"path": "/etc/hosts"})]),
    ]
    out = approvals.replay_policy(_RM_POLICY, rows)
    assert out["ok"] is True
    assert out["policy"] == "gate-rm-rf"
    assert out["scanned_events"] == 4
    assert out["scanned_tool_calls"] == 4
    assert out["matches"] == 2
    assert out["by_runtime"] == {"openclaw": 1, "claude_code": 1}
    assert out["by_tool"] == {"exec": 2}
    assert len(out["samples"]) == 2
    assert all("rm -rf" in s["command"] for s in out["samples"])


def test_replay_command_not_regex_excludes():
    policy = {
        "name": "gate-push-except-fork",
        "match": {"tool": "exec",
                  "command_regex": r"git\s+push",
                  "command_not_regex": r"my-fork"},
    }
    rows = [
        _row("e1", "s", "2026-06-01T00:00:00Z",
             [("exec", {"command": "git push origin main --force"})]),
        _row("e2", "s", "2026-06-01T00:00:01Z",
             [("exec", {"command": "git push my-fork feature"})]),
    ]
    out = approvals.replay_policy(policy, rows)
    assert out["matches"] == 1
    assert out["samples"][0]["command"] == "git push origin main --force"


def test_replay_invalid_regex_returns_error_not_crash():
    out = approvals.replay_policy(
        {"name": "bad", "match": {"command_regex": "["}}, [])
    assert out["ok"] is False
    assert "invalid policy" in out["error"]


def test_replay_dedups_row_ids_and_caps_samples():
    """Merged event_type queries can return the same row twice — count once.
    Samples cap at max_samples while ``matches`` keeps counting."""
    rows = []
    for i in range(30):
        rows.append(_row(f"e{i}", "s", f"2026-06-01T00:00:{i:02d}Z",
                         [("exec", {"command": "rm -rf /tmp/x"})]))
    rows.append(dict(rows[0]))  # duplicate id e0 from the second query
    out = approvals.replay_policy(_RM_POLICY, rows)
    assert out["scanned_events"] == 30
    assert out["matches"] == 30
    assert len(out["samples"]) == 20  # default max_samples


def test_replay_tolerates_data_as_json_string():
    """Cross-process transports may serialise the ``data`` column."""
    row = _row("e1", "s", "2026-06-01T00:00:00Z",
               [("exec", {"command": "rm -rf /tmp/x"})])
    row["data"] = json.dumps(row["data"])
    out = approvals.replay_policy(_RM_POLICY, [row])
    assert out["matches"] == 1


def test_replay_garbage_rows_never_crash():
    rows = [None, 42, "nope", {}, {"id": "x", "data": "{not json"},
            {"id": "y", "data": {"type": "message", "message": {"content": None}}}]
    out = approvals.replay_policy(_RM_POLICY, rows)
    assert out["ok"] is True
    assert out["matches"] == 0


# ── monitor (dry-run) mode ────────────────────────────────────────────────


class _StoreStub:
    def __init__(self):
        self.ingested: list[dict] = []

    def ingest_approval(self, approval: dict):
        self.ingested.append(approval)


@pytest.fixture()
def monitor_env(monkeypatch):
    """Patch the cloud round-trip + kill path to FAIL the test if reached,
    and capture local approval persists."""
    store = _StoreStub()
    monkeypatch.setattr(
        approvals, "_post_approval_request",
        lambda *a, **k: pytest.fail("monitor mode must not call the cloud"))
    monkeypatch.setattr(
        approvals, "_poll_decision",
        lambda *a, **k: pytest.fail("monitor mode must not poll for a decision"))
    monkeypatch.setattr(
        approvals, "_kill_session",
        lambda *a, **k: pytest.fail("monitor mode must never kill a session"))
    import clawmetry.local_store as _ls
    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: store)
    return store


def test_monitor_mode_never_blocks_and_records_simulated(monitor_env):
    policy = approvals._compile_policy({
        "name": "mon-rm",
        "match": {"tool": "exec", "command_regex": r"rm\s+-rf"},
        "action": "monitor",
    })
    assert policy is not None
    result = approvals.process_tool_call(
        api_key="test-key", node_id="node-1", session_id="claude_code:s1",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/scratch"}, policies=[policy])
    assert result["decision"] == "monitored"
    assert result["killed"] is False
    assert result["policy"] == "mon-rm"
    assert len(monitor_env.ingested) == 1
    row = monitor_env.ingested[0]
    assert row["status"] == "simulated"
    assert "rm -rf /tmp/scratch" in row["action"]
    assert "mon-rm" in (row.get("decision_reason") or "")


def test_monitor_mode_non_matching_tool_is_untouched(monitor_env):
    policy = approvals._compile_policy({
        "name": "mon-rm",
        "match": {"tool": "exec", "command_regex": r"rm\s+-rf"},
        "action": "monitor",
    })
    result = approvals.process_tool_call(
        api_key="test-key", node_id="node-1", session_id="s",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "ls -la"}, policies=[policy])
    assert result["decision"] == "no_policy"
    assert monitor_env.ingested == []


# ── POST /api/policy/replay route ─────────────────────────────────────────


@pytest.fixture()
def replay_client(monkeypatch):
    from flask import Flask
    import routes.policy as rp

    rows = [
        _row("e1", "claude_code:sess-1", "2026-06-01T00:00:00Z",
             [("Bash", {"command": "rm -rf build/"})], flavor="claude"),
        _row("e2", "s2", "2026-06-01T00:00:01Z",
             [("exec", {"command": "echo hi"})]),
    ]

    def _fake_ls_call(method_name, **kwargs):
        assert method_name == "query_events"
        assert "since" in kwargs and "limit" in kwargs
        return rows

    monkeypatch.setattr(rp, "_ls_call", _fake_ls_call)
    app = Flask(__name__)
    app.register_blueprint(rp.bp_policy)
    return app.test_client()


def test_replay_route_happy_path(replay_client):
    resp = replay_client.post("/api/policy/replay", json={
        "policy": {"name": "gate-rm",
                   "match": {"tool": "exec", "command_regex": r"rm\s+-rf"}},
        "days": 7,
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["matches"] == 1
    assert body["by_runtime"] == {"claude_code": 1}
    assert body["days"] == 7
    assert body["since"]


def test_replay_route_rejects_missing_policy(replay_client):
    resp = replay_client.post("/api/policy/replay", json={"days": 7})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_replay_route_rejects_bad_regex(replay_client):
    resp = replay_client.post("/api/policy/replay", json={
        "policy": {"name": "bad", "match": {"command_regex": "["}}})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_replay_route_clamps_days(replay_client):
    resp = replay_client.post("/api/policy/replay", json={
        "policy": {"name": "gate-rm",
                   "match": {"tool": "exec", "command_regex": r"rm\s+-rf"}},
        "days": 9999,
    })
    assert resp.status_code == 200
    assert resp.get_json()["days"] == 30
