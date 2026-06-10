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
import threading
import time
import uuid
from datetime import date
from typing import Any, Optional

logger = logging.getLogger("clawmetry.adapters.nemo")


# ── Free-tier daily ingest cap (issue #1170) ───────────────────────────
#
# NeMo Agent Toolkit users are the highest-value paid-conversion segment
# we observe (enterprise GPU buyers). Shipping the adapter under OSS gave
# the whole NeMo experience away for free, undercutting the sibling
# ``integrations/nat/`` Cloud-bound variant. The product-P0 fix caps free
# ingest at ``NEMO_FREE_DAILY_CAP`` events per UTC day; Pro users ingest
# unlimited. Counter resets at the UTC date boundary.
#
# State lives at module scope (not per-adapter) so that two independent
# NeMoAdapter instances pointing at the same local store share one cap —
# the cap is a tenant-level economic gate, not a per-instance throttle.
NEMO_FREE_DAILY_CAP = 1000

# Internal: lock + counter + date-key for the per-day budget.
_CAP_LOCK = threading.Lock()
_CAP_STATE: dict[str, Any] = {
    "date": "",          # UTC YYYY-MM-DD currently being counted
    "count": 0,          # events ingested today (Pro + Free both count for telemetry)
    "dropped": 0,        # events dropped today because cap was hit
    "warned": False,     # only log the cap-hit WARNING once per day
    "last_drop_ts": "",  # ISO timestamp of most recent drop (for banner staleness)
}


def _today_key() -> str:
    """UTC date key used to slice the cap counter."""
    return date.today().isoformat()


def _rollover_locked() -> None:
    """Reset counters when a new UTC day begins. Caller must hold ``_CAP_LOCK``."""
    today = _today_key()
    if _CAP_STATE["date"] != today:
        _CAP_STATE["date"] = today
        _CAP_STATE["count"] = 0
        _CAP_STATE["dropped"] = 0
        _CAP_STATE["warned"] = False
        _CAP_STATE["last_drop_ts"] = ""


def _is_pro() -> bool:
    """Best-effort Pro check that fails closed (treats unknown as Free).

    Reuses ``dashboard._is_pro_user()`` — the same helper PR #1553 added
    for auto-pause gating (#1169) and that #1168 uses for Telegram
    dispatch. Imported lazily so the adapter never hard-requires
    ``dashboard`` at module load (the adapter ships in the same wheel but
    standalone usage shouldn't crash if a downstream user vendored only
    the package directory).
    """
    try:
        import dashboard as _d  # noqa: WPS433
        return bool(_d._is_pro_user())
    except Exception:
        return False


def get_nemo_cap_state() -> dict:
    """Return a snapshot of the daily cap state for the dashboard banner.

    Shape (stable contract used by ``/api/nemo-cap-status`` and the
    Brain / Tokens-tab upsell banner)::

        {
            "cap": 1000,                # int — free-tier daily limit
            "used": 137,                # int — events ingested today
            "dropped": 0,               # int — events dropped today (free-tier only)
            "is_pro": False,            # bool — caller is on Cloud-Pro
            "cap_hit": False,           # bool — free-tier cap reached today
            "date": "2026-05-17",       # UTC date key for the current bucket
        }
    """
    with _CAP_LOCK:
        _rollover_locked()
        return {
            "cap": NEMO_FREE_DAILY_CAP,
            "used": int(_CAP_STATE["count"]),
            "dropped": int(_CAP_STATE["dropped"]),
            "is_pro": _is_pro(),
            "cap_hit": (not _is_pro()) and int(_CAP_STATE["count"]) >= NEMO_FREE_DAILY_CAP,
            "date": _CAP_STATE["date"] or _today_key(),
        }


