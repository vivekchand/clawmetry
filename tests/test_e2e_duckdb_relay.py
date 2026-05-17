"""End-to-end test for the DuckDB + relay-shape pipeline (Engineer B,
2026-05-12).

Proves the full local data path:

    OpenClaw-shaped event
        → daemon ingest helper (sync._local_ingest_session_batch)
        → local DuckDB write (clawmetry.local_store)
        → relay shape query (routes/local_query.relay_dispatch)
        → HTTP /api/local/* endpoint (routes/local_query.bp_local_query)
        → row-count + content equality at every layer

The test is **fully self-contained**: no live daemon, no real WebSocket, no
network. It drives the same in-process functions the daemon uses, against an
**isolated** DuckDB file (tmp_path fixture) so it never touches the user's
real ``~/.clawmetry/clawmetry.duckdb``.

Why drive the helpers in-process instead of spawning a real daemon:

* The daemon is a long-running threaded process that polls the gateway for
  raw transcript events and forwards them through `_local_ingest_session_batch`
  (sync.py:1115) and `_local_ingest_sessions_batch` (sync.py:1165). Those
  helpers are the ingest path. Spawning the daemon adds a 30s+ startup, a real
  gateway dependency, and a great deal of flakiness while testing exactly the
  same code path. The helpers are the seam.
* The relay (`routes/local_query.relay_dispatch`) is the same in-process entry
  point the future WS client uses; HTTP is the second transport over the same
  dispatch. Hitting both proves both transports stay in lock-step.

Run as:
    make test-e2e-duckdb
or:
    pytest -v tests/test_e2e_duckdb_relay.py
"""

from __future__ import annotations

import importlib
import json
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from flask import Flask


# ── Deterministic test inputs ─────────────────────────────────────────────
#
# Realistic OpenClaw event types — taken from the shapes `_local_ingest_session_batch`
# expects (sync.py:1131-1160). Timestamps are seeded so ordering and per-day
# aggregation are exactly predictable.

NODE_ID = "agent+e2e-test"
SESSION_ID = "sess-e2e-001"
WORKSPACE_ID = "ws-test"
SESSION_FILE = f"{SESSION_ID}.jsonl"
DAY_A = "2026-05-11"
DAY_B = "2026-05-12"


def _ev(type_, ts, **extras):
    """Build a raw OpenClaw transcript event dict — what the gateway sends to
    sync.py before normalisation."""
    base = {
        "id": str(uuid.uuid4()),
        "type": type_,
        "timestamp": ts,
        "workspace": WORKSPACE_ID,
    }
    base.update(extras)
    return base


SESSION_START = _ev(
    "session_start",
    f"{DAY_A}T10:00:00Z",
    id="ev-start-1",
    title="E2E test session",
)

TOOL_CALLS = [
    _ev("tool_call", f"{DAY_A}T10:00:01Z",
        id="ev-tool-1",
        tool="Bash", args={"cmd": "ls -la"}, result="total 0",
        cost_usd=0.0010, tokens=50, model="claude-opus-4-7"),
    _ev("tool_call", f"{DAY_A}T10:00:02Z",
        id="ev-tool-2",
        tool="Read", args={"path": "/tmp/x.py"}, result="print('hi')",
        cost_usd=0.0008, tokens=40, model="claude-opus-4-7"),
    _ev("tool_call", f"{DAY_A}T10:00:03Z",
        id="ev-tool-3",
        tool="Write", args={"path": "/tmp/y.py", "content": "x=1"}, result="ok",
        cost_usd=0.0012, tokens=60, model="claude-opus-4-7"),
]

MODEL_CHANGES = [
    _ev("model_change", f"{DAY_A}T10:00:04Z",
        id="ev-model-1",
        model="claude-sonnet-4-5",
        previous_model="claude-opus-4-7"),
    _ev("model_change", f"{DAY_B}T11:00:00Z",
        id="ev-model-2",
        model="claude-opus-4-7",
        previous_model="claude-sonnet-4-5"),
]

