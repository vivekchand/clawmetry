#!/usr/bin/env node
/**
 * Pseudolocale (en-XA) gate: verifies locale machinery is live and
 * surfaces un-extracted UI strings per tab.
 *
 * TWO DIFFERENT THINGS, TWO DIFFERENT SEVERITIES. Conflating them is
 * what kept this script out of CI (#2258):
 *
 *   1. MACHINERY  — is the pseudolocale actually applied, does the
 *      switcher list en-XA, does the locale survive a tab switch.
 *      These are invariants, not a backlog. They ALWAYS exit 1.
 *   2. RESIDUAL   — how many un-extracted English strings are left on
 *      each tab. This IS a backlog being worked down, so it is soft by
 *      default. STRICT=1 demands zero; MAX_RESIDUAL=<n> is the ratchet
 *      in between, failing only when the backlog GROWS.
 *
 * Until 2026-09-11 a single STRICT flag governed both, so the only
 * exit-1 path was `STRICT && fail > 0`. Without STRICT the script
 * printed "Locale machinery verified" and exited 0 even when the
 * machinery check had just failed, which made it useless as a gate:
 * wiring it into CI would have added a job that could not go red.
 *
 * Requires a running ClawMetry OSS dashboard at CLAWMETRY_URL
 * (default http://localhost:8900). Unreachable means SKIP when run by
 * hand, but REQUIRE_DASHBOARD=1 turns that into a failure so a CI job
 * cannot pass by never testing anything.
 *
 * Run:
 *   node tests/e2e/pseudolocale.mjs
 *   HEADLESS=0          node tests/e2e/pseudolocale.mjs  # show browser
 *   STRICT=1            node tests/e2e/pseudolocale.mjs  # demand zero residual
 *   MAX_RESIDUAL=40     node tests/e2e/pseudolocale.mjs  # ratchet
 *   REQUIRE_DASHBOARD=1 node tests/e2e/pseudolocale.mjs  # no silent skip
 *   CLAWMETRY_URL=http://localhost:9000 node tests/e2e/pseudolocale.mjs
 *
 * Exits 1 when a machinery check fails, when the dashboard is required
 * and absent, when STRICT=1 and any string is un-extracted, or when
 * MAX_RESIDUAL is set and the residual count exceeds it.
 */
import { chromium } from 'playwright';

const BASE_URL = process.env.CLAWMETRY_URL || 'http://localhost:8900';
const HEADLESS  = process.env.HEADLESS !== '0';
const STRICT    = process.env.STRICT === '1';
const PAUSE_MS  = HEADLESS ? 1200 : 2500;
// A CI job that quietly passes when the dashboard never booted is worse
// than no job at all: it reports a verdict it did not reach.
const REQUIRE_DASHBOARD = process.env.REQUIRE_DASHBOARD === '1';
// Ratchet. Unset means "report only"; a number fails when the residual
// backlog grows past it, without demanding the zero that STRICT does.
const MAX_RESIDUAL = process.env.MAX_RESIDUAL === undefined
  ? null
  : Number.parseInt(process.env.MAX_RESIDUAL, 10);

// High-coverage tabs to walk. Add more as the catalog converges.
const TABS = [
  'Overview',
  'Brain',
  'Sessions',
  'Health',
  'Crons',
  'Cost',
  'Memory',
  'Logs',
  'Config',
];

// Words/patterns that are legitimately in plain English and must not be
// wrapped in t() — model families, product names, short tokens, URLs.
const WHITELIST_PATTERNS = [
  /^claude/i, /^gpt/i, /^llama/i, /^gemini/i, /^qwen/i, /^mistral/i,
  /^openclaw/i, /^clawmetry/i, /^nemoclaw/i, /^opencode/i, /^cursor/i,
  /^\d[\d.,kKmMbB%$€£¥]*$/,
  /^[a-z0-9._+\-/]{1,3}$/i,
  /^https?:/i,
  /^[A-Z]{2,5}$/,
  /^[a-z]{1,3}$/i,
];

function isWhitelisted(word) {
  return WHITELIST_PATTERNS.some(p => p.test(word));
}

/**
 * Extract plain-English words (≥4 chars) that are NOT inside ⟦…⟧
 * brackets, skipping known raw-data containers so we don't flag
 * session transcripts, tool outputs, or log content.
 */
