# Bring your own agent: AgentCore, Pydantic AI, LangChain

ClawMetry observes any agent that speaks OpenTelemetry. These examples point three popular stacks at ClawMetry's built-in OTLP receiver, with no ClawMetry SDK and no code changes beyond standard OTel setup. Full guide: [`docs/BRING_YOUR_OWN_AGENT.md`](../../docs/BRING_YOUR_OWN_AGENT.md).

Start ClawMetry first:

```bash
pip install 'clawmetry[otel]' && clawmetry     # dashboard + OTLP receiver on :8900
```

| Example | Stack | Needs an API key? |
|---|---|---|
| `pydantic_ai_agent.py` | Pydantic AI (native OTel instrumentation) | No. Falls back to `TestModel`, zero cost |
| `langchain_agent.py` | LangChain via OpenLLMetry instrumentation | No. Falls back to `GenericFakeChatModel` |
| `strands_agentcore_agent.py` | Strands (the AWS Bedrock AgentCore SDK) | Yes: `ANTHROPIC_API_KEY` or AWS credentials |

Run any of them:

```bash
pip install pydantic-ai-slim opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
python pydantic_ai_agent.py
```

Then open the dashboard: the app appears in the runtime switcher and Agent Inventory as `<service.name> (OTel)`, its runs land in the Tracing tab as span trees, each conversation becomes a row in Sessions, and Usage shows tokens plus dollar cost (derived from the model's pricing when spans carry token counts but no cost, which is the OTel norm).

## Deploying to AWS Bedrock AgentCore

The integration is environment variables on the AgentCore runtime resource. With Terraform:

```hcl
environment_variables = {
  AGENT_OBSERVABILITY_ENABLED = "true"
  OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
  OTEL_EXPORTER_OTLP_ENDPOINT = "https://clawmetry.observability.internal:8900"
  OTEL_EXPORTER_OTLP_HEADERS  = "Authorization=Bearer ${var.clawmetry_token}"
  OTEL_RESOURCE_ATTRIBUTES    = "service.name=${var.agent_name},deployment.environment=${var.environment}"
}
```

Keep CloudWatch and X-Ray working by pointing the exporter at an OTel Collector that fans out to both destinations. `deployment.environment` keeps Dev, Test and Prod fleets separable in ClawMetry. Off-box senders authenticate with the gateway token as a Bearer header.

A working AgentCore project to try this on: the [awslabs agentcore-samples](https://github.com/awslabs/agentcore-samples) repository, whose partner-observability tutorials use exactly this exporter re-pointing pattern.
