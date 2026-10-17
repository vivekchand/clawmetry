# Feature blueprint: Shared free Physical AI evidence

## Feature Summary

Compose the public robotics journal, existing daemon-owned DuckDB, read-only query proxy and incident delivery for requirements.md. Jumper is a built-in adapter; Mizu imports it.

## Component Blueprint Composition

No external blueprint dependencies are declared. Existing code contracts were read in journal.py, asimov/store.py, daemon.py, local_store.py, query_contract.py, sync.py, incident_alerts.py and routes/asimov.py. Those concrete components are reused rather than copied.

## Feature-Specific Components

```component
name: JumperObserver
container: Robot application
responsibilities:
	- Normalize named SI telemetry without loading a robot SDK
	- Publish bounded robotics.v1 evidence to JournalWriter
	- Record TaskGate decisions and DeskMonitor episodes without actuating a robot
```

```component
name: PhysicalAiProjection
container: Sync daemon
responsibilities:
	- Ingest known journal sources using the existing writer and transaction
	- Expose generic runs, events and bounded encrypted snapshots
	- Dispatch sanitized incidents after commit and lock release
```

```component
name: PhysicalAiView
container: Dashboard, Hosted browser
responsibilities:
	- Query persisted evidence through the read-only daemon proxy or decrypted cloud provider
	- Render measurements, decisions, incidents and missing-state explanations
	- Poll only while visible and preserve optional advanced paid workbench access
```

`#JumperObserver` emits robotics.v1 records to `#PhysicalAiProjection` through the existing asynchronous JournalWriter. `#PhysicalAiProjection` stores observations and events before notification dispatch; the Flask request path never opens a journal or owns a writer. `#PhysicalAiView` queries the same projection locally, or reads the bounded encrypted snapshot and authenticated encrypted history relay in cloud.

## System Contracts

### Key Contracts
Known sources are asimov_sdk, asimov_recording, jumper_native, jumper_app and jumper_recording. Legacy Asimov methods filter the first two. Canonical physical_ai_runs/events queries are E2E trace scoped; malformed cursors reject before store access. Journals are bounded, queue loss is explicit, repeated ingestion does not repeat alerts. Named joints never assume DDS/policy array ordering. No MuJoCo, NumPy, ONNX or Pro dependency enters the observer package.

The daemon persists a source-support ledger beside journal cursors. A missing or changed canonical source-registry token resets each affected cursor once, under the existing per-file and per-pass limits. Evidence, cursor and support marker commit together; immutable event identities suppress duplicate observations and notifications during replay. The ledger remembers rejected source classification so unchanged unsupported files, including appended bodies, remain cheap to skip. Inode replacement or truncation requires classification again. Existing five-column cursor rows and Asimov projections remain compatible.

### Integration Contracts
Observation fields are explicit joints/base, source time, optional collision/table bounds and clearance. Command requests, guard decisions, controller receipts and guard incidents are separate records. Finding notifications accept fixed known kinds and never include raw observation or source content. Source clock is distinct from receipt clock.

The `/api/extensions` response exposes one primary Physical AI navigation entry. A valid installed workbench declared by the entitled plugin retains its original destination; absent a declaration, `/physical-ai` is the built-in fallback. The optional `physical_ai_advanced` array remains backward-compatible diagnostic metadata for validated installed workbenches. A plain local `/physical-ai` visit redirects to the installed default, while specific `run` or `hardware` history links remain on the built-in page. User-facing links name the workbench explicitly and do not duplicate the Physical AI switch as "More installed tools".

The additive `physical_ai_hardware` list supplies `{id, label, href}` for supported recorded-source destinations from `clawmetry.physical_ai.catalog`. It declares support, not discovery of a live device. The built-in template uses that same catalog for its Hardware selector; absent matching loaded evidence it shows an empty filtered history, never another hardware family. Pagination, cancellation and source/receipt separation remain unchanged. The template applies existing dark dashboard tokens before paint.

`ui.snapshot` is an optional local plugin metadata hook. It declares entitled workbench navigation without requiring a Flask app in the daemon. The sync daemon validates that declaration and carries the resulting `ui.navigation` plus `ui.physical_ai_hardware` in the existing encrypted system snapshot. Missing/older/failed hooks retain the built-in fallback. Hosted browsers consume only the owning node's decrypted declarations and the cloud's real route capabilities; installed server packages alone are not evidence of node entitlement. No new poller or plaintext telemetry path is introduced.

### Integration Boundaries
Robot host owns physics and command transport. Observer is read-only; generic task gate defaults no qualified actions. Only an explicitly enabled simulator host forwards an allowed request. Hardware actuation stays unavailable. Shared daemon owns DuckDB, encryption, notifications and query proxy. Browser never gains motor control.

## Architecture Decision Records

### ADR-001: Built-in OSS adapter
**Context:** User explicitly rejected a standalone observer plugin. **Decision:** Ship Jumper in the normal main wheel, preserving existing paid-adapter boundaries. **Consequences:** Mizu contains scenes/skills/film only and imports the shared API.

### ADR-002: Extend public journal projection
**Context:** Existing free Asimov collector already owns discovery and persistence. **Decision:** Add known sources and generic filtered queries, retaining legacy methods unchanged. **Consequences:** No second database or poller and no Pro implementation copy.

### ADR-003: Honest physical outcomes
**Context:** Controller approval or damping cannot prove safety. **Decision:** Store separate typed evidence, unknown outcomes and explicit simulation provenance. **Consequences:** Missing bridge/state is visible, and alert delivery follows existing preferences.


### ADR-004: Preserve the established workbench
**Context:** The user rejected the light fallback page replacing the existing dark robot workbench and losing Hardware navigation. **Decision:** Retain valid installed workbench defaults, apply existing dark tokens to the free fallback, and expose declared hardware support through shared metadata. Extend the private workbench's existing armless source renderer for Jumper in its own repository. **Consequences:** One ordinary adapter installation remains sufficient; paid implementations and controls retain their existing boundaries, and no new look replaces the user's established workbench.
