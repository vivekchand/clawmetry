# Built-in physical agent observation

## Overview

A Jumper owner should install ordinary ClawMetry and use its existing observation and governance surfaces. A separate observer package fragments discovery and asks users to understand plugin internals. The explicit user correction authorizes the Jumper adapter as OSS; Mizu is a separate simulator/skills/demo application only. The implementation-plan.md recorded this intent and architecture before implementation. This document expands that existing plan into stable acceptance IDs.

## Terminology

Supported: an adapter with an exposed, known telemetry contract. Simulation evidence: measured simulator output, not hardware qualification. Task decision: permission to forward a request in an explicitly enabled host integration, not proof a robot stopped.

## Requirements

### REQ-JUMPER-001: One installation
As a robot owner, I want the ordinary ClawMetry installation to observe supported robot activity, so I can review it without a separate observer plugin.
- AC-JUMPER-001.1: When a normal wheel is installed without Pro or simulator libraries, the system shall include the Jumper observer and generic Physical AI view.
- AC-JUMPER-001.2: When an application publishes named telemetry, the system shall discover and persist its journal through the existing daemon and expose the same evidence to the view.
- AC-JUMPER-001.3: When no hardware bridge is connected, the system shall explain the missing connection without claiming automatic access to unpublished robot state.
- AC-JUMPER-001.4: When an upgrade adds a supported source, the system shall reconsider journals skipped by an earlier collector in bounded, persistent replay passes. An unchanged support registry shall not repeat the replay or duplicate evidence and notifications.

### REQ-JUMPER-002: Scope and state honesty
As a robot operator, I want decisions and measurements distinguished from execution outcomes, so I can understand what actually happened.
- AC-JUMPER-002.1: When a request is evaluated, the system shall record its task identity, decision and separate controller receipt if supplied by the host.
- AC-JUMPER-002.2: When state is stale, invalid, out of scope or an action is unqualified, the system shall withhold permission to forward it.
- AC-JUMPER-002.3: When hardware is observed, the system shall never invoke a controller or infer a physical stop.
- AC-JUMPER-002.4: When workspace checks are applied, the system shall recompute measured full-body clearance against the task workspace.

### REQ-JUMPER-003: Shared evidence and alerts
As an owner away from the desk, I want a recorded history and incident notifications through my preferences, so I can review relevant episodes.
- AC-JUMPER-003.1: When a typed finding is committed, the system shall use the existing incident delivery path with fixed sanitized descriptions and deduplication.
- AC-JUMPER-003.2: When cloud sync is enabled, the system shall expose bounded robot evidence only in the existing encrypted snapshot/relay path.
- AC-JUMPER-003.3: When another legacy Asimov run is read, its existing source-specific API shall remain Asimov-only.
- AC-JUMPER-003.4: When the view is hidden or suspended, the system shall stop its polling.

## Non-goals, alternatives and accepted risks

No hardware DDS connection, motor control, guaranteed containment, human detection, intent classification, cup manipulation, website simulator hosting or paid-adapter ungating in this OSS change. A standalone adapter package was rejected by the user. Raw file reads in Flask and a second database were rejected because they break cloud parity and daemon writer ownership. Runtime transcript catalogue inflation was rejected: this is robot evidence, not an LLM chat runtime. Third-party host measurements are unverified; record provenance and missing values honestly. Channel delivery status is not proof of phone display.
