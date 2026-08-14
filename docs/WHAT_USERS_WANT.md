# What Users Want — August 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-08-14 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** The roadmap-synthesis session is scoped to `vivekchand/clawmetry` only this run — `vivekchand/clawmetry-cloud` is inaccessible (same scope misconfiguration blocking the intel-scout and roadmap-synthesis bots for **13 consecutive runs**). Cloud signals are carried forward from the 2026-07-31 synthesis, which had live dual-repo access. **Fix (one-time):** Add `vivekchand/clawmetry-cloud` to the roadmap-synthesis and intel-scout session scopes at https://code.claude.com.

---

## TL;DR (this week)

The OTel/Tracing EPIC broke its 12-week stall: OTLP receiver (JSON, port 4318, no protobuf), a working Tracing tab, turn-anchored trace UI, and a dependency-free `clawmetry.trace` SDK all landed in a 48-hour window (Aug 12–14). The Desktop App also had a major launch week — signed macOS .dmg, Authenticode-signed Windows installer, Linux .deb, global CLI, self-healing daemon. Both were founder-initiated with zero user-issue demand in OSS. The three persistently HOT user themes — cost enforcement, the proxy kill-switch, and the P0 security bug — each closed the week exactly where they opened it: 0 PRs, 10+ weeks open.

---

## Hot themes (build these next)

### 1. Cost Control — Enforcement, Alerts & Weekly Digest

- **Demand**: 9+ open issues across both repos (5 cloud intel + 4 OSS proxy issues), last raised cloud intel 2026-06-25. Intel scores 7–9/10.
- **Representative quotes** (carried from 2026-07-31 synthesis; cloud repo inaccessible this run):
  - *"Just a number climbing in silence while five engineers stared at dashboards that gave us totals and nothing else."* — `clawmetry-cloud#1683` (dev.to post, $1,800 silent GPT-4o spike)
  - *"I use LLMs daily… anywhere from $200–$400 tops… I just can't figure how to burn that much money a month responsibly."* — `clawmetry-cloud#653` (HN 474-comment thread, intel-score 9/10)
  - *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache writes accumulated."* — `clawmetry-cloud#655` (dev.to $47K retroactive bill)
- **Why it matters**: The spend-flow visualization shipped Aug 3. The Cost tab now shows "$0 out-of-pocket — covered by" for flat-rate users (Aug 12), partially addressing subscription-mode cost inflation. Those are the visibility layers. What's still missing: graduated budget alerts (50%/80%/95% cap), a weekly spend digest to Slack/email, and hard enforcement before the limit is hit. Visibility without enforcement is watching a fire you can't put out. `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts) remains unstarted. Competitors Helicone and AgentPulse ship budget alerts on day one.
- **Linked issues**: `clawmetry-cloud#1683`, `clawmetry-cloud#1694`, `clawmetry-cloud#1695`, `clawmetry-cloud#1696`, `clawmetry-cloud#1701`, `clawmetry-cloud#653`, `clawmetry-cloud#652`, `clawmetry-cloud#655`, `clawmetry-cloud#1484`, `clawmetry-cloud#1088`, `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`
- **Likely scope**: Both — OSS proxy (port 4100) gets enforcement rules; cloud gets budget alerts + weekly digest
- **Suggested first step**: Land `clawmetry-cloud#1484` (scheduled spend digest + graduated alerts). The spend-flow visualization and "$0 out-of-pocket" display are in place; the alert layer on top is the natural next PR.
- **Weeks unaddressed** (enforcement half): **10+** (up from 9+ last week)

---

### 2. Agent Kill-Switch / Proxy Policy Engine

- **Demand**: 6+ open issues (3 OSS + 3+ cloud). TokPinch launched with 250 stars in 2 weeks on exactly these features. `clawmetry-cloud#4` is now **163 days old** (filed 2026-03-06).
- **Representative quotes** (carried):
  - *"TokPinch intercepts heartbeat pings to Claude Opus and routes them to Haiku or Sonnet… saving 10–50% API cost."* — `clawmetry#2816`
  - *"An agent at a real customer deleted the production DB in 9 seconds. We need a kill switch."* — `clawmetry-cloud#692`
  - *"Managed cloud proxy endpoint — fleet-wide enforcement + observability without running anything locally."* — `clawmetry-cloud#53`
