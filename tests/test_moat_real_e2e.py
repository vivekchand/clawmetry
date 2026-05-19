"""MOAT 2026-05-19 — real OpenClaw E2E across the full dashboard surface.

User mandate (verbatim, EOD 2026-05-19):

    "Send a real message through OpenClaw locally, then verify the ENTIRE
     chain landed in DuckDB AND every relevant API endpoint returns
     correct data. This is the MOAT."

Sibling files:
  - ``tests/test_moat_live_openclaw_e2e.py`` — same harness pattern, 5
    endpoints (sessions / transcript / session-tools / usage / brain-history
    / flow / local-transcript). Existed before this file; left untouched.
  - ``tests/test_moat_send_message_e2e.py`` — synthetic events. Memory
    ``feedback_synthetic_tests_missed_real_event_shape.md`` documents the
    three MOAT migrations that shipped green-synthetic E2E but flunked on
    real v3 data — this file's reason for existing.

What this file adds beyond the sibling:
  - ``/api/overview``    — main dashboard aggregator (model + active session)
  - ``/api/channels``    — Flow diagram channel list
  - ``/api/crons``       — cron job inventory (must 200 even with no jobs)
  - ``/api/system-health`` — disk/mem/uptime/channels (must 200 always)

Pipeline (everything real except the cloud POST, mocked):

    openclaw gateway (subprocess, hermetic OPENCLAW_HOME)
      + openclaw agent --local --message …       -> <sid>.jsonl
        -> clawmetry.sync.sync_sessions_recent   -> DuckDB events table
          -> /api/overview /api/channels /api/crons /api/system-health
             /api/sessions /api/transcript /api/usage /api/brain-history
             /api/flow

DuckDB hard rule (memory ``reference_duckdb_process_lock.md``): the
dashboard reads via the daemon's HTTP proxy in prod. In this hermetic
harness no daemon is running; the local_store singleton is owned by
this test process, so a direct ``store._fetch`` is the correct in-test
equivalent of the daemon proxy. (PR-#1559 sibling does the same — see
``test_data_blob_round_trips_byte_identical`` there.)

Run: ``make test-moat-real`` or
``python3 -m pytest tests/test_moat_real_e2e.py -v``
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest
from flask import Flask


# ── openclaw binary discovery (matches sibling test) ──────────────────────


def _find_openclaw_binary() -> str | None:
    env = os.environ.get("OPENCLAW_BIN")
    if env and os.path.exists(env) and os.access(env, os.X_OK):
        return env
    brew = "/opt/homebrew/bin/openclaw"
    if os.path.exists(brew) and os.access(brew, os.X_OK):
        return brew
    return shutil.which("openclaw")


OPENCLAW_BIN = _find_openclaw_binary()


# Real LLM credentials required: the canonical ``<sid>.jsonl`` only flushes
# after the model call returns. Fake key -> 401 -> no file -> fixture asserts
# explode. GitHub Actions does not expose repo secrets to PRs from forks,
# so external-contributor PRs cannot satisfy this. Skip the whole module
# with a clear reason so contributor CI stays green.
REQUIRED_LLM_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY")
_FAKE_LLM_KEY_MARKERS = ("fake-clawmetry", "sk-ant-fake", "sk-fake")


def _have_real_llm_key() -> bool:
    """True iff env has a non-empty, non-fake LLM key on any accepted alias."""
    for name in REQUIRED_LLM_ENV:
        v = os.environ.get(name, "")
        if v and not any(m in v for m in _FAKE_LLM_KEY_MARKERS):
            return True
    return False


pytestmark = [
    pytest.mark.skipif(
        OPENCLAW_BIN is None,
        reason=(
            "openclaw binary not on PATH; install via `brew install openclaw` "
            "or `npm install -g openclaw`. CI: use .github/actions/setup-openclaw."
        ),
    ),
    pytest.mark.skipif(
        not _have_real_llm_key(),
        reason=(
            "Real MOAT E2E needs a real LLM key (ANTHROPIC_API_KEY, "
            "ANTHROPIC_AUTH_TOKEN, or CLAUDE_API_KEY). GitHub Actions does not "
            "expose repo secrets to PRs from forks, so this is expected on "
            "contributor PRs. It runs on push to main and on PRs from the main "
            "repo where the secret is available. Set ANTHROPIC_API_KEY locally "
            "to run it during development."
        ),
    ),
]


# ── Constants ─────────────────────────────────────────────────────────────


NODE_ID = "agent+moat-real-e2e-2026-05-19"
# Two candidate session-dir layouts — see sibling test for the trace of
# why both must be probed (OpenClaw v3 honours STATE_DIR differently
# between binary versions).
SESSIONS_SUBPATH_FLAT = ("agents", "main", "sessions")
SESSIONS_SUBPATH_NESTED = (".openclaw", "agents", "main", "sessions")
MESSAGE_BODY = "MOAT real E2E ping 2026-05-19 closes #1791"
RECIPIENT = "+15555550199"
GATEWAY_BOOT_TIMEOUT_SECS = 30
TEST_OVERALL_BUDGET_SECS = 120


# ── Subprocess helpers (port-pickers, gateway/agent boot) ─────────────────


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_gateway(home: str, port: int, token: str) -> subprocess.Popen:
    env = {
        **os.environ,
        "OPENCLAW_HOME": home,
        "OPENCLAW_GATEWAY_TOKEN": token,
        "NO_COLOR": "1",
        "OPENCLAW_DISABLE_UPDATE_CHECK": "1",
    }
    log_path = os.path.join(home, "gateway.log")
    log_fh = open(log_path, "w")  # noqa: SIM115
    proc = subprocess.Popen(
        [
            OPENCLAW_BIN, "gateway",
            "--port", str(port),
            "--auth", "token", "--token", token,
            "--allow-unconfigured", "--bind", "loopback", "--verbose",
        ],
        env=env, stdout=log_fh, stderr=subprocess.STDOUT, cwd=home,
    )
    proc._cm_log_path = log_path  # type: ignore[attr-defined]
    return proc


def _wait_for_gateway(port: int, token: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    last = "no attempts"
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/models",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=2) as r:
                if 200 <= r.status < 500:
                    return
        except urllib.error.HTTPError as e:
            if e.code in (200, 401, 403):
                return
            last = f"HTTP {e.code}"
        except Exception as e:
            last = repr(e)
        time.sleep(0.5)
    raise AssertionError(
        f"openclaw gateway never responded on 127.0.0.1:{port} within "
        f"{timeout}s (last={last})"
    )


def _stop_gateway(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass
    except Exception:
        pass


def _send_message(home: str, message: str) -> subprocess.CompletedProcess:
    """Drive ``openclaw agent --local`` — hermetic to ``home``.

    Mirrors the sibling test's ``_send_message`` (kept duplicated, not
    factored, so the two MOAT harnesses can evolve independently
    without one breaking the other through a shared helper rev)."""
    state_dir = os.path.join(home, "state")
    os.makedirs(state_dir, exist_ok=True)
    env = {**os.environ}
    for k, fake in (
        ("OPENAI_API_KEY", "sk-fake-clawmetry-moat-real-e2e"),
        ("ANTHROPIC_API_KEY", "sk-ant-fake-clawmetry-moat-real-e2e"),
        ("GEMINI_API_KEY", "fake-clawmetry-moat-real-e2e"),
    ):
        env.setdefault(k, fake)
    env["OPENCLAW_HOME"] = home
    env["OPENCLAW_STATE_DIR"] = state_dir
    env["OPENCLAW_DISABLE_UPDATE_CHECK"] = "1"
    env["NO_COLOR"] = "1"
    return subprocess.run(
        [
            OPENCLAW_BIN, "agent", "--local",
            "--message", message, "--to", RECIPIENT,
            "--model", "anthropic/claude-opus-4-7",
            "--json", "--timeout", "30",
        ],
        env=env, capture_output=True, text=True, timeout=60,
    )


def _find_session_jsonl(
    home: str, proc: subprocess.CompletedProcess | None = None
) -> str:
    candidate_dirs = [
        os.path.join(home, "state", *SESSIONS_SUBPATH_FLAT),
        os.path.join(home, *SESSIONS_SUBPATH_NESTED),
        os.path.join(home, *SESSIONS_SUBPATH_FLAT),
    ]
    for sd in candidate_dirs:
        if not os.path.isdir(sd):
            continue
        candidates = [
            os.path.join(sd, f) for f in os.listdir(sd)
            if (
                f.endswith(".jsonl")
                and not f.endswith(".trajectory.jsonl")
                and ".trajectory" not in f
            )
        ]
        if candidates:
            candidates.sort(key=os.path.getmtime, reverse=True)
            return candidates[0]
    tree = []
    for root, _, files in os.walk(home):
        rel = os.path.relpath(root, home)
        for f in files:
            tree.append(os.path.join(rel, f) if rel != "." else f)
        if len(tree) > 30:
            tree.append("... (truncated)")
            break
    rc = getattr(proc, "returncode", "<no proc>")
    stderr_tail = (proc.stderr or "")[-1024:] if proc is not None else ""
    stdout_tail = (proc.stdout or "")[-1024:] if proc is not None else ""
    raise AssertionError(
        "openclaw did not write a canonical <sid>.jsonl under any known "
        f"sessions dir.\n  probed: {candidate_dirs}\n  tree: {tree}\n"
        f"  agent rc: {rc}\n  stderr (1K): {stderr_tail}\n"
        f"  stdout (1K): {stdout_tail}"
    )


def _wait_drained(store, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain ring (depth={store.health()['ring_depth']})"
    )


# ── Fixture ───────────────────────────────────────────────────────────────


@pytest.fixture
def live(tmp_path, monkeypatch):
    """Real gateway + real ``openclaw agent --local`` send + daemon ingest
    + DuckDB + every endpoint the user mandate calls out."""
    overall_start = time.monotonic()

    # 1) Gateway
    home = tmp_path / "openclaw_home"
    home.mkdir()
    port = _free_port()
    token = "moat-real-e2e-token-2026-05-19"
    gateway_proc = _start_gateway(str(home), port, token)
    try:
        _wait_for_gateway(port, token, timeout=GATEWAY_BOOT_TIMEOUT_SECS)
    except Exception:
        log_path = getattr(gateway_proc, "_cm_log_path", None)
        tail = ""
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path) as fh:
                    tail = fh.read()[-4096:]
            except Exception:
                tail = "<could not read gateway.log>"
        _stop_gateway(gateway_proc)
        raise AssertionError(
            "openclaw gateway boot failed; log tail:\n" + tail
        )

    # 2) Send-message
    proc = _send_message(str(home), MESSAGE_BODY)
    session_path = _find_session_jsonl(str(home), proc=proc)
    with open(session_path) as fh:
        first_line = fh.readline().strip()
    assert first_line, (
        f"openclaw session JSONL empty: {session_path!r}\n"
        f"agent rc: {proc.returncode}\n"
        f"stderr (1K): {(proc.stderr or '')[:1024]}\n"
        f"stdout (1K): {(proc.stdout or '')[:1024]}"
    )
    first_obj = json.loads(first_line)
    assert isinstance(first_obj, dict) and first_obj.get("type"), (
        f"first JSONL line not typed: {first_obj!r}"
    )
    sessions_dir = os.path.dirname(session_path)
    session_id = os.path.basename(session_path).rsplit(".jsonl", 1)[0]

    # 3) Daemon + Flask
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", sessions_dir)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.local_query as lq
    importlib.reload(lq)
    # Endpoint blueprints we will exercise.
    import routes.sessions as sessions_blueprint
    importlib.reload(sessions_blueprint)
    import routes.brain as brain_blueprint
    importlib.reload(brain_blueprint)
    import routes.usage as usage_blueprint
    importlib.reload(usage_blueprint)
    import routes.infra as infra_blueprint
    importlib.reload(infra_blueprint)
    import routes.overview as overview_blueprint
    importlib.reload(overview_blueprint)
    import routes.health as health_blueprint
    importlib.reload(health_blueprint)
    import routes.crons as crons_blueprint
    importlib.reload(crons_blueprint)

    # Force daemon discovery to a dead path so any host daemon doesn't
    # intercept the in-process local_store calls.
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH",
        str(tmp_path / "no-such-discovery.json"), raising=True,
    )
    lq._invalidate_daemon_cache()

    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", sessions_dir, raising=False)

    ls.get_store()  # warm flusher

    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    app.register_blueprint(sessions_blueprint.bp_sessions)
    app.register_blueprint(brain_blueprint.bp_brain)
    app.register_blueprint(usage_blueprint.bp_usage)
    app.register_blueprint(infra_blueprint.bp_logs)
    app.register_blueprint(overview_blueprint.bp_overview)
    app.register_blueprint(health_blueprint.bp_health)
    app.register_blueprint(crons_blueprint.bp_crons)

    yield {
        "home":          str(home),
        "sessions_dir":  sessions_dir,
        "session_path":  session_path,
        "session_id":    session_id,
        "ls":            ls,
        "sync":          sync_mod,
        "lq":            lq,
        "client":        app.test_client(),
        "first_event":   first_obj,
        "agent_proc":    proc,
    }

    _stop_gateway(gateway_proc)
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass

    elapsed = time.monotonic() - overall_start
    if elapsed > TEST_OVERALL_BUDGET_SECS:
        print(
            f"\n[moat-real-e2e] WARNING: fixture wall-clock {elapsed:.1f}s "
            f"exceeded {TEST_OVERALL_BUDGET_SECS}s budget"
        )


# ── Drive helpers (shared across tests) ───────────────────────────────────


def _drive_daemon(sync_mod, sessions_dir: str, store) -> int:
    config = {
        "api_key": "cm_test_moat_real",
        "encryption_key": None,
        "node_id": NODE_ID,
    }
    state = {"last_event_ids": {}}
    paths = {"sessions_dir": sessions_dir}
    with patch.object(sync_mod, "_post") as mock_post:
        n = sync_mod.sync_sessions_recent(config, state, paths, minutes=60)
    assert mock_post.called, "sync did not call _post (cloud wire broken)"
    _wait_drained(store)
    return n


def _seed_sessions_table(env_) -> None:
    """``sync_sessions_recent`` only writes the events table; the
    sessions-table fast-paths (/api/sessions, /api/overview) need
    metadata rows. Replicate what the daemon's metadata loop does."""
    sync_mod = env_["sync"]
    store = env_["ls"].get_store()
    total_tokens = 0
    for line in open(env_["session_path"]):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        usage = (obj.get("message") or {}).get("usage") or {}
        total_tokens += int(usage.get("totalTokens", 0) or 0)
    started = env_["first_event"].get("timestamp") or "2026-01-01T00:00:00Z"
    sync_mod._local_ingest_sessions_batch(
        [{
            "session_id":    env_["session_id"],
            "agent_type":    "openclaw",
            "agent_id":      "main",
            "title":         "MOAT real E2E session",
            "started_at":    started,
            "updated_at":    started,
            "status":        "active",
            "total_tokens":  total_tokens,
            "total_cost":    0.0,
            "message_count": 1,
        }],
        node_id=NODE_ID,
    )
    _wait_drained(store)


