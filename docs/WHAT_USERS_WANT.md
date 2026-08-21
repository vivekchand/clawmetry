# What Users Want — August 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-08-21 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** `vivekchand/clawmetry-cloud` is inaccessible for the **14th consecutive run** (same scope misconfiguration). Cloud intel is carried forward from the 2026-07-31 synthesis. Real user pain in the cloud repo is accumulating unfiled and untracked. **Fix:** Add `vivekchand/clawmetry-cloud` to the roadmap-synthesis and intel-scout session scopes at https://code.claude.com. This is the one configuration change blocking dual-repo awareness.

---

## TL;DR (this week)

The orchestration capture sprint (sub-agents, workflows, parent edges) landed the prerequisite for Session Replay — making the replay viewer the most obvious unstarted build in the backlog. Cost enforcement entered its 11th straight week with 0 PRs while the proxy gained kill controls for 6 more runtimes and Cursor/Copilot got pre-execution gates. Enterprise security hardening shipped. The proxy policy enforcement gap (the piece that turns a rule into an actual block) remains open.

---

## Hot themes (build these next)

### 1. Cost Control — Enforcement, Budget Caps & Spend Digest

- **Demand**: 3 OSS issues (`clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`) + 5+ cloud intel issues carried from 2026-07-31 (cloud inaccessible). Reactions: 0 in OSS (these are developer-filed, not community-voted). Intel scores carried: 7–9/10.
- **Representative quotes** (carried from 2026-07-31 cloud synthesis):
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` ($1,800 silent GPT-4o spike)
  - *"I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled."* — `clawmetry-cloud#655` ($47K retroactive bill)
- **Why it matters**: Spend-flow visualization shipped Aug 3. Cost tab shows "$0 out-of-pocket" for flat-rate users. Those are the visibility layers. What's still missing: dollar-based cost-spiral breaker (trigger at >$2 in 5 min — `#2818`), rapid-fire request-rate breaker (`#2817`), and smart model routing heuristic (`#2816`). OSS issues filed 2026-06-07; zero PRs since. Helicone and AgentPulse ship hard budget caps on day one. Visibility without enforcement is watching a fire you cannot put out.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#1683`, `clawmetry-cloud#1694`, `clawmetry-cloud#1695`, `clawmetry-cloud#1484`, `clawmetry-cloud#653`, `clawmetry-cloud#655`
- **Likely scope**: Both — OSS proxy (`clawmetry/proxy.py`, port 4100) gets enforcement rules; cloud gets budget alerts + weekly spend digest
- **Suggested first step**: Wire the dollar-based spiral breaker into `proxy.py` — trigger at configurable threshold (default $2/5 min), log the block, surface it in the Alerts tab. The proxy intercept point exists; this is a policy rule, not new infrastructure.
- **Weeks unaddressed**: **11+** (up from 10+ last week; `clawmetry-cloud#4` emergency-stop filed 2026-03-06 is **167 days old**)

---

### 2. Session Replay / Orchestration Viewer

- **Demand**: 4 coordinated OSS issues (`clawmetry#4813`–`#4816`), all filed 2026-08-14. This week the data prerequisite shipped.
- **Representative context**: The orchestration capture sprint (Aug 14–21) landed sub-agent parent edges, prompt/reply/status fields, and live flow registries in DuckDB (`clawmetry#5008`, `#5013`, `#5014`, `#5016`, `#5032`). The data is now in the store. The viewer — replay tree UI, capture-mode display, inline subagent sidechains — is entirely unbuilt. `#4813` specifies the DB schema (`replay_events` table, `/api/replay-tree` endpoint); `#4815` covers the Claude Code mapper (Task/Agent/Workflow fanout); `#4816` covers the OpenClaw mapper (ACP replay stream + approvals audit). `#4814` has a `bot-pr-opened` label suggesting a PR was opened but not yet tracked here.
- **Why it matters**: Sessions with 20+ `Agent`/`Task` calls are the norm for power users; the flat linear transcript viewer is unintelligible at that scale. The orchestration data is now captured. The gap between "data in DuckDB" and "user can replay what the agent did" is purely a UI build — no further backend prerequisite. This is the highest-leverage feature given what already shipped this week.
- **Linked issues**: `clawmetry#4813`, `clawmetry#4814`, `clawmetry#4815`, `clawmetry#4816`
- **Likely scope**: OSS — the replay tree and viewer live in `routes/sessions.py` + the sessions frontend
- **Suggested first step**: Ship the `replay_events` table + `/api/replay-tree` endpoint from `clawmetry#4813`'s spec (the schema is written; it's a DuckDB table + one query endpoint). That unblocks `#4814` and `#4815` as follow-on PRs.
- **Weeks unaddressed**: **1** (filed 2026-08-14; data foundation just became available this week)

