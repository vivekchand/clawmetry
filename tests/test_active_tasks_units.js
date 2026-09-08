// Behavioural unit tests for the Overview "Active Tasks" classifiers in
// clawmetry/static/js/app.js. Replays the exact records from the founder's
// 2026-09-07 report against the SHIPPED source (regex-extracted, vm-evaluated).
//
// Run: node tests/test_active_tasks_units.js
//
// The static guards in test_active_tasks_honesty.py pin the shape of the fix;
// these pin its behaviour, so a refactor that keeps the names but reintroduces
// the lie still fails.

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

function extractFunction(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

function sandboxWith(names, extra) {
  const sandbox = Object.assign({ Date: Date, String: String, Number: Number,
                                  Math: Math, JSON: JSON }, extra || {});
  vm.createContext(sandbox);
  let code = names.map(extractFunction).join('\n');
  code += '\n' + names.map(n => 'this.' + n + ' = ' + n + ';').join('\n');
  vm.runInContext(code, sandbox);
  return sandbox;
}

// ── _ovBucketOf: a FAILED task never renders as complete ───────────────────
console.log('_ovBucketOf (founder report: FAILED sub-agent drawn with a green tick)');
{
  const s = sandboxWith(['_ovBucketOf', '_cmIsWorkingStatus', '_cmIsFailedStatus']);
  const bucket = s._ovBucketOf;

  // The exact record shape behind the screenshot: the modal read FAILED, the
  // card read ✅, because nothing handled status === 'failed'.
  eq(bucket({ status: 'failed' }), 'failed',
     "status 'failed' -> failed bucket (was: complete, with a ✅)");
  eq(bucket({ status: 'error' }), 'failed', "status 'error' -> failed");
  eq(bucket({ status: 'aborted' }), 'failed', "status 'aborted' -> failed");

  eq(bucket({ status: 'active' }), 'running', "status 'active' -> running");
  eq(bucket({ status: 'running' }), 'running', "daemon's 'running' -> running");
  eq(bucket({ status: 'stale' }), 'complete', "plain 'stale' -> complete");
  eq(bucket({ status: 'idle' }), 'complete', "'idle' is not a failure");

  // The legacy heuristic must still work.
  eq(bucket({ status: 'stale', abortedLastRun: true, outputTokens: 0 }), 'failed',
     'stale + aborted + zero output -> failed (legacy heuristic preserved)');
  eq(bucket({ status: 'stale', abortedLastRun: true, outputTokens: 500 }), 'complete',
     'stale + aborted but it produced output -> complete');

  eq(bucket(null), 'complete', 'null record does not throw');
  eq(bucket({}), 'complete', 'empty record does not throw');
}

// ── _ovEndedMs: never invent an end time ───────────────────────────────────
console.log('_ovEndedMs (founder report: Aug-20 task labelled "Finished 1 min ago")');
{
  const s = sandboxWith(['_ovEndedMs']);
  const ended = s._ovEndedMs;
  const NOW = Date.now();

  // THE BUG. A spawn from 2026-08-20 that never ran: runtime 0s, no
  // completion. routes/sessions.py could not parse its timestamp so it stamped
  // updatedAt = now. The old code returned that and the card said
  // "Finished 1 min ago" eighteen days later.
  eq(ended({ updatedAt: NOW, startedAt: NOW, runtimeMs: 0,
             completionTs: '', completionStatus: '', outputTokens: 0 }), 0,
     'never-ran spawn with a now-stamped updatedAt -> 0 (unknown), not now');

  // A real completion is still trusted, by every available route.
  eq(ended({ completionTs: '2026-09-07T10:00:00Z' }), Date.parse('2026-09-07T10:00:00Z'),
     'completionTs wins when present');
  eq(ended({ startedAt: 1000, runtimeMs: 500 }), 1500,
     'startedAt + runtimeMs when the spawn actually ran');
  eq(ended({ updatedAt: 4242, runtimeMs: 0, outputTokens: 12 }), 4242,
     'updatedAt trusted once output proves the spawn ran');
  eq(ended({ updatedAt: 99, runtimeMs: 0, completionStatus: 'ok' }), 99,
     'updatedAt trusted once a completionStatus proves it finished');

  eq(ended({ completionTs: 'not-a-date', runtimeMs: 0 }), 0,
     'unparseable completionTs does not fall back to a fabricated time');
  eq(ended(null), 0, 'null record does not throw');
}

// ── _cmRuntimeOf: the `runtime` field is a DURATION on sub-agent records ───
console.log('_cmRuntimeOf (founder report: Codex sub-agent stamped OpenClaw)');
{
  const prefixSrc = src.match(/var _CM_RT_PREFIXES = \{[\s\S]*?\n\};/)[0];
  const s = sandboxWith(['_cmRuntimeOf'], {});
  // _cmRuntimeOf closes over the prefix tables; evaluate them in the same ctx.
  vm.runInContext(prefixSrc + '\nvar _CM_OTLP_RT = {};', s);
  const rtOf = s._cmRuntimeOf;

  // THE BUG. /api/subagents emits "runtime" as a formatted DURATION.
  // Short-circuiting on it meant every sub-agent resolved to the openclaw
  // default — so a Codex task was filed under OpenClaw.
  eq(rtOf({ runtime: '12m', runtimeName: 'codex' }), 'codex',
     "runtimeName wins over the duration string in `runtime`");
  eq(rtOf({ runtime: '2h 5m', agentType: 'claude_code' }), 'claude_code',
     'agentType wins over the duration string');
  eq(rtOf({ runtime: '44s', sessionId: 'codex:abc-123' }), 'codex',
     'session-id prefix still resolves');

  // A genuine runtime name in `runtime` (OTLP/server-tagged rows) still works.
  eq(rtOf({ runtime: 'cursor' }), 'cursor', 'a real runtime name in `runtime` still resolves');

  // Unattributable records fall back to the documented default.
  eq(rtOf({ runtime: '12m' }), 'openclaw', 'a bare duration falls back to the default');
}

// ── _ovVisible: a count must never promise more than the list will show ────
console.log('_ovVisible (founder-verified: "489 tasks on other runtimes" led to an EMPTY view)');
{
  const s = sandboxWith(['_ovVisible','_ovRecentlyFinished','_ovBucketOf','_ovEndedMs',
                         '_cmIsWorkingStatus','_cmIsFailedStatus']);
  vm.runInContext('var OV_RECENT_DONE_MS = 60*60*1000;', s);
  const vis = s._ovVisible;
  const NOW = 1_700_000_000_000;
  const ago = ms => NOW - ms;

  const running   = {status:'active'};
  const doneNow   = {status:'stale', completionTs:new Date(ago(5*60*1000)).toISOString()};
  const doneOld   = {status:'stale', completionTs:new Date(ago(6*24*3600*1000)).toISOString()};
  const failedNow = {status:'failed', completionTs:new Date(ago(2*60*1000)).toISOString()};
  const failedOld = {status:'failed', completionTs:new Date(ago(9*24*3600*1000)).toISOString()};
  const neverRan  = {status:'failed', updatedAt:NOW, runtimeMs:0};

  eq(vis([running], NOW).total, 1, 'a running task is always visible');
  eq(vis([doneNow], NOW).total, 1, 'a task finished 5 min ago is visible');
  eq(vis([doneOld], NOW).total, 0, 'a task finished 6 days ago is NOT visible');
  eq(vis([failedNow], NOW).total, 1, 'a failure 2 min ago is visible');
  eq(vis([failedOld], NOW).total, 0, 'a failure 9 days ago is NOT visible');
  eq(vis([neverRan], NOW).total, 0, 'a never-ran spawn is not visible on a now-stamped updatedAt');

  // THE BUG: counting raw rows said 489; only the visible ones may be promised.
  const many = [doneOld, doneOld, doneOld, failedOld, neverRan];
  eq(vis(many, NOW).total, 0,
     'a pile of old tasks counts as ZERO — the empty state must not send someone to an empty view');
  eq(vis(many.concat([running, doneNow]), NOW).total, 2,
     'only the genuinely visible tasks are counted');

  const mixed = vis([running, doneNow, failedNow, doneOld], NOW);
  eq(mixed.running.length, 1, 'running bucket');
  eq(mixed.done.length, 1, 'done bucket');
  eq(mixed.failed.length, 1, 'failed bucket');

  eq(vis(null, NOW).total, 0, 'null list does not throw');
  eq(vis([], NOW).total, 0, 'empty list is zero');
}

console.log('');
console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
