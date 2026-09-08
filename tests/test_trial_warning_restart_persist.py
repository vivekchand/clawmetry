"""The trial-warning once-per-day guard must survive a daemon restart.

_maybe_send_trial_warning throttles POST /ingest/trial-warning via the
in-memory _TRIAL_WARNING_STATE["last_warn_day"]. Auto-update restarts the
daemon on every release (often several per day), which resets that guard —
each restart re-fired the POST and the cloud emailed the customer again
(2026-08-10 trial-email spam RCA: one account got 5+ "trial has ended"
emails in a single day). The fix persists the warned day to
~/.clawmetry/trial_warnings.json (the same file routes/trial.py's
/api/trial/mark-warned writes) so a fresh process sees it and stays quiet.

Hermetic: no real HTTP, no real home directory.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _fresh_sync(monkeypatch, tmp_path):
    """Import clawmetry.sync fresh (simulates a daemon process start) with
    the warnings file redirected into tmp_path and network/config stubbed."""
    sys.modules.pop('clawmetry.sync', None)
    import clawmetry.sync as s
    monkeypatch.setattr(
        s, '_TRIAL_WARNINGS_PATH', str(tmp_path / 'trial_warnings.json'))
    monkeypatch.setattr(s, 'load_config', lambda: {'api_key': 'cm_test'})
    posts = []
    monkeypatch.setattr(
        s, '_post', lambda *a, **kw: posts.append(a) or {})
    return s, posts


IN_WINDOW = {'trial_days_left': 1}  # default warning window is 2 days


def test_first_warning_fires_and_persists(monkeypatch, tmp_path):
    s, posts = _fresh_sync(monkeypatch, tmp_path)
    s._maybe_send_trial_warning(IN_WINDOW)
    assert len(posts) == 1, 'first in-window heartbeat should warn'
    data = json.loads((tmp_path / 'trial_warnings.json').read_text())
    today = s.datetime.now(s.timezone.utc).strftime('%Y-%m-%d')
    assert data == {today: 1}


def test_same_process_second_beat_is_throttled(monkeypatch, tmp_path):
    s, posts = _fresh_sync(monkeypatch, tmp_path)
    s._maybe_send_trial_warning(IN_WINDOW)
    s._maybe_send_trial_warning(IN_WINDOW)
    assert len(posts) == 1


def test_restart_does_not_refire(monkeypatch, tmp_path):
    """The regression: a fresh process (auto-update restart) must see the
    on-disk record and NOT re-POST the same day."""
    s1, posts1 = _fresh_sync(monkeypatch, tmp_path)
    s1._maybe_send_trial_warning(IN_WINDOW)
    assert len(posts1) == 1

    # Simulate the daemon restarting: brand-new module, empty in-memory state.
    s2, posts2 = _fresh_sync(monkeypatch, tmp_path)
    assert s2._TRIAL_WARNING_STATE['last_warn_day'] == ''
    s2._maybe_send_trial_warning(IN_WINDOW)
    assert posts2 == [], (
        'restarted daemon re-fired /ingest/trial-warning on the same UTC day')
    # And the fast-path cache is primed so later beats skip the disk read.
    assert s2._TRIAL_WARNING_STATE['last_warn_day'] != ''


def test_corrupt_warnings_file_never_raises(monkeypatch, tmp_path):
    s, posts = _fresh_sync(monkeypatch, tmp_path)
    (tmp_path / 'trial_warnings.json').write_text('{not json!!')
    s._maybe_send_trial_warning(IN_WINDOW)  # must not raise
    assert len(posts) == 1, 'corrupt state file should fail open (warn once)'
    # And the write path repairs the file.
    data = json.loads((tmp_path / 'trial_warnings.json').read_text())
    assert isinstance(data, dict) and len(data) == 1


def test_mark_warned_endpoint_record_suppresses_daemon(monkeypatch, tmp_path):
    """The file is shared with routes/trial.py's /api/trial/mark-warned —
    a record written by that endpoint must also suppress the daemon POST."""
    s, posts = _fresh_sync(monkeypatch, tmp_path)
    today = s.datetime.now(s.timezone.utc).strftime('%Y-%m-%d')
    (tmp_path / 'trial_warnings.json').write_text(json.dumps({today: 1}))
    s._maybe_send_trial_warning(IN_WINDOW)
    assert posts == []


def test_unreadable_dir_never_raises(monkeypatch, tmp_path):
    """Persistence failure must not break the warning itself (never raises)."""
    s, posts = _fresh_sync(monkeypatch, tmp_path)
    # Point the warnings file somewhere unwritable-ish: a path whose parent
    # is an existing FILE, so makedirs/open both fail.
    blocker = tmp_path / 'blocker'
    blocker.write_text('x')
    monkeypatch.setattr(
        s, '_TRIAL_WARNINGS_PATH', str(blocker / 'trial_warnings.json'))
    s._maybe_send_trial_warning(IN_WINDOW)  # must not raise
    assert len(posts) == 1
