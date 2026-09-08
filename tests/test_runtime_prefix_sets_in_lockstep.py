"""Every runtime in the catalogue must be in EVERY prefix set, both sides.

A session id is namespaced ``<runtime>:<native-id>`` and ``agent_type`` stays
``openclaw`` for all of them, so a runtime is only visible where its prefix is
listed. That list is duplicated in six Python places and four JS maps, and a
miss is silent: the sessions land in DuckDB, the rollup buckets them as
OpenClaw, and the runtime filter shows nothing. FLYWHEEL 2a records that qm
shipped missing from ``_CM_RT_PREFIXES`` exactly this way.

This is the guard that would have caught it. Adding a runtime to
``entitlements.PAID_RUNTIMES`` now fails CI until every consumer knows about
it.

``openclaw`` / ``nemoclaw`` are excluded: they are the default bucket, and the
sets deliberately disagree about whether to name them (``_CM_RT_PREFIXES``
lists openclaw and not nemoclaw; ``routes/harness`` lists both). Extra ids a
set carries beyond the catalogue (e.g. ``gemini_cli`` in the hook allowlist)
are fine — this asserts coverage, not equality.
"""
from __future__ import annotations

import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_APP_JS = os.path.join(_ROOT, "clawmetry", "static", "js", "app.js")


def _expected() -> set:
    from clawmetry.entitlements import ALL_RUNTIMES
    return set(ALL_RUNTIMES) - {"openclaw", "nemoclaw"}


def _python_sets():
    from clawmetry import local_store, sync
    from routes import attention, harness, usage
    return {
        "clawmetry.sync._RUNTIME_PREFIXES": sync._RUNTIME_PREFIXES,
        "clawmetry.sync._LITE_RT_LABELS": set(sync._LITE_RT_LABELS),
        "clawmetry.local_store._NON_OPENCLAW_RUNTIME_PREFIXES":
            set(local_store._NON_OPENCLAW_RUNTIME_PREFIXES),
        "routes.harness._NON_OPENCLAW_PREFIXES": harness._NON_OPENCLAW_PREFIXES,
        "routes.usage._NON_OPENCLAW_RT_SET": usage._NON_OPENCLAW_RT_SET,
        "routes.usage._RUNTIME_PREFIXES": usage._RUNTIME_PREFIXES,
        "routes.attention._KNOWN_RUNTIMES": attention._KNOWN_RUNTIMES,
    }


@pytest.mark.parametrize("name", sorted(_python_sets()))
def test_python_prefix_set_covers_every_catalogue_runtime(name):
    actual = _python_sets()[name]
    missing = sorted(_expected() - set(actual))
    assert not missing, (
        f"{name} is missing {missing}. Sessions from those runtimes would be "
        f"bucketed as OpenClaw (or dropped) on this surface. Add them to the "
        f"set in the same PR that adds them to PAID_RUNTIMES."
    )


def _js_map(var_decl: str) -> set:
    """Pull the keys out of one object literal in app.js."""
    src = open(_APP_JS, encoding="utf-8").read()
    start = src.index(var_decl)
    body = src[start + len(var_decl):]
    body = body[:body.index("};")]
    # Strip // comments and string literals first: a runtime named in prose
    # or inside a label must not be mistaken for a key. Keys may share a
    # line ("codex: 'Codex', cursor: 'Cursor'"), so this is not line-anchored.
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"'[^']*'|\"[^\"]*\"", "''", body)
    return set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", body))


@pytest.mark.parametrize("var_decl,label", [
    ("var _CM_RT_PREFIXES = {", "session-id prefix set"),
    ("var _Q_RUNTIME_NAMES = {", "quality-tab label map"),
    # _CM_RT_LABEL renders the runtime name in the UI. It was missed twice in a
    # row (gemini_cli, then openhands) because it shares its trailing line with
    # _Q_RUNTIME_NAMES, so a search-and-replace lands on whichever comes first
    # and the other silently keeps rendering a raw slug.
    ("var _CM_RT_LABEL = {", "runtime label map"),
])
def test_js_runtime_map_covers_every_catalogue_runtime(var_decl, label):
    missing = sorted(_expected() - _js_map(var_decl))
    assert not missing, (
        f"app.js {label} ({var_decl.strip()}) is missing {missing}. The "
        f"frontend runtime filter and labels are derived from these maps, so "
        f"a missing id renders as OpenClaw or as a raw slug."
    )


def test_every_catalogue_runtime_has_a_landing_path():
    from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_LANDING_PATHS
    missing = sorted(set(ALL_RUNTIMES) - set(RUNTIME_LANDING_PATHS))
    assert not missing, (
        f"RUNTIME_LANDING_PATHS is missing {missing} — the README grid guard "
        f"and the live storefront check both read it."
    )


def test_every_catalogue_runtime_has_a_label():
    from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_LABELS
    missing = sorted(set(ALL_RUNTIMES) - set(RUNTIME_LABELS))
    assert not missing, f"RUNTIME_LABELS is missing {missing}"


def test_every_catalogue_runtime_has_a_presence_probe():
    from clawmetry.entitlements import ALL_RUNTIMES
    from clawmetry.runtime_probe import RUNTIME_PROBES
    missing = sorted(set(ALL_RUNTIMES) - {p.id for p in RUNTIME_PROBES})
    assert not missing, (
        f"runtime_probe is missing {missing} — onboarding would not notice "
        f"those runtimes on a user's machine."
    )
