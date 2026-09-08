"""Guard knows the two workspace kinds, and cannot silently act on them.

``repo_scan`` emits ``repo_config_exec`` and ``agent_config_tamper`` in the same
shape as every detector incident. They bypassed ``DETECTOR_KINDS`` (which exists
so a new detector cannot be added without the surfaces that render it noticing)
because they live outside ``detectors``, and every Guard surface rendered them
as their raw id.

Four properties are pinned here:

* one list, not two that drift: ``ALL_INCIDENT_KINDS`` is the union, every
  renderable kind has plain-words copy, and the policy form is BUILT from that
  copy rather than re-typed;
* a policy must NAME a workspace kind to act on it. ``trigger_kind: ""`` means
  any signal about the agent, so a standing "pause anything critical" rule
  cannot start pausing sessions over a property of a checkout;
* the daemon still hands workspace findings to the policy pass (that is what
  makes a named policy possible at all);
* a workspace finding is reachable in the Guard list: it carries no spend, so
  the money ranking would bury it, and it sorts on its own axis instead of
  being given an invented dollar figure.
"""
from __future__ import annotations

import os
import re
import sys
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import routes.guard as guard  # noqa: E402
from clawmetry import detectors as _det  # noqa: E402
from clawmetry import policy_engine as pe  # noqa: E402
from clawmetry import repo_scan as _rs  # noqa: E402
from clawmetry import sync as _sync  # noqa: E402

_APP_JS = os.path.join(_REPO_ROOT, "clawmetry", "static", "js", "app.js")


def _js() -> str:
    with open(_APP_JS, encoding="utf-8") as fh:
        return fh.read()


def _js_map(name: str) -> dict:
    """Parse a `var NAME = { key: 'value', ... };` literal out of app.js."""
    src = _js()
    start = src.index("var " + name + " = {")
    end = src.index("};", start)
    body = src[start:end]
    return dict(re.findall(r"^\s*([a-z_]+)\s*:\s*'([^']*)'", body, re.M))


# ── one list ───────────────────────────────────────────────────────────────
def test_the_union_is_the_two_halves():
    assert _det.WORKSPACE_KINDS == _rs.WORKSPACE_KINDS
    assert _det.ALL_INCIDENT_KINDS == _det.DETECTOR_KINDS + _det.WORKSPACE_KINDS
    assert set(_det.DETECTOR_KINDS).isdisjoint(_det.WORKSPACE_KINDS)


def test_repo_scan_emits_only_declared_kinds(tmp_path):
    ws = tmp_path / "repo"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text("[core]\n\tfsmonitor = /tmp/x.sh\n",
                                        encoding="utf-8")
    (ws / ".claude").mkdir()
    (ws / ".claude" / "settings.json").write_text(
        '{"hooks": {"PreToolUse": [{"hooks": [{"command": "/tmp/y.sh"}]}]}}',
        encoding="utf-8")
    kinds = {f["kind"] for f in _rs.scan_workspace(str(ws))}
    assert kinds, "fixture should trip both scanners"
    assert kinds <= set(_rs.WORKSPACE_KINDS), f"undeclared kind emitted: {kinds}"


@pytest.mark.parametrize("kind", _det.ALL_INCIDENT_KINDS)
def test_every_kind_has_plain_words_in_the_guard_tab(kind):
    """The whole point of the union: a kind the product can emit cannot reach
    a screen as its raw id."""
    assert kind in _js_map("GUARD_KIND_LABEL"), (
        f"{kind} renders as its raw id in the Guard tab; add it to "
        f"GUARD_KIND_LABEL in app.js")


@pytest.mark.parametrize("kind", _det.ALL_INCIDENT_KINDS)
def test_every_kind_has_plain_words_in_the_alerts_feed(kind):
    assert kind in _js_map("LOOP_KIND_LABEL"), (
        f"{kind} renders as its raw id in the alerts feed; add it to "
        f"LOOP_KIND_LABEL in app.js")


def test_the_policy_form_is_built_from_the_label_map():
    """A second hand-kept list is how a kind ends up renderable but not
    selectable, which is exactly how these two stayed invisible."""
    src = _js()
    assert "guardKindOptions()" in src
    for kind in _det.DETECTOR_KINDS:
        assert "'<option value=\"%s\">" % kind not in src, (
            f"the policy form re-types {kind}; build the options from "
            f"GUARD_KIND_LABEL instead")


def test_the_js_workspace_list_matches_python():
    src = _js()
    listed = re.search(r"var GUARD_WORKSPACE_KINDS = \[([^\]]*)\]", src).group(1)
    got = tuple(re.findall(r"'([a-z_]+)'", listed))
    assert got == _rs.WORKSPACE_KINDS


# ── a policy must name it ──────────────────────────────────────────────────
def _incident(kind, severity="critical"):
    return {"kind": kind, "session_id": "cursor:1", "runtime": "cursor",
            "severity": severity, "title": "t", "detail": "d", "evidence": {},
            "spend_at_risk_usd": 0.0, "spend_basis": "unknown"}


def _policy(trigger_kind="", action="pause"):
    return {"policy_id": "p1", "enabled": True, "scope_runtime": "",
            "scope_agent_id": "", "trigger_kind": trigger_kind,
            "min_severity": "warning", "min_repeat": 0, "min_duration_s": 0,
            "min_spend_usd": 0, "min_spend_at_risk_usd": 0, "action": action}


_FACTS = {"cursor:1": {"cost_usd": 1.0, "bad_for_seconds": 999,
                       "runtime": "cursor", "cwd": "/w", "agent_id": "main"}}


