# PRD: ClawMetry Tracing

**Status:** Draft for build · **Date:** 2026-05-22 · **Owner:** Tracing working group
**Panel:** 3 Principal Engineers (Observability/OTel · Agent-tracing systems · Performance/Cloud) + 4 PMs (Core debug · Cost · Agency/monetization · Platform/fleet)
**Supersedes:** the naive `?tracing=1`-gated tab shipped 2026-05-22 (event-chain "staircase"). That tab stays gated until this PRD's v1 lands.

---

## 0. Why this exists (and what was wrong)

The first Tracing tab built a "tree" by following each event's `data.parentId`. In OpenClaw v3 that pointer is a **conversation linked-list** (each event points to the immediately-preceding one), so a 1559-event run nested ~1399 levels deep into a diagonal staircase. That is not a trace — it's a prettier transcript. This PRD specifies a **real** trace: a shallow, wide tree of typed spans with correct parent/child causality, latency, and per-span cost — the unit of debugging for agents.

---

## 1. Observability primer (shared vocabulary)

*(from PE-Observability; grounded in the OpenTelemetry spec, which is **Stable** for tracing and **Development** for the GenAI conventions.)*

- **Trace** — everything that happened for one logical run, as a tree of spans sharing one `trace_id`.
- **Span** — one timed unit of work. Canonical fields: `trace_id`, `span_id`, `parent_span_id` (empty on the root), `name` (low-cardinality), `start_time`/`end_time` (**duration is derived = end − start**), `kind` (SERVER/CLIENT/INTERNAL/PRODUCER/CONSUMER; default INTERNAL), `status` (Unset/Ok/Error + message-only-on-error), `attributes` (flat k/v), `events` (point-in-time annotations), `links` (cross-tree causality).
- **The tree is defined purely by `parent_span_id`.** Root has none; each other span points at exactly one parent; same-parent spans are siblings. Many-to-many uses *links*, never parents.
- **Waterfall** = render each span as a horizontal bar (x = time from trace start, width = duration), rows ordered depth-first with one level of indent per `parent_span_id` hop. A parent bar extending past its children = work/wait outside the children; overlapping siblings = concurrency; error = red.
- **"Good" depth** for an agent run is **3–5 levels**, branching a few children per node — NOT a flat list (no causality) and NOT a deep chain (fake nesting).

**GenAI semantic conventions** (`gen_ai.*`) define the span taxonomy we map to:

| Operation | `gen_ai.operation.name` | Span name | Kind |
|---|---|---|---|
| LLM call | `chat` | `chat {model}` | CLIENT/INTERNAL |
| Tool call | `execute_tool` | `execute_tool {tool}` | INTERNAL |
| Retrieval/RAG | `retrieval` | `retrieval {source}` | CLIENT |
| Embeddings | `embeddings` | `embeddings {model}` | CLIENT |
| Agent run | `invoke_agent` | `invoke_agent {agent}` | INTERNAL/CLIENT |
| Multi-agent | `invoke_workflow` | `invoke_workflow {name}` | INTERNAL |

Key attributes: `gen_ai.provider.name` (use this, **not** the deprecated `gen_ai.system`), `gen_ai.request.model`, `gen_ai.usage.input_tokens`/`output_tokens` (must include cached), `gen_ai.response.finish_reasons`, `gen_ai.tool.name`, `gen_ai.tool.call.id`, `gen_ai.agent.name`, `error.type`. Sensitive content (`gen_ai.input.messages`/`output.messages`) is **opt-in, never captured by default** — for us it rides the E2E-encrypted path only.

**Canonical example — one turn calling 2 tools + a sub-agent (this is the target shape):**

