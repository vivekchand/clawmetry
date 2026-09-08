"""Orchestration capture — NemoClaw leg.

A NemoClaw sandbox hosts a full OpenClaw workspace, so a sandboxed agent
that delegates writes the same ``agent:main:subagent:<uuid>`` entries into
the sandbox's ``sessions.json`` that host OpenClaw writes. The sync daemon
now reads that index per sandbox (``_parse_openclaw_subagent_index`` +
``_ingest_sandbox_subagent_rows``) and ``NemoClawAdapter.list_sessions``
joins the resulting ``subagents`` rows back into child Sessions.

Index-entry shapes in these tests mirror a REAL entry captured live on
2026-08-20 from a 2026.8 OpenClaw ``sessions.json`` (a ``sessions_spawn``
run that failed after 55 ms): fields ``spawnDepth / subagentRole /
sessionId / sessionFile / spawnedBy / label / status / startedAt / endedAt /
updatedAt / runtimeMs`` — and NO ``task`` / ``model`` / ``totalTokens`` on
that failed spawn. Transcript lines use the real v3 ``message`` envelope
(role user = content string; role assistant = content parts list + usage),
as captured from ``~/.openclaw/agents/main/sessions/*.jsonl``.
"""
from __future__ import annotations

import importlib
import json
import time
import uuid

import pytest

MAIN_UUID = "74bc4ddb-a09f-4a9d-93c2-904ea7708938"
CHILD_SA_UUID = "d38a6bbd-c530-4119-ac84-ae1e3b91c775"
CHILD_FILE_UUID = "55d5d1e2-fdb4-48de-9a67-c98254038e95"


def _real_index(*, now_ms: int | None = None, child_status: str = "failed",
                ended: bool = True, task: str = "") -> dict:
    """sessions.json index with the REAL captured field set."""
    now_ms = now_ms or int(time.time() * 1000)
    child: dict = {
        "spawnDepth": 1,
        "subagentRole": "leaf",
        "subagentControlScope": "none",
        "thinkingLevel": "high",
        "sessionId": CHILD_FILE_UUID,
        "sessionFile": f"/sandbox/.openclaw/agents/main/sessions/{CHILD_FILE_UUID}.jsonl",
        "spawnedBy": "agent:main:main",
        "spawnedWorkspaceDir": "/sandbox/.openclaw/workspace",
        "label": "ping-test",
        "status": child_status,
        "startedAt": now_ms - 60000,
        "updatedAt": now_ms,
        "lastInteractionAt": now_ms,
        "sessionStartedAt": now_ms - 60000,
        "runtimeMs": 55,
    }
    if ended:
        child["endedAt"] = now_ms - 55000
    if task:
        child["task"] = task
    return {
        "agent:main:main": {
            "sessionId": MAIN_UUID,
            "sessionFile": f"/sandbox/.openclaw/agents/main/sessions/{MAIN_UUID}.jsonl",
            "model": "anthropic/claude-opus-4-6",
        },
        f"agent:main:subagent:{CHILD_SA_UUID}": child,
    }


def _v3_user_line(text: str, ts_iso: str) -> dict:
    """Real v3 user-message envelope (content is a plain string)."""
    return {
        "type": "message",
        "id": str(uuid.uuid4()),
        "timestamp": ts_iso,
        "message": {"role": "user", "content": text,
                    "timestamp": int(time.time() * 1000)},
    }


def _v3_assistant_line(text: str, ts_iso: str, *, total_tokens: int = 120) -> dict:
    """Real v3 assistant envelope (content parts list + usage block)."""
    return {
        "type": "message",
        "id": str(uuid.uuid4()),
        "timestamp": ts_iso,
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "model": "anthropic/claude-opus-4-6",
            "provider": "anthropic",
            "usage": {"input": 100, "output": 20, "totalTokens": total_tokens},
        },
    }


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh LocalStore at a tmp path (same pattern as
    test_nemoclaw_runtime_adapter.py) so tests never touch the dev DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))  # daemon-detection shield
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _ingest_jsonl(store, batch: list[dict], fname: str, subagent_id: str | None):
    """Same call the sandbox loop makes (minus the cloud POST)."""
    from clawmetry import sync as _sync
    _sync._local_ingest_session_batch(batch, fname, "test-node",
                                      subagent_id, agent_type="nemoclaw")
    store.flush()


def _ingest_index(store, index: dict, sb_name: str = "sb-alpha"):
    from clawmetry import sync as _sync
    sub = _sync._parse_openclaw_subagent_index(index)
    _sync._ingest_sandbox_subagent_rows(sub, sb_name, "test-node")
    store.flush()
    return sub


# ── _parse_openclaw_subagent_index (pure) ────────────────────────────────────


def test_parse_index_real_shape():
    from clawmetry import sync as _sync
    sub = _sync._parse_openclaw_subagent_index(_real_index())
    assert CHILD_FILE_UUID in sub
    rec = sub[CHILD_FILE_UUID]
    assert rec["subagent_id"] == CHILD_SA_UUID
    # spawnedBy 'agent:main:main' resolves to the main entry's OWN sessionId.
    assert rec["parent_session_id"] == MAIN_UUID
    assert rec["label"] == "ping-test"
    assert rec["status"] == "failed"
    assert rec["spawn_depth"] == 1
    assert rec["subagent_role"] == "leaf"
    # No task on the real failed capture -> empty, never invented.
    assert rec["task"] == ""


