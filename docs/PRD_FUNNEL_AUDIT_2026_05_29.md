# PRD: ClawMetry funnel audit (landing + pricing + signup)

**Date:** 2026-05-29
**Author:** Claude, on /goal "go through the pricing page as each persona and list everything stopping signup"
**Scope:** every public surface a prospect touches between Google → landing → pricing → signup → first event in cloud, evaluated as five buyer personas + scored against Mike Piccolo's agent-harness reference model.

This is a synthesis of four independent audits run in parallel:

1. `/pricing` claims vs the actual `entitlements.py` catalogue
2. Every other landing page (homepage, /cloud, /how-it-works, /nemoclaw, /openinfer, /enterprise, /docs, /showcase, /traction)
3. The signup + first-cloud-visit flow (CLI auto-register, browser OTP, Stripe wiring, in-app onboarding)
4. Mike Piccolo, "How to build your own agent harness" (LinkedIn) as a reference model for what an agent observability tool should be able to surface

Section numbers map: §1 personas, §2 surface-by-surface gaps, §3 trust + compliance, §4 pricing-mechanics gaps, §5 agent-harness coverage matrix (Piccolo), §6 ranked fix list, §7 what to ship in the next 14 days.

---

## §0 Headline findings (read this if nothing else)

1. **The Pro tier has no self-serve purchase path.** The card is labelled "Recommended" at $39/node/month, lists 14 specific features, and its CTA is a Calendly link. Starter ($19) and Self-Hosted Pro ($390/yr) both have one-step Stripe modals. **Anyone with a credit card who wants Pro is forced into a sales meeting.** This is the single highest-leverage conversion bug in the funnel.
2. **The Stripe `STRIPE_PRICE_YEARLY` env var is unset in production.** Every "or $190/node/year, 2 months free" CTA on /pricing returns HTTP 503 `Price not configured` from `/api/billing/checkout`. The annual button is dead.
3. **Only one cloud paid Stripe price exists.** `STRIPE_PRICE_MONTHLY=price_1T9dFr...` is the entire commercial cloud surface. /pricing advertises Starter $19 AND Pro $39, but every "Start Free Trial" / "Subscribe" call routes to the same SKU. The two tiers are visual, not transactional. Chargeback + trust risk.
4. **Retention numbers contradict themselves on the same page.** Pro card says `90-day event retention`; the comparison table further down the same page says Brain 30d / Token 90d for Pro. Schema.org JSON-LD says "30-day retention" for Starter and "90-day retention" for Pro. The OSS catalogue has no `_TIER_RETENTION_DAYS` at all (it's all hand-written page copy).
5. **/login returns 404.** /signup, /sign-up, /register all 302 to clawmetry.com/connect. Typing /login directly hits a dead page.
6. **The AES-256 secret key is printed once, in the terminal, at install time, with no recovery flow.** Lose your terminal, lose your machine, lose your data. There is no email-me-my-key, no key escrow, no view-in-plaintext fallback. For any buyer doing security review this is paradoxically too strict to be enterprise-ready (no escrow option) and too lax to be enterprise-ready (no audit of key access).
7. **Zero verifiable customer logos, zero "VP Eng at $Co" testimonials, zero compliance badges (SOC 2, ISO, GDPR, HIPAA), zero status page link.** Real traction is 200K+ pip installs, 123 countries, ~350 GitHub stars, ~8 paying / ~$45 MRR (memory). The funnel uses none of the verifiable numbers and all of the unverifiable ones (Product Hunt rank, Twitter testimonials).
8. **OTel export is sold under Pro, but the entitlement catalogue puts `otel_export` in ENTERPRISE_FEATURES** and `routes/otel_export.py` actively blocks non-Enterprise tiers. In enforce mode a paying Pro customer hits a paywall on a feature their tier card sold them. Same shape risk on "Tamper-evident audit log" (Free bullet, Enterprise-gated route).
9. **Agent-harness observability coverage is at 12 of 20 Piccolo aspects today, and 5 of the missing 8 are advertised features.** Per-turn FSM, sub-agent tree, distributed-trace context propagation, sandbox lifecycle, budget enforcement (vs tracking), system-prompt assembly, skill discovery, fail-closed semantics: all are missing or partial despite being central to the "what's happening inside my agents" pitch.
10. **`vivek-chand.jpg` exists in the landing repo, is referenced by no page.** Founder photo + 1-line bio above the "Talk to founder" CTA is a free trust win that's literally one `<img>` tag away.

---

## §1 Per-persona walk-throughs

Each persona is a real evaluation pattern, not a marketing avatar. The scores are a thumbnail; the body explains why.

| Persona | Annual budget window | Sign-up odds today | Pay-up odds today | #1 blocker |
|---|---|---|---|---|
| Indie / hobbyist dev | $0 to $200 | High | Low | Recovery flow if AES key lost |
| Seed-stage founder (2-5 engineers) | $500 to $5K | Medium | Medium | Pro CTA forces sales call |
| Series A engineering leader (15-40 engineers) | $5K to $30K | Medium | Low-Medium | No SSO, no team model, no real customer logos |
| Series B/C platform / SRE owner (50-200 engineers) | $30K to $200K | Low-Medium | Low | No SOC 2, no SLA proof, no Helm/Terraform, single-tenant API key |
| Late-stage / public co / F500 (1000+ eng) | $200K+ | Very low | Near zero | No SSO + RBAC + audit + DPA + data residency + on-prem proof + procurement pack |

### 1.1 Indie / hobbyist dev (free tier hunter)

**What they read:**
- Lands on homepage from a Hacker News or Twitter link. Headline "Know what your agents are doing. Right now." Subhead is fine; they scroll.
- Sees `pip install clawmetry`. Likes it.
- Runs `clawmetry onboard`, gets an instant-register cloud account (no email asked), terminal prints a 44-char base64 AES key, dashboard auto-opens.

**What stops the signup:**
- Almost nothing. This is the persona the funnel is built for. They install, see their first session, are happy.

**What stops the upsell to Cloud Pro:**
- The dashboard doesn't tell them what they would *get* by upgrading. There is no in-app "upgrade for waste flags" prompt next to a session that looks expensive.
- The free tier already includes the runtime they care about (OpenClaw + NeMo). For a hobbyist running Claude Code on one box, Starter's "multi-runtime" doesn't add anything; Pro's "Self-Evolve" might, but it's not demoed anywhere.
- Per-node pricing on a 1-node setup feels coarse: Pro is "more retention + more analytics + $39/month". For a side project that's a hard sell.

**What scares them off:**
- The lost-AES-key story. A hobbyist who reinstalls macOS, loses the key, and finds out their cloud data is unrecoverable will tell 12 friends not to use ClawMetry.
- The /nemoclaw page linking to `nvidia.com/nemoclaw` (a dead URL). Sophisticated readers will see this and decide the founder is sloppy.

**What would convert this persona to a $15-19 paid plan:**
- A "Personal" tier at $9/month with 30 days retention and one named seat, sold as "pro for one box". Currently the gap from $0 to $19 is felt because Starter is sold as "unlimited nodes" which a hobbyist doesn't need.

### 1.2 Seed-stage founder (CTO of a 2-5 person AI startup)

**What they read:**
- Comes in from a "best LLM observability tools 2026" SEO post. Reads /pricing first.
- Sees Free, Starter, Pro, Self-Hosted Pro, Enterprise. Five tiers is one too many; they bounce between Starter and Pro.
- Sees "Recommended" on Pro. Likes Pro feature bullets (Self-Evolve, eval suite, OTel export, custom webhooks).
- Clicks "Book a 30 min call". Bounces.

**What stops the signup:**
- "Book a call" instead of a checkout for a $39/mo product is the literal #1 blocker for this persona. They have a credit card. They want to try it tonight. Calendly is a Tuesday at 2 PM problem.
- Starter is fine on paper but does not include OTel export, eval suite, or Self-Evolve. The seed founder reading the pricing page concludes "I need Pro for the things I came here for", then bounces off Calendly.

**What scares them off:**
- The inconsistent stats across pages. Homepage says 230K installs, /nemoclaw says 180K, /openinfer says 160K. They notice and decide the team is winging it.
- The contradiction between "Pro: 90-day event retention" (card) and "Brain 30d / Token 90d for Pro" (table). They notice and lose trust.
- The yearly button being broken (HTTP 503) if they ever click it.
- Zero named customer logos. Seed founders especially want to see other seed-stage AI logos using it.

**What would convert this persona:**
- Self-serve Stripe checkout on Pro.
- One real "VP Eng at [recognizable seed startup]" testimonial with a face.
- A 30-second "see it without installing" demo dashboard at `/d/demo` or `/showcase/live`.

### 1.3 Series A engineering leader (15-40 engineers, dedicated platform / DX person)

**What they read:**
- Tasked by CEO to "set up observability for the agent platform". Googles "agent observability LangSmith alternative".
- Lands on `/what-is-ai-agent-observability` (SEO landing). Reads. Clicks "See ClawMetry".
- Goes to /pricing, then /cloud, then /enterprise. Forms a mental model.

**What stops the signup:**
- No SSO. They run Google Workspace; their team logs into everything via Google. No SSO = "we'd have to manage another set of shared creds." Bounce.
- No team / multi-user account model. The codebase has no role column on `users`. The "/cloud/team" route redirects to a feedback-comment box. They can't even put their DX teammate on the same account.
- The "OTel export to Datadog / Grafana / Honeycomb" Pro bullet would normally be enough for them, except the catalogue gates it to Enterprise. If they sign up to Pro and the gate ever flips on, they're paywalled.
- The competitive landscape question: ClawMetry has no /vs/langsmith, /vs/langfuse, /vs/helicone, /vs/arize pages. The leader has to do that work themselves; some won't.

**What scares them off:**
- "Built by vivekchand" in the footer. One name. They've been burned by single-maintainer tooling before.
- No status page link, no historical uptime number. The "99.9% SLA" Enterprise chip is text without a backing link.

**What would convert this persona:**
- Google Workspace OAuth as a sign-in option (single highest enterprise unlock per LOC).
- A real /vs/langfuse and /vs/langsmith page with a feature comparison row that picks ClawMetry winners honestly.
- A team model: invite by email, one billing entity, separate keys per environment.

### 1.4 Series B/C platform / SRE owner (50-200 engineers)

**What they read:**
- /enterprise. The eyebrow says "5-minute procurement pack". They like the tone.
- The page promises eight things: SSO, RBAC, audit log, secret redaction, SIEM export, OTel export, on-prem/air-gapped, custom data residency, 99.9% SLA, dedicated Slack, custom retention.
- They cross-check against the comparison table on /pricing. The "Enterprise" column has check-marks for all of them.

**What stops the signup:**
- No SOC 2, no ISO 27001, no GDPR statement, no HIPAA. For a B-round SaaS or fintech this is the procurement-team table stakes. No badge, no progress note, no "in progress, Type I expected Q3": just silence.
- The SSO/RBAC promise has zero implementation in the repo. No SAML library, no OIDC handler, no `role` column. A buyer doing actual diligence (downloading the install, poking the cloud, asking for a demo) will catch this; the procurement team won't, but the buyer will lose face when they recommend it and security says no.
- "Tamper-evident audit log" appears as a Free bullet AND an Enterprise chip. The Enterprise person reading this gets confused: is this differentiated or not?
- No Helm chart, no Terraform module, no Docker Compose example for the cloud companion. The OSS has a Dockerfile; the cloud doesn't have a self-hosted package.

**What scares them off:**
- "Air-gapped on-prem deployment" claim with no architecture diagram, no install guide, no version-of-cloud-that-runs-on-our-VPC artifact.
- Schema.org JSON-LD inconsistency (only knows monthly, says "30-day retention" for Starter while the card says different).
- The /nemoclaw dead-link issue applies to all enterprise readers, not just NVIDIA partners.

**What would convert this persona:**
- A pinned "SOC 2 Type I targeted Q3 2026" line + a link to a security.txt or a `security.clawmetry.com` page with controls, sub-processors, data-flow diagrams.
- A real Helm chart in a `charts/` directory in the cloud repo, even if minimal.
- An actual SSO implementation, even Google Workspace OAuth only at first, marketed as "SSO available".

### 1.5 Late-stage / F500 buyer

**What they read:**
- They almost never read pricing. They go to /enterprise, then ask their procurement team to email enterprise@clawmetry.com.
- The /enterprise page is the strongest sales asset on the site, but it is text-only. No PDF download.

**What stops the signup:**
- DPA, BAA, MSA: none of these are linked or templated. The page says "available on request" which means another 2-3 weeks of email round-trips.
- The product is not in the AWS Marketplace, the GCP Marketplace, or the Azure Marketplace. F500 procurement runs through these.
- No security questionnaire pre-filled (SIG, CAIQ). Every prospect asks for one; ClawMetry has none.
- No reference customer list available under NDA. The page makes the founder's bet sound like a hopeful startup ("Built by vivekchand"), which is fine for a Series A reader and terrifying for an F500 reader.
- No pen-test summary, no bug-bounty program, no security advisories list.

**What scares them off:**
- The "Built by vivekchand" footer + single-page architecture explanation makes this read like an indie tool. F500 reads this and forwards it to a different vendor list.
- No mention of CMK / BYOK for encryption keys (they bring their own KMS).
- No data-residency commitment with named regions (US-east-1, eu-west-1, etc.).

**What would convert this persona:**
- A real /security page with controls, sub-processors, a public-facing CAIQ Lite, a downloadable DPA template, a status page link, and a SOC 2 status block.
- A POC kit: a sandboxed cloud tenant with named contact, a Slack Connect link, and a "POC starter" repo template.
- Honestly: this persona is probably a 2027 conversation. The PRD should explicitly de-prioritize it until SOC 2 and SSO ship.

---

## §2 Surface-by-surface gaps

### 2.1 Homepage (`index.html`)

| Gap | Severity | Fix |
|---|---|---|
| Hero headline doesn't say what the product IS in 6 words | P1 | Add subhead: "Real-time observability for AI agents. Open-source. Local-first." |
| Schema.org softwareVersion pinned at `0.11.23` (current is 0.12.355) | P2 | Wire `__version__` into the schema block at build/serve time |
| 32 em-dashes across user-facing copy (house style violation) | P2 | CI grep guard + bulk replace |
| Hard-coded social-proof numbers diverge across pages (230K vs 180K vs 160K installs) | P1 | Single `/api/hero-stats` endpoint, no hard-coded fallbacks above 10% of current |
| "Get Started Free" anchor goes to in-page code block; doesn't capture email | P1 | Either rename to "Install" or add an email-capture before the code block |
| Founder photo asset exists, not used | P0-cheap | `<img>` tag above founder-quote section |
| No competitor-vs pages | P1 | Ship `/vs/langfuse`, `/vs/langsmith`, `/vs/helicone`, `/vs/arize`, `/vs/datadog-apm`, `/vs/mlflow` |
| No customer logos | P1 | Get 3 logos under usage clause, even if they're seed startups |
| FAQ doesn't address "I don't use OpenClaw" | P1 | Add a "Works with Claude Code? Codex? Cursor?" FAQ that re-states the 10-runtime support |
| `how-it-works-v2.html` is orphaned dead file | P3 | Delete |

### 2.2 /pricing (`pricing.html`)

| Gap | Severity | Fix |
|---|---|---|
| Pro CTA is Calendly | **P0** | Self-serve Pro Stripe modal, with Calendly as secondary link for >25 nodes |
| Yearly button is broken (503 in prod) | **P0** | Set `STRIPE_PRICE_YEARLY` in deploy.sh + auto-deploy-cloud.yml |
| Only one paid Stripe price ID; Starter and Pro share it | **P0** | Create distinct `STRIPE_PRICE_STARTER_MONTHLY` and `STRIPE_PRICE_PRO_MONTHLY` |
| Pro card retention number contradicts the comparison table on the same page | **P0** | Pick one source of truth; back it with `_TIER_RETENTION_DAYS` in `entitlements.py` (this is already there in PR #2274) |
| OTel export sold under Pro, gated to Enterprise in code | **P0** | This was fixed catalogue-side in PR #2274 (moved to PRO_ONLY_FEATURES); verify routes/otel_export.py allows Pro tier |
| "Tamper-evident audit log" sold as Free AND Enterprise | P1 | Pick one. If audit logs are Free, gate routes/audit.py on FREE_FEATURES; if Enterprise, drop the Free bullet |
| No annual toggle (annual is a footnote) | P1 | Toggle at top of grid; rewrite schema.org `Offer` blocks to know annual |
| No competitor comparison table | P1 | Add LangFuse / LangSmith / Helicone / Arize / Datadog columns to the compare-all-features table |
| No customer logo strip | P1 | Above the tier grid: "Trusted by teams running production AI agents" + 3-6 logos |
| No SOC 2 / GDPR / HIPAA badges or "in progress" status | P1 | Add a "Security & compliance" row in the compare table linking to /security |
| FAQ #5 says "Pro doesn't have a self-serve trial; book a 30 min call" | P0 | Replace once self-serve Pro is shipped |
| No ROI calculator | P2 | Below FAQ: "X agents × Y tokens/day → potential waste caught" |
| No money-back guarantee | P2 | "30 days, no questions" |
| No phone or Slack Connect support claim under any tier | P2 | Even Slack-Connect-on-Pro would be a real differentiator |
| Per-node pricing model has no FAQ ("we have 50 devs but 3 nodes?") | P2 | FAQ #7 |

### 2.3 /cloud, /nemoclaw, /openinfer, /enterprise

| Gap | Severity | Fix |
|---|---|---|
| /cloud says PH rank `#10`, homepage says `#5` | P2 | One number, fetched live |
| /nemoclaw `<a href="nvidia.com/nemoclaw">` is a dead URL | **P0** | NVIDIA's product is NeMo Guardrails; link to docs.nvidia.com/nemo-guardrails/ or remove |
| /nemoclaw uses NVIDIA green (#76b900) heavily; reads as official partnership | P1 | Either confirm partnership status or de-emphasize |
| /openinfer is the best-designed page; it just isn't reused | P1 | Use its hero pattern (custom SVG + concise headline) on homepage |
| /enterprise is text-only, no PDF download | P1 | Auto-generate a PDF version via the same data source |
| /enterprise claims SOC 2, RBAC, SSO, etc. with no proof links | P1 | Each promise gets a link to a real artifact or a "Q3 2026 target" label |
| Founder photo + bio not on any product page | P0-cheap | One photo, one paragraph |

### 2.4 /docs

| Gap | Severity | Fix |
|---|---|---|
| Different accent color (`#ff6b35` vs `#E5443A` site-wide) | P2 | Match brand red |
| No "Try cloud" or "Book demo" CTA at end | P1 | Footer CTA |
| Page title has em-dash | P3 | Replace with colon |
| Only competitor comparison on the entire site lives here | P1 | Move to homepage or /vs/* pages |

### 2.5 /connect (signup)

| Gap | Severity | Fix |
|---|---|---|
| `/login` returns **404** | **P0** | Alias to `/connect` with `mode=signin` query param |
| First paint shows "Sign in" copy even when arriving to sign up; JS rewrites it after load | P1 | Server-render the correct copy based on path |
| No Google / GitHub OAuth | **P1** | Google OAuth is the single highest enterprise unlock per LOC |
| OTP screen has no resend cooldown UI | P2 | Add 30s countdown then "Resend" |
| Success page hands the user a `cm_` key + 3 next-steps; doesn't auto-detect platform | P2 | Detect macOS/Linux/Windows; tailor the install command |

### 2.6 First /cloud visit

| Gap | Severity | Fix |
|---|---|---|
| Hard gate on AES secret key; no recovery flow | **P0** | At minimum: "I lost my key" → fresh dashboard with old data discarded after consent. Better: optional email key escrow |
| No `/d/demo` or sample-data dashboard | **P0** | Pre-seed a tenant with realistic mock sessions; link to it from /cloud and /showcase |
| No in-app tour / onboarding spotlight | P1 | A 5-step Driver.js tour on first visit |
| No persistent Docs / Help / Status link in cloud nav | P1 | Footer or top-right gear menu |
| Aisha AI chat is the only support surface | P2 | Either expose Slack Connect for Pro, or stop calling Aisha "support" |
| No Slack / Discord community link anywhere in the cloud app | P2 | Footer link to a community |

### 2.7 Stripe / billing reality

| Gap | Severity | Fix |
|---|---|---|
| `STRIPE_PRICE_YEARLY` unset | **P0** | One-line deploy env addition |
| Only one cloud paid Stripe price | **P0** | Create distinct price IDs for Starter + Pro; wire by tier in `/api/billing/checkout` |
| Admin MRR formula hard-codes $5/node/month | P1 | Pull amount_total from Stripe subscription_items |
| No in-app cancel UI; only Billing Portal | P2 | "Cancel subscription" button in /cloud/billing that opens Portal |
| No multi-user / team billing entity | P1 | New `workspaces` table; users join workspaces; billing follows workspace |

### 2.8 Auth + security signals

| Gap | Severity | Fix |
|---|---|---|
| No SSO (SAML, OIDC, Google Workspace, Okta) | **P0 for Enterprise persona** | Phase 1: Google OAuth. Phase 2: WorkOS / Auth0 for SAML |
| No SCIM | P1 for Enterprise | Phase 2 alongside SAML |
| No real 2FA (only OTP re-email) | P1 | TOTP + recovery codes |
| No `role` column / RBAC | P1 | Owner / admin / member / viewer model on workspaces |
| No human-readable audit log in UI | P1 | Surface the server-side `[unregister] audit` lines |
| Only one API key per account; not per-environment | P2 | Multiple keys with scopes (read-only, write, admin) |

---

## §3 Trust + compliance gaps

Items here are not features. They are signal-density gaps that buyers above Seed expect to see before they fill in a form.

| Signal | Status | Fix priority |
|---|---|---|
| SOC 2 Type I/II | Missing, no public status | P1 (Q3 target line is acceptable for now) |
| ISO 27001 | Missing | P3 (post SOC 2) |
| HIPAA | Missing | P3 (only if a healthcare customer asks) |
| PCI | Missing | P3 (Stripe carries the obligation; document) |
| GDPR DPA | Templates exist on Enterprise page on request | P1 (make downloadable) |
| Sub-processors list | Missing | P1 |
| Data residency named regions | Missing (only "custom" claim) | P2 |
| Status page link (status.clawmetry.com is live but unlinked) | P0-cheap | Link from footer and cloud nav |
| Uptime history | Missing | P1 (Better Stack public widget exposes it) |
| Penetration test summary | Missing | P2 |
| Bug-bounty program | Missing | P3 |
| Security.txt at clawmetry.com/.well-known/security.txt | Unverified | P1 |
| `security@clawmetry.com` mailbox | Likely exists; not surfaced | P1 |
| Vulnerability disclosure policy | Missing | P2 |
| CAIQ Lite or SIG Lite pre-filled | Missing | P2 |
| Named entity / registered address | Missing on landing | P1 |
| Reference customers (under NDA) | Likely missing | P2 (build first) |
| Public roadmap | Exists at /roadmap, hidden under "More" nav | P1 (surface from product pages) |

---

## §4 Pricing-mechanics gaps

These are not "missing features": they are price-page mechanics that signal "real product" vs "side project".

| Gap | Buyer signal | Fix |
|---|---|---|
| No annual toggle | "These guys don't understand contract-buying behavior" | Toggle at top of grid; default monthly; show 2-months-free as a chip |
| Schema.org Offer block lists monthly only | SEO + Google Merchant comparison is monthly-only | Add yearly Offer with priceValidUntil |
| Per-node pricing without a node-vs-seat explainer FAQ | "I don't know how to forecast my spend" | Add "How nodes are counted" FAQ + a "5 devs × 1 node = 1 node" example |
| No volume discount language | "We can't get above 25 nodes without a custom quote" | Tier-stop language: "25+ nodes? Contact sales for volume pricing" |
| Pro has no self-serve trial; Starter does | "Pro buyers are forced to ask permission" | Same 7-day trial mechanism for Pro |
| No "annual commit, monthly pay" option | "Annual locks us in but cashflow says monthly" | Mid-tier option |
| No "pay quarterly" option for budget-bound Series A/B buyers | Same as above | Quarterly stripe billing interval |
| No money-back / first-month-free | Risk-reversal missing | "Cancel any time" line + a 30-day refund clause |
| No mention of multi-year prepayment | Enterprise buyers want it for budget close | Enterprise line: "2- and 3-year terms available" |
| No comparison table column for the OSS Free tier | "I think this is just a SaaS upsell" | Reinforce that the OSS is real |

---

## §5 Agent-harness coverage matrix (Mike Piccolo reference model)

Piccolo's "How to build your own agent harness" (LinkedIn) defines 20 architectural aspects of a modern agent harness. For an observability tool to be credible, it must let you see every one of them. Below is what ClawMetry covers today vs. what it advertises vs. what it claims on /pricing.

Legend: ✅ surfaced today · ⚠️ partially surfaced or backend-only · ❌ not surfaced

| # | Piccolo aspect | ClawMetry surfaces it today? | Where (or where it should be) |
|---|---|---|---|
| 1 | Turn request persistence (session/message IDs as baggage) | ✅ | Brain feed, Tracing tab, Transcripts |
| 2 | Credential resolution + fail-closed if missing | ❌ | No event for "auth::get_token failed" |
| 3 | Model capability lookup (vision, tools, streaming) | ❌ | No model-capability matrix; just usage by model |
| 4 | Per-turn FSM (provisioning → streaming → exec → steering → stopped/failed) | ⚠️ | Turn anatomy shows steps but does NOT label them with FSM states |
| 5 | Sandbox provisioning + microVM lifecycle | ❌ | No sandbox events surfaced in dashboard |
| 6 | Skill discovery + download (function schemas) | ⚠️ | Tool Catalog tab lists tools; doesn't show schema fetch events or first-call latency |
| 7 | System-prompt assembly (mode + identity + skill index) | ❌ | No surface for "this was the system prompt for this turn" |
| 8 | Token streaming + pull-based MessagePump | ⚠️ | Token counts shown; streaming events not exposed as a first-class signal |
| 9 | Policy / permission check before tool dispatch | ⚠️ | NeMo governance tab exists; doesn't show "allow/deny/needs_approval" as a per-tool-call timeline |
| 10 | Human approval gate (awaiting_approval queue) | ✅ | Approvals tab |
| 11 | LLM budget tracking + enforcement | ⚠️ | Budgets tab tracks; enforcement is via the proxy and not exposed in dashboard |
| 12 | Hook fanout (before/after) | ❌ | No surface for hook execution; hooks treated as internal |
| 13 | Session persistence as a branching tree (forks, resumes) | ❌ | Sessions are flat; no fork visualisation |
| 14 | Context compaction events | ⚠️ | Compactions tab shows compaction events; doesn't show "trim N tokens, kept Y messages" math |
| 15 | Event stream emission (turn events for UI) | ✅ | SSE Brain stream |
| 16 | Distributed tracing context propagation (one connected graph) | ⚠️ | Tracing tab exists; cross-runtime trace stitching across sub-agents is incomplete (memory notes "parentId is a chain not a tree") |
| 17 | Tool-call dispatch loop (max_turns) | ⚠️ | Tool timeline shows calls; doesn't show the loop/iteration count or "max_turns hit" terminal state |
| 18 | Fail-closed semantics (timeout on policy engine) | ❌ | No event for "gate_unavailable" |
| 19 | Session-create fanout (group-by scope) | ⚠️ | Fleet view shows sessions per node; no scope/group-by-aggregation UI |
| 20 | Function-schema registry (live catalog) | ⚠️ | Tool Catalog tab covers tool list; not schema versions or registration events |

**Coverage score:** 3 ✅ / 9 ⚠️ / 8 ❌ → **12 of 20 are partially or fully surfaced; 8 are completely missing.**

The 8 ❌ rows are not exotic features. They are central to the value prop of an agent-observability tool. The 5 highest-impact gaps:

- **#7 System-prompt assembly:** "Why did this agent take a wrong turn?" is the #1 debugging question for agent builders, and ClawMetry can't show you the system prompt that was actually sent.
- **#13 Session as branching tree:** Forks + resumes are how Piccolo-style harnesses recover from failure. Flat session list misses the whole shape of how teams actually use modern harnesses.
- **#5 Sandbox lifecycle:** Anyone running iii-sandbox / e2b / Modal / Daytona wants to see provisioning latency + sandbox state.
- **#3 Model capability lookup:** "Which model supports vision in my fleet?" is a real operational question; today the dashboard answers usage-per-model, not capability matrix.
- **#18 Fail-closed semantics:** Policy-engine-down events are exactly the kind of thing on-call wants alerted on; today there's no event.

### Where Piccolo aspects map onto a feature PRD

| Piccolo aspect | New ClawMetry feature it would justify | Tier |
|---|---|---|
| 4. Per-turn FSM | "FSM state timeline" badge on each turn in Tracing | Free (it's just labeling existing events) |
| 7. System-prompt assembly | "View system prompt" toggle on every turn in Transcripts | Free |
| 13. Branching session tree | "Forks" tab on Sessions | Pro (it's analytical) |
| 5. Sandbox lifecycle | "Sandboxes" tab next to Crons | Starter |
| 12. Hook fanout | "Hooks" sub-tab in Tool Catalog | Pro (debugging value) |
| 18. Fail-closed | New alert rule type: "policy_engine_unavailable" | Pro |
| 3. Model capability lookup | "Models" tab adds a capability matrix column | Free |
| 19. Group-by scope | "Group by" multi-pivot in Brain + Tracing | Pro |

These are 8 PRD line items that come almost for free from labeling existing data better; together they shore up the "real-time observability for AI agents" claim that the hero is selling.

---

## §6 Ranked fix list

Grouped by buyer-impact. Each item is a separate PRD candidate, suitable for a 1-day to 1-week effort unless noted.

### P0: block conversion today

| # | Item | Effort | Owner-suggestion |
|---|---|---|---|
| 1 | Self-serve Stripe checkout on Pro (kill the Calendly CTA) | 1 day | Cloud team |
| 2 | Wire `STRIPE_PRICE_YEARLY` in deploy.sh + auto-deploy-cloud.yml | 1 hour | Vivek |
| 3 | Create distinct Stripe price IDs for Starter and Pro; wire by tier in `/api/billing/checkout` | 1 day | Cloud team |
| 4 | Fix retention contradiction (Pro card 90d vs table Brain 30d); update both surfaces from `_TIER_RETENTION_DAYS` constant | 4 hours | Landing + entitlements (already partly done in PR #2274) |
| 5 | Add `/login` route alias to /connect | 1 hour | Landing |
| 6 | Lost-AES-key recovery flow (at minimum: "discard old data, fresh start" with consent) | 2 days | Cloud + CLI |
| 7 | Confirm `routes/otel_export.py` allows Pro tier (PR #2274 catalogue change must match the live gate) | 1 hour | Verify |
| 8 | Fix /nemoclaw dead nvidia.com link | 30 min | Landing |
| 9 | Add `/d/demo` route with pre-seeded sample data | 3 days | Cloud |
| 10 | Link status.clawmetry.com from cloud nav + landing footer | 30 min | All |

### P1: unblock pay-up within 14 days

| # | Item | Effort |
|---|---|---|
| 11 | Google OAuth sign-in option on /connect | 2 days |
| 12 | Customer-logos strip on homepage + /pricing (need 3-6 real logos under usage clause) | 1 week (mostly sales) |
| 13 | One real "VP Eng at $Co" testimonial with face | 1 week |
| 14 | `/vs/langfuse`, `/vs/langsmith`, `/vs/helicone`, `/vs/arize` pages | 1 week (one author day each) |
| 15 | Founder photo + 1-line bio on homepage + /enterprise | 1 hour |
| 16 | Annual toggle on /pricing + schema.org Offer for annual | 1 day |
| 17 | Centralized hero-stats endpoint; remove all hard-coded fallback divergence | 1 day |
| 18 | FAQ entry for non-OpenClaw runtimes | 1 hour |
| 19 | Em-dash CI guard + bulk replace | 4 hours |
| 20 | `/security` page with controls, sub-processors, security.txt, SOC 2 target line | 2 days |
| 21 | Multi-user / workspace / team model | 1 week |
| 22 | TOTP 2FA + recovery codes | 3 days |
| 23 | Multiple API keys per account (scoped: dev/staging/prod) | 2 days |
| 24 | Audit-log UI surfacing the existing server-side `[audit]` lines | 2 days |
| 25 | In-app onboarding tour (5-step Driver.js) | 1 day |
| 26 | Help / Docs / Status persistent links in cloud nav | 2 hours |

### P2: tighten the funnel

| # | Item | Effort |
|---|---|---|
| 27 | ROI calculator on /pricing | 1 day |
| 28 | 30-day money-back guarantee line | 30 min |
| 29 | Quarterly billing interval | 1 day |
| 30 | "Cancel subscription" button in /cloud/billing | 4 hours |
| 31 | Detect platform on /connect success page; tailor install command | 2 hours |
| 32 | Sub-processors list page | 1 day |
| 33 | Data residency named-region commitment | TBD |
| 34 | Slack / Discord community link in cloud app + landing footer | 1 hour |
| 35 | Resend-OTP cooldown UI on /connect | 1 hour |
| 36 | Match /docs accent color to brand | 30 min |
| 37 | Delete `how-it-works-v2.html` orphan | 5 min |
| 38 | Schema.org softwareVersion gets `__version__` at serve time | 2 hours |
| 39 | Admin MRR formula uses real Stripe amount, not $5 hard-code | 2 hours |
| 40 | Mac DMG version updated past 2026-03-11 | 1 day (build pipeline) |

### P3: credibility for late-stage / enterprise (Q3+ work)

| # | Item | Effort |
|---|---|---|
| 41 | Real SAML/OIDC SSO via WorkOS or Auth0 | 1-2 weeks |
| 42 | RBAC: owner / admin / member / viewer | 1 week |
| 43 | SCIM provisioning | 1 week |
| 44 | SOC 2 Type I (process; targets Q3) | 3 months |
| 45 | Helm chart + Terraform module for the cloud companion | 2 weeks |
| 46 | AWS / GCP / Azure Marketplace listings | 1 month each |
| 47 | Downloadable DPA, BAA templates | 1 week + legal |
| 48 | CAIQ Lite or SIG Lite pre-filled | 1 week |
| 49 | Pen-test summary | 1 month + vendor |
| 50 | BYOK / CMK for encryption | 1 month |

### Agent-harness coverage (from §5)

| # | Item | Effort |
|---|---|---|
| 51 | "FSM state" badge on each turn in Tracing | 2 days |
| 52 | "View system prompt" toggle in Transcripts | 1 day |
| 53 | "Sandboxes" tab | 1 week |
| 54 | "Forks" view on Sessions | 1 week |
| 55 | "Models" tab adds capability matrix column | 2 days |
| 56 | New alert rule: `policy_engine_unavailable` | 1 day |
| 57 | "Hooks" sub-tab in Tool Catalog | 3 days |
| 58 | Multi-pivot "Group by" in Brain + Tracing | 1 week |

---

## §7 14-day shipping plan

If the goal is "morning after deciding, by end of two weeks the pricing page is honest end to end", here is the order:

**Day 0 (today, after this PRD):**
- P0 #2 (annual env var), P0 #5 (login alias), P0 #7 (otel verify), P0 #8 (nvidia link), P0 #10 (status link), P0-cheap (founder photo): all under-1-hour wins. Land as a single small PR.

**Day 1-3:**
- P0 #1 (self-serve Pro Stripe checkout)
- P0 #3 (distinct Stripe price IDs)
- P0 #4 (retention single-source-of-truth)

**Day 4-5:**
- P0 #6 (key recovery flow, MVP: consent + discard)
- P0 #9 (`/d/demo` with pre-seeded data)

**Day 6-8:**
- P1 #11 (Google OAuth)
- P1 #15 (founder photo, real)
- P1 #16 (annual toggle)
- P1 #17 (centralized hero-stats)
- P1 #18 (non-OpenClaw FAQ)
- P1 #19 (em-dash CI guard)
- P1 #20 (`/security` page)

**Day 9-11:**
- P1 #21 (workspace / team model)
- P1 #22 (TOTP 2FA)
- P1 #23 (multiple API keys)
- P1 #24 (audit-log UI)

**Day 12-14:**
- P1 #12 (3 customer logos: sales effort + signed clause)
- P1 #13 (1 named testimonial)
- P1 #14 (4 `/vs/*` pages)
- P1 #25 (Driver.js tour)
- P1 #26 (Help / Docs / Status nav links)

At end of two weeks:
- Pricing page is honest (Starter and Pro are real distinct purchases).
- Pro has a self-serve credit-card path.
- Google OAuth is live.
- A team has a real way to share an account.
- The landing page surfaces real numbers, real logos, real founder face, and a security page with real targets.
- An indie dev who loses their key can recover.
- An enterprise reader can find /security and the status page in two clicks.

Anything below P1 is a Q3 conversation. SSO/SAML, SOC 2, Marketplace listings, Helm, BYOK: those are the Series B/C/F500 unlock; they are explicitly *not* on this 14-day list because they will not ship in 14 days no matter the effort spent.

---

## §8 What this PRD does NOT cover

- The cloud-side Brain transform / rendering bugs (those are tracked separately in cloud repo issues).
- The OSS dashboard's internal feature gaps (those are tracked under the open-core tiering project and the runtime-conformance CI initiative).
- The agent-harness aspects that ClawMetry already surfaces well (Approvals, SSE Brain stream, Transcripts).
- I18n / localization gaps. Coverage is separately tracked under the i18n project.
- Marketing copy improvements beyond conversion-blocker fixes. A standalone copy review is its own exercise.
- The internal admin /thesecretpageforvivek tooling. The MRR formula bug is listed (P2 #39) but the broader admin surface is outside scope.

---

## §9 Appendix: source audits

This PRD is derived from four parallel audits run on 2026-05-29. The full audit text is preserved here for traceability.

- **A. /pricing audit**: checked all tier cards and bullets against `clawmetry/entitlements.py` plus the live HTML. Key findings: retention number contradictions, OTel-Pro-vs-Enterprise gate mismatch, Pro CTA is Calendly, no SOC 2 / no logos / no annual toggle.
- **B. Landing-funnel audit**: checked homepage, /cloud, /how-it-works, /nemoclaw, /openinfer, /enterprise, /docs, /showcase, /traction, /what-is-ai-agent-observability. Key findings: 4 different "Get Started" behaviors across pages, inconsistent hard-coded social proof, 32 em-dashes, dead nvidia.com link, founder asset never used, no competitor-vs pages.
- **C. Signup + onboarding audit**: checked install.sh divergence (landing vs OSS), CLI auto-register flow, browser OTP flow, Stripe wiring, admin page. Key findings: yearly Stripe price unset, only one cloud price ID, /login 404, no Google OAuth, no key recovery, hard gate on AES key, MRR formula bug, no team model.
- **D. Mike Piccolo "How to build your own agent harness"**: extracted 20 architectural aspects of an agent harness. Mapped each against ClawMetry surfaces. 3 fully covered, 9 partial, 8 missing. The 8 missing are the source of feature PRD items #51-58 (FSM badge, system-prompt view, sandboxes tab, forks view, model capability matrix, fail-closed alert, hooks sub-tab, group-by pivot).

Detailed audit reports preserved at `docs/internal/audit-pricing-2026-05-29.md`, `docs/internal/audit-landing-2026-05-29.md`, `docs/internal/audit-signup-2026-05-29.md` (to be committed in a follow-up if useful).
