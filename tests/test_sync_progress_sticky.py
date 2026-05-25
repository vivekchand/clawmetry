"""
Regression: the "syncing…" banner must not stick on "Aggregating: crons" forever.

The sync-progress banner is a fresh-install affordance. The daemon's startup
sync walks phases and ends with status="complete". But the steady-state main
loop calls sync_crons() (and friends) every tick, each of which records its
phase as "running" on entry. Before the fix, those steady-state calls re-opened
the banner indefinitely (sync_crons even early-returns with no cron jobs.json,
leaving it pinned on "crons/running/0/0"). This guards that once the first sync
completes, steady-state phase churn is suppressed.
"""
import importlib
import json


def _sync():
    return importlib.import_module("clawmetry.sync")


def test_steady_state_phase_churn_does_not_reopen_banner(tmp_path, monkeypatch):
    sync = _sync()
    pf = tmp_path / "sync_progress.json"
    monkeypatch.setattr(sync, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(sync, "SYNC_PROGRESS_FILE", pf)
    monkeypatch.setattr(sync, "_sync_progress_done", False)
    monkeypatch.setattr(sync, "_sync_progress_started_at", None)

    # initial sync: phases render normally
    sync._record_sync_progress("indexing", 3, 10)
    assert json.loads(pf.read_text())["phase"] == "indexing"

    # initial sync completes -> banner clears
    sync._record_sync_progress("complete", 0, 0, status="complete")
    assert json.loads(pf.read_text())["status"] == "complete"

    # steady-state main-loop ticks (sync_crons / sync_sessions / ...) must be
    # ignored -- this is exactly what was sticking the banner on "crons".
    sync._record_sync_progress("crons", 0)
    sync._record_sync_progress("sessions", 0)
    sync._record_sync_progress("crons", 0, 0)
    after = json.loads(pf.read_text())
    assert after["status"] == "complete", "steady-state churn re-opened the banner"
    assert after["phase"] == "complete", f"banner stuck on {after['phase']!r}"


def test_initial_sync_still_shows_phases_until_complete(tmp_path, monkeypatch):
    sync = _sync()
    pf = tmp_path / "sync_progress.json"
    monkeypatch.setattr(sync, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(sync, "SYNC_PROGRESS_FILE", pf)
    monkeypatch.setattr(sync, "_sync_progress_done", False)
    monkeypatch.setattr(sync, "_sync_progress_started_at", None)

    # before completion, every phase update is honored (fresh-install UX intact)
    for phase in ("discovering", "indexing", "crons", "memory"):
        sync._record_sync_progress(phase, 0)
        assert json.loads(pf.read_text())["phase"] == phase
        assert json.loads(pf.read_text())["status"] == "running"
