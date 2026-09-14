#!/usr/bin/env python3
"""Generate docs/FRAMEWORK_COVERAGE.md from clawmetry/framework_map.py.

The coverage document is public, and a coverage table that disagrees with the
code is worse than none, because a reviewer trusts it (REQ-GOV-FWM-003). So it
is never hand-edited: this script renders it from the one mapping contract.

Usage
-----
    python3 scripts/gen_framework_coverage.py            # rewrite the doc
    python3 scripts/gen_framework_coverage.py --check    # CI: exit 1 on drift
    python3 scripts/gen_framework_coverage.py --verify-atlas ATLAS-2026.08.yaml

``--verify-atlas`` checks every ATLAS identifier the contract references
against a downloaded mitre-atlas/atlas-data release (format v6 ``dist/v6/`` or
the legacy ``dist/ATLAS.yaml``): the identifier exists, its type matches and
its name matches. It needs PyYAML and a local file, so it is a maintainer step
when the pinned edition changes, not a CI gate.
"""
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_PATH = os.path.join(REPO_ROOT, "docs", "FRAMEWORK_COVERAGE.md")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from clawmetry import framework_map as fm  # noqa: E402

# v6 section name / legacy object-type -> the contract's ``type`` word.
_V6_SECTIONS = {"tactics": "tactic", "techniques": "technique",
                "mitigations": "mitigation", "case-studies": "case-study"}


def _atlas_objects(path: str) -> tuple:
    import yaml  # maintainer-only dependency
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    objs = {}
    if isinstance(data.get("techniques"), dict):  # format-version 6
        version = str((data.get("collection") or {}).get("version") or "?")
        for section, kind in _V6_SECTIONS.items():
            for ident, obj in (data.get(section) or {}).items():
                objs[ident] = (kind, str(obj.get("name") or ""))
    else:  # legacy dist/ATLAS.yaml
        version = str(data.get("version") or "?")
        for matrix in data.get("matrices") or []:
            for value in matrix.values():
                if isinstance(value, list):
                    for obj in value:
                        if isinstance(obj, dict) and "id" in obj:
                            objs[obj["id"]] = (str(obj.get("object-type")), str(obj.get("name") or ""))
        for obj in data.get("case-studies") or []:
            objs[obj["id"]] = ("case-study", str(obj.get("name") or ""))
    return version, objs


def verify_atlas(path: str) -> int:
    version, objs = _atlas_objects(path)
    problems = []
    for ident, meta in fm.FRAMEWORKS["atlas"]["catalog"].items():
        got = objs.get(ident)
        if got is None:
            problems.append(f"{ident}: absent from ATLAS {version}")
        elif got != (meta["type"], meta["name"]):
            problems.append(f"{ident}: contract says {meta['type']} {meta['name']!r}, "
                            f"ATLAS {version} says {got[0]} {got[1]!r}")
        else:
            print(f"ok  {ident}  {got[0]}  {got[1]}  (ATLAS {version})")
    for ident in fm.referenced_ids("atlas"):
        if ident not in fm.FRAMEWORKS["atlas"]["catalog"]:
            problems.append(f"{ident}: referenced but missing from the contract catalog")
    for p in problems:
        print(f"FAIL {p}")
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if docs/FRAMEWORK_COVERAGE.md is out of date")
    ap.add_argument("--verify-atlas", metavar="ATLAS_YAML",
                    help="verify ATLAS identifiers against a downloaded release")
    args = ap.parse_args(argv)

    if args.verify_atlas:
        return verify_atlas(args.verify_atlas)

    rendered = fm.render_coverage_markdown()
    if args.check:
        try:
            with open(DOC_PATH, encoding="utf-8") as f:
                current = f.read()
        except OSError:
            current = ""
        if current != rendered:
            print("docs/FRAMEWORK_COVERAGE.md is out of date with clawmetry/framework_map.py.\n"
                  "Regenerate: python3 scripts/gen_framework_coverage.py")
            return 1
        print("docs/FRAMEWORK_COVERAGE.md matches the framework mapping contract.")
        return 0
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"wrote {os.path.relpath(DOC_PATH, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
