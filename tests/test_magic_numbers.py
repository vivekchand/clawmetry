"""
Test for magic numbers in dashboard.py.

This test ensures that time-related constants are extracted to named constants
rather than being hardcoded as magic numbers throughout the codebase.
"""

import ast
import re
import pytest


# Magic numbers that should be extracted to named constants
# Maps the raw number to its semantic meaning
# Only includes time-related constants that make sense as time durations
MUST_BE_NAMED = {
    60: "SECONDS_PER_MINUTE",
    120: "SECONDS_PER_2_MINUTES",
    300: "SECONDS_PER_5_MINUTES",
    600: "SECONDS_PER_10_MINUTES",
    900: "SECONDS_PER_15_MINUTES",
    1200: "SECONDS_PER_20_MINUTES",
    1800: "SECONDS_PER_30_MINUTES",
    3600: "SECONDS_PER_HOUR",
    86400: "SECONDS_PER_DAY",
}


def get_python_magic_numbers():
    """Find all magic numbers in dashboard.py that should be named constants."""
    with open("dashboard.py", "r") as f:
        content = f.read()

    issues = []

    # Find numeric literals in expressions that look like time values
    # Pattern: looking for bare numbers in time-related contexts
    lines = content.split("\n")

    # Known time-related patterns
    time_patterns = [
        (r"time\.sleep\((\d+)\)", "time.sleep"),
        (r"time\.time\(\) - (\d+)", "time.time() - N"),
        (r"cutoff = time\.time\(\) - (\d+)", "cutoff = time.time() - N"),
        (r">= (\d+)", ">= N"),
        (r"> (\d+)", "> N"),
        (r"< (\d+)", "< N"),
        (r"- (\d+)", "- N"),
        (r"/ (\d+)", "/ N"),
        (r"\* (\d+)", "* N"),
        (r"cooldown_sec = (\d+)", "cooldown_sec = N"),
        (r"window_start = now - (\d+)", "window_start = now - N"),
        (r"window_2min = now - (\d+)", "window_2min = now - N"),
        (r"hour_ago = now - (\d+)", "hour_ago = now - N"),
        (r"if now - mtime > (\d+)", "if now - mtime > N"),
    ]

    for line_no, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith("#"):
            continue

        # Skip string literals
        if '"' in line or "'" in line:
            continue

        # Skip JavaScript code (embedded in HTML template strings)
        js_patterns = [
            "function(",
            "=>",
            ".filter(",
            ".map(",
            ".reduce(",
            "var ",
            "let ",
            "const ",
            "for (",
            "while (",
            "return ts",
            "return p",
            "start <",
            ".start <",
            "age /",
            "continue;",
            "ev.vx",
            "ev.vy",
            "other.vx",
            "other.vy",
            "rx *",
            "ry *",
            "rd2",
            "rf =",
        ]
        if any(js_pat in line for js_pat in js_patterns):
            continue

        for pattern, context in time_patterns:
            match = re.search(pattern, line)
            if match:
                num = int(match.group(1))
                if num in MUST_BE_NAMED:
                    issues.append(
                        {
                            "line": line_no,
                            "number": num,
                            "name": MUST_BE_NAMED[num],
                            "context": context,
                            "text": line.strip()[:80],
                        }
                    )

    return issues


def get_named_constants():
    """Find which named time constants are actually defined."""
    with open("dashboard.py", "r") as f:
        content = f.read()

    # Look for constant definitions at module level
    # Pattern: NAME = number  or  NAME = expression involving numbers
    constant_pattern = r"^([A-Z][A-Z_]*)\s*=\s*(\d+|timedelta|\d+\s*\*\s*\d+)"

    found = set()
    for line in content.split("\n"):
        match = re.match(constant_pattern, line.strip())
        if match:
            found.add(match.group(1))

    return found


def test_no_magic_numbers_in_dashboard():
    """Test that time-related magic numbers are extracted to named constants.

    This test will FAIL if magic numbers like 60, 300, 86400 are found
    in dashboard.py without corresponding named constants.
    """
    issues = get_python_magic_numbers()

    # Get already named constants to exclude from failures
    named = get_named_constants()

    # Filter out numbers that ARE already named
    unaccounted = [i for i in issues if i["name"] not in named]

    if unaccounted:
        msg = (
            f"Found {len(unaccounted)} magic numbers that should be named constants:\n"
        )
        for issue in unaccounted[:10]:
            msg += f"  Line {issue['line']}: {issue['name']} ({issue['number']}) in {issue['context']}\n"
            msg += f"    {issue['text']}\n"
        if len(unaccounted) > 10:
            msg += f"  ... and {len(unaccounted) - 10} more\n"
        pytest.fail(msg)
