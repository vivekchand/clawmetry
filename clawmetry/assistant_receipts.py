"""Durable at-most-once Assistant work on the daemon's existing DuckDB writer.

Only complete responses are retained. Prompts, provider keys and partial journals
are never placed in receipts. All SQL uses the store's existing write lock.
"""
from __future__ import annotations

import json
import time

MAX_RECEIPTS = 256
RETENTION_SECONDS = 900


class Receipts:
    def __init__(self, store):
        if getattr(store, '_read_only', True):
            raise RuntimeError('Assistant requires the daemon writer')
        self.store = store
        with store._write_lock:
            store._conn.execute('''CREATE TABLE IF NOT EXISTS assistant_requests (
                request_id VARCHAR PRIMARY KEY, epoch VARCHAR NOT NULL,
                operation VARCHAR NOT NULL, digest VARCHAR NOT NULL,
                state VARCHAR NOT NULL, expires_at DOUBLE NOT NULL,
                result_json VARCHAR, http_status INTEGER)''')
            store._conn.execute('ALTER TABLE assistant_requests ADD COLUMN IF NOT EXISTS journal_json VARCHAR')
            # Any previous producer disappeared with its daemon. A replay must
            # not spend again even if the provider finished before the crash.
            store._conn.execute('''UPDATE assistant_requests SET state='interrupted',
                result_json=?, http_status=503 WHERE state='running' ''',
                [json.dumps({'error': 'The assistant restarted before this request completed. Start a new request.'})])

    def claim(self, request_id, epoch, operation, digest):
        now = time.time()
        with self.store._write_lock:
            conn = self.store._conn
            conn.execute("DELETE FROM assistant_requests WHERE expires_at < ? AND state != 'running'", [now])
            row = conn.execute('''SELECT epoch, operation, digest, state, result_json, http_status, journal_json
                FROM assistant_requests WHERE request_id=?''', [request_id]).fetchone()
            if row:
                if row[1] != operation or row[2] != digest:
                    raise ValueError('request identity conflict')
                return {'state': row[3], 'data': json.loads(row[4]) if row[4] else None, 'status': row[5],
                        'journal': json.loads(row[6]) if row[6] else None}
            if conn.execute('SELECT COUNT(*) FROM assistant_requests').fetchone()[0] >= MAX_RECEIPTS:
                raise OverflowError('request capacity')
            conn.execute('''INSERT INTO assistant_requests VALUES (?,?,?,?,?,?,NULL,NULL,NULL)''',
                         [request_id, epoch, operation, digest, 'running', now + RETENTION_SECONDS])
            return None

    def lookup(self, request_id, epoch, operation, digest):
        """Read an exact original request after restart; never claim new work."""
        with self.store._write_lock:
            row = self.store._conn.execute(
                """SELECT state, result_json, http_status, journal_json FROM assistant_requests
                WHERE request_id=? AND epoch=? AND operation=? AND digest=? AND expires_at>=?""",
                [request_id, epoch, operation, digest, time.time()]).fetchone()
        if not row:
            return None
        return {'state': row[0], 'data': json.loads(row[1]) if row[1] else None, 'status': row[2],
                'journal': json.loads(row[3]) if row[3] else None}

    def finish(self, request_id, outcome, check, *, journal=None):
        """Validate and atomically commit the final artifact and its receipt.

        check is an internal cancellation/lease barrier, never an RPC argument.
        Caller serializes controls against this commit using its job lock.
        """
        from clawmetry.local_store import _assistant_encode_messages
        mutation = outcome.mutation or {}
        encoded_messages = None
        if mutation.get('kind') == 'conversation':
            encoded_messages = _assistant_encode_messages(mutation['messages'])
        encoded_result = json.dumps(outcome.data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        encoded_journal = json.dumps(journal, ensure_ascii=False, separators=(',', ':'), allow_nan=False) if journal else None
        with self.store._write_lock:
            check()
            conn = self.store._conn
            conn.execute('BEGIN TRANSACTION')
            try:
                row = conn.execute('SELECT state FROM assistant_requests WHERE request_id=?', [request_id]).fetchone()
                if not row or row[0] != 'running':
                    raise RuntimeError('request already finished')
                kind = mutation.get('kind')
                if kind == 'conversation':
                    conn.execute('''INSERT INTO assistant_conversations (id,title,messages,updated_at)
                        VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,
                        messages=excluded.messages,updated_at=excluded.updated_at''',
                        [mutation['conversation_id'], mutation['title'], encoded_messages, int(time.time()*1000)])
                elif kind == 'panel_create':
                    conn.execute('''INSERT INTO custom_dashboard_panels
                        (panel_id,name,question,sql,chart_spec,created_at,updated_at) VALUES (?,?,?,?,?,?,?)''',
                        [mutation[k] for k in ('panel_id','name','question','sql','chart_spec','created_at','updated_at')])
                elif kind == 'panel_delete':
                    conn.execute('DELETE FROM custom_dashboard_panels WHERE panel_id=?', [mutation['panel_id']])
                conn.execute('''UPDATE assistant_requests SET state=?, result_json=?, http_status=?, expires_at=?, journal_json=?
                    WHERE request_id=?''', ['complete' if outcome.status < 400 else 'failed', encoded_result,
                    outcome.status, time.time()+RETENTION_SECONDS, encoded_journal, request_id])
                check()
                conn.execute('COMMIT')
            except BaseException:
                conn.execute('ROLLBACK')
                raise

    def fail(self, request_id, message, status):
        with self.store._write_lock:
            self.store._conn.execute('''UPDATE assistant_requests SET state='failed', result_json=?,
                http_status=?, expires_at=? WHERE request_id=? AND state='running' ''',
                [json.dumps({'error': message}), status, time.time()+RETENTION_SECONDS, request_id])
