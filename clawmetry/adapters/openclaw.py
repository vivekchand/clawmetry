"""OpenClawAdapter — thin wrapper around existing dashboard.py helpers.

This adapter does NOT re-implement OpenClaw session parsing. It delegates
to the long-standing helpers in ``dashboard.py`` via a late import, the
same way ``routes/*.py`` modules do. The point of this file is to expose
the existing OpenClaw observability surface through the unified
:class:`~clawmetry.adapters.base.AgentAdapter` interface, so the dashboard
treats OpenClaw exactly like any other agent.

Zero behavior change: when no other adapter is registered, the UI looks
identical to the pre-refactor dashboard.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Set

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.openclaw")


def _d():
    """Late import to avoid circular init with dashboard module."""
    import dashboard as _dash

    return _dash


class OpenClawAdapter(AgentAdapter):
    name = "openclaw"
    display_name = "OpenClaw"

    def detect(self) -> DetectResult:
        try:
            d = _d()
            workspace = getattr(d, "WORKSPACE", None) or ""
            sessions_dir = getattr(d, "SESSIONS_DIR", None) or ""
            gateway_url = getattr(d, "GATEWAY_URL", None) or ""
            sessions = []
            try:
                sessions = d._get_sessions() or []
            except Exception as exc:
                logger.debug(f"OpenClaw _get_sessions() failed in detect: {exc}")

            default_home = os.path.expanduser("~/.openclaw")
            detected = bool(
                sessions
                or (workspace and os.path.isdir(workspace))
                or (sessions_dir and os.path.isdir(sessions_dir))
                or os.path.isdir(default_home)
            )
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=bool(gateway_url),
                workspace=workspace or default_home,
                session_count=len(sessions),
                capabilities=[c.value for c in self.capabilities()],
                meta={
                    "gatewayUrl": gateway_url,
                    "sessionsDir": sessions_dir,
                },
            )
        except Exception as exc:
            logger.warning(f"OpenClaw detect() raised: {exc}")
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> List[Session]:
        try:
            raw = _d()._get_sessions() or []
        except Exception as exc:
            logger.warning(f"OpenClaw list_sessions() failed: {exc}")
            return []
        out: List[Session] = []
        for s in raw[:limit]:
            updated_ms = s.get("updatedAt") or 0
            started_at = (updated_ms / 1000.0) if updated_ms else 0.0
            out.append(
                Session(
                    agent=self.name,
                    id=s.get("sessionId") or s.get("key") or "",
                    display_name=s.get("displayName") or "",
                    model=s.get("model") or "",
                    source=s.get("channel") or "",
                    started_at=started_at,
                    total_tokens=int(s.get("totalTokens") or 0),
                    extra={
                        "kind": s.get("kind") or "direct",
                        "contextTokens": s.get("contextTokens"),
                        "agentId": s.get("agent") or "main",
                    },
                )
            )
        return out

    def read_session(self, session_id: str) -> Optional[Session]:
        for s in self.list_sessions(limit=1000):
            if s.id == session_id or s.id.startswith(session_id):
                return s
        return None

    def list_events(self, session_id: str, limit: int = 500) -> List[Event]:
        # PR 1 scope: events endpoint delegates to existing OpenClaw routes.
        # Full event normalization into the unified schema is deferred to the
        # follow-up PR that actually renders events in the per-agent session
        # view; OpenClaw already has rich transcript endpoints users hit via
        # the existing Sessions tab.
        return []

    def capabilities(self) -> Set[Capability]:
        return {
            Capability.SESSIONS,
            Capability.EVENTS,
            Capability.COST,
            Capability.SUBAGENTS,
            Capability.CRONS,
            Capability.SKILLS,
            Capability.MEMORY,
            Capability.BRAIN,
            Capability.LOGS,
            Capability.GATEWAY_RPC,
            Capability.CHANNELS,
        }

    def running(self) -> bool:
        try:
            return bool(getattr(_d(), "GATEWAY_URL", None))
        except Exception:
            return False
