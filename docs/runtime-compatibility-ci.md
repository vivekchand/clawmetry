# Cross-platform runtime compatibility

`runtime-compatibility.yml` verifies the exact candidate of `clawmetry-pro`
against this OSS checkout on standard Linux, Windows and macOS runners. Runtime
IDs come from `SUPPORTED_RUNTIMES.txt`; the workflow does not carry another list.
It currently runs adapter unit and recorded-fixture suites, not live provider
turns. The existing private live-conformance workflow remains in place.

## Selection and reuse

Known adapter, adapter-test and runtime-fixture edits select their runtime on
all three operating systems. Shared code, dependencies, new runtime names and
unknown paths select the entire catalogue. Only README.md, CHANGELOG.md and
.gitignore are explicitly cosmetic. An unavailable comparison base selects all
runtimes. Missing suites and entirely skipped suites fail rather than claim
coverage. Each runtime has a five-minute execution limit. Main pushes watch all package Python modules,
adapter suite families and runtime fixtures, so a new shared helper cannot
bypass the conservative full-catalogue fallback. UI-only assets do not trigger
this adapter matrix.

Suite discovery recognizes `test_<runtime>_adapter*.py`,
`test_adapter_<runtime>.py` and `test_<runtime>_runtime_adapter.py` in both
test roots. OpenClaw additionally runs OSS `test_openclaw_list_events.py` and
`test_openclaw_replay_events.py`, matching its existing suite family. Candidate
preparation checks installed-wheel metadata, the extension entry point and
import location before testing. Private JUnit input is size-bounded, DTDs are
rejected across XML encodings, and malformed reports fail verification.

Pro and OSS suites execute in separate pytest processes with their own
working directories and conftests, within one five-minute runtime deadline.
Paid catalogue entries require a Pro-side suite. Every group must execute at
least one case, and stale JUnit is removed before execution. The exact built
Pro wheel is force-reinstalled even when its package version is unchanged. Private checkouts disable Git
newline conversion and allow long Windows fixture paths through transient
configuration, preserving the indexed recorded data on every platform.

Successful results are keyed by both repositories' indexed file contents, the
selected runtimes, actual hosted OS image/platform/architecture and exact Python
patch version. Image and interpreter updates invalidate reuse. A partial success
cannot satisfy a full-catalogue run. Only a success marker is cached. Manual
dispatch accepts an exact `pro_sha` (or resolves `main` once) and `force: true`
bypasses result reuse for a fresh dependency/platform check, including reruns
of that forced workflow attempt.

## Authentication and confidentiality

The public workflow requires `PRO_REPO_READ_TOKEN` with Contents read on the
private Pro repository, and, for direct cross-repository dispatch, `PRO_STATUS_TOKEN` with Commit
statuses write there to report results. The local bridge route needs only the
read credential in public CI; the Mac reports the final private status. Existing `CLOUD_REPO_PAT` is a migration fallback;
dedicated fine-grained credentials are preferable. Provider keys are not used.

Private fetch output, build output, wheel files, fixtures and pytest output stay
on the ephemeral runner. Git authentication is transient environment
configuration, never persisted in the checkout. The wheel is installed and the
adjacent source package is moved aside before testing. Raw JUnit is parsed
privately. Public output contains runtime IDs and passed/failed/timed-out/
missing-coverage/unverified statuses only. The selection artifact contains IDs,
hashes and OS labels, expires after one day, and contains no private files.

Pull requests to this public workflow run only the secret-free orchestration
guards. Candidate execution uses the trusted default-branch workflow through
manual dispatch, relevant main pushes or `pro-runtime-compatibility` repository
dispatch. Never use pull_request_target to execute public PR code with tokens.

## Pro dispatch contract

The private dispatcher sends `pro_sha`, `base_sha` and the PR number to the
public repository. For PRs the candidate is the PR head SHA, not GitHub's
synthetic merge SHA. The public workflow resolves the candidate once and posts
the final `OSS runtime compatibility` status to that exact private commit.
Superseded candidates of the same Pro PR share a concurrency group.

Install the public workflow first and prove a manual three-OS run. Then install
`python3 scripts/ci/local_runtime_dispatch.py --install` from the reviewed
checkout on the owner's Mac. It copies the consumer outside the checkout to
`~/Library/Application Support/ClawMetryCI/` and registers a once-per-minute
LaunchAgent. The directory and state file are private to the owner. Existing
`gh` authentication stays on the Mac; no new personal CI token is needed.

Set private `OSS_RUNTIME_CI_LOCAL_BRIDGE=true` after installing the consumer.
The private producer's own workflow token writes an exact-candidate pending
request. The consumer reads only the fixed producer workflow's successful
same-repository runs and trusted status markers, claims each request with a
nonce, and dispatches only the fixed OSS workflow. It does not execute candidate
code. The public run name carries the nonce. Atomic local state and receipt
reconciliation prevent immediate duplicate delivery after an uncertain API
response. Failed deliveries retry at five-minute intervals, then report failure.
Newer requests supersede old markers without an old result overwriting them.
The Mac must be awake and the owner logged in; offline requests stay pending.

Request and claimed markers bind the producer workflow run ID and attempt.
A different run on the same commit cannot adopt a newer request. The local
cursor tracks each run attempt separately, including producer reruns; legacy
run-only cursors migrate to attempt one.

Verify a real dispatch and exact-SHA callback before setting private
`OSS_RUNTIME_CI_ENABLED=true`. A dedicated `OSS_CI_DISPATCH_TOKEN` with public
Contents write remains an optional direct route, using the public-side private
status credential for its callback. Do not remove existing private coverage
before its replacement passes. This path-filtered check is continuous coverage;
it must not enter an always-required aggregate without a no-impact reporting
path on every PR.

To stop the local consumer, run
`launchctl bootout gui/$(id -u)/com.clawmetry.runtime-dispatch` and remove the
private `OSS_RUNTIME_CI_LOCAL_BRIDGE` variable. Remove `OSS_RUNTIME_CI_ENABLED`
to stop automatic production of requests. Logs and state remain local.

The local consumer rechecks each automatic request against its original private
branch head. It confirms an inactive head on a later poll before marking the
request superseded, so a new producer run cannot lose a race with an older head
snapshot. Explicit manual comparisons remain available for historical candidates.
Retrying a public run refreshes pending and the new conclusion while that run
still owns the source status. A newer request or different public run on the
same source SHA keeps ownership of its own status.