---

### 3. Secret Egress Host-Binding — Security Signal Gap

- **Demand**: 3 OSS issues (`clawmetry#4807`, `clawmetry#4863`, `clawmetry#5044`), all `severity:high`, filed 2026-08-14, 2026-08-15, 2026-08-21 (today). Automated harness filings, but represent a confirmed adapter gap: secret egress host-binding enforcement events from OpenClaw are not captured as a security signal in ClawMetry.
- **Why it matters**: The Security tab now tells the truth (`#4973` merged Aug 17) and the enterprise security review hardened egress (`#4972` merged Aug 21). But if the runtime is enforcing host-binding and ClawMetry doesn't ingest those events, the Security tab is honest about what it sees — not what's happening. Three high-severity filings in 7 days from the harness scanner suggests the gap is persistent across adapter versions.
- **Linked issues**: `clawmetry#4807`, `clawmetry#4863`, `clawmetry#5044`
- **Likely scope**: OSS — adapter extension in `clawmetry/adapters/openclaw.py`, specifically the `_openclaw_doctor_findings` method
- **Suggested first step**: Extend the OpenClaw adapter to ingest `host_binding_enforcement` events from the agent's security log and surface them on the Security tab as a new signal class.
- **Weeks unaddressed**: **1** (escalating — 3 filings in 7 days)

---

## Warm themes (worth tracking)

- **OTel/BYO-Agent Ingest** (`clawmetry#4779`, `clawmetry#4784`): OTLP receiver shipped (JSON, port 4318). Auto-discovery of OTel-emitting apps on the same machine (`#4784`, filed Aug 12) and the full SDK epic (`#4779`) are the natural follow-on. Neither has a PR. Filed 6-9 days ago; too early to call HOT.

- **OTel Trace Hierarchy / Span Relationships** (`clawmetry#1006`): Foundation shipped (OTLP ingest, Tracing tab, turn-anchored UI). Parent→child span rendering and distributed trace stitching remain unbuilt. The EPIC (`#1006`) is not closed. Watch for users filing this explicitly now that the Tracing tab exists.

- **React v2 Migration** (`clawmetry#1492` + RFCs `#1493`, `#1494`, `#1497`, `#1519`): **14+ weeks open, 0 PRs.** Design handoff exists locally. At 14 weeks with no commits, this is stalled or effectively cancelled. A decision either way — first PR or explicit close — would clean up 5 open issues.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): **15+ weeks open, 0 PRs.** DuckDB is the right backend; it just needs a prompt template + endpoint + chart rendering layer. Filed as PRD; full spec in private cloud repo.

- **LLM-as-Judge Evals** (`clawmetry#1619`): **14+ weeks open, 0 PRs.** Competitive differentiator vs. LangSmith/Langfuse (both cloud-host their evals). Phase 1 is local-only so no session data leaves the machine.

- **DuckDB-everywhere + Redis hot cache** (`clawmetry#1032`): Still open since May 12. The write-path (80x faster ingest, landed Aug 9) is done. The read-path hot cache is unbuilt.

- **E2E Robustness** (`clawmetry#4552`): 119 comments, active cron-driven tracker. Ongoing; not stalled.

- **More Runtimes** (`clawmetry#882`): Kimi (`#4978`), Exo (`#4942`), and Devin (`#4974`) all shipped this week — now at 22 runtimes. `#882` targets Cline, Hermes, and others still on the list.

- **Remote Approval Gates — Policy Enforcement** (`clawmetry#881`): Push-notification half shipped Jul 25. Tool risk classification + approve-and-remember shipped this week (`#4964`). The rule-enforcement bridge — wiring `clawmetry#4735`'s rule schema into `proxy.py` so a matched call actually pauses — is still the missing enforcement piece. Overlaps with HOT Theme #1.

