"""TRUE end-to-end pipeline test — REAL OpenClaw turn (no synthetic seed).

Proves the full daemon pipeline end to end, driven by a REAL OpenClaw turn
(not hand-written JSONL):

    openclaw agent --local  (real turn → real <sid>.jsonl on disk)
        → sync.sync_sessions_recent  (the REAL daemon entry point that walks
                                      the workspace, reads files, parses lines,
                                      batches them)
            → sync._flush_session_batch
                → sync._local_ingest_session_batch
                    → clawmetry.local_store DuckDB
                        → /api/local/events            (HTTP)
                        → /api/sessions                (HTTP, fast path)
                        → /api/brain-history           (HTTP, fast path)
                        → /api/transcript/<sid>        (HTTP, JSONL path)

What changed (2026-05-31): this file used to WRITE 11 synthetic events to a
JSONL and assert exact counts/costs/tool-args. A synthetic seed can't catch a
break in OpenClaw's own transcript format or in the file→daemon parse path —
the whole point of an e2e. It now runs a real turn and asserts RELATIONAL
invariants that hold for ANY real turn (a real LLM turn is non-deterministic,
so exact counts/costs are not assertable; that math is covered by unit tests
like tests/test_event_metrics_extraction.py):

  * the turn writes a canonical <sid>.jsonl that the daemon ingests (n > 0);
  * every layer (DuckDB / query_events / relay / HTTP) agrees on the SAME
    event count — the cross-layer MOAT guarantee, whatever the count is;
  * all events share ONE session_id (no id drift across the pipeline);
  * re-running the daemon is idempotent (no duplicate rows);
  * the session surfaces through every dashboard API a browser hits;
  * any tool_call events round-trip their tool name + args dict.

Model selection (no raw API key needed locally): if ANTHROPIC_API_KEY is set
(CI) the turn uses anthropic/claude-3-5-haiku-20241022; else if the `claude`
CLI is logged in (dev box) it uses claude-cli/<model> via the subscription
($0 metered); else the module skips. Either path writes the same canonical
JSONL the daemon ingests.

Run as:
    pytest -v tests/test_e2e_real_openclaw_pipeline.py
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


NODE_ID = "agent+e2e-real-test"
RECIPIENT = "+15555550100"
# A prompt that nudges a tool call so the tool-args round-trip assertion has
# something to chew on when the model cooperates. The pipeline assertions do
# not depend on a tool actually running (a real turn is non-deterministic).
TURN_MESSAGE = (
    "Run the bash command `echo hello-clawmetry` using your tools, then reply "
    "with the word done."
)

_OPENCLAW_BIN = shutil.which("openclaw")


def _pick_model():
    """Cheapest real-turn model that will actually authenticate here.

    CI sets ANTHROPIC_API_KEY (the embedded anthropic provider). A dev box
    usually has no key but a logged-in `claude` CLI — OpenClaw's claude-cli
    provider drives it via the Claude subscription (no key, $0 metered)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic/claude-3-5-haiku-20241022"
    if shutil.which("claude"):
        return "claude-cli/sonnet"
    return None


_MODEL = _pick_model()

pytestmark = pytest.mark.skipif(
    not (_OPENCLAW_BIN and _MODEL),
    reason=(
        "needs the openclaw binary AND a usable model: set ANTHROPIC_API_KEY "
        "(CI) or log in the `claude` CLI (dev). Skipping rather than faking."
    ),
)

# Canonical session location written by `openclaw agent --local` with an
# OPENCLAW_STATE_DIR override (flat: <state>/agents/main/sessions/<sid>.jsonl).
SESSIONS_SUBPATH = ("agents", "main", "sessions")


def _run_real_turn(home: str) -> str:
    """Run ONE real OpenClaw turn into a hermetic home; return the sessions dir.

    Mirrors the production invocation tests/test_moat_live_openclaw_e2e.py
    uses. The anthropic/ (or claude-cli/) prefix is what drives OpenClaw v3
    harness selection. We honour a real ANTHROPIC_API_KEY when present; on a
    dev box the claude-cli provider needs no key (uses the logged-in CLI)."""
    state_dir = os.path.join(home, "state")
    sessions_dir = os.path.join(state_dir, *SESSIONS_SUBPATH)
    os.makedirs(state_dir, exist_ok=True)
    env = {**os.environ}
    env["OPENCLAW_HOME"] = home
    env["OPENCLAW_STATE_DIR"] = state_dir
    env["OPENCLAW_DISABLE_UPDATE_CHECK"] = "1"
    env["NO_COLOR"] = "1"
    proc = subprocess.run(
        [
            _OPENCLAW_BIN, "agent", "--local",
            "--message", TURN_MESSAGE, "--to", RECIPIENT,
            "--model", _MODEL,
            "--json", "--timeout", "60",
        ],
        env=env, capture_output=True, text=True, timeout=150,
    )
    # rc may be non-zero on a tool/policy hiccup; what matters is that the
    # canonical <sid>.jsonl was written (that is what the daemon ingests).
    if not os.path.isdir(sessions_dir):
        pytest.skip(
            f"openclaw turn wrote no sessions dir (rc={proc.returncode}); "
            f"stderr tail: {proc.stderr[-400:]!r}"
        )
    return sessions_dir


