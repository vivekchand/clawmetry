"""PR provenance report: agent sessions on changed files, as SARIF, with an
opt-in CI gate (vivekchand/clawmetry#5946).

Requirement: https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/4e224b46-71a6-4d32-933d-7fb6bfde30d0

The demo is a real one: a scratch git repository where an agent session
writes a file with a known issue, a real DuckDB store holding that session's
events and a Guard finding, a bundle exported from that store, and the CLI
run from the bundle alone with the network blocked and the store unreachable,
which is exactly what a CI runner has.

* AC-OBS-PRP-001.1 -- changed files linked with basis, unattributed listed:
  ``test_links_carry_basis_and_unattributed_files_are_listed``,
  ``test_demo_repo_store_export_then_ci_run_from_bundle``.
* AC-OBS-PRP-001.2 -- association, basis on every link and annotation:
  ``test_every_annotation_says_association_and_carries_basis``.
* AC-OBS-PRP-001.3 -- Guard findings as SARIF results on linked files:
  ``test_demo_repo_store_export_then_ci_run_from_bundle``,
  ``test_guard_severity_maps_to_sarif_level``.
* AC-OBS-PRP-001.4 -- scanner findings annotated only on linked files:
  ``test_demo_repo_store_export_then_ci_run_from_bundle``,
  ``test_scanner_findings_on_unlinked_files_stay_unannotated``.
* AC-OBS-PRP-001.5 -- no prompt, no tool output, no credential in outputs:
  ``test_demo_repo_store_export_then_ci_run_from_bundle``.
* AC-OBS-PRP-001.6 -- from a bundle with no store and no network, and from
  the store: ``test_demo_repo_store_export_then_ci_run_from_bundle``.
* AC-OBS-PRP-001.7 -- digest, substitution, missing commits:
  ``test_tampered_bundle_is_invalid_evidence``,
  ``test_bundle_from_another_change_is_invalid_evidence``,
  ``test_uncovered_commits_and_stale_bundles_are_reported``,
  ``test_committed_bundle_gate_behaviours_end_to_end``.
* AC-OBS-PRP-001.8 -- off by default; enabled needs an evidence behaviour:
  ``test_gate_is_off_unless_enabled_even_with_a_critical_finding``,
  ``test_gate_refuses_to_run_without_an_evidence_behaviour``.
* AC-OBS-PRP-001.9 -- threshold, live and expired exceptions:
  ``test_gate_threshold_and_exceptions``,
  ``test_committed_bundle_gate_behaviours_end_to_end``.
* AC-OBS-PRP-001.10 -- decision records who, when, rule, head, exceptions:
  ``test_gate_decision_is_auditable``.
* AC-OBS-PRP-001.11 -- one pull-request comment, updated in place:
  ``test_pr_comment_is_created_once_then_updated``.
"""
from __future__ import annotations

import datetime as dt
import http.server
import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clawmetry import pr_provenance as pp  # noqa: E402

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
PROMPT_MARKER = "PROMPT-TEXT-MUST-NOT-LEAK"
TOOL_OUTPUT_MARKER = "TOOL-OUTPUT-MUST-NOT-LEAK"
FAKE_ANTHROPIC_KEY = "sk-ant-api03-" + "Q" * 40
FAKE_GITHUB_TOKEN = "ghp_" + "Z" * 36

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


# ── helpers ────────────────────────────────────────────────────────────────

def _git(repo, *args, env=None):
    full_env = dict(os.environ, GIT_AUTHOR_NAME="Dev", GIT_AUTHOR_EMAIL="dev@example.com",
                    GIT_COMMITTER_NAME="Dev", GIT_COMMITTER_EMAIL="dev@example.com",
                    GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    full_env.update(env or {})
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True, env=full_env).stdout.strip()


def _write(repo, rel, text):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _bundle(links, sessions=(), commits=(), head="h" * 40, base="b" * 40, generated_at=NOW):
    return pp.build_bundle(
        project="acme/demo", base_sha=base, head_sha=head, commits=list(commits),
        changed_files=list(links), links=links,
        sessions={s["session_id"]: s for s in sessions},
        incidents_by_session={s["session_id"]: s.get("incidents_raw", []) for s in sessions},
        generated_at=generated_at)


