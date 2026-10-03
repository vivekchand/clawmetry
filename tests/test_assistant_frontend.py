"""Read-only contract checks for the Assistant browser surface.

These tests do not start a browser or call a model. Node VM tests exercise the
real requestStream function and the page with controlled byte streams and a
small DOM. Layout checks guard template order; visual validation stays manual.

* AC-ASSIST-005.1 -- template composer ordering: existing asset/layout guard;
  desktop/mobile layout and native light/dark palettes need manual validation.
* AC-ASSIST-005.2 -- actual delta callbacks and visible text before done.
* AC-ASSIST-005.3 -- complete payload fidelity; interrupted/failed turns never
  become ready answers. Persistence itself is covered by backend tests.
* AC-ASSIST-005.4 -- stop/navigation identity guards, transport failure and
  bounded stream cleanup.

Factory requirement fb690e36-8372-48f6-8e52-32fe5bffc345 v2 and blueprint
4be233ec-e717-4886-a6e3-8bf855597abb v10 were read before these tests were added.
"""

import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest


ROOT = Path(__file__).parents[1]
ASSISTANT_JS = ROOT / "clawmetry/static/js/assistant.js"
ASSISTANT_HTML = ROOT / "clawmetry/templates/tabs/assistant.html"
ASSISTANT_CSS = ROOT / "clawmetry/static/css/assistant.css"
DASHBOARD = ROOT / "dashboard.py"


_DOM_JS = r"""
const fs = require('fs');
const vm = require('vm');

class Node {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this.attributes = {};
    this.style = {};
    this.hidden = false;
    this.value = '';
    this.scrollHeight = 42;
    this.bounds = {top: 100, bottom: 200};
    this.scrollCalls = [];
    this._text = null;
    this.className = '';
    this.classList = {
      add: (...names) => names.forEach((name) => {
        if (!this.className.split(/\s+/).includes(name)) this.className += (this.className ? ' ' : '') + name;
      }),
      remove: (...names) => { this.className = this.className.split(/\s+/).filter((name) => name && !names.includes(name)).join(' '); },
      toggle: (name, on) => {
        const has = this.className.split(/\s+/).includes(name);
        if ((on && !has) || (!on && has)) this.classList[on ? 'add' : 'remove'](name);
      },
    };
  }
  set textContent(value) { this.children = []; this._text = String(value == null ? '' : value); }
  get textContent() {
    return (this._text == null ? '' : this._text) + this.children.map((child) => child.textContent).join('');
  }
  get firstChild() { return this.children[0] || null; }
  get childElementCount() { return this.children.length; }
  appendChild(child) { child.parentNode = this; this.children.push(child); return child; }
  removeChild(child) { const i = this.children.indexOf(child); if (i >= 0) this.children.splice(i, 1); child.parentNode = null; return child; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === 'id') this.id = String(value); }
  getAttribute(name) { return this.attributes[name]; }
  addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); }
  dispatch(name, event = {}) { (this.listeners[name] || []).forEach((handler) => handler(event)); }
  focus() {}
  select() {}
  getBoundingClientRect() { return this.bounds; }
  scrollIntoView(options) { this.scrollCalls.push(options); }
  querySelector(selector) {
    if (selector === '.cm-assistant-main' && this.className.split(/\s+/).includes('cm-assistant-main')) return this;
    if (selector === 'span') return this.children.find((child) => child.tagName === 'SPAN') || null;
    if (selector === '.cm-assistant-send-arrow') return this.children.find((child) => child.className === 'cm-assistant-send-arrow') || null;
    for (const child of this.children) { const found = child.querySelector(selector); if (found) return found; }
    return null;
  }
  querySelectorAll() { return []; }
}

const elements = new Map();
function add(id, tag, className) {
  const node = new Node(tag);
  node.id = id;
  node.className = className || '';
  elements.set(id, node);
  return node;
}
const page = add('page-assistant', 'div', 'page active');
const main = add('main', 'main', 'cm-assistant-main');
page.appendChild(main);
[
  ['cm-assistant-suggestions', 'div'], ['cm-assistant-status-message', 'div'],
  ['cm-assistant-data-notice', 'div'], ['cm-assistant-composer', 'form'],
  ['cm-assistant-input', 'textarea'], ['cm-assistant-voice', 'button'],
  ['cm-assistant-new-chat', 'button'], ['cm-assistant-engine', 'select'],
  ['cm-assistant-api-key', 'input'], ['cm-assistant-key-row', 'div'],
  ['cm-assistant-thread', 'section'], ['cm-assistant-history-list', 'div'],
  ['cm-assistant-status-pill', 'div'], ['cm-assistant-status-label', 'span'],
  ['cm-assistant-scope', 'span'], ['cm-assistant-setup-title', 'strong'],
  ['cm-assistant-setup-description', 'p'], ['cm-assistant-managed-copy', 'p'],
  ['cm-assistant-managed-link', 'a'],
].forEach(([id, tag]) => main.appendChild(add(id, tag)));
const send = add('cm-assistant-send', 'button');
send.appendChild(new Node('span'));
const arrow = new Node('span'); arrow.className = 'cm-assistant-send-arrow'; send.appendChild(arrow);
main.appendChild(send);
const engine = elements.get('cm-assistant-engine');
engine.options = ['auto', 'claude_cli', 'anthropic'].map((value) => { const option = new Node('option'); option.value = value; return option; });
engine.value = 'auto';

const document = {
  readyState: 'loading',
  getElementById: (id) => elements.get(id) || null,
  createElement: (tag) => new Node(tag),
  querySelectorAll: () => [],
  addEventListener: () => {},
};
"""


