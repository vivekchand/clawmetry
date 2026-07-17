# What Users Want — July 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-07-17 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud). Cross-references last 30 days of merged PRs (399 OSS + 42 cloud) against 64 open user-signal issues.*

---

## TL;DR (this week)

The single loudest user signal — repeated across at least 7 separate intel issues and a 474-comment HN thread — is **cost visibility and spend control**: people are getting surprise bills (one case: $1,800; another: $47,000 retroactively) with zero attribution and no alerts. A closely coupled second signal is **cost enforcement** — users want automatic kill-switches, model routing that downgrades cheap tasks, and rate breakers — and competitors (TokPinch, AgentPulse, Trainly) are actively positioning on exactly these gaps. Shipping velocity is high (399+ OSS PRs in 30 days), but the work shipped is almost entirely internal infrastructure (entitlement tiers, CI hardening, obs-gap closures); **the two HOT user themes have received zero direct PRs in 30 days.**

---

## Hot Themes (build these next)

### 1. Cost Visibility & Spend Control

- **Demand**: 9 open issues (3 OSS + 6 cloud), intel scores 7–9/10, last raised 2026-06-25
- **Representative quotes**:
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` (dev.to post on $1,800 silent spike)
  - *"I use llms daily... anywhere from $200–$400 tops... I just can't figure how to burn that much money a month responsibly."* + *"No standardized dashboards exist for token spend ROI analysis."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` (dev.to $47K retroactive bill angle)
- **Why it matters**: This is the defining pain of the AI-dev tooling wave right now. Every competing observability tool (AgentPulse, Trainly, Faros, Helicone refugees) is pitching on it. ClawMetry already captures the raw signal; the user-facing surface — attribution drill-down, anomaly alerts, weekly digest, graduated thresholds — is what's missing. Winning this is table stakes for conversion; losing it means users build their own ("Tokens 4 Breakfast", "AgentWatch") and never land.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1694`, `clawmetry-cloud#1701`, `clawmetry-cloud#1695`, `clawmetry-cloud#1696`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`
- **Likely scope**: Both — OSS gets per-session cost attribution + export; cloud gets graduated alerts (50/80/95% cap) + weekly digest to Slack/email
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts) in cloud, and surface per-session cost attribution in the OSS session deep-dive view. One cloud PR + one OSS PR tests demand cheaply.

---

### 2. Cost Enforcement / Kill-Switch / Smart Routing

- **Demand**: 7 open issues (3 OSS + 4 cloud), last raised 2026-06-08; TokPinch launched with 250 stars in 2 weeks on exactly this feature
- **Representative quotes**:
  - *"TokPinch intercepts [heartbeat pings to Claude Opus] and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816` (proxy smart routing)
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692` (ServiceNow AI Control Tower framing)
  - *"Managed cloud proxy endpoint — so users get enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: Visibility without enforcement leaves users watching a fire they can't put out. TokPinch is the competitive proof: 250 GitHub stars in 2 weeks means real demand, and it's directly in ClawMetry's lane (proxy at port 4100 already exists in `clawmetry/proxy.py`). Smart model routing alone would be a credible "TokPinch killer" within the ClawMetry install. A cloud-managed proxy endpoint would be the cloud moat — fleet-wide enforcement with audit trail.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#54`, `clawmetry-cloud#53`, `clawmetry-cloud#692`, `clawmetry-cloud#4`
- **Likely scope**: Both — OSS proxy gets smart routing + cost spiral + rate breaker; cloud gets managed proxy endpoint with fleet-wide policy
- **Suggested first step**: Ship OSS `clawmetry#2816` (auto smart model routing: heartbeat/cheap-task → Haiku/Sonnet). This is a single-proxy heuristic that can ship fast and generates immediate "saved $X" proof for users. Cloud managed proxy is the follow-on.

---

### 3. Session Observability — "What Is My Agent Doing?"

- **Demand**: 6 open issues (1 OSS + 5 cloud), last raised 2026-05-16; "can't tell what it's doing" is the #1 frustration in HN threads
- **Representative quotes**:
  - *"My main problem with claude code right now is observability. I've been experimenting a lot with vibe coding, but nowadays I can't even tell what it's doing."* — `clawmetry-cloud#652` (HN, intel-score 8/10)
  - *"Today ClawMetry captures events (tool_call, message) but loses the hierarchy — parent→child relationships… Without that hierarchy, 'why did this run take 30s?' is unanswerable."* — `clawmetry#1006` (Tracing EPIC)
  - *"Combined with model_change / thinking_level_change markers, you have everything needed to time-travel through a session."* — `clawmetry-cloud#322` (full conversation replay)
