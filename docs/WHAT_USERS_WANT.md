# What Users Want — September 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-09-11 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** The roadmap-synthesis session is scoped to `vivekchand/clawmetry` only — `vivekchand/clawmetry-cloud` is inaccessible for the **17th consecutive run** (the Aug 14 doc reported 13). Cloud signals from the 2026-07-31 synthesis are carried forward and marked *[carried]*. Real cloud user pain continues to accumulate unfiled. **Fix (one-time):** Add `vivekchand/clawmetry-cloud` to the roadmap-synthesis and intel-scout session scopes at https://code.claude.com.

---

## TL;DR (this week)

The Session Replay EPIC (4 issues filed Aug 14) has been open for 4 weeks with 0 PRs — it describes the single biggest gap in the core transcript viewer. Security hardening is the clearest story of the last 30 days: workspace scanning, red-team corpus, supply-chain hook detection, and a stall-detector fix all landed. That's internal quality investment, not user-ask response. The three HOT user themes from August — cost enforcement, the agent kill-switch, and the P0 security credential bug — each enter September exactly where they entered August: 0 PRs, weeks more open. Cloud signals are now 6 weeks stale and degrading.

---

## Hot themes (build these next)

### 1. Session Replay — Runtime-Aware Transcript Viewer

- **Demand**: 4 open OSS issues (`clawmetry#4813`, `#4814`, `#4815`, `#4816`), all filed 2026-08-14. 0 reactions (no external users yet), but these are architecture-level issues filed because the current viewer is demonstrably broken for multi-agent sessions.
- **What they say**:
  - *"The transcript viewer is a single flat renderer driven by one endpoint (`/api/transcript/<id>`) that assumes a linear message list. It's runtime-blind — every runtime is coerced into the same flat shape. Sub-agent trees collapse. Workflow fanouts collapse. Mode changes vanish."* — `clawmetry#4813`
  - *"Claude Code is the highest-fanout runtime we support — memory + observed data confirm sessions with 20+ `Agent`/`Task` calls in this repo alone. Today the transcript viewer shows the parent turn with a single collapsed 'Task' tool chip — the child's actual work is never inlined."* — `clawmetry#4815`
  - *"Today the session UI shows **nothing** about how a session ran: Auto vs interactive vs plan vs `--dangerously-skip-permissions`. Claude Code emits `permission-mode` on every session but `_parse_v3_event` never consumes it."* — `clawmetry#4814`
