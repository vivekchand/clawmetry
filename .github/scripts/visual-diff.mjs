#!/usr/bin/env node
/**
 * visual-diff.mjs — capture full-page screenshots of the same dashboard
 * "tabs" on two running clawmetry dashboards (BASE_URL vs HEAD_URL),
 * pixel-diff them, and write artefacts under OUT_DIR.
 *
 * The clawmetry dashboard is a single-page Flask app — every tab lives at
 * `/` and is switched via the global `switchTab(name)` JS function (no
 * query-string, no hash routing). So we navigate once per tab to `/`, then
 * call `switchTab(<name>)` via Playwright `evaluate`, settle, and screenshot.
 *
 * Inputs (env):
 *   BASE_URL              http://127.0.0.1:8081
 *   HEAD_URL              http://127.0.0.1:8082
 *   OUT_DIR               directory for *.png + manifest.json
 *   PR_SCREENSHOT_TABS    comma-separated tab names (default below)
 *
 * Output:
 *   $OUT_DIR/<view>__<slug>__before.png
 *   $OUT_DIR/<view>__<slug>__after.png
 *   $OUT_DIR/<view>__<slug>__diff.png
 *   $OUT_DIR/manifest.json — [{view, tab, slug, diffPct, hasDiff, baseOk, headOk}]
 *
 * Exits 0 even with diffs — workflow consumes manifest.json and decides.
 */
import { chromium } from "playwright";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8081";
const HEAD_URL = process.env.HEAD_URL || "http://127.0.0.1:8082";
const OUT_DIR = process.env.OUT_DIR || "screenshots";

// Tabs that actually exist on the OSS dashboard nav (see dashboard.py
// switchTab() handlers + the .nav-tab buttons). `overview` is the implicit
// default — listed first so we get a `root` baseline shot.
const DEFAULT_TABS =
  "overview,flow,brain,approvals,alerts,notifications,context,usage,crons,memory,security";
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
  let ok = true;
  try {
    // The dashboard opens long-lived SSE streams (logs/brain/health), so
    // waiting for `networkidle` deadlocks. Use `domcontentloaded` and rely
    // on the explicit dwell + scroll loop below to settle content.
    const resp = await page.goto(baseUrl + "/", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    if (!resp || resp.status() >= 400) ok = false;

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
  } catch {
    ok = false;
    const placeholder = new PNG({ width: 1, height: 1 });
    await fs.writeFile(file, PNG.sync.write(placeholder));
  } finally {
    await ctx.close();
  }
  return ok;
}

async function diffPair(beforeFile, afterFile, diffFile) {
  const a = PNG.sync.read(await fs.readFile(beforeFile));
  const b = PNG.sync.read(await fs.readFile(afterFile));
  if (a.width !== b.width || a.height !== b.height) {
    // Different page heights — declare full diff and copy "after" as the
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
      console.error(`${label} server unreachable at ${url}/ — aborting.`);
      process.exit(2);
    }
  }

  const browser = await chromium.launch();
  const manifest = [];

  for (const view of VIEWS) {
    for (const tab of TABS) {
      const slug = slugify(tab);
      const beforeFile = path.join(OUT_DIR, `${view.name}__${slug}__before.png`);
      const afterFile = path.join(OUT_DIR, `${view.name}__${slug}__after.png`);
      const diffFile = path.join(OUT_DIR, `${view.name}__${slug}__diff.png`);

      const baseOk = await shoot(browser, BASE_URL, view, tab, beforeFile);
      const headOk = await shoot(browser, HEAD_URL, view, tab, afterFile);
      const diffPct = await diffPair(beforeFile, afterFile, diffFile);
      const entry = {
        view: view.name,
        tab,
        slug,
        diffPct,
        hasDiff: diffPct > 0.01,
        baseOk,
        headOk,
      };
      manifest.push(entry);
      console.log(
        `[diff] ${view.name} ${tab} -> ${(diffPct * 100).toFixed(2)}%${
          entry.hasDiff ? " (FLAGGED)" : ""
        }${baseOk && headOk ? "" : " [render-error]"}`
      );
    }
  }

  await browser.close();
  await fs.writeFile(
    path.join(OUT_DIR, "manifest.json"),
    JSON.stringify(manifest, null, 2)
  );
  console.log(`Wrote ${manifest.length} comparisons to ${OUT_DIR}/`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
