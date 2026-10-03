// Regression: canonical replay data must never replace the conversation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(require('node:path').join(__dirname, '../clawmetry/static/js/app.js'), 'utf8');
const names = ['_loadReplayTree', '_resetTranscriptReplay', '_updateReplayStatePanel', 'replayFilter', '_buildReplayEvent', 'viewTranscript', 'loadEarlierMessages', 'showTranscriptList', 'replayTogglePlay'];
const code = names.map(name => {
  const match = src.match(new RegExp('^(?:async )?function ' + name + '\\([^]*?^}', 'm'));
  assert.ok(match, name); return match[0];
}).join('\n');
class Element {
  constructor() { this.style = {}; this.children = []; this.isConnected = true; this.innerHTML = ''; this.textContent = ''; }
  appendChild(el) { this.children.push(el); el.parentNode = this; }
  insertBefore(el, before) { this.children.splice(this.children.indexOf(before), 0, el); el.parentNode = this; }
  remove() { this.isConnected = false; this.parentNode.children = this.parentNode.children.filter(el => el !== this); }
}
const ids = {};
for (const id of ['transcript-viewer', 'transcript-messages', 'replay-controls', 'replay-state', 'replay-state-model', 'replay-state-thinking', 'replay-state-tokens', 'transcript-toc', 'replay-play-btn', 'replay-scrubber', 'transcript-list', 'transcript-back-btn', 'transcript-meta']) ids[id] = new Element();
const parent = new Element(); parent.appendChild(ids['transcript-messages']);
const window = {_transcriptViewRequest: 1, _replayEvents: []};
let timer;
const context = {window, Number, clearInterval: () => {timer=null;}, setInterval: callback => {timer=callback; return 1;}, escHtml: value => String(value || ''), t: (key, vars, fallback) => fallback, document: {
  createElement: () => new Element(),
  getElementById: id => id === 'replay-tree-container' ? parent.children.find(el => el.id === id) : ids[id],
  querySelectorAll: () => [],
}, _replayFilteredEvents: () => window._replayEvents, _replayRenderCurrent: () => {}, _isHistoryGapMsg: () => false};
vm.createContext(context); vm.runInContext(code, context);
let requests = 0, renders = 0, pending;
window._cmReplayTree = { fetchReplayTree: () => { requests++; return new Promise(resolve => {pending = resolve;}); }, renderTree: (tree, mount) => { renders++; mount.innerHTML = 'tree'; return !!tree.row_count; } };
(async () => {
  context._loadReplayTree('claude_code:real-session', 1);
  let mount = parent.children[0];
  assert.equal(requests, 0, 'opening a conversation does not fetch advanced replay');
  assert.notEqual(ids['transcript-messages'].style.display, 'none');
  mount.open = true;
  const load = mount.ontoggle(); mount.ontoggle();
  assert.equal(requests, 1, 'repeated toggles deduplicate pending request');
  pending({row_count: 110}); await load;
  assert.equal(renders, 1);
  assert.notEqual(ids['transcript-messages'].style.display, 'none', 'real canonical rows cannot hide conversation');
  assert.notEqual(ids['replay-controls'].style.display, 'none', 'replay controls survive tree render');
  await mount.ontoggle(); assert.equal(requests, 1, 'reopening uses loaded details');
  window._transcriptViewRequest++;
  context._resetTranscriptReplay();
  assert.equal(mount.isConnected, false);
  assert.equal(ids['replay-state'].style.display, 'none');
  context._loadReplayTree('codex:next-session', 2); mount = parent.children[0]; mount.open = true;
  const stale = mount.ontoggle();
  window._transcriptViewRequest++;
  context._resetTranscriptReplay();
  pending({row_count: 110}); await stale;
  assert.equal(renders, 1, 'late result for previous session is discarded');
  context._loadReplayTree('openclaw:empty', 3); mount = parent.children[0]; mount.open = true;
  const empty = mount.ontoggle(); pending({row_count: 0}); await empty;
  assert.match(mount.children[1].textContent, /No advanced replay events/);
  context._resetTranscriptReplay();
  window._cmReplayTree.fetchReplayTree = async () => {throw Error('unavailable');};
  context._loadReplayTree('offline', 3); mount = parent.children[0]; mount.open = true;
  await mount.ontoggle(); assert.match(mount.children[1].textContent, /reopen.*retry/);
  window._cmReplayTree.fetchReplayTree = async () => ({row_count: 110});
  await mount.ontoggle(); assert.equal(mount.children[1].innerHTML, 'tree');

  window._replaySessionModel = 'claude-fable-5-1';
  window._replayEvents = [{timestamp: 100, tokens: null}, {timestamp: 100, tokens: 540}, {timestamp: 200, tokens: 584, modelId:'second-model'}];
  context.replayFilter('all', true);
  assert.equal(window._replayIndex, 2, 'initial selection is last message');
  context._updateReplayStatePanel(200, 2);
  assert.equal(ids['replay-state-model'].textContent, 'second-model');
  assert.equal(ids['replay-state-tokens'].textContent, (1124).toLocaleString());
  context._updateReplayStatePanel(100, 0);
  assert.equal(ids['replay-state-tokens'].textContent, 'Not recorded', 'same timestamp must not count future blocks');
  assert.equal(ids['replay-state-model'].textContent, 'claude-fable-5-1');
  assert.match(ids['replay-state-model'].title, /Session model/);
  context.replayFilter('user'); assert.equal(window._replayIndex, 0, 'explicit filters still start at first match');
  window._replayEvents = [{tokens: 0}, {tokens: -4}, {tokens: NaN}, {tokens: Infinity}];
  context._updateReplayStatePanel(null, 3);
  assert.equal(ids['replay-state-tokens'].textContent, '0', 'measured zero differs from absent usage');
  window._replaySessionModel = null; window._replayEvents = [{tokens: null}];
  context._updateReplayStatePanel(null, 0);
  assert.equal(ids['replay-state-model'].textContent, 'Not recorded');
  assert.equal(ids['replay-state-thinking'].textContent, 'Not recorded');
  assert.equal(context._buildReplayEvent({role:'user',tokens:0},0).tokens,0);
  assert.equal(context._buildReplayEvent({role:'user',tokens:Infinity},0).tokens,null);
  // Real transcript-open logic: late A must not overwrite B, and backing
  // out during loading must leave the list visible with playback stopped.
  const waiting = new Map();
  window.CLOUD_MODE = true;
  window.cmProv = {of: () => null};
  context.fetch = async url => ({ok:true, json: () => url.startsWith('/api/transcript/')
    ? new Promise(resolve => waiting.set(decodeURIComponent(url.split('/').pop()), resolve)) : Promise.resolve({})});
  for (const name of ['_updateLoadEarlierBtn','_refreshHistoryGapRow','loadSimilarRuns','_loadInputsPanel','_loadLifecycleCoverageLine','_loadAuthorityPanel','_loadOrchestrationPanel','_loadSelfReportsPanel']) context[name] = () => {};
  const first = context.viewTranscript('claude_code:A');
  await new Promise(resolve => setImmediate(resolve));
  const second = context.viewTranscript('codex:B');
  await new Promise(resolve => setImmediate(resolve));
  waiting.get('codex:B')({name:'B',model:'model-B',messageCount:2,messages:[{role:'user',content:'prompt',timestamp:100},{role:'assistant',content:'answer',timestamp:100,tokens:7}]});
  await second;
  assert.equal(window._replayIndex, 1);
  assert.equal(window._replayEvents.length, 2);
  assert.equal(ids['replay-controls'].style.display, '');
  waiting.get('claude_code:A')({name:'A',model:'model-A',messageCount:0,messages:[]});
  await first;
  assert.equal(window._replaySessionModel, 'model-B', 'out-of-order response cannot replace active session');
  context.replayTogglePlay();
  assert.equal(window._replayIndex, 0, 'Play restarts from the beginning after opening at the end');
  assert.equal(window._replayPlaying, true);
  context.showTranscriptList();
  assert.equal(window._replayPlaying, false);
  assert.equal(window._replayEvents.length, 0);
  assert.equal(ids['replay-controls'].style.display, 'none');
  assert.equal(ids['transcript-viewer'].style.display, 'none');
  assert.equal(ids['transcript-list'].style.display, '');
  const pendingOpen = context.viewTranscript('claude_code:C');
  await new Promise(resolve => setImmediate(resolve));
  context.showTranscriptList();
  waiting.get('claude_code:C')({name:'C',model:'model-C',messages:[]});
  await pendingOpen;
  assert.equal(window._replaySessionModel, null);
  assert.equal(ids['transcript-viewer'].style.display, 'none');

  // A page of earlier messages can arrive after the next session opens.
  let page;
  context.fetch = async () => ({ok:true,json: () => new Promise(resolve => {page=resolve;})});
  window._transcriptPaging = {sid:'A',hasMore:true};
  const earlier = context.loadEarlierMessages();
  await new Promise(resolve => setImmediate(resolve));
  window._transcriptPaging = {sid:'B',hasMore:false};
  window._transcriptAllMessages = [{content:'B'}];
  page({messages:[{content:'A'}],has_more:false});
  await earlier;
  assert.equal(window._transcriptAllMessages[0].content, 'B');
  console.log('PASS: Sessions reader, opt-in tree, retry, navigation, summary and playback regression cases');
})().catch(error => {console.error(error); process.exitCode = 1;});
