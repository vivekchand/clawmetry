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

check('complete tree has no cut notice', !populatedMount.innerHTML.includes('replay-tree-truncated'));

// A cut tree says how many events it lists.
const cutMount = new _StubEl('div');
api.renderTree(Object.assign({}, tree, {truncated: true, row_count: 8000, event_limit: 8000}), cutMount);
check('cut tree shows the notice', cutMount.innerHTML.includes('class="replay-tree-truncated"'));
check('cut notice names the event count', cutMount.innerHTML.includes('The first 8000 events'));

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

// Nested delegations render inside their parent, with label and approvals.
const treeNested = {
  session_id: 's3', runtime: 'claude_code', row_count: 6, mode: null,
  workflows: [],
  turns: [{
    turn_id: 'u1',
    events: [{span_id: 'spawn1', kind: 'agent.spawn', runtime: 'claude_code'}],
    delegations: [{
      span_id: 'spawn1', label: 'Explore <repo>',
      events: [{span_id: 'spawn2', kind: 'agent.spawn', runtime: 'claude_code'}],
      approvals: [{span_id: 'ap1', kind: 'approval.decided'}],
      delegations: [{
        span_id: 'spawn2', label: '', approvals: [],
        events: [{span_id: 'grand-u1', kind: 'llm.call', runtime: 'claude_code'}],
        delegations: [],
      }],
    }],
    approvals: [],
  }],
};
const nestedMount = new _StubEl('div');
api.renderTree(treeNested, nestedMount);
const nestedHtml = nestedMount.innerHTML;
check('nested delegation rendered at depth 2', nestedHtml.includes('data-depth="2"'));
check('nested delegation sits inside its parent',
      nestedHtml.indexOf('delegated span spawn2') > nestedHtml.indexOf('delegated span spawn1') &&
      nestedHtml.indexOf('delegated span spawn2') < nestedHtml.lastIndexOf('</details>'));
check('delegation label escaped', nestedHtml.includes('Explore &lt;repo&gt;'));
check('delegation approvals badge', nestedHtml.includes('replay-tree-badge approvals">✓1'));

