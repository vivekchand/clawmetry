"""The ``untrusted_package_source`` Guard detector (vivekchand/clawmetry-pro#242).

CVE-2026-59176 (functype-mcp-server): an MCP tool took a ``version`` string,
installed ``functype@<version>`` and imported it, so ``file:/tmp/evil`` ran
attacker code in the server. These tests pin that the argument is read, that
ordinary versions stay quiet, and that the severity follows where the source
points (recognition, not suppression).
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402
from clawmetry import framework_map as fm  # noqa: E402
from clawmetry import policy_engine as pe  # noqa: E402
from clawmetry.detector_package_source import classify_spec  # noqa: E402

SID = "claude_code:pkg-src-test"
KIND = "untrusted_package_source"


def _call(tool, args, n):
    return {"event_type": "tool_call", "ts": f"2026-09-30T09:00:{n:02d}",
            "data": {"tool": tool, "args": args}}


def _newest_first(chrono):
    return list(reversed(chrono))


def _run(chrono, facts=None):
    return detectors.untrusted_package_source(_newest_first(chrono), SID, "claude_code",
                                              facts=facts)


def test_fires_on_the_cve_2026_59176_shape():
    inc = _run([_call("mcp__functype__set_functype_version", {"version": "file:/tmp/evil-pkg"}, 1),
                _call("mcp__functype__get_docs", {"symbol": "Option"}, 2)])
    assert inc and inc["kind"] == KIND
    assert inc["severity"] == "critical"
    hit = inc["evidence"]["hits"][0]
    assert hit == {"tool": "mcp__functype__set_functype_version", "arg": "version",
                   "source": "local", "where": "/tmp/evil-pkg", "why": "a temporary directory"}
    assert "CVE-2026-59176" in inc["detail"]
    assert inc["first_bad_step"] == 0


def test_quiet_on_versions_tags_and_shas():
    for v in ("^3.2.0", "~1.4", "3.2.0", "latest", "next", "beta", ">=1 <2",
              "1.2.3 - 2.0.0", "3f2a9c1d4e5b6a7c", "*", "", "workspace:*"):
        assert _run([_call("mcp__pkg__set_version", {"version": v}, 1)]) is None, v
    # A name, a scoped name with a range, and a path under a non-spec key.
    assert _run([_call("mcp__pkg__add", {"package": "@types/node@^20"}, 1),
                 _call("Read", {"file_path": "/tmp/notes.txt"}, 2),
                 _call("Bash", {"command": "npm i file:/tmp/x"}, 3)]) is None


def test_every_source_shape_is_recognised():
    cases = {
        "file:/tmp/evil": "local", "functype@file:/tmp/evil": "local",
        "link:../x": "local", "./vendor/x": "local", "../x": "local",
        "npm:evil@1.0": "alias", "git+ssh://git@github.com/a/b.git": "git",
        "github:a/b": "git", "a/b#main": "git",
        "https://evil.example/x.tgz": "url",
    }
    for spec, want in cases.items():
        got = classify_spec(spec, version_key=True)
        assert got and got["source"] == want, (spec, got)


def test_github_shorthand_only_counts_under_a_version_key():
    assert classify_spec("acme/tools", version_key=False) is None
    assert classify_spec("acme/tools", version_key=True)["source"] == "git"


def test_a_pinned_internal_source_is_a_named_warning_not_silence():
    inc = _run([_call("mcp__deps__install",
                      {"dependencies": [{"name": "core", "spec": "git+ssh://git@git.acme.io/core.git#v2"}]}, 1)])
    assert inc and inc["severity"] == "warning"
    assert inc["evidence"]["hits"][0]["where"] == "git.acme.io"


def test_url_credentials_never_reach_the_finding():
    inc = _run([_call("mcp__deps__install",
                      {"packageSpec": "https://bob:s3cr3t-token@pkgs.example/x.tgz"}, 1)])
    assert inc and inc["evidence"]["hits"][0]["where"] == "pkgs.example"
    assert "s3cr3t" not in json.dumps(inc)


def test_a_path_outside_the_working_directory_is_critical():
    chrono = [_call("mcp__deps__install", {"version": "file:/opt/elsewhere/pkg"}, 1)]
    assert _run(chrono, {"cwd": "/work/repo"})["severity"] == "critical"
    # Inside the workspace it is a deliberate local package: a warning.
    inside = [_call("mcp__deps__install", {"version": "file:/work/repo/packages/core"}, 1)]
    assert _run(inside, {"cwd": "/work/repo"})["severity"] == "warning"
    # With no cwd there is nothing to compare against: a warning.
    assert _run(chrono)["severity"] == "warning"


def test_arguments_sent_as_a_json_string_are_read():
    ev = {"event_type": "assistant", "ts": "2026-09-30T09:00:01",
          "data": {"tool_calls": [{"function": {"name": "set_version",
                                                "arguments": json.dumps({"version": "file:/tmp/x"})}}]}}
    inc = detectors.untrusted_package_source([ev], SID, "codex")
    assert inc and inc["severity"] == "critical"


def test_never_raises_on_junk():
    junk = [None, 3, {"event_type": "tool_call", "data": "x{"},
            {"event_type": "tool_call", "data": {"tool": "t", "args": {"version": object()}}},
            {"event_type": "tool_call", "data": {"tool": "t", "args": {"version": "x" * 5000}}}]
    assert detectors.untrusted_package_source(junk, SID, "claude_code") is None


def test_a_policy_can_act_on_it():
    inc = _run([_call("mcp__functype__set_functype_version", {"version": "file:/tmp/evil-pkg"}, 1)])
    policy = {"policy_id": "p-pkg", "name": "stop on untrusted package", "enabled": True,
              "trigger_kind": KIND, "action": "stop", "min_severity": "critical"}
    decisions = pe.evaluate([inc], [policy])
    assert len(decisions) == 1 and decisions[0]["kind"] == KIND


def test_run_all_emits_it_with_framework_references():
    chrono = [_call("mcp__functype__set_functype_version", {"version": "file:/tmp/evil-pkg"}, 1)]
    found = [i for i in detectors.run_all(_newest_first(chrono), SID, "claude_code")
             if i["kind"] == KIND]
    assert len(found) == 1
    tags = found[0]["frameworks"]
    assert tags == fm.framework_tags(KIND)
    assert tags["owasp_asi"] == ["ASI02", "ASI04", "ASI05"]
    assert KIND in detectors.DETECTOR_KINDS
