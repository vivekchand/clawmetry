#!/usr/bin/env python3
"""List the HTTP routes this repo registers, and which ones a release ADDED.

**Why this exists.** clawmetry-cloud refuses to boot when an installed OSS
route has no ``cloud_route_policy`` entry — deliberately, because an
unclassified route might serve a cloud tenant data it should not. That
fail-closed design makes an OSS release that adds a route deadlock the two
cloud pull requests against each other:

* the auto-pin PR (``chore: auto-pin clawmetry==X``) goes red on every check
  that constructs the app, all on the same ``enforcer.py: sys.exit(1)``;
* the PR carrying the policy entry is red against the OLD pin, because its
  entry points at a route the installed OSS does not have yet.

Each needs the other, so neither can go green alone. The fix is one line of
process — fold the Dockerfile bump into the policy PR — but it reads as a
catastrophe: ~18 failing checks on a pin that changed a version string.

``auto-deploy-cloud.yml`` runs this with ``--added-since`` so the pin PR says
so in its own body instead of leaving the next reader to rediscover it.
Specified as RouteInventoryReporter in the "Release Verification and Merge
Gating" blueprint, under the section named for this deadlock.

Routes are read with :mod:`ast`, not a regex: a decorator argument is a
literal in the tree and guessing at it from text mis-reads f-strings and
multi-line calls.

The decorator literal IS the served path here, so no prefix is applied: no
blueprint in this repository is registered with a ``url_prefix`` (checked, not
assumed — ``grep -r url_prefix routes/ dashboard.py`` finds nothing). Should
one ever be, a rule listed here would no longer match the path the policy
entry has to name, and this is the line that says so.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys

#: Where HTTP routes live. ``routes/`` is one Blueprint per feature;
#: ``dashboard.py`` still carries a few inline ``@app.route`` registrations.
ROUTE_SOURCES = ("routes", "dashboard.py", "dashboard_claudecode.py")

#: Decorator attribute names that register a route. ``add_url_rule`` is a
#: plain call rather than a decorator and is handled alongside them.
ROUTE_DECORATORS = ("route", "get", "post", "put", "patch", "delete")


def _rules_from_source(source: str, origin: str) -> set[str]:
    """Every route rule registered in one module's source."""
    out: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        print(f"warning: cannot parse {origin}", file=sys.stderr)
        return out
    for node in ast.walk(tree):
        calls = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = [d for d in node.decorator_list if isinstance(d, ast.Call)]
        elif isinstance(node, ast.Call):
            calls = [node]
        for call in calls:
            func = call.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ROUTE_DECORATORS + ("add_url_rule",):
                continue
            if not call.args:
                continue
            first = call.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                if first.value.startswith("/"):
                    out.add(first.value)
    return out


def _read(path: str, ref: str | None) -> str | None:
    """A file's contents at *ref*, or from the working tree when ref is None."""
    if ref is None:
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return None
    try:
        return subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None  # the file did not exist at that ref


def _paths(ref: str | None) -> list[str]:
    """The route-bearing files at *ref* (or in the working tree)."""
    if ref is None:
        found = []
        for src in ROUTE_SOURCES:
            if os.path.isdir(src):
                # os.walk, not os.listdir: `routes/entitlement/` is a
                # subpackage holding 435 of this repo's routes, and a
                # non-recursive listing reported none of them. Worktree mode
                # and ref mode then disagreed by 435 routes while both looked
                # plausible, which is the exact failure this script exists
                # not to produce.
                for root, _dirs, files in os.walk(src):
                    found += [os.path.join(root, f) for f in sorted(files)
                              if f.endswith(".py")]
            elif os.path.isfile(src):
                found.append(src)
        return sorted(found)
    done = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref],
                          capture_output=True, text=True)
    if done.returncode != 0:
        # A traceback in a release workflow reads as "the tooling broke", which
        # is the one message this script must never send. Return nothing and
        # let the caller report the bad ref.
        return []
    listing = done.stdout.splitlines()
    return sorted(p for p in listing
                  if p.endswith(".py")
                  and (p.startswith("routes/") or p in ROUTE_SOURCES))


def routes_at(ref: str | None = None) -> set[str]:
    """Every route rule registered at *ref* (default: the working tree)."""
    out: set[str] = set()
    for path in _paths(ref):
        source = _read(path, ref)
        if source:
            out |= _rules_from_source(source, f"{ref or 'worktree'}:{path}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--added-since", metavar="REF",
                    help="print only the routes that REF does not have")
    ap.add_argument("--ref", help="read routes at this ref instead of the "
                                  "working tree")
    args = ap.parse_args()

    # The working tree is the one side that is always readable, so it is the
    # yardstick both refs are held to. Without it the check had a hole in the
    # middle: on a shallow checkout NEITHER ref resolves, both sets come back
    # empty, the difference is empty, and the script reports "this release
    # added no routes" with a success exit. That is the silence this whole
    # thing exists to prevent, and it reached CI.
    reference = routes_at(None)
    if not reference:
        print("error: no routes found in the working tree — run this from the "
              "repository root", file=sys.stderr)
        return 2
    floor = len(reference) * 0.8

    current = routes_at(args.ref)
    if args.ref and len(current) < floor:
        print(f"error: only {len(current)} routes readable at {args.ref!r} "
              f"against {len(reference)} in the working tree — the ref is "
              "missing or its tree is incomplete", file=sys.stderr)
        return 2
    if args.added_since:
        before = routes_at(args.added_since)
        # A base that reads SHORT is as dangerous as one that does not read
        # at all, and far harder to notice: the difference between "this
        # release added two routes" and "this release added four hundred" is
        # the difference between a usable instruction and one that sends the
        # reader off to classify the whole API. A shallow checkout that
        # cannot serve part of the tree lands here.
        if len(before) < floor:
            print(f"error: only {len(before)} routes readable at "
                  f"{args.added_since!r} against {len(reference)} in the "
                  "working tree — the ref is missing or its tree is "
                  "incomplete", file=sys.stderr)
            return 2
        current -= before
    for rule in sorted(current):
        print(rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
