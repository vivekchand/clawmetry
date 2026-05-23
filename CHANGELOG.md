## [Unreleased]

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
