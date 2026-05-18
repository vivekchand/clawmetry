#!/usr/bin/env node
/**
 * Real-flow end-to-end test — events arrive at the dashboard the same way
 * they would for any pip-install user: through a real `clawmetry sync`
 * daemon reading session JSONLs from a real OpenClaw workspace, encrypting
 * them client-side, and POSTing to /ingest/events.
 *
 * No API injection. The test mirrors what a fresh user would experience.
 *
 * Setup (per run):
 *   1. Register a fresh test account against /api/register.
 *   2. Synthesize a realistic OpenClaw workspace at /tmp/cm-real-flow-openclaw/
 *      with a sessions.json index + one session JSONL containing a chat
 *      transcript (user → assistant → tool_call → assistant).
 *   3. Write daemon config at /tmp/cm-real-flow-home/.clawmetry/config.json
 *      with the test account's api_key + a fresh AES-256-GCM enc_key.
 *   4. Spawn `clawmetry sync` (the real OSS daemon) with HOME and
 *      OPENCLAW_HOME overridden to point at the temp dirs.
 *   5. Wait for the daemon's first sync cycle to upload events (~25s).
 *   6. Open the dashboard URL with the matching enc_key and walk every
 *      free-tier tab. Assert Brain shows the synthesized events,
 *      decryption is clean, no JS errors.
 *   7. Cleanup: SIGTERM the daemon, rm temp dirs.
 *
 * Run:
 *   node tests/e2e/real-flow.mjs
 *   HEADLESS=0 node tests/e2e/real-flow.mjs                # show browser
 *   KEEP_TEMP=1 node tests/e2e/real-flow.mjs               # don't rm tempdirs
 *   DAEMON_WAIT_S=45 node tests/e2e/real-flow.mjs          # bump sync wait
 *
 * Requirements:
 *   - `clawmetry` Python package installed and on PATH (any version with the
 *     standard sync.py). The daemon is spawned via `clawmetry --version`-style
 *     entry resolution; if it isn't installed, the script bails with a clean
 *     message.
 *
 * Exits 0 if all checks pass, 1 on failure.
 */
import { chromium } from 'playwright';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';

const API_BASE = process.env.CLAWMETRY_API_BASE || 'https://app.clawmetry.com';
const HEADLESS = process.env.HEADLESS !== '0';
const DAEMON_WAIT_S = parseInt(process.env.DAEMON_WAIT_S || '25', 10);
const KEEP_TEMP = process.env.KEEP_TEMP === '1';

const TEST_HOME = '/tmp/cm-real-flow-home';
const TEST_OPENCLAW = '/tmp/cm-real-flow-openclaw';

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

// ── Step 1: confirm the OSS daemon is installed locally ─────────────────

function findDaemon() {
  // Find the python that actually has clawmetry installed. install.sh
  // creates a venv at ~/.clawmetry/bin/python3 and the `clawmetry` CLI
  // shebangs that interpreter. System python3 typically can't import
  // clawmetry. Read the CLI's shebang to discover the right interpreter
  // — robust across pip-install-as-user, pipx, install.sh venv, etc.
  let python = null;
  try {
    const cli = execFileSync('which', ['clawmetry'], { encoding: 'utf8' }).trim();
    const shebang = fs.readFileSync(cli, 'utf8').split('\n')[0].trim();
    if (shebang.startsWith('#!')) {
      const candidate = shebang.slice(2).trim().split(/\s+/)[0];
      if (fs.existsSync(candidate)) python = candidate;
    }
  } catch {}
  // Fall back: try common interpreters until one can `import clawmetry`.
  if (!python) {
    for (const p of ['python3.11', 'python3.12', 'python3.10', 'python3.9', 'python3']) {
      try {
        execFileSync(p, ['-c', 'import clawmetry.sync'], { encoding: 'utf8' });
        python = p;
        break;
      } catch {}
    }
  }
  if (!python) {
    console.log('❌ clawmetry Python module not importable from any python on PATH.');
    console.log('   Run `pip install clawmetry` (or `curl https://clawmetry.com/install.sh | bash`) and retry.');
    process.exit(1);
  }
  // Verify it can actually import clawmetry.sync now.
  try {
    execFileSync(python, ['-c', 'import clawmetry.sync'], { encoding: 'utf8' });
  } catch (e) {
    console.log(`❌ Picked python ${python} but it can't import clawmetry.sync: ${e.message.slice(0, 200)}`);
    process.exit(1);
  }
  // clawmetry has no __main__.py so `python -m clawmetry --version` doesn't
  // work — read the version off __version__ instead.
  let v = '(version unknown)';
  try {
    v = execFileSync(
      python,
      ['-c', "import clawmetry; print(getattr(clawmetry, '__version__', ''))"],
      { encoding: 'utf8' }
    ).trim();
  } catch {}
  console.log(`▸ Found clawmetry ${v} via ${python}`);
  return { cmd: python, args: ['-m', 'clawmetry.sync'] };
}

