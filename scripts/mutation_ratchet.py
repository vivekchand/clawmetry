#!/usr/bin/env python3
"""Measure whether the guards actually catch bugs, and refuse to let that decay.

Line coverage cannot detect a weakened test. Change ``assert score == 10`` to
``assert score is not None`` and coverage is byte-for-byte identical while the
assertion stops asserting. Every mechanism that depends on a human noticing that
diff is a convention, and a coding agent under pressure to turn CI green will
find the cheapest path through a convention every time.

Mutation testing is the measurement that notices. It deliberately breaks the
SOURCE in small ways -- flip ``>=`` to ``>``, swap ``and`` for ``or``, bump a
constant -- and re-runs the tests. A mutant that survives is a change to
production behaviour that no test objects to. The kill rate is therefore a
direct measure of how much the suite is really holding.

Then it ratchets: ``verification/mutation_targets.json`` records a baseline per
target and CI fails when the live score drops below it. Coverage may improve
freely; it may not erode quietly. Lowering a baseline means editing that file,
which is small, reviewable, and in CODEOWNERS -- turning a silent weakening into
a visible decision. That is the achievable goal. Making tampering *impossible*
is not on the table; making it impossible to do *unnoticed* is.

Targets are deliberately the small, critical guard modules rather than the whole
17k-line dashboard: those decide what can merge, and they run in seconds.

Usage::

    python3 scripts/mutation_ratchet.py                # check against baselines
    python3 scripts/mutation_ratchet.py --report       # show surviving mutants
    python3 scripts/mutation_ratchet.py --update-baseline   # record current scores
"""
from __future__ import annotations

import argparse
import ast
import atexit
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(REPO_ROOT, "verification", "mutation_targets.json")


# ---------------------------------------------------------------------------
# Mutation operators
# ---------------------------------------------------------------------------

_CMP_SWAP = {
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}


class _Mutator(ast.NodeTransformer):
    """Apply exactly ONE mutation, identified by index, per pass.

    One-at-a-time matters: two simultaneous mutations can cancel out, and a
    surviving pair tells you nothing about which change the tests missed.
    """

    def __init__(self, target_index: int):
        self.target_index = target_index
        self.counter = 0
        self.applied: str = ""

    def _hit(self) -> bool:
        hit = self.counter == self.target_index
        self.counter += 1
        return hit

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.ops) == 1 and type(node.ops[0]) in _CMP_SWAP:
            if self._hit():
                old = type(node.ops[0]).__name__
                new_cls = _CMP_SWAP[type(node.ops[0])]
                node.ops[0] = new_cls()
                self.applied = f"line {node.lineno}: comparison {old} -> {new_cls.__name__}"
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if self._hit():
            old = type(node.op).__name__
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
            self.applied = f"line {node.lineno}: boolean {old} -> {type(node.op).__name__}"
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._hit():
            self.applied = f"line {node.lineno}: removed 'not'"
            return node.operand
        return node

    def visit_Constant(self, node):
        # Only mutate ints that are not bare 0/1 flags-in-disguise; bumping a
        # threshold is the highest-signal constant mutation.
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            if node.value > 1 and self._hit():
                old = node.value
                node.value = node.value + 1
                self.applied = f"line {node.lineno}: constant {old} -> {node.value}"
        return node


def _count_mutations(tree: ast.AST) -> int:
    counter = _Mutator(-1)
    counter.visit(copy.deepcopy(tree))
    return counter.counter


def _mutate(source: str, index: int) -> tuple[str, str] | None:
    tree = ast.parse(source)
    mutator = _Mutator(index)
    mutated = mutator.visit(copy.deepcopy(tree))
    if not mutator.applied:
        return None
    ast.fix_missing_locations(mutated)
    try:
        return ast.unparse(mutated), mutator.applied
    except Exception:  # noqa: BLE001 - unparse can fail on exotic trees
        return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_tests(test_command: list, cwd: str, timeout: int) -> bool:
    """True when the suite PASSES (which, for a mutant, means it survived).

    The timeout must stay tight. A guard suite runs in seconds, but a mutant
    can push code into a slow path -- breaking the gate's credential check, for
    instance, drops it into a 30-second polling loop. With a generous timeout
    each such mutant costs minutes and the whole run stops being viable in CI.
    A hang is treated as a kill: the mutant changed behaviour enough to matter.
    """
    try:
        proc = subprocess.run(
            test_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False


# Subtrees copied into the sandbox. Small enough to copy in well under a
# second, and enough for the guard tests to resolve their own REPO_ROOT.
_SANDBOX_TREES = ("scripts", "tests", "verification", ".github/workflows")


def _build_sandbox(tmp_root: str) -> str:
    """Copy the parts of the repo the guard tests need into a scratch tree.

    Mutation runs NEVER touch the real working tree. An earlier version wrote
    mutants into the source file and restored it in a ``finally`` block, which
    is fine until the process is killed -- a SIGKILL skips both ``finally`` and
    ``atexit``, and the repository is left holding an ``ast.unparse``d mutant
    with every comment stripped. That happened during development of this very
    script. Operating on a copy makes the failure mode impossible rather than
    merely unlikely.
    """
    for tree in _SANDBOX_TREES:
        src = os.path.join(REPO_ROOT, tree)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(tmp_root, tree)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".hypothesis"),
        )
    return tmp_root


