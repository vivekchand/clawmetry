// Unit tests for issue #1596 — Brain SSE exponential-backoff reconnect.
//
// Before this fix the EventSource.onerror handler only scheduled a single
// `loadBrainPage(true)` poll 5s later, then went silent forever. If that
// poll also failed (still partitioned) the user saw an indefinitely stale
// feed with no UI signal beyond the small "● POLLING" pill.
//
// We pull the helpers out of the shipped app.js source via regex + vm —
// same pattern as test_appjs_units.js — and exercise:
//
//   (1) _brainSSEBackoffMs returns the 1s/2s/4s/8s/16s/30s ladder.
//   (2) _scheduleBrainSSEReconnect schedules a NEW retry every time the
//       previous one fails (i.e. the bug: only one retry, ever).
//   (3) After >30s of failed retries _showBrainConnectionLostBanner has
//       been invoked (banner surfaces) and the copy is no-em-dash + non-
//       technical (per feedback_no_em_dashes_in_user_facing_copy.md +
//       feedback_simple_ui_for_nontechnical.md).
//   (4) Multiple back-to-back onerror calls do NOT spawn parallel retry
//       chains — single chain only (no retry storm).
//   (5) _resetBrainSSEReconnectState clears banner + retry on connect.

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

function truthy(value, label) {
  if (value) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label + ' (got falsy)');
  }
}

