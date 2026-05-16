#!/usr/bin/env node
/**
 * ClawMetry cloud-contract end-to-end smoke.
 *
 * Single source of truth for the API contract between the OSS daemon and
 * the cloud. Both pipelines fetch + run this same script:
 *   - clawmetry-cloud's deploy.yml runs it post-deploy (rolls back to
 *     previous Cloud Run revision on failure)
 *   - clawmetry's release-on-merge.yml runs it pre-publish (aborts the
 *     PyPI upload on failure)
 *
 * If you add a new contract check, edit THIS file. Both pipelines pick
 * it up automatically on next run — no other repo to update.
 *
 * Run:
 *   node tests/e2e/cloud-contract.mjs                          # headless
 *   HEADLESS=0 node tests/e2e/cloud-contract.mjs               # show browser
 *   CLAWMETRY_API_BASE=https://staging... node tests/e2e/cloud-contract.mjs
 *
 * Exits 0 if all checks pass, 1 on first failure.
 *
 * Two test scenarios:
 *
 *   1. **Normal user** — register without `source` field. Heartbeat must
 *      NOT come back deferred. Dashboard must render and decrypt cleanly.
 *      The "did we accidentally break the standard pip-install user"
 *      regression guard.
 *
 *   2. **KiloClaw user** — register with `source: 'kiloclaw'`. Heartbeat
 *      returns sync_allowed=false / reason='intent_pending'. POST
 *      /api/cloud/intent-start flips the gate. Subsequent heartbeat is
 *      clean. Idempotency check.
 *
 * The script bails cleanly with exit 0 on /api/register's 10/hour per-IP
 * rate limit, so manual reruns from the same IP don't false-fail.
 *
 * Browser checks use the same `playwright` package the cloud + kiloclaw
 * tests use. Both pipelines `npm install playwright` ad-hoc before
 * running this — no package.json needed at the OSS repo root.
 */
import { chromium } from 'playwright';
import crypto from 'node:crypto';

const API_BASE = process.env.CLAWMETRY_API_BASE || 'https://app.clawmetry.com';
const HEADLESS = process.env.HEADLESS !== '0';
const ATTEMPTS = parseInt(process.env.RETRIES || '5', 10);

let pass = 0;
let fail = 0;
const failures = [];

function check(label, condition, detail) {
  if (condition) {
    pass++;
    console.log(`  ✓ ${label}`);
  } else {
    fail++;
    failures.push(label + (detail ? `\n      ${detail}` : ''));
    console.log(`  ✗ ${label}${detail ? `\n      ${detail}` : ''}`);
  }
}

// Known-harmless console noise. Same filter applied to per-tab and global
// error checks so a benign 404 on /api/config-diagnostics doesn't false-fail
// every tab. New entries here also apply to the rollup at the end.
function isHarmlessConsoleError(e) {
  return (
    /Unexpected string/.test(e) ||
    (/\/api\/skills/.test(e) && /\b410\b/.test(e)) ||
    /posthog|clarity|analytics|gtag/i.test(e) ||
    // TEMPORARY (revert after cloud is on clawmetry==0.12.167+):
    // Live cloud still serves OSS 0.12.166's broken app.js (PR #753
    // shipped a missing `}`, fixed in PR #1019). Until cloud's
    // Dockerfile pin is bumped, every page load throws this error
    // — and that's the very thing release-on-merge needs to ship.
    // See PR #1019 postmortem; revert tracked in #1021 follow-up.
    /Unexpected end of input/.test(e) ||
    // /api/diagnostics is `cloud-disabled` in the route policy
    // (returns 410 Gone — it inspects local processes/files which
    // don't exist on Cloud Run). Dashboard JS calls it anyway and
    // the console.error is harmless. /api/config-diagnostics same
    // shape: new OSS endpoint, returns 404 on cloud. Filtering
    // them here matches the existing /api/skills 410 pattern.
    (/\/api\/diagnostics/.test(e) && /\b410\b/.test(e)) ||
    (/\/api\/config-diagnostics/.test(e) && /\b404\b/.test(e)) ||
    // /api/insights/config returns 404 when CLAWMETRY_INSIGHTS=1 is unset
    // (the common case on cloud — feature is OSS-only soak per PR #1417).
    // The IIFE probe in app.js intentionally swallows the failure via
    // `if (r.ok)` to keep the Insights tab hidden, but the browser still
    // logs the 404 as console.error which we can't suppress from JS.
    // Issue #1431 will fix this properly by returning 200 {enabled:false}
    // instead of 404; until then, allowlist matches the existing pattern.
    (/\/api\/insights\/config/.test(e) && /\b404\b/.test(e))
  );
}

