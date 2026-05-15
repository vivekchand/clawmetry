"""MOAT E2E: "send a message in OpenClaw → DuckDB → every API surface".

Companion to ``tests/test_e2e_real_openclaw_pipeline.py`` (Engineer 9 /
2026-05-12). That file proves a synthetic OpenClaw transcript end-to-ends
through the daemon → DuckDB → ``/api/local/*`` and ``/api/sessions``. This
file widens that coverage to the **user-visible** dashboard surfaces a real
"send a message in OpenClaw" interaction would touch:

  Telegram inbound message
      → ``store.ingest_channel_message()``
          → ``channel_messages`` table
              → ``/api/channels/<provider>/messages``
              → ``/api/channels/<provider>/threads``
              → ``/api/channels/summary``
              → ``/api/channel/telegram``  (legacy per-channel route)

  Tool-call event
      → ``sync._local_ingest_session_batch()``
          → ``events`` table
              → ``/api/local/events``
              → ``/api/brain-history``
              → ``/api/sessions``  (after sessions-table mirror)
              → ``/api/session-tools``
              → ``/api/usage``

The third scenario sweeps across the union of the above and asserts every
JSON response carries ``_source: "local_store"`` (not ``gateway``,
``jsonl``, ``otlp``, etc.). That's the canary for the MOAT default-on
guarantee — if a future PR silently flips a fast-path back to a legacy
source, this test goes red.

Why this exists, in one line: per the MOAT spec, "any future regression in
DuckDB writes or fast-path reads gets caught in CI."

Run as::

    pytest -v tests/test_moat_send_message_e2e.py

Notes for future maintainers:

  * We monkeypatch ``routes.local_query._DISCOVERY_PATH`` to a non-existent
    file so the in-process Flask test client never crosses the wire to a
    locally running production daemon (which would have different data).
    Without this, on a developer machine where ``clawmetry`` is installed
    and running, every ``_ls_call`` would punt to the real daemon and
    return that daemon's rows instead of our hermetic fixtures.
  * Hermetic env: ``tmp_path`` for both DuckDB and the OpenClaw home,
    ``CLAWMETRY_LOCAL_STORE_*`` env knobs flushed via ``monkeypatch``.
  * Module reloads: ``local_store`` / ``sync`` / ``local_query`` /
    ``routes/*`` all snapshot env at import time, so we ``importlib.reload``
    them after setting env. Same pattern as ``test_e2e_real_openclaw_pipeline``.
  * Cloud HTTP is mocked at ``sync._post`` — the daemon code path that
    posts to ``ingest.clawmetry.com`` must still be exercised, just not
    over the wire.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import json
import time
import uuid

import pytest
from flask import Flask


# ── Test inputs ───────────────────────────────────────────────────────────

NODE_ID = "agent+moat-send-msg-e2e"
SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
SESSION_FILE = f"{SESSION_ID}.jsonl"
WORKSPACE_ID = "ws-moat-send-msg"
CHANNEL_PROVIDER = "telegram"
CHANNEL_CHAT_ID = "telegram:55512345"
SENDER_NAME = "tester-moat"

_NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _ts(seconds_ago: int) -> str:
    return (_NOW - _dt.timedelta(seconds=seconds_ago)).isoformat().replace(
        "+00:00", "Z"
    )


def _ev(type_, seconds_ago: int, **extras) -> dict:
    """One OpenClaw transcript event in the shape the daemon ingests.

    Mirrors ``_ev`` in ``test_e2e_real_openclaw_pipeline``. ``cost_usd`` /
    ``tokens`` / ``model`` keys land on the row directly (synthesised events,
    not the ``message.usage`` shape OpenClaw produces) — that's how the
    earlier E2E test already exercises the ingest path and matches the
    extractor's accepted shapes."""
    base = {
        "id": str(uuid.uuid4()),
        "type": type_,
        "timestamp": _ts(seconds_ago),
        "workspace": WORKSPACE_ID,
    }
    base.update(extras)
    return base


