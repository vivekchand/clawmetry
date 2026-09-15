# OpenTelemetry recipe: LangGraph with OpenLLMetry

A LangGraph agent with one tool, instrumented with OpenLLMetry, exporting to ClawMetry. The code is [`examples/otel/langgraph/`](../examples/otel/langgraph/). It runs in CI on every change against a live ClawMetry (job `otel-recipe-langgraph` in `.github/workflows/ci.yml`), and the check fails unless the run reads back as a session with the right tokens and the tool call. This page records what that check proved, under which versions, and what it did not prove.

Companion pages: [OPENTELEMETRY.md](OPENTELEMETRY.md) for the receiver, [BRING_YOUR_OWN_AGENT.md](BRING_YOUR_OWN_AGENT.md) for other frameworks.

## Verified versions

| Package | Version |
|---|---|
| `langgraph` | 1.2.11 |
| `langchain-core` | 1.6.3 |
| `opentelemetry-instrumentation-langchain` | 0.62.3 |
| `opentelemetry-sdk` | 1.44.0 |
| `opentelemetry-exporter-otlp-proto-http` | 1.44.0 |

Python 3.11. The CI job installs the full dependency closure hash-pinned from `.github/requirements/otel-recipe-langgraph.txt`, in a virtualenv of its own, separate from ClawMetry's. Newer versions will usually work; these are the ones that were proven.

| Property | Value |
|---|---|
| Wire encoding | OTLP over HTTP, `http/protobuf`, to `/v1/traces` (install the receiver as `pip install 'clawmetry[otel]'`) |
| Semantic conventions | OpenTelemetry GenAI conventions as emitted by `opentelemetry-semantic-conventions-ai` 0.5.1: `gen_ai.input.messages` / `gen_ai.output.messages` with message parts, `gen_ai.usage.input_tokens` / `output_tokens`, and the dotted cache keys `gen_ai.usage.cache_read.input_tokens` / `gen_ai.usage.cache_creation.input_tokens` |
| Model in the check | A deterministic stub chat model (no provider key, no cost) reporting 120 + 18 and 160 + 9 tokens for its two calls |

## Run it

```bash
pip install 'clawmetry[otel]' && clawmetry          # dashboard and receiver on :8900

cd examples/otel/langgraph
pip install -r requirements.txt
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
python agent.py --thread support-42
```

The setup is standard OpenTelemetry. `agent.py` builds a `TracerProvider` with a `service.name`, adds an `OTLPSpanExporter`, and calls `LangchainInstrumentor().instrument(tracer_provider=provider)`. Call `provider.shutdown()` before a short-lived process exits, or the last batch is lost.

### A ClawMetry on another machine

Loopback senders are trusted. Anything else must send the dashboard's gateway token as a Bearer header, which the OTLP exporter reads from the environment:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://clawmetry.internal:8900
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <gateway token>"
```

The CI check binds the dashboard to every interface and exports through the runner's non-loopback address. It proves an export without the header is refused with 401 and the recipe's export with it is accepted. Start the dashboard with `--host 0.0.0.0` (it binds loopback by default). `CLAWMETRY_OTLP_ALLOW_UNAUTH=1` turns the check off for a network that already gates access.

The dashboard serves plain HTTP; it does not terminate TLS itself. The `https://` endpoint above assumes a TLS terminator (a reverse proxy or load balancer) in front of it. Without one, use `http://` only on a network you trust, because the Bearer token then travels in cleartext. The CI check exports over plain HTTP inside the runner.

## What arrives

One LangGraph run produces one trace of ten spans:

```
invoke_agent LangGraph                 top span; carries gen_ai.conversation.id = the thread
└─ LangGraph.workflow
   ├─ execute_task agent
   │  ├─ <model>.chat                  gen_ai.request.model, gen_ai.usage.* tokens
   │  └─ execute_task tools_condition
   ├─ execute_task tools
   │  └─ execute_tool lookup_invoice   gen_ai.tool.name, arguments and result
   └─ execute_task agent
      ├─ <model>.chat
      └─ execute_task tools_condition
```

