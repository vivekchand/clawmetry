"""clawmetry/repo_readiness.py — how legible is this repo to an agent?

Before you blame the agent, look at what you handed it. A repo with no
instruction file, no discoverable test command and no lint gate produces
stuck loops, and ClawMetry already has the detector data to show that
correlation on the same screen.

This module scores a repository on the things an agent actually needs to
find its way around:

    instruction file · instruction loaded · test command · build command
    lint gate · CI config · agent assets (skills / commands / sub-agents)

Design rules this module is bound by
------------------------------------
**ADR-004 posture grading** (the rule the Security tab's posture registry
already follows, recorded on the Local Observability Service blueprint):

* ``fail`` — ONLY a filesystem fact, where "is it honoured?" does not
  arise: a file exists or it does not, a literal byte is in a file or it
  is not. Every failing check here traces to code in this module that
  opened the thing it grades.
* ``warn`` — present but partial, or an inherited default we did not
  measure. An inherited default counts as **unmeasured, not ready**.
* ``unknown`` — **weight 0**. A thing we cannot read at all is reported
  as an explicit unknown that cannot move the grade in either direction.
  A file we lack permission to read, or a runtime that does not report
  what it loaded, lands here. Never a penalty.

**No network calls.** Every input is a filesystem fact in a directory the
caller already named. Nothing here opens a socket, and nothing here runs a
subprocess: we never execute the build we are grading. "Does the build
succeed?" is a question a read-only observer cannot answer without
changing the machine, so the graded check is "is a build command
discoverable", and the execution axis is reported as an honest unknown
unless a detector already observed it.

**Derived, not hand-maintained.** The per-runtime instruction / skills
file names come from ``runtime_memory.project_relative_roots()`` — the same
declarations the Memory and Skills browsers read — so a new runtime flows
in automatically instead of drifting a second copy.

Everything is pure: :func:`score_repo` takes a path and an optional bundle
of already-measured signals, and returns a JSON-ready envelope. It never
raises.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Iterable, Optional

log = logging.getLogger("clawmetry.repo_readiness")

#: Largest config file we will read while probing. Real Makefiles and
#: package.json files are far below this; anything larger is a data file
#: that got named like a config, and reading it is not worth the stall.
_MAX_PROBE_BYTES = 512 * 1024

#: How deep to look for a git root when the caller hands us a subdirectory.
_MAX_GIT_WALK = 24

# ── status vocabulary ──────────────────────────────────────────────────────
PASS = "pass"
WARN = "warn"
FAIL = "fail"
UNKNOWN = "unknown"


def _check(cid: str, label: str, status: str, detail: str,
           remediation: Optional[str], weight: int, *,
           evidence: Optional[str] = None,
           severity: str = "medium") -> dict:
    """One graded check.

    ``evidence`` names the file this module actually opened to reach the
    verdict, so a reader can tell a measured result from a shipped
    constant. An ``unknown`` check is forced to weight 0 here rather than
    at every call site, so no future check can accidentally penalise the
    operator for something we could not read.
    """
    return {
        "id": cid,
        "label": label,
        "status": status,
        "detail": detail,
        "remediation": remediation,
        "severity": severity,
        "weight": 0 if status == UNKNOWN else int(weight),
        "evidence": evidence,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Filesystem probes. Every one of these opens (or stats) a real path and
# reports what it found there. None of them run anything.
# ═══════════════════════════════════════════════════════════════════════════

class _Unreadable(Exception):
    """A path exists but we could not read it — grade UNKNOWN, weight 0."""


def _probe_key(path: str):
    """Identity of a path for de-duplication.

    ``Makefile`` and ``makefile`` are the SAME file on macOS and Windows,
    so probing both would report one Makefile twice. Case-folding the
    string is not enough (``realpath`` preserves the case you asked for,
    and ``normcase`` is the identity on POSIX), so identity comes from the
    inode when we can stat it. On a case-sensitive filesystem the two
    names are genuinely different files with different inodes and both are
    still reported, which is correct.
    """
    try:
        st = os.stat(path)
        return (st.st_dev, st.st_ino)
    except OSError:
        return os.path.normcase(os.path.abspath(path))


def _read_text(path: str) -> Optional[str]:
    """Read a small text file. ``None`` when it does not exist.

    Raises :class:`_Unreadable` when the path is there but unreadable, so
    the caller can grade an explicit zero-weight unknown instead of
    reporting "absent" for something that may well be present.
    """
    try:
        if not os.path.isfile(path):
            return None
    except OSError as e:
        raise _Unreadable(str(e))
    try:
        with open(path, "rb") as fh:
            raw = fh.read(_MAX_PROBE_BYTES)
    except OSError as e:
        raise _Unreadable(str(e))
    return raw.decode("utf-8", errors="replace")


def _exists(path: str) -> bool:
    try:
        return os.path.exists(path)
    except OSError:
        return False


def _isdir_nonempty(path: str) -> bool:
    try:
        if not os.path.isdir(path):
            return False
        with os.scandir(path) as it:
            for _ in it:
                return True
        return False
    except OSError:
        return False


def _make_targets(text: str) -> set:
    """Target names declared in a Makefile.

    Reads the literal bytes: a line starting at column 0 with
    ``name:`` (not ``.PHONY``, not a variable assignment) declares a
    target. Recipe lines are tab-indented and never match.
    """
    out = set()
    for line in text.splitlines():
        if not line or line[0] in (" ", "\t", "#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.\-/ ]+?)\s*:(?!=)", line)
        if not m:
            continue
        for name in m.group(1).split():
            if name.startswith("."):
                continue
            out.add(name)
    return out


def _package_scripts(text: str) -> Optional[dict]:
    """``scripts`` from a package.json. ``None`` when it will not parse."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    scripts = data.get("scripts")
    return scripts if isinstance(scripts, dict) else {}


