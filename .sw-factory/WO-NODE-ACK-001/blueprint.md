## Feature Summary

This correctness addendum implements [@Node activity current rows and partial positive sightings](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/d33e1d0b-43c1-4d3f-8d0d-8de6628d0583). It fixes permanently capped inventories without treating incomplete observations as complete comparisons. It adds no OT integration, native execution sensor or process control.

## Component Blueprint Composition

This addendum extends the existing [@Node activity composition](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/72d9ec38-2671-4258-a5ad-ffe36c84b27c) and [@feature blueprint](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/30fa3bd8-d322-4b39-8674-6a86d73fb229). Their contracts for process identity, unknown attribution, private persistence, encrypted synchronization and complete-comparison gap handling remain in force. In particular, the existing ban on inferred removals or recovery from incomplete scans is unchanged.

`#NodeActivityCollector` continues to send a bounded source-qualified batch to `#NodeActivityStore`. No collection cap or process candidate budget increases. `#NodeActivityStore` prioritizes the current batch in the public inventory and separately tracks positive process sightings. `#NodeActivityView` presents the resulting row times, first-observed evidence and coverage limits using the existing stored API response.

## Feature-Specific Components

No new runtime component is introduced. The existing `NodeActivityStoreMixin` gains private durable process-sighting state that is independent from the complete-comparison `source_state`. Existing metadata helpers or a bounded private table remain within the same daemon-owned DuckDB writer boundary; no new persistence service or dependency is needed.

### Public inventory merge

For every partial entity source, deduplicate and place incoming rows first, stamp `observed_at` from the source scan and set `stale=false`. Append only prior rows not in the current batch, preserving their last `observed_at` and setting `stale=true`; legacy times remain null rather than being replaced with the current scan time. Apply that source's public row cap after the merge. Existing partial/unknown aggregate semantics remain unchanged.

### Private process-sighting ledger

Keep source identity, quiet initialization state, sticky `history_limited` state, and a bounded mapping from stable process identity to its last positive observation time. The identity includes the existing PID plus measured start identity and source identity. Update last-positive time for observed known identities. Prune records outside the event-retention window, normally 24 hours, and cap the ledger at 16,384 identities.

A first readable data-bearing scan is a quiet positive baseline, including migration from an install without the new ledger. Later partial scans can emit a first-observed event only for an identity that can be durably retained in the active history context. Persist the ledger atomically with observations and events so restart cannot replay an already recorded sighting. The complete source-comparison baseline remains separate and is discarded/re-established according to the existing gap contract.

An unavailable, disabled, unsupported or empty partial scan resets positive initialization so the next readable scan is quiet. For the same source identity, preserve all unexpired known dedup keys across this reset, restart and monitoring disable/re-enable. A genuinely changed source identity establishes a separate quiet current epoch. Partial/complete transitions do not erase unexpired identity knowledge.

### Saturation and safe reset

At capacity, retain all unexpired known identities and suppress positive events for unknown identities that cannot be retained. Incoming public rows still remain fresh and visible. Set `sighting_history_limited=true` and add an explicit coverage reason that positive-sighting history is incomplete.

This limit is sticky. Pruning, temporary free capacity, a same-source gap, restart or re-enable cannot clear it or cause an untracked saturated identity to masquerade as a new first sighting. Clear the limited state only through a quiet complete scan whose full comparison/dedup set fits the ledger, or a genuinely new source identity with its own quiet epoch. A quiet reset records no retrospective removals, recovery or first-observed events.

### Positive event contract

Use `kind=process_observed`, title `A process was first observed`, severity `info`, `finding=false` and unknown actor unless independently supported attribution exists under the unchanged parent contract. Detail and evidence must say first observed within retained history under partial collection, not lifetime first appearance or a proven process start. Preserve the positively measured process row as evidence; no absent prior row is proof that the process was absent. The existing event list, replay and encrypted snapshot can carry this informational event without inventing sessions or exposing arbitrary PID controls.

### Visible age and coverage

Use inventory headings that describe observations rather than promising that every row is current. Processes, listeners, selected settings and login evidence show their row observation time or an explicit unknown-time state when stale; a fresh current batch does not refresh the age of an old retained row. Existing coverage rendering must show the reported positive-history limit. No new browser clock or poller is needed.

