# What Users Want — August 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-08-28 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note (14 consecutive runs):** `vivekchand/clawmetry-cloud` is inaccessible to the roadmap-synthesis bot. Cloud signals are carried forward from the 2026-07-31 synthesis, which was the last run with live dual-repo access. That data is now **28 days stale**. **Fix (one-time):** Add `vivekchand/clawmetry-cloud` to the roadmap-synthesis session scope at https://code.claude.com. Every week this stays broken, real cloud customer pain goes unfiled and unranked.

---

## TL;DR (this week)

The past two weeks shipped a serious amount of product: PR Trace (link a PR to the agent session that wrote it), team session sharing with org-key encryption, behavioral detectors beyond loops, repo AI-readiness scoring, and the git outcome join (cost per merged change, rework rate). These are real user-facing features — but **none of them were requested by open issues**. Meanwhile, two consecutive releases (0.12.759, 0.12.760) failed post-publish canary verification, meaning every new `pip install clawmetry` for several days downloaded a broken package. And the three persistently HOT user themes — cost enforcement, the agent kill-switch, and the P0 plaintext-key security bug — enter their 12th, 25th+, and 22nd weeks without a single PR. Shipping is fast. The gap between what ships and what users are asking for is widening.

---

## Hot themes (build these next)

### 1. Release Quality — Canary Verification Failures *(NEW this week)*

- **Demand**: 2 open P0 bugs filed this week, both automated by the canary harness.
- **What they say**:
  - `clawmetry#5119` (Aug 23): `0.12.760` on PyPI fails post-publish verification. Every new `pip install clawmetry` resolved this version. Canary run linked.
  - `clawmetry#5106` (Aug 22): `0.12.759` on PyPI fails post-publish verification. Same exposure window.
- **Why it matters**: Two back-to-back broken releases means the canary was either not gate-blocking merges or the merge gate was bypassed. Each broken version stays the default `pip install` until yanked or superseded. New users trying ClawMetry for the first time hit a broken install. That's the worst possible first impression — and unlike a dashboard bug, it's invisible until someone tries to install. If the canary exists but doesn't block, it's a warning sign with no teeth; if it does block but two releases escaped, the gate has a hole.
- **Linked issues**: `clawmetry#5119`, `clawmetry#5106`
- **Likely scope**: OSS — the canary, the gate in `scripts/e2e_gate.py`, and `verification/matrix.json`
- **Suggested first step**: Root-cause the escape path (gate misconfiguration, CDN propagation lag, race condition on publish→canary timing) and land the guard in the same PR as the fix, per the template in both issues. `#5133` (retry on CDN propagation lag) was merged Aug 23 — verify whether that was the root cause for both failures or only one of them.

---

### 2. Cost Control — Enforcement, Alerts & Weekly Digest *(HOT, week 12)*

- **Demand**: 9+ open issues across both repos (5 cloud intel + 4 OSS proxy issues); last raised cloud intel 2026-06-25. Intel scores 7–9/10. Reactions: highest in corpus.
- **Representative quotes** (carried from 2026-07-31; cloud repo inaccessible):
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` (dev.to post, $1,800 silent GPT-4o spike)
  - *"I use LLMs daily… anywhere from $200–$400 tops… I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` (dev.to $47K retroactive bill)
- **Why it matters**: The visibility stack is now complete — spend-flow visualization (Aug 3), "$0 out-of-pocket" display for flat-rate users (Aug 12), cost provenance labels on every figure (Aug 26). What's still missing: **graduated budget alerts** (50%/80%/95% cap triggers), a **weekly spend digest** to Slack/email, and **hard enforcement** before the limit is hit. You can see exactly how the fire is spreading. You still cannot put it out. `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts) remains unstarted. This is week 12 without a PR.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#1694`–`#1696`, `clawmetry-cloud#1701`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`, `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`
- **Likely scope**: Both — OSS proxy (port 4100) gets enforcement rules; cloud gets budget alerts + weekly digest
- **Suggested first step**: Wire the Rule Builder REST backend (`#4735`) into `proxy.py` so a `budget_cap` rule actually blocks calls at port 4100. The configuration layer is live; the enforcement bridge is one PR.

---

### 3. Agent Kill-Switch / Proxy Policy Engine *(HOT, 25+ weeks for cloud#4)*