def _reset_cap_state_for_tests() -> None:
    """Test-only hook — wipe cap counters between cases."""
    with _CAP_LOCK:
        _CAP_STATE["date"] = ""
        _CAP_STATE["count"] = 0
        _CAP_STATE["dropped"] = 0
        _CAP_STATE["warned"] = False
        _CAP_STATE["last_drop_ts"] = ""


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

        Issue #1170: free-tier callers are capped at ``NEMO_FREE_DAILY_CAP``
        events per UTC day. Once the cap is hit we drop subsequent events
        and surface a banner via ``/api/nemo-cap-status``. Pro users
        bypass the cap entirely.
        """
        try:
            row = self.map_event(event)
        except Exception as exc:
            logger.warning("nemo adapter: map_event raised %r - dropping", exc)
            return None
        if row is None:
            return None
        # Free-tier daily cap (#1170). Performed AFTER map_event so we
        # don't even map events that will be dropped, but BEFORE ingest
        # so we don't pollute DuckDB beyond the cap.
        with _CAP_LOCK:
            _rollover_locked()
            if not _is_pro() and _CAP_STATE["count"] >= NEMO_FREE_DAILY_CAP:
                _CAP_STATE["dropped"] = int(_CAP_STATE["dropped"]) + 1
                _CAP_STATE["last_drop_ts"] = _now_iso()
                if not _CAP_STATE["warned"]:
                    _CAP_STATE["warned"] = True
                    logger.warning(
                        "nemo adapter: free-tier daily cap reached "
                        "(%d/%d events today). Further NeMo events are "
                        "dropped until UTC midnight. Upgrade to Cloud-Pro "
                        "for unlimited ingest: "
                        "https://app.clawmetry.com/upgrade?source=nemo_cap",
                        NEMO_FREE_DAILY_CAP,
                        NEMO_FREE_DAILY_CAP,
                    )
                return None
            _CAP_STATE["count"] = int(_CAP_STATE["count"]) + 1
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


# ── NemoClaw RUNTIME read-side AgentAdapter ────────────────────────────────
#
# NemoClaw is a Free runtime alongside OpenClaw (FREE_RUNTIMES in
# clawmetry/entitlements.py contains {"openclaw", "nemoclaw"}). It is the
# NVIDIA-flavored wrapper of OpenClaw that ingests events tagged with
# ``agent_type='nemoclaw'`` (filesystem source or in-process). This facade
# exposes those events through the standard :class:`AgentAdapter` shape so
# the multi-agent UI chip bar + /api/agents + the runtime switcher all see
# NemoClaw alongside OpenClaw.
#
# Distinct from the push-mode ``NeMoAdapter`` above, which receives NeMo
# Guardrails (governance) callback events tagged ``agent_type='nemo'``.
# Guardrails is a Free *feature* (``nemo_governance``), not a runtime.
#
# Renamed from ``NeMoReaderAdapter`` (PR #2339, OSS 0.12.370) which
# incorrectly used ``name='nemo'`` and queried governance events. The
# canonical runtime id per /api/runtimes + FREE_RUNTIMES is ``nemoclaw``;
# this rename aligns /api/agents with the rest of the runtime catalogue.
from .base import AgentAdapter, Capability, DetectResult, Event, Session


def _read_nemoclaw_skill_catalog() -> dict:
    """Read catalog-metadata.json from the nemoclaw skills directory.

    Checks two candidate locations (blueprint dir first, then a flat
    ~/.nemoclaw/skills/ fallback). Returns a dict of skill_catalog_*
    keys if the file is found; empty dict otherwise — never raises.
    """
    import json
    from pathlib import Path

    home = Path.home()
    candidates = [
        home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "skills" / "catalog-metadata.json",
        home / ".nemoclaw" / "skills" / "catalog-metadata.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text())
            meta = raw.get("metadata", {})
            return {
                "skill_catalog_min_version": meta.get("minNemoClawVersion", ""),
                "skill_catalog_tested_version": meta.get("testedNemoClawVersion", ""),
                "skill_catalog_export_sha256": raw.get("exportContentSha256", ""),
                "skill_catalog_source_commit": raw.get("sourceCommit", meta.get("sourceCommit", "")),
                "skill_catalog_source_sha256": raw.get("sourceContentSha256", meta.get("sourceContentSha256", "")),
            }
        except Exception as exc:
            logger.debug("nemoclaw skill catalog read failed (%s): %s", path, exc)
    return {}


# Mirrors the host constants exported by the harness
# (nemoclaw dist/lib/inference/local.js): the local Ollama backend is
# reached at host.docker.internal when ClawMetry/NemoClaw runs inside a
# container, otherwise at the loopback address.
_OLLAMA_HOST_DOCKER_INTERNAL = "http://host.docker.internal:11434"
_OLLAMA_LOCALHOST = "http://127.0.0.1:11434"


def _resolve_ollama_host() -> tuple[str, str]:
    """Resolve the Ollama base URL and how it was chosen.

    Mirrors the OLLAMA_HOST_DOCKER_INTERNAL vs OLLAMA_LOCALHOST resolution
    in the harness (dist/lib/inference/local.js):

    * An explicit ``OLLAMA_HOST`` env var always wins (mode ``"explicit"``).
    * Inside a container (``/.dockerenv`` present or ``OLLAMA_IN_DOCKER``
      truthy) the docker-internal host is used (mode ``"docker-internal"``).
    * Otherwise the loopback host is used (mode ``"loopback"``).

    Returns ``(host, mode)``. Never raises.
    """
    import os

    explicit = (os.environ.get("OLLAMA_HOST") or "").strip()
    if explicit:
        # Bare host:port (no scheme) — normalise to a URL like the harness.
        if "://" not in explicit:
            explicit = "http://" + explicit
        return explicit, "explicit"

    in_docker = False
    try:
        in_docker = os.path.exists("/.dockerenv") or bool(
            (os.environ.get("OLLAMA_IN_DOCKER") or "").strip()
        )
    except Exception:
        in_docker = False
    if in_docker:
        return _OLLAMA_HOST_DOCKER_INTERNAL, "docker-internal"
    return _OLLAMA_LOCALHOST, "loopback"


def _read_nemoclaw_ollama_inference() -> dict:
    """Surface the local Ollama inference host + available model roster.

    Closes obs-gap #2959: the harness resolves the Ollama host and exposes
    ``getOllamaModelOptions()`` (the local model roster queried from
    ``/api/tags`` or ``ollama list``), but ClawMetry never surfaced either,
    so the dashboard could not show which inference host a NemoClaw session
    used or what models the local backend advertises.

    Queries ``{host}/api/tags`` with a short timeout (mirrors
    getOllamaModelOptions). The host/mode are always returned; the model
    roster is only added when the backend answers. Never raises — returns a
    dict with ``host``/``hostMode`` even when Ollama is unreachable.
    """
    import json
    import urllib.request

    host, mode = _resolve_ollama_host()
    out: dict = {"ollama_host": host, "ollama_host_mode": mode}
    try:
        url = host.rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=0.6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = payload.get("models") if isinstance(payload, dict) else None
        names: list[str] = []
        for m in models or []:
            if isinstance(m, dict):
                name = m.get("name") or m.get("model")
                if name:
                    names.append(str(name))
        # Stable, de-duplicated roster for predictable dashboard rendering.
        out["ollama_local_models"] = sorted(set(names))
    except Exception as exc:
        logger.debug("nemoclaw ollama model roster query failed (%s): %s", host, exc)
    return out


class NemoClawAdapter(AgentAdapter):
    """Read-side adapter for the NemoClaw Free runtime.

    Reads events tagged ``agent_type='nemoclaw'`` from DuckDB. Detection
    is "any nemoclaw-tagged events present" so an OSS install with no
    NemoClaw data does not clutter the chip bar.
    """

    name = "nemoclaw"
    display_name = "NemoClaw"

    def detect(self) -> DetectResult:
        n = 0
        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store(read_only=True)
            rows = store._fetch(
                "SELECT COUNT(*) FROM events WHERE agent_type = ?",
                ["nemoclaw"],
            )
            if rows:
                n = int(rows[0][0])
        except Exception as exc:
            logger.debug("nemoclaw detect read failed: %s", exc)
        meta: dict = {"event_count": n}
        meta.update(_read_nemoclaw_skill_catalog())
        meta["ollama_inference"] = _read_nemoclaw_ollama_inference()
        return DetectResult(
            name=self.name,
            display_name=self.display_name,
            detected=n > 0,
            running=False,
            workspace="(DuckDB-backed runtime view)",
            session_count=0,
            capabilities=[c.value for c in self.capabilities()],
            meta=meta,
        )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        sessions: list[Session] = []
        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store(read_only=True)
            rows = store._fetch(
                "SELECT session_id, MIN(ts) AS started, MAX(ts) AS ended, "
                "COUNT(*) AS n_events, SUM(token_count) AS tokens, "
                "SUM(cost_usd) AS cost FROM events "
                "WHERE agent_type = ? AND session_id IS NOT NULL "
                "GROUP BY session_id ORDER BY started DESC LIMIT ?",
                ["nemoclaw", int(limit)],
            )
            for r in rows or []:
                sid = r[0]
                started = r[1] or 0.0
                ended = r[2] or 0.0
                # ts column is VARCHAR (ISO string or epoch-as-string);
                # coerce to float for the dataclass typed fields.
                try:
                    started_f = float(started) if started not in ("", None) else 0.0
                except (TypeError, ValueError):
                    started_f = 0.0
                try:
                    ended_f = float(ended) if ended not in ("", None) else None
                except (TypeError, ValueError):
                    ended_f = None
                n_ev = int(r[3] or 0)
                tokens = int(r[4] or 0)
                cost = float(r[5] or 0.0)
                sessions.append(Session(
                    agent=self.name,
                    id=str(sid),
                    title=f"NemoClaw session {str(sid)[:8]}",
                    started_at=started_f,
                    ended_at=ended_f,
                    message_count=n_ev,
                    total_tokens=tokens,
                    cost_usd=cost,
                ))
        except Exception as exc:
            logger.debug("nemoclaw list_sessions read failed: %s", exc)
        return sessions

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        events: list[Event] = []
        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store(read_only=True)
            rows = store._fetch(
                "SELECT id, event_type, ts, model, token_count "
                "FROM events WHERE agent_type = ? AND session_id = ? "
                "ORDER BY ts ASC LIMIT ?",
                ["nemoclaw", str(session_id), int(limit)],
            )
            for r in rows or []:
                events.append(Event(
                    agent=self.name,
                    session_id=str(session_id),
                    id=str(r[0]),
                    type=str(r[1] or "event"),
                    ts=float(r[2]) if isinstance(r[2], (int, float)) else 0.0,
                    tokens=int(r[4] or 0),
                    extra={"model": r[3]} if r[3] else {},
                ))
        except Exception as exc:
            logger.debug("nemoclaw list_events read failed: %s", exc)
        return events

    def capabilities(self) -> set[Capability]:
        return {
            Capability.SESSIONS,
            Capability.EVENTS,
            Capability.BRAIN,
            Capability.COST,
            Capability.SKILLS,
        }


# Back-compat alias: the previous (mis-named) class still imports OK so
# any out-of-tree code that referenced ``NeMoReaderAdapter`` from
# ``clawmetry.adapters.nemo`` keeps working. Marked for removal once
# downstream usage is confirmed clean.
NeMoReaderAdapter = NemoClawAdapter


__all__ = [
    "NeMoAdapter",
    "NemoClawAdapter",
    "NeMoReaderAdapter",  # back-compat alias for NemoClawAdapter
    "MAPPED_EVENT_TYPES",
    "NEMO_FREE_DAILY_CAP",
    "get_nemo_cap_state",
]