def _incident(kind="credential_access", severity="critical", title="read a credential file"):
    return {"signature": f"daemon_detect_{kind}", "severity": severity, "kind": kind,
            "title": title, "details": {"spend_at_risk_usd": 0.25, "spend_basis": "measured"}}


def _all_text(*paths):
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            out.append(fh.read())
    return "\n".join(out)


@pytest.fixture
def demo_repo(tmp_path):
    """A repository where one agent commit writes a known SQL injection."""
    repo = str(tmp_path / "demo")
    os.makedirs(repo)
    _git(repo, "init", "-q", "-b", "main")
    _write(repo, "README.md", "demo\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "app/db.py",
           "def find(cur, name):\n"
           "    return cur.execute(\"SELECT * FROM users WHERE name = '%s'\" % name)\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m",
         "feat: user lookup\n\nClawmetry-Session: claude_code:demo-1")
    _write(repo, "app/util.py", "def slug(x):\n    return x.lower()\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: slug helper")
    _write(repo, "docs/notes.md", "human notes\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs: notes")
    return {"repo": repo, "base": base, "head": _git(repo, "rev-parse", "HEAD")}


@pytest.fixture
def store(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "store.duckdb"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.LocalStore()
    yield st
    try:
        st.close()
    except Exception:
        pass


def _seed_store(st, repo):
    ts = (dt.datetime.now(UTC) - dt.timedelta(minutes=10)).isoformat()
    later = (dt.datetime.now(UTC) + dt.timedelta(hours=3)).isoformat()
    events = [
        {"id": "u1", "node_id": "n1", "session_id": "claude_code:demo-1",
         "agent_type": "claude_code", "event_type": "message", "ts": ts,
         "data": {"role": "user", "content": f"{PROMPT_MARKER} use key {FAKE_ANTHROPIC_KEY}"}},
        {"id": "w1", "node_id": "n1", "session_id": "claude_code:demo-1",
         "agent_type": "claude_code", "event_type": "tool_call", "ts": ts,
         "model": "claude-opus-5", "cost_usd": 0.5,
         "data": {"name": "Write", "input": {"file_path": os.path.join(repo, "app", "db.py"),
                                             "content": TOOL_OUTPUT_MARKER}}},
        {"id": "r1", "node_id": "n1", "session_id": "claude_code:demo-1",
         "agent_type": "claude_code", "event_type": "tool_result", "ts": ts,
         "data": {"content": TOOL_OUTPUT_MARKER}},
        # A read is not a write, and a write after the head commit is not in it.
        {"id": "rd", "node_id": "n1", "session_id": "claude_code:demo-1",
         "agent_type": "claude_code", "event_type": "tool_call", "ts": ts,
         "data": {"name": "Read", "input": {"file_path": os.path.join(repo, "docs", "notes.md")}}},
        {"id": "late", "node_id": "n1", "session_id": "claude_code:demo-1",
         "agent_type": "claude_code", "event_type": "tool_call", "ts": later,
         "data": {"name": "Edit", "input": {"file_path": os.path.join(repo, "docs", "notes.md")}}},
        {"id": "p2", "node_id": "n1", "session_id": "codex:demo-2", "agent_type": "codex",
         "event_type": "tool_call", "ts": ts, "model": "gpt-5-codex",
         "data": {"name": "apply_patch",
                  "input": "*** Begin Patch\n*** Add File: app/util.py\n+x\n*** End Patch\n"}},
    ]
    st.ingest_many(events)
    st.flush()
    st.ingest_loop_signal(
        "claude_code:demo-1", "daemon_detect_credential_access", 1, severity="critical",
        agent_type="claude_code",
        details={"kind": "credential_access", "spend_at_risk_usd": 0.42,
                 "spend_basis": "measured",
                 "message": f"read ~/.aws/credentials holding {FAKE_ANTHROPIC_KEY}"})


def _scanner_sarif(path):
    doc = {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "Semgrep OSS", "rules": [
            {"id": "python.sqli", "shortDescription": {"text": "SQL injection"}}]}},
        "results": [
            {"ruleId": "python.sqli", "level": "error",
             "message": {"text": f"User input in SQL; token seen {FAKE_GITHUB_TOKEN}"},
             "locations": [{"physicalLocation": {"artifactLocation": {"uri": "app/db.py"},
                                                 "region": {"startLine": 2}}}]},
            {"ruleId": "python.sqli", "level": "warning", "message": {"text": "docs mention"},
             "locations": [{"physicalLocation": {"artifactLocation": {"uri": "./docs/notes.md"},
                                                 "region": {"startLine": 1}}}]},
        ]}]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return path


