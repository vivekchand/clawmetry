"""Epoch timestamps must persist without poisoning a whole ingest batch."""
import importlib
import math
import os
import time
from datetime import datetime, timezone

import duckdb
import pytest

from clawmetry import cost_windows as cw


def _duck():
    db = duckdb.connect()
    # These tests change libc's TZ after the driver has loaded. Older ICU
    # versions cache their startup zone; align both clocks explicitly rather
    # than assuming a connection notices an in-process environment mutation.
    if os.environ.get('TZ'):
        db.execute('SET TimeZone = ?', [os.environ['TZ']])
    return db


@pytest.fixture(params=['UTC', 'America/Los_Angeles'])
def zone(request, monkeypatch):
    if not hasattr(time, 'tzset'):
        pytest.skip('Runtime timezone changes are unavailable')
    monkeypatch.setenv('TZ', request.param)
    time.tzset()
    try:
        yield
    finally:
        monkeypatch.undo()
        time.tzset()


@pytest.mark.parametrize('value', [1794060518, 1794060518.125, '1794060518',
    '1794060518.125', '1.794060518125e9', 1794060518125, '1794060518125',
    0, '0', -1, '-1', -1794060518125, '-1794060518125'])
def test_epoch_python_and_sql_use_the_same_local_day(zone, value):
    seconds = float(value)
    if abs(seconds) > 1e11:
        seconds /= 1000
    expected = datetime.fromtimestamp(seconds, timezone.utc).astimezone().date().isoformat()
    with _duck() as db:
        actual = db.execute('SELECT ' + cw.day_expr_sql('$1'), [value]).fetchone()[0]
    assert cw.local_day(value) == actual == expected


@pytest.mark.parametrize('value', ['20260824', '2026-08-24',
    '2026-08-25T02:30:00Z', '2026-08-24T19:30:00-07:00',
    '2026-08-24 19:30:00', '2026-08-24T99:99:99'])
def test_iso_calendar_contract_and_prefix_fallback_are_preserved(zone, value):
    expected = '2026-08-24'
    if value.endswith('Z') or value.endswith('-07:00'):
        expected = datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone().date().isoformat()
    with _duck() as db:
        actual = db.execute('SELECT ' + cw.day_expr_sql('$1'), [value]).fetchone()[0]
    assert cw.local_day(value) == actual == expected


@pytest.mark.parametrize('iso', ['2026-03-08T07:30:00Z', '2026-03-08T10:30:00Z',
                                '2026-11-01T08:30:00Z', '2026-11-01T09:30:00Z'])
def test_epoch_and_iso_agree_across_local_dst_changes(zone, iso):
    epoch = datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp()
    with _duck() as db:
        actual = db.execute('SELECT ' + cw.day_expr_sql('$1'), [str(epoch)]).fetchone()[0]
    assert actual == cw.local_day(epoch) == cw.local_day(iso)


@pytest.mark.parametrize('value', [None, True, False, '', 'garbage', '2026-99-99',
    math.nan, math.inf, -math.inf, 'NaN', 'Infinity', 1e100, '1e100'])
def test_bad_values_cannot_become_a_real_rollup_day(value):
    assert cw.local_day(value) is None
    with _duck() as db:
        # SQL retains its historical junk bucket, but must never throw.
        db.execute('SELECT ' + cw.day_expr_sql('$1'), [value]).fetchone()


@pytest.mark.parametrize('columns', [('ts); DROP TABLE events; --', 'id'),
    ('ts', 'id || secret'), ('e.ts', 'id'), ('ts', 'e.id')])
def test_event_dedup_sql_accepts_only_its_fixed_identifier_pairs(columns):
    import clawmetry.local_store as ls
    with pytest.raises(ValueError, match='internal event timestamp identifiers'):
        ls._event_turn_key_expr_sql(*columns)


