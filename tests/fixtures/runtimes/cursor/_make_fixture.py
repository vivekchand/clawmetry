"""Generate a Cursor IDE ``state.vscdb`` fixture for the adapter tests.

Materialises a global-storage ``state.vscdb`` (and an optional per-workspace
``state.vscdb``) whose schema + key/value shapes mirror a REAL Cursor install
captured on macOS:

  Tables (both DBs):
    ItemTable     (key TEXT PRIMARY KEY, value BLOB)   -- stock VS Code state
    cursorDiskKV  (key TEXT PRIMARY KEY, value BLOB)   -- Cursor AI chat store

  Global ItemTable index row:
    composer.composerHeaders -> {"allComposers": [ {composerId, createdAt,
                                  name, unifiedMode, ...}, ... ]}

  Global cursorDiskKV rows (one per chat/composer session):
    composerData:<composerId>  -> a JSON blob; messages live in EITHER
        * fullConversationHeadersOnly: [ {bubbleId, type}, ... ]  (newer)
          with each body a SEPARATE row  bubbleId:<composerId>:<bubbleId>
        * conversationMap: { bubbleId: bubble }                   (inline/older)
    bubbleId:<composerId>:<bubbleId> -> a single message bubble:
        {type:1|2, text, createdAt, toolFormerData?, tokenCount?}
        (type 1 = user, 2 = assistant)

  Per-workspace ItemTable legacy rows (older layout):
    aiService.prompts      -> [ {text, ...}, ... ]      (user prompts)
    aiService.generations  -> [ {textDescription, ...}, ... ] (assistant gens)

Content here is SYNTHETIC but real-SHAPED (we never copy the user's real
Cursor DB, which holds private code/prompts). Run directly to regenerate the
committed .db files:

    python3 tests/fixtures/runtimes/cursor/_make_fixture.py
"""
from __future__ import annotations

import json
import os
import sqlite3

