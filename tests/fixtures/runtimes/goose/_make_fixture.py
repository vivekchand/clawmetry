"""Generate the Goose SQLite fixture for the adapter tests.

Materialises ``sessions/sessions.db`` matching Goose's REAL schema, captured
from a live Goose 1.35.0 install (``schema_version`` = 13) that ran
``goose run`` against local Ollama. The fixture content is synthetic (a
short hello-world conversation + a shell tool call/result), but every column
name, type, content_json block shape, and timestamp format is exactly what
Goose writes on disk.

Real captured shapes this replicates (verbatim from the live DB):

  * ``sessions.created_at`` / ``updated_at`` are SQLite ``CURRENT_TIMESTAMP``
    text, e.g. ``"2026-05-25 19:51:12"`` (UTC, space-separated, no TZ).
  * ``sessions.total_tokens`` / ``input_tokens`` / ``output_tokens`` /
    ``accumulated_total_tokens`` are populated INTEGERs; ``accumulated_cost``
    is NULL for local Ollama (tokens real, USD not computed).
  * ``model_config_json`` -> ``{"model_name":"llama3.2",...}``.
  * ``messages.created_timestamp`` is an INTEGER epoch in SECONDS;
    ``messages.tokens`` is NULL (usage lives on the session row).
  * ``content_json`` is a JSON ARRAY of blocks:
      text:         {"type":"text","text":"..."}
      tool request: {"type":"toolRequest","id":"call_x","toolCall":{"status":
                     "success","value":{"name":"...","arguments":{...}}},
                     "_meta":{"goose_extension":"developer"}}
      tool result:  {"type":"toolResponse","id":"call_x","toolResult":{"status":
                     "success","value":{"content":[{"type":"text","text":"..."}],
                     "isError":false}}}  (arrives on a role=user row)

Run directly to regenerate the committed .db file:

    python3 tests/fixtures/runtimes/goose/_make_fixture.py

Both this generator and the generated .db are committed: the .db lets tests
run with no build step, and this file documents the exact on-disk shape the
adapter parses.
"""
from __future__ import annotations

import json
import os
import sqlite3

# Real Goose 1.35.0 schema (sessions.db, schema_version 13). Verbatim column
# set + types from the live capture; indexes/extra tables omitted as the
# adapter never touches them.
SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    user_set_name BOOLEAN DEFAULT FALSE,
    session_type TEXT NOT NULL DEFAULT 'user',
    working_dir TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extension_data TEXT DEFAULT '{}',
    total_tokens INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    accumulated_total_tokens INTEGER,
    accumulated_input_tokens INTEGER,
    accumulated_output_tokens INTEGER,
    accumulated_cost REAL,
    schedule_id TEXT,
    recipe_json TEXT,
    user_recipe_values_json TEXT,
    provider_name TEXT,
    model_config_json TEXT,
    goose_mode TEXT NOT NULL DEFAULT 'auto',
    archived_at TIMESTAMP,
    project_id TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_timestamp INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens INTEGER,
    metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
