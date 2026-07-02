# UX_AUDIT.md - beginner-friendliness + information architecture

> Companion to `AUDIT.md` (feature-works audit) and `FLYWHEEL.md` (the vision:
> "observability for people who have never used one... if a first-timer with zero
> context can't understand a screen in five seconds, it's not done. Power tools
> demoted and progressively disclosed, never the first thing a beginner sees").
> This file audits whether the dashboard lives up to that, and proposes a
> minimal, two-tier IA. Grounded in the real nav (`dashboard.py` ~12036-12160,
> re-verified against origin/main @ ea77faca on second pass; a first draft was
> built from a stale checkout and missed Agent Graph) and all 30 tab templates;
> no business numbers (public repo).

## The one-line verdict
A first-time user lands on **~27 nav destinations** (9 primary + a "Live trace"
group with **11 sub-items, expanded by default**, whose header itself opens a
12th screen + a 7-item Advanced section), most named in insider vocabulary
(span, topology, turn anatomy, context economics, swimlane, harness, provenance,
waterfall, autonomy score). This is an **expert tool wearing a beginner's
promise.** The fix is not to delete power, it is to **default to a tiny beginner
surface and move the depth behind progressive disclosure** (a collapsed
"Developer" section + session drill-downs + a Settings home).

---

## 1. Beginner-friendliness rating per screen

Rating = who understands it in 5 seconds. 🟢 anyone · 🟡 needs a hint · 🔴 expert only.

| Nav label | Screen | Rating | Why / jargon |
|---|---|---|---|
| Agents | inventory | 🟢 | "Every agent, is it alive, what it costs." Clear. Good beginner home. |
| Live trace (group header) | overview | 🟡 | **The default landing screen has no nav item of its own**: clicking the "Live trace" group label opens `overview`. A beginner cannot find "home" by name; the label describes the group, not the screen. |
| Agent Graph | agents | 🔴 | "Who spawned whom - cross-session agent topology from span data." Topology/span jargon; also currently stuck on "Loading..." (bug, see §5). |
| Flow | flow | 🟡 | "How your messages get answered" is friendly; the rail still assumes channel/gateway/tool mental model. |
| Brain | brain | 🔴 | Name is a metaphor; content is a raw event stream (span, loop detection, "plumbing"). Powerful, not beginner-legible. |
| Models | models | 🟡 | "fallback rate", "model diversity" are analyst terms. |
| LLM Context | context | 🔴 | "context window", "compaction". Pure ML jargon. |
| Tracing | tracing | 🔴 | "span tree", "waterfall", "trace_id". Developer/OTel concept. |
| Turn anatomy | turn-anatomy | 🔴 | "turn", "waterfall", "compaction". Expert timing view. |
| Tool catalog | tool-catalog | 🟡 | "provenance", "p50/p95", "MCP server". Useful but jargony. |
| Context economics | context-economics | 🔴 | "context utilization", "compaction trigger", "overflow". |
| Harness | harness | 🔴 | "harness" means nothing to a newcomer; runtime-specific. |
| Swimlane | swimlane | 🔴 | "swimlane", "race mode". Compare-sessions power tool. |
| Approvals | approvals | 🟢 | Clear + actionable (approve/deny). Keep prominent. |
| Alerts | alerts | 🟢 | "Get notified when something goes wrong." Clear. |
| Cost | usage | 🟢 | "$ today/week/month." The single clearest screen. |
| Dives | dives | 🔴 | Name gives no clue; it is actually "ask questions in plain English" (great feature, terrible label). |
| Session replay (beta) | transcripts | 🟡 | "Conversations across channels" is clear; the label "Session replay" is techy. |
| Crons | crons | 🟡 | "cron" is developer vocabulary; means "scheduled jobs". |
| Memory | memory | 🟡 | Reasonable; "access log" is jargon. |
| Notifications | notifications | 🟢 | Slack/Email/PagerDuty - clear (Pro). |
| Security | security | 🟡 | "posture", "sandbox", "approval audit". |
| Tool Policy | policy | 🟡 | "allowlist", "sandbox". Overlaps Security. |
| Skills | skills | 🟢 | "Shortcuts your agent can use." Clear. |
| Self-Evolve | selfevolve | 🟡 | "How your agent could improve" is clear; the name is buzzy. |
| Version impact | version-impact | 🔴 | "regression detection", "upgrade impact". Analyst view. |
| (hidden) clusters | clusters | 🔴 | "cohort", "similarity". Not in nav. |
| (hidden) history | history | 🟡 | Time-series charts. Not in nav (duplicates Cost trends). |
| (hidden) logs | logs | 🟡 | Raw daemon logs. Not in nav. |
| (hidden) subagents | subagents | 🔴 | "orchestration", "queue lanes", "run ledger". Not in nav. |

**Score: of ~27 nav destinations, ~5 are 🟢 beginner-safe, ~11 are 🟡, ~12 are 🔴 expert-only, and most of the expert ones are surfaced at the top level by default.**

---

## 2. The repetition / overlap problem (asked: "do we repeat with different naming?")

No two screens are byte-identical, but there are **clusters of screens that answer
the same user question in different vocabulary**, which reads as repetition to a
newcomer:

- **"What is my agent doing / what happened?"** is answered SEVEN ways:
  **Overview (as "Live trace"), Flow, Brain, Tracing, Agent Graph, Turn anatomy,
  Swimlane.** Flow (journey rail) and Brain (event stream) are the two live/global
  views; **Tracing, Turn anatomy, Agent Graph, and Swimlane are session/topology
  detail views** that sit in the global nav. Seven "activity" entries in one group
  is the single biggest source of overwhelm. Bonus confusion: Tracing's own
  drill-down ALSO contains an agent graph, so the concept appears twice.
- **The internal ids collide with the labels:** the tab whose id is `agents` is
  labeled **"Agent Graph"**, while the tab labeled **"Agents"** has id
  `inventory`. Same word, two different screens, depending on whether you read
  the code or the UI (also: Cost=`usage`, Session replay=`transcripts`, Tool
  Policy=`policy`, Live trace header=`overview`). Align ids with labels when
  renaming, or drift like this keeps re-emerging.
- **"What is this costing / how are tokens used?"** is answered FOUR ways:
  **Cost, Models, LLM Context, Context economics.** Different angles ($ vs
  by-model vs per-turn-context vs window-utilization), but a beginner sees four
  cost-ish tabs.
- **"What is allowed / how am I notified?"** spans FIVE:
  **Approvals, Alerts, Notifications, Security, Tool Policy** (rule vs gate vs
  routing vs posture vs allowlist). All "guardrails," scattered.
- **Trace-ish naming pile-up:** the group "Live **trace**" contains "**Trac**ing"
  (and Flow) - three trace-flavored names for one idea.
- **Genuine near-duplicate to resolve:** the hidden **history** tab (token/cost
  over time) duplicates the trend charts already on **Cost**. Fold or drop.

---

## 3. Proposed two-tier IA (minimal by default, depth on demand)

### Tier 1 - the beginner home (what shows by default). The 5-second questions.
| Item | Answers | Built from |
|---|---|---|
| **Home** | Is everything OK, at a glance? | overview (today it hides behind the "Live trace" group header - give the landing screen its own named nav item) |
| **Agents** | Is it on? what does it cost? who owns it? | inventory |
| **Activity** (rename **Brain**) | What is it doing right now? | brain (+ Flow as a view toggle inside it) |
| **Cost** | What am I paying? | usage (absorbs Models / Context as sub-sections) |
| **Conversations** (rename **Session replay**) | What did it say / do? | transcripts |
| **Approvals** | Anything waiting on me? | approvals |
| **Alerts** | Tell me when something breaks | alerts (+ Notifications as its "delivery" sub-tab) |

Seven clear items. Every one passes the 5-second test.

### Tier 2 - "Developer" section (one collapsed group, closed by default)
Flow (if not merged), **Tracing, Turn anatomy, Agent Graph, Swimlane** (ideally
these four move to be **tabs inside a session drill-down**, not global nav),
Tool catalog, LLM Context, Context economics, Models (if not absorbed by Cost),
Dives (rename **"Ask"**), Harness, Version impact, clusters, subagents, logs.

### Execution risk register (so the restructure ships safely)
- **Keep `data-tab` ids stable.** Deep links, localStorage state, tests, and the
  capability-derived visibility map (`_CM_RT_CAPS`) key off ids. Rename LABELS
  (i18n `en.json`) freely; change ids only with redirects.
- **Respect existing users' drawer state.** The Live-trace drawer persists
  open/closed in localStorage; flipping the default to collapsed must only apply
  when no stored preference exists, so power users are not disrupted.
- **i18n:** all renames go through `en.json` keys; autotranslate fans out the
  other 35 locales. Never hand-edit non-English locales.
- **Per-runtime tab gating must survive.** Tabs show/hide by the runtime's
  declared Capability enum; moving items between groups must not detach them
  from that derivation.
- **Cloud parity:** the nav ships in the OSS wheel, so the restructure reaches
  app.clawmetry.com only after an OSS release + cloud pin bump. Verify the tab
  switcher e2e on BOTH surfaces before calling it done.
- **Phasing:** Phase A = regroup + rename + collapse (nav-only, low risk).
  Phase B = move the four session-scoped views into the session drill-down
  (real UX work: they need a session-picker context). Do not bundle them.

### Tier 3 - Settings / gear (rarely-touched config + governance)
Crons, Memory, Security, Tool Policy, Skills, Self-Evolve, NemoClaw, and node/account config.

### The biggest single win
**Move the four session-scoped views (Tracing, Turn anatomy, Agent Graph,
Swimlane) out of the global sidebar and into the session detail** a user opens
from Activity/Conversations. They are meaningless without a selected session, so
they should not compete for top-level attention. This alone cuts the sidebar from
~27 to ~13 and removes most of the 🔴 jargon from first contact.

---

## 4. Plain-language rename map (jargon -> human)
| Now | Proposed | Now | Proposed |
|---|---|---|---|
| Brain | Activity | Dives | Ask |
| LLM Context | What the model sees | Session replay | Conversations |
| Context economics | Context usage (under Cost) | Turn anatomy | Turn timing |
| Swimlane | Compare sessions | Harness | Runtime extras |
| Tracing | Traces (dev) | Tool catalog | Tools |
| Agent Graph | Who spawned what | Tool Policy | Tool permissions |
| Crons | Schedules | Self-Evolve | Improvement tips |

Keep OpenClaw-neutral, no em-dashes, plain words (per FLYWHEEL copy rules).

---

## 5. Also found (adjacent)
- **Agent Graph is stuck on "Loading..."** on app.clawmetry.com (founder screenshot 2026-07-02). Likely its own loader, separate from the Cost-tab trend crash fixed in #3453. Tracked for a follow-up fix.
- **4 tabs are in the codebase but unmapped in nav** (clusters, history, logs, subagents): decide surface-or-remove; hidden-but-shipped is dead weight.

## Open items (priority)
1. Ship the Tier-1 beginner sidebar + collapse everything else into a default-closed "Developer" group (biggest perceived-simplicity win, low risk: nav-only).
2. Move the 4 session-scoped views into the session drill-down.
3. Apply the plain-language rename map (i18n `en.json`, autotranslate syncs locales).
4. Fold `history` into Cost; decide on the other 3 unmapped tabs.
5. Fix Agent Graph "Loading...".

_Last updated: 2026-07-02. Grounded in dashboard.py nav + 30 tab templates._