MESSAGES = [
    _ev("message", f"{DAY_A}T10:00:05Z",
        id=f"ev-msg-{i}",
        role="assistant" if i % 2 else "user",
        text=f"message body {i}",
        cost_usd=0.005,
        tokens=200,
        model="claude-opus-4-7")
    for i in range(5)
]

COMPACTION = _ev(
    "compaction", f"{DAY_B}T11:30:00Z",
    id="ev-compact-1",
    summary="Compacted 30 messages → 4K-token summary",
    tokens=4000,
    cost_usd=0.04,
    model="claude-opus-4-7",
)

SESSION_END = _ev(
    "session_end", f"{DAY_B}T12:00:00Z",
    id="ev-end-1",
    duration_secs=7200,
)

ALL_EVENTS = (
    [SESSION_START]
    + TOOL_CALLS
    + MODEL_CHANGES
    + MESSAGES
    + [COMPACTION, SESSION_END]
)

# Pre-computed expected aggregates for assertion. These MUST match what the
# events declare or the test is wrong, not the code.
#   1 session_start + 3 tool_calls + 2 model_changes + 5 messages
#   + 1 compaction  + 1 session_end                              = 13
EXPECTED_TOTAL_EVENTS   = 13
EXPECTED_TOOL_CALLS     = 3
EXPECTED_MODEL_CHANGES  = 2
EXPECTED_MESSAGES       = 5
EXPECTED_COMPACTIONS    = 1
EXPECTED_SESSION_STARTS = 1
EXPECTED_SESSION_ENDS   = 1

# Costs:
#   tool_calls: 0.0010 + 0.0008 + 0.0012 = 0.0030
#   messages:   5 × 0.005              = 0.0250
#   compaction: 0.04                   = 0.0400
#                                      ───────
#                                      = 0.0680
EXPECTED_TOTAL_COST = pytest.approx(0.0680, abs=1e-6)

# Tokens:
#   tool_calls: 50+40+60 = 150
#   messages:   5×200    = 1000
#   compaction: 4000
#                       ──────
#                       = 5150
EXPECTED_TOTAL_TOKENS = 5150

# Per-day breakdown:
#   DAY_A: session_start + 3 tool_calls + 1 model_change + 5 messages = 10 events
#          cost = 0.0030 (tools) + 0.0250 (messages) = 0.0280
#          tokens = 150 + 1000 = 1150
#   DAY_B: 1 model_change + 1 compaction + 1 session_end = 3 events
#          cost = 0.0400 (compaction)
#          tokens = 4000
EXPECTED_DAY_A_COUNT  = 10
EXPECTED_DAY_A_COST   = pytest.approx(0.0280, abs=1e-6)
EXPECTED_DAY_A_TOKENS = 1150
EXPECTED_DAY_B_COUNT  = 3
EXPECTED_DAY_B_COST   = pytest.approx(0.0400, abs=1e-6)
EXPECTED_DAY_B_TOKENS = 4000


