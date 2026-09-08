"""Pydantic AI agent observed by ClawMetry over pure OpenTelemetry.

Start ClawMetry first (``pip install clawmetry && clawmetry``), then:

    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
    python pydantic_ai_agent.py

Works with any model Pydantic AI supports. With ``ANTHROPIC_API_KEY`` set it
runs a real Claude call; without one it falls back to Pydantic AI's built-in
``TestModel`` so the whole telemetry pipeline is testable end to end at zero
cost. Either way the agent, its model calls, and its tool calls land in
ClawMetry's Tracing, Sessions, and Usage tabs.

No ClawMetry SDK, no vendor lock-in: this file only uses the OpenTelemetry
SDK and Pydantic AI's own ``InstrumentationSettings``.
"""

import os
import uuid

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ── 1. Point OpenTelemetry at ClawMetry ─────────────────────────────────────
# ClawMetry's OTLP receiver listens on the dashboard port at /v1/traces.
# service.name becomes the app's identity in the runtime switcher and the
# Agent Inventory; deployment.environment keeps dev/tst/prod separable.
endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:8900")
resource = Resource.create({
    "service.name": os.environ.get("OTEL_SERVICE_NAME", "invoice-copilot"),
    "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "dev"),
    # One process run = one conversation. AgentCore stamps a session id for
    # you; a local framework needs to say which spans belong together so
    # ClawMetry can show them as one session.
    "session.id": os.environ.get("AGENT_SESSION_ID", f"invoice-copilot-{uuid.uuid4().hex[:8]}"),
})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces"))
)

# ── 2. A normal Pydantic AI agent, instrumented ─────────────────────────────
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.models.instrumented import InstrumentationSettings  # noqa: E402

if os.environ.get("ANTHROPIC_API_KEY"):
    model = "anthropic:claude-sonnet-5"
else:
    from pydantic_ai.models.test import TestModel
    model = TestModel()
    print("(no ANTHROPIC_API_KEY: using pydantic-ai TestModel, zero cost)")

# One line turns on OpenTelemetry for every agent in the process.
Agent.instrument_all(InstrumentationSettings(tracer_provider=provider))

agent = Agent(
    model,
    system_prompt="You are an invoice lookup copilot. Use your tools.",
)


@agent.tool_plain
def lookup_invoice(invoice_id: str) -> str:
    """Look up one invoice by its id."""
    return f"Invoice {invoice_id}: $1,240.00, due 2026-09-15, status OPEN"


if __name__ == "__main__":
    result = agent.run_sync("What is the status of invoice INV-1042?")
    print("agent said:", result.output)
    provider.shutdown()  # flush the span batch before the process exits
    print("spans exported to", endpoint)
    print("open the ClawMetry dashboard: Tracing tab -> invoice-copilot")
