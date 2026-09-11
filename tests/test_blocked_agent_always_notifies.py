"""A blocked agent reaches a human with nothing configured.

Burned 2026-09-11: Claude Code's pre-tool hook ran ``python -m clawmetry`` from
a directory holding an older clawmetry checkout, argparse exited 2, and Claude
Code blocked every tool call for about six hours. The hook errors were ingested,
but ``blocked_on_user`` did not know a hook-rejected call meant "blocked",
nothing paged, and the only zero-config channel was a banner in a dashboard
nobody had open. These tests pin the three fixes:

* detection: hook errors with nothing succeeding after them are a blocked
  agent, critical when the failing hook is ClawMetry's own gate;
* delivery: urgent incidents also go to a desktop notification and, on a
  cloud-connected node, to cloud (which always emails the account owner);
* prevention: the ``-m`` hook fallback keeps the agent's cwd off sys.path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402
from clawmetry import hook_ownership  # noqa: E402
from clawmetry import incident_alerts as ia  # noqa: E402

_OWN = ("PreToolUse:Read hook error: [/Users/v/.clawmetry/bin/python3 -m "
        "clawmetry hook claude-code --base http://127.0.0.1:8900]: usage: "
        "clawmetry ... error: argument command: invalid choice: 'hook'")
_FOREIGN = ("PreToolUse:Bash hook error: [/opt/acme/guard.sh]: "
            "guard.sh: line 3: jq: command not found")


def _ts(i: int) -> str:
    return f"2026-09-11T01:{i // 60:02d}:{i % 60:02d}"


def _ev(et: str, data: dict, i: int) -> dict:
    return {"event_type": et, "ts": _ts(i), "data": data}


def _call(tool: str, i: int) -> dict:
    return _ev("tool_call", {"role": "assistant", "tool_name": tool,
                             "tool_calls": [{"name": tool, "input": {}}]}, i)


def _hook_err(text: str, i: int) -> dict:
    return _ev("tool_result", {"role": "tool", "content": text,
                               "extra": {"isError": True}}, i)


def _newest_first(*evs):
    return list(reversed(list(evs)))


# ── detection ────────────────────────────────────────────────────────────────

def test_own_gate_erroring_twice_is_critical_blocked_on_user():
    evs = _newest_first(_call("Read", 1), _hook_err(_OWN, 2),
                        _call("Bash", 3), _hook_err(_OWN, 4))
    inc = detectors.blocked_on_user(evs, "claude_code:s1", "claude_code",
                                    facts={"idle_seconds": 5})
    assert inc and inc["kind"] == "blocked_on_user"
    assert inc["severity"] == "critical"
    assert "ClawMetry's own gate" in inc["title"]
    assert inc["evidence"]["own_gate"] is True
    assert inc["evidence"]["hook_errors"] == 2
    assert inc["evidence"]["asked_via"] == "hook"


def test_foreign_hook_error_after_idle_is_a_warning():
    evs = _newest_first(_call("Bash", 1), _hook_err(_FOREIGN, 2))
    inc = detectors.blocked_on_user(evs, "claude_code:s2", "claude_code",
                                    facts={"idle_seconds": 600})
    assert inc and inc["severity"] == "warning"
    assert "failing hook" in inc["title"]
    assert inc["evidence"]["own_gate"] is False


def test_single_fresh_hook_error_is_not_yet_an_incident():
    evs = _newest_first(_call("Bash", 1), _hook_err(_FOREIGN, 2))
    assert detectors.blocked_on_user(evs, "s3", "claude_code",
                                     facts={"idle_seconds": 10}) is None


def test_a_successful_call_after_the_errors_means_it_recovered():
    evs = _newest_first(
        _call("Read", 1), _hook_err(_OWN, 2), _call("Read", 3), _hook_err(_OWN, 4),
        _call("Read", 5), _ev("tool_result", {"role": "tool", "content": "ok"}, 6))
    assert detectors.blocked_on_user(evs, "s4", "claude_code",
                                     facts={"idle_seconds": 9999}) is None


def test_a_human_reply_after_the_errors_clears_it():
    evs = _newest_first(
        _call("Read", 1), _hook_err(_OWN, 2), _call("Bash", 3), _hook_err(_OWN, 4),
        _ev("message", {"role": "user", "content": "fixed the hook"}, 5))
    assert detectors.blocked_on_user(evs, "s5", "claude_code",
                                     facts={"idle_seconds": 9999}) is None


def test_a_deliberate_hook_denial_is_not_a_blocked_agent():
    """A policy a person set that denies a call is a decision, not a fault."""
    denied = "Hook PreToolUse:Bash denied this tool call: rm -rf is not allowed"
    evs = _newest_first(_call("Bash", 1), _hook_err(denied, 2),
                        _call("Bash", 3), _hook_err(denied, 4))
    assert detectors.blocked_on_user(evs, "s6", "claude_code",
                                     facts={"idle_seconds": 9999}) is None


def test_run_all_surfaces_the_own_gate_incident():
    evs = _newest_first(_call("Read", 1), _hook_err(_OWN, 2),
                        _call("Bash", 3), _hook_err(_OWN, 4))
    kinds = [i["kind"] for i in detectors.run_all(evs, "claude_code:s7", "claude_code",
                                                  facts={"idle_seconds": 5})]
    assert "blocked_on_user" in kinds


# ── delivery ─────────────────────────────────────────────────────────────────

class _Latch:
    def __init__(self):
        self.sent = {}

    def incident_alert_last_sent(self, *, session_id, kind):
        return self.sent.get((session_id, kind), 0)

    def record_incident_alert(self, *, session_id, kind, delivered_via=None, severity=""):
        self.sent[(session_id, kind)] = int(time.time() * 1000)


@pytest.fixture
def quiet_sinks(monkeypatch, tmp_path):
    monkeypatch.setattr(ia, "_fleet_db_path", lambda: str(tmp_path / "fleet.db"))
    monkeypatch.setattr(ia, "_BUILTIN_PREFS_FILE", str(tmp_path / "prefs.json"))
    monkeypatch.setattr(ia, "_load_alerts_config", lambda: {})
    monkeypatch.setattr(ia, "_budget_config", lambda: {})
    monkeypatch.setattr(ia, "_MEMO", {})
    calls = {"desktop": [], "cloud": []}
    monkeypatch.setattr(ia, "send_desktop",
                        lambda t, m: calls["desktop"].append((t, m)) or True)
    monkeypatch.setattr(ia, "send_cloud",
                        lambda inc, m: calls["cloud"].append(inc["kind"]) or True)
    return calls


def _inc(kind, sev):
    return {"kind": kind, "session_id": "claude_code:s1", "runtime": "claude_code",
            "severity": sev, "title": "ClawMetry's own gate is blocking claude_code",
            "detail": "Every tool call is rejected.", "evidence": {}}


def test_a_blocked_agent_goes_to_desktop_and_cloud_with_nothing_configured(quiet_sinks):
    res = ia.deliver_incident(_Latch(), _inc("blocked_on_user", "warning"))
    assert res["delivered"] is True
    assert {"banner", "desktop", "cloud"} <= set(res["delivered_via"])
    assert quiet_sinks["cloud"] == ["blocked_on_user"]
    assert quiet_sinks["desktop"][0][0].startswith("ClawMetry: ")


def test_any_critical_incident_is_urgent(quiet_sinks):
    res = ia.deliver_incident(_Latch(), _inc("file_blast_radius", "critical"))
    assert {"desktop", "cloud"} <= set(res["delivered_via"])


def test_an_ordinary_warning_does_not_pop_up_or_email(quiet_sinks):
    res = ia.deliver_incident(_Latch(), _inc("network_egress", "warning"))
    assert res["delivered"] is True
    assert "desktop" not in res["delivered_via"]
    assert quiet_sinks["desktop"] == [] and quiet_sinks["cloud"] == []


def test_desktop_notification_passes_text_as_argv_not_script(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DESKTOP_ALERTS", "1")
    monkeypatch.setattr(ia.sys, "platform", "darwin")
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/" + name)
    seen = {}

    def fake_run(argv, **kw):
        seen["argv"] = argv
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    evil = 'x" & do shell script "rm -rf ~" & "'
    assert ia.send_desktop(evil, "body") is True
    script = " ".join(a for a in seen["argv"][:-2])
    assert "rm -rf" not in script, "incident text must never enter the AppleScript"
    assert seen["argv"][-2:] == [evil, "body"]


def test_desktop_is_off_by_env(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DESKTOP_ALERTS", "0")
    assert ia.send_desktop("t", "m") is False


def test_cloud_notice_posts_with_the_node_key(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CLOUD_INCIDENT_ALERTS", "1")
    from clawmetry import sync as _sync
    import clawmetry.config as _cfg
    monkeypatch.setattr(_cfg, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(_sync, "load_config",
                        lambda: {"api_key": "cm_test", "node_id": "mac-1"})
    monkeypatch.setattr(_sync, "INGEST_URL", "https://ingest.example")
    seen = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true, "dispatched": ["email:owner"]}'

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        seen["auth"] = req.get_header("Authorization")
        seen["body"] = json.loads(req.data)
        return _Resp()

    monkeypatch.setattr(ia.urllib.request, "urlopen", fake_urlopen)
    assert ia.send_cloud(_inc("blocked_on_user", "critical"), "msg") is True
    assert seen["url"] == "https://ingest.example/api/cloud/incidents/notify"
    assert seen["auth"] == "Bearer cm_test"
    assert seen["body"]["node_id"] == "mac-1"
    assert seen["body"]["kind"] == "blocked_on_user"


def test_cloud_notice_needs_a_connected_node(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CLOUD_INCIDENT_ALERTS", "1")
    from clawmetry import sync as _sync
    import clawmetry.config as _cfg
    monkeypatch.setattr(_cfg, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(_sync, "load_config", lambda: {"api_key": "", "node_id": "x"})

    def boom(*a, **k):
        raise AssertionError("no network for a local-only node")

    monkeypatch.setattr(ia.urllib.request, "urlopen", boom)
    assert ia.send_cloud(_inc("blocked_on_user", "critical"), "msg") is False


# ── prevention ───────────────────────────────────────────────────────────────

def test_module_launch_flags_by_interpreter():
    assert hook_ownership.module_launch_flags((3, 12)) == "-P"
    assert hook_ownership.module_launch_flags((3, 9), user_site_install=False) == "-I"
    assert hook_ownership.module_launch_flags((3, 9), user_site_install=True) == ""


def test_dash_m_fallback_is_isolated_in_both_gates(monkeypatch, tmp_path):
    import clawmetry.claude_code_gate as ccg
    import clawmetry.runtime_gates as rg
    bindir = tmp_path / "nolauncher" / "bin"
    bindir.mkdir(parents=True)
    for mod in (ccg, rg):
        monkeypatch.setattr(mod.sys, "executable", str(bindir / "python3"))
    flags = hook_ownership.module_launch_flags()
    want = f" {flags} -m clawmetry hook " if flags else " -m clawmetry hook "
    assert want in ccg._hook_command("http://127.0.0.1:8900")
    assert want in rg._hook_command("cursor", "http://127.0.0.1:8900")


@pytest.mark.skipif(sys.version_info < (3, 11), reason="-P needs Python 3.11")
def test_dash_P_really_ignores_a_shadowing_checkout_in_cwd(tmp_path):
    """The actual failure, reproduced: a ``clawmetry/`` folder in the agent's
    working directory. With ``-P`` the import still resolves to the real one."""
    shadow = tmp_path / "clawmetry"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("SHADOW = True\n")
    env = dict(os.environ, PYTHONPATH=_REPO_ROOT)
    out = subprocess.run(
        [sys.executable, "-P", "-c",
         "import clawmetry; print(getattr(clawmetry, 'SHADOW', False))"],
        cwd=str(tmp_path), env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"
