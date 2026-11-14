## Feature Summary

Node owners can search retained processes by name, PID or ClawMetry role and inspect the monitor's own CPU and resident memory. While the Node view is active, real process/resource measurements update about every two seconds independently of slow ingest. This implements [@Process search and ClawMetry resource visibility](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/29fd5189-7479-4259-8b97-2f74a5d4031b).

## Component Blueprint Composition

Compose the existing [@Node activity observation capability](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/2dffd534-2073-4af2-b943-d6dbed701ee1): `#NodeActivityCollector` samples process identity and counters, `#NodeActivityService` owns daemon cadence, `#NodeActivityStore` persists observations, and `#NodeActivityView` presents stored evidence. No host stats are read in HTTP handlers.

`#NodeActivityService` invokes `#NodeActivityCollector` through one independent worker using the actual daemon writer, started before cloud I/O and backfill. It records a bounded resource/process frame in `#NodeActivityStore` every two seconds during a viewer lease. Full listener, login, sensitive-file and event-history work remains at 30 seconds. The publisher holds at most one unsent frame and does not block sampling.

`#NodeActivityView` requests stored frames from the existing API and merges them with full-history data. Its renderInventory function delegates to renderProcesses and renderClawmetry. The former searches all retained rows before pagination; the latter shows recognized monitoring roles independently of the main search. Search and page state survive live refreshes and reset when the node changes.

For hosted viewing, the cloud Node interceptor reads existing owner-bound encrypted cache frames and decrypts them in the browser. Authenticated reads renew the owning node's viewing presence; existing normal/Assistant wake responses carry bounded node_activity_live_ttl to the independent delivery worker. That worker renews only the observation lease and executes no generic command.

## Feature-Specific Components

No additional runtime component is needed. This feature extends the existing collector, service, store and view components. The search input, navigation buttons, self-usage section, CPU bars and freshness badge are additions to the existing NodeActivityView template and stylesheet, not a new application or poller.

## System Contracts

### Key Contracts

- AC-OBS-NODE-SEARCH-001: renderProcesses filters all retained rows by case-insensitive name, PID and recognized ClawMetry label before sorting and slicing pages of 100. Search, clear and pagination use cached data without extra requests.
- AC-OBS-NODE-SEARCH-002: the collector samples its own PID before bounded enumeration and retains recognized monitoring processes ahead of the general cap. Exact launch-entry recognition yields only fixed role metadata; command lines remain transient and actor attribution is unchanged.
- CPU is computed from comparable PID/start-time-bound counter deltas. Zero differs from unavailable. The existing comparison-gap limit remains 120 seconds; initial sampling becomes measurable on the next healthy interval. RSS is per process and is never presented as an exact summed application total.
- AC-OBS-NODE-SEARCH-003: schedule uses one 2000ms active-view timer; load requests live=1 for lightweight frames and full history every 30 seconds. Hidden/off-tab changes abort requests and stop the timer. A maximum 40-second lease expires without further viewing; no other tab activates the fast sampler.
- Old collectors may fall back after five unavailable live responses to the existing ten/fifteen second snapshot cadence. New capabilities.live_metrics prevents an unsupported downgrade. Fresh, sampling, delayed and snapshot states remain explicit; older live frames cannot replace newer frames.
- Startup rejects read-only proxy stores and reacquires the writer after local query ownership is established. Shutdown prevents writes after a completed collection when stopping. Denied/missing sensor observations preserve explicit coverage limitations.

### Integration Contracts

GET /api/node-activity keeps its original full response. The live=1 query selects query_node_activity_live, which reads the persisted frame and renews ephemeral local viewing interest. The private daemon RPC method is allowlisted and daemon-token authenticated; mutation methods remain private to the writer.

The live frame contains schema_version, available, node, collected_at, summary, resource/process coverage, preferences and bounded processes, with live=true, refresh_seconds=2 and stale_after_seconds=8. It carries no command arguments, environment, file content or digest. The existing full nodeActivity encrypted snapshot remains compatible.

Cloud publication encrypts frames on the node with existing AES-GCM and posts through /ingest/cache under node_activity_live:owner:node with a 12-second TTL. Cloud cache reads verify exact caller owner and node membership before renewing presence. Presence has a 40-second maximum, includes no measurements and uses the existing cache backend. Normal and Assistant wake paths return remaining TTL; identity, epoch, stale-capability and generic-action boundaries remain intact. The browser verifies node identity after decryption. No new public HTTP endpoint, generic command execution or faster full-snapshot build is introduced.

### Verification and rollback

Collector/store/RPC/lifecycle tests cover identity reuse, inaccessible enumeration, blocked ingest, viewer expiry, startup ownership and shutdown. JS and responsive browser tests cover retained-row search, self visibility, stale/fallback states, escaped values, live ordering and request lifecycle. Cloud tests cover encryption, exact ownership, TTL expiry and absence of repeated snapshot reads. Actual local frames advanced at 2.01 and 2.046 seconds; release completion additionally requires the published wheel, deployed cloud frames and actual hosted UI. Rollback reinstalls the previous wheel and cloud revision; there is no schema migration.

## Architecture Decision Records

### ADR-001: Identify monitoring roles without publishing command lines

**Context:** ClawMetry runs under Python names and can be hidden by bounded inventory ordering.

**Decision:** Sample the current collector first and recognize exact supported launch entry points transiently. Persist fixed roles only and retain those rows within the existing cap.

**Consequences:** Users can locate the monitor without leaking invocation arguments or inventing actor identity. Inaccessible processes and unknown launch paths remain explicitly unrecognized.

### ADR-002: Independent measurements with active-view acceleration

**Context:** A 139-second ingest cycle invalidated CPU comparisons and made the dashboard static.

**Decision:** Replace ingest-loop-triggered collection with one daemon worker. Accelerate only process/resource frames during bounded viewing interest, retaining the expensive full cadence and existing CPU interval checks.

**Consequences:** Healthy observations produce measured CPU about every two seconds even during backfill. Idle cost stays bounded; CPU warm-up and denied counters remain honest rather than fabricated.

### ADR-003: Encrypted latest frames and existing wake hints

**Context:** Faster full snapshots are costly, and queued generic actions wait for the same ingest loop that delayed measurements.

**Decision:** Reuse the authenticated encrypted cache and independent existing wake channel for bounded viewing presence. Publish only the latest frame with short TTL and decrypt in the browser.

**Consequences:** Cloud gets live process measurements without plaintext data or an extra command poller. Older collectors keep snapshot behavior, leases expire off-tab, and network delays cannot stall measurement.
