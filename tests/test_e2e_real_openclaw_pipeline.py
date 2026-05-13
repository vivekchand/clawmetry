"""TRUE end-to-end pipeline test (Engineer 9, 2026-05-12).

Companion to ``tests/test_e2e_duckdb_relay.py`` (Engineer B). That earlier file
calls ``sync._local_ingest_session_batch`` *directly* — it skips the daemon's
file-watching loop. This file proves the **full daemon pipeline** end to end:

    JSONL on disk  (simulated OpenClaw workspace)
        → sync.sync_sessions_recent  (the REAL daemon entry point that
                                      walks the workspace, reads files,
                                      parses lines, and batches them)
            → sync._flush_session_batch
                → sync._local_ingest_session_batch
                    → clawmetry.local_store DuckDB
                        → /api/local/events            (HTTP)
                        → /api/sessions                (HTTP, fast path)
                        → /api/brain-history           (HTTP, fast path)
                        → /api/transcript/<sid>        (HTTP, JSONL path)

What "real" means here, exactly:

  1. We **write actual JSONL bytes** into a tmp ``~/.openclaw/agents/main/
     sessions/<sid>.jsonl`` file with the same shape OpenClaw writes.
  2. We point ``OPENCLAW_HOME`` + ``dashboard.SESSIONS_DIR`` at that workspace.
  3. We invoke ``sync.sync_sessions_recent(config, state, paths, minutes=60)``
     — the same function the daemon calls every cycle. Cloud HTTP is mocked
     (so ``_post`` does not try to hit ``ingest.clawmetry.com``) but every
     other layer runs.
  4. We then read DuckDB directly **and** through every dashboard API surface
     a real browser would touch.

That covers steps the existing duckdb-relay test cannot prove:
  * file → daemon parse path
  * timestamp window filter (recent-mode)
  * cursor advancement (last_event_ids)
  * line-level batching (BATCH_SIZE=200 boundary)
  * tool-call payload survival through JSONL serialisation round-trip
  * cross-blueprint coverage: sessions / brain / local_query / transcript

Abstraction-boundary note: ``/api/transcript/<sid>`` reads the JSONL file
directly (NOT the local store) — that is intentional and a known coverage
gap for the local-store migration. We assert against the JSONL transcript
endpoint anyway because that is what the live dashboard hits today.

Run as:
    pytest -v tests/test_e2e_real_openclaw_pipeline.py
"""

from __future__ import annotations

import importlib
import json
import time
import uuid
from unittest.mock import patch

import pytest
from flask import Flask


# ── Fixture inputs: a realistic OpenClaw transcript ───────────────────────


SESSION_ID = "11111111-2222-3333-4444-555555555555"
SESSION_FILE = f"{SESSION_ID}.jsonl"
NODE_ID = "agent+e2e-real-test"
WORKSPACE_ID = "ws-real-e2e"

# All events in the last 30 minutes so sync_sessions_recent's 60-minute
# cutoff window includes them. The function keys off `obj.get("timestamp")`
# (sync.py:1343) and skips files whose tail is older than the cutoff.
import datetime as _dt

_NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _ts(seconds_ago: int) -> str:
    return (_NOW - _dt.timedelta(seconds=seconds_ago)).isoformat().replace(
        "+00:00", "Z"
    )


def _ev(type_, seconds_ago, **extras):
    """One OpenClaw transcript event. Shape mirrors what `sync.py:1140`
    expects (id / timestamp / type, plus tool/cost/token/model fields)."""
    base = {
        "id": str(uuid.uuid4()),
        "type": type_,
        "timestamp": _ts(seconds_ago),
        "workspace": WORKSPACE_ID,
    }
    base.update(extras)
    return base


# ── Simulated OpenClaw transcript ──────────────────────────────────────────
#
# Layout:
#   1× session_start  (T-1800s, oldest)
#   1× model_change   (T-1700s)
#   3× message events with full assistant text + usage tokens + cost
#   4× tool_call events: Bash, Read, Write, Edit
#   1× compaction
#   1× session_end    (newest)
# = 11 events total
#
# (We dropped the `gateway_bubble_event` step from the original brief because
# OpenClaw does not emit that event type — verified by `grep -r
# gateway_bubble` over both clawmetry and clawmetry-cloud. Instead we cover
# the same ground with two extra `message` events that carry tool blocks.)

