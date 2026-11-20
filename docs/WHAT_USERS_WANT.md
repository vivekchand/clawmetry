# What Users Want — November 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-11-20 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** Cloud repo inaccessible this run (GitHub session scope limited to OSS repo). Open cloud issues and cloud PRs are carried forward from the 2026-10-02 synthesis. Only OSS-visible changes are new this week.

---

## TL;DR (this week)

The daemon reliability "blitz" (6 root-cause PRs, week of Nov 14) fixed five specific failure modes — but 8 field-failure bugs are still open and the published artifact itself has been failing conformance verification for 4+ weeks (`#6491`, 76 comments). Users who install ClawMetry today may get a broken daemon. Meanwhile, OTLP P0 (`#5938`) finally shipped after 11 weeks — the longest-running hot theme from the last synthesis is now closed. OTLP P1, Session Replay, and all Enterprise Readiness issues remain unshipped, with Session Replay now entering week 14 without a PR on the highest-fanout runtime (Claude Code).

---

## Hot themes (build these next)

### 1. Daemon Reliability — Field Failures and Broken Published Artifact

- **Demand**: 9 open `bug` issues (8 `field-failure` + `#6491`), spanning Linux/macOS/Windows × Python 3.9–3.15. `#6491` has 76 comments and has been open since Oct 20 (4+ weeks). The blitz fixed 5 root causes — but different failure modes keep opening.
- **Representative quotes**:
  - *"The conformance heartbeat failed against the PUBLISHED artifact. This is not a red PR check. It means the product a user installs right now is broken, independent of anything currently being worked on."* — `clawmetry#6491` (76 comments, Oct 20)
  - `[field-failure] daemon: daemon_ingest_stalled on Darwin (py 3.9)` — `clawmetry#6492` (26 comments, Oct 20)
  - `[field-failure] daemon: daemon_lock_refused on Darwin (py 3.15)` — `clawmetry#6497` (26 comments, Oct 21)
- **Why it matters**: Zero-config observation-by-default is ClawMetry's core UX promise. A daemon that refuses to start or stalls on ingest breaks that promise silently — users see no data and have no obvious path to debug it. 76 comments on `#6491` after a week-of-blitz means either the fix didn't ship or the fix shipped and a different conformance failure persists. Either way, it is now a install-time trust problem. The blitz PR cadence is healthy; closing the remaining 8 issues is the unfinished work.
- **Linked issues**: `clawmetry#6491`, `clawmetry#6492`, `clawmetry#6497`, `clawmetry#6517`, `clawmetry#6537`, `clawmetry#6538`, `clawmetry#6567`, `clawmetry#6588`, `clawmetry#6595`, `clawmetry#6597`
- **Likely scope**: OSS — `clawmetry/sync.py`, `clawmetry/local_store.py`, daemon lock and ingest paths
- **Suggested first step**: Treat `#6491` (heartbeat failure, 76 comments) as a yank/hotfix decision before any new feature work. Then close the 8 open field-failure bugs by linking each to the specific fix PR or reopening triage.
- **Weeks open (oldest)**: **4 weeks** (`#6491`) ⚠️

---

### 2. Session Replay — Runtime-Aware Transcript Viewer

- **Demand**: 2 open OSS issues (`clawmetry#4814`, `#4815`), first filed 2026-08-14. No external user reactions (architecture-level: the current viewer is broken for multi-agent sessions — the most common Claude Code usage pattern).
- **Representative quotes**:
  - *"Claude Code is the highest-fanout runtime we support — sessions with 20+ Agent/Task calls. Today the transcript viewer shows the parent turn with a single collapsed 'Task' tool chip — the child's actual work is never inlined."* — `clawmetry#4815` (4 comments)
  - *"Today the session UI shows nothing about how a session ran: Auto vs interactive vs plan vs `--dangerously-skip-permissions`. Approvals asked count is stored but the transcript viewer never fetches it."* — `clawmetry#4814` (4 comments)
- **Why it matters**: Claude Code is the most-used runtime ClawMetry monitors. Any session with 20+ subagents — which this repo itself generates — collapses to a single chip. The OpenClaw session fix shipped in Oct repaired data flow into the viewer; for Claude Code multi-agent sessions, the viewer itself remains broken. Users who come to ClawMetry to understand *what their agent actually did* hit the worst-case scenario immediately on the highest-fanout runtime.
- **Linked issues**: `clawmetry#4814`, `clawmetry#4815`
- **Likely scope**: OSS — `routes/sessions.py`, `clawmetry/local_store.py`, replay_events table
- **Suggested first step**: Ship the canonical `replay_events` schema design as a tracked issue, then the permission-mode surface (`#4814`) as the narrowest first PR (2–4 hours, no new data model needed).
- **Weeks open without a PR**: **14** ⚠️⚠️

---

### 3. OTLP P1 — Durable Acknowledgements and Unsampled Usage Accounting

