"""The root Dockerfile's hash-pinned runtime set must still match requirements.txt.

`Dockerfile` no longer installs `-r requirements.txt` directly: it installs
`.github/requirements/docker-runtime.txt` with `--require-hashes`, so the image
gets artifacts whose sha256 is declared rather than whatever the index serves at
build time.

That pin buys reproducibility and costs a second file that can drift. The
failure mode is silent and one-directional: add a dependency to
requirements.txt, and the image simply does not get it -- `docker build` still
succeeds, and nothing else in CI builds this image (only
deploy/self-hosted/Dockerfile.release is built, by container-image.yml). The
same class of drift already bit clawmetry-cloud, whose production image and
requirements.txt disagreed on a gevent floor until someone noticed by hand.

The image installs a SECOND pinned set, and it is guarded here too.
`.github/requirements/docker-package.txt` pins the part of setup.py's
install_requires that requirements.txt does not name -- waitress, cryptography,
cffi, websocket-client -- because the `pip install -e .` layer resolved those
four live against the index: the editable install has nothing to pin, but the
wheel's own requirements do. requirements.txt and install_requires are
different manifests, so covering one says nothing about the other, and the
drift here is silent in the other direction: add a dependency to setup.py and
the image resolves it unpinned without a word.

So this is the guard that makes both pins honest. It is pure parsing -- no
network, no pip -- so it runs in the Syntax & Lint job on Python 3.9 alongside
the other drift guards.

Named explicitly in .github/workflows/ci.yml because this repo's CI runs FILE
LISTS, not `pytest tests/`: a guard added without a line there runs in no job
at all.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIREMENTS = os.path.join(REPO_ROOT, "requirements.txt")
PINNED = os.path.join(REPO_ROOT, ".github", "requirements", "docker-runtime.txt")
DOCKERFILE = os.path.join(REPO_ROOT, "Dockerfile")

# A requirements line (`name>=1.2,<2 ; marker  # comment`) is taken apart in
# explicit steps rather than by one pattern over the whole line. One pattern
# needs a repeated specifier group, and the operator class [<>=!~] overlaps the
# version class it is followed by, so a run like `!!!!` can be divided between
# them exponentially many ways: on a line the pattern ultimately rejects, that
# is catastrophic backtracking, and it was measured at 14s for a 39-character
# string before this was split up (CodeQL "Inefficient regular expression").
#
# Each pattern below is anchored, applied once per step, and consumes at least
# one character, so a line costs time linear in its length no matter what it
# contains.
_NAME = re.compile(r"^[A-Za-z0-9._-]+")
_SPEC = re.compile(r"^\s*(?P<op>[<>=!~]=?)\s*(?P<version>[^,;\s]+)\s*,?")
_PIN = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)==(?P<version>[^\s\\]+)$")
_PY_MARKER = re.compile(
    r"""python_version\s*(?P<op>[<>=!]=?)\s*['"](?P<version>[0-9.]+)['"]"""
)


