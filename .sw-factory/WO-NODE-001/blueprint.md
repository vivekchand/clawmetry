## Feature Summary

Node activity explains observed resource use, process and listener changes, and selected sensitive configuration changes. It implements the [Node activity requirements](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/7619d6bd-85f0-4a34-be97-4e7710f64621) with daemon-owned collection and storage, evidence-based findings, persisted operator reviews, and a node-wide visual tab. Periodic observation does not establish complete execution history or prove an actor's intent.

## Component Blueprint Composition

The Local Observability Service remains the daemon and local query boundary. Governance Policy and Approval remains the authority for existing supported-session controls. Node findings have their own identity and are not inserted into session policy tables through invented sessions.

## Feature-Specific Components

```component
name: NodeActivityCollector
container: Local Observability Service
responsibilities:
	- Collects bounded portable host metadata in clawmetry/node_activity.py.
	- Uses psutil for resource, process, listener and available login observations.
	- Fingerprints a closed set of sensitive configuration paths without exporting contents.
	- States polling, namespace, permissions and truncation limits per source.
```

```component
name: NodeActivityStore
container: Local Observability Service
responsibilities:
	- Stores observations, safe current entities, durable changes, preferences and reviews in clawmetry/node_activity_store.py.
	- Preserves prior evidence when a source is incomplete.
	- Applies bounded history retention through the daemon writer.
```

```component
name: NodeActivityService
container: Local Observability Service
responsibilities:
	- Coordinates collection on a separate bounded daemon cadence in clawmetry/node_activity_service.py.
	- Reads current policy, persists the batch, and builds the encrypted snapshot slice.
	- Exposes validated daemon operations through routes/node_activity.py and routes/local_query.py.
```

```component
name: NodeActivityView
container: Dashboard browser
responsibilities:
	- Renders the Node activity tab from persisted evidence in templates/tabs/node-activity.html and static/js/node-activity.js.
	- Presents Observe, Govern and Guard views, change history, coverage and event replay.
	- Uses existing theme and typography through static/css/node-activity.css.
	- Stops polling and replay when the tab is inactive or hidden.
```

`#NodeActivityCollector` sends a source-qualified batch to `#NodeActivityStore` through `#NodeActivityService`. Collection runs even in local-only mode and never occurs inside Flask request handlers. Raw arguments, environment values and secret contents do not cross this boundary.

`#NodeActivityStore` supplies one bounded node-wide response to `#NodeActivityView` through `#NodeActivityService`. The response includes nullable measurements, safe entities, changes, reviews, source coverage and recorded times. Public changes exclude internal fingerprints and collection state.

`#NodeActivityService` adds `nodeActivity` to the existing encrypted system snapshot. The cloud client interceptor reads that slice through the shared snapshot cache and verifies the selected node. Hosted policy and review writes use the existing authenticated encrypted node relay or report an explicit unavailable result; they never pretend to persist in the cloud container.

## System Contracts

### Key Contracts

- The initial inventory is a baseline, not a trusted clean-state claim.
- Each source reports complete, partial, unavailable, disabled or unsupported coverage with observation time and a factual reason.
- Removals require a complete comparable scan of the same source and namespace. Permission failures and capped scans do not imply removals.
- Process identity contains a start token in addition to its PID. A process name is not an agent identity.
- A listener means a socket is bound. It does not establish external reachability or an outbound transfer.
- File fingerprints are keyed locally. Public payloads contain safe labels and changed metadata, never file content or fingerprints.
- Node findings and reviews use their own IDs. A review does not change original evidence or grant future machine access.
- Observation is enabled by default, can be disabled by the operator, and never installs privileged sensors or changes another process.
- Unknown activity has no arbitrary PID control. Existing Guard actions retain their own session resolver, capability check and actuator verification.
- Local reads use the daemon query proxy. The daemon owns all writes under its existing lock.
- Retention and response caps are visible. Polling can miss activity between observations.

### Integration Contracts

- `GET /api/node-activity` returns schema version, scope, node, collected time, stale limit, nullable summary, samples, processes, listeners, events, coverage, preferences and retention/truncation information.
- `POST /api/node-activity/preferences` validates only declared boolean collection/review preferences and records the daemon result.
- `POST /api/node-activity/reviews` validates an existing change ID and the declared review decision before a daemon write.
- The browser reads the same response shape from the local service or the selected hosted node's `nodeActivity` snapshot.
- Frontend polling uses one cached, deduplicated request only while the tab is visible and active. A generation or node mismatch discards the response.

## Architecture Decision Records

### ADR-NODE-001: Reuse a portable host library

Context: Complete native event capture requires different privileged sensors on Linux, macOS and Windows. A new collector must not silently replace existing security software.

Decision: Use maintained psutil APIs for bounded periodic metadata collection and explicit source coverage. Preserve an integration boundary for maintained event sensors in later work.

Consequences: The first release observes current state and comparable changes. It cannot capture every short-lived operation or attribute file reads from polling.

### ADR-NODE-002: Keep node findings distinct

Context: Existing Guard policies act on supported sessions. Many host changes have no session evidence.

Decision: Store node findings and human reviews independently. Reach existing Guard only for a real verified session.

Consequences: No fake sessions, arbitrary process termination or implied attacker attribution are introduced.

### ADR-NODE-003: Use the existing encrypted cloud path

Context: Cloud containers do not contain the node's filesystem or DuckDB.

Decision: Collect on the node, store in DuckDB, encrypt with the existing snapshot, and render from the shared browser snapshot cache.

Consequences: Node detail remains encrypted in hosted storage. Missing snapshots remain unavailable rather than becoming cloud-host measurements.
