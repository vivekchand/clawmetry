// Unit tests for the class-bug sibling drain of issue #1596 — log SSE
// exponential-backoff reconnect.
//
// Before this fix the `logStream.onerror` handler scheduled a single
// `startLogStream()` 5s later, then went silent forever if that also
// failed. Same shape as the Brain SSE bug PR #1610 fixed. This suite
// mirrors test_brain_sse_reconnect.js — same sandbox harness, same
// seven cases — applied to the log-stream helpers.
//
// Cases:
//   (1) _logSSEBackoffMs returns the 1s/2s/4s/8s/16s/30s ladder.
//   (2) _scheduleLogSSEReconnect chain survives repeated failures
//       (the bug shape: before the fix, only one retry was scheduled).
//   (3) After >30s of failed retries the banner surfaces with non-tech
//       copy ("Log connection lost"), no em-dash, no jargon.
//   (4) Rapid back-to-back schedule calls collapse to a SINGLE pending
//       timer — no parallel retry storm.
//   (5) _resetLogSSEReconnectState clears banner + chain on successful
//       reconnect (called from `onopen`).
//   (6) Hidden tab pauses the retry chain.
//   (7) _stopLogStream tears down the retry chain on explicit stop so
//       a stale timer can't reopen a closed connection.

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

function buildSandbox(opts) {
  opts = opts || {};
  const lines = src.split('\n');
  const wantedVars = [
    'var logStream = null;',
    'var _logSSERetryTimer = null;',
    'var _logSSERetryAttempt = 0;',
    'var _logSSEFirstFailMs = 0;',
    'var _LOG_SSE_BACKOFF_MS = ',
    'var _LOG_SSE_BACKOFF_MAX_MS = ',
    'var _LOG_SSE_BANNER_THRESHOLD_MS = ',
  ];
  const varLines = [];
  wantedVars.forEach(function(prefix) {
    const found = lines.find(function(l) { return l.indexOf(prefix) === 0; });
    if (!found) throw new Error('missing var line: ' + prefix);
    varLines.push(found);
  });

  const bannerEl = { id: '', style: { cssText: '', display: '' }, innerHTML: '' };
  const streamParent = {
    insertBefore: function(child) {},
  };
  const streamEl = { parentElement: streamParent };

  const sandbox = {
    Date: Date,
    console: console,
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
        if (id === 'logs-full') return streamEl;
        if (id === 'ov-logs') return streamEl;
        if (id === 'log-connection-lost-banner') {
          return sandbox._bannerVisible ? bannerEl : null;
        }
        return null;
      },
      createElement: function(tag) {
        sandbox._bannerVisible = true;
        return bannerEl;
      },
    },
    _bannerVisible: false,
    _bannerEl: bannerEl,
  };

  let code = varLines.join('\n') + '\n';
  const fns = [
    '_logSSEBackoffMs',
    '_showLogConnectionLostBanner',
    '_hideLogConnectionLostBanner',
    '_scheduleLogSSEReconnect',
    '_resetLogSSEReconnectState',
    '_stopLogStream',
  ];
  fns.forEach(function(name) { code += extractFunction(name) + '\n'; });

  // Stub startLogStream — we don't want to construct a real EventSource;
  // the retry chain should _call_ it via the timer and we assert calls.
  code += 'function startLogStream() { sandbox_startCalls = (sandbox_startCalls || 0) + 1; }\n';
  code += 'var sandbox_startCalls = 0;\n';

  code += 'this.api = {\n';
  code += '  _logSSEBackoffMs: _logSSEBackoffMs,\n';
  code += '  _scheduleLogSSEReconnect: _scheduleLogSSEReconnect,\n';
  code += '  _resetLogSSEReconnectState: _resetLogSSEReconnectState,\n';
  code += '  _showLogConnectionLostBanner: _showLogConnectionLostBanner,\n';
  code += '  _hideLogConnectionLostBanner: _hideLogConnectionLostBanner,\n';
  code += '  _stopLogStream: _stopLogStream,\n';
  code += '  getStartCalls: function() { return sandbox_startCalls; },\n';
  code += '  getRetryAttempt: function() { return _logSSERetryAttempt; },\n';
  code += '  getFirstFailMs: function() { return _logSSEFirstFailMs; },\n';
  code += '  setFirstFailMs: function(v) { _logSSEFirstFailMs = v; },\n';
  code += '  getRetryTimer: function() { return _logSSERetryTimer; },\n';
  code += '};';

  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  return { sandbox: sandbox, api: sandbox.api, bannerEl: bannerEl };
}

function fireNextTimer(sandbox) {
  if (sandbox._timers.length === 0) return null;
  const t = sandbox._timers.shift();
  t.fn();
  return t;
}

// Case 1 — backoff ladder
console.log('_logSSEBackoffMs ladder (sibling of #1610)');
{
  const { api } = buildSandbox();
  eq(api._logSSEBackoffMs(0), 1000, 'attempt 0 -> 1s');
  eq(api._logSSEBackoffMs(1), 2000, 'attempt 1 -> 2s');
  eq(api._logSSEBackoffMs(2), 4000, 'attempt 2 -> 4s');
  eq(api._logSSEBackoffMs(3), 8000, 'attempt 3 -> 8s');
  eq(api._logSSEBackoffMs(4), 16000, 'attempt 4 -> 16s');
  eq(api._logSSEBackoffMs(5), 30000, 'attempt 5 -> 30s (cap)');
  eq(api._logSSEBackoffMs(99), 30000, 'attempt 99 -> 30s (still capped)');
  eq(api._logSSEBackoffMs(-1), 1000, 'negative attempt -> 1s (clamp)');
}