def test_parse_index_unresolvable_spawner_keeps_parent_none():
    """A child whose spawner entry is missing gets parent None — not a guess."""
    from clawmetry import sync as _sync
    index = _real_index()
    del index["agent:main:main"]
    rec = _sync._parse_openclaw_subagent_index(index)[CHILD_FILE_UUID]
    assert rec["parent_session_id"] is None


def test_parse_index_ignores_non_subagent_keys():
    from clawmetry import sync as _sync
    assert _sync._parse_openclaw_subagent_index(
        {"agent:main:main": {"sessionId": MAIN_UUID}}) == {}
    assert _sync._parse_openclaw_subagent_index("not-a-dict") == {}


# ── linkage + enrichment ─────────────────────────────────────────────────────


def test_child_linkage_prompt_reply_and_tokens(isolated_store):
    """Delegation with a transcript: parent edge, kind, prompt from the
    child's own first user turn, reply from its last assistant turn, tokens
    from the child's OWN persisted usage (never the parent's)."""
    now = time.time()

    def iso(off: float) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now + off))

    # Parent transcript under its own file uuid.
    _ingest_jsonl(isolated_store, [
        _v3_user_line("Use the subagents tool to spawn one subagent", iso(0)),
        _v3_assistant_line("Spawned. Run ID: fc8920c6", iso(1), total_tokens=500),
    ], f"{MAIN_UUID}.jsonl", None)
    # Child transcript flushed under its SUBAGENT uuid (what the sandbox
    # loop now passes as subagent_id — the query_subagents join key).
    _ingest_jsonl(isolated_store, [
        _v3_user_line("Reply with exactly the word pong and nothing else.", iso(2)),
        _v3_assistant_line("pong", iso(3), total_tokens=120),
    ], f"{CHILD_FILE_UUID}.jsonl", CHILD_SA_UUID)
    _ingest_index(isolated_store,
                  _real_index(child_status="completed", ended=True))

    from clawmetry.adapters.nemo import NemoClawAdapter
    sessions = {s.id: s for s in NemoClawAdapter().list_sessions()}
    child = sessions[CHILD_SA_UUID]
    assert child.parent_id == MAIN_UUID
    assert child.extra["kind"] == "subagent"
    assert child.extra["isSubagent"] is True
    assert child.extra["depth"] == 1
    assert child.extra["agentType"] == "leaf"
    assert child.extra["label"] == "ping-test"
    assert child.title == "ping-test"
    assert child.extra["sandbox"] == "sb-alpha"
    # Prompt = the child's first user turn (IS the handed task text).
    assert child.extra["prompt"].startswith("Reply with exactly the word pong")
    assert child.extra["reply"] == "pong"
    # Tokens come from the child's own events, not the parent's 500.
    assert child.total_tokens == 120
    assert child.end_reason != "error"
    # The parent stays a plain top-level session.
    parent = sessions[MAIN_UUID]
    assert parent.parent_id is None
    assert "kind" not in parent.extra


def test_registry_task_wins_as_prompt(isolated_store):
    """When the registry persisted a task, it IS the handed context."""
    _ingest_jsonl(isolated_store, [
        _v3_user_line("Reply with pong.", "2026-08-20T00:17:38+00:00"),
    ], f"{CHILD_FILE_UUID}.jsonl", CHILD_SA_UUID)
    _ingest_index(isolated_store,
                  _real_index(child_status="completed", ended=True,
                              task="Reply with exactly the word pong"))
    from clawmetry.adapters.nemo import NemoClawAdapter
    child = {s.id: s for s in NemoClawAdapter().list_sessions()}[CHILD_SA_UUID]
    assert child.extra["prompt"] == "Reply with exactly the word pong"
    # No assistant turn on disk -> no reply invented.
    assert "reply" not in child.extra


# ── status mapping ───────────────────────────────────────────────────────────


def test_failed_child_without_transcript(isolated_store):
    """The REAL capture: a 55 ms 'failed' spawn that never wrote a
    transcript. The child is synthesised from the registry row alone —
    parent edge + error, but NO invented prompt/reply, zero messages."""
    _ingest_index(isolated_store, _real_index(child_status="failed", ended=True))
    from clawmetry.adapters.nemo import NemoClawAdapter
    sessions = {s.id: s for s in NemoClawAdapter().list_sessions()}
    child = sessions[CHILD_SA_UUID]
    assert child.parent_id == MAIN_UUID
    assert child.end_reason == "error"
    assert child.message_count == 0
    assert "prompt" not in child.extra
    assert "reply" not in child.extra
    assert child.cost_status != "running"
    assert child.ended_at is not None


