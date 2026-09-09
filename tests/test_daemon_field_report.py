"""The daemon must report the failures that stop it from working.

Field failure 2026-09-08: a Pro node's daemon was locked out of its own pid
lock and retried every 30 seconds for twelve hours. It reached nobody. It
exited 0, so launchd recorded successes; the DuckDB error handler and the
auto-update worker both initialise AFTER the lock is claimed, so neither ran;
with no daemon there was no heartbeat, so the node went quiet, and quiet is
not an event. The customer found out and emailed us a screenshot.

The pipeline that should have caught it already existed and had one producer,
the installer. These tests pin the daemon as its second: that it reports the
failure, that it does NOT report the normal cases, that it cannot spam, and
that the report carries aggregates and nothing else.
"""
import json
import time

import pytest

from clawmetry import field_report as fr


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "_config_dir", lambda: tmp_path)
    # Sendable by default; individual tests re-suppress.
    monkeypatch.setattr(fr, "_suppressed", lambda: "")
    monkeypatch.setattr(fr, "_install_id", lambda: "11111111-2222-3333-4444-555555555555")
    return tmp_path


@pytest.fixture()
def sent(monkeypatch):
    """Capture what would go on the wire."""
    out = []
    monkeypatch.setattr(fr, "_send", out.append)
    return out


# ── the privacy contract, key by key ─────────────────────────────────────────
def test_the_report_is_a_closed_dict_of_aggregates():
    p = fr.daemon_failure_payload("daemon_lock_refused", version="0.12.845")
    assert set(p) == {
        "install_id", "stage", "session_id", "failure_class",
        "bootstrap_python", "desktop_version", "os", "os_version", "arch",
    }


def test_the_server_side_key_is_one_row_per_class_per_day():
    """The sink drops a conflicting (install_id, session_id, stage). A constant
    session id would therefore record the first daemon failure an install ever
    had and mute every later one, including a different failure class."""
    import time as _t

    day = _t.strftime("%Y%m%d", _t.gmtime())
    a = fr.daemon_failure_payload("daemon_lock_refused", "1")["session_id"]
    b = fr.daemon_failure_payload("daemon_ingest_stalled", "1")["session_id"]
    assert a == f"daemon_lock_refused-{day}"
    assert a != b, "two failure classes would collide onto one row"


def test_the_report_carries_no_identifying_values(home, monkeypatch):
    """A machine's paths, users, hostname and node id must never be on the
    wire. Asserted over the SERIALISED body, so a nested value cannot smuggle
    one past a key check."""
    import getpass
    import os
    import socket

    blob = json.dumps(fr.daemon_failure_payload("daemon_ingest_stalled", "0.12.845"))
    for secret in (str(home), os.path.expanduser("~"), socket.gethostname(),
                   getpass.getuser()):
        if secret and len(secret) > 2:
            assert secret not in blob, f"{secret!r} reached the payload"


def test_an_unknown_failure_class_is_coerced_not_forwarded():
    """The cloud coerces anything outside its enum to "unknown"; matching that
    here means the wire value is never a surprise, including free text."""
    p = fr.daemon_failure_payload("rm -rf /Users/alper/secret", version="1")
    assert p["failure_class"] == "unknown"


def test_python_version_is_the_family_not_the_build():
    p = fr.daemon_failure_payload("daemon_lock_refused", version="1")
    assert p["bootstrap_python"].count(".") == 1  # "3.11", never "3.11.9"


# ── the opt-outs ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("var", ["CLAWMETRY_OFFLINE", "SELF_HOSTED",
                                 "CLAWMETRY_SELF_HOSTED"])
def test_an_air_gapped_or_self_hosted_install_sends_nothing(home, monkeypatch,
                                                            sent, var):
    """The narrow ``is_custom_endpoint()`` check misses both of these: an
    air-gapped node sets no endpoint, and a self-hosted server IS the endpoint
    so it never sets one either. A report about a broken daemon is exactly the
    kind of well-meant call that gets shipped past an air gap."""
    monkeypatch.undo()  # drop the fixture's blanket _suppressed stub
    # ... and immediately restore the isolation it also carried: nothing in
    # this suite may read or write the real ~/.clawmetry.
    monkeypatch.setattr(fr, "_config_dir", lambda: home)
    monkeypatch.setattr(fr, "_install_id", lambda: "1" * 32)
    monkeypatch.setenv(var, "1")
    assert fr._suppressed() == "egress_suppressed"
    assert fr.report_daemon_failure("daemon_lock_refused") is False
    assert sent == []


@pytest.mark.parametrize("reason", ["telemetry_optout", "egress_suppressed"])
def test_a_suppressed_install_sends_nothing(monkeypatch, sent, reason):
    monkeypatch.setattr(fr, "_suppressed", lambda: reason)
    assert fr.report_daemon_failure("daemon_lock_refused") is False
    assert sent == []