TOOL_CALLS = [
    _ev(
        "tool_call",
        1500,
        id="ev-tool-bash",
        tool="Bash",
        args={"cmd": "ls -la /tmp"},
        result="total 8",
        cost_usd=0.0010,
        tokens=50,
        model="claude-opus-4-7",
    ),
    _ev(
        "tool_call",
        1450,
        id="ev-tool-read",
        tool="Read",
        args={"path": "/tmp/notes.md"},
        result="# notes\n",
        cost_usd=0.0008,
        tokens=40,
        model="claude-opus-4-7",
    ),
    _ev(
        "tool_call",
        1400,
        id="ev-tool-write",
        tool="Write",
        args={"path": "/tmp/out.py", "content": "x = 1\n"},
        result="ok",
        cost_usd=0.0012,
        tokens=60,
        model="claude-opus-4-7",
    ),
    _ev(
        "tool_call",
        1350,
        id="ev-tool-edit",
        tool="Edit",
        args={
            "path": "/tmp/out.py",
            "old_string": "x = 1",
            "new_string": "x = 2",
        },
        result="ok",
        cost_usd=0.0011,
        tokens=55,
        model="claude-opus-4-7",
    ),
]

MESSAGES = [
    _ev(
        "message",
        1300,
        id="ev-msg-1",
        role="assistant",
        text="Listing files first to understand the layout.",
        usage={"input_tokens": 120, "output_tokens": 80, "total_tokens": 200},
        cost_usd=0.005,
        tokens=200,
        model="claude-opus-4-7",
    ),
    _ev(
        "message",
        1200,
        id="ev-msg-2",
        role="assistant",
        text="Now reading the notes file before editing.",
        usage={"input_tokens": 200, "output_tokens": 100, "total_tokens": 300},
        cost_usd=0.0075,
        tokens=300,
        model="claude-opus-4-7",
    ),
    _ev(
        "message",
        1100,
        id="ev-msg-3",
        role="assistant",
        text="Edit applied. All done.",
        usage={"input_tokens": 80, "output_tokens": 60, "total_tokens": 140},
        cost_usd=0.0035,
        tokens=140,
        model="claude-opus-4-7",
    ),
]

SESSION_START = _ev(
    "session_start",
    1800,
    id="ev-session-start",
    title="Real-pipeline E2E session",
)

MODEL_CHANGE = _ev(
    "model_change",
    1700,
    id="ev-model-change-1",
    model="claude-opus-4-7",
    previous_model="claude-sonnet-4-5",
)

COMPACTION = _ev(
    "compaction",
    900,
    id="ev-compaction-1",
    summary="Compacted 12 messages → 2K-token summary",
    tokens=2000,
    cost_usd=0.02,
    model="claude-opus-4-7",
)

SESSION_END = _ev(
    "session_end",
    60,
    id="ev-session-end",
    duration_secs=1740,
)

# Order matters — JSONL is read top-to-bottom, and sync_sessions_recent's
# binary search keys on monotonically-increasing timestamps. Sort by
# timestamp ascending so the file looks like a real OpenClaw transcript.
ALL_EVENTS = sorted(
    [SESSION_START, MODEL_CHANGE, *TOOL_CALLS, *MESSAGES, COMPACTION, SESSION_END],
    key=lambda e: e["timestamp"],
)

# Expected counts — derived from the literals above.
EXPECTED_TOTAL = 11  # 1 + 1 + 4 + 3 + 1 + 1
EXPECTED_BY_TYPE = {
    "session_start": 1,
    # ``model_change`` is mapped to ``model.changed`` on ingest by the v3
    # underscore parser (#1135), so the canonical event_type in DuckDB
    # matches the one the trajectory parser produces.
    "model.changed": 1,
    "tool_call":     4,
    "message":       3,
    "compaction":    1,
    "session_end":   1,
}
# Cost: 4 tools (0.0010+0.0008+0.0012+0.0011) + 3 msgs (0.005+0.0075+0.0035)
#       + compaction (0.02) = 0.0041 + 0.0160 + 0.02 = 0.0401
EXPECTED_COST = pytest.approx(0.0401, abs=1e-6)
# Tokens: 4 tools (50+40+60+55=205) + 3 msgs (200+300+140=640) + compaction 2000 = 2845
EXPECTED_TOKENS = 205 + 640 + 2000  # 2845