@pytest.fixture
def no_network(monkeypatch):
    def _refuse(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)


# ── linking ────────────────────────────────────────────────────────────────

def test_links_carry_basis_and_unattributed_files_are_listed():
    commits = [{"sha": "c1", "session_id": "claude_code:s1", "files": ["a.py", "b.py"]},
               {"sha": "c2", "session_id": None, "files": ["c.md"]}]
    links = pp.link_files(["a.py", "b.py", "c.md", "d.py"], commits,
                          {"codex:s2": {"b.py", "d.py", "outside.py"}})
    assert links["a.py"] == [{"session_id": "claude_code:s1", "basis": pp.BASIS_TRAILER}]
    assert {"session_id": "codex:s2", "basis": pp.BASIS_WRITE} in links["b.py"]
    assert len(links["b.py"]) == 2
    assert links["c.md"] == []           # unattributed, not dropped
    assert links["d.py"] == [{"session_id": "codex:s2", "basis": pp.BASIS_WRITE}]
    assert "outside.py" not in links     # only files this change touched


def test_observed_writes_read_every_stored_shape(tmp_path):
    repo = str(tmp_path / "r")
    os.makedirs(repo)
    head = dt.datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    before, after = "2026-09-14T11:00:00+00:00", "2026-09-14T13:00:00+00:00"
    events = [
        {"event_type": "tool_call", "ts": before,
         "data": {"name": "Edit", "input": json.dumps({"file_path": os.path.join(repo, "a.py")})}},
        {"event_type": "assistant", "ts": before,
         "data": {"tool_calls": [{"name": "MultiEdit", "input": {"file_path": "b.py"}}]}},
        {"event_type": "message", "ts": before,
         "data": {"toolMetas": [{"name": "write_file", "input": {"path": "sub/c.py"}}]}},
        {"event_type": "message", "ts": before,
         "data": {"message": {"role": "assistant", "content": [
             {"type": "tool_use", "name": "apply_patch",
              "input": {"patch": "*** Update File: d.py\n@@\n-x\n+y\n"}}]}}},
        {"event_type": "tool_call", "ts": before,
         "data": {"name": "Write", "input": {"file_path": "/etc/passwd"}}},
        {"event_type": "tool_call", "ts": before,
         "data": {"name": "Read", "input": {"file_path": os.path.join(repo, "e.py")}}},
        {"event_type": "tool_call", "ts": after,
         "data": {"name": "Write", "input": {"file_path": os.path.join(repo, "f.py")}}},
    ]
    got = pp.observed_writes(events, repo, cwd=None, until=head)
    assert got == {"a.py", "b.py", "sub/c.py", "d.py"}
    # A relative path resolves against the session's working directory.
    assert pp.observed_writes(events[1:2], repo, cwd=os.path.join(repo, "pkg")) == {"pkg/b.py"}


# ── SARIF ──────────────────────────────────────────────────────────────────

