# What Users Want — August 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-08-07 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** The roadmap-synthesis session is scoped to `vivekchand/clawmetry` only this run — `vivekchand/clawmetry-cloud` is inaccessible (same scope misconfiguration blocking the intel-scout bot for 12 consecutive runs, issues `#3466`–`#3834`). Cloud signals are carried forward from the 2026-07-31 synthesis, which had live dual-repo access. **Fix (one-time):** Add `vivekchand/clawmetry-cloud` to the roadmap-synthesis and intel-scout session scopes at https://code.claude.com.

---

## TL;DR (this week)

Evals got the most concentrated engineering investment in recent memory — 12 PRs in 4 days (Aug 3–6) shipping verdict chips, Score button per conversation, DeepEval integration, and deterministic evaluators. The spend-flow visualization also landed (“Where the money goes”). Neither was requested by a user issue. None of the five persistently HOT user themes moved: cost enforcement, the agent kill-switch, the P0 security bug, the tracing EPIC, and the React v2 migration each closed the week exactly where they opened it. The plaintext-API-keys security bug (`clawmetry-cloud#315`) is now **136 days old**.

---

## Hot themes (build these next)

### 1. Cost Control — Enforcement, Alerts & Weekly Digest

- **Demand**: 9+ open issues across both repos (5 cloud intel + 4 OSS proxy issues), last raised cloud intel 2026-06-25. Intel scores 7–9/10.
- **Representative quotes** (carried from 2026-07-31 synthesis; cloud repo inaccessible this run):
  - *“Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else.”* — `clawmetry-cloud#1683` (dev.to post, $1,800 silent GPT-4o spike)
  - *“I use LLMs daily… anywhere from $200–$400 tops… I just can’t figure how to burn that much money a month responsibly.”* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *“By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated.”* — `clawmetry-cloud#655` (dev.to $47K retroactive bill)
- **Why it matters**: The **spend-flow visualization shipped this week** — users can now see “where the money goes” at the node level. That’s the visibility half. What’s still missing: graduated budget alerts (50/80/95% cap), a weekly spend digest to Slack/email, and hard enforcement before the limit is hit. Visibility without enforcement is watching a fire you can’t put out. `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts) remains unstarted. Competitors Helicone and AgentPulse ship budget alerts on day one.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#1694`, `clawmetry-cloud#1695`, `clawmetry-cloud#1696`, `clawmetry-cloud#1701`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`, `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`
- **Likely scope**: Both — OSS proxy (port 4100) gets enforcement rules; cloud gets budget alerts + weekly digest
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts). The spend-flow visualization is now in place; the alert layer on top is the natural next PR.
- **Weeks unaddressed** (enforcement half): **9+** (up from 8+)

---

### 2. Agent Kill-Switch / Proxy Policy Engine

- **Demand**: 6+ open issues (3 OSS + 3+ cloud). TokPinch launched with 250 stars in 2 weeks on exactly these features. `clawmetry-cloud#4` is now **154 days old** (filed 2026-03-06).
- **Representative quotes** (carried):
  - *“TokPinch intercepts heartbeat pings to Claude Opus and routes them to Haiku or Sonnet… saving 10–50% API cost.”* — `clawmetry#2816`
  - *“An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch.”* — `clawmetry-cloud#692`
  - *“Managed cloud proxy endpoint — fleet-wide enforcement + observability without running anything locally.”* — `clawmetry-cloud#53`
- **Why it matters**: The phone-push approval notification shipped July 25–26. That’s the *alert* half. The *policy* half — smart model routing, dollar cost-spiral breaker, rate breaker — is still unbuilt. Users can see the fire and get a phone ping; they still cannot set a rule that prevents the action. `clawmetry#2816`–`#2818` have been open 9 weeks with zero PRs.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#4`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry-cloud#692`
- **Likely scope**: Both — OSS proxy gets the policy rules; cloud gets the managed proxy endpoint with fleet-wide enforcement
- **Suggested first step**: Ship `clawmetry#2816` (auto smart model routing: heartbeat/cheap tasks → Haiku/Sonnet). The proxy at port 4100 already exists. One PR, immediate “saved $X” proof.
- **Weeks unaddressed**: **9+** (OSS `#2816`–`#2818`); **22+** (`clawmetry-cloud#4`, filed 2026-03-06)

