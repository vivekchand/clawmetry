"""Bounded replay of committed event changes, independent of source clocks.

The journal contains identities only. The daemon writes it in the event's own
transaction; readers receive current persisted payloads as idempotent upserts.
Sequence gaps after rollback are harmless. Retention deletion invalidates the
cursor epoch so a client cannot keep displaying events the store removed.
"""
from __future__ import annotations

import time
import uuid

from clawmetry.investigations import _bounded_rows, decode_cursor, encode_cursor

MAX_CHANGES = 100_000
PRUNE_BATCH = 10_000
ACTIVITY_DDL = [
    "CREATE SEQUENCE IF NOT EXISTS event_change_position START 1",
    """CREATE TABLE IF NOT EXISTS event_changes (
        position BIGINT PRIMARY KEY DEFAULT nextval('event_change_position'),
        event_id VARCHAR NOT NULL, node_id VARCHAR, session_id VARCHAR,
        agent_type VARCHAR
    )""",
    """CREATE TABLE IF NOT EXISTS event_change_head (
        singleton INTEGER PRIMARY KEY, epoch VARCHAR NOT NULL,
        head BIGINT NOT NULL, floor BIGINT NOT NULL
    )""",
    """INSERT INTO event_change_head VALUES (1, CAST(uuid() AS VARCHAR), 0, 0)
        ON CONFLICT (singleton) DO NOTHING""",
]


def _scope(node_id=None, runtime=None, session_id=None):
    scope = {"node_id": node_id or None, "runtime": runtime or None, "session_id": session_id or None}
    for value in scope.values():
        if value is not None and (not isinstance(value, str) or len(value) > 1024):
            raise ValueError('invalid activity scope')
    return scope


def _where(scope, alias=''):
    from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES
    prefix = alias + '.' if alias else ''
    clauses, args = [], []
    for key in ('node_id', 'session_id'):
        if scope[key]:
            clauses.append(prefix + key + '=?')
            args.append(scope[key])
    if scope['runtime']:
        prefixes = sorted(_NON_OPENCLAW_RUNTIME_PREFIXES)
        marks = ','.join('?' for _ in prefixes)
        clauses.append(f"(CASE WHEN split_part({prefix}session_id, ':', 1) IN ({marks}) "
                       f"THEN split_part({prefix}session_id, ':', 1) "
                       f"WHEN {prefix}agent_type IN ('main','subagent','cron','') THEN 'openclaw' "
                       f"ELSE {prefix}agent_type END)=?")
        args.extend(prefixes + [scope['runtime']])
    return ' AND '.join(clauses) or 'TRUE', args


