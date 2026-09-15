// Dashboard cold load (#5935): startup must not load screens nobody opened,
// and must not send the same request twice.
//
// Measured before the fix: 121 API requests in one page load, 103 in the
// first 10 s, 22 in flight at the peak, against the browser's six connections
// per origin. The page lands on Sessions, yet startup loaded the whole
// Overview plus a Crons and Memory prefetch, so the requests the visible
// screen needed waited in the browser queue until their client timeouts fired
// ("Initial load failed timeout", "System health load failed timeout",
// "loadCrons failed timeout").
//
// Runs under `node tests/test_cold_load_boot_js.js` (no jsdom, well under a
// second). Pulls the real functions out of app.js so this tests shipped source.
// Factory requirement 08aff8e1-2a68-41c2-8052-da53bbbdd749, AC 2 and AC 3.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
  if (actual === expected) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label);
    console.log('       expected: ' + JSON.stringify(expected));
    console.log('       actual:   ' + JSON.stringify(actual));
  }
}

function extract(name, isAsync) {
  const re = new RegExp('^' + (isAsync ? 'async ' : '') + 'function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

// Helpers that may not exist on a pre-#5935 build: fall back to a stub so the
// suite reports the BEHAVIOUR difference instead of dying on a missing name.
function extractOr(name, fallback) {
  try { return extract(name, false); } catch (e) { return fallback; }
}

const HELPERS = [
  extract('_cmIsOverviewTab', false),
  'var _cmWidgetLoadedAt = {};',
  extractOr('_cmMarkLoaded', 'function _cmMarkLoaded(k) { _cmWidgetLoadedAt[k] = Date.now(); }'),
  extractOr('_cmLoadedWithin', 'function _cmLoadedWithin() { return false; }'),
].join('\n');

function counters() {
  const c = {};
  const bump = (k) => function () { c[k] = (c[k] || 0) + 1; return Promise.resolve(true); };
  return { c, bump };
}

function fakeElement() {
  return { style: {}, textContent: '', innerHTML: '', classList: { add() {}, remove() {} } };
}

// ── 1. bootDashboard loads only the landing screen ────────────────────────
async function bootWith(currentTab) {
  const { c, bump } = counters();
  const sandbox = {
    console,
    Promise,
    Date,
    localStorage: { getItem: () => null, setItem() {} },
    fetch: () => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ authRequired: false, valid: true, needsSetup: false }),
    }),
    // Timers never fire: the suite checks what boot STARTS, not what a
    // safety timeout does 8 s later.
    setTimeout: () => 0,
    document: { getElementById: () => fakeElement() },
    t: (k, p, fallback) => fallback,
    setBootStep: () => {},
    _safeFinishBoot: () => {},
    _shouldPingAuthFailFirstLoad: () => false,
    _pingAuthFailFirstLoad: () => {},
    loadAll: bump('loadAll'),
    loadOverviewTasks: bump('loadOverviewTasks'),
    loadSystemHealth: bump('loadSystemHealth'),
    loadCrons: bump('loadCrons'),
    loadMemory: bump('loadMemory'),
    loadSandboxStatus: () => {},
    startLogStream: () => {},
    startHealthStream: () => {},
    startSystemHealthRefresh: () => {},
    startOverviewRefresh: () => {},
    startOverviewTasksRefresh: () => {},
  };
  vm.createContext(sandbox);
  vm.runInContext(
    'var BOOT_HARD_TIMEOUT_MS = 8000;\n'
    + 'var _cmCurrentTab = ' + JSON.stringify(currentTab) + ';\n'
    + HELPERS + '\n'
    + extract('_withTimeout', false) + '\n'
    + extract('bootDashboard', true) + '\n'
    + 'this._boot = bootDashboard;',
    sandbox,
  );
  await sandbox._boot();
  // Let the microtasks boot chained settle.
  for (let i = 0; i < 20; i++) await Promise.resolve();
  return c;
}

