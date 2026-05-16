"""Tier-1 DuckDB fast path for /api/skills fidelity counts.

The endpoint historically scanned every session JSONL touched in the
last 7 days on every request, looking for Read-tool calls whose target
was a SKILL.md or a file under a skill's scripts/references/assets dir.
With 50-200 active sessions this is the panel's slowest stage.

This test asserts:
  1. Unit — when the local DuckDB has Read-tool events targeting a
     skill's SKILL.md / scripts dir, ``query_recent_read_tool_calls``
     returns one row per call with the file_path payload.
  2. E2E — synthetic OpenClaw-shaped events round-trip:
        ingest -> DuckDB -> /api/skills -> body_fetch_count_7d /
        linked_file_read_count_7d
     Both v3 ``tool.call`` events and assistant ``message`` events
     with ``toolMetas`` are accepted.
  3. Fallback — empty store + empty workspace -> empty fidelity counts
     (no synthetic data, no crash).
"""

from __future__ import annotations

import importlib
import os
import time

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app with bp_skills registered, fresh DuckDB per test, plus
    one synthetic skill on disk so /api/skills has something to count
    against (the skill discovery itself is a cheap directory listing —
    not what this fast-path migration is about)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    # Lay down a skill on disk: .openclaw/skills/demo-skill/{SKILL.md,scripts/run.py}
    skills_root = tmp_path / "openclaw" / "skills"
    skill_dir = skills_root / "demo-skill"
    (skill_dir / "scripts").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: a demo skill\n---\nbody line\n"
    )
    (skill_dir / "scripts" / "run.py").write_text("print('hello')\n")
    # Backdate the SKILL.md mtime so age > 7d but < 30d ('unused' bucket
    # if no body fetches; but we want 'healthy' once we add fetches).
    old = time.time() - (10 * 86400)
    os.utime(skill_dir / "SKILL.md", (old, old))

    import dashboard as _d
    monkeypatch.setattr(_d, "WORKSPACE", str(tmp_path / "openclaw"), raising=False)
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "sessions_empty"), raising=False)

    import routes.skills as skills_mod
    importlib.reload(skills_mod)

    a = Flask(__name__)
    a.register_blueprint(skills_mod.bp_skills)
    yield a, ls, str(skill_dir)
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _ingest_tool_call(store, *, sid: str, ts: str, file_path: str,
                      ev_id: str | None = None, name: str = "Read"):
    """Insert one v3 top-level tool.call event."""
    if ev_id is None:
        ev_id = f"tc-{sid}-{ts}-{file_path}"
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "tool.call",
        "ts":         ts,
        "data":       {"name": name, "input": {"file_path": file_path}},
    })


def _ingest_assistant_with_toolmetas(store, *, sid: str, ts: str,
                                      file_path: str, name: str = "Read",
                                      ev_id: str | None = None):
    """Insert a trajectory-shape assistant message event whose
    ``data.toolMetas`` carries the Read invocation."""
    if ev_id is None:
        ev_id = f"msg-{sid}-{ts}-{file_path}"
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "message",
        "ts":         ts,
        "data":       {
            "type": "model.completed",
            "completionText": "reading the skill",
            "toolMetas": [{"name": name, "input": {"file_path": file_path}}],
        },
    })


# ── E2E: synthetic events round-trip through DuckDB → /api/skills ─────────


def test_skills_fast_path_counts_body_fetch_from_tool_call(app):
    """A v3 tool.call event targeting SKILL.md must increment
    body_fetch_count_7d for that skill on the next /api/skills hit."""
    a, ls, skill_dir = app
    store = ls.get_store()
    sm = os.path.join(skill_dir, "SKILL.md")
    _ingest_tool_call(store, sid="s1", ts="2026-05-15T10:00:00+00:00", file_path=sm)
    _ingest_tool_call(store, sid="s1", ts="2026-05-15T10:01:00+00:00", file_path=sm)
    _wait_flush(store)

    body = a.test_client().get("/api/skills").get_json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert "demo-skill" in by_name
    assert by_name["demo-skill"]["body_fetch_count_7d"] == 2
    assert by_name["demo-skill"]["linked_file_read_count_7d"] == 0
    assert by_name["demo-skill"]["status"] == "stuck" or \
           by_name["demo-skill"]["status"] == "healthy"