class ActivityStoreMixin:
    def _record_event_changes_locked(self, event_ids):
        """Caller holds the writer lock AND the source mutation transaction."""
        ids = list(dict.fromkeys(event_ids))
        if not ids:
            return
        for offset in range(0, len(ids), 200):
            chunk = ids[offset:offset + 200]
            marks = ','.join('?' for _ in chunk)
            self._conn.execute(
                'INSERT INTO event_changes(event_id,node_id,session_id,agent_type) '
                'SELECT id,node_id,session_id,agent_type FROM events '
                f'WHERE id IN ({marks}) ORDER BY id', chunk)
        self._conn.execute('UPDATE event_change_head SET head=GREATEST(head, '
                           '(SELECT COALESCE(MAX(position),0) FROM event_changes)) WHERE singleton=1')
        head, floor = self._conn.execute('SELECT head,floor FROM event_change_head WHERE singleton=1').fetchone()
        if head - floor >= MAX_CHANGES + PRUNE_BATCH:
            floor = head - MAX_CHANGES
            self._conn.execute('DELETE FROM event_changes WHERE position<=?', [floor])
            self._conn.execute('UPDATE event_change_head SET floor=? WHERE singleton=1', [floor])

    def _invalidate_activity_locked(self):
        """A deletion needs a fresh bootstrap, never a silent stale buffer."""
        self._conn.execute('DELETE FROM event_changes')
        self._conn.execute('UPDATE event_change_head SET epoch=?,floor=head WHERE singleton=1',
                           [uuid.uuid4().hex])

    def query_activity(self, *, node_id=None, runtime=None, session_id=None,
                       cursor=None, limit=100):
        from clawmetry.local_store import _EVENT_COLS, _row_to_event
        scope = _scope(node_id, runtime, session_id)
        lim = max(1, min(int(limit or 100), 200))
        # Capture BEFORE bootstrap. A commit racing the following read will be
        # replayed on the next page, even if it was already seen in the preview.
        epoch, head, floor = self._fetch('SELECT epoch,head,floor FROM event_change_head WHERE singleton=1', [])[0]
        body = {'schema_version': 1, 'scope': scope, 'rows': [], 'removed_ids': [],
                'cursor': None, 'has_more': False, 'resync_required': False,
                'coverage': {'node_reachable': True, 'preview_limited': False,
                             'payload_truncated_ids': [], 'read_at': int(time.time() * 1000)},
                'mode': 'replay' if cursor else 'bootstrap'}
        position = head
        if cursor:
            try:
                value = decode_cursor(cursor, scope, 'activity')
                if (not isinstance(value, list) or len(value) != 2 or value[0] != epoch
                        or type(value[1]) is not int or not floor <= value[1] <= head):
                    raise ValueError('position is unavailable')
                position = value[1]
            except (TypeError, ValueError):
                body.update(resync_required=True, reason='cursor_unavailable')
                return body
            where, params = _where(scope)
            changes = self._fetch('SELECT position,event_id FROM event_changes '
                                  f'WHERE position>? AND position<=? AND {where} '
                                  'ORDER BY position LIMIT ?', [position, head, *params, lim + 1])
            body['has_more'] = len(changes) > lim
            changes = changes[:lim]
            position = changes[-1][0] if body['has_more'] else head
            ids = list(dict.fromkeys(c[1] for c in changes))
            if ids:
                where, params = _where(scope)
                rows = self._fetch('SELECT ' + ','.join(_EVENT_COLS) + ' FROM events '
                                   f"WHERE {where} AND id IN ({','.join('?' for _ in ids)})", [*params, *ids])
                by_id = {r[0]: _row_to_event(r, _EVENT_COLS) for r in rows}
                body['rows'] = [by_id[eid] for eid in ids if eid in by_id]
                body['removed_ids'] = [eid for eid in ids if eid not in by_id]
        else:
            where, params = _where(scope)
            rows = self._fetch('SELECT ' + ','.join(_EVENT_COLS) + ' FROM events '
                               f'WHERE {where} ORDER BY created_at DESC,id DESC LIMIT ?', [*params, lim + 1])
            body['coverage']['preview_limited'] = len(rows) > lim
            body['rows'] = [_row_to_event(r, _EVENT_COLS) for r in reversed(rows[:lim])]
        after_epoch, after_floor = self._fetch('SELECT epoch,floor FROM event_change_head WHERE singleton=1', [])[0]
        if after_epoch != epoch or position < after_floor:
            body.update(rows=[], removed_ids=[], resync_required=True, reason='history_changed_during_read')
            return body
        body['coverage']['payload_truncated_ids'] = _bounded_rows(body['rows'])
        if all(scope.values()):
            from clawmetry.investigations import (
                current_incident,
                execution_state,
                scope_sql,
            )
            where, params = scope_sql(session_id, runtime, node_id)
            sessions = self._fetch('SELECT status,ended_at,last_active_at,outcome FROM sessions '
                                   f'WHERE {where} ORDER BY updated_at DESC LIMIT 1', params)
            body['execution'] = execution_state(sessions)
            body['incidents'] = [current_incident(row) for row in self.query_incidents(**scope, limit=20)]
        body['cursor'] = encode_cursor(scope, [epoch, position], 'activity')
        return body
