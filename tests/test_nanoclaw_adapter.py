"""Tests for clawmetry/adapters/nanoclaw.py.

Exercises NanoClawAdapter against the committed SQLite fixtures
(tests/fixtures/runtimes/nanoclaw/data/v2-sessions/...) built by
_make_sqlite_fixtures.py, plus a regenerated tmp-path copy so tests
never depend on a stale committed DB.

Covers: detection (count = session folders), session summary
(message_count across both tables, min/max timestamps), event merge
(inbound + outbound merge-sorted by seq with correct roles + parent_id),
the unknown-on-disk reality (model=="" / total_tokens==0 / cost None),
and the never-raises contract against missing / corrupt DBs.
"""
from __future__ import annotations

import os
import sqlite3

import pytest

from clawmetry.adapters.base import Capability, Event, Session
from clawmetry.adapters.nanoclaw import NanoClawAdapter

import importlib.util

_FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes", "nanoclaw")
_GEN_PATH = os.path.join(_FIX_DIR, "_make_sqlite_fixtures.py")


def _load_generator():
    spec = importlib.util.spec_from_file_location("_nanoclaw_fixture_gen", _GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def data_dir(tmp_path):
    """Freshly materialised v2-sessions root (independent of committed DBs)."""
    gen = _load_generator()
    return gen.make_fixtures(str(tmp_path / "v2-sessions"))


# ── committed fixtures sanity ────────────────────────────────────────────


def test_committed_fixtures_exist():
    root = os.path.join(_FIX_DIR, "data", "v2-sessions")
    inbound = os.path.join(root, "default", "sess-0001", "inbound.db")
    outbound = os.path.join(root, "default", "sess-0001", "outbound.db")
    assert os.path.isfile(inbound)
    assert os.path.isfile(outbound)
    adapter = NanoClawAdapter(data_dir=root)
    assert adapter.detect().detected is True


# ── detect ───────────────────────────────────────────────────────────────


def test_detect_when_present(data_dir):
    r = NanoClawAdapter(data_dir=data_dir).detect()
    assert r.detected is True
    assert r.name == "nanoclaw"
    assert r.display_name == "NanoClaw"
    assert r.running is False
    assert r.session_count == 1
    assert Capability.SESSIONS.value in r.capabilities
    assert Capability.EVENTS.value in r.capabilities
    assert r.meta["dataDir"] == data_dir


def test_detect_counts_multiple_session_folders(data_dir):
    # Add a second group/session by copying the first session's DBs.
    import shutil

    src = os.path.join(data_dir, "default", "sess-0001")
    dst = os.path.join(data_dir, "groupB", "sess-0002")
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(src, "inbound.db"), os.path.join(dst, "inbound.db"))
    shutil.copy(os.path.join(src, "outbound.db"), os.path.join(dst, "outbound.db"))
    r = NanoClawAdapter(data_dir=data_dir).detect()
    assert r.session_count == 2


def test_detect_missing_dir():
    r = NanoClawAdapter(data_dir="/no/such/nanoclaw/v2-sessions").detect()
    assert r.detected is False
    assert r.session_count == 0
    # capabilities still advertised so the chip bar can show a grey dot
    assert Capability.SESSIONS.value in r.capabilities


def test_detect_empty_dir(tmp_path):
    empty = tmp_path / "v2-sessions"
    empty.mkdir()
    r = NanoClawAdapter(data_dir=str(empty)).detect()
    # dir exists but no session folders -> not detected
    assert r.detected is False
    assert r.session_count == 0


# ── list_sessions ──────────────────────────────────────────────────────────


def test_list_sessions_summary(data_dir):
    [s] = NanoClawAdapter(data_dir=data_dir).list_sessions()
    assert isinstance(s, Session)
    assert s.agent == "nanoclaw"
    assert s.id == "sess-0001"
    # 2 inbound + 2 outbound = 4 messages across both tables
    assert s.message_count == 4
    # display_name comes from the latest (highest-seq) message text
    assert s.display_name == "session compacted"
    assert s.extra["agentGroupId"] == "default"


def test_list_sessions_min_max_timestamps(data_dir):
    [s] = NanoClawAdapter(data_dir=data_dir).list_sessions()
    # min = first inbound TS, max = last outbound TS
    assert s.started_at == pytest.approx(_iso("2026-05-25T10:00:00.000Z"))
    assert s.ended_at == pytest.approx(_iso("2026-05-25T10:01:02.500Z"))
    assert s.started_at < s.ended_at


def test_list_sessions_model_and_tokens_unknown_on_disk(data_dir):
    """Documents the OPEN QUESTION: no model/token/cost columns on disk."""
    [s] = NanoClawAdapter(data_dir=data_dir).list_sessions()
    assert s.model == ""
    assert s.total_tokens == 0
    assert s.input_tokens == 0
    assert s.output_tokens == 0
    assert s.cost_usd is None