def run_target(target: dict, limit: int, timeout: int, verbose: bool = False) -> dict:
    real_path = os.path.join(REPO_ROOT, target["module"])
    with open(real_path, encoding="utf-8") as fh:
        original = fh.read()

    tmp_root = tempfile.mkdtemp(prefix="cm-mutation-")
    atexit.register(lambda: shutil.rmtree(tmp_root, ignore_errors=True))

    killed = 0
    survived: list = []
    skipped = 0

    try:
        _build_sandbox(tmp_root)
        sandbox_path = os.path.join(tmp_root, target["module"])

        # Sanity check the sandbox BEFORE measuring anything. If the unmutated
        # suite does not pass here, every mutant would also "fail" and be
        # counted as killed, producing a triumphant 100% that means nothing.
        # A silently meaningless ratchet is worse than no ratchet, because it
        # reports success while enforcing nothing.
        if not _run_tests(target["test_command"], tmp_root, timeout):
            raise RuntimeError(
                f"Baseline suite for {target['module']} FAILS in the mutation "
                "sandbox before any mutation is applied. Every mutant would be "
                "scored as killed, so the result would be a meaningless 100%. "
                "Check that _SANDBOX_TREES copies everything the tests need."
            )

        tree = ast.parse(original)
        total_possible = _count_mutations(tree)
        indices = list(range(total_possible))[:limit]

        for index in indices:
            result = _mutate(original, index)
            if result is None:
                skipped += 1
                continue
            mutated_source, description = result
            if mutated_source == original:
                skipped += 1
                continue

            with open(sandbox_path, "w", encoding="utf-8") as fh_:
                fh_.write(mutated_source)

            tests_passed = _run_tests(target["test_command"], tmp_root, timeout)
            if tests_passed:
                survived.append(description)
                if verbose:
                    print(f"    SURVIVED  {description}")
            else:
                killed += 1
                if verbose:
                    print(f"    killed    {description}")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    # Paranoia: the real file must be byte-identical to what we started with.
    with open(real_path, encoding="utf-8") as fh:
        assert fh.read() == original, (
            f"{target['module']} was modified during the mutation run. This "
            "should be impossible now that mutation happens in a sandbox."
        )

    evaluated = killed + len(survived)
    score = (killed / evaluated) if evaluated else 0.0
    return {
        "module": target["module"],
        "evaluated": evaluated,
        "killed": killed,
        "survived": survived,
        "skipped": skipped,
        "score": round(score, 4),
    }


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", action="store_true", help="list surviving mutants")
    ap.add_argument("--verbose", action="store_true", help="print each mutant")
    ap.add_argument(
        "--update-baseline",
        action="store_true",
        help="record current scores as the new baseline (raising is normal; "
        "lowering must be justified in the PR)",
    )
    ap.add_argument("--only", default="", help="run a single module by path")
    args = ap.parse_args()

    config = load_config()
    limit = config.get("max_mutants_per_target", 40)
    timeout = config.get("per_mutant_timeout_seconds", 90)

    results = []
    for target in config["targets"]:
        if args.only and target["module"] != args.only:
            continue
        print(f"  mutating {target['module']} ...")
        result = run_target(target, limit, timeout, verbose=args.verbose)
        result["baseline"] = target.get("baseline_score", 0.0)
        results.append(result)
        print(
            f"    {result['killed']}/{result['evaluated']} killed "
            f"= {result['score']:.0%}  (baseline {result['baseline']:.0%})"
        )

    if args.update_baseline:
        for target in config["targets"]:
            for result in results:
                if result["module"] == target["module"]:
                    target["baseline_score"] = result["score"]
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
        print(f"\nBaselines written to {CONFIG_PATH}")
        return 0

    print()
    regressions = [r for r in results if r["score"] < r["baseline"]]

    if args.report:
        for result in results:
            if result["survived"]:
                print(f"Surviving mutants in {result['module']}:")
                for description in result["survived"]:
                    print(f"  - {description}")
                print(
                    "  Each line is a behaviour change no test objected to. "
                    "Either add an assertion, or accept it deliberately.\n"
                )

    if regressions:
        print("MUTATION SCORE REGRESSION")
        print("=" * 72)
        for result in regressions:
            print(
                f"  {result['module']}: {result['score']:.0%} "
                f"< baseline {result['baseline']:.0%}"
            )
            for description in result["survived"][:5]:
                print(f"      survived: {description}")
        print()
        print(
            "The tests got weaker. Either restore the assertions that were "
            "removed, or -- if this reduction is genuinely correct -- lower the "
            "baseline in verification/mutation_targets.json in this same PR and "
            "say why. The point is that weakening must be visible, not silent."
        )
        return 1

    print("OK - every target is at or above its mutation-score baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
