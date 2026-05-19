"""clawmetry/dives_prompt.py — prompt template + schema descriptor for Dives.

Dives lets users ask plain-English questions; an LLM generates a SQL query
against the local DuckDB store; the result is rendered as a chart.

This module owns:
  - ``PROMPT_VERSION`` — bump when the template changes incompatibly.
  - ``_COL_DOCS`` — human descriptions for every column in the 9 allowlisted
    tables. Column names + types come from ``PRAGMA table_info`` at runtime;
    this dict is the knowledge layer the LLM can't infer from names alone.
  - ``build_schema_descriptor(store)`` — combines runtime PRAGMA output with
    the static column docs into a plain-text schema block.
  - ``build_dives_prompt(question, store)`` — returns
    ``{"system": <system prompt + schema + few-shots>, "user": <question>}``
    ready for the Anthropic messages API (or any OpenAI-compat API).

Safety: the LLM output is always run through
``clawmetry.dives_sql_safety.validate_sql`` before execution.  The prompt
reinforces the same constraints so the model learns to self-police (belt +
suspenders).

Sub-issue: https://github.com/vivekchand/clawmetry/issues/1001
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clawmetry.local_store import LocalStore

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

# Bump when the template changes in a backward-incompatible way so callers
# can detect that cached prompts need regeneration.
PROMPT_VERSION = 1

# ---------------------------------------------------------------------------
# Allowlisted tables (mirrors dives_sql_safety.ALLOWED_TABLES)
# ---------------------------------------------------------------------------

# Kept here as an ordered tuple so the schema descriptor has a stable,
# human-friendly ordering.  Kept in sync with dives_sql_safety.ALLOWED_TABLES
# by the test suite (test_dives_tables_match_allowlist).
_DIVES_TABLES: tuple[str, ...] = (
    "events",
    "sessions",
    "daily_aggregates",
    "memory_blobs",
    "heartbeats",
    "system_snapshots",
    "openclaw_channels",
    "crons",
    "subagents",
)

# ---------------------------------------------------------------------------
# Column documentation
# ---------------------------------------------------------------------------

# Human descriptions for each column in each allowlisted table.  Column names
# and SQL types come from PRAGMA table_info at runtime; these strings are the
# extra semantic layer the LLM can't infer from column names alone.
_COL_DOCS: dict[str, dict[str, str]] = {
    "events": {
        "id":           "unique event ID",
        "agent_type":   "agent runtime (openclaw, hermes, ...)",
        "node_id":      "machine / container ID",
        "agent_id":     "agent instance (usually 'main')",
        "session_id":   "conversation session this event belongs to",
        "workspace_id": "workspace / project ID",
        "event_type":   "category (tool_call, llm_turn, error, ...)",
        "ts":           "ISO-8601 timestamp of the event",
        "data":         "BLOB - JSON payload; use json_extract_string() to query fields",
        "cost_usd":     "LLM cost in USD (NULL for non-LLM events)",
        "token_count":  "tokens consumed in this event",
        "model":        "LLM model ID (e.g. claude-3-5-sonnet-20241022)",
        "created_at":   "Unix milliseconds when the row was written",
    },
    "sessions": {
        "agent_type":            "agent runtime",
        "session_id":            "unique session identifier",
        "node_id":               "machine / container ID",
        "agent_id":              "agent instance (usually 'main')",
        "workspace_id":          "workspace / project ID",
        "title":                 "short session title (often the first user message)",
        "started_at":            "ISO-8601 session start time",
        "last_active_at":        "ISO-8601 most recent activity",
        "ended_at":              "ISO-8601 session end time (NULL if still running)",
        "status":                "running | completed | error | ...",
        "total_tokens":          "cumulative token usage for the session",
        "cost_usd":              "cumulative LLM cost in USD for the session",
        "message_count":         "number of turns in the session",
        "metadata":              "BLOB - extra metadata",
        "updated_at":            "Unix milliseconds of last row update",
        "outcome":               "success | failure | ambiguous (set by outcome classifier)",
        "outcome_confidence":    "classifier confidence 0-1",
        "outcome_classified_at": "Unix milliseconds when outcome was set",
        "eval_score":            "LLM-as-judge score 0-5",
        "eval_reason":           "judge's reasoning text",
        "eval_judge_model":      "model used for evaluation",
        "eval_scored_at":        "Unix milliseconds when eval was run",
        "eval_rubric":           "rubric used for evaluation",
    },
    "daily_aggregates": {
        "agent_type":   "agent runtime",
        "agent_id":     "agent instance",
        "workspace_id": "workspace / project ID",
        "day":          "ISO date string (YYYY-MM-DD)",
        "cost_usd":     "total LLM cost for this agent on this day",
        "token_count":  "total tokens consumed on this day",
        "event_count":  "number of events on this day",
        "error_count":  "number of error events on this day",
    },
    "memory_blobs": {
        "agent_type": "agent runtime",
        "agent_id":   "agent instance",
        "path":       "file path of the memory file (e.g. SOUL.md, MEMORY.md)",
        "ts":         "ISO-8601 last-modified time",
        "blob":       "BLOB - raw file contents (do not SELECT; use size_bytes instead)",
        "sha256":     "SHA-256 content hash",
        "size_bytes": "file size in bytes",
        "updated_at": "Unix milliseconds when the row was written",
    },
    "heartbeats": {
        "agent_type":   "agent runtime",
        "node_id":      "machine / container ID",
        "ts":           "ISO-8601 heartbeat timestamp",
        "version":      "ClawMetry version string",
        "e2e":          "TRUE if end-to-end health check passed",
        "size_mb":      "local DuckDB file size in MB at heartbeat time",
        "events_total": "total events in the local store at heartbeat time",
        "data":         "BLOB - additional node metadata",
    },
    "system_snapshots": {
        "agent_type": "agent runtime",
        "node_id":    "machine / container ID",
        "ts":         "ISO-8601 snapshot timestamp",
        "kind":       "snapshot type (disk, cpu, ram, gpu, ...)",
        "data":       "BLOB - JSON snapshot payload; use json_extract_string() to query",
    },
    "openclaw_channels": {
        "session_id":   "session this channel metadata belongs to",
        "channel":      "channel adapter (telegram, slack, discord, signal, ...)",
        "chat_type":    "private | group | channel",
        "subject":      "chat title or topic",
        "origin_label": "human-readable source label",
    },
    "crons": {
        "agent_type":  "agent runtime",
        "cron_id":     "unique cron job ID",
        "agent_id":    "agent instance",
        "name":        "human-readable cron name",
        "schedule":    "cron schedule expression (e.g. '0 9 * * 1')",
        "enabled":     "TRUE if the cron is active",
        "last_run_at": "ISO-8601 last execution time",
        "last_status": "ok | error | skipped",
        "next_run_at": "ISO-8601 next scheduled run",
        "data":        "BLOB - extra cron metadata",
        "updated_at":  "Unix milliseconds of last row update",
    },
    "subagents": {
        "agent_type":        "agent runtime",
        "subagent_id":       "unique sub-agent ID",
        "parent_session_id": "session that spawned this sub-agent",
        "spawned_at":        "ISO-8601 spawn time",
        "ended_at":          "ISO-8601 completion time (NULL if still running)",
        "task":              "task description given to the sub-agent",
        "status":            "running | completed | error | ...",
        "cost_usd":          "LLM cost incurred by this sub-agent in USD",
        "token_count":       "tokens consumed by this sub-agent",
        "data":              "BLOB - additional sub-agent metadata",
        "updated_at":        "Unix milliseconds of last row update",
    },
}

# ---------------------------------------------------------------------------
# Chart types
# ---------------------------------------------------------------------------

SUPPORTED_CHART_TYPES: tuple[str, ...] = ("bar", "line", "pie", "table", "number")

# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------

# Three question shapes: aggregation-over-time, ranking, group-by-count.
# Each SQL is validated by the test suite via dives_sql_safety.validate_sql.
_FEW_SHOT_EXAMPLES: list[dict] = [
    {
        "question": "Total cost per agent today",
        "answer": {
            "sql": (
                "SELECT agent_type, SUM(cost_usd) AS cost "
                "FROM events "
                "WHERE DATE(ts) = CURRENT_DATE "
                "  AND cost_usd IS NOT NULL "
                "GROUP BY agent_type "
                "ORDER BY cost DESC "
                "LIMIT 50"
            ),
            "chart_type": "bar",
            "x": "agent_type",
            "y": "cost",
            "title": "Total cost per agent today",
            "description": "Cumulative LLM cost grouped by agent runtime for today.",
        },
    },
    {
        "question": "Top 10 most-used tools this week",
        "answer": {
            "sql": (
                "SELECT json_extract_string(data, '$.tool_name') AS tool, "
                "       COUNT(*) AS calls "
                "FROM events "
                "WHERE event_type = 'tool_call' "
                "  AND ts >= CAST(DATE_TRUNC('week', CURRENT_DATE) AS VARCHAR) "
                "  AND json_extract_string(data, '$.tool_name') IS NOT NULL "
                "GROUP BY tool "
                "ORDER BY calls DESC "
                "LIMIT 10"
            ),
            "chart_type": "bar",
            "x": "tool",
            "y": "calls",
            "title": "Top 10 tools this week",
            "description": "Tool call frequency ranked highest to lowest for the current week.",
        },
    },
    {
        "question": "Sessions started in the last 24h, by status",
        "answer": {
            "sql": (
                "SELECT status, COUNT(*) AS n "
                "FROM sessions "
                "WHERE started_at >= CAST(NOW() - INTERVAL '24 hours' AS VARCHAR) "
                "GROUP BY status "
                "ORDER BY n DESC "
                "LIMIT 20"
            ),
            "chart_type": "pie",
            "x": "status",
            "y": "n",
            "title": "Session status in last 24h",
            "description": "Distribution of session outcomes started in the last 24 hours.",
        },
    },
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_HEADER = f"""\
You are an expert SQL author for ClawMetry, a real-time AI agent observability \
dashboard. You write SELECT queries against a local DuckDB database and return a \
JSON envelope that the dashboard uses to render a chart.