A `stream()` run produces the same ten spans as `invoke()`; the check runs one of each.

## Identity: application, run, conversation

| What | Where it comes from |
|---|---|
| Application | Resource `service.name` (`invoice-agent`). It becomes the runtime identity `invoice_agent` everywhere, shown as `invoice-agent (OTel)` in the runtime switcher |
| Run | The trace. One `invoke()` or `stream()` call is one trace |
| Conversation (session) | The LangGraph thread (`config={"configurable": {"thread_id": ...}}`) |

**How the thread becomes a session.** OpenLLMetry sends the thread as `gen_ai.conversation.id` on the top `invoke_agent` span only. Every span beneath it, including both model calls and the tool call, carries it as `traceloop.association.properties.thread_id` instead. ClawMetry reads both as the same identifier, recorded exactly as sent, so the whole run is one session named by the thread, and every later run on that thread joins the same session.

Order of precedence for a span's session:

1. `gen_ai.conversation.id` sent by the emitter
2. `traceloop.association.properties.thread_id` (the LangGraph thread)
3. `session.id` on the span or the resource
4. Nothing sent: the trace, as `<application>:trace:<trace_id>`

Whichever wins is recorded exactly as sent. The thread outranks `session.id` even when your application stamps `session.id` on every span: the top span resolves through its conversation id, so if `session.id` won on the spans beneath it, one run would split into two sessions again. To name the session yourself, send `gen_ai.conversation.id`.

**No thread, no conversation id.** LangGraph does not need a thread unless you use a checkpointer, and without one nothing identifies a conversation. ClawMetry then records one session per trace, so each run is its own session, named `invoice_agent:trace:<trace_id>` (the `trace:` segment marks it as derived, not sent). Cardinality is one session per run: a chat loop that calls `invoke()` per turn without a thread shows as one session per turn. Pass a thread to group turns.

A trace is not an assistant definition. The application is `service.name`; a session is a conversation or a run; nothing is inferred beyond that.

## What each tab shows for span-only data

Checked against a dashboard running with no sync daemon, after one run on a thread, by reading the API endpoints the tabs load their data from (for example `/api/local/traces`, `/api/usage` and `/api/guard/sessions`), not by looking at the rendered tabs:

| Tab | What it shows |
|---|---|
| Tracing | The run as one trace: 10 spans, tokens, derived cost, the model, the span tree with each span's attributes |
| Sessions | One row per thread (or per trace, with no thread) under `invoice_agent`: title `invoke_agent LangGraph`, 2 model calls, token total, cost |
| Transcript | Nothing. There is no transcript for a span-only application; message content, where the instrumentation records it, is in each span's detail in Tracing |
| Usage | Not verified. On the daemon-free dashboard above, the Usage tab's daily totals did not include these tokens |
| Guard | The session is listed, but labelled as OpenClaw and offered controls that cannot reach this agent (see below). Guard detectors over span tool calls are separate work (vivekchand/clawmetry#5938) |

Cost is derived from tokens and the model name, because spans carry no cost. The stub reports `claude-sonnet-4-5`; a real model's name is priced the same way. A model name the pricing table does not recognise (a deployment alias, for example) still gets a derived cost from a fallback rate, so check that the model shown in Tracing is the one you pay for before relying on the figure.

## Limits

- **Observe only.** This path observes an agent; it cannot pause, stop or gate it. A span arrives after the step it describes has run, and ClawMetry has no process or hook to reach in a remote LangGraph service. Any Pause, Stop or Kill offered for such a session does nothing to the agent.
- **A stub model, not a provider.** The check proves the telemetry pipeline end to end. It does not prove a provider integration: a real provider's model name, streaming token accounting and cache token reporting have not been run through this check.
- **Not yet covered by the check:** export retries and partial delivery (vivekchand/clawmetry#5949), late spans arriving after their session was materialized, and spans with missing token fields.