def test_running_only_within_recency_window(isolated_store):
    """No endedAt + fresh updatedAt -> running; stale -> not running."""
    from clawmetry.adapters.nemo import NemoClawAdapter
    _ingest_index(isolated_store,
                  _real_index(child_status="", ended=False))
    child = {s.id: s for s in NemoClawAdapter().list_sessions()}[CHILD_SA_UUID]
    assert child.cost_status == "running"

    stale_ms = int((time.time() - 3600) * 1000)
    _ingest_index(isolated_store,
                  _real_index(now_ms=stale_ms, child_status="", ended=False))
    child = {s.id: s for s in NemoClawAdapter().list_sessions()}[CHILD_SA_UUID]
    assert child.cost_status != "running"


def test_compound_failure_reasons_map_to_error(isolated_store):
    """Substring matching on compound reason strings (contract)."""
    from clawmetry import sync as _sync
    from clawmetry.adapters.nemo import NemoClawAdapter
    index = _real_index(child_status="killed: sandbox torn down", ended=True)
    sub = _sync._parse_openclaw_subagent_index(index)
    _sync._ingest_sandbox_subagent_rows(sub, "sb-alpha", "test-node")
    isolated_store.flush()
    child = {s.id: s for s in NemoClawAdapter().list_sessions()}[CHILD_SA_UUID]
    assert child.end_reason == "error"


# ── honesty ──────────────────────────────────────────────────────────────────


def test_advisor_sibling_gets_no_parent(isolated_store):
    """Advisor-dir sessions are sibling agents, not delegations — no edge."""
    advisor_uuid = str(uuid.uuid4())
    _ingest_jsonl(isolated_store, [
        _v3_user_line("analyse the last run", "2026-08-20T01:00:00+00:00"),
        _v3_assistant_line("analysis done", "2026-08-20T01:00:05+00:00"),
    ], f"{advisor_uuid}.jsonl", None)
    _ingest_index(isolated_store, _real_index())
    from clawmetry.adapters.nemo import NemoClawAdapter
    adv = {s.id: s for s in NemoClawAdapter().list_sessions()}[advisor_uuid]
    assert adv.parent_id is None
    assert "kind" not in adv.extra
    assert "prompt" not in adv.extra


def test_unresolvable_spawner_child_has_no_parent(isolated_store):
    """Registry row without a resolvable spawner: child still surfaces
    (kind='subagent') but parent_id stays None — never guessed."""
    index = _real_index(child_status="completed", ended=True)
    del index["agent:main:main"]
    _ingest_index(isolated_store, index)
    from clawmetry.adapters.nemo import NemoClawAdapter
    child = {s.id: s for s in NemoClawAdapter().list_sessions()}[CHILD_SA_UUID]
    assert child.parent_id is None
    assert child.extra["kind"] == "subagent"


def test_sandbox_loop_passes_subagent_id_and_ingests_rows(isolated_store):
    """End-to-end through the mocked openshell loop: the sandbox's
    sessions.json is read once per sandbox, a delegation transcript flushes
    under its SUBAGENT uuid (the query_subagents join key), a plain
    transcript keeps the filename uuid, and one subagents row lands."""
    from unittest.mock import MagicMock, patch
    from clawmetry.sync import sync_sandbox_sessions_openshell

    def _run(returncode=0, stdout=""):
        r = MagicMock()
        r.returncode = returncode
        r.stdout = stdout
        return r

    index = _real_index(child_status="completed", ended=True,
                        task="Reply with exactly the word pong")
    line = json.dumps({"type": "message", "id": "e1",
                       "timestamp": "2026-08-20T00:17:38+00:00",
                       "message": {"role": "user", "content": "hi"}})
    side_effects = [
        _run(0, json.dumps([{"name": "sb-alpha", "status": "running"}])),
        _run(0, json.dumps(index)),                          # cat sessions.json
        _run(0, f"{MAIN_UUID}.jsonl\n{CHILD_FILE_UUID}.jsonl\n"),  # ls main
        _run(0, line + "\n"),                                # cat parent jsonl
        _run(0, line + "\n"),                                # cat child jsonl
        _run(1, ""),                                         # ls advisor (absent)
    ]

    flush_calls = []
    with patch("clawmetry.sync._find_openshell_bin",
               return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, f, *a, **k: flush_calls.append((f, a))):
        sync_sandbox_sessions_openshell(
            {"api_key": "", "encryption_key": None, "node_id": "n1"}, {})

    by_fname = {f: a for f, a in flush_calls}
    # positional args after fname: api_key, enc_key, node_id, subagent_id
    assert by_fname[f"{CHILD_FILE_UUID}.jsonl"][3] == CHILD_SA_UUID
    assert by_fname[f"{MAIN_UUID}.jsonl"][3] is None
    isolated_store.flush()
    rows = isolated_store.query_subagents(agent_type="nemoclaw")
    assert len(rows) == 1
    assert rows[0]["subagent_id"] == CHILD_SA_UUID
    assert rows[0]["parent_session_id"] == MAIN_UUID
    assert rows[0]["task"] == "Reply with exactly the word pong"


def test_capabilities_advertise_subagents():
    from clawmetry.adapters.base import Capability
    from clawmetry.adapters.nemo import NemoClawAdapter
    assert Capability.SUBAGENTS in NemoClawAdapter().capabilities()