def test_skills_fast_path_counts_linked_file_from_assistant_msg(app):
    """An assistant message event projecting a Read on
    scripts/run.py via toolMetas must increment
    linked_file_read_count_7d for the skill."""
    a, ls, skill_dir = app
    store = ls.get_store()
    sm = os.path.join(skill_dir, "SKILL.md")
    run_py = os.path.join(skill_dir, "scripts", "run.py")
    _ingest_assistant_with_toolmetas(
        store, sid="s2", ts="2026-05-15T11:00:00+00:00", file_path=sm,
    )
    _ingest_assistant_with_toolmetas(
        store, sid="s2", ts="2026-05-15T11:01:00+00:00", file_path=run_py,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/skills").get_json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert by_name["demo-skill"]["body_fetch_count_7d"] == 1
    assert by_name["demo-skill"]["linked_file_read_count_7d"] == 1
    # Body+linked → healthy bucket
    assert by_name["demo-skill"]["status"] == "healthy"


def test_skills_fast_path_drops_non_read_tool_calls(app):
    """Tool calls for non-Read tools (e.g. Bash, Write) must not
    inflate either fidelity counter."""
    a, ls, skill_dir = app
    store = ls.get_store()
    sm = os.path.join(skill_dir, "SKILL.md")
    _ingest_tool_call(store, sid="s3", ts="2026-05-15T12:00:00+00:00",
                      file_path=sm, name="Bash")
    _ingest_tool_call(store, sid="s3", ts="2026-05-15T12:01:00+00:00",
                      file_path=sm, name="Write")
    _wait_flush(store)

    body = a.test_client().get("/api/skills").get_json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert by_name["demo-skill"]["body_fetch_count_7d"] == 0
    assert by_name["demo-skill"]["linked_file_read_count_7d"] == 0


def test_skills_fast_path_returns_empty_counts_when_store_empty(app):
    """No DuckDB rows + empty SESSIONS_DIR -> demo-skill present (it's
    on disk) but with zero fidelity counts. No exception."""
    a, _ls, _skill_dir = app
    body = a.test_client().get("/api/skills").get_json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert "demo-skill" in by_name
    assert by_name["demo-skill"]["body_fetch_count_7d"] == 0
    assert by_name["demo-skill"]["linked_file_read_count_7d"] == 0


# ── Unit: the LocalStore method itself ─────────────────────────────────────


def test_query_recent_read_tool_calls_returns_empty_on_empty(app):
    _a, ls, _sd = app
    store = ls.get_store()
    rows = store.query_recent_read_tool_calls(since="2026-05-01T00:00:00Z")
    assert rows == []


def test_query_recent_read_tool_calls_extracts_v3_tool_call(app):
    _a, ls, _sd = app
    store = ls.get_store()
    _ingest_tool_call(store, sid="sx", ts="2026-05-15T13:00:00+00:00",
                      file_path="/abs/path/SKILL.md")
    _wait_flush(store)
    rows = store.query_recent_read_tool_calls(since="2026-05-01T00:00:00Z")
    assert len(rows) == 1
    assert rows[0]["session_id"] == "sx"
    assert rows[0]["file_path"] == "/abs/path/SKILL.md"


def test_query_recent_read_tool_calls_extracts_legacy_content_block(app):
    """Older transcripts whose data.message.content still carries raw
    {type:'toolCall',name:'Read',...} blocks must be extracted too —
    closes the gap the legacy scanner depended on."""
    _a, ls, _sd = app
    store = ls.get_store()
    store.ingest({
        "id":         "leg-1",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "leg-sess",
        "event_type": "message",
        "ts":         "2026-05-15T14:00:00+00:00",
        "data":       {
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "toolCall", "name": "Read",
                     "input": {"file_path": "/legacy/SKILL.md"}},
                ],
            }
        },
    })
    _wait_flush(store)
    rows = store.query_recent_read_tool_calls(since="2026-05-01T00:00:00Z")
    assert len(rows) == 1
    assert rows[0]["file_path"] == "/legacy/SKILL.md"


