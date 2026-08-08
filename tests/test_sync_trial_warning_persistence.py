"""Trial-warning once-per-day guard must survive daemon restarts.

2026-08-08 spam RCA: `_maybe_send_trial_warning`'s once-per-day guard was
process-memory only. The daemon restarts on every auto-update (which
tracks every PyPI release), so each restart re-fired the warning and a
customer received the "your trial ends in 2 days" email hourly.

These tests pin the fix: the last-warn day is persisted to
``~/.clawmetry/trial_warning_state.json`` and consulted by fresh
processes before firing.

Hermetic: no real HTTP, HOME redirected to a tmp dir.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync(monkeypatch, tmp_path):
    monkeypatch.setenv('HOME', str(tmp_path))
    sys.modules.pop('clawmetry.sync', None)
    import clawmetry.sync as s
    # Re-point the persisted marker at the tmp HOME (the module-level
    # constant was computed at import with the real HOME on some platforms).
    monkeypatch.setattr(
        s, '_TRIAL_WARNING_STATE_PATH',
        str(tmp_path / '.clawmetry' / 'trial_warning_state.json'))
    s._TRIAL_WARNING_STATE['last_warn_day'] = ''
    monkeypatch.setattr(s, 'load_config', lambda: {'api_key': 'cm_test'})
    yield s


@pytest.fixture
def posts(sync, monkeypatch):
    calls = []
    monkeypatch.setattr(
        sync, '_post',
        lambda path, body, key, timeout=6: calls.append((path, body)) or {})
    return calls


def test_first_fire_posts_and_persists(sync, posts):
    sync._maybe_send_trial_warning({'trial_days_left': 2})
    assert len(posts) == 1
    assert posts[0][0] == '/ingest/trial-warning'
    with open(sync._TRIAL_WARNING_STATE_PATH, encoding='utf-8') as fh:
        assert json.load(fh)['last_warn_day']


def test_same_process_same_day_fires_once(sync, posts):
    for _ in range(10):
        sync._maybe_send_trial_warning({'trial_days_left': 2})
    assert len(posts) == 1


def test_restart_same_day_does_not_refire(sync, posts, monkeypatch):
    """The spam scenario: fire once, then simulate a daemon restart by
    clearing the in-memory guard. The disk marker must still block."""
    sync._maybe_send_trial_warning({'trial_days_left': 2})
    assert len(posts) == 1
    sync._TRIAL_WARNING_STATE['last_warn_day'] = ''  # "restart"
    sync._maybe_send_trial_warning({'trial_days_left': 2})
    assert len(posts) == 1, 'restarted daemon must not re-fire the same day'


def test_next_day_fires_again(sync, posts):
    sync._persist_trial_warning_day('2000-01-01')
    sync._TRIAL_WARNING_STATE['last_warn_day'] = ''
    sync._maybe_send_trial_warning({'trial_days_left': 1})
    assert len(posts) == 1, 'a marker from a previous day must not block'


def test_outside_window_never_fires(sync, posts):
    sync._maybe_send_trial_warning({'trial_days_left': 6})
    assert posts == []
    assert not os.path.exists(sync._TRIAL_WARNING_STATE_PATH)


def test_unreadable_marker_does_not_crash(sync, posts):
    os.makedirs(os.path.dirname(sync._TRIAL_WARNING_STATE_PATH), exist_ok=True)
    with open(sync._TRIAL_WARNING_STATE_PATH, 'w', encoding='utf-8') as fh:
        fh.write('not-json{{{')
    sync._maybe_send_trial_warning({'trial_days_left': 2})
    assert len(posts) == 1
