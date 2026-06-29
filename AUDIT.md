# AUDIT.md - ClawMetry (OSS) feature-promise audit

> Living tracker for "does every promised feature actually work, end to end?"
> Pair with `FLYWHEEL.md` (the "done" bar: merged → released → deployed → **verified live by me, with evidence**).
> Public repo: feature status only, **no pricing/MRR/funnel** (those live in `clawmetry-cloud/AUDIT.md`).

## How to use this file
- Every promised, user-facing capability gets a row with an honest **Status**.
- **Status legend:**
  - ✅ **Verified** - confirmed working end to end this cycle, with evidence noted.
  - 🟡 **Needs verification** - believed working but not re-confirmed live this cycle.
  - 🔴 **Broken / gap** - confirmed not working, or promised but not real (link the issue).
  - 🛠️ **Fixed (pending verify-live)** - fix merged/landed; awaiting production verification.
  - 🚧 **Preview / partial** - ships but plan-gated, OTA-later, or incomplete; copy must say so.
- When you verify a row, replace the Status + add the date and the evidence (snapshot decrypt / screenshot / device photo).
- A 🔴 that is user-facing is a conversion bug (the hosted trial IS the product) - fix or honestly degrade, never leave a silent blank.

## Audit method (the only valid "pass")
1. Walk the trial path: hosted dashboard as a trial user, switch runtimes, click the tab → zero blank/wrong/error states + clean console.
2. For data/observability features: send a **real** message/turn and watch it travel channel → daemon → DuckDB → handler → rendered tab → (cloud) snapshot.
3. Verify across **all 12 runtimes**, not just OpenClaw (`/api/runtimes`).
4. For device-facing slices: the 4-repo chain (pro adapter → OSS `_build_device_summary` → cloud wheel/relay → firmware render).

---

## A. Onboarding & cloud connect

| # | Promised capability | Status | Notes / evidence |
|---|---|---|---|
| A1 | `pip install clawmetry && clawmetry` zero-config local dashboard | 🟡 | Re-verify clean-machine install boots dashboard + sync. |
| A2 | "Enable Cloud Sync" modal: **one-click GitHub/Google sign-up** | 🛠️ | **Fixed in PR #3375** (this branch). Was email-only despite cloud OAuth being live. Reuses the `clawmetry connect` loopback bridge; registers node + starts sync. Verified: served HTML/JS + routes + browser screenshot + tests. **TODO:** verify-live a real Google/GitHub round-trip connects a node. |
| A2b | **Connect must clear the local-only `nocloud` marker** | 🛠️ | **Real burn 2026-06-28 (founder):** a local-only install writes `~/.clawmetry/nocloud` → `is_cloud_disabled()` True → the daemon runs LOCAL-ONLY and **never pushes**, so "Enable Cloud Sync" silently did nothing and cloud showed 0 nodes despite a healthy syncing daemon. **Fixed in PR #3375:** new `config.enable_cloud()` clears the marker, called from `_full_connect_with_key` + both `cmd_connect` paths, which now also **restart** the daemon (not just "start if absent") so it re-evaluates cloud mode. Founder's node remediated live (marker removed + reconnected → 1 node visible). |
| A2c | Account/key alignment on connect | 🟡 | Same burn: the node synced under a different account key (`cm_c9af6`) than the browser session (`cm_f6a68e`), so the fleet showed 0 nodes. Re-connect aligns them, but consider surfacing "this node is on account X, you are viewing account Y" instead of a silent empty fleet. |
| A3 | Email OTP cloud signup from the modal | 🟡 | Works as a signup, but note: the JS email path opens `app.clawmetry.com/auth?token=` and does **not** itself write the local node config (unlike the new OAuth path which fully connects). Consider routing email verify through `_full_connect_with_key` too for parity. |
| A4 | `clawmetry connect` CLI (OAuth + email + key paste) | 🟡 | Loopback OAuth bridge present (`cli.py:_oauth_browser_login`); re-verify all three paths. |
| A5 | Daemon auto-update (no manual pip) | 🟡 | Root-caused + fixed 2026-06-13 (install newest aged-in). Re-confirm field nodes converge. |

