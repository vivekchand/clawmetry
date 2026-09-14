#!/usr/bin/env python3
"""Build and check the PR provenance demo repository (vivekchand/clawmetry#5946).

``build`` creates a scratch git repository where an agent commit writes a file
with a known SQL injection, a provenance bundle committed into the change the
way the pilot flow does it, a scanner SARIF with a finding on that file and on
a human-written file, and an exceptions file. The session metadata and Guard
finding in this bundle are FIXTURES (``generated_by`` says so); the store
export path is exercised for real by ``tests/test_pr_provenance.py``.

``verify`` asserts what a reviewer would see: the scanner finding on the agent
file carries the session, the one on the human file does not, the Guard
finding is an error-level result on the agent file, and the gate decision is
the expected one.

Used by ``.github/workflows/pr-provenance-action.yml`` to run the composite
action in ``integrations/github-action`` end to end.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from clawmetry import pr_provenance as pp  # noqa: E402

SESSION = "claude_code:demo-session-1"
CODEX_SESSION = "codex:demo-session-2"


def _git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="Demo", GIT_AUTHOR_EMAIL="demo@example.com",
               GIT_COMMITTER_NAME="Demo", GIT_COMMITTER_EMAIL="demo@example.com")
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def _write(repo, rel, text):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path) or repo, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build(out: str) -> dict:
    repo = os.path.join(out, "repo")
    os.makedirs(repo, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _write(repo, "README.md", "demo service\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    _write(repo, "app/db.py",
           "def find_user(cur, name):\n"
           "    return cur.execute(\"SELECT * FROM users WHERE name = '%s'\" % name)\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"feat: user lookup\n\nClawmetry-Session: {SESSION}")
    _write(repo, "app/util.py", "def slug(value):\n    return value.lower()\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: slug helper")
    _write(repo, "docs/notes.md", "Written by a human.\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs: notes")
    head = _git(repo, "rev-parse", "HEAD")

    commits = pp.git_commits(repo, base, head)
    changed = pp.git_changed_files(repo, base, head)
    links = pp.link_files(changed, commits, {CODEX_SESSION: {"app/util.py"}})
    bundle = pp.build_bundle(
        project="demo/service", base_sha=base, head_sha=head, commits=commits,
        changed_files=changed, links=links,
        sessions={SESSION: {"runtime": "claude_code", "models": ["claude-opus-5"],
                            "cost_usd": 0.61},
                  CODEX_SESSION: {"runtime": "codex", "models": ["gpt-5-codex"],
                                  "cost_usd": None}},
        incidents_by_session={SESSION: [{
            "signature": "daemon_detect_credential_access", "severity": "critical",
            "kind": "credential_access", "title": "read a cloud credentials file",
            "details": {"spend_at_risk_usd": 0.12, "spend_basis": "measured"}}]},
        generated_by="fixture: scripts/pr_provenance_demo.py")
    _write(repo, ".clawmetry/pr-provenance.json", json.dumps(bundle, indent=2) + "\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: provenance bundle")

    scanner = {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "Demo SAST", "rules": [
            {"id": "python.sql-injection", "shortDescription": {"text": "SQL injection"}}]}},
        "results": [
            {"ruleId": "python.sql-injection", "level": "error",
             "message": {"text": "User input is formatted into a SQL statement."},
             "locations": [{"physicalLocation": {"artifactLocation": {"uri": "app/db.py"},
                                                 "region": {"startLine": 2}}}]},
            {"ruleId": "python.sql-injection", "level": "warning",
             "message": {"text": "SQL mentioned in documentation."},
             "locations": [{"physicalLocation": {"artifactLocation": {"uri": "docs/notes.md"},
                                                 "region": {"startLine": 1}}}]},
        ]}]}
    scanner_path = os.path.join(out, "scanner.sarif")
    with open(scanner_path, "w", encoding="utf-8") as fh:
        json.dump(scanner, fh)
    exceptions_path = os.path.join(out, "exceptions.json")
    with open(exceptions_path, "w", encoding="utf-8") as fh:
        json.dump({"exceptions": [
            {"id": "DEMO-1", "rule": "clawmetry/guard/credential_access",
             "expires": "2999-01-01", "approved_by": "demo-security-owner",
             "reason": "fixture credentials in the demo"},
            {"id": "DEMO-2", "rule": "python.sql-injection", "path": "app/db.py",
             "expires": "2999-01-01", "approved_by": "demo-security-owner",
             "reason": "demo of an approved exception"}]}, fh)
    return {"repo": repo, "base": base, "scanner": scanner_path, "exceptions": exceptions_path}


def verify(sarif_path: str, report_path: str, expect_gate: str) -> None:
    with open(sarif_path, encoding="utf-8") as fh:
        sarif = json.load(fh)
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)
    assert sarif["version"] == "2.1.0", sarif.get("version")
    ours = sarif["runs"][0]
    scanner = next(r for r in sarif["runs"][1:] if r["tool"]["driver"]["name"] == "Demo SAST")

    guard = [r for r in ours["results"] if r["ruleId"] == "clawmetry/guard/credential_access"]
    assert guard, "no Guard result"
    assert {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] for r in guard} == {"app/db.py"}
    assert all(r["level"] == "error" for r in guard)

    by_uri = {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]: r
              for r in scanner["results"]}
    agent = by_uri["app/db.py"]["properties"]["clawmetry"]
    assert [p["session_id"] for p in agent] == [SESSION], agent
    assert agent[0]["basis"] == [pp.BASIS_TRAILER] and agent[0]["association_only"] is True
    assert "clawmetry" not in (by_uri["docs/notes.md"].get("properties") or {})
    assert "docs/notes.md" in ours["properties"]["clawmetry"]["unattributed_files"]

    gate = report["gate"]
    assert report["evidence"]["status"] == pp.EVIDENCE_OK, report["evidence"]
    assert gate["outcome"] == expect_gate, gate
    for key in ("rule_version", "actor", "decided_at", "head_sha"):
        assert gate.get(key), key
    if expect_gate == "pass":
        assert {e["id"] for e in gate["exceptions_applied"]} == {"DEMO-1", "DEMO-2"}, gate
    print(f"demo verified: gate={gate['outcome']}, scanner finding on app/db.py linked to {SESSION}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--sarif", required=True)
    v.add_argument("--report", required=True)
    v.add_argument("--expect-gate", required=True, choices=("disabled", "pass", "fail"))
    args = ap.parse_args(argv)
    if args.cmd == "build":
        info = build(os.path.abspath(args.out))
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a", encoding="utf-8") as fh:
                for k, val in info.items():
                    fh.write(f"{k}={val}\n")
        print(json.dumps(info, indent=2))
        return 0
    verify(args.sarif, args.report, args.expect_gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