- **Why it matters**: Rule Builder Phase 1 (`#4735`) landed the `/api/v2/rules` REST backend this week — that's the configuration layer. But the enforcement layer — `proxy.py` applying those rules at the interception point (port 4100) to actually block/reroute/pause calls — is still not built. A rule you can define but the proxy doesn't enforce is a database row, not a kill-switch. Cache Hit Rate + Routing Advisor tiles (`#4610`) give routing *visibility*; they don't give routing *control*. `clawmetry#2816`–`#2818` remain open with 0 PRs.
- **Linked issues**: `clawmetry#2816`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#4`, `clawmetry-cloud#53`, `clawmetry-cloud#54`, `clawmetry-cloud#692`
- **Likely scope**: Both — OSS proxy gets the policy rules wired in; cloud gets the managed proxy endpoint with fleet-wide enforcement
- **Suggested first step**: Wire `#4735`'s rule schema into `proxy.py` so a rule with `action: block` actually intercepts calls at port 4100. The REST backend is already in place; this is the enforcement bridge PR.
- **Weeks unaddressed**: **10+** (OSS `#2816`–`#2818`); **23+** (`clawmetry-cloud#4`, filed 2026-03-06)

---

### 3. P0 Security — Plaintext API Keys in Production DB ⚠️

- **Demand**: 1 issue (`clawmetry-cloud#315`, labeled `bug`, filed **2026-04-14**, now **143 days old**).
- **What it says**: `users.api_key` stores raw `cm_*` tokens in cleartext in the production database. Confirmed in prod. Anyone with read access — developer access, backups, GCP logs, support tooling — can impersonate any user.
- **Why it matters**: This is not a prioritization dispute — it is a confirmed security exposure that is now **20+ weeks old**. Every week paying customers onboard while the exposure window grows. The fix is a single PR: bcrypt the stored keys, run a one-time migration script, update the verification flow.
- **Linked issues**: `clawmetry-cloud#315`
- **Likely scope**: Cloud only
- **Suggested first step**: Bcrypt stored keys with a one-time migration. Estimated 1 day of work.
- **Weeks unaddressed**: **20+** (up from 19+ last week)

---

## Warm themes (worth tracking)

- **Session Tracing EPIC** (`clawmetry#1006`, `clawmetry-cloud#321`, `#322`, `#320`, `#703`): **Major movement this week — demoted from HOT to WARM.** OTLP receiver shipped (JSON, port 4318, hex ids — `#4785`), Tracing tab restored and populated (`#4789`), turn-anchored trace UI with collapsed tools and jump-to-turn TOC (`#4802`), and `clawmetry.trace` dependency-free SDK in review (`#4804`). The full span hierarchy and replay scrubber (the core ask of `#1006`) remain unbuilt, but the ingest and display foundation now exists. Watch for users requesting parent→child relationship rendering and distributed trace stitching as the next filed issue.

- **OTel Emitter Discovery** (`clawmetry#4783`): New this week. Now that the OTLP receiver works, auto-detection of OTel-emitting applications on the same machine (process env scan for `OTEL_EXPORTER_OTLP_ENDPOINT`, port probing on 4317/4318) is the natural follow-on. Filed as a scoped enhancement; not a blocker.

- **React v2 Migration** (`clawmetry#1492`, RFCs `#1493`/`#1494`/`#1497`/`#1519`): **13+ weeks open, 0 PRs.** Design handoff exists at `/Users/vivek/Downloads/design_handoff_clawmetry_v2/`. At 13 weeks with no commits, this is stalled or cancelled. A decision — either a first PR or an explicit close — would clean up 5 open issues.

- **Remote Approval Gates — Policy Layer** (`clawmetry#881`, `clawmetry-cloud#1192`): Push-notification half shipped Jul 25. Rule Builder REST backend shipped (`#4735`) this week. The enforcement bridge — wiring rules into `proxy.py` so a matched call actually pauses — is still the missing piece. Overlaps with HOT Theme #2.

- **Subscription-Mode Cost Accounting** (`clawmetry-cloud#1088`): Partially addressed — Cost tab now shows "$0 out-of-pocket — covered by" for flat-rate users (`#4774`, Aug 12). The visual ~100x cost inflation for Claude Max / ChatGPT Plus / Codex OAuth users is mitigated at the display layer. Watch for follow-up on whether the underlying per-token accounting is also suppressed for flat-rate traffic.

- **DuckDB-everywhere + Redis hot cache** (`clawmetry#1032`): Foundational for Dives (`#999`) and the trace tree (`#1006`). Open since May 12. 0 PRs. The 80x ingest speedup (`#4669`) hit the write path this week; the read-path hot cache is still unbuilt.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): 14+ weeks open, 0 PRs. Enables NL questions over local DuckDB agent data. Foundational for advanced analytics. DuckDB is the right backend; just needs the prompt template + endpoint + chart rendering layer.

- **Version-Aware Health Regression Detection** (`clawmetry#2861`): **Shipped this week** via `#4625` — version-regression banner now appears in the System Health panel. Issue `#2861` can be closed.

- **ClickClack channel adapter** (`clawmetry#3837` et al.): **7 automated filings** in ~25 days (`severity:high`). Fix is one string (`"clickclack"`) added to `_CHANNEL_DIRS` in `clawmetry/sync.py` + one route in `routes/channels.py`. Each new filing is a harness cycle spent on a known one-line gap.

