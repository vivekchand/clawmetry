"""Guard the MOAT event-shape manifest.

The MOAT suite has historically caught endpoint regressions with synthetic
event payloads, then missed real OpenClaw v3 drift because the synthetic shape
had no live sibling. This guard keeps tests/MOAT_EVENT_SHAPES.md in lockstep
with synthetic MOAT fixtures.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union


TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
MANIFEST_PATH = TESTS_DIR / "MOAT_EVENT_SHAPES.md"
MANIFEST_DISPLAY = "tests/MOAT_EVENT_SHAPES.md"

EXCLUDED_MOAT_FILES = {
    "test_moat_event_shape_manifest_guard.py",
    "test_moat_live_openclaw_e2e.py",
    "test_moat_real_e2e.py",
}


@dataclass(frozen=True)
class ManifestRow:
    event_type: str
    synthetic_test_file: str
    live_fixture_test_file: str
    last_verified_date: str


def _strip_cell(cell: str) -> str:
    cell = cell.strip()
    if len(cell) >= 2 and cell[0] == cell[-1] == "`":
        cell = cell[1:-1].strip()
    return cell


def _parse_manifest() -> Dict[str, ManifestRow]:
    rows: Dict[str, ManifestRow] = {}
    header_seen = False
    expected_header = [
        "event_type",
        "synthetic_test_file",
        "live_fixture_test_file",
        "last_verified_date",
    ]

    for lineno, line in enumerate(MANIFEST_PATH.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [_strip_cell(cell) for cell in stripped.strip("|").split("|")]
        if len(cells) != 4:
            raise AssertionError(
                f"{MANIFEST_DISPLAY}:{lineno} has {len(cells)} columns; "
                "expected 4"
            )
        lowered = [cell.lower() for cell in cells]
        if lowered == expected_header:
            header_seen = True
            continue
        if all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells):
            continue
        if not header_seen:
            raise AssertionError(f"{MANIFEST_DISPLAY}:{lineno} appears before header")

        row = ManifestRow(*cells)
        if not row.event_type:
            raise AssertionError(f"{MANIFEST_DISPLAY}:{lineno} has blank event_type")
        if row.event_type in rows:
            raise AssertionError(
                f"{MANIFEST_DISPLAY}:{lineno} duplicates event_type "
                f"{row.event_type!r}"
            )
        rows[row.event_type] = row

    if not header_seen:
        raise AssertionError(f"{MANIFEST_DISPLAY} is missing the manifest table")
    return rows


def _string_literal(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _event_type_literals(path: Path) -> Set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    event_types: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if _string_literal(key) == "event_type":
                    value_literal = _string_literal(value)
                    if value_literal:
                        event_types.add(value_literal)

        elif isinstance(node, ast.keyword) and node.arg == "event_type":
            value_literal = _string_literal(node.value)
            if value_literal:
                event_types.add(value_literal)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            event_types.update(_event_type_defaults(node))

        elif isinstance(node, ast.Call):
            event_types.update(_event_constructor_call_types(node))

    return event_types


def _event_type_defaults(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
) -> Set[str]:
    event_types: Set[str] = set()

    positional_args = list(node.args.args)
    positional_defaults = list(node.args.defaults)
    default_start = len(positional_args) - len(positional_defaults)
    for arg, default in zip(positional_args[default_start:], positional_defaults):
        if arg.arg == "event_type":
            value_literal = _string_literal(default)
            if value_literal:
                event_types.add(value_literal)

    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if arg.arg == "event_type":
            value_literal = _string_literal(default) if default is not None else None
            if value_literal:
                event_types.add(value_literal)

    return event_types


def _event_constructor_call_types(node: ast.Call) -> Set[str]:
    # tests/test_moat_send_message_e2e.py builds raw OpenClaw transcript
    # events with _ev("message", ...); sync later stores that first argument
    # as the DuckDB event_type.
    if not isinstance(node.func, ast.Name) or node.func.id != "_ev" or not node.args:
        return set()
    value_literal = _string_literal(node.args[0])
    return {value_literal} if value_literal else set()


def _synthetic_moat_files() -> Iterable[Path]:
    for path in sorted(TESTS_DIR.glob("test_moat_*.py")):
        if path.name in EXCLUDED_MOAT_FILES:
            continue
        yield path


def _synthetic_event_type_uses() -> Dict[str, List[str]]:
    uses: Dict[str, List[str]] = {}
    for path in _synthetic_moat_files():
        for event_type in _event_type_literals(path):
            uses.setdefault(event_type, []).append(path.name)
    return uses


def _split_path_cell(cell: str) -> List[str]:
    if not cell:
        return []
    normalized = cell.replace("<br>", ",").replace("<br/>", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def test_moat_event_shape_manifest_covers_synthetic_event_types():
    manifest = _parse_manifest()
    uses = _synthetic_event_type_uses()

    missing = sorted(set(uses) - set(manifest))
    assert not missing, "\n".join(
        "event_type {event_type!r} used in `{files}` but missing from "
        "`{manifest}`".format(
            event_type=event_type,
            files=", ".join(sorted(uses[event_type])),
            manifest=MANIFEST_DISPLAY,
        )
        for event_type in missing
    )


def test_moat_synthetic_manifest_rows_have_live_siblings():
    manifest = _parse_manifest()
    orphans = [
        row.event_type
        for row in manifest.values()
        if row.synthetic_test_file and not row.live_fixture_test_file
    ]

    assert not orphans, "\n".join(
        "synthetic-only event_type {event_type!r} — add a live sibling or "
        "remove the synthetic test".format(event_type=event_type)
        for event_type in sorted(orphans)
    )


def test_moat_event_shape_manifest_paths_exist():
    manifest = _parse_manifest()
    missing_paths = []

    for row in manifest.values():
        for path_text in (
            _split_path_cell(row.synthetic_test_file)
            + _split_path_cell(row.live_fixture_test_file)
        ):
            path = Path(path_text)
            if path.is_absolute() or not (REPO_ROOT / path).exists():
                missing_paths.append(path_text)

    assert not missing_paths, (
        f"{MANIFEST_DISPLAY} references missing test files: "
        f"{sorted(set(missing_paths))!r}"
    )