- **Demand**: 6+ open issues (3 OSS + 3+ cloud). `clawmetry-cloud#4` is now **175 days old** (filed 2026-03-06).
- **Representative quotes** (carried):
  - *"TokPinch intercepts heartbeat pings to Claude Opus and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816`
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692`
  - *"Managed cloud proxy endpoint — fleet-wide enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: The Rule Builder REST backend landed Aug 11 (`#4735`). The behavioral detectors now go beyond loops — file blast radius, credential access, network egress, privilege change — all landed Aug 25 (`#5168`). You can see an agent doing something dangerous. You still cannot stop it via a declared policy. The detection is there; the interruption is not. `clawmetry-cloud#4` (emergency stop) has been open for 175 days.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#4`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry-cloud#692`
- **Likely scope**: Both — OSS proxy applies rules at port 4100; cloud adds managed proxy endpoint
- **Suggested first step**: Add `action: block | pause | reroute` enforcement to `proxy.py` using the rule schema from `#4735`. The detection side is complete; this is the action side.

---

### 4. P0 Security — Plaintext API Keys in Production DB *(HOT, week 22; cloud only)*

- **Demand**: 1 confirmed issue (`clawmetry-cloud#315`, filed 2026-04-14, **now 136 days old**). Labeled `bug`. Confirmed in production.
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production database. Anyone with developer access, backup access, GCP log access, or support tooling access can impersonate any paying customer.
- **Why it matters**: Not a prioritization question — this is a confirmed security exposure that every paying customer since 2026-04-14 is affected by. Estimated fix: 1 day (bcrypt stored keys + one-time migration script + verification flow update). The cloud repo is inaccessible this run so it is impossible to verify whether any PR was opened in the past 14 days. **If this has been fixed, close `#315` and it will drop off next week's synthesis. If it hasn't, this is now 22 weeks old.**
- **Linked issues**: `clawmetry-cloud#315`
- **Likely scope**: Cloud only
- **Suggested first step**: bcrypt stored keys, one-time migration, update verification flow. 1 day of work.

---

## Warm themes (worth tracking)

- **React v2 Migration** (`clawmetry#1492`, RFCs `#1493`/`#1494`/`#1497`/`#1519`): **15+ weeks open, 0 PRs.** Design handoff at `/Users/vivek/Downloads/design_handoff_clawmetry_v2/`. This needs an explicit decision: either a first commit or a close. Five open issues accumulating staleness.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): 16+ weeks open, 0 PRs. NL questions over local DuckDB agent data. DuckDB is in place; just needs the prompt template + endpoint + chart rendering layer.

- **DuckDB hot cache** (`clawmetry#1032`): Read-path hot cache still unbuilt. DuckDB self-repair shipped (`#5177`, Aug 25) and the write path got 80x faster (`#4669`, Aug 9). The read-path cache for Dives and the trace tree is the remaining open piece.

- **OTel Emitter Discovery** (`clawmetry#4783`): Auto-detect OTel-emitting apps on the same machine (process env scan for `OTEL_EXPORTER_OTLP_ENDPOINT`, port probing 4317/4318). Natural follow-on now that the OTLP receiver works.

- **Remote Approval Gates — Enforcement Bridge** (`clawmetry#881`, `clawmetry-cloud#1192`): Push-notification half shipped Jul 25. Rule Builder REST backend shipped Aug 11 (`#4735`). The missing piece: wiring rules into `proxy.py` so a matched call actually pauses. Overlaps with HOT Theme #3.

- **Session Replay EPIC** (`clawmetry#4813`–`#4816`, filed Aug 14): Canonical `replay_events` schema, `/api/replay-tree/` endpoint, and runtime-specific mappers for Claude Code and OpenClaw. The transcript viewer is currently runtime-blind — it collapses sub-agent trees, `Task`/`Workflow` fanout, YOLO vs plan mode, and approvals into a flat list. As agent complexity grows (sessions with 20+ sub-agents observed in this repo alone), a flat transcript is increasingly meaningless. 4 issues, 0 PRs. **New this fortnight — not in the Aug 14 synthesis.**

- **Helicone-Refugee Importer** (`clawmetry-cloud#962`): One-click import of Helicone JSON logs + cache analytics panel. Real acquisition channel. 0 PRs.

- **ClickClack channel adapter** (`clawmetry#3837` et al.): **7+ automated `severity:high` filings in ~5 weeks.** One-line fix: add `"clickclack"` to `_CHANNEL_DIRS` in `clawmetry/sync.py` + one route in `routes/channels.py`. Each new filing is a harness cycle on a known one-line gap.

---

## Closed-loop themes (we shipped this)

