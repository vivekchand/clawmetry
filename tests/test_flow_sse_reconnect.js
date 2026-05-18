// Unit tests for the class-bug sibling drain of issue #1596 — Flow SSE
// exponential-backoff reconnect.
//
// Before this fix the `_flowSse.onerror` handler scheduled a single
// `_startFlowSse()` 5s later, then went silent forever if that also
// failed. Same shape as the Brain SSE bug PR #1610 fixed. This suite
// mirrors test_brain_sse_reconnect.js — same sandbox harness, same
// seven cases — applied to the Flow-stream helpers.

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
    'var _flowSse = null;',
    'var _flowSSERetryTimer = null;',
    'var _flowSSERetryAttempt = 0;',
    'var _flowSSEFirstFailMs = 0;',
    'var _FLOW_SSE_BACKOFF_MS = ',
    'var _FLOW_SSE_BACKOFF_MAX_MS = ',
    'var _FLOW_SSE_BANNER_THRESHOLD_MS = ',
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
        if (id === 'flow-live-pane') return streamEl;
        if (id === 'flow-connection-lost-banner') {
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
    '_flowSSEBackoffMs',
    '_showFlowConnectionLostBanner',
    '_hideFlowConnectionLostBanner',
    '_scheduleFlowSSEReconnect',
    '_resetFlowSSEReconnectState',
    '_stopFlowSse',
  ];
  fns.forEach(function(name) { code += extractFunction(name) + '\n'; });

  // Stub _startFlowSse — no real EventSource. The retry chain calls it
  // via the timer; we assert the call count.
  code += 'function _startFlowSse() { sandbox_startCalls = (sandbox_startCalls || 0) + 1; }\n';
  code += 'var sandbox_startCalls = 0;\n';

  code += 'this.api = {\n';
  code += '  _flowSSEBackoffMs: _flowSSEBackoffMs,\n';
  code += '  _scheduleFlowSSEReconnect: _scheduleFlowSSEReconnect,\n';
  code += '  _resetFlowSSEReconnectState: _resetFlowSSEReconnectState,\n';
  code += '  _showFlowConnectionLostBanner: _showFlowConnectionLostBanner,\n';
  code += '  _hideFlowConnectionLostBanner: _hideFlowConnectionLostBanner,\n';
  code += '  _stopFlowSse: _stopFlowSse,\n';
  code += '  getStartCalls: function() { return sandbox_startCalls; },\n';
  code += '  getRetryAttempt: function() { return _flowSSERetryAttempt; },\n';
  code += '  getFirstFailMs: function() { return _flowSSEFirstFailMs; },\n';
  code += '  setFirstFailMs: function(v) { _flowSSEFirstFailMs = v; },\n';
  code += '  getRetryTimer: function() { return _flowSSERetryTimer; },\n';
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
console.log('_flowSSEBackoffMs ladder (sibling of #1610)');
{
  const { api } = buildSandbox();
  eq(api._flowSSEBackoffMs(0), 1000, 'attempt 0 -> 1s');
  eq(api._flowSSEBackoffMs(1), 2000, 'attempt 1 -> 2s');
  eq(api._flowSSEBackoffMs(2), 4000, 'attempt 2 -> 4s');
  eq(api._flowSSEBackoffMs(3), 8000, 'attempt 3 -> 8s');
  eq(api._flowSSEBackoffMs(4), 16000, 'attempt 4 -> 16s');
  eq(api._flowSSEBackoffMs(5), 30000, 'attempt 5 -> 30s (cap)');
  eq(api._flowSSEBackoffMs(99), 30000, 'attempt 99 -> 30s (still capped)');
  eq(api._flowSSEBackoffMs(-1), 1000, 'negative attempt -> 1s (clamp)');
}

// Case 2 — chain survives repeated failures
console.log('reconnect chain survives repeated failures (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now());
  api._scheduleFlowSSEReconnect();
  eq(sandbox._timers.length, 1, 'first failure schedules 1 retry timer');
  eq(sandbox._timers[0].ms, 1000, 'first retry uses 1s backoff');

  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 1, '_startFlowSse called once after 1st timer');
  api._scheduleFlowSSEReconnect();
  eq(sandbox._timers.length, 1, 'second failure schedules another retry');
  eq(sandbox._timers[0].ms, 2000, 'second retry uses 2s backoff');

  fireNextTimer(sandbox);
  api._scheduleFlowSSEReconnect();
  eq(sandbox._timers[0].ms, 4000, 'third retry uses 4s backoff');

  fireNextTimer(sandbox);
  eq(api.getStartCalls(), 3, '3 retry attempts fired in total -- no silent death');
}

// Case 3 — banner threshold + non-tech copy
console.log('connection-lost banner surfaces after 30s of failed retries (sibling of #1610)');
{
  const { api, sandbox, bannerEl } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);

  api._scheduleFlowSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown after 30s of failed retries');
  truthy(bannerEl.innerHTML.indexOf('Flow connection lost') !== -1,
    'banner contains stream-specific copy "Flow connection lost"');
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
  fresh.api._scheduleFlowSSEReconnect();
  eq(fresh.sandbox._bannerVisible, false,
    'fresh <30s failure does NOT surface banner (avoid noise on transient blips)');
}

// Case 4 — no parallel retry storm
console.log('no parallel retry storm on rapid onerror bursts (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now());
  for (let i = 0; i < 10; i++) api._scheduleFlowSSEReconnect();
  eq(sandbox._timers.length, 1,
    '10 rapid schedules -> 1 pending timer (single chain, no storm)');
}

// Case 5 — reset on connect
console.log('_resetFlowSSEReconnectState clears banner + chain on reconnect (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleFlowSSEReconnect();
  truthy(sandbox._bannerVisible, 'banner shown before reset');
  eq(sandbox._timers.length, 1, 'timer pending before reset');

  api._resetFlowSSEReconnectState();
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
  api._scheduleFlowSSEReconnect();
  eq(sandbox._timers.length, 0,
    'hidden tab -> no retry scheduled (deferred until visible)');
}

// Case 7 — _stopFlowSse teardown
console.log('_stopFlowSse tears down retry chain (sibling of #1610)');
{
  const { api, sandbox } = buildSandbox();
  api.setFirstFailMs(Date.now() - 31000);
  api._scheduleFlowSSEReconnect();
  truthy(sandbox._timers.length === 1, 'timer pending before stop');
  truthy(sandbox._bannerVisible, 'banner shown before stop');

  api._stopFlowSse();
  eq(sandbox._timers.length, 0, 'timer cleared after _stopFlowSse');
  eq(api.getRetryAttempt(), 0, 'retry attempt reset on stop');
  eq(api.getFirstFailMs(), 0, 'first-fail timestamp reset on stop');
  eq(sandbox._bannerEl.style.display, 'none', 'banner hidden on stop');
}

// Defense-in-depth: source-level scan for forbidden patterns.
// Verifies memory: feedback_no_reload_in_bootstrap_e2e -- no
// location.reload() can sneak into the SSE retry handler.
console.log('source scan: no location.reload() in Flow SSE retry path');
{
  ['_scheduleFlowSSEReconnect', '_resetFlowSSEReconnectState', '_stopFlowSse',
   '_showFlowConnectionLostBanner', '_hideFlowConnectionLostBanner', '_flowSSEBackoffMs']
    .forEach(function(name) {
      const body = extractFunction(name);
      truthy(body.indexOf('location.reload') === -1,
        name + ' does NOT call location.reload()');
    });
}

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' -- ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
