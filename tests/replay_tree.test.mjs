// JS-side smoke test for the replay-tree skeleton (#4813 part 3).
//
// Extracts the _cmReplayTree IIFE from app.js, runs it against a stubbed
// window + document, and asserts the public surface + core behavior:
//   1. window._cmReplayTree + window._debugReplayTree land on the window
//   2. renderTree returns false for an empty tree (fallback trigger)
//   3. renderTree returns true and populates innerHTML for a non-empty tree

import fs from 'fs';

const src = fs.readFileSync(
  new URL('../clawmetry/static/js/app.js', import.meta.url), 'utf8');

const start = src.indexOf('(function _cmReplayTree() {');
if (start < 0) throw new Error('_cmReplayTree IIFE not found in app.js');
const end = src.indexOf('})();', start) + 5;
const code = src.slice(start, end);

// Minimal DOM stub — the module only touches innerHTML / classList /
// createElement in renderTree; debugReplayTree is not exercised here.
class _StubEl {
  constructor(tag) {
    this.tagName = (tag || 'div').toUpperCase();
    this.children = [];
    this._innerHTML = '';
    this.style = { cssText: '' };
    this.classList = { add: () => {}, remove: () => {}, toggle: () => {} };
  }
  get innerHTML() { return this._innerHTML; }
  set innerHTML(v) { this._innerHTML = v; }
  appendChild(c) { this.children.push(c); return c; }
  remove() {}
}
const document = {
  createElement: (tag) => new _StubEl(tag),
  getElementById: () => null,
  body: new _StubEl('body'),
};
const window = {};
const fetch = () => Promise.reject(new Error('fetch not exercised'));

const fn = new Function(
  'window', 'document', 'fetch',
  code + '; return {api: window._cmReplayTree, debug: window._debugReplayTree};'
);
const {api, debug} = fn(window, document, fetch);

let pass = 0, fail = 0;
const check = (name, cond) => {
  if (cond) pass++;
  else { fail++; console.log('FAIL:', name); }
};

check('public API exposed', api && typeof api.renderTree === 'function' &&
                            typeof api.fetchReplayTree === 'function' &&
                            typeof api.registerKindRenderer === 'function');
check('debug hook exposed', typeof debug === 'function');

// Empty tree → false + cleared mount.
const emptyMount = new _StubEl('div');
const rEmpty = api.renderTree({row_count: 0, turns: [], workflows: []}, emptyMount);
check('empty tree returns false', rEmpty === false);
check('empty tree clears mount', emptyMount.innerHTML === '');

// Non-empty tree → true + populated mount, mode chip + turn rendered.
const tree = {
  session_id: 's1',
  runtime: 'claude_code',
  row_count: 3,
  mode: {permission: 'bypassPermissions', sandbox: 'danger-full-access'},
  workflows: [],
  turns: [{
    turn_id: 'u1',
    events: [
      {span_id: 'u1', kind: 'llm.call', payload: {prompt: 'hi'}, runtime: 'claude_code'},
      {span_id: 'a1', kind: 'llm.response', payload: {}, runtime: 'claude_code'},
    ],
    delegations: [],
    approvals: [],
  }],
};
const populatedMount = new _StubEl('div');
const rFull = api.renderTree(tree, populatedMount);
check('non-empty tree returns true', rFull === true);
check('tree wrapper rendered', populatedMount.innerHTML.includes('class="replay-tree"'));
check('yolo mode chip painted', populatedMount.innerHTML.includes('data-yolo="1"'));
check('turn rendered', populatedMount.innerHTML.includes('data-turn-id="u1"'));
check('llm.call event rendered', populatedMount.innerHTML.includes('llm.call'));

// Custom kind renderer wins over neutral fallback.
api.registerKindRenderer('claude_code', 'llm.call', () => '<div class="CUSTOM"></div>');
const customMount = new _StubEl('div');
api.renderTree(tree, customMount);
check('custom kind renderer wins', customMount.innerHTML.includes('CUSTOM'));

// Delegations render inline under their spawning turn.
const treeWithDelegation = {
  session_id: 's2',
  runtime: 'claude_code',
  row_count: 4,
  mode: null,
  workflows: [],
  turns: [{
    turn_id: 'u1',
    events: [
      {span_id: 'u1', kind: 'llm.call', runtime: 'claude_code'},
      {span_id: 'spawn1', kind: 'agent.spawn', runtime: 'claude_code'},
    ],
    delegations: [{
      span_id: 'spawn1',
      events: [{span_id: 'child-u1', kind: 'llm.call', runtime: 'claude_code'}],
      delegations: [],
    }],
    approvals: [],
  }],
};
const delegMount = new _StubEl('div');
api.renderTree(treeWithDelegation, delegMount);
check('delegation wrapper rendered',
      delegMount.innerHTML.includes('replay-tree-delegations'));
check('delegation summary references spawn id',
      delegMount.innerHTML.includes('delegated span spawn1'));

if (fail > 0) {
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(1);
}
console.log(`${pass} passed`);
