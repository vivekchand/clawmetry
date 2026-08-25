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

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator

from . import phase as _phase


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
class LogSource:
    """One place an adapter's runtime logs can be read from.

    ``kind`` is ``"file"`` (tail/follow ``path``) or ``"command"`` (run
    ``command`` and capture stdout). Command args may contain the literal
    placeholder ``"{lines}"`` which the log reader substitutes with the
    requested tail line count (e.g. ``["docker", "logs", "--tail",
    "{lines}", name]``). ``follow_command`` is an optional follow-style
    variant (``--follow`` / ``-f``) used by the SSE stream; command
    sources without one cannot be live-followed and the stream falls
    back to the file ``path`` when present.

    ``format`` is a rendering hint only: ``"text"`` (plain lines) or
    ``"jsonl"`` (one JSON object per line).

    HONESTY CONTRACT: adapters must only return sources that actually
    exist / are runnable right now — a missing log file means an empty
    list, never an invented path.
    """

    id: str
    label: str
    kind: str  # 'file' | 'command'
    path: str | None = None
    command: list[str] | None = None
    follow_command: list[str] | None = None
    format: str = "text"  # 'text' | 'jsonl'

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "path": self.path,
            "command": self.command,
            "followCommand": self.follow_command,
            "format": self.format,
        }


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
    ended_at: float | None = None
    parent_id: str | None = None
    message_count: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float | None = None
    cost_status: str = ""
    # Why the session ended, in the RUNTIME's own words where it has any
    # (``user_stopped``, ``max_turns``, ``turn_aborted:interrupted``). Where a
    # runtime states none, ``resolve_phase`` fills one of the shared reasons in
    # ``clawmetry.adapters.phase.END_REASONS``; an adapter's own account of
    # what happened is never overwritten.
    end_reason: str = ""
    # Working directory the session ran in ("" when the runtime hides it).
    # First-class because kill/pause pid resolution keys on it
    # (process_control.resolve_by_cwd); adapters should ALSO mirror it into
    # extra["cwd"] while older OSS wheels without this field are in the
    # fleet (a pro adapter passing cwd= against an old wheel would crash).
    cwd: str = ""

    # ── Phase model (see clawmetry/adapters/phase.py) ─────────────────────
    # An adapter that can see its runtime's state sets ``phase`` (and
    # ``status`` where it can see more) directly. One that cannot leaves both
    # empty and ``resolve_phase`` derives what it can from the timestamps.
    # ``None`` after resolution means the observed data could not establish a
    # phase. That is an answer, and it is deliberately not ``idle``.
    phase: str | None = None
    status: str | None = None
    # When the session entered ``phase``. Filled from the DURABLE record
    # (``local_store.record_session_phase``), never recomputed per pass: a
    # daemon restart must not reset "waiting on you for 14 minutes" to zero.
    phase_since: float | None = None
    # How the phase was reached (``adapter`` / ``status`` / ``recency`` / ...)
    # so a reader can tell an asserted phase from a derived one.
    phase_basis: str = ""
    # Last observed activity. Falls back to ``ended_at``, which is what most
    # adapters actually put there (the last event timestamp, or the file
    # mtime) -- NOT an assertion that the session is over.
    last_activity_at: float | None = None
    # Can a pending ask be answered from ClawMetry? ``None`` = not known.
    # Keeps "a control that cannot work must say why" structural rather than a
    # convention each surface can forget.
    resolvable: bool | None = None
    # The directory the session was LAUNCHED in, set once at first observation
    # and never overwritten, so it stays comparable against ``cwd`` (where the
    # session is running now). Landing the field is this work order; the drift
    # comparison that uses it is a later one.
    initial_cwd: str = ""

    extra: dict[str, Any] = field(default_factory=dict)

    def observed_activity_at(self) -> float | None:
        """Best last-activity timestamp this session carries.

        ``ended_at`` is the fallback on purpose: across every shipped adapter
        it holds the last event timestamp (or the file mtime), i.e. the newest
        thing observed, not a claim that the session finished. Only
        ``end_reason`` asserts an end.
        """
        if self.last_activity_at:
            return self.last_activity_at
        return self.ended_at or (self.started_at or None)

    def resolve_phase(self, *, now: float | None = None, pid_alive=None):
        """Fill ``phase`` / ``status`` / ``phase_basis`` / ``end_reason`` in place.

        Idempotent: an adapter that already set ``phase`` keeps it (the
        verdict's first rule is that the adapter wins). Deliberately does NOT
        set ``phase_since`` -- that comes from the durable record, because a
        value recomputed here would reset on every daemon restart.

        ``pid_alive`` is injected rather than imported so the adapter layer
        stays free of process syscalls; the daemon passes
        ``process_control.is_alive``.

        Returns the :class:`clawmetry.adapters.phase.PhaseVerdict`.
        """
        if self.phase_basis:
            # Already resolved. Re-deriving would read our own derived phase
            # back as an adapter assertion and launder a ``recency`` verdict
            # into an ``adapter`` one, which is exactly the provenance the
            # basis exists to keep straight.
            return _phase.PhaseVerdict(self.phase, self.status,
                                       self.end_reason, self.phase_basis)
        extra = self.extra if isinstance(self.extra, dict) else {}
        verdict = _phase.resolve(
            now=now if now is not None else time.time(),
            phase=self.phase,
            status=self.status,
            end_reason=self.end_reason,
            last_activity_at=self.observed_activity_at(),
            started_at=self.started_at or None,
            archived=bool(extra.get("archived")),
            pid=extra.get("pid"),
            pid_alive=pid_alive,
        )
        self.phase = verdict.phase
        self.status = verdict.status
        self.phase_basis = verdict.basis
        if verdict.end_reason and not self.end_reason:
            self.end_reason = verdict.end_reason
        if not self.initial_cwd:
            # ONLY from an adapter that genuinely knows the launch directory.
            # Not defaulted to ``cwd`` HERE: this object is rebuilt on every
            # pass, so seeding from wherever the session is running now would
            # re-seed it every time and the two would be equal by construction.
            # The first-observation seed belongs in the durable record
            # (``local_store.record_session_phase``), which CAN tell a first
            # sighting from a re-read and freezes the value it seeds.
            launch = extra.get("initialCwd") or extra.get("initial_cwd") or ""
            self.initial_cwd = str(launch or "")[:1024]
        return verdict

    def to_dict(self) -> dict[str, Any]:
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
            "cwd": self.cwd,
            "phase": self.phase,
            "status": self.status,
            "phaseSince": self.phase_since,
            "phaseBasis": self.phase_basis,
            "lastActivityAt": self.observed_activity_at(),
            "resolvable": self.resolvable,
            "initialCwd": self.initial_cwd,
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
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    parent_id: str | None = None
    tokens: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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
    capabilities: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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
    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Empty list if none."""
        ...

    def read_session(self, session_id: str) -> Session | None:
        """Return a single session by native ID, or ``None``."""
        return next(
            (s for s in self.list_sessions(limit=1000) if s.id == session_id),
            None,
        )

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Return events for a session in chronological order."""
        return []

    def stream_events(self) -> Iterator[Event]:
        """Yield new events as they arrive. Blocking generator.

        Default implementation yields nothing — adapters that cannot
        stream live should simply not override this, and the UI will
        fall back to polling :meth:`list_events`.
        """
        return iter(())

    def log_sources(self) -> list[LogSource]:
        """Return the runtime's readable log sources, best-first.

        Default: none — the Logs tab shows an honest "no log stream"
        state. Adapters that return a non-empty list should also include
        :attr:`Capability.LOGS` in :meth:`capabilities` so the UI gates
        the tab correctly. Must be cheap and must never raise; only
        return sources that exist right now (see :class:`LogSource`).
        """
        return []

    @abstractmethod
    def capabilities(self) -> set[Capability]:
        """Return the set of :class:`Capability` flags this adapter exposes."""
        ...

    def running(self) -> bool:
        """Best-effort liveness check. Default: delegate to detect()."""
        try:
            return self.detect().running
        except Exception:
            return False
