"""Abstract data provider interface for ClawMetry."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Session:
    session_id: str
    display_name: str
    model: str
    channel: str
    updated_at: int
    total_tokens: int = 0
    kind: str = "direct"
    label: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    event_id: str
    session_id: str
    event_type: str
    ts: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    ts: str
    level: str
    message: str
    channel: Optional[str] = None
    session_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryFile:
    path: str
    size: int
    modified: Optional[str] = None
    content: Optional[str] = None


@dataclass
class MetricPoint:
    metric_type: str
    ts: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class ClawMetryDataProvider(ABC):
    """
    Abstract data provider for ClawMetry.

    OSS ships LocalDataProvider (reads ~/.openclaw files directly).
    Cloud implements TursoDataProvider in the private clawmetry-cloud package.

    All methods are synchronous. Cloud providers use connection pooling internally.
    """

    def __init__(self, sessions_dir: str = "", log_dir: str = "",
                 workspace: str = "", metrics_file: str = "",
                 fleet_db: str = "", **kwargs):
        self.sessions_dir = sessions_dir
        self.log_dir = log_dir
        self.workspace = workspace
        self.metrics_file = metrics_file
        self.fleet_db = fleet_db

    # ── Sessions ──────────────────────────────────────────────────────────────

    @abstractmethod
    def list_sessions(self, limit: int = 30, include_subagents: bool = True,
                      since_ms: Optional[int] = None) -> List[Session]:
        """Return recent sessions, newest first."""
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Return a single session by ID."""
        ...

    @abstractmethod
    def get_session_index(self) -> Dict[str, Dict]:
        """Return sessions.json-style map: session_key → metadata dict."""
        ...

    # ── Events ────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_events(self, session_id: str, limit: int = 500,
                   tail_bytes: Optional[int] = None) -> List[Event]:
        """Return events for a session. tail_bytes: read only last N bytes of JSONL."""
        ...

    # ── Logs ──────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_log_lines(self, date_str: Optional[str] = None,
                      limit: int = 1000) -> List[str]:
        """Return raw log lines for a date (YYYY-MM-DD). None = today."""
        ...

    @abstractmethod
    def list_log_dates(self, days_back: int = 31) -> List[str]:
        """Return list of YYYY-MM-DD strings that have log data."""
        ...

    # ── Memory / Workspace ────────────────────────────────────────────────────

    @abstractmethod
    def list_memory_files(self) -> List[MemoryFile]:
        """Return workspace memory files with metadata."""
        ...

    @abstractmethod
    def read_workspace_file(self, relative_path: str) -> str:
        """Return content of a file relative to workspace root."""
        ...

    # ── Crons ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def list_crons(self) -> List[Dict[str, Any]]:
        """Return cron job definitions."""
        ...

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Return health status. Override for custom checks."""
        return {"provider": self.__class__.__name__, "ok": True}
