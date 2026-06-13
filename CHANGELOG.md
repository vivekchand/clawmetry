## [Unreleased]

### Per-session loops slice so the Command River whirlpool binds the exact looping agent (2026-06-13)
- **Why:** the cloud Brain "Command River" draws a red whirlpool plus a Kill/Pause alarm on the looping lane, but the only loop signal it had was `deviceSummary.alert`, whose heartbeat path strips the session_id. So the whirlpool could only bind when the alert text happened to name a session in view; there was no precise per-agent loop signal to bind the alarm to the exact sub-agent.
- **What:** the daemon snapshot now carries a top-level `loops` array. Each entry is one currently-active loop or stuck incident the detectors already flagged, carrying the canonical `session_id` the river keys lanes on, plus `kind` (stuck_loop / no_progress / repeated_tool_failure / action_discrepancy), a plain-words `title`, `count`, `first_bad_step_ts`, `since`, `severity`, and `runtime`. It is sourced for free from the loop_signals rows the existing detector pass writes (one indexed 30-minute read, no recompute, CPU-cheap) and is self-clearing: a session that stops looping ages out of the window and drops from the slice. Only rows a detector genuinely wrote appear, never synthesized; titles stay to the detector's plain-words summary (the same exposure as the already-shipped device alert), so detail stays in the per-session encrypted brain feed.
- **Verified:** a new guard seeds a looping session and asserts `loops[]` carries its session_id, kind, and count; that a non-looping session is absent; that an aged-out loop self-clears; that a row without a session_id is never emitted; and that the slice is bounded and deduped per session. Revert-proven (stub the builder to return an empty list, the guard goes red).

### Runtime pixel logos on the local dashboard (#3097) (2026-06-13)
- **Why:** the hosted dashboard already shows the founder-approved Chunky Mascots pixel-art logo per runtime, but a self-hosted (OSS) user saw only emoji glyphs. The local dashboard should feel like the same product.
- **What:** vendors the canonical logo set under `clawmetry/static/runtime-logos/` (sprite atlas of one symbol per runtime plus a neutral fallback, brand manifest, and the 12 standalone svgs) so it ships in the wheel. A new `clawmetry/static/js/runtime-logos.js` exposes `window.cmRuntimeIcon(id, size, opts)` (unknown id falls back to the generic mascot and never throws) plus `cmRuntimeBrand`, fetching and inlining the atlas once. The runtime switcher chips, the global runtime chip menu, the session list rows, and the Brain source chips now render the mascot, keyed strictly off the runtime id from `GET /api/runtimes` so the set grows automatically as paid runtimes are added. The Brain List/Flow Command River is cloud-only and is not affected.
- **Verified:** the local dashboard serves the sprite, manifest, and helper; a headless render of all three wired surfaces paints each runtime's mascot and falls back to the generic glyph for an unknown runtime. Guard tests assert the shipped sprite carries a symbol for every runtime in the entitlements catalog plus the fallback (revert-proven), and that `cmRuntimeIcon` resolves a known id and falls back for an unknown one.

### Auto-update now installs the newest aged-in release instead of the absolute latest (#3093) (2026-06-13)
- **Why:** the daemon auto-update gated the unattended install on the absolute latest version's age against a 48h stability window. During an active release run (many publishes less than 48h apart) the latest is always too fresh, so the daemon held every check and never updated, leaving nodes stuck on an old build. This matched the fleet audit where almost no active node was current and every shipped fix reached nobody.
- **What:** the auto-updater now selects the newest version above the current build that has aged past the stability window and installs that specific version (pinned), so the fleet tracks latest-minus-window and keeps moving forward during active development. The update banner still advertises the absolute latest; only the silent install targets the aged release. The window stays 48h, overridable via `CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS`.
- **Verified:** new selection tests (newest aged-in chosen over a too-fresh latest; none when all too fresh; lower window installs more), revert-proven, 26 tests green on Python 3.9.

### Efficiency grade + savings hint on the desk device summary (#3073) (2026-06-12)
- **Why:** the efficiency grade shipped to the web (0.12.515) but the desk device glance had no way to show it; the device is exactly the surface where one letter + one dollar figure beats a dashboard.
- **What:** deviceSummary.efficiency = {grade, save_monthly_usd}, computed once per snapshot cycle and shared with the top-level efficiency slice (CPU budget), omitted entirely when data is thin so the firmware never renders a fake grade.
- **Verified:** 37 tests green incl. new present/omitted/garbage-coercion cases; also fixed the stale schema==1 assertion (deviceSummary is schema 2).

### Design-critique quick wins: honest empty states + plain words across Overview, Cost, Skills (#3070) (2026-06-12)
- **Why:** a 26-screen design-critique workflow flagged visible trust-breakers on the trial path: a red jargon banner ("no OTLP data for 5601 minutes"), token-first cost cards with an approx sign, an empty 14-day chart under populated totals, a permanently-dashed stat band, a green "ALL GOOD" verdict above a never-used skill, and a Fleet pointer shown to single-machine users.
- **What:** banner copy humanized ("One of our data feeds from your agent stopped about 4 days ago...") and suppressed while the live feed is active (2-minute window); Cost cards lead with dollars ("about $55.42") and demote tokens; the 14-day chart section hides until it has data; Session quality gets a plain title, an honest empty state, and a gear for the rubric; Burn/Proj/OK-ratio cells hide when null and SPENDING becomes "Cost today"; the Skills verdict is computed from the rows; the local-only strip drops the Fleet link unless more than one node exists. 19 new i18n keys.
- **Verified:** screenshots of Overview/Cost/Skills on a live dashboard confirm each change; banner suppression probe-verified both ways; node --check + en.json parse green; the branch also fixes main's pre-existing missing-i18n-key test failure.

### A-F efficiency grade + measured savings ideas on Overview and Cost (#3066) (2026-06-12)
- **Why:** ClawMetry showed what agents spend but never whether that spend was reasonable, and the existing cost-optimizer suggestions carried hardcoded "~$2-5/month" strings instead of measured numbers. A deep-dive into tokencost's health-grade idea showed a single letter grade plus a ranked, dollar-quantified action plan is the most newcomer-legible cost signal; adapted here to ClawMetry's read-only, snapshot-driven, per-runtime-honest architecture (full design spec from a 26-screen design-critique workflow, with two adversarial copy verification passes).
- **What:** new `clawmetry/efficiency.py` computes, per node and per runtime, three metrics (reuse rate, cache-write payoff, average context), a 0-100 score with an A-F grade (honest null under 10 calls), and ranked savings actions (smaller-model for short tasks, trim long conversations, stop re-read waste) with dollars measured from `rollup_model_daily` aggregates priced via `providers_pricing` and capped at 90% of projected monthly spend. Ships as `GET /api/efficiency` (server-side `?runtime=` scoping), an `efficiency` snapshot slice with `byRuntime` for cloud/device parity, an Overview hero chip ("Efficiency B, save about $29/mo", trust-gated, never a placeholder) and a Cost-tab "Savings ideas" card in plain words with honest collecting/paused/stale-daemon states.
- **Verified:** 31 unit/endpoint tests (savings recomputed in-test from pricing rates to the cent; per-runtime scoping; never-raise on garbage rows) plus a real-DuckDB integration smoke; UI verified rendering live in all states on a worktree dashboard with screenshots.

### Retry stranded Claude Code sub-agent writes so the Command River never drops to 0 lanes (#3063) (2026-06-12)
- **Why:** `sync_family_runtimes` advanced the per-session high-water mark for a sub-agent child even when its `ingest_subagent` write raised (the write sits inside a `log.debug`-only try/except). When the daemon hit a transient DuckDB writer-lock / WAL conflict window (for example during a restart), the child row was dropped and the watermark moved past it, so the child was skipped on every later pass even after the store recovered. A real Claude Code session that fanned out to 24 sub-agents could therefore render 0 lanes in the Brain Command River.
- **What:** the watermark now advances only when the sub-agent row actually landed, so a failed write is retried on the next pass (self-healing) instead of being stranded. Unchanged children still short-circuit on the watermark, so the daemon stays light; only genuinely-unwritten children are re-attempted.
- **Verified:** added `test_failed_subagent_write_is_retried_not_watermarked` (revert-proven red without the fix); verified live on a real daemon that parent `claude_code:1aaf7ca1` carries 24 sub-agents in both the local query server and the decrypted cloud snapshot, with zero ingest corruption.

### Record Claude Code sub-agent fan-out as river lanes (#3045) (2026-06-12)
- **Why:** a Claude Code session that fanned out into many sub-agents showed as "1 agent" in the new Brain Flow view, because the daemon recorded only top-level sessions. The sub-agent transcripts (`~/.claude/projects/<cwd>/<session>/subagents/agent-*.jsonl`) were never linked to their parent.
- **What:** `sync_family_runtimes` now records any adapter child session (one whose `parent_id` is set, emitted by the clawmetry-pro claude_code adapter 0.3.5) into the `subagents` table via `ingest_subagent`, with the parent session id, status, cost, tokens, and label. Children are excluded from the top-level sessions list so they do not clutter it, and their per-event rows are skipped (cost rides the sub-agent row, keeping the daemon light). The Brain Flow view then renders each sub-agent as its own lane over time, so a session that spawned 23 helpers shows 23 lanes blooming, not one.
- **Verified:** running the real `sync_family_runtimes` path against a real-scale store produced 23 sub-agent lanes for a session that previously showed 1, with correct labels, status, and cost.

