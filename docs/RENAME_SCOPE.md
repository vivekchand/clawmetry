# Scoping a rename away from "Claw"

**Status:** analysis only — no decision, no work started.
**Baseline:** `v0.12.748`, 1,861 tracked files, 20,268 case-insensitive
occurrences of `clawmetry`, 7,682 of `openclaw`.
**Question this answers:** if we decided to drop "claw" from the product
name, what would it actually cost, and what is the migration path for the
two irreversible pieces — the PyPI name and `ingest.clawmetry.com`?

---

## 0. TL;DR

Roughly **25–45 engineer-days** of focused work, plus a **calendar tail of
months** that no amount of engineering shortens (fleet convergence, Windows
SmartScreen reputation, search re-indexing). The work is not hard; it is
wide, and three or four specific code paths can silently strand installs in
the field if sequenced wrong.

The rename is *technically* migratable — mostly because two seams already
exist that were built for other reasons: `clawmetry/endpoints.py`
centralises every managed-cloud hostname, and the auto-update machinery
already reaches every install within minutes of a release. Those two are
what make a fleet-wide pivot possible at all.

The single largest cost is not in this repo. It is the private
`clawmetry-cloud` repo (SaaS app, license server, Stripe, OAuth, admin,
closed-wheel hosting) plus the identity surfaces attached to it — none of
which are visible from here and none of which are cheap.

---

## 1. Blast radius, in five tiers

### Tier 0 — prose and tests. Mechanical.

| Area | Hits | Files |
|---|---|---|
| `tests/` | 8,065 | 949 |
| `docs/` | 1,560 | 83 |
| root (README, FLYWHEEL, ARCHITECTURE, PRD, AUDIT, …) | 1,562 | 38 |
| `.github/` | 481 | 35 |

`sed`-able, but 949 test files is a diff nobody can review and a merge
conflict against every open branch. **`CHANGELOG.md` (462 hits) must NOT be
rewritten** — it is a historical record; rewriting it makes past releases
un-greppable and every entry subtly false.

### Tier 1 — internal identifiers. One-way, invisible to users if atomic.

- Python package directory `clawmetry/` and every `clawmetry.*` import —
  3,467 hits across 175 files, plus the top-level `routes/` and `helpers/`
  packages shipped alongside it in the wheel.
- 21 `importlib` / `__import__` sites outside tests. Most are stdlib
  (`__import__("pathlib")`), but each one has to be eyeballed: a
  grep-and-replace does not see a module name assembled from a string.
- `setup.py` `package_data` keys (`"clawmetry"`, `"clawmetry.v2"`) — a
  missed key ships a wheel with no `static/` or `templates/`, which fails
  at runtime, not at build time.
- `clawhub-plugin` publishes as `clawmetry-plugin`; `integrations/nat`
  publishes as `clawmetry-nat`.

### Tier 2 — user-visible, but survivable with aliases.

- **257 distinct `CLAWMETRY_*` environment variables.** Every one is a
  documented contract with someone's CI, Dockerfile, or systemd unit. Needs
  a dual-read shim (`NEW_X` falls back to `CLAWMETRY_X`) kept for several
  releases, with a deprecation warning that does not fire on every request.
- **`~/.clawmetry/` state directory** — `config.json`, `license.key`,
  `clawmetry.duckdb`, `sync.log`, `fleet.db`, `local_query.json`,
  `cloud_plan.json`, `trial_state.json`, `onboarding.json`, `server.json`,
  `bin/`, and the `nocloud` / `free_only.marker` / `pro_installed.json`
  markers. The migration is a one-time move plus a compatibility symlink —
  but **the daemon holds the DuckDB writer lock**, so the move has to happen
  with the daemon stopped, from a process that can prove it is stopped.
  Get this wrong and you corrupt the local store, which is the one artifact
  the user cannot re-download.
- CLI entry point `clawmetry` — ship both console scripts indefinitely.
- Wire surface: `X-Clawmetry-Budget-Status`, `X-Clawmetry-Runtime`,
  `X-ClawMetry-Proxy`, `X-Clawmetry-Trial-Blocked`,
  `X-Clawmetry-Bundle-Controls`, and the `clawmetry-*` User-Agent strings.
  Send both old and new headers during overlap; read both forever.
- The `cm_` API-key prefix. Leave it. Stripe still uses `sk_`; nobody cares
  what a key prefix once abbreviated.

### Tier 3 — external identity. Irreversible, and the real cost.

- **PyPI name** — cannot be renamed. See §2.
- **Domains** — `clawmetry.com`, `app.`, `ingest.`, `license.`, `build.`,
  `docs.`, plus `clawmetry.app` / `.net`. See §3.
