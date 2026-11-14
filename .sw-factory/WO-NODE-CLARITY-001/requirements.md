## Node Evidence Clarity Follow-up: Approved Correctness Addition

Status: approved focused correctness and clarity addition; implementation and verification pending. Existing 12 criteria and prior delivery evidence remain unchanged. This addition addresses observed-count ambiguity, unmeasured process CPU, inaccessible macOS listeners and an event diagram whose generic categories do not explain the selected evidence. It adds no native execution sensor, process controls, privilege escalation or external/OT integration.

### REQ-OBS-NODE-CLARITY-001: Observed counts and exact totals

As an operator, I want visible observation counts to be distinct from whole-node totals so that a capped inventory remains useful without implying completeness.

* AC-OBS-NODE-CLARITY-001.1: When process or listener observations are available, the view shall display their positively observed count separately from any exact total, and shall state when the exact total is unknown because coverage is partial or bounded.
* AC-OBS-NODE-CLARITY-001.2: When a source is empty, unavailable or stale, the view shall distinguish a measured complete zero, zero accessible observations with incomplete coverage, unavailable collection and retained stale rows without presenting any of them as the same current zero.

### REQ-OBS-NODE-CLARITY-002: Measured process CPU intervals

As an operator, I want process CPU to describe a measured interval so that unknown or discontinuous measurements do not appear as idle usage.

* AC-OBS-NODE-CLARITY-002.1: When two comparable cumulative CPU observations exist for the same measured PID and process-start identity, the system shall report CPU usage from their actual elapsed interval with its CPU-capacity convention and measurement interval available to the view.
* AC-OBS-NODE-CLARITY-002.2: When a process CPU baseline is absent or invalid after first observation, PID reuse, daemon restart, a collection gap or unreadable counters, the system shall report that interval unavailable with an explanation rather than inventing a rate or reporting zero.

### REQ-OBS-NODE-CLARITY-003: Permitted macOS listener observations

As a macOS operator, I want accessible listener evidence when the primary API is denied so that ordinary account permissions do not hide all observable ports.

* AC-OBS-NODE-CLARITY-003.1: When primary macOS listener collection is permission denied or unsupported and a documented permitted fallback is available, the collector shall obtain only accessible TCP listener observations within declared time, output and row bounds, without privilege escalation, and shall report the method and incomplete scope.
* AC-OBS-NODE-CLARITY-003.2: When fallback observations are malformed, truncated, interrupted or change collection method, the system shall preserve safe stable listener identities and partial/gap semantics without inferring removals, recovery or complete inventory from missing rows.

### REQ-OBS-NODE-CLARITY-004: Plain recorded-event explanation

As an operator, I want the selected event explained in ordinary language so that I can understand the observation without interpreting an unevidenced category diagram.

* AC-OBS-NODE-CLARITY-004.1: When an event is selected or replayed, the primary story shall explain what was observed, when and on which process or resource, state attribution only when supported, and expose relevant uncertainty without drawing unsupported actor relationships.
* AC-OBS-NODE-CLARITY-004.2: When technical evidence is available, the view shall keep before/after and source details accessible progressively without requiring those details to understand the primary event story or replacing the original recorded evidence.

### REQ-OBS-NODE-CLARITY-005: Useful empty-source explanation

As an operator, I want the reason for missing observations where I encounter them so that an empty list does not imply that nothing is running or listening.

* AC-OBS-NODE-CLARITY-005.1: When an Observe inventory has no current observations or a source is disabled, unsupported or unavailable, the view shall show the source-specific collection reason and a working link to its coverage explanation.

### REQ-OBS-NODE-CLARITY-006: Actual evidence and compatible delivery

As an operator, I want the actual collector and encrypted hosted path validated so that a convincing component demo cannot substitute for working node evidence.

* AC-OBS-NODE-CLARITY-006.1: When this follow-up is verified for delivery, an owned harmless live process and TCP listener shall be observed through the actual collector and DuckDB, with a measured process CPU interval and the same evidence verified in local and encrypted hosted views.
* AC-OBS-NODE-CLARITY-006.2: When an older stored or hosted snapshot lacks the new count or CPU metadata, the view shall continue to render its available evidence with honest measurement and coverage limits rather than fail, invent a CPU rate or infer a complete total.
