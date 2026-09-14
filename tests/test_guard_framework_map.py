"""Guard framework references: the contract, the findings, the decisions, the doc.

Factory requirement "Guard Framework References" (15504aea-9ca0-4a1a-a23d-8e825e4f78f9),
issue #5943. The contract is ``clawmetry/framework_map.py``; these tests re-derive
its facts from the code that produces findings rather than trusting either side.

Criteria and the tests that hold them:

* AC-GOV-FWM-001.1 every finding kind is mapped or says none with a reason:
  ``test_every_finding_kind_is_mapped_or_says_none``.
* AC-GOV-FWM-001.2 one mapping version and a verified edition per framework:
  ``test_editions_and_mapping_version_are_declared``.
* AC-GOV-FWM-001.3 rationale, limit, and a firing and a quiet test that exist:
  ``test_mapped_kinds_carry_rationale_limits_and_real_tests``.
* AC-GOV-FWM-001.4 identifiers exist in the pinned catalog, ATLAS types kept apart:
  ``test_every_identifier_is_in_its_pinned_catalog``.
* AC-GOV-FWM-002.1 findings carry references, mapping version and mode:
  ``test_run_all_findings_carry_their_references``,
  ``test_workspace_and_fleet_findings_carry_their_references``,
  ``test_guard_sessions_route_returns_references``.
* AC-GOV-FWM-002.2 decisions carry references and an evidence level, never effective:
  ``test_policy_decision_copies_the_incident_references``,
  ``test_actions_route_labels_evidence_strength``,
  ``test_evidence_level_never_claims_effective``.
* AC-GOV-FWM-003.1 the public doc is generated and drift fails:
  ``test_coverage_doc_matches_the_contract``.
* AC-GOV-FWM-003.2 the doc says coverage not compliance and lists every gap:
  ``test_coverage_doc_says_coverage_not_compliance_and_lists_gaps``.
"""
from __future__ import annotations

import importlib.util
import itertools
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
from clawmetry import detector_swarm as swarm  # noqa: E402
from clawmetry import detectors  # noqa: E402
from clawmetry import framework_map as fm  # noqa: E402
from clawmetry import policy_engine as pe  # noqa: E402
from clawmetry import repo_scan  # noqa: E402

_DOC = os.path.join(_REPO_ROOT, "docs", "FRAMEWORK_COVERAGE.md")


# ── the contract ─────────────────────────────────────────────────────────────
def test_every_finding_kind_is_mapped_or_says_none():
    # Auto-discovered: a new detector, workspace or fleet kind with no entry
    # fails here, so nobody has to remember to update a second list.
    assert set(fm.MAPPINGS) == set(detectors.ALL_INCIDENT_KINDS)
    for kind, entry in fm.MAPPINGS.items():
        ids = [i for key in fm.FRAMEWORK_KEYS for i in entry.get(key) or ()]
        assert entry["status"] in ("verified", "none"), kind
        if entry["status"] == "none":
            assert ids == [], f"{kind} says none but carries {ids}"
            assert len(entry.get("none_reason", "").strip()) > 20, kind
        else:
            assert ids, f"{kind} is verified with no identifier"


def test_editions_and_mapping_version_are_declared():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", fm.MAPPING_VERSION)
    assert set(fm.FRAMEWORKS) == set(fm.FRAMEWORK_KEYS)
    for key, fw in fm.FRAMEWORKS.items():
        for field in ("name", "edition", "source", "revision"):
            assert str(fw.get(field) or "").strip(), f"{key}.{field}"
    assert fm.FRAMEWORKS["owasp_llm"]["edition"] == "2026 v1.0"
    assert fm.FRAMEWORKS["owasp_asi"]["edition"] == "2026"
    assert fm.FRAMEWORKS["atlas"]["edition"] == "2026.08"


def _test_exists(ref: str) -> bool:
    path, _, name = ref.partition("::")
    full = os.path.join(_REPO_ROOT, path)
    if not name or not os.path.isfile(full):
        return False
    with open(full, encoding="utf-8") as fh:
        return re.search(r"^def " + re.escape(name) + r"\(", fh.read(), re.M) is not None


def test_mapped_kinds_carry_rationale_limits_and_real_tests():
    for kind, entry in fm.MAPPINGS.items():
        if entry["status"] != "verified":
            continue
        for field in ("rationale", "limits", "requires"):
            assert len(str(entry.get(field) or "").strip()) > 15, f"{kind}.{field}"
        tests = entry.get("tests") or {}
        assert set(tests) == {"positive", "benign"}, kind
        for role, ref in tests.items():
            assert _test_exists(ref), f"{kind} {role} test {ref!r} does not exist"


_ATLAS_PREFIX = (("AML.TA", "tactic"), ("AML.CS", "case-study"),
                 ("AML.M", "mitigation"), ("AML.T", "technique"))