- **GitHub repo** — `vivekchand/clawmetry`. GitHub redirects the URL and git
  remotes, so this is the cheapest Tier-3 item, but stars/forks/search rank
  attach to the new name and inbound links decay.
- **Desktop code-signing reputation.** `com.clawmetry.desktop` is the macOS
  bundle identifier (`build_mac.spec`, `setup_py2app.py`); a new bundle ID
  is a *different application* to Gatekeeper and to every user's existing
  install. On Windows, `ClawMetry-Setup-${VERSION}.exe` under
  `$LOCALAPPDATA\Programs\ClawMetry` is Authenticode-signed via Azure
  Artifact Signing — a new product/publisher string **resets SmartScreen
  reputation**, so early adopters of the renamed build get the red
  "unrecognised app" wall for weeks. This is calendar time, not eng time,
  and it cannot be bought back.
- **Not visible from this repo, and probably the biggest bucket:**
  `clawmetry-cloud` — Stripe product/price names and customer-facing
  invoices, OAuth client registrations and redirect URIs, the Ed25519
  license issuer, Cloud Run service names, DNS, and the
  `vivek@clawmetry.com` sender identity (a new sending domain restarts email
  reputation warm-up).

---

## 2. Migration path — PyPI

PyPI has no rename operation. The path is a **pivot shim**, and the ordering
is load-bearing.

1. **Register `<newname>` on PyPI now**, before anything else. It is free
   and it is the only step that gets more expensive by waiting.
2. **Publish `<newname>` at the current version number**, not at `0.1.0`.
   The update checker compares versions; a version that goes backwards
   breaks the comparison for every install that has already pivoted.
3. **Ship one final `clawmetry` release as the pivot.** It must:
   - declare `install_requires=["<newname>>=<current>"]`,
   - keep a working `clawmetry` console script that exec's the new entry
     point,
   - and — this is the part that decides whether the migration works —
     **ship an update checker pointed at the new name.**

   `routes/update_check.py` polls `https://pypi.org/pypi/clawmetry/json` and
   the self-update path in `routes/meta.py:442` runs `pip install -U
   clawmetry`. If the pivot release does not repoint both at `<newname>`,
   every install in the field pins to the last `clawmetry` version *forever*
   and the fleet never moves.
4. **Keep publishing `clawmetry` releases** that do nothing but bump the
   pin, for as long as you want the shim to keep pulling stragglers forward.
   Never yank the old project — yanking breaks reproducible builds for
   anyone who pinned.

**Highest-risk code path in the entire rename:** cross-name self-update.
`clawmetry/update_respawn.py` runs `pip install --upgrade clawmetry==<target>`
and then respawns; `clawmetry/update_guard.py` and
`clawmetry/distinfo_cleanup.py` exist specifically because in-place upgrades
on Windows already misbehave. A cross-name upgrade is a strictly harder case
than the one that needed `distinfo_cleanup.py`, and a failure here does not
degrade — it leaves a half-installed daemon. This needs the full 3-OS × 2-Python
matrix plus a deliberate "upgrade from the last old-name version" test that
does not exist today.

---

## 3. Migration path — `ingest.clawmetry.com`

This one is in better shape than expected.

**What helps:**
- `clawmetry/endpoints.py` (149 lines) is a genuine seam:
  `DEFAULT_INGEST_URL`, `DEFAULT_APP_URL`, env override, `endpoint_hosts()`.
- No certificate pinning anywhere; TLS goes through truststore/certifi, so a
  new host with a new cert just works.
- The host is a **compile-time default, not persisted** into
  `~/.clawmetry/config.json`. That means a shipped release genuinely moves
  the fleet — no per-install reconfiguration.

**Sequence:**
1. New ingest host live, serving *both* names, with the old hostname as a
   permanent CNAME/proxy in front of it.
2. Ship a release that flips `DEFAULT_INGEST_URL`.
3. Watch convergence on the fleet view. Do not touch the old host until the
   tail is flat.
4. Keep `ingest.clawmetry.com` resolving and serving **indefinitely** — not
   for 12 months. Installs with auto-update disabled (`CLAWMETRY_AUTO_UPDATE=0`),
   air-gapped deployments, and pinned versions will point at it forever. It
   is one DNS record and a proxy rule; the cost of dropping it is silent
   data loss for precisely the most conservative customers.

**Two traps found in the current code — both must be fixed *before* the flip:**

- **`is_custom_endpoint()` is `ingest_url() != DEFAULT_INGEST_URL`.** The
  moment `DEFAULT_INGEST_URL` changes, any install that sets
  `CLAWMETRY_INGEST_URL=https://ingest.clawmetry.com` explicitly — which is
  exactly what a cautious operator does — starts reading as a *self-hosted*
  deployment. `egress_suppressed()` then returns `True`, and its docstring
  lists **update checks** among the discretionary calls it suppresses. That
  install stops updating permanently, on the release that was supposed to
  migrate it. Fix: make the managed-host check a set membership over
  `{old, new}`, not a string equality, and land that change *at least one
  release before* the flip so it is already in the field.
