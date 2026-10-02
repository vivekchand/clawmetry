# Clear English explanations

## Overview

People use ClawMetry to understand what their agents did and what needs attention.
Long sentences, unexplained terms, and inconsistent messages make that task harder.
This change applies ASD-STE100 Issue 9 as the reference for English explanations that ClawMetry writes.
It covers the dashboard, CLI, errors, alerts, generated reports, help, and public documentation across the product repositories.

The English catalog already contains shared messages. Templates and source files also contain messages outside that catalog.
Weekly insights currently request short output but do not check the resulting language.
The migration must cover those separate paths and report unfinished work explicitly.

## Terminology

- **Owned text:** an explanation written by ClawMetry, including generated explanations.
- **Source evidence:** agent messages, logs, user input, commands, identifiers, and quoted evidence.
- **Mechanical check:** a test for a defined subset of writing rules. It does not establish full STE compliance.
- **Reviewed text:** text assessed for meaning, grammar, terminology, and the applicable rules by a reviewer familiar with the standard.

## Requirements

### REQ-STE-001: Consistent explanations

As an agent operator, I want clear explanations so that I can understand the state and choose the next action.

- AC-STE-001.1: When ClawMetry writes English explanations, the writing policy shall identify the standard, scope, controlled terminology, and review procedure.
- AC-STE-001.2: When an explanation contains a technical term, the project glossary shall give its meaning and permitted use.
- AC-STE-001.3: When wording changes, the system shall preserve commands, identifiers, values, uncertainty, and source evidence.

### REQ-STE-002: Prevent language regressions

As a contributor, I want checks during review so that new text cannot silently bypass the writing policy.

- AC-STE-002.1: When a checked message violates an implemented rule, the checker shall report its source and the rule.
- AC-STE-002.2: When a checked message changes or is added, CI shall reject new mechanical violations.
- AC-STE-002.3: When existing violations are removed, the baseline shall decrease. New entries shall not be accepted as debt during a pull request.
- AC-STE-002.4: When the inventory runs, it shall distinguish checked text, source candidates awaiting extraction, and surfaces in other repositories.
- AC-STE-002.5: When a check passes, its report shall identify its limits and shall not claim full compliance.

### REQ-STE-003: Generated explanations

As an operator, I want generated explanations to follow the same policy without extra latency or disclosure of my data.

- AC-STE-003.1: When weekly insights request generated prose, both synthesis paths shall use the same English writing instructions.
- AC-STE-003.2: When generated prose fails the implemented checks or is empty, the system shall show a fixed fallback and retain the underlying result rows.
- AC-STE-003.3: When a generated response is rejected, its known token usage shall still contribute to the estimated cost.
- AC-STE-003.4: When language validation runs, it shall require no network call, additional model call, poller, or user configuration.

### REQ-STE-004: Complete migration

As a maintainer, I want evidence for each surface so that unfinished coverage remains visible.

- AC-STE-004.1: When a screen is migrated, its initial HTML, dynamic messages, accessibility text, and English catalog shall be assessed together.
- AC-STE-004.2: Before the rollout is declared complete, all in-scope repositories and generated paths shall be reviewed, released, and verified in their served artifacts.
- AC-STE-004.3: Translations shall retain separate language checks. Source evidence shall remain distinguishable from owned explanations.

## Non-goals and alternatives

This work does not rewrite observed agent output or enforce writing rules on other agents.
It does not change API field names, commands, measurements, or control permissions.
It does not add a build step or a language service to the installed app.

A prompt-only approach cannot check the text that users receive.
A readability score does not check word meaning or the STE dictionary.
A general spell checker does not distinguish technical terms from ordinary vocabulary.
Vale is a useful editorial tool, but it does not establish full STE compliance either.
Use small offline checks for the first release and keep semantic review explicit.

## Risks and reversal

Rewriting can change meaning or hide uncertainty. Review the facts against the previous message and the producing code.
Automated extraction can miss concatenated or generated text. Record those sources as pending instead of reporting them as checked.
A broad word replacement can corrupt source evidence. Never run automatic replacement on agent content or arbitrary source files.
A rejected generated summary can be less informative. Keep the result rows and state that the summary is unavailable.
The changes require no data migration. A code revert restores the previous messages and checker behavior.

## Delivery evidence

Track implementation and review in `docs/STE100_COVERAGE.md`.
The initial delivery is a stage of the complete migration, not evidence that every explanation complies.

## References

- [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
- [ASD guidance on tools](https://www.asd-ste100.org/STEsoftware.html)
- [Vale documentation](https://docs.vale.sh/)
