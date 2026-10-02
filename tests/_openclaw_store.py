"""Find the transcript OpenClaw just wrote, on either of its two layouts.

OpenClaw through 2026.5.x wrote the canonical conversation to
``<state>/agents/main/sessions/<sid>.jsonl``. 2026.9.x keeps it in a
per-agent SQLite database at
``<state>/agents/main/agent/openclaw-agent.sqlite`` and never creates that
directory at all -- measured against a live 2026.9.2 (the version
``.github/actions/setup-openclaw`` pins) on 2026-10-02: a turn writes
``transcript_events`` rows and no ``.jsonl`` anywhere under the home.

The live-E2E modules in this directory assert on the JSONL, and so does the
daemon they drive. Rather than teach each of them a second storage format
they call here, which materialises the store with the daemon's own reader,
``clawmetry/openclaw_sqlite.py``. What comes back has the shape they already
read -- ``<sid>.jsonl``, ``<sid>.trajectory.jsonl``, ``sessions.json`` -- so
it can be handed straight to ``sync`` as ``sessions_dir``.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

# Where OpenClaw's state root sits under the test's home. ``OPENCLAW_STATE_DIR``
# puts it at ``<home>/state``; some versions treat ``OPENCLAW_HOME`` as $HOME
# and nest under ``<home>/.openclaw`` instead (both have been observed in this
# CI job), and the oldest flat layout is the bare home. Probe all three, in the
# same order the JSONL probes in these modules use.
_STATE_SUBDIRS = ("state", ".openclaw", "")


def sqlite_store_root(home: str) -> str | None:
    """The state root under ``home`` holding a SQLite transcript store, or
    None when this OpenClaw wrote JSONL instead."""
    from clawmetry import openclaw_sqlite as ocs

    for sub in _STATE_SUBDIRS:
        root = os.path.join(home, sub) if sub else home
        if ocs.has_transcript_store(root):
            return root
    return None


def mirror_sqlite_sessions(home: str) -> str | None:
    """Materialise OpenClaw's SQLite transcripts as ``<sid>.jsonl`` files and
    return the directory holding them, or None when there is no such store.

    The mirror root is redirected under ``home`` so a run leaves nothing in
    the developer's ``~/.clawmetry``. ``sync_mirror`` never raises.
    """
    from clawmetry import openclaw_sqlite as ocs

    root = sqlite_store_root(home)
    if root is None:
        return None
    mirror_root = Path(home) / "sqlite-mirror"
    with patch.object(ocs, "mirror_root", lambda: mirror_root):
        return ocs.sync_mirror(root, {})


def newest_session_jsonl(sessions_dir: str) -> str | None:
    """Newest canonical ``<sid>.jsonl`` in ``sessions_dir``, or None.

    Filters the ``.trajectory.jsonl`` / ``.trajectory-path.json`` sidecars:
    only the bare ``<sid>.jsonl`` is the conversation file the daemon reads.
    """
    if not os.path.isdir(sessions_dir):
        return None
    cands = [
        os.path.join(sessions_dir, f)
        for f in os.listdir(sessions_dir)
        if f.endswith(".jsonl") and ".trajectory" not in f
    ]
    if not cands:
        return None
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[0]