## B. Core observability (free, all runtimes)

| # | Promised capability | Status | Notes / evidence |
|---|---|---|---|
| B1 | Sessions list + full transcript per session | 🟡 | Re-verify per runtime; transcript on cloud needs `cm-cloud-transcript`. |
| B2 | Brain (live reasoning/tool feed) + 24h history | 🟡 | SSE `/api/brain-stream`; re-verify per-session filter + canonical session_id. |
| B3 | Flow / Command River (channels → gateway → models → tools) | 🟡 | Phase-1 client-side; re-verify lanes populate per runtime. |
| B4 | Usage / cost analytics (token + cost) | 🟡 | Cost accuracy was 6.4x over-counted (fixed vs ccusage). Re-verify to the dollar. |
| B5 | Subagent tracker (status + cost) | 🟡 | Stranded sub-agent write retry shipped (#3063/#3064). Re-verify. |
| B6 | System health (disk/mem/uptime/GPU) | 🟡 | |
| B7 | Efficiency grade (A–F) + measured savings | 🟡 | Shipped #3066. Verify numbers are real, not placeholder. |
| B8 | **12-runtime** coverage (OpenClaw, NemoClaw free; +10 pro) | 🟡 | Per-runtime E2E matrix must pass for all 12, not just OpenClaw. |
| B9 | Per-runtime scope (no node-wide leak under the switcher) | 🟡 | 5 leaks found+fixed 2026-06-11. Re-run `scripts/verify_runtime_filtering.py`. |

## C. Control plane (the landing's headline promises)

| # | Promised capability | Status | Notes / evidence |
|---|---|---|---|
| C1 | **One-click Kill** a runaway agent from cloud | 🔴/🚧 | Memory flags this as historically **vapor / read-only-conflict / disabled** on device. Chain exists (`enqueue_node_action` → heartbeat → `_dispatch_pending_action`). **Audit priority:** confirm it actually kills a real agent E2E, or mark the copy as Preview. |
| C2 | **Pause / resume** an agent mid-task | 🔴/🚧 | Same as C1 - recon done (SIGSTOP/CONT, proxy `pause_<sid>`), real E2E unproven. Verify or honestly gate. |
| C3 | Approvals (approve/deny) for family runtimes | 🟡 | Was DEAD for claude_code/codex/cursor (fixed #2984). Re-verify a real pending approval resolves. |
| C4 | Hallucination / anomaly detection | 🟡 | Trajectory-anomaly research done; confirm what's actually shipped vs landing copy. |
| C5 | Crons CRUD via gateway RPC | 🟡 | |
| C6 | Custom alerts / budgets / webhooks | 🟡 | Pro-gated; confirm gate + upgrade CTA (no silent no-op). |

## D. Cross-cutting invariants (from FLYWHEEL)

| # | Invariant | Status | Notes |
|---|---|---|---|
| D1 | Cloud parity: every data card has a `cm-cloud-*` interceptor or honest empty state | 🟡 | Sweep for silent blanks on hosted trial. |
| D2 | No OpenClaw-only copy anywhere (runtime-neutral) | 🟡 | Many surfaces still need the sweep (burned 2026-06-01). |
| D3 | CPU budget ≤ ~5–10% of one core | 🟡 | Profile daemon with `sample <pid>`; caps + result-cache in place. |
| D4 | No em-dashes / double-dashes in user-facing copy | 🟡 | Grep payloads before shipping copy. |

---

## Open items / next actions (priority order)
1. **C1/C2 kill + pause E2E** - the biggest credibility risk: landing promises them; prove real or gate as Preview.
2. **A2 verify-live** - real Google/GitHub OAuth round-trip connects a node + snapshot renders on cloud (PR #3375).
3. **B8 12-runtime matrix** - fan out a per-runtime E2E (`/workflow`), assert each lands in Brain by agent_type with cost+tokens.
4. **A3 email-path parity** - make the email modal path also fully connect the node (currently signup-only).
5. **D1 cloud-parity sweep** - hunt silent blank cards on the hosted trial.

_Last updated: 2026-06-28 - seeded during the cloud-OAuth-CTA fix. Update rows as you verify them._