def _normalize(name):
    """PEP 503 normalisation, so Flask/flask and typing_extensions match."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _release(version):
    """The numeric release tuple. Fails loudly on anything it cannot compare."""
    core = version.split("+", 1)[0]
    parts = core.split(".")
    out = []
    for part in parts:
        if not part.isdigit():
            # A pre/post/dev segment would need real PEP 440 handling. Nothing
            # in this closure has one; refuse rather than compare it wrongly.
            raise AssertionError(
                "cannot compare non-numeric version segment %r in %r; this "
                "guard needs extending before such a pin lands" % (part, version)
            )
        out.append(int(part))
    return tuple(out)


def _pad(left, right):
    width = max(len(left), len(right))
    return left + (0,) * (width - len(left)), right + (0,) * (width - len(right))


def _satisfies(version, op, bound):
    got, want = _pad(_release(version), _release(bound))
    if op == ">=":
        return got >= want
    if op == ">":
        return got > want
    if op == "<=":
        return got <= want
    if op == "<":
        return got < want
    if op == "==":
        return got == want
    if op == "!=":
        return got != want
    raise AssertionError("unhandled specifier operator %r" % op)


def image_python_version():
    """The interpreter the image runs, read from the Dockerfile's FROM line.

    Read rather than hardcoded so that a base-image bump moves this guard's
    marker evaluation with it instead of leaving it asserting about 3.14
    forever.
    """
    with open(DOCKERFILE, encoding="utf-8") as handle:
        for line in handle:
            match = re.match(r"^FROM\s+python:(?P<version>[0-9]+\.[0-9]+)", line)
            if match:
                return match.group("version")
    raise AssertionError("no `FROM python:<major>.<minor>` line in Dockerfile")


def _marker_applies(marker, py_version):
    """True when a `python_version` marker holds for the image interpreter.

    Only `python_version` markers appear in requirements.txt. Any other marker
    is treated as applying, which is the safe direction: it can only demand
    that a package be pinned, never excuse one.
    """
    if not marker:
        return True
    match = _PY_MARKER.search(marker)
    if not match:
        return True
    return _satisfies(py_version, match.group("op"), match.group("version"))


def parse_requirements():
    """[(name, [(op, version)], marker)] for every real line in requirements.txt."""
    entries = []
    with open(REQUIREMENTS, encoding="utf-8") as handle:
        for raw in handle:
            # Comment off, then the environment marker, then name, then each
            # specifier in turn -- see the patterns above for why it is stepwise.
            line = raw.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            body, _, marker = line.partition(";")
            body = body.strip()
            name_match = _NAME.match(body)
            assert name_match, "unparsed requirements.txt line: %r" % line
            rest = body[name_match.end():]
            specs = []
            while rest.strip():
                spec_match = _SPEC.match(rest)
                assert spec_match, (
                    "unparsed specifier %r in requirements.txt line: %r" % (rest, line)
                )
                specs.append(
                    (spec_match.group("op"), spec_match.group("version"))
                )
                rest = rest[spec_match.end():]
            entries.append((name_match.group(0), specs, marker.strip()))
    return entries


def parse_pinned():
    """{normalized name: version} plus the hash count for each pin."""
    pins = {}
    hashes = {}
    current = None
    with open(PINNED, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # A continued line ends in a backslash; drop it first so the
            # patterns above can stay anchored at both ends.
            if line.endswith("\\"):
                line = line[:-1].rstrip()
            if line.startswith("--hash="):
                assert current, "--hash line before any pin: %r" % line
                hashes[current] = hashes.get(current, 0) + 1
                continue
            match = _PIN.match(line)
            assert match, "unparsed docker-runtime.txt line: %r" % line
            current = _normalize(match.group("name"))
            assert current not in pins, "%s pinned twice" % current
            pins[current] = match.group("version")
    return pins, hashes


def test_every_requirement_is_pinned_and_satisfied():
    """Each requirements.txt entry that applies on the image's interpreter is pinned."""
    py_version = image_python_version()
    pins, _ = parse_pinned()
    missing = []
    violated = []
    for name, specs, marker in parse_requirements():
        if not _marker_applies(marker, py_version):
            continue
        key = _normalize(name)
        if key not in pins:
            missing.append(name)
            continue
        for op, bound in specs:
            if not _satisfies(pins[key], op, bound):
                violated.append(
                    "%s is pinned at %s, which does not satisfy %s%s"
                    % (name, pins[key], op, bound)
                )
    assert not missing, (
        "requirements.txt names %s, which .github/requirements/docker-runtime.txt "
        "does not pin, so the image would not install it. Regenerate the set "
        "(see that file's header)." % ", ".join(sorted(missing))
    )
    assert not violated, (
        "the pinned set no longer satisfies requirements.txt:\n  "
        + "\n  ".join(sorted(violated))
    )


def test_every_pin_is_exact_and_carries_a_hash():
    """--require-hashes is only worth as much as the hashes actually present."""
    pins, hashes = parse_pinned()
    assert pins, "docker-runtime.txt pins nothing"
    unhashed = sorted(name for name in pins if not hashes.get(name))
    assert not unhashed, (
        "pinned with no --hash line, which --require-hashes would reject at "
        "build time: %s" % ", ".join(unhashed)
    )