def test_every_identifier_is_in_its_pinned_catalog():
    llm = fm.FRAMEWORKS["owasp_llm"]["catalog"]
    asi = fm.FRAMEWORKS["owasp_asi"]["catalog"]
    atlas = fm.FRAMEWORKS["atlas"]["catalog"]
    assert sorted(llm) == [f"LLM{n:02d}:2026" for n in range(1, 11)]
    assert sorted(asi) == [f"ASI{n:02d}" for n in range(1, 11)]
    for ident, meta in atlas.items():
        want = next(t for prefix, t in _ATLAS_PREFIX if ident.startswith(prefix))
        assert meta["type"] == want, f"{ident} typed {meta['type']}, id says {want}"
        assert meta["name"].strip()
    for kind, entry in fm.MAPPINGS.items():
        for key in fm.FRAMEWORK_KEYS:
            for ident in entry.get(key) or ():
                assert ident in fm.FRAMEWORKS[key]["catalog"], f"{kind}: {ident}"
    # Nothing in the ATLAS catalog is dead weight: every entry is referenced.
    assert sorted(atlas) == fm.referenced_ids("atlas")


# ── findings carry the references ────────────────────────────────────────────
def _loop_events():
    chrono = [{"event_type": "tool_call", "ts": f"2026-06-11T10:00:{i:02d}",
               "data": {"tool": "Bash", "args": {"cmd": "git status"}}} for i in range(5)]
    return list(reversed(chrono))


def test_run_all_findings_carry_their_references():
    found = detectors.run_all(_loop_events(), "claude_code:abc123")
    assert found and {i["kind"] for i in found} == {"stuck_loop"}
    tags = found[0]["frameworks"]
    assert tags == fm.framework_tags("stuck_loop")
    assert tags["owasp_llm"] == ["LLM06:2026"]
    assert tags["atlas"] == ["AML.T0034.002"]
    assert tags["mapping_version"] == fm.MAPPING_VERSION
    assert tags["mode"] == "detect" and tags["pre_action_control"] is False


def test_workspace_and_fleet_findings_carry_their_references():
    finding = repo_scan._finding("agent_config_tamper", "warning", "t", "d", {},
                                 "claude_code:s", "claude_code")
    assert finding["frameworks"]["atlas"] == ["AML.T0081"]
    assert finding["frameworks"]["owasp_asi"] == ["ASI04"]

    now = time.time()
    fp = ("PUT", "cache.internal", "/board")
    fleet = swarm.coordinated_action(
        {f"claude_code:s{n}": [fp] for n in range(3)},
        history={}, history_since_ms=(now - 7 * 86400) * 1000, now=now,
        min_families=2, settle_hours=1)
    assert fleet, "fixture should produce a coordinated_action finding"
    assert fleet[0]["frameworks"] == fm.framework_tags("coordinated_action")
    assert fleet[0]["frameworks"]["owasp_asi"] == ["ASI07", "ASI08"]


@pytest.fixture()
def sessions_payload(monkeypatch):
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    sessions = [{"session_id": f"cursor:{n}", "status": "active", "cost_usd": 1.0,
                 "started_at": now_iso, "last_active_at": now_iso, "metadata": {}}
                for n in ("old", "new")]
    stored = fm.framework_tags("credential_access")
    stored["mapping_version"] = "stored-at-emit"
    signals = [
        # Written before references existed: labelled from the current contract.
        {"session_id": "cursor:old", "severity": "warning", "repeat_count": 3,
         "details": {"kind": "stuck_loop", "message": "m", "detail": "d",
                     "spend_at_risk_usd": 0, "evidence": {}}},
        # Written with references: returned as stored, not relabelled.
        {"session_id": "cursor:new", "severity": "warning", "repeat_count": 3,
         "details": {"kind": "credential_access", "message": "m", "detail": "d",
                     "spend_at_risk_usd": 0, "evidence": {}, "frameworks": stored}},
    ]
    monkeypatch.setattr(guard, "_ls_call", lambda m, **kw: (
        sessions if m == "query_sessions_table"
        else signals if m == "query_recent_loop_signals" else None))
    monkeypatch.setattr(guard, "_live_only_rows", lambda out: [])
    monkeypatch.setattr(guard, "_runtime_supports_signals", lambda *a, **k: {
        "controllable": True, "reason": "", "state": "controllable",
        "actions": ["pause", "stop", "kill"], "no_pause": False})
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    return app.test_client().get("/api/guard/sessions").get_json()


def test_guard_sessions_route_returns_references(sessions_payload):
    by_id = {r["session_id"]: r for r in sessions_payload["sessions"]}
    old = by_id["cursor:old"]["incident"]["frameworks"]
    assert old == fm.framework_tags("stuck_loop")
    new = by_id["cursor:new"]["incident"]["frameworks"]
    assert new["mapping_version"] == "stored-at-emit"
    assert new["owasp_llm"] == ["LLM02:2026"]


