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

### Readable attribute fallbacks

Design recorded before implementation on 2026-10-02. The connected dashboard
shows the internal key `nav.guard_tooltip` because the English catalog lacks
that key and the attribute translator discards the original tooltip.
The same translator handles input hints and accessible names.

`clawmetry/static/js/i18n.js` shall retain each attribute's original literal
text before applying a translation. Resolution shall use the selected language,
then the English catalog, then that original text. Repeated application and
language changes shall not replace the stored fallback with translated text.
Missing text shall stay empty instead of exposing an internal key.

The live navigation in `dashboard.py` shall have catalog entries for all its
translation keys. The Guard explanation shall describe the warnings and
available controls without promising that every agent can be stopped.
The catalog and HTML fallback shall agree. The existing template-key guard
shall also inspect the served dashboard literal without importing the app.

Tests shall execute the shipped translation runtime with missing catalogs,
partial translations, repeated application, and language changes. They shall
cover title, placeholder, and accessible-name attributes. Restoring the prior
runtime or catalog shall make the relevant regression fail.
This correction changes no actions, data, permissions, or network requests.
Other unreviewed navigation wording remains in the migration inventory.

### Command-line help

The central parser in `clawmetry/cli.py` has 182 literal help values. The initial source audit found 35 mechanical findings in 30 values.
The AST extractor and prose migration now check those values, with no remaining mechanical findings.
This delivery applies the existing requirements to command discovery and option help. It does not yet close interactive prompts or command-result messages.

`#EnglishInventory` uses an AST extractor in `scripts/english_python.py`.
It reads literal `help`, `description`, `epilog`, and `title` arguments from supported argparse calls without importing or executing the CLI.
Adjacent Python string literals form one message. Dynamic expressions remain explicit pending entries.
Central parser prose must be literal for the language gate to pass. The inventory still reports unsupported or empty fields for review.
Findings retain the source file, line, parser receiver, option name, and field.
Only prose fields are checked. Option spellings, defaults, choices, destinations, and program behavior are not rewritten.

Central parser help in `clawmetry/cli.py` is revised after reviewing each finding in context.
Command examples and option references stay explicit. Local setup help no longer implies that all network activity is disabled.
The CLI help checks use the 20-word instruction limit and the same empty debt baseline as the browser corpus.
The inventory continues to list all other Python text as pending.

Tests render real argparse help without loading the dashboard, store, or sync daemon.
The regression checks cover local setup, cloud connection, update policy, key-file input, and destructive command options.
Comparing the parsed source before and after migration, with only prose fields removed, gives identical results.
The new rendered-help guard fails against the previous help text and passes after migration.
No additional runtime dependency, network call, or model request is required.

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
The inventory separately discovers `frontend/src` TypeScript and TSX files as pending sources. Their JSX and translation API require separate extraction.

Connection, Quality, and Security messages now have consistent catalog and fallback text.
Security messages retain counts and uncertainty. Matching recorded hashes does not establish that no events were removed.
Tests execute the shipped translation function and relevant renderers with the catalog both available and unavailable.
Cost labels retain their amounts and financial basis. Channel loading messages retain the selected channel.
These checks do not close the complete surfaces: their other dynamic rendering still requires extraction and review.
This step does not close CLI, documentation, cloud, Pro, website, or full editorial review.

### Parameterized browser explanations

This follow-up design is recorded before implementation, after consolidating the initial browser and CLI work into PR #6248.
The inventory still lists 48 calls with computed keys, computed fallbacks, or missing literal fallbacks.
Calls with a fixed catalog key and known parameters can use the catalog's literal template directly.
The migration shall retain each supplied value, unit, singular/plural distinction, and HTML-escaping boundary.
It shall not evaluate arbitrary source expressions or replace observed agent text.

Forwarding helpers and table-driven keys require separate treatment. They shall remain pending unless their complete key and fallback set is extracted and checked.
A helper that can run before the translation library loads shall interpolate supported placeholders locally, or retain its existing computed fallback until that behavior is implemented and tested.
Tests shall use the shipped translation function and relevant rendered functions with the catalog present and absent. Any helper change shall also be tested without a translation function.
No poller, API call, package dependency, or pricing behavior changes are required.
The initial release PR remains fixed while its CI runs. This follow-up will have its own verification and release evidence.

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
