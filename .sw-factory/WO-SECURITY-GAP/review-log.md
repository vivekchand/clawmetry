<!--lint disable strong-marker-->

# Review Log: WO-SECURITY-GAP

**Work Order:** WO-SECURITY-GAP — Guard security boundaries and timely incident handling
**Initialized At (UTC):** 2026-10-25T23:32:57Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Continuous security review, round 1

Reviewer: delegated protection-coverage agent. Base: `9425e2dd90`; scope is the incremental security service, store mixin, signature extraction, incident evidence/lifecycle extensions, commit wakeup and daemon wiring.

### Requirements alignment

- **Blocking B1, REQ-GOV-SBG-002:** notification delivery runs synchronously before policy containment. Configured network channels can each wait ten seconds. Containment and later sessions wait behind those requests.
- **Blocking B2, REQ-GOV-SBG-002:** `query_security_session` applies `json.loads` to the arbitrary-string fallback of `_from_blob`. Invalid metadata causes permanent global cursor retries rather than a bounded fallback.
- **Blocking B3, REQ-GOV-SBG-002:** incremental `_policy` creates a new duration memo on each call. A five-minute active incident produces `bad_for_seconds=0.0`; duration-gated policies cannot match through this path.
- **Blocking B4, REQ-GOV-SBG-002/004:** generic security evidence attachment includes harmless tail calls. A key read dated 2020 followed by a current harmless command has both references, so stale security evidence becomes an active episode and can trigger policy action.

### Blueprint alignment

- **Blocking B5, exact scope:** episodes bind node/runtime/session, but the compatibility `loop_signals` key omits node/runtime. Two nodes with a colliding session and kind overwrite the projected finding. Guard must select findings by confirmed node/runtime scope.
- **Blocking B6, threading:** baseline and policy readers use the shared DuckDB connection directly. Their new security-thread caller races main-thread reads/writes; swallowed failures can silently erase baseline or policy evidence. Use the existing per-thread read path.
- **Blocking B7, durable action latch:** main and security threads can enter check-then-upsert policy handling concurrently and both dispatch one action. The shared path needs serialization or an atomic durable claim.

### Architecture and conventions

The pure signature extraction, indexed scoped reads, daemon-owned writer, bounded page/window limits, post-commit wakeup and explicit observation labels follow existing boundaries. The planned replacement of timestamp/id progress with the existing committed event-change journal must be reviewed after implementation; it is needed for payload updates and clock/id-order races.

### Tests and build health

Safe direct review probes reproduced notification-before-containment order, zero duration for a five-minute episode, malformed-metadata `JSONDecodeError`, and harmless-tail evidence refreshing an old credential event. These probes only called Python functions with stubbed actions and harmless synthetic arguments. No dangerous command ran. Existing focused tests do not cover those cases yet.

### User-facing verification

Deferred to the parent release verification. This review covers backend evidence and service behavior; neither unit results nor a source review establish live prevention or hosted deployment.

### Security, privacy and data safety

The new signature incident stores rule identifiers and redacted structural evidence rather than raw commands. Approval/entitlement authority is not expanded. Blocking findings B4, B5 and B7 must be resolved before any live enforcement drill.

### Verdict

**CHANGES_REQUESTED.** Seven blocking findings. Recheck the complete changed scope after fixes, including the new journal cursor implementation and regression tests.

### Round 1 supplemental findings and remediation checkpoint

The journal change exposed two additional blockers, now repaired in the working tree: journal receipt order differs from action order because batch journal writes sort event IDs; detector windows now sort source timestamps. Explicit security evidence also needs result/user records; filtering them to tool calls caused prompt injection to stop cursor progress. The current attachment path preserves implicated step kinds.

The delegated reviewer added and ran stale-evidence versus new-upload regressions, and exact-node/runtime Guard projection tests. Related Guard suites passed 171 tests. The focused security/incident/policy/signature/coverage suite passed 142 tests after the recency repairs. These results are a remediation checkpoint, not a release approval.

Remaining blocking recheck items:

- Legacy action signatures still promote quoted inspection commands into automatic security findings. Probes include harmless `grep`/`echo`/`git log` mentions and a printed reverse-shell example. Verify near misses and genuine execution separately.
- Initial journal bootstrap still excludes rows using wall-clock `created_at`; a first-batch clock correction can skip committed evidence before the first cursor exists. Drain retained positions or record an explicit bounded-history gap.
- The main detector caller can still perform synchronous policy alert delivery while holding the new shared policy lock. Ensure network delay cannot block security containment through that caller.

Performance evidence: a temporary isolated DuckDB with 100,000 journal rows required 0.241 seconds wall and 0.261 seconds process CPU for 128 distinct-session window reads. A composite scope index did not materially improve this workload. Measure the complete service under realistic load before claiming the daemon CPU budget.

**Checkpoint verdict: CHANGES_REQUESTED.** Final scope recheck remains pending after these edits settle. No dangerous command, agent control, or external message was executed by the review probes.


## Continuous security review, round 2

Reviewer: delegated protection-coverage agent, independent recheck of the current shared working tree. Scope: committed-journal ingestion, exact scope and replay, detector signature precision and implicated evidence, incident projection, shared policy locking and eligibility, durable notification outbox, and protection evidence rendering.

### Requirements and blueprint alignment

The earlier seven blockers and supplemental bootstrap, evidence-order and synchronous-alert-lock issues are repaired in the reviewed source. The service now reuses the committed journal and retained floor, records an explicit history gap, uses exact node/runtime/session windows, retries failed detector/evidence writes, and queues notifications separately from containment. Unknown command inspection is informational. Source review confirms cursor, inspection status and sticky history-gap metadata now share one transaction.