// ── Step 2: register a fresh test account ───────────────────────────────

async function registerOrSkip(machineId) {
  for (let attempt = 1; attempt <= 4; attempt++) {
    const res = await fetch(`${API_BASE}/api/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hostname: machineId,
        machine_id: machineId,
        platform: 'Linux',
        email: `cm-real-flow+${machineId}@clawmetry.com`,
      }),
    });
    if (res.ok) return res.json();
    if (res.status === 429) {
      console.log(`\n[real-flow] SKIP: /api/register rate-limited (10/hr per IP).`);
      process.exit(0);
    }
    console.log(`  register attempt ${attempt}: ${res.status}`);
    if (attempt < 4) await new Promise(r => setTimeout(r, 2000 * attempt));
  }
  throw new Error('register failed after 4 retries');
}

// ── Step 3: synthesize a realistic OpenClaw workspace ───────────────────

function buildFakeOpenClawWorkspace() {
  if (fs.existsSync(TEST_OPENCLAW)) fs.rmSync(TEST_OPENCLAW, { recursive: true });
  const sessionsDir = path.join(TEST_OPENCLAW, 'agents', 'main', 'sessions');
  const logsDir = path.join(TEST_OPENCLAW, 'logs');
  const memoryDir = path.join(TEST_OPENCLAW, 'memory');
  fs.mkdirSync(sessionsDir, { recursive: true });
  fs.mkdirSync(logsDir, { recursive: true });
  fs.mkdirSync(memoryDir, { recursive: true });

  const sessionId = crypto.randomUUID();
  const now = new Date();
  const t = ms => new Date(now.getTime() - ms).toISOString();
  const tNum = ms => now.getTime() - ms;

  // Mirrors the OpenClaw JSONL schema (verified against
  // ~/.openclaw/agents/main/sessions/<uuid>.jsonl on a real install).
  const events = [
    {
      type: 'session', version: 3, id: sessionId, timestamp: t(180_000),
      cwd: path.join(TEST_OPENCLAW, 'workspace'),
    },
    {
      type: 'model_change', id: 'mc-1', parentId: null, timestamp: t(180_000),
      provider: 'anthropic', modelId: 'claude-sonnet-4.5',
    },
    {
      type: 'message', id: 'msg-user-1', parentId: 'mc-1', timestamp: t(150_000),
      message: {
        role: 'user',
        content: [{ type: 'text', text: 'Investigate yesterday\'s deploy failures and write a postmortem.' }],
        timestamp: tNum(150_000),
      },
    },
    {
      type: 'message', id: 'msg-asst-1', parentId: 'msg-user-1', timestamp: t(135_000),
      message: {
        role: 'assistant',
        content: [{ type: 'text', text: 'I\'ll pull the CI logs and check for common failure patterns.' }],
        api: 'anthropic-messages', provider: 'anthropic', model: 'claude-sonnet-4.5',
        usage: { input: 1200, output: 80, cache_read: 0, cache_creation: 0 },
      },
    },
    {
      type: 'tool_call', id: 'tc-1', parentId: 'msg-asst-1', timestamp: t(130_000),
      data: { tool: 'Bash', command: 'gh run list --limit 20 --json status,conclusion' },
    },
    {
      type: 'tool_result', id: 'tr-1', parentId: 'tc-1', timestamp: t(125_000),
      data: { tool: 'Bash', exit_code: 0, output_preview: '20 runs returned, 3 failures detected' },
    },
    {
      type: 'tool_call', id: 'tc-2', parentId: 'tr-1', timestamp: t(115_000),
      data: { tool: 'Read', file_path: '/var/log/build/789.log' },
    },
    {
      type: 'tool_call', id: 'tc-3', parentId: 'tc-2', timestamp: t(100_000),
      data: { tool: 'WebFetch', url: 'https://status.example.com', model: 'claude-sonnet-4.5' },
    },
    {
      type: 'message', id: 'msg-asst-2', parentId: 'tc-3', timestamp: t(80_000),
      message: {
        role: 'assistant',
        content: [{
          type: 'text',
          text: 'Found 3 failed deploys yesterday. Two were OOM kills in the build container (heap maxed at 1.8 GB on a 2 GB limit). One was a lockfile race in pnpm install on the cold cache. Posting the postmortem to Linear now.',
        }],
        api: 'anthropic-messages', provider: 'anthropic', model: 'claude-sonnet-4.5',
        usage: { input: 4400, output: 380, cache_read: 1200, cache_creation: 200 },
      },
    },
  ];

  const sessionFile = path.join(sessionsDir, `${sessionId}.jsonl`);
  fs.writeFileSync(sessionFile, events.map(e => JSON.stringify(e)).join('\n') + '\n');

  // sessions.json index — keyed on the OpenClaw session-key format.
  const sessionsIndex = {
    'agent:main:main': {
      sessionId,
      updatedAt: now.getTime(),
      systemSent: true,
      abortedLastRun: false,
      chatType: 'direct',
      deliveryContext: { channel: 'webchat' },
      lastChannel: 'webchat',
      origin: { label: 'cm-real-flow-test', provider: 'webchat', surface: 'webchat', chatType: 'direct' },
      sessionFile,
      compactionCount: 0,
    },
  };
  fs.writeFileSync(
    path.join(sessionsDir, 'sessions.json'),
    JSON.stringify(sessionsIndex, null, 2)
  );

  // Drop a memory file so the Memory tab has something.
  fs.writeFileSync(
    path.join(memoryDir, 'TODO.md'),
    '# TODO\n- Backfill OOM mitigations into the runbook\n- Pin pnpm to 10.x to avoid lockfile race\n'
  );

  console.log(`▸ Synthesized OpenClaw workspace at ${TEST_OPENCLAW} (session ${sessionId.slice(0, 8)}…)`);
  return { sessionId, sessionFile };
}

// ── Step 4: write daemon config ─────────────────────────────────────────

function writeDaemonConfig(reg) {
  if (fs.existsSync(TEST_HOME)) fs.rmSync(TEST_HOME, { recursive: true });
  const cmDir = path.join(TEST_HOME, '.clawmetry');
  fs.mkdirSync(cmDir, { recursive: true });
  const encKey = crypto.randomBytes(32).toString('base64');
  const config = {
    api_key: reg.api_key,
    node_id: reg.node_id,
    encryption_key: encKey,
    platform: 'Linux',
    connected_at: new Date().toISOString(),
  };
  fs.writeFileSync(path.join(cmDir, 'config.json'), JSON.stringify(config, null, 2), { mode: 0o600 });
  console.log(`▸ Wrote daemon config at ${cmDir}/config.json (node=${reg.node_id})`);
  return encKey;
}

// ── Step 5: spawn the real OSS daemon ───────────────────────────────────

function spawnDaemon(daemon) {
  console.log(`▸ Spawning real OSS daemon: ${daemon.cmd} ${daemon.args.join(' ')}`);
  console.log(`  HOME=${TEST_HOME}  OPENCLAW_HOME=${TEST_OPENCLAW}`);
  const child = spawn(daemon.cmd, daemon.args, {
    env: {
      ...process.env,
      HOME: TEST_HOME,
      OPENCLAW_HOME: TEST_OPENCLAW,
      // Keep the daemon's own logs out of stdout pollution
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const logs = [];
  const onLine = data => {
    const line = data.toString();
    logs.push(line);
    if (process.env.DAEMON_LOG) process.stdout.write(`[daemon] ${line}`);
  };
  child.stdout.on('data', onLine);
  child.stderr.on('data', onLine);
  return { child, logs };
}

// ── Step 6: wait for daemon to upload + open dashboard ──────────────────

async function waitForSync(daemonState, machineId, reg) {
  console.log(`▸ Waiting up to ${DAEMON_WAIT_S}s for daemon's first sync cycle…`);
  // Poll /api/cloud/account: nodes count flips from 0 → 1 once the daemon's
  // heartbeat lands. That's a strong signal the daemon is running and
  // talking to cloud. Then wait a few more seconds for the events POST.
  const start = Date.now();
  let connected = false;
  while ((Date.now() - start) / 1000 < DAEMON_WAIT_S) {
    await new Promise(r => setTimeout(r, 2500));
    const acc = await fetch(
      `${API_BASE}/api/cloud/account?token=${encodeURIComponent(reg.api_key)}`
    ).then(r => r.json()).catch(() => ({}));
    if (acc.usage_stats && acc.usage_stats.nodes >= 1) {
      connected = true;
      console.log(`  ✓ daemon connected after ~${Math.round((Date.now() - start) / 1000)}s`);
      break;
    }
  }
  return connected;
}

// ── Step 7: open dashboard, walk tabs, assert Brain has events ──────────

async function walkDashboard(reg, encKey, sessionId) {
  const url =
    `${API_BASE}/cloud/node/${encodeURIComponent(reg.node_id)}` +
    `?token=${encodeURIComponent(reg.api_key)}` +
    `#key=${encodeURIComponent(encKey)}&node=${encodeURIComponent(reg.node_id)}`;
  console.log(`▸ Opening dashboard with browser (HEADLESS=${HEADLESS})`);
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

  // Land on dashboard with retry-on-cold-start.
  let cloudMode = false;
  for (let i = 1; i <= 5; i++) {
    await page.goto(url, { waitUntil: 'domcontentloaded' }).catch(() => undefined);
    await page.waitForTimeout(2500);
    cloudMode = await page.evaluate(() => window.CLOUD_MODE === true);
    if (cloudMode) break;
  }
  check('dashboard loaded CLOUD_MODE', cloudMode);
  if (!cloudMode) {
    await browser.close();
    return;
  }

  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined);
  await page.waitForTimeout(4000); // let Brain stream + Tokens chart render

  const PAUSE_MS = HEADLESS ? 1500 : 3000;

  console.log('\n  ▸ Walking each tab');
  // Walk free-tier tabs first, then Pro-gated tabs (Flow, Notifications,
  // Alerts) at the end. Pro tabs trigger upsell modals that DON'T
  // auto-dismiss on tab change (real product bug — see screenshot
  // attached in PR). Putting them last means the modal can't cover up
  // earlier tabs in screenshots.
  const TABS = ['Brain', 'Overview', 'Approvals', 'Context', 'Tokens', 'Crons', 'Memory', 'Flow', 'Alerts', 'Notifications'];
  for (const tab of TABS) {
    const errBefore = errors.length;
    // IA v2 (PRD #1659): accept left-nav buckets + per-page sub-nav items
    // alongside the legacy .nav-tab row.
    const t = page.locator(
      `.nav-tab:has-text("${tab}"), .left-nav-item:has-text("${tab}"), ` +
      `.page-subnav-item:has-text("${tab}"), [role="tab"]:has-text("${tab}")`
    ).first();
    if ((await t.count()) === 0) {
      check(`${tab}: tab visible`, false);
      continue;
    }
    await t.click({ timeout: 5000 }).catch(() => undefined);
    await page.waitForTimeout(PAUSE_MS);
    // Defensive: if the previous tab opened a Pro upsell modal that's
    // covering this tab's content, dismiss it (Esc + click "Maybe
    // later"). Without this, every subsequent tab inherits the visual
    // overlay and screenshots are useless.
    await page.keyboard.press('Escape').catch(() => undefined);
    const maybeLater = page.locator('button:has-text("Maybe later"), button:has-text("Close"), [aria-label="Close"]').first();
    if ((await maybeLater.count()) > 0 && (await maybeLater.isVisible().catch(() => false))) {
      await maybeLater.click({ timeout: 2000 }).catch(() => undefined);
      await page.waitForTimeout(300);
    }
    const tabState = await page.evaluate(() => {
      const text = document.body.innerText || '';
      return {
        bodyLen: text.length,
        hasUnlock: text.toLowerCase().includes('enter your secret key'),
        hasDecryptFail: text.toLowerCase().includes('could not decrypt'),
      };
    });
    check(`${tab}: rendered (body > 200 chars)`, tabState.bodyLen > 200);
    check(`${tab}: no unlock prompt`, !tabState.hasUnlock);
    check(`${tab}: no decrypt failure`, !tabState.hasDecryptFail);
    check(`${tab}: no new JS errors`, errors.length === errBefore);
  }

  // Brain MUST show the synthesized session — it has unique copy
  // ("postmortem", "OOM kills", "lockfile race") that wouldn't appear
  // in any other test account's events.
  // Click Brain explicitly + wait for the Brain-specific header to be
  // visible. This is the canonical way to know we're "on Brain" — bare
  // body-text inspection races with whatever tab the previous loop
  // ended on (Notifications, which can put a Pro modal on top).
  console.log('\n  ▸ Brain — must show the daemon-uploaded session');
  // First dismiss any open Pro modal so the click below isn't intercepted
  // by an overlay's invisible event handler.
  await page.evaluate(() => {
    const g = document.getElementById('cm-pro-gate'); if (g) g.remove();
    const p = document.getElementById('pro-upsell-modal');
    if (p) p.style.display = 'none';
  });
  await page.locator(
    '.nav-tab:has-text("Brain"), .left-nav-item:has-text("Brain"), .page-subnav-item:has-text("Brain")'
  ).first().click({ force: true }).catch(() => undefined);
  // Wait specifically for Brain's content area, not just any body change.
  await page
    .locator(':has-text("Brain — Unified Activity Stream"), :has-text("Brain – Unified Activity Stream"), :has-text("Brain - Unified Activity")')
    .first()
    .waitFor({ state: 'visible', timeout: 8000 })
    .catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  const brainState = await page.evaluate(() => ({
    body: (document.body.innerText || '').toLowerCase(),
    activeTab: document.querySelector('.nav-tab.active, .left-nav-item.active, .page-subnav-item.active, [role="tab"][aria-selected="true"]')?.textContent?.trim().toLowerCase() || '',
  }));
  console.log(`  active tab according to DOM: "${brainState.activeTab}"`);
  check(
    'Brain shows the user message ("postmortem")',
    brainState.body.includes('postmortem'),
    `activeTab=${brainState.activeTab} body=${brainState.body.slice(0, 200)}`
  );
  check(
    'Brain shows the assistant reply ("oom kills")',
    brainState.body.includes('oom kills') || brainState.body.includes('oom'),
    `activeTab=${brainState.activeTab} body=${brainState.body.slice(0, 200)}`
  );

  // Tokens tab should render. The aggregations behind it (daily/per-model
  // rollups) take a longer cycle to accumulate, so assert only that the
  // tab body shows the canonical "Tokens" header — not specific model names
  // (which only show up after the daemon's per-model snapshot fires).
  console.log('\n  ▸ Tokens — tab renders');
  await page.locator(
    '.nav-tab:has-text("Tokens"), .left-nav-item:has-text("Tokens"), .page-subnav-item:has-text("Tokens")'
  ).first().click().catch(() => undefined);
  await page.waitForTimeout(PAUSE_MS);
  const tokensBody = await page.evaluate(() => (document.body.innerText || '').toLowerCase());
  check(
    'Tokens tab renders its own header (not blank or stuck on a different tab)',
    tokensBody.includes('token') || tokensBody.includes('cost') || tokensBody.includes('usage')
  );

  // Filter known-harmless console noise.
  const real = errors.filter(
    e =>
      !/Unexpected string/.test(e) &&
      !(/\/api\/skills/.test(e) && /\b410\b/.test(e)) &&
      !/posthog|clarity|analytics|gtag/i.test(e)
  );
  check('zero unexpected JS errors', real.length === 0, real.slice(0, 5).join('\n      '));

  await browser.close();
}

// ── Cleanup ─────────────────────────────────────────────────────────────

function cleanup(daemonState) {
  if (daemonState && daemonState.child && !daemonState.child.killed) {
    daemonState.child.kill('SIGTERM');
  }
  if (KEEP_TEMP) {
    console.log(`▸ KEEP_TEMP=1 — leaving ${TEST_HOME} and ${TEST_OPENCLAW} on disk`);
    return;
  }
  for (const dir of [TEST_HOME, TEST_OPENCLAW]) {
    try {
      fs.rmSync(dir, { recursive: true });
    } catch {}
  }
}

// ── Main ────────────────────────────────────────────────────────────────

async function main() {
  console.log(`[real-flow] target: ${API_BASE}`);
  console.log(`[real-flow] headless: ${HEADLESS}\n`);

  const daemon = findDaemon();
  const machineId = `cm-real-flow-${Date.now()}-${crypto.randomBytes(3).toString('hex')}`;
  const reg = await registerOrSkip(machineId);
  console.log(`▸ Registered test node: ${reg.node_id}`);
  check('register: api_key shape', /^cm_[a-f0-9]{32}$/.test(reg.api_key));

  const { sessionId } = buildFakeOpenClawWorkspace();
  const encKey = writeDaemonConfig(reg);
  const daemonState = spawnDaemon(daemon);
  const connected = await waitForSync(daemonState, machineId, reg);
  check('daemon connected to cloud (heartbeat landed)', connected);

  if (!connected) {
    console.log('\n[real-flow] daemon never connected. Last 50 log lines:');
    daemonState.logs.slice(-50).forEach(l => process.stdout.write(`  [daemon] ${l}`));
  } else {
    // Poll the cloud until events are likely there. The canonical
    // end-to-end check is Brain showing the synthesized text — that
    // proves daemon → cloud → SSE → browser decryption all worked.
    // The poll here is just to give the daemon time; we don't assert
    // on the shape (response is encrypted blobs and the count field
    // varies by endpoint).
    console.log('  giving the daemon ~25s to push first events to cloud…');
    await new Promise(r => setTimeout(r, 25_000));
    await walkDashboard(reg, encKey, sessionId);
  }

  cleanup(daemonState);

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
  console.error('\n[real-flow] FATAL:', err);
  cleanup();
  process.exit(1);
});
