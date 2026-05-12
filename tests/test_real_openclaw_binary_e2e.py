"""TRUE end-to-end: spawn the real ``openclaw`` binary and prove its
session JSONL flows through the daemon → DuckDB → API.

Companion to ``tests/test_e2e_real_openclaw_pipeline.py`` (which fabricates
the JSONL by hand). That earlier test cannot catch a regression where the
real OpenClaw transcript shape drifts away from what the daemon parser
expects — because both sides were authored by us. This test fixes that
gap by invoking the actual installed CLI and pointing the daemon at
whatever it wrote.

Pipeline under test (every layer is REAL except the cloud HTTP POST,
which is mocked because we're not reaching ``ingest.clawmetry.com`` from
unit tests):

    subprocess.run([openclaw, "agent", "--local", "--message", ...])
        → openclaw writes ~/.openclaw/agents/main/sessions/<sid>.jsonl
            → clawmetry.sync.sync_sessions_recent (REAL daemon entry point)
                → _flush_session_batch
                    → _local_ingest_session_batch
                        → DuckDB ``events`` table
                            → /api/local/events     (HTTP)
                            → /api/sessions         (HTTP, fast path)

The OpenClaw subcommand we use is::

    openclaw agent --local --message "<prompt>" --to "+15555550100" \\
        --json --timeout 30

``--local`` runs the embedded agent (no separate gateway daemon needed).
``--to`` is required by the CLI to derive a session key. We deliberately
provide a fake provider API key so the LLM call fails fast (~2s) — what
we care about is the **transcript file**, not the model response. OpenClaw
still writes ``session`` + ``model_change`` + user/assistant ``message``
events to disk before bubbling up the auth error.

Skip behaviour: this test is skipped when ``/opt/homebrew/bin/openclaw``
(or any ``openclaw`` on ``$PATH``) is missing — so CI runners without
OpenClaw skip cleanly with a clear ``reason``.

Run as::

    pytest -v tests/test_real_openclaw_binary_e2e.py
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import time
from unittest.mock import patch

import pytest
from flask import Flask


# ── Locate the binary ──────────────────────────────────────────────────────


def _find_openclaw_binary() -> str | None:
    """Return path to ``openclaw`` if installed, else None.

    Order: explicit env override → Homebrew default → ``$PATH`` lookup.
    """
    env = os.environ.get("OPENCLAW_BIN")
    if env and os.path.exists(env) and os.access(env, os.X_OK):
        return env
    brew = "/opt/homebrew/bin/openclaw"
    if os.path.exists(brew) and os.access(brew, os.X_OK):
        return brew
    return shutil.which("openclaw")


OPENCLAW_BIN = _find_openclaw_binary()

pytestmark = pytest.mark.skipif(
    OPENCLAW_BIN is None,
    reason="openclaw binary not installed (set OPENCLAW_BIN or install via "
           "`npm install -g openclaw`)",
)


# ── Fixture: spawn openclaw, ingest its JSONL into a hermetic DuckDB ───────


SESSION_FILE_GLOB = "*.jsonl"
SESSIONS_SUBPATH = (".openclaw", "agents", "main", "sessions")
NODE_ID = "agent+real-binary-e2e"


def _run_openclaw_agent(home: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Invoke ``openclaw agent --local`` with a hermetic ``OPENCLAW_HOME``.

    The agent will fail at the LLM call (we hand it a deliberately bogus
    OpenAI key) but only after writing the session/model/message events to
    the transcript JSONL — which is the artefact we actually want.
    """
    env = os.environ.copy()
    env["OPENCLAW_HOME"] = home
    # Pin a known-bad key for every provider OpenClaw might try, so the LLM
    # call resolves quickly (auth error in ~2s) instead of hanging on a
    # network timeout. Bogus keys also keep us off real billing.
    env["OPENAI_API_KEY"] = "sk-fake-clawmetry-test-key"
    env["ANTHROPIC_API_KEY"] = "sk-ant-fake-clawmetry-test-key"
    env["GEMINI_API_KEY"] = "fake-clawmetry-test-key"
    # Quiet the CLI's update probe — irrelevant to the test, slow when
    # offline.
    env["OPENCLAW_DISABLE_UPDATE_CHECK"] = "1"
    env["NO_COLOR"] = "1"

    cmd = [
        OPENCLAW_BIN,
        "agent",
        "--local",
        "--message", "echo hello clawmetry",
        "--to", "+15555550100",
        "--json",
        "--timeout", "30",
    ]
    return subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        timeout=timeout,
        text=True,
    )