- **P0 Security: Plaintext API Keys** (`clawmetry-cloud#315`, filed 2026-04-14): Cloud repo inaccessible — cannot verify current status. As of the 2026-07-31 read, this was **20+ weeks old with 0 PRs**. If still open, this is the most urgent unfixed item in the product. Estimated fix: 1 day (bcrypt stored keys + migration script).

---

## Closed-loop themes (we shipped this)

**New this week (2026-08-14 → 2026-08-21):**

- **Orchestration Capture** (`clawmetry#5008`, `#5013`, `#5014`, `#5016`, `#5032`, merged Aug 19–20): Sub-agent parent edges, prompt/reply/status, live flow registries. DuckDB now holds the data foundation for Session Replay. Addresses prerequisite for `clawmetry#4813`–`#4816`.

- **Stop/Pause for 6 more runtimes + Cursor/Copilot pre-execution gates** (`clawmetry#5009`, `#5031`, merged Aug 20): Partial close of the Agent Kill-Switch theme (`clawmetry-cloud#4`, `clawmetry#2817`). POSIX kill and proxy 503 now reach 6 additional runtimes. Cursor and Copilot get pre-tool-call gate hooks. Proxy enforcement policy in `clawmetry/proxy.py` still pending.

- **Needs-you attention layer** (`clawmetry#4916`, `#4922`, `#4924`, `#4929`, merged Aug 16): Which agent is waiting on you, across all runtimes. One-line wiring via `clawmetry hook attention`.

- **Tool risk classification + approve-and-remember** (`clawmetry#4964`, merged Aug 17): Call-level risk classification, `min_risk` policies, and approve-and-remember across all 21 runtimes. Partial close of `clawmetry#881` (remote approval gates).

- **Built-in monitors + delivery channels** (`clawmetry#4961`, merged Aug 17): Honest delivery channel list, mute/pin controls, per-monitor destination routing.

- **Runtime expansion: Kimi, Exo, Devin** (`clawmetry#4978`, `#4942`, `#4974`, merged Aug 16–17 and Aug 21): Three new runtimes in one week. Now at 22+ runtimes. Partial close of `clawmetry#882`.

- **Enterprise security hardening** (`clawmetry#4972`, `#4973`, merged Aug 17–21): Security tab now tells the truth. Third-party asset loads removed, egress closed, trust artifacts added. Preparation for enterprise reviews.

