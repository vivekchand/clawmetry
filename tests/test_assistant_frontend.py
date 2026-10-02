"""Read-only contract checks for the Assistant browser surface.

These tests do not start a browser or call a model.  The one behavioral check
uses a deliberately small DOM and fetch mock to exercise the history race that
is easy to miss in a visual smoke test.
"""

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

    script = textwrap.dedent(
        r"""
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
        const pending = {};
        function response(body, status = 200) {
          return { ok: status >= 200 && status < 300, status, text: () => Promise.resolve(JSON.stringify(body)) };
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
          if (elements.get('cm-assistant-thread').textContent.includes('**B answer**')) throw new Error('emphasis punctuation was displayed literally');
          if (!elements.get('cm-assistant-thread').textContent.includes('<script>literal</script>')) throw new Error('untrusted inline code was not kept as text');
          if (elements.get('cm-assistant-thread').textContent.includes('A answer')) throw new Error('older conversation overwrote newer conversation');

          const input = elements.get('cm-assistant-input');
          input.value = 'leave while answering';
          elements.get('cm-assistant-composer').dispatch('submit', { preventDefault() {} });
          await flush();
          if (!elements.get('cm-assistant-thread').textContent.includes('I’m checking the available evidence...')) throw new Error('chat did not enter its waiting state');
          context.assistantLeave();
          if (elements.get('cm-assistant-thread').textContent.includes('I’m checking the available evidence...')) throw new Error('leaving left a stale pending chat in the thread');
          pending.chat(response({ conversation_id: 'after-leave', answer: 'late answer', panels: [], sources: [] }));
          await flush();
        })().catch((error) => { console.error(error.message); process.exit(1); });
        """
    )
    subprocess.run([node, "-e", script], cwd=ROOT, check=True)
