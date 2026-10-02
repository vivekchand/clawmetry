"""The signed self-hosted image's runtime pin must still match setup.py.

`deploy/self-hosted/Dockerfile.release` installs the published clawmetry wheel
as `pip install "$1[otel]"`. Two hash-pinned sets stand in front of that line so
pip finds every name already satisfied and resolves none of them itself:

    otel-requirements.txt      the `[otel]` extra (opentelemetry-proto, protobuf)
    runtime-requirements.txt   the wheel's own install_requires

This guard is for the second one. Its drift is silent and one-directional, the
same shape as the root image's (tests/test_docker_runtime_pin.py): add a
dependency to setup.py's install_requires, and the pinned set simply does not
carry it -- so the wheel install resolves that one name live from the index and
`docker build` still succeeds. The pin quietly stops being a pin, and the
signature and SBOM on the published image go on attesting to bytes that are no
longer reproducible.

It matters more here than for the root image. container-image.yml pushes this
one to ghcr.io/vivekchand/clawmetry, cosign signs the index and every platform
manifest, and an SPDX SBOM is attested per platform digest.

Pure parsing -- no network, no pip -- so it runs in the Syntax & Lint job on
Python 3.9 alongside the other drift guards. The hashes themselves are checked
by pip at build time (`--require-hashes`), and container-image.yml builds this
image on both published architectures for every PR touching this directory, so
an unbuildable set fails there rather than here.

Named explicitly in .github/workflows/ci.yml because this repo's CI runs FILE
LISTS, not `pytest tests/`: a guard added without a line there runs in no job
at all.
"""
import ast
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP_PY = os.path.join(REPO_ROOT, "setup.py")
SELF_HOSTED = os.path.join(REPO_ROOT, "deploy", "self-hosted")
PINNED = os.path.join(SELF_HOSTED, "runtime-requirements.txt")
DOCKERFILE = os.path.join(SELF_HOSTED, "Dockerfile.release")

# The stepwise patterns and the version comparison are the root image's guard,
# imported rather than re-written: they are anchored and applied once per step
# so a requirement line costs time linear in its length (one combined pattern
# backtracks catastrophically -- see that file's comment).
_sibling = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "test_docker_runtime_pin.py")


def _helpers():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_docker_runtime_pin", _sibling)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# A marker clause, e.g. `python_version >= "3.10"` or
# `python_full_version < "3.9.2"`. install_requires uses only these two
# variables; anything else makes this guard fail rather than guess.
_CLAUSE = re.compile(
    r"""^\s*(?P<var>python_version|python_full_version)\s*"""
    r"""(?P<op>[<>=!]=?)\s*['"](?P<version>[0-9.]+)['"]\s*$"""
)


def image_python_version():
    """The interpreter the image runs, read from Dockerfile.release's FROM line.

    Read rather than hardcoded so a base-image bump moves this guard's marker
    evaluation with it instead of leaving it asserting about 3.14 forever.
    """
    with open(DOCKERFILE, encoding="utf-8") as handle:
        for line in handle:
            match = re.match(r"^FROM\s+python:(?P<version>[0-9]+\.[0-9]+)", line)
            if match:
                return match.group("version")
    raise AssertionError("no `FROM python:<major>.<minor>` line in Dockerfile.release")


def _marker_applies(marker, py_version, satisfies):
    """True when an install_requires marker holds for the image interpreter.

    `python_full_version` is compared against <major>.<minor>.0: every
    full-version marker in install_requires is a py3.9 boundary, so the patch
    component of the image's interpreter cannot change the answer. Clauses are
    joined with `and` only; an `or` would need real precedence handling, so it
    fails loudly instead.
    """
    if not marker:
        return True
    assert " or " not in marker, (
        "this guard handles `and`-joined markers only, got %r" % marker
    )
    for clause in marker.split(" and "):
        match = _CLAUSE.match(clause)
        assert match, (
            "unparsed environment marker %r in setup.py install_requires; this "
            "guard needs extending before such a requirement lands" % clause
        )
        left = py_version
        if match.group("var") == "python_full_version":
            left = py_version + ".0"
        if not satisfies(left, match.group("op"), match.group("version")):
            return False
    return True


