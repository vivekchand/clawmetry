"""The dashboard is never held behind a preparation screen.

The blocking first-install overlay was removed on 2026-09-20 after it
trapped a working dashboard three times in four days: it locked the
hosted nav for accounts with nothing to wait for (#6058), it held a
populated dashboard for 9m21s while waiting for a sweep to finish
(#6099), and it settled into a terminal "taking a little longer" state
on one transient probe failure during a daemon upgrade and never
re-checked, because settling clears its own poll timer.

The daemon still records how far its first pass has got, and still
publishes that in the encrypted snapshot, because the hosted first-run
banner reads it. What is gone is anything that covers the dashboard
with it. A machine with no agents is told so by the Agents roster's own
empty state, on the page, with the rest of the product reachable.

AC-OBS-FRP-001.1: the dashboard is not covered while collection runs
AC-OBS-FRP-001.2: restart, upgrade and existing-history impose no wait
AC-OBS-FRP-001.3: an empty machine is told on the page, not behind it
AC-OBS-FRP-001.6: readiness travels in the machine's own snapshot
"""
import ast
from pathlib import Path

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


def test_agent_activity_during_setup_opens_the_dashboard(store):
    """AC-OBS-FRP-001.2 -- rows arriving mid-sweep end the wait.

    This assertion used to read the other way round, and that is the bug.
    Readiness was keyed on the daemon finishing every phase for every
    runtime, so a new install on a machine with existing agent history sat
    on the preparation screen for minutes (9m21s measured on a real node)
    while the data behind it was already queryable. An install over an
    established history is an established installation the moment its rows
    land; the screen replaces empty panels, and these panels are not empty.
    """
    from clawmetry.startup import record_progress
    record_progress(store, "discovering")
    assert store.query_startup_status()["initialized"] is False
    store._conn.execute("INSERT INTO sessions (agent_type, session_id, updated_at) VALUES ('openclaw', 'arriving', 1)")
    status = store.query_startup_status()
    assert status["has_data"] is True
    assert status["initialized"] is True
    # Still mid-sweep: the phase stays honest, only the gate opens.
    assert status["phase"] == "discovering"


def test_a_later_sweep_phase_cannot_reclose_the_dashboard(store):
    """AC-OBS-FRP-001.2 -- the release is not undone by the next tick.

    ``record_progress`` runs once per phase for the whole sweep. A user who
    was let through must not be pulled back onto the screen by the next one.
    """
    from clawmetry.startup import record_progress
    store._conn.execute("INSERT INTO sessions (agent_type, session_id, updated_at) VALUES ('claude_code', 'existing', 1)")
    record_progress(store, "discovering")
    assert store.query_startup_status()["initialized"] is True
    for phase in ("runtime_history", "logs", "crons"):
        record_progress(store, phase, 1, 50)
        assert store.query_startup_status()["initialized"] is True



def test_daemon_diagnostics_are_not_agent_activity(store):
    """AC-OBS-FRP-001.3 -- releasing on data must not release on noise.

    The daemon writes its own error and telemetry events on every install.
    Now that ``has_data`` alone opens the dashboard, counting those would
    walk a machine that has never run an agent straight onto empty panels,
    which is the one case the screen exists to serve.
    """
    from clawmetry.startup import record_progress
    record_progress(store, "discovering")
    store.ingest({"id": "diagnostic", "agent_type": "daemon", "node_id": "test",
                  "event_type": "daemon_error", "ts": "2026-09-16T10:00:00Z"})
    store.flush()
    status = store.query_startup_status()
    assert status["has_data"] is False
    assert status["initialized"] is False


def test_malformed_progress_does_not_crash(store):
    from clawmetry.startup import SETTING, record_progress
    for raw in ("invalid", "[]", "null"):
        store.set_node_setting(SETTING, raw)
        record_progress(store, "discovering")
        assert store.query_startup_status()["initialized"] is False


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


@pytest.mark.parametrize("readiness", [[], {}, "pending", {"available": False},
    {"available": True, "initialized": "false", "has_data": False}])
