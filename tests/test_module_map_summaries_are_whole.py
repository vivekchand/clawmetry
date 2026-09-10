"""A wrapped docstring line must not silently truncate the module map.

`docs/MODULE_MAP.md` is generated from each module's docstring, and the
generator used to take the first LINE. A module whose opening sentence wrapped
therefore got a row cut mid-clause, and the table read as though the module
were barely documented:

    | `clawmetry/detectors.py` | large | research-backed, judge-free, CPU-cheap trajec |

Thirteen modules were in that state when this was written, and nobody had
noticed, because nothing failed: the generator and its `--check` gate agreed
with each other perfectly on a truncated string. Drift Bot eventually reported
the fourteenth as a MISSING entry (2026-09-09, PR #5752), which is the same
symptom wearing a different hat.

Wrapping a line is a formatting choice. It must never change generated
documentation.
"""
import ast
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
MAP = REPO / "docs" / "MODULE_MAP.md"

sys.path.insert(0, str(REPO / "scripts"))
import gen_module_map as gen  # noqa: E402


def _rows():
    for line in MAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[-1]:
                yield cells[0].strip("`"), cells[-1]


def test_the_map_has_rows():
    assert len(list(_rows())) > 100, "the map is empty or its shape changed"


@pytest.mark.parametrize("path,summary", list(_rows()))
def test_no_row_is_cut_mid_sentence(path, summary):
    """Every row ends at a sentence boundary, or at an explicit ellipsis for
    the rare summary too long to fit a table cell."""
    assert summary.endswith((".", "!", "?", "…")) or not summary[-1].isalnum(), (
        f"{path}: the map row ends mid-sentence ({summary[-40:]!r}). "
        "Its docstring's first sentence probably wraps; the generator must "
        "join it, not cut it."
    )


def test_a_wrapped_first_sentence_is_joined():
    """The bug directly: two spellings of the same docstring must generate the
    same summary."""
    one_line = ast.parse('"""Alpha beta gamma delta epsilon."""')
    wrapped = ast.parse('"""Alpha beta gamma\ndelta epsilon."""')
    assert gen._summary(one_line) == gen._summary(wrapped) == \
        "Alpha beta gamma delta epsilon."


def test_only_the_first_sentence_is_taken():
    tree = ast.parse('"""First one. Second one that must not be here."""')
    assert gen._summary(tree) == "First one."


def test_a_version_number_is_not_a_sentence_end():
    """`0.12.845.` and `REQ-OBS-033.` look like sentence ends and are not."""
    tree = ast.parse('"""Shipped in 0.12.845 for REQ-OBS-033, and it works."""')
    assert gen._summary(tree).endswith("and it works.")


def test_an_enormous_first_sentence_is_bounded():
    tree = ast.parse('"""' + "word " * 200 + '."""')
    assert len(gen._summary(tree)) <= gen._SUMMARY_MAX + 1


def test_the_second_paragraph_is_not_pulled_in():
    tree = ast.parse('"""Summary line\nthat wraps.\n\nA second paragraph."""')
    assert gen._summary(tree) == "Summary line that wraps."


def test_the_committed_map_is_what_the_generator_produces():
    """The same check CI runs, here too, so this file fails for the right
    reason rather than leaving a stale map to a different job."""
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "gen_module_map.py"),
                        "--check"], capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