Two blockers remain in this round:

- **B8, unknown inspection must not actuate:** the new eligibility check tests `policy.action` before the actual escalation rung is selected. A policy whose declared action is alert and whose next due step is kill still produces a kill decision for `inspection_incomplete` with `policy_eligible=False`. The pure-engine reproduction used an alert-to-kill ladder, a persisted first rung, and a synthetic clock; no control executed. Check the selected action and cover both informational kinds and explicitly ineligible evidence through ladders.
- **B9, one durable graph and exact-scope projection:** the periodic detector path reconciles only lifecycle kinds. After the incremental worker persists a scoped security episode/projection, the periodic path also writes its old unscoped `daemon_detect_KIND` signal. A real isolated DuckDB reproduction with recent synthetic credential-read arguments yielded one scoped row after the worker and two rows after the actual periodic pass. Route both producers through the same security episode/projection, with an overlap regression.

### Tests and build

`python3 -m pytest -q -p no:cacheprovider tests/test_security_ingest.py tests/test_security_ingest_recovery.py tests/test_security_evidence_recency.py tests/test_security_scope_and_priority.py tests/test_incident_lifecycle.py tests/test_guard_policy_enforcement.py tests/test_guard_escalation_ladder.py tests/test_protection_evidence.py tests/test_cloud_guard_signals_slices.py` passed **227 tests**. The two direct probes above expose missing integration cases despite that green suite.

### Advisories

- Existing human-alert cooldown is keyed by session and kind. Distinct node/runtime episodes have separate outbox rows, but a colliding session/kind can suppress the second notification. This is an existing alert-latch limitation; exact incident scope must not be inferred from the notification cooldown.
- Existing policy-read and decision-latch failures are caught by the shared policy path. An evidence inspection can therefore complete while containment is unavailable. The node inspection status certifies evidence inspection only, never policy enforcement success.
- Adaptive throttling uses process CPU, which includes other daemon threads. Its budget is conservative under concurrent work; source review does not establish an isolated per-service CPU percentage or a live latency guarantee.

### User-facing and runtime verification

The local and encrypted snapshot payload reuse the same Guard builder; current cloud interception preserves those session objects. Unit tests cover old snapshots, malformed values, escaping, scope filtering and honest unknown states. This review does not establish actual native runtime denial, subprocess isolation, generated-code safety, PyPI publication, cloud deployment, or live UI behavior. Those require the parent workflow's independent runtime and release evidence.

### Verdict

**CHANGES_REQUESTED.** Two remaining blockers (B8 and B9); three advisories. Recheck after fixes and rerun the focused suites. All review probes used isolated temporary stores, synthetic arguments and stubbed controls/notification senders.


### Independent gate review, round 1

Reviewer: security_detection_audit. Scope: approval_binding.py, approvals.py, claude_code_gate.py, runtime_gates.py, hooks_claude_code.py, gate_policy_cache.py, routes/hooks.py, routes/policy.py and their changed tests. The reviewer did not author these files.

Requirements, architecture and security findings:

- **Blocking G1 (AC-GOV-SBG-001.3), resolved:** the receiver treated entitlement exceptions as entitled. A matching policy could then deny on a storage failure. The regression originally tested an empty policy list. Current matching-policy probes now return no_op; native mirrors return ask.
- **Blocking G2 (AC-GOV-SBG-001.1), resolved:** the receiver collapsed non-object inputs to an empty object before binding. A safe Flask-only probe approved one string and resumed a different string with allow. The current receiver rejects the unsupported input without persisting a row.
- **Blocking G3 (AC-GOV-SBG-001.2), resolved:** missing or invalid pending budgets left no client deadline. Clients now stop a known pending wait with deny or native ask before the installed runtime ceiling.
- **Blocking G4 (bounded input), pending recheck:** the digest size cap was checked per string, then after complete JSON serialization. Aggregate payload size must be rejected before allocating an arbitrarily larger canonical value.
- **Blocking G5 (runtime identity), pending recheck:** the legacy Claude hook supplied a native unprefixed session ID to a process helper that defaults such IDs to OpenClaw. Exact persistent grants must retain the actual runtime on this path.
- **Blocking G6 (exact input types), pending recheck:** invalid JSON strings and actual objects with a raw key normalized into the same object in Cursor/Copilot clients. Unsupported input must retain its type or be refused.
- **Blocking G7 (invocation identity), pending assessment:** runtimes without a native call ID can deduplicate concurrent identical invocations into one approval. One review must not silently authorize two non-idempotent calls. A local per-hook invocation nonce can distinguish calls while remaining stable across that client's HTTP retries.

The gate implementation now separates no-policy/monitor/unentitled outcomes from explicit allow, preserving native permission prompts. Known protected transport/persistence failures deny only the current call. Legacy watcher behavior and kill_on_deny=False remain distinct. Strict digests bind full arguments, cwd, source, kind and exact tool names. The policy snapshot is local, scoped, short-lived and cannot create authority after a current entitlement failure.

Verification: independently reproduced current malformed-input deny with zero new approval rows and matching-policy entitlement-failure no_op. Detector-lane suites separately passed 323 tests after exact evidence and execution-precision changes; these do not establish live hook prevention. Parent owns real runtime and hosted verification.

**Gate verdict: CHANGES_REQUESTED.** Recheck G4 through G7 and the complete gate change after the owning agent finishes remediation. No tool action, live session signal or external message was executed by these probes.