// ── 2. loadCrons asks for cron health once ────────────────────────────────
async function cronsHealthCalls() {
  const { c, bump } = counters();
  const sandbox = {
    console,
    Promise,
    window: { CLOUD_MODE: false },
    fetchJsonWithTimeout: () => Promise.resolve({ jobs: [] }),
    fetch: () => Promise.resolve({ json: () => Promise.resolve({ jobs: [] }) }),
    document: { querySelectorAll: () => [], getElementById: () => null },
    renderCrons: () => {},
    loadCronHealth: bump('loadCronHealth'),
    loadQueueLanes: () => {},
    loadCronsMultiNode: () => {},
    visibilitySetInterval: () => 0,
    escHtml: (s) => s,
  };
  vm.createContext(sandbox);
  vm.runInContext(
    'var _cronJobs = []; var _cronActionsAvailable = false; var _cronWritesAvailable = false;'
    + ' var _cronAutoRefreshTimer = null;\n'
    + extract('loadCrons', true) + '\nthis._load = loadCrons;',
    sandbox,
  );
  await sandbox._load();
  return c.loadCronHealth || 0;
}

// ── 3. the refresh starters do not repeat a load startup just did ─────────
function starter(fnName, loaderName, loadedKey, currentTab, justLoaded) {
  const { c, bump } = counters();
  const sandbox = {
    console,
    Date,
    window: {},
    clearInterval: () => {},
    visibilitySetInterval: () => 0,
  };
  sandbox[loaderName] = bump(loaderName);
  vm.createContext(sandbox);
  vm.runInContext(
    'var _cmCurrentTab = ' + JSON.stringify(currentTab) + '; var _ovTasksTimer = null;\n'
    + HELPERS + '\n'
    + (justLoaded ? '_cmMarkLoaded(' + JSON.stringify(loadedKey) + ');\n' : '')
    + extract(fnName, false) + '\nthis._start = ' + fnName + ';',
    sandbox,
  );
  sandbox._start();
  return c[loaderName] || 0;
}

// ── 4. consumers of /api/overview share ONE request (AC 3) ───────────────
async function sharedOverview() {
  let fetches = 0;
  let release;
  const gate = new Promise((r) => { release = r; });
  const sandbox = {
    console,
    Promise,
    AbortController,
    setTimeout,
    clearTimeout,
    fetch: (url) => {
      fetches++;
      return gate.then(() => ({ ok: true, json: () => Promise.resolve({ url: url, n: fetches }) }));
    },
  };
  vm.createContext(sandbox);
  let helper;
  try { helper = extract('_cmFetchOverviewShared', false); } catch (e) { return { missing: true }; }
  const budget = src.match(/^var _CM_OVERVIEW_BUDGET_MS = \d+;/m);
  vm.runInContext(
    'var _inflightJsonFetches = {};\n'
    + (budget ? budget[0] : '') + '\n'
    + extract('fetchJsonWithTimeout', true) + '\n'
    + helper + '\nthis._shared = _cmFetchOverviewShared;',
    sandbox,
  );
  // Five consumers ask while the first request is still in flight.
  const pending = [1, 2, 3, 4, 5].map(() => sandbox._shared());
  release();
  const answers = await Promise.all(pending);
  const duringFlight = fetches;
  const same = answers.every((a) => a === answers[0]);
  // After it settles, a later refresh must fetch again, not reuse a stale answer.
  await sandbox._shared();
  return { missing: false, duringFlight, same, afterSettle: fetches };
}

// ── 5. slow /api/usage never erases figures that WERE measured ────────────
// A runtime is selected and /api/usage times out with no earlier answer:
// loadMiniWidgets has just drawn that runtime's cost and tokens from
// /api/runtime-summary. The still-loading placeholders must not replace them.
function stillLoadingWith(scope) {
  const ids = ['cost-today', 'cost-week', 'cost-month', 'token-rate', 'tokens-today', 'cost-basis-badge'];
  const els = {};
  ids.forEach((id) => { els[id] = fakeElement(); els[id].textContent = 'measured'; els[id].innerHTML = 'measured'; });
  const sandbox = {
    window: { _cmRuntimeScope: scope, _cmCostTodayRaw: 1.5, _cmTodayTokensRaw: 42 },
    document: { getElementById: (id) => els[id] || null },
  };
  vm.createContext(sandbox);
  vm.runInContext(extract('_cmUsageTilesStillLoading', false) + '\nthis._f = _cmUsageTilesStillLoading;', sandbox);
  sandbox._f();
  return { els, win: sandbox.window };
}

