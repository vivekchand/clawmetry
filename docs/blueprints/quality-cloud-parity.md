# Feature Blueprint: Quality Grade Cloud Parity

> Local mirror of the Software Factory Feature Blueprint of the same name.
> The hosted record is the system of record; this file exists so drift-bot,
> PR review, and headless agents can read the same spec without a factory
> login. When the hosted blueprint is created or updated, keep this file in
> step (FLYWHEEL 1f).

## Feature Summary

A hosted ClawMetry user viewing the Quality tab should see the same grade
that the local dashboard shows for their machine. Before this feature, the
hosted container answered quality requests from its own DuckDB — which is
present but empty — and reported a working machine as having produced nothing.
The grade now travels in the encrypted snapshot the daemon emits on each
sync cycle, and the hosted process refuses to answer from its own store.

The root cause was two coupled faults: the quality grade never had a snapshot
slice, so the cloud had nothing to render; and the hosted endpoint fell back
to reading its own empty store rather than returning an honest "not available"
response. Both faults produced the same screen — "Nothing to grade yet" — for
opposite reasons.

## Component Blueprint Composition

This feature extends two existing components without redefining them.

`#CloudSnapshotSync` in `clawmetry/sync.py` bakes the encrypted snapshot the
hosted dashboard renders. Per the cloud-parity hard gate, any data surface
that a hosted trial user can click must be served by a `cm-cloud-*`
interceptor over a snapshot slice, or must show an honest locked state. The
Quality tab inherited that obligation but had no slice; this feature adds one.

`#QualityRoutes` in `routes/quality.py` serves `GET /api/quality/report-card`
and owns the composition logic for the report card payload. This feature
extracts the composition into a shared callable (`compose_report_card`) so
both the request handler and the daemon build identical payloads from the same
code path, eliminating the divergence that produced a different answer on
screen depending on where the request was served.

## Feature-Specific Components

```component
name: QualitySnapshotBuilder
container: ClawMetry Sync Daemon
responsibilities:
  - Reading the node's quality sessions exactly three times per snapshot cycle:
    the current window, the prior window, and a 30-day calibration history
  - Calling compose_report_card once for the node-wide card and once per
    runtime seen in either the current window or the 30-day history
  - Hoisting calibration thresholds to the slice root rather than embedding
    them in each per-runtime card
  - Returning an empty dict {} on any exception so the snapshot never fails
    to build over one optional slice
```

`#QualitySnapshotBuilder` is implemented as `_build_quality_snapshot()` in
`clawmetry/sync.py`, called from `sync_system_snapshot()`. It imports
`compose_report_card` from `routes.quality` at call time (late import, same
pattern as the other snapshot builders that use route-layer helpers).

The three-read constraint is load-bearing: the daemon runs this builder on
every snapshot cycle, and emitting one card per runtime must not multiply the
store reads proportionally. Rows are grouped in Python after the three fetches;
no additional queries are made regardless of how many runtimes are present.

The quiet-runtime rule is also load-bearing: a runtime that ran sessions in
the last 30 days but was quiet this week must still appear in `byRuntime` with
an honest "nothing to grade this week" card. Without it, the hosted tab would
fall back to the node-wide card when a runtime filter was selected and show
another runtime's grade under the wrong runtime's name.

## System Contracts

### Key Contracts

The `quality` snapshot slice has the shape
`{window_hours, all, byRuntime, thresholds}`. `all` is the node-wide report
card. `byRuntime` is a dict keyed by runtime identifier; each value is the
report card for that runtime and never contains sessions belonging to a
different runtime. `thresholds` is the calibration map, hoisted once to the
slice root and absent from each per-runtime card (it is byte-identical across
cards and carrying it inline multiplied the slice size by the runtime count).

`compose_report_card` in `routes/quality.py` is the single canonical builder
for the report card payload. Both the sync daemon (`_build_quality_snapshot`)
and the request handler (`quality_report_card`) call it. No other code path
may build a report card payload; duplicating the composition logic is the
drift pattern this feature closes.

The store is read exactly three times per `_build_quality_snapshot()` call:
once for the current window (the `window_hours` parameter, default 168h),
once for the prior window of the same length (for week-over-week comparison),
and once for the 30-day calibration history. Emitting one card per runtime
must not add queries: rows are split in Python, and `_assess_rows` is called
once over the node's full window rows with its assessment map reused across
every per-runtime card.

