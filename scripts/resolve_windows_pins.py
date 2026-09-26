#!/usr/bin/env python3
"""Regenerate .github/requirements/windows-enterprise-tls.txt.

windows-enterprise-tls.yml runs on windows-latest at Python 3.13 and installs
pytest + mitmproxy + requests. That set has to be hash-pinned like every other
CI install in this repo, and the closure cannot be obtained from pip on Linux:

    pip install --dry-run --platform win_amd64 --python-version 3.13 ...

still evaluates environment markers against the interpreter doing the
resolving. On Linux that is wrong in both directions at once -- it drops
`pydivert; sys_platform == "win32"` (a real Windows dependency of mitmproxy)
and it requires `mitmproxy-linux; sys_platform == "linux"` (which publishes no
Windows distribution, so every mitmproxy 12.x is rejected and the resolve lands
silently on 11.0.2). Either mistake produces a file that breaks the job.

So resolve it here with the markers evaluated for the target, backtracking over
versions, then assert the result is self-consistent before writing it.

    python3 scripts/resolve_windows_pins.py            # resolve + validate
    python3 scripts/resolve_windows_pins.py --write    # ... and write the file

Dependabot owns the routine bumps and rewrites the hashes with them; this
script is for the cases it cannot do on its own (a new direct requirement, or
a resolve that has to be re-derived from scratch).
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

ROOTS = ["pytest", "mitmproxy", "requests"]

# The job's runner: windows-latest, actions/setup-python 3.13.
TARGET_PYTHON = Version("3.13.9")
ENV = {
    "sys_platform": "win32",
    "platform_system": "Windows",
    "os_name": "nt",
    "platform_machine": "AMD64",
    "python_version": "3.13",
    "python_full_version": str(TARGET_PYTHON),
    "implementation_name": "cpython",
    "implementation_version": str(TARGET_PYTHON),
    "platform_python_implementation": "CPython",
    "platform_release": "11",
    "extra": "",
}

OUT = Path(__file__).resolve().parent.parent / ".github" / "requirements" / "windows-enterprise-tls.txt"

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


def wheel_matches(filename: str) -> bool:
    """Is this wheel installable on win_amd64 / CPython 3.13?"""
    tags = filename[:-4].split("-")
    if len(tags) < 3:
        return False
    plat, abi, pythons = tags[-1], tags[-2], tags[-3].split(".")
    if plat not in ("any", "win_amd64"):
        return False
    for py in pythons:
        if py in ("py2", "py3", "cp313"):
            return True
        if py.startswith("py3") and py[3:].isdigit() and int(py[3:]) <= 13:
            return True
        # an abi3 wheel built against an older CPython works on newer ones
        if abi.startswith("abi3") and py.startswith("cp3") and py[3:].isdigit() and int(py[3:]) <= 13:
            return True
    return False


def installable(files: list[dict]) -> bool:
    """Could pip install something for this release on the runner?"""
    for f in files:
        if f.get("yanked"):
            continue
        name = f["filename"]
        if name.endswith((".tar.gz", ".zip")):
            return True  # sdist: pip builds it on the runner
        if name.endswith(".whl") and wheel_matches(name):
            return True
    return False


def candidates(name: str) -> list[Version]:
    out = []
    for raw, files in project(name)["releases"].items():
        try:
            version = Version(raw)
        except InvalidVersion:
            continue
        if version.is_prerelease or not files or not installable(files):
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
    """Every dependency edge satisfied, every package installable on the target."""
    chosen = {canonicalize_name(n): Version(v) for n, v in closure}
    display = {canonicalize_name(n): n for n, _ in closure}
    errors = []
    for name, version in closure:
        info = release(name, version)
        requires_python = info["info"].get("requires_python") or ""
        if requires_python and not SpecifierSet(requires_python).contains(TARGET_PYTHON):
            errors.append(f"{name}=={version}: requires_python {requires_python} excludes {TARGET_PYTHON}")
        if not installable([f for f in info["urls"]]):
            errors.append(f"{name}=={version}: nothing installable on win_amd64/py3.13")
        for req in dependencies(name, version):
            dep = canonicalize_name(req.name)
            if dep not in chosen:
                errors.append(f"{name}=={version}: needs {req.name!r}, missing from the closure")
            elif not req.specifier.contains(chosen[dep], prereleases=False):
                errors.append(
                    f"{name}=={version}: needs {req.name}{req.specifier}, "
                    f"closure has {display[dep]}=={chosen[dep]}"
                )
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

    constraints = {canonicalize_name(r): (r, SpecifierSet("")) for r in ROOTS}
    solution = solve(constraints, {})
    if solution is None:
        sys.exit("no resolution for " + " ".join(ROOTS))

    closure = sorted(
        ((release(display, v)["info"]["name"], str(v))
         for key, v in solution.items()
         for display in [constraints.get(key, (key,))[0] if key in constraints else key]),
        key=lambda x: x[0].lower(),
    )

    errors = validate(closure)
    print(f"resolved {len(closure)} packages for win_amd64 / CPython {TARGET_PYTHON}")
    if errors:
        print("closure is NOT self-consistent:")
        for err in errors:
            print("  -", err)
        return 1
    print("closure is self-consistent")

    if not args.write:
        for name, version in closure:
            print(f"  {name}=={version}")
        print(f"\n(--write to update {OUT.relative_to(OUT.parent.parent.parent)})")
        return 0

    text = OUT.read_text()
    header = text.split("\n# Regenerating", 1)[0]
    marker = "\n# Regenerating (targets the job's platform, not the local one):\n"
    marker += "#   python3 scripts/resolve_windows_pins.py --write\n\n"
    OUT.write_text(header + marker + hash_blocks(closure))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
