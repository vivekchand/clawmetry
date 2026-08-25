// README screenshot capture — Playwright against a live dashboard (default :8900).
// Shoots the marketing set with the runtime filter cleared, so every cost
// window (today / week / month) is populated instead of a runtime-scoped view
// where two of the three read $0.00 and the app looks broken.
// Usage: node capture-readme.mjs [--base http://localhost:8900] [--out ../../screenshots/_new]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const BASE = arg('base', 'http://localhost:8900');
const OUT = path.resolve(arg('out', new URL('../../screenshots/_new', import.meta.url).pathname));

const HIDE_CSS = `
  [id*="banner" i],#version-badge,#cm-device-pill,#update-banner,
  .cm-banner,.sync-banner,#cookie-consent,#consent-banner {display:none !important;}
`;

// data-tab id -> shot name
const SHOTS = [
  ['overview', 'overview'],
  ['flow', 'flow'],
  ['usage', 'cost'],
  ['transcripts', 'sessions'],
  ['tracing', 'tracing'],
  ['agents', 'agents'],
  ['brain', 'activity'],
  ['alerts', 'alerts'],
  ['evals', 'quality'],
  ['inventory', 'agents-inventory'],
  ['tool-catalog', 'tools'],
  ['memory', 'memory'],
  ['skills', 'skills'],
  ['security', 'security'],
  ['policy', 'policy'],
  ['context-economics', 'context'],
  ['models', 'models'],
  ['crons', 'crons'],
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1680, height: 1000 }, deviceScaleFactor: 2 });
await ctx.addInitScript(() => {
  try {
    localStorage.removeItem('cm-runtime-filter');   // All runtimes
    localStorage.setItem('cm_ab_pill_dismissed', '1');
  } catch {}
});
const page = await ctx.newPage();
await page.goto(BASE, { waitUntil: 'networkidle' }).catch(() => {});
await page.waitForTimeout(4000);
fs.mkdirSync(OUT, { recursive: true });

for (const [tab, name] of SHOTS) {
  try {
    await page.evaluate((t) => window.switchTab && window.switchTab(t), tab);
    await page.waitForTimeout(3000);
    // Wait until the tab has actually rendered numbers: several panels lazy-load
    // on switch and shoot as "--" placeholders if you fire the camera too early.
    await page.waitForFunction(() => {
      const el = document.querySelector('.tab-content:not([style*="none"])') || document.body;
      const t = (el.innerText || '');
      return t.length > 200 && !/^\s*$/.test(t);
    }, { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(6000);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    await page.addStyleTag({ content: HIDE_CSS }).catch(() => {});
    await page.screenshot({ path: path.join(OUT, name + '.png') });
    console.log('shot', name);
  } catch (e) { console.warn('FAIL', name, e.message); }
}
await ctx.close();
await browser.close();
console.log('done ->', OUT);
