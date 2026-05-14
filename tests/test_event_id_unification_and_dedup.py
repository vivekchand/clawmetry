"""Tests for #1232 — unified Claude Code event id derivation + v6→v7 dedup.

Three independent ingest paths used to write the same logical Claude Code
event under three different ids, defeating ``INSERT OR IGNORE`` dedup at the
local store boundary. The user observed 2x and 3x duplicate rows in Brain.

This test module covers both halves of the fix:

* **Write side**: ``_canonical_event_id`` produces an identical id for the
  same source event regardless of which translation path it flows through.
  Subagent rows keep their path-scoped scheme — different subagent files
  can legitimately reuse the same uuid, so the file basename must scope.

* **Migration side**: ``_run_dedup_migration_v7`` collapses pre-existing
  duplicate rows. Idempotent — second pass is a no-op. Index is created.
  Legitimate single rows are untouched.
"""

from __future__ import annotations

import importlib
import json
import time
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Reload local_store + sync with a fresh DuckDB per test."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH",
        str(tmp_path / "clawmetry.duckdb"),
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


# ── Half 1: id derivation must agree across all 3 ingest paths ──────────────

# A faithful Claude Code top-level assistant message — the shape that
# triggered the user's bug report (every assistant event got 2x rows).
SAMPLE_ASSISTANT = {
    "parentUuid": "e0a1b7f7-08e2-441d-b90a-e009fb3a6dd8",
    "isSidechain": False,
    "message": {
        "model": "claude-opus-4-7",
        "id": "msg_01TrFfvo7esVGyq81zMQUMAW",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "ok"}],
    },
    "type": "assistant",
    "timestamp": "2026-05-14T22:03:01.267Z",
    "uuid": "a8f0ec6e-47d9-4d31-991c-f12a13886ef0",
    "sessionId": "49f1d9fc-0848-4b6b-8fd7-64633bbc6b58",
}

# A queue-operation event — these have NO uuid in the source jsonl, so the
# canonical id falls back to the deterministic hash. The user observed
# 3x duplicates here (3 different ingest schemes, all wrote distinct ids).
SAMPLE_QUEUE_OP = {
    "type": "queue-operation",
    "operation": "enqueue",
    "timestamp": "2026-05-14T22:02:50.880Z",
    "sessionId": "49f1d9fc-0848-4b6b-8fd7-64633bbc6b58",
    "content": "Conversation info ...",
}


def test_canonical_id_top_level_event_with_uuid_is_deterministic(isolated_store):
    """Same source line → identical canonical id, every time."""
    sync, _ls = isolated_store
    a = sync._canonical_event_id(SAMPLE_ASSISTANT, session_id="sess-1")
    b = sync._canonical_event_id(dict(SAMPLE_ASSISTANT), session_id="sess-1")
    assert a == b
    assert a == "cc-msg:a8f0ec6e-47d9-4d31-991c-f12a13886ef0"


def test_canonical_id_uses_uuid_regardless_of_session_for_top_events(isolated_store):
    """Top-level events with a uuid are session-independent — that uuid is
    globally unique. Two different ``session_id`` parameters must produce
    the same id (the bug was paths #2 and #3 disagreeing on session_id)."""
    sync, _ls = isolated_store
    a = sync._canonical_event_id(SAMPLE_ASSISTANT, session_id="sess-A")
    b = sync._canonical_event_id(SAMPLE_ASSISTANT, session_id="sess-B")
    assert a == b


def test_canonical_id_strips_path_specific_metadata(isolated_store):
    """When the translate path injects ``_claude_session_id`` /
    ``_openclaw_session_id`` / ``_oc_cc_kind`` / ``parentUuid`` etc., the
    canonical id must NOT change. That metadata is the per-path noise the
    bug surfaced through."""
    sync, _ls = isolated_store
    base = sync._canonical_event_id(SAMPLE_QUEUE_OP, session_id="sess-1")
    polluted = dict(SAMPLE_QUEUE_OP)
    polluted["_claude_session_id"] = "abc"
    polluted["_openclaw_session_id"] = "def"
    polluted["_oc_cc_kind"] = "top"
    polluted["_subagent_file"] = "agent-foo.jsonl"
    polluted["parentUuid"] = "ignored"
    polluted["parentId"] = "also-ignored"
    after = sync._canonical_event_id(polluted, session_id="sess-1")
    assert base == after
    assert base.startswith("cc-derived:")


