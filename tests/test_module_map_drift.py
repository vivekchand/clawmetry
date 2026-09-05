"""CI guard against module-inventory drift in the architecture docs.

``docs/MODULE_MAP.md`` is generator output (``scripts/gen_module_map.py``).
This fails when the committed file no longer matches the source tree, and
when the curated tables in ``CLAUDE.md`` name a module that has moved or been
deleted.

Burned 2026-09-05: ``CLAUDE.md``'s route table listed 17 of the 70 modules
under ``routes/`` and none of the 82 blueprints the app registers, and
``ARCHITECTURE.md`` described a 13-blueprint app that had not existed for
months. Both files were hand-maintained, so nothing caught it.

Sibling of ``test_query_contract_drift.py`` (generated doc must match its
source) and ``test_runtime_count_copy_sync.py`` (numbers in prose must match
the catalogue).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "gen_module_map.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen_module_map", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = _load_generator()


def test_committed_module_map_matches_the_source_tree():
    """docs/MODULE_MAP.md is exactly what the generator emits today."""
    assert GEN.DOC_PATH.exists(), (
        "docs/MODULE_MAP.md is missing. Generate it with "
        "`python3 scripts/gen_module_map.py`."
    )
    assert GEN.DOC_PATH.read_text(encoding="utf-8") == GEN.render(), (
        "docs/MODULE_MAP.md is stale. A module was added, removed, renamed, "
        "crossed a size band, or changed its docstring or its URL prefixes. "
        "Regenerate it with `python3 scripts/gen_module_map.py` and commit "
        "the result."
    )


def test_check_mode_agrees_with_the_committed_file():
    """``--check`` is the contract `make lint-module-map` runs on."""
    assert GEN.check() == 0


def test_every_blueprint_the_app_registers_is_in_the_map():
    """A blueprint registered in dashboard.py must be findable in the doc.

    This is the half the generator cannot check on its own: it reads the
    modules, not the registration list, so a blueprint defined in a file the
    generator does not scan would be invisible in both places.
    """
    source = (REPO / "dashboard.py").read_text(encoding="utf-8")
    # `from routes.meta import bp_otel as _bp_otel` registers under the alias;
    # the map knows the blueprint by its real name.
    aliases = dict(
        (alias, real)
        for real, alias in re.findall(r"import\s+(\w+)\s+as\s+(\w+)", source)
    )
    registered = {
        aliases.get(name, name)
        for name in re.findall(r"app\.register_blueprint\(\s*(\w+)", source)
    }
    assert registered, "no register_blueprint calls found; the regex is stale"

    doc = GEN.DOC_PATH.read_text(encoding="utf-8")
    missing = sorted(bp for bp in registered if f"`{bp}`" not in doc)
    assert not missing, (
        "dashboard.py registers blueprints that docs/MODULE_MAP.md does not "
        f"list: {missing}. Either the defining module lives outside the "
        "directories in gen_module_map.SECTIONS (add it there), or the map "
        "needs regenerating."
    )


# Modules named in the curated CLAUDE.md tables. The tables are short on
# purpose; this only asserts that what they DO name still exists, which is
# how they went stale last time (files split out of dashboard.py and the
# table kept pointing at the old home).
_CODE_REF = re.compile(
    r"`((?:routes|clawmetry|helpers|scripts|tests)/[\w./]+\.py|\w+\.py)`"
)


@pytest.mark.parametrize("doc_name", ["CLAUDE.md", "ARCHITECTURE.md"])
def test_docs_do_not_name_modules_that_no_longer_exist(doc_name):
    text = (REPO / doc_name).read_text(encoding="utf-8")
    referenced = sorted(set(_CODE_REF.findall(text)))
    assert referenced, f"{doc_name} names no modules; the regex is stale"

    missing = [ref for ref in referenced if not (REPO / ref).exists()]
    assert not missing, (
        f"{doc_name} points at modules that do not exist: {missing}. "
        "Update the prose, or the file moved and the reference did not."
    )