def _toml_sections(text: str) -> set:
    """Section headers literally present in a TOML file.

    A deliberate literal-byte scan rather than a TOML parse: Python 3.9 has
    no ``tomllib`` and this repo does not take new dependencies. We only
    ever ask "is this section header in the file", which a scan answers
    exactly.
    """
    return {
        m.group(1).strip()
        for m in re.finditer(r"^\s*\[([^\[\]]+)\]\s*$", text, re.MULTILINE)
    }


def _glob_any(root: str, subdir: str, suffixes: Iterable) -> list:
    """Files directly under ``root/subdir`` with any of ``suffixes``."""
    out = []
    try:
        with os.scandir(os.path.join(root, subdir)) as it:
            for e in it:
                if e.is_file() and any(e.name.endswith(s) for s in suffixes):
                    out.append(subdir + "/" + e.name)
    except OSError:
        return []
    return sorted(out)


def _walk_test_files(root: str, limit: int = 4000) -> bool:
    """Does this repo contain Go test files? (``*_test.go``, capped walk.)"""
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in ("node_modules", "vendor")]
        for fn in filenames:
            seen += 1
            if seen > limit:
                return False
            if fn.endswith("_test.go"):
                return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# The checks
# ═══════════════════════════════════════════════════════════════════════════

#: Catalog "memory" roots that are written BY the agent, not by a person.
#: The catalog is the right source for "where does this runtime read
#: project context", but a few of those roots are the runtime's own
#: transcript or scratch memory. A repo containing `.aider.input.history`
#: has not been documented for an agent; it has merely been used by one, and
#: passing the instruction check on it would be a false pass of exactly the
#: kind ADR-004 exists to stop. A denylist, not an allowlist, so a runtime
#: added tomorrow flows in graded rather than silently ignored.
_AGENT_WRITTEN_ROOTS = frozenset({
    ".aider.chat.history.md",   # aider writes the chat transcript here
    ".aider.input.history",     # aider writes the prompt history here
    ".goose/memory",            # goose's own memory store
    "memory",                   # OpenClaw agent memory directory
    "MEMORY.md",                # OpenClaw agent memory file
})


def _instruction_roots(runtime: Optional[str]) -> list:
    """Project-scoped instruction-file roots, derived from the catalog."""
    try:
        from clawmetry import runtime_memory
        roots = runtime_memory.project_relative_roots(["memory"])
    except Exception as e:  # noqa: BLE001 — never break the score over this
        log.debug("repo-readiness: catalog unavailable: %s", e)
        return []
    roots = [r for r in roots if r["rel"] not in _AGENT_WRITTEN_ROOTS]
    if runtime and runtime not in ("all", "any"):
        roots = [r for r in roots if r["runtime"] == runtime]
    return roots


