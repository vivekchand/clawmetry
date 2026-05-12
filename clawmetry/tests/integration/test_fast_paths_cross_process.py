"""Cross-process fast-path integration test for issue #1088.

PROBLEM
=======
DuckDB at ``~/.clawmetry/clawmetry.duckdb`` is single-writer. Under the
standard install (``pip install clawmetry`` + launchd / systemd) the sync
daemon runs as one process and the dashboard as another. The dashboard's
direct ``local_store.get_store()`` open hits ``IOException: Could not set
lock`` and silently falls through to the slow JSONL parsing path —
making every ``_try_local_store_*`` fast-path *dead code* in production.

This test BOOTS THE TWO PROCESSES SEPARATELY and asserts that the five
migrated fast-paths fire (``_source == "local_store"``), proving the
daemon HTTP proxy (``routes/local_query.local_store_via_daemon``) closes
the gap.

LAYOUT
======
* ``daemon`` subprocess: opens DuckDB read-write (taking the writer lock),
  starts the ``local_server`` HTTP endpoint, writes the discovery file,
  ingests a few events, then sleeps until the parent kills it.
* ``dashboard`` (this test process): boots the Flask app from
  ``dashboard.py`` against the same isolated workspace, hits the five
  endpoints over HTTP via Werkzeug's test client, asserts each response
  carries ``_source: "local_store"`` (or in the heatmap case, that the
  daemon-proxied counts are non-zero).

The dashboard's direct DuckDB open WILL fail (the daemon holds the lock).
The fast-paths only succeed because they go through the daemon HTTP
proxy. Removing ``local_store_via_daemon`` from ``routes/local_query.py``
would make this whole test fail.

The test is marked ``@pytest.mark.integration`` and skipped when duckdb
isn't installed, so the unit-test suite stays fast.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid

import pytest


pytestmark = pytest.mark.integration


def _has_duckdb() -> bool:
    try:
        import duckdb  # noqa: F401
        return True
    except ImportError:
        return False


def _wait_for_discovery(disc_path: str, timeout_s: float = 10.0) -> dict:
    """Poll for the discovery file (port + token + pid) the daemon writes
    on boot. Returns the parsed dict. Raises TimeoutError after ``timeout_s``."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if os.path.exists(disc_path):
            try:
                with open(disc_path) as fh:
                    data = json.load(fh)
                if data.get("port") and data.get("token") and data.get("pid"):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        time.sleep(0.1)
    raise TimeoutError(f"discovery file not ready: {disc_path}")


def _wait_for_port(port: int, timeout_s: float = 5.0) -> None:
    """Poll the port until something accepts a TCP connection. The daemon's
    HTTP server takes a beat to bind after the discovery file lands."""
    deadline = time.monotonic() + timeout_s
    last_err = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError as e:
            last_err = e
            time.sleep(0.1)
    raise TimeoutError(f"port {port} never accepted: {last_err}")


