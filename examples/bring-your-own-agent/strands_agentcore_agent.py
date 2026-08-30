"""Strands agent (the AWS Bedrock AgentCore SDK) observed by ClawMetry.

This is the same agent shape the awslabs agentcore-samples tutorials deploy
to AgentCore Runtime. Locally it runs with Anthropic or Bedrock credentials;
deployed to AgentCore it needs NO code change, because the integration is
environment variables on the runtime resource (see the Terraform snippet in
README.md and docs/BRING_YOUR_OWN_AGENT.md).

Local run:

    pip install 'strands-agents[anthropic]' opentelemetry-exporter-otlp-proto-http
    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
    export OTEL_RESOURCE_ATTRIBUTES="service.name=payments-agent,deployment.environment=dev"
    export ANTHROPIC_API_KEY=...   # or AWS credentials for the Bedrock default
    python strands_agentcore_agent.py

On AgentCore Runtime, ADOT auto-instruments the agent; re-pointing
OTEL_EXPORTER_OTLP_ENDPOINT at a ClawMetry inside your VPC is the same
partner-observability pattern AWS documents for Langfuse, Instana and
Datadog. Keep CloudWatch too by fanning out through an OTel Collector.
"""

import os
import uuid

from strands import Agent, tool
from strands.telemetry import StrandsTelemetry

# ── 1. Point Strands' OpenTelemetry at ClawMetry ────────────────────────────
# StrandsTelemetry honors OTEL_EXPORTER_OTLP_ENDPOINT and
# OTEL_RESOURCE_ATTRIBUTES; nothing ClawMetry-specific in the agent.
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:8900")
os.environ.setdefault(
    "OTEL_RESOURCE_ATTRIBUTES",
    "service.name=payments-agent,deployment.environment=dev,"
    f"session.id=payments-{uuid.uuid4().hex[:8]}",
)
StrandsTelemetry().setup_otlp_exporter()


# ── 2. A normal Strands agent ───────────────────────────────────────────────
@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up one invoice by its id."""
    return f"Invoice {invoice_id}: $1,240.00, due 2026-09-15, status OPEN"


if os.environ.get("ANTHROPIC_API_KEY"):
    from strands.models.anthropic import AnthropicModel
    model = AnthropicModel(model_id="claude-sonnet-5", max_tokens=512)
    agent = Agent(model=model, tools=[lookup_invoice])
else:
    # Default: Bedrock, using your AWS credentials, same as on AgentCore.
    agent = Agent(tools=[lookup_invoice])

if __name__ == "__main__":
    result = agent("What is the status of invoice INV-1042?")
    print(result)
    print("open the ClawMetry dashboard: Tracing tab -> payments-agent")
