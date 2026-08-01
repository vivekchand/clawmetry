import fs from 'fs';
const src = fs.readFileSync(new URL('../clawmetry/static/js/app.js', import.meta.url), 'utf8');
// Extract just the sequence helpers (no DOM needed).
const start = src.indexOf('function _brainSeqDuration');
const marker = 'return out;';
const endBlock = src.indexOf(marker, start) + marker.length + '\n}'.length;
const code = src.slice(start, endBlock);
const escHtml = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const _CM_RT_PREFIXES = {claude_code:1, codex:1, s:1};
const _CM_RT_LABEL = {claude_code:'Claude Code', codex:'Codex', s:'S'};
const fn = new Function('escHtml', '_CM_RT_PREFIXES', '_CM_RT_LABEL', code + '; return {_brainGroupSequences, _brainSeqDuration};');
const {_brainGroupSequences, _brainSeqDuration} = fn(escHtml, _CM_RT_PREFIXES, _CM_RT_LABEL);

const T = (min) => new Date(Date.UTC(2026, 7, 1, 0, min, 0)).toISOString();
let pass = 0, fail = 0;
const check = (name, cond) => { cond ? pass++ : (fail++, console.log('FAIL:', name)); };

// Interleaved feed: two concurrent sessions, newest-first.
const rows = [
  {ev:{sessionId:'claude_code:aaa11111', time:T(10)}, html:'<a3>'},
  {ev:{sessionId:'codex:bbb22222',       time:T(9)},  html:'<b2>'},
  {ev:{sessionId:'claude_code:aaa11111', time:T(4)},  html:'<a2>'},
  {ev:{sessionId:'claude_code:aaa11111', time:T(0)},  html:'<a1>'},
  {ev:{sessionId:'codex:bbb22222',       time:T(0)},  html:'<b1>'},
];
const out = _brainGroupSequences(rows);

check('one block per session', (out.match(/class="brain-seq"/g)||[]).length === 2);
check('session order follows newest activity', out.indexOf('aaa11111') < out.indexOf('bbb22222'));
check('runtime label resolved', out.includes('Claude Code') && out.includes('Codex'));
check('per-session duration', out.includes('10m 0s') && out.includes('9m 0s'));
check('event counts', out.includes('3 events') && out.includes('2 events'));
check('every row rendered exactly once', ['<a1>','<a2>','<a3>','<b1>','<b2>']
  .every(r => (out.match(new RegExp(r, 'g'))||[]).length === 1));
check('newest-first preserved inside a block', out.indexOf('<a3>') < out.indexOf('<a2>'));
check('collapsible affordance present', out.includes('toggleBrainSequence'));

// Single session -> flat, byte-identical to pre-sequence rendering.
const solo = [
  {ev:{sessionId:'claude_code:aaa11111', time:T(1)}, html:'<x>'},
  {ev:{sessionId:'claude_code:aaa11111', time:T(0)}, html:'<y>'},
];
check('single-session feed renders flat', _brainGroupSequences(solo) === '<x><y>');
check('empty feed', _brainGroupSequences([]) === '');

// A USER row (runtimes that emit one) starts a new block within its session.
const turns = [
  {ev:{sessionId:'s:1', type:'TOOL', time:T(5)}, html:'<t2>'},
  {ev:{sessionId:'s:1', type:'USER', time:T(4)}, html:'<u2>'},
  {ev:{sessionId:'s:1', type:'TOOL', time:T(1)}, html:'<t1>'},
  {ev:{sessionId:'s:1', type:'USER', time:T(0)}, html:'<u1>'},
];
const tout = _brainGroupSequences(turns);
check('USER rows split turns within a session', (tout.match(/class="brain-seq"/g)||[]).length >= 2);

check('duration formatting', _brainSeqDuration(500)==='<1s' && _brainSeqDuration(45000)==='45s' && _brainSeqDuration(3900000)==='1h 5m');
check('bad duration safe', _brainSeqDuration(NaN)==='' && _brainSeqDuration(-5)==='');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
