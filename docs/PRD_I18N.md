# PRD — Internationalization (i18n) for ClawMetry

> Status: **Draft for approval** · Owner: autonomous agent loop · Created: 2026-05-24
> Scope: the dashboard app, the landing/marketing site, the cloud surface, and the README/docs.
> Decisions locked with the user: **fully-automated LLM-bot translation · all ~30+ languages at once · per-language SEO is required (landing uses crawlable locale subpaths) · the chosen language must stay consistent across pages, reloads, and surfaces.**
>
> _(Revised after the initial "client-side-only" pick: the user added "it needs to be SEO-friendly for that local language too" and "if they change language it should remain consistent." Per-language SEO is incompatible with a single client-side-swapped URL, so the **landing** now uses locale subpaths + `hreflang`; the **dashboard** stays client-side since it's behind the tool and never indexed. Consistency is handled by a shared cross-subdomain cookie + URL locale, see §3.8.)_

## 0. TL;DR

Make every word ClawMetry shows a user translatable, ship ~30+ languages on day one, auto-detect the visitor's language, let them override it from a switcher in the top-right, and keep the whole thing fresh **without a human translator in the loop** — a CI bot (Claude) translates every new or changed English string into all languages on each PR. The README and docs get the same treatment via a `docs/i18n/<lang>/` tree.

The single hard constraint that dictates the entire design: **ClawMetry has no build step and no npm** (CLAUDE.md, non-negotiable). So the runtime is vanilla JS + Flask/Jinja + a flat JSON catalog, with all extraction/validation/translation happening in **CI**, never on the user's machine.

**How hard is it?** The plumbing is ~3-4 days. The real work is the one-time string extraction across a 16.5k-line `app.js` + 23 templates + the landing HTML (~2-3 weeks, heavily mechanizable). Translation itself is automated and ongoing-free. RTL (Arabic/Hebrew) is a separate, optional chunk. Verdict: **medium effort to wire, large-but-mechanical effort to extract, near-zero effort to maintain once the bot is running.**

---

## 1. Goals / Non-goals

### Goals
- Every user-facing string in the **dashboard**, **landing site**, and **README/docs** renders in the visitor's language.
- **~30+ languages** at launch (full list in §8), including CJK (zh, ja, ko), Indic (hi, ta, kn, bn, te, mr), and major European/SEA languages.
- **Auto-detect** the visitor's language; **switcher in the top-right** to override; choice **persists**.
- **The chosen language stays consistent everywhere** — across page navigation, reloads, *and* across surfaces (landing → app → cloud, all on `*.clawmetry.com`). One choice, honored once and remembered. (§3.8)
- **Per-language SEO on the landing site** — each language is a crawlable URL (`clawmetry.com/ja/`) that Google indexes with the right `lang`/`hreflang`, a localized `<title>`/`<meta description>`/Open Graph, and a per-locale sitemap entry. A shared `clawmetry.com/ja/pricing` link opens in Japanese. (§4.2)
- Numbers, dates, costs, relative times, and plurals format per-locale (via native `Intl.*`).
- **Zero new runtime dependency**, no build step, no npm — honor CLAUDE.md.
- **Self-maintaining**: adding an English string anywhere triggers automatic translation into all languages on the next PR. English is the single source of truth.
- **Never crash on a missing translation** — always fall back to English (matches the "never crash on bad input" rule).

### Non-goals (v1)
- Locale in the URL for the **dashboard** app — it's behind the tool, never indexed, so client-side + persisted choice is enough. (Per-language SEO applies to the **landing** and **docs**, which *are* public — that's now in-scope, see §4.2.)
- Human/professional translation review or a translation-management platform (Crowdin/Weblate/Tolgee) — explicitly out; the bot owns it.
- Translating **user data** (agent transcripts, log lines, model output) — that's the user's content, not our chrome. We localize the *interface*, not the observed data.
- Right-to-left layout (Arabic/Hebrew/Persian/Urdu) — phased to a later milestone (§8, Phase 5) because the current CSS uses physical properties (`margin-left`, inline styles) and needs a logical-property pass first.
- Localizing currency *values* — costs stay in USD (it's billing); only the *number formatting* (grouping/decimal separators) localizes.

---

## 2. The constraint that rules everything out

ClawMetry has **no build step and no npm**. That immediately disqualifies the "normal" web i18n stacks that assume a bundler:

| Approach | Why it's out (for the runtime) |
|---|---|
| `react-intl` / `lingui` / `vue-i18n` | Require a build + framework. The live UI is vanilla JS in `app.js`. (The dormant `static/v2/dist/` Vite build is **not wired in** — ignore it.) |
| Flask-Babel / gettext `.po`/`.mo` | Adds the `Babel` dependency **and** a `pybabel compile` step. Violates minimal-deps + no-build. Also splits the source of truth between server `.po` and client JSON. |
| Webpack/Vite-bundled i18next | Same build-step problem. |

What survives the constraint:
- **A flat JSON catalog** (`locales/<lang>.json`) — one source of truth, shared by the few server-rendered bits and the client.
- **Native `Intl.*`** (`Intl.NumberFormat`, `DateTimeFormat`, `RelativeTimeFormat`, `PluralRules`, `ListFormat`) — built into every browser we support, zero dependency, locale-aware out of the box.
- **A tiny (~120-line) vanilla `t()` runtime** that loads the active locale's JSON and translates `data-i18n` DOM nodes + exposes `t("...")` to `app.js`. No framework.

> **Build-vs-buy answer to "is there an OSS project to make this fast?"**
> Yes, several — but given the no-build constraint and the "fully automated bot, no platform" decision, the fastest *correct* path is a thin custom runtime, not adopting a heavy framework. For reference, the OSS options and why we pass on them:
> - **i18next** (de-facto standard, *can* run no-build via CDN with `i18next-browser-languagedetector` + `i18next-http-backend`) — viable fallback if our `t()` runtime ever needs ICU/context features. ~50 kB. We start without it and only adopt if needed.
> - **Polyglot.js** (Airbnb, ~6 kB, interpolation + plurals) — closest in spirit to our custom runtime; a fine drop-in if we'd rather not hand-roll.
> - **FormatJS / `intl-messageformat`** — standards-based ICU; heavier, only if rich pluralization demands it.
> - Management platforms (**Weblate** self-host, **Crowdin** free-for-OSS, **Tolgee**) — explicitly **out** per the automated-bot decision, but documented here as the upgrade path if we ever want human review.

---

## 3. Architecture

### 3.1 The catalog (single source of truth)

```
clawmetry/static/locales/        # under static/ so the existing /static route serves them
                                  # AND the existing package_data glob ships them — no new endpoint, no setup.py change
    en.json          # SOURCE OF TRUTH — only humans/agents edit this (indirectly, by adding strings)
    zh-CN.json        # bot-generated
    ja.json           # bot-generated
    hi.json           # bot-generated
    ... (30+)
    _meta.json        # language registry: code, endonym, dir(ltr|rtl), enabled, dev, font-stack
```

- Shipped inside the wheel automatically: `setup.py`'s `package_data` already globs `static/**/*` and `MANIFEST.in` has `recursive-include clawmetry/static *`, so files under `static/locales/` ride along with no packaging change. Cloud (which serves the pinned wheel) gets them for free.
- Served to the browser via the existing cache-busted static route: `GET /static/locales/<lang>.json`. (Phase 0 shipped this exact layout.)

### 3.2 Key strategy: **English string as the key** (with explicit keys only where needed)

The migration friction is the whole ballgame here. With 766 string-writes in `app.js` and 23 inline templates, inventing a dotted key name for every string (`overview.autonomy.title`) is weeks of bikeshedding. Instead:

- **Default: the English text *is* the key.** `t("How independent is your agent?")`. The catalog maps the English source string → translation.
  - Pro: minimal rewriting (wrap or mark, don't name), maximal context for the LLM bot, trivially greppable.
  - Con: editing the English wording orphans the old translation — **but that's fine in an auto-bot world**: the bot detects the new source string and re-translates it; an orphan-sweep prunes the dead key. No human is maintaining key↔string mapping by hand.
- **Explicit keys** (a dotted namespace) **only** for: strings with placeholders/plurals, strings whose English is ambiguous out of context ("Open", "Close", "Stop"), and anything reused in many places. Marked `t("verb.stop", "Stop")` (key + English default).

This hybrid is what gettext/Polyglot call "source-as-msgid" and it's the right call for a bot-driven shop.

### 3.3 Runtime — two entry points, one catalog

**(a) Static HTML in templates** — mark translatable nodes with `data-i18n`:
```html
<!-- before -->
<div>How independent is your agent?</div>
<!-- after -->
<div data-i18n>How independent is your agent?</div>
<!-- attributes: -->
<button data-i18n-attr="title" title="Refresh">↻</button>
```
On load and on language change, the runtime walks the DOM, reads each `data-i18n` node's English text as the key, and swaps in the translation. Placeholder/`--` nodes and `data-i18n-skip` zones are left alone.

**(b) JS-generated strings in `app.js`** — wrap in `t()`:
```js
// before
el.textContent = "No data yet";
// after
el.textContent = t("No data yet");
el.innerHTML = t("{n} sessions today", { n: count });   // ICU-lite interpolation
```

The runtime (`static/js/i18n.js`, ~120 lines, no deps):
```
window.i18n = {
  lang, dict,
  t(key, vars) → lookup(dict, key) ?? key (English fallback), then interpolate {vars} + Intl plurals,
  setLang(code) → fetch /static/locales/<code>.json, swap dict, re-walk DOM, persist to localStorage, set <html lang>/<dir>,
  num(n) / date(d) / rel(d) / list(arr) → thin Intl.* wrappers bound to the active locale,
}
```
Loaded **before** `app.js` in the live `DASHBOARD_HTML` (dashboard.py:10831 — the *live* one; the block at 2988 is dead, do not touch it).

### 3.4 Detection & the switcher

**Precedence (highest wins):**
1. **URL locale** (landing only) — `clawmetry.com/ja/...`. Authoritative for that page load so shared/indexed links always open in their language; also writes the cookie so the choice sticks as the user navigates away from a prefixed URL.
2. **Explicit choice** — the shared `cm-lang` cookie (scoped to `.clawmetry.com` so it spans landing + app + cloud) and `localStorage` mirror. Set by the switcher. Sticky.
3. **`navigator.languages`** (the browser's real Accept-Language preference) — the *primary* auto signal for a first-time visitor. More accurate than IP, no server round-trip.
4. **Geo-IP hint** — a *weak secondary* signal. The cloud/landing edge already exposes a country header (Cloud Run / Cloudflare `CF-IPCountry`); a tiny `/api/geo` echoes it and we map country→language **only when (3) is inconclusive**.
5. **English** default (`x-default` for hreflang).

> **Judgment call on "auto-detect by IP":** IP geolocation for *language* is a known anti-pattern (a French speaker in Berlin gets German). We honor the intent — auto-detection that "just works" — but rank `navigator.languages` first and treat IP as a tiebreaker hint, with the user's explicit choice always overriding. This is the industry-standard precedence and avoids the classic "why is your site German, I'm just travelling" complaint.

**Switcher UI** (top-right, per the ask):
- A globe-icon dropdown rendered into the existing top-bar (dashboard: injected next to the LIVE/refresh row; landing: top nav).
- Lists each language by its **endonym** (native name: "日本語", "Français", "தமிழ்", "ಕನ್ನಡ") — never translate the language menu into the current language.
- On select → `i18n.setLang(code)`; no page reload (re-walk the DOM in place — note the FLYWHEEL rule: **no `location.reload()` in bootstrap JS**, it crashes Playwright fixtures).

### 3.5 Formatting (numbers, dates, costs, plurals)

All via native `Intl.*`, bound to the active locale — no library:
- **Costs**: `Intl.NumberFormat(lang, {style:'currency', currency:'USD'})` → keeps USD, localizes grouping/decimal (`$1,234.50` vs `1.234,50 $US`).
- **Token counts / big numbers**: `Intl.NumberFormat(lang, {notation:'compact'})` → `1.2M` / `120万`.
- **Dates/times**: `Intl.DateTimeFormat`.
- **"3 minutes ago"**: `Intl.RelativeTimeFormat`.
- **Plurals**: `Intl.PluralRules` drives the `_one`/`_other`/`_many` suffix lookup in the catalog (handles languages with 1, 2, 3, 4, or 6 plural forms — e.g. Arabic's six, Russian's three).

### 3.6 Fonts (so nothing renders as □□□ "tofu")

- CJK and Indic scripts need real glyph coverage. Strategy: **system-font-first, Noto web-font fallback, subset per script, lazy-loaded only when that script is active.**
- Add `Noto Sans`, `Noto Sans JP`, `Noto Sans SC/TC`, `Noto Sans KR`, `Noto Sans Tamil`, `Noto Sans Devanagari`, `Noto Sans Kannada`, etc. (Noto = "no tofu") with `font-display:swap`, `unicode-range`-scoped `@font-face`, loaded only for the active locale so a French user never downloads CJK fonts.
- Verify line-height/letter-spacing don't clip tall Indic stacks or wide CJK; loosen the cramped `letter-spacing:1.5px; text-transform:uppercase` headers (uppercasing is meaningless in most non-Latin scripts — gate it behind `:lang(en)` etc.).

### 3.7 RTL (phased, Phase 5)

- Set `<html dir="rtl">` for ar/he/fa/ur from `_meta.json`.
- Requires migrating physical CSS props → **logical properties** (`margin-inline-start`, `padding-inline`, `inset-inline`) and auditing the heavy inline `style="...margin-left..."` usage in templates. Real work → its own milestone, not blocking the ~30 LTR languages.

### 3.8 Consistency — one choice, honored everywhere

The user's requirement: *"if they change language it should remain consistent."* It must persist across **page navigation, reloads, and surfaces** (landing ↔ app ↔ cloud). Three coordinated stores keep it consistent:

1. **Shared cookie** `cm-lang`, scoped to `Domain=.clawmetry.com` (so `clawmetry.com`, `app.clawmetry.com`, and the cloud read the *same* value), `Max-Age` ~1 year, `SameSite=Lax`. This is what makes a language picked on the marketing site carry into the logged-in app and vice-versa.
2. **`localStorage['cm-lang']`** mirror — fast, synchronous read on the dashboard (no cookie round-trip) and the authority for the auth-gated app where there's no per-page server render.
3. **URL locale** on the landing (`/ja/...`) — the SEO-visible, shareable form; writing the cookie on every locale-prefixed page load keeps (1)/(2)/(3) in agreement.

On switch, `i18n.setLang(code)` writes all three atomically, updates `<html lang>`/`dir` in place (no `location.reload()` — Playwright-safe), and on the landing **navigates to the same page under the new locale prefix** so the URL, cookie, and rendered language never disagree. Because the cookie is domain-wide, a user who set Tamil once never re-picks it — every ClawMetry property they open is already Tamil.

> Edge case handled: a logged-out visitor sets `ja` on the landing → cookie on `.clawmetry.com` → signs into `app.clawmetry.com` → the dashboard reads the same cookie/localStorage and boots in Japanese with zero interaction. Conversely, changing it in the app updates the cookie the landing will honor on the next visit.

---

## 4. Surfaces

### 4.1 Dashboard (OSS app) — the long pole
- Files: live `DASHBOARD_HTML` (dashboard.py:10831), `static/js/app.js` (16.5k lines, ~766 DOM-write sites), `static/js/{alerts,nav-dropdown,gw-setup,auth-bootstrap}.js`, 23 `templates/tabs/*.html`, 5 `templates/partials/*.html`.
- Work: load `i18n.js` first; mark template strings with `data-i18n`; wrap JS strings with `t()`; add the switcher to the top-bar.
- **Cloud gets this for free** — the cloud serves the pinned OSS wheel's `app.js`/templates. No separate cloud i18n build. (Just confirm `cm-cloud-*` interceptors don't hardcode English fallbacks.)

### 4.2 Landing / marketing site (`clawmetry-landing`) — SEO-friendly per language
- Separate repo, Flask + `render_template_string` over standalone HTML (`index.html`, `pricing.html`, `cloud.html`, …).
- Same JSON-catalog + `data-i18n` runtime, its own `locales/`.
- **Locale subpaths, server-rendered per language** (the SEO requirement). Two equivalent ways to produce them with no client-build:
  - **(a) Flask route prefix** `/<lang>/...` that renders the page with the locale's catalog server-side (Jinja `data-i18n` substituted at render time, not just in-browser). Translated text is in the initial HTML, so Googlebot indexes the real language.
  - **(b) CI pre-render** — a build-time step emits a static `/<lang>/index.html` per page from the same catalog and serves them as files. (Matches the landing's static-HTML nature; no runtime cost.)
  Pick (a) if we want one canonical render path, (b) if we want pure static hosting. Either way the **client-side runtime still runs** for the in-page switcher and `Intl` formatting.
- **Per-page SEO emitted for every locale:**
  - `<html lang="ja">` + `<link rel="alternate" hreflang="ja" href="https://clawmetry.com/ja/pricing">` for every language, plus `hreflang="x-default"` → English.
  - Localized `<title>`, `<meta name="description">`, and Open Graph / Twitter card text (these live in the catalog too, under a `meta.*` namespace).
  - `<link rel="canonical">` per locale URL.
  - A **multilingual sitemap** (`sitemap.xml` with `xhtml:link` alternates) so Search Console sees the language set.
- **No hard geo/Accept-Language redirect of crawlers.** `/` serves English (`x-default`) with full hreflang alternates; first-time human visitors get a *dismissible* "View in 日本語?" banner (driven by `navigator.languages`/geo) that links to the locale subpath. Hard-redirecting Googlebot (which crawls from the US with `Accept-Language: en`) would de-index the other languages — the subpaths are the canonical indexable URLs and must stay directly reachable.
- Switcher in the top nav navigates to the same page's locale prefix **and** sets the domain-wide cookie (§3.8), so the choice follows the user into the app.

### 4.3 README & docs
- Convention: `docs/i18n/<lang>/README.md` (keep root `README.md` as English canonical + a language bar at the very top linking to each translation).
  ```
  <!-- top of README.md -->
  **Read this in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [Français](docs/i18n/fr/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [தமிழ்](docs/i18n/ta/README.md) · …
  ```
- Generated by the **same bot** (§5): the translation Action diffs `README.md` (and selected `docs/*.md`), Claude translates to Markdown preserving code blocks/links/anchors, commits to the `docs/i18n/<lang>/` tree. A staleness badge/marker notes the source commit each translation was generated from.

---

## 5. The translation flywheel (fully automated, no human gate)

This is the chosen production model and the part that makes it "easy to maintain & evolve."

```
PR adds/edits an English string (in en.json, README.md, or a doc)
        │
        ▼
CI: extract + lint gate
   - scan templates/app.js for data-i18n / t() and rebuild locales/en.json
   - FAIL the PR if a user-facing string is unmarked (heuristic: visible text ≥2 letters
     outside a data-i18n-skip / no-translate zone)  ← keeps coverage at 100%
        │
        ▼
On merge to main → "i18n-autotranslate" GitHub Action (Claude):
   - diff en.json vs each <lang>.json → find missing/changed keys
   - batch-translate ONLY the deltas via the Claude API (model: latest Sonnet for cost,
     Opus for marketing/landing copy), with a glossary + "do-not-translate" list
   - prune orphaned keys (English source removed)
   - same for README/docs deltas
   - open/auto-merge a "chore(i18n): sync translations" PR (it touches only locales/ + docs/i18n/)
        │
        ▼
[RELEASE] picks it up → PyPI → cloud pin → live in all languages
```

Bot guardrails (so "no human gate" doesn't mean "no quality bar"):
- **Glossary / do-not-translate list** (`locales/_glossary.json`): product nouns that must NOT translate — "ClawMetry", "OpenClaw", "DuckDB", "cron", tab names if we choose, code identifiers, `{placeholders}`, brand copy. The prompt enforces it.
- **Placeholder integrity check**: post-translation lint fails if `{n}`, `%s`, HTML tags, or markdown links/anchors don't survive 1:1.
- **No-em-dash rule** carries into translated marketing copy (memory: AI-tell).
- **Length sanity**: flag translations >2× English length (German/Tamil expansion can break fixed-width chips) for a follow-up CSS check; don't block.
- **Idempotent + cheap**: only translates deltas, so steady-state cost is a few keys per PR. Full-catalog backfill is a one-time cost at launch.
- **Pseudolocale `en-XA`** generated in CI (`[!! Ħöw íñðëþëñðëñţ… !!]`, +30% length): a fake locale that visually surfaces (a) any string that *wasn't* extracted (shows up un-accented) and (b) layout that breaks on longer text. Ship it as a hidden dev-only locale.

---

## 6. Phased rollout & effort

| Phase | Scope | Effort | Gate to next |
|---|---|---|---|
| **0 — Foundation** | `i18n.js` runtime, `locales/en.json` + `_meta.json`, switcher component, detection precedence, `Intl` formatters, CI extract+lint gate, pseudolocale. **No real translations yet** — English routes through `t()`. | ~3-4 d | Switcher flips to `en-XA` and the whole dashboard shows accented text → proves coverage wiring. |
| **1 — Dashboard extraction** | Mark all 23 templates + wrap all `app.js`/aux-JS strings. The grind; mechanizable with a codemod + the pseudolocale to find misses. | ~1.5-2 wk | `en-XA` shows <1% un-accented user-facing text. |
| **2 — Autotranslate bot** | The GitHub Action, glossary, placeholder/markdown integrity checks, orphan prune, auto-PR. | ~3-4 d | Bot opens a green sync PR; spot-check zh/ja/hi render correctly. |
| **3 — All ~30+ languages live** | Run the full backfill; ship Noto font subsets; QA top locales in-browser; `[RELEASE]` → PyPI → cloud. | ~1 wk (mostly QA + fonts) | Decrypt a live snapshot + screenshot the dashboard in zh-CN/ja/ta. |
| **4 — Landing (SEO) + README/docs** | Locale-subpath rendering + `hreflang`/canonical/localized meta + multilingual sitemap on the landing; domain-wide cookie wiring; README language bar + `docs/i18n/<lang>/` generated by the bot. | ~1.5 wk | `clawmetry.com/ja/pricing` returns Japanese in the **initial HTML** (curl, not just JS); hreflang validates; language persists landing→app via the shared cookie. |
| **5 — RTL + polish (optional)** | Logical-property CSS pass; enable ar/he/fa/ur; fix expansion-driven layout breaks flagged in Phase 1. | ~1-1.5 wk | dir=rtl renders without mirrored-layout bugs. |

**Total to "all languages live across app + landing + README" (Phases 0-4): ~5-6 weeks of focused work, most of it the mechanical extraction in Phase 1.** RTL is additive.

### 6.1 Launch language set (~32; user chose "all at once")
`en` (source) · `zh-CN` · `zh-TW` · `ja` · `ko` · `hi` · `bn` · `ta` · `te` · `kn` · `ml` · `mr` · `gu` · `pa` · `es` · `es-419` · `pt-BR` · `pt-PT` · `fr` · `de` · `it` · `nl` · `pl` · `ru` · `uk` · `tr` · `id` · `vi` · `th` · `fil` · `sv` · `el`
RTL (Phase 5): `ar` · `he` · `fa` · `ur`.

### 6.2 SEO (now in-scope, landing + docs)
Per-language SEO is a v1 requirement. The landing serves real translated HTML per locale subpath with `hreflang`/canonical/localized meta + a multilingual sitemap (§4.2) — so Google indexes each language and a `/<lang>/` link opens in that language. The README/docs are SEO-discoverable for free: GitHub renders each `docs/i18n/<lang>/README.md` as its own indexable page, and we cross-link them with a language bar + (if a docs site exists) the same locale-subpath + hreflang pattern. The **dashboard** is intentionally excluded — it's behind the tool and not meant to be indexed.

---

## 7. Maintenance & evolution (the "easy to evolve" requirement)

- **English is the only file a human/agent ever edits.** Everything else is generated. Adding a feature = add English strings → bot fills the rest on merge.
- **CI coverage gate** makes un-internationalized strings *impossible to merge* — the codebase can't regress to hardcoded English.
- **Graceful fallback**: missing key → English; missing locale file → English. Never a blank or a crash (matches the project rule).
- **Cheap by construction**: catalog is static JSON behind cache-busting; the only translated locale fetched is the active one; fonts subset per script. No request storm, no per-tab fan-out (honors the FLYWHEEL performance bar).
- **Cloud inherits automatically** via the wheel pin — no parallel cloud i18n to maintain.
- **Upgrade path documented**: if quality ever demands humans, drop the bot's auto-merge and point Weblate/Crowdin at `locales/` (it's the format they all natively consume). Nothing else changes.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Machine translation reads slightly off (idioms, marketing) | Glossary + Opus for landing copy + pseudolocale catches layout, not tone; community can PR fixes to any `<lang>.json` and the bot leaves human-edited keys alone (mark `"_locked": true`). |
| Layout breaks on long translations (de/ta/fi) | Pseudolocale (+30%) in CI surfaces it pre-launch; flag >2× length; prefer flexible chips over fixed widths. |
| Tofu boxes for CJK/Indic | Noto subsets per script, `unicode-range`-scoped, lazy per active locale. |
| 16.5k-line `app.js` extraction misses strings | Pseudolocale = exhaustive visual audit; CI lint blocks unmarked text; codemod does the bulk pass. |
| Editing the dead `DASHBOARD_HTML` (line 2988) | Documented: the **second** block (10831) is live; runtime/loader changes go there + the static/template files. |
| Bot mangles `{placeholders}` / markdown links | Post-translation integrity lint fails the sync PR. |
| RTL half-done looks worse than not done | Explicitly phased out of v1; LTR-only until the logical-property CSS pass lands. |
| Translation API cost | Delta-only translation; steady-state is pennies/PR; one-time backfill is the only spike. |

---

## 9. Success metrics
- **Coverage**: pseudolocale shows <1% un-accented user-facing text across dashboard + landing.
- **Completeness**: every enabled locale has 100% of `en.json` keys (CI-asserted).
- **Detection accuracy**: a fresh visitor with `Accept-Language: ja` lands in Japanese with no interaction; switching to Français persists across reloads.
- **Consistency**: a language picked on the landing carries into `app.clawmetry.com` (and back) with zero re-selection — verified via the `.clawmetry.com` cookie surviving navigation, reload, and surface-hop. (§3.8)
- **SEO**: `curl https://clawmetry.com/ja/pricing` returns Japanese text in the initial HTML (not English + JS); `hreflang` alternates + canonical validate; the multilingual sitemap lists every locale URL; Search Console shows the language set indexed.
- **Performance unchanged**: only one locale JSON + one script-scoped font set fetched; no new per-tab poller; Network panel shows no regression (FLYWHEEL bar).
- **Maintenance**: a PR adding a new English string ships translated to all ~30+ languages with zero human translation work.

---

## 10. Open decisions (my calls, flag to override)
1. **Custom `t()` runtime vs Polyglot.js vs i18next-CDN** → **custom ~120-line runtime** (zero dep, fits no-build best). Swap to Polyglot if hand-rolling plurals gets fiddly.
2. **English-string-as-key vs dotted keys** → **English-as-key hybrid** (explicit keys only for placeholder/ambiguous strings). Fastest migration, best LLM context.
3. **Where the PRD/catalog lives** → OSS repo (`clawmetry/locales/`), shipped in the wheel; cloud + landing reuse it.
4. **README structure** → root English canonical + `docs/i18n/<lang>/README.md` + a top-of-file language bar.
5. **Switcher labels** → native endonyms, never translated.
6. **Landing locale rendering** → **server-rendered locale subpaths** (`/<lang>/`) for SEO. Sub-decision (4.2a Flask route-prefix vs 4.2b CI pre-render) → lean **route-prefix** for one canonical render path; switch to pre-render if we move the landing to pure static hosting. Flag to override.
7. **Consistency mechanism** → domain-wide `cm-lang` cookie on `.clawmetry.com` + `localStorage` mirror + URL locale on landing, kept in sync on every switch (§3.8).

---

🤖 Drafted by Claude Code. Honors CLAUDE.md (no build step, minimal deps, never-crash, no em-dashes in user copy) and FLYWHEEL.md (performance budget, DuckDB-irrelevant here since i18n is pure chrome, verify-live before "done").
