"""Tests for consistent error handling patterns across the codebase."""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLAWMETRY_DIR = Path(__file__).parent.parent / "clawmetry"

SKIP_FILES = {
    "clawmetry/interceptor.py",
}


class ErrorHandlerAnalyzer(ast.NodeVisitor):
    """Analyze Python code for error handling patterns."""

    def __init__(self):
        self.violations = []
        self.current_file = None
        self.current_function = None
        self.imports = set()

    def visit_FunctionDef(self, node):
        old_function = self.current_function
        old_imports = self.imports.copy()
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        self.imports = old_imports

    def visit_AsyncFunctionDef(self, node):
        old_function = self.current_function
        old_imports = self.imports.copy()
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        self.imports = old_imports

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)

    def visit_Try(self, node):
        for handler in node.handlers:
            exc_type = self._get_exception_type(handler.type)
            has_logging = self._check_for_logging(handler.body)
            has_raise = self._check_for_raise(handler.body)
            body_is_pass_only = len(handler.body) == 1 and isinstance(
                handler.body[0], ast.Pass
            )

            if exc_type == "Exception" and not handler.name:
                if body_is_pass_only:
                    self.violations.append(
                        {
                            "file": self.current_file,
                            "function": self.current_function,
                            "line": handler.lineno,
                            "pattern": "bare_except_pass",
                            "message": "Bare 'except Exception:' with only 'pass' - silent swallow",
                        }
                    )
            elif exc_type == "Exception" and handler.name:
                if not has_logging and not has_raise:
                    self.violations.append(
                        {
                            "file": self.current_file,
                            "function": self.current_function,
                            "line": handler.lineno,
                            "pattern": "except_exception_no_logging",
                            "message": f"'except Exception as {handler.name}:' without logging or raise",
                        }
                    )
        self.generic_visit(node)

    def _check_for_logging(self, body):
        """Check if any statement in body contains logging."""
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    if self._is_logging_call(node):
                        return True
        return False

    def _is_logging_call(self, node):
        """Check if a call is a logging call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in (
                "debug",
                "info",
                "warning",
                "error",
                "critical",
                "exception",
            ):
                if isinstance(node.func.value, ast.Name):
                    name = node.func.value.id
                    if name in ("log", "logger", "logging"):
                        return True
        if isinstance(node.func, ast.Name):
            if node.func.id in (
                "debug",
                "info",
                "warning",
                "error",
                "critical",
                "exception",
            ):
                if "logging" in self.imports:
                    return True
        return False

    def _check_for_raise(self, body):
        """Check if any statement in body raises an exception."""
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Raise):
                    return True
        return False

    def _get_exception_type(self, handler_type):
        if handler_type is None:
            return None
        if isinstance(handler_type, ast.Name):
            return handler_type.id
        if isinstance(handler_type, ast.Tuple):
            return tuple(
                elt.id if isinstance(elt, ast.Name) else None
                for elt in handler_type.elts
            )
        return None


def find_bare_except_pass_violations():
    """Find all bare 'except Exception: pass' patterns in clawmetry package."""
    violations = []
    analyzer = ErrorHandlerAnalyzer()

    for py_file in CLAWMETRY_DIR.rglob("*.py"):
        rel_path = str(py_file.relative_to(CLAWMETRY_DIR.parent))
        if rel_path in SKIP_FILES:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source)
            analyzer.current_file = rel_path
            analyzer.imports = set()
            analyzer.visit(tree)
            violations.extend(analyzer.violations)
            analyzer.violations = []
        except SyntaxError:
            continue

    return violations


def test_no_bare_except_pass():
    """Verify no bare 'except Exception: pass' patterns exist - error handlers must log or re-raise."""
    violations = find_bare_except_pass_violations()

    if violations:
        msg = (
            "Found inconsistent error handling (bare except + pass with no logging):\n"
        )
        for v in violations:
            msg += f"  {v['file']}:{v['line']} in {v['function']}() - {v['message']}\n"
        assert False, msg


if __name__ == "__main__":
    violations = find_bare_except_pass_violations()
    if violations:
        print("ERROR HANDLING VIOLATIONS FOUND:")
        for v in violations:
            print(f"  {v['file']}:{v['line']} in {v['function']}() - {v['message']}")
        sys.exit(1)
    else:
        print("No error handling violations found.")
        sys.exit(0)
