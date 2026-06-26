# What Users Want — June 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-06-26 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

## TL;DR (this week)

Users are independently building their own cost dashboards (AgentWatch, Tokens 4 Breakfast, CostReveal) because they can't see spend across multiple tools or identify *what caused* a spike — not just how much it cost. This week's shipping has been dominated by entitlement API infrastructure (~15 commits for a pricing-comparison backend), which is internally necessary but addresses zero active user intel signals. Three proxy cost-protection features (clawmetry#2816, #2817, #2818) have been labeled `roadmap-now` for three weeks with no PR opened. Shipping is fast; it's just not pointed at the user pain.

---

## Hot themes (build these next)

### 1. Cross-tool / multi-provider cost tracking

- **Demand**: 5 open issues (0 OSS + 5 cloud), last raised 2026-06-25
- **Representative quotes**:
  - > "No standardized dashboards exist for token spend ROI analysis at company level." — HN 474-comment thread (clawmetry-cloud#653, intel score 9/10)
  - > "I use multiple AI tools for work and also my side projects, and the annoying part was to track my costs and token usage across tools. Everytime I had to visit each tool and its respective usage setting to check it and I was losing patience and also was getting hit by surprise limits." — Tokens 4 Breakfast author (clawmetry-cloud#1694)
  - > "The Copilot CLI's OpenTelemetry export is great for usage analytics, but it emits **no cost or billing metric**… the one thing teams actually want — 'how much did this cost' — is the one thing the telemetry can't express today." — Copilot CLI issue author (clawmetry-cloud#1696)
- **Why it matters**: Three independent developers built or bought their own multi-tool cost tracker this year (Tokens 4 Breakfast macOS app, AgentWatch terminal dashboard, CostReveal OpenAI-only SaaS). The common thread: "useful if that's all you need" — existing tools are too narrow. ClawMetry has the adapter architecture for Claude Code + Codex + Cursor + Copilot CLI + OpenClaw, but the README doesn't say so clearly and the Usage tab doesn't surface a prominent cross-tool total. This is a discovery + UX problem as much as a feature gap. Faros is explicitly marketing against "no cross-developer aggregation" — ClawMetry's exact value prop — and winning because of a messaging vacuum (clawmetry-cloud#650).
- **Linked issues**: clawmetry-cloud#653, clawmetry-cloud#1694, clawmetry-cloud#1696, clawmetry-cloud#1701, clawmetry-cloud#650
- **Likely scope**: Both — OSS for the runtime adapters and Usage tab hero metric; cloud for cross-developer aggregation and team-level spend roll-ups
- **Suggested first step**: Add "total cross-tool spend (last 30d)" as the top-line hero stat on the Usage tab; add one sentence to the README hero ("ClawMetry tracks Claude Code, Codex, Cursor, Copilot CLI, and OpenClaw in one dashboard"). Takes a day, closes the positioning gap before a competitor does.

---

### 2. Active cost protection — stop the bleed before the bill

- **Demand**: 6 open issues (3 OSS + 3 cloud), 3 of those labeled `roadmap-now` for 3+ weeks, 0 PRs opened
- **Representative quotes**:
  - > "Almost every cost tool on the market only answers *how much* while we were desperately asking *what caused it*. Those are completely different questions." — dev.to post with 15 reactions, 9 comments (clawmetry-cloud#1683)
  - > "Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else." — same post, describing a $1,800 spike from a silent autosave hook
  - > "$47K AI bills… no budget gate that checks the running total after each call." (clawmetry-cloud#655)
- **Why it matters**: The dev.to "$0 bug that cost $1,800" post got 15 reactions and 9 comments — unusually high engagement for a pain post. The demand is for two things: (a) attribution ("what caused it, not just how much") and (b) enforcement ("stop it before the bill"). OSS already has three issues with complete implementation plans labeled `roadmap-now`: auto model routing (clawmetry#2816, ~95% savings on heartbeat/cheap calls), rapid-fire rate breaker (clawmetry#2817), and dollar cost-spiral breaker (clawmetry#2818). Cloud companion: graduated Slack/email spend digest (clawmetry-cloud#1484). None has a PR. CostReveal is winning on attribution for OpenAI-only users; it has no multi-agent coverage. The gap to close is OSS enforcement + attribution storytelling.
- **Linked issues**: clawmetry#2816, clawmetry#2817, clawmetry#2818, clawmetry-cloud#1683, clawmetry-cloud#1484, clawmetry-cloud#4, clawmetry-cloud#655
- **Likely scope**: Both — OSS proxy enforcement (rate/cost/routing breakers in `clawmetry/proxy.py`); cloud for managed proxy endpoint (clawmetry-cloud#53) and spend digest notifications (clawmetry-cloud#1484)
- **Suggested first step**: Ship the dollar cost-spiral breaker (clawmetry#2818) — the simplest of the three, extends the existing `VelocityBreaker`, directly named by the market signal. The implementation plan is complete in the issue comment; open the PR today.

---

### 3. "Can't tell what Claude Code is doing" — native Claude Code observability

- **Demand**: 4 open issues across both repos, last raised 2026-05-07
- **Representative quotes**:
  - > "My main problem with claude code right now is observability. I've been experimenting a lot with vibe coding, but nowadays I can't even tell what it's doing. It's still delivering me value, but the trust on the company is going down and I've already started looking for alternatives." — HN comment (clawmetry-cloud#652, intel score 8/10)
  - > "Claude Code stores session logs locally on each developer's machine with no built-in mechanism for aggregating usage across developers, projects, or environments into a single dashboard." — Faros.ai blog, explicitly positioning against ClawMetry's exact value prop (clawmetry-cloud#650)
- **Why it matters**: AgentPulse shipped "Show HN: Real-Time Observability Dashboard for Claude Code and Codex" and has since expanded to orchestration features (clawmetry-cloud#649) — a competitor is shipping what ClawMetry should own. A user is on record saying they're looking for alternatives because the existing visibility is insufficient. ClawMetry's Claude Code telemetry coverage (fastMode, thinkLevel, identityTarget, authority tracking — all landed in June 2026) is technically solid, but there is no first-run experience for a new Claude Code user that surfaces this, and no dedicated "Claude Code" tab. The EPIC (clawmetry-cloud#703) has been open since May with no PRs.
- **Linked issues**: clawmetry-cloud#652, clawmetry-cloud#649, clawmetry-cloud#650, clawmetry-cloud#703, clawmetry-cloud#1189
- **Likely scope**: Both — OSS for a dedicated Claude Code tab and first-run UX; cloud for cross-developer fleet aggregation
- **Suggested first step**: Add a "Claude Code" first-class tab to the OSS dashboard (active sessions, cost this week, model distribution, top tools, authority violations). The underlying data is already in DuckDB; this is a routing + template PR. Close the positioning gap before AgentPulse does.

---

## Warm themes (worth tracking)

- **Helicone refugees** (clawmetry-cloud#962): Helicone has been in maintenance since 2026-03-03; buyers' guides actively warn against it. A concrete, time-sensitive refugee audience is looking for a drop-in replacement with prompt-cache analytics and multi-provider coverage. No PR or outreach has happened in 2+ months. The window is closing as refugees pick alternatives.

- **Enterprise OTel compliance positioning** (clawmetry-cloud#1695): An Elastic engineer filed a formal integration request because Claude Code is excluded from the Anthropic Compliance API — OTLP is the only telemetry path (7 comments in 20 days). ClawMetry already ships an OTLP receiver (`/v1/metrics`, `/v1/traces`, `/v1/logs`). This is a docs gap, not a feature gap — the "Claude Code for Enterprise compliance" setup guide doesn't exist yet.

- **Kill-switch / agentic safety enforcement** (clawmetry-cloud#692, clawmetry-cloud#1192, clawmetry#2): ServiceNow's AI Control Tower launched with kill-switch as the centrepiece at Knowledge 2026. Market narrative converging on "dashboards are observability — enforcement is what stops the $47k bill." OSS authority tracking landed observe-only (2026-06-25) as a foundation; kill-switch/approval-gate enforcement is still cloud-EPIC stage.

- **Multi-channel rendering bug** (clawmetry#503): Real user `jaimezapa` (April 2026) can't see Slack + WhatsApp simultaneously in the Flow panel. Labeled `needs-info` and stale for 3 months. Either close the info gap or close as won't-fix — aged stale `needs-info` looks like abandonment to external contributors.

- **Subscription-mode cost accounting** (clawmetry-cloud#1088): ChatGPT-Plus / Codex OAuth / Claude Max flat subscribers see grossly inflated cost numbers (100x off) because per-token rates are applied to prepaid traffic. This is a data-validity issue for a growing user segment, not a missing feature.

---

## Closed-loop themes (we shipped this)

- **Local-only Brain feed empty**: Daemon heartbeat spam flooded the events table in local-only mode, pushing real agent events out. Fixed and released in v0.12.529 via clawmetry#3317/3318 (merged 2026-06-25, OSS). Watching for follow-up reports.

- **Fleet-level agent spawn topology** (clawmetry#1012): Cross-session agent spawn graph (Tracing epic phase 6) shipped via clawmetry#3315 (2026-06-25, OSS). Part of the multi-agent observability story.

- **NemoClaw OCSF audit log ingest** (clawmetry#3299): OpenShell OCSF sandbox audit events now ingest into DuckDB and surface in `list_events()` via clawmetry#3309 (2026-06-24, OSS). Harness observability gap closure.

- **Tool-scope authority tracking** (observe-only): `AuthorityConfig` + `AuthorityChecker` now log out-of-scope tool declarations as `authority_violation` events in DuckDB (2026-06-25, OSS). First building block toward the kill-switch; no enforcement yet.

---

## Quiet noise (likely not signal)

- Automated harness-gap issues (clawmetry#2730, clawmetry#3014, clawmetry#2796): bot-filed observability gaps (OpenClaw voice fields, NemoClaw inference config). PRs were bot-opened; no user reactions or community engagement — medium-severity plumbing, not user-visible pain.
- i18n pseudolocale audit (clawmetry#2258): internal quality work, zero external requests.
- Most cloud `enhancement` issues from April–May have 0 reactions and 0 comments — founder-filed product specs without external validation. Worth tracking internally; not user signal.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS commits in last 30d | ~30+ (high throughput) |
| HOT themes shipped toward | 1 / 3 (heartbeat spam bug fix) |
| HOT themes with 0 PRs despite `roadmap-now` label | 3 (clawmetry#2816, #2817, #2818 — 3+ weeks stale) |
| Dominant shipping theme this week | Entitlement API infrastructure (~15 commits: pricing-comparison endpoints) — 0 user intel issues back this work |
| Multi-channel bug (#503) age | 3 months, `needs-info`, no movement |
| Average issue→PR latency (shipped items) | Fast for bugs (same-day); 3+ weeks and counting for user-intel features |

**The gap to name**: The entitlement API buildout this week (tier_spec, feature_spec, runtime_spec, what-if batch variants, capacity_diff_at) is purely founder-gut infrastructure for the cloud pricing page. It's necessary for monetization. But not one of the 5 user intel issues filed in the last week — all pointing at cost tracking and protection — has a single PR opened against it. The roadmap says `roadmap-now`; the shipping doesn't reflect it.

**Themes HOT for 2+ weeks without action**: cross-tool cost tracking (clawmetry-cloud#653 open since May), active cost protection (clawmetry#2816/2817/2818 labeled `roadmap-now` in early June), multi-channel bug (clawmetry#503 open since April).

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed. Generated every Friday 09:00 UTC.
