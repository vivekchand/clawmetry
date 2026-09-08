"""clawmetry/ingest_contract.py -- what ClawMetry accepts, declared once.

Why this module exists
----------------------
Four things describe the ingest surface, and until now none of them
shared a source:

1. the server, which validates requests;
2. ``docs/INGEST.md``, which a person reads;
3. the per-runtime setup prompts, which an AGENT reads -- and where a
   wrong header name is a silent failure, because the agent will
   confidently write it;
4. the public reference on the landing site, where a claim the repo
   denies now fails the truthfulness gate.

Four hand-maintained descriptions of one contract is four chances to
drift, and the drift is worst in (3): a prompt that teaches an agent a
header we do not accept is worse than no prompt at all.

So the contract is data. The server reads its constants from here, the
doc is generated from here, and CI fails when the committed doc and this
file disagree -- the same shape as ``query_contract.py`` and
``gen_query_contract_doc.py`` for the read side.

What this is NOT
----------------
Not a schema validator and not a parser registry. ClawMetry's inputs are
typed on arrival: OTLP has its own proto, and the run/event API takes a
declared shape. There is deliberately no "accepts any format" surface
here to describe, because accepting syslog, CEF or raw text would mean
accepting data this product has nothing to say about.
"""

from __future__ import annotations

CONTRACT_VERSION = "ingest/1"

# ── Headers ─────────────────────────────────────────────────────────────
# Lower-case on the wire. HTTP header lookup is case-insensitive, but
# every example we publish uses this spelling so a copy-paste, a grep and
# an agent's guess all agree.

HEADER_KEY = "x-clawmetry-key"
HEADER_RUNTIME = "x-clawmetry-runtime"
HEADER_ENV = "x-clawmetry-env"
HEADER_LEGACY_TOKEN = "X-ClawMetry-Token"

#: Body cap, enforced before decode. A 40 MB protobuf is refused with a
#: sentence rather than parsed until something runs out of patience.
MAX_BODY_BYTES = 10 * 1024 * 1024

#: Events per run/event request. Already the write API's cap.
MAX_EVENTS_PER_BATCH = 1000

HEADERS = (
    {
        "name": HEADER_KEY,
        "required": "for a caller that is not on this machine",
        "doc": "An ingest key: clawmetry key create --name ci --scope write:ingest",
    },
    {
        "name": HEADER_RUNTIME,
        "required": "no",
        "doc": (
            "Which runtime is pushing -- claude_code, my-engine, anything "
            "matching [a-z0-9][a-z0-9_-]{0,39}. An unrecognised name is "
            "accepted: in-house engines are a supported case. Sets the "
            "resource's service.name, which is what the runtime is derived "
            "from. Without it the runtime comes from service.name as sent."
        ),
    },
    {
        "name": HEADER_ENV,
        "required": "no",
        "doc": (
            "Environment or project label -- production, team-a.staging. "
            "Sets deployment.environment. This is the one grouping axis "
            "above runtime, and deliberately the only one."
        ),
    },
    {
        "name": "Content-Type",
        "required": "yes, on OTLP",
        "doc": "application/x-protobuf or application/json. See encodings.",
    },
    {
        "name": "Content-Encoding",
        "required": "no",
        "doc": "gzip, if you compressed the body.",
    },
)

# ── Surfaces ────────────────────────────────────────────────────────────

SURFACES = (
    {
        "path": "/v1/traces",
        "method": "POST",
        "accepts": "OTLP traces",
        "doc": (
            "Spans. The GenAI convention's model-call spans land here, and "
            "this is the surface an OTel SDK or Collector already speaks."
        ),
    },
    {
        "path": "/v1/metrics",
        "method": "POST",
        "accepts": "OTLP metrics",
        "doc": "Counters and histograms.",
    },
    {
        "path": "/v1/logs",
        "method": "POST",
        "accepts": "OTLP logs",
        "doc": (
            "Log records. Claude Code and Codex export their per-turn event "
            "stream this way, with cost and tokens per record."
        ),
    },
    {
        "path": "/api/v1/runs",
        "method": "POST",
        "accepts": "JSON",
        "doc": "Open a run; returns run_id. For engines that would rather "
               "push typed records than build OTLP.",
    },
    {
        "path": "/api/v1/runs/<id>/events",
        "method": "POST",
        "accepts": "JSON",
        "doc": f"Append one event or a batch of up to {MAX_EVENTS_PER_BATCH}.",
    },
    {
        "path": "/api/v1/runs/<id>/end",
        "method": "POST",
        "accepts": "JSON",
        "doc": "Mark the run ended. Optional.",
    },
    {
        "path": "/api/v1/runs/<id>",
        "method": "GET",
        "accepts": "-",
        "doc": "Read back: was the run persisted?",
    },
    {
        "path": "/api/v1/runtimes",
        "method": "GET",
        "accepts": "-",
        "doc": "The runtimes ClawMetry knows about. Free, no key needed.",
    },
)

# ── Encodings ───────────────────────────────────────────────────────────