def test_guard_severity_maps_to_sarif_level():
    assert pp.sarif_level("critical") == "error"
    assert pp.sarif_level("warning") == "warning"
    assert pp.sarif_level("info") == "note"
    links = {"a.py": [{"session_id": "claude_code:s1", "basis": pp.BASIS_WRITE}]}
    sess = [{"session_id": "claude_code:s1", "runtime": "claude_code", "models": ["m"],
             "cost_usd": 1.0, "incidents_raw": [_incident(severity="warning", kind="stuck_loop")]}]
    sarif = pp.to_sarif(_bundle(links, sess))
    guard = [r for r in sarif["runs"][0]["results"] if r["ruleId"] == "clawmetry/guard/stuck_loop"]
    assert guard and guard[0]["level"] == "warning"
    assert guard[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "a.py"


def test_every_annotation_says_association_and_carries_basis():
    links = {"a.py": [{"session_id": "claude_code:s1", "basis": pp.BASIS_TRAILER}], "b.py": []}
    sess = [{"session_id": "claude_code:s1", "runtime": "claude_code", "models": [],
             "cost_usd": None, "incidents_raw": [_incident()]}]
    bundle = _bundle(links, sess)
    scanner = {"runs": [{"tool": {"driver": {"name": "S"}}, "results": [
        {"ruleId": "r", "level": "error", "message": {"text": "m"},
         "locations": [{"physicalLocation": {"artifactLocation": {"uri": "a.py"}}}]}]}]}
    runs, annotated = pp.annotate_scanner_runs([scanner], bundle)
    sarif = pp.to_sarif(bundle, runs)
    results = sarif["runs"][0]["results"] + sarif["runs"][1]["results"]
    assert len(results) == 3
    for res in results:
        props = res["properties"]["clawmetry"]
        rows = props if isinstance(props, list) else [props]
        for row in rows:
            assert row["basis"] == [pp.BASIS_TRAILER]
            assert row["association_only"] is True
        assert "not proof of cause" in res["message"]["text"] or \
            "linked to this file by" in res["message"]["text"]
    md = pp.render_markdown(bundle, {"status": "ok"}, pp.evaluate_gate(
        bundle=bundle, evidence={"status": "ok"}), annotated)
    assert "association, not proof" in md
    assert "cost" in md and "unknown" in md   # an unknown cost is not rendered as $0.00


def test_scanner_findings_on_unlinked_files_stay_unannotated(tmp_path):
    links = {"a.py": [{"session_id": "codex:s1", "basis": pp.BASIS_WRITE}], "b.py": []}
    bundle = _bundle(links, [{"session_id": "codex:s1", "runtime": "codex", "models": [],
                              "cost_usd": 0.1}])
    doc = json.load(open(_scanner_sarif(str(tmp_path / "s.sarif"))))
    doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] = "b.py"
    runs, annotated = pp.annotate_scanner_runs([doc], bundle)
    assert annotated == []
    assert all("clawmetry" not in (r.get("properties") or {}) for r in runs[0]["results"])
    assert len(runs[0]["results"]) == 2      # reproduced, not dropped
    # The only ClawMetry results are provenance notes and Guard findings:
    # nothing here judges code content.
    rule_ids = {r["ruleId"] for r in pp.to_sarif(bundle)["runs"][0]["results"]}
    assert rule_ids == {pp.PROVENANCE_RULE_ID}


# ── bundle evidence ────────────────────────────────────────────────────────

def _commits(*shas):
    return [{"sha": s, "session_id": None, "files": ["a.py"]} for s in shas]


def test_tampered_bundle_is_invalid_evidence():
    bundle = _bundle({"a.py": []}, commits=_commits("c1"))
    assert pp.verify_bundle(bundle) == (True, "")
    bundle["links"]["a.py"] = [{"session_id": "claude_code:forged", "basis": pp.BASIS_TRAILER}]
    ev = pp.assess_evidence(bundle, range_shas=["c1"], head_sha="c1")
    assert ev["status"] == pp.EVIDENCE_INVALID
    assert "digest" in ev["reason"]
    assert "not proof of authenticity" in ev["digest_note"]


def test_bundle_from_another_change_is_invalid_evidence():
    other = _bundle({"a.py": []}, commits=_commits("x1", "x2"))
    ev = pp.assess_evidence(other, range_shas=["c1", "c2"], head_sha="c2")
    assert ev["status"] == pp.EVIDENCE_INVALID
    assert "another change" in ev["reason"]


def test_uncovered_commits_and_stale_bundles_are_reported():
    bundle = _bundle({"a.py": []}, commits=_commits("c1"),
                     generated_at=NOW - dt.timedelta(hours=30))
    ev = pp.assess_evidence(bundle, range_shas=["c1", "c2"], head_sha="c2", now=NOW)
    assert ev["status"] == pp.EVIDENCE_PARTIAL and ev["uncovered"] == ["c2"]
    ev = pp.assess_evidence(bundle, range_shas=["c1"], head_sha="c1", now=NOW, max_age_hours=24)
    assert ev["status"] == pp.EVIDENCE_STALE
    ev = pp.assess_evidence(bundle, range_shas=["c1"], head_sha="c1", now=NOW, max_age_hours=48)
    assert ev["status"] == pp.EVIDENCE_OK
    assert pp.assess_evidence(None, range_shas=["c1"], head_sha="c1")["status"] == pp.EVIDENCE_MISSING


# ── gate ───────────────────────────────────────────────────────────────────

