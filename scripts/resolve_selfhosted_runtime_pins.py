#!/usr/bin/env python3
"""Regenerate deploy/self-hosted/runtime-requirements.txt.

Dockerfile.release installs the published clawmetry wheel as
`pip install "$1[otel]"`. The `[otel]` extra's two names are already satisfied
by otel-requirements.txt before that line runs, so pip resolves neither -- but
the wheel's OWN install_requires (flask, waitress, cryptography, cffi, duckdb,
websocket-client, truststore, certifi) had nothing standing in front of it and
resolved live against the index at build time.

This script resolves that closure for the image's target so it can be pinned
the same way. The closure cannot be obtained from pip on this machine:

    pip install --dry-run --python-version 3.14 clawmetry

evaluates environment markers against the interpreter doing the resolving, and
clawmetry's install_requires branches on `python_version` in four places
(cryptography, cffi, zstandard, truststore). Resolving on 3.11 picks the 3.9
and sub-3.14 arms and produces a file that is wrong for the image.

So resolve it here with the markers evaluated for the target, then assert the
result is self-consistent and installable on BOTH published architectures
before writing it.

    python3 scripts/resolve_selfhosted_runtime_pins.py            # resolve + validate
    python3 scripts/resolve_selfhosted_runtime_pins.py --write    # ... and write the file

Dependabot owns the routine bumps (.github/dependabot.yml watches
/deploy/self-hosted for pip) and rewrites the hashes with them; this script is
for the cases it cannot do on its own -- a new direct requirement, or a resolve
that has to be re-derived from scratch.

Modelled on scripts/resolve_windows_pins.py, which does the same job for the
Windows enterprise-TLS job's set.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

# clawmetry's install_requires, with the markers already evaluated for the
# image's interpreter (python_version == "3.14"):
#   cryptography  -> the >=50.0.0 arm (python_version >= "3.10")
#   cffi          -> the >=2 arm      (python_version >= "3.10")
#   truststore    -> included         (python_version >= "3.10")
#   zstandard     -> DROPPED          (python_version < "3.14")
# scripts/.. no, the guard that keeps this list honest is
# tests/test_selfhosted_runtime_pin.py, which re-derives it from setup.py.
ROOTS = [
    "flask>=2.0,<4",
    "waitress>=2.0",
    "cryptography>=50.0.0",
    "cffi>=2",
    "duckdb>=0.10,!=1.4.5",
    "websocket-client>=1.6",
    "truststore>=0.8",
    "certifi>=2024.7.4",
]

# The image: FROM python:3.14-slim, published for linux/amd64 and linux/arm64.
TARGET_PYTHON = Version("3.14.0")
ENV = {
    "sys_platform": "linux",
    "platform_system": "Linux",
    "os_name": "posix",
    "platform_machine": "x86_64",
    "python_version": "3.14",
    "python_full_version": str(TARGET_PYTHON),
    "implementation_name": "cpython",
    "implementation_version": str(TARGET_PYTHON),
    "platform_python_implementation": "CPython",
    "platform_release": "6.1.0",
    "extra": "",
}

# Both platforms container-image.yml builds. A release that has a wheel for one
# and not the other breaks exactly one architecture's build, which is the
# failure this set exists to make impossible.
PLATFORM_TAGS = {
    "amd64": ("manylinux", "x86_64"),
    "arm64": ("manylinux", "aarch64"),
}

OUT = Path(__file__).resolve().parent.parent / "deploy" / "self-hosted" / "runtime-requirements.txt"

_projects: dict[str, dict] = {}
_releases: dict[tuple[str, str], dict] = {}


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as fh:
        return json.load(fh)


def project(name: str) -> dict:
    key = canonicalize_name(name)
    if key not in _projects:
        _projects[key] = _get(f"https://pypi.org/pypi/{name}/json")
    return _projects[key]


def release(name: str, version) -> dict:
    key = (canonicalize_name(name), str(version))
    if key not in _releases:
        _releases[key] = _get(f"https://pypi.org/pypi/{name}/{version}/json")
    return _releases[key]


def _py_tag_ok(pythons: list[str], abi: str) -> bool:
    for py in pythons:
        if py in ("py2", "py3", "cp314"):
            return True
        if py.startswith("py3") and py[3:].isdigit() and int(py[3:]) <= 14:
            return True
        # an abi3 wheel built against an older CPython works on newer ones
        if abi.startswith("abi3") and py.startswith("cp3") and py[3:].isdigit() and int(py[3:]) <= 14:
            return True
    return False


def wheel_matches(filename: str, arch: str) -> bool:
    """Is this wheel installable on linux/<arch> at CPython 3.14?"""
    tags = filename[:-4].split("-")
    if len(tags) < 3:
        return False
    plats, abi, pythons = tags[-1].split("."), tags[-2], tags[-3].split(".")
    if not _py_tag_ok(pythons, abi):
        return False
    family, machine = PLATFORM_TAGS[arch]
    for plat in plats:
        if plat == "any":
            return True
        # manylinux_2_28_x86_64, manylinux2014_aarch64, musllinux_1_2_x86_64
        if plat.endswith("_" + machine) and (plat.startswith(family) or plat.startswith("musllinux")):
            return True
    return False


def installable(files: list[dict], arch: str) -> bool:
    """Could pip install something for this release on linux/<arch>?"""
    for f in files:
        if f.get("yanked"):
            continue
        name = f["filename"]
        if name.endswith((".tar.gz", ".zip")):
            return True  # sdist: pip builds it in the image
        if name.endswith(".whl") and wheel_matches(name, arch):
            return True
    return False


def installable_everywhere(files: list[dict]) -> bool:
    return all(installable(files, arch) for arch in PLATFORM_TAGS)


def candidates(name: str) -> list[Version]:
    out = []
    for raw, files in project(name)["releases"].items():
        try:
            version = Version(raw)
        except InvalidVersion:
            continue
        if version.is_prerelease or not files or not installable_everywhere(files):
            continue
        requires_python = (files[0] or {}).get("requires_python") or ""
        if requires_python:
            try:
                if not SpecifierSet(requires_python).contains(TARGET_PYTHON):
                    continue
            except Exception:
                pass
        out.append(version)
    return sorted(out, reverse=True)


_candidates: dict[str, list[Version]] = {}


def candidate_list(name: str) -> list[Version]:
    key = canonicalize_name(name)
    if key not in _candidates:
        _candidates[key] = candidates(name)
    return _candidates[key]


def dependencies(name: str, version):
    """Requirements that apply on the target, extras excluded."""
    for raw in release(name, version)["info"].get("requires_dist") or []:
        try:
            req = Requirement(raw)
        except Exception:
            continue
        if req.marker and not req.marker.evaluate(ENV):
            continue
        yield req


def solve(constraints: dict, chosen: dict) -> dict | None:
    pending = [c for c in constraints if c not in chosen]
    if not pending:
        return dict(chosen)
    # most-constrained first: fewest candidates to try
    pending.sort(key=lambda c: (len(candidate_list(constraints[c][0])), c))
    key = pending[0]
    display, spec = constraints[key]
    for version in candidate_list(display):
        if not spec.contains(version, prereleases=False):
            continue
        merged = dict(constraints)
        ok = True
        for req in dependencies(display, version):
            name = canonicalize_name(req.name)
            if name in merged:
                merged[name] = (merged[name][0], merged[name][1] & req.specifier)
            else:
                merged[name] = (req.name, req.specifier)
            display_name, spec_now = merged[name]
            if name in chosen:
                if not spec_now.contains(chosen[name], prereleases=False):
                    ok = False
                    break
            elif not any(spec_now.contains(c, prereleases=False) for c in candidate_list(display_name)):
                ok = False
                break
        if not ok:
            continue
        chosen[key] = version
        got = solve(merged, chosen)
        if got is not None:
            return got
        del chosen[key]
    return None


def validate(closure: list[tuple[str, str]]) -> list[str]:
    """Every dependency edge satisfied, every package installable on both arches."""
    chosen = {canonicalize_name(n): Version(v) for n, v in closure}
    display = {canonicalize_name(n): n for n, _ in closure}
    errors = []
    for name, version in closure:
        info = release(name, version)
        requires_python = info["info"].get("requires_python") or ""
        if requires_python and not SpecifierSet(requires_python).contains(TARGET_PYTHON):
            errors.append(f"{name}=={version}: requires_python {requires_python} excludes {TARGET_PYTHON}")
        for arch in PLATFORM_TAGS:
            if not installable(list(info["urls"]), arch):
                errors.append(f"{name}=={version}: nothing installable on linux/{arch} at py3.14")
        for req in dependencies(name, version):
            dep = canonicalize_name(req.name)
            if dep not in chosen:
                errors.append(f"{name}=={version}: needs {req.name!r}, missing from the closure")
            elif not req.specifier.contains(chosen[dep], prereleases=False):
                errors.append(
                    f"{name}=={version}: needs {req.name}{req.specifier}, "
                    f"closure has {display[dep]}=={chosen[dep]}"
                )
    # every root must be satisfied by what we picked
    for raw in ROOTS:
        root = Requirement(raw)
        key = canonicalize_name(root.name)
        if key not in chosen:
            errors.append(f"root {raw!r} missing from the closure")
        elif not root.specifier.contains(chosen[key], prereleases=False):
            errors.append(f"root {raw!r} not satisfied by {chosen[key]}")
    return errors


def hash_blocks(closure: list[tuple[str, str]]) -> str:
    blocks = []
    for name, version in closure:
        info = release(name, version)
        hashes = []
        for url in info["urls"]:
            if url.get("yanked"):
                continue
            digest = url["digests"].get("sha256")
            if digest and digest not in hashes:
                hashes.append(digest)
        if not hashes:
            sys.exit(f"no sha256 published for {name}=={version}")
        canonical = info["info"]["name"]
        blocks.append(
            f"{canonical}=={version} \\\n"
            + " \\\n".join(f"    --hash=sha256:{h}" for h in hashes)
        )
    return "\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the pinned set in place")
    args = parser.parse_args()

    constraints = {}
    for raw in ROOTS:
        req = Requirement(raw)
        constraints[canonicalize_name(req.name)] = (req.name, req.specifier)
    solution = solve(constraints, {})
    if solution is None:
        sys.exit("no resolution for " + " ".join(ROOTS))

    closure = sorted(
        ((release(key, v)["info"]["name"], str(v)) for key, v in solution.items()),
        key=lambda x: x[0].lower(),
    )

    errors = validate(closure)
    print(f"resolved {len(closure)} packages for linux/amd64 + linux/arm64 at CPython {TARGET_PYTHON}")
    for name, version in closure:
        print(f"  {name}=={version}")
    if errors:
        print("\nclosure is NOT self-consistent:")
        for err in errors:
            print("  " + err)
        return 1

    body = hash_blocks(closure)
    if args.write:
        existing = OUT.read_text() if OUT.exists() else ""
        header = existing.split("\n# ---8<--- hashes below are generated ---8<---\n")[0] if "---8<---" in existing else ""
        if header:
            OUT.write_text(header + "\n# ---8<--- hashes below are generated ---8<---\n" + body)
        else:
            OUT.write_text(body)
        print(f"\nwrote {OUT}")
    else:
        print("\n" + body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