def _find_session_jsonl(home: str) -> str:
    """Locate the .jsonl OpenClaw just wrote. Skips the trajectory file."""
    sessions_dir = os.path.join(home, *SESSIONS_SUBPATH)
    if not os.path.isdir(sessions_dir):
        raise AssertionError(
            f"openclaw did not create sessions dir at {sessions_dir!r}; "
            f"home contents: {os.listdir(home) if os.path.isdir(home) else '<missing>'}"
        )
    candidates = [
        os.path.join(sessions_dir, f)
        for f in os.listdir(sessions_dir)
        if f.endswith(".jsonl") and ".trajectory" not in f
    ]
    if not candidates:
        raise AssertionError(
            f"no .jsonl files in {sessions_dir!r}; contents: "
            f"{os.listdir(sessions_dir)}"
        )
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def _wait_drained(store, timeout: float = 5.0) -> None:
    """Wait for the local-store flusher thread to drain the in-memory
    ring buffer to DuckDB. The store is async-write by default so an
    immediate read after ingest can race the flusher otherwise."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


@pytest.fixture
def real_openclaw(tmp_path, monkeypatch):
    """Spawn openclaw against a tmp ``OPENCLAW_HOME``, then wire up the
    daemon + Flask app exactly as the real dashboard does at boot.

    Yields a dict with everything the test needs (workspace path, session
    JSONL path, Flask test client, sync module, local_store module).
    """
    home = tmp_path / "openclaw_home"
    home.mkdir()

    # 1) Spawn the real binary. This is the part we cannot fake.
    proc = _run_openclaw_agent(str(home))
    # We DON'T assert returncode==0 — the LLM call is meant to fail with our
    # bogus key. We only need OpenClaw to have written the session JSONL.

    session_path = _find_session_jsonl(str(home))
    # Sanity: file must contain at least one line and the first line must be
    # a parseable JSON object with a 'type' field. If this fails the binary's
    # transcript schema has drifted and the daemon parser would silently
    # drop everything.
    with open(session_path, "r") as fh:
        first = fh.readline().strip()
    assert first, (
        f"openclaw session JSONL is empty: {session_path!r}\n"
        f"stderr (first 1KB): {(proc.stderr or '')[:1024]}"
    )
    first_obj = json.loads(first)
    assert isinstance(first_obj, dict) and first_obj.get("type"), (
        f"first JSONL line missing 'type': {first_obj!r}"
    )

    sessions_dir = os.path.dirname(session_path)

    # 2) Wire up the daemon's local-first stack against this hermetic home.
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", sessions_dir)

    # Reload modules that read env at import time so they see the tmp paths.
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Several routes do `import dashboard as _d; _d.SESSIONS_DIR`. Set it
    # AFTER reloads so they pick the right path up at request time.
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", sessions_dir, raising=False)

    # Touch the writer so the flusher thread is up before the first ingest.
    ls.get_store()

    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    app.register_blueprint(sessions_mod.bp_sessions)

    yield {
        "home":             str(home),
        "sessions_dir":     sessions_dir,
        "session_path":     session_path,
        "session_filename": os.path.basename(session_path),
        "db_path":          str(db_path),
        "ls":               ls,
        "sync":             sync,
        "lq":               lq,
        "client":           app.test_client(),
        "proc":             proc,
        "first_event":      first_obj,
    }

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _drive_real_pipeline(sync_mod, sessions_dir: str, store) -> int:
    """Run the REAL daemon entry point against the OpenClaw-written JSONL."""
    config = {
        "api_key":        "cm_test_real_binary_fake",
        "encryption_key": None,
        "node_id":        NODE_ID,
    }
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": sessions_dir}
    with patch.object(sync_mod, "_post") as mock_post:
        n = sync_mod.sync_sessions_recent(config, state, paths, minutes=60)
    assert mock_post.called, (
        "sync_sessions_recent did not call _post — daemon → cloud wire "
        "broke. Even though we mock it, the call must happen."
    )
    _wait_drained(store)
    return n


# ── 1. The binary actually wrote something we can parse ───────────────────


def test_openclaw_binary_produced_a_session_jsonl(real_openclaw):
    """The most basic guarantee: spawning ``openclaw agent --local`` left
    a non-empty .jsonl on disk whose first line is a JSON object with a
    'type' field. If this fails, the OpenClaw transcript schema drifted
    and every downstream test in this file would also fail — but for less
    obvious reasons."""
    path = real_openclaw["session_path"]
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0
    # First event from `openclaw agent` is always 'session' (transcript bootstrap).
    first = real_openclaw["first_event"]
    assert first.get("type") == "session", (
        f"expected first event type 'session', got {first.get('type')!r}; "
        f"OpenClaw may have changed its transcript bootstrap format"
    )
    # Session id is the canonical correlation key the daemon will use to
    # stamp DuckDB rows.
    assert first.get("id"), "session bootstrap event missing 'id' field"


# ── 2. Daemon ingest of the REAL JSONL into DuckDB ────────────────────────


def test_real_jsonl_flows_through_daemon_into_duckdb(real_openclaw):
    """The end-to-end claim: the same ``sync_sessions_recent`` function the
    OSS daemon calls every cycle picks up the real OpenClaw transcript and
    writes rows into DuckDB. No fabricated JSONL — just the bytes the
    binary wrote.

    Note: ``_list_session_jsonls`` matches *every* ``.jsonl`` file in the
    sessions dir, including OpenClaw's sidecar ``<sid>.trajectory.jsonl``
    (a parallel trace stream). Both files are real OpenClaw output, so we
    count lines across both rather than just the primary transcript.
    """
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    n = _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    # Count timestamped lines across every .jsonl file in the dir — that's
    # what the daemon iterates, so that's what we expect.
    line_count = 0
    for fname in os.listdir(real_openclaw["sessions_dir"]):
        if not fname.endswith(".jsonl"):
            continue
        with open(os.path.join(real_openclaw["sessions_dir"], fname), "r") as fh:
            line_count += sum(1 for ln in fh if ln.strip())

    assert n == line_count, (
        f"sync_sessions_recent processed {n} events, expected {line_count} "
        f"(every non-empty line across all .jsonl files in {real_openclaw['sessions_dir']!r})"
    )

    rows_in_duckdb = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert rows_in_duckdb > 0, "DuckDB events table empty after daemon ingest"
    assert rows_in_duckdb <= n, (
        f"DuckDB has more rows ({rows_in_duckdb}) than the daemon processed "
        f"({n}) — duplicate inserts?"
    )


def test_real_jsonl_session_id_makes_it_into_duckdb(real_openclaw):
    """The session_id the daemon derives from the .jsonl filename must be
    the same UUID OpenClaw burned into the transcript's first 'session'
    event. Otherwise per-session API queries return nothing."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    expected_sid = real_openclaw["session_filename"].split(".jsonl", 1)[0]
    sids = {r[0] for r in store._fetch(
        "SELECT DISTINCT session_id FROM events", []
    )}
    assert expected_sid in sids, (
        f"session_id derivation drifted: expected {expected_sid!r}, "
        f"DuckDB has {sids!r}"
    )


