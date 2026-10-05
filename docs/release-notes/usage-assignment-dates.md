# Assignment dates on the Usage tab

These notes describe #6353, #6339 and #6360. Other changes carried by this release are documented under Unreleased in CHANGELOG.md.

## What changes

- **An assignment made from the Usage tab can have a start date and an end date (#6353).** The assignment form in the Cost by Project card has two optional date fields. With a start date, the assignment covers sessions that started on or after that day. With an end date, it covers sessions that started before that day. With neither, it covers all sessions, as before. The form refuses an end date that is not later than the start date. Each assignment in the card shows its period.
- **A workflow node in the replay lists its error and the model and tool calls made for it (#6339).** In the workflow graph of a replayed session, a node that made model or tool calls shows their count. Opening the node lists those calls and, when the node failed, its error.
- **Other branches of a Pi conversation open from the replay (#6360).** When a Pi session has stored branches, the branch notice in the replay lists them as buttons with the first prompt and the number of entries only that branch has. A button loads that branch, with the count of entries it shares with the session and a button to go back. If a branch does not load, a message appears above the session replay, which stays.

## Verification and limits

- #6353: 2 new tests in `tests/test_project_attribution_budgets.py` (42 in the file). Not checked in a running dashboard.
- #6339: 12 new checks in `tests/replay_tree.test.mjs`. The replay details are hidden on the hosted dashboard, so this is local only.
- #6360: 13 new checks in `tests/replay_tree.test.mjs` (81 in the file) and 3 new tests in `tests/test_replay_tree_endpoint.py` (21 in the file). It shows nothing until a clawmetry-pro version with the Pi branch streams (0.7.51 or later) is installed. Local only, for the same reason.
- A date is sent as midnight on the clock of the machine that runs ClawMetry. The period is tested against the start of a session, so a session that runs across the start date stays on the side where it began.
- Assigning a single session and removing an assignment are still API only.
- The hosted dashboard does not show project assignments, so this is local only.

No change here adds an HTTP route (#6360 adds one field, `branches.stored`, to the `/api/replay-tree` response), so the cloud pin needs no new route-policy entry. Package versioning and tagging remain owned by the release workflow.
