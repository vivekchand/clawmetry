## Unreleased

- **Release: the Developer > Gateway screen is gone. Nothing replaces it, because nothing was needed: the OpenClaw gateway token is auto-detected server-side. Carrier `[RELEASE]` so #4885 reaches PyPI, the fleet, and the cloud pin.**
  - **Why:** founder ask 2026-08-15 with a screenshot of the page, "this screen can be removed, we don't need this." The form asked the user to paste a token the product already reads for itself. `_detect_gateway_token()` in `dashboard.py` pulls it from `OPENCLAW_GATEWAY_TOKEN`, from `~/.openclaw/openclaw.json`, or from the running gateway process, and `OPENCLAW_GATEWAY_URL` covers remote, Docker, and reverse-proxy setups. The page was the last survivor of the v0.1 era, when OpenClaw was the only runtime ClawMetry watched. It shipped as an opt-in tab in #4575 after the auto-popping setup wizard was retired, and it is now a config surface for a value that needs no configuring, in a product that detects 20+ runtimes automatically.
  - **What:** deleted `clawmetry/templates/tabs/gateway.html`, its nav item and template include in `dashboard.py`, and the `gwSetupConnect()` / `updateGwStatus()` pair in `clawmetry/static/js/gw-setup.js` that only ever drove that form. Everything headless in that file stays: a `?token=XXX` URL still auto-configures on load, and a token this browser remembered in `localStorage` is still posted to `/api/gw/config`. `/api/gw/config` itself is untouched, so remote sign-in with a raw token (the login overlay's Advanced path) still works.
  - **Verified:** dashboard booted locally, served HTML has no `page-gateway` and no `gw-token-input`, and the Developer drawer renders Flow, Models, Tracing, Agent Graph, Tools, Context usage, Harness, Ask with no Gateway row (Playwright screenshot). `tests/test_beginner_nav_phase_a.py` nav expectations updated; `tests/test_e2e_oss_all_tabs.py` drops the gateway tab from its sweep; the #1127 dead-end guard now pins that neither the tab nor the retired wizard comes back. Drive-by: the drawer membership assertion had already drifted from the shipped nav (Tracing returned to the drawer after Phase B moved it out) and was red before this change; it now matches reality.

- **Release: the desktop shell checks PyPI every 60 seconds instead of every 6 hours, and finally honours that interval when an update fails. Carrier `[RELEASE]` so #4879 produces a new `.dmg` / `.exe` / `.AppImage` — `desktop/app.py` ships in the BUNDLE, not the wheel, so PyPI alone does not deliver it.**
  - **Why:** founder ask 2026-08-15, prompted by the previous entry. 0.12.707 armed the post-trial paywall, which made the upgrade overlay the only surface a lapsed user can reach — so a layout defect there is a lockout, and 0.12.708 fixes exactly that. Telling a user who cannot reach the "Activate license" button to wait up to six hours and then relaunch, with no in-app way to trigger it, is not a recovery path. 60s also matches the daemon's own update worker (`routes/update_check.py`, `CLAWMETRY_UPDATE_CHECK_SECS`), so the shell stops being the slower of the two supervisors.
  - **The 6h figure was already a fiction, and that is the more interesting half.** `UPGRADE_CHECK_INTERVAL_SECS` is enforced solely through the `last-upgrade.json` stamp, and the failure paths never wrote one. So after any failed update `_should_upgrade()` stayed true and the watcher retried on the very next tick: a failing update re-ran every `WATCHER_TICK_SECS` (60s) indefinitely, whatever the interval said. 6h only ever throttled successes. Verified against the pre-change code — three consecutive failures, stamp never written, `_should_upgrade()` true every time. Every attempt now stamps, so the interval governs the failure path for the first time.
  - **That retry could also silently disable crash-respawn.** It ran a 300s-timeout subprocess synchronously inside the same watcher loop that respawns a crashed daemon, so an unreachable PyPI meant 300s blocked → 60s tick → 300s blocked, indefinitely, with the app unable to notice its daemon had died. The watcher's update now has its own 90s budget (`WATCHER_UPDATE_TIMEOUT_SECS`), bounding that window to ~1–2 missed checks. `bootstrap()`'s first-install path keeps 300s: no runtime exists yet, it must succeed, and it may pull ~100MB. Lowering the cadence created neither defect; it removed the last reason to tolerate them.
  - **Honest limit:** existing installs keep the old shell until they redownload the bundle — `desktop/` changes cannot reach an installed `.app` through pip. The venv's clawmetry still updates normally; it is the shell's own cadence that is frozen until a fresh download.
  - `tests/test_desktop_upgrade_cadence.py` (10 tests) pins the cadence, both guards, the tick-vs-interval relationship, the bounded starvation window, and that `CLAWMETRY_AUTO_UPDATE=0` still short-circuits before any subprocess — polling more often must not erode the opt-out. Each guard verified falsifiable by reverting it in isolation. Blueprint *Desktop Application Distribution* patched to v10 (7 stale "6h" references, ADR-008, and a "known follow-up" the code had already delivered).

- **Release: the post-trial paywall is no longer a lockout, and it quotes the price Stripe actually charges. Carrier `[RELEASE]` so #4873 reaches PyPI and the fleet; pairs with the cloud pin roll and clawmetry-landing#640.**
  - **Why:** 0.12.707 armed the paywall for the first time, which meant the upgrade overlay went from a screen almost nobody saw to the *only* screen a lapsed user sees. Two defects that were harmless while it was inert became blocking.
  - **The overlay could not be scrolled, so its own escape hatches were unreachable.** The container was `position: fixed; inset: 0` with `align-items: center` and no `overflow`. When the card is taller than the window, centering pushes the overflow out of *both* ends of a fixed container, and with no scroller there is no way to reach it. The two controls stranded at the bottom of the card are **"Activate license key"** and **"Continue free with OpenClaw + NVIDIA NemoClaw"** — so on a short window this was not a paywall, it was a lockout: a self-hosted customer holding a valid key could not enter it, and a user who just wanted their free runtimes back could not decline. Fixed by making the container the scroller (`align-items: flex-start`, `overflow-y: auto`, `overscroll-behavior: contain`) with `margin: auto` on the card so it still centres when it fits, plus a vertical padding trim. Card is 872px.
  - **The free-runtime fallback named a runtime the user had just lost.** The label map read `nemoclaw: 'NanoClaw'`. Those are two different runtimes: `nemoclaw` is NVIDIA NemoClaw and lives in `FREE_RUNTIMES`; `nanoclaw` is separate and lives in `PAID_RUNTIMES`. The one line that tells a blocked user what still works was advertising something behind the paywall and never naming the thing they kept. Now `NVIDIA NemoClaw`, matching `RUNTIME_LABELS` and `/pricing`.
  - **Overlay copy brought in line with `/pricing`.** The charged amounts were already correct (`starter 9/90`, `pro 19/190`, matching Stripe's `_SUB_PRICING`) — what was missing was everything around them. Added the struck-through annual anchors, taken from `pricing.html`'s `data-wasyr` (`$190` Starter, `$390` Pro) rather than invented; monthly deliberately carries no anchor because `/pricing` publishes none, and correctly hides the annual-only device line. Subtitles now match `/pricing` verbatim, and the interval pill reads "2 months free" like the public page. The benefit list is now **tier-aware** — previously selecting Pro repainted the price but left Starter's benefits under it, so the Pro card sold Starter. `_selTier`/`_selInterval` moved into module state so the background entitlement poll can no longer reset the user's selection mid-repaint.
  - **New gate (clawmetry-cloud):** the overlay quotes a price and then opens the Checkout that bills it, and nothing enforced that those agree — the license-checkout path has carried a guard for exactly this since the "$190-shown-$290-charged" bug, but the overlay never did. `tests/test_overlay_price_parity_gate.py` reads `PLAN_PRICES` out of the wheel the Dockerfile actually pins and asserts it against `_SUB_PRICING`, so it fires on the pin bump — the moment drift could reach production.
  - **Docs:** `PUBLIC_CLAIMS.md` — the file that calls itself the canonical pricing source — still carried the pre-reprice `$29`/`$290` for Pro and `$290` for Self-Hosted, months after `/pricing` and Stripe moved to `$19`/`$190`. Reconciled in clawmetry-landing#640, with the tiebreaker written down (the **charged** amount wins) and both other surfaces named as greppable anchors so the next reconcile is mechanical.

- **Release: DeepSeek Harness (`dsh`) is the newest paid runtime. Sessions from github.com/deepseek-ai/deepseek-harness (launched 2026-08-13, ~93k stars in its first day) appear in the fleet, sessions, usage, and Brain views like every other harness — zero config. Carrier `[RELEASE]` so #4841 reaches PyPI and the fleet (auto-updates within ~6h); pairs with pro 0.7.6 (clawmetry-pro#136/#137) and the cloud wheel roll (clawmetry-cloud#2004).**
  - **Why:** founder ask 2026-08-14 on `/goal`: "we are going to introduce another paid runtime support" for DeepSeek's new harness. dsh writes the cleanest session format of any runtime we support (documented JSONL event log with inline per-request usage and provider/model provenance), but compresses it with Zstandard by default — and Python ≤3.13 has no stdlib zstd, so naive support would force a compiled dependency onto every Pro install. The founder's constraint: "validate if this harness is detected before installing the dependency."
  - **What:** OSS wiring for the `deepseek_harness` runtime id: adapter spec + detection roots (`$DSH_HOME/sessions`, default `~/.dsh/sessions`) + label in `clawmetry/sync.py`, `PAID_RUNTIMES` + `RUNTIME_LABELS` in `clawmetry/entitlements.py`, probe in `clawmetry/runtime_probe.py` (env `DSH_HOME`), runtime prefix sets in `clawmetry/local_store.py` / `routes/harness.py` / `routes/usage.py`, numbat agent aliases (`deepseek-harness`, `dsh`), frontend label / paid flag / capability caps / flow tile / letter icon in `clawmetry/static/js/app.js`, and verified DeepSeek official API pricing in `clawmetry/providers_pricing.py` (`deepseek-v4-flash` $0.14/$0.28, `deepseek-v4-pro` $0.435/$0.87 per 1M, per api-docs.deepseek.com 2026-08-14). The adapter itself ships in clawmetry-pro (#136): pure-filesystem `detect()`, zstd-frame JSONL reader with torn-tail recovery, format-version refusal (dsh promises breaking changes; version != 0 is skipped, never mis-parsed), and a **detection-gated lazy dependency** — `zstandard` is pip-installed in a background one-shot only after compressed dsh session data is positively detected on the machine, marker-throttled to one attempt/week, degrading gracefully (plaintext sessions still served, `detect().meta.zstd` reports `pending-install`/`unavailable`) until it lands.
  - **Verified:** 15 new adapter tests in clawmetry-pro (fixtures are the dsh repo's own E2E-captured session logs, materialized into the live `--<project-key>--/<id>/session.jsonl[.zstd]` layout; full pro suite 453 passed / 25 skipped) + OSS catalogue drift guard updated (`tests/test_advertised_runtimes_match_catalogue.py` green). Follow-up: /pricing + homepage runtime list in clawmetry-landing must add DeepSeek Harness per the PUBLIC_CLAIMS.md workflow before the count is advertised.

- **Release: `clawmetry uninstall` now drains numbat's agent hooks and removes the managed numbat binary — no harness is left with a hook pointing at a deleted binary.**
  - **Why:** carrier `[RELEASE]`. Founder ask 2026-08-14: "shall we also uninstall numbat when we do clawmetry uninstall? of course, if we had installed it — this also means we update all the hooks where it has registered." This was a latent bug, not just a nice-to-have: `clawmetry secure enable` installs the numbat binary to `~/.clawmetry/bin` and registers hooks (via `numbat hook install --agent all`) inside each harness's own config — Claude Code settings.json, Codex hooks.json, etc. — that reference that binary by absolute path. `clawmetry uninstall` purges `~/.clawmetry` wholesale, deleting the binary while every agent config still pointed at it: the exact stale-hook bug class #4817 fixed for ClawMetry's own runtime hooks, but for numbat's.
  - **What:** new step 1c in `_cmd_uninstall` (`clawmetry/cli.py`) runs BEFORE pip uninstall and BEFORE the `~/.clawmetry` purge (the binary must still exist to run its own uninstaller): `clawmetry/secure.py` gains `managed_numbat()` — the binary counts as ours ONLY when it lives in `~/.clawmetry/bin`; a numbat the user put on PATH themselves is never touched — and `drain_hooks_for_uninstall()`, which shells out to `numbat hook uninstall --agent all` (shared pure `build_hook_uninstall_cmd`, also now used by `clawmetry secure disable`) and never raises: on failure the uninstall continues and prints the exact manual command to run before deleting `~/.clawmetry/bin`. The binary itself is then removed by the existing `~/.clawmetry` purge. The uninstall preview lists the numbat item so the confirm screen is honest about touching agent configs. `--keep-data` skips the drain entirely — that path keeps `~/.clawmetry`, so binary + hooks stay valid for the reinstall-later flow (numbat's durable file sink keeps collecting; only the HTTP sink goes quiet while the dashboard is down).
  - **Verified:** 5 new unit tests in `tests/test_secure_cli.py` (16 total green): uninstall cmd mirrors install scope, PATH-installed numbat is never treated as managed, drain no-ops without a managed binary (asserts subprocess is never invoked), drain runs the exact `hook uninstall --agent all` invocation against the managed binary, and drain failure (nonzero exit AND raised OSError) reports the manual command without raising. `py_compile` clean on `clawmetry/cli.py` + `clawmetry/secure.py`. Docs: `docs/NUMBAT.md` quick-start now documents the uninstall behavior.

- **Release: Runtime-aware session replay foundation. New canonical replay-event schema, `replay_events` DuckDB table, `/api/replay-tree/<sid>` endpoint that groups events into turns / inline delegations / workflow lanes / per-turn approval badges, and a dormant JS renderer skeleton with a runtime dispatcher — the substrate every per-runtime mapper (Claude Code sidechains, OpenClaw subagent+flow DAGs, Antigravity cascades, n8n workflow-first executions, Codex per-turn approval policies, and 13 Pro-repo adapters) will plug into.**
  - **Why:** carrier `[RELEASE]` so #4828 reaches PyPI and the fleet (auto-updates within ~6h). Founder ask 2026-08-14 on `/goal`: "better visibility on when it's creating sub-agents or spawning workflows — what those workflows are doing — sometimes Claude Code spans 40+ workflows; similarly OpenClaw has a different architecture; NanoClaw has different one … we need to represent more accurately as per the respective runtimes." Today's transcript viewer is a single flat runtime-blind renderer — Claude Code Task/Agent fanouts collapse into a truncated tool chip, OpenClaw's purpose-built `acp_replay_events` stream is unused (`grep acp_replay` in the OSS repo returned zero), and per-turn mode changes (`permission-mode`: default/acceptEdits/plan/**bypassPermissions**) are on disk but never surfaced. This release lands the neutral substrate; per-runtime mappers arrive one PR at a time in #4815 (Claude Code), #4816 (OpenClaw), and the 13 Pro adapter issues (#123-#135).
  - **What:** ships #4828 (all three parts squashed). NEW `clawmetry/replay_schema.py`: `ReplayEvent` TypedDict + `ALL_KINDS` enum (`llm.call`/`response`, `thinking`, `tool.call`/`result`, `agent.spawn`/`return`, `workflow.start`/`stage`/`end`, `approval.requested`/`decided`, `mode.changed`, `compaction`) + `ModeChip`/`ApprovalInfo` side-channel dicts + `validate()` with strict "mode field valid only on `mode.changed`" and "approval field valid only on `approval.*`" rules that keep adapters from bloating the store. NEW `replay_events` DuckDB table in `clawmetry/local_store.py` with four indices covering the endpoint's query paths (`session_id, ts` / `parent_span_id` / `runtime, kind` / `created_at`). NEW `query_replay_events(session_id, limit)` LocalStore method that decodes payload/mode/approval BLOBs back to dicts so the endpoint doesn't re-decode. Registered as a new `replay_events` shape (`trust=e2e`, `backing=query_replay_events`) in `clawmetry/query_contract.py` so the drift CI keeps `_SHAPES`, doc, and endpoint in lock-step. NEW `/api/local/replay-events/<sid>` (daemon-proxy) and `/api/replay-tree/<sid>` (tree-builder) endpoints. NEW pure `_build_replay_tree(session_id, rows)` grouping fn in `routes/sessions.py` that folds a flat event stream into nested `{turns[{turn_id, events, delegations, approvals}], workflows, mode, runtime}` — llm.call at session root starts a turn, agent.spawn events pull their children inline under the spawning turn, workflow.start/stage/end group into a workflow lane, approval.* events attach to the tool_call they gated, mode.changed feeds the top-level mode chip (latest wins). NEW dormant JS renderer skeleton in `clawmetry/static/js/app.js` (`window._cmReplayTree.renderTree` + `registerKindRenderer(runtime, kind, fn)` — the runtime dispatcher pattern mirrors the Harness tab template system at `app.js:16729`; per-runtime overrides plug in per (runtime, kind), unknown runtimes fall through to a neutral kind renderer, recursive delegations render inline with `data-depth` for depth-aware CSS). Skeleton is NOT wired into `openTranscriptModal` yet (that lands in #4814 alongside mode+approvals ingest) — manual verification during per-runtime adapter development via `window._debugReplayTree(sessionId)` (creates a floating debug panel). `renderTree` returns false on `row_count=0` so callers fall back to the existing flat `_replayRenderCurrent` path (no dead UI per FLYWHEEL §0a.4). `parent_span_id` is the DELEGATION edge only — NOT the transcript-chain parent (OpenClaw v3 `parentId` and Qwen Code `parentUuid` are chains, not trees; the schema module docstring calls this out to guard adapter authors).
  - **Verified:** 33 Python tests + 12 JS tests all green locally + all 23 required CI checks green on #4828 (Syntax & Lint, API Tests × 3 OS, E2E Gate, Live OpenClaw E2E, MOAT Verifier + Keystone, Eval Suite Gate, Install/boot/health, Wheel install & asset presence, Entitlement API, Compression Safety, Cross-repo handoff, OSS golden path, pip install × 3 OS, PR build). New tests: 11 in `tests/test_replay_schema.py` (kind enum uniqueness/prefix invariants, validator, DuckDB table shape + index presence via a temp DuckDB), 10 in `tests/test_replay_tree_endpoint.py` (query_replay_events empty + populated with BLOB decode, all six branches of _build_replay_tree, endpoint's honest empty shape), 12 JS checks in `tests/replay_tree.test.mjs` (public API surface, empty vs populated renderTree, custom kind renderer wins over neutral fallback, delegation inline rendering — extract-IIFE-and-eval pattern from the existing `brain_sequences.test.mjs`). Two pinned-allowlist tests updated: `test_local_query_dispatch_edge_cases::test_known_shapes_are_exactly_the_allowlist` gains `replay_events`, `test_query_contract_goldens::DISPATCH_ARGS` gains `replay_events` with `session_id="sess-a"`, and the new golden `tests/fixtures/query_contract/replay_events.json` is `row_count=0` (expected until adapter mappers land). Docs: `docs/QUERY_CONTRACT.md` regenerated via `scripts/gen_query_contract_doc.py`. This release lands substrate only — no user-visible UI change yet. The transcript viewer stays on the existing flat renderer until #4814 wires the tree renderer + mode chip + approvals rail; each per-runtime mapper (#4815 Claude Code, #4816 OpenClaw, 13 Pro adapter issues) lights up its runtime's replay data one at a time.

- **Release: TOOL_CALL rows in Brain / Unified Activity Stream now render `Tool(arg preview)` instead of a blank body next to the badge. Every Bash / Read / Edit / Grep / MCP-tool invocation is now visible in the live feed at a glance.**
  - **Why:** carrier `[RELEASE]` so #4822 reaches PyPI and the fleet (auto-updates within ~6h). Founder ask 2026-08-14 on `/goal` with a screenshot of the Activity tab: "why are tool calls not displayed in activity?? fix it." TOOL_RESULT and MESSAGE rows rendered content, but every TOOL_CALL row showed only the badge and source pill — no tool name, no arguments, no way to skim what the agent actually did.
  - **What:** ships #4822. Root cause was in `routes/brain.py::_extract_brain_detail_raw`: the extractor walked `data.message.content`, then a flat-key list (`finalPromptText`/`completionText`/`output`/`result`/`input`/`summary`/`text`/`name`/`content`), then the `data.data.*` mirror, then attachment fields. The v3 mapper writes TOOL_CALL rows with the payload nested under `data.tool_calls[i].{name, input}` (Anthropic / OpenAI-flavoured) with a flat `data.tool_name` mirror, and top-level `data.content` is `""`. None of the existing candidates matched, so `detail` came back empty and the Brain feed's row renderer printed a blank body. Two new helpers in `routes/brain.py` fix it: `_summarise_tool_call_input(inp)` compresses a tool-input dict to a one-line preview using a small primary-key list (`command`, `cmd`, `file_path`, `path`, `filename`, `pattern`, `query`, `q`, `url`, `description`, `prompt`) with generic first-string-value + JSON dump fallbacks; `_summarise_tool_calls(data)` walks `data.tool_calls[]`, joins multiple calls with ` · `, and falls back to the flat `data.tool_name` when the list is absent. Wired into `_extract_brain_detail_raw` right after the message-envelope branch, before the flat-key loop — TOOL_RESULT and MESSAGE rows are unaffected because they carry content in the existing paths.
  - **Verified:** 2 new unit tests in `tests/test_brain_history_v3_event_detail.py` cover the canonical Bash row (`data.content=""`, real `tool_calls` list), Read-prefers-`file_path`, multiple tool_calls joined with ` · `, OpenAI-style `arguments` key, flat `tool_name` fallback, junk-list entries (None / "x" / {} / str-input), and empty `tool_calls[]` falls through. The pre-existing `test_extract_brain_detail_unit_handles_all_shapes` still passes (no regression on message-envelope / v3 top-level / v3 mirror / string-data shapes). Live-verified on the running dashboard: `/api/brain-history?limit=300` returned 96/96 recent TOOL_CALL rows with a non-empty `detail`, and the browser screenshot of the Activity tab shows rows like `Bash(rm _smoke_gate.py)`, `Read(/x/dashboard.py)`, `Edit(/…/brain.py)`, and multi-tool `Read(/a.py) · Read(/b.py)`. All 22 CI checks green on #4822 (Syntax & Lint, API tests × 3 OS, E2E Gate, Live OpenClaw E2E, MOAT Verifier + Keystone, Eval Suite Gate, Install/boot/health, wheel + asset presence, visual-diff, drift-bot, Compression Safety, Entitlement, OSS golden path, pip install × 3 OS).

- **Release: Evals is now Quality. A report card that answers "is my agent doing good work?" in three seconds. Hand-stamped letter grade on a paper card, ranked failure patterns with the $ cost, plain-English rough runs, and an inline "Prevent this →" builder that turns a real trace into a persistent check.**
  - **Why:** carrier `[RELEASE]` so #4824 reaches PyPI and the fleet (auto-updates within ~6h). Founder ask 2026-08-14 on `/goal` after the score-first + drill-down slice (0.12.695) shipped: "what is this really? I'm unable to even understand what is to be done here. Can you please get steve jobs & elon musk involved first to design how evals should be for clawmetry, use claude design skill to brainstorm & create mockups & then implement." The previous release was tactical: rearranged the same page (Recently Scored table, tile grid, Judge card). The founder was right that this stayed inside the old page's shape rather than rethinking what Evals should BE for the newcomer audience CLAUDE.md calls out ("people who have never used one, ordinary people running and managing hundreds of AI agents"). This release starts from a blank canvas.
  - **What:** ships #<new>. Two design perspectives were commissioned in parallel (Jobs = emotional letter-grade metaphor; Musk = cold "what did it cost you" numbers), then synthesized into an HTML mockup ([Artifact link](https://claude.ai/code/artifact/670ec08c-d2dc-4cd8-9623-155b4297f6fa)) that the founder approved before any production code was written. The tab is renamed **"Evals" → "Quality"** in the sidebar and inside; `data-tab="evals"` and every `/api/evals/*` endpoint stay intact for backward compat + muscle-memory. The rewritten tab has four elements, and only four: (1) a report-card hero with a stamped red-pen letter grade on aged paper, one plain sentence ("Your agents did good work this week. 5 rough ones cost you $2.30 and about 18 minutes."), and 7 colored day-dots for the week trend; (2) **What went wrong** panel with ranked failure patterns with count + $ cost + avg duration; (3) **The N rough runs** panel with plain-English one-liners per bad session (no bare session hashes; names come from `sessions.title` or a truncated id, story comes from the outcome enum); (4) a quiet footer that explains the deterministic-signals baseline and offers the LLM-judge upgrade for writing-quality scoring. Every rough run carries a `Prevent this →` action that expands **inline** (not modal) into an eval builder pre-filled with a plain-English "fail-when" clause guessed from the story ("the same tool errors more than 3 times without progress toward the task"). The builder saves via `POST /api/quality/checks` to `~/.clawmetry/quality_checks.jsonl` (chmod 600), returning `{ok, id, deferred_enforcement: true}`; the runner that acts on saved checks ships in the next release, and the UI is honest about that ("Saved locally. Live enforcement lands in the next release."). Backend: new `routes/quality.py` blueprint with `GET /api/quality/report-card` composing existing `query_outcomes` reads across all 17 canonical runtimes, enriched with `query_recent_evals` for optional judge blending. New `clawmetry/quality.py` module holds pure helpers: `grade_for(0..1) → A|B|C|D|F`, `_session_score(row)` blending outcome (60%) + judge (40%), `story_for(row)` mapping outcome enum to a plain-English sentence, and `compute_report_card(rows)` producing the full envelope. Grade never blanks without a judge key, since the deterministic outcome signal carries it. Frontend: `loadEvalsTab` detects the redesigned shell via `data-quality-tab="1"` and calls `loadQualityTab`; on an older cached template it falls back to the legacy renderer, so a cache-stale user never sees a broken tab. All 12 old evaluator tiles + the "Recently Scored Sessions" table + the drill-down drawer from 0.12.695 are removed from this surface (endpoints kept for tests + external callers).
  - **Verified:** 8 tests in `tests/test_quality_route.py` pass: honest empty envelope shape (every key the UI reads is present), grade reflects outcome mix (2/3 success → B or C), all-clean sessions produce "No rough ones", week bucket shape, POST /api/quality/checks rejects empty `fail_when` with 400, valid save persists a JSONL record + returns `{ok, id, deferred_enforcement:true}`, guard that no pattern label leaks ML jargon (eval/rubric/judge/metric/score), guard that `story_for` never returns blank. `py_compile` clean on routes/quality.py + clawmetry/quality.py + dashboard.py. `node --check` clean on the JS. i18n keys added: `nav.quality`, `nav.quality_tooltip`, and 30+ `quality.*` keys for every UI string. Cloud route policy classification and cm-cloud-quality interceptor land in the paired clawmetry-cloud PR. Design provenance: parallel Jobs + Musk fork agents ran, both concepts saved in-session; mockup published as private Artifact; founder green-lit direction ("Yes, ship this") + primary user ("Solo founder / PM") before implementation began. This is the first slice of a longer plan: follow-up releases wire the checks runner (fail-fast on match), add datasets + runs (Braintrust-style diffs), and add a G-Eval plain-English rubric writer.

- **Release: Evals tab reads as a working product, not a wall of tiles. Score-first reorder + clickable Recently Scored rows that open a per-session drill-down drawer with the judge's full reason, per-check breakdown, and rubric.**
  - **Why:** carrier `[RELEASE]` so #4806 reaches PyPI and the fleet (auto-updates within ~6h). Founder ask 2026-08-14 on `/goal`: "there are lot of boxes, but why? recent scored sessions has no way to click on it to understand better, is it just vaporbox or real?" Audit confirmed: only 1 of 12 evaluator tiles (`answer-quality`) drives the Recently Scored table today; the other 11 either need a judge key the user has not given, a Pro plugin that is not registered, or a `pip install` extra. Rows in Recently Scored were dead pills (no `onclick`, no `/api/evals/session/<sid>` endpoint, no drill-down UI), and the Judge setup card was the FIRST thing on the tab, reading as "give us your key first" instead of "here is a working score". Research across Braintrust, Langfuse, LangSmith, Phoenix, DeepEval, and Humanloop found one canonical aha moment: user picks a real trace, sees a score with reasoning inline. ClawMetry starts with 54 real Claude Code sessions already in DuckDB (zero config, no SDK upload), which is a unique advantage the current tab was burying.
  - **What:** ships #4806. Four changes across seven files. (1) Reorder `clawmetry/templates/tabs/evals.html` score-first: Recently Scored + 24h summary sit at the TOP, the Judge card moves to the BOTTOM as a configuration section, so a first-time visitor sees working scored data (or an honest "no scores yet" state) before being asked for anything. (2) Trim the tile grid from 12 to the 4 evaluators that write per-session values (outcome, reliability_score, eval_score, faithfulness_score). The other 8 aggregate-only signals collapse into a `+ N other signals ClawMetry tracks` details toggle so they stay honestly present without dominating the tab. `_entry_view` in `clawmetry/evaluators.py` now exposes `value_field` so the JS can do the split. (3) NEW endpoint `GET /api/evals/session/<sid>` in `routes/evals.py` returns everything the drill-down needs in one shot: judge full reason (not the truncated one-liner the table shows), every per-metric verdict from `eval_metrics`, the rubric text the judge used, the session's outcome + reliability + faithfulness signals, plus cost and tokens. Composed from a new `LocalStore.query_session_eval_detail` (single scalar SELECT on the sessions row) and `LocalStore.query_eval_metrics(session_id=sid)`. Gated `@gate("eval_suite")` for consistency with `/api/evals/recent`. Allowlisted through the daemon proxy so the dashboard never opens the writer-locked DuckDB itself. (4) NEW drill-down drawer in `clawmetry/static/js/app.js` (`openEvalSessionDrawer`, `closeEvalSessionDrawer`, `evalsRescoreFromDrawer`). Recently Scored rows now carry an `onclick` handler that opens a right-side panel with judge reason (full paragraph, not truncated), per-check breakdown as a scannable list with pass/fail colored badges, rubric verbatim in a monospace block, a Re-score button that reloads the drawer in place, and an Open full transcript action that switches to the Transcripts tab. Drawer built on demand from JS (no template change needed beyond the row handler), scrim closes on outside click, self-contained token/cost formatters (the module-level `fmtTokens` / `fmtCost` are function-scoped and unreachable at top level).
  - **Verified:** 64 tests in `tests/test_evals_route_gates.py` + `tests/test_evaluators_catalogue.py` pass. New coverage: grace-mode shape for `/api/evals/session/<sid>` (session and metrics keys present, catalogue label attached, 404 on unknown), enforce-mode 402 matrix extended with the new route, and the paid-route gate count pin bumped 9 to 10. Two pre-existing failures in `test_eval_regression_replay` confirmed on `origin/main`, unrelated. JS syntax check clean via `node --check`. Ruff clean on the three files I edited. Drift-bot flagged 3 Blueprint doc gaps (new endpoint + new query method not yet in the Advanced Evaluation and Automation and Local Observability Service Blueprints), acknowledged in a follow-up sync via the factory.8090.ai dashboard since Blueprints live out-of-repo. Windows API Tests 7 failures were `ReadTimeout` on `/api/system-health` unrelated to this change (same suite passed on macos + ubuntu + Live OpenClaw E2E + OSS Golden Path); Windows retry initiated. Follow-ups planned in the plan artifact: Week 2 Datasets + "Add from trace" from Sessions/Brain/Errors (Langfuse pattern), Week 3 Runs + two-run diff (Braintrust pattern), Week 4 G-Eval plain-English rubric writer + 2 seed golden suites shipped in the wheel.

- **Release: `clawmetry --turn-off-cloud-sync` now actually deletes every trace of your telemetry from the cloud, not just stops future uploads. Founder ask 2026-08-13: "I meant my clawmetry account to sync locally & to stop cloud sync but I still see cloud sync happening — the moment user turns off cloud sync we should delete every trace of it from cloud."**
  - **Why:** carrier `[RELEASE]` so #4799 reaches PyPI and the fleet (auto-updates within ~6h). Founder screenshots on 2026-08-13: `clawmetry status` correctly reported `Cloud sync: ⏸ Local-only (account linked; data stays on this machine)` after `--turn-off-cloud-sync`, but the app.clawmetry.com/cloud page still showed `1 Node · Node registered, syncing sessions… Session data is being encrypted and pushed` with every runtime row showing "Syncing…" and session counts intact. Root cause: the toggle wrote the `~/.clawmetry/nocloud` marker so `is_cloud_disabled()` on the next `_post` short-circuited future pushes, but did nothing about the encrypted snapshots + node_registry row + owner_hash-scoped data that had already landed on the cloud. Meanwhile a snapshot POST that was mid-body-stream at the moment of the flip could still complete (the marker gates the NEXT POST, not the one already on the wire).
  - **What:** ships #4799 (OSS) + clawmetry-cloud #1988 (paired). After writing the marker, `_cmd_cloud_toggle(False)` now (1) bounces the sync daemon (`launchctl kickstart -k` on macOS / `systemctl restart` on Linux) so any in-flight snapshot POST aborts, then (2) POSTs `{"confirm":"PURGE_DATA"}` to `ingest.clawmetry.com/api/account/purge-data` with the account key. That new endpoint (paired cloud PR) auto-discovers every `owner_hash` + email-scoped table from `information_schema` (drift-proof — same discovery `/api/account/delete` uses, catches every future table the day it ships) and DELETEs every row for this owner_hash, WHILE KEEPING the `users` row and Stripe subscription so `--turn-on-cloud-sync` re-enables in one command. Best-effort: local-only is already in effect before the purge call runs, so a network failure / offline machine / older cloud that predates the endpoint doesn't undo the OFF state — the CLI prints a retry hint. Older clouds get a per-node DELETE fallback via `/api/cloud/nodes/<id>` so at least the visible fleet row disappears. Skip flags: `CLAWMETRY_TOGGLE_SKIP_PURGE=1` for marker-only automation; `CLAWMETRY_ENDPOINT` set (self-hosted) skips managed-cloud purge entirely — the operator owns their data plane. Confirmation token is `PURGE_DATA` (distinct from `/api/account/delete`'s `DELETE`) so a mistyped call can't cross-execute.
  - **Verified:** 14 tests in `tests/test_cloud_toggles.py` (7 new): happy-path purge with account key wired through + row counts surfaced, purge-failure surface + local-only still holds, no-account skip, daemon-kick invocation on OFF, wire-shape guard (POST + Bearer + `PURGE_DATA` confirm on the resolved ingest URL), self-hosted opt-out, per-node DELETE fallback on 404. 6 tests in `clawmetry-cloud` `tests/test_account_purge_data.py`: every discovered owner_hash + email table purged EXCEPT `users`, drift-proof for `some_future_*` tables, works without an email, 401/400 auth + confirm guards, happy path returns `{ok:true, purged, kept:["users","stripe"]}`. All 20 pass. Live-verify after this cuts: on the founder's `Macbook-Pro-4.local` node (`cm_20a…a6b3`, account `vivek+13aug757@clawmetry.com`), `clawmetry --turn-off-cloud-sync` → refresh `app.clawmetry.com/cloud` → expect 0 nodes / 0 sessions / no "Syncing…" runtime tiles.

- **Release: fresh cloud signups on the desktop app now actually get the 7-day Pro trial. `clawmetry connect --start-sync-now` stops crashing on an interactive prompt in non-interactive subprocess mode.**
  - **Why:** carrier `[RELEASE]` so #4792 reaches PyPI and the fleet (auto-updates within ~6h). Founder live-hit 2026-08-13 immediately after v0.12.691 shipped: fresh cloud OTP signup via the desktop pane landed with the dashboard showing `Cloud Connected` but `clawmetry status` reporting `Plan: Free` with no trial and paid runtimes NOT syncing. Root cause was in a totally different code path than #4788: `clawmetry connect --key cm_… --start-sync-now` (the subprocess apply_cm_key shells out to) crashed on `EOFError` from an interactive `input()` asking for a custom encryption key — the prompt fired unconditionally on every fresh install (no keychain key, no saved config key). apply_cm_key runs the subprocess with `capture_output=True` (no TTY), input() raises, subprocess dies non-zero BEFORE reaching `_activate_signup_trial` at cli.py:1242, and #4776's `_fallback_persist_cm_key` rescues the pairing but never mints the trial. Net effect: users on v0.12.691 doing a desktop-pane cloud signup landed paired-but-trial-less, same symptom #4788 was supposed to fix but through a completely different failure mode.
  - **What:** ships #4792. Two-part fix. **Part A (root cause):** `clawmetry/cli.py::_cmd_connect` gains a `_non_interactive` gate that fires on `--start-sync-now`, `--keep-local`, or `not sys.stdin.isatty()` — in that mode the three enc-key branches that previously always prompted (`_kc_key`, `_saved_enc_key`, no-key-at-all) silently keep the existing keychain/config key or auto-generate a fresh one. Users can re-key later from Settings if they want a custom secret. `--start-sync-now` was already documented as "skip prompts" so this closes the last hole. **Part B (defense in depth):** `desktop/onboarding.py::_fallback_persist_cm_key` also POSTs `/api/license/trial/signup` and activates the returned license locally, so any FUTURE class of subprocess failure (network, missing binary, permissions) never leaves a user paired-but-Free again. Standalone from `cli._activate_signup_trial` because that reads api_key from `~/.clawmetry/config.json` which the crashed subprocess didn't get to write.
  - **Verified:** 6 new tests in `tests/test_apply_cm_key_fallback_persist.py` — fallback mints trial + activates returned license + exact api_key round-trips; network/broken-import/server-no-key edges never crash pairing; cli.py source guards ensure exactly 3 `if _non_interactive:` branches (one per enc-key path) composed of `--start-sync-now` + `--keep-local` + `not sys.stdin.isatty()`. All 18 pass (6 new + 12 existing) + 38 related connect/OAuth tests still green. Live-verified on founder's machine: rescued the paired-but-Free install by running `echo "" | clawmetry connect --key cm_… --start-sync-now` (empty stdin = auto-generate — same effect the fix now provides silently). Result: `Pro trial active: every runtime unlocked on this machine, 7 days left.`

- **Release: clicking "ClawMetry Cloud" in onboarding now starts the 7-day Pro trial, same as self-host already does. Cloud users experience every runtime unlocked for a week before the paywall.**
  - **Why:** carrier `[RELEASE]` so #4788 reaches PyPI and the fleet (auto-updates within ~6h). Founder ask 2026-08-12 (asap): *"when user clicks ClawMetry Cloud in the onboarding we should start the 7-day Pro trial, same as we do for self-host — users should experience the full product for 7 days so they can start paying after end of 7 days."* Cloud signups landed on FREE with paid runtimes locked while self-host signups got the full 7-day rail — exactly backwards from what converts users to paid after the trial ends. Root cause: only `clawmetry connect` (the CLI + the desktop pane's `apply_cm_key` subprocess) called `_activate_signup_trial` → `/api/license/trial/signup`. Three in-process cloud pairing paths inside the dashboard skipped it entirely: (1) the dashboard cloud modal OTP (`/api/cloud-cta/verify-otp`) only called `_write_cloud_token`, no identity persist, no trial mint; (2) the OAuth loopback bridge cloud rail (`_full_connect_with_key`) persisted identity, enabled cloud, restarted the daemon — but never hit the trial endpoint, while its self-host sibling `_selfhost_signin_with_key` DID mint the trial; (3) any direct caller of `_write_cloud_token`. Net effect: a founder testing with a fresh email account via the browser modal saw `Plan: Free` and every paid runtime locked, with no obvious path from "signed in" to "using the product".
  - **What:** ships #4788. New `dashboard._activate_trial_for_key(api_key)` helper takes the cm_ key directly (so in-process paths don't need to bounce through `~/.clawmetry/config.json` first), returns `'active' | 'expired' | 'unavailable'`, never raises. `_full_connect_with_key` calls it before `enable_cloud()`/daemon restart — return signature grows to `(node_id, enc_key, trial)`, OAuth bridge callback updated to unpack and surface `trial` on `_OAUTH_BRIDGE`. `_selfhost_signin_with_key` replaces its inline trial block with the same helper — cloud + self-host now share ONE trial rail so they can't drift again. `/api/cloud-cta/verify-otp` routes through `_full_connect_with_key` instead of just `_write_cloud_token`, so OTP signups mint the trial too (response body gains `trial`); falls back to `_write_cloud_token` on exceptions so pairing succeeds even if daemon restart / trial mint fails. Desktop pane path unaffected (already went through `clawmetry connect` which already activated the trial) — this closes the parity gap for the browser/OTP/OAuth surfaces only.
  - **Verified:** 6 new tests in `tests/test_cloud_cta_oauth.py` pin: `_activate_trial_for_key` rejects non-cm_ prefixes without touching the network, happy path returns `'active'`, expired trial returns `'expired'` without calling `activate()`, network errors return `'unavailable'` without raising, `_full_connect_with_key` MUST call the helper with the exact cm_ key, `/api/cloud-cta/verify-otp` MUST route through `_full_connect_with_key` (NOT `_write_cloud_token`), and a DRY guard pinning that both cloud and self-host helpers call the same trial helper. All 27 OAuth tests pass (6 new + 21 existing). Related CLI trial tests still green (`test_connect_provisioning_order`, `test_onboard_local_default`, `test_connect_otp_skip`, `test_login_bare_namespace` — 31 pass total). Drift-bot green on the fix PR — the local-seam architecture now matches the Blueprint.

- **Release: the Welcome / cloud-vs-self-host / "please sign in" gate stops re-appearing on every dashboard launch after you already completed cloud onboarding. Both OTP paths now actually pair the local machine.**
  - **Why:** carrier `[RELEASE]` so #4775 and #4776 reach PyPI (and the fleet on the next 6h auto-update). Founder live-hit 2026-08-12, third same-day report: after picking Managed cloud in the desktop pane, entering email, submitting the OTP, and landing on the dashboard, the browser modal re-asked "cloud vs self-host?", the modal below it asked to log in again, and `clawmetry status` reported `Not connected / Daemon Not running / Free` — even though the browser tab at app.clawmetry.com correctly showed the account as PRO. Two independent bugs conspired: (1) the dashboard's cloud modal (`clawmetry/static/js/gw-setup.js::cloudVerifyOtp()`) posted OTP directly to `https://app.clawmetry.com/api/otp/verify` instead of through the local `/api/cloud-cta/verify-otp` seam; cloud minted a `cm_` key, set the browser cookie (hence PRO in the browser), and redirected, but the LOCAL dashboard never received the token, so `_write_cloud_token()` was never called, `/api/cloud-cta/status` stayed `connected:false`, and the onboarding gate stayed `required:true`. (2) The desktop pane's own OTP path derived `signed_in` from `apply_cm_key`'s subprocess exit code, so a good OTP + valid `cm_` key + a failed `clawmetry connect` subprocess (transient network, missing venv binary) → `~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json` got written with `signed_in:false, mode:""` → the dashboard's `_shell_stamp_choice()` returned `""` (per #4763's spec, dismissed panes don't bypass the gate) → gate re-prompted even though the USER actually did complete sign-in. Compounding it, the fresh `cm_` key was thrown away entirely when the subprocess failed, so the machine wasn't just missing daemon-start — it wasn't paired at all. Founder's stuck stamp: `{"completed": true, "signed_in": false, "provider": "email", "email": "vivek+12aug612@clawmetry.com", "mode": ""}`.
  - **What:** ships #4775 (dashboard modal path, in the pip wheel — reaches everyone on next auto-update) and #4776 (desktop shell path, in the .dmg — reaches everyone on next installer redownload). #4775: `cloudVerifyOtp()` now POSTs to the local `/api/cloud-cta/verify-otp` (which persists the `cm_` key via `_write_cloud_token`), then to `/api/onboarding/complete {choice:'managed'}` to write the gate file, enable cloud sync, register the persistent daemon, and reload so the modal never re-fires. #4776: `apply_cm_key` gains a fallback that persists the freshly-minted `cm_` key to `~/.openclaw/openclaw.json` (same path `_write_cloud_token` uses) even when the `clawmetry connect` subprocess fails — machine ends up paired for identity, daemon-start / pro-provisioning retry later. `_write_onboarding_marker` now derives `signed_in` from whether a `captured_key` was actually minted (USER-perspective success), not from the exit code of a downstream subprocess; `mode` unconditionally carries `captured_mode`.
  - **Verified:** 12 new tests in `tests/test_apply_cm_key_fallback_persist.py` pin: subprocess-failure fallback persists the key, `signed_in` derived from key presence not exit code, marker respects the captured mode, existing keys aren't overwritten, malformed cloud responses fall through, corrupted JSON in `openclaw.json` gets replaced. All 35 desktop-onboarding tests pass (12 new + 23 existing). Hot-patched into the founder's local venv and verified end-to-end via a headless OAuth pair: `clawmetry status` now reports `Cloud sync: ✅ Connected, Plan: Trial, 11 runtimes watching`; `/api/onboarding/state` returns `{required:false, source:gate, state:managed}`; the modal did not re-appear on subsequent dashboard loads.

- **Release: Grafana-style date/time-range picker on Activity & Sessions replaces the crude Live/1h/6h/24h/Custom… button strip. Founder ask 2026-08-12: "I need a more polished picker to easily set a date-time range without difficulty — that should be a big selling point."**
  - **Why:** carrier `[RELEASE]` so #4771 reaches PyPI and the fleet. The previous UI on both the Activity (brain) tab and the Sessions (transcripts) tab exposed only 4–5 preset buttons plus a `<input type="datetime-local">` pair for the custom window — the datetime-local input's tiny calendar-icon hit-target is a well-known UX rough edge and the button strip only offered 1h/6h/24h/7d, forcing anyone with a "what happened at 3AM two days ago?" question through the awkward Custom flow. Users doing post-mortem digging or scoping the session list to a business window couldn't do it fluidly.
  - **What:** ships #4771. One reusable `window.cmTimeRangePicker.mount(container, {...})` module (`clawmetry/static/js/time-range-picker.js`) now backs both screens. The trigger is a compact button showing the active window — `● Live` (with a pulsing green dot), `Last 6 hours`, or `Aug 12, 09:00 → 15:00` for absolute ranges. Clicking opens a two-pane popover: labelled `From`/`To` datetime inputs on the left with an `Apply time range` primary button, twelve quick ranges on the right (5 min through 90 days) with `● Live · streaming` pinned at the top. Fixed-position popover so parent-panel `overflow: hidden` can't clip it, outside-click and Esc close, Enter inside either date field applies, per-instance selection persisted to `localStorage` so a page revisit reopens the same window, and a small `N sessions in this window · M hidden` counter renders next to the picker on Sessions. Backend contracts unchanged — the picker's `onChange` forwards to the existing `setBrainTimeRange` / `setTranscriptTimeRange` helpers plus two new absolute-mode entry points (`applyBrainAbsoluteRange`, `applyTranscriptAbsoluteRange`); SSE, density chart, "Viewing history" banner, and the session-active-in-window filter all keep working unchanged. Themed for both light and dark (green `#22c55e` live indicator with pulse animation, `color-mix` accent tints for hover/active states, mobile stack layout under 640px). Legacy `_brainSetRangeActiveBtn` / `_txSetRangeActiveBtn` shims stay in place as no-op-safe when the crude strip is absent so any lingering call sites don't blow up.
  - **Verified:** headless-Chromium smoke test on both screens against a live dashboard — cold-start shows "● Live", picker opens with 13 items (Live + 12 quick), quick pick applies and populates `_brainRange`/`_transcriptRange`, absolute From/To picks apply and produce the human-readable label with a `→`, back-to-live works, no console errors. Sessions counter reads "50 sessions in this window" after picking Last 30 days against a real workspace. `python3 -m py_compile dashboard.py` + `node -c` on both JS files clean. Full PR CI (30 checks including drift-bot, MOAT Keystone, MOAT Verifier's 72 tests, visual-diff, C4 handoff, E2E Gate, entire Sync matrix on 3.11/3.12/3.13) passed on #4771 before merge.

- **Release: fresh desktop installers ship again. `clawmetry.com/download` stops serving a 2-day-stale .dmg that misses every fix cut since 2026-08-10.**
  - **Why:** carrier `[RELEASE]` so #4766 flips the switch on the whole release pipeline. Founder live-hit 2026-08-12: after the .dmg's "Send code" button surfaced the SSL cert-verify error a third time, the real root cause turned out to be that `desktop-artifacts.yml` had been failing on every run since 2026-08-10, so `releases/latest` still pointed at v0.12.681 from that date. Users downloading from clawmetry.com kept getting a build that predates every desktop fix shipped after 2026-08-10, including #4752 (SSL cert verify), #4758 (shell writes the dashboard gate stamp), and the trial-mint reliability work. The chain: PyGObject 3.52+ (pinned at 3.56.3) compiles against `girepository-2.0`; the Linux job installed only `libgirepository1.0-dev`; meson-python errored deterministically; the strict attach step (`needs: [macos, windows, linux]`, `fail_on_unmatched_files: true`) skipped publishing whenever any platform failed; four draft releases (v0.12.682/683/685/686) piled up unpublished behind the wall. macOS and Windows artifacts built successfully every run but sat in workflow-artifacts storage, never attached.
  - **What:** ships #4766. `.github/workflows/desktop-artifacts.yml` now installs `libgirepository-2.0-dev` alongside `-1.0` (older subdeps of `webkit2gtk-4.1` still reference the 1.0 headers). `ubuntu-24.04` (current `ubuntu-latest`) has both in the default archive, so no PPA and no runner pin. This unblocks the standard release-on-merge → desktop-artifacts → publish flow for every subsequent `[RELEASE]`. The four already-cut draft tags need one manual `gh workflow run desktop-artifacts.yml --ref v0.12.<n>` each to rebuild and publish, since release tags don't retroactively re-fire when the workflow they were supposed to trigger is fixed after the fact.
  - **Verified:** PyGObject upstream release notes confirm 3.52 as the girepository-2.0 boundary. `ubuntu-24.04` `apt-cache show libgirepository-2.0-dev` returns a valid package. The workflow YAML parses. End-to-end proof rides this release: after the new tag cuts, one manual `gh workflow run desktop-artifacts.yml --ref v0.12.<new>` should now go green across all three OS jobs, the attach step should run, and `curl -sIL https://github.com/vivekchand/clawmetry/releases/latest/download/ClawMetry-mac.dmg` should redirect to the freshly published tag rather than v0.12.681.

- **Release: any .dmg version stops the "Welcome to ClawMetry / Where should ClawMetry keep an eye on your agents?" gate from re-appearing after you already answered it in the desktop app.**
  - **Why:** carrier `[RELEASE]` so #4763 reaches PyPI and the whole desktop fleet on the next 6h auto-update, regardless of installer age. Founder live-hit 2026-08-12 (second failure of the same day): the previous fix (#4758) taught the desktop shell to also write the dashboard gate's own state file, but `desktop/` code ships only inside the .app bundle (PyInstaller-frozen; confirmed via `setup.py::packages` + `desktop/build_mac.spec`). That means #4758's fix reaches a user only when they download a fresh installer, and every user on any pre-#4758 .dmg still saw the "Welcome to ClawMetry" gate re-appear immediately after finishing shell onboarding, until they redownloaded. The pip wheel auto-updates every 6h; the .app bundle does not.
  - **What:** ships #4763. Mirrors #4758's idea on the pip-wheel side, where it reaches the whole fleet without a new .dmg: `routes/onboarding.py::_resolve_state()` now also reads the desktop shell's own `onboarding-completed.json` (the file the shell has always written, from every .dmg version: macOS `~/Library/Application Support/ClawMetry/runtime/`, Windows `%LOCALAPPDATA%/ClawMetry/runtime/`, Linux `${XDG_DATA_HOME:-~/.local/share}/ClawMetry/runtime/`). If it says `signed_in=True`, translate the stamp to the matching gate choice: new-.dmg stamps carry an explicit `mode` (`cloud`/`selfhost`) and map to `managed` / `selfhost_trial` directly; old-.dmg stamps lack that field, so infer from the `~/.clawmetry/nocloud` marker (the same self-host intent signal `_cloud_connected()` already respects). Dismissed-pane stamps (`signed_in=False`) do NOT bypass the gate, so a user who cancelled shell onboarding still owes a choice in the browser. Precedence stays intent-aware: explicit browser gate file, then active local license, then shell stamp, then cloud token, so trial-then-paid users' state reflects their actual entitlement rather than the historical shell choice. Path shape mirrors `desktop/app.py::_runtime_dir` byte-for-byte, duplicated (not imported) because the pip wheel doesn't ship `desktop/`.
  - **Verified:** new 15-test regression suite `tests/test_onboarding_state_reads_desktop_shell_stamp.py` green (fresh install still prompts, new-.dmg selfhost + cloud recognised, old-.dmg no-mode + nocloud → `selfhost_trial`, old-.dmg no-mode + no marker → `managed`, dismissed-pane stays gated, browser gate file wins over shell stamp, license wins over shell stamp, corrupt/wrong-shape stamps fall through, path shape pinned, and a wire-up guard that fails loudly if a future refactor drops the shell-stamp branch from `_resolve_state`). `pytest -k onboard` sweep 97 passed. Also fixed `tests/test_onboarding_gate.py` fixture: it wasn't isolating the shell stamp path, so on any dev box with the real .app installed the pre-fix fresh-install test silently read the real user's stamp and passed for the wrong reason. End-to-end proof rides this release: on any existing .dmg (pre-#4758 included), the auto-updated dashboard should stop re-showing the gate on the next `clawmetry` restart or the 6h daemon update tick.

- **Release: completing Self-Host in the desktop pane no longer re-prompts you for Self-Host in the dashboard on the very next screen.**
  - **Why:** carrier `[RELEASE]` so #4758 reaches PyPI and the desktop fleet. Founder live-hit 2026-08-12: launched the desktop app, went through the shell's onboarding pane (Continue with GitHub, then chose Self-Host), the daemon booted, the dashboard loaded, and the same "Self-Host / Sign in for a free 7-day Pro trial that unlocks every runtime" modal re-appeared on top of the welcome view, asking to onboard AGAIN. Root cause: two separate onboarding stamp files in two different locations, and only one of them was being written. The shell stamps `~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json` (checked by its own `is_first_launch`, gates the shell's pane on relaunch). The dashboard's gate reads `~/.clawmetry/onboarding.json` (checked by `routes/onboarding.py::_STATE_PATH` via `_resolve_state`). After `apply_cm_key` runs `clawmetry connect --key ... --keep-local`, the dashboard's `/api/onboarding/state` fell through every branch: the choice file did not exist, the trial license had not landed on disk yet (silent `auto_provision_pro` failure, network race, or cloud reject), and `_cloud_connected()` short-circuited on the nocloud marker. So `{required: true}` came back and the modal re-appeared. The user's explicit choice was invisible to the dashboard.
  - **What:** ships #4758. `mark_onboarding_completed` in `desktop/onboarding.py` now takes a `mode` kwarg. When `signed_in` is True AND `mode` is known (`cloud` / `selfhost`), it also writes `~/.clawmetry/onboarding.json` with the matching gate choice (`managed` / `selfhost_trial`), using the exact schema `routes/onboarding.py::_write_choice_file` writes and `_resolve_state` reads. Skipped-auth deliberately does NOT write to the dashboard stamp, so a dismissed pane never lies to the gate that a choice was made. The shell in `desktop/app.py` now passes `mode=(api._captured_mode or "cloud") if ok_key else ""` at the call site.
  - **Verified:** new 8-test regression suite `tests/test_desktop_onboarding_dashboard_gate.py` green (selfhost writes both stamps with `choice=selfhost_trial`, cloud writes `choice=managed`, skipped auth leaves the dashboard gate empty, signed-in-without-mode leaves it empty, unknown mode is ignored, gate choice matches `routes/onboarding.py::_CHOICES`, write failure never raises, gate path shape pinned). Revert-proven: replacing `_record_dashboard_gate_choice` with a no-op reproduces the pre-fix failure mode (`~/.clawmetry/onboarding.json` unwritten). End-to-end proof rides this release: on a fresh .dmg, completing shell onboarding with Self-Host should now boot straight into the dashboard with no re-prompt modal.

- **Release: the desktop app's Self-Host sign-in now actually opens the browser tab it promises.**
  - **Why:** carrier `[RELEASE]` so #4754 reaches PyPI and the desktop fleet. Founder live-hit 2026-08-12: opened the desktop app, hit the Self-Host modal's "Continue with GitHub" (and "Continue with Google"), and the pane sat forever on the "Finish sign-in in the new browser tab" spinner with no browser tab ever appearing. Root cause: the sign-in handler in `clawmetry/static/js/gw-setup.js` calls `window.open(oauthUrl, '_blank')`, and WKWebView (macOS) / EdgeWebView2 (Windows) silently drop `window.open` requests that would need a new native window. The Python bridge to hand external URLs to the system browser (`DesktopAPI.open_external`, shipped in #4752) already existed, but nothing routed the OAuth `window.open` through it, so the URL never left the webview.
  - **What:** ships #4754. On every `window.events.loaded` the desktop shell injects a small shim that overrides `window.open` and intercepts `<a href target=_blank>` clicks for cross-origin `https://` URLs, forwarding them to `window.pywebview.api.open_external` (which already calls `webbrowser.open`). Same-origin and relative URLs (e.g. the `/api/usage/export` CSV download click) are untouched so the webview handles them normally. The shim is idempotent (`window.__clawmetryExternalShim` guard) and reinstalls on every navigation, so daemon-restart reloads and future navigations stay covered. Covers the Self-Host OAuth flow plus every other `target="_blank"` / cross-origin `window.open` link in the dashboard.
  - **Verified:** `python3 -m py_compile desktop/app.py` clean; the injected JS is a syntactic no-op on browsers where `window.pywebview.api` is absent (falls straight through to the original `window.open`), so dashboard-in-browser behavior is unchanged. End-to-end proof rides this release: on a fresh .dmg built from the release tag, opening the desktop app and clicking "Continue with GitHub" in the Self-Host modal should now open the OAuth URL in the default browser and the spinner should clear once the loopback bridge receives the key.

- **Release: the desktop app's "Send code" no longer fails with an SSL certificate error on a fresh install.**
  - **Why:** carrier `[RELEASE]` so #4752 reaches PyPI and the desktop fleet. Founder screenshot 2026-08-12: on the sign-in pane, clicking "Send code" surfaced `network error: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)>`. The desktop shell runs from a PyInstaller-frozen binary whose bundled Python has OpenSSL wired to no CA bundle, so every outbound HTTPS from `desktop/onboarding.py::_post_email_otp` verified against an empty trust store and failed. Sign-in was unreachable through the email OTP path on any first-run install that didn't already have a system-wide CA bundle discoverable by the frozen Python.
  - **What:** ships #4752. New `desktop/onboarding.py::_ssl_context()` resolves the trust store in a three-layer fallback — `truststore` (Python 3.10+; OS-native trust store, honours user-added and enterprise CAs), then `certifi` (Mozilla bundle now bundled inside the .app/.exe via `collect_all('certifi')` in all three PyInstaller specs), then the pre-fix default context (kept so a build without either dep still imports, but the two deps are now pinned in `desktop/requirements-dev.txt` so the fallback stops being reachable in practice). Context is cached at module scope so every OTP retry doesn't re-parse the PEM. `_post_email_otp` passes `context=_ssl_context()` when the target is `https://`; skipped for `http://` so a self-hosted user pointed at a loopback dev endpoint isn't broken by a pointless handshake.
  - **Verified:** new `tests/test_desktop_ssl_trust_store.py` — 6 tests pinning the invariants a future edit could regress (valid SSLContext returned, truststore preferred when importable, certifi fallback populates `ca_certs`, context is cached, HTTPS OTP passes a context, HTTP loopback does not). Reported machine's failure mode is exactly reproducible from a fresh venv with certifi absent, and green after the fix; the same POST in the same shell now returns a normal `{"ok": true}` OTP send response.

- **Release: dragging ClawMetry.app to Trash no longer leaves the user auto-signed-in on the next install.**
  - **Why:** carrier `[RELEASE]` so #4745 reaches PyPI and the desktop fleet. Founder support thread 2026-08-12: deleted `/Applications/ClawMetry.app`, expected a fresh install to prompt for sign-in, saw the dashboard boot straight into the previous account. Root cause: `.app` removal only takes the bundle. The thin-shell runtime venv under `~/Library/Application Support/ClawMetry`, the DuckDB local store under `~/.clawmetry`, the OpenClaw sidecar files (`~/.openclaw/clawmetry.db*`, `.clawmetry-fleet.db*`), and — critically — the `clawmetry.cloudToken` key in `~/.openclaw/openclaw.json` all persist, and the reinstall's bootstrap reads that token before the user sees the login pane. macOS has no OS-level uninstall hook (Windows MSIs run one, Debian `apt purge` runs `postrm`; drag-to-trash runs nothing), so the fix has to live in the app itself.
  - **What:** ships #4745. Three layers so drag-to-trash Just Works. (1) `clawmetry uninstall` now removes the thin-shell runtime dir (per-OS: `~/Library/Application Support/ClawMetry` on macOS, `%LOCALAPPDATA%\ClawMetry` on Windows, `~/.local/share/ClawMetry` on Linux), the OpenClaw sidecar files ClawMetry owns, and strips ONLY the `clawmetry` key from `~/.openclaw/openclaw.json` (the rest of the file belongs to OpenClaw; deletes the file entirely if our key was the sole content). New flags `--yes` / `-y`, `--unattended` (silent, always exit 0), `--keep-data` (preserve DuckDB + `history.db`), `--dry-run`. (2) New "Uninstall ClawMetry…" item in the desktop app's own menu — confirms via a JS dialog, stops the daemon, shells out to the venv's `clawmetry uninstall --yes`, then quits the window. (3) A macOS `com.clawmetry.app-watchdog` LaunchAgent installed at desktop bootstrap: every 5 minutes plus once on load, checks whether the `.app` is gone but the runtime dir survives; if so, invokes `clawmetry uninstall --unattended`. Two-layer teardown so a half-broken venv can't strand state — primary path uses the CLI, fallback is inline shell (`rm -rf`, `/usr/bin/python3` to strip the token, `launchctl bootout` to remove itself). Skipped when `sys.frozen` is unset (dev mode never drops a plist pointing at a developer checkout), and the plist watches the actual bundle path from `sys.executable` rather than a hardcoded `/Applications/ClawMetry.app` so non-standard install locations still work.
  - **Verified:** new `tests/test_uninstall_drag_to_trash.py` (7 tests: strip preserves other keys, deletes empty file, no-op when key absent, dry-run enumerates the runtime dir + token strip, plist is valid via `plutil -lint` and its shell command via `sh -n`, dev-mode watchdog no-op) green alongside the existing 7 uninstall tests; broader `pytest -k "uninstall or cloud_token"` sweep 27 passed. End-to-end proof rides this release: on a machine that installed a pre-fix desktop build, dragging the `.app` to Trash and waiting 5 minutes should now leave `~/Library/Application Support/ClawMetry` gone, `clawmetry.cloudToken` stripped from `~/.openclaw/openclaw.json`, and a reinstall's first launch presenting the sign-in pane instead of the previous account.

- **Release: the Claude Code approval hook no longer pops console windows on Windows.**
  - **Why:** carrier `[RELEASE]` so #4717 reaches PyPI and the fleet. Founder live-hit 2026-08-10 on the Windows lab machine: terminal windows kept popping up over the desktop app. The PreToolUse approval-gate hook command is built from `sys.executable`, the venv's console-mode `python.exe`; when Claude Code runs under a windowless parent (the desktop app), every gated tool call (Bash, WebFetch, WebSearch) makes Windows allocate a visible console for the hook process, and a call parked for approval keeps that window on screen until the human decides (hook timeout is the policy window plus buffer, up to 7 days).
  - **What:** ships #4717. `_hook_command()` swaps `python.exe` for the adjacent `pythonw.exe` (GUI subsystem, never allocates a console) via a pure helper `_windowless_python()`. Non-Windows installs and venvs without `pythonw.exe` are untouched; existing installs self-heal because the gate installer refreshes any marker-matched entry whose command differs on the next watcher tick.
  - **Verified:** 23 tests green in `tests/test_runtime_gates_and_hooks.py`, new assertions revert-proven (red on the un-fixed module); live on the reporting machine the patched gate rewrote the real `~/.claude/settings.json` entry to the pythonw command, and the hook client was exercised under pythonw with explicit pipes (the spawn shape Claude Code uses): stdin/stdout round-trip works and the fail-open contract holds (rc=0, no output, no window).

- **Release: a daemon restart can no longer re-send the "trial ending" warning on the same day.**
  - **Why:** carrier `[RELEASE]` so #4714 reaches PyPI and the fleet. The daemon throttles `POST /ingest/trial-warning` (the trigger for the "your trial ends in N days" customer email) with an in-memory once-per-UTC-day guard only. Auto-update restarts the daemon on every release, often several times a day, and each restart reset the guard and re-fired the POST. 2026-08-10 trial-email spam RCA: one account received 5+ "trial has ended" emails in a single day. Cloud-side dedup landed in clawmetry-cloud #1970; this is the daemon-side half, so the duplicate request never leaves the machine at all.
  - **What:** ships #4714. The warned day is now persisted to `~/.clawmetry/trial_warnings.json`, the same `{"YYYY-MM-DD": days_left}` file the dashboard's `/api/trial/mark-warned` endpoint already writes, so either writer suppresses the other. A fresh daemon process checks the file before POSTing and primes its in-memory fast path from it. Both new helpers never raise: corrupt or unwritable state files fail open (warn once, repair where possible), keeping the heartbeat path crash-proof.
  - **Verified:** new 6-test regression suite `tests/test_trial_warning_restart_persist.py`, including the core restart case (fresh module import against the same state file must not re-POST); revert-proven (6 red with the sync.py fix stashed, green restored) alongside the existing `test_sync_trial_gating.py` suite, 19 tests green total.

- **Release: the desktop app's background updates now respect the update kill switch and stability window.**
  - **Why:** carrier `[RELEASE]` so #4706 reaches PyPI and the desktop fleet. The desktop shell's 6h auto-upgrade shelled the venv's `clawmetry update`, a bare pip upgrade that read neither `CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS` nor `CLAWMETRY_AUTO_UPDATE`, and the shell's own pre-check only recognized the literal `0`. An operator who configured a stability window or the kill switch (both documented, both honored by the daemon's updater) still had every desktop install jump straight to the newest wheel. Tracked as a known follow-up in the Desktop Application Distribution blueprint.
  - **What:** ships #4706. New `clawmetry update --unattended` flag: target selection defers to the daemon's own policy helpers in `routes/update_check.py` (kill switch including implicit CI disable, stability window, newest aged-in release) and pins the install to that version; when nothing may be installed it installs nothing, and an unevaluable policy fails closed. The desktop shell passes the flag, aligns its kill-switch pre-check with the daemon parser (false/no/off and CI, not just `0`), and keeps a one-shot plain-update fallback strictly for venvs predating the flag so bootstrap still works. Plain interactive `clawmetry update` is unchanged.
  - **Verified:** 84 tests green (new `tests/test_cli_unattended_update.py` and `tests/test_desktop_unattended_update.py` plus the existing aged-in selection suite), including a parity matrix pinning the shell's parser to `routes/update_check.py::_env_auto_update_disabled`; revert-proven (79 red on the un-fixed code, green after).

- **Release: desktop download links no longer 404 while a release is being cut.**
  - **Why:** carrier `[RELEASE]` so the draft-until-attached release flow governs the next cut. Founder live-hit 2026-08-10: clicking any desktop download button on clawmetry.com returned a GitHub 404. The buttons resolve through GitHub's `releases/latest/download/<fixed-name>` convention, but release-on-merge published the v0.12.674 GitHub Release at 22:32 UTC, minutes before desktop-artifacts finished building and attaching the installers at 22:35, so the empty release became "latest" and every download link 404'd for the whole build window. Worse, partial uploads were tolerated (`fail_on_unmatched_files: false`), so one failed installer job would have left its platform's link broken until the next release.
  - **What:** ships #4699. `release-on-merge.yml` now pushes the release tag explicitly (draft releases do not create tags, and the desktop-artifacts dispatch needs the ref) and creates the GitHub Release as a draft; drafts are invisible to `releases/latest`, so downloads keep serving the previous complete release while installers build. `desktop-artifacts.yml` attaches all assets and publishes the release in the same step, marking it latest only then, and now refuses to publish when any of the five installer patterns is missing: a broken desktop build keeps the release draft instead of shipping dead links. PyPI and the cloud pin are unaffected either way; they key off PyPI, not the GitHub Release.
  - **Verified:** root cause confirmed in the live v0.12.674 run logs (release published 22:32:26Z, all ten assets attached 22:35:38Z, matching the founder's 404 screenshot in between); all three fixed-name download URLs re-checked at HTTP 200 once assets landed; both workflows YAML-parse clean. End-to-end proof rides this release: after merge, confirm the new release appears as draft first, flips to published latest only after desktop-artifacts completes, and the three download URLs never 404 during the window.
- **Release: the self-updater cleans up after itself — stale version metadata no longer accumulates, and a failed update hand-off no longer stalls the fleet for 15 minutes.**
  - **Why:** carrier `[RELEASE]` so #4702 reaches PyPI and the fleet. Observed live on a Windows lab machine 2026-08-10: every in-place pip upgrade run while a sibling clawmetry process held `.pyd`/`.exe` files open half-failed its uninstall of the previous version, leaving that version's `clawmetry-*.dist-info` behind — five stale ones (0.12.655–0.12.669) sat alongside the current install. `importlib.metadata` resolves the FIRST matching dist-info in directory-listing order (alphabetical on NTFS), so the OLDEST stale version won every metadata probe and pip ran uninstalls against the wrong RECORD. Separately, the same box sat 12+ minutes behind a fresh release: the Windows respawn path leaks `~/.clawmetry/update-in-progress.lock` when the helper hand-off fails or the helper aborts because the parent never exited, and every subsequent 60s check then silently skips ("another process is updating") until the 900s staleness window breaks the lock.
  - **What:** ships #4702. New `clawmetry/distinfo_cleanup.py` removes `clawmetry-*.dist-info` dirs strictly older than the installed version plus `~lawmetry*` pip-uninstall corpses (newer-than-current metadata is deliberately kept — that's the just-upgraded-but-not-yet-restarted window); wired at update-check worker boot (daemon and dashboard roles) and after a successful `perform_self_update`. The Windows out-of-process helper (`update_respawn.py`) runs its own stdlib-only prune after pip succeeds and now releases the update lock when it aborts; `routes/update_check.py` releases the lock and records a `failed` attempt when the respawn hand-off itself fails. The desktop shell's `_get_installed_version` picks the highest parsed version instead of newest mtime, since a partially-uninstalled stale dir can carry a fresher mtime than the real install.
  - **Verified:** 7-test regression guard `tests/test_stale_distinfo_cleanup.py` (cleanup semantics, metadata resolution, source-checkout no-op, ghost-install case, wiring pins into `perform_self_update` and the worker boot) green alongside the existing self-update suites; end-to-end on a real venv seeded with the five observed stale dist-infos plus a `~lawmetry` corpse, `importlib.metadata.version` reproduced the bug (0.12.655) before cleanup and returned the installed 0.12.674 with only the current dist-info remaining after, with a second pass confirming idempotence.

- **Release: the desktop install carousel draws its slides as crisp vector art instead of raster screenshots.**
  - **Why:** carrier `[RELEASE]` so #4697 reaches the desktop installers. Founder feedback 2026-08-09 on the first-run carousel: the slide images look bad. The slides showed downscaled PNG screenshots of the landing site (shipped in the previous carousel release) plus a remote device-square.png fetch for the Desk slide. A shrunken website screenshot tells a new user nothing and reads as cheap, and the remote fetch broke the pane's own contract of no external assets and no network beyond loopback.
  - **What:** ships #4697. Each slide's art is now a purpose-built inline SVG in the brand palette: the hero slide is an idealized in-app render of the dashboard (window chrome, stat tiles, spend chart, per-model bars, live session rows), the builder slide a blueprint scaffold, the Desk slide the device with approve and deny pills on its screen, the enterprise slide an identity ring feeding a shield with a check. The art stage is frameless with a soft drop shadow. The four bundled screenshot PNGs, their PyInstaller bundling blocks, the remote img fallback, and the emoji fallback map are all removed; the pane is fully self-contained again. The keep-local self-host guard and the carousel CTA pointer-events fix from previous releases are untouched.
  - **Verified:** all four slides rendered and screenshotted in a browser at 1250x800; new guard `tests/test_desktop_carousel_art.py` is revert-proven (red at collection on the pre-fix code, green after) and pins: vector art for every slide, no raster art keys, well-formed SVGs with no embedded or external images, and a self-contained carousel payload (data URIs only).

- **Release: the desktop Self-host choice now actually keeps data on the machine.**
  - **Why:** carrier `[RELEASE]` for the keep-local connect fix. Founder live-hit 2026-08-09: choosing Self-host in desktop onboarding ran `connect --key cm_ --defer-sync`, but `--defer-sync` only skips the daemon start. The connect still rode the full cloud rail (`enable_cloud()`, family-mark reset), never wrote the local-only marker, and the shell then started `clawmetry sync` itself, so a machine whose user explicitly chose "data stays local" pushed snapshots to cloud and showed a green "Cloud Connected" badge.
  - **What:** ships #4694 plus #4692. New `clawmetry connect --keep-local` flag mapping to the existing keep-local rail: the local-only marker is written up front (the daemon must never observe a cm_ key without it), `enable_cloud()` is never called, the ownership OTP is skipped (the key comes from the shell's own OAuth loopback, the same authenticated provenance as `--start-sync-now`, and the subprocess runs headless where a prompt would hang onboarding), and automated `--key` invocations no longer spawn a stray port-8900 dashboard next to the shell's own. Desktop onboarding's selfhost mode now passes `--keep-local --defer-sync`. Complements the sign-in guard released in 0.12.672: that one stopped the profile-menu sign-in from flipping egress on; this one stops the original onboarding choice from being dropped.
  - **Verified:** new `tests/test_connect_keep_local.py` (marker written and cloud rail skipped on keep-local, cloud rail intact on plain connect, parser and desktop wiring pins) plus the existing connect suites, 9 tests green; on the reporting Windows machine the unwanted egress was switched off live via the sync toggle and confirmed `local_only: true`.

- **Release: the desktop install carousel's buttons open the page they name, and each slide shows a real screenshot of it.**
  - **Why:** carrier `[RELEASE]` so #4686 reaches PyPI and the fleet. Founder report 2026-08-09: on the desktop install carousel, clicking "Explore Agent Builder" opened clawmetry.com/device instead of build.clawmetry.com. The four slides are stacked with position:absolute and inactive ones were hidden with opacity alone, which leaves them clickable; the Desk-device slide is painted on top, so its invisible CTA swallowed clicks meant for the visible Agent Builder button.
  - **What:** ships #4686. Inactive slides are now visibility:hidden plus pointer-events:none (the cross-fade is preserved with a delayed visibility transition), so only the visible slide can be clicked. Slide art is upgraded from emoji placeholders to bundled screenshots of the actual target pages (clawmetry.com, build.clawmetry.com, the Desk device page, the Enterprise page), embedded as data URIs so the pane stays fully self-contained, Ubuntu-installer style; emoji art remains the fallback when an asset is missing. All three PyInstaller specs bundle the new screenshots.
  - **Verified:** headless-Chrome hit-test on the rendered pane confirms the element under the Agent Builder CTA now fires open_ext('https://build.clawmetry.com'); slides 1 and 2 rendered and eyeballed with the real screenshots in place; desktop/onboarding.py compiles clean.

- **Release: signing in can no longer switch a self-host install to cloud sync.**
  - **Why:** carrier `[RELEASE]` so the sign-in egress guard reaches PyPI and the fleet. Founder report 2026-08-09: a self-host machine (egress off by choice) hit the "Not signed in" identity bug, so the user signed back in from the profile menu. That entry opens the cloud-CTA modal, whose OAuth start defaulted to the managed rail; the connect then called `enable_cloud()`, deleted the local-only marker, and the node silently started pushing snapshots, with the header flipping to a green "Cloud Connected" on a machine whose whole promise was local-only.
  - **What:** ships the sign-in guard PR. `dashboard.py` gains `_selfhost_intent()` (local-only marker or a recorded selfhost onboarding choice). `/api/cloud-cta/oauth-start` with no explicit mode now resolves the rail from that intent, so a self-host install signing back in rides the identity-only selfhost rail; explicit modes always win. The profile menu's "Sign in / Create account" passes the new signin intent, while the "Enable Cloud Sync" CTA, the onboarding cloud card, the e2e-key modal, and alert sign-up CTAs keep sending an explicit managed mode: clicking those IS the egress opt-in. Identity and egress stay separate choices, per the onboarding gate's own contract.
  - **Verified:** 59 tests green across the profile-menu, OAuth-CTA, and onboarding-gate suites (new: intent resolution matrix, `_selfhost_intent` signal tests, JS wiring pins); on the reporting machine the unwanted egress was stopped live via the sync toggle (`local_only: true` confirmed) and the served endpoints re-checked.

- **Release: the profile menu shows who you are on cloud-OAuth sign-ins instead of "Not signed in".**
  - **Why:** carrier `[RELEASE]` so #4680 reaches PyPI and the fleet. Founder report 2026-08-09: a fully signed-in, cloud-connected node (GitHub OAuth) opened the avatar menu to "Not signed in" rendered directly above Billing & plan and Sign out. The menu's only identity source was the license `sub`; a cloud-OAuth account with no local license file has none, so the header fell through to the signed-out label while the signed-in items still rendered.
  - **What:** ships #4680. `dashboard.py` gains `_account_email_for_token()`: it resolves the sign-in email behind a cm_ key from `~/.clawmetry/config.json` (`account_email`, trusted only when keyed to this token) with a cached, best-effort fallback to the cloud's `/api/cloud/account`, persisting the result back when it belongs to the same key; internal placeholder identities (`agent+*@clawmetry.auto`, `.linked`) are never shown. Connect flows now store `account_email` at pairing time. `/api/cloud-cta/status` returns `account_email`; the profile menu falls back to it for `who`, and a signed-in menu whose email is unresolvable (offline, pre-claim) now says "Signed in", never "Not signed in". Also fixes a latent guard bug: the profile i18n-key regex truncated `profile.e2e_key` to a bogus `profile.e`, leaving `test_profile_menu.py` red on main.
  - **Verified:** 56 tests green across the profile-menu, OAuth-CTA, and onboarding-gate suites (including the previously red i18n guard); live on the reporting Windows machine, `_account_email_for_token(_read_cloud_token())` resolved the real account email for the exact token that reproduced the bug.
- **Feature: the trial paywall's "Continue to payment" goes straight to per-account Stripe checkout, and the dashboard unlocks itself after payment.**
  - **Why:** founder feedback 2026-08-09 (desktop trial-ended modal): the user is already signed in locally, so the payment CTA should open Stripe checkout for that account, charge, and activate Pro/Starter with no license key to paste. Instead the CTA opened the generic upgrade page. Root cause was a cross-process bug: the per-account URL the cloud attaches to heartbeats was cached only in the sync daemon's memory, which the dashboard process can never see, so `resolved_upgrade_url()` only ever saw module defaults.
  - **What:** ships #4679. New `POST /api/trial/checkout` (allowlisted while hard-blocked) asks the cloud to mint a per-account Stripe Checkout Session (`POST /api/billing/checkout-session`, node api_key auth), falling back to the heartbeat-cached `checkout_url`, then the generic upgrade page: always HTTP 200 with a usable URL, so the button never dead-ends on an older cloud. The daemon now persists heartbeat `{upgrade_url, checkout_url}` to `~/.clawmetry/trial_state.json` for the dashboard process to read. The overlay CTA opens the checkout tab synchronously (popup-blocker safe), redirects it to the minted session, then polls the refresh endpoint every 5s for 10 minutes, so the license the cloud attaches to the next heartbeat unlocks the dashboard within seconds. The 402 payload and `/api/trial/status` now advertise `checkout_endpoint` and `checkout_url`. The cloud endpoint ships separately in clawmetry-cloud; until then the button degrades exactly as before.
  - **Verified:** 9 new guard tests in `tests/test_trial_checkout.py` (fallback chain, live session mint with URL and auth-header assertions, cloud failure never 500s, daemon-to-dashboard persistence, env override, corrupt state file); `node` syntax check on app.js; full 31-check CI matrix green on #4679. Software Factory blueprint synced (Local Agent Observability: new TrialHardBlockPaywall component, contracts, ADR-002).

- **Fix: Sessions tab blanked for anyone with sessions (shipped in 0.12.669).**
  - **Why:** founder report 2026-08-09: the Sessions tab is blank for ANY user with at least one session: the row loop's `function(t)` parameter shadows the global i18n `t()`, and the Score button inside the loop calls `t('transcripts.score_btn', ...)`, so the first row throws and the catch paints "Failed to load transcripts". The API is unaffected; only the render dies.
  - **What:** #4675: param renamed to `tx`, plus an auto-discovering guard test (`tests/test_app_js_t_shadowing.py`) that fails CI if any callback shadowing `t` calls i18n inside its body. Reached PyPI in 0.12.669 (carried by the #4676 release).
  - **Verified:** guard revert-proven (red on pre-fix main at app.js:16031, green after); fix injected into the live 0.12.667 dashboard on the founder's Windows box rendered all 9 session rows where the tab was blank; the published 0.12.669 wheel cracked and confirmed to carry the fixed loop.

- **Fix: Notifications sits directly under Approvals and Alerts again; nav guard synced with the shipped Evals and Gateway tabs.**
  - **Why:** the Phase-A nav guard (`tests/test_beginner_nav_phase_a.py`) was red on main. Two shipped nav changes had drifted past it: #4295 added the top-level Evals tab but inserted it between Alerts and Notifications, breaking the founder request (2026-07-29) that Notifications sit directly under its two consumers, and #4575 added the opt-in Gateway tab to the Developer drawer without updating the guard.
  - **What:** Evals moves below Notifications so the Approvals, Alerts, Notifications trio is contiguous again (both tabs stay; membership was intentional in both releases). The guard now encodes the nine-item Tier-1 order and the Gateway drawer membership.
  - **Verified:** revert-proof (guard red on the pre-fix nav, green after the reorder), all 8 module tests pass, other tab guards are membership-only and unaffected.

- **Fix: persistent console window after Windows self-update (Release: carrier).**
  - **Why:** 0.12.667 made the self-updater's pip run windowless, but the RELAUNCHED daemon still popped a console — permanently. Founder report 2026-08-09: a Windows Terminal tab titled with the venv exe path, open forever. Root cause reproduced live: every daemon-(re)spawn path used DETACHED_PROCESS (parent gets NO console), and on Windows a console-subsystem child of a console-less parent allocates a fresh VISIBLE console — the pip-launcher clawmetry.exe re-execs python.exe workers, so the relaunched daemon's workers each owned an on-screen console for the daemon's lifetime.
  - **What:** every Windows daemon-spawn site now uses CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP (a hidden console all descendants inherit) instead of DETACHED_PROCESS: update_respawn.py relaunch, routes/update_check.py helper spawn, daemon_registration.start_background_subprocess, and both cli.py fallback spawns. Same terminal-detach and Ctrl+C-isolation semantics, zero visible consoles.
  - **Verified:** reproduced on the founder's Windows 11 box with a minimal probe: a sleeping python child of a DETACHED parent created a visible console titled with the python path (matching the reported window); the identical child under CREATE_NO_WINDOW created none. All four files compile; the live windowed daemon was killed and respawned hidden by the desktop shell.

- **Release: roughly 80x faster fresh-install ingest (bulk flush, pre-insert integrity chain, per-batch hooks, batch session/span APIs).**
  - **Why:** carrier `[RELEASE]` so #4669 reaches PyPI and the fleet. Fresh installs ingested at about 19 events/s end to end: a 1000-event flush took about 53s, and a first run with hundreds of sessions left the dashboard empty for hours. Three compounding root causes on the local store write path: (1) duckdb's Python parameter binding retries a failed `import pandas` for nearly every bound value, and CPython never caches a failed import, so each attempt re-scans sys.path (a 1000-event flush spent about 45 of its 48 seconds inside roughly 28,000 failed pandas imports); (2) the flush inserted row by row and then re-UPDATEd every fresh row to stamp the integrity chain, a delete plus reinsert against all six secondary indexes per event; (3) the disabled SIEM/OTLP hooks paid a failed `clawmetry_pro` import per event (about 4.4ms each).
  - **What:** ships #4669. Negative-cache the pandas miss (`sys.modules` sentinel, applied only when pandas is genuinely absent, opt out with `CLAWMETRY_NO_IMPORT_NEGATIVE_CACHE=1`); compute the tamper-evident hash chain in Python before insert (same scheme and ordering as before, byte-for-byte) and fold it into one chunked multi-row VALUES insert inside the existing transaction; resolve redaction/SIEM/OTLP enablement once per batch in `ingest_many`; new `ingest_sessions_batch` and `ingest_spans_batch` APIs (one lock hold, one transaction per batch) wired into the sync daemon's session mirror and family-runtime span reconstruction. Also fixes a latent chain-fork on flush retry: the in-memory chain head now advances only after COMMIT. Writer-lock design, ring pop-after-commit, INSERT OR IGNORE dedup, rollup exactly-once counting, redaction behavior, and the DuckDB thread/memory caps are unchanged.
  - **Verified:** guard suite `tests/test_ingest_bulk_flush.py` (17 tests): the perf guard (5000-event ingest plus flush under 10s) proven red on un-fixed main (356.8s) and green post-fix (4.5s, about 1100 events/s) on the same Windows machine; integrity chain byte-for-byte parity with the legacy stamping for a fixed multi-node sequence, `verify_integrity()` valid across redelivery and restarts; related suites (local store, integrity, rollups, spans, sync integration, family ingest, crash recovery) diffed against origin/main with zero new failures. Full 28-check CI matrix green on #4669 including Live OpenClaw E2E and the MOAT verifier.

- **Feature: rename the Conversations tab to Sessions (shipped in 0.12.667).**
  - **Why:** "Sessions" is the normal term across every harness we observe (Claude Code, Codex, Cursor, OpenClaw), and the tab is where you dig deep into sessions; "Conversations" was the odd one out.
  - **What:** #4656: nav label, tooltip, and in-tab copy (time-window tooltip, empty state, inventory work count) now say session(s). The `data-tab="transcripts"` id and `nav.session_replay` i18n key are unchanged, so deep links and stored state keep working. Only `en.json` changes by hand; the autotranslate workflow fanned the other locales out in #4665. Reached PyPI in 0.12.667 (carried by the #4666 release) and app.clawmetry.com via the cloud pin bump (clawmetry-cloud #1960).
  - **Verified:** full CI matrix green on #4656 (31 checks incl. drift-bot, Live OpenClaw E2E, visual-diff); the published 0.12.667 wheel cracked and confirmed to carry the rename before pinning cloud.

- **Release: ship windowless self-update, self-healing sync daemon, global CLI, and trial-expiry banners to end users.**
  - **Why:** carrier `[RELEASE]` so #4657 reaches PyPI and the fleet. Until this ships, every unattended Windows self-update pops a visible cmd window (seen live during an enterprise client call 2026-08-08), fresh installs that skipped sign-in show an empty dashboard forever, and desktop users have no `clawmetry` on PATH.
  - **What:** no new code; ships #4657.
  - **Verified:** end-to-end this release - after PyPI publish, confirm the founder's Windows 11 desktop install auto-updates to the new version (one final visible pip window from the old helper is expected), then confirm the NEXT update check produces zero visible console windows, `clawmetry --version` works in a fresh terminal, and the dashboard shows sessions with the sync daemon healed by the shell.

- **Fix: mystery cmd windows flashing on Windows during self-update.**
  - **Why:** founder report 2026-08-08 — console windows popping open and closing on their own, including during a call with an enterprise client. Traced live with a process-creation monitor: (1) `clawmetry/update_respawn.py` runs detached (no console), so the `pip install` child it spawns without `CREATE_NO_WINDOW` gets a brand-new VISIBLE console for the whole seconds-to-minutes install — this fires on every real unattended update, and the fleet updates constantly; (2) a dashboard running from a source checkout can never version-converge (pip installs to site-packages, the process re-runs the checkout), so the Windows respawn plan looped forever — exit → pip → relaunch → still stale — flashing 3-4 windows per minute.
  - **What:** `update_respawn.py` runs pip with `CREATE_NO_WINDOW`; `routes/update_check.py` gains `_running_from_source_checkout()` (`.git` next to the package) and `_maybe_auto_update()` refuses to fire there, logging why.
  - **Verified:** reproduced the respawn loop live (process monitor caught `update_respawn` → pip → relaunch cycling at ~70s), killed it, applied the guard, then watched for visible `ConsoleWindowClass` windows for 120s spanning two watcher ticks: none appeared.

- **Fix: desktop shell owns the sync daemon — a fresh install shows data instead of an empty dashboard.**
  - **Why:** the shell only started the sync/ingest daemon in one narrow path (a cm_ key captured during first-launch onboarding). Skip sign-in, or connect later via CLI, and local ingest never ran: every page sat on its empty state while banners told a desktop user to go run `clawmetry status` in a terminal. Confirmed live on the founder's Windows box 2026-08-08 — a connected node with 4 Claude Code sessions on disk showed $0.00 everywhere because the daemon had died at 15:01 and nothing restarted it (schtasks registration had also silently failed, so there was no supervisor at all). Founder expectation: install → sign in → see every runtime, no terminal.
  - **What:** `desktop/app.py` — (1) `ensure_sync_daemon()`: liveness-probe the daemon via `~/.clawmetry/local_query.json` (PID alive + query-server port accepting), and if dead run the venv's `clawmetry sync`; called off the boot path at launch and from every watcher tick, with a 300s retry floor. Independent of cloud sign-in — local ingest is the product. (2) Single-instance guard: `start_daemon()` records `{app_pid, daemon_pid, port}` in `runtime/app-instance.json`; a second launch attaches its window to the live instance's daemon instead of stacking another, and a daemon whose owning app died (pre-fix versions leaked one per relaunch) is killed and replaced at boot. (3) Onboarding gains an explicit hosting choice pane after sign-in — ClawMetry Cloud (`connect --start-sync-now`) vs Local/Self-host (`connect --defer-sync` + `clawmetry sync`), both starting the same 7-day all-runtimes trial, defaulting to cloud after 180s. `clawmetry/static/js/app.js` — `checkLicenseExpiry()` now also fires BEFORE the cliff: trial with ≤3 days left or in grace shows the red banner ("Your trial ends today…" / "ends in N days") with a 4h re-show on dismiss; previously a trial at 0 days left rendered nothing anywhere. Also added the missing `nav.evals_tooltip` / `nav.notifications_tooltip` locale keys that leaked raw i18n keys into sidebar tooltips.
  - **Verified:** live on the founder's Windows 11 desktop install: `ensure_sync_daemon()` took the daemon from dead to alive (discovery-file probe False→True), and `/api/sessions` immediately returned real Claude Code sessions; the orphaned second dashboard daemon was detected and killed; all three `_check_existing_instance` cases (attach / orphan / stale) unit-tested against the live daemon; ran the dashboard from source against the machine's real trial license (0 days left, grace) and screenshotted the new red trial banner with its Get-a-license CTA rendering above the tab content.

- **Feature: desktop app installs a global `clawmetry` CLI + instant warm launches.**
  - **Why:** the desktop app's runtime venv was invisible to the terminal — desktop users who typed `clawmetry` in cmd/PowerShell got "not recognized" unless they separately `pip install`ed, splitting the install base. And warm launches could stall 20+ seconds on the splash whenever the 6h stamp expired, because `bootstrap()` ran a blocking `pip install --upgrade` before starting the daemon. Founder ask 2026-08-08: the app must be super snappy and the CLI must work globally so users can run both.
  - **What:** `desktop/app.py` — (1) `ensure_global_cli()` runs off the boot path on every launch: Windows writes a `%LOCALAPPDATA%\ClawMetry\bin\clawmetry.cmd` shim delegating to the venv exe, appends that dir to the per-user PATH (HKCU, no admin) and broadcasts `WM_SETTINGCHANGE`; macOS/Linux symlink `~/.local/bin/clawmetry`. (2) `bootstrap()` fast-path: if the venv already has a runnable clawmetry, return immediately — the watcher thread owns the 6h upgrade cadence in the background and drift-restarts the daemon, so launch never blocks on PyPI. (3) `_get_installed_version()` reads the dist-info directory name instead of spawning the venv interpreter (~1s → ~1ms, also on every watcher tick). (4) The system-Python probe result is cached in `runtime/bootstrap-python.json`. (5) Daemon ready-poll tightened 0.4s → 0.15s. `desktop/installer/windows.nsi` uninstaller now removes the shim dir and strips its user-PATH entry.
  - **Verified:** on a live Windows 11 install of the shipped desktop app (runtime venv at clawmetry 0.12.666): warm-path `bootstrap()` measured 0.3ms and dist-info version read 1.4ms; `ensure_global_cli()` wrote the shim, registered the PATH entry, and a fresh-PATH shell resolved `clawmetry` to the shim and printed `clawmetry 0.12.666`.

- **Release: ship the E2E key settings panel and the Windows/Linux installers to end users.**
  - **Why:** carrier `[RELEASE]` so #4645 and #4648 reach the next tagged build and PyPI release instead of sitting merged-but-unpublished on main.
  - **What:** no new code; ships #4645 and #4648.
  - **Verified:** end-to-end this release, confirm `pip install --upgrade clawmetry` exposes the "Cloud sync key" profile-menu item, and confirm `releases/latest/download/ClawMetry-windows-setup.exe` and `releases/latest/download/clawmetry-linux.AppImage` resolve on GitHub once `desktop-artifacts.yml` runs against the new tag.

- **Feature: reveal and regenerate the E2E encryption key from the local dashboard settings.**
  - **Why:** the only way to see the secret that decrypts cloud-synced snapshots was `clawmetry status --show-key` on the CLI. Founder ask 2026-08-08: expose it in Settings on `localhost:8900`, never on the hosted cloud dashboard, with a regenerate option for a suspected leak.
  - **What:** `GET /api/local/e2e-key` and `POST /api/local/e2e-key/regenerate`, both bare `@app.route` registrations in `dashboard.py`'s OSS-only route section (not a Blueprint), so the hosted `clawmetry-cloud` app never mounts them. New "Cloud sync key" profile-menu item opens a modal (masked key, reveal toggle, copy button, regenerate with an explicit confirm step) via `clawmetry/templates/partials/e2e-key-modal.html` + `clawmetry/static/js/gw-setup.js`.
  - **Verified:** ran the dashboard locally against a fake `~/.clawmetry/config.json`, confirmed both endpoints' configured/not-configured states, and drove the modal through Playwright end to end (reveal, copy-to-clipboard, regenerate-with-confirm) against the real rendered page.

- **Feature: real native installers for the Windows and Linux desktop app.**
  - **Why:** Windows shipped a `.zip` of a PyInstaller one-folder build, and the Linux CI job has been named "Linux single-folder + AppImage" since day one but only ever produced a `.tar.gz`, the AppImage step was never written. Founder priority 2026-08-08: every platform's download must be a real installer.
  - **What:** `desktop/installer/windows.nsi` (NSIS) wraps the Windows build into `ClawMetry-Setup-<version>.exe`, Start Menu and Desktop shortcuts, an uninstaller in Add/Remove Programs, per-user install with no UAC prompt. The Linux job now stages an AppDir and runs `appimagetool`, producing `clawmetry-linux.AppImage`. Building and running the real frozen Linux binary locally to validate this surfaced a genuine bug: the Linux build has never actually been able to open a window, PyInstaller bundled whatever `gi`/PyGObject the build machine's system python3 had, compiled for the wrong Python ABI for the frozen interpreter. Fixed by pinning `PyGObject==3.48.2` for Linux in `desktop/requirements-dev.txt` and installing the dev headers it needs to compile against the CI job's own interpreter.
  - **Verified:** compiled `windows.nsi` locally with `makensis` against a stand-in build folder. Built the real PyInstaller Linux binary locally, reproduced the `gi` import crash, applied the fix, rebuilt, and confirmed a clean launch. Built the actual `.AppImage` with `appimagetool` and ran it under Xvfb, screenshot confirms the real onboarding UI renders (not just a clean exit code).

- **Release: ship the drag-to-Applications DMG layout to end users.**
  - **Why:** #4646 rewrote the DMG-build step but no signed `.dmg`
    carries the new layout yet. Carrier `[RELEASE]` so users see the
    two-icon drag-and-drop window on the next download instead of the
    lone `ClawMetry.app`.
  - **What:** no new code; ships #4646.
  - **Verified:** end-to-end this release — download the fresh `.dmg`,
    mount, confirm the window shows ClawMetry + Applications side-by-
    side in a 600x300 icon-view window with hidden toolbar.

- **Fix: DMG opens with a drag-to-Applications layout instead of an empty window.**
  - **Why:** the shipped `.dmg` mounted to a window showing only
    `ClawMetry.app` — no `Applications` shortcut for users to drag it
    onto. Live report 2026-08-08: *"why is there no drop to
    applications folder — check how we did for clawmetry-mac app it's
    a separate repo — we should reuse same approach."*
  - **What:** rewrote the "Wrap into .dmg" step in
    `.github/workflows/desktop-artifacts.yml` to stage the `.app` +
    an `Applications` symlink into a directory, build a UDRW writable
    DMG, `osascript` the Finder into positioning icons (ClawMetry.app
    left, Applications right, 96px icons, hidden toolbar/statusbar),
    then `hdiutil convert` to the final compressed UDZO. Signing/
    notarization steps unchanged — they still operate on the final
    `dist/*.dmg`. Pattern lifted from `vivekchand/clawmetry-mac`'s
    build-sign-release workflow so both native macOS surfaces
    (Swift menubar app + pywebview desktop app) present identical
    drag-to-install UX.
  - **Verified:** YAML parses locally. End-to-end verification is the
    next release — mounting the shipped `.dmg` must show two
    side-by-side icons (ClawMetry, Applications) in a 600x300 icon-
    view window with no toolbar.

- **Release: stable desktop-app download URLs + Windows console-window fix reach the wheel and the next signed builds.**
  - **Why:** the desktop thin-shell app had no public, permanent download link (`desktop-artifacts.yml` only produced version-suffixed GitHub Release assets reachable by digging into CI runs), and a real Windows-only bug survived because nothing had exercised those code paths end to end: the shell is built windowed (`console=False`) but every subprocess it spawns (`python -m venv`, `pip install`, the venv's `clawmetry` CLI, the daemon itself) is a console executable, so Windows flashed a console window on first launch and every relaunch. Carrier `[RELEASE]` so #4640 actually reaches the next tagged build.
  - **What:** `desktop-artifacts.yml` now uploads a fixed-name copy of each platform build (`ClawMetry-mac.dmg`, `ClawMetry-windows.zip`, `clawmetry-linux.tar.gz`) alongside the versioned one, so `github.com/vivekchand/clawmetry/releases/latest/download/<fixed-name>` always resolves to the current release with no version bookkeeping. This is what `clawmetry-landing`'s new `/download/<os>` buttons link to. `desktop/app.py` and `desktop/onboarding.py` gained a shared `_win_subprocess_kwargs()` helper applying `CREATE_NO_WINDOW` to every subprocess call on Windows (no-op elsewhere).
  - **Verified:** ran `desktop/app.py` end-to-end under Xvfb (GTK-WebKit backend) before and after the fix: real venv bootstrap, real `pip install clawmetry` from PyPI, real onboarding auth pane with a real OTP round-trip, real daemon spawn serving a working `/api/overview`, identical behavior both times (the fix is a no-op outside `platform.system() == "Windows"`, confirming it doesn't regress macOS/Linux). End-to-end for this release: the tag push must cascade to `desktop-artifacts.yml` and produce the fixed-name assets on the GitHub Release. Will confirm with `curl -I` on `releases/latest/download/ClawMetry-windows.zip` post-release. Carries #4640.

- **Release: ship dashboard sign-out login fix to end users.**
  - **Why:** #4632 fixed the "Enter your access token" primary prompt on
    main but no signed `.dmg` / PyPI wheel carries it yet. Carrier
    `[RELEASE]` so the fix reaches installs.
  - **What:** no new code; ships #4632.
  - **Verified:** end-to-end this release — sign-out on the shipped
    `.dmg` must show the new hierarchy (Sign back in primary red,
    GitHub/Google/OTP secondary, gateway-token in Advanced disclosure).

- **Fix: dashboard sign-out login pane no longer shows "Enter your access token" as the primary prompt.**
  - **Why:** users who clicked Sign Out on the dashboard landed on a
    confusing overlay whose primary CTA was a raw access-token input.
    The token concept is an internal implementation detail (gateway JWT
    on the local machine); users think in terms of accounts. Reported
    live 2026-08-08: *"what the hell is this access token?? I told
    1000 times we should not have such confusing things — there should
    be only login / signup via google / github / otp."*
  - **What:** rewrote `clawmetry/templates/partials/overlays.html` login
    card to mirror `clawmetry onboard` and the desktop first-launch
    pane. Primary: "Sign back in (this machine)" (solid red, one-click,
    visible only when the loopback detected-token probe answers — so
    hidden on remote access). Secondary: three cloud sign-in options —
    Continue with GitHub, Continue with Google, Continue with email
    (OTP). The raw gateway-token entry is preserved for legitimate
    remote-access users behind an Advanced `<details>` disclosure at
    the bottom, so nobody has to see "access token" as a top-level
    prompt. New JS handlers `clawmetryOauthLogin(provider)` and
    `clawmetryEmailOtpStart()` in `auth-bootstrap.js`; both reuse
    existing endpoints (`/api/cloud-cta/oauth-start`,
    `/api/auth/email-otp`) so no new server surface. Both clear the
    `cm-signed-out` marker on success so the next page load auto-signs
    in via the detected-token bootstrap.
  - **Verified:** HTML + JS parse; new functions defined
    (`clawmetryOauthLogin`, `clawmetryEmailOtpStart`); existing
    `clawmetryLogin` still wired to the Advanced token input so
    remote-access users are not broken; headless Chrome screenshot of
    the rendered overlay confirms the new hierarchy (Sign back in
    prominent, OAuth/OTP visible, gateway token buried).

- **Release: header cloud-sync toggle reaches users — one-click pause/resume from the dashboard.**
  - **Why:** the sync-toggle chip landed on main in #4623 (9f6355209) but
    hasn't shipped in a signed `.dmg` or PyPI release yet. Carrier
    `[RELEASE]` so the feature actually reaches installs — a
    stay-on-main fix helps no user.
  - **What:** no new code; ships #4623 into a bundle.
  - **Verified:** end-to-end is this release — the tag push must
    auto-cascade to desktop-artifacts (regression check for the
    `actions: write` fix), produce `ClawMetry-0.12.<n>.dmg` with the
    sync chip present in the header (grep the bundle's PYZ for
    `sync-toggle-btn` — analogous to how #4619's shipment was
    verified for `btn-tertiary`).

- **Release: auth pane hierarchy fix — GitHub/Google now primary, email tertiary.**
  - **Why:** screenshot verification of v0.12.659 caught a visual bug —
    the red "Sign in with email" button dominated GitHub/Google buttons
    on the first-launch auth pane. That's the wrong signal: OAuth is
    one-click while email is two-step (send OTP, verify). The CLI's
    `clawmetry onboard` already presents `[1] GitHub  [2] Google` as
    primary with email as fallback; the desktop pane didn't match.
  - **What:** carrier `[RELEASE]` for the fix that landed in #4618.
    No new code in this PR; the visual hierarchy fix rides along.
  - **Verified:** side-by-side screenshots before/after in the #4618
    description. End-to-end verification is this release: the tag push
    must (a) auto-cascade to `desktop-artifacts.yml` (regression check
    for the auto-cascade fix), (b) produce `ClawMetry-0.12.<n>.dmg`
    with the corrected auth pane inside.

- **Feature: Cache Hit Rate and Routing Advisor tiles land under the Usage tab, answering the two efficiency tactics Uber's CTO named on the Aug 6, 2026 earnings call.**
  - **Why:** Uber's CTO on the Q2 2026 call: "the next phase will not be characterized by who spends the most tokens, but about how people use them as efficiently as possible." Frontier-AI adoption at Uber quadrupled since January while cost per token trended down, thanks to prompt caching, default model selection, per-engineer visibility, and open-weight experiments. Every CFO on the S&P 500 now asks the same board question with a smaller budget and no internal GenAI Gateway. ClawMetry ships the two most CFO-legible answers off the shelf.
  - **What:** two tiles positioned directly under the Efficiency grade. Cache-Hit tile shows the current hit rate, the amount already saved from cached reads, and a conservative estimate of the amount left on the table (flagged as an estimate; cacheable-fraction constant exposed in the payload so the UI labels it honestly). Routing Advisor tile shows total potential monthly savings and the top five safe same-provider model downgrades, sourced from `providers_pricing.downgrade_model_name`'s guarded resolver (never cross-provider, never a bare-family splice that synthesises a non-existent id). Both tiles derive client-side from the shared `/api/efficiency` cache, so they add zero fetches per tab load and are cloud-safe by construction via the existing `cm-cloud-efficiency` interceptor. Two new public API endpoints (`/api/efficiency/cache-hit-rate`, `/api/efficiency/routing-advisor`) stay for external consumers and reconcile with `/api/efficiency` by construction, both honour `?days=` clamping, both never 500.
  - **Verified:** 36/36 tests in `tests/test_efficiency.py` pass (5 new endpoint tests join the existing suite: shape, per-runtime scoping, `?days=` clamp, realised pull, never-500 on store failure). Served `static/js/app.js` contains `renderCacheHitRateCard` + `renderRoutingAdvisorCard`. Rendered `tabs/usage.html` (via Jinja) contains both card ids. FLYWHEEL Hard Gate 4 (No Dead UI) satisfied. Cloud parity satisfied without touching the cloud repo: both tiles read the same cached `/api/efficiency` blob that the existing `cm-cloud-efficiency` interceptor already serves from the snapshot. Blueprint and Requirement in 8090 Factory carry the new `CacheHitRate` and `RoutingAdvisor` components plus three new acceptance criteria (`AC-OBS-CEA-002.3` cache hit rate + estimate labelling, `AC-OBS-CEA-002.4` routing recommendation, `AC-OBS-CEA-002.5` realised vs potential); no drift. Carries #4610.

- **Release: first `.dmg` that ships end-to-end signed + notarized + first-launch onboarding.**
  - **Why:** the desktop bundle capability landed in stages this evening —
    (a) the thin-shell PyInstaller `.app` (#4602), (b) signing pipeline
    wiring (#4603), (c) workflow-file syntax fix (#4605), (d) `pyinstaller`
    marker fix + release-on-merge tag cascade (#4608), (e) `actions: write`
    permission + tag-derived VERSION (#4612), and (f) the first-launch
    onboarding pane itself (#4614). Each release since v0.12.658 had one
    or more of those pieces missing. This release is the first one where
    the complete chain fires end-to-end from a single `[RELEASE]` merge:
    PyPI wheel publishes, tag pushes, `desktop-artifacts.yml` auto-fires
    on the tag (permission fix), macOS PyInstaller finds pyinstaller
    (marker fix), signs and notarizes both `.app` and `.dmg` (secrets
    wiring), and attaches everything to the GitHub Release named for the
    right version (VERSION fix). And when the user opens the `.dmg`, the
    first-launch onboarding pane runs — GitHub/Google/Email OTP sign-in,
    auto Pro trial provisioning for entitled accounts, cross-sell
    carousel during bootstrap, dashboard-content-ready gate — instead
    of dropping them on an anonymous empty dashboard.
  - **What:** no new code changes in THIS release — a `[RELEASE]` carrier
    to fire the full pipeline for the first time end-to-end. The prior
    `## Unreleased` entries describe the actual changes shipping.
  - **Verified:** end-to-end verification IS this release. Success bar:
    (1) `release-on-merge` bumps to `v0.12.<n>` and pushes tag WITHOUT
    manual intervention, (2) `desktop-artifacts.yml` auto-fires on the
    tag WITHOUT a manual `gh workflow run`, (3) all three OS jobs green,
    (4) release attaches `ClawMetry-{correct_version}.dmg` (not stale
    by one version), (5) `spctl --assess --type open` on the downloaded
    `.dmg` returns `accepted, source=Notarized Developer ID`, (6) first
    launch shows the onboarding pane.

- **Feature: desktop app now onboards new users natively — sign-in pane, auto Pro trial, cross-sell carousel, dashboard-content-ready gate.**
  - **Why:** a user who chose the `.dmg` over `pip install` is the highest-intent
    surface we have; the old shell was a passive webview that dropped them on
    the same anonymous empty dashboard a `pip install` would produce, wasting
    that signal. Trial provisioning existed in the backend (`auto_provision_pro`
    in `clawmetry/license.py`) but had no in-app trigger — the paywall CTA
    just did `window.open('clawmetry.com/connect')` and users had to bring a
    `cm_` key back manually. Result: desktop installs converted to trial at
    single-digit rates.
  - **What:** `desktop/onboarding.py` — a new self-contained module (stdlib only)
    that renders three surfaces inside the pywebview window: (1) an auth pane
    mirroring `clawmetry onboard`'s three paths (GitHub OAuth loopback,
    Google OAuth loopback, email OTP — same server endpoints), (2) an
    Ubuntu-installer-style cross-sell carousel that auto-advances through
    Agent Builder, Desk device, and Enterprise SSO while the runtime venv
    provisions, (3) a ready-gate spinner that keeps the pane up until
    `/api/overview` returns content or 20s elapses. `desktop/app.py` gains a
    `DesktopAPI` class exposed as `window.pywebview.api.*` so the pane's JS
    can call into Python for OAuth, OTP send/verify, external-link opens, and
    skip. Post-auth the shell shells out to
    `runtime/venv/bin/clawmetry connect --key cm_… --start-sync-now` — no
    duplication of key-validation, `auto_provision_pro`, or sync-daemon
    start in the shell. First-launch state stamped in
    `~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json`
    so relaunches skip the pane. Cloud sync is default-ON per product spec;
    the header toggle to disable is a follow-up. `desktop/build_mac.spec` +
    `build_windows.spec` + `build_linux.spec` explicitly list `onboarding`
    in `hiddenimports` so a future refactor can't silently drop it from the
    bundle. `desktop/README.md` and Software Factory Blueprint updated with
    the new sequence.
  - **Verified:** onboarding.py + app.py both parse (`python3 -c "import ast;
    ast.parse(open(...).read())"`); DesktopAPI unit smoke tests pass (skip_auth
    sets the event, open_external rejects non-https, start_oauth rejects
    unknown providers, send_email_otp rejects invalid emails, verify_email_otp
    rejects short codes). End-to-end verification is the next release: the
    tag push must produce a `.dmg` that on first launch shows the auth pane,
    completes GitHub OAuth via loopback, provisions the Pro wheel for a
    trial-entitled account, and dismisses when `/api/overview` returns data.

- **Fix: macOS `.dmg` now actually builds — pyinstaller was excluded from macOS via a stray sys_platform marker; release-on-merge now kicks tag-triggered workflows the GITHUB_TOKEN can't cascade.**
  - **Why:** two bugs in a row prevented v0.12.656 and v0.12.657 from
    shipping desktop bundles even though PyPI got the wheels cleanly.
    (1) `desktop/requirements-dev.txt` pinned pyinstaller with
    `sys_platform != "darwin"` — literally excluding it on macOS. The
    workflow's macOS job then runs `pyinstaller --clean --noconfirm
    desktop/build_mac.spec` and dies with exit 127 ("command not
    found"). The comment above the workflow step even says "PyInstaller
    (not py2app)" but the requirements file thought it was
    py2app-on-mac. (2) `release-on-merge.yml` creates the release tag
    with the default GITHUB_TOKEN, and GitHub Actions deliberately
    suppresses cascade triggers for GITHUB_TOKEN events — so the
    `on: push: tags:` gate on `desktop-artifacts.yml` never fired even
    after the workflow-file syntax fix in v0.12.657. Every release
    since v0.12.656 has needed a manual `gh workflow run
    desktop-artifacts.yml --ref v0.12.<n>` to build the bundles.
  - **What:** (1) collapse the pyinstaller line in
    `desktop/requirements-dev.txt` to a single unconditional
    `pyinstaller>=6.0` and drop the unused py2app + `setuptools<70`
    macOS pins — all three build specs are PyInstaller specs, py2app
    is not on the shipping path. (2) add an explicit
    `gh workflow run desktop-artifacts.yml --ref v0.12.<n>` step at
    the end of `release-on-merge.yml` right after the `gh release
    create` step, so every future release fires the desktop-bundle
    build automatically. Non-blocking (`|| echo`) so a dispatch failure
    never blocks the PyPI publish that already succeeded upstream.
  - **Verified:** locally,
    `pip install -r desktop/requirements-dev.txt` on macOS installs
    pyinstaller (was previously silently skipped by the sys_platform
    marker). The `gh workflow run` step is idempotent and safe on
    re-runs. End-to-end verification is this release: the tag push
    must produce a signed+notarized `.dmg` + Windows `.zip` + Linux
    `.tar.gz` attached to the GitHub Release WITHOUT any manual
    dispatch step from me.

- **Fix: desktop-artifacts workflow now parses — signed `.dmg` ships on tag push instead of failing at the workflow-file level.**
  - **Why:** the wiring release (v0.12.656) attempted to gate the signing
    steps with `if: ${{ secrets.MACOS_SIGN_IDENTITY != '' }}` at step level.
    GitHub Actions rejects `secrets.*` inside `if:` — that context is only
    legal in `env:`, `with:`, and `run:`. The parser refused the whole
    workflow file, so every run (both the tag push and a manual dispatch
    for retry) failed at "This run likely failed because of a workflow
    file issue" before any job started. Net effect: `clawmetry 0.12.656`
    published to PyPI cleanly but the GitHub Release for that tag had
    zero binary assets attached.
  - **What:** hoist the presence checks to job-level `env` and gate the
    steps on `env.HAS_CERT` / `env.HAS_SIGN`, which is legal in `if:`.
    Also declare `permissions: contents: write` on the release job so
    `softprops/action-gh-release@v2` can attach files even when the org
    default GITHUB_TOKEN scope is read-only. First tag on which the fix
    lands is the one this release cuts.
  - **Verified:** YAML parses locally (`python3 -c "import yaml; yaml.safe_load(...)"`);
    no `secrets.*` references remain inside any `if:` conditional
    (`grep -nE '^\s*if:.*secrets\.'` returns nothing). End-to-end
    verification comes with this release's tag push — the macOS job
    must import the cert, sign both the `.app` and the `.dmg`, and the
    release job must attach all three OS bundles to the GitHub Release.

- **Release: macOS desktop `.dmg` now ships signed + notarized on every tag push.**
  - **Why:** the desktop-app scaffold landed in #4602 with the signing pipeline
    wired but the six Apple credentials were not yet in the repo, so
    `desktop-artifacts.yml` on a `v*.*.*` tag would still produce an unsigned
    `.dmg` — Gatekeeper would warn on first launch and the app-store-quality
    experience the desktop bundle was built for wouldn't actually reach users.
  - **What:** `MACOS_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID`,
    `APPLE_APP_SPECIFIC_PASSWORD`, `MACOS_CERT_P12_BASE64`, and
    `MACOS_CERT_PASSWORD` are now set on `vivekchand/clawmetry`. On every
    tag push, `desktop-artifacts.yml` codesigns and hardened-runtime-signs
    `ClawMetry.app`, submits the wrapping `.dmg` to Apple's notary service via
    `notarytool`, staples the ticket, and attaches the finished `.dmg` to the
    GitHub Release alongside the Windows `.zip` and Linux `.tar.gz`.
  - **Verified:** local proof — `~/Downloads/ClawMetry-signed.dmg` (7.3 MB) is
    signed by `Developer ID Application: InstaLabs LLC (8LVH596RA5)` and
    `spctl --assess --type open` reports `accepted, source=Notarized Developer
    ID`; the six secrets are confirmed present via `gh secret list` at
    2026-08-07T21:12Z. CI verification comes in this release: the tag push
    for this version is the first end-to-end exercise of the notarization
    path on GitHub-hosted runners.

- **Fix: installers now sweep and remove stale clawmetry duplicates instead of only detecting them.**
  - **Why:** #4335 (`clawmetry/installs.py`) taught the CLI to *detect and
    warn* about a stale clawmetry copy elsewhere on PATH, but nothing
    actually removed one — `install.ps1`/`install.sh` only ever cleaned up a
    previous install at their OWN target directory, and `install.cmd` has no
    dedicated venv at all, so re-running it (or switching between it and
    `install.ps1`) leaves the old copy installed and dormant. Live-reproduced
    2026-08-07: a plain `pip install --user` into a system Python left
    clawmetry 0.11.99 dormant next to a current 0.12.655 dedicated-venv
    install — harmless here only because PATH ordering happened to favor the
    venv.
  - **What:** all three canonical installers (`install.sh`, `install.ps1`,
    `install.cmd`) now sweep every python/python3 interpreter reachable on
    PATH before installing and `pip uninstall -y clawmetry` from every one of
    them except the venv/target they're about to (re)build; best-effort,
    never fails the install (`|| true` under install.sh's `set -e`).
    `install.cmd` additionally removes a leftover `install.ps1`-created venv
    at `%LOCALAPPDATA%\clawmetry` since it has no venv of its own and the two
    would otherwise coexist and shadow each other. `clawmetry/doctor.py`'s
    install census is unchanged and still catches whatever a sweep can't
    reach (e.g. a copy on a PATH entry that wasn't scanned).
  - **Verified:** 10 new tests (`tests/test_installer_stale_sweep.py`:
    bash -n / PowerShell parser syntax checks, sweep ordering before the
    install step, own-install-dir exclusion, best-effort-under-`set -e`), all
    16 pre-existing `install.sh` tests still green; reproduced the exact live
    scenario on the affected machine — reinstalled clawmetry into a second
    system Python, confirmed both `install.cmd` and `install.ps1` detected
    and removed it via `pip show`/`pip uninstall` before reinstalling fresh,
    `clawmetry --version` correct afterward. `install.sh` not behaviorally
    re-run beyond `bash -n` (Windows dev machine, no macOS/Linux box handy);
    behavioral proof for all three lands in
    `.github/workflows/install-test.yml`.

- **Added qm as the 17th observable runtime.** qm
  (github.com/yc-software/qm, qm.ycombinator.com) is YC's Postgres-
  backed multiplayer agent harness (launched 2026-07-29 MIT). Because
  qm delegates to Pi, OpenCode, Codex, and Claude Code (all already
  Pro adapters), a qm user is definitionally a Pro user and skipping
  qm meant every YC-portfolio deployment ran blind. Adapter reads qm's
  own Postgres tables (sessions / session_entries / session_llm_requests /
  turn_metrics / runs) in read-only mode via pg8000 (or psycopg2 /
  psycopg if already installed). It reads DATABASE_URL with a
  CLAWMETRY_QM_DATABASE_URL override for read-replica setups. Surfaces
  the org-scope layer (who in the org ran what, cron health across
  scopes, scope-level tokens) that Pi/OpenCode/Codex/Claude Code cannot
  see individually. Ships across the 6-PR chain: clawmetry-pro#120
  (QMAdapter + 14 tests), clawmetry#4582 (this repo — registration in
  10 lists + runtime probe + README + 4 pin tests bumped to 17), 
  clawmetry-cloud#1945 (runtime-locks FAM + Grok drift-fix),
  clawmetry-landing#611 + #612 (17 to 18 counts + chip grid),
  clawmetry-pro#121 (release 0.7.5), and clawmetry-cloud#1947 (wheel
  0.7.5 baked into the served image so activated daemons auto-provision
  QMAdapter on their next 30-min cycle).

- **Fixed the root cause of ClawMetry silently no longer auto-updating.**
  The browser onboarding gate (`routes/onboarding.py`, the default
  first-run path since the 2026-07-31 hard-gate rollout) completed a
  `managed`/`selfhost_*` choice without ever starting or registering a
  background sync daemon — only the CLI paths (`clawmetry connect`,
  `clawmetry onboard`) did that. The only thing left polling PyPI was the
  foreground dashboard's in-process checker thread, which stops the
  moment that one process exits (closed terminal, sleep, reboot, crash),
  silently and permanently halting auto-update until a human manually
  relaunched `clawmetry`. Onboarding completion now always calls the new
  `clawmetry/daemon_registration.py::ensure_persistent_daemon()`.
  Windows also gets real persistence for the first time: previously it had
  no launchd/systemd equivalent at all (`_start_daemon`'s Windows branch
  fell straight to an unsupervised detached subprocess), so a Windows node
  lost auto-update after any reboot/logoff/crash even when a daemon HAD
  been registered — it now registers a logon-triggered, restart-on-failure
  Task Scheduler task. Finally, `auto_update` self-healing (re-asserting
  the default-on `True` after a stale persisted `False`) previously only
  ran for entitled *paid* cloud accounts via the heartbeat
  (`_sync_auto_update_with_plan`); self-hosted and free-tier installs had
  no path back to `True`. The update-check worker now heals a stale unset
  `False` for every role/tier on boot, while a real, explicit user opt-out
  (`POST /api/update-check/config`) is now tracked and never overridden.
- **Fixed an onboarding-complete request hang introduced by the daemon-registration
  fix above.** `register_systemd`/`register_launchd` shelled out to
  systemctl/launchctl with no timeout, synchronously inside the
  `/api/onboarding/complete` HTTP handler the browser's init sequence waits
  on. A runner or container with no working user systemd/dbus session can
  make those commands hang instead of failing fast, blocking the response
  indefinitely (caught live via a PR's own visual-diff bot: mobile
  screenshots stuck forever on "Initializing ClawMetry"). Every
  `daemon_registration.py` subprocess call is now bounded to a few seconds,
  and the registration call itself is dispatched on a background thread so
  onboarding-complete never blocks on it at all.
- **Retired the legacy "ClawMetry Setup" gateway-token modal.** It auto-popped
  on every dashboard load regardless of whether onboarding had already
  completed (v0.1-era UX from before the product detected 17+ non-OpenClaw
  runtimes). The existing onboarding-gate modal (managed cloud vs self-host,
  which already tracks completion correctly via `/api/onboarding/state`) is
  now the only first-run gate. A new opt-in "Gateway" tab under the
  Developer drawer still lets real OpenClaw users paste a gateway token
  manually. The Agents (Inventory) tab now shows an upgrade nudge for a
  detected-but-not-yet-entitled runtime instead of a "sync starting up"
  message that would never resolve.
- **`clawmetry status` shows an explicit `Plan:` line** (Free / Trial /
  Trial Expired / Starter / Pro), unconditional unlike the old `License:`
  block, which stayed silent whenever no local key file existed.
- **Expired trials now actually stop ingesting new paid-runtime data.**
  `sync_family_runtimes` checks `entitlements.allows_runtime()` per adapter
  per sync cycle. Previously only an install-time "is the pro wheel on
  disk" check gated ingestion, so a trial that later expired kept
  ingesting new Claude Code/Codex/etc. sessions indefinitely once the
  wheel had landed once.
- **Fixed a same-day regression in the trial-end hard-block gate**
  (`clawmetry/trial_enforcement.py`, shipped default-on earlier the same
  day): it was hard-blocking (HTTP 402) every plain OSS/free install, not
  just an expired trial or subscription. Verified live before the fix: a
  fresh `pip install clawmetry` with no license or cloud account returned
  `hard_blocked: true, source: "oss"` on `/api/sessions` and
  `/api/overview` and never finished booting the dashboard. Now only a
  source that was actually on a paid or trial tier and has since passed
  its expiry is blocked; a never-entitled install passes through
  untouched. See `docs/TRIAL_ENFORCEMENT.md`.

- **Score any conversation, right where you read it.** Every row in the
  Conversations tab gets a small **Score** button that runs the same judge
  the daemon uses (via `POST /api/evals/rescore/<session_id>`). Result
  renders inline as a colored badge — green ≥ 4, amber ≥ 2.5, red below —
  with the judge's one-line reason on hover. If no judge key is set the
  button flips into "Set judge key →" that opens the rubric + key modal on
  the spot, so the setup lives where you first need it instead of behind
  the small ⚙ icon on the Evals tab. On `app.clawmetry.com/node/*` the
  live-Score button is replaced with a stored-score badge computed by the
  daemon on the machine that has the judge key + session DuckDB, since
  scoring can't run on the cloud proxy.

- **Trial ends → paid.** ClawMetry now blocks the dashboard UI + sync when
  the trial period ends, prompting checkout with an un-dismissable modal.
  Signed licenses land automatically over the heartbeat after payment, so
  the dashboard unlocks within one 60s cycle with no restart. Set
  `CLAWMETRY_HARD_BLOCK=0` to opt out (support only). Details:
  `docs/TRIAL_ENFORCEMENT.md`.
- **xAI Grok is the 18th observed runtime.** The Grok Build CLI (Rust binary
  at `~/.grok/bin/grok`, installed via `curl x.ai/cli/install.sh`) now shows
  up across the dashboard when Pro is licensed. Token accounting reads the
  global `~/.grok/logs/unified.jsonl` (VERIFIED `shell.turn.inference_done`
  row shape from the cereblab wire-level analysis + openusage#646); session
  listing walks `~/.grok/sessions/<encoded-cwd>/<uuid>/`; cost derives via
  the freshly-added `providers_pricing.xai` rates (grok-4 $3/$15, grok-3
  $3/$15, grok-3-mini $0.30/$0.50, grok-code-fast-1 $0.20/$1.50, grok-2
  $2/$10). Adapter lives in clawmetry-pro (0.7.4). Undocumented msg-name
  branches parse defensively, so a wrong field guess produces NO data,
  never fabricated data.
- **Grok's outbound repo-upload panel.** The pro adapter surfaces the raw
  `repo_state.upload.enqueued` manifests from `unified.jsonl` on
  `Session.extra.uploadedPayloads` (fileId, size_bytes, file_count,
  repo_path) plus a `uploadedBytesTotal` aggregate. The Grok tab can
  render "what left your machine to xAI this session", a differentiated
  view no other runtime needs, and the direct answer to the July 2026
  disclosure that Grok Build silently uploaded entire repos to a
  `grok-code-session-traces` GCS bucket.

## 0.12.650

- **The profile menu now respects that you're self-hosted.** "Upgrade plan"
  on a trial license opens the self-hosted pricing flow on clawmetry.com
  (the buy modal preselected) instead of the cloud app's account funnel,
  and "Billing & plan" only appears when the node is actually linked to a
  cloud account. The old "Gateway settings" gear and menu item are gone:
  the gateway wizard is first-run setup and still opens itself whenever
  the gateway is unconfigured, which is the only time it can help.

## 0.12.648

- **The savings ideas now read the spend flow.** The efficiency card on the
  Cost tab gains a new idea, "Trim thinking on routine work", derived from
  the measured "Where the money goes" flow: it appears only when thinking
  makes up at least 40% of what your agents spend on output, shows the
  measured share, and is always labeled as an estimate. Ideas are scoped
  per runtime, so a runtime switcher selection only ever shows ideas
  computed from that runtime's own numbers.

## 0.12.647

- **Check verdicts on the conversation view.** Opening a transcript now shows
  the session's structural check chips (green pass, red fail, reason on
  hover) in the metadata panel, the same verdicts the Evals tab lists, so
  you can judge a conversation's health right where you read it.

## 0.12.646

- **The free checks show their work.** The Evals tab's recently-scored table
  gains a Checks column: one chip per structural verdict (green pass, red
  fail, the reason on hover). Sessions scored only by the free checks are
  listed too, so evals visibly work out of the box before any judge key is
  added. Fail chips say what happened ("tool errors"), never a double
  negative. Hosted dashboards are unchanged (the verdicts live on the node).

## 0.12.644

- **Where the money goes: a spend flow for the whole node.** The Cost tab now
  opens with a flow chart tracing spend from what your agents read (your
  messages, earlier replies, tool results, and the derived system prompt and
  tool definitions overhead) through each runtime into what they write
  (thinking, replies, built-in and MCP tool calls), with real dollars and
  tokens on every band. Shares are measured from actual session content and
  reconciled against model-reported usage per call, so category sums always
  match the cost of record; anything content cannot explain is labeled as a
  derived estimate, never invented. New `GET /api/spend-flow` endpoint
  (respects the runtime switcher and the free 24h history window) and a
  `spendFlow` snapshot slice for the hosted dashboard.

## 0.12.643

- **Family ingest is starvation-proof.** The per-cycle adapter walk now
  rotates its start position (cursor persisted in daemon state), so a daemon
  that keeps dying mid-pass — e.g. a native crash loop under launchd
  KeepAlive — still reaches every runtime within a few passes. Previously a
  bounced daemon restarted the walk in the same fixed order every run:
  runtimes early in the list kept ingesting while the tail (Copilot,
  Antigravity) silently never landed, leaving their sessions missing and
  per-runtime rollups/scoped alerts reading $0.

## 0.12.643

- **Free deterministic checks now actually run.** The zero-LLM-cost structural
  evaluators (tool errors, JSON validity, required tool args, length bounds)
  were pruned in #4436 as an unintegrated orphan; the real gap was that they
  never understood stored event rows. They are back, bridged to the real
  DuckDB shapes, and the sync daemon scores every completed session with them
  on the eval cadence at zero cost, no key needed
  (CLAWMETRY_DETERMINISTIC_CHECKS, default no-tool-errors). Verdicts land in
  the new per-metric eval_metrics table and are served by
  GET /api/evals/metrics. Also fixes a double-count that reported every tool
  call twice to the extractors.
- **Optional DeepEval metric engine.** `pip install "clawmetry[deepeval]"`
  (Python 3.10+) adds two judge-backed agent metrics from the Apache-2.0
  DeepEval library: "Did the agent use its tools right?" (argument
  correctness) and "Did the conversation get finished?" (conversation
  completeness). Runs fully locally: DeepEval telemetry is force-disabled in
  code before the library ever imports, no vendor account is used, and every
  judge call goes through ClawMetry's own provider-direct judge (your key,
  your provider, transcripts redacted first; keyless local servers like
  Ollama work too). Off by default; enable by naming metrics in
  CLAWMETRY_DEEPEVAL_METRICS. The evaluator library shows honest per-box
  states: "Needs install" without the extra, "Needs key" without a judge key.
  See docs/EVALS_DEEPEVAL.md.
- **Golden suites grade with YOUR rubric.** `clawmetry eval --suite` judged
  with the shipped default rubric even when ~/.clawmetry/evals.yaml had a
  tuned one; the suite judge now uses the same merged rubric as the
  production judge.

## 0.12.641

- Re-publish of 0.12.640 (same ghost-wheel race as 0.12.636: the release
  workflow checked out the `main` ref before the merge commit propagated and
  published without the runtime-scoped alerts/approvals code). Root cause
  fixed: release-on-merge now builds the PR's merge_commit_sha exactly.

## 0.12.640

- **Alerts and approvals are runtime-scoped by default.** Alert rules carry a
  per-rule scope: creating a rule while the runtime switcher is set inherits
  that runtime, and "All runtimes (node-wide)" is the explicit opt-in (rule
  rows show a scope chip either way). Scoped rules evaluate per-runtime
  slices end to end: daily-spend and token-velocity read the per-runtime
  DuckDB rollups, event-stream rules filter by the session-id prefix, and
  quality rules (score drop / failure rate) read a per-runtime quality
  window — a scoped rule never fires on a node-wide number.
- **The Approvals tab now shows for every runtime** (it was hidden behind the
  OpenClaw gateway capability) and scopes its pending + history rows to the
  selected runtime; /api/approvals and /api/approvals-audit accept
  ?runtime=. The stale "node-wide" banner is gone from both tabs.

## 0.12.639

- **Runtime feature parity: the dashboard stops being OpenClaw-first.** Every
  advertised surface now runs on real per-runtime logic or gates honestly:
  - **Agent Graph for every runtime.** Spans are reconstructed from each family
    runtime's normalized events at ingest (session root, llm.call, tool.<n>,
    agent.spawn from Task tool-calls + subagent records) with the real
    agent_type/agent_id, so "who spawned whom" renders with real cost/token
    rollups — Claude Code shows main → Explore/general-purpose/... instead of
    an empty panel. Graph honours the runtime switcher (?runtime=).
  - **Approvals works locally for all runtimes — and Claude Code gets a real
    pre-tool gate.** The tab now reads the local DuckDB queue and writes
    policies.yml through validated endpoints; a generic gate-handler seam
    turns the OpenClaw exec-policy flip into one handler and adds a Claude
    Code PreToolUse hook (merge-safe installer, `clawmetry hook claude-code`
    client, sliced long-poll receiver, fail-open, loopback-only) so a policy
    match parks the tool call until you decide from the dashboard.
  - **Logs are runtime-aware.** /api/logs + /api/logs-stream take ?runtime=
    and serve the adapter's declared LogSource (hermes errors.log, nanoclaw
    docker logs, codex codex-tui.log, n8n event log) or say honestly that a
    runtime has no daemon log stream — never another runtime's logs under the
    selected runtime's name.
  - **Security posture scans the selected runtime.** Provider registry with
    the full OpenClaw scan moved intact, a real Claude Code provider
    (settings.json permissions/hooks/MCP auto-trust/dangerous grants), a
    Codex provider (approval_policy/sandbox_mode), and a neutral
    "not available yet" envelope instead of a red openclaw.json failure.
  - **Tab visibility can no longer lie.** The sidebar derives from each
    adapter's declared capabilities served by /api/agents (static map is just
    the fallback), the dead 'cost' tab id is fixed so no-cost runtimes hide
    the Cost tab, and logs/version-impact leave the false "node-wide" set.
  Pairs with clawmetry-pro 0.7.2 (claude_code declares SUBAGENTS; hermes/
  nanoclaw/codex/n8n declare real log sources).

## 0.12.637

- Re-publish of 0.12.636: the published 0.12.636 wheel raced the merge commit
  and was built without the GitHub Copilot runtime changes (the release
  workflow self-bumped from pre-merge main). 0.12.637 is the first PyPI
  artifact actually containing the 17th-runtime support described under
  0.12.636 below.

## 0.12.636

- **GitHub Copilot is the 17th observed runtime.** Copilot CLI sessions under
  `~/.copilot/session-state/` now show up across the dashboard: conversations +
  bash/edit/view tool calls from `events.jsonl`, model routing (auto-mode picks
  surface as model-change events), cache-aware token split, and **vendor-billed
  cost** from the `session-store.db` per-call usage ledger (nano-AIU credits at
  GitHub's published $0.04/credit overage price — exact, not estimated), plus
  repository/branch attribution. Adapter lives in clawmetry-pro (0.7.2).
- Approval policies match Copilot tool names (`bash`, `powershell`, `view`,
  `edit`, `create`, `grep`, `rg`, `glob`, `web_fetch`, `web_search`) via the
  canonical tool categories.

## 0.12.613

- **Antigravity is the 16th observed runtime.** Google Antigravity (IDE + CLI, all
  four product flavors under `~/.gemini/`) now shows up across the dashboard:
  sessions from brain JSONL transcripts, planner/tool steps as events, CHECKPOINT
  compactions, per-generation Gemini model + token split (prompt/thinking/response)
  and cost decoded from the `gen_metadata` store, background-generation burn,
  subagent + battle-mode metadata. Adapter lives in clawmetry-pro (0.6.0).
- Approval policies match Antigravity tool names (`run_command`, `view_file`,
  `write_to_file`, `search_web`, …) via the canonical tool categories.
- Fixed: n8n was missing from the harness-data and usage-slicing runtime
  registries (the Pro n8n harness panel rendered empty; per-runtime usage
  lumped n8n into OpenClaw). Same pass adds pi/deep agents/n8n to the lite
  runtime labels.

## [Unreleased]

### Fix: the trial paywall was armed for nobody, and paid runtimes kept syncing after a trial ended (2026-08-15)
- **Why:** the trial-end hard-block layer has been complete and default-ON for weeks and had never fired once. Verified against production: an account whose trial ended two days earlier was still ingesting and pushing 10 paid runtimes to cloud. The cause was a missing signal, not a missing gate. Once a trial lapses the cloud reports the plan as `free`, which is byte-identical to what a brand-new install reports, and the resolver deliberately refuses to block a plain free install (blocking those would brick every fresh `pip install`). With no way to tell a burnt trial from a never-trialed machine, it declined to block either, and the same missing signal left the ingest gate open too.
- **What:** the heartbeat now carries `trial_end` and `trial_used`, the daemon mirrors them into its plan cache, and the resolver treats a consumed trial past its end date as lapsed. Paid-runtime adapters stop being read, the dashboard returns HTTP 402 for paid surfaces, and the OpenClaw and NemoClaw runtimes keep working throughout. An operator who would rather not upgrade can choose "continue on free runtimes only" and keep that surface.
- **What:** on a confirmed lapse the closed `clawmetry-pro` package is now removed from the machine rather than only gated, because a gated package still sitting in site-packages can be imported by hand. Removal sweeps both install locations, clears the running process, and reverses itself automatically once the account pays. Locally ingested history is left untouched, so paying later restores the data rather than leaving a gap.
- **What:** the post-trial overlay gained a plan picker (Monthly or Annual, Starter or Pro) and now opens a payment page scoped to the chosen plan and account, so a self-hosted operator can subscribe without leaving their own dashboard. A paste-in license field remains for machines that cannot reach the payment page. The runtime count in that copy is read live rather than hardcoded, which has drifted every previous time it was written by hand.
- **Verified:** a real blocked instance returns 402 on paid surfaces with the activation and payment routes still reachable, and serves OpenClaw normally in free-runtime mode. Two customer-affecting bugs were caught before release by checking the real account population: a paying subscriber would have been blocked (every paying customer carries a past trial date, since signup starts with a trial), and the lapse verdict would have reached only 1.7% of the accounts it was meant for. Both fixed, both pinned by tests that fail on the unfixed code.

### Feature: onboard offers agent security monitoring, default-yes (2026-08-02)
- **Why:** `clawmetry secure enable` (0.12.625's numbat one-liner) only helped users who already knew it existed — nothing in the install flow surfaced it, so the realistic activation path was reading a docs page. Silently auto-enabling on install was considered and rejected: the hook install edits each harness's own config (Claude settings.json, Codex hooks.json, …), and an observability layer whose promise is "read-only by default" must never modify agent configs without a visible answer (founder 2026-08-02).
- **What:** every terminal path of `clawmetry onboard` now ends with an "Agent security monitoring (recommended)" offer — a one-keystroke default-yes [Y/n] that states up front what gets touched and that `clawmetry secure disable` undoes it, then runs the existing `secure enable` flow with the wizard answer as the consent (no second prompt). Declining prints the enable-later one-liner; EOF/no-TTY counts as decline (headless installs never modify agent configs); an existing numbat install (managed or PATH) skips the offer entirely so re-running onboard never nags.

### Fix: Overview hero said "It's idle right now" while main sessions were hard at work (2026-08-02)
- **Why:** the hero's alive-state read only `/api/subagents`, which lists spawned Task-tool children. Main terminal sessions (Claude Code busy in several terminals) never appear there, so a working node read as idle. For a product whose promise is "is my agent alive, what is it doing", the headline was untruthful (founder report, app.clawmetry.com claude_code view).
- **What:** a per-runtime `last_activity_ms` recency signal (newest event ts / session `last_active_at`, epoch ms) now rides the existing rollup: `query_model_rollup`, the `runtimeSummary` snapshot slice, and the local `/api/runtime-summary` route carry it, and the hero computes busy as an active subagent OR activity within the last 3 minutes, scoped to the runtime switcher (all-runtimes uses the max). Cached 30 seconds with a single in-flight fetch; on a fetch error the previous data is kept and retried in 5 seconds so a cold-load timeout cannot pin the hero on idle. Also fixes the latent live tok/s chip bug this exposed: it diffed the today-token counter across renders without noticing the runtime scope changed sources between samples (rendering "23,058,079 tok/s"); samples are now same-scope with a sanity ceiling.
- **Verified:** guard tests across all four hops (store rollup, snapshot builder, local route, hero JS) proven red on un-fixed code; live daemon patched and the decrypted cloud snapshot carried the field 1.9 minutes fresh; browser render showed "It's working right now." node-wide and scoped while the reporting session itself was the activity source.

### Feature: expired-trial banner with a buy path on the local dashboard (2026-08-02)
- **Why:** once a self-host trial ended, the local dashboard had no honest purchase path: the paywall modal pitches "Start 7-day free trial" (one per account, so a dead end post-trial) and the selfhost modal's ended-step only appears on a re-signup attempt.
- **What:** a banner keyed off the entitlement's expired flag (expired trial or expired paid license, tier-aware copy) with "Get a license" pointing at self-host pricing and "I have a license key" opening the existing paste surface. One entitlement fetch on load, no poller; dismiss lasts 24 hours.

### Fix: Agents-tab empty state on fresh self-host installs (2026-08-02)
- **Why:** a just-activated self-host machine with 523 Claude Code sessions showed the generic "No agents yet, and that is fine. Nothing to configure." The empty-state guidance detects runtimes via the adapter registry, which cannot see paid runtimes (Claude Code, Cursor, and friends) until the clawmetry-pro wheel installs after activation, and the client never re-polled an empty roster, so one transient empty stuck until the tab was re-clicked.
- **What:** the /api/inventory empty branch falls back to the filesystem lite detector, so the "Claude Code detected, sync is starting up" guidance renders in exactly the pre-activation window it was designed for; the empty state retries every 20 seconds while the inventory tab is active and visible; the copy drops the stale "10 more runtimes" count (key renamed to inventory.empty_body_v2 so all locales fall back to correct English).

### Fix: removed the two-runtime "No OpenClaw or NVIDIA NemoClaw detected" banner (2026-08-02)
- **Why:** the banner predates multi-runtime ClawMetry. With 16 observed runtimes it told users running any of the other 14 (the triggering report: a Claude Code node with 521 live sessions) to install OpenClaw or NemoClaw, and it rendered permanently on cloud node pages, where the server can never filesystem-detect a runtime.
- **What:** removed the banner markup, the `checkAgentPresence` 60s poller (one fewer background request), and its five locale keys across all 36 locales. `GET /api/agent-presence` and the heartbeat `agent_install` mirror stay: cloud consumers still read them. Regression guards pin the removal so the two-runtime framing cannot quietly return.

### Fix: `clawmetry login` crashed with AttributeError for signed-out users (2026-08-02)
- **Why:** the `login` subparser only defines `--force`, but `_cmd_login` delegates to `_cmd_connect`, which read `args.key` directly — so every not-yet-logged-in user hit `AttributeError: 'Namespace' object has no attribute 'key'` instead of the sign-in flow. Already-logged-in users were unaffected (login short-circuits to account info before the delegation).
- **What:** `_cmd_connect` now treats `key` like every other connect-only flag (`getattr` with a default), matching how it already reads `enc_key`, `key_only`, `no_daemon`, etc. Regression test (`tests/test_login_bare_namespace.py`) drives `_cmd_login` with the exact bare Namespace argparse produces for `clawmetry login`.

### Feature: `clawmetry secure` — one-command numbat setup (2026-08-01)
- **Why:** the 0.12.625 numbat ingest shipped the pipes, but wiring them still meant reading a docs page and running numbat's own CLI (a founder typed `clawmetry secure` the same evening and got argparse usage — the command name users reach for was obvious). Multi-step security-tool deployment is exactly the class of thing ClawMetry turns into one zero-config command.
- **What:** new `clawmetry secure enable|status|disable` (clawmetry/secure.py, stdlib-only). `enable` downloads the platform-matched numbat release binary with SHA-256 verification against the release's checksums.txt into `~/.clawmetry/bin`, then installs MONITOR-ONLY hooks (`--emit findings`, file sink + HTTP sink at this dashboard's `/api/numbat/ingest`; never `--enforce`, never `numbat collect` — the OTLP receiver would contend with ClawMetry's own `/v1/logs`). Loud consent prompt before touching agent configs (hook install edits each harness's own settings; `--yes` for automation, refuses without a TTY otherwise). `status` shows numbat's per-agent CONFIG/LIVE/WIRED inventory plus how many findings ClawMetry has ingested (via the daemon proxy) and the file-sink size. `disable` runs `numbat hook uninstall --agent all`. An existing PATH install of numbat is reused, never shadowed. docs/NUMBAT.md now leads with the one-liner.

### Feature: numbat ingest — ClawMetry is the console for Perplexity's agent-EDR (2026-08-01)
- **Why:** Perplexity open-sourced [numbat](https://github.com/perplexityai/numbat) (2026-07-29): endpoint security detection for ~27 AI agent harnesses (50+ CEL rules — secret-exfil chains, permission bypasses, persistence — plus opt-in pre-action blocking). It emits NDJSON findings but ships no UI, no storage, and no fleet view; its own issue tracker has users asking where to route the output. ClawMetry already had the destination tables, the alert pipeline, and the Security surface — this wires them together.
- **What:** one shared mapper (`clawmetry/numbat_ingest.py`) feeds two paths, deduped by numbat's deterministic ids: the sync daemon tails `~/.numbat/*.ndjson` (durable primary; per-file byte cursors), and the dashboard accepts numbat's HTTP batches on `POST /api/numbat/ingest` (gzip + bearer supported, loopback zero-config). Findings → `security_events` + a `numbat_finding` events row so count-over-threshold alert rules fire; enforcement decisions → `guardrail_events`; numbat's raw `event` records are skipped by design (they mirror session activity ClawMetry already ingests from the harnesses' own files — storing both would double-count). Critical/high findings fire banner+Telegram immediately with the standard cooldown; an opt-in `numbat security finding` seed rule lands on the Alerts tab. Wire schema pinned to numbat `0.2.x` — unknown versions are counted, logged, never crash ingest. Setup + coexistence guide (OTLP :4318 contention, OpenClaw exclusive `plugins.allow`): `docs/NUMBAT.md`.

### Feature: Brain feed surfaces failed tool calls — ERROR events, per-run issue badges, error-only filter (#4395) (2026-08-01)
- **Why:** the store has carried per-tool-result error flags since ingest (family adapters stamp `extra.isError`, the OpenClaw v3 mapper stamps `is_error`; benign read-guards already downgraded), but `/api/brain-history` dropped them — a failed Bash call and a clean one looked identical in the feed, and the UI's ❌ ERROR icon was unreachable. Third Brain-visualizer adoption (issues-detected view), for all 16 runtimes.
- **What:** the local-store mapper retypes flagged tool results to first-class `ERROR` events. Error rows render red-tinted with the ❌ pill; sequence blocks get a `⚠ N` per-run badge; swimlane lanes with failures get a red ring plus the error count in their tooltip; the type-chip strip grows a red `ERROR (N)` chip that is the error-only view. Text is never inspected — only the stored structured flag — so "21 passed, 0 failed" can't false-positive. Also fixed en route: `setBrainTypeFilter` called `renderBrainFeed()`, a function that never existed, so every type-chip click died on a ReferenceError and type filtering had been silently broken since the chips shipped.
- **Verified:** live against the founder node's real DuckDB (4 real failures surfaced, badged, red-ringed, and isolated by the chip — screenshots on the PR); 26 JS sequence checks (5 new) + new `tests/test_brain_error_surfacing.py` pinning the mapper contract for family/v3/benign/clean shapes.

### Fix: hosted Evals card + judge modal show your machine's real judge status, never a fake key form (2026-08-01)
- **Why:** on the hosted dashboard the Evals card rendered the cloud container's state: "API key: not set" plus a live-looking key form. A key pasted there was saved to the container's ephemeral disk and never reached the machine the judge actually runs on (founder report 2026-08-01: "I did api key yesterday — this screen feels like just a fake screen"). The judge-key modal (Overview gear / Evals "Judge setup") had the same trap, only partially masked by a cloud-side patch pinned to that modal's element ids.
- **What:** the sync daemon now bakes the node's real judge status into the snapshot's evals slice (`evals.judge`: enabled, key_present, provider, model, last_error, last_ok_at — booleans and labels only, never key material). In cloud mode the Evals card and the judge-key modal render that truth — scoring ON / key rejected / no key yet — with guidance that the key lives on your machine, and never render a key form. The cloud-side `cm-cloud-evals-keynote` patch is superseded and `POST /api/evals/key` is being cloud-disabled as a backstop.

### Feature: LLM Context tab merged into Context usage, now honest and session + runtime scoped (#4375) (2026-08-01)
- **Why:** the LLM Context Inspector rendered fabricated numbers: hardcoded token counts for its composition bars (Safety 120, Memories 200), percent-of-window guesses for tool schemas, OpenClaw-only section names under any runtime filter, and a node-wide cumulative gauge that could read 761K / 200K (100%). It was also the last tab the runtime switcher could not scope at all. Founder call 2026-08-01: make it honest and session-scoped, merge with Context usage.
- **What:** the tab is gone; Context usage is the single context surface and every number on it is measured. New "Current context window" gauge from the latest real turn (input plus cache tokens against that turn's model-aware window). `/api/context-economics` accepts `runtime=` with server-side session-prefix scoping (unknown runtime returns empty, never node-wide), and the session chips also filter client-side, fixing the hosted dashboard where picking a chip silently kept showing all sessions. Summary chips are recomputed from the scoped lists. `switchTab('context')` aliases to Context usage so old deep links keep working; no-cost runtimes (Cursor, PicoClaw, NanoClaw) keep the tab via the EVENTS capability. Also fixed a live click bug found during verification: `JSON.stringify` inside double-quoted onclick attributes truncated the handler, so session chips, transcript links and swimlane lane controls threw on click; all 9 sites now use the new `attrJsStr()` helper, with a static guard (8 broken lines on the old code, 0 now).
- **Verified:** new runtime-scope test suite against a real DuckDB fixture, revert-proven red on the un-fixed backend; 37/37 all-tabs post-auth E2E green against a live boot of the branch; runtime scoping curl-verified through the daemon proxy on real data; browser click-through of chips, runtime switcher and the alias with screenshots on the PR.

### Fix: Brain feed shows each message once, on every surface (#4354) (2026-07-31)
- **Why:** the hosted Brain feed showed one agent reply three times and one inbound Telegram message twice, with the Telegram pill reading "[object Object]" (founder screenshot). One turn legitimately lands in DuckDB as several rows (transcript copy with cost, v3 model.completed, a tokens=0 delivery-mirror echo; inbound messages also as gateway prompt.submitted plus the transcript user turn carrying an "(untrusted metadata)" preamble). The content collapse existed only in the local /api/brain-history, so the cloud blob shipped every sibling; the user pair escaped even locally because the preamble defeats the exact-string key and the raw text sits under the 40-char floor.
- **What:** new `clawmetry/brain_dedupe.py`, the single collapse implementation used by routes/brain.py AND both cloud blob builders (`_build_brain_events`, `_build_brain_events_window`). Text keys are normalized (preambles stripped, whitespace collapsed); a same-session short-text pass (10 s window) dedupes short inbound messages without ever merging cross-session broadcasts; the richest row wins (transcript copy with cost over echoes). The Telegram channel pill now unwraps a sender block (name/username/id) instead of String()-ing it.
- **Verified:** 14 tests built from the real incident rows (collapse both directions, must-not-collapse guards, revert-proven red on un-fixed code); live E2E against the real store: the incident window returns exactly 2 rows through both the local API path and the blob builder (was 3 local, 5 cloud).

### Fix: no emoji logos in CLI output; uniform runtime bullets in `clawmetry status` (#4351) (2026-07-31)
- **Why:** founder report from a live node: the Runtimes list gave OpenClaw a lobster emoji (and NemoClaw a lightning bolt) while every family runtime got a plain bullet. It read as favoritism in a runtime-neutral product, and the double-width emoji broke the checkmark column alignment. The proxy banner carried the same emoji.
- **What:** one bullet style for every runtime row; the proxy banner drops the emoji and its em-dash. Pure output formatting, no behavior change.
- **Verified:** ran `clawmetry status` and `clawmetry proxy` live on a 9-runtime node from the branch; columns align, all rows identical in style.

### Feature: self-hosted fleet overview page at /selfhosted (#4341) (2026-07-31)
- **Why:** the 0.12.605 Enterprise release shipped the self-hosted server with JSON-only fleet APIs; operators asked "is every agent box alive and current?" and had no page to look at.
- **What:** admin-gated HTML at `/selfhosted` (SELF_HOSTED=true only): node roster with hostname, platform, daemon version, last-seen, and liveness badges (online / N min ago / N h ago), plus E2E mode and stored-event count. Zero JS, inline CSS, dark-mode aware, HTML-escaped fields. Rich per-node views remain each node's own local dashboard. The managed cloud pre-classifies the route as cloud-disabled (clawmetry-cloud #1850), so the pin audit stays clean.
- **Verified:** 3 new tests (auth 401, empty state, heartbeating node row with online badge and escaping sanity; suite 17/17); live SELF_HOSTED boot with a real heartbeat, rendered page screenshot reviewed.

### Feature: stale duplicate installs are detected and explained (#4335) (2026-07-31)
- **Why:** auto-update keeps exactly one environment current, the one the sync daemon runs from (the installer venv at `~/.clawmetry`). A leftover pip copy elsewhere on PATH (for example a pre-venv `pip install --user`) never updates, and when it shadows the venv binary, `clawmetry --version` and `clawmetry status` report a stale version while the node is actually current. Founder live-hit 2026-07-31: PATH CLI at 0.12.601 while the daemon venv ran 0.12.606, which read as "auto-update is broken".
- **What:** new `clawmetry/installs.py` install census (dist-info directory globs, no subprocess, never raises). CLI startup prints a stderr warning when this process is a stale copy outside the daemon environment, including the exact pip command for the environment that owns the copy (parsed from the console-script shebang); skipped for `--json` and the hooks/agent fast paths, silenced by `CLAWMETRY_NO_STALE_WARN=1`. `clawmetry status` shows the daemon's real version when it differs from the CLI's; `status --json` adds an `installs` block and `daemon.installed_version` (additive). `clawmetry doctor` gains an "Installs on this machine" section listing the daemon environment and every distinct `clawmetry` on PATH with versions, flagging stale copies with the fix; census warnings never affect doctor's connectivity exit code.
- **Verified:** 20 unit tests (posix + windows venv layouts, dist-info debris, `clawmetry_pro` non-match, all stale/not-stale branches, warning copy, kill switch, PATH symlink dedup, doctor never-raises); live on the affected machine: census reports both installs correctly, simulated stale state fires the warning with the correct interpreter-specific fix, real `status --json` carries the new fields.

### Fix: heartbeat liveness watchdog respects the opt-in egress gate (#4337) (2026-07-31)
- **Why:** follow-up to #4329, caught live on the Windows verification node minutes after 0.12.606 auto-rolled: the silenced 401 wall was replaced by `CRITICAL: N consecutive heartbeat failures` every ~15s — the watchdog's skip-guard knew only the #3281 local-only marker, not the new no-account state, and the daemon-error tee evicts real agent events from the Brain feed.
- **What:** the guard now keys on `cloud_egress_enabled(config)` (one truth for both no-egress states); regression test pins the watchdog to that helper.
- **Verified:** 6/6 guard tests; to be re-verified live on the same Windows node post-release (no 401s, no CRITICALs).

### Fix: cloud egress is opt-in — a self-hosted node sends nothing until the user links an account (#4329) (2026-07-31)
- **Why:** founder rule — default install = self-host, zero ingest. Gating was opt-OUT only (nocloud marker), so a never-connected node (license-key onboarding) POSTed `X-Api-Key:""` heartbeats every ~55s, got 401 + 3 retries per cycle, and filled sync.log with warnings (found live on a real Windows node).
- **What:** `config.cloud_egress_enabled()` single opt-in truth; `_post()` returns a `_no_account` sentinel on empty api_key (covers every `/ingest/*` write); `send_heartbeat()` early-returns; startup banner says once "SELF-HOSTED: no cloud account linked… run `clawmetry login`"; cycle summary reads "Ingested locally (self-hosted, nothing sent)" with no "(unencrypted)" scare-suffix. Anonymous install/update pings unchanged (install-registry funnel).
- **Verified:** 5 guard tests with network-off tripwire, revert-proven (3 red on un-fixed code); neighbors green; to be re-verified live on the Windows node post-release.

### Feature: ClawMetry Enterprise: self-hosted server mode, configurable endpoint, OTLP config export, audit export CLI (#4321) (2026-07-31)
- **Why:** enterprise buyers need self-hosting and OpenTelemetry compatibility (the checkboxes competitors win on) without giving up the managed cloud path. Everything below is additive: cloud-path defaults and the config format are unchanged.
- **What:** (1) One endpoint knob: `CLAWMETRY_ENDPOINT` env, falling back to `CLAWMETRY_INGEST_URL` (legacy), then the new `endpoint` key in `~/.clawmetry/config.json`, then the managed cloud. Every daemon/CLI/dashboard call routes through `clawmetry/endpoints.py`, including four previously hardcoded URLs; a custom endpoint also disables install telemetry and anonymous analytics so data never leaves the deployment. (2) `SELF_HOSTED=true` turns the dashboard process into a single-tenant server: `routes/selfhosted_ingest.py` speaks the daemon sync protocol (auth, heartbeat + relay, all `/ingest/*`, cache read-back, minimal approvals) on an append-only SQLite store, with node tokens (`CLAWMETRY_API_TOKENS`) + admin Basic auth, fleet endpoints, and `/api/export/events`; one-command deploy at `deploy/self-hosted/` (compose + runbook); `/auth` answers `e2e: false` by default so nodes ingest plaintext inside the VPC (`CLAWMETRY_SELF_HOSTED_E2E=1` restores blob encryption); the only optional phone-home is an off-by-default daily license ping with a documented 5-field payload. (3) The `otlp_endpoint` config key starts the GenAI trace exporter in the sync daemon (headless-safe), disjoint from the env-var dashboard scope so nothing double-exports; spans gain deterministic per-session trace ids and `execute_tool` child spans. (4) `clawmetry export --from --to --format jsonl|csv` dumps the immutable event log from the configured endpoint for compliance handoff. Docs: `docs/enterprise.md`.
- **Verified:** 30 new tests (endpoint resolution order, self-hosted flag/auth/protocol/export, OTLP span shape against an in-memory collector, export CLI) + 132 touched-area regression tests green; live smoke of a `SELF_HOSTED=true` boot end to end: `/auth` -> heartbeat (plan=enterprise, relay roundtrip) -> `/ingest/events` -> CSV and JSONL export via curl and the new CLI.
### Feature: Agent CLI Phase 1: the dashboard's core reads from the terminal (#4322) (2026-07-31)
- **Why:** everything visible in the UI should be checkable without a browser, so humans and CI can test features headlessly and AI coding agents (Claude Code, Codex, Cursor, ...) can read their own telemetry mid-task and self-correct: observe, diagnose, change behavior, verify. This makes ClawMetry part of the agent's toolchain, not just a human dashboard.
- **What:** six read-only commands in the new `clawmetry/cli_cmds/` package, dispatched on a fast path (~40ms, no dashboard import): `sessions` (list + `--transcript/--cost/--errors/--lineage/--journey/--export json|md`), `activity` (event feed; `--follow` streams NDJSON with `_meta`/`_end` frames and a resume cursor, guarded by `--idle-timeout`/`--max-events` so it can never hang), `waste` (files re-read in the same session), `progress` (forward-progress ratio + loop signals), `usage` (`--by model|day|team`, `--efficiency` grade, `--export csv`), and `selfevolve` (exit 4 with the standard upgrade body; the implementation ships in clawmetry-pro). Stable exit codes (0 ok / 3 no data source / 4 upgrade required / 6 not found), stdout carries data and stderr carries decoration, `--json` everywhere. Reads go through the sync daemon's query proxy (never the DuckDB writer lock) with a direct read-only fallback on single-process installs. Docs: `docs/CLI.md` + a `clawmetry-selfcheck` agent skill. Also fixes a real observability gap found during live verification: the Read-tool extractors missed the family-adapter `tool_calls[*]` event shape, so re-read and skills-fidelity metrics reported zero for Claude Code / Codex / Cursor sessions.
- **Verified:** 15 new hermetic tests (extractor shapes, exit-code contract, runtime prefix filtering, stream frame contract); live E2E on a real install over the daemon proxy: all commands serve real data, `usage` totals reconcile with `--by model`, and the extractor fix took Read-path rows from 0 to 208 on the same store.

### Feature: judge works with any model provider + simple verified key entry (2026-07-31)
- **Why:** founder direction on the Evals tab: "the UI should ask to enter key, simple, and should work with various models, not just Claude." Plus the live burn behind #4313: a truncated key paste was saved silently, the card said "Scoring is ON", and every judge call 401'd forever with no surface telling anyone.
- **What:** the judge card now carries an inline form: provider dropdown (Anthropic, OpenAI, Google Gemini, OpenRouter, Custom OpenAI-compatible for Ollama/LM Studio/vLLM), model field prefilled per provider, key field, base-URL field for custom, one "Save & verify" button. Saving fires one tiny real test call first; a bad key comes back as "Not saved: the provider rejected this key (unauthorized)" and nothing is written. `eval_runner` gains provider-routed `_judge_request` (Anthropic Messages / OpenAI chat.completions with max_completion_tokens / Gemini generateContent / OpenRouter / custom base URL, raw HTTP, deps unchanged), `judge_provider` in the rubric (explicit wins, else inferred from the model id), `validate_judge_key`, `set_judge_selection`, and last-judge-call status; a rejected key flips the card to a red re-add state on the next tick (closes #4313). `custom` counts as configured with only a base URL, since local servers need no key. `/api/evals/key` GET now returns the provider catalogue + selection + last status; POST validates by default (`validate:false` opt-out) and saves provider, model, key, and base URL in one step.
- **Verified:** 11 new multi-provider tests (wire shapes per provider, rubric-provider precedence, validate paths, selection rewrite, keyless-custom) + key-store/route-gate suites adapted, zero net-new failures vs the pre-existing box-flake baseline; live dev-server E2E: POST with a wrong key returned 400 "rejected (unauthorized)" and saved nothing, clearing a key works; browser walk: form renders in the card, provider switch swaps default model/hint/base-URL field, bad paste shows the red inline reason (screenshots in .claude/).

### Feat: `clawmetry login` + one-flag cloud-sync toggles, all discoverable in `--help` (#4316) (2026-07-31)
- **Why:** signing in or pausing cloud sync required knowing the connect/disconnect/nocloud-marker machinery. A non-engineer needs one obvious command for "log me in" and one flag each for sync on/off (founder request).
- **What:** `clawmetry login` shows account info when a key exists, otherwise runs the existing interactive connect flow (email OTP / Google/GitHub incl. headless paste-code). `--turn-off-cloud-sync` writes the `~/.clawmetry/nocloud` marker — the daemon checks it on every cloud POST so egress stops within seconds, no restart, account key kept (unlike `disconnect`). `--turn-on-cloud-sync` removes it via `config.enable_cloud()`, warns when `CLAWMETRY_NO_CLOUD` env still forces local-only, and points to `login` when no account is linked. `--help`/`help` gains a Cloud section listing login/connect/disconnect/doctor + both toggles.
- **Verified:** 7 unit tests incl. a help-text contract guard; `--help` output visually confirmed; ruff zero-delta vs main.

### Feat: enterprise networks — corporate TLS interception support, `clawmetry doctor`, no more flashing console windows (#4312) (2026-07-31)
- **Why:** on enterprise Windows machines behind TLS-intercepting proxies (Zscaler/Netskope/Palo Alto), every cloud call died with `CERTIFICATE_VERIFY_FAILED: CA cert does not include key usage extension` — the proxy re-signs TLS with an internal root CA that is in the Windows cert store but not certifi's bundle, and Python 3.13's default-on `VERIFY_X509_STRICT` rejects corporate CAs lacking the keyUsage extension (real customer failure, Windows 11 + Python 3.13). Separately, the detached (console-less) Windows daemon made every periodic subprocess probe flash a visible cmd window — scary enough that a pilot flagged it.
- **What:** new `clawmetry/net.py` process-wide bootstrap at daemon/CLI/dashboard start: OS trust store via `truststore.inject_into_ssl()` (dep gated `python_version >= "3.10"`, guarded fallback to certifi), clears `VERIFY_X509_STRICT` while keeping hostname + chain validation ON, loads `CLAWMETRY_CA_BUNDLE` env / config `ca_bundle` / `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` on top of system trust, installs a global urllib opener that re-reads `HTTPS_PROXY`/`NO_PROXY` at daemon start, and a loudly-warned `tls_verify:false` / `CLAWMETRY_TLS_NO_VERIFY=1` pilot escape hatch. New `clawmetry doctor` subcommand (DNS → TCP → proxy CONNECT → TLS → heartbeat POST; on failure fetches the peer cert verification-off and prints the issuer + certmgr.msc Base-64 export walkthrough; exit 0 only when all pass). New `clawmetry/winconsole.py` patches `subprocess.Popen` with `CREATE_NO_WINDOW` so daemon children never open console windows; `dashboard._start_daemon_background` gets real Windows detach flags (`start_new_session` is POSIX-only). Docs: `docs/enterprise-networking.md`.
- **Verified:** 32 unit tests green on py3.9 + py3.13; new `windows-enterprise-tls.yml` CI ran REAL interception on windows-latest/py3.13 (mitmproxy): untrusted → doctor exit 1 + "TLS interception detected" guidance; CA certutil-imported into the Windows Root store → truststore validated through the proxy and the heartbeat POST reached ingest.clawmetry.com (HTTP 401 = transport works); store cleared + `CLAWMETRY_CA_BUNDLE` → full pass. Live doctor runs green on macOS (certifi fallback) and failure-path verified against self-signed.badssl.com.

### Feature: install lifecycle telemetry + mandatory first-run onboarding gate (#4286, #4288) (2026-07-31)
- **Why:** the 7k-downloads-a-day investigation showed PyPI counts are almost entirely mirrors, CI, and our own auto-update fleet (roughly 50-100 real installs/day), and the funnel could not say whether any install ever onboarded: the install ping fired once per install forever, upgrades were invisible, and installs could not be linked to nodes or accounts.
- **What:** telemetry now reports one anonymous `install` event per install, one `update` per new version (including headless daemons after auto-updates), and one `onboarded` event carrying the choice made; the authenticated heartbeat and license activation carry `install_id` so the cloud installs registry links every install to its node and account. New first-run gate on the dashboard: pick Managed cloud (existing OTP/Google/GitHub connect) or Self-host (free 7-day Pro trial via email code, or a CLAW1 license key). Installs already cloud-connected or licensed never see it; CI environments and `CLAWMETRY_SKIP_ONBOARDING=1` bypass it; the hosted dashboard never gates. Cloud counterpart (merged + deployed): installs board and truthful growth tiles in the Founder Console.
- **Verified:** 40 new tests across both suites; gate screenshot-reviewed; cloud half verified live end to end (onboarded event posted to production, row with onboarding_state read back from Postgres, then removed).

### Feature: dedicated Evals tab + honest per-box "Live" badges (2026-07-31)
- **Why:** founder audit: the Overview card said the evaluator library was "live" while the LLM-as-judge had scored zero sessions on the box — the judge ships wired into the sync daemon (claude-haiku-4-5 on the user's own key, 100/hr cap, redacted transcripts) but is silent until a judge API key exists, and the static catalogue badge never said so. Real infrastructure deserved a real home and honest state, not a card that overstates.
- **What:** new left-nav **Evals** tab (`tabs/evals.html`): judge status card (model, key presence, plain-language how-it-works, one-click key setup), 24h score summary + p50/p10 + 7d regression-replay line, the full named-evaluator library (moved from Overview; Overview keeps a one-line strip linking to the tab), recently-scored sessions with per-row re-score, and golden-suite list (`GET /api/evals/suites`, new). `catalogue_with_coverage` gains `judge_ready`: on a box with a store and no judge key, judge-backed evaluators (answer-quality) report **needs_key** ("Needs key" amber badge + "Add a judge API key" action) instead of "Live", and the payload's `live` count drops accordingly; `/api/evaluators` now attaches `judge: {enabled, key_present, keys, model}`. Cloud container (no store) keeps static statuses so a keyless relay env never mislabels a node.
- **Verified:** 10/10 catalogue tests incl. new needs_key downgrade + faithfulness-hook-without-key tests; i18n guards green (8 new en.json keys, logs.html entity fix); worktree dev-server browser walk: Evals nav item renders, judge card shows the honest amber "Waiting for a judge API key" state with model + key status, "5 / 10 live now" count, "Needs key" badges on answer-quality + faithfulness, honest empty recent/suites cards, Overview one-line strip. Judge scoring itself stays idle until the operator adds a key (by design; the tab's one-click setup is the activation path).

### Feature: locked runtimes lead to in-dashboard sign-in + trial, never a pricing tab (#4287) (2026-07-31)
- **Why:** the founder's original report: clicking a paid runtime dumped users at the pricing page / external upgrade URL even after sign-in-first onboarding shipped; the dashboard already had the whole rail (cloud-cta OTP + /api/trial/activate minting and activating the trial license locally) but the paywall never used it.
- **What:** the runtime-switcher paywall CTA runs an inline email -> code -> activate flow and reloads on success so the runtime unlocks in place; the Agents empty-state CTA opens the same modal; plan-ladder prices corrected to live pricing (Pro $19/$190, was stale $29/$290).
- **Verified:** live in the founder dashboard: CTA click reveals the sign-in step, $19/node/mo renders, no external upgrade links remain in the modal.

### Feature: Conversations time-window picker for post-mortem digging (#4284) (2026-07-31)
- **Why:** founder request during the 2026-07-30 Brain-window RCA (#4285): when a P0 lands, developers need to time-travel — pick the incident window and read exactly which conversations were active and what context the agent had, then write the RCA. Brain already had a range picker; Conversations didn't.
- **What:** the Conversations tab gains the same range bar as Brain — Live (default) / 1h / 6h / 24h / 7d / Custom with From/To pickers, a "Viewing history · X → Y" banner with Back to live, and an overlap filter on [started, modified] so a conversation that began before the window but was still active inside it is listed. `/api/transcripts`' DuckDB fast path now ships `started` (ms) alongside `modified`; new i18n keys ride the autotranslate bot; honest window-scoped empty state. Companion cloud PR #1829 (merged) makes the hosted interceptor emit `started` too.
- **Verified:** in the running app (worktree boot): Live=50 rows → 24h=38 → a 1-hour slice from 2 days ago=1 genuinely-active conversation → back to live=50; banner/active-button/empty states confirmed in-browser; 2 new tests on the `started` emission.
- **Why:** founder screenshots: the Agents tab showed a different row set and fold count for every runtime-switcher choice while its own banner promised a node-wide view (the selected runtime was force-promoted out of the 24h-inactive fold and re-sorted to row 0); the "Show N inactive agents" row was not clickable anywhere (the toggle tr landed in an implicit anonymous tbody, so the handler's sibling lookup silently no-oped, and it had no pointer cursor); and a Claude Max machine showed hundreds of API-equivalent dollars with no hint that the subscription covers them. Bonus: the "Today" tile summed lifetime cost.
- **What:** the active/inactive partition now depends only on real activity, with the selected runtime highlighted in place, so the roster is identical across switcher changes; the fold toggle lives in an explicit tbody, resolves its body via closest('table'), and looks clickable; the daemon's agent-inventory slice carries the same billing detection the desk device uses (per-agent covered/metered chip, accountPlan, extraCost24hUsd), so the Today tile mirrors the device hero ("$0.00 extra / Claude Max 20x covers it, ~$85 at API rates") and the tile sums the last 24h, not lifetime. Doing-now gains the device's 24h token count.
- **Verified:** real headless-Chromium harness against the shipped app.js: identical row set and fold text across all/claude_code/openclaw, fold click reveals all six hidden rows, covered hero and chips render; 11 new revert-proven guards (10 fail on the un-fixed code); neighboring inventory and i18n suites green.

### Fix: ghost installs self-heal, self-update timeout rolls back (#4270) (2026-07-30)
- **Why:** founder live-hit: the one-line installer printed success but ended with "bash: ~/.local/bin/clawmetry: No such file or directory" and the dashboard could not start. A pip killed mid-install (the daemon self-update's 180s timeout) lays down the new wheel's files but never generates console scripts, so site-packages claims the latest version while bin/clawmetry is gone; every later plain upgrade no-ops against that metadata and the symlink dangles. Forensics on the machine: dist-info with no INSTALLER file and no bin/ entries in RECORD.
- **What:** install.sh now checks the entry point after installing and force-reinstalls when it is missing (uv path plus an ensurepip/pip fallback), before creating the symlink; the version banner probes with python3 -I so a source checkout's stale egg-info cannot misreport the installed version. perform_self_update rolls back on TimeoutExpired and generic exceptions too (previously only a nonzero pip exit), and the rollback uses --force-reinstall --no-deps so entry points regenerate regardless of what the half-installed metadata claims.
- **Verified:** reproduced on the affected machine (entry point deleted, patched installer re-run: repair step fired, CLI and dashboard restored); install-test.yml now deletes the entry point and re-runs the installer on linux and macos; 8 new tests, revert-proven (6 fail on the un-fixed code); the served clawmetry.com/install.sh proxies raw main and was curl-verified to carry the fix post-merge.

### Fix: local-only tells the truth everywhere + Managed-first onboard (#4264, #4265) (2026-07-30)
- **Why:** founder live-hits on a signed-in Self-Host node: green "Cloud Connected" badge, "Cloud sync: Connected" in status, and "Synced ... (E2E encrypted)" daemon logs — on a machine whose nocloud marker was correctly blocking all egress (cloud showed zero nodes). Separately, the Activity pane parked forever on "Failed to load: timeout" from an SSE connection-slot leak plus a never-retried boot-jank abort.
- **What:** /api/cloud-cta/status returns {connected, account_linked, local_only} with local-only winning; the badge renders an amber Local-only pill; clawmetry status prints "Local-only (account linked; data stays on this machine)" (+ cloud_sync.local_only in --json); the daemon cycle logs "Ingested locally (local-only, nothing sent)". Activity: switchTab closes pane-scoped SSE streams; one deferred retry heals the timeout error. Onboard: [1] Managed (default; we host, easy for a large fleet, both app.clawmetry.com and localhost:8900) / [2] Self-Host (great for one node, fleet is yours); cloud finale ensures the local dashboard serves; headless/EOF still never creates an account.
- **Verified:** all four honesty surfaces live-verified on the reporting machine (marker present, zero cloud nodes); Activity settles into a rendered feed with 3 concurrent streams; 20 onboard tests green.

### Fix: Self-Hosted sign-in never touches the cloud dashboard (#4258) (2026-07-30)
- **Why:** founder live-run: the Self-Hosted trial sign-in held the data promise (marker kept, 0 nodes synced) but connect's finale ran the cloud ceremony anyway: E2E key prompt + secret printed, then "All done! Opening your dashboard..." launching app.clawmetry.com/cloud with the key in the URL fragment.
- **What:** keep-local sign-ins say "Verifying your account…", skip the encryption-key ceremony entirely (silent auto-generate), never print the secret or a cloud URL, and end by opening http://localhost:8900. Drive-by: probe-count asserts 14 -> 15 for n8n.
- **Verified:** 29 onboard/probe tests green.

### Fix: OTP sign-in is recoverable (#4257) (2026-07-30)
- **Why:** founder live-hit at the 6-digit-code prompt: a typo'd email or an undelivered code was a dead end (no resend, no change-email, a stray Enter burned one of the 3 attempts, three failures dropped to a raw paste-an-API-key prompt) — the classic OTP abandonment point.
- **What:** at the code prompt r resends and typing an email IS the typo fix (switches address, fresh code there); blank input never burns an attempt; three wrong codes offer a different-email/resend/stop fork; send failures offer corrected-email retry; invalid emails get one re-prompt, with a hint line printed right after send.
- **Verified:** 5 tests drive the full journeys against a scripted server (typo-fix at code prompt, double resend, blanks-don't-burn, 3-wrong-then-new-email, invalid-email retry).

### Feature: n8n is the 15th observed runtime (2026-07-30)
- **Why:** n8n is the largest open-source workflow-automation platform and its AI Agent nodes make it an agent runtime, but it has no per-run token or cost observability of its own (token usage is buried on the model sub-node's run data and never surfaced). Per-step AI cost attribution is exactly what ClawMetry does. Scoped in clawmetry-pro#108; Activepieces was assessed in the same pass and deferred.
- **What:** OSS side of the chain: `n8n` joins `PAID_RUNTIMES` + labels + aliases-free catalogue, the family adapter specs (`clawmetry_pro.adapters.n8n`), the runtime session-id prefix registries (sync, local_store, app.js), the free-tier presence probe (`~/.n8n`, honors `N8N_USER_FOLDER`), lite detection + recency data paths, the runtime switcher (label, prefix, caps `SESSIONS/EVENTS/COST`), Flow lane, pixel logo sprite (`rt-n8n` + chip) + manifest + brand. The adapter itself (SQLite `~/.n8n/database.sqlite`, WAL-aware read-only, flatted decoder, workflow executions as sessions, node runs as tool calls, AI Agent prompt + model attribution, REST stop-execution kill handler) ships in clawmetry-pro 0.5.0.
- **Verified:** real n8n 2.32.6 capture (CLI import + execute: success, intentional failure, AI-agent run) drives 37 adapter tests in clawmetry-pro incl. a WAL-visibility regression guard; OSS pin suites green (labels/logos/no-leak/catalogue/entitlements/capability parity, 173 tests). Token-bearing success capture still needs a real model key before COST is advertised as verified.
### Feature: onboard is a two-option fork with plans stated once (#4249, #4250) (2026-07-30)
- **Why:** founder redesign: the fork should be purely WHERE it runs (Self-Hosted vs Cloud); sign-in is just how the trial starts on either path, and the per-option tier repetition read like three pricing pages in a terminal.
- **What:** a Plans block printed once above the menu, tiers stacked (Free $0 watch OpenClaw + NVIDIA NemoClaw forever; Starter $9/node/mo everything in Free + observability for all 14 runtimes; Pro $19/node/mo everything in Starter + governance: alerts, approvals, evals). [1] Self-Hosted (default): have-key -> paste/activate, else "Start your free 7-day Pro trial? [Y/n]" -> connect keep-local mode (new args.keep_local skips the Case-B re-prompt; marker kept, trial minted + activated, dashboard ensured); declined -> free tier. [2] Cloud: full connect with the E2E story in the copy (snapshots sealed on-machine, only you hold the key), fleet dashboard + desk device named. Headless/EOF/--local unchanged: free local, no account.
- **Verified:** 32 onboard tests green including plans-stated-once and stacked-tier copy pins; full flow rendered live on a 10-runtime machine.

### Feature: keeping data local still signs you in and activates the trial (#4237) (2026-07-30)
- **Why:** founder hit it live: [1] Sign in on a nocloud machine fell into connect's "keep local-only?" prompt, and answering keep dropped the auth entirely — no account, no trial key, paid runtimes gated behind a bare pricing link. Identity is what unlocks runtimes; egress is a separate decision.
- **What:** connect's keep-local answer now offers "Sign in anyway to unlock every runtime here with a free 7-day Pro trial license? [Y/n]" — yes runs the normal Google/GitHub/email auth with the nocloud marker kept (cloud enable + backfill skipped, marker re-touched, local dashboard ensured and health-checked); _activate_signup_trial() is module-level and runs at the end of every successful connect, so bare connect sign-ins mint their trial too and onboard no longer double-calls.
- **Verified:** 31 onboard tests green; trial helper covered directly (mints+activates live key; refuses expired with an honest pricing notice).

### Fix: local-only onboard actually serves localhost:8900 and says so truthfully (#4224) (2026-07-29)
- **Why:** founder screenshots: onboard printed "Watching your agents locally / http://localhost:8900" while the port refused connections — only the sync daemon was ever started, no process served the dashboard on a local-only machine; two lines above, "Your data is syncing to the cloud" printed on a node whose promise is that nothing leaves it; and [1] Sign in was re-asked "keep local-only?" by connect's marker prompt, where [2] silently dropped the chosen auth.
- **What:** _ensure_local_dashboard() health-checks the port, registers a KeepAlive com.clawmetry.dashboard launchd job (or detached-subprocess fallback) when silent, and polls within a hard 12s bound; the URL prints with "(live now)" only when the port answered, else an honest "did not come up: start it yourself: clawmetry, logs: ~/.clawmetry/dashboard.log". Daemon-registration copy is mode-aware (local-only says "Nothing leaves this machine."). Onboard [1] clears the nocloud marker before connect; a failed sign-in restores it.
- **Verified:** on the reporting machine itself: curl 8900 000 -> ran the helper -> launchd job -> curl 200, dashboard live; 26 onboard tests green (7 new).

### Feature: onboard signs you in first, then hands you a 7-day Pro trial (#4220) (2026-07-29)
- **Why:** the menu asked a hosting question (local/cloud/key) at the exact moment the user wants to see their agents, and the anonymous instant-register path meant sign-ups with no identity; the founder's spec: authenticate everyone first (Google, GitHub, or email OTP), then unlock every runtime locally through a real trial license key on the same rail Self-Hosted Pro uses.
- **What:** [1] Sign in / Sign up (default) runs the existing connect auth then calls the cloud's POST /api/license/trial/signup and activates the returned 7-day tier=trial key locally; re-runs reissue the same trial (original expiry, one per email across the CLI and dashboard flows) and an expired trial prints an honest notice. [2] License key forks on "do you have one?" and sends key-less users to clawmetry.com/pricing?deploy=self with the Self-Hosted toggle preselected. [3] Skip for now is the old local-only. EOF/no-TTY/--local/CLAWMETRY_LOCAL_ONLY still never mint an account; anonymous _instant_register is no longer reachable from onboard.
- **Verified:** 22 onboard tests green including full sign-in→trial→activate wiring against a faked endpoint; menu + detection copy rendered live on a 10-runtime machine; pricing deep-link browser-verified live (data-deployment="self", Buy License CTAs).

### Release fix: republish so the detection grid actually ships (#4218) (2026-07-29)
- **Why:** the published 0.12.587 wheel was built from a stale checkout: cracking it shows the pre-#4215 runtime_probe (per-line tier labels) and dashboard.py still at 0.12.586, even though the v0.12.587 tag points at the correct merge commit. The FLYWHEEL-documented release race (0.12.453 class): a wheel must be verified, not assumed, before the version is treated as carrying the change.
- **What:** no code change; this release exists to rebuild from current main so the next published wheel contains #4215.
- **Verified:** wheel-crack of the new version must show the 3-per-row grid renderer and the [x]-swap styling in cli.py before this entry's version is cited anywhere.

### Feature: onboard detection block reads as one confident grid (#4215) (2026-07-29)
- **Why:** the wizard's runtime-detection list printed a per-line tier label, so a typical dev machine saw nine "(Pro)" tags plus a 3-line license paragraph before the product had shown any value: a paywall ledger as the welcome mat, at the exact conversion moment #3917 was built for.
- **What:** detections render as a 3-per-row checkmark grid (10 runtimes = 4 lines instead of 10) with the tier story told exactly once in two quiet summary lines pointing at the [2] Cloud / [3] license-key menu options; both unlock paths and the "Free forever" copy survive verbatim; entitlements, pricing, and the menu are untouched.
- **Verified:** rendered live on a 10-runtime machine with the wizard's exact styling: 12 lines to 7, columns aligned; 9 detection tests (2 new pinning grid shape + singular unlock line) and the 12 entitlement-API detection tests pass.

### Fix: connect backfills local-only history to the cloud (#4197) (2026-07-29)
- **Why:** after running local-only on a trial license, Enable Cloud Sync connected the account but the cloud dashboard sat at "No machines connected yet / 0 sessions": the family high-water marks were stamped done during local-only ingest, so the first cloud-connected pass skipped every session.
- **What:** clawmetry connect clears the family high-water marks after saving the config; the next daemon pass re-ingests every session (idempotent locally) and pushes the full set to the newly connected account, printing "Queued N existing session(s) for cloud backfill". No-op on fresh installs; best-effort so connect never fails on housekeeping.
- **Verified:** the manual equivalent on the reporting machine re-synced 3,948 events to the cloud on the next family pass; wiring and reset behavior are pinned by revert-proof tests.

### Feature: Notifications sits next to Approvals and Alerts (#4193) (2026-07-29)
- **Why:** founder request with screenshot: the channel manager was buried in the collapsed Advanced drawer, so the natural journey "Alerts says no channels, where do I add one?" dead-ended two groups away from the tabs that consume it.
- **What:** the Notifications item rides Tier-1 directly beneath Approvals and Alerts (envelope icon, tooltip naming the four channel types); removed from the Advanced drawer; data-tab id and switchTab('notifications') unchanged so deep links keep working; nav guard tests pin the new eight-item order.
- **Verified:** live browser walk on the requesting machine: the sidebar renders with Notifications directly under Alerts and clicking it opens the channel manager ("1 channel configured, plan: trial").

### Fix: a connected notification channel actually shows as connected (#4188) (2026-07-29)
- **Why:** the self-hosted Notifications tab unlocked locally, but a channel the user connected never showed as connected: the card stayed on "Connect", the status stuck on "No channels configured yet", and an enabled alert rule kept its "no channels" dead end.
- **What:** the tab's channel loader read a stale variable name (the swallowed ReferenceError left the row list empty every load); and dashboard.py's duplicated alerts-webhook config trio meant the winning save function silently dropped the telegram keys the API route accepts. Both copies now persist telegram_bot_token / telegram_chat_id and the loader reads the variable it declared.
- **Verified:** live on the reporting machine: saving a Telegram channel echoes the token, persists across reload, the tab renders "1 channel configured, plan: trial" with the Telegram card on Edit + Test, and the Alerts tab shows zero "no channels" chips; the two new tests fail on the un-fixed code.

### Fix: the full event log is visible, nothing stripped (#4181) (2026-07-29)
- **Why:** every Activity/Brain feed row was cut at exactly 200 characters server-side (300 on the legacy and SSE paths), mid-word, and expanding a row showed the same stub because the server had already thrown the rest away; encrypted-thinking rows rendered as blank lines that read like more truncation.
- **What:** the local-store fast path, the legacy JSONL path, and the SSE live stream serve the complete detail (bounded upstream by the 64 KB ingest cap on tool-result bodies); collapsed rows line-clamp to three lines client-side and click-to-expand reveals everything; thinking events whose text the runtime never stored get an honest placeholder.
- **Verified:** live on the reporting machine: max served detail went 200 to 3,622 chars with zero rows at exactly 200; guard tests fail on the old caps.

### Fix: the Agents roster shows real numbers, no phantom OpenClaw (#4182) (2026-07-29)
- **Why:** on a fresh Windows machine the roster showed "OpenClaw / detected" with no OpenClaw installed and 0 conversations / $0 for every runtime despite real ingested sessions: query_model_rollup was missing from the daemon-proxy allowlist (so every roster number zeroed when the dashboard composed the roster), and the builder kept every zero-substance runtime bucket with OpenClaw hard-coded detected.
- **What:** query_model_rollup joins the daemon-proxy allowlist; a roster row must be detected or have recorded work (sessions/turns/tokens/cost incl. rolling windows); OpenClaw's detected flag is adapter-or-substance, never unconditional; freshly installed runtimes with no ingest yet still show.
- **Verified:** live on the reporting machine the roster went from three zero rows to exactly one true row (Claude Code, 3 conversations, real cost, real model); two of the five new tests fail on the old code.

### Fix: CI runners never self-update mid-job (#4183) (2026-07-29)
- **Why:** the recurring visual-diff "flake" was the auto-updater: its startup check fires 60s after boot, so whenever a release had just published, the PR-branch dashboard in CI pip-updated and exec-restarted itself mid-screenshot-sweep; the failure rate tracked release cadence.
- **What:** a truthy CI environment variable implicitly disables unattended upgrades (an ephemeral runner must render the code it was started with); CLAWMETRY_AUTO_UPDATE=1 re-arms explicitly, =0 still hard-disables, user machines are unchanged.
- **Verified:** the first guarded visual-diff run completed all 66 comparisons with zero render-errors where three prior runs died mid-sweep; new tests pin the CI guard, the opt-in override, and kill-switch precedence.

### Fix: the Notifications channel manager works self-hosted (#4178) (2026-07-29)
- **Why:** the Notifications tab (the delivery-destination manager Alerts and Approvals use) hard-locked behind a cloud signup and only recognized cloud accounts, so enabled alert rules said "no channels" with no way to add one - even on a validly entitled self-hosted trial.
- **What:** local-first tier resolution; a local channel adapter over /api/alert-channels so Slack, Telegram, and PagerDuty connect, edit, test, and deliver entirely from this machine (telegram keys newly accepted; the local test endpoint gains telegram and pagerduty targets); Alerts reads its channel chips from the same local config. Email and Phone honestly remain cloud-only.
- **Verified:** live on the affected machine: no signup lock, five channel cards, plan trial; a telegram config saved locally and the local test attempted real delivery. Guard tests pin the adapter and the local-first resolution.

### Feat: alerts and approvals fully work self-hosted, gated by the real trial lifecycle (#4172, #4173, #4171) (2026-07-28)
- **Why:** the Alerts tab only recognized cloud accounts, so a machine holding a valid self-hosted trial key got a "Sign up for ClawMetry Cloud" modal selling it the trial it already had; and in grace mode an EXPIRED trial remained a permanent unlock because the permissive branch ran before any expiry check. Founder directive: alerts and approvals must work self-hosted, stop at trial expiry, and continue on a fully paid key.
- **What:** the Alerts tab resolves the LOCAL entitlement first and, when entitled, reads and writes rules through the local routes (cloud vocabulary accepted and mapped); Approvals was already local and properly gated. Grace mode now never covers an expired entitlement, so the whole paid surface (alerts, approvals, paid runtime watch) dies when the trial lapses and lives indefinitely on a paid key, while never-entitled installs keep full grace. Also carries #4171: the Windows update lock rides through the helper handoff (no more concurrent sibling pips) with a propagation-sized retry ladder.
- **Verified:** live on the founder's machine: Alerts tab with no signup modal and a cost_daily rule saved locally; full lifecycle pinned through the real @gate decorators over a real key file (active trial 200 / expired trial 402 / paid 200 / no-license grace intact), revert-proof red on the old gates.

### Fix: the auto-update relaunch gets a UTF-8 stdout (#4168) (2026-07-28)
- **Why:** the 0.12.579 unattended run proved detect + install + relaunch, and the freshly relaunched dashboard then died printing its own startup banner: its stdout is the updater helper's log file, not a console, so Python picked cp1252 and the banner's arrows and emoji raised UnicodeEncodeError.
- **What:** the helper exports PYTHONIOENCODING=utf-8 and PYTHONUTF8=1 into the relaunch environment.
- **Verified:** guard test asserts both vars on the relaunch; overlay confirmed live on the affected machine.

### Feat: the runtime switcher defaults to the one runtime that has sessions (#4164) (2026-07-28)
- **Why:** a Claude-Code-only machine listed OpenClaw 0 sessions, NemoClaw 0 sessions, Claude Code 3 sessions, and still made the user pick by hand on first visit.
- **What:** when the user has never chosen a runtime (no stored key, no URL pin) and exactly one runtime has sessions, the switcher defaults to it, persisted through the same path as a manual pick so later choices always win. Multiple non-zero runtimes or none keep the honest All-runtimes aggregate; OTLP apps and URL-pinned tabs are exempt. Runs before the switcher's single-runtime visibility gate, which used to early-return past any chance to default.
- **Verified:** fresh headless browser against the live machine: clean profile lands on claude_code with no interaction; JS contract test guards the conditions.

### Fix: Windows relaunch uses the .exe when argv0 is the extensionless launcher (#4154) (2026-07-28)
- **Why:** the first live unattended update detected and installed in ten seconds, then the dashboard relaunch died with Errno 2: console-script argv0 on Windows is the extensionless launcher path, so the fallback built a python invocation of a file that does not exist.
- **What:** _respawn_cmdline probes argv0 plus .exe. With this the full loop (detect, install, relaunch) is hands-free on Windows.
- **Verified:** revert-proof test on the Windows runner; this release IS the third live proof run, executed by the shipped 0.12.577 helper on the affected machine.

### Fix: Windows auto-update installs out-of-process, and failed attempts are visible (#4146) (2026-07-28)
- **Why:** the first live unattended-update run failed silently. Measured in isolation on the affected machine: Windows denies even RENAMING the running clawmetry.exe (WinError 32), so the pre-rename that in-process pip relied on never protected anything, every attempt failed into a 30-minute backoff, and the failures were recorded nowhere a human could see.
- **What:** on Windows the updater now runs NO in-process pip: a detached stdlib-only helper (clawmetry.update_respawn) waits for the process to exit, installs the target with one retry, and relaunches the exact command line even when the install fails. Every attempt (started/handoff/installed/failed plus pip's error tail) is persisted and served as last_attempt in /api/update-check/status. Status wording: runtimes are "watching (local)"; "syncing" is reserved for the explicit Cloud sync line; the hardcoded OpenClaw line is detection-gated.
- **Verified:** helper chain live on the affected machine (wait, real pip, relaunch proof file); 39 update-suite tests green; this release is the second live proof run for the five-minute unattended bar.

### Fix: trial hotfixes, the properties bug, the unclosable modal, honest status copy (#4140) (2026-07-28)
- **Why:** three follow-ups found live minutes after 0.12.575: Entitlement.is_paid/.expired are properties and the new license-override code called them as methods (silently reverting status to "FREE plan" under a valid trial key); /api/auth/check returned needsSetup on machines with no OpenClaw, which app.js renders as a mandatory close-button-hidden modal on every load; and status copy framed cloud sync as the goal of a local trial.
- **What:** property access fixed in the sync gate and status; needsSetup now fires only when an OpenClaw install is actually present; status says "watching ... locally (Trial plan)". Tests now build REAL Entitlement objects instead of shape-alike doubles, so the property/method class of bug goes red in CI.
- **Verified:** live on the affected machine: status shows Claude Code watching (Trial plan); auth/check returns needsSetup=false; fresh Playwright load shows the modal and banner both gone with the Claude Code home tab fully rendered. This release also serves as the live proof of #4133: the affected machine must self-update onto it unattended within five minutes of PyPI.

### Fix: every install self-updates within minutes, on every OS (#4133) (2026-07-28)
- **Why:** the founder's Windows machine stayed on 0.12.573 after 0.12.574 shipped, banner dutifully reporting update_available. Auto-update was daemon-role-only and a local-only install has no daemon, so no process on such a machine could ever install a release; and on Windows even an opted-in process could not restart itself (the restart path was exit-and-let-launchd/systemd-respawn, and Windows has neither).
- **What:** default-on auto-update now applies to every role, with an actual restart mechanism per situation (_restart_plan): supervised POSIX exits for the supervisor to respawn; unsupervised POSIX re-execs in place; Windows spawns a detached helper that relaunches the exact command line about five seconds after exit, output to ~/.clawmetry/restart.log. The dashboard joins the 60-second PyPI poll whenever auto-update is on; CLAWMETRY_AUTO_UPDATE=0 restores the banner-only daily cadence. A cross-process lock serializes pip between the daemon and dashboard fast loops.
- **Verified:** 66 update-suite tests green; revert-proof red on the old daemon-only rail. Also defuses a latent test landmine (the unsupervised-daemon test armed a REAL os.execv timer inside pytest).

### Fix: the local trial actually turns the product on (#4136) (2026-07-28)
- **Why:** activating the local trial wrote a valid key and flipped the dashboard tier to Trial, and then nothing else happened: status said "FREE plan, NOT syncing", the three detected Claude Code sessions never ingested, the setup modal greeted every load, and the empty-state banner pitched installing OpenClaw. Five broken links, found live on the founder's machine minutes after the first real trial activation.
- **What:** a valid self-hosted license now overrides the cloud "paused" verdict in the daemon's sync gate (which also guards LOCAL DuckDB ingest); run_daemon() falls back to an in-memory local-only config instead of crash-looping on "Run: clawmetry connect"; clawmetry status resolves entitlement through clawmetry.entitlements like every other surface; POST /api/trial/activate spawns the sync daemon so ingestion starts with the trial; and the setup modal + no-agent banner suppress themselves when every detected runtime is already watched.
- **Verified:** live on the affected machine: the fixed daemon logs "local-only mode", ingests all three Claude Code sessions (runtime=claude_code) into DuckDB, and /api/sessions serves them. 8 new tests; revert-proof red on the sync-gate override; JS contract guards on both frontend suppressions.

### Feat: start the free trial from the local dashboard, no cloud tab required (#4120) (2026-07-27)
- **Why:** trying a paid runtime (Claude Code, Codex, Cursor, and the rest) required the full cloud sign-up: an account page in a new tab, node registration, then a daemon heartbeat before the plan reached the local install. For someone who just ran pip install on their own machine that is a funnel cliff at the exact conversion moment. The founder called it out live while prepping a Windows product demo.
- **What:** the setup modal now takes an email, the existing send-otp proxy mails the 6-digit code, and the new POST /api/trial/activate exchanges the verified code with the license server (POST /api/license/trial, shipped in clawmetry-cloud #1791) for a signed 7-day trial key, activated through the existing license.activate() path: written 0600, entitlement cache invalidated, pro wheel auto-provisioned. The signed key IS the entitlement and verifies offline, so the trial keeps working with no cloud session and no network. Includes the load-bearing mapping fix: parse_license coerced unknown tiers to TIER_PRO, so a trial token would have silently granted full Pro; tier=trial now maps to TIER_TRIAL. One trial per email server-side, with same-clock reissue for lost keys.
- **Verified:** full browser E2E (Playwright) on a real Windows 10 machine against the real dashboard + the real cloud handler code: email step, wrong-code error surfaced, correct code, key written and verified on disk, entitlement flipped oss to trial, claude_code unlocked in runtime-detection after reload. 8 hermetic tests per repo plus revert-proofs on both tier fixes (red on un-fixed code, green restored). Cloud endpoint verified live post-deploy on app.clawmetry.com.

### Fix: Windows demo-readiness batch, found by running the dashboard on a real Windows 10 box (#4117) (2026-07-27)
- **Why:** four Windows failure classes, all silent: Claude Code sessions never synced (the cwd slug encoder handled only "/" and "." so C:\Users\Name never matched the real C--Users-Name project dir); the Disk/RAM/Load tiles rendered "--" (df/free//proc/loadavg do not exist on Windows and every call site swallowed the failure); setup demanded an OpenClaw gateway token on machines with no OpenClaw, printing a POSIX pipeline as the how-to on Windows; and the sync daemon died whenever the launching terminal closed (start_new_session is a POSIX no-op, so the daemon sat in the console's process group).
- **What:** the slug encoder collapses backslash and the drive colon; helpers/system.py gains stdlib-only disk/memory/load/CPU probes (GlobalMemoryStatusEx, GetSystemTimes deltas, registry CPU model) with the Load slot falling back to CPU utilisation where load average does not exist; runtime detection (/api/entitlement/runtime-detection, previously unconsumed) now drives the setup step, listing what was actually found with the gateway path one click away and a PowerShell token hint on Windows; the daemon spawns DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP; the pid file honours TEMP; hardware probing falls back from wmic (absent on Windows 11 24H2+) to the registry; sessions.json is read as UTF-8 (an emoji in a session title used to raise UnicodeDecodeError under cp1252 and skip the channel preload).
- **Verified:** every fix exercised on the real Windows machine (slug verified against the actual ~/.claude/projects dir; tiles show real values; modal rendered via Playwright screenshot; wmic-absent path simulated and red/green proven). 3-OS CI matrix green; the 13 suite failures on Windows reproduce identically on unmodified main (pre-existing).

### Feat: the empty-state banner now knows all 14 runtimes and sells the trial instead of a second agent (#3973) (2026-07-23)
- **Why:** a machine running Claude Code, Cursor, or any other paid runtime with no data yet was told "No OpenClaw or NVIDIA NemoClaw detected. Install one to start seeing data." — telling a user who already has an agent to install a different one, at the exact moment they are most convertible. Live Clarity replays showed real users bouncing off this state.
- **What:** detect_agent_install() now reports every non-free runtime found on disk (via the existing _detect_runtimes_lite free-tier detector) with per-runtime entitlement (entitled_runtime, not grace-mode allows_runtime); when an uncovered runtime is present, the banner swaps to "Detected {runtimes} on this machine. ClawMetry Pro watches them in real time." with a Start-7-day-free-trial CTA (source=no-agent-banner, harness attributed) and fires paywall_view telemetry. Truly-empty machines keep the install CTAs. The announcement pill retires the desk device in favor of the Agent Builder cross-sell (build.clawmetry.com). 3 new i18n keys shipped across all 36 locales.
- **Verified:** 7 new tests in test_no_agent_detected_state.py pin the payload + banner/JS contracts; full banner/paywall/i18n selection shows zero regressions vs clean main (stash-compared); payload smoke-tested on a real machine listing detected runtimes with entitled=false; verify_i18n_coverage.py green.

### Fix: Windows hardening batch, the node stops breaking itself (#3915, #3916, #3918, #3878, #3856) (2026-07-22)
- **Why:** four separate Windows failure modes were found live on a real Windows 11 node in 48 hours: auto-update bricked the install (pip uninstalled the old version, then WinError 32 on the locked running clawmetry.exe left ZERO versions installed and every command dying with ModuleNotFoundError); `clawmetry uninstall` crashed mid-purge (the sync daemon was never stopped on Windows, its open sync.log cannot be deleted there) and left a zombie launcher plus a half-deleted config dir behind a false success message; the dashboard Logs tab crashed mid-SSE (bare "openclaw" argv cannot launch the npm .cmd wrapper, select() on a pipe is POSIX-only, `tail` does not exist) and then drowned in 429 retries; and the Agents tab told a user with a visibly running OpenClaw that there was "nothing to configure" while the daemon simply was not ingesting.
- **What:** the updater pre-renames the running exe before pip and rolls back to the previous version on a failed install, so a node can never be left with zero installs; uninstall stops every clawmetry process first (CIM enumeration, no new deps), warns instead of crashing on locked files, verifies the rmtree honestly, and hands the running launcher to a detached delete; all four streaming paths go through the new portable process_control.PipeLineReader or pure-Python file follows (no tail, no select-on-pipe, which()-resolved openclaw); the Agents tab empty state now says the truth and points to the action when runtimes are detected but the daemon is down; and the test suite's HOME sandboxing finally works on Windows (ntpath.expanduser conftest shim, 350 call sites in 246 files were silently un-sandboxed).
- **Verified:** every fix revert-proven red-then-green on the real Windows 11 machine that hit it; full CI matrix green per PR including windows-latest; the uninstall recovery sequence was field-tested manually on the affected node before being encoded; regression guards are auto-discovering (raw os.kill(pid,0) probes, select.select, tail subprocesses each fail CI if reintroduced).

### Fix: onboarding wizard renders styling in the classic Windows console instead of escape garbage (#3795) (2026-07-17)
- **Why:** `clawmetry onboard` in a cmd.exe conhost window printed literal ANSI garbage around every styled string. The wizards gate colors on `isatty()`, which is True in conhost, but conhost ships with Virtual Terminal processing OFF so escapes are not interpreted; Windows Terminal enables VT by default which is why it never showed there. Invisible before 0.12.557 because the closed-stdout bug swallowed all wizard output. Surfaced by the founder on a live cmd window minutes after 0.12.557 shipped.
- **What:** new `_ansi_ok()` helper enables VT via `SetConsoleMode` (no-op in Windows Terminal) and reports whether escapes render; the `onboard`/`account`/`connect` color gates use it with a plain-text fallback, and `main()` calls it early so the unconditional ANSI emitters (uninstall, account warnings) render correctly too. Same PR also ships the silent-CLI class guards in CI: output-asserting 3-OS CLI smoke (the old smoke steps were continue-on-error and could never fail), a lint banning stdout/stderr TextIOWrapper rebinds, and a breadcrumb log when the CLI devnull guard fires on a process that had a console.
- **Verified:** `ast.parse` clean; piped `onboard --local` emits zero ESC bytes (non-tty fallback intact); lint revert-proven (4 hits on the pre-#3791 dashboard.py, 0 on main); live conhost rendering to be confirmed on a real cmd window post-release.

### Fix: Windows CLI no longer swallows all output (`--help`, `onboard`, `connect` were silent) (#3791) (2026-07-17)
- **Why:** on Windows, every clawmetry CLI surface printed nothing and exited 0: `--help`, `--version`, the `onboard` wizard and the `connect` prompts all wrote to a dead stream. A first-run user saw a blank, apparently hung terminal, which reads as "the product is broken" in the first minute of a trial (surfaced live in an enterprise demo on 2026-07-17). Root cause: dashboard.py's duplicated force-UTF-8 header rebound sys.stdout to a second TextIOWrapper over the same underlying buffer; the orphaned first wrapper's GC finalizer closed that shared buffer, and the CLI's closed-handle guard (built for pythonw) then silently swapped in a devnull sink: exit 0, no output, no error, since the 2026-06-12 release (#3046).
- **What:** both blocks now call `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in place. reconfigure() is idempotent and cannot orphan a wrapper, so the duplicated header is harmless, and the emoji-on-cp1252 protection is preserved.
- **Verified:** on Windows 11 / Python 3.13: `--help` prints the full 69-line usage and exits 0 (was 0 bytes), `onboard --local` renders the whole wizard (was 0 bytes), `connect` shows its prompts (was 0 bytes), and stdout stays open after `import dashboard` plus gc.collect(). Regression guard `tests/test_stdout_survives_import.py` shipped in the same PR, revert-proven (both tests red on the un-fixed code, green with the fix), and runs in the 3-OS matrix so Windows CI now catches this class permanently.

### Fix: `connect --key … --start-sync-now` no longer demands a second OTP (#3777) (2026-07-17)
- **Why:** the connect command the cloud dashboard tells a freshly signed-in user to paste (`clawmetry connect --key cm_… --start-sync-now`) triggered ANOTHER email OTP, even though the key was just minted inside an OTP-verified web session. Onboarding asked the user to prove the same thing twice, and the gate hard-exits in non-interactive shells. Security-wise the client-side OTP never gated anything: the `cm_` key is a bearer credential the server accepts directly on `/auth` and ingest.
- **What:** passing `--start-sync-now` alongside `--key` now skips the ownership OTP and goes straight to connect + sync. A bare `--key` connect (key obtained from anywhere else) still verifies via OTP, and re-connecting with the already-saved key still skips as before. The flag's help text now says what it does instead of "no-op".
- **Verified:** 3 regression tests (skip with the flag, still-asks without it, saved-key reconnect skip); the skip test proven red on the un-fixed code.
- **Released:** 2026-07-17 [RELEASE] carrier, so the dashboard's paste-and-go connect command stops double-OTPing new signups immediately.

### Fix: uninstall removes every com.clawmetry.* launchd agent, not just sync (#3749) (2026-07-15)
- **Why:** `clawmetry uninstall` reported "fully uninstalled" while the dashboard kept serving on localhost:8900. It only unloaded `com.clawmetry.sync.plist`; the dashboard agent (`KeepAlive=true`) and the `com.clawmetry.sandbox.*` agents stayed registered, so launchd kept the server alive off the deleted `~/.clawmetry` venv (open file handles survive the rmtree) and respawned it on every login, with the orphaned sandbox agents crash-looping at exit 78. Reproduced live on a user machine on 2026-07-15.
- **What:** uninstall now globs every `~/Library/LaunchAgents/com.clawmetry.*.plist`, boots each out (`launchctl bootout`, falling back to `unload` on older macOS) and deletes it BEFORE removing any files, so KeepAlive can never resurrect the server; Linux gets the same broadening across `clawmetry*.service` user units. A new `_kill_dashboard_processes()` sweeps up hand-started dashboards, skipping the uninstall process itself and its parent, and never matching the ClawMetry.app desktop bundle.
- **Verified:** 3 regression tests (all-plists removal + unrelated plists untouched, `unload` fallback when `bootout` is unavailable, self-PID skip) green on py3.9; full CI matrix green on #3749; the leftover-agent state was reproduced and cleaned on the affected machine.

### Fix: auto-update restarts both the dashboard and the daemon onto the new wheel (#3634) (2026-07-10)
- **Why:** the live hands-off verification showed the daemon self-updating cleanly while the local dashboard kept serving the previous build from memory; the unattended path only ever restarted the sync daemon.
- **What:** the shared restart helper is now role-aware: it restarts the other long-running service first (launchctl on macOS, systemctl --user on Linux, best-effort) and itself last, so both processes come back on the freshly installed wheel.
- **Verified:** source-level guard red on the un-fixed code; auto-update suite 26/26. This release is also the first full minutes-fresh cycle on the new updater (the 0.12.552 daemon should install it within about 3 minutes of publish).


### Fix: auto-update retries a just-published release in about 2 minutes (#3630) (2026-07-10)
- **Why:** the live verification of the fast update loop caught its own first bug: PyPI's JSON API advertises a release 1 to 3 minutes before pip's index can serve it, and that "no matching distribution" failure was treated as a broken wheel, sitting out the full 30-minute backoff for a 2-minute propagation lag. At 20+ releases a day that race is routine.
- **What:** distribution-not-found failures now retry within `CLAWMETRY_AUTOUPDATE_PROPAGATION_RETRY_SECS` (default 120); every other install failure keeps the long broken-target backoff. Backoff bookkeeping moved to explicit per-target deadlines. Also updates the plan-sync log line that still promised a "48h stability window".
- **Verified:** new guard red on the un-fixed code; auto-update suite 30/30.


### Feature: updater posture on the status API (#3627) (2026-07-10)
- **Why:** with the fleet now tracking releases within minutes, "is this node actually on the fast update loop?" must be answerable from the API, not by reading env vars and logs on the box.
- **What:** `/api/update-check/status` gains an `updater` block: role, effective check interval, age gate, and kill-switch state.
- **Verified:** endpoint test (suite 11/11); this release doubles as the live hands-off verification of the fast auto-update loop.


### Feature: auto-update now keeps every install on the latest release within minutes (#3624) (2026-07-10)
- **Why:** ClawMetry ships 20+ releases a day, and a user found their node promising to self-update "within about two days". Worse, the checker was started without the daemon role, so the default-on auto-update policy never acted on free or local-only installs at all; only trial and paid nodes (whose plan sync explicitly wrote the flag) ever self-updated.
- **What:** the sync daemon now starts the update checker with the daemon role (the root-cause fix), polls PyPI every 60 seconds (`CLAWMETRY_UPDATE_CHECK_SECS`, clamped 30s to 1 day), and installs the absolute latest release by default (`CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS` now defaults to 0; set it to restore a stability window). Unsupervised daemons (containers, kubectl-exec wrappers, manual runs) re-exec their own process after installing instead of running the old wheel in memory until someone restarts them; Windows keeps the defer-to-next-start behavior and `CLAWMETRY_AUTOUPDATE_EXEC_RESTART=0` disables the re-exec. Failed installs back off 30 minutes so the fast loop never hammers pip on a broken target. The bad-wheel safety net is the existing boot rollback guard, plus the `CLAWMETRY_AUTO_UPDATE=0` kill switch.
- **Verified:** 28 tests green including 10 new guards (cadence, worker loop per-tick behavior, dashboard cadence preserved, age-gate default, sync.py role wiring, re-exec gating), revert-proven 8/10 red on the un-fixed code.


### Feature: date-time range filter on the Brain Activity stream (#3610) (2026-07-10)
- **Why:** the Activity stream only ever showed the newest events, so the most common incident question, "what happened at 3AM last night?", was unanswerable. A time window turns the Brain tab into an investigation tool.
- **What:** `/api/brain-history` accepts `since`/`until` (ISO-8601 or epoch; aliases `start`/`end`; bad values degrade to no bound, reversed bounds swap) served from the indexed DuckDB `ts` column, with the window echoed back and the response cache keyed per range. The Brain tab gains a range bar (Live, 1h, 6h, 24h, Custom from/to) with a Viewing-history banner, a HISTORY pill, and a density chart that re-anchors its buckets to the selected window. History mode freezes the live machinery (SSE, reconnects, poll fallbacks) so the frozen view can never be clobbered by incoming events. For hosted dashboards, the daemon's brain relay now honors window args (it used to discard them and answer with the newest-50), returning a windowed, brain-shaped, E2E-encrypted blob; the paired cloud change gives window requests their own relay cache key and decrypts client-side.
- **Verified:** real-data end-to-end on a live node (two historical windows, every returned event strictly in-window), browser walkthrough of preset, custom and back-to-live with a clean console, 11 backend tests plus 15 JS unit checks all proven red on the un-fixed code.

### Feature: Pi and Deep Agents runtimes, taking ClawMetry to 14 observed runtimes (#3597) (2026-07-09)
- **Why:** Pi (pi.dev, the Earendil coding agent, 68k+ GitHub stars) and Deep Agents (LangChain's deepagents) are fast-growing agent runtimes users run alongside the existing 12; both persist rich local session data ClawMetry can observe read-only.
- **What:** registry entries (paid tier), session-id prefixes `pi-` / `deepagents-` wired through the daemon, per-runtime scoping and no-leak filters, runtime switcher labels, capability-derived tabs (sessions, events, cost), logo sprite symbols, and docs. The adapters ship in clawmetry-pro 0.4.0: Pi parses the versioned JSONL session tree (v1 linear and v3 tree, stored per-turn cost, reasoning and 1h-cache token fields); Deep Agents reads LangGraph SqliteSaver checkpoint databases, decoding both the checkpoint channel_values layout (library usage) and the writes-table layout (the dcode CLI, which never folds messages into checkpoints).
- **Verified:** adapter unit suites 36/36 and 39/39 against REAL captured stores from live spike turns (exact token, stored-cost, and model assertions); live conformance matrix green 14/14 including real installed-runtime turns for both new runtimes; picoclaw/pi prefix no-collision regression test.

### Fix: Approvals protection rules now actually block risky commands on OpenClaw (#3589) (2026-07-08)
- **Why:** the protection-rule toggles were inert on OpenClaw agents. ClawMetry's own approval watcher is reactive (it matches a tool_call only after the transcript records it, by which point the command already ran), and OpenClaw did not emit a matchable tool_call on that path. Proven live: an agent told to `rm -rf` a sentinel dir deleted it with no approval.
- **What:** the daemon (already fetching cloud policies every 2s, running inside the OpenClaw box) now drives OpenClaw's OWN pre-execution gate. When an enabled require_approval policy covering exec is active it runs `openclaw exec-policy preset cautious` (security=allowlist, ask=on-miss, askFallback=deny) so a non-allowlisted exec pauses before running and is denied if unanswered; when none are, it restores `yolo`, but only if it was the one that set cautious (never clobbers a hand-set posture). Idempotent, guarded (no-op off an OpenClaw host), best-effort.
- **Verified:** live controlled A/B on a hosted node — the same `rm -rf` that deleted a sentinel dir under yolo was prevented under cautious (dir survived). Unit tests 8/8.

### Fix: full chat replies in the Brain / cloud Activity feed (#3586) (2026-07-08)
- **Why:** the v3 row stores the same reply text up to three times and the synthesized message block added a fourth; that quadrupling blew the 1500-byte per-event ceiling, so the tighten loop squeezed every string to 150 chars and the cloud feed showed a stub of each reply while the OpenClaw dashboard showed the full message.
- **What:** blob events for v3 chat rows are now lean (duplicates dropped; the blob's only readers use `message.content`), chat text gets a 1200-char per-string cap (default stays 600 elsewhere), and the over-ceiling tighten ladder gains gentle rungs (1000, 700) so a borderline event loses a sentence, not two-thirds of the message. The hard 1500-byte event ceiling is unchanged, so the desk-device buffer math is untouched. Pairs with clawmetry-cloud's click-to-expand, which fetches the untruncated transcript on demand through the heartbeat relay.
- **Verified:** regression test with a realistic ~900-char reply proven red on the un-fixed code and green with the fix; neighboring brain suites show identical results with and without.

### Fix: OpenClaw v3 conversations now show up in the Brain / cloud Activity feed (#3581) (2026-07-07)
- **Why:** a node holding a real OpenClaw v3 conversation showed "No brain activity events found" on the cloud Activity tab even with the full conversation in DuckDB. The daemon's v3 parser stores conversations as `prompt.submitted{finalPromptText}` / `model.completed{completionText, assistantTexts, toolMetas}`, but the brain pipeline never learned that shape: `_brain_row_renderable` only knew `content`/`text`/`tool_calls` (every assistant reply dropped), `prompt.submitted` sat on the blanket skip list (the user side silenced), and the pushed blob carried no `message` block for the cloud renderer. A pure-chat v3 session contributed zero brain events. NemoClaw runs the OpenClaw adapter, so it was equally dark.
- **What:** new `_v3_chat_message()` projects the daemon's own v3 keys onto the canonical `{role, content[]}` shape; renderable accepts v3 chat rows (textless plumbing still skipped); `_rows_to_brain_events` synthesizes `{type:'message', message:{...}}` that the existing cloud `transformEvents` and device `brain_event_to_row` already render. No cloud or firmware change needed.
- **Verified:** regression fixtures copied from a live node's DuckDB rows; `tests/test_brain_v3_chat_events.py` proven red on the un-fixed code (4 failures) and green with the fix (6/6).

### Fix: denying an approval now actually stops Claude Code and friends, and late-picked-up sessions can no longer slip past your rules (2026-07-03)
- **Pressing Deny on an approval did not stop agents running under Claude Code, Codex, Goose, opencode or Aider (#3498).** The deny path only knew how to stop OpenClaw sessions through the gateway, which has never heard of family-runtime sessions, so the denied agent kept running (caught live: a deny sent from the phone logged killed=False while the Claude Code canary carried on). Denying now uses the same guarded process stop the Stop button uses: it finds the agent's own process, double-checks the process id still belongs to it, and shuts down its whole process tree. OpenClaw keeps its existing gateway path, and the log says which mechanism fired. If neither mechanism can reach the session, the honest killed=False warning remains.
- **A session that ClawMetry picked up late could act without ever being checked against your approval rules (#3498).** The watcher tracked its place by the events' own timestamps; when a brand-new project directory was ingested minutes after its events happened (seen live), newer events had already moved that marker past them, so those tool calls were never evaluated. The watcher now tracks when events actually land in the local store, so a late-arriving session is checked the moment it appears. Nothing double-fires: a persisted seen list keeps every event exactly-once, including across daemon restarts, and the extra bookkeeping is indexed and bounded so the daemon stays light.
- **Verified:** revert-proof regression tests for both bugs (11 red on the old code, 64 green after across the approvals and process-control suites), plus a full-chain rehearsal where a late-ingested Claude Code tool call was denied and the process kill path fired with killed=True.

### Fix: pause and kill now work for Claude Code on a Mac set to a non-English language (2026-07-03)
- **On a Mac without psutil whose system language is not English, pressing Pause, Kill or Resume on a Claude Code session could still do nothing (#3497).** Before signaling a process, ClawMetry double-checks that the process id still belongs to your agent by comparing start times. Reading the live start time uses the system `ps` tool, which prints month and day names in the system language (for example "Do 2. Jul" on a German Mac). The safety check only understands English names, so it could never confirm the process and safely refused every request. ClawMetry now asks `ps` for plain English output regardless of the system language, so the check works everywhere. The safety intent is unchanged: output that genuinely cannot be understood still refuses.
- **Verified:** three new regression tests, proven red on the unfixed code and green after the fix, including one that simulates a German-language Mac and asserts the guard verifies, and one that asserts unparseable output still refuses.

### Fix: per-runtime cost is accurate again (family spend was booked as OpenClaw) (2026-07-02)
- **The Cost tab could show OpenClaw carrying the whole machine's spend while Claude Code showed today's cost but $0 for the week and month (#3490).** One event mapper stamped every transcript event as OpenClaw, so the daily cost rollup booked all family-runtime spend (Claude Code, Codex, and friends) under OpenClaw. On a real node, OpenClaw showed $2,005 for the month when its true total was $4.37.
- Events are now attributed by their session's runtime (the same rule every other view uses), and on update the store rebuilds its cost history once so past spend moves to the right runtime automatically - no reinstall, nothing to run. Verified on a live node: after the rebuild, OpenClaw and Qwen Code match their roster lifetimes exactly, and Claude Code's week and month are consistent with its today.

### Fix: the Agents roster no longer looks like it changes on every runtime switch (2026-07-02)
- **Switching the runtime dropdown made the Agents tab appear to show different data each time (#3482).** The roster is one node-wide list, and the selected runtime's row is deliberately kept visible instead of folding under "Show N inactive". But the promoted row landed in an arbitrary position and nothing said why an idle runtime suddenly appeared, so the list read as random. Now the selected runtime is always the first row, and a small "selected" tag (with a plain-words tooltip) marks a row that is only visible because it is selected. The numbers were always identical across selections; this makes the behavior visible and predictable.

### Fix: pause, kill and resume now actually work for Claude Code on a Mac in any timezone (2026-07-02)
- **On a Mac without psutil, pressing Pause, Kill or Resume on a Claude Code session from the web dashboard, the desk device, or the mobile apps did nothing unless the machine happened to be set to UTC (#3477).** Before signaling a process, ClawMetry double-checks that the process id still belongs to your agent, so it can never kill a stranger's process that reused the id. That safety check compared the recorded start time, which Claude Code writes as a UTC timestamp string, against the live start time the system reports in your local timezone. In any timezone other than UTC the two strings never matched, so the safety check refused every request and the buttons silently did nothing. Found and verified live during mobile app end-to-end testing. The check now understands both renderings of the same instant (and prefers Claude Code's unambiguous numeric start time when available), so the controls work in every timezone. The safety intent is unchanged: a start time that cannot be parsed, or a genuinely different process, still refuses.
- **Pause no longer freezes a parent program that shares a process group with the agent.** Pausing an agent used to stop every process in the agent's process groups, which could include the very tool that asked for the pause (seen live in the same end-to-end test). Pause and Resume now only signal whole groups that belong exclusively to the agent's own process tree; in shared groups only the agent's processes are signaled, so the agent still freezes and bystanders never do.
- **Verified:** five new regression tests, proven red on the unfixed code and green after the fix, including one that reproduces the exact UTC-versus-local mismatch under a Europe/Berlin timezone and one where an orchestrator sharing the group survives its own pause call while the agent stops.

### Session deep-dive: Trace, Turn timing and Compare live with the session now (2026-07-02)
- **The three session-scoped expert views moved out of the sidebar and into the session itself (#3473).** Tracing, Turn timing and Compare sessions only make sense for a specific session, so they no longer take up global navigation space. Open any conversation and use the new "Deep dive" row to jump straight into that session's trace, its per-turn timing, or a side-by-side comparison, with the session already selected. Old bookmarks and links to those pages keep working. The Developer section now holds just the fleet-wide tools: Flow, Models, LLM Context, Agent Graph, Tools, Context usage, Runtime extras, and Ask.
- **Verified:** live browser walk against real data (all three deep-dives open with the session preselected, no list bleeding under the detail) plus seven new guards in tests/test_session_deep_dive.py.

### Fix: the Agent Graph tab loads instead of sitting on "Loading..." (2026-07-02)
- **Clicking Agent Graph showed "Loading..." forever, locally and on the hosted dashboard (#3462).** The tab's loader was wired into a leftover, never-rendered copy of the page markup, so it simply never ran. It is now wired into the live page: the graph draws when there is span data, an honest "no data in this window" note shows when there is none, and the hosted dashboard now explains that the agent graph is built from your local data store rather than showing a misleading empty state. A new class-level guard fails CI if any tab's loader is ever wired only into the dead markup again.

### A simpler sidebar: seven plain items, expert views one click away (2026-07-02)
- **The dashboard sidebar is now beginner-first (#3458).** A first-time user used to face about 27 navigation entries, many named in insider vocabulary, with an 11-item expert group expanded by default. The sidebar now shows seven plain-words items: Home (the landing screen finally has its own name), Agents, Activity (was Brain), Cost, Conversations (was Session replay), Approvals, and Alerts. Every deep-dive view lives in a collapsed "Developer" section: Flow, Models, LLM Context, Tracing, Agent Graph, Turn timing, Tools, Context usage, Runtime extras, Compare sessions, and Ask (was Dives). Schedules (was Crons) and Memory moved under Advanced.
- **Nothing was removed and nothing breaks.** Every screen keeps its internal id, so bookmarks, deep links, and per-runtime tab visibility work unchanged. Opening a link to a Developer view automatically reveals the section so you can see where you are. If you had the expert group open before, it stays open for you.
- **Verified:** live browser walk on a fresh profile (seven items, section toggle, tab switching, deep-link reveal, Advanced click-through) plus eight new structural guards in tests/test_beginner_nav_phase_a.py.

### Fix: the Cost tab no longer hangs on "Loading..." (2026-07-02)
- **Every card on the Cost tab (Top Sessions by Cost, Cost By Plugin/Skill, Trace Clusters, Activity Heatmap, Cost Comparison) could sit on "Loading..." forever (#3453).** When a node did not yet have enough history, the usage API returned an empty trend object, and the trend renderer tried to read a property off it and threw. Because that renderer runs early while the Cost tab is loading, the error stopped every card after it from drawing. The trend card now handles an empty trend cleanly, and the Cost tab is hardened so a single card can never block the rest of the page. Verified live: all cards render again.

### Fix: the sync daemon now starts and is detected correctly on a root server or VPS (2026-07-01)
- **On a server you run as root (a VPS reached over SSH), the background sync daemon could fail to start and `clawmetry status` would always say "Daemon: Not running" (#3423).** Root usually has no per-user service session, so the old startup silently did nothing and status only knew how to look for a per-user service. ClawMetry now installs a proper system service for root (which starts and survives reboots), falls back to a plain background process if needed, and detects the daemon by looking for the actual running process. `clawmetry status` also shows the installed ClawMetry version now, so it is obvious at a glance whether a machine is up to date.

### Fix: paid runtimes now sync as soon as you upgrade to Trial or Pro (2026-06-30)
- **After upgrading from Free to a Trial or Pro plan, paid runtimes like Claude Code could keep showing "NOT syncing" and `clawmetry status` could still say "FREE plan" (#3414).** The plan a node knows about was only refreshed by the background daemon on a heartbeat, so if the daemon was down or had not checked in since you upgraded, the local copy stayed stale. Now `clawmetry status` reads your live plan from your account and updates the local copy on the spot, and the daemon re-checks your plan on every heartbeat, so paid runtimes start syncing right after you upgrade, with no restart needed.

### Change: `clawmetry onboard` always shows the run options now (2026-06-30)
- **Re-running the setup wizard always shows the Local / Cloud / License key options, even if you are already connected (#3410).** It used to say "Already connected" and skip the menu, so you could not re-run it to switch how ClawMetry runs. Now you can switch any time. If you are already connected and just press Enter, it keeps your current setup and changes nothing, so re-running is always safe.

### Fix: Google and GitHub sign-in now works on a remote or headless server (2026-06-30)
- **`clawmetry connect` with Google or GitHub used to hang on a machine with no local browser, like a VPS you reach over SSH (#3407).** The old flow waited for the browser to redirect back to the machine running the CLI, which never happens when the browser is on your laptop and the CLI is on a remote box. ClawMetry now detects a headless or remote box and switches to a paste-code sign-in (the same style as the Claude Code CLI): it prints a sign-in link, you open it on any device, and after you approve it shows a short one-time code that you paste back into the terminal. Desktop sign-in is unchanged, and email one-time codes still work as before. Force the paste flow anywhere with `CLAWMETRY_NO_BROWSER=1`.

### Fix: the Brain feed no longer shows the same message two or three times (2026-06-29)
- **One assistant turn was rendering as duplicate rows in the Brain "Live event stream" (#3383).** A single OpenClaw turn lands as an `assistant` row plus one or two `model.completed` siblings a second or two apart (one a zero-token `delivery-mirror` echo), all carrying the same text. Because their timestamps and ids differ, the existing exact-match dedupe missed them, so the same paragraph appeared two or three times in the feed. The Brain feed now collapses these siblings to the single richest row per session and message (within a short time window), so each turn shows once. A genuine repeat of the same text in a later turn, a different session, and short repeated phrases are all left untouched. Verified on live data: a paragraph that showed three times now shows once, with 14 duplicate rows removed from a 110-event feed.

### Enable Cloud Sync: one-click GitHub/Google sign-up, and it actually turns sync on (2026-06-29)
- **The "Enable Cloud Sync" dashboard modal now offers one-click GitHub and Google sign-up (#3375).** It was email-only before, even though the cloud already supports GitHub and Google login. The new buttons run the same secure loopback flow as `clawmetry connect`: your browser signs in on the cloud, and the freshly minted key comes back to the dashboard over `127.0.0.1` only (it never travels the network in the clear). The dashboard then registers this machine, generates your end-to-end encryption key, and starts the sync daemon, so a single click both creates the account and connects the node. Email sign-up still works as before.
- **Connecting to cloud now clears the local-only marker, so sync truly starts (#3380).** A local-only install writes `~/.clawmetry/nocloud`, which keeps the daemon from sending anything to the cloud. Until now, clicking "Enable Cloud Sync" (or running `clawmetry connect`) wrote your account token but left that marker in place, so the daemon kept running local-only and your machine never appeared in the cloud dashboard (it showed zero nodes despite a healthy daemon). An explicit opt-in to cloud now removes the marker and restarts the daemon so it picks up the change immediately. Passive updates still never re-enable cloud on their own, and an explicit `CLAWMETRY_NO_CLOUD=1` is still honored.
- **Verified:** new guards in `tests/test_cloud_cta_oauth.py` cover the OAuth start/status routes, the full connect (config written), the marker being cleared on connect, and `enable_cloud()` idempotency. Confirmed live on a real node: removing the marker and reconnecting flipped the daemon to encrypted cloud push and the machine appeared in the fleet.

### Fix: local-only installs no longer flood themselves with cloud errors (and Brain shows your agent again) (2026-06-25)
- **A local-only install kept logging "node appears offline in cloud" every few seconds and the Brain feed filled with our own errors instead of your agent (#3317).** In local-only mode there is no cloud to reach, but the daemon was still trying to send a heartbeat on every cycle, failing, and recording a critical error each time. Those errors piled into the local activity store and pushed your real agent events out of the Brain feed. Local-only mode is now silent (no heartbeat, no errors), and the Brain feed filters out ClawMetry's own background diagnostics so your agent's actual activity always shows.

### Entitlement path helpers: affordable_tiers and tier_locks_path (2026-06-23)
- **Two new helpers in `clawmetry.entitlements` close the gaps in tier-navigation queries (#3280, #3284).** `affordable_tiers(features=None, runtimes=None, channels=None, retention_days=None, nodes=None)` returns the ordered list of purchasable tiers that satisfy all supplied requirements, so a paywall prompt can surface the cheapest qualifying option rather than defaulting to the highest tier. `tier_locks_path(from_tier, to_tier)` is the marginal-loss mirror of `tier_unlocks_path`: it returns per-rung what a user would lose at each step of a downgrade, with chained `next_tier` semantics, completing the four-member `_path` family (`tier_path`, `capacity_diff_path`, `tier_unlocks_path`, `tier_locks_path`).
- **Why:** the paywall prompt had no single call to find the cheapest tier meeting a set of requirements, and there was no query to enumerate what is lost at each step of a downgrade path (needed for churn-prevention flows and downgrade-confirmation modals). Both helpers live purely in the library layer so feature code and cloud flows can call them without re-implementing the tier walk.
- **Verified:** 1044 tests pass. `GET /api/entitlement/affordable-tiers` and `GET /api/entitlement/tier-locks-path` are wired in `routes/entitlement.py`.

### Fix: local-only installs now ingest your agents (and Brain shows your full history) (2026-06-23)
- **A local-only install (the new [1] Local only path) crash-looped the sync daemon, so nothing was ingested (#3285).** The local-only setup wrote a config with no API key, but the daemon's startup read that key directly and crashed on every boot before it could read your agent sessions. The daemon now starts cleanly with or without an account, and existing broken local-only installs self-heal on this update (no reinstall needed). Local-only mode never sends anything to the cloud regardless.
- **The Brain tab now shows ALL of your local history, with no 24-hour limit and no upgrade prompt (#3286).** On your own machine your agent history is yours, so the local dashboard no longer caps the Brain view to the last 24 hours. ClawMetry's own background diagnostics are also hidden from the Brain feed now, so a busy or restarting daemon can't bury your agent's actual activity.

### Install: the installer now asks before creating a cloud account (2026-06-23)
- **`curl -fsSL https://clawmetry.com/install.sh | bash` no longer creates a cloud account by default (#3281).** The setup wizard used to default a no-account answer (and a headless install with no terminal) straight into creating a cloud account, so some people ended up with an account they never asked for. It now presents a clear choice: **[1] Local only** (free, no account, nothing leaves your machine, the default), **[2] Cloud** (free trial dashboard you can open anywhere), or **[3] License key** (activate Self-Hosted Pro for all 12 runtimes, offline). A non-interactive install defaults to local and never creates an account. You can script it with `--local` / `--cloud` or `CLAWMETRY_LOCAL_ONLY=1`. Local-only writes the `~/.clawmetry/nocloud` marker so updates can't silently re-enable cloud sync; the local dashboard at http://localhost:8900 works exactly as before.

### Security: stronger protection for custom encryption passphrases (2026-06-14)
- **A typed custom secret is now run through a strong, salted key derivation (#3127).** Previously a custom passphrase was stored as-is and turned into the encryption key with a single, unsalted hash, so a weak passphrase could be brute-forced offline and the same passphrase produced the same key for everyone. ClawMetry now derives the key with scrypt and a random salt at setup and stores only the derived key (you back it up and paste it as before, via `clawmetry status --show-key`); the passphrase itself is never saved. Existing installs are unaffected and keep decrypting their data. If you auto-generate your key (the default), nothing changes.

### Privacy: machine details are now end-to-end encrypted (2026-06-14)
- **Your machine's details no longer leave your machine in cleartext (#3124).** The security-posture scan and the machine fingerprint (OS, CPU architecture, core count, RAM, and local network IP addresses) used to ride the plaintext heartbeat, where the cloud stored them unencrypted. They now travel inside the end-to-end-encrypted system snapshot (the `machineInfo` and `securityPosture` slices) and are decrypted only in your browser; the cloud keeps an opaque blob it cannot read. The Machine, Network, and Security views render this client-side from the decrypted snapshot. The plaintext heartbeat keeps only routing fields. (Re-applies the security-posture move that a stale-rebase merge had silently reverted, with a guard test. Paired cloud change stops persisting the data and purged existing rows.)

### Release: publish the per-session loops[] snapshot slice to PyPI (2026-06-13)
- Ships the daemon `loops[]` slice (each entry carries the canonical session_id for an active loop or stuck incident) so the cloud Command River can bind the red whirlpool and the Kill/Pause alarm to the exact looping agent. Carries the feature merged in #3100.

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

### Privacy: security posture is now end-to-end encrypted (2026-06-10)
- **Your machine's security scan no longer leaves your machine in cleartext (#2979).** ClawMetry runs a local security-posture scan (a score plus a list of checks) and used to attach it to the plaintext heartbeat, where the cloud stored it unencrypted. It now travels inside the end-to-end-encrypted system snapshot and is decrypted only in your browser; the cloud stores an opaque blob it cannot read. The Security tab renders it client-side from the decrypted snapshot. (Paired cloud change stops persisting it and purged existing rows.)

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
