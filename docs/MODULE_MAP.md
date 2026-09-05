# ClawMetry module map

> GENERATED FILE, do not edit by hand. Regenerate with
> `python3 scripts/gen_module_map.py` (CI fails on drift via
> `tests/test_module_map_drift.py`).

226 modules, 81 Flask blueprints. `CLAUDE.md` carries a short curated table of the ones you reach for most often; this is the whole list.

Size bands are deliberately coarse so this file does not churn on every PR: **small** is under 200 lines, **medium** under 1k, **large** under 5k, **huge** is 5k and up.

The **Serves** column is the URL space a module owns, collapsed to two path segments. A blank one means the module registers no routes of its own (it is a library, or its rules are built dynamically).

## Top level

The Flask app itself plus the optional SQLite time-series companion.

| Module | Size | Purpose |
|---|---|---|
| `dashboard.py` | huge | ClawMetry - See your agent think 🦞 |
| `history.py` | medium | ClawMetry History - Time-series data collection and storage. |

## HTTP routes (`routes/`)

One module per feature, each owning one or more Flask blueprints. New endpoints go here, never in `dashboard.py`.

| Module | Size | Blueprints | Serves | Purpose |
|---|---|---|---|---|
| `routes/_dedupe.py` | small |  |  | sibling-dedupe helper for v3 event sums (issue #1451). |
| `routes/advisor.py` | medium | `bp_advisor` | `/api/advisor` | ClawMetry Advisor: natural-language Q&A over your agent. |
| `routes/agents.py` | medium | `bp_agents` | `/api/agents` | Multi-agent adapter endpoints. |
| `routes/alerts.py` | large | `bp_alerts`, `bp_budget` | `/api/_harness`, `/api/agents`, `/api/alert-channels`, `/api/alerts`, `/api/budget`, `/api/emergency-stop` | Budget + Alerts endpoints. |
| `routes/approval_routing.py` | small | `bp_approval_routing` | `/a`, `/a/decide`, `/api/approvals` | OSS stub after the impl moved to clawmetry-pro. |
| `routes/assets.py` | small | `bp_assets` | `/api/assets` | OSS asset registry API. |
| `routes/attention.py` | medium | `bp_attention` | `/api/attention`, `/api/hooks` | "which of my agents needs me right now". |
| `routes/audit.py` | small | `bp_audit` | `/api/audit-log` | Enterprise audit-log query endpoint. |
| `routes/autonomy.py` | medium | `bp_autonomy` | `/api/autonomy` | Autonomy Score endpoint. |
| `routes/bench.py` | medium | `bp_bench` | `/api/bench` | Harness Engineering tab endpoints (Blueprint: Harness Benchmarks & |
| `routes/bootstrap.py` | small | `bp_bootstrap` | `/api/bootstrap` | "First Contact" bootstrap artifact endpoints. |
| `routes/brain.py` | large | `bp_brain` | `/api/brain`, `/api/brain-history`, `/api/brain-stream`, `/api/llm-call-timeline` | Brain event feed endpoints. |
| `routes/channels.py` | large | `bp_channels` | `/api/channel`, `/api/channel-delivery-health`, `/api/channels` | Per-channel adapter endpoints. |
| `routes/cohort.py` | medium | `bp_cohort` | `/api/cohort-compare`, `/api/sessions` | Cohort compare and similar runs (WO-60; requirement "Cohort compare and |
| `routes/compliance.py` | small | `bp_compliance` | `/api/compliance` | OSS stub after the impl lives in clawmetry-pro. |
| `routes/components.py` | large | `bp_components` | `/api/component` | Per-panel component detail endpoints. |
| `routes/context_economics.py` | small | `bp_context_economics` | `/api/context-coverage`, `/api/context-economics` | context-window economics (PRD P1-2). |
| `routes/crons.py` | large | `bp_crons` | `/api/agent-intentions`, `/api/cron`, `/api/cron-health`, `/api/cron-run-log`, `/api/crons` | Cron CRUD + health + run-log endpoints. |
| `routes/delegated.py` | small | `bp_delegated` | `/api/cursor`, `/api/delegated-usage` | Connect a Cursor account from the dashboard, and read delegated usage. |
| `routes/device.py` | medium | `bp_device` | `/api/device`, `/device-preview` | Device snapshot — a compact, screen-sized JSON for hardware companions. |
| `routes/dives.py` | medium | `bp_dives` | `/api/dives` | ClawMetry Dives: NL-to-SQL-to-chart over the local DuckDB store. |
| `routes/entitlement.py` | huge | `bp_entitlement` | `/api/entitlement`, `/api/features`, `/api/license`, `/api/paywall`, `/api/runtimes`, `/api/tiers` | ``bp_entitlement``. |
| `routes/evals.py` | medium | `bp_evals` | `/api/evals`, `/api/evaluators` | Eval (LLM-as-judge) endpoints. |
| `routes/extensions.py` | small | `bp_extensions` | `/api/extensions` | diagnostic introspection for the entry-point plugin loader. |
| `routes/fleet_history.py` | medium | `bp_fleet` | `/api/nodes`, `/fleet` | Multi-node fleet endpoints. |
| `routes/govern.py` | small | `bp_govern` | `/api/govern` | agent identity: a principal you can attach things to. |
| `routes/guard.py` | medium | `bp_guard` | `/api/guard` | Guard — live session control and enforcement policies. |
| `routes/harness.py` | small | `bp_harness` | `/api/harness` | ``bp_harness`` — the per-harness custom-tab API. |
| `routes/health.py` | large | `bp_health` | `/api/_internal`, `/api/agent-presence`, `/api/authority-violations`, `/api/backups`, `/api/config-diagnostics`, `/api/diagnostics`, `/api/doctor-findings`, `/api/gateway-health`, `/api/handler-latency`, `/api/health`, `/api/health-stream`, `/api/heartbeat-ping`, `/api/heartbeat-status`, `/api/heatmap`, `/api/loop-detection`, `/api/loop-signals`, `/api/mcp-stats`, `/api/rate-limits`, `/api/reliability`, `/api/sandbox-status`, `/api/security-threats`, `/api/service-status`, `/api/system-health`, `/api/version-health`, `/healthz` | Health / reliability / diagnostics / rate-limits endpoints. |
| `routes/heartbeat.py` | medium | `bp_heartbeat` | `/api/heartbeat`, `/api/heartbeat-loops` | Heartbeat liveness panel API endpoint (#686). |
| `routes/hitl.py` | medium | `bp_hitl` | `/api/hitl` | Human-in-the-loop (HITL) pause API. |
| `routes/hooks.py` | large | `bp_hooks` | `/api/hooks`, `/api/lifecycle`, `/api/sessions` | local receiver for runtime pre-tool hooks. |
| `routes/infra.py` | large | `bp_config`, `bp_logs`, `bp_memory`, `bp_security` | `/api/automation-analysis`, `/api/context-anatomy`, `/api/cost-optimization`, `/api/cost-optimizer`, `/api/file`, `/api/flow`, `/api/flow-events`, `/api/llmfit`, `/api/logs`, `/api/logs-stream`, `/api/memory`, `/api/memory-access`, `/api/memory-analytics`, `/api/memory-files`, `/api/memory-rag`, `/api/numbat`, `/api/security` | Infrastructure / security / config / logs endpoints. |
| `routes/insights.py` | medium | `bp_insights` | `/api/insights`, `/insights` | Weekly Insights Digest endpoints. |
| `routes/inventory.py` | medium | `bp_inventory` | `/api/inventory` | Agent Inventory tab API. |
| `routes/local_query.py` | large | `bp_local_query` | `/__local_query__`, `/api/local` | coherent local query API over the DuckDB store. |
| `routes/meta.py` | large | `bp_auth`, `bp_cloud_relay`, `bp_gateway`, `bp_otel`, `bp_otlp_traces`, `bp_version`, `bp_version_impact` | `/.well-known/security.txt`, `/api/anon-auth-fail-ping`, `/api/auth`, `/api/cloud`, `/api/export`, `/api/gw`, `/api/install-age`, `/api/otel`, `/api/otel-status`, `/api/update`, `/api/version`, `/api/version-impact`, `/auth`, `/v1/logs`, `/v1/metrics`, `/v1/traces` | Auth / gateway / OTLP / version / version-impact. |
| `routes/nemoclaw.py` | small | `bp_nemoclaw` | `/api/nemoclaw` | OSS stub after the impl moved to clawmetry-pro. |
| `routes/onboarding.py` | medium | `bp_onboarding` | `/api/account`, `/api/onboarding` | the first-run onboarding gate state machine. |
| `routes/org_analytics.py` | small | `bp_org_analytics` | `/api/org-analytics` | OSS stub after the impl lives in clawmetry-pro. |
| `routes/otel_export.py` | medium | `bp_otel_export` | `/api/otel` | Pro+ OTel/OTLP export. |
| `routes/overview.py` | large | `bp_overview` | `/api/activity-heatmap`, `/api/channels`, `/api/cloud-cta`, `/api/cloud-proxy`, `/api/device`, `/api/health-timeline`, `/api/overview`, `/api/prompt-errors`, `/api/sync`, `/api/timeline` | Main-dashboard endpoints. |
| `routes/plugins.py` | medium | `bp_plugins` | `/api/plugins` | Plugin registry: unified view of installed plugins (#692). |
| `routes/policy.py` | medium | `bp_policy` | `/api/approvals`, `/api/approvals-audit`, `/api/policy`, `/api/tool-policy` | tool-policy + sandbox + exec-approval audit (PRD P1-1). |
| `routes/quality.py` | medium | `bp_quality` | `/api/quality` | the Quality tab endpoint. |
| `routes/readiness.py` | small | `bp_readiness` | `/api/repo-readiness` | ``bp_readiness`` — repo AI-readiness. |
| `routes/reasoning.py` | medium | `bp_reasoning` | `/api/reasoning` | Reasoning chain viewer endpoint. |
| `routes/reports.py` | medium | `bp_reports` | `/api/reports`, `/reports`, `/reports/export.csv` | ClawMetry Reports: markdown + embedded DuckDB SQL. |
| `routes/review.py` | medium | `bp_review` | `/api/review` | decision sampling review surface (issue #1615). |
| `routes/rules.py` | small | `bp_rules` | `/api/v2` | Rule Builder backend endpoints. |
| `routes/runtime_ingest.py` | small | `bp_runtime_ingest` | `/api/v1` | OSS stub after the impl moved to clawmetry-pro. |
| `routes/runtime_memory.py` | small | `bp_runtime_memory` | `/api/runtimes` | Per-runtime Memory & Skills browser API. |
| `routes/scheduler.py` | small | `bp_scheduler` | `/api/run-ledger` | OpenClaw run-ledger + queue-lane endpoints. |
| `routes/selfconfig.py` | medium | `bp_selfconfig` | `/api/selfconfig` | Self-configuration diff viewer endpoints. |
| `routes/selfdiag.py` | small | `bp_selfdiag` | `/api/self-reports` | Agent self-diagnostics read API (WO-59). |
| `routes/selfevolve.py` | small | `bp_selfevolve` | `/api/selfevolve` | OSS stub after the impl moved to clawmetry-pro. |
| `routes/selfhosted_ingest.py` | medium | `bp_selfhosted` | `/api/approvals`, `/api/cloud`, `/api/export`, `/api/ingest`, `/api/register`, `/api/selfhosted`, `/auth`, `/ingest/autonomy`, `/ingest/cache`, `/ingest/events`, `/ingest/heartbeat`, `/ingest/logs`, `/ingest/memory`, `/ingest/sessions`, `/ingest/stream`, `/ingest/system-snapshot`, `/selfhosted` | ClawMetry Enterprise self-hosted ingest API. |
| `routes/sessions.py` | huge | `bp_sessions` | `/api/agents`, `/api/authority`, `/api/compactions`, `/api/cost-split`, `/api/delegation-tree`, `/api/error-triage`, `/api/export`, `/api/fallbacks`, `/api/live-sessions`, `/api/orchestration`, `/api/orchestration-summary`, `/api/outcomes`, `/api/replay-tree`, `/api/run-compare`, `/api/session-errors`, `/api/session-governance`, `/api/session-insight`, `/api/session-lineage`, `/api/session-model-journey`, `/api/session-orchestration`, `/api/session-tools`, `/api/sessions`, `/api/spans`, `/api/subagents`, `/api/task-runs`, `/api/transcript`, `/api/transcript-events`, `/api/transcript-page`, `/api/transcripts`, `/api/waste-summary` | Session / transcript / sub-agent API endpoints. |
| `routes/signals.py` | medium | `bp_signals` | `/api/briefs`, `/api/signals` | Behaviour Signals read API (WO-58). |
| `routes/skills.py` | medium | `bp_skills` | `/api/skills` | Skills fidelity telemetry endpoints (GH #687). |
| `routes/sla.py` | small | `bp_sla` | `/api/sla` | SLA policy CRUD + compliance-status endpoints. |
| `routes/spend_flow.py` | small | `bp_spend_flow` | `/api/spend-flow` | node-wide AI spend flow (the "where does the |
| `routes/tool_catalog.py` | medium | `bp_tool_catalog` | `/api/mcp-servers`, `/api/tool-catalog` | interactive tool catalog + provenance (PRD P1-3). |
| `routes/tracing.py` | large | `bp_tracing` | `/api/trace`, `/api/traces` | Phoenix/Arize-style tracing endpoints. |
| `routes/trail.py` | small | `bp_trail` | `/api/trail` | decision-trail coverage, declared per runtime. |
| `routes/trial.py` | medium | `bp_trial` | `/api/trial` | Local free-trial activation. |
| `routes/turn_anatomy.py` | medium | `bp_turn_anatomy` | `/api/turn-anatomy` | per-turn anatomy waterfall (PRD P0-3). |
| `routes/update_check.py` | large | `bp_update_check` | `/api/update-check` | Auto-update checker with changelog notification. |
| `routes/usage.py` | huge | `bp_usage` | `/api/activity-today`, `/api/anomalies`, `/api/efficiency`, `/api/forward-progress`, `/api/model-attribution`, `/api/nemo-cap-status`, `/api/runtime-summary`, `/api/sessions`, `/api/skill-attribution`, `/api/skills`, `/api/token-attribution`, `/api/token-velocity`, `/api/usage` | Usage / analytics / anomaly / attribution endpoints. |
| `routes/workspaces.py` | small | `bp_workspaces` | `/api/workspaces` | Multi-profile OpenClaw workspace discovery + switcher. |

## Shared helpers (`helpers/`)

Helpers extracted out of `dashboard.py`. Route modules still reach the ones that have not moved yet via a late `import dashboard as _d`.

| Module | Size | Blueprints | Serves | Purpose |
|---|---|---|---|---|
| `helpers/gateway.py` | medium |  |  | OpenClaw gateway WebSocket RPC + HTTP invoke client. |
| `helpers/hardware.py` | small |  |  | Real host hardware detection (CPU / cores / RAM / backend). |
| `helpers/logs.py` | medium |  |  | Filesystem helpers for OpenClaw log discovery + tail + grep. |
| `helpers/openapi.py` | medium | `bp_openapi` | `/api/docs`, `/openapi.json` | auto-generate an OpenAPI 3.1 spec from Flask routes. |
| `helpers/pricing.py` | small |  |  | Pure helpers for mapping model names to providers. |
| `helpers/streams.py` | small |  |  | Bounded SSE client accounting. |
| `helpers/system.py` | medium |  |  | Portable system uptime helpers. |

## Package (`clawmetry/`)

The pip-installable package: CLI, sync daemon, DuckDB store, detectors, enforcement and the free runtime adapters.

| Module | Size | Purpose |
|---|---|---|
| `clawmetry/_gate.py` | medium | Shared 402 ``upgrade_required`` decorator for entitlement-gated routes. |
| `clawmetry/_paywall.py` | medium | Shared 402 ``upgrade_required`` body builder for OSS stub blueprints. |
| `clawmetry/_paywall_events.py` | large | In-process rolling store for ``POST /api/paywall/event`` client beacons. |
| `clawmetry/alert_evaluator.py` | large | Local alert-rule evaluator — pure logic, no I/O (PRD #779 PR-D part 2). |
| `clawmetry/approval_events.py` | small | The public seam between approvals and whoever delivers them. |
| `clawmetry/approvals.py` | large | cloud-mediated approval policy engine. |
| `clawmetry/attention_hook.py` | small | the `clawmetry hook attention` client. |
| `clawmetry/audit.py` | medium | append-only audit log. |
| `clawmetry/behaviour_signals.py` | large | Behaviour Signals: what people and agents *say* about a run (WO-58). |
| `clawmetry/brain_dedupe.py` | medium | Shared collapse for duplicate Brain-feed events. |
| `clawmetry/briefs.py` | medium | Briefs (WO-62): a saved question, a schedule, and a destination channel. |
| `clawmetry/ccr.py` | small | CCR — reversible event-payload compression for the DuckDB store (#2843). |
| `clawmetry/claude_code_gate.py` | medium | Claude Code pre-tool gate: policy-driven PreToolUse hook, local-first. |
| `clawmetry/cli.py` | huge |  |
| `clawmetry/cohort_compare.py` | medium | Cohort compare and similar runs: pure math, no I/O (WO-60). |
| `clawmetry/cohort_queries.py` | medium | Store reads behind cohort compare and similar runs (WO-60). |
| `clawmetry/config.py` | medium | ClawMetry configuration dataclass. |
| `clawmetry/connector_health.py` | small | Connector liveness — turn the daemon's ``connector.health`` signal |
| `clawmetry/context_coverage.py` | small | Which context-blowout signals we can actually see, per runtime. |
| `clawmetry/context_windows.py` | medium | Context-window sizing across every runtime ClawMetry ingests. |
| `clawmetry/cost_windows.py` | small | One definition of "today", "this week" and "this month" for every cost surface. |
| `clawmetry/cursor_connector.py` | medium | Opt-in pull of Cursor cloud-agent usage, with the operator's own key. |
| `clawmetry/daemon_registration.py` | medium | one place that knows how to make the |
| `clawmetry/deepeval_bridge.py` | medium | optional DeepEval metric engine (local-first). |
| `clawmetry/delegated_usage.py` | medium | Usage for work a runtime handed to another vendor's agent. |
| `clawmetry/detector_behaviour.py` | medium | Is this agent doing something it does not normally do? |
| `clawmetry/detector_calibration.py` | medium | How a detector decides what "too many" means, for THIS runtime and THIS team. |
| `clawmetry/detector_money.py` | small | What a finding costs, and therefore what to look at first. |
| `clawmetry/detector_surface.py` | medium | What a tool call actually touched, and what a finding may repeat back. |
| `clawmetry/detectors.py` | large | research-backed, judge-free, CPU-cheap trajectory |
| `clawmetry/deterministic_evaluators.py` | medium | cheap, code-based checks on sessions. |
| `clawmetry/distinfo_cleanup.py` | small | prune stale dist-info left by partial upgrades. |
| `clawmetry/dives_prompt.py` | medium | prompt template + schema descriptor for Dives. |
| `clawmetry/dives_sql_safety.py` | medium | SQL safety validator for ClawMetry Dives (AI SQL -> chart over local DuckDB). |
| `clawmetry/doctor.py` | medium | clawmetry doctor — enterprise network connectivity diagnostics. |
| `clawmetry/efficiency.py` | medium | Efficiency grade + measured savings (pure math). |
| `clawmetry/endpoints.py` | small | clawmetry.endpoints — single source of truth for cloud endpoint resolution. |
| `clawmetry/entitlements.py` | huge | open-core entitlement resolution. |
| `clawmetry/error_signal.py` | small | OSS delegating shim after the impl moved to clawmetry-pro. |
| `clawmetry/eval_regression_replay.py` | medium | Phase 3 evals: regression-replay. |
| `clawmetry/eval_runner.py` | large | Local-first LLM-as-judge scoring of completed sessions. |
| `clawmetry/eval_suite_runner.py` | medium | Phase 2 evals: golden test sets + CLI runner. |
| `clawmetry/evaluators.py` | medium | the named evaluator CATALOGUE (single source of truth). |
| `clawmetry/event_shape.py` | small | ONE normalizer for every stored event shape. |
| `clawmetry/event_shape_classify.py` | medium | Event-shape classifier implementation (private to :mod:`clawmetry.event_shape`). |
| `clawmetry/extensions.py` | medium | ClawMetry extension/plugin system. |
| `clawmetry/flow_trace.py` | medium | Flow trace assembly for the Harness Engineering tab (REQ-HB-006). |
| `clawmetry/gateway_protocol.py` | small | the single source of the OpenClaw gateway |
| `clawmetry/gateway_tap.py` | medium | live OpenClaw gateway WebSocket subscriber. |
| `clawmetry/git_outcomes.py` | medium | Read a repository and say whether the agent's work shipped (REQ-OBS-CEA-022). |
| `clawmetry/guard_actuator.py` | medium | Guard actuator — the ONE path from a decision to a process. |
| `clawmetry/harness_bench.py` | medium | Harness Engineering bench: pure scoring math, no I/O. |
| `clawmetry/harness_templates.py` | medium | Per-harness custom-tab template registry. |
| `clawmetry/hook_ownership.py` | medium | Ownership-aware editing of a shared hooks array. |
| `clawmetry/hooks.py` | medium | Hook lifecycle manager — install manifest and atomic install/uninstall API. |
| `clawmetry/hooks_claude_code.py` | large | Claude Code hooks → ClawMetry: pre-execution approval gate + phone pushes. |
| `clawmetry/incident_alerts.py` | medium | deliver a detector incident to a human. |
| `clawmetry/insights.py` | medium | Weekly Insights Digest — LLM-over-DuckDB summary of the last 7 days. |
| `clawmetry/installs.py` | medium | Install census — find every clawmetry copy on this machine and flag stale ones. |
| `clawmetry/instrument.py` | medium | ``clawmetry instrument <runtime>`` — switch a runtime's own OpenTelemetry |
| `clawmetry/interceptor.py` | medium | Zero-config HTTP interceptor for LLM API cost tracking. |
| `clawmetry/latency_tracker.py` | small | Per-endpoint p50/p95 handler-latency tracker (in-memory rolling window). |
| `clawmetry/license.py` | huge | self-hosted Pro/Enterprise license client. |
| `clawmetry/lifecycle_coverage.py` | medium | Which lifecycle facts each runtime can put on a session's trail. |
| `clawmetry/local_server.py` | medium | HTTP query server hosted INSIDE the sync daemon process. |
| `clawmetry/local_store.py` | huge | Local DuckDB event store — Phase 1 of the local-first refactor (#964). |
| `clawmetry/mcp_install.py` | medium | Register the ClawMetry MCP server with each runtime's MCP configuration |
| `clawmetry/mcp_server.py` | medium | ClawMetry MCP server — exposes local telemetry as MCP tools (stdio transport). |
| `clawmetry/narrator.py` | small | LLM-narrated alert enrichment (issue #1412, Feature C). |
| `clawmetry/net.py` | medium | clawmetry.net — outbound TLS + proxy bootstrap for enterprise networks. |
| `clawmetry/numbat_ingest.py` | medium | map Perplexity numbat NDJSON records into ClawMetry rows. |
| `clawmetry/onboarding_state.py` | small | the ONE writer for the first-run gate's |
| `clawmetry/org_key.py` | small | The organisation key: one secret, shared by the people in one organisation. |
| `clawmetry/otel_exporter.py` | medium | Outbound OTLP trace exporter for ClawMetry. |
| `clawmetry/otel_profiles.py` | small | OTel runtime profiles — the seam between the generic OTLP receiver and |
| `clawmetry/otel_push.py` | small | OSS delegating shim after the impl moved to clawmetry-pro. |
| `clawmetry/otlp_json.py` | medium | stdlib OTLP/JSON decoder (issue #4781). |
| `clawmetry/outcome_classifier.py` | large | Auto-label every session with an outcome. |
| `clawmetry/policy_engine.py` | medium | Guard policies — turn a detector incident into an enforcement decision. |
| `clawmetry/process_control.py` | large | host-side process control for runaway agents. |
| `clawmetry/provenance.py` | medium | Every number says how it was obtained. |
| `clawmetry/providers_pricing.py` | medium | ClawMetry provider detection and pricing table. |
| `clawmetry/proxy.py` | large | ClawMetry Proxy — opt-in enforcement layer between OpenClaw and LLM providers. |
| `clawmetry/published_benchmarks.py` | small | Published (harness, model) benchmark pairs for the Harness Engineering tab. |
| `clawmetry/quality.py` | medium | the Quality tab's plain-English layer. |
| `clawmetry/quality_signals.py` | medium | evidence-bearing quality signals. |
| `clawmetry/quality_thresholds.py` | small | per-runtime threshold calibration. |
| `clawmetry/query_contract.py` | medium | the declared q/1 query contract registry. |
| `clawmetry/question_sets.py` | medium | Question-set approvals — decisions beyond yes/no (WO-52, phase 1). |
| `clawmetry/redaction.py` | medium | Defense-in-depth secret redaction for the daemon ingest path. |
| `clawmetry/relay.py` | small | DEPRECATED stub. |
| `clawmetry/replay_schema.py` | small | Canonical replay-event schema. |
| `clawmetry/repo_readiness.py` | medium | how legible is this repo to an agent? |
| `clawmetry/resume_hints.py` | medium | How a human restarts a session ClawMetry can no longer control. |
| `clawmetry/retention.py` | small | How long this node keeps event data — one answer, with its reason. |
| `clawmetry/risk.py` | medium | Hallucination Risk Indicator (issue #567). |
| `clawmetry/runtime_gates.py` | medium | Pre-tool gates for Cursor and GitHub Copilot CLI — "block before it runs". |
| `clawmetry/runtime_memory.py` | large | Per-runtime Memory & Skills file browser. |
| `clawmetry/runtime_probe.py` | medium | zero-dependency presence probes for every |
| `clawmetry/runtime_records.py` | medium | What each runtime actually records — so a surface can say "not recorded" |
| `clawmetry/secure.py` | medium | clawmetry secure — one-command numbat (Perplexity agent-EDR) setup. |
| `clawmetry/security_posture.py` | large | Runtime-aware security posture registry. |
| `clawmetry/self_diagnostics.py` | medium | Agent self-diagnostics: reports an agent files about its own trouble, and |
| `clawmetry/selfhosted.py` | small | clawmetry.selfhosted — ClawMetry Enterprise single-tenant server mode. |
| `clawmetry/session_context.py` | medium | Inputs & context: what the agent was actually given, per session. |
| `clawmetry/session_titles.py` | medium | ChatGPT-style session titles from the first real user prompt. |
| `clawmetry/siem.py` | small | OSS delegating shim after the impl moved to clawmetry-pro. |
| `clawmetry/signal_shifts.py` | medium | Signal shifts (WO-62): notice when a behaviour-signal rate moves, explain |
| `clawmetry/span_reconstruct.py` | medium | Runtime-agnostic span reconstruction for family runtimes (Agent Graph WS-A). |
| `clawmetry/spend_flow.py` | medium | node-wide AI spend flow (pure math). |
| `clawmetry/sync.py` | huge | Cloud sync daemon for clawmetry connect. |
| `clawmetry/telemetry.py` | medium | anonymous, opt-out, install-lifecycle pings. |
| `clawmetry/token_confidence.py` | medium | Token Probability Visualizer (issue #563). |
| `clawmetry/tool_risk.py` | medium | deterministic call-level risk classification. |
| `clawmetry/trace.py` | medium | clawmetry.trace — Dependency-free Python tracing SDK for AI applications. |
| `clawmetry/trace_auto.py` | medium | Automatic PR tracing: capture, publish and comment, with no command. |
| `clawmetry/trace_capture.py` | medium | Build a PR trace bundle from local session data (PRD-pr-trace.md §4b). |
| `clawmetry/trace_stamp.py` | medium | Stamp agent-authored commits with the ClawMetry session that produced them. |
| `clawmetry/trace_viewer.py` | medium | Render a trace bundle to a self-contained HTML page (PRD-pr-trace.md §4g). |
| `clawmetry/track.py` | small | clawmetry.track — Zero-config HTTP interceptor for LLM cost tracking. |
| `clawmetry/trail_store.py` | medium | Trail store methods: session intent, typed-event back-fill, per-session git join. |
| `clawmetry/trial_enforcement.py` | medium | Trial-end hard-block layer. |
| `clawmetry/update_guard.py` | small | Crash-loop rollback guard for daemon self-update (firmware-OTA style). |
| `clawmetry/update_respawn.py` | medium | Windows out-of-process updater. |
| `clawmetry/waste_flags.py` | small | OSS delegating shim after the impl moved to clawmetry-pro. |
| `clawmetry/watchdog.py` | medium | macOS "app-vanished" watchdog. |
| `clawmetry/winconsole.py` | small | clawmetry.winconsole — stop Windows console windows flashing. |
| `clawmetry/workload_profiles.py` | small | Workload profiling for the Harness Engineering tab (REQ-HB-004). |

## Free runtime adapters (`clawmetry/adapters/`)

The runtime adapters that ship in open source. The paid ones live in `clawmetry-pro` and register over the `clawmetry.extensions` entry point; see `sync._FAMILY_ADAPTER_SPECS` for the load order.

| Module | Size | Purpose |
|---|---|---|
| `clawmetry/adapters/base.py` | medium | Adapter base class + unified schemas. |
| `clawmetry/adapters/cost.py` | small | Shared cost-derivation helper for the bundled runtime adapters. |
| `clawmetry/adapters/goose.py` | medium | GooseAdapter — read Goose (Block / block/goose) sessions from its SQLite store. |
| `clawmetry/adapters/nemo.py` | large | NeMoAdapter — push-mode telemetry exporter for NVIDIA's NeMo Agent Toolkit. |
| `clawmetry/adapters/openclaw.py` | large | This adapter does NOT re-implement OpenClaw session parsing. It delegates |
| `clawmetry/adapters/phase.py` | medium | The session phase model: one state machine, every runtime. |
| `clawmetry/adapters/registry.py` | small | Process-wide adapter registry. |

## Data providers (`clawmetry/providers/`)

The pluggable data-provider layer behind `CLAWMETRY_PROVIDER`.

| Module | Size | Purpose |
|---|---|---|
| `clawmetry/providers/base.py` | small | Abstract data provider interface for ClawMetry. |
| `clawmetry/providers/local.py` | medium | Local filesystem data provider — reads directly from ~/.openclaw files. |
| `clawmetry/providers/turso.py` | small | Turso cloud data provider for ClawMetry cloud dashboard. |

## CLI subcommands (`clawmetry/cli_cmds/`)

Subcommands dispatched by `clawmetry/cli.py`.

| Module | Size | Purpose |
|---|---|---|
| `clawmetry/cli_cmds/_common.py` | medium | Shared plumbing for the agent-facing read CLI. |
| `clawmetry/cli_cmds/activity.py` | small | `clawmetry activity` — the Brain event feed from the terminal. |
| `clawmetry/cli_cmds/progress.py` | small | `clawmetry progress` — is the agent actually getting anywhere? |
| `clawmetry/cli_cmds/selfevolve.py` | small | `clawmetry selfevolve` — OSS 402 stub for the Pro self-improvement engine. |
| `clawmetry/cli_cmds/sessions.py` | medium | `clawmetry sessions` — list sessions; drill into one with facets. |
| `clawmetry/cli_cmds/usage.py` | small | `clawmetry usage` — token/cost analytics from the terminal. |
| `clawmetry/cli_cmds/waste.py` | small | `clawmetry waste` — the re-read tax, from the terminal. |

## v2 API (`clawmetry/v2/`)

The versioned public API surface.

| Module | Size | Blueprints | Serves | Purpose |
|---|---|---|---|---|
| `clawmetry/v2/route_map.py` | small |  |  | Canonical tab-name mapping between v1 and v2 URL schemes. |
| `clawmetry/v2/routes.py` | medium | `bp_v2` | `/api/v2` | ClawMetry v2 Flask blueprint. |