# Daemon subprocess: opens the DuckDB read-write (so it holds the writer
# lock that would block any other process), starts local_server, and seeds
# the store with a handful of events + a typed-sessions row + an aggregate
# row so each of the five migrated fast-paths has data to return.
_DAEMON_SCRIPT = textwrap.dedent("""
    import json, os, sys, time, uuid

    # Force the local store + discovery file under the test workspace.
    home = os.environ["CLAWMETRY_TEST_HOME"]
    os.environ["HOME"] = home
    os.environ.setdefault("CLAWMETRY_LOCAL_STORE_PATH", os.path.join(home, "events.duckdb"))
    # Tight flusher interval so seeded rows are visible to the dashboard
    # within the test's wait budget (default is multiple seconds).
    os.environ.setdefault("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")

    # Repo root on sys.path so 'routes' + 'clawmetry' import.
    sys.path.insert(0, os.environ["CLAWMETRY_REPO_ROOT"])

    from clawmetry import local_store, local_server

    # Override discovery path so we never touch the user's real ~/.clawmetry.
    discovery_path = os.path.join(home, "local_query.json")
    local_server.DISCOVERY_PATH = type(local_server.DISCOVERY_PATH)(discovery_path)

    store = local_store.get_store(read_only=False)  # takes the writer lock

    # Seed events.
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")
    for i in range(5):
        store.ingest({
            "id": f"e{i}-{uuid.uuid4()}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-cross-proc-1",
            "event_type": "tool_call",
            "ts": now_iso,
            "data": {"tool": "fs.read", "input": "/etc/hosts"},
            "cost_usd": 0.001,
            "token_count": 42,
            "model": "claude-sonnet-4-test",
        })

    # Seed a row in the typed sessions table so query_sessions_table returns
    # something for /api/overview + /api/sessions fast-paths.
    store._fetch(
        "INSERT INTO sessions (agent_type, session_id, agent_id, title, "
        "started_at, last_active_at, status, total_tokens, cost_usd, "
        "message_count, metadata, updated_at) VALUES "
        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ["openclaw", "sess-cross-proc-1", "main", "test session",
         now_iso, now_iso, "active", 42, 0.001, 1,
         json.dumps({"model": "claude-sonnet-4-test"}).encode("utf-8"),
         int(time.time() * 1000)],
    )
    # Seed daily aggregate so /api/usage fast-path returns data.
    today = time.strftime("%Y-%m-%d")
    store._fetch(
        "INSERT INTO daily_aggregates (agent_type, agent_id, workspace_id, "
        "day, cost_usd, token_count, event_count) VALUES "
        "(?, ?, ?, ?, ?, ?, ?)",
        ["openclaw", "main", "default", today, 0.001, 42, 5],
    )

    # Force the flusher to drain so the seeded events are visible to other
    # processes via SELECT (DuckDB's WAL is per-connection — buffered writes
    # only become visible to readers after a commit).
    try:
        store._flush_now()
    except Exception:
        pass
    time.sleep(0.3)

    port = local_server.start()

    # Drop a marker file so the parent knows seeding finished. The discovery
    # file alone isn't enough — local_server writes it during start() before
    # we've necessarily run all the seeding above.
    with open(os.path.join(home, "ready.marker"), "w") as fh:
        fh.write(str(port))

    # Sleep until the parent SIGTERMs us. SIGINT (KeyboardInterrupt) makes
    # for a clean atexit flush.
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
""")