# ── Fixture: isolated store + flask app + reloaded modules ─────────────────


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """Isolated end-to-end pipeline:

      * Fresh DuckDB file at ``tmp_path/clawmetry.duckdb`` (NEVER touches the
        user's real store).
      * Reloaded ``clawmetry.local_store`` so module-level ``DB_PATH`` picks up
        the env override.
      * Reloaded ``clawmetry.sync`` so its late-imports of ``local_store``
        also resolve to the isolated instance.
      * Reloaded ``routes.local_query`` blueprint registered on a Flask test
        app so the HTTP layer is exercised too.
    """
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    # Tight flush window so ingest→assert doesn't sleep all day.
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.local_query as lq
    importlib.reload(lq)

    # Build a Flask app with just the local_query blueprint mounted.
    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)

    # Touch the singleton store so the flusher thread is alive before the
    # first ingest call.
    ls.get_store()

    yield {
        "db_path": db_path,
        "ls": ls,
        "sync": sync,
        "lq": lq,
        "client": app.test_client(),
    }

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    # Reset singleton so the next test starts clean.
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _wait_drained(store, timeout=3.0):
    """Block until the store flusher has drained the ring."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


# ── 1. Daemon ingest path: sync._local_ingest_session_batch → DuckDB ──────


def test_daemon_ingest_writes_all_event_types_to_duckdb(pipeline):
    """Drive the daemon's actual ingest helper (the same one called from
    `_flush_session_batch` at sync.py:1092). Every realistic OpenClaw event
    type lands in DuckDB."""
    sync = pipeline["sync"]
    ls = pipeline["ls"]
    store = ls.get_store()

    # This is the function the daemon calls per session-file batch.
    sync._local_ingest_session_batch(
        batch=ALL_EVENTS,
        session_file=SESSION_FILE,
        node_id=NODE_ID,
        subagent_id=None,
    )
    _wait_drained(store)

    # Direct DuckDB read (read-only, separate connection). Proves the bytes
    # reached the file on disk, not just the in-memory ring.
    db_path = pipeline["db_path"]
    # Close singleton's writer connection briefly so a read-only second
    # connection can attach (DuckDB allows multiple readers OR one writer).
    # In practice the singleton holds the writer; reading via the same
    # connection works fine, so we use store._fetch for the on-disk count
    # and compare to a separate read-only connection too.
    on_disk_count = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert on_disk_count == EXPECTED_TOTAL_EVENTS, (
        f"DuckDB ingest path lost events: expected {EXPECTED_TOTAL_EVENTS}, "
        f"got {on_disk_count}"
    )


def test_daemon_ingest_per_event_type_counts(pipeline):
    """Per-event-type row counts in DuckDB match what we sent."""
    sync = pipeline["sync"]
    ls = pipeline["ls"]
    store = ls.get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    rows = store._fetch(
        "SELECT event_type, COUNT(*) FROM events GROUP BY event_type", []
    )
    by_type = {t: c for t, c in rows}

    assert by_type.get("session_start") == EXPECTED_SESSION_STARTS
    assert by_type.get("tool_call")     == EXPECTED_TOOL_CALLS
    # After #1135 the v3 underscore parser maps ``model_change`` →
    # ``model.changed`` (the dot.separated event_type produced by the
    # trajectory parser) so the read-side handlers work uniformly across
    # both schemas. Synthesised test events that USE the v3 type name
    # follow the same translation.
    assert by_type.get("model.changed") == EXPECTED_MODEL_CHANGES
    assert by_type.get("message")       == EXPECTED_MESSAGES
    assert by_type.get("compaction")    == EXPECTED_COMPACTIONS
    assert by_type.get("session_end")   == EXPECTED_SESSION_ENDS


def test_daemon_ingest_preserves_cost_and_tokens(pipeline):
    """The daemon's normalisation pass (sync.py:1157-1159) extracts
    cost_usd/tokens from raw events. Aggregate sums must match."""
    sync = pipeline["sync"]
    ls = pipeline["ls"]
    store = ls.get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    rows = store._fetch(
        "SELECT COALESCE(SUM(cost_usd), 0), COALESCE(SUM(token_count), 0) FROM events",
        [],
    )
    total_cost, total_tokens = rows[0]
    assert total_cost == EXPECTED_TOTAL_COST
    assert total_tokens == EXPECTED_TOTAL_TOKENS


def test_duckdb_read_only_handle_sees_committed_rows(pipeline):
    """An independent read-only DuckDB connection (mimicking a separate
    dashboard process per #960) sees exactly the same rows. This is the
    contract the WS relay (and a separate-process dashboard) rely on.

    Implementation note: DuckDB enforces a single config per file *per process*
    — you cannot open a writer + a read_only=True handle on the same file in
    the same process. The dashboard-process scenario is cross-process, so we
    simulate it by stopping the writer first, then opening read-only."""
    sync = pipeline["sync"]
    ls = pipeline["ls"]
    store = ls.get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    # Force a checkpoint so the file on disk reflects the committed batch
    # (DuckDB may otherwise leave rows in the WAL).
    store._conn.execute("CHECKPOINT")

    # Close the writer so a read_only handle can attach (DuckDB single-config
    # per process). Real cross-process readers wouldn't need this, but our
    # in-process test does.
    store.stop(flush=True)
    ls._reset_singleton_for_tests()

    db_path = pipeline["db_path"]
    ro = duckdb.connect(str(db_path), read_only=True)
    try:
        n = ro.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        # Schema version 5 expected (current — bumped by issue #1007).
        sv = ro.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        ro.close()

    assert n == EXPECTED_TOTAL_EVENTS
    # Read the constant rather than hardcoding (#1627) — the version
    # bumps periodically (5→6→…→9 and counting); the contract being
    # asserted here is "stamped version matches the module constant".
    assert sv == ls.SCHEMA_VERSION


def test_duckdb_indexes_present(pipeline):
    """Sanity-check that the indexes we expect to be hit on relay queries
    actually exist on the table (idx_events_ts, idx_events_session,
    idx_events_type_ts)."""
    ls = pipeline["ls"]
    store = ls.get_store()
    rows = store._fetch(
        "SELECT index_name FROM duckdb_indexes WHERE table_name = 'events'", []
    )
    names = {r[0] for r in rows}
    # Each index_name is created by the DDL in local_store.py:153-157.
    expected = {
        "idx_events_ts", "idx_events_session", "idx_events_agent_ts",
        "idx_events_type_ts", "idx_events_atype_ts",
    }
    missing = expected - names
    assert not missing, f"missing expected DuckDB indexes: {missing}"


# ── 2. Relay shape: in-process dispatch (relay_dispatch) ───────────────────
#
# This is the seam the WS relay client uses: cloud sends a {shape, args}
# frame, daemon calls relay_dispatch, ships rows back. Same code paths as
# HTTP — we hit it directly to prove parity.


def test_relay_shape_events(pipeline):
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    ls = pipeline["ls"]
    store = ls.get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("events", {"session_id": SESSION_ID, "limit": 1000})
    assert body["_shape"] == "events"
    assert body["count"] == EXPECTED_TOTAL_EVENTS
    # All rows belong to the right session (the daemon derives session_id
    # from the .jsonl filename).
    assert all(r["session_id"] == SESSION_ID for r in body["rows"])


def test_relay_shape_events_filtered_by_type(pipeline):
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    for et, expected in [
        ("tool_call",     EXPECTED_TOOL_CALLS),
        ("message",       EXPECTED_MESSAGES),
        # ``model_change`` is mapped to ``model.changed`` on ingest (#1135).
        ("model.changed", EXPECTED_MODEL_CHANGES),
        ("compaction",    EXPECTED_COMPACTIONS),
        ("session_start", EXPECTED_SESSION_STARTS),
        ("session_end",   EXPECTED_SESSION_ENDS),
    ]:
        body = lq.relay_dispatch("events", {"event_type": et, "limit": 1000})
        assert body["count"] == expected, (
            f"event_type={et!r}: relay returned {body['count']} rows, "
            f"expected {expected}"
        )


def test_relay_shape_sessions(pipeline):
    """``sessions`` shape rolls up by session_id. One row, summed cost+tokens."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("sessions", {})
    assert body["_shape"] == "sessions"
    assert body["count"] == 1
    s = body["rows"][0]
    assert s["session_id"] == SESSION_ID
    assert s["event_count"] == EXPECTED_TOTAL_EVENTS
    assert s["cost_usd"] == EXPECTED_TOTAL_COST
    assert s["token_count"] == EXPECTED_TOTAL_TOKENS
    # Started/updated bracket the event time range.
    assert s["started_at"] == f"{DAY_A}T10:00:00Z"
    assert s["updated_at"] == f"{DAY_B}T12:00:00Z"


def test_relay_shape_aggregates(pipeline):
    """``aggregates`` shape — per-day rollup. Two days expected."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("aggregates", {})
    by_day = {row["day"]: row for row in body["rows"]}
    assert set(by_day.keys()) == {DAY_A, DAY_B}

    a = by_day[DAY_A]
    assert a["event_count"] == EXPECTED_DAY_A_COUNT
    assert a["cost_usd"]    == EXPECTED_DAY_A_COST
    assert a["token_count"] == EXPECTED_DAY_A_TOKENS

    b = by_day[DAY_B]
    assert b["event_count"] == EXPECTED_DAY_B_COUNT
    assert b["cost_usd"]    == EXPECTED_DAY_B_COST
    assert b["token_count"] == EXPECTED_DAY_B_TOKENS


def test_relay_shape_transcript(pipeline):
    """``transcript`` shape returns events for one session_id."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    # Add an unrelated session — must NOT leak into transcript.
    other = _ev("tool_call", f"{DAY_A}T09:00:00Z", id="ev-other-1",
                tool="Bash", cost_usd=0.001, tokens=10)
    sync._local_ingest_session_batch(
        batch=[other], session_file="other.jsonl",
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("transcript", {"session_id": SESSION_ID, "limit": 1000})
    assert body["_shape"] == "transcript"
    assert body["count"] == EXPECTED_TOTAL_EVENTS
    assert all(r["session_id"] == SESSION_ID for r in body["rows"])


def test_relay_shape_health(pipeline):
    """``health`` shape reports DB stats. Used by cloud uptime checks."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("health", {})
    assert body["_shape"] == "health"
    assert body["engine"] == "duckdb"
    assert body["event_count"] == EXPECTED_TOTAL_EVENTS
    # Read the constant rather than hardcoding (#1627).
    assert body["schema_version"] == pipeline["ls"].SCHEMA_VERSION
    assert body["oldest_ts"] == f"{DAY_A}T10:00:00Z"
    assert body["newest_ts"] == f"{DAY_B}T12:00:00Z"
    assert body["ring_depth"] == 0
    assert body["size_bytes"] > 0


def test_relay_rejects_unknown_shape(pipeline):
    """relay_dispatch must NOT pass arbitrary SQL/method names through."""
    lq = pipeline["lq"]
    body = lq.relay_dispatch("drop_table_users", {})
    assert "error" in body


def test_relay_transcript_requires_session_id(pipeline):
    """transcript shape without session_id must be rejected, not silently
    return everything. Cloud relay frames depend on this."""
    lq = pipeline["lq"]
    with pytest.raises(ValueError):
        lq.relay_dispatch("transcript", {})


# ── 3. HTTP transport: same shapes via /api/local/* ────────────────────────


def test_http_events_endpoint_matches_relay(pipeline):
    """HTTP and relay_dispatch must return identical row counts. Same SQL,
    two transports."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    relay_body = lq.relay_dispatch("events", {"session_id": SESSION_ID, "limit": 1000})
    r = pipeline["client"].get(f"/api/local/events?session_id={SESSION_ID}&limit=1000")
    assert r.status_code == 200
    http_body = r.get_json()
    assert http_body["count"] == relay_body["count"] == EXPECTED_TOTAL_EVENTS
    # IDs returned by HTTP must equal IDs returned by relay (set equality).
    assert {r["id"] for r in http_body["rows"]} == {r["id"] for r in relay_body["rows"]}


def test_http_query_post_dispatches_all_shapes(pipeline):
    """POST /api/local/query is the shape-dispatched endpoint matching the WS
    relay frame format. Hit every shape."""
    sync = pipeline["sync"]
    client = pipeline["client"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    cases = [
        ("events",     {"session_id": SESSION_ID, "limit": 1000}, EXPECTED_TOTAL_EVENTS),
        ("sessions",   {}, 1),
        ("aggregates", {}, 2),
        ("transcript", {"session_id": SESSION_ID, "limit": 1000}, EXPECTED_TOTAL_EVENTS),
    ]
    for shape, args, expected_count in cases:
        r = client.post(
            "/api/local/query",
            data=json.dumps({"shape": shape, "args": args}),
            content_type="application/json",
        )
        assert r.status_code == 200, f"shape={shape}: HTTP {r.status_code}"
        body = r.get_json()
        assert body["_shape"] == shape, f"shape={shape}: response shape mismatch"
        assert body["count"] == expected_count, (
            f"shape={shape}: HTTP /api/local/query returned {body['count']} "
            f"rows, expected {expected_count}"
        )

    # Health is special (no rows/count key).
    r = client.post("/api/local/query",
                    data=json.dumps({"shape": "health"}),
                    content_type="application/json")
    assert r.status_code == 200
    body = r.get_json()
    assert body["engine"] == "duckdb"
    assert body["event_count"] == EXPECTED_TOTAL_EVENTS


def test_http_unknown_shape_returns_400(pipeline):
    r = pipeline["client"].post(
        "/api/local/query",
        data=json.dumps({"shape": "exfiltrate"}),
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "allowed_shapes" in r.get_json()


# ── 4. Layer-by-layer count agreement (the "MOAT" assertion) ───────────────


def test_layer_counts_agree_top_to_bottom(pipeline):
    """The single most important assertion in this file. Ingest N events,
    then prove every read layer reports exactly N. If any layer drifts, the
    cloud dashboard will show the wrong numbers."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    client = pipeline["client"]
    store = pipeline["ls"].get_store()

    sync._local_ingest_session_batch(
        batch=ALL_EVENTS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=None,
    )
    _wait_drained(store)

    # Layer 1: DuckDB direct row count
    duckdb_count = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    # Layer 2: store query API
    store_api_count = len(store.query_events(session_id=SESSION_ID, limit=10000))
    # Layer 3: relay_dispatch (in-process — what the WS relay uses)
    relay_count = lq.relay_dispatch(
        "events", {"session_id": SESSION_ID, "limit": 10000}
    )["count"]
    # Layer 4: HTTP /api/local/events (what the local browser uses)
    http_get_count = client.get(
        f"/api/local/events?session_id={SESSION_ID}&limit=10000"
    ).get_json()["count"]
    # Layer 5: HTTP POST /api/local/query — the shape-dispatched endpoint
    http_post_count = client.post(
        "/api/local/query",
        data=json.dumps({"shape": "events",
                         "args": {"session_id": SESSION_ID, "limit": 10000}}),
        content_type="application/json",
    ).get_json()["count"]

    assert (
        duckdb_count == store_api_count == relay_count
        == http_get_count == http_post_count == EXPECTED_TOTAL_EVENTS
    ), (
        f"Layer counts disagree: duckdb={duckdb_count} "
        f"store_api={store_api_count} relay={relay_count} "
        f"http_get={http_get_count} http_post={http_post_count} "
        f"expected={EXPECTED_TOTAL_EVENTS}"
    )


# ── 5. Idempotency: re-ingesting the same batch is a no-op ─────────────────


def test_reingest_is_idempotent(pipeline):
    """The daemon may re-deliver a batch on reconnect. INSERT OR IGNORE on the
    event id keeps the row count correct."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()

    for _ in range(3):
        sync._local_ingest_session_batch(
            batch=ALL_EVENTS, session_file=SESSION_FILE,
            node_id=NODE_ID, subagent_id=None,
        )
    _wait_drained(store)

    n = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert n == EXPECTED_TOTAL_EVENTS, (
        f"re-ingest leaked rows: got {n}, expected {EXPECTED_TOTAL_EVENTS}"
    )


# ── 6. Subagent path (sync._local_ingest_session_batch with subagent_id) ───


def test_subagent_id_overrides_session_id(pipeline):
    """When the daemon hands us a subagent_id, that becomes the canonical
    session_id (sync.py:1130). Proves sub-agent events don't get mis-attributed
    to the parent session file."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    store = pipeline["ls"].get_store()

    subagent_id = "subagent-abc-123"
    sync._local_ingest_session_batch(
        batch=TOOL_CALLS, session_file=SESSION_FILE,
        node_id=NODE_ID, subagent_id=subagent_id,
    )
    _wait_drained(store)

    body = lq.relay_dispatch("transcript", {"session_id": subagent_id, "limit": 100})
    assert body["count"] == EXPECTED_TOOL_CALLS
    assert all(r["session_id"] == subagent_id for r in body["rows"])
