# LangGraph recipe: a one-tool agent observed over OpenTelemetry

A minimal LangGraph agent with one tool (`lookup_invoice`), instrumented with OpenLLMetry and exporting OTLP to ClawMetry. No ClawMetry SDK and no provider key: the model is a deterministic stub that reports fixed token usage.

This exact file runs in CI on every change (the `otel-recipe-langgraph` job in `.github/workflows/ci.yml`), against a live dashboard, with the versions in `requirements.txt`. Full guide, including what was verified and what was not: [`docs/OTEL_RECIPE_LANGGRAPH.md`](../../../docs/OTEL_RECIPE_LANGGRAPH.md).

```bash
pip install 'clawmetry[otel]' && clawmetry        # dashboard and OTLP receiver on :8900

# in the agent's own environment
pip install -r requirements.txt
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
python agent.py --thread support-42               # one session per thread
python agent.py --thread support-42 --stream      # same session, second run
python agent.py                                   # no thread: one session per run
```

Sending to ClawMetry on another machine:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://clawmetry.internal:8900
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <gateway token>"
```

To call a real model, replace `build_model()` in `agent.py` with any LangChain chat model that supports tool calling. The CI check proves the telemetry pipeline, not a provider integration.