## Continuous security review, round 3

Reviewer: delegated protection-coverage agent. Final source recheck of parent-owned continuous security service/store, signature parser and detector evidence, shared policy matching and dispatch, local-store journal integration, incident persistence/projection, and the corresponding regression suites.

### Remediation and findings

B8 is repaired independently of the earlier policy declaration check: `policy_engine.evaluate` now checks the selected escalation rung before constructing an actuating decision. Both unknown inspection kind and explicitly ineligible security evidence are covered by persisted alert-to-kill ladder regressions. Progress, inspection status and sticky history-gap writes remain atomic. No additional blockers were found in this rechecked parent/detector scope.

At the parent's request, this reviewer implemented B9 after independently reproducing it. `reconcile_session` now records all durable kinds but retains positive recovery only for lifecycle kinds. The periodic caller requires a confirmed active durable episode before notification, control or compatibility fallback. Six regressions failed before the fix and pass after it: producer overlap in both orders, colliding node/session scopes, failed persistence, and old/future evidence. Since this reviewer authored that remediation, its independent approval is delegated separately to the detector audit agent and must be read with that agent's verdict.

### Validation

`python3 -m pytest -q -p no:cacheprovider tests/test_security_ingest.py tests/test_security_ingest_recovery.py tests/test_security_evidence_recency.py tests/test_security_scope_and_priority.py tests/test_incident_lifecycle.py tests/test_guard_policy_enforcement.py tests/test_guard_escalation_ladder.py tests/test_protection_evidence.py tests/test_cloud_guard_signals_slices.py tests/test_detector_incident_delivery.py` passed **250 tests in 8.29 seconds**. `git diff --check` passed. The earlier B8 pure reproduction now returns no actuating decision; the actual-store B9 overlap regressions retain one episode and one scoped projection.

### Advisories and verification limits

Round 2 advisories remain: the existing notification cooldown uses session/kind; evidence inspection completion does not prove policy response availability; process CPU throttling is conservative process-wide accounting. Neither static review nor synthetic store tests prove native runtime denial, subprocess isolation or generated-code safety. Parent-owned real runtime drills, release, cloud promotion, decrypted hosted rendering and live artifact verification remain required work. The coverage UI continues to report independent sandbox/scanner evidence as unavailable where no such source exists.

### Verdict

**APPROVED for the independently reviewed parent/detector source scope**, with zero remaining blockers in that scope and the three documented advisories. B9 was implemented by this reviewer and requires the separate independent detector-audit verdict. This is not approval of unverified runtime behavior or completion of the release/user objective.


### Independent gate review, round 2

Reviewer: security_detection_audit. Rechecked the complete gate scope from round 1, including new binding, cache, hook-client, receiver, persistent-grant and legacy-runtime changes. The reviewer did not implement these files.

G1 through G7 are resolved in the reviewed source. Aggregate identity validation now rejects oversized combined values before canonical JSON allocation. Legacy Claude execution supplies its actual runtime explicitly. Unsupported Cursor/Copilot input types stay distinct. Each client creates one invocation nonce per hook process and reuses it across HTTP retries; distinct invocations cannot share a pending verdict even without native call IDs. Old clients with neither nonce nor native ID do not deduplicate.

Strict binding covers complete JSON arguments and context. Pending transport failure, malformed verdict, missing budget, native-timeout ceiling and persistence failure preserve declared policy authority without signaling a whole session. Unentitled/no-policy/monitor outcomes are no_op, so they cannot bypass native permissions. Native question and permission failures retain ask. Auto-generated persistent approvals bind exact arguments, runtime, tool and cwd; intentional hand-authored broad policies remain unchanged.

Independent verification: 364 tests passed across test_hook_action_binding, test_gate_policy_cache, test_hooks_claude_code, test_runtime_gates_and_hooks, test_hooks, test_question_set_approvals, test_mirror_gate, test_tool_risk, test_tool_risk_remember_flow and test_gate_needs_no_secrets. The 25 deprecation warnings are existing datetime.utcnow usage. Direct pure probes confirmed JSON type distinction, distinct invocation digests and malformed-input type separation in both clients. No live tool action or external message was executed by this review.

Architecture and privacy: existing local queues, runtime hooks, exact session controls and encrypted cloud paths are reused. Policy snapshots remain scoped local files. No new arbitrary process-control surface or package dependency was introduced. Parent owns native-runtime, cross-platform and hosted release evidence; local tests alone do not establish live prevention.

**Gate scope verdict: APPROVED.** This is not an overall Work Order approval: the separate B10 incident-recency finding and final deployment verification remain pending.


### Independent gate compatibility review, round 3

Reviewer: security_detection_audit. Scoped follow-up of approvals.py and routes/policy.py exact remembered grants, plus hosted routes/approval_bindings.py, routes/api.py, routes/api_v1.py, routes/cloud.py and routes/push.py in the isolated cloud worktree. These files were implemented by the gate agent, not this reviewer.

The hosted envelope adds only the runtime and opaque versioned action digest; complete arguments and cwd remain local or on the existing encrypted rail. Hosted writes validate digest shape, runtime, tool and approve action. Policy edits retain binding authority; different exact grants remain distinct. Binding-aware policy fetches declare a capability header. Bound grants carry a never-match fallback expression, and old daemon fetches omit these grants, so ignoring a new field cannot broaden permission. The phone's permanent choice requires exact metadata and no longer derives a prefix rule from a displayed command preview.

