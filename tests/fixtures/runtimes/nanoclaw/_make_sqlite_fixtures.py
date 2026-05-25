"""Generate NanoClaw SQLite fixtures for the adapter tests.

Materialises a realistic ``data/v2-sessions/<group>/<session>/`` tree with
``inbound.db`` + ``outbound.db`` matching NanoClaw's real schema (captured
from github.com/nanocoai/nanoclaw src/db/schema.ts):

  inbound.db   -> messages_in, delivered, destinations, session_routing
  outbound.db  -> messages_out, processing_ack, session_state, container_state

We populate the message tables with a minimal, ordered conversation:
  seq 0 (inbound, kind=chat)   user: "ship the nanoclaw adapter"
  seq 1 (outbound, kind=chat-sdk) assistant reply (in_reply_to the user msg)
  seq 2 (inbound, kind=chat)   user follow-up
  seq 3 (outbound, kind=system) a system message

``seq`` is unique within the session ACROSS both tables (host=even,
container=odd), so merge-sorting by seq reconstructs the transcript.

Run directly to regenerate the committed .db files:

    python3 tests/fixtures/runtimes/nanoclaw/_make_sqlite_fixtures.py

Both this generator and the generated .db files are committed: the .db
files let tests run without a build step, and this file documents the
exact on-disk shape the adapter parses.
"""
from __future__ import annotations

import json
import os
import sqlite3

# ── real NanoClaw schema (src/db/schema.ts) ──────────────────────────────

INBOUND_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages_in (
  id             TEXT PRIMARY KEY,
  seq            INTEGER UNIQUE,
  kind           TEXT NOT NULL,
  timestamp      TEXT NOT NULL,
  status         TEXT DEFAULT 'pending',
  process_after  TEXT,
  recurrence     TEXT,
  series_id      TEXT,
  tries          INTEGER DEFAULT 0,
  trigger        INTEGER NOT NULL DEFAULT 1,
  platform_id    TEXT,
  channel_type   TEXT,
  thread_id      TEXT,
  content        TEXT NOT NULL,
  source_session_id TEXT,
  on_wake        INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS delivered (
  message_out_id      TEXT PRIMARY KEY,
  platform_message_id TEXT,
  status              TEXT NOT NULL DEFAULT 'delivered',
  delivered_at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS destinations (
  name            TEXT PRIMARY KEY,
  display_name    TEXT,
  type            TEXT NOT NULL,
  channel_type    TEXT,
  platform_id     TEXT,
  agent_group_id  TEXT
);
CREATE TABLE IF NOT EXISTS session_routing (
  id           INTEGER PRIMARY KEY CHECK (id = 1),
  channel_type TEXT,
  platform_id  TEXT,
  thread_id    TEXT
);
"""

OUTBOUND_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages_out (
  id             TEXT PRIMARY KEY,
  seq            INTEGER UNIQUE,
  in_reply_to    TEXT,
  timestamp      TEXT NOT NULL,
  deliver_after  TEXT,
  recurrence     TEXT,
  kind           TEXT NOT NULL,
  platform_id    TEXT,
  channel_type   TEXT,
  thread_id      TEXT,
  content        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS processing_ack (
  message_id     TEXT PRIMARY KEY,
  status         TEXT NOT NULL,
  status_changed TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_state (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS container_state (
  id                       INTEGER PRIMARY KEY CHECK (id = 1),
  current_tool             TEXT,
  tool_declared_timeout_ms INTEGER,
  tool_started_at          TEXT,
  updated_at               TEXT NOT NULL
);
"""

GROUP_ID = "default"
SESSION_ID = "sess-0001"

# RFC3339 timestamps, strictly increasing.
TS = [
    "2026-05-25T10:00:00.000Z",
    "2026-05-25T10:00:05.250Z",
    "2026-05-25T10:01:00.000Z",
    "2026-05-25T10:01:02.500Z",
]


def _build_inbound(path: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(INBOUND_SCHEMA)
        # seq 0: user chat (content is JSON with a text body)
        conn.execute(
            "INSERT INTO messages_in (id, seq, kind, timestamp, status, "
            "trigger, platform_id, channel_type, thread_id, content, on_wake) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "in-0",
                0,
                "chat",
                TS[0],
                "processed",
                1,
                "tg:42",
                "telegram",
                "t-1",
                json.dumps({"text": "ship the nanoclaw adapter"}),
                0,
            ),
        )
        # seq 2: user follow-up (content is a bare JSON string)
        conn.execute(
            "INSERT INTO messages_in (id, seq, kind, timestamp, status, "
            "trigger, platform_id, channel_type, thread_id, content, on_wake) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "in-2",
                2,
                "chat",
                TS[2],
                "processed",
                1,
                "tg:42",
                "telegram",
                "t-1",
                json.dumps("and write the tests too"),
                0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _build_outbound(path: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(OUTBOUND_SCHEMA)
        # seq 1: assistant chat-sdk reply, in_reply_to the user's first msg
        conn.execute(
            "INSERT INTO messages_out (id, seq, in_reply_to, timestamp, kind, "
            "platform_id, channel_type, thread_id, content) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "out-1",
                1,
                "in-0",
                TS[1],
                "chat-sdk",
                "tg:42",
                "telegram",
                "t-1",
                json.dumps({"text": "on it - adapter coming up"}),
            ),
        )
        # seq 3: system message
        conn.execute(
            "INSERT INTO messages_out (id, seq, in_reply_to, timestamp, kind, "
            "platform_id, channel_type, thread_id, content) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "out-3",
                3,
                None,
                TS[3],
                "system",
                "tg:42",
                "telegram",
                "t-1",
                json.dumps({"text": "session compacted"}),
            ),
        )
        # session_state KV (no model/token/cost data lives here either)
        conn.execute(
            "INSERT INTO session_state (key, value, updated_at) VALUES (?, ?, ?)",
            ("turn_count", "2", TS[3]),
        )
        conn.commit()
    finally:
        conn.close()


def make_fixtures(base_dir: str | None = None) -> str:
    """Create the fixture tree under *base_dir* and return the v2-sessions root."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = base_dir or os.path.join(here, "data", "v2-sessions")
    session_dir = os.path.join(root, GROUP_ID, SESSION_ID)
    os.makedirs(session_dir, exist_ok=True)
    inbound = os.path.join(session_dir, "inbound.db")
    outbound = os.path.join(session_dir, "outbound.db")
    # Regenerate cleanly.
    for p in (inbound, outbound):
        if os.path.exists(p):
            os.remove(p)
    _build_inbound(inbound)
    _build_outbound(outbound)
    return root


if __name__ == "__main__":
    out = make_fixtures()
    print(f"NanoClaw fixtures written under: {out}")
    for dirpath, _dirs, files in os.walk(out):
        for f in sorted(files):
            print(f"  {os.path.join(dirpath, f)}")
