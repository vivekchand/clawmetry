"""Local filesystem data provider — reads directly from ~/.openclaw files."""
from __future__ import annotations
import glob
import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from clawmetry.providers.base import (
    ClawMetryDataProvider, Event, LogEntry, MemoryFile, MetricPoint, Session
)

_MEMORY_FILE_NAMES = [
    "MEMORY.md", "SOUL.md", "IDENTITY.md", "USER.md",
    "AGENTS.md", "TOOLS.md", "HEARTBEAT.md", "BOOTSTRAP.md",
]


class LocalDataProvider(ClawMetryDataProvider):
    """
    Reads data directly from local OpenClaw filesystem paths.
    Mirrors existing dashboard.py file-reading behavior exactly.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sessions_index_cache: Optional[Dict] = None
        self._sessions_index_mtime: float = 0

    # ── Sessions ──────────────────────────────────────────────────────────────

    def _sessions_index_path(self) -> str:
        return os.path.join(self.sessions_dir, "sessions.json") if self.sessions_dir else ""

    def get_session_index(self) -> Dict[str, Dict]:
        idx_path = self._sessions_index_path()
        if not idx_path or not os.path.exists(idx_path):
            return {}
        try:
            mtime = os.path.getmtime(idx_path)
            if mtime != self._sessions_index_mtime:
                with open(idx_path, "r", encoding="utf-8") as f:
                    self._sessions_index_cache = json.load(f)
                self._sessions_index_mtime = mtime
        except Exception:
            self._sessions_index_cache = {}
        return self._sessions_index_cache or {}

    def list_sessions(self, limit: int = 30, include_subagents: bool = True,
                      since_ms: Optional[int] = None) -> List[Session]:
        index = self.get_session_index()
        sessions = []
        for key, meta in index.items():
            if not isinstance(meta, dict):
                continue
            sid = meta.get("sessionId", key)
            updated = meta.get("updatedAt", 0)
            if since_ms and updated < since_ms:
                continue
            is_subagent = ":subagent:" in key
            if not include_subagents and is_subagent:
                continue
            kind = "subagent" if is_subagent else "cron" if ":cron:" in key else "direct"
            sessions.append(Session(
                session_id=sid,
                display_name=meta.get("label") or meta.get("displayName") or key[:40],
                model=meta.get("model", "unknown"),
                channel=meta.get("lastChannel") or meta.get("channel", "unknown"),
                updated_at=updated,
                total_tokens=meta.get("totalTokens", 0) or 0,
                kind=kind,
                label=meta.get("label", ""),
                extra=meta,
            ))
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    def get_session(self, session_id: str) -> Optional[Session]:
        index = self.get_session_index()
        for key, meta in index.items():
            if not isinstance(meta, dict):
                continue
            if meta.get("sessionId", key) == session_id:
                is_subagent = ":subagent:" in key
                kind = "subagent" if is_subagent else "cron" if ":cron:" in key else "direct"
                return Session(
                    session_id=session_id,
                    display_name=meta.get("label") or meta.get("displayName") or key[:40],
                    model=meta.get("model", "unknown"),
                    channel=meta.get("lastChannel") or meta.get("channel", "unknown"),
                    updated_at=meta.get("updatedAt", 0),
                    total_tokens=meta.get("totalTokens", 0) or 0,
                    kind=kind,
                    label=meta.get("label", ""),
                    extra=meta,
                )
        return None

    # ── Events ────────────────────────────────────────────────────────────────

    def get_events(self, session_id: str, limit: int = 500,
                   tail_bytes: Optional[int] = None) -> List[Event]:
        if not self.sessions_dir:
            return []
        jsonl_path = os.path.join(self.sessions_dir, f"{session_id}.jsonl")
        if not os.path.exists(jsonl_path):
            return []
        events = []
        try:
            with open(jsonl_path, "rb") as f:
                if tail_bytes:
                    size = f.seek(0, 2)
                    f.seek(max(0, size - tail_bytes))
                    f.readline()  # skip partial line
                raw = f.read().decode("utf-8", errors="replace")
            for i, line in enumerate(raw.splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ev_type = obj.get("type", "unknown")
                ts = obj.get("timestamp") or obj.get("ts") or ""
                events.append(Event(
                    event_id=f"{session_id}:{i}",
                    session_id=session_id,
                    event_type=ev_type,
                    ts=ts,
                    data=obj,
                ))
        except Exception:
            pass
        return events[-limit:]

    # ── Logs ──────────────────────────────────────────────────────────────────

    def _log_file_path(self, date_str: str) -> Optional[str]:
        if not self.log_dir:
            return None
        for prefix in ("openclaw", "moltbot"):
            p = os.path.join(self.log_dir, f"{prefix}-{date_str}.log")
            if os.path.exists(p):
                return p
        return None

    def get_log_lines(self, date_str: Optional[str] = None, limit: int = 1000) -> List[str]:
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self._log_file_path(date_str)
        if not path:
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            return [l.rstrip("\n") for l in lines[-limit:]]
        except Exception:
            return []

    def list_log_dates(self, days_back: int = 31) -> List[str]:
        dates = []
        today = datetime.now(timezone.utc)
        for i in range(days_back):
            ds = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if self._log_file_path(ds):
                dates.append(ds)
        return dates

    # ── Memory / Workspace ────────────────────────────────────────────────────

    def list_memory_files(self) -> List[MemoryFile]:
        files = []
        if not self.workspace:
            return files
        # Named files at workspace root
        for name in _MEMORY_FILE_NAMES:
            p = os.path.join(self.workspace, name)
            if os.path.exists(p):
                stat = os.stat(p)
                files.append(MemoryFile(
                    path=name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                ))
        # Daily notes in memory/ subdir
        mem_dir = os.path.join(self.workspace, "memory")
        if os.path.isdir(mem_dir):
            for fname in sorted(os.listdir(mem_dir), reverse=True):
                if fname.endswith(".md"):
                    p = os.path.join(mem_dir, fname)
                    stat = os.stat(p)
                    files.append(MemoryFile(
                        path=f"memory/{fname}",
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    ))
        return files

    def read_workspace_file(self, relative_path: str) -> str:
        if not self.workspace:
            return ""
        # Security: prevent path traversal
        full = os.path.realpath(os.path.join(self.workspace, relative_path))
        if not full.startswith(os.path.realpath(self.workspace)):
            raise ValueError(f"Path traversal blocked: {relative_path!r}")
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    # ── Crons ─────────────────────────────────────────────────────────────────

    def list_crons(self) -> List[Dict[str, Any]]:
        # Try cron/jobs.json relative to parent of workspace
        candidates = []
        if self.workspace:
            base = os.path.dirname(self.workspace)
            candidates.append(os.path.join(base, "cron", "jobs.json"))
        candidates += [
            os.path.expanduser("~/.openclaw/cron/jobs.json"),
            os.path.expanduser("~/.clawdbot/cron/jobs.json"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("jobs", [])
                except Exception:
                    pass
        return []

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "LocalDataProvider",
            "ok": True,
            "sessions_dir": self.sessions_dir,
            "sessions_dir_exists": os.path.isdir(self.sessions_dir) if self.sessions_dir else False,
            "log_dir": self.log_dir,
            "log_dir_exists": os.path.isdir(self.log_dir) if self.log_dir else False,
            "workspace": self.workspace,
            "workspace_exists": os.path.isdir(self.workspace) if self.workspace else False,
        }
