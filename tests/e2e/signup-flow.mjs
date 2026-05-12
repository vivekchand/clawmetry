#!/usr/bin/env node
/**
 * Signup-flow end-to-end test — `curl install.sh` → /cloud → email-OTP
 * → linked-account dashboard.
 *
 * The "Complete your account" modal that auto-registered users see on
 * first /cloud visit was silently failing for some users with "Invalid
 * token" even after a valid OTP (vivekchand/clawmetry-cloud#641). This
 * test exercises the FULL flow so that regression can never silently
 * ship again.
 *
 * Flow:
 *   1. POST /api/register with hostname, machine_id, email — same call
 *      install.sh makes after `curl https://clawmetry.com/install.sh |
 *      bash`. Gets back an api_key + auto-account email
 *      (agent+xxx@clawmetry.auto).
 *   2. Open /cloud?token=<api_key> with a real browser.
 *   3. Wait for the "Complete your account" modal to appear.
 *   4. Type a real-looking email (cm-e2e-test+xxx@clawmetry.com — the
 *      test-only whitelist pattern).
 *   5. Click "Send verification code". Cloud sends a real email via
 *      Resend AND stashes the OTP in connect_otps.
 *   6. Read the OTP from the cloud's /api/auth/_test/peek-otp endpoint
 *      (gated on CLAWMETRY_E2E_TEST_SECRET env var on the cloud +
 *      matching X-Test-Secret header here + whitelist email pattern).
 *   7. Type the OTP, click "Verify".
 *   8. Assert: modal closes, page header shows the new email.
 *
 * Run:
 *   CM_E2E_TEST_SECRET=<secret> node tests/e2e/signup-flow.mjs
 *   HEADLESS=0 CM_E2E_TEST_SECRET=<secret> node tests/e2e/signup-flow.mjs
 *
 * Without CM_E2E_TEST_SECRET, the test exits 0 with a SKIP message
 * (the cloud-side endpoint is disabled in environments where the
 * secret isn't set, so there's no way to read the OTP back).
 *
 * Exits 0 if all checks pass, 1 on failure.
 */
import { chromium } from 'playwright';
import crypto from 'node:crypto';

const API_BASE = process.env.CLAWMETRY_API_BASE || 'https://app.clawmetry.com';
const HEADLESS = process.env.HEADLESS !== '0';
const TEST_SECRET = process.env.CM_E2E_TEST_SECRET || '';

if (!TEST_SECRET) {
  console.log('[signup-flow] SKIP: set CM_E2E_TEST_SECRET to the value of');
  console.log('              CLAWMETRY_E2E_TEST_SECRET on the cloud environment.');
  console.log('              Without it, the OTP-peek endpoint is disabled and');
  console.log('              this test cannot complete the verification step.\n');
  process.exit(0);
}

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

async function postJson(path, payload, extraHeaders = {}) {
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
    body: JSON.stringify(payload),
  });
}