## System Contracts

### Key Contracts

* Current positive rows take priority over stale history within every source's existing cap.
* First-observed sightings are positive evidence only. They do not assert actual starts, complete inventories, removals, recovery, trusted human identity or attacker intent.
* Same-source retained identity knowledge survives cap rotation, restart, gaps and re-enable; quiet initialization is a separate flag.
* Identity state is bounded by the retained-history window and a 16,384-record capacity. Saturation fails closed for new positive events and remains visible until a safe quiet reset.
* A partial scan never becomes a negative comparison. The next complete scan after a partial/gap re-establishes the complete baseline quietly under the existing contract.
* Internal identity ledgers and source-comparison state remain private DuckDB data. Public rows and events contain no command arguments, environment values, secret contents or reusable file fingerprints.
* This is a correction to stored evidence semantics. Existing daemon cadence, route read-only collection boundary, authentication and encrypted cloud path remain unchanged.

### Integration Contracts

* Public entity rows add `observed_at` and explicit `stale` state without changing the existing API endpoint.
* Process coverage adds `sighting_history_limited` plus a factual reason; complete/partial/unavailable state still describes collection coverage independently.
* The event stream accepts `process_observed` through existing generic evidence/replay rendering. Positive-sighting identities and event dedup are persisted within the writer transaction.
* No live host collection is added to Flask routes and no new cloud plaintext metadata or action endpoint is introduced.

### Validation

Use focused tests for a full stale public cap followed by a new partial incoming process, per-source row caps and legacy unknown row times; quiet initial/migrated partial baseline; later first positive sighting; cap rotation, restart and same-source gap/re-enable dedup; source change quiet baseline; PID reuse under the existing identity contract; sticky capacity exhaustion and safe complete rebaseline; unchanged no-removal/no-recovery semantics; and stored UI row-time/coverage-limit rendering. Verify a harmless real process is visible and produces an informational positive sighting on an already-capped monitored node without using a synthetic seed as release proof.

## Architecture Decision Records

### ADR-NODE-PART-001: Separate positive sightings from complete comparisons

Context: A host can remain over the process cap indefinitely. Waiting for complete scans discards useful positive evidence, while treating partial absence as a change creates false events.

Decision: Maintain a separate bounded durable positive-sighting ledger and incoming-first public inventory. Keep the existing complete-comparison state machine unchanged.

Consequences: Operators can see observed work on capped hosts. Events explicitly describe retained-history sightings, while negative conclusions still require complete comparable evidence.

### ADR-NODE-PART-002: Keep incomplete history explicit at capacity

Context: Evicting an unexpired dedup key to admit a new one can replay an old process as a first sighting during cap rotation or restart.

Decision: Preserve known identities and suppress untrackable positive events. Retain a sticky history-limit indication until a safe quiet complete rebaseline or a genuinely new source identity.

Consequences: The system may omit positive events while history is limited. It states this gap rather than fabricate novelty or expand storage without a bound.

## Merged Code References