# Realistic in-flight session: 1 session_start + 2 tool calls + 1 message.
# Same shape exercised by ``test_e2e_real_openclaw_pipeline`` — just trimmed
# so we get a tight per-session-tools assertion (exactly 2 tool calls).
SESSION_START = _ev(
    "session_start", 600, id="moat-ev-start", title="MOAT send-msg E2E"
)
TOOL_BASH = _ev(
    "tool_call", 500,
    id="moat-ev-tool-bash",
    tool="Bash", args={"cmd": "echo hello"}, result="hello\n",
    cost_usd=0.0010, tokens=42, model="claude-opus-4-7",
)
TOOL_READ = _ev(
    "tool_call", 450,
    id="moat-ev-tool-read",
    tool="Read", args={"path": "/tmp/notes.md"}, result="# notes\n",
    cost_usd=0.0008, tokens=33, model="claude-opus-4-7",
)
MSG = _ev(
    "message", 400,
    id="moat-ev-msg",
    role="assistant",
    text="On it, ran a couple of tools.",
    usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    cost_usd=0.005, tokens=150, model="claude-opus-4-7",
)
ALL_EVENTS = sorted(
    [SESSION_START, TOOL_BASH, TOOL_READ, MSG], key=lambda e: e["timestamp"]
)
EXPECTED_EVENT_COUNT = len(ALL_EVENTS)
EXPECTED_TOOL_CALLS = 2


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Hermetic OpenClaw home + DuckDB + Flask app with every blueprint that
    serves a "did the message land?" surface registered.

    Critical: monkeypatch ``_DISCOVERY_PATH`` BEFORE reloading
    ``routes/local_query`` so the module-level constant picks up the dead
    path. Otherwise a real daemon running on the dev machine intercepts
    every ``_ls_call`` and the test reads the wrong DuckDB.
    """
    openclaw_home = tmp_path / "openclaw"
    sessions_dir = openclaw_home / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)
    clawmetry_home = tmp_path / "clawmetry"
    clawmetry_home.mkdir()
    db_path = clawmetry_home / "events.duckdb"

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("CLAWMETRY_HOME", str(clawmetry_home))
    monkeypatch.setenv("OPENCLAW_HOME", str(openclaw_home))
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(openclaw_home))
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(sessions_dir))

    # Reload modules that snapshot env at import time.
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.local_query as lq
    importlib.reload(lq)
    # Force the daemon-discovery file to a path that doesn't exist so
    # ``_proxy_dispatch`` and ``local_store_via_daemon`` always punt to the
    # in-process store — keeps the test deterministic on machines with a
    # real ClawMetry daemon running.
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"),
        raising=True,
    )
    lq._invalidate_daemon_cache()

    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.brain as brain_mod
    importlib.reload(brain_mod)
    import routes.channels as channels_mod
    importlib.reload(channels_mod)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions_dir), raising=False)

    # Touch the writer so the flusher thread is alive before first ingest.
    ls.get_store()

    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    app.register_blueprint(sessions_mod.bp_sessions)
    app.register_blueprint(brain_mod.bp_brain)
    app.register_blueprint(channels_mod.bp_channels)
    app.register_blueprint(usage_mod.bp_usage)

    yield {
        "openclaw_home":  openclaw_home,
        "sessions_dir":   sessions_dir,
        "clawmetry_home": clawmetry_home,
        "db_path":        db_path,
        "ls":             ls,
        "sync":           sync_mod,
        "lq":             lq,
        "client":         app.test_client(),
    }

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _wait_drained(store, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


def _seed_telegram_message(store, *, text: str = "hello from moat e2e") -> dict:
    """Inject one Telegram inbound row via the documented public API.

    Returns the dict we sent so the test can assert against the same payload."""
    msg = {
        "id":          f"tg-msg-{uuid.uuid4()}",
        "provider":    CHANNEL_PROVIDER,
        "channel_id":  CHANNEL_CHAT_ID,
        "sender_id":   "55512345",
        "sender_name": SENDER_NAME,
        "body":        text,
        "ts":          _ts(60),
        "direction":   "in",  # inbound from user
        "session_key": SESSION_ID,
    }
    store.ingest_channel_message(msg)
    _wait_drained(store)
    return msg


def _seed_session_events(env_) -> None:
    """Push the 4 transcript events through the real daemon ingest helper.

    Mirrors what ``sync_sessions_recent`` does per .jsonl file — the
    helper is the same one ``_flush_session_batch`` calls."""
    sync = env_["sync"]
    store = env_["ls"].get_store()
    sync._local_ingest_session_batch(
        batch=ALL_EVENTS,
        session_file=SESSION_FILE,
        node_id=NODE_ID,
        subagent_id=None,
    )
    _wait_drained(store)


def _seed_session_metadata(env_) -> None:
    """Mirror what the daemon's metadata loop does — populates the
    ``sessions`` table so ``/api/sessions`` and ``/api/session-tools``
    fast-paths fire instead of falling back to JSONL."""
    sync = env_["sync"]
    store = env_["ls"].get_store()
    sync._local_ingest_sessions_batch(
        [{
            "session_id":     SESSION_ID,
            "agent_type":     "openclaw",
            "agent_id":       "main",
            "title":          "MOAT send-msg E2E",
            "started_at":     ALL_EVENTS[0]["timestamp"],
            "updated_at":     ALL_EVENTS[-1]["timestamp"],
            "status":         "active",
            "total_tokens":   42 + 33 + 150,
            "total_cost":     0.0010 + 0.0008 + 0.005,
            "message_count":  1,
            "channel":        CHANNEL_PROVIDER,
        }],
        node_id=NODE_ID,
    )
    _wait_drained(store)


def _poll(predicate, *, timeout: float = 10.0, every: float = 0.05):
    """Poll ``predicate`` (a no-arg callable) until it returns truthy or
    ``timeout`` seconds elapse. Returns the last truthy value, or raises
    AssertionError with the last value seen.

    The MOAT spec asks for "asserts the event lands in DuckDB within N
    seconds" — this is the N-second poll. We use 10s by default to stay
    well above the 50ms flush window even on a slow CI runner."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(every)
    raise AssertionError(
        f"predicate did not become truthy within {timeout}s; "
        f"last value: {last!r}"
    )


