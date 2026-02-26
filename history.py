"""
ClawMetry History - Time-series data collection and storage.

Collects snapshots from the OpenClaw gateway every 60s and stores them
in a local SQLite database for historical analysis.

Database: ~/.clawmetry/history.db (configurable via CLAWMETRY_HISTORY_DB)
"""

import os
import json
import time
import sqlite3
import threading
from datetime import datetime

__all__ = ['HistoryDB', 'HistoryCollector']

DEFAULT_DB_PATH = os.path.expanduser('~/.clawmetry/history.db')
POLL_INTERVAL = 60  # seconds
RETENTION_DAYS = 90
ROLLUP_AFTER_DAYS = 7  # aggregate into hourly after 7 days


class HistoryDB:
    """SQLite-backed time-series store for ClawMetry."""

    def __init__(self, db_path=None):
        self.db_path = db_path or os.environ.get('CLAWMETRY_HISTORY_DB', DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, timeout=10)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute('PRAGMA journal_mode=WAL')
            self._local.conn.execute('PRAGMA synchronous=NORMAL')
        return self._local.conn

    def _init_schema(self):
        conn = self._get_conn()
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                labels_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(timestamp);
            CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics(metric_name, timestamp);

            CREATE TABLE IF NOT EXISTS sessions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                session_key TEXT NOT NULL,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                model TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                extra_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_ts ON sessions_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_sessions_key ON sessions_log(session_key, timestamp);

            CREATE TABLE IF NOT EXISTS cron_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                job_id TEXT NOT NULL,
                job_name TEXT DEFAULT '',
                status TEXT DEFAULT 'unknown',
                duration_ms INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                extra_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_cron_ts ON cron_runs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_cron_job ON cron_runs(job_id, timestamp);

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                raw_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(timestamp);

            CREATE TABLE IF NOT EXISTS metrics_rollup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                interval TEXT NOT NULL,
                avg_value REAL,
                min_value REAL,
                max_value REAL,
                sum_value REAL,
                count INTEGER,
                labels_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_rollup_ts ON metrics_rollup(metric_name, interval, timestamp);
        ''')
        conn.commit()

    def insert_metric(self, name, value, labels=None, ts=None):
        ts = ts or time.time()
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO metrics (timestamp, metric_name, metric_value, labels_json) VALUES (?, ?, ?, ?)',
            (ts, name, value, json.dumps(labels or {}))
        )
        conn.commit()

    def insert_metrics_batch(self, rows):
        """rows: list of (ts, name, value, labels_dict)"""
        conn = self._get_conn()
        conn.executemany(
            'INSERT INTO metrics (timestamp, metric_name, metric_value, labels_json) VALUES (?, ?, ?, ?)',
            [(ts, n, v, json.dumps(l or {})) for ts, n, v, l in rows]
        )
        conn.commit()

    def insert_session(self, session_key, tokens_in, tokens_out, cost, model, status='active', ts=None, extra=None):
        ts = ts or time.time()
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO sessions_log (timestamp, session_key, tokens_in, tokens_out, cost, model, status, extra_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (ts, session_key, tokens_in, tokens_out, cost, model, status, json.dumps(extra or {}))
        )
        conn.commit()

    def insert_cron_run(self, job_id, job_name, status, duration_ms=0, error='', ts=None, extra=None):
        ts = ts or time.time()
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO cron_runs (timestamp, job_id, job_name, status, duration_ms, error, extra_json) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (ts, job_id, job_name, status, duration_ms, error, json.dumps(extra or {}))
        )
        conn.commit()

    def insert_snapshot(self, raw_data, ts=None):
        ts = ts or time.time()
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO snapshots (timestamp, raw_json) VALUES (?, ?)',
            (ts, json.dumps(raw_data) if isinstance(raw_data, dict) else raw_data)
        )
        conn.commit()

    def query_metrics(self, metric_name, from_ts, to_ts, interval=None):
        """Query metrics with optional time bucketing.
        interval: 'minute', 'hour', 'day' or None for raw data.
        """
        conn = self._get_conn()

        if interval and interval in ('minute', 'hour', 'day'):
            divisor = {'minute': 60, 'hour': 3600, 'day': 86400}[interval]
            rows = conn.execute('''
                SELECT CAST(timestamp / ? AS INTEGER) * ? as bucket_ts,
                       AVG(metric_value) as avg_val,
                       MIN(metric_value) as min_val,
                       MAX(metric_value) as max_val,
                       SUM(metric_value) as sum_val,
                       COUNT(*) as cnt
                FROM metrics
                WHERE metric_name = ? AND timestamp >= ? AND timestamp <= ?
                GROUP BY bucket_ts
                ORDER BY bucket_ts
            ''', (divisor, divisor, metric_name, from_ts, to_ts)).fetchall()
            return [dict(r) for r in rows]
        else:
            rows = conn.execute('''
                SELECT timestamp, metric_value, labels_json
                FROM metrics
                WHERE metric_name = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            ''', (metric_name, from_ts, to_ts)).fetchall()
            return [dict(r) for r in rows]

    def query_sessions(self, from_ts, to_ts, session_key=None):
        conn = self._get_conn()
        if session_key:
            rows = conn.execute('''
                SELECT * FROM sessions_log
                WHERE timestamp >= ? AND timestamp <= ? AND session_key = ?
                ORDER BY timestamp
            ''', (from_ts, to_ts, session_key)).fetchall()
        else:
            rows = conn.execute('''
                SELECT * FROM sessions_log
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            ''', (from_ts, to_ts)).fetchall()
        return [dict(r) for r in rows]

    def query_crons(self, from_ts, to_ts, job_id=None):
        conn = self._get_conn()
        if job_id:
            rows = conn.execute('''
                SELECT * FROM cron_runs
                WHERE timestamp >= ? AND timestamp <= ? AND job_id = ?
                ORDER BY timestamp
            ''', (from_ts, to_ts, job_id)).fetchall()
        else:
            rows = conn.execute('''
                SELECT * FROM cron_runs
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            ''', (from_ts, to_ts)).fetchall()
        return [dict(r) for r in rows]

    def query_snapshot(self, timestamp):
        """Get the snapshot closest to a given timestamp."""
        conn = self._get_conn()
        row = conn.execute('''
            SELECT * FROM snapshots
            ORDER BY ABS(timestamp - ?) LIMIT 1
        ''', (timestamp,)).fetchone()
        if row:
            d = dict(row)
            try:
                d['raw_json'] = json.loads(d['raw_json'])
            except (json.JSONDecodeError, TypeError):
                pass
            return d
        return None

    def get_available_metrics(self):
        """List all distinct metric names."""
        conn = self._get_conn()
        rows = conn.execute('SELECT DISTINCT metric_name FROM metrics ORDER BY metric_name').fetchall()
        return [r['metric_name'] for r in rows]

    def get_stats(self):
        """DB stats for debugging."""
        conn = self._get_conn()
        stats = {}
        for table in ['metrics', 'sessions_log', 'cron_runs', 'snapshots']:
            row = conn.execute(f'SELECT COUNT(*) as cnt, MIN(timestamp) as oldest, MAX(timestamp) as newest FROM {table}').fetchone()
            stats[table] = dict(row)
        return stats

    def cleanup(self, retention_days=None):
        """Delete data older than retention_days and create rollups."""
        retention_days = retention_days or RETENTION_DAYS
        cutoff = time.time() - (retention_days * 86400)
        rollup_cutoff = time.time() - (ROLLUP_AFTER_DAYS * 86400)
        conn = self._get_conn()

        # Create hourly rollups for data older than ROLLUP_AFTER_DAYS
        conn.execute('''
            INSERT OR IGNORE INTO metrics_rollup (timestamp, metric_name, interval, avg_value, min_value, max_value, sum_value, count, labels_json)
            SELECT CAST(timestamp / 3600 AS INTEGER) * 3600, metric_name, 'hour',
                   AVG(metric_value), MIN(metric_value), MAX(metric_value), SUM(metric_value), COUNT(*), '{}'
            FROM metrics
            WHERE timestamp < ?
            GROUP BY CAST(timestamp / 3600 AS INTEGER) * 3600, metric_name
        ''', (rollup_cutoff,))

        # Delete old raw data
        for table in ['metrics', 'sessions_log', 'cron_runs', 'snapshots']:
            conn.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff,))

        # Delete old rollups
        conn.execute('DELETE FROM metrics_rollup WHERE timestamp < ?', (cutoff,))

        conn.commit()
        conn.execute('PRAGMA optimize')


class HistoryCollector:
    """Background thread that polls the gateway and stores snapshots."""

    def __init__(self, db, gw_invoke_fn, interval=POLL_INTERVAL):
        self.db = db
        self._gw_invoke = gw_invoke_fn
        self.interval = interval
        self._stop = threading.Event()
        self._thread = None
        self._last_session_tokens = {}  # session_key -> last_total_tokens
        self._last_cron_runs = {}  # job_id -> set of run timestamps seen
        self._cleanup_counter = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name='history-collector')
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        # Initial delay to let the app start
        self._stop.wait(10)
        while not self._stop.is_set():
            try:
                self._collect()
            except Exception as e:
                print(f"[history] Collection error: {e}")
            # Periodic cleanup every ~60 cycles (1 hour)
            self._cleanup_counter += 1
            if self._cleanup_counter >= 60:
                try:
                    self.db.cleanup()
                except Exception as e:
                    print(f"[history] Cleanup error: {e}")
                self._cleanup_counter = 0
            self._stop.wait(self.interval)

    def _collect(self):
        ts = time.time()
        snapshot = {}

        # Collect sessions
        sessions_data = self._gw_invoke('sessions_list', {'limit': 100, 'messageLimit': 0})
        if sessions_data and 'sessions' in sessions_data:
            sessions = sessions_data['sessions']
            snapshot['sessions'] = sessions

            total_tokens_in = 0
            total_tokens_out = 0
            total_cost = 0
            active_count = 0

            for s in sessions:
                key = s.get('key', s.get('sessionId', 'unknown'))
                tokens_in = s.get('inputTokens', s.get('tokensIn', 0)) or 0
                tokens_out = s.get('outputTokens', s.get('tokensOut', 0)) or 0
                cost = s.get('totalCost', s.get('cost', 0)) or 0
                model = s.get('model', '')

                total_tokens_in += tokens_in
                total_tokens_out += tokens_out
                total_cost += cost

                # Check if session is active (updated in last 5 min)
                updated = s.get('updatedAt', '')
                if updated:
                    try:
                        if isinstance(updated, str):
                            ut = datetime.fromisoformat(updated.replace('Z', '+00:00')).timestamp()
                        else:
                            ut = updated / 1000 if updated > 1e12 else updated
                        if ts - ut < 300:
                            active_count += 1
                    except (ValueError, TypeError):
                        pass

                # Log session snapshot
                self.db.insert_session(key, tokens_in, tokens_out, cost, model, 'active', ts)

            # Aggregate metrics
            metrics_batch = [
                (ts, 'tokens_in_total', total_tokens_in, {}),
                (ts, 'tokens_out_total', total_tokens_out, {}),
                (ts, 'cost_total', total_cost, {}),
                (ts, 'sessions_active', active_count, {}),
                (ts, 'sessions_count', len(sessions), {}),
            ]

            # Per-model breakdown
            by_model = {}
            for s in sessions:
                m = s.get('model', 'unknown')
                if m not in by_model:
                    by_model[m] = {'tokens_in': 0, 'tokens_out': 0, 'cost': 0}
                by_model[m]['tokens_in'] += s.get('inputTokens', s.get('tokensIn', 0)) or 0
                by_model[m]['tokens_out'] += s.get('outputTokens', s.get('tokensOut', 0)) or 0
                by_model[m]['cost'] += s.get('totalCost', s.get('cost', 0)) or 0

            for model, vals in by_model.items():
                metrics_batch.append((ts, 'tokens_in_by_model', vals['tokens_in'], {'model': model}))
                metrics_batch.append((ts, 'tokens_out_by_model', vals['tokens_out'], {'model': model}))
                metrics_batch.append((ts, 'cost_by_model', vals['cost'], {'model': model}))

            self.db.insert_metrics_batch(metrics_batch)

        # Collect crons
        crons_data = self._gw_invoke('cron', {'action': 'list', 'includeDisabled': True})
        if crons_data and 'jobs' in crons_data:
            jobs = crons_data['jobs']
            snapshot['crons'] = jobs

            enabled = sum(1 for j in jobs if j.get('enabled'))
            self.db.insert_metric('crons_enabled', enabled, ts=ts)
            self.db.insert_metric('crons_total', len(jobs), ts=ts)

            # Check for recent runs
            for job in jobs:
                jid = job.get('id', '')
                jname = job.get('name', job.get('label', ''))
                last_run = job.get('lastRun', {})
                if isinstance(last_run, dict) and last_run.get('startedAt'):
                    run_ts_str = last_run.get('startedAt', '')
                    try:
                        if isinstance(run_ts_str, str):
                            run_ts = datetime.fromisoformat(run_ts_str.replace('Z', '+00:00')).timestamp()
                        else:
                            run_ts = run_ts_str / 1000 if run_ts_str > 1e12 else run_ts_str
                    except (ValueError, TypeError):
                        run_ts = 0

                    seen = self._last_cron_runs.get(jid, set())
                    if run_ts and run_ts not in seen:
                        status = last_run.get('status', 'unknown')
                        duration = last_run.get('durationMs', 0) or 0
                        error = last_run.get('error', '') or ''
                        self.db.insert_cron_run(jid, jname, status, duration, error, ts=run_ts)
                        seen.add(run_ts)
                        self._last_cron_runs[jid] = seen

        # Store full snapshot
        if snapshot:
            self.db.insert_snapshot(snapshot, ts)