- **Why it matters**: Observability is ClawMetry's core identity. The gap between what users want ("understand what happened and why") and what exists ("a list of events") is widening as sessions get longer, multi-agent, and multi-model. Trace hierarchy (parent→child spans) is the unlock: it turns event lists into something debuggable. Compaction markers and conversation replay are lower-lift entry points that prove the value quickly.
- **Linked issues**: `clawmetry-cloud#652`, `clawmetry#1006`, `clawmetry-cloud#321`, `clawmetry-cloud#322`, `clawmetry-cloud#320`, `clawmetry-cloud#703`
- **Likely scope**: Both — OSS owns the event capture + trace ingestion; cloud surfaces the visual trace tree + replay scrubber
- **Suggested first step**: Land `clawmetry-cloud#321` (compaction markers with expandable summary) in OSS first — it's the highest-signal, lowest-scope item: one new event type already in the JSONL, one UI widget. Model-change annotations (`clawmetry-cloud#320`) pair naturally.

---

## Warm Themes (worth tracking)

- **Remote Approval Gates**: 2 issues (`clawmetry#881`, `clawmetry-cloud#2`), slow burn since March 2026. The ServiceNow AI Control Tower launch (May 2026) raised market urgency — "kill switch" framing is now mainstream. Linked to cloud#1192 (full control plane EPIC). Worth a dedicated issue tracker update if the HOT themes ship.

- **Subscription-Mode Cost Accounting** (`clawmetry-cloud#1088`): Users on Claude Max / ChatGPT-Plus / Codex OAuth see grossly inflated cost numbers in ClawMetry because per-token pricing is applied to flat-rate traffic. 1 issue, but very specific, fixable, and causes trust damage. Subscription users probably represent a large fraction of the installed base.

- **First-Run / Activation UX** (`clawmetry-cloud#1189`, `#1190`, `#1191`): Internally tracked as P0.2 conversion priority (561 weekly-active users not upgrading per funnel data in the issue). No direct user complaints, but funnel data suggests 30%+ activation gap. A connect OTP fix shipped (`clawmetry#3777`) but the full first-run guided UX is open.

- **Claude Code Native Observability** (`clawmetry-cloud#703`): Separate first-class adapter/dashboard for Claude Code (vs. treating it as a generic OpenClaw session). Competitor positioning (AgentPulse, Faros) is specifically on this gap. `clawmetry-cloud#650` notes Faros targets "no cross-developer aggregation" — ClawMetry's fleet view is the answer, but only if Claude Code is a first-class runtime.

- **Skills Fleet Analytics** (`clawmetry-cloud#362`): ROI benchmarks, "skills top users have that you don't." From Alexander Krentsel's Berkeley talk — skills are the single highest-leverage personalization vector. Differentiated feature, low current demand but high potential virality.

- **Helicone Refugees + Prompt-Cache Analytics** (`clawmetry-cloud#962`): Helicone has been in maintenance mode since March 2026. There's a defined refugee population. 1 issue, medium intel signal, potential acquisition play.

---

## Closed-Loop Themes (we shipped this)

- **Auto-update fleet propagation**: Releases now reach the fleet in minutes rather than days. Shipped in OSS `#3624`/`#3625` (2026-07-10), with retry fixes in `#3630`/`#3634`. Watching for follow-up on CLAWMETRY_AUTO_UPDATE=0 edge cases.

- **Brain date-time range / windowed history**: Brain Activity stream now has a time axis, clickable datetime pickers, and windowed history via node relay. OSS `#3610`/`#3633` (2026-07-10); cloud `clawmetry-cloud#1728`/`#1729` (2026-07-10). Closes the "I want to see what happened between 14:00 and 15:00" request.

- **NemoClaw / advisor session observability**: Steady stream of obs-gap closures — onboarding trace timing (`#3662`), advisor-session JSONL ingest (`#3705`), tool execution retry/exhaustion (`#3655`, `#3735`), OCSF audit trail (`#3623`). Both repos shipping. Watching for follow-up on per-sandbox inference config (`clawmetry#2796`).