- **Why it matters**: ClawMetry's strongest claim is "observe what your agent actually did." The transcript viewer is where that claim is either proved or disproved. For a Claude Code session with 20+ subagent hops, it currently proves nothing — it shows a flat list of parent turns with collapsed tool chips. Workflows are invisible. Permission mode is invisible. OpenClaw's ACP replay stream (the richest per-agent trace that exists) is completely ignored (#4816). Every user who opens a complex session sees noise.
- **Linked issues**: `clawmetry#4813`, `clawmetry#4814`, `clawmetry#4815`, `clawmetry#4816`
- **Likely scope**: OSS — the transcript viewer, `replay_events` table, and `/api/replay-tree` endpoint all live in OSS
- **Suggested first step**: Ship `clawmetry#4813` first (canonical schema + `replay_events` table + `/api/replay-tree` skeleton). It's the foundation the runtime-specific mappers (#4814–#4816) all depend on. The PR is architecturally defined and scoped; this is a sequencing issue, not a design ambiguity.
- **Weeks open without a PR**: **4**

---

### 2. Cost Control — Enforcement, Alerts & Weekly Digest *[carried from cloud, 13+ weeks]*

- **Demand**: 9+ open issues across both repos (5 cloud intel + 4 OSS proxy issues). Intel scores 7–9/10. *[carried from 2026-07-31 synthesis]*
- **Representative quotes** *(carried; cloud repo inaccessible)*:
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683`
  - *"I use LLMs daily… anywhere from $200–$400 tops… I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` ($47K retroactive bill)
- **Why it matters**: Spend-flow visualization shipped Aug 3. The "$0 out-of-pocket — covered by" label for flat-rate users shipped Aug 12. That's two layers of visibility delivered. What has not shipped in 13+ weeks: graduated budget alerts (50%/80%/95%), a weekly spend digest to Slack/email, and hard enforcement before the limit is hit. Visibility without enforcement is watching a fire you can't put out. Competitors Helicone and AgentPulse ship budget alerts on day one.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`, `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`
- **Likely scope**: Both — OSS proxy (port 4100) gets enforcement rules; cloud gets budget alerts + weekly digest
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts). The visualization layer exists; the alert layer is the natural next PR.
- **Weeks unaddressed** (enforcement half): **13+** (up from 10+ last week)

---

### 3. Agent Kill-Switch / Proxy Policy Engine *[carried from cloud, 26+ weeks]*

- **Demand**: 6+ open issues (3 OSS + 3+ cloud). `clawmetry-cloud#4` is now **~189 days old** (filed 2026-03-06).
- **Representative quotes** *(carried)*:
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692`
  - *"TokPinch intercepts heartbeat pings to Claude Opus and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816`
  - *"Managed cloud proxy endpoint — fleet-wide enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: Rule Builder Phase 1 (`#4735`, shipped Aug 11) gave the `/api/v2/rules` REST backend — the configuration layer. But the enforcement layer — `proxy.py` applying rules at the interception point (port 4100) to actually block/reroute/pause calls — is still not wired up. A rule you can define but the proxy doesn't enforce is a database row, not a kill-switch.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#4`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry-cloud#692`
- **Likely scope**: Both
- **Suggested first step**: Wire `#4735`'s rule schema into `proxy.py` so a rule with `action: block` actually intercepts calls at port 4100. The REST backend is in place; this is the enforcement bridge PR.
- **Weeks unaddressed**: **13+** (OSS); **27+** (`clawmetry-cloud#4`, filed 2026-03-06)

---

### 4. P0 Security — Plaintext API Keys in Production DB ⚠️ *[carried, 21+ weeks]*

- **Demand**: 1 issue (`clawmetry-cloud#315`, labeled `bug`, filed **2026-04-14**, now **~150 days old**).
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production database. Confirmed in prod. Anyone with read access — developer access, backups, GCP logs, support tooling — can impersonate any user.
- **Why it matters**: This is not a prioritization dispute — it is a confirmed security exposure that has been growing for 21+ weeks while paying customers continue to onboard. Estimated fix: 1 day (bcrypt stored keys, one-time migration script, update verification flow).
- **Linked issues**: `clawmetry-cloud#315`
- **Likely scope**: Cloud only
- **Suggested first step**: Bcrypt stored keys with a one-time migration.
- **Weeks unaddressed**: **21+** (up from 20+ last week)

---

## Warm themes (worth tracking)

- **Off-box / CI agent observability** (`clawmetry#4779`, `clawmetry#5679`): **Partially shipped this period.** `#5684` landed the ingest key + generated contract + setup prompt + live status (`/api/onboarding/ingest-status` via `#5730`). The full BYOA OTel ingest EPIC (`#4779`) and the off-box authentication architecture (`#5679`) remain open — SDK, auto-detection, and the promise that "any app already emitting OTel shows up on its own" are unbuilt. The front door is open; the auto-discovery isn't.

- **Queue Lanes UI** (`clawmetry#5721`): **New this week.** When `#5668` cut the unreachable Sub-Agents & Queue Lanes tab, one panel had no duplicate elsewhere: `/api/run-ledger` (lane rollup) has live data and zero UI consumers. `#5721` proposes a queue-lane rollup in the Crons tab. Low effort, addresses a live data gap.

- **React v2 / SPA migration** (`clawmetry#1492`, RFCs `#1493`/`#1494`/`#1496`/`#1497`/`#1519`): **16+ weeks open, 0 PRs.** Design handoff exists at `/Users/vivek/Downloads/design_handoff_clawmetry_v2/`. This is now long enough that a decision — either a first PR or an explicit close — would be more honest than keeping 5 open issues on the board. Silence here is its own signal.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): **17+ weeks open, 0 PRs.** NL question → SQL → chart over local DuckDB. One PR away from a differentiating demo. The backend endpoint and LLM prompt are the only missing pieces.

