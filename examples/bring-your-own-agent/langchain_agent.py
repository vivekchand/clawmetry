"""LangChain chain observed by ClawMetry via OpenLLMetry instrumentation.

Start ClawMetry first (``pip install clawmetry && clawmetry``), then:

    pip install langchain-core opentelemetry-instrumentation-langchain \
        opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
    python langchain_agent.py

Works with any LangChain chat model. With no API key it uses LangChain's
built-in ``GenericFakeChatModel`` so the telemetry pipeline is testable end
to end at zero cost. The same three lines of OpenTelemetry setup cover
LangGraph too: the instrumentor hooks LangChain's callback system, which
LangGraph nodes run through.
"""

import os
import uuid

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ── 1. Point OpenTelemetry at ClawMetry ─────────────────────────────────────
endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:8900")
resource = Resource.create({
    "service.name": os.environ.get("OTEL_SERVICE_NAME", "support-triage"),
    "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "dev"),
    # LangChain does not stamp a conversation id on its spans, so group this
    # process run as one ClawMetry session at the resource level.
    "session.id": os.environ.get("AGENT_SESSION_ID", f"support-triage-{uuid.uuid4().hex[:8]}"),
})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces"))
)

# ── 2. Instrument LangChain (OpenLLMetry) ───────────────────────────────────
from opentelemetry.instrumentation.langchain import LangchainInstrumentor  # noqa: E402

LangchainInstrumentor().instrument(tracer_provider=provider)

# ── 3. A normal LangChain chain ─────────────────────────────────────────────
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

if os.environ.get("ANTHROPIC_API_KEY"):
    from langchain_anthropic import ChatAnthropic
    model = ChatAnthropic(model="claude-sonnet-5")
else:
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    model = GenericFakeChatModel(messages=iter([
        "Priority: HIGH. Route to billing. The customer reports a duplicate charge.",
    ]))
    print("(no ANTHROPIC_API_KEY: using LangChain GenericFakeChatModel, zero cost)")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You triage support tickets. Answer with a priority and a route."),
    ("human", "{ticket}"),
])
chain = prompt | model

if __name__ == "__main__":
    out = chain.invoke({"ticket": "I was charged twice for my ClawMetry Pro seat."})
    print("chain said:", getattr(out, "content", out))
    provider.shutdown()  # flush the span batch before the process exits
    print("spans exported to", endpoint)
    print("open the ClawMetry dashboard: Tracing tab -> support-triage")
