# What Users Want — July 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-07-10 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

---

## TL;DR (this week)

The single loudest theme, sustained for 3+ months across both repos, is **silent cost spikes with no real-time attribution or alerts** — multiple independent developers have built their own tools to fill this gap, and at least three named competitors (AgentPulse, Faros, Trainly) are now directly targeting it. Shipping velocity is extremely high (~14 PRs/day in July) but the majority of that output is entitlement-API expansion and infra; the three HOT user themes have received only partial attention. The product is currently shaped more by platform buildout than by user signal.

---

## Hot themes (build these next)

### 1. Silent cost spikes — real-time attribution, graduated alerts, spend digests

- **Demand**: 10+ open issues across both repos (3 OSS + 7+ cloud), spike in intel hits in June 2026. Representative secondary signal: a 474-comment HN thread on token ROI visibility, a dev.to post on retroactive $47K bills, and three independent tools built because nothing existed.
- **Representative quotes**:
  - > "Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else." — clawmetry-cloud#1683 ([intel/pain] silent $1,800 API cost spike)
  - > "I use multiple AI tools for work... the annoying part was to track my costs... Everytime I had to visit each tool and its respective dashboard." — clawmetry-cloud#1694 ([intel/pain] "Tokens 4 Breakfast" DIY cost tracker)
  - > "I was running some autonomous agents and realized I had no idea how much I was spending until the bill hit." — clawmetry-cloud#1701 ([intel/pain] AgentWatch terminal monitor)