def test_list_sessions_newest_first(data_dir):
    import shutil

    # Second session whose only message is far in the future -> sorts first.
    dst = os.path.join(data_dir, "default", "sess-zzz")
    os.makedirs(dst, exist_ok=True)
    conn = sqlite3.connect(os.path.join(dst, "inbound.db"))
    gen = _load_generator()
    conn.executescript(gen.INBOUND_SCHEMA)
    conn.execute(
        "INSERT INTO messages_in (id, seq, kind, timestamp, content) "
        "VALUES (?, ?, ?, ?, ?)",
        ("z0", 0, "chat", "2099-01-01T00:00:00.000Z", '{"text":"future"}'),
    )
    conn.commit()
    conn.close()
    # outbound.db is optional; absence must not break the read
    ids = [s.id for s in NanoClawAdapter(data_dir=data_dir).list_sessions()]
    assert ids[0] == "sess-zzz"
    assert "sess-0001" in ids


# ── list_events ───────────────────────────────────────────────────────────


def test_list_events_merge_sorted_by_seq(data_dir):
    events = NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    assert all(isinstance(e, Event) for e in events)
    # 4 messages total, merge-sorted by seq 0,1,2,3
    assert [e.extra["seq"] for e in events] == [0, 1, 2, 3]
    # roles: inbound chat -> user, outbound chat-sdk -> assistant,
    # inbound chat -> user, outbound system -> system
    assert [e.role for e in events] == ["user", "assistant", "user", "system"]
    # all message-typed (no tool structure in these tables)
    assert all(e.type == "message" for e in events)


def test_list_events_content_parsed(data_dir):
    events = NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    assert events[0].content == "ship the nanoclaw adapter"
    assert events[1].content == "on it - adapter coming up"
    # seq 2 stored content as a bare JSON string
    assert events[2].content == "and write the tests too"


def test_list_events_parent_id_from_in_reply_to(data_dir):
    events = NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    # outbound seq 1 replies to inbound id "in-0"
    assert events[1].id == "out-1"
    assert events[1].parent_id == "in-0"
    # inbound rows have no parent
    assert events[0].parent_id is None


def test_list_events_tokens_zero(data_dir):
    events = NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    assert all(e.tokens == 0 for e in events)


def test_list_events_chronological_ts(data_dir):
    events = NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    ts = [e.ts for e in events]
    assert ts == sorted(ts)


def test_list_events_unknown_session(data_dir):
    assert NanoClawAdapter(data_dir=data_dir).list_events("nope") == []


# ── capabilities (honesty) ─────────────────────────────────────────────────


def test_capabilities_only_sessions_and_events():
    caps = NanoClawAdapter().capabilities()
    assert caps == {Capability.SESSIONS, Capability.EVENTS}
    assert Capability.COST not in caps
    assert Capability.SUBAGENTS not in caps
    assert Capability.CRONS not in caps
    assert Capability.GATEWAY_RPC not in caps


# ── never-raises contract ───────────────────────────────────────────────────


def test_never_raises_on_corrupt_db(tmp_path):
    session_dir = tmp_path / "v2-sessions" / "g" / "s"
    session_dir.mkdir(parents=True)
    # Garbage where a SQLite file should be.
    (session_dir / "inbound.db").write_bytes(b"this is not a sqlite database")
    (session_dir / "outbound.db").write_bytes(b"\x00\x01\x02 corrupt")
    adapter = NanoClawAdapter(data_dir=str(tmp_path / "v2-sessions"))
    # None of these may raise.
    r = adapter.detect()
    assert r.detected is True  # inbound.db marker present
    # Corrupt DB -> readable=True attempt may fail; session may be dropped.
    sessions = adapter.list_sessions()
    assert isinstance(sessions, list)
    events = adapter.list_events("s")
    assert events == []


def test_never_raises_on_missing_data_dir():
    adapter = NanoClawAdapter(data_dir="/definitely/not/here")
    assert adapter.detect().detected is False
    assert adapter.list_sessions() == []
    assert adapter.list_events("x") == []


def test_read_only_does_not_modify_db(data_dir):
    """Reading must not change the DB file mtime/size (immutable open)."""
    db = os.path.join(data_dir, "default", "sess-0001", "outbound.db")
    before = os.stat(db)
    NanoClawAdapter(data_dir=data_dir).list_events("sess-0001")
    after = os.stat(db)
    assert before.st_size == after.st_size
    assert before.st_mtime == after.st_mtime


# ── helpers ───────────────────────────────────────────────────────────────


def _iso(s: str) -> float:
    from clawmetry.adapters.nanoclaw import _parse_ts

    return _parse_ts(s)
