"""Visible local desktop coverage.

AC-CHATGPT-001.2: the desktop uses one existing accounting namespace.
AC-CHATGPT-001.4: the selected runtime discloses unsupported desktop modes.
AC-CHATGPT-001.7: local desktop coverage keeps the paid Codex entitlement.

Exercise the shipped UI helper: a runtime change must remove the old claim,
and repeated refreshes must not accumulate coverage banners or fetch data.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def test_desktop_coverage_tracks_the_selected_runtime():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to execute the shipped browser helper")
    source = (Path(__file__).parents[1] / "clawmetry/static/js/app.js").read_text()
    start = source.index("function _cmApplyDesktopCoverageNote(page) {")
    end = source.index("function _cmApplyRuntimeScopeNote(name) {", start)
    script = """
const assert = require('node:assert/strict');
let runtime = 'codex';
let requests = 0;
global.fetch = () => { requests++; throw new Error('Coverage must not fetch'); };
global._cmRuntimeFilter = () => runtime;
global.document = { createElement: () => ({ remove() { page.children.splice(page.children.indexOf(this), 1); } }) };
const page = {
  children: [], firstChild: null,
  querySelector(selector) { return this.children.find(n => '#' + n.id === selector); },
  insertBefore(note) { this.children.unshift(note); }
};
""" + source[start:end] + """
_cmApplyDesktopCoverageNote(page);
assert.equal(page.children.length, 1);
assert.match(page.children[0].textContent, /local ChatGPT Work/);
assert.match(page.children[0].textContent, /Regular Chat and cloud Work conversations are not monitored/);
_cmApplyDesktopCoverageNote(page);
assert.equal(page.children.length, 1);
for (runtime of ['all', 'openclaw', 'claude_code']) {
  _cmApplyDesktopCoverageNote(page);
  assert.equal(page.children.length, 0);
}
runtime = 'codex';
_cmApplyDesktopCoverageNote(page);
assert.equal(page.children.length, 1);
assert.equal(requests, 0);
console.log(JSON.stringify({notes: page.children.length, requests}));
"""
    result = subprocess.run([node, "-e", script], text=True, capture_output=True, check=True)
    assert json.loads(result.stdout) == {"notes": 1, "requests": 0}


def test_desktop_reuses_paid_codex_identity():
    """AC-CHATGPT-001.2, AC-CHATGPT-001.7: no second accounting namespace."""
    from clawmetry.entitlements import ALL_RUNTIMES, PAID_RUNTIMES, RUNTIME_LABELS

    assert "codex" in PAID_RUNTIMES
    assert RUNTIME_LABELS["codex"] == "Codex / ChatGPT Work"
    assert "chatgpt" not in ALL_RUNTIMES
