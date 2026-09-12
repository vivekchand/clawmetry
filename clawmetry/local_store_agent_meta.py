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

    def set_agent_meta(self, agent_key: str, owner=None, notes=None, team=None) -> None:
        """Upsert one Agent-Inventory label row (owner / notes / team)."""
        ...

    def query_agent_meta(self) -> dict[str, dict[str, Any]]:
        """Return {agent_key: {owner, notes, team, updated_at}} for every labeled runtime/scope."""
        ...
