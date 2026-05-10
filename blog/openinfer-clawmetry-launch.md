# Closing the observability gap in heterogeneous inference

*A joint post by OpenInfer and ClawMetry — accompanying the launch of OpenInfer's managed service for OpenClaw.*

> **TL;DR** — OpenInfer is launching a managed inference service for OpenClaw that dynamically routes each agent request to the cheapest hardware that meets its SLA — including non-NVIDIA silicon like AWS Graviton. Drop a `config.json` into your OpenClaw directory and your existing agent runs unchanged on the new substrate. ClawMetry plugs in with zero extra config and surfaces what each routing decision actually cost in tokens, dollars, and latency — per session, per sub-agent, per tool call. The two products together give you complete visibility *and* automatic optimization without changing a line of agent code.

---

## The awkward gap that comes with smart routing

Every inference router worth using makes opinionated decisions on the user's behalf: this prompt goes to a GPU, that one to a CPU, this batch to a smaller model, that one to a bigger one. OpenInfer's managed service for OpenClaw is no exception — its scheduler classifies each incoming request by context length, latency tier, and runtime signals, then sends it to whichever processor in the mesh can serve it cheapest within the SLA.

That's a strict win for cost. But it creates a new visibility problem.

When the agent operator opens a dashboard the next morning and asks *"why did yesterday's spend spike?"*, the answer they used to get from a single-vendor LLM call ("we made N calls × M tokens × $X/token") doesn't apply. Now the right answer is *"42% of your sessions ran on the L40S queue at 40 tok/s, the other 58% ran on EPYC CPUs at 20 tok/s aggregate, and the spike came from one runaway agent that re-spawned 17 sub-agents inside a Telegram thread."* You can't see any of that from inference-layer metrics alone — the router doesn't know which sub-agent was talking to which user, and the agent runtime doesn't know which silicon ran each turn.

This is the observability gap. Two layers, each smart at its own job, neither holding the full picture.

The combined product closes it.

---

## What launches Friday

OpenInfer's managed service for OpenClaw is a drop-in replacement for the inference layer in your OpenClaw deployment. Concretely:

- **Single-file integration.** Drop `config.json` into your OpenClaw workspace. No changes to agent code, tools, or skills. The agent calls its model the same way it always did; OpenInfer's scheduler routes the request behind an OpenAI-compatible endpoint to whichever processor in its mesh is the cheapest fit for the SLA.
- **Heterogeneous fleet.** Each session is dispatched across CPUs, GPUs, NPUs, and custom silicon — five architectures so far. Latency-critical turns go to the L40S queue; long-running background reasoning goes to EPYC Graviton CPUs at a fraction of the cost. You don't pick the hardware. The router does.
- **File-backed KV cache for cross-processor migration.** A three-tier memory hierarchy (VRAM → RAM → NVMe) means a session can migrate between processors at prefill/decode boundaries without re-paying the prefill cost. The agent never knows it moved.
- **Capacity headroom.** OpenInfer's published reference numbers show ~+50% capacity on a single AWS `g6e.16xlarge` (L40S + EPYC 7R13) with no additional GPU spend, by recruiting the otherwise-idle CPUs into the inference fabric. Same dollar, more sessions.

For the deeper architecture — vertical disaggregation, the `batchEngine` SLA-aware scheduler, custom Q4_0 kernels — see OpenInfer's [previous post on heterogeneous silicon](https://openinfer.io/news/2026-04-20-vertical-disaggregation-maximizing-throughput-on-heterogeneous-silicon/).

---

## What ClawMetry shows you about OpenInfer-routed inference

ClawMetry is the open-source observability layer for OpenClaw agents (`pip install clawmetry`, 150K+ installs across 100+ countries). Because it observes at the agent layer — not the inference layer — it correctly attributes every token, dollar, and second back to the *session*, *sub-agent*, and *tool call* that caused it, regardless of which processor OpenInfer routed it to.

For a user running both products, the integration is zero-touch. ClawMetry's HTTP interceptor (a small monkey-patch on the OpenClaw process's HTTPX/Requests stack) sees every inference call as it goes out, captures provider, model, token counts, and end-to-end latency, and stitches them into the existing dashboard surfaces:

- **Brain tab** — the unified real-time stream now annotates each LLM turn with the OpenInfer route taken (CPU vs GPU pool), so you can scroll a Telegram chat replay and see *"this turn cost $0.0008, ran on EPYC, 1.4 s end-to-end"* alongside the user's message and the agent's reply.
- **Tokens tab** — token + cost charts split by routing decision. The same model served on two processors shows up as two cost lines, so you can see exactly what fraction of the spend is the cheap path.
- **Sessions tab** — per-session cost attribution with model + route mix. Useful for billing, quota, and "which user is expensive?" questions.
- **Sub-agent tracker** — a runaway agent that fanned out 17 sub-agents shows up as a tree, each leaf with its own cost. You can see exactly where the spend went.
- **Alerts** — set a rule once: "page me if any single session exceeds $5 or any agent spawns >10 sub-agents in 60 seconds." Works across the OpenInfer-routed fleet without any per-route configuration.

