# NanoClaw REAL session SQLite captures

Captured: 2026-05-25T08:12:06Z
Source: github.com/nanocoai/nanoclaw @ cabc7c0f82ed08a85f763eaa063f162abdc1fa1c (package version 2.0.69)
Created by NanoClaw's OWN runtime code: src/db/session-db.ts ensureSchema()/insertMessage()
  compiled to dist/ via 'npm run build' (tsc), better-sqlite3 11.10.0.
Outbound rows replicate container src/db/messages-out.ts writeMessageOut() (identical SQL + OUTBOUND_SCHEMA).

Layout: <agent_group_id>/<session_id>/{inbound.db,outbound.db}
Real data_dir resolution: path.resolve(process.cwd(),'data')/v2-sessions  (CWD-relative; NO env override).

## inbound.db .schema
```sql
CREATE TABLE messages_in (
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
                 -- 0 = accumulated context (don't wake), 1 = wake agent
  platform_id    TEXT,
  channel_type   TEXT,
  thread_id      TEXT,
  content        TEXT NOT NULL,
  -- For agent-to-agent inbound rows: the source session that emitted the
  -- triggering outbound. Used as a return path when the target replies —
  -- the reply routes back to this exact session, not to the source agent
  -- group's "newest" session. NULL on channel-side inbound and on a2a rows
  -- written before this column existed.
  source_session_id TEXT,
  on_wake        INTEGER NOT NULL DEFAULT 0
               -- 1 = only deliver on the container's first poll (fresh start).
               -- Dying containers (past first poll) skip these rows.
);
CREATE INDEX idx_messages_in_series ON messages_in(series_id);
CREATE TABLE delivered (
  message_out_id      TEXT PRIMARY KEY,
  platform_message_id TEXT,
  status              TEXT NOT NULL DEFAULT 'delivered',
  delivered_at        TEXT NOT NULL
);
CREATE TABLE destinations (
  name            TEXT PRIMARY KEY,
  display_name    TEXT,
  type            TEXT NOT NULL,   -- 'channel' | 'agent'
  channel_type    TEXT,            -- for type='channel'
  platform_id     TEXT,            -- for type='channel'
  agent_group_id  TEXT             -- for type='agent'
);
CREATE TABLE session_routing (
  id           INTEGER PRIMARY KEY CHECK (id = 1),
  channel_type TEXT,
  platform_id  TEXT,
  thread_id    TEXT
);
```

## outbound.db .schema
```sql
CREATE TABLE messages_out (
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
CREATE TABLE processing_ack (
  message_id     TEXT PRIMARY KEY,
  status         TEXT NOT NULL,
  status_changed TEXT NOT NULL
);
CREATE TABLE session_state (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE container_state (
  id                       INTEGER PRIMARY KEY CHECK (id = 1),
  current_tool             TEXT,
  tool_declared_timeout_ms INTEGER,
  tool_started_at          TEXT,
  updated_at               TEXT NOT NULL
);
```

## USAGE ON DISK: NONE.
messages_in / messages_out have NO model/token/cost columns. The Agent SDK
transcript .jsonl (which carries usage) lives INSIDE the container at
$HOME/.claude/projects/<dir>/<sessionId>.jsonl and is archived-to-markdown
then rotated/deleted; it is NOT on the host-visible session dir. claude.ts
translateEvents() reads only result.text + session_id and discards usage/cost.
