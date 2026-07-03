# What Users Want — July 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-07-03 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

---

## TL;DR (this week)

Users keep asking two things loudly: **"warn me before I spend $1,800 without noticing"** and **"show me what my whole team is spending, not just me."** The billing infrastructure replatform (Stripe, plan switching, pricing) shipped at pace in cloud, but the direct user pain — graduated spend alerts, scheduled cost digests, team-wide ROI rollups — remains open. Velocity is very high (861 PRs merged across both repos in 30 days) but is concentrated in internal infrastructure (entitlement API expansion in OSS, Stripe replatform in cloud); the HOT user-facing themes are being addressed partially but not closed.

---

## Hot themes (build these next)

### 1. Surprise Bill Prevention & Real-Time Spend Control

- **Demand**: 9 open issues (3 OSS + 6 cloud), backed by a 474-comment HN thread and multiple viral pain posts; reactions: 0 (new label system, not a proxy for signal weight here)
- **Last raised**: 2026-06-25 (cloud #1701)
- **Representative quotes**:
  - > "Just a number climbing in silence while five engineers spent three days hunting down a $1,800 spike with zero attribution." — clawmetry-cloud#1683
  - > "I use multiple AI tools for work and also my side projects, and the annoying part is there's no single place to track costs across all of them." — clawmetry-cloud#1694
  - > "I was running some autonomous agents and realized I had no idea how much I was spending" (user then built their own terminal monitor) — clawmetry-cloud#1701
- **Why it matters**: Three separate developers independently built their own tooling (AgentWatch, Tokens4Breakfast, a terminal monitor) to solve the problem ClawMetry already claims to solve. Each one is a missed conversion. The Dev.to article on retroactive $47K AI bills (clawmetry-cloud#655) circulates every time a new bill-shock wave hits HN. The emergency-stop endpoint shipped (#3445 OSS, #1613 cloud), but users need alerts *before* the damage, not just a kill switch.
- **Linked issues**: clawmetry-cloud#1683, clawmetry-cloud#1701, clawmetry-cloud#1694, clawmetry-cloud#655, clawmetry-cloud#1484, clawmetry-cloud#692, clawmetry-cloud#4, clawmetry#2817, clawmetry#2818
- **Likely scope**: Both — OSS gets the proxy-side dollar-spiral breaker (#2818) and req/min rate limiter (#2817); cloud gets the graduated threshold alerts (50/80/95% of monthly cap) and scheduled weekly digest (#1484).
- **Suggested first step**: Ship clawmetry-cloud#1484 (scheduled spend digest + graduated budget alerts at 50/80/95%) — this is a notification layer, not enforcement, so it's safe and fast to ship. Pair it with a blog post that targets the bill-shock search term.

---

### 2. Team-Wide Token ROI / Cross-Developer Visibility

- **Demand**: 4 open issues (1 OSS + 3 cloud), HN thread signal (474 comments, clawmetry-cloud#653), active competitor targeting
- **Last raised**: 2026-05-11 (clawmetry-cloud#703)
- **Representative quotes**:
  - > "I use llms daily...anywhere from $200-$400 tops...I just can't figure how to burn [this much]" — from the 474-comment HN thread on lack of team-wide token ROI (clawmetry-cloud#653)
  - Faros is pitching "no cross-developer aggregation" as the gap to fill — the exact gap ClawMetry is supposed to own (clawmetry-cloud#650)
- **Why it matters**: The tool is used per-developer, but budget decisions are made per-team. Every engineering manager who sees one developer's ClawMetry dashboard and asks "how do I see this for all 12 engineers?" and can't get an answer is a lost Pro or Enterprise conversion. Faros is explicitly targeting this positioning gap; if they close it first, the enterprise story is gone.
- **Linked issues**: clawmetry-cloud#653, clawmetry-cloud#650, clawmetry-cloud#308, clawmetry-cloud#703, clawmetry-cloud#1201
- **Likely scope**: Both — OSS audit_log table (#3420) is the data foundation; cloud is the aggregation and UI layer (cross-developer rollups, manager-view, export).
- **Suggested first step**: A `/api/team-usage` endpoint that aggregates cost + token data across connected nodes, gated behind Pro/cloud, with a simple manager-view table in the cloud dashboard. It doesn't need to be beautiful — it needs to exist so the demo is possible.

---

### 3. First-Run Activation: Fix the Empty/Broken First Impression

- **Demand**: 3 open issues (all cloud), tagged P0 by the team — already internally prioritized but still open
- **Last raised**: 2026-05-28 (clawmetry-cloud#1189)
- **Why it matters**: The onboarding loop has been patched multiple times (clawmetry#3410, clawmetry#3407, cloud#1705 — always show options, headless OAuth, paste-code flow) but the core issue — new users see an empty/broken screen on first run — remains open. Every conversion from free to trial to paid starts with first run. A broken first impression means every downstream metric (trial rate, activation rate, upgrade rate) is running at a discount. This is the highest-leverage fix in the funnel.
- **Linked issues**: clawmetry-cloud#1189, clawmetry-cloud#1190, clawmetry-cloud#1191
- **Likely scope**: Both (OSS owns the local first-run experience; cloud owns the upgrade moment and trial lifecycle)
- **Suggested first step**: Close clawmetry-cloud#1189 first — the empty screen is the worst offender. Specifically: add a "no data yet" state with a guided checklist (connect → wait 60s → see first session appear). The upgrade modal (#1190) and trial nurture (#1191) are only valuable if the user gets past the empty screen.

---

### 4. Smart Model Routing & Cost-Proxy Enforcement

- **Demand**: 3 open issues (2 OSS + 1 cloud), cross-repo, with clear competitor reference (TokPinch, which reached ~250 stars in 2 weeks)
- **Last raised**: 2026-06-07 (clawmetry#2816)
- **Representative quotes**:
  - > "TokPinch's most financially impactful feature: smart routing — auto-downgrade cheap tasks to a cheaper model, saving 10-50% API cost" — clawmetry-cloud#54
- **Why it matters**: ClawMetry surfaces smart-routing savings in the usage panel (shipped, #3450 OSS) but doesn't actually do the routing. TokPinch does. The observation-without-enforcement gap is real: users can see they *could* save 40% on their API bill but ClawMetry doesn't help them get there. The managed cloud proxy endpoint (#53) is the right cloud-side answer.
- **Linked issues**: clawmetry#2816, clawmetry#2817, clawmetry#2818, clawmetry-cloud#54, clawmetry-cloud#53
- **Likely scope**: OSS for the local proxy heuristic; cloud for the managed enforcement endpoint
- **Suggested first step**: Implement the content-agnostic req/min breaker in the local proxy first (#2817, OSS) — it's surgical and doesn't require model-specific heuristics. Then layer in the heuristic cheap-task router (#2816).

---

### 5. React v2 UI Migration (Parallel Rails)

- **Demand**: 7 open issues (all OSS), EPIC with RFC sub-issues
- **Last raised**: 2026-05-16 (clawmetry#1519)
- **Why it matters**: The current Flask-rendered UI is showing its age relative to competitors. The v2 migration is on parallel rails (`/v2`) so it's low-risk, but the epic has been open for 7 weeks and only navigation scaffolding has shipped (Phase A + B). The competitor AgentPulse (clawmetry-cloud#649) explicitly positioned its React-based dashboard as a differentiator. UX polish compounds: every sprint that ships on the old stack is tech debt for the migration.
- **Linked issues**: clawmetry#1492, clawmetry#1493, clawmetry#1494, clawmetry#1496, clawmetry#1497, clawmetry#1517, clawmetry#1519
- **Likely scope**: OSS only (the React SPA; cloud mirrors at app.clawmetry.com/v2 via #1497)
- **Suggested first step**: Close clawmetry#1493 (React SPA scaffold + pip-package bundling) — unblocks all downstream RFCs.

---

## Warm themes (worth tracking)

- **Distributed Tracing / OTel Agent Graph** (1 OSS EPIC + 2 cloud issues): clawmetry#1006 (OTel trace tree EPIC), clawmetry-cloud#1695 (Claude Code OTel-only telemetry path), clawmetry-cloud#1696 (Copilot CLI OTel cost parity). Agent graph loader fixed (#3462), but the full parent→child trace hierarchy is unbuilt. Slow burn; will become HOT if a competitor ships it first.

- **Subscription-Mode Cost Accounting** (1 cloud issue): clawmetry-cloud#1088. Users on Claude Max / ChatGPT-Plus / Codex subscriptions see inflated cost numbers. Small fix, high-trust moment: when the numbers are wrong, users stop trusting the dashboard. Worth a quick patch.

- **Remote Approvals + Governance Control Plane** (3 issues across repos): clawmetry-cloud#2 (remote approval gates), clawmetry#881 (OSS roadmap placeholder), clawmetry-cloud#1192 (full EPIC: approvals + policy + kill-switch + audit + replay). The persistent approval strip shipped in cloud (#1608) and the emergency-stop endpoint is live (#3445 OSS, #1613 cloud). The remaining gap is the *full governance flow* — mobile approvals, webhook-triggered gates, policy editor. A WARM theme approaching HOT as agents get more autonomous.

- **Session Timeline / Replay** (3 cloud issues): clawmetry-cloud#320 (model-change annotations), clawmetry-cloud#321 (compaction markers), clawmetry-cloud#322 (full replay with time scrubber). No shipped progress yet. Useful but not urgent.

- **Autonomy Monitoring & SOUL.md Drift Alerts** (3 cloud issues): clawmetry-cloud#360 (autonomy score trending), clawmetry-cloud#361 (SOUL.md values-drift alerts), clawmetry-cloud#363 (cron intention gap alerts). Grounded in the Berkeley keynote on autonomous agent design. Forward-looking; worth tracking as agent autonomy increases.

---

## Closed-loop themes (we shipped this)

- **Billing Replatform** (cloud): Stripe plan switching, pricing catalogue ($29→$19 reprice), upgrade modals, free plan, annual plans, trial logic — addressed in ~15 cloud PRs merged 2026-06-10 through 2026-06-14. Watching for follow-up UX issues.

- **Cloud Dashboard Spot Control** (cloud): one-click stop/pause/resume of a runaway agent — addressed in clawmetry-cloud#1613 (merged 2026-06-10). Persistent approval strip with inline Approve/Deny — clawmetry-cloud#1608 (merged 2026-06-10).

- **Cloud Sync OAuth / Connect Flow** (OSS): one-click GitHub/Google connect, headless paste-code sign-in — clawmetry#3375, #3380, #3381 (merged 2026-06-28/29). Watching: does this reduce the "can't connect" support burden?

- **Navigation Redesign: Beginner-First Sidebar** (OSS): Phase A (#3458, merged 2026-07-02) + Phase B session deep-dive (#3473, merged 2026-07-02).

- **Audit Log Foundation** (OSS): DuckDB-backed audit_log table + `/api/audit-log` — clawmetry#3420 (merged 2026-07-01). Prerequisite for team visibility and enterprise compliance story.

- **Cost Attribution Fix** (OSS): per-runtime cost rollup now correctly attributes family spend — clawmetry#3490 (merged 2026-07-02).

- **Security Hardening Sprint** (cloud, 2026-06-10): Stripe webhook signature verification (#1579), admin-token gate (#1585), cleartext machine fingerprint fix (#1660), real firmware SHA256 (#1665), cleartext security_posture fix (#1593). Solid sprint; watching for follow-up CVE reports.

- **Voice Stack** (cloud): OpenAI Realtime upstream (4× faster turns, #1594), streaming WS endpoint (#1580), semantic VAD (#1605) — all merged 2026-06-10 through 2026-06-12.

---

## Quiet noise (likely not signal)

- **Automated observability-gap issues** (clawmetry#2730, #3014, #2796): bot-generated from a harness audit of openclaw voice/talk lifecycle fields and nemoclaw inference config. Not user-reported; worth shipping eventually but not signal.
- **Internal roadmap EPIC issues with no reactions** (clawmetry#1032, #1038, #1522–#1524): DuckDB-everywhere, Redis hot cache, E2E encryption keychain — all appear to be founder-authored internal planning items, not inbound user requests.
- **One-off standard-library requests** (clawmetry#882 "More Claws support", clawmetry#881 "Remote approval gates" roadmap placeholders): Vague placeholder issues with no body detail beyond the roadmap promise text. Track via the real issues instead.

---

## ⚠️ Security flag (separate from roadmap)

**clawmetry-cloud#315 [P0] — Plaintext API key in `users.api_key` column**: The raw `cm_*` token is stored in cleartext alongside `api_key_hash`. Anyone with read access to the database can impersonate any user. This is not a roadmap theme — it should be fixed now, ahead of any feature work.

---

## Velocity check

| Metric | OSS | Cloud | Total |
|--------|-----|-------|-------|
| PRs merged (last 30d) | 602 | 259 | 861 |
| Issues analysed (open, user-signal labels) | 27 | 36 | 63 |
| HOT themes with shipped progress | 3/5 | — | partial |
| HOT themes fully closed | 0 | — | 0 |

- **What's absorbing the velocity**: OSS — entitlement API expansion (26+ `feat(entitlement)` PRs in the last 10 days, building the full tier/feature/runtime catalog, path, and batch endpoint family). Cloud — billing Stripe replatform (15+ PRs). Both are necessary infrastructure but neither directly closes a HOT user theme.
- **Themes HOT for 2+ weeks without closure**:
  - Surprise Bill Prevention: first raised **2026-03-06** (clawmetry-cloud#4) — **119 days open**, partially addressed
  - Team-Wide ROI: first raised **2026-05-06** (clawmetry-cloud#653) — **58 days open**, not meaningfully addressed
  - First-Run Activation [P0]: first raised **2026-05-28** (clawmetry-cloud#1189) — **36 days open**, not addressed
- **Honest read**: The product is shipping at very high velocity, but the user-pain themes that generate inbound noise are aging. The entitlement API and billing infrastructure being built are *prerequisites* for the monetization story — but they don't reduce the bill-shock complaints or fix the empty first-run screen. A user reading ClawMetry's changelog would see dozens of releases and zero resolution to their most common complaint.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency + corroborating HN/competitor signal. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed. Published weekly as a draft PR so the maintainer can accept, amend, or ignore — the paper trail of decisions is the point.
