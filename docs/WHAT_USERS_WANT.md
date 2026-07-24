# What Users Want — July 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-07-24 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Note on cloud data this run:** `vivekchand/clawmetry-cloud` is outside the MCP session scope this firing. Cloud issue signals are carried forward from the 2026-07-17 synthesis. OSS data is fresh as of 2026-07-24. The intel-scout scope blocker (see Quiet Noise below) is now at **11 consecutive failed runs** — this is a structural blind spot, not a one-off.

---

## TL;DR (this week)

The two loudest user themes — cost visibility and kill-switch enforcement — are unchanged from last week: still HOT, still 0 PRs for 7+ consecutive weeks. What did ship (97 OSS PRs in 7 days) was almost entirely founder-driven: 23 PRs building the entitlement/paywall engine, 19 CI-harness PRs, and 14 CLI scriptability PRs. None of these had open user-signal issues requesting them. The intel-scout pipeline has now failed 11 consecutive times due to a session-scope misconfiguration, meaning cloud user pain is accumulating untracked. Two structural problems on the table: the product is shipping at high velocity away from user signals, and the signal-capture pipeline itself is broken.

---

## Hot Themes (build these next)

### 1. Cost Visibility & Spend Control

- **Demand**: 9 open issues (3 OSS + 6 cloud, carried from 2026-07-17), last raised 2026-06-25. Intel scores 7–9/10.
- **Representative quotes**:
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` (dev.to post on $1,800 silent spike)
  - *"I use llms daily... anywhere from $200–$400 tops... I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` (dev.to $47K retroactive bill)
- **Why it matters**: Cost attribution is the defining pain of the AI-dev tooling wave. Competitors (AgentPulse, Trainly, Helicone refugees) are actively pitching on it. ClawMetry already captures raw signal; the missing surface is per-session attribution drill-down, anomaly alerts, weekly digest, and graduated spend thresholds. Winning this is table stakes for conversion.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1694`, `clawmetry-cloud#1701`, `clawmetry-cloud#1695`, `clawmetry-cloud#1696`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`
- **Likely scope**: Both — OSS gets per-session cost attribution + export; cloud gets graduated alerts (50/80/95% cap) + weekly digest to Slack/email
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts) in cloud, and surface per-session cost attribution in the OSS session deep-dive view.
- **Weeks unaddressed**: 7+ (since June 7, 2026 proxy issues filed; cloud issues older)

---

### 2. Cost Enforcement / Kill-Switch / Smart Routing

- **Demand**: 7 open issues (3 OSS + 4 cloud, carried from 2026-07-17). TokPinch launched with 250 stars in 2 weeks on exactly this feature.
- **Representative quotes**:
  - *"TokPinch intercepts [heartbeat pings to Claude Opus] and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816`
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692`
  - *"Managed cloud proxy endpoint — so users get enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: Visibility without enforcement leaves users watching a fire they can't put out. The proxy at `clawmetry/proxy.py` (port 4100) already exists. Smart model routing (`clawmetry#2816`), a cost-spiral breaker (`clawmetry#2818`), and a rate-breaker (`clawmetry#2817`) are spec'd and open. TokPinch is the competitive proof these are wanted. Zero PRs landed in 7+ weeks.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#54`, `clawmetry-cloud#53`, `clawmetry-cloud#692`, `clawmetry-cloud#4`
- **Likely scope**: Both — OSS proxy gets smart routing + cost spiral + rate breaker; cloud gets managed proxy endpoint with fleet-wide policy
- **Suggested first step**: Ship `clawmetry#2816` (auto smart model routing: heartbeat/cheap-task → Haiku/Sonnet). Single-proxy heuristic, fast to ship, generates immediate "saved $X" proof for users.
- **Weeks unaddressed**: 7+ (proxy issues filed 2026-06-07; cloud enforcement issues open since March 2026)

---

### 3. Session Observability — Trace Tree & Replay