CONTENT_TYPES = (
    ("application/x-protobuf", "OTLP protobuf. The default for the OTel "
                               "Collector and the SDKs, and smaller on the wire."),
    ("application/json", "OTLP/JSON. Useful when a client cannot produce "
                         "protobuf -- a script, a serverless function, a "
                         "platform that only emits JSON."),
)

CONTENT_ENCODINGS = (
    ("gzip", "Accepted on every surface."),
)

# ── Responses ───────────────────────────────────────────────────────────
# Every one of these carries a sentence in its body, not only a code.
# These are read inside an agent's terminal with no documentation open.

RESPONSES = (
    (200, "Accepted."),
    (400, "The body did not decode, or a routing header was malformed. The "
          "message names what was expected."),
    (401, "No key, or a key this ClawMetry does not know. It may have been "
          "revoked, or belong to a different install."),
    (403, "A valid key that lacks write:ingest. Different from 401 on "
          "purpose: 'your key is wrong' and 'your key is fine and may not "
          "do this' send you to different fixes."),
    (413, f"Body over {MAX_BODY_BYTES // (1024 * 1024)} MB. Split the batch, "
          "or compress with Content-Encoding: gzip."),
    (429, "Intake is paused because a budget limit was exceeded."),
    (501, "OTLP support is not installed on this ClawMetry: "
          "pip install clawmetry[otel]"),
)

# ── Authentication ──────────────────────────────────────────────────────

AUTH_MODES = (
    {
        "name": "Loopback",
        "when": "The agent and ClawMetry are on the same machine.",
        "how": "Nothing to configure. This is the zero-config path and it is "
               "what most installs use.",
    },
    {
        "name": "Gateway token",
        "when": "An exporter elsewhere on a trusted LAN.",
        "how": "Authorization: Bearer $OPENCLAW_GATEWAY_TOKEN",
    },
    {
        "name": "Ingest key",
        "when": "Anything that is not on this machine: CI, a container, a "
                "serverless function, a hosted product, a teammate's laptop.",
        "how": f"clawmetry key create --name ci --scope write:ingest, then "
               f"{HEADER_KEY}: cmk_...",
    },
)

# ── GenAI attributes ────────────────────────────────────────────────────
# Saying what we do NOT read is what makes the rest of this credible, and
# it is checked against the source: tests/test_ingest_contract_drift.py
# asserts every name below appears (or does not appear) in the mapper.

GENAI_READ = (
    ("gen_ai.operation.name", "Marks the span as a model call."),
    ("gen_ai.request.model", "The model asked for."),
    ("gen_ai.response.model", "The model actually served."),
    ("gen_ai.provider.name", "Provider; gen_ai.system is read as the older name."),
    ("gen_ai.usage.input_tokens", "Input tokens."),
    ("gen_ai.usage.output_tokens", "Output tokens."),
    ("gen_ai.usage.cache_read_input_tokens", "Prompt-cache reads."),
    ("gen_ai.usage.cache_creation_input_tokens", "Prompt-cache writes."),
    ("gen_ai.usage.cost_usd", "Cost, when the exporter states one. An "
                              "explicit cost always wins over a derived one."),
    ("gen_ai.tool.name", "Tool name on execute_tool spans."),
    ("gen_ai.conversation.id", "Session id."),
    ("gen_ai.agent.id", "Agent id."),
    ("gen_ai.input.messages", "Prompt content, when the exporter sends it."),
    ("gen_ai.output.messages", "Response content, when the exporter sends it."),
)

GENAI_NOT_READ = (
    # These two are FIXED in #5685 / PR #5686, which is open against main
    # while this branch is stacked elsewhere. Listing them here is the
    # honest state of THIS tree, and the drift guard in the other
    # direction (an unread attribute that turns out to be read) makes
    # whichever PR merges second update this list -- which is the point of
    # having both directions checked.
    ("gen_ai.usage.cache_read.input_tokens",
     "Prompt-cache reads under the CURRENT convention spelling (dot before "
     "the noun). Only the underscore spelling is read here; the dotted one "
     "lands with #5686, and until then an exporter that opted in to "
     "gen_ai_latest_experimental has its cached tokens read as zero."),
    ("gen_ai.usage.cache_creation.input_tokens",
     "Prompt-cache writes under the current convention spelling. Same as "
     "above; lands with #5686."),
    ("gen_ai.usage.reasoning.output_tokens",
     "Reasoning tokens. There is no column to put them in yet, so they are "
     "dropped rather than mis-filed into output tokens."),
    ("gen_ai.response.finish_reasons",
     "Not yet read. Would let us spot truncation and unusual stops."),
    ("gen_ai.response.time_to_first_chunk",
     "Not yet read. Streaming latency per span."),
)

__all__ = [
    "CONTRACT_VERSION", "HEADER_KEY", "HEADER_RUNTIME", "HEADER_ENV",
    "HEADER_LEGACY_TOKEN", "MAX_BODY_BYTES", "MAX_EVENTS_PER_BATCH",
    "HEADERS", "SURFACES", "CONTENT_TYPES", "CONTENT_ENCODINGS",
    "RESPONSES", "AUTH_MODES", "GENAI_READ", "GENAI_NOT_READ",
]
