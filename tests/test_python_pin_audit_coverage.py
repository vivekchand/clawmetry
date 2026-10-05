"""Every declared Python dependency file is audited, and every acceptance is live.

`.github/workflows/supply-chain.yml` audits the repository's Python
dependencies for known advisories. For a long time it audited exactly one
file -- `requirements.txt` -- while the 34 hash-pinned sets in
`.github/requirements/` and the OTLP decoder baked into the published,
signed self-hosted image (`deploy/self-hosted/otel-requirements.txt`) were
never scanned at all. `scripts/audit_python_pins.py` now covers all of them.

This file is the floor under that coverage. The audit script is only as honest
as its two declaration lists, and both can rot in silence:

  * an acceptance whose pin has since moved describes a version the repository
    no longer installs, so it would wave through a real advisory on the new
    one;
  * an `unauditable` entry whose cause has been fixed silently removes a file
    from the audit forever;
  * a new requirements file added next week is covered automatically by the
    discovery globs, but a file added OUTSIDE them (a new directory, a
    different name) would be audited by nothing and nothing would say so.

So the rules are checked here rather than left to a reviewer remembering them.
That is the same reason `tests/test_unpinned_pip_installs_declared.py` and
`tests/test_pip_bootstrap_py39_pin.py` exist, and this test runs in the same
job they do: ci.yml's "Syntax & Lint", on every PR. It has to be checked
there, because the supply-chain audit is non-blocking on pull requests by
design -- so a declaration that quietly stopped matching the tree would
otherwise surface only on the Monday schedule, if anyone read it.

No network, no pip-audit run: this checks the declarations against the tree.
"""

import json
import os
import re
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "audit_python_pins.py")
ACCEPTANCE = os.path.join(REPO_ROOT, ".github", "requirements", "audit-acceptance.json")
WORKFLOW = os.path.join(REPO_ROOT, ".github", "workflows", "supply-chain.yml")

# Every Python dependency file in the tree must be reachable by the audit's
# discovery globs. Anything here is deliberately out of scope, with a reason.
OUT_OF_SCOPE = {
    # Not a requirements file: it is the audit's own declaration data.
    ".github/requirements/audit-acceptance.json",
}