def _rank_rels(roots: list) -> list:
    """Instruction paths, most widely read first.

    The order is DERIVED: a file eleven runtimes read (``AGENTS.md``) is a
    better thing to suggest than one a single runtime reads, and the catalog
    already knows how many declare each. Hand-picking a favourite here would
    be the drift this module exists to avoid.
    """
    counts: dict = {}
    for spec in roots:
        counts[spec["rel"]] = counts.get(spec["rel"], 0) + 1
    return sorted(counts, key=lambda rel: (-counts[rel], rel))


def _asset_roots(runtime: Optional[str]) -> list:
    try:
        from clawmetry import runtime_memory
        roots = runtime_memory.project_relative_roots(["skills", "commands", "agents"])
    except Exception as e:  # noqa: BLE001
        log.debug("repo-readiness: catalog unavailable: %s", e)
        return []
    if runtime and runtime not in ("all", "any"):
        roots = [r for r in roots if r["runtime"] == runtime]
    return roots


def _present(root: str, rel: str) -> bool:
    """Is this declared root present in the repo, with content?"""
    full = os.path.join(root, rel.replace("/", os.sep))
    try:
        if os.path.isdir(full):
            return _isdir_nonempty(full)
        if os.path.isfile(full):
            return os.path.getsize(full) > 0
    except OSError:
        return False
    return False


def runtime_coverage(root: str, roots: Optional[list] = None) -> list:
    """Which runtimes would find an instruction file in this repo.

    One row per runtime that declares any project-scoped instruction file,
    with the files actually present. This is the per-runtime honesty layer:
    a repo can be perfectly legible to Claude Code and invisible to Cursor,
    and a single node-wide "has instructions" tick would hide that.
    """
    roots = roots if roots is not None else _instruction_roots(None)
    by_rt: dict = {}
    for spec in roots:
        row = by_rt.setdefault(spec["runtime"], {
            "runtime": spec["runtime"],
            "label": spec["runtime_label"],
            "files": [],
            "looked_for": [],
        })
        row["looked_for"].append(spec["rel"])
        if _present(root, spec["rel"]):
            row["files"].append(spec["rel"])
    out = []
    for row in by_rt.values():
        row["has_instructions"] = bool(row["files"])
        row["files"] = sorted(set(row["files"]))
        row["looked_for"] = sorted(set(row["looked_for"]))
        out.append(row)
    out.sort(key=lambda r: (not r["has_instructions"], r["label"].lower()))
    return out


def _check_instruction_file(root: str, runtime: Optional[str],
                            coverage: list) -> dict:
    scoped = runtime and runtime not in ("all", "any")
    found = sorted({f for row in coverage for f in row["files"]})
    if found:
        if scoped:
            detail = "%s reads %s in this repo." % (
                coverage[0]["label"] if coverage else runtime,
                ", ".join(found[:4]))
        else:
            names = [r["label"] for r in coverage if r["has_instructions"]]
            detail = "%s present; read by %s." % (
                ", ".join(found[:4]),
                ", ".join(names[:4]) + (" and more" if len(names) > 4 else ""))
        return _check(
            "instruction_file", "Instruction file", PASS, detail, None, 25,
            evidence=found[0], severity="critical")
    looked = _rank_rels(_instruction_roots(runtime))
    if not looked:
        return _check(
            "instruction_file", "Instruction file", UNKNOWN,
            "No runtime on this machine declares a project instruction file, "
            "so there is nothing to look for.", None, 25, severity="critical")
    hint = ", ".join(looked[:5])
    return _check(
        "instruction_file", "Instruction file", FAIL,
        "No instruction file in this repo. Looked for %s%s."
        % (hint, " and %d more" % (len(looked) - 5) if len(looked) > 5 else ""),
        "Add an instruction file at the repo root (%s) describing what the "
        "project is, how to run it, and the conventions to follow."
        % looked[0],
        25, severity="critical")


