# What Users Want — November 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-11-27 09:00 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

> **Cloud data note:** Cloud repo inaccessible this run (GitHub session scope limited to OSS repo). This is the **5th consecutive week** with no cloud data. Cloud issues are carried forward from the 2026-10-02 synthesis. Cloud-side signal is now stale enough to be treated as directional, not current.

---

## TL;DR (this week)

The week was dominated by a branding sprint (Little Clawbot mascot) and continued CI hardening. One field-failure bug was fixed (Windows stall watchdog, `#6719`). The published product verification failure (`#6491`) is now **5+ weeks open at 76 comments** with no fix PR — the most expensive open issue by user-trust cost. Session Replay enters week 15 with zero PRs. ChatGPT Work on Codex shipped (`#6671`) — proving the team can land new feature PRs when prioritized — which makes the 15-week absence of a Session Replay PR harder to explain.

---

## Hot themes (build these next)

### 1. Daemon Reliability — Field Failures and Broken Published Artifact

- **Demand**: 7 open `bug` issues (6 `field-failure` + `#6491`). `#6491` has 76 comments and has been open since Oct 20 (5+ weeks). Net improvement: 2 field-failure bugs closed since last week (`#6719` closed by `#6720` this week; likely `#6497` / `#6537` earlier). Still 6 field-failure bugs open spanning Linux/macOS/Windows × Python 3.9–3.14.
- **Representative quotes**:
  - *"The conformance heartbeat failed against the PUBLISHED artifact. This is not a red PR check. It means the product a user installs right now is broken, independent of anything currently being worked on."* — `clawmetry#6491` (76 comments, Oct 20, **still open**)
  - `[field-failure] daemon: daemon_ingest_stalled on Darwin (py 3.9)` — `clawmetry#6492` (32 comments, Oct 20)
  - `[field-failure] daemon: daemon_ingest_stalled on Linux (py 3.10)` — `clawmetry#6567` (18 comments, Nov 5)
- **Why it matters**: Zero-config observation-by-default is ClawMetry's core UX promise. `#6491` says that promise is broken right now for anyone who `pip install`s. At 76 comments and 5 weeks, this has stopped being a tracking issue and started being a reputational event. The daemon blitz last week fixed Windows stall detection (`#6719`) — good progress on the class — but `#6491` tracks a different failure: published artifact conformance. These are distinct problem spaces. A user trying ClawMetry today hits `#6491` before they ever hit a field-failure bug.
- **Linked issues**: `clawmetry#6491`, `clawmetry#6492`, `clawmetry#6517`, `clawmetry#6538`, `clawmetry#6567`, `clawmetry#6588`, `clawmetry#6595`, `clawmetry#6597`
- **Likely scope**: OSS — `clawmetry/sync.py`, `clawmetry/local_store.py`, published artifact build pipeline
- **Suggested first step**: Answer publicly on `#6491` whether `pip install clawmetry && clawmetry` works right now on the latest release. If yes, close it and document what the heartbeat was flagging. If no, yank or hotfix before shipping any new feature.
- **Weeks open (oldest)**: **5 weeks** (`#6491`) ⚠️⚠️

---

### 2. Session Replay — Runtime-Aware Transcript Viewer

- **Demand**: 2 open OSS issues (`clawmetry#4814`, `#4815`), first filed 2026-08-14. **Week 15** without a PR. Highest-fanout runtime (Claude Code) generates sessions with 20+ Agent/Task calls that collapse to a single chip in the current viewer.
- **Representative quotes**:
  - *"Claude Code is the highest-fanout runtime we support — sessions with 20+ Agent/Task calls. Today the transcript viewer shows the parent turn with a single collapsed 'Task' tool chip — the child's actual work is never inlined."* — `clawmetry#4815` (4 comments)
  - *"Today the session UI shows nothing about how a session ran: Auto vs interactive vs plan vs `--dangerously-skip-permissions`. Approvals asked count is stored but the transcript viewer never fetches it."* — `clawmetry#4814` (4 comments)
- **Why it matters**: Claude Code is the most-used runtime ClawMetry monitors — including by this repository's own automation. Any session with 20+ subagents collapses to a single chip. This week's ChatGPT Work on Codex PR (`#6671`) shows the team can ship new runtime surface area in one focused PR. Session Replay needs the same. Users who come to ClawMetry to understand *what their agent actually did* hit the worst-case scenario immediately on the highest-fanout runtime.
- **Linked issues**: `clawmetry#4814`, `clawmetry#4815`
- **Likely scope**: OSS — `routes/sessions.py`, `clawmetry/local_store.py`, replay_events table
- **Suggested first step**: Ship the permission-mode surface (`#4814`) as the narrowest first PR (2–4 hours, no new data model needed). The ChatGPT Work PR shows what a focused runtime-surface PR looks like.
- **Weeks open without a PR**: **15** ⚠️⚠️

