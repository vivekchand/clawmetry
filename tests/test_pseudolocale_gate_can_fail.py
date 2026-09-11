"""The pseudolocale gate must be able to go red.

`tests/e2e/pseudolocale.mjs` shipped for months as a script that could not
fail. Measured on `origin/main` before this guard: `git grep -rn pseudolocale
.github/` returned nothing, so it ran in no job, and even run by hand its only
exit-1 path was:

    if (STRICT && fail > 0) { ... process.exit(1) }

Everything else fell through to `console.log('  ✅ Locale machinery verified')`
and exit 0. Against a server that answers every probe and localises nothing,
the script printed `0 passed, 4 failed` and then `✅ Locale machinery verified`
and exited 0. Wiring that into CI would have added a green light wired to
nothing, which is worse than no light.

The fix separates two things the single STRICT flag had conflated:

  MACHINERY  is the pseudolocale applied, does the switcher list en-XA, does
             the locale survive a tab switch. Invariants. Always exit 1.
  RESIDUAL   how many un-extracted English strings remain. A backlog. Soft by
             default, STRICT=1 for zero, MAX_RESIDUAL=<n> for a ratchet.

These are static checks over the shipped script and workflow. They run in the
lint job, so the contract holds even in a job with no browser. The behaviour
itself was verified by running the script against both a real dashboard and a
deliberately broken one; this guard stops the semantics regressing silently.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = (REPO / "tests" / "e2e" / "pseudolocale.mjs").read_text(encoding="utf-8")
WORKFLOWS = REPO / ".github" / "workflows"


def _code_only(src: str) -> str:
    """Strip `//` line comments and `/* */` blocks.

    The script's own header documents the failure modes it must not have, and
    quotes the string it must no longer print unconditionally. Matching raw
    text would assert against the explanation instead of the code.
    """
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(
        ln for ln in src.splitlines() if not ln.lstrip().startswith("//")
    )


CODE = _code_only(SCRIPT)


def test_machinery_failure_exits_nonzero_without_strict():
    """The whole point. A dead locale switcher is not a backlog item."""
    assert "if (STRICT && fail > 0)" not in CODE, (
        "machinery failures are still gated behind STRICT, so the script "
        "exits 0 on a dashboard where nothing is localised"
    )
    # There must be an unconditional `fail > 0` exit.
    assert re.search(r"if \(fail > 0\) \{", CODE), (
        "no unconditional `if (fail > 0)` branch: nothing makes a machinery "
        "failure fatal"
    )


def test_success_is_not_announced_over_a_machinery_failure():
    """`✅ Locale machinery verified` must come after the fail check, not
    before it. Printing it above the check is how a red run read as green."""
    verified = CODE.index("Locale machinery verified")
    fail_exit = CODE.index("if (fail > 0) {")
    assert fail_exit < verified, (
        "the script announces 'Locale machinery verified' before it checks "
        "whether any machinery check failed"
    )


def test_residual_strings_do_not_go_through_the_machinery_counter():
    """`check()` is the machinery counter. Feeding residual strings into it
    makes an unfinished backlog indistinguishable from a broken switcher,
    which is the conflation that kept this script out of CI."""
    assert "no un-extracted strings`, false" not in CODE, (
        "residual strings are still reported through check(), so they count "
        "as machinery failures"
    )


def test_a_required_dashboard_cannot_be_skipped():
    """Unreachable means skip by hand and fail in CI. A job that passes
    because nothing booted reports a verdict it never reached."""
    assert "REQUIRE_DASHBOARD" in CODE, (
        "no REQUIRE_DASHBOARD escape hatch: an unreachable dashboard always "
        "exits 0, so a CI job would pass without testing anything"
    )
    i = CODE.index("if (!reachable)")
    block = CODE[i:i + 900]
    assert "process.exit(1)" in block, (
        "the unreachable branch never exits non-zero, even when the dashboard "
        "is declared required"
    )


def test_the_ratchet_exists_and_is_separate_from_strict():
    """STRICT demands zero, which the backlog is nowhere near. MAX_RESIDUAL is
    what lets CI fail on growth without demanding zero first."""
    assert "MAX_RESIDUAL" in CODE
    assert re.search(r"totalLeaking > MAX_RESIDUAL", CODE), (
        "MAX_RESIDUAL is read but never compared against the residual count"
    )


def test_the_probe_is_retried():
    """Measured on a node with real history, the first `/api/overview` call
    took 4.18s against a 4s single-shot timeout while the next two took 1.3s.
    A gate that fails because one cold call was 180ms late is a flaky gate,
    and flaky gates get ignored rather than fixed."""
    assert "PROBE_ATTEMPTS" in CODE, "reachability probe is still a single shot"
    assert re.search(r"attempt <= PROBE_ATTEMPTS", CODE)


def test_the_script_is_actually_wired_into_a_workflow():
    """The original defect: a guard that runs in no job. This is the same
    class as an unlisted pytest file, which CI here also never executes."""
    hits = [
        p.name
        for p in WORKFLOWS.glob("*.yml")
        if "pseudolocale" in p.read_text(encoding="utf-8")
    ]
    assert hits, (
        "no workflow references pseudolocale, so the script gates nothing "
        "no matter what its exit codes are"
    )


def test_the_workflow_requires_the_dashboard():
    """Wiring it in without REQUIRE_DASHBOARD would re-create the silent pass
    at the workflow level instead of the script level."""
    wf = (WORKFLOWS / "pseudolocale-e2e.yml").read_text(encoding="utf-8")
    assert "REQUIRE_DASHBOARD" in wf, (
        "the workflow does not set REQUIRE_DASHBOARD, so a dashboard that "
        "fails to boot makes the job pass"
    )
    assert "npm ci" in wf, "workflow uses npm install rather than npm ci"
