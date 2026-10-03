"""Durable Guard episodes, owned by the daemon's existing DuckDB writer.

Only the two trajectory kinds with a positive recovery contract migrate here.
``loop_signals`` is their compatibility projection, written in the same
transaction. Policy/action and notification cooldown latches are untouched.
Reads raise on storage failure: an unavailable investigation is not an empty one.
"""
from __future__ import annotations

import json
import logging
import math
import time
import uuid
from datetime import datetime, timezone

log = logging.getLogger("clawmetry.incidents")

LIFECYCLE_KINDS = frozenset({"stuck_loop", "repeated_tool_failure"})
STALE_AFTER_MS = 30 * 60 * 1000
MAX_EVIDENCE_REFS = 64
INCIDENT_DDL = [
    """CREATE TABLE IF NOT EXISTS incident_episodes (
        incident_id VARCHAR PRIMARY KEY,
        node_id VARCHAR NOT NULL,
        runtime VARCHAR NOT NULL,
        session_id VARCHAR NOT NULL,
        kind VARCHAR NOT NULL,
        state VARCHAR NOT NULL,
        first_seen BIGINT NOT NULL,
        last_seen BIGINT NOT NULL,
        updated_at BIGINT NOT NULL,
        last_evidence_at BIGINT,
        recovered_at BIGINT,
        acknowledged_at BIGINT,
        evidence_refs VARCHAR NOT NULL,
        recovery_ref VARCHAR,
        details VARCHAR NOT NULL
    )""",
    """CREATE INDEX IF NOT EXISTS idx_incident_scope
        ON incident_episodes(session_id, runtime, node_id)""",
    """CREATE TABLE IF NOT EXISTS incident_heads (
        node_id VARCHAR NOT NULL,
        runtime VARCHAR NOT NULL,
        session_id VARCHAR NOT NULL,
        kind VARCHAR NOT NULL,
        incident_id VARCHAR NOT NULL,
        PRIMARY KEY (node_id, runtime, session_id, kind)
    )""",
    """CREATE TABLE IF NOT EXISTS incident_ack_requests (
        incident_id VARCHAR PRIMARY KEY,
        requested_at BIGINT NOT NULL
    )""",
]

_COLS = ("incident_id", "node_id", "runtime", "session_id", "kind", "state",
         "first_seen", "last_seen", "updated_at", "last_evidence_at",
         "recovered_at", "acknowledged_at", "evidence_refs", "recovery_ref", "details")
_SELECT = ", ".join(_COLS)
_DETAIL_KEYS = ("title", "detail", "severity", "evidence", "spend_at_risk_usd",
                "spend_basis", "burn_rate_usd_per_min", "frameworks", "observation",
                "delivered_via")


def epoch_ms(value):
    """Unambiguous UTC milliseconds, or None for missing/invalid source time."""
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            num = dt.timestamp() * 1000
        except (TypeError, ValueError, OverflowError, OSError):
            return None
    else:
        if num < 100_000_000_000:
            num *= 1000
    if not math.isfinite(num) or not 0 < num < 253_402_300_800_000:
        return None
    return int(num)


def clean_refs(refs):
    """Copy only identifiers and time. Never persist a raw tool payload here."""
    out = []
    seen = set()
    for ref in refs if isinstance(refs, (list, tuple)) else ():
        if not isinstance(ref, dict):
            continue
        event_id = ref.get("event_id")
        if not isinstance(event_id, str) or not event_id or len(event_id) > 1024:
            continue
        call = ref.get("tool_call_id")
        key = (event_id, call if isinstance(call, str) else "")
        if key in seen:
            continue
        seen.add(key)
        item = {"event_id": event_id, "ts": epoch_ms(ref.get("ts"))}
        for field in ("tool_call_id", "span_id", "trace_id"):
            val = ref.get(field)
            if isinstance(val, str) and val and len(val) <= 1024:
                item[field] = val
        out.append(item)
    # Retain the episode's first evidence even after many moving windows.
    return out if len(out) <= MAX_EVIDENCE_REFS else out[:8] + out[-56:]


def _row(row):
    if not row:
        return None
    result = dict(zip(_COLS, row))
    for field in ("details", "evidence_refs", "recovery_ref"):
        result[field] = json.loads(result[field]) if result[field] else None
    details = result.pop("details") or {}
    result.update({key: details.get(key) for key in _DETAIL_KEYS})
    result["schema_version"] = 1
    result["cost_provenance"] = (
        "unknown" if result.get("spend_basis") in (None, "", "unknown") else "estimated")
    if result["cost_provenance"] == "unknown":
        result["spend_at_risk_usd"] = None
    return result