- **Demand**: 6 open issues (1 OSS + 5 cloud, carried from 2026-07-17), last raised 2026-05-16.
- **Representative quotes**:
  - *"My main problem with claude code right now is observability. I've been experimenting a lot with vibe coding, but nowadays I can't even tell what it's doing."* — `clawmetry-cloud#652` (HN, intel-score 8/10)
  - *"Today ClawMetry captures events (tool_call, message) but loses the hierarchy — parent→child relationships… Without that hierarchy, 'why did this run take 30s?' is unanswerable."* — `clawmetry#1006` (Tracing EPIC)
- **Why it matters**: Observability is ClawMetry's core identity. The gap between "understand what happened and why" and "a flat list of events" is widening as sessions go multi-agent and multi-model. Trace hierarchy (parent→child spans) and compaction markers are the unlock. EPIC `#1006` is open since May 2026; no PRs landed this week.
- **Linked issues**: `clawmetry-cloud#652`, `clawmetry#1006`, `clawmetry-cloud#321`, `clawmetry-cloud#322`, `clawmetry-cloud#320`, `clawmetry-cloud#703`
- **Likely scope**: Both — OSS owns event capture + trace ingestion; cloud surfaces the visual trace tree + replay scrubber
- **Suggested first step**: Land `clawmetry-cloud#321` (compaction markers with expandable summary) — one new event type in JSONL, one UI widget, highest signal/scope ratio of the tracing cluster.
- **Weeks unaddressed**: 10+ (EPIC open since 2026-05-11)

---

## New Signal This Week

### 4. Entitlement/Paywall Transparency (EMERGING — watch closely)

- **Demand**: Zero user issues requesting this. **23 PRs shipped in 7 days** building the entitlement engine (tier-calculation APIs, paywall event store, feature/runtime gating on ~10 previously-open endpoints: evals, anomaly detection, error-triage, tool-policy, audit logs, health timeline).
- **Why it's a signal to watch**: Founder-driven monetization infrastructure is shipping at the highest velocity of any theme this week — faster than any user-facing feature. The gating PRs (#3804, #3805, #3812, #3813, #3815, #3816, #3823, #3824, #3828) apply paywalls to features users currently access for free, with no communication or docs PRs preceding them. This creates a support ticket risk: users will hit walls without understanding why. No user issues are requesting entitlement gates; several existing issues (#999, #1006, #1032, #1492) are waiting for the same engineering bandwidth that entitlement consumed this week.
- **Suggested action**: Before the gates go live, land a "why is this locked?" inline upgrade path (`clawmetry#3919` `upgrade_required_body_for_runtime` is a start). Document which features are gating and when.
- **Linked PRs this week**: `#3804`–`#3816`, `#3828`, `#3890`–`#3986` (entitlement engine cluster)

### 5. CLI Scriptability (WARM — emerging demand pattern)

- **Demand**: No explicit user issues, but 14 CLI PRs in 7 days all follow the same pattern: `--json` flags and new subcommands (`clawmetry diagnose`, `channels`, `features`, `runtimes`, `nodes`, `retention`, `bundle`, `extensions`). This is a consistent engineering bet that users want to pipe ClawMetry outputs into scripts, CI, and monitoring.
- **Why it matters**: If this bet is right, ClawMetry becomes the `jq`-friendly observability primitive for AI pipelines. If it's wrong, it's polish on an unpopular path. Open a discussion issue or track activation of `--json` flag usage to validate.
- **Linked PRs**: `#3818`, `#3820`, `#3827`–`#3832`, `#3845`, `#3849`, `#3870`, `#3873`, `#3879`, `#3981`

---

## Warm Themes (worth tracking)

