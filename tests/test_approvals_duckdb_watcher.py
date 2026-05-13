"""Tests for the DuckDB-backed approvals watcher (PRD #779 PR-E).

Pre-2026-05-13, ``clawmetry/approvals.py:watch_iteration`` tail-globbed
``~/.openclaw/agents/main/sessions/*.jsonl``. That worked only for OpenClaw
— Hermes / Codex / Claude Code adapters had no path to the policy engine.
The watcher now reads ``local_store.query_events()`` directly, which every
adapter feeds.

These tests exercise the new watcher against an isolated DuckDB and a
stubbed ``process_tool_call`` so we don't need a real cloud round-trip.

What's covered:

  1. Happy path — ingest 3 fake events with toolCall blocks → run watcher
     → assert process_tool_call called 3 times with the right payload.
  2. Dedup / watermark — running the watcher twice in a row must not
     re-fire on already-seen events.
  3. Mixed event types — only assistant-with-toolCall events trigger the
     watcher; plain text messages are ignored.
  4. Non-OpenClaw adapter — an event tagged ``agent_type='hermes'`` still
     fires (proves the unified-store contract).
  5. State persistence — write the watermark, simulate a daemon restart
     (reload module, reset _state), assert no double-processing.

The fixture pattern mirrors ``tests/test_approvals_local_store.py`` —
isolated per-test DuckDB under ``tmp_path`` via the
``CLAWMETRY_LOCAL_STORE_PATH`` env var.
"""

from __future__ import annotations

import importlib
import os
import sys
import time

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── helpers ───────────────────────────────────────────────────────────────


def _ts(seconds_offset: float = 0.0) -> str:
    """Deterministic ISO-8601 ts so test data is sortable + stable across
    test runs. Lexicographic == chronological for this format."""
    base = 1_700_000_000  # 2023-11-14T22:13:20Z; long before any real ingest
    t = base + seconds_offset
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def _msg_event(eid: str, sid: str, ts: str, *,
               agent_type: str = "openclaw",
               role: str = "assistant",
               content: list | None = None) -> dict:
    """Build a row in the shape ``sync._local_ingest_session_batch`` would
    write for an OpenClaw / Anthropic-style transcript event."""
    return {
        "id": eid,
        "agent_type": agent_type,
        "node_id": "node-test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "message",
        "ts": ts,
        "data": {
            "type": "message",
            "timestamp": ts,
            "message": {
                "role": role,
                "content": content or [],
            },
        },
    }


def _toolcall_block(name: str, args: dict, *, blk_id: str = "tc-1",
                    style: str = "openclaw") -> dict:
    """Both flavours of tool-invocation block. ``openclaw`` uses
    ``toolCall`` + ``arguments``; ``anthropic`` uses ``tool_use`` + ``input``.
    Both must be detected by the watcher."""
    if style == "anthropic":
        return {"type": "tool_use", "id": blk_id, "name": name, "input": args}
    return {"type": "toolCall", "id": blk_id, "name": name, "arguments": args}


# ── fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def watcher(tmp_path, monkeypatch):
    """Reload local_store + approvals against an isolated DuckDB and a
    sync-state.json under tmp_path. Captures every process_tool_call
    invocation for assertion."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    # Reload local_store FIRST so its module-level path constants pick up
    # the env vars, then reload approvals so its lazy ``from clawmetry
    # import local_store`` resolves to the freshly-loaded module.
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.approvals as ap
    importlib.reload(ap)

    # Redirect the watermark file into the per-test tmp dir so we don't
    # touch the developer's real ~/.clawmetry/sync-state.json.
    state_path = tmp_path / "sync-state.json"
    monkeypatch.setattr(ap, "_STATE_PATH", state_path)
    # Force the in-memory watermark mirror to re-prime from disk.
    ap._state["last_check_ts"] = None
    ap._state["seen_ids_at_boundary"] = set()

    # Capture every process_tool_call invocation. Replace it on the module
    # and turn off the threading.Thread spawn so assertions are
    # deterministic (real watcher fires-and-forgets in a daemon thread).
    captured: list[dict] = []

    def _fake_process(api_key, node_id, session_id, tool_call_id,
                      tool_name, args, policies):
        captured.append({
            "api_key": api_key,
            "node_id": node_id,
            "session_id": session_id,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "args": args,
            "policies": policies,
        })

    monkeypatch.setattr(ap, "process_tool_call", _fake_process)

    class _SyncThread:
        """Drop-in for threading.Thread that runs synchronously on .start().
        Lets the test assert process_tool_call was invoked without sleeping
        for the daemon thread to schedule. We can't monkey-patch
        ``threading.Thread`` globally — local_store's flusher uses it too
        with kwargs (``name=``) that this stub doesn't accept. Instead we
        replace the *module-bound* reference inside ``approvals``."""
        def __init__(self, target=None, args=(), kwargs=None, daemon=False, **_kw):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}
        def start(self):
            if self._target is not None:
                self._target(*self._args, **self._kwargs)

    # Bind the stub on a shim threading module so only ``ap.threading.Thread``
    # is replaced, not the real module that local_store also imports.
    import types as _types
    _shim = _types.SimpleNamespace(Thread=_SyncThread, Event=ap.threading.Event)
    monkeypatch.setattr(ap, "threading", _shim)

    # A fixed policy that matches every tool call. The watcher only spawns
    # process_tool_call when at least one policy is loaded; the fake above
    # ignores the policy match, so any non-empty list works.
    policies = [{
        "name": "match-all",
        "tool": "",
        "command_regex": None,
        "command_not_regex": None,
        "args_regex": None,
        "action": "require_approval",
        "timeout": 60,
        "on_timeout": "deny",
    }]

    yield ap, ls, captured, policies, state_path

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. happy path ─────────────────────────────────────────────────────────


def test_watcher_dispatches_three_toolcalls(watcher):
    """Three assistant events, each with one toolCall block → three
    process_tool_call invocations with the expected payload shape."""
    ap, ls, captured, policies, _ = watcher
    store = ls.get_store()

    # Anchor watermark to "before the test events" so they're all visible.
    ap._state["last_check_ts"] = _ts(-10)

    for i in range(3):
        store.ingest(_msg_event(
            eid=f"ev-{i}",
            sid=f"sess-{i}",
            ts=_ts(i),
            content=[_toolcall_block(
                name=f"bash_{i}",
                args={"cmd": f"echo {i}"},
                blk_id=f"tc-{i}",
            )],
        ))
    store._flush_now()

    n = ap.watch_iteration("api-key-test", "node-test", policies=policies)
    assert n == 3
    assert len(captured) == 3

    # Most-recent-first ordering from query_events; sort by tool_call_id
    # for stable assertions.
    by_id = {c["tool_call_id"]: c for c in captured}
    assert set(by_id) == {"tc-0", "tc-1", "tc-2"}
    assert by_id["tc-0"]["session_id"] == "sess-0"
    assert by_id["tc-0"]["tool_name"] == "bash_0"
    assert by_id["tc-0"]["args"] == {"cmd": "echo 0"}
    assert by_id["tc-2"]["tool_name"] == "bash_2"


# ── 2. dedup / watermark advances ─────────────────────────────────────────


def test_watcher_does_not_redispatch_on_second_pass(watcher):
    """One event → first watch_iteration fires once → second pass sees
    nothing new (watermark advanced past the row's ts)."""
    ap, ls, captured, policies, _ = watcher
    store = ls.get_store()
    ap._state["last_check_ts"] = _ts(-10)

    store.ingest(_msg_event(
        eid="ev-once", sid="sess-once", ts=_ts(0),
        content=[_toolcall_block("rm", {"cmd": "rm -rf /tmp/x"}, blk_id="tc-once")],
    ))
    store._flush_now()

    first = ap.watch_iteration("k", "n", policies=policies)
    assert first == 1
    assert len(captured) == 1

    # Second pass — no new ingest, watermark has moved past the row.
    second = ap.watch_iteration("k", "n", policies=policies)
    assert second == 0
    assert len(captured) == 1, "process_tool_call must not be re-invoked"


# ── 3. mixed event types ──────────────────────────────────────────────────


def test_watcher_skips_messages_without_toolcall(watcher):
    """A plain assistant text message must not fire process_tool_call;
    only the message that carries a toolCall block does."""
    ap, ls, captured, policies, _ = watcher
    store = ls.get_store()
    ap._state["last_check_ts"] = _ts(-10)

    # No-toolCall: just a text block.
    store.ingest(_msg_event(
        eid="ev-text", sid="sess-A", ts=_ts(0),
        content=[{"type": "text", "text": "thinking out loud"}],
    ))
    # With a toolCall.
    store.ingest(_msg_event(
        eid="ev-tool", sid="sess-A", ts=_ts(1),
        content=[_toolcall_block("bash", {"cmd": "ls"}, blk_id="tc-yes")],
    ))
    store._flush_now()

    n = ap.watch_iteration("k", "n", policies=policies)
    assert n == 1
    assert len(captured) == 1
    assert captured[0]["tool_call_id"] == "tc-yes"


# ── 4. non-OpenClaw adapter (Hermes) ──────────────────────────────────────


def test_watcher_processes_non_openclaw_adapter(watcher):
    """Same toolCall but stored under agent_type='hermes' (Anthropic-style
    ``tool_use`` block, ``input`` instead of ``arguments``). Proves the
    PRD acceptance: the watcher is adapter-agnostic now."""
    ap, ls, captured, policies, _ = watcher
    store = ls.get_store()
    ap._state["last_check_ts"] = _ts(-10)

    store.ingest(_msg_event(
        eid="ev-hermes", sid="sess-hermes", ts=_ts(0),
        agent_type="hermes",
        content=[_toolcall_block(
            "bash", {"command": "uname -a"},
            blk_id="tc-hermes",
            style="anthropic",
        )],
    ))
    store._flush_now()

    n = ap.watch_iteration("k", "n", policies=policies)
    assert n == 1
    assert len(captured) == 1
    assert captured[0]["session_id"] == "sess-hermes"
    assert captured[0]["tool_name"] == "bash"
    # ``input`` was promoted to ``args`` regardless of the wire-format key.
    assert captured[0]["args"] == {"command": "uname -a"}


# ── 5. state persistence across daemon restart ────────────────────────────


def test_watermark_survives_daemon_restart(watcher, monkeypatch):
    """First watcher run advances the watermark on disk; resetting the
    in-memory mirror (simulating a daemon restart) must reload from disk
    and skip the already-processed event — no double-fire."""
    ap, ls, captured, policies, state_path = watcher
    store = ls.get_store()
    ap._state["last_check_ts"] = _ts(-10)

    store.ingest(_msg_event(
        eid="ev-pre-restart", sid="sess-X", ts=_ts(0),
        content=[_toolcall_block("bash", {"cmd": "true"}, blk_id="tc-pre")],
    ))
    store._flush_now()

    n1 = ap.watch_iteration("k", "n", policies=policies)
    assert n1 == 1
    assert state_path.exists(), "watermark must be persisted after first iteration"

    # Simulate a daemon restart: clear the in-memory mirror, leave the
    # store + on-disk watermark intact. The next iteration must reload the
    # watermark from disk and NOT re-fire on the same event.
    captured.clear()
    ap._state["last_check_ts"] = None
    ap._state["seen_ids_at_boundary"] = set()

    n2 = ap.watch_iteration("k", "n", policies=policies)
    assert n2 == 0, "post-restart pass must not redispatch the already-seen event"
    assert captured == []

    # In-memory watermark must now match what we persisted.
    import json as _j
    with state_path.open() as fh:
        blob = _j.load(fh)
    assert blob.get(ap._STATE_KEY) is not None
    assert ap._state["last_check_ts"] == blob[ap._STATE_KEY]