- **Helicone-Refugee Importer** (`clawmetry-cloud#962`): One-click import of Helicone JSON logs + cache analytics panel. Real acquisition channel. 0 PRs.

---

## Closed-loop themes (we shipped this)

**New this week (2026-08-08 → 2026-08-14):**

- **OTel / Tracing foundation** (`#4785`, `#4789`, `#4796`, `#4802`, `#4804`): OTLP receiver works out of the box (JSON, port 4318, hex ids — no protobuf). Tracing tab restored and populated from local DuckDB. Turn-anchored trace UI with collapsed tools + jump-to-turn TOC. `clawmetry.trace` dependency-free SDK (in review). E2E smoke test. **Largest single-week movement on a HOT user theme in 3 months.** Watch for span-hierarchy and distributed-trace-stitching follow-ups from users who asked for `clawmetry#1006`.

- **Desktop App native installers** (`#4602`, `#4614`, `#4646`, `#4648`, `#4705`): First signed macOS .dmg with drag-to-Applications layout. Authenticode-signed Windows installer (fixes Smart App Control uninstall block). Linux .deb. Global CLI, self-healing sync daemon, 6-hour background auto-update (`#4706`). First-launch onboarding pane — sign in, auto Pro trial, cross-sell carousel (`#4614`). **No OSS user issues requested this; founder-initiated distribution investment.**

- **Onboarding & trial lifecycle** (`#4788`, `#4792`, `#4775`, `#4776`, `#4694`, `#4799`, `#4707`): Root cause of trial-less cloud signups fixed (subprocess EOFError on non-interactive encryption-key prompt — `#4792`). Cloud sign-in activates 7-day Pro trial at signup. Onboarding gate + login prompt no longer re-appear after successful OTP. Self-host sign-in provisions the 7-day trial. `--turn-off-cloud-sync` now purges every cloud trace. Uninstall removes all ClawMetry traces so fresh install re-onboards cleanly.