def test_real_jsonl_event_types_populate_columns(real_openclaw):
    """Every row that came from a real OpenClaw line must have a non-empty
    event_type column. A bug here would cause the dashboard's "by type"
    rollups to report everything as 'unknown'."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    rows = store._fetch(
        "SELECT event_type, COUNT(*) FROM events GROUP BY event_type", []
    )
    assert rows, "no rows in events table"
    by_type = {t: c for t, c in rows}
    # 'session' is OpenClaw's bootstrap event (first line of every
    # transcript). If we ingested anything from the real binary we MUST
    # have at least one of these.
    assert by_type.get("session", 0) >= 1, (
        f"expected >=1 'session' event, got types: {by_type!r}"
    )
    # Real OpenClaw also emits at least one 'message' for the user prompt.
    assert by_type.get("message", 0) >= 1, (
        f"expected >=1 'message' event (user prompt), got types: {by_type!r}"
    )
    # No 'unknown' rows — every line had a 'type' field that round-tripped.
    assert by_type.get("unknown", 0) == 0, (
        f"some real JSONL lines were ingested as event_type='unknown' "
        f"({by_type.get('unknown')} rows) — type field lost in pipeline"
    )


def test_real_jsonl_data_blob_round_trips(real_openclaw):
    """The full original event JSON survives in the ``data`` BLOB column.
    Important because the dashboard's tool/payload inspectors fish fields
    out of that blob — a serialisation drop would break them silently."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    rows = store._fetch(
        "SELECT id, event_type, data FROM events WHERE event_type='session' LIMIT 1",
        [],
    )
    assert rows, "no 'session' row in DuckDB to inspect"
    eid, etype, blob = rows[0]
    payload = json.loads(bytes(blob).decode("utf-8"))
    assert payload.get("type") == "session"
    assert payload.get("id") == eid, (
        f"DuckDB id column ({eid!r}) drifted from data.id "
        f"({payload.get('id')!r})"
    )
    assert payload.get("timestamp"), "timestamp lost from data blob"


# ── 3. /api/local/events round-trips the real JSONL ───────────────────────


