# English writing policy

Use ASD-STE100 Issue 9 as the reference for English explanations written by ClawMetry.
Read the [official standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) for its full rules and dictionary.
The project checker covers a mechanical subset. A passing result does not establish full compliance.

## Scope

Apply this policy to UI text, tooltips, accessibility text, errors, alerts, CLI messages, reports, and technical documentation.
Apply it to both fixed and generated explanations.
Use the same policy in the cloud, Pro, and website repositories.

Keep agent transcripts, user input, logs, code, commands, identifiers, and quoted evidence unchanged.
Write any explanation of that evidence separately.
Translations need review in their own language. STE is an English standard.

## Write the explanation

1. State what happened or what the measurement means.
2. State the effect when the effect is known.
3. Give the next action when the user can take one.
4. State uncertainty when the evidence is incomplete.

Use short sentences and consistent terms. Prefer active voice.
Use one instruction in each sentence, except where the standard permits simultaneous actions.
Put a necessary condition before its instruction.
Use no contractions, idioms, semicolons, or em dashes in owned prose.
Use complete words rather than removing articles to shorten a sentence.

The standard permits 20 words in a procedural sentence and 25 in a descriptive sentence.
Apply its word-count rules to identifiers, numbers, units, parentheses, proper names, and displayed labels.
Text in parentheses counts as one word in the outer sentence. Check its contents as a separate sentence too (Rule 8.5).
The project checker uses a conservative count for supported forms.
It cannot identify every proper name or determine the grammatical role of a word.
Unclassified strings use the stricter limit until their type is recorded in `docs/english_message_types.json`.

Use the [project glossary](../clawmetry/data/english_terms.json) to keep technical terms consistent.
It records domain meanings and editorial preferences. It does not replace the ASD dictionary.
Review new technical nouns and verbs against the categories in the standard.
Do not add a term merely to suppress a finding.

For example, write:

> ClawMetry cannot reach the collector on this machine. Some screens may be incomplete. ClawMetry will try the connection again.

Do not claim that data is safe, an agent stopped, or an action succeeded unless the available evidence establishes it.
Keep estimated costs distinct from confirmed charges. Keep missing values distinct from zero.

## Review a change

Run the mechanical check:

```sh
python3 scripts/check_english.py
python3 scripts/check_english.py --inventory
```

Resolve each new finding. When existing findings are removed, reduce the baseline:

```sh
python3 scripts/check_english.py --update-baseline
```

This command cannot add new debt. CI also compares the baseline with the pull request base.
An exception is tied to the exact text and its source. It is not a permanent permission for a key or file.

Review the complete rendered message, including inserted values.
Verify terminology, approved meanings, grammatical roles, and the facts against the standard and the data-producing code.
Use an STE-qualified reviewer before asserting full compliance.
Keep the same meaning in the English catalog and the initial HTML or JavaScript fallback.

Mechanical checks do not cover every source. Read [the coverage record](STE100_COVERAGE.md) before making a coverage claim.

## Generated text

Use the shared instructions in `clawmetry/english.py` at generation boundaries.
Validate the result before displaying or storing the explanation.
Use fixed fallbacks when validation fails. Retain the source results and known token usage.
Do not rewrite observed agent text, send it to an extra service, or retry generation just to satisfy a style check.

Current integrations cover weekly insights, Activity explanations, alerts, Advisor, charts, and evaluation reasons.
Other generated paths remain pending until separately integrated and verified.
The fallback and its result count require review just like any other message.

## Claims and release

Use “STE-aligned” while migration or editorial review is incomplete.
Do not describe a checker, an AI model, or this product as ASD-certified.
[ASD guidance](https://www.asd-ste100.org/STEsoftware.html) explains the limits of checking tools.

Follow `FLYWHEEL.md` for release and live verification.
Check the served text on local and hosted surfaces, including failure states and missing data.
Record evidence per surface before declaring the migration complete.
