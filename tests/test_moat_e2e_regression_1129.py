"""End-to-end MOAT regression gauntlet for the 4 read-path bugs filed in
issue #1129.

Each of the 4 fixes is queued in its own PR (#1130, #1131, #1132 — #1128 is
unrelated dead-code in sync.py) but **none are merged yet**. This file
exercises every bug from the *outside* of the fix — i.e. through the public
write+read API — so the moment the corresponding PR lands the test flips
green and stays green forever.

Expected behaviour today on bare ``main``: **all 4 tests FAIL**. That is
the proof the gauntlet actually catches the bugs.

Expected behaviour after #1130 + #1131 + #1132 merge: **all 4 PASS**.

Each test is independent: a failure in one does not mask the others.
We synthesise OpenClaw-shape events instead of spawning the real binary
because (a) it's faster, (b) the binary needs LLM creds, and (c) the
failure modes are 100% determined by the field shape — which we can pin
down here with a hand-written payload.

Reference fixtures patterns: ``tests/test_real_openclaw_binary_e2e.py``
(heaviest E2E, real binary) and ``tests/test_local_store_sync_integration.py``
(lighter pattern using only local_store + sync helpers — what we copy here).
"""

from __future__ import annotations

import importlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


# ── Shared fixture: hermetic DuckDB + reloaded local_store + sync ─────────


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Spin up a fresh, on-disk DuckDB per test. Reloads ``local_store``
    + ``sync`` so module-level paths pick up the tmp DB. Yields the two
    modules so each test can drive whichever entry point it wants
    (``store.ingest`` for direct event writes, ``sync.sync_sessions_recent``
    for the daemon path)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    yield {"ls": ls, "sync": sync, "tmp_path": tmp_path}
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _wait_drained(store, timeout=2.0):
    """Wait for the async flusher to commit ring → DuckDB."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain (depth={store.health()['ring_depth']})"
    )


# ── Test 1 — phantom .trajectory session_id (PR #1130) ────────────────────


def test_phantom_trajectory_session_id_not_in_duckdb(isolated_store, monkeypatch):
    """Bug 1: ``_list_session_jsonls`` walks every ``*.jsonl`` including
    ``<sid>.trajectory.jsonl`` / ``<sid>.checkpoint.jsonl`` /
    ``<sid>.deleted.jsonl`` sidecars. ``_canonical_session_file`` then splits
    the basename at ``.jsonl``, producing a session_id like ``aaa.trajectory``.
    Result: a phantom row per sidecar, polluting ``/api/sessions`` and
    ``/api/brain-history``.

    This test builds a real sessions dir on disk with one real session
    plus three sidecars, runs the daemon's ``sync_sessions_recent`` (the
    same entry point launchd hits every 15s), and asserts the only
    session_id that landed in DuckDB is the real one — no ``.trajectory``
    / ``.checkpoint`` / ``.deleted`` suffix anywhere.

    On main today: 4 distinct session_ids in DuckDB (real + 3 phantoms).
    After #1130: 1 distinct session_id.
    """
    sync = isolated_store["sync"]
    ls = isolated_store["ls"]
    sessions_dir = isolated_store["tmp_path"] / "sessions"
    sessions_dir.mkdir()

    # Recent timestamp so sync_sessions_recent's 60-min cutoff includes it.
    now = datetime.now(timezone.utc)
    ts = (now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")

    real_sid = "aaaaaaaa-1111-2222-3333-444444444444"

    # 1) Real session: 1 event.
    (sessions_dir / f"{real_sid}.jsonl").write_text(
        json.dumps({"id": "ev-real-1", "type": "message", "timestamp": ts,
                    "message": {"role": "user", "content": "hi"}}) + "\n"
    )
    # 2) Trajectory sidecar: 10 events. Same UUID prefix.
    traj_lines = [
        json.dumps({"id": f"traj-{i}", "type": "trace.artifacts",
                    "timestamp": ts, "data": {"trace": "noisy"}})
        for i in range(10)
    ]
    (sessions_dir / f"{real_sid}.trajectory.jsonl").write_text("\n".join(traj_lines) + "\n")
    # 3) Checkpoint sidecar: 5 events.
    chk_lines = [
        json.dumps({"id": f"chk-{i}", "type": "checkpoint.snapshot",
                    "timestamp": ts, "data": {"snapshot": "x"}})
        for i in range(5)
    ]
    (sessions_dir / f"{real_sid}.checkpoint.jsonl").write_text("\n".join(chk_lines) + "\n")
    # 4) Deleted sidecar: 2 events. (Per #1130 description, also filtered.)
    del_lines = [
        json.dumps({"id": f"del-{i}", "type": "session.deleted",
                    "timestamp": ts, "data": {}})
        for i in range(2)
    ]
    (sessions_dir / f"{real_sid}.deleted.jsonl").write_text("\n".join(del_lines) + "\n")

    config = {"api_key": "cm_test", "encryption_key": None, "node_id": "agent+test-1129"}
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": str(sessions_dir)}
    with patch.object(sync, "_post"):
        sync.sync_sessions_recent(config, state, paths, minutes=60)

    store = ls.get_store()
    _wait_drained(store)

    sids = {r[0] for r in store._fetch("SELECT DISTINCT session_id FROM events", [])}
    # The bug surfaces as session_ids ending in ".trajectory", ".checkpoint",
    # or ".deleted". Any of those means the sidecar was ingested.
    bad = {s for s in sids
           if s and (s.endswith(".trajectory") or s.endswith(".checkpoint")
                     or s.endswith(".deleted"))}
    assert not bad, (
        f"phantom session_id(s) leaked into DuckDB from sidecar .jsonl files: "
        f"{bad!r}. All session_ids in DuckDB: {sids!r}"
    )
    # Stronger claim: only the real session should appear.
    assert sids == {real_sid}, (
        f"expected only the real session_id {real_sid!r} in DuckDB, "
        f"got {sids!r} — sidecar files are being ingested as phantom sessions"
    )


# ── Test 2 — _event_to_row drops nested OpenClaw metrics (PR #1131) ───────


def test_event_metrics_extracted_from_nested_openclaw_payload(isolated_store):
    """Bug 2: ``_event_to_row`` reads ``e['cost_usd'] / e['token_count'] /
    e['model']`` directly off the top-level event dict. OpenClaw's gateway
    instead nests them under ``data.modelId`` and
    ``data.promptCache.lastCallUsage.{input,output,total}``. The store
    silently writes NULLs into all three columns.

    PR #1131 adds ``_extract_event_metrics`` which understands the nested
    shapes. This test:

    1. Writes one OpenClaw-shape event (nested) — must be extracted.
    2. Writes one Anthropic-shape event with top-level keys — must be
       preserved (regression: don't break the existing path).

    On main today: NULL columns for the OpenClaw event.
    After #1131: model/token_count populated, cost_usd either populated
    via ``providers_pricing`` or left NULL but not the OTHER two columns.
    """
    ls = isolated_store["ls"]
    store = ls.get_store()

    # Recent ts to keep query happy.
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 1) OpenClaw nested-shape event. This is the row that breaks today.
    oc_event = {
        "id": "ev-openclaw-1",
        "node_id": "agent+test-1129",
        "agent_id": "main",
        "session_id": "moat-bug2",
        "event_type": "trace.artifacts",
        "ts": ts,
        # NB: top-level cost_usd / token_count / model deliberately ABSENT.
        # The data blob carries them in OpenClaw's native nested form.
        "data": {
            "type": "trace.artifacts",
            "modelId": "claude-opus-4-7",
            "provider": "anthropic",
            "promptCache": {
                "lastCallUsage": {"input": 100, "output": 200, "total": 300},
            },
        },
    }
    store.ingest(oc_event)

    # 2) Already-extracted top-level event (interceptor / claude-cli adapter
    #    / cloud sync flow). Must keep working — regression guard.
    flat_event = {
        "id": "ev-flat-1",
        "node_id": "agent+test-1129",
        "agent_id": "main",
        "session_id": "moat-bug2",
        "event_type": "tool_call",
        "ts": ts,
        "model": "claude-haiku",
        "token_count": 42,
        "cost_usd": 0.0017,
        "data": {"tool": "Bash", "input": "ls"},
    }
    store.ingest(flat_event)

    _wait_drained(store)

    rows = {r["id"]: r for r in store.query_events(session_id="moat-bug2")}
    assert set(rows.keys()) == {"ev-openclaw-1", "ev-flat-1"}, (
        f"expected both events to land in DuckDB, got: {list(rows.keys())!r}"
    )

    oc = rows["ev-openclaw-1"]
    # Hard claim: model + tokens MUST be extracted from the nested payload.
    assert oc["model"] == "claude-opus-4-7", (
        f"OpenClaw event lost model: column = {oc['model']!r}, expected "
        f"'claude-opus-4-7' (extracted from data.modelId). "
        f"This is the silent NULL bug from #1129."
    )
    assert oc["token_count"] == 300, (
        f"OpenClaw event lost token_count: column = {oc['token_count']!r}, "
        f"expected 300 (data.promptCache.lastCallUsage.total). "
        f"This is the silent NULL bug from #1129."
    )
    # Cost is opportunistic: providers_pricing may or may not know about
    # claude-opus-4-7. Either NULL or a sensible positive float is OK —
    # the bug is that the OTHER two columns are NULL today.
    assert oc["cost_usd"] is None or oc["cost_usd"] > 0, (
        f"cost_usd should be NULL or positive, got {oc['cost_usd']!r}"
    )

    # Regression guard: top-level shape still works.
    flat = rows["ev-flat-1"]
    assert flat["model"] == "claude-haiku"
    assert flat["token_count"] == 42
    assert round(flat["cost_usd"], 6) == 0.0017


# ── Test 3 — /api/transcript renders OpenClaw shapes (PR #1132 bug 3) ─────


def test_transcript_renders_openclaw_event_shapes(isolated_store, monkeypatch):
    """Bug 3: ``_try_local_store_transcript`` (routes/sessions.py) assumes
    every DuckDB event row is an Anthropic-shape ``{role, content, usage,
    tool_calls}`` dict. OpenClaw writes ``{type: "<ns>.<action>", data:
    {...}}``. The fallback path treats ``role = obj.get("type")`` — so the
    transcript renders empty rows with role ``"trace.artifacts"`` etc.,
    OR (worse) drops them entirely because the content+role allowlist
    skips them.

    PR #1132 adds ``_is_openclaw_event`` + ``_expand_openclaw_event`` which
    map:

    - ``prompt.submitted`` (``data.finalPromptText``) → user
    - ``trace.artifacts`` (``data.assistantTexts``) → assistant
    - ``model.completed`` (``data.completionText``) → assistant
    - ``session.ended``, ``agent.heartbeat`` → skipped (plumbing)

    Today on main: messageCount == 0 (or worse — garbage rows with
    role="trace.artifacts"). After #1132: messageCount == 3.
    """
    ls = isolated_store["ls"]
    sync = isolated_store["sync"]
    store = ls.get_store()

    sid = "moat-bug3"
    base = datetime.now(timezone.utc)

    def _ts(offset_sec):
        return (base + timedelta(seconds=offset_sec)).isoformat().replace("+00:00", "Z")

    # Five OpenClaw-shape events. The first three should render as
    # transcript turns; the last two are plumbing and MUST be skipped.
    # Shape note (per commit 9be80b5): the v3 sync parser stamps
    # ``data.type`` at the top of the data blob AND nests the original
    # OpenClaw payload under ``data.data``. The transcript helper reads
    # content fields from that inner ``data`` dict. The fixture mirrors
    # that real production shape so we exercise the same code path users hit.
    events = [
        {
            "id": "oc-1", "node_id": "n", "agent_id": "main",
            "session_id": sid, "event_type": "prompt.submitted",
            "ts": _ts(0),
            "data": {
                "type": "prompt.submitted",
                "data": {"finalPromptText": "hi"},
            },
        },
        {
            "id": "oc-2", "node_id": "n", "agent_id": "main",
            "session_id": sid, "event_type": "trace.artifacts",
            "ts": _ts(1),
            "data": {
                "type": "trace.artifacts",
                "modelId": "claude-opus-4-7",
                "data": {
                    "assistantTexts": ["hello!"],
                    "promptCache": {
                        "lastCallUsage": {"input": 50, "output": 30, "total": 80},
                    },
                },
            },
        },
        {
            "id": "oc-3", "node_id": "n", "agent_id": "main",
            "session_id": sid, "event_type": "model.completed",
            "ts": _ts(2),
            "data": {
                "type": "model.completed",
                "data": {"completionText": "more"},
            },
        },
        # Plumbing — must NOT appear in the transcript.
        {
            "id": "oc-4", "node_id": "n", "agent_id": "main",
            "session_id": sid, "event_type": "session.ended",
            "ts": _ts(3),
            "data": {"type": "session.ended", "data": {}},
        },
        {
            "id": "oc-5", "node_id": "n", "agent_id": "main",
            "session_id": sid, "event_type": "agent.heartbeat",
            "ts": _ts(4),
            "data": {"type": "agent.heartbeat", "data": {}},
        },
    ]
    for ev in events:
        store.ingest(ev)
    _wait_drained(store)

    # Reload routes/sessions.py so it picks up the same local_store singleton
    # we've been writing to (it does a late ``from clawmetry import
    # local_store`` so a reload is enough — no Flask app needed).
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    result = sessions_mod._try_local_store_transcript(sid)
    assert result is not None, (
        "_try_local_store_transcript returned None even though DuckDB has "
        "5 events for this session — the helper short-circuited."
    )
    assert result.get("_source") == "local_store"

    msgs = result.get("messages") or []
    # Reject phantom rows that the buggy fallback might emit.
    bad_roles = [m for m in msgs
                 if m.get("role") in ("trace.artifacts", "prompt.submitted",
                                      "model.completed", "session.ended",
                                      "agent.heartbeat", "unknown")]
    assert not bad_roles, (
        f"transcript leaked OpenClaw event types as transcript roles: "
        f"{bad_roles!r}. The renderer must map them to user/assistant/tool "
        f"or skip — never expose the wire-protocol type to the user."
    )

    # The 3 real turns must be present.
    by_role_content = [(m.get("role"), m.get("content")) for m in msgs]
    assert ("user", "hi") in by_role_content, (
        f"missing user turn ('hi') from prompt.submitted. Got: {by_role_content!r}"
    )
    assert ("assistant", "hello!") in by_role_content, (
        f"missing assistant turn ('hello!') from trace.artifacts.assistantTexts. "
        f"Got: {by_role_content!r}"
    )
    assert ("assistant", "more") in by_role_content, (
        f"missing assistant turn ('more') from model.completed.completionText. "
        f"Got: {by_role_content!r}"
    )
    # Exactly 3 — nothing else, in particular no session.ended / agent.heartbeat.
    assert len(msgs) == 3, (
        f"expected exactly 3 transcript turns (user + 2 assistant), got "
        f"{len(msgs)}: {by_role_content!r}. session.ended and agent.heartbeat "
        f"must be skipped as plumbing."
    )

    # Model must be picked up from the trace.artifacts event's modelId.
    assert result.get("model") == "claude-opus-4-7", (
        f"model not extracted from data.modelId; got {result.get('model')!r}"
    )
    # Tokens must come from data.promptCache.lastCallUsage.total.
    assert result.get("totalTokens", 0) > 0, (
        f"totalTokens should reflect promptCache.lastCallUsage.total (80), "
        f"got {result.get('totalTokens')!r}"
    )


# ── Test 4 — /api/sessions message_count is computed (PR #1132 bug 4) ─────


def test_sessions_message_count_reflects_actual_event_count(isolated_store):
    """Bug 4: ``query_sessions_table`` reads ``message_count`` directly from
    the sessions table column, but the OpenClaw ingest path never populates
    it (only sync.py + Claude Code adapter do). Result: every OpenClaw
    session shows ``message_count: 0`` even when there are dozens of
    events for it.

    PR #1132 fixes this with a correlated subquery against ``events``,
    taking ``GREATEST(stored_value, computed_count)`` so adapters that
    DO populate the column (and may have no events table rows) still work.

    On main today: message_count == 0 for the populated session.
    After #1132: message_count == 7.
    """
    ls = isolated_store["ls"]
    store = ls.get_store()

    base = datetime.now(timezone.utc)
    def _ts(offset_sec):
        return (base + timedelta(seconds=offset_sec)).isoformat().replace("+00:00", "Z")

    # Session row WITHOUT an explicit message_count (i.e. column starts at 0).
    store.ingest_session({
        "agent_type": "openclaw",
        "session_id": "s1",
        "node_id": "n",
        "agent_id": "main",
        "title": "MOAT bug 4 test",
        "started_at": _ts(0),
        "last_active_at": _ts(10),
        "status": "active",
        "total_tokens": 0,
        "cost_usd": 0.0,
        # message_count omitted on purpose — exercises the bug.
    })

    # 7 events for that session.
    for i in range(7):
        store.ingest({
            "id": f"s1-ev-{i}",
            "node_id": "n",
            "agent_id": "main",
            "session_id": "s1",
            "event_type": "message",
            "ts": _ts(i),
            "data": {"i": i},
        })

    # Edge case: a SECOND session with zero events.
    store.ingest_session({
        "agent_type": "openclaw",
        "session_id": "s-empty",
        "node_id": "n",
        "agent_id": "main",
        "title": "Empty session",
        "started_at": _ts(100),
        "last_active_at": _ts(100),
        "status": "active",
    })

    _wait_drained(store)

    rows = store.query_sessions_table(agent_type="openclaw", limit=50)
    by_sid = {r["session_id"]: r for r in rows}

    assert "s1" in by_sid, (
        f"populated session 's1' missing from query_sessions_table output: "
        f"{list(by_sid.keys())!r}"
    )
    assert by_sid["s1"]["message_count"] == 7, (
        f"message_count for 's1' should reflect the 7 events ingested for it, "
        f"got {by_sid['s1']['message_count']!r}. This is the silent-zero bug "
        f"from #1129 — the column is never populated on OpenClaw ingest, so "
        f"the read-side has to compute it from events."
    )

    # Edge case: zero-event session must not crash, must be 0.
    assert "s-empty" in by_sid
    assert by_sid["s-empty"]["message_count"] == 0, (
        f"empty session should report message_count=0, got "
        f"{by_sid['s-empty']['message_count']!r}"
    )


# ── Test 5 — v3 underscore session renders end-to-end via fast path ───────


def test_v3_session_renders_transcript_via_local_store_fast_path(isolated_store):
    """Bug 5 (MOAT closing): real-world OpenClaw .jsonl files use the v3
    underscore schema (#1135). PR #1137 added ``_parse_v3_event`` which
    maps each underscore type to the trajectory-shape dot.separated
    ``event_type`` column — but the parser dropped ``type`` from the
    serialised ``data`` blob and stored content fields FLAT at the top
    level.

    The downstream transcript expander in routes/sessions.py uses
    ``_is_openclaw_event(obj)`` which checks ``obj.get("type")`` for a dot;
    on v3-mapped rows that returned None, so the OpenClaw branch never
    fired, the function fell through to the Anthropic shape, and
    /api/transcript/<sid> rendered 0 messages even though /api/brain-history
    (which reads the typed event_type column directly) worked fine.

    This test feeds a synthetic v3 session through the daemon ingest path
    and asserts that ``_try_local_store_transcript`` returns the local_store
    fast path with the correct user/assistant/tool turns. On main before
    this PR: messageCount==0. After: messageCount>=3 (user, assistant, tool).
    """
    sync = isolated_store["sync"]
    ls = isolated_store["ls"]
    store = ls.get_store()

    sid = "moat-bug5-v3-session"
    base = datetime.now(timezone.utc)
    def _ts(offset_sec):
        return (base + timedelta(seconds=offset_sec)).isoformat().replace("+00:00", "Z")

    # Real-shape v3 events (mirror what OpenClaw writes today).
    v3_events = [
        {"type": "session", "version": 3, "id": sid,
         "timestamp": _ts(0), "cwd": "/tmp/x"},
        {"type": "model_change", "id": "mc1", "timestamp": _ts(1),
         "modelId": "claude-opus-4-7", "provider": "anthropic"},
        {"type": "message", "id": "u1", "timestamp": _ts(2),
         "message": {"role": "user",
                     "content": [{"type": "text", "text": "ping"}]}},
        {"type": "message", "id": "a1", "timestamp": _ts(3),
         "message": {"role": "assistant",
                     "content": [{"type": "text", "text": "pong"}],
                     "model": "claude-opus-4-7",
                     "usage": {"input": 10, "output": 5, "totalTokens": 15}}},
        {"type": "tool_use_result", "id": "tr1", "timestamp": _ts(4),
         "tool_use_id": "tu1",
         "content": [{"type": "text", "text": "tool ran"}]},
    ]

    sync._local_ingest_session_batch(
        v3_events,
        session_file=f"{sid}.jsonl",
        node_id="agent+test-1129",
        subagent_id=None,
    )
    _wait_drained(store)

    # Reload routes/sessions.py so it picks up the same local_store singleton.
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    result = sessions_mod._try_local_store_transcript(sid)
    assert result is not None, (
        "_try_local_store_transcript returned None for a v3 session — "
        "the fast path short-circuited (rows empty or exception)."
    )
    assert result.get("_source") == "local_store", (
        f"transcript must come from local_store fast path, got "
        f"_source={result.get('_source')!r}"
    )

    msgs = result.get("messages") or []
    by_role_content = [(m.get("role"), m.get("content")) for m in msgs]

    # Reject phantom rows that the buggy fallback might emit.
    bad_roles = [m for m in msgs
                 if m.get("role") in ("session.started", "model.changed",
                                      "prompt.submitted", "model.completed",
                                      "tool.result", "unknown")]
    assert not bad_roles, (
        f"transcript leaked v3 wire-protocol event types as transcript roles: "
        f"{bad_roles!r}. The renderer must map them to user/assistant/tool."
    )

    # The 3 real turns must be present with correct role mapping.
    assert ("user", "ping") in by_role_content, (
        f"missing user turn ('ping') from v3 message(user→prompt.submitted). "
        f"Got: {by_role_content!r}"
    )
    assistants = [c for r, c in by_role_content if r == "assistant"]
    assert any("pong" in (c or "") for c in assistants), (
        f"missing assistant turn ('pong') from v3 message(assistant→model.completed). "
        f"Got: {by_role_content!r}"
    )
    tools = [c for r, c in by_role_content if r == "tool"]
    assert any("tool ran" in (c or "") for c in tools), (
        f"missing tool turn ('tool ran') from v3 tool_use_result→tool.result. "
        f"Got: {by_role_content!r}"
    )

    assert result.get("messageCount", 0) >= 3, (
        f"expected at least 3 transcript turns (user + assistant + tool), got "
        f"{result.get('messageCount')!r}: {by_role_content!r}. "
        f"This is the MOAT-closing bug — without data.type the OpenClaw "
        f"discriminator rejects every v3 row."
    )

    # Model must be picked up from data.modelId on the assistant turn.
    assert result.get("model") == "claude-opus-4-7", (
        f"model not extracted from v3 assistant data.modelId; "
        f"got {result.get('model')!r}"
    )
    # Tokens must come from data.data.promptCache.lastCallUsage.total.
    assert result.get("totalTokens", 0) >= 15, (
        f"totalTokens should reflect v3 usage.totalTokens (15), "
        f"got {result.get('totalTokens')!r}"
    )
