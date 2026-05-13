"""Tests for ``clawmetry.dives_sql_safety.validate_sql``.

Covers the Dives SQL safety validator (issue #1000). Two suites:

* ``VALID_QUERIES`` — 10+ realistic SELECT / WITH queries against the local
  DuckDB store. Each must validate cleanly. These are the false-positive
  regression net.
* ``MALICIOUS_QUERIES`` — 20+ injection / abuse attempts. Each must be
  rejected, and the rejection ``reason`` must mention the right category so
  failures are easy to triage.

The two lists are large on purpose; the validator is the security boundary for
Dives so we'd rather over-test it than under-test it.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make the package importable when running as `pytest tests/...` from repo root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clawmetry.dives_sql_safety import (  # noqa: E402
    MAX_SQL_LENGTH,
    validate_sql,
)


# ---------------------------------------------------------------------------
# Valid queries — must pass.
# ---------------------------------------------------------------------------
# Each entry is (id, sql). Keep them realistic so they double as docs.
VALID_QUERIES: list[tuple[str, str]] = [
    ("simple_select",
        "SELECT COUNT(*) FROM events"),
    ("select_with_where",
        "SELECT agent_type, SUM(cost_usd) AS total "
        "FROM events WHERE ts >= '2026-05-01' GROUP BY agent_type"),
    ("select_order_limit",
        "SELECT session_id, model FROM sessions "
        "ORDER BY started_at DESC LIMIT 50"),
    ("select_join",
        "SELECT s.session_id, COUNT(e.id) AS n "
        "FROM sessions s LEFT JOIN events e USING (session_id) "
        "GROUP BY s.session_id"),
    ("select_case",
        "SELECT agent_type, "
        "       CASE WHEN cost_usd > 1 THEN 'expensive' ELSE 'cheap' END AS bucket "
        "FROM events"),
    ("select_subquery",
        "SELECT * FROM ("
        "  SELECT agent_type, SUM(tokens_in) AS t FROM events GROUP BY 1"
        ") sub WHERE t > 1000"),
    ("with_cte_basic",
        "WITH daily AS (SELECT date_trunc('day', ts) AS d, SUM(cost_usd) AS c "
        "FROM events GROUP BY 1) "
        "SELECT d, c FROM daily ORDER BY d"),
    ("with_multi_cte",
        "WITH a AS (SELECT * FROM events), "
        "     b AS (SELECT session_id, COUNT(*) AS n FROM a GROUP BY 1) "
        "SELECT * FROM b WHERE n > 10"),
    ("select_window_fn",
        "SELECT session_id, ts, "
        "       SUM(cost_usd) OVER (PARTITION BY session_id ORDER BY ts) AS running "
        "FROM events"),
    ("select_string_with_keyword_inside",
        # The literal contains the word DROP — must NOT trip the keyword scan.
        "SELECT 'do not DROP this row' AS label, COUNT(*) FROM events"),
    ("select_with_comment_above",
        "-- count rows per agent\nSELECT agent_type, COUNT(*) FROM events GROUP BY 1"),
    ("select_qualified_column",
        "SELECT events.agent_type, events.cost_usd FROM events LIMIT 5"),
    ("select_trailing_semicolon",
        "SELECT 1;"),
]


@pytest.mark.parametrize("name,sql", VALID_QUERIES, ids=[v[0] for v in VALID_QUERIES])
def test_valid_queries_pass(name: str, sql: str) -> None:
    ok, reason = validate_sql(sql)
    assert ok, f"expected valid, got reject ({reason}) for {name!r}: {sql!r}"
    assert reason is None


def test_valid_query_count() -> None:
    """Guard against accidentally shrinking the false-positive net."""
    assert len(VALID_QUERIES) >= 10


# ---------------------------------------------------------------------------
# Malicious queries — must be rejected.
# ---------------------------------------------------------------------------
# Each entry is (id, sql, expected_reason_substring). The substring is
# lowercased before comparison — it just needs to appear somewhere in the
# returned reason so we know the right rule fired.
MALICIOUS_QUERIES: list[tuple[str, str, str]] = [
    # Multi-statement classics
    ("injection_drop_semicolon",
        "SELECT 1; DROP TABLE events;--",
        "multiple"),
    ("injection_quote_drop",
        "SELECT * FROM events WHERE id = ''; DROP TABLE events; --'",
        "multiple"),
    ("two_selects",
        "SELECT 1; SELECT 2",
        "multiple"),

    # DDL / DML attempts
    ("bare_drop",
        "DROP TABLE events",
        "only select"),
    ("bare_insert",
        "INSERT INTO events VALUES (1)",
        "only select"),
    ("bare_update",
        "UPDATE events SET cost_usd = 0",
        "only select"),
    ("bare_delete",
        "DELETE FROM events",
        "only select"),
    ("bare_alter",
        "ALTER TABLE events ADD COLUMN x INT",
        "only select"),
    ("bare_create",
        "CREATE TABLE x AS SELECT 1",
        "only select"),
    ("bare_truncate",
        "TRUNCATE events",
        "only select"),

    # DuckDB-specific footguns
    ("attach_remote",
        "ATTACH 'http://evil.example.com/db' AS evil",
        "only select"),
    ("install_extension",
        "INSTALL httpfs",
        "only select"),
    ("load_extension",
        "LOAD httpfs",
        "only select"),
    ("pragma",
        "PRAGMA database_list",
        "only select"),
    ("copy_to_file",
        "COPY events TO '/tmp/exfil.csv'",
        "only select"),
    ("set_search_path",
        "SET search_path = malicious",
        "only select"),

    # Hidden statements inside otherwise-valid SELECTs. A block comment that
    # encloses the DROP is fine (it's literally commented out); a comment that
    # *precedes* a hidden statement must still be caught.
    ("line_comment_then_drop",
        "SELECT 1 --\n; DROP TABLE events",
        "multiple"),
    ("block_comment_then_drop",
        "SELECT 1 /* harmless */ ; DROP TABLE events",
        "multiple"),
    ("comment_then_inline_drop",
        # post-comment-strip: ``SELECT 1   DROP TABLE events`` — no semicolon,
        # single statement, but the keyword scan must still spot DROP.
        "SELECT 1 /* harmless */ DROP TABLE events",
        "banned keyword: drop"),

    # Function-call attacks (file-system access)
    ("read_csv_call",
        "SELECT * FROM read_csv('/etc/passwd')",
        "read_csv"),
    ("read_parquet_call",
        "SELECT * FROM read_parquet('s3://bucket/x.parquet')",
        "read_parquet"),
    ("read_json_call",
        "SELECT * FROM read_json('/tmp/x.json')",
        "read_json"),
    ("write_csv_call",
        "SELECT write_csv(events, '/tmp/x.csv') FROM events",
        "write_csv"),
    ("glob_call",
        "SELECT glob('/etc/*')",
        "glob"),
    ("httpfs_call",
        "SELECT httpfs('http://x')",
        "httpfs"),
    ("system_function_call",
        "SELECT system_function('rm -rf /')",
        "system_function"),

    # UNION exfil tries to read forbidden tables — these are SELECTs but they
    # *also* try to slip in a banned keyword via stacked statement.
    ("union_then_drop",
        "SELECT 1 UNION SELECT 2; DROP TABLE events",
        "multiple"),

    # Pathological / oversize inputs
    ("oversize",
        "SELECT " + ("a," * (MAX_SQL_LENGTH // 2)) + "1 FROM events",
        "too long"),
    ("empty",
        "",
        "empty"),
    ("whitespace_only",
        "   \n\t  ",
        "empty"),
    ("comments_only",
        "-- nothing here\n/* still nothing */",
        "no statement"),
    ("nul_byte",
        "SELECT 1\x00; DROP TABLE events",
        "nul"),

    # Misc shapes that aren't SELECT
    ("show_tables",
        "SHOW TABLES",
        "only select"),
    ("describe",
        "DESCRIBE events",
        "only select"),
    ("explain",
        "EXPLAIN SELECT * FROM events",
        "only select"),
    ("begin_transaction",
        "BEGIN; SELECT 1; COMMIT",
        "multiple"),
    ("call_procedure",
        "CALL foo()",
        "only select"),
]

@pytest.mark.parametrize(
    "name,sql,expected",
    MALICIOUS_QUERIES,
    ids=[m[0] for m in MALICIOUS_QUERIES],
)
def test_malicious_queries_rejected(name: str, sql: str, expected: str) -> None:
    ok, reason = validate_sql(sql)
    assert not ok, f"expected reject for {name!r}, but passed: {sql!r}"
    assert reason is not None
    assert expected.lower() in reason.lower(), (
        f"reason for {name!r} = {reason!r} did not contain {expected!r}"
    )


def test_malicious_query_count() -> None:
    """Guard against accidentally shrinking the malicious-input net."""
    assert len(MALICIOUS_QUERIES) >= 20


# ---------------------------------------------------------------------------
# Misc behavioural tests
# ---------------------------------------------------------------------------

def test_none_input_rejected() -> None:
    ok, reason = validate_sql(None)  # type: ignore[arg-type]
    assert not ok
    assert reason


def test_non_string_input_rejected() -> None:
    ok, reason = validate_sql(123)  # type: ignore[arg-type]
    assert not ok
    assert reason


def test_returns_tuple_of_bool_and_optional_str() -> None:
    ok, reason = validate_sql("SELECT 1")
    assert isinstance(ok, bool)
    assert reason is None or isinstance(reason, str)


def test_case_insensitive_keywords() -> None:
    ok, reason = validate_sql("select 1 from events")
    assert ok, reason
    ok, _ = validate_sql("dRoP TaBlE events")
    assert not ok


def test_string_literal_with_doubled_quotes_does_not_break_parser() -> None:
    ok, reason = validate_sql("SELECT 'it''s fine' AS x")
    assert ok, reason


def test_unterminated_string_does_not_hang_or_crash() -> None:
    # An unterminated string literal is suspicious; we don't care whether it
    # passes or fails, only that we don't hang/crash on it.
    ok, reason = validate_sql("SELECT 'oops")
    assert isinstance(ok, bool)
    assert reason is None or isinstance(reason, str)