def test_dockerfile_installs_the_pinned_set_with_require_hashes():
    """The wiring is the point; a pin no layer installs is decoration."""
    with open(DOCKERFILE, encoding="utf-8") as handle:
        dockerfile = handle.read()
    assert ".github/requirements/docker-runtime.txt" in dockerfile, (
        "Dockerfile does not COPY the pinned runtime set"
    )
    assert re.search(
        r"pip install[^\n]*--require-hashes[^\n]*docker-runtime\.txt", dockerfile
    ), "Dockerfile does not install docker-runtime.txt with --require-hashes"
    assert not re.search(
        r"^RUN pip install[^\n]*-r requirements\.txt", dockerfile, re.M
    ), (
        "the Dockerfile installs requirements.txt directly again, which "
        "re-introduces the unpinned resolve docker-runtime.txt replaced"
    )


# -- the second pinned set: setup.py's install_requires -----------------------
#
# requirements.txt is not install_requires. The guards above hold
# docker-runtime.txt to the first; these hold docker-package.txt, together with
# it, to the second -- the manifest the WHEEL declares and the `pip install -e .`
# layer therefore resolves.
#
# The marker evaluation is stricter here than for requirements.txt. That file
# carries only `python_version` markers, so an unrecognised one can be treated
# as applying (the safe direction). install_requires carries
# `python_full_version` too, and compound `A and B` clauses, so an unrecognised
# marker fails rather than guesses -- the same rule
# tests/test_selfhosted_runtime_pin.py applies to the signed release image's
# copy of this closure.
PACKAGE_PINNED = os.path.join(
    REPO_ROOT, ".github", "requirements", "docker-package.txt"
)
SETUP_PY = os.path.join(REPO_ROOT, "setup.py")

_CLAUSE = re.compile(
    r"""^\s*(?P<var>python_version|python_full_version)\s*"""
    r"""(?P<op>[<>=!]=?)\s*['"](?P<version>[0-9.]+)['"]\s*$"""
)


def _install_requires_marker_applies(marker, py_version):
    """True when every clause of an install_requires marker holds for the image."""
    if not marker:
        return True
    for clause in marker.split(" and "):
        match = _CLAUSE.match(clause)
        assert match, (
            "unparsed environment marker %r in setup.py install_requires; this "
            "guard needs extending before such a pin lands" % marker
        )
        left = py_version
        if match.group("var") == "python_full_version":
            # `3.15` compares as `3.15.0` against a patch-level bound. Every
            # full-version marker in install_requires is a py3.9 boundary, so
            # the patch digit only ever decides 3.9.0/3.9.1 vs 3.9.2.
            left = py_version + ".0"
        if not _satisfies(left, match.group("op"), match.group("version")):
            return False
    return True


