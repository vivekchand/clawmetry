# Feature Blueprint: Bring-Your-Own-Agent OTel Ingest and ClawMetry SDK

> Local mirror of the Software Factory Feature Blueprint of the same name
> (project `b415065f-ab2f-4f53-8864-0c009fd098cb`). The hosted record is the
> system of record; this file exists so drift-bot, PR review, and headless
> agents can read the same spec without a factory login. When the hosted
> blueprint is created or updated, keep this file in step (FLYWHEEL 1f).

## Feature Summary

A developer building an AI application should be able to see their agent's
traces in ClawMetry within one minute, without learning ClawMetry. Two doors
lead to the same room: point any OpenTelemetry-instrumented application at the
machine (no code change, standard OTLP endpoint), or add a few lines of the
ClawMetry SDK to a Python or TypeScript agent. Whichever door they use, the
application appears on its own in the runtime switcher, its traces open in the
Tracing tab with a real waterfall, and its cost and tokens roll into the same
tiles as a native runtime.

Most of the ingest half already exists and is proven (`#2822`, `#2871`): the
OTLP receiver persists spans, `service.name` becomes an `agent_type`, and the
daemon rolls foreign applications into `runtimeSummary`. This blueprint covers
the five gaps between "spans are stored" and "a stranger's agent is visible in
five seconds": the default OTLP port, the protobuf dependency, the Tracing tab
reading `spans`, the SDK itself, and machine-level discovery of applications
already emitting OTel somewhere else.

## Component Blueprint Composition

The feature composes capabilities that already exist. It does not redefine
them; it extends their reach.

```component
name: OtlpReceiver
container: ClawMetry Dashboard
responsibilities:
	- Serving `POST /v1/traces`, `/v1/metrics`, `/v1/logs` on the `bp_otel` blueprint
	- Decoding protobuf, OTLP/JSON, and gzip request bodies into one request shape
	- Mapping spans into the in-memory metric cache and the DuckDB `spans` table
	- Reporting receiver state on `GET /api/otel-status`
```

`#OtlpReceiver` exists in code today (`routes/meta.py` plus the
`_process_otlp_*` mappers in `dashboard.py`) but has no component block in the
@Local Agent Observability Component Blueprint, so it is defined here and
should move up into that blueprint when someone with Software Factory write
access next syncs it. This feature adds a second bind address
(`#OtlpCompatListener`) and a second decoder (`#OtlpJsonDecoder`) to it, and
changes neither its mapping semantics nor its storage shape.

`#LocalStore` owns the `spans` table and the read surfaces `query_spans`,
`query_recent_spans`, `query_trace_rollup`, and `query_otlp_app_rollup`. The
daemon holds the writer lock; every other process reads through
`local_store_via_daemon`. This feature adds no new table. `query_trace_rollup`
already aggregates per `trace_id` and becomes the backbone of the spans-backed
trace list.

`#RuntimeSummaryBuilder` in `clawmetry/sync.py` composes `runtimeSummary` on
the daemon snapshot timer and calls `_merge_otlp_apps_into_summary`, which
turns each distinct foreign `agent_type` into a first-class runtime entry
carrying `otlp: true` and a humanized `display_name`. The frontend already
renders those under an "OpenLLMetry / OTLP apps" group and in the Agent
Inventory roster. Discovery output in this feature reuses that same seam
rather than inventing a parallel list.

`#TracingRoutes` in `routes/tracing.py` serves `/api/traces` and
`/api/trace/<id>` and is today entirely events-derived: it groups the `events`
table by `session_id` and reconstructs spans from event pairs. A foreign OTLP
application produces spans and no events, so it is currently absent from the
product's flagship trace view. This feature gives that component a second
source.

`#CloudSnapshotSync` bakes the encrypted snapshot the hosted dashboard renders.
Per the cloud-parity hard gate, any trace surface that a hosted trial user can
click must be served by a `cm-cloud-*` interceptor over a snapshot slice, or
must show an honest locked state. Discovery and the spans-backed trace list
both inherit that obligation.

