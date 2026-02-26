-- ClawMetry Turso Schema
-- Run this against your Turso database to set up cloud persistence.
-- Example: turso db shell <dbname> < turso_schema.sql

-- ── Nodes ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nodes (
    node_id      TEXT PRIMARY KEY,
    name         TEXT,
    hostname     TEXT,
    version      TEXT,
    tags         TEXT DEFAULT '[]',
    status       TEXT DEFAULT 'online',
    registered_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    last_seen_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    metadata     TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_nodes_last_seen ON nodes (last_seen_at);

-- ── Metrics ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metrics (
    id          TEXT DEFAULT (LOWER(HEX(RANDOMBLOB(16)))) PRIMARY KEY,
    node_id     TEXT,
    metric_name TEXT,
    value       REAL,
    attributes  TEXT DEFAULT '{}',
    ts          TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics (ts);
CREATE INDEX IF NOT EXISTS idx_metrics_node_id ON metrics (node_id);

-- ── Events ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          TEXT DEFAULT (LOWER(HEX(RANDOMBLOB(16)))) PRIMARY KEY,
    node_id     TEXT,
    event_type  TEXT,
    session_id  TEXT,
    data        TEXT DEFAULT '{}',
    ts          TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events (ts);
CREATE INDEX IF NOT EXISTS idx_events_node_id ON events (node_id);

-- ── Sessions ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    node_id      TEXT,
    session_id   TEXT,
    display_name TEXT,
    status       TEXT,
    model        TEXT,
    total_tokens INTEGER DEFAULT 0,
    cost_usd     REAL DEFAULT 0,
    started_at   TEXT,
    updated_at   TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (node_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions (updated_at);
CREATE INDEX IF NOT EXISTS idx_sessions_node_id ON sessions (node_id);

-- ── 7-day auto-cleanup ────────────────────────────────────────────────
-- Turso doesn't have built-in cron. Options:
-- 1. Run this SQL periodically via an external cron job or GitHub Action:
--    DELETE FROM metrics WHERE ts < datetime('now', '-7 days');
--    DELETE FROM events WHERE ts < datetime('now', '-7 days');
--    DELETE FROM sessions WHERE updated_at < datetime('now', '-7 days');
-- 2. ClawMetry's health-check mechanism can trigger cleanup automatically.
