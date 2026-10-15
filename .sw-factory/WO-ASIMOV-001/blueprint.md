## Feature Summary

Implements [Asimov 1 observation requirements](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/a508a5c5-8821-4964-8930-3561b7d02f2b), REQ-ASIMOV-001 through REQ-ASIMOV-006. Developers inspect free local evidence from explicit Observe connections, explicit application tracing and official SDK recordings. Feedback remains distinct from intent and unknown outcomes. Hardware qualification is pending.

## Component Blueprint Composition

Reuse the robotics.v1 journal, existing LocalStore writer, authenticated query proxy and encrypted system snapshot. Merged Pro #338 and cloud #2623 define inspected compatibility contracts. RP1 #340 owns the shared humanoid viewer; this feature does not depend on that pending viewer.

Automatic ingestion tails already-written journals. It never opens an SDK robot connection or installs tracing. Live collection starts only through the explicit observe CLI; application tracing starts only through observe(robot). The local view and hosted browser consume persisted projections.

## Feature-Specific Components

```component
name: AsimovObserver
container: Optional collector process
responsibilities:
	- Execute observer.observe_live only after explicit CLI observe
	- Require Observe authority and data-publish-disabled LiveKit grants
	- Subscribe to state without media or motion commands
```

```component
name: AsimovSdkTracer
container: Developer application
responsibilities:
	- Install sdk.SdkObserver only through an explicit observation context
	- Preserve original SDK returns and ordinary exception identity
	- Propagate KeyboardInterrupt and SystemExit without failure recording
```

```component
name: AsimovRecordingImporter
container: ClawMetry CLI
responsibilities:
	- Parse official recordings through recording.import_recording
	- Bound memory and preserve source clocks and incomplete status
```

```component
name: AsimovNormalizer
container: Optional collector process, Developer application, CLI
responsibilities:
	- Map SDK state through sdk.normalize_state with all 25 joint units
	- Preserve nulls, clock provenance and unknown outcomes
```

```component
name: AsimovJournalWriter
container: Optional collector process, Developer application, CLI
responsibilities:
	- Use journal.JournalWriter for bounded nonblocking evidence queues
	- Bound journal storage and report dropped or incomplete evidence
```

```component
name: AsimovLocalStore
container: Existing sync daemon
responsibilities:
	- Tail journals on the existing daemon writer connection
	- Commit immutable events and cursor progress together
	- Provide persisted runs, events and bounded snapshot projections
```

```component
name: AsimovReadView
container: Local web application, Hosted browser
responsibilities:
	- Consume authenticated persisted projections in routes/asimov.py and asimov.js
	- Present measured joints, source clocks and command evidence
	- Explain stale, missing, incomplete and unqualified evidence
```

AsimovObserver, AsimovSdkTracer and AsimovRecordingImporter supply normalized evidence to AsimovJournalWriter. AsimovLocalStore ingests the resulting files inside the existing writer process. No SDK, network or database work occurs in journal producer callbacks.

AsimovReadView is a consumer of persisted projections, not an intermediary that serializes database records or encrypts snapshots. AsimovLocalStore.snapshot intentionally builds the cloud projection directly from DuckDB. sync_system_snapshot adds payload.asimov before the existing shared encryption layer encrypts the envelope. The hosted browser decrypts and renders that projection; the cloud server cannot inspect it.

## System Contracts

### Key Contracts