```
invoke_agent "main"                          INTERNAL  Ok  [t0 .. +8.0s]
├─ chat claude-opus-4-7                       CLIENT   Ok  [+0.0 .. +1.2s]  in=1850 out=120  finish=tool_use
├─ execute_tool Read                          INTERNAL Ok  [+1.2 .. +1.5s]  call_a1
├─ execute_tool web_search                    INTERNAL Ok  [+1.2 .. +2.6s]  call_b2  (concurrent)
├─ chat claude-opus-4-7                        CLIENT   Ok  [+2.6 .. +3.4s]  in=2400 out=90   finish=tool_use
├─ invoke_agent "summarizer" (sub)            INTERNAL Ok  [+3.4 .. +7.0s]
│  ├─ chat claude-sonnet-4                     CLIENT   Ok  [+3.5 .. +5.0s]
│  └─ execute_tool fetch_document             INTERNAL Ok  [+5.0 .. +5.4s]
└─ chat claude-opus-4-7                        CLIENT   Ok  [+7.0 .. +8.0s]  finish=stop
```

---

## 2. Problem & why ClawMetry's current surfaces fail

*(from PM-Core)* A multi-step agent is a distributed system: every tool call is a fallible network request, every reasoning step a non-deterministic decision. When a run goes wrong the failure is usually **upstream of where it surfaces**. Today ClawMetry has **transcripts** and the **brain feed** — a *chronological log*, not a *causal tree*. They cannot answer the four core jobs:

1. **Root-cause a bad run** — which step introduced the error (flat log interleaves concurrent sub-agents by timestamp; no causality).
2. **Find the slow step** — no per-span duration, no waterfall.
3. **Find the expensive step** — cost is run/model-aggregate, never per-step in a tree.
4. **Inspect the exact LLM call** — brain summarizes; no reliable verbatim input/output for one call.

Tracing is the missing primitive: *why*, *in what order*, *how long*, *what each step cost*.

---

## 3. Personas & JTBD

*(from PM-Core)*
- **P1 Solo operator ("Sam")** — primary, ~70% of base, semi-technical. *"My nightly agent produced a wrong result — show me which step broke and why, without grepping JSONL."* / *"This run cost 5× normal — which call spent it?"*
- **P2 Agency ("Priya")** — monetization driver, multi-node Cloud-Pro. *"A client says the agent did X wrong Tuesday — pull that run, show the offending step as evidence."* / *"Break cost down per run/step to attribute client spend."*
- **P3 Platform engineer ("Marcus")** — fleet, expansion seat. *"Latency/failure spiked — drill from aggregate into representative slow/failed traces and localize to a tool or model."* / *"Compare a known-good run to a current bad run."*
- **P4 Builder ("Dev")** — evangelist. *"The model picked the wrong tool — show the verbatim context that went in and the raw output."*