def test_query_recent_read_tool_calls_respects_since(app):
    """Events older than ``since`` must be excluded — keeps the
    7d-window contract /api/skills depends on."""
    _a, ls, _sd = app
    store = ls.get_store()
    _ingest_tool_call(store, sid="old", ts="2026-04-01T00:00:00+00:00",
                      file_path="/x/SKILL.md")
    _ingest_tool_call(store, sid="new", ts="2026-05-15T15:00:00+00:00",
                      file_path="/x/SKILL.md")
    _wait_flush(store)
    rows = store.query_recent_read_tool_calls(since="2026-05-10T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["session_id"] == "new"


# ── v3 real-shape regression (issue #1385) ────────────────────────────────


def test_query_recent_read_tool_calls_v3_assistant_event(app):
    """v3 real-shape regression (#1385): real OpenClaw v3 emits the
    parent agent's tool-use blocks under ``event_type='assistant'``
    (not ``'message'``). The previous predicate matched
    ``message`` only, so v3 nodes silently returned zero Read calls
    and ``/api/skills`` body_fetch counts went to 0 across the
    fleet. Fixture distilled from a real
    ``data.message.content[*]`` block extracted from
    ``/Users/vivek/.clawmetry/clawmetry.duckdb`` on 2026-05-15."""
    _a, ls, _sd = app
    store = ls.get_store()
    store.ingest({
        "id":         "v3-asst-read-1",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "v3-real",
        "event_type": "assistant",
        "ts":         "2026-05-15T22:22:09.768Z",
        # Real v3 ``assistant`` event payload — content list with a
        # tool_use block (the same shape Anthropic's SDK echoes).
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "thinking", "thinking": "..."},
                    {
                        "type": "tool_use",
                        "id":   "toolu_01abc",
                        "name": "Read",
                        "input": {"file_path": "/abs/SKILL.md"},
                    },
                ],
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    rows = store.query_recent_read_tool_calls(since="2026-05-01T00:00:00Z")
    assert len(rows) == 1, f"v3 assistant tool_use ignored; rows={rows}"
    assert rows[0]["file_path"] == "/abs/SKILL.md"
    assert rows[0]["session_id"] == "v3-real"


def test_query_recent_read_tool_calls_v3_subagent_assistant_event(app):
    """v3 real-shape regression (#1385): subagents call Read too
    (Task → haiku worker scanning files). The widened predicate
    must include ``subagent:assistant`` so /api/skills credits
    reads done by subagents (which is the majority of skill-content
    fetches in real-world OpenClaw sessions)."""
    _a, ls, _sd = app
    store = ls.get_store()
    store.ingest({
        "id":         "v3-sub-read-1",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "v3-real",
        "event_type": "subagent:assistant",
        "ts":         "2026-05-15T22:23:00.000Z",
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-haiku-4-5",
                "content": [
                    {
                        "type": "tool_use",
                        "id":   "toolu_subagent",
                        "name": "Read",
                        "input": {"file_path": "/abs/scripts/run.py"},
                    },
                ],
            },
        },
        "model": "claude-haiku-4-5",
    })
    _wait_flush(store)

    rows = store.query_recent_read_tool_calls(since="2026-05-01T00:00:00Z")
    assert len(rows) == 1, f"v3 subagent:assistant ignored; rows={rows}"
    assert rows[0]["file_path"] == "/abs/scripts/run.py"


def test_query_tool_call_invocations_v3_assistant_event(app):
    """v3 real-shape regression (#1385): /api/plugins fast-path
    (``query_tool_call_invocations``) also filtered on
    ``event_type='message'`` — same bug, same fix. After the
    widening, every tool_use block in a v3 ``assistant`` event must
    contribute one row to the per-plugin invocation counter."""
    _a, ls, _sd = app
    store = ls.get_store()
    store.ingest({
        "id":         "v3-asst-multitool",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "v3-real-2",
        "event_type": "assistant",
        "ts":         "2026-05-15T22:30:00.000Z",
        # Real v3 shape — assistant content list with three tool_use
        # blocks (verbatim names observed on this box: Bash, Write,
        # Glob, WebSearch, Read, etc.).
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "tool_use", "name": "Bash",
                     "input": {"command": "ls"}},
                    {"type": "tool_use", "name": "Write",
                     "input": {"file_path": "/x", "content": "y"}},
                    {"type": "tool_use", "name": "Read",
                     "input": {"file_path": "/x"}},
                ],
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    rows = store.query_tool_call_invocations(since="2026-05-01T00:00:00Z")
    names = sorted(r["name"] for r in rows)
    assert names == ["Bash", "Read", "Write"], (
        f"v3 assistant tool_use names lost; rows={rows}"
    )


# ── Daemon-call mocking: route hits the proxy, not direct open ─────────────


def test_skills_route_uses_daemon_proxy_when_available(app, monkeypatch):
    """When ``local_store_via_daemon`` returns a populated row list, the
    route must use it (and NOT fall through to direct open / JSONL)."""
    a, _ls, skill_dir = app
    sm = os.path.join(skill_dir, "SKILL.md")
    canned = [
        {"ts": "2026-05-15T16:00:00+00:00", "session_id": "proxy-1", "file_path": sm},
        {"ts": "2026-05-15T16:01:00+00:00", "session_id": "proxy-1", "file_path": sm},
    ]
    calls = {"n": 0}

    def fake_proxy(method_name, **kwargs):
        calls["n"] += 1
        assert method_name == "query_recent_read_tool_calls"
        return canned

    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", fake_proxy)

    body = a.test_client().get("/api/skills").get_json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert calls["n"] == 1, "route did not call the daemon proxy"
    assert by_name["demo-skill"]["body_fetch_count_7d"] == 2
