# DEC-002: Mandatory local assessment privacy

## Summary
Implement the reusable local boundary for private tracking issue #2549. This OSS slice contains no billing rules, paid rubric, provider client, inference activation or new persistence. Pro evidence selection and managed-service integration follow through daemon/plugin seams. Existing ingestion and judge opt-out behavior stays unchanged.

## Code reuse and package structure
Reuse actual strict patterns and validators in clawmetry/redaction.py, never helpers that fall back to raw input. Built-in coverage: ASCII email, international + phone, validated card/IBAN, existing US SSN/UK NINO/Indian Aadhaar/Dutch BSN formats. Arbitrary names, addresses, Unicode email and contextual identification remain unsupported. Explicit required category/language policies fail closed for unsupported coverage. Structured secret fields are wholly withheld regardless of value type. No new dependencies.

New clawmetry/assessment_privacy.py, tests/test_assessment_privacy.py and technical docs/ASSESSMENT_PRIVACY.md. Parent updates docs/EGRESS.md and required CI. No product revenue/pricing prose in OSS.

## Components and flow
Immutable policy metadata -> bounded request-local masking session -> canonical immutable JSON bytes -> consent/egress gate -> caller's bounded transport. Local restoration is separate from outbound bytes. No module-level mapping cache, files, database, telemetry or network client. Exceptions expose controlled codes only.

A session masks exactly one JSON-like payload, including nested keys and values, state, questions, rubrics and metadata. Exact PII values remain equal within one request using random opaque tokens; namespaces differ across sessions/accounts. Secret removal precedes PII masking and is irreversible, including secret containers, private keys, bearer/basic credentials and known token formats. Include generic apikey_ shapes without any actual credential. Reject reserved-token literals and colliding sanitized keys. Bound UTF-8 bytes, depth, node count, finite numbers and elapsed scan time; reject unknown objects instead of stringifying. Global redaction switches cannot weaken assessment masking.

Maps stay only in memory, with safe repr and serialization refusal. Clear on close and TTL expiry. Restore exact issued placeholders once, only within explicitly permitted explanation fields and the correct local scope. Escape display text. Unknown/forged/cross-request tokens remain masked; typed scores/labels have no restoration path. Expired maps preserve masked text without guessing. Never persist or transmit restored values/maps.

Dispatch uses only masked immutable bytes. Recheck consent policy/generation, egress suppression and expiry on every attempt under a revocation lock. Revocation must not acknowledge while a send starts; already-started work is distinguishable. Transport callback owns no raw input and must have a bounded deadline. Component does not claim all existing LLM paths use it.

## Steps
1. Plan/context/checklist before code.
2. Agent implements module and adversarial tests only; parent owns docs, CI and integration review.
3. Dedicated independent review covers privacy, consent, resource limits, restoration and evidence; fix blockers.
4. Green OSS PR, merge, separate release PR, inspect published wheel, cloud pin/deploy where required and installed-contract verification. Managed assessment activation stays off until Pro integration/provider readiness.

## Testing
Inspect actual bytes delivered to a fake external-hop transport. Cover each category/secret in all nested locations, equality and isolation, literal/forged tokens, key collisions, cyclic/deep/non-JSON/nonfinite/oversized input, detector failure/timeout, global opt-outs, unsupported policy/language, no/changed/revoked consent, retry and concurrent revoke/send, offline/custom endpoint, TTL expiry, one-pass escaped restoration. Run existing redaction/PII/egress suites and CI across Python versions/OS. Unit fixtures do not establish real assessment E2E; this pure local component needs no provider request. Inspect the published wheel before claiming shipped functionality.

Initial implementation policy is ASCII English only; reject other text rather than claiming coverage. Required CI uses the existing hash-pinned cross-platform/Python 3.9 and 3.11 dependency set. Mirror the seven privacy/restoration criteria directly from their linked Factory detail, declare matching test coverage and regenerate the module inventory.

Review-driven shared detector correction: a known provider-key suffix with underscores escapes the existing candidate regex, and long percent-only email candidates backtrack beyond the masking deadline. Extend the narrow shared redaction.py candidate patterns and their regression tests to capture complete known credentials and prevent pathological scans. Keep existing ingest opt-out/fallback policy unchanged. Bound every candidate path and verify adversarial timing in a subprocess; checking a clock only between unbounded regex calls is insufficient.

The same review extends candidate correction to bounded PEM labels, country-length IBAN boundaries (including mixed case), case-insensitive NINO and ambiguous separated numeric tails. Strict card/phone validators remain strict. Ingestion withholds an ambiguous candidate, while assessment preparation rejects the entire payload. Scan-window tests exercise every offset in a full stride so a partial match cannot preempt a complete identifier.

Traceability verification also found an existing AC-GUX-001.1 manifest entry without its namespace in the manifest's in-repo prefixes. Include the missing AC-GUX- prefix metadata; preserve the guard's assertions and all existing uncovered criteria.
