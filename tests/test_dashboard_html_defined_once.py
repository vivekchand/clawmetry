"""`dashboard.py` defines `DASHBOARD_HTML` exactly once.

It used to define it twice. The first definition — 5,036 lines of inline
HTML/CSS/JS — was overwritten at import time by the second and never rendered.
It still shipped in every wheel, and it still answered greps.

The cost was not bytes. It was that **four separate documents each had to warn
about it**: FLYWHEEL.md ("only the SECOND renders"), ARCHITECTURE.md,
AGENTS.md, and CLAUDE.md. A rule that has to be restated in four places to stop
people editing the wrong copy is a defect in the code, not a documentation gap.
It also meant a grep for any UI symbol found the dead copy first — including
`detectProjectBadge` with the developer's personal project names, which kept
matching in the repo for hours after the live one was deleted, and which
shipped to every customer inside a string nobody could render.

A second definition silently wins or silently loses depending on order. This
asserts there is only one, so the question cannot arise again.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD = REPO / "dashboard.py"
SRC = DASHBOARD.read_text(encoding="utf-8")


def _dashboard_html_assignments():
    tree = ast.parse(SRC)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DASHBOARD_HTML":
                    out.append((node.lineno, node.end_lineno))
    return sorted(out)


def test_defined_exactly_once():
    spans = _dashboard_html_assignments()
    assert len(spans) == 1, (
        f"DASHBOARD_HTML is assigned {len(spans)} times at lines "
        f"{[s[0] for s in spans]}. A second definition silently wins or loses "
        "by source order: edits land in a copy that never renders, and greps "
        "find the dead one first. Keep one."
    )


def test_the_surviving_one_is_the_template_loader():
    """Not the inline blob — the one that includes the live templates."""
    (start, end) = _dashboard_html_assignments()[0]
    body = "\n".join(SRC.split("\n")[start - 1:end])
    assert "{% include 'tabs/" in body, (
        "the surviving DASHBOARD_HTML does not include the live tab templates; "
        "the wrong definition was kept"
    )
    assert "url_for('static'" in body, (
        "the surviving DASHBOARD_HTML does not load the static assets"
    )


def test_no_personal_project_names_ship_in_dashboard_py():
    """These lived on inside the dead blob's copy of detectProjectBadge."""
    lowered = SRC.lower()
    for name in ("mockround", "vedicvoice"):
        assert name not in lowered, (
            f"{name!r} is a personal project name and must not ship in "
            "dashboard.py"
        )
    assert "function detectProjectBadge" not in SRC, (
        "the hardcoded project-badge map is back in dashboard.py"
    )
