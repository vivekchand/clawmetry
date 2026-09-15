# LiteLLM gateway usage

If your assistants send their model calls through a [LiteLLM](https://github.com/BerriAI/litellm) proxy, ClawMetry can show what that traffic cost **by team, by person and by virtual key**, using the identity and the prices LiteLLM already has. Nothing changes in your apps.

Tested against **LiteLLM 1.83.7**, a proxy backed by its own Postgres database (virtual keys and teams need one). CI runs that exact version end to end on every change to this path: `.github/workflows/litellm-gateway.yml`.

## Turn it on

Add LiteLLM's OpenTelemetry callback to the proxy config:

```yaml
litellm_settings:
  callbacks: ["otel"]
```

and point its exporter at ClawMetry's receiver when you start the proxy:

```bash
OTEL_EXPORTER=otlp_http \
OTEL_ENDPOINT=http://127.0.0.1:8900/v1/traces \
OTEL_SERVICE_NAME=litellm-gateway \
litellm --config config.yaml
```

The proxy's own environment needs the OpenTelemetry packages, which `litellm[proxy]` does not install:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

Without them LiteLLM logs `No module named 'opentelemetry'` as a non-blocking error, keeps serving requests, and exports nothing, so ClawMetry shows no gateway usage at all. CI uses 1.44.0 of all three.

LiteLLM's default exporter sends protobuf, so the ClawMetry that receives it needs `pip install clawmetry[otel]`. Keep LiteLLM's default tracer name (do not set `OTEL_TRACER_NAME`): ClawMetry recognises LiteLLM's telemetry by that name together with the `model_id` resource attribute LiteLLM adds.

Spend appears on the **Usage** tab, in the *Cost by Team* card, under **Through your LiteLLM gateway**, and in `GET /api/usage/by-team` as the `gateway` object.

## What you get

For every request the proxy served:

| Kept | Where it comes from |
|------|---------------------|
| Team, team name, user, user email, organisation, key name | The key LiteLLM authenticated (`metadata.user_api_key_*`) |
| The model the caller asked for, and the deployment model LiteLLM called | `gen_ai.response.model` (the proxy returns the model group), `hidden_params.litellm_model_name` / `gen_ai.request.model` |
| Provider, input and output tokens, cache-read and cache-write tokens when the provider reported them | `gen_ai.system`, `gen_ai.usage.*`, `metadata.usage_object` |
| Spend | `gen_ai.cost.total_cost`, falling back to `hidden_params.response_cost` |
| Streamed or not, succeeded or failed, start time and duration | `llm.is_streaming`, span status and `error.type`, the span |
| Trace id, parent span id, provider response id | the span |

Per team, the Usage card shows requests, failed requests, spend, and each person and key under it.

## How the numbers are counted

* **Spend is LiteLLM's figure, labelled as such.** It is what LiteLLM priced from its model cost map or your custom pricing, in US dollars. ClawMetry does not re-price it, and it is not your provider's invoice. On the card it carries the same cost label as every other cost in ClawMetry, *published rates* (usage value, not a bill), and its tooltip names LiteLLM as the source of the rate. In `GET /api/usage/by-team` the `gateway` object says `cost_source: "gateway_reported"` (in the price book's terms, `priced_from: "vendor_reported"`, which maps to the same *published rates* label), and its `provenance` map holds the full label for each spend figure.
* **Upstream calls are not priced a second time.** If ClawMetry's HTTP interceptor is loaded inside the LiteLLM proxy process, the proxy's calls to its providers (Azure OpenAI deployments included) are recorded without a cost and marked `via_gateway: "gateway:litellm"`, because the request's cost is already the gateway record above.
* **No reported cost is not zero.** A request that succeeded without a cost is counted and listed as *not priced*; a team with no priced request shows *not reported*, not `$0.00`.
* **Failed requests** are counted per team, apart from successful ones.
* **Cached answers are not charged twice.** When LiteLLM answers from its own response cache, its telemetry still carries the full model cost, but LiteLLM's spend log charges nothing. ClawMetry recognises the repeat by its provider response id and counts it as a request without charging it, whichever of the two arrives first.
* **Resent telemetry changes nothing.** An exporter that retries a batch replaces the same records.
* **Retries inside LiteLLM** are recorded the way LiteLLM records them: one request, with its final outcome.

## Kept apart from your agents' costs

A call an agent made *through* the proxy is already in that agent's own cost. So the gateway figure is a **separate subtotal**. It is never added to the agent totals, a proxied request never becomes an agent session, and the proxy never appears as an agent, in the runtime switcher or on the Agents tab.

To tell you how much overlaps, the card says how many gateway requests share a trace with telemetry from another source (an agent that propagates W3C `traceparent` to the proxy), and how many could not be matched. An unmatched request may still be inside an agent's cost; ClawMetry says so rather than guessing.

If you were already exporting LiteLLM traces to ClawMetry before this, those earlier requests stay as they were stored (one small "session" each, under a runtime named after the proxy). Requests from now on are counted as described here.

## Who a request belongs to

Attribution uses only the identity LiteLLM derived from the **authenticated key**. A caller can put `team_id` in a request's `metadata`, and LiteLLM copies it onto the span as `metadata.team_id`; ClawMetry ignores it. The `user` field a caller sends is kept for the record as a caller-supplied label and is never used as the user.

The receiver authenticates **who is sending** telemetry (loopback, the gateway token), not what a trusted sender writes inside it. Anyone who can post to `/v1/traces` can post a span that claims a team. Expose the receiver only to your proxy. OTLP over plain HTTP is not encrypted, and TLS to the receiver protects the connection, not the content end to end.

## Not included

* An importer for LiteLLM's database or its `/spend/logs` API. The OpenTelemetry export already carries per-request cost and identity, and reading the database would need its credential or the proxy's master key.
* Negotiated rates or a price book, budgets per project, and labels for vendor-reported versus contract prices on the other cost surfaces.
* Matching a gateway request to an agent call that did not propagate trace context.
* The hosted dashboard, which has no OpenTelemetry receiver.