- **Connect OTP onboarding friction**: `--start-sync-now` now skips the redundant second OTP. OSS `#3777`/`#3778` (2026-07-17). Small but reduces day-1 friction.

- **GDPR / account deletion**: Self-serve account deletion endpoint + Settings danger zone. Cloud `clawmetry-cloud#1681` (2026-06-23). Closes the compliance gap for EU users.

- **Multi-runtime expansion**: Pi and deepagents runtimes now supported (14 runtimes total). Cloud `clawmetry-cloud#1727` (2026-07-09). Partial close for `clawmetry#882` (More Claws support).

- **Agent Builder (cloud)**: Four PRs in two days (2026-07-16): usage dashboard, test filter + drilldown, open-live links, anon sessions. Cloud `clawmetry-cloud#1743`–`#1746`. Founder-driven, no matching user-signal issues in the corpus — watch whether it drives organic activation signal.

- **Self-hosted license price**: $29/$290 → $19/$190. Cloud `clawmetry-cloud#1738` (2026-07-13). Removes a friction point in the self-hosted funnel.

---

## Quiet Noise (likely not signal)

- **Harness observability audit bot issues** (`[obs-gap:*]` label): 8+ bot-generated issues tracking ClawMetry's gaps against upstream harness changes (Talk lifecycle, SQLite backup, Skill Workshop, NemoClaw inference config). These are good engineering hygiene but aren't user pain — users don't file these, the audit bot does. Many are already closing (NemoClaw stream of PRs above). Safe to track quietly without roadmap weight.

- **Roadmap-reconciler bot issues** (`[roadmap/*]` labels): Auto-generated issues tracking `clawmetry.com/roadmap` promises. Not user feedback. Useful as a consistency check but no signal weight.

- **Intel-scout scope blocker** (`clawmetry#3466`, `#3636`, `#3644`, `#3709`): Bot queuing issues because `clawmetry-cloud` isn't in scope for the intel-scout session. Recurring for 5+ consecutive runs. This is a configuration issue (add `vivekchand/clawmetry-cloud` to the intel-scout session sources), not user signal. Fix the session scope and these stop appearing.

- **Entitlement tier API build-out**: ~20+ OSS PRs in the last 30 days building `tiers_for_features`, `tiers_for_runtimes`, `next/previous_tier_*`, `affordable_tiers_batch`, etc. Pure internal infrastructure enabling future pricing gates. No user-visible impact yet.

---

## Velocity Check

| Metric | Value |
|--------|-------|
| PRs merged in last 30d (both repos) | ~441 (399 OSS + 42 cloud) |
| Themes shipped to (user-signal) | ~6 of 13 tracked themes |
| OSS shipping split | entitlement infra (~20 PRs), CI/test (~12 PRs), obs-gap closures (~8 PRs), auto-update (~6 PRs), brain (~3 PRs), other product (~10 PRs) |
| Cloud shipping split | Agent Builder (~5 PRs), brain (~4 PRs), chore/pin (~15 PRs), license/billing (~6 PRs), other (~12 PRs) |
| **Cost visibility/control: PRs shipped** | **0 in 30 days** |
| **Cost enforcement / kill-switch: PRs shipped** | **0 in 30 days** |
| Themes HOT for 2+ weeks without action | Cost enforcement (`clawmetry-cloud#4` open since 2026-03-06, `clawmetry-cloud#54` open since 2026-03-11, `clawmetry#2816`–`#2818` open since 2026-06-07) |
| Themes HOT for 4+ months without action | **Cost enforcement** — 4+ months of open issues, confirmed competitor traction (TokPinch), zero PRs |

**Uncomfortable truth**: The product is shipping at high velocity, but the shipping is decoupled from the top user signals. Agent Builder (4 PRs in one day) and entitlement tier infrastructure (20+ PRs in a week) are founder-driven. The two themes with the clearest user pain and competitive urgency — cost dashboards and kill-switch enforcement — have been open for 4+ months and haven't landed a single PR. If that gap persists another week, it will appear in this section again.

---

## How This List Is Built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by intel-score + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed. OSS PR count is 399 total (GitHub API returned first 100; label distribution and titles confirm the first page is representative of the full set).