async function findUnextractedWords(page) {
  return page.evaluate(() => {
    const SKIP_SELECTORS = [
      'pre', 'code', 'script', 'style',
      '.log-line', '.log-output', '.transcript-content',
      '.session-message', '.tool-result', '.tool-call-body',
      '[data-raw]', '.json-viewer', '.code-block',
      '.cm-brain-event-body', '.cm-tool-output',
    ].join(',');

    const clone = document.body.cloneNode(true);
    clone.querySelectorAll(SKIP_SELECTORS).forEach(n => n.remove());

    const text = clone.innerText || '';
    const words = [];
    // Split on translated segments (⟦…⟧) and scan only the gaps.
    for (const chunk of text.split(/⟦[^⟧]*⟧/u)) {
      const found = chunk.match(/\b[a-zA-Z]{4,}\b/g);
      if (found) words.push(...found);
    }
    return [...new Set(words)];
  });
}

let pass = 0;
let fail = 0;
const failures = [];

function check(label, ok, detail) {
  if (ok) {
    pass++;
    console.log(`  ✓ ${label}`);
  } else {
    fail++;
    failures.push(label + (detail ? `\n      ${detail}` : ''));
    console.log(`  ✗ ${label}${detail ? `\n      ${detail}` : ''}`);
  }
}

