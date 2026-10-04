"""Bounded assistant persistence and read-only query tests."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_URL", "http://127.0.0.1:8911")
    monkeypatch.setenv("CLAWMETRY_TOKEN", "ci-test-token")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "assistant.duckdb")
    )
    import clawmetry.local_store as local_store

    local_store._reset_singleton_for_tests()
    importlib.reload(local_store)
    store = local_store.get_store()
    yield local_store, store
    local_store._reset_singleton_for_tests()


def test_assistant_conversation_schema_write_reopen_and_read(fresh_store):
    local_store, store = fresh_store
    messages = [
        {"role": "user", "content": "How many runs finished today?"},
        {
            "role": "assistant",
            "content": "There were three.",
            "panels": [{"title": "Runs", "rows": [{"count": 3}]}],
        },
    ]

    saved = store.save_assistant_conversation(
        conversation_id="conversation-1",
        title="Daily runs",
        messages=messages,
    )
    assert saved["id"] == "conversation-1"
    assert saved["title"] == "Daily runs"
    assert saved["messages"] == messages
    assert saved["updated_at"] > 0
    assert store.query_assistant_conversations(limit=30)[0] == {
        "id": "conversation-1",
        "title": "Daily runs",
        "updated_at": saved["updated_at"],
    }

    assert store.query_assistant_conversation(conversation_id="missing") == {}
    assert store.query_assistant_conversation(conversation_id="") == {}
    assert (
        store._conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()[0]
        == local_store.SCHEMA_VERSION
    )

    store.stop(flush=False)
    local_store._reset_singleton_for_tests()
    reopened = local_store.get_store()
    assert reopened.query_assistant_conversation(
        conversation_id="conversation-1"
    ) == saved


def test_assistant_conversation_bounds_messages_and_panel_rows(fresh_store):
    _local_store, store = fresh_store

    with pytest.raises(ValueError, match="50 messages"):
        store.save_assistant_conversation(
            conversation_id="too-many",
            title="Too many",
            messages=[{"role": "user", "content": "x"}] * 51,
        )

    with pytest.raises(ValueError, match="500 rows"):
        store.save_assistant_conversation(
            conversation_id="too-many-rows",
            title="Too many rows",
            messages=[
                {
                    "role": "assistant",
                    "panels": [{"rows": [{"n": n} for n in range(501)]}],
                }
            ],
        )


def test_assistant_conversation_accepts_route_shaped_sources_and_results(
    fresh_store,
):
    _local_store, store = fresh_store
    messages = [
        {
            "role": "assistant",
            "answer": "Seven sessions matched.",
            "sources": [{"label": "Sessions", "rows": 7, "preview": []}],
            "query_result": {"rows": 7, "panels": 1},
        }
    ]

    saved = store.save_assistant_conversation(
        conversation_id="route-shaped",
        title="Route-shaped answer",
        messages=messages,
    )
    assert saved["messages"] == messages


def test_assistant_query_distinguishes_empty_rows_from_sql_failure(fresh_store):
    _local_store, store = fresh_store

    empty = store.query_assistant_sql(sql="SELECT 1 WHERE 1 = 0")
    assert empty == {"rows": []}

    failed = store.query_assistant_sql(sql="SELECT FROM sessions")
    assert failed["rows"] == []
    assert failed["error"]

    truncated = store.query_assistant_sql(
        sql=(
            "SELECT 1 AS value UNION ALL SELECT 2 AS value "
            "UNION ALL SELECT 3 AS value"
        ),
        max_rows=2,
    )
    assert truncated["rows"] == [{"value": 1}, {"value": 2}]
    assert truncated["truncated"] is True
    assert "truncated" in truncated["notice"].lower()


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM events",
        "REPLACE INTO sessions (agent_type, session_id, updated_at) VALUES ('x', 'x', 1)",
        "SELECT * FROM 'events'",
        "SELECT * FROM 'secret.csv'",
        "SELECT * FROM sessions, 'secret.csv'",
        """SELECT * FROM sessions, "secret.csv" """,
        'SELECT * FROM sessions, "/tmp/secret.parquet"',
        "SELECT * FROM range(3)",
        "SELECT * FROM secret_table",
        "SELECT read_text('/tmp/secret')",
        """SELECT "read_text"('/tmp/secret')""",
        """SELECT * FROM "read_text"('/tmp/secret')""",
        "SELECT data FROM events",
        "SELECT metadata FROM sessions",
        "SELECT * FROM events",
    ],
)
def test_assistant_query_rejects_unsafe_or_raw_sql(fresh_store, sql):
    _local_store, store = fresh_store
    result = store.query_assistant_sql(sql=sql)
    assert result["rows"] == []
    assert result["error"]


def test_assistant_query_allows_only_explicit_safe_functions_and_tables(
    fresh_store,
):
    _local_store, store = fresh_store

    result = store.query_assistant_sql(
        sql="SELECT count(*) AS total FROM events"
    )
    assert result == {"rows": [{"total": 0}]}

    result = store.query_assistant_sql(sql="SELECT upper('ok') AS value")
    assert result == {"rows": [{"value": "OK"}]}

    result = store.query_assistant_sql(
        sql="SELECT replace('claude_code', '_', '-') AS value"
    )
    assert result == {"rows": [{"value": "claude-code"}]}

    for sql in (
        "SELECT current_date AS today",
        "SELECT current_timestamp AS current_time",
        "SELECT now() AS current_time",
        "SELECT date_trunc('day', current_timestamp) AS today",
        "SELECT current_date - INTERVAL '7 days' AS since",
    ):
        result = store.query_assistant_sql(sql=sql)
        assert "error" not in result
        assert len(result["rows"]) == 1
        assert isinstance(next(iter(result["rows"][0].values())), str)

    result = store.query_assistant_sql(
        sql=(
            "WITH filtered AS ("
            "SELECT session_id FROM sessions WHERE session_id IN ('none')"
            ") SELECT count(*) AS total FROM filtered"
        )
    )
    assert result == {"rows": [{"total": 0}]}

    result = store.query_assistant_sql(
        sql="SELECT row_number() OVER () AS n FROM sessions"
    )
    assert result == {"rows": []}


def test_assistant_query_allows_grouped_cost_arithmetic_regression(fresh_store):
    _local_store, store = fresh_store
    result = store.query_assistant_sql(
        sql=(
            "SELECT agent_type AS runtime, "
            "ROUND(SUM(cost_usd), 4) AS estimated_api_equivalent_cost_usd, "
            "COUNT(cost_usd) AS sessions_with_known_cost, "
            "COUNT(*) - COUNT(cost_usd) AS sessions_with_unknown_cost "
            "FROM sessions GROUP BY agent_type "
            "ORDER BY estimated_api_equivalent_cost_usd DESC NULLS LAST LIMIT 100"
        )
    )
    assert "error" not in result
    assert isinstance(result["rows"], list)

    for predicate in (
        "runtime ILIKE '%claude%'",
        "runtime NOT LIKE '%never%'",
        "runtime NOT ILIKE '%never%'",
    ):
        result = store.query_assistant_sql(
            sql=f"SELECT runtime FROM sessions WHERE {predicate}"
        )
        assert "error" not in result
        assert isinstance(result["rows"], list)

    result = store.query_assistant_sql(
        sql=(
            "SELECT runtime, COUNT(*) AS session_count, "
            "SUM(cost_usd) AS estimated_api_equivalent_cost_usd, "
            "COUNT(cost_usd) AS sessions_with_known_cost, "
            "COUNT(*) - COUNT(cost_usd) AS sessions_with_unknown_cost, "
            "MIN(started_at) AS earliest_session_started_at, "
            "MAX(started_at) AS latest_session_started_at "
            "FROM sessions "
            "WHERE LOWER(runtime) LIKE '%claude%' "
            "OR LOWER(runtime) LIKE '%codex%' "
            "GROUP BY runtime "
            "ORDER BY estimated_api_equivalent_cost_usd DESC NULLS LAST "
            "LIMIT 100"
        )
    )
    assert "error" not in result
    assert isinstance(result["rows"], list)


def test_assistant_query_allows_memory_metadata_but_rejects_blob(fresh_store):
    _local_store, store = fresh_store

    metadata = store.query_assistant_sql(
        sql="SELECT agent_type, path, size_bytes FROM memory_blobs"
    )
    assert "error" not in metadata
    assert isinstance(metadata["rows"], list)

    raw = store.query_assistant_sql(sql="SELECT blob FROM memory_blobs")
    assert raw["rows"] == []
    assert raw["error"]

    wildcard = store.query_assistant_sql(sql="SELECT * FROM memory_blobs")
    assert wildcard["rows"] == []
    assert wildcard["error"]


def test_assistant_query_derives_runtime_from_family_session_prefixes(fresh_store):
    _local_store, store = fresh_store
    with store._write_lock:
        store._conn.executemany(
            """
            INSERT INTO sessions
                (agent_type, session_id, node_id, agent_id, status, updated_at)
            VALUES ('openclaw', ?, 'node', 'main', 'completed', ?)
            """,
            [("codex:family-1", 1), ("claude_code:family-2", 2)],
        )
        store._conn.executemany(
            """
            INSERT INTO events
                (id, agent_type, node_id, agent_id, session_id, event_type,
                 ts, created_at)
            VALUES (?, 'openclaw', 'node', 'main', ?, 'message', ?, ?)
            """,
            [
                ("runtime-event-1", "codex:family-1", "2026-01-01T00:00:00Z", 1),
                ("runtime-event-2", "claude_code:family-2", "2026-01-01T00:00:01Z", 2),
            ],
        )

    sessions = store.query_assistant_sql(
        sql=(
            "SELECT session_id, agent_type, runtime FROM sessions "
            "ORDER BY session_id"
        )
    )
    assert sessions == {
        "rows": [
            {"session_id": "claude_code:family-2", "agent_type": "openclaw", "runtime": "claude_code"},
            {"session_id": "codex:family-1", "agent_type": "openclaw", "runtime": "codex"},
        ]
    }

    events = store.query_assistant_sql(
        sql=(
            "SELECT session_id, agent_type, runtime FROM events "
            "ORDER BY session_id"
        )
    )
    assert events == {
        "rows": [
            {"session_id": "claude_code:family-2", "agent_type": "openclaw", "runtime": "claude_code"},
            {"session_id": "codex:family-1", "agent_type": "openclaw", "runtime": "codex"},
        ]
    }


def test_assistant_query_rejects_views_and_keeps_external_access_unchanged(
    fresh_store,
):
    _local_store, store = fresh_store
    with store._write_lock:
        store._conn.execute(
            "CREATE VIEW assistant_secret AS SELECT 1 AS value"
        )
        before = store._conn.execute(
            "SELECT current_setting('enable_external_access')"
        ).fetchone()[0]

    result = store.query_assistant_sql(
        sql="SELECT value FROM assistant_secret"
    )
    assert result["rows"] == []
    assert result["error"]
    after = store._conn.execute(
        "SELECT current_setting('enable_external_access')"
    ).fetchone()[0]
    assert after == before


def test_assistant_query_timeout_interrupts_only_its_cursor(fresh_store):
    _local_store, store = fresh_store
    with store._write_lock:
        store._conn.execute(
            """
            INSERT INTO events
                (id, agent_type, node_id, agent_id, event_type, ts, created_at)
            SELECT
                'assistant-timeout-' || CAST(i AS VARCHAR),
                'openclaw', 'local', 'assistant-test', 'message',
                '2026-01-01T00:00:00Z', i
            FROM range(1000) AS source(i)
            """
        )
        before = store._conn.execute(
            "SELECT current_setting('enable_external_access')"
        ).fetchone()[0]

    result = store.query_assistant_sql(
        sql="SELECT count(*) AS n FROM events a, events b, events c",
        timeout_secs=0.05,
    )
    assert result["rows"] == []
    assert "timed out" in result["error"].lower()
    assert store._conn.execute("SELECT 1").fetchone() == (1,)
    after = store._conn.execute(
        "SELECT current_setting('enable_external_access')"
    ).fetchone()[0]
    assert after == before


def test_assistant_methods_are_daemon_allowlisted():
    from routes.local_query import _DAEMON_METHODS

    assert {
        "query_assistant_conversations",
        "query_assistant_conversation",
        "save_assistant_conversation",
        "query_assistant_sql",
    } <= _DAEMON_METHODS


def test_planner_outcome_coverage_example_excludes_unknown_sentinels(fresh_store):
    from routes.assistant import _PLAN
    _local_store, store = fresh_store
    # Exercise the exact SQL taught to the planner, rather than asserting that
    # a prompt happens to contain words such as "unknown".
    expression = _PLAN.split("Use COUNT(CASE WHEN\n", 1)[1].split(" instead.", 1)[0]
    expression = "COUNT(CASE WHEN\n" + expression
    with store._write_lock:
        store._conn.executemany(
            "INSERT INTO sessions (agent_type, session_id, outcome, updated_at) VALUES ('openclaw', ?, ?, 1)",
            [(f"coverage-{index}", value) for index, value in enumerate(
                [None, "", " unknown ", "Unspecified", "completed"]
            )],
        )
    result = store.query_assistant_sql(sql="SELECT " + expression + " AS measured FROM sessions")
    assert result == {"rows": [{"measured": 1}]}


@pytest.mark.parametrize('table,insert', [
    ('events', "INSERT INTO events (id,agent_type,node_id,agent_id,event_type,ts,data,created_at) VALUES ('row','openclaw','local','main','message','2026-10-02',?,1)"),
    ('sessions', "INSERT INTO sessions (agent_type,session_id,metadata,updated_at) VALUES ('openclaw','row',?,1)"),
    ('memory_blobs', "INSERT INTO memory_blobs (agent_type,agent_id,path,blob,updated_at) VALUES ('openclaw','main','MEMORY.md',?,1)"),
    ('heartbeats', "INSERT INTO heartbeats (agent_type,node_id,ts,data) VALUES ('openclaw','local','2026-10-02',?)"),
    ('system_snapshots', "INSERT INTO system_snapshots (agent_type,node_id,ts,kind,data) VALUES ('openclaw','local','2026-10-02','system',?)"),
    ('crons', "INSERT INTO crons (agent_type,cron_id,data,updated_at) VALUES ('openclaw','row',?,1)"),
    ('subagents', "INSERT INTO subagents (agent_type,subagent_id,data,updated_at) VALUES ('openclaw','row',?,1)"),
])
def test_whole_row_and_json_queries_cannot_expose_payloads(fresh_store, table, insert):
    import json
    _local_store, store = fresh_store
    secret = 'PRIVATE_RAW_PAYLOAD_MUST_STAY_LOCAL'
    with store._write_lock:
        store._conn.execute(insert, [secret.encode()])
    for projection in ('record', 'to_json(record)'):
        result = store.query_assistant_sql(sql=f'SELECT {projection} AS result FROM {table} record')
        assert 'error' not in result, result
        assert len(result['rows']) == 1
        assert secret not in json.dumps(result, default=str)
        encoded = result['rows'][0]['result']
        if projection == 'to_json(record)':
            record = json.loads(encoded)
            assert not ({'data', 'blob', 'metadata'} & set(record))
            assert record['agent_type'] == 'openclaw'