---

### 3. OTLP P1 — Durable Acknowledgements and Unsampled Usage Accounting

- **Demand**: 1 open `bug` (`clawmetry#5949`, 8 comments) + 5 WO-MON schema completeness enhancements (`#6071`–`#6075`). Filed 2026-09-13. **Week 11.**
- **Representative quotes**:
  - *"Never return an unqualified success after silently losing accepted records; follow OTLP partial-success/retry semantics and document rejected counts."* — `clawmetry#5949` (P1, 8 comments)
  - *"Extend existing spans storage to composite identity, resource/scope/schema provenance, links, events, status, timestamps and content policy; migrate existing rows safely."* — `clawmetry#6071`
- **Why it matters**: OTLP P0 (`#5938`) shipped after 11 weeks; P1 is now week 11. The pattern says this either ships next week or enters the "27-week graveyard". An OTLP producer that sends spans to ClawMetry and sees `200 OK` currently has no guarantee those spans made it to durable storage. For LangGraph, Azure AI Foundry, and AWS AgentCore integrations, silent loss is a correctness bug and an audit-trail compliance gap.
- **Linked issues**: `clawmetry#5949`, `clawmetry#6071`, `clawmetry#6072`, `clawmetry#6073`, `clawmetry#6074`, `clawmetry#6075`
- **Likely scope**: OSS — `clawmetry/local_store.py`, OTLP receiver in `routes/meta.py`
- **Suggested first step**: Ship OTLP partial-success semantics (`#5949`) first — bounded queue + explicit acknowledgement. The schema completeness series (`#6071`–`#6075`) is additive and can follow.
- **Weeks open**: **11** — at the P0 inflection point. ⚠️

---

## Warm themes (worth tracking)

- **Enterprise readiness cluster** (`clawmetry#5948`, `#5946`, `#5942`, `#5940`, `#5937`): Signed container image, CI/CD GitHub Action, fleet install (Windows service + VDI + Linux linger), LiteLLM proxy callback, cost figure provenance labels. All filed 2026-09-13, all `bot-plan-only`. **11 weeks, 0 PRs.** The LiteLLM hardening dep bumps this week touched advisory/dependency layers — the feature itself (proxy callback + OTel ingestion) remains unbuilt.

- **DuckDB migration tail** (`clawmetry#1032`, `#1038`): Phase 6 Cloud SQL teardown + "query-spine P9" retire monolith snapshot. DuckDB 2.0 bumped in deps — the actual Cloud SQL retirement and snapshot retirement have no PR. **28+ weeks.**

- **React v2 migration** (`clawmetry#1492`, `#1493`, `#1497`, `#1519`): SPA scaffold, typed v2 contracts, cloud mirror, polish. **28+ weeks open, 0 PRs.** At this age it needs either a PR date, explicit de-prioritization in the open issues, or closure. Middle ground is drift.

- **Governance / audit evidence contracts** (`clawmetry#6349`, `#6122`, `#6121`): Source-rights evidence hook (AcqPath integration), JEV versioned advisory contracts, Jev decision-request observability. 7–10 weeks, low comment volume.

- **LLM-as-judge evals** (`clawmetry#1619`): **28+ weeks open, 0 PRs.** UI shell exists; local auto-scoring evaluator doesn't.

- **ClawMetry Dives — AI SQL→Chart** (`clawmetry#999`): **28+ weeks open, 0 PRs.** Backend endpoint is the only missing piece.

- **OpenClaw provider account priority** (`clawmetry#5748`): Connected provider account priority not captured (4 comments). OpenClaw is a free OSS runtime — this is real OSS user signal.

---

## Closed-loop themes (we shipped this)

**New since 2026-11-20 (this week):**

- **Windows stall watchdog fix** (`clawmetry#6719`, closed by `#6720`, merged Nov 25): The daemon now detects Windows suspend/resume in the stall watchdog, fixing one field-failure class on Windows Python 3.13. Net: 1 field-failure bug closed, 6 remain.

- **ChatGPT Work on Codex** (`clawmetry#6364`, closed by `#6671`, merged Nov 21): Local ChatGPT Work coverage is now disclosed on the shared Codex runtime. First new runtime surface area since the OpenClaw session fix.

- **Little Clawbot branding** (`#6724`, `#6725`, merged Nov 26): New product mascot across every brand surface. Brand-driven, not user-signal-driven.

- **Physical AI documentation** (`#6729`, merged Nov 26): Docs introducing digital and physical AI observability and governance narrative. Aligns with the robotics query seam shipped last week.

**Carried from prior periods:**

