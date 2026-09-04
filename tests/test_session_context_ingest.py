"""Inputs & context ingest: ``context.compiled`` -> ``session_context`` rows.

Feeds OpenClaw's trajectory-recorder event shape (verified against the
openclaw dist: ``{traceSchema, type, ts, seq, sessionId, workspaceDir,
provider, modelId, data:{systemPrompt, prompt, messages, tools[], imagesCount,
streamStrategy, transport}}``) through ``LocalStore.ingest`` into a TEMP
DuckDB and asserts: rows per kind, redaction, the 64 KB cap (sha/size still
describe the full text), sha dedupe with ``turns`` increment, the family
adapter nesting (``data.extra``), the raw event's ``messages`` being replaced
by a count, and the trajectory sidecar reader in ``sync.py``.

Temp store only: never touches ~/.clawmetry.
"""
from __future__ import annotations

import hashlib
import importlib
import json

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ctx.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.get_store()
    yield st
    try:
        st.stop(flush=True)
    except Exception:
        pass


SECRET = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef"
TOOLS = [
    {"name": "read", "description": "Read a file", "parameters": {"type": "object"}},
    {"name": "bash", "description": "Run a shell command", "parameters": {"type": "object"}},
    {"name": "write", "description": "Write a file", "parameters": {"type": "object"}},
]


def _trajectory_event(sid="11111111-2222-3333-4444-555555555555", *, seq=1,
                      system_prompt="You are a helpful agent.", prompt="fix the bug",
                      tools=TOOLS, ts="2026-09-04T10:00:00.000Z"):
    line = {
        "traceSchema": "openclaw-trajectory", "schemaVersion": 1,
        "traceId": sid, "source": "runtime", "type": "context.compiled",
        "ts": ts, "seq": seq, "sourceSeq": seq, "sessionId": sid,
        "sessionKey": "agent:main:main", "runId": "run-1",
        "workspaceDir": "/Users/dev/proj", "provider": "anthropic",
        "modelId": "claude-sonnet-4-5", "modelApi": "anthropic-messages",
        "data": {
            "systemPrompt": system_prompt, "prompt": prompt,
            "messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
            "tools": tools, "imagesCount": 0, "streamStrategy": "auto",
            "transport": "sdk", "transcriptLeafId": "leaf-1",
        },
    }
    return {
        "id": f"{sid}:ctx:{seq}", "agent_type": "openclaw", "node_id": "node-test",
        "agent_id": "main", "session_id": sid, "event_type": "context.compiled",
        "ts": ts, "data": line, "model": "claude-sonnet-4-5",
    }


def _by_kind(rows):
    out = {}
    for r in rows:
        out.setdefault(r["kind"], []).append(r)
    return out


def test_rows_per_kind_with_measured_sha_and_size(store):
    sp = "You are a helpful agent. api_key = " + SECRET + " never share it."
    store.ingest(_trajectory_event(system_prompt=sp))
    store._flush_now()
    rows = store.query_session_context(session_id="11111111-2222-3333-4444-555555555555")
    k = _by_kind(rows)
    assert set(k) == {"system_prompt", "user_prompt", "tools_available", "runtime_meta"}

    spr = k["system_prompt"][0]
    assert spr["sha256"] == hashlib.sha256(sp.encode()).hexdigest()
    assert spr["size_bytes"] == len(sp.encode())
    assert spr["turns"] == 1
    # Redacted before it rests in DuckDB; the fingerprint is stable.
    assert SECRET not in spr["content"]
    assert "[REDACTED:" in spr["content"]
    assert spr["content_truncated"] is False

    up = k["user_prompt"][0]
    assert up["content"] == "fix the bug"

    tools = k["tools_available"][0]
    assert json.loads(tools["summary"]) == ["bash", "read", "write"]
    # Definitions JSON is fingerprinted but not returned as content.
    assert tools["content"] is None
    assert tools["size_bytes"] > 0

    meta = json.loads(k["runtime_meta"][0]["summary"])
    assert meta["transport"] == "sdk"
    assert meta["streamStrategy"] == "auto"
    assert meta["messages_count"] == 2
    assert meta["tools_count"] == 3
    assert meta["model"] == "claude-sonnet-4-5"
    assert meta["provider"] == "anthropic"
    assert meta["cwd"] == "/Users/dev/proj"


