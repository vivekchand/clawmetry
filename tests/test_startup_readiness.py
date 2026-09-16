"""First-install preparation uses durable data and never traps the browser.

AC-OBS-FRP-001.1: progress and automatic handoff
AC-OBS-FRP-001.2: restart and upgrade bypass
AC-OBS-FRP-001.3: empty-store guidance
AC-OBS-FRP-001.4: bounded fallback and working retry
AC-OBS-FRP-001.5: visibility and in-flight deduplication
AC-OBS-FRP-001.6: shared cloud snapshot, no cloud-host reads
"""
import ast
from pathlib import Path
import shutil
import subprocess

from flask import Flask, render_template_string
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    from clawmetry import local_store
    # Pass an isolated DB path BEFORE constructing any store. No singleton,
    # no daemon discovery and no touch of the developer's real history.
    monkeypatch.setattr(local_store, "DB_PATH", tmp_path / "startup.duckdb")
    monkeypatch.setattr(local_store, "_migrate_legacy_db_path", lambda: None)
    monkeypatch.setattr(local_store, "_maybe_compact_on_startup", lambda: None)
    instance = local_store.LocalStore()
    yield instance
    instance.stop(flush=False)


def test_first_sync_waits_until_complete_and_survives_restart(store):
    from clawmetry.startup import record_progress
    assert store.query_startup_status()["initialized"] is False
    record_progress(store, "discovering")
    record_progress(store, "runtime_history", 2, 4)
    assert store.query_startup_status()["initialized"] is False
    record_progress(store, "complete", complete=True)
    assert store.query_startup_status()["initialized"] is True
    record_progress(store, "discovering")
    status = store.query_startup_status()
    assert status["initialized"] is True
    assert status["has_data"] is False  # empty is a finished setup, not a spinner


def test_existing_sessions_do_not_get_gated_after_an_upgrade(store):
    from clawmetry.startup import record_progress
    store._conn.execute("INSERT INTO sessions (agent_type, session_id, updated_at) VALUES ('codex', 'existing', 1)")
    record_progress(store, "discovering")
    status = store.query_startup_status()
    assert status["has_data"] is True
    assert status["initialized"] is True


def test_agent_activity_during_setup_does_not_finish_the_import(store):
    from clawmetry.startup import record_progress
    record_progress(store, "discovering")
    store._conn.execute("INSERT INTO sessions (agent_type, session_id, updated_at) VALUES ('openclaw', 'arriving', 1)")
    assert store.query_startup_status()["has_data"] is True
    assert store.query_startup_status()["initialized"] is False


def test_daemon_diagnostics_are_not_agent_activity(store):
    store.ingest({"id": "diagnostic", "agent_type": "daemon", "node_id": "test",
                  "event_type": "daemon_error", "ts": "2026-09-16T10:00:00Z"})
    store.flush()
    assert store.query_startup_status()["has_data"] is False


def test_malformed_progress_does_not_crash(store):
    from clawmetry.startup import SETTING, record_progress
    for raw in ("invalid", "[]", "null"):
        store.set_node_setting(SETTING, raw)
        record_progress(store, "discovering")
        assert store.query_startup_status()["initialized"] is False


def test_endpoint_uses_daemon_and_preserves_unavailable(monkeypatch):
    from routes import local_query, onboarding
    app = Flask(__name__)
    app.register_blueprint(onboarding.bp_onboarding)
    calls = []

    def proxy(method):
        calls.append(method)
        return {"available": True, "initialized": False, "has_data": False}

    monkeypatch.setattr(local_query, "local_store_call_via_daemon", proxy)
    response = app.test_client().get("/api/onboarding/readiness")
    assert response.status_code == 200
    assert response.json["initialized"] is False
    assert calls == ["query_startup_status"]
    assert "query_startup_status" in local_query._DAEMON_METHODS
    monkeypatch.setattr(local_query, "local_store_call_via_daemon", lambda _: None)
    response = app.test_client().get("/api/onboarding/readiness")
    assert response.status_code == 503
    assert response.json == {"available": False}


def test_upgrading_dashboard_can_read_an_older_populated_daemon(monkeypatch):
    from routes import local_query, onboarding
    app = Flask(__name__)
    app.register_blueprint(onboarding.bp_onboarding)
    monkeypatch.setattr(local_query, "local_store_call_via_daemon",
                        lambda method, **kw: [{"session_id": "existing"}] if method == "query_sessions_table" else local_query.PROXY_UNAVAILABLE)
    response = app.test_client().get("/api/onboarding/readiness")
    assert response.json == {"available": True, "initialized": True, "has_data": True}


def test_daemon_progress_is_in_the_encrypted_snapshot(store, tmp_path, monkeypatch):
    from clawmetry import sync
    monkeypatch.setattr(sync, "_startup_store", store)
    monkeypatch.setattr(sync, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(sync, "SYNC_PROGRESS_FILE", tmp_path / "progress.json")
    monkeypatch.setattr(sync, "_sync_progress_done", False)
    monkeypatch.setattr(sync, "_sync_progress_started_at", None)
    monkeypatch.setattr(sync, "load_config", lambda: {})
    sync._record_sync_progress("runtime_history", 4, 8)
    assert sync._build_first_run()["readiness"]["done"] == 4
    sync._record_sync_progress("complete", 0, status="complete")
    assert sync._build_first_run()["readiness"]["initialized"] is True
    sync._record_sync_progress("crons", 0)
    assert sync._build_first_run()["readiness"]["phase"] == "complete"


def test_live_template_renders_preparation_and_ships_assets():
    tree = ast.parse((ROOT / "dashboard.py").read_text())
    html = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DASHBOARD_HTML" for t in n.targets))
    app = Flask(__name__, template_folder=str(ROOT / "clawmetry/templates"))
    with app.test_request_context():
        rendered = render_template_string(html, version="test")
    assert 'id="first-run"' in rendered
    for asset in ("js/first-run.js", "css/first-run.css"):
        assert asset in rendered
        assert (ROOT / "clawmetry/static" / asset).is_file()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required for browser state tests")
def test_browser_state_machine():
    result = subprocess.run(["node", str(ROOT / "tests/test_startup_readiness.js")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
