"""Scoped, bounded investigation reads shared by local and encrypted clients.

All evidence comes from the existing store. Scope is checked in SQL before
pagination; missing history, stale observations and unknown outcomes stay
explicit. This module neither tails source files nor runs detectors.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time

from clawmetry.incident_store import STALE_AFTER_MS

MAX_PAGE = 200
MAX_PAYLOAD_CHARS = 16_384


def scope_sql(session_id, runtime, node_id):
    """Return one canonical runtime predicate for events and typed sessions."""
    from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES
    for value in (session_id, runtime, node_id):
        if not isinstance(value, str) or not value or len(value) > 1024:
            raise ValueError("session_id, runtime and node_id are required")
    prefixes = sorted(_NON_OPENCLAW_RUNTIME_PREFIXES)
    marks = ",".join("?" for _ in prefixes)
    rt = (f"CASE WHEN split_part(session_id, ':', 1) IN ({marks}) "
          "THEN split_part(session_id, ':', 1) "
          "WHEN agent_type IN ('main','subagent','cron','') THEN 'openclaw' "
          "ELSE agent_type END")
    return f"session_id=? AND node_id=? AND ({rt})=?", [session_id, node_id, *prefixes, runtime]


def _scope_key(scope):
    return hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()[:24]


def encode_cursor(scope, position, kind="history"):
    raw = json.dumps({"v": 1, "scope": _scope_key(scope), "kind": kind,
                      "position": position}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor, scope, kind="history"):
    if not isinstance(cursor, str) or not cursor or len(cursor) > 4096:
        raise ValueError("invalid cursor")
    try:
        obj = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("invalid cursor") from exc
    if (not isinstance(obj, dict) or obj.get("v") != 1 or obj.get("kind") != kind
            or obj.get("scope") != _scope_key(scope)):
        raise ValueError("cursor does not match this scope")
    return obj.get("position")


def current_incident(incident, now=None):
    """Derive uncertainty even if the daemon/check has been disabled."""
    if not incident:
        return None
    result = dict(incident)
    now = int(time.time() * 1000) if now is None else now
    last = result.get("last_evidence_at")
    if result["state"] == "active" and (last is None or now - last >= STALE_AFTER_MS):
        result["state"] = "stale"
    return result


def execution_state(rows):
    if not rows:
        return {"status": "unknown", "outcome": None}
    status, ended, active, outcome = rows[0]
    if ended and status in (None, "", "active", "running"):
        status = "ended"
    return {"status": status or "unknown", "outcome": outcome,
            "last_active_at": active, "ended_at": ended, "source": "persisted_session"}


def _bounded_rows(rows):
    """Limit individual payloads and identify every shortened row to callers."""
    truncated = []
    for row in rows:
        for key in ("data", "input", "output", "attributes", "events"):
            if key not in row:
                continue
            raw = json.dumps(row[key], ensure_ascii=False, default=str)
            if len(raw) > MAX_PAYLOAD_CHARS:
                row[key] = {"preview": raw[:MAX_PAYLOAD_CHARS], "truncated": True}
                truncated.append(row.get("id") or row.get("span_id"))
    return list(dict.fromkeys(truncated))


class InvestigationStoreMixin:
    """Reads on LocalStore's existing read connection; no second writer."""

    def query_investigation(self, *, session_id, runtime, node_id,
                            incident_id=None, cursor=None, limit=100):
        from clawmetry.local_store import _EVENT_COLS, _row_to_event
        from clawmetry.retention import resolve
        where, params = scope_sql(session_id, runtime, node_id)
        scope = {"session_id": session_id, "runtime": runtime, "node_id": node_id}
        lim = max(1, min(int(limit), MAX_PAGE))
        now = int(time.time() * 1000)
        retention = resolve(store=self)
        days = retention["effective_days"]
        cutoff = now - days * 86_400_000 if days is not None else 0
        coverage = {"node_reachable": True, "requested": dict(scope, incident_id=incident_id),
                    "limit": lim, "returned": 0, "has_more": False, "next_cursor": None,
                    "retention_days": days, "retained_after": cutoff or None,
                    "missing_event_ids": [], "evidence_complete": True,
                    "payload_truncated_ids": [], "incident_available": incident_id is None,
                    "order": "source_time_desc_event_id_desc", "source": "persisted"}
        body = {"schema_version": 1, "scope": scope, "incident": None,
                "rows": [], "evidence_rows": [], "native_spans": [],
                "execution": {"status": "unknown", "outcome": None, "last_active_at": None},
                "coverage": coverage, "resync_required": False}
        history_where, history_params = where + " AND created_at >= ?", params + [cutoff]
        if cursor:
            try:
                pos = decode_cursor(cursor, scope)
                if (not isinstance(pos, list) or len(pos) != 2
                        or any(not isinstance(v, str) or not v or len(v) > 1024 for v in pos)):
                    raise ValueError("invalid history position")
            except ValueError:
                body.update(resync_required=True, resync_reason="invalid_or_wrong_scope_cursor")
                return body
            history_where += " AND (ts < ? OR (ts = ? AND id < ?))"
            history_params += [pos[0], pos[0], pos[1]]
        cols = ",".join(_EVENT_COLS)
        rows = [_row_to_event(r, _EVENT_COLS) for r in self._fetch(
            f"SELECT {cols} FROM events WHERE {history_where} "
            "ORDER BY ts DESC, id DESC LIMIT ?", history_params + [lim + 1])]
        more = len(rows) > lim
        body["rows"] = rows[:lim]
        coverage.update(returned=len(body["rows"]), has_more=more)
        if more:
            last = body["rows"][-1]
            coverage["next_cursor"] = encode_cursor(scope, [last["ts"], last["id"]])
        if body["rows"]:
            coverage.update(from_ts=body["rows"][-1]["ts"], to_ts=body["rows"][0]["ts"])
        session = self._fetch(
            "SELECT status, ended_at, last_active_at, outcome FROM sessions WHERE " +
            where + " ORDER BY updated_at DESC LIMIT 1", params)
        if session:
            body["execution"] = execution_state(session)
        if incident_id:
            episodes = self.query_incidents(incident_id=incident_id, **scope, limit=1)
            incident = current_incident(episodes[0], now) if episodes else None
            body["incident"] = incident
            coverage["incident_available"] = bool(incident)
            if incident:
                refs = list(incident.get("evidence_refs") or [])
                if incident.get("recovery_ref"):
                    refs.append(incident["recovery_ref"])
                ids = list(dict.fromkeys(r["event_id"] for r in refs))
                if ids:
                    marks = ",".join("?" for _ in ids)
                    body["evidence_rows"] = [_row_to_event(r, _EVENT_COLS) for r in self._fetch(
                        f"SELECT {cols} FROM events WHERE {where} AND created_at >= ? "
                        f"AND id IN ({marks}) ORDER BY ts, id", params + [cutoff, *ids])]
                available = {r["id"] for r in body["evidence_rows"]}
                missing = [eid for eid in ids if eid not in available]
                coverage.update(missing_event_ids=missing, evidence_complete=not missing)
                if missing:
                    coverage["missing_reason"] = "not_retained_or_not_available_in_scope"
                body["native_spans"] = self._investigation_native_spans(refs, scope, cutoff)
        coverage["payload_truncated_ids"] = _bounded_rows(body["rows"] + body["evidence_rows"])
        coverage["truncated"] = bool(more or coverage["payload_truncated_ids"])
        return body

    def _investigation_native_spans(self, refs, scope, cutoff):
        """Native identities are exact joins, never inferred from tool names."""
        pairs = {(r.get("span_id"), r.get("trace_id")) for r in refs if r.get("span_id")}
        if not pairs:
            return []
        clauses, args = [], []
        for span, trace in pairs:
            clauses.append("(span_id=? AND trace_id=?)" if trace else "(span_id=?)")
            args.extend([span, trace] if trace else [span])
        cols = ("span_id", "trace_id", "parent_span_id", "name", "kind", "status_code",
                "start_ts", "end_ts", "duration_ms", "tool_name")
        rows = self._fetch("SELECT " + ",".join(cols) + " FROM spans WHERE session_id=? "
                           "AND node_id=? AND agent_type=? AND start_ts>=? AND (" +
                           " OR ".join(clauses) + ") LIMIT 65",
                           [scope["session_id"], scope["node_id"], scope["runtime"],
                            cutoff / 1000, *args])
        return [dict(zip(cols, r), relationship="native") for r in rows]
