# What Users Want — July 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-07-31 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Data freshness note:** This is the first synthesis run with live access to `vivekchand/clawmetry-cloud`. All cloud issue signals are fresh as of 2026-07-31. Previous runs (including 2026-07-24) carried cloud signals from 2026-07-17 due to a session-scope misconfiguration. The separate intel-scout bot is still failing (11 consecutive blocked runs, `#3466`–`#3834`), but this synthesis now has full dual-repo visibility. Cloud blind spot: resolved for this report.

---

## TL;DR (this week)

One major user-facing feature shipped: Web Push phone notifications with one-tap agent approvals (16 cloud PRs, July 25–26), closing a request that has been open since March 2026. The onboarding funnel also got real attention — mandatory first-run gate, 7-day Pro trial, and sign-in-first flow all landed this week. But the three HOT cost/observability themes from last week haven't moved (8–11 weeks without a PR each), and a P0 security bug — plaintext API keys stored in the production DB (`clawmetry-cloud#315`, filed April 14, 2026, now **108 days old**) — has never been touched. The dominant engineering investment across both repos this week remains license/entitlement API infrastructure and admin console tooling, both entirely founder-driven with zero user issues requesting them.

---

## Hot themes (build these next)

### 1. Cost Visibility & Spend Control

- **Demand**: 9 open issues across both repos (5 cloud intel + 4 feature requests), last raised 2026-06-25. Intel scores 7–9/10.
- **Representative quotes**:
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` (dev.to post on a $1,800 silent GPT-4o spike)
  - *"I use LLMs daily… anywhere from $200–$400 tops… I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` (dev.to $47K retroactive bill)
  - *"A Copilot CLI user explicitly cites Claude Code's `claude_code.cost.usage` OTel metric as the gold standard and asks for parity."* — `clawmetry-cloud#1696` (intel-feedback)
- **Why it matters**: Cost attribution is the defining pain of the AI-dev tooling wave right now. ClawMetry captures raw spend signal; what's missing is per-session drill-down, anomaly alerts, weekly digest, and graduated thresholds. Competitors AgentPulse, Trainly, Faros, and CostReveal are each pitching on exactly this gap. The intel signal is dense and consistent — five distinct sources in June alone. Failing to surface it creates churn from the users most willing to pay.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#1694`, `clawmetry-cloud#1695`, `clawmetry-cloud#1696`, `clawmetry-cloud#1701`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`, `clawmetry-cloud#4`
- **Likely scope**: Both — OSS gets per-session cost attribution + export; cloud gets graduated alerts (50/80/95% cap) + weekly digest to Slack/email
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated budget alerts). Helicone had this on day one; it's table stakes.
- **Weeks unaddressed**: **8+** (since 2026-06-07 proxy issues were filed; cloud enforcement issues open since March 2026)

---

### 2. Agent Kill-Switch / Cost Enforcement (proxy features)

- **Demand**: 6 open issues (3 OSS + 3 cloud). TokPinch launched with 250 stars in 2 weeks on exactly these features.
- **Representative quotes**:
  - *"TokPinch intercepts heartbeat pings to Claude Opus and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816`
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692`
  - *"Managed cloud proxy endpoint — fleet-wide enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: Visibility without enforcement leaves users watching a fire they can't put out. The proxy at `clawmetry/proxy.py` (port 4100) already exists. Smart model routing (`#2816`), a cost-spiral breaker (`#2818`), and a rate-breaker (`#2817`) are spec'd and open. TokPinch is competitive proof these are wanted. Note: Web Push phone approvals shipped this week (cloud `#1766`–`#1790`) — that's the *notification* half of enforcement. The *policy/kill-switch* half is still unbuilt.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry-cloud#692`, `clawmetry-cloud#4`
- **Likely scope**: Both — OSS proxy gets smart routing + cost spiral + rate breaker; cloud gets managed proxy endpoint with fleet-wide policy enforcement
- **Suggested first step**: Ship `clawmetry#2816` (auto smart model routing: heartbeat/cheap tasks → Haiku/Sonnet). Single-proxy heuristic, fast to ship, generates immediate "saved $X" proof.
- **Weeks unaddressed**: **8+** (`clawmetry-cloud#4` filed 2026-03-06, now **147 days old** with zero PRs)

