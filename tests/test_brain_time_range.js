// Unit tests for the Brain date-time range filter ("what happened at 3AM?").
//
// The historical-window view is only trustworthy if the LIVE machinery is
// fully gated while a range is active: before these guards, three code paths
// (SSE reconnect flush, the es.onerror poll fallback, and _startBrainSSE
// itself) would clobber a historical view with fresh live events.
//
// Extraction pattern mirrors test_brain_sse_reconnect.js: pull the shipped
// functions out of app.js via regex + vm so the test always tracks the real
// source, no bundler needed.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
  if (actual === expected) { passed++; console.log('  ok   ' + label); }
  else {
    failed++;
    console.log('  FAIL ' + label);
    console.log('       expected: ' + JSON.stringify(expected));
    console.log('       actual:   ' + JSON.stringify(actual));
  }
}

function truthy(v, label) {
  if (v) { passed++; console.log('  ok   ' + label); }
  else { failed++; console.log('  FAIL ' + label + ' (got falsy)'); }
}

function extractFunction(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

function el(overrides) {
  return Object.assign({
    style: {},
    value: '',
    textContent: '',
    innerHTML: '',
    classList: {
      toggle: function () {},
      contains: function () { return true; },
      add: function () {},
      remove: function () {},
    },
    getAttribute: function () { return null; },
  }, overrides || {});
}

function buildSandbox(domById) {
  domById = domById || {};
  const sandbox = {
    console: console,
    Date: Date,
    isNaN: isNaN,
    isFinite: isFinite,
    parseInt: parseInt,
    encodeURIComponent: encodeURIComponent,
    JSON: JSON,
    Math: Math,
    // state the extracted functions reference
    _brainRange: null,
    _brainRangeRetries: 0,
    _brainRefreshTimer: null,
    _brainSSE: null,
    _brainSSEConnected: false,
    _brainSSERetryTimer: null,
    _brainSSERetryAttempt: 0,
    _brainSSEFirstFailMs: 0,
    _BRAIN_SSE_BACKOFF_MS: [1000, 2000, 4000],
    _BRAIN_SSE_BACKOFF_MAX_MS: 30000,
    _BRAIN_SSE_BANNER_THRESHOLD_MS: 30000,
    // call recorders
    _calls: { stopSSE: 0, loadBrain: 0, setTimeoutCount: 0, eventSourceCount: 0 },
    _stopBrainSSE: null, // installed below so it can record
    loadBrainPage: null,
    t: function (k, a, fallback) { return fallback || k; },
    setTimeout: null,
    clearTimeout: function () {},
    _showBrainConnectionLostBanner: function () {},
    localStorage: { getItem: function () { return null; } },
    document: {
      hidden: false,
      getElementById: function (id) {
        return Object.prototype.hasOwnProperty.call(domById, id) ? domById[id] : el();
      },
      querySelector: function () { return el(); },
      querySelectorAll: function () { return []; },
    },
  };
  sandbox._stopBrainSSE = function () { sandbox._calls.stopSSE++; };
  sandbox.loadBrainPage = function () { sandbox._calls.loadBrain++; };
  sandbox.setTimeout = function () { sandbox._calls.setTimeoutCount++; return 1; };
  sandbox.EventSource = function () {
    sandbox._calls.eventSourceCount++;
    this.addEventListener = function () {};
    this.close = function () {};
  };
  sandbox._updateBrainLiveIndicator = function () {};
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  const fns = [
    '_brainRangeIso', '_brainRangeHuman', '_brainSetRangeActiveBtn',
    '_brainUpdateRangeUI', 'setBrainTimeRange', 'applyBrainCustomRange',
    '_enterBrainHistoryMode', '_startBrainSSE', '_scheduleBrainSSEReconnect',
  ];
  fns.forEach(function (n) { vm.runInContext(extractFunction(n), sandbox); });
  // _startBrainSSE / _scheduleBrainSSEReconnect were re-defined by the
  // extraction; the recorders above are only for stop/load/timeouts.
  return sandbox;
}

// ── (1) ISO formatting ──────────────────────────────────────────────────
console.log('PASS group: _brainRangeIso');
{
  const sb = buildSandbox();
  const iso = vm.runInContext('_brainRangeIso(new Date(Date.UTC(2026, 6, 10, 3, 0, 0)))', sb);
  eq(iso, '2026-07-10T03:00:00Z', 'formats second-precision UTC ISO with Z');
}

// ── (2) preset sets a frozen window and freezes live machinery ──────────
console.log('PASS group: setBrainTimeRange presets');
{
  const sb = buildSandbox();
  vm.runInContext('setBrainTimeRange(3600)', sb);
  truthy(sb._brainRange, 'preset sets _brainRange');
  const spanMs = new Date(sb._brainRange.until) - new Date(sb._brainRange.since);
  eq(spanMs, 3600000, 'preset window spans exactly 1h');
  eq(sb._calls.stopSSE, 1, 'entering history mode stops the SSE stream');
  eq(sb._calls.loadBrain, 1, 'entering history mode fetches the window');
}

// ── (3) Back to live clears the range and reloads ───────────────────────
console.log('PASS group: back to live');
{
  const sb = buildSandbox();
  vm.runInContext('setBrainTimeRange(3600)', sb);
  vm.runInContext("setBrainTimeRange('live')", sb);
  eq(sb._brainRange, null, 'live clears _brainRange');
  eq(sb._calls.loadBrain, 2, 'back-to-live reloads the live feed');
}

// ── (4) custom range swaps reversed bounds ──────────────────────────────
console.log('PASS group: applyBrainCustomRange');
{
  const from = el({ value: '2026-07-10T05:00' });
  const to = el({ value: '2026-07-10T03:00' });
  const sb = buildSandbox({ 'brain-range-from': from, 'brain-range-to': to });
  vm.runInContext('applyBrainCustomRange()', sb);
  truthy(sb._brainRange, 'custom range applied');
  truthy(new Date(sb._brainRange.since) < new Date(sb._brainRange.until),
         'reversed from/to inputs are swapped, never an inverted window');
}

// ── (5) live stream cannot open while a range is active ─────────────────
console.log('PASS group: SSE gating in history mode');
{
  const sb = buildSandbox();
  vm.runInContext('_brainRange = {since: "2026-07-10T02:00:00Z", until: "2026-07-10T04:00:00Z"};', sb);
  vm.runInContext('_startBrainSSE()', sb);
  eq(sb._calls.eventSourceCount, 0, '_startBrainSSE refuses to open an EventSource in history mode');
  vm.runInContext('_scheduleBrainSSEReconnect()', sb);
  eq(sb._calls.setTimeoutCount, 0, '_scheduleBrainSSEReconnect schedules nothing in history mode');
}

// ── (6) live mode still opens SSE (the gate is not stuck) ───────────────
console.log('PASS group: live mode unaffected');
{
  const sb = buildSandbox();
  vm.runInContext('_brainRange = null;', sb);
  vm.runInContext('_startBrainSSE()', sb);
  eq(sb._calls.eventSourceCount, 1, '_startBrainSSE opens normally when live');
}

// ── (7) source-level guards for paths vm can't easily execute ───────────
console.log('PASS group: source-level gating anchors');
{
  truthy(/if \(_brainSSEEverConnected && !_brainRange\)/.test(src),
         'SSE reconnect flush is gated on !_brainRange');
  truthy(/if \(_brainRange\) return; \/\/ stale response for an old range|_bhRange !== _brainRange\) return/.test(src),
         'loadBrainPage drops stale responses for an old range');
  truthy(/if \(!_brainRange && document\.getElementById\('page-brain'\)/.test(src),
         'es.onerror poll fallback is gated on !_brainRange');
}

console.log('');
console.log('PASS ' + passed + ' / FAIL ' + failed);
process.exit(failed === 0 ? 0 : 1);
