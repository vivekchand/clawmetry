# English migration coverage

Status: implementation in progress. Full STE compliance is not established.

Generate the current inventory with:

```sh
python3 scripts/check_english.py --inventory
```

The inventory discovers files on each run. File counts are not review counts.
The baseline is empty for the currently extracted corpus. This does not close the pending source or editorial reviews.

| Surface | Mechanical checks | Remaining evidence |
| --- | --- | --- |
| English catalog | All string values | Full dictionary, grammatical role, and meaning review |
| Live HTML templates | Literal prose across inline tags and accessibility attributes | Rendered expressions, inserted values, and editorial review |
| Weekly insight fallbacks | Shared fixed messages | Integration tests and served report verification |
| Weekly generated insights | Common instructions and validation on both synthesis paths | Generation evaluation and editorial quality review |
| Activity turn explanations | Same synthesis boundary with a screen-specific fallback | Served behavior and editorial quality review |
| Overview, alerts, and setup | Selected messages simplified | Complete dynamic-message and visual review |
| Browser JavaScript | Files discovered in the inventory | Extract dynamic messages and check their completed forms |
| CLI, API errors, and desktop | Files discovered in the inventory | Extract owned explanations and migrate by feature |
| English documentation | Files discovered in the inventory | Editorial migration and documentation lint integration |
| Pro explanations | Separate repository | Inventory, migration, and verification |
| Cloud explanations and email | Separate repository | Inventory, migration, and hosted verification |
| Website explanations | Separate repository | Inventory, migration, and served-page verification |
| Alerts and scheduled briefs | Shared instructions and validation; original alert or result table retained | Served behavior and editorial review |
| Advisor answers | Both transports checked; known token usage retained | Served behavior and editorial review |
| Chart explanations | Titles and descriptions checked after JSON parsing; SQL retained | Served behavior and editorial review |
| Evaluation reasons | Classic and DeepEval reasons checked; scores and verdicts retained | Served behavior and editorial review |
| Other generated paths | Pending source review | Complete the inventory across repositories |

## Completion requirements

- Every in-scope source has an owner and a reviewed text inventory.
- Mechanical findings are resolved or explicitly classified as source evidence or extraction artifacts.
- New messages cannot bypass the applicable checks.
- Every generated path has shared instructions, validation, and an assessed fallback.
- Values, units, uncertainty, commands, and identifiers retain their meaning.
- An STE-qualified reviewer has assessed the applicable writing rules and dictionary use.
- Local and hosted artifacts have been released and verified, with evidence recorded per surface.

## Current delivery

Requirements: [STE100_REQUIREMENTS.md](STE100_REQUIREMENTS.md).
Design: [STE100_BLUEPRINT.md](STE100_BLUEPRINT.md).
Writing guide: [STE100_WRITING.md](STE100_WRITING.md).

These records were written before implementation and published to Software Factory on 2026-10-02.
Requirement: `a5f5d75b-43b5-4f55-ab9a-393865c606ca` (version 3).
Blueprint: `3d07dd70-06dd-4a2e-b4bd-122ee55ac751` (version 3). The expanded generation design is recorded locally. Publishing that revision failed because the Factory keychain credential was unavailable.
Draft delivery: [PR #6248](https://github.com/vivekchand/clawmetry/pull/6248).
No production release or whole-product compliance claim is recorded here.

## Verification recorded on 2026-10-02

Base revision: `19cb235ae5e8a14e44f5efe871d79ff9c0dc530f`.

- The three new test modules pass: 57 tests.
- Restoring the base insight implementation makes all 12 generated-prose rejection tests fail. Restoring this change makes them pass.
- The corpus check covers 2,670 extracted messages in 44 sources. Mechanical findings decreased from 109 to zero.
- The inventory lists 461 source candidates awaiting extraction or review. These are not counted as checked messages.
- Wrapped sentences cannot bypass the sentence limit. CSS that was incorrectly catalogued as prose is now a code literal.
- All template translation keys exist in the English catalog. The language suites contain 57 tests; the translation suites contain 119 tests.
- The revised setup template renders with no mechanical findings. Its text describes the actual control boundary.
- The built wheel contains byte-identical copies of all 61 changed runtime and asset files.
- Python 3.9 syntax, JavaScript syntax, and CI test-file coverage pass. Nine implemented STE criteria have explicit test declarations in the Factory manifest. The policy, editorial, and full-rollout criteria remain pending.
- Existing insight tests pass with the new language tests: 75 tests. Four free-tier cases previously inherited the developer's installed Pro license. Their fixture now supplies the intended free tier.
- The Activity route uses the same validated synthesis and an appropriate fallback. Its missing configuration import is corrected. An unknown relay model stays unknown.
- The six insight outcome-template tests pass against temporary DuckDB stores.
- Existing JavaScript tests pass: 232 assertions. The pre-existing Show/Hide handler quoting defect is corrected with the shared attribute-string encoder.
- Browser security policy rejected the local file preview. CI run `36990448237` captured 74 desktop and mobile views, all with HTTP 200. Desktop Security, Harness, and Quality and mobile Harness were inspected. The changed help text fits; unmigrated dynamic copy remains visible. Onboarding and hosted verification remain pending.
- The combined language, generated-boundary, insight, classic-judge, and DeepEval test run passes 141 tests. The optional real DeepEval import test is skipped; the live paid judge test is deselected. Model calls and notification delivery are mocked.
- Existing brief and Dives telemetry tests pass: 42 tests. Existing chart and Advisor auth suites pass 201 tests; one Self-Evolve entitlement assertion fails with HTTP 402 on both the base and changed Advisor implementation.
- The expanded wheel contains byte-identical copies of all 68 changed runtime and asset files. Fourteen implemented STE criteria now have test declarations.
- CI caught the missing local dashboard address in Security help. The address is restored, and all 35 hosted Security and guard-inventory checks pass locally.

These results establish the implemented subset and regression behavior. They do not establish whole-product compliance or a production release.