"""

_MODEL_CFG = json.dumps({
    "model_name": "llama3.2",
    "context_limit": None,
    "temperature": None,
    "max_tokens": None,
    "toolshim": False,
    "toolshim_model": None,
})

_USER_META = json.dumps({"userVisible": True, "agentVisible": True})


def _text_block(text: str) -> str:
    return json.dumps([{"type": "text", "text": text}])


def _tool_request_block(call_id: str, name: str, args: dict) -> str:
    return json.dumps([{
        "type": "toolRequest",
        "id": call_id,
        "toolCall": {"status": "success", "value": {"name": name, "arguments": args}},
        "_meta": {"goose_extension": "developer"},
    }])


def _tool_response_block(call_id: str, text: str, is_error: bool = False) -> str:
    return json.dumps([{
        "type": "toolResponse",
        "id": call_id,
        "toolResult": {
            "status": "success",
            "value": {
                "content": [{"type": "text", "text": text}],
                "isError": is_error,
            },
        },
    }])


# (session_id, name, created, updated, total, input, output, accum, cost, [messages])
# Each message: (message_id, role, content_json, created_timestamp)
_SESSIONS = [
    {
        "id": "20260525_1",
        "name": "Python HelloWorld Example",
        "created_at": "2026-05-25 19:51:12",
        "updated_at": "2026-05-25 19:51:18",
        "total_tokens": 606,
        "input_tokens": 545,
        "output_tokens": 61,
        "accumulated_total_tokens": 606,
        "accumulated_cost": None,
        "messages": [
            ("msg_demo_1_a", "user",
             _text_block("Write a one-line Python hello world and explain it."),
             1779738672),
            ("chatcmpl-101", "assistant",
             _text_block(
                 "```python\nprint(\"Hello, World!\")\n```\n"
                 "The print() function writes the given string to standard output."),
             1779738677),
        ],
    },
    {
        "id": "20260525_2",
        "name": "CLI Session",
        "created_at": "2026-05-25 19:51:26",
        "updated_at": "2026-05-25 19:51:27",
        "total_tokens": 580,
        "input_tokens": 548,
        "output_tokens": 32,
        "accumulated_total_tokens": 580,
        "accumulated_cost": None,
        "messages": [
            ("msg_demo_2_a", "user",
             _text_block("What is 7 times 8? Answer with just the number."),
             1779738686),
            ("chatcmpl-102", "assistant", _text_block("56"), 1779738687),
        ],
    },
    {
        "id": "20260525_3",
        "name": "Running bash from Goose",
        "created_at": "2026-05-25 19:51:46",
        "updated_at": "2026-05-25 19:52:32",
        "total_tokens": 16389,
        "input_tokens": 6552,
        "output_tokens": 20,
        "accumulated_total_tokens": 16389,
        "accumulated_cost": None,
        "messages": [
            ("msg_demo_3_a", "user",
             _text_block("Use the shell tool to run: echo hello-from-goose"),
             1779738706),
            # assistant turn that issues a tool call
            ("chatcmpl-103", "assistant",
             _tool_request_block("call_demo01", "shell", {"command": "echo hello-from-goose"}),
             1779738710),
            # tool output is fed back on a role=user row (real Goose behaviour)
            ("msg_demo_3_b", "user",
             _tool_response_block("call_demo01", "hello-from-goose\n"),
             1779738712),
            # a second tool call that errors (real captures include isError:true)
            ("chatcmpl-104", "assistant",
             _tool_request_block("call_demo02", "shell", {"cmd": "bad-args"}),
             1779738720),
            ("msg_demo_3_c", "user",
             _tool_response_block("call_demo02", "Error: missing field `command`", is_error=True),
             1779738722),
            # final assistant text wrap-up
            ("chatcmpl-105", "assistant",
             _text_block("Done. The command printed hello-from-goose."),
             1779738732),
        ],
    },
]


def make_fixture(db_path: str) -> str:
    """Create sessions.db at ``db_path`` (parent dirs created). Returns the path."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO schema_version (version) VALUES (13)")
        for s in _SESSIONS:
            conn.execute(
                "INSERT INTO sessions (id, name, description, session_type, "
                "working_dir, created_at, updated_at, total_tokens, input_tokens, "
                "output_tokens, accumulated_total_tokens, accumulated_cost, "
                "provider_name, model_config_json, goose_mode) "
                "VALUES (?, ?, '', 'user', ?, ?, ?, ?, ?, ?, ?, ?, 'ollama', ?, 'auto')",
                (
                    s["id"], s["name"], "/tmp/goose-demo-workspace",
                    s["created_at"], s["updated_at"],
                    s["total_tokens"], s["input_tokens"], s["output_tokens"],
                    s["accumulated_total_tokens"], s["accumulated_cost"], _MODEL_CFG,
                ),
            )
            for (message_id, role, content_json, created_ts) in s["messages"]:
                conn.execute(
                    "INSERT INTO messages (message_id, session_id, role, "
                    "content_json, created_timestamp, tokens, metadata_json) "
                    "VALUES (?, ?, ?, ?, ?, NULL, ?)",
                    (message_id, s["id"], role, content_json, created_ts, _USER_META),
                )
        conn.commit()
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "sessions", "sessions.db")
    path = make_fixture(out)
    print(f"wrote {path}")