def install_requires():
    """The literal install_requires list from setup.py."""
    import ast

    with open(SETUP_PY, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", None) != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == "install_requires":
                return list(ast.literal_eval(keyword.value))
    raise AssertionError("no literal install_requires= in setup.py")


def _parse_pin_file(path, label):
    """({normalized name: version}, {normalized name: hash count}) for a pin set."""
    pins = {}
    hashes = {}
    current = None
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("\\"):
                line = line[:-1].rstrip()
            if line.startswith("--hash="):
                assert current, "--hash line before any pin: %r" % line
                assert re.match(r"^--hash=sha256:[0-9a-f]{64}$", line), (
                    "a pin must be hashed with a full sha256: %r" % line
                )
                hashes[current] = hashes.get(current, 0) + 1
                continue
            match = _PIN.match(line)
            assert match, "unparsed %s line: %r" % (label, line)
            current = _normalize(match.group("name"))
            assert current not in pins, "%s pinned twice in %s" % (current, label)
            pins[current] = match.group("version")
    return pins, hashes


def _parse_install_requirement(raw):
    """(name, [(op, version)], marker) for one install_requires entry."""
    body, _, marker = raw.partition(";")
    body = body.strip()
    name_match = _NAME.match(body)
    assert name_match, "unparsed install_requires entry: %r" % raw
    rest = body[name_match.end():]
    specs = []
    while rest.strip():
        spec_match = _SPEC.match(rest)
        assert spec_match, "unparsed specifier %r in %r" % (rest, raw)
        specs.append((spec_match.group("op"), spec_match.group("version")))
        rest = rest[spec_match.end():]
    return name_match.group(0), specs, marker.strip()


def test_every_install_requires_entry_is_pinned_by_one_of_the_two_sets():
    """Nothing the wheel declares is left for `pip install -e .` to resolve."""
    py_version = image_python_version()
    runtime_pins, _ = parse_pinned()
    package_pins, _ = _parse_pin_file(PACKAGE_PINNED, "docker-package.txt")
    pins = dict(runtime_pins)
    pins.update(package_pins)
    missing = []
    violated = []
    for raw in install_requires():
        name, specs, marker = _parse_install_requirement(raw)
        if not _install_requires_marker_applies(marker, py_version):
            continue
        key = _normalize(name)
        if key not in pins:
            missing.append(name)
            continue
        for op, bound in specs:
            if not _satisfies(pins[key], op, bound):
                violated.append(
                    "%s is pinned at %s, which does not satisfy %s%s"
                    % (name, pins[key], op, bound)
                )
    assert not missing, (
        "setup.py install_requires names %s on Python %s, which neither "
        ".github/requirements/docker-runtime.txt nor "
        ".github/requirements/docker-package.txt pins -- so the image's "
        "`pip install -e .` layer resolves it live against the index with no "
        "hash. Add it to docker-package.txt (see that file's header)."
        % (", ".join(sorted(missing)), py_version)
    )
    assert not violated, (
        "the pinned sets no longer satisfy setup.py install_requires:\n  "
        + "\n  ".join(sorted(violated))
    )


def test_the_two_pinned_sets_do_not_pin_the_same_name():
    """One name, one version: two layers must not install it twice."""
    runtime_pins, _ = parse_pinned()
    package_pins, _ = _parse_pin_file(PACKAGE_PINNED, "docker-package.txt")
    both = sorted(set(runtime_pins) & set(package_pins))
    assert not both, (
        "pinned in BOTH docker-runtime.txt and docker-package.txt: %s. The two "
        "files are installed as consecutive layers, so a name in both can drift "
        "into two different versions and the later layer silently replaces the "
        "earlier one." % ", ".join(both)
    )


def test_every_package_pin_is_exact_and_carries_a_hash():
    """--require-hashes is only worth as much as the hashes actually present."""
    pins, hashes = _parse_pin_file(PACKAGE_PINNED, "docker-package.txt")
    assert pins, "docker-package.txt pins nothing"
    unhashed = sorted(name for name in pins if not hashes.get(name))
    assert not unhashed, (
        "pinned with no --hash line, which --require-hashes would reject at "
        "build time: %s" % ", ".join(unhashed)
    )


def test_dockerfile_installs_the_package_set_before_the_editable_install():
    """A pin that lands after the layer it protects protects nothing."""
    with open(DOCKERFILE, encoding="utf-8") as handle:
        dockerfile = handle.read()
    assert ".github/requirements/docker-package.txt" in dockerfile, (
        "Dockerfile does not COPY the pinned install_requires set"
    )
    install = re.search(
        r"pip install[^\n]*--require-hashes[^\n]*docker-package\.txt", dockerfile
    )
    assert install, (
        "Dockerfile does not install docker-package.txt with --require-hashes"
    )
    editable = re.search(r"^RUN pip install[^\n]*(?<!-r )-e \.", dockerfile, re.M)
    assert editable, "Dockerfile no longer installs the working tree with `-e .`"
    assert install.start() < editable.start(), (
        "docker-package.txt is installed AFTER `pip install -e .`, so that "
        "layer still resolves the wheel's requirements from the index first"
    )