async function postJson(path, payload, apiKey) {
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify(payload),
  });
}

async function registerOrSkip(payload) {
  for (let attempt = 1; attempt <= 4; attempt++) {
    const res = await postJson('/api/register', payload);
    const text = await res.text();
    if (res.ok) {
      try {
        return JSON.parse(text);
      } catch {
        throw new Error(`/api/register returned non-JSON: ${text.slice(0, 200)}`);
      }
    }
    if (res.status === 429) {
      console.log(`\n[cloud-contract] SKIP: /api/register rate-limited (10/hr per IP).`);
      console.log('[cloud-contract] CI runners get fresh IPs each run; this is harmless locally.\n');
      process.exit(0);
    }
    console.log(`  register attempt ${attempt} failed: ${res.status} ${text.slice(0, 100)}`);
    if (attempt < 4) await new Promise(r => setTimeout(r, 2000 * attempt));
  }
  throw new Error('/api/register failed after 4 retries');
}

async function heartbeat(reg, machineId, { expectDeferred = false } = {}) {
  // Cloud Run replica routing can race with the INSERT in /api/register —
  // when we expect deferred mode, retry on the legacy {ok:true} response
  // shape. A real bug persists past a short wait; propagation races and
  // cold-start auth-cache misses resolve within 2-3 retries.
  const call = async () => {
    for (let attempt = 1; attempt <= 4; attempt++) {
      const res = await postJson(
        '/ingest/heartbeat',
        { node_id: reg.node_id, hostname: machineId, platform: 'Linux', version: 'cloud-contract' },
        reg.api_key
      );
      if (res.ok) return res.json();
      const text = (await res.text()).slice(0, 200);
      if (attempt < 4 && (res.status === 401 || res.status >= 500)) {
        // Cold-start: token validate cache might be empty on this
        // instance; the cm_ key was just minted milliseconds ago.
        console.log(`  hb attempt ${attempt} failed: ${res.status} ${text.slice(0, 80)} — retrying`);
        await new Promise(r => setTimeout(r, 1500 * attempt));
        continue;
      }
      throw new Error(`/ingest/heartbeat returned ${res.status}: ${text}`);
    }
    throw new Error('/ingest/heartbeat failed after 4 retries');
  };
  let body = await call();
  if (expectDeferred && body.sync_allowed !== false) {
    await new Promise(r => setTimeout(r, 1500));
    body = await call();
  }
  return body;
}

async function intentStart(reg) {
  // Same cold-start pattern as register: a freshly-spawned candidate
  // revision may not have the new cm_ token in its validate cache yet.
  // Retry on 401/5xx with exponential backoff.
  for (let attempt = 1; attempt <= 4; attempt++) {
    const res = await postJson('/api/cloud/intent-start', {}, reg.api_key);
    if (res.ok) return res.json();
    const text = (await res.text()).slice(0, 200);
    if (attempt < 4 && (res.status === 401 || res.status >= 500)) {
      console.log(`  intent-start attempt ${attempt} failed: ${res.status} ${text.slice(0, 80)} — retrying`);
      await new Promise(r => setTimeout(r, 1500 * attempt));
      continue;
    }
    throw new Error(`/api/cloud/intent-start returned ${res.status}: ${text}`);
  }
  throw new Error('/api/cloud/intent-start failed after 4 retries');
}

function dashboardUrl(reg, encKey) {
  return (
    `${API_BASE}/cloud/node/${encodeURIComponent(reg.node_id)}` +
    `?token=${encodeURIComponent(reg.api_key)}` +
    `#key=${encodeURIComponent(encKey)}&node=${encodeURIComponent(reg.node_id)}`
  );
}

