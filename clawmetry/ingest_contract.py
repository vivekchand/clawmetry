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

# HTTP response codes returned by the OTLP receiver (REQ-OBS-OIA-001).
# Source: ``routes/meta.py::_otlp_receive`` and ``clawmetry/otlp_intake.py``.
#
# There used to be a 429 here: while a spending-limit pause was active every
# export was refused. The agents can keep running through an advisory pause,
# so the spend that followed the incident was never recorded. Intake no
# longer pauses; see OTLP_ACKNOWLEDGEMENT.
OTLP_RESPONSE_CODES: dict[int, str] = {
    200: (
        "Stored. Sent only after the local store confirmed the write. The body "
        "is an empty export response (``{}`` for OTLP/JSON, an empty protobuf "
        "message for protobuf). When some items were malformed (a span with no "
        "id or name, or an item carrying a value the store cannot hold, such "
        "as a token count beyond its range) the rest are stored and the body carries "
        "``partialSuccess`` with the refused count in ``rejectedLogRecords``, "
        "``rejectedSpans`` or ``rejectedDataPoints``. Do not retry."
    ),
    400: (
        "Malformed or undecodable body. Nothing is stored. Response body "
        "contains ``{\"error\": \"<reason>\"}``. Do not retry the same body."
    ),
    401: (
        "A request from another machine without a valid token (see "
        "Authentication). Refused before the body is read. Fix the "
        "credentials; retrying unchanged will be refused again."
    ),
    501: (
        "Binary protobuf body received but ``opentelemetry-proto`` is not "
        "installed. Install with ``pip install clawmetry[otel]`` or switch "
        "to OTLP/JSON (``Content-Type: application/json``)."
    ),
    503: (
        "Not stored: the local store did not confirm the write (the daemon "
        "that owns it is restarting, busy or unreachable). Nothing in the "
        "export is acknowledged. Retry after the ``Retry-After`` delay; items "
        "that did reach the store are recognised on retry and not counted "
        "twice."
    ),
}

# Seconds sent in ``Retry-After`` with a 503. Read by clawmetry/otlp_intake.py.
OTLP_RETRY_AFTER_SECONDS: int = 5

# When an export is acknowledged. Source: ``clawmetry/otlp_intake.py``.
OTLP_ACKNOWLEDGEMENT: str = (
    "The receiver keeps no intake queue of its own. It answers 200 only after "
    "the local store confirms the write, and 503 with ``Retry-After`` when it "
    "cannot, so a batch the store could not take stays in the exporter's own "
    "retry buffer. How long an exporter retries, and what it drops when that "
    "buffer is full, is the exporter's configuration (for the OpenTelemetry "
    "SDKs, the exporter timeout and the batch processor's queue size). A "
    "spending-limit pause on the observed agents does not pause intake: "
    "activity after a budget incident is still recorded."
)

# How a re-delivery is recognised, per endpoint. OTLP delivery is
# at-least-once, so this is what keeps a retry from becoming a second charge.
OTLP_REDELIVERY_IDENTITY: dict[str, str] = {
    "/v1/logs": (
        "A hash of the sender's ``service.name``, the session, the event name, "
        "the record's own ``time_unix_nano`` and ``observed_time_unix_nano``, "
        "its body and every attribute. A retried record replaces itself. Two "
        "model calls that differ in their own time or in any attribute (a "
        "request id, for example) are two records and both are counted; two "
        "that are identical in all of these are one."
    ),
    "/v1/traces": (
        "The span's ``span_id``. A re-delivered span replaces the stored one, "
        "so a later delivery carrying a corrected end time or status "
        "overwrites the first. The live tiles count a span once per "
        "``trace_id`` and ``span_id``."
    ),
    "/v1/metrics": (
        "Runtime-profile metrics are stored keyed by a hash of the sender, the "
        "session, the metric name, the data point's own time, its attributes "
        "and its value. Other metrics count once per data point that carries "
        "its own time; a point with no time cannot be told apart from a new "
        "one."
    ),
}