- **`clawmetry/interceptor.py:76`** computes `_EXCLUDED_HOST_DEFAULTS` at
  import time from `endpoint_hosts()`. During overlap the old host must stay
  in that set, or the interceptor starts treating ClawMetry's own egress as
  billable LLM traffic and inflates the user's cost numbers.

---

## 4. Cost

| Bucket | Engineer-days |
|---|---|
| Tier 0 — docs, tests, CI strings | 2–3 |
| Tier 1 — package/import rename, packaging, wheel data | 3–5 |
| Tier 2 — env-var aliases, state-dir migration, dual CLI | 5–8 |
| PyPI pivot + cross-name self-update, tested on 3 OS × 2 Py | 5–10 |
| Domain cutover + the two `endpoints.py` fixes | 2–3 |
| Desktop rebuild, re-sign, re-notarise, installer rename | 3–5 |
| `clawmetry-cloud` (unseen — Stripe, OAuth, license, DNS, email) | 5–10 |
| **Total** | **25–45** |

≈ **5–9 weeks solo**, during which the flywheel ships nothing else, since
every release in flight conflicts with the rename diff.

Calendar costs that no engineering removes: fleet convergence to the new
package name (weeks, and never 100%), SmartScreen reputation rebuild
(weeks), search re-indexing and inbound-link decay (months), and email
sending-domain warm-up.

---

## 5. Assessment

The rename is feasible and the path above is real. It is not worth doing on
the evidence that prompted it: one comment, one upvote, arguing that a
phonetic association with another project's launch marketing is
disqualifying. That is not a signal, and the alternative it proposed —
naming off "Claude" — is worse than the status quo, since Anthropic's
trademark guidelines do not permit product names built on it.

**The one thing that would change this analysis** is legal exposure rather
than sentiment: if "Claw" is or becomes a registered mark for AI-agent
software, the rename stops being optional and the cost above becomes a
schedule, not a choice. That is worth a trademark search now — it is cheap,
and it is the only version of this question with a deadline attached.

**Cheap hedge, if any action is wanted today (≈$20, under an hour):**
register the candidate PyPI name and the domain defensively, and land the
`is_custom_endpoint()` set-membership fix from §3 — that one is a latent
bug regardless of whether a rename ever happens.

---

## 6. Appendix — candidate names (availability checked 2026-08-23)

**Finding that shapes the whole shortlist:** of ~65 names with any semantic
content tested, **the `.com` was registered for every single one** — 65/65,
including obscure coinages like `orbimetry.com` and `vantris.com`. The
method was validated against controls (`google.com` → registered,
`zzqxwvunlkj7.com` → free), and pronounceable *nonsense* of the same shape
(`zelmetry`, `quorbimetry`) came back free. So the result is real: any name
a person would recognise as a word is already held, mostly by drop-catchers.
A `.com` therefore means an aftermarket purchase (typically low-to-mid four
figures for a parked coinage), or shipping on `.dev` / `.io`, as Pydantic
(`pydantic.dev`) and Braintrust (`braintrust.dev`) already do.

PyPI is the looser constraint — every plain English word is squatted there
too, but coinages and compounds are largely free.

| Candidate | PyPI | .dev | .app | Notes |
|---|---|---|---|---|
| **runmetry** | FREE | FREE | FREE | Keeps the `-metry` DNA; "run" is the noun the product measures |
| **lumetry** | FREE | FREE | FREE | lumen + -metry; prettier, vaguer |
| **clarimetry** | FREE | FREE | — | clarity + -metry; slightly corporate |
| **telemetron** | FREE | FREE | FREE | Memorable, instrument-flavoured |
| **agentdeck** | FREE | taken | — | Flight-deck framing fits the control plane |
| **agentgauge** | FREE | taken | FREE | Plain, instantly legible |
| **metrion** / **vantris** / **lumeta** | FREE | — | mixed | Blank-slate coinages; no free association to trade on |

### Recommendation: `RunMetry`

Beyond reading well, it is the only candidate that makes the §1–§4 work
materially cheaper. The rename becomes a **morpheme swap of identical
shape** — `s/claw/run/` preserves every capitalisation convention in the
codebase in one pass:

```
ClawMetry     → RunMetry
clawmetry     → runmetry
CLAWMETRY_*   → RUNMETRY_*        (all 257 env vars)
~/.clawmetry/ → ~/.runmetry/
com.clawmetry.desktop → com.runmetry.desktop
```