function extractFunction(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

// Build a sandbox with the brain-SSE module-level vars + the helpers we
// want to exercise. We pull the `var _brainSSE…` declarations + caps
// directly out of app.js so the test always tracks the shipped values.
function buildSandbox(opts) {
  opts = opts || {};
  const lines = src.split('\n');
  const wantedVars = [
    'var _brainSSE = null;',
    'var _brainSSEConnected = false;',
    'var _brainSSERetryTimer = null;',
    'var _brainSSERetryAttempt = 0;',
    'var _brainSSEFirstFailMs = 0;',
    'var _BRAIN_SSE_BACKOFF_MS = ',
    'var _BRAIN_SSE_BACKOFF_MAX_MS = ',
    'var _BRAIN_SSE_BANNER_THRESHOLD_MS = ',
    'var _brainRefreshTimer = null;',
  ];
  const varLines = [];
  wantedVars.forEach(function(prefix) {
    const found = lines.find(function(l) { return l.indexOf(prefix) === 0; });
    if (!found) throw new Error('missing var line: ' + prefix);
    varLines.push(found);
  });

  // Banner host + brain stream stub so insertBefore() doesn't crash.
  // We'll record show/hide via instrumentation on document.createElement.
  const created = [];
  const bannerEl = { id: '', style: { cssText: '', display: '' }, innerHTML: '' };
  // Pre-existing brain-stream element so banner host can be appended.
  const streamParent = {
    insertBefore: function(child) { created.push(child); },
  };
  const streamEl = { parentElement: streamParent };

  // page-brain element controls whether retries are scheduled at all.
  const pageBrain = {
    classList: {
      _active: opts.pageActive !== false,
      contains: function(cls) { return cls === 'active' && this._active; },
    },
  };

  const sandbox = {
    Date: Date,
    console: console,
    // Track scheduled timers so the test can drive time deterministically.
    _timers: [],
    _nextTimerId: 1,
    setTimeout: function(fn, ms) {
      const id = sandbox._nextTimerId++;
      sandbox._timers.push({ id: id, fn: fn, ms: ms });
      return id;
    },
    clearTimeout: function(id) {
      sandbox._timers = sandbox._timers.filter(function(t) { return t.id !== id; });
    },
    document: {
      hidden: !!opts.hidden,
      getElementById: function(id) {
        if (id === 'brain-stream') return streamEl;
        if (id === 'page-brain') return pageBrain;
        if (id === 'brain-connection-lost-banner') {
          return sandbox._bannerVisible ? bannerEl : null;
        }
        if (id === 'brain-live-indicator') return null;
        return null;
      },
      createElement: function(tag) {
        // Mark banner as live the moment _showBrainConnectionLostBanner
        // runs, so subsequent getElementById('brain-connection-lost-banner')
        // returns the same element (matches real DOM lifecycle).
        sandbox._bannerVisible = true;
        return bannerEl;
      },
    },
    _bannerVisible: false,
    _bannerEl: bannerEl,
    loadBrainPage: function() {},
  };

  // Build the source string we'll evaluate in the sandbox.
  let code = varLines.join('\n') + '\n';
  const fns = [
    '_brainSSEBackoffMs',
    '_updateBrainLiveIndicator',
    '_showBrainConnectionLostBanner',
    '_hideBrainConnectionLostBanner',
    '_scheduleBrainSSEReconnect',
    '_resetBrainSSEReconnectState',
    '_stopBrainSSE',
  ];
  fns.forEach(function(name) { code += extractFunction(name) + '\n'; });

  // Stub _startBrainSSE because we don't want to construct a real
  // EventSource — the retry chain should _call_ it via the timer, and
  // the test asserts the call count.
  code += 'function _startBrainSSE() { sandbox_startCalls = (sandbox_startCalls || 0) + 1; }\n';
  code += 'var sandbox_startCalls = 0;\n';

  code += 'this.api = {\n';
  code += '  _brainSSEBackoffMs: _brainSSEBackoffMs,\n';
  code += '  _scheduleBrainSSEReconnect: _scheduleBrainSSEReconnect,\n';
  code += '  _resetBrainSSEReconnectState: _resetBrainSSEReconnectState,\n';
  code += '  _showBrainConnectionLostBanner: _showBrainConnectionLostBanner,\n';
  code += '  _hideBrainConnectionLostBanner: _hideBrainConnectionLostBanner,\n';
  code += '  _stopBrainSSE: _stopBrainSSE,\n';
  code += '  getStartCalls: function() { return sandbox_startCalls; },\n';
  code += '  getRetryAttempt: function() { return _brainSSERetryAttempt; },\n';
  code += '  getFirstFailMs: function() { return _brainSSEFirstFailMs; },\n';
  code += '  setFirstFailMs: function(v) { _brainSSEFirstFailMs = v; },\n';
  code += '  getRetryTimer: function() { return _brainSSERetryTimer; },\n';
  code += '};';

  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  return { sandbox: sandbox, api: sandbox.api, created: created, bannerEl: bannerEl };
}

// Pop the next-due timer and fire it (simulates the wall clock).
function fireNextTimer(sandbox) {
  if (sandbox._timers.length === 0) return null;
  // Fire in FIFO order — we only schedule one at a time.
  const t = sandbox._timers.shift();
  t.fn();
  return t;
}

// ── Case 1 — backoff ladder ────────────────────────────────────────────
console.log('_brainSSEBackoffMs ladder (issue #1596)');
{
  const { api } = buildSandbox();
  eq(api._brainSSEBackoffMs(0), 1000, 'attempt 0 → 1s');
  eq(api._brainSSEBackoffMs(1), 2000, 'attempt 1 → 2s');
  eq(api._brainSSEBackoffMs(2), 4000, 'attempt 2 → 4s');
  eq(api._brainSSEBackoffMs(3), 8000, 'attempt 3 → 8s');
  eq(api._brainSSEBackoffMs(4), 16000, 'attempt 4 → 16s');
  eq(api._brainSSEBackoffMs(5), 30000, 'attempt 5 → 30s (cap)');
  eq(api._brainSSEBackoffMs(99), 30000, 'attempt 99 → 30s (still capped)');
  eq(api._brainSSEBackoffMs(-1), 1000, 'negative attempt → 1s (clamp)');
}

// ── Case 2 — reconnect AFTER one failed poll fallback ──────────────────
//
// This is the bug. Before #1596 the onerror handler scheduled one poll
// and stopped. We assert that successive failures keep adding to the
// retry chain — i.e. _startBrainSSE gets called again and again.
console.log('reconnect chain survives failed poll fallback (issue #1596)');
{
  const { api, sandbox } = buildSandbox();

  // Simulate first failure — caller would have set _brainSSEFirstFailMs.
  api.setFirstFailMs(Date.now());
  api._scheduleBrainSSEReconnect();
  eq(sandbox._timers.length, 1, 'first failure schedules 1 retry timer');
  eq(sandbox._timers[0].ms, 1000, 'first retry uses 1s backoff');

  // Fire the timer — that calls _startBrainSSE once. Now simulate the
  // reconnect also failing — caller (onerror) would call _schedule again.
  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 1, '_startBrainSSE called once after 1st timer');
  api._scheduleBrainSSEReconnect();
  eq(sandbox._timers.length, 1, 'second failure schedules another retry');
  eq(sandbox._timers[0].ms, 2000, 'second retry uses 2s backoff (chain continues)');

  // Fire + schedule again — chain keeps going at 4s.
  fireNextTimer(sandbox);
  api._scheduleBrainSSEReconnect();
  eq(sandbox._timers[0].ms, 4000, 'third retry uses 4s backoff (chain continues)');

  // The bug shape: before the fix, schedule was only called once and
  // never re-scheduled. With the fix every onerror calls schedule, and
  // the chain keeps producing _startBrainSSE attempts indefinitely.
  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 3, '3 retry attempts fired in total — no silent death');
}

