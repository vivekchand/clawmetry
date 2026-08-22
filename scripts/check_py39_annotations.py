#!/usr/bin/env python3
"""Ban PEP 604 (``str | None``) unions in positions Python 3.9 evaluates.

``setup.py`` advertises ``python_requires=">=3.8"`` and the macOS desktop
bundle ships a Python 3.9 venv, so every shipped module has to *import* on
3.9. ``X | Y`` between types is a syntax the 3.9 parser accepts but the 3.9
runtime rejects (``TypeError: unsupported operand type(s) for |``), which is
why the existing ``ast.parse`` lint gate rides straight past it.

That is not theoretical: 0.12.753 shipped a ``def f() -> str | None:`` at
``clawmetry/cli.py`` module scope, so **every** ``clawmetry`` command died at
import on 3.9 — including ``clawmetry uninstall``, which left affected users
with no supported way off the product. CI missed it three ways: the lint gate
only parses, the 3.9 test leg only runs ``tests/test_api.py`` (never imports
the CLI), and ``install-test.yml`` smoke-tests ``clawmetry --version`` on 3.12
only.

Positions Python 3.9 evaluates, and this script therefore rejects:

* function/method signatures (arguments and return) — evaluated at ``def``
  time, unless the module has ``from __future__ import annotations``;
* module-level and class-level variable annotations — same rule;
* any *other* expression (type aliases, ``isinstance(x, int | str)``,
  ``typing.cast(int | None, v)``) — evaluated regardless of the future
  import, so the future import does not excuse these.

Function-local variable annotations are never evaluated at runtime (PEP 526),
so they are left alone.

Usage::

    python3 scripts/check_py39_annotations.py            # scan shipped modules
    python3 scripts/check_py39_annotations.py --json     # machine-readable

``tests/test_py39_annotation_guard.py`` calls :func:`check` so the gate also
fires under ``make test``.
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import sys

# Every .py the installed wheel imports at runtime. Keep in step with the
# `files` list in the ci.yml "Check Python syntax" gate.
TARGET_GLOBS = (
    "clawmetry/**/*.py",
    "routes/**/*.py",
)
TARGET_FILES = ("dashboard.py", "dashboard_claudecode.py", "history.py")

# One side of the `|` being one of these is what separates a *type* union
# from an ordinary bitwise-or over sets/ints (`FREE_RUNTIMES | PAID_RUNTIMES`).
_TYPE_NAMES = {
    "str", "int", "float", "bool", "bytes", "complex",
    "list", "dict", "set", "tuple", "frozenset", "object", "type",
    "Any", "Optional", "Union", "List", "Dict", "Set", "Tuple", "Callable",
    "Sequence", "Mapping", "Iterable", "Iterator", "Path", "Decimal",
}


def _has_future_annotations(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            if any(alias.name == "annotations" for alias in node.names):
                return True
    return False


def _looks_like_type(node: ast.AST) -> bool:
    """True when *node* reads as a type expression rather than a value."""
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in _TYPE_NAMES
    if isinstance(node, ast.Attribute):
        return node.attr in _TYPE_NAMES
    if isinstance(node, ast.Subscript):  # list[str], Dict[str, int], …
        return _looks_like_type(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _looks_like_type(node.left) or _looks_like_type(node.right)
    return False


def _type_unions(node: ast.AST):
    """Yield every ``X | Y`` under *node* that reads as a type union."""
    for child in ast.walk(node):
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.BitOr):
            if _looks_like_type(child.left) or _looks_like_type(child.right):
                yield child


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)  # py3.9+
    except Exception:
        return "<union>"


def _scan_source(path: str, src: str) -> list[dict]:
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as exc:
        return [{
            "file": path, "line": exc.lineno or 0, "kind": "syntax-error",
            "expr": exc.msg, "why": "file does not parse",
        }]

    future = _has_future_annotations(tree)
    findings: list[dict] = []
    deferred: set[int] = set()  # id() of annotation nodes the future import covers

    # Pass 1 — annotation positions. Only class/module scope and signatures
    # are evaluated; the future import defers all of them.
    class _Walk(ast.NodeVisitor):
        def __init__(self):
            self.depth = 0  # >0 == inside a function body

        def _sig(self, node):
            anns = [node.returns] if node.returns else []
            a = node.args
            args = list(getattr(a, "posonlyargs", [])) + list(a.args) + list(a.kwonlyargs)
            args += [a.vararg, a.kwarg]
            anns += [arg.annotation for arg in args if arg is not None and arg.annotation]
            for ann in anns:
                for u in _type_unions(ann):
                    deferred.add(id(u))
                    if not future:
                        findings.append({
                            "file": path, "line": u.lineno, "kind": "signature",
                            "expr": _unparse(ann),
                            "why": "evaluated at def time on py3.9",
                        })

        def visit_FunctionDef(self, node):
            self._sig(node)
            self.depth += 1
            self.generic_visit(node)
            self.depth -= 1

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_AnnAssign(self, node):
            if node.annotation is not None:
                for u in _type_unions(node.annotation):
                    deferred.add(id(u))
                    # PEP 526: local annotations are never evaluated.
                    if not future and self.depth == 0:
                        findings.append({
                            "file": path, "line": u.lineno, "kind": "annotation",
                            "expr": _unparse(node.annotation),
                            "why": "module/class-scope annotation is evaluated on py3.9",
                        })
            self.generic_visit(node)

    _Walk().visit(tree)

    # Pass 2 — everything else. `X = int | None`, `isinstance(v, int | str)`,
    # `cast(int | None, v)`: evaluated whatever the future import says.
    for u in _type_unions(tree):
        if id(u) in deferred:
            continue
        findings.append({
            "file": path, "line": u.lineno, "kind": "runtime-expression",
            "expr": _unparse(u),
            "why": "evaluated at runtime; `from __future__ import annotations` does not help",
        })

    findings.sort(key=lambda f: (f["line"], f["kind"]))
    return findings


def _targets(root: str) -> list[str]:
    seen, out = set(), []
    for rel in TARGET_FILES:
        if os.path.isfile(os.path.join(root, rel)):
            seen.add(rel)
            out.append(rel)
    for pattern in TARGET_GLOBS:
        for rel in sorted(glob.glob(os.path.join(root, pattern), recursive=True)):
            rel = os.path.relpath(rel, root)
            if rel not in seen:
                seen.add(rel)
                out.append(rel)
    return out


def check(root: str = ".") -> list[dict]:
    """Return every py3.9-fatal union across the shipped modules."""
    findings = []
    for rel in _targets(root):
        path = os.path.join(root, rel)
        try:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
        except OSError:
            continue
        findings.extend(_scan_source(rel, src))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repo root to scan")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    findings = check(args.root)
    if args.json:
        print(json.dumps(findings, indent=2))
    elif findings:
        print("PEP 604 unions that Python 3.9 evaluates at import time:\n")
        for f in findings:
            print(f"  {f['file']}:{f['line']}: {f['expr']}  ({f['why']})")
        print(
            "\nFix: add `from __future__ import annotations` at the top of the "
            "module (signatures / class-scope annotations), or spell the union "
            "as `Optional[X]` / `Union[X, Y]` (runtime expressions).\n"
            f"{len(findings)} problem(s)."
        )
    else:
        print(f"OK — no py3.9-fatal unions ({len(_targets(args.root))} files scanned)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
