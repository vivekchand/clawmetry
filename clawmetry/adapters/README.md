# `clawmetry/adapters/`

Per-framework translators that map a native agent runtime's data format
onto ClawMetry's unified `Session` / `Event` schema (see `base.py`).

| Adapter | Source framework | Mode | Module |
|---------|------------------|------|--------|
| `OpenClawAdapter` | [OpenClaw](https://github.com/openclaw/openclaw) | pull (filesystem) | `openclaw.py` |
| `HermesAdapter` | [Hermes Agent](https://github.com/NousResearch/hermes-agent) | pull (SQLite) | `hermes.py` |
| `NeMoAdapter` | [NVIDIA NeMo Agent Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit) | push (callback) | `nemo.py` |

See `base.py` for `AgentAdapter`, `Session`, `Event`, and `Capability`.
See `registry.py` for how pull-mode adapters are registered + detected.

---

## NeMo Agent Toolkit (`nemo.py`) — issue #234

NVIDIA's NeMo Agent Toolkit is a Python framework for building agents.
Many ClawMetry users run NeMo agents alongside or instead of OpenClaw.
`NeMoAdapter` lets ClawMetry ingest NeMo telemetry without requiring
`nemo_toolkit` to be installed in the dashboard process.

### Mode

**Push, not pull.** Unlike `OpenClawAdapter` and `HermesAdapter`, NeMo
emits events into a callback bus rather than persisting them somewhere
we can scan. `NeMoAdapter` is therefore **not** an `AgentAdapter`
subclass — it's a thin callback receiver that you wire into the NeMo
runtime, and it writes mapped rows directly to the local DuckDB via
`LocalStore.ingest`. The dashboard reads `agent_type='nemo'` rows from
the same `events` table that powers OpenClaw views, so no new read
paths are required.

### Wiring

```python
from clawmetry import local_store
from clawmetry.adapters.nemo import NeMoAdapter

adapter = NeMoAdapter(local_store.get_store())

# Subscribe to NeMo's event bus. The exact API varies by NeMo version —
# this is the IntermediateStepManager pattern; tracing exporters work
# the same way.
nat_manager.subscribe(adapter.on_event)
```

`on_event` accepts both `dict` events and NeMo's native
`IntermediateStep` objects (it duck-types attribute / key access), so
the same call site works regardless of which surface you hook into.

### Assumed event shape

The NeMo plugin SDK is still evolving and has no stable Python-side
contract we can pin. We duck-type the OpenTelemetry-span-flavoured
shape currently emitted by the toolkit's bundled exporters (Phoenix,
Langfuse, W&B Weave). Every field below is optional — missing fields
fall back to sensible defaults; malformed input is logged and dropped,
never raises:

```python
{
    "event_type": "LLM_END",          # or IntermediateStepType.LLM_END enum
    "name":       "claude-3.5-sonnet",
    "span_id":    "abc123",           # stable across the matching START
    "trace_id":   "session-uuid",     # → ClawMetry session_id
    "start_time": 1715000000.0,       # epoch seconds (ms also accepted)
    "end_time":   1715000001.4,
    "attributes": {                   # or "metadata" / "payload" / "data"
        "model":          "claude-3.5-sonnet",
        "prompt":         "…",                 # LLM_START
        "completion":     "…",                 # LLM_END
        "input_tokens":   512,
        "output_tokens":  128,
        "cost_usd":       0.0032,
        "tool_name":      "tavily_search",     # TOOL_*
        "tool_input":     {…},
        "tool_output":    "…",
        "workflow_name":  "research",          # WORKFLOW_*
        "error":          None,
        "status":         "completed",
    },
}
```

### Event-type mapping

| NeMo `event_type` (any case) | ClawMetry `event_type` |
|------------------------------|------------------------|
| `WORKFLOW_START`, `TASK_START` | `session.started` |
| `WORKFLOW_END`, `TASK_END`     | `session.ended` |
| `LLM_START`, `llm_call`        | `prompt.submitted` |
| `LLM_END`, `llm_response`      | `model.completed` |
| `TOOL_START`, `tool_call`      | `tool.call` |
| `TOOL_END`, `tool_result`      | `tool.result` |

These are the same dot.separated values
`clawmetry/sync.py::_parse_v3_event` produces for OpenClaw v3 events,
so the dashboard's brain feed, transcript view, and cost analytics
render NeMo data identically to OpenClaw data.

Unknown event types are logged at `WARNING` and skipped — the adapter
never crashes on bad input, in line with ClawMetry's "never crash on
bad input" convention.

### Sibling package: `integrations/nat/`

A separate PyPI-distributable package, `clawmetry-nat`, lives at
`integrations/nat/` for users who want to send NeMo telemetry to
ClawMetry **Cloud** (HTTP POST + JSONL fallback). `NeMoAdapter` here
is the **local-DuckDB** ingestion path used by `clawmetry` itself.
The taxonomies and field conventions are kept aligned between the
two so anyone reading both at once gets a consistent mental model.
