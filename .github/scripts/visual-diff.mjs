#!/usr/bin/env node
/**
 * visual-diff.mjs -- capture full-page screenshots of the same dashboard
 * "tabs" on two running clawmetry dashboards (BASE_URL vs HEAD_URL),
 * pixel-diff them, and write artefacts under OUT_DIR.
 *
 * The clawmetry dashboard is a single-page Flask app -- every tab lives at
 * `/` and is switched via the global `switchTab(name)` JS function (no
 * query-string, no hash routing). So we navigate once per tab to `/`, then
 * call `switchTab(<name>)` via Playwright `evaluate`, settle, and screenshot.
 *
 * Inputs (env):
 *   BASE_URL                     http://127.0.0.1:8081
 *   HEAD_URL                     http://127.0.0.1:8082
 *   OUT_DIR                      directory for *.png + manifest.json
 *   PR_SCREENSHOT_TABS           comma-separated tab names (default below)
 *   CLAWMETRY_VISUAL_DIFF_TOKEN  gateway token to seed into localStorage
 *                                BEFORE navigation, dismisses login overlay.
 *                                MUST match each dashboard's
 *                                OPENCLAW_GATEWAY_TOKEN, otherwise every
 *                                shot is a login overlay (bot is theater).
 *
 * Output:
 *   $OUT_DIR/<view>__<slug>__before.png
 *   $OUT_DIR/<view>__<slug>__after.png
 *   $OUT_DIR/<view>__<slug>__diff.png
 *   $OUT_DIR/manifest.json -- [{view, tab, slug, diffPct, hasDiff,
 *                              baseOk, headOk, baseStatus, headStatus}]
 *
 * Exits 0 on clean run (with or without pixel diffs).
 * Exits 2 if either server is unreachable before screenshots start.
 * Exits 3 if any auth gap is detected: HTTP non-200 response, auth overlay
 *   still visible after token injection, OR pre-flight /api/auth/check
 *   rejection (token mismatch caught before screenshot loop starts).
 */
import { chromium } from "playwright";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8081";
const HEAD_URL = process.env.HEAD_URL || "http://127.0.0.1:8082";
const OUT_DIR = process.env.OUT_DIR || "screenshots";
// Token seeded into localStorage before navigation. Must match the
// OPENCLAW_GATEWAY_TOKEN env that booted both dashboards, otherwise the
// bootstrap JS shows the login overlay and every screenshot is just that.
const AUTH_TOKEN = process.env.CLAWMETRY_VISUAL_DIFF_TOKEN || "";

// Tabs that actually exist on the OSS dashboard nav (see dashboard.py
// switchTab() handlers + the .nav-tab buttons). `overview` is the implicit
// default -- listed first so we get a `root` baseline shot.
const DEFAULT_TABS =
  "overview,flow,brain,usage,crons,memory,security,subagents,transcripts,logs,skills,models,approvals,alerts,notifications,context,limits,clusters,history";
const TABS = (process.env.PR_SCREENSHOT_TABS || DEFAULT_TABS)
  .split(",")
  .map((p) => p.trim())
  .filter(Boolean);

const VIEWS = [
  { name: "desktop", width: 1280, height: 720, deviceScaleFactor: 1 },
  {
    name: "mobile",
    width: 375,
    height: 667,
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
  },
];

const slugify = (t) =>
  t === "overview" ? "root" : t.replace(/[^a-z0-9]+/gi, "-").toLowerCase();

async function reachable(url) {
  try {
    const r = await fetch(url, { method: "GET" });
    return r.status < 500;
  } catch {
    return false;
  }
}

/**
 * Pre-flight: call /api/auth/check with the token and return an error string
 * if the token is rejected, or null if auth is accepted.
 *
 * Must run BEFORE the browser loop so a token mismatch fails fast instead
 * of producing a wall of identical login-overlay screenshots with exit 0.
 * (The overlay sets ok=false in shoot() but HTTP status is still 200, so
 * the old authGaps check never fired -- the script exited 0 silently.)
 */
