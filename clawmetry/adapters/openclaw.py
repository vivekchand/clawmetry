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

import hashlib
import json
import logging
import os
import time as _time
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

    # ── Span reconstruction (issue #1010 / Trace 4) ────────────────────────

    @staticmethod
    def _span_id(*parts: str) -> str:
        return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]

    @staticmethod
    def _trace_id(session_id: str) -> str:
        return hashlib.sha256(session_id.encode()).hexdigest()[:32]

    @staticmethod
    def _build_spans_from_events(events: list, session_id: str) -> list:
        """Map raw JSONL objects to OTel-shaped span dicts.

        Mapping per issue #1010:
        - ``session`` (version set)   → root span (INTERNAL)
        - ``message`` (role=assistant) → llm.call span (CLIENT, child of root)
          - each tool_use block       → tool.<name> span (CLIENT, child of llm)
        - ``subagent_spawn``          → agent.spawn span (INTERNAL, link to child trace)

        Span IDs are deterministic SHA-256 prefixes so re-ingesting is idempotent.
        """
        _sid = OpenClawAdapter._span_id
        trace_id = OpenClawAdapter._trace_id(session_id)
        session_span_id = _sid("session", session_id)
        now = _time.time()
        spans: list = []

        for obj in events:
            if not isinstance(obj, dict):
                continue
            t = obj.get("type")
            raw_ts = obj.get("timestamp") or obj.get("ts") or now
            try:
                ts = float(raw_ts)
            except (TypeError, ValueError):
                ts = now

            if t == "session" and obj.get("version") is not None:
                spans.append({
                    "span_id": session_span_id,
                    "trace_id": trace_id,
                    "name": "session",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "attributes": {"session.version": obj.get("version"), "session.id": session_id},
                })

            elif t == "message" and isinstance(obj.get("message"), dict):
                msg = obj["message"]
                if msg.get("role") != "assistant":
                    continue
                model = msg.get("model") or ""
                usage = msg.get("usage") or {}
                tok_in = int(usage.get("input_tokens") or usage.get("inputTokens") or 0)
                tok_out = int(usage.get("output_tokens") or usage.get("outputTokens") or 0)
                llm_sid = _sid("llm", session_id, str(raw_ts))
                spans.append({
                    "span_id": llm_sid,
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": f"llm.call {model}".strip() if model else "llm.call",
                    "kind": "CLIENT",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "model": model or None,
                    "tokens_input": tok_in or None,
                    "tokens_output": tok_out or None,
                    "token_count": (tok_in + tok_out) or None,
                })
                content = msg.get("content") or []
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        tool_name = block.get("name") or "tool"
                        tool_id = block.get("id") or ""
                        spans.append({
                            "span_id": _sid("tool", session_id, str(raw_ts), tool_id, tool_name),
                            "trace_id": trace_id,
                            "parent_span_id": llm_sid,
                            "name": f"tool.{tool_name}",
                            "kind": "CLIENT",
                            "start_ts": ts,
                            "session_id": session_id,
                            "agent_type": "openclaw",
                            "tool_name": tool_name,
                            "input": block.get("input"),
                        })

            elif t in ("subagent_spawn", "agent_spawn"):
                sub_id = (
                    obj.get("subagent_id") or obj.get("agentId") or obj.get("agent_id") or ""
                )
                child_trace = hashlib.sha256(sub_id.encode()).hexdigest()[:32] if sub_id else ""
                spans.append({
                    "span_id": _sid("spawn", session_id, str(raw_ts), sub_id),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "agent.spawn",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "links": [{"trace_id": child_trace, "span_id": "0" * 16}] if child_trace else None,
                    "attributes": {"subagent_id": sub_id} if sub_id else None,
                })

        return spans

    def reconstruct_spans(self, jsonl_path: str) -> list:
        """Read an OpenClaw JSONL transcript and return OTel-shaped span dicts.

        The returned list can be fed directly to ``local_store.ingest_span()``.
        Returns an empty list and logs a warning on I/O errors.
        """
        session_id = os.path.basename(jsonl_path).split(".jsonl", 1)[0]
        try:
            with open(jsonl_path, encoding="utf-8", errors="replace") as fh:
                events = []
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as exc:
            logger.warning("reconstruct_spans: cannot read %s: %s", jsonl_path, exc)
            return []
        return self._build_spans_from_events(events, session_id)

    def running(self) -> bool:
        try:
            return bool(getattr(_d(), "GATEWAY_URL", None))
        except Exception:
            return False