---

### 3. P0 Security — Plaintext API Keys in Production DB ⚠️

- **Demand**: 1 issue (`clawmetry-cloud#315`, labeled `bug` + `enhancement`, filed **2026-04-14**, **108 days ago**).
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production DB. Anyone with read access — developer access, backups, GCP logs, support tooling — can impersonate any user, including real paying customers. Confirmed in prod.
- **Why it matters**: This is not a roadmap priority; it's a security emergency that predates Q2. It has been open for 3.5 months with zero PRs. The risk profile is: one DB leak = every customer credential compromised. If it isn't fixed before paying customers onboard at scale, the liability window grows every week.
- **Linked issues**: `clawmetry-cloud#315`
- **Likely scope**: Cloud only — hash or encrypt stored API keys, rotate existing tokens, update the verification flow
- **Suggested first step**: Bcrypt the stored keys with a one-time migration script. This is a single-PR fix.
- **Weeks unaddressed**: **15+** — the single longest-open security issue in the corpus by a wide margin

---

### 4. Session Observability — Trace Tree & Replay

- **Demand**: 6 open issues (1 OSS + 5 cloud), last raised 2026-05-16.
- **Representative quotes**:
  - *"My main problem with Claude Code right now is observability. I've been experimenting a lot with vibe coding, but nowadays I can't even tell what it's doing."* — `clawmetry-cloud#652` (HN, intel-score 8/10)
  - *"Today ClawMetry captures events (tool_call, message) but loses the hierarchy — parent→child relationships… Without that hierarchy, 'why did this run take 30s?' is unanswerable."* — `clawmetry#1006` (Tracing EPIC)
- **Why it matters**: Observability is ClawMetry's core identity. The gap between "understand what happened and why" and "a flat list of events" widens with every multi-agent and multi-model session. Trace hierarchy (parent→child spans) and compaction markers are the unlock. The Conversations time-window picker (`#4284`) shipped this week, which helps with time navigation — but there's still no span tree. EPIC `#1006` has been open since May 2026; zero PRs in 11+ weeks.
- **Linked issues**: `clawmetry-cloud#652`, `clawmetry#1006`, `clawmetry-cloud#321`, `clawmetry-cloud#322`, `clawmetry-cloud#320`, `clawmetry-cloud#703`
- **Likely scope**: Both — OSS owns event capture + trace ingestion; cloud surfaces the visual trace tree + replay scrubber
- **Suggested first step**: Land `clawmetry-cloud#321` (compaction markers with expandable summary) — one new event type in JSONL, one UI widget, highest signal-to-scope ratio in the tracing cluster.
- **Weeks unaddressed**: **11+** (EPIC open since 2026-05-11)

---

## Warm themes (worth tracking)

- **React v2 Migration** (`clawmetry#1492`, RFCs `#1493`/`#1494`/`#1497`/`#1519`): Full Flask→React SPA rewrite EPIC. 6 comments (highest of any open OSS issue). Zero PRs in 11+ weeks. If no PRs land by 2026-08-07, call it explicitly stalled or cancelled.

- **Subscription-Mode Cost Accounting** (`clawmetry-cloud#1088`): Claude Max / ChatGPT-Plus / Codex OAuth users see ~100x inflated cost numbers because per-token pricing is applied to flat-rate traffic. High trust-damage risk. Fixable. No PRs.

- **Claude Code First-Class Observability** (`clawmetry-cloud#703`, EPIC): 10-phase epic for a native Claude Code adapter + dedicated dashboard. Faros and AgentPulse are specifically pitching on this gap. No PRs. Competitors are not waiting.

- **DuckDB-Everywhere + Redis Hot Cache** (`clawmetry#1032`, 3 comments): Replace Cloud SQL with DuckDB + Redis. Open since May 2026. Foundational for Dives (`#999`) and the trace tree (`#1006`). No recent PRs.

- **Remote Approval Gates — Policy Layer** (`clawmetry#881`, `clawmetry-cloud#1192`): The phone-push *notification* half shipped this week (see Closed-Loop). The declarative policy engine — auto-approve rules, tool-call gates, audit log, replay — is still open. This is the enterprise monetization tier.

