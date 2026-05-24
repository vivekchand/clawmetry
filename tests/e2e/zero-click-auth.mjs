#!/usr/bin/env node
/**
 * Zero-click localhost auto-login — E2E coverage for issue #1356 (PR-E).
 *
 * What this proves
 * ----------------
 * A fresh user installs ClawMetry, has a GATEWAY_TOKEN configured, and
 * opens http://localhost:8900/. They MUST land on the live dashboard with
 * NO login overlay, NO password prompt, NO copy/paste step. The page
 * silently fetches the locally-discoverable token via /api/auth/detected-token
 * (PR-B) and the bootstrap script (PR-C) stashes it into localStorage
 * before the overlay would ever paint.
 *
 * Negative path
 * -------------
 * The detected-token endpoint MUST refuse non-localhost callers — even
 * if the loopback caller spoofs X-Forwarded-For. Anyone reverse-proxying
 * the dashboard onto a public hostname must NOT receive the token.
 *
 * Status (2026-05-15)
 * -------------------
 * This test depends on PR-B (`/api/auth/detected-token` endpoint) and
 * PR-C (zero-click bootstrap shim in auth-bootstrap.js / app.js). Until
 * both land, expect the positive test to fail (overlay still shows) and
 * the negative test to fail with HTTP 404 (route not yet registered).
 * That's the intended state — this PR is a tracking PR for E2E coverage,
 * marked Draft.
 *
 * Run
 * ---
 *   node tests/e2e/zero-click-auth.mjs
 *   HEADLESS=0 node tests/e2e/zero-click-auth.mjs       # show browser
 *   PORT=8910 node tests/e2e/zero-click-auth.mjs        # custom port
 *   KEEP_TEMP=1 node tests/e2e/zero-click-auth.mjs      # keep tmp workspace
 *
 * Exits 0 if all checks pass, 1 on failure.
 */
import { chromium } from 'playwright';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';

const PORT = parseInt(process.env.PORT || '8910', 10); // non-default to avoid clobbering a real local dashboard
const HEADLESS = process.env.HEADLESS !== '0';
const KEEP_TEMP = process.env.KEEP_TEMP === '1';
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || `tok-${crypto.randomBytes(8).toString('hex')}`;

const TEST_DIR = path.join(os.tmpdir(), `cm-zero-click-${Date.now()}`);
const TEST_OPENCLAW = path.join(TEST_DIR, 'openclaw');

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

// ── Resolve the dashboard entrypoint ──────────────────────────────────
//
// Prefer the in-repo dashboard.py so the test runs against the worktree
// under review, not whatever pip-installed clawmetry happens to be on
// PATH. Fall back to `clawmetry` CLI if dashboard.py isn't reachable
// (e.g. when this file is fetched standalone).

function resolveDashboardCommand() {
  const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
  const dashboardPy = path.join(repoRoot, 'dashboard.py');
  if (fs.existsSync(dashboardPy)) {
    // Find a python with flask + waitress + cryptography importable.
    for (const p of ['python3.11', 'python3.12', 'python3.10', 'python3.9', 'python3']) {
      try {
        execFileSync(p, ['-c', 'import flask, waitress, cryptography'], { encoding: 'utf8' });
        return { cmd: p, args: [dashboardPy, '--port', String(PORT)], cwd: repoRoot };
      } catch {}
    }
    console.log('⚠  dashboard.py exists but no python with flask+waitress+cryptography found. Falling back to `clawmetry` CLI.');
  }
  return { cmd: 'clawmetry', args: ['--port', String(PORT)] };
}

// ── Synthesize an empty OpenClaw workspace ────────────────────────────

function buildWorkspace() {
  fs.mkdirSync(path.join(TEST_OPENCLAW, 'agents', 'main', 'sessions'), { recursive: true });
  fs.mkdirSync(path.join(TEST_OPENCLAW, 'logs'), { recursive: true });
  fs.writeFileSync(
    path.join(TEST_OPENCLAW, 'agents', 'main', 'sessions', 'sessions.json'),
    '{}'
  );
  console.log(`▸ Synthesized OpenClaw workspace at ${TEST_OPENCLAW}`);
}

// ── Spawn the dashboard with GATEWAY_TOKEN set ────────────────────────

