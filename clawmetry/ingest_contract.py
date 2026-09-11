"""clawmetry/ingest_contract.py — the declared ingest/1 contract registry.

Single source of truth for the two ingest surfaces ClawMetry exposes:

* **OTLP receiver** — ``/v1/metrics``, ``/v1/traces``, ``/v1/logs``
  (standard OpenTelemetry HTTP/JSON and HTTP/protobuf, plus gzip).
* **Run/event ingest API** — ``/api/v1/runs*``
  (structured run/step records from custom runtimes; Pro feature).

``docs/INGEST.md`` is generated from this module by
``scripts/gen_ingest_doc.py``; ``tests/test_ingest_doc_drift.py`` fails CI
when the committed doc drifts from the generator output.

Versioning: evolution inside ``ingest/1`` is additive only. Adding an
endpoint, a content-type, or an attribute is fine. Removing or renaming
one requires bumping to ``ingest/2``.
"""
from __future__ import annotations

CONTRACT_VERSION = "ingest/1"

# ── OTLP receiver ────────────────────────────────────────────────────────────

# Endpoints served by ``routes/meta.py`` (bp_otel / bp_otlp_traces).
OTLP_ENDPOINTS: dict[str, dict] = {
    "/v1/metrics": {
        "methods": ["POST"],
        "doc": (
            "OTLP metrics. Ingests ``gen_ai.client.token.usage`` counters "
            "and ``gen_ai.client.operation.duration`` histograms into the "
            "token/cost tiles."
        ),
        "json_support": True,
        "protobuf_support": True,
    },
    "/v1/traces": {
        "methods": ["POST"],
        "doc": (
            "OTLP traces. Ingests GenAI spans (LLM calls, tool calls, "
            "sub-agent spawns) into the span tree and session timeline."
        ),
        "json_support": True,
        "protobuf_support": True,
    },
    "/v1/logs": {
        "methods": ["POST"],
        "doc": (
            "OTLP logs. Ingests the agent event stream exported by "
            "Claude Code, Codex, and other runtimes (cost/token/model "
            "per log record) into the cost and usage tiles."
        ),
        "json_support": True,
        "protobuf_support": True,
    },
}

# Content-Type values accepted on all three OTLP endpoints.
# Source: ``dashboard.py::_otlp_decode``.
OTLP_CONTENT_TYPES: dict[str, str] = {
    "application/x-protobuf": (
        "Binary protobuf encoding. Requires ``pip install clawmetry[otel]`` "
        "(``opentelemetry-proto`` + ``protobuf``). Raises HTTP 501 when the "
        "extra is absent."
    ),
    "application/json": (
        "OTLP/JSON encoding. Works on a plain ``pip install clawmetry`` with "
        "no extras. ``ignore_unknown_fields`` is set, so forward-compat keys "
        "from newer producers do not cause a 400."
    ),
}

# Content-Encoding values accepted on all OTLP endpoints.
# Source: ``dashboard.py::_gunzip_safe``.
OTLP_ENCODINGS: list[str] = ["identity", "gzip"]

# Hard cap on the decompressed body size.
# Source: ``dashboard.py::_OTLP_MAX_DECOMPRESSED``.
OTLP_MAX_DECOMPRESSED_MB: int = 64
OTLP_MAX_DECOMPRESSED_ENVVAR: str = "CLAWMETRY_OTLP_MAX_DECOMPRESSED_MB"

# HTTP response codes returned by the OTLP receiver.
# Source: ``routes/meta.py::_otlp_receive``.
OTLP_RESPONSE_CODES: dict[int, str] = {
    200: "Accepted. Response body is ``{}`` (empty JSON object).",
    400: "Malformed or undecodable body. Response body contains ``{\"error\": \"<reason>\"}``.",
    429: "Budget limit exceeded; OTLP intake is paused. Response body contains ``{\"paused\": true}``.",
    501: (
        "Binary protobuf body received but ``opentelemetry-proto`` is not "
        "installed. Install with ``pip install clawmetry[otel]`` or switch "
        "to OTLP/JSON (``Content-Type: application/json``)."
    ),
}

# ── gen_ai.* attribute mapping ───────────────────────────────────────────────

