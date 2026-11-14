# Product records and independent review

Write the requirement before implementing a product change. State the problem,
who is affected, acceptance criteria, non-goals, alternatives, risks and rollback.
Describe the architecture and contracts in a linked blueprint when needed.
An independent reviewer reads those records, the exact candidate diff and its
test evidence before approving the change. A citation check cannot perform that
review.

## Where records live

Use `docs/product-records/<name>.md` for a public record in this repository.
Internal requirements, architecture, commercial decisions and cross-repository
work belong in the private `clawmetry-cloud/docs/product-records/` directory.
Use private GitHub issues for actionable work orders and their acceptance tests.
The private issue tracker remains the backlog if a Projects board is unavailable.
Do not copy private records or their contents into public pull requests.

Preserve requirement and acceptance-criterion IDs when records move or change.
Original Factory document IDs and URLs remain in the private migration index.
Historical links are accepted for compatibility, but new work needs no Factory
account, API key or paid review service.

## Cite a record

For a local document, the PR body contains this line (the file must exist and
contain text):

```text
Product record: docs/product-records/session-controls.md
```

For private or cross-repository context, link its GitHub issue or versioned file:

```text
Product record: https://github.com/vivekchand/clawmetry-cloud/issues/123
Product record: https://github.com/vivekchand/clawmetry-cloud/blob/main/docs/product-records/requirements/<document-id>.md
```

The public CI token cannot read private records. The reviewer must open the
record and verify its criteria; CI only checks that a citation has the expected
form. A URL alone is not evidence that the requirement is complete.

A change that needs no product record can retain an explicit `No-PRD: <reason>`
line. Documentation, test, workflow and dependency-only changes remain exempt.
Do not use the exemption as the default for product changes.

## Review one candidate

1. Read the requirement and linked blueprints before coding. Check related open
   PRs so parallel changes do not create contradictory models or contracts.
2. Implement the smallest change that satisfies the criteria. Update the records
   and acceptance-test mapping together when behavior changes.
3. Give a fresh reviewer context the exact head commit, changed paths, relevant
   records, tests and verification evidence. Reuse an existing agent account;
   review on demand instead of starting another paid review for every push.
4. Record the reviewed SHA, findings, resolutions and verdict in the private work
   order or PR review. A new code/contract change needs review of that delta.
   Unchanged evidence may be reused for the same candidate.
5. Fix blocking findings and pass all functional, security, package and deployment
   checks. Never fabricate a status from a retired reviewer. The required E2E
   aggregate includes the portable product-record check.

## Migrated work orders

Keep original WO numbers, priorities, statuses, linked records, parent/child
relationships, comments and PR evidence. Completed records can stay in the
private archive; actionable work belongs in private issues. A work-order CLI
must read those issues or local records rather than call the retired service.

The local Software Factory skill's requirements, blueprint and execution
templates remain useful without its hosted service. Requirements and review
discipline are mandatory; a particular vendor is not.