def _check_instruction_loaded(root: str, coverage: list,
                              loaded_evidence: Optional[dict]) -> dict:
    """Did the runtime actually load the instruction file it found?

    A file on disk is not a file in the context window. Some runtimes could
    report this; none of the runtimes ClawMetry observes report it today,
    and we do not guess — reading the file ourselves proves only that WE
    read it. So this is an explicit zero-weight unknown with the hook in
    place: pass ``loaded_evidence`` and it grades for real.
    """
    has_file = any(r["has_instructions"] for r in coverage)
    if isinstance(loaded_evidence, dict) and loaded_evidence.get("observed"):
        rts = loaded_evidence.get("runtimes") or []
        return _check(
            "instruction_loaded", "Instruction file actually loaded", PASS,
            "Reported loaded by %s." % (", ".join(rts) or "the runtime"),
            None, 15, evidence=loaded_evidence.get("source"), severity="high")
    if not has_file:
        return _check(
            "instruction_loaded", "Instruction file actually loaded", UNKNOWN,
            "There is no instruction file to load yet.", None, 15,
            severity="high")
    return _check(
        "instruction_loaded", "Instruction file actually loaded", UNKNOWN,
        "The file is on disk, but no runtime on this machine reports which "
        "context files it loaded, so we cannot confirm the agent read it. "
        "Scored as unknown, not as a pass and not as a penalty.",
        None, 15, severity="high")


def _check_test_command(root: str) -> dict:
    """Is there a discoverable way to run this project's tests?"""
    found: list = []
    partial: list = []
    unreadable: list = []

    seen: set = set()

    def probe(rel, fn):
        path = os.path.join(root, rel)
        key = _probe_key(path)
        if key in seen:
            return
        try:
            text = _read_text(path)
        except _Unreadable:
            seen.add(key)
            unreadable.append(rel)
            return
        if text is None:
            return
        seen.add(key)
        fn(rel, text)

    def _mk(rel, text):
        targets = _make_targets(text)
        for name in ("test", "tests", "check"):
            if name in targets:
                found.append("%s: `make %s`" % (rel, name))
                return

    def _pkg(rel, text):
        scripts = _package_scripts(text)
        if scripts is None:
            unreadable.append("%s (not valid JSON)" % rel)
            return
        if scripts.get("test"):
            found.append("%s: `npm test`" % rel)

    def _pyproject(rel, text):
        secs = _toml_sections(text)
        if "tool.pytest.ini_options" in secs:
            found.append("%s: [tool.pytest.ini_options]" % rel)
        elif "tool.poetry" in secs or "project" in secs:
            partial.append("%s declares a project but no test config" % rel)

    def _ini(rel, text):
        if rel == "setup.cfg":
            if "[tool:pytest]" in text:
                found.append("%s: [tool:pytest]" % rel)
            return
        found.append(rel)

    def _cargo(rel, text):
        partial.append("%s (`cargo test` is a Cargo default, not a project "
                       "choice we can verify)" % rel)

    def _gomod(rel, text):
        if _walk_test_files(root):
            found.append("%s + *_test.go: `go test ./...`" % rel)
        else:
            partial.append("%s but no *_test.go files found" % rel)

    probe("Makefile", _mk)
    probe("makefile", _mk)
    probe("GNUmakefile", _mk)
    probe("Justfile", lambda r, t: (found.append("%s: `just test`" % r)
                                    if re.search(r"^test\b", t, re.M) else None))
    probe("package.json", _pkg)
    probe("pyproject.toml", _pyproject)
    probe("pytest.ini", _ini)
    probe("tox.ini", _ini)
    probe("setup.cfg", _ini)
    probe("Cargo.toml", _cargo)
    probe("go.mod", _gomod)

    if found:
        return _check(
            "test_command", "Test command discoverable", PASS,
            "An agent can find how to run the tests: %s." % "; ".join(found[:3]),
            None, 20, evidence=found[0].split(":")[0], severity="high")
    if partial:
        return _check(
            "test_command", "Test command discoverable", WARN,
            "Only an inherited default: %s. An inherited default is "
            "unmeasured, not ready." % "; ".join(partial[:2]),
            "Add an explicit `test` target (Makefile) or `scripts.test` "
            "(package.json) so the command is discoverable without guessing.",
            20, evidence=partial[0].split(" ")[0], severity="high")
    if unreadable and not found:
        return _check(
            "test_command", "Test command discoverable", UNKNOWN,
            "Could not read %s, so we cannot say either way."
            % ", ".join(unreadable[:3]), None, 20, severity="high")
    return _check(
        "test_command", "Test command discoverable", FAIL,
        "No test entry point an agent can find (checked Makefile, "
        "package.json, pyproject.toml, pytest.ini, tox.ini, setup.cfg, "
        "Cargo.toml, go.mod).",
        "Add a `test` target to a Makefile, or `scripts.test` to "
        "package.json, so the agent can verify its own work.",
        20, severity="high")


