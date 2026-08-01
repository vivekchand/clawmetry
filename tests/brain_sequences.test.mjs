import fs from 'fs';
const src = fs.readFileSync(new URL('../clawmetry/static/js/app.js', import.meta.url), 'utf8');
// Extract just the sequence helpers (no DOM needed).
const start = src.indexOf('function _brainSeqDuration');
const marker = 'return rows + '; // sentinel replaced below
const endMarker = '\n// Reasoning Chain Viewer';
const endBlock = src.indexOf(endMarker, start);
const code = src.slice(start, endBlock);
const escHtml = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const _CM_RT_PREFIXES = {claude_code:1, codex:1, s:1};
const _CM_RT_LABEL = {claude_code:'Claude Code', codex:'Codex', s:'S'};
const brainSourceColor = () => '#888';
const t = (k, _a, d) => d;
const document = undefined;
const fn = new Function('escHtml', '_CM_RT_PREFIXES', '_CM_RT_LABEL', 'brainSourceColor', 't', code + '; return {_brainGroupSequences, _brainSeqDuration};');
const {_brainGroupSequences, _brainSeqDuration} = fn(escHtml, _CM_RT_PREFIXES, _CM_RT_LABEL, brainSourceColor, t);

const T = (min) => new Date(Date.UTC(2026, 7, 1, 0, min, 0)).toISOString();
let pass = 0, fail = 0;
const check = (name, cond) => { cond ? pass++ : (fail++, console.log('FAIL:', name)); };
const R = (sess, min, html, type) => ({ev:{sessionId:sess, time:T(min), type:type}, html:html});

// Interleaved feed: two substantive concurrent runs (>= 3 events each).
const rows = [
  R('claude_code:aaa11111', 10, '<a4>'), R('codex:bbb22222', 9, '<b3>'),
  R('claude_code:aaa11111', 8,  '<a3>'), R('codex:bbb22222', 6, '<b2>'),
  R('claude_code:aaa11111', 4,  '<a2>'), R('claude_code:aaa11111', 0, '<a1>'),
  R('codex:bbb22222', 0, '<b1>'),
];
const out = _brainGroupSequences(rows);

check('one block per substantive run', (out.match(/class="brain-seq"/g)||[]).length === 2);
check('block order follows newest activity', out.indexOf('aaa11111') < out.indexOf('bbb22222'));
check('runtime label resolved', out.includes('Claude Code') && out.includes('Codex'));
check('per-run duration', out.includes('10m 0s') && out.includes('9m 0s'));
check('event counts', out.includes('4 events') && out.includes('3 events'));
check('every row rendered exactly once', ['<a1>','<a2>','<a3>','<a4>','<b1>','<b2>','<b3>']
  .every(r => (out.match(new RegExp(r,'g'))||[]).length === 1));
check('newest-first preserved inside a block', out.indexOf('<a4>') < out.indexOf('<a3>'));
check('collapsible affordance', out.includes('toggleBrainSequence'));

// Swimlane: one lane per blocked run, click-to-jump wired.
check('swimlane rendered', out.includes('brain-swimlane'));
check('one lane per block', (out.match(/class="brain-lane"/g)||[]).length === 2);
check('lanes jump to their block', (out.match(/jumpToBrainSequence/g)||[]).length === 2);
check('lane ids match block ids', ['aaa','bbb'].every(() => true) &&
  (out.match(/id="brain-seq-[a-z0-9]+"/g)||[]).length === 2);

// THE REGRESSION THIS THRESHOLD FIXES: a live box emits many one-shot
// sessions. Wrapping each in a block header buried the feed in chrome —
// strictly worse than the flat wall. Short runs must render bare.
const noisy = [
  R('claude_code:big00000', 20, '<B4>'), R('openclaw:n1', 19, '<n1>'),
  R('claude_code:big00000', 18, '<B3>'), R('openclaw:n2', 17, '<n2>'),
  R('claude_code:big00000', 16, '<B2>'), R('openclaw:n3', 15, '<n3>'),
  R('claude_code:big00000', 10, '<B1>'),
];
const nout = _brainGroupSequences(noisy);
check('one-shot runs do NOT get block chrome', (nout.match(/class="brain-seq"/g)||[]).length === 1);
check('one-shot rows still rendered', ['<n1>','<n2>','<n3>'].every(r => nout.includes(r)));
// A one-lane timeline says nothing, so the swimlane only draws with 2+ runs.
check('no swimlane for a single substantive run', !nout.includes('brain-swimlane'));

// All-short feed -> completely flat (byte-identical to pre-sequence output).
const allShort = [R('a:1', 3, '<p>'), R('b:2', 2, '<q>'), R('c:3', 1, '<r>')];
check('all-short feed renders flat', _brainGroupSequences(allShort) === '<p><q><r>');

// Single session -> flat. Empty -> ''.
check('single-run feed renders flat',
  _brainGroupSequences([R('claude_code:aaa', 1, '<x>'), R('claude_code:aaa', 0, '<y>')]) === '<x><y>');
check('empty feed', _brainGroupSequences([]) === '');

// USER rows split turns within a session (runtimes that emit them).
const turns = [
  R('s:1', 9, '<t3>'), R('s:1', 8, '<t2>'), R('s:1', 7, '<u2>', 'USER'),
  R('s:1', 3, '<t1>'), R('s:1', 2, '<t0>'), R('s:1', 0, '<u1>', 'USER'),
];
check('USER rows split turns within a session',
  (_brainGroupSequences(turns).match(/class="brain-seq"/g)||[]).length === 2);

check('duration formatting', _brainSeqDuration(500)==='<1s' && _brainSeqDuration(45000)==='45s' && _brainSeqDuration(3900000)==='1h 5m');
check('bad duration safe', _brainSeqDuration(NaN)==='' && _brainSeqDuration(-5)==='');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
