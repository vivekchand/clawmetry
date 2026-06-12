# What Users Want — June 2026 Edition

*Auto-generated weekly by the roadmap synthesis bot. Last updated: 2026-06-12 10:30 UTC. Aggregates signal across both `vivekchand/clawmetry` (OSS) and `vivekchand/clawmetry-cloud` (cloud).*

## TL;DR (this week)

The loudest unsolved user pain is **"I can't see what my agent is doing"** — three HN intel threads plus two open EPICs confirm the gap, and two direct competitors (AgentPulse, Faros) are explicitly targeting it right now. Cost intelligence is the second cluster: team-level chargeback, subscription-mode billing blindness (Claude Max / ChatGPT-Plus users see inflated costs that are wrong by design), and proactive spend alerts are all open. Shipping velocity is extremely high — 2,028 merged PRs across both repos in 30 days — but disproportionately focused on voice/device features that have **zero user-demand issues**; the tracing and subscription-mode cost EPICs have been open 18–32 days without resolution.

## Hot themes (build these next)

### 1. "I can't see what my agent is doing" — tracing, sub-agent visibility, run-vs-run diff

- **Demand**: 9 open issues (3 OSS + 3 cloud product + 3 cloud competitor-intel), 0 explicit reactions (reactions not used on this tracker), last raised 2026-06-11
- **Representative quotes**:
  - `clawmetry-cloud#652`: *"My main problem with claude code right now is observability. I've been experimenting a lot with vibe coding, but nowadays I can't even tell what it's doing. It's still delivering me results... but I can't figure out how it's getting there."*
  - `clawmetry-cloud#653`: *"No standardized dashboards exist for token spend ROI analysis... I just can't figure how to burn that much money a month responsibly."* (from a 474-comment HN thread)
  - `clawmetry#1006`: *"Today ClawMetry captures events (tool_call, message) but loses the hierarchy — parent→child relationships between user prompt → LLM call → tool calls → sub-agent spawns. Without that hierarchy, 'why did this run take 30s?' is unanswerable."*
- **Why it matters**: AgentPulse (Show HN, `clawmetry-cloud#649`) launched as a direct ClawMetry alternative specifically on this angle. Faros (`clawmetry-cloud#650`) is targeting the "no cross-developer aggregation" gap — the same value prop ClawMetry owns. If these competitors ship a collapsible trace tree before ClawMetry, the positioning as the observability-first tool gets diluted. The IBM practitioner study (n=38) cited in `clawmetry#3001` found 76% of practitioners rank "understanding agentic flow" as their top analytics need; 77% struggle with root cause. Run-vs-run diff has no current competitor coverage.
- **Linked issues**: `clawmetry#1006`, `clawmetry#1008`, `clawmetry#1012`, `clawmetry#3001`, `clawmetry-cloud#652`, `clawmetry-cloud#703`, `clawmetry-cloud#649`, `clawmetry-cloud#650`, `clawmetry-cloud#651`
- **Likely scope**: Both — OSS gets OTel trace tree + run-vs-run diff panel; cloud gets the cross-machine aggregation surface that no competitor has
- **Suggested first step**: Merge the trace-tree UI (`clawmetry#1008`, bot-PR already open) to unblock the EPIC; then ship run-vs-run flow divergence (`clawmetry#3001`) as the headline differentiator that competitors don't have

---

### 2. Cost intelligence: team chargeback + subscription blindness + spend guardrails

- **Demand**: 10 open issues (5 OSS + 5 cloud), 0 explicit reactions, last raised 2026-06-08
- **Representative quotes**:
  - `clawmetry-cloud#653`: *"I use LLMs daily... anywhere from $200–$400 tops... I just can't figure how to burn that much money a month responsibly."*
  - `clawmetry-cloud#655`: *"By step nine you have a context window the size of a small novel and a per-call cost that has tripled because cache write costs are not what you expected."* (retroactive $47K AI bill scenario)
  - `clawmetry-cloud#1088`: users on ChatGPT-Plus, Codex OAuth, and Claude Max see **grossly inflated cost numbers** because per-token rates are applied to already-flat-fee traffic — *"their dashboards are wrong by design."* This is a correctness problem, not a feature request.
