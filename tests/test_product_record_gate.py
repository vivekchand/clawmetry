"""The product-record gate must actually fail.

FLYWHEEL.md section 0c makes "write the PRD in 8090 first" the standard.
scripts/check_product_record.py is what stops it being a rule everyone agrees
with and nobody follows.

A gate that cannot fail is worse than no gate: it reports success forever and
everyone stops looking. This repo has been burned by exactly that (an invalid
ruff rule plus `|| true` linted nothing for months), so every branch here is
asserted against a case that must be REJECTED, not only ones that pass.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "check_product_record.py"


def _load():
    spec = importlib.util.spec_from_file_location("_prg", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prg = _load()

_LINK = ("https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb"
         "/requirements/1e232fe6-5b9b-48dd-8873-70e52684067a")


def _verdict(body, paths, monkeypatch):
    monkeypatch.setenv("PR_BODY", body)
    monkeypatch.setattr(prg, "changed_files", lambda base, head: paths)
    return prg.main()


# ── the case that must be rejected ──────────────────────────────────────

def test_code_change_with_no_record_is_rejected(monkeypatch):
    """The whole point. If this ever returns 0 the gate is decorative."""
    assert _verdict("just a change", ["clawmetry/local_store.py"], monkeypatch) == 1


def test_empty_body_is_rejected(monkeypatch):
    assert _verdict("", ["routes/usage.py"], monkeypatch) == 1


def test_bare_opt_out_without_a_reason_is_rejected(monkeypatch):
    """"No-PRD:" with nothing after it is a shrug, not a decision."""
    assert _verdict("No-PRD:", ["clawmetry/sync.py"], monkeypatch) == 1


def test_a_link_to_something_else_is_not_a_record(monkeypatch):
    assert _verdict(
        "see https://github.com/vivekchand/clawmetry/pull/1",
        ["clawmetry/sync.py"], monkeypatch,
    ) == 1


def test_the_word_factory_alone_is_not_a_record(monkeypatch):
    assert _verdict(
        "discussed with the factory team", ["clawmetry/sync.py"], monkeypatch
    ) == 1


# ── the cases that must pass ────────────────────────────────────────────

def test_a_requirement_link_passes(monkeypatch):
    assert _verdict(f"Implements {_LINK}", ["clawmetry/sync.py"], monkeypatch) == 0


def test_a_blueprint_link_passes(monkeypatch):
    bp = _LINK.replace("/requirements/", "/blueprints/")
    assert _verdict(f"Designed in {bp}", ["clawmetry/sync.py"], monkeypatch) == 0


def test_opt_out_with_a_reason_passes(monkeypatch):
    assert _verdict(
        "No-PRD: typo in a log string", ["clawmetry/sync.py"], monkeypatch
    ) == 0


@pytest.mark.parametrize("paths", [
    ["docs/compatibility.md"],
    ["CHANGELOG.md"],
    ["FLYWHEEL.md"],
    [".github/workflows/ci.yml"],
    ["tests/test_efficiency.py"],
    ["scripts/check_product_record.py"],
])
def test_non_product_changes_skip_the_gate(paths, monkeypatch):
    """Writing the record must not itself be gated on citing a record."""
    assert _verdict("", paths, monkeypatch) == 0


def test_a_mixed_pr_still_needs_a_record(monkeypatch):
    """Docs alongside code does not launder the code."""
    assert _verdict(
        "", ["docs/compatibility.md", "clawmetry/local_store.py"], monkeypatch
    ) == 1


# ── dependency bumps ────────────────────────────────────────────────────
#
# Dependabot cannot write "No-PRD:" into a PR body and cannot be configured
# to. Before this exemption every npm advisory fix was unmergeable from the
# moment it opened -- one of them rated high severity -- while the pip
# equivalents sailed through on the .txt suffix alone.


def test_the_npm_dependabot_shape_passes(monkeypatch):
    """The exact file list of PR #5376, one of the bumps that was stuck."""
    assert _verdict(
        "", ["frontend/package-lock.json", "frontend/package.json"], monkeypatch
    ) == 0


@pytest.mark.parametrize("paths", [
    ["package.json"],
    ["package-lock.json"],
    ["frontend/package.json"],
    ["frontend/package-lock.json"],
    ["clawhub-plugin/package.json"],
    ["npm-shrinkwrap.json"],
    ["yarn.lock"],
    ["pnpm-lock.yaml"],
    ["desktop/requirements-dev.txt"],  # the pip half, exempt all along
])
def test_dependency_files_skip_the_gate(paths, monkeypatch):
    assert _verdict("", paths, monkeypatch) == 0


@pytest.mark.parametrize("path", [
    "clawmetry/mypackage.json",
    "clawmetry/data/package.json.bak",
    "routes/package_json.py",
])
def test_merely_looking_like_a_manifest_is_not_enough(path, monkeypatch):
    """Matched on the whole basename. A suffix test would exempt these."""
    assert _verdict("", [path], monkeypatch) == 1


def test_a_dependency_bump_alongside_code_still_needs_a_record(monkeypatch):
    """The exemption must not become a way to smuggle code in."""
    assert _verdict(
        "", ["frontend/package.json", "clawmetry/local_store.py"], monkeypatch
    ) == 1


# ── it has to run as a script, not just import ──────────────────────────

def test_the_script_runs_and_exits_nonzero_for_real(tmp_path):
    """Guard the wiring: CI invokes this as a subprocess, so a syntax or
    import error must show up here rather than as a silent pass."""
    r = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        env={"PR_BODY": "", "BASE_SHA": "HEAD", "HEAD_SHA": "HEAD",
             "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, cwd=str(_REPO),
    )
    # HEAD...HEAD is an empty diff, so this exits 0 -- what matters is that it
    # RAN.
    assert r.returncode == 0, r.stderr[:800]
    assert "product-record gate" in (r.stdout + r.stderr)