- **Tracing — full span hierarchy** (`clawmetry#1006`): The OTLP receiver, Tracing tab, and turn-anchored session UI shipped in August. What the EPIC actually asked for — parent→child span rendering and distributed trace stitching — is still unbuilt. Now that the display foundation exists, the first user to try cross-service distributed tracing will file this explicitly.

- **Evals — LLM-as-judge** (`clawmetry#1619`): Score-first reordering and per-session drill-down shipped Aug 14. The original ask (auto-scoring with LLM-as-judge on every completed session, configurable rubric, local) is still not built. The UI exists; the backend evaluator doesn't.

- **Windows bootstrap** (`clawmetry#5794`, field-failure): `no_distribution` failure on Windows Python 3.11 crossed the telemetry reporting threshold 2026-09-10. Automated, but real: this is a reproducible install failure that blocks a class of users from starting at all.

---

## Closed-loop themes (we shipped this)

**New since 2026-08-14 (this period's substantive merges):**

- **Ingest key + off-box observability foundation** (`clawmetry#5684`, `clawmetry#5730`, merged Sep 2026): The ingest key, generated `/api/v1/runs` contract, setup prompt, and live ingest-status endpoint (`/api/onboarding/ingest-status`) all landed. Partial close of `clawmetry#5679` (off-box auth) and `clawmetry#4779` (BYOA EPIC). The full SDK and auto-detection remain open.

- **Fish Audio — 24th chat channel** (`clawmetry#5055`, merged Sep 11): Fish Audio voice/telephony channel ingest added. ClawMetry now supports 24 chat channels.

- **Stall detector stops crying wolf** (`clawmetry#5836`/`#5840`, merged Sep 11): The daemon no longer reports every sleeping laptop as a stalled agent. Reduces false-positive incident noise that has been a low-level user complaint since the stall detector shipped.

- **Daemon reports its own failures** (`clawmetry#5752`, merged Sep 10): The daemon now surfaces the failures that stop it working — previously a broken daemon was silently unhealthy. Addresses a class of "ClawMetry shows nothing, can't figure out why" support pain.

- **Security hardening — workspace scan + red-team corpus** (`#5647`, `#5674`, `#5677`, `#5687`, `#5690`, `#5692`, `#5697`, `#5699`, `#5700`, `#5708`, merged Sep 2026): GitSpawn-class attacks, poisoned linked worktrees, npm supply-chain hooks, package.json install hooks, MCP injection, and workspace-kind classification all added to Guard + CI. No user issues requested these — internal security investment.

- **Dashboard accuracy fixes** (`#5593`, `#5596`, `#5607`, `#5617`, `#5636`, `#5643`, `#5651`, `#5656`, `#5662`, `#5678`, merged Sep 2026): Approvals queue stopped crying wolf; per-runtime sessions reach the hosted cloud tab; overview task counts fixed; sub-agent `runtime` field type fixed; OpenAI cache-read not double-counted; anomaly baselines served correctly. Ongoing correctness debt paid down.

- **Dead surfaces removed** (`#5603` Ask tab, `#5668` Sub-Agents & Queue Lanes tab, merged Sep 8): Two tabs users could never open successfully have been removed. Negative-feature shipping that improves first-run honesty.

- **Werkzeug debugger loopback-only** (`#5382`/`#5791`, merged Sep 10): Debugger now restricted to loopback bind. Security hygiene close.

**Continuing from prior:**
- Desktop App native installers (macOS .dmg, Windows, Linux .deb) — Aug 2026.
- Rule Builder Phase 1 REST backend (`#4735`) — Aug 11.
- OTLP receiver + Tracing tab foundation — Aug 12–14.

---

## Quiet noise (likely not signal)

- **Automated harness-observability gap filings** (~40+ open OSS issues, `[obs-gap:*]` labels): Harness scanner identifies coverage gaps; none represent direct user pain. The `[obs-gap:openclaw]` filed Sep 9 (`#5748`, connected provider account priority) is the current `severity:medium` example.

- **Intel-scout / roadmap-synthesis scope blockers**: Both bots blocked from `vivekchand/clawmetry-cloud` for **17 consecutive weekly runs**. Real cloud user pain is accumulating unfiled. Fix: add `vivekchand/clawmetry-cloud` to both bots' session scope at https://code.claude.com. This is the same note from the past 4 months. It has not been actioned.

- **Bot-plan-only tracking issues** (13 of 23 enhancement issues carry `bot-plan-only`): These are Claude-generated architectural plans waiting for a PR. They represent real features, but they don't represent external user demand — they're self-generated scope. Treat them as implementation backlog, not validated user asks.

- **Version-bump + RELEASE PRs**: ~60–70% of merged PRs are `chore: bump to v0.12.*` and `[RELEASE]` wrapper PRs. Healthy automation; not signal.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (last 30d, estimated excl. bumps/RELEASE/i18n/deps) | ~240–280 |
| User-signal themes shipped (last 30d) | **2** (ingest key / BYOA partial; stall detector false-positive fix) |
| **Largest PR cluster (last 30d, excl. bumps)** | Security hardening (~12 PRs) — **0 user issues requested** |
| **2nd largest cluster** | Dashboard accuracy fixes (~10 PRs) — **1 user issue referenced** (#5534) |
| Session Replay EPIC: PRs shipped | **0 (4 weeks open)** |
| Cost enforcement / kill-switch: PRs shipped | **0 (13+ weeks; `clawmetry-cloud#4` open ~189 days)** |
| P0 Security `clawmetry-cloud#315`: PRs shipped | **0 (~150 days)** |
| React v2 EPIC (`clawmetry#1492`): PRs shipped | **0 (16+ weeks — decision needed: ship or close)** |
| Dives EPIC (`clawmetry#999`): PRs shipped | **0 (17+ weeks)** |
| Themes HOT for 2+ weeks without action | Session Replay (4 wks), Cost enforcement (13+ wks), Kill-switch (27+ wks), P0 security (21+ wks) |
| Themes HOT for 5+ months without action | `clawmetry-cloud#4` (emergency stop, filed 2026-03-06) |
| Intel-scout/roadmap-synthesis failures (consecutive) | **17** |

**Uncomfortable truths this week:**

1. **Session Replay has been open 4 weeks with zero PRs — and it's describing a core product failure.** The transcript viewer is ClawMetry's moment of truth: "here's what your agent actually did." For any multi-agent Claude Code session, that moment currently fails. Sub-agent trees collapse. Workflow fanouts vanish. Permission mode is invisible. The 4-issue EPIC filed Aug 14 has a clear starting point (`#4813`), a clear sequence, and no design ambiguity. The only missing thing is a PR.

2. **Three-quarters of last 30d shipping is infrastructure / internal quality, not user-signal response.** Security hardening, accuracy fixes, dead-tab removals, stall-detector tuning — all legitimate work. But when you strip bumps, releases, and internal quality PRs, the ratio of user-signal→shipped is roughly 2 themes out of ~30+ distinct feature-adjacent PRs. That ratio is the same as last month.

3. **Cost enforcement is in its 13th week of 0 PRs.** The visibility half shipped (spend-flow Aug 3, subscription display Aug 12). The enforcement half — alerts, caps, digest — has waited through three synthesis cycles unchanged.

4. **The security bug is now ~150 days old.** `clawmetry-cloud#315` (plaintext `cm_*` keys in production) has 0 PRs. Every paying customer who has onboarded since April 14 has had their credential stored in cleartext. The estimated fix is 1 day.

5. **React v2 has been open 16 weeks with 0 PRs.** At this point it should be explicitly closed or a first PR should exist. Open epics with no activity are not a roadmap; they're archaeology. If v2 is cancelled, close the 5 issues so the board reflects reality.

6. **The cloud blindspot is now 6 weeks stale and worsening.** The last live read of `clawmetry-cloud` was 2026-07-31. This synthesis has carried those signals through 6 weekly runs. Every week the bot is blocked, cloud user pain accumulates unfiled. The fix is a single configuration change at https://code.claude.com that has been noted in every report since 2026-07-31 with no action.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **39 open OSS issues analyzed** (cloud inaccessible — signals carried from 2026-07-31 synthesis). **23 enhancement-label OSS issues** (0 intel-feedback, 0 intel-pain, 0 user-filed bug labels in OSS — all issue signal in OSS is either bot-generated or founder-initiated). **~240–280 substantive merged PRs** in the 30-day window from the OSS repo. The `bug` label in OSS contains predominantly automated harness-gap filings and field-failure telemetry, not user-reported defects.
