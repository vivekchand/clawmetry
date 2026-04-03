"""Test that dashboard.py has no duplicate function definitions."""

import ast
import subprocess


def test_no_duplicate_functions():
    """Ensure dashboard.py has no duplicate function definitions."""
    with open("dashboard.py", "r") as f:
        content = f.read()

    tree = ast.parse(content)
    func_defs = {}
    dupes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name in func_defs:
                dupes.append(node.name)
            else:
                func_defs[node.name] = node.lineno

    assert len(dupes) == 0, (
        f"Duplicate function definitions found: {sorted(set(dupes))}"
    )


def test_dashboard_syntax():
    """Ensure dashboard.py has valid Python syntax."""
    result = subprocess.run(
        ["python3", "-m", "py_compile", "dashboard.py"], capture_output=True
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"
