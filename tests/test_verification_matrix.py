"""The declared verification surface must stay honest.

``verification/matrix.json`` is only worth having if it cannot drift from
reality. These tests check the checker: that a cell pointing at a deleted
verifier fails, that "gated" cannot be claimed for a workflow which does not
report on every pull request, and that the ratchets actually ratchet.
"""
from __future__ import annotations

import copy
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import verification_matrix as vm  # noqa: E402


@pytest.fixture()
def matrix():
    return vm.load_matrix()


# ---------------------------------------------------------------------------
# The shipped matrix must be clean
# ---------------------------------------------------------------------------

def test_shipped_matrix_has_no_drift(matrix):
    problems = vm.check(matrix)
    assert not problems, (
        "verification/matrix.json declares coverage that does not exist:\n"
        + "\n".join(f"  {p['cell']}: {p['problem']}" for p in problems)
    )


def test_matrix_declares_the_python39_cell(matrix):
    """The cell 0.12.753 fell through must stay declared and gated."""
    cells = {c["id"]: c for _, c in vm.iter_cells(matrix)}
    assert "pip-install-linux-py39" in cells, (
        "The Python 3.9 pip-install cell is gone. python_requires is >=3.8 and "
        "the macOS desktop bundle ships a 3.9 venv."
    )
    assert cells["pip-install-linux-py39"]["status"] == "gated", (
        "The 3.9 cell must block merges. It was ungated when 0.12.753 shipped "
        "a CLI that died at import on every 3.9 install."
    )


def test_every_cell_has_an_id_and_status(matrix):
    for product_key, cell in vm.iter_cells(matrix):
        assert cell.get("id"), f"a cell in {product_key} has no id"
        assert cell.get("status") in vm.VALID_STATUS, (
            f"{cell.get('id')} has invalid status {cell.get('status')!r}"
        )


def test_open_holes_are_documented_not_just_counted(matrix):
    """A hole without impact stated is a hole nobody will prioritise."""
    for hole in matrix.get("open_holes") or []:
        assert hole.get("id"), "an open hole has no id"
        assert hole.get("detail"), f"{hole['id']} has no detail"
        assert hole.get("impact"), f"{hole['id']} does not say what it costs"
        assert hole.get("owner"), f"{hole['id']} has no owning repo"


# ---------------------------------------------------------------------------
# The checker must actually catch drift
# ---------------------------------------------------------------------------

def test_missing_verifier_is_caught(matrix):
    broken = copy.deepcopy(matrix)
    product = next(iter(broken["products"]))
    broken["products"][product]["cells"][0]["verifier"] = "tests/does_not_exist.py"
    problems = vm.check(broken)
    assert any("does not exist" in p["problem"] for p in problems), (
        "a cell pointing at a deleted verifier must fail the check"
    )


def test_missing_workflow_job_is_caught(matrix):
    broken = copy.deepcopy(matrix)
    product = next(iter(broken["products"]))
    broken["products"][product]["cells"][0]["verifier"] = "ci.yml::no-such-job"
    problems = vm.check(broken)
    assert any("not found in" in p["problem"] for p in problems), (
        "a cell naming a job that no longer exists must fail the check"
    )


def test_gated_cell_backed_by_path_filtered_workflow_is_rejected(matrix):
    """'gated' is a claim about blocking merges, and it must be true.

    install-test.yml is path-filtered on pull_request, so it stays silent for a
    setup.py change. Declaring a cell gated against it would assert protection
    that does not exist.
    """
    broken = copy.deepcopy(matrix)
    product = next(iter(broken["products"]))
    broken["products"][product]["cells"][0]["status"] = "gated"
    broken["products"][product]["cells"][0]["verifier"] = "install-test.yml::test-linux"
    problems = vm.check(broken)
    assert any("gated" in p["problem"] for p in problems), (
        "a gated cell must be backed by a workflow that runs on every PR"
    )


def test_duplicate_cell_ids_are_caught(matrix):
    broken = copy.deepcopy(matrix)
    product = next(iter(broken["products"]))
    cells = broken["products"][product]["cells"]
    cells.append(copy.deepcopy(cells[0]))
    problems = vm.check(broken)
    assert any("duplicate" in p["problem"] for p in problems)


def test_invalid_status_is_caught(matrix):
    broken = copy.deepcopy(matrix)
    product = next(iter(broken["products"]))
    broken["products"][product]["cells"][0]["status"] = "probably-fine"
    problems = vm.check(broken)
    assert any("invalid status" in p["problem"] for p in problems)


# ---------------------------------------------------------------------------
# Ratchets
# ---------------------------------------------------------------------------

def test_adding_an_open_hole_without_fixing_one_fails(matrix):
    """Stops 'manual' becoming a dumping ground for unverified surface."""
    broken = copy.deepcopy(matrix)
    broken["open_holes"].append(
        {
            "id": "brand-new-hole",
            "detail": "something else is unverified",
            "impact": "unknown",
            "owner": "clawmetry",
        }
    )
    problems = vm.check(broken)
    assert any("open_holes rose" in p["problem"] for p in problems), (
        "the open-holes ratchet must reject a net increase in known gaps"
    )


def test_removing_gated_cells_fails(matrix):
    broken = copy.deepcopy(matrix)
    for product in broken["products"].values():
        for cell in product["cells"]:
            if cell["status"] == "gated":
                cell["status"] = "manual"
    problems = vm.check(broken)
    assert any("gated cells fell" in p["problem"] for p in problems), (
        "downgrading gated coverage to manual must fail the ratchet"
    )


def test_summary_counts_match_the_document(matrix):
    s = vm.summary(matrix)
    cells = list(vm.iter_cells(matrix))
    assert s["total_cells"] == len(cells)
    assert sum(s["by_status"].values()) == len(cells)
    assert s["open_holes"] == len(matrix.get("open_holes") or [])


def test_matrix_json_is_valid_json():
    with open(vm.MATRIX_PATH, encoding="utf-8") as fh:
        json.load(fh)