## Feature-Specific Components

```component
name: OtlpCompatListener
container: ClawMetry Dashboard
responsibilities:
	- Binding the conventional OTLP/HTTP port (4318) in addition to the dashboard port
	- Serving only the `/v1/*` receiver routes on that port, never the dashboard UI or `/api/*`
	- Degrading to a logged warning when the port is already held by a local collector
	- Honoring `CLAWMETRY_OTLP_PORT` and `CLAWMETRY_OTLP_PORT_DISABLE`
```

```component
name: OtlpJsonDecoder
container: ClawMetry Dashboard
responsibilities:
	- Parsing OTLP/JSON `resourceSpans` payloads with the standard library alone
	- Producing the same span row shape `_process_otlp_traces` writes today
	- Serving as the default decode path when `opentelemetry-proto` is absent
	- Preserving the protobuf path unchanged when the `otel` extra is installed
```

```component
name: SpanTraceSource
container: ClawMetry Dashboard
responsibilities:
	- Listing traces from the `spans` table via `query_trace_rollup` for applications with no events
	- Building the waterfall and tree for a span-native trace from `parent_span_id`
	- Merging span-derived and event-derived traces into one `/api/traces` response without duplicates
	- Scoping every response by the active runtime filter (`agent_type` for OTLP applications)
```

```component
name: ClawmetryTracer
container: ClawMetry SDK (Python)
responsibilities:
	- Exposing `clawmetry.trace.init(app=...)` and a `@trace` / context-manager span API
	- Emitting OTLP/JSON over HTTP with no OpenTelemetry dependency
	- Setting `service.name` from `app` so the application self-identifies as its own runtime
	- Buffering and dropping silently when no ClawMetry is listening, never raising into the host application
```

```component
name: OtelEmitterDiscovery
container: ClawMetry Sync Daemon
responsibilities:
	- Probing for an existing OTLP collector on the conventional ports
	- Scanning same-user process environments for `OTEL_EXPORTER_OTLP_*` endpoints
	- Emitting a `detectedOtelApps` snapshot slice describing what was found and where it currently sends
	- Producing an actionable prompt ("send a copy here") rather than modifying any application's configuration
```

`#OtlpCompatListener` fronts `#OtlpReceiver`: it runs a second WSGI server in a
daemon thread over a Flask application that registers only `bp_otel`, so a span
arriving on 4318 lands in exactly the same handler, decoder, and store path as
one arriving on 8900. The split exists because the conventional port is the
difference between "set an environment variable we document" and "it already
worked," and because exposing the full dashboard on a second port would widen
the authentication surface for no gain.

`#OtlpJsonDecoder` is selected by `_otlp_decode` before it reaches protobuf. The
current decoder answers HTTP 501 for every payload when `opentelemetry-proto`
is missing, which is the default install, so the advertised receiver is off for
most users on first run. JSON is the encoding an SDK controls and the one the
standard library can parse, so the dependency-free path removes the extra from
the critical path while the protobuf path keeps serving collectors that only
speak binary.

`#SpanTraceSource` is consumed by `#TracingRoutes`, not by the frontend
directly. `/api/traces` asks it for span-backed rollups, merges them with the
event-derived list keyed by trace identity, and sorts the union by start time.
`/api/trace/<id>` tries events first and falls back to spans, so a native
OpenClaw session keeps its richer event reconstruction while a foreign
application still gets a real waterfall.

`#ClawmetryTracer` writes to `#OtlpCompatListener` over loopback. It carries no
OpenTelemetry dependency because the base install is deliberately Flask,
waitress, cryptography, and DuckDB, and an SDK that dragged
`opentelemetry-sdk` into a user's application would be a heavier ask than the
OpenLLMetry two-liner it competes with. Applications that already run
OpenTelemetry should use their existing exporter and skip the SDK entirely.

`#OtelEmitterDiscovery` publishes into the same `runtimeSummary` seam
`#RuntimeSummaryBuilder` owns, but in a distinct `detectedOtelApps` slice: a
detected application has not sent ClawMetry anything, so it must never be
counted as an observed runtime with zero cost. It is a prompt, not a row.

## System Contracts

### Key Contracts

Span identity is idempotent on `span_id`. Re-delivery of a batch, whether from
an SDK retry or a collector replay, upserts rather than duplicates, which is
already how `ingest_spans_batch` behaves and which the JSON path must preserve.

A foreign application's `agent_type` is derived only from resource
`service.name` through `_otlp_service_name_to_agent_type`, and can never
collide with a native runtime: the twelve session-prefix runtimes plus
`openclaw` and `nemoclaw` are excluded from the OTLP rollup. A native runtime
must never be re-bucketed as a foreign application, which
`tests/test_runtime_filter_no_leak.py` guards.

The trace list is a union, not a replacement. Enabling `#SpanTraceSource` must
not remove, reorder within its own timestamp, or alter any event-derived trace
that appears today, and a session carrying both events and OTel spans resolves
to exactly one trace entry.

Discovery is read-only. `#OtelEmitterDiscovery` never writes to another
application's configuration, environment, or files, and never reads process
environments belonging to another user.

The receiver stays closed to the network. Loopback is trusted; a non-loopback
caller needs the gateway token unless `CLAWMETRY_OTLP_ALLOW_UNAUTH` is set.
Binding a second port must not weaken that rule, and the compat listener binds
loopback by default.

### Integration Contracts

`POST /v1/traces` accepts `application/x-protobuf`, `application/json`, and
either under `Content-Encoding: gzip`, on both the dashboard port and 4318, and
answers `200 {}` on success and `400` on a malformed body. It answers `501`
only when a protobuf payload arrives without `opentelemetry-proto` installed;
a JSON payload never answers `501` after this feature lands.

`GET /api/otel-status` reports `available` (always true: OTLP/JSON traces and
logs need no extra), `protobuf` (whether `opentelemetry-proto` is installed,
which is what `available` alone used to mean), `jsonIngest` (the signals the
dependency-free decoder covers, currently `["traces", "logs"]`), plus the
existing `hasData`, `lastReceived`, `counts`, and `export*` fields.

The receiver's listening surface is configured by three environment variables.
`CLAWMETRY_OTLP_PORT` overrides the conventional port (`4318`; `0` binds an
ephemeral port, which the tests use). `CLAWMETRY_OTLP_HOST` overrides the bind
address, which defaults to `127.0.0.1` regardless of the dashboard's own
`--host`, so widening the ingest surface is always deliberate.
`CLAWMETRY_OTLP_PORT_DISABLE=1` stops the second listener entirely, leaving
`/v1/*` served on the dashboard port alone.

`GET /api/traces` returns `{available, traces[], total}` where each trace
carries `trace_id`, `title`, `start_ms`, `duration_ms`, `span_count`, `model`,
`total_tokens`, `total_cost_usd`, `error_count`, `status`, plus a new `source`
of `events` or `spans` so the frontend can label provenance.

The snapshot gains `detectedOtelApps[]` with `name`, `endpoint`, `evidence`
(one of `port_probe`, `process_env`), and `first_seen_ms`. Absence of the key
means discovery did not run, which the hosted dashboard renders as nothing
rather than as an empty state.

### Integration Boundaries

The SDK owns its wire format and its buffering; the receiver owns validation
and storage. The SDK never writes DuckDB, never reads `~/.clawmetry`, and never
assumes a daemon is running.

Free tier owns the OTLP path end to end. The Pro custom-runtime HTTP ingest
(`/api/v1/runs`, `routes/runtime_ingest.py`) stays a separate, entitlement-gated
door for structured run objects. The SDK targets the free OTLP door so adoption
is never paywalled; a paid tier may later add SDK features, never SDK access.

## Architecture Decision Records

### ADR-001: Bind 4318 rather than document a custom endpoint

Context: every OpenTelemetry SDK and collector defaults to
`http://localhost:4318`. ClawMetry serves its receiver on the dashboard port,
so today every user must discover and set `OTEL_EXPORTER_OTLP_ENDPOINT`, which
is the single largest drop-off in a zero-config product.

Decision: run a second WSGI listener on 4318 in a daemon thread, serving only
`bp_otel`, bound to loopback, disabled by one environment variable, and
silently skipped when the port is already taken.

Consequences: an already-instrumented application needs zero configuration. A
machine already running an OTel Collector keeps its collector, and ClawMetry
logs that it stepped aside rather than fighting for the port. The dashboard
port keeps serving `/v1/*` too, so nothing that works today breaks.

### ADR-002: Dependency-free OTLP/JSON instead of moving protobuf into the base install

Context: `opentelemetry-proto` plus `protobuf` sit behind the `otel` extra, so
a default `pip install clawmetry` answers `501` to every OTLP request. Moving
them into `install_requires` would fix it in one line but adds roughly five
megabytes and a notoriously version-sensitive dependency to every install,
against the minimal-dependency rule.

Decision: parse OTLP/JSON with the standard library, make that the default
path, and keep protobuf as an optional accelerator for collectors that only
emit binary. JSON traces and logs use the stdlib decoder **even when protobuf
is installed**, because the protobuf JSON parser is wrong for this payload:
protobuf maps `bytes` fields from base64, but OTLP/JSON overrides that for
`traceId` / `spanId` / `parentSpanId`, which are lowercase hex. Routing JSON
through `json_format.Parse` silently base64-decoded every id (measured live:
span id `3333333333333333` persisted as `df7df7df7df7df7df7df7df7`).

Consequences: the receiver works on a vanilla install, ids round-trip so they
can be correlated with the emitting app and with any other backend, and the SDK
can target a format ClawMetry can always read. The JSON parser becomes
ClawMetry-owned code that must track the OTLP schema, which is stable and
versioned, and which a fixture test pins.

### ADR-003: The Tracing tab reads spans as a second source, not as a replacement

Context: `routes/tracing.py` is events-first by design so tracing works with no
exporter at all, which is the right default for OpenClaw. The cost is that
span-only applications are invisible in the one view built to show traces.

Decision: add a spans-backed source and union it into the existing responses,
preferring the event reconstruction when a trace has both.

Consequences: no regression for native runtimes, real waterfalls for foreign
applications, and one merge point that must stay deduplicated. The alternative,
rewriting tracing to be spans-first, would require synthesizing spans for every
native runtime and was rejected as a much larger change with no user-visible
gain.

### ADR-004: The SDK carries no OpenTelemetry dependency

Context: the obvious SDK is a thin wrapper over `opentelemetry-sdk` plus
OpenLLMetry. That is also exactly what a developer can already do in two lines
without ClawMetry shipping anything.

Decision: ship a small SDK that speaks OTLP/JSON directly over HTTP, and
document the OpenLLMetry path as the recommended route for applications that
already run OpenTelemetry.

Consequences: the SDK is installable into a constrained application without
dependency negotiation, and it stays honest about not being a general tracing
framework. Applications needing full OpenTelemetry semantics are pointed at
OpenTelemetry, which the vendor-neutral positioning already promises.

### ADR-005: Discovery reports, it does not reconfigure

Context: the most useful version of "find agents on this machine" would patch
an application's environment to add ClawMetry as an exporter. That is a write
into software ClawMetry does not own, from a product whose first promise is
read-only.

Decision: detect and surface, with a copyable instruction the user applies
themselves.

Consequences: detection stays safe and cross-platform, at the cost of one
manual step. Process-environment reading is unavailable for other users'
processes on macOS without elevation, so discovery degrades to port probing
there and must say so rather than reporting nothing found.