def test_all_three_translate_paths_produce_identical_id(isolated_store):
    """The contract that fixes the user's dupes: same Claude Code source
    line → same id from path #1 (sync_claude_cli_sessions →
    _translate_claude_cli_event), path #2 (process-discovery
    _translate_claude_session_line, no openclaw_session_id), and path #3
    (sessions.json walk, with openclaw_session_id)."""
    sync, _ls = isolated_store
    join_id = "625c0ad9-71af-4a56-9a3b-cab396860a85"

    # Path #1: _translate_claude_cli_event tags _cc_source then
    # _local_ingest_session_batch routes through _canonical_event_id.
    translated_p1 = sync._translate_claude_cli_event(SAMPLE_ASSISTANT)
    assert translated_p1.get("_cc_source") is True, (
        "_translate_claude_cli_event must mark events so the legacy "
        "_local_ingest path uses canonical id derivation"
    )
    id_p1 = sync._canonical_event_id(translated_p1, session_id=join_id)

    # Path #2: process-discovery — no openclaw_session_id, kind="top".
    row_p2 = sync._translate_claude_session_line(
        SAMPLE_ASSISTANT,
        session_id="claude-cli-uuid",  # the Claude session id, not OpenClaw
        node_id="local",
        line_no=42,
    )
    # Path #3: sessions.json walk — with openclaw_session_id, kind="top".
    row_p3 = sync._translate_claude_session_line(
        SAMPLE_ASSISTANT,
        session_id="claude-cli-uuid",
        node_id="local",
        line_no=42,
        openclaw_session_id=join_id,
        kind="top",
    )
    # All three ids agree — that's the dedup contract that lets
    # INSERT OR IGNORE collapse them at the store boundary.
    assert id_p1 == row_p2["id"] == row_p3["id"]
    assert id_p1 == "cc-msg:a8f0ec6e-47d9-4d31-991c-f12a13886ef0"


def test_subagent_id_keeps_path_scoped_scheme(isolated_store):
    """Subagent rows are NOT the dupes — different subagent files can reuse
    the same uuid, so the file basename must remain part of the id. The
    canonical-id treatment intentionally skips ``kind="subagent"``."""
    sync, _ls = isolated_store
    join_id = "oc-sess-1"
    row = sync._translate_claude_session_line(
        SAMPLE_ASSISTANT,
        session_id="claude-cli-uuid",
        node_id="local",
        line_no=42,
        openclaw_session_id=join_id,
        kind="subagent",
        subagent_file="agent-foo",
    )
    assert row["id"].startswith("openclaw-cc:oc-sess-1:subagent:agent-foo:")
    # The uuid is preserved at the tail of the id.
    assert row["id"].endswith(":a8f0ec6e-47d9-4d31-991c-f12a13886ef0")


def test_canonical_id_no_uuid_falls_back_to_deterministic_hash(isolated_store):
    """Events without a uuid (queue-operation, summary, etc.) get a stable
    content-derived id. Two reads of the same line → same id."""
    sync, _ls = isolated_store
    a = sync._canonical_event_id(SAMPLE_QUEUE_OP, session_id="sess-1")
    b = sync._canonical_event_id(dict(SAMPLE_QUEUE_OP), session_id="sess-1")
    assert a == b
    assert a.startswith("cc-derived:sess-1:2026-05-14T22:02:50.880Z:queue-operation:")


# ── Half 2: dedup migration ─────────────────────────────────────────────────


def _seed_old_schema_dupes(db_path: Path) -> tuple[int, list[str]]:
    """Pre-populate a DuckDB with a v6 events table containing the exact
    duplicate id schemes the bug created. Returns (total_seeded,
    legit_singleton_ids) so tests can verify the right rows survive."""
    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id            VARCHAR PRIMARY KEY,
            agent_type    VARCHAR NOT NULL DEFAULT 'openclaw',
            node_id       VARCHAR NOT NULL,
            agent_id      VARCHAR NOT NULL DEFAULT 'main',
            session_id    VARCHAR,
            workspace_id  VARCHAR,
            event_type    VARCHAR NOT NULL,
            ts            VARCHAR NOT NULL,
            data          BLOB,
            cost_usd      DOUBLE,
            token_count   INTEGER,
            model         VARCHAR,
            created_at    BIGINT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version    INTEGER PRIMARY KEY,
            applied_at BIGINT NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO schema_version VALUES (?, ?)",
        [6, int(time.time() * 1000)],
    )

    sess = "625c0ad9-71af-4a56-9a3b-cab396860a85"
    now_ms = int(time.time() * 1000)

    # Dupe set A: assistant event with uuid → 2 rows (path #1 bare + path #3 prefixed)
    asst_uuid = "a8f0ec6e-47d9-4d31-991c-f12a13886ef0"
    asst_ts = "2026-05-14T22:03:01.267Z"
    asst_body_p1 = json.dumps({
        "type": "assistant", "uuid": asst_uuid, "timestamp": asst_ts,
        "message": {"role": "assistant", "content": "ok"}
    }).encode("utf-8")
    asst_body_p3 = json.dumps({
        "type": "assistant", "uuid": asst_uuid, "timestamp": asst_ts,
        "message": {"role": "assistant", "content": "ok"},
        "_claude_session_id": "x", "_openclaw_session_id": sess,
    }).encode("utf-8")
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [asst_uuid, "openclaw", "node1", "main", sess, None, "assistant",
         asst_ts, asst_body_p1, None, None, None, now_ms],
    )
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [f"openclaw-cc:{sess}:top:{asst_uuid}", "openclaw", "node1", "main",
         sess, None, "assistant", asst_ts, asst_body_p3, None, None, None, now_ms],
    )

    # Dupe set B: attachment event with uuid (4-way dupe in user data was
    # actually 2 distinct uuids × 2 paths each — model that)
    att_uuids = ["29a6fa5f-81d1-4cc9-aa5f-48143580f73f",
                 "29124d13-814e-4597-b7e5-dc4dc8bc3e1a"]
    att_ts = "2026-05-09T10:01:27.863Z"
    for u in att_uuids:
        body = json.dumps({"type": "attachment", "uuid": u, "timestamp": att_ts}).encode()
        conn.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [u, "openclaw", "node1", "main", sess, None, "attachment",
             att_ts, body, None, None, None, now_ms],
        )
        conn.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [f"openclaw-cc:{sess}:top:{u}", "openclaw", "node1", "main", sess, None,
             "attachment", att_ts, body, None, None, None, now_ms],
        )

    # Legit singleton: a tool-result row that shouldn't be touched
    tool_id = f"openclaw-cc:{sess}:tool-result:abc.txt"
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [tool_id, "openclaw", "node1", "main", sess, None, "tool-result",
         "2026-05-14T20:00:00Z", b"tool body", None, None, None, now_ms],
    )

    # Legit singleton: subagent row (different subagent reuses uuid in real
    # data, so the file basename in the id is load-bearing)
    sub_id = f"openclaw-cc:{sess}:subagent:agent-foo:{asst_uuid}"
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [sub_id, "openclaw", "node1", "main", sess, None, "subagent:assistant",
         "2026-05-14T20:00:01Z", b"sub body", None, None, None, now_ms],
    )

    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    return total, [tool_id, sub_id]