The legacy local path now supplies explicit runtime for unprefixed native session IDs and preserves the complete original input separately before stamping internal metadata. Older incomplete receipts require a fresh review. Independent pure probes verified exact grants reject changed content, runtime, cwd and tool, while a legacy compiler without binding metadata cannot match the fallback expression.

Independent verification: 117 OSS tests passed across action binding, remembered choices, policy cache and policy-route gates; 58 hosted tests passed across approval edge cases and push subscriptions, including executable inline-JS checks. Hosted datetime.utcnow deprecation warnings remain. These tests use isolated stores/stubs and establish source compatibility, not a deployed database migration or live native runtime prevention.

**Scoped compatibility verdict: APPROVED.** Final native and hosted release evidence remains the parent's responsibility.

Follow-up browser-management boundary reopened: the actual Approvals template used the filtered daemon endpoint without a capability header, and rendered custom rules only locally. Exact hosted grants were consequently hidden from browser management even though the v1 API could list/delete them. At the parent's request this reviewer implemented a narrow UI repair: the management fetch declares v1 capability and authentication with a bounded wait; both modes render custom rules; cloud removal uses the owner-authenticated DELETE endpoint; exact bindings display "Exact action" instead of the legacy fallback expression. Existing manual cloud rules remain manageable. Failed reads/deletions are explicit. Two executable template regressions failed before the repair and pass afterward; the new file test_approval_grant_management_ui.py is explicitly registered in CI. Isolated desktop and 390px mobile screenshots were rendered and inspected in evidence/approval-grants-desktop.png and evidence/approval-grants-mobile.png; neither is a live hosted verification. Since this reviewer authored the UI follow-up, independent UI approval is delegated to protection_coverage and is pending its verdict. The legacy daemon filter remains unchanged.


### Independent response retry review

Reviewer: security_detection_audit. Scope: sync._apply_guard_policies strict worker mode, security_ingest._policy strict propagation, LocalStore policy read methods and incident_alerts._cooldown_kind.

The first strict wrapper did not observe actual SQL failures: the real store converted failed policy, ladder and latch reads into empty/no-action results. Three reviewer-owned actual-store regressions failed before the follow-up and pass afterward. Current strict store calls propagate underlying read failure, leave the committed cursor untouched, then resume after recovery with one durable policy decision. Periodic callers preserve compatible non-strict behavior. Pre-action audit/outbox failures also propagate. Scoped notification cooldown separates exact node/runtime pairs without changing operational cooldown keys.

Independent verification: seven failure-and-retry cases passed, including three failures injected inside actual SQL reads and four method-level policy/latch/audit/outbox outages. The full notification and policy enforcement suites passed in the earlier 82-pass run; the two failures in that run were the separately tracked B10 historical-evidence cases.

**Retry and cooldown scope verdict: APPROVED.** Separate policy latch identity remains keyed on session/policy/rung; collision across nodes/runtimes was reported to the parent for scope assessment. B10 is still pending independent recheck.


### Independent durable producer and recency review, B9/B10

Reviewer: security_detection_audit. The reviewer did not author the incident-store, reconciliation, periodic producer, worker status or session-row projection changes reviewed here. Reviewer-owned regressions supplied the historical-critical reproduction and the partial-shell-status failure.

B9 is resolved: periodic and incremental producers use the same durable security episode graph and exact projection identity. The periodic path requires confirmed active persistence before any notification/control fallback. Security kinds do not acquire lifecycle recovery from unrelated successful calls. Persistence failure, stale/future evidence and colliding node scopes have actual-store regressions.

B10 is resolved: observation freshness is evaluated on its own implicated evidence before any previous episode can contribute recency. Historical security observations have deterministic scope/reference/severity identities, remain stale and preserve the fresh head; new current evidence starts independently of a stale head. Replaying the same old critical evidence cannot escalate a current warning or create a history row per tick. Reviewer tests now assert both producers retain the original warning head and the same historical identities after two further periodic replays.

Unsupported shell syntax persists a policy-ineligible coverage finding, advances the journal and records partial inspection with a bounded limitation count. Later evidence remains processable. Unexpected detector failure still retains the cursor for retry. The actual session-table reader now includes node_id, allowing the Guard route's exact-scope projection to display persisted inspection gaps instead of withholding a valid scoped finding.

Independent verification: **178 tests passed in 12.87 seconds** across evidence recency, security recovery, lifecycle, Guard checks, incident delivery, incremental security ingest, protection evidence and approval management UI. This includes the original B10 two red cases, the reviewer partial-syntax red case, exact head replay checks and actual-store daemon-to-Guard projection. Notification queue fixtures now use current source time; historical findings correctly do not notify as live threats. All controls and network delivery in these tests are isolated/stubbed.

**B9/B10 source verdict: APPROVED.** This is separate from native runtime proof and deployment verification, which remain the parent's responsibility.


### Independent scoped policy-latch review

Reviewer: security_detection_audit. Scope: LocalStore schema19, scope migration and policy read/write methods; sync exact fact/duration keys, scope-partitioned policy dispatch and periodic reconciliation; the Guard policy-history Scope cell; migration, ladder and reviewer regressions. The reviewer did not author these changes.

The original reviewer actual-store regressions demonstrated that a second node or runtime with the same native session ID inherited the first scope's policy latch. Both now pass. The durable primary key explicitly includes node, runtime, native session, policy and rung. Periodic and strict-worker paths share that exact identity; scoped calls never silently downgrade to a legacy store signature. Scope-partitioned engine inputs prevent colliding native IDs from borrowing cost, duration or ladder progress. Facts retain exact tuple keys in memory and use tagged readable JSON keys in persisted duration state. Worker durable episode age updates the same fact object used by exact evaluation.