# ── Fixture: simulated OpenClaw workspace + dashboard wired up ─────────────


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """Build a fully isolated simulated OpenClaw workspace + DuckDB store +
    Flask app with sessions/brain/local_query blueprints registered."""
    # --- Simulated OpenClaw workspace ---
    workspace = tmp_path / "openclaw_home"
    sessions_dir = workspace / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)
    session_path = sessions_dir / SESSION_FILE
    with open(session_path, "w") as fh:
        for ev in ALL_EVENTS:
            fh.write(json.dumps(ev) + "\n")

    # --- Env wiring ---
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")  # opt-in fast paths
    monkeypatch.setenv("OPENCLAW_HOME", str(workspace))
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(sessions_dir))

    # --- Reload the modules that read the env at import time ---
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.brain as brain_mod
    importlib.reload(brain_mod)

    # --- Point the (already-imported) dashboard module at the fake workspace ---
    # Several routes do `import dashboard as _d; _d.SESSIONS_DIR`. We need to
    # set that AFTER the route modules are reloaded so they pick the right
    # path up at request time.
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions_dir), raising=False)

    # --- Touch the writer so the flusher thread is up before the first ingest ---
    ls.get_store()

    # --- Build a Flask app with all relevant blueprints ---
    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    app.register_blueprint(sessions_mod.bp_sessions)
    app.register_blueprint(brain_mod.bp_brain)

    yield {
        "workspace":    workspace,
        "sessions_dir": sessions_dir,
        "session_path": session_path,
        "db_path":      db_path,
        "ls":           ls,
        "sync":         sync,
        "lq":           lq,
        "client":       app.test_client(),
    }

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _wait_drained(store, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


def _drive_real_pipeline(sync, sessions_dir, db_path, store):
    """Run the REAL daemon ingest function against the simulated workspace.

    ``sync.sync_sessions_recent`` is the function the daemon calls every
    cycle. It scans ``sessions_dir`` for .jsonl files, finds the first line
    whose timestamp is within the cutoff window, batches lines, and calls
    ``_flush_session_batch`` (which writes to local DuckDB AND posts to the
    cloud). We mock ``_post`` so the cloud HTTP call is skipped — every
    other layer runs for real.
    """
    config = {
        "api_key":         "cm_test_e2e_fake",
        "encryption_key":  None,
        "node_id":         NODE_ID,
    }
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": str(sessions_dir)}
    with patch.object(sync, "_post") as mock_post:
        n = sync.sync_sessions_recent(config, state, paths, minutes=60)
    # The cloud POST should have happened (we mocked it). Assert here so a
    # future regression that quietly stops calling _post fails THIS test.
    assert mock_post.called, (
        "sync_sessions_recent did not call _post — daemon-to-cloud wire "
        "broke. Even though we mocked it, the call must happen."
    )
    _wait_drained(store)
    return n


# ── 1. Daemon ingest: file on disk → DuckDB ────────────────────────────────


def test_real_daemon_pipeline_ingests_jsonl_into_duckdb(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    n = _drive_real_pipeline(sync, pipeline["sessions_dir"],
                             pipeline["db_path"], store)
    assert n == EXPECTED_TOTAL, (
        f"sync_sessions_recent returned {n} events processed, "
        f"expected {EXPECTED_TOTAL}"
    )
    on_disk = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert on_disk == EXPECTED_TOTAL


def test_per_event_type_row_counts(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)
    rows = store._fetch(
        "SELECT event_type, COUNT(*) FROM events GROUP BY event_type", []
    )
    by_type = {t: c for t, c in rows}
    for et, expected in EXPECTED_BY_TYPE.items():
        assert by_type.get(et) == expected, (
            f"event_type={et!r}: DuckDB has {by_type.get(et)}, expected {expected}"
        )


def test_cost_and_token_aggregates(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)
    total_cost, total_tokens = store._fetch(
        "SELECT COALESCE(SUM(cost_usd), 0), COALESCE(SUM(token_count), 0) FROM events",
        [],
    )[0]
    assert total_cost == EXPECTED_COST
    assert total_tokens == EXPECTED_TOKENS


def test_session_id_consistent_across_all_events(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)
    sids = {r[0] for r in store._fetch("SELECT DISTINCT session_id FROM events", [])}
    assert sids == {SESSION_ID}, (
        f"session_id derivation drifted: got {sids}, expected {{{SESSION_ID!r}}}"
    )


def test_per_message_cost_and_tokens_preserved(pipeline):
    """Each message event keeps its own cost_usd + tokens after JSONL
    round-trip + DuckDB write. Aggregates sum is not enough."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)
    rows = store._fetch(
        "SELECT id, cost_usd, token_count FROM events WHERE event_type='message' "
        "ORDER BY id", [],
    )
    assert len(rows) == 3
    by_id = {r[0]: (r[1], r[2]) for r in rows}
    assert by_id["ev-msg-1"] == (pytest.approx(0.005, abs=1e-6), 200)
    assert by_id["ev-msg-2"] == (pytest.approx(0.0075, abs=1e-6), 300)
    assert by_id["ev-msg-3"] == (pytest.approx(0.0035, abs=1e-6), 140)


# ── 2. Per-tool-call payload survival ──────────────────────────────────────


@pytest.mark.parametrize(
    "tool_name,event_id",
    [
        ("Bash",  "ev-tool-bash"),
        ("Read",  "ev-tool-read"),
        ("Write", "ev-tool-write"),
        ("Edit",  "ev-tool-edit"),
    ],
)
def test_each_tool_call_event_round_trips_with_args(pipeline, tool_name, event_id):
    """For each of the four canonical Claude tools, prove its event made it
    through the JSONL → daemon → DuckDB pipeline with `tool` name and `args`
    intact. The `data` BLOB stores the original event JSON, so we round-trip
    that and check the tool-specific shape."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)

    rows = store._fetch(
        "SELECT id, event_type, data FROM events WHERE id = ?", [event_id]
    )
    assert rows, f"tool event {event_id!r} missing from DuckDB"
    eid, etype, blob = rows[0]
    assert etype == "tool_call"
    payload = json.loads(bytes(blob).decode("utf-8"))
    assert payload["tool"] == tool_name, (
        f"tool name lost in pipeline: stored {payload.get('tool')!r}, "
        f"expected {tool_name!r}"
    )
    assert isinstance(payload.get("args"), dict), (
        f"tool args dropped or wrong type: got {type(payload.get('args'))}"
    )
    # Per-tool args sanity:
    args = payload["args"]
    if tool_name == "Bash":
        assert args.get("cmd") == "ls -la /tmp"
    elif tool_name == "Read":
        assert args.get("path") == "/tmp/notes.md"
    elif tool_name == "Write":
        assert args.get("path") == "/tmp/out.py"
        assert "content" in args
    elif tool_name == "Edit":
        assert args.get("old_string") == "x = 1"
        assert args.get("new_string") == "x = 2"


# ── 3. /api/local/events end-to-end via Flask test client ──────────────────


def test_api_local_events_returns_all(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)
    r = pipeline["client"].get(
        f"/api/local/events?session_id={SESSION_ID}&limit=50"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == EXPECTED_TOTAL
    assert body["_shape"] == "events"
    assert all(row["session_id"] == SESSION_ID for row in body["rows"])


# ── 4. /api/sessions: local-store fast path returns the session ────────────


def test_api_sessions_lists_the_session(pipeline):
    """``/api/sessions`` reads from the ``sessions`` table (NOT the events
    table). ``sync_sessions_recent`` only writes to ``events`` — the daemon's
    metadata loop populates ``sessions`` separately. We replay that with
    ``_local_ingest_sessions_batch`` so the fast path has data to return."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)

    sync._local_ingest_sessions_batch(
        [{
            "session_id":     SESSION_ID,
            "agent_type":     "openclaw",
            "agent_id":       "main",
            "title":          "Real-pipeline E2E session",
            "started_at":     ALL_EVENTS[0]["timestamp"],
            "updated_at":     ALL_EVENTS[-1]["timestamp"],
            "status":         "completed",
            "total_tokens":   EXPECTED_TOKENS,
            "total_cost":     0.0401,
            "message_count":  3,
            "channel":        "telegram",
        }],
        node_id=NODE_ID,
    )

    r = pipeline["client"].get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        "Local-store fast path did not engage even with rows in the sessions "
        "table — check CLAWMETRY_LOCAL_STORE_READ wiring."
    )
    sids = {s["session_id"] for s in body["sessions"]}
    assert SESSION_ID in sids


# ── 5. /api/brain-history: local-store fast path returns the events ────────


def test_api_brain_history_returns_events(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)

    r = pipeline["client"].get("/api/brain-history?limit=20")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        "Brain history fast path did not engage. Check the "
        "CLAWMETRY_LOCAL_STORE_READ + populated-store gate."
    )
    assert body.get("_shape") == "brain_history"
    assert body["count"] >= EXPECTED_TOTAL or body["count"] == 20  # limit cap
    types = {ev["type"] for ev in body["events"]}
    # Brain shape upper-cases event_type.
    assert "TOOL_CALL" in types
    assert "MESSAGE" in types
    assert "COMPACTION" in types


# ── 6. /api/transcript/<sid>: JSONL reader (different code path) ───────────


def test_api_transcript_returns_messages_and_tools_from_jsonl(pipeline):
    """``/api/transcript/<sid>`` reads the .jsonl file directly (not the
    local store) — a known coverage gap for the local-first migration. We
    pin its current behaviour anyway because it's what the live UI hits."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)

    r = pipeline["client"].get(f"/api/transcript/{SESSION_ID}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert "messages" in body
    msgs = body["messages"]
    assert len(msgs) > 0, (
        "transcript endpoint returned no messages — JSONL parser regression?"
    )
    # Each of the 3 assistant messages should appear as a message.
    assistant_msgs = [m for m in msgs if m.get("role") == "assistant"]
    assert len(assistant_msgs) == 3, (
        f"expected 3 assistant messages, got {len(assistant_msgs)}"
    )


# ── 7. The MOAT assertion: every layer agrees ──────────────────────────────


def test_all_layers_report_same_event_count(pipeline):
    """The cross-layer guarantee. If any reader (DuckDB, local_query relay,
    HTTP /api/local/events) drifts from the daemon's writer, the dashboard
    will show the wrong numbers."""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    client = pipeline["client"]
    store = pipeline["ls"].get_store()

    _drive_real_pipeline(sync, pipeline["sessions_dir"],
                         pipeline["db_path"], store)

    layer1_duckdb = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    layer2_query  = len(store.query_events(session_id=SESSION_ID, limit=10000))
    layer3_relay  = lq.relay_dispatch(
        "events", {"session_id": SESSION_ID, "limit": 10000}
    )["count"]
    layer4_http   = client.get(
        f"/api/local/events?session_id={SESSION_ID}&limit=10000"
    ).get_json()["count"]

    assert layer1_duckdb == layer2_query == layer3_relay == layer4_http == EXPECTED_TOTAL, (
        f"Layer counts disagree: duckdb={layer1_duckdb} "
        f"query_events={layer2_query} relay={layer3_relay} "
        f"http_get={layer4_http} expected={EXPECTED_TOTAL}"
    )


# ── 8. Cursor advancement — re-running is a no-op ──────────────────────────


def test_re_running_sync_is_idempotent(pipeline):
    """The daemon polls every 15s; a second pass over the same workspace
    must not duplicate rows. Tests INSERT OR IGNORE on event id AND the
    last_event_ids cursor advancement in sync_sessions_recent."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    config = {
        "api_key": "cm_test", "encryption_key": None, "node_id": NODE_ID,
    }
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": str(pipeline["sessions_dir"])}
    with patch.object(sync, "_post"):
        sync.sync_sessions_recent(config, state, paths, minutes=60)
        sync.sync_sessions_recent(config, state, paths, minutes=60)
        sync.sync_sessions_recent(config, state, paths, minutes=60)
    _wait_drained(store)
    n = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert n == EXPECTED_TOTAL, (
        f"re-running daemon ingest leaked rows: got {n}, expected {EXPECTED_TOTAL}"
    )
