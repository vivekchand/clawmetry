"""
clawmetry_nat/mapper.py

Maps NVIDIA NeMo Agent Toolkit IntermediateStep events to ClawMetry's
brain event schema.

NAT event types (from nat.data_models.intermediate_step):
  - WORKFLOW_START / WORKFLOW_END       → session start / session end
  - LLM_START / LLM_END                → turn event with token counts
  - TOOL_START / TOOL_END              → tool event
  - task_start / task_end              → session boundaries (legacy API)
  - llm_call, tool_call                → core agent operations

ClawMetry brain event fields (subset):
  type, session_id, timestamp, data: {
    role, model, content, usage: {input, output, cacheRead, cacheWrite, cost}
    tool_name, tool_input, tool_output, duration_ms, error
  }
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_str(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    s = str(value)
    return s[:limit] if len(s) > limit else s


class NATEventMapper:
    """
    Converts NAT IntermediateStep objects (or plain dicts) to ClawMetry events.

    Usage:
        mapper = NATEventMapper(session_id="my-session")
        claw_event = mapper.map(nat_step)
    """

    # NAT event type strings — cover both the enum names and string keys
    WORKFLOW_START_TYPES = {
        "WORKFLOW_START",
        "workflow_start",
        "task_start",
        "TASK_START",
    }
    WORKFLOW_END_TYPES = {"WORKFLOW_END", "workflow_end", "task_end", "TASK_END"}
    LLM_START_TYPES = {"LLM_START", "llm_start", "llm_call"}
    LLM_END_TYPES = {"LLM_END", "llm_end", "llm_response"}
    TOOL_START_TYPES = {"TOOL_START", "tool_start", "tool_call"}
    TOOL_END_TYPES = {"TOOL_END", "tool_end", "tool_result"}

    def __init__(self, session_id: Optional[str] = None, model: str = "nat-agent"):
        self.session_id = session_id or str(uuid.uuid4())
        self.model = model
        # Track open LLM/tool spans so we can compute durations on END events
        self._llm_spans: Dict[str, float] = {}  # span_id → start_time_ms
        self._tool_spans: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map(self, step: Any) -> Optional[Dict[str, Any]]:
        """
        Map a NAT step to a ClawMetry event dict.

        Accepts:
        - NAT IntermediateStep objects (with .event_type / .name / .metadata attrs)
        - Plain dicts with 'event_type' key
        - Returns None if the step is not mappable.
        """
        event_type = self._get_event_type(step)
        if not event_type:
            return None

        if event_type in self.WORKFLOW_START_TYPES:
            return self._map_session_start(step)
        if event_type in self.WORKFLOW_END_TYPES:
            return self._map_session_end(step)
        if event_type in self.LLM_START_TYPES:
            return self._map_llm_start(step)
        if event_type in self.LLM_END_TYPES:
            return self._map_llm_end(step)
        if event_type in self.TOOL_START_TYPES:
            return self._map_tool_start(step)
        if event_type in self.TOOL_END_TYPES:
            return self._map_tool_end(step)
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_event_type(self, step: Any) -> Optional[str]:
        """Extract event_type string from a NAT step (object or dict)."""
        if isinstance(step, dict):
            et = step.get("event_type") or step.get("type") or ""
            # Could be an enum value with .value
            return str(et.value) if hasattr(et, "value") else str(et)
        # NAT IntermediateStep object
        et = getattr(step, "event_type", None) or getattr(step, "type", None)
        if et is None:
            return ""
        return str(et.value) if hasattr(et, "value") else str(et)

    def _get_metadata(self, step: Any) -> Dict[str, Any]:
        if isinstance(step, dict):
            return step.get("metadata") or step.get("data") or {}
        return getattr(step, "metadata", None) or {}

    def _get_name(self, step: Any) -> str:
        if isinstance(step, dict):
            return step.get("name", "")
        return getattr(step, "name", "") or ""

    def _get_span_id(self, step: Any) -> str:
        """Extract or synthesise a span ID for duration tracking."""
        meta = self._get_metadata(step)
        return (
            meta.get("span_id")
            or meta.get("run_id")
            or meta.get("trace_id")
            or self._get_name(step)
            or str(uuid.uuid4())
        )

    def _base_event(self, etype: str) -> Dict[str, Any]:
        return {
            "type": etype,
            "session_id": self.session_id,
            "timestamp": _now_iso(),
            "source": "nat",
        }

    # ── Session events ────────────────────────────────────────────────

    def _map_session_start(self, step: Any) -> Dict[str, Any]:
        meta = self._get_metadata(step)
        ev = self._base_event("session")
        ev["data"] = {
            "event": "start",
            "label": meta.get("workflow_name")
            or self._get_name(step)
            or "nat-workflow",
            "model": meta.get("model") or self.model,
            "nat_config": meta.get("config") or {},
        }
        return ev

    def _map_session_end(self, step: Any) -> Dict[str, Any]:
        meta = self._get_metadata(step)
        ev = self._base_event("session")
        ev["data"] = {
            "event": "end",
            "label": meta.get("workflow_name")
            or self._get_name(step)
            or "nat-workflow",
            "summary": {
                "total_tokens": meta.get("total_tokens") or 0,
                "total_cost": meta.get("total_cost") or 0.0,
                "status": meta.get("status") or "completed",
                "error": _safe_str(meta.get("error")),
            },
        }
        return ev

    # ── LLM events ────────────────────────────────────────────────────

    def _map_llm_start(self, step: Any) -> Dict[str, Any]:
        span_id = self._get_span_id(step)
        self._llm_spans[span_id] = time.monotonic() * 1000

        meta = self._get_metadata(step)
        ev = self._base_event("message")
        ev["message"] = {
            "role": "user",
            "content": _safe_str(meta.get("prompt") or meta.get("input") or ""),
            "model": meta.get("model") or self.model,
        }
        ev["_span_id"] = span_id
        return ev

    def _map_llm_end(self, step: Any) -> Dict[str, Any]:
        span_id = self._get_span_id(step)
        started_ms = self._llm_spans.pop(span_id, None)
        duration_ms = int(time.monotonic() * 1000 - started_ms) if started_ms else 0

        meta = self._get_metadata(step)

        # Token usage — NAT stores these under various key names
        tok_in = (
            meta.get("input_tokens")
            or meta.get("prompt_tokens")
            or meta.get("tokens_input")
            or 0
        )
        tok_out = (
            meta.get("output_tokens")
            or meta.get("completion_tokens")
            or meta.get("tokens_output")
            or 0
        )

        # Cost — NAT may give us a cost dict or a scalar
        cost_raw = meta.get("cost") or meta.get("total_cost") or 0.0
        cost = (
            float(cost_raw)
            if isinstance(cost_raw, (int, float))
            else (
                float(cost_raw.get("total", 0)) if isinstance(cost_raw, dict) else 0.0
            )
        )

        ev = self._base_event("message")
        ev["message"] = {
            "role": "assistant",
            "content": _safe_str(
                meta.get("output") or meta.get("response") or meta.get("text") or ""
            ),
            "model": meta.get("model") or self.model,
            "usage": {
                "input": int(tok_in),
                "output": int(tok_out),
                "cacheRead": int(meta.get("cache_read_tokens") or 0),
                "cacheWrite": int(meta.get("cache_write_tokens") or 0),
                "cost": {"total": cost},
            },
        }
        ev["durationMs"] = duration_ms
        return ev

    # ── Tool events ───────────────────────────────────────────────────

    def _map_tool_start(self, step: Any) -> Dict[str, Any]:
        span_id = self._get_span_id(step)
        self._tool_spans[span_id] = time.monotonic() * 1000

        meta = self._get_metadata(step)
        name = self._get_name(step) or meta.get("tool_name") or "unknown_tool"

        ev = self._base_event("message")
        ev["message"] = {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "name": name,
                    "arguments": meta.get("tool_input")
                    or meta.get("args")
                    or meta.get("inputs")
                    or {},
                }
            ],
            "model": self.model,
        }
        ev["_span_id"] = span_id
        return ev

    def _map_tool_end(self, step: Any) -> Dict[str, Any]:
        span_id = self._get_span_id(step)
        started_ms = self._tool_spans.pop(span_id, None)
        duration_ms = int(time.monotonic() * 1000 - started_ms) if started_ms else 0

        meta = self._get_metadata(step)
        name = self._get_name(step) or meta.get("tool_name") or "unknown_tool"
        error = meta.get("error")

        ev = self._base_event("message")
        ev["message"] = {
            "role": "tool",
            "content": [
                {
                    "type": "toolResult",
                    "name": name,
                    "output": _safe_str(
                        meta.get("tool_output")
                        or meta.get("output")
                        or meta.get("result")
                    ),
                    "error": _safe_str(error) if error else None,
                }
            ],
            "model": self.model,
        }
        ev["durationMs"] = duration_ms
        return ev