- **TLS/certifi fixes + gate hook fail-closed reliability** (`clawmetry#5030`, `#5034`, `#5035`, `#5038`, `#5040`, merged Aug 20): certifi bundled so every install has a trust store. Gate hooks now launch via the console script (fixes a fail-closed DoS where hooks silently didn't fire).

- **Pro paywall fix** (`clawmetry#5003`, `#5004`, merged Aug 19): Pro accounts no longer see the upgrade modal at boot. Daemon proxy no longer drops positional args.

- **Email sign-in fix** (`clawmetry#5002`, `#5027`, merged Aug 20): "Continue with email" on the login wall now works; it was calling a cloud-only route.

- **Sessions tab scoped to active runtime** (`clawmetry#5015`, merged Aug 21): `/api/transcripts` now scoped per runtime so per-runtime lists aren't starved by the global 50-row cap.

- **Alerts system stabilized** (`clawmetry#4903`, `#4913`, `#4936`, `#4937`, merged Aug 16): Every alert now has a destination. Alerts tab no longer wedges on "Loading alerts…" after enabling a rule.

- **Ghost sessions removed + honest heartbeat** (`clawmetry#4943`, `#4946`, merged Aug 16–17): Ghost sessions dropped from Sessions list. False SILENT heartbeat banner removed.

**Continuing from prior weeks:**
- Spend-flow visualization (`#4494`/`#4513`, Aug 3): visibility delivered, enforcement open (HOT Theme #1).
- OTel foundation: OTLP receiver, Tracing tab, turn-anchored UI, `clawmetry.trace` SDK (Aug 12–14).
- Desktop native installers: macOS .dmg, Windows Authenticode, Linux .deb, self-healing daemon (Aug 14–17).
- Rule Builder Phase 1 REST backend (`#4735`, Aug 11): enforcement bridge still pending.

---

## Quiet noise (likely not signal)

- **Automated harness-gap issues** (12 of 37 OSS enhancement issues, filed by `scripts/harness/audit.py`): Coverage gaps the scanner identified. All carry `automated` + `harness-gap` labels. Exception: the secret egress host-binding cluster (`#4807`, `#4863`, `#5044`) has 3 `severity:high` filings in 7 days — elevated to HOT Theme #3.

- **Entitlement API buildout** (~15 PRs in the last 30 days, `#4902`, `#4905`, `#4909`, `#4914`, `#4957`, `#4963`): Time-indexed scalar helpers for the open-core paywall engine. Legitimate infrastructure. Zero user issues requested these.

- **i18n syncs + dependency bumps** (`#4887`, `#4919`, `#4965`, `#4969`–`#4971`): Routine maintenance.

- **Intel-scout / roadmap-synthesis scope blockers** (`vivekchand/clawmetry-cloud` inaccessible): Real cloud user pain accumulating unfiled. The 14-run gap means at least 14 weeks of cloud signal are invisible to this document.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (Aug 14–21, excl. bumps/RELEASE/i18n/deps) | ~40 |
| OSS PRs merged (last 30d, estimated) | **~600+** |
| User-signal themes shipped (Aug 14–21) | 4 (Orchestration Capture, Kill controls +6 runtimes, Needs-you, Tool risk/approve-and-remember) |
| **Largest PR cluster (Aug 14–21, excl. bumps)** | Control-plane sprint (~20 PRs) — partial user-demand signal |
| Cost enforcement / proxy policy (HOT Theme #1) | **0 PRs, 11+ weeks** |
| Session Replay viewer (HOT Theme #2) | **0 PRs** (data foundation landed this week; viewer is the gap) |
| Secret Egress Security Signal (HOT Theme #3) | **0 PRs**, 3 `severity:high` filings in 7 days |
| React v2 EPIC (`clawmetry#1492`) | **0 PRs, 14+ weeks — stalled or cancelled** |
| ClawMetry Dives (`clawmetry#999`) | **0 PRs, 15+ weeks** |
| LLM-as-Judge Evals (`clawmetry#1619`) | **0 PRs, 14+ weeks** |
| Themes HOT 2+ weeks without action | Cost enforcement (`#2816`–`#2818`, since 2026-06-07) |
| Themes HOT 5+ months without action | `clawmetry-cloud#4` (emergency stop, filed 2026-03-06, **167 days**) |
| Cloud intel-scout / synthesis failures (consecutive) | **14** |

**Uncomfortable truths this week:**

1. **Orchestration capture shipped the prerequisite for Session Replay, but the viewer didn't follow.** `clawmetry#4813`–`#4816` describe exactly what to build now that the data is in DuckDB. The gap between "data captured" and "user can replay it" is a UI build. This is the most actionable gap in the current backlog.

2. **Cost enforcement is in its 11th week with 0 PRs.** The proxy now kills sessions across 12+ runtimes. It still doesn't enforce a dollar cap. These are two different code paths in `proxy.py` — one (SIGKILL) is built, one (policy budget check) is not. The infrastructure is there; it needs a rule that checks `cost_in_window > threshold` before forwarding.

3. **14 consecutive cloud-repo failures mean this document is partially blind.** The P0 security bug (`clawmetry-cloud#315`, plaintext API keys, confirmed in prod) may or may not be fixed — this synthesis cannot tell. Every week the scope misconfiguration persists is a week of real user pain invisible to this document. The fix is one configuration change.

4. **Three epics (v2 React, Dives, Evals) are past 14 weeks with 0 PRs.** At that age, these need an explicit decision: commit to a first PR or close the issues. Open issues without commits are not a roadmap; they're a graveyard that makes the backlog look more planned than it is.

5. **Enterprise security hardening shipped with no user-issue demand.** `#4972` (remove third-party assets, close egress, add trust artifacts) is legitimate preparation for enterprise sales. It's not user-signal-driven; it's founder-driven. That's fine — but the three HOT user-signal themes remain unaddressed while founder-gut work ships.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **37 open OSS enhancement issues analyzed** (cloud inaccessible — signals carried from 2026-07-31 synthesis). **~600+ merged OSS PRs** in the 30-day window. 0 `intel-feedback`, 0 `intel-pain`, 0 `bug` labels active in OSS. Demand signal is inferred from cloud issues (carried) and developer-filed OSS enhancement issues. All enhancement issues have 0 community reactions — this is an internally-driven backlog with no public upvote signal. Session Replay and Secret Egress themes are promoted to HOT based on issue velocity and data-layer readiness, not reaction count.