Two demos are worth calling out, both new for this launch:

**1. The cost-by-route view.** In the Tokens tab you'll see two new lines: one for OpenInfer's GPU pool, one for the CPU pool. They're computed locally on the user's machine — no inference internals leak — and they make the cost story OpenInfer is already telling provable to the operator's own finance team.

**2. The kill switch.** Most agentic systems today have no graceful "stop" — when a sub-agent recursion goes wrong, you watch the token meter run until the API key hits a quota wall. ClawMetry is shipping a per-session kill switch that talks back to the OpenClaw gateway and ends the runaway in-place. Combined with OpenInfer's per-tier SLA budgets, this means operators get both *automatic cost control at the substrate* and *explicit user control at the agent*.

---

## Try it together

We've published a short integration guide and a one-config-file recipe so you can wire both products against your existing OpenClaw deployment in under five minutes:

- **Start the OpenInfer beta** — [openinfer.io/beta](https://openinfer.io/beta/)
- **Install ClawMetry** — `pip install clawmetry && clawmetry`
- **Read the joint integration guide** — [linked from both blogs]

If you're an OpenClaw operator running multi-tenant workloads or sensitive data: this combination is the closest thing we have to a complete agent operations stack today. OpenInfer makes the substrate cheap and fast. ClawMetry makes everything that happens on it observable, attributable, and controllable. Neither requires changes to your agent code.

---

## What's next

Two of the things we heard from beta users in the past week are already on the roadmap:

- **A "raw payload" toggle** in the Brain tab so users studying OpenClaw's behaviour can flip between the structured view and the exact bytes sent upstream.
- **Memory-access history** — clicking on a memory file shows the sessions and turns that read or wrote it, so you can ask "why does the agent think this?" and trace the answer.

Both ship in the next ClawMetry release.

---

## Quotes

> "OpenInfer turns the inference substrate from a fixed cost into a routing problem. ClawMetry's job is to make sure that, when the substrate gets smart, the operator doesn't get blind. Together you get the cost curve of heterogeneous compute and the explainability of a single-vendor stack — without the trade-off either has alone."
> — **Vivek Chand**, founder, ClawMetry

> *[Quote from Kam Eshghi / Behnam Bastani, OpenInfer — to be added]*

---

*ClawMetry is open-source observability for AI agents — `pip install clawmetry`. OpenInfer is a managed inference service that routes agent workloads across heterogeneous silicon. Both products believe the operator should never have to choose between cost and visibility.*

---

### Editor's notes (remove before publishing)

**For Kam / OpenInfer team — placeholders to fill in:**
1. Concrete numbers for the cost-by-route demo: % of spend on CPU pool vs GPU pool on a representative workload, and absolute $ savings vs single-vendor LLM call. We can pull from the same `g6e.16xlarge` fixture used in the reference post.
2. The `config.json` snippet for the integration guide — exact shape of the file so the post can show "drop this in `~/.openclaw/`".
3. OpenInfer-side quote (Kam or Behnam).
4. A screenshot of the ClawMetry Tokens tab showing the two cost lines (GPU/CPU split) — Vivek to capture once the live demo is recorded.
5. Confirm public-facing positioning of the L40S + EPYC numbers (~+50% capacity) — happy to use exact figures from your reference post or substitute fresh ones from the OpenClaw managed-service benchmark.

**For ClawMetry side — pre-publish checklist:**
- [ ] Land the kill-switch capability in `routes/sessions.py` (currently in design — issue to be filed) so the post's claim is shipped, not aspirational.
- [ ] Land "raw payload toggle" in the Brain tab — addresses pain point #1 from beta feedback.
- [ ] Land memory-access history (`memory_read` / `memory_write` event types annotated with originating session_id) — addresses pain point #2.
- [ ] Capture the screenshots referenced above.
- [ ] Co-publish on both blogs same day; cross-link.
- [ ] Social: announce on LinkedIn from both founder accounts; schedule for the Friday launch window.

### Editorial notes on voice (internal)

This draft was assembled from five distinct perspectives:

1. **Technical infra writer** — opening problem framing (the "observability gap"), the architecture call-out, integration mechanics. Mirrors OpenInfer's reference post: declarative, problem-first, quotes their coined concepts.
2. **Product marketer** — the "complete agent operations stack" positioning in the closing section, the explicit value props per dashboard tab, the buyer-language summary.
3. **Developer advocate** — the "Try it together" section, the under-five-minutes claim, the actual install command. The promise is reproducibility, not vague capability.
4. **Narrative storyteller** — the "awkward gap" framing in the opening, the "you can scroll a Telegram chat replay and see…" sentence. Concrete > abstract every time.
5. **Data analyst** — the demo numbers section, the cost-by-route view, the explicit "two new lines in the Tokens tab" specificity. Avoids the trap of making promises before screenshots exist.

If you want a lighter / heavier version, easiest dial is the demo numbers section: trim to one paragraph for a marketing audience, expand with a benchmark table for an engineering audience.
