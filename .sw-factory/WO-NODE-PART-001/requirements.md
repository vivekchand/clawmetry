## Overview

**Status: approved correctness follow-up; implementation awaits the linked design record.** On a monitored machine whose process count permanently exceeds the collection cap, the Node activity view can omit newly observed processes because stale rows occupy the public cap first. Its history can also remain empty because a complete process comparison is never available. Operators need current positive evidence without being told that a partial inventory proves a process start, a removal, a recovery or an attack. This follow-up extends the [@Node activity requirement](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/7619d6bd-85f0-4a34-be97-4e7710f64621). Existing safeguards for unknown attribution, process identity, source gaps, local storage and encrypted synchronization remain in force.

The change prioritizes incoming observations within existing public caps and adds bounded durable first-observed process sightings during partial coverage. It does not raise collection limits, claim a complete inventory, add native execution capture, introduce process controls or implement the separate external/OT research proposal. Alternatives rejected are unbounded inventories, silently treating partial scans as complete, discarding fresh rows behind stale data, and suppressing every positive sighting until a full scan becomes possible. Accepted limits remain visible: periodic collection misses activity, history expires, and positive-sighting history can become incomplete when its deduplication budget is exhausted.

## Terminology

* Incoming row: an entity positively observed in the current source scan.
* Stale row: prior evidence not positively observed in the current scan; it is not evidence that the entity ended.
* First-observed sighting: a positive process observation within retained history, not proof of its actual start or first existence.
* Source epoch: a source identity and its quiet initialization state. Restart alone does not create a new identity.
* Limited sighting history: an explicit state in which the bounded identity ledger cannot safely retain further unknown identities.

## Requirements

### REQ-OBS-NODE-PART-001: Fresh bounded inventory

As an operator, I want the newest measured rows to be visible so that a permanently capped inventory can still explain current activity.

* AC-OBS-NODE-PART-001.1: When a source scan is partial, the system shall place unique incoming rows before retained stale rows and apply that source's public cap after the merge.
* AC-OBS-NODE-PART-001.2: When a row is positively observed, the system shall mark it current with that observation time; retained stale rows shall keep their prior observation time or an explicit unknown time for legacy evidence.

### REQ-OBS-NODE-PART-002: Honest positive sightings

As an investigator, I want newly retained process sightings during partial coverage so that useful positive evidence does not depend on a complete inventory.

* AC-OBS-NODE-PART-002.1: When a source first supplies readable process rows, including initialization after installation, migration, a source change or a collection gap, the system shall establish a quiet positive-sighting baseline.
* AC-OBS-NODE-PART-002.2: When a later partial scan observes a retainable process identity not known in the current retained-history context, the system shall record an informational first-observed sighting that explicitly does not prove an actual start, a complete inventory or malicious intent.
* AC-OBS-NODE-PART-002.3: When an unexpired process identity is observed again after cap rotation, daemon restart, a same-source gap, disable/re-enable or transition between partial and complete coverage, the system shall suppress duplicate first-observed sightings while preserving the quiet-initialization rule.

### REQ-OBS-NODE-PART-003: Bounded, explicit sighting history

As an operator, I want positive-sighting history to remain bounded and honest so that an exhausted budget cannot create misleading repeated events.

* AC-OBS-NODE-PART-003.1: When the identity budget cannot retain an unknown process identity, the system shall preserve unexpired known identities, suppress the untrackable positive event and expose limited sighting history until a safe quiet rebaseline.
* AC-OBS-NODE-PART-003.2: When retained sighting history expires, the system shall apply its declared retention window and identity bound without representing a later retained-window observation as the process's lifetime first appearance.

### REQ-OBS-NODE-PART-004: Visible observation age

As an operator, I want row age and coverage limits to remain visible so that a mixed inventory cannot look like a wholly current or complete view.

* AC-OBS-NODE-PART-004.1: When the view contains current and stale rows or limited sighting history, the system shall show per-row observation age or unknown time, describe the mixed-age inventory honestly and display the reported sighting-history limit.