- **Why it matters**: Three distinct sub-pains compound here: (a) teams want per-agent/per-project chargeback (`clawmetry#3000`, `clawmetry-cloud#653`); (b) subscription users are actively mis-served by the current cost display (`clawmetry-cloud#1088` — affects every Claude Max user today); (c) proactive budget guardrails are absent (`clawmetry#2817`, `clawmetry#2818`, `clawmetry-cloud#1484`). The Headroom token-compression proxy hit 16.8k GitHub stars doing just the measurement side; ClawMetry is the natural owner of "measure + alert + enforce."
- **Linked issues**: `clawmetry-cloud#4`, `clawmetry-cloud#653`, `clawmetry-cloud#655`, `clawmetry-cloud#1088`, `clawmetry-cloud#1484`, `clawmetry#2837`, `clawmetry#2839`, `clawmetry#2817`, `clawmetry#2818`, `clawmetry#3000`
- **Likely scope**: Both — OSS gets proxy guardrails (rate-breaker + cost-spiral breaker) + cache risk surface; cloud gets team chargeback + subscription-mode billing flag
- **Suggested first step**: `clawmetry-cloud#1088` (subscription-mode flag to zero out per-token cost for flat-rate users) is the highest-severity correctness bug for paying users and ships independently in a few hours; then `clawmetry#3000` (per-agent/per-team attribution) to close the chargeback gap

---

### 3. Claude Code as a first-class runtime (not "OpenClaw with a Claude Code skin")

- **Demand**: 7 issues (3 cloud intel/product + 4 OSS automated obs-gaps), 0 explicit reactions, last raised 2026-06-11
- **Representative quotes**:
  - `clawmetry-cloud#649` (AgentPulse Show HN): *"What started out as an observability platform has matured into an orchestration platform as well."* — a competitor shipping Claude Code native observability right now
  - `clawmetry-cloud#703`: ClawMetry currently treats Claude Code as "OpenClaw running Claude Code." The EPIC calls for a separate adapter, dashboard surfaces, and first-run flow native to Claude Code users.
  - `clawmetry#3015`: Claude CLI commentary/progress events produce no span — traces from Claude Code sessions look empty compared to OpenClaw sessions, which makes ClawMetry look broken to new Claude Code users
- **Why it matters**: Claude Code is the fastest-growing runtime in the OpenClaw family. All three recent competitor-intel items (AgentPulse, Faros, Trainly) specifically target Claude Code users, not generic OpenClaw users. A Claude Code user who discovers ClawMetry today lands on an OpenClaw-shaped product with gaps. Shipping EPIC `clawmetry-cloud#703` is a defensive positioning move: own the category before a purpose-built competitor does.
- **Linked issues**: `clawmetry-cloud#703`, `clawmetry-cloud#649`, `clawmetry-cloud#650`, `clawmetry#3015`, `clawmetry#3016`, `clawmetry#2875`, `clawmetry#2861`
- **Likely scope**: Both — OSS gets the adapter obs-gap fixes; cloud gets the Claude Code-specific landing + dashboard surfaces
- **Suggested first step**: The three obs-gap bot-PRs (`clawmetry#3015`, `clawmetry#3016`, `clawmetry#2875`) ship the correctness baseline; then design a Claude Code-specific empty/landing state as the visible differentiator (part of `clawmetry-cloud#703`)

---

## Warm themes (worth tracking)

- **Remote approval gates / Control Plane** (`clawmetry-cloud#2`, `#692`, `#1192`, `clawmetry#1369`): being actively built. Kill/pause shipped, policy replay eval shipped. Full Control Plane (`#1192`) deliberately sequenced after activation P0s land — correct call, just watch the sequencing dependency.
- **Session replay + model-change annotations** (`clawmetry-cloud#320`, `#321`, `#322`): no competing work visible. Warm but unfunded. Compaction markers (`#321`) answer "what happened to my session?" and could be a quick win that differentiates the transcript view.
- **Helicone refugee capture** (`clawmetry-cloud#962`): time-sensitive. Helicone has been in maintenance since 2026-03-03; buyers' guides are already routing away. One importer + Claude prompt-cache analytics panel could convert active refugees. Window is closing — if this isn't built by Q3, the moment is gone.
- **Self-hosted cloud / data residency** (`clawmetry-cloud#1201`): listed in the pricing matrix as "Pro+" but not built. Enterprise buyers block on this. Not urgent for consumer users; high-urgency for any enterprise deal.
- **Proactive narrated notifications** (`clawmetry#1412`): LLM-narrated "what just happened" alerts vs dry threshold fires. No external demand signal, but differentiating once tracing ships.

---

## Closed-loop themes (we shipped this)

