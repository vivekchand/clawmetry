# Improve: understand an incident and plan prevention

## Overview

An operator reviewing a correction or frustration signal needs to understand the
conversation that produced it. Sending them to the whole Setup inventory leaves
them to diagnose the failure themselves. Explain with Assistant starts a saved
conversation with the selected occurrence and its recorded context attached.

The answer connects what the person wanted, what the agent attempted, and what
the results establish. It proposes a small prevention step and an observable
check for a future run. Applying changes and monitoring later runs are separate
actions; a proposed fix is never described as already applied or proven.

This is a local feature record prepared before implementation using the Software
Factory skill's fallback workflow. Hosted Factory sync is pending connector
access. It extends the existing Assistant requirement
fb690e36-8372-48f6-8e52-32fe5bffc345 and blueprint
4be233ec-e717-4886-a6e3-8bf855597abb, with evidence access supplied by PR #6350.

## Terminology

An occurrence is one recorded user message behind an Improve signal. A signal
is a wording-based candidate for investigation, not a verified failure or cause.

## Requirements

### REQ-IMPROVE-CHAT-001: Explain an occurrence

As an operator, I want to ask Assistant about a selected Improve occurrence,
so that I can understand what happened without finding session identifiers.

- AC-IMPROVE-CHAT-001.1: When Explain with Assistant is selected, the system shall
  open a new Assistant conversation with the exact occurrence reference and a
  readable question, starting once when the selected engine and data are ready.
- AC-IMPROVE-CHAT-001.2: When diagnosing an occurrence, the system shall retrieve
  the message and bounded surrounding messages and tool evidence from the
  authenticated node's store before generating an answer.
- AC-IMPROVE-CHAT-001.3: When the reference is absent, unavailable, outside scope,
  or unsupported by the installed collector, the system shall explain recovery
  without guessing a session or sending an ungrounded diagnosis.
- AC-IMPROVE-CHAT-001.4: When the node/account changes or the user leaves, edits,
  or replaces the pending question, the system shall cancel automatic submission
  and prevent evidence crossing that boundary.
- AC-IMPROVE-CHAT-001.5: When answering, the system shall request a plain-language
  explanation, distinguish observations from uncertainty, propose a prevention
  step with a future verification criterion, and not claim to apply or verify it.
- AC-IMPROVE-CHAT-001.6: When the answer is saved or followed up, its source
  references shall remain attached through the existing Assistant history.

## Feature blueprint

### Feature Summary

This feature composes the existing Improve candidate builder and Assistant
executor to satisfy REQ-IMPROVE-CHAT-001 in local and encrypted hosted clients.

### Component Blueprint Composition

The Improve candidate builder attaches a single canonical occurrence reference
to each signal. The Assistant browser receives that reference without copying
transcripts, then sends it through the existing authenticated Assistant transport.
The Assistant service uses PR #6350's redacted, scoped evidence reader and its
bounded investigation/context/persistence pipeline.

### Feature-Specific Components

```component
name: AssistantImprove
container: Local sync daemon
responsibilities:
	- Validate occurrence references and retrieve the selected user message
	- Seed bounded context reads with explicit coverage and existing redaction
	- Frame diagnosis, prevention and future verification without acting on agents
```

### System Contracts

`improve` in a chat request contains only `session_id`, `runtime`, and an
`events:`-qualified `event_id`. The daemon supplies node identity. The reference
does not bypass runtime entitlement, export redaction, provider selection,
offline controls, cancellation, or saved-conversation limits.

Three initial reads count against the existing eight-read budget: the anchor,
up to 10 preceding items, and up to 20 following items in the first hour. Limits
and continuations remain visible. The planner may continue or widen reads within
its remaining budget. No new poller, raw-file request read, provider endpoint,
automatic configuration write, or automatic recurrence monitor is introduced.

The reference must match the evidence reader's canonical session runtime.
Runtimes without a supported identity contract retain their excerpts and show
why Assistant cannot attach them. They do not silently fall back to another
runtime. Updating those adapter contracts is outside this handoff change.

### Architecture Decision Records

#### ADR-001: Extend the existing Assistant evidence path

Context: A separate explanation endpoint would duplicate provider, persistence,
scope, and encrypted relay behavior. Decision: seed the existing chat pipeline
with a validated occurrence. Consequences: follow-ups and saved sources work in
the same conversation, and delivery depends on PR #6350.