# Span / log-record attributes read by ``dashboard.py::_otel_to_row``.
# Values are (description, fallback_attrs) tuples.
GEN_AI_ATTRS_READ: dict[str, tuple[str, list[str]]] = {
    "gen_ai.request.model": (
        "Model name used for the request.",
        ["gen_ai.response.model", "llm.model", "model"],
    ),
    "gen_ai.usage.input_tokens": (
        "Input token count.",
        ["llm.usage.prompt_tokens", "input_tokens"],
    ),
    "gen_ai.usage.output_tokens": (
        "Output token count.",
        ["llm.usage.completion_tokens", "output_tokens"],
    ),
    "gen_ai.usage.total_tokens": (
        "Total token count.",
        ["llm.usage.total_tokens", "total_tokens"],
    ),
    "gen_ai.usage.cache_read.input_tokens": (
        "Cached input tokens read (Anthropic / OpenAI prompt caching).",
        ["gen_ai.usage.cache_read_input_tokens", "cache_read_input_tokens"],
    ),
    "gen_ai.usage.cache_creation.input_tokens": (
        "Cache-write tokens (Anthropic prompt caching).",
        ["gen_ai.usage.cache_creation_input_tokens", "cache_creation_input_tokens"],
    ),
    "gen_ai.usage.cost_usd": (
        "Pre-computed cost in USD. When absent, ClawMetry prices the tokens locally.",
        ["llm.usage.cost", "cost_usd"],
    ),
    "gen_ai.provider.name": (
        "Provider string (e.g. ``anthropic``, ``openai``).",
        ["gen_ai.system", "llm.provider", "provider"],
    ),
    "gen_ai.tool.name": (
        "Name of the tool called (on ``execute_tool`` spans).",
        ["tool.name", "code.function"],
    ),
    "gen_ai.conversation.id": (
        "Session or conversation identifier.",
        ["session.id", "openclaw.session_id", "session_id"],
    ),
    "gen_ai.agent.id": (
        "Agent identifier.",
        ["agent.id", "openclaw.agent_id", "agent_id"],
    ),
    "gen_ai.input.messages": (
        "Input message list (current GenAI semconv).",
        ["gen_ai.prompt"],
    ),
    "gen_ai.output.messages": (
        "Output message list (current GenAI semconv).",
        ["gen_ai.completion"],
    ),
    "gen_ai.operation.name": (
        "Operation kind (``chat``, ``text_completion``, ``generate_content``). "
        "Read to decide whether a span counts as a run: OpenLLMetry and "
        "traceloop-sdk name LLM spans ``<vendor>.chat`` / ``<vendor>.completion`` "
        "and tag the operation here, so without it a bring-your-own-agent "
        "install records spans while the live Runs tile stays at zero.",
        [],
    ),
}

# Attributes that appear in GenAI semconv but are NOT yet consumed.
#
# This list is published in docs/INGEST.md, so a name here is a promise to the
# reader that sending it changes nothing. ``gen_ai.operation.name`` was listed
# and was in fact read by ``dashboard.py::_process_otlp_traces`` to classify a
# span as a run -- caught by this module's own drift check (#5682). Verify
# against the code before adding a name, not against intent.
#
# ``gen_ai.agent.name`` is genuinely unread on the ingest path: ClawMetry's own
# exporter WRITES it (``clawmetry/otel_exporter.py``), and nothing reads it back.
GEN_AI_ATTRS_NOT_READ: list[str] = [
    "gen_ai.agent.name",
]

# ── Run / event ingest API ───────────────────────────────────────────────────

# Endpoints served by ``routes/runtime_ingest.py`` (bp_runtime_ingest).
# The stub OSS blueprint returns HTTP 402 on all Pro-gated write paths.
RUN_ENDPOINTS: dict[str, dict] = {
    "GET /api/v1/runtimes": {
        "tier": "free",
        "doc": "List runtimes ClawMetry knows about. Same data the runtime switcher reads.",
    },
    "POST /api/v1/runs": {
        "tier": "pro",
        "doc": "Open a run. Returns ``{ok, run_id, runtime}``.",
    },
    "POST /api/v1/runs/<run_id>/events": {
        "tier": "pro",
        "doc": "Append one or many events to an open run.",
    },
    "POST /api/v1/runs/<run_id>/end": {
        "tier": "pro",
        "doc": "Mark the run ended. Optional — the run also closes on inactivity.",
    },
    "GET /api/v1/runs/<run_id>": {
        "tier": "pro",
        "doc": "Read-back: confirm the run was persisted and return its metadata.",
    },
}

# HTTP response codes for the run/event endpoints.
RUN_RESPONSE_CODES: dict[int, str] = {
    200: "Success (GET requests).",
    201: "Accepted (POST requests).",
    400: "Malformed request body.",
    401: "Token required but missing or incorrect.",
    402: "Pro plan required; OSS stub returns this on all write endpoints.",
    429: "Rate limit or budget pause.",
}
