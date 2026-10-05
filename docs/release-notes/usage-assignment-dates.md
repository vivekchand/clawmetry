# Assignment dates on the Usage tab

These notes describe #6353. Other changes carried by this release are documented under Unreleased in CHANGELOG.md.

## What changes

- **An assignment made from the Usage tab can have a start date and an end date (#6353).** The assignment form in the Cost by Project card has two optional date fields. With a start date, the assignment covers sessions that started on or after that day. With an end date, it covers sessions that started before that day. With neither, it covers all sessions, as before. The form refuses an end date that is not later than the start date. Each assignment in the card shows its period.

## Verification and limits

- #6353: 2 new tests in `tests/test_project_attribution_budgets.py` (42 in the file). Not checked in a running dashboard.
- A date is sent as midnight on the clock of the machine that runs ClawMetry. The period is tested against the start of a session, so a session that runs across the start date stays on the side where it began.
- Assigning a single session and removing an assignment are still API only.
- The hosted dashboard does not show project assignments, so this is local only.

The change adds no HTTP route, so the cloud pin needs no new route-policy entry. Package versioning and tagging remain owned by the release workflow.
