# Guard security boundaries

Guard uses distinct evidence for observation, approval and containment.
A recorded call does not prove execution. An approval does not prove that the runtime applied its decision.

## Approval identity

A reused approval binds the runtime, session, exact tool, complete JSON arguments, working directory and invocation identity.
A different file body, recipient, environment or target requires another decision.
Object key order does not change the identity. Array order and JSON value types remain significant.
Older command-only grants are not converted into complete grants.

Generated permanent grants use the same complete action contract across sessions.
An operator can still write an explicit broad policy. That choice is separate from remembering one reviewed action.
Older clients must not receive bound policies as broad preview expressions.

When no policy applies, ClawMetry leaves native runtime permissions in control.
A monitor policy does not grant permission to run a tool.
A known pending protected invocation is denied if its approval cannot be verified before the runtime deadline.
Native question and permission dialogs retain their own human review path.

The daemon can retain fresh, scoped policy evidence for an initial service outage.
That evidence expires after 60 seconds. Missing, stale or unavailable authority falls back to native permissions.
It must not be described as verified ClawMetry prevention.

## Committed security evidence

The daemon uses the existing committed event-change journal.
It follows durable positions rather than source timestamps or the machine clock.
Completed sessions remain eligible for security inspection.
A journal retention gap stays visible. It does not establish a clean inspection.
Newer committed records have a bounded priority lane while complete historical
backfill continues. Startup can hand priority to the retained tail; the FIFO
cursor still owns every skipped interval. Both positions commit together.
Guard reports pending backfill separately. Page and CPU budgets still apply.

Each finding references only the source steps that support it.
Unrelated later activity cannot make an old credential read current.
Unknown command syntax produces an inspection limitation, not an accusation.
Coverage-only findings cannot trigger process-control actions, including later escalation steps.

The existing store writer owns findings, cursor state and notification references.
Progress and its coverage state commit together.
Notification delivery uses a separate durable queue.
A slow network must not hold the shared policy claim and dispatch lock.
The service bounds each page and limits its CPU duty at sustained load.

## Paths and priority

One declared mutation outside a known workspace can produce a finding.
Path comparisons use lexical POSIX or Windows components, including drive and UNC boundaries.
A shared string prefix is not containment.
These checks do not resolve symlinks, shell expansion or filesystem permissions.

Critical security evidence takes priority over model spend.
Operational findings retain cost ordering.
Model cost does not increase the security severity of a credential or privilege finding.

## Independent protection

The Guard disclosure separates recorded activity, hook configuration, review decisions and available process controls.
It also states whether native isolation or independent code-check evidence is available.
A saved configuration is not a verified sandbox.
Exported telemetry cannot inherit local process controls or local hook claims.

A program can access files or networks without naming them in its tool arguments.
Use native runtime isolation and endpoint controls to enforce those boundaries across subprocesses.
The model API proxy does not enforce arbitrary process network traffic.

Use independent code and dependency checks before releasing generated changes.
The existing PR provenance report can attach agent evidence to external scanner SARIF results.
A one-line authorization defect does not need a large file footprint.
No command-pattern detector can establish that arbitrary generated code is safe.

## Verification

The repeatable local drill is `scripts/security_runtime_drill.py`.
It runs a real agent turn with two harmless temporary targets.
The protected target must stay absent. The ordinary target must be created.
A real approval record must contain the denial.
Runtime authentication is required. The drill uses isolated configuration and a private temporary store.

Unit fixtures establish local contracts only.
Release verification must also inspect the published wheel, hosted package pin, encrypted snapshot and served Guard view.
