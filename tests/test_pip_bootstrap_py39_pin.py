"""The Python 3.9 pip bootstrap pin must stay on a pip that supports 3.9.

`.github/requirements/pip-bootstrap-py39.txt` exists because its sibling
`pip-bootstrap.txt` pins a pip that declares `Requires-Python >=3.10`, which
the release canary's 3.9 matrix cell cannot install at all. That file's own
header already says a Dependabot bump to 26.1+ "must be REFUSED" -- and until
this guard, nothing enforced it.

That gap is not theoretical. Dependabot proposed exactly that bump (#6047,
26.0.1 -> 26.2 in this file), and it went green on every PR check. It could,
because the only job that installs this file is `release-canary.yml`, which
does not run on pull requests: the bump passes review, merges, and the failure
surfaces afterwards, on the release path, in the job whose whole purpose is to
prove a published release installs. A refusal a reviewer has to remember is
the weakest kind there is, and this one had a green checkmark arguing against
it.

So the rule is checked here instead, where every PR runs it.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PY39_PIN = os.path.join(".github", "requirements", "pip-bootstrap-py39.txt")
RELEASE_CANARY = os.path.join(".github", "workflows", "release-canary.yml")

# pip 26.0.1 declares `Requires-Python >=3.9`; 26.1 moved it to `>=3.10` and
# every release since has kept it there. The boundary is expressed as "below
# 26.1" rather than "exactly 26.0.1" on purpose: a 26.0.x security release, or
# some future pip that restores 3.9, is a bump this guard should ALLOW. What it
# must never allow is a version that cannot be installed on the interpreter the
# file exists to serve.
PIP_FIRST_RELEASE_WITHOUT_PY39 = (26, 1)

_PIN_RE = re.compile(r"^pip==([0-9][^\s\\]*)", re.MULTILINE)


def _read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path), encoding="utf-8") as handle:
        return handle.read()


def _version_tuple(version):
    """Numeric release segment of a PEP 440 version, as a comparable tuple.

    pip's versions are plain `major.minor[.micro]`, so the numeric prefix is
    the whole ordering. Anything trailing (a pre-release marker, say) is
    dropped rather than guessed at -- a pre-release is not a pin this file
    should be carrying either way.
    """
    parts = []
    for segment in version.split("."):
        match = re.match(r"^(\d+)", segment)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts)


def test_py39_bootstrap_pins_a_pip_that_supports_python_39():
    pins = _PIN_RE.findall(_read(PY39_PIN))

    assert pins, (
        "%s pins no pip at all. This file's entire job is to name the pip the "
        "3.9 matrix cell installs." % PY39_PIN
    )
    assert len(pins) == 1, (
        "%s pins pip %s times; expected exactly one pin, because "
        "--require-hashes installs every listed version and the 3.9 cell can "
        "only use one of them." % (PY39_PIN, len(pins))
    )

    version = pins[0]
    assert _version_tuple(version) < PIP_FIRST_RELEASE_WITHOUT_PY39, (
        "%s pins pip==%s, which declares Requires-Python >=3.10 and therefore "
        "cannot install on the Python 3.9 cell in %s -- the one job that reads "
        "this file.\n\n"
        "This is the bump the file's header says must be refused. It is not "
        "caught by any other PR check, because release-canary.yml does not run "
        "on pull requests; merging it breaks the release path instead.\n\n"
        "If this arrived as a Dependabot PR: close it. The pin moves again "
        "when the repository drops Python 3.9, not before."
        % (PY39_PIN, version, RELEASE_CANARY)
    )


def test_release_canary_still_installs_the_py39_pin_on_its_39_cell():
    """The guard above is only worth anything while this file is still used.

    Pointing the 3.9 cell at `pip-bootstrap.txt` would "simplify away" the
    second file and reintroduce the same Requires-Python failure from the
    other direction, leaving the test above passing over a file nothing
    installs.
    """
    canary = _read(RELEASE_CANARY)

    assert PY39_PIN.replace(os.sep, "/") in canary, (
        "%s no longer installs %s. Either the 3.9 matrix cell is gone -- in "
        "which case delete that pin file and this guard together -- or it was "
        "repointed at a pip set that cannot install on 3.9."
        % (RELEASE_CANARY, PY39_PIN)
    )


@pytest.mark.parametrize(
    "version,expected",
    [
        ("26.0.1", True),
        ("26.0.2", True),
        ("26.1", False),
        ("26.2", False),
        ("26.2.1", False),
        ("27.0", False),
    ],
)
def test_boundary_is_the_release_that_dropped_39(version, expected):
    """The comparison itself, so the guard cannot pass by mis-parsing.

    A version check that silently returns the wrong answer is the same dead
    guard this file was written to replace.
    """
    assert (_version_tuple(version) < PIP_FIRST_RELEASE_WITHOUT_PY39) is expected