# The session a received item joins when the sender names none.
OTLP_SESSION_IDENTITY: dict[str, str] = {
    "/v1/logs": (
        "The first of ``session.id``, ``session_id``, "
        "``gen_ai.conversation.id``, ``conversation.id`` and "
        "``cursor.conversation.id``, on the record and then on the resource. "
        "A record with none of them is stored and counted in the team, "
        "repository and person rollups, but joins no session."
    ),
    "/v1/traces": (
        "The first of ``gen_ai.conversation.id``, ``session.id``, "
        "``openclaw.session_id`` and ``session_id``. When a span carries none "
        "(and its runtime is not ``openclaw``), its trace becomes the session "
        "as ``<runtime>:trace:<trace_id>``, so every trace without an id adds "
        "one session. A sender that starts sending a conversation id later "
        "starts new sessions under it; the earlier trace-derived sessions are "
        "kept as they are and are not merged."
    ),
    "/v1/metrics": (
        "``session.id`` on the data point, then on the resource. With neither, "
        "the stored row has no session."
    ),
}

# Received data that is held in memory only, and what the spend rollup reads.
OTLP_LIVE_VIEW_ONLY: str = (
    "The ``openclaw.*`` metrics and the GenAI ``gen_ai.client.token.usage`` "
    "and ``gen_ai.client.operation.duration`` metrics feed the live token, "
    "cost and run tiles only. They are held in memory, are not written to the "
    "local store and are gone after a restart; the intake status counts them "
    "as ``live_view_only``, and metrics nothing reads as ``not_read``. The "
    "live tiles remember the most recent 20,000 items when recognising a "
    "re-delivery. The spend rollup (``/api/otel/rollup``) sums received log "
    "records only: span cost is not added to it, so a sender that samples its "
    "traces does not reduce it. A group in which no record reported a cost "
    "has no spend figure rather than zero, and says how many records carried "
    "one."
)

# Authentication on the OTLP endpoints. Source: ``dashboard.py`` before_request.
OTLP_AUTH: str = (
    "A request from this machine (loopback) needs no credentials. A request "
    "from another machine must send the gateway token as ``Authorization: "
    "Bearer <token>`` (or ``?token=``) and is otherwise refused with 401 "
    "before its body is read, including when no gateway token is configured. "
    "``CLAWMETRY_OTLP_ALLOW_UNAUTH=1`` accepts unauthenticated requests from "
    "the network, for a trusted LAN only."
)

# The ``intake`` block of ``GET /api/otel-status``.
OTLP_INTAKE_STATUS: str = (
    "``GET /api/otel-status`` carries an ``intake`` block. Per signal, "
    "``items`` counts what arrived (``received``), what is in the store "
    "(``stored``), what was refused as malformed (``rejected``), what was "
    "already stored or repeated in the same export (``already_stored``), what "
    "is held only in the live tiles (``live_view_only``), metrics nothing "
    "reads (``not_read``), events not recorded because another source already "
    "reports that session (``skipped_other_source``) and items the sender was "
    "asked to send again (``retry_requested``). ``requests`` counts "
    "acknowledged, partially acknowledged, retry-requested, malformed, "
    "protobuf-unavailable and unauthorized requests, and requests received "
    "during a spending-limit pause. ``last_success_at``, ``last_failure_at`` "
    "and ``last_failure`` (a fixed category) close each signal. Counts start "
    "when the receiver starts. The block holds no record content, attribute "
    "value or credential."
)

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
        "Session or conversation identifier. Fallbacks are read in the order "
        "listed, so a LangGraph thread (``traceloop.association.properties.thread_id``, "
        "what OpenLLMetry stamps on every span below the run's top span) outranks "
        "``session.id`` on the span or the resource.",
        ["traceloop.association.properties.thread_id",
         "session.id", "openclaw.session_id", "session_id"],
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
