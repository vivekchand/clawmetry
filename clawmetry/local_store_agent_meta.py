"""
clawmetry/local_store_agent_meta.py — AgentMetaMixin for LocalStore.

Short companion so Drift Bot can see the agent-meta API at the head of
local_store.py via the import there, rather than being buried at line ~6000
of a 20k-line file. Mixed into LocalStore alongside TrailStoreMixin.

Machine-scope keys (``node:<id>``) and principal ids (``ap_...``) coexist
safely because neither format overlaps the other.

Public API visible here:
  - set_agent_meta(agent_key, *, owner, notes, team)
  - query_agent_meta() -> {agent_key: {owner, notes, team, updated_at}}
  - node_scope_key(node_id) -> str  (machine-wide label key)
  - _NODE_SCOPE_PREFIX = "node:"

Requires the consuming class to supply self._write_lock, self._conn,
and self._fetch — all provided by LocalStore.
"""
from __future__ import annotations
import time
from typing import Any

class AgentMetaMixin:
    _NODE_SCOPE_PREFIX = "node:"

    @staticmethod
    def node_scope_key(node_id: str) -> str:
        """Return the agent_meta key for a machine-wide label on node_id."""
        return AgentMetaMixin._NODE_SCOPE_PREFIX + str(node_id or "").strip()

    def set_agent_meta(
        self,
        agent_key: str,
        owner: str | None = None,
        notes: str | None = None,
        team: str | None = None,
    ) -> None:
        """Upsert one Agent-Inventory label row (owner / notes / team).

        ``agent_key`` is a principal id (``ap_...``), a machine scope key
        (``node:<id>``), or a bare runtime name. Partial updates are honored
        via COALESCE so setting only ``team`` preserves existing ``owner``
        (and vice versa). ``None`` means "don't touch this field"; an
        explicit empty string is stored as-is and renders as unassigned in
        the ladder. Idempotent.
        """
        if not agent_key:
            raise ValueError("agent_meta must include 'agent_key'")
        agent_key = str(agent_key).lower().strip()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._write_lock:
            self._conn.execute(
                """
                INSERT INTO agent_meta (agent_key, owner, notes, team, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (agent_key) DO UPDATE SET
                    owner      = COALESCE(excluded.owner,      agent_meta.owner),
                    notes      = COALESCE(excluded.notes,      agent_meta.notes),
                    team       = COALESCE(excluded.team,       agent_meta.team),
                    updated_at = excluded.updated_at
                """,
                [agent_key, owner, notes, team, now_iso],
            )

    def query_agent_meta(self) -> dict[str, dict[str, Any]]:
        """Return ``{agent_key: {owner, notes, team, updated_at}}`` for every
        labeled runtime/scope. Read-only; uses self._fetch so callers must
        NOT hold self._write_lock on entry."""
        sql = """
            SELECT agent_key, owner, notes, team, updated_at
            FROM agent_meta
            ORDER BY agent_key ASC
        """
        out: dict[str, dict[str, Any]] = {}
        for r in self._fetch(sql, []):
            key = r[0]
            if not key:
                continue
            out[str(key)] = {
                "owner": r[1] or "",
                "notes": r[2] or "",
                "team": r[3] or "",
                "updated_at": r[4] or "",
            }
        return out
