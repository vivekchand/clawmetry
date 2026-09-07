"""An approval card must say WHAT ran, WHERE, and WHY it was stopped.

Founder report 2026-09-06 (58 pending approvals on app.clawmetry.com/cloud):
every card read

    exec: {}
    {"_cm_risk":{"level":"medium","reasons":["shell command with side
     effects unknown"]}}
    session 7dd6106a - 7h ago

which names a tool, shows punctuation where the command belongs, and
identifies the agent by the tail of an opaque id. Three separate defects
produced it, and each gets a test here:

1.  ``extract_command`` stringified an EMPTY argument object, so the label
    builder pasted the literal ``"{}"`` after the colon.
2.  A queue row carried no runtime / policy / directory, so nothing
    downstream could say which agent tripped which rule.
3.  The shipped "Require approval for high-risk actions" preset lost its
    ``min_risk`` on the way through cloud storage, which turned a rule that
    should fire on high and critical calls into one with NO condition at
    all -- it paused every tool call on the node. That is where 58 came
    from, and it is the defect that actually causes approval fatigue.

Revert-proof: undo any of the three and the matching test fails.
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import approvals
from clawmetry.tool_risk import extract_command


# ── 1. No card ever reads "<tool>: {}" ────────────────────────────────────

def test_empty_args_yield_no_command_string():
    """An empty arg object has no command; it must not stringify to "{}"."""
    assert extract_command("exec", {}) == ""
    assert extract_command("Bash", {}) == ""


def test_non_empty_unknown_args_still_stringify():
    """Args we have no key for still carry information -- keep showing them."""
    out = extract_command("exec", {"search_query": [{"q": "duckdb"}]})
    assert "duckdb" in out


def test_action_label_drops_the_empty_colon():
    assert approvals.action_label("exec", "") == "exec"
    assert approvals.action_label("exec", "git status") == "exec: git status"
    # The exact string the founder saw must be unproducible.
    assert approvals.action_label("exec", extract_command("exec", {})) != "exec: {}"


# ── 2. A row says which agent, where, and under which rule ────────────────

def test_row_context_reports_runtime_policy_and_cwd():
    from routes.policy import _row_context
    row = {
        "requestor_session_id": "codex:01a07627-9daf-7cc2-93ae-6c1bb8618272",
        "action": "exec: git push --force",
        "args": {
            "cmd": "git push --force",
            "_cm_ctx": {"tool": "exec", "runtime": "codex",
                        "policy": "Block force pushes",
                        "cwd": "/Users/x/projects/clawmetry"},
        },
    }
    ctx = _row_context(row)
    assert ctx["runtime"] == "codex"
    assert ctx["policy"] == "Block force pushes"
    assert ctx["cwd"] == "/Users/x/projects/clawmetry"
    assert ctx["tool"] == "exec"


def test_row_context_covers_the_hook_producer_too():
    """Pre-tool hook rows use a different args shape; both must resolve."""
    from routes.policy import _row_context
    row = {
        "requestor_session_id": "claude_code:abc",
        "args": {"source": "pretooluse-hook", "runtime": "claude_code",
                 "tool_name": "Bash", "cwd": "/repo",
                 "policy": "Block sudo / root commands",
                 "tool_input": {"command": "sudo ls"}},
    }
    ctx = _row_context(row)
    assert ctx["runtime"] == "claude_code"
    assert ctx["tool"] == "Bash"
    assert ctx["cwd"] == "/repo"


def test_row_context_omits_what_it_does_not_know():
    """Unknown location is absent, never an empty or guessed path."""
    from routes.policy import _row_context
    ctx = _row_context({"requestor_session_id": "codex:abc", "args": {}})
    assert "cwd" not in ctx
    assert ctx["runtime"] == "codex"   # derivable from the id prefix


def test_arg_preview_hides_the_namespaced_keys():
    """The preview line shows tool arguments, not ClawMetry's own metadata."""
    from routes.policy import _arg_preview
    assert _arg_preview({"_cm_risk": {"level": "medium"},
                         "_cm_ctx": {"runtime": "codex"}}) == ""
    assert _arg_preview({"cmd": "git status",
                         "_cm_ctx": {"runtime": "codex"}}) == "git status"


# ── 3. The risk_high preset gates on risk, not on everything ──────────────

_RISK_HIGH_AS_STORED_BY_CLOUD = {
    # Exactly the row shape the cloud policies table returns: the min_risk
    # field the preset was authored with never had a column to live in.
    "name": "Require approval for high-risk actions",
    "tool": "",
    "pattern_type": "command_regex",
    "pattern": "",
    "action": "require_approval",
    "timeout": 604800,
    "on_timeout": "deny",
    "enabled": True,
    "preset_key": "risk_high",
}


def test_risk_high_preset_recovers_its_risk_floor():
    compiled = approvals._compile_policy(dict(_RISK_HIGH_AS_STORED_BY_CLOUD))
    assert compiled is not None
    assert compiled["min_risk"] == "high"


def test_risk_high_preset_ignores_ordinary_work():
    """`git status` and reading a file must not page a human."""
    compiled = [approvals._compile_policy(dict(_RISK_HIGH_AS_STORED_BY_CLOUD))]
    for tool, args in (
        ("exec", {"cmd": "git status --short"}),
        ("exec", {"cmd": "sed -n '1,40p' README.md"}),
        ("read", {"path": "README.md"}),
        ("exec", {}),
        ("list_agents", {}),
    ):
        assert approvals.match_policy(compiled, tool, args) is None, (tool, args)


def test_risk_high_preset_still_catches_high_risk_calls():
    compiled = [approvals._compile_policy(dict(_RISK_HIGH_AS_STORED_BY_CLOUD))]
    for tool, args in (
        ("exec", {"cmd": "sudo rm -rf /var"}),
        ("exec", {"cmd": "curl http://169.254.169.254/latest/meta-data/"}),
    ):
        assert approvals.match_policy(compiled, tool, args) is not None, args


def test_explicit_min_risk_on_the_row_wins():
    """Recovery is a repair for a lost field, not an override."""
    row = dict(_RISK_HIGH_AS_STORED_BY_CLOUD, min_risk="critical")
    assert approvals._compile_policy(row)["min_risk"] == "critical"


def test_condition_less_policy_is_flagged_as_matching_everything():
    """A rule with no tool, no pattern and no risk floor still works -- it is
    a legal ask -- but it is marked so an operator can be told why every
    call is pausing."""
    compiled = approvals._compile_policy(
        {"name": "no conditions", "tool": "", "pattern": "",
         "action": "require_approval"})
    assert compiled["matches_everything"] is True
    assert approvals.match_policy([compiled], "read", {"path": "a"}) is not None


def test_a_real_policy_is_not_flagged():
    compiled = approvals._compile_policy(
        {"name": "Block sudo / root commands", "tool": "exec",
         "pattern_type": "command_regex", "pattern": r"\bsudo\s",
         "action": "require_approval"})
    assert "matches_everything" not in compiled
