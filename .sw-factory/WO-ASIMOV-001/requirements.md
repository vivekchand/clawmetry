# Asimov 1 observation connector

## Overview
Asimov developers need to understand what their humanoid is doing and connect its measured condition with the application that requested an action. ClawMetry shall provide a free, open-source observation connector and useful local inspection, with the same evidence suitable for its existing encrypted Physical AI history pipeline.

The first delivery observes and records. It shall distinguish physical feedback, requested actions, source-reported faults and unknown outcomes, and shall state the actual validation level. Founder outreach and hardware sponsorship discussions are separate activities, not implementation acceptance criteria.

## Terminology
- Observe credential: Menlo connection authority limited to receiving robot information.
- Command evidence: a request, return or exception observed in an explicitly instrumented controlling application; it does not establish acceptance or movement.
- Source time: timestamp reported by the robot or a recording, distinct from collector receipt time.
- Hardware qualification: verification using actual Asimov hardware rather than SDK fixtures or a simulator.

## Requirements

### REQ-ASIMOV-001: Free local observation
As an Asimov developer, I want to inspect robot evidence locally without a paid license, so that I can debug my application on my own machine.
- AC-ASIMOV-001.1: When Pro is absent and license enforcement is enabled, the connector shall still import supported recordings and display persisted telemetry locally.
- AC-ASIMOV-001.2: When the developer starts the connector without optional Menlo dependencies, the system shall explain the required installation without breaking ordinary ClawMetry commands.
- AC-ASIMOV-001.3: When live credentials are absent, the system shall offer the recording path and shall not invent a robot connection.

### REQ-ASIMOV-002: Read-only live telemetry
As a robot operator, I want observation that cannot issue motion commands, so that monitoring does not change robot behavior.
- AC-ASIMOV-002.1: When connected with the documented Observe credential, the collector shall receive state without calling a robot command or changing connection authority.
- AC-ASIMOV-002.2: When state is received, the system shall preserve available positions, velocities, currents and temperatures for all 25 actuators, orientation, battery and alerts with explicit units.
- AC-ASIMOV-002.3: When measurements are missing or null, the system shall preserve that uncertainty instead of showing zero.
- AC-ASIMOV-002.4: When a connection fails or telemetry stops advancing, the system shall show stale/disconnected evidence and record a bounded diagnostic without claiming current robot state.

### REQ-ASIMOV-003: Opt-in application tracing
As an application developer, I want to connect commands with observed feedback, so that I can explain what happened during an agent run.
- AC-ASIMOV-003.1: When tracing is explicitly installed, the system shall record the original application's command requests, returns and exceptions without changing their result or control flow.
- AC-ASIMOV-003.2: When the SDK returns without an authoritative outcome, the system shall retain an unknown outcome and shall not claim command acceptance or successful movement.
- AC-ASIMOV-003.3: When tracing is not installed, the system shall not patch SDK methods automatically.

### REQ-ASIMOV-004: Official recording import
As an Asimov developer, I want to inspect Menlo SDK recordings, so that I can debug offline or share evidence from a remote robot owner.
- AC-ASIMOV-004.1: When a valid official recording is imported, the system shall retain robot/run identity, source timing, telemetry and command distinctions.
- AC-ASIMOV-004.2: When records are malformed, truncated or outside supported bounds, the system shall continue safely where possible and report incomplete evidence.
- AC-ASIMOV-004.3: When the same imported evidence is replayed, persisted events shall not silently duplicate or overwrite conflicting identities.

### REQ-ASIMOV-005: Bounded durable evidence
As a robot developer, I want recording to remain lightweight, so that observation does not block the application or grow without limit.
- AC-ASIMOV-005.1: When a producer records evidence, its callback shall use a bounded nonblocking queue and shall not perform database or network work.
- AC-ASIMOV-005.2: When queue or disk bounds are reached, the system shall surface dropped/incomplete evidence and shall not falsely report a complete recording.
- AC-ASIMOV-005.3: When evidence is queried, the system shall read persisted DuckDB state through the daemon writer service rather than raw robot files in a request handler.
- AC-ASIMOV-005.4: When evidence is serialized for the existing robotics pipeline, the system shall preserve the robotics.v1 contract, nanosecond precision, source/receipt clocks and explicit environment.

### REQ-ASIMOV-006: Honest delivery and coexistence
As a ClawMetry user, I want clear compatibility and validation boundaries, so that I can rely on the claimed support.
- AC-ASIMOV-006.1: When hardware has not been exercised, documentation and UI shall explicitly avoid claiming hardware-qualified support.
- AC-ASIMOV-006.2: When Pro is installed, Asimov integration shall coexist with existing SO101/RoboSim/RP1 evidence and shall not replace unrelated plugin handlers.
- AC-ASIMOV-006.3: When the hosted Asimov view is opened, it shall render the emitted encrypted `asimov` snapshot slice after client-side decryption or explain unavailable evidence; server-side raw robot reads are forbidden.
- AC-ASIMOV-006.4: When packaging the connector, the system shall not raise ClawMetry's declared Python minimum or require numerical/media libraries for users who do not run Asimov collection.
