# Bring your own agent: OpenTelemetry ingestion end to end

ClawMetry ships adapters for 30 agent runtimes with local footprints (Claude Code, Codex, Cursor, OpenClaw and friends). This guide covers everything else: **any agent that speaks OpenTelemetry**, including fleets you do not run on your laptop.

Who this is for:

- **AWS Bedrock AgentCore** fleets (Strands, LangGraph, CrewAI agents deployed to AgentCore Runtime)
- **Pydantic AI** apps (native OTel instrumentation)
- **LangChain / LangGraph** apps (via OpenLLMetry instrumentation)
- Anything else that can set `OTEL_EXPORTER_OTLP_ENDPOINT`

If you are already paying a hosted tracing SaaS to look at these traces, note that the integration below is the same OTLP exporter you already configured, pointed at software you run yourself.

Companion pages: [`docs/OPENTELEMETRY.md`](OPENTELEMETRY.md) for the receiver and exporter basics, and [`examples/bring-your-own-agent/`](../examples/bring-your-own-agent/) for the runnable code below.

## How it works

ClawMetry's dashboard includes a native OTLP receiver:

| Endpoint | Accepts |
|---|---|
| `POST /v1/traces` | OTLP protobuf or JSON, gzip ok |
| `POST /v1/metrics` | same |
| `POST /v1/logs` | same |

Spans following the [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) are mapped onto typed columns at ingest:

| Your telemetry | Becomes |
|---|---|
| `gen_ai.usage.input_tokens` / `output_tokens`, cache token attrs | Token accounting, cache-aware |
| `gen_ai.request.model`, `gen_ai.provider.name` / `gen_ai.system` | Model and provider attribution |
| tokens x model (when spans carry no cost, the OTel norm) | Dollar cost, derived from a maintained multi-provider pricing table |
| `gen_ai.tool.name` | Tool call visibility |
| `gen_ai.conversation.id` / `session.id` | A session row per conversation |
| `service.name` (resource) | The app's identity: one entry in the runtime switcher and Agent Inventory, shown as `your-app (OTel)` |
| `deployment.environment` (resource) | Kept on spans and sessions so dev / test / prod stay separable |

What lights up in the dashboard: the **Tracing** tab (span trees per trace), **Sessions** (one row per conversation, with tokens, cost, title and liveness), **Usage** (per-model tokens and cost), **Agent Inventory** and the runtime switcher (one row per app), and budget caps and alert rules driven by the same telemetry.

Honesty notes, so nothing surprises you later:

- This path is **observation only**. Pause / stop / kill and pre-tool gates need a runtime ClawMetry can reach as a process or hook; a span stream is not that.
- OTLP arrives at the receiver in **plaintext**. The end-to-end encryption ClawMetry's sync daemon provides covers the daemon path; for OTLP the answer is to self-host the receiver inside your network, where the plaintext never leaves.

## Five-minute local start (no API key needed)

```bash
pip install 'clawmetry[otel]' && clawmetry      # dashboard + receiver on :8900
pip install pydantic-ai-slim opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
python examples/bring-your-own-agent/pydantic_ai_agent.py
```

The example runs a real Pydantic AI agent with a tool call. Without an `ANTHROPIC_API_KEY` it uses Pydantic AI's built-in `TestModel`, so the whole pipeline is testable at zero cost. Open `http://localhost:8900`: the Tracing tab shows the run as `invoke_agent -> chat -> execute_tool -> chat`, Sessions shows the conversation, and the switcher shows `invoice-copilot (OTel)`.

## AWS Bedrock AgentCore, end to end

AgentCore auto-instruments every agent with ADOT (the AWS OpenTelemetry distro) and exports GenAI-semconv spans over OTLP. Re-pointing that exporter is the same partner-observability pattern AWS documents for Langfuse, Instana and Datadog.

### Topology

```
AgentCore Runtime (ADOT)  ->  OTel Collector (your VPC)  ->  ClawMetry (self-hosted, your VPC)
                                     \->  CloudWatch / X-Ray (unchanged)
```

Use the collector fan-out so CloudWatch keeps working. A direct exporter connection to ClawMetry also works if you do not need CloudWatch.

