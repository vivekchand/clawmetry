// Unit tests for pure functions in clawmetry/static/js/app.js.
//
// Covers issue #1127 fixes #2 (formatBrainTime year handling) and #5 (stuck
// banner localStorage dismissal). Runs under `node tests/test_appjs_units.js`
// — no JSDOM, no Playwright, ~50ms. Pulls the target functions out of
// app.js via regex and evaluates them in a sandbox with a stub
// `localStorage`, so we test the actual shipped source rather than a copy.

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
  // Match `function NAME(...) { ... }` with a balanced top-level brace.
  // app.js uses 2-space indent and never nests another top-level
  // `function NAME` so the first `^}` after the opening line is the close.
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

// ── Test bug #2 — formatBrainTime year handling ────────────────────────
console.log('formatBrainTime (issue #1127 — year missing for cross-year dates)');
{
  const fnSrc = extractFunction('formatBrainTime');
  const sandbox = { Date: Date };
  vm.createContext(sandbox);
  vm.runInContext(fnSrc + '\nthis._formatBrainTime = formatBrainTime;', sandbox);
  const fmt = sandbox._formatBrainTime;

  // Pin "now" to a deterministic moment by stubbing Date's no-arg constructor.
  // We do it via a small wrapper so the function under test always sees the
  // same "now". new Date(isoStr) must still work for real ISO strings.
  function withNow(nowIso, fn) {
    const RealDate = Date;
    sandbox.Date = function(arg) {
      if (arguments.length === 0) return new RealDate(nowIso);
      return new RealDate(arg);
    };
    sandbox.Date.prototype = RealDate.prototype;
    try { return fn(); } finally { sandbox.Date = RealDate; }
  }

  // Same day → "Today"
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2026-05-13T10:07:28.619Z');
    truthy(out.indexOf('Today') !== -1, 'same day → contains "Today"');
    truthy(out.indexOf('2026') === -1, 'same day → no year');
  });

  // Same year, different day → no year (e.g. "9 May")
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2026-05-09T10:07:28.619Z');
    truthy(out.indexOf('May') !== -1, 'same year → contains "May"');
    truthy(out.indexOf('2026') === -1, 'same year → year omitted (compact)');
    truthy(out.indexOf('Today') === -1, 'same year → not "Today"');
  });

  // Different year → MUST include year (the bug)
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2025-05-09T10:07:28.619Z');
    truthy(out.indexOf('May') !== -1, 'cross-year → contains "May"');
    truthy(out.indexOf('2025') !== -1, 'cross-year → year included (bug #1127.2)');
  });

  // Bad input → does not throw (graceful fallback, exact shape not asserted
  // because formatBrainTime's pre-existing behaviour is to let Date(NaN)
  // through; we only require it doesn't crash).
  withNow('2026-05-13T15:00:00Z', function() {
    let threw = false;
    try { fmt(null); } catch(e) { threw = true; }
    eq(threw, false, 'null → no throw');
    try { fmt(''); } catch(e) { threw = true; }
    eq(threw, false, 'empty string → no throw');
  });
}

// ── Test bug #5 — stuck-session dismissal persistence ──────────────────
console.log('stuck-session banner dismissal (issue #1127 — resurfaces after reload)');
{
  // Build a minimal sandbox with a stub localStorage.
  const store = {};
  const sandbox = {
    Date: Date,
    localStorage: {
      getItem: function(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
      setItem: function(k, v) { store[k] = String(v); },
      removeItem: function(k) { delete store[k]; },
    },
    document: {
      getElementById: function() { return null; },
    },
    _stuckCount: 0,
    _stuckSessions: {},
    _updateStuckBadge: function() {},
    _clearStuckBanner: function() {},
  };

  // Pull in the helpers and the show/dismiss handlers.
  const wanted = [
    '_readStuckDismissals',
    '_writeStuckDismissals',
    '_pruneStuckDismissals',
    '_isStuckDismissed',
    '_markStuckDismissed',
  ];
  const constants = [];
  src.split('\n').forEach(function(line) {
    if (line.indexOf('var _STUCK_DISMISS_KEY') === 0) constants.push(line);
    if (line.indexOf('var _STUCK_DISMISS_TTL_MS') === 0) constants.push(line);
  });
  let code = constants.join('\n') + '\n';
  wanted.forEach(function(name) { code += extractFunction(name) + '\n'; });
  code += '\nthis.api = {\n';
  wanted.forEach(function(name) { code += '  ' + name + ': ' + name + ',\n'; });
  code += '};';

  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // No dismissal yet.
  eq(api._isStuckDismissed('s-1'), false, 'fresh state → not dismissed');

  // Mark dismissed, verify persists.
  api._markStuckDismissed('s-1');
  eq(api._isStuckDismissed('s-1'), true, 'after _markStuckDismissed → dismissed');
  eq(api._isStuckDismissed('s-2'), false, 'different session → independent');

  // Round-trip via store → simulates page reload.
  truthy(store['stuck-session-dismissed'], 'persisted into localStorage');
  // Empty cache, re-read.
  const reload = JSON.parse(store['stuck-session-dismissed']);
  truthy(reload['s-1'] > 0, 'localStorage holds timestamp for s-1');

  // Empty / blank session id → never dismissed.
  eq(api._isStuckDismissed(''), false, 'empty sessionId → not dismissed');
  api._markStuckDismissed(''); // no-op
  eq(Object.keys(JSON.parse(store['stuck-session-dismissed'])).length, 1,
     'empty sessionId is a no-op');

  // TTL prune: backdate s-1 to 25h ago, prune drops it.
  const stale = JSON.parse(store['stuck-session-dismissed']);
  stale['s-1'] = Date.now() - 25 * 60 * 60 * 1000;
  store['stuck-session-dismissed'] = JSON.stringify(stale);
  eq(api._isStuckDismissed('s-1'), false, '> 24h old → no longer dismissed');
  const after = JSON.parse(store['stuck-session-dismissed'] || '{}');
  truthy(!('s-1' in after), '> 24h entry pruned from store');
}

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' — ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
