// The gate on the first-run report panel (#5766).
//
// The panel says "No agent sessions on this machine yet" and then tells the
// reader nothing was detected and to try `clawmetry --sample`. Shown to
// somebody whose sessions ARE syncing, every one of those sentences is a
// lie, and it renders directly under a header counting their sessions.
//
// It shipped that way because the gate read a session count out of
// `/api/overview` by trying three key names and returning 0 when none of
// them was present. The cloud node page builds that payload client-side
// from the encrypted snapshot and carries `sessionCount` only — none of the
// three — so a machine with 1,281 synced sessions scored zero and was told
// it had no agents.
//
// Runs under `node tests/test_first_run_gate_js.js` — no jsdom, ~50ms.
// Pulls the real functions out of app.js so this tests shipped source.

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

function extractFunction(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

const keyVars = src.match(/^var _FRR_SESSION_KEYS[\s\S]*?^var _FRR_EVENT_KEYS[\s\S]*?;$/m);
if (!keyVars) throw new Error('could not find the _FRR_* key lists in app.js');

const sandbox = { isFinite: isFinite, Array: Array };
vm.createContext(sandbox);
vm.runInContext(
  keyVars[0] + '\n'
  + extractFunction('_frrCount') + '\n'
  + extractFunction('_frrLooksEmpty') + '\n'
  + 'this._empty = _frrLooksEmpty; this._count = _frrCount;'
  + 'this._SK = _FRR_SESSION_KEYS;', sandbox);
const empty = sandbox._empty;

console.log('_frrLooksEmpty — the panel only fires on a payload that says zero');

// The regression. This IS the shape the cloud node page hands the frontend.
eq(empty({ sessionCount: 1281, mainTokens: 900000, spending: { today: 4 } }), false,
   'a cloud payload carrying only sessionCount is NOT empty (#5766)');
eq(sandbox._count({ sessionCount: 1281 }, sandbox._SK), 1281,
   'sessionCount is read as a session count');

// OSS shapes, which carry `sessions` as well.
eq(empty({ sessions: 12, sessionCount: 12, sessionsToday: 3 }), false,
   'an OSS payload with sessions is not empty');
eq(empty({ sessions: [{ id: 'a' }] }), false,
   'a non-empty sessions ARRAY is not empty');

// A busy machine that has simply not run anything since midnight. Taking the
// first key found rather than the max would call this one empty.
eq(empty({ sessionsToday: 0, sessionCount: 1281 }), false,
   'sessionsToday=0 does not override a non-zero all-time count');

// Unknown is not zero. A reshaped, truncated or timed-out payload must stay
// silent rather than accuse a working install of having no runtimes.
eq(empty({}), false, 'an empty object is unknown, not empty');
eq(empty(null), false, 'a null payload is unknown, not empty');
eq(empty(undefined), false, 'an undefined payload is unknown, not empty');
eq(empty({ model: 'claude-opus-5' }), false,
   'a payload with no count field at all is unknown, not empty');

// And the panel must still do its job on a genuinely fresh machine.
eq(empty({ sessions: [], sessionCount: 0, events: 0 }), true,
   'a genuinely empty payload still shows the panel');
eq(empty({ sessions: 0, sessionCount: 0, sessionsToday: 0, events: 0 }), true,
   'all-zero counts still show the panel');
eq(empty({ sessionCount: 0 }), true,
   'a cloud payload reporting zero sessions still shows the panel');

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' — ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