// Case 2 — chain survives repeated failures (the bug shape)
console.log('reconnect chain survives repeated failures (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now());
  api._scheduleLogSSEReconnect();
  eq(sandbox._timers.length, 1, 'first failure schedules 1 retry timer');
  eq(sandbox._timers[0].ms, 1000, 'first retry uses 1s backoff');

  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 1, 'startLogStream called once after 1st timer');
  api._scheduleLogSSEReconnect();
  eq(sandbox._timers.length, 1, 'second failure schedules another retry');
  eq(sandbox._timers[0].ms, 2000, 'second retry uses 2s backoff');

  fireNextTimer(sandbox);
  api._scheduleLogSSEReconnect();
  eq(sandbox._timers[0].ms, 4000, 'third retry uses 4s backoff');

  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 3, '3 retry attempts fired in total -- no silent death');
}

// Case 3 — banner threshold
console.log('connection-lost banner surfaces after 30s of failed retries (sibling of #1610)');
{
  const { api, sandbox, bannerEl } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000); // past threshold

  api._scheduleLogSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown after 30s of failed retries');
  truthy(bannerEl.innerHTML.indexOf('Log connection lost') !== -1,
    'banner contains stream-specific copy "Log connection lost"');
  truthy(bannerEl.innerHTML.indexOf('Reconnecting') !== -1,
    'banner contains "Reconnecting"');
  truthy(bannerEl.innerHTML.indexOf('—') === -1,
    'banner contains NO em-dash (feedback_no_em_dashes_in_user_facing_copy.md)');
  truthy(bannerEl.innerHTML.indexOf('--') === -1,
    'banner contains NO double-dash');
  truthy(bannerEl.innerHTML.indexOf('readyState') === -1,
    'banner does NOT leak technical jargon');
  truthy(bannerEl.innerHTML.indexOf('EventSource') === -1,
    'banner does NOT mention "EventSource" jargon');
  truthy(bannerEl.innerHTML.indexOf('WebSocket') === -1,
    'banner does NOT mention "WebSocket" jargon');

  const fresh = buildSandbox();
  fresh.api.setFirstFailMs(Date.now() - 5000);
  fresh.api._scheduleLogSSEReconnect();
  eq(fresh.sandbox._bannerVisible, false,
    'fresh <30s failure does NOT surface banner (avoid noise on transient blips)');
}

// Case 4 — no parallel retry storm
console.log('no parallel retry storm on rapid onerror bursts (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now());
  for (let i = 0; i < 10; i++) api._scheduleLogSSEReconnect();
  eq(sandbox._timers.length, 1,
    '10 rapid schedules -> 1 pending timer (single chain, no storm)');
}

// Case 5 — reset on connect
console.log('_resetLogSSEReconnectState clears banner + chain on reconnect (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleLogSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown before reset');
  eq(sandbox._timers.length, 1, 'timer pending before reset');

  api._resetLogSSEReconnectState();
  eq(sandbox._timers.length, 0, 'timer cleared after reset');
  eq(api.getRetryAttempt(), 0, 'retry attempt reset to 0');
  eq(api.getFirstFailMs(), 0, 'first-fail timestamp reset to 0');
  eq(sandbox._bannerEl.style.display, 'none', 'banner hidden after reset');
}

// Case 6 — visibility guard
console.log('retries pause when tab hidden (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox({ hidden: true });
  api.setFirstFailMs(Date.now());
  api._scheduleLogSSEReconnect();
  eq(sandbox._timers.length, 0,
    'hidden tab -> no retry scheduled (deferred until visible)');
}

// Case 7 — _stopLogStream teardown
console.log('_stopLogStream tears down retry chain (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleLogSSEReconnect();
  truthy(sandbox._timers.length === 1, 'timer pending before stop');
  truthy(sandbox._bannerVisible, 'banner shown before stop');

  api._stopLogStream();
  eq(sandbox._timers.length, 0, 'timer cleared after _stopLogStream');
  eq(api.getRetryAttempt(), 0, 'retry attempt reset on stop');
  eq(api.getFirstFailMs(), 0, 'first-fail timestamp reset on stop');
  eq(sandbox._bannerEl.style.display, 'none', 'banner hidden on stop');
}

// Defense-in-depth: source-level scan for forbidden patterns in the
// retry path. Verifies memory: feedback_no_reload_in_bootstrap_e2e --
// no location.reload() can sneak into the SSE retry handler.
console.log('source scan: no location.reload() in log SSE retry path');
{
  // Pull every function we touch in the retry chain and assert none of
  // them contains location.reload.
  ['_scheduleLogSSEReconnect', '_resetLogSSEReconnectState', '_stopLogStream',
   '_showLogConnectionLostBanner', '_hideLogConnectionLostBanner', '_logSSEBackoffMs']
    .forEach(function(name) {
      const body = extractFunction(name);
      truthy(body.indexOf('location.reload') === -1,
        name + ' does NOT call location.reload()');
    });
}

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' -- ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