## Hard constraints
- Only SELECT (or WITH ... SELECT) is allowed. Never INSERT, UPDATE, DELETE, DROP,
  CREATE, ATTACH, PRAGMA, or any write/DDL statement.
- Only query tables listed in the schema below. Never reference other tables.
- Always add LIMIT (max 500) when the result set could be large.
- Never use file-read functions (read_csv, read_parquet, glob, httpfs, etc.).
- BLOB columns must not be SELECTed raw; use json_extract_string() for JSON payloads.
- Return JSON only. No markdown fences, no explanation text outside the JSON object.

## Response format (JSON, exactly these six keys)
{{
  "sql":         "<your SELECT query>",
  "chart_type":  "bar | line | pie | table | number",
  "x":           "<column name for x-axis or label>",
  "y":           "<column name for y-axis or value>",
  "title":       "<short chart title>",
  "description": "<one sentence explaining what the chart shows>"
}}

chart_type guide:
  bar    -- ranked or grouped comparisons
  line   -- time series and trends
  pie    -- proportions (max 8 slices; prefer bar for > 8)
  table  -- multi-column results with no natural chart shape
  number -- single scalar answer (COUNT, SUM, AVG, ...)

## Prompt version
PROMPT_VERSION={PROMPT_VERSION}
""".strip()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_schema_descriptor(store: "LocalStore | None" = None) -> str:
    """Return a plain-text schema block for the 9 allowlisted tables.

    When *store* is provided, column names and SQL types are fetched via
    ``store.dives_table_columns(table)`` so the descriptor reflects any
    migrations applied since this module was written.  When *store* is
    ``None`` (tests, import-time checks) the static column list from
    ``_COL_DOCS`` is used as the fallback.
    """
    lines: list[str] = ["Allowlisted tables and their columns:\n"]

    for table in _DIVES_TABLES:
        col_docs = _COL_DOCS.get(table, {})

        if store is not None:
            try:
                pragma_rows = store.dives_table_columns(table)
                cols = [(r["name"], r["ctype"]) for r in pragma_rows]
            except Exception:
                cols = [(name, "") for name in col_docs]
        else:
            cols = [(name, "") for name in col_docs]

        lines.append(f"Table: {table}")
        for name, ctype in cols:
            doc = col_docs.get(name, "")
            type_part = f" ({ctype})" if ctype else ""
            doc_part = f"  -- {doc}" if doc else ""
            lines.append(f"  {name}{type_part}{doc_part}")
        lines.append("")

    return "\n".join(lines)


def build_dives_prompt(
    question: str,
    store: "LocalStore | None" = None,
) -> dict[str, str]:
    """Build the system + user messages for a Dives LLM call.

    Args:
        question: The plain-English question from the user.
        store:    Open ``LocalStore`` instance.  When provided the schema
                  descriptor is generated from ``PRAGMA table_info`` so it
                  reflects any live migrations; otherwise a static descriptor
                  is used (sufficient for unit tests).

    Returns:
        ``{"system": ..., "user": ...}`` — pass ``system`` as the Anthropic
        ``system`` parameter and wrap ``user`` in a ``messages`` list with
        ``role="user"``.

    Raises:
        ValueError: if *question* is empty or whitespace-only.
    """
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string")

    schema = build_schema_descriptor(store)
    few_shot_json = json.dumps(_FEW_SHOT_EXAMPLES, indent=2)

    system = "\n\n".join([
        _SYSTEM_PROMPT_HEADER,
        "## Schema\n" + schema,
        "## Few-shot examples\n" + few_shot_json,
    ])

    return {"system": system, "user": question.strip()}


__all__ = [
    "PROMPT_VERSION",
    "SUPPORTED_CHART_TYPES",
    "build_schema_descriptor",
    "build_dives_prompt",
]