- **Demand**: 1 open `bug` (`clawmetry#5949`, 8 comments) + 5 WO-MON schema completeness enhancements (`#6071`–`#6075`). Filed 2026-09-13.
- **Representative quotes**:
  - *"Never return an unqualified success after silently losing accepted records; follow OTLP partial-success/retry semantics and document rejected counts."* — `clawmetry#5949` (P1, 8 comments)
  - *"Extend existing spans storage to composite identity, resource/scope/schema provenance, links, events, status, timestamps and content policy; migrate existing rows safely."* — `clawmetry#6071`
- **Why it matters**: OTLP P0 (`#5938`) finally shipped after 11 weeks — the span normalization / Guard bypass and unredacted storage is now fixed. P1 is the next piece: an OTLP producer that sends spans successfully to ClawMetry and sees `200 OK` has no guarantee those spans made it to durable storage. For LangGraph, Azure AI Foundry, AWS AgentCore integrations, silent loss is a correctness bug in cost accounting and a compliance gap in audit trails.
- **Linked issues**: `clawmetry#5949`, `clawmetry#6071`, `clawmetry#6072`, `clawmetry#6073`, `clawmetry#6074`, `clawmetry#6075`
- **Likely scope**: OSS — `clawmetry/local_store.py`, OTLP receiver in `routes/meta.py`
- **Suggested first step**: Ship OTLP partial-success semantics (`#5949`) first — bounded queue + explicit acknowledgement. The schema completeness series (`#6071`–`#6075`) is additive and can follow.
- **Weeks open**: **10** (P1); OTLP P0 closed after 11 weeks ✓

---

## Warm themes (worth tracking)

- **Enterprise readiness cluster** (`clawmetry#5948`, `#5946`, `#5942`, `#5940`, `#5937`): Signed container image, CI/CD GitHub Action, fleet install (Windows service + VDI + Linux linger), LiteLLM proxy callback, cost figure provenance labels. All filed 2026-09-13, all `bot-plan-only`. 10+ weeks, 0 PRs. The LiteLLM hardening PRs this week touched the advisory/dependency layer — the feature itself (proxy callback + OTel ingestion) is unbuilt. If enterprise is a growth vector, one of these five needs a PR slot.

- **DuckDB migration tail** (`clawmetry#1032`, `#1038`, `#1471`, `#1540`, `#1722`, `#2991`): Phase 6 Cloud SQL teardown + "query-spine P9" retire monolith snapshot. DuckDB 2.0 bumped in deps this week — the actual Cloud SQL retirement and snapshot retirement have no PR. 27+ weeks.

- **React v2 migration** (`clawmetry#1492`, `#1493`, `#1496`, `#1497`, `#1519`): SPA scaffold, typed v2 contracts, cloud mirror, polish. 27+ weeks open, 0 PRs. At this age, either it gets a PR date or it gets closed. Middle ground is drift.

- **Governance / audit evidence contracts** (`clawmetry#6349`, `#6122`, `#6121`, `#5944`): Source-rights evidence hook (AcqPath integration), JEV versioned advisory contracts, Jev decision-request observability, MITRE ATLAS case study replay against Guard. The approval evidence commit link shipped this month (`#6530`) — adjacent work. 2–10 weeks, low comment volume.

- **LLM-as-judge evals** (`clawmetry#1619`): 27+ weeks open, 0 PRs. UI shell exists; local auto-scoring evaluator doesn't.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): 27+ weeks open, 0 PRs. Backend endpoint is the only missing piece.

---

## Closed-loop themes (we shipped this)

**New since 2026-10-02 (last 30 days of substantive merges):**

- **OTLP P0 — span normalization, Guard bypass, unredacted storage** (`clawmetry#5938`, shipped Nov 2026): After 11 weeks as the loudest open HOT theme, the OTLP P0 is now closed. Span tool calls are now normalized into the event contract so Guard evaluates them, and redaction runs before storage. Watching for follow-up reports on P1 (`#5949`).

- **Daemon reliability blitz — 5 root causes fixed** (PRs `#6612`, `#6621`, `#6622`, `#6618`, `#6613`, merged Nov 14–15): Daemon can now reclaim a lock from a stuck process; PID reuse within tolerance is detected; `save_state()` failure no longer causes false `daemon_ingest_stalled` reports; workspace-relative fleet DB skipped when workspace is a CWD fallback; `sync --restart` now restarts only the correct user's store. **8 field-failure bugs remain open — the class is not closed, 5 root causes are.**

- **Path traversal containment on /api/reasoning, /api/logs, /api/skills** (`clawmetry#6658`, `#6659`, merged Nov 20): File path is now contained on the three API endpoints that serve filesystem-relative content. Security fix.

- **Approval evidence commit link** (`clawmetry#6530`, merged Nov 2026): Approvals are linked to the git commit that recorded the approved action; audit trail now bridges ClawMetry's approval table and repo history.

- **Robotics / physical AI control-plane query seam** (`clawmetry#6662`, `#6663`, merged Nov 20): Authenticated control-plane query seam for robotics runtimes. First step toward observable physical AI.