# ── Tests: every endpoint listed in the user mandate ──────────────────────


def test_real_message_writes_canonical_event_types_to_duckdb(live):
    """Sanity: ingest of the real OpenClaw <sid>.jsonl writes the v3
    namespaced types we assert against in downstream API tests below."""
    sync_mod = live["sync"]
    store = live["ls"].get_store()
    n = _drive_daemon(sync_mod, live["sessions_dir"], store)
    assert n >= 1, (
        f"sync ingested 0 events; agent stderr (1K): "
        f"{(live['agent_proc'].stderr or '')[:1024]}"
    )
    by_type = dict(store._fetch(
        "SELECT event_type, COUNT(*) FROM events GROUP BY event_type", []
    ))
    assert by_type.get("session.started", 0) >= 1, (
        f"missing session.started bootstrap row; types={by_type!r}"
    )
    turn_rows = (
        by_type.get("prompt.submitted", 0) + by_type.get("model.completed", 0)
    )
    assert turn_rows >= 1, (
        f"missing prompt.submitted / model.completed turn row; "
        f"types={by_type!r}"
    )


def test_api_overview_reflects_new_session(live):
    """/api/overview is the dashboard's main aggregator — must surface the
    new session via the local-store fast path (no gateway in this test)."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    _seed_sessions_table(live)

    r = live["client"].get("/api/overview")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert isinstance(body, dict), f"/api/overview non-dict: {body!r}"
    # The fast path tags itself; absence => silent fallback to gateway
    # (which would 500 in this hermetic test).
    assert body.get("_source") == "local_store", (
        f"/api/overview did not use local-store fast path; "
        f"_source={body.get('_source')!r}"
    )
    # Required shape keys (any one missing = JS dashboard crashes).
    for k in ("activeSessions", "cronCount", "cronEnabled", "cronDisabled"):
        assert k in body, f"/api/overview missing {k!r}; keys={sorted(body)}"


def test_api_channels_returns_known_list(live):
    """/api/channels powers the Flow diagram. Must 200 + return a list
    (empty list is legitimate for a fresh hermetic install)."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    r = live["client"].get("/api/channels")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert isinstance(body, dict), f"/api/channels non-dict: {body!r}"
    assert "channels" in body, f"/api/channels missing 'channels': {sorted(body)}"
    assert isinstance(body["channels"], list), (
        f"/api/channels: 'channels' not a list — {type(body['channels'])}"
    )


