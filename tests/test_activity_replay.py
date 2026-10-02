"""Committed live activity.

AC-OBS-INV-004.1: committed positions replay late inserts and payload updates.

AC-OBS-INV-004.2: quiet/ended sessions are not inferred from missing rows.
"""
import pytest

from tests import test_incident_lifecycle as lifecycle

store = lifecycle.store
server = lifecycle.server

SCOPE = {'node_id': 'node-a', 'runtime': 'codex', 'session_id': 'codex:session'}


def add(store, id, ts='2026-10-02T10:00:00Z', **kwargs):
    row = {'id': id, 'node_id': 'node-a', 'agent_type': 'codex', 'session_id': 'codex:session',
               'event_type': 'tool_result', 'ts': ts, 'data': {'text': id}}
    row.update(kwargs)
    store.ingest(row)
    store._flush_now()
    return row


def read(store, **kwargs):
    return store.query_activity(**dict(SCOPE, **kwargs))


def test_late_event_and_clock_reversal_are_replayed_by_committed_position(store, monkeypatch):
    add(store, 'first')
    start = read(store)
    assert [e['id'] for e in start['rows']] == ['first']
    # Both event time and ingestion wall time can be earlier after clock correction.
    from clawmetry import local_store
    with monkeypatch.context() as patch:
        patch.setattr(local_store.time, 'time', lambda: 1000)
        add(store, 'late', '2020-01-01T00:00:00Z')
    result = read(store, cursor=start['cursor'])
    assert [e['id'] for e in result['rows']] == ['late']
    assert not result['resync_required']
    assert read(store, cursor=result['cursor'])['rows'] == []


def test_restart_replay_and_duplicate_ingest_do_not_repeat(store):
    row = add(store, 'first')
    cursor = read(store)['cursor']
    store.ingest(row)
    store._flush_now()
    assert read(store, cursor=cursor)['rows'] == []
    store.stop(flush=True)
    from clawmetry.local_store import LocalStore
    reopened = LocalStore()
    try:
        add(reopened, 'second')
        assert [e['id'] for e in read(reopened, cursor=cursor)['rows']] == ['second']
    finally:
        reopened.stop(flush=True)


def test_payload_replacement_is_a_new_committed_upsert(store):
    row = add(store, 'first')
    cursor = read(store)['cursor']
    from clawmetry.otlp_sources import replace_payload
    row['data'] = {'text': 'completed payload'}
    assert replace_payload(store, row)
    page = read(store, cursor=cursor)
    assert len(page['rows']) == 1
    assert page['rows'][0]['id'] == 'first'
    assert page['rows'][0]['data']['text'] == 'completed payload'


def test_failed_transaction_never_exposes_a_position(store):
    cursor = read(store)['cursor']
    from clawmetry.local_store import _txn
    with pytest.raises(RuntimeError), store._write_lock, _txn(store._conn):
        store._conn.execute("INSERT INTO events(id,node_id,agent_type,session_id,event_type,ts,data,created_at) VALUES ('uncommitted','node-a','codex','codex:session','tool_result','now','{}',1)")
        store._record_event_changes_locked(['uncommitted'])
        raise RuntimeError('rollback')
    assert read(store, cursor=cursor)['rows'] == []
    add(store, 'committed')
    assert [e['id'] for e in read(store, cursor=cursor)['rows']] == ['committed']


def test_scope_applies_before_page_limit_and_cursor_is_scope_bound(store):
    cursor = read(store)['cursor']
    for i in range(6):
        add(store, 'other-' + str(i), node_id='other')
    for i in range(5):
        add(store, str(i))
    found = []
    for _ in range(5):
        page = read(store, cursor=cursor, limit=2)
        found.extend(e['id'] for e in page['rows'])
        cursor = page['cursor']
        if not page['has_more']:
            break
    assert found == ['0', '1', '2', '3', '4']
    assert read(store, cursor=cursor, node_id='other')['resync_required']
    assert read(store, cursor='broken')['resync_required']


def test_expired_journal_requests_resync_and_remains_bounded(store, monkeypatch):
    from clawmetry import activity_store
    monkeypatch.setattr(activity_store, 'MAX_CHANGES', 3)
    monkeypatch.setattr(activity_store, 'PRUNE_BATCH', 1)
    cursor = read(store)['cursor']
    for i in range(9):
        add(store, str(i))
    result = read(store, cursor=cursor)
    assert result['resync_required'] and result['rows'] == []
    assert store._fetch('SELECT count(*) FROM event_changes', [])[0][0] <= 3
    fresh = read(store, limit=2)
    assert len(fresh['rows']) == 2 and fresh['coverage']['preview_limited']


def test_retention_deletion_invalidates_live_cursors(store):
    add(store, 'retained')
    cursor = read(store)['cursor']
    store.delete_events_by_type('tool_result')
    result = read(store, cursor=cursor)
    assert result['resync_required'] and result['rows'] == []


def test_bootstrap_captures_position_before_reading_rows(store, monkeypatch):
    add(store, 'first')
    fetch = store._fetch
    inserted = []
    def racing(sql, args):
        if 'FROM events' in sql and not inserted:
            inserted.append(add(store, 'racing'))
        return fetch(sql, args)
    monkeypatch.setattr(store, '_fetch', racing)
    initial = read(store)
    delta = read(store, cursor=initial['cursor'])
    assert 'racing' in {e['id'] for e in initial['rows'] + delta['rows']}
    assert 'racing' in {e['id'] for e in delta['rows']}


def test_quiet_activity_reports_execution_and_finding_state_independently(store):
    import time
    now = time.time() * 1000
    episode = lifecycle.observe(store, lifecycle.finding(at=now), now=now)
    store.ingest_session({'session_id': SCOPE['session_id'], 'node_id': SCOPE['node_id'],
                          'agent_type': 'codex', 'status': 'active',
                          'ended_at': '2026-10-02T10:01:00Z'})
    first = read(store)
    assert first['rows'] == []
    assert first['execution']['status'] == 'ended'
    assert first['incidents'][0]['state'] == 'active'
    store.recover_incident(incident_id=episode['incident_id'], observed_at=now + 1,
                           recovery_ref={'event_id': 'success', 'ts': now + 1, 'reason': 'tool_succeeded'})
    second = read(store, cursor=first['cursor'])
    assert second['rows'] == []
    assert second['incidents'][0]['state'] == 'recovered'
    assert second['execution']['status'] == 'ended'