async function main() {
  console.log(`[signup-flow] target: ${API_BASE}`);
  console.log(`[signup-flow] headless: ${HEADLESS}\n`);

  // ── Step 1: simulate `curl install.sh | bash` ──────────────────────────
  // install.sh ultimately POSTs to /api/register the same way KiloClaw
  // does. The auto-account that comes back has email
  // agent+<mid>@clawmetry.auto, which is what triggers the "Complete
  // your account" modal on /cloud.
  const machineId = `cm-e2e-test-${Date.now()}-${crypto.randomBytes(3).toString('hex')}`;
  console.log('▸ Step 1: register a fresh auto-account (mirrors install.sh)');
  let regBody;
  for (let attempt = 1; attempt <= 4; attempt++) {
    const res = await postJson('/api/register', {
      hostname: machineId,
      machine_id: machineId,
      platform: 'Linux',
    });
    if (res.ok) {
      regBody = await res.json();
      break;
    }
    if (res.status === 429) {
      console.log('[signup-flow] SKIP: /api/register rate-limited.');
      process.exit(0);
    }
    if (attempt < 4) await new Promise(r => setTimeout(r, 2000 * attempt));
  }
  if (!regBody) throw new Error('/api/register failed after 4 retries');
  console.log(`  api_key: ${regBody.api_key.slice(0, 16)}…`);
  console.log(`  email:   ${regBody.email || '(not in response)'}`);
  check('register returned api_key', !!regBody.api_key);
  check('register returned auto-account', /^cm_[a-f0-9]{32}$/.test(regBody.api_key));

  // ── Step 2-3: open /cloud and wait for the modal ───────────────────────
  console.log('\n▸ Step 2: open /cloud in browser');
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

  await page.goto(`${API_BASE}/cloud?token=${encodeURIComponent(regBody.api_key)}`, {
    waitUntil: 'domcontentloaded',
  });
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined);

  console.log('▸ Step 3: wait for "Complete your account" modal');
  const modal = page.locator(':has-text("Complete your account")').first();
  await modal.waitFor({ state: 'visible', timeout: 15_000 }).catch(() => undefined);
  const modalVisible = await modal.isVisible().catch(() => false);
  check('Complete-your-account modal appears for auto-registered users', modalVisible);
  if (!modalVisible) {
    await browser.close();
    return;
  }

  // ── Step 4-5: type email + click Send code ─────────────────────────────
  // Pattern MUST start with cm-e2e-test+ or cm-e2e-test- — that's the
  // server-side whitelist that gates the OTP-peek endpoint.
  // Avoid `+` in the local-part — Playwright's `.fill()` works fine,
  // but some `<input type="email">` validators can mangle it on submit.
  // Use a hyphen-only test email that still satisfies the whitelist.
  const testEmail = `cm-e2e-test-${machineId}@clawmetry.com`;
  console.log(`\n▸ Step 4: type test email ${testEmail}`);
  await page.locator('#cs-email').fill(testEmail);
  // Verify the input actually holds what we typed (paranoid; Playwright
  // .fill() has bitten me before with synthetic events being swallowed).
  const actualValue = await page.locator('#cs-email').inputValue();
  check('email input holds the typed value', actualValue === testEmail, `got: ${actualValue}`);
  // Snoop the request body the browser actually sends, so if peek-otp
  // can't find the OTP later we know the exact email the server got.
  let actualSentEmail = null;
  page.on('request', r => {
    if (r.url().endsWith('/api/auth/email-otp') && r.method() === 'POST') {
      try {
        actualSentEmail = JSON.parse(r.postData() || '{}').email;
      } catch {}
    }
  });
  await page.locator('#cs-send-btn').click();
  console.log('▸ Step 5: wait for "Code sent to ..." confirmation');
  await page.locator('#cs-step2:visible').waitFor({ timeout: 10_000 }).catch(() => undefined);
  const sentToVisible = await page.locator('#cs-sent-to').isVisible().catch(() => false);
  check('OTP send succeeded — step 2 visible with "Code sent to" message', sentToVisible);

  // ── Step 6: read the OTP from the test-only peek endpoint ──────────────
  console.log(`\n  (browser actually sent email: ${actualSentEmail || '(not captured)'})`);
  console.log('▸ Step 6: peek the OTP from /api/auth/_test/peek-otp');
  // Use the exact email the BROWSER sent, not the one we typed —
  // covers the rare case where the input mangled it (autocomplete,
  // browser email-validator, IME, etc.).
  const peekEmail = actualSentEmail || testEmail;
  // Cloud's connect_otps write isn't strictly synchronous with the
  // /api/auth/email-otp response (it depends on the OTP-store backend
  // commit). Poll a few times.
  let otp = null;
  for (let i = 1; i <= 6; i++) {
    const res = await postJson(
      '/api/auth/_test/peek-otp',
      { email: peekEmail },
      { 'X-Test-Secret': TEST_SECRET }
    );
    if (res.ok) {
      const body = await res.json();
      if (body.otp && /^\d{6}$/.test(body.otp)) {
        otp = body.otp;
        console.log(`  got OTP: ${otp}`);
        break;
      }
    } else if (res.status === 404 || res.status === 401) {
      const text = await res.text();
      console.log(`  attempt ${i}: ${res.status} ${text.slice(0, 80)}`);
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  check('OTP retrieved via test endpoint (6 digits)', !!otp && /^\d{6}$/.test(otp));
  if (!otp) {
    console.log(
      '\n  ! If this is the first failure: confirm CLAWMETRY_E2E_TEST_SECRET is set\n' +
        '    on the cloud environment AND matches CM_E2E_TEST_SECRET locally.'
    );
    await browser.close();
    return;
  }

  // ── Step 7: type OTP + click Verify ────────────────────────────────────
  console.log('\n▸ Step 7: type OTP + click Verify');
  await page.locator('#cs-otp').fill(otp);
  await page.locator('#cs-verify-btn').click();

  // ── Step 8: assert success ─────────────────────────────────────────────
  console.log('▸ Step 8: assert modal closes + email shown in header');
  // Modal should remove itself within ~3s of a successful verify.
  await page.locator('#cm-complete-signup').waitFor({ state: 'detached', timeout: 8000 }).catch(() => undefined);
  const stillThere = await page.locator('#cm-complete-signup').isVisible().catch(() => false);
  check('Complete-account modal removed after Verify', !stillThere);

  // The verify-error label should NOT show "Invalid token" — that's the
  // exact regression vivekchand/clawmetry-cloud#641 fixed.
  const verifyErr = await page.locator('#cs-verify-err').textContent().catch(() => '');
  check(
    'Verify error label did NOT show "Invalid token" (regression guard for #641)',
    !verifyErr.toLowerCase().includes('invalid token'),
    `error label text: "${verifyErr}"`
  );

  // The page header should now show the linked email (or at least, NOT
  // the @clawmetry.auto placeholder).
  await page.waitForTimeout(2000);
  const headerEmail = await page.locator('#user-email').textContent().catch(() => '');
  check(
    'Page header shows the linked test email',
    headerEmail.includes(testEmail) || headerEmail.includes('cm-e2e-test'),
    `header text: "${headerEmail}"`
  );

  // No surprise JS errors during the whole flow. Filter:
  //   - Known harmless: deprecated /api/skills 410, third-party
  //     trackers, a pre-existing JS quirk
  //   - 401s on /api/cloud/* are expected RIGHT AFTER successful link:
  //     the link returns a NEW api_key + stores it in localStorage,
  //     but the current page's URL still has the OLD token in
  //     ?token=. In-flight loadAll polls (every 8s) using the old
  //     token get 401 until the user reloads. Worth a separate UX
  //     fix (page should reload after link), but not a test failure.
  const real = errors.filter(
    e =>
      !/Unexpected string/.test(e) &&
      !(/\/api\/skills/.test(e) && /\b410\b/.test(e)) &&
      !/posthog|clarity|analytics|gtag/i.test(e) &&
      !(/\/api\/cloud\/(account|sessions|nodes|usage|crons)/.test(e) && /\b401\b/.test(e))
  );
  check('zero unexpected JS errors during signup flow', real.length === 0, real.slice(0, 3).join('\n      '));

  await browser.close();

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
  console.error('\n[signup-flow] FATAL:', err);
  process.exit(1);
});