def _critical_bundle():
    links = {"app/db.py": [{"session_id": "claude_code:s1", "basis": pp.BASIS_TRAILER}]}
    return _bundle(links, [{"session_id": "claude_code:s1", "runtime": "claude_code",
                            "models": ["m"], "cost_usd": 1.0, "incidents_raw": [_incident()]}])


def test_gate_is_off_unless_enabled_even_with_a_critical_finding():
    decision = pp.evaluate_gate(bundle=_critical_bundle(), evidence={"status": "invalid"})
    assert decision["enabled"] is False
    assert decision["outcome"] == "disabled"


def test_gate_refuses_to_run_without_an_evidence_behaviour():
    with pytest.raises(pp.GateConfigError):
        pp.evaluate_gate(bundle=_critical_bundle(), evidence={"status": "ok"}, fail_on="critical")
    with pytest.raises(pp.GateConfigError):
        pp.evaluate_gate(bundle=_critical_bundle(), evidence={"status": "ok"},
                         fail_on="critical", on_missing_evidence="maybe")


def test_gate_threshold_and_exceptions():
    b = _critical_bundle()
    ok = {"status": "ok", "head_sha": "h"}
    assert pp.evaluate_gate(bundle=b, evidence=ok, fail_on="critical",
                            on_missing_evidence="fail", now=NOW)["outcome"] == "fail"
    live = {"id": "EX-1", "rule": "clawmetry/guard/credential_access", "path": "app/db.py",
            "expires": "2026-10-01", "approved_by": "sec-lead", "reason": "fixture creds"}
    d = pp.evaluate_gate(bundle=b, evidence=ok, fail_on="critical", on_missing_evidence="fail",
                         exceptions=[live], now=NOW)
    assert d["outcome"] == "pass"
    assert d["exceptions_applied"][0]["id"] == "EX-1"
    expired = dict(live, id="EX-0", expires="2026-09-01")
    d = pp.evaluate_gate(bundle=b, evidence=ok, fail_on="critical", on_missing_evidence="fail",
                         exceptions=[expired], now=NOW)
    assert d["outcome"] == "fail"
    assert [e["id"] for e in d["exceptions_expired"]] == ["EX-0"]
    assert d["exceptions_applied"] == []
    no_expiry = dict(live, id="EX-2", expires="")
    d = pp.evaluate_gate(bundle=b, evidence=ok, fail_on="critical", on_missing_evidence="fail",
                         exceptions=[no_expiry], now=NOW)
    assert d["outcome"] == "fail" and d["exceptions_rejected"][0]["id"] == "EX-2"
    # A warning-only change passes a critical gate and fails a warning gate.
    warn = _bundle({"a.py": [{"session_id": "codex:s", "basis": pp.BASIS_WRITE}]},
                   [{"session_id": "codex:s", "runtime": "codex", "models": [], "cost_usd": 0,
                     "incidents_raw": [_incident(severity="warning", kind="no_progress")]}])
    assert pp.evaluate_gate(bundle=warn, evidence=ok, fail_on="critical",
                            on_missing_evidence="fail")["outcome"] == "pass"
    assert pp.evaluate_gate(bundle=warn, evidence=ok, fail_on="warning",
                            on_missing_evidence="fail")["outcome"] == "fail"
    # Missing evidence does what the operator chose, and says so.
    partial = {"status": "partial", "reason": "1 commit(s) ... not covered", "head_sha": "h"}
    clean = _bundle({"a.py": []})
    assert pp.evaluate_gate(bundle=clean, evidence=partial, fail_on="critical",
                            on_missing_evidence="fail")["outcome"] == "fail"
    d = pp.evaluate_gate(bundle=clean, evidence=partial, fail_on="critical",
                         on_missing_evidence="pass")
    assert d["outcome"] == "pass" and "allowed by --on-missing-evidence pass" in d["reasons"][0]


def test_gate_decision_is_auditable():
    d = pp.evaluate_gate(bundle=_critical_bundle(), evidence={"status": "ok", "head_sha": "abc123"},
                         fail_on="critical", on_missing_evidence="fail", actor="ci-bot",
                         now=NOW)
    for key, want in (("outcome", "fail"), ("rule_version", pp.RULE_VERSION),
                      ("threshold", "critical"), ("evidence_behaviour", "fail"),
                      ("actor", "ci-bot"), ("decided_at", "2026-09-14T12:00:00Z"),
                      ("head_sha", "abc123")):
        assert d[key] == want, key
    assert d["exceptions_applied"] == [] and d["blocking"][0]["rule_id"] == \
        "clawmetry/guard/credential_access"