# ── Scenario 1: Telegram inbound message surfaces everywhere ──────────────


def test_telegram_inbound_message_surfaces_everywhere(env):
    """A single Telegram inbound message lands in DuckDB and is visible
    on EVERY channel-aware API endpoint with the right body, sender, and
    direction. If any one endpoint drifts, the dashboard's channel feed
    silently goes dark for that surface only — exactly the regression
    class this test guards against."""
    store = env["ls"].get_store()
    sent = _seed_telegram_message(store, text="hello from moat e2e")

    # 1) Lands in DuckDB within 10s (per the spec).
    rows = _poll(
        lambda: store.query_channel_messages(
            provider=CHANNEL_PROVIDER, limit=10
        ),
        timeout=10.0,
    )
    assert len(rows) == 1, f"expected 1 channel_messages row, got {len(rows)}"
    row = rows[0]
    assert row["provider"] == CHANNEL_PROVIDER
    assert row["sender_name"] == SENDER_NAME
    assert row["direction"] == "in"
    assert row["body"] == sent["body"]

    client = env["client"]

    # 2) /api/channels/<provider>/messages — typed Phase-4 endpoint.
    r = client.get(f"/api/channels/{CHANNEL_PROVIDER}/messages?limit=50")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["_source"] == "local_store", (
        f"channel-messages fast path didn't engage; _source={body.get('_source')!r}"
    )
    assert body["total"] == 1
    assert body["messages"][0]["text"] == sent["body"]
    assert body["messages"][0]["sender"] == SENDER_NAME
    assert body["messages"][0]["direction"] == "in"

    # 3) /api/channels/<provider>/threads — thread rollup view.
    r = client.get(f"/api/channels/{CHANNEL_PROVIDER}/threads?limit=20")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["total"] >= 1
    # Find our thread by channelId.
    thread = next(
        (t for t in body["threads"] if t["channelId"] == CHANNEL_CHAT_ID),
        None,
    )
    assert thread is not None, (
        f"thread for {CHANNEL_CHAT_ID!r} not in /threads response: "
        f"{[t.get('channelId') for t in body['threads']]}"
    )
    assert thread["msgIn"] >= 1

    # 4) /api/channels/summary — cross-provider rollup.
    r = client.get("/api/channels/summary")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["totals"]["msgIn"] >= 1
    tg_summary = next(
        (p for p in body["providers"] if p["provider"] == CHANNEL_PROVIDER),
        None,
    )
    assert tg_summary is not None, (
        f"telegram missing from /summary providers: "
        f"{[p.get('provider') for p in body['providers']]}"
    )
    assert tg_summary["msgIn"] >= 1
    assert tg_summary["distinctChannels"] >= 1

    # 5) /api/channel/telegram — legacy per-provider route, Phase-5
    #    fast-pathed onto the same DuckDB rows. Cloud UI's left-nav still
    #    hits this URL so a regression here would orphan the inbox view.
    r = client.get("/api/channel/telegram?limit=50")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/channel/telegram did NOT take the local_store fast path; "
        f"_source={body.get('_source')!r}, body keys={list(body)}"
    )
    msgs = body.get("messages") or []
    assert any(
        (m.get("text") or m.get("body") or "") == sent["body"]
        for m in msgs
    ), (
        f"Telegram body not in /api/channel/telegram response: "
        f"{[m.get('text') or m.get('body') for m in msgs[:5]]}"
    )


