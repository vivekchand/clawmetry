# English explanation policy

## Feature Summary

This design implements [Clear English explanations](STE100_REQUIREMENTS.md).
It combines an editorial policy, a project glossary, offline checks, and a migration inventory.
Mechanical results and full editorial review are separate evidence.

The first implementation is [ClawMetry PR #6248](https://github.com/vivekchand/clawmetry/pull/6248).
Assess the new modules and CI integration against that branch until it merges.
It covers the English catalog, literal templates, weekly insights, Activity explanations, alerts, Advisor answers, chart explanations, and evaluation reasons.
Other dynamic messages, documentation, repositories, and editorial review remain pending in `docs/STE100_COVERAGE.md`.

## Component Blueprint Composition

The existing English catalog and translation runtime continue to supply browser text.
The weekly digest continues to obtain facts through the existing daemon query path.
Language checks operate on owned text after generation and before display or storage in the digest.

## Feature-Specific Components

```component
name: EnglishPolicy
container: Python package
responsibilities:
	- Check the implemented mechanical rules without network access
	- Load project terminology from clawmetry/data/english_terms.json
	- Provide shared generation instructions
```

Implementation: `clawmetry/english.py`. The module returns rule identifiers and explanations; it never rewrites input.

```component
name: EnglishInventory
container: CI
responsibilities:
	- Discover English catalog messages and visible template text
	- Report remaining source files that need extraction and review
	- Reject new violations against a content-bound baseline
```

Implementation: `scripts/check_english.py`, with a baseline in `docs/english_baseline.json`.
`#EnglishInventory` sends extracted messages to `#EnglishPolicy` and reports file locations.
The baseline identifies the source, text hash, and rule. A changed message cannot inherit an exception for an old message.
CI also compares the baseline with the pull request base so contributors cannot add debt to make a new violation pass.

```component
name: InsightLanguageBoundary
container: Python package
responsibilities:
	- Apply the common policy to direct and relayed synthesis
	- Keep result rows and known token usage when prose is rejected
	- Use a fixed message when a summary is unavailable
```

Implementation: `clawmetry/insights.py`.
`#InsightLanguageBoundary` calls `#EnglishPolicy` once per generated explanation.
It records only the rule identifiers in warnings, not the rejected prose or user rows.
The existing Activity caller in `routes/brain.py` supplies its own fixed fallback because that screen has no digest result table.
It loads the insight configuration from `clawmetry/insights.py` and does not invent a model name for relay responses.

### Additional generation boundaries

The alert narrator in `clawmetry/narrator.py` applies common instructions and validates narration before returning it to dispatch.
Rejected narration returns no enrichment, so the existing caller retains its original alert.
Scheduled briefs retain their four-sentence limit; other alerts retain their three-sentence limit.
The brief fallback reports an unavailable summary without guessing whether the credential was missing.

Advisor in `routes/advisor.py` validates the final answer after either transport completes.
Its fallback keeps the response's model, context count, and known token usage.
Shared transport functions still accept custom output contracts used by Dives.

Dives in `clawmetry/dives_prompt.py` requests the common writing rules for titles and descriptions.
The boundary in `routes/dives.py` validates these fields after JSON parsing.
SQL, chart types, axis mappings, and query results are not language-rewritten.

The classic evaluation boundary in `clawmetry/eval_runner.py` validates the reason separately from the parsed score.
The optional bridge in `clawmetry/deepeval_bridge.py` requests the same rules for explanation fields and validates each completed metric reason.
Existing JSON schema retries remain unchanged; language rejection does not trigger them.
The score, pass/fail result, source transcript, and persistence path remain unchanged.

### Browser fallback coverage

This delivery follows PR #6248. Its design was committed before implementation.
The first audit used a regular expression and found 775 candidates with a null parameter argument.
The implemented source extractor replaces that audit for supported translation calls, including parameterized calls.
It checks 980 literal fallback occurrences. It reports 48 calls with dynamic or missing literal arguments as pending.
Other browser rendering remains pending. This delivery has not been released.

The checker verifies that each supported literal key exists in the English catalog.
Its literal fallback must match the catalog, with HTML entities decoded for comparison.
Missing catalog entries are added after reviewing their use in the surrounding UI.
Parameterized messages retain their values, units, identifiers, and escaping.
Empty results and unavailable results keep separate explanations.
Source evidence and executable content stay outside the prose inventory.

`scripts/english_js.py` distinguishes code, comments, string literals, regex literals, and template expressions without executing source.
`scripts/check_english.py` reports source locations and message keys. Known forwarding helpers have explicit argument positions.
Unsupported expressions remain pending. This lexer is not a full JavaScript parser; `node --check` verifies syntax separately.
Regression tests cover escaped quotes, nested arguments, template expressions, Unicode escapes, division, and optional calls.

Connection, Quality, and Security messages now have consistent catalog and fallback text.
Security messages retain counts and uncertainty. Matching recorded hashes does not establish that no events were removed.
Tests execute the shipped translation function and relevant renderers with the catalog both available and unavailable.
Cost labels retain their amounts and financial basis. Channel loading messages retain the selected channel.
These checks do not close the complete surfaces: their other dynamic rendering still requires extraction and review.
This step does not close CLI, documentation, cloud, Pro, website, or full editorial review.

## System Contracts

- English descriptions use a 25-word limit. Instructions use a 20-word limit.
- Unclassified text uses the stricter 20-word limit until its type is recorded.
- The checker reports its implemented subset. It does not assert dictionary or semantic compliance.
- The glossary records project terms and editorial preferences. It is not a copy of the ASD dictionary.
- Prose catalog keys and placeholders are stable during text migration. Missing template keys are added. CSS incorrectly stored as a translation is removed from all catalogs and kept as code.
- Source evidence, commands, and identifiers are protected from rewriting.
- Missing or invalid generated text has a fixed fallback. No additional model request is made.
- The existing facts, data persistence path, encryption, and access controls remain authoritative.
- An inventory entry does not mean that a message was reviewed.

## Architecture Decision Records

### ADR-001: Offline mechanical checks plus editorial review

**Context:** The standard includes contextual meaning and parts of speech, which a small checker cannot establish.

**Decision:** Implement only well-defined mechanical checks and document their limits. Require editorial review against the official standard.

**Consequences:** CI catches regressions in the implemented subset. Full compliance remains a separate review outcome.

### ADR-002: Reuse existing text sources

**Context:** The app already has a shared English catalog, live templates, and translation fallbacks.

**Decision:** Check those sources directly. Discover additional source candidates and migrate them in complete surface groups.

**Consequences:** No second translation runtime or frontend build step is needed. Dynamic sources remain explicitly pending until covered.

### ADR-003: Reject generated prose without rewriting facts

**Context:** A language rewrite can change values, uncertainty, or the meaning of source evidence.

**Decision:** Use shared instructions, offline validation, and fixed fallbacks. Keep the original query results.

**Consequences:** Rejection costs no additional model call. The user still has access to the underlying evidence.