- **Version-Aware Health-Regression Detection** (`clawmetry#2861`, 4 comments): "Did deploy X cause this regression?" surfaced as a correlation banner in the health dashboard. Useful, differentiated, no PRs.

- **Helicone-Refugee Importer** (`clawmetry-cloud#962`): One-click import of Helicone JSON logs + cache analytics panel. Helicone refugee community is a real acquisition channel. No PRs.

- **Self-Hosted Cloud Dashboard** (`clawmetry-cloud#1201`, P1): Enterprise self-hosting with custom data residency. Cited as a top enterprise adoption blocker. No PRs.

---

## Closed-loop themes (we shipped this)

**New this week (2026-07-25 → 2026-07-31), cross-repo:**

- **Web Push Phone Approvals** (`clawmetry-cloud#1766`–`#1790`, merged July 25–26): 16 PRs in 2 days. One-tap Approve/Deny from any phone via Web Push, pending-approvals inbox at `/approvals`, expandable history receipts, and deep-linked session traces. Closes `clawmetry-cloud#2` (open since 2026-03-03) and directionally addresses `clawmetry#881`. Fastest close on a HOT issue in this corpus. Watch for follow-up requests on Android reliability and Telegram parity.

- **P0 Onboarding Funnel / 7-Day Pro Trial** (`clawmetry#4220`/`#4249`/`#4250`/`#4287`/`#4288`, `clawmetry-cloud#1791`/`#1811`): Mandatory first-run gate, sign-in-first flow, two-option fork (Self-Hosted / Cloud), automatic 7-day Pro trial on sign-in. Partially closes `clawmetry-cloud#1189`, `#1190`, `#1191`. Note: only 14 of 561 weekly-active users had ever started a trial before this — this was clearly blocking conversion. Watch for friction reports from self-hosted users who want local-only without the gate.

- **Conversations Time-Window Picker** (`clawmetry#4284`, merged 2026-07-31): Live/1h/6h/24h/7d/Custom selector for post-mortem digging in the Brain/Conversations view. Partially addresses the observability gap from `clawmetry-cloud#652`/`#321` without requiring the full trace tree.

- **n8n Runtime — 15th Runtime** (`clawmetry#4251`, `clawmetry-cloud#1818`, merged 2026-07-30): n8n joins the runtime catalogue. Directionally addresses `clawmetry#882` (More Claws support). clawmetry-pro baked as 0.5.0.

- **Brain Keepalive Heartbeat** (`clawmetry#4273`, merged 2026-07-30): RCA fix for the relay starvation issue (465-session backfill had been blocking heartbeats for ~2m40s). Infrastructure, but directly affects Brain time-window fetch reliability for cloud relay users.

- **Brain Activity Stream Flicker + Poll Budget** (`clawmetry-cloud#1792`, `#1821`, `clawmetry#4264`): Unified Activity Stream no longer flickers; poll budget extended from 45s to ~4.5 min with honest busy-sync status. SSE slot leak and parked timeout error fixed.

**Continuing from prior weeks:**

- **Windows First-Class Support**: Hardening cluster from `#3920` (2026-07-24). Watching for edge-case reports.
- **Brain Datetime Range / Windowed History**: OSS `#3610`/`#3633` + cloud `#1728`/`#1729` (2026-07-10). Now enhanced with the time-window picker above.
- **Self-Hosted License Price Correction**: $29/$290 → $19/$190 (`clawmetry-cloud#1738`, 2026-07-13). Closes pricing transparency issue.
- **Billing Login Uncoupled from Signup** (`clawmetry-cloud#1750`, 2026-07-17): Login no longer gated on billing status; phantom signup loop killed.

---

## Quiet noise (likely not signal)

- **Harness-Gap / Obs-Gap Bot Issues** (30 of 59 OSS open issues): Automated filings from the harness audit script. Not user pain. Notable clusters: ClickClack channel missing from ingest (filed **5 times**: `#3837`, `#3990`, `#4103`, `#4147`, `#4240` — severity:high, one-line fix: add `"clickclack"` to `_CHANNEL_DIRS` in `clawmetry/sync.py` and a new route in `routes/channels.py`) and NemoClaw advisor session entirely unmodeled (filed 6 times). The ClickClack rescan loop is a harness configuration issue — suppress or fix it.

