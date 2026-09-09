"""`clawmetry status` must not report health it has not checked.

Field failure (2026-09-08, a Pro node): the daemon had not started since 19:32
the previous evening, yet status printed "Cloud sync: Connected", "Runtimes:
watching", "Daemon: Running (launchd)" and a bare 12-hour-old "Last sync" with
no comment. Every green tick was reporting CONFIGURATION; nothing on the screen
reported whether data was actually moving, so the customer had to mail us a
screenshot to find out his node was dead.

Two things are asserted here: that a registered-but-not-running launchd job is
not called "Running", and that a stale last-sync is called out in words a
non-engineer can act on.
"""
import json

import pytest

from clawmetry import cli
from clawmetry import sync


# ── launchctl output means less than its exit code suggests ──────────────────
RUNNING = '''{
	"LimitLoadToSessionType" = "Aqua";
	"StandardOutPath" = "/Users/x/.clawmetry/sync.log";
	"Label" = "com.clawmetry.sync";
	"OnDemand" = false;
	"LastExitStatus" = 0;
	"PID" = 4242;
	"Program" = "/usr/bin/python3";
};'''

RESTART_LOOPING = '''{
	"LimitLoadToSessionType" = "Aqua";
	"StandardOutPath" = "/Users/x/.clawmetry/sync.log";
	"Label" = "com.clawmetry.sync";
	"OnDemand" = false;
	"LastExitStatus" = 0;
	"Program" = "/usr/bin/python3";
};'''


def test_a_job_with_a_pid_is_running():
    st = cli._launchd_job_state(RUNNING)
    assert st["pid"] == 4242


def test_a_registered_job_without_a_pid_is_not_running():
    """This is the whole bug: `launchctl list` exits 0 for this job too."""
    st = cli._launchd_job_state(RESTART_LOOPING)
    assert st["pid"] is None
    assert st["last_exit"] == 0


def test_garbage_listing_does_not_raise():
    assert cli._launchd_job_state("not launchctl output")["pid"] is None
    assert cli._launchd_job_state("")["pid"] is None


# ── a stale last-sync must be named ──────────────────────────────────────────
def test_a_recent_sync_is_not_flagged():
    import datetime as dt

    now = dt.datetime(2026, 9, 9, 8, 0, tzinfo=dt.timezone.utc).timestamp()
    age, stale = cli._sync_age("2026-09-09T07:59:30+00:00", now=now)
    assert stale is False
    assert age == "30s ago"


def test_the_field_failure_is_flagged_in_hours():
    import datetime as dt

    now = dt.datetime(2026, 9, 9, 7, 51, tzinfo=dt.timezone.utc).timestamp()
    age, stale = cli._sync_age("2026-09-08T19:32:21+00:00", now=now)
    assert stale is True
    assert age == "12h ago"


@pytest.mark.parametrize("bad", ["", None, "not a timestamp", "????"])
def test_an_unreadable_timestamp_accuses_nobody(bad):
    age, stale = cli._sync_age(bad)
    assert (age, stale) == (None, False)


def test_a_naive_timestamp_is_read_as_utc():
    import datetime as dt

    now = dt.datetime(2026, 9, 9, 7, 51, tzinfo=dt.timezone.utc).timestamp()
    _, stale = cli._sync_age("2026-09-08T19:32:21", now=now)
    assert stale is True


# ── the advice the user actually reads ───────────────────────────────────────
@pytest.fixture()
def stalled_state(tmp_path, monkeypatch):
    state = tmp_path / "sync_state.json"
    state.write_text(json.dumps({"last_sync": "2026-01-01T00:00:00+00:00"}))
    monkeypatch.setattr(sync, "STATE_FILE", state)
    return state


def test_stalled_node_gets_a_sentence_and_a_command(stalled_state, capsys):
    cli._print_stall_advice("")
    out = capsys.readouterr().out
    assert "Nothing has synced" in out
    assert "clawmetry sync --restart" in out


def test_the_lock_loop_signature_gets_its_own_instruction(stalled_state, capsys):
    """The log line the customer sent us names the actual cause; when it is
    there, tell him the thing that fixes THAT."""
    cli._print_stall_advice(
        "[clawmetry-sync] Another instance is already running. Exiting.\n" * 3
    )
    out = capsys.readouterr().out
    assert "leftover lock file" in out
    assert "pip install -U clawmetry" in out


def test_a_healthy_node_stays_quiet(tmp_path, monkeypatch, capsys):
    import datetime as dt

    state = tmp_path / "sync_state.json"
    state.write_text(json.dumps(
        {"last_sync": dt.datetime.now(dt.timezone.utc).isoformat()}))
    monkeypatch.setattr(sync, "STATE_FILE", state)
    cli._print_stall_advice("")
    assert capsys.readouterr().out == ""


def test_no_state_file_is_not_an_accusation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sync, "STATE_FILE", tmp_path / "missing.json")
    cli._print_stall_advice("")
    assert capsys.readouterr().out == ""
