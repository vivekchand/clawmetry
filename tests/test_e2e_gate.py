"""The merge gate must actually block the things it claims to block.

``scripts/e2e_gate.py`` backs the one required status check on ``main``. If its
evaluation is wrong, every other guard in the repository is decorative, so the
logic is tested directly over synthetic check-run payloads (no network).

The regression that motivated the file has its own test below:
``test_syntax_and_lint_failure_blocks_the_merge``. Before L0, ``Syntax & Lint``
was not aggregated, so the Python 3.9 annotation guard could go red while the
pull request merged green -- which is how 0.12.753 shipped a CLI that died at
import on every 3.9 install.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))

import e2e_gate  # noqa: E402
from e2e_gate import REQUIRED_SPECS, Spec, evaluate  # noqa: E402


def run(name, conclusion="success", status="completed", run_id=1):
    return {
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "id": run_id,
        "html_url": f"https://example.invalid/{run_id}",
    }


def state_of(results, label):
    for res in results:
        if res.spec.label == label:
            return res.state
    raise AssertionError(f"no result for {label!r}")


# --------------------------------------------------------------------------
# Single-job specs
# --------------------------------------------------------------------------

def test_single_check_passes():
    spec = Spec("Lint", "Syntax & Lint")
    assert state_of(evaluate([spec], [run("Syntax & Lint")]), "Lint") == "passed"


def test_single_check_failure_fails_the_gate():
    spec = Spec("Lint", "Syntax & Lint")
    results = evaluate([spec], [run("Syntax & Lint", "failure")])
    assert state_of(results, "Lint") == "failed"


def test_missing_check_is_pending_not_passed():
    """A check that never reported must never count as success."""
    spec = Spec("Lint", "Syntax & Lint")
    assert state_of(evaluate([spec], []), "Lint") == "pending"


def test_skipped_and_neutral_count_as_passing():
    spec = Spec("Lint", "Syntax & Lint")
    for conclusion in ("skipped", "neutral"):
        results = evaluate([spec], [run("Syntax & Lint", conclusion)])
        assert state_of(results, "Lint") == "passed", conclusion


# --------------------------------------------------------------------------
# Matrix specs -- the shrinking-matrix trap
# --------------------------------------------------------------------------

def test_matrix_passes_when_all_legs_pass():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(4)]
    assert state_of(evaluate([spec], runs), "pip") == "passed"


def test_matrix_fails_when_one_leg_fails():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(3)]
    runs.append(run("pip install (windows)", "failure", run_id=9))
    assert state_of(evaluate([spec], runs), "pip") == "failed"


def test_matrix_pending_while_legs_still_reporting():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(2)]
    assert state_of(evaluate([spec], runs), "pip") == "pending"


def test_shrinking_the_matrix_does_not_silently_pass():
    """Deleting a matrix leg must fail the gate, not reduce coverage quietly.

    This is the whole point of min_count. A glob alone would happily match the
    three remaining legs and report success, so dropping Windows from the
    matrix would look identical to passing on it.
    """
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(3)]
    assert state_of(evaluate([spec], runs), "pip") == "pending"


# --------------------------------------------------------------------------
# Cancellation / replacement races
# --------------------------------------------------------------------------

def test_cancelled_alone_is_pending_not_failed():
    """cancel-in-progress must not fast-fail the gate."""
    spec = Spec("Lint", "Syntax & Lint")
    results = evaluate([spec], [run("Syntax & Lint", "cancelled")])
    assert state_of(results, "Lint") == "pending"


def test_in_progress_replacement_beats_stale_cancellation():
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "cancelled", run_id=1),
        run("Syntax & Lint", None, status="in_progress", run_id=2),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "pending"


def test_stale_cancellation_never_outranks_a_real_failure():
    """Priority must require BOTH completed AND a definitive conclusion.

    Found by mutation testing: changing ``status == "completed" and conclusion
    in DEFINITIVE`` to ``or`` survived the original suite, because the cases it
    covered happened to reach the same verdict either way. This one does not.
    A cancelled run with a HIGHER id must still lose to a genuine failure --
    under ``or`` the cancellation would score (2, high), outrank the failure,
    and the gate would report pending instead of failing. A red check would
    quietly become a slow check.
    """
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "failure", run_id=1),
        run("Syntax & Lint", "cancelled", run_id=99),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


def test_queued_run_does_not_outrank_a_definitive_one():
    """A queued rerun must not mask an already-known failure."""
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "failure", run_id=1),
        run("Syntax & Lint", None, status="queued", run_id=50),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


def test_definitive_result_beats_in_progress_rerun():
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", None, status="in_progress", run_id=1),
        run("Syntax & Lint", "failure", run_id=2),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


# --------------------------------------------------------------------------
# The shipped configuration
# --------------------------------------------------------------------------

def test_syntax_and_lint_failure_blocks_the_merge():
    """Revert-proof for the 0.12.753 class.

    Syntax & Lint carries scripts/check_py39_annotations.py. Before L0 this
    check was not aggregated by the gate, so it could be red on a merging PR.
    If someone removes it from REQUIRED_SPECS, this test goes red.
    """
    # Every spec satisfied at exactly its required leg count.
    runs = []
    rid = 0
    for spec in REQUIRED_SPECS:
        for leg in range(spec.min_count):
            rid += 1
            name = (
                spec.pattern.replace("*", f"leg{leg}")
                if "*" in spec.pattern
                else spec.pattern
            )
            runs.append(run(name, run_id=rid))
    assert all(r.state == "passed" for r in evaluate(REQUIRED_SPECS, runs)), (
        "baseline should be fully green"
    )

    # Now fail only Syntax & Lint.
    broken = [r for r in runs if r["name"] != "Syntax & Lint"]
    broken.append(run("Syntax & Lint", "failure", run_id=999))
    results = evaluate(REQUIRED_SPECS, broken)
    assert any(r.state == "failed" for r in results), (
        "A red Syntax & Lint MUST block the merge. If this fails, the py3.9 "
        "guard is advisory again and 0.12.753 can recur."
    )


@pytest.mark.parametrize(
    "label",
    [
        "Syntax & Lint",
        "API Tests (3 OS)",
        "pip install matrix",
        "MOAT Verifier",
        "Entitlement API tests",
        "Wheel install & assets",
    ],
)
def test_l0_additions_are_still_required(label):
    """These were advisory before L0. Removing one is a coverage regression."""
    assert any(s.label == label for s in REQUIRED_SPECS), (
        f"{label!r} was dropped from the merge gate. It was added in L0 "
        "precisely because a green PR could merge with it red."
    )


def test_pip_install_matrix_expects_exactly_the_py39_leg():
    """3 OS on 3.11 + the ubuntu 3.9 leg = 4. Exact, in both directions.

    Too FEW means the 3.9 leg stopped gating -- how 0.12.753 escaped. Too MANY
    means the gate waits forever for a leg that never reports, which times out
    and blocks every merge. Both directions are bugs, so this is ==, not >=.
    Changing the CI matrix means changing this number deliberately.
    """
    spec = next(s for s in REQUIRED_SPECS if s.label == "pip install matrix")
    assert spec.min_count == 4, (
        "The pip install matrix must be exactly 4 legs (ubuntu/macos/windows on "
        "3.11, plus ubuntu on 3.9). If ci.yml's matrix genuinely changed, update "
        "this number in the same PR."
    )


def test_api_tests_matrix_covers_all_three_operating_systems():
    spec = next(s for s in REQUIRED_SPECS if s.label == "API Tests (3 OS)")
    assert spec.min_count == 3, (
        "API Tests must gate on all three operating systems. Fewer silently "
        "drops an OS from merge protection."
    )


def test_main_refuses_to_run_without_credentials():
    """No token or no sha must be a hard error, never an accidental pass.

    Found by mutation testing: dropping the ``not`` from the credential guard,
    or turning its ``and`` into ``or``, both survived the original suite. Either
    mutation makes the gate skip its own check and fall through -- the worst
    possible failure mode for a merge gate, since it would report success
    without ever looking at a single check run.
    """
    argv, env = sys.argv[:], os.environ.get("GITHUB_TOKEN")
    os.environ.pop("GITHUB_TOKEN", None)
    sys.argv = ["e2e_gate.py", "--repo", "o/r", "--sha", "abc123"]
    try:
        assert e2e_gate.main() == 2, "missing GITHUB_TOKEN must exit 2"
    finally:
        sys.argv = argv
        if env is not None:
            os.environ["GITHUB_TOKEN"] = env

    argv = sys.argv[:]
    os.environ["GITHUB_TOKEN"] = "t"
    sys.argv = ["e2e_gate.py", "--sha", "abc123"]
    try:
        assert e2e_gate.main() == 2, "missing --repo must exit 2"
    finally:
        sys.argv = argv
        if env is None:
            os.environ.pop("GITHUB_TOKEN", None)
        else:
            os.environ["GITHUB_TOKEN"] = env


def test_every_spec_has_a_nonempty_pattern_and_sane_count():
    for spec in REQUIRED_SPECS:
        assert spec.pattern.strip(), f"{spec.label} has an empty pattern"
        assert spec.min_count >= 1, f"{spec.label} has min_count < 1"


def test_no_duplicate_labels():
    labels = [s.label for s in REQUIRED_SPECS]
    assert len(labels) == len(set(labels)), f"duplicate spec labels: {labels}"


def test_list_mode_runs_without_network():
    """--list must work with no token, so the gate is inspectable locally."""
    argv = sys.argv[:]
    sys.argv = ["e2e_gate.py", "--list"]
    try:
        assert e2e_gate.main() == 0
    finally:
        sys.argv = argv
