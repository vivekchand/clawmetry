# Process search and live measurements verification

The Node view searches all retained processes by name, PID and recognized ClawMetry role before pagination. A separate section shows identified collector/dashboard processes with measured CPU and resident memory. Raw command lines are used transiently for exact entry-point recognition and are never serialized.

One daemon writer worker replaces ingest-loop collection. Full observations remain at 30 seconds; process/resource frames accelerate to two seconds while a bounded viewer lease is active. Request handlers read persisted frames through authenticated daemon RPC. CPU rates retain PID/start-time identity and comparison-gap checks. The browser's one active-view loop preserves search and stops on hidden/off-tab changes.

Cloud frames remain AES-GCM encrypted through the existing authenticated cache. Owned cache reads renew presence for at most 40 seconds; existing wake responses carry only that bounded observation hint independently of slow ingest. Publication has one unsent frame and never blocks sampling. No generic command executes on the wake worker.

## Verification evidence

- Initial focused collector, store, lifecycle and browser suite: 117 passed, including actual process/listener checks and 320/1280 viewport tests.
- Regression proof against the original source: 17 new collector cases and the JS pagination assertion failed; restored candidate passed.
- Live cadence and startup/stop guards cover blocked ingest, read-only proxy rejection, lease expiry, expensive-source exclusion, private RPC authentication, delayed/snapshot states and search preservation.
- Cloud Node/relay/wake/inline-JS suite: 232 passed, including exact owner/node binding, lease expiry and no repeated full-snapshot read.
- Actual installed local frames advanced by 1.941 and 1.890 seconds. The running browser showed measured collector/dashboard CPU, changing resident memory and CPU bars, with ClawMetry search preserved and Live, every 2 seconds visible.
- English mechanical checks, acceptance traceability, CI test listing and module map passed. Acceptance coverage is 440/508 with the pre-existing 68 uncovered unchanged.

## Release state

Public feature PR: https://github.com/vivekchand/clawmetry/pull/6519
Paired cloud PR: https://github.com/vivekchand/clawmetry-cloud/pull/2661

Release checks are in progress. The feature is not yet publicly released or hosted-live verified. After current-head CI passes, follow the separate release PR, verified published wheel, cloud pin/deploy, encrypted-frame and hosted-browser checks before claiming completion.

## Drift check evidence

The first live-cadence drift verdict cited older frontend behavior. Current renderInventory delegates to renderProcesses and renderClawmetry; those functions implement retained-row filtering/pagination and the dedicated self-usage section. schedule uses a 2000ms live interval, load requests live=1, and the old ten/fifteen second period is an explicit older-collector fallback. The hosted blueprint now names these functions and contracts for review. No check is bypassed.

The remaining drift finding identified the automatically created feature blueprint as a placeholder. It is now populated with the actual component composition, contracts, verification limits and three ADRs, verified by rereading the hosted record. The local blueprint mirrors that feature record rather than duplicating the shared capability document.