def test_api_local_events_returns_real_jsonl_rows(real_openclaw):
    """Hit ``/api/local/events`` filtered by the real session_id and assert
    the rows come back. This is exactly the call the dashboard's Brain
    feed makes."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    sid = real_openclaw["session_filename"].split(".jsonl", 1)[0]
    r = real_openclaw["client"].get(
        f"/api/local/events?session_id={sid}&limit=100"
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["_shape"] == "events"
    assert body["count"] >= 1, (
        f"/api/local/events returned 0 rows for real session {sid!r}"
    )
    assert all(row["session_id"] == sid for row in body["rows"]), (
        "API returned rows whose session_id does NOT match the real "
        "OpenClaw session UUID"
    )


# ── 4. /api/sessions fast path lists the real session ─────────────────────


def test_api_sessions_lists_the_real_session(real_openclaw):
    """``/api/sessions`` reads from the ``sessions`` table (not ``events``).
    ``sync_sessions_recent`` only writes to ``events`` — the daemon's
    metadata loop populates ``sessions`` separately. Replay that with
    ``_local_ingest_sessions_batch`` so the fast path has a row."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()
    _drive_real_pipeline(sync_mod, real_openclaw["sessions_dir"], store)

    sid = real_openclaw["session_filename"].split(".jsonl", 1)[0]
    # Pull started/updated timestamps from the real JSONL the binary wrote.
    with open(real_openclaw["session_path"], "r") as fh:
        ts_lines = []
        for ln in fh:
            try:
                obj = json.loads(ln)
                if obj.get("timestamp"):
                    ts_lines.append(obj["timestamp"])
            except Exception:
                continue
    assert ts_lines, "no timestamps in the real JSONL — schema drift?"

    sync_mod._local_ingest_sessions_batch(
        [{
            "session_id":    sid,
            "agent_type":    "openclaw",
            "agent_id":      "main",
            "title":         "Real binary E2E",
            "started_at":    ts_lines[0],
            "updated_at":    ts_lines[-1],
            "status":        "completed",
            "total_tokens":  0,
            "total_cost":    0.0,
            "message_count": 1,
        }],
        node_id=NODE_ID,
    )
    _wait_drained(store)

    r = real_openclaw["client"].get("/api/sessions")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        "Local-store fast path did not engage — check "
        "CLAWMETRY_LOCAL_STORE_READ + populated-sessions-table gate."
    )
    sids = {s["session_id"] for s in body["sessions"]}
    assert sid in sids, (
        f"/api/sessions did not surface the real session {sid!r}; "
        f"returned: {sids!r}"
    )


# ── 5. Re-running the daemon over the same JSONL is idempotent ────────────


def test_real_jsonl_idempotent_re_ingest(real_openclaw):
    """The daemon polls every 15s; a second pass over the same on-disk
    transcript must NOT duplicate rows. Tests INSERT OR IGNORE on event id
    AND the last_event_ids cursor advancement against real OpenClaw IDs
    (which use OpenClaw's own short-hash format, not our test UUIDs)."""
    sync_mod = real_openclaw["sync"]
    store = real_openclaw["ls"].get_store()

    config = {
        "api_key": "cm_test", "encryption_key": None, "node_id": NODE_ID,
    }
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": real_openclaw["sessions_dir"]}

    with patch.object(sync_mod, "_post"):
        sync_mod.sync_sessions_recent(config, state, paths, minutes=60)
        sync_mod.sync_sessions_recent(config, state, paths, minutes=60)
        sync_mod.sync_sessions_recent(config, state, paths, minutes=60)
    _wait_drained(store)

    sid = real_openclaw["session_filename"].split(".jsonl", 1)[0]
    # Total rows after 3 passes — must equal rows after 1 pass.
    total_rows = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    # Compute a fresh single-pass baseline by truncating + reingesting.
    store._fetch("DELETE FROM events", [])
    state2 = {"last_event_ids": {}}
    with patch.object(sync_mod, "_post"):
        sync_mod.sync_sessions_recent(config, state2, paths, minutes=60)
    _wait_drained(store)
    one_pass_rows = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert total_rows == one_pass_rows, (
        f"re-running daemon ingest leaked rows: 3-pass DuckDB total = "
        f"{total_rows}, single-pass baseline = {one_pass_rows}"
    )
    # Sanity: the session we care about has rows under its real UUID.
    sid_rows = store._fetch(
        "SELECT COUNT(*) FROM events WHERE session_id = ?", [sid]
    )[0][0]
    assert sid_rows >= 1, (
        f"session_id={sid!r} has no rows after re-ingest"
    )