def _check_build_command(root: str) -> dict:
    """Is there a discoverable way to build this project?

    We report whether the command can be FOUND, never whether it succeeds:
    running a build changes the machine and usually reaches the network,
    and this module does neither.
    """
    found: list = []
    unreadable: list = []

    seen: set = set()

    def probe(rel, fn):
        path = os.path.join(root, rel)
        key = _probe_key(path)
        if key in seen:
            return
        try:
            text = _read_text(path)
        except _Unreadable:
            seen.add(key)
            unreadable.append(rel)
            return
        if text is not None:
            seen.add(key)
            fn(rel, text)

    def _mk(rel, text):
        targets = _make_targets(text)
        for name in ("build", "all", "install", "dist"):
            if name in targets:
                found.append("%s: `make %s`" % (rel, name))
                return

    def _pkg(rel, text):
        scripts = _package_scripts(text)
        if scripts is None:
            unreadable.append("%s (not valid JSON)" % rel)
            return
        if scripts.get("build"):
            found.append("%s: `npm run build`" % rel)

    def _pyproject(rel, text):
        if "build-system" in _toml_sections(text):
            found.append("%s: [build-system]" % rel)

    probe("Makefile", _mk)
    probe("makefile", _mk)
    probe("GNUmakefile", _mk)
    probe("package.json", _pkg)
    probe("pyproject.toml", _pyproject)
    for rel in ("setup.py", "Dockerfile", "Cargo.toml", "go.mod",
                "CMakeLists.txt", "build.gradle", "build.gradle.kts",
                "pom.xml", "Gemfile"):
        if _exists(os.path.join(root, rel)):
            found.append(rel)

    if found:
        return _check(
            "build_command", "Build command discoverable", PASS,
            "%s. Whether the build succeeds is not graded: ClawMetry never "
            "runs your build." % "; ".join(found[:3]),
            None, 10, evidence=found[0].split(":")[0])
    if unreadable:
        return _check(
            "build_command", "Build command discoverable", UNKNOWN,
            "Could not read %s, so we cannot say either way."
            % ", ".join(unreadable[:3]), None, 10)
    return _check(
        "build_command", "Build command discoverable", FAIL,
        "No build entry point an agent can find (checked Makefile, "
        "package.json, pyproject.toml, setup.py, Dockerfile and the usual "
        "Cargo / Go / Gradle / Maven manifests).",
        "Add a `build` target or script so the agent knows how to produce "
        "an artifact without guessing.",
        10)


_LINT_CONFIG_FILES = (
    ".ruff.toml", "ruff.toml", ".flake8", ".pylintrc", "pylintrc",
    ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json",
    ".eslintrc.yml", ".eslintrc.yaml", "eslint.config.js",
    "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts",
    "biome.json", "biome.jsonc", ".golangci.yml", ".golangci.yaml",
    ".rubocop.yml", ".pre-commit-config.yaml", ".pre-commit-config.yml",
    ".swiftlint.yml", "rustfmt.toml", ".rustfmt.toml", ".stylelintrc",
    ".clang-format", "checkstyle.xml", ".editorconfig",
)


