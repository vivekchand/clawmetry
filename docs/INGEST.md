# Sending data to ClawMetry (ingest/1)

> GENERATED FILE, do not edit by hand. Source of truth:
> `clawmetry/ingest_contract.py`. Regenerate with
> `python3 scripts/gen_ingest_doc.py` (CI fails on drift).

Most people never read this page. ClawMetry detects the agents on
the machine it runs on and starts observing them with no
configuration at all.

This page is for the other case: an agent that is **not** on that
machine — running in CI, in a container, in a serverless function,
inside a hosted product, or on somebody else's laptop. Those push to
ClawMetry instead of being detected by it.

## Authentication

| Mode | When | How |
|---|---|---|
| Loopback | The agent and ClawMetry are on the same machine. | Nothing to configure. This is the zero-config path and it is what most installs use. |
| Gateway token | An exporter elsewhere on a trusted LAN. | Authorization: Bearer $OPENCLAW_GATEWAY_TOKEN |
| Ingest key | Anything that is not on this machine: CI, a container, a serverless function, a hosted product, a teammate's laptop. | clawmetry key create --name ci --scope write:ingest, then x-clawmetry-key: cmk_... |

An ingest key can **only push**. It grants no read scope, so a key
left in a CI runner cannot read a prompt, a cost or a session back
out. It is never given a CORS header and cannot be created with a
browser origin: ingest is server-to-server.

## Endpoints

| Method | Path | Accepts | |
|---|---|---|---|
| `POST` | `/v1/traces` | OTLP traces | Spans. The GenAI convention's model-call spans land here, and this is the surface an OTel SDK or Collector already speaks. |
| `POST` | `/v1/metrics` | OTLP metrics | Counters and histograms. |
| `POST` | `/v1/logs` | OTLP logs | Log records. Claude Code and Codex export their per-turn event stream this way, with cost and tokens per record. |
| `POST` | `/api/v1/runs` | JSON | Open a run; returns run_id. For engines that would rather push typed records than build OTLP. |
| `POST` | `/api/v1/runs/<id>/events` | JSON | Append one event or a batch of up to 1000. |
| `POST` | `/api/v1/runs/<id>/end` | JSON | Mark the run ended. Optional. |
| `GET` | `/api/v1/runs/<id>` | - | Read back: was the run persisted? |
| `GET` | `/api/v1/runtimes` | - | The runtimes ClawMetry knows about. Free, no key needed. |

## Encodings

| `Content-Type` | |
|---|---|
| `application/x-protobuf` | OTLP protobuf. The default for the OTel Collector and the SDKs, and smaller on the wire. |
| `application/json` | OTLP/JSON. Useful when a client cannot produce protobuf -- a script, a serverless function, a platform that only emits JSON. |

| `Content-Encoding` | |
|---|---|
| `gzip` | Accepted on every surface. |

## Headers

| Header | Required | |
|---|---|---|
| `x-clawmetry-key` | for a caller that is not on this machine | An ingest key: clawmetry key create --name ci --scope write:ingest |
| `x-clawmetry-runtime` | no | Which runtime is pushing -- claude_code, my-engine, anything matching [a-z0-9][a-z0-9_-]{0,39}. An unrecognised name is accepted: in-house engines are a supported case. Sets the resource's service.name, which is what the runtime is derived from. Without it the runtime comes from service.name as sent. |
| `x-clawmetry-env` | no | Environment or project label -- production, team-a.staging. Sets deployment.environment. This is the one grouping axis above runtime, and deliberately the only one. |
| `Content-Type` | yes, on OTLP | application/x-protobuf or application/json. See encodings. |
| `Content-Encoding` | no | gzip, if you compressed the body. |

`x-clawmetry-runtime` and `x-clawmetry-env` are resolved once per request
and applied to every event in it. They are written into the resource
attributes the mappers already read, so a header is exactly as
powerful as the equivalent exporter setting — and the header wins,
because it is the one you set per request.