@pytest.fixture
def cross_process_daemon():
    """Spawn the daemon subprocess and yield the discovery dict. Tears
    down the subprocess + isolated workspace on exit."""
    if not _has_duckdb():
        pytest.skip("duckdb not installed")

    workspace = tempfile.mkdtemp(prefix=f"clawmetry-test-{uuid.uuid4().hex[:8]}-")
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    # Snapshot any env vars the test mutates so we can restore them on
    # teardown — avoids cross-test contamination (e.g. a leftover HOME=tmp
    # path that was deleted by the previous fixture run).
    saved_env = {
        k: os.environ.get(k)
        for k in ("HOME", "CLAWMETRY_LOCAL_STORE_READ",
                  "CLAWMETRY_LOCAL_STORE_PATH", "CLAWMETRY_LOCAL_FLUSH_SECS")
    }
    env = {
        **os.environ,
        "CLAWMETRY_TEST_HOME": workspace,
        "CLAWMETRY_REPO_ROOT": repo_root,
        # Make sure the daemon doesn't think it's in cloud mode etc.
        "CLAWMETRY_LOCAL_STORE_READ": "1",
    }
    proc = subprocess.Popen(
        [sys.executable, "-c", _DAEMON_SCRIPT],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        # Wait for both: discovery file (server bound) AND ready marker
        # (events seeded). Either alone leaves a race window.
        ready_marker = os.path.join(workspace, "ready.marker")
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            if os.path.exists(ready_marker) and os.path.exists(
                os.path.join(workspace, "local_query.json")
            ):
                break
            if proc.poll() is not None:
                _, err = proc.communicate(timeout=2)
                pytest.fail(
                    f"daemon exited prematurely (rc={proc.returncode}): "
                    f"{err.decode('utf-8', 'replace')[:2000]}"
                )
            time.sleep(0.1)
        else:
            pytest.fail("daemon never reported ready within 15s")

        disc = _wait_for_discovery(os.path.join(workspace, "local_query.json"))
        _wait_for_port(disc["port"])
        yield {"workspace": workspace, "discovery": disc}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
        shutil.rmtree(workspace, ignore_errors=True)
        # Restore env vars so the next test (or the rest of the suite)
        # doesn't see a HOME pointing at our deleted tmp dir.
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_fast_paths_fire_under_cross_process_daemon(cross_process_daemon):
    """All five migrated fast-paths must serve from the local store via the
    daemon HTTP proxy when daemon + dashboard run in separate processes."""
    workspace = cross_process_daemon["workspace"]
    discovery = cross_process_daemon["discovery"]

    # Point the dashboard at the same isolated workspace + discovery file.
    # Reload the local_query module so its cached discovery + paths pick up
    # the new env. Critical: this test process must NOT open the DuckDB
    # itself — the daemon holds the writer lock and our open would raise
    # IOException. The whole point of the test is to prove the proxy
    # gets us there without ever touching the file directly.
    os.environ["HOME"] = workspace
    os.environ["CLAWMETRY_LOCAL_STORE_READ"] = "1"
    os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = os.path.join(workspace, "events.duckdb")

    import importlib
    import routes.local_query as lq
    importlib.reload(lq)
    lq._DISCOVERY_PATH = os.path.join(workspace, "local_query.json")
    lq._invalidate_daemon_cache()

    # Sanity: prove the proxy itself works (lower-level than the routes).
    rows = lq.local_store_via_daemon("query_events", limit=10)
    assert rows is not None and len(rows) >= 5, (
        f"daemon proxy returned {rows!r} — expected the seeded events"
    )

    # Build a minimal Flask "dashboard" with just the blueprints we need —
    # boots in milliseconds, no need to call dashboard.main() which would
    # start an HTTP server. The fast-paths use late `import dashboard as _d`
    # for shared helpers (sessions dir, gateway invokers, etc.); since the
    # daemon's seeded data is enough to satisfy the fast-path branches and
    # the legacy fallbacks return harmless defaults on a fresh
    # workspace, we don't need a real dashboard backend wired in.
    import dashboard  # noqa: F401  — populates module-level helpers
    from flask import Flask
    import routes.sessions as sessions_mod
    import routes.brain as brain_mod
    import routes.usage as usage_mod
    import routes.health as health_mod
    import routes.overview as overview_mod
    importlib.reload(sessions_mod)
    importlib.reload(brain_mod)
    importlib.reload(usage_mod)
    importlib.reload(health_mod)
    importlib.reload(overview_mod)

    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    app.register_blueprint(brain_mod.bp_brain)
    app.register_blueprint(usage_mod.bp_usage)
    app.register_blueprint(health_mod.bp_health)
    app.register_blueprint(overview_mod.bp_overview)
    client = app.test_client()

    # 1. /api/sessions  → routes/sessions.py:_try_local_store_sessions
    r = client.get("/api/sessions")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/sessions did NOT use local_store: {body!r}"
    )

    # 2. /api/brain-history → routes/brain.py:_try_local_store_brain
    r = client.get("/api/brain-history?limit=20")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/brain-history did NOT use local_store: {body!r}"
    )

    # 3. /api/usage  → routes/usage.py:_try_local_store_usage
    r = client.get("/api/usage")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/usage did NOT use local_store: {body!r}"
    )

    # 4. /api/heatmap  → routes/health.py:_try_local_store_heatmap
    r = client.get("/api/heatmap?days=1")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/heatmap did NOT use local_store: {body!r}"
    )
    assert body.get("max", 0) > 0, "heatmap should reflect seeded events"

    # 5. /api/overview  → routes/overview.py:_try_local_store_overview
    r = client.get("/api/overview")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"/api/overview did NOT use local_store: {body!r}"
    )
    assert body.get("sessionCount", 0) >= 1, "overview should see the seeded session"


def test_dashboard_falls_back_when_daemon_dies(cross_process_daemon):
    """When the daemon process is killed mid-flight, the next dashboard
    request must NOT 500 — it should silently fall through to the legacy
    JSONL/gateway path. This is the safety property that lets us ship the
    proxy without risking dashboard outages."""
    import importlib
    import routes.local_query as lq
    importlib.reload(lq)

    # Point at a stale discovery file referencing a definitely-dead PID.
    # Same shape as the daemon writes, but the PID is bogus, so
    # _read_discovery's liveness check should drop it.
    workspace = cross_process_daemon["workspace"]
    fake_disc = os.path.join(workspace, "fake.json")
    with open(fake_disc, "w") as fh:
        json.dump({"port": 65000, "token": "x" * 32, "pid": 999999}, fh)
    lq._DISCOVERY_PATH = fake_disc
    lq._invalidate_daemon_cache()

    started = time.monotonic()
    result = lq.local_store_via_daemon("query_events", limit=5)
    elapsed = time.monotonic() - started
    assert result is None, (
        f"expected None when daemon is dead (so caller falls through), got {result!r}"
    )
    assert elapsed < 1.0, (
        f"fallback took {elapsed:.2f}s — the dead-PID liveness check should "
        "make this near-instant"
    )
