# clawmetry-nat

> NVIDIA NeMo Agent Toolkit (NAT) telemetry exporter for [ClawMetry](https://clawmetry.com)

Maps NAT `IntermediateStep` workflow events to ClawMetry's brain event format so you can observe, debug, and analyse your NAT agent workflows in the ClawMetry dashboard.

[![PyPI version](https://img.shields.io/pypi/v/clawmetry-nat.svg)](https://pypi.org/project/clawmetry-nat/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../LICENSE)

---

## Features

| NAT event | ClawMetry event |
|-----------|----------------|
| `WORKFLOW_START` / `task_start` | Session start |
| `LLM_START` | User message (prompt captured) |
| `LLM_END` | Assistant message + token counts + cost |
| `TOOL_START` / `tool_call` | Tool call event |
| `TOOL_END` / `tool_result` | Tool result event |
| `WORKFLOW_END` / `task_end` | Session end + cost summary |

- **Zero hard dependencies** — stdlib only (no `nvidia-nat` required at runtime)
- **Dual mode**: HTTP POST to ClawMetry ingest API *or* local JSONL files
- **Batched & async-safe**: background flush thread, never blocks your agent loop
- **NAT plugin**: optional native registration as a NAT tracing exporter

---

## Installation

```bash
pip install clawmetry-nat
```

With NAT native plugin support:

```bash
pip install "clawmetry-nat[nat]"
```

---

## Quick Start

### Callback mode (no `nvidia-nat` required)

```python
from clawmetry_nat import ClawMetryNATExporter

exporter = ClawMetryNATExporter(
    clawmetry_url="https://ingest.clawmetry.com",
    api_key="YOUR_CLAWMETRY_API_KEY",
)

# Call on_event() from wherever you receive NAT events
exporter.on_event(nat_intermediate_step)

# Or pass it as a callback when configuring your workflow
```

### Environment variables

```bash
export CLAWMETRY_URL="https://ingest.clawmetry.com"
export CLAWMETRY_API_KEY="your-key"
```

Then just:

```python
exporter = ClawMetryNATExporter()   # picks up env vars automatically
```

### Offline / JSONL mode

If no `CLAWMETRY_API_KEY` is set, events are written to `~/.clawmetry/nat/*.jsonl`.
You can also force JSONL mode:

```python
exporter = ClawMetryNATExporter(jsonl_dir="/tmp/nat-events")
```

### Context manager

```python
with ClawMetryNATExporter() as exporter:
    exporter.on_event(step1)
    exporter.on_event(step2)
# Flushes automatically on exit
```

---

## NAT Native Plugin (requires `nvidia-nat`)

Register as a native NAT tracing plugin so it appears in `nat info components -t tracing`:

```python
# In your app startup, before running nat workflows
from clawmetry_nat.exporter import register_clawmetry_exporter
register_clawmetry_exporter()
```

Then configure in `workflow.yaml`:

```yaml
general:
  telemetry:
    tracing:
      clawmetry:
        _type: clawmetry
        url: "https://ingest.clawmetry.com"
        api_key: "YOUR_KEY"
        model: "nemotron-3-nano"
```

### Subclass approach (advanced)

```python
from clawmetry_nat import ClawMetryNATExporter
from nat.observability.exporter.raw_exporter import RawExporter
from nat.data_models.intermediate_step import IntermediateStep

class MyExporter(ClawMetryNATExporter, RawExporter[IntermediateStep, IntermediateStep]):
    async def export_processed(self, item: IntermediateStep) -> None:
        self.on_event(item)   # delegate to ClawMetry bridge
        # your additional logic here
```

---

## Configuration

| Parameter / Env var | Default | Description |
|---------------------|---------|-------------|
| `clawmetry_url` / `CLAWMETRY_URL` | `https://ingest.clawmetry.com` | ClawMetry ingest endpoint |
| `api_key` / `CLAWMETRY_API_KEY` | *(none)* | ClawMetry API key |
| `session_id` | auto-generated UUID | Fixed session identifier |
| `model` | `nat-agent` | Model label used in events |
| `batch_size` / `CLAWMETRY_NAT_BATCH_SIZE` | `50` | Max events per HTTP POST |
| `flush_interval_sec` / `CLAWMETRY_NAT_FLUSH_SEC` | `5` | Auto-flush interval (seconds) |
| `jsonl_dir` / `CLAWMETRY_NAT_JSONL_DIR` | `~/.clawmetry/nat` | JSONL output directory |

---

## Event Schema Reference

ClawMetry brain events (JSON):

```json
{
  "type": "message",
  "session_id": "uuid",
  "timestamp": "2026-03-23T10:00:00Z",
  "source": "nat",
  "message": {
    "role": "assistant",
    "content": "Response text",
    "model": "nat-agent",
    "usage": {
      "input": 512,
      "output": 128,
      "cacheRead": 0,
      "cacheWrite": 0,
      "cost": {"total": 0.0032}
    }
  },
  "durationMs": 1240
}
```

---

## Development

```bash
git clone https://github.com/vivekchand/clawmetry
cd integrations/nat
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

MIT — see [LICENSE](../../LICENSE)

Part of the [ClawMetry](https://clawmetry.com) observability ecosystem.