def test_cap_keeps_full_sha_and_size(store):
    from clawmetry.session_context import CONTENT_CAP
    big = "x" * (CONTENT_CAP + 5000)
    store.ingest(_trajectory_event(system_prompt=big))
    store._flush_now()
    rows = store.query_session_context(session_id="11111111-2222-3333-4444-555555555555")
    spr = _by_kind(rows)["system_prompt"][0]
    assert spr["size_bytes"] == CONTENT_CAP + 5000
    assert spr["sha256"] == hashlib.sha256(big.encode()).hexdigest()
    assert len(spr["content"].encode()) <= CONTENT_CAP
    assert spr["content_truncated"] is True


def test_same_sha_bumps_turns_not_rows(store):
    sid = "11111111-2222-3333-4444-555555555555"
    store.ingest(_trajectory_event(sid, seq=1, ts="2026-09-04T10:00:00Z"))
    store.ingest(_trajectory_event(sid, seq=2, ts="2026-09-04T10:05:00Z"))
    store.ingest(_trajectory_event(sid, seq=3, ts="2026-09-04T10:09:00Z", prompt="now add tests"))
    store._flush_now()
    rows = store.query_session_context(session_id=sid)
    k = _by_kind(rows)
    assert len(k["system_prompt"]) == 1
    assert k["system_prompt"][0]["turns"] == 3
    assert k["system_prompt"][0]["first_ts"] == "2026-09-04T10:00:00Z"
    assert k["system_prompt"][0]["last_ts"] == "2026-09-04T10:09:00Z"
    assert len(k["tools_available"]) == 1 and k["tools_available"][0]["turns"] == 3
    # A different user prompt is a different fact: two rows.
    assert sorted(r["content"] for r in k["user_prompt"]) == ["fix the bug", "now add tests"]
    # Raw events are all kept (one per turn).
    evs = store.query_events(session_id=sid, event_type="context.compiled", limit=50)
    assert len(evs) == 3


def test_raw_event_is_compacted_not_dropped(store):
    sid = "11111111-2222-3333-4444-555555555555"
    store.ingest(_trajectory_event(sid))
    store._flush_now()
    evs = store.query_events(session_id=sid, event_type="context.compiled", limit=5)
    assert len(evs) == 1
    data = evs[0]["data"]
    if isinstance(data, str):
        data = json.loads(data)
    inner = data["data"]
    assert "messages" not in inner
    assert inner["messagesCount"] == 2
    assert inner["systemPrompt"] == "You are a helpful agent."
    assert data["workspaceDir"] == "/Users/dev/proj"


