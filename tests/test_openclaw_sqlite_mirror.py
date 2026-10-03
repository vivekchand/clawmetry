"""OpenClaw 2026.9.x keeps transcripts in SQLite, not ``<sid>.jsonl``.

``clawmetry/openclaw_sqlite.py`` mirrors that store back into the JSONL
layout the daemon reads. These tests build a database with the real table
shapes (captured from OpenClaw 2026.9.7, schema_version 24) and pin:

  * events, the sessions.json index and context.compiled trajectory lines
    all land in the mirror, append-only across passes;
  * a transcript rewritten underneath us never duplicates or reorders
    already-mirrored lines;
  * ``sync._openclaw_sessions_dir`` picks the mirror only when the legacy
    sessions dir has no live transcript;
  * ``sync_sessions`` ingests the mirrored events;
  * a store on the schema that predates ``transcript_events.event_zstd``
    still mirrors (that column arrives with 2026.9.6 / agent schema 23;
    2026.9.2 — the version CI pins — is schema 19 and has only
    ``event_json``).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from clawmetry import openclaw_sqlite as ocs

SID = "a2a98642-289c-4f06-b989-53f3bfca3b5d"

_SCHEMA = """
CREATE TABLE session_nodes (session_key TEXT PRIMARY KEY,
  current_session_id TEXT NOT NULL, entry_json TEXT NOT NULL);
CREATE TABLE session_windows (session_id TEXT PRIMARY KEY, session_key TEXT,
  created_at INTEGER, updated_at INTEGER, transcript_updated_at INTEGER,
  status TEXT, chat_type TEXT, model_provider TEXT, model TEXT,
  display_name TEXT);
CREATE TABLE transcript_events (session_id TEXT NOT NULL, seq INTEGER NOT NULL,
  event_json TEXT, created_at INTEGER NOT NULL, event_zstd BLOB,
  PRIMARY KEY (session_id, seq));
CREATE TABLE transcript_event_identities (session_id TEXT NOT NULL,
  event_id TEXT NOT NULL, seq INTEGER NOT NULL,
  PRIMARY KEY (session_id, event_id));
CREATE TABLE trajectory_runtime_events (session_id TEXT NOT NULL,
  seq INTEGER NOT NULL, run_id TEXT, event_json TEXT NOT NULL,
  created_at INTEGER NOT NULL, PRIMARY KEY (session_id, seq));