# ── real Cursor vscdb schema ─────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS ItemTable (
  key   TEXT PRIMARY KEY,
  value BLOB
);
CREATE TABLE IF NOT EXISTS cursorDiskKV (
  key   TEXT PRIMARY KEY,
  value BLOB
);
"""

# Two composer sessions. Timestamps are ms-epoch (Cursor's native unit).
AGENT_ID = "2bfaf51e-b8da-4800-933b-1e217d08d5ba"   # newer header+rows format
CHAT_ID = "3f582f7c-801d-4f75-9bff-3be4b2368251"     # inline conversationMap format

# ms-epoch, strictly increasing within each session.
T0 = 1779182203579  # agent session create
T1 = 1779182205000
T2 = 1779182206500
T3 = 1779182208000
C0 = 1779182300000  # chat session create
C1 = 1779182301000
C2 = 1779182302000


def _put(conn: sqlite3.Connection, table: str, key: str, value) -> None:
    conn.execute(
        f"INSERT OR REPLACE INTO {table} (key, value) VALUES (?, ?)",  # noqa: S608
        (key, json.dumps(value)),
    )


def _build_global(path: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)

        # ── ItemTable: the session index (composer.composerHeaders) ───────
        _put(
            conn,
            "ItemTable",
            "composer.composerHeaders",
            {
                "allComposers": [
                    {
                        "type": "head",
                        "composerId": AGENT_ID,
                        "createdAt": T0,
                        "name": "Ship the cursor adapter",
                        "unifiedMode": "agent",
                    },
                    {
                        "type": "head",
                        "composerId": CHAT_ID,
                        "createdAt": C0,
                        # no name -> title falls back to first user message
                        "unifiedMode": "chat",
                    },
                ]
            },
        )

        # ── Session 1 (AGENT_ID): newer header+rows format ────────────────
        # composerData carries the ORDER (fullConversationHeadersOnly); each
        # bubble BODY is a separate cursorDiskKV row.
        _put(
            conn,
            "cursorDiskKV",
            f"composerData:{AGENT_ID}",
            {
                "_v": 3,
                "composerId": AGENT_ID,
                "createdAt": T0,
                "unifiedMode": "agent",
                "name": "Ship the cursor adapter",
                "modelConfig": {"modelName": "claude-4.6-sonnet"},
                "conversationMap": {},  # empty -> bodies live in bubbleId rows
                "fullConversationHeadersOnly": [
                    {"bubbleId": "b1", "type": 1},
                    {"bubbleId": "b2", "type": 2},
                    {"bubbleId": "b3", "type": 2},  # tool-call bubble
                ],
            },
        )
        # bubble bodies
        _put(
            conn,
            "cursorDiskKV",
            f"bubbleId:{AGENT_ID}:b1",
            {
                "bubbleId": "b1",
                "type": 1,  # user
                "text": "write the Cursor adapter",
                "createdAt": T1,
            },
        )
        _put(
            conn,
            "cursorDiskKV",
            f"bubbleId:{AGENT_ID}:b2",
            {
                "bubbleId": "b2",
                "type": 2,  # assistant
                "text": "on it - reading the vscdb schema now",
                "createdAt": T2,
                "tokenCount": 128,  # usage HINT only, not a billed total
            },
        )
        _put(
            conn,
            "cursorDiskKV",
            f"bubbleId:{AGENT_ID}:b3",
            {
                "bubbleId": "b3",
                "type": 2,  # assistant tool call (no text)
                "text": "",
                "createdAt": T3,
                "toolFormerData": {
                    "name": "read_file",
                    "params": {"path": "clawmetry/adapters/cursor.py"},
                    "status": "completed",
                },
            },
        )

        # ── Session 2 (CHAT_ID): inline conversationMap format ────────────
        _put(
            conn,
            "cursorDiskKV",
            f"composerData:{CHAT_ID}",
            {
                "_v": 2,
                "composerId": CHAT_ID,
                "createdAt": C0,
                "unifiedMode": "chat",
                "conversationMap": {
                    "m1": {
                        "bubbleId": "m1",
                        "type": 1,
                        "text": "how do I read Cursor chats?",
                        "createdAt": C1,
                    },
                    "m2": {
                        "bubbleId": "m2",
                        "type": 2,
                        # richText fallback (text empty) -> must still flatten
                        "text": "",
                        "richText": json.dumps(
                            {
                                "root": {
                                    "children": [
                                        {"text": "open state.vscdb read-only"}
                                    ]
                                }
                            }
                        ),
                        "createdAt": C2,
                    },
                },
                "fullConversationHeadersOnly": [],
            },
        )

        conn.commit()
    finally:
        conn.close()


def _build_workspace(path: str) -> None:
    """A per-workspace DB exercising the LEGACY aiService.* layout."""
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        _put(
            conn,
            "ItemTable",
            "aiService.prompts",
            [
                {"text": "legacy: refactor the parser", "commandType": 4},
                {"text": "legacy: add a test", "commandType": 4},
            ],
        )
        _put(
            conn,
            "ItemTable",
            "aiService.generations",
            [
                {
                    "textDescription": "legacy: refactored the parser",
                    "type": "composer",
                    "unixMs": C1,
                }
            ],
        )
        conn.commit()
    finally:
        conn.close()


def make_fixture(base_dir: str | None = None, with_workspace: bool = True) -> str:
    """Create the Cursor fixture tree under *base_dir*; return the GLOBAL db path.

    Layout mirrors a real Cursor profile::

        <root>/User/globalStorage/state.vscdb
        <root>/User/workspaceStorage/<hash>/state.vscdb   (legacy aiService)
    """
    here = os.path.dirname(os.path.abspath(__file__))
    root = base_dir or os.path.join(here, "data")
    global_dir = os.path.join(root, "User", "globalStorage")
    os.makedirs(global_dir, exist_ok=True)
    global_db = os.path.join(global_dir, "state.vscdb")
    if os.path.exists(global_db):
        os.remove(global_db)
    _build_global(global_db)

    if with_workspace:
        ws_dir = os.path.join(root, "User", "workspaceStorage", "1779182202220")
        os.makedirs(ws_dir, exist_ok=True)
        ws_db = os.path.join(ws_dir, "state.vscdb")
        if os.path.exists(ws_db):
            os.remove(ws_db)
        _build_workspace(ws_db)

    return global_db


if __name__ == "__main__":
    out = make_fixture()
    print(f"Cursor fixture written; global db: {out}")
    root = os.path.dirname(os.path.dirname(os.path.dirname(out)))
    for dirpath, _dirs, files in os.walk(root):
        for f in sorted(files):
            print(f"  {os.path.join(dirpath, f)}")
