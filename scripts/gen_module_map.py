#!/usr/bin/env python3
"""Generate docs/MODULE_MAP.md — the full inventory of this repo's modules.

WHY THIS EXISTS
===============
``CLAUDE.md`` and ``ARCHITECTURE.md`` used to carry hand-written tables of
"the route modules" and "the package modules". They drifted, badly: on
2026-09-05 the route table listed 17 of the 70 modules under ``routes/`` and
none of the 82 blueprints the app registers, and both files quoted line
counts thousands of lines out of date. An agent reading them looked for a
feature in ``dashboard.py`` that had lived in its own module for months.

A hand-maintained inventory of a repo this size is not maintainable, so this
one is generated. The curated tables in ``CLAUDE.md`` stay small on purpose
(the modules you reach for most often) and point here for the rest.

Two deliberate choices keep the committed file stable enough to gate CI on:

* **No exact line counts.** A byte-accurate size column would change on
  almost every PR, so every unrelated PR would go red until someone
  regenerated the doc. Sizes are reported as coarse bands instead, which
  move perhaps twice a year.
* **Structure, not prose.** Module path, the blueprints it defines, the URL
  rules it registers, and the first line of its docstring. All of that is
  read out of the source with ``ast``; nothing is imported, so this runs
  without Flask, DuckDB or any optional dependency installed.

Usage::

    python3 scripts/gen_module_map.py            # rewrite the doc
    python3 scripts/gen_module_map.py --check    # exit 1 on drift

``tests/test_module_map_drift.py`` calls :func:`check` so CI fails on drift,
and ``make lint-module-map`` runs the same check locally.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
DOC_PATH = REPO / "docs" / "MODULE_MAP.md"

# (directory, heading, blurb). Order is the order of the sections in the doc.
SECTIONS: list[tuple[str, str, str]] = [
    (
        ".",
        "Top level",
        "The Flask app itself plus the optional SQLite time-series companion.",
    ),
    (
        "routes",
        "HTTP routes (`routes/`)",
        "One module per feature, each owning one or more Flask blueprints. "
        "New endpoints go here, never in `dashboard.py`.",
    ),
    (
        "helpers",
        "Shared helpers (`helpers/`)",
        "Helpers extracted out of `dashboard.py`. Route modules still reach "
        "the ones that have not moved yet via a late `import dashboard as _d`.",
    ),
    (
        "clawmetry",
        "Package (`clawmetry/`)",
        "The pip-installable package: CLI, sync daemon, DuckDB store, "
        "detectors, enforcement and the free runtime adapters.",
    ),
    (
        "clawmetry/adapters",
        "Free runtime adapters (`clawmetry/adapters/`)",
        "The runtime adapters that ship in open source. The paid ones live in "
        "`clawmetry-pro` and register over the `clawmetry.extensions` entry "
        "point; see `sync._FAMILY_ADAPTER_SPECS` for the load order.",
    ),
    (
        "clawmetry/providers",
        "Data providers (`clawmetry/providers/`)",
        "The pluggable data-provider layer behind `CLAWMETRY_PROVIDER`.",
    ),
    (
        "clawmetry/cli_cmds",
        "CLI subcommands (`clawmetry/cli_cmds/`)",
        "Subcommands dispatched by `clawmetry/cli.py`.",
    ),
    (
        "clawmetry/v2",
        "v2 API (`clawmetry/v2/`)",
        "The versioned public API surface.",
    ),
]

# Files that are packaging plumbing rather than product code.
SKIP_NAMES = {"__init__.py", "__main__.py", "setup.py", "conftest.py"}

# Line-count bands. Coarse on purpose: see the module docstring.
BANDS: list[tuple[int, str]] = [
    (200, "small"),
    (1_000, "medium"),
    (5_000, "large"),
]
BAND_HUGE = "huge"

_BAND_LEGEND = (
    "Size bands are deliberately coarse so this file does not churn on every "
    "PR: **small** is under 200 lines, **medium** under 1k, **large** under "
    "5k, **huge** is 5k and up."
)


def band(lines: int) -> str:
    """Return the coarse size band for a line count."""
    for ceiling, name in BANDS:
        if lines < ceiling:
            return name
    return BAND_HUGE


def _summary(tree: ast.Module) -> str:
    """First sentence-ish line of the module docstring, one line, no pipes."""
    doc = ast.get_docstring(tree) or ""
    first = ""
    for raw in doc.splitlines():
        if raw.strip():
            first = raw.strip()
            break
    # Most docstrings open by restating the module path ("routes/alerts.py --
    # Budget + Alerts endpoints"). The path is already the first column, so
    # drop the restatement rather than printing it twice.
    for sep in (" -- ", " — ", ": ", " - "):
        head, found, tail = first.partition(sep)
        if found and head.endswith(".py") and tail.strip():
            first = tail.strip()
            break
    # A `|` would break the markdown table; a backslash-escape renders badly
    # in some viewers, so use a comma, which is what the prose means anyway.
    return first.replace("|", ",").strip()


def _blueprints_and_rules(tree: ast.Module) -> tuple[list[str], list[str]]:
    """Blueprint variable names defined here, and the URL rules on them."""
    blueprints: list[str] = []
    rules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            call = node.value
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "Blueprint"
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        blueprints.append(target.id)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not isinstance(func, ast.Attribute) or func.attr not in (
                    "route",
                    "get",
                    "post",
                ):
                    continue
                if not dec.args:
                    continue
                first = dec.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    rules.append(first.value)

    return sorted(set(blueprints)), sorted(set(rules))


def _rule_prefixes(rules: list[str]) -> str:
    """Collapse URL rules to their distinct two-segment prefixes.

    Listing every rule would put thousands of lines in the doc and would
    churn constantly. The prefix is what a reader actually needs: which part
    of the URL space this module owns.
    """
    prefixes: set[str] = set()
    for rule in rules:
        parts = [p for p in rule.split("/") if p and not p.startswith("<")]
        if not parts:
            continue
        prefixes.add("/" + "/".join(parts[:2]))
    return ", ".join(f"`{p}`" for p in sorted(prefixes))


def _scan(directory: str) -> list[dict]:
    """Collect one record per module in ``directory`` (non-recursive)."""
    base = REPO / directory if directory != "." else REPO
    if not base.is_dir():
        return []

    out: list[dict] = []
    for path in sorted(base.glob("*.py")):
        if path.name in SKIP_NAMES:
            continue
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            # Never crash on bad input: report the module, skip the detail.
            out.append(
                {
                    "path": rel,
                    "band": band(text.count("\n") + 1),
                    "blueprints": [],
                    "prefixes": "",
                    "summary": "(unparseable)",
                }
            )
            continue
        blueprints, rules = _blueprints_and_rules(tree)
        out.append(
            {
                "path": rel,
                "band": band(text.count("\n") + 1),
                "blueprints": blueprints,
                "prefixes": _rule_prefixes(rules),
                "summary": _summary(tree),
            }
        )
    return out


def render() -> str:
    """Render the whole document."""
    sections = [(d, h, b, _scan(d)) for d, h, b in SECTIONS]
    module_total = sum(len(rows) for _, _, _, rows in sections)
    blueprint_total = len(
        {
            bp
            for _, _, _, rows in sections
            for row in rows
            for bp in row["blueprints"]
        }
    )

    lines = [
        "# ClawMetry module map",
        "",
        "> GENERATED FILE, do not edit by hand. Regenerate with",
        "> `python3 scripts/gen_module_map.py` (CI fails on drift via",
        "> `tests/test_module_map_drift.py`).",
        "",
        f"{module_total} modules, {blueprint_total} Flask blueprints. "
        "`CLAUDE.md` carries a short curated table of the ones you reach for "
        "most often; this is the whole list.",
        "",
        _BAND_LEGEND,
        "",
        "The **Serves** column is the URL space a module owns, collapsed to "
        "two path segments. A blank one means the module registers no routes "
        "of its own (it is a library, or its rules are built dynamically).",
        "",
    ]

    for directory, heading, blurb, rows in sections:
        if not rows:
            continue
        lines += [f"## {heading}", "", blurb, ""]
        has_bp = any(row["blueprints"] for row in rows)
        if has_bp:
            lines += [
                "| Module | Size | Blueprints | Serves | Purpose |",
                "|---|---|---|---|---|",
            ]
        else:
            lines += ["| Module | Size | Purpose |", "|---|---|---|"]
        for row in rows:
            if has_bp:
                bps = ", ".join(f"`{b}`" for b in row["blueprints"])
                lines.append(
                    f"| `{row['path']}` | {row['band']} | {bps} | "
                    f"{row['prefixes']} | {row['summary']} |"
                )
            else:
                lines.append(
                    f"| `{row['path']}` | {row['band']} | {row['summary']} |"
                )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def check() -> int:
    """Return 0 when the committed doc matches what we would render."""
    want = render()
    if not DOC_PATH.exists():
        print(f"{DOC_PATH.relative_to(REPO)} is missing; run scripts/gen_module_map.py")
        return 1
    have = DOC_PATH.read_text(encoding="utf-8")
    if have == want:
        print(f"module map in sync ({DOC_PATH.relative_to(REPO)})")
        return 0
    print(
        f"{DOC_PATH.relative_to(REPO)} is out of date.\n"
        "Regenerate it with: python3 scripts/gen_module_map.py"
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit 1 instead of rewriting the doc",
    )
    args = parser.parse_args()

    if args.check:
        return check()

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(render(), encoding="utf-8")
    print(f"wrote {DOC_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
