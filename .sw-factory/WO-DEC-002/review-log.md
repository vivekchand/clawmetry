<!--lint disable strong-marker-->

# Review Log: WO-DEC-002

**Work Order:** WO-DEC-002 — Mandatory local assessment masking and scoped restoration
**Initialized At (UTC):** 2026-10-01T09:10:32Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Independent final review, 2026-10-01

Reviewer: dedicated `decision_credits_final_review` agent, reviewing DEC-002 in the isolated OSS worktree. No implementation files were edited by the reviewer.

### Requirements and blueprint alignment

The reviewed implementation satisfies the seven mirrored privacy/restoration criteria for this local primitive. It masks nested keys and values, preserves exact identifier equality within one request, isolates requests, fails closed on unsupported coverage or masking failures, and restricts restoration to an authorized local explanation. It adds no inference activation, provider client, billing logic, persistence, or daemon writer path. Consent/egress checks remain a caller-facing boundary that future integrations must actually use.

### Findings resolved before approval

- Known provider credentials containing underscores or hyphens were initially emitted unchanged or partially redacted. Complete supported suffixes are now removed irreversibly, with regression tests in both the assessment and shared redaction suites.
- Percent-only email candidates and repeated incomplete private-key headers initially exceeded scan deadlines inside regular expressions. Shared patterns were corrected; the assessment boundary now bounds strings, unbroken lexemes, and overlapping scan windows. Actual adversarial subprocess tests enforce elapsed-time bounds.
- A phone at offset 1012 initially became a token for only its prefix, leaving its final digits on the wire. Window ownership now assigns each candidate start once with real lookbehind and sufficient lookahead. The suite checks every offset from 512 through 1023 for supported formats and exact equality/restoration.
- Greedy IBAN candidates initially consumed adjacent uppercase prose and missed valid identifiers. Candidates now use country-specific lengths and case-insensitive ASCII matching. Lowercase/mixed-case IBAN and NINO coverage is tested.
- Valid card/phone prefixes followed by ambiguous numeric prose initially passed unchanged. Such assessment payloads now stop with a controlled ambiguity error; no partial identifier is sent or restored.
- Structured secret aliases and the documented 4 KiB string/320-character lexeme limits were clarified and covered.

### Architecture, security, privacy and resource review

Reviewed the complete masking/secret prepass, immutable bytes handed to transport, policy and scope checks, per-attempt consent/egress checks, serialized revocation, TTL cleanup, weak timer ownership, serialization refusal, controlled exceptions, and one-pass escaped restoration. Restorable values remain local and secrets never enter the restoration map. The component relies on trusted synchronous transports honoring their supplied timeout, as explicitly documented. It does not claim names, addresses, Unicode text, or contextual identification are covered, and it makes no anonymity claim.

### Verification performed independently

- `python -m pytest -q tests/test_assessment_privacy.py tests/test_redaction_pii.py`: **140 passed**.
- `python -m pytest -q tests/test_redaction.py tests/test_egress_suppression.py`: **70 passed**.
- Additional independent probes: **300** phone/card/IBAN/national-ID boundary cases passed after the window fix; **237** generated IBAN country-length/case/spacing examples passed exact masking and restoration checks.
- Reproduced and then verified the original provider-key, percent/PEM, partial-phone, IBAN-prose, and ambiguous numeric-tail findings.
- `scripts/check_ac_coverage.py --check`: passed, seven new criteria covered and the existing ratchet preserved.
- `scripts/gen_module_map.py --check` and `git diff --check`: passed.

These are local primitive and fake-transport checks. No provider request or production action was made. Browser verification is not applicable to this code-only component; cross-platform CI, release, published-wheel inspection, and production installation verification remain delivery steps.

### Files reviewed and verdict

Reviewed `clawmetry/assessment_privacy.py`, shared `clawmetry/redaction.py` changes, the three changed/new assessment and redaction test files, `docs/ASSESSMENT_PRIVACY.md`, `docs/EGRESS.md`, acceptance mirror/baseline, module inventory, CI changes, and work-order plan/context.

- Remaining blocking findings: **0**.
- Remaining advisory findings requiring code changes: **0**.
- **Verdict: APPROVED for the reviewed DEC-002 local primitive.** This is not approval or evidence of a completed managed assessment or recovery flow.

## Style-only follow-up review, 2026-10-01

The same independent reviewer checked the import ordering, sorted slot declarations, explicit `subprocess.run(check=False)`, and line-local explanations for the three fail-closed exception boundaries. No semantic drift was found: slot names are unchanged, subprocess checking retains its previous default, and exception handling is unchanged. The unused blank review template was removed; the completed review above is preserved.

- `python -m pytest -q tests/test_assessment_privacy.py`: **92 passed** after the style changes.
- Remaining blocking findings: **0**.
- **Verdict: APPROVED.** No implementation files were edited by the reviewer.