def test_real_ingest_preserves_epoch_events_and_persistent_rollup_parity(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAWMETRY_LOCAL_STORE_PATH', str(tmp_path / 'events.duckdb'))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    values = [1794060518.125, 1794060518, '1794060518.125', 1794060518125,
              '2026-11-07T12:48:38.125Z', '20260824']
    unknown = ['not-a-date', 'NaN', 'infinity', '-infinity', '10000-01-01T00:00:00Z']
    try:
        store.ingest_many([dict(id=str(i), node_id='fixture', agent_id='main',
            agent_type='openclaw', session_id='fixture', event_type='model.completed',
            ts=value, model='fixture-model', token_count=10, cost_usd=1.)
            for i, value in enumerate(values)])
        store.ingest_many([dict(id='unknown-' + str(i), node_id='fixture', agent_id='main',
            agent_type='openclaw', session_id='unknown-clock', event_type=kind,
            ts=value, model='fixture-model', token_count=10, cost_usd=1.)
            for i, (value, kind) in enumerate((value, kind) for value in unknown
                                             for kind in ['assistant', 'model.completed'])])
        store.flush()
        count = len(values) + 2 * len(unknown)
        assert store._conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == count
        assert store.health()['ring_depth'] == 0
        model = {str(day): float(cost) for day, cost in store._conn.execute(
            'SELECT day,SUM(cost_usd) FROM rollup_model_daily GROUP BY day').fetchall()}
        runtime = {str(day): float(cost) for day, cost in store._conn.execute(
            'SELECT day,SUM(cost_usd) FROM rollup_runtime_daily GROUP BY day').fetchall()}
        assert model == runtime
        live = {row['day']: float(row['cost_usd']) for row in store.query_aggregates()}
        assert {day: cost for day, cost in live.items() if day in model} == model
        assert sum(model.values()) == len(values)
        assert sum(live.values()) == count  # Unknown clocks cannot prove duplicate turns.
        assert all(day in model or day in {value[:10] for value in unknown} for day in live)
    finally:
        store.stop(flush=True)
    reopened = ls.LocalStore()
    try:
        assert reopened._conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == count
        assert {str(day): float(cost) for day, cost in reopened._conn.execute(
            'SELECT day,SUM(cost_usd) FROM rollup_runtime_daily GROUP BY day').fetchall()} == runtime
        with ls._AGG_CACHE_LOCK:
            ls._AGG_CACHE.clear()
        assert {row['day']: float(row['cost_usd']) for row in reopened.query_aggregates()} == live
    finally:
        reopened.stop(flush=True)


def test_valid_sibling_turns_still_deduplicate_across_epoch_and_iso(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAWMETRY_LOCAL_STORE_PATH', str(tmp_path / 'siblings.duckdb'))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    try:
        store.ingest_many([dict(id=str(i), node_id='fixture', agent_id='main',
            agent_type='openclaw', session_id='siblings', event_type=kind,
            ts=stamp, token_count=10, cost_usd=2.) for i, (kind, stamp) in enumerate([
                ('assistant', '2026-11-07T12:48:38Z'),
                ('model.completed', 1794055718),
            ])])
        store.flush()
        rows = store.query_aggregates()
        assert sum(row['event_count'] for row in rows) == 2
        assert sum(float(row['cost_usd']) for row in rows) == 2.
    finally:
        store.stop(flush=True)


def test_subagent_queries_keep_unknown_clocks_and_deduplicate_known_instants(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAWMETRY_LOCAL_STORE_PATH', str(tmp_path / 'subagents.duckdb'))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    try:
        store.ingest_subagent(dict(subagent_id='child', parent_session_id='parent',
            spawned_at='2026-11-07T12:00:00Z', agent_type='openclaw', cost_usd=0., token_count=0))
        turns = [('assistant', '2026-11-07T12:48:38Z'),
                 ('model.completed', 1794055718000)]
        turns += [(kind, stamp) for stamp in ['not-a-date', 'infinity']
                  for kind in ['assistant', 'model.completed']]
        store.ingest_many([dict(id=str(i), node_id='fixture', agent_id='main',
            agent_type='openclaw', session_id='child', event_type=kind,
            ts=stamp, token_count=10, cost_usd=1.)
            for i, (kind, stamp) in enumerate(turns)])
        store.flush()
        rows = store.query_subagents(parent_session_id='parent')
        assert len(rows) == 1 and rows[0]['subagent_id'] == 'child'
        assert rows[0]['cost_usd'] == 5.
        assert rows[0]['token_count'] == 50
    finally:
        store.stop(flush=True)