Migration preserves old rows with unknown node scope, without guessing an identity. Compatible ambiguous history suppresses the whole policy ladder instead of restarting rung zero or authorizing escalation; audit rows remain readable with unknown scope labels. Exact rows preserve complete native IDs and survive store restart. Copy failure rolls back mutation and schema version together. Strict database failures still propagate to retain the security journal cursor; no new process-control surface was introduced.

One review consistency issue, explicit runtime versus inferred agent type in fact construction, was corrected and covered by a new unprefixed-native-ID regression. The history Scope cell escapes node/runtime values and distinguishes old unknown scope without replacing native IDs with hashes.

Independent verification: **147 tests passed in 13.50 seconds** across ladder/migration, policy enforcement, recency, recovery and incident delivery; after the final runtime consistency change, **42 focused tests passed in 5.41 seconds**, including reviewer-owned node/runtime collision cases, actual SQL failure/retry and durable age. No real actuator or external message was executed. `git diff --check` passed.

**Scoped policy-latch verdict: APPROVED.** Native control identity on a real running agent and final publication/deployment evidence remain the parent's verification work.


### Independent priority/backfill assessment and review

Reviewer: security_detection_audit. The reviewer authored actual-store regressions and benchmark experiments, but did not implement the priority service or query changes. security_gate_audit independently reviewed the seven new regression cases.

The FIFO-only timing issue is material. The existing journal writer retains about 100,000 receipts, pruning at 110,000; a million retained receipts is not a normal reachable case. Even at the one-second minimum cadence, 100,000/128 pages require about13 minutes before reaching a new tail append. Isolated complete-page measurements with 128 interleaved scopes required roughly 386 ms process CPU on early pages; applying the existing duty formula yields about 67 minutes at that observed page cost. Late pages with full 200-event context were more expensive. These are calculated equivalents, not a measured full-queue drain or evidence of typical customer load. A short completed session is excluded from the periodic active-session pass, and its new evidence can become stale before FIFO processing reaches it.

The minimal repair reuses one exact evaluator and the same incident, policy and outbox graph. One bounded priority page precedes one FIFO page. The durable cursor keeps both positions in one progress transaction. Boot/recovery handoff can prioritize the retained tail while every skipped interval stays owned by FIFO; healthy priority advances monotonically. Lane groups remain separate so a historical anchor cannot hide a fresh call. Epoch/floor races and read/evidence/progress failures retain both durable positions. Backfill remains explicitly partial; the feature does not assert complete inspection while earlier activity is pending.

Independent actual-store tests captured six red failures before the implementation. All seven cases now pass: completed/active fresh evidence on the first bounded pass, complete FIFO visitation and delayed old-source discovery, overlap episode/outbox/policy-latch deduplication, both-cursor failure rollback, restart handoff and skipped-interval preservation, and same-episode identity after aging before FIFO replay. The broader six-suite run passed **184 tests in 9.55 seconds**. Only harmless synthetic tool arguments were inspected; no command, native process signal or external notification was executed.

Sanitized benchmark evidence is saved at evidence/security-priority-benchmark.json. With 100,000 old receipts plus one fresh completed-session credential read, the warm measured local finding/outbox response was 113 ms with one historical scope,302ms with10 scopes, and3.005s with 128 interleaved scopes. The complete dual-page passes consumed 160 ms, 381 ms and 3.519 s process CPU respectively. FIFO advanced only to 128 while priority reached 100001. Each distribution used six actual passes, discarding the first from the five-sample warm mean. Calculated sleep was not executed. This demonstrates a bounded first-pass response on the fixture, not a production latency SLA; the existing process-wide CPU target and 60-second sleep ceiling remain unchanged.

**Priority service source verdict: APPROVED.** Remaining limits include sustained input beyond capacity, independent native prevention, network delivery latency and deployed behavior. These are not broadened by the source or benchmark evidence.


### Independent OTLP scope regression remediation review

Reviewer: security_detection_audit. Scope: the materialized-session node fallback in local_store.py and changed assertions in test_otlp_trace_guard_redaction.py and test_otlp_span_parity_sources_content.py. protection_coverage authored this remediation.

The old bare-signature assertions were replaced with stronger scoped checks: exact prefix plus full 24-hex suffix format, an independently computed expected scope digest, node/runtime/kind and durable incident ID. Existing redaction, after-the-fact provenance, non-controllability and encrypted hosted roundtrip assertions remain intact.

The tests exposed a real producer inconsistency rather than only stale assertions. Span tool events already use the virtual receiver node "otlp" when the exporter omits node.id; materialized sessions retained NULL. The exact Guard filter consequently withheld the valid scoped incident. Session materialization now uses the same fallback while preserving explicit exporter nodes. No scope filter was weakened, and telemetry-only sessions retain their observation/control restrictions. Two new real-receiver tests cover missing and explicit node identities.

Independent verification: **32 tests passed in 9.89 seconds** across both complete files. The destructive-looking commands remain inert span attribute strings; no native control or network notification was executed by these tests. The encrypted snapshot roundtrip remains part of the validation.

**OTLP remediation source verdict: APPROVED.** This does not substitute for hosted deployment verification or claim an agent seen only through telemetry can be controlled.

### Approval owner compatibility follow-up