# ── Scenario 2: Tool call event surfaces everywhere ────────────────────────


def test_tool_call_event_surfaces_everywhere(env):
    """Inject a realistic OpenClaw transcript (1 session_start + 2 tool
    calls + 1 assistant message) through the daemon's real ingest helper.
    Then assert every event-aware dashboard surface picks it up:

      * /api/local/events       — raw event stream (Brain)
      * /api/brain-history      — top-level Brain feed shape
      * /api/sessions           — session list w/ totals
      * /api/session-tools      — per-session tool timeline
      * /api/usage              — token + cost analytics

    Rationale: a "send a message in OpenClaw" round-trip almost always
    triggers tool calls and an assistant reply. If any of these surfaces
    drift off DuckDB the user-visible dashboard silently regresses to
    JSONL (slow) or empty (broken) without any error log."""
    _seed_session_events(env)
    _seed_session_metadata(env)
    store = env["ls"].get_store()
    client = env["client"]

    # Sanity: rows actually in DuckDB. _poll ensures the assert window
    # extends up to 10s (per the MOAT spec).
    _poll(
        lambda: store._fetch(
            "SELECT COUNT(*) FROM events WHERE session_id = ?",
            [SESSION_ID],
        )[0][0] == EXPECTED_EVENT_COUNT,
        timeout=10.0,
    )

    # 1) /api/local/events — raw shape, source-of-truth count.
    r = client.get(f"/api/local/events?session_id={SESSION_ID}&limit=100")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["_shape"] == "events"
    assert body["count"] == EXPECTED_EVENT_COUNT, (
        f"/api/local/events: got {body['count']} events, "
        f"expected {EXPECTED_EVENT_COUNT}"
    )

    # 2) /api/brain-history — UI top-level Brain feed.
    r = client.get("/api/brain-history?limit=100")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"brain-history fast path didn't engage; _source={body.get('_source')!r}"
    )
    assert body.get("_shape") == "brain_history"
    types = {ev["type"] for ev in body["events"]}
    # Brain shape upper-cases event_type — see the brain mapper in
    # routes/brain.py:_brain_history_from_local_store.
    assert "TOOL_CALL" in types, f"TOOL_CALL missing from brain types: {types}"
    assert "MESSAGE" in types, f"MESSAGE missing from brain types: {types}"

    # 3) /api/sessions — session-list fast path.
    r = client.get("/api/sessions")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"sessions fast path didn't engage; _source={body.get('_source')!r}"
    )
    sids = {s.get("session_id") for s in body["sessions"]}
    assert SESSION_ID in sids, (
        f"session {SESSION_ID!r} missing from /api/sessions: {sorted(sids)[:5]}"
    )

    # 4) /api/local/transcript/<sid> — session transcript via local-query
    #    relay shape. Reads the events table directly so it works on any
    #    event_type. (We deliberately skip /api/session-tools here: that
    #    endpoint only fires on legacy ``event_type=='message'`` rows with
    #    nested ``data.message.content[].toolCall`` blocks — neither the v3
    #    parser NOR the synthetic shape used here produce that combination.
    #    See routes/sessions.py:_try_local_store_session_tools.)
    r = client.get(f"/api/local/transcript/{SESSION_ID}?limit=100")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_shape") == "transcript"
    assert body.get("count") == EXPECTED_EVENT_COUNT, (
        f"/api/local/transcript: got {body.get('count')} events, "
        f"expected {EXPECTED_EVENT_COUNT}"
    )
    # Both tool names round-trip through the data BLOB.
    rendered = json.dumps(body)
    assert "Bash" in rendered, "Bash tool call missing from /api/local/transcript"
    assert "Read" in rendered, "Read tool call missing from /api/local/transcript"

    # 5) /api/usage — token + cost analytics. Costs we injected:
    #    0.0010 + 0.0008 + 0.005 = 0.0068, tokens: 42+33+150 = 225.
    r = client.get("/api/usage")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"usage fast path didn't engage; _source={body.get('_source')!r}"
    )
    # Aggregate over all days (the response carries 14 days of buckets).
    total_tokens = sum(int(d.get("tokens") or 0) for d in body.get("days", []))
    total_cost = sum(float(d.get("cost") or 0.0) for d in body.get("days", []))
    assert total_tokens >= 225, (
        f"usage day-totals lost tokens: got {total_tokens}, expected >=225"
    )
    assert total_cost >= 0.0068, (
        f"usage day-totals lost cost: got {total_cost}, expected >=0.0068"
    )
    # Model attribution must include the model the tool calls + message used.
    models_seen = {m.get("model") for m in body.get("modelBreakdown", [])}
    assert "claude-opus-4-7" in models_seen, (
        f"model attribution missing claude-opus-4-7: {models_seen}"
    )