### Configuration (Terraform)

The whole integration is environment variables on the AgentCore runtime resource, rolled out by your existing pipeline:

```hcl
environment_variables = {
  AGENT_OBSERVABILITY_ENABLED = "true"
  OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
  OTEL_EXPORTER_OTLP_ENDPOINT = "https://clawmetry.observability.internal:8900"
  OTEL_EXPORTER_OTLP_HEADERS  = "Authorization=Bearer ${var.clawmetry_token}"
  OTEL_RESOURCE_ATTRIBUTES    = "service.name=${var.agent_name},deployment.environment=${var.environment}"
}
```

Notes:

- `service.name` is the fleet's legibility: `payments-agent` in Dev and Prod stays one app, separable by `deployment.environment`. One hundred agents in Dev and twenty in Prod stay distinguishable in every view.
- AgentCore stamps a session id on the telemetry of each runtime session; ClawMetry groups spans into sessions by it (`session.id` / `gen_ai.conversation.id`).
- The Python OTLP exporters (and ADOT) send protobuf, so install the receiver as `pip install 'clawmetry[otel]'` (the Docker image includes it). OTLP/JSON senders work on a bare install.
- ClawMetry self-hosts as a single Docker container (`docker run -p 8900:8900 clawmetry`); data lives in an embedded DuckDB on your infrastructure.
- Off-box senders authenticate with the gateway token as a `Bearer` header. `CLAWMETRY_OTLP_ALLOW_UNAUTH=1` disables auth for the `/v1/*` endpoints when something else (a collector inside a private network) already gates access.

### A reference app to try

The [awslabs/agentcore-samples](https://github.com/awslabs/agentcore-samples) repository is a working open-source AgentCore project; its `06-AgentCore-observability` tutorials include the partner-observability notebooks whose exporter re-pointing this guide uses. `examples/bring-your-own-agent/strands_agentcore_agent.py` in this repo is the same Strands agent shape, runnable locally with Anthropic or AWS credentials and deployable to AgentCore unchanged.

## Pydantic AI

Pydantic AI instruments itself with OpenTelemetry; no third-party instrumentation package is needed:

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings

provider = TracerProvider(resource=Resource.create({
    "service.name": "invoice-copilot",
    "deployment.environment": "dev",
}))
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://localhost:8900/v1/traces")))
Agent.instrument_all(InstrumentationSettings(tracer_provider=provider))
```

Everything after that is a normal Pydantic AI agent. Pydantic AI stamps its own `gen_ai.conversation.id`, so each run appears as its own session with no extra work. Call `provider.shutdown()` before a short-lived process exits so the batch exporter flushes.

## LangChain and LangGraph

LangChain emits OTel through the OpenLLMetry instrumentation package, which hooks the callback system LangGraph nodes also run through:

```python
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
LangchainInstrumentor().instrument(tracer_provider=provider)   # same provider as above
```

LangChain does not stamp a conversation id on its spans, so put one on the resource to group a run as a session:

```python
Resource.create({"service.name": "support-triage", "session.id": run_id})
```

ClawMetry also understands OpenLLMetry's indexed prompt attributes (`gen_ai.prompt.0.role` and friends), so message content shows in the span detail where the instrumentation records it.

## Troubleshooting

- **Traces but no session rows**: spans carry no `session.id` / `gen_ai.conversation.id`. Add one (span attribute or resource attribute). Traces and usage work without it; sessions need it.
- **App missing from the switcher**: the resource has no `service.name`, so spans bucket under `custom`. Set it.
- **Cost shows zero**: spans carry neither token attributes nor a cost attribute. Token counts are enough; ClawMetry derives dollars from the model id, cache-aware.
- **401 from the receiver**: off-box senders need `Authorization: Bearer <gateway token>`, or set `CLAWMETRY_OTLP_ALLOW_UNAUTH=1` when the network already gates access.
- **Nothing arrives at all**: the exporter protocol must be `http/protobuf` (or JSON); a gRPC-only exporter (port 4317 style) needs an OTel Collector in front, receiving gRPC and exporting `otlphttp` to ClawMetry.