def test_dedup_migration_collapses_duplicates(tmp_path, monkeypatch):
    """Seed a v6 store with the exact id-scheme dupes the bug created;
    open via local_store; verify v7 dedup migration collapsed each group
    to one row, and the unrelated singleton rows are untouched."""
    db_path = tmp_path / "clawmetry.duckdb"
    seeded_total, singleton_ids = _seed_old_schema_dupes(db_path)
    # 2 assistant + 4 attachment + 2 singletons = 8
    assert seeded_total == 8

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store(read_only=False)

    conn = duckdb.connect(str(db_path), read_only=False)
    after_total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    # Each (ts, type, session, uuid) group collapses to 1.
    # 1 assistant + 2 attachments (2 distinct uuids) + 2 singletons = 5.
    assert after_total == 5

    # The 22:03:01 assistant group: 2 → 1
    asst_count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE ts='2026-05-14T22:03:01.267Z' "
        "AND event_type='assistant'"
    ).fetchone()[0]
    assert asst_count == 1

    # The 2026-05-09 attachment group: 4 → 2 (2 distinct uuids preserved)
    att_count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE ts='2026-05-09T10:01:27.863Z' "
        "AND event_type='attachment'"
    ).fetchone()[0]
    assert att_count == 2

    # The legit singletons must still be there.
    for sid in singleton_ids:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM events WHERE id=?", [sid]
        ).fetchone()[0]
        assert cnt == 1, f"singleton {sid!r} was wrongly removed"

    # Schema bumped.
    sv = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert sv >= 7

    conn.close()
    store.stop(flush=False)


def test_dedup_migration_is_idempotent(tmp_path, monkeypatch):
    """Open the store twice; the second open must NOT delete any more rows."""
    db_path = tmp_path / "clawmetry.duckdb"
    _seed_old_schema_dupes(db_path)

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store1 = ls.get_store(read_only=False)
    conn = duckdb.connect(str(db_path), read_only=False)
    after_first = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    store1.stop(flush=False)

    # Second open — schema_version is already 7, dedup must skip.
    ls._reset_singleton_for_tests()
    importlib.reload(ls)
    store2 = ls.get_store(read_only=False)
    conn = duckdb.connect(str(db_path), read_only=False)
    after_second = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    store2.stop(flush=False)

    assert after_second == after_first


def test_dedup_migration_creates_perf_index(tmp_path, monkeypatch):
    """The v7 migration brings a new (session_id, ts, event_type) index for
    future analytical queries that scan a session timeline by event_type."""
    db_path = tmp_path / "clawmetry.duckdb"
    _seed_old_schema_dupes(db_path)

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store(read_only=False)

    conn = duckdb.connect(str(db_path), read_only=False)
    rows = conn.execute(
        "SELECT index_name FROM duckdb_indexes() "
        "WHERE table_name='events' AND index_name='idx_events_session_ts_type'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()
    store.stop(flush=False)


def test_dedup_migration_safe_on_fresh_store(tmp_path, monkeypatch):
    """A brand-new store (no events at all) must come up cleanly with
    schema_version=7 and zero events. The migration must not error."""
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store(read_only=False)

    conn = duckdb.connect(str(db_path), read_only=False)
    n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    sv = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    conn.close()
    store.stop(flush=False)

    assert n == 0
    assert sv == ls.SCHEMA_VERSION