- **Windows certmgr.msc TLS guidance** (`clawmetry#6629`, merged Nov 15): Desktop TLS interception now surfaces actionable guidance on Windows. Usability fix for enterprise TLS inspection environments.

**Carried from prior periods (see 2026-10-02 synthesis for full list):**

Enterprise readiness batches 1–5, hosted Guard/Signals parity, cloud project cost report, OpenClaw session fix, privacy masking, Guard hardening series (remote script, system-prompt outreach, package-source CVE-2026-59176, credential encoding evasion), cost accounting repair, adapter revision tracking.

---

## Quiet noise (likely not signal)

- **Weekly-digest and good-first-issue-scan issues** (`clawmetry#6636`, `#6348`, `#6190`, `#6126`, `#5977`, plus ~12 good-first-issue-scan issues): Bot-generated operational noise. Not user signal.

- **WO-MON OTLP schema completeness series** (`clawmetry#6071`–`#6075`): The P0 and P1 bugs in this cluster are signal; the five work-order enhancement trackers are internal scope backlog.

- **Bot-plan-only tracking issues** (~22 of 66 open issues carry `bot-plan-only`): Claude-generated architectural plans waiting for a PR. Real features, not validated external user asks.

- **CI hardening PRs** (~24 of 45 merged PRs this period): Advisory clearances, dep bumps, pin set updates. Healthy hygiene; not user feature signal. DuckDB 2.0 bumped in this batch.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (last 30 days, all) | **45** |
| OSS PRs merged (last 30 days, substantive — excl. deps/CI/RELEASE/bumps) | **~8** |
| Cloud PRs merged | *not accessible this run* |
| User-signal themes shipped (last 30 days) | **3** (OTLP P0, daemon partial, path traversal, robotics seam) |
| **Largest PR cluster** | CI hardening (24 PRs) |
| **Daemon reliability `#6491`** | **4+ weeks open, 76 comments** ⚠️⚠️ |
| **Open field-failure bugs** | **8** (oldest: Oct 20) ⚠️ |
| **OTLP P0 `#5938`** | **SHIPPED ✓** (11 weeks after filing) |
| **OTLP P1 `#5949`** | **10 weeks open, 0 PRs** ⚠️ |
| Session Replay EPIC: PRs shipped | **0 (14 weeks open)** ⚠️⚠️ |
| Enterprise readiness cluster: PRs shipped | **0 (10+ weeks)** ⚠️ |
| Evals EPIC (`#1619`): PRs shipped | **0 (27+ weeks)** |
| Dives EPIC (`#999`): PRs shipped | **0 (27+ weeks)** |
| React v2 EPIC (`#1492`): PRs shipped | **0 (27+ weeks)** |
| Themes HOT for 2+ weeks without action | Daemon `#6491` (4 wks), Session Replay (14 wks) |
| Cloud repo accessible this run | **No** (OSS scope only) |

**Uncomfortable truths this month:**

1. **The published product has been failing conformance verification for 4+ weeks (`#6491`, 76 comments) while a "daemon reliability blitz" shipped.** The blitz fixed different root causes than what `#6491` tracks. Either the fix didn't reach the published artifact, or a different failure persists. 76 comments and still open means this needs an explicit "is pip install clawmetry working right now?" check, not more PRs on adjacent paths.

2. **OTLP P0 closed after 11 weeks — good.** The pattern holds: a P0 that gets triaged and tracked eventually ships. OTLP P1 (`#5949`) is now week 10. If the pattern holds, it ships in week 11–12. If it doesn't, it goes into the "27-week graveyard" with evals, dives, and React v2.

3. **Session Replay is week 14 with zero PRs.** Claude Code generates the most complex multi-agent sessions in the product's target market. The transcript viewer collapses every subagent to a single chip. This week's robotics query seam PR (`#6662`) shows the team can ship new feature architecture. The same capacity could close Session Replay in 1–2 PRs.

4. **Three epics are 27 weeks old with zero PRs.** React v2 (`#1492`), Evals (`#1619`), Dives (`#999`). No technical blocker is documented. These are either actively de-prioritized (which should be stated explicitly) or stuck in perpetual "next sprint" planning. 27 weeks is a decision, not a delay.

5. **Cloud issues remain inaccessible.** The plaintext API key bug (`clawmetry-cloud#315`), cost enforcement intel signals, and Guard cloud signals are carried from July 2026 data. 4 consecutive weeks of OSS-only synthesis means the cloud-side user signal is now stale enough to be misleading.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **66 open OSS issues analyzed** (10 `bug` + 44 `enhancement` + 12 other; 0 `intel-feedback` / 0 `intel-pain` in OSS — all OSS issue signal is bot-generated or founder-initiated). **Cloud issues inaccessible this run** — carried from 2026-10-02. **45 merged OSS PRs** in the 30-day window (~8 substantive). Cloud repo out of session GitHub scope this run.
