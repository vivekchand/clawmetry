"""The verification surface may grow. It may not shrink quietly.

Line coverage cannot see a guard being weakened: change ``assert x == 5`` to
``assert x is not None`` and coverage is byte-for-byte identical while the guard
stops guarding. Anything that relies on a human noticing that diff is a
convention, and conventions are exactly what an agent under pressure to make CI
green optimises away.

So the enforcement here is mechanical and needs no second reviewer:

* every guard file named in ``verification/guards.json`` must still exist, and
  must not have been emptied out to a stub;
* every ratchet must be at or above its recorded baseline.

This does not make weakening impossible -- an agent can still edit
``guards.json``. It makes weakening impossible to do *silently*: the baseline is
a small, high-signal file that appears in the diff, and lowering a number there
is an explicit act you can review, rather than a subtle assertion change buried
in a large test file.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_PATH = os.path.join(REPO_ROOT, "verification", "guards.json")

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


def _census() -> dict:
    with open(CENSUS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_census_file_exists_and_parses() -> None:
    assert os.path.isfile(CENSUS_PATH), (
        "verification/guards.json is missing. It records the verification "
        "surface; without it nothing detects guards being removed."
    )
    census = _census()
    assert census.get("guard_files"), "census lists no guard files"
    assert census.get("ratchets"), "census lists no ratchets"


@pytest.mark.parametrize(
    "entry",
    _census()["guard_files"],
    ids=lambda e: e["path"],
)
def test_guard_file_still_exists(entry: dict) -> None:
    path = os.path.join(REPO_ROOT, entry["path"])
    assert os.path.isfile(path), (
        f"Guard file {entry['path']} is gone.\n\n"
        f"Why it exists: {entry['why']}\n\n"
        "If this removal is intentional, delete its entry from "
        "verification/guards.json in the same PR and say why in the description."
    )


@pytest.mark.parametrize(
    "entry",
    _census()["guard_files"],
    ids=lambda e: e["path"],
)
def test_guard_file_is_not_hollowed_out(entry: dict) -> None:
    """Deleting the body while keeping the filename must not pass."""
    path = os.path.join(REPO_ROOT, entry["path"])
    if not os.path.isfile(path):
        pytest.skip("missing file; see test_guard_file_still_exists")
    size = os.path.getsize(path)
    floor = entry.get("min_bytes", 500)
    assert size >= floor, (
        f"{entry['path']} shrank to {size} bytes (floor {floor}). A guard "
        "reduced to a stub still imports and still 'passes'.\n\n"
        f"Why it exists: {entry['why']}"
    )


# --------------------------------------------------------------------------
# Ratchets -- live values measured from the real configuration
# --------------------------------------------------------------------------

def _live_ratchets() -> dict:
    import e2e_gate
    import verification_matrix as vm

    workflow_dir = os.path.join(REPO_ROOT, ".github", "workflows")
    workflows = []
    for ext in ("yml", "yaml"):
        workflows.extend(glob.glob(os.path.join(workflow_dir, f"*.{ext}")))

    pip_spec = next(
        (s for s in e2e_gate.REQUIRED_SPECS if s.label == "pip install matrix"),
        None,
    )

    matrix = vm.load_matrix()
    cells = [c for _, c in vm.iter_cells(matrix)]

    with open(
        os.path.join(REPO_ROOT, "verification", "mutation_targets.json"),
        encoding="utf-8",
    ) as fh:
        mutation_config = json.load(fh)

    import importlib.util

    ac_spec = importlib.util.spec_from_file_location(
        "check_ac_coverage",
        os.path.join(REPO_ROOT, "scripts", "check_ac_coverage.py"),
    )
    ac_gate = importlib.util.module_from_spec(ac_spec)
    ac_spec.loader.exec_module(ac_gate)
    ac_declared, _ac_mentioned = ac_gate.scan_tests()
    ac_manifest = ac_gate.load_manifest()
    ac_covered = sum(
        1 for c in ac_manifest["criteria"] if c["id"] in ac_declared
    )

    return {
        "acceptance_criteria_covered": ac_covered,
        "e2e_gate_required_specs": len(e2e_gate.REQUIRED_SPECS),
        "pip_install_matrix_legs": pip_spec.min_count if pip_spec else 0,
        "workflow_files_parsed": len(workflows),
        "declared_matrix_cells": len(cells),
        "gated_matrix_cells": sum(1 for c in cells if c.get("status") == "gated"),
        "mutation_targets": len(mutation_config.get("targets") or []),
    }


def test_mutation_baselines_are_measured_not_aspirational() -> None:
    """A baseline of 0 disables the ratchet while looking configured."""
    with open(
        os.path.join(REPO_ROOT, "verification", "mutation_targets.json"),
        encoding="utf-8",
    ) as fh:
        config = json.load(fh)

    for target in config.get("targets") or []:
        score = target.get("baseline_score")
        assert isinstance(score, (int, float)), (
            f"{target['module']} has no baseline_score"
        )
        assert score > 0, (
            f"{target['module']} has a baseline of {score}. A zero baseline "
            "means every mutant may survive and the ratchet enforces nothing. "
            "Measure a real one: python3 scripts/mutation_ratchet.py "
            "--update-baseline"
        )


@pytest.mark.parametrize("name", sorted(_census()["ratchets"].keys()))
def test_ratchet_has_not_regressed(name: str) -> None:
    census = _census()
    baseline = census["ratchets"][name]
    live = _live_ratchets()

    assert name in live, (
        f"Ratchet {name!r} is recorded but no longer measured. Either restore "
        "the measurement in _live_ratchets() or remove the baseline entry."
    )

    assert live[name] >= baseline["value"], (
        f"RATCHET REGRESSION: {name} dropped from {baseline['value']} to "
        f"{live[name]}.\n\n"
        f"Why this ratchet exists: {baseline['why']}\n\n"
        "Verification coverage is only allowed to increase. If this reduction "
        "is genuinely correct, lower the baseline in verification/guards.json "
        "in this same PR and justify it in the PR description -- so the "
        "decision is visible rather than absorbed silently."
    )


def test_raising_a_ratchet_is_encouraged() -> None:
    """A live value far above baseline means the census is stale, not wrong.

    Informational: it nudges the baseline upward so new coverage is locked in
    rather than left free to erode back. It never fails the build.
    """
    census = _census()
    live = _live_ratchets()
    stale = [
        f"{name}: baseline {spec['value']} but live is {live[name]}"
        for name, spec in census["ratchets"].items()
        if name in live and live[name] > spec["value"]
    ]
    if stale:
        print(
            "\nRatchets that could be raised (locking in new coverage):\n  "
            + "\n  ".join(stale)
        )