def test_snapshot_omits_invalid_readiness(readiness, tmp_path, monkeypatch, caplog):
    from clawmetry import sync
    from types import SimpleNamespace
    # The minimal CI job imports sync before DuckDB/dashboard and keeps its
    # standalone stdout logger. Capture that logger regardless of import order.
    monkeypatch.setattr(sync.log, "propagate", True)
    monkeypatch.setattr(sync, "_startup_store", SimpleNamespace(query_startup_status=lambda: readiness))
    monkeypatch.setattr(sync, "SYNC_PROGRESS_FILE", tmp_path / "progress.json")
    monkeypatch.setattr(sync, "_sync_progress_done", True)
    snapshot = sync._build_first_run()
    assert snapshot["done"] is True
    assert "readiness" not in snapshot
    assert "readiness" in caplog.text


def test_no_blocking_preparation_screen_ships():
    """AC-OBS-FRP-001.1 -- nothing covers the dashboard while it collects.

    Asserted against the RENDERED page, not the source, because the
    overlay reached the browser through a Jinja include and two asset
    tags rather than through anything importable. Checking the shipped
    files alone would pass while an include still pulled one in.
    """
    tree = ast.parse((ROOT / "dashboard.py").read_text())
    html = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DASHBOARD_HTML" for t in n.targets))
    app = Flask(__name__, template_folder=str(ROOT / "clawmetry/templates"))
    with app.test_request_context():
        rendered = render_template_string(html, version="test")
    assert 'id="first-run"' not in rendered, (
        "the blocking preparation overlay is back in the rendered page"
    )
    for asset in ("js/first-run.js", "css/first-run.css"):
        assert asset not in rendered, f"{asset} is referenced again"
        assert not (ROOT / "clawmetry/static" / asset).exists(), f"{asset} is back"
    assert not (ROOT / "clawmetry/templates/partials/first-run.html").exists()


def test_nothing_gates_the_dashboard_on_a_readiness_probe():
    """AC-OBS-FRP-001.1 -- no code path waits on a setup check again.

    The overlay published ``window.cmFirstRun`` and three unrelated
    things deferred to it: the shared poller helper, the cloud sync
    banner and the boot overlay. The banner's guard was an unconditional
    ``if (window.cmFirstRun) return;``, so it never ran at all once the
    overlay shipped. Those call sites are the reason a deleted screen
    can still hold the product, so assert they are gone too.
    """
    # Auto-discovered, not a file list. The first pass of this guard read
    # app.js alone and missed a live ``window.cmFirstRun.start(d)`` in
    # onboarding.js, which Drift Bot caught. A hand-maintained scope is how
    # the next leftover survives, so sweep everything that ships.
    js_dir = ROOT / "clawmetry/static/js"
    scanned = sorted(js_dir.glob("*.js"))
    assert len(scanned) > 5, f"expected the shipped js directory, found {scanned}"
    offenders = [p.name for p in scanned if "cmFirstRun" in p.read_text()]
    assert offenders == [], f"these still defer to the removed screen: {offenders}"
    onboarding = (ROOT / "routes/onboarding.py").read_text()
    assert "/api/onboarding/readiness" not in onboarding, (
        "the readiness endpoint outlived its only consumer"
    )


def test_an_empty_machine_is_told_on_the_page():
    """AC-OBS-FRP-001.3 -- the guidance survives the overlay.

    Removing the screen must not remove the one thing it did that was
    worth doing. The Agents roster remains reachable and carries a
    runtime-neutral empty state, reachable, with the nav still live.
    """
    inventory = (ROOT / "clawmetry/templates/tabs/inventory.html").read_text()
    assert 'id="inv-empty"' in inventory
    assert 'data-i18n="inventory.empty_title"' in inventory
    assert '<div class="page" id="page-inventory">' in inventory
    assistant = (ROOT / "clawmetry/templates/tabs/assistant.html").read_text()
    assert 'id="cm-assistant-input"' in assistant
    assert 'data-tab="inventory"' in (ROOT / "dashboard.py").read_text()
