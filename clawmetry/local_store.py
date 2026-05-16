"""Local DuckDB event store — Phase 1 of the local-first refactor (#964).

Switched from SQLite to DuckDB (decision: 2026-05-11). Same public API; the
durability + concurrency model differs (DuckDB MVCC instead of SQLite WAL),
but the surface — ``ingest()``, ``query_events()``, ``query_sessions()``,
``query_aggregates()``, ``health()``, ``vacuum()`` — is unchanged.

Why DuckDB:
* Columnar storage → analytical queries (GROUP BY, time-window aggregates,
  per-tool/per-session/per-day rollups) run an order of magnitude faster than
  on SQLite. The dashboard's Brain/Tokens/Sessions tabs are exactly that
  shape of workload.
* Native Parquet and CSV I/O — future cheap archival + ad-hoc export are a
  one-liner, not a library swap.
* Time-series-friendly query patterns become first-class.
* Trade-off: a real wheel dependency (~14 MB) instead of stdlib sqlite3.
  Considered acceptable: the analytical advantages compound as the local
  store accrues months of data.

NOT in this module (deliberately):
* Network — there is no HTTP server here. Adding endpoints is a follow-up
  blueprint.
* Encryption — events are stored plaintext locally. Cloud sync continues
  to do its own E2E encryption pass before POSTing.
* Cloud sync — independent. Adding the local store does not change what
  ``sync.py`` ships.

Concurrency model:
* DuckDB connections are heavyweight; we keep a process-wide singleton
  connection guarded by a ``threading.Lock`` for writes. Reads are issued
  via ``.cursor()`` instances which are thread-safe.
* DuckDB allows only one *writer* process per file; multiple *readers* are
  allowed. The daemon process owns the writer; future external readers
  (e.g. a separate dashboard process per #960) will open with
  ``read_only=True``.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

import duckdb

log = logging.getLogger("clawmetry.local_store")


# Public knobs — tuned for the common case (one daemon, one dashboard, ≤1 K
# events/s sustained on a developer laptop). Adjust via env vars only.

# Naming history:
#   0.12.164  → events.db    (SQLite — replaced by DuckDB the same release)
#   0.12.165  → events.duckdb (DuckDB; name implied "only events" but we
#                              also store sessions, memory_blobs, heartbeats,
#                              system_snapshots, spans, etc. in this same DB)
#   0.12.166+ → clawmetry.duckdb (the all-up local store for whatever
#                                 ClawMetry needs across multi-agent
#                                 frameworks — past + future tables)
#
# Compatibility: if a user has an existing events.duckdb but no
# clawmetry.duckdb, the next start renames it in place. Lossless,
# no schema change. See _migrate_legacy_db_path() below.
DB_PATH = Path(
    os.environ.get(
        "CLAWMETRY_LOCAL_STORE_PATH",
        os.path.expanduser("~/.clawmetry/clawmetry.duckdb"),
    )
)
LEGACY_DB_PATH = Path(os.path.expanduser("~/.clawmetry/events.duckdb"))


def _migrate_legacy_db_path() -> None:
    """If the old events.duckdb exists and the new clawmetry.duckdb doesn't,
    rename in place. Single os.rename — atomic on POSIX. Safe to call on
    every start; no-op when there's nothing to migrate.

    We intentionally DON'T touch the legacy file when the new name already
    exists (would lose data) and DON'T touch CLAWMETRY_LOCAL_STORE_PATH-
    overridden paths (test fixtures, custom installs)."""
    if "CLAWMETRY_LOCAL_STORE_PATH" in os.environ:
        return  # Custom path; user knows what they're doing.
    if not LEGACY_DB_PATH.exists():
        return
    if DB_PATH.exists():
        # Both files present — keep the new one as live. Don't clobber.
        log.info("local store: legacy events.duckdb still present alongside "
                 "clawmetry.duckdb. Keeping clawmetry.duckdb; old file "
                 "untouched (delete manually if you want to reclaim space).")
        return
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_DB_PATH.rename(DB_PATH)
        # Move the WAL too so DuckDB recovers cleanly on first open.
        legacy_wal = LEGACY_DB_PATH.with_suffix(LEGACY_DB_PATH.suffix + ".wal")
        new_wal = DB_PATH.with_suffix(DB_PATH.suffix + ".wal")
        if legacy_wal.exists() and not new_wal.exists():
            legacy_wal.rename(new_wal)
        log.info("local store: migrated legacy %s → %s",
                 LEGACY_DB_PATH.name, DB_PATH.name)
    except OSError as e:
        log.warning("local store: failed to migrate legacy %s → %s: %s. "
                    "Will create a fresh clawmetry.duckdb; old file "
                    "untouched.", LEGACY_DB_PATH.name, DB_PATH.name, e)

FLUSH_INTERVAL_SECS = float(os.environ.get("CLAWMETRY_LOCAL_FLUSH_SECS", "2.0"))
FLUSH_BATCH = int(os.environ.get("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000"))
RING_MAX = int(os.environ.get("CLAWMETRY_LOCAL_RING_MAX", "10000"))
LOCAL_MAX_BYTES = int(
    float(os.environ.get("CLAWMETRY_LOCAL_MAX_GB", "5.0")) * 1024 * 1024 * 1024
)

SCHEMA_VERSION = 7

# ── Two-layer schema (multi-agent) ──────────────────────────────────────────
#
# Layer 1: shared core. Every agent (OpenClaw, Claude Code, Hermes, Cursor,
# Codex, Aider, …) writes here. `agent_type` is the discriminator.
#
# Layer 2: agent-specific extensions. Only added when a concept is unique to
# one agent OR shared by 2+. Keeps the columnar tables clean of NULL columns
# we'd otherwise carry to support every framework's quirks.
#
# Discriminator: `agent_type` is the FRAMEWORK (openclaw/claude_code/hermes/
# cursor/codex/aider). `agent_id` (already on events) is the INSTANCE within
# that framework (main/subagent/cron). Both coexist.

_DDL = [
    # ── Layer 1: shared core ─────────────────────────────────────────────────
    """
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
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_ts          ON events(ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_session     ON events(session_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_agent_ts    ON events(agent_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_type_ts     ON events(event_type, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_atype_ts    ON events(agent_type, ts)",
    # Speeds up the v7 dedup migration (#1232) and any future analytical
    # query that wants to scan a single session's timeline by event_type
    # without hitting the full ts index.
    "CREATE INDEX IF NOT EXISTS idx_events_session_ts_type ON events(session_id, ts, event_type)",
    """
    CREATE TABLE IF NOT EXISTS sessions (
        agent_type      VARCHAR NOT NULL DEFAULT 'openclaw',
        session_id      VARCHAR NOT NULL,
        node_id         VARCHAR,
        agent_id        VARCHAR DEFAULT 'main',
        workspace_id    VARCHAR,
        title           VARCHAR,
        started_at      VARCHAR,
        last_active_at  VARCHAR,
        ended_at        VARCHAR,
        status          VARCHAR,
        total_tokens    INTEGER DEFAULT 0,
        cost_usd        DOUBLE DEFAULT 0,
        message_count   INTEGER DEFAULT 0,
        metadata        BLOB,
        updated_at      BIGINT NOT NULL,
        PRIMARY KEY (agent_type, session_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_sessions_active    ON sessions(agent_type, last_active_at)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_node      ON sessions(node_id, last_active_at)",
    """
    CREATE TABLE IF NOT EXISTS daily_aggregates (
        agent_type    VARCHAR NOT NULL DEFAULT 'openclaw',
        agent_id      VARCHAR NOT NULL,
        workspace_id  VARCHAR,
        day           VARCHAR NOT NULL,
        cost_usd      DOUBLE DEFAULT 0,
        token_count   INTEGER DEFAULT 0,
        event_count   INTEGER DEFAULT 0,
        error_count   INTEGER DEFAULT 0,
        PRIMARY KEY (agent_type, agent_id, workspace_id, day)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_blobs (
        agent_type    VARCHAR NOT NULL,
        agent_id      VARCHAR NOT NULL DEFAULT 'main',
        path          VARCHAR NOT NULL,
        ts            VARCHAR,
        blob          BLOB,
        sha256        VARCHAR,
        size_bytes    INTEGER,
        updated_at    BIGINT NOT NULL,
        PRIMARY KEY (agent_type, agent_id, path)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS heartbeats (
        agent_type        VARCHAR NOT NULL DEFAULT 'openclaw',
        node_id           VARCHAR NOT NULL,
        ts                VARCHAR NOT NULL,
        version           VARCHAR,
        e2e               BOOLEAN,
        size_mb           DOUBLE,
        events_total      INTEGER,
        data              BLOB,
        PRIMARY KEY (agent_type, node_id, ts)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_heartbeats_node_ts ON heartbeats(node_id, ts)",
    """
    CREATE TABLE IF NOT EXISTS system_snapshots (
        agent_type    VARCHAR NOT NULL DEFAULT 'openclaw',
        node_id       VARCHAR NOT NULL,
        ts            VARCHAR NOT NULL,
        kind          VARCHAR NOT NULL,
        data          BLOB,
        PRIMARY KEY (agent_type, node_id, ts, kind)
    )
    """,
    # ── Layer 2: agent-specific extensions ───────────────────────────────────
    # OpenClaw-only: channel context (Telegram/Slack/...). Other agents don't
    # have this; keeping it out of `sessions` avoids 5 NULL columns per row.
    """
    CREATE TABLE IF NOT EXISTS openclaw_channels (
        session_id    VARCHAR PRIMARY KEY,
        channel       VARCHAR,
        chat_type     VARCHAR,
        subject       VARCHAR,
        origin_label  VARCHAR
    )
    """,
    # Epic #1032 Phase 5: channel adapter CONFIG (distinct from
    # openclaw_channels above, which is per-session channel METADATA).
    # One row per provider (telegram, slack, signal, discord, ...). The
    # blob is the E2E-encrypted adapter config (bot tokens, OAuth secrets,
    # phone numbers, etc.) — cloud never sees plaintext. Status fields
    # (enabled, last_test_at, last_test_ok) are non-secret summaries that
    # the cloud UI can render after a cache_push.
    """
    CREATE TABLE IF NOT EXISTS channel_config (
        provider               VARCHAR PRIMARY KEY,
        enabled                BOOLEAN DEFAULT FALSE,
        config_json_encrypted  BLOB,
        last_test_at           VARCHAR,
        last_test_ok           BOOLEAN,
        last_test_error        VARCHAR,
        updated_at             VARCHAR
    )
    """,
    # Shared by OpenClaw + Hermes (and any future cron-supporting agent).
    """
    CREATE TABLE IF NOT EXISTS crons (
        agent_type     VARCHAR NOT NULL,
        cron_id        VARCHAR NOT NULL,
        agent_id       VARCHAR DEFAULT 'main',
        name           VARCHAR,
        schedule       VARCHAR,
        enabled        BOOLEAN,
        last_run_at    VARCHAR,
        last_status    VARCHAR,
        next_run_at    VARCHAR,
        data           BLOB,
        updated_at     BIGINT NOT NULL,
        PRIMARY KEY (agent_type, cron_id)
    )
    """,
    # Phase 3 of #1032 — alert rules. Authored in the cloud UI, relayed to the
    # local DuckDB via heartbeat-piggyback, then read by the in-process alert
    # evaluator. owner_hash binds each rule to the cm_ token that owns it
    # (sha256 of the token, matching the cloud-side _owner_hash_for helper).
    # condition_json is the rule body (threshold, alert_type, channel_ids,
    # etc.) serialized exactly as cloud stores it — keeping the local store
    # opaque to schema drift on the cloud's `alerts` table.
    """
    CREATE TABLE IF NOT EXISTS alert_rules (
        id              VARCHAR PRIMARY KEY,
        owner_hash      VARCHAR,
        name            VARCHAR,
        condition_json  BLOB,
        enabled         BOOLEAN DEFAULT TRUE,
        created_at      VARCHAR,
        updated_at      VARCHAR,
        last_fired_at   VARCHAR,
        fire_count      INTEGER DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_alert_rules_owner ON alert_rules(owner_hash, enabled)",
    # Shared by OpenClaw subagents + Claude Code Task tool.
    """
    CREATE TABLE IF NOT EXISTS subagents (
        agent_type        VARCHAR NOT NULL,
        subagent_id       VARCHAR NOT NULL,
        parent_session_id VARCHAR,
        spawned_at        VARCHAR,
        ended_at          VARCHAR,
        task              VARCHAR,
        status            VARCHAR,
        cost_usd          DOUBLE DEFAULT 0,
        token_count       INTEGER DEFAULT 0,
        data              BLOB,
        updated_at        BIGINT NOT NULL,
        PRIMARY KEY (agent_type, subagent_id)
    )
    """,
    # Epic #1032 Phase 4 — approval queue. Authored locally when the policy
    # watcher fires on a tool-call, mirrored to the cloud cache via heartbeat
    # cache_push so the cloud Approvals inbox paints from cache, and resolved
    # via the heartbeat-piggyback pending_queries channel (cloud → node).
    # DuckDB is authoritative; Cloud SQL row is no longer written. owner_hash
    # binds each request to the cm_ token that owns it (sha256 of the token,
    # matching the cloud-side _owner_hash_for helper). `args` is the encoded
    # toolCall arguments — stored as BLOB so we don't drag a JSONB-style
    # schema bump through here when callers stuff arbitrary dicts in.
    """
    CREATE TABLE IF NOT EXISTS approvals (
        id                     VARCHAR PRIMARY KEY,
        owner_hash             VARCHAR,
        requestor_session_id   VARCHAR,
        action                 VARCHAR,
        args                   BLOB,
        status                 VARCHAR NOT NULL DEFAULT 'pending',
        created_at             VARCHAR,
        resolved_at            VARCHAR,
        resolver               VARCHAR,
        decision               VARCHAR,
        decision_reason        VARCHAR
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_approvals_owner_status ON approvals(owner_hash, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_approvals_session ON approvals(requestor_session_id, created_at)",
    # Issue #1088 Phase 4 (2026-05-13) — channel-message foundation. Replaces
    # the per-provider log-grep + JSONL-scan path that the 21 routes in
    # ``routes/channels.py`` use today. Each row is one inbound or outbound
    # message on a chat-channel adapter (Telegram, Signal, WhatsApp, Discord,
    # Slack, IRC, iMessage, WebChat, …). Schema is provider-agnostic — the
    # ``provider`` column discriminates and ``raw_blob`` carries the
    # adapter-specific payload (attachments, message_id, sender metadata) so
    # we don't need a per-provider column carry. Only 3 providers will land
    # fast-paths in this PR; the remaining 18 follow once the schema proves
    # out (see issue #1088 follow-up).
    """
    CREATE TABLE IF NOT EXISTS channel_messages (
        id            VARCHAR PRIMARY KEY,
        agent_id      VARCHAR NOT NULL DEFAULT 'main',
        provider      VARCHAR NOT NULL,
        channel_id    VARCHAR,
        sender_id     VARCHAR,
        sender_name   VARCHAR,
        body          VARCHAR,
        ts            VARCHAR NOT NULL,
        direction     VARCHAR NOT NULL,
        session_key   VARCHAR,
        raw_blob      BLOB,
        created_at    BIGINT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_chmsg_provider_ts  ON channel_messages(provider, ts)",
    "CREATE INDEX IF NOT EXISTS idx_chmsg_channel_ts   ON channel_messages(provider, channel_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_chmsg_session      ON channel_messages(session_key, ts)",
    # Issue #951 (2026-05-13) — per-agent budget overrides. One row per
    # agent_id with a daily and/or monthly USD limit. If a row is missing
    # for a given agent_id the global ``budget_config`` (daily/monthly_limit)
    # applies. The dashboard's ``_budget_check`` reads this table on every
    # cost-entry append and fires tiered alerts (80% warning, 100% critical)
    # against the matching per-agent limit, falling back to global only when
    # there is no override. Either limit column may be NULL — that side then
    # falls back to global independently (e.g. you can set a daily limit
    # without committing to a monthly one).
    """
    CREATE TABLE IF NOT EXISTS agent_budgets (
        agent_id          VARCHAR PRIMARY KEY,
        daily_limit_usd   DOUBLE,
        monthly_limit_usd DOUBLE,
        updated_at        BIGINT NOT NULL
    )
    """,
    # Issue #605 follow-up (DuckDB-first rule) — cron-run timeline storage.
    # One row per JSONL line in ``~/.openclaw/cron/runs/<jobId>.jsonl``. The
    # daemon's ``sync_cron_runs`` helper scans those files every cycle and
    # upserts rows here so ``/api/crons/<jobId>/runs`` can read from the
    # columnar store instead of re-parsing JSONL on every request.
    #
    # Schema rationale: we keep a dedicated table (not ``events``) because
    # ``delivered_at`` / ``next_run_at`` are first-class columns and the
    # cron-timeline UI's filter + sort patterns
    # (``WHERE job_id=? ORDER BY started_at DESC``) want a primary-key prefix
    # match, not a substring scan over ``data`` blobs. ``id`` is the dedup
    # key — synthesised from ``job_id + ts`` when the JSONL doesn't include
    # one, so re-ingestion of the same line is a no-op.
    """
    CREATE TABLE IF NOT EXISTS cron_runs (
        id              VARCHAR PRIMARY KEY,
        node_id         VARCHAR,
        agent_type      VARCHAR NOT NULL DEFAULT 'openclaw',
        agent_id        VARCHAR NOT NULL DEFAULT 'main',
        job_id          VARCHAR NOT NULL,
        started_at      VARCHAR,
        ended_at        VARCHAR,
        duration_ms     INTEGER,
        status          VARCHAR,
        error_message   VARCHAR,
        token_count     INTEGER,
        cost_usd        DOUBLE,
        delivered_at    VARCHAR,
        next_run_at     VARCHAR,
        raw_jsonl_line  VARCHAR,
        data            BLOB,
        created_at      BIGINT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_cron_runs_job_id     ON cron_runs(job_id, started_at)",
    "CREATE INDEX IF NOT EXISTS idx_cron_runs_started_at ON cron_runs(started_at)",
    # Issue #690 — "First Contact" bootstrap archive. OpenClaw's BOOTSTRAP.md
    # runs once at first startup to negotiate agent identity, then SELF-DELETES.
    # The capture helper in ``clawmetry/sync.py`` snapshots the file (and the
    # session id active at capture time) into this table BEFORE OpenClaw
    # removes it, so we keep a read-only "First Contact" artifact for the
    # life of the node. Dedup key is (node_id, agent_id, content_sha256) —
    # re-capture on unchanged content is a no-op, but a re-bootstrap with
    # different content lands as a fresh row so we preserve the full
    # first-contact history when OpenClaw re-negotiates identity.
    """
    CREATE TABLE IF NOT EXISTS bootstrap_archive (
        node_id           VARCHAR NOT NULL,
        agent_id          VARCHAR NOT NULL DEFAULT 'main',
        captured_at       VARCHAR NOT NULL,
        file_mtime        VARCHAR,
        content           VARCHAR,
        content_sha256    VARCHAR,
        first_session_id  VARCHAR,
        size_bytes        INTEGER,
        source_path       VARCHAR,
        PRIMARY KEY (node_id, agent_id, content_sha256)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_bootstrap_node ON bootstrap_archive(node_id, captured_at)",
    # Issue #1007 (Phase 1 of epic #1006) — OTel-compatible span storage.
    # One row per OTel span received via the /v1/traces OTLP receiver. Shape
    # mirrors the OpenTelemetry data model so any OTLP-emitting SDK (OpenAI,
    # Anthropic, LangChain, OpenClaw with OTel exporter, …) lands here
    # without a bespoke per-SDK translator. Follows the open OTel spec — not
    # a fork or wrapper of any vendor's code.
    #
    # Column-level rationale:
    #   * ``span_id`` is PK so re-delivery of the same OTel span (common with
    #     the OTLP HTTP exporter's retry-on-503 path) is a no-op via
    #     ``INSERT OR REPLACE``.
    #   * Time columns: ``start_ts`` / ``end_ts`` are DOUBLE unix-seconds
    #     (matches what OTel proto's ``start_time_unix_nano`` carries once
    #     converted). ``ts`` mirrors ``start_ts`` and is the canonical
    #     retention key for vacuum / range pruning — keeping it separate
    #     means we can someday store ``ts`` = ingest-time without breaking
    #     query semantics that key off span start.
    #   * Typed top-level columns (``model``, ``tool_name``, ``cost_usd``,
    #     ``tokens_input``, ``tokens_output``, ``token_count``) are
    #     projected from common OTel ``gen_ai.*`` attribute conventions in
    #     ``_otel_to_row`` (see dashboard.py) so the dashboard's usage views
    #     don't need to JSON-extract on every read.
    #   * BLOB columns (``input``, ``output``, ``attributes``, ``events``,
    #     ``links``) carry JSON-encoded values, decoded back on read.
    #     Matches the convention used by ``events.data`` / ``heartbeats.data``
    #     — see ``_decode_data_blob_rows`` for the symmetric decoder.
    #
    # Storage envelope (per epic #1006): ~70 spans/session × ~15 KB ≈
    # 1 MB/session. Heavy-user 50 sessions/day = ~50 MB/day, ~18 GB/year.
    # Mitigated by Snappy compression + opt-in ``clawmetry prune --spans``.
    """
    CREATE TABLE IF NOT EXISTS spans (
        span_id            VARCHAR PRIMARY KEY,
        trace_id           VARCHAR NOT NULL,
        parent_span_id     VARCHAR,
        agent_type         VARCHAR NOT NULL DEFAULT 'openclaw',
        agent_id           VARCHAR DEFAULT 'main',
        node_id            VARCHAR,
        session_id         VARCHAR,
        service_name       VARCHAR,
        name               VARCHAR NOT NULL,
        kind               VARCHAR,
        status_code        VARCHAR,
        status_message     VARCHAR,
        status             VARCHAR,
        start_ts           DOUBLE NOT NULL,
        end_ts             DOUBLE,
        duration_ms        DOUBLE,
        duration_ns        BIGINT,
        model              VARCHAR,
        tool_name           VARCHAR,
        cost_usd           DOUBLE,
        token_count        INTEGER,
        tokens_input       INTEGER,
        tokens_output      INTEGER,
        input              BLOB,
        output             BLOB,
        attributes         BLOB,
        events             BLOB,
        links              BLOB,
        ts                 DOUBLE NOT NULL,
        created_at         BIGINT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_spans_trace_id    ON spans(trace_id, span_id)",
    "CREATE INDEX IF NOT EXISTS idx_spans_trace_start ON spans(trace_id, start_ts)",
    "CREATE INDEX IF NOT EXISTS idx_spans_parent      ON spans(parent_span_id)",
    "CREATE INDEX IF NOT EXISTS idx_spans_session     ON spans(session_id, start_ts)",
    "CREATE INDEX IF NOT EXISTS idx_spans_agent_ts    ON spans(agent_type, start_ts)",
    "CREATE INDEX IF NOT EXISTS idx_spans_ts          ON spans(ts)",
    # Issue #1364 — loop-detection signals from clawmetry/proxy.py's
    # ``LoopDetector``. Today the detector logs + writes to its private
    # SQLite (``~/.clawmetry/proxy.db``); the dashboard had no view into
    # those events. Persisting them here surfaces capability 2.f
    # ("agent looping / stalling detection") in the Monte Carlo framework
    # via /api/loop-signals + the Brain tab badge.
    #
    # PK is (session_id, signature) so re-detection of the same loop in
    # the same session is an UPSERT (we keep the running ``repeat_count``
    # and update ``last_seen``). Different sessions hitting the same
    # signature are independent rows — looping is a per-session pathology.
    """
    CREATE TABLE IF NOT EXISTS loop_signals (
        session_id     VARCHAR NOT NULL,
        signature      VARCHAR NOT NULL,
        repeat_count   INTEGER NOT NULL DEFAULT 1,
        first_seen     TIMESTAMP NOT NULL,
        last_seen      TIMESTAMP NOT NULL,
        severity       VARCHAR DEFAULT 'warning',
        agent_type     VARCHAR DEFAULT 'openclaw',
        details        BLOB,
        PRIMARY KEY (session_id, signature)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_loop_signals_last_seen ON loop_signals(last_seen DESC)",
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version    INTEGER PRIMARY KEY,
        applied_at BIGINT NOT NULL
    )
    """,
]


# ── Schema migrations (v1 → v2) ────────────────────────────────────────────
#
# DuckDB doesn't support `ALTER TABLE ADD COLUMN IF NOT EXISTS` cleanly, so
# we check pg_tables-style introspection and run ALTERs only when needed.
# Idempotent: safe to call on a v2 store.

_MIGRATIONS_V2 = [
    # Existing 0.12.164 stores have `events` without agent_type — backfill it
    # to 'openclaw' (the only agent that wrote anything in v1).
    ("events", "agent_type", "VARCHAR DEFAULT 'openclaw'"),
    # daily_aggregates also gains agent_type. The PK change is the tricky part —
    # DuckDB won't let us alter the PK in place. v1 stores will keep their old
    # PK (agent_id, workspace_id, day); writes from v2 use ON CONFLICT DO
    # UPDATE on the PK that exists. New stores get the v2 PK directly.
    ("daily_aggregates", "agent_type", "VARCHAR DEFAULT 'openclaw'"),
]


def _apply_migrations(conn) -> None:
    """Add columns missing from a v1 store. Idempotent. Tolerant of
    tables not existing yet (fresh stores have nothing to migrate)."""
    # Get the set of tables that currently exist; skip migrations for any
    # table that doesn't.
    existing_tables = {
        row[0] for row in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
    }
    for table, col, decl in _MIGRATIONS_V2:
        if table not in existing_tables:
            continue
        existing_cols = {
            row[1] for row in conn.execute(
                f"PRAGMA table_info('{table}')"
            ).fetchall()
        }
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


# ── v7 dedup migration (#1232) ───────────────────────────────────────────────
#
# Three independent ingest paths used to write the same logical Claude Code
# event under three different ids (see ``_canonical_event_id`` in
# ``clawmetry/sync.py`` for the full diagnosis). The unified id derivation
# fixes future writes; this migration cleans the historical mess.
#
# Strategy: collapse rows that share ``(session_id, ts, event_type, dedup_key)``,
# where ``dedup_key`` is the underlying event uuid when extractable, or an
# MD5 of the body otherwise. We keep the smallest ``rowid`` per group. The
# rowid is opaque to DuckDB user-visible queries, but it's the only stable
# tie-breaker for "the row that was inserted first" — which is the right
# semantics here (preserve the original row, drop the later re-writes).
#
# The id-tail extraction handles all three id schemes the bug created:
#   bare 36-char uuid                            → uuid:<uuid>
#   openclaw-cc:<sess>:top:<uuid>                → uuid:<uuid>
#   openclaw-cc:<sess>:top:line:<N>              → body:<md5(data)>
#   <sess>:<ts>:<type>                           → body:<md5(data)>
#   cc-msg:<uuid>                                → uuid:<uuid>
#   cc-derived:<sess>:<ts>:<type>:<digest>       → derived:<digest>
#
# Idempotent: running it twice is a no-op (the second pass sees one row per
# group, deletes nothing). Gated by ``schema_version`` so it only fires on
# the v6→v7 transition; subsequent daemon starts skip it.

_DEDUP_KEY_SQL = """
    CASE
        WHEN regexp_matches(id, '^cc-msg:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
            THEN 'uuid:' || regexp_extract(id, '^cc-msg:(.+)$', 1)
        WHEN regexp_matches(id, '^cc-derived:')
            THEN 'derived:' || regexp_extract(id, ':([0-9a-f]{16})$', 1)
        WHEN regexp_matches(id, '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
            THEN 'uuid:' || id
        WHEN regexp_matches(id, '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
            THEN 'uuid:' || regexp_extract(id, '([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', 1)
        ELSE 'body:' || COALESCE(md5(data::VARCHAR), '')
    END
"""


def _run_dedup_migration_v7(conn) -> int:
    """One-time pass to collapse pre-#1232 duplicate rows in ``events``.

    Returns the number of rows deleted. Safe to call on a fresh store
    (no events → no deletions). Safe to call repeatedly (no remaining
    dupes after a successful first pass → no deletions).
    """
    # Confirm the events table exists — fresh stores get the v7 stamp without
    # ever having had v6 data, so there's nothing to dedup.
    has_events = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='main' AND table_name='events'"
    ).fetchone()[0]
    if not has_events:
        return 0
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events_pre_v7_dedup AS
        SELECT * FROM events
    """)
    # Materialise the (rowid, dedup_key) projection so DuckDB doesn't have to
    # re-evaluate the regex twice (once to find dupes, once to delete them).
    delete_sql = f"""
        DELETE FROM events
        WHERE rowid IN (
            SELECT rowid FROM (
                SELECT
                    rowid,
                    MIN(rowid) OVER (
                        PARTITION BY session_id, ts, event_type, ({_DEDUP_KEY_SQL})
                    ) AS keep_rowid
                FROM events
            )
            WHERE rowid != keep_rowid
        )
    """
    cur = conn.execute(delete_sql)
    # DuckDB's executemany doesn't surface affected-row count cleanly; do a
    # follow-up COUNT to compute a delta. The DELETE is the slow part; this
    # extra COUNT is cheap.
    # We capture the delta by counting rows touched: a simpler alternative is
    # to read changes() but DuckDB doesn't expose it on Python's connection.
    # Caller's COUNT(*) before/after is the canonical truth — this return
    # value is best-effort for logging only.
    try:
        return int(cur.fetchone()[0]) if cur.description else 0
    except Exception:
        return 0


def _to_blob(value: Any) -> bytes | None:
    """Coerce arbitrary value (dict / list / str / bytes / None) to a BLOB
    suitable for DuckDB. Used by the non-event ingest helpers (sessions,
    memory, heartbeats) — events have their own row-builder."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace")
    try:
        return json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")
    except Exception:
        return str(value).encode("utf-8", errors="replace")


def _open_connection(*, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection at DB_PATH, creating the directory if needed.

    Retries briefly on "Conflicting lock is held" — that error fires when an
    older sync daemon hasn't fully released the file lock yet (e.g. moments
    after install.sh's ``pkill -f clawmetry.sync``). install.sh used to
    ``sleep 1`` defensively; we now retry here so install.sh can return to
    the prompt immediately and the lock-release race is owned by the
    daemon-side code that actually cares about it. (#1215)
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 5 attempts × 0.5s = 2.5s budget. Beats a fixed install.sh sleep
    # because (a) most opens succeed on the first try and pay zero, and (b)
    # if the conflicting holder is genuinely stuck we surface the real
    # DuckDB error instead of silently sleeping past it.
    last_exc: Exception | None = None
    for attempt in range(5):
        try:
            return duckdb.connect(str(DB_PATH), read_only=read_only)
        except duckdb.IOException as exc:
            msg = str(exc)
            if "Conflicting lock" not in msg and "could not set lock" not in msg:
                raise
            last_exc = exc
            time.sleep(0.5)
    # Out of retries — re-raise the last lock error so the caller sees it.
    if last_exc is not None:
        raise last_exc
    return duckdb.connect(str(DB_PATH), read_only=read_only)  # unreachable


# ── Singleton store ─────────────────────────────────────────────────────────

# Two distinct singletons: one for the writer (sync daemon), one for read-only
# consumers (the dashboard process when daemon owns the writer lock). DuckDB
# allows multiple read-only handles per file even while a writer holds the
# lock, but ONLY across processes — a single process can hold one or the
# other, not both. So if both singletons are requested in the same process
# (unusual, but possible in tests or all-in-one local mode), `read_only=True`
# transparently shares the writer's connection.
_store_rw: "LocalStore | None" = None
_store_ro: "LocalStore | None" = None
_store_lock = threading.Lock()


def get_store(read_only: bool = False) -> "LocalStore":
    """Lazy-init the process-wide singleton. Cheap to call repeatedly.

    `read_only=True` opens the DuckDB file in RO mode, skipping the schema
    migration + background flusher. Use this in dashboard / API processes
    that do not own the writer lock — typically a separate process from the
    daemon that's ingesting events.

    If a writer singleton already exists in this process, `read_only=True`
    just returns the writer (DuckDB cannot have an RW handle and an RO
    handle to the same file in the same process). All read-paths on
    LocalStore work the same regardless of mode; ingest() raises in RO mode.
    """
    global _store_rw, _store_ro
    if not read_only:
        if _store_rw is not None:
            return _store_rw
        with _store_lock:
            if _store_rw is None:
                if _store_ro is not None:
                    raise RuntimeError(
                        "local_store: cannot open writer — read-only handle "
                        "already exists in this process. Get a fresh process "
                        "to write."
                    )
                _store_rw = LocalStore(read_only=False)
                _store_rw.start()
            return _store_rw
    # read_only path
    if _store_rw is not None:
        # Same-process reader — share the writer connection (DuckDB allows
        # multiple cursors but not a separate RO handle on the same file).
        return _store_rw
    if _store_ro is not None:
        return _store_ro
    with _store_lock:
        if _store_rw is not None:
            return _store_rw
        if _store_ro is None:
            _store_ro = LocalStore(read_only=True)
            # No flusher to start — RO never writes.
        return _store_ro


def _reset_singleton_for_tests() -> None:
    """Test-only helper. Drops the cached stores so the next get_store() picks
    up new env vars (DB path, flush knobs)."""
    global _store_rw, _store_ro
    with _store_lock:
        for name in ("_store_rw", "_store_ro"):
            store = globals().get(name)
            if store is not None:
                try:
                    store.stop(flush=False)
                except Exception:
                    pass
        _store_rw = None
        _store_ro = None


class LocalStore:
    """Thread-safe local event store with a background batched flusher.

    `read_only=True` opens the DuckDB in RO mode — read paths work the same,
    ingest()/flush() raise. Used by the dashboard process while the daemon
    process owns the writer lock.
    """

    def __init__(self, read_only: bool = False) -> None:
        self._read_only = read_only
        self._ring: deque[dict[str, Any]] = deque(maxlen=RING_MAX)
        self._ring_lock = threading.Lock()
        # DuckDB connection state isn't safe across concurrent transactions.
        # All writes go through ``_write_lock``; reads issue cursors which
        # DuckDB makes thread-safe internally.
        self._write_lock = threading.Lock()
        self._dropped = 0
        self._flusher_stop = threading.Event()
        self._flusher_thread: threading.Thread | None = None
        self._last_flush_ts = time.monotonic()
        if not read_only:
            # Rename the legacy events.duckdb in place BEFORE opening — once
            # we hold a connection we can't atomically rename the file out
            # from under DuckDB. RO mode skips this: if the file doesn't
            # exist yet, the daemon hasn't started, and there's nothing to
            # read anyway.
            _migrate_legacy_db_path()
        self._conn = _open_connection(read_only=read_only)
        if not read_only:
            self._migrate()

    def _migrate(self) -> None:
        """Bring the store schema up to current SCHEMA_VERSION. Order matters:
          1. v1→v2 column-add migrations (only do anything on legacy stores
             that pre-date agent_type) — must run BEFORE the DDL because the
             new `idx_events_atype_ts` index references agent_type.
          2. Full v2 DDL — CREATE TABLE/INDEX IF NOT EXISTS, no-op on
             already-migrated tables, creates the new tables on fresh stores.
          3. Version-gated data migrations (v6→v7 dedup, etc.) — only run on
             stores that haven't seen this version yet. Idempotent at the
             SQL level too, but the version gate makes the common (already-
             migrated) case a single SELECT.
          4. Stamp the schema_version row.
        """
        with self._write_lock:
            # Step 1: column-add migrations for legacy v1 stores. Tolerant
            # of "table doesn't exist" — fresh stores have no v1 tables to
            # migrate, the DDL below will create them at v2 directly.
            try:
                _apply_migrations(self._conn)
            except Exception:
                log.exception("local store: column-add migrations failed (continuing)")
            # Step 2: full v2 DDL. CREATE IF NOT EXISTS makes this idempotent
            # for both fresh stores (creates everything) and migrated stores
            # (only creates the new tables that didn't exist).
            for stmt in _DDL:
                self._conn.execute(stmt)
            # Step 3: version-gated data migrations.
            cur = self._conn.execute("SELECT MAX(version) AS v FROM schema_version")
            row = cur.fetchone()
            current = row[0] if row and row[0] is not None else 0
            if current < 7:
                # v6 → v7: collapse Claude Code event duplicates the three
                # ingest paths used to produce (#1232). Wrapped in try/except
                # so a regex/lock issue doesn't brick daemon startup — the
                # write-side fix in sync.py is the real correctness path; this
                # cleanup is opportunistic.
                try:
                    before = self._conn.execute(
                        "SELECT COUNT(*) FROM events"
                    ).fetchone()[0]
                    _run_dedup_migration_v7(self._conn)
                    after = self._conn.execute(
                        "SELECT COUNT(*) FROM events"
                    ).fetchone()[0]
                    deleted = max(0, before - after)
                    if deleted:
                        log.info(
                            "local store: v7 dedup migration removed %d "
                            "duplicate event row(s) (%d → %d)",
                            deleted, before, after,
                        )
                    else:
                        log.debug(
                            "local store: v7 dedup migration found no dupes (rows=%d)",
                            after,
                        )
                except Exception:
                    log.exception(
                        "local store: v7 dedup migration failed (continuing — "
                        "future writes still dedup via canonical id)"
                    )
            # Step 4: stamp the version.
            if current < SCHEMA_VERSION:
                self._conn.execute(
                    "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
                    [SCHEMA_VERSION, int(time.time() * 1000)],
                )

    # ── lifecycle ────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background flusher. Safe to call multiple times.
        No-op in read-only mode."""
        if self._read_only:
            return
        if self._flusher_thread and self._flusher_thread.is_alive():
            return
        self._flusher_stop.clear()
        t = threading.Thread(
            target=self._flusher_loop,
            name="clawmetry-local-store-flusher",
            daemon=True,
        )
        self._flusher_thread = t
        t.start()
        log.info("local store: started, db=%s", DB_PATH)

    def stop(self, *, flush: bool = True) -> None:
        """Stop the flusher. Optionally drain the ring first."""
        self._flusher_stop.set()
        if self._flusher_thread:
            self._flusher_thread.join(timeout=10)
        if flush:
            try:
                self._flush_now()
            except Exception:
                log.exception("local store: final flush on stop failed")
        # Close the underlying connection so a subsequent process can open it.
        try:
            with self._write_lock:
                self._conn.close()
        except Exception:
            pass

    # ── ingest ──────────────────────────────────────────────────────────

    def ingest(self, event: dict[str, Any]) -> None:
        """Queue one event. Returns immediately; the flusher persists in the
        background. Required keys: ``id``, ``node_id``, ``event_type``, ``ts``.
        Other columns optional. Re-ingesting the same id is a no-op (INSERT OR
        IGNORE) so callers don't need their own dedup."""
        if self._read_only:
            raise RuntimeError("local_store: ingest() called on read-only store")
        if not event.get("id"):
            raise ValueError("event must include 'id'")
        if not event.get("node_id"):
            raise ValueError("event must include 'node_id'")
        if not event.get("event_type"):
            raise ValueError("event must include 'event_type'")
        if not event.get("ts"):
            raise ValueError("event must include 'ts'")
        with self._ring_lock:
            if len(self._ring) >= RING_MAX:
                self._dropped += 1
            self._ring.append(event)
        if len(self._ring) >= FLUSH_BATCH:
            self._flush_now()

    def ingest_many(self, events: Iterable[dict[str, Any]]) -> None:
        for e in events:
            self.ingest(e)

    # ── ingest helpers for the non-event tables ────────────────────────────
    #
    # Sessions/memory/heartbeats are low-volume, low-frequency writes (one
    # per session-update / per memory-file / per minute). They bypass the
    # ring buffer and write synchronously — simpler than batching, and the
    # contention with the flusher is negligible at this rate.

    def ingest_session(self, session: dict[str, Any]) -> None:
        """Upsert one session row. Required: session_id. Other fields optional."""
        sid = session.get("session_id")
        if not sid:
            raise ValueError("session must include 'session_id'")
        atype = session.get("agent_type") or "openclaw"
        meta_blob = _to_blob(session.get("metadata"))
        now_ms = int(time.time() * 1000)
        params = [
            atype, sid,
            session.get("node_id"),
            session.get("agent_id") or "main",
            session.get("workspace_id"),
            session.get("title"),
            session.get("started_at"),
            session.get("last_active_at"),
            session.get("ended_at"),
            session.get("status"),
            int(session.get("total_tokens") or 0),
            float(session.get("cost_usd") or 0),
            int(session.get("message_count") or 0),
            meta_blob,
            now_ms,
        ]
        with self._write_lock:
            # Upsert: replace if (agent_type, session_id) exists.
            self._conn.execute("""
                INSERT INTO sessions (
                    agent_type, session_id, node_id, agent_id, workspace_id,
                    title, started_at, last_active_at, ended_at, status,
                    total_tokens, cost_usd, message_count, metadata, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (agent_type, session_id) DO UPDATE SET
                    node_id        = excluded.node_id,
                    agent_id       = excluded.agent_id,
                    workspace_id   = excluded.workspace_id,
                    title          = COALESCE(excluded.title, sessions.title),
                    started_at     = COALESCE(sessions.started_at, excluded.started_at),
                    last_active_at = excluded.last_active_at,
                    ended_at       = excluded.ended_at,
                    status         = excluded.status,
                    total_tokens   = excluded.total_tokens,
                    cost_usd       = excluded.cost_usd,
                    message_count  = excluded.message_count,
                    metadata       = COALESCE(excluded.metadata, sessions.metadata),
                    updated_at     = excluded.updated_at
            """, params)

    def ingest_memory_blob(self, blob_row: dict[str, Any]) -> None:
        """Upsert one memory blob (e.g. CLAUDE.md, ~/.openclaw/memory/notes.md).

        Required: agent_type, path. Optional: agent_id, blob, sha256, ts.
        Re-ingesting with the same sha256 is a no-op (cheap dedup)."""
        atype = blob_row.get("agent_type")
        path = blob_row.get("path")
        if not atype or not path:
            raise ValueError("memory blob must include 'agent_type' and 'path'")
        agent_id = blob_row.get("agent_id") or "main"
        blob = blob_row.get("blob")
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="replace")
        sha = blob_row.get("sha256")
        if not sha and blob is not None:
            import hashlib
            sha = hashlib.sha256(blob).hexdigest()
        size = blob_row.get("size_bytes")
        if size is None and blob is not None:
            size = len(blob)
        now_ms = int(time.time() * 1000)
        with self._write_lock:
            # Skip the write if the blob hasn't changed (sha256 match).
            if sha:
                cur = self._conn.execute(
                    "SELECT sha256 FROM memory_blobs WHERE agent_type=? AND agent_id=? AND path=?",
                    [atype, agent_id, path],
                )
                row = cur.fetchone()
                if row and row[0] == sha:
                    return
            self._conn.execute("""
                INSERT INTO memory_blobs (
                    agent_type, agent_id, path, ts, blob, sha256, size_bytes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (agent_type, agent_id, path) DO UPDATE SET
                    ts         = excluded.ts,
                    blob       = excluded.blob,
                    sha256     = excluded.sha256,
                    size_bytes = excluded.size_bytes,
                    updated_at = excluded.updated_at
            """, [atype, agent_id, path, blob_row.get("ts"), blob, sha, size, now_ms])

    def ingest_channel(self, ch: dict[str, Any]) -> None:
        """Upsert one OpenClaw channel-context row. Required: session_id.
        Optional: channel, chat_type, subject, origin_label."""
        sid = ch.get("session_id")
        if not sid:
            raise ValueError("channel must include 'session_id'")
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO openclaw_channels (
                    session_id, channel, chat_type, subject, origin_label
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (session_id) DO UPDATE SET
                    channel      = COALESCE(excluded.channel, openclaw_channels.channel),
                    chat_type    = COALESCE(excluded.chat_type, openclaw_channels.chat_type),
                    subject      = COALESCE(excluded.subject, openclaw_channels.subject),
                    origin_label = COALESCE(excluded.origin_label, openclaw_channels.origin_label)
            """, [sid, ch.get("channel"), ch.get("chat_type"),
                  ch.get("subject"), ch.get("origin_label")])

    def ingest_channel_message(self, msg: dict[str, Any]) -> None:
        """Upsert one channel-message row (issue #1088 Phase 4).

        Required keys: ``id``, ``provider``, ``ts``, ``direction``.
        Optional: ``agent_id`` (default ``"main"``), ``channel_id``,
        ``sender_id``, ``sender_name``, ``body``, ``session_key``,
        ``raw_blob`` (any JSON-able value — coerced to BLOB for opaque
        per-provider extras like attachments / message_id / reactions).

        ``direction`` MUST be ``"in"`` (inbound from user) or ``"out"``
        (outbound from agent). The PRIMARY KEY is ``id`` so re-ingesting
        the same upstream id is a no-op (the daemon scans logs +
        transcripts on every cycle; idempotency is essential).

        We coerce ``provider`` to lowercase so ``"Telegram"`` and
        ``"telegram"`` round-trip to the same partition — every query
        helper below also lowercases on input.
        """
        mid = msg.get("id")
        if not mid:
            raise ValueError("channel_message must include 'id'")
        provider = msg.get("provider")
        if not provider:
            raise ValueError("channel_message must include 'provider'")
        ts = msg.get("ts")
        if not ts:
            raise ValueError("channel_message must include 'ts'")
        direction = msg.get("direction")
        if direction not in ("in", "out"):
            raise ValueError(
                "channel_message direction must be 'in' or 'out' "
                f"(got {direction!r})"
            )
        provider = str(provider).lower().strip()
        raw_blob = _to_blob(msg.get("raw_blob"))
        body = msg.get("body")
        if body is not None:
            body = str(body)
        now_ms = int(time.time() * 1000)
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO channel_messages (
                    id, agent_id, provider, channel_id, sender_id, sender_name,
                    body, ts, direction, session_key, raw_blob, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    agent_id     = COALESCE(excluded.agent_id, channel_messages.agent_id),
                    provider     = excluded.provider,
                    channel_id   = COALESCE(excluded.channel_id, channel_messages.channel_id),
                    sender_id    = COALESCE(excluded.sender_id, channel_messages.sender_id),
                    sender_name  = COALESCE(excluded.sender_name, channel_messages.sender_name),
                    body         = COALESCE(excluded.body, channel_messages.body),
                    ts           = excluded.ts,
                    direction    = excluded.direction,
                    session_key  = COALESCE(excluded.session_key, channel_messages.session_key),
                    raw_blob     = COALESCE(excluded.raw_blob, channel_messages.raw_blob)
            """, [
                str(mid),
                str(msg.get("agent_id") or "main"),
                provider,
                msg.get("channel_id"),
                msg.get("sender_id"),
                msg.get("sender_name"),
                body,
                str(ts),
                direction,
                msg.get("session_key"),
                raw_blob,
                now_ms,
            ])

    def ingest_channel_config(
        self,
        provider: str,
        encrypted_blob: bytes | None,
        enabled: bool | None = None,
        status_meta: dict[str, Any] | None = None,
    ) -> None:
        """Upsert one channel-adapter config row (epic #1032 Phase 5).

        ``encrypted_blob`` is the E2E ciphertext of the adapter config dict
        (bot token, OAuth secret, etc.). The cloud never sees plaintext;
        ciphertext only ever traverses the wire and only ever rests in this
        local DuckDB. The blob may be ``None`` when callers want to update
        status without rotating the config (e.g. ``channel_test`` results).

        ``status_meta`` is a non-secret summary the cloud can later display:
        ``{"last_test_at", "last_test_ok", "last_test_error"}``. Any subset
        is honored; missing keys leave the existing value untouched.

        Idempotent: re-upserting the same provider replaces the blob and
        merges status_meta. The COALESCE pattern preserves prior status
        fields when a partial update arrives (e.g. a config rotation that
        doesn't include a fresh test result)."""
        if not provider:
            raise ValueError("channel_config must include 'provider'")
        provider = str(provider).lower().strip()
        meta = status_meta or {}
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Coerce blob: bytes/bytearray pass through; str gets utf-8-encoded;
        # None means "don't touch the blob" (status-only update). The ON
        # CONFLICT clause uses COALESCE so an explicit None preserves the
        # existing row's blob.
        if encrypted_blob is not None and not isinstance(encrypted_blob, (bytes, bytearray)):
            if isinstance(encrypted_blob, str):
                encrypted_blob = encrypted_blob.encode("utf-8")
            else:
                raise ValueError("encrypted_blob must be bytes or str")
        blob_bytes = bytes(encrypted_blob) if encrypted_blob is not None else None
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO channel_config (
                    provider, enabled, config_json_encrypted,
                    last_test_at, last_test_ok, last_test_error, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (provider) DO UPDATE SET
                    enabled               = COALESCE(excluded.enabled, channel_config.enabled),
                    config_json_encrypted = COALESCE(excluded.config_json_encrypted, channel_config.config_json_encrypted),
                    last_test_at          = COALESCE(excluded.last_test_at, channel_config.last_test_at),
                    last_test_ok          = COALESCE(excluded.last_test_ok, channel_config.last_test_ok),
                    last_test_error       = COALESCE(excluded.last_test_error, channel_config.last_test_error),
                    updated_at            = excluded.updated_at
            """, [
                provider,
                bool(enabled) if enabled is not None else None,
                blob_bytes,
                meta.get("last_test_at"),
                bool(meta["last_test_ok"]) if "last_test_ok" in meta and meta["last_test_ok"] is not None else None,
                meta.get("last_test_error"),
                now_iso,
            ])

    def ingest_cron(self, cron: dict[str, Any]) -> None:
        """Upsert one cron-job row. Required: cron_id.

        Dict-shaped ``schedule`` values (the gateway shape:
        ``{kind:'every', everyMs:60000}``) are JSON-encoded before storing
        so ``_row_to_cron_job`` in ``routes/crons.py`` can decode them
        back. Without this, DuckDB's default ``str(dict)`` representation
        is not valid JSON and downstream consumers (e.g.
        ``/api/agent-intentions`` schedule-kind projection) lose the
        ``kind``/``everyMs`` fields needed to compute firings."""
        cid = cron.get("cron_id")
        if not cid:
            raise ValueError("cron must include 'cron_id'")
        atype = cron.get("agent_type") or "openclaw"
        data_blob = _to_blob({k: v for k, v in cron.items()
                              if k not in {"cron_id", "agent_type", "agent_id",
                                           "name", "schedule", "enabled",
                                           "last_run_at", "last_status",
                                           "next_run_at"}})
        schedule = cron.get("schedule")
        if isinstance(schedule, (dict, list)):
            schedule = json.dumps(schedule, separators=(",", ":"))
        now_ms = int(time.time() * 1000)
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO crons (
                    agent_type, cron_id, agent_id, name, schedule, enabled,
                    last_run_at, last_status, next_run_at, data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (agent_type, cron_id) DO UPDATE SET
                    agent_id     = excluded.agent_id,
                    name         = COALESCE(excluded.name, crons.name),
                    schedule     = COALESCE(excluded.schedule, crons.schedule),
                    enabled      = excluded.enabled,
                    last_run_at  = excluded.last_run_at,
                    last_status  = excluded.last_status,
                    next_run_at  = excluded.next_run_at,
                    data         = COALESCE(excluded.data, crons.data),
                    updated_at   = excluded.updated_at
            """, [atype, cid, cron.get("agent_id") or "main",
                  cron.get("name"), schedule,
                  bool(cron.get("enabled", True)),
                  cron.get("last_run_at"), cron.get("last_status"),
                  cron.get("next_run_at"), data_blob, now_ms])

    def ingest_cron_run(self, run: dict[str, Any]) -> None:
        """Upsert one cron-run row (issue #605 DuckDB follow-up).

        Required: ``id`` and ``job_id``. Everything else is optional and
        defaults to ``None`` / ``0``. Re-ingesting the same id is a no-op
        which is exactly what we want — the sync daemon scans the JSONL
        files with an offset cursor, but a restart that re-reads a few
        bytes (or a JSONL writer that re-emits a line) must not produce
        duplicate rows.

        Stable id rule: the daemon synthesises ``f"{job_id}:{started_at}"``
        when the JSONL line doesn't carry one. That keeps the dedup
        deterministic across re-scans without depending on file offsets
        for correctness (offsets are still tracked for skip-on-cycle
        efficiency, but they're a performance hint, not the dedup key)."""
        rid = run.get("id")
        if not rid:
            raise ValueError("cron_run must include 'id'")
        job_id = run.get("job_id")
        if not job_id:
            raise ValueError("cron_run must include 'job_id'")
        atype = run.get("agent_type") or "openclaw"
        agent_id = run.get("agent_id") or "main"
        # Anything callers stuffed in beyond the first-class columns ends up
        # in the BLOB so we don't lose provenance. ``usage`` is the common
        # one — gateway writers emit a dict with input/output token splits
        # we'd otherwise drop.
        first_class = {
            "id", "job_id", "node_id", "agent_type", "agent_id",
            "started_at", "ended_at", "duration_ms", "status",
            "error_message", "token_count", "cost_usd",
            "delivered_at", "next_run_at", "raw_jsonl_line",
        }
        data_blob = _to_blob({k: v for k, v in run.items()
                              if k not in first_class})
        # Coerce numeric fields defensively — JSONL writers have shipped
        # strings, floats, and missing values across versions.
        try:
            duration_ms = int(run.get("duration_ms") or 0)
        except (TypeError, ValueError):
            duration_ms = 0
        try:
            token_count = int(run.get("token_count") or 0)
        except (TypeError, ValueError):
            token_count = 0
        try:
            cost_usd = float(run.get("cost_usd") or 0)
        except (TypeError, ValueError):
            cost_usd = 0.0
        err_msg = run.get("error_message") or ""
        if err_msg and not isinstance(err_msg, str):
            err_msg = str(err_msg)
        if err_msg and len(err_msg) > 2000:
            err_msg = err_msg[:2000]
        raw_line = run.get("raw_jsonl_line")
        if raw_line is not None and not isinstance(raw_line, str):
            raw_line = str(raw_line)
        now_ms = int(time.time() * 1000)
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO cron_runs (
                    id, node_id, agent_type, agent_id, job_id,
                    started_at, ended_at, duration_ms, status, error_message,
                    token_count, cost_usd, delivered_at, next_run_at,
                    raw_jsonl_line, data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
            """, [
                str(rid), run.get("node_id"), atype, agent_id, str(job_id),
                run.get("started_at"), run.get("ended_at"),
                duration_ms, run.get("status"), err_msg,
                token_count, cost_usd,
                run.get("delivered_at"), run.get("next_run_at"),
                raw_line, data_blob, now_ms,
            ])

    def ingest_subagent(self, sa: dict[str, Any]) -> None:
        """Upsert one subagent rollup row. Required: subagent_id."""
        sid = sa.get("subagent_id")
        if not sid:
            raise ValueError("subagent must include 'subagent_id'")
        atype = sa.get("agent_type") or "openclaw"
        data_blob = _to_blob({k: v for k, v in sa.items()
                              if k not in {"subagent_id", "agent_type",
                                           "parent_session_id", "spawned_at",
                                           "ended_at", "task", "status",
                                           "cost_usd", "token_count"}})
        now_ms = int(time.time() * 1000)
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO subagents (
                    agent_type, subagent_id, parent_session_id, spawned_at,
                    ended_at, task, status, cost_usd, token_count, data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (agent_type, subagent_id) DO UPDATE SET
                    parent_session_id = COALESCE(excluded.parent_session_id, subagents.parent_session_id),
                    spawned_at        = COALESCE(subagents.spawned_at, excluded.spawned_at),
                    ended_at          = excluded.ended_at,
                    task              = COALESCE(excluded.task, subagents.task),
                    status            = excluded.status,
                    cost_usd          = excluded.cost_usd,
                    token_count       = excluded.token_count,
                    data              = COALESCE(excluded.data, subagents.data),
                    updated_at        = excluded.updated_at
            """, [atype, sid, sa.get("parent_session_id"),
                  sa.get("spawned_at"), sa.get("ended_at"),
                  sa.get("task"), sa.get("status"),
                  float(sa.get("cost_usd") or 0),
                  int(sa.get("token_count") or 0),
                  data_blob, now_ms])

    def ingest_loop_signal(
        self,
        session_id: str,
        signature: str,
        repeat_count: int,
        first_seen: str | None = None,
        last_seen: str | None = None,
        severity: str = "warning",
        agent_type: str = "openclaw",
        details: Any = None,
    ) -> None:
        """Upsert one loop-detection signal (issue #1364).

        Called from ``clawmetry.proxy.LoopDetector`` whenever a request
        pattern repeats often enough within the configured window to
        flag a loop. PK is ``(session_id, signature)`` so the same
        loop pattern recurring in the same session bumps ``repeat_count``
        and refreshes ``last_seen`` instead of creating a new row —
        callers pass the latest cumulative count.

        ``first_seen`` / ``last_seen`` accept ISO-8601 strings; if absent
        we stamp ``time.time()`` for both. ``details`` is any
        JSON-friendly value (e.g. ``{"model": "...", "request_hash": ...}``)
        and is stored as a BLOB so the route can hydrate it back into the
        UI without a fixed schema.

        Permissive — never raises on bad input; we drop the write rather
        than crash the proxy. The detector is on the request hot path."""
        if not session_id or not signature:
            return
        try:
            count = int(repeat_count or 0)
        except (TypeError, ValueError):
            count = 0
        if count <= 0:
            return
        # Use local-naive time so the value compares apples-to-apples with
        # ``current_timestamp - INTERVAL`` in ``query_recent_loop_signals``
        # (DuckDB's TIMESTAMP column has no zone; mixing UTC strings with
        # TZ-aware ``current_timestamp`` shifts rows out of the window on
        # any host whose local TZ != UTC).
        now_iso = datetime.now().isoformat(timespec="seconds")
        first = first_seen or now_iso
        last = last_seen or now_iso
        sev = (severity or "warning").strip()[:32]
        atype = (agent_type or "openclaw").strip()[:64]
        details_blob = _to_blob(details) if details is not None else None
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO loop_signals (
                    session_id, signature, repeat_count,
                    first_seen, last_seen, severity, agent_type, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (session_id, signature) DO UPDATE SET
                    repeat_count = GREATEST(loop_signals.repeat_count, excluded.repeat_count),
                    last_seen    = GREATEST(loop_signals.last_seen, excluded.last_seen),
                    first_seen   = LEAST(loop_signals.first_seen, excluded.first_seen),
                    severity     = excluded.severity,
                    agent_type   = excluded.agent_type,
                    details      = COALESCE(excluded.details, loop_signals.details)
            """, [
                str(session_id)[:128],
                str(signature)[:256],
                count,
                first,
                last,
                sev,
                atype,
                details_blob,
            ])

    def query_recent_loop_signals(
        self,
        *,
        limit: int = 20,
        since_minutes: int = 60,
    ) -> list[dict[str, Any]]:
        """Return recent loop-detection signals, newest first (issue #1364).

        Filters to rows whose ``last_seen`` falls within the last
        ``since_minutes`` minutes; pass ``since_minutes <= 0`` to disable
        the window and return any row regardless of age. ``limit`` is
        clamped to ``[1, 200]``."""
        try:
            lim = int(limit)
        except (TypeError, ValueError):
            lim = 20
        lim = max(1, min(200, lim))
        try:
            window_min = int(since_minutes)
        except (TypeError, ValueError):
            window_min = 60
        clauses: list[str] = []
        params: list[Any] = []
        if window_min > 0:
            # Cast both sides to naive TIMESTAMP so the comparison stays in
            # local wall-clock — same convention the writer uses.
            clauses.append(
                "last_seen >= (current_timestamp::TIMESTAMP - INTERVAL (? * 60) SECOND)"
            )
            params.append(window_min)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT session_id, signature, repeat_count,
                   first_seen, last_seen, severity, agent_type, details
            FROM loop_signals
            {where}
            ORDER BY last_seen DESC, session_id, signature
            LIMIT ?
        """
        params.append(lim)
        cols = ["session_id", "signature", "repeat_count",
                "first_seen", "last_seen", "severity", "agent_type", "details"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            # Stringify timestamps so JSON serialisation is trivial — DuckDB
            # returns ``datetime.datetime`` objects which Flask's jsonify
            # handles, but downstream JS expects ISO strings everywhere
            # else in the codebase.
            for tcol in ("first_seen", "last_seen"):
                v = d.get(tcol)
                if hasattr(v, "isoformat"):
                    d[tcol] = v.isoformat()
            raw = d.get("details")
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    try:
                        d["details"] = json.loads(text)
                    except (ValueError, TypeError):
                        d["details"] = text
                except UnicodeDecodeError:
                    d["details"] = None
            out.append(d)
        return out

    def ingest_alert_rule(self, rule: dict[str, Any]) -> None:
        """Upsert one alert rule. Required: ``id``.

        Optional: ``owner_hash``, ``name``, ``condition_json``,
        ``enabled`` (default True), ``created_at``, ``updated_at``,
        ``last_fired_at``, ``fire_count``.

        ``condition_json`` accepts a dict / list / str / bytes — it is
        coerced to a BLOB via the same path as session metadata, so the
        cloud can store whichever rule shape it likes without dragging
        a schema bump through here. Pre-existing values for
        ``created_at``, ``last_fired_at``, and ``fire_count`` are
        preserved across upserts (the relay-driven write path doesn't
        know them — only the local evaluator does)."""
        rid = rule.get("id")
        if not rid:
            raise ValueError("alert rule must include 'id'")
        cond_blob = _to_blob(rule.get("condition_json"))
        enabled = rule.get("enabled")
        enabled = True if enabled is None else bool(enabled)
        # fire_count is coerced to int when supplied, otherwise we keep the
        # existing value via the ON CONFLICT clause below.
        try:
            fire_count = int(rule.get("fire_count")) if rule.get("fire_count") is not None else 0
        except (TypeError, ValueError):
            fire_count = 0
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO alert_rules (
                    id, owner_hash, name, condition_json, enabled,
                    created_at, updated_at, last_fired_at, fire_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    owner_hash     = COALESCE(excluded.owner_hash, alert_rules.owner_hash),
                    name           = COALESCE(excluded.name, alert_rules.name),
                    condition_json = COALESCE(excluded.condition_json, alert_rules.condition_json),
                    enabled        = excluded.enabled,
                    updated_at     = COALESCE(excluded.updated_at, alert_rules.updated_at),
                    last_fired_at  = COALESCE(excluded.last_fired_at, alert_rules.last_fired_at),
                    fire_count     = CASE
                                       WHEN excluded.fire_count > 0
                                         THEN excluded.fire_count
                                       ELSE alert_rules.fire_count
                                     END
            """, [
                str(rid),
                rule.get("owner_hash"),
                rule.get("name"),
                cond_blob,
                enabled,
                rule.get("created_at"),
                rule.get("updated_at"),
                rule.get("last_fired_at"),
                fire_count,
            ])

    def delete_alert_rule(self, rule_id: str) -> int:
        """Delete one alert rule by id. Returns 1 on delete, 0 when missing.

        Uses a SELECT-before-DELETE check because DuckDB's ``cur.rowcount``
        is unreliable for DELETE on some versions (returns -1). Cheap at
        our scale — alert rules are a tiny table."""
        if not rule_id:
            return 0
        # Check existence first so we can return an accurate 0/1.
        rid = str(rule_id)
        rows_before = self._fetch(
            "SELECT 1 FROM alert_rules WHERE id = ? LIMIT 1", [rid]
        )
        if not rows_before:
            return 0
        with self._write_lock:
            self._conn.execute("DELETE FROM alert_rules WHERE id = ?", [rid])
        return 1

    # ── Per-agent budgets (issue #951) ───────────────────────────────────

    def set_agent_budget(
        self,
        agent_id: str,
        *,
        daily_limit_usd: float | None = None,
        monthly_limit_usd: float | None = None,
    ) -> None:
        """Upsert one per-agent budget override row. Required: ``agent_id``.

        Either / both of ``daily_limit_usd`` and ``monthly_limit_usd`` may
        be ``None`` — that side falls back to the global budget. Pass
        ``0`` (or any non-positive value) on either column to clear the
        per-agent limit on that side while preserving the other; pass
        both as ``None`` and you may as well call ``delete_agent_budget``
        for symmetry, but the row is preserved either way."""
        if not agent_id:
            raise ValueError("agent budget must include 'agent_id'")
        now_ms = int(time.time() * 1000)
        # Coerce numeric inputs; None stays NULL in DuckDB.
        def _coerce(v):
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        d = _coerce(daily_limit_usd)
        m = _coerce(monthly_limit_usd)
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO agent_budgets (
                    agent_id, daily_limit_usd, monthly_limit_usd, updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT (agent_id) DO UPDATE SET
                    daily_limit_usd   = excluded.daily_limit_usd,
                    monthly_limit_usd = excluded.monthly_limit_usd,
                    updated_at        = excluded.updated_at
            """, [str(agent_id), d, m, now_ms])

    def get_agent_budget(self, agent_id: str) -> dict[str, Any] | None:
        """Return one per-agent budget row or ``None`` when no override is
        configured. Callers should fall back to the global budget config
        on a ``None`` return."""
        if not agent_id:
            return None
        rows = self._fetch(
            "SELECT agent_id, daily_limit_usd, monthly_limit_usd, updated_at "
            "FROM agent_budgets WHERE agent_id = ? LIMIT 1",
            [str(agent_id)],
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "agent_id": r[0],
            "daily_limit_usd": r[1],
            "monthly_limit_usd": r[2],
            "updated_at": r[3],
        }

    def query_agent_budgets(self, *, limit: int = 500) -> list[dict[str, Any]]:
        """Return all per-agent budget overrides, most-recently-updated
        first. Cheap — this table is tiny (one row per agent)."""
        rows = self._fetch(
            "SELECT agent_id, daily_limit_usd, monthly_limit_usd, updated_at "
            "FROM agent_budgets ORDER BY updated_at DESC LIMIT ?",
            [int(limit)],
        )
        return [
            {
                "agent_id": r[0],
                "daily_limit_usd": r[1],
                "monthly_limit_usd": r[2],
                "updated_at": r[3],
            }
            for r in rows
        ]

    def delete_agent_budget(self, agent_id: str) -> int:
        """Delete one per-agent override row. Returns 1 on delete, 0 when
        missing. After deletion the agent falls back to the global budget."""
        if not agent_id:
            return 0
        aid = str(agent_id)
        rows_before = self._fetch(
            "SELECT 1 FROM agent_budgets WHERE agent_id = ? LIMIT 1", [aid]
        )
        if not rows_before:
            return 0
        with self._write_lock:
            self._conn.execute(
                "DELETE FROM agent_budgets WHERE agent_id = ?", [aid]
            )
        return 1

    # ── BOOTSTRAP archive (issue #690) ──────────────────────────────────────

    def ingest_bootstrap_archive(self, row: dict[str, Any]) -> bool:
        """Insert one BOOTSTRAP.md snapshot. Returns True if a new row was
        written, False if (node_id, agent_id, content_sha256) already exists.

        Required keys: ``node_id``, ``content``. Optional: ``agent_id``
        (default ``"main"``), ``captured_at`` (default = now UTC ISO),
        ``file_mtime``, ``first_session_id``, ``source_path``. ``content``
        is stored as VARCHAR (BOOTSTRAP.md is small markdown — there's no
        reason to BLOB-encode). ``content_sha256`` is computed here when
        missing so callers don't have to.

        Idempotent: re-capturing the same content for the same
        (node_id, agent_id) is a no-op. If the file is rewritten (different
        content), a new row is inserted — preserving the full first-contact
        history when the bootstrap is re-negotiated.
        """
        if self._read_only:
            raise RuntimeError(
                "local_store: ingest_bootstrap_archive() on read-only store"
            )
        node_id = row.get("node_id")
        if not node_id:
            raise ValueError("bootstrap archive row must include 'node_id'")
        content = row.get("content")
        if content is None:
            raise ValueError("bootstrap archive row must include 'content'")
        if isinstance(content, (bytes, bytearray)):
            content = content.decode("utf-8", errors="replace")
        else:
            content = str(content)
        agent_id = row.get("agent_id") or "main"
        sha = row.get("content_sha256")
        if not sha:
            import hashlib
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        captured_at = row.get("captured_at")
        if not captured_at:
            from datetime import datetime, timezone
            captured_at = datetime.now(timezone.utc).isoformat()
        size_bytes = row.get("size_bytes")
        if size_bytes is None:
            size_bytes = len(content.encode("utf-8"))
        params = [
            str(node_id),
            str(agent_id),
            str(captured_at),
            row.get("file_mtime"),
            content,
            sha,
            row.get("first_session_id"),
            int(size_bytes),
            row.get("source_path"),
        ]
        with self._write_lock:
            # Detect dup BEFORE the insert so we can return an accurate flag.
            cur = self._conn.execute(
                "SELECT 1 FROM bootstrap_archive "
                "WHERE node_id=? AND agent_id=? AND content_sha256=? LIMIT 1",
                [str(node_id), str(agent_id), sha],
            )
            if cur.fetchone():
                return False
            self._conn.execute(
                """
                INSERT INTO bootstrap_archive (
                    node_id, agent_id, captured_at, file_mtime, content,
                    content_sha256, first_session_id, size_bytes, source_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params,
            )
        return True

    def query_bootstrap_archive(
        self,
        *,
        node_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Read bootstrap-archive rows, newest first.

        ``node_id`` scopes the result to one machine; ``agent_id`` further
        narrows to a single agent within that node. Returns full content —
        BOOTSTRAP.md is tiny (typically <8 KB) so there's no value in a
        lazy-content variant."""
        clauses: list[str] = []
        params: list[Any] = []
        if node_id:
            clauses.append("node_id = ?")
            params.append(str(node_id))
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(str(agent_id))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT node_id, agent_id, captured_at, file_mtime, content,
                   content_sha256, first_session_id, size_bytes, source_path
            FROM bootstrap_archive
            {where}
            ORDER BY captured_at DESC, agent_id
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["node_id", "agent_id", "captured_at", "file_mtime", "content",
                "content_sha256", "first_session_id", "size_bytes",
                "source_path"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            out.append(dict(zip(cols, r)))
        return out

    def ingest_approval(self, approval: dict[str, Any]) -> None:
        """Upsert one approval-queue row. Required: ``id``.

        Optional: ``owner_hash``, ``requestor_session_id``, ``action``,
        ``args`` (dict / list / str / bytes — coerced to BLOB via
        ``_to_blob``), ``status`` (default ``"pending"``), ``created_at``,
        ``resolved_at``, ``resolver``, ``decision``, ``decision_reason``.

        Re-ingesting the same id updates non-NULL fields and bumps the
        status; pre-existing decision metadata is preserved when the new
        row only carries the request (the common case — policy watcher
        creates the row, decision flow updates it via
        ``update_approval_decision`` below)."""
        aid = approval.get("id")
        if not aid:
            raise ValueError("approval must include 'id'")
        args_blob = _to_blob(approval.get("args"))
        status = approval.get("status") or "pending"
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO approvals (
                    id, owner_hash, requestor_session_id, action, args,
                    status, created_at, resolved_at, resolver, decision,
                    decision_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    owner_hash           = COALESCE(excluded.owner_hash, approvals.owner_hash),
                    requestor_session_id = COALESCE(excluded.requestor_session_id, approvals.requestor_session_id),
                    action               = COALESCE(excluded.action, approvals.action),
                    args                 = COALESCE(excluded.args, approvals.args),
                    status               = excluded.status,
                    created_at           = COALESCE(approvals.created_at, excluded.created_at),
                    resolved_at          = COALESCE(excluded.resolved_at, approvals.resolved_at),
                    resolver             = COALESCE(excluded.resolver, approvals.resolver),
                    decision             = COALESCE(excluded.decision, approvals.decision),
                    decision_reason      = COALESCE(excluded.decision_reason, approvals.decision_reason)
            """, [
                str(aid),
                approval.get("owner_hash"),
                approval.get("requestor_session_id"),
                approval.get("action"),
                args_blob,
                status,
                approval.get("created_at"),
                approval.get("resolved_at"),
                approval.get("resolver"),
                approval.get("decision"),
                approval.get("decision_reason"),
            ])

    def update_approval_decision(
        self,
        approval_id: str,
        decision: str,
        resolver: str,
        reason: str | None = None,
    ) -> int:
        """Mark a pending approval as resolved. Returns 1 on update,
        0 when the row is missing OR already decided (idempotent).

        ``decision`` is the human-readable verdict (``"approve"`` /
        ``"deny"`` from the cloud UI button click). ``status`` is bumped
        to mirror the cloud-side semantics: ``approved`` / ``denied``,
        falling back to ``decision`` itself for forward-compat with
        future verdicts (e.g. ``deferred``). ``resolved_at`` is stamped
        with the current UTC ISO timestamp.

        Only updates rows still in the ``pending`` state — late
        retries from the cloud relay are a no-op so the user's first
        click wins even if the network reorders deliveries."""
        if not approval_id:
            return 0
        if decision == "approve":
            new_status = "approved"
        elif decision == "deny":
            new_status = "denied"
        else:
            new_status = decision or "decided"
        from datetime import datetime, timezone
        resolved_at = datetime.now(timezone.utc).isoformat()
        with self._write_lock:
            # Pre-check is the only reliable way to distinguish "first
            # successful flip" from "already decided, no-op" on DuckDB
            # versions whose UPDATE rowcount returns -1. We do it inside
            # the write lock so the read-then-write pair is atomic against
            # concurrent decision attempts.
            pre = self._conn.execute(
                "SELECT status FROM approvals WHERE id = ? LIMIT 1",
                [str(approval_id)],
            ).fetchone()
            if not pre:
                return 0
            if pre[0] != "pending":
                return 0
            self._conn.execute("""
                UPDATE approvals
                SET status          = ?,
                    decision        = ?,
                    decision_reason = ?,
                    resolver        = ?,
                    resolved_at     = ?
                WHERE id = ?
                  AND status = 'pending'
            """, [new_status, decision, reason, resolver, resolved_at,
                  str(approval_id)])
        return 1

    def ingest_system_snapshot(self, snap: dict[str, Any]) -> None:
        """Insert one system-snapshot row. Append-only;
        (agent_type, node_id, ts, kind) PK silently ignores duplicates."""
        node_id = snap.get("node_id")
        ts = snap.get("ts")
        kind = snap.get("kind")
        if not node_id or not ts or not kind:
            raise ValueError("snapshot must include 'node_id', 'ts', 'kind'")
        atype = snap.get("agent_type") or "openclaw"
        data_blob = _to_blob({k: v for k, v in snap.items()
                              if k not in {"node_id", "ts", "kind", "agent_type"}})
        with self._write_lock:
            self._conn.execute("""
                INSERT OR IGNORE INTO system_snapshots (
                    agent_type, node_id, ts, kind, data
                ) VALUES (?, ?, ?, ?, ?)
            """, [atype, node_id, ts, kind, data_blob])

    def ingest_heartbeat(self, hb: dict[str, Any]) -> None:
        """Insert one heartbeat row. Append-only; (agent_type, node_id, ts) PK
        means duplicate timestamps are silently ignored (the daemon only sends
        one heartbeat per interval anyway)."""
        node_id = hb.get("node_id")
        ts = hb.get("ts")
        if not node_id or not ts:
            raise ValueError("heartbeat must include 'node_id' and 'ts'")
        atype = hb.get("agent_type") or "openclaw"
        data_blob = _to_blob({k: v for k, v in hb.items()
                              if k not in {"node_id", "ts", "agent_type",
                                           "version", "e2e", "size_mb",
                                           "events_total"}})
        with self._write_lock:
            self._conn.execute("""
                INSERT OR IGNORE INTO heartbeats (
                    agent_type, node_id, ts, version, e2e, size_mb,
                    events_total, data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                atype, node_id, ts,
                hb.get("version"),
                bool(hb.get("e2e")),
                hb.get("local_store_size_mb") or hb.get("size_mb"),
                (hb.get("local_store") or {}).get("events_total")
                  if isinstance(hb.get("local_store"), dict) else hb.get("events_total"),
                data_blob,
            ])

    # ── spans (OTel trace ingest) ───────────────────────────────────────
    #
    # Issue #1007 / epic #1006. Spans land here from the OTLP /v1/traces
    # receiver (see ``dashboard.py:_process_otlp_traces`` → ``_otel_to_row``
    # → ``put_span``). We accept a permissive dict-shape so producers other
    # than OTel-proto can write spans directly without dragging a protobuf
    # dependency through this module (e.g. tests, future OpenClaw/Claude
    # Code adapters).
    #
    # Cross-process safety: spans are upserted synchronously under
    # ``_write_lock`` — same path as ``ingest_session`` / ``ingest_cron`` /
    # ``ingest_heartbeat`` (the non-event helpers). Volume per /v1/traces
    # POST is bounded (~hundreds of spans batch, not the multi-kHz
    # tool-call stream that needs the ring), so we don't gain anything
    # from a flusher queue here and we get strong "after POST 200, span is
    # in DuckDB" semantics for free.

    def ingest_span(self, span: dict[str, Any]) -> None:
        """Upsert one OTel-shaped span row.

        Required keys: ``span_id``, ``trace_id``, ``name``, ``start_ts``.
        ``start_ts`` is unix-seconds (float). ``end_ts`` defaults to
        ``start_ts`` when missing (zero-duration span — valid for
        events/markers).

        Optional shape (all coerced gracefully when absent):
          * Identity: ``parent_span_id``, ``agent_type`` (default
            ``"openclaw"``), ``agent_id`` (default ``"main"``), ``node_id``,
            ``session_id``, ``service_name``
          * Status: ``kind``, ``status`` (free-form), ``status_code`` /
            ``status_message`` (OTel-shaped)
          * Metrics: ``duration_ms``, ``duration_ns``, ``cost_usd``,
            ``token_count``, ``tokens_input``, ``tokens_output``, ``model``,
            ``tool_name``
          * JSON payloads: ``input``, ``output``, ``attributes``, ``events``,
            ``links`` — accept dict / list / str / bytes; coerced to BLOB
            via ``_to_blob`` and decoded back via ``_decode_data_blob_rows``
            equivalent in ``query_spans``.

        ``INSERT OR REPLACE`` semantics: re-delivering the same ``span_id``
        overwrites the prior row. OTel exporters retry on transient 5xx,
        so idempotency is essential; making it ON CONFLICT DO REPLACE
        (rather than DO NOTHING) means a retry that carries late-arriving
        ``end_ts`` correctly overwrites the half-row from the first try.

        Also exposed as ``put_span`` for symmetry with the helper name the
        issue body uses (``local_store.put_span``).
        """
        if self._read_only:
            raise RuntimeError("local_store: ingest_span() called on read-only store")
        span_id = span.get("span_id")
        if not span_id:
            raise ValueError("span must include 'span_id'")
        trace_id = span.get("trace_id")
        if not trace_id:
            raise ValueError("span must include 'trace_id'")
        name = span.get("name")
        if not name:
            raise ValueError("span must include 'name'")
        start_ts = span.get("start_ts")
        if start_ts is None:
            raise ValueError("span must include 'start_ts'")
        try:
            start_ts_f = float(start_ts)
        except (TypeError, ValueError):
            raise ValueError(f"span 'start_ts' must be numeric (got {start_ts!r})")
        end_ts = span.get("end_ts")
        try:
            end_ts_f = float(end_ts) if end_ts is not None else start_ts_f
        except (TypeError, ValueError):
            end_ts_f = start_ts_f
        # Duration: prefer explicit, else derive from (end - start).
        duration_ms = span.get("duration_ms")
        duration_ns = span.get("duration_ns")
        if duration_ms is None and duration_ns is None:
            duration_ms = max(0.0, (end_ts_f - start_ts_f) * 1000.0)
        elif duration_ms is None and duration_ns is not None:
            try:
                duration_ms = float(duration_ns) / 1_000_000.0
            except (TypeError, ValueError):
                duration_ms = None
        elif duration_ns is None and duration_ms is not None:
            try:
                duration_ns = int(float(duration_ms) * 1_000_000)
            except (TypeError, ValueError):
                duration_ns = None

        def _i(v):
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        def _f(v):
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        params = [
            str(span_id),
            str(trace_id),
            span.get("parent_span_id"),
            str(span.get("agent_type") or "openclaw"),
            str(span.get("agent_id") or "main"),
            span.get("node_id"),
            span.get("session_id"),
            span.get("service_name"),
            str(name),
            span.get("kind"),
            span.get("status_code"),
            span.get("status_message"),
            span.get("status"),
            start_ts_f,
            end_ts_f,
            _f(duration_ms),
            _i(duration_ns),
            span.get("model"),
            span.get("tool_name"),
            _f(span.get("cost_usd")),
            _i(span.get("token_count")),
            _i(span.get("tokens_input")),
            _i(span.get("tokens_output")),
            _to_blob(span.get("input")),
            _to_blob(span.get("output")),
            _to_blob(span.get("attributes")),
            _to_blob(span.get("events")),
            _to_blob(span.get("links")),
            start_ts_f,  # ts = canonical retention key, mirror of start_ts
            int(time.time() * 1000),
        ]
        # DuckDB doesn't support ON CONFLICT DO REPLACE; emulate with
        # DELETE-then-INSERT inside one transaction. Same pattern works for
        # ``INSERT OR REPLACE`` semantics without losing the FK-free PK
        # constraint enforcement.
        with self._write_lock:
            with _txn(self._conn):
                self._conn.execute(
                    "DELETE FROM spans WHERE span_id = ?",
                    [str(span_id)],
                )
                self._conn.execute("""
                    INSERT INTO spans (
                        span_id, trace_id, parent_span_id, agent_type, agent_id,
                        node_id, session_id, service_name, name, kind,
                        status_code, status_message, status,
                        start_ts, end_ts, duration_ms, duration_ns,
                        model, tool_name, cost_usd, token_count,
                        tokens_input, tokens_output,
                        input, output, attributes, events, links,
                        ts, created_at
                    ) VALUES (?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?,
                              ?, ?, ?,
                              ?, ?, ?, ?,
                              ?, ?, ?, ?,
                              ?, ?,
                              ?, ?, ?, ?, ?,
                              ?, ?)
                """, params)

    # Alias used by the issue body / callers that prefer "put" semantics.
    def put_span(self, span: dict[str, Any]) -> None:
        """Alias for :meth:`ingest_span`. Provided so the OTLP receiver can
        call ``local_store.get_store().put_span(...)`` per the issue spec
        without us painting the rest of the module a different colour."""
        self.ingest_span(span)

    def query_spans(
        self,
        *,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        agent_type: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Read spans. Defaults to most recent first (by ``start_ts DESC``).

        Filters compose with AND. ``since`` / ``until`` are unix-second
        floats matching the ``start_ts`` / ``end_ts`` column type. Pass
        ``trace_id`` to fetch one trace's spans (the trace-tree UI's
        canonical query).

        BLOB columns (``input``, ``output``, ``attributes``, ``events``,
        ``links``) are decoded back to JSON dict/list where the stored
        bytes parse, plain str when they don't, ``None`` when empty.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if trace_id:
            clauses.append("trace_id = ?")
            params.append(str(trace_id))
        if span_id:
            clauses.append("span_id = ?")
            params.append(str(span_id))
        if parent_span_id:
            clauses.append("parent_span_id = ?")
            params.append(str(parent_span_id))
        if session_id:
            clauses.append("session_id = ?")
            params.append(str(session_id))
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(str(agent_id))
        if agent_type:
            clauses.append("agent_type = ?")
            params.append(str(agent_type))
        if since is not None:
            clauses.append("start_ts >= ?")
            params.append(float(since))
        if until is not None:
            clauses.append("start_ts <= ?")
            params.append(float(until))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT span_id, trace_id, parent_span_id, agent_type, agent_id,
                   node_id, session_id, service_name, name, kind,
                   status_code, status_message, status,
                   start_ts, end_ts, duration_ms, duration_ns,
                   model, tool_name, cost_usd, token_count,
                   tokens_input, tokens_output,
                   input, output, attributes, events, links,
                   ts
            FROM spans
            {where}
            ORDER BY start_ts DESC, span_id DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = [
            "span_id", "trace_id", "parent_span_id", "agent_type", "agent_id",
            "node_id", "session_id", "service_name", "name", "kind",
            "status_code", "status_message", "status",
            "start_ts", "end_ts", "duration_ms", "duration_ns",
            "model", "tool_name", "cost_usd", "token_count",
            "tokens_input", "tokens_output",
            "input", "output", "attributes", "events", "links",
            "ts",
        ]
        blob_cols = ("input", "output", "attributes", "events", "links")
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            for c in blob_cols:
                raw = d.get(c)
                if raw is None:
                    continue
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    try:
                        d[c] = json.loads(text)
                    except (ValueError, TypeError):
                        d[c] = text
                except UnicodeDecodeError:
                    d[c] = None
            out.append(d)
        return out

    def query_recent_spans(
        self,
        *,
        limit: int = 50,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """MOAT issue #1364: read-side surface for spans we already store.

        Thin convenience wrapper over :meth:`query_spans` returning the most
        recent spans (``start_ts DESC``) optionally filtered by session.
        Shape is purpose-built for the dashboard ``/api/spans`` endpoint and
        the Brain-tab "Spans" table — only the columns the table renders are
        guaranteed to be present, so we don't promise BLOB fidelity here
        (callers wanting full ``input/output/attrs`` should hit
        :meth:`query_spans` directly).

        Args:
          limit: Max rows to return (clamped 1-500 by the route layer).
          session_id: Optional session filter — when set, returns spans for
            that one OpenClaw session.
        """
        rows = self.query_spans(
            session_id=session_id,
            limit=int(limit),
        )
        # Project to the contract the UI table reads. Keep the BLOB columns
        # present (already decoded by query_spans) so a future detail-drawer
        # has them without a second round-trip.
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append({
                "span_id":         r.get("span_id"),
                "parent_span_id":  r.get("parent_span_id"),
                "trace_id":        r.get("trace_id"),
                "name":            r.get("name"),
                "kind":            r.get("kind"),
                "session_id":      r.get("session_id"),
                "service_name":    r.get("service_name"),
                "start_time":      r.get("start_ts"),
                "end_time":        r.get("end_ts"),
                "duration_ms":     r.get("duration_ms"),
                "status":          r.get("status"),
                "model":           r.get("model"),
                "tool_name":       r.get("tool_name"),
                "cost_usd":        r.get("cost_usd"),
                "tokens_input":    r.get("tokens_input"),
                "tokens_output":   r.get("tokens_output"),
                "attrs":           r.get("attributes"),
                "events":          r.get("events"),
            })
        return out

    def query_recent_read_tool_calls(
        self,
        *,
        since: str | None = None,
        limit: int = 50_000,
    ) -> list[dict[str, Any]]:
        """Tier-1 MOAT (issue #1364): /api/skills fidelity fast-path.

        Returns one row per Read-tool invocation since ``since`` (ISO-8601
        timestamp), shape ``{ts, session_id, file_path}``. Used by
        ``routes/skills.py`` to count "body fetched" + "linked file read"
        events per skill without walking every session JSONL on disk
        (the legacy scanner re-opens 50-200+ files on every page render).

        Tool-call shapes covered (all three appear in the wild):
          * v3 top-level events with ``event_type`` in
            ``{'tool.call', 'toolCall', 'tool_use'}`` — read from
            ``data.input.file_path`` / ``data.arguments.file_path``.
          * Assistant ``message`` events with
            ``data.toolMetas[*].input.file_path`` (PR #1132 trajectory
            parser shape).
          * Legacy assistant message events whose
            ``data.message.content[*]`` still carries raw
            ``{type:'toolCall'|'tool_use', name, input/arguments}`` blocks
            (older OpenClaw transcripts that pre-date PR #1132's
            trajectory projection).

        Tool name is matched case-insensitively against
        ``{'read', 'readfile', 'read_file'}`` — same set the legacy
        ``_scan_fidelity_events`` checked. The ``file_path`` argument is
        pulled from the first non-empty of ``file_path`` / ``path`` /
        ``filename`` (Anthropic SDK + OpenClaw both shapes seen).

        Rows where no Read-tool path can be extracted are dropped so the
        caller iterates only useful events.

        ``limit`` clamps total returned rows; defaults to 50k which is
        ~1 million-token agent-week worth of Read calls. Callers should
        pass a 7d ``since`` to keep the result set bounded.
        """
        try:
            lim = int(limit)
        except (TypeError, ValueError):
            lim = 50_000
        lim = max(1, min(200_000, lim))

        clauses: list[str] = [
            "(event_type IN ('tool.call', 'toolCall', 'tool_use')"
            " OR event_type = 'message')"
        ]
        params: list[Any] = []
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT ts, session_id, event_type, data
            FROM events
            {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(lim)

        out: list[dict[str, Any]] = []
        for ts, sid, ev_type, raw in self._fetch(sql, params):
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    continue

            for path in _iter_read_tool_paths(ev_type, data):
                out.append({
                    "ts":         ts,
                    "session_id": sid,
                    "file_path":  path,
                })
        return out

    def query_tool_call_invocations(
        self,
        *,
        since: str | None = None,
        limit: int = 50_000,
    ) -> list[dict[str, Any]]:
        """Tier-1 MOAT: /api/plugins fast-path.

        Returns one row per tool invocation since ``since`` (ISO-8601
        timestamp), shape ``{ts, name}``. Used by ``routes/plugins.py`` to
        count per-plugin invocations over the last 30d without re-walking
        every session JSONL on every Plugins-tab render (the legacy scanner
        re-opens up to 60 files per request and parses every line).

        Tool-call shapes covered (matches :func:`_iter_tool_invocation_names`):
          * Top-level events with ``event_type`` in
            ``{'tool.call', 'toolCall', 'tool_use'}`` — uses ``data.name``.
          * Assistant ``message`` events with
            ``data.toolMetas[*].name`` (PR #1132 trajectory parser shape).
          * Legacy assistant message events whose
            ``data.message.content[*]`` carries raw
            ``{type:'toolCall'|'tool_use', name}`` blocks (older OpenClaw
            transcripts that pre-date PR #1132's trajectory projection).

        Tool name is returned verbatim (lower-cased by the caller). Rows
        with no extractable name are dropped.

        ``limit`` clamps total returned rows; defaults to 50k which covers
        a busy agent-month worth of tool calls. Callers should pass a 30d
        ``since`` to keep the result set bounded.
        """
        try:
            lim = int(limit)
        except (TypeError, ValueError):
            lim = 50_000
        lim = max(1, min(200_000, lim))

        clauses: list[str] = [
            "(event_type IN ('tool.call', 'toolCall', 'tool_use')"
            " OR event_type = 'message')"
        ]
        params: list[Any] = []
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT ts, event_type, data
            FROM events
            {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(lim)

        out: list[dict[str, Any]] = []
        for ts, ev_type, raw in self._fetch(sql, params):
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    continue

            for name in _iter_tool_invocation_names(ev_type, data):
                out.append({"ts": ts, "name": name})
        return out

    # ── flush ───────────────────────────────────────────────────────────

    def _flusher_loop(self) -> None:
        while not self._flusher_stop.is_set():
            self._flusher_stop.wait(FLUSH_INTERVAL_SECS)
            try:
                self._flush_now()
            except Exception:
                log.exception("local store: flush failed (will retry)")

    def _flush_now(self) -> int:
        """Drain the ring into DuckDB in one transaction. Returns rows written.
        Snapshot-then-pop pattern: events stay in the ring until the COMMIT
        succeeds, so a write failure leaves them queued for the next attempt
        instead of vanishing."""
        with self._ring_lock:
            if not self._ring:
                return 0
            batch = list(self._ring)
        rows = [_event_to_row(e) for e in batch]
        with self._write_lock:
            with _txn(self._conn):
                self._conn.executemany(
                    """
                    INSERT OR IGNORE INTO events
                      (id, agent_type, node_id, agent_id, session_id, workspace_id,
                       event_type, ts, data, cost_usd, token_count, model, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    rows,
                )
        with self._ring_lock:
            for _ in range(len(batch)):
                if self._ring:
                    self._ring.popleft()
        self._last_flush_ts = time.monotonic()
        # Issue #1343 Phase 2.2 — kick the approvals watcher when a tool_call
        # row just landed. The watcher_loop reads from DuckDB; the COMMIT
        # above is what makes the row visible to it. Kicking before the
        # commit would race the watcher to an empty read. Coalesces inside
        # approvals._kick_event so a 50-event burst → 1 wakeup.
        for e in batch:
            et = e.get("event_type")
            if et == "tool_call" or et == "toolCall":
                try:
                    from clawmetry import approvals as _approvals
                    _approvals.watcher_kick()
                except Exception:
                    pass  # partial install / approvals.py not importable
                break  # one kick per batch; coalesces N events into 1 wake
        return len(rows)

    # ── queries ─────────────────────────────────────────────────────────

    def query_events(
        self,
        *,
        session_id: str | None = None,
        agent_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Read events. Defaults to most recent first."""
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT id, agent_type, node_id, agent_id, session_id, workspace_id,
                   event_type, ts, data, cost_usd, token_count, model
            FROM events
            {where}
            ORDER BY ts DESC, id DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [_row_to_event(r, _EVENT_COLS) for r in self._fetch(sql, params)]

    def query_sessions(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """One row per distinct session_id seen, with start/end timestamps,
        event count, and total cost."""
        clauses: list[str] = ["session_id IS NOT NULL"]
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT
              session_id,
              MIN(agent_id)               AS agent_id,
              MIN(ts)                     AS started_at,
              MAX(ts)                     AS updated_at,
              COUNT(*)                    AS event_count,
              COALESCE(SUM(cost_usd), 0)  AS cost_usd,
              COALESCE(SUM(token_count), 0) AS token_count
            FROM events
            {where}
            GROUP BY session_id
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [_row_to_dict(r, ["session_id","agent_id","started_at","updated_at",
                                  "event_count","cost_usd","token_count"])
                for r in self._fetch(sql, params)]

    def query_heartbeats(
        self,
        *,
        node_id: str | None = None,
        agent_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Read heartbeat rows. Defaults to most recent first.

        Each row is a single daemon liveness ping (one per heartbeat
        interval, typically every 60s). Use ``since=<iso ts>`` to filter to
        a recent window (e.g. last 24h). The ``data`` BLOB is decoded back
        to a JSON dict when valid, str otherwise, None when empty.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if node_id:
            clauses.append("node_id = ?")
            params.append(node_id)
        if agent_type:
            clauses.append("agent_type = ?")
            params.append(agent_type)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT agent_type, node_id, ts, version, e2e, size_mb,
                   events_total, data
            FROM heartbeats
            {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["agent_type", "node_id", "ts", "version", "e2e", "size_mb",
                "events_total", "data"]
        return _decode_data_blob_rows(self._fetch(sql, params), cols)

    def query_channels(
        self,
        *,
        session_id: str | None = None,
        channel: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """OpenClaw channel context per session (Telegram/Slack/etc.)."""
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?"); params.append(session_id)
        if channel:
            clauses.append("channel = ?"); params.append(channel)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT session_id, channel, chat_type, subject, origin_label
            FROM openclaw_channels
            {where}
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["session_id", "channel", "chat_type", "subject", "origin_label"]
        return [_row_to_dict(r, cols) for r in self._fetch(sql, params)]

    def query_flow_runs(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Aggregate historical flow runs from the ``events`` table.

        A "flow run" is one session's worth of events. For each session we
        compute the start time, total duration, distinct models invoked,
        tool-call count, total cost, and a left-joined channel from the
        ``openclaw_channels`` per-session metadata table.

        Status is heuristic: any event with ``event_type LIKE '%error%'``
        flips the run to ``failed``; otherwise ``completed``. We don't try
        to detect "in-progress" here — the live Flow view is the source of
        truth for that.

        Ordered most-recent first (by ``MAX(ts)``). Issue #611.
        """
        clauses: list[str] = ["e.session_id IS NOT NULL"]
        params: list[Any] = []
        if agent_id:
            clauses.append("e.agent_id = ?")
            params.append(agent_id)
        if since:
            clauses.append("e.ts >= ?")
            params.append(since)
        if until:
            clauses.append("e.ts <= ?")
            params.append(until)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT
              e.session_id                              AS session_id,
              MIN(e.agent_id)                           AS agent_id,
              MIN(e.ts)                                 AS started_at,
              MAX(e.ts)                                 AS updated_at,
              COUNT(*)                                  AS event_count,
              COUNT(DISTINCT e.model)
                  FILTER (WHERE e.model IS NOT NULL)    AS models_invoked,
              LIST(DISTINCT e.model)
                  FILTER (WHERE e.model IS NOT NULL)    AS model_list,
              COUNT(*) FILTER (WHERE
                  e.event_type IN ('tool_call', 'toolCall', 'tool_use'))
                                                        AS tools_called,
              COALESCE(SUM(e.cost_usd), 0)              AS total_cost,
              COALESCE(SUM(e.token_count), 0)           AS token_count,
              MAX(CASE WHEN LOWER(e.event_type) LIKE '%error%'
                       THEN 1 ELSE 0 END)               AS has_error,
              MIN(c.channel)                            AS channel
            FROM events e
            LEFT JOIN openclaw_channels c
              ON c.session_id = e.session_id
            {where}
            GROUP BY e.session_id
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = [
            "session_id", "agent_id", "started_at", "updated_at",
            "event_count", "models_invoked", "model_list", "tools_called",
            "total_cost", "token_count", "has_error", "channel",
        ]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            row = dict(zip(cols, r))
            started = row.get("started_at") or ""
            ended = row.get("updated_at") or ""
            row["duration_seconds"] = _duration_seconds(started, ended)
            row["status"] = "failed" if row.pop("has_error", 0) else "completed"
            ml = row.pop("model_list", None) or []
            # DuckDB LIST returns a Python list already; coerce just in case.
            try:
                row["models"] = [str(m) for m in ml if m]
            except TypeError:
                row["models"] = []
            row["channels_touched"] = 1 if row.get("channel") else 0
            out.append(row)
        return out

    def query_channel_messages(
        self,
        *,
        provider: str | None = None,
        channel_id: str | None = None,
        since: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Read channel-message rows (issue #1088 Phase 4).

        Returns rows ordered most-recent first. The ``raw_blob`` BLOB is
        decoded back to JSON dict where possible, str otherwise, None when
        empty — same convention as the other ``data``-blob tables so callers
        can hand the row straight to the API without a second decode.

        Filters:
          * ``provider`` — exact match, lowercased (``"telegram"`` etc.).
          * ``channel_id`` — exact match (e.g. Telegram chat id, Slack
            channel id, Discord guild+channel composite).
          * ``since`` — ISO-8601 timestamp; rows with ``ts >= since``.

        Defaults to ``limit=50`` to mirror the existing per-channel route's
        page size — the dashboard's "messages" panes show 50 messages by
        default and lazy-load older ones via the offset query param the
        legacy path supports.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if provider:
            clauses.append("provider = ?")
            params.append(str(provider).lower().strip())
        if channel_id:
            clauses.append("channel_id = ?")
            params.append(str(channel_id))
        if since:
            clauses.append("ts >= ?")
            params.append(str(since))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT id, agent_id, provider, channel_id, sender_id, sender_name,
                   body, ts, direction, session_key, raw_blob
            FROM channel_messages
            {where}
            ORDER BY ts DESC, id DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["id", "agent_id", "provider", "channel_id", "sender_id",
                "sender_name", "body", "ts", "direction", "session_key",
                "raw_blob"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            raw = d.get("raw_blob")
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    try:
                        d["raw_blob"] = json.loads(text)
                    except (ValueError, TypeError):
                        d["raw_blob"] = text
                except UnicodeDecodeError:
                    d["raw_blob"] = None
            out.append(d)
        return out

    def query_channel_threads(
        self,
        *,
        provider: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Per-thread (per ``channel_id``) summary for one provider
        (issue #1088 Phase 4).

        Returns one row per distinct ``channel_id`` ordered by most-recent
        activity. Each row carries the latest sender, latest body snippet,
        and total inbound / outbound counts so the cloud UI's "threads"
        panel can render without a second fetch.

        Why a dedicated helper instead of asking the route to GROUP BY:
        DuckDB's columnar engine makes this a single scan, but the result
        shape is route-specific (we drop the raw_blob; we project a snippet
        column). Keeping the SQL here means the future WS relay can expose
        the same shape verbatim.
        """
        if not provider:
            return []
        sql = """
            SELECT
              channel_id,
              MAX(ts)                                        AS last_ts,
              ARG_MAX(sender_name, ts)                       AS last_sender,
              ARG_MAX(body, ts)                              AS last_body,
              ARG_MAX(direction, ts)                         AS last_direction,
              ARG_MAX(session_key, ts)                       AS session_key,
              SUM(CASE WHEN direction = 'in'  THEN 1 ELSE 0 END) AS msg_in,
              SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END) AS msg_out,
              COUNT(*)                                       AS total
            FROM channel_messages
            WHERE provider = ?
              AND channel_id IS NOT NULL
            GROUP BY channel_id
            ORDER BY last_ts DESC
            LIMIT ?
        """
        rows = self._fetch(
            sql, [str(provider).lower().strip(), int(limit)]
        )
        cols = ["channel_id", "last_ts", "last_sender", "last_body",
                "last_direction", "session_key", "msg_in", "msg_out", "total"]
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(zip(cols, r))
            # Cap snippet at 200 chars so the threads pane stays compact
            # — the full body is one query away via query_channel_messages.
            body = d.get("last_body") or ""
            if isinstance(body, str) and len(body) > 200:
                d["last_body"] = body[:200]
            d["msg_in"]  = int(d.get("msg_in")  or 0)
            d["msg_out"] = int(d.get("msg_out") or 0)
            d["total"]   = int(d.get("total")   or 0)
            out.append(d)
        return out

    def query_channel_summary(
        self,
        *,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Cross-provider counts for the channels overview tab
        (issue #1088 Phase 4).

        Returns one row per provider with inbound / outbound counts and the
        most-recent activity timestamp. Powers ``/api/channels/summary``,
        which the cloud-side channels overview page hits on every nav.

        ``agent_id`` scopes the result to a single agent instance; ``None``
        sums across the local node.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(str(agent_id))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT
              provider,
              COUNT(*)                                          AS total,
              SUM(CASE WHEN direction = 'in'  THEN 1 ELSE 0 END) AS msg_in,
              SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END) AS msg_out,
              COUNT(DISTINCT channel_id)                        AS distinct_channels,
              MAX(ts)                                           AS last_ts
            FROM channel_messages
            {where}
            GROUP BY provider
            ORDER BY last_ts DESC NULLS LAST
        """
        cols = ["provider", "total", "msg_in", "msg_out",
                "distinct_channels", "last_ts"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            d["total"]             = int(d.get("total")             or 0)
            d["msg_in"]            = int(d.get("msg_in")            or 0)
            d["msg_out"]           = int(d.get("msg_out")           or 0)
            d["distinct_channels"] = int(d.get("distinct_channels") or 0)
            out.append(d)
        return out

    def query_crons(
        self,
        *,
        agent_type: str | None = None,
        agent_id: str | None = None,
        enabled_only: bool = False,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Cron jobs registered with the agent gateway."""
        clauses: list[str] = []
        params: list[Any] = []
        if agent_type:
            clauses.append("agent_type = ?"); params.append(agent_type)
        if agent_id:
            clauses.append("agent_id = ?"); params.append(agent_id)
        if enabled_only:
            clauses.append("enabled = TRUE")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT agent_type, cron_id, agent_id, name, schedule, enabled,
                   last_run_at, last_status, next_run_at, data, updated_at
            FROM crons
            {where}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["agent_type", "cron_id", "agent_id", "name", "schedule",
                "enabled", "last_run_at", "last_status", "next_run_at",
                "data", "updated_at"]
        return _decode_data_blob_rows(self._fetch(sql, params), cols)

    def query_cron_runs(
        self,
        *,
        job_id: str | None = None,
        agent_type: str | None = None,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Per-job cron-run timeline (issue #605 DuckDB follow-up).

        Returns rows most-recent-first (``ORDER BY started_at DESC``). The
        ``data`` BLOB carries the freeform per-run extras (``usage`` dict
        with input/output token split, gateway-specific fields) and is
        decoded back to a dict where possible — same shape contract as
        ``query_crons``.

        ``limit`` defaults to 50 (one page in the timeline UI) and is
        clamped to ``[1, 500]``. Callers wanting a full sweep should
        page; we deliberately keep the upper bound modest so a buggy
        client can't yank megabytes of run history in one shot."""
        clauses: list[str] = []
        params: list[Any] = []
        if job_id:
            clauses.append("job_id = ?"); params.append(str(job_id))
        if agent_type:
            clauses.append("agent_type = ?"); params.append(agent_type)
        if agent_id:
            clauses.append("agent_id = ?"); params.append(agent_id)
        if since:
            clauses.append("started_at >= ?"); params.append(since)
        if until:
            clauses.append("started_at <= ?"); params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        try:
            lim = int(limit)
        except (TypeError, ValueError):
            lim = 50
        lim = max(1, min(500, lim))
        sql = f"""
            SELECT id, node_id, agent_type, agent_id, job_id,
                   started_at, ended_at, duration_ms, status, error_message,
                   token_count, cost_usd, delivered_at, next_run_at,
                   raw_jsonl_line, data, created_at
            FROM cron_runs
            {where}
            ORDER BY started_at DESC, id DESC
            LIMIT ?
        """
        params.append(lim)
        cols = ["id", "node_id", "agent_type", "agent_id", "job_id",
                "started_at", "ended_at", "duration_ms", "status",
                "error_message", "token_count", "cost_usd",
                "delivered_at", "next_run_at", "raw_jsonl_line",
                "data", "created_at"]
        return _decode_data_blob_rows(self._fetch(sql, params), cols)

    def query_subagents(
        self,
        *,
        parent_session_id: str | None = None,
        agent_type: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Subagent rollup rows."""
        clauses: list[str] = []
        params: list[Any] = []
        if parent_session_id:
            clauses.append("parent_session_id = ?"); params.append(parent_session_id)
        if agent_type:
            clauses.append("agent_type = ?"); params.append(agent_type)
        if status:
            clauses.append("status = ?"); params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT agent_type, subagent_id, parent_session_id, spawned_at,
                   ended_at, task, status, cost_usd, token_count, data, updated_at
            FROM subagents
            {where}
            ORDER BY spawned_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["agent_type", "subagent_id", "parent_session_id", "spawned_at",
                "ended_at", "task", "status", "cost_usd", "token_count",
                "data", "updated_at"]
        return _decode_data_blob_rows(self._fetch(sql, params), cols)

    def query_channel_configs(
        self,
        *,
        provider: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Channel-adapter config rows (epic #1032 Phase 5).

        Returns one dict per provider with the FULL row including the
        ``config_json_encrypted`` BLOB (caller is responsible for decryption
        on the local node — cloud must never call this with the blob field
        attached to a wire response). The blob comes back as ``bytes`` or
        ``None`` when no config has been pushed yet.

        Use :meth:`query_channel_config_status` instead when you only need
        the non-secret status summary (``enabled``, ``last_test_at``,
        ``last_test_ok``, ``last_test_error``). That helper omits the blob
        so it's safe to feed straight into a cache_push payload."""
        clauses: list[str] = []
        params: list[Any] = []
        if provider:
            clauses.append("provider = ?"); params.append(str(provider).lower().strip())
        if enabled_only:
            clauses.append("enabled = TRUE")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT provider, enabled, config_json_encrypted,
                   last_test_at, last_test_ok, last_test_error, updated_at
            FROM channel_config
            {where}
            ORDER BY provider ASC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["provider", "enabled", "config_json_encrypted",
                "last_test_at", "last_test_ok", "last_test_error", "updated_at"]
        return [_row_to_dict(r, cols) for r in self._fetch(sql, params)]

    def query_channel_config_status(
        self,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """Non-secret status summary for one or all providers (epic #1032
        Phase 5). Always omits ``config_json_encrypted`` so callers don't
        accidentally leak ciphertext into cache_push payloads. When
        ``provider`` is None returns a row per configured provider; with a
        provider filter returns at most one row."""
        clauses: list[str] = []
        params: list[Any] = []
        if provider:
            clauses.append("provider = ?"); params.append(str(provider).lower().strip())
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT provider, enabled, last_test_at, last_test_ok,
                   last_test_error, updated_at
            FROM channel_config
            {where}
            ORDER BY provider ASC
        """
        cols = ["provider", "enabled", "last_test_at", "last_test_ok",
                "last_test_error", "updated_at"]
        return [_row_to_dict(r, cols) for r in self._fetch(sql, params)]

    def query_alert_rules(
        self,
        *,
        owner_hash: str | None = None,
        enabled_only: bool = False,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Read alert-rule rows. Defaults to most-recently-updated first.

        ``owner_hash`` scopes the result to one cm_ token (sha256 of the
        token). ``enabled_only=True`` filters to ``enabled=TRUE``. The
        ``condition_json`` BLOB is decoded back to a JSON dict where
        valid (str otherwise, None when empty) so callers can drop the
        whole row into ``/api/alerts/rules`` without a second decode."""
        clauses: list[str] = []
        params: list[Any] = []
        if owner_hash:
            clauses.append("owner_hash = ?")
            params.append(owner_hash)
        if enabled_only:
            clauses.append("enabled = TRUE")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT id, owner_hash, name, condition_json, enabled,
                   created_at, updated_at, last_fired_at, fire_count
            FROM alert_rules
            {where}
            ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST, id
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["id", "owner_hash", "name", "condition_json", "enabled",
                "created_at", "updated_at", "last_fired_at", "fire_count"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            raw = d.get("condition_json")
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    try:
                        d["condition_json"] = json.loads(text)
                    except (ValueError, TypeError):
                        d["condition_json"] = text
                except UnicodeDecodeError:
                    d["condition_json"] = None
            out.append(d)
        return out

    def query_approvals(
        self,
        *,
        owner_hash: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Read approval-queue rows. Defaults to most-recently-created first.

        ``owner_hash`` scopes the result to one cm_ token (sha256 of the
        token). ``status`` filters by stage (``pending`` / ``approved`` /
        ``denied`` / …). The ``args`` BLOB is decoded back to a JSON dict
        where valid (str otherwise, None when empty) so callers can hand
        the row straight to the API without a second decode."""
        clauses: list[str] = []
        params: list[Any] = []
        if owner_hash:
            clauses.append("owner_hash = ?")
            params.append(owner_hash)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT id, owner_hash, requestor_session_id, action, args,
                   status, created_at, resolved_at, resolver, decision,
                   decision_reason
            FROM approvals
            {where}
            ORDER BY COALESCE(created_at, '') DESC, id
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["id", "owner_hash", "requestor_session_id", "action", "args",
                "status", "created_at", "resolved_at", "resolver",
                "decision", "decision_reason"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            raw = d.get("args")
            if raw is not None:
                try:
                    text = (raw.decode("utf-8")
                            if isinstance(raw, (bytes, bytearray)) else raw)
                    try:
                        d["args"] = json.loads(text)
                    except (ValueError, TypeError):
                        d["args"] = text
                except UnicodeDecodeError:
                    d["args"] = None
            out.append(d)
        return out

    def query_memory_blobs(
        self,
        *,
        agent_type: str | None = None,
        agent_id: str | None = None,
        path_prefix: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Read memory-blob rows. Defaults to most recent first.

        Each row mirrors the ``memory_blobs`` schema columns
        (``agent_type``, ``agent_id``, ``path``, ``ts``, ``blob``,
        ``sha256``, ``size_bytes``, ``updated_at``). The ``blob`` BLOB
        is decoded back to a UTF-8 string when valid (memory files are
        always plaintext markdown — CLAUDE.md, SOUL.md, memory/*.md);
        leaves it as ``bytes`` if decoding fails, ``None`` when empty.

        Filters:
          - ``agent_type``: exact match on the framework discriminator
            (e.g. ``"openclaw"``, ``"claude_code"``).
          - ``agent_id``: exact match on the instance within that
            framework (``"main"``, ``"subagent"``, ``"cron"``).
          - ``path_prefix``: SQL ``LIKE prefix%`` on the path column —
            useful for scoping to ``"memory/"`` daily files vs root
            workspace files.

        Sort order matches the other ``query_*`` methods: most-recently-
        updated first. ``LIMIT 200`` default mirrors ``query_subagents``."""
        clauses: list[str] = []
        params: list[Any] = []
        if agent_type:
            clauses.append("agent_type = ?"); params.append(agent_type)
        if agent_id:
            clauses.append("agent_id = ?"); params.append(agent_id)
        if path_prefix:
            clauses.append("path LIKE ?"); params.append(f"{path_prefix}%")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT agent_type, agent_id, path, ts, blob, sha256,
                   size_bytes, updated_at
            FROM memory_blobs
            {where}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["agent_type", "agent_id", "path", "ts", "blob", "sha256",
                "size_bytes", "updated_at"]
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            d = dict(zip(cols, r))
            raw = d.get("blob")
            if raw is not None:
                try:
                    d["blob"] = (raw.decode("utf-8")
                                 if isinstance(raw, (bytes, bytearray)) else raw)
                except UnicodeDecodeError:
                    # Non-utf8 binary memory file (rare); leave as bytes so
                    # callers can still get the raw payload.
                    d["blob"] = bytes(raw)
            out.append(d)
        return out

    def query_system_snapshots(
        self,
        *,
        node_id: str | None = None,
        kind: str | None = None,
        agent_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """System health snapshots (cpu, mem, disk, gpu rollups)."""
        clauses: list[str] = []
        params: list[Any] = []
        if node_id:
            clauses.append("node_id = ?"); params.append(node_id)
        if kind:
            clauses.append("kind = ?"); params.append(kind)
        if agent_type:
            clauses.append("agent_type = ?"); params.append(agent_type)
        if since:
            clauses.append("ts >= ?"); params.append(since)
        if until:
            clauses.append("ts <= ?"); params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT agent_type, node_id, ts, kind, data
            FROM system_snapshots
            {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(int(limit))
        cols = ["agent_type", "node_id", "ts", "kind", "data"]
        return _decode_data_blob_rows(self._fetch(sql, params), cols)

    def query_sessions_table(
        self,
        *,
        agent_type: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Read rows directly from the typed ``sessions`` table.

        Distinct from :meth:`query_sessions`, which aggregates the events
        table by ``GROUP BY session_id``. The ``sessions`` table is the
        typed-session view written by ``sync.py`` + the daemon — it carries
        title, status, message_count, and a metadata BLOB.

        ``agent_type`` filters rows to a single adapter (e.g. ``"openclaw"``,
        ``"hermes"``) — used by ``/api/agents/<name>/sessions`` to render
        per-adapter session lists from DuckDB.

        Returns one dict per row with ``metadata`` already JSON-decoded
        (``{}`` when missing or invalid). Rows are ordered most-recently-
        active first.

        Used by ``routes/sessions.py:_try_local_store_sessions`` and
        ``routes/overview.py:_try_local_store_overview`` so the SQL lives
        in one place — and so the daemon HTTP proxy
        (``routes/local_query.py:local_store_via_daemon``) can expose it
        for cross-process callers (issue #1088).
        """
        clauses: list[str] = []
        params: list[Any] = []
        if agent_type:
            clauses.append("s.agent_type = ?")
            params.append(str(agent_type))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        # ``sessions.message_count`` is only populated by the typed-session
        # ingest path (sync.py + claude_code adapter). The OpenClaw events
        # path never sets it, so reading the column gave ``message_count: 0``
        # for every OpenClaw session (#1129 bug 4). Compute it on read via a
        # correlated subquery against ``events`` and fall back to the stored
        # column for agents that DO populate it (e.g. ingest from sync.py
        # where the events table may be empty).
        sql = f"""
            SELECT s.agent_type, s.session_id, s.agent_id, s.title, s.started_at,
                   s.last_active_at, s.ended_at, s.status, s.total_tokens, s.cost_usd,
                   GREATEST(
                       COALESCE(s.message_count, 0),
                       (SELECT COUNT(*) FROM events e
                          WHERE e.session_id = s.session_id
                            AND e.agent_type = s.agent_type)
                   ) AS message_count,
                   s.metadata
            FROM sessions s
            {where}
            ORDER BY COALESCE(s.last_active_at, s.started_at) DESC NULLS LAST
            LIMIT ?
        """
        params.append(int(limit))
        rows = self._fetch(sql, params)
        cols = ["agent_type", "session_id", "agent_id", "title", "started_at",
                "last_active_at", "ended_at", "status", "total_tokens",
                "cost_usd", "message_count", "metadata"]
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(zip(cols, r))
            raw = d.get("metadata")
            meta: dict[str, Any] = {}
            if raw:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    meta = json.loads(text) if text else {}
                    if not isinstance(meta, dict):
                        meta = {}
                except (ValueError, TypeError, UnicodeDecodeError):
                    meta = {}
            d["metadata"] = meta
            out.append(d)
        return out

    def query_compactions(
        self,
        *,
        session_id: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Read OpenClaw compaction events (issue #1088 phase 3).

        Compaction events live in the ``events`` table with
        ``event_type='compaction'``. Their ``data`` blob carries the
        original transcript shape: ``{type:"compaction", summary:"...",
        tokensBefore:N, firstKeptEntryId:"...", fromHook:bool,
        timestamp:"..."}``. This helper projects them into the row shape
        ``/api/compactions`` returns so the route doesn't need to re-decode.

        ``session_id`` filters to one session (returns full summary text).
        Defaults to most-recent first."""
        clauses: list[str] = ["event_type = 'compaction'"]
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT session_id, ts, data
            FROM events
            {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(int(limit))
        out: list[dict[str, Any]] = []
        for r in self._fetch(sql, params):
            sid, ts, raw = r
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    data = {}
            out.append({
                "session_id":          sid,
                "timestamp":           data.get("timestamp") or ts or "",
                "summary":             data.get("summary") or "",
                "tokens_before":       int(data.get("tokensBefore") or data.get("tokens_before") or 0),
                "first_kept_entry_id": data.get("firstKeptEntryId") or data.get("first_kept_entry_id") or "",
                "from_hook":           bool(data.get("fromHook") or data.get("from_hook") or False),
            })
        return out

    def query_cost_split(
        self,
        *,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Per-session input/output/cache token + cost split (issue #1088 phase 3).

        Aggregates ``message`` events by ``session_id`` extracting the
        ``data.message.usage`` block — the same structure
        ``/api/cost-split`` walks the JSONL for. Returns one row per
        session ordered by total cost descending.

        ``session_id`` filters to one session (limit ignored). Otherwise
        returns the top ``limit`` sessions by total cost."""
        clauses: list[str] = ["event_type = 'message'"]
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT session_id, model, data
            FROM events
            {where}
            ORDER BY ts ASC
        """
        # Aggregate in Python — DuckDB's JSON extraction would work but we
        # want consistent decoding with query_events (which Python already
        # does), and the row counts here are bounded by limit*~200 turns.
        per_session: dict[str, dict[str, Any]] = {}
        for sid, model, raw in self._fetch(sql, params):
            if not sid:
                continue
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    data = {}
            msg = data.get("message") if isinstance(data.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            if not usage:
                continue
            agg = per_session.setdefault(sid, {
                "session_id":          sid,
                "primary_model":       "",
                "input_tokens":        0,
                "output_tokens":       0,
                "cache_read_tokens":   0,
                "cache_write_tokens":  0,
                "input_cost_usd":      0.0,
                "output_cost_usd":     0.0,
                "cache_read_cost_usd": 0.0,
                "cache_write_cost_usd": 0.0,
                "total_cost_usd":      0.0,
                "_model_tokens":       {},
            })
            agg["input_tokens"]       += int(usage.get("input", 0) or 0)
            agg["output_tokens"]      += int(usage.get("output", 0) or 0)
            agg["cache_read_tokens"]  += int(usage.get("cacheRead", 0) or 0)
            agg["cache_write_tokens"] += int(usage.get("cacheWrite", 0) or 0)
            cost_obj = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
            agg["input_cost_usd"]      += float(cost_obj.get("input", 0) or 0)
            agg["output_cost_usd"]     += float(cost_obj.get("output", 0) or 0)
            agg["cache_read_cost_usd"] += float(cost_obj.get("cacheRead", 0) or 0)
            agg["cache_write_cost_usd"] += float(cost_obj.get("cacheWrite", 0) or 0)
            agg["total_cost_usd"]      += float(cost_obj.get("total", 0) or 0)
            mt = int(usage.get("totalTokens", 0) or 0)
            mm = msg.get("model") or model or ""
            if mt and mm:
                agg["_model_tokens"][mm] = agg["_model_tokens"].get(mm, 0) + mt
        out: list[dict[str, Any]] = []
        for agg in per_session.values():
            mt = agg.pop("_model_tokens", {})
            agg["primary_model"] = (
                max(mt.items(), key=lambda kv: kv[1])[0] if mt else ""
            )
            agg["total_tokens"] = (
                agg["input_tokens"] + agg["output_tokens"]
                + agg["cache_read_tokens"] + agg["cache_write_tokens"]
            )
            input_plus_cache = agg["input_tokens"] + agg["cache_read_tokens"]
            agg["cache_hit_ratio_pct"] = (
                round(agg["cache_read_tokens"] / input_plus_cache * 100, 1)
                if input_plus_cache else 0.0
            )
            # Round cost fields to 6 decimals for consistency with the legacy path.
            for k in ("input_cost_usd", "output_cost_usd", "cache_read_cost_usd",
                      "cache_write_cost_usd", "total_cost_usd"):
                agg[k] = round(agg[k], 6)
            out.append(agg)
        out.sort(key=lambda r: r.get("total_cost_usd", 0), reverse=True)
        if session_id:
            return out
        return out[:int(limit)]

    def query_context_window_peek(
        self,
        *,
        scan_sessions: int = 5,
    ) -> dict[str, Any]:
        """Peak context-window measurement for the latest active session.

        Mirrors the legacy ``/api/context-anatomy`` JSONL scanner that
        walks the most-recent N session files looking for the last
        non-zero ``usage.input_tokens`` reading from a ``message`` event.
        That number represents the live conversation's running context
        size as observed by the model on its most recent turn.

        Why a dedicated query: the existing ``query_cost_split`` returns
        SUMMED input_tokens across the whole session, which is the wrong
        number for a "current context size" gauge — a session with 50
        turns adding 5K each shows 250K (over the 200K window), when
        the actual prompt context never exceeded 50K. The right number
        is the LAST per-turn ``input_tokens`` value the model reported.

        Field-name compatibility: OpenClaw's native JSONL emits
        ``usage.input`` while the Anthropic SDK echo uses
        ``usage.input_tokens``. We accept either, mirroring
        ``clawmetry/sync.py`` and the legacy ``routes/infra.py`` scanner
        (which checked only ``input_tokens`` — fixing that latent gap
        is a free side-effect of the migration).

        Returns ``{"session_id": str, "input_tokens": int, "ts": str}``
        for the most-recent active session that has at least one
        non-zero reading. Returns ``{"input_tokens": 0}`` if nothing is
        observable (fresh DB, no message events yet).

        Args:
            scan_sessions: How many most-recent sessions to walk before
                giving up. Matches the legacy file-scan budget of 5.
        """
        # Step 1: most-recent N sessions ordered by last activity. The
        # session table has updated_at; we use events for the same answer
        # so a single index lookup on ts handles it.
        recent_sessions = self._fetch(
            """
            SELECT session_id, MAX(ts) AS last_ts
            FROM events
            WHERE session_id IS NOT NULL
              AND event_type = 'message'
            GROUP BY session_id
            ORDER BY last_ts DESC
            LIMIT ?
            """,
            [int(scan_sessions)],
        )
        for sid_row in recent_sessions:
            sid, _last_ts = sid_row[0], sid_row[1]
            if not sid:
                continue
            # Step 2: walk this session's message events newest-first
            # until we find the first non-zero reading.
            rows = self._fetch(
                """
                SELECT ts, data
                FROM events
                WHERE session_id = ?
                  AND event_type = 'message'
                ORDER BY ts DESC, id DESC
                """,
                [sid],
            )
            for ts, raw in rows:
                data: dict[str, Any] = {}
                if raw is not None:
                    try:
                        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                        parsed = json.loads(text) if text else {}
                        if isinstance(parsed, dict):
                            data = parsed
                    except (ValueError, TypeError, UnicodeDecodeError):
                        continue
                msg = data.get("message") if isinstance(data.get("message"), dict) else {}
                usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                # Sometimes OpenClaw nests usage at top level — fall through
                if not usage:
                    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                if not usage:
                    continue
                # OpenClaw native field: "input"; Anthropic SDK echo: "input_tokens"
                tok = (
                    usage.get("input_tokens")
                    or usage.get("inputTokens")
                    or usage.get("input")
                    or 0
                )
                try:
                    tok = int(tok)
                except (TypeError, ValueError):
                    tok = 0
                if tok > 0:
                    return {
                        "session_id":   sid,
                        "input_tokens": tok,
                        "ts":           ts,
                    }
        return {"input_tokens": 0}

    def query_model_fallbacks(
        self,
        *,
        session_limit: int = 100,
        top: int = 10,
    ) -> dict[str, Any]:
        """Aggregate model/provider fallbacks across recent sessions.

        Drives ``/api/fallbacks`` (Tier-1 MOAT migration). Replaces the legacy
        path that opened up to ``session_limit`` JSONL files from disk and
        walked them line-by-line with a Python state machine — at 100 sessions
        × ~5 MB transcripts that's a multi-second probe even with warm cache.

        Algorithm: pull every ``message`` row whose ``message.role='assistant'``
        for the most-recent ``session_limit`` sessions (ordered by latest
        event ts), walk each session's turns in chronological order, and
        emit a transition each time ``model`` or ``provider`` differs from
        the previous assistant turn. Aggregate by (from_model, from_provider,
        to_model, to_provider) and rank by count.

        Returns a payload identical to what the legacy route assembled:
        ``{scanned, sessions_affected, top_transitions:[{from_model,
        to_model, from_provider, to_provider, count, sessions:[sid,…]}]}``.

        Empty workspace → ``{scanned:0, sessions_affected:0,
        top_transitions:[]}`` with no exception. Caller treats that as a
        miss and may fall through to the legacy walker (though for an
        empty DuckDB the legacy walker also returns empty).
        """
        try:
            sl = max(1, min(500, int(session_limit)))
        except (TypeError, ValueError):
            sl = 100
        try:
            tn = max(1, min(50, int(top)))
        except (TypeError, ValueError):
            tn = 10

        # Step 1: pick the N most-recent sessions that have at least one
        # assistant message. CTE keeps this a single round-trip.
        sql = """
            WITH recent_sessions AS (
                SELECT session_id, MAX(ts) AS last_ts
                FROM events
                WHERE event_type = 'message' AND session_id IS NOT NULL
                GROUP BY session_id
                ORDER BY last_ts DESC
                LIMIT ?
            )
            SELECT e.session_id, e.ts, e.data
            FROM events e
            INNER JOIN recent_sessions r ON e.session_id = r.session_id
            WHERE e.event_type = 'message'
            ORDER BY e.session_id, e.ts ASC, e.id ASC
        """
        rows = self._fetch(sql, [sl])

        # Step 2: walk per-session in Python. DuckDB JSON extract on a
        # nested path varies across versions; the deserialise+walk loop
        # is unambiguous and stays under millisecond per session.
        scanned_sids: set[str] = set()
        affected_sids: set[str] = set()
        pair_counts: dict[tuple, dict] = {}
        prev_model: str | None = None
        prev_provider: str | None = None
        prev_sid: str | None = None

        for sid, ts, raw in rows:
            scanned_sids.add(sid)
            if sid != prev_sid:
                # New session — reset state machine.
                prev_model = None
                prev_provider = None
                prev_sid = sid
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    continue
            msg = data.get("message") if isinstance(data.get("message"), dict) else data
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "assistant":
                continue
            model = (msg.get("model") or "").strip()
            provider = (msg.get("provider") or "").strip()
            if prev_model is not None and model and (
                model != prev_model or provider != prev_provider
            ):
                key = (prev_model, prev_provider, model, provider)
                bucket = pair_counts.get(key)
                if bucket is None:
                    bucket = {"count": 0, "sessions": []}
                    pair_counts[key] = bucket
                bucket["count"] += 1
                if sid not in bucket["sessions"]:
                    bucket["sessions"].append(sid)
                affected_sids.add(sid)
            if model:
                prev_model = model
                prev_provider = provider
            elif prev_model is None:
                prev_model = ""
                prev_provider = ""

        ranked = sorted(
            pair_counts.items(), key=lambda x: x[1]["count"], reverse=True
        )[:tn]
        top_transitions = [
            {
                "from_model":    k[0],
                "from_provider": k[1],
                "to_model":      k[2],
                "to_provider":   k[3],
                "count":         v["count"],
                "sessions":      v["sessions"][:10],
            }
            for k, v in ranked
        ]
        return {
            "scanned":           len(scanned_sids),
            "sessions_affected": len(affected_sids),
            "top_transitions":   top_transitions,
        }

    def query_session_model_journey(
        self,
        *,
        session_id: str,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Ordered model + message events for one session (issue #1088 phase 3).

        Returns rows ordered by timestamp ASC, each carrying enough fields
        to drive ``/api/session-model-journey`` segment computation:
          * model_change rows: ``{kind:'model_change', model, provider, ts}``
          * message rows:      ``{kind:'message', model, provider, total_tokens, total_cost, ts}``
          * thinking rows:     ``{kind:'thinking_level_change', level, ts}``

        Single-session helper — caller passes ``session_id``. Uses the
        existing events table; no new schema required."""
        if not session_id:
            return []
        sql = """
            SELECT event_type, ts, data, model
            FROM events
            WHERE session_id = ?
              AND event_type IN ('model_change', 'message', 'thinking_level_change')
            ORDER BY ts ASC, id ASC
            LIMIT ?
        """
        out: list[dict[str, Any]] = []
        for et, ts, raw, ev_model in self._fetch(sql, [session_id, int(limit)]):
            data: dict[str, Any] = {}
            if raw is not None:
                try:
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    parsed = json.loads(text) if text else {}
                    if isinstance(parsed, dict):
                        data = parsed
                except (ValueError, TypeError, UnicodeDecodeError):
                    data = {}
            if et == "model_change":
                out.append({
                    "kind":      "model_change",
                    "model":     data.get("modelId") or data.get("model") or ev_model or "",
                    "provider":  data.get("provider") or "",
                    "ts":        ts,
                })
            elif et == "thinking_level_change":
                out.append({
                    "kind":  "thinking_level_change",
                    "level": data.get("thinkingLevel") or data.get("level") or "",
                    "ts":    ts,
                })
            else:  # message
                msg = data.get("message") if isinstance(data.get("message"), dict) else {}
                usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                cost_obj = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
                out.append({
                    "kind":         "message",
                    "model":        msg.get("model") or ev_model or "",
                    "provider":     msg.get("provider") or "",
                    "total_tokens": int(usage.get("totalTokens", 0) or 0),
                    "total_cost":   float(cost_obj.get("total", 0) or 0),
                    "ts":           ts,
                })
        return out

    def query_aggregates(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """Per-day rollup. Computed on the fly from events; columnar storage
        means this is cheap even at hundreds-of-thousands of rows."""
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT
              substr(ts, 1, 10)            AS day,
              agent_id,
              COUNT(*)                     AS event_count,
              COALESCE(SUM(cost_usd), 0)   AS cost_usd,
              COALESCE(SUM(token_count), 0) AS token_count
            FROM events
            {where}
            GROUP BY day, agent_id
            ORDER BY day DESC
        """
        return [_row_to_dict(r, ["day","agent_id","event_count","cost_usd","token_count"])
                for r in self._fetch(sql, params)]

    # ── ops / maintenance ──────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Snapshot of store state — for the /local/health endpoint and the
        dashboard footer."""
        size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        rows = self._fetch(
            "SELECT COUNT(*) AS n, MIN(ts) AS oldest, MAX(ts) AS newest FROM events",
            []
        )
        n, oldest, newest = (rows[0] if rows else (0, None, None))
        with self._ring_lock:
            ring_depth = len(self._ring)
            dropped = self._dropped
        return {
            "db_path": str(DB_PATH),
            "engine": "duckdb",
            "size_bytes": int(size_bytes),
            "size_mb": round(size_bytes / 1024 / 1024, 2),
            "size_cap_bytes": LOCAL_MAX_BYTES,
            "event_count": int(n or 0),
            "oldest_ts": oldest,
            "newest_ts": newest,
            "ring_depth": ring_depth,
            "ring_max": RING_MAX,
            "ring_dropped_total": dropped,
            "schema_version": SCHEMA_VERSION,
            "last_flush_ago_s": round(time.monotonic() - self._last_flush_ts, 2),
        }

    def vacuum(self, *, prune_to_bytes: int | None = None) -> dict[str, Any]:
        """Reclaim space. If ``prune_to_bytes`` is set (or the DB has exceeded
        ``LOCAL_MAX_BYTES``), delete oldest events first until the projected
        size fits, then run a CHECKPOINT to reclaim file size."""
        self._flush_now()
        before_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        cap = prune_to_bytes if prune_to_bytes is not None else LOCAL_MAX_BYTES
        deleted = 0
        if before_size > cap:
            n_rows = (self._fetch("SELECT COUNT(*) FROM events", []) or [(0,)])[0][0]
            if n_rows > 0 and before_size > 0:
                bytes_per_row = before_size / n_rows
                excess_bytes = (before_size - cap) * 1.2
                rows_to_drop = int(excess_bytes / bytes_per_row) if bytes_per_row else 0
                if rows_to_drop > 0:
                    with self._write_lock:
                        with _txn(self._conn):
                            cur = self._conn.execute(
                                """
                                DELETE FROM events WHERE id IN (
                                  SELECT id FROM events ORDER BY ts ASC LIMIT ?
                                )
                                """,
                                [rows_to_drop],
                            )
                            # DuckDB returns rowcount=-1 for DELETE in some
                            # versions; if so, trust our planned count.
                            try:
                                rc = cur.rowcount
                            except Exception:
                                rc = -1
                            deleted = rc if rc is not None and rc >= 0 else rows_to_drop
        # CHECKPOINT forces DuckDB to merge WAL → main file, reclaiming space
        # similarly to SQLite VACUUM. Cheaper than full VACUUM on large DBs.
        with self._write_lock:
            try:
                self._conn.execute("CHECKPOINT")
            except Exception:
                log.exception("local store: CHECKPOINT failed")
        after_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        return {
            "deleted_rows": int(deleted),
            "before_bytes": before_size,
            "after_bytes": after_size,
            "cap_bytes": cap,
            "reclaimed_bytes": max(0, before_size - after_size),
        }

    # ── internals ───────────────────────────────────────────────────────

    def _fetch(self, sql: str, params: list[Any]) -> list[tuple]:
        """Issue a read, returning raw row tuples. DuckDB's ``.cursor()`` is
        thread-safe; we don't take the write lock for reads. We do however
        serialise with the writer through the lock to dodge transaction-state
        edge cases — DuckDB's reader-vs-writer story within one connection is
        better with light serialisation. At our scale (hundreds of qps max)
        this costs nothing."""
        with self._write_lock:
            cur = self._conn.execute(sql, params)
            return cur.fetchall()


# ── helpers ────────────────────────────────────────────────────────────────

_EVENT_COLS = [
    "id", "agent_type", "node_id", "agent_id", "session_id", "workspace_id",
    "event_type", "ts", "data", "cost_usd", "token_count", "model",
]


def _extract_event_metrics(
    e: dict[str, Any],
) -> tuple[float | None, int | None, str | None]:
    """Pull (cost_usd, token_count, model) from an event with shape fallbacks.

    Top-level ``cost_usd`` / ``token_count`` / ``model`` are honoured first —
    that's what the interceptor, claude-cli adapter, sync, and tests already
    provide. When absent (the OpenClaw gateway/jsonl shape), we fall through
    nested payload shapes:

      * OpenClaw: ``data.modelId`` + ``data.provider`` +
        ``data.promptCache.lastCallUsage.{input,output,total,cacheRead,cacheWrite}``
      * OpenClaw message: ``data.message.usage.{inputTokens,outputTokens,totalTokens}``
        with ``data.message.usage.cost.total`` (already-priced)
      * Anthropic SDK:  ``data.usage.{input_tokens,output_tokens,total_tokens}``

    Cost is derived from tokens × pricing only when input/output split AND
    provider AND model are all known (so we match
    ``providers_pricing.estimate_cost_usd``'s asymmetric rates). When only
    ``total`` is available, we leave cost=None — the brain UI / read-side
    aggregates compute it from tokens+model on demand and shouldn't see a
    half-correct value here.

    Never raises: any extraction failure quietly leaves the field as None
    so the store stays a permissive ingest path (#1129)."""
    cost = e.get("cost_usd")
    tokens = e.get("token_count")
    model = e.get("model")
    provider = e.get("provider")

    d = e.get("data") if isinstance(e.get("data"), dict) else None
    if d is None:
        return cost, tokens, model

    if not model:
        model = d.get("modelId") or d.get("model") or d.get("model_id")
        # Message-shape: data.message.{model, provider}
        msg = d.get("message") if isinstance(d.get("message"), dict) else None
        if not model and msg is not None:
            model = msg.get("model")
        if not provider and msg is not None:
            provider = provider or msg.get("provider")
    if not provider:
        provider = d.get("provider")

    tokens_in: int | None = None
    tokens_out: int | None = None

    if tokens is None:
        # 1. OpenClaw: data.promptCache.lastCallUsage
        pc = d.get("promptCache") if isinstance(d.get("promptCache"), dict) else None
        if pc is not None:
            lcu = pc.get("lastCallUsage") if isinstance(pc.get("lastCallUsage"), dict) else None
            if lcu is not None:
                t = lcu.get("total")
                i = lcu.get("input") or 0
                o = lcu.get("output") or 0
                if t is None and (i or o):
                    t = int(i) + int(o)
                if t:
                    try:
                        tokens = int(t)
                    except (TypeError, ValueError):
                        pass
                if i:
                    try:
                        tokens_in = int(i)
                    except (TypeError, ValueError):
                        pass
                if o:
                    try:
                        tokens_out = int(o)
                    except (TypeError, ValueError):
                        pass

        # 2. OpenClaw message: data.message.usage.{inputTokens,outputTokens,totalTokens}
        if tokens is None:
            msg = d.get("message") if isinstance(d.get("message"), dict) else None
            usage = msg.get("usage") if msg and isinstance(msg.get("usage"), dict) else None
            if usage is not None:
                t = usage.get("totalTokens") or usage.get("total_tokens")
                i = usage.get("inputTokens") or usage.get("input_tokens") or 0
                o = usage.get("outputTokens") or usage.get("output_tokens") or 0
                if t is None and (i or o):
                    t = int(i) + int(o)
                if t:
                    try:
                        tokens = int(t)
                    except (TypeError, ValueError):
                        pass
                if i and tokens_in is None:
                    try:
                        tokens_in = int(i)
                    except (TypeError, ValueError):
                        pass
                if o and tokens_out is None:
                    try:
                        tokens_out = int(o)
                    except (TypeError, ValueError):
                        pass
                # Already-priced cost is reliable — prefer it over re-derivation.
                cost_obj = usage.get("cost") if isinstance(usage.get("cost"), dict) else None
                if cost is None and cost_obj is not None:
                    ct = cost_obj.get("total")
                    if ct is not None:
                        try:
                            cost = float(ct)
                        except (TypeError, ValueError):
                            pass

        # 3. Anthropic SDK: data.usage.{input_tokens,output_tokens,total_tokens}
        if tokens is None:
            u = d.get("usage") if isinstance(d.get("usage"), dict) else None
            if u is not None:
                t = u.get("total_tokens") or u.get("totalTokens")
                i = u.get("input_tokens") or u.get("inputTokens") or 0
                o = u.get("output_tokens") or u.get("outputTokens") or 0
                if t is None and (i or o):
                    t = int(i) + int(o)
                if t:
                    try:
                        tokens = int(t)
                    except (TypeError, ValueError):
                        pass
                if i and tokens_in is None:
                    try:
                        tokens_in = int(i)
                    except (TypeError, ValueError):
                        pass
                if o and tokens_out is None:
                    try:
                        tokens_out = int(o)
                    except (TypeError, ValueError):
                        pass

    # Derive cost only when input/output split + provider + model are all known.
    # estimate_cost_usd uses asymmetric input/output rates; a single ``total``
    # can't be priced correctly, so leave cost=None and let read-side compute.
    if cost is None and provider and model and (tokens_in or tokens_out):
        try:
            from clawmetry.providers_pricing import estimate_cost_usd
            est = estimate_cost_usd(
                provider=str(provider),
                tokens_in=int(tokens_in or 0),
                tokens_out=int(tokens_out or 0),
                model=str(model),
            )
            if est:
                cost = float(est)
        except Exception:
            pass

    return cost, tokens, model


def _event_to_row(e: dict[str, Any]) -> tuple:
    """Coerce an event dict into the column tuple for the events table.
    Unknown keys are tolerated and dropped — events come from many sources
    (jsonl parser, gateway, claude-cli adapter) with slightly different
    shapes, and the store should not be the strict-schema choke point."""
    data = e.get("data")
    if data is not None and not isinstance(data, (bytes, bytearray)):
        if isinstance(data, str):
            data = data.encode("utf-8")
        else:
            data = json.dumps(data, separators=(",", ":")).encode("utf-8")
    cost, tokens, model = _extract_event_metrics(e)
    return (
        str(e["id"]),
        str(e.get("agent_type") or "openclaw"),
        str(e["node_id"]),
        str(e.get("agent_id") or "main"),
        e.get("session_id"),
        e.get("workspace_id"),
        str(e["event_type"]),
        str(e["ts"]),
        data,
        float(cost) if cost is not None else None,
        int(tokens) if tokens is not None else None,
        model,
        int(time.time() * 1000),
    )


def _row_to_event(row: tuple, cols: list[str]) -> dict[str, Any]:
    """Inverse of _event_to_row. Decodes ``data`` BLOB back to JSON if valid,
    else to a UTF-8 string, else leaves as None."""
    out = dict(zip(cols, row))
    raw = out.get("data")
    if raw is not None:
        try:
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            try:
                out["data"] = json.loads(text)
            except (ValueError, TypeError):
                out["data"] = text
        except UnicodeDecodeError:
            out["data"] = None
    return out


def _row_to_dict(row: tuple, cols: list[str]) -> dict[str, Any]:
    """Generic tuple-to-dict for non-event rows (sessions, aggregates)."""
    return dict(zip(cols, row))


def _duration_seconds(start_iso: str, end_iso: str) -> float:
    """Best-effort ISO-timestamp diff in seconds. Returns 0.0 on parse fail.

    Events arrive from multiple sources with slightly different ISO formats
    (``Z`` suffix vs ``+00:00`` vs naive). We normalise the common cases
    and never raise — flow-runs read paths must stay permissive."""
    if not start_iso or not end_iso:
        return 0.0
    def _parse(s: str):
        try:
            s2 = s.replace("Z", "+00:00") if s.endswith("Z") else s
            return datetime.fromisoformat(s2)
        except (TypeError, ValueError):
            return None
    a, b = _parse(start_iso), _parse(end_iso)
    if a is None or b is None:
        return 0.0
    try:
        return max(0.0, (b - a).total_seconds())
    except (TypeError, ValueError):
        return 0.0


_READ_TOOL_NAMES = frozenset({"read", "readfile", "read_file"})


def _iter_read_tool_paths(event_type: str | None, data: dict) -> Iterable[str]:
    """Yield ``file_path`` arguments for every Read-like tool invocation
    described by ``data``. Handles all three on-the-wire shapes the
    OpenClaw + trajectory-projection pipeline emits — see
    :meth:`LocalStore.query_recent_read_tool_calls` for the full list.

    Yields nothing for non-Read tool calls or when no path argument can
    be extracted; the caller treats absence as "skip this row".
    """
    if not isinstance(data, dict):
        return

    def _path_from_input(inp: Any) -> str:
        if isinstance(inp, str):
            try:
                inp = json.loads(inp)
            except (ValueError, TypeError):
                return ""
        if not isinstance(inp, dict):
            return ""
        for key in ("file_path", "path", "filename"):
            v = inp.get(key)
            if isinstance(v, str) and v:
                return v
        return ""

    et = (event_type or "").lower()

    # Shape 1: top-level tool.call / toolCall / tool_use event.
    if et in ("tool.call", "toolcall", "tool_use"):
        name = (data.get("name") or "").lower()
        if name in _READ_TOOL_NAMES:
            p = _path_from_input(data.get("input") or data.get("arguments"))
            if p:
                yield p
        return

    # Shape 2: assistant ``message`` event with ``toolMetas`` projection
    # (PR #1132 trajectory parser shape).
    metas = data.get("toolMetas")
    if isinstance(metas, list):
        for m in metas:
            if not isinstance(m, dict):
                continue
            if (m.get("name") or "").lower() not in _READ_TOOL_NAMES:
                continue
            p = _path_from_input(m.get("input"))
            if p:
                yield p

    # Shape 3: legacy assistant message events whose
    # ``data.message.content`` still carries raw
    # ``{type:'toolCall'|'tool_use'}`` blocks (older transcripts that
    # pre-date PR #1132's trajectory projection).
    msg = data.get("message")
    if isinstance(msg, dict) and msg.get("role") == "assistant":
        content = msg.get("content")
        if isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") not in ("toolCall", "tool_use"):
                    continue
                if (blk.get("name") or "").lower() not in _READ_TOOL_NAMES:
                    continue
                p = _path_from_input(blk.get("input") or blk.get("arguments"))
                if p:
                    yield p


def _iter_tool_invocation_names(event_type: str | None, data: dict) -> Iterable[str]:
    """Yield the tool ``name`` for every tool invocation described by
    ``data``. Mirrors the three on-the-wire shapes
    :func:`_iter_read_tool_paths` handles, but for ALL tool names — used
    by :meth:`LocalStore.query_tool_call_invocations` to power the
    /api/plugins per-plugin invocation counter.

    Yields the raw name string (caller lower-cases for matching). Yields
    nothing when the event isn't a tool call shape we recognise.
    """
    if not isinstance(data, dict):
        return

    et = (event_type or "").lower()

    # Shape 1: top-level tool.call / toolCall / tool_use event.
    if et in ("tool.call", "toolcall", "tool_use"):
        name = data.get("name") or data.get("tool")
        if isinstance(name, str) and name:
            yield name
        return

    # Shape 2: assistant ``message`` event with ``toolMetas`` projection
    # (PR #1132 trajectory parser shape).
    metas = data.get("toolMetas")
    if isinstance(metas, list):
        for m in metas:
            if not isinstance(m, dict):
                continue
            name = m.get("name") or m.get("tool")
            if isinstance(name, str) and name:
                yield name

    # Shape 3: legacy assistant message events whose
    # ``data.message.content`` still carries raw
    # ``{type:'toolCall'|'tool_use'}`` blocks. Note: the legacy
    # `_count_invocations` in routes/plugins.py only checked
    # `block.type == 'tool_use'` (PR-#1132 shape pre-projection). We
    # also count `toolCall` here so the fast-path matches OpenClaw's
    # current on-disk shape — strict superset of the legacy count.
    msg = data.get("message")
    if isinstance(msg, dict) and msg.get("role") == "assistant":
        content = msg.get("content")
        if isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") not in ("toolCall", "tool_use"):
                    continue
                name = blk.get("name") or blk.get("tool")
                if isinstance(name, str) and name:
                    yield name


def _decode_data_blob_rows(rows: Iterable[tuple], cols: list[str]) -> list[dict[str, Any]]:
    """tuple→dict for tables that have a ``data`` BLOB column. Decodes the
    BLOB back to JSON dict where possible; str otherwise; None when empty.
    Same pattern crons/subagents/system_snapshots/heartbeats all use."""
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(zip(cols, r))
        raw = d.get("data")
        if raw is not None:
            try:
                text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                try:
                    d["data"] = json.loads(text)
                except (ValueError, TypeError):
                    d["data"] = text
            except UnicodeDecodeError:
                d["data"] = None
        out.append(d)
    return out


@contextmanager
def _txn(conn: duckdb.DuckDBPyConnection) -> Iterator[None]:
    """Explicit BEGIN/COMMIT around a write block. DuckDB autocommits by
    default; this contextmanager makes batch atomicity explicit."""
    conn.execute("BEGIN")
    try:
        yield
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
