"""Indexed exact-scope reads for the daemon's incremental security service."""
from __future__ import annotations

import json
import logging
import time

log = logging.getLogger(__name__)
SECURITY_INGEST_DDL = [
    """CREATE TABLE IF NOT EXISTS security_notifications (
        incident_id VARCHAR PRIMARY KEY, revision VARCHAR NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0, next_try BIGINT NOT NULL DEFAULT 0,
        policy_id VARCHAR NOT NULL DEFAULT '')""",
]


class SecurityIngestStoreMixin:
    def query_security_settings(self):
        # Strict read: unavailable settings cannot silently become a new cursor.
        return {str(k): str(v) for k, v in self._fetch(
            "SELECT key,value FROM node_settings WHERE key LIKE 'guard.%'", [])}

    @staticmethod
    def _security_runtime_clause():
        from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES
        prefixes = sorted(_NON_OPENCLAW_RUNTIME_PREFIXES)
        marks = ",".join("?" for _ in prefixes)
        expr = (f"CASE WHEN split_part(session_id, ':', 1) IN ({marks}) "
                "THEN split_part(session_id, ':', 1) "
                "WHEN agent_type IN ('main','subagent','cron','') THEN 'openclaw' "
                "ELSE agent_type END")
        return expr, prefixes

    def query_security_changes(self, *, position=None, epoch=None, limit=128, bootstrap_after=0):
        from clawmetry.local_store import _EVENT_COLS, _row_to_event
        current_epoch, head, floor = self._fetch(
            "SELECT epoch,head,floor FROM event_change_head WHERE singleton=1", [])[0]
        gap = epoch is not None and (epoch != current_epoch or position < floor)
        if position is None:
            # Start at retained committed history, independent of every wall
            # clock. Drain is bounded, and a pre-existing floor is a gap.
            position = floor
            gap = floor > 0
        elif gap:
            position = floor
        if type(position) is not int or not floor <= position <= head:
            raise ValueError("Security journal position is unavailable")
        cols = _EVENT_COLS + ["created_at"]
        rows = self._fetch(
            "SELECT c.position," + ",".join("e." + c for c in cols) +
            " FROM event_changes c LEFT JOIN events e ON e.id=c.event_id "
            "WHERE c.position>? AND c.position<=? ORDER BY c.position LIMIT ?",
            [position, head, max(1, min(128, int(limit)))])
        result = []
        for item in rows:
            row = _row_to_event(item[1:], cols) if item[1] is not None else {}
            row["position"] = item[0]
            result.append(row)
        after_epoch, after_floor = self._fetch(
            "SELECT epoch,floor FROM event_change_head WHERE singleton=1", [])[0]
        if after_epoch != current_epoch or position < after_floor:
            raise RuntimeError("Security journal changed during inspection")
        return dict(rows=result, epoch=current_epoch, head=head, floor=floor, history_gap=gap,
                    position=rows[-1][0] if rows else position)

    def query_security_window(self, *, session_id, node_id, runtime, position, limit=200):
        from clawmetry.local_store import _EVENT_COLS, _row_to_event
        cols = _EVENT_COLS + ["created_at"]
        expr, prefixes = self._security_runtime_clause()
        where = " AND ".join(("session_id=?", "node_id=?", f"({expr})=?"))
        # The journal's position is independent of timestamps. DISTINCT
        # removes repeated payload-update receipts for the same stored event.
        ids = self._fetch(
            "SELECT event_id,MAX(position) AS last_position FROM event_changes "
            f"WHERE {where} AND position<=? GROUP BY event_id "
            "ORDER BY last_position DESC LIMIT ?",
            [session_id, node_id, *prefixes, runtime, position, max(1, min(200, int(limit)))])
        if not ids:
            return []
        marks = ",".join("?" for _ in ids)
        rows = self._fetch("SELECT " + ",".join(cols) + f" FROM events WHERE id IN ({marks})",
                           [entry[0] for entry in ids])
        by_id = {row[0]: _row_to_event(row, cols) for row in rows}
        from clawmetry.incident_store import epoch_ms
        # Discovery order is not action order: the journal sorts IDs inside
        # a transaction. Detectors receive the store's newest-source-first
        # contract, with journal position used only as a stable time tie.
        positions = dict(ids)
        return sorted(by_id.values(), key=lambda row: (
            epoch_ms(row.get("ts")) or 0, positions[row["id"]]), reverse=True)

    def query_security_session(self, *, session_id, node_id, runtime):
        cols = ("session_id", "node_id", "agent_type", "agent_id", "cwd", "metadata",
                "status", "ended_at", "started_at", "last_active_at", "cost_usd")
        expr, prefixes = self._security_runtime_clause()
        rows = self._fetch("SELECT " + ",".join(cols) + " FROM sessions "
                           f"WHERE session_id=? AND node_id=? AND ({expr})=? LIMIT 1",
                           [session_id, node_id, *prefixes, runtime])
        if not rows:
            return None
        result = dict(zip(cols, rows[0]))
        from clawmetry.local_store import _from_blob
        meta = _from_blob(result.get("metadata"))
        if isinstance(meta, bytes):
            meta = meta.decode("utf-8", "replace")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (TypeError, ValueError):
                log.warning("Security session metadata is malformed; optional context is unavailable")
                meta = {}
        result["metadata"] = meta if isinstance(meta, dict) else {}
        return result

    def enqueue_security_notification(self, *, incident, policy_id=""):
        from hashlib import sha256
        body = json.dumps([incident.get("severity"), incident.get("evidence_refs")],
                          sort_keys=True, separators=(",", ":"))
        revision = sha256(body.encode()).hexdigest()
        with self._write_lock:
            self._conn.execute(
                "INSERT INTO security_notifications(incident_id,revision,next_try,policy_id) VALUES (?,?,0,?) "
                "ON CONFLICT(incident_id) DO UPDATE SET revision=excluded.revision,next_try=0,attempts=0,"
                "policy_id=excluded.policy_id WHERE security_notifications.revision<>excluded.revision",
                [incident["incident_id"], revision, str(policy_id)])
        return {"delivered": False, "delivered_via": [], "reason": "Security notification queued"}

    def drain_security_notifications(self, *, deliver, limit=4, now=None):
        now_ms = int((time.time() if now is None else now) * 1000)
        # Orphan rows can only follow configured evidence retention.
        with self._write_lock:
            self._conn.execute("DELETE FROM security_notifications WHERE incident_id NOT IN "
                               "(SELECT incident_id FROM incident_episodes)")
        rows = self._fetch("SELECT incident_id,revision,attempts,policy_id FROM security_notifications "
                           "WHERE next_try<=? ORDER BY next_try,incident_id LIMIT ?",
                           [now_ms, max(1, min(10, int(limit)))])
        for iid, revision, attempts, policy_id in rows:
            values = self.query_incidents(incident_id=iid, limit=1)
            if not values:
                continue
            result = deliver(values[0], policy_id)
            reason = str((result or {}).get("reason") or "")
            retry = not isinstance(result, dict) or reason.startswith(("no channel", "alert failed"))
            with self._write_lock:
                if retry:
                    delay = min(3_600_000, 10_000 * (2 ** min(8, int(attempts))))
                    self._conn.execute("UPDATE security_notifications SET attempts=attempts+1,next_try=? "
                                       "WHERE incident_id=? AND revision=?", [now_ms + delay, iid, revision])
                else:
                    self._conn.execute("DELETE FROM security_notifications WHERE incident_id=? AND revision=?",
                                       [iid, revision])
        return len(rows)

    def commit_security_progress(self, *, cursor, status, history_gap=False):
        from clawmetry.local_store import _txn
        values = [("guard.security.cursor", cursor),
                  ("guard.security.status", json.dumps(status, separators=(",", ":")))]
        if history_gap:
            values.append(("guard.security.history_gap", "true"))
        with self._write_lock, _txn(self._conn):
            self._conn.executemany(
                "INSERT INTO node_settings(key,value,updated_at) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                [(key, value, int(time.time() * 1000)) for key, value in values])