**New this fortnight (2026-08-14 → 2026-08-28):**

- **PR Trace** (`#5115`, `#5123`, `#5125`–`#5130`, `#5131`, Aug 23): `clawmetry trace capture` links a pull request to the agent session that produced it. Auto-wires via hook. Publishes an anonymized trace bundle to `trace.clawmetry.com`. Zero OSS user issues filed requesting this; founder-initiated. Watch for team adoption feedback.

- **Team session sharing + org key** (`#5217`, `#5221`, `#5224`, `#5225`, Aug 25): Seal a shared session with the organisation key so colleagues can read it in the browser without installing anything. Session titles now carried encrypted (the cloud stops seeing them). No OSS user issues requested this directly; relates to `clawmetry-cloud#53` (managed observability without local install). **Partial HOT Theme #3 close — observability layer; enforcement layer still open.**

- **Behavioral detectors beyond loops** (`#5168`, `#5200`, Aug 25): Detects file blast radius, credential access, network egress, privilege change — calibrated per runtime, ranked by spend-at-risk. Closes the detection half of the kill-switch story. Enforcement (actually pausing the agent) still unbuilt.

- **Repo AI-readiness scoring** (`#5214`, `#5223`, Aug 25): Scores how legible a repo is to an agent (CLAUDE.md, test harness, CI feedback loop) next to its stuck rate on the Harness tab. No OSS user issues filed requesting this.

- **Git outcome join** (`#5212`, `#5238`, Aug 26): Cost per merged change, rework rate, abandoned-session spend. Every figure carries its measurement basis; unavailable figures say `available: false` rather than `$0`. **Partial HOT Theme #2 close — cost visibility improved; enforcement still missing.**

- **Cost provenance labels** (`#5215`, `#5238`, Aug 26): Every dollar figure says whether it was measured, derived, or estimated. Replaces silent `$0.00` cost windows (the bug that motivated this work). **Partial HOT Theme #2 close — visibility complete; enforcement incomplete.**

- **DuckDB self-repair** (`#5177`, `#5182`, Aug 25): Invalidated DuckDB no longer bricks the daemon; it repairs itself instead of running silently broken. Closes a class of "empty dashboard" bugs.

- **E2E encryption hardened** (`#5150`, `#5151`, `#5159`, `#5160`, Aug 24): End-to-end encryption made an invariant (not an optimization). Browser-side decrypt path published. Account key removed from URL.

- **OTLP daemon-free intake** (`#5210`, `#5224`, Aug 25): OTLP receiver hardened into a daemon-free path. Teams that don't install the daemon locally can still send OTLP telemetry.

- **Hook coexistence** (`#5209`, Aug 25): ClawMetry never deletes a hook it didn't write (other tools, e.g., GitLens, write to the same `settings.json`).

- **Context windows per provider** (`#5202`, `#5207`, Aug 25): Context windows now sized per provider; instrumentation overhead measured and published.

- **New runtimes** (`#5226`/`#5230` OpenWorker, `#5263`/`#5264` Grok Bot, Aug 26): 27th and 28th supported runtimes. Also: Goose session-store path fixed for non-XDG platforms (`#5222`).

- **Session phase unification** (`#5211`, `#5220`, Aug 25): One session phase across every runtime (WO-1). Standardizes the session lifecycle across 28 adapters.

- **CI hardening wave** (`#5246`, `#5249`–`#5253`, `#5274`–`#5276`, `#5279`–`#5281`, Aug 26–28): SHA-pinned GitHub Actions across all workflows, least-privilege token scopes, untrusted inputs bound to env vars, Dependabot for npm. 10+ PRs. **Zero OSS user issues requested this.**

- **Canary fix** (`#5133`, Aug 23): `fix(canary): retry pip install in matrix jobs for CDN propagation lag`. This was the postmortem fix for the CDN-propagation window. The two P0 bugs (`#5106`, `#5119`) are still open pending resolution confirmation.

**Continuing from Aug 14 synthesis:**
- Tracing tab + OTLP receiver + `clawmetry.trace` SDK (Aug 12–14)
- Desktop App native installers: macOS .dmg, Windows Authenticode, Linux .deb (Aug 12–14)
- Rule Builder REST backend `#4735` (Aug 11)
- 80x faster fresh-install ingest `#4669` (Aug 9)

---

## Quiet noise (likely not signal)

