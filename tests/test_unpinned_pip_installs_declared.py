"""Every unpinned `pip install` in CI, the images and the installer is declared.

`--require-hashes` is how this repo installs almost everything: 68 install
sites across the workflows, the Dockerfiles and the composite actions resolve
from a hash-pinned set in `.github/requirements/`, so a compromised or yanked
release cannot change what a job runs. Dozens of hardening PRs put those pins
in place one workflow at a time.

Twenty install sites are deliberately NOT pinned, and they fall into two
groups.

Ten of them install this repository's own working tree or a wheel built
earlier in the same job -- `pip install .`, `pip install -e .`,
`pip install dist/clawmetry-*.whl`. There is nothing to pin: the artifact is
the code under test, it never came from an index, and a hash would describe
the commit rather than verify it. Those are recognised structurally by
`_is_local_artifact` below and need no bookkeeping.

The other ten resolve from an index without a hash, on purpose, and each one
has a reason that is specific enough to write down. The release canary
installs the exact version just published, because proving a published release
installs is the entire job. The SBOM step installs `requirements.txt`
unpinned, because an SBOM of a frozen environment would describe the frozen
file instead of what `pip install clawmetry` produces today. The cross-repo
handoff installs clawmetry-cloud's requirements, which live in another
repository and move when it moves, so no file here could carry their hashes.
Those ten are listed in `ACCEPTED` with the reason each is accepted.

They are the pip half of this repository's remaining OSSF Scorecard
Pinned-Dependencies findings, and they are why that probe will not reach 10.
That is a deliberate ceiling, not a backlog.

What was missing is a floor. Every one of those twenty sites already carried
an inline comment explaining itself, and several carry an explicit "do not
'fix' this" note -- but nothing checked the set. An eleventh unpinned
`pip install` added to a workflow next week would resolve from the network
with no hash, draw a sixteenth Scorecard finding, and pass every check in this
repository, because the only thing standing between the pinned installs and
the unpinned ones was a reviewer remembering which was which. That is the same
gap `tests/test_pip_bootstrap_py39_pin.py` was written to close, for the same
reason: a refusal a reviewer has to remember is the weakest kind there is.

So the rule is checked here instead:

  * a new unpinned `pip install` that is neither a local artifact nor listed
    in `ACCEPTED` fails, and the failure says to add `--require-hashes` or to
    declare it with a reason;
  * an `ACCEPTED` entry that no longer matches anything in the tree also
    fails, so the list cannot rot into a description of a repository that has
    moved on.

Only `pip install` is in scope. Action refs are already ratcheted by
`tests/test_action_refs_pinned.py`, and npm installs by the committed
lockfiles those directories carry.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files whose shell bodies are scanned. Workflows and composite actions run
# with a job token; the Dockerfiles build what ships; install.sh is what a
# user pipes into a shell.
WORKFLOW_DIRS = (
    os.path.join(".github", "workflows"),
    os.path.join(".github", "actions"),
)
SHELL_FILES = (
    "Dockerfile",
    os.path.join("deploy", "self-hosted", "Dockerfile.release"),
    os.path.join("clawhub-plugin", "install.sh"),
)

# `pip install` only counts at a command position. Matching the bare substring
# anywhere would fire on the many comments and `echo` strings in these files
# that quote a pip command while explaining one -- including, recursively, the
# comments this guard exists to protect.
_SEPARATORS = re.compile(r"\|\||&&|;|\||\n")
_LEADING_WORDS = re.compile(
    r"^(?:!|\(|\{|RUN|if|then|elif|else|do|while|until|time|sudo|command|exec|env)\s+"
)
_PIP_INSTALL = re.compile(
    r"^(?:\S*/)?(?:python[0-9.]*\s+-m\s+)?(?:\S*/)?pip[0-9.]*\s+install\b(?P<args>.*)$"
)

# A flag that takes a separate value, so that value is not an install target.
_FLAGS_WITH_VALUE = {
    "-r", "--requirement", "-c", "--constraint", "-i", "--index-url",
    "--extra-index-url", "-f", "--find-links", "--target", "-t",
    "--python-version", "--platform", "--abi", "--implementation",
    "--prefix", "--root", "--cache-dir", "--log", "--proxy",
    "--progress-bar", "--report", "--config-settings",
}

# A target that is this repository's own tree or a wheel built in the same job.
_LOCAL_ARTIFACT = re.compile(r"^(?:\.|\./.*|.*\.whl|.*/\*\.whl)$")


def _strip_comment(line):
    """Drop a trailing `#` comment, honouring quotes."""
    kept = []
    quote = None
    for char in line:
        if quote is not None:
            kept.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            kept.append(char)
            continue
        if char == "#":
            break
        kept.append(char)
    return "".join(kept)


def _pip_install_commands(script):
    """Yield (command, args) for every `pip install` at a command position."""
    for raw_line in script.splitlines():
        line = _strip_comment(raw_line)
        for segment in _SEPARATORS.split(line):
            segment = segment.strip()
            previous = None
            while segment != previous:
                previous = segment
                segment = _LEADING_WORDS.sub("", segment).strip()
            match = _PIP_INSTALL.match(segment)
            if match is not None:
                yield segment, match.group("args").strip()


def _targets(args):
    """The install targets in an argument string, with flags removed."""
    targets = []
    tokens = args.split()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in _FLAGS_WITH_VALUE:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        # Shell redirections are not targets.
        if token.startswith(("2>", ">", "1>")):
            index += 1
            continue
        targets.append(token)
        index += 1
    return targets


def _is_local_artifact(args):
    """True when every install target is this tree or a wheel built here.

    `pip install .`, `pip install -e .` and `pip install dist/*.whl` have
    nothing to pin: the artifact is the commit under test. A bare
    `pip install` with no target at all (`-r` only) is not local.
    """
    if "-r" in args.split() or "--requirement" in args.split():
        return False
    targets = _targets(args)
    if not targets:
        return False
    return all(_LOCAL_ARTIFACT.match(target) for target in targets)


def _normalise(args):
    """A stable key for an install, independent of its line number."""
    return " ".join(args.split())


# Every unpinned, index-resolving `pip install` in the tree, with the reason it
# is accepted. Keyed on (path, exact argument string) rather than a line
# number, so moving a step does not rewrite this file.
#
# Adding an entry here is a deliberate act: it says "this install resolves from
# the network with no hash, and that is correct". If you cannot write the
# reason, use `--require-hashes` and a set under `.github/requirements/`.
ACCEPTED = {
    (
        os.path.join(".github", "workflows", "api-latency-smoke.yml"),
        "--no-cache-dir clawmetry",
    ): (
        "The `pypi` cell of a matrix whose other cell installs the wheel just "
        "built. Comparing the published release against the local build is "
        "what the matrix exists to do, so pinning either side removes the "
        "comparison."
    ),
    (
        os.path.join(".github", "workflows", "conformance-heartbeat.yml"),
        "--no-cache-dir clawmetry",
    ): (
        "The heartbeat installs the CURRENT published release and asserts it "
        "imports and runs. A pin would test a release nobody is installing. "
        "pip itself is bootstrapped from a hash-pinned set in the same step, "
        "so only the package under test is unpinned. Two jobs in this file "
        "(the per-OS matrix and the single-Python cell) run the same install."
    ),
    (
        os.path.join(".github", "workflows", "cross-repo-handoff.yml"),
        "-r cloud/requirements.txt",
    ): (
        "clawmetry-cloud's requirements, from the checkout of THAT repository. "
        "The file lives in another repo and moves when it moves, so no file "
        "here could carry its hashes. Best-effort already (`|| true`): the "
        "suite stubs what it cannot import."
    ),
    (
        os.path.join(".github", "workflows", "cross-repo-handoff.yml"),
        '"$(python cloud/tests/e2e_browser/oss_pin.py)"',
    ): (
        "The OSS pin is computed at run time from cloud/Dockerfile and comes "
        "back as `clawmetry==X.Y.Z`, so the version IS pinned -- by the file "
        "the cloud image builds from. A hash here would have to be updated in "
        "lockstep with another repository's Dockerfile."
    ),
    (
        os.path.join(".github", "workflows", "pr-screenshots.yml"),
        "-r head/requirements.txt",
    ): (
        "The PR's own requirements, from its own checkout -- the thing under "
        "test. The harness standing around it (duckdb, requests, Playwright) "
        "comes from hash-pinned sets in the same step."
    ),
    (
        os.path.join(".github", "workflows", "release-canary.yml"),
        '--no-cache-dir "clawmetry==${VERSION}"',
    ): (
        "The canary installs the exact version just published, from PyPI, to "
        "prove that release installs. The version is pinned; a hash cannot be "
        "because the artifact did not exist when this file was written."
    ),
    (
        os.path.join(".github", "workflows", "release-on-merge.yml"),
        '--quiet --no-cache-dir "clawmetry==$NEW" 2>/dev/null',
    ): (
        "The post-publish propagation check, which retries until PyPI's "
        "/simple/ index serves the version this job just uploaded. Same "
        "reason as the canary: the artifact is newer than this file."
    ),
    (
        os.path.join(".github", "workflows", "supply-chain.yml"),
        "--quiet -r requirements.txt",
    ): (
        "The SBOM step. An SBOM of a frozen, hash-pinned environment would "
        "describe the pin file instead of describing what `pip install "
        "clawmetry` actually resolves to today, which is the only question a "
        "published SBOM is there to answer."
    ),
    (
        os.path.join("deploy", "self-hosted", "Dockerfile.release"),
        '--no-cache-dir "$1[otel]"',
    ): (
        "`$1` is the single locally built wheel the preceding `set --` glob "
        "resolved out of /tmp/dist, installed with the OTLP extra. A local "
        "wheel path that a scanner cannot see through a shell variable."
    ),
    (
        os.path.join("clawhub-plugin", "install.sh"),
        "--quiet --upgrade clawmetry 2>/dev/null",
    ): (
        "The end-user installer. Installing the latest published clawmetry is "
        "the product; pinning it would ship users a frozen version."
    ),
}


def _scan():
    """Every pip install in the scanned files, as (path, args, command)."""
    yaml = pytest.importorskip("yaml")
    found = []

    def walk(node, on_run):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "run" and isinstance(value, str):
                    on_run(value)
                else:
                    walk(value, on_run)
        elif isinstance(node, list):
            for value in node:
                walk(value, on_run)

    for directory in WORKFLOW_DIRS:
        absolute = os.path.join(REPO_ROOT, directory)
        for root, _dirs, files in os.walk(absolute):
            for name in sorted(files):
                if not name.endswith((".yml", ".yaml")):
                    continue
                path = os.path.join(root, name)
                relative = os.path.relpath(path, REPO_ROOT)
                with open(path, encoding="utf-8") as handle:
                    document = yaml.safe_load(handle)
                scripts = []
                walk(document, scripts.append)
                for script in scripts:
                    for command, args in _pip_install_commands(script):
                        found.append((relative, args, command))

    for relative in SHELL_FILES:
        path = os.path.join(REPO_ROOT, relative)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            # Join Dockerfile/shell line continuations so a wrapped command
            # is read as one.
            source = handle.read().replace("\\\n", " ")
        for command, args in _pip_install_commands(source):
            found.append((relative, args, command))

    return found


def _unpinned():
    """Index-resolving pip installs: not hash-pinned, not a local artifact."""
    rows = []
    for relative, args, command in _scan():
        if "--require-hashes" in args:
            continue
        if _is_local_artifact(args):
            continue
        rows.append((relative, _normalise(args), command))
    return rows


def test_pip_installs_are_pinned_or_declared():
    """No unpinned pip install may appear without a declared reason."""
    undeclared = sorted(
        {
            (relative, args)
            for relative, args, _command in _unpinned()
            if (relative, args) not in ACCEPTED
        }
    )
    assert not undeclared, (
        "These `pip install` commands resolve from an index with no hash and "
        "are not declared:\n"
        + "\n".join(f"  {path}\n      pip install {args}" for path, args in undeclared)
        + "\n\nInstall it with `--require-hashes` from a set under "
        ".github/requirements/, or -- if resolving unpinned is the point of "
        "the step -- add it to ACCEPTED in "
        "tests/test_unpinned_pip_installs_declared.py with the reason."
    )


def test_accepted_entries_still_exist():
    """A declared exception must still describe something in the tree."""
    live = {(relative, args) for relative, args, _command in _unpinned()}
    stale = sorted(key for key in ACCEPTED if key not in live)
    assert not stale, (
        "These ACCEPTED entries match no `pip install` in the tree any more. "
        "The install was pinned, moved or deleted -- remove the entry:\n"
        + "\n".join(f"  {path}\n      pip install {args}" for path, args in stale)
    )


def test_hash_pinned_installs_are_the_norm():
    """The pinned majority is the premise of this guard; assert it holds.

    If `--require-hashes` installs ever stopped outnumbering unpinned ones by
    a wide margin, the ACCEPTED list would have quietly become the rule rather
    than the exception, and this file would be documenting a regression
    instead of guarding against one.
    """
    pinned = [row for row in _scan() if "--require-hashes" in row[1]]
    assert len(pinned) > 3 * len(_unpinned()), (
        f"{len(pinned)} hash-pinned installs against {len(_unpinned())} "
        "unpinned: the ratio this guard assumes no longer holds."
    )


def test_every_accepted_entry_has_a_reason():
    """An entry with an empty or throwaway reason is not a declaration."""
    for key, reason in ACCEPTED.items():
        assert reason and len(reason.strip()) > 40, (
            f"ACCEPTED entry {key} needs a reason that explains why resolving "
            "unpinned is correct for that step."
        )
