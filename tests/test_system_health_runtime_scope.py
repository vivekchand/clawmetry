"""System Health on the Overview tab follows the runtime switcher.

Burned 2026-09-14: with the switcher on Claude Code the panel listed
"OpenClaw Gateway :18789", a "Healthy" heartbeat, Cron Jobs and "Connect a
channel", none of which Claude Code has, and Sub-Agents read "0 runs, 100%
success" because the endpoint stamped every counted run a success.

* AC-GOV-001.3 -- a runtime with no sub-agent outcome keeps its run count and
  reports no success rate instead of inventing one.
* AC-OBS-002.3 -- when the sub-agent store cannot be read the card is marked
  unavailable rather than showing zeros as current.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from routes.health import subagent_health_block  # noqa: E402

_APP_JS = os.path.join(_REPO, "clawmetry", "static", "js", "app.js")
_OVERVIEW = os.path.join(_REPO, "clawmetry", "templates", "tabs", "overview.html")


def _src(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _function_body(src, header):
    start = src.index(header)
    nxt = re.search(r"\n(?:async )?function ", src[start + len(header):])
    return src[start: start + len(header) + (nxt.start() if nxt else len(src))]


_STATS = {
    "openclaw": {"spawned": 4, "completed": 3, "failed": 1, "running": 0},
    "claude_code": {"spawned": 2, "completed": 0, "failed": 0, "running": 2},
    "nemoclaw": {"spawned": 1, "completed": 1, "failed": 0, "running": 0},
}


# ── backend: /api/system-health sub-agent block ──────────────────────────────


def test_scoped_to_selected_runtime():
    block = subagent_health_block(_STATS, "claude_code")
    assert block["runs"] == 2
    assert block["running"] == 2


def test_no_finished_runs_reports_no_success_rate():
    block = subagent_health_block(_STATS, "claude_code")
    assert block["successPct"] is None


def test_idle_runtime_is_not_one_hundred_percent():
    block = subagent_health_block({}, "codex")
    assert block["available"] is True
    assert block["runs"] == 0
    assert block["successPct"] is None


def test_success_rate_counts_only_finished_runs():
    block = subagent_health_block(_STATS, "openclaw")
    assert block["successPct"] == 75


def test_all_sums_every_runtime():
    block = subagent_health_block(_STATS, "all")
    assert block["runs"] == 7
    assert block["successPct"] == 80


def test_nemoclaw_includes_openclaw_adapter_bucket():
    assert subagent_health_block(_STATS, "nemoclaw")["runs"] == 5


def test_unreadable_store_is_unavailable_not_zero():
    block = subagent_health_block(None, "claude_code")
    assert block["available"] is False
    assert block["runs"] is None
    assert block["successPct"] is None


# ── template: every runtime-specific section can be hidden as a unit ─────────


class _DivTree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.ancestors = {}

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        el_id = dict(attrs).get("id")
        if el_id:
            self.ancestors[el_id] = [i for i in self.stack if i]
        self.stack.append(el_id)

    def handle_endtag(self, tag):
        if tag == "div" and self.stack:
            self.stack.pop()


@pytest.mark.parametrize("child,wrap", [
    ("sh-crons", "sh-crons-wrap"),
    ("sh-subagents", "sh-subagents-wrap"),
    ("delegation-chains-panel", "sh-subagents-wrap"),
    ("sh-heartbeat", "sh-heartbeat-wrap"),
    ("sh-channel-ingest", "sh-channel-ingest-wrap"),
    ("sh-gateway", "sh-gateway-wrap"),
])
def test_runtime_specific_section_is_wrapped(child, wrap):
    tree = _DivTree()
    tree.feed(_src(_OVERVIEW))
    assert wrap in tree.ancestors.get(child, []), f"#{child} is not inside #{wrap}"
    # A wrapper must not swallow the machine-wide disk card.
    assert wrap not in tree.ancestors.get("sh-disks", [])


def test_template_has_scope_note_and_services_label():
    html = _src(_OVERVIEW)
    assert 'id="sh-scope-note"' in html
    assert 'id="sh-services-label"' in html


# ── frontend: loadSystemHealth gates on declared capabilities ────────────────


def test_panel_gates_openclaw_only_checks():
    body = _function_body(_src(_APP_JS), "async function loadSystemHealth()")
    assert "_shRuntimeScope()" in body
    assert "scope.has('GATEWAY_RPC')" in body
    assert "services.filter" in body and "openclaw" in body
    assert "_shShow('sh-heartbeat-wrap', isOc)" in body
    assert "_shShow('sh-crons-wrap', scope.has('CRONS'))" in body
    assert "_shShow('sh-subagents-wrap', scope.has('SUBAGENTS'))" in body
    hb = body[body.index("Heartbeat status in system health"):body.index("/api/heartbeat-status")]
    assert "isOc" in hb, "heartbeat is fetched for runtimes that have none"
    ingest = body[body.index("Channel ingest (#1310"):body.index("Handler latency (#1283)")]
    assert "scope.has('CHANNELS')" in ingest
    gw = body[body.index("Gateway health (#852)"):body.index("Sandbox Status (conditional)")]
    assert "isOc" in gw
    for card in ("Inference Provider (conditional)", "Security Posture (conditional)"):
        seg = body[body.index(card):body.index(card) + 400]
        assert "has('GATEWAY_RPC')" in seg, card
    assert "?runtime=" in body


def test_sandbox_status_loader_does_not_reshow_openclaw_config_cards():
    # loadSandboxStatus writes the same inference/security cards from
    # openclaw.json; without the gate it re-shows them under Claude Code.
    body = _function_body(_src(_APP_JS), "async function loadSandboxStatus()")
    assert "d.inference && infEl && _shRuntimeScope().has('GATEWAY_RPC')" in body
    assert "d.security && secEl && _shRuntimeScope().has('GATEWAY_RPC')" in body


def test_subagent_card_never_invents_a_success_rate():
    body = _function_body(_src(_APP_JS), "async function loadSystemHealth()")
    seg = body[body.index("// Sub-agents"):body.index("Delegation chain panel")]
    assert "No finished runs" in seg
    assert "unavailable" in seg
    # The legacy cloud shape ({runs, successPct: 100}) has no completed count;
    # its percentage must not be rendered as measured.
    assert "typeof sa.completed === 'number'" in seg


def test_diagnostics_and_reliability_follow_the_switcher():
    src = _src(_APP_JS)
    assert "_shRuntimeScope()" in _function_body(src, "async function loadDiagnostics()")
    assert "_shRuntimeScope()" in _function_body(src, "async function _loadReliabilityWidget()")


def test_openclaw_heartbeat_cards_hide_under_other_runtimes():
    # "Is your agent alive?" and the header heartbeat card both read
    # OpenClaw's 30-minute HEARTBEAT_OK session (routes/overview.py).
    src = _src(_APP_JS)
    hb = _function_body(src, "async function loadHeartbeat()")
    assert "_shShow('heartbeat-panel', hbOc)" in hb
    assert hb.index("if (!hbOc) return;") < hb.index("/api/heartbeat")
    panel = _function_body(src, "async function loadSystemHealth()")
    assert "_shShow('heartbeat-panel', isOc)" in panel
    assert "_shShow('overview-heartbeat-card', false)" in panel
    html = _src(_OVERVIEW)
    render = html[html.index("window.renderOverviewHeartbeat"):html.index("function pollOnce")]
    assert "_shRuntimeScope().has('GATEWAY_RPC')" in render
    assert render.index("has('GATEWAY_RPC')") < render.index("card.style.display = 'flex'")


def test_runtime_switch_reloads_the_panel():
    body = _function_body(_src(_APP_JS), "function _cmApplyRuntimeSelection(val)")
    assert "loadSystemHealth()" in body


def test_every_shipped_runtime_has_a_capability_entry():
    # Burned 2026-09-15: muse_code, openworker, qm and replit had no entry, so
    # the sidebar showed them every tab (OpenClaw's crons and gateway tabs
    # included) and the hosted dashboard, which has no /api/agents override,
    # could not scope System Health for them.
    from clawmetry import entitlements
    block = re.search(r"var _CM_RT_CAPS = \{(.*?)\n\};", _src(_APP_JS), re.S).group(1)
    caps = {m.group(1): set(re.findall(r"'([A-Z_]+)'", m.group(2)))
            for m in re.finditer(r"^\s*(\w+):\s*\[(.*?)\]", block, re.M)}
    shipped = set(entitlements.FREE_RUNTIMES) | set(entitlements.PAID_RUNTIMES)
    missing = sorted(shipped - set(caps))
    assert not missing, f"runtimes with no _CM_RT_CAPS entry: {missing}"
    openclaw_only = {"GATEWAY_RPC", "CRONS", "CHANNELS"}
    leaks = {rt: sorted(c & openclaw_only) for rt, c in caps.items()
             if rt not in ("openclaw", "nemoclaw") and c & openclaw_only}
    assert not leaks, f"OpenClaw-only capabilities on another runtime: {leaks}"


def test_subagent_card_shows_real_runs_even_if_caps_map_lags():
    # The hosted dashboard only has the static _CM_RT_CAPS map; a runtime whose
    # adapter emits children must not have them hidden by a stale entry.
    body = _function_body(_src(_APP_JS), "async function loadSystemHealth()")
    assert "var showSa = scope.has('SUBAGENTS') || (typeof subagents.runs === 'number' && subagents.runs > 0);" in body
    assert "_shShow('sh-subagents-wrap', showSa);" in body
    assert "if (showSa) {" in body


def test_declared_caps_override_rerenders_system_health():
    body = _function_body(_src(_APP_JS), "async function _cmLoadDeclaredCaps()")
    changed = body[body.index("if (changed) {"):]
    assert "loadSystemHealth()" in changed


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_scope_resolves_from_declared_caps_under_node():
    src = _src(_APP_JS)
    caps = re.search(r"var _CM_RT_CAPS = \{.*?\n\};", src, re.S).group(0)
    scope_fn = _function_body(src, "function _shRuntimeScope()")
    script = caps + "\n" + scope_fn + """
var CURRENT;
function _cmRuntimeFilter() { return CURRENT; }
function _cmCapsForRuntime(rt) { return _CM_RT_CAPS[rt]; }
var out = {};
['all', 'openclaw', 'nemoclaw', 'claude_code', 'codex', 'not_a_runtime'].forEach(function (rt) {
  CURRENT = rt;
  var s = _shRuntimeScope();
  out[rt] = {gw: s.has('GATEWAY_RPC'), crons: s.has('CRONS'), sub: s.has('SUBAGENTS')};
});
console.log(JSON.stringify(out));
"""
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["all"] == {"gw": True, "crons": True, "sub": True}
    assert out["openclaw"]["gw"] and out["nemoclaw"]["gw"]
    assert out["claude_code"] == {"gw": False, "crons": False, "sub": True}
    # Codex emits Collab child threads as sub-agents (pro 0.7.28).
    assert out["codex"] == {"gw": False, "crons": False, "sub": True}
    # An unmapped runtime is not OpenClaw: it gets machine-wide checks only.
    assert out["not_a_runtime"] == {"gw": False, "crons": False, "sub": False}