def _check_lint_gate(root: str) -> dict:
    found: list = []
    unreadable: list = []
    for rel in _LINT_CONFIG_FILES:
        if _exists(os.path.join(root, rel)):
            found.append(rel)

    seen: set = set()

    def probe(rel, fn):
        path = os.path.join(root, rel)
        key = _probe_key(path)
        if key in seen:
            return
        try:
            text = _read_text(path)
        except _Unreadable:
            seen.add(key)
            unreadable.append(rel)
            return
        if text is not None:
            seen.add(key)
            fn(rel, text)

    def _mk(rel, text):
        targets = _make_targets(text)
        for name in ("lint", "fmt", "format", "check"):
            if name in targets:
                found.append("%s: `make %s`" % (rel, name))
                return

    def _pkg(rel, text):
        scripts = _package_scripts(text)
        if scripts is None:
            unreadable.append("%s (not valid JSON)" % rel)
            return
        if scripts.get("lint") or scripts.get("format"):
            found.append("%s: `npm run lint`" % rel)

    def _pyproject(rel, text):
        secs = _toml_sections(text)
        for name in ("tool.ruff", "tool.black", "tool.flake8", "tool.isort",
                     "tool.mypy", "tool.pylint"):
            if any(s == name or s.startswith(name + ".") for s in secs):
                found.append("%s: [%s]" % (rel, name))
                return

    probe("Makefile", _mk)
    probe("makefile", _mk)
    probe("package.json", _pkg)
    probe("pyproject.toml", _pyproject)

    if found:
        return _check(
            "lint_gate", "Lint or format gate", PASS,
            "A style gate the agent can run before it hands work back: %s."
            % ", ".join(found[:3]),
            None, 10, evidence=found[0].split(":")[0])
    if unreadable:
        return _check(
            "lint_gate", "Lint or format gate", UNKNOWN,
            "Could not read %s, so we cannot say either way."
            % ", ".join(unreadable[:3]), None, 10)
    return _check(
        "lint_gate", "Lint or format gate", FAIL,
        "No lint or format config in the repo, and no `lint` target or "
        "script.",
        "Add a linter config (ruff, eslint, golangci-lint) or a `lint` "
        "target. Without one the agent cannot tell whether its edit matches "
        "the house style.",
        10)


_CI_FILES = (
    ".gitlab-ci.yml", ".gitlab-ci.yaml", ".circleci/config.yml",
    "azure-pipelines.yml", "Jenkinsfile", ".travis.yml", ".drone.yml",
    "bitbucket-pipelines.yml", "cloudbuild.yaml", "cloudbuild.yml",
    ".woodpecker.yml", "wercker.yml",
)


def _check_ci_config(root: str) -> dict:
    found = _glob_any(root, ".github/workflows", (".yml", ".yaml"))
    for rel in _CI_FILES:
        if _exists(os.path.join(root, rel)):
            found.append(rel)
    if _isdir_nonempty(os.path.join(root, ".buildkite")):
        found.append(".buildkite/")
    if found:
        return _check(
            "ci_config", "CI configuration", PASS,
            "%d CI config%s in the repo (%s). An agent can read what "
            "\"green\" means here." % (
                len(found), "" if len(found) == 1 else "s",
                ", ".join(found[:3])),
            None, 10, evidence=found[0])
    return _check(
        "ci_config", "CI configuration", FAIL,
        "No CI configuration found (checked .github/workflows and the usual "
        "GitLab / CircleCI / Azure / Jenkins / Travis files).",
        "Add a CI workflow. It is the only place that states, in a form an "
        "agent can read, which checks have to pass.",
        10)


def _check_agent_assets(root: str, runtime: Optional[str]) -> dict:
    """Skills / commands / sub-agent definitions the runtime would discover.

    Absent is graded ``warn``, not ``fail``: most healthy repos ship none,
    and a check that fails on a healthy repo teaches the reader to ignore
    the grade.
    """
    roots = _asset_roots(runtime)
    if not roots:
        return _check(
            "agent_assets", "Skills and commands", UNKNOWN,
            "No runtime on this machine declares project-scoped skills, so "
            "there is nothing to look for.", None, 10)
    found = [spec["rel"] for spec in roots if _present(root, spec["rel"])]
    found = sorted(set(found))
    if found:
        return _check(
            "agent_assets", "Skills and commands", PASS,
            "The repo ships agent assets the runtime will discover: %s."
            % ", ".join(found[:4]),
            None, 10, evidence=found[0], severity="low")
    # Suggest a directory-shaped root (".claude/skills") over a bare name
    # ("skills"): a one-word hint at the repo root reads as a typo.
    hint = next((r["rel"] for r in roots if "/" in r["rel"]), roots[0]["rel"])
    return _check(
        "agent_assets", "Skills and commands", WARN,
        "No repo-scoped skills, slash commands or sub-agent definitions. "
        "That is normal, and it is also the cheapest thing to add.",
        "Repeated multi-step work in this repo is worth packaging as a "
        "skill (%s/) so every session starts from it." % hint,
        10, severity="low")


# ═══════════════════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════════════════

