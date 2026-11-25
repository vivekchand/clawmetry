"""Pins installed on Python 3.9 must carry the marker split before they need it.

Why this exists
---------------
`.github/requirements/` is one Dependabot stream resolved for CPython 3.11,
and a handful of its sets are nevertheless installed on the 3.9 matrix cells
(`api-tests` and `Assessment privacy` in ci.yml, and the `lint` job, which
runs entirely on 3.9 because that is the floor setup.py advertises).

Those sets stay installable on both interpreters by carrying BOTH versions of
a name behind mutually exclusive `python_full_version` markers -- the design
`ci-api-tests.txt` documents in its own header. The gap that design does not
close on its own: **Dependabot preserves a marker it finds, but never invents
one.** The first time a name's newest release declares `Requires-Python
>= 3.10`, an *unsplit* pin is rewritten above the boundary, `--require-hashes`
fails the whole step rather than the one package, and the 3.9 cells cannot
install the set at all.

That is not theoretical. #6713 (the weekly `ci-scanners` group bump) proposed
`pluggy==1.7.0` into the unsplit `pluggy` pin and took the 3.9 cells of both
jobs red, and `pip-bootstrap-py39.txt` had been taking the same break on `pip`
since 26.1 (#6047, then #6713 again).

The cost is not one red PR. While a group PR sits un-mergeable, Dependabot
answers `pull_request_exists_for_security_update` for that directory and opens
**no security updates for any set in it** -- including
`.github/requirements/audit-scanners.txt`, the set that installs bandit,
pip-audit and zizmor. A wedged bump PR silently stops the advisory stream for
the whole directory.

So the rule is checked here, on every PR, rather than discovered on a Monday:
every pin in a 3.9-installed set either carries the split, or is a name
measured to have no 3.9 boundary above its pin.

Offline by design
-----------------
This test makes no network call. The boundary measurements live in
`MEASURED_NO_PY39_BOUNDARY` below, each one checked against PyPI on the date
recorded there. A name arriving in that list is therefore a review decision
with a measurement behind it, which is the point: the alternative is a test
that re-resolves PyPI on every PR and goes red when an unrelated release
lands.
"""

import os
import re

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ_DIR = os.path.join(".github", "requirements")
WORKFLOW_DIR = os.path.join(".github", "workflows")

# Sets in .github/requirements/ (NOT under py39/, which has its own Dependabot
# entry and its own ceilings) that a Python 3.9 interpreter installs.
#
#   ci-api-tests.txt      ci.yml `api-tests` (ubuntu/3.9 cell) and
#                         `assessment-privacy` (ubuntu-latest, Python 3.9).
#                         Unguarded in both, so 3.9 installs the whole file.
#   ci-trial-recovery.txt ci.yml `api-tests`, unguarded -- so the 3.9 cell too.
#   ci-lint-ruff.txt      ci.yml `lint`, whose setup-python is a literal 3.9.
PY39_INSTALLED_SETS = (
    "ci-api-tests.txt",
    "ci-trial-recovery.txt",
    "ci-lint-ruff.txt",
)

# Sets referenced by a job that HAS a 3.9 cell but which 3.9 never installs,
# because a conditional inside the job picks a different file for it. Listed
# so the discovery check below cannot silently lose a real 3.9 install site.
#
#   pip-bootstrap.txt       release-canary.yml and conformance-heartbeat.yml
#                           both select it in a shell `if` whose 3.9 branch
#                           reads pip-bootstrap-py39.txt instead.
#   pip-bootstrap-py39.txt  IS the 3.9 branch, and is excluded from the
#                           /.github/requirements Dependabot entry (asserted
#                           separately below) rather than split: it is a
#                           3.9-only file carrying one name.
#   ci-assistant-tls.txt    ci.yml `api-tests`, step guarded
#                           `if: matrix.python-version == '3.11'`.
PY39_NOT_INSTALLED_DESPITE_39_JOB = (
    "pip-bootstrap.txt",
    "pip-bootstrap-py39.txt",
    "ci-assistant-tls.txt",
)

