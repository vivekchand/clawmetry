"""Agent-framework adapters for ClawMetry.

An adapter translates a specific AI-agent framework's native data format
(filesystem layout, database schema, event log) into ClawMetry's unified
:class:`Session`/:class:`Event` schema so the dashboard can observe it.

Adapters are registered at startup::

    from clawmetry.adapters import registry
    from clawmetry.adapters.openclaw import OpenClawAdapter
    registry.register(OpenClawAdapter())

The ``/api/agents`` route iterates :func:`registry.detect_all` and returns
all detected adapters with their capabilities + session counts. The UI
renders one chip per adapter and gates tabs by capability.

Design notes
------------
- Adapters handle *agent framework* translation (OpenClaw JSONL vs Hermes
  SQLite vs Claude Code JSONL, …). The ``clawmetry/providers/`` layer
  handles *storage backend* translation (local disk vs Turso cloud).
  Orthogonal axes — we intentionally do not merge them.
- Adapters must be zero-cost when their agent is not installed: ``detect()``
  should return ``None`` quickly, never raise.
- Adapters are read-only unless they declare ``GATEWAY_RPC`` capability.
"""
from __future__ import annotations

from .base import (
    AgentAdapter,
    Capability,
    DetectResult,
    Event,
    Session,
)
from . import registry

__all__ = [
    "AgentAdapter",
    "Capability",
    "DetectResult",
    "Event",
    "Session",
    "registry",
]
