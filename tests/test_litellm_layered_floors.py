"""The LiteLLM pin set's declared security floors must be the versions it installs.

`.github/requirements/ci-litellm-proxy.txt` carries a block of hand-applied
security floors -- packages litellm pins at versions with open advisories, so
they cannot come out of `uv pip compile` at all and are raised by hand
afterwards. The file's header lists them under "Currently layered:" and tells
the next editor to re-apply them after any regeneration.

That list is prose, and prose and pins drift apart silently. They did: the
PyJWT floor was raised to 2.15.0 in the header while the pin below stayed at
2.13.0, so the file documented a floor it did not install and 12 advisories
came back. Nothing failed, because nothing compared the two halves.

The failure mode is not a careless human. Every entry in that block is spelled
exactly like a requirement line (`Name==Version`), which is also what an
automated dependency bump searches a requirements file for -- so the comment is
a decoy that matches before the real pin does, and a bump can land having
edited only the decoy. That is a bump this guard should FAIL, loudly, on the PR
that proposes it, rather than leaving a green checkmark over a lowered floor.

So the rule is checked here: every version named under "Currently layered:"
must equal the version actually pinned for that package in the same file.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LITELLM_PIN = os.path.join(".github", "requirements", "ci-litellm-proxy.txt")

_MARKER = "Currently layered:"

# `Name==Version` as it appears both in the prose block and as a real pin.
_REQ_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9][^\s\\,]*)")


def _normalize(name):
    """PEP 503 name normalization, so `PyJWT` and `pyjwt` compare equal."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _read():
    path = os.path.join(REPO_ROOT, LITELLM_PIN)
    assert os.path.exists(path), "%s is missing" % LITELLM_PIN
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _declared_floors(text):
    """The `Name==Version` pairs listed under the "Currently layered:" marker.

    The block is the run of comment lines after the marker, ending at the first
    comment line that names no requirement (the header's explanatory prose
    resumes there).
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _MARKER in line:
            break
    else:
        pytest.fail(
            "%s no longer has a %r block. The layered floors are the only "
            "record of which pins were raised by hand; if the block moved or "
            "was renamed, update this guard rather than deleting it."
            % (LITELLM_PIN, _MARKER)
        )

    floors = {}
    for line in lines[i + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("#"):
            break
        found = _REQ_RE.findall(stripped)
        if not found:
            # A blank comment line directly after the marker is part of the
            # block's formatting; prose after any floor ends it.
            if floors:
                break
            continue
        for name, version in found:
            floors[_normalize(name)] = (name, version)
    return floors


def _actual_pins(text):
    """The versions the file actually installs, keyed by normalized name."""
    pins = {}
    for line in text.splitlines():
        if line.startswith((" ", "\t", "#")) or not line.strip():
            continue
        match = _REQ_RE.match(line.strip())
        if match:
            pins[_normalize(match.group(1))] = match.group(2)
    return pins


def test_layered_floor_block_is_found():
    """The block exists and names the floors, so the guard below has teeth."""
    floors = _declared_floors(_read())
    assert floors, "found the %r marker but parsed no floors from it" % _MARKER
    # The block has never held fewer than a handful; a parse that silently
    # collapsed to one entry would pass the assertion above while checking
    # almost nothing.
    assert len(floors) >= 5, "parsed only %d floor(s): %s" % (len(floors), sorted(floors))


def test_every_declared_floor_is_pinned_at_that_version():
    text = _read()
    floors = _declared_floors(text)
    pins = _actual_pins(text)

    missing = sorted(key for key in floors if key not in pins)
    assert not missing, (
        "%s declares a layered floor for %s under %r, but pins no such "
        "package. Either the pin was dropped or the floor is stale -- fix "
        "whichever is wrong, do not delete this check."
        % (LITELLM_PIN, ", ".join(missing), _MARKER)
    )

    drifted = []
    for key, (spelling, declared) in sorted(floors.items()):
        actual = pins[key]
        if actual != declared:
            drifted.append("%s: header says %s, file pins %s" % (spelling, declared, actual))

    assert not drifted, (
        "The declared security floors in %s do not match what it installs:\n"
        "  %s\n"
        "Each of these floors was raised by hand because the resolved pin "
        "carried an open advisory. A header that names a version the file "
        "does not install is a floor that is not there. Raise the pin (with "
        "every sha256 the release publishes), or, if the floor is genuinely "
        "no longer needed, remove it from the block and say why."
        % (LITELLM_PIN, "\n  ".join(drifted))
    )


def test_pyjwt_floor_clears_its_advisories():
    """The regression that motivated this guard, pinned as its own case.

    PyJWT 2.13.0 carries 12 advisories; 11 are fixed in 2.14.0 and the last in
    2.15.0. Asserted independently of the block above so that a future edit
    which drops PyJWT from the prose list cannot also quietly drop the floor.
    """
    pins = _actual_pins(_read())
    pinned = pins.get("pyjwt")
    assert pinned is not None, "%s no longer pins pyjwt" % LITELLM_PIN

    parts = tuple(int(part) for part in pinned.split(".")[:3] if part.isdigit())
    assert parts >= (2, 15, 0), (
        "pyjwt is pinned at %s; the advisories against it are cleared only "
        "from 2.15.0. litellm pins a lower version, and this file installs "
        "with `--no-deps --require-hashes`, so carrying the higher one is "
        "deliberate and must survive a regeneration." % pinned
    )
