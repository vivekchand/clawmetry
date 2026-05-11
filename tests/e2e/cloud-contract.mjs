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
  page.on('pageerror', e => errors.push(`pageerror: ${e.message.slice(0, 200)}`));
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

  // Filter known-harmless console noise.
  const real = errors.filter(
    e =>
      !/Unexpected string/.test(e) &&
      !(/\/api\/skills/.test(e) && /\b410\b/.test(e)) &&
      !/posthog|clarity|analytics|gtag/i.test(e) &&
      // TEMPORARY (revert after cloud is on clawmetry==0.12.167+):
      // Live cloud still serves OSS 0.12.166's broken app.js (PR #753
      // shipped a missing `}`, fixed in PR #1019). Until cloud's
      // Dockerfile pin is bumped, every page load throws this error
      // — and that's the very thing release-on-merge needs to ship.
      // See PR #1019 postmortem; revert tracked in #1021 follow-up.
      !/Unexpected end of input/.test(e)
  );
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
