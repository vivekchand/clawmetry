# What Users Want — June 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-06-19 09:00 UTC.*
*Aggregates signal across `vivekchand/clawmetry` (OSS) and — when in session scope — `vivekchand/clawmetry-cloud` (cloud).*

> **⚠️ Coverage note:** `vivekchand/clawmetry-cloud` was **not accessible** this run (not in MCP session scope). All data below reflects the OSS repo only. Cloud-side user signal is unread this week. Add `vivekchand/clawmetry-cloud` to the session's allowed repositories to get the full picture.

---

## TL;DR (this week)

The OSS issue tracker has **zero open `intel-feedback` or `intel-pain` issues**, meaning there is no systematic channel funnelling user pain into the roadmap. The only externally-filed user complaint — a multi-channel flow visibility bug (#503) — is **11 weeks old and unresolved**. Meanwhile the team shipped ~1,000+ PRs in the past 30 days, overwhelmingly driven by a monetization entitlements system, CI hardening, and architectural migration work. **Shipping velocity is high; documented user demand is nearly invisible. These two things are not the same.**

---

## Hot themes (build these next)

### 1. Multi-channel flow visibility

- **Demand**: 1 open issue (1 OSS + 0 cloud), 0 tracked reactions, filed 2026-04-02, **unresolved at 11 weeks**
- **Representative quotes**:
  - > "There seems to be an issue where I can't see two different channels at once (Slack + WhatsApp). Slack is fine but the flow doesn't show WhatsApp (only referenced in the Gateway widget). If I go to the Brain tab I see the traces for WhatsApp but they are tagged under main (I have it binded to another agent) instead, with the logs showing only msg metadata." — `jaimezapa`, [clawmetry#503](https://github.com/vivekchand/clawmetry/issues/503)
- **Why it matters**: This is the **only externally-filed user bug in the entire open issue tracker**. It describes two distinct failures: (a) the Flow panel silently drops a channel from the visualisation, and (b) multi-agent channel binding is mis-attributed in Brain traces. For a tool whose headline feature is observability across channels and agents, silent mislabelling is a trust-breaking regression. The reporter left after 2 comments; there has been no fix and no follow-up in 11 weeks. Every week this sits open is a week another user silently gives up and never files a report.
- **Linked issues**: [clawmetry#503](https://github.com/vivekchand/clawmetry/issues/503)
- **Likely scope**: OSS (Flow panel rendering) + possible gateway/sync fix for agent-binding attribution
- **Suggested first step**: Reproduce with a local 2-channel setup (Slack + any second adapter), confirm whether the Flow panel exclusion is a frontend rendering bug or a missing `/api/flow` data field. Scope is likely a one-day fix; doing it sends a signal that external bug reports get closed.

### 2. Cloud sync E2E trust gap (P0)

- **Demand**: 1 open issue (1 OSS + 0 cloud — cloud issue tracker unread this week), 2 comments, filed 2026-05-16
- **Representative quotes**:
  - > "There is NO equivalent test for the cloud half: daemon DuckDB → AES-256-GCM encrypt → /ingest/events → cloud brain cache → /api/cloud/brain → client decrypt → render. Any regression in the encryption envelope, the cloud cache key, or the dashboard JS decryption silently produces empty Brain feeds without any test failing. We've shipped 4 cloud-touching PRs today with no E2E gate validating the round-trip is intact." — `vivekchand`, [clawmetry#1456](https://github.com/vivekchand/clawmetry/issues/1456)
- **Why it matters**: ~317 cloud users on the paid tier. A silent break in the AES-256-GCM envelope or the cloud cache shape produces empty Brain feeds with zero test failure and zero console error visible to the user. The team has shipped hundreds of cloud-touching PRs since this was filed with no E2E gate. The issue is self-assessed as P0.
- **Linked issues**: [clawmetry#1456](https://github.com/vivekchand/clawmetry/issues/1456)
- **Likely scope**: Both (OSS sync daemon + cloud ingest/serve, requires both processes running end-to-end)
- **Suggested first step**: `tests/test_moat_cloud_roundtrip_e2e.py` as described in the issue. Estimated 6 hr (M). The entitlements tier system just shipped 32 PRs; the trust layer protecting paid-tier data has no E2E test.

---

## Warm themes (worth tracking)

- **ClawMetry v2 React SPA migration** (8 open issues: #1492, #1493, #1494, #1495, #1496, #1497, #1517, #1519 — all OSS, all founder-filed). Live Trace and Skills tabs shipped in v2 this week. Parallel-rails `/v2` route is active. Risk: the migration backlog is large and has no external demand signal attached to it.
- **DuckDB-everywhere / MOAT architecture** (4 open issues: #1471, #1540, #1722, #1743 — all OSS, all founder-filed). Active work; Query Spine P4 cache push shipped. Architectural consolidation is ongoing but shows no direct connection to user-reported pain.
- **Tracing / OTel** (3 open issues: #1006, #1008, #1012 — all OSS, all founder-filed). Some tracing work shipped this week (run-vs-run diff, first-response latency). No external demand documented.
- **Proxy cost spiral controls** (3 open issues: #2816, #2817, #2818 — all OSS, all founder-filed). Dollar-based cost-spiral breaker, rapid-fire rate breaker, smart model routing — none yet converted to PRs. Useful for multi-agent cost governance but no user request on file.
- **Harness observability gaps** (2 open auto-filed issues: #2730, #3014 — openclaw voice/talk lifecycle fields). #3133 partially shipped a fix for voice lifecycle field extraction from DuckDB blobs, but #2730 and #3014 remain open as the harness audit still flags gaps.

---

## Closed-loop themes (shipped this week)

- **Entitlements / tier gating system**: addressed in clawmetry#2831, #2955, #2978, #3078, #3079, #3080, #3096, #3139, #3140, #3152, #3153, #3156, #3161, #3162, #3163, #3165–#3169, #3171–#3175, #3179, #3181–#3183, #3187, #3188, #3191, #3193 (merged 2026-06-14 to 2026-06-18, OSS). 32-PR burst. Complete tier catalog, upgrade/downgrade diffs, lock reasons, channel/retention/node gates, 402 paywall bodies. **No user request on file for this feature cluster** — it is founder-driven monetization infrastructure.
- **NemoClaw / model-router observability**: addressed in clawmetry#2951, #3092, #3123, #3135, #3136, #3143, #3148, #3186 (merged 2026-06-14 to 2026-06-17, OSS). Agents.yaml roster, Ollama hosts, proxy model lists, sandbox phases surfaced in `DetectResult.meta`.
- **Usage / cost analytics**: addressed in clawmetry#2855, #2929, #3038, #3040, #3194 (merged 2026-06-14 to 2026-06-18, OSS). Compression-potential card, cache re-read tax surface, by-team attribution, per-agent cost split. Partial overlap with warm theme #503 (multi-channel cost attribution) but no direct connection.
- **Voice / talk lifecycle fields**: addressed in clawmetry#3003, #3133 (merged 2026-06-14, OSS). Partial fix for harness gap #2730 — `list_events()` now extracts mode/transport/provider from voice records. Harness gap issue remains open pending full audit sign-off.
- **Session / tracing metadata**: addressed in clawmetry#3028, #3044, #3061, #3119, #3121, #3151, #3160, #3176 (merged 2026-06-14 to 2026-06-15, OSS). Session parentId, end_reason, first-response latency, run-vs-run flow diff, version-health endpoint.
- **License system hardening**: addressed in clawmetry#3025, #3049, #3059, #3105 (merged 2026-06-14 to 2026-06-15, OSS). Offline verify, Ed25519 fingerprint, audit events, 0600 key write.
- **Security / privacy**: addressed in clawmetry#3077, #3127, #2981 (merged 2026-06-14 to 2026-06-15, OSS). Salted scrypt KDF, credential scanner badge, E2E-encrypted security posture in snapshot.

---

## Quiet noise (likely not signal)

- **Automated harness-gap bugs** (#2730, #3014): Filed by `github-actions` via `scripts/harness/audit.py`. These describe observability blind spots but are not user-reported pain — they are tooling output. Partial fix shipped (#3133); remainder is engineering hygiene.
- **Watchdog scope notification** (#3196): Filed today as a fallback because the production smoke watchdog cannot write to `clawmetry-cloud` (out of session scope). Three regressions were detected at `app.clawmetry.com` (`/healthz` → 404, `/fleet/` → 302, one more). **These should be migrated to `clawmetry-cloud` and triaged.** They are not user-reported — they are automated smoke-test failures.

---

## Velocity check

| Metric | Value |
|--------|-------|
| Merged PRs in last 30 days (OSS, partial: last 6 days only in sample) | 100 of ~1,043 total |
| PRs in last 6 days with entitlement/monetization label | ~32 (~32%) |
| Open `intel-feedback` issues | **0** |
| Open `intel-pain` issues | **0** |
| External user bug reports (non-automated, non-founder) | **1** (#503, 11 weeks old) |
| Cloud repo read (this run) | **❌ Not accessible** |
| Themes HOT for 2+ weeks without action | **#503 (multi-channel flow, 11 weeks)**, **#1456 (cloud E2E test gap, 5 weeks)** |

**Uncomfortable truth**: With no open `intel-feedback` or `intel-pain` issues, there is no documented evidence that the product roadmap this week was shaped by user signal. The dominant investment — a 32-PR entitlements system — has no corresponding user request in the tracker. Whether that is the right call is the founder's judgment to make, but it cannot be attributed to user demand as recorded.

The one external user who filed a complaint (#503) has been waiting 11 weeks. That is the loudest signal in the tracker, precisely because it is the only one.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs to detect what's already addressed — in either repo.

This week: **`vivekchand/clawmetry-cloud` was not in MCP session scope** and could not be read. OSS-only data used. Fix by adding the cloud repo to the allowed repository list for this session.

*Filed by the `roadmap-synthesis` bot — [bot-roadmap-synthesis]*