def test_api_crons_returns_jobs_list(live):
    """/api/crons must always 200 and return ``jobs`` (empty list when no
    gateway/file-backed crons). Hermetic install has none."""
    r = live["client"].get("/api/crons")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert isinstance(body, dict), f"/api/crons non-dict: {body!r}"
    assert "jobs" in body, f"/api/crons missing 'jobs': {sorted(body)}"
    assert isinstance(body["jobs"], list), (
        f"/api/crons: 'jobs' not list — {type(body['jobs'])}"
    )


def test_api_system_health_returns_sections(live):
    """/api/system-health must always 200 with at least one documented
    section (channels / system / crons / disk / memory)."""
    r = live["client"].get("/api/system-health")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert isinstance(body, dict), f"/api/system-health non-dict: {body!r}"
    documented = {
        "channels", "channel_ingest", "system", "crons", "disk", "memory",
        "daemon",
    }
    assert set(body) & documented, (
        f"/api/system-health missing all documented sections; "
        f"keys={sorted(body)}"
    )


def test_api_sessions_lists_new_session(live):
    """Required-by-mandate: /api/sessions must include the new sid."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    _seed_sessions_table(live)
    r = live["client"].get("/api/sessions")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/sessions _source={body.get('_source')!r}"
    )
    sids = {s.get("session_id") for s in (body.get("sessions") or [])}
    assert live["session_id"] in sids, (
        f"/api/sessions missing {live['session_id']!r}; got {sorted(sids)[:5]}"
    )


def test_api_transcript_contains_prompt_text(live):
    """Required-by-mandate: /api/transcript/<id> must contain the sent text."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    r = live["client"].get(f"/api/transcript/{live['session_id']}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    rendered = json.dumps(body.get("messages") or [])
    assert MESSAGE_BODY in rendered, (
        f"sent text {MESSAGE_BODY!r} missing from /api/transcript"
    )