function spawnDashboard(cmd) {
  console.log(`▸ Spawning dashboard: ${cmd.cmd} ${cmd.args.join(' ')}`);
  console.log(`  OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN.slice(0, 8)}…`);
  const child = spawn(cmd.cmd, cmd.args, {
    cwd: cmd.cwd,
    env: {
      ...process.env,
      OPENCLAW_GATEWAY_TOKEN: GATEWAY_TOKEN,
      OPENCLAW_HOME: TEST_OPENCLAW,
      // Prevent the dashboard from hijacking the user's real workspace.
      HOME: TEST_DIR,
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const logs = [];
  const onLine = data => {
    const line = data.toString();
    logs.push(line);
    if (process.env.DASH_LOG) process.stdout.write(`[dash] ${line}`);
  };
  child.stdout.on('data', onLine);
  child.stderr.on('data', onLine);
  return { child, logs };
}

async function waitForReady(timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/`, { redirect: 'manual' });
      if (r.status < 500) return true;
    } catch {}
    await new Promise(r => setTimeout(r, 500));
  }
  return false;
}

// ── Test 1: positive — overlay must NOT show, dashboard renders ─────

async function testZeroClickAutoLogin() {
  console.log('\n[1/3] Positive: zero-click localhost auto-login');
  const browser = await chromium.launch({ headless: HEADLESS });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${e.message.slice(0, 200)}`));
  page.on('console', m => {
    if (m.type() === 'error') errors.push(`console.error: ${m.text().slice(0, 200)}`);
  });

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'domcontentloaded' });

  // Give the bootstrap shim time to call /api/auth/detected-token,
  // hydrate localStorage, and hide the overlay (or never show it).
  await page.waitForTimeout(1500);

  const overlay = page.locator('#login-overlay');
  let overlayHidden = false;
  try {
    await overlay.waitFor({ state: 'hidden', timeout: 5000 });
    overlayHidden = true;
  } catch {
    overlayHidden = false;
  }
  check(
    'login overlay (#login-overlay) is hidden — user lands on dashboard with no password prompt',
    overlayHidden,
    overlayHidden ? '' : 'overlay still visible after 5s — auto-login did not fire'
  );

  // Dashboard root rendered. The overview tab is the canonical landing
  // tab. Select by `data-tab="overview"` because IA refactor v2 (PR #1662)
  // renamed the visible label to "Live trace" — text matching no longer
  // works. Both the legacy top `.nav-tab` and the IA-v2 sidebar
  // `.left-nav-item` get `.active` toggled by switchTab() and both
  // carry data-tab.
  const overviewTab = page
    .locator('.nav-tab.active[data-tab="overview"], .left-nav-item.active[data-tab="overview"]')
    .first();
  let overviewVisible = false;
  try {
    await overviewTab.waitFor({ state: 'visible', timeout: 5000 });
    overviewVisible = true;
  } catch {}
  check(
    'Overview tab is visible — dashboard root rendered',
    overviewVisible,
    overviewVisible ? '' : 'no .nav-tab.active or .left-nav-item.active with data-tab="overview" found'
  );

  // Token must be in localStorage — that's how every later /api/* call
  // gets authorized via the bootstrap-injected fetch wrapper.
  const stored = await page.evaluate(
    () =>
      localStorage.getItem('clawmetry-token') ||
      localStorage.getItem('cm-token') ||
      sessionStorage.getItem('cm-token')
  );
  check(
    'gateway token was auto-stashed into localStorage by the bootstrap',
    !!stored && stored.length > 0,
    stored ? `stored ${stored.length} char token` : 'localStorage empty — bootstrap never fetched detected-token'
  );

  // No JS errors during the auto-login sequence.
  // Filter known-benign noise: analytics blocked in CI + CDN resources
  // unreachable in sandboxed runners (net::ERR_CERT_AUTHORITY_INVALID etc.).
  const noisyOk = errors.filter(e =>
    !/posthog|clarity|gtag|analytics/i.test(e) && !e.includes('net::ERR'));
  check(
    'no JS errors during auto-login',
    noisyOk.length === 0,
    noisyOk.slice(0, 3).join('\n      ')
  );

  await browser.close();
}

// ── Test 2: negative — endpoint refuses non-localhost callers ───────
//
// This is a request-only test (no browser). PR-B's contract says
// /api/auth/detected-token MUST inspect request.remote_addr (and any
// trusted proxy headers) and refuse to surface the token to anyone but
// loopback. We verify by sending an X-Forwarded-For that masquerades as
// a public IP — the endpoint must NOT honor it.
//
// The endpoint is hit from 127.0.0.1 (localhost), but with a forged
// X-Forwarded-For. A correct implementation either:
//   (a) ignores XFF entirely and trusts only the real socket peer, OR
//   (b) explicitly rejects when XFF resolves to a non-loopback IP.
// Either way, the endpoint should NOT return 200+token to a request
// that *claims* to be from a public IP.