---

### 3. P0 Security — Plaintext API Keys in Production DB ⚠️

- **Demand**: 1 issue (`clawmetry-cloud#315`, labeled `bug`, filed **2026-04-14**, now **136 days old**).
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production database. Confirmed in prod. Anyone with read access — developer access, backups, GCP logs, support tooling — can impersonate any user.
- **Why it matters**: This is not a roadmap priority dispute — it is a security emergency that is now 19+ weeks old. Every week paying customers onboard while the exposure window grows. The fix is a single PR: bcrypt the stored keys, run a one-time migration script, update the verification flow. It has not been touched.
- **Linked issues**: `clawmetry-cloud#315`
- **Likely scope**: Cloud only
- **Suggested first step**: Bcrypt stored keys with a one-time migration. Estimated 1 day of work.
- **Weeks unaddressed**: **19+** (up from 15+ the week prior)

---

### 4. Session Tracing EPIC — OTel-Compatible Trace Tree & Span Hierarchy

- **Demand**: 5+ open issues (1 OSS EPIC + 4 cloud), last raised 2026-05-16. EPIC `#1006` open **12+ weeks**.
- **Representative quotes** (carried):
  - *“My main problem with Claude Code right now is observability. I’ve been experimenting a lot with vibe coding, but nowadays I can’t even tell what it’s doing.”* — `clawmetry-cloud#652` (HN thread, intel-score 8/10)
  - *“Today ClawMetry captures events (tool_call, message) but loses the hierarchy — parent→child relationships… Without that hierarchy, ‘why did this run take 30s?’ is unanswerable.”* — `clawmetry#1006`
- **Why it matters**: Observability is ClawMetry’s stated identity. The Brain session swimlane shipped this week; the spend-flow visualization shipped this week. Both are useful. Neither substitutes for a span tree. A flat list of events is not a trace. `clawmetry#1006` is 12+ weeks old with zero PRs; AgentPulse and Faros are actively pitching on exactly this gap.
- **Linked issues**: `clawmetry#1006`, `clawmetry-cloud#321`, `clawmetry-cloud#322`, `clawmetry-cloud#320`, `clawmetry-cloud#703`
- **Likely scope**: Both — OSS owns event capture + OTel ingestion; cloud surfaces the visual trace tree + replay scrubber
- **Suggested first step**: Land `clawmetry-cloud#321` (compaction markers with expandable summary) — one new event type, one UI widget, highest signal-to-scope ratio in the cluster.
- **Weeks unaddressed**: **12+** (up from 11+)

---

## Warm themes (worth tracking)

- **React v2 Migration** (`clawmetry#1492`, RFCs `#1493`/`#1494`/`#1497`/`#1519`): 12+ weeks open, **0 PRs**. Design handoff exists (`/Users/vivek/Downloads/design_handoff_clawmetry_v2/`). At 12 weeks with no commits against the branch, this is approaching stalled-or-cancelled. A decision — either a first PR or an explicit close — would clean up 5 open issues.

- **DuckDB-everywhere + Redis hot cache** (`clawmetry#1032`): Foundational for Dives (`#999`) and the trace tree (`#1006`). Open since May 12. 0 PRs.

- **Remote Approval Gates — Policy Layer** (`clawmetry#881`, `clawmetry-cloud#1192`): Push-notification half shipped July 25. Declarative policy engine (auto-approve rules, tool-call gates, audit log, replay) is still unbuilt. Enterprise monetization tier.

- **Subscription-Mode Cost Accounting** (`clawmetry-cloud#1088`): Claude Max / ChatGPT-Plus / Codex OAuth users see ~100x inflated cost numbers because per-token pricing is applied to flat-rate traffic. High trust-damage risk. 0 PRs.