There is one grouping axis above runtime, on purpose. A
dataset/collection/tag taxonomy is what a log platform needs when it
has thousands of unrelated sources. This is not that.

## Limits

| | |
|---|---|
| Body | 10 MB |
| Events per batch | 1000 |

## Responses

Every response carries a sentence in its body, not only a code.
These get read inside an agent's terminal output with no
documentation open.

| Code | Means |
|---|---|
| `200` | Accepted. |
| `400` | The body did not decode, or a routing header was malformed. The message names what was expected. |
| `401` | No key, or a key this ClawMetry does not know. It may have been revoked, or belong to a different install. |
| `403` | A valid key that lacks write:ingest. Different from 401 on purpose: 'your key is wrong' and 'your key is fine and may not do this' send you to different fixes. |
| `413` | Body over 10 MB. Split the batch, or compress with Content-Encoding: gzip. |
| `429` | Intake is paused because a budget limit was exceeded. |
| `501` | OTLP support is not installed on this ClawMetry: pip install clawmetry[otel] |

## Example

```bash
clawmetry key create --name ci --scope write:ingest

curl -X POST http://localhost:8900/v1/traces \
  -H "x-clawmetry-key: $CLAWMETRY_KEY" \
  -H 'x-clawmetry-runtime: my-engine' \
  -H 'x-clawmetry-env: production' \
  -H 'Content-Type: application/json' \
  --data-binary @spans.json
```

## GenAI attributes

ClawMetry reads the OpenTelemetry GenAI semantic conventions, so an
app instrumented with any conforming library needs no
ClawMetry-specific SDK.

### Read

| Attribute | |
|---|---|
| `gen_ai.operation.name` | Marks the span as a model call. |
| `gen_ai.request.model` | The model asked for. |
| `gen_ai.response.model` | The model actually served. |
| `gen_ai.provider.name` | Provider; gen_ai.system is read as the older name. |
| `gen_ai.usage.input_tokens` | Input tokens. |
| `gen_ai.usage.output_tokens` | Output tokens. |
| `gen_ai.usage.cache_read_input_tokens` | Prompt-cache reads. |
| `gen_ai.usage.cache_creation_input_tokens` | Prompt-cache writes. |
| `gen_ai.usage.cost_usd` | Cost, when the exporter states one. An explicit cost always wins over a derived one. |
| `gen_ai.tool.name` | Tool name on execute_tool spans. |
| `gen_ai.conversation.id` | Session id. |
| `gen_ai.agent.id` | Agent id. |
| `gen_ai.input.messages` | Prompt content, when the exporter sends it. |
| `gen_ai.output.messages` | Response content, when the exporter sends it. |

### Not read

Listed because a reference that only says what works is not one you
can plan against.

| Attribute | |
|---|---|
| `gen_ai.usage.cache_read.input_tokens` | Prompt-cache reads under the CURRENT convention spelling (dot before the noun). Only the underscore spelling is read here; the dotted one lands with #5686, and until then an exporter that opted in to gen_ai_latest_experimental has its cached tokens read as zero. |
| `gen_ai.usage.cache_creation.input_tokens` | Prompt-cache writes under the current convention spelling. Same as above; lands with #5686. |
| `gen_ai.usage.reasoning.output_tokens` | Reasoning tokens. There is no column to put them in yet, so they are dropped rather than mis-filed into output tokens. |
| `gen_ai.response.finish_reasons` | Not yet read. Would let us spot truncation and unusual stops. |
| `gen_ai.response.time_to_first_chunk` | Not yet read. Streaming latency per span. |

## What ClawMetry does not accept

There is no endpoint that takes syslog, CEF, GELF, Apache logs or
raw text. ClawMetry's inputs are typed on arrival, and a parser
layer would exist only to accept data this product has nothing to
say about. If you want general log ingestion, use a log platform —
and point it at ClawMetry's own export, which speaks OTLP.