The hosted path exposed a downgrade hazard: an older policy parser ignores the digest field. Bound policies now serialize an impossible command regex for legacy readers; aware readers authorize only the exact digest. New daemons advertise the v1 action-binding capability when fetching cloud policies. The cloud stores only opaque digest/runtime metadata for this purpose; raw arguments and cwd remain node-local. Two local tests exercise serialization and capability negotiation.

Additional full-payload legacy regressions failed before repair: native unprefixed session IDs could share a remembered grant across explicit runtimes, and watcher metadata stamping lost reserved argument keys when reconstructing a grant. Session grant digests now include explicit runtime. New watcher rows preserve their complete original tool_input beneath the metadata envelope; older incomplete receipts refuse remembered grants until a fresh review. The two regressions failed before changes and pass after them.

Verification:304 tests passed across test_hook_action_binding, test_gate_policy_cache, test_hooks_claude_code, test_runtime_gates_and_hooks, test_tool_risk_remember_flow, test_tool_risk and test_mirror_gate. Native client code is unchanged from independent G1-G7 review. Follow-up scoped independent review is requested, not yet claimed complete here.


## Recency remediation and grant-management review, round 4

The detector audit's independent B9 review found B10: a delayed historical critical observation could overwrite a current warning's details while inheriting its recent timestamp. This reviewer implemented the parent-assigned repair. Security observations crossing the current/historical recency boundary now occupy separate episodes. Historical episodes have deterministic scope/evidence/severity identities, retain stale history, and cannot replace the current head. Both daemon producers require their confirmed observation state, and historical observations do not queue active notifications. Positive recovery remains exclusive to lifecycle kinds. Actual-store regressions cover both producers, retained warning heads, repeated historical replay, and historical-first/current/replayed ordering.

Two adjacent corrections landed in the authorized scope: parser limitations persist a partial inspection status and bounded limitation count while advancing the journal; and `query_sessions_table` now includes its stored node identity so exact-scope Guard projection can match actual persisted sessions. The existing full daemon-to-Guard inspection-gap regression passes again without relaxing identity or active-state gates.

Bounded hook capture now reports unknown when an outer or nested 100-item search cannot prove absence. A positive owned-hook hit remains configuration evidence and records inspection completeness separately. The independent gate reviewer approved this capture source and its three regression cases. No runtime execution proof is inferred.

Validation: security recency, Guard checks, protection evidence, ingest recovery, lifecycle and ingest suites passed **160 tests in 10.56 seconds**. Notification-queue fixtures now use current source timestamps to test actual active delivery, while historical-evidence tests retain old source times. Detector audit independently rechecked the B10 recency and partial-status cases; read that agent's final verdict for approval of this reviewer's implementation.

### Independent approval-rule management UI review

This reviewer independently inspected the detector agent's `approvals.html` changes and its shipped-template behavior tests. Both local and hosted modes expose exact and manual grants, escape names/patterns, label exact identity without displaying the legacy fallback regex, retain controls after failed deletion, and show list-read failures. The hosted management read carries authentication and the v1 capability marker; deletion encodes the rule identifier and preserves server errors. The local write retains the established full-list update behavior.

The two actual-template JavaScript behavior tests passed. Desktop and 390px mobile screenshot artifacts were inspected; grant labels and Remove controls remain legible without overflow. Screenshots use isolated rendering, not a live account or proof of hosted deployment.

**UI verdict: APPROVED**, zero blocking findings in the independently reviewed grant-management source/behavior scope. Runtime drills, deployment, encrypted hosted rendering and release completion remain parent-owned verification work. B10 implementation approval remains with the independent detector auditor.

### Scope-owner remediation evidence

Actual-store AC-GOV-SBG-002.2/.4 regressions failed twice before the change: a policy acted on node-a/Claude and suppressed the same native session on node-b/Claude or node-a/Codex. The same probes now pass. Policy action identities remain readable and untruncated; schema19 widens the durable key to node/runtime/session/policy/rung. A transaction rebuild preserves original rows, rejects migration success on copy failure, and retries safely. Legacy unknown node/runtime history is marked legacy_unscoped in audit output, omitted from exact ladder state and conservatively suppresses compatible entire ladders. Old 128-character identity truncations cannot authorize a replay either.

Both incremental strict and modern periodic calls use exact scope, including facts and rung reads/writes. Signature fallback remains for genuinely legacy unscoped calls only. Exact scope never silently downgrades. Strict database exceptions still pin the durable worker cursor for retry. The incident selected for an alert keeps its durable incident ID and exact scope. In-memory fact maps retain readable tuple keys and compatible same-object native aliases; persisted timing memo keys are tagged JSON arrays, not opaque IDs. The audit history displays node/runtime and labels unknown historical scope explicitly.

Verification:136 tests passed across the five scope/security suites with three then-open coverage-owned B10/partial tests excluded. An additional113 tests passed across escalation, enforcement, base local-store and scorecard consumers. Migration/restart probes include NULL legacy runtime, exact long IDs and failed-copy rollback; a browser-JavaScript behavior probe checks readable escaped audit scope. Independent scope re-review is requested; no autonomous-control or release claim is made by this evidence.


### Independent investigation-copy review

Reviewed the parent's three copy corrections in `templates/tabs/guard.html` and `static/js/investigations.js`, plus the updated actual-client assertion. Finding history now includes security risks in its description; both initial and incremental investigation renders label the stored session value as “Last recorded session state”; generic next-step guidance now refers to highlighted evidence and tool inputs. No data source, state computation or control behavior changes. These labels avoid presenting a persisted session row as a live process check and apply to one-off security evidence.