def install_requires():
    """The literal install_requires list from setup.py."""
    tree = ast.parse(open(SETUP_PY, encoding="utf-8").read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", None) != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == "install_requires":
                return list(ast.literal_eval(keyword.value))
    raise AssertionError("no literal install_requires= in setup.py")


def parse_requirement(raw, helpers):
    """(name, [(op, version)], marker) for one install_requires entry."""
    body, _, marker = raw.partition(";")
    body = body.strip()
    name_match = helpers._NAME.match(body)
    assert name_match, "unparsed install_requires entry: %r" % raw
    rest = body[name_match.end():]
    specs = []
    while rest.strip():
        spec_match = helpers._SPEC.match(rest)
        assert spec_match, "unparsed specifier %r in %r" % (rest, raw)
        specs.append((spec_match.group("op"), spec_match.group("version")))
        rest = rest[spec_match.end():]
    return name_match.group(0), specs, marker.strip()


def parse_pinned(helpers):
    """({normalized name: version}, {normalized name: hash count})."""
    pins = {}
    hashes = {}
    current = None
    with open(PINNED, encoding="utf-8") as handle:
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
            match = helpers._PIN.match(line)
            assert match, "unparsed runtime-requirements.txt line: %r" % line
            current = helpers._normalize(match.group("name"))
            assert current not in pins, "%s pinned twice" % current
            pins[current] = match.group("version")
    return pins, hashes


def test_every_install_requires_entry_is_pinned_and_satisfied():
    """Each install_requires entry that applies on the image's interpreter is pinned."""
    helpers = _helpers()
    py_version = image_python_version()
    pins, _ = parse_pinned(helpers)

    missing = []
    violated = []
    for raw in install_requires():
        name, specs, marker = parse_requirement(raw, helpers)
        if not _marker_applies(marker, py_version, helpers._satisfies):
            continue
        key = helpers._normalize(name)
        if key not in pins:
            missing.append(raw)
            continue
        for op, bound in specs:
            if not helpers._satisfies(pins[key], op, bound):
                violated.append(
                    "%s is pinned at %s, which does not satisfy %s%s"
                    % (name, pins[key], op, bound)
                )
    assert not missing, (
        "setup.py install_requires names %s on Python %s, which "
        "deploy/self-hosted/runtime-requirements.txt does not pin. The signed "
        "image would resolve those live from the index at build time. "
        "Regenerate with `python3 scripts/resolve_selfhosted_runtime_pins.py "
        "--write`." % (", ".join(sorted(missing)), py_version)
    )
    assert not violated, "\n".join(violated)


def test_requirements_excluded_by_marker_are_not_pinned():
    """A dependency the image's interpreter does not ask for must not be in the set.

    `zstandard` is the live case: install_requires carries it only for
    `python_version < "3.14"`, so on this image the wheel never asks for it and
    pinning it would put a package in a published server image that nothing
    imports.
    """
    helpers = _helpers()
    py_version = image_python_version()
    pins, _ = parse_pinned(helpers)

    applies = set()
    declared = set()
    for raw in install_requires():
        name, _, marker = parse_requirement(raw, helpers)
        key = helpers._normalize(name)
        declared.add(key)
        if _marker_applies(marker, py_version, helpers._satisfies):
            applies.add(key)

    # Only names setup.py declares are judged here. Everything else in the set
    # is a transitive dependency, which --require-hashes requires and which
    # this guard has no list to check against.
    unwanted = sorted((declared - applies) & set(pins))
    assert not unwanted, (
        "deploy/self-hosted/runtime-requirements.txt pins %s, which setup.py "
        "asks for only on an interpreter this image does not run (Python %s)."
        % (", ".join(unwanted), py_version)
    )


def test_every_pin_carries_a_hash():
    """A pin with no hash silently disables --require-hashes for that package."""
    helpers = _helpers()
    pins, hashes = parse_pinned(helpers)
    assert pins, "runtime-requirements.txt pins nothing"
    unhashed = sorted(name for name in pins if not hashes.get(name))
    assert not unhashed, (
        "these pins carry no --hash line: %s" % ", ".join(unhashed)
    )


def test_dockerfile_installs_the_set_before_the_wheel():
    """The pinned set must be installed with --require-hashes, ahead of the wheel.

    Order is the whole mechanism: installed first, pip finds every name
    satisfied when the wheel goes in and resolves none of them. Installed after,
    the wheel's own resolve has already happened and the pin buys nothing.
    """
    body = open(DOCKERFILE, encoding="utf-8").read()
    # Comments in this file discuss the wheel install, so judge the directives
    # only.
    directives = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )

    assert "COPY runtime-requirements.txt" in directives, (
        "Dockerfile.release does not COPY runtime-requirements.txt into the build"
    )
    pin_install = re.search(
        r"pip install[^\n]*--require-hashes[^\n]*runtime-requirements\.txt", directives
    )
    assert pin_install, (
        "Dockerfile.release does not install runtime-requirements.txt with "
        "--require-hashes"
    )
    wheel_install = re.search(r'pip install[^\n]*"\$1\[otel\]"', directives)
    assert wheel_install, "Dockerfile.release does not install the wheel as $1[otel]"
    assert pin_install.start() < wheel_install.start(), (
        "runtime-requirements.txt is installed AFTER the wheel, so the wheel's "
        "own dependency resolve still happens against the index"
    )