"""


# The same tables as above on the pre-2026.9.6 schema: transcript_events
# carries event_json only. Naming event_zstd against this store raised
# "no such column", which sync_mirror turned into a pass that returned
# None — so on 2026.9.2 the mirror produced nothing at all.
_SCHEMA_PRE_ZSTD = _SCHEMA.replace(
    "  event_json TEXT, created_at INTEGER NOT NULL, event_zstd BLOB,\n",
    "  event_json TEXT, created_at INTEGER NOT NULL,\n",
)


def _event(i: int, role: str = "user") -> dict:
    msg: dict = {"role": role, "content": f"turn {i} — héllo"}
    if role == "assistant":
        msg.update({"model": "gpt-6-astra", "provider": "openai",
                    "content": [{"type": "text", "text": f"reply {i}"}],
                    "usage": {"input": 10, "output": 5, "totalTokens": 15,
                              "cost": {"total": 0.001}}})
    return {"type": "message", "id": f"ev-{i}", "parentId": None,
            "timestamp": f"2026-10-01T22:24:{i:02d}.000Z", "message": msg}


def _add_events(db: Path, events: list, start: int = 0) -> None:
    conn = sqlite3.connect(db)
    for i, ev in enumerate(events, start=start):
        conn.execute("INSERT INTO transcript_events (session_id, seq, event_json,"
                     " created_at) VALUES (?,?,?,0)", (SID, i, json.dumps(ev)))
        conn.execute("INSERT INTO transcript_event_identities VALUES (?,?,?)",
                     (SID, ev["id"], i))
    conn.commit()
    conn.close()


@pytest.fixture
def openclaw_home(tmp_path, monkeypatch):
    """A fake ~/.openclaw with an empty legacy sessions dir + the SQLite
    transcript store, and the mirror redirected under tmp_path."""
    return _build_openclaw_home(tmp_path, monkeypatch, _SCHEMA)


@pytest.fixture
def openclaw_home_pre_zstd(tmp_path, monkeypatch):
    """The same, on the schema that predates transcript_events.event_zstd."""
    return _build_openclaw_home(tmp_path, monkeypatch, _SCHEMA_PRE_ZSTD)


def _build_openclaw_home(tmp_path, monkeypatch, schema: str):
    oc = tmp_path / ".openclaw"
    (oc / "agents" / "main" / "sessions").mkdir(parents=True)
    db = ocs.agent_db_path(oc)
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.executescript(schema)
    conn.execute("INSERT INTO session_nodes VALUES (?,?,?)", (
        "agent:main:main", SID,
        json.dumps({"sessionId": SID, "chatType": "direct"})))
    conn.execute("INSERT INTO session_windows VALUES (?,?,?,?,?,?,?,?,?,?)", (
        SID, "agent:main:main", 1, 2, 2, "done", "direct", "openai",
        "gpt-6-astra", "Hello"))
    conn.execute("INSERT INTO trajectory_runtime_events VALUES (?,?,?,?,0)", (
        SID, 0, "r1", json.dumps({"type": "session.started", "sessionId": SID})))
    conn.execute("INSERT INTO trajectory_runtime_events VALUES (?,?,?,?,0)", (
        SID, 1, "r1", json.dumps({"type": "context.compiled", "sessionId": SID,
                                  "seq": 2, "ts": "2026-10-01T22:24:00Z"})))
    conn.commit()
    conn.close()
    monkeypatch.setattr(ocs, "mirror_root", lambda: tmp_path / "mirror")
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(oc))
    ocs._fingerprints.clear()
    return oc


def _lines(path: Path) -> list:
    return [json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()]


def _ids(path: Path) -> list:
    return [e["id"] for e in _lines(path)]


def test_mirror_writes_transcript_index_and_context(openclaw_home):
    _add_events(ocs.agent_db_path(openclaw_home),
                [_event(0), _event(1, "assistant")])
    out = Path(ocs.sync_mirror(openclaw_home, {}))
    transcript = out / f"{SID}.jsonl"

    assert _ids(transcript) == ["ev-0", "ev-1"]
    # Pure ASCII on disk: the JSONL readers open with the platform encoding.
    assert transcript.read_bytes().isascii()
    assert _lines(transcript)[0]["message"]["content"].endswith("héllo")

    index = json.loads((out / "sessions.json").read_text(encoding="utf-8"))
    entry = index["agent:main:main"]
    assert entry["sessionId"] == SID
    assert entry["model"] == "gpt-6-astra"  # filled from session_windows
    assert entry["sessionFile"].endswith(f"{SID}.jsonl")

    # Only context.compiled is mirrored out of the trajectory table.
    traj = _lines(out / f"{SID}.trajectory.jsonl")
    assert [t["type"] for t in traj] == ["context.compiled"]
    # Re-keyed on the table's per-session seq: the event's own seq restarts
    # every run, which would collapse every context row onto one event id.
    assert traj[0]["seq"] == 1


def test_mirror_is_append_only_across_passes(openclaw_home):
    db = ocs.agent_db_path(openclaw_home)
    _add_events(db, [_event(0), _event(1, "assistant")])
    state: dict = {}
    out = Path(ocs.sync_mirror(openclaw_home, state))
    ocs.sync_mirror(openclaw_home, state)  # no-op pass
    assert len(_lines(out / f"{SID}.jsonl")) == 2

    _add_events(db, [_event(2)], start=2)
    ocs._fingerprints.clear()
    ocs.sync_mirror(openclaw_home, state)
    assert _ids(out / f"{SID}.jsonl") == ["ev-0", "ev-1", "ev-2"]


def test_uncompressed_2026_9_3_schema_mirrors_without_optional_zstd_column(openclaw_home):
    db = ocs.agent_db_path(openclaw_home)
    with sqlite3.connect(db) as conn:
        conn.execute("ALTER TABLE transcript_events DROP COLUMN event_zstd")
    _add_events(db, [_event(0), _event(1, "assistant")])
    state = {}
    out = Path(ocs.sync_mirror(openclaw_home, state))
    assert _ids(out / f"{SID}.jsonl") == ["ev-0", "ev-1"]
    ocs._fingerprints.clear()
    ocs.sync_mirror(openclaw_home, state)
    assert _ids(out / f"{SID}.jsonl") == ["ev-0", "ev-1"]


def test_rewritten_transcript_never_duplicates_lines(openclaw_home):
    db = ocs.agent_db_path(openclaw_home)
    _add_events(db, [_event(0), _event(1, "assistant"), _event(2)])
    state: dict = {}
    out = Path(ocs.sync_mirror(openclaw_home, state))

    # OpenClaw compacts: drops ev-1, renumbers, appends ev-3.
    conn = sqlite3.connect(db)
    conn.execute("DELETE FROM transcript_events")
    conn.execute("DELETE FROM transcript_event_identities")
    conn.commit()
    conn.close()
    _add_events(db, [_event(0), _event(2), _event(3, "assistant")])
    ocs._fingerprints.clear()
    ocs.sync_mirror(openclaw_home, state)

    assert _ids(out / f"{SID}.jsonl") == ["ev-0", "ev-1", "ev-2", "ev-3"]


def test_undecodable_zstd_event_stalls_instead_of_skipping(openclaw_home, monkeypatch):
    db = ocs.agent_db_path(openclaw_home)
    _add_events(db, [_event(0)])
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO transcript_events (session_id, seq, event_zstd,"
                 " created_at) VALUES (?,?,?,0)", (SID, 1, b"\x28\xb5\x2f\xfd"))
    conn.commit()
    conn.close()
    _add_events(db, [_event(2)], start=2)
    monkeypatch.setattr(ocs, "_zstd_decompress", lambda blob: None)
    state: dict = {}
    out = Path(ocs.sync_mirror(openclaw_home, state))
    assert _ids(out / f"{SID}.jsonl") == ["ev-0"]

    # Decoder shows up: the session resumes at the compressed event, in order.
    monkeypatch.setattr(ocs, "_zstd_decompress",
                        lambda blob: json.dumps(_event(1, "assistant")).encode())
    ocs.sync_mirror(openclaw_home, state)
    assert _ids(out / f"{SID}.jsonl") == ["ev-0", "ev-1", "ev-2"]


def test_no_sqlite_store_returns_none(tmp_path):
    assert ocs.sync_mirror(tmp_path / "nope", {}) is None


def test_sessions_dir_prefers_live_jsonl_over_mirror(openclaw_home):
    from clawmetry import sync
    legacy = openclaw_home / "agents" / "main" / "sessions"
    _add_events(ocs.agent_db_path(openclaw_home), [_event(0)])

    paths = {"sessions_dir": str(legacy)}
    got = sync._openclaw_sessions_dir(paths, {})
    assert Path(got) == ocs.mirror_sessions_dir()
    assert paths["sessions_dir"] == got
    # Without state: plain lookup, same answer, no DB work.
    assert sync._openclaw_sessions_dir() == got

    # An install still writing .jsonl keeps using the real directory.
    (legacy / "live.jsonl").write_text("{}\n")
    assert sync._openclaw_sessions_dir(paths, {}) == str(legacy)
    assert paths["sessions_dir"] == str(legacy)


def test_sync_sessions_ingests_sqlite_transcripts(openclaw_home, monkeypatch):
    from clawmetry import sync
    _add_events(ocs.agent_db_path(openclaw_home),
                [_event(0), _event(1, "assistant")])
    flushed: list = []
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(
        sync, "_flush_session_batch",
        lambda batch, fname, *a, **k: flushed.append((fname, list(batch))))
    monkeypatch.setattr(sync, "_sync_trajectory_context", lambda *a, **k: 0)

    paths = {"sessions_dir": str(openclaw_home / "agents" / "main" / "sessions")}
    state: dict = {}
    config = {"api_key": "k", "node_id": "n"}
    assert sync.sync_sessions(config, state, paths) == 2
    assert flushed[0][0] == f"{SID}.jsonl"
    assert [e["id"] for e in flushed[0][1]] == ["ev-0", "ev-1"]
    # Second cycle: cursor held, nothing re-sent.
    assert sync.sync_sessions(config, state, paths) == 0


def test_mirror_reads_a_store_without_event_zstd(openclaw_home_pre_zstd):
    """2026.9.2 (agent schema 19) has no transcript_events.event_zstd.

    The column arrived with 2026.9.6 / schema 23. Selecting it from an
    older store raised ``no such column: event_zstd``, sync_mirror caught
    that and returned None, and the whole mirror came out empty on exactly
    the version ``.github/actions/setup-openclaw`` pins.
    """
    db = ocs.agent_db_path(openclaw_home_pre_zstd)
    cols = {
        row[1]
        for row in sqlite3.connect(db).execute(
            "PRAGMA table_info(transcript_events)")
    }
    assert "event_zstd" not in cols, (
        "fixture no longer models the pre-2026.9.6 schema; this test would "
        "pass vacuously"
    )

    _add_events(db, [_event(0), _event(1, "assistant")])
    out = ocs.sync_mirror(openclaw_home_pre_zstd, {})
    assert out is not None, "mirror pass gave up on a store it can read"
    assert _ids(Path(out) / f"{SID}.jsonl") == ["ev-0", "ev-1"]
    index = json.loads(
        (Path(out) / "sessions.json").read_text(encoding="utf-8"))
    assert index["agent:main:main"]["sessionId"] == SID


def test_session_header_cwd_reaches_the_sessions_row(openclaw_home, monkeypatch, tmp_path):
    """OpenClaw records a session's working directory once, on the v4
    ``{"type": "session", ..., "cwd": ...}`` header that opens every
    transcript (clawmetry-pro#228). The mirror must keep that line and the
    local ingest must harvest it into ``sessions.cwd``, or OpenClaw sessions
    stay a wall of UUIDs with no workspace scan."""
    import importlib

    from clawmetry import sync

    header = {"type": "session", "version": 4, "id": SID,
              "timestamp": "2026-10-01T22:23:59.000Z",
              "cwd": "/Users/test/.openclaw/workspace"}
    _add_events(ocs.agent_db_path(openclaw_home),
                [header, _event(0), _event(1, "assistant")])

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    store = ls.get_store()

    flushed: list = []
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(
        sync, "_flush_session_batch",
        lambda batch, fname, *a, **k: flushed.append((fname, list(batch))))
    monkeypatch.setattr(sync, "_sync_trajectory_context", lambda *a, **k: 0)
    paths = {"sessions_dir": str(openclaw_home / "agents" / "main" / "sessions")}
    assert sync.sync_sessions({"api_key": "k", "node_id": "n"}, {}, paths) == 3

    fname, batch = flushed[0]
    # The mirror kept the header as the first line of the transcript.
    assert batch[0]["type"] == "session"
    assert batch[0]["cwd"] == "/Users/test/.openclaw/workspace"

    # The sessions row itself comes from sessions.json (no cwd there); the
    # transcript ingest fills the location in afterwards.
    store.ingest_sessions_batch([{"agent_type": "openclaw", "session_id": SID,
                                  "node_id": "n", "status": "done"}])
    sync._local_ingest_session_batch(batch, fname, "n", None)
    row = next(r for r in store.query_sessions_table(limit=50)
               if r.get("session_id") == SID)
    assert row.get("cwd") == "/Users/test/.openclaw/workspace"
