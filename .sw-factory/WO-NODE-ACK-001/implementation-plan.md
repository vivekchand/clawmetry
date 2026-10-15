# Implementation Plan: WO-NODE-ACK-001

## Summary and approved scope

A real hosted save was applied, then duplicate delivery posted an unconfirmed result over the original acknowledgement. Reproduce using the real LocalStore, then let only the nonce claimant publish an outcome. A retained claimed nonce returns without mutation or result publication. Preserve first-attempt failure and crash uncertainty; no automatic retry or receipt store.

Factory requirement `d33e1d0b-43c1-4d3f-8d0d-8de6628d0583` and design `2dffd534-2073-4af2-b943-d6dbed701ee1` were updated, read back and approved before implementation. Four new ACs govern mutation ownership, acknowledgement ownership, expired retained duplicates and fail-closed first attempts. The original referenced Node blueprints were read in the prior execution and remain unchanged.

## Reuse and architecture

Reuse `clawmetry/sync.py`'s sealed Node action path, node/request binding, existing action lock, durable timestamp nonce ledger, preference/review methods, query readback and encrypted result publication. Keep the 512-entry cap and current 600-second claim retention, 300-second freshness checks and cloud cache boundaries. No new dependency, schema, receipt payload, cloud transport or UI API is required.

Inside the existing lock, load retained claims after authenticated decryption and valid node/request binding. Return immediately for a retained claimed nonce. For an unclaimed nonce, retain freshness, exact operation fields and capacity validation before the durable claim and original apply/readback/result path. This ordering prevents an expired or malformed duplicate from manufacturing a replacement error. Do not relax validation for unclaimed actions or apply claimed actions again.

## Files and sequence

1. Save verified records, context and this plan before code changes.
2. Add real LocalStore integration guards in the existing `tests/test_node_activity_wiring.py`; prove current duplicate behaviour fails the expected one-result contract before editing implementation.
3. Make the minimal ordering/return change in `clawmetry/sync.py`, and update the existing stub replay assertion to expect unchanged original acknowledgement.
4. Exercise concurrent duplicates, changed-body reuse, retained expired duplicates, restarted stores, original apply failure, interrupted claim and result-publication failure. A fresh request remains the only recovery path. Preserve cap and ledger-read failure guards.
5. Mirror the four exact Factory ACs in `docs/acceptance_criteria.json`, cite one per line in meaningful test docstrings and tighten the ratchet.
6. Obtain independent cloud and root review, resolve blockers, run focused tests and relevant lint/drift gates, then refresh main and prepare the isolated correction PR. Root owns merge/release and actual hosted proof.

## Testing and evidence limits

The initial diagnostic used an actual isolated LocalStore, all six preferences true, sealed duplicate delivery and intercepted result publication. It reproduced two acknowledgement results (success then failure), one retained nonce and unchanged true preferences, without contacting cloud or production.

New real-store tests use scratch HOME/audit/store, no server fixture and intercepted result posting. Run the focused wiring and collector/store suites with `--noconftest`. Confirm ledger and preference/event state in DuckDB, not stub-only counters. Concurrent callers must execute once and publish one result; reopening the database must retain suppression. First apply failure or lost result publication must not become duplicate success. Fresh requests must still work. Keep existing authentication, binding, cap and fail-closed tests.

Run targeted product Python lint, syntax, Python 3.9 annotation, AC coverage, daemon allowlist, module map and CI test-file coverage checks appropriate to the minimal change. No browser/product UI behaviour changes are planned. Actual hosted Save settings/review confirmation remains a post-release task; isolated tests do not claim deployed proof.

## Ownership

node_backend authors implementation/tests/manifest and execution artifacts in the isolated `fix/node-ack-once` worktree. Existing cloud delegate independently reviews transport semantics and final code; root independently verifies and owns merge/release/deployment. No production node or peer branch is mutated during this execution. Direct Factory MCP and a Factory work-order record are not exposed here; the record-owning delegate supplied verified readbacks before implementation, and this local execution uses the approved root task as its work-order scope.

## Implementation and verification evidence

Six real-LocalStore guards failed on the original product code, recorded in `/tmp/clawmetry-node-qa/node-ack-red.log`. After the minimal product correction, eight real-store integration guards and existing suites pass: **64 focused tests** including the frontend runner. The four exact new criteria are mirrored and the ratchet is tightened to 386/454 covered with the prior 68 uncovered unchanged. No new production store schema or receipt state exists.

The test module now installs a scratch HOME/audit path and NullHandler before sync fixture imports. This prevents expected test failures from appending warnings to the live daemon log. The first isolated standalone diagnostic already used scratch HOME before import. Earlier direct pytest invocations could append warning-log lines despite isolated audit/store paths; production log content was left untouched afterward, and no production preferences or telemetry stores were mutated.

Syntax, Python 3.9 compatibility, daemon allowlist, module-map drift, CI test-file coverage, English and whitespace checks pass. The changed wiring test file lints clean. Default Ruff on the large existing sync module reports 26 pre-existing findings; its code/message multiset matches HEAD exactly, with no new finding.

Cloud delegate independently reviewed the complete product/test/manifest bucket, read both transport paths and result cache semantics, and ran 63 backend/wiring source tests successfully. Root independently reviewed the minimal product diff and ran all 27 wiring tests. Review approval is for implementation only: inspected release wheel, daemon upgrade, hosted preference save/review and final user-facing completion remain PENDING under root ownership.
