"""
routes/selfhosted_ingest.py — ClawMetry Enterprise self-hosted ingest API.

Registered by dashboard.py ONLY when SELF_HOSTED=true (see
clawmetry/selfhosted.py). Implements the server side of the daemon's cloud
sync protocol (clawmetry/sync.py `_post` call sites) so `CLAWMETRY_ENDPOINT`
can point a fleet of nodes at a single-tenant server inside a customer VPC:

* ``POST /auth``                     — node token check (+ ``e2e`` policy)
* ``POST /ingest/heartbeat``         — liveness + cache pushes + relay queries
* ``POST /ingest/{events,sessions,logs,memory,system-snapshot,stream,autonomy}``
* ``POST /api/ingest``               — legacy cron-events path
* ``POST /ingest/cache``             — relay answers
* ``POST /api/selfhosted/subscribe`` — queue a relay query for a node
* ``GET  /api/cloud/cache/<key>``, ``GET /api/cloud/brain`` — relay read-back
* ``GET  /api/cloud/policies``, ``POST /api/cloud/alerts/dispatch`` — stubs
* ``POST /api/approvals/request``, ``GET /api/approvals/<id>`` + admin decision
* ``GET  /api/export/events``        — audit export (JSONL/CSV, time-ranged)
* ``GET  /api/selfhosted/nodes``, ``GET /api/selfhosted/status``
* ``GET  /selfhosted``               — fleet overview page (admin-gated HTML)

Storage is a single SQLite database (stdlib, WAL) at
``CLAWMETRY_SELF_HOSTED_DB`` (default ``~/.clawmetry/selfhosted.db``):

* ``ingest_log``  — append-only raw record of every accepted POST (the
  immutable audit log; rows are never updated or deleted)
* ``events``      — plaintext events extracted for query/export (empty when
  nodes E2E-encrypt; see CLAWMETRY_SELF_HOSTED_E2E)
* ``nodes``, ``sessions``, ``cache``, ``pending_queries``, ``approvals``

Auth: node endpoints take ``X-Api-Key`` ∈ CLAWMETRY_API_TOKENS; read/export
endpoints take that or admin HTTP Basic (CLAWMETRY_ADMIN_USER/_PASSWORD).
Encrypted envelopes (``{"encrypted": true, "blob": ...}``) are stored opaque —
this server never sees an encryption key.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

from clawmetry.selfhosted import (
    check_admin_or_token,
    check_api_key,
    e2e_enabled,
)

logger = logging.getLogger("clawmetry.routes.selfhosted_ingest")

bp_selfhosted = Blueprint("selfhosted_ingest", __name__)

# RLock: handlers hold this around their whole read/write, and _db() re-enters
# it for first-time DDL init.
_DB_LOCK = threading.RLock()
_INIT_DONE = False

_DDL = """
CREATE TABLE IF NOT EXISTS ingest_log (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    node_id     TEXT,
    path        TEXT NOT NULL,
    encrypted   INTEGER NOT NULL DEFAULT 0,
    payload     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,
    node_id     TEXT,
    agent_type  TEXT,
    agent_id    TEXT,
    session_id  TEXT,
    event_type  TEXT,
    ts          TEXT,
    model       TEXT,
    token_count INTEGER,
    cost_usd    REAL,
    data        TEXT,
    received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sh_events_ts ON events(ts);
CREATE TABLE IF NOT EXISTS nodes (
    node_id    TEXT PRIMARY KEY,
    hostname   TEXT,
    platform   TEXT,
    version    TEXT,
    first_seen TEXT,
    last_seen  TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    node_id    TEXT,
    session_id TEXT,
    payload    TEXT,
    updated_at TEXT,
    PRIMARY KEY (node_id, session_id)
);
CREATE TABLE IF NOT EXISTS cache (
    cache_key  TEXT PRIMARY KEY,
    blob       TEXT,
    shape      TEXT,
    args_hash  TEXT,
    ttl_s      INTEGER,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS pending_queries (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id  TEXT NOT NULL,
    query    TEXT NOT NULL,
    added_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id         TEXT PRIMARY KEY,
    node_id    TEXT,
    payload    TEXT,
    status     TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    decided_at TEXT
);
"""


def _db_path() -> str:
    return os.environ.get(
        "CLAWMETRY_SELF_HOSTED_DB",
        os.path.expanduser("~/.clawmetry/selfhosted.db"),
    )


def _db() -> sqlite3.Connection:
    global _INIT_DONE
    path = _db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    if not _INIT_DONE:
        with _DB_LOCK:
            conn.executescript(_DDL)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
            except Exception:
                pass
            conn.commit()
            _INIT_DONE = True
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reset_for_tests() -> None:
    """Test helper — forget DB-init state (tests repoint CLAWMETRY_SELF_HOSTED_DB)."""
    global _INIT_DONE
    _INIT_DONE = False


# ── Auth helpers ────────────────────────────────────────────────────────────


def _request_api_key():
    key = request.headers.get("X-Api-Key", "")
    if key:
        return key
    body = request.get_json(silent=True)
    if isinstance(body, dict):
        return body.get("api_key", "")
    return ""


def _node_auth_or_401():
    if check_api_key(_request_api_key()):
        return None
    return jsonify({"ok": False, "error": "invalid_api_key"}), 401


def _admin_auth_or_401():
    if check_admin_or_token(request):
        return None
    return (
        jsonify({"ok": False, "error": "unauthorized"}),
        401,
        {"WWW-Authenticate": 'Basic realm="clawmetry-selfhosted"'},
    )


# ── Ingest plumbing ─────────────────────────────────────────────────────────


def _log_ingest(conn, path: str, payload: dict) -> None:
    conn.execute(
        "INSERT INTO ingest_log (received_at, node_id, path, encrypted, payload)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            _now(),
            str(payload.get("node_id") or ""),
            path,
            1 if payload.get("encrypted") else 0,
            json.dumps(payload, separators=(",", ":"), default=str),
        ),
    )


def _touch_node(conn, node_id: str, hostname="", platform="", version="") -> None:
    if not node_id:
        return
    now = _now()
    conn.execute(
        "INSERT INTO nodes (node_id, hostname, platform, version, first_seen, last_seen)"
        " VALUES (?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(node_id) DO UPDATE SET"
        "  hostname = CASE WHEN excluded.hostname != '' THEN excluded.hostname ELSE nodes.hostname END,"
        "  platform = CASE WHEN excluded.platform != '' THEN excluded.platform ELSE nodes.platform END,"
        "  version  = CASE WHEN excluded.version  != '' THEN excluded.version  ELSE nodes.version  END,"
        "  last_seen = excluded.last_seen",
        (node_id, hostname or "", platform or "", version or "", now, now),
    )


def _store_event(conn, node_id: str, ev: dict) -> None:
    """Tolerantly extract one plaintext event into the queryable table."""
    if not isinstance(ev, dict):
        return
    ev_id = str(
        ev.get("id")
        or ev.get("eventId")
        or ev.get("messageId")
        or uuid.uuid4().hex
    )
    data = ev.get("data")
    conn.execute(
        "INSERT OR IGNORE INTO events"
        " (id, node_id, agent_type, agent_id, session_id, event_type, ts,"
        "  model, token_count, cost_usd, data, received_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ev_id,
            str(ev.get("node_id") or node_id or ""),
            str(ev.get("agent_type") or ""),
            str(ev.get("agent_id") or ""),
            str(ev.get("session_id") or ""),
            str(ev.get("event_type") or ev.get("type") or "unknown"),
            str(ev.get("ts") or ev.get("timestamp") or ""),
            str(ev.get("model") or ""),
            ev.get("token_count"),
            ev.get("cost_usd"),
            json.dumps(data, separators=(",", ":"), default=str)
            if data is not None
            else None,
            _now(),
        ),
    )


def _accept_ingest(path: str, extract_events_key: str = None):
    """Shared handler body for the fire-and-forget /ingest/* endpoints."""
    err = _node_auth_or_401()
    if err:
        return err
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    node_id = str(payload.get("node_id") or "")
    with _DB_LOCK:
        conn = _db()
        try:
            _log_ingest(conn, path, payload)
            _touch_node(conn, node_id)
            if (
                extract_events_key
                and not payload.get("encrypted")
                and isinstance(payload.get(extract_events_key), list)
            ):
                for ev in payload[extract_events_key]:
                    _store_event(conn, node_id, ev)
            conn.commit()
        finally:
            conn.close()
    return jsonify({"ok": True})


# ── Node-facing endpoints ───────────────────────────────────────────────────


@bp_selfhosted.route("/auth", methods=["POST"])
def sh_auth():
    payload = request.get_json(silent=True) or {}
    if not check_api_key(_request_api_key()):
        return jsonify({"ok": False, "error": "invalid_api_key"}), 401
    node_id = str(
        payload.get("existing_node_id") or payload.get("hostname") or ""
    ).strip()
    with _DB_LOCK:
        conn = _db()
        try:
            _touch_node(conn, node_id, hostname=str(payload.get("hostname") or ""))
            conn.commit()
        finally:
            conn.close()
    return jsonify(
        {
            "ok": True,
            "valid": True,
            "node_id": node_id,
            "sync_allowed": True,
            "plan": "enterprise",
            "e2e": e2e_enabled(),
        }
    )


@bp_selfhosted.route("/api/register", methods=["POST"])
def sh_register():
    # Self-hosted servers use operator-provisioned tokens (CLAWMETRY_API_TOKENS);
    # open self-registration would let anyone who can reach the port mint access.
    return (
        jsonify(
            {
                "ok": False,
                "error": "registration_disabled",
                "message": "Self-hosted mode: connect with a configured token: "
                "CLAWMETRY_ENDPOINT=<this server> clawmetry connect --key cm_...",
            }
        ),
        403,
    )


@bp_selfhosted.route("/ingest/heartbeat", methods=["POST"])
def sh_heartbeat():
    err = _node_auth_or_401()
    if err:
        return err
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    node_id = str(payload.get("node_id") or "")
    pending = []
    with _DB_LOCK:
        conn = _db()
        try:
            _touch_node(
                conn,
                node_id,
                platform=str(payload.get("platform") or ""),
                version=str(payload.get("version") or ""),
            )
            now = _now()
            for push in payload.get("cache_pushes") or []:
                if not isinstance(push, dict) or not push.get("key"):
                    continue
                conn.execute(
                    "INSERT INTO cache (cache_key, blob, shape, args_hash, ttl_s, updated_at)"
                    " VALUES (?, ?, ?, ?, ?, ?)"
                    " ON CONFLICT(cache_key) DO UPDATE SET blob=excluded.blob,"
                    "  ttl_s=excluded.ttl_s, updated_at=excluded.updated_at",
                    (
                        str(push["key"]),
                        push.get("blob"),
                        "",
                        "",
                        int(push.get("ttl_s") or 0),
                        now,
                    ),
                )
            if node_id:
                rows = conn.execute(
                    "SELECT seq, query FROM pending_queries WHERE node_id = ?"
                    " ORDER BY seq LIMIT 20",
                    (node_id,),
                ).fetchall()
                for row in rows:
                    try:
                        pending.append(json.loads(row["query"]))
                    except Exception:
                        pass
                if rows:
                    conn.execute(
                        "DELETE FROM pending_queries WHERE seq <= ? AND node_id = ?",
                        (rows[-1]["seq"], node_id),
                    )
            conn.commit()
        finally:
            conn.close()
    return jsonify(
        {
            "ok": True,
            "sync_allowed": True,
            "plan": "enterprise",
            "viewer_active": False,
            "pending_queries": pending,
        }
    )


@bp_selfhosted.route("/ingest/events", methods=["POST"])
def sh_ingest_events():
    return _accept_ingest("/ingest/events", extract_events_key="events")


@bp_selfhosted.route("/api/ingest", methods=["POST"])
def sh_api_ingest():
    return _accept_ingest("/api/ingest", extract_events_key="events")


@bp_selfhosted.route("/ingest/sessions", methods=["POST"])
def sh_ingest_sessions():
    err = _node_auth_or_401()
    if err:
        return err
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    node_id = str(payload.get("node_id") or "")
    with _DB_LOCK:
        conn = _db()
        try:
            _log_ingest(conn, "/ingest/sessions", payload)
            _touch_node(conn, node_id)
            now = _now()
            for sess in payload.get("sessions") or []:
                if not isinstance(sess, dict):
                    continue
                sid = str(sess.get("session_id") or "")
                if not sid:
                    continue
                conn.execute(
                    "INSERT INTO sessions (node_id, session_id, payload, updated_at)"
                    " VALUES (?, ?, ?, ?)"
                    " ON CONFLICT(node_id, session_id) DO UPDATE SET"
                    "  payload=excluded.payload, updated_at=excluded.updated_at",
                    (
                        node_id,
                        sid,
                        json.dumps(sess, separators=(",", ":"), default=str),
                        now,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
    return jsonify({"ok": True})


@bp_selfhosted.route("/ingest/logs", methods=["POST"])
def sh_ingest_logs():
    return _accept_ingest("/ingest/logs")


@bp_selfhosted.route("/ingest/memory", methods=["POST"])
def sh_ingest_memory():
    return _accept_ingest("/ingest/memory")


@bp_selfhosted.route("/ingest/system-snapshot", methods=["POST"])
def sh_ingest_snapshot():
    return _accept_ingest("/ingest/system-snapshot")


@bp_selfhosted.route("/ingest/stream", methods=["POST"])
def sh_ingest_stream():
    return _accept_ingest("/ingest/stream")


@bp_selfhosted.route("/ingest/autonomy", methods=["POST"])
def sh_ingest_autonomy():
    return _accept_ingest("/ingest/autonomy")


@bp_selfhosted.route("/ingest/cache", methods=["POST"])
def sh_ingest_cache():
    err = _node_auth_or_401()
    if err:
        return err
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload.get("cache_key"):
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    with _DB_LOCK:
        conn = _db()
        try:
            conn.execute(
                "INSERT INTO cache (cache_key, blob, shape, args_hash, ttl_s, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(cache_key) DO UPDATE SET blob=excluded.blob,"
                "  shape=excluded.shape, args_hash=excluded.args_hash,"
                "  ttl_s=excluded.ttl_s, updated_at=excluded.updated_at",
                (
                    str(payload["cache_key"]),
                    payload.get("blob"),
                    str(payload.get("shape") or ""),
                    str(payload.get("args_hash") or ""),
                    int(payload.get("ttl") or payload.get("ttl_s") or 0),
                    _now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return jsonify({"ok": True})


# ── Relay read-back + stubs ─────────────────────────────────────────────────


# NOTE: deliberately NOT /api/cloud/subscribe — the OSS dashboard already
# owns that rule (routes/meta.py bp_cloud_relay, the local-daemon relay).
# Fleet-level subscribe (queue a query for a REMOTE node's next heartbeat)
# lives under the selfhosted namespace instead.
@bp_selfhosted.route("/api/selfhosted/subscribe", methods=["POST"])
def sh_subscribe():
    err = _admin_auth_or_401()
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    node_id = str(payload.get("node_id") or "")
    if not node_id:
        return jsonify({"ok": False, "error": "node_id required"}), 400
    query = {k: v for k, v in payload.items() if k != "node_id"}
    with _DB_LOCK:
        conn = _db()
        try:
            conn.execute(
                "INSERT INTO pending_queries (node_id, query, added_at) VALUES (?, ?, ?)",
                (node_id, json.dumps(query, separators=(",", ":")), _now()),
            )
            conn.commit()
        finally:
            conn.close()
    return jsonify(
        {"ok": True, "status": "queued", "cache_key": query.get("cache_key", "")}
    )


def _cache_lookup(cache_key: str):
    with _DB_LOCK:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT * FROM cache WHERE cache_key = ?", (cache_key,)
            ).fetchone()
        finally:
            conn.close()
    return row


@bp_selfhosted.route("/api/cloud/cache/<path:cache_key>", methods=["GET"])
def sh_cache_get(cache_key):
    err = _admin_auth_or_401()
    if err:
        return err
    row = _cache_lookup(cache_key)
    if row is None:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify(
        {
            "ok": True,
            "cache_key": row["cache_key"],
            "blob": row["blob"],
            "shape": row["shape"],
            "ttl_s": row["ttl_s"],
            "updated_at": row["updated_at"],
        }
    )


@bp_selfhosted.route("/api/cloud/brain", methods=["GET"])
def sh_brain_get():
    err = _admin_auth_or_401()
    if err:
        return err
    key = request.args.get("key", "")
    row = _cache_lookup(key) if key else None
    if row is None:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "blob": row["blob"], "updated_at": row["updated_at"]})


@bp_selfhosted.route("/api/cloud/policies", methods=["GET"])
def sh_policies():
    return jsonify({"policies": []})


@bp_selfhosted.route("/api/cloud/alerts/dispatch", methods=["POST"])
def sh_alerts_dispatch():
    err = _node_auth_or_401()
    if err:
        return err
    # Sink delivery (Slack/PagerDuty/webhooks) is a customer-side decision;
    # acknowledge so the daemon's alert evaluator doesn't retry forever.
    return jsonify({"ok": True, "deduped": False, "dispatched": []})


# ── Approvals (minimal single-tenant flow) ──────────────────────────────────


@bp_selfhosted.route("/api/approvals/request", methods=["POST"])
def sh_approval_request():
    # Daemon authenticates with Authorization: Bearer <token> on /api/* paths.
    bearer = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
    if not check_api_key(bearer or _request_api_key()):
        return jsonify({"ok": False, "error": "invalid_api_key"}), 401
    payload = request.get_json(silent=True) or {}
    approval_id = str(payload.get("id") or uuid.uuid4().hex)
    with _DB_LOCK:
        conn = _db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO approvals (id, node_id, payload, status, created_at)"
                " VALUES (?, ?, ?, 'pending', ?)",
                (
                    approval_id,
                    str(payload.get("node_id") or ""),
                    json.dumps(payload, separators=(",", ":"), default=str),
                    _now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return jsonify({"ok": True, "id": approval_id, "status": "pending"})


@bp_selfhosted.route("/api/approvals/<approval_id>", methods=["GET"])
def sh_approval_status(approval_id):
    bearer = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
    if not check_api_key(bearer or _request_api_key()):
        return jsonify({"ok": False, "error": "invalid_api_key"}), 401
    with _DB_LOCK:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT status FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        finally:
            conn.close()
    if row is None:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "status": row["status"]})


@bp_selfhosted.route("/api/selfhosted/approvals/<approval_id>/decision", methods=["POST"])
def sh_approval_decide(approval_id):
    err = _admin_auth_or_401()
    if err:
        return err
    decision = str((request.get_json(silent=True) or {}).get("status") or "").lower()
    if decision not in ("approved", "denied"):
        return jsonify({"ok": False, "error": "status must be approved|denied"}), 400
    with _DB_LOCK:
        conn = _db()
        try:
            cur = conn.execute(
                "UPDATE approvals SET status = ?, decided_at = ? WHERE id = ?",
                (decision, _now(), approval_id),
            )
            conn.commit()
            updated = cur.rowcount
        finally:
            conn.close()
    if not updated:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "id": approval_id, "status": decision})


# ── Audit export + admin reads ──────────────────────────────────────────────

_EXPORT_COLS = (
    "id",
    "node_id",
    "agent_type",
    "agent_id",
    "session_id",
    "event_type",
    "ts",
    "model",
    "token_count",
    "cost_usd",
    "data",
    "received_at",
)


@bp_selfhosted.route("/api/export/events", methods=["GET"])
def sh_export_events():
    err = _admin_auth_or_401()
    if err:
        return err
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")
    fmt = request.args.get("format", "jsonl").lower()
    if fmt not in ("jsonl", "csv"):
        return jsonify({"ok": False, "error": "format must be jsonl|csv"}), 400

    where, params = [], []
    if date_from:
        where.append("ts >= ?")
        params.append(date_from)
    if date_to:
        where.append("ts <= ?")
        params.append(date_to)
    sql = "SELECT * FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ts"

    def _rows():
        with _DB_LOCK:
            conn = _db()
            try:
                yield from conn.execute(sql, params).fetchall()
            finally:
                conn.close()

    if fmt == "csv":
        def _gen_csv():
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(_EXPORT_COLS)
            yield buf.getvalue()
            for row in _rows():
                buf.seek(0)
                buf.truncate()
                writer.writerow([row[c] for c in _EXPORT_COLS])
                yield buf.getvalue()

        return Response(_gen_csv(), mimetype="text/csv")

    def _gen_jsonl():
        for row in _rows():
            rec = {c: row[c] for c in _EXPORT_COLS}
            if rec.get("data"):
                try:
                    rec["data"] = json.loads(rec["data"])
                except Exception:
                    pass
            yield json.dumps(rec, separators=(",", ":"), default=str) + "\n"

    return Response(_gen_jsonl(), mimetype="application/x-ndjson")


@bp_selfhosted.route("/api/selfhosted/nodes", methods=["GET"])
def sh_nodes():
    err = _admin_auth_or_401()
    if err:
        return err
    with _DB_LOCK:
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT * FROM nodes ORDER BY last_seen DESC"
            ).fetchall()
        finally:
            conn.close()
    return jsonify({"ok": True, "nodes": [dict(r) for r in rows]})


@bp_selfhosted.route("/api/selfhosted/status", methods=["GET"])
def sh_status():
    err = _admin_auth_or_401()
    if err:
        return err
    with _DB_LOCK:
        conn = _db()
        try:
            counts = {
                table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for table in ("nodes", "events", "ingest_log", "sessions", "cache")
            }
        finally:
            conn.close()
    return jsonify(
        {
            "ok": True,
            "self_hosted": True,
            "e2e": e2e_enabled(),
            "db_path": _db_path(),
            "counts": counts,
            "ts": _now(),
        }
    )


# ── Fleet page (v1) ─────────────────────────────────────────────────────────

_FLEET_PAGE_TMPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClawMetry Enterprise: fleet</title>
<style>
 body{{font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      margin:2rem auto;max-width:64rem;padding:0 1rem;color:#1a1d21;background:#fafbfc}}
 h1{{font-size:1.3rem}} table{{border-collapse:collapse;width:100%;margin:1rem 0}}
 th,td{{text-align:left;padding:.45rem .7rem;border-bottom:1px solid #e2e5e9}}
 th{{font-weight:600;color:#5f6670;font-size:.8rem;text-transform:uppercase}}
 .ok{{color:#1a7f37}} .stale{{color:#b35900}} .dead{{color:#c0332b}}
 .muted{{color:#7a828c;font-size:.85rem}}
 code{{background:#eef0f3;padding:.1rem .35rem;border-radius:4px}}
 @media (prefers-color-scheme: dark){{
   body{{color:#e6e8eb;background:#14171a}} th{{color:#9aa3ad}}
   th,td{{border-color:#2a2f35}} code{{background:#22272d}} .muted{{color:#8b939d}}
 }}
</style></head><body>
<h1>ClawMetry Enterprise fleet</h1>
<p class="muted">Self-hosted server &middot; E2E blob encryption: <strong>{e2e}</strong>
 &middot; {node_count} node(s) &middot; {event_count} events stored &middot; generated {ts}</p>
<table><thead><tr>
 <th>Node</th><th>Hostname</th><th>Platform</th><th>Daemon</th><th>Last seen</th><th>Status</th>
</tr></thead><tbody>
{rows}
</tbody></table>
<p class="muted">Each node keeps its full dashboard at its own <code>localhost:8900</code>.
 APIs: <code>/api/selfhosted/nodes</code>, <code>/api/selfhosted/status</code>,
 <code>/api/export/events?from=&amp;to=&amp;format=jsonl|csv</code>.</p>
</body></html>"""


def _fleet_row(node, now):
    from datetime import datetime

    last = str(node["last_seen"] or "")
    label, cls = "never", "dead"
    if last:
        try:
            seen = datetime.fromisoformat(last)
            age = (now - seen).total_seconds()
            if age < 180:
                label, cls = "online", "ok"
            elif age < 3600:
                label, cls = f"{int(age // 60)} min ago", "stale"
            else:
                label, cls = f"{int(age // 3600)} h ago", "dead"
        except Exception:
            label, cls = last, "muted"
    import html as _html

    esc = lambda v: _html.escape(str(v or ""))  # noqa: E731
    return (
        f"<tr><td><code>{esc(node['node_id'])}</code></td>"
        f"<td>{esc(node['hostname'])}</td><td>{esc(node['platform'])}</td>"
        f"<td>{esc(node['version'])}</td><td>{esc(last[:19].replace('T', ' '))}</td>"
        f"<td class=\"{cls}\">{esc(label)}</td></tr>"
    )


@bp_selfhosted.route("/selfhosted", methods=["GET"])
def sh_fleet_page():
    """Minimal fleet overview for the self-hosted server (admin-gated HTML).

    v1 scope: node roster with liveness. Rich per-node views stay on each
    node's own local dashboard; this page is the at-a-glance fleet answer
    to "is every agent box alive and current?".
    """
    err = _admin_auth_or_401()
    if err:
        return err
    from datetime import datetime, timezone

    with _DB_LOCK:
        conn = _db()
        try:
            nodes = conn.execute(
                "SELECT * FROM nodes ORDER BY last_seen DESC"
            ).fetchall()
            event_count = conn.execute(
                "SELECT COUNT(*) AS n FROM events"
            ).fetchone()["n"]
        finally:
            conn.close()
    now = datetime.now(timezone.utc)
    rows = "\n".join(_fleet_row(n, now) for n in nodes) or (
        '<tr><td colspan="6" class="muted">No nodes yet. Connect one with: '
        "<code>CLAWMETRY_ENDPOINT=&lt;this server&gt; clawmetry connect --key cm_...</code>"
        "</td></tr>"
    )
    html = _FLEET_PAGE_TMPL.format(
        e2e="on" if e2e_enabled() else "off (plaintext inside deployment)",
        node_count=len(nodes),
        event_count=event_count,
        ts=now.strftime("%Y-%m-%d %H:%M UTC"),
        rows=rows,
    )
    return Response(html, mimetype="text/html")