* Schema clawmetry.robotics.v1; UUID32 run identity; positive sequence; nanoseconds as decimal strings below 2\*\*63; hardware or simulation environment; integer dropped_total; finite JSON; maximum event 64 KiB.
* Joint position radians, velocity radians/second, current amps and temperature Celsius. Missing values remain null. Do not infer torque, odometry, body positions, command acceptance or physical success.
* Only explicit live operations need Python 3.12 and optional Menlo SDK 0.1.0. observer.require_sdk is a function: its checks and SDK imports execute when called by observe_live or data_only_client_class, never at module import. Core startup, ingestion, recording import, status and web reads do not invoke it.
* Observe collection rejects Control or unknown roles, requires data-publish-disabled grants, disables media subscriptions and calls no motion or mode method.
* Command tracing is explicit. Ordinary Exception failures are recorded through bounded nonblocking queues and re-raised unchanged. Process-control exceptions propagate without command-failure instrumentation.
* Queues, journal files, ingest batches and snapshots have limits. Loss, malformed rows and recorder errors remain visible.
* Cursor and immutable event writes share a transaction. Equal replay deduplicates; conflicting payloads fail visibly.

### Runtime Entry Points and Thread Lifecycle

run_daemon calls clawmetry.asimov.daemon.start automatically only to tail already-existing local journals using its existing LocalStore writer handle. This allows an explicit recording import to appear without a second ingest command. It is automatic file ingestion, not automatic live SDK collection or tracing; it imports no Menlo SDK, resolves no credentials and connects to no robot.

start skips duplicate startup only when the existing worker is alive. A terminated thread reports is_alive false and a subsequent start replaces it. Recoverable ingest exceptions are caught, logged and retried on the same worker after its bounded wait. Shutdown stops ingestion before writer teardown. No automatic robot reconnection or hardware qualification is implied.

### Writer Ownership and Query Contracts

`routes.asimov._call` obtains `local_store.get_store(read_only=True)`. This expresses read intent without opening a second database: inside the writer process it returns the existing writer singleton; a separate dashboard process receives the existing `_ProxyStore`. `query_asimov_runs` and `query_asimov_events` forward over the private bearer-authenticated allowlisted daemon RPC, where the writer-owned store executes the query. Ingestion uses its writer lock. Request handlers never scan journals, recordings or status files.

Explicit CLI import, status and inspect commands may read local files outside HTTP handlers. They create no cloud plaintext path. Snapshot generation reads the daemon writer directly and does not call the view or scan journals.

### Integration Contracts

* run.started records source_kind asimov_sdk or asimov_recording, observation_only, scope and validation provenance. Observations carry the joint names and measured values.

* observation kind matches merged Pro feedback projection. Structured joints/base/battery retain separate source and receipt clocks.
* Commands retain requested, returned, failed and sent distinctions. Outcome remains unknown.
* /asimov and /api/asimov/runs remain free with enforced licensing; normal gateway and private daemon bearer authentication still apply.
* payload.asimov carries bounded summaries and recent non-observation events. trace_window declares scope, retained count and truncation. Full local history uses bounded pagination.
* /cloud/node/\<id>/asimov requires node authorization. Browser decryption retains the node secret locally, shares the snapshot cache, pauses hidden polling and rejects old-context asynchronous responses.
* Freshness derives from stored observation receipt time. Frozen snapshots cannot remain live. Provider cancellation releases the renderer without cancelling a shared fetch.

### Integration Boundaries

OSS owns the free connector and local view. Pro retains advanced robotics and existing handlers. Cloud owns hosted authorization and encrypted transport. RP1 owns humanoid.js and its renderer. No Asimov control or media path is added. Sponsorship and hardware qualification remain separate.

## Architecture Decision Records

### ADR-001: Optional Menlo dependencies

**Context:** SDK Python and media requirements exceed core. **Decision:** Lazy imports only inside explicit live operations with actionable errors. **Consequences:** Core installation and module imports retain the declared Python floor.

### ADR-002: Free evidence without Pro

**Context:** Basic local observation must be free. **Decision:** Emit the compatible journal and use a narrow free ingest/read path without replacing extensions. **Consequences:** Verify Pro absence, enforced licensing, real Pro parser compatibility and authenticated writer RPC.

### ADR-003: Honest hardware qualification

**Context:** SDK fixtures cannot prove physical behavior. **Decision:** Mark hardware qualification pending and preserve provenance and unknown outcomes. **Consequences:** Experimental SDK/recording support can ship while physical qualification remains open.