`tests/test_investigation_client.py` independently passed **8 tests in 0.52 seconds**. **Scoped verdict: APPROVED**, no blocking or advisory findings for these copy-only edits. This review does not certify the underlying persisted status as current process state.


### Final delegated-lane checkpoint

The combined ingest, recovery, security recency, scope/priority, lifecycle, policy enforcement/escalation, protection evidence, cloud slices, incident delivery, Guard checks and grant-management suites passed **300 tests in 17.88 seconds**; whitespace checks passed. The independent detector reviewer subsequently approved B9/B10 source and extended head/history-replay assertions, and the independent gate reviewer approved capture truncation. No remaining implementation or review task is outstanding in this delegated lane. The overall work order still requires the parent-owned release and live verification steps.


## Parent verification checkpoint before PR

All delegated source scopes are independently APPROVED above. A broad run over nineteen changed test files passed 650 tests. A subsequent store/security/scope/protection sweep passed 200 tests; the final investigation copy suite passed 29 tests. These runs overlap and are not cumulative test counts. Ruff comparison over 51 touched Python files found zero new findings; existing repository-wide lint debt remains unchanged. Module map, framework map, Python 3.9 annotation, English mechanical, acceptance coverage, CI test-file registration, JavaScript syntax and whitespace checks passed.

Real native turns passed in Claude Code and Copilot: the protected target remained absent, an ordinary target existed, and each private store recorded a denial. Cursor did not reach the hook because authentication was required. A further real Claude turn wrote one harmless file in a separate temporary directory. The normal installed adapter and daemon family ingest committed eight actual events; the security service persisted one boundary finding. Browser inspection verified the completed session's history entry, exact highlighted evidence and explicit unknown isolation/code-check states. Screenshots and sanitized runtime evidence are adjacent. The preview uses a private receiver/store and suppresses delivery; it does not establish production daemon, notification, sandbox, arbitrary egress or hosted enforcement.

Raw browser developer diagnostics for request timing were declined by automatic approval review and were not retried through another surface. No request-volume measurement is claimed.

Source is ready for PR and CI. The full work order remains incomplete until required native verification, release, wheel inspection, cloud promotion and hosted evidence are recorded.

Scope-owner final local rerun:140 tests passed, with the three then-open coverage-owned B10/partial-status regressions excluded. A further focused escalation run passed36 before the last two scope-fact mismatch probes were appended. Missing exact session facts now skips periodic response and raises in strict handling; it never supplies zero-filled authority for a generic policy. Explicit row runtime is consistent with its in-memory scope key. Persisted timing memo keys are domain-tagged readable JSON arrays, keeping legacy native-ID strings separate from exact scope keys.

Compatibility consequence: historical rows without reliable node scope conservatively suppress compatible policy ladders. They remain visible as unknown scope instead of being assigned to a guessed node or reused as escalation authority. A deliberate new policy identity can establish fresh exact-scope history. This behavior avoids replaying a control during upgrade.


## Priority inspection coverage disclosure

Authored by protection-coverage agent after the parent identified historical backfill delaying new evidence. This delta is limited to the existing protection-evidence builder and Guard renderer; the parent owns the priority ingestion mechanism and its timing verification.

The node-status projection now carries a strictly typed `backfill_pending` flag and bounded `priority_processed` count alongside FIFO `processed`. Pending backfill remains partial coverage. With a fresh positive priority count the existing Guard row says recent activity was inspected while earlier activity remains pending. Without that positive evidence it only states that earlier inspection remains pending. Stale, unavailable and disabled states retain their meanings, and history-gap disclosure remains visible. No new endpoint or poll was added.

Four new builder cases and actual shipped-JavaScript behavior assertions failed before this change and pass after it. The protection/cloud-slice suite passed **40 tests**; direct renderer assertions, JavaScript syntax and whitespace checks passed. Independent gate-audit review was requested; its verdict is recorded separately. No all-clear, runtime-prevention or end-to-end latency claim follows from these disclosure tests.


Independent gate review identified a wording blocker in the priority disclosure: `priority_processed` counts receipts rather than proving source-event freshness or successful inspection of each row. The positive-count copy was corrected to “Newer records were processed while earlier activity remains pending inspection.” Zero/unknown priority counts continue to disclose pending earlier activity only. The earlier wording in the authorship checkpoint above is superseded by this correction. Typed fields, stale/unavailable handling and history-gap disclosure remain unchanged. The same 40 focused tests pass after the revised shipped-JavaScript assertions; syntax and whitespace checks pass. Final independent approval is recorded by the gate auditor separately.

## Independent priority disclosure and regression-source review

Reviewer: security_gate_audit. Read-only source review of the protection-evidence builder/Guard disclosure authored by protection_coverage and the seven priority regression cases authored by security_detection_audit. The reviewer did not author these deltas. Parent-owned priority service implementation is outside this scoped verdict.

The builder accepts only a real Boolean backfill flag and a bounded integer priority receipt count, keeps pending history partial, and preserves stale/unavailable/disabled meanings. The shipped renderer retains pending-history and history-gap disclosure without an all-clear or prevention claim. One blocking wording issue was corrected during review: a positive priority count measures selected receipt processing, which can include historical-source or unscoped records; it did not establish that recent source activity was successfully inspected. The final copy now states, "Newer records were processed while earlier activity remains pending inspection." It reports the receipt-level fact without upgrading it into source freshness or complete inspection.

