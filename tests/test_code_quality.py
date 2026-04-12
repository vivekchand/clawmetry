"""Tests for code quality issues in dashboard.py."""

import ast
import pytest


def get_dashboard_path():
    """Get path to dashboard.py relative to this test file."""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(test_dir), "dashboard.py")


class TestDashboardCodeQuality:
    """Test dashboard.py for code quality issues."""

    def test_no_duplicate_security_posture_hash(self):
        """Detect duplicate _security_posture_hash definitions at module level."""
        dashboard_path = get_dashboard_path()

        with open(dashboard_path, "r") as f:
            source = f.read()

        tree = ast.parse(source)

        lines_with_assignment = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "_security_posture_hash"
                    ):
                        lines_with_assignment.append(target.lineno)

        duplicates = []
        seen = set()
        for lineno in lines_with_assignment:
            if lineno in seen:
                duplicates.append(lineno)
            seen.add(lineno)

        if len(lines_with_assignment) != len(set(lines_with_assignment)):
            pytest.fail(
                f"Duplicate _security_posture_hash definitions found at lines: {sorted(set(duplicates))}"
            )
