"""The mutation ratchet must measure the same thing twice.

A ratchet that moves on its own is worse than no ratchet: it fails pull
requests that changed nothing relevant, and the only ways out are to lower the
baseline (weakening it) or to re-run until it passes (normalising red). Both
destroy the thing it exists to do.

It really did move. The same commit scored 53%, 50% and 47% on three runs, and
it failed #5107, which had not touched the mutated file. Exactly one mutant ever
flipped: ``line 92: constant 3 -> 4``, the ``min_count`` on the API Tests spec.

That mutant is the only one in the set whose mutated source is the SAME LENGTH
as the original. CPython invalidates a cached ``.pyc`` by ``(mtime, size)``, and
the sandbox is reused across mutants, so when two same-size writes land within
one mtime tick the interpreter decides its cache is still valid and runs the
PREVIOUS bytecode. The mutation silently did not apply, the suite passed, and a
killed mutant was recorded as a survivor.

Verifying by re-running the real thing costs minutes, which is not viable per
PR, so this asserts the two mechanical properties that make it deterministic
instead. Both are cheap and neither needs a mutation run.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "mutation_ratchet.py")


def _load():
    spec = importlib.util.spec_from_file_location("_mutation_ratchet_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_script_exists() -> None:
    assert os.path.isfile(SCRIPT), "scripts/mutation_ratchet.py is missing"


def test_subprocess_never_writes_bytecode(monkeypatch) -> None:
    """The fix for the stale-.pyc heisenbug, asserted rather than remembered.

    Without this, a same-length mutation can be masked by cached bytecode and
    reported as a survivor, which is what made the score nondeterministic.
    """
    module = _load()
    captured = {}

    class _Result:
        returncode = 0

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return _Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._run_tests(["true"], REPO_ROOT, 60)

    env = captured.get("env")
    assert env is not None, (
        "_run_tests no longer passes an explicit env, so PYTHONDONTWRITEBYTECODE "
        "is not guaranteed and a same-length mutation can be masked by a stale "
        ".pyc."
    )
    assert env.get("PYTHONDONTWRITEBYTECODE") == "1", (
        "PYTHONDONTWRITEBYTECODE is not set for the mutant test run. CPython "
        "invalidates .pyc by (mtime, size), so a mutation that does not change "
        "the file's length can execute the previous bytecode and be recorded as "
        "a false survivor."
    )


def test_timeout_is_indeterminate_not_a_kill(monkeypatch) -> None:
    """A hang is not evidence that an assertion objected.

    Counting a timeout as a kill made the score depend on machine speed, since
    a mutant that pushes code into a slow path may finish under one load and
    not another.
    """
    module = _load()

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    verdict = module._run_tests(["true"], REPO_ROOT, 1)

    assert verdict == "indeterminate", (
        f"a timed-out mutant was classified {verdict!r}. Treating it as a kill "
        "inflates the score by machine speed; treating it as survived would "
        "fail the ratchet for the same reason. It is neither: exclude it."
    )


def test_verdicts_are_the_three_expected_values(monkeypatch) -> None:
    module = _load()

    class _Ok:
        returncode = 0

    class _Fail:
        returncode = 1

    monkeypatch.setattr(module.subprocess, "run", lambda cmd, **kw: _Ok())
    assert module._run_tests(["true"], REPO_ROOT, 60) == "survived"

    monkeypatch.setattr(module.subprocess, "run", lambda cmd, **kw: _Fail())
    assert module._run_tests(["true"], REPO_ROOT, 60) == "killed"


def test_pycache_purge_helper_exists_and_works(tmp_path) -> None:
    """Belt and braces for the same failure mode."""
    module = _load()
    cache = tmp_path / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "stale.pyc").write_bytes(b"stale")

    module._purge_pycache(str(tmp_path))

    assert not cache.exists(), (
        "_purge_pycache left a __pycache__ behind, so stale bytecode can still "
        "mask a same-length mutation."
    )


def test_baseline_keeps_headroom_below_the_measured_score() -> None:
    """A baseline pinned exactly to the live score is a fragile gate.

    Determinism is proven locally, but CI runs a different interpreter on
    different hardware. Leaving a little headroom means an unrelated PR cannot
    be failed by a one-mutant difference, while the floor still catches a real
    regression. If the gap grows large the baseline should be raised
    deliberately, which is a visible edit.
    """
    import json

    with open(
        os.path.join(REPO_ROOT, "verification", "mutation_targets.json"),
        encoding="utf-8",
    ) as fh:
        config = json.load(fh)

    for target in config.get("targets") or []:
        score = target.get("baseline_score")
        assert 0 < score < 1.0, (
            f"{target['module']} has baseline {score}. Zero enforces nothing; "
            "1.0 demands a 100% kill rate that no realistic suite reaches, "
            "which would be a gate with no path to green."
        )