Independent test-source review approved all seven priority cases. They use real temporary stores and real detector/policy paths, with only boundary fault injection and a forbidden actuator stub. The cases meaningfully cover completed/active fresh findings ahead of historical FIFO, eventual old-source attack discovery, overlap identity and outbox/policy idempotence, both-cursor retention on actual read/evidence/progress failures, startup tail handoff without discarding the skipped FIFO interval, and same-evidence episode identity after aging. These tests assert observable evidence/progress outcomes rather than mocking expected detector outputs. They do not prove wall-clock latency under sustained ingestion or native runtime prevention.

Independent verification: protection/cloud-slice tests passed40; the seven priority regressions passed7; whitespace checks passed. **Scoped UI disclosure and priority-test-source verdict: APPROVED.** Review of the service algorithm, broader recovery behavior, performance, publication and live verification remains with its assigned reviewer and the parent.


## OTLP CI contract and producer-scope remediation

Parent-assigned triage reproduced both OTLP failures with protobuf enabled. Actual stored rows were critical observed-only security findings with `daemon_detect_file_blast_radius:<24 hex>` signatures; legacy exact-name lookups missed them. The two tests now validate the scoped namespace, full suffix format, independently calculated SHA-256 scope digest, and node/kind/incident metadata. Existing severity, provenance, non-control and encrypted hosted roundtrip assertions remain intact.

The stricter lookup exposed a real hosted parity regression: spans without `node.id` produced tool events under the existing virtual receiver node `otlp`, while their materialized sessions retained NULL node identity. The exact-scope filter correctly refused to join them. The parent authorized a producer repair: `materialize_sessions_from_spans` now uses that same existing virtual identity only when the source node is absent. Explicit exporter node IDs survive unchanged; no scope-filter or control semantics changed. A new two-case regression verifies absent and explicit source nodes through real intake and stored session/tool rows.

Both original files independently pass **32 tests**. The detector auditor independently reviewed and approved the source/test remediation. A clean temporary OSS virtualenv installed the exact hash-pinned CI base and OTLP requirements; decoder availability was asserted and clawmetry-pro was absent. All **201 tests in the complete 15-file OTLP CI job passed in 36.25 seconds** on local macOS/Python 3.14. One warning came from a compatibility-listener thread during socket teardown (`Bad file descriptor`); no test failed. This local run does not replace Linux/Python 3.11 CI. The developer environment with an installed Pro profile showed four additional daemon-free profile-path failures, which were absent from this clean OSS environment and from the original CI log; no unrelated production or test behavior was changed to hide them.

Whitespace checks passed. No commit or release was performed by this delegated lane.


### CI remediation and scanner checkpoint

The first OSS head passed most checks but failed two OTLP compatibility cases and the Bandit count ratchet. The strict scoped projection exposed both an obsolete exact-signature test lookup and a real producer mismatch: received tool events used virtual node otlp while a materialized session retained NULL. The producer now keeps the same virtual identity for absent node.id and preserves explicit exporter nodes. All severity, observation-only control, provenance and encrypted hosted assertions remain. A clean hash-pinned OSS environment passed the full 201-test OTLP job; independent review passed both complete affected files.

Bandit 1.9.4 from the CI hash-pinned requirements completed with 308 medium-or-higher findings, zero HIGH findings and zero parse errors. Static migration SQL and a shared fixed-column, bound-ID episode read removed duplicated query constructions. There is no new suppression and no relaxed threshold; the ratchet tightens from 309 to 308. The two new ingest query builders use fixed column/runtime expression construction with bound source values; the count is not a claim that existing repository findings are resolved. Summary evidence is adjacent.

The load-review refinement is independently approved above and has separate synthetic load evidence, explicitly distinct from native runtime proof. Release and hosted verification remain pending.

## Independent static-SQL reuse and OTLP scope review

Reviewer: security_gate_audit. Read-only review of parent-authored migration/episode SQL refactors and protection_coverage's OTLP producer fallback/tests. No product edits were made by this reviewer.

The schema19 migration now adds its absent unknown node_id column inside the existing outer schema transaction, then uses a static INSERT/SELECT with COALESCE for legacy NULL values. It preserves the same readable composite identities and conservative unknown-scope semantics. An independent actual DuckDB fault injection after ALTER and before copy confirmed rollback restores both the original schema and historical row, removes the temporary scoped table, and permits a successful retry. Existing startup rollback regressions also pass.

All five identical incident-by-ID lookup sites now reuse _episode_row_locked. Its selected column names are fixed module constants and its incident ID remains a bound SQL parameter. Observation, historical replay, recovery and acknowledgement call it under the same existing writer-lock/transaction boundaries; return decoding is unchanged. The two remaining security-ingest SQL builders use fixed imported column identifiers, fixed runtime-expression fragments and generated parameter placeholders; runtime/node/session/event values remain bound. No new suppression or scan-ratchet relaxation is part of these refactors.

OTLP materialization now assigns the established virtual node identity 'otlp' only when the exporter omitted its node, matching tool_events_for_span. Explicit source node IDs remain unchanged. The two formerly legacy signature lookups now require the exact scoped signal identity plus readable node/runtime/kind and durable incident ID, retaining observed-after-the-fact and redaction assertions. The new actual-receiver cases verify both missing and explicit node identity across materialized session and generated tool events.

Independent verification:120 migration/escalation, incident lifecycle and evidence-recency tests passed;32 OTLP parity/redaction tests passed. Python compilation and whitespace checks passed. The local unpinned Bandit run completed before cancellation was attempted, but this review makes no baseline-count claim; the parent's pinned CI-equivalent scanner owns that result.

**Scoped functional and SQL-safety verdict: APPROVED.** These tests do not establish deployed OTLP delivery, native prevention, live latency or release completion.