def _safe_details(incident):
    from clawmetry.redaction import scrub_payload
    details, _ = scrub_payload({k: incident.get(k) for k in _DETAIL_KEYS})
    if not isinstance(details, dict):
        details = {"title": "Finding details unavailable", "severity": "warning"}
    encoded = json.dumps(details, allow_nan=False, separators=(",", ":"))
    if len(encoded) > 32_768:
        raise ValueError("incident details exceed the bounded record size")
    return encoded


class IncidentStoreMixin:
    """Requires LocalStore's connection, write lock, fetch and read-only flag."""

    def _prune_incidents_locked(self, cutoff_ms):
        """The event-retention transaction also removes old finding metadata.

        Acknowledgement does not extend retention. Delete only heads pointing
        to expired episodes so a more recent recurrence remains intact.
        """
        self._conn.execute(
            "DELETE FROM incident_heads WHERE incident_id IN "
            "(SELECT incident_id FROM incident_episodes WHERE last_seen < ?)", [cutoff_ms])
        self._conn.execute(
            "DELETE FROM incident_ack_requests WHERE incident_id IN "
            "(SELECT incident_id FROM incident_episodes WHERE last_seen < ?)", [cutoff_ms])
        self._conn.execute("DELETE FROM incident_episodes WHERE last_seen < ?", [cutoff_ms])

    def record_incident_observation(self, *, incident, node_id, observed_at=None):
        """Idempotently observe an episode. Invalid input is logged and dropped."""
        if self._read_only:
            raise RuntimeError("cannot record an incident on a read-only store")
        try:
            if not isinstance(incident, dict) or incident.get("kind") not in LIFECYCLE_KINDS:
                raise ValueError("unknown lifecycle kind")
            scope = [node_id, incident.get("runtime"), incident.get("session_id"),
                     incident["kind"]]
            if any(not isinstance(v, str) or not v or len(v) > 1024 for v in scope):
                raise ValueError("incident requires exact node, runtime and session identity")
            refs = clean_refs(incident.get("evidence_refs"))
            if not refs:
                raise ValueError("incident requires stored evidence references")
            details = _safe_details(incident)
            now = epoch_ms(observed_at) if observed_at is not None else int(time.time() * 1000)
            if now is None:
                raise ValueError("invalid observation time")
        except (TypeError, ValueError) as exc:
            log.warning("Incident observation ignored: %s", exc)
            return None
        from clawmetry.local_store import _txn
        latest = max((r["ts"] for r in refs if r["ts"] is not None), default=None)
        with self._write_lock, _txn(self._conn):
            head = self._conn.execute(
                "SELECT incident_id FROM incident_heads WHERE node_id=? AND runtime=? "
                "AND session_id=? AND kind=?", scope).fetchone()
            old_raw = self._conn.execute(
                f"SELECT {_SELECT} FROM incident_episodes WHERE incident_id=?",
                [head[0]]).fetchone() if head else None
            old = _row(old_raw)
            if old and old["state"] == "recovered":
                recovery_at = (old.get("recovery_ref") or {}).get("ts")
                if latest is None or recovery_at is None or latest <= recovery_at:
                    return old  # replay of the same pre-recovery detector window
                old = None
            incident_id = old["incident_id"] if old else "inc_" + uuid.uuid4().hex
            if old and "delivered_via" not in incident:
                saved_details = json.loads(details)
                saved_details["delivered_via"] = old.get("delivered_via")
                details = json.dumps(saved_details, separators=(",", ":"))
            refs = clean_refs((old["evidence_refs"] if old else []) + refs)
            latest = max(latest or 0, (old or {}).get("last_evidence_at") or 0) or None
            state = "active" if latest is not None and now - latest < STALE_AFTER_MS else "stale"
            if (old and state == old["state"] and refs == old["evidence_refs"]
                    and json.loads(details) == json.loads(old_raw[-1])):
                return old  # polling the same evidence is not another observation
            first = old["first_seen"] if old else now
            last = max(now, old["last_seen"]) if old else now
            self._conn.execute(
                "INSERT INTO incident_episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "NULL, ?, ?, NULL, ?) ON CONFLICT (incident_id) DO UPDATE SET "
                "state=excluded.state, last_seen=excluded.last_seen, updated_at=excluded.updated_at, "
                "last_evidence_at=excluded.last_evidence_at, evidence_refs=excluded.evidence_refs, "
                "details=excluded.details",
                [incident_id, *scope, state, first, last, last, latest,
                 (old or {}).get("acknowledged_at"), json.dumps(refs), details])
            self._conn.execute(
                "INSERT INTO incident_heads VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (node_id,runtime,session_id,kind) DO UPDATE SET "
                "incident_id=excluded.incident_id", [*scope, incident_id])
            result = _row(self._conn.execute(
                f"SELECT {_SELECT} FROM incident_episodes WHERE incident_id=?",
                [incident_id]).fetchone())
            self._project_incident_locked(result)
            return result

    def _project_incident_locked(self, incident):
        """Compatibility only. Caller holds the writer lock and transaction."""
        from clawmetry import ccr
        sid, kind = incident["session_id"], incident["kind"]
        signature = "daemon_detect_" + kind
        if incident["state"] != "active":
            row = self._conn.execute(
                "SELECT details FROM loop_signals WHERE session_id=? AND signature=?",
                [sid, signature]).fetchone()
            try:
                detail = json.loads(ccr.maybe_decompress(row[0])) if row and row[0] else {}
            except (TypeError, ValueError):
                detail = {}
            if detail.get("incident_id") == incident["incident_id"]:
                self._conn.execute("DELETE FROM loop_signals WHERE session_id=? AND signature=?",
                                   [sid, signature])
            return
        detail = {k: incident.get(k) for k in _DETAIL_KEYS}
        detail.update({"source": "daemon_detector", "kind": kind,
                       "message": incident.get("title"),
                       "incident_id": incident["incident_id"], "node_id": incident["node_id"],
                       "evidence_refs": incident["evidence_refs"], "state": "active"})
        # loop_signals uses local wall time, unlike the UTC epoch episode table.
        first = datetime.fromtimestamp(incident["first_seen"] / 1000, timezone.utc).astimezone().replace(tzinfo=None).isoformat()
        last = datetime.fromtimestamp(incident["last_seen"] / 1000, timezone.utc).astimezone().replace(tzinfo=None).isoformat()
        severity = incident.get("severity") or "warning"
        count = {"info": 3, "warning": 5, "critical": 10}.get(severity, 5)
        self._conn.execute(
            "INSERT INTO loop_signals VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (session_id,signature) DO UPDATE SET repeat_count=excluded.repeat_count, "
            "first_seen=excluded.first_seen, last_seen=excluded.last_seen, "
            "severity=excluded.severity, agent_type=excluded.agent_type, details=excluded.details",
            [sid, signature, count, first, last, severity, incident["runtime"],
             json.dumps(detail).encode("utf-8")])

    def recover_incident(self, *, incident_id, recovery_ref, observed_at=None):
        """Close only with positive later evidence, supplied by the daemon pass."""
        if self._read_only:
            raise RuntimeError("cannot recover an incident on a read-only store")
        refs = clean_refs([recovery_ref])
        reason = recovery_ref.get("reason") if isinstance(recovery_ref, dict) else None
        if not refs or reason not in ("tool_succeeded", "progress_observed"):
            return None
        proof = dict(refs[0], reason=reason)
        now = epoch_ms(observed_at) if observed_at is not None else int(time.time() * 1000)
        if now is None:
            return None
        from clawmetry.local_store import _txn
        with self._write_lock, _txn(self._conn):
            old = _row(self._conn.execute(
                f"SELECT {_SELECT} FROM incident_episodes WHERE incident_id=?",
                [incident_id]).fetchone())
            if not old or old["state"] == "recovered":
                return old
            if (proof["ts"] is None or old["last_evidence_at"] is None
                    or proof["ts"] <= old["last_evidence_at"]):
                return old
            self._conn.execute(
                "UPDATE incident_episodes SET state='recovered', recovered_at=?, "
                "recovery_ref=?, updated_at=? WHERE incident_id=?",
                [now, json.dumps(proof), now, incident_id])
            old.update(state="recovered", recovered_at=now, recovery_ref=proof, updated_at=now)
            self._project_incident_locked(old)
            return old

    def age_incidents(self, *, observed_at=None):
        """Silence is uncertainty, never recovery. Called once per daemon pass."""
        if self._read_only:
            raise RuntimeError("cannot age incidents on a read-only store")
        now = epoch_ms(observed_at) if observed_at is not None else int(time.time() * 1000)
        if now is None:
            return 0
        from clawmetry.local_store import _txn
        with self._write_lock, _txn(self._conn):
            rows = self._conn.execute(
                f"SELECT {_SELECT} FROM incident_episodes WHERE state='active' "
                "AND (last_evidence_at IS NULL OR last_evidence_at <= ?)",
                [now - STALE_AFTER_MS]).fetchall()
            for row in rows:
                incident = _row(row)
                incident.update(state="stale", updated_at=now)
                self._conn.execute("UPDATE incident_episodes SET state='stale', updated_at=? "
                                   "WHERE incident_id=?", [now, incident["incident_id"]])
                self._project_incident_locked(incident)
            return len(rows)

    def acknowledge_incident(self, *, incident_id, acknowledged=True, observed_at=None,
                             requested_at_ms=None):
        """Operator acknowledgement has no effect on recovery or controls."""
        if self._read_only:
            raise RuntimeError("cannot acknowledge an incident on a read-only store")
        if not isinstance(acknowledged, bool):
            raise TypeError("acknowledged must be a boolean")
        now = epoch_ms(observed_at) if observed_at is not None else int(time.time() * 1000)
        requested = epoch_ms(requested_at_ms) if requested_at_ms is not None else now
        if now is None or requested is None:
            raise ValueError("invalid acknowledgement time")
        from clawmetry.local_store import _txn
        with self._write_lock, _txn(self._conn):
            old = _row(self._conn.execute(
                f"SELECT {_SELECT} FROM incident_episodes WHERE incident_id=?", [incident_id]).fetchone())
            if not old:
                return None
            watermark = self._conn.execute(
                "SELECT requested_at FROM incident_ack_requests WHERE incident_id=?", [incident_id]).fetchone()
            if watermark and requested <= watermark[0]:
                return old
            self._conn.execute("UPDATE incident_episodes SET acknowledged_at=?, updated_at=? "
                               "WHERE incident_id=?", [now if acknowledged else None, now, incident_id])
            self._conn.execute("INSERT INTO incident_ack_requests VALUES (?, ?) "
                               "ON CONFLICT (incident_id) DO UPDATE SET requested_at=excluded.requested_at",
                               [incident_id, requested])
        rows = self.query_incidents(incident_id=incident_id, limit=1)
        return rows[0] if rows else None

    def query_incidents(self, *, runtime=None, node_id=None, session_id=None,
                        state=None, incident_id=None, limit=100):
        """Bounded exact-scope reads. A missing filter never becomes a wildcard."""
        clauses, args = [], []
        for key, val in (("runtime", runtime), ("node_id", node_id),
                         ("session_id", session_id), ("state", state),
                         ("incident_id", incident_id)):
            if val not in (None, ""):
                clauses.append(key + " = ?")
                args.append(str(val))
        try:
            lim = max(1, min(int(limit), 500))
        except (ValueError, TypeError):
            lim = 100
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        return [_row(r) for r in self._fetch(
            f"SELECT {_SELECT} FROM incident_episodes{where} "
            "ORDER BY updated_at DESC, incident_id DESC LIMIT ?", args + [lim])]

    def query_incident_heads(self, *, session_id=None, runtime=None, node_id=None, limit=600):
        """Only open episodes, including stale ones, for bounded reconciliation."""
        clauses = ["state <> 'recovered'"]
        args = []
        for key, val in (("session_id", session_id), ("runtime", runtime), ("node_id", node_id)):
            if val:
                clauses.append("i." + key + " = ?")
                args.append(str(val))
        return [_row(r) for r in self._fetch(
            "SELECT " + ", ".join("i." + k for k in _COLS) +
            " FROM incident_heads h JOIN incident_episodes i USING (incident_id) WHERE " +
            " AND ".join(clauses) + " ORDER BY i.updated_at DESC LIMIT ?",
            args + [max(1, min(int(limit), 1000))])]

    def query_incident_window(self, *, session_id, node_id, runtime, limit=200):
        """An exact session/node window with runtime checked before the limit."""
        from clawmetry.local_store import (
            _EVENT_COLS,
            _NON_OPENCLAW_RUNTIME_PREFIXES,
            _row_to_event,
        )
        prefixes = sorted(_NON_OPENCLAW_RUNTIME_PREFIXES)
        marks = ",".join("?" for _ in prefixes)
        runtime_expr = (f"CASE WHEN split_part(session_id, ':', 1) IN ({marks}) "
                        "THEN split_part(session_id, ':', 1) "
                        "WHEN agent_type IN ('main','subagent','cron','') THEN 'openclaw' "
                        "ELSE agent_type END")
        return [_row_to_event(r, _EVENT_COLS) for r in self._fetch(
            "SELECT " + ",".join(_EVENT_COLS) + " FROM events "
            f"WHERE session_id=? AND node_id=? AND ({runtime_expr})=? "
            "ORDER BY ts DESC, id DESC LIMIT ?",
            [session_id, node_id, *prefixes, runtime, max(1, min(int(limit), 200))])]