def test_family_adapter_shape_via_extra(store):
    """A paid adapter emits Event(type='context.compiled', extra={...}); the
    daemon wraps it as data={role, content, _runtime, extra}. Same rows."""
    sid = "claude_code:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    # NO agent_type key: the family ingest in sync.py does not set one, and a
    # test that supplied it hid the bug that made this panel read empty.
    store.ingest({
        "id": "claude_code:ctx-1", "node_id": "n",
        "agent_id": "main", "session_id": sid, "event_type": "context.compiled",
        "ts": "2026-09-04T11:00:00Z", "model": "claude-opus-4-1",
        "data": {"role": "", "content": "", "_runtime": "claude_code", "extra": {
            "prompt": "refactor the parser",
            "tools": ["Bash", "Read", "Edit"],
            "runtimeMeta": {
                "cwd": "/Users/dev/proj", "version": "2.1.150",
                "permissionMode": "default",
                "mcpServers": [{"name": "github"}, {"name": "linear"}],
                "contextFiles": [{"path": "/Users/dev/proj/CLAUDE.md", "size_bytes": 4321}],
            },
        }},
    })
    store._flush_now()
    rows = store.query_session_context(session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    k = _by_kind(rows)
    assert "system_prompt" not in k          # never invented
    assert json.loads(k["tools_available"][0]["summary"]) == ["Bash", "Edit", "Read"]
    assert json.loads(k["mcp_servers"][0]["summary"]) == ["github", "linear"]
    assert k["context_file"][0]["summary"] == "/Users/dev/proj/CLAUDE.md"
    assert k["context_file"][0]["size_bytes"] == 4321
    meta = json.loads(k["runtime_meta"][0]["summary"])
    assert meta["version"] == "2.1.150"
    assert meta["permissionMode"] == "default"
    assert meta["cwd"] == "/Users/dev/proj"
    assert meta["model"] == "claude-opus-4-1"
    assert "mcpServers" not in meta and "contextFiles" not in meta
    # Bare-id lookup matched the prefixed row; the filter narrows by runtime.
    assert store.query_session_context(session_id=sid, agent_type="codex") == []
    # The row is labelled with the runtime that produced it, which is what the
    # Inputs panel asks for (?runtime=claude_code). Labelled "openclaw" the
    # panel filters its own data out and says "Nothing captured".
    assert {r["agent_type"] for r in rows} == {"claude_code"}
    assert len(store.query_session_context(session_id=sid, agent_type="claude_code")) == len(rows)


def test_family_raw_event_is_compacted_too(store):
    from clawmetry.session_context import CONTENT_CAP
    sid = "codex:bbbbbbbb-bbbb-cccc-dddd-eeeeeeeeeeee"
    store.ingest({
        "id": "codex:ctx-1", "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "context.compiled", "ts": "2026-09-04T11:00:00Z",
        "data": {"role": "", "content": "", "extra": {"systemPrompt": "y" * (CONTENT_CAP + 10),
                                                        "messages": [1, 2, 3]}},
    })
    store._flush_now()
    ev = store.query_events(session_id=sid, event_type="context.compiled", limit=5)[0]
    data = ev["data"] if isinstance(ev["data"], dict) else json.loads(ev["data"])
    assert "messages" not in data["extra"] and data["extra"]["messagesCount"] == 3
    assert data["extra"]["systemPromptTruncated"] is True
    assert len(data["extra"]["systemPrompt"]) <= CONTENT_CAP
    spr = _by_kind(store.query_session_context(session_id=sid))["system_prompt"][0]
    assert spr["size_bytes"] == CONTENT_CAP + 10


def test_non_context_events_produce_no_rows(store):
    store.ingest({
        "id": "e1", "agent_type": "openclaw", "node_id": "n", "agent_id": "main",
        "session_id": "s1", "event_type": "prompt.submitted",
        "ts": "2026-09-04T11:00:00Z", "data": {"systemPrompt": "not a context event"},
    })
    store.ingest({
        "id": "e2", "agent_type": "openclaw", "node_id": "n", "agent_id": "main",
        "session_id": "s1", "event_type": "context.compiled",
        "ts": "2026-09-04T11:00:00Z", "data": {"note": "no known fields"},
    })
    store._flush_now()
    assert store.query_session_context(session_id="s1") == []


def test_pure_helper_never_raises():
    from clawmetry import session_context as sc
    assert sc.rows_from_event({}) == []
    assert sc.rows_from_event({"event_type": "context.compiled"}) == []
    assert sc.rows_from_event({"event_type": "context.compiled", "session_id": "s", "data": "not json"}) == []
    assert sc.compact_raw_event_data("plain") == "plain"


def test_trajectory_sidecar_reader(store, tmp_path):
    """sync._sync_trajectory_context reads ONLY context.compiled lines out of
    <sid>.trajectory.jsonl, keys them on the sidecar's sessionId, keeps a line
    cursor, and never mints a '<uuid>.trajectory' phantom session."""
    from clawmetry import sync as _sync
    sid = "99999999-2222-3333-4444-555555555555"
    sdir = tmp_path / "sessions"
    sdir.mkdir()
    (sdir / f"{sid}.jsonl").write_text('{"type":"session","version":3,"id":"%s"}\n' % sid)
    ev = _trajectory_event(sid)["data"]
    other = dict(ev, type="prompt.submitted", seq=2, data={"prompt": "x"})
    sidecar = sdir / f"{sid}.trajectory.jsonl"
    sidecar.write_text(json.dumps(ev) + "\n" + json.dumps(other) + "\n" + "not json\n")
    state: dict = {}
    n = _sync._sync_trajectory_context(str(sdir), state, "node-test")
    assert n == 1
    assert state["trajectory_ctx_cursor"][f"{sid}.trajectory.jsonl"] == 3
    store._flush_now()
    rows = store.query_session_context(session_id=sid)
    assert {r["kind"] for r in rows} == {"system_prompt", "user_prompt", "tools_available", "runtime_meta"}
    evs = store.query_events(session_id=sid, limit=10)
    assert [e["event_type"] for e in evs] == ["context.compiled"]
    assert store.query_events(session_id=f"{sid}.trajectory", limit=10) == []
    # Second pass: cursor holds, nothing re-read.
    assert _sync._sync_trajectory_context(str(sdir), state, "node-test") == 0
    # Appended turn is picked up and dedupes onto the same sha.
    with open(sidecar, "a") as fh:
        fh.write(json.dumps(dict(ev, seq=3, ts="2026-09-04T10:20:00.000Z")) + "\n")
    assert _sync._sync_trajectory_context(str(sdir), state, "node-test") == 1
    store._flush_now()
    spr = _by_kind(store.query_session_context(session_id=sid))["system_prompt"][0]
    assert spr["turns"] == 2


def test_missing_sessions_dir_is_quiet(store, tmp_path):
    from clawmetry import sync as _sync
    assert _sync._sync_trajectory_context(str(tmp_path / "nope"), {}, "n") == 0


# ── Runtime label on the row (the "empty panel" bug, 2026-09-04) ───────────

def test_runtime_of_event_prefers_declared_then_stamped_then_prefix(monkeypatch):
    from clawmetry import session_context as sc
    # 1. The trajectory reader declares agent_type outright.
    assert sc.runtime_of_event({"agent_type": "openclaw", "session_id": "s1"}) == "openclaw"
    # 2. The family ingest declares nothing and stamps data._runtime.
    assert sc.runtime_of_event({
        "session_id": "claude_code:abc",
        "data": {"role": "", "content": "", "_runtime": "claude_code", "extra": {}},
    }) == "claude_code"
    # 3. Neither: the session-id prefix, through the one shared resolver.
    monkeypatch.setattr(
        "clawmetry.waste_flags.runtime_from_session_id",
        lambda sid: str(sid).split(":", 1)[0],
    )
    assert sc.runtime_of_event({"session_id": "cursor:abc", "data": {}}) == "cursor"
    # 4. Nothing to go on: the only Free runtime, never a guess.
    assert sc.runtime_of_event({"session_id": "plain-uuid", "data": {}}) == "openclaw"


def test_family_rows_are_findable_under_their_own_runtime(store):
    """The regression this file exists to hold: the Inputs panel asks for
    ``?runtime=claude_code``; rows stamped ``openclaw`` filter themselves out
    and the panel reports "Nothing captured for this session yet"."""
    sid = "claude_code:11111111-aaaa-bbbb-cccc-222222222222"
    store.ingest({
        "id": "claude_code:ctx-live", "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "context.compiled",
        "ts": "2026-09-04T12:00:00Z",
        "data": {"role": "", "content": "", "_runtime": "claude_code",
                 "extra": {"prompt": "why is the panel empty?",
                           "tools": ["Bash"],
                           "runtimeMeta": {"cwd": "/Users/dev/proj"}}},
    })
    store._flush_now()
    scoped = store.query_session_context(session_id=sid, agent_type="claude_code")
    assert {r["kind"] for r in scoped} == {"user_prompt", "tools_available", "runtime_meta"}
    assert store.query_session_context(session_id=sid, agent_type="openclaw") == []


def test_reingesting_the_same_event_does_not_invent_turns(store):
    """The family ingest re-reads a whole session every time it grows. The
    same context event arriving again is the same occurrence, not a turn."""
    sid = "claude_code:33333333-aaaa-bbbb-cccc-444444444444"
    event = {
        "id": "claude_code:ctx-dup", "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "context.compiled",
        "ts": "2026-09-04T12:00:00Z",
        "data": {"role": "", "content": "", "_runtime": "claude_code",
                 "extra": {"prompt": "one request", "tools": ["Bash"]}},
    }
    for _ in range(4):
        store.ingest(dict(event))
    store._flush_now()
    rows = _by_kind(store.query_session_context(session_id=sid))
    assert rows["user_prompt"][0]["turns"] == 1
    # A genuinely later occurrence of the same fact still counts.
    store.ingest(dict(event, id="claude_code:ctx-dup-2", ts="2026-09-04T12:30:00Z"))
    store._flush_now()
    rows = _by_kind(store.query_session_context(session_id=sid))
    assert rows["user_prompt"][0]["turns"] == 2
    assert rows["user_prompt"][0]["last_ts"] == "2026-09-04T12:30:00Z"


def test_migration_relabels_rows_written_under_the_old_code(store):
    """Stores written before the fix hold family rows stamped ``openclaw``.
    Reopening relabels them from the session-id prefix, so the panel finds
    history it already had rather than only sessions ingested since."""
    store._conn.execute("""
        INSERT INTO session_context (agent_type, session_id, node_id, kind,
            sha256, size_bytes, content, summary, first_ts, last_ts, turns,
            source, created_at)
        VALUES ('openclaw', 'codex:55555555-aaaa-bbbb-cccc-666666666666', 'n',
                'user_prompt', 'deadbeef', 11, NULL, '{"chars":11}',
                '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z', 1,
                'context.compiled', 0)
    """)
    import clawmetry.local_store as ls
    ls._apply_migrations(store._conn)
    rows = store.query_session_context(
        session_id="codex:55555555-aaaa-bbbb-cccc-666666666666",
        agent_type="codex",
    )
    assert len(rows) == 1 and rows[0]["agent_type"] == "codex"
    # Idempotent, and an unprefixed OpenClaw row is never touched.
    ls._apply_migrations(store._conn)
    assert len(store.query_session_context(
        session_id="codex:55555555-aaaa-bbbb-cccc-666666666666")) == 1


def test_migration_drops_the_stale_copy_instead_of_colliding(store):
    """A session ingested both before and after the fix has the same fact
    under two labels. The correctly-labelled row survives; the relabel must
    not trip the primary key."""
    for atype in ("openclaw", "cursor"):
        store._conn.execute(f"""
            INSERT INTO session_context (agent_type, session_id, node_id, kind,
                sha256, size_bytes, content, summary, first_ts, last_ts, turns,
                source, created_at)
            VALUES ('{atype}', 'cursor:77777777-aaaa-bbbb-cccc-888888888888',
                    'n', 'user_prompt', 'cafebabe', 7, NULL, '{{"chars":7}}',
                    '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z', 1,
                    'context.compiled', 0)
        """)
    import clawmetry.local_store as ls
    ls._apply_migrations(store._conn)
    rows = store.query_session_context(
        session_id="cursor:77777777-aaaa-bbbb-cccc-888888888888")
    assert len(rows) == 1 and rows[0]["agent_type"] == "cursor"