async function main() {
  console.log(`[pseudolocale] target : ${BASE_URL}/?lang=en-XA`);
  console.log(`[pseudolocale] strict : ${STRICT}`);
  console.log(`[pseudolocale] tabs   : ${TABS.join(', ')}\n`);

  // Probe the dashboard before launching Playwright.
  //
  // Retried, and not on a 4s single shot. `/api/overview` fans out over the
  // whole store, and measured on a node with real history the first call took
  // 4.18s against exactly that timeout while the next two took 1.3s. A gate
  // that reports "dashboard not reachable" because one cold call was 180ms
  // late is a flaky gate, and a flaky gate gets ignored rather than fixed.
  const PROBE_ATTEMPTS = 5;
  const PROBE_TIMEOUT_MS = 15000;
  let reachable = false;
  for (let attempt = 1; attempt <= PROBE_ATTEMPTS && !reachable; attempt++) {
    try {
      const r = await fetch(`${BASE_URL}/api/overview`, {
        signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
      });
      reachable = r.status < 500;
    } catch {}
    if (!reachable && attempt < PROBE_ATTEMPTS) {
      console.log(`[pseudolocale] probe ${attempt}/${PROBE_ATTEMPTS} failed, retrying`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  if (!reachable) {
    if (REQUIRE_DASHBOARD) {
      console.error(`[pseudolocale] FAIL: dashboard required but not reachable at ${BASE_URL}.`);
      console.error('  REQUIRE_DASHBOARD=1 is set, so this is a failure rather than a skip:');
      console.error('  a gate that passes without testing anything is not a gate.');
      process.exit(1);
    }
    console.log(`[pseudolocale] SKIP: dashboard not reachable at ${BASE_URL}.`);
    console.log('  Start it with:  clawmetry  (or: python3 dashboard.py --port 8900)');
    process.exit(0);
  }

  const browser = await chromium.launch({
    headless: HEADLESS,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined,
  });
  const ctx  = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  // ── 1. Navigate with ?lang=en-XA ────────────────────────────────────
  console.log('▸ Navigating to dashboard with ?lang=en-XA');
  await page.goto(`${BASE_URL}/?lang=en-XA`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  // ── 2. Verify pseudolocale is active ─────────────────────────────────
  const bodyText    = await page.evaluate(() => document.body.innerText || '');
  const bracketHits = (bodyText.match(/⟦/g) || []).length;
  check(
    'pseudolocale active: ⟦…⟧ markers visible on first load',
    bracketHits > 0,
    `found ${bracketHits} bracket(s)`
  );

  // ── 3. Confirm locale switcher lists en-XA ───────────────────────────
  const globeBtn = page.locator(
    '[aria-label*="language" i], .lang-switcher, .globe-icon, [data-lang-trigger], .cm-lang-btn'
  ).first();
  if ((await globeBtn.count()) > 0) {
    await globeBtn.click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(500);
    const menuText = await page.evaluate(() => document.body.innerText);
    const hasXA = menuText.includes('Pseudo') || menuText.includes('XA') || menuText.includes('en-XA');
    check('locale switcher shows en-XA option', hasXA);
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(300);
  }

  // ── 4. Walk tabs ─────────────────────────────────────────────────────
  console.log('\n▸ Walking tabs');
  const tabReport = {};

  for (const tabName of TABS) {
    const navItem = page.locator(
      `[data-tab="${tabName.toLowerCase()}"], .nav-tab:has-text("${tabName}"), [role="tab"]:has-text("${tabName}")`
    ).first();

    if ((await navItem.count()) === 0) {
      console.log(`  — ${tabName}: nav item not found, skipping`);
      continue;
    }

    await navItem.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(PAUSE_MS);

    // Confirm locale is still active after the tab switch.
    const tabBody    = await page.evaluate(() => document.body.innerText || '');
    const tabBrackets = (tabBody.match(/⟦/g) || []).length;
    check(`${tabName}: locale active after tab switch`, tabBrackets > 0, `brackets: ${tabBrackets}`);

    // Scan for un-extracted words.
    const allWords = await findUnextractedWords(page);
    const leaking  = allWords.filter(w => !isWhitelisted(w));
    tabReport[tabName] = leaking;

    if (leaking.length === 0) {
      console.log(`  ✓ ${tabName}: no un-extracted strings`);
    } else {
      const preview = leaking.slice(0, 8).join(', ');
      const msg = `${leaking.length} un-extracted word(s): ${preview}${leaking.length > 8 ? ', …' : ''}`;
      // Residual strings are counted, never fed to check(): check() is
      // machinery only, and mixing them is what made a dead switcher
      // indistinguishable from an unfinished backlog.
      console.log(`  ⚠ ${tabName}: ${msg}`);
    }
  }

  // ── 5. Summary ───────────────────────────────────────────────────────
  const leakyTabs   = Object.entries(tabReport).filter(([, w]) => w.length > 0);
  const totalLeaking = leakyTabs.reduce((s, [, w]) => s + w.length, 0);

  console.log('\n▸ Un-extracted string summary (first 6 per tab):');
  if (leakyTabs.length === 0) {
    console.log('  (none — full coverage!)');
  } else {
    for (const [tab, words] of leakyTabs) {
      const extra = words.length > 6 ? ` … (+${words.length - 6} more)` : '';
      console.log(`  ${tab}: ${words.slice(0, 6).join(', ')}${extra}`);
    }
  }

  await browser.close();

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`  ${pass} passed, ${fail} failed`);
  console.log(`  ${totalLeaking} un-extracted string(s) across ${leakyTabs.length} tab(s)`);

  // Machinery first, and unconditionally. A broken locale switcher is not
  // a backlog item, and saying "verified" over one is how this script
  // managed to report success on a dashboard where nothing was localised.
  if (fail > 0) {
    console.log('\nMachinery failures:');
    failures.forEach(f => console.log(`  • ${f}`));
    console.log('\n  ❌ Locale machinery is broken. This is not the residual backlog.');
    process.exit(1);
  }

  console.log('  ✅ Locale machinery verified');

  if (STRICT && totalLeaking > 0) {
    console.log(`\n  ❌ STRICT=1 and ${totalLeaking} un-extracted string(s) remain.`);
    process.exit(1);
  }
  if (MAX_RESIDUAL !== null && Number.isFinite(MAX_RESIDUAL) && totalLeaking > MAX_RESIDUAL) {
    console.log(`\n  ❌ residual backlog grew: ${totalLeaking} un-extracted string(s), ` +
                `ratchet allows ${MAX_RESIDUAL}.`);
    console.log('  Extract the new strings, or raise MAX_RESIDUAL deliberately and say why.');
    process.exit(1);
  }
  if (totalLeaking > 0) {
    console.log(`  (${totalLeaking} un-extracted string(s) within budget` +
                `${MAX_RESIDUAL !== null ? ` of ${MAX_RESIDUAL}` : ''}; ` +
                'STRICT=1 demands zero)');
  }
}

main().catch(err => {
  console.error('\n[pseudolocale] FATAL:', err);
  process.exit(1);
});
