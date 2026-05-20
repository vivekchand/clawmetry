# PRD — Cloud Pro: Agent Reliability (ClawBench on your real traffic) + Pipelines (CrawlBar)

Status: Draft · Owner: ClawMetry · Date: 2026-05-20 · Tier: **Cloud Pro** ($5/node/mo)

> TL;DR. ClawMetry already *observes* agents and *scores completed sessions* with an LLM judge (eval Phases 1–3). The natural next step — and the strongest paid differentiator we have — is to score **how reliably the agent works**, on the user's **own production traces**, using [ClawBench](https://github.com/openclaw/clawbench)'s trace-based methodology. Everyone else benchmarks models on synthetic tasks; we grade *your* agent on *your* traffic and tell you the one config change that buys the most reliability. A second, lighter surface borrows [CrawlBar](https://github.com/openclaw/crawlbar)'s manifest control-plane idea to give crawler/cron **data pipelines** a freshness + last-run view.

---

## 1. Why now / the gap

ClawMetry today answers *"what is my agent doing and what does it cost?"* (Flow, Brain, Models, Cost, Embodied) and *"how could it improve?"* (Self-Evolve — qualitative findings). What it does **not** answer with a number the user can trust over time:

> **"How reliable is my agent, why does it fail, and is it my model or my config?"**

That is exactly the question ClawBench was built to answer — and ClawMetry is uniquely positioned because **we already have the traces**. No new instrumentation, no synthetic task suite to babysit: the events / tool-calls / sessions / sub-agents already live in local DuckDB.

This is a Cloud Pro feature because it is a *premium, computed insight* (a score + taxonomy + attribution), not a raw view — the kind of thing that converts a free node to paid.

## 2. The two inspirations

### 2a. ClawBench — *primary fit* (the paid feature)
ClawBench scores the **full stack — harness, config, and model — not just the LLM**, by analysing execution **traces** rather than final outputs. Concepts we adopt:
- **Trace-based deterministic checks** — read-before-write, self-verification, recovery-after-error, tool-misuse — scored from the trajectory, not the answer.
- **Failure taxonomy** — ~13 deterministic failure modes (hallucinated completion, verification skipped, tool misuse, looping, …) instead of binary pass/fail.
- **Reliability metrics** — `pass^k` (all k runs must pass), Signal-to-Noise, bootstrap confidence intervals. ClawBench's headline finding: *"47% of 40-task variance is seed noise"* — i.e. a single run lies; reliability needs repetition.
- **Config ablation** — fingerprint the plugin/skill stack and measure its impact *separately* from the model. ClawBench: *"swapping the plugin configuration produces score swings 10× larger than swapping the model."* This is the killer insight for our users: the lever is usually their config, not their model.
- LLM judge is **capped (≤10% weight) behind a deterministic floor** — keeps scores trustworthy + cheap. Matches our local-first judge stance.

### 2b. CrawlBar — *secondary fit* (a lighter surface + an architecture pattern)
CrawlBar is a macOS menu-bar control plane for local crawler apps: it **discovers tools via drop-in manifest JSON**, shows **status / freshness / data counts**, and runs **refresh / doctor**. Two takeaways:
- **Manifest-based discovery** → directly reinforces our multi-harness adapter direction (Hermes, Claude Code, Codex): a harness/pipeline ships a manifest and ClawMetry observes it with no code change.
- **Freshness + last-run + row-count + refresh/doctor** → a natural **"Pipelines"** surface for crawler/cron data jobs (data-freshness SLAs), which today have no first-class home in ClawMetry.

## 3. The natural fit (this extends what already exists)

ClawMetry already ships a 3-phase eval system; ClawBench is **Phase 4**, applied to real traffic:

| Existing | What it does | ClawBench adds (this PRD) |
|---|---|---|
| `eval_runner.py` (Phase 1) | LLM-as-judge scores *completed sessions* | Deterministic **trace** checks (read-before-write, verify, recover) so the score isn't judge-only |
| `eval_suite_runner.py` (Phase 2) | Golden test sets + CLI | **Failure taxonomy** vocabulary shared with golden runs |
| `eval_regression_replay.py` (Phase 3) | Re-run a past input through current config | **pass^k / config-ablation**: replay k× and attribute swings to config vs model |
| `routes/selfevolve.py` | *Qualitative* "how to improve" findings (category/severity) | A *quantitative* **Reliability Score** the findings hang off of |

So we are not bolting on a foreign benchmark — we are putting a **number and a taxonomy** under the qualitative Self-Evolve story, reusing the eval plumbing, the DuckDB trace store, and the snapshot→Redis→cloud display path.

## 4. The feature — "Agent Reliability" (Cloud Pro tab)

A new **Reliability** tab (Cloud Pro; Free sees a teaser). Computed locally, displayed in cloud.

**Headline (the "score card"):**
- **Reliability Score 0–100** + letter grade, over a rolling window — the `pass^k`-weighted, deterministic-floored aggregate of recent sessions/crons.
- **Confidence interval + "noise" flag** — if recent volume is too low to be trustworthy, say so (ClawBench's honesty about seed noise), don't show a fake precise number.
- **Trend sparkline** — score over the last N days (rides the same daily-rollup path we just built for Cost).

**Failure taxonomy panel:**
- Breakdown of recent failures across the ~13 modes (hallucinated completion, verification-skipped, tool-misuse, loop, recovery-failed, …), each with count, % of failures, and one-click drill-down to the offending session transcript (we already render transcripts in cloud).

**Config-ablation panel (the conversion hook):**
- "Your **config**, not your model, is your biggest reliability lever." We already know the plugin/skill stack (Skills tab) + the model mix (Models tab). Surface: *"Sessions with skill X enabled fail 3× more on verification"* / *"disabling plugin Y would raise your score ~12 pts (est.)"* — derived from the trace cohort split, not a live ablation (no re-billing).
- Optional, opt-in **active replay** (Phase 3 infra): re-run a sampled past input k× under the current vs a candidate config and report the real swing. Gated + bounded (uses the user's own model via the `openclaw agent` delegation pattern we use for Self-Evolve — no credential handling, no cloud-side LLM).

**Per-session drill-down:**
- Open any session → its trace timeline annotated with the deterministic checks it passed/failed (read-before-write ✓, self-verify ✗, recovered-from-error ✓), plus the LLM-judge note (≤10% weight). This is the ClawBench "execution trace score" applied to one real run.

## 5. Architecture (fits our invariants exactly)

- **Local compute, cloud display.** Scoring runs on the **daemon**, over local DuckDB traces (`query_events` / `query_sessions` / `query_subagents`). The LLM-judge portion delegates to **`openclaw agent`** (OpenClaw's own creds) — the same delegation we shipped for Self-Evolve — so ClawMetry never handles a model credential and the cloud never runs an LLM.
- **Blessed data path.** The computed reliability rollup (score, taxonomy counts, ablation cohorts, per-session annotations — all aggregates, no raw prompts) rides the **encrypted snapshot → Redis → cloud**, decrypted client-side. Cloud SQL stores nothing new.
- **Pro gating.** Tab + payload gated by `_is_pro_user()` (same as Alerts). Free tier: a blurred score + "Upgrade to grade your agent" CTA (one click = conversion).
- **Cadence + cost.** Deterministic checks are cheap (pure trace walk) — run every snapshot. The judge + any active replay are gated (e.g. ≤ once/6h, opt-in) like Self-Evolve, so we never re-bill on a heartbeat.
- **No new dependencies.** Reuses Flask + DuckDB + the existing eval modules + the `cm-cloud-*` interceptor pattern.

## 6. CrawlBar surface — "Pipelines" (smaller, Pro)

A **Pipelines** card/tab that treats crawler + cron *data jobs* like CrawlBar treats crawlers:
- Per-pipeline **last-run, freshness (age vs expected cadence), rows/items produced, status, doctor**.
- **Manifest discovery:** a pipeline (or harness adapter) drops a manifest (name, refresh cmd, freshness SLA, data-count query) — ClawMetry lists it with no code change, mirroring CrawlBar's `~/.crawlbar/apps/*.json` extensibility and reinforcing our multi-harness adapter roadmap.
- **Freshness alerts** reuse the existing Alerts engine ("pipeline X stale > SLA").
- This is where CrawlBar's "control plane for many local-first tools" idea lands inside ClawMetry without duplicating CrawlBar (we *observe*; we don't replace its menu-bar UX).

## 7. Phased rollout

1. **P1 — Deterministic trace score (no LLM).** Trace-walk checks (read-before-write, self-verify, recover, loop, tool-misuse) → Reliability Score + taxonomy in the snapshot; cloud Reliability tab (Pro). Cheap, always-on, immediately credible.
2. **P2 — Config ablation (cohort split).** Attribute failures to plugin/skill/model cohorts from existing traces. The conversion hook.
3. **P3 — Reliability trend + Self-Evolve link.** Daily score rollup (reuse Cost `dailyUsage` plumbing); Self-Evolve findings cite the score.
4. **P4 — Active replay (opt-in, `pass^k`).** Phase-3 regression-replay × k via `openclaw agent`; real config-vs-model swing. Bounded + gated.
5. **P5 — Pipelines (CrawlBar).** Manifest discovery + freshness/last-run/doctor + freshness alerts.

## 8. Success metrics
- **Conversion:** Free→Pro lift attributable to the Reliability tab / config-ablation CTA.
- **Engagement:** Reliability tab WAU among Pro nodes; drill-down clicks per session.
- **Trust:** scores never shown below the confidence floor (no "fake precision" complaints).
- **Cost discipline:** judge/replay LLM spend per node stays within the gated budget.

## 9. Open questions / risks
- **Score legibility for non-technical users** (our audience can barely `pip install`). The number + one-line "biggest lever" must lead; the taxonomy is secondary. Avoid jargon (no "Taguchi S/N" in the UI; keep that in tooltips/docs).
- **Low-volume nodes** → not enough runs for `pass^k`. Must degrade to "collecting data" honestly (the seed-noise lesson).
- **Mapping ClawBench's task-suite checks onto free-form production traces** — some checks (deterministic completion) assume a known goal; on real traffic we approximate via the agent's own stated objective + tool outcomes. Validate against Self-Evolve agreement.
- **Active replay side effects** — replaying a past input could re-trigger real tools (sends, writes). P4 must run in a dry-run/sandboxed mode or against read-only inputs only.
- **CrawlBar overlap** — keep Pipelines an *observability* surface; don't reimplement CrawlBar's control-plane actions beyond refresh/doctor passthrough.

---

*Inspirations: [openclaw/clawbench](https://github.com/openclaw/clawbench) (trace-based full-stack agent scoring) · [openclaw/crawlbar](https://github.com/openclaw/crawlbar) (manifest control-plane for local pipelines).*
