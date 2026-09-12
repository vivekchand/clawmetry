"""
clawmetry/local_store_agent_meta.py — AgentMetaMixin for LocalStore.

Short companion so Drift Bot can see the agent-meta API at the head of
local_store.py via the import there, rather than being buried at line ~6000
of a 20k-line file. Mixed into LocalStore alongside TrailStoreMixin.

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
    """Mixin that adds the agent-meta label surface to LocalStore.

    Owner, team, and notes can be attached at three levels — agent,
    machine (node), and runtime — and are resolved on read, not stored
    on session rows.  See REQ-OBS-004 and AC-OBS-004.x.
    """

    # Namespace prefix for machine-wide label keys. Principal ids start
    # "ap_" and bare runtime names contain no ":", so "node:<id>" cannot
    # collide with either.
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

        ``agent_key`` is the runtime key, a principal id ("ap_..."), or a
        machine-scope key ("node:<id>"). Partial updates are honored via
        COALESCE so setting only ``notes`` preserves an existing ``owner``
        (and vice versa). An explicit empty string is stored as-is; ``None``
        means "don't touch this field". Idempotent.

        The daemon owns the writer lock, so this goes through the daemon
        proxy from the dashboard process (see ``set_agent_meta`` in
        ``routes/local_query._DAEMON_METHODS``).
        """
        if not agent_key:
            raise ValueError("agent_meta must include 'agent_key'")
        agent_key = str(agent_key).lower().strip()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._write_lock:  # type: ignore[attr-defined]
            self._conn.execute("""  # type: ignore[attr-defined]
                INSERT INTO agent_meta (agent_key, owner, notes, team, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (agent_key) DO UPDATE SET
                    owner      = COALESCE(excluded.owner, agent_meta.owner),
                    notes      = COALESCE(excluded.notes, agent_meta.notes),
                    team       = COALESCE(excluded.team,  agent_meta.team),
                    updated_at = excluded.updated_at
            """, [
                agent_key,
                owner,
                notes,
                team,
                now_iso,
            ])

    def query_agent_meta(self) -> dict[str, dict[str, Any]]:
        """Return ``{agent_key: {owner, notes, team, updated_at}}`` for every
        labeled runtime/scope. Read-only; goes through ``self._fetch`` (no
        write-lock — callers MUST NOT wrap this in ``with self._write_lock``
        as that would deadlock a regular Lock)."""
        sql = """
            SELECT agent_key, owner, notes, team, updated_at
            FROM agent_meta
            ORDER BY agent_key ASC
        """
        out: dict[str, dict[str, Any]] = {}
        for r in self._fetch(sql, []):  # type: ignore[attr-defined]
            key = r[0]
            if not key:
                continue
            out[str(key)] = {
                "owner": r[1],
                "notes": r[2],
                "team": r[3],
                "updated_at": r[4],
            }
        return out