Every runtime that appears in either the current window rows or the 30-day
history rows gets its own entry in `byRuntime`. A runtime that was quiet this
week but active in the last 30 days gets a card stating it has nothing to
grade this week, in its own name. Absence from the current window is not
grounds for omission from `byRuntime`.

The `quality` slice returns `{}` on any exception and must never propagate an
exception to `sync_system_snapshot`. A misconfiguration, an import failure, or
a store error in the quality builder must not prevent the rest of the snapshot
from being emitted.

### Integration Contracts

`GET /api/quality/report-card` when served by the hosted dashboard
(`CLAWMETRY_CLOUD=1`) always returns `store_available: false` with a message
explaining that the grade lives on the user's machine. It never reads the
hosted container's DuckDB for this response. The distinction matters because
an empty store answers queries successfully with zero rows, which produces
"Nothing to grade yet" — a false statement about a machine that is grading
normally. `store_available: false` is an honest "I cannot see your machine"
and must not say "Nothing to grade".

`GET /api/quality/report-card` when served by a local dashboard
(`CLAWMETRY_CLOUD` unset) reads from the daemon query path and returns
`store_available: true` when the store answers (even with zero rows).
An empty local store is a true statement that this machine has no graded runs
this week; the response may say "Nothing to grade yet" in that case.

An unreachable store — `_store_via_daemon_or_direct` returning `None` rather
than `[]` — is not an empty grade. The local handler returns
`store_available: false` in that case, using the same message as the hosted
process. The distinction between `None` (store unreachable) and `[]` (store
answered with nothing) is preserved through the entire call chain.

### Integration Boundaries

`compose_report_card` is importable from `routes.quality` by both the sync
daemon and the request handler. Its signature takes rows as arguments rather
than a fetch callable: the daemon fetches once and passes sub-lists; the
request handler passes the rows it has already fetched. Neither path is
special-cased inside the function.

The sync daemon never calls `_store_via_daemon_or_direct`. It holds the writer
lock and reads from `local_store.get_store()` directly. The request handler
uses `_store_via_daemon_or_direct` to read through the daemon's query server.
The two paths are separated at the module boundary: `_build_quality_snapshot`
is in `sync.py`; `quality_report_card` is in `routes/quality.py`.

The `CLAWMETRY_CLOUD` environment variable is the only signal the request
handler reads to decide whether to serve from the snapshot or refuse. It is
not threaded through as a function argument; `os.environ.get` is called at
request time.

## Architecture Decision Records

### ADR-001: Extract compose_report_card rather than duplicate composition

Context: the request handler in `routes/quality.py` built the report card
payload inline. The sync daemon needed to build the same payload for the
snapshot. Duplicating the inline logic would have been the path of least
resistance but would have produced two code paths that could diverge silently.

Decision: extract the composition into `compose_report_card`, make it accept
rows as arguments (rather than fetching internally), and have both callers
pass their already-fetched rows to it.

Consequences: one code path for the report card payload. The daemon's
per-runtime cards are provably identical in structure to what the local request
handler would return, because they use the same function. The test
`test_precomputed_assessments_match_the_request_path` pins this.

### ADR-002: CLAWMETRY_CLOUD gates the endpoint; no runtime argument

Context: the hosted dashboard could signal its nature through a function
argument, a constructor parameter, or an environment variable. The environment
variable already existed (`CLAWMETRY_CLOUD`) and was already read by other
parts of the hosted process to suppress local-only behavior.

Decision: read `os.environ.get('CLAWMETRY_CLOUD')` at request time in
`quality_report_card`. No new argument is added to the function.

Consequences: the behavior is consistent with how other endpoints handle the
hosted/local distinction, the environment variable stays the single source of
truth, and tests can toggle the behavior with `monkeypatch.setenv` without
touching function signatures.

### ADR-003: Calibration thresholds hoisted to slice root, not per-card

Context: the first version of the snapshot slice embedded the full calibration
thresholds in every per-runtime card. At 14 runtimes the thresholds were
repeated 14 times; each copy was byte-identical. The thresholds made up
roughly a quarter of the slice by size.

Decision: hoist `thresholds` to the slice root as a single key, and strip it
from every per-runtime card before returning. The cloud interceptor reattaches
it per card when composing the response.

Consequences: slice size scales with the number of runtimes for the `byRuntime`
keys (unavoidable), but not for the calibration data (avoided). The per-card
strip is visible in `_build_quality_snapshot` after the per-runtime loop.
The test `test_calibration_is_carried_once_not_per_card` pins the absence of
`thresholds` in every individual card.
