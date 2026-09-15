"""A one-tool LangGraph agent, observed by ClawMetry over OpenTelemetry.

The instrumentation is OpenLLMetry (``opentelemetry-instrumentation-langchain``),
which hooks LangChain's callback system and therefore every LangGraph node.
Nothing ClawMetry-specific runs in this process: it is a standard OTLP/HTTP
exporter pointed at ClawMetry's receiver.

Run it (ClawMetry first, ``pip install 'clawmetry[otel]' && clawmetry``):

    pip install -r requirements.txt
    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
    python agent.py --thread support-42

Options:

    --thread ID     LangGraph thread id. Every run on one thread is one
                    ClawMetry session. Omit it and each run is its own session
                    (one per trace).
    --stream        run the graph with ``stream()`` instead of ``invoke()``.
    --question TXT  what to ask the agent.

Remote ClawMetry: set ``OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>"``.
The OTLP exporter reads that variable itself.

Model: no provider key is needed. The default model is ``StubChatModel`` below,
a deterministic chat model that asks for the tool once, then answers, and
reports fixed token usage. It proves the telemetry pipeline end to end at zero
cost; it does not prove a provider integration. To use a real model, replace
``build_model()`` with any LangChain chat model that supports tool calling (for
example ``ChatAnthropic`` from ``langchain-anthropic``); nothing else changes.

tests/test_otel_recipe_langgraph.py and scripts/verify_otel_recipe_langgraph.py
depend on the stub's token figures (STUB_USAGE) and on the tool name.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, List, Optional

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

APP_NAME = "invoice-agent"
TOOL_NAME = "lookup_invoice"
MODEL_NAME = "claude-sonnet-4-5"
# (input, output) tokens the stub reports for its two model calls in one run:
# the call that requests the tool, then the call that answers.
STUB_USAGE = ((120, 18), (160, 9))


def setup_telemetry() -> TracerProvider:
    """Point OpenTelemetry at ClawMetry and instrument LangChain/LangGraph."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:8900")
    resource = Resource.create({
        # service.name is the app's identity in ClawMetry (runtime switcher,
        # Agent Inventory, every per-runtime view).
        "service.name": os.environ.get("OTEL_SERVICE_NAME", APP_NAME),
        "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "dev"),
    })
    provider = TracerProvider(resource=resource)
    # Headers (OTEL_EXPORTER_OTLP_HEADERS) are read by the exporter itself.
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")))

    from opentelemetry.instrumentation.langchain import LangchainInstrumentor
    LangchainInstrumentor().instrument(tracer_provider=provider)
    return provider


def build_model():
    """The chat model. Replace with a real one to call a provider."""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    class StubChatModel(BaseChatModel):
        """Asks for the tool once, then answers. Reports fixed token usage."""

        model_name: str = MODEL_NAME

        @property
        def _llm_type(self) -> str:
            return "stub-chat"

        def bind_tools(self, tools: Any, **kwargs: Any) -> "StubChatModel":
            return self

        def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None,
                      run_manager: Any = None, **kwargs: Any) -> ChatResult:
            answered = any(isinstance(m, ToolMessage) for m in messages)
            (tin, tout) = STUB_USAGE[1] if answered else STUB_USAGE[0]
            usage = {"input_tokens": tin, "output_tokens": tout, "total_tokens": tin + tout}
            if answered:
                result = next(m for m in reversed(messages) if isinstance(m, ToolMessage))
                msg = AIMessage(content=f"Here is what I found. {result.content}",
                                usage_metadata=usage,
                                response_metadata={"model_name": self.model_name})
            else:
                msg = AIMessage(content="", tool_calls=[{
                    "name": TOOL_NAME, "args": {"invoice_id": "INV-1042"}, "id": "call_1",
                }], usage_metadata=usage, response_metadata={"model_name": self.model_name})
            return ChatResult(generations=[ChatGeneration(message=msg)],
                              llm_output={"model_name": self.model_name})

    return StubChatModel()


def build_graph():
    """agent -> (tool call?) -> tools -> agent -> END."""
    from langchain_core.tools import tool
    from langgraph.graph import START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    @tool(TOOL_NAME)
    def lookup_invoice(invoice_id: str) -> str:
        """Look up one invoice by its id."""
        return f"Invoice {invoice_id}: $1,240.00, due 2026-10-15, status OPEN."

    tools = [lookup_invoice]
    model = build_model().bind_tools(tools)

    def agent(state: MessagesState):
        return {"messages": [model.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--thread", default=None)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--question", default="What is the status of invoice INV-1042?")
    args = parser.parse_args()

    provider = setup_telemetry()
    app = build_graph()
    inputs = {"messages": [("user", args.question)]}
    config = {"configurable": {"thread_id": args.thread}} if args.thread else {}

    if args.stream:
        final = None
        for state in app.stream(inputs, config=config, stream_mode="values"):
            final = state
    else:
        final = app.invoke(inputs, config=config)
    print("agent said:", final["messages"][-1].content)

    # Flush the batch before a short-lived process exits, or spans are lost.
    provider.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