// ── Case 3 — banner shows after >30s of failed retries ─────────────────
console.log('connection-lost banner surfaces after 30s of failed retries (issue #1596)');
{
  const { api, sandbox, bannerEl } = buildSandbox();

  // Simulate first failure at T=0.
  const t0 = Date.now();
  api.setFirstFailMs(t0 - 31000); // 31s ago — past the 30s threshold

  // Schedule a retry — _scheduleBrainSSEReconnect should show the banner.
  api._scheduleBrainSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown after 30s of failed retries');

  // Banner copy must be non-technical + no em-dashes (per memory).
  truthy(bannerEl.innerHTML.indexOf('Connection lost') !== -1,
    'banner contains "Connection lost"');
  truthy(bannerEl.innerHTML.indexOf('Reconnecting') !== -1,
    'banner contains "Reconnecting"');
  truthy(bannerEl.innerHTML.indexOf('—') === -1,
    'banner contains NO em-dash (feedback_no_em_dashes_in_user_facing_copy.md)');
  truthy(bannerEl.innerHTML.indexOf('--') === -1,
    'banner contains NO double-dash');
  truthy(bannerEl.innerHTML.indexOf('readyState') === -1,
    'banner does NOT leak technical jargon (feedback_simple_ui_for_nontechnical.md)');
  truthy(bannerEl.innerHTML.indexOf('EventSource') === -1,
    'banner does NOT mention "EventSource" jargon');
  truthy(bannerEl.innerHTML.indexOf('WebSocket') === -1,
    'banner does NOT mention "WebSocket" jargon');

  // Counter-case: fresh failure (<30s) does NOT show the banner.
  const fresh = buildSandbox();
  fresh.api.setFirstFailMs(Date.now() - 5000); // 5s ago
  fresh.api._scheduleBrainSSEReconnect();
  eq(fresh.sandbox._bannerVisible, false,
    'fresh <30s failure does NOT surface banner (avoid noise on transient blips)');
}

// ── Case 4 — single retry chain, no parallel storm ─────────────────────
console.log('no parallel retry storm on rapid onerror bursts (issue #1596)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now());

  // 10 back-to-back schedules (e.g. a flapping connection firing onerror
  // repeatedly before the first retry has even fired). The chain MUST
  // collapse them into a single pending timer, NOT spawn 10 parallel
  // retries that would all fire and reconnect 10 EventSources.
  for (let i = 0; i < 10; i++) api._scheduleBrainSSEReconnect();
  eq(sandbox._timers.length, 1,
    '10 rapid schedules → 1 pending timer (single chain, no storm)');
}

// ── Case 5 — _resetBrainSSEReconnectState clears banner + chain ────────
console.log('_resetBrainSSEReconnectState clears banner + chain on connect (issue #1596)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleBrainSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown before reset');
  eq(sandbox._timers.length, 1, 'timer pending before reset');

  api._resetBrainSSEReconnectState();
  eq(sandbox._timers.length, 0, 'timer cleared after reset');
  eq(api.getRetryAttempt(), 0, 'retry attempt reset to 0');
  eq(api.getFirstFailMs(), 0, 'first-fail timestamp reset to 0');
  // bannerEl.style.display set to 'none' — banner is now hidden.
  eq(sandbox._bannerEl.style.display, 'none', 'banner hidden after reset');
}

// ── Case 6 — visibility-aware retry (pause when tab hidden) ────────────
console.log('retries pause when tab hidden (issue #1596 — optional visibility guard)');
{
  const { api, sandbox } = buildSandbox({ hidden: true });
  api.setFirstFailMs(Date.now());
  api._scheduleBrainSSEReconnect();
  eq(sandbox._timers.length, 0,
    'hidden tab → no retry scheduled (deferred until visible)');
}

// ── Case 7 — leaving brain page tears down retry chain ─────────────────
console.log('_stopBrainSSE tears down retry chain (issue #1596 — no stale timers)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleBrainSSEReconnect();
  truthy(sandbox._timers.length === 1, 'timer pending before stop');
  truthy(sandbox._bannerVisible, 'banner shown before stop');

  api._stopBrainSSE();
  eq(sandbox._timers.length, 0, 'timer cleared after _stopBrainSSE');
  eq(api.getRetryAttempt(), 0, 'retry attempt reset on stop');
  eq(api.getFirstFailMs(), 0, 'first-fail timestamp reset on stop');
  eq(sandbox._bannerEl.style.display, 'none', 'banner hidden on stop');
}

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' — ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
