"""Turso cloud data provider for ClawMetry cloud dashboard."""

from __future__ import annotations
import hashlib
import json
import logging
import os
import urllib.request
import urllib.error
from clawmetry.providers.base import ClawMetryDataProvider, Event, Session

logger = logging.getLogger("clawmetry.providers.turso")


class TursoDataProvider(ClawMetryDataProvider):
    """
    Reads data from Turso (libSQL) for the ClawMetry cloud dashboard.
    Set CLAWMETRY_PROVIDER=turso with TURSO_URL + TURSO_TOKEN + CLAWMETRY_TOKEN.
    owner_hash is derived from the cm_ API token automatically.
    """

    def __init__(
        self, turso_url="", turso_token="", owner_hash="", node_id="", **kwargs
    ):
        super().__init__(**kwargs)
        self.turso_url = turso_url or os.environ.get("TURSO_URL", "")
        self.turso_token = turso_token or os.environ.get("TURSO_TOKEN", "")
        cm_token = os.environ.get("CLAWMETRY_TOKEN", "")
        self.owner_hash = owner_hash or (
            hashlib.sha256(cm_token.encode()).hexdigest() if cm_token else ""
        )
        self.node_id = node_id or os.environ.get("CLAWMETRY_NODE_ID", "")

    def _query(self, sql, params=None):
        if not self.turso_url or not self.turso_token:
            return []
        args = []
        for p in params or []:
            if p is None:
                args.append({"type": "null", "value": None})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            else:
                args.append({"type": "text", "value": str(p)})
        payload = json.dumps(
            {
                "requests": [
                    {"type": "execute", "stmt": {"sql": sql, "args": args}},
                    {"type": "close"},
                ]
            }
        ).encode()
        req = urllib.request.Request(
            self.turso_url.rstrip("/") + "/v2/pipeline",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.turso_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            result = data["results"][0]
            if result.get("type") == "error":
                logger.error("Turso error: %s", result.get("error"))
                return []
            cols = [c["name"] for c in result["response"]["result"]["cols"]]
            return [
                {
                    cols[i]: (cell.get("value") if cell.get("type") != "null" else None)
                    for i, cell in enumerate(row)
                }
                for row in result["response"]["result"]["rows"]
            ]
        except Exception as e:
            logger.warning("Turso query failed: %s", e)
            return []

    def list_sessions(self, limit=30, include_subagents=True, since_ms=None):
        sql = "SELECT * FROM sessions WHERE owner_hash=?"
        params = [self.owner_hash]
        if self.node_id:
            sql += " AND node_id=?"
            params.append(self.node_id)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        return [
            Session(
                session_id=r.get("session_id", ""),
                display_name=r.get("display_name", ""),
                model=r.get("model", ""),
                channel="",
                updated_at=int(r.get("updated_at") or 0),
                total_tokens=int(r.get("total_tokens") or 0),
            )
            for r in self._query(sql, params)
        ]

    def get_session(self, session_id):
        rows = self._query(
            "SELECT * FROM sessions WHERE session_id=? AND owner_hash=? LIMIT 1",
            [session_id, self.owner_hash],
        )
        if not rows:
            return None
        r = rows[0]
        return Session(
            session_id=r.get("session_id", ""),
            display_name=r.get("display_name", ""),
            model=r.get("model", ""),
            channel="",
            updated_at=int(r.get("updated_at") or 0),
            total_tokens=int(r.get("total_tokens") or 0),
        )

    def get_session_index(self):
        return {
            s.session_id: {
                "session_id": s.session_id,
                "display_name": s.display_name,
                "model": s.model,
                "updated_at": s.updated_at,
                "total_tokens": s.total_tokens,
            }
            for s in self.list_sessions(limit=200)
        }

    def get_events(self, session_id, limit=500, tail_bytes=None):
        rows = self._query(
            "SELECT * FROM events WHERE owner_hash=? AND session_id=? ORDER BY ts DESC LIMIT ?",
            [self.owner_hash, session_id, limit],
        )
        return [
            Event(
                event_id=str(i),
                session_id=r.get("session_id", ""),
                event_type=r.get("event_type", ""),
                ts=r.get("ts", ""),
                data=json.loads(r.get("data") or "{}"),
            )
            for i, r in enumerate(rows)
        ]

    def get_log_lines(self, date_str=None, limit=1000):
        return []

    def list_log_dates(self, days_back=31):
        return []

    def list_memory_files(self):
        return []

    def read_workspace_file(self, relative_path):
        return ""

    def list_crons(self):
        return []

    def health_check(self):
        try:
            rows = self._query("SELECT 1 AS ok")
            return {"provider": "turso", "ok": bool(rows), "url": self.turso_url}
        except Exception as e:
            import logging

            logging.debug("Turso health check failed: %s", e)
            return {"provider": "turso", "ok": False, "error": str(e)}