Implementation merged through [PR 6419](https://github.com/vivekchand/clawmetry/pull/6419) as [commit 1b5861720024](https://github.com/vivekchand/clawmetry/commit/1b586172002466aa6f992f9131950e1f08e188cd). These links resolve to the merged main implementation; line anchors were checked against that merge commit. This section records implementation traceability only. Release publication and hosted verification for this correction remain pending; merge and passing CI do not establish either result. The contracts and architecture decisions above remain unchanged.

| Concern | Merged main reference |
| --- | --- |
| Incoming-first inventory and per-row age | [Current-first public projection](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/node_activity_store.py#L36) |
| Qualified partial positive and bounded durable identity state | [First-observed event](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/node_activity_store.py#L47); [Readable-source boundary](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/node_activity_store.py#L62); [Private sightings and sticky limit](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/node_activity_store.py#L67) |
| Atomic writer integration | [Persisted observation transaction](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/node_activity_store.py#L193) |
| Inventory, positive-event and gap regressions | [Each-source cap priority](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity.py#L377); [Qualified private sightings](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity.py#L403); [Restart, gap and re-enable dedup](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity.py#L425) |
| Saturation and actual disabled-collector boundary | [Sticky saturation and quiet reset](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity.py#L456); [Real disabled-batch regression](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity.py#L577) |
| Visible row time and incomplete history | [Inventory row ages](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/static/js/node-activity.js#L131); [Independent coverage-limit presentation](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/static/js/node-activity.js#L139); [Observed inventory headings](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/templates/tabs/node-activity.html#L16) |
| Actor map correction | [Actor slot without a connection and qualified map caption](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/templates/tabs/node-activity.html#L14); [Invisible actor gap](https://github.com/vivekchand/clawmetry/blob/main/clawmetry/static/css/node-activity.css#L42) |
| Executed UI evidence | [Fresh, stale, legacy and limited-history render assertions](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity_js.js#L185); [Rendered unknown, Human and Agent map guard](https://github.com/vivekchand/clawmetry/blob/main/tests/test_node_activity_browser.py#L78) |

## Hosted Action Acknowledgement Ownership Addendum

**Status: approved minimal design; implementation, release and hosted verification pending.** This section addresses REQ-GOV-NODE-ACK-001 in the linked correctness requirement. The prior merged-main references above describe the partial-observation correction; they are not evidence that this acknowledgement correction has shipped.

### Observed failure and required ownership

A single hosted Govern save arrived through both durable PostgreSQL delivery and the fast relay approximately 0.66 seconds apart. The original delivery claimed the nonce and applied the requested state. A later duplicate returned a failure and posted it under the same action acknowledgement key, replacing the original result. The browser correctly required confirmation and reported the save as unconfirmed; this design changes the duplicate execution/result path, not that browser standard.

Only the execution that originally claims a nonce owns its action result. An already-claimed delivery must stop without mutation and without publishing a replacement acknowledgement, including a duplicate-failure or expiry-failure acknowledgement. Duplicate recognition must take precedence over an expired-envelope failure while the existing retained claim/cache still provides valid duplicate evidence. The original claimant's success or failure result remains stable against later duplicate delivery.

### Minimal integration and failure boundaries

Reuse the current bounded nonce claim tracking, existing action-result cache and encrypted acknowledgement transport. Preserve the 512-nonce bound and existing TTL/cache retention; add no receipt table, service or unbounded history. Perform duplicate classification within the existing claim ownership boundary before any duplicate path can manufacture a posted error result. Retain ordinary validation and expiry rejection for a genuinely unclaimed action. No secrets, decrypted action payloads or new plaintext cloud metadata are introduced.

An original claimant that crashes, fails application or cannot publish a confirmed persisted result leaves the browser unconfirmed. A duplicate is not an automatic recovery executor and cannot publish a substitute result. The operator must refresh/check the node and issue a fresh request when needed; the system must not silently retry the claimed action or claim that aborting confirmation undid it. This is bounded within-retention duplicate suppression and result ownership, not perpetual exactly-once execution or a new durable receipt guarantee.

### Focused validation

Exercise one nonce delivered through both relay paths and prove one mutation plus one original-owner result. Deliver further duplicates after a confirmed original success and after an original failure; prove no mutation and no replacement acknowledgement in either case. Deliver an expired duplicate while its claim/cache is valid and prove the cached original result is unchanged. Simulate an original crash/apply failure/result-publication failure and prove that duplicate delivery cannot retry, manufacture confirmation or replace the original result. Keep the existing nonce bound and retention tests. Harmless integration verification must distinguish a confirmed persisted result from pending/unconfirmed delivery; no live completion is claimed by this design record.

### ADR-NODE-PART-003: Original nonce claimant owns acknowledgement

Context: Two legitimate transport paths can deliver the same hosted action. Suppressing a second mutation is insufficient if the duplicate can overwrite the action's cached result and turn an applied save into an unconfirmed one.

Decision: Keep the original nonce claimant as the sole result owner. Suppress already-claimed duplicates before expiry/error publication, within the existing bounded claim/cache retention. Do not introduce durable receipts or automatic replay.

Consequences: Duplicate delivery cannot replace a valid original result. A failed or crashed original attempt can remain unconfirmed and needs a fresh operator request; the existing UI must continue to report that uncertainty honestly. The original process-observation contracts and both earlier architecture decisions are unchanged.
