"""NeMoAdapter — push-mode telemetry exporter for NVIDIA's NeMo Agent Toolkit.

Issue #234. NVIDIA's NeMo Agent Toolkit (a.k.a. "NAT") emits OpenTelemetry-
style spans/events through its ``nemo_toolkit.observability`` module. Many
ClawMetry users run NeMo agents alongside or instead of OpenClaw; this
adapter lets ClawMetry ingest those events without requiring NeMo to be
installed in the dashboard process.

Design — different from the other adapters in this package
----------------------------------------------------------
The :class:`~clawmetry.adapters.base.AgentAdapter` subclasses (Hermes,
OpenClaw) are *pull*-mode: they own a filesystem location and the dashboard
periodically asks them for sessions/events. NeMo, by contrast, is *push*-
mode: it emits events into a callback bus and we have to subscribe. So
:class:`NeMoAdapter` does not subclass ``AgentAdapter`` — it is a thin
callback receiver that maps NeMo event dicts onto the same dot.separated
``event_type`` taxonomy that ``clawmetry/sync.py::_parse_v3_event`` uses
for OpenClaw v3 and writes them to the local DuckDB via
``LocalStore.ingest``. The dashboard's existing brain feed, transcript
view, and analytics queries all read from that table, so NeMo data is
surfaced everywhere OpenClaw data is, with zero new read paths.

Assumed NeMo event shape
------------------------
NeMo's plugin SDK is still evolving and there is no stable Python-side
contract we can pin. We duck-type the OpenTelemetry-span-flavoured shape
that the toolkit currently emits — and that NeMo's own bundled exporters
(Phoenix, Langfuse, W&B Weave) consume — so the adapter works against
multiple NeMo versions without a hard ``import nemo_toolkit``::

    {
        "event_type": "LLM_START" | "LLM_END" | "TOOL_START" | "TOOL_END"
                      | "WORKFLOW_START" | "WORKFLOW_END",
        # OTel-flavoured span fields:
        "name": "claude-3.5-sonnet" | "tavily_search" | "research_workflow",
        "span_id": "…",            # stable across START/END
        "trace_id": "…",           # = ClawMetry session_id
        "start_time": <epoch_ms> | <iso8601>,
        "end_time":   <epoch_ms> | <iso8601>,   # END events only
        "attributes": {
            # LLM:
            "model": "claude-3.5-sonnet",
            "prompt": "…",                  # LLM_START
            "completion": "…",              # LLM_END
            "input_tokens": 512,            # LLM_END (also "prompt_tokens")
            "output_tokens": 128,           # LLM_END (also "completion_tokens")
            "cost_usd": 0.0032,             # LLM_END (optional)
            # TOOL:
            "tool_name": "tavily_search",
            "tool_input": {…},              # TOOL_START
            "tool_output": "…",             # TOOL_END
            "error": "…",                   # any (optional)
            # WORKFLOW:
            "workflow_name": "research",
        },
    }

Every field is optional. Unknown ``event_type`` values are logged at
``WARNING`` and dropped; malformed dicts never raise out of
:meth:`NeMoAdapter.on_event`. NeMo's native ``IntermediateStep`` objects
are also accepted — :meth:`on_event` reads attributes by name and falls
back to dict access, so the same code path handles both shapes.

Event-type mapping
------------------

================  ===========================
NeMo event_type    ClawMetry event_type
================  ===========================
WORKFLOW_START     ``session.started``
WORKFLOW_END       ``session.ended``
LLM_START          ``prompt.submitted``
LLM_END            ``model.completed``
TOOL_START         ``tool.call``
TOOL_END           ``tool.result``
================  ===========================

These match the values produced by ``_parse_v3_event`` for OpenClaw,
so the dashboard renders NeMo sessions identically to OpenClaw sessions.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger("clawmetry.adapters.nemo")


# NeMo event-type → ClawMetry dot.separated event_type.
#
# Both the SCREAMING_SNAKE form emitted by NeMo's IntermediateStepType
# enum *and* the lowercase form NeMo's tracing exporters sometimes emit
# are accepted, so we don't accidentally drop events on a version that
# normalises one but not the other. Mirrors NATEventMapper in the
# standalone ``integrations/nat`` PyPI package.
_EVENT_TYPE_MAP: dict[str, str] = {
    # Workflow lifecycle
    "WORKFLOW_START": "session.started",
    "workflow_start": "session.started",
    "TASK_START":     "session.started",
    "task_start":     "session.started",
    "WORKFLOW_END":   "session.ended",
    "workflow_end":   "session.ended",
    "TASK_END":       "session.ended",
    "task_end":       "session.ended",
    # LLM calls
    "LLM_START":   "prompt.submitted",
    "llm_start":   "prompt.submitted",
    "llm_call":    "prompt.submitted",
    "LLM_END":     "model.completed",
    "llm_end":     "model.completed",
    "llm_response": "model.completed",
    # Tool calls
    "TOOL_START":  "tool.call",
    "tool_start":  "tool.call",
    "tool_call":   "tool.call",
    "TOOL_END":    "tool.result",
    "tool_end":    "tool.result",
    "tool_result": "tool.result",
}

# Stable ordered list of unique ClawMetry event_types this adapter can emit.
# Tests + docs reference this — keep deduplicated.
MAPPED_EVENT_TYPES: tuple[str, ...] = (
    "session.started",
    "session.ended",
    "prompt.submitted",
    "model.completed",
    "tool.call",
    "tool.result",
)


def _now_iso() -> str:
    # Lazy import — keep top of module lean.
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _coerce_ts(value: Any) -> str:
    """Return an ISO-8601 timestamp string.

    Accepts:
      * ISO-8601 strings (passed through verbatim)
      * epoch seconds (int/float) — converted
      * epoch milliseconds (int/float, ``>= 1e11``) — converted
      * None / unparseable — falls back to "now"
    """
    if value is None or value == "":
        return _now_iso()
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        from datetime import datetime, timezone
        # Heuristic: anything past year ~5138 in seconds is almost
        # certainly milliseconds. NeMo's IntermediateStep currently uses
        # seconds (float), but some OTel SDKs emit nanoseconds — we
        # don't try to handle ns to avoid mis-classifying microsecond
        # epochs; callers can pre-normalise.
        v = float(value)
        if v >= 1e11:
            v /= 1000.0
        try:
            return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return _now_iso()
    return _now_iso()


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Duck-typed attribute/key lookup — works for dicts and namespace-ish
    objects (e.g. NeMo's ``IntermediateStep``)."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_event_type(event: Any) -> Optional[str]:
    """Pull the raw event_type string out of a NeMo event.

    Handles ``event_type``, ``type``, and the case where the value is an
    enum (``IntermediateStepType.LLM_END``) by reading ``.value`` /
    ``.name``.
    """
    raw = _get(event, "event_type") or _get(event, "type")
    if raw is None:
        return None
    if hasattr(raw, "value"):
        try:
            return str(raw.value)
        except Exception:
            pass
    if hasattr(raw, "name"):
        try:
            return str(raw.name)
        except Exception:
            pass
    return str(raw)


def _attrs(event: Any) -> dict:
    """Best-effort extraction of the OTel-style ``attributes`` dict.

    NeMo's plugin SDK has gone through three names for this field in
    recent versions — ``attributes`` (OTel-standard), ``metadata``
    (IntermediateStep), and ``payload`` (raw bus events) — so we try all
    three. Returns ``{}`` if none are present.
    """
    for key in ("attributes", "metadata", "payload", "data"):
        val = _get(event, key)
        if isinstance(val, dict):
            return val
    return {}


def _first(d: dict, *keys: str, default: Any = None) -> Any:
    """Return the first non-None value among ``d[keys[0]]``, ``d[keys[1]]``,
    … falling back to ``default``. Lets us accept multiple field names
    for the same concept (NeMo's evolved naming, OTel synonyms, etc.)
    without nested ``or`` chains that drop falsy-but-valid 0s."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class NeMoAdapter:
    """Receives NeMo Agent Toolkit events and writes them to ClawMetry's
    local DuckDB.

    Construct one of these in your NeMo bootstrap and pass
    :meth:`on_event` as the callback to whatever event source the
    toolkit exposes (e.g. ``IntermediateStepManager.subscribe`` or a
    custom ``TracingExporter``)::

        from clawmetry import local_store
        from clawmetry.adapters.nemo import NeMoAdapter

        adapter = NeMoAdapter(local_store.get_store())
        nat_manager.subscribe(adapter.on_event)

    The adapter holds no state across events except short-lived span
    timing bookkeeping; it is safe to share one instance across threads
    (``LocalStore.ingest`` is thread-safe via its internal ring buffer).
    """

    AGENT_TYPE = "nemo"

    def __init__(
        self,
        local_store: Any,
        *,
        node_id: str = "local",
        agent_id: str = "main",
        default_session_id: Optional[str] = None,
        default_model: str = "nemo-agent",
    ) -> None:
        """
        Args:
            local_store: a ``LocalStore`` (or any object exposing
                ``.ingest(event_dict)``). Pass ``clawmetry.local_store.get_store()``.
            node_id: ClawMetry node identifier — appears in the multi-node
                fleet view. Defaults to ``"local"``.
            agent_id: ClawMetry agent identifier (within the node). Defaults
                to ``"main"``.
            default_session_id: Session UUID used when an inbound event
                carries no ``trace_id`` / ``session_id``. Auto-generated.
            default_model: Model label used when an LLM event omits one.
        """
        self._store = local_store
        self._node_id = node_id
        self._agent_id = agent_id
        self._default_session_id = default_session_id or str(uuid.uuid4())
        self._default_model = default_model
        # span_id → start_time_iso, for stamping the START timestamp on
        # the matching END event (so duration analytics work even when
        # NeMo's exporter only stamps end_time on the END side).
        self._open_spans: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_event(self, event: Any) -> Optional[dict]:
        """Map ``event`` onto a ClawMetry row and ingest it.

        Returns the ingested row dict (handy for tests / inspection),
        or ``None`` if the event was skipped (unknown type, missing
        required fields, …). Never raises — internal errors are logged
        at ``WARNING`` and swallowed, because losing one telemetry event
        should never crash the host agent.
        """
        try:
            row = self.map_event(event)
        except Exception as exc:
            logger.warning("nemo adapter: map_event raised %r — dropping", exc)
            return None
        if row is None:
            return None
        try:
            self._store.ingest(row)
        except Exception as exc:
            logger.warning("nemo adapter: local_store.ingest raised %r", exc)
            return None
        return row

    def map_event(self, event: Any) -> Optional[dict]:
        """Pure mapping: NeMo event → ClawMetry row, no side-effects.

        Exposed for tests and for callers who want to inspect or
        post-process before ingest. ``on_event`` is just
        ``map_event`` + ``ingest``.
        """
        raw_type = _get_event_type(event)
        if not raw_type:
            return None
        mapped = _EVENT_TYPE_MAP.get(raw_type)
        if mapped is None:
            logger.warning(
                "nemo adapter: unknown event_type %r — dropping (known: %s)",
                raw_type,
                sorted(set(_EVENT_TYPE_MAP)),
            )
            return None

        attrs = _attrs(event)
        # session_id resolution — prefer the NeMo trace_id (groups all
        # events from one workflow run), then any session-id key the
        # caller set, then our adapter-wide default.
        session_id = (
            _get(event, "trace_id")
            or _first(attrs, "trace_id", "session_id", "workflow_id")
            or _get(event, "session_id")
            or self._default_session_id
        )
        span_id = _get(event, "span_id") or _first(attrs, "span_id") or str(uuid.uuid4())

        # Pick a timestamp. END events prefer end_time; START events
        # prefer start_time. Falls back to wall-clock now.
        if mapped in ("session.ended", "model.completed", "tool.result"):
            ts = _coerce_ts(_get(event, "end_time") or _get(event, "timestamp"))
        else:
            ts = _coerce_ts(_get(event, "start_time") or _get(event, "timestamp"))

        # Build the dot.separated row in the same shape sync.py's v3
        # parser produces (see _parse_v3_event). The dashboard's read
        # path treats agent_type="nemo" rows identically to OpenClaw
        # rows because they share this schema.
        row: dict = {
            "id": f"{session_id}:{span_id}:{mapped}:{ts}",
            "agent_type": self.AGENT_TYPE,
            "node_id": self._node_id,
            "agent_id": self._agent_id,
            "session_id": str(session_id),
            "workspace_id": None,
            "event_type": mapped,
            "ts": ts,
            "data": {},
            "cost_usd": None,
            "token_count": None,
            "model": None,
        }

        # Per-type enrichment. Mirrors sync.py::_parse_v3_event's
        # ``data`` shape (top-level discriminator + nested ``data``
        # payload) so routes/sessions.py reads the same key paths.
        inner: dict = {}

        if mapped == "session.started":
            self._open_spans[span_id] = ts
            label = (
                _first(attrs, "workflow_name", "task_name", "name")
                or _get(event, "name")
                or "nemo-workflow"
            )
            row["data"].update({"label": label, "timestamp": ts})
            inner.update({"label": label})

        elif mapped == "session.ended":
            row["data"].update({
                "label": _first(attrs, "workflow_name", "task_name") or _get(event, "name") or "",
                "status": _first(attrs, "status", default="completed"),
                "error": _first(attrs, "error"),
                "timestamp": ts,
            })
            inner.update({
                "status": row["data"]["status"],
                "error": row["data"]["error"],
            })

        elif mapped == "prompt.submitted":
            self._open_spans[span_id] = ts
            prompt = _first(attrs, "prompt", "input", "text", default="")
            model = _first(attrs, "model", "model_name") or self._default_model
            row["model"] = model
            row["data"].update({
                "finalPromptText": str(prompt),
                "modelId": model,
                "timestamp": ts,
            })
            inner.update({
                "finalPromptText": str(prompt),
                "modelId": model,
            })

        elif mapped == "model.completed":
            completion = _first(attrs, "completion", "output", "response", "text", default="")
            model = _first(attrs, "model", "model_name") or self._default_model
            in_tok = _first(attrs, "input_tokens", "prompt_tokens", "tokens_input", default=0)
            out_tok = _first(attrs, "output_tokens", "completion_tokens", "tokens_output", default=0)
            cost = _first(attrs, "cost_usd", "cost", "total_cost")
            # cost may be a dict {total, input, output} — flatten.
            if isinstance(cost, dict):
                cost = cost.get("total")
            try:
                in_tok = int(in_tok or 0)
                out_tok = int(out_tok or 0)
            except (TypeError, ValueError):
                in_tok, out_tok = 0, 0
            try:
                cost_f: Optional[float] = float(cost) if cost is not None else None
            except (TypeError, ValueError):
                cost_f = None
            total_tok = in_tok + out_tok
            last_call_usage = {
                "input": in_tok,
                "output": out_tok,
                "total": total_tok,
            }
            row["model"] = model
            row["token_count"] = total_tok
            row["cost_usd"] = cost_f
            row["data"].update({
                "completionText": str(completion),
                "assistantTexts": [str(completion)] if completion else [],
                "modelId": model,
                "promptCache": {"lastCallUsage": last_call_usage},
                "timestamp": ts,
            })
            inner.update({
                "completionText": str(completion),
                "assistantTexts": [str(completion)] if completion else [],
                "modelId": model,
                "promptCache": {"lastCallUsage": last_call_usage},
            })

        elif mapped == "tool.call":
            self._open_spans[span_id] = ts
            tool_name = (
                _first(attrs, "tool_name", "name")
                or _get(event, "name")
                or "unknown_tool"
            )
            tool_input = _first(attrs, "tool_input", "input", "args", "arguments", default={})
            row["data"].update({
                "name": tool_name,
                "input": tool_input,
                "id": span_id,
                "timestamp": ts,
            })
            inner.update({
                "name": tool_name,
                "input": tool_input,
                "id": span_id,
            })

        elif mapped == "tool.result":
            tool_name = (
                _first(attrs, "tool_name", "name")
                or _get(event, "name")
                or "unknown_tool"
            )
            output = _first(attrs, "tool_output", "output", "result", default="")
            error = _first(attrs, "error")
            row["data"].update({
                "name": tool_name,
                "tool_use_id": span_id,
                "output": output if isinstance(output, str) else str(output),
                "result": output if isinstance(output, str) else str(output),
                "is_error": bool(error),
                "error": error,
                "timestamp": ts,
            })
            inner.update({
                "name": tool_name,
                "tool_use_id": span_id,
                "output": row["data"]["output"],
                "result": row["data"]["result"],
                "is_error": row["data"]["is_error"],
                "error": error,
            })

        # Stamp the discriminator the dashboard's read path looks for
        # (routes/sessions.py::_is_openclaw_event), and nest the
        # type-specific payload under ``data.data`` — mirrors
        # sync.py::_parse_v3_event.
        row["data"]["type"] = mapped
        row["data"]["data"] = inner
        return row


__all__ = ["NeMoAdapter", "MAPPED_EVENT_TYPES"]