- **Claude Code First-Class Observability** (`clawmetry-cloud#703` EPIC): 10-phase epic for native Claude Code adapter + dedicated dashboard. AgentPulse and Faros are pitching on this. 0 PRs.

- **Version-Aware Health Regression Detection** (`clawmetry#2861`): “Did deploy X cause this regression?” surfaced as a correlation banner. Useful, differentiated. 0 PRs.

- **Helicone-Refugee Importer** (`clawmetry-cloud#962`): One-click import of Helicone JSON logs + cache analytics panel. Real acquisition channel. 0 PRs.

- **ClickClack channel adapter** (`clawmetry#3837`, `#3990`, `#4147`, `#4240` + 2 earlier): Filed **6 times** by the harness scanner, each flagged `severity:high`. The fix is one string (`"clickclack"`) added to `_CHANNEL_DIRS` in `clawmetry/sync.py` plus a new route in `routes/channels.py`. The scanner will keep refiling this until it’s fixed or suppressed.

---

## Closed-loop themes (we shipped this)

**New this week (2026-08-01 → 2026-08-07):**

- **Evals major push** (`clawmetry#4505`/`#4509`/`#4557`/`#4487`/`#4492`/`#4493`/`#4496`/`#4572`, merged Aug 3–6): Verdict chips on Evals tab and transcript detail view, Score button per conversation, optional DeepEval metric engine (`clawmetry[deepeval]`), deterministic evaluators wired to real stored events, golden-suite rubric fix, free checks visible without a judge key, cloud-mode Score fix. 12 PRs in 4 days. No user issues requested this; founder-initiated push. Watch for: Android reliability reports, Telegram parity requests.

- **Spend-flow visualization** (`clawmetry#4494`/`#4513`, merged Aug 3): Node-wide AI spend flow (“Where the money goes”: context in → runtime → output out) + `thinking_trim` savings idea surfaced from measured spend. **Partially closes HOT Theme #1** — visibility delivered, enforcement still open.

- **Two new runtimes**: QM as 17th observable runtime (`clawmetry#4582`, Aug 7); xAI Grok as 18th runtime (`clawmetry#4547`, Aug 5). Now **18 runtimes** total. Directionally addresses `clawmetry#882`.

- **Trial-end hard-block + expired-trial banner** (`clawmetry#4566`/`#4444`, Aug 2–6): Trial-end hard-block enforcement (default ON) and an expired-trial banner with a buy path. Funnel closure.

- **Auth & daemon fixes** (`clawmetry#4579`/`#4495`, Aug 3–6): Auto-update root cause fix, self-host trial silently-failing bug, runtime-chip cloud redirect, and explicit sign-out sticks (no silent zero-click re-login).

- **Profile menu upgrade** (`clawmetry#4524`, Aug 3): Self-hosted upgrade sells the self-hosted license; legacy gateway settings entry points removed. Closes the self-hosted → paid conversion path.

- **Runtime feature parity** (`clawmetry#4464`/`#4472`, Aug 2): Real Agent Graph, Approvals (Claude Code hooks), Logs & Security now live for all 16 runtimes. Directionally closes `clawmetry#882`.

**Continuing from prior weeks (selected):**

- Web Push Phone Approvals (`clawmetry-cloud#1766`–`#1790`, Jul 25–26): Watching for Android reliability and Telegram parity follow-ups.
- n8n runtime — 15th runtime (`clawmetry#4251`, Jul 30).
- Onboarding funnel / 7-day Pro trial (`clawmetry#4288`/`#4287`, Jul 28–31).
- Brain time-window picker (`clawmetry#4284`, Jul 31).

---

## Quiet noise (likely not signal)

- **Harness-observability gap issues** (38 of 62 open OSS issues): Automated bot filings for `[obs-gap:openclaw]` and `[obs-gap:nemoclaw]`. These are not user pain; they are coverage gaps the harness bot identified. The **ClickClack obs-gap** (`severity:high`) has been filed 6 times in 18 days — it is the loudest automated signal in the repo by volume. One-line fix in `sync.py`.

