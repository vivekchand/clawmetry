## Overview

An operator can see agent transcripts but cannot use them to explain changes made by other processes on the same machine. Resource totals also cannot explain a new listener or a change to remote access. The operator needs one node-wide view of observed processes, resources, listeners, selected sensitive configuration changes, and the evidence available to explain them. This request follows the operator's review of the Albert Heijn incident and approval of an interactive Node activity concept.

This feature adds a Node activity tab with Observe, Govern, Guard, change history, coverage, and event replay. Observation is the default. The first release uses periodic host observations. It shall not claim complete execution capture, identify an unknown process as AI or an attacker, or claim that a remote user is authorised from an account name. Governance records monitoring preferences and human review decisions. Guard presents findings and reaches existing session controls only when a supported session is independently identified.

Alternatives rejected: transcript-only checks miss unrelated activity; snapshot-only claims of complete execution omit short-lived processes; a new kernel driver would duplicate maintained sensor projects and require a separate privileged deployment. Periodic collection uses the maintained psutil platform library. Optional external sensor integrations and kernel-level prevention are separate work. Risks include collection overhead, sensitive host metadata, incomplete permissions, false change reports, and baseline poisoning. Collection is bounded and can be disabled. Missing evidence remains explicit. Cloud copies remain encrypted. Disabling monitoring stops new collection and does not change processes or erase history.

## Terminology

- Node: the host or container namespace visible to the daemon.
- Observation: a measurement from a named source at a recorded time.
- Change: a difference between comparable observations, not proof of the action that caused it.
- Finding: a change that matches a declared review rule, not proof of compromise.
- Review: an operator record that a specific finding is expected or requires investigation.

## Requirements

### REQ-OBS-NODE-001: Node observations

As an operator, I want to see current node activity so that I can explain resource use and services.

- AC-OBS-NODE-001.1: When the collector can read a source, the system shall store its observation time, coverage state, and available resource, process, listener, or login measurements.
- AC-OBS-NODE-001.2: When a value cannot be measured, the system shall retain an unknown value and explain its coverage limit.
- AC-OBS-NODE-001.3: When monitoring is disabled, the system shall stop new collection and retain the prior history with a disabled state.

### REQ-OBS-NODE-002: Comparable change history

As an operator, I want to see changes and their evidence so that I can investigate unexpected activity.

- AC-OBS-NODE-002.1: When a scope is observed for the first time, the system shall establish an initial baseline without reporting existing entities as newly added threats.
- AC-OBS-NODE-002.2: When a later complete comparable observation changes an entity, the system shall record a stable change with its before and after evidence.
- AC-OBS-NODE-002.3: When a source is incomplete or unavailable, the system shall preserve prior evidence as stale and shall not infer entity removal or recovery from the gap.
- AC-OBS-NODE-002.4: When a process ID is reused with a different start identity, the system shall keep the process identities distinct.

### REQ-GOV-NODE-003: Attribution and privacy

As an operator, I want evidence-based attribution without disclosure of secret contents.

- AC-GOV-NODE-003.1: When no supported session is independently matched, the system shall identify the activity as unattributed and shall not invent a human, agent, or attacker identity.
- AC-GOV-NODE-003.2: When a configuration fingerprint is collected, the system shall not copy file contents, command arguments, environment values, or reusable secret hashes into the public node payload.
- AC-GOV-NODE-003.3: When node detail is sent to hosted storage, the system shall include it only in the encrypted node snapshot.

### REQ-GOV-NODE-004: Operator governance

As an operator, I want to select review rules and record decisions so that ordinary work does not become an unexplained alarm.

- AC-GOV-NODE-004.1: When the operator changes a supported monitoring preference, the daemon shall validate and persist the preference and record the change for review.
- AC-GOV-NODE-004.2: When the operator marks a recorded change expected or requiring investigation, the system shall retain the original evidence and record the review separately.
- AC-GOV-NODE-004.3: When a preference or review write is unavailable, the system shall report that it was not saved and shall not show success.

### REQ-GOV-NODE-005: Node Guard

As an operator, I want important node changes grouped for review so that I can respond without treating every new process as an attack.

- AC-GOV-NODE-005.1: When enabled review rules match a sensitive configuration change or a new non-loopback listener, the system shall present a finding with the matching evidence and its uncertainty.
- AC-GOV-NODE-005.2: When an activity has no independently matched supported session, the feature shall not expose arbitrary process termination as a Guard action.
- AC-GOV-NODE-005.3: When a node is observed through a container or restricted account, the system shall state that scope and shall not describe it as unrestricted host coverage.

### REQ-OBS-NODE-006: Local and hosted views

As an operator, I want the same node evidence locally and in the hosted dashboard.

- AC-OBS-NODE-006.1: When the tab loads locally, its handlers shall read persisted daemon observations without collecting live host data in a request.
- AC-OBS-NODE-006.2: When the tab loads for a hosted node, its client shall read the selected node's decrypted snapshot and shall not substitute the cloud server's host observations.
- AC-OBS-NODE-006.3: When the tab is hidden, inactive, or switched to another node, its polling and replay shall stop or discard obsolete results.
- AC-OBS-NODE-006.4: When the global runtime selection changes, the tab shall remain explicitly node-wide and shall not hide unrelated activity.

### REQ-OBS-NODE-007: Visual explanation

As an operator, I want to follow an event through the node so that I can understand a change without reading raw records.

- AC-OBS-NODE-007.1: When an observed event is selected, the map, evidence, resource history, and replay position shall show the same event.
- AC-OBS-NODE-007.2: When motion is reduced or the tab is hidden, the interface shall stop travel animations while retaining the evidence.
- AC-OBS-NODE-007.3: When no observations are available, the tab shall show a useful unavailable state and shall not insert illustrative telemetry.
- AC-OBS-NODE-007.4: When the view is used on a narrow screen, its controls and evidence shall remain accessible without page-level horizontal overflow.