def test_assistant_assets_are_loaded_and_router_hooks_exist():
    dashboard = DASHBOARD.read_text()
    js = ASSISTANT_JS.read_text()
    html = ASSISTANT_HTML.read_text()

    assert "css/assistant.css" in dashboard
    assert "js/assistant.js" in dashboard
    app_js = (ROOT / "clawmetry/static/js/app.js").read_text()
    assert "loadAssistantPage" in app_js
    assert "assistantLeave" in app_js
    assert 'id="page-assistant"' in html
    assert "window.loadAssistantPage" in js
    assert "window.assistantLeave" in js

    # AC-ASSIST-005.1: DOM reading/tab order, not a mirror of CSS declarations.
    class MainOrder(HTMLParser):
        in_main = False

        def __init__(self):
            super().__init__()
            self.ids = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "main":
                self.in_main = "cm-assistant-main" in attrs.get("class", "").split()
            if self.in_main and "id" in attrs:
                self.ids.append(attrs["id"])

        def handle_endtag(self, tag):
            if tag == "main":
                self.in_main = False

    parsed = MainOrder()
    parsed.feed(html)
    ordered = [
        "cm-assistant-title", "cm-assistant-thread", "cm-assistant-composer",
        "cm-assistant-input", "cm-assistant-suggestions", "cm-assistant-status-message",
    ]
    assert [identifier for identifier in parsed.ids if identifier in ordered] == ordered


def test_assistant_js_parses_and_renders_untrusted_values_as_text():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")

    subprocess.run([node, "--check", str(ASSISTANT_JS)], check=True)
    source = ASSISTANT_JS.read_text()

    # The surface creates DOM nodes and assigns textContent.  Keep this guard
    # tight because generated labels, rows, errors, and source names all come
    # from provider/store data.
    assert "textContent" in source
    assert "innerHTML" not in source
    assert "onclick=" not in source


def test_assistant_has_voice_denial_and_abort_paths():
    source = ASSISTANT_JS.read_text()

    assert "AbortController" in source
    assert "_assistantTimedOut" in source
    assert "event.error === 'not-allowed'" in source
    assert "Voice input is not supported by this browser" in source
    assert "cancelAllRequests('leave')" in source


def test_history_detail_requests_cannot_let_an_older_click_overwrite_a_newer_one():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")

    script = _DOM_JS + textwrap.dedent(
        r"""
        const pending = {};
        function response(body, status = 200) {
          return {
            ok: status >= 200 && status < 300, status,
            headers: { get: () => 'application/json' },
            json: () => Promise.resolve(body),
            text: () => Promise.resolve(JSON.stringify(body)),
          };
        }
        global.fetch = (url) => {
          if (url.endsWith('/status')) return Promise.resolve(response({
            available: false, providers: [], scope: 'All runtimes on this node', managed: {},
          }));
          if (url.endsWith('/conversations')) return Promise.resolve(response({
            conversations: [
              { id: 'a', title: 'Conversation A', updated_at: Date.now() },
              { id: 'b', title: 'Conversation B', updated_at: Date.now() },
            ],
          }));
          const id = url.split('/').pop();
          return new Promise((resolve) => { pending[id] = resolve; });
        };
        const context = {
          console, document, navigator: { language: 'en-US' }, fetch: global.fetch,
          setTimeout, clearTimeout, Date, JSON, Number, String, Array, Object, Math,
          Promise, AbortController: undefined,
        };
        context.window = context;
        vm.runInNewContext(fs.readFileSync('clawmetry/static/js/assistant.js', 'utf8'), context);
        context.loadAssistantPage();

        const flush = () => new Promise((resolve) => setTimeout(resolve, 5));
        (async () => {
          await flush();
          await flush();
          const history = elements.get('cm-assistant-history-list');
          if (history.children.length !== 2) throw new Error('history did not render');
          history.children[0].dispatch('click');
          history.children[1].dispatch('click');
          pending.b(response({ id: 'b', messages: [{ role: 'assistant', content: '**B answer** `<script>literal</script>`' }] }));
          await flush();
          await flush();
          pending.a(response({ id: 'a', messages: [{ role: 'assistant', content: 'A answer' }] }));
          await flush();
          await flush();
          if (!elements.get('cm-assistant-thread').textContent.includes('B answer')) throw new Error('newer conversation was lost');
          if (!elements.get('cm-assistant-status-message').hidden) throw new Error('loaded conversation kept its loading notice');
          if (elements.get('cm-assistant-thread').textContent.includes('**B answer**')) throw new Error('emphasis punctuation was displayed literally');
          if (!elements.get('cm-assistant-thread').textContent.includes('<script>literal</script>')) throw new Error('untrusted inline code was not kept as text');
          if (elements.get('cm-assistant-thread').textContent.includes('A answer')) throw new Error('older conversation overwrote newer conversation');

          const input = elements.get('cm-assistant-input');
          input.value = 'leave while answering';
          elements.get('cm-assistant-composer').dispatch('submit', { preventDefault() {} });
          await flush();
          if (!elements.get('cm-assistant-thread').textContent.includes('Checking your question...')) throw new Error('chat did not enter its waiting state');
          context.assistantLeave();
          if (elements.get('cm-assistant-thread').textContent.includes('Checking your question...')) throw new Error('leaving left a stale pending chat in the thread');
          pending.chat(response({ conversation_id: 'after-leave', answer: 'late answer', panels: [], sources: [] }));
          await flush();
          if (elements.get('cm-assistant-thread').textContent.includes('late answer')) throw new Error('late JSON answer rendered after leaving');
        })().catch((error) => { console.error(error.message); process.exit(1); });
        """
    )
    subprocess.run([node, "-e", script], cwd=ROOT, check=True, timeout=20)