# ── decisions carry the references and the strength of the evidence ─────────
def test_policy_decision_copies_the_incident_references():
    inc = fm.tag_incident({"kind": "no_progress", "session_id": "s1",
                           "runtime": "claude_code", "severity": "warning",
                           "title": "t", "detail": "", "evidence": {"total_tool_calls": 30}})
    policy = {"policy_id": "p1", "enabled": True, "scope_runtime": "", "scope_agent_id": "",
              "trigger_kind": "", "min_severity": "info", "min_repeat": 0,
              "min_duration_s": 0, "min_spend_usd": 0.0, "action": "pause"}
    [decision] = pe.evaluate([inc], [policy])
    assert decision["frameworks"] == fm.framework_tags("no_progress")
    # An incident that carries no references yields an empty dict, not a guess.
    bare = dict(inc)
    bare.pop("frameworks")
    [plain] = pe.evaluate([bare], [policy])
    assert plain["frameworks"] == {}


def test_actions_route_labels_evidence_strength(monkeypatch):
    rows = [
        {"session_id": "a", "policy_id": "p", "action": "monitor", "kind": "stuck_loop",
         "enforced": False, "result_ok": False, "result_detail": "recorded"},
        {"session_id": "b", "policy_id": "p", "action": "pause", "kind": "no_progress",
         "enforced": False, "result_ok": False, "result_detail": "DRY RUN: would pause"},
        {"session_id": "c", "policy_id": "p", "action": "kill", "kind": "credential_access",
         "enforced": True, "result_ok": True, "result_detail": "signalled"},
        {"session_id": "d", "policy_id": "p", "action": "stop", "kind": "privilege_change",
         "enforced": True, "result_ok": False, "result_detail": "no such process"},
        {"session_id": "e", "policy_id": "p", "action": "pause", "kind": "crashed",
         "enforced": True, "result_ok": False, "result_detail": "pending"},
    ]
    monkeypatch.setattr(guard, "_ls_call", lambda m, **kw: (
        rows if m == "query_policy_actions" else None))
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    body = app.test_client().get("/api/guard/actions").get_json()
    by_sid = {r["session_id"]: r for r in body["actions"]}
    assert {s: r["evidence_level"] for s, r in by_sid.items()} == {
        "a": "configured", "b": "configured", "c": "exercised",
        "d": "failed", "e": "configured"}
    assert by_sid["c"]["frameworks"]["atlas"] == ["AML.T0055"]
    assert by_sid["e"]["frameworks"]["mapped"] is False  # crashed maps to none


def test_evidence_level_never_claims_effective():
    actions = ("monitor", "alert", "pause", "stop", "kill", "", None, "PAUSE")
    details = ("", "pending", "signalled", "failed", None)
    for action, enforced, ok, detail in itertools.product(
            actions, (True, False, None), (True, False, None), details):
        level = fm.evidence_level(action, enforced, ok, detail)
        assert level in ("configured", "exercised", "failed"), (action, enforced, ok, detail)
    assert "effective" in fm.EVIDENCE_LEVELS  # vocabulary, deliberately unassigned


def test_framework_tags_is_a_fresh_copy_and_unknown_kinds_are_unmapped():
    a = fm.framework_tags("stuck_loop")
    a["owasp_llm"].append("LLM01:2026")
    assert fm.framework_tags("stuck_loop")["owasp_llm"] == ["LLM06:2026"]
    unknown = fm.framework_tags("not_a_kind")
    assert unknown["mapped"] is False and unknown["atlas"] == []
    assert fm.tag_incident(None) is None


# ── the public document ──────────────────────────────────────────────────────
def _load_generator():
    path = os.path.join(_REPO_ROOT, "scripts", "gen_framework_coverage.py")
    spec = importlib.util.spec_from_file_location("gen_framework_coverage", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_coverage_doc_matches_the_contract():
    with open(_DOC, encoding="utf-8") as fh:
        assert fh.read() == fm.render_coverage_markdown(), (
            "docs/FRAMEWORK_COVERAGE.md drifted: python3 scripts/gen_framework_coverage.py")
    assert _load_generator().main(["--check"]) == 0


def test_coverage_doc_names_what_each_family_reads():
    # Review of #5952: the intro said every finding came "from what the call's
    # arguments contained", false for workspace (reads the folder) and
    # silent-failure (reads errors, approvals, restarts) kinds.
    families = {e["family"] for e in fm.MAPPINGS.values()}
    assert families <= set(fm.FAMILY_SOURCES), families - set(fm.FAMILY_SOURCES)
    doc = fm.render_coverage_markdown()
    intro = doc[:doc.index("## Editions verified against")]
    assert "arguments contained" not in intro
    for family in families:
        assert f"`{family}`" in intro and fm.FAMILY_SOURCES[family] in intro, family


def test_coverage_doc_says_coverage_not_compliance_and_lists_gaps():
    with open(_DOC, encoding="utf-8") as fh:
        doc = fh.read()
    assert "coverage, not compliance" in doc
    assert "—" not in doc  # public copy: no em-dashes
    gaps = doc[doc.index("## Gaps"):doc.index("## Policy decisions")]
    for key in ("owasp_llm", "owasp_asi"):
        expected = fm.coverage_gaps(key)
        assert expected, key
        for ident in expected:
            assert ident in gaps, f"gap {ident} missing from the Gaps section"
        for ident in fm.referenced_ids(key):
            assert ident not in gaps, f"{ident} is mapped but listed as a gap"
    for kind in fm.MAPPINGS:
        assert f"`{kind}`" in doc