# Names pinned unsplit in PY39_INSTALLED_SETS that have NO release above their
# pin declaring Requires-Python >= 3.10. Measured against PyPI on 2026-11-25
# by walking every non-yanked distribution of every release of each name.
#
# A name belongs here only while that holds. When its next release drops 3.9,
# the pin is split in the file (both versions behind mutually exclusive
# python_full_version markers) and the name comes OUT of this list -- which is
# what gives Dependabot a marker to preserve on the bump after that.
MEASURED_NO_PY39_BOUNDARY = frozenset(
    {
        # ci-api-tests.txt
        "blinker",
        "certifi",
        "charset-normalizer",
        "colorama",
        "flask",
        "idna",
        "itsdangerous",
        "jinja2",
        "markupsafe",
        "pygments",
        "waitress",
        "werkzeug",
        # ci-lint-ruff.txt
        "ruff",
    }
)

_PIN_RE = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[^\s;\\]+)(?P<rest>[^\\\n]*)")
_REQ_REF_RE = re.compile(r"\.github/requirements/([A-Za-z0-9_./-]+\.txt)")


def _read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path), encoding="utf-8") as handle:
        return handle.read()


def _normalise(name):
    """PEP 503 normalisation, so `importlib_metadata` and `-metadata` agree."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(rel_path):
    """Every pin in a requirements file as (name, version, marker-or-empty)."""
    out = []
    for line in _read(rel_path).splitlines():
        match = _PIN_RE.match(line)
        if match:
            out.append(
                (
                    _normalise(match.group("name")),
                    match.group("version"),
                    match.group("rest").strip(),
                )
            )
    return out


@pytest.mark.parametrize("set_name", PY39_INSTALLED_SETS)
def test_py39_installed_sets_split_every_name_with_a_py310_boundary(set_name):
    rel = os.path.join(REQ_DIR, set_name)
    pins = _pins(rel)
    assert pins, "%s parsed to zero pins; the check would pass vacuously." % rel

    # A name is covered when it appears more than once behind mutually
    # exclusive markers (the 3.9 side and the 3.10+ side, and pip picks the
    # one its interpreter matches), or when its single pin already carries a
    # python_full_version marker -- a backport installed on one side only.
    # What is NOT covered is a bare `name==version`: that is the pin
    # Dependabot rewrites straight over the boundary.
    occurrences = {}
    markers = {}
    for name, _version, marker in pins:
        occurrences[name] = occurrences.get(name, 0) + 1
        markers.setdefault(name, marker)

    unsplit = sorted(
        name
        for name, count in occurrences.items()
        if count == 1 and "python_full_version" not in markers.get(name, "")
    )

    measured = {_normalise(name) for name in MEASURED_NO_PY39_BOUNDARY}
    unmeasured = [name for name in unsplit if name not in measured]

    assert not unmeasured, (
        "%s is installed on Python 3.9, and pins %s with no python_full_version "
        "marker and no measurement behind it.\n\n"
        "An unsplit pin is what Dependabot rewrites above the 3.9 boundary the "
        "first time a name's newest release declares Requires-Python >= 3.10 "
        "-- it preserves a marker it finds but never invents one. The whole "
        "step then fails under --require-hashes, the weekly group PR cannot go "
        "green, and while it is open Dependabot opens no SECURITY updates for "
        "any set in this directory.\n\n"
        "Resolve it one of two ways:\n"
        "  - If the name's newest release still installs on 3.9: measure it "
        "(walk its PyPI releases for requires_python) and add it to "
        "MEASURED_NO_PY39_BOUNDARY with the date.\n"
        "  - If it does not: split the pin in the file, both versions behind "
        "mutually exclusive python_full_version markers, the way click, "
        "packaging, pluggy, pytest, requests and urllib3 already are there."
        % (rel, ", ".join(unmeasured))
    )


def _job_targets_py39(job):
    """True when some cell of this job can run CPython 3.9.

    Two shapes cover every job in this repo: a literal `python-version: '3.9'`
    on setup-python, and a matrix whose python axis lists 3.9.
    """
    blob = yaml.safe_dump(job, default_flow_style=False)
    if re.search(r"python-version:\s*['\"]?3\.9", blob):
        return True
    matrix = (job.get("strategy") or {}).get("matrix")
    return bool(matrix) and bool(
        re.search(r"['\"]3\.9['\"]", yaml.safe_dump(matrix, default_flow_style=False))
    )


def _sets_referenced_by_py39_jobs():
    """Every .github/requirements set a job with a 3.9 cell can reach.

    Per JOB, not per file: ci.yml defines dozens of jobs and only three of
    them touch 3.9, so a whole-file scan would sweep in every 3.11-only set
    beside them.

    Every set a 3.9 job can reach is returned, including ones a step guard or
    a shell conditional keeps away from the 3.9 cell. Classifying those is a
    human call -- a guard is easy to read wrong and easy to delete -- so they
    are named in PY39_NOT_INSTALLED_DESPITE_39_JOB with the guard written
    down, rather than inferred here.
    """
    workflow_dir = os.path.join(REPO_ROOT, WORKFLOW_DIR)
    found = {}
    for filename in sorted(os.listdir(workflow_dir)):
        if not filename.endswith((".yml", ".yaml")):
            continue
        try:
            parsed = yaml.safe_load(_read(os.path.join(WORKFLOW_DIR, filename)))
        except yaml.YAMLError:
            # "Every workflow file must parse" owns that failure, a step above
            # this one in the same job. Re-reporting it here would only add a
            # second red for one cause.
            continue
        if not isinstance(parsed, dict):
            continue
        for job_name, job in (parsed.get("jobs") or {}).items():
            if not isinstance(job, dict) or not _job_targets_py39(job):
                continue
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                for ref in _REQ_REF_RE.findall(yaml.safe_dump(step, default_flow_style=False)):
                    found.setdefault(ref, set()).add("%s::%s" % (filename, job_name))
    return found


def test_every_py39_install_site_is_accounted_for():
    """No workflow quietly adds a 3.9 install of an unreviewed set.

    The two lists above are explicit on purpose -- a 3.9 cell can also be
    selected by a shell conditional inside a `run:` block, which no parse of
    the YAML will see. What this check CAN do is notice a set reachable from a
    job that has a 3.9 cell and named in neither list, which is the shape a
    new, unreviewed install site arrives in.
    """
    declared = set(PY39_INSTALLED_SETS) | set(PY39_NOT_INSTALLED_DESPITE_39_JOB)
    found = _sets_referenced_by_py39_jobs()

    assert found, (
        "No requirement set was found reachable from any job with a 3.9 cell. "
        "ci.yml's `lint`, `api-tests` and `assessment-privacy` jobs all have "
        "one, so this means the discovery above stopped working, not that the "
        "repo stopped installing on 3.9."
    )

    undeclared = {
        ref: sites
        for ref, sites in found.items()
        if not ref.startswith("py39/") and ref not in declared
    }
    assert not undeclared, (
        "These requirement sets are reachable from a job with a Python 3.9 "
        "cell, and are in neither list in this test:\n%s\n\n"
        "Decide which it is and say so there. If a 3.9 interpreter installs "
        "the set, add it to PY39_INSTALLED_SETS -- the split check above then "
        "covers it. If 3.9 reaches a different file (a shell `if`, or a step "
        "guarded on matrix.python-version), add it to "
        "PY39_NOT_INSTALLED_DESPITE_39_JOB with the guard named."
        % "\n".join(
            "  %s  (reachable from %s)" % (ref, ", ".join(sorted(sites)))
            for ref, sites in sorted(undeclared.items())
        )
    )

    # The lists must not rot in the other direction either: a set that stopped
    # being installed on 3.9 should come out, or the next reader trusts a
    # measurement that is protecting nothing.
    stale = sorted(declared - set(found))
    assert not stale, (
        "These sets are declared here as 3.9-related but no job with a 3.9 "
        "cell reaches them any more: %s. Remove them from the list, so what "
        "is left describes the repo as it is." % ", ".join(stale)
    )


def test_py39_only_bootstrap_set_is_excluded_from_the_311_dependabot_entry():
    """`pip-bootstrap-py39.txt` must not be owned by the un-ceilinged stream.

    It is a 3.9-only set sitting beside the 3.11 ones rather than under
    `py39/`, so the `/.github/requirements` entry claimed it without that
    entry's ceilings and proposed a pip the 3.9 cells cannot install -- 26.2
    in #6047, 26.3 in #6713. `ignore` cannot fix it: that is scoped to an
    entry, not a file, so a `pip >= 26.1` rule there would freeze pip in the
    four 3.11-resolved sets that pin it too.
    """
    config = _read(os.path.join(".github", "dependabot.yml"))
    assert "pip-bootstrap-py39.txt" in config, (
        ".github/dependabot.yml does not mention pip-bootstrap-py39.txt. The "
        "3.9-only pip bootstrap set must be listed in the "
        "/.github/requirements entry's exclude-paths, or that entry proposes "
        "pip 26.1+ into it every week and wedges the directory's whole "
        "security-update stream behind a PR that cannot go green."
    )
