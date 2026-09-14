"""clawmetry/framework_map.py: which published framework items a Guard finding is relevant to.

The one mapping contract (REQ-GOV-FWM-001, Factory requirement
15504aea-9ca0-4a1a-a23d-8e825e4f78f9) from every Guard finding kind to
identifiers in three frameworks:

* ``owasp_llm``: OWASP Top 10 for LLM Applications, 2026 edition, v1.0
  (``LLM01:2026`` to ``LLM10:2026``);
* ``owasp_asi``: OWASP Top 10 for Agentic Applications, 2026 edition
  (``ASI01`` to ``ASI10``);
* ``atlas``: MITRE ATLAS 2026.08, where a tactic (``AML.TA``), a technique
  (``AML.T``), a mitigation (``AML.M``) and a case study (``AML.CS``) are kept
  apart by their declared ``type``.

What a reference MEANS, stated once because it is the easiest thing to get
wrong: the finding is *relevant to* that item. It is not a claim that the risk
is prevented, and no compliance or certification follows from it. Every
finding is ``mode: "detect"`` and ``pre_action_control: False``: it is raised
after the activity it describes, from what its family reads
(:data:`FAMILY_SOURCES`), never before a tool runs.
A kind with no honest identifier says ``none`` and why, instead of borrowing
an unrelated one.

Consumers:

* ``detectors.run_all``, ``repo_scan`` and ``detector_swarm`` stamp
  ``incident["frameworks"]`` with :func:`framework_tags`;
* ``policy_engine.evaluate`` copies it onto the decision it makes;
* ``routes/guard.py`` returns it on ``/api/guard/sessions`` incidents and
  ``/api/guard/actions`` rows, the latter with :func:`evidence_level`;
* ``scripts/gen_framework_coverage.py`` renders ``docs/FRAMEWORK_COVERAGE.md``
  from :func:`render_coverage_markdown`, and ``--check`` fails CI on drift.

Pure: no I/O, no clawmetry imports, never raises. Any change to an identifier,
edition or mapping bumps ``MAPPING_VERSION``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Bumped whenever an identifier, an edition or a kind's mapping changes, so a
#: stored finding says which contract labelled it.
MAPPING_VERSION = "2026-09-14.1"

#: What a finding can establish. The same for every kind today, declared once
#: so no surface re-derives it.
FINDING_CAPABILITY = {
    "observe": True,             # the activity is recorded in the store
    "detect": True,              # a finding is raised
    "evidence": True,            # the finding row keeps what it rested on
    "pre_action_control": False,  # raised after the call ran, never before it
}

#: What each finding family reads. Not every finding comes from tool-call
#: arguments: workspace kinds read the folder, silent-failure kinds read
#: results, errors and session starts. Rendered into the public doc so the
#: coverage page never overstates where a finding came from.
FAMILY_SOURCES: Dict[str, str] = {
    "trajectory": "the sequence of tool calls in one session and the results they returned",
    "behaviour": "tool-call arguments (and, for credentials, tool output), not syscalls",
    "silent_failure": ("tool results, API error events, pending approvals or questions, and "
                       "session (re)starts"),
    "workspace": "configuration files in the session's working directory, not tool calls",
    "fleet": "tool-call arguments across several unrelated sessions on the node",
}

# ── Framework editions, each identifier checked against the edition named ────
FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "owasp_llm": {
        "name": "OWASP Top 10 for LLM Applications",
        "edition": "2026 v1.0",
        "source": "https://genai.owasp.org/ (OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf)",
        "revision": "v1.0 document, title page dated 2026-08-04",
        "catalog": {
            "LLM01:2026": "Prompt Injection",
            "LLM02:2026": "Sensitive Information Disclosure",
            "LLM03:2026": "Excessive Agency",
            "LLM04:2026": "Supply Chain",
            "LLM05:2026": "Data and Model Poisoning",
            "LLM06:2026": "Unbounded Consumption",
            "LLM07:2026": "Misinformation",
            "LLM08:2026": "Hidden Context Exposure",
            "LLM09:2026": "Vector and Embedding Weaknesses",
            "LLM10:2026": "Improper Output Handling",
        },
    },
    "owasp_asi": {
        "name": "OWASP Top 10 for Agentic Applications",
        "edition": "2026",
        "source": "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
        "revision": "Version 2026 document, December 2025",
        "catalog": {
            "ASI01": "Agent Goal Hijack",
            "ASI02": "Tool Misuse and Exploitation",
            "ASI03": "Identity and Privilege Abuse",
            "ASI04": "Agentic Supply Chain Vulnerabilities",
            "ASI05": "Unexpected Code Execution (RCE)",
            "ASI06": "Memory & Context Poisoning",
            "ASI07": "Insecure Inter-Agent Communication",
            "ASI08": "Cascading Failures",
            "ASI09": "Human-Agent Trust Exploitation",
            "ASI10": "Rogue Agents",
        },
    },
    "atlas": {
        "name": "MITRE ATLAS",
        "edition": "2026.08",
        "source": "https://github.com/mitre-atlas/atlas-data/blob/main/dist/v6/ATLAS-2026.08.yaml",
        "revision": ("git blob dfd4e180fdca949eb26cb59555d9c346adcd6781, format-version 6.0.0; "
                     "the identifiers below carry the same type and name in 2026.06, "
                     "the edition OWASP LLM 2026 v1.0 cites"),
        # Only the identifiers this contract references. ATLAS holds hundreds
        # of objects, so its gaps are not enumerated here.
        "catalog": {
            "AML.TA0012": {"type": "tactic", "name": "Privilege Escalation"},
            "AML.T0034.002": {"type": "technique", "name": "Agentic Resource Consumption"},
            "AML.T0055": {"type": "technique", "name": "Unsecured Credentials"},
            "AML.T0081": {"type": "technique", "name": "Modify AI Agent Configuration"},
            "AML.T0086": {"type": "technique", "name": "Exfiltration via AI Agent Tool Invocation"},
            "AML.T0101": {"type": "technique", "name": "Data Destruction via AI Agent Tool Invocation"},
        },
    },
}

FRAMEWORK_KEYS = ("owasp_llm", "owasp_asi", "atlas")

# ── The mapping, one entry per finding kind ──────────────────────────────────
# ``status`` is "verified" (every identifier checked against its edition's
# text) or "none" (no identifier applies; ``none_reason`` says why).
# ``tests`` name a test that fires on the behaviour and one that stays quiet on
# benign work; the contract test fails if either does not exist.
MAPPINGS: Dict[str, Dict[str, Any]] = {
    # Trajectory: is this agent stuck?
    "stuck_loop": {
        "family": "trajectory",
        "owasp_llm": ("LLM06:2026",), "owasp_asi": ("ASI02",), "atlas": ("AML.T0034.002",),
        "status": "verified",
        "rationale": ("LLM06:2026 names multi-turn tool calling loops (Scenario 7) and lists "
                      "state hashing to detect recursive loops as a mitigation. ASI02 lists loop "
                      "amplification as a common example. AML.T0034.002 is an agent driven into "
                      "wasteful tool calls."),
        "limits": ("Detects the repetition whatever caused it; it cannot tell an adversary-induced "
                   "loop from a bug. It reports; it does not cap spend."),
        "requires": "a runtime whose adapter records tool calls",
        "tests": {"positive": "tests/test_detectors.py::test_stuck_loop_identical_calls_positive",
                  "benign": "tests/test_detectors.py::test_stuck_loop_negative_legitimate_different_calls"},
    },
    "no_progress": {
        "family": "trajectory",
        "owasp_llm": ("LLM06:2026",), "owasp_asi": ("ASI02",), "atlas": ("AML.T0034.002",),
        "status": "verified",
        "rationale": ("LLM06:2026 mitigation 8 is detecting a session causing resource-intensive "
                      "action without a clear end state. ASI02 names over-invoking costly APIs. "
                      "AML.T0034.002 is an agent pushed into many tool calls that waste budget."),
        "limits": ("A busy session with no file change may be legitimate research. Cause is not "
                   "attributed."),
        "requires": "a runtime whose adapter records tool calls",
        "tests": {"positive": "tests/test_detectors.py::test_no_progress_positive",
                  "benign": "tests/test_detectors.py::test_no_progress_negative_with_write"},
    },
    "repeated_tool_failure": {
        "family": "trajectory",
        "owasp_llm": (), "owasp_asi": (), "atlas": (),
        "status": "none",
        "none_reason": ("A tool that keeps failing is a reliability signal. LLM06:2026 was "
                        "considered and rejected: failures alone are not unbounded consumption."),
    },
    "action_discrepancy": {
        "family": "trajectory",
        "owasp_llm": ("LLM07:2026",), "owasp_asi": (), "atlas": (),
        "status": "verified",
        "rationale": ("LLM07:2026 Scenario 7 is fabricated task completion. An agent carrying on "
                      "after a failed tool result without retrying or acknowledging it is the "
                      "precursor to that report."),
        "limits": ("Does not read the agent's final claim, so it cannot establish that a false "
                   "completion was reported. The LLM 2026 v1.0 crosswalk relates LLM07 to ASI10 "
                   "Rogue Agents for an agent that falsifies task completion. That link is not "
                   "followed here: this finding sees only the step before a completion claim, not "
                   "the falsified report or any sign of a rogue agent."),
        "requires": "a runtime whose adapter records tool results",
        "tests": {"positive": "tests/test_detectors.py::test_action_discrepancy_positive",
                  "benign": "tests/test_detectors.py::test_action_discrepancy_negative_retry"},
    },
    # Behaviour: is it doing something it does not normally do?
    "file_blast_radius": {
        "family": "behaviour",
        "owasp_llm": ("LLM03:2026",), "owasp_asi": ("ASI02",), "atlas": ("AML.T0101",),
        "status": "verified",
        "rationale": ("LLM03:2026 covers agent actions destroying data through over-broad tools. "
                      "ASI02 names deleting valuable data and passing rm -rf / to a shell. "
                      "AML.T0101 is data destruction through an agent tool."),
        "limits": ("Reads tool-call arguments, not syscalls. A wide edit can be a correct "
                   "refactor. Raised after the command ran."),
        "requires": "a runtime whose adapter records tool-call arguments",
        "tests": {"positive": "tests/test_detectors_behavioural.py::test_blast_radius_root_delete_is_critical",
                  "benign": "tests/test_detectors_behavioural.py::test_blast_radius_ignores_a_normal_edit_session"},
    },
    "credential_access": {
        "family": "behaviour",
        "owasp_llm": ("LLM02:2026",), "owasp_asi": ("ASI03",), "atlas": ("AML.T0055",),
        "status": "verified",
        "rationale": ("LLM02:2026 lists credentials and API keys as protected information. ASI03 "
                      "defines agent identity to include authentication material. AML.T0055 is "
                      "reading insecurely stored credentials from files, environment variables "
                      "and private keys, the locations this detector matches."),
        "limits": ("Matches secret locations and token-shaped values in arguments and output; a "
                   "program the agent runs that reads a secret itself is invisible. Access is not "
                   "disclosure. AML.T0083 was rejected: no agent configuration file is matched."),
        "requires": "a runtime whose adapter records tool-call arguments",
        "tests": {"positive": "tests/test_detectors_behavioural.py::test_credential_access_flags_env_file_read",
                  "benign": "tests/test_detectors_behavioural.py::test_credential_access_ignores_env_example"},
    },
    "network_egress": {
        "family": "behaviour",
        "owasp_llm": (), "owasp_asi": ("ASI02",), "atlas": ("AML.T0086",),
        "status": "verified",
        "rationale": ("ASI02 names exfiltrating information through legitimate tools. AML.T0086 is "
                      "exfiltration through an agent tool that writes to a remote location, which "
                      "the write-direction ground reports."),
        "limits": ("Contacting a new host is not exfiltration. Hosts are read from arguments, not "
                   "network traffic. First-time hosts need a learned baseline, so a new install is "
                   "silent on that ground. LLM02:2026 was not mapped: no disclosure is observed."),
        "requires": "a runtime whose adapter records tool-call arguments; a cohort baseline for first-time hosts",
        "tests": {"positive": "tests/test_detectors_behavioural.py::test_egress_flags_a_host_absent_from_the_baseline",
                  "benign": "tests/test_detectors_behavioural.py::test_egress_ignores_localhost"},
    },
    "privilege_change": {
        "family": "behaviour",
        "owasp_llm": ("LLM03:2026",), "owasp_asi": ("ASI03",), "atlas": ("AML.TA0012",),
        "status": "verified",
        "rationale": ("LLM03:2026 covers agents acting with standing high privilege. ASI03 is "
                      "escalating access. AML.TA0012 is the Privilege Escalation tactic; it is a "
                      "tactic, not a technique, because no ATLAS technique describes sudo, setuid "
                      "or IAM grants run by an agent."),
        "limits": ("Reads commands, not the resulting privilege. AML.T0105 Escape to Host was "
                   "rejected: only the privileged-container pattern relates to it."),
        "requires": "a runtime whose adapter records tool-call arguments",
        "tests": {"positive": "tests/test_detectors_behavioural.py::test_privilege_change_flags_sudo",
                  "benign": "tests/test_detectors_behavioural.py::test_privilege_change_ignores_ordinary_commands"},
    },
    # Silent failure: it stopped, and nobody was told.
    "rate_limited": {
        "family": "silent_failure",
        "owasp_llm": (), "owasp_asi": (), "atlas": (),
        "status": "none",
        "none_reason": ("A provider throttling the agent is an availability symptom reported for "
                        "operations; no item in these frameworks describes it."),
    },
    "blocked_on_user": {
        "family": "silent_failure",
        "owasp_llm": (), "owasp_asi": (), "atlas": (),
        "status": "none",
        "none_reason": ("An agent waiting on a person is an operational state. It is not evidence "
                        "that the AML.M0029 human-in-the-loop mitigation was applied correctly."),
    },
    "crashed": {
        "family": "silent_failure",
        "owasp_llm": (), "owasp_asi": (), "atlas": (),
        "status": "none",
        "none_reason": "A crash loop is a reliability signal; no item in these frameworks describes it.",
    },
    # Workspace: a property of the folder the agent was pointed at.
    "repo_config_exec": {
        "family": "workspace",
        "owasp_llm": (), "owasp_asi": ("ASI05",), "atlas": (),
        "status": "verified",
        "rationale": ("ASI05 is unexpected code execution; a checkout's own git config or "
                      "folder-open task runs a program during ordinary operations."),
        "limits": ("Reports the configuration, not that it ran. LLM04:2026 was rejected: its scope "
                   "is the model and dataset supply chain. AML.T0011 was rejected: it concerns AI "
                   "artifacts."),
        "requires": "the session's working directory is known",
        "tests": {"positive": "tests/test_redteam_corpus.py::test_worktree_hookspath_is_flagged",
                  "benign": "tests/test_redteam_corpus.py::test_default_hookspath_is_not_flagged"},
    },
    "agent_config_tamper": {
        "family": "workspace",
        "owasp_llm": (), "owasp_asi": ("ASI04",), "atlas": ("AML.T0081",),
        "status": "verified",
        "rationale": ("AML.T0081 is modifying an agent's configuration so a change persists and "
                      "affects every agent that reads it. ASI04 covers tampered artefacts an agent "
                      "loads, with pinning configs as a mitigation."),
        "limits": ("Flags hook commands ClawMetry did not install; the project author may have "
                   "added them on purpose. It does not show who wrote them."),
        "requires": "the session's working directory is known",
        "tests": {"positive": "tests/test_guard_workspace_kinds.py::test_claude_hook_file_on_a_cursor_session_names_cursor",
                  "benign": "tests/test_guard_workspace_kinds.py::test_all_clawmetry_hooks_emit_no_finding"},
    },
    "package_manifest_exec": {
        "family": "workspace",
        "owasp_llm": (), "owasp_asi": ("ASI04", "ASI05"), "atlas": (),
        "status": "verified",
        "rationale": ("ASI05 Example 6 is a package install whose hostile code runs during "
                      "installation. ASI04 covers third-party components that bring unsafe code."),
        "limits": ("Reports the install script, not that it ran or that it is hostile. AML.T0011.001 "
                   "was rejected: it concerns packages presented for AI tasks."),
        "requires": "the session's working directory is known",
        "tests": {"positive": "tests/test_redteam_corpus.py::test_an_install_hook_is_reported",
                  "benign": "tests/test_redteam_corpus.py::test_a_publish_or_ordinary_script_is_ignored"},
    },
    # Fleet: only visible across sessions.
    "coordinated_action": {
        "family": "fleet",
        "owasp_llm": (), "owasp_asi": ("ASI07", "ASI08"), "atlas": (),
        "status": "verified",
        "rationale": ("ASI07 includes covert channels between agents, and unrelated agents "
                      "converging on one shared destination is how a shared cache becomes a "
                      "message board. ASI08 names repeated identical intents across agents as an "
                      "observable symptom."),
        "limits": ("Read from tool arguments, not the network. Needs several unrelated session "
                   "families and a full settle window of node memory; a new node reports nothing."),
        "requires": "several unrelated session families and a full settle window of node memory",
        "tests": {"positive": "tests/test_detectors_coordinated_action.py::test_unrelated_sessions_writing_one_unseen_prefix_fire_once",
                  "benign": "tests/test_detectors_coordinated_action.py::test_an_orchestrator_and_its_subagents_count_once"},
    },
}

#: Policy decision evidence levels (REQ-GOV-FWM-002). ``effective`` is part of
#: the vocabulary and is never assigned: nothing independently observes the
#: outcome of a signal yet.
EVIDENCE_LEVELS = ("configured", "exercised", "failed", "effective")
_ACTUATING = frozenset({"pause", "stop", "kill"})


def framework_tags(kind: Any) -> Dict[str, Any]:
    """The references a finding of ``kind`` carries. A fresh dict every call,
    so a consumer mutating it cannot change the contract. Unknown kinds get
    empty lists and ``mapped: False``. Never raises."""
    try:
        entry = MAPPINGS.get(str(kind or ""))
    except Exception:
        entry = None
    out: Dict[str, Any] = {"mapping_version": MAPPING_VERSION}
    for key in FRAMEWORK_KEYS:
        out[key] = list((entry or {}).get(key) or ())
    out["mapped"] = bool(entry) and entry.get("status") == "verified"
    out["mode"] = "detect"
    out["pre_action_control"] = FINDING_CAPABILITY["pre_action_control"]
    return out


def tag_incident(incident: Any) -> Any:
    """Stamp ``incident["frameworks"]`` in place and return the incident.
    Leaves anything that is not a dict untouched. Never raises."""
    try:
        if isinstance(incident, dict):
            incident["frameworks"] = framework_tags(incident.get("kind"))
    except Exception:
        pass
    return incident


def evidence_level(action: Any, enforced: Any, result_ok: Any,
                   result_detail: Any = "") -> str:
    """How strong the evidence behind one recorded policy decision is.

    * ``configured``: a policy matched and no action ran (monitor, alert,
      dry run, not entitled, or recorded but the actuator never reported).
    * ``exercised``: the actuator ran a pause, stop or kill and said it worked.
    * ``failed``: the actuator ran and said it did not.

    ``effective`` would need an independent check of the outcome, which does
    not exist, so it is never returned.
    """
    try:
        act = str(action or "").strip().lower()
        if act not in _ACTUATING or not bool(enforced):
            return "configured"
        if bool(result_ok):
            return "exercised"
        if str(result_detail or "").strip().lower() in ("", "pending"):
            return "configured"
        return "failed"
    except Exception:
        return "configured"


def referenced_ids(framework: str) -> List[str]:
    """Every identifier of ``framework`` some kind references, sorted."""
    seen = set()
    for entry in MAPPINGS.values():
        seen.update(entry.get(framework) or ())
    return sorted(seen)


def coverage_gaps(framework: str) -> List[str]:
    """Catalog identifiers no kind references: the honest gap list."""
    cat = (FRAMEWORKS.get(framework) or {}).get("catalog") or {}
    used = set(referenced_ids(framework))
    return [i for i in cat if i not in used]


def _name(framework: str, ident: str) -> str:
    v = FRAMEWORKS[framework]["catalog"].get(ident)
    return v.get("name", "") if isinstance(v, dict) else str(v or "")


def _cell(framework: str, ids) -> str:
    return "<br>".join(f"{i} {_name(framework, i)}" for i in ids) or "none"


def render_coverage_markdown(kinds: Optional[List[str]] = None) -> str:
    """The public coverage document, generated from this module only."""
    order = list(kinds) if kinds else list(MAPPINGS)
    lines = [
        "# Guard framework coverage",
        "",
        "<!-- GENERATED by scripts/gen_framework_coverage.py from clawmetry/framework_map.py."
        " Do not edit by hand; CI fails on drift. -->",
        "",
        f"Mapping version `{MAPPING_VERSION}`.",
        "",
        "This page says which items of three published frameworks each Guard finding is relevant "
        "to. It describes **coverage, not compliance**. A reference means a finding can draw a "
        "reviewer's attention to activity related to that item. It does not mean the risk is "
        "prevented, and no certification or conformance claim follows from it.",
        "",
        "Every finding is raised after the activity it describes, never before a tool runs. "
        "Capability for every kind: observe yes, detect yes, evidence yes, "
        "pre-action control no. A Guard policy may pause, stop or kill a session after a finding; "
        "that is configured per node and is not counted as coverage here.",
        "",
        "What each family of findings reads:",
        "",
    ]
    for family in dict.fromkeys(MAPPINGS[k]["family"] for k in order):
        lines.append(f"* `{family}`: {FAMILY_SOURCES.get(family, 'not declared')}.")
    lines += [
        "",
        "## Editions verified against",
        "",
        "| Framework | Edition | Source | Revision |",
        "|---|---|---|---|",
    ]
    for key in FRAMEWORK_KEYS:
        fw = FRAMEWORKS[key]
        lines.append(f"| {fw['name']} | {fw['edition']} | {fw['source']} | {fw['revision']} |")
    lines += [
        "",
        "## Findings",
        "",
        "| Finding | Family | OWASP LLM 2026 | OWASP Agentic 2026 | MITRE ATLAS | Status |",
        "|---|---|---|---|---|---|",
    ]
    for kind in order:
        e = MAPPINGS[kind]
        atlas = "<br>".join(
            f"{i} {_name('atlas', i)} ({FRAMEWORKS['atlas']['catalog'][i]['type']})"
            for i in e.get("atlas") or ()) or "none"
        lines.append(
            f"| `{kind}` | {e['family']} | {_cell('owasp_llm', e.get('owasp_llm') or ())} | "
            f"{_cell('owasp_asi', e.get('owasp_asi') or ())} | {atlas} | {e['status']} |")
    lines += ["", "## Why, and where it stops", ""]
    for kind in order:
        e = MAPPINGS[kind]
        lines.append(f"### `{kind}`")
        lines.append("")
        if e["status"] == "none":
            lines.append(f"No identifier. {e['none_reason']}")
        else:
            lines.append(f"* **Why:** {e['rationale']}")
            lines.append(f"* **Limits:** {e['limits']}")
            lines.append(f"* **Needs:** {e['requires']}")
            lines.append(f"* **Fires on:** `{e['tests']['positive']}`")
            lines.append(f"* **Quiet on:** `{e['tests']['benign']}`")
        lines.append("")
    lines += ["## Gaps", "",
              "Items no Guard finding is mapped to. Guard does not claim coverage of these.", ""]
    for key in ("owasp_llm", "owasp_asi"):
        fw = FRAMEWORKS[key]
        gaps = coverage_gaps(key)
        lines.append(f"* **{fw['name']} {fw['edition']}:** "
                     + ("; ".join(f"{i} {_name(key, i)}" for i in gaps) or "none"))
    lines += [
        "* **MITRE ATLAS:** not enumerated. ATLAS catalogs hundreds of adversary techniques; only "
        "the identifiers in the table above are claimed.",
        "* **Not covered by any finding:** prompt content inspection, model and dataset supply "
        "chain, generated-code scanning, and memory or retrieval poisoning.",
        "* **Not yet in this contract:** the pre-tool gates (tool risk classification and hook "
        "approvals), which can hold an action before it runs.",
        "",
        "## Policy decisions",
        "",
        "Each Guard policy decision carries the references of the finding kind it acted on and an "
        "evidence level:",
        "",
        "* `configured`: a policy matched and no action ran (monitor, alert, dry run, not enabled "
        "on this plan, or the actuator never reported).",
        "* `exercised`: a pause, stop or kill ran and the actuator reported success.",
        "* `failed`: the actuator ran and reported failure.",
        "* `effective` is never assigned: nothing independently observes the outcome yet.",
        "",
    ]
    return "\n".join(lines)