- **Agent kill/pause/resume**: addressed in `clawmetry#2996` (merged 2026-06-10) + `clawmetry-cloud#1613` (merged 2026-06-10). Watching for follow-up on policy coverage for family-runtime tool calls.
- **Security posture hardening**: XSS sanitization (`clawmetry#2958`), SSRF guard (`clawmetry#2967`), OTLP auth (`clawmetry#2961`), security_posture encrypted (`clawmetry#2979`), plaintext DB credentials scrubbed (`clawmetry-cloud#1564`). All merged 2026-06-10. **Note**: `clawmetry-cloud#315` (plaintext `api_key` column, P0) is distinct from this batch and still open.
- **One-step onboarding**: `clawmetry#2915` + `clawmetry-cloud#1510` (merged 2026-06-08/09). Trial-by-default also shipped (`clawmetry-cloud#1548`). Watching funnel retention numbers.
- **Per-runtime cost scoping**: fixed in `clawmetry#3029` + `clawmetry-cloud#1618`–`#1622` cluster (merged 2026-06-11). Cost, Context-econ, and Flow tabs now properly scoped per runtime.
- **Approval policy dry-run**: `clawmetry#2980` (merged 2026-06-10) + `clawmetry#2984` (family-runtime tool calls coverage). Policy replay eval is live.

---

## Quiet noise (likely not signal)

- **Automated obs-gap issues** (`clawmetry#2795`, `#2796`, `#2959`, `#2960`, `#2957`, `#3014`, `#3015`, `#3016`): machine-generated observability gap reports. Real gaps, but no external user urgency signal. Bot-PR pipeline is the right handler.
- **clawmetry#503** (Multiple channels display bug, April 2026): real bug, 0 reactions, `needs-info` label — needs reporter follow-up to unblock.
- **Architecture MOAT issues** (`clawmetry#1032`, `#1038`, `#1471`, `#1540`, `#1722`, `#1743`): infrastructure work with no user pull signal. Correct to do, but shouldn't crowd out the HOT themes.

---

## Velocity check

- **Themes shipped to in last 30d**: 5 (kill/resume, security hardening, onboarding, cost-scoping, approval dry-run) out of ~12 active theme areas = **5/12** (split: ~4 OSS-led + ~3 cloud-led, with kill/resume + security spanning both)
- **Total merged PRs in last 30d**: 1,418 OSS + 610 cloud = **2,028 PRs** — high absolute velocity
- **Average issue→PR latency**: bot-generated obs-gap issues resolve in 1–2 days; user-reported issues trail longer (e.g. `clawmetry#503`, open since April 2026 = 70+ days)
- **Themes HOT for 2+ weeks without action**:
  - `clawmetry#1006` / `clawmetry-cloud#703` (Tracing EPIC / Claude Code native observability): open since 2026-05-11 — **32 days**. Sub-issues have bot-PRs in flight but the user-facing trace tree has not shipped.
  - `clawmetry-cloud#1088` (Subscription-mode cost accounting): open since 2026-05-25 — **18 days**. Every Claude Max + ChatGPT-Plus user currently sees wrong cost numbers.

---

## ⚠️ Honest call-out: founder-gut vs user-signal this week

**Voice/desk-device** received the heaviest engineering concentration in both repos this week: 10+ cloud PRs covering EVI bridge, OpenAI Realtime upstream (4x faster), streaming WSS, push-to-talk VAD, Claw voice button on the dashboard, echo guard, OTA firmware, and relay-side mic RMS logging. User-demand signal for voice: **zero open issues, zero reactions, no intel threads in either repo.**

This is either a deliberate bet on a future distribution channel (the desk device as a new product surface) or classic founder-distraction from the hardest, highest-signal work. It is worth naming: the tracing EPIC — which competitors are actively shipping against — has been open 32 days while voice shipped multiple times daily.

Similarly, the **React v2 SPA migration** (`clawmetry#1492` + 16 sub-issues) is a significant ongoing investment with zero external user pressure. The current Flask UI has no user complaints in the issue tracker.

Neither of these investments is wrong. But both consume bandwidth that the HOT themes above are waiting for.

---

## How this list is built

Reads every open `intel-feedback` / `intel-pain` / `bug` / `enhancement` issue across BOTH repos (`vivekchand/clawmetry` and `vivekchand/clawmetry-cloud`), clusters semantically, ranks by reaction count + recency. Cross-references the last 30 days of merged PRs to detect what is already addressed — in either repo. **Corpus this run**: 92 open issues (61 OSS + 31 cloud) + 2,028 merged PRs (1,418 OSS + 610 cloud).

**Label note**: neither repo uses the `intel-feedback` or `intel-pain` GitHub label in practice. Intel issues in `clawmetry-cloud` use title prefixes `[intel/pain]`, `[intel/competitor]`, `[intel/content]` under the `enhancement` label. All 92 issues had 0 GitHub reactions — the public issue tracker is not being used for community thumbs-up gathering; reaction counts are therefore not a ranking signal this week.