// A workflow whose start event carries nodes is drawn as a graph.
const wfStart = {
  span_id: 'wf1', kind: 'workflow.start', runtime: 'n8n',
  payload: {
    workflow: 'Digest <daily>', status: 'error',
    nodes: [
      {name: 'Trigger', type: 'manualTrigger', position: [0, 0]},
      {name: 'Agent', type: 'agent', position: [200, 0]},
      {name: 'Model', type: 'lmChatAnthropic', position: [200, 200]},
      {name: 'Never <run>', type: 'code', position: [400, 0]},
    ],
    edges: [
      {from: 'Trigger', to: 'Agent', type: 'main', output: 0},
      {from: 'Model', to: 'Agent', type: 'ai_languageModel', output: 0},
      {from: 'Agent', to: 'Never <run>', type: 'main', output: 0},
      {from: 'Agent', to: 'Gone', type: 'main', output: 0},
    ],
  },
};
const stage = (node, status, extra) => ({
  span_id: 'st-' + node, parent_span_id: 'wf1', kind: 'workflow.stage',
  runtime: 'n8n', payload: Object.assign({node, status}, extra || {}),
});
const wfTree = {
  session_id: 'n8n-1', runtime: 'n8n', row_count: 5, mode: null, turns: [],
  workflows: [{span_id: 'wf1', kind: 'workflow', events: [
    wfStart, stage('Trigger', 'success', {duration_ms: 1}),
    stage('Agent', 'error', {is_error: true, error: 'boom'}),
    stage('Model', 'success'), stage('Model', 'error', {is_error: true}),
  ]}],
};
const wfMount = new _StubEl('div');
api.renderTree(wfTree, wfMount);
const wfHtml = wfMount.innerHTML;
check('workflow graph rendered', wfHtml.includes('<svg class="replay-wf-graph"'));
check('one box per node', (wfHtml.match(/class="replay-wf-node"/g) || []).length === 4);
check('edge to an unknown node is dropped',
      (wfHtml.match(/class="replay-wf-edge/g) || []).length === 3);
check('sub-node edge is marked', wfHtml.includes('replay-wf-edge replay-wf-edge-sub'));
check('node that ran well is marked success',
      wfHtml.includes('data-node="Trigger" data-status="success"'));
check('failed node is marked error', wfHtml.includes('data-node="Agent" data-status="error"'));
check('latest run of a node wins', wfHtml.includes('data-node="Model" data-status="error"'));
check('node with no run is marked none',
      wfHtml.includes('data-node="Never &lt;run&gt;" data-status="none"'));
check('node name escaped', !wfHtml.includes('Never <run>'));
check('workflow name in the summary, escaped', wfHtml.includes('workflow Digest &lt;daily&gt;'));
check('run count caption', wfHtml.includes('3 of 4 nodes ran'));
check('event rows stay available', wfHtml.includes('class="replay-wf-events"') &&
      wfHtml.includes('workflow.stage'));

// No canvas positions: nodes are placed in columns and still all drawn.
const noPos = JSON.parse(JSON.stringify(wfTree));
noPos.workflows[0].events[0].payload.nodes.forEach(n => { delete n.position; });
const noPosMount = new _StubEl('div');
api.renderTree(noPos, noPosMount);
check('graph without positions still draws every node',
      (noPosMount.innerHTML.match(/class="replay-wf-node"/g) || []).length === 4);
check('graph without positions has no NaN', !noPosMount.innerHTML.includes('NaN'));

// A start with no nodes (a Goose recipe) keeps the plain list.
const recipeMount = new _StubEl('div');
api.renderTree({
  session_id: 'g1', runtime: 'goose', row_count: 1, mode: null, turns: [],
  workflows: [{span_id: 'r1', kind: 'workflow', events: [
    {span_id: 'r1', kind: 'workflow.start', runtime: 'goose',
     payload: {workflow: 'recipe', title: 'Release notes', steps: []}}]}],
}, recipeMount);
check('workflow without nodes has no graph', !recipeMount.innerHTML.includes('replay-wf-graph'));
check('workflow without nodes still lists its events',
      recipeMount.innerHTML.includes('workflow.start'));
check('recipe title in the summary', recipeMount.innerHTML.includes('workflow Release notes'));

// Data n8n keeps outside the database: the graph, and a note instead of counts.
const offMount = new _StubEl('div');
const off = JSON.parse(JSON.stringify(wfTree));
off.workflows[0].events = [off.workflows[0].events[0]];
off.workflows[0].events[0].payload.run_data = 'offloaded:fs';
api.renderTree(off, offMount);
check('offloaded run says the node runs are not stored',
      offMount.innerHTML.includes('not stored in the database'));

// Model and tool calls of sub-nodes are listed on the node they served,
// matched to the workflow by the stage they name (clawmetry-pro#132).
const actTree = JSON.parse(JSON.stringify(wfTree));
actTree.workflows[0].events[0].payload.nodes.push(
  {name: 'Calc', type: 'toolCalculator', position: [300, 200]});
actTree.workflows[0].events.push(
  {span_id: 'st-calc', parent_span_id: 'wf1', kind: 'workflow.stage', runtime: 'n8n',
   payload: {node: 'Calc', status: 'success', role: 'tool'}},
  {span_id: 'st-model2', parent_span_id: 'wf1', kind: 'workflow.stage', runtime: 'n8n',
   payload: {node: 'Model', status: 'success', role: 'model'}});
actTree.turns = [{turn_id: 'c1', approvals: [], delegations: [{
  span_id: 'sp1', label: 'workflow', approvals: [], delegations: [], events: [
    {span_id: 'x-call', kind: 'tool.call', runtime: 'n8n',
     payload: {tool: 'other', node: 'Agent', agent_node: 'Agent', stage_span_id: 'st-child'}}],
}], events: [
  {span_id: 'c1', kind: 'llm.call', runtime: 'n8n',
   payload: {node: 'Model', agent_node: 'Agent', model: 'claude-<x>', stage_span_id: 'st-model2'}},
  {span_id: 'r1', kind: 'llm.response', runtime: 'n8n',
   payload: {node: 'Model', stage_span_id: 'st-model2',
             usage: {input_tokens: 120, output_tokens: 30}}},
  {span_id: 't1', kind: 'tool.call', runtime: 'n8n',
   payload: {tool: 'toolCalculator', node: 'Calc', agent_node: 'Agent',
             args: {expr: '<2+2>'}, call_id: 't1', stage_span_id: 'st-calc'}},
  {span_id: 't1r', kind: 'tool.result', runtime: 'n8n',
   payload: {tool: 'toolCalculator', call_id: 't1', node: 'Calc',
             output: 'division by <zero>', is_error: true}},
  {span_id: 'plain', kind: 'tool.call', runtime: 'n8n', payload: {tool: 'x', node: 'Agent'}},
]}];
const actMount = new _StubEl('div');
api.renderTree(actTree, actMount);
const actHtml = actMount.innerHTML;
const agentDetail = actHtml.slice(
  actHtml.indexOf('class="replay-wf-node-detail" data-node="Agent"'));
check('agent node lists its calls',
      (agentDetail.match(/class="replay-wf-call"/g) || []).length === 2);
check('call counts in the node summary',
      agentDetail.includes('Model calls: 1 · Tool calls: 1'));
check('model call names the model and its tokens',
      agentDetail.includes('claude-&lt;x&gt;') && agentDetail.includes('120 tokens in, 30 out'));
check('tool call shows its arguments, escaped',
      agentDetail.includes('{&quot;expr&quot;:&quot;&lt;2+2&gt;&quot;}'));
check('failed tool call is marked with its output',
      agentDetail.includes('data-kind="tool" data-error="1"') &&
      agentDetail.includes('division by &lt;zero&gt;'));
check('call of another workflow with the same node name is not listed',
      !agentDetail.includes('>other<'));
check('failed node detail is open and shows the error',
      actHtml.includes('data-node="Agent" data-status="error" open') &&
      agentDetail.includes('class="replay-wf-node-error">boom'));
check('count marker on the agent node only',
      (actHtml.match(/class="replay-wf-node-count"/g) || []).length === 1 &&
      actHtml.includes('class="replay-wf-node-count-text"') );
check('sub-node has no detail of its own',
      !actHtml.includes('class="replay-wf-node-detail" data-node="Calc"'));
check('no raw markup from call text', !actHtml.includes('<zero>') && !actHtml.includes('<2+2>'));
// Without calls, only the failed node gets a detail entry.
check('graph without calls lists the failed node only',
      (wfHtml.match(/class="replay-wf-node-detail"/g) || []).length === 1 &&
      !wfHtml.includes('replay-wf-node-count'));
check('workflow with no failure and no call has no details block',
      !offMount.innerHTML.includes('replay-wf-node-details'));

// In-flight counts on a turn's opening llm.call become header badges, and a
// fork spawn tags its delegation (clawmetry-pro#123, #4815).
const inFlightTree = {
  session_id: 's5', runtime: 'claude_code', row_count: 9, mode: null, workflows: [],
  turns: [{
    turn_id: 'u1',
    events: [
      {span_id: 'u1', kind: 'llm.call', runtime: 'claude_code',
       payload: {in_flight_at_start: {background_agents: 3, workflows: 1}}},
      {span_id: 'forkspawn', kind: 'agent.spawn', runtime: 'claude_code',
       payload: {context_inheritance: 'fork'}},
      {span_id: 'freshspawn', kind: 'agent.spawn', runtime: 'claude_code',
       payload: {context_inheritance: 'fresh'}},
    ],
    delegations: [
      {span_id: 'forkspawn', label: 'fork', approvals: [], delegations: [],
       events: [{span_id: 'fc1', kind: 'llm.call', runtime: 'claude_code'}]},
      {span_id: 'freshspawn', label: 'Explore', approvals: [],
       events: [{span_id: 'nestedfork', kind: 'agent.spawn', runtime: 'claude_code',
                 payload: {context_inheritance: 'fork'}}],
       delegations: [{span_id: 'nestedfork', label: '', approvals: [], events: [],
                      delegations: []}]},
    ],
    approvals: [],
  }, {
    turn_id: 'u2',
    events: [
      {span_id: 'u2', kind: 'llm.call', runtime: 'claude_code',
       payload: {in_flight_at_start: {background_agents: 0, workflows: '<b>2</b>'}}},
      {span_id: 'u2b', kind: 'llm.call', runtime: 'claude_code',
       payload: {in_flight_at_start: {background_agents: 7}}},
    ],
    delegations: [], approvals: [],
  }, {
    turn_id: 'u3',
    events: [{span_id: 'u3', kind: 'llm.call', runtime: 'claude_code', payload: {}}],
    delegations: [], approvals: [],
  }],
};
const inFlightMount = new _StubEl('div');
api.renderTree(inFlightTree, inFlightMount);
const turnHtml = (id) => {
  const h = inFlightMount.innerHTML;
  const from = h.indexOf('data-turn-id="' + id + '"');
  const to = h.indexOf('</section>', from);
  return h.slice(from, to);
};
const count = (h, needle) => h.split(needle).length - 1;
check('in-flight agent count on the turn header',
      turnHtml('u1').includes('replay-tree-badge in-flight') &&
      turnHtml('u1').includes('Background agents running: 3'));
check('in-flight workflow count on the turn header',
      turnHtml('u1').includes('Workflows running: 1'));
check('in-flight badges sit in the header',
      turnHtml('u1').indexOf('Workflows running: 1') < turnHtml('u1').indexOf('</header>'));
check('zero and non-numeric counts draw no badge',
      !turnHtml('u2').includes('replay-tree-badge in-flight'));
check('only the opening llm.call is read', !turnHtml('u2').includes('running: 7'));
check('turn without counts has no in-flight badge',
      !turnHtml('u3').includes('replay-tree-badge in-flight'));
check('fork delegations are tagged, top level and nested',
      count(turnHtml('u1'), 'replay-tree-badge fork') === 2);
const freshAt = turnHtml('u1').indexOf('delegated span freshspawn');
const freshSummary = turnHtml('u1').slice(freshAt, turnHtml('u1').indexOf('</summary>', freshAt));
check('fresh delegation is not tagged', !freshSummary.includes('replay-tree-badge fork'));
check('fork tag is on the fork delegation',
      turnHtml('u1').slice(turnHtml('u1').indexOf('delegated span forkspawn'), freshAt)
        .includes('Inherited context'));
check('delegation without a spawn payload is not tagged',
      !nestedHtml.includes('replay-tree-badge fork') &&
      !delegMount.innerHTML.includes('replay-tree-badge fork'));

// Notices above the turns (clawmetry-pro#135): a branched Pi conversation
// says the replay follows one branch, and an Aider replay says what the
// history file does not hold.
const noteHtml = (tree) => {
  const m = new _StubEl('div');
  api.renderTree(Object.assign(
    {session_id: 'n', row_count: 1, mode: null, workflows: [],
     turns: [{turn_id: 'u1', events: [], delegations: [], approvals: []}]}, tree), m);
  return m.innerHTML;
};
const piHtml = noteHtml({runtime: 'pi', branches: {branch_points: 2, entries_off_active_path: 7}});
check('branched conversation shows the branch notice',
      piHtml.includes('data-note="branches"') && piHtml.includes('Branch points in this conversation: 2.'));
check('branch notice counts the entries it leaves out',
      piHtml.includes('not shown: 7.'));
check('branch notice sits above the turns',
      piHtml.indexOf('data-note="branches"') < piHtml.indexOf('replay-tree-turn'));
check('no hidden entries, no hidden-entries sentence',
      !noteHtml({runtime: 'pi', branches: {branch_points: 1, entries_off_active_path: 0}})
        .includes('not shown'));
check('no branches field, no branch notice',
      !noteHtml({runtime: 'pi'}).includes('replay-tree-note') &&
      !noteHtml({runtime: 'pi', branches: null}).includes('replay-tree-note'));
check('branch counts that are not numbers draw no notice',
      !noteHtml({runtime: 'pi', branches: {branch_points: '<b>2</b>'}}).includes('replay-tree-note') &&
      !noteHtml({runtime: 'pi', branches: {branch_points: 0}}).includes('replay-tree-note'));
const aiderHtml = noteHtml({runtime: 'aider'});
check('aider replay says what the history file does not hold',
      aiderHtml.includes('data-note="aider"') && aiderHtml.includes('no tool calls'));
check('other runtimes get no aider notice',
      !noteHtml({runtime: 'claude_code'}).includes('replay-tree-note') &&
      !populatedMount.innerHTML.includes('replay-tree-note'));

if (fail > 0) {
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(1);
}
console.log(`${pass} passed`);