_GRADES = (
    (90, "A", "Ready", "#22c55e"),
    (75, "B", "Good", "#84cc16"),
    (60, "C", "Fair", "#f59e0b"),
    (40, "D", "Thin", "#f97316"),
    (0, "F", "Bare", "#ef4444"),
)


def _grade(checks: list) -> tuple:
    """pass = full weight, warn = half, fail = zero, unknown = not counted.

    ``unknown`` checks carry weight 0 (forced in :func:`_check`), so they
    fall out of both the numerator and the denominator: a thing we cannot
    read can move the grade in neither direction.
    """
    total = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["status"] == PASS)
    earned += sum(c["weight"] * 0.5 for c in checks if c["status"] == WARN)
    if total <= 0:
        return "U", "Not scored", "#64748b", 0.0
    pct = earned / total * 100
    for floor, letter, label, color in _GRADES:
        if pct >= floor:
            return letter, label, color, round(pct, 1)
    return "F", "Bare", "#ef4444", round(pct, 1)


def git_root(path: str) -> Optional[str]:
    """Nearest ancestor of *path* holding a ``.git`` entry.

    Pure filesystem walk — no ``git`` subprocess, so this costs a handful
    of stats and cannot reach the network. Handles worktrees and submodules,
    where ``.git`` is a file rather than a directory.
    """
    if not isinstance(path, str) or not path.strip():
        return None
    try:
        cur = os.path.abspath(os.path.expanduser(path.strip()))
    except (OSError, ValueError):
        return None
    for _ in range(_MAX_GIT_WALK):
        try:
            if os.path.exists(os.path.join(cur, ".git")):
                return cur
        except OSError:
            return None
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