_PIN_RE = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*==\s*([^\s;\\#]+)", re.MULTILINE)


def _load():
    with open(ACCEPTANCE) as handle:
        return json.load(handle)


def _discovered():
    """The file list the audit script itself reports, via its --list mode."""
    out = subprocess.run(
        [sys.executable, SCRIPT, "--list"],
        cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert out.returncode == 0, "audit_python_pins.py --list failed:\n%s" % out.stderr
    return {line.split()[0] for line in out.stdout.splitlines() if line.strip()}


def _tree_requirements_files():
    """Requirements-style files found by walking the tree, ignoring vendored trees."""
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
    found = set()
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            if not name.endswith(".txt"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), REPO_ROOT)
            rel = rel.replace(os.sep, "/")
            if rel.startswith(".github/requirements/"):
                found.add(rel)
            elif name == "requirements.txt" or name.endswith("-requirements.txt"):
                found.add(rel)
            elif name.startswith("requirements-") :
                found.add(rel)
    return found


def test_acceptance_file_is_valid_json_with_both_sections():
    data = _load()
    assert "accepted_advisories" in data, "acceptance file lost its accepted_advisories section"
    assert "unauditable" in data, "acceptance file lost its unauditable section"


def test_every_declared_path_still_exists():
    """A declaration naming a file that is gone describes a repository that moved on."""
    data = _load()
    missing = []
    for section in ("accepted_advisories", "unauditable"):
        for rel in data.get(section) or {}:
            if not os.path.isfile(os.path.join(REPO_ROOT, rel)):
                missing.append("%s (declared under %s)" % (rel, section))
    assert not missing, (
        "These declarations in .github/requirements/audit-acceptance.json name files "
        "that no longer exist. Delete the stale entries:\n  " + "\n  ".join(missing)
    )


def test_every_accepted_advisory_matches_the_version_still_pinned():
    """An acceptance is for one version. If the pin moved, the acceptance is void.

    This is the rule that matters most. Each acceptance here says "this
    package, at THIS version, has no installable fix on the interpreter this
    file serves". Bump the pin and that sentence is no longer about the
    repository -- but the advisory ids would keep being waved through. So the
    declaration is held to the version actually pinned.
    """
    data = _load()
    problems = []
    for rel, entries in (data.get("accepted_advisories") or {}).items():
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue  # covered by test_every_declared_path_still_exists
        with open(path) as handle:
            pinned = {
                name.lower().replace("_", "-"): version
                for name, version in _PIN_RE.findall(handle.read())
            }
        for entry in entries:
            package = entry["package"].lower().replace("_", "-")
            if package not in pinned:
                problems.append(
                    "%s declares an acceptance for %r, which the file no longer pins"
                    % (rel, entry["package"])
                )
            elif pinned[package] != entry["version"]:
                problems.append(
                    "%s declares an acceptance for %s==%s, but the file now pins %s==%s. "
                    "Re-audit that version: the advisories it is named by, and whether a "
                    "fix is installable, may both have changed."
                    % (rel, entry["package"], entry["version"], entry["package"], pinned[package])
                )
    assert not problems, (
        "Stale advisory acceptances in .github/requirements/audit-acceptance.json:\n  "
        + "\n  ".join(problems)
    )


def test_every_accepted_advisory_is_also_named_in_the_pin_files_header():
    """The machine-readable declaration and the prose must not drift apart.

    Each pin file's header carries the long form of its acceptance -- what it
    accepts, why no fix is reachable, how narrow the exposure is, and what
    ends it -- written in GHSA ids. This file carries the machine-checkable
    half in the PYSEC ids pip-audit reports. Two lists of the same facts in two
    places is exactly how a stale acceptance survives review, so the GHSA
    aliases recorded here are held to the header that explains them: adding an
    id to the audit's allowlist without writing down why fails.
    """
    data = _load()
    missing = []
    for rel, entries in (data.get("accepted_advisories") or {}).items():
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path) as handle:
            header = handle.read()
        for entry in entries:
            for alias in entry.get("ghsa_aliases") or []:
                if alias not in header:
                    missing.append(
                        "%s: %s is allowlisted for %s but is not explained in the pin "
                        "file's header" % (rel, alias, entry["package"])
                    )
    assert not missing, (
        "These accepted advisories are not documented where a reader of the pin "
        "would see them. Add the reasoning to the pin file's header:\n  "
        + "\n  ".join(missing)
    )


def test_every_declaration_carries_a_reason():
    """A declaration without a reason is a silenced finding, not an accepted one."""
    data = _load()
    thin = []
    for rel, entries in (data.get("accepted_advisories") or {}).items():
        for entry in entries:
            if len((entry.get("reason") or "").strip()) < 60:
                thin.append("accepted_advisories[%s] %s" % (rel, entry.get("package")))
            if not entry.get("ghsa_aliases"):
                thin.append("accepted_advisories[%s] %s has no ghsa_aliases" % (rel, entry.get("package")))
            if not entry.get("ids"):
                thin.append("accepted_advisories[%s] %s has no advisory ids" % (rel, entry.get("package")))
    for rel, entry in (data.get("unauditable") or {}).items():
        if len((entry.get("reason") or "").strip()) < 60:
            thin.append("unauditable[%s]" % rel)
        if not (entry.get("retry_when") or "").strip():
            thin.append("unauditable[%s] has no retry_when: say what would let it be audited" % rel)
    assert not thin, (
        "These declarations need a reason specific enough to review:\n  " + "\n  ".join(thin)
    )


def test_every_requirements_file_in_the_tree_is_discovered_by_the_audit():
    """A requirements file the discovery globs cannot see is audited by nothing."""
    discovered = _discovered()
    uncovered = sorted(_tree_requirements_files() - discovered - OUT_OF_SCOPE)
    assert not uncovered, (
        "These Python dependency files are not reachable by the audit's discovery "
        "globs, so scripts/audit_python_pins.py would never scan them. Add their "
        "location to PINNED_GLOBS (or RANGE_FILES) in that script, or list them in "
        "OUT_OF_SCOPE here with a reason:\n  " + "\n  ".join(uncovered)
    )


def test_the_audit_covers_the_published_self_hosted_image_pins():
    """The one audited file that is not CI-only must never silently leave the set.

    `deploy/self-hosted/otel-requirements.txt` is baked into the signed
    self-hosted server image that is published to users. Every other file in
    this audit describes a CI job; an advisory in this one ships. It is called
    out by name so that a refactor of the discovery globs cannot drop it
    without a test saying so.
    """
    assert "deploy/self-hosted/otel-requirements.txt" in _discovered(), (
        "The published self-hosted image's OTLP pin set dropped out of the audit's "
        "discovery globs. That is the only audited file whose advisories reach a "
        "user machine -- restore it in scripts/audit_python_pins.py."
    )


def test_supply_chain_workflow_runs_the_audit_script():
    """The script is only a guard if the workflow actually calls it."""
    with open(WORKFLOW) as handle:
        body = handle.read()
    assert "scripts/audit_python_pins.py" in body, (
        "supply-chain.yml no longer runs scripts/audit_python_pins.py, so the "
        "pinned sets and the published image's pins are unaudited again."
    )


def test_audit_script_is_syntactically_valid():
    out = subprocess.run(
        [sys.executable, "-m", "py_compile", SCRIPT],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert out.returncode == 0, out.stderr



# ---------------------------------------------------------------------------
# The decision rules, exercised directly. These need no network and no
# pip-audit: `classify` is pure, which is why it was split out of the audit
# loop. The second test is the one that matters -- it is the rule three
# sibling-repo PRs (clawmetry-cloud #2546, clawmetry-pro #204, #300) were each
# filed to establish, and a regression in it would make the whole audit green
# while scanning nothing.
# ---------------------------------------------------------------------------

def _audit_module():
    """Import scripts/audit_python_pins.py by path (scripts/ is not a package)."""
    path = os.path.join(REPO_ROOT, "scripts", "audit_python_pins.py")
    import importlib.util

    spec = importlib.util.spec_from_file_location("audit_python_pins", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_and_accepted_pass_but_undeclared_findings_fail():
    audit = _audit_module()
    accepted = {"a.txt": {("urllib3", "PYSEC-1")}}

    status, _, failure = audit.classify("a.txt", set(), None, accepted, {})
    assert (status, failure) == (audit.CLEAN, None)

    status, _, failure = audit.classify(
        "a.txt", {("urllib3", "PYSEC-1")}, None, accepted, {}
    )
    assert (status, failure) == (audit.ACCEPTED, None), "a declared advisory must not fail"

    status, _, failure = audit.classify(
        "a.txt", {("urllib3", "PYSEC-1"), ("flask", "PYSEC-9")}, None, accepted, {}
    )
    assert status == audit.FINDINGS and failure, "a NEW advisory in a file with an acceptance must fail"
    assert "flask PYSEC-9" in failure and "urllib3" not in failure


def test_a_file_with_no_verdict_fails_unless_it_is_declared():
    """A scanner that could not run must never read as a scanner that found nothing."""
    audit = _audit_module()

    status, _, failure = audit.classify("a.txt", None, "pip exploded", {}, {})
    assert status == audit.NO_VERDICT, "an unresolvable file must not be reported as clean"
    assert failure and "Do not let it pass as clean" in failure

    declared = {"a.txt": {"reason": "mitmproxy needs 3.12", "retry_when": "runner moves"}}
    status, note, failure = audit.classify("a.txt", None, "pip exploded", {}, declared)
    assert (status, failure) == (audit.UNAUDITABLE, None)
    assert note == "mitmproxy needs 3.12", "the reason is reported on every run"


def test_an_unauditable_declaration_that_now_resolves_fails():
    """Otherwise a fixed cause silently removes a file from the audit forever."""
    audit = _audit_module()
    declared = {"a.txt": {"reason": "r" * 60, "retry_when": "x"}}
    status, _, failure = audit.classify("a.txt", set(), None, {}, declared)
    assert status == audit.CLEAN and failure, "a stale unauditable declaration must fail"
    assert "Remove the declaration" in failure


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