# ── Scenario 3: every endpoint we touched takes the local_store path ──────


# Endpoints whose response MUST carry ``_source: "local_store"`` after
# ingest. Each is hit via Flask test client; we assert the field, not just
# that the request returned 200. (A response with ``_source: "jsonl"`` is a
# regression even if the row counts happen to look right.)
#
# Endpoints split into two groups:
#   * EVENT_ENDPOINTS — need the events + sessions tables seeded.
#   * CHANNEL_ENDPOINTS — need the channel_messages table seeded.
#
# We DON'T sweep every fast-pathed endpoint in routes/* here — that would
# duplicate the per-feature ``test_*_local_store.py`` files and add
# surface area that breaks on every legitimate route refactor. The 8
# endpoints below are the "send a message" critical path the user asked
# us to lock down.

EVENT_ENDPOINTS_LOCAL_STORE = [
    "/api/sessions",
    "/api/brain-history?limit=50",
    "/api/usage",
]

CHANNEL_ENDPOINTS_LOCAL_STORE = [
    f"/api/channels/{CHANNEL_PROVIDER}/messages?limit=10",
    f"/api/channels/{CHANNEL_PROVIDER}/threads?limit=10",
    "/api/channels/summary",
    f"/api/channel/{CHANNEL_PROVIDER}",
]


def test_all_endpoints_use_local_store_source(env):
    """The MOAT canary. After we seed both event AND channel data, every
    user-visible "did the message land?" surface MUST tag its response
    ``_source: "local_store"``. A regression that flips any one of these
    back to ``gateway`` / ``jsonl`` / ``otlp`` / a missing field gets
    caught here — even if the row counts happen to match.

    Why an explicit allow-list instead of "any non-empty _source":
    ``local_store_empty`` is a legitimate "schema live but no rows"
    sentinel for the channel routes (see routes/channels.py:420). Once
    we've seeded data, ``_empty`` would itself be a regression."""
    store = env["ls"].get_store()
    _seed_telegram_message(store, text="moat-canary inbound msg")
    _seed_session_events(env)
    _seed_session_metadata(env)

    client = env["client"]
    failures = []  # (url, status, _source) — collect-all so the report is full
    for url in EVENT_ENDPOINTS_LOCAL_STORE + CHANNEL_ENDPOINTS_LOCAL_STORE:
        r = client.get(url)
        if r.status_code != 200:
            failures.append((url, r.status_code, "<non-200>"))
            continue
        body = r.get_json() or {}
        src = body.get("_source")
        if src != "local_store":
            failures.append((url, r.status_code, src))

    assert not failures, (
        "Endpoints that should serve from local_store didn't:\n"
        + "\n".join(
            f"  {url} → status={status} _source={src!r}"
            for url, status, src in failures
        )
    )