- **Intel-scout scope blockers** (8 issues, `#3466`–`#3834`): The intel-scout bot still cannot access `vivekchand/clawmetry-cloud`. 12 consecutive blocked runs. Real cloud user pain is accumulating unfiled. Fix: add `vivekchand/clawmetry-cloud` to the bot’s session scope.

- **Entitlement API buildout** (19+ OSS PRs in the last 30 days): Time-indexed scalar helpers (`has_feature_at`, `missing_features_at_path_batch`, etc.) building the open-core paywall engine. Legitimate founder-driven infrastructure. Zero user issues requested these.

- **CI/C6 harness PRs** (~8 PRs this week): Branch-protection applier fixes, Playwright caching, e2e-gate guard and concurrency fixes. Internal quality work.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (Aug 1–7, estimated) | ~100 |
| OSS PRs merged (last 30d, total) | **601** |
| User-signal themes shipped (Aug 1–7) | 5 (evals, spend-flow viz, 2 runtimes, runtime parity) |
| Largest PR cluster (Aug 1–7, excl. bumps/RELEASE) | Entitlement API scalars (~20 PRs) — **0 user issues requested** |
| 2nd largest PR cluster | Evals push (~12 PRs) — **0 user issues requested** |
| **Cost enforcement / kill-switch: PRs shipped** | **0 (9+ weeks; `clawmetry-cloud#4` open 154 days)** |
| **Tracing EPIC (`clawmetry#1006`): PRs shipped** | **0 (12+ weeks)** |
| **React v2 EPIC (`clawmetry#1492`): PRs shipped** | **0 (12+ weeks — approaching stalled/cancelled)** |
| **Security bug `clawmetry-cloud#315` (plaintext API keys)** | **0 PRs in 136 days** |
| Themes HOT for 2+ weeks without action | Cost enforcement (`#2816`–`#2818`, since 2026-06-07) |
| Themes HOT for 5+ months without action | `clawmetry-cloud#4` (emergency stop, filed 2026-03-06, **154 days**) |
| Intel-scout failures (consecutive) | **12** — cloud intel accumulating unfiled |

**Uncomfortable truths this week:**

1. **The two biggest PR clusters had zero user-issue demand.** Entitlement API (~20 PRs) and Evals (~12 PRs) were both founder-initiated. That’s a legitimate call — founders know things that don’t show up in issues. But objectively, the product was shaped entirely by gut this week, not by user signal.

2. **The security bug is now 136 days old.** `clawmetry-cloud#315` (plaintext API keys, confirmed in prod) has had 0 PRs in 19+ weeks. A single DB read or log dump exposes every customer credential. This is not a prioritization decision anymore — it is a liability that grows every week paying customers onboard.

3. **Spend enforcement is the missing half of what just shipped.** The “Where the money goes” spend-flow visualization is a real step forward. Users can now see what they’re spending. They still cannot set a budget alert or trigger a kill-switch at 80% of limit. The most-requested user outcome — “stop before I go over” — is undelivered.

4. **The ClickClack gap has been filed 6 times.** Each scan generates a new `severity:high` issue. The fix is one string. The harness is spending real audit cycles on a known gap that has a one-line fix.

5. **Cloud repo is blind again.** The July 31 synthesis had live access to `vivekchand/clawmetry-cloud`. This week’s run does not. The same scope misconfiguration that has blocked the intel-scout bot for 12 consecutive runs is now also blocking the roadmap-synthesis run. Cloud user pain is carried forward from a week-old snapshot.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what’s already addressed — in either repo.

This run: **62 open OSS issues analyzed** (cloud inaccessible — signals carried from 2026-07-31 synthesis). **601 merged PRs** in the 30-day window from the OSS repo. No `intel-feedback` or `intel-pain` label exists in OSS; all demand signal is inferred from cloud issues (carried) and human-filed OSS enhancement issues. Note: 38 of 62 OSS issues are automated harness-gap filings, not user pain.