- **React v2 Migration** (`clawmetry#1492`, 6 comments — highest comment count of any open issue): Full Flask→React SPA rewrite EPIC. RFCs open (#1493, #1494, #1497, #1519). No PRs this week. The 6 comments signal real internal/community interest; the 0 PRs signal it's blocked or deprioritized. If no PRs land next week, call it explicitly stalled.

- **Remote Approval Gates** (`clawmetry#881`): 1 issue, open since 2026-05-05. The ServiceNow AI Control Tower launch raised market urgency. Linked to cloud#1192 (full control plane EPIC). Worth escalating if kill-switch theme is addressed (they're adjacent).

- **Subscription-Mode Cost Accounting** (`clawmetry-cloud#1088`, carried): Claude Max / ChatGPT-Plus / Codex OAuth users see inflated cost numbers because per-token pricing is applied to flat-rate traffic. High trust-damage risk. Fixable.

- **Claude Code Native Observability** (`clawmetry-cloud#703`, carried): First-class adapter/dashboard for Claude Code sessions. Faros and AgentPulse are specifically pitching on this gap. The fleet view is the answer only if Claude Code is a first-class runtime.

- **DuckDB-Everywhere / EPIC** (`clawmetry#1032`, 3 comments): Replace Cloud SQL with DuckDB + Redis hot cache. Open since May 2026. Foundational for the Dives feature (#999). No recent PRs.

- **Version-Aware Health-Regression Detection** (`clawmetry#2861`, 4 comments): "Did deploy X cause this regression?" surfaced as correlation in the health dashboard. Useful, no PRs.

- **Windows First-Class Support** (shipped last week, watching): 6 PRs in coordinated release (`#3920`). Actively closing; watch for follow-up reports on edge cases.

---

## Closed-Loop Themes (we shipped this)

**New this week (2026-07-18 → 2026-07-24):**

- **ClickClack channel adapter**: Obs-gap filed 2026-07-20 (`clawmetry#3837`), fixed 2026-07-22 (`#3969`). **2-day turnaround** — fastest close in the corpus. Shows the obs-gap pipeline works when scoped correctly.
- **Gateway log surfacing**: `#3843` — gateway rotating log files now surfaced in OpenClawAdapter.
- **PTY relay fields in session list**: `#3874` — closes obs-gap for PTY relay detection.
- **NemoClaw advisor output-state classification**: `#3910` — obs-gap closed.
- **Plugin ingress lifecycle phases**: `#3887` — gateway plugin health now shows lifecycle phases.
- **Presence roster from `gateway.status`**: `#3891` — who's-online surfaced.
- **MCP app widget state**: `#3896` — pinned MCP widget state observable.
- **Brain duplicate replies**: `#3935` — OpenClaw replies no longer render twice in Activity feed.
- **Windows hardening (comprehensive)**: `#3920` release — uninstall crash, log streams, pip upgrade race, POSIX API crashes, HOME env patching. Windows now a first-class platform.
- **Trusted-proxy device pairing state**: `#3893` — surfaced in DetectResult.meta.

**Continuing from prior weeks:**

- **Auto-update fleet propagation**: Released in `#3624`/`#3625` (2026-07-10). Watching for `CLAWMETRY_AUTO_UPDATE=0` edge cases.
- **Brain datetime range / windowed history**: `#3610`/`#3633` OSS + cloud `#1728`/`#1729` (2026-07-10).
- **Connect OTP onboarding friction**: `#3777`/`#3778` (2026-07-17).
- **GDPR / account deletion**: `clawmetry-cloud#1681` (2026-06-23). EU compliance gap closed.
- **Multi-runtime expansion**: 14 runtimes now supported. `clawmetry-cloud#1727` (2026-07-09).
- **Self-hosted license price**: $29/$290 → $19/$190. `clawmetry-cloud#1738` (2026-07-13).

---

## Quiet Noise (likely not signal)

- **Intel-scout scope blockers** (9 open issues: `#3466`, `#3636`, `#3644`, `#3709`, `#3798`, `#3803`, `#3814`, `#3821`, `#3834`): The intel-scout bot has failed **11 consecutive runs** because `vivekchand/clawmetry-cloud` is not in its session scope. Cloud user issues are queuing up unfiled. This is a configuration fix — add `vivekchand/clawmetry-cloud` to the intel-scout session's repo sources. Until fixed, this roadmap synthesis is flying partially blind on cloud pain. **This is getting worse, not better.**

- **Harness observability audit bot issues** (`[obs-gap:*]` label): 7 open bot-generated issues tracking harness gaps (cloud-workspace conflicts, SQLite backup lifecycle, Skill Workshop proposals, Talk lifecycle). Good engineering hygiene, not user pain. Several closing via the obs-gap closure PRs above.

- **Roadmap-reconciler bot issues** (`[roadmap/*]` labels): Auto-generated consistency checks. Not user feedback.

- **Good-first-issue scan** (`#3842`): Bot-generated, 2026-07-20. Housekeeping.

- **Entitlement test infrastructure**: `#3933` (raise timeout 5→10 min) and related CI fixes — internal, not user signal.

---

## Velocity Check

| Metric | Value |
|--------|-------|
| PRs merged last 7 days (OSS only, cloud not accessible) | **97** |
| PRs merged last 30 days (OSS, prior synthesis) | ~399 OSS + ~42 cloud |
| Largest theme this week by PR count | CI/E2E harness (19 PRs) |
| Second largest theme | Entitlement engine (14 PRs) + CLI (14 PRs) tied |
| User-signal themes shipped this week | ~10 obs-gap closures, 0 on HOT cost themes |
| **Cost visibility / spend control: PRs shipped** | **0 (7+ weeks running)** |
| **Cost enforcement / kill-switch: PRs shipped** | **0 (7+ weeks running)** |
| **Tracing EPIC (#1006): PRs shipped** | **0 (10+ weeks since filed)** |
| **React v2 EPIC (#1492): PRs shipped** | **0 (10+ weeks since filed)** |
| Themes HOT for 2+ weeks without action | Cost enforcement (`#2816`–`#2818`, since 2026-06-07) |
| Themes HOT for 4+ months without action | **Cost enforcement** — `clawmetry-cloud#4` open since 2026-03-06, `clawmetry-cloud#54` since 2026-03-11, zero PRs |
| Intel-scout failures (consecutive) | **11** — cloud user pain not being captured |

**Uncomfortable truths this week:**

1. **The HOT themes haven't moved.** Cost visibility and cost enforcement have been at the top of this doc for 2+ weekly syntheses with zero PR movement. If they're not on the roadmap, remove them from HOT. If they are, something is blocking them that isn't visible in this report.

2. **The biggest engineering investment this week was monetization infrastructure, not user features.** 23 entitlement PRs landed in 7 days — more than any user-facing theme. This is a legitimate founder decision (monetization enables sustainability), but it consumes the same bandwidth that `#1006`, `#1492`, and the proxy features have been waiting for.

3. **The intel-scout pipeline is broken.** 11 consecutive scope failures mean cloud user issues are being lost. This report is systematically underweighting cloud pain until the configuration is fixed. The fix is one line: add `vivekchand/clawmetry-cloud` to the intel-scout session's `sources`.

4. **Entitlement gates are going in without docs or upgrade-path UX.** Features that were previously free are being gated — evals, anomaly detection, error-triage, tool-policy, audit logs, health timeline — all in one week. No user-communication PRs or docs PRs accompanied these. The first support tickets will come from users hitting walls they didn't know existed.

---

## How This List Is Built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by intel-score + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed.

This run: 36 open OSS issues analyzed (all `enhancement`; no `bug`/`intel-feedback`/`intel-pain` labels exist in OSS), 97 merged OSS PRs in the most-recent 7 days. Cloud repo was outside MCP session scope — cloud signals carried from 2026-07-17 synthesis. Cloud access needs to be added to restore full cross-repo coverage.