- **Why it matters**: Every OpenClaw user with a pay-as-you-go API key is exposed to runaway spending with no guard. Three competing tools (TokPinch, AgentWatch, "Tokens 4 Breakfast") launched within recent months directly targeting this gap. The fact that users are building their own solutions is the clearest possible product-market signal. ClawMetry already has the data layer — it just hasn't surfaced the alerting UX.
- **Linked issues**: clawmetry#2816, clawmetry#2817, clawmetry#2818, clawmetry-cloud#4, clawmetry-cloud#1484, clawmetry-cloud#1683, clawmetry-cloud#1694, clawmetry-cloud#1701, clawmetry-cloud#655, clawmetry-cloud#653
- **Likely scope**: Both — alerting logic is OSS (proxy); push delivery (Slack/email digests) is cloud. Subscription-mode cost accounting (clawmetry-cloud#1088) is cloud only, since it requires knowing a user's plan.
- **Suggested first step**: Ship graduated budget thresholds (50/80/95% of monthly cap) with in-dashboard banner + optional Slack webhook. This is already specced in clawmetry-cloud#1484 and pairs with the existing velocity-breaker work. One PR, no new infra.

### 2. Claude Code native observability — separate from OpenClaw, OTel-first

- **Demand**: 7 open cloud issues (competitor intel + user pain + Compliance API gap), 0 shipped PRs directly against this epic.
- **Representative quotes**:
  - > "My main problem with claude code right now is observability... I can't even tell what it's doing. It's still delivering me good code but I have no idea what it's doing or why." — clawmetry-cloud#652 ([intel/pain])
  - > "No standardized dashboards exist for token spend ROI analysis across a developer team. Users have to cobble together spreadsheets." — clawmetry-cloud#653 ([intel/pain] HN 474-comment thread)
  - > "Unlike the Claude Enterprise web product, Cowork and Claude Code activity is explicitly excluded from the Compliance API — confirmed across all plan tiers including Enterprise." — clawmetry-cloud#1695 ([intel/pain] Compliance API exclusion)
- **Why it matters**: Claude Code is now a distinct agent category with its own session format, its own billing, and — critically — its own telemetry dead-end: Anthropic's Compliance API explicitly excludes it, making OTel the *only* supported path. Three competitors (AgentPulse on HN with "Show HN: Real-Time Observability for Claude Code and Codex", Faros pitching "no cross-developer aggregation", Trainly offering free trace audits) have identified the same gap. ClawMetry has `dashboard_claudecode.py` but it is treated as an afterthought; the epic (clawmetry-cloud#703) has sat open since May 11.
- **Linked issues**: clawmetry-cloud#703, clawmetry-cloud#649, clawmetry-cloud#650, clawmetry-cloud#651, clawmetry-cloud#652, clawmetry-cloud#653, clawmetry-cloud#1695, clawmetry-cloud#1696
- **Likely scope**: Both — the OSS dashboard needs a first-class Claude Code tab/view; cloud gets team-wide aggregation and OTel export as the monetization wedge.
- **Suggested first step**: Rename/promote `dashboard_claudecode.py` to a first-class Blueprint (`/claude-code`), add a dedicated sidebar item, and ensure it surfaces session cost, tool call counts, and model usage from DuckDB. Clawmetry-cloud#703 has the full PRD.

### 3. Proxy enforcement gap — smart model routing + cost-spiral breaker

- **Demand**: 3 OSS enhancement issues (#2816, #2817, #2818) all filed 2026-06-07 citing a specific TokPinch competitor blog post. Cloud: #54, #53, #692.
- **Representative quotes**:
  - > "When OpenClaw sends a heartbeat ping or a short message like 'hi' to Claude Opus ($15/MTok input), TokPinch intercepts it and routes it to a cheaper model automatically. Zero config on the user's part." — clawmetry-cloud#54
  - > "ClawMetry's LoopDetector catches identical request hashes. The VelocityBreaker is token-based. TokPinch adds: cost spiral trigger on >$2 spent in 5 minutes + auto exponential-backoff pause." — clawmetry#2818
- **Why it matters**: ClawMetry's proxy (`clawmetry/proxy.py`, port 4100) already exists and handles budget limits and loop detection. The gap is two specific capabilities that TokPinch shipped and users are now asking for by name: (a) auto-routing cheap/heartbeat tasks to cheaper models, (b) a dollar-denominated cost-spiral breaker with exponential backoff. These are additive to existing code, not replacements.
- **Linked issues**: clawmetry#2816, clawmetry#2817, clawmetry#2818, clawmetry-cloud#54, clawmetry-cloud#53, clawmetry-cloud#692
- **Likely scope**: OSS (proxy.py) for the logic; cloud for the managed endpoint version (#53).
- **Suggested first step**: Add the dollar-based cost-spiral breaker to `proxy.py` (clawmetry#2818) — it's the highest-differentiation capability and requires only a new VelocityBreaker trigger condition. Smart routing (#2816) can follow.

---

## Warm themes (worth tracking)

- **Subscription-mode cost accounting**: 1 cloud issue (#1088), but affects every user on ChatGPT-Plus, Codex OAuth, or Claude Max — they see inflated cost numbers everywhere because per-token rates are applied to flat-rate traffic. Helicone refugees (#962) are specifically asking for this. Linked: clawmetry-cloud#1088, clawmetry-cloud#962.

- **OTel trace hierarchy / span tree**: 3 OSS issues (#1006, #2730, #3014). Today ClawMetry captures events but loses parent→child hierarchy. The Compliance API gap (HOT theme #2) makes OTel the only viable telemetry path for Claude Code, so this has strategic urgency beyond the user asks. Agent graph data layer shipped (#3544) but the trace tree UI hasn't. Linked: clawmetry#1006, clawmetry#2730, clawmetry#3014, clawmetry-cloud#1695.

- **Approvals / Remote control gates**: 3 issues (#881 OSS, #2 cloud, #1192 cloud). Active shipping progress in July (pre-exec gate #3589, deny-kill #3498). Steady demand, partly addressed. Worth watching for follow-up friction. Linked: clawmetry#881, clawmetry-cloud#2, clawmetry-cloud#1192.

- **Session timeline richness** (compaction markers, model-change annotations, full replay): 3 cloud issues (#320, #321, #322). Brain feed improvements shipped (v3 chat turns #3581, date-time filter #3610), but compaction markers and time-scrubber replay remain open. Low urgency, high delight potential. Linked: clawmetry-cloud#320, clawmetry-cloud#321, clawmetry-cloud#322.

- **Cron intention gap alerts** (push-notify when scheduled agent action fails silently): 1 cloud issue (#363). Cron is described as the "magic sauce" of OpenClaw. July fixes surfaced on-exit triggers and detached-run metadata (#3507, #3527, #3428) but the *alerting* (notify user when a cron silently fails to fire) is still open. Linked: clawmetry-cloud#363.

- **Version-aware health-regression detection**: 1 OSS issue (#2861, filed 2026-06-08). Surface a banner when latency/error rate spikes correlate with an OpenClaw version bump. "Error rate +180% since you upgraded to 2026.4.29." High value for users caught by upgrade instability. Linked: clawmetry#2861.

---

## Closed-loop themes (we shipped this)

- **Cost tab crashes / loading hangs**: addressed in clawmetry#3453 (merged 2026-07-02). Watching for follow-up reports.
- **Per-runtime cost attribution** (family sessions booked as openclaw): addressed in clawmetry#3490 (merged 2026-07-02). Watching.
- **Smart-routing savings surfaced in /api/usage**: addressed in clawmetry#3450 (merged 2026-07-01). Partial answer to HOT theme #3 (proxy routing) — the savings are now *visible*; the auto-routing logic itself is still open.
- **Global emergency-stop endpoint + proxy enforcement**: addressed in clawmetry#3445 (merged 2026-07-01). Addresses part of clawmetry-cloud#4 / clawmetry-cloud#692 (kill-switch). Full dollar-based spiral breaker still open.
- **Approvals pre-exec gate driving OpenClaw native gate**: addressed in clawmetry#3589 (merged 2026-07-08). Partially closes clawmetry-cloud#2 / clawmetry#881.
- **Brain activity feed (OpenClaw v3 + date-time filter)**: addressed in clawmetry#3581, #3586, #3610 (merged 2026-07-07–10). Follow-up from user complaints about empty Activity tab.
- **Beginner-first sidebar navigation**: addressed in clawmetry#3458, #3473 (merged 2026-07-02). Partially addresses clawmetry-cloud#1189 (first-run guided UX).
- **Additional runtime support (Pi, Deep Agents)**: addressed in clawmetry#3597 (merged 2026-07-09). Partial close of clawmetry#882 (More Claws support).
- **Voice/TTS gateway event ingest**: addressed in clawmetry#3578 (merged 2026-07-07). Partially addresses clawmetry#2730 / clawmetry#3014 (voice lifecycle obs gaps).

---

## Quiet noise (likely not signal)

- The `obs-gap:openclaw` and `obs-gap:nemoclaw` issues (#2730, #2796, #3014 in OSS) are automated harness-observability audit outputs, not user-filed pain. They describe internal coverage gaps, not user-reported breakage.
- OSS `[intel-scout]` issue #3466 is a bot filing noting that clawmetry-cloud write access isn't scoped — meta-noise, not user signal.
- OSS `[roadmap/later]` issues #881/#882 are reconciler-bot filings tracking roadmap promises, not organic user requests.
- All open OSS issues have 0 reactions — community engagement on GitHub itself is low; signal is primarily coming from the cloud intel cluster and external sources (HN, dev.to, competitor analysis).

---

## Velocity check

- **PRs merged (last 30 days, OSS only, clawmetry-cloud inaccessible this run)**: 139+ visible across pages 1–2 (covers July 1–10); June 10–30 data is on page 3+ and not included. Actual 30-day total is likely ~250–300.
- **Category breakdown of visible July PRs**:
  - Entitlement API expansion: ~60 PRs (43% of output) — *zero open user issues drive this*
  - Release/version bumps/i18n: ~25 PRs (18%)
  - Cost/usage fixes: 6 PRs
  - Sessions/session context: 5 PRs
  - Approvals: 3 PRs
  - Nav/UX: 3 PRs
  - Crons: 4 PRs
  - NemoClaw: 4 PRs
  - Process-control/infra: 5 PRs
  - Other (security, health, reports, agent-resources): 4 PRs
- **Themes shipped to directly in last 30 days**: 8 of the above closed-loop items.
- **Average issue→PR latency for shipped**: not calculable without creation dates for each shipped issue; the emergency-stop (#4 filed 2026-03-06, #3445 merged 2026-07-01) = ~117 days.
- **Themes HOT for 2+ weeks without action**:
  - **Claude Code native observability** (clawmetry-cloud#703): open since 2026-05-11 — 60 days, 0 PRs shipped.
  - **Graduated spend alerts** (clawmetry-cloud#1484): open since 2026-06-08 — 32 days, 0 PRs shipped. Intel pain hits in clawmetry-cloud#1683, #1694, #1701 are all from June 23–25, *after* this was filed.
  - **Smart model routing / cost-spiral breaker** (clawmetry#2816–#2818): open since 2026-06-07 — 33 days, 0 PRs shipped (though smart-routing savings are now surfaced in the UI via #3450).

**Uncomfortable truth**: The entitlement API build-out (~60 PRs in July, ~43% of total output) has no corresponding open user issues in either repo. It is either purely platform/monetization infrastructure, or the issues are being tracked internally and not publicly. Either way, it is the single largest consumer of engineering throughput this month and it is invisible to the user-signal → roadmap loop this document is meant to maintain.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency + intel-source quality. Cross-references the last 30 days of merged PRs (OSS only — cloud repo not in MCP scope this run) to detect what's already addressed. Cloud PRs are not included in velocity counts; cloud issue signal *is* included. Run every Friday 09:00 UTC.