async function testEndpointRefusesNonLocalhost() {
  console.log('\n[2/3] Negative: detected-token must refuse non-localhost callers');

  // Sanity: localhost call should succeed once PR-B lands.
  const localResp = await fetch(`http://127.0.0.1:${PORT}/api/auth/detected-token`);
  const localOk = localResp.status === 200;
  check(
    'localhost request to /api/auth/detected-token returns 200 (PR-B)',
    localOk,
    `got ${localResp.status} — endpoint may not be implemented yet`
  );

  // Spoofed XFF — an honest implementation must NOT return the token.
  const spoofedResp = await fetch(`http://127.0.0.1:${PORT}/api/auth/detected-token`, {
    headers: { 'X-Forwarded-For': '203.0.113.42' }, // TEST-NET-3, never routable
  });
  const spoofedRefused = spoofedResp.status === 403 || spoofedResp.status === 404;
  let spoofedBody = '';
  try {
    spoofedBody = (await spoofedResp.text()).slice(0, 120);
  } catch {}
  check(
    'spoofed X-Forwarded-For from public IP gets 403/404 — endpoint refuses to leak token off-loopback',
    spoofedRefused,
    `got ${spoofedResp.status} body=${spoofedBody}`
  );

  // Belt-and-braces: even if the response is 200, the body must NOT
  // contain a non-empty token field. Catches naive impls that return
  // {token: null} on refusal.
  if (spoofedResp.status === 200) {
    let body = {};
    try {
      body = JSON.parse(spoofedBody);
    } catch {}
    check(
      'spoofed XFF response carries no token in body',
      !body.token || body.token === '' || body.token === null,
      `body.token=${JSON.stringify(body.token)}`
    );
  }
}

// ── Test 3: smoke — overlay element exists in DOM (regression guard) ─
//
// Cheap guard against someone deleting the overlay markup entirely
// during PR-C and accidentally making this test pass via element
// non-existence.

async function testOverlayElementStillExists() {
  console.log('\n[3/3] Smoke: #login-overlay element still exists in DOM');
  const browser = await chromium.launch({ headless: HEADLESS });
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);
  const exists = await page.evaluate(() => !!document.getElementById('login-overlay'));
  check(
    '#login-overlay element exists in DOM (just hidden, not deleted)',
    exists,
    'overlay markup gone — test cannot prove auto-login if there is nothing to auto-dismiss'
  );
  await browser.close();
}

// ── Cleanup ────────────────────────────────────────────────────────────

function cleanup(dashState) {
  if (dashState && dashState.child && !dashState.child.killed) {
    dashState.child.kill('SIGTERM');
    // Hard kill if it didn't exit cleanly.
    setTimeout(() => {
      if (!dashState.child.killed) dashState.child.kill('SIGKILL');
    }, 3000).unref();
  }
  if (KEEP_TEMP) {
    console.log(`▸ KEEP_TEMP=1 — leaving ${TEST_DIR} on disk`);
    return;
  }
  try {
    fs.rmSync(TEST_DIR, { recursive: true });
  } catch {}
}

// ── Main ───────────────────────────────────────────────────────────────

async function main() {
  console.log(`[zero-click-auth] port=${PORT} headless=${HEADLESS}`);
  console.log(`[zero-click-auth] tmp=${TEST_DIR}\n`);

  buildWorkspace();
  const cmd = resolveDashboardCommand();
  const dashState = spawnDashboard(cmd);

  const ready = await waitForReady();
  check('dashboard is reachable on the test port', ready);
  if (!ready) {
    console.log('\n[zero-click-auth] dashboard never became ready. Last 30 log lines:');
    dashState.logs.slice(-30).forEach(l => process.stdout.write(`  [dash] ${l}`));
    cleanup(dashState);
    process.exit(1);
  }

  try {
    await testZeroClickAutoLogin();
    await testEndpointRefusesNonLocalhost();
    await testOverlayElementStillExists();
  } finally {
    cleanup(dashState);
  }

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`  ${pass} passed, ${fail} failed`);
  if (fail > 0) {
    console.log('\nFailures:');
    failures.forEach(f => console.log(`  • ${f}`));
    console.log(
      '\nNOTE: This PR (PR-E) lands BEFORE PR-B (/api/auth/detected-token endpoint)\n' +
      '      and PR-C (zero-click bootstrap) merge. Until they do, the positive\n' +
      '      test will fail (overlay still shows) and the localhost-200 check\n' +
      '      will fail (endpoint returns 404). That is expected.'
    );
    process.exit(1);
  }
  console.log('  All checks passed');
}

main().catch(err => {
  console.error('\n[zero-click-auth] FATAL:', err);
  process.exit(1);
});
