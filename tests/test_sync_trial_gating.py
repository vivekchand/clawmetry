"""Test client-side trial gating in clawmetry/sync.py.

Covers:
  - _update_trial_state caches plan + sync_allowed correctly
  - _sync_allowed() default True until cloud says otherwise
  - "Trial expired -> Sync paused" log fires once per UTC day, not every call
  - "Pro plan detected -> Sync resumed" log fires on transition back
  - 429 from _post toggles sync_allowed=False (server confirms throttle)
  - sync_*() entry points bail early when sync_allowed=False

Hermetic: never makes real HTTP. Reuses each test's monkeypatch to neuter
network / time / log side-effects.
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import logging
import os
import sys
import urllib.error

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# We import the module fresh per test to reset the in-memory _TRIAL_STATE.

@pytest.fixture
def sync(monkeypatch):
    sys.modules.pop('clawmetry.sync', None)
    import clawmetry.sync as s
    # Default: pretend sync is allowed (matches module default).
    s._TRIAL_STATE['sync_allowed'] = True
    s._TRIAL_STATE['plan'] = None
    s._TRIAL_STATE['trial_days_left'] = None
    s._TRIAL_STATE['last_log_day'] = ''
    # The clawmetry-sync logger has propagate=False so caplog (which hooks
    # the root logger) won't see records. Flip it on for the test scope.
    _prev = s.log.propagate
    s.log.propagate = True
    yield s
    s.log.propagate = _prev


# ── _update_trial_state ────────────────────────────────────────────────────

def test_update_caches_plan_and_sync_flag(sync):
    sync._update_trial_state({
        'sync_allowed': False, 'plan': 'trial_expired',
        'trial_days_left': 0, 'upgrade_url': 'https://app.clawmetry.com/cloud',
    })
    assert sync._TRIAL_STATE['sync_allowed'] is False
    assert sync._TRIAL_STATE['plan'] == 'trial_expired'
    assert sync._TRIAL_STATE['trial_days_left'] == 0
    assert sync._TRIAL_STATE['upgrade_url'] == 'https://app.clawmetry.com/cloud'

def test_default_sync_allowed_true(sync):
    """Until cloud responds, the daemon optimistically syncs."""
    assert sync._sync_allowed() is True

def test_pause_log_fires_once_per_day(sync, caplog):
    caplog.set_level(logging.WARNING, logger=sync.log.name)
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    # Same UTC day → second call should NOT add another warning.
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    pause_logs = [r for r in caplog.records if 'Trial expired' in r.getMessage()]
    assert len(pause_logs) == 1, \
        f'Expected 1 pause log per day; got {len(pause_logs)}'

def test_pause_log_includes_upgrade_url(sync, caplog):
    caplog.set_level(logging.WARNING, logger=sync.log.name)
    sync._update_trial_state({
        'sync_allowed': False, 'plan': 'trial_expired',
        'upgrade_url': 'https://app.clawmetry.com/cloud',
    })
    pause_logs = [r for r in caplog.records if 'Trial expired' in r.getMessage()]
    assert pause_logs
    msg = pause_logs[0].getMessage()
    assert 'https://app.clawmetry.com/cloud' in msg
    assert 'Upgrade to Pro' in msg

def test_resume_log_fires_on_pro_transition(sync, caplog):
    caplog.set_level(logging.INFO, logger=sync.log.name)
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    # Now upgrade detected.
    sync._update_trial_state({'sync_allowed': True, 'plan': 'pro'})
    resume_logs = [r for r in caplog.records if 'sync resumed' in r.getMessage()]
    assert len(resume_logs) == 1
    assert sync._TRIAL_STATE['plan'] == 'pro'
    assert sync._sync_allowed() is True

def test_no_resume_log_when_already_pro(sync, caplog):
    """Don't log 'resumed' on every Pro heartbeat — only on transition."""
    caplog.set_level(logging.INFO, logger=sync.log.name)
    sync._update_trial_state({'sync_allowed': True, 'plan': 'pro'})
    sync._update_trial_state({'sync_allowed': True, 'plan': 'pro'})
    sync._update_trial_state({'sync_allowed': True, 'plan': 'pro'})
    resume_logs = [r for r in caplog.records if 'sync resumed' in r.getMessage()]
    assert len(resume_logs) == 0


# ── 429 handling: server-side throttle confirms client cache ──────────────

def test_post_429_marks_sync_paused(sync, monkeypatch):
    """When server returns 429, the client should immediately update its
    cache so subsequent uploads short-circuit before the network round-trip."""
    err = urllib.error.HTTPError(
        url='https://app.clawmetry.com/api/ingest/events', code=429,
        msg='Too Many', hdrs={},
        fp=io.BytesIO(json.dumps({
            'error': 'rate_limit_exceeded', 'plan': 'trial_expired',
            'retry_after': 30,
        }).encode()),
    )
    fake_urlopen_calls = []
    def fake_urlopen(req, timeout=None):
        fake_urlopen_calls.append(req.full_url)
        raise err
    monkeypatch.setattr(sync.urllib.request, 'urlopen', fake_urlopen)
    monkeypatch.setattr(sync.time, 'sleep', lambda *a, **kw: None)
    with pytest.raises(RuntimeError, match='HTTP 429'):
        sync._post('/ingest/events', {'node_id': 'n'}, 'cm_x')
    assert sync._TRIAL_STATE['sync_allowed'] is False
    assert sync._TRIAL_STATE['plan'] == 'trial_expired'


# ── Sync entry points bail early ──────────────────────────────────────────

def test_sync_sessions_bails_when_paused(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    spy = []
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: spy.append(a) or {})
    n = sync.sync_sessions(
        {'api_key': 'cm_x', 'node_id': 'n'},
        {},
        {'sessions_dir': '/tmp/nope'},
    )
    assert n == 0
    assert spy == [], 'sync_sessions must NOT make any POSTs when paused'

def test_sync_logs_bails_when_paused(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False})
    spy = []
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: spy.append(a) or {})
    n = sync.sync_logs(
        {'api_key': 'cm_x', 'node_id': 'n'},
        {}, {'log_dir': '/tmp/nope'},
    )
    assert n == 0 and spy == []

def test_sync_memory_bails_when_paused(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False})
    spy = []
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: spy.append(a) or {})
    n = sync.sync_memory(
        {'api_key': 'cm_x', 'node_id': 'n'},
        {}, {'workspace': '/tmp/nope'},
    )
    assert n == 0 and spy == []

def test_sync_crons_bails_when_paused(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False})
    spy = []
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: spy.append(a) or {})
    n = sync.sync_crons(
        {'api_key': 'cm_x', 'node_id': 'n'},
        {}, {},
    )
    assert n == 0 and spy == []

def test_sync_system_snapshot_bails_when_paused(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False})
    spy = []
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: spy.append(a) or {})
    n = sync.sync_system_snapshot(
        {'api_key': 'cm_x', 'node_id': 'n'},
        {}, {},
    )
    assert n == 0 and spy == []


# ── Sync resumes on flip to pro ──────────────────────────────────────────

def test_sync_resumes_when_plan_flips_back(sync, monkeypatch):
    sync._update_trial_state({'sync_allowed': False, 'plan': 'trial_expired'})
    assert sync._sync_allowed() is False
    # Heartbeat returns pro on next beat -> _update_trial_state flips it.
    sync._update_trial_state({'sync_allowed': True, 'plan': 'pro'})
    assert sync._sync_allowed() is True