def test_api_usage_buckets_today(live):
    """Required-by-mandate: /api/usage must come from local_store."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    _seed_sessions_table(live)
    r = live["client"].get("/api/usage")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/usage _source={body.get('_source')!r}"
    )
    assert "days" in body, f"/api/usage missing 'days': {sorted(body)}"


def test_api_brain_history_contains_turn_event(live):
    """Required-by-mandate: /api/brain-history must surface a turn event."""
    _drive_daemon(live["sync"], live["sessions_dir"], live["ls"].get_store())
    r = live["client"].get("/api/brain-history?limit=100")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/brain-history _source={body.get('_source')!r}"
    )
    types = {(ev.get("type") or "").upper() for ev in (body.get("events") or [])}
    expected_any = {"MESSAGE", "PROMPT.SUBMITTED", "MODEL.COMPLETED"}
    assert types & expected_any, (
        f"no turn event in /api/brain-history (expected any of "
        f"{sorted(expected_any)}); got {sorted(types)}"
    )


def test_api_flow_returns_envelope(live):
    """Required-by-mandate: /api/flow returns the streaming envelope."""
    r = live["client"].get("/api/flow")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("ok") is True, f"/api/flow envelope: {body!r}"
    assert body.get("type") == "flow-events"


def test_user_prompt_text_persists_in_duckdb_blob(live):
    """Stricter assertion than the transcript test: the raw bytes must be
    readable from a DuckDB row. v3 stores user text under
    ``finalPromptText`` (top-level + nested ``data.finalPromptText``)."""
    sync_mod = live["sync"]
    store = live["ls"].get_store()
    _drive_daemon(sync_mod, live["sessions_dir"], store)
    rows = store._fetch(
        "SELECT data FROM events WHERE event_type IN "
        "('prompt.submitted','model.completed') AND data IS NOT NULL", []
    )
    found = False
    for (blob,) in rows:
        try:
            payload = json.loads(bytes(blob).decode("utf-8"))
        except Exception:
            continue
        for fpt in (
            payload.get("finalPromptText"),
            (payload.get("data") or {}).get("finalPromptText")
            if isinstance(payload.get("data"), dict) else None,
        ):
            if isinstance(fpt, str) and MESSAGE_BODY in fpt:
                found = True
                break
        if found:
            break
        content = (payload.get("message") or {}).get("content")
        if isinstance(content, str) and MESSAGE_BODY in content:
            found = True
            break
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and MESSAGE_BODY in str(c.get("text", "")):
                    found = True
                    break
            if found:
                break
    assert found, (
        f"sent message {MESSAGE_BODY!r} not found in any DuckDB "
        "prompt.submitted/model.completed row — pipeline lossy."
    )
