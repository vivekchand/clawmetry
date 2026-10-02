# What Users Want — October 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-10-02 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** Cloud repo inaccessible this run (GitHub session scope limited to OSS repo). Open cloud issues and cloud PRs are carried forward from the 2026-09-18 synthesis. Only OSS-visible changes are new this week.

---

## TL;DR (this week)

This week shipped meaningful Guard hardening — four separate PRs tightening detection (remote script piped into shell, system-prompt instructing outreach, package-source CVE-2026-59176, credential encoding evasions) plus a privacy fix masking local assessment payloads and repairing identifier boundary leaks. OpenClaw 2026.9.x sessions were broken and are now fixed. Cost accounting for repeated session totals and billing scope was repaired. **The uncomfortable headline is the same as last week, now louder: OTLP P0/P1 (#5938, #5949) are entering their third week without a PR.** Every enterprise OTel user still has their span tool calls invisible to Guard and stored unredacted. Week 3 is not an engineering ambiguity — it is a scheduling decision that has not been made.

---

## Hot themes (build these next)

### 1. OTLP Telemetry Correctness — Spans Bypass Guard and Durability Broken

- **Demand**: 2 open `bug` issues (P0 + P1), 7 open `enhancement` issues on schema completeness; 18+ comments across the bugs. Filed 2026-09-13–17.
- **Representative quotes**:
  - *"Guard reads `store.query_events`, but spans go to a separate spans table via `put_span`. No detector ever sees them. [...] Redaction runs only in `LocalStore.ingest`. Span input/output/attributes are stored as received."* — `clawmetry#5938` (P0, 13 comments)
  - *"Never return an unqualified success after silently losing accepted records; follow OTLP partial-success/retry semantics and document rejected counts."* — `clawmetry#5949` (P1, 5 comments)
  - *"Extend existing spans storage to composite identity, resource/scope/schema provenance, links, events, status, timestamps and content policy; migrate existing rows safely."* — `clawmetry#6071` (schema completeness)
- **Why it matters**: The enterprise readiness push shipped LiteLLM, CI/CD provenance, and self-hosted signed images. Every enterprise customer integrating via OTel — LangGraph, Azure AI Foundry, AWS AgentCore — is sending telemetry into a layer that (a) never routes their span tool calls to Guard and (b) stores prompt text unredacted. This week's Guard hardening (four PRs, remote script + system-prompt outreach + package-source CVE + credential encoding) shows the detection team is actively shipping. The span normalization fix belongs on exactly the same track and has the same root surface. Three weeks without a PR on a P0 is now a calendar commitment question.
- **Linked issues**: `clawmetry#5938` (P0), `clawmetry#5949` (P1), `clawmetry#6071`, `clawmetry#6072`, `clawmetry#6073`, `clawmetry#6074`, `clawmetry#6075`, `clawmetry#6077`
- **Likely scope**: OSS — `clawmetry/sync.py`, `clawmetry/local_store.py`, Guard detector path
- **Suggested first step**: Close `clawmetry#5938` first: normalize tool-call spans into the existing event contract so Guard evaluates them, and run redaction before storage. The test requirement is a canary that does not execute a destructive command — this is a one-PR scope.
- **Weeks open**: **3** ⚠️⚠️ (P0 entering third week without a PR)

---

### 2. Session Replay — Runtime-Aware Transcript Viewer

- **Demand**: 3 open OSS issues (`clawmetry#4814`, `#4815`, `#4816`), first filed 2026-08-14. No external user reactions (early signal, but architecture-level: the current viewer is demonstrably broken for multi-agent sessions).
- **Representative quotes**:
  - *"Claude Code is the highest-fanout runtime we support — sessions with 20+ Agent/Task calls. Today the transcript viewer shows the parent turn with a single collapsed 'Task' tool chip — the child's actual work is never inlined."* — `clawmetry#4815`
  - *"Today the session UI shows nothing about how a session ran: Auto vs interactive vs plan vs `--dangerously-skip-permissions`. Approvals asked count is stored but the transcript viewer never fetches it."* — `clawmetry#4814`
  - *"OpenClaw has the richest on-disk trace of any runtime we support — a purpose-built `acp_replay_events` stream, plus normalized tables. We ignore all of it and render the flat JSONL."* — `clawmetry#4816`
- **Why it matters**: ClawMetry's core claim is "observe what your agent actually did." The transcript viewer is where that claim is demonstrated or disproved. For any Claude Code session with subagents, it disproves it: sub-agent trees collapse to a single chip, permission mode is invisible, workflow fanouts vanish. The OpenClaw session fix this week (#6233, #6242) repaired data flowing into the viewer — but the viewer itself, for the multi-agent case, remains broken. Users who upgrade to fix the missing-session bug will now see sessions again, and then immediately see the flat-chip problem.
- **Linked issues**: `clawmetry#4814`, `clawmetry#4815`, `clawmetry#4816`
- **Likely scope**: OSS — `routes/sessions.py`, `clawmetry/local_store.py`, `replay_events` table
- **Suggested first step**: Ship the canonical schema and `replay_events` table design first (dependency for all three mappers), then the permission-mode surface (#4814) as the narrowest first PR.
- **Weeks open without a PR**: **7** ⚠️⚠️

---

### 3. Cost Enforcement — Budget Alerts and Spend Digest

- **Demand**: 9+ open issues across both repos (3 OSS proxy issues + 6+ cloud intel issues carried from 2026-07-31). *[Cloud intel signals carried — unverified against current open issues.]*
- **Representative quotes** *(carried; cloud issues inaccessible)*:
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683`
  - *"I use LLMs daily… I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` ($47K retroactive bill)
- **Why it matters**: This week's cost accounting repair (#6215, #6216) fixed repeated session totals and billing scope — the numbers are now accurate. Budget visibility is excellent. The enforcement half — graduated budget alerts (50%/80%/95%), weekly spend digest to Slack/email, hard caps — remains unshipped. Fixing the accuracy of a number nobody is alerted about is progress; the alert is the missing step that makes that progress actionable.
- **Linked issues**: `clawmetry-cloud#1683` *[carried]*, `clawmetry-cloud#653` *[carried]*, `clawmetry-cloud#655` *[carried]*, `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`
- **Likely scope**: Both — OSS proxy gets enforcement rules; cloud gets alert delivery + digest
- **Suggested first step**: Graduated budget alerts at 50%/80%/95% of the per-project budget. The budget row exists; the alert evaluation path does not.
- **Weeks unaddressed (alert/digest half)**: **16+** ⚠️

---

### 4. P0 Security — Plaintext API Keys in Production DB ⚠️ *[carried, 24+ weeks]*

- **Demand**: 1 issue (`clawmetry-cloud#315`, labeled `bug`, filed **2026-04-14**). Cannot be verified closed — cloud issues inaccessible. No cloud PRs this week with explicit API key migration.
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production database. Anyone with database read access — backup access, GCP logs, support tooling, a developer credential — can impersonate any user.
- **Why it matters**: 24 weeks open through active paying customer growth. Estimated fix: 1 day (bcrypt stored keys, one-time migration). Carrying forward until cloud issues are readable and this can be confirmed closed.
- **Linked issues**: `clawmetry-cloud#315` *[carried — status unverifiable]*
- **Likely scope**: Cloud only
- **Suggested first step**: Bcrypt stored keys with a one-time migration.
- **Weeks open (if still open)**: **24+**

---

## Warm themes (worth tracking)

- **Daemon stall on Windows Python 3.13** (`clawmetry#5932`, filed Sep 13, 20 comments): Still open. Note: the Windows uninstall stall (#6138) was a different code path and has now shipped. This is a runtime ingest failure (`daemon_ingest_stalled`) for an installed customer on Windows + Python 3.13. 20 comments is not background noise.

- **Jev evaluator integration** (`clawmetry#6121`, `clawmetry#6122`, filed Sep 20): Two weeks old, no reactions, still `bot-plan-only`. Observe Jev decision requests with accurate usage/attribution, plus versioned advisory assessment contracts + encrypted snapshot support. Internal scope expansion from the WO-MON series. If Jev is a near-term release, these need PRs in the next 2–3 weeks.

- **Enterprise readiness cluster**: Signed container image (#5948), CI/CD GitHub Action + SARIF (#5946), Windows service + VDI install (#5942), LiteLLM proxy callback (#5940), cost figure provenance labels (#5937), project + user tags + per-project budgets (#5941). All filed 2026-09-13, all `bot-plan-only`. No reactions, no PRs. Five distinct enterprise requirements from the same planning day — prioritization signal is absent.

- **Off-box ingest SDK** (`clawmetry#4779`, `clawmetry#5679`): Partial ship. Ingest key + generated contract + setup prompt + live status landed. The full SDK and auto-detection remain open.

- **Evals — LLM-as-judge** (`clawmetry#1619`): **19+ weeks open, 0 PRs.** Score-first reordering and session drill-down shipped earlier. The core ask — auto-scoring with configurable rubric, local, on every completed session — remains unbuilt. UI shell exists; evaluator doesn't. At 19 weeks, a decision is warranted.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): **20+ weeks open, 0 PRs.** NL question → SQL → chart over local DuckDB. No movement. A backend endpoint is the only missing piece.

- **Outcome Provenance / Delayed Feedback** (`clawmetry#6077`): 2 weeks old. Extend git_outcomes and cohort infrastructure with explicit outcome/feedback records, attribution confidence, and revision/delay/missingness tracking. Enterprise-relevant; depends on OTLP schema completeness.

---

## Closed-loop themes (we shipped this)

**New since 2026-09-25 (this week's substantive merges):**

- **OpenClaw 2026.9.x session fix** (`clawmetry#6233`, `#6242`, merged Oct 2): Sessions on OpenClaw 2026.9.x were invisible; root cause was a SQLite transcript store migration. Sessions now appear again.

- **Privacy: local assessment masking + identifier boundary repair** (`clawmetry#6227`, `#6228`, merged Oct 1): Assessment payloads are now masked locally; identifier boundary leaks that could leak session-scoped data across users are repaired.

- **Guard: remote script piped into shell** (`clawmetry#6211`, merged Oct 1): A curl/wget piped directly into sh/bash on a fresh install is now flagged. Addresses a common supply-chain attack pattern.

- **Guard: system-prompt instructing outreach** (`clawmetry#6210`, merged Oct 1): A skill or system-prompt file telling an agent to reach out to an external URL is now flagged (ATLAS CS0051 S13, CS0049 S05-S06).

- **Guard: package-source CVE-2026-59176** (`clawmetry#6203`, merged Sep 30): Tool arguments installing a package from a path, temp dir, or remote source are now flagged. Critical for temp dir or out-of-cwd path.

- **Guard: exec approval drift fix** (`clawmetry#6186`, merged Sep 30): OpenClaw exec approval that was turned off out-of-band is now re-applied.

- **Guard: credential encoding evasion resistance** (`clawmetry#6182`, merged Sep 27): Credential inspection now resists encoding evasions; coverage gaps are exposed rather than hidden.

- **Cost accounting repair** (`clawmetry#6215`, `#6216`, merged Sep 30): Repeated session totals and runtime billing scope were double-counting. Numbers are now correct.

- **Adapter revision tracking across Pro upgrades** (`clawmetry#6221`, `#6223`, merged Oct 1): Loaded adapter revisions are tracked across Pro upgrades, repairing accounting gaps when a Pro adapter replaces a free one mid-session.

- **has_capacity_batch + endpoints** (`clawmetry#5114`, merged Oct 1): Batch capacity-check endpoint landed, enabling bulk entitlement checks.

**Carried from prior weeks (see 2026-09-25 synthesis for full list):**

- Enterprise readiness batches 1–5, hosted Guard/Signals parity, cost basis labels everywhere, cloud project cost report + finance reader, privacy/security hardening, auth fix, DPA first draft, Qwen Code free tier, dashboard opens on Agents roster, OpenClaw native approvals.

---

## Quiet noise (likely not signal)

- **WO-MON OTLP schema completeness series** (`clawmetry#6071`–`#6077`, filed Sep 17): Seven work-order tracking issues. Real features, but self-generated internal scope. The two *bugs* in this cluster (#5938, #5949) are signal; the enhancement trackers are backlog.

- **Bot-plan-only tracking issues** (~22 of 35 enhancement issues carry `bot-plan-only`): Claude-generated architectural plans waiting for a PR. Real features, not validated external user asks. Implementation backlog.

- **CI hardening PRs** (~10 merged PRs this week): Hash-pinned pip bootstraps, advisory clearances, supply-chain hardening. Healthy hygiene; not user feature signal.

- **Version-bump + RELEASE + i18n + deps PRs**: ~50–60% of merged PRs. Automation working correctly.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (this week, excl. bumps/RELEASE/i18n/deps) | ~10 substantive |
| Cloud PRs merged (this week) | *not accessible this run* |
| User-signal themes shipped (this week) | **5** (OpenClaw session fix, privacy masking, 3× Guard hardening, cost accounting repair) |
| **Largest PR cluster (this week)** | Guard hardening (4 PRs) |
| **OTLP P0 bug `clawmetry#5938`** | **3rd week open, 0 PRs** ⚠️⚠️ |
| **OTLP P1 bug `clawmetry#5949`** | **3rd week open, 0 PRs** ⚠️⚠️ |
| Session Replay EPIC: PRs shipped | **0 (7 weeks open)** ⚠️ |
| Cost enforcement alerts/digest: PRs shipped | **0 (16+ weeks)** ⚠️ |
| P0 Security `clawmetry-cloud#315`: PRs shipped | **0 (24+ weeks, status unverifiable)** ⚠️⚠️ |
| Evals EPIC (`clawmetry#1619`): PRs shipped | **0 (19+ weeks)** |
| Dives EPIC (`clawmetry#999`): PRs shipped | **0 (20+ weeks)** |
| React v2 EPIC (`clawmetry#1492`): PRs shipped | **0 (19+ weeks)** |
| Themes HOT for 2+ weeks without action | OTLP P0/P1 (week 3), Session Replay (7 wks), cost enforcement alerts (16+ wks) |
| Cloud repo accessible this run | **No** (OSS scope only — 3rd consecutive run) |

**Uncomfortable truths this week:**

1. **OTLP P0/P1 are in their third week without a PR.** This week shipped four Guard hardening PRs from the same team that owns the span normalization fix. The technical context is live. A third week without a PR means it is not an engineering blocker — it is a prioritization decision that should be made explicitly rather than by inaction.

2. **OpenClaw 2026.9.x sessions are fixed, but users who upgrade to see their sessions will immediately encounter the flat-chip transcript viewer.** The session fix brings users back to the product. The broken multi-agent view is now more likely to be the first thing they notice.

3. **Three epics are now 19–20 weeks old with zero PRs.** React v2 (#1492), Evals (#1619), Dives (#999). Each has a defined first step and no unresolved design ambiguity. At 20 weeks, these are effectively cancelled features unless they get a PR or get explicitly closed.

4. **Cost enforcement alerts remain 16+ weeks unshipped.** This week's cost accounting fix made the numbers accurate. A budget display with accurate numbers but no alert threshold is a reporting tool, not a control. The alert path is 5–10 hours of work.

5. **Cloud issues remain inaccessible for the third consecutive run.** The plaintext API key bug, cost enforcement intel signals, and Guard cloud issues are carried from 2026-07-31 data. The synthesis is operating on stale cloud signal.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **35 open OSS issues analyzed** (3 `bug` + 32 `enhancement`; 0 `intel-feedback` / 0 `intel-pain` in OSS — all OSS issue signal is bot-generated or founder-initiated). **Cloud issues inaccessible this run** — carried from 2026-09-18. **~10 substantive merged OSS PRs** in the 7-day window. Cloud repo out of session GitHub scope this run (3rd consecutive week).