def _canonical_session(sessions_dir: str) -> tuple[str, int]:
    """Return (session_id, raw_line_count) for the canonical <sid>.jsonl the
    turn wrote, skipping the .trajectory.jsonl sidecar."""
    cands = [
        f for f in os.listdir(sessions_dir)
        if f.endswith(".jsonl") and not f.endswith(".trajectory.jsonl")
    ]
    if not cands:
        pytest.skip(
            f"no canonical <sid>.jsonl in {sessions_dir} "
            f"(only sidecars: {os.listdir(sessions_dir)}) — the turn did not "
            f"complete a model call; check auth/quota."
        )
    sid = cands[0][: -len(".jsonl")]
    path = os.path.join(sessions_dir, cands[0])
    n_lines = sum(1 for ln in open(path) if ln.strip())
    return sid, n_lines


def _wait_drained(store, timeout=4.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


@pytest.fixture(scope="module")
def real_turn(tmp_path_factory):
    """Run the real turn ONCE for the whole module (one billed/subscription
    turn feeds every assertion — cost discipline)."""
    home = str(tmp_path_factory.mktemp("openclaw_home"))
    sessions_dir = _run_real_turn(home)
    sid, n_lines = _canonical_session(sessions_dir)
    return {"home": home, "sessions_dir": sessions_dir,
            "session_id": sid, "n_lines": n_lines}


@pytest.fixture
def pipeline(real_turn, tmp_path, monkeypatch):
    """Wire the real turn's workspace into a hermetic DuckDB store + Flask app
    with sessions/brain/local_query blueprints."""
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("OPENCLAW_HOME", real_turn["home"])
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", real_turn["sessions_dir"])

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic store: a real ClawMetry daemon on the dev box would otherwise
    # make get_store() return a proxy to the daemon's DuckDB. Force the
    # in-process direct store on BOTH the write side (_daemon_registered) and
    # the read side (lq._read_discovery → None makes _proxy_dispatch fall
    # through to direct-open). No-op in CI (no daemon).
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.brain as brain_mod
    importlib.reload(brain_mod)

    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", real_turn["sessions_dir"], raising=False)

    ls.get_store()  # bring the flusher up before the first ingest

    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    app.register_blueprint(sessions_mod.bp_sessions)
    app.register_blueprint(brain_mod.bp_brain)

    yield {
        "session_id":   real_turn["session_id"],
        "sessions_dir": real_turn["sessions_dir"],
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


def _drive_real_pipeline(sync, sessions_dir, store):
    """Run the REAL daemon ingest function over the real turn's workspace.
    Cloud HTTP is mocked so we don't hit ingest.clawmetry.com; every other
    layer runs. Returns the number of events the daemon processed."""
    config = {"api_key": "cm_test_e2e_fake", "encryption_key": None,
              "node_id": NODE_ID}
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": str(sessions_dir)}
    with patch.object(sync, "_post") as mock_post:
        n = sync.sync_sessions_recent(config, state, paths, minutes=60)
    assert mock_post.called, (
        "sync_sessions_recent did not call _post — daemon-to-cloud wire broke."
    )
    _wait_drained(store)
    return n


# ── 1. Daemon ingest: a real turn's JSONL lands in DuckDB ──────────────────


def test_real_turn_ingests_into_duckdb(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    n = _drive_real_pipeline(sync, pipeline["sessions_dir"], store)
    assert n > 0, "daemon processed 0 events from the real turn's JSONL"
    on_disk = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert on_disk == n, (
        f"daemon reported {n} processed but DuckDB holds {on_disk} — "
        f"ingest dropped rows between parse and write."
    )
    assert on_disk > 0


def test_single_session_id_no_drift(pipeline):
    """Every ingested event must carry the ONE real session_id. A real turn
    has exactly one session; id drift in the parse path is a real bug class."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)
    sids = {r[0] for r in store._fetch("SELECT DISTINCT session_id FROM events", [])}
    assert sids == {pipeline["session_id"]}, (
        f"session_id drift: DuckDB has {sids}, expected "
        f"{{{pipeline['session_id']!r}}} (the real turn's session)."
    )


def test_message_event_present(pipeline):
    """Any real turn produces at least one message row (the user prompt and,
    on success, the assistant reply). This is the floor an e2e must clear."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)
    rows = store._fetch(
        "SELECT event_type, COUNT(*) FROM events GROUP BY event_type", []
    )
    by_type = {t: c for t, c in rows}
    msg_like = sum(
        c for t, c in by_type.items()
        if t and ("message" in t.lower() or "prompt" in t.lower()
                  or "completed" in t.lower())
    )
    assert msg_like >= 1, (
        f"no message/prompt-like event ingested from the real turn; "
        f"event types seen: {sorted(by_type)}"
    )


# ── 2. Tool-call payload survival (conditional — tools may not run) ────────


def test_tool_calls_round_trip_when_present(pipeline):
    """IF the turn issued tool calls, each must keep its tool name + args dict
    through the JSONL → daemon → DuckDB round-trip. Skips (does not fail) when
    the model chose not to call a tool — a real turn is non-deterministic."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)
    rows = store._fetch(
        "SELECT id, data FROM events WHERE event_type = 'tool_call'", []
    )
    if not rows:
        pytest.skip("the real turn issued no tool_call events this run")
    for eid, blob in rows:
        payload = json.loads(bytes(blob).decode("utf-8"))
        assert payload.get("tool"), f"tool_call {eid} lost its tool name"
        assert isinstance(payload.get("args"), (dict, type(None))), (
            f"tool_call {eid} args wrong type: {type(payload.get('args'))}"
        )


# ── 3. Cross-layer agreement: the MOAT guarantee ──────────────────────────


def test_all_layers_report_same_event_count(pipeline):
    """DuckDB / query_events / relay / HTTP must agree on the SAME count —
    whatever it is. If any reader drifts from the daemon's writer the
    dashboard shows wrong numbers. (Exact count is non-deterministic across
    real turns, so we assert agreement, not a magic number.)"""
    sync = pipeline["sync"]
    lq = pipeline["lq"]
    client = pipeline["client"]
    store = pipeline["ls"].get_store()
    sid = pipeline["session_id"]

    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)

    layer1_duckdb = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    layer2_query = len(store.query_events(session_id=sid, limit=10000))
    layer3_relay = lq.relay_dispatch(
        "events", {"session_id": sid, "limit": 10000}
    )["count"]
    layer4_http = client.get(
        f"/api/local/events?session_id={sid}&limit=10000"
    ).get_json()["count"]

    assert layer1_duckdb == layer2_query == layer3_relay == layer4_http > 0, (
        f"layer counts disagree: duckdb={layer1_duckdb} "
        f"query_events={layer2_query} relay={layer3_relay} "
        f"http_get={layer4_http}"
    )


# ── 4. HTTP surfaces a browser hits ────────────────────────────────────────


def test_api_local_events_returns_session(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)
    r = pipeline["client"].get(
        f"/api/local/events?session_id={pipeline['session_id']}&limit=5000"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["_shape"] == "events"
    assert body["count"] > 0
    assert all(row["session_id"] == pipeline["session_id"] for row in body["rows"])


def test_api_sessions_lists_the_session(pipeline):
    """``/api/sessions`` reads the ``sessions`` table (not events).
    ``sync_sessions_recent`` only writes events, so we replay the daemon's
    metadata loop with ``_local_ingest_sessions_batch`` for the real sid."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)

    sid = pipeline["session_id"]
    sync._local_ingest_sessions_batch(
        [{
            "session_id":    sid,
            "agent_type":    "openclaw",
            "agent_id":      "main",
            "title":         "Real-turn E2E session",
            "status":        "completed",
            "message_count": 1,
        }],
        node_id=NODE_ID,
    )

    r = pipeline["client"].get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        "local-store fast path did not engage — check CLAWMETRY_LOCAL_STORE_READ."
    )
    assert sid in {s["session_id"] for s in body["sessions"]}


def test_api_brain_history_returns_events(pipeline):
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)

    r = pipeline["client"].get("/api/brain-history?limit=50")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("_shape") == "brain_history"
    assert body["count"] > 0


def test_api_transcript_returns_messages_from_jsonl(pipeline):
    """``/api/transcript/<sid>`` reads the .jsonl directly (not the store).
    A real turn must yield at least one message (the user prompt)."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    _drive_real_pipeline(sync, pipeline["sessions_dir"], store)

    r = pipeline["client"].get(f"/api/transcript/{pipeline['session_id']}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert "messages" in body
    assert len(body["messages"]) > 0, (
        "transcript endpoint returned no messages — JSONL parser regression?"
    )


# ── 5. Idempotency: re-running the daemon must not duplicate rows ──────────


def test_re_running_sync_is_idempotent(pipeline):
    """The daemon polls every ~15s; a second pass over the same workspace
    must not duplicate rows (INSERT OR IGNORE on id + cursor advancement)."""
    sync = pipeline["sync"]
    store = pipeline["ls"].get_store()
    config = {"api_key": "cm_test", "encryption_key": None, "node_id": NODE_ID}
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": str(pipeline["sessions_dir"])}
    with patch.object(sync, "_post"):
        n1 = sync.sync_sessions_recent(config, state, paths, minutes=60)
        sync.sync_sessions_recent(config, state, paths, minutes=60)
        sync.sync_sessions_recent(config, state, paths, minutes=60)
    _wait_drained(store)
    count = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
    assert count == n1 > 0, (
        f"re-running daemon ingest changed the row count: first pass {n1}, "
        f"DuckDB now {count} — idempotency (INSERT OR IGNORE / cursor) broke."
    )
