"""A module may not define the same top-level name twice.

Python keeps the LAST definition, silently. That is not a style nit: in
``clawmetry/sync.py`` a helper named ``_session_cwd`` was added beside an
existing one of the same name, and the new definition replaced the old for all
THREE of its callers. The original read a raw adapter dict through a
twelve-alias set (``workingDir``, ``directory``, ``folder``, ...); the
replacement read two keys. Family sessions whose runtime spells the directory
any other way stopped persisting ``sessions.cwd``, which is the column
``process_control`` promotes to find a pid and the one the workspace scanner
keys on. Nothing failed. The tests passed. The wheel shipped.

Line coverage cannot see this, review rarely does in a 25,000-line module, and
grep does not either unless you already suspect it. An AST walk does, in
milliseconds, for every module at once, which is why this guard is
auto-discovering rather than a list of files someone has to remember to extend.
"""
from __future__ import annotations

import ast
import collections
import json
import os

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Every first-party module. Discovered, never listed: a guard with a
#: hand-kept scope drifts the moment somebody adds a file.
_ROOTS = ("clawmetry", "routes")


def _modules() -> list:
    out = []
    for root in _ROOTS:
        base = os.path.join(_REPO_ROOT, root)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in {"__pycache__", "static", "templates",
                                        "locales", "node_modules"}]
            for name in filenames:
                if name.endswith(".py"):
                    out.append(os.path.join(dirpath, name))
    out.append(os.path.join(_REPO_ROOT, "dashboard.py"))
    return sorted(p for p in out if os.path.isfile(p))


def _duplicates(path: str) -> dict:
    """``{name: [line, line]}`` for every top-level def/class defined twice.

    Only module scope: a method named the same in two classes is fine, and a
    conditional re-definition inside a function is a different question.
    """
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError:
        return {}
    seen = collections.defaultdict(list)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seen[node.name].append(node.lineno)
    return {n: ls for n, ls in seen.items() if len(ls) > 1}


#: Files that already carry this debt, with the count they carry. A ratchet
#: rather than an allowlist: the number may fall, never rise, so the existing
#: 60 do not block work while nothing new joins them.
_BASELINE_PATH = os.path.join(_REPO_ROOT, "verification",
                              "shadowed_definitions.json")


def _baseline() -> dict:
    try:
        with open(_BASELINE_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("baseline") or {}
    except Exception:
        return {}


@pytest.mark.parametrize("path", _modules(),
                         ids=lambda p: os.path.relpath(p, _REPO_ROOT))
def test_no_shadowed_module_functions(path):
    rel = os.path.relpath(path, _REPO_ROOT)
    dupes = _duplicates(path)
    allowed = int(_baseline().get(rel, 0))
    assert len(dupes) <= allowed, (
        f"{rel} defines {len(dupes)} top-level names more than once "
        f"(baseline {allowed}): {dict(list(dupes.items())[:8])}.\n"
        "Python keeps the LAST one and says nothing, so every caller of the "
        "first silently changes behaviour. Rename one, or delete the dead copy."
    )


def test_the_baseline_is_measured_not_aspirational():
    """A baseline higher than reality lets new debt in under cover of old."""
    for rel, allowed in _baseline().items():
        path = os.path.join(_REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue
        actual = len(_duplicates(path))
        assert actual == allowed, (
            f"{rel} carries {actual} shadowed names but the baseline records "
            f"{allowed}. Lower it to {actual} (progress) rather than leaving "
            f"headroom for the next one."
        )


def test_the_guard_sees_a_shadow_when_there_is_one(tmp_path):
    """A guard nobody has watched fail is not a guard."""
    p = tmp_path / "m.py"
    p.write_text("def f():\n    return 1\n\n\ndef f():\n    return 2\n",
                 encoding="utf-8")
    assert _duplicates(str(p)) == {"f": [1, 5]}