@pytest.mark.parametrize("kind", _rs.WORKSPACE_KINDS)
def test_any_signal_does_not_match_a_workspace_finding(kind):
    """The burn this prevents: one preset with no condition paused everything
    on the node. A rule written about runaway agents must not silently acquire
    a new meaning because a scanner started emitting critical findings."""
    assert pe.evaluate([_incident(kind)], [_policy("")], _FACTS) == []


@pytest.mark.parametrize("kind", _rs.WORKSPACE_KINDS)
def test_a_policy_that_names_the_kind_matches(kind):
    decisions = pe.evaluate([_incident(kind)], [_policy(kind)], _FACTS)
    assert [d["kind"] for d in decisions] == [kind]
    assert decisions[0]["action"] == "pause"


def test_any_signal_still_matches_a_detector_kind():
    """The exclusion must be surgical: catch-all rules keep working."""
    decisions = pe.evaluate([_incident("stuck_loop")], [_policy("")], _FACTS)
    assert [d["kind"] for d in decisions] == ["stuck_loop"]


# ── the daemon hands them to the policy pass ───────────────────────────────
class _EmitStore:
    def __init__(self, cwd):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        self.row = {"session_id": "cursor:abc", "agent_type": "cursor",
                    "started_at": now_iso, "last_active_at": now_iso,
                    "status": "active", "cost_usd": 1.0, "cwd": cwd,
                    "metadata": {}}

    def query_sessions_table(self, limit=300):
        return [self.row]

    def query_events(self, **kw):
        return [{"event_type": "tool_call", "ts": self.row["started_at"],
                 "data": {"tool": "x"}}]

    def query_approvals(self, **kw):
        return []

    def ingest_loop_signal(self, **kw):
        return None

    def __getattr__(self, name):
        return lambda *a, **k: None


def test_workspace_findings_reach_the_policy_pass(tmp_path, monkeypatch):
    ws = tmp_path / "repo"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text("[core]\n\tfsmonitor = /tmp/x.sh\n",
                                        encoding="utf-8")
    monkeypatch.setattr(_det, "run_all", lambda *a, **k: [])
    monkeypatch.setattr(_sync, "_record_guard_observation", lambda *a, **k: None)
    seen = []
    monkeypatch.setattr(_sync, "_apply_guard_policies",
                        lambda store, state, incs, facts: seen.append(
                            [i["kind"] for i in incs]))
    _sync._emit_detector_incidents(_EmitStore(str(ws)), {})
    assert seen == [["repo_config_exec"]], (
        "a named policy cannot fire on a finding the pass never sees")


# ── reachable in the list ──────────────────────────────────────────────────
@pytest.fixture()
def client():
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    return app.test_client()


def _sig(sid, kind, sev, spend):
    return {"session_id": sid, "signature": "daemon_detect_" + kind,
            "severity": sev, "repeat_count": 3, "first_seen": None,
            "details": {"kind": kind, "message": kind, "detail": "d",
                        "spend_at_risk_usd": spend, "spend_basis":
                        "burn_rate" if spend else "unknown", "evidence": {}}}


@pytest.fixture()
def rows(monkeypatch, client):
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    sessions = [
        {"session_id": "cursor:rich", "status": "active", "cost_usd": 200.0,
         "started_at": now_iso, "last_active_at": now_iso, "metadata": {}},
        {"session_id": "cursor:poisoned", "status": "active", "cost_usd": 0.0,
         "started_at": now_iso, "last_active_at": now_iso, "metadata": {},
         "cwd": "/w/poisoned"},
    ]
    signals = [_sig("cursor:rich", "stuck_loop", "warning", 170.0),
               _sig("cursor:poisoned", "repo_config_exec", "critical", 0.0)]
    monkeypatch.setattr(guard, "_ls_call", lambda m, **kw: (
        sessions if m == "query_sessions_table"
        else signals if m == "query_recent_loop_signals" else None))
    monkeypatch.setattr(guard, "_live_only_rows", lambda out: [])
    monkeypatch.setattr(guard, "_runtime_supports_signals", lambda *a, **k: {
        "controllable": True, "reason": "", "state": "controllable",
        "actions": ["pause", "stop", "kill"], "no_pause": False})
    return client.get("/api/guard/sessions").get_json()


def test_the_workspace_finding_is_its_own_field(rows):
    by_id = {r["session_id"]: r for r in rows["sessions"]}
    poisoned = by_id["cursor:poisoned"]
    assert poisoned["workspace"]["kind"] == "repo_config_exec"
    # Not ranked against money: it does not displace the behavioural incident.
    assert poisoned["incident"] is None
    assert by_id["cursor:rich"]["workspace"] is None
    assert by_id["cursor:rich"]["incident"]["kind"] == "stuck_loop"


def test_a_poisoned_checkout_sorts_above_an_expensive_loop(rows):
    """It is not more expensive. It is uncosted and irreversible, and burying
    it under every spending session would make it unreachable. The alternative
    was to invent a dollar figure so it would sort well, which is the thing
    ``annotate_spend`` refuses to do."""
    assert [r["session_id"] for r in rows["sessions"]][0] == "cursor:poisoned"


def test_it_counts_as_flagged(rows):
    assert rows["flagged"] == 2
    # ...but contributes no money to the headline, because none is known.
    assert rows["spend_at_risk_usd"] == 170.0


def test_the_row_cwd_comes_from_the_column(rows):
    by_id = {r["session_id"]: r for r in rows["sessions"]}
    assert by_id["cursor:poisoned"]["cwd"] == "/w/poisoned"