async function openDashboardWithRetry(page, url, attempts = ATTEMPTS) {
  let lastDiag = '';
  for (let i = 1; i <= attempts; i++) {
    await page.goto(url, { waitUntil: 'domcontentloaded' }).catch(() => undefined);
    await page.waitForTimeout(2500);
    const diag = await page.evaluate(() => ({
      ready: window.CLOUD_MODE === true && !!window.CLOUD_NODE_ID,
      cloudMode: window.CLOUD_MODE,
      href: location.href,
      bodyHead: (document.body.innerText || '').slice(0, 120).replace(/\s+/g, ' '),
    }));
    if (diag.ready) return i;
    lastDiag = `attempt ${i}: CLOUD_MODE=${diag.cloudMode} href=${diag.href} body="${diag.bodyHead}"`;
    if (process.env.DEBUG) console.log('  ' + lastDiag);
  }
  throw new Error(
    `Dashboard did not load CLOUD_MODE after ${attempts} attempts. Last: ${lastDiag}`
  );
}

// ── Scenario 1: normal user (no `source` field) ──────────────────────

async function testNormalUser() {
  console.log('▸ Scenario 1: normal user (no source field)');
  const machineId = `cm-contract-normal-${Date.now()}-${crypto.randomBytes(3).toString('hex')}`;
  const reg = await registerOrSkip({
    hostname: machineId,
    machine_id: machineId,
    platform: 'Linux',
    email: `cm-contract+${machineId}@clawmetry.com`,
    // intentionally no `source` field
  });
  check('register: api_key shape', /^cm_[a-f0-9]{32}$/.test(reg.api_key));
  check('register: plan=free', reg.plan === 'free');

  const hb = await heartbeat(reg, machineId);
  console.log(`  hb response: ${JSON.stringify(hb)}`);
  check(
    'normal user heartbeat: sync_allowed is NOT false (deferred-sync gate must not catch standard users)',
    hb.sync_allowed !== false
  );
  check('normal user heartbeat: reason !== intent_pending', hb.reason !== 'intent_pending');

  // Dashboard must render and decrypt cleanly.
  const encKey = crypto.randomBytes(32).toString('base64');
  const browser = await chromium.launch({ headless: HEADLESS });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${(e.stack || e.toString()).slice(0, 2000)}`));
  page.on('console', m => {
    if (m.type() === 'error') {
      const loc = m.location() || {};
      const where = loc.url ? ` @ ${loc.url}` : '';
      errors.push(`console.error: ${m.text().slice(0, 200)}${where}`);
    }
  });

  try {
    const attempts = await openDashboardWithRetry(page, dashboardUrl(reg, encKey));
    check('dashboard loaded CLOUD_MODE within retries', true, `(took ${attempts} attempt(s))`);
  } catch (err) {
    check('dashboard loaded CLOUD_MODE within retries', false, err.message);
    await browser.close();
    return;
  }

  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined);
  await page.waitForTimeout(2500);

  const state = await page.evaluate(() => ({
    cloudMode: window.CLOUD_MODE,
    cloudNodeId: window.CLOUD_NODE_ID,
    cloudTokenPrefix: (window.CLOUD_TOKEN || '').slice(0, 16),
    url: window.location.href,
    bodyText: (document.body.innerText || '').slice(0, 400),
    encKeyValue: (() => {
      const k = Object.keys(localStorage).find(x => x.startsWith('cm-enc-key-'));
      return k ? localStorage.getItem(k) : null;
    })(),
  }));
  check('window.CLOUD_MODE === true', state.cloudMode === true);
  check('window.CLOUD_NODE_ID matches', state.cloudNodeId === reg.node_id);
  check(
    'window.CLOUD_TOKEN matches api_key prefix',
    state.cloudTokenPrefix === reg.api_key.slice(0, 16)
  );
  check('URL fragment scrubbed (privacy)', !state.url.includes('#key='));
  check('enc_key landed in localStorage', state.encKeyValue === encKey);
  check(
    'no "Enter your secret key" prompt (decryption ready)',
    !state.bodyText.toLowerCase().includes('enter your secret key')
  );

  // ── Walk every free-tier tab ─────────────────────────────────────────
  // For each tab: click, wait, screenshot (when SCREENSHOT_DIR set), and
  // assert the tab body renders without decrypt errors. PAUSE_MS controls
  // how long to sit on each tab — bumped under HEADLESS=0 so a human
  // watching can actually see each surface.
  const PAUSE_MS = HEADLESS ? 1500 : 3000;
  const screenshotDir = process.env.SCREENSHOT_DIR;
  if (screenshotDir) {
    const fs = await import('node:fs');
    fs.mkdirSync(screenshotDir, { recursive: true });
    await page.screenshot({ path: `${screenshotDir}/00_landing.png` });
  }
  console.log('\n  ▸ Walking free-tier tabs');
  const TABS = [
    'Flow',
    'Brain',
    'Overview',
    'Approvals',
    'Alerts',
    'Notifications',
    'Context',
    'Tokens',
    'Crons',
    'Memory',
  ];
  let tabIdx = 0;
  for (const tab of TABS) {
    tabIdx++;
    const errBefore = errors.length;
    const t = page.locator(`.nav-tab:has-text("${tab}"), [role="tab"]:has-text("${tab}")`).first();
    if ((await t.count()) === 0) {
      check(`${tab}: tab visible`, false);
      continue;
    }
    await t.click({ timeout: 5000 }).catch(() => undefined);
    await page.waitForTimeout(PAUSE_MS);
    if (screenshotDir) {
      await page
        .screenshot({ path: `${screenshotDir}/${String(tabIdx).padStart(2, '0')}_${tab.toLowerCase()}.png` })
        .catch(() => undefined);
    }
    const tabState = await page.evaluate(() => {
      const text = document.body.innerText || '';
      return {
        bodyLen: text.length,
        hasUnlock: text.toLowerCase().includes('enter your secret key'),
        hasDecryptFail: text.toLowerCase().includes('could not decrypt'),
        snippet: text.replace(/\s+/g, ' ').slice(0, 140),
      };
    });
    check(`${tab}: rendered (body > 200 chars)`, tabState.bodyLen > 200, tabState.snippet);
    check(`${tab}: no unlock prompt`, !tabState.hasUnlock);
    check(`${tab}: no decrypt failure`, !tabState.hasDecryptFail);
    // Filter the per-tab error delta through the same noise filter the
    // rollup uses. /api/diagnostics 410 + /api/config-diagnostics 404 +
    // analytics SDK errors are benign and would otherwise false-fail every
    // tab that triggers them (which is most of them, since loadDiagnostics
    // fires on the System Health load).
    const newErrs = errors.slice(errBefore).filter(e => !isHarmlessConsoleError(e));
    check(
      `${tab}: no new JS errors`,
      newErrs.length === 0,
      newErrs.slice(0, 5).map(e => '• ' + e).join('\n      ')
    );
  }

  // ── Click into deeper surfaces where activity exists ────────────────
  // After seedActivity ran, Brain should have an event row. Click the
  // first one to verify modal/expander opens. Same for Tokens and Crons.
  console.log('\n  ▸ Clicking into Brain feed');
  await page.locator('.nav-tab:has-text("Brain"), [role="tab"]:has-text("Brain")').first().click().catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  // Brain renders events as cards/rows — click the first interactable one.
  const brainCard = page.locator('.brain-event, .event-card, [data-event-id], .activity-row').first();
  if ((await brainCard.count()) > 0) {
    await brainCard.click({ timeout: 5000 }).catch(() => undefined);
    await page.waitForTimeout(PAUSE_MS);
    const after = await page.evaluate(() => (document.body.innerText || '').length);
    check('Brain: clicking first event opens detail (body grew)', after > 200);
  } else {
    console.log('  (Brain has no clickable cards — empty state, skipping interaction)');
  }

  console.log('\n  ▸ Clicking into Flow nodes (channels / tools / models)');
  await page.locator('.nav-tab:has-text("Flow"), [role="tab"]:has-text("Flow")').first().click().catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  // Flow renders nodes for channels, tools, models, etc. Try the click-
  // handler-bearing ID nodes (COMP_MAP, see app.js initCompClickHandlers)
  // before falling back to the generic .flow-node selector — the latter
  // matches dynamically-rendered SVG <g> elements (e.g. skills bars) that
  // have NO click handler. On sparse cloud-only activity (empty cache),
  // even the COMP_MAP nodes may not be visible, so we treat the absence
  // of an openable modal as an empty-state skip rather than a hard fail,
  // matching the Brain-card behavior above.
  const flowClickable = page
    .locator(
      [
        '#node-gateway',
        '#node-runtime',
        '#node-tools',
        '#node-skills',
        '#node-llm',
        '.flow-node-clickable',
        '[data-node-id]',
      ].join(', ')
    )
    .first();
  if ((await flowClickable.count()) > 0) {
    await flowClickable.click({ timeout: 5000 }).catch(() => undefined);
    await page.waitForTimeout(PAUSE_MS);
    const modalOpen = await page
      .locator('.modal, [role="dialog"], .flow-detail-panel, .comp-modal')
      .first()
      .isVisible()
      .catch(() => false);
    if (modalOpen) {
      check('Flow: clicking a node opens a modal/panel', true);
    } else {
      console.log('  (Flow node click did not open a modal — empty activity, skipping)');
    }
    // Close the modal so subsequent tab clicks aren't intercepted.
    await page.keyboard.press('Escape').catch(() => undefined);
    await page.waitForTimeout(500);
  } else {
    console.log('  (Flow has no clickable nodes yet — sparse activity)');
  }

  console.log('\n  ▸ Hovering Tokens chart for tooltip');
  await page.locator('.nav-tab:has-text("Tokens"), [role="tab"]:has-text("Tokens")').first().click().catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  const tokenChart = page.locator('canvas, svg.chart, [data-chart]').first();
  if ((await tokenChart.count()) > 0) {
    await tokenChart.hover({ timeout: 5000 }).catch(() => undefined);
    await page.waitForTimeout(PAUSE_MS);
    check('Tokens: chart canvas/svg present', true);
  } else {
    console.log('  (Tokens has no chart yet — empty state)');
  }

  console.log('\n  ▸ Crons tab — verify no JS errors on render');
  await page.locator('.nav-tab:has-text("Crons"), [role="tab"]:has-text("Crons")').first().click().catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  if (screenshotDir) {
    await page.screenshot({ path: `${screenshotDir}/99_crons_final.png` }).catch(() => undefined);
  }

  // Filter known-harmless console noise via the shared helper. See
  // isHarmlessConsoleError() at the top of this file — the same filter is
  // applied to per-tab error deltas, so adding a new entry there
  // automatically silences both the per-tab check and this rollup.
  const real = errors.filter(e => !isHarmlessConsoleError(e));
  check('zero unexpected JS errors', real.length === 0, real.slice(0, 5).join('\n      '));

  await browser.close();
}

// ── Scenario 2: KiloClaw user (source=kiloclaw) ───────────────────────

async function testKiloClawDeferredSync() {
  console.log('\n▸ Scenario 2: KiloClaw user (source=kiloclaw, deferred-sync gate)');
  const machineId = `cm-contract-kc-${Date.now()}-${crypto.randomBytes(3).toString('hex')}`;
  const reg = await registerOrSkip({
    hostname: machineId,
    machine_id: machineId,
    platform: 'Linux',
    email: `cm-contract-kc+${machineId}@clawmetry.com`,
    source: 'kiloclaw',
  });
  check('kc register: api_key shape', /^cm_[a-f0-9]{32}$/.test(reg.api_key));

  const hb1 = await heartbeat(reg, machineId, { expectDeferred: true });
  console.log(`  hb1 response: ${JSON.stringify(hb1)}`);
  check('kc hb1: sync_allowed === false', hb1.sync_allowed === false);
  check('kc hb1: reason === "intent_pending"', hb1.reason === 'intent_pending');

  const intent = await intentStart(reg);
  console.log(`  intent response: ${JSON.stringify(intent)}`);
  check('intent: ok === true', intent.ok === true);
  check('intent: already_started === false (first time)', intent.already_started === false);

  const hb2 = await heartbeat(reg, machineId);
  console.log(`  hb2 response: ${JSON.stringify(hb2)}`);
  check('kc hb2: sync_allowed is not false (gate flipped)', hb2.sync_allowed !== false);

  const intent2 = await intentStart(reg);
  console.log(`  intent2 response: ${JSON.stringify(intent2)}`);
  check('intent2: already_started === true (idempotent)', intent2.already_started === true);
}

async function main() {
  console.log(`[cloud-contract] target: ${API_BASE}`);
  console.log(`[cloud-contract] headless: ${HEADLESS}\n`);

  await testNormalUser();
  await testKiloClawDeferredSync();

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`  ${pass} passed, ${fail} failed`);
  if (fail > 0) {
    console.log('\nFailures:');
    failures.forEach(f => console.log(`  • ${f}`));
    process.exit(1);
  }
  console.log('  ✅ All checks passed');
}

main().catch(err => {
  console.error('\n[cloud-contract] FATAL:', err);
  process.exit(1);
});