async function preflightAuth(url, token) {
  if (!token) return null; // no token configured -- auth is optional on this instance
  try {
    const params = `?token=${encodeURIComponent(token)}`;
    const r = await fetch(`${url}/api/auth/check${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await r.json().catch(() => ({}));
    if (data.valid === true) return null; // accepted
    return (
      `${url}: /api/auth/check returned valid=${data.valid}` +
      (data.needsSetup ? " needsSetup=true" : "") +
      ". Ensure OPENCLAW_GATEWAY_TOKEN on the server matches CLAWMETRY_VISUAL_DIFF_TOKEN."
    );
  } catch (e) {
    return `${url}: /api/auth/check threw: ${e && e.message}`;
  }
}

async function shoot(browser, baseUrl, view, tab, file) {
  const ctx = await browser.newContext({
    viewport: { width: view.width, height: view.height },
    deviceScaleFactor: view.deviceScaleFactor,
    isMobile: !!view.isMobile,
    hasTouch: !!view.hasTouch,
    userAgent: view.isMobile
      ? "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
      : undefined,
  });
  const page = await ctx.newPage();
  // Kill animations + caret blink for stable pixel comparisons.
  await page.addInitScript(() => {
    const css =
      "*,*::before,*::after{animation-duration:0s !important;animation-delay:0s !important;transition-duration:0s !important;transition-delay:0s !important;caret-color:transparent !important;}";
    const style = document.createElement("style");
    style.appendChild(document.createTextNode(css));
    document.documentElement.appendChild(style);
  });
  // Seed the gateway token into localStorage BEFORE any dashboard script
  // runs. The bootstrap path in dashboard.py calls
  //   fetch('/api/auth/check?token=' + encodeURIComponent(stored))
  // on every page load (see DASHBOARD_HTML inline <script>). If the token
  // matches OPENCLAW_GATEWAY_TOKEN the login overlay never shows; otherwise
  // every screenshot is just the overlay (the bug we're fixing). The same
  // injected fetch wrapper then attaches the Authorization header to every
  // subsequent /api/* call, so tabs that hit gateway-protected endpoints
  // render real data instead of 401.
  if (AUTH_TOKEN) {
    await page.addInitScript((token) => {
      try {
        localStorage.setItem("clawmetry-token", token);
        localStorage.setItem("clawmetry-gw-token", token);
      } catch {
        /* Storage disabled in some headless modes; harmless fallthrough. */
      }
    }, AUTH_TOKEN);
  }
  let ok = true;
  let httpStatus = 0;
  try {
    // The dashboard opens long-lived SSE streams (logs/brain/health), so
    // waiting for `networkidle` deadlocks. Use `domcontentloaded` and rely
    // on the explicit dwell + scroll loop below to settle content.
    const resp = await page.goto(baseUrl + "/", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    httpStatus = resp ? resp.status() : 0;
    if (!resp || resp.status() >= 400) ok = false;
    // Auth-gap canary: a 3xx on '/' means the dashboard redirected us off
    // the SPA root (e.g. to a sign-in page on a future variant). Treat as
    // a hard auth failure so the workflow loudly fails instead of posting
    // a wall of identical "login" screenshots.
    if (resp && resp.status() >= 300 && resp.status() < 400) ok = false;

    // Switch to the requested tab via the page's own router. Overview is the
    // default landing tab so we only call switchTab() for everything else.
    if (tab !== "overview") {
      try {
        await page.evaluate((name) => {
          if (typeof window.switchTab === "function") window.switchTab(name);
        }, tab);
      } catch {
        ok = false;
      }
    }

    // Let JS-driven content fetch + render. Most tabs fire one or two
    // /api/* calls and paint. networkidle would block forever if any SSE
    // stream is open, so just dwell.
    await page.waitForTimeout(1200);

    // Auth-gap canary #2: if the login overlay or the gateway-setup
    // overlay is visible after dwell, the token seed didn't take. Surface
    // it now so the workflow can fail loudly instead of publishing a wall
    // of identical overlay shots.
    const overlayBlocking = await page.evaluate(() => {
      const seen = [];
      for (const id of ["login-overlay", "gw-setup-overlay"]) {
        const el = document.getElementById(id);
        if (!el) continue;
        const cs = getComputedStyle(el);
        if (cs.display !== "none" && cs.visibility !== "hidden") {
          seen.push(id);
        }
      }
      return seen;
    });
    if (overlayBlocking.length > 0) {
      ok = false;
      console.error(
        `[auth-gap] ${baseUrl} tab=${tab} overlay still visible: ${overlayBlocking.join(", ")}`
      );
    }

    // Scroll the active panel into view + back to top so lazy-rendered
    // sections fire their IntersectionObservers.
    await page.evaluate(async () => {
      const total = document.documentElement.scrollHeight;
      const step = window.innerHeight;
      for (let y = 0; y < total; y += step) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 60));
      }
      window.scrollTo(0, 0);
      await new Promise((r) => setTimeout(r, 200));
    });

    await page.screenshot({ path: file, fullPage: true });
  } catch (err) {
    ok = false;
    console.error(`[shoot] ${baseUrl} tab=${tab} threw:`, err && err.message);
    const placeholder = new PNG({ width: 1, height: 1 });
    await fs.writeFile(file, PNG.sync.write(placeholder));
  } finally {
    await ctx.close();
  }
  return { ok, status: httpStatus };
}

async function diffPair(beforeFile, afterFile, diffFile) {
  const a = PNG.sync.read(await fs.readFile(beforeFile));
  const b = PNG.sync.read(await fs.readFile(afterFile));
  if (a.width !== b.width || a.height !== b.height) {
    // Different page heights -- declare full diff and copy "after" as the
    // visual diff for the reviewer to eyeball.
    await fs.copyFile(afterFile, diffFile);
    return 1.0;
  }
  const out = new PNG({ width: a.width, height: a.height });
  const mismatched = pixelmatch(
    a.data,
    b.data,
    out.data,
    a.width,
    a.height,
    { threshold: 0.1, includeAA: false, diffMask: false }
  );
  await fs.writeFile(diffFile, PNG.sync.write(out));
  return mismatched / (a.width * a.height);
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });

  for (const [label, url] of [
    ["BASE", BASE_URL],
    ["HEAD", HEAD_URL],
  ]) {
    if (!(await reachable(url + "/"))) {
      console.error(`${label} server unreachable at ${url}/ -- aborting.`);
      process.exit(2);
    }
  }

  // Pre-flight: verify the gateway token is accepted by both servers BEFORE
  // starting the screenshot loop. Previously, a token mismatch would silently
  // produce a wall of identical login-overlay PNGs and exit 0 (because
  // HTTP 200 is still returned by the SPA root even with the overlay up, so
  // the old status-only authGaps check never fired). Fail early and loudly.
  if (AUTH_TOKEN) {
    const preflightErrors = [];
    for (const [label, url] of [["BASE", BASE_URL], ["HEAD", HEAD_URL]]) {
      const err = await preflightAuth(url, AUTH_TOKEN);
      if (err) preflightErrors.push(`${label}: ${err}`);
    }
    if (preflightErrors.length > 0) {
      console.error(
        "\nPre-flight auth check FAILED. The gateway token is not accepted.\n" +
        "Every screenshot would just be the login overlay -- aborting early.\n" +
        preflightErrors.map((s) => "  " + s).join("\n") + "\n"
      );
      process.exit(3);
    }
    console.log("[preflight] auth OK on BASE and HEAD");
  }

  const browser = await chromium.launch();
  const manifest = [];
  const authGaps = [];

  for (const view of VIEWS) {
    for (const tab of TABS) {
      const slug = slugify(tab);
      const beforeFile = path.join(OUT_DIR, `${view.name}__${slug}__before.png`);
      const afterFile = path.join(OUT_DIR, `${view.name}__${slug}__after.png`);
      const diffFile = path.join(OUT_DIR, `${view.name}__${slug}__diff.png`);

      const baseRes = await shoot(browser, BASE_URL, view, tab, beforeFile);
      const headRes = await shoot(browser, HEAD_URL, view, tab, afterFile);
      const diffPct = await diffPair(beforeFile, afterFile, diffFile);

      // Sanity gate: '/' must return HTTP 200 AND no auth overlay must be
      // visible. A non-200 means the SPA didn't render. ok=false with HTTP 200
      // means an overlay was visible after token injection (shoot() sets
      // ok=false when #login-overlay / #gw-setup-overlay is visible, but the
      // old code never added that to authGaps -- fixed here).
      for (const [label, res] of [["base", baseRes], ["head", headRes]]) {
        if (res.status !== 200) {
          authGaps.push(
            `${label} ${view.name}/${tab}: HTTP ${res.status || "no-response"} (expected 200)`
          );
        } else if (!res.ok) {
          // HTTP 200 but ok=false: shoot() detected an auth overlay or render
          // error. Treat as an auth gap so the workflow fails loudly instead of
          // silently posting overlay screenshots with a green exit code.
          authGaps.push(
            `${label} ${view.name}/${tab}: auth overlay visible or render error (token not accepted)`
          );
        }
      }

      const entry = {
        view: view.name,
        tab,
        slug,
        diffPct,
        hasDiff: diffPct > 0.01,
        baseOk: baseRes.ok,
        headOk: headRes.ok,
        baseStatus: baseRes.status,
        headStatus: headRes.status,
      };
      manifest.push(entry);
      console.log(
        `[diff] ${view.name} ${tab} -> ${(diffPct * 100).toFixed(2)}%${
          entry.hasDiff ? " (FLAGGED)" : ""
        }${baseRes.ok && headRes.ok ? "" : " [render-error]"} base=${baseRes.status} head=${headRes.status}`
      );
    }
  }

  await browser.close();
  await fs.writeFile(
    path.join(OUT_DIR, "manifest.json"),
    JSON.stringify(manifest, null, 2)
  );
  console.log(`Wrote ${manifest.length} comparisons to ${OUT_DIR}/`);

  if (authGaps.length > 0) {
    console.error(
      "\nAuth gap: one or more tabs had a non-200 response or a visible auth overlay.\n" +
        "The gateway token was not accepted. Captured PNGs are likely login overlays,\n" +
        "not real tab content. Fix the boot config:\n" +
        "OPENCLAW_GATEWAY_TOKEN + CLAWMETRY_VISUAL_DIFF_TOKEN must match."
    );
    for (const gap of authGaps) console.error("  - " + gap);
    process.exit(3);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
