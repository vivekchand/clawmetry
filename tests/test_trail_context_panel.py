"""The Inputs panel ("What the agent knew") renders what the API returns.

Two field bugs met on one card (founder report 2026-09-05: "why are runtime
details, tools used repeated & both empty?"):

  * ``/api/sessions/<id>/context`` fills ``content`` only for the TEXT kinds.
    ``tools_available``/``mcp_servers`` carry their payload in ``names`` and
    ``runtime_meta`` in ``meta``. The renderer read ``content`` alone, so
    exactly the kinds whose data lives elsewhere printed "Empty" while that
    data sat in the response.
  * A kind legitimately has SEVERAL rows -- the store keys context by sha256,
    so a context that changed mid-session is several versions. Rendered
    one-per-row they became two identically labelled sections with nothing on
    screen to tell them apart.

This executes the real renderer against a payload shaped like the reported
session (tools went 1 -> 5 when ToolSearch loaded, so two ``tools_available``
and two ``runtime_meta`` rows). A string-match test would have passed on the
broken code, so the block is run under node.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_TRAIL_JS = os.path.join(_ROOT, "clawmetry", "static", "js", "trail.js")
_CI = os.path.join(_ROOT, ".github", "workflows", "ci.yml")

# The reported session, reduced to the shape the endpoint returns.
_PAYLOAD = {
    "items": [
        {"kind": "runtime_meta", "content": None, "size_bytes": 173,
         "meta": {"cwd": "/repo", "model": "claude-opus-5", "tools_count": 1}},
        {"kind": "runtime_meta", "content": None, "size_bytes": 173,
         "meta": {"cwd": "/repo", "model": "claude-opus-5", "tools_count": 5}},
        {"kind": "tools_available", "content": None, "size_bytes": 73,
         "names": ["Bash", "ToolSearch", "mcp__chrome__navigate"]},
        {"kind": "tools_available", "content": None, "size_bytes": 73,
         "names": ["Bash"]},
        {"kind": "user_prompt", "content": "the opening request", "size_bytes": 19},
    ]
}


def _render():
    """Run the renderer's grouping block over _PAYLOAD and return its HTML."""
    if not shutil.which("node"):
        pytest.fail(
            "node is required for this guard; a skip here would hide the "
            "regression it exists to catch"
        )
    src = open(_TRAIL_JS, encoding="utf-8").read()
    marker = "    /* ONE section per kind"
    assert marker in src, (
        "the grouping block in renderContext() is gone or its opening comment "
        "was renamed. If you refactored it, point this harness at the new "
        "block; do not delete the guard: without the grouping, every kind "
        "renders once per stored version and the kinds whose payload lives in "
        "names/meta render as Empty."
    )
    start = src.index(marker)
    end = src.index("    if (!items.length) {")
    block = src[start:end]
    harness = """
const esc = s => String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const muted = t => '<div class="trail-muted">' + esc(t) + '</div>';
const T = (k, f, vars) => String(f).replace(/\\{(\\w+)\\}/g, (m, n) => (vars && vars[n] !== undefined) ? vars[n] : m);
const KIND_LABEL = {
  system_prompt: 'Instructions it was given', user_prompt: 'Opening prompt',
  tools_available: 'Tools it could use', mcp_servers: 'Connected services (MCP)',
  context_file: 'Project notes it read', runtime_meta: 'Runtime details' };
const items = %s.items;
let html = '';
%s
process.stdout.write(html);
""" % (json.dumps(_PAYLOAD), block)
    out = subprocess.run([shutil.which("node"), "-e", harness],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_each_kind_renders_exactly_once():
    html = _render()
    assert html.count("Runtime details") == 1, "runtime_meta rendered twice"
    assert html.count("Tools it could use") == 1, "tools_available rendered twice"


def test_the_payload_is_read_from_names_and_meta_not_content():
    """The kinds whose data does not live in `content` must not say Empty."""
    html = _render()
    assert ">Empty<" not in html, "a kind with data rendered as Empty"
    # Every tool across both versions, because "what it could use" over a
    # session is the union, and the two rows share a timestamp so neither is
    # "the latest".
    for tool in ("Bash", "ToolSearch", "mcp__chrome__navigate"):
        assert tool in html, tool
    assert "claude-opus-5" in html, "runtime_meta fields missing"


def test_it_says_what_changed_rather_than_hiding_a_version():
    html = _render()
    assert "tools_count" in html, "the field that moved is not named"
    assert "changed during the session" in html.lower()


def test_the_opening_prompt_is_not_repeated_in_this_panel():
    """It is already shown as "The request" beside this card."""
    assert "Opening prompt" not in _render()


def test_registered_in_ci_explicit_lists():
    ci = open(_CI, encoding="utf-8").read()
    assert "tests/test_trail_context_panel.py" in ci, (
        "CI runs explicit file lists; this test must be named in ci.yml or "
        "it never runs"
    )
