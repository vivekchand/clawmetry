"""Adapter base class + unified schemas.

Every agent framework (OpenClaw, Hermes, Claude Code, Codex, Cursor, …)
implements :class:`AgentAdapter` and translates its native data into the
shared :class:`Session` / :class:`Event` shapes below. The dashboard only
ever sees the unified shapes — it does not know what native format sits
behind them.

Schema design: fields are a *superset* across all known agents today.
Hermes pre-computes cache/reasoning tokens and cost; OpenClaw does not.
Adapters fill what they have and leave the rest as zero / empty. The
``capabilities()`` set tells the UI which panels to render.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set


class Capability(str, Enum):
    """UI/data capabilities an adapter may expose.

    The dashboard gates panels by these. An adapter that returns
    ``{SESSIONS, EVENTS}`` gets only the Sessions tab; one that adds
    ``BRAIN`` unlocks the live event stream; adding ``GATEWAY_RPC``
    enables control-plane actions (pause/resume, cron CRUD).
    """

    SESSIONS = "sessions"
    EVENTS = "events"
    COST = "cost"
    SUBAGENTS = "subagents"
    CRONS = "crons"
    SKILLS = "skills"
    MEMORY = "memory"
    BRAIN = "brain"
    LOGS = "logs"
    GATEWAY_RPC = "gateway_rpc"
    CHANNELS = "channels"


@dataclass
class Session:
    """A conversation with an agent.

    ``agent`` identifies which adapter produced this row. ``id`` is the
    native session identifier (UUID, timestamp-hash, etc.) — opaque to
    the platform. Token breakdown fields default to 0 for adapters that
    do not compute them; ``cost_usd=None`` means "unknown / not tracked".
    """

    agent: str
    id: str
    display_name: str = ""
    title: str = ""
    model: str = ""
    source: str = ""
    started_at: float = 0.0
    ended_at: Optional[float] = None
    parent_id: Optional[str] = None
    message_count: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: Optional[float] = None
    cost_status: str = ""
    end_reason: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "agent": self.agent,
            "id": self.id,
            "displayName": self.display_name or self.title or self.id[:24],
            "title": self.title,
            "model": self.model,
            "source": self.source,
            "startedAt": self.started_at,
            "endedAt": self.ended_at,
            "parentId": self.parent_id,
            "messageCount": self.message_count,
            "totalTokens": self.total_tokens,
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "cacheReadTokens": self.cache_read_tokens,
            "cacheWriteTokens": self.cache_write_tokens,
            "reasoningTokens": self.reasoning_tokens,
            "costUsd": self.cost_usd,
            "costStatus": self.cost_status,
            "endReason": self.end_reason,
        }
        if self.extra:
            d["extra"] = self.extra
        return d


@dataclass
class Event:
    """A single ordered event within a session.

    ``type`` covers: ``message``, ``tool_call``, ``tool_result``,
    ``model_change``, ``thinking``, ``compaction``, ``error``, plus
    adapter-defined custom types in ``extra.customType``.
    """

    agent: str
    session_id: str
    id: str
    type: str
    ts: float = 0.0
    role: str = ""
    content: str = ""
    tool_name: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    parent_id: Optional[str] = None
    tokens: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "agent": self.agent,
            "sessionId": self.session_id,
            "id": self.id,
            "type": self.type,
            "ts": self.ts,
            "role": self.role,
            "content": self.content,
            "toolName": self.tool_name,
            "toolCalls": self.tool_calls,
            "parentId": self.parent_id,
            "tokens": self.tokens,
        }
        if self.extra:
            d["extra"] = self.extra
        return d


@dataclass
class DetectResult:
    """What :meth:`AgentAdapter.detect` returns.

    ``detected=False`` means the agent is not installed / no data dir
    on this machine. ``detected=True, running=False`` means the agent
    is installed but not currently active — still show in the chip bar
    with a grey dot, so users see historical data.
    """

    name: str
    display_name: str
    detected: bool
    running: bool = False
    workspace: str = ""
    session_count: int = 0
    capabilities: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "detected": self.detected,
            "running": self.running,
            "workspace": self.workspace,
            "sessionCount": self.session_count,
            "capabilities": self.capabilities,
            "meta": self.meta,
        }


class AgentAdapter(ABC):
    """Base class for all agent-framework adapters.

    Adapter subclasses must set :attr:`name` + :attr:`display_name` and
    implement :meth:`detect`, :meth:`list_sessions`, :meth:`capabilities`.
    Other methods are optional — default impls return empty results so
    the UI gracefully degrades.
    """

    name: str = ""
    display_name: str = ""

    @abstractmethod
    def detect(self) -> DetectResult:
        """Return a :class:`DetectResult`. Must never raise.

        Implementations should be cheap (filesystem stat, SQLite
        ``SELECT count(*)``) — this runs on every page load.
        """
        ...

    @abstractmethod
    def list_sessions(self, limit: int = 100) -> List[Session]:
        """Return recent sessions, newest first. Empty list if none."""
        ...

    def read_session(self, session_id: str) -> Optional[Session]:
        """Return a single session by native ID, or ``None``."""
        return next(
            (s for s in self.list_sessions(limit=1000) if s.id == session_id),
            None,
        )

    def list_events(self, session_id: str, limit: int = 500) -> List[Event]:
        """Return events for a session in chronological order."""
        return []

    def stream_events(self) -> Iterator[Event]:
        """Yield new events as they arrive. Blocking generator.

        Default implementation yields nothing — adapters that cannot
        stream live should simply not override this, and the UI will
        fall back to polling :meth:`list_events`.
        """
        return iter(())

    @abstractmethod
    def capabilities(self) -> Set[Capability]:
        """Return the set of :class:`Capability` flags this adapter exposes."""
        ...

    def running(self) -> bool:
        """Best-effort liveness check. Default: delegate to detect()."""
        try:
            return self.detect().running
        except Exception:
            return False