# ── pull-request comment ───────────────────────────────────────────────────

class _FakeGitHub(http.server.BaseHTTPRequestHandler):
    comments: list = []

    def log_message(self, *a):
        pass

    def _reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._reply(200, self.comments)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.comments.append({"id": len(self.comments) + 1, "body": payload["body"]})
        self._reply(201, self.comments[-1])

    def do_PATCH(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        cid = int(self.path.rsplit("/", 1)[-1])
        for c in self.comments:
            if c["id"] == cid:
                c["body"] = payload["body"]
        self._reply(200, {"id": cid})


def test_pr_comment_is_created_once_then_updated():
    _FakeGitHub.comments = [{"id": 99, "body": "an unrelated human comment"}]
    server = http.server.HTTPServer(("127.0.0.1", 0), _FakeGitHub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        api = f"http://127.0.0.1:{server.server_address[1]}"
        first = pp.upsert_pr_comment(repository="acme/demo", pr_number=7, token="t",
                                     body="one\n" + pp.COMMENT_MARKER, api_url=api)
        second = pp.upsert_pr_comment(repository="acme/demo", pr_number=7, token="t",
                                      body="two\n" + pp.COMMENT_MARKER, api_url=api)
    finally:
        server.shutdown()
    assert first["action"] == "created" and second["action"] == "updated"
    ours = [c for c in _FakeGitHub.comments if pp.COMMENT_MARKER in c["body"]]
    assert len(ours) == 1 and ours[0]["body"].startswith("two")
    assert len(_FakeGitHub.comments) == 2


# ── the user's repository is read, never written ───────────────────────────

@needs_git
def test_git_calls_go_through_the_read_only_chokepoint(demo_repo, monkeypatch):
    """CLAUDE.md: every git call against a repository the operator chose goes
    through git_outcomes' allowlist. The two subcommands added for this
    feature are read-only, and an option that writes a file is refused on
    every subcommand, including the ones that were already allowed."""
    from clawmetry import git_outcomes

    for bad in (("diff-tree", "--output=/tmp/x", "a", "b"), ("log", "--output=/tmp/x"),
                ("log", "--output", "/tmp/x"), ("diff", "a", "b"), ("fetch", "origin")):
        with pytest.raises(git_outcomes.UnsafeGitCommand):
            git_outcomes._assert_read_only(bad)
    git_outcomes._assert_read_only(("merge-base", "a", "b"))
    git_outcomes._assert_read_only(("diff-tree", "-r", "--output-indicator-new=+", "a", "b"))

    seen = []
    real = git_outcomes._git

    def spy(repo, *args, **kw):
        seen.append(args[0])
        return real(repo, *args, **kw)

    monkeypatch.setattr(git_outcomes, "_git", spy)
    repo, base, head = demo_repo["repo"], demo_repo["base"], demo_repo["head"]
    assert pp.git_changed_files(repo, base, head) == ["app/db.py", "app/util.py", "docs/notes.md"]
    assert len(pp.git_commits(repo, base, head)) == 3
    assert pp.git_rev_parse(repo, "HEAD") == head
    pp.git_project(repo)
    pp.git_default_base_ref(repo)
    assert {"merge-base", "diff-tree", "log", "rev-parse"} <= set(seen)
    assert set(seen) <= git_outcomes._READ_ONLY_SUBCOMMANDS


@needs_git
def test_an_inferred_empty_change_is_not_reported_as_a_pass(demo_repo, no_network, capsys,
                                                            monkeypatch, tmp_path):
    """With no --base, the base is the merge base with the default branch. On
    the default branch itself that is HEAD, the change is empty, and a gate
    over nothing would pass. The command refuses instead."""
    from clawmetry import cli
    import clawmetry.cli_cmds._common as common

    # This path reads the store: never let a test reach the machine's own.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    def _no_store():
        raise RuntimeError("no store in this test")
    monkeypatch.setattr(common, "get_read_store", _no_store)

    repo = demo_repo["repo"]
    assert cli.trace_main(["report", "--repo", repo]) == 0          # feature branch vs main
    assert "3 files" in capsys.readouterr().out
    _git(repo, "checkout", "-q", "main")
    assert cli.trace_main(["report", "--repo", repo, "--fail-on", "critical",
                           "--on-missing-evidence", "fail"]) == 2
    assert "Nothing to report" in capsys.readouterr().out


# ── the demo, end to end ───────────────────────────────────────────────────

@needs_git
def test_demo_repo_store_export_then_ci_run_from_bundle(demo_repo, store, tmp_path, monkeypatch):
    repo, base = demo_repo["repo"], demo_repo["base"]
    _seed_store(store, repo)

    # 1. On the developer's machine: read the store, export the bundle.
    commits = pp.git_commits(repo, base, demo_repo["head"])
    changed = pp.git_changed_files(repo, base, demo_repo["head"])
    assert changed == ["app/db.py", "app/util.py", "docs/notes.md"]
    links, meta, incidents = pp.collect_from_store(store, repo=repo, commits=commits,
                                                   changed_files=changed)
    assert {"session_id": "claude_code:demo-1", "basis": pp.BASIS_TRAILER} in links["app/db.py"]
    assert {"session_id": "claude_code:demo-1", "basis": pp.BASIS_WRITE} in links["app/db.py"]
    assert links["app/util.py"] == [{"session_id": "codex:demo-2", "basis": pp.BASIS_WRITE}]
    assert links["docs/notes.md"] == []   # read, and edited only after the head commit
    assert meta["claude_code:demo-1"]["cost_usd"] == pytest.approx(0.5)
    assert meta["codex:demo-2"]["cost_usd"] is None   # never priced: unknown, not zero
    bundle = pp.build_bundle(project="acme/demo", base_sha=base, head_sha=demo_repo["head"],
                             commits=commits, changed_files=changed, links=links, sessions=meta,
                             incidents_by_session=incidents)
    bundle_path = str(tmp_path / "provenance.json")
    with open(bundle_path, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh)

    # 2. On the CI runner: no store, no network, just the bundle.
    from clawmetry import cli
    import clawmetry.cli_cmds._common as common

    def _no_store():
        raise AssertionError("the CI path must not open a store")
    monkeypatch.setattr(common, "get_read_store", _no_store)
    for sock_attr in ("connect",):
        monkeypatch.setattr(socket.socket, sock_attr,
                            lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    sarif_out, md_out, js_out = (str(tmp_path / n) for n in ("out.sarif", "out.md", "out.json"))
    rc = cli.trace_main(["report", "--repo", repo, "--base", base, "--head", "HEAD",
                         "--bundle", bundle_path,
                         "--scanner-sarif", _scanner_sarif(str(tmp_path / "semgrep.sarif")),
                         "--sarif-out", sarif_out, "--markdown-out", md_out,
                         "--json-out", js_out])
    assert rc == 0   # a critical finding, but the gate was not enabled

    sarif = json.load(open(sarif_out))
    assert sarif["version"] == "2.1.0" and len(sarif["runs"]) == 2
    ours, semgrep = sarif["runs"]
    by_rule = {}
    for res in ours["results"]:
        uri = res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        by_rule.setdefault(res["ruleId"], []).append((uri, res))
    guard = by_rule["clawmetry/guard/credential_access"]
    # One result for one finding on one file, carrying both bases: the commit
    # names the session AND its own write was observed.
    assert [u for u, _ in guard] == ["app/db.py"]
    assert guard[0][1]["level"] == "error"
    props = guard[0][1]["properties"]["clawmetry"]
    assert props["session_id"] == "claude_code:demo-1"
    assert sorted(props["basis"]) == sorted([pp.BASIS_TRAILER, pp.BASIS_WRITE])
    assert "docs/notes.md" in ours["properties"]["clawmetry"]["unattributed_files"]
    assert ours["properties"]["clawmetry"]["evidence"]["status"] == pp.EVIDENCE_OK
    assert ours["properties"]["clawmetry"]["gate"]["outcome"] == "disabled"

    db_finding, notes_finding = semgrep["results"]
    assert semgrep["tool"]["driver"]["name"] == "Semgrep OSS"
    sessions = {p["session_id"] for p in db_finding["properties"]["clawmetry"]}
    assert sessions == {"claude_code:demo-1"}
    assert "clawmetry" not in (notes_finding.get("properties") or {})

    everything = _all_text(sarif_out, md_out, js_out)
    for leak in (PROMPT_MARKER, TOOL_OUTPUT_MARKER, FAKE_ANTHROPIC_KEY, FAKE_GITHUB_TOKEN):
        assert leak not in everything, leak
    with open(bundle_path, encoding="utf-8") as fh:
        exported = fh.read()
    for leak in (PROMPT_MARKER, TOOL_OUTPUT_MARKER, FAKE_ANTHROPIC_KEY, str(tmp_path)):
        assert leak not in exported, leak


@needs_git
def test_committed_bundle_gate_behaviours_end_to_end(demo_repo, tmp_path, no_network):
    """The pilot flow: the developer commits the bundle into the change, CI
    gates on it. A known critical finding blocks only when the gate is on;
    an approved exception passes; an expired one does not; a bundle that
    predates a later commit is missing evidence, handled as configured."""
    from clawmetry import cli

    repo, base = demo_repo["repo"], demo_repo["base"]
    commits = pp.git_commits(repo, base, demo_repo["head"])
    changed = pp.git_changed_files(repo, base, demo_repo["head"])
    links = pp.link_files(changed, commits, {})
    bundle = pp.build_bundle(
        project="acme/demo", base_sha=base, head_sha=demo_repo["head"], commits=commits,
        changed_files=changed, links=links,
        sessions={"claude_code:demo-1": {"runtime": "claude_code", "models": ["m"],
                                         "cost_usd": 0.5}},
        incidents_by_session={"claude_code:demo-1": [_incident()]})
    rel = ".clawmetry/pr-provenance.json"
    _write(repo, rel, json.dumps(bundle))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: provenance bundle")
    bundle_path = os.path.join(repo, rel)
    ex_path = str(tmp_path / "exceptions.json")

    def run(*extra):
        return cli.trace_main(["report", "--repo", repo, "--base", base,
                               "--bundle", bundle_path, "--json-out",
                               str(tmp_path / "r.json"), *extra])

    def gate():
        return json.load(open(str(tmp_path / "r.json")))["gate"]

    assert run() == 0
    assert run("--fail-on", "critical") == 2      # no evidence behaviour chosen
    assert run("--fail-on", "critical", "--on-missing-evidence", "fail") == 1
    assert gate()["evidence_status"] == pp.EVIDENCE_OK   # the bundle's own commit is not missing

    with open(ex_path, "w") as fh:
        json.dump({"exceptions": [{"id": "EX-7", "rule": "clawmetry/guard/credential_access",
                                   "expires": "2999-01-01", "approved_by": "sec-lead",
                                   "reason": "fixture"}]}, fh)
    assert run("--fail-on", "critical", "--on-missing-evidence", "fail",
               "--exceptions", ex_path, "--actor", "ci-bot") == 0
    assert gate()["exceptions_applied"][0]["id"] == "EX-7" and gate()["actor"] == "ci-bot"

    with open(ex_path, "w") as fh:
        json.dump({"exceptions": [{"id": "EX-7", "rule": "clawmetry/guard/credential_access",
                                   "expires": "2001-01-01", "approved_by": "sec-lead",
                                   "reason": "fixture"}]}, fh)
    assert run("--fail-on", "critical", "--on-missing-evidence", "fail",
               "--exceptions", ex_path) == 1
    assert gate()["exceptions_expired"][0]["id"] == "EX-7"

    # A commit after the export: the bundle no longer covers the change.
    _write(repo, "app/late.py", "x = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: late")
    clean_ex = str(tmp_path / "all.json")
    with open(clean_ex, "w") as fh:
        json.dump({"exceptions": [{"id": "EX-8", "rule": "clawmetry/guard/credential_access",
                                   "expires": "2999-01-01", "approved_by": "sec-lead",
                                   "reason": "fixture"}]}, fh)
    assert run("--fail-on", "critical", "--on-missing-evidence", "fail",
               "--exceptions", clean_ex) == 1
    assert gate()["evidence_status"] == pp.EVIDENCE_PARTIAL
    assert run("--fail-on", "critical", "--on-missing-evidence", "pass",
               "--exceptions", clean_ex) == 0

    # Tampering with the committed bundle makes it invalid evidence.
    tampered = dict(bundle, links={"app/db.py": []})
    _write(repo, rel, json.dumps(tampered))
    assert run("--fail-on", "critical", "--on-missing-evidence", "fail") == 1
    assert gate()["evidence_status"] == pp.EVIDENCE_INVALID