**Out of scope as a persona:** the SDK developer who instruments their own code (that's LangSmith/Phoenix). Our user adds nothing — we derive traces by observing OpenClaw. That constraint is the moat (§7).

---

## 4. Use cases (prioritized)

| # | Pri | Story |
|---|-----|-------|
| U1 | P0 | Debug a failed run — trace highlights the span where the error *originated*. |
| U2 | P0 | Find the slow step — waterfall shows which span dominated wall-clock. |
| U3 | P0 | Find the expensive step — per-span token/cost rolled up the tree. |
| U4 | P0 | Inspect the exact LLM call — verbatim assembled input + raw output + tokens. |
| U5 | P1 | Understand sub-agent spawns — sub-agents as nested subtrees with the spawning step. |
| U6 | P1 | Agent graph — node graph of tools/models/sub-agents to read the *shape* / spot loops. |
| U7 | P0 | Browse & filter the trace list — duration, cost, status, #steps; filter failed/slow/expensive. |
| U8 | P2 | Compare two runs (defer). |
| U9 | P2 | Detect runaway loops (lite badge if cheap). |
| U10 | P3 | Live-tail an in-progress run (defer; reuse brain-stream SSE). |

**v1 spine = U1–U4 + U7.** U5/U6 in v1 if cheap. U8–U10 deferred.

---

## 5. Data model & span reconstruction (the heart of the fix)

*(from PE-Observability + PE-Agent-systems + repo scan)*

**Sources, in priority order:**
1. **Real OTel spans** — the repo already has a proper `spans` table (`local_store.py`: `span_id` PK, `trace_id`, `parent_span_id`, `kind`, `status`, `start_ts`/`end_ts`/`duration_ms`, `model`, `tool_name`, `cost_usd`, `tokens_input/output`, `input`/`output`/`attributes` BLOBs) fed by the OTLP `/v1/traces` receiver. **When spans exist for a session, use them directly** — they're already correct.
2. **Derive from events** — when no OTel spans exist (the common case), reconstruct from the events table. Real v3 `event_type`s: `prompt.submitted`, `model.completed`, `tool.call`, `tool.result`, `subagent:*`, plus legacy `assistant`/`user`/`tool-result`. Tool calls live as `tool_use` blocks inside `data.message.content[*]`.

**Reconstruction algorithm (replaces the parentId chain):**
- **Trace = one session** (grain decision Q1; revisit per-prompt later). Root span = `invoke_agent {agent}`.
- **`prompt.submitted` / user** → marks a turn; not its own deep level.
- **`model.completed` / assistant** → a `chat` (LLM) span, child of the agent root. Carries model, input/output tokens, finish reason.
- **`tool_use` block** (inside the assistant turn) → an `execute_tool` span, **child of that `chat` span**, keyed by `tool_use.id`.
- **`tool.result` / `tool-result`** → close the matching `execute_tool` span via `tool_use_id == tool_use.id` (**the single most important join**); set `end_time`, and `status=Error` + `error.type` if the result is an error.
- **`subagent:*`** → group into an `invoke_agent` subtree (one level), re-parented under the turn that spawned it; correlate via spawn tool-call id / sub-session id.
- **Timing fallbacks:** end = matching result ts, else next-sibling start; mark inferred timing `clawmetry.synthetic_timing=true`. **Never** parent a span on the previous span just to get depth.
- **Cost/latency roll up** child→parent by summing leaves; rolled-up cost **must reconcile** with `/api/usage` for that run (guardrail G1).

**Resulting depth:** agent root → chat + tool siblings → optional sub-agent subtree = the 3–5 levels of §1, not 1399.

---

## 6. UX / feature set (v1)

*(from PE-Agent-systems teardown; ranked by value)*

**v1 must-have:**
1. **Trace list** — columns: name, time, **duration, total tokens, cost, status, model, span count** + rollups (#LLM calls, #tool calls). Default sort surfaces errors/slow. Filters: failed / slow / expensive / agent / channel.
2. **Two-panel detail: span tree (left) + span detail (right)**, kind icons (🧠 llm · 🔧 tool · 🤖 agent · 📚 retrieval), per-node duration bar + tokens + cost inline.
3. **Time-proportional waterfall** — relative bar + absolute ms; expand/collapse + Expand-All/Collapse-All; **error spans red and floated to attention**.
4. **Kind-aware span detail panel** — LLM: model + params + verbatim messages (E2E) + tokens + cost; tool: name + args + result; retrieval: docs + scores. MIME-aware (Markdown/JSON).
5. **Cost + tokens propagated child→parent**, shown inline in the tree (find the budget hotspot — aligns with ClawMetry's cost framing).
6. **Errors first-class** — red in list + tree, status filter, click-to-jump-to-first-error.

**v1 if cheap, else first fast-follow:**
7. **Agent graph** — minimal static node graph (tools/models/sub-agents as nodes, control flow as edges).
8. **Latency/cost percentile color-coding** relative to siblings.

**Deferred:** in-trace Filtered-Only/Show-All/Most-Relevant for 1000+ span runs (LangSmith pattern), streaming TTFT split bar, timeline-scaled-by-tokens + cache-hit distribution (Braintrust), chat/thread second view, virtualization/preview mode, run compare, evals/scoring.

---

## 7. Differentiation

*(from PM-Cost + PM-Agency)* We don't win on feature checklists. Structural moats:
1. **Zero-instrumentation, agent-native** — every competitor needs an SDK/decorator/proxy; we derive traces by observing OpenClaw with zero code. *"The only agent tracer you don't have to instrument."*
2. **Privacy is the product** — trace contents are the most sensitive payload (verbatim LLM I/O). They ride the E2E-encrypted path; cloud renders them decrypted **client-side only**. *"See your full prompts in the cloud dashboard; we can't read them."*
3. **Cost-native, flat-priced** — per-span cost rollup extends existing cost infra; $5/node, no per-trace meter (vs LangSmith ~$2.50–5/1k traces).
4. **OpenClaw-native semantics** — render *why a sub-agent spawned*, channel/cron provenance, gateway/runtime/brain in one trace, while staying OTel-shaped for interop.

**Conceded:** evals/experiments, framework breadth, enterprise-scale sampling.

---

## 8. Success metrics & guardrails

- **Activation:** ≥40% of weekly-active dashboards open ≥1 trace/week within 60d; time-to-first-trace <5 min.
- **Time-to-root-cause (headline):** median open-failed-trace → open error span/exact call **<30s**; waterfall→span-detail CTR >60%.
- **Retention:** of week-1 trace users, >35% open another in week 4.
- **Monetization:** tracing in top-3 upgrade-attributed surfaces; retention-window + compare + cross-run analytics = Cloud-Pro.
- **Guardrails (don't ship a lie):** G1 rolled-up trace cost reconciles with `/api/usage` within tolerance for >95% of runs; G2 span attribution spot-checked against **real** OpenClaw v3 events (we've been burned by synthetic-green/real-zero).

---

## 9. Risks & open questions

- **R1 Trace fidelity from observation, not instrumentation** — a wrong-but-authoritative tree is worse than none. Mitigate: G1/G2, smoke on live DuckDB before un-gating.
- **R2 Privacy-in-cloud must be airtight** — trace contents follow the `*_blob` E2E pattern; decrypt client-side only; security review; never log plaintext span bodies server-side.
- **R3 Legibility for big runs** — default-collapse, error-first ordering, jump-to-slowest/most-expensive.
- **Q1** Trace grain: session vs per-prompt? (v1: session; revisit.)
- **Q4** Do we capture verbatim LLM inputs in ingest today? U4 depends on it — audit before committing.
- **Q3** Sub-agent spawn links: reliable from gateway/JSONL or inferred?

---

## 10. Implementation plan (phased; tab stays gated until Phase 2 ships)

- **Phase 1 — correct span reconstruction (backend).** Rewrite `routes/tracing.py` `_build_spans` per §5: prefer real OTel spans (`query_spans`), else derive with the `tool_use ↔ tool_result` join, OTel `gen_ai.*` kinds, child→parent cost/latency rollup. Verify on live data: depth 3–5, cost reconciles with `/api/usage`.
- **Phase 2 — v1 UI.** Span detail panel (kind-aware, MIME), kind icons, cost/tokens inline + rollup, error-first ordering + jump-to-error, trace-list filters. Un-gate behind `?tracing=1` only after Phase 2 review; full un-gate after dogfood.
- **Phase 3 — differentiators.** Agent graph upgrade, percentile color-coding, in-trace filtering for big runs.
- **Phase 4 — cloud.** Ship corrected `traces` in the snapshot (`sync._build_traces` already reuses `_build_spans`, so Phase 1 flows automatically; re-verify size budget) + cloud interceptor; verify live.

---

## Panel sign-off
- **PE-Observability:** model is OTel-correct; the `tool_use↔tool_result` join is the load-bearing primitive — get it right or the tree is fiction.
- **PE-Agent-systems:** v1 spine (list → waterfall → tree → kind-aware detail → cost rollup, error-first) matches table-stakes across Phoenix/LangSmith/Langfuse/Braintrust/Datadog; agent graph is the differentiator to keep cheap-but-present.
- **PE-Performance/Cloud:** reconstruction must stay DuckDB-first; snapshot traces stay span-capped + free-text-stripped (the `raw`-bloat lesson); reconcile cost (G1).
- **PMs:** ship the single-run debug loop first; gate retention/compare/cross-run as Pro; privacy-in-cloud is the headline, protect it.
