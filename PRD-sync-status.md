# PRD: "Syncing your data" + Transparent Status Log

**Status:** Draft → Build · **Date:** 2026-05-23 · **Owner:** Sync-Status working group
**Panel:** Principal UX Eng (industry patterns) · Principal Sync Eng (existing signals) · Principal Cloud Eng (snapshot delivery) · PM (personas / metrics)
**Related:** [PRD-tracing.md](PRD-tracing.md)

---

## 1. Problem

The cloud dashboard is **blank for the first 30s–2min after signup** while the daemon discovers the workspace, ingests JSONL/gateway/OTLP into DuckDB, and pushes the first encrypted snapshot. For a user who "barely pip installed", blank == broken. The cost is concrete:

- **Activation cliff.** Guided empty states lift activation ~60%; users decide in 3–5s whether to stay.
- **"Is it broken?" tickets.** Sentry's "Waiting for events" forum trail is the canonical example — users get stuck within minutes.
- **Patience window doubles** with a real progress bar (22.6s vs 9s median tolerance), but **fake** progress destroys trust the moment it finishes and the page is still empty.

**Today** ClawMetry shows: zeros in the model cards, a generic "Syncing your data… Overview will populate shortly" banner with no detail and no error path. Most tabs render zeros, a few say "no data," none narrate progress.

## 2. Personas & JTBD

- **Sam — semi-technical solo operator.** "When I just signed up, show me proof the daemon is working and an honest ETA, so I don't reboot or close the tab."
- **Priya — agency rep onboarding her first client.** "When my client is watching, label each step in plain English so the silence doesn't make me look incompetent."
- **Ravi — platform eng adding a fleet node.** "When I add node #5, confirm *this specific node* is Verified without SSHing in."

## 3. Use cases (prioritized)

| # | Pri | Story |
|---|-----|-------|
| U1 | P0 | First 60s — sticky banner with 5 named steps, active step pulses, honest ETA. |
| U2 | P0 | First few minutes — live counts per step ("Indexed 412 / ~1,200 sessions"). |
| U3 | P0 | Sync failure / partial data — inline actionable card (verbatim error, copy button, step-scoped Retry, docs deeplink). |
| U4 | P0 | Tabs show skeletons, not zeros, until first snapshot lands. Auto-clear when verified. |
| U5 | P1 | Returning after long absence — passive "Last verified 14d ago — resuming sync" pill. |
| U6 | P1 | Multi-node fleet — per-node sync chip (Verified / Syncing 67% / Stalled 4m). |
| U7 | P2 | Diagnostics download + per-step ETAs trained on volume. |

## 4. Existing signals (reuse, don't rebuild)

From the PE-Sync audit:
- `~/.clawmetry/sync_progress.json` — daemon writes `{phase, done, total, status, started_at, updated_at}` for **7 named phases**: `sessions_recent / memory / session_metadata / crons / channel_messages / sessions / complete`.
- `/api/sync-progress` — already serves the JSON.
- `/api/local/health` — `event_count, ring_depth, ring_dropped_total, last_flush_ago_s, sync_dlq_depth, oldest_ts, newest_ts`.
- Cloud already has a minimal `cm-sync-bar` that polls `/api/cloud/nodes` for `session_count > 0`.
- 16 named snapshot builders we can narrate.

**Gaps to fill:** frontend doesn't render the rich progress; no actionable error surface; no persistent `first_ready_at`.

## 5. v1 — what we ship

1. Sticky top-of-dashboard banner; auto-clear-when-verified.
2. **5-step stepper** rolled up from real phases: `Discovering → Indexing events → Aggregating → Pushing snapshot → Verified`.
3. **Per-step counts** + **honest ETA** = `elapsed × (1 − pct)/pct`, never a CSS timer.
4. **"Show details" drawer** — Vercel-style structured log: `HH:MM:SS  ✓ Discovered 247 session files`. Max 20 lines, no PII.
5. **Error card** when a step fails or `sync_dlq_depth > 0`: verbatim error + copy + step-scoped **Retry** + docs deeplink + **"Last successful sync"** timestamp.
6. **Skeletons replace zeros** on snapshot-fed tabs until first non-empty snapshot.
7. **Auto-clear** on three independent signals: phase=`complete`, `event_count ≥ 1`, 1h `verified` localStorage flag. Never time-only.
8. **Hard fail-safe:** after p99+30s with no progress, banner flips to the error card (no banner-that-never-clears).
9. **Sample-data escape hatch** (Sentry lesson): "Run a sample turn" button so users can verify the UI works pre-data.

### Out of v1 (deferred)
Diagnostics download · per-step ETAs trained on volume · multi-node aggregate sync view · resume affordance after long offline windows · server-side persistent `first_ready_at` column.

## 6. Differentiation

- **Zero-instrumentation = perfect telemetry.** We own the daemon — every step is a known state-machine transition. Progress is truthful, not theatre.
- **E2E-encrypted = server-confirmable counts only.** The banner derives from cardinality, never plaintext content. *"Verified 1,204 sessions, 0 readable to ClawMetry."*
- **$5/node flat.** No event meter, no "approaching limit" nudge in the banner.

## 7. Success metrics

- **TTFDV** (time-to-first-data-visible): p50 ≤ 30s · p90 ≤ 120s.
- **Activation:** % reaching a non-empty tab within 2 min → +25pp.
- **Banner-clear rate:** ≥98% reach Verified without manual intervention.
- **Support deflection:** "is it broken?" tickets -50% in 30 days.
- **Day-2 retention:** +10pp for cloud signups.

## 8. Risks & guardrails

- **Banner that never clears** → fail-safe to error card after p99+30s.
- **PII leakage in the log drawer** → step names + counts + durations + error codes only. **No paths, no message bodies, no tokens.**
- **Alarmist red for benign transients** → red gated on N retries or >30s.
- **AI-tell em-dashes** in banner copy → reviewed per the no-em-dashes rule.

## 9. Phased build

- **Phase 1 (this PR):** OSS-side rich banner. Renders the 5-step stepper from existing `/api/sync-progress` + `/api/local/health`; auto-clear on the 3 signals; minimal error card.
- **Phase 2:** Cloud-side richer surface — same component reading via cloud-proxy or snapshot key. Per-node sync chip on Fleet.
- **Phase 3:** Diagnostics bundle download + sample-turn escape hatch.

## 10. Panel sign-off

- **UX:** Vercel-style structured log + Sentry-lesson sample-data escape; never fake progress; auto-clear on real signals only.
- **Sync:** Foundation solid (`sync_progress.json` + 7 phases + `local/health`); rich render + error surface fills the gap.
- **Cloud:** Don't add a new readiness endpoint in v1 — use existing OSS endpoints + snapshot. `nodes.first_snapshot_at` lands in Phase 2.
- **PM:** Keep banner copy short, plain English, no em-dashes.