def test_no_install_id_means_no_report(monkeypatch, sent):
    monkeypatch.setattr(fr, "_install_id", lambda: "")
    assert fr.report_daemon_failure("daemon_lock_refused") is False
    assert sent == []


# ── a restart loop must not become a ping loop ───────────────────────────────
def test_the_second_report_inside_the_window_is_dropped(sent):
    assert fr.report_daemon_failure("daemon_lock_refused") is True
    assert fr.report_daemon_failure("daemon_lock_refused") is False
    assert len(sent) == 1


def test_the_throttle_survives_a_restart(home, sent):
    """The restart-loop case is a NEW process every 30 seconds, so in-memory
    throttling would throttle nothing. The stamp is on disk."""
    assert fr.report_daemon_failure("daemon_lock_refused") is True
    import importlib

    importlib.reload(fr)  # a brand new process, same home
    fr._config_dir = lambda: home
    fr._suppressed = lambda: ""
    fr._install_id = lambda: "1" * 32
    fr._send = sent.append
    assert fr.report_daemon_failure("daemon_lock_refused") is False


def test_the_window_expires(home, sent):
    assert fr.report_daemon_failure("daemon_lock_refused") is True
    stamp = fr._dedupe_file("daemon_lock_refused")
    old = time.time() - (fr.DEDUPE_SECS + 60)
    import os

    os.utime(stamp, (old, old))
    assert fr.report_daemon_failure("daemon_lock_refused") is True


def test_classes_are_throttled_independently(sent):
    assert fr.report_daemon_failure("daemon_lock_refused") is True
    assert fr.report_daemon_failure("daemon_ingest_stalled") is True


def test_a_hanging_post_still_stamps(home, monkeypatch):
    """Stamped before the send: a POST that burns its whole timeout must not
    let the next restart try again 30 seconds later."""
    monkeypatch.setattr(fr, "_send", lambda p: time.sleep(0.2))
    monkeypatch.setattr(fr, "BLOCKING_TIMEOUT_SEC", 0.05)
    assert fr.report_daemon_failure("daemon_lock_refused", blocking=True) is True
    assert fr._dedupe_file("daemon_lock_refused").exists()


def test_blocking_send_is_bounded(monkeypatch):
    """The failing path exits the process next; it may not hang there."""
    monkeypatch.setattr(fr, "_send", lambda p: time.sleep(5))
    monkeypatch.setattr(fr, "BLOCKING_TIMEOUT_SEC", 0.1)
    t0 = time.time()
    fr.report_daemon_failure("daemon_lock_refused", blocking=True)
    assert time.time() - t0 < 2.0


# ── when the daemon is and is not broken ─────────────────────────────────────
def _state(home, monkeypatch, last_sync):
    import clawmetry.sync as sync

    f = home / "sync-state.json"
    f.write_text(json.dumps({"last_sync": last_sync} if last_sync else {}))
    monkeypatch.setattr(sync, "STATE_FILE", f)
    return f


def test_a_node_that_never_synced_is_not_called_broken(home, monkeypatch):
    """A fresh install has no timestamp. Unknown is not the same as stalled,
    and reporting every new install as a field failure would bury the real
    ones."""
    _state(home, monkeypatch, None)
    assert fr.last_sync_age_secs() is None


def test_an_unparseable_timestamp_accuses_nobody(home, monkeypatch):
    _state(home, monkeypatch, "yesterday-ish")
    assert fr.last_sync_age_secs() is None


def test_the_field_failure_reads_as_hours_stale(home, monkeypatch):
    _state(home, monkeypatch, "2026-09-08T19:32:21+00:00")
    age = fr.last_sync_age_secs()
    assert age is not None and age > 3600


def test_a_fresh_sync_is_not_stale(home, monkeypatch):
    import datetime as dt

    _state(home, monkeypatch, dt.datetime.now(dt.timezone.utc).isoformat())
    assert fr.last_sync_age_secs() < 60


# ── the daemon's own no-progress check ───────────────────────────────────────
def test_a_healthy_daemon_reports_nothing(home, monkeypatch, sent):
    import datetime as dt
    import clawmetry.sync as sync

    _state(home, monkeypatch, dt.datetime.now(dt.timezone.utc).isoformat())
    sync._report_if_ingest_stalled()
    assert sent == []


def test_a_wedged_daemon_reports_itself(home, monkeypatch, sent):
    """The process is up, the watchdog thread is scheduling, and no cycle has
    completed in an hour. Every liveness probe in the stack says fine."""
    import clawmetry.sync as sync

    _state(home, monkeypatch, "2026-09-08T19:32:21+00:00")
    sync._report_if_ingest_stalled()
    assert [p["failure_class"] for p in sent] == ["daemon_ingest_stalled"]


def test_the_stall_check_never_raises(monkeypatch):
    """It runs inside the watchdog thread; an exception there would silently
    stop the heartbeat and cost us the lock."""
    import clawmetry.sync as sync

    monkeypatch.setattr(fr, "last_sync_age_secs",
                        lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    sync._report_if_ingest_stalled()  # must not raise