def score_repo(path: str, *, runtime: Optional[str] = None,
               signals: Optional[dict] = None,
               loaded_evidence: Optional[dict] = None) -> dict:
    """Score one repository. Never raises, never opens a socket.

    ``runtime`` scopes the instruction / asset checks to one runtime, so a
    repo legible to Claude Code but invisible to Cursor reads honestly under
    the runtime switcher. ``signals`` is the already-measured stuck-rate
    bundle from :func:`pair_signals`; it is displayed next to the score and
    never folded into it.
    """
    # An empty / non-string path must NOT quietly resolve to the process cwd:
    # os.path.abspath("") returns it, so a caller that lost its path would
    # score whatever directory the dashboard happens to be running in and
    # present it as the user's repo.
    root = None
    if isinstance(path, str) and path.strip():
        try:
            root = os.path.abspath(os.path.expanduser(path.strip()))
        except (OSError, ValueError):
            root = None
    if not root or not os.path.isdir(root):
        return {
            "status": "not_found",
            "path": path,
            "detail": "That directory is not on this machine.",
            "checks": [], "score": "U", "score_label": "Not scored",
            "score_color": "#64748b", "score_pct": 0.0,
            "passed": 0, "failed": 0, "warnings": 0, "unknowns": 0,
            "total": 0, "signals": signals or _empty_signals(),
            "runtime_coverage": [],
            "scanned_at": datetime.now().isoformat(),
        }

    coverage = runtime_coverage(root, _instruction_roots(runtime))
    checks = [
        _check_instruction_file(root, runtime, coverage),
        _check_instruction_loaded(root, coverage, loaded_evidence),
        _check_test_command(root),
        _check_build_command(root),
        _check_lint_gate(root),
        _check_ci_config(root),
        _check_agent_assets(root, runtime),
    ]
    letter, label, color, pct = _grade(checks)
    return {
        "status": "ok",
        "path": root,
        "name": os.path.basename(root) or root,
        "is_git_repo": _exists(os.path.join(root, ".git")),
        "runtime": runtime or "all",
        "score": letter,
        "score_label": label,
        "score_color": color,
        "score_pct": pct,
        "checks": checks,
        "passed": sum(1 for c in checks if c["status"] == PASS),
        "failed": sum(1 for c in checks if c["status"] == FAIL),
        "warnings": sum(1 for c in checks if c["status"] == WARN),
        "unknowns": sum(1 for c in checks if c["status"] == UNKNOWN),
        "total": len(checks),
        "runtime_coverage": coverage,
        "signals": signals if signals is not None else _empty_signals(),
        "scanned_at": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# The pairing: what actually happened to agents working in this repo
# ═══════════════════════════════════════════════════════════════════════════

_SIGNAL_KINDS = ("stuck_loop", "no_progress", "repeated_tool_failure",
                 "action_discrepancy")

#: ``loop_signals.signature`` → detector class, mirroring
#: ``sync._LOOPS_KIND_BY_SIGNATURE`` (the daemon's own mapping). A signature
#: we do not recognise is still a genuine loop (the proxy LoopDetector writes
#: a request hash), so it counts as ``stuck_loop`` rather than being dropped.
_KIND_BY_SIGNATURE = {
    "daemon_stuck": "stuck_loop",
    "daemon_detect_stuck_loop": "stuck_loop",
    "daemon_detect_no_progress": "no_progress",
    "daemon_detect_repeated_tool_failure": "repeated_tool_failure",
    "daemon_detect_action_discrepancy": "action_discrepancy",
}


def _empty_signals() -> dict:
    return {
        "sessions": 0,
        "stuck_sessions": 0,
        "stuck_rate": None,
        "incidents": {k: 0 for k in _SIGNAL_KINDS},
        "window_days": 0,
        "has_history": False,
    }


def signal_kind(signature: str, details: Any) -> Optional[str]:
    """Classify one ``loop_signals`` row. ``None`` when it is not a loop."""
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except (ValueError, TypeError):
            details = None
    if isinstance(details, dict):
        kind = str(details.get("kind") or "").strip()
        if kind in _SIGNAL_KINDS:
            return kind
    sig = str(signature or "")
    kind = _KIND_BY_SIGNATURE.get(sig)
    if kind:
        return kind
    return "stuck_loop" if sig else None


def pair_signals(rows: Iterable, *, window_days: int) -> dict:
    """Fold ``query_repo_activity`` rows for ONE repo into the pairing block.

    Each row is one session that ran in this repo, optionally carrying the
    loop signal the detector wrote for it. ``stuck_rate`` is ``None`` — not
    ``0.0`` — when there are no sessions, because "no agent has worked here"
    and "every agent sailed through" are different facts.
    """
    sessions = set()
    stuck = set()
    incidents = {k: 0 for k in _SIGNAL_KINDS}
    for row in rows or ():
        if not isinstance(row, dict):
            continue
        sid = str(row.get("session_id") or "").strip()
        if not sid:
            continue
        sessions.add(sid)
        kind = signal_kind(row.get("signature"), row.get("details"))
        if kind:
            stuck.add(sid)
            incidents[kind] += 1
    n = len(sessions)
    return {
        "sessions": n,
        "stuck_sessions": len(stuck),
        "stuck_rate": round(len(stuck) / n * 100, 1) if n else None,
        "incidents": incidents,
        "window_days": int(window_days),
        "has_history": n > 0,
    }


def group_by_repo(rows: Iterable) -> "dict[str, list]":
    """Bucket ``query_repo_activity`` rows by the git root of their ``cwd``.

    A session that ran three directories deep in a checkout belongs to that
    checkout, not to its own subdirectory. Rows whose ``cwd`` no longer
    exists on this machine fall back to the recorded path so a deleted
    checkout still reports its history instead of vanishing.
    """
    out: dict = {}
    for row in rows or ():
        if not isinstance(row, dict):
            continue
        cwd = str(row.get("cwd") or "").strip()
        if not cwd:
            continue
        root = git_root(cwd) or cwd
        out.setdefault(root, []).append(row)
    return out


def rank_repos(rows: Iterable, *, window_days: int, limit: int = 25) -> list:
    """Repos an agent has actually worked in, busiest first.

    Returns ``[{path, name, exists, signals, last_active_at}, …]``. Pure —
    the caller decides which ones to score.
    """
    out = []
    for root, group in group_by_repo(rows).items():
        last = ""
        for row in group:
            ts = str(row.get("last_active_at") or "")
            if ts > last:
                last = ts
        out.append({
            "path": root,
            "name": os.path.basename(root) or root,
            "exists": os.path.isdir(root),
            "last_active_at": last or None,
            "signals": pair_signals(group, window_days=window_days),
        })
    out.sort(key=lambda r: (-(r["signals"]["sessions"]),
                            r["last_active_at"] or "", r["path"]),
             reverse=False)
    out.sort(key=lambda r: (r["signals"]["sessions"],
                            r["last_active_at"] or ""), reverse=True)
    return out[:max(1, int(limit))]