- **Automated obs-gap filings** (~40+ open OSS issues): Harness scanner filings for `[obs-gap:openclaw]`, `[obs-gap:nemoclaw]`. Not user pain — coverage gaps the harness identified. The ClickClack filings (`severity:high`, 7+ in 5 weeks) are the actionable one: one-line fix.

- **Entitlement scalar buildout**: 40+ OSS PRs since Aug 1 building the open-core paywall scaffolding. Zero user issues requested any of this.

- **Bot scope blockers** (`#3466`+): The intel-scout and roadmap-synthesis bots have been blocked from `vivekchand/clawmetry-cloud` for **14 consecutive runs**. Real cloud customer pain is accumulating unfiled. Every week this stays broken, the signal-to-noise ratio in this document degrades.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (Aug 14–28) | ~100+ |
| OSS PRs merged (last 30d) | **~150+** (search returned 656 total, filter Aug 29–present) |
| User-signal themes shipped (Aug 14–28) | 2 partial closes (behavioral detectors; cost provenance) |
| **Largest PR cluster (Aug 14–28)** | CI hardening (~10 PRs) — **0 user issues requested** |
| **2nd largest cluster** | PR Trace feature (~8 PRs) — **0 user issues requested** |
| **Team session sharing** | Shipped — **0 OSS user issues requested** |
| **Cost enforcement / kill-switch: PRs shipped** | **0 (week 12 / week 25+)** |
| **P0 Security `clawmetry-cloud#315`** | **Unknown — cloud inaccessible (14 runs)** |
| **React v2 EPIC (`clawmetry#1492`)** | **0 PRs (15+ weeks — stalled or cancelled)** |
| **Canary verification failures** | 2 back-to-back P0 failures (0.12.759, 0.12.760) |
| Themes HOT for 2+ weeks without action | Cost enforcement (wk 12), kill-switch (wk 12 OSS / wk 25+ cloud) |
| Themes HOT for 5+ months without action | `clawmetry-cloud#4` (filed 2026-03-06, now **175 days**) |
| Intel-scout/roadmap-synthesis failures (consecutive) | **14** |

**Uncomfortable truths this week:**

1. **Two consecutive broken releases with no merge-gate block.** `0.12.759` and `0.12.760` both failed post-publish canary verification. The `#5133` CDN-propagation fix was the postmortem — but two issues still sit open. If the canary gate blocked these releases, the issues would have been filed and closed before PyPI. If it didn't block, every new install in that window got a broken package. That's the loop to close: canary → gate → merge is not optional.

2. **CI hardening shipped 10 PRs this week with zero user demand.** SHA-pinned actions and least-privilege tokens are real security improvements. They are also 10 PRs against infrastructure that users have never asked about, while 2 open P0 bugs sit unfixed and a kill-switch request is 175 days old.

3. **The visibility-to-enforcement gap on cost control is now explicit.** Cost provenance (Aug 26), git outcome join, spend-flow visualization (Aug 3), "$0 out-of-pocket" labels (Aug 12) — the entire cost *visibility* stack shipped in 4 weeks. The cost *enforcement* stack (alerts, caps, digest) has 0 PRs across 12 weeks. Users can now read exactly how their budget is burning. They still cannot stop it.

4. **PR Trace and team session sharing shipped with no OSS demand signal.** These are differentiated features — especially the org-key-encrypted sharing model. But they were founder-initiated. The risk is shipping things users will value less than the things they're explicitly asking for. The test: do any users file "I love the PR Trace feature" or "session sharing saved my team" in the next 2 weeks?

5. **The cloud blindspot is 28 days and worsening.** Three of four HOT themes are primarily cloud-side (cost enforcement alerts, kill-switch managed proxy, P0 security). This document cannot verify whether any of them moved because the bot has been blocked from `vivekchand/clawmetry-cloud` for 14 runs. One configuration change at https://code.claude.com fixes it.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **2 open OSS P0 bug issues + 39 open enhancement issues analyzed** (cloud inaccessible — 14 consecutive run failures; cloud signals carried from 2026-07-31, now 28 days stale). **~150+ merged PRs** in the 30-day window from OSS. No `intel-feedback` or `intel-pain` label exists in OSS; demand signal is inferred from cloud issues (carried) and OSS enhancement issues. Of the 39 OSS enhancement issues: ~15 are automated harness-gap scanner filings, 4 are the new Session Replay epic, and the remainder are the large EPICs (React v2, DuckDB, Dives, proxy enforcement, OTel) plus runtime coverage expansion. The `bug` label contains 2 genuine P0 canary failures plus predominantly automated harness-gap filings.