- **Rule Builder Phase 1 REST backend** (`#4735`, merged Aug 11): `/api/v2/rules` REST backend — configuration layer for the policy engine. Issue `clawmetry#1517` partially closed. Enforcement in `proxy.py` still pending (see HOT Theme #2).

- **Version health regression banner** (`#4625`, merged Aug 8): "Did deploy X cause this regression?" now surfaces as a correlation banner in System Health. Closes `clawmetry#2861`.

- **Cache Hit Rate + Routing Advisor tiles** (`#4610`, merged Aug 7): Routing visibility — cache-hit rate and model routing suggestions in the dashboard. Visibility only; the control half (auto-rerouting) is still in `clawmetry#2816`.

- **Grafana-style date/time range picker** (`#4771`, merged Aug 12): Activity and Sessions tabs now have a polished date/time-range picker. Addresses implicit UX complaint about time-range filtering.

- **80x faster fresh-install ingest** (`#4669`, merged Aug 9): Bulk flush, pre-insert integrity chain, batch session/span APIs. Significant perf milestone for new users with large session history.

- **Windows UX fixes** (`#4673`, `#4705`, `#4717`, `#4752`, `#4754`): Python 3 auto-install on Windows. Authenticode signing (fixes Smart App Control uninstall block). `pythonw.exe` for Claude Code hook (no console popup). TLS cert verification on OTP/OAuth POSTs. Cross-origin URLs routed to system browser.

- **Cloud-sync toggle in header** (`#4623`, merged Aug 8): One-click pause/resume for cloud sync without a full `--turn-off-cloud-sync`.

- **Fish Audio TTS cost tracking** (`#4768`, `#4726`, merged Aug 10–12): Fish Audio S2.1 TTS calls captured as `tts_call` events with cost backfill. Extends coverage of non-LLM AI spend.

- **Evals: score-first reorder + per-session drill-down drawer** (`#4806`/`#4818`, merged Aug 14): Evals tab reordered by score; per-session drill-down drawer added. Second evals push in 2 weeks; still no user-issue demand in OSS.

- **Cost tab subscription display** (`#4774`, merged Aug 12): Shows "$0 out-of-pocket — covered by" for flat-rate users instead of inflated per-token API costs. Partially addresses `clawmetry-cloud#1088`.

**Continuing from prior weeks:**
- Spend-flow visualization (`#4494`/`#4513`, Aug 3) — partial HOT Theme #1 close (visibility delivered, enforcement open).
- Web Push Phone Approvals (`clawmetry-cloud#1766`–`#1790`, Jul 25–26) — watching for Android reliability follow-ups.
- 18 runtimes total (QM Aug 7; xAI Grok Aug 5).
- Trial-end hard-block + expired-trial banner (`#4566`/`#4444`, Aug 2–6).

---

## Quiet noise (likely not signal)

- **Harness-observability gap issues** (~40 open OSS issues outside the enhancement set): Automated bot filings for `[obs-gap:openclaw]` and `[obs-gap:nemoclaw]`. Not user pain; coverage gaps the harness scanner identified. The **ClickClack obs-gap** (`severity:high`) is the loudest automated signal by volume — **7 filings in ~25 days**. One-line fix in `sync.py`.

- **Intel-scout / roadmap-synthesis scope blockers** (`#3466`–`#3834`+): Both bots blocked from `vivekchand/clawmetry-cloud` for **13 consecutive runs**. Real cloud user pain is accumulating unfiled. Fix: add `vivekchand/clawmetry-cloud` to both bots' session scope at https://code.claude.com.

- **Entitlement API buildout** (40+ OSS PRs since Aug 1): Time-indexed scalar helpers building the open-core paywall engine. Legitimate infrastructure. Zero user issues requested these.

- **CI/harness housekeeping** (~8 PRs): Branch-protection applier fixes, Playwright caching, e2e-gate guard and concurrency fixes. Internal quality work.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (Aug 8–14, estimated excl. bumps/RELEASE/i18n) | ~50 |
| OSS PRs merged (last 30d, estimated) | **~600+** |
| User-signal themes shipped (Aug 8–14) | 2 (Tracing foundation; version health regression `#2861`) |
| **Largest PR cluster (Aug 8–14, excl. bumps/RELEASE)** | Desktop App native installers (~15 PRs) — **0 user issues requested** |
| **2nd largest PR cluster** | Entitlement API scalars (~15 PRs) — **0 user issues requested** |
| **OTel/Tracing EPIC: first meaningful PRs** | **This week** (after 12 weeks of 0 PRs) |
| **Cost enforcement / kill-switch: PRs shipped** | **0 (10+ weeks; `clawmetry-cloud#4` open 163 days)** |
| **P0 Security `clawmetry-cloud#315`** | **0 PRs in 143 days** |
| **React v2 EPIC (`clawmetry#1492`): PRs shipped** | **0 (13+ weeks — stalled or cancelled)** |
| Themes HOT for 2+ weeks without action | Cost enforcement (`#2816`–`#2818`, since 2026-06-07) |
| Themes HOT for 5+ months without action | `clawmetry-cloud#4` (emergency stop, filed 2026-03-06, **163 days**) |
| Intel-scout/roadmap-synthesis failures (consecutive) | **13** — cloud intel accumulating unfiled |

**Uncomfortable truths this week:**

1. **The OTel/Tracing push is real progress — but the span hierarchy is still missing.** Users asked for `clawmetry#1006` (OTel-compatible trace tree with parent→child relationships). What shipped is the ingest and display foundation: OTLP receiver, Tracing tab, turn-anchored session UI. That's the right first step. What's unbuilt: parent→child span rendering and distributed trace stitching. The filed EPIC (`#1006`) is not closed. Watch for users filing that ask explicitly now that the Tracing tab exists.

2. **Desktop App was the week's biggest shipping story with zero user-issue demand.** The macOS .dmg, Windows Authenticode installer, Linux .deb, global CLI, and self-healing daemon are legitimate distribution investments. But no OSS user issue requested any of these. Distribution expands reach; it doesn't serve the users already here who want cost enforcement, kill-switches, and trace hierarchies.

3. **Cost enforcement is in its 10th week with 0 PRs.** Spend-flow visualization (Aug 3) and the "$0 out-of-pocket" label (Aug 12) delivered full visibility. Enforcement — budget caps, graduated alerts, weekly digest — is the unbuilt half of the most-requested user outcome. The visibility shipped in two weeks; the enforcement has been waiting 10+ weeks.

4. **The security bug is 143 days old and growing.** `clawmetry-cloud#315` (plaintext API keys, confirmed in prod) has had 0 PRs in 20+ weeks. Estimated fix: 1 day. Every paying customer who onboarded since 2026-04-14 has had their credential stored in cleartext.

5. **Cloud blindspot is worsening — 14 days of unseen signal.** The last live read of `vivekchand/clawmetry-cloud` was 2026-07-31. This synthesis carries cloud signals that are now 14 days stale. Both bots are blocked for the 13th consecutive run. The scope fix takes one configuration change.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **24 open OSS enhancement issues analyzed** (cloud inaccessible — signals carried from 2026-07-31 synthesis). **~600+ merged PRs** in the 30-day window from the OSS repo. No `intel-feedback` or `intel-pain` label exists in OSS; demand signal is inferred from cloud issues (carried) and human-filed OSS enhancement issues. The `bug` label exists in OSS and contains predominantly automated harness-gap filings, not user-reported defects.