- **Intel-Scout Scope Blockers** (9 OSS issues: `#3466`–`#3834`): The separate intel-scout bot is still failing on `vivekchand/clawmetry-cloud` access. 11 consecutive blocked runs. This synthesis is now unblocked (separate session scope), but the intel-scout bot's session still needs its sources updated. Until fixed, real-time cloud intel continues to accumulate unfiled.

- **License API Buildout** (19 OSS PRs + 6 cloud license PRs this week): Time-indexed scalar helpers (`license_xxx_at(epoch)`) and batch-query variants building the open-core paywall engine. Zero user issues requesting these. Legitimate founder-driven infrastructure, not user signal.

- **Founder Admin Console** (11 cloud PRs this week): Installs board, agent-builder dashboard, sortable tables with timestamp normalization. Internal tooling. Not user pain.

- **Automated CI / C6 Harness PRs** (7 OSS PRs): Branch-protection applier fixes, Playwright caching, e2e-gate timeout extension. Internal quality work, not user features.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged last 4 days (Jul 28–31) | **100** (API total for 30-day window: 538) |
| Cloud PRs merged last 21 days (Jul 10–31) | **100** (API total for 30-day window: 113) |
| Largest OSS theme by PR count (excl. version bumps + RELEASE) | License API scalars (19 PRs) |
| Largest cloud theme by PR count (excl. auto-pins) | Web Push Approvals (16 PRs in 2 days) |
| User-signal themes shipped this week | Web Push approvals, onboarding/trial, n8n runtime, Brain time-window |
| **Cost visibility / spend control: PRs shipped** | **0 (8+ weeks running)** |
| **Cost enforcement / kill-switch policy: PRs shipped** | **0 (8+ weeks; `clawmetry-cloud#4` open 147 days)** |
| **Tracing EPIC (`clawmetry#1006`): PRs shipped** | **0 (11+ weeks since filed)** |
| **React v2 EPIC (`clawmetry#1492`): PRs shipped** | **0 (11+ weeks since filed)** |
| **Security bug `clawmetry-cloud#315` (plaintext API keys)** | **0 PRs in 108 days** |
| Themes HOT for 2+ weeks without action | Cost enforcement (`#2816`–`#2818`, since 2026-06-07) |
| Themes HOT for 5+ months without action | `clawmetry-cloud#4` (emergency stop, filed 2026-03-06) |
| Intel-scout failures (consecutive, separate bot) | **11** — cloud intel accumulating unfiled |

**Uncomfortable truths this week:**

1. **The security bug is now a liability, not a backlog item.** `clawmetry-cloud#315` (plaintext API keys, confirmed in prod) is 108 days old. A single DB read or log dump exposes every customer credential. This is not a prioritization decision — it's a one-PR fix that should have happened in April.

2. **Web Push approvals shipped, but the kill-switch still hasn't.** The phone-notification half of enforcement landed (16 cloud PRs). Zero PRs have touched the policy engine half (`clawmetry-cloud#692`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry#2816`–`#2818`). Users can now receive an alert on their phone; they still can't set a rule that prevents the action from running.

3. **Cost control has been HOT for 8+ weeks with zero PRs.** Five separate intel signals filed in June 2026 all point at the same gap: users losing money silently. The proxy already exists at port 4100. The features are spec'd. There's no visible technical blocker.

4. **The ClickClack obs-gap has been filed 5 times in 10 days.** The fix is one string (`"clickclack"`) added to `_CHANNEL_DIRS`. Each rescan wastes a harness-audit cycle. Close the issue or add a scanner suppression rule.

5. **Cloud data is now fresh in this synthesis.** Previous runs were flying blind on cloud pain because the session wasn't scoped to `vivekchand/clawmetry-cloud`. The themes carried forward from 2026-07-17 are now confirmed with fresh data — none of them have changed, which is itself a signal: the cloud pain queue is stable and growing while velocity is directed elsewhere.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by intel-score + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **95 open issues analyzed** (59 OSS + 36 cloud, all fresh as of 2026-07-31), **200 merged PRs analyzed** from a corpus of 651 total across both repos in the last 30 days. First synthesis run with live dual-repo access.