@pytest.mark.parametrize('runtime_column', ['runtime', 'Runtime', 'RUNTIME'])
def test_saved_panel_headers_stay_readable_with_runtime_lookup_fallback(runtime_column):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is not installed')
    source = (ROOT / 'clawmetry/static/js/custom-dashboard.js').read_text()
    helpers = source[source.index('  function esc('):source.index('  function panelTarget(')]
    table = source[source.index('  function renderTable('):source.index('  function renderChart(')]
    script = '\n'.join([
        "var window = {_cmRuntimeLabel: value => value === 'claude_code' ? 'Claude Code' : value};",
        helpers, table,
        "var host = {}; renderTable(host, [{estimated_cost_usd:12, " + runtime_column + ":'claude_code', tokens:null, note:'<script>alert(1)</script>'}]);",
        "console.log(host.innerHTML);",
    ])
    result = subprocess.run([node, '-e', script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert '<th>Estimated Cost Usd</th>' in result.stdout
    assert '<td>Claude Code</td>' in result.stdout
    assert result.stdout.index('<td>Claude Code</td>') < result.stdout.index('<td>12</td>')
    assert 'Not measured' in result.stdout
    assert '<script>' not in result.stdout
    assert '&lt;script&gt;' in result.stdout


def test_saved_panels_explain_their_scope_and_link_to_assistant():
    source = (ROOT / 'clawmetry/templates/tabs/overview.html').read_text()
    section = source.split('id="custom-dashboard-section"', 1)[1].split('</section>', 1)[0]
    assert "switchTab('assistant')" in section
    assert 'Each panel keeps its saved filters' in section
    assert 'runtime selector above does not change these panels' in section


_STREAM_JS = r"""
const assert = require('node:assert/strict');
const { TextDecoder } = require('node:util');
const flush = () => new Promise(resolve => setImmediate(resolve));
const frame = (type, data, eol = '\n') =>
  'event: ' + type + eol + 'data: ' + JSON.stringify(data) + eol + eol;
const saved = {
  conversation_id: 'saved-1', answer: 'Café 世界 🦞\nSecond line',
  panels: [{chart_spec: {chart_type: 'number', title: 'Recorded sessions', y: 'count'}, rows: [{count: 3}]}],
  sources: [{label: 'Local evidence', rows: [{runtime: 'codex', count: 3}], sql: 'SELECT count(*) FROM sessions'}],
};
const plain = value => JSON.parse(JSON.stringify(value));

function controlledStream() {
  const queued = [];
  let waiting = null;
  const stream = {
    reads: 0, cancellations: 0,
    read() {
      this.reads++;
      if (queued.length) return consume(queued.shift());
      assert.equal(waiting, null, 'only one read may be outstanding');
      return new Promise((resolve, reject) => { waiting = {resolve, reject}; });
    },
    cancel() {
      this.cancellations++;
      if (waiting) { waiting.resolve({done: true}); waiting = null; }
      return Promise.resolve();
    },
    push(value) { deliver({done: false, value: Buffer.from(value)}); },
    end() { deliver({done: true}); },
    fail(error) { deliver({error}); },
  };
  function consume(item) {
    return item.error ? Promise.reject(item.error) : Promise.resolve(item);
  }
  function deliver(item) {
    if (!waiting) { queued.push(item); return; }
    const pending = waiting;
    waiting = null;
    if (item.error) pending.reject(item.error);
    else pending.resolve(item);
  }
  stream.response = {
    ok: true, status: 200,
    headers: {get: () => 'text/event-stream; charset=utf-8'},
    body: {getReader: () => stream, cancel: () => stream.cancel()},
    json() { assert.fail('an SSE response must not be buffered as JSON'); },
  };
  return stream;
}

function transport(response, overrides = {}) {
  const fs = require('node:fs');
  const vm = require('node:vm');
  const source = fs.readFileSync('clawmetry/static/js/assistant.js', 'utf8');
  // Evaluate the actual private function verbatim, without changing exports
  // or evaluating the DOM module. Include its real request-removal helper.
  const remove = source.slice(source.indexOf('  function removeRequest('),
                              source.indexOf('  function requestJson('));
  const request = source.slice(source.indexOf('  function requestStream('),
                               source.indexOf('  function cancelAllRequests('));
  assert.ok(remove && request, 'requestStream extraction anchors moved');
  const state = {requests: []};
  const timers = new Map();
  const calls = [];
  const context = {
    state, TextDecoder, AbortController,
    fetch: async (url, options) => { calls.push({url, options}); return response; },
    setTimeout: (fn, ms) => { const token = {}; timers.set(token, {fn, ms}); return token; },
    clearTimeout: token => timers.delete(token),
    ...overrides,
  };
  vm.createContext(context);
  vm.runInContext(remove + '\n' + request, context);
  return {state, timers, calls, start: onEvent => context.requestStream(
    '/api/assistant/chat', {method: 'POST', body: '{"stream":true}'}, onEvent)};
}

function assertClean(harness, stream) {
  assert.equal(harness.state.requests.length, 0, 'request must be unregistered');
  assert.equal(harness.timers.size, 0, 'deadline must be cleared');
  if (stream) assert.ok(stream.cancellations > 0, 'reader must be cancelled');
}
"""


def _run_node(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    # Keep Node alive while promises are pending: an unresolved read without
    # active handles otherwise exits successfully and silently skips assertions.
    wrapped = "\n".join([
        "const watchdog = setTimeout(() => { console.error('Node test stalled'); process.exit(1); }, 10000);",
        "(async () => {",
        script,
        "})().then(() => clearTimeout(watchdog)).catch(error => { console.error(error); process.exit(1); });",
    ])
    result = subprocess.run(
        [node, "-e", wrapped], cwd=ROOT, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("eol", ["\n", "\r\n", "mixed"], ids=["lf", "crlf", "mixed"])
def test_request_stream_preserves_utf8_and_framing_at_every_byte_boundary(eol):
    """AC-ASSIST-005.2: chunks may split characters, JSON or CRLF delimiters."""
    _run_node(_STREAM_JS + "const eolMode = " + json.dumps(eol) + r"""
        const eol = eolMode === 'mixed' ? '\r\n' : eolMode;
        const lastEol = eolMode === 'mixed' ? '\n' : eol;
        const expected = [
          ['status', {message: 'Reading evidence'}],
          ['delta', {text: 'Café 世界 🦞'}],
          ['delta', {text: '\nSecond line'}],
        ];
        const wire = Buffer.from(
          ': heartbeat' + eol + eol +
          frame('status', expected[0][1], eol) +
          'event: delta' + eol + 'data: {"text":' + eol +
          'data: "Café 世界 🦞"}' + eol + eol +
          frame('tool', {input: 'private tool payload'}, eol) +
          frame('thinking', {text: 'private reasoning'}, eol) +
          frame('delta', expected[2][1], lastEol) + frame('done', saved, lastEol));
        const splits = [];
        // Every possible two-chunk split, plus multiple cuts inside the same
        // multi-byte character and frame. All partitions are deterministic.
        for (let cut = 1; cut < wire.length; cut++) {
          splits.push([wire.subarray(0, cut), wire.subarray(cut)]);
        }
        for (const width of [1, 2, 3, 5, 17, wire.length]) {
          const chunks = [];
          for (let offset = 0; offset < wire.length; offset += width) {
            chunks.push(wire.subarray(offset, offset + width));
          }
          splits.push(chunks);
        }
        for (const chunks of splits) {
          const stream = controlledStream();
          chunks.forEach(chunk => stream.push(chunk));
          stream.end();
          const harness = transport(stream.response);
          const events = [];
          const request = harness.start((type, data) => events.push([type, plain(data)]));
          assert.deepEqual(plain(await request.promise), saved);
          assert.deepEqual(events, expected);
          assertClean(harness, stream);
        }
    """)


def test_request_stream_delivers_deltas_before_done_without_waiting_for_eof():
    """AC-ASSIST-005.2: callbacks occur while the final response is withheld."""
    _run_node(_STREAM_JS + r"""
        const stream = controlledStream();
        const harness = transport(stream.response);
        const events = [];
        const request = harness.start((type, data) => events.push([type, plain(data)]));
        let settled = false;
        request.promise.then(() => { settled = true; });
        stream.push(frame('status', {message: 'Gathering evidence'}));
        await flush();
        assert.deepEqual(events, [['status', {message: 'Gathering evidence'}]]);
        assert.equal(settled, false);
        const delta = frame('delta', {text: saved.answer}, '\r\n');
        stream.push(delta.slice(0, -1));
        await flush();
        assert.equal(events.length, 1, 'a frame needs its entire blank-line delimiter');
        stream.push('\n');
        await flush();
        assert.deepEqual(events[1], ['delta', {text: saved.answer}]);
        assert.equal(settled, false, 'actual text must arrive before done');
        stream.push(frame('done', saved) + frame('delta', {text: 'late duplicate'}));
        assert.deepEqual(plain(await request.promise), saved);
        assert.equal(events.length, 2, 'done is terminal even within one read');
        assertClean(harness, stream);
    """)


@pytest.mark.parametrize("fault", [
    "eof", "partial-json", "unframed-done", "bad-json", "array", "null",
    "missing-answer", "missing-conversation", "provider-error", "save-error",
    "reader-error", "invalid-utf8", "truncated-utf8", "oversize",
])
def test_request_stream_faults_never_resolve_as_saved_answers(fault):
    """AC-ASSIST-005.3: even a complete-looking delta needs valid saved done."""
    _run_node(_STREAM_JS + "const fault = " + json.dumps(fault) + r"""
        const stream = controlledStream();
        const harness = transport(stream.response);
        const events = [];
        const request = harness.start((type, data) => events.push([type, plain(data)]));
        const rejected = assert.rejects(request.promise, error => {
          assert.ok(error.message, 'failure must explain itself');
          if (fault === 'provider-error') assert.match(error.message, /Provider unavailable/);
          if (fault === 'save-error') assert.match(error.message, /could not be saved/);
          return true;
        });
        stream.push(frame('delta', {text: saved.answer}));
        await flush();
        assert.deepEqual(events, [['delta', {text: saved.answer}]]);
        const bad = {
          'partial-json': 'event: done\ndata: {"answer":',
          'unframed-done': frame('done', saved).slice(0, -1),
          'bad-json': 'event: done\ndata: {broken}\n\n',
          'array': frame('done', []),
          'null': frame('done', null),
          'missing-answer': frame('done', {conversation_id: 'unsaved'}),
          'missing-conversation': frame('done', {answer: saved.answer}),
          'provider-error': frame('error', {error: 'Provider unavailable'}) + frame('done', saved),
          'save-error': frame('error', {error: 'The answer could not be saved'}) + frame('done', saved),
          'invalid-utf8': Buffer.from([0xff]),
          'truncated-utf8': Buffer.from([0xf0, 0x9f]),
          'oversize': Buffer.alloc(2 * 1024 * 1024 + 1, 32),
        };
        if (bad[fault] !== undefined) stream.push(bad[fault]);
        if (fault === 'reader-error') stream.fail(new Error('connection reset'));
        else stream.end();
        await rejected;
        assert.equal(events.length, 1, 'failure must never fabricate a completion callback');
        assertClean(harness, stream);
    """)


@pytest.mark.parametrize("missing", ["body", "reader", "decoder"])
def test_request_stream_missing_transport_is_explicit_and_recoverable(missing):
    """AC-ASSIST-005.4: unsupported transport rejects with actionable feedback."""
    _run_node(_STREAM_JS + "const missing = " + json.dumps(missing) + r"""
        const stream = controlledStream();
        if (missing === 'body') stream.response.body = null;
        if (missing === 'reader') stream.response.body = {};
        const harness = transport(stream.response, missing === 'decoder' ? {TextDecoder: undefined} : {});
        const request = harness.start(() => assert.fail('unsupported transport emitted text'));
        await assert.rejects(request.promise, /cannot receive live replies.*try again/i);
        assert.equal(stream.reads, 0);
        assertClean(harness);
    """)


def test_request_stream_legacy_json_and_http_errors_keep_their_contract():
    _run_node(_STREAM_JS + r"""
        for (const status of [200, 401, 503]) {
          const body = status === 200 ? saved : {error: 'Engine unavailable'};
          const harness = transport({
            ok: status === 200, status, headers: {get: () => 'application/json'},
            json: async () => body,
          });
          const request = harness.start(() => assert.fail('JSON fallback must not simulate deltas'));
          if (status === 200) assert.deepEqual(plain(await request.promise), saved);
          else await assert.rejects(request.promise, error => {
            assert.equal(error.status, status);
            assert.deepEqual(plain(error.data), body);
            return true;
          });
          assertClean(harness);
        }
        const harness = transport({
          ok: true, headers: {get: () => 'text/html'},
          json: async () => { throw new SyntaxError('not JSON'); },
        });
        await assert.rejects(harness.start(() => {}).promise, /unavailable.*Refresh and try again/);
        assertClean(harness);
    """)


@pytest.mark.parametrize("with_abort_controller", [True, False], ids=["abort", "no-abort-api"])
def test_request_stream_deadline_cancels_stalled_reader_and_clears_resources(with_abort_controller):
    """AC-ASSIST-005.4: enforce the bounded deadline without real sleeps."""
    _run_node(_STREAM_JS + "const withAbort = " + json.dumps(with_abort_controller) + r"""
        const stream = controlledStream();
        const harness = transport(stream.response, withAbort ? {} : {AbortController: undefined});
        const request = harness.start(() => assert.fail('stalled transport emitted text'));
        const rejected = assert.rejects(request.promise, error => {
          assert.equal(error._assistantTimedOut, true);
          return true;
        });
        await flush();
        assert.equal(stream.reads, 1);
        assert.equal(harness.timers.size, 1);
        const deadline = [...harness.timers.values()][0];
        assert.ok(deadline.ms > 0 && deadline.ms <= 180000);
        deadline.fn();
        await rejected;
        if (withAbort) assert.equal(request.controller.signal.aborted, true);
        assertClean(harness, stream);
    """)


@pytest.mark.parametrize("with_abort_controller", [True, False], ids=["abort", "no-abort-api"])
def test_request_stream_deadline_rejects_fetch_that_never_resolves(with_abort_controller):
    """AC-ASSIST-005.4: the deadline also bounds waiting for response headers."""
    _run_node(_STREAM_JS + "const withAbort = " + json.dumps(with_abort_controller) + r"""
        const harness = transport(null, {
          fetch: () => new Promise(() => {}),
          ...(withAbort ? {} : {AbortController: undefined}),
        });
        const request = harness.start(() => assert.fail('unresolved fetch emitted text'));
        let failure;
        const outcome = request.promise.then(
          () => assert.fail('timed out fetch resolved successfully'),
          error => { failure = error; },
        );
        [...harness.timers.values()][0].fn();
        await flush();
        assert.ok(failure, 'deadline must settle the request even if fetch ignores abort');
        assert.equal(failure._assistantTimedOut, true);
        await outcome;
        assertClean(harness);
    """)


def test_request_stream_cancels_response_body_that_arrives_after_deadline():
    """AC-ASSIST-005.4: a late fetch must not strand an unbounded stream read."""
    _run_node(_STREAM_JS + r"""
        const stream = controlledStream();
        let resolveFetch;
        const harness = transport(null, {
          AbortController: undefined,
          fetch: () => new Promise(resolve => { resolveFetch = resolve; }),
        });
        const request = harness.start(() => assert.fail('expired response emitted text'));
        const rejected = assert.rejects(request.promise, error => error._assistantTimedOut === true);
        [...harness.timers.values()][0].fn();
        await rejected;
        assertClean(harness);
        // No bytes ever arrive: checking timedOut after read() is too late.
        resolveFetch(stream.response);
        await flush();
        assert.ok(stream.cancellations > 0, 'late response body must be closed without waiting for data');
        assertClean(harness);
    """)


_PAGE_STREAM_JS = _DOM_JS + _STREAM_JS + r"""
const streams = [];
const chatCalls = [];
const timers = new Map();
let historyLoads = 0;
function jsonResponse(body) {
  return {
    ok: true, status: 200, headers: {get: () => 'application/json'},
    json: async () => body, text: async () => JSON.stringify(body),
  };
}
const context = {
  console, document, navigator: {language: 'en-US'}, TextDecoder, AbortController,
  innerHeight: 800,
  setTimeout(fn, ms) { const token = {}; timers.set(token, {fn, ms}); return token; },
  clearTimeout: token => timers.delete(token),
  fetch: async (url, options) => {
    if (url.endsWith('/status')) return jsonResponse({
      available: true, data_available: true, providers: [], managed: {},
    });
    if (url.endsWith('/conversations')) {
      historyLoads++;
      return jsonResponse({conversations: [{id: 'b', title: 'Conversation B'}]});
    }
    if (url.endsWith('/conversations/b')) return jsonResponse({
      id: 'b', messages: [{role: 'assistant', content: 'Saved conversation B'}],
    });
    assert.ok(url.endsWith('/chat'), 'unexpected fetch: ' + url);
    const stream = streams.shift();
    assert.ok(stream, 'test must provide each chat response');
    chatCalls.push({options, payload: JSON.parse(options.body)});
    return stream.response;
  },
};
context.window = context;
vm.runInNewContext(fs.readFileSync('clawmetry/static/js/assistant.js', 'utf8'), context);
context.loadAssistantPage();
await flush();
const thread = elements.get('cm-assistant-thread');
const status = elements.get('cm-assistant-status-message');
const input = elements.get('cm-assistant-input');
const submit = () => elements.get('cm-assistant-composer').dispatch('submit', {preventDefault() {}});
function byClass(root, name) {
  return root.children.flatMap(child => [
    ...(child.className.split(/\s+/).includes(name) ? [child] : []),
    ...byClass(child, name),
  ]);
}
async function startChat(question = 'Which agents worked today?') {
  const stream = controlledStream();
  streams.push(stream);
  input.value = question;
  submit();
  await flush();
  return stream;
}
function assertIdle() {
  assert.equal(input.getAttribute('aria-busy'), 'false');
  assert.equal(send.querySelector('span').textContent, 'Send');
  assert.equal(byClass(thread, 'is-streaming').length, 0);
}
"""


def test_send_message_shows_real_partial_text_then_final_sources_and_panels():
    """AC-ASSIST-005.2/.3: DOM progresses before done; saved payload wins once."""
    _run_node(_PAGE_STREAM_JS + r"""
        assert.equal(thread.childElementCount, 0);
        assert.ok(!main.className.includes('has-messages'));
        const stream = await startChat();
        assert.equal(chatCalls[0].payload.stream, true);
        assert.equal(chatCalls[0].options.credentials, 'same-origin');
        assert.equal(chatCalls[0].options.method, 'POST');
        assert.match(main.className, /has-messages/);
        assert.equal(send.querySelector('span').textContent, 'Stop');
        assert.match(thread.textContent, /Checking your question/);
        stream.push(frame('status', {message: 'Reading recorded sessions'}));
        await flush();
        assert.match(thread.textContent, /Reading recorded sessions/);
        assert.equal(byClass(thread, 'is-assistant')[0].children[1].children[1].textContent, '');
        const answer = '**Café 世界 🦞** `<script>literal</script>`';
        stream.push(frame('thinking', {text: 'hidden reasoning'}));
        stream.push(frame('tool', {input: 'hidden tool payload'}));
        stream.push(frame('delta', {text: answer.slice(0, 5)}));
        await flush();
        const content = byClass(thread, 'cm-assistant-message-content')[1];
        assert.equal(content.textContent, answer.slice(0, 5));
        assert.match(thread.textContent, /Writing answer/);
        assert.ok(!status.textContent.includes('Answer ready'));
        assert.equal(historyLoads, 1, 'partial turns must not refresh saved history');
        stream.push(frame('delta', {text: answer.slice(5)}));
        await flush();
        assert.equal(content.textContent, 'Café 世界 🦞 <script>literal</script>');
        assert.ok(content.children.some(child => child.tagName === 'STRONG'));
        assert.ok(content.children.some(child => child.tagName === 'CODE'));
        assert.ok(!thread.textContent.includes('hidden reasoning'));
        assert.ok(!thread.textContent.includes('hidden tool payload'));
        assert.equal(byClass(thread, 'cm-assistant-panel').length, 0);
        stream.push(frame('done', {...saved, answer}));
        await flush();
        assert.equal(content.textContent, 'Café 世界 🦞 <script>literal</script>');
        assert.equal(byClass(thread, 'is-assistant').length, 1);
        assert.equal(byClass(thread, 'cm-assistant-stream-status').length, 0);
        assert.equal(byClass(thread, 'cm-assistant-panel-title')[0].textContent, 'Recorded sessions');
        assert.equal(byClass(thread, 'cm-assistant-number')[0].textContent, '3');
        assert.match(byClass(thread, 'cm-assistant-sources')[0].textContent, /Local evidence/);
        assert.match(thread.textContent, /SELECT count\(\*\) FROM sessions/);
        assert.match(status.textContent, /Answer ready/);
        assert.equal(historyLoads, 2);
        assertIdle();
        assert.equal(timers.size, 0);
        assert.ok(stream.cancellations > 0);
        const followup = await startChat('What changed?');
        assert.equal(chatCalls[1].payload.conversation_id, saved.conversation_id);
        followup.push(frame('done', saved));
        await flush();
    """)


@pytest.mark.parametrize("fault", ["eof", "provider-error", "save-error", "timeout"])
def test_send_message_preserves_failed_partial_as_incomplete_and_allows_retry(fault):
    """AC-ASSIST-005.3/.4: partial failure cannot become a ready/saved answer."""
    _run_node(_PAGE_STREAM_JS + "const fault = " + json.dumps(fault) + r"""
        const stream = await startChat();
        stream.push(frame('delta', {text: 'Partial evidence 🦞'}));
        await flush();
        if (fault === 'eof') stream.end();
        else if (fault === 'timeout') {
          assert.equal(timers.size, 1);
          [...timers.values()][0].fn();
        } else stream.push(frame('error', {error: fault === 'save-error'
          ? 'The answer could not be saved' : 'Provider unavailable'}));
        await flush();
        assert.match(thread.textContent, /Partial evidence 🦞/);
        assert.match(byClass(thread, 'cm-assistant-stream-status')[0].textContent, /Incomplete answer/i);
        assert.match(status.className, /is-error/);
        assert.ok(!status.textContent.includes('Answer ready'));
        if (fault === 'timeout') assert.match(status.textContent, /too long|timed out/i);
        assert.equal(historyLoads, 1);
        assert.equal(byClass(thread, 'cm-assistant-panel').length, 0);
        assertIdle();
        assert.equal(timers.size, 0);
        assert.ok(stream.cancellations > 0);
        const retry = await startChat('Try a narrower question');
        assert.equal(chatCalls[1].payload.conversation_id, undefined, 'unsaved turn must not adopt an id');
        retry.push(frame('done', saved));
        await flush();
        assert.match(status.textContent, /Answer ready/);
        assertIdle();
    """)


@pytest.mark.parametrize("action", ["stop", "leave", "new-chat", "conversation"])
def test_send_message_cancellation_and_navigation_ignore_late_stream_events(action):
    """AC-ASSIST-005.4: preserve stopped partials; stale events cannot change UI."""
    _run_node(_PAGE_STREAM_JS + "const action = " + json.dumps(action) + r"""
        const oldStream = await startChat();
        oldStream.push(frame('delta', {text: 'Useful partial 🦞'}));
        await flush();
        if (action === 'stop') submit();
        if (action === 'leave') { context.assistantLeave(); context.loadAssistantPage(); }
        if (action === 'new-chat') elements.get('cm-assistant-new-chat').dispatch('click');
        if (action === 'conversation') elements.get('cm-assistant-history-list').children[0].dispatch('click');
        await flush();
        assert.equal(chatCalls[0].options.signal.aborted, true);
        assertIdle();
        if (action === 'stop' || action === 'leave') {
          assert.match(thread.textContent, /Useful partial 🦞/);
          assert.match(thread.textContent, /Stopped.*incomplete/);
        } else if (action === 'conversation') {
          assert.match(thread.textContent, /Saved conversation B/);
          assert.ok(!thread.textContent.includes('Useful partial'));
        } else {
          assert.equal(thread.childElementCount, 0);
          assert.ok(!main.className.includes('has-messages'));
        }
        // The mock transport deliberately ignores abort and delivers late data
        // after a new request owns the page. Identity guards must still hold.
        const currentStream = await startChat('A newer question');
        currentStream.push(frame('delta', {text: 'Current response'}));
        await flush();
        const before = thread.textContent;
        const beforeStatus = status.textContent;
        oldStream.push(frame('status', {message: 'Stale status'}) +
          frame('delta', {text: 'Stale delta'}) +
          frame('done', {...saved, answer: 'Stale final answer', conversation_id: 'stale-id'}));
        await flush();
        assert.equal(thread.textContent, before);
        assert.equal(status.textContent, beforeStatus);
        assert.equal(input.getAttribute('aria-busy'), 'true', 'old cleanup must not unlock new composer');
        assert.equal(historyLoads, 1);
        assert.ok(oldStream.cancellations > 0);
        currentStream.push(frame('done', {...saved, answer: 'Current response'}));
        await flush();
        assert.match(thread.textContent, /Current response/);
        assert.ok(!thread.textContent.includes('Stale'));
        assert.equal(historyLoads, 2);
        assertIdle();
        assert.equal(timers.size, 0);
    """)


def test_send_message_stop_closes_stalled_reader_without_abort_controller():
    """AC-ASSIST-005.4: Stop releases a reader even with no native abort API."""
    _run_node(_PAGE_STREAM_JS + r"""
        context.AbortController = undefined;
        const stream = await startChat();
        stream.push(frame('delta', {text: 'Keep this partial answer'}));
        await flush();
        assert.equal(chatCalls[0].options.signal, undefined);
        assert.equal(timers.size, 1);
        submit();
        await flush();
        assert.ok(stream.cancellations > 0, 'Stop must close the active reader immediately');
        assert.equal(timers.size, 0, 'Stop must settle without waiting for timeout or another chunk');
        assert.match(thread.textContent, /Keep this partial answer/);
        assert.match(thread.textContent, /Stopped.*incomplete/);
        assert.equal(historyLoads, 1);
        assertIdle();
    """)


@pytest.mark.parametrize("answer_bottom, follows", [(400, True), (-50, False), (1500, False)])
def test_stream_scroll_follows_visible_answer_without_jumping_away_from_older_messages(answer_bottom, follows):
    """Follow the visible answer above the composer, independent of mobile history height."""
    _run_node(_PAGE_STREAM_JS + "const answerBottom = " + json.dumps(answer_bottom)
              + "; const follows = " + json.dumps(follows) + r"""
        document.scrollingElement = {scrollHeight: 5000, scrollTop: 100, clientHeight: 600};
        elements.get('cm-assistant-composer').bounds = {top: 500, bottom: 600};
        const stream = await startChat();
        const article = byClass(thread, 'is-assistant')[0];
        article.bounds = {top: answerBottom - 100, bottom: answerBottom};
        article.scrollCalls.length = 0;
        stream.push(frame('delta', {text: 'Live text'}));
        await flush();
        assert.equal(article.scrollCalls.length, follows ? 1 : 0);
        assert.match(article.textContent, /Live text/);
        stream.push(frame('done', {...saved, answer: 'Live text'}));
        await flush();
        assertIdle();
    """)