(async function main() {
  console.log('bootDashboard: startup loads only the screen the page lands on');
  const onSessions = await bootWith('transcripts');
  eq(onSessions.loadAll || 0, 0, 'landing on Sessions does not run the Overview loadAll fan-out');
  eq(onSessions.loadSystemHealth || 0, 0, 'landing on Sessions does not load system health');
  eq(onSessions.loadOverviewTasks || 0, 0, 'landing on Sessions does not load Overview tasks');
  eq(onSessions.loadCrons || 0, 0, 'startup does not prefetch the Crons screen');
  eq(onSessions.loadMemory || 0, 0, 'startup does not prefetch the Memory screen');

  const onOverview = await bootWith('overview');
  eq(onOverview.loadAll || 0, 1, 'landing on Overview still loads it');
  eq(onOverview.loadSystemHealth || 0, 1, 'landing on Overview still loads system health');
  eq(onOverview.loadOverviewTasks || 0, 1, 'landing on Overview still loads its tasks');
  eq(onOverview.loadCrons || 0, 0, 'landing on Overview does not prefetch Crons either');

  console.log('loadCrons: one cron-health request per load');
  eq(await cronsHealthCalls(), 1, 'loadCrons calls loadCronHealth exactly once');

  console.log('refresh starters: no immediate duplicate of a load that just happened');
  eq(starter('startSystemHealthRefresh', 'loadSystemHealth', 'systemHealth', 'transcripts', false), 0,
    'system-health starter sends nothing while the page is on Sessions');
  eq(starter('startSystemHealthRefresh', 'loadSystemHealth', 'systemHealth', 'overview', true), 0,
    'system-health starter does not repeat the load startup just finished');
  eq(starter('startSystemHealthRefresh', 'loadSystemHealth', 'systemHealth', 'overview', false), 1,
    'system-health starter loads Overview when it has not loaded yet');
  eq(starter('startOverviewTasksRefresh', 'loadOverviewTasks', 'overviewTasks', 'transcripts', false), 0,
    'tasks starter sends nothing while the page is on Sessions');
  eq(starter('startOverviewTasksRefresh', 'loadOverviewTasks', 'overviewTasks', 'overview', true), 0,
    'tasks starter does not repeat the load startup just finished');
  eq(starter('startOverviewTasksRefresh', 'loadOverviewTasks', 'overviewTasks', 'overview', false), 1,
    'tasks starter loads Overview tasks when they have not loaded yet');

  console.log('shared overview request: concurrent consumers send one request');
  const so = await sharedOverview();
  eq(so.missing, false, 'app.js defines the shared overview request helper');
  if (!so.missing) {
    eq(so.duringFlight, 1, 'five concurrent consumers send exactly one /api/overview request');
    eq(so.same, true, 'every consumer receives the same answer');
    eq(so.afterSettle, 2, 'a refresh after the request settled fetches fresh data');
  }

  console.log('slow usage: placeholders only where nothing was measured');
  const scoped = stillLoadingWith({ runtime: 'codex', cost: 1.5 });
  eq(scoped.els['cost-today'].innerHTML, 'measured', 'a runtime-scoped cost tile keeps its measured figure');
  eq(scoped.els['tokens-today'].textContent, 'measured', 'a runtime-scoped token tile keeps its measured figure');
  eq(scoped.win._cmCostTodayRaw, 1.5, 'the hero still reads the runtime-scoped cost');
  const nodeWide = stillLoadingWith(null);
  eq(/still loading/.test(nodeWide.els['cost-today'].innerHTML), true, 'node-wide cost tile shows still loading');
  eq(nodeWide.els['cost-week'].textContent, '--', 'node-wide week tile shows its placeholder, not $0.00');
  eq(nodeWide.els['cost-basis-badge'].innerHTML, '', 'no basis badge beside a figure that is still loading');

  console.log('');
  console.log(passed + ' passed, ' + failed + ' failed');
  if (failed) process.exit(1);
  console.log('PASS');
})().catch(function (e) {
  console.log('FAIL (harness): ' + (e && e.stack || e));
  process.exit(1);
});