### Restore per-runtime Cost 7d/30d windows + context-econ session_chips dropped by a stale-rebase merge (#3004, #3029) (2026-06-11)
- **Why:** the trajectory-detectors PR (#3020) was cut from a base predating the byRuntime slices PR (#3008), and its squash-merge silently dropped #3008's per-runtime snapshot hunks in `clawmetry/sync.py` while keeping the detector code. The published detectors wheel (0.12.506) therefore lacks `tokens_7d` and `session_chips`, so the cloud Cost week/month cards and Context-economics gauge fell back to lifetime/empty under a single-runtime filter.
- **What:** restored the dropped hunks, additively and without touching the detector code: the rolling 7d/30d per-runtime token+cost windows on `runtimeSummary[rt]` (`tokens_7d` / `cost_7d_usd` / `tokens_30d` / `cost_30d_usd`), the `dailyUsage.byRuntime` 14-day series, and the per-runtime `utilization` + `session_chips` under `contextEconomics.byRuntime[rt]`. Ships alongside the detectors, which stay intact.
- **Verified:** the existing `tests/test_byruntime_slices.py` guard (which survived the merge) was proven RED on the clobbered code (4 failed) and GREEN after the restore (4 passed), so a future clobber fails CI. The published wheel is grepped for both `clawmetry/detectors.py` and the `tokens_7d` + `session_chips` markers in `clawmetry/sync.py` before the cloud repins.

### Recut: publish the trajectory detectors to an installable version (2026-06-11)
- **Why:** the detector code (#3020) and its release entry (#3021) are on main, but the prior release run computed 0.12.505 while a concurrent byRuntime release had already uploaded a 0.12.505 wheel (without detectors) seconds earlier, so PyPI rejected the detectors wheel as a duplicate filename. 0.12.505 on PyPI therefore does not contain `clawmetry/detectors.py`. This recut bumps `dashboard.py` so `max(PyPI, dashboard.py) + 1` lands on the next free version and publishes the detectors for real.
- **What:** version bump only; no code change. The published wheel is grepped for `clawmetry/detectors.py` and the `_emit_detector_incidents` daemon wiring before this is considered done.

### Catch stuck loops, repeated tool failures, and agents that continue after an error (#2999, #3020) (2026-06-11)
- **Why:** the landing page promises ClawMetry catches stuck loops and silent failures, but until now the only signal was a single "long no-progress tool streak" detector. This makes the rest of the claim true with small, judge-free, CPU-cheap heuristics over the trajectories the daemon already has in DuckDB, so it works for every runtime without an expensive LLM judge and without needing the enforcement proxy.
- **What:** a new `clawmetry/detectors.py` with four heuristics, each over a session's recent event sequence: `stuck_loop` (the same tool called with the same arguments three or more times in a row, or a short repeating tool cycle), `no_progress` (many tool calls with zero file writes or edits and no completion), `repeated_tool_failure` (the same tool erroring repeatedly), and a narrow, honest `action_discrepancy` (a tool failed and the agent immediately ran a different command or marked the task done without retrying or acknowledging the error). Each detector is bounded to the last N events, never crashes on malformed input, and has env-tunable thresholds.
- **Honesty note:** `action_discrepancy` is the only place the word "hallucination" is defensible, and only for that concrete behavior. It is heuristic and lower-precision by design, so it is surfaced at a lower severity and never claims hallucination with false confidence in the data.
- **How it surfaces:** the daemon runs the detectors on the same cadence as the existing stuck detector and rides the exact same path, a `loop_signals` row plus the self-clearing heartbeat slice, so each incident appears in the device and cloud alert with zero cloud or firmware change. Incidents are deduplicated per session and kind and self-clear when the behavior stops. This is detection only, never an automatic kill; each incident tells the user they can Stop or Pause the agent from the dashboard or device. Opt out with `CLAWMETRY_DETECTORS=0`.
- **Verified:** positive and negative tests per detector, a healthy-session guard that must flag nothing, a TRAIL-shaped tool-failure fixture, and a daemon-integration test that a seeded looping session surfaces through the loop_signals to device-alert path. The stuck_loop and action_discrepancy guards were proven to fail before the detector logic existed and pass after. Validating against the full MAST-Data and TRAIL datasets is a tracked follow-up.

### Republish the per-runtime byRuntime snapshot slices (burned 0.12.504 recut) (2026-06-11)
- **Why:** the per-runtime byRuntime slices below shipped in code via #3008, and were released as 0.12.504, but that PyPI version was deleted right after upload. A deleted PyPI filename can never be re-uploaded, so the byRuntime code was on main and on the cloud pin but installable nowhere. This recut republishes the same code as the next version so the cloud can repin to something that actually installs.
- **What:** no code change in this entry, this is a clean release of the slices already on main: per-runtime daily series (dailyUsage.byRuntime), per-runtime rolling totals (runtimeSummary tokens_7d / cost_7d_usd / tokens_30d / cost_30d_usd), per-runtime context economics (contextEconomics.byRuntime utilization + session_chips), and the Flow Active-Tools runtime filter.
- **Verified:** the published wheel is grepped for byRuntime, tokens_7d, and session_chips in clawmetry/sync.py and for the _backfillFlowFromBrain runtime filter in clawmetry/static/js/app.js before the cloud repins. The release workflow now bumps from max(PyPI-latest, dashboard.py version) so it skips the burned 0.12.504 (fixed in #3012).

### Per-runtime snapshot slices for the Cost chart, Cost cards, Context economics, and Flow Active Tools (#3004, #3008) (2026-06-11)
- **Why:** the recent runtime-scope sweep made every hosted tab honest, but three sub-panels still fell back to empty or to lifetime numbers when you scoped to a single runtime, because the daemon snapshot carried no per-runtime data for them.
- **What:** the daemon now emits real per-runtime slices, all sourced from the materialized daily rollup table (no extra full event scans). The Cost 14-day chart gets a per-runtime daily token and cost series (`dailyUsage.byRuntime`). The Cost week and month cards get true rolling 7-day and 30-day per-runtime totals (`tokens_7d` / `cost_7d_usd` / `tokens_30d` / `cost_30d_usd` on each runtime summary) instead of standing in lifetime. The Context economics utilization gauge and session chips are now bucketed per runtime, so a single-runtime view shows that runtime's readings rather than an empty state. Every addition is additive; the existing node-wide keys are unchanged.
- **Plus a Flow fix:** the Flow tab's Active Tools row, seeded from recent reasoning events, now respects the runtime switcher, so picking one runtime no longer lights up tools from the others.
- **Verified:** new fixture tests seed the daily rollup with two runtimes across several days and assert the 14-day per-runtime series, the 7-day and 30-day windows, and per-runtime utilization and chips; a JavaScript test runs the Flow backfill over mixed-runtime events and asserts only the selected runtime lights up. Both were proven to fail on the un-fixed code and pass after. The cloud reads these slices via its own interceptors in a separate follow-up.

### Release: kill, pause, and resume a runaway agent on the host (#2996) (2026-06-10)
- New `clawmetry/process_control.py` plus three daemon actions (`kill_session`, `pause_session`, `resume_session`) let an operator stop a runaway agent from the dashboard or the desk device. The cloud relays the command over the existing heartbeat queue; the daemon resolves the session to its real OS process and acts.
- Per runtime: Claude Code is resolved via its live PID map (`~/.claude/sessions/<pid>.json`), Codex/Goose/opencode/Aider via working-directory plus argv match; OpenClaw and NemoClaw are cancelled through `openclaw tasks cancel`. Cursor is intentionally unsupported (one IDE process holds every session).
- Stop sends SIGINT to cancel the current turn; kill escalates SIGTERM then SIGKILL across the full descendant set; pause uses SIGSTOP and resume uses SIGCONT, so a paused agent holds its state and continues where it left off. A pid reuse guard re-verifies process start time before any signal, and every action also writes the proxy HITL pause file so a proxied runtime refuses further model calls even if a signal is missed. Every kill, pause, and resume writes an audit row.
- The action types ship inert: nothing happens until the cloud enqueues a command for a node the requester owns.

### Fix: approval policies now fire for Claude Code, Codex, Cursor and the other family runtimes (#2984) (2026-06-10)
- **Approval policies silently never fired for the family runtimes.** Those adapters record each tool call as its own `tool_call` event carrying a `tool_calls` array, but the policy watcher only scanned `message`/`assistant` events and could not parse the array shape, so a rule like "pause on `rm -rf`" matched nothing a Claude Code or Codex agent did. On a real node, a 14-day replay saw 15 tool calls before this fix and 5,015 after (310 matches for a risky-exec rule, all correctly attributed).
- The watcher and the new replay endpoint now share one event-type list (so the eval can never disagree with enforcement), and the extractor understands the family adapters' `tool_calls` array, including args under `input`, `arguments`, or `args`. Tool-result echoes (non-assistant roles) still never fire policies.
- Found by replaying a candidate policy over the live store with the eval shipped in #2980. Guarded by tests that use the exact row shape observed in a live database.

### Approvals: test a rule before you turn it on (replay eval + monitor mode) (#2980) (2026-06-10)
- **Replay a candidate policy against your own history (`POST /api/policy/replay`).** Before saving an approval rule, you can now see exactly what it would have paused over the last N days (up to 30), across every runtime: match counts, a per-runtime and per-tool breakdown, and up to 20 sample commands. Nothing is created, blocked, or sent to the cloud; it is a pure read over the local event store. This turns "will this rule pause my agent every 30 seconds?" from a guess into a number.
- **`action: monitor` policies (dry run).** A policy can now run in monitor mode: when it fires, ClawMetry records what it would have paused in the approvals audit feed (status `simulated`) and lets the agent continue untouched. No cloud round-trip, no blocking, no session kill. Trial a rule live for a few days, read the audit feed, then flip it to `require_approval` with confidence. The `/api/approvals-audit` summary now reports a `simulated` count alongside pending/approved/denied.
- Both features reuse the existing policy engine end to end (same YAML and cloud-builder policy shapes, same cross-harness tool aliasing), so a rule authored for `exec` evaluates Claude Code's `Bash`, Codex's `shell`, and friends identically. Verified by 12 new tests including revert-proofs and guards that fail if monitor mode ever reaches the cloud or the kill path.

### Cost accuracy: stop double-counting turns, scope Top Sessions per runtime, fix $0 hosted models (2026-06-10)
- **No more doubled cost on the Models tab, 24h columns, sessions list, and device summary (#2972, #2976).** OpenClaw v3 records each billable turn as two rows (an assistant row and a sibling completion row with the same cost and tokens). Several rollups summed both, so cost and token totals read up to double on the Models tab, the 24h spend columns, the per-model breakdown, the sessions list, and the desk device, while the Cost tab showed the correct number. All of these now use the same de-duplication the Cost tab already used, so every cost surface agrees.
- **Top Sessions by Cost now honours the runtime switcher (#2976).** With a specific runtime selected, the Cost tab's "Top Sessions" listed node-wide sessions. It now scopes to the selected runtime.
- **Hosted Mistral, Qwen, and DeepSeek are no longer priced at $0 (#2976).** Any model whose name contained one of those families was treated as a free local model, so real API spend showed as $0. Mistral now uses its real per-token rates, Qwen and DeepSeek use a conservative non-zero rate, and genuinely local models (llama, gemma, phi, or anything with an explicit local prefix) stay free.
- **Namespaced model ids now price correctly (#2976).** Models addressed through OpenRouter (`anthropic/claude-...`) or Bedrock (`us.anthropic.claude-...`) missed the model-specific pricing and fell back to a generic rate, undercharging Claude by roughly 5x. The pricing lookup now strips the provider namespace first.

### Security: SSRF guard on webhooks, interceptor no longer breaks streaming, atomic 0600 config (2026-06-10)
- **SSRF guard on alert webhooks + gateway config (#2967).** User-configured webhook URLs (generic/Slack/Discord) were POSTed to with no validation, so a webhook pointed at an internal address could reach the cloud metadata endpoint, the local gateway, or other internal hosts. Outbound webhook targets are now validated and any host that resolves to a loopback, link-local, private, reserved, multicast, or unspecified address is refused. The `/api/gw/config` setup route, which opens an outbound connection to a caller-supplied URL, is no longer auth-exempt for non-loopback callers.
- **Interceptor no longer breaks streaming or writes into the agent workspace (#2969).** The optional HTTP interceptor force-read every response body, which for a streaming request consumed the caller's stream before it could iterate (turning token-by-token streaming into a single blocking wait). It now captures the body only for non-streaming calls. Its cost sidecar moved from `~/.openclaw` (the agent's workspace, which ClawMetry must not write to) into ClawMetry's own `~/.clawmetry` directory; the daemon tails both the new and legacy locations so nothing is lost.
- **config.json written atomically as 0600 (#2969).** The config file (which holds the API key and encryption key) was created world-readable for a brief window before its mode was tightened. It is now created 0600 atomically, closing that window on shared hosts.

### Security: sanitize transcript markdown (XSS) + authenticate OTLP receivers (2026-06-10)
- **Stored XSS fixed (#2958).** Transcript markdown was rendered with `marked.parse()` straight into `innerHTML`, with no sanitization. Transcript content includes agent output, tool arguments, exec commands, and inbound chat-channel messages, so a payload such as `<img src=x onerror=...>` could run script in the dashboard origin (gateway-token theft locally, cloud-key theft on the hosted dashboard). All markdown now goes through `cmSafeMarkdown()`, which runs `DOMPurify.sanitize()` over the parsed output before it touches the DOM. `marked` and DOMPurify are vendored and pinned (`static/vendor/`), replacing an unpinned CDN script. Verified: 6 attack vectors neutralized, real markdown preserved; guard test asserts every `marked.parse()` is sanitizer-wrapped.
- **OTLP receivers authenticated + DoS-bounded (#2961).** The `/v1/metrics`, `/v1/traces`, and `/v1/logs` ingest endpoints skipped the auth check (it only applied to `/api/*`), so anyone who could reach the port could inject fake cost and token data. They are now gated like `/api/*`: loopback stays trusted (zero-config local exporters keep working), non-loopback requires the gateway token, with an opt-out env for trusted LANs. The gzip decode path is bounded (a small gzip bomb could decompress to many gigabytes and exhaust memory) and a request-body size cap was added. Guard test covers the auth gate and the gzip bound.

### Release: PR-sweep roll-up: MCP server, token accuracy, session search, eval gates (2026-06-10)
- **`clawmetry mcp` (#2931):** a stdlib-only MCP stdio server with five read-only tools (list_sessions, get_cost_summary, get_session_trace, list_events, get_health) over the daemon's local query endpoint, so agents can query their own telemetry. Verified with a live initialize/tools/call round-trip against a running daemon.
- **Token accuracy family:** output_tokens floor seeded from message_start with max-only reconciliation (#2905); reasoning/thinking tokens extracted in the openclaw adapter via a shared helper with regression tests (#2948); reasoning_tokens tracked through the proxy SSE parser, SQLite, and interceptor JSONL (#2913); SDK totalTokens preferred in spans, combined with reasoning as max(totalTokens, in+out+reasoning) so nothing double-counts (#2936).
- **Session search (#2928):** GET /api/local/search over title + eval_reason through the daemon proxy (no writer-lock contention), limit clamped, 8 tests.
- **Observability + safety:** full-native nemoclaw build detection via enforcement symbols (#2926); per-session tool-order churn detection, info-level and never-blocking (#2923); cache/compression-safety eval suite as a deterministic CI gate (#2930); deterministic/code evaluator library (#2920); C1 golden path gains a content-verification tier and the tab sweeps cover all 32 dashboard tabs (#2922, #2937, #2949).

### Fix: openclaw reasoning/thinking tokens now extracted (#2876) (2026-06-10)
- Anthropic extended-thinking sessions emit a reasoning-token share inside the per-turn `usage` object that input+output alone never account for. The openclaw adapter's usage-extraction only read input/output/cacheRead/cacheWrite, so `Session.reasoning_tokens` was always 0 and per-turn `token_count` was systematically under-reported for reasoning-capable models.
- New `_reasoning_tokens()` helper reads any known spelling (`reasoning_tokens`, `reasoningTokens`, `thinking_tokens`, `thinkingTokens`, `thinking_input_tokens`, …), coercing to a non-negative int. Wired into `list_events()` (surfaces `reasoningTokens` in `event.extra`), `_build_spans_from_events()` (adds `tokens_reasoning` and folds it into the LLM span's `token_count`), and `list_sessions()` (populates `Session.reasoning_tokens`).
- Verified: new tests pin the reasoning-token extraction, the helper's key-variant/garbage-input handling, and existing input/output/cache splits stay unchanged.

### Release: runtime paywall shows the real plan ladder (#2945) (2026-06-09)
- The "Two ways to observe X" card asked users to start a trial without ever saying what the plans are. The modal now mirrors the live clawmetry.com/pricing ladder: Free $0 forever (OpenClaw + NemoClaw), Starter $9/node/mo (every supported runtime, 7-day free trial, no card), Pro $29/node/mo (alerts, budgets, loop detection, fleet), with a footnote that annual plans include the desk device and that self-hosted uses the same plans with a license key (link to /pricing).
- Prices live in one `_cmPlanPrices` object so a reprice is a one-line change. Trial CTA and paywall telemetry wiring unchanged; guard tests assert tiers, the self-hosted mention, the pricing link, and the no-em-dash copy rule.

### Release: locked-runtime upgrade affordance renders in grace mode (#2942) (2026-06-09)
- The conversion surface was dead: grace mode reported every paid runtime as allowed, so the runtime switcher's lock affordance and the two-path upgrade card never rendered for anyone (12 paywall views in 30 days fleet-wide), even though an unentitled account's paid-runtime data is never ingested anyway (the pro adapter only auto-provisions for entitled accounts). "Allowed by grace" was indistinguishable from "silently broken".
- New grace-independent `Entitlement.entitled_runtime()` plus an `entitled` flag on every `runtime_catalog()` entry; `allowed`/`locked` enforcement semantics are unchanged. The catalog loader now marks paid, unentitled runtimes with the lock affordance even in grace; selecting one opens the existing non-blocking two-path card, and runtimes detected on the machine keep the "running here" label.
- Hosted guard: the cloud container resolves entitlement as OSS-free, so in CLOUD_MODE the teaser is suppressed for pro/starter/paid plans and active trials (account plan + trial state, re-checked after the async account load). A paying or trialing hosted user never sees it.
- Verified: 40 entitlement/catalog/route tests green incl. a JS-wiring guard; revert-proof: the new tests fail on the prior build.

### Release: auto-update ON by default for the supervised sync daemon + crash-loop rollback guard (#2939) (2026-06-09)
- Why: the 2026-06-09 fleet audit found 92% of active nodes running daemons months behind the pinned cloud wheel (75% at 0.12.0-0.12.299 vs 0.12.493). Auto-update existed but was opt-in, so effectively nobody had it; every shipped fix reached almost nobody and the hosted dashboard rendered blank or stale cards against old snapshots, including for paying users.
- `auto_update` now defaults ON, acting ONLY in the supervised sync-daemon process (launchd/systemd, role passed by `run_daemon`); the dashboard process keeps the explicit opt-in toggle. Rails: `CLAWMETRY_AUTO_UPDATE=0` hard kill switch, the existing 48h PyPI release-age stability window, and an unsupervised daemon installs the new wheel but defers its restart (never self-kills ingest with nothing to respawn it).
- New `clawmetry/update_guard.py`: firmware-OTA-style crash-loop rollback. `perform_self_update` arms it after pip succeeds; `run_daemon` checks it at boot. Three rapid boots on a fresh wheel roll back to the previous version (recorded in `~/.clawmetry/update_rollback.json`) and exit for the supervisor to respawn on the known-good build; a healthy run self-confirms after 5 minutes.
- Verified: 21 unit tests (gating, kill switch, role separation, deferred restart, 3-boot rollback, failed-rollback-keeps-running, expiry/mismatch/confirm) plus a revert-proof: the default-on test fails on the prior opt-in default.

### Release: daemon auto-provision UPGRADES clawmetry-pro (+ valid wheel filename) (2026-06-09)
- `auto_provision_pro` returned early whenever pro was importable, so an installed pro NEVER upgraded — rolling a newer wheel to the cloud reached no existing node (the claude_code ai-title fix in pro 0.3.4 sat unused because every daemon kept 0.3.3). Now it re-validates against the server each cycle: downloads the small wheel, reads its METADATA version, and installs (pip --upgrade) only when strictly newer; a download/check failure keeps the current version (never strands a working node).
- `_download_wheel` saved to a random `mkstemp` name (`clawmetry_pro-ab12.whl`) that pip rejects as "not a valid wheel filename", silently breaking every re-download. Now it preserves the real PEP-427 filename from Content-Disposition in a temp dir.

### Release: clean claim-watcher re-exec (#2918) (2026-06-09)
- The one-step onboarding claim-watcher (0.12.491) re-execs to adopt the real account. os.execv keeps the same PID, so _acquire_pid_lock saw its own live PID and the DuckDB writer lock stayed held — the re-exec'd daemon could fail to start (relying on the launchd KeepAlive crash-restart). Now it stops the store (flush + release the writer lock) and releases the pid lock before execv, so the restart is clean.

### Release: one-step first-node onboarding — daemon adopts the real account automatically (#2915) (2026-06-08)
- A zero-friction install lands on a throwaway placeholder account (agent+<hash>@clawmetry.auto), invisible from the user's real login. The daemon now watches for that node being claimed onto the user's real account (by the cloud /cloud auto-claim when `clawmetry connect` opens the browser) and adopts it automatically — NO `clawmetry connect --key` step.
- While on a placeholder, the daemon polls /api/cloud/claim-status every 5s; the moment the node is claimed it rewrites config with the real key and re-execs, so every thread (heartbeat, snapshot push, pro auto-provision) restarts on the real account and the node syncs there directly. Re-exec also runs the existing pro auto-provision, so adopting a Trial/Pro key installs the pro package and the other runtimes (Claude Code, Codex, …) start syncing automatically.

### Release: warn when a machine is on a temporary (unlinked) account (#2910) (2026-06-08)
- Fixes the recurring "I installed ClawMetry but my dashboard shows 0 nodes" trap. A zero-friction install binds the daemon to a throwaway placeholder account (agent+<hash>@clawmetry.auto, renamed .linked after device pairing) that is invisible from the user's real login, so the node silently never appears under their email. `clawmetry status` printed the placeholder account with no hint anything was wrong.
- `clawmetry status` now tags the account line ("temporary, not linked") and prints a block with the exact relink command; the zero-friction `clawmetry connect` prints the same warning at install time (skipped for a keyed `--key cm_...` connect, which lands on the real account). To sync a machine to your account, run the `clawmetry connect --key cm_...` command from the "+ Add node" box on app.clawmetry.com/cloud.

### Release: tamper-evident hash chain ON by default (#2906) (2026-06-08)
- The Free, always-on tamper-evident hash chain (Security tab integrity card + `clawmetry verify-integrity`) defaulted to OFF (`CLAWMETRY_INTEGRITY=0`), so on a standard install nothing ever stamped and the integrity card showed a perpetual "empty" state (chain_length=0). Default it ON to match the product promise; set `CLAWMETRY_INTEGRITY=0` to disable on an extreme-volume node.
- The per-flush duplicate check is now a single `IN(...)` lookup instead of a `SELECT` per event (flush batch up to 1000 rows), keeping default-on stamping within the daemon CPU budget. `events.id` is an indexed PRIMARY KEY so the lookups are point ops, not scans.

### Release: OTLP spans now actually persist in production (#2896) (2026-06-08)
- **Bring-your-own-agent was silently dropped:** the /v1/traces receiver runs in the dashboard process, which does not own the DuckDB writer lock, so get_store() returns a proxy that forwards writes to the daemon but only passes keyword args. put_span was called positionally and was not in the daemon allowlist, so every OTLP span no-opped whenever a daemon runs (every real install): the POST returned 200 but nothing persisted, and a foreign OpenLLMetry/OTLP app never appeared in the runtime switcher or Agent Inventory. The OTLP test suite missed it because it forces single-process, where get_store() is the real writer.
- **Fix:** allowlist put_span in routes/local_query._DAEMON_METHODS and call put_span(span=...) by keyword so the span forwards through the proxy to the daemon writer (same pattern as set_agent_meta). A new regression test forces the proxy path the suite skipped and asserts the span forwards as a keyword plus put_span is allowlisted.
- **Verified live:** a real OpenLLMetry-shaped OTLP trace sent to a running daemon+dashboard now persists in DuckDB, surfaces via query_otlp_app_rollup with derived cost, flows into runtimeSummary + agentInventory, and renders on the hosted dashboard as an "(OTel)" agent row plus the switcher "OpenLLMetry / OTLP apps" optgroup. Before the fix: zero spans persisted.

### Release: OpenLLMetry/OTLP apps visible in the runtime switcher + inventory (#2871) (2026-06-08)
- **Bring your own agent, now visible:** a foreign OpenLLMetry/OTel-instrumented app (LangChain, CrewAI, OpenAI Agents, custom) that sends OTLP traces now appears as its own entry in the global runtime switcher (under an "OpenLLMetry / OTLP apps" group) and as a real row in the Agent Inventory roster, with its cost, tokens, and session counts. Completes #2822 (which gave such apps an agent_type from service.name) and #2853 (the inventory roster).
- **How:** the daemon's cached rollup runs one GROUP BY agent_type over the spans table for agent_types that are not one of the 12 known session-prefix runtimes (top 50 by recent activity, with a logged warning on truncation), never a per-request scan. Native runtimes still filter by session-id prefix; OTLP apps filter by agent_type, so the two paths stay disjoint and the per-runtime no-leak contract holds (extended test asserts no leak in either direction). Rides the existing runtimeSummary + agentInventory snapshot slices, so the hosted dashboard picks it up on the next version pin with no new interceptor.
- **Verified:** 11 new tests incl. the extended no-leak contract and a CPU-budget structural guard; in-process E2E confirms an OTLP app surfaces with correct cost and scopes only to itself.

### Release: Agent Inventory tab + evaluator library + audit log made real (#2853, #2863, #2845) (2026-06-08)
- **Agent Inventory tab (#2853):** a single-pane control-tower roster of every agent on the node, with what it runs, what it costs, whether it is alive, its outcome, and an editable owner label. Composed from already-computed rollups (no new per-request scan); newcomer-first plain language; honest node-wide scope note under the runtime switcher; per-runtime no-leak contract preserved (agentInventoryByRuntime returns only the selected runtime's row). New snapshot keys agentInventory + agentInventoryByRuntime, /api/inventory route, agent_meta store table.
- **Named evaluator library (#2863):** ClawMetry's existing quality signals are now a named, branded evaluator catalogue (agent-goal-accuracy from the outcome classifier, agent-flow-quality from the reliability score, answer-quality from the local LLM judge, pii/secrets/prompt-injection detectors from the policy-event scan, hallucination-risk, plus Pro entries agent-efficiency, agent-tool-error-detector, and the new content-grounded faithfulness evaluator). GET /api/evaluators serves the catalogue (cloud-safe, no-store path returns it); an anti-drift test asserts every free evaluator maps to a real signal. Pro faithfulness compute lives in clawmetry-pro, local-first on the user's own key; OSS shows a locked state until the plugin is present.
- **Audit log made real (#2845):** record_audit had zero callers, so the Enterprise audit log was a hollow pipe. Wired producers at approval / HITL / budget / alert-rule decision sites, surfaced the tamper-evident hash-chain integrity status and a recent-activity feed in the Security tab, and added a regression test that mechanically asserts an audit row lands on each producer path.
- **Why:** these are the prosumer "AI control tower" surfaces from the Traceloop/ServiceNow competitive direction: discover every agent, govern with a real audit trail, and grade quality with a named evaluator library, for the operator who will never buy an enterprise governance suite.
- **Verified:** 25/25 CI on #2853 and #2845, 19/19 on #2863; 9 inventory tests, 8 catalogue tests (incl. anti-drift), 13 audit-producer tests, 11 Pro faithfulness tests. Cloud interceptors (cm-cloud-inventory, cm-cloud-security, cm-cloud-evaluators) + the Pro wheel rebuild follow in the cloud repo.

### Release: OpenLLMetry ingest + eval-to-alert loop (#2822, #2823) (2026-06-08)
- **Accept OpenLLMetry traffic end to end (#2822):** any OpenLLMetry/OTel-instrumented app (LangChain, CrewAI, OpenAI Agents, custom) can now point its OTLP exporter at ClawMetry and render correctly. The /v1/* receivers accept OTLP/JSON and gzip (previously protobuf-only, others got HTTP 400); indexed gen_ai.prompt.N.content / gen_ai.completion.N.content attributes assemble into input/output (size-capped); resource service.name maps to a per-app agent_type slug (fallback "custom") so foreign spans no longer mis-bucket under the OpenClaw runtime; live tiles read gen_ai.usage.* keys and count GenAI spans as runs; /v1/metrics ingests gen_ai.client.token.usage and gen_ai.client.operation.duration.
- **Why:** OpenLLMetry is the neutral OTel GenAI instrumentation standard (it remains open source post acquisition). This makes "bring your own agent" real: two lines of their code, zero ClawMetry SDK.
- **Eval-to-monitor loop (#2823):** two new alert rule types, eval_score_below (average judge score over a window drops below threshold) and outcome_failure_rate (failed/stuck/loop sessions exceed a percent of classified sessions), both gated by min_sessions to avoid single-sample noise; /api/run-compare now includes eval_score with signed delta, eval_reason, per-side outcome and an improved/regressed/same verdict. Eval scores and outcome labels existed but triggered nothing; now they alert and grade run comparisons.
- **Verified:** 25/25 CI checks on both PRs; 14 new OTLP edge-case tests incl. a real OpenLLMetry-shaped fixture; 15 new alert/run-compare tests; runtime-filter no-leak contract test passes.

### Added
- **Billing-mode detection** — the daemon now detects whether each runtime is on a **subscription** (Claude Pro/Max, ChatGPT, Cursor) vs **metered** API key vs **local** (Ollama/llama.cpp), cross-platform (macOS/Windows/Linux), reading only non-secret config (`~/.claude.json` `oauthAccount`, env/config keys — never a keychain secret, never a prompt). Pushed on the heartbeat so the cloud + desk device show **actual cash** big and **API-equivalent** small (a Max-20x user's $7k/day API-equivalent is ~$6.67/day actual). Spec: `docs/BILLING_MODE_DETECTION.md`.

### Release: trial-bug alerts modal + remaining frontend (2026-06-06)
- Publishes the alerts editor-modal fix (#17, always-render + client-side gate) plus all trial-bug frontend on main (clusters endpoint, security guards) so the hosted dashboard serves them after the cloud pin.


### Trial-bug daemon slice: approvals audit (2026-06-06)
- **approvalsAudit**: ship the exec-approval decision audit (refactored routes/policy.py into a reusable _approvals_audit_payload) so the Policy tab audit renders on the hosted dashboard. The cloud interceptor already reads sp.approvalsAudit.


### Trial-bug daemon slice: Harness tab (templates + per-runtime data) (2026-06-06)
- **harness**: ship the Harness slice (templates + per-runtime data blobs) so the Harness tab renders on the hosted dashboard instead of "Loading harness view..." forever. Refactored routes/harness.py http_harness_data into a reusable _harness_data_for(runtime) shared by the route + the snapshot. Cloud interceptor follows.


### Trial-bug daemon slice: cron health summary (2026-06-06)
- **cronHealthSummary**: ship the cron health summary (reuse routes.crons._try_local_store_cron_health_summary) so the "Cron Health Monitor" card renders on the hosted dashboard instead of blank. Cloud interceptor follows.


### Trial-bug daemon slices: autonomy, context util, transcript runtime (2026-06-06)
- **autonomy**: snapshot now carries the autonomy block (reusing the store-backed `routes.autonomy._try_local_store_autonomy`) so the Overview "How independent is your agent?" card renders on the hosted dashboard instead of being stuck on "Just getting started".
- **contextEconomics.utilization**: ship the utilization time-series (it was computed but never stored) so the cloud context-window gauge has readings.
- **transcripts**: stamp `runtime` on each snapshot transcript so the cloud Transcripts tab can filter by runtime (was unset, so every session looked like openclaw).
- Part of the verified trial-bug remediation; cloud interceptors that read these slices follow.


### Release: honest per-runtime scope banner on Overview (#2763) (2026-06-06)
- **Why:** Overview mixes runtime-scoped cards (today's tasks/outcome, activity strip, hero token/cost) with node-wide cards (autonomy, reliability, activity heatmap). Showing node-wide numbers under a runtime filter confused users.
- **What:** when a specific runtime is selected, Overview shows one banner stating exactly what is scoped vs node-wide, so a node-wide number never looks runtime-specific. Removed on "all".
- **Verified:** node --check.


### Release: per-runtime scoping for the Overview outcome tile + activity strip (#2761) (2026-06-06)
- **Why:** with the runtime switcher set to a specific runtime, the Outcome tile and the activity-counters strip showed identical node-wide numbers for every runtime (only the header session count + spend re-scoped). Confusing: codex and openclaw appeared to do the same work.
- **What:** query_outcomes / query_events / query_tool_call_invocations accept a runtime filter (the canonical session-prefix clause); the snapshot emits outcomesByRuntime + activityTodayByRuntime; /api/outcomes + /api/activity-today accept ?runtime=; the loaders pass the switcher value. Cloud cm-cloud-outcomes / cm-cloud-activity interceptors serve byRuntime and never fall back to the node-wide number for a specific runtime.
- **Verified:** tests/test_per_runtime_filter.py (per-runtime filtering; unknown runtime leaks nothing).


### Release: CPU budget, the daemon stays light (#2750, #2751) (2026-06-06)
- **Why:** the sync daemon was observed at ~200% CPU (two full cores) on a 12-core box. Profiling showed ~100% inside DuckDB (allocator + BufferPool::EvictBlocks). Root cause: DuckDB defaulted to threads == core count (so one aggregate query fanned across all 12 cores) and the hot query_aggregates rollup was re-run on every dashboard poll with no cache.
- **What:** (1) every DuckDB connection now caps threads (default 2) + memory_limit (default 2GB), env-overridable via CLAWMETRY_DUCKDB_THREADS / CLAWMETRY_DUCKDB_MEMORY_LIMIT, so no single query can take over the machine. (2) query_aggregates is result-cached with a short TTL (default 20s, CLAWMETRY_AGG_CACHE_TTL, 0=off); the daemon recomputes on a timer and handlers read the cache, which is what actually cuts AVERAGE CPU. Now a FLYWHEEL principle (the daemon targets <=5-10% CPU).
- **Verified:** tests/test_duckdb_cpu_cap.py + tests/test_aggregate_cache.py; live profile confirmed DuckDB was the hot path.


### Release: outcomes snapshot slice for the hosted Outcome tile (#2746) (2026-06-06)
- **Why:** the revived Overview Outcome tile fetches /api/outcomes, which on the hosted dashboard hits a server with no local DuckDB, so it showed "no completed tasks" even when the node had outcomes.
- **What:** an `outcomes` slice (1d roll-up) added to the E2E snapshot, mirroring routes/sessions.api_outcomes (query_outcomes then aggregate_outcomes) on the daemon's own store handle. A cm-cloud-outcomes interceptor renders the tile client-side from the snapshot; cloud stays blind.
- **Verified:** py_compile; reuses the same store method + classifier as the OSS route.


### Release: surface today's activity counters (#2742) (2026-06-06)
- **Why:** _collect_activity_counters_today (tool calls / exec / browser / messages / unique tools today) was defined but never called, so the numbers were computed and dropped with no UI (UI-coverage audit).
- **What:** an activityToday slice in the E2E snapshot, a cached (30s) /api/activity-today route reading the same DuckDB rollup, and a compact "Today" activity strip on the Overview tab (hidden until there is activity).
- **Verified:** py_compile (sync + usage), node --check app.js, Jinja renders the strip ids. Cloud cm-cloud-activity interceptor follows for hosted parity.


### Release: revive dead-UI cards from the UI-coverage audit (#2739, #2740) (2026-06-06)
- **Why:** a verified UI-coverage audit ("every signal we capture must have a UI") found several cards that existed only in the dead first DASHBOARD_HTML block, so they never rendered despite fully-working JS, the same trap that hid the eval tile.
- **What:** lifted four cards into live templates: Cost Forecast + Prompt Cache (Usage tab), the Today task-outcome tile (Overview), and the proxy Loop-signals badge + table (Brain). No JS changes needed; the existing loaders (loadCostForecast, loadCacheAnalytics, loadOutcomeTile, loadLoopSignals) already targeted these ids.
- **Verified:** Jinja renders usage.html / overview.html / brain.html with every revived id present; JS call sites confirmed in loadUsage / overview load / loadBrainPage.


### Release: eval scores in the encrypted snapshot (hosted dashboard) (#2736) (2026-06-06)
- **Why:** the Eval card fetches /api/evals/summary, which on the hosted dashboard hits a server with no local DuckDB, so it always showed an empty placeholder.
- **What:** the daemon now adds an `evals` slice (avg score + coverage over 24h, plus recent scored sessions) to the E2E-encrypted snapshot, built on the daemon's own store handle. A cloud interceptor can render the Eval card client-side from the decrypted snapshot; the cloud server never sees the data. Best-effort; empty until a judge key is set.
- **Verified:** py_compile; mirrors the existing contextEconomics/toolCatalog snapshot slices. Live-verified by decrypting the snapshot for the `evals` key after release.


### Release: evals privacy + a live UI to set the judge API key (#2725, #2726) (2026-06-06)
- **Why:** the eval judge sends session transcripts to a third-party LLM (Anthropic/OpenAI), but transcripts were sent UNREDACTED, and the only way to provide the required key was a daemon env var most users never set. The eval UI that would expose this had been orphaned in the dead DASHBOARD_HTML block, so it never rendered.
- **What:** (1) transcripts are now redacted before the judge: the ingest secret redactor (API keys, tokens, Bearer, private keys) plus an email-PII pass, before truncation, respecting CLAWMETRY_REDACT. (2) A live Eval card on the Overview tab (avg score + coverage) opens a modal with a Judge API key section: pick provider, paste key, Save. The key is stored locally chmod 600 (never synced), and the eval runner resolves env var first then the saved key, fresh each tick. Presence-only status, never the value.
- **Verified:** tests/test_eval_redact_before_judge.py + tests/test_eval_judge_key_store.py; Jinja renders the live overview card + modal with the key input present.


### Release: evals skip quietly when no judge API key is configured (#2718) (2026-06-06)
- **Why:** evals are default-on, but the judge calls a real LLM (Anthropic/OpenAI) needing an API key. With no key the scheduler attempted every session and logged a warning each tick ("evals: judge call failed ... ANTHROPIC_API_KEY not set"), spamming sync.log; on a box that did have a key in the daemon env it would also spend silently.
- **What:** `score_session` checks for the judge model's provider key up front (gpt/o* -> OPENAI_API_KEY, else ANTHROPIC_API_KEY). With no key it returns a quiet SKIP, never invokes the judge, and logs the notice once per process. Evals are now effectively implicit opt-in: they run (and spend) only when an LLM key is set.
- **Verified:** `tests/test_eval_skip_without_key.py` (no key -> skip + judge not called; with key -> not the no-key path).


### Release: evals judge works without httpx (stdlib urllib fallback) (#2715) (2026-06-06)
- **Why:** the evals judge hard-imported `httpx` to route its LLM call through the cost interceptor, but httpx is not a clawmetry dependency (deps stay minimal: flask + waitress + cryptography). On the daemon's own venv every judge call died with "No module named 'httpx'" (sync.log: "evals: judge call failed ... No module named 'httpx'") and no session was ever scored.
- **What:** `_judge_http_post_json` prefers httpx when installed (keeps interceptor cost tracking for eval spend) and falls back to stdlib urllib when it is not, so the judge runs on a minimal install. Both provider branches (Anthropic + OpenAI) route through it.
- **Verified:** `tests/test_eval_judge_httpx_fallback.py` (urllib fallback when httpx absent, Anthropic + OpenAI parse paths, missing-key raises).


### Release: `clawmetry status` shows the linked account email (#2710) (2026-06-05)
- **Why:** status showed the api_key but not which account the node is linked to, so a node connected to the wrong account (the two-account trap) was invisible from the box.
- **What:** an `Account:` line resolves the email (and plan) from the cloud via `/api/cloud/account`. Best-effort: a non-`cm_` key skips the call, and a short 2.5s timeout plus never-raise keep status fast and offline-safe (the line is simply omitted when the lookup fails). Honours `CLAWMETRY_APP_BASE`. Wired into both status output paths.
- **Verified:** `tests/test_status_account_email.py` (resolves email+plan, non-`cm_` key skips the network, offline is graceful, honours `CLAWMETRY_APP_BASE`).

### Release: detected runtimes classified by activity (last_active + status + source) (#2707) (2026-06-05)
- **Why:** detecting a runtime by its on-disk data dir does not mean it is in active use. A Cursor `state.vscdb` or an `opencode.db` can sit untouched for months, but the Fleet showed every detected runtime as "syncing" next to the one you used minutes ago. On a real box a Cursor chat history last written in July 2025 rendered like a live node, and an OpenClaw sub-agent looked like a standalone install.
- **What:** `_detect_runtimes_for_heartbeat` now enriches each reported runtime with `last_active` (epoch, newest mtime of its native store via a bounded walk so a large `~/.claude/projects` tree cannot slow the heartbeat), `status` (`active` used within 7 days, `idle` within 30 days, `stale` older, `unknown`), and `source` (`standalone` vs `openclaw_subagent` when the only or most recent activity is via `~/.openclaw/agents/<runtime>`). Additive and back-compat; consumers that ignore the new keys are unaffected. The cloud Fleet badge that renders this ships separately.
- **Verified:** `tests/test_runtime_activity_status.py` (active/idle/stale/unknown, standalone vs sub-agent precedence, newest-mtime picks the recent file, heartbeat carries the status).

### Release: clawmetry-pro installs into a HOME fallback when site-packages is read-only (#2704) (2026-06-05)
- **Why:** a system-wide install (e.g. `/opt/clawmetry` owned by root) run by a non-root daemon (a systemd user service) cannot write the Pro wheel into the interpreter site-packages. The auto-provisioner failed with `[Errno 13] Permission denied: .../site-packages/clawmetry_pro`, so the paid runtime adapters (Claude Code, Codex, Cursor, and more) silently never loaded despite an entitled account. The only workaround was a manual `sudo chown`, which no normal user discovers. Found on a real self-hosted box.
- **What:** `_site_packages_target()` now reports whether the interpreter site-packages is actually writable (`os.access` W_OK). When it is not, the wheel extracts into a HOME-owned fallback dir (`~/.clawmetry/pro-packages`) and that dir is put on `sys.path` so the adapters import, with no sudo or chown needed. `_pip_install_wheel` short-circuits to the same path (pip would fail on read-only site-packages too). `ensure_pro_on_path()` adds the fallback to `sys.path` at daemon startup before plugin discovery and before each provision, so an already-fallback-installed pro is detected and the install stays idempotent. Covers any read-only-install layout, not just `/opt`.
- **Verified:** `tests/test_pro_install_fallback.py` (read-only goes to the fallback and onto the path; pip short-circuit; writable uses the normal path; `ensure_pro_on_path` idempotent); 30 license tests pass.

### Release: deviceSummary slice in the cloud snapshot (WiFi hardware transport) (#2677) (2026-06-04)
- **Why:** step 2 of the hardware-companion initiative. The device transport is WiFi-to-cloud (works for the whole fleet from anywhere, unlike a BLE-to-one-machine buddy). ClawMetry's E2E invariant means the cloud cannot read your data, so the device must hold the key and decrypt a slice itself.
- **What:** the daemon now emits a compact all-runtime `deviceSummary` slice (cost_today_usd, tokens_today, active_sessions, runtimes_active, health, approval, alert) into the existing E2E-encrypted snapshot, via `_build_device_summary` on the daemon's own store handle (never a read_only re-open, per FLYWHEEL §1). A WiFi device GETs the snapshot from cloud, decrypts with the user's key, and renders just this slice; the cloud stays blind. Approve/Deny is wired (the daemon owns the approvals queue); `alert` is null for now (its history lives in the dashboard process, a follow-up).
- **Verified:** `tests/test_device_summary_snapshot.py` covers shape, cost/token passthrough, never-raise on missing inputs, active-session counting, and oldest-pending-approval surfacing plus amber health. Post-release the live cloud snapshot is decrypted to confirm the slice is present.

### Release: device snapshot, an all-runtime feed for a hardware companion (#2673) (2026-06-04)
- **Why:** step 1 of the physical-companion initiative. Devices like Clawdmeter and Anthropic's claude-desktop-buddy (plus the $99 reseller riding its firmware) are Claude-only by design. ClawMetry already ingests all 12 runtimes into DuckDB, so one device fed by ClawMetry covers every runtime, not one vendor. This is the foundation under the firmware and the pre-order; it proves the whole data path with zero hardware.
- **What:** new `bp_device` (routes/device.py). `GET /api/device/snapshot` returns a compact, screen-sized, all-runtime payload (cost_today_usd, tokens_today, active_sessions, runtimes_active, health green/amber/red, top firing alert, oldest pending approval). DuckDB-first via the daemon proxy (never raw FS), a 5s TTL cache so a chatty device cannot storm the daemon, and never-raise so the device always gets a valid shape. `GET /device-preview` is a self-contained HTML virtual device (no build step) that polls the snapshot, renders the all-runtime metrics plus a health LED, and shows Approve/Deny when an approval is pending.
- **Verified:** real server boot returned live data through the daemon proxy (cost, tokens, a firing alert, health amber); /device-preview rendered. `tests/test_device_snapshot.py` covers the empty-store valid-zero payload, active-session counting, and oldest-pending-approval surfacing plus amber health.

### Release: OTLP /v1/logs receiver — ingest Claude Code / Codex OTel event stream (#2596) (2026-06-04)
- **Why:** the OTLP receiver had /v1/metrics + /v1/traces but no /v1/logs. Claude Code (and Codex) export their per-turn EVENT stream as OTel *logs* (event_name like `claude_code.api_request` with cost/token/model attributes), so OTel-configured installs gave signal we dropped. Surfaced by the harness-observability audit.
- **What:** add `POST /v1/logs` (mirrors /v1/traces; 501 without the `clawmetry[otel]` extra) + `_process_otlp_logs`, which maps any OTLP LogRecord carrying cost/token/duration attributes into the cost / tokens / runs metric tiles. Point an agent at it with `OTEL_LOGS_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://localhost:8900`.
- **Test:** `tests/test_otlp_logs.py` builds a synthetic ExportLogsServiceRequest and asserts a claude_code.api_request lands in cost+tokens+runs; a non-cost event is ignored.

### Release: Context economics filters per-runtime (snapshot byRuntime slice) (2026-06-03)
- **Why:** like Tool catalog, the Context-economics tab showed the all-runtimes aggregate on every runtime tab (founder report). Compactions from every runtime were lumped together.
- **What:** the contextEconomics snapshot slice now carries `byRuntime` (runtime -> {compactions, overflow_sessions, summary}) via `_context_econ_by_runtime`, grouped by each compaction's session_id prefix. The cloud interceptor serves the selected runtime's view (empty for a runtime that never compacted). Removed context-economics from `_CM_RT_AGGREGATE` so its 'not yet filtered' banner no longer shows.
- **Guard:** `tests/test_context_econ_per_runtime.py` (per-runtime split + reconciliation).

### Release: Tool catalog filters per-runtime (snapshot byRuntime slice) (2026-06-03)
- **Why:** selecting opencode/codex on the node page showed Claude Code's tools (Bash/Read/Edit/chrome-devtools) — the all-runtimes aggregate (founder report). The Tool-catalog snapshot slice was a single aggregate.
- **What:** `_build_tool_catalog_slice` now also emits `byRuntime` (runtime -> {tools, groups, totals}), derived from each tool_call event's session_id prefix. The cloud interceptor serves the selected runtime's catalog (empty for a runtime that never invoked a tool). Verified on a real node: claude_code 26 tools / 1425 calls, opencode/codex absent (correctly empty). Removed tool-catalog from `_CM_RT_AGGREGATE` so its 'not yet filtered' banner no longer shows.
- **Guard:** `tests/test_tool_catalog_per_runtime.py` (per-runtime split + sum reconciles to the aggregate).

### Release: Fleet shows only runtimes with REAL sessions (drop 0-session phantoms) (2026-06-03)
- **Why:** the Fleet rendered a "Cursor — detected here / appears shortly / Syncing…" card that never resolved. The lite detector flags a runtime from directory/config presence alone — the Cursor *IDE* being installed makes `~/Library/Application Support/Cursor` exist even when the Cursor *agent* was never used — so the daemon reported it with `sessions=0` and the cloud showed a stuck phantom (founder report).
- **What:** `_detect_runtimes_for_heartbeat()` now drops any runtime with 0 sessions. "Installed & running" for observability means there is real data; a runtime with zero sessions isn't advertised until it produces one. Verified on the founder's machine: Cursor (0) dropped; Claude Code/Codex/Qwen/Goose/opencode/Hermes/PicoClaw (all >0, all real) kept.
- **Guard:** `tests/test_detected_runtimes_no_phantom.py` asserts 0-session runtimes never leak.

### Release: per-runtime sidebars derive from DECLARED capabilities (#2575) (2026-06-03)
- **Why:** the first pass (#2571/#2572) hid tabs from a hand-written list that an LLM helper had hallucinated parts of (NemoClaw mislabeled a "NeMo toolkit"; Hermes/Cursor/NanoClaw credited with crons/memory/skills they don't have). Founder caught it — "should I even trust you?".
- **What:** tab visibility now derives mechanically from each adapter's declared `Capability` enum (`_CM_RT_CAPS` → `_CM_CAP_TABS`), not prose. OpenClaw + NemoClaw (sandboxed OpenClaw, identical caps) show the full set; cost runtimes (Claude Code, Codex, Aider, Goose, opencode, Qwen) show Sessions/Events/Cost tabs; Cursor/PicoClaw/NanoClaw (no COST) show less. A CI parity guard (`test_runtime_tab_capability_parity.py`) re-extracts the contract and fails on drift, so this can't silently rot again.
- **Verified:** node --check clean; parity test green; closed-source pro adapters guarded by the parallel test in clawmetry-pro.

### hide OpenClaw-only tabs for non-OpenClaw runtimes (carries #2571) (2026-06-03)
- **Why:** selecting a non-OpenClaw runtime (Claude Code, Codex, …) and opening Memory/Skills/Self-Evolve/Crons/Tool-Policy/NeMo showed OpenClaw's data under a "this view is node-wide" banner — irrelevant tabs that just add cognitive load (founder feedback).
- **What:** those six OpenClaw-only sidebar tabs are now HIDDEN when a non-OpenClaw runtime is selected; OpenClaw + NemoClaw (and "all runtimes") still show everything. On a now-hidden tab, the view falls back to Overview. Applied on load (pinned ?runtime=) and on every runtime switch.
- **Verified:** node --check clean; per-runtime hide logic unit-checked.


### Release: on-demand runtime backfill — daemon capability (carries #2568) (2026-06-03)
- **Why:** family runtimes default-sync the most-recent 50 sessions (cost/payload bound), but the local DuckDB can hold all history. The user should be able to dig back as far as they want on demand (founder 2026-06-03).
- **What:** a `runtime_backfill` pending action raises ONE runtime's ingest depth (`_effective_family_limit` = max(default-50, on-demand override), capped 5000); the next `sync_family_runtimes` pass pulls the older sessions into DuckDB and uploads them. The cloud Fleet card's "sync N older" affordance triggers it (clawmetry-cloud #1361).
- **Verified:** 7 new unit tests (default, per-runtime isolation, monotonic, step-up, cap, allowlist, bad-input); full OSS CI matrix.


### Release: scoped Overview shows the runtime's footprint, not an empty today-window (carries #2565) (2026-06-03)
- **Why:** selecting a runtime whose sessions are older than today (e.g. OpenClaw, 2 sessions from 2 days ago) made the Overview show "0 sessions today" while the switcher said "OpenClaw · 2 sessions" — it read as "sessions gone." Not a data bug (verified via v1 usage day=0 / month=2).
- **What:** when a runtime is selected, the Overview shows that runtime's FOOTPRINT matching the switcher — SESSIONS = the switcher's per-runtime total, the tile label flips "Sessions today" -> "Sessions", the hero drops the "today" suffix, and cost/tokens use the month figure. Node-wide ('all') keeps the live "today" framing.
- **Verified:** node --check clean; hero-wording logic unit-checked (scoped "2 sessions"; all "68 sessions today").


### Release: Overview SPENDING wk/mo scope to selected runtime (carries #2562) (2026-06-03)
- **What:** completes the node-detail Overview runtime scoping (follows #2558). The SPENDING card's wk/mo sub-figures now scope to the selected runtime via a v1 usage `period=week|month` fetch (local-mode fallback uses the runtime-summary slice); `runtime=all` keeps node-wide. The whole Overview screen (sessions / tokens / cost / model / spending) now reflects only the selected runtime.
- **Verified:** v1 `period=week` live (claude_code 52.9M tokens / $0 OAuth); node --check clean.


### Release: Overview cards scope to the selected runtime (carries #2558) (2026-06-03)
- **Why:** with a runtime selected, the node-detail Overview stat cards + hero showed NODE-WIDE numbers (e.g. 68 sessions / 3.8M tokens / claude-opus-4-8 while "PicoClaw" was selected). Only the switcher label changed, not the data (the FLYWHEEL runtime-filter rule, §1c).
- **What:** `loadMiniWidgets` now scopes sessions / tokens / cost / model to the selected runtime. Cloud mode sources the period-accurate numbers from the public v1 API (`/api/v1/usage?runtime=&period=day|month`, server-side filtered); local mode falls back to the `/api/runtime-summary` per-runtime slice. `_renderOverviewHero` reads the scope so the headline mirrors the cards. `runtime=all` keeps the node-wide path unchanged.
- **Verified:** live v1 data — PicoClaw -> 0 sessions / 0 tokens; Claude Code -> 2 sessions / 490K today / 82M month. Auth rides the cm_token cookie the cloud page already sets. node --check clean.


### Release: per-runtime Fleet tabs + pip-less pro provisioning (carries #2548, #2551) + release-flake fix (2026-06-03)
- **Per-runtime tabs:** the global runtime filter now honours a tab-local `?runtime=<id>` URL param (overrides the shared `localStorage` key). This lets the cloud Fleet open each synced runtime in its own browser tab — Claude Code in one, Codex in another — each independent. `_cmRuntimeFilter()` prefers the URL pin; `_cmSetRuntimeFilter()` updates the URL (not localStorage) in a pinned tab. (#2551)
- **Pip-less pro provisioning:** the daemon venv (`~/.clawmetry/bin/python3`) often has no `pip`, so `auto_provision_pro` failed forever with `No module named pip` and paid runtimes never installed on entitled accounts. The installer now does `pip → ensurepip → unzip the (pure-Python --no-deps) wheel into site-packages`, so it always succeeds. Also fixed the wrong `clawmetry status` hint (it suggested `pip install clawmetry-pro`, which is closed-source + needs no pip). (#2548)
- **Release-flake fix:** a third-party DoubleClick/Google-Ads pixel returning 400 false-failed the cloud-contract release gate (`zero unexpected JS errors`). Added ad/measurement domains to `isHarmlessConsoleError` so third-party beacons we don't control can't block a publish.
- **Verified:** OSS CI matrix green; pip-less install proven live on a real pip-less daemon venv (synced 10 runtimes / 45945 events to the Fleet); 7 URL-pin assertions + 3 install-fallback unit tests.


### Release: provision clawmetry-pro into pip-less daemon venvs (carries #2548) (2026-06-03)
- **Why:** the cloud sync daemon runs from `~/.clawmetry/bin/python3`, a venv that on many installs has no `pip` (sometimes no `ensurepip`). `auto_provision_pro` shelled to `python -m pip install <wheel>` and failed every cycle with `No module named pip` — so on entitled (Trial/Pro) accounts the paid runtime adapters (Claude Code, Codex, Cursor, Aider, Goose, opencode, Qwen, …) downloaded but never installed and stayed locked in the Fleet despite a valid entitlement.
- **What:** `clawmetry-pro` is a pure-Python `--no-deps` wheel (a zip), so the installer is now resilient: `pip install → ensurepip+retry → unzip wheel into site-packages`. The unzip fallback writes the `.dist-info` so both `import` and `importlib.metadata.version` resolve it on the daemon's next start. Also fixed the `clawmetry status` hint that wrongly suggested `pip install clawmetry-pro` (closed-source, served via `/api/license/download`, not PyPI).
- **Verified:** 3 new unit tests (unzip extracts importably, pip-missing falls back to unzip, pip-present never falls back), 26 pass. Verified live on a real pip-less daemon venv: after install + graceful restart the node synced Claude Code/Codex/Cursor/Goose/opencode/Qwen/Hermes/Nano/Pico (45945 events) to the cloud Fleet.


### Release: named source for out-loop / production agents (carries #2497) (2026-06-02)
- **Why:** `import clawmetry.track` already auto-tracks any Python agent's LLM calls (it patches httpx/requests, so OpenAI Agents SDK / LangChain / Vercel AI SDK / E2B all flow through), but they showed up as anonymous scripts. The first step toward out-loop SDK products as a first-class source class (the biggest TAM gap).
- **What:** `clawmetry.track.set_source("my-agent")` + a `CLAWMETRY_SOURCE` env var tag every intercepted LLM call with a name, so a production agent becomes a first-class source you can attribute cost to per product. Each `llm_call` event now carries a `source` field.
- **Verified:** 4 new unit tests (set_source, env fallback, default, bounded); full OSS CI matrix green.


### Release: live ⚡ tok/s in the Overview hero (carries #2494) (2026-06-02)
- **What:** the web Overview hero now shows live tokens/sec while the agent is producing — matching `clawmetry status --live`. Computed from the today-token delta between renders (a raw token total is stashed alongside the formatted one). Frontend-only; reaches cloud via the pinned wheel.
- **Verified:** node --check clean; full OSS CI matrix green.


### Release: `clawmetry status --live` — in-terminal live status bar (carries #2491) (2026-06-02)
- **Why:** Pi-parity for the terminal-native crowd — see what your agent is doing + what it's costing without leaving the shell.
- **What:** a refreshing one-line terminal status (sessions · tokens · cost · running model · live tokens/sec), read from the daemon's local store via the read-only proxy (falls back to a direct read when no daemon). Live TPS is the total-token delta over wall time. `_status_live_line()` is a pure, unit-tested helper.
- **Verified:** 3 new unit tests (aggregation, TPS from delta, empty-safe); full OSS CI matrix green.


### Release: context graph — error->cause edge (carries #2488) (2026-06-02)
- **What:** query_session_errors(session_id) + GET /api/session-errors/<id> return a session's failed spans, each with its parent span (the upstream decision one hop away) — the error->cause edge that completes the graph's core edge set (session->tool, parent->subagent, decision->approval/guardrail, cost->decision, error->cause). OTel-only; the per-session tool-failure rate covers the non-OTel case.
- **Verified:** 1 new unit test (failed spans only, with parent; empty-safe); full OSS CI matrix green.


### Release: 'Start here' — the #1 fix on the Recoverable-spend card (carries #2485) (2026-06-02)
- **What:** the Overview Recoverable-spend card now surfaces the single highest-leverage fix as a green "Start here:" line, picked from the waste-summary fields (reasoning $ share / failing tools / low cache / compaction). Computed in the frontend so it works identically in cloud + self-hosted with no backend.
- **Verified:** node --check clean; full OSS CI matrix green.


### Release: actionable recommendations on the decision insight (carries #2483) (2026-06-02)
- **What:** /api/session-insight now turns each waste flag into advice — what to DO, not just what happened (reasoning-heavy -> lower effort/cheaper model; cache-poor -> warm the cache; tools-failing -> fix the tool; compaction -> smaller context; model-fallback -> pin the model; fanned-out -> true cost incl children; policy-denied -> review). Returns a `recommendations` list; a guard test asserts every flag the insight can emit has advice.
- **Verified:** py_compile clean; insight + recommendations unit tests green; full OSS CI matrix green.


### Release: /api/session-insight is now the complete per-session context-graph answer (carries #2479) (2026-06-02)
- **What:** the session-insight endpoint now folds in the governance lineage, so one call returns cost + waste flags + sub-agent fan-out + governance (approval/guardrail decision + denied counts, with a `policy_denied` flag when blocked) — the single endpoint that will power the decision-insight card.
- **Verified:** py_compile clean; insight unit tests green; full OSS CI matrix green.


### Release: context graph — governance lineage edge + per-session 🛡 chip (carries #2476, #2477) (2026-06-02)
- **Why:** the decision->approval / decision->guardrail edge — which tool calls a session put through governance, and how they were decided — is core to a context graph and was unrendered.
- **What:** `_session_governance()` + `GET /api/session-governance/<id>` join the approval queue (by requestor_session_id) with NeMo guardrail verdicts (by session_id) into a session's policy lineage with a denied-count; cost-breakdown aggregates the same per session; the session chip renders 🛡 N gated · M denied (green / red if denied) next to the cost-intel + fan-out chips.
- **Verified:** 2 new unit tests (join + denied-count; empty-safe); py_compile + node --check clean; full OSS CI matrix green.


### Release: Overview 'Recoverable spend' card — the cost-intel cluster's glanceable payoff (carries #2472) (2026-06-02)
- **Why:** the per-session chips + the /api/waste-summary roll-up deserve a glanceable home — the one card that answers "where is my agent bill going to waste?"
- **What:** a "Recoverable spend" card under the Overview hero rendering the fleet waste roll-up (reasoning tax $, low-cache / tool-failing / compaction-heavy / model-fallback session counts, "N of M recent sessions show a waste signal") with a link to the productivity-gains blog post. Hidden entirely when nothing is flagged (honest empty state). Caps the cost-intelligence cluster shipped today (💰🧠⚡🔀⚠♻↳) + the context-graph lineage/insight.
- **Verified:** node --check clean; full OSS CI matrix green. Frontend-only; reaches a node when its daemon upgrades to this wheel (and the cloud via the pinned wheel).


### Release: fleet 'recoverable spend' waste summary (carries #2469) (2026-06-02)
- **Why:** the productivity-gains framework (today's blog post) deserves to be a live number, not just prose — aggregate the per-session cost-intel into where the bill is actually going to waste.
- **What:** `_derive_waste_summary()` + `GET /api/waste-summary` roll up reasoning tax ($ sum), low-cache / tool-failing / compaction-heavy / model-fallback session counts, and the flagged-session total across recent sessions. Deliberately no fabricated single "you saved $X" headline (mirrors the blog's honesty); the operator drills into the flagged sessions via the per-session chips.
- **Verified:** 2 new unit tests (aggregation correctness + empty-safe); full OSS CI matrix green (the MOAT perf-benchmark flake on the untouched gateway_health endpoint cleared on rerun).


### Release: context graph — unified session insight + the true-cost fan-out chip (carries #2466, #2467) (2026-06-02)
- **Why:** the lineage traversal needs to become an answer a user sees — "what did this ask really cost, and where did it waste?"
- **What:** (1) `_derive_session_insight()` + `GET /api/session-insight/<id>` join the cost-intel cluster with the lineage into one answer no flat tab gives — the TRUE cost of an ask (own + sub-agent fan-out) + the waste flags that fired (reasoning_heavy / cache_poor / tools_failing / compaction_thrash / model_fallback / fanned_out). (2) The first VISIBLE context-graph signal in the session list: `query_subagent_cost_rollup()` rolls up each parent's sub-agent spend in one GROUP BY; the session chip renders `↳ +$X · N agents` (the real cost of an ask incl. its fan-out) next to the cost-intel chips.
- **Verified:** 4 new unit tests (insight all-flags/true-cost/clean/empty; rollup GROUP BY); py_compile + node --check clean; full OSS CI matrix green.


### Release: context graph — session decision-lineage traversal, the first view (carries #2463) (2026-06-02)
- **Why:** the cost-intelligence cluster shipped today is the rich per-session signal a temporal decision graph needs; this is the first materialized projection of it (founder direction).
- **What:** `query_session_lineage(session_id)` walks the parent->subagent edges (`subagents.parent_session_id` -> `subagent_id`) with a DuckDB `WITH RECURSIVE` CTE and returns every node in the fan-out with depth + cost + outcome — one ask's full delegation tree and the cost each branch incurred downstream, one round-trip. No new tables (edges are JOINs over existing rows). Exposed at `GET /api/session-lineage/<id>` with a root/downstream/total cost rollup; added to the daemon allowlist.
- **Verified:** 2 new unit tests exercising the real DuckDB recursive CTE (tree depth + downstream cost rollup; root-only/empty); full OSS CI matrix green.


### Release: per-session compaction-count chip — completes the cost-intel cluster (carries #2460) (2026-06-02)
- **Why:** each auto-compaction silently re-summarises (and re-bills) the context window; a session that compacted many times is thrashing its context — wasted tokens you never see.
- **What:** counts compaction events from the events already fetched once per family session, stashes `compactionCount` onto the metadata + cloud rows; `/api/sessions/cost-breakdown` surfaces it; the chip renders ♻ compacted N× next to 💰/🧠/⚡/🔀/⚠. This completes the per-session cost-intelligence chip cluster: 💰 total · 🧠 reasoning · ⚡ cache · 🔀 model-fallback · ⚠ tools-failing · ♻ compactions.
- **Verified:** py_compile + node --check clean; cost-intel unit tests green; full OSS CI matrix green.


### Release: per-session tool failure-rate chip (carries #2456) (2026-06-02)
- **Why:** a tool that keeps erroring (browser 40%, a flaky MCP) is invisible — the user just sees the agent "thinking" while tokens burn on retries.
- **What:** `_session_tool_health(events)` counts tool-result events + the share that came back a REAL (non-benign) error (reuses `error_signal`'s benign filter so it's actionable, not alarmist); the family ingest fetches events once (transcript loop reuses them) and stashes `toolErrorPct` onto the session metadata + cloud rows; `/api/sessions/cost-breakdown` surfaces it; the chip renders ⚠ N% tools failing (amber, red >=30%) next to 💰/🧠/⚡/🔀.
- **Verified:** 3 new unit tests (real errors counted, empty when no tools, clean=0%); py_compile + node --check clean; full OSS CI matrix green.


### Release: silent model-fallback flag + cache-% chip for OpenClaw/Claude Code (carries #2454) (2026-06-02)
- **Why:** a session that silently ran on >1 model (a fallback/downgrade no CLI surfaces) is a cost+quality signal; and the cache-hit % chip from the foundation should also light up for the event-usage runtimes.
- **What:** `query_cost_split` now returns `model_count` + `secondary_model` per session; `/api/sessions/cost-breakdown` grafts `cache_hit_pct` for OpenClaw/Claude Code (family runtimes get it from the metadata foundation) and sets a `model_mix` flag when >1 model; the session chip renders 🔀 model fallback (amber, models in the tooltip) next to 💰/🧠/⚡.
- **Verified:** extended `test_local_store` cost-split test (model_count + secondary); py_compile + node --check clean; full OSS CI matrix green.


### Release: cost-intelligence foundation — reasoning-tax $ + cache-hit % per session (carries #2450) (2026-06-02)
- **Why:** the next "where did my money go" gems (reasoning-tax, cache-efficiency, model-mix) had no queryable data — the per-session token split (input/output/cache/reasoning) was dropped at event ingest and the sessions table never stored it.
- **What:** `_session_cost_intel(s)` stashes the token split + derives reasoning-tax $ (reasoning billed at the OUTPUT rate via OSS pricing) + cache-hit % onto the session metadata at family ingest (and the cloud session rows); `/api/sessions/cost-breakdown` grafts those onto each row; the session chip renders 🧠 $X reasoning + ⚡ N% cache (color-coded) next to 💰 total, shown only for runtimes whose adapter reports the field (reasoning: codex/qwen/opencode/hermes/nemo; cache: those + claude_code). Also the data layer the context graph needs.
- **Verified:** 5 new unit tests (cloud reasoning>0 + cache%; local reasoning=real $0; no-model omits reasoning; never-raises); py_compile + node --check clean; full OSS CI matrix green. Daemon-side + frontend (reaches cloud via the pinned wheel); local chip path is wired + tested, the cloud chip reads the carried snapshot fields.


### Release: real $ cost for every paid runtime — the #1 gem (carries #2446 + clawmetry-pro 0.3.1) (2026-06-02)
- **Why:** the headline reason to pay. codex / goose / qwen_code / aider / claude_code all extract real token splits + a model id but the source CLIs never persist a USD figure, so the Cost tab showed **nothing** for 5 of the paid runtimes despite having everything needed to price them. (OpenClaw/Claude-Code already derived cost via `estimate_event_cost_usd`; the family runtimes were dark.)
- **What:** (1) **closed `clawmetry-pro` 0.3.1** (shipped to the licensed/auto-provisioned wheel download): a new `clawmetry_pro/lib/cost.py::derive_cost_usd` wraps the OSS cache-aware pricing path (resolves provider from model, applies Anthropic cache multipliers, returns a **real `0.0`** for local/self-hosted models — you pay for hardware, not per token — and `None` only when genuinely unpriceable), and each of the 5 adapters now derives `cost_usd` (`cost_status='derived'`). (2) **OSS #2446:** the family ingest already carried the derived per-session cost onto the session row; this spreads that cost across the session's events in proportion to each event's `token_count`, so the **event-based Cost-tab total** sums to the true session cost instead of `$0` (last-event fallback when no token split).
- **Verified:** clawmetry-pro suite 175 passed (new `test_cost.py` + 5 adapter tests updated from the old "local = unknown/None" contract to "local = real $0.00"); per-runtime conformance CI green for all 11 runtimes; the distribution sums exactly to the session cost; full OSS CI matrix green. Daemon-side; a node shows real cost once it runs this OSS wheel **and** has the pro 0.3.1 wheel (licensed / auto-provisioned).

### Release: GitHub/Google browser sign-in for `clawmetry connect` + NemoClaw governance snapshot slice (carries #2442, #2443) (2026-06-02)
- **Why:** the web `clawmetry.com/connect` page already had GitHub/Google OAuth, but the **terminal** `clawmetry connect` was email+OTP only — the founder wanted social sign-in for linking a node too. Separately, the cloud `cm-cloud-nemoclaw` governance interceptor had no daemon data to serve, so paid users saw a `{installed:false}` placeholder.
- **What:** (1) `clawmetry connect` now offers **GitHub/Google browser sign-in** alongside email+OTP. A new `_oauth_browser_login(provider)` spins up a one-shot **loopback** server on `127.0.0.1:0`, opens the cloud OAuth flow with `cli_port=<our port>`, and captures the `cm_` key the callback redirects back to loopback (same pattern as `gh`/`gcloud`); it falls back to email OTP on timeout/failure, and the key only ever travels over loopback. The prompt now leads with `[1] GitHub  [2] Google`, or type your email for a code (the `cm_` paste and email-OTP paths are unchanged). Pairs with the cloud `oauth_start`/`oauth_callback` `cli_port` support (cookie-pinned state, integer-port-only loopback redirect, no open-redirect). (2) The sync daemon now emits a `governance` snapshot slice (`_build_governance()`) so the cloud governance tab renders real NemoClaw governance for paid users instead of the `{installed:false}` fallback — honest by construction (only fields `_detect_nemoclaw()` actually observes; `policy`/`network_policies`/`presets` left empty rather than fabricated).
- **Verified:** `py_compile` clean on `cli.py` + `sync.py`; the CLI loopback capture is unit-tested (captures a `cm_` token, rejects a non-`cm_` one → email fallback); the cloud `cli_port` round-trip is live-verified (`?cli_port=55555` → `state=cli.55555.<nonce>`; privileged port 80 rejected). The governance slice returns `{installed:false}` on a no-NemoClaw host and is non-regressive (absent == prior behaviour); the rich NemoClaw-present path is not E2E-verified (no NemoClaw install available). Daemon + CLI change; reaches a node when its daemon upgrades to this wheel.

### Release: pro auto-provisioning on `clawmetry connect` + NeMo governance now closed-source (carries #2437, #2436) (2026-06-01)
- **Why:** two halves of the open-core boundary. (1) A paying cloud account's daemon never actually pulled the closed `clawmetry-pro` wheel, so the 10 paid runtimes showed "unlocked" in the UI but had **no data** — the daemon was never observing them. (2) The NeMo governance layer shipped in public OSS, so any self-hoster could run the enterprise governance surface for free and never pay. Both undercut the model where you pay to observe *more runtimes* and to *govern* a fleet.
- **What:** (1) `clawmetry connect` now **auto-provisions** `clawmetry-pro` for entitled cloud accounts: it asks the cloud (`GET /api/license/entitlement`) whether the `cm_` account is entitled and, only for an entitled plan (Starter/Pro/Trial/Enterprise), downloads + installs the closed wheel from our HTTPS `/api/license/download`. A **free or unknown account installs nothing**; a failed download **never crashes or blocks** `connect` (the node simply stays on the free runtimes, OpenClaw + NemoClaw); the install is idempotent and only ever fetches a wheel from our own HTTPS endpoint (a literal-localhost override exists for tests only). The self-hosted `clawmetry activate <KEY>` signed-license path is hardened to actually download + install the scoped wheel too. (2) The OSS NeMo governance routes (`/api/nemoclaw/*`) are now a **402 `upgrade_required` stub**; the real governance implementation (`bp_nemoclaw`, 12 routes) moved into closed-source `clawmetry-pro` (0.3.0) and only registers when the licensed wheel is installed. Licensed self-hosters get real governance via the downloaded wheel; unlicensed self-hosters get the honest 402.
- **Verified:** cloud `/api/license/entitlement` live and **fail-closed** (an unknown `cm_` key resolves to `{"entitled":false,"plan":"free"}`, so a daemon installs nothing); cloud `/api/license/download` returns 402 for a free account and a test asserts the wheel is never served to it; OSS 8 new license tests (free=no-install, entitled=download+install, install-failure-never-raises, refuses-non-https); the rebuilt `clawmetry-pro` 0.3.0 wheel registers the `nemoclaw` blueprint + all 12 governance routes from a clean install (pro suite 168 passed). The cloud server itself is unchanged here — it still runs the pinned OSS wheel and serves governance to existing cloud users as before; the cloud-pin bump + a `cm-cloud-nemoclaw` snapshot interceptor are a separate, later step so no paying cloud user is downgraded.

### Release: Swimlane compare view + runtime-neutral copy (carries #2433, #2432) (2026-06-01)
- **Why:** founder research into Pi Observability surfaced one feature we lacked: a side-by-side, live multi-agent comparison. Our edge over single-agent trace tools is that we can put RUNTIMES and fleet NODES in lanes, not just one agent's variants. Also: ClawMetry supports 12 runtimes, but some dashboard copy still framed it as OpenClaw-only.
- **What:** (1) A new **Swimlane Compare** tab: pick up to 4 sessions, or one-click "compare 1 per runtime", and see each as a parallel live lane with a header (model, cost, in/out tokens, context %) and a dense event stream (turns, thinking, tool calls/results) reusing the existing transcript-events/sessions/usage endpoints (no new backend). Single and Swimlane modes are real; Race is an initial cost/latency ordering (full turn-by-turn race, SSE live tail, per-turn token deltas, and an event inspector are the next iteration). Respects the active-tab-only polling rule and the global runtime switcher. (2) Runtime-neutral copy: the compactions empty-state and context-economics description no longer say "OpenClaw" where any of the 12 runtimes applies.
- **Verified:** full OSS CI matrix green (API tests 3 OS, sync matrix 3 OS x 3 Py, Live OpenClaw E2E, OSS golden path, MOAT, eval gate, pip install macOS/Linux/Windows); node --check on app.js clean; new tab wired into the live (second) DASHBOARD_HTML block, not the dead inline HTML. Frontend-only; reaches the cloud via the pinned wheel.

### Release: clawmetry connect starts sync by default (carries #2428) (2026-06-01)
- **Why:** the founder hit this live. Running `clawmetry connect` left the cloud dashboard empty because the previous default deferred the sync daemon (it printed "Sync is paused" and never started it), so the node never heartbeated and "0 nodes" persisted. A user who connects wants their observability now, not after discovering a separate `clawmetry sync` step.
- **What:** `clawmetry connect` now starts the sync daemon by default. A new `--defer-sync` flag keeps the old paused behavior (for provisioning a node you do not want syncing yet); `--start-sync-now` is retained as a no-op alias (it is now the default) so existing scripts and the cloud dashboard's copy of the connect command keep working. The server-side deferred-sync gate for auto-provisioned (KiloClaw) nodes is unchanged, so the cost and privacy reason the deferral existed is unaffected.
- **Verified:** py_compile + ast.parse clean; full OSS CI green (API tests + sync matrix on 3 OS, pip install on macOS/Linux/Windows, MOAT, eval gate, golden path). CLI-behavior change, verify with a live run: `clawmetry connect` starts sync, `clawmetry connect --defer-sync` stays paused.

### Fixed: make every number true - context-window 1M, sessions/reliability/flow-actions no longer blank or contradictory, Brain stops leaking raw objects (2026-06-01)
- **Why:** the founder found the dashboard contradicting itself - the Overview hero said "2 sessions today" while the SESSIONS stat card showed 0; RELIABILITY sat on a permanent "--"; the Flow MESSAGES/MIN, ACTIONS TAKEN, ACTIVE TOOLS read 0 right after a real tool-using turn; the LLM Context Inspector showed a 200K window (26% used) while OpenClaw correctly showed 1M (5%); and the Brain feed dumped raw `[object Object]` and giant `<task-notification>` blobs. Each made the product look untrustworthy. The theme of this fix: every number must be real, labeled, and backfilled from DuckDB, never live-only-and-blank, and two cards must never silently disagree.
- **What:** (1) Context window: `context_window_for_model` now treats the `claude-opus-4-8` family as a 1M-context model by default (OpenClaw records it without the `[1m]` marker ClawMetry keyed on), so the gauge reads against 1M like OpenClaw does; older models stay at their correct defaults. (2) Overview SESSIONS card now reads `sessionCount` (sessions today, synchronously, never blank) and is relabeled "Sessions today" so it matches the hero instead of showing the active-list length. (3) Reliability: implemented the `loadReliabilityCard()` function that was called but never defined (so the card was stuck on "--"); it now shows a real direction/score when data exists and an honest "No data yet" otherwise, never a dangling dash. (4) Flow ACTIONS TAKEN now backfills from the DuckDB-backed gateway message count on load instead of reading 0 until a live event arrives; MESSAGES/MIN and ACTIVE TOOLS stay live-driven (0 is the honest value for an idle agent and is not faked). (5) Brain feed no longer renders `[object Object]` (array/object content is coerced to readable text) or raw `<task-notification>` envelopes (collapsed to a compact summary + status), on both the live client path and the server `routes/brain.py` extractor.
- **Verified:** live against the running OpenClaw 2026.5.28 gateway - `context_window_for_model("claude-opus-4-8", 52600)` returns 1000000 (sonnet/opus-4-7 stay 200000); `/api/reliability` returns valid JSON so the card renders "No data yet" on a fresh node; gateway `today_messages` is a real positive number feeding ACTIONS TAKEN; `/api/brain-history` shows 0 raw blobs and 0 `[object Object]` after the fix. Frontend + read-path; reaches the cloud via the pinned wheel (the 1M window also needs the node daemon to restart, since it serves that value from its own process).


### Fixed: Gateway node + WebChat now populate from OpenClaw 2026.5.28's structured-JSON gateway log (2026-06-01)
- **Why:** continued from the real end-to-end gateway test. After the protocol-4 fix, the Gateway node still showed empty routes/stats and WebChat never appeared in Flow. Two causes: (1) OpenClaw 2026.5.28 leaves a 0-byte `~/.openclaw/logs/gateway.log` stub and writes the real log as structured JSON to `/tmp/openclaw/openclaw-<date>.log`, but the log-path resolver preferred the legacy file whenever it merely existed (returning the empty stub), and the component parser only understood the old plaintext format; (2) `/api/channels` read the hardcoded (now-empty) legacy path, so it never saw the `webchat connected` line.
- **What:** (1) the gateway-log resolver now requires the legacy file to be non-empty before preferring it, else falls through to the newest `/tmp/openclaw/openclaw-*.log`; (2) the Gateway-component parser gained a structured-JSON branch that reconstructs each JSON line's `time` + subsystem-tag + `message` into the legacy `TS [tag] body` shape and reuses the existing categorization (messages / heartbeats / crons / errors); (3) `/api/channels` now uses the same resolver so WebChat is detected from the live log.
- **Verified:** live against the running OpenClaw 2026.5.28 gateway, the Gateway component now reports today_messages 225 (was 0) and `/api/channels` returns `["tui", "webchat"]` (was `["tui"]`), so WebChat renders in the Flow diagram. Request-handler file read (matches the existing pattern); defensive against missing/short/malformed lines.


### Fixed: live gateway tap speaks protocol 4 + Flow no longer mislabels CLI turns as Telegram (2026-06-01)
- **Why:** surfaced by a real end-to-end test (a real WebChat message sent through the live OpenClaw 2026.5.28 gateway). Three real bugs were blocking the Flow tab's Gateway/WebChat data: (1) ClawMetry's live gateway WebSocket tap hardcoded protocol 3, but OpenClaw 2026.5.28's gateway now requires protocol 4, so every tap connection was rejected with `protocol-mismatch` and no live channel data ever arrived; (2) the tap refused to connect to a gateway running `auth.mode=none` (it raised on a missing token before even trying); (3) Flow attributed an unknown-sender message to `telegram` and labeled the reply leg with the model provider name (`claude-cli`) instead of the message's real channel, so a plain local agent turn showed up as a Telegram conversation.
- **What:** (1) the tap now negotiates protocol range 3..4 (`maxProtocol: 4`); (2) it connects to no-auth gateways (sends the `auth` field only when a token exists); (3) the flow-events channel attribution drops the `telegram` guess in favor of a neutral `openclaw` for unknown senders, stops treating a provider name as a channel, and makes the reply leg carry the same channel as that session's inbound turn; (4) the gateway-log path is resolved robustly (prefers `~/.openclaw/logs/gateway.log`, else the newest `/tmp/openclaw/openclaw-*.log` that OpenClaw 2026.5.28 actually writes).
- **Verified:** live handshake against the running local gateway confirms the protocol-mismatch is gone (the gateway now accepts protocol 4 and advances past the version check); the flow-events channel for a real local turn now reads `openclaw`, not `telegram`. Daemon-side change reaches a node when its daemon upgrades to this wheel.


### Release: Flow redesign - newcomer-legible journey rail + live trace-accurate packet view (carries #2394) (2026-05-31)
- **Why:** Flow is the product's flagship, most-advertised screen, but it read as an engineering topology - tangled crossing connectors, no plain-language story, every node glowing whether or not it had fired. For someone who has never used an observability tool (the FLYWHEEL vision), it did not answer the one question they have: how does my message get answered, and what is my agent doing right now.
- **What:** (1) A "How your messages get answered" journey rail headline (You -> Channels -> Gateway -> Brain -> Tools -> reply) with live per-stage sub-stats and a single travelling signal dot - the five-second story. (2) De-spaghetti: removed the four connector paths that cut diagonally across the canvas to the infrastructure row; infrastructure is now a calm base with one tidy vertical "runs on" link, plus a faint reply loop routed low/left so it never crosses the tool fan-out. (3) Active-vs-available: channels and tools are dim by default ("available") and only light + glow when actually invoked, so "what is firing now" pops. (4) Live, event-driven packet: a warm-accent dot now travels the REAL connector that just fired (inbound: You->channel->gateway->brain; tool: brain->tool; reply: brain->reply), and the rail's active station tracks the live stage with a 4s idle-decay back to the Brain resting state - all wired into the existing SSE handlers, no new endpoints. Unmapped tool types pulse the neutral skills edge rather than falsely lighting "Exec"; the live tool-call feed keeps the exact per-call truth. (5) Bug fixes: the Active Tools stat no longer renders the banned em-dash entity (shows a count), and the Tokens stat no longer renders "0K" (shows 0 / NK / N.NM).
- **Verified:** live against real local data (worktree dashboard) - rail renders, packet dots travel the correct edges, rail stages light, token shows a real number, and the reply curve's bounding box was checked programmatically to stay left of the tool column and above the infrastructure line. node --check, en.json valid, test_i18n_no_raw_codes 69 passed, every node/path id preserved. Frontend-only; reaches the cloud via the pinned wheel. Flow stays a live "what is firing now" view; per-turn replay is reserved for the Tracing screen.

### Release: human-first Overview hero - lead with the story, demote power tools (carries #2391) (2026-05-31)
- **Why:** the new FLYWHEEL vision is observability for people who've never used one. The Overview was inverted for that person: it opened with power-user tools (Compare Runs / Error Triage, each asking you to paste a session or event ID a first-timer doesn't have) and an abstract autonomy card, and buried the one thing a newcomer actually wants to know - what is my agent doing right now.
- **What:** a new `#overview-hero` is the first thing on the page and answers, in plain words and about five seconds: the alive-state ("It's working / idle right now" from `/api/subagents`), the last thing the agent did (the most recent assistant reply, reused from the transcript `loadActivityStream` already fetched - no extra request), and a one-line stat row (sessions today, free-on-your-plan spend, running model). It makes no health claim it can't back. The autonomy / run-health / compare-runs / error-triage cards move into a collapsed "Advanced tools" disclosure - still one click away for power users, out of the newcomer's first view (progressive disclosure).
- **Verified:** confirmed live on app.clawmetry.com (logged in) by running the production `_renderOverviewHero()` against real data - renders "idle / replied 'pong' / 1 session / $0 free / sonnet". Frontend-only; reaches the cloud via the pinned wheel.

### Release: UI/UX pass round 2 - tracing reply, turn-anatomy in cloud, runtime-note + detected-runtime switcher (carries #2385/#2386/#2387) (2026-05-31)
- **Why:** follow-ups from the user's live-prod screenshots after the raw-codes fix (0.12.374).
- **What:** (1) Tracing Chat tab shows the agent reply, not just the prompt: the snapshot now keeps a truncated per-span detail/output (was dropped for size, leaving the cloud Chat tab empty) and `_traceExtractMessages` aggregates an agent span's descendant subtree first. (2) Cloud Turn-anatomy detail: new `turnAnatomy` snapshot slice (per-session turns built daemon-side via `routes.turn_anatomy._build_turns`) so the cloud interceptor renders the waterfall instead of "Event store not available here". (3) The misleading "Showing all runtimes, not filtered to X" note is suppressed on aggregate tabs when only one runtime actually has data. (4) The runtime switcher now groups locked (Pro) runtimes that are actually DETECTED on this machine under "Detected on this machine - upgrade to observe", distinct from generic catalog rows.
- **Verified:** confirmed live on app.clawmetry.com (logged in) that 0.12.374's raw-code fixes render correctly; the cloud span-detail gap that broke the tracing reply was found via live data inspection and fixed. Daemon-side slices reach a node when its daemon upgrades to this wheel; frontend reaches the cloud via the pinned wheel.

### Release: Tracing Chat tab shows the agent reply, not just the prompt (carries #2381) (2026-05-31)
- **Why:** user-reported (screenshot): clicking "invoke_agent main" in the Tracing tab showed the USER prompt but never the agent reply.
- **What:** the agent-root span is a container with empty own detail (the user prompt lives on a child prompt span, the assistant reply on a child chat/llm span's detail). `_traceExtractMessages` now, for an agent-kind span, aggregates the whole descendant subtree (prompt to user, llm to assistant, tool to tool/result, in start-time order) so the Chat tab shows the full user to assistant(+tools) conversation.
- **Verified:** aggregation logic emits both the prompt and the reply. Frontend-only; reaches the cloud via the pinned wheel.

### Release: fix raw HTML entities + missing i18n keys leaking into the UI (carries #2378) (2026-05-31)
- **Why:** users saw raw codes on live prod, screenshots in hand: the Flow diagram rendered "&#x1F50D; Search" instead of the magnifier emoji, turn-anatomy showed "prompt &rarr; model call(s)" instead of arrows, the Overview showed the raw i18n key "OVERVIEW.RUN_HEALTH_TITLE" instead of "Run health", and the Flow footer showed "flow.session_lanes".
- **What:** (1) Every emoji/arrow HTML entity is now a real Unicode glyph across all 26 tab/partial templates AND all 36 locale JSON catalogs (the i18n applier renders the locale VALUE via textContent, which does not decode entities, and SVG text nodes do not either; the entities were stored in the catalogs, so converting templates alone would not have fixed it). The em-dash entity becomes a spaced hyphen to honor the user-facing em-dash ban. (2) Added the 20 i18n keys that were used in templates but missing from en.json (overview.run_health_title, flow.session_lanes, tracing.tree_gantt, transcripts.replay_*, brain.*_title, security.pol_*, ...), and made the i18n applier fall back to the element's English markup text on a missing key so a missing key can never render as the raw key again, in any locale.
- **Verified:** new guard `tests/test_i18n_no_raw_codes.py` pins all three invariants (no emoji/arrow entities in templates or locale values; every template data-i18n key present in en.json); 109 i18n tests pass; i18n.js + all 38 locale files validate. Frontend-only; reaches the cloud via the pinned wheel; visual verification on app.clawmetry.com after the cloud pin.

### Changed: free-plan runtime paywall reframed as a non-blocking two-path modal (2026-05-31)
- **Why:** when a free-plan user selected a Pro runtime (e.g. Claude Code) in the header switcher, `_cmShowRuntimePaywall` threw a hard "Claude Code is a Pro runtime" wall over their data, with a single "Start free trial" CTA that — until cloud #1259 added the `/upgrade` route — 404'd. For a user whose only runtime is a Pro one, that's a dead-end first run, and the copy buried the fact that two runtimes are free.
- **What:** the modal is reframed as a non-blocking, two-path card (same dismissible overlay, same revert behavior): Path 1 reassures that **OpenClaw and NemoClaw are free, forever** (no trial needed); Path 2 offers the **no-card 7-day Pro trial** to audit the selected runtime "and every other agent runtime ClawMetry supports". Drops the stale "Upgrade to Pro to observe X, plus Claude Code, Codex…" line (which redundantly listed the runtime you'd just clicked). CTA still points at `/upgrade?source=runtime-switcher` (now a live route, not a 404). Complements the earlier free-plan runtime-UX work (locked runtimes never render as active + the install-OpenClaw/NemoClaw empty-state banner).
- **Verified:** `node --check` clean; rendered the modal standalone (label="Claude Code") and screenshotted — the two-path card renders as designed. Frontend-only (`app.js`); reaches the cloud via the pinned wheel (cloud pin bump to follow).

### Release: open-core plugin host wired into the daemon, proxy, and claudecode app (carries #2277/#2347/#2356) (2026-05-30)
- **Why:** `dashboard.py` calls `load_plugins()` at import time, so the dashboard process picked up `clawmetry.extensions` entry-point plugins (clawmetry-pro adapters, ingest hooks, policy/routing blueprints). But ClawMetry runs three other long-lived processes that never import `dashboard`, so paid plugins silently failed to register in them: the **sync daemon** (`python -m clawmetry.sync`, where ingest happens), the **enforcement proxy** (`python -m clawmetry.proxy`, the LLM-egress chokepoint), and the **standalone Claude Code dashboard** (`dashboard_claudecode.create_app`). A Pro plugin would register in one process and be missing in the others.
- **What:** each of the three entry points now calls `clawmetry.extensions.load_plugins` at startup, matching the dashboard. The daemon calls `load_plugins()` (no Flask app, so adapters/event-hooks register); the proxy and claudecode app call `load_plugins(app)` so blueprints register on their Flask apps. All three calls are wrapped in try/except and only log a warning on failure, so a broken plugin can never crash the ingest daemon or the egress proxy. Pure additions, no behavior change for pure-OSS installs (no entry points to load).
- **Verified:** dedicated regression tests for each (`tests/test_sync_loads_plugins.py`, `tests/test_proxy_loads_plugins.py`, `tests/test_claudecode_loads_plugins.py`) assert load_plugins is called exactly once, that load errors are swallowed with a warning, and that the existing app shape is preserved. Full CI matrix green. Daemon/proxy-side change, so it reaches a node when its daemon upgrades to this wheel; cloud pin bump to follow.

### Added: GET /api/brain/clusters for behavioral session clustering (#2357, closes #1650)
- New endpoint on `bp_brain` groups sessions by dominant tool category, cost tier, error presence, and model family (the same dimensions as `/api/sessions/clusters`), reusing the DuckDB helpers in `routes/usage.py` via a lazy import. Honors the same 24h retention cap as `/api/brain-history`: non-Pro users get `capped_at_24h: true` and a 1-day window; Pro users query up to 90 days via `?days=`. Graceful empty payload when DuckDB has no data. Hermetic tests cover both Pro and non-Pro paths.

### Added: transcript replay state panel + play/pause (#2344, #609)
- The replay scrubber gains an "as of T" state panel (current model, thinking level, cumulative tokens as the scrubber moves) and a Play/Pause button that auto-advances turns at 10 Hz. Frontend-only (`app.js` + `transcripts.html`), defensive null-guarded, i18n-attributed. Reaches the cloud via the pinned wheel.

### Docs: i18n residual-strings inventory for the pseudolocale audit (#2279, #2258)
- Adds `docs/i18n-residual.tsv`, a machine-generated catalog of the 89 un-extracted dynamic-string sites in `app.js` (46 Class B, 43 Class D) that Phases 1 and 2 skipped, as the Pass 2 work list for the Phase 3 implementor. Docs-only.

### Release: free-plan runtime UX — locked runtimes never render as active + per-screen runtime chip (carries #2351) (2026-05-30)
- **Why:** on the free plan the Flow tab rendered Claude Code (a Pro runtime) as an active "coding agent" while the empty-state banner said "install OpenClaw or NemoClaw" — a contradiction, with no per-screen indication of which runtime a tab was showing.
- **What:** (1) `_applyRuntimeFlowDiagram` no longer renders a runtime in `_cmLockedRuntimes` (populated from `/api/runtimes` when locking is on, e.g. the cloud free plan) as an active topology — it falls back to the default OpenClaw diagram; the header switcher carries the lock + upgrade affordance. (2) New per-screen **runtime chip** (fixed bottom-right on every tab) names the runtime the current screen is showing and is a second switch point: clicking opens a menu mirroring the header dropdown, with locked runtimes showing a padlock and routing to upgrade. Reuses the existing switcher state and mirrors the header `<select>` so the two stay in lockstep.
- **Verified:** `node --check` clean; the locked dropdown render was simulated end to end (OpenClaw free + all 10 family runtimes as `🔒 … · Upgrade`). Frontend-only; reaches the cloud via the pinned wheel.

### Release: runtime detection requires a real install + running, not a bare folder (carries #2341) (2026-05-30)
- **Why:** a node reported `openclaw_detected: true` on a machine where OpenClaw was uninstalled. Both detectors fell back to "`~/.openclaw` exists / is non-empty", but ClawMetry itself creates `~/.openclaw/workspace` to store its own sidecar files (`.clawmetry-metrics.json` via `_save_metrics_to_disk` → `os.makedirs`, and `.clawmetry-fleet.db`), so the dir is never empty → a permanent false positive that propagated to the cloud API (`agent_install`) and the UI.
- **What:** `clawmetry/sync.py:_detect_openclaw_install_for_heartbeat` and `dashboard.py:_detect_openclaw_install` now drop the bare-dir fallback and require a **genuine** signal — the `openclaw` CLI on PATH, `/Applications/OpenClaw.app`, a **live gateway** (pid alive or port 18789 listening, via the new `_openclaw_gateway_running`), a `gateway.pid`, real session `.jsonl` files, or workspace markers (SOUL/AGENTS/MEMORY.md). ClawMetry's own files are never counted. The `agent_install` payload now also carries `openclaw_running` (installed AND gateway live). `clawmetry/adapters/openclaw.py:detect()` got the same tightening, and now reports `running` from actual gateway liveness instead of the configured URL. `_detect_family_runtimes` now carries `detected` + `running` per runtime so every runtime reports installed-vs-running uniformly.
- **Verified:** `tests/test_openclaw_detection_real.py` (6 cases, wired into the OSS MOAT CI suite) — bare dir + ClawMetry-only files → not detected; workspace markers / real sessions / live gateway → detected; payload carries `openclaw_running`. Confirmed on the affected machine: the detector now returns `False`. Daemon-side change → reaches a node when its daemon upgrades to this wheel; cloud pin bump to follow.

### Added: firstRun snapshot key for guided activation UX (2026-05-29)
- The sync daemon now ships a `firstRun` top-level key in `sync_system_snapshot` so the cloud dashboard can render a guided "we are syncing your data" state instead of an empty page during the first 60 seconds after install. Pure passthrough of `sync_progress.json` (which has been recorded since #748) plus the in-process `_sync_progress_done` flag. The cloud reader derives a 4-state UI from this: Connecting (no progress file), Syncing (progress file present, not done), First value (first session present in the snapshot), Activated (done and at least one session). Keeping state derivation client-side means the cloud can tweak the state machine without an OSS release. Cheap to build (one file read), graceful on read failure (returns the empty default per the never-crash rule). Foundation slice for vivekchand/clawmetry-cloud#1189 (P0.1 activation). No behaviour change to local OSS users. (#2304)

### Docs: FLYWHEEL.md ban on em-dashes is now a canonical rule (2026-05-28)
- Promoted the buried one-liner in FLYWHEEL.md section 2 into a full rule with scope, allowed exceptions, and a belt-and-braces grep-before-send check. Covers landing HTML, dashboard banners, marketing copy, CHANGELOG entries, bounty and job posts (incl. external platforms), public docs, modals, and PR text users see. Allowed in code comments, internal notes, commit messages, internal-only PR bodies. Cites two prior burns (PR #211 landing copy, the rentahuman.ai bounty redraft) so the next agent does not repeat them. Doc-only; no code change, no version bump.


### Release: server-side runtime filter on /api/usage — Cost/Tokens tab de-merges (2026-05-28)
- The Cost / Tokens tab kept showing **merged** totals after Brain/Transcripts/Tracing de-merged: the aggregates are pre-grouped by `(agent_id, day)` without a runtime dimension, so client-side filtering wasn't possible. `query_aggregates` and `query_daily_usage_splits` now take an optional `runtime` param that adds a `session_id`-prefix `WHERE` clause **before** the dedupe CTE, reusing the same cost + token math. Per-runtime totals reconcile with the unfiltered total **by construction** (verified on a synthetic DuckDB: $10.20 unfiltered = $4.60 claude_code + $4.30 openclaw + $0.40 picoclaw + $0.90 goose, with the `model.completed` sibling correctly deduped). `/api/usage` reads `?runtime=…`; the frontend `loadUsage` appends it from the global switcher. (#2245)

### Release: evidence-based asset registry — first slice (carries #2231) (2026-05-28)
- DuckDB-backed asset registry now ships on PyPI: turns Self-Evolve findings (and any other agent discovery) into reviewable, reusable assets with provenance — `pending → approved/rejected → deprecated`, every asset tied to a source `session_id`/`run_id`, daemon-proxied reads + writes, full `/api/assets` surface, and a one-click "save as asset" hook on the Self-Evolve route. See the detailed Added entry below for design + scope. No cloud pin bump.

### Added: evidence-based asset registry — first slice (2026-05-28)
- New DuckDB-backed asset registry that converts individual agent discoveries (Self-Evolve findings, useful prompts, improved skills) into **reviewable, reusable assets with provenance** — without auto-promoting unreviewed local changes to team/company defaults (#2201). Lifecycle `pending → approved/rejected → deprecated`; every asset traces to a source `session_id`/`run_id`. Types: `skill`, `prompt`, `workflow`, `playbook`, `memory_snippet`, `tool_config`, `evaluation_case`. The daemon owns writes; reads ride the daemon proxy so the cloud can paint from a snapshot the same way (added to the `_DAEMON_METHODS` allowlist next to `ingest_approval` / `update_approval_decision`).
- HTTP surface (`routes/assets.py`): `GET /api/assets` (filter by `status` / `asset_type` / `source_run_id` / `source_session_id` / `limit`), `GET /api/assets/<id>`, `POST /api/assets` (create candidate), `POST /api/assets/<id>/review` (`approve` / `reject` / `deprecate`).
- Self-Evolve hook: `POST /api/selfevolve/findings/save-as-asset` packages a finding into a `pending` candidate asset with its source `session_id` attached and a `self-evolve` provenance tag — one-click promotion from a finding card to the registry. Approval still requires an explicit reviewer action.
- Foundation lives in OSS (DuckDB-first); the richer review/promote console with reviewer identity + auto-recommendation is the planned Pro surface. 19 unit + HTTP tests; daemon-side only, no cloud pin bump.

### Added: agents must work in an isolated git worktree (FLYWHEEL.md §0) (2026-05-28)
- Documented hard rule: multiple Claude Code agents and crons run against this repo concurrently — editing the main checkout is unsafe because another process can switch branches mid-edit and clobber uncommitted changes. Future agents must start with `EnterWorktree` (or `git worktree add .claude/worktrees/<slug> -b feat/<slug> origin/main`). Burned 2026-05-28 when an autonomous process checked out a different branch in the shared working tree and wiped the in-progress asset-registry edits.

### Added: Compare-two-runs widget + Error-triage list on Overview (2026-05-28)
- UI consumers for the two backend primitives shipped earlier this day in #2196: a **Compare two runs** card that calls `/api/run-compare` and renders the side-by-side panel with green/red signed deltas (lower-is-better for cost/steps/errors/flags; higher-is-better for cache hit); and an **Error triage** card that lists currently-resolved errors (most-recent-first, with `Unresolve` per row) plus an input row that POSTs to `/api/error-triage/resolve` with an optional note. Both cards live on Overview between the health-timeline strip and the existing refresh-bar, fire-and-forget on every `loadAll()` tick. Completes the user-visible loop for items #2 and #5 of #2196 (#2238).

### Release: syslog/SIEM export + verify-integrity daemon-proxy fix (carries #2217 + #2222) (2026-05-28)
- The Enterprise-grade syslog/SIEM exporter from #2217 ships on PyPI, plus the verify-integrity CLI fix from #2222 (caught by FLYWHEEL §7 live verification — the new CLI crashed against a running daemon because the proxy allowlist did not include the new method). See the detailed entries below. Off by default; activates only when `CLAWMETRY_SIEM_HOST` is set. No cloud pin bump.

### Added: syslog/SIEM export (CEF + JSON over udp/tcp/tcp-tls) (2026-05-28)
- Daemon-side SIEM exporter (#2199 / #2217) that streams every event to a Splunk / QRadar / ArcSight / Elastic SIEM or any RFC 5424 collector. New `clawmetry/siem.py` is a pure-formatter + bounded-queue + single background sender thread; activated when `CLAWMETRY_SIEM_HOST` is set (off otherwise). CEF (`CEF:0|ClawMetry|clawmetry|<ver>|<sigId>|<name>|<sev>|<ext>`) or compact JSON, framed as RFC 5424. Stable signature-ID map (1001 tool call, 1002 tool result, 2001/2002 message, 3001 LLM usage, 4001 session start, 5001 budget exceeded, 6001 security threat, 7001 approval required, 8001 cron run, 9002 daemon error, 9999 generic) — new event types fall through to 9999 so adding a new event type does not require a SIEM-side change. Wired into `LocalStore.ingest()` *after* the redaction pass (#2204) so secrets never leave via syslog either, and the line carries the `chain_prev_hash` / `chain_hash` from #2210 in `cs5` / `cs6` so the SIEM message has the same audit-grade payload as DuckDB. Bounded queue + reconnect: ingest never blocks on socket IO, a dead collector drops + counts rather than back-pressures, the worker survives transient writer failures. 21 unit tests; UDP + TCP + JSON locally verified against a netcat listener (received CEF lines with `sent=N dropped=0 errors=0`). Daemon-side only; no cloud pin.

### Fixed: verify-integrity CLI crashed when a sync daemon is running (2026-05-28)
- `clawmetry verify-integrity` (shipped in 0.12.342) crashed immediately against any standard install: `get_store(read_only=True)` returns `_ProxyStore` because DuckDB locks at the process level and the daemon holds the writer; the proxy forwards each call through HTTP to `/__local_query__/<method>` on the daemon, but the daemon-side allowlist (`_DAEMON_METHODS` in `routes/local_query.py`) did not include `verify_integrity` — so the proxy returned `None` and the CLI crashed on `result["status"]` (TypeError). Fixed in two layers (#2222): allowlist entry so the proxy succeeds, plus a defensive `if result is None` branch in the CLI that prints a clear "could not reach the running daemon's verifier — restart the sync daemon" message and exits 2 instead of crashing. Three new regression tests (`tests/test_verify_integrity_cli_proxy.py`) pin the allowlist + the graceful-None + the existing invalid-chain branches so the family cannot regress. Caught by FLYWHEEL §7 live verification; no user had hit it yet.

### Added: error triage — mark known/expected errors as resolved (2026-05-28)
- A user can now mute a known/expected error so it stops inflating counts on Tracing / Health / the run-compare deltas. New `resolved_errors` DuckDB table (event_id PK + resolved_at + optional note); `local_store.mark_error_resolved` (idempotent upsert) / `unmark_error_resolved` (truthful removed-bool, since DuckDB's `cursor.rowcount` is -1 for DELETEs) / `query_resolved_errors` returning the map. Three new routes on `bp_sessions`: POST/DELETE `/api/error-triage/resolve` and GET `/api/error-triage/resolved`. The snapshot ships a `resolvedErrors: {event_id: {resolved_at, note}}` slice so the cloud renders the same muted state local does — persisted in DuckDB (not `localStorage`) so it transits the E2E-encrypted cloud and is consistent across devices. Daemon-side foundation; the UI consumer (Resolve button + Show-resolved toggle) ships in a follow-up (#2196 / #2230). Verified live: snapshot decrypt confirms the slice (48 keys vs 47); table migration ran cleanly.

### Added: /api/run-compare for per-run A/B with deltas (2026-05-28)
- New endpoint that takes two session ids and returns side-by-side stats (cost, tokens, steps, context, cache hit, errors, waste flags, severity) with signed deltas; each delta carries `abs`, `pct` (None when A is zero to avoid /0), and `favorable` (lower-is-better for cost/steps/errors/flags; higher-is-better for cache hit). Stats are computed from the same primitives the snapshot uses — #2202 corrected error flag + #2215 waste-flag signals — so the Compare view reads the same truth the Overview health timeline + cost numbers do. The UI consumer (a Compare modal on the Sessions tab) ships in a follow-up; this PR is the data primitive (#2196 / #2227). Daemon-side only; no cloud code change required.

### Added: per-runtime health timeline on Overview (2026-05-28)
- Compact sparkline of recent sessions, bucketed by runtime, on the Overview tab. Each dot summarises one session: **red** for any real error (post #2202 benign-error filtering), **yellow** for any waste flag (#2215), **green** for a clean run; hovering shows time, error/flag count, cost. New `clawmetry/waste_flags.py` helpers (`runtime_from_session_id`, `severity_from_counts`, `event_is_real_error`) make snapshot + route share one truth, the daemon ships a `healthTimeline` snapshot slice, `/api/health-timeline` (30 s cache) returns the same shape for the local dashboard, and `templates/tabs/overview.html` + `static/js/app.js` render the dot strip — hiding the card when no runtime has dots. Daemon-side primitive + dashboard render only; cloud inherits the snapshot slice, no cloud code change required (#2196 / #2225). Verified live: decrypting the cloud snapshot shows 5 runtimes (`claude_code`: 30 dots, `openclaw`: 2, `qwen_code`: 2, `opencode`: 3, `goose`: 3), severity mix 10 red / 1 yellow / 29 green.

### Added: per-run waste flags in the snapshot (2026-05-28)
- Per-session waste-flag heuristics that turn an anomalous run from "something is unusual" into "here's the lever to pull": `runaway` (>30 tool steps), `cold_cache` (<50% hit AND >5 steps), `unscoped_result` (>10KB tool result), `bloated_context` (>50k tokens on a single step). Thresholds are env-tunable (`CLAWMETRY_WASTE_*`). New `clawmetry/waste_flags.py` is a pure-function classifier + per-session aggregator covering both Anthropic `data.usage` and Claude Code `data.extra` shapes. The daemon's `_build_waste_flags()` ships a `wasteFlags: {session_id -> [flags]}` slice on the snapshot — sessions with no flags are omitted so "empty == clean run". Daemon-side only; cloud renders client-side, no cloud change required (#2196 / #2215). Verified live by decrypting the cloud snapshot: 22 sessions flagged across `runaway` + `unscoped_result` with concrete actionable messages.

### Fixed: Brain density chart leaked across runtimes + cross-adapter no-leak contract test (2026-05-28)
- Picking a runtime emptied the Brain *list* ("No recent Claude Code activity, 87 sessions older than this window") but left the density *chart* full of bars from other runtimes — `renderBrainChart` filtered by source/type pills but never by `_cmRuntimeFilter` or the channel pill (#2214). It now mirrors the four filters `renderBrainStream` already applies.
- New `tests/test_runtime_filter_no_leak.py` — cross-adapter contract test that seeds events from every known runtime (claude_code/qwen_code/codex/hermes/goose/opencode/cursor/nanoclaw/picoclaw/aider) plus a bare-UUID openclaw-default, then asserts `/api/model-attribution?runtime=` returns ONLY that runtime's turns (exact count, no leak / no loss) and `/api/runtime-summary` buckets every session into exactly one runtime. Plus pure-function bucketing coverage (mirror of frontend `_cmRuntimeOf` and `sync._runtime_of_session`) and JS static guards on renderBrainChart + renderBrainStream so a future edit can't drop the runtime filter from either function without CI failing.
### Release: tamper-evident hash chain for event audit log (carries #2210) (2026-05-28)
- Per-node SHA-256 chain over events now ships on PyPI, plus the new `clawmetry verify-integrity` CLI. Off by default (set `CLAWMETRY_INTEGRITY=1` to enable stamping; existing stores migrate cleanly and pre-chain rows are reported separately by the verifier). See the detailed Added entry below for the design and the cost-backfill-safety guarantee. No cloud pin bump.

### Added: tamper-evident hash chain for event audit log (2026-05-28)
- The local DuckDB event store had no tamper-evidence: a compromised host or an accidental edit to a historical event row could not be detected. Naive whole-row hashing would not work because columns like `cost_usd` / `token_count` / `model` / `data` get mutated post-insert by the cost backfill and other enrichers (`local_store.py:3901` and `:3980` are real `UPDATE events SET ... WHERE id` paths), so any chain that covered them would break on every normal operation. The fix (#2200 / #2210) is a per-node SHA-256 chain that hashes only the immutable identity fields of an event: `id`, `agent_type`, `node_id`, `agent_id`, `session_id`, `workspace_id`, `event_type`, `ts`. `clawmetry/local_store.py` gets `chain_prev_hash` / `chain_hash` columns on `events` (added via the existing `_MIGRATIONS_V2` pattern so existing stores upgrade safely) and a new `chain_heads` table that tracks the current head per node; `_stamp_integrity()` runs inside the same flush transaction as the row insert so hashes land atomically with the data they cover. A new reader `verify_integrity(node_id=None)` walks the chain and returns VALID or the first broken link. `clawmetry/cli.py` exposes `clawmetry verify-integrity [--node-id ID]` (read-only open, prints scope + checked count + pre-chain count + result). Off by default via `CLAWMETRY_INTEGRITY=1`; when disabled the columns stay NULL and there is zero overhead. 10 unit tests cover the genesis hash, sequential links, per-node scoping, pre-chain counting, tamper detection on each immutable field, and the critical acceptance test that a real `backfill_event_costs` does NOT invalidate the chain. Daemon-side only; the cloud inherits the chain via the snapshot. No cloud pin bump.

### Fixed: benign tool results no longer inflate error counts (2026-05-27)
- Tool results carrying an `isError`/`is_error` flag for non-failures — Claude Code's `File has (not) been read yet` / `File has been modified since read` read-guards and transient `gateway timeout after …` retries — were counted as real errors across Tracing / Health / Self-Evolve and the snapshot. Measured on a live store, the read-guards alone were ~two thirds of all flagged tool errors. New `clawmetry/error_signal.py` is the single benign-error classifier; the fix lands at the **ingest chokepoint** so every reader and the snapshot inherit the corrected flag — `sync.py` corrects the stored flag at both ingest paths (v3 `tool_use_result` and the Claude Code family adapter) and stamps `data.benign_error`, `local_store.backfill_benign_errors()` (bounded, idempotent, id-cursor paged, mirrors the cost backfill) heals history, and `routes/selfevolve._classify_event` consults the same helper. Result text is preserved (only the flag is corrected). Daemon-side only — cloud inherits via the snapshot, no cloud change required (#2196 / #2202). Verified live: backfill cleared 96 historical flagged-but-benign errors; the recent-20k-event window dropped from 80 to 40 flagged tool errors with genuine errors preserved.

### Release: secret redaction at the ingest chokepoint (carries #2204) (2026-05-28)
- Daemon-side defense-in-depth secret scrubbing now ships on PyPI. Cuts off the leaked-key surface where an agent echoes a token into a tool arg or transcript. See the detailed entry below for design + opt-out. No cloud pin bump.

### Added: secret redaction at the ingest chokepoint (2026-05-27)
- Events are stored plaintext in local DuckDB before the cloud-sync E2E boundary, so an API key / bearer token / password echoed into a tool argument or transcript would land verbatim on disk. New `clawmetry/redaction.py` scrubs secret-shaped values **before** they're queued for persistence, applied at the single chokepoint `LocalStore.ingest()` (#2197). High-precision patterns (provider keys `sk-`/`sk-ant-`/`AKIA…`/`AIza…`/`ghp_…`/`xox[bapr]-…`/`glpat-`, `Bearer <token>`, `key=value` secrets, PEM private-key blocks) and explicitly sensitive field names (`api_key`, `password`, `authorization`, …, excluding `*_tokens` counts) are replaced with a **stable fingerprint** `[REDACTED:<sha8>]` — same secret always maps to the same token so de-dup/cardinality survive, but the value is irreversible. On by default; `CLAWMETRY_REDACT=0` disables. Structural identifiers (id/node_id/session_id/model/token_count/…) pass through untouched; never crashes on bad input. Daemon-side only (cloud renders already-scrubbed data) — no cloud pin bump.

### Fixed: Overview MODEL card now actually scopes to the runtime (2026-05-27)
- The previous cut wired the Overview MODEL card via `applyBrainModelToAll` (Flow-diagram labels only) and `loadMiniWidgets` then overwrote `#model-primary` with the node-dominant model, so it still showed claude-opus-4-x when Qwen Code was selected. The scoping now lives in `loadMiniWidgets` itself (the single place the card is set on Overview): a selected runtime shows that runtime's primary model from `/api/runtime-summary` (`qwen3:8b` for Qwen Code), `—` if it has no model turns (#2191).

### Added: Overview model card scopes to the selected runtime (2026-05-27)
- The Overview headline MODEL card showed the node-dominant model (claude-opus-4-7) even when a specific runtime was selected. It now shows the selected runtime's primary model (e.g. `qwen3:8b` for Qwen Code), matching the Models tab (#2187). New `GET /api/runtime-summary` (per-runtime tokens/cost/turns/sessions/primary_model; mirrors the daemon `runtimeSummary` snapshot slice). Cost/tokens stay node totals (today/week/month windows the all-time slice can't decompose per day).

### Added: Models tab filters by the selected runtime (2026-05-27)
- The Models tab was an aggregate that merged every runtime, so picking "Qwen Code" still showed claude-opus-4-7 / 19,802 turns (with only an honest "all runtimes" note from the prior release). It now filters for real (#2183): the daemon ships a compact `runtimeSummary` snapshot slice (per-runtime tokens/turns/cost/sessions + a model-attribution block), `/api/model-attribution?runtime=<prefix>` scopes the breakdown server-side, and the cloud `cm-cloud-models` interceptor returns `runtimeSummary[<runtime>]`. Selecting Qwen Code now correctly shows `qwen3:8b` / 9 turns instead of the merged claude-opus-4-7 totals — an honest empty set when a runtime has no model turns, never a silent merge. Overview headline + Cost tab reuse the same slice next.

### Fixed: runtime switcher is now honest on every tab (2026-05-27)
- Picking a specific runtime (e.g. Qwen Code) in the header switcher used to leave almost every tab showing merged data from other runtimes (Claude Code / OpenClaw) with no indication — only Transcripts, Brain, Tracing, and the Flow diagram actually scoped. Now the selection is honest everywhere (#2180):
  - **Real client-side filtering** (session-id prefix = runtime) on the tabs that carry session-level data: **Turn anatomy** (`/api/traces`, scoped empty state), **Active Tasks** on Overview (`/api/subagents`), and the Overview **"Main Agent Activity" feed** (`/api/brain-history`) — the last was the "feed shows OpenClaw cron chatter while Qwen is selected" report.
  - **Transcripts / Session replay** no longer silently fall back to "all runtimes" when the selected runtime has no transcripts (the "I picked Qwen but see Claude Code" confusion); they show a scoped empty state instead.
  - **Global switcher counts are merge-MAX, not replace:** a per-tab loader's subset (Transcripts only sees transcript-bearing sessions) can no longer drop a runtime that has sessions but no transcripts (qwen) from the dropdown or revert the selection to "all".
  - **Honest scope note** on tabs the switcher can't scope client-side: aggregate tabs (Models, Cost/Usage, Tool catalog, Context economics, LLM Context) say "Showing all runtimes — not yet filtered to \<runtime\>", and node-wide tabs (Crons, Memory, Security, Skills, Self-evolve, Approvals, Alerts) say "\<runtime\> is selected, but this view is node-wide." True per-runtime aggregation for Models/Cost/Overview-stats is the planned follow-up.

### Fixed: Tool Catalog mislabeled builtins + empty drill-down on non-OpenClaw runtimes (2026-05-27)
- **Cross-runtime provenance (#2177):** the Tool Catalog decided "builtin" *only* from the OpenClaw sandbox `tool_policy` allow set, which a Claude Code / Codex node never ships — so Bash/Read/Edit/Write/Task* all fell through to "plugin" (a Claude Code node read "1 builtin / 7 MCP / 14 plugin"). A runtime-agnostic `RUNTIME_BUILTINS` set (Claude Code + Codex core tools) is now unioned into the builtin universe in both the live `/api/tool-catalog` route and the snapshot slice. Names are runtime-distinct (PascalCase vs snake_case vs `mcp__`) so the union can't collide, and a genuinely unknown name is still "plugin". The same node now reads `builtin: 12 / mcp: 7 / plugin: 2`.
- **Cloud drill-down was always empty (#2177):** clicking a tool to expand its recent calls showed "No individual calls captured" for every tool in the cloud. The `cm-cloud-tool-catalog` interceptor reads `snapshot.toolCatalog.calls[name]`, but the daemon's snapshot slice only ever shipped `{tools, groups}`; the cold fall-through then hit the cloud server's `/calls` route, which reads a DuckDB that is empty on the container. The snapshot now ships a bounded per-tool `calls` map (the 15 newest calls of each shipped tool: `{ts_ms, duration_ms, status, session_id}`), keyed by tool name to match the interceptor. +22.8 KB / 4.7% of the snapshot, served behind the existing `system-snapshot` ETag/304. No cloud change needed — the interceptor already reads this key. Verified by decrypting the live cloud snapshot.

### Release: per-adapter Flow diagram + runtime-aware Brain empty state (2026-05-27)
- **Per-adapter Flow/Overview diagram (#2174):** the Flow diagram always showed OpenClaw's channel→gateway→agent→tools topology even for runtimes that have neither. Coding-CLI runtimes (Claude Code, Codex, Cursor, Aider, Goose, opencode, Qwen) and the minimal PicoClaw/NanoClaw now get a generated, runtime-correct diagram (Terminal → agent → coding tools → Workspace, animated edges); OpenClaw/Hermes keep the rich hand-built SVG. The Overview pane mirrors it. Driven by the global runtime switcher.
- **Runtime-aware Brain empty state (#2174):** selecting a runtime with sessions on record but no recent events showed a bare "No activity yet" that contradicted the switcher's "Goose · 3 sessions". Now it explains the session count and points to the Tracing tab.

### Fixed: Active Tasks showed week-old runs as "Recently Completed" (2026-05-27)
- The overview Active Tasks panel filtered "Recently Completed/Failed" by each task's run **duration** (`runtimeMs < 2h`) instead of **how long ago it finished**, so a 5-minute task that ended days ago kept showing as "recent" and an idle node looked busy. Now bounded by finish age (1h), derived the same way the card's "Finished N ago" label is (`completionTs → updatedAt → startedAt+runtime`). Idle nodes correctly show "No active tasks — The AI is idle"; running tasks still always show. (#2170)

### Release: runtime switcher scopes Tracing + clearer "N sessions" labels (2026-05-27)
- The global runtime switcher now also filters the **Tracing** tab (event-derived traces set `trace_id = session_id`, whose prefix is the runtime). Brain + Transcripts + Tracing now all de-merge by runtime. (#2167)
- Switcher option labels now read **"Claude Code · 22 sessions"** / **"OpenClaw · 1 session"** / **"All runtimes · 23 sessions"** instead of a bare `(22)`, which had read as "22 Claude Code runtimes" (there is one runtime running many sessions). (#2167)

### Release: runtime switcher now scopes the Brain activity stream (2026-05-27)
- The global runtime switcher (header dropdown) now filters the Brain "Unified Activity Stream" too, not just Transcripts. The Brain feed merged every runtime (OpenClaw + Claude Code + Codex + …) with no separation, which is the spot the merge most confused debugging. `renderBrainStream` honours `cm-runtime-filter` alongside the existing source/type/channel filters (each event's `sessionId` prefix is the runtime discriminator). Picking a runtime scopes the stream in place. Transcripts + Brain now both filter; Tracing/Cost/Overview still merge (follow-ups). (#2160)

### Release: per-MCP-server rollup + global runtime switcher (2026-05-27)
- **Per-MCP-server cost & latency rollup (#2156, closes #2007):** new `GET /api/mcp-servers` + a "MCP servers" card on the Tool Catalog tab that groups the agent's MCP tool calls by server (the `mcp__<server>__<tool>` prefix) so you can see which MCP server is hot, slow, or error-prone: call volume, p50/p95 latency, error rate, the tools each server exposes, and the model spend of the turns that called it. Reuses the tool catalog's `tool_call`→`tool_result` join; latency/volume/error-rate are exact, cost is best-effort (the calling turn's cache-aware spend, labelled as such), and transport (stdio/sse/http) + cold-start are omitted rather than faked (they need new ingest). A bounded `mcpServers` snapshot slice ships the same rollup to the cloud. Verified live: `chrome-devtools-mcp` · 26 calls · 229ms/2.9s p50/p95 · 23% errors · $30.69 turn spend.
- **Global runtime switcher (#2157):** the per-runtime filter that previously only rendered on the Transcripts tab is now an always-visible header control (`Runtime ▾` → All / OpenClaw / Claude Code / Codex / NanoClaw / …), shown only when more than one runtime is detected so single-runtime installs are unchanged. The runtime is derived from the session-id prefix; the selection persists and reloads the current tab so runtime-aware views re-filter. Makes the multi-runtime de-merge discoverable instead of buried on one tab.

### Release: loop badge on Sessions, spend optimizer, v2 Cost tab, --v2-default (2026-05-26)
- Ships four merged feature PRs end to end:
  - **Loop-detection badge on Sessions cards (#2134):** the `loop_signals` data that already powered the Brain-tab badge now surfaces as an amber **⚠ Looping** badge on each session card (where users look first). `loadSessions()` fetches `/api/loop-signals` in its existing `Promise.all`; the badge links to the Brain tab for per-request detail. Fails silently (no badge, no error) when the proxy/local store is unreachable.
  - **Spend Optimization recommender (#1884):** read-only `GET /api/usage/optimization-recommendations` reads the last 30 days of spans and applies a static heuristic (deterministic tools like bash/read/ls rarely need heavy reasoning) to rank tools that can safely route to a cheaper model tier, with projected monthly savings. New 💡 Spend Optimization card on the Tokens tab (hidden until data arrives), i18n-registered. No writes, no LLM calls, no new deps; the card stays hidden for nodes whose spans lack cost attribution.
  - **v2 Cost tab — real data (#2005):** `/v2/cost` replaces its "Coming soon" stub with integration bars + a 7-day daily cost table (▲ spike markers) + a fleet leaderboard + spike log. `GET /api/v2/cost` reads real per-(agent, day) cost from `query_aggregates` via the daemon proxy — the same source the v1 Usage tab trusts — so the three views are internally consistent to the penny; spikes are computed from real day-over-day deltas. No fabricated numbers; graceful empty state when the store is cold.
  - **`clawmetry --v2-default` (#1980):** new opt-in flag mounts the v2 SPA at `/` and shifts v1 to `/v1/` (default behaviour and all `/api/*` routes unchanged; the v2 blueprint still only registers under `CLAWMETRY_V2=1`). Completes the #1500 acceptance criteria.

### Fixed: remote / Docker / reverse-proxy gateway via OPENCLAW_GATEWAY_URL (2026-05-26)
- Running ClawMetry where the OpenClaw gateway lives on another host (Docker with the OpenClaw files mounted, a reverse proxy, an Android device on the LAN) was stuck at "Invalid token or gateway not responding" even with a valid token. When the mounted OpenClaw files contained the token, `_load_gw_config` auto-set `GATEWAY_URL = http://127.0.0.1:18789` (the container's own loopback), so every gateway call hit nothing. The only override was an easy-to-miss "Optional:" URL field in the setup wizard, with no environment variable for Docker/compose users to pre-configure. Now `OPENCLAW_GATEWAY_URL` is honoured before the localhost default in all three spots that resolve the gateway: `_load_gw_config`, `_auto_discover_gateway`, and the `/api/gw-config` POST path. So `docker run -e OPENCLAW_GATEWAY_URL=http://192.168.x.y:18789 …` just works. Explicit beats implicit: a set env var is tried before auto-discovery (a wrong value will block local auto-detection, which is the intended precedence). The wizard's URL field is relabelled from "Optional:" to make clear it is required for remote/Docker/reverse-proxy/Android setups, with the env var spelled out inline. (#2132, closes #2106)

### Release: dashboard tab i18n COMPLETE — all 36 languages (2026-05-26)
- Backfills the remaining 18 languages' dashboard tab translations (ar/de/el/fa/fil/he/id/it/nl/pl/pt-PT/ru/sv/th/tr/uk/ur/vi), bringing every dashboard tab to 100% coverage across all 36 languages (incl. RTL). Completes the i18n initiative: dashboard + cloud + landing + README all fully localized. Generated by the Claude CLI autotranslate bot.

### Fixed: Spending hero card now matches Cost tab (2026-05-26)
- The snapshot's `spending` block was read from the daemon's `state.json` (stale, usually `{today:0,week:0,month:0}` on fresh nodes), while `dailyUsage` was correctly derived live from DuckDB events × pricing (#2058). The cloud Spending hero card consumes `snap.spending` → rendered $0 while the Cost tab showed the real four-figure month. Now `spending` derives from `dailyUsage`'s `todayCost`/`weekCost`/`monthCost` so both surfaces agree; `state.json` stays as a fallback when dailyUsage is empty. (#2143, closes #2142)

### Release: spending hero card matches Cost tab (2026-05-26)
- Publishes #2143 (closes #2142): the Spending hero card on the cloud overview now reflects the same dollar figure as the Cost tab instead of showing $0 alongside a four-figure Cost tab.

### Release: interactive observability surfaces — tool catalog, context economics, drill-down runs (2026-05-26)
- Publishes the last two PRD observability surfaces plus interactivity across the run-ledger tab, all on the on-disk / `openclaw`-CLI data path:
  - **Tool catalog + provenance + latency (#2136, P1-3):** every tool the agent invoked, grouped by provenance (builtin / MCP / plugin), with call count + **p50/p95 latency** + error rate (derived from the `tool.call`→`tool.result` join in DuckDB events). Rows are **click-to-expand** into recent individual calls (duration + ok/error + session deep-link); sortable + provenance-filterable. Bounded `toolCatalog` snapshot key for cloud.
  - **Context economics (#2137, P1-2):** a context-window **utilization gauge over time**, the **compaction log** tagged proactive-vs-overflow with **tokens reclaimed**, and an overflow-then-retry flag. Compaction rows **click-to-expand** (before/after tokens + summary + transcript deep-link); clickable session chips scope the gauge. Bounded `contextEconomics` snapshot key.
  - **Interactive run-ledger (#2138):** the Sub-Agents/Queue-Lanes tab is now explorable — click a lane to filter Recent Runs, click a run to expand its detail drawer (run id, scope, delivery, outcome, timing, error) with an "Open session →" deep-link. Filter/expand state survives the auto-refresh.

### Fixed: cloud Dives via heartbeat relay (was a raw DuckDB error) (2026-05-26)
- The cloud **Dives** tab (NL-to-SQL exploration) showed a raw `Local store unavailable: IO Error: Cannot open database "/root/.clawmetry/clawmetry.duckdb" in read-only mode: database does not exist`. The cloud server has no DuckDB and cannot decrypt the E2E snapshot, so it can't run Dives' arbitrary SQL server-side. Dives now rides the heartbeat-piggyback relay like cron does (local compute, cloud display): the daemon gets a `dives_query` action, runs the NL-to-SQL + query on its **own** DuckDB writer handle (never a `read_only=True` re-open), and posts the AES-256-GCM-encrypted `{sql, chart_spec, rows}` result to `/ingest/cache` for the browser to poll + decrypt client-side. The cloud never sees plaintext. The local `/api/dives/query` handler also degrades gracefully now — a keyless/cold cloud fall-through returns a clean "run Dives on your local dashboard" message instead of the raw IO error. The NL-to-SQL step runs on the node, so it needs an Anthropic credential (env var or `claude` CLI OAuth) locally; without one the relay returns the existing no-auth banner. (#2127 + cloud)

### Fixed: installer no longer wipes ~/.clawmetry on upgrade (silent local-history loss + crash) (2026-05-25)
- `curl … | bash` ran an unconditional `rm -rf ~/.clawmetry` before recreating the venv, but that directory is **both the venv and the data dir** — it holds the local DuckDB store (`clawmetry.duckdb`) and `config.json` (the node_id + E2E encryption key). Two consequences: (1) **every upgrade silently destroyed local DuckDB history** (only `config.json` was backed up/restored; a 423 MB store on the reporting machine was deleted), and (2) on a machine with the sync daemon running, the wipe raced the daemon's live DuckDB writes — `rm` deleted the contents, the daemon kept recreating `clawmetry.duckdb.wal`, and the final `rmdir` failed with `Directory not empty`, which `set -e` turned into a full install abort that left a half-wiped, non-bootable install. The installer now **upgrades in place**: when a venv already exists it just runs `uv`/`pip install --upgrade` (DuckDB + config untouched); when the venv is missing or partial but data is present it stashes the data aside, rebuilds the venv (keeping uv's Python 3.11), and restores it; fresh installs are unchanged. Cloud history (snapshot-based) was never affected — only local DuckDB history was at risk, and only until this fix. Served live from `main` (install.sh isn't in the PyPI wheel), so it deployed on merge. Verified by repairing the exact failing machine end to end: config recovered from the pre-`rm` temp backup, venv rebuilt, daemon back up, DuckDB re-ingesting, dashboard serving real data, same node_id + encryption key. (#2120)

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