- OTLP P0 (`#5938`) — span normalization, Guard bypass, unredacted storage, shipped Nov 2026.
- Daemon reliability blitz — 5 root causes fixed, Nov 14–15.
- Path traversal containment — `/api/reasoning`, `/api/logs`, `/api/skills`, Nov 20.
- Robotics / physical AI control-plane query seam — Nov 20.
- Approval evidence commit link — Nov 2026.
- Windows certmgr.msc TLS guidance — Nov 15.

---

## Quiet noise (likely not signal)

- **Weekly-digest and good-first-issue-scan issues**: Bot-generated operational noise. Not user signal.

- **WO-MON OTLP schema completeness series** (`clawmetry#6071`–`#6075`): The P1 bug (`#5949`) in this cluster is signal; the five work-order enhancement trackers are internal scope backlog.

- **Bot-plan-only tracking issues** (~22 of 38 open issues carry `bot-plan-only` or `enhancement`): Claude-generated architectural plans waiting for a PR. Real features, not validated external user asks.

- **CI hardening PRs** (~12 of ~17 merged PRs this period): Dep bumps, pin set updates, Dependabot stream repairs. DuckDB 2.0 bumped in this batch. Healthy hygiene; not user feature signal.

---

## Velocity check

| Metric | Value |
|--------|-------|
| OSS PRs merged (last 7 days) | **~17** |
| OSS PRs merged (last 7 days, substantive — excl. deps/CI/RELEASE/bumps) | **~5** (Windows fix, ChatGPT Work, branding, physical AI docs, URL scheme security) |
| Cloud PRs merged | *not accessible (5th consecutive week)* |
| User-signal themes shipped (last 7 days) | **1** (#6719 field-failure) |
| **Largest PR cluster (last 7d)** | CI hardening (~12 PRs) |
| **`#6491` published product verification** | **5+ weeks open, 76 comments** ⚠️⚠️ |
| **Open field-failure bugs** | **6** (down from 8 two weeks ago) |
| **OTLP P1 `#5949`** | **11 weeks open, 0 PRs** ⚠️ |
| Session Replay EPIC: weeks open | **15 weeks, 0 PRs** ⚠️⚠️ |
| Enterprise readiness cluster | **11 weeks, 0 PRs** ⚠️ |
| Evals EPIC (`#1619`) | **28+ weeks, 0 PRs** |
| Dives EPIC (`#999`) | **28+ weeks, 0 PRs** |
| React v2 EPIC (`#1492`) | **28+ weeks, 0 PRs** |
| Themes HOT for 2+ weeks without action | `#6491` (5 wks), Session Replay (15 wks), OTLP P1 (11 wks) |
| Cloud repo accessible this run | **No** (OSS scope only, 5 consecutive weeks) |

**Uncomfortable truths this week:**

1. **The branding sprint shipped (Little Clawbot) while `#6491` has been open for 5+ weeks.** Branding is valuable — it was clearly intentional work. But the published product is still failing verification at 76 comments. The question isn't whether the branding work was worth doing; it's whether the team has an explicit answer to "is pip install clawmetry working right now?" If yes, close `#6491` with a comment explaining what the heartbeat flags. If no, the trust cost of shipping a mascot before a yank/hotfix is real.

2. **ChatGPT Work on Codex shipped this week.** That's exactly the shape of a Session Replay PR — one focused feature, one PR, done. If the team can ship ChatGPT Work in one PR, Session Replay (`#4814`) needs a credible explanation for why it hasn't gotten the same treatment in 15 weeks. "It's on the roadmap" is not an explanation at week 15.

3. **OTLP P1 (`#5949`) is at week 11.** OTLP P0 shipped in week 11 after tracking. If the pattern holds, P1 ships next week. If it doesn't, the pattern breaks and P1 joins the 27-week graveyard. This is the fork in the road.

4. **Three epics are 28 weeks old with zero PRs** (React v2, Evals, Dives). These need an explicit state: active, deferred, or closed. Open epics with no PR after 6 months are not a roadmap; they're aspirations without commitment. Close the ones that won't happen in 2026, or assign a PR date.

5. **Cloud repo is now 5 consecutive weeks inaccessible.** The plaintext API key bug (`clawmetry-cloud#315`), cloud cost enforcement signals, and Guard cloud signals are now stale July 2026 data. This synthesis is increasingly OSS-only. If the cloud repo is out of scope permanently, the "aggregates signal across both repos" header should be updated.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs in both repos to detect what's already addressed — in either repo.

This run: **38 open OSS issues analyzed** (10 `bug` + 24 `enhancement` + 4 other; 0 `intel-feedback` / 0 `intel-pain` in OSS — all OSS issue signal is bot-generated or founder-initiated). **Cloud issues inaccessible this run** (5th consecutive week) — carried from 2026-10-02. **~17 merged OSS PRs** in the last 7 days (~5 substantive). Cloud repo out of session GitHub scope this run.