CLI length and rhythm are unchanged, so docs, muscle memory and every
screenshot in the README survive. A shape-changing rename (`clawmetry` →
`agentdeck`) turns Tier 0 and Tier 1 from a reviewable mechanical diff into
a hand-audited one across 949 test files. Nothing about the Tier 3 costs
changes — PyPI, domains and signing reputation are indifferent to which name
you pick — but the cheap tiers get meaningfully cheaper and safer.

**Not checked, and required before committing to any of these:** a real
trademark search in the relevant classes. Availability on PyPI and in DNS
says nothing about whether a mark is already registered.

### 6.1 On short numeric names (the `8090.ai` shape)

`8090.ai` itself is unavailable for a reason worth stating plainly: **8090 is
our own vendor.** `.mcp.json` points at `api.factory.8090.dev`, FLYWHEEL.md
tracks this repo in 8090 Software Factory at `factory.8090.ai`, and the
plugin ships as `8090-inc/software-factory-plugin`. Naming the product after
the toolchain vendor is a trademark problem and guarantees confusion in our
own docs.

The *style* has three concrete problems for this product specifically:

1. **A leading digit is not a legal Python identifier.** `import 8090` is a
   `SyntaxError`. Our import path is `clawmetry.*` across 175 files and the
   `setup.py` `package_data` keys *are* the package name, so a numeric brand
   permanently forces dist-name ≠ import-name (the `pillow`/`PIL` split).
   That makes the §2 pivot shim and the `package_data` seam more fragile,
   which is the opposite of what we want during a migration.
2. **This product is already saturated with port numbers** — 8900 dashboard,
   4100 proxy, 18789 gateway. "Run 8090 on port 8900" is a sentence we would
   have to write in the docs and say in support.
3. **Numerics are the most speculated domain category, not the least.**
   Every numeric checked (`1090`, `8090`, `8900`, `406`, `121`) is registered
   on both `.ai` and `.com`.

What is right about the instinct is the blank slate: no morpheme to defend,
no association to shed. If we want that, the shape to use is **letter+digit**
(`k6`, `k9s`, `s3`), which stays a valid identifier and a sane CLI:

| Candidate | Identifier | PyPI | .ai | .com |
|---|---|---|---|---|
| **obs9** | yes | FREE | taken | **FREE** |
| tel9 | yes | FREE | FREE | taken |
| t1090 / r1090 | yes | FREE | FREE | FREE |

`obs9.com` was the only free `.com` in ~70 names checked. The best-motivated
numeric is **1090** — the frequency (MHz) on which every aircraft broadcasts
its telemetry to ground stations, which is precisely what the daemon does —
but the identifier and port-collision problems still apply.

**Recommendation is unchanged: `RunMetry`.** Note that `runmetry.ai` is also
free, so it satisfies the `.ai` preference without any of the above.

### 6.2 `Rangehead`

**Availability — the only clean sweep found in ~75 names checked:**

| | identifier | PyPI | .com | .ai | .dev | .io |
|---|---|---|---|---|---|---|
| **rangehead** | yes | FREE | **FREE** | FREE | FREE | FREE |

A free `.com` is worth real money here: every other semantically meaningful
candidate would mean an aftermarket purchase (low-to-mid four figures for a
parked coinage) or launching on `.dev`. `rangehead` also happens to be nine
characters, exactly `clawmetry`'s length, so CLI rhythm, docs layout and
screenshots survive unchanged.

**It has a true story, and a better one than the current name has.** In
aerospace a *range* is the instrumented test corridor — range telemetry,
range safety. The Range Safety Officer is the one person who can terminate a
vehicle in flight when it leaves its envelope. That is precisely this
product: observe everything by default, terminate on a policy the user
declared. It explains both halves — the dashboard and the control plane —
which "ClawMetry" never did.

**Two real costs:**

1. **`head` is overloaded in exactly our space.** Attention heads, `git
   HEAD`, HTTP `HEAD`, the head of a stream. A share of first-contact
   readers in AI infra will parse it as something about transformer heads.
2. **It does not self-describe.** `-metry` at least said *measurement*.
   Rangehead needs a sentence of explanation in every headline, bio and
   Show HN title, forever. The story is good, but stories need airtime.

It also forfeits the `s/claw/run/` mechanical-migration argument from §6 —
Tier 0/1 returns to a hand-audited diff across 949 test files, roughly 2–4
engineer-days more than `RunMetry`. Against a 25–45 day total that is noise.

The rest of the range family is unavailable (`downrange` taken on all TLDs;
`rangesafe.com`, `rangeops.com` taken), so `rangehead` is the one that is
actually free.

**Verdict:** it clears the bar. The choice is between a safe, self-
describing, cheap-to-migrate name whose `.com` is gone (`RunMetry`) and an
ownable one with a real story and a free `.com` that has to be taught
(`Rangehead`). Either is defensible; the `head` collision is the only thing
that would give me pause. A trademark search is still required.
