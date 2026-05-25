## [Unreleased]

### Release: OpenClaw observability surfaces — turn anatomy, tool-policy/sandbox, v2 sub-agents (2026-05-25)
- Publishes three new observability surfaces that close the top gaps from the OpenClaw observability PRD (`docs/PRD_OPENCLAW_OBSERVABILITY_GAPS.md`), all built on the on-disk / `openclaw`-CLI data path (the gateway WS token grants zero scopes on a stock install, so RPC polling is not viable):
  - **Per-turn anatomy waterfall + stalled detector (#2118, P0-3):** `GET /api/turn-anatomy?session_id=…` decomposes a session into turns (events between `prompt.submitted` boundaries) and emits ordered spans — prompt → model call(s) → each tool (start→end via the `tool_call.id`→`tool_result.toolUseId` join) → compaction → reply — laid out on the wall-clock timeline; plus `GET /api/turn-anatomy/stalled` for sessions whose latest turn has had no event past a threshold. Reads existing DuckDB events (no new ingest); never silent-zeros (handles v3 + Claude Code/Codex shapes).
  - **Tool-policy + sandbox + exec-approval audit (#2119, P1-1):** a new Tool Policy tab showing per-agent sandbox mode + tool allow/deny (from `openclaw sandbox explain --json`, OpenClaw's own creds) and the exec-approval decision audit. New `run_ledger`-style `tool_policy` table + `sync_tool_policy` pass + bounded `toolPolicy` snapshot key + `/api/tool-policy` and `/api/approvals-audit`.
  - **v2 React Sub-Agents page (#2113):** replaces the "Coming soon" stub with the queue-lane monitor + run-ledger + sub-agent fan-out tree on `/api/run-ledger`, matching the v1 surface shipped in 0.12.319.

### Release: opencode + Qwen Code runtimes (2026-05-25)
- Publishes #2108. Two more standalone coding agents join the multi-agent pipeline, both built firsthand (installed + run against local Ollama, zero cost): **opencode** (SQLite `~/.local/share/opencode/opencode.db`; transcripts, model, tool calls, real tokens + cost) and **Qwen Code** (JSONL `~/.qwen/projects/<hash>/chats/<id>.jsonl`, Gemini-CLI lineage; transcripts, model, tool calls + thinking, token usage). Detected zero-config; in sessions + transcripts + runtime switcher. Full set now 11 runtimes: OpenClaw, PicoClaw, NanoClaw, Hermes, Claude Code, Codex, Cursor, Aider, Goose, opencode, Qwen Code. 153 compat tests green.

### Tracing tab is GA (2026-05-25)
- The Phoenix/Arize-style **Tracing** tab — every session as a trace, with a span **waterfall**, a **span tree**, an **agent graph**, and a span-detail drawer — is now shown in the nav by default for every install (it had been behind a `?tracing=1` flag while the span-detail drawer and daemon-proxy reliability were finished). Power users can hide it with `?tracing=0`. Verified live against the real daemon: lists real traces and renders a 361-span trace's waterfall + tree with per-span tokens/durations. (#2091)

### Fixed: $0 cost + mislabelled spans for Claude Code / adapter runtimes (2026-05-25)
- Traces (and the Cost tab, Overview, budgets) showed **$0 for sessions that clearly cost money** on the multi-runtime adapters (Claude Code, Codex, …): a real 430,291-token session read $0. Those events pre-set `token_count` (the lumped total) and stash the input/output/cache split under `data.extra` with no provider, so the #2049 derivation skipped them. Cost is now derived from that split × model pricing (cache-aware, provider inferred from the model), and the `claude_code` adapter carries cache tokens so new turns price cache-accurately. Verified: the $0 trace now reads **$29.578365**, an exact match to its raw-JSONL input/output ground truth.
- Also: those adapters use `event_type='message'` for both turns (speaker in `data.role`), so the trace builder rendered every assistant turn as a generic `event` span instead of a `chat`/llm span and never built a `prompt` span. Span classification now keys on `data.role` too, and prompt text is read from `data.content`. (#2107)

### Release: Aider + Goose runtimes (2026-05-25)
- Publishes #2098. Two more standalone coding agents join the multi-agent pipeline: **Aider** (`.aider.chat.history.md` per-project transcripts; model + token counts) and **Goose** (Block; SQLite `~/.local/share/goose/sessions/sessions.db`; transcripts, tool calls, real token totals). Both were built firsthand: the tools were installed and run against local Ollama (zero cost) to capture their real on-disk format, then verified against it. Each is one `_FAMILY_ADAPTER_SPECS` row + a switcher label. Detected zero-config; shown in the sessions list + transcripts + runtime switcher. The full agent set is now OpenClaw, PicoClaw, NanoClaw, Hermes, Claude Code, Codex, Cursor, Aider, Goose. 127 compat tests green.

### Fixed + Added: Emergency Stop All + Fix work everywhere (2026-05-25)
- **Fixed:** Emergency-Stop-All and the per-job kill used the dead v3 `_gw_invoke("cron",{action:"update"/"list"})` path — 502'd locally on v3 too. Migrated to `openclaw cron disable`, reading the **gateway's authoritative job list via the CLI** (not DuckDB, which lags ingest and risked silently disabling stale ids). Returns 409 with "approve the device pairing" guidance on scope-pending. (#2097)
- **Fixed:** The "🔧 Fix" button on errored crons was a stub (`# TODO: integrate with AI agent messaging system`) returning a fake "Fix request submitted" toast. Now actually shells `openclaw agent --session-id clawmetry-cron-fix-<id> --message <ctx> --json` in a daemon thread, giving the agent the cron's name/schedule/lastError/consecutiveFailures so it can investigate + apply a fix. Same escape hatch as Self-Evolve's Fix. (#2097)
- **Added:** Emergency Stop All + Fix work from the **cloud** via the heartbeat relay (`cron_killall` + `cron_fix` actions). Every cron button (create/run/toggle/edit/delete/kill-all/Fix) is now un-gated in cloud. Bulk EmergencyStop reports the disabled count; Fix's agent session shows up live in the Brain feed. (#2097 + cloud)

### Release: OpenClaw run ledger — queue-lane monitor + sub-agent runs (2026-05-25)
- Publishes #2096 (UI), building on #2092 (data layer, shipped in 0.12.318). OpenClaw 2026.5.x moved its background-run bookkeeping out of the now-empty `~/.openclaw/subagents/runs.json` into a unified SQLite ledger at `~/.openclaw/tasks/runs.sqlite` — so ClawMetry's sub-agent view had gone stale and the queue/lane scheduler was never observed. The sync daemon now mirrors that ledger into DuckDB (`run_ledger`: every sub-agent / cron / CLI run with status, delivery, timing and parent/child linkage), exposed via `/api/run-ledger` (+ `/tree`) and a bounded `runLedger` snapshot key. The **Sub-Agents** tab now leads with a live **Queue Lanes** monitor (`cli` / `cron` / `subagent` saturation bars — `runtime` *is* the OpenClaw queue lane — with running-vs-cap, idle/active and ✓/✗ counts) and a **Recent Runs** list. Verified against 147 live rows (read-only on the source; the production DuckDB writer was never touched). Closes the PRD's two top observability gaps (queue/lane + sub-agent runs).
- Why on-disk and not the gateway RPCs the PRD first assumed: the gateway WS token grants **zero scopes** on a stock install (every `operator.read` RPC is rejected, verified live), so the RPC path is blocked for most users; reading the SQLite read-only needs no scope and stays DuckDB-first. Design doc: `docs/PRD_OPENCLAW_OBSERVABILITY_GAPS.md`.

### Cost: price family-runtime (Claude Code / Cursor) sessions — Tracing & Cost showed $0 (2026-05-25)
- The Tracing and Cost tabs showed **$0.00** for Claude Code (and other family-runtime) sessions even with hundreds of thousands of Opus tokens. The #2049 cost backfill estimated cost only from `data.usage`, but family-runtime events carry the token split under `data.extra.{inputTokens,outputTokens}`, so they were skipped. The backfill now falls back to `data.extra`; existing events are re-priced on the daemon's next startup pass. Verified live: traces went $0 → up to $33.33 per session and `/api/usage` today went $0 → $501.58. Publishes #2093.

### Observability: ingest OpenTelemetry GenAI semantic-convention spans + derive their cost (2026-05-25)
- ClawMetry's OTLP `/v1/traces` receiver now maps the current OpenTelemetry GenAI semantic conventions (v1.37) — the shape MLflow's `@mlflow/mlflow-openclaw` tracer and other GenAI auto-tracers emit — so those spans light up the trace tree and cost views instead of landing with empty session/tool/agent. New keys mapped: `gen_ai.tool.name` → tool, `gen_ai.conversation.id` → session, `gen_ai.agent.id` → agent, `gen_ai.provider.name`, `gen_ai.input.messages`/`gen_ai.output.messages`, and the prompt-cache token keys. Because cost is not an OTel-standard span attribute, GenAI emitters ship token-only spans; ClawMetry now derives their cost the same way the event ingest does (#2049) — tokens × model pricing, cache-aware, provider inferred from the model — but only when the exporter sent none, so an explicit value (including 0 for a local model) still wins. All older `gen_ai.*`/`llm.*` keys remain mapped (purely additive). Makes ClawMetry a first-class, vendor-neutral consumer of any OTel GenAI emitter. (#2087)

### Robustness: daemon self-heals DuckDB index corruption (2026-05-25)
- A SIGKILL/OOM/reboot during a DuckDB write (especially a bulk UPDATE) can leave an explicit ART index out of sync with its table; the next DELETE/UPSERT then raises `FATAL: database invalidated... Failed to delete all rows from index`, every subsequent op fails, and the daemon crash-loops until manual recovery (1.4 GB+ file is fine; only the index is bad). Now the daemon main cycle catches the FATAL via `local_store.is_index_corruption_error`, calls `heal_index_corruption()` — drop every `idx_%` on a fresh connection, `CHECKPOINT`, re-run the schema DDL (idempotent `CREATE INDEX IF NOT EXISTS` rebuilds them clean from table data) — and continues. Verified end-to-end on a live 1.4 GB DB: 34 indexes dropped + 34 recreated, 929 events preserved, clean reboot. (#2081, closes #2073)

### Release: daemon self-heals DuckDB index corruption (2026-05-25)
- Publishes #2081 (closes #2073): the sync daemon now self-heals from DuckDB index corruption (kill-during-write) on the next cycle instead of crash-looping.

### Release: fix Claude Code double-count (OpenClaw-spawned sessions) (2026-05-25)
- Publishes #2078, a correctness follow-up to the multi-agent runtimes work (#2060). A Claude Code session that OpenClaw spawned was counted twice (once as `openclaw` via the claude-index ingest, once as `claude_code:<id>` via the new adapter). The daemon now reads OpenClaw's `sessions.json` index (`cliSessionIds`) and skips OpenClaw-owned Claude sessions in the `claude_code` ingest, so an orchestrated session shows once and standalone Claude Code sessions still ingest normally. Verified on a real machine: 29 of 387 `~/.claude` sessions were affected.

### Added: opt-in auto-update — install new releases automatically (2026-05-25)
- A new "Auto-update" toggle in the update banner. When on, ClawMetry installs each newly published release automatically instead of waiting for a click. The always-on background update-checker (in the dashboard server process, so it works with no browser open) runs the same vetted `pip install -U` + restart path the manual "Update now" button uses; off by default. On the hosted cloud the toggle shows "Auto-updates on Cloud" (the cloud is kept current centrally). Publishes #2074.
- Cloud half (#2075): each OSS release now rolls out to the hosted cloud hands-off — `auto-deploy-cloud.yml` waits for the new version on PyPI, then auto-merges the Dockerfile-pin PR once cloud CI is green (pin-only diff guard; the candidate smoke-gate still protects prod before traffic flips).

### Added: full cloud cron management — run/pause/edit/delete from the cloud (2026-05-25)
- Building on cloud cron-create (#2053), the per-row **Run Now / Disable-Enable / Edit / Delete** buttons (and the health-panel Pause) now work from app.clawmetry.com. Each relays through the heartbeat-piggyback transport: the cloud enqueues a `cron_action`, the local daemon runs the matching `openclaw cron` subcommand (its own creds; v3 dropped the gateway cron tool), and the E2E-encrypted result is posted back for the browser to decrypt — the cloud never sees plaintext. Bulk "Emergency Stop All" and the AI "Fix" button stay local-only. Also fixed: `run_openclaw_cron` only passes `--json` to the subcommands that accept it (enable/disable/run/edit reject it). (#2068)

### Subagents: "Finished N ago" used run duration, not end time (2026-05-25)
- The Overview Tasks card read "Finished 0s ago" for subagents that actually ended days ago. `_ovTimeLabel` computed the relative finish time from `runtimeMs` — a *duration*, which the dead-subagent freeze (#2038) forces to 0 for stale spawns — instead of an end timestamp. Now derived from `completionTs` then `updatedAt` (last activity) then `startedAt+runtime`; blank when genuinely unknown. Verified against a live node: 5-day-old spawns now read "Finished 4d ago". Pairs with #2062 (shipped in 0.12.311), which fixed the subagent Brain Events tab to match the `src`/`sessionId` fields the cloud feed emits. Publishes #2067.

### Release: multi-agent runtimes — Hermes, Claude Code, Codex, Cursor (2026-05-25)
- Publishes #2060. ClawMetry now observes many AI-agent runtimes, not just OpenClaw: **Hermes, Claude Code, Codex, and Cursor** join OpenClaw/PicoClaw/NanoClaw as first-class runtimes, each detected zero-config, read in its real native format via a dedicated read-only adapter, ingested into the local DuckDB store + cloud snapshot tagged with its runtime, shown in the sessions list + transcripts, and filterable via the Session replay runtime switcher.
- The pipeline is now adapter-driven: a single `_FAMILY_ADAPTER_SPECS` registry in `clawmetry/sync.py` is the source of truth for detection, ingest, dashboard registration, and the switcher. Adding a runtime is "ship an adapter + one registry row." Sessions/events are namespaced `<runtime>:<id>` and tagged so every existing read path returns them.
- New/completed adapters, each built and verified against a real install: **Codex** (`~/.codex` rollout JSONL, model + token usage from real `token_count` events), **Cursor** (`state.vscdb` SQLite, opened `mode=ro`+`query_only` so the uncheckpointed `-wal` holding the chat is visible), **Claude Code** (`list_events` added; user/assistant/thinking/tool_use/tool_result + token usage from `~/.claude/projects`), and **Hermes** (`~/.hermes/state.db`) wired through. Adapters are honest about what each runtime actually stores (e.g. Cursor has no billed cost on disk).
- Verified live, zero-config, on a real machine: detection found all six at once (PicoClaw, NanoClaw, Hermes, Claude Code, Codex, Cursor) and one ingest run landed their real sessions into DuckDB. 94 compat tests pass; see `docs/compatibility.md`.

### Cost: derive from tokens × model pricing (no more $0 for real usage) (2026-05-25)
- The Cost tab showed ~$0 for heavy usage (1.53M tokens summed to $0.0081) because cost came only from a provider-reported `cost_usd` that OpenClaw/OAuth events don't carry — nothing derived cost from tokens × model pricing. Now the daemon derives the API-equivalent cost at ingest from each event's own token split × model rate (cache-aware: Anthropic cache read 0.1× / write 1.25× of input rate; self-hosted models resolve to $0) and stores it, so aggregates, per-session costs, and budgets all reflect real spend. A one-time idempotent backfill recomputes `cost_usd` for events ingested before the fix. New `providers_pricing.provider_for_model` + `estimate_event_cost_usd`. Verified: real events derive to ~$443 (vs the old $0.008). (#2058, closes #2049)

### Release: cost derived from tokens × pricing (2026-05-25)
- Publishes #2058 (closes #2049): the Cost tab now shows real (API-equivalent) cost instead of ~$0 for OpenClaw/OAuth usage — derived at ingest from tokens × model pricing, with a backfill for historical events.

### Fixed + Added: cron writes on OpenClaw v3 + create-cron from cloud (2026-05-25)
- **Fixed:** Every cron write button (New Job, Delete, Pause/Enable, Run, Edit) was silently broken on OpenClaw v3. They called the gateway's `/tools/invoke` `cron` tool, which v3 removed ("Tool not available: cron"), and ClawMetry's gateway token is read-only — so every mutation 502'd. Migrated all cron writes to the `openclaw cron` CLI (uses OpenClaw's own creds, same as Self-Evolve's `openclaw agent`). Reads (list/runs) unchanged. When the gateway needs a one-time device-scope approval for writes, the API now returns a clear 409 with "approve the device pairing" guidance instead of a confusing 502. (#2053)
- **Added:** Create a cron from the cloud dashboard. The "+ New Job" button now works on app.clawmetry.com via the heartbeat-piggyback relay: cloud enqueues a `cron_create` action, the local daemon runs `openclaw cron add`, and the E2E-encrypted result is posted back for the browser to decrypt — the cloud never sees plaintext. Mirrors the Self-Evolve "Fix" relay. (#2053 + cloud)

### Release: runtime switcher on Session replay (2026-05-25)
- Publishes #2050. When OpenClaw + PicoClaw + NanoClaw run on the same node their sessions share one dashboard; the Session replay (transcripts) tab now has a **Runtime** chip-switcher to scope the list to a single runtime for a clean deep-dive, with **All** (merged) as the default. Chips show per-runtime counts and only appear when more than one runtime is present; the choice persists. The runtime is derived from the namespaced session id (`picoclaw:` / `nanoclaw:`), so it works identically locally and in the cloud with no server change. Verified live (OpenClaw 27 / PicoClaw 1 / NanoClaw 2): selecting PicoClaw narrows to its session, All restores the merged view.

### Release: i18n RTL support (Arabic / Hebrew / Persian / Urdu) + Noto fonts (2026-05-25)
- The dashboard now supports **right-to-left languages**: Arabic, Hebrew, Persian, Urdu (36 languages total). Picking one flips the whole UI to RTL (sidebar moves right, nav mirrors) via `<html dir="rtl">`, with targeted CSS so the layout mirrors correctly while numbers, code, log lines and costs stay LTR. Extended the font stack with Noto Sans per-script families and load subsetted Noto Sans Arabic + Hebrew webfonts so glyphs render even without system fonts. All translations generated by the local Claude CLI bot. Publishes #2047.

### Release: fix the syncing banner sticking forever on "Aggregating: crons" (2026-05-25)
- The "Syncing your OpenClaw workspace" banner stuck on **Aggregating: crons** indefinitely even though sync was healthy (events + E2E snapshots flowing every ~60s). Root cause: the progress banner is a fresh-install affordance, but the steady-state main loop calls `sync_crons()` (and the other phase fns) every tick, each recording its phase as `running` on entry, re-opening the banner forever (it pinned on `crons` because `sync_crons` early-returns with no cron `jobs.json` and never recorded a terminal state). Fix: once the initial sync reaches `complete`, steady-state phase updates are suppressed (a daemon restart still shows the initial-sync banner); `sync_crons` now records a terminal state on the no-cron-file path. Regression-tested. Publishes #2042.

### Subagents: actually freeze runtime — ignore poisoned cache (2026-05-25)
- Follow-up to the runtime-freeze fix: the first cut (#2032, 0.12.305) only recomputed when `runtime_ms` was absent, but the daemon caches a `runtime_ms` that is itself a `now - spawn` re-derived every snapshot (observed 402M → 403M → 404M, ever-growing), so the cached value was truthy and the fix never ran — stale subagents still climbed to "112h". Caught by verifying against the live DuckDB store, not synthetic rows. Now non-active (idle/stale/completed/failed) subagents ALWAYS recompute frozen at last activity and ignore the cached value; active/running keep the live clock. Verified: all 8 stale subagents 404198958ms → 0. (#2038, closes #2031)

### Release: subagent runtime freeze (real fix) (2026-05-25)
- Publishes #2038 (closes #2031): the Active-Tasks runtime for dead/stale subagents stops climbing — supersedes the incomplete 0.12.305 fix.

### Subagents: freeze runtime for dead subagents (2026-05-25)
- The subagent / Active-Tasks tracker showed an ever-growing runtime ("111h 50m" and climbing) for `stale` subagents — `_try_local_store_subagents` derived runtime as `now - spawned_at` when the daemon hadn't cached a value, so an agent that died days ago looked like it was still running for 4.6 days. Runtime is now active *work* time: status is computed first, only `active`/`running` agents' clocks run to now; `idle`/`stale`/`completed`/`failed` freeze at last activity (`ended_at`, else last `updated_at`). The daemon's cached `runtime_ms` still wins. (#2032, closes #2031)

### Release: subagent runtime freeze (2026-05-25)
- Publishes #2032 (closes #2031): dead/stale subagents stop displaying an ever-growing runtime; the Active-Tasks runtime now reflects real active work time.

### Release: PicoClaw + NanoClaw sessions in the sessions list + transcripts (2026-05-25)
- Publishes #2028 (phase 3b of NanoClaw/PicoClaw support; builds on #2013 adapters + #2014 cloud runtime label). PicoClaw and NanoClaw sessions are now fully observable the way OpenClaw sessions are: they appear in the sessions list and render as transcripts, locally and in the cloud.
- The sync daemon's new `sync_family_runtimes()` reads each detected runtime's sessions + events through the reader adapters and maps them onto the SAME DuckDB rows OpenClaw uses, via the daemon's own writer handle: `agent_type='openclaw'` so every existing read path returns them with no filter changes (runtime carried in `metadata.runtime` + `data._runtime`), session ids namespaced (`picoclaw:<key>` / `nanoclaw:<id>`) to avoid PK collisions, renderable event types so transcripts render and counts work, and float-epoch timestamps converted to the ISO strings DuckDB expects. Session rows are also pushed to `/ingest/sessions` so the cloud sessions list shows them; transcripts ride the existing snapshot builder. Gated by `_sync_allowed()`, throttled 60s, no `local_store.py` changes.
- The sessions list (`_try_local_store_sessions`) now surfaces `model` (from `metadata.recent_model`) and `runtime`, filling the model column for family sessions and for OpenClaw sessions on the local-store read path.
- Verified live end to end on a real node: `/api/sessions` shows the PicoClaw + NanoClaw rows, `/api/transcript` renders the PicoClaw session in full (user → assistant → exec tool call + args → tool result → summary), and the decrypted live cloud snapshot carries all three family transcripts. CI: `tests/test_family_runtime_ingest.py` in the moat-tests job; 45 compat tests green on Python 3.9.

### Release: i18n — 32 languages live (2026-05-25)
- The dashboard now ships **32 languages** (en + zh-CN, zh-TW, es, es-419, hi, bn, ta, te, kn, ml, mr, gu, pa, pt-BR, pt-PT, ja, ko, fr, de, it, nl, pl, ru, uk, tr, id, vi, th, fil, sv, el). All generated from the English source by the autotranslate bot running on the local Claude Code CLI (no API key), with glossary + placeholder integrity enforced and key-parity CI-gated (every locale carries the full 85-key catalog). Pick a language from the top-right switcher; choice persists across reloads and surfaces. Publishes #2024. See docs/PRD_I18N.md.

### Perf/correctness: dashboard audit — reliability scoring + overview self-poll (2026-05-25)
- Proactive sweep for siblings of #1954 (prefix-only `clawmetry-` matcher) and #1969 (ungated pollers). (1) `sync.py`'s reliability/score builder skipped helper sessions with `sid.startswith("clawmetry-")`, missing the full OpenClaw form `agent:main:explicit:clawmetry-*` — so ClawMetry's own selfevolve/probe runs could pollute the user's real-agent reliability score; now uses the central `is_clawmetry_internal_session` matcher (both forms). (2) `overview.html` had a second, independent `/api/overview` self-poll firing every 60s with no `document.hidden` gate (decoupled from app.js's `loadAll`, so #1969's coalesce window couldn't reach it); now gated on visibility. (#2020, closes #2019)

### Release: dashboard audit fixes (2026-05-25)
- Publishes #2020 (closes #2019): reliability scoring excludes ClawMetry helper sessions in both id forms, and the Overview heartbeat card stops self-polling `/api/overview` while the browser tab is hidden.

### Release: UI polish + observability backlog (2026-05-25)
- Security tab: warnings elevated, passing checks collapse to pills, calm "all clear" state (#1953).
- Session replay: tool chips expand by default; Self-Evolve runs hidden behind "Show plumbing" (#1975, #2001).
- New: Dives tab (plain-English to SQL to chart, #1976), intent-vs-execution divergence (#1977), outbound OTLP GenAI exporter to Datadog/Grafana/Honeycomb (#1978), proxy velocity breaker + per-session budget fence (#1979).
- v2 rails: Brain timeline at /v2/brain (#2006).

### Release: NanoClaw + PicoClaw runtime support, validated against live installs (2026-05-25)
- Publishes #2013 + #2014. ClawMetry now observes two more OpenClaw-family runtimes via reader adapters for their **real** native session formats (verified by actually installing and running both, not by assuming a shared layout). This corrects #956/#1981, whose premise that NanoClaw and PicoClaw "share the OpenClaw on-disk layout exactly" was false for both.
  - **PicoClaw** (`sipeed/picoclaw`, Go): flat `providers.Message` JSONL at `~/.picoclaw/workspace/sessions/<key>.jsonl` (+ `.meta.json`). `clawmetry/adapters/picoclaw.py` reads transcripts, model, and tool calls. Running it for real (v0.2.9 + local Ollama) caught two bugs the relabeled-OpenClaw fixtures could not: tool calls are OpenAI-nested under `function.{name,arguments}` (a flat read dropped them), and Go trims trailing zeros from fractional seconds, which made `datetime.fromisoformat()` raise on Python 3.9/3.10 and zero the timestamp. Tokens/cost are not on disk, so they are honestly surfaced as 0/unavailable.
  - **NanoClaw** (`nanocoai/nanoclaw`, TS): per-session SQLite (`inbound.db`/`outbound.db`) under a CWD-relative `<checkout>/data/v2-sessions/`. `clawmetry/adapters/nanoclaw.py` opens them strictly read-only + immutable and merge-sorts inbound/outbound by `seq`. NanoClaw has no `~/.nanoclaw` and no env var, so detection discovers common checkout locations plus a `CLAWMETRY_NANOCLAW_DIR` override. Model/tokens/cost are not in the message tables (the SDK transcript with usage lives in the container and is rotated), so they are surfaced as unavailable.
  - **Cloud runtime label:** the sync daemon detects these runtimes (pure detection, no DuckDB/writer-lock) and ships the result in the encrypted snapshot (`runtimeInfo.items[]` rows + a small `detectedRuntimes` key). The cloud Runtime panel shows the runtime next to OpenClaw with no cloud code change. Live-verified by decrypting a real node's snapshot (`PicoClaw: detected (1 session)`, `NanoClaw: detected (2 sessions)`).
  - Ships real captured sessions as fixtures (`tests/fixtures/runtimes/<rt>/REAL/` + PROVENANCE) and CI tests (`test_picoclaw_adapter.py`, `test_nanoclaw_adapter.py`, `test_runtime_detection_snapshot.py`) wired into the `moat-tests` job. See `docs/PRD_PICOCLAW.md`, `docs/PRD_NANOCLAW.md`, `docs/compatibility.md`.

### Release: LLM Context Inspector OSS↔cloud parity (2026-05-25)
- Publishes #1983: `/api/overview` now filters `clawmetry-*` plumbing sessions out of the main-session pick AND `sessionCount`, so OSS no longer surfaces a 204K SelfEvolve run as the user's main session (fixes the live divergence where the LLM Context Inspector showed `204.5K / 200K (100%)` on OSS while the cloud snapshot for the same node correctly showed `37.8K / 200K (19%)`). Adds two new `/api/overview` response fields the LLM Context tab now reads as the single source of truth on both sides: `currentContextTokens` (live prompt size from the latest assistant turn — the right value for a "Context Window Usage" gauge; `mainTokens` was cumulative and exceeded the window after a couple of turns) and `skillHeaderTokens` (real header-token sum, replacing the misleading `contextWindow*0.008 = 1.6K` approximation the frontend fell back to when `/api/skills` is 410-Gone in cloud). `query_context_window_peek` also gains an `exclude_clawmetry=True` default with a 4× over-fetch so a burst of plumbing rows can't crowd the user's real session out of the scan budget. Cloud-side snapshot + frontend halves shipped earlier under #1956.

### Release: surface a down inbound channel loudly (2026-05-24)
- Publishes #1996 (follow-up to the connector-liveness detector). A red top banner now appears the moment an enabled inbound channel's poll goes **down** ("Telegram is not receiving messages. Inbound down 37h. Your agent can still send, but is not hearing replies."), driven by `/api/system-health.connector_liveness`. The classifier moved to `clawmetry/connector_health.py` (shared so the dashboard and the daemon snapshot agree), and `sync_system_snapshot` now ships a `connectorLiveness` key so the cloud dashboard has the data too. This is the loud half of the alarm that was missing when a node went deaf for ~37h with everything showing green.

### Release: connector-liveness alarm + cloud Brain hygiene (2026-05-24)
- Publishes #1992 + #1990, both born from a real incident: an OpenClaw node (Diya) went **deaf for ~37h** — its Telegram inbound long-poll wedged after a network stall (the abort timed out and it never restarted) while outbound (scheduled crons) kept firing, so nothing looked broken and ClawMetry showed green the whole time.
- **Added — connector-liveness detection (#1992):** the sync daemon now tails **both** `gateway.log` and `gateway.err.log` for channel inbound-poll lifecycle signals (`starting provider`, `Polling stall detected`, `health-monitor … reason: disconnected`, `channel stop exceeded … abort`) and records them as `connector.health` events. `/api/system-health.connector_liveness` classifies each **enabled** channel (from `openclaw.json`) as `down` / `degraded` / `ok` / `unknown` — `down` meaning "most-recent signal is a stall/disconnect/wedge with no recovery for ≥15m → this channel can no longer receive messages." This is the alarm that was missing: gateway health is process-level (the process was alive), and the prior per-channel `mins_ago` couldn't tell a dead poller from idle traffic. Pinned against the real production log lines; live-verified (93 signals ingested). Prominent UI + cloud-snapshot surfacing follow.
- **Fixed — Self-Evolve leaked into the cloud Brain feed (#1990):** `_build_brain_cache_pushes` pushed events to the cloud cache without the `hide_clawmetry_session()` filter the OSS-local Brain path applies, so `clawmetry-selfevolve` / `clawmetry-fix` helper sessions were hidden locally but shown on app.clawmetry.com. Now filtered at the `_rows_to_brain_events` chokepoint (with query headroom so the feed still lands ~50 real events).
- **Fixed — redundant provenance JSON in Brain detail (#1990):** channel adapters stack two `(untrusted metadata)` blocks ("Conversation info {chat_id,sender,…}" then "Sender {label,id,name}") ahead of a user message; the parser stripped only the first, so the second echoed the sender as raw JSON even though the provenance pill already shows it. Now strips every leading provenance block; a real ` ```json ` message body is still never eaten.

### Release: i18n Phase 0 foundation (2026-05-24)
- Publishes #1987: the dashboard now ships the internationalization foundation — a top-right language switcher, auto-detection, a vanilla `Intl`-backed runtime, and a JSON catalog under `static/locales/` (en + ja/fr + en-XA pseudolocale). Pure frontend chrome; cloud picks it up on the next OSS pin bump. Full string extraction + the ~30-language autotranslate bot follow in later phases. See `docs/PRD_I18N.md`.

### i18n Phase 0: internationalization foundation (2026-05-24)
- First slice of the i18n initiative (`docs/PRD_I18N.md`): the dashboard can now render in multiple languages with a **top-right language switcher**, auto-detection, and a choice that persists across reloads and surfaces. No build step, no new dependency — a vanilla runtime (`static/js/i18n.js`) translates `data-i18n` DOM nodes, exposes `window.t()` for JS strings (Phase 1 onward), and formats numbers/dates/plurals via native `Intl.*`. A flat JSON catalog under `static/locales/` (`en.json` source of truth + `_meta.json` registry, shipped in the wheel and shared with the upcoming v2 React SPA, see #1986) drives both. Detection precedence: `?lang=` > `cm-lang` cookie (`.clawmetry.com`-scoped for cross-surface consistency) / localStorage > `navigator.languages` > English; a missing key falls back to English, never blank. Ships `en` + proof translations `ja`/`fr` + an `en-XA` pseudolocale (dev) for extraction-coverage QA. A starter set of strings (left-nav labels + overview header) is marked; full string extraction is Phase 1. CI guard (`tests/test_i18n_catalog.py`) enforces locale key-parity with English. Verified live in the running dashboard.

### Perf: gate background pollers + coalesce loadAll fan-out (2026-05-23)
- The dashboard was firing a request storm regardless of the active tab and while the browser tab was hidden — in a 25-second sample: `/api/local/health` × 13, `/api/sync-progress` × 12, `/api/cloud/approvals` × 5, `/api/overview` × 3 in a single second, `/api/budget/status` × 3. Four ungated/uncoalesced pollers that pre-dated PRD #1252's visibility wrapper. Fixed: routed `_cmSyncTick` and `_cmOnboardingTimer` through `visibilitySetInterval` and bumped them to 15 s (banners still self-dismiss on the verified/heartbeat-landed state, so on-tab time-to-clear is unchanged); added a `document.hidden` gate on the approvals nav-badge poll; added an in-flight Promise reuse + 2 s recently-completed coalesce window to `loadAll()` so heartbeat-landed / connection-restored / switchTab / periodic-interval bursts share one fetch instead of stampeding. (#1970, closes #1969)

### Release: gate background pollers (2026-05-23)
- Publishes #1970 (closes #1969): the dashboard no longer fires `/api/local/health` and `/api/sync-progress` every 2.5 s on every tab — gated on the visible tab and slowed to 15 s, with `loadAll()` callers coalesced so they share one fetch instead of bursting.

- **Improved:** `clawmetry connect` now offers a one-time conversion choice when the local-only marker is set AND a human typed the command in a terminal: `[1] Sign up for cloud` (removes the marker, proceeds with email/OTP) or `[2] Keep local-only`. Automated callers — `install.sh`, `curl | bash`, any invocation with `--key-only` / `--no-daemon` / `--key=` / `--enc-key=`, or any non-TTY environment — still silent-refuse, preserving the #1937 fix so updates never re-prompt. `--force` keeps its one-shot bypass. (#1966)
- **Improved:** Session-replay (Embodied) list now renders ChatGPT-style titles (first user prompt, truncated) on top with the UUID demoted to a muted sub-line. Snapshot-side derivation in `clawmetry/sync.py:_build_transcripts`; renderer in `static/js/app.js:loadTranscripts`. Backwards-compatible — old snapshots still render, just with "Untitled session". (#1962)

### Alerts: kill alert fatigue (2026-05-23)
- The Alerts tab's *Recent alert history* was unusable: every row read "20576d ago" (~56 years), runs of identical alerts (5 dup `token_velocity`, 2 dup `stuck_session`) stacked as separate rows, and ClawMetry's *own* helper sessions (`clawmetry-fix`, `clawmetry-selfevolve`, `clawmetry-subagent-t`) fired user-visible stuck-session alerts they should never have triggered. Fixed with: (1) `alerts.js#formatTimeAgo` normalizes epoch-seconds-as-number (the API stores `fired_at` as `time.time()` seconds; JS was treating it as ms → epoch 0 → ~20576 days); (2) `renderHistory` filters rows >3 days old and collapses consecutive identical alerts into a single row with a "× N" badge; (3) each row has a hover tooltip explaining what the alert type means; (4) `is_clawmetry_internal_session` now matches the full OpenClaw session-id form (`agent:main:explicit:clawmetry-*`) in addition to the bare prefix, so the stuck-session evaluator no longer fires on our own plumbing (same root-cause class as cloud#1063). (#1957, closes #1954)

### Release: alerts cleanup (2026-05-23)
- Publishes #1957 (closes #1954): kills the "20576d ago" timestamps, collapses duplicate alert rows, hides internal helpers from stuck-session alerts, adds 3-day TTL + hover tooltips on the Alerts tab.

- **Added:** Persistent local-only mode (closes #1937). Set `CLAWMETRY_NO_CLOUD=1` or `touch ~/.clawmetry/nocloud` and the sync daemon keeps ingesting OpenClaw events into your local DuckDB but skips every cloud POST (heartbeat, snapshot, /ingest/*). The localhost dashboard stays fully usable; updates no longer silently re-prompt for an email. `clawmetry disconnect` now writes the marker for you, removes the stale sync-progress file so the dashboard banner stops lying, and prints how to re-enable. `clawmetry connect` refuses politely when the marker is set (override with `--force`). New `/api/cloud-status` gates the sync-progress banner so it doesn't appear when there's nothing to sync. (#1956)
- **Improved:** Stuck-session banner now shows the actual task (first user prompt > displayName > channel·agent·model > UUID), an "Open session →" button that deep-links to the transcript, and renames the left-nav tab from "Embodied β" to "Session replay (beta)" — the universal name used by LogRocket/Hotjar/Sentry/Datadog. (#1952)
- **Fixed:** In-app "Update now" was failing with `No module named pip` on uv-provisioned daemon venvs (every user on the uv-bootstrapped install). Bootstrap pip via stdlib `ensurepip --upgrade --default-pip` first, capture pip's real stderr so the banner shows *why* it failed instead of just `exit 1`, and pass `--no-cache-dir` to dodge the uv-cache-stale race. (#1948)

### Release: Transparent sync-status banner (2026-05-23)
- Publishes #1943: first-install "Syncing your OpenClaw workspace" banner with a 5-step stepper (Discovering → Indexing events → Aggregating → Pushing snapshot → Verified), live counts and honest ETA from the daemon's existing /api/sync-progress + /api/local/health signals, an expandable structured log (no PII), and an actionable error card when sync queues a retry or stalls. Auto-clears on three independent signals. No new endpoints. PRD-sync-status.md ships alongside.
- **Fixed:** Alerts tab on OSS shows the Approvals-style 6-toggle list again. PR #1885 had silently rewritten `alerts.js` end-to-end (+333/-484) while claiming a one-block scope, reverting #1840 / #1847 / #1851 / #1854. Restored the pre-#1885 file and re-applied only the intended Manage-channels patch. (#1944)

### Release: Self-Evolve accuracy fix + backlog (2026-05-23)
- Publishes the Self-Evolve accuracy hardening (#1929 — no more false "broken/regression" findings from absence-of-usage) plus a merged backlog: OTel spans from JSONL (#1931), tabbed span-detail panel (#1936), /api/dives (#1932), config-drift badge (#1826), /api/component/mcp (#1827), runtime DuckDB fast-path (#1887), outcomes impact API (#1824), 503-banner wiring (#1825), alerts manage-channels (#1885), and CI/e2e hardening (#1850/#1886/#1888/#1889/#1891).

### Release: Skills in cloud + remove Classic nav (2026-05-23)
- Publishes #1926 (skills ship in the cloud snapshot so the Skills tab works on app.clawmetry.com) and #1927 (removed the dead Classic-nav link).

### Release: cron Calendar with notification counts + month grid (2026-05-22)
- Publishes #1923. The Crons Calendar sub-tab now shows "Fired so far" (lifetime runs) and "Upcoming (30d)" (predicted fires across all active jobs over the next 30 days), plus a current-month grid marking past actual runs (green / red on failure) and future predicted fires (blue) per day. New `_cronEnumerateFiresMs` walks the schedule forward (capped); the run loader widened from 7 to ~40 days so past runs land on the right cells. Counts work in cloud too (future fires are computed client-side from the schedule).

### Replay: tool turns deep-dive into name + args + result (2026-05-22)
- The Embodied/replay tab rendered every tool turn as a generic "Tool call" / "Tool result" chip with no tool name, input, or output. Root cause was a data bug, not cosmetics: Claude-Code rows nest the Anthropic message under `data.message` and record tools as content blocks (`tool_use` / `tool_result`), but the transcript builder only read top-level `content` and a top-level `tool_calls` key, so it dropped the name/args/result entirely (verified on real data: 13/15 turns of one session arrived blank, another was 118/178 blank). The builder now lifts each tool block into a named turn carrying its input/output, the replay renders an expandable deep-dive chip (tool name in the header, exact args/result one click away), and the duplicate empty-noise turns those rows used to produce are gone. Cloud-snapshot tool detail is bounded (600-char preview within an 8 KB/transcript budget) so it never bloats the shared snapshot; full detail stays on the local dashboard.

### Release: replay tool deep-dive (name + args + result) (2026-05-22)
- Publishes #1912 (closes #1911): the Embodied/replay tool turns now show the tool name and expandable input/result instead of nameless "Tool call"/"Tool result" chips.

### Release: gate the Tracing tab behind a flag (2026-05-22)
- Publishes #1914: the Tracing tab is hidden from the nav by default and revealed only with ?tracing=1 (or ?tab=tracing) while the span-tree view is reworked.

### Release: cron schedule renders correctly + run-history no longer 502s (2026-05-22)
- Publishes #1908. Two cron-tab bugs: (1) a cron's schedule rendered as a literal `{}` because the sync daemon flattened OpenClaw's structured schedule to a string and read the wrong field name (`cron` instead of `expr`), collapsing to an empty dict; the daemon now persists the full `{kind,expr,tz}` schedule and the frontend `formatSchedule` is hardened to never print raw JSON. (2) Clicking a cron row showed "Could not load run history (HTTP 502)" because the frontend threw on the legacy gateway endpoint (which always 502s in cloud); it's now best-effort so the DuckDB-backed timeline drives rendering and shows "No run history yet" instead. Also teaches `cronToHuman` the hour-range form (e.g. `37 9-21 * * *` becomes "at :37 hourly, 09:00 to 21:00").

### Release: cloud snapshot — traces + memory-access keys, snapshot perf fix (2026-05-22)
- Publishes #1905: the daemon now ships `traces` and `memoryAccess` in the snapshot (cloud half of the Tracing tab and Memory access log), hides `clawmetry-*` helper sessions from the snapshot, and strips the per-message `raw` payload from snapshot transcripts to keep the shared snapshot small (the raw toggle stays a local-dashboard feature).

### Release: Tracing tab + memory access log + internal-session hiding (2026-05-22)
- Publishes three changes: the Tracing tab (#1903), the memory access log (#1900, closes #1896), and hiding ClawMetry's own helper sessions from user-facing views (#1902).

### Tracing: Phoenix/Arize-style Tracing tab (2026-05-22)
- New Tracing tab under Live trace: a list of every trace (session), and on click a span waterfall, a span tree, and an agent graph (main → sub-agents). Events-first, so it works without any OTLP exporter; OTel spans merge in when present. New endpoints `/api/traces` and `/api/trace/<id>`, DuckDB-first.

### Memory: access log (when memory was read + which conversation triggered it) (2026-05-22)
- The Memory tab has a new "Access log" view showing every memory tool access (memory_search / memory_get) with its query, time, and originating session. Click a row to open the conversation that triggered it. New `/api/memory-access` endpoint, DuckDB-first.

### Sessions: hide ClawMetry's own helper sessions from user-facing views (2026-05-22)
- Sessions ClawMetry spawns to do its own work (Self-Evolve, Fix-with-AI, memory probes — all named `clawmetry-*`) were leaking into stuck-session alerts, the transcripts list, the active-sessions list, the Brain feed, and the memory access log. They are now hidden by default (override with `CLAWMETRY_SHOW_INTERNAL_SESSIONS=1`) so our plumbing doesn't mix with the user's agent activity.

### Release: Transcript raw payload toggle (2026-05-22)
- Publishes the raw ↔ pretty transcript toggle (#1898, closes #1895): see the exact JSON payload OpenClaw recorded for each turn, with a Copy button.

### Transcript: raw ↔ pretty payload toggle (2026-05-22)
- The transcript viewer has a new "{ } Raw" toggle that flips the whole conversation between the beautified turns and the verbatim JSON payload OpenClaw recorded for each turn — requested by users who want to study OpenClaw's exact behavior, not just read a cleaned-up transcript. The raw payload is capped per-message (12 KB, with a truncation marker) so it never bloats the response or the cloud snapshot it rides into. Adds a `raw` field to `/api/transcript/<id>` messages, populated DuckDB-first from the already-ingested event data.

### Release: Self-Evolve on-demand only (2026-05-22)
- Publishes the on-demand Self-Evolve change (#1892): no more hourly Opus auto-run; runs only when you click Analyze/Re-analyze.

### Self-Evolve: on-demand only (no more hourly auto-run) (2026-05-22)
- Self-Evolve no longer runs on a timer — it was spending Opus turns on a schedule (the job flagged itself for it) and re-ran on every daemon restart (in-memory clock). It now runs ONLY when you click Analyze/Re-analyze. Local uses /api/selfevolve/analyze; cloud uses a new `selfevolve_analyze` heartbeat-relay action so the Re-analyze button triggers a fresh run on the daemon. Opt back into periodic refresh with CLAWMETRY_SELFEVOLVE_AUTO=1.

### Release: Self-Evolve "Fix with AI" (local + cloud relay) (2026-05-21)
- Publishes the Fix-button feature (#1876 local, #1878 cloud relay + daemon `selfevolve_fix` action) and the daemon gateway-token detection fix.

### Self-Evolve: "Fix with AI" cloud relay (2026-05-21)
- The Fix button now works from app.clawmetry.com: the cloud queues an authenticated, owner-scoped `selfevolve_fix` action on the heartbeat-piggyback relay; the local daemon runs `openclaw agent` in a background thread and posts the E2E-encrypted result to the cloud cache, which the browser polls + decrypts. Button is no longer gated to the local dashboard.

### Self-Evolve: "Fix with AI" button on findings (2026-05-21)
- Each Self-Evolve finding now has a "✨ Fix with AI" button. Clicking it (after a confirm) dispatches the finding's suggestion to your local agent via `openclaw agent` (OpenClaw's own creds — ClawMetry's gateway token is read-only), which actually applies the change. Status shows Queued → Agent working → ✅ <summary>. Local dashboard for now; the cloud relay is a follow-up. New endpoints: `POST /api/selfevolve/fix`, `GET /api/selfevolve/fix/status`.

### Fix: daemon detects gateway token (snapshot auth_token_status was false "missing") (2026-05-21)
- `_build_diagnostics()` runs in the sync daemon, where `dashboard.GATEWAY_TOKEN` is never populated (the daemon doesn't run the dashboard's startup detection) and `OPENCLAW_GATEWAY_TOKEN` is unset under launchd — so the snapshot reported `auth_token_status="missing"` even when `openclaw.json` has a gateway token. Cloud showed "Auth token: missing" and Self-Evolve generated false HIGH-severity findings. Now falls back to `_detect_gateway_token()` (the same detector the dashboard + Security posture use).

### Replay: tool turns as compact chips (2026-05-21)
- Empty tool_use/tool_result bubbles now render as compact role-accented chips instead of blank boxes.

### Perf: tab-scope system-health fan-out (2026-05-21)
- loadSystemHealth (4 endpoints) polled on every tab; gated to Overview.

### Perf: tab-scope tool prefetch (2026-05-21)
- _prefetchToolData polled 12 component/tool endpoints every 30s on every tab; gated to Flow/Overview.

### Perf: tab-scope updateFlowStats (2026-05-21)
- The Flow-tab live-stats timer polled /api/overview on every tab. Gated to Flow/Overview.

### Perf: tab-scoped Overview polling (2026-05-21)
- The Overview refresh fan-out (loadAll: health/heartbeat/diagnostics/skills/reliability/…, the brain stream, overview-tasks, token-velocity) polled regardless of the active tab, bursting requests on every screen. Now gated on the active tab so they pause off Overview.

### Alerts: toggle reflects saved rules (flatten condition_json) (2026-05-21)
- The daemon nests alert_type/threshold inside condition_json; the toggle render checked top-level alert_type and never matched, so a saved rule showed OFF. Flatten condition_json. Completes the alerts toggle e2e.

### Alerts: saved rules render on load (decrypt key fix) (2026-05-21)
- loadAlertsPage decrypted the E2E rules_blob via a helper with the wrong key name + a missing decryptBlob, so saved rules silently never rendered. Self-contained decrypt mirroring the cm-cloud interceptors. This is the fix that makes Enable/toggle stick across reloads.

### Alerts: toggle persists through cache lag + dedup (2026-05-21)
- Optimistic toggle state now survives the cloud-cache-warm window (no flicker-revert) and rapid clicks no longer create duplicate rules.

### Alerts: fix toggle row layout (restore status dot for the grid) (2026-05-21)
- The always-show-toggles render dropped the status dot; the row is a 5-column grid so the title column collapsed and wrapped. Re-added the dot.

### Alerts: all types always shown as toggles (Approvals pattern) (2026-05-21)
- The Alerts tab now always lists the canonical alert types as on/off toggles (default OFF), mapping each to a saved rule so types stay visible after you enable one (previously enabling one hid the rest). Optimistic flip + delayed reload so the switch responds instantly.

### Alerts: on/off toggle switch (default OFF), matching Approvals (2026-05-21)
- The Alerts tab now uses the same on/off slider as the Approvals protection rules instead of an Enable button. Examples render OFF; flipping the slider POST-creates+enables the rule (OFF->ON) or disables it (ON->OFF), with a delayed reload so it flips without a manual refresh. Approval protection policies now also seed DISABLED (opt-in) by default.

### Alerts: saved rules now render (decrypt the E2E rules_blob) (2026-05-21)
- Follow-up to the alerts Enable fix. The Alerts tab read plaintext `data.alerts`, but a cache hit returns the rule list as an E2E-encrypted `rules_blob` only the browser can decrypt — so a rule the user just enabled was created + cached but never rendered (tab stayed on canned examples). loadAlertsPage now decrypts `rules_blob` via unwrapListAsync. Completes the Enable -> Enabled (with Disable) e2e.

### Alerts Enable works e2e + dashboard no longer locks the DuckDB writer (2026-05-21)
- "Clicking Enable does nothing" was three bugs: (1) **writer-lock root cause** — the dashboard's `get_store()` opened a DuckDB handle, and even a read-only handle takes a process-level lock that blocks the daemon's writer (stalling ingestion + blanking Models/Embodied/Cost/alerts); `get_store()` in a non-writer process now returns a proxy that forwards to the daemon HTTP query server and opens NO handle. (2) the cloud relay `alert_rule_upsert` body lacked owner_hash so rules were stored NULL and the cache_push filter dropped them — the daemon now stamps its own owner_hash. (3) the frontend "Enable" PUT a non-existent example id (404, swallowed) — it now POSTs a real rule from the template. Verified e2e: POST -> daemon upsert -> cache_push -> cloud Alerts tab shows the rule.

### Approvals actually fire + surface in the cloud inbox (2026-05-21)
- Fixed the recurring "protection rules toggled but never see a pending approval." Three stacked bugs: (1) the watcher matched policies by exact tool name, so OpenClaw-authored `exec` policies never matched the claude-cli `Bash` tool (now harness-agnostic via tool categories); (2) `process_tool_call` only POSTed to a legacy endpoint and never wrote the DuckDB `approvals` table that the heartbeat cache_push surfaces in the cloud inbox (now `ingest_approval` on match + `update_approval_decision` on resolve); (3) a dashboard process holding the DuckDB writer could stall ingestion so the watcher saw nothing (role-gate writer fix). Verified e2e: `rm -rf` -> watcher match -> DuckDB pending -> cache_push -> cloud inbox shows the decrypted pending approval.

### Cloud Pro: Agent Reliability score (P1, ClawBench-style) (2026-05-21)
- New `_build_reliability()` scores recent session traces on deterministic checks (tool_success, recovered, read_before_write, no_loop, acted) into a 0-100 Reliability Score + grade + failure taxonomy, shipped in the snapshot (no LLM, daemon's own store handle). clawmetry-cloud renders it as a score card on the Self-Evolve page. First slice of PRD-cloud-pro-agent-reliability.md.

### Writer-steal fix completed: role gate set before dashboard import (#1814, 2026-05-20)
- Follow-up to #1810. The `CLAWMETRY_ROLE=dashboard` gate was set just before `dashboard_main()`, but `from dashboard import main` runs earlier and dashboard.py has module-level/handler `get_store()` calls — so the dashboard could still race in and grab the DuckDB writer before the gate was active (Models/Embodied/Cost-history intermittently blanked). Setting the env before the import closes it. Verified live: daemon keeps the writer across restarts; Models, Embodied, and the Cost 14-day history all render correctly in cloud.

### Cloud parity: sub-agents, writer-lock stability, Cost history (2026-05-20)
- **Active Tasks / sub-agents (#1809).** The cloud Active Tasks panel showed "No active tasks" while sub-agents ran (`/api/subagents` read the cloud's empty filesystem). Sub-agents now flow jsonl -> DuckDB -> snapshot -> Redis -> cloud (read back via `query_subagents`); active sub-agents' transcripts ride the snapshot too so the click-through shows what each one is doing.
- **Stop the dashboard stealing the DuckDB writer (#1810).** Root cause of "Models/Embodied randomly go empty in cloud": the dashboard process grabbed the DuckDB *writer* lock, starving the sync daemon so every snapshot read returned empty. Only the daemon writes now — a `CLAWMETRY_ROLE=dashboard` gate + a daemon-registered guard + no longer deleting the local-query discovery file on exit (that gap was the steal window). Verified the daemon keeps the writer across repeated restarts.
- **Cost tab real per-day history (#1811).** The Cost tab rendered tokens as if everything happened today. DuckDB `query_aggregates` had the correct per-day history all along; the daemon now ships a 14-day `dailyUsage` rollup in the snapshot and clawmetry-cloud renders it.

### Cloud Self-Evolve: the daemon asks OpenClaw itself (2026-05-20)
- **Why.** The cloud Self-Evolve tab dead-ended on "Self-Evolve needs an Anthropic credential" — the cloud server has no model credential, and ClawMetry's gateway token is read-only (`operator.read`), so neither the cloud nor a ClawMetry gateway connection can run the review.
- **What.** The daemon now delegates the review to **OpenClaw itself**: `openclaw agent --session-id clawmetry-selfevolve --json` runs a real, isolated agent turn on OpenClaw's OWN credentials, and the structured findings are parsed and shipped in the encrypted system snapshot (`selfEvolve`). The session transcript also lands on disk -> DuckDB, so it flows local -> Redis -> cloud while ClawMetry stays read-only on the gateway (it only invokes OpenClaw's own owner-access CLI). Refresh is gated (6h) + backgrounded; context is built on the daemon's own store handle in the snapshot thread (a read-only re-open / worker-thread query deadlocks the writer); cold start falls back to the on-disk cache so the cloud renders instantly. clawmetry-cloud intercepts `/api/selfevolve/{status,latest,analyze}` and renders `snap.selfEvolve`.
- **Verified.** Live against app.clawmetry.com: the node's encrypted snapshot decrypts to `selfEvolve.status.available=true` + findings; a fresh `openclaw agent` run produced well-formed JSON findings (loop/model/cost/reliability) parsed cleanly. Carries PR #1806.

### Cloud Embodied: per-session transcripts via snapshot (2026-05-20)
- The cloud Embodied tab showed "No messages in this transcript" because `/api/transcript/<id>` read the cloud's empty filesystem. The daemon now puts recent per-session transcripts (capped 80 messages, ~8 most-recent sessions) in the encrypted snapshot, built on its own store handle. clawmetry-cloud intercepts the fetch and renders them. Verified: cloud renders the same messages as local.

### Cloud parity: overview overlap, Logs removal, Models attribution (2026-05-20)
- **Overview overlap.** `.overview-split` was a fixed-height grid; a tall System Health panel overflowed it and collided with the "Is your agent alive?" heartbeat panel below. Now grows (`height:auto` + `min-height`) with a flow-pane `min-height` so it can't collapse.
- **Logs tab removed.** Added no value (cloud dead-end + local duplicate of the Flow/Brain live stream). Nav item, page, and the "tools" KPI redirect to Brain.
- **Models attribution → cloud.** The cloud Models tab was empty because `/api/model-attribution` needs per-turn data that only lives in local DuckDB. The daemon now puts `modelAttribution` (per-turn turns/sessions/switches) in the encrypted snapshot, computed on its own store handle (a read-only re-open deadlocks the daemon write lock). clawmetry-cloud renders it. Verified the cloud snapshot decrypts to the same numbers as local.

### Cloud Diagnostics: sync detected-config so the cloud panel isn't a dead-end (2026-05-20)
- **Why.** Paid cloud nodes saw "Diagnostics are local-only, open the dashboard on the host" because the detected-config data was never synced. The Security posture panel (which also inspects local config) already syncs and renders fine, proving config inspection can ride the encrypted snapshot.
- **What.** `sync_system_snapshot` now includes a `diagnostics` block (gateway URL/port, workspace path, auth-token presence only, never the token value, OpenClaw env flags, and `validate_configuration()` warnings) mirroring the OSS `/api/diagnostics` shape. clawmetry-cloud renders it client-side from the decrypted snapshot.
- **Verified.** Live against app.clawmetry.com: the node's encrypted `system_snapshot` decrypts with the node key and now carries the `diagnostics` block. Carries PR #1791.

### MOAT EOD refire: PyPI 0.12.249 carries PR #1730 + PR #1732 (issue #1746, 2026-05-19)
- **Why.** PRs #1723, #1730, #1732 all merged within 35s tonight. All three release-on-merge runs computed `NEW=0.12.248` from the same starting main, then each tried `twine upload --skip-existing`. PyPI accepted #1723's wheel first; the other two were silently skipped. Net result: PyPI 0.12.248 only carried #1723's alerts-modal centering fix, while main moved to v0.12.248 with the #1732 commit.
- **What this release does.** No code change beyond this CHANGELOG entry — exists purely to re-fire `release-on-merge.yml` so v0.12.249 picks up the missing #1730 (DuckDB daemon-proxy for service-status + flow/runs) and #1732 (gateway WS `client.id="openclaw-control-ui"` so crons/sessions/messages reads return scopes) commits that already landed in main.
- **Follow-up.** Issue #1746 tracks the underlying release workflow race; `release-on-merge.yml` needs a `concurrency` group so only one publish runs at a time, plus a hard-fail (not `--skip-existing`) on duplicate uploads.

### Gateway-tap opt-in nudge for users impacted by PR #1228 default-OFF flip (issue #1233, 2026-05-17)
- **Why.** PR #1228 flipped the live WS gateway tap (`clawmetry/gateway_tap.py`) from default-ON to default-OFF for the OpenClaw `operator.read` scope-grant transition. Users who previously relied on the tap for inbound channel-message bodies (Telegram, Signal, Discord, etc.) silently lost capture; the fix landed but no upgrade prompt told them how to re-enable.
- **Detection (DuckDB, cached 5m).** New `_compute_gateway_tap_comms()` in `routes/overview.py`: tap env unset + 1+ `channel_messages` rows in prior 7d + 0 rows in last 24h. Three predicates so we never nag fresh installs or users who already opted back in.
- **Banner.** `/api/overview` piggybacks `_comms.show_gateway_tap_banner` + `show_pro_cta`. Dashboard renders a dismissible amber strip explaining how to re-enable (`CLAWMETRY_ENABLE_WS_TAP=1`) and offering Pro defaults to non-Pro users. Sticky dismiss via `localStorage`.
- **Tests.** `tests/test_gateway_tap_opt_in_banner.py` covers banner-fires / no-prior-activity / recent-activity-suppresses / tap-already-enabled cases against an in-memory DuckDB.

### Alerts comms: PR #1410 ship moment for the no-OTLP cohort (issue #1419, 2026-05-16)
- **Changelog callout.** Alert rules now fire on real OpenClaw spend, not just OTLP-fed installs. The ~99% of users without the `[otel]` extra had `daily_spent=0` forever, so "alert when spend > $X" rules never triggered until PR #1410 wired the DuckDB events fallback into `_get_budget_status`.
- **Alerts tab banner.** When a user has 1+ rules, 0 historical fires, and the oldest rule is more than 24h old, `/api/alerts/rules` returns `_comms.show_alerts_comms_banner: true`. The Alerts tab renders a one-line notice that the previous rules should start triggering normally. Dismissible.
- **Cloud-Pro CTA.** Same cohort, plus `cost_source == "duckdb"` (no OTLP) plus not already on Pro, surfaces a "richer telemetry plus 90-day retention" upsell inline in the banner.
- **"Last fired" pill per rule.** Each rule card shows `Last fired: 5m ago` (green pill) when the rule has fired at least once, otherwise `Not yet fired` (muted pill). Converts the silent fix into a visible win the user can pin in muscle memory.

### MOAT batch: 7 user-visible Tier-1 bypasses → DuckDB fast-path (2026-05-15)
Single-day push that pulls seven dashboard surfaces off the JSONL/process-stat path and onto the daemon-proxy DuckDB read path. Each migration ships with a synthetic-event E2E test that proves the round-trip (LocalStore.ingest → DuckDB → endpoint returns the expected shape). All seven are paired with `_try_local_store_*` early-returns plus the legacy fallback verbatim — no behavior regression, just latency.

- **`/api/context-anatomy` Session-history bucket → DuckDB** (#1370). Replaces a 5×N JSONL scan with one indexed SQL aggregate; ~200-800ms → <5ms on busy workspaces. Drive-by: also accepts OpenClaw-native `usage.input` token shape so non-Anthropic-SDK nodes stop silent-zeroing.
- **`/api/spans` surfaces OTel spans we already persist** (#1372 — MOAT cap 1.b structured event capture). New Brain-tab `📐 Spans` toggle, lazy-loaded from the existing `spans` table. No new ingestion — pure exposure of what the OTLP receiver was already capturing.
- **`/api/loop-signals` exposes LoopDetector signals from clawmetry/proxy.py** (#1373 — MOAT cap 2.f loop/stall detection). New `loop_signals` DuckDB table with `(session_id, signature)` PK + upsert semantics; Brain-tab badge hidden until count > 0.
- **Brain tab UX clean-up** (#1375). `Show plumbing` toggle (default off) hides QUEUE-OPERATION rows; provenance JSON blocks (`Conversation info (untrusted metadata): {...}`) collapse to inline channel pills (`📱 Telegram · Vivek Chand · 22:15  ⓘ`) with click-to-expand JSON. ~8 rows/Telegram-message → 2-3 rows.
- **`/api/skills` fidelity counts → DuckDB** (#1378). Replaces a 7d × N-session JSONL scan with one SQL aggregate over `events`. New `query_recent_read_tool_calls()` handles all three on-the-wire shapes (v3 `tool.call`, trajectory `toolMetas`, legacy `data.message.content`).
- **`/api/fallbacks` model-transition aggregator → DuckDB** (#1380). Replaces opening up to 100 transcript files per request with one CTE+walk over `events`; multi-second → ms.

### Login flow hardening (issue #1356, 2026-05-15)
- **`pgrep -f "openclaw-gatewa"` typo fix** (#1357). Four callsites in `dashboard.py` had the trailing `y` truncated, so process-env auto-detection silently returned no token; on systems without `OPENCLAW_GATEWAY_TOKEN` env var or matching config-file fallback, `GATEWAY_TOKEN` stayed `None` and `/api/auth/check` rejected every input. +4 bytes.
- **`/api/auth/detected-token` localhost-only bootstrap endpoint** (#1359 PR-B). Returns the on-disk gateway token to a loopback caller so the dashboard JS can self-bootstrap without a 48-char manual paste. Hardened with four stacked defenses: raw WSGI `REMOTE_ADDR` (not Flask attribute, defends against future ProxyFix wrap), Host-header allowlist (DNS rebinding), reject any `Forwarded`/`X-Forwarded-*`/`X-Real-IP` (proxy markers), refuse to register when bound to non-loopback host (`--host 0.0.0.0`). 27 unit tests.
- **Zero-click bootstrap JS** (#1358 PR-C). `auth-bootstrap.js` checks `localStorage` first; if empty, fetches `/api/auth/detected-token`, stores the result, and re-enters `checkAuth()` inline (no `location.reload()` — that broke Playwright E2E with "Execution context was destroyed", fixed in followup #1363).
- **CLI startup banner prints one-click `/auth?token=` URL** (#1360 PR-D). When `GATEWAY_TOKEN` is detected at startup, prints `-> http://localhost:8900/auth?token=<TOKEN>  (one-click sign-in)` next to the dashboard URL. `--host 0.0.0.0` is reframed as `localhost` so the link only works from the local machine.
- **Playwright E2E coverage for the zero-click flow** (#1361 PR-E).
- **Hotfix: drop `location.reload()` from PR-C** (#1363). The bootstrap-IIFE-reload anti-pattern caught the entire E2E suite ERRORing at setup; re-entering `checkAuth(token)` inline keeps the token in `localStorage` for the fetch shim without pulling the navigation context out from under the fixture. P0 issue #1368 filed for a fast lint guard.

### Browser-level regression sweep (2026-05-12 evening)
- **getattr guards for 3 endpoints returning 500** (#1077). `_estimate_usd_per_token` (routes/sessions.py: `/api/delegation-tree`), `AgentReliabilityScorer` (routes/health.py: `/api/reliability`), `_build_clusters` (routes/meta.py: `/api/clusters`). All three returned `AttributeError` 500s when the underlying helper hadn't shipped; now degrade to `{...empty data, _missing: true}` so the dashboard renders cleanly. Caught by a real-browser audit that scraped DevTools console for cloud users; complements PR clawmetry-cloud#750 which suppresses harmless 410/404 calls.

### DuckDB-everywhere + heartbeat-piggyback transport (epic #1032 phase 1–5, partial #964 close-out)
- **`/api/transcript/<sid>` reads from local DuckDB** (#1056) under `CLAWMETRY_LOCAL_STORE_READ=1`. Closes the explicit local-first blocker surfaced by the real-OpenClaw E2E pipeline.
- **`/api/memory-files`, `/api/file`, `/api/memory`, `/api/memory-analytics` read from local DuckDB** (#1059) via new `LocalStore.query_memory_blobs()`. POST `/api/file` writes still on the filesystem — read-only by default.
- **Tier-1 fast paths**: `/api/component/tool/<name>`, `/api/component/brain`, `/api/autonomy`, `/api/advisor/{ask,status}`, `/api/reasoning` (#1057). The 5 OS-state component endpoints (runtime/machine/storage/network/gateway) intentionally stay off the event store.
- **Daemon dispatches heartbeat-piggybacked queries** (#1054, #1055). Replaces the killed WS relay path. Cloud responds to `/ingest/heartbeat` with `pending_queries`; daemon dispatches via `routes/local_query._dispatch()`, encrypts, POSTs to `/ingest/cache`. Industry-validated by Datadog Remote Config / AWS SSM Run Command / OpenTelemetry OpAMP-HTTP.
- **Phase 2 — brain cache_push on heartbeat** (#1061). Top-50 brain events ride along with every `/ingest/heartbeat` body under `brain:{owner_hash}:{node}:recent` (3600s TTL). Cloud Brain tab paints in <100ms with zero Cloud SQL hits on the happy path.
- **Phase 3 — alert rules in DuckDB + cache_push** (#1062). New `alert_rules` table (SCHEMA_VERSION 2 → 3), CRUD via `LocalStore`, fast path on `/api/alerts/rules`, plus a single `alerts:{owner_hash}:rules` cache entry per heartbeat. Cloud reads encrypted blob, browser decrypts.
- **Phase 4 — approvals queue in DuckDB + decision-via-pending_queries** (#1064). New `approvals` table, fast path on `/api/approvals*`, pending queue pushed to `approvals:{owner_hash}:queue` on heartbeat. Cloud decisions queued back via `pending_queries` actions — no inbound network on the OSS side.
- **Phase 5 — channel adapter config in DuckDB** (#1063). New `channel_config` table holds E2E-encrypted blobs (Telegram bot tokens, Slack OAuth, etc.) — cloud never sees plaintext. Adapter status summary pushed to `channels:{owner_hash}:status` every heartbeat.
- **Real OpenClaw binary E2E coverage** (#1058). 8 tests spawn `openclaw agent --local --message ... --json` against a hermetic `OPENCLAW_HOME` and round-trip the produced JSONL through the real daemon → DuckDB → `/api/local/events` + `/api/sessions`. Skips cleanly on CI without the binary.
- **Coverage**: 32/32 `_try_local_store_*`-gated endpoints have full seed→hit→`_source`-assert tests.

### JS response-shape tolerance (forward-compat, #1071)
- `app.js` now ships `unwrapList` / `unwrapListAsync` helpers that
  accept all three Phase 2–5 envelopes (legacy array, local-store
  `{key:[...], _source:"local_store"}`, cloud cache `{key_blob:"...",
  _source:"cache"}`). On `_source:"cache"` the helper reaches for the
  cloud-injected `decryptBlob` to decode ciphertext in-browser; if the
  decryptor isn't loaded yet we degrade to an empty list silently —
  never throws, never blocks the dashboard from painting. Applied to
  `loadAlertRules` + the three `/api/brain-history` consumers.
- Pre-publish `tests/e2e/cloud-contract.mjs` per-tab JS-error check
  now goes through the same `isHarmlessConsoleError()` filter as the
  global rollup. Stops `/api/diagnostics` 410 + `/api/config-diagnostics`
  404 from false-failing every tab. Flow node-click test now degrades
  to a SKIP on empty-activity instead of hard-asserting modal-open.

### Local store: multi-agent foundation + naming (epic #964)
- **Local DB renamed** `events.duckdb` → `clawmetry.duckdb`. The DB now
  holds events, sessions, memory blobs, heartbeats, system snapshots
  (and soon spans for tracing) — `events.duckdb` was outgrowing its name.
  **Auto-migrates** an existing `events.duckdb` (and its `.wal` sibling)
  on next start. Lossless, no schema change. Skipped if you've set
  `CLAWMETRY_LOCAL_STORE_PATH` to a custom location.
- **Multi-agent schema** (SCHEMA_VERSION 1 → 2). New tables: `sessions`,
  `memory_blobs`, `heartbeats`, `system_snapshots`, `crons`, `subagents`,
  `openclaw_channels`. `agent_type` discriminator added to `events` and
  `daily_aggregates` so OpenClaw / Claude Code / Hermes / Cursor / Codex /
  Aider all coexist in one store. v1 stores auto-upgraded with `ALTER
  TABLE ADD COLUMN agent_type DEFAULT 'openclaw'` — legacy rows preserved.
- **Daemon write-through for sessions / memory / heartbeats**. Each cloud
  sync (`/ingest/sessions`, `/ingest/memory`, `/ingest/heartbeat`) now also
  persists locally before shipping to cloud. Best-effort; local failures
  never block cloud sync.
- **Dashboard reads sessions from local DB** under
  `CLAWMETRY_LOCAL_STORE_READ=1` (opt-in, falls through to gateway/JSONL
  when unset OR store is empty).

### Cloud cold-data relay (epic #964 phases 3b + 4)
- **WebSocket relay client** (`clawmetry/relay.py`) — long-lived WS to
  `wss://app.clawmetry.com/api/node/relay`. Listens for `{type:"query"}`
  frames from the cloud, dispatches via the same `relay_dispatch()` the
  local HTTP API uses, returns chunked responses. Reconnect with
  exponential backoff (2s → 60s cap). Cloud dashboard can now ask the
  user's machine for data older than the 24h hot window without us paying
  for permanent cloud storage.
- **`websocket-client` is now a base install dep** (was previously
  `extras_require["relay"]`). The opt-in caused cloud users to silently
  miss the relay. `pip install clawmetry && clawmetry connect` "just works"
  again. The `[relay]` extra is kept as a no-op for backwards compat with
  old install scripts.
- Cloud-side broker shipped in `clawmetry-cloud#705` + `#711` + `#712`
  (gunicorn + gevent-websocket migration so flask-sock can do WS upgrades
  in production).

### Heartbeat
- **`local_store_size_mb`** + `local_store` health block on every
  heartbeat. Cloud-side rollout playbook will gate phase 2 (cloud
  retention slim) on ≥80% of nodes reporting healthy local stores.

### Brain history
- **Opt-in fast path** under `CLAWMETRY_LOCAL_STORE_READ=1` —
  `/api/brain-history` returns directly from the local DuckDB (tagged
  `_source: "local_store"`) instead of re-parsing JSONL. Falls through to
  the legacy parser when the env var is unset OR the store is empty.

### Tests
- 70+ new tests covering: relay dispatch, chunking, error frames,
  capability drift, brain fast-path, sessions fast-path, schema
  migration v1→v2, ingest_session/memory_blob/heartbeat helpers, daemon
  write-through, the events.duckdb→clawmetry.duckdb rename + WAL move,
  env-override skip, no-clobber when both files exist.

### Local-first foundation (epic #964 phase 1) — first shipped in 0.12.164
- **Local DuckDB event store** at `~/.clawmetry/events.duckdb` — durable record of every telemetry event the daemon parses. Switched from SQLite to DuckDB (decision in clawmetry-cloud meta-PRD): columnar storage makes the dashboard's GROUP BY / time-window analytics 10–100× faster, and unlocks future Parquet export. Adds `duckdb>=0.10` as a dependency.
- **Daemon writes through to local store** at parse time — local is now the source of truth, cloud is a hot cache. Failures in the local path never block cloud sync.
- **Two new diagnostic endpoints** — `/api/local-store/health` and `/api/local-store/events` for verification + test harnesses
- 27 passing tests cover ingest validation, idempotency, batch flush, query filters, restart persistence, ring overflow, and the full sync→store wire-through
- Note: 0.12.164's SQLite `events.db` file is left in place but no longer read; safe to delete after upgrade.

---

## v0.12.120

### Improved
- **Uninstall purges server-side registration** — `clawmetry uninstall` now calls `/api/unregister` to delete the node_registry entry, preventing stale account re-linking on reinstall (#741)

---

## v0.12.119

### Improved
- **E2E secret key shown during install** — `curl | bash` now displays the encryption key so users can paste it when opening the dashboard (#738)

## v0.12.118

### Agent Observability Suite
- **Real-time event streamer** — Dropbox-style file-size diffing pushes brain events instantly instead of 15s polling (#718)
- **Channel session badges** — Telegram/WhatsApp/Discord/Slack/IRC/iMessage badges in Brain tab with filter chips (#725)
- **Channel metadata sync** — session_key, channel, chat_type synced to cloud for multi-channel visibility (#726)
- **Skill badges + file browser** — skill usage badges on brain events + IDE-like skill file browser (#728)
- **Flow tab architecture upgrade** — provider stack with fallback slots, skills column, Brain→Skills path (#729)
- **LLM Context Inspector** — token breakdown bars, system prompt viewer, compaction history (#730)
- **Agent Runtime Timeline** — per-turn drill-down with tool/LLM/user phase bars (#731)
- **ACP sub-agent visibility** — nested sub-agent events in runtime timeline (#732)
- **E2E key from URL fragment** — encryption key passed via `#hash`, never touches the server (#734)

### Fixed
- Heartbeat interval NaN when `interval_seconds` is missing (#717)

### Docs
- Comprehensive agent observability guide with architecture diagrams (OBSERVABILITY.md) (#733)

### Added (prior unreleased)
- **Cloud autonomy trending** (pairs with clawmetry-cloud#360). The sync daemon now computes a daily autonomy aggregate (median nudge gap, autonomy ratio, 7-day trend slope) locally from session transcripts and pushes only the aggregate — not raw content — to `ingest.clawmetry.com/ingest/autonomy`. Raw memory stays E2E-encrypted; cloud displays the trend on `app.clawmetry.com/fleet`. Throttled to one push per UTC day. Respects `cloud_autonomy_sync: false` opt-out.

### Fixed
- **Skills tab sort order** — dead skills were sorting to the *bottom* of the list instead of the top (`order['dead']` is 0, and `0 || 9` evaluates to 9, so "dead" slipped to the end). Uses `in` membership check now so "Safe to remove" rows surface where they should.

### Fixed
- **`pip install clawmetry` now actually works end-to-end.** Since the routes/ helpers/ templates/ extractions (0.12.90-series), the published wheels silently omitted the non-Python asset directories — installed users' dashboards 404'd on `/static/js/app.js` and failed at import because `from routes.sessions import bp_sessions` had no target. `static/` and `templates/` now ship under the `clawmetry/` package; `routes/` and `helpers/` are declared top-level packages. A new `wheel-install` CI job verifies every release by installing the wheel in a fresh venv and requesting `/static/js/app.js`.
- **Structural move**: `static/*` → `clawmetry/static/*`, `templates/*` → `clawmetry/templates/*`. `app = Flask(...)` now passes `static_folder` / `template_folder` pointed at the package-relative paths. URL surface (`/static/...`) unchanged; users see no behavioural difference.
- **Boot overlay no longer hangs forever on slow setups.** `waitress threads=8` → `32`, and `bootDashboard()` races an 8s hard timeout so the overlay always dismisses even when one bootstrap endpoint stalls.
- **Subagent modal now shows logs for GC'd / failed spawns.** Reconstructs child output from the parent session's `Internal task completion event` messages; splits into **Overview** + **Brain Events** tabs; skips auto-refresh for immutable entries; Active Tasks panel tightened from 24h window to 10 minutes.
- **Subprocess + WebSocket hang-proofing**: `df`, `free`, `uptime`, `pgrep` get `timeout=2`; `_gw_ws_rpc` uses `ws.settimeout(5)` so a stalled gateway can't pin the request thread.
- **`/api/subagents` cache-mutation bug** — the endpoint was mutating the shared `_sessions_cache["data"]` list, causing duplicate entries to accumulate on every call. Now copies before mutating.

### Added
- **Service status indicators** — fleet node cards now display color-coded status dots for Gateway, Channels, Sync, and Resources (closes #254)
- New `/api/service-status` endpoint returns compact `{gateway, channels, sync, resources}` dict suitable for sync-daemon heartbeat payloads
- `/api/system-health` now includes `service_status` field in the same format, enabling local-node fleet self-registration

### How it works
- Sync daemons include `service_status` in their `POST /api/nodes/<id>/metrics` push
- Fleet overview renders a mini status bar under each node card: 🟢 GW · 🟢 telegram · 🟢 sync · 🟡 res
- Color legend: green = healthy, yellow = degraded, red = down, gray = unknown

---

## v0.12.63 (2026-03-22)
- fix: robust Ollama detection -- PATH fallback + HTTP ping to localhost:11434
- feat: sync daemon heartbeat includes ollama status (installed, running, models)

## [0.12.71] — 2026-03-22

### Fixed
- Security posture scan timeout — JS client timeout increased 8s → 25s, gateway API timeout 5s → 8s (fixes "Posture scan failed: timeout" error)

### Added
- Screenshots of all OSS dashboard tabs in README (Brain, Overview, Flow, Tokens, Memory, Security)

## [0.12.69] — 2026-03-22

### Fixed
- Updated logo to new lobster SVG, embedded as base64 data URI (works offline)
- Brain stream now shows full content — removed single-line ellipsis truncation, wraps by default

## [0.12.68] — 2026-03-22

### Fixed
- Remove duplicate type filter pills in Brain tab — type chips now use a dedicated container with `innerHTML =` instead of `+=`
- Remove non-working Graph view toggle from Brain tab — live list feed is now the default with no toggle

## [0.12.66] — 2026-03-22

### Removed
- Agents, Context, and Channels tabs from OSS dashboard (simplifies to 7 core tabs)
- Backend routes: `/api/subagents`, `/api/context-inspector`, `/api/channel-metrics`

### Fixed
- CI: removed stale tests for deleted routes

## [0.12.65] — 2026-03-22

### Fixed
- Remove stale tests for deleted API routes (`/api/channel-metrics`, `/api/subagents`, `/api/context-inspector`)

## [0.12.64] — 2026-03-22

### Removed
- **Agents tab** — removed sub-agent gantt/timeline view (confusing, stale sessions with no active/idle filter)
- **Context tab** — removed workspace context inspector (not actionable for most users)
- **Channels tab** — removed per-channel OTLP metrics tab (requires OTLP setup, shows empty state for most)
- Corresponding backend API routes: `/api/subagents`, `/api/subagent/<id>/activity`, `/api/context-inspector`, `/api/channel-metrics`
- OTLP queue lane depth metrics storage (channels-only feature)

Simplifies OSS dashboard to 7 core tabs: **Flow, Brain, Overview, Crons, Tokens, Memory, Security**

## [0.12.61] — 2026-03-20

### Added
- **Cron management UI**: full CRUD for cron jobs from the dashboard (GH #253)
  - Run Now button with confirmation dialog for on-demand job execution
  - Enable/Disable toggle per job with instant UI feedback
  - Edit and Delete buttons now active (previously disabled pending gateway testing)
  - New Job button to create cron jobs from the dashboard
  - Auto-refresh every 30s with checkbox toggle to pause it
  - Human-readable schedule descriptions alongside cron expressions (e.g., `*/30 * * * *` shows "every 30 minutes")
  - Multi-node cron status panel: shows online/offline status and cron summary for each registered fleet node
  - Execution history with heatmap calendar (click any job to expand)

## [0.12.60] — 2026-03-19

### Added
- **Channels tab**: per-channel observability with webhook error rates, message duration p50/p99, queue depth, and cost attribution grouped by channel
- OTLP status indicator in `clawmetry status` CLI command with restart hint
- New `/api/channel-metrics` endpoint for per-channel OTLP metrics

## [0.12.59] — 2026-03-19

### Fixed
- Add `/api/memory` and `/api/flow` route aliases for E2E health checks
- Recent-first sync strategy for Brain feed

## [0.12.57] — 2026-03-17

### Added
- Click-to-expand brain stream events (click any row to see full detail text)
- Hover highlight on brain event rows

## [0.12.56] — 2026-03-17

### Fixed
- Initial sync no longer hangs on large session directories (batch size 10 → 200, 5K event cap per cycle, newest-first, incremental state saving)

## [0.12.55] — 2026-03-17

### Fixed
- Store raw passphrase in config instead of derived hash (show what the user typed, not gibberish)

## [0.12.54] — 2026-03-17

### Fixed
- Support arbitrary passphrases as encryption keys (auto-derives 256-bit AES key via SHA-256)
- Existing configs with raw passphrases self-heal on next sync

## [0.12.53] — 2026-03-17

### Fixed
- NameError crash on encryption key prompt (`_input` not defined in `_cmd_connect`)

## [0.12.52] — 2026-03-17

### Improved
- Always show encryption key prompt during onboard and connect (full transparency)
- Existing key shown masked with option to keep or replace

## [0.12.51] — 2026-03-17

### Added
- Prompt for custom encryption key during `clawmetry connect` (press Enter to auto-generate)

---

## [0.12.45] — 2026-03-15

### Fixed
- `clawmetry connect --key` no longer crashes in non-interactive shells (SSH, CI/CD, Docker)
- Sync daemon retries on 401/503 (cloud cold-start resilience)

---

## [0.12.44] — 2026-03-15

### Fixed
- Sync daemon `_post()` retries once on 401/503 responses (cloud cold-start resilience)
- Prevents sync daemon from permanently skipping sessions when Cloud Run returns transient auth errors

---

## [0.12.43] — 2026-03-15

### Fixed
- `sync_crons` now sends full schedule object, state (lastRunAtMs, lastDurationMs, nextRunAtMs, lastError, consecutiveFailures), and task description to cloud
- Maps `consecutiveErrors` field (OpenClaw's actual field name) to `consecutiveFailures` for renderer compatibility

---

## [0.10.11] — 2026-02-28

### Fixed
- Dark mode now correctly forced on load — initTheme() was overriding body dark mode with localStorage light default

---

## [0.10.10] — 2026-02-28

### Changed
- Dark mode always on, remove theme toggle (merged via PR #37)

---

## [0.10.9] — 2026-02-28

### Changed
- Dark mode is now the permanent default — removed theme toggle button

---

## [0.10.8] — 2026-02-28

### Fixed
- Auth check runs before boot sequence — login overlay shows immediately if token invalid/missing
- Boot overlay no longer covers the login prompt on stale token
- Overview request storm on boot: removed duplicate loadAll() call, added in-flight guard

---

## [0.10.7] — 2026-02-28

### Fixed
- Port conflict check moved to daemon mode only — foreground mode was false-positive blocking all ports

---

## [0.10.6] — 2026-02-28

### Fixed
- Port conflict: only kill our own stale clawmetry process, not arbitrary apps on the same port
- Clear error message if another app is already using the port

---

## [0.10.5] — 2026-02-28

### Fixed
- Installer now auto-starts daemon immediately after install via full binary path (works with curl|bash)

---

## [0.10.4] — 2026-02-28

### Fixed
- Hide `clawmetry connect` command from help (cloud integration not yet production ready)

---

## [0.10.3] — 2026-02-28

### Fixed
- Architecture diagram boxes broken due to emoji double-width characters — switched to pure ASCII +---+ style

---

# Changelog

## [0.12.99] — 2026-03-31

### Fixed
- **NemoClaw install**: `docker exec -i` flag so heredoc stdin reaches sandbox — supervisord now installs correctly via `curl|bash` (#459)
- **NemoClaw install**: Detect real OpenClaw data dir inside sandbox at install time (#458)
- **Channel messages**: Populate channel message counts when per-message metadata is empty — reads channel from sessions.json deliveryContext (#461)
- **Channel messages**: Track both inbound (user) and outbound (assistant) messages


## [0.11.0] - 2026-03-01

### Added
- Brain tab: unified real-time activity stream for main agent + all sub-agents
- Brain tab: filter pills with glow highlight, chart filtering by agent
- Brain tab: `/api/brain-history` + `/api/brain-stream` endpoints
- Brain tab: spinner feedback on pill click
- Nav reorder: Flow | Overview | Brain | Crons | Tokens | Memory

### Fixed
- Windows CI: UTF-8 encoding, stdout handling
- E2E tests: auth token injection per-page, boot overlay dismissal
- Sub-Agents tab removed from nav


All notable changes to ClawMetry are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [0.10.1] — 2026-02-28

### Fixed
- Hide OTLP "not available" error from startup banner — only shows when otel is actually installed

---

## [0.10.0] — 2026-02-28

### Added
- **18 channel live popups** — all OpenClaw channels now show live message bubbles in Flow:
  iMessage (chat.db), WhatsApp, Signal, Discord, Slack, Webchat, IRC, BlueBubbles,
  Google Chat, MS Teams, Mattermost, Matrix, LINE, Nostr, Twitch, Feishu, Zalo
- **Cost Optimizer** — llmfit integration detects local models runnable on your hardware;
  Apple Metal speed correction; task-level savings recommendations; ollama pull commands
- **Full test suite** — pytest API tests, Playwright E2E, BrowserStack cross-browser tests
- **CI matrix** — Linux/macOS/Windows on every PR via GitHub Actions
- **BrowserStack CI** — Chrome, Firefox, Safari, Edge on merge to main
- **Auto-publish workflow** — `git tag vX.Y.Z && git push --tags` publishes to PyPI
- **Makefile** — `make dev`, `make test-fast`, `make test`, `make lint`
- `CHANGELOG.md` — this file

### Fixed
- Gateway token not found on restart (`openclaw.json` missing from config search path)
- New channels (iMessage etc.) missing from `KNOWN_CHANNELS` list
- Overview page channel nodes not rendering (getElementById on unappended DOM clone)
- Unconfigured channels (Signal/WhatsApp) showing in Flow when not in config
- `grep`/`tail`/`pgrep` subprocess calls replaced with pure Python (Windows compatibility)
- `/tmp/openclaw` hardcoded log paths replaced with `_get_log_dirs()` cross-platform helper
- Windows UTF-8 crash — 🦞 emoji in BANNER failed on cp1252 encoding
- `setup.py` reading `dashboard.py` without `encoding="utf-8"` (Windows pip install failure)

### Changed
- Channel nodes in Flow now hide automatically if not configured in `openclaw.json`
- Only channels actually set up appear in Flow/Overview visualizations

---

## [0.9.17] — 2026-02-23

- Gateway auth theme fix
- Context inspector spec branch
- Various stability improvements

---

## [0.9.x] — 2026-02-13 to 2026-02-23

- Initial public release
- Flow visualization, Overview, Sessions, Crons, Usage, Logs, Memory, Transcripts tabs
- Telegram channel support
- Sub-agent tracking
- Cost tracking and budget alerts
- OTLP receiver (experimental)

## [0.10.2] — 2026-02-28

### Added
- Full CLI with subcommands: `clawmetry start/stop/restart/status/connect/uninstall`
- Daemon support: launchd (macOS) + systemd (Linux) — auto-starts on login
- Architecture overview on startup matching clawmetry.com/how-it-works
- `clawmetry --help` and `clawmetry help` 
# v0.12.77

## v0.12.87 (2026-03-30)
- `clawmetry status` now shows all NemoClaw sandbox nodes with connection status
- `clawmetry status --show-key` reveals enc key per sandbox
- New `--key-only` flag: OTP on host without starting daemon (host has no OpenClaw)
- New `--enc-key` flag: non-interactive connect for sandboxes
- Only sandboxes appear in app.clawmetry.com, not the host
- Clean end message after NemoClaw install

## v0.12.244 (re-cut: workflow ate the previous bump)
- Re-trigger PyPI publish so cloud auto-pin picks up the v0.12.243 sync.py drift fix at v0.12.244

## v0.12.245
- fix(sync): daemon uploads per-session event_count + size_bytes (#1697) — Embodied tab now shows real counts on cloud
- feat(replay): Replay tab queries DuckDB instead of optional SQLite collector (#1698) — chart populates out of the box
- fix(nav): rename 'Rules' to 'Alerts' to match page content (#1696)

## v0.12.246
- feat(ia): nav regroup — Flow/Brain/Logs/Models/LLM Context under Live; Crons + Memory promoted top-level (#1702)
- fix(cloud-nav): Version impact hidden in cloud mode (#1700)
- fix(advisor): Self-Evolve auto-detects Anthropic key from OpenClaw config; no more blocking takeover panel (#1703)
- fix(skills): Skills tab now discovers ~/.openclaw/plugin-skills/ (was returning 0 even with installed skills) (#1703)

## v0.12.247
- feat(classifier): cognitive_loop 6th outcome class. Catches recursive self-validation, the Wolfgang's burnout case) (#1709)
- feat(brain): forward-progress signal (tokens per state delta) + Pro alert + DuckDB query (#1710)
- fix(ci): auto-deploy-cloud workflow now watches CHANGELOG.md so [RELEASE] PRs auto-fire cloud pin
